#!/usr/bin/env python3
"""Stage01 (IRIDIS6, read only): what the post-spin-up observation run needs from the pinned model and from an
existing finished spin-up, for the 20 OzFlux / JapanFlux sites.

1. Pinned CTSM / CDEPS / FATES source (default /iridisfs/scratch/ly3n24/CLM_FATES/CTSM):
   - git HEAD of CTSM and FATES;
   - DATM stream definitions for transient CO2 (co2tseries.*) and aerosol deposition (presaero.*), the valid values
     of DATM_CO2_TSERIES / DATM_PRESAERO and of CLM_CO2_TYPE;
   - the header of the default transient CO2 file (variables, units, time axis), so a NOAA-based file can copy it;
   - the history update frequency (upfreq) of the FATES fields used for EC comparison.
2. Finished NORMAL400 cases under cases/ (name contains NORMAL): run type, reference case, last archived restart.
   One template case (the first finished one, or --template-case) is read in detail: CO2 / aerosol / N-deposition
   settings, DATM streams, history settings, the files of its last restart set, spinup_state and the number of
   FATES restart variables in the land restart.
3. The AU-ASM direct AD400 case, if it exists.
4. Time coverage of the ten OzFlux L6 files (first / last time stamp).

Nothing is modified. Output: a new folder $HOME/ozjp_post_spinup_stage01_<UTC> with stage01_inventory.json.

Usage (login node, conda env clm_fates_env):
  python3 -B 01_post_spinup_inputs_inventory_READONLY.py --self-test
  python3 -B 01_post_spinup_inputs_inventory_READONLY.py [--template-case NAME]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CTSM = BASE / "CTSM"
CASES = BASE / "cases"
SITES = BASE / "sites" / "MY_EC_SITE"
ASM_CASE = "AU-ASM_OZ_FIXNC_GRIDREF_AD400_DIRECT"
OZ_L6 = {"AU-ASM": ["AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc",
                    "AliceSpringsMulga2_20240821T0700_to_20260423T0000_L6.nc"],
         "AU-Cow": ["CowBay_20090101T0900_to_20260423T0000_L6.nc"], "AU-Cpr": ["Calperum_L6.nc"],
         "AU-DaS": ["DalyUncleared_20080101T0000_to_20260423T0000_L6.nc"], "AU-Dry": ["DryRiver_L6.nc"],
         "AU-Gin": ["Gingin_L6.nc"], "AU-How": ["HowardSprings_L6.nc"], "AU-Stp": ["SturtPlains_L6.nc"],
         "AU-Tum": ["Tumbarumba1_L6.nc"]}
FATES_VARS = ("FATES_GPP", "FATES_NEP", "FATES_NPP", "FATES_AUTORESP", "FATES_HET_RESP", "FATES_LAI", "FATES_VEGC")
ENV_KEYS = ("CASE", "COMPSET", "RUN_TYPE", "RUN_STARTDATE", "RUN_REFCASE", "RUN_REFDATE", "RUN_REFDIR", "GET_REFCASE",
            "STOP_OPTION", "STOP_N", "REST_N", "RESUBMIT", "CONTINUE_RUN", "CALENDAR", "CLM_ACCELERATED_SPINUP",
            "CLM_CO2_TYPE", "CCSM_CO2_PPMV", "DATM_CO2_TSERIES", "DATM_PRESAERO", "DATM_YR_START", "DATM_YR_END",
            "DATM_YR_ALIGN", "DATM_MODE", "CLM_BLDNML_OPTS", "CLM_NML_USE_CASE", "CLM_FORCE_COLDSTART", "DIN_LOC_ROOT",
            "DOUT_S_ROOT", "RUNDIR", "EXEROOT")
LND_KEYS = ("finidat", "fsurdat", "fates_paramfile", "spinup_state", "co2_ppmv", "co2_type", "use_fates",
            "use_fates_fixed_biogeog", "use_fates_nocomp", "use_fates_sp", "use_init_interp", "init_interp_method",
            "stream_fldfilename_ndep", "stream_year_first_ndep", "stream_year_last_ndep", "model_year_align_ndep",
            "ndep_taxmode", "ndep_varlist", "calc_human_stress_indices", "hist_fincl1", "hist_fincl2", "hist_fincl3",
            "hist_nhtfrq", "hist_mfilt", "hist_avgflag_pertape", "hist_empty_htapes", "fates_spitfire_mode",
            "fates_parteh_mode", "use_lch4", "suplnitro", "use_nitrif_denitrif")


def utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def short(v, n=300):
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s if len(s) <= n else s[:n] + " ..."


# ---------------------------------------------------------------- source
def git_head(path):
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=30).stdout.strip() or None
    except Exception:
        return None


def find_one(root, rel_candidates):
    for rel in rel_candidates:
        p = Path(root) / rel
        if p.is_file():
            return p
    return None


def xml_entries(text, tag, name_re):
    """Raw XML blocks <tag ... name="X" ...> ... </tag> (or id="X") whose name matches name_re."""
    out = []
    for m in re.finditer(rf"<{tag}\b[^>]*\b(?:name|id)=\"([^\"]+)\"[^>]*>(.*?)</{tag}>", text, re.S):
        if re.search(name_re, m.group(1)):
            out.append((m.group(1), m.group(0)))
    return out


def entry_summary(block):
    """valid_values / default_value / desc of a CIME config entry block."""
    g = lambda t: (re.search(rf"<{t}>(.*?)</{t}>", block, re.S) or [None, ""])[1]
    return {"valid_values": short(g("valid_values")), "default_value": short(g("default_value")),
            "desc": short(g("desc"), 200),
            "values": [short(x, 160) for x in re.findall(r"<value[^>]*>.*?</value>", block, re.S)][:12]}


def fortran_call(text, vname):
    """The set_history_var(...) statement that defines vname (continuation lines joined)."""
    m = re.search(rf"vname\s*=\s*['\"]{re.escape(vname)}['\"]", text)
    if not m:
        return None
    start = text.rfind("call", 0, m.start())
    if start < 0:
        start = text.rfind("\n", 0, m.start()) + 1
    lines = []
    for line in text[start:].splitlines():
        code = line.split("!")[0].rstrip()
        lines.append(code.rstrip("&").strip())
        if not code.endswith("&"):
            break
    stmt = " ".join(x for x in lines if x)
    up = re.search(r"upfreq\s*=\s*([A-Za-z0-9_]+)", stmt)
    return {"upfreq": up.group(1) if up else None, "statement": short(stmt, 400)}


def nc_header(path):
    from netCDF4 import Dataset, num2date
    with Dataset(str(path)) as ds:
        h = {"dims": {k: len(v) for k, v in ds.dimensions.items()},
             "vars": {k: {"dims": list(v.dimensions), "units": getattr(v, "units", ""),
                          "long_name": getattr(v, "long_name", "")} for k, v in ds.variables.items()},
             "global_attrs": {k: short(ds.getncattr(k), 200) for k in ds.ncattrs()}}
        if "time" in ds.variables:
            t = ds.variables["time"]
            h["time_first_last_raw"] = [float(t[0]), float(t[-1])]
            try:
                d = num2date([t[0], t[-1]], t.units, getattr(t, "calendar", "standard"))
                h["time_first_last"] = [str(d[0]), str(d[1])]
            except Exception as exc:
                h["time_decode_error"] = short(exc, 120)
        for k, v in ds.variables.items():
            if "co2" in k.lower() and v.ndim >= 1:
                a = v[:].ravel()
                h.setdefault("co2_first_last", {})[k] = [float(a[0]), float(a[-1])]
    return h


def source_inventory(ctsm):
    out = {"ctsm_root": str(ctsm), "ctsm_head": git_head(ctsm), "fates_head": git_head(ctsm / "src" / "fates")}
    sdef = find_one(ctsm, ["components/cdeps/datm/cime_config/stream_definition_datm.xml"])
    dcfg = find_one(ctsm, ["components/cdeps/datm/cime_config/config_component.xml"])
    ccfg = find_one(ctsm, ["cime_config/config_component.xml"])
    fhist = find_one(ctsm, ["src/fates/main/FatesHistoryInterfaceMod.F90"])
    out["files"] = {k: (str(v) if v else None) for k, v in
                    (("stream_definition_datm", sdef), ("datm_config_component", dcfg),
                     ("ctsm_config_component", ccfg), ("fates_history", fhist))}
    if sdef:
        t = sdef.read_text(errors="replace")
        out["co2_streams"] = [{"name": n, "xml": short(b, 1500)} for n, b in xml_entries(t, "stream_entry", r"co2")]
        out["presaero_streams"] = [n for n, _ in xml_entries(t, "stream_entry", r"presaero")]
    if dcfg:
        t = dcfg.read_text(errors="replace")
        out["datm_entries"] = {n: entry_summary(b) for n, b in xml_entries(t, "entry", r"^DATM_(CO2_TSERIES|PRESAERO)$")}
    if ccfg:
        t = ccfg.read_text(errors="replace")
        out["ctsm_entries"] = {n: entry_summary(b) for n, b in xml_entries(t, "entry", r"^(CLM_CO2_TYPE|CCSM_BGC)$")}
    if fhist:
        t = fhist.read_text(errors="replace")
        out["fates_history"] = {v: fortran_call(t, v) for v in FATES_VARS}
    return out


# ---------------------------------------------------------------- cases
def env_values(case):
    vals = {}
    for f in sorted(Path(case).glob("env_*.xml")):
        for m in re.finditer(r"<entry\s+id=\"([^\"]+)\"\s+value=\"([^\"]*)\"", f.read_text(errors="replace")):
            vals.setdefault(m.group(1), m.group(2))
    for _ in range(6):                     # expand $VAR / ${VAR} references between entries
        changed = False
        for k, v in vals.items():
            nv = re.sub(r"\$\{?([A-Z_][A-Z0-9_]*)\}?", lambda m: vals.get(m.group(1), m.group(0)), v)
            if nv != v:
                vals[k], changed = nv, True
        if not changed:
            break
    return vals


def lnd_values(lnd_in):
    out = {}
    if not Path(lnd_in).is_file():
        return out
    text = Path(lnd_in).read_text(errors="replace")
    for k in LND_KEYS:
        m = re.search(rf"^\s*{k}\s*=\s*(.+?)\s*$", text, re.M | re.I)
        if m:
            out[k] = short(m.group(1), 400)
    return out


def rest_sets(dout):
    rd = Path(dout) / "rest"
    return sorted(p.name for p in rd.iterdir() if p.is_dir()) if rd.is_dir() else []


def year_of(stamp):
    m = re.match(r"(\d{4})", stamp or "")
    return int(m.group(1)) if m else None


def scan_normal_cases(cases_root):
    rows = []
    if not Path(cases_root).is_dir():
        return rows
    for case in sorted(Path(cases_root).iterdir()):
        if not case.is_dir() or "NORMAL" not in case.name.upper() or not (case / "env_run.xml").is_file():
            continue
        e = env_values(case)
        sets = rest_sets(e.get("DOUT_S_ROOT", ""))
        y0, y1 = year_of(e.get("RUN_STARTDATE")), year_of(sets[-1]) if sets else None
        rows.append({"case": case.name, "run_type": e.get("RUN_TYPE"), "refcase": e.get("RUN_REFCASE"),
                     "refdate": e.get("RUN_REFDATE"), "startdate": e.get("RUN_STARTDATE"),
                     "rest_sets": len(sets), "last_rest": sets[-1] if sets else None,
                     "years_done": (y1 - y0) if (y0 and y1) else None,
                     "co2": e.get("CCSM_CO2_PPMV"), "co2_type": e.get("CLM_CO2_TYPE"),
                     "spinup": e.get("CLM_ACCELERATED_SPINUP")})
    return rows


def datm_streams(path):
    out = []
    if not Path(path).is_file():
        return out
    try:
        root = ET.parse(str(path)).getroot()
    except ET.ParseError as exc:
        return [{"parse_error": short(exc)}]
    for s in root.iter("stream_info"):
        files = [f.text.strip() for f in s.iter("file") if f.text]
        g = lambda t: (s.find(t).text.strip() if s.find(t) is not None and s.find(t).text else None)
        out.append({"name": s.get("name"), "n_files": len(files), "first_file": files[0] if files else None,
                    "last_file": files[-1] if files else None, "year_first": g("year_first"),
                    "year_last": g("year_last"), "year_align": g("year_align"), "tintalgo": g("tintalgo"),
                    "mapalgo": g("mapalgo"), "meshfile": g("meshfile"),
                    "datavars": [short(v.text, 80) for v in s.iter("var") if v.text][:10]})
    return out


def restart_info(dout, stamp):
    d = Path(dout) / "rest" / stamp
    info = {"dir": str(d), "files": sorted(p.name for p in d.iterdir()) if d.is_dir() else []}
    lnd = [d / f for f in info["files"] if ".clm2.r." in f and f.endswith(".nc")]
    if lnd:
        from netCDF4 import Dataset
        with Dataset(str(lnd[0])) as ds:
            v = ds.variables.get("spinup_state")
            info["clm_restart"] = lnd[0].name
            info["spinup_state"] = None if v is None else int(v[:].ravel()[0])
            info["n_fates_vars"] = sum(1 for k in ds.variables if k.lower().startswith("fates"))
            info["n_vars"] = len(ds.variables)
    return info


def case_detail(case_dir):
    case_dir = Path(case_dir)
    e = env_values(case_dir)
    det = {"case": case_dir.name, "env": {k: e.get(k) for k in ENV_KEYS},
           "lnd_in": lnd_values(case_dir / "CaseDocs" / "lnd_in"),
           "datm_streams": datm_streams(case_dir / "CaseDocs" / "datm.streams.xml")}
    for f in ("user_nl_clm", "user_nl_datm", "user_nl_datm_streams"):
        p = case_dir / f
        if p.is_file():
            det[f] = [short(l, 200) for l in p.read_text(errors="replace").splitlines()
                      if l.strip() and not l.lstrip().startswith("!")][:40]
    st = case_dir / "CaseStatus"
    if st.is_file():
        det["casestatus_tail"] = [short(l, 160) for l in st.read_text(errors="replace").splitlines()[-4:]]
    sets = rest_sets(e.get("DOUT_S_ROOT", ""))
    det["rest_sets"] = len(sets)
    if sets:
        det["last_restart"] = restart_info(e["DOUT_S_ROOT"], sets[-1])
    return det, e


# ---------------------------------------------------------------- L6 coverage
def l6_coverage(sites_root):
    from netCDF4 import Dataset, num2date
    out = {}
    for site, files in OZ_L6.items():
        for f in files:
            p = Path(sites_root) / site / "forcing" / "raw" / f
            if not p.is_file():
                out[f] = {"site": site, "status": "MISSING"}
                continue
            with Dataset(str(p)) as ds:
                t = ds.variables["time"]
                d = num2date([t[0], t[-1]], t.units, getattr(t, "calendar", "standard"))
                out[f] = {"site": site, "status": "OK", "first": str(d[0]), "last": str(d[1]), "n": len(t)}
    return out


# ---------------------------------------------------------------- driver
def run(a):
    out = Path(a.out_dir) if a.out_dir else Path.home() / f"ozjp_post_spinup_stage01_{utc()}"
    out.mkdir(parents=True, exist_ok=False)
    res = {"generated_utc": utc()}
    print("== 1. pinned source", flush=True)
    src = source_inventory(Path(a.ctsm))
    res["source"] = src
    print(f"  CTSM {src['ctsm_head']} | FATES {src['fates_head']}")
    for k, v in src["files"].items():
        print(f"  {k}: {v}")
    for n, d in (src.get("datm_entries") or {}).items():
        print(f"  {n}: valid [{d['valid_values']}] default [{d['default_value']}]")
    for n, d in (src.get("ctsm_entries") or {}).items():
        print(f"  {n}: valid [{d['valid_values']}] default [{d['default_value']}] values {d['values'][:4]}")
    for s in src.get("co2_streams", []):
        print(f"  STREAM {s['name']}: {s['xml'][:600]}")
    print(f"  presaero streams: {src.get('presaero_streams')}")
    for v, d in (src.get("fates_history") or {}).items():
        print(f"  {v}: upfreq={d['upfreq'] if d else None} | {d['statement'][:220] if d else 'NOT FOUND'}")
    print("== 2. NORMAL400 cases", flush=True)
    rows = scan_normal_cases(Path(a.cases_root))
    res["normal_cases"] = rows
    for r in rows[:80]:
        print(f"  {r['case']} | {r['run_type']} ref {r['refcase']}@{r['refdate']} start {r['startdate']} | "
              f"rest {r['rest_sets']} last {r['last_rest']} years {r['years_done']} | CO2 {r['co2_type']} {r['co2']}")
    if len(rows) > 80:
        print(f"  ... {len(rows) - 80} more in JSON")
    tmpl = a.template_case or next((r["case"] for r in rows if (r["years_done"] or 0) >= 400), None)
    if tmpl:
        det, env = case_detail(Path(a.cases_root) / tmpl)
        res["template"] = det
        print(f"== 2b. template case {tmpl}", flush=True)
        for k, v in det["env"].items():
            if v not in (None, ""):
                print(f"  env {k} = {v}")
        for k, v in det["lnd_in"].items():
            print(f"  lnd_in {k} = {v}")
        for s in det["datm_streams"]:
            print(f"  datm stream {s.get('name')}: {s.get('n_files')} files, {s.get('year_first')}-{s.get('year_last')}"
                  f" align {s.get('year_align')} tint {s.get('tintalgo')} map {s.get('mapalgo')} | {s.get('first_file')}")
        for f in ("user_nl_clm", "user_nl_datm", "user_nl_datm_streams"):
            for l in det.get(f, []):
                print(f"  {f}: {l}")
        lr = det.get("last_restart", {})
        print(f"  last restart {lr.get('dir')} | {lr.get('files')} | spinup_state {lr.get('spinup_state')} | "
              f"FATES vars {lr.get('n_fates_vars')} of {lr.get('n_vars')}")
        co2f = next((m.group(0) for s in src.get("co2_streams", []) for m in
                     re.finditer(r"\$DIN_LOC_ROOT/[^<\s]*fco2[^<\s]*\.nc", s["xml"])), None)
        if co2f and env.get("DIN_LOC_ROOT"):
            p = Path(co2f.replace("$DIN_LOC_ROOT", env["DIN_LOC_ROOT"]))
            res["default_co2_file"] = {"path": str(p), "exists": p.is_file()}
            if p.is_file():
                res["default_co2_file"]["header"] = nc_header(p)
            print(f"  default CO2 file {p} exists={p.is_file()}")
            if p.is_file():
                h = res["default_co2_file"]["header"]
                print(f"    dims {h['dims']} | time {h.get('time_first_last')} raw {h.get('time_first_last_raw')}")
                for k, v in h["vars"].items():
                    print(f"    var {k} {v['dims']} [{v['units']}] {v['long_name']}")
                print(f"    co2 first/last {h.get('co2_first_last')}")
    else:
        print("  no finished NORMAL400 case found; pass --template-case")
    print("== 3. AU-ASM AD400 case", flush=True)
    asm = Path(a.cases_root) / ASM_CASE
    if asm.is_dir():
        det, _ = case_detail(asm)
        res["asm_case"] = det
        print(f"  {ASM_CASE}: rest sets {det['rest_sets']} | {det.get('casestatus_tail', [''])[-1]}")
    else:
        print(f"  {ASM_CASE}: not created")
    print("== 4. OzFlux L6 time coverage", flush=True)
    try:
        cov = l6_coverage(Path(a.sites_root))
    except Exception as exc:
        cov = {"error": short(exc)}
    res["l6_coverage"] = cov
    for f, d in cov.items():
        print(f"  {d.get('site') if isinstance(d, dict) else ''} {f}: {d}")
    (out / "stage01_inventory.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(f"STAGE01 DONE (read only) | {out}/stage01_inventory.json")
    return 0


def self_test():
    import tempfile
    import numpy as np
    from netCDF4 import Dataset
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        c = d / "CTSM"
        (c / "components/cdeps/datm/cime_config").mkdir(parents=True)
        (c / "cime_config").mkdir()
        (c / "src/fates/main").mkdir(parents=True)
        (c / "components/cdeps/datm/cime_config/stream_definition_datm.xml").write_text(
            '<streams><stream_entry name="co2tseries.20tr"><stream_datafiles><file first_year="1850">'
            '$DIN_LOC_ROOT/atm/datm7/CO2/fco2_datm_global_simyr_1750-2014_CMIP6_c180929.nc</file></stream_datafiles>'
            '<stream_datavars><var>CO2 Sa_co2diag</var></stream_datavars></stream_entry>'
            '<stream_entry name="presaero.clim_2000"><stream_datafiles/></stream_entry></streams>')
        (c / "components/cdeps/datm/cime_config/config_component.xml").write_text(
            '<entry_id><entry id="DATM_CO2_TSERIES"><valid_values>none,20tr,20tr.latbnd</valid_values>'
            '<default_value>none</default_value><desc>CO2 time series</desc></entry></entry_id>')
        (c / "cime_config/config_component.xml").write_text(
            '<entry_id><entry id="CLM_CO2_TYPE"><valid_values>constant,diagnostic,prognostic</valid_values>'
            '<default_value>constant</default_value></entry></entry_id>')
        (c / "src/fates/main/FatesHistoryInterfaceMod.F90").write_text(
            "    call this%set_history_var(vname='FATES_GPP', units='kg m-2 s-1', &\n"
            "         long='gross primary production', use_default='active', & ! comment\n"
            "         avgflag='A', vtype=site_r8, hlms='CLM:ALM', upfreq=group_hifr_simple, index=ih_gpp_si)\n")
        src = source_inventory(c)
        assert src["co2_streams"][0]["name"] == "co2tseries.20tr" and src["presaero_streams"] == ["presaero.clim_2000"]
        assert src["datm_entries"]["DATM_CO2_TSERIES"]["valid_values"] == "none,20tr,20tr.latbnd"
        assert src["ctsm_entries"]["CLM_CO2_TYPE"]["default_value"] == "constant"
        assert src["fates_history"]["FATES_GPP"]["upfreq"] == "group_hifr_simple"
        assert src["fates_history"]["FATES_NEP"] is None
        # case with archive and a land restart
        case = d / "cases" / "XX-Abc_FIXNC_NORMAL400"
        (case / "CaseDocs").mkdir(parents=True)
        arch = d / "archive" / case.name / "rest" / "2813-01-01-00000"
        arch.mkdir(parents=True)
        (case / "env_run.xml").write_text(
            '<file><entry id="RUN_TYPE" value="hybrid"><type>char</type></entry>'
            '<entry id="RUN_STARTDATE" value="2413-01-01"></entry><entry id="RUN_REFCASE" value="XX-Abc_AD400"></entry>'
            '<entry id="DOUT_S_ROOT" value="$ARCH_ROOT/$CASE"></entry><entry id="ARCH_ROOT" value="' + str(d / "archive")
            + '"></entry><entry id="CASE" value="' + case.name + '"></entry>'
            '<entry id="DIN_LOC_ROOT" value="' + str(d / "in") + '"></entry></file>')
        (case / "CaseDocs/lnd_in").write_text(" finidat = 'x.nc'\n stream_year_first_ndep = 2000\n use_fates = .true.\n")
        (case / "CaseDocs/datm.streams.xml").write_text(
            '<file><stream_info name="CLM1PT.x"><datafiles><file>/a/2013.nc</file><file>/a/2018.nc</file></datafiles>'
            '<datavars><var>FSDS Faxa_swdn</var></datavars><year_first>2013</year_first><year_last>2018</year_last>'
            '<year_align>2013</year_align></stream_info></file>')
        (case / "user_nl_clm").write_text("! c\nhist_nhtfrq = 0\n")
        with Dataset(str(arch / f"{case.name}.clm2.r.2813-01-01-00000.nc"), "w") as ds:
            ds.createDimension("one", 1)
            ds.createVariable("spinup_state", "i4", ("one",))[:] = 0
            ds.createVariable("fates_CohortsPerSite", "i4", ("one",))[:] = 3
        rows = scan_normal_cases(d / "cases")
        assert rows[0]["years_done"] == 400 and rows[0]["last_rest"] == "2813-01-01-00000", rows
        det, env = case_detail(case)
        assert det["env"]["DOUT_S_ROOT"].endswith(f"archive/{case.name}") and det["lnd_in"]["finidat"] == "'x.nc'"
        assert det["datm_streams"][0]["n_files"] == 2 and det["datm_streams"][0]["year_align"] == "2013"
        assert det["last_restart"]["spinup_state"] == 0 and det["last_restart"]["n_fates_vars"] == 1
        assert det["user_nl_clm"] == ["hist_nhtfrq = 0"]
        # CO2 file header
        f = d / "co2.nc"
        with Dataset(str(f), "w") as ds:
            ds.createDimension("time", None); ds.createDimension("lat", 1); ds.createDimension("lon", 1)
            t = ds.createVariable("time", "f8", ("time",)); t.units = "days since 1750-01-01 00:00:00"
            t.calendar = "noleap"; t[:] = np.array([182.5, 547.5])
            v = ds.createVariable("CO2", "f8", ("time", "lat", "lon")); v.units = "ppmv"; v[:] = [[[277.0]], [[277.5]]]
        h = nc_header(f)
        assert h["dims"]["time"] == 2 and h["co2_first_last"]["CO2"] == [277.0, 277.5] and "1750" in h["time_first_last"][0]
    print("STAGE01 SELF-TEST PASS (stream/config/F90 extraction, env expansion, NORMAL case scan, restart "
          "spinup_state, CO2 file header; no IRIDIS files)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--ctsm", default=str(CTSM))
    ap.add_argument("--cases-root", default=str(CASES))
    ap.add_argument("--sites-root", default=str(SITES))
    ap.add_argument("--template-case")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    return self_test() if a.self_test else run(a)


if __name__ == "__main__":
    sys.exit(main())

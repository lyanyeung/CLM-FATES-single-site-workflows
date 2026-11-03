#!/usr/bin/env python3
"""Stage02 (IRIDIS6): transient NOAA CO2 for the observation run, and a no-Slurm CIME preview of the
observation-run configuration on a clone of one finished NORMAL400 case.

A. Pinned source, read only. Checks the chain that carries a DATM CO2 stream to CLM:
   - CCSM_BGC=CO2A -> flds_co2a;
   - DATM_CO2_TSERIES -> datm flds_co2 and the co2tseries stream;
   - CLM imports Sa_co2diag when co2_type is 'diagnostic'.
   Also checks:
   - the single-point stream reader;
   - that a user override of stream datafiles reaches the input-data list;
   - the FATES phenology day counter kept in the restart;
   - every history field of the two observation-run tapes. Half-hourly FATES fields must be updated every time
     step (upfreq group_hifr).
B. CO2 file. Writes the NOAA GML global annual means as a DATM CO2 stream file:
   - source: the committed CSV, SHA256 checked;
   - layout: that of the default CMIP6 file;
   - written once, to experiments/NonCompetitionObserved22/co2_adopted/, read-only, with a receipt.
   An existing file is verified and never overwritten.
C. CO2 continuity. For each finished NORMAL400 case, compares the constant spin-up CO2 with the NOAA value of its
   first forcing year. It also gives the transient stream's value on 1 January of that year and its annual mean.
D. Preview (skipped with --no-preview):
   - create_clone --keepexe of the template NORMAL400 case into the new Stage02 folder;
   - hybrid start from its last restart, on the real calendar of its forcing years;
   - transient CO2 and the two output tapes;
   - case.setup, preview_namelists and check_input_data;
   - the generated lnd_in / datm_in / datm.streams.xml / nuopc.runconfig are compared with the template's.
   No build and no submit. The clone is marked DO_NOT_SUBMIT.

Output: a new folder $HOME/ozjp_post_spinup_stage02_<UTC> with stage02_result.json.

Usage (login node, conda env clm_fates_env):
  python3 -B 02_noaa_co2_stream_and_obsrun_preview.py --self-test
  python3 -B 02_noaa_co2_stream_and_obsrun_preview.py --noaa-csv NOAA.csv [--template-case NAME] [--no-preview]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CTSM = BASE / "CTSM"
CASES = BASE / "cases"
CO2_DEST = (BASE / "experiments" / "NonCompetitionObserved22" / "co2_adopted" /
            "fco2_datm_global_NOAA_GML_annmean_1979-2025_rev20261009.nc")
NOAA_SHA256 = "d82714c8a014a232b08e8bc150ddaaedf2ec4a80db65d6fe0eb93eb84f9db7db"
NOAA_REVISION = "NOAA GML co2_annmean_gl.csv, file revision 2026-10-09"
TEMPLATE = "AT-Neu_B03_FIXNC_NORMAL400"
CO2_STREAM = "co2tseries.cmip6_20tr"
CO2_TSERIES = "cmip6_20tr"

# Layout of the default CMIP6 CO2 stream file (CESM inputdata atm/datm7/CO2, read 3 Nov 2026)
LAYOUT_SOURCE = ("fco2_datm_global_simyr_1750-2014_CMIP6_c180929.nc, SHA256 "
                 "28dcbdf032b35e1240f24b9f44a44d7df1e458c1844ac1854824879f12e347a9")
LAYOUT_DIMS = {"time": None, "lat": 1, "lon": 1, "nv": 4, "bounds": 2}
LAYOUT_VARS = {"lonc": ("f8", ("lat", "lon")), "latc": ("f8", ("lat", "lon")),
               "lonv": ("f8", ("lat", "lon", "nv")), "latv": ("f8", ("lat", "lon", "nv")),
               "mask": ("f8", ("lat", "lon")), "frac": ("f8", ("lat", "lon")), "area": ("f8", ("lat", "lon")),
               "CO2": ("f4", ("time", "lat", "lon")), "time": ("f4", ("time",)),
               "time_bnds": ("f4", ("time", "bounds")), "date": ("i4", ("time",))}
FILL_F4 = 9.96921e36
FILL_I4 = -2147483647

# Observation-run output tapes. Tape 1 starts with the spin-up list.
TAPE_DAILY = ("TOTSOMC", "TOTSOMN", "TLAI", "FATES_GPP", "FATES_NPP", "TWS", "H2OSNO",
              "FATES_NEP", "FATES_HET_RESP", "FATES_AUTORESP", "FATES_MAINT_RESP", "FATES_GROWTH_RESP",
              "FATES_LAI", "FATES_VEGC", "FATES_LEAFC", "HR", "EFLX_LH_TOT", "FSH", "QVEGT", "QVEGE", "QSOIL",
              "FSA", "FIRA", "FGR", "FSDS", "TSA", "RH2M", "TSOI_10CM", "SOILWATER_10CM", "PCO2", "TOTECOSYSC")
TAPE_HH = ("FATES_GPP", "FATES_NEP", "FATES_HET_RESP", "FATES_MAINT_RESP", "EFLX_LH_TOT", "FSH", "QVEGT",
           "FSA", "FIRA", "FGR", "FSDS", "TBOT", "TSOI_10CM")
LND_ALLOWED_DIFF = {"finidat", "co2_type", "hist_fincl1", "hist_fincl2", "hist_nhtfrq", "hist_mfilt"}
DATM_ALLOWED_DIFF = {"flds_co2"}
RUNCONFIG_KEYS = ("start_type", "start_ymd", "start_tod", "stop_option", "stop_n", "stop_ymd", "restart_option",
                  "restart_n", "calendar", "flds_co2a", "flds_co2b", "flds_co2c", "atm_cpl_dt", "lnd_cpl_dt")
NON_MET_STREAMS = ("presaero", "presndep", "preso3", "topo", "co2tseries", "bias_correct", "anomaly")
DROP_USER_NL_CLM = {"finidat", "hist_fincl1", "hist_fincl2", "hist_fincl3", "hist_nhtfrq", "hist_mfilt",
                    "hist_avgflag_pertape", "hist_empty_htapes"}

# (id, file under CTSM, block regex or None, regexes that must all match inside the block)
SOURCE_CHECKS = (
    ("CCSM_BGC_ACCEPTS_CO2A", "components/cmeps/cime_config/config_component_cesm.xml",
     r'<entry id="CCSM_BGC">.*?</entry>', (r"<valid_values>[^<]*\bCO2A\b", r"<file>env_run\.xml</file>")),
    ("CCSM_BGC_NONE_FOR_DATM", "components/cmeps/cime_config/config_component_cesm.xml",
     r'<entry id="CCSM_BGC">.*?</entry>', (r'<value compset="_DATM">none</value>',)),
    ("FLDS_CO2A_FROM_BGC_MODE", "components/cmeps/cime_config/namelist_definition_drv.xml",
     r'<entry id="flds_co2a">.*?</entry>', (r'<value BGC_MODE="CO2A[^"]*">\s*\.true\.\s*</value>',)),
    ("BGC_MODE_IS_CCSM_BGC", "components/cmeps/cime_config/buildnml", None,
     (r"config\[[\"']BGC_MODE[\"']\]\s*=\s*case\.get_value\([\"']CCSM_BGC[\"']\)",)),
    ("DATM_FLDS_CO2", "components/cdeps/datm/cime_config/namelist_definition_datm.xml",
     r'<entry id="flds_co2">.*?</entry>',
     (r"<value>\s*\.true\.\s*</value>", r'<value datm_co2_tseries="none">\s*\.false\.\s*</value>')),
    ("DATM_CO2_STREAM_ADDED", "components/cdeps/datm/cime_config/buildnml", None,
     (r'streamlist\.append\(\s*"co2tseries\.\{\}"\.format\(datm_co2_tseries\)\s*\)',)),
    ("DATM_EXPORTS_SA_CO2DIAG", "components/cdeps/datm/datm_pres_co2_mod.F90", None,
     (r"dshr_fldList_add\(\s*fldsExport\s*,\s*'Sa_co2diag'\s*\)",)),
    ("CO2_STREAM_SINGLE_POINT", "components/cdeps/datm/cime_config/stream_definition_datm.xml",
     r'<stream_entry name="co2tseries\.cmip6_20tr">.*?</stream_entry>',
     (r"<meshfile>\s*none\s*</meshfile>", r"<var>\s*CO2\s+Sa_co2diag\s*</var>", r"<mapalgo>\s*none\s*</mapalgo>",
      r"<tintalgo>\s*linear\s*</tintalgo>", r"<taxmode>\s*extend\s*</taxmode>")),
    ("STRDATA_SINGLE_POINT", "components/cdeps/streams/dshr_strdata_mod.F90", None,
     (r"single point stream data, no action required",)),
    ("STREAM_OVERRIDE_IN_INPUT_LIST", "components/cdeps/cime_config/stream_cdeps.py", None,
     (r'if var_key == "datafiles":\s*\n\s*stream_datafiles = mod_dict\[var_key\]',)),
    ("CTSM_IMPORTS_SA_CO2DIAG", "src/cpl/nuopc/lnd_import_export.F90", None,
     (r"if \(flds_co2a \.or\. flds_co2b \.or\. flds_co2c\) then\s*\n\s*call fldlist_add\(fldsToLnd_num, "
      r"fldsToLnd, Sa_co2prog\)\s*\n\s*call fldlist_add\(fldsToLnd_num, fldsToLnd, Sa_co2diag\)",
      r"must have Sa_co2diag in import state if co2_type equal diagnostic")),
    ("FATES_PHEN_DAY_IN_RESTART", "src/fates/main/FatesRestartInterfaceMod.F90", None,
     (r"vname\s*=\s*'fates_phen_model_date'",)),
    ("FATES_PHEN_DAY_COUNTER", "src/fates/biogeochem/EDPhysiologyMod.F90", None,
     (r"currentSite%phen_model_date\s*=\s*currentSite%phen_model_date\s*\+\s*1",)),
)


class Stop(Exception):
    pass


def utc():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def short(v, n=300):
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s if len(s) <= n else s[:n] + " ..."


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- A. source
def run_source_checks(ctsm):
    out = []
    for cid, rel, block_re, musts in SOURCE_CHECKS:
        p = Path(ctsm) / rel
        if not p.is_file():
            out.append({"id": cid, "file": rel, "ok": False, "detail": "FILE MISSING"})
            continue
        text = p.read_text(errors="replace")
        if block_re:
            m = re.search(block_re, text, re.S)
            if not m:
                out.append({"id": cid, "file": rel, "ok": False, "detail": "BLOCK NOT FOUND"})
                continue
            text = m.group(0)
        missing = [r for r in musts if not re.search(r, text, re.S)]
        out.append({"id": cid, "file": rel, "ok": not missing,
                    "detail": "ok" if not missing else "missing: " + "; ".join(missing)})
    return out


def fates_fields(text):
    """{vname: upfreq} from FatesHistoryInterfaceMod.F90 (continuation lines joined)."""
    flat = re.sub(r"&[ \t]*(![^\n]*)?\n[ \t]*&?", " ", text)
    out = {}
    for chunk in re.split(r"call\s+this%set_history_var\(", flat)[1:]:
        c = chunk[:2500]
        m = re.search(r"vname\s*=\s*'([^']+)'", c)
        if m:
            u = re.search(r"upfreq\s*=\s*([A-Za-z0-9_]+)", c)
            out.setdefault(m.group(1), u.group(1) if u else None)
    return out


def history_field_check(ctsm):
    ctsm = Path(ctsm)
    fh = ctsm / "src/fates/main/FatesHistoryInterfaceMod.F90"
    rst = ctsm / "doc/source/users_guide/setting-up-and-running-a-case/history_fields_fates.rst"
    fates = fates_fields(fh.read_text(errors="replace")) if fh.is_file() else {}
    rst_names = set(re.findall(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s", rst.read_text(errors="replace"), re.M)) \
        if rst.is_file() else set()
    clm_wanted = sorted({f for f in TAPE_DAILY + TAPE_HH if not f.startswith("FATES_")})
    src_hits = {}
    pat = re.compile(r"fname\s*=\s*['\"](" + "|".join(map(re.escape, clm_wanted)) + r")['\"]")
    if (ctsm / "src").is_dir():
        for f in sorted((ctsm / "src").rglob("*.F90")):
            if "/fates/" in f.as_posix():
                continue
            for m in pat.finditer(f.read_text(errors="replace")):
                src_hits.setdefault(m.group(1), f.relative_to(ctsm).as_posix())
    rows = []
    for tape, fields in (("daily", TAPE_DAILY), ("halfhourly", TAPE_HH)):
        for f in fields:
            if f.startswith("FATES_"):
                up = fates.get(f)
                ok = f in fates and (tape == "daily" or "hifr" in (up or ""))
                where = f"FATES upfreq={up}" if f in fates else "NOT IN FatesHistoryInterfaceMod.F90"
            else:
                ok = f in rst_names or f in src_hits
                where = ("history_fields_fates.rst" if f in rst_names else "") + \
                        (f" {src_hits[f]}" if f in src_hits else "") or "NOT FOUND"
            rows.append({"tape": tape, "field": f, "ok": ok, "where": where.strip()})
    return {"n_fates_fields": len(fates), "rst_found": rst.is_file(), "rows": rows}


# ---------------------------------------------------------------- B. CO2 file
def read_noaa(path):
    rows = {}
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.lower().startswith("year"):
            continue
        y, m = s.split(",")[:2]
        rows[int(y)] = float(m)
    years = sorted(rows)
    if not years or years != list(range(years[0], years[-1] + 1)):
        raise Stop("NOAA table years are not contiguous")
    return rows


def year_axis(year, y0):
    """(mid-year, 1 Jan, next 1 Jan) in days since y0-01-01, gregorian. Mid-year = half the year length after
    1 Jan, as in the layout file (1750: 182.5, 1752 leap: 913.0)."""
    a = (date(year, 1, 1) - date(y0, 1, 1)).days
    b = (date(year + 1, 1, 1) - date(y0, 1, 1)).days
    return a + (b - a) / 2.0, a, b


def build_co2_file(rows, out_path):
    import numpy as np
    from netCDF4 import Dataset
    years = sorted(rows)
    y0 = years[0]
    with Dataset(str(out_path), "w", format="NETCDF3_CLASSIC") as ds:
        ds.title = "NOAA GML global annual mean surface CO2 as a CDEPS DATM CO2 stream (co2tseries layout)"
        ds.source = f"{NOAA_REVISION}, SHA256 {NOAA_SHA256}"
        ds.layout_template = LAYOUT_SOURCE
        ds.time_convention = ("annual means stamped at mid-year (gregorian), as in the layout template; DATM "
                              "interpolates linearly and holds the end values (taxmode extend)")
        ds.created_by = ("CLM-FATES-single-site-workflows examples/OzFlux_JapanFlux_PostSpinup/scripts/"
                         "02_noaa_co2_stream_and_obsrun_preview.py")
        for k, n in LAYOUT_DIMS.items():
            ds.createDimension(k, n)

        def var(name, attrs, fill=None):
            dt, dims = LAYOUT_VARS[name]
            v = ds.createVariable(name, dt, dims, fill_value=fill)
            for k, val in attrs.items():
                v.setncattr(k, val)
            return v

        var("lonc", {"units": "degrees_east", "lname": "Longitude of grid cell center", "bounds": "lonv"})[:] = 180.0
        var("latc", {"units": "degrees_north", "lname": "Latitude of grid cell center", "bounds": "latv"})[:] = 0.0
        var("lonv", {"units": "degree_east", "lname": "Longitudes of grid cell vertices"})[:] = [[[0., 360., 360., 0.]]]
        var("latv", {"units": "degrees_north", "lname": "Latitudes of grid cell vertices"})[:] = [[[90., -90., -90., 90.]]]
        for name, ln in (("mask", "Mask of active cells: 1=active"), ("frac", "Fraction of grid cell that is active")):
            var(name, {"units": "unitless", "lname": ln, "coordinate": "latc lonc"})[:] = 1.0
        var("area", {"units": "radians^2", "lname": "Area of grid cell", "coordinate": "latc lonc"})[:] = 4.0 * np.pi
        co2 = var("CO2", {"coordinate": "latc lonc time", "units": "ppmv", "lname": "CO2 concentration"},
                  fill=np.float32(FILL_F4))
        units = f"days since {y0:04d}-01-01 00:00:00"
        t = var("time", {"long_name": "time", "units": units, "calendar": "gregorian", "bounds": "time_bnds"},
                fill=np.float32(FILL_F4))
        tb = var("time_bnds", {"long_name": "time", "units": units, "calendar": "gregorian"})
        d = var("date", {"calendar": "gregorian",
                         "comment": "This variable is NOT used when read by datm, the time coordinate is used"},
                fill=np.int32(FILL_I4))
        for i, y in enumerate(years):
            mid, a, b = year_axis(y, y0)
            t[i] = mid
            tb[i, :] = [a, b]
            d[i] = y * 10000 + 702
            co2[i, 0, 0] = rows[y]


def verify_co2_file(path, rows):
    from netCDF4 import Dataset
    years = sorted(rows)
    with Dataset(str(path)) as ds:
        ds.set_auto_mask(False)
        dims = {k: (None if v.isunlimited() else len(v)) for k, v in ds.dimensions.items()}
        if dims != LAYOUT_DIMS or len(ds.dimensions["time"]) != len(years):
            raise Stop(f"CO2 file dims {dims} differ from the layout {LAYOUT_DIMS}")
        for k, (dt, vd) in LAYOUT_VARS.items():
            v = ds.variables.get(k)
            if v is None or v.dtype.str[1:] != dt or tuple(v.dimensions) != vd:
                raise Stop(f"CO2 file variable {k} differs from the layout")
        co2 = ds.variables["CO2"][:, 0, 0]
        t = ds.variables["time"]
        if ds.variables["CO2"].units != "ppmv" or t.calendar != "gregorian" or not t.units.startswith("days since"):
            raise Stop("CO2 file units / calendar differ from the layout")
        for i, y in enumerate(years):
            if abs(float(co2[i]) - rows[y]) > 1e-4 or abs(float(t[i]) - year_axis(y, years[0])[0]) > 1e-6:
                raise Stop(f"CO2 file value or time wrong for {y}")
            if int(ds.variables["date"][i]) != y * 10000 + 702:
                raise Stop(f"CO2 file date wrong for {y}")
        if (co2 >= FILL_F4 * 0.1).any():
            raise Stop("CO2 file has fill values (single-point streams may not)")
    return {"n_years": len(years), "first": [years[0], rows[years[0]]], "last": [years[-1], rows[years[-1]]],
            "time_units": f"days since {years[0]:04d}-01-01 00:00:00"}


def install_co2(rows, dest, csv_sha):
    dest = Path(dest)
    receipt = dest.with_name(dest.name + ".receipt.json")
    if dest.exists():
        info = verify_co2_file(dest, rows)
        s = sha256(dest)
        rec = json.loads(receipt.read_text()) if receipt.is_file() else None
        if rec and rec.get("sha256") != s:
            raise Stop(f"existing CO2 file SHA256 {s} differs from its receipt {rec.get('sha256')}")
        return {"status": "EXISTING_VERIFIED", "path": str(dest), "sha256": s, "receipt": str(receipt),
                "receipt_found": rec is not None, **info}
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.tmp{os.getpid()}")
    try:
        build_co2_file(rows, tmp)
        verify_co2_file(tmp, rows)
        data = tmp.read_bytes()
    finally:
        if tmp.exists():
            tmp.unlink()
    with open(dest, "xb") as f:
        f.write(data)
    os.chmod(dest, 0o444)
    s = sha256(dest)
    info = verify_co2_file(dest, rows)
    rec = {"file": str(dest), "sha256": s, "bytes": len(data), "noaa_csv_sha256": csv_sha,
           "noaa_revision": NOAA_REVISION, "layout_template": LAYOUT_SOURCE, "stream": CO2_STREAM,
           "written_utc": utc(), **info}
    with open(receipt, "x") as f:
        f.write(json.dumps(rec, indent=1) + "\n")
    os.chmod(receipt, 0o444)
    return {"status": "INSTALLED", "path": str(dest), "sha256": s, "receipt": str(receipt), **info}


def stream_co2_stats(rows, y):
    """Linear interpolation between mid-year values, end values held: value on 1 Jan of y and annual mean of y."""
    c = lambda k: rows[min(max(k, min(rows)), max(rows))]
    return {"jan1": 0.5 * (c(y - 1) + c(y)), "annual_mean": 0.125 * c(y - 1) + 0.75 * c(y) + 0.125 * c(y + 1)}


# ---------------------------------------------------------------- cases (as Stage01)
def env_values(case):
    vals = {}
    for f in sorted(Path(case).glob("env_*.xml")):
        for m in re.finditer(r"<entry\s+id=\"([^\"]+)\"\s+value=\"([^\"]*)\"", f.read_text(errors="replace")):
            vals.setdefault(m.group(1), m.group(2))
    for _ in range(6):
        changed = False
        for k, v in vals.items():
            nv = re.sub(r"\$\{?([A-Z_][A-Z0-9_]*)\}?", lambda m: vals.get(m.group(1), m.group(0)), v)
            if nv != v:
                vals[k], changed = nv, True
        if not changed:
            break
    return vals


def rest_sets(dout):
    rd = Path(dout) / "rest"
    return sorted(p.name for p in rd.iterdir() if p.is_dir()) if rd.is_dir() else []


def year_of(stamp):
    m = re.match(r"(\d{4})", stamp or "")
    return int(m.group(1)) if m else None


def datm_streams(path):
    """{stream name: {leaf tags, files, vars}} from a generated datm.streams.xml."""
    out = {}
    if not Path(path).is_file():
        return out
    root = ET.parse(str(path)).getroot()
    for s in root.iter("stream_info"):
        d = {c.tag: (c.text or "").strip() for c in s if len(c) == 0}
        d["files"] = [f.text.strip() for f in s.iter("file") if f.text]
        d["vars"] = [re.sub(r"\s+", " ", v.text.strip()) for v in s.iter("var") if v.text]
        d.pop("datafiles", None)
        d.pop("datavars", None)
        out[s.get("name")] = d
    return out


def met_stream(streams):
    for name, d in streams.items():
        if not name.lower().startswith(NON_MET_STREAMS):
            return name, d
    return None, None


def continuity(cases_root, rows):
    out = []
    root = Path(cases_root)
    if not root.is_dir():
        return out
    for case in sorted(root.iterdir()):
        if not case.is_dir() or "NORMAL" not in case.name.upper() or not (case / "env_run.xml").is_file():
            continue
        e = env_values(case)
        sets = rest_sets(e.get("DOUT_S_ROOT", ""))
        y0, y1 = year_of(e.get("RUN_STARTDATE")), (year_of(sets[-1]) if sets else None)
        if not (y0 and y1 and y1 - y0 >= 400):
            continue
        name, met = met_stream(datm_streams(case / "CaseDocs" / "datm.streams.xml"))
        r = {"case": case.name, "co2_type": e.get("CLM_CO2_TYPE"), "spinup_co2": e.get("CCSM_CO2_PPMV"),
             "met_stream": name, "first_forcing_year": None}
        if met and met.get("year_first", "").isdigit():
            y = int(met["year_first"])
            r["first_forcing_year"] = y
            if y in rows and r["spinup_co2"]:
                spin = float(r["spinup_co2"])
                st = stream_co2_stats(rows, y)
                r.update({"noaa": rows[y], "spinup_minus_noaa": round(spin - rows[y], 3),
                          "stream_jan1": round(st["jan1"], 3), "stream_annual_mean": round(st["annual_mean"], 3),
                          "jan1_minus_spinup": round(st["jan1"] - spin, 3),
                          "annual_mean_minus_spinup": round(st["annual_mean"] - spin, 3)})
        out.append(r)
    return out


# ---------------------------------------------------------------- D. preview helpers
def parse_namelist(path):
    vals, key = {}, None
    for line in Path(path).read_text(errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("!"):
            continue
        if s.startswith("&") or s == "/":
            key = None
            continue
        m = re.match(r"([A-Za-z0-9_%]+)\s*=\s*(.*)$", s)
        if m:
            key = m.group(1).lower()
            vals[key] = m.group(2).strip()
        elif key:
            vals[key] += " " + s
    return {k: re.sub(r"\s+", " ", v).strip() for k, v in vals.items()}


def parse_runconfig(path):
    vals = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$", line)
        if m:
            vals.setdefault(m.group(1), m.group(2))
    return vals


def dict_diff(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def fincl(fields):
    return ",".join(f"'{f}'" for f in fields)


def rewrite_user_nl_clm(text, finidat, ncpl):
    """Template user_nl_clm without its finidat / history lines (and their continuation lines), plus the
    observation-run block."""
    out, skipping = [], False
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*=", line)
        if m:
            skipping = m.group(1).lower() in DROP_USER_NL_CLM
        elif not s or s.startswith("!"):
            out.append(line)
            continue
        if not skipping:
            out.append(line)
    out += ["",
            "! ---- observation run (OzFlux_JapanFlux_PostSpinup Stage02): hybrid start from the final NORMAL400",
            "! ---- restart; tape 1 daily, tape 2 every model time step (EC comparison)",
            f"finidat = '{finidat}'",
            f"hist_fincl1 = {fincl(TAPE_DAILY)}",
            f"hist_fincl2 = {fincl(TAPE_HH)}",
            "hist_nhtfrq = -24, 1",
            f"hist_mfilt = 365, {365 * ncpl}"]
    return "\n".join(out) + "\n"


def co2_stream_block(path, years):
    return "\n".join([
        "! ---- observation run (OzFlux_JapanFlux_PostSpinup Stage02): NOAA GML global annual CO2",
        f"{CO2_STREAM}:datafiles = {path}",
        f"{CO2_STREAM}:year_first = {years[0]}",
        f"{CO2_STREAM}:year_last = {years[1]}",
        f"{CO2_STREAM}:year_align = {years[0]}"]) + "\n"


def run_cmd(cmd, cwd=None, seconds=600):
    r = subprocess.run([str(x) for x in cmd], cwd=str(cwd) if cwd else None, text=True, capture_output=True,
                       timeout=seconds)
    return r.returncode, r.stdout, r.stderr


def must(cmd, cwd=None, seconds=600):
    rc, out, err = run_cmd(cmd, cwd, seconds)
    if rc:
        raise Stop(f"COMMAND FAILED ({rc}): {' '.join(map(str, cmd))}\nOUT: {out[-1500:]}\nERR: {err[-1500:]}")
    return out.strip()


def q(case, key, extra=()):
    return must([Path(case) / "xmlquery", key, *extra, "--value"], cwd=case, seconds=120)


def ch(case, key, val):
    must([Path(case) / "xmlchange", f"{key}={val}"], cwd=case, seconds=120)


def template_fingerprint(case):
    """SHA256 of the template's env_*.xml and user_nl_* files (create_clone opens the source case writable)."""
    files = sorted(list(Path(case).glob("env_*.xml")) + list(Path(case).glob("user_nl_*")))
    return {f.name: sha256(f) for f in files if f.is_file()}


def template_throughput(case):
    """'Model Throughput' (simulated years/day) of the newest timing file of the template."""
    files = sorted((Path(case) / "timing").glob("cesm_timing.*"), key=lambda p: p.stat().st_mtime) \
        if (Path(case) / "timing").is_dir() else []
    for f in reversed(files):
        if f.suffix == ".gz":
            import gzip
            text = gzip.open(f, "rt", errors="replace").read()
        else:
            text = f.read_text(errors="replace")
        m = re.search(r"Model Throughput:\s*([0-9.]+)\s*simulated_years/day", text)
        if m:
            return {"file": f.name, "simulated_years_per_day": float(m.group(1))}
    return None


def preview(a, out, tmpl, co2_path, noaa_years):
    ctsm, src = Path(a.ctsm), Path(a.cases_root) / tmpl
    res = {"template": tmpl, "checks": []}
    chk = lambda cid, ok, detail="": res["checks"].append({"id": cid, "ok": bool(ok), "detail": short(detail, 400)})
    e = env_values(src)
    sets = rest_sets(e.get("DOUT_S_ROOT", ""))
    if not sets:
        raise Stop(f"{tmpl}: no archived restart set")
    last = sets[-1]
    refdate = last[:10]
    land_rest = Path(e["DOUT_S_ROOT"]) / "rest" / last / f"{tmpl}.clm2.r.{last}.nc"
    if not land_rest.is_file():
        raise Stop(f"{tmpl}: land restart missing {land_rest}")
    t_streams = datm_streams(src / "CaseDocs" / "datm.streams.xml")
    met_name, met = met_stream(t_streams)
    if not met or not met.get("year_first", "").isdigit():
        raise Stop(f"{tmpl}: met stream not found in CaseDocs/datm.streams.xml")
    y0, y1 = int(met["year_first"]), int(met["year_last"])
    if CO2_STREAM in t_streams:
        raise Stop(f"{tmpl}: template already has {CO2_STREAM}")
    res.update({"last_restart": last, "land_restart": str(land_rest), "land_restart_sha256": sha256(land_rest),
                "met_stream": met_name, "forcing_years": [y0, y1], "n_years": y1 - y0 + 1})
    name = f"OBSPREVIEW_{tmpl}"
    case = out / "case" / name
    case.parent.mkdir(parents=True)
    before = template_fingerprint(src)
    must([ctsm / "cime/scripts/create_clone", "--case", case, "--clone", src, "--keepexe",
          "--cime-output-root", out / "cime_output"], cwd=ctsm / "cime/scripts", seconds=900)
    (case / "DO_NOT_SUBMIT_PREVIEW_ONLY.txt").write_text(
        "Stage02 preview clone. Namelists only: never build or submit this case.\n")
    changed = sorted(k for k, v in template_fingerprint(src).items() if before.get(k) != v)
    chk("TEMPLATE_FILES_UNCHANGED", not changed, f"changed {changed}" if changed else f"{len(before)} files")
    chk("CLONE_IDENTITY", q(case, "CASE") == name, q(case, "CASE"))
    chk("CLONE_KEEPS_EXE", q(case, "EXEROOT") == e.get("EXEROOT") and q(case, "BUILD_COMPLETE").upper() == "TRUE",
        f"EXEROOT {q(case, 'EXEROOT')} BUILD_COMPLETE {q(case, 'BUILD_COMPLETE')}")
    ch(case, "RUNDIR", out / "cime_output" / name / "run")
    ch(case, "DOUT_S_ROOT", out / "cime_output" / "archive" / name)
    rundir, dout = q(case, "RUNDIR"), q(case, "DOUT_S_ROOT")
    chk("CLONE_DIRS_INSIDE_STAGE02", rundir.startswith(str(out)) and dout.startswith(str(out)), f"{rundir} | {dout}")
    if not (rundir.startswith(str(out)) and dout.startswith(str(out))):
        raise Stop(f"clone RUNDIR / DOUT_S_ROOT outside the Stage02 folder: {rundir} | {dout}")
    ncpl = int(q(case, "ATM_NCPL"))
    settings = {"RUN_TYPE": "hybrid", "RUN_REFCASE": tmpl, "RUN_REFDATE": refdate, "RUN_REFTOD": "00000",
                "RUN_STARTDATE": f"{y0:04d}-01-01", "GET_REFCASE": "FALSE", "CONTINUE_RUN": "FALSE",
                "CLM_ACCELERATED_SPINUP": "off", "CLM_CO2_TYPE": "diagnostic", "CCSM_BGC": "CO2A",
                "DATM_CO2_TSERIES": CO2_TSERIES, "STOP_OPTION": "nyears", "STOP_N": str(y1 - y0 + 1),
                "REST_OPTION": "nyears", "REST_N": "1", "RESUBMIT": "0"}
    for k, v in settings.items():
        ch(case, k, v)
    t_nl = (src / "user_nl_clm").read_text(errors="replace")
    (case / "user_nl_clm").write_text(rewrite_user_nl_clm(t_nl, land_rest, ncpl))
    t_ds = (src / "user_nl_datm_streams").read_text(errors="replace") if (src / "user_nl_datm_streams").is_file() else ""
    if "co2tseries" in t_ds:
        raise Stop("template user_nl_datm_streams already mentions co2tseries")
    (case / "user_nl_datm_streams").write_text(t_ds.rstrip("\n") + "\n" + co2_stream_block(co2_path, noaa_years))
    if not (case / ".case.run").is_file():
        must([case / "case.setup"], cwd=case, seconds=600)
    must([case / "preview_namelists"], cwd=case, seconds=900)
    for k, v in settings.items():
        got = q(case, k)
        chk(f"XML_{k}", got.strip().lower() == v.lower(), got)
    # lnd_in
    ln, lt = parse_namelist(case / "CaseDocs/lnd_in"), parse_namelist(src / "CaseDocs/lnd_in")
    chk("LND_CO2_TYPE_DIAGNOSTIC", ln.get("co2_type") == "'diagnostic'", ln.get("co2_type"))
    chk("LND_FINIDAT_FINAL_NORMAL400", ln.get("finidat") == f"'{land_rest}'", ln.get("finidat"))
    chk("LND_TWO_TAPES", ln.get("hist_nhtfrq", "").replace(" ", "") == "-24,1" and "'FATES_NEP'" in ln.get("hist_fincl2", ""),
        f"nhtfrq {ln.get('hist_nhtfrq')} mfilt {ln.get('hist_mfilt')}")
    d = dict_diff(ln, lt)
    chk("LND_ONLY_EXPECTED_DIFFS", set(d) <= LND_ALLOWED_DIFF, f"diff keys {d}")
    res["lnd_in_diff"] = {k: {"template": short(lt.get(k), 160), "preview": short(ln.get(k), 160)} for k in d}
    # datm_in
    dn, dt = parse_namelist(case / "CaseDocs/datm_in"), parse_namelist(src / "CaseDocs/datm_in")
    chk("DATM_FLDS_CO2_TRUE", dn.get("flds_co2") == ".true.", dn.get("flds_co2"))
    d = dict_diff(dn, dt)
    chk("DATM_ONLY_EXPECTED_DIFFS", set(d) <= DATM_ALLOWED_DIFF, f"diff keys {d}")
    res["datm_in_diff"] = {k: {"template": dt.get(k), "preview": dn.get(k)} for k in d}
    # streams
    s_new = datm_streams(case / "CaseDocs/datm.streams.xml")
    co2s = s_new.get(CO2_STREAM, {})
    res["co2_stream"] = co2s
    chk("STREAM_CO2_FILE", co2s.get("files") == [str(co2_path)], co2s.get("files"))
    chk("STREAM_CO2_YEARS", [co2s.get("year_first"), co2s.get("year_last"), co2s.get("year_align")] ==
        [str(noaa_years[0]), str(noaa_years[1]), str(noaa_years[0])], co2s)
    chk("STREAM_CO2_SINGLE_POINT", co2s.get("meshfile") == "none" and co2s.get("mapalgo") == "none" and
        co2s.get("tintalgo") == "linear" and co2s.get("taxmode") == "extend" and
        co2s.get("vars") == ["CO2 Sa_co2diag"], co2s)
    other_new = {k: v for k, v in s_new.items() if k != CO2_STREAM}
    chk("STREAMS_OTHERWISE_IDENTICAL", other_new == t_streams,
        f"changed: {[k for k in set(other_new) | set(t_streams) if other_new.get(k) != t_streams.get(k)]}")
    # nuopc.runconfig
    rn, rt = parse_runconfig(case / "CaseDocs/nuopc.runconfig"), parse_runconfig(src / "CaseDocs/nuopc.runconfig")
    res["runconfig"] = {k: {"template": rt.get(k), "preview": rn.get(k)} for k in RUNCONFIG_KEYS}
    chk("RUNCONFIG_FLDS_CO2A", rn.get("flds_co2a") == ".true.", rn.get("flds_co2a"))
    chk("RUNCONFIG_START", rn.get("start_ymd") == f"{y0:04d}0101", f"start_ymd {rn.get('start_ymd')} "
                                                                 f"start_type {rn.get('start_type')}")
    # input data
    rc, o, err = run_cmd([case / "check_input_data"], cwd=case, seconds=900)
    lines = [l for l in (o + err).splitlines() if l.strip()]
    missing = [l for l in lines if re.search(r"missing|not found|cannot find|could not", l, re.I)]
    chk("CHECK_INPUT_DATA", rc == 0 and not missing, f"rc {rc}; " + " | ".join(missing[:6] or lines[-3:]))
    res["check_input_data_tail"] = [short(l, 200) for l in lines[-12:]]
    res["atm_ncpl"] = ncpl
    try:
        res["wallclock_case_run"] = q(case, "JOB_WALLCLOCK_TIME", ("--subgroup", "case.run"))
    except Stop as exc:
        res["wallclock_case_run"] = f"query failed: {short(exc, 120)}"
    tp = template_throughput(src)
    res["template_throughput"] = tp
    if tp and tp["simulated_years_per_day"] > 0:
        res["estimated_hours_without_extra_output"] = round(24.0 * (y1 - y0 + 1) / tp["simulated_years_per_day"], 2)
    res["case"] = str(case)
    res["ok"] = all(c["ok"] for c in res["checks"])
    return res


# ---------------------------------------------------------------- driver
def run(a):
    out = Path(a.out_dir) if a.out_dir else Path.home() / f"ozjp_post_spinup_stage02_{utc()}"
    out.mkdir(parents=True, exist_ok=False)
    res = {"generated_utc": utc(), "out": str(out)}
    status = 0
    try:
        print("== A. pinned source", flush=True)
        sc = run_source_checks(Path(a.ctsm))
        res["source_checks"] = sc
        for c in sc:
            print(f"  {'PASS' if c['ok'] else 'FAIL'} {c['id']}: {c['detail'][:160]}")
        hf = history_field_check(Path(a.ctsm))
        res["history_fields"] = hf
        bad = [r for r in hf["rows"] if not r["ok"]]
        print(f"  history fields: {len(hf['rows']) - len(bad)}/{len(hf['rows'])} ok (FATES fields parsed "
              f"{hf['n_fates_fields']}, rst {'found' if hf['rst_found'] else 'MISSING'})")
        for r in hf["rows"]:
            if r["field"].startswith("FATES_") or not r["ok"]:
                print(f"    {'ok ' if r['ok'] else 'BAD'} {r['tape']:10s} {r['field']:18s} {r['where']}")
        if not all(c["ok"] for c in sc) or bad:
            raise Stop("source or history-field check failed: no CO2 file, no preview")
        print("== B. CO2 stream file", flush=True)
        csv_sha = sha256(a.noaa_csv)
        if csv_sha != NOAA_SHA256:
            raise Stop(f"NOAA CSV SHA256 {csv_sha} != {NOAA_SHA256}")
        rows = read_noaa(a.noaa_csv)
        years = (min(rows), max(rows))
        co2 = install_co2(rows, Path(a.co2_dest), csv_sha)
        res["co2_file"] = co2
        print(f"  {co2['status']} {co2['path']}\n  sha256 {co2['sha256']} | {co2['n_years']} years "
              f"{co2['first']} .. {co2['last']} | {co2['time_units']}")
        print("== C. CO2 continuity, finished NORMAL400 cases", flush=True)
        cont = continuity(Path(a.cases_root), rows)
        res["continuity"] = cont
        off = [r for r in cont if r.get("spinup_minus_noaa") is None or abs(r["spinup_minus_noaa"]) > 0.005]
        j = [r["jan1_minus_spinup"] for r in cont if "jan1_minus_spinup" in r]
        m = [r["annual_mean_minus_spinup"] for r in cont if "annual_mean_minus_spinup" in r]
        print(f"  {len(cont)} cases; {len(cont) - len(off)} spin-up CO2 = NOAA(first forcing year) within 0.005 ppm")
        if j:
            print(f"  transient stream at the hand-off (1 Jan of first year) minus spin-up: {min(j):+.2f} .. "
                  f"{max(j):+.2f} ppm; first-year mean minus spin-up: {min(m):+.3f} .. {max(m):+.3f} ppm")
        for r in off:
            print(f"    {r['case']}: first year {r['first_forcing_year']} spin-up {r['spinup_co2']} "
                  f"NOAA {r.get('noaa')} diff {r.get('spinup_minus_noaa')}")
        if a.no_preview:
            print("== D. preview skipped (--no-preview)")
        else:
            tmpl = a.template_case or TEMPLATE
            print(f"== D. preview on a clone of {tmpl} (no build, no submit)", flush=True)
            pv = preview(a, out, tmpl, Path(co2["path"]), years)
            res["preview"] = pv
            print(f"  clone {pv['case']}")
            print(f"  forcing {pv['forcing_years']} ({pv['n_years']} yr) | restart {pv['last_restart']} | "
                  f"ATM_NCPL {pv['atm_ncpl']} | wallclock {pv['wallclock_case_run']} | throughput "
                  f"{pv['template_throughput']} | est. h {pv.get('estimated_hours_without_extra_output')}")
            for c in pv["checks"]:
                print(f"  {'PASS' if c['ok'] else 'FAIL'} {c['id']}: {c['detail'][:200]}")
            for k, v in pv["lnd_in_diff"].items():
                print(f"    lnd_in {k}: {v['template'][:70]} -> {v['preview'][:110]}")
            for k, v in pv["datm_in_diff"].items():
                print(f"    datm_in {k}: {v['template']} -> {v['preview']}")
            for k, v in pv["runconfig"].items():
                if v["template"] != v["preview"]:
                    print(f"    runconfig {k}: {v['template']} -> {v['preview']}")
            if not pv["ok"]:
                status = 1
    except Stop as exc:
        res["stop"] = str(exc)
        print(f"STOP: {exc}")
        status = 1
    (out / "stage02_result.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(f"STAGE02 {'DONE' if status == 0 else 'NOT PASSED'} | {out}/stage02_result.json")
    return status


# ---------------------------------------------------------------- self-test
def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        # A. source checks on a minimal tree
        c = d / "CTSM"
        snippets = {
            "components/cmeps/cime_config/config_component_cesm.xml":
                '<entry id="CCSM_BGC"><valid_values>none,CO2A,CO2B,CO2C</valid_values><values>'
                '<value compset="_DATM">none</value></values><file>env_run.xml</file></entry>',
            "components/cmeps/cime_config/namelist_definition_drv.xml":
                '<entry id="flds_co2a"><values><value>.false.</value><value BGC_MODE="CO2A.*">.true.</value>'
                '</values></entry>',
            "components/cmeps/cime_config/buildnml": 'config["BGC_MODE"] = case.get_value("CCSM_BGC")\n',
            "components/cdeps/datm/cime_config/namelist_definition_datm.xml":
                '<entry id="flds_co2"><values><value>.true.</value><value datm_co2_tseries="none">.false.</value>'
                '</values></entry>',
            "components/cdeps/datm/cime_config/buildnml":
                '        streamlist.append("co2tseries.{}".format(datm_co2_tseries))\n',
            "components/cdeps/datm/datm_pres_co2_mod.F90": "    call dshr_fldList_add(fldsExport, 'Sa_co2diag')\n",
            "components/cdeps/datm/cime_config/stream_definition_datm.xml":
                '<stream_entry name="co2tseries.cmip6_20tr"><stream_meshfile><meshfile>none</meshfile>'
                '</stream_meshfile><stream_datavars><var>CO2   Sa_co2diag</var></stream_datavars><stream_mapalgo>'
                '<mapalgo>none</mapalgo></stream_mapalgo><stream_tintalgo><tintalgo>linear</tintalgo>'
                '</stream_tintalgo><stream_taxmode><taxmode>extend</taxmode></stream_taxmode></stream_entry>',
            "components/cdeps/streams/dshr_strdata_mod.F90": "! single point stream data, no action required.\n",
            "components/cdeps/cime_config/stream_cdeps.py":
                '                    if var_key == "datafiles":\n'
                '                        stream_datafiles = mod_dict[var_key]\n',
            "src/cpl/nuopc/lnd_import_export.F90":
                "    if (flds_co2a .or. flds_co2b .or. flds_co2c) then\n"
                "       call fldlist_add(fldsToLnd_num, fldsToLnd, Sa_co2prog)\n"
                "       call fldlist_add(fldsToLnd_num, fldsToLnd, Sa_co2diag)\n"
                "  call shr_sys_abort( subname//' ERROR: must have Sa_co2diag in import state if co2_type equal "
                "diagnostic')\n",
            "src/fates/main/FatesRestartInterfaceMod.F90":
                "    call this%set_restart_var(vname='fates_phen_model_date', vtype=site_int, &\n",
            "src/fates/biogeochem/EDPhysiologyMod.F90":
                "    currentSite%phen_model_date = currentSite%phen_model_date + 1\n",
        }
        for rel, txt in snippets.items():
            (c / rel).parent.mkdir(parents=True, exist_ok=True)
            (c / rel).write_text(txt)
        sc = run_source_checks(c)
        assert all(x["ok"] for x in sc) and len(sc) == len(SOURCE_CHECKS), [x for x in sc if not x["ok"]]
        (c / "components/cdeps/datm/cime_config/stream_definition_datm.xml").write_text(
            snippets["components/cdeps/datm/cime_config/stream_definition_datm.xml"].replace("extend", "cycle"))
        assert [x["id"] for x in run_source_checks(c) if not x["ok"]] == ["CO2_STREAM_SINGLE_POINT"]
        # history fields: every FATES field hifr except one daily-only field placed on the half-hourly tape
        fh = c / "src/fates/main/FatesHistoryInterfaceMod.F90"
        fl = [f for f in TAPE_DAILY + TAPE_HH if f.startswith("FATES_")]
        fh.write_text("".join(
            f"    call this%set_history_var(vname='{f}', units='kg m-2 s-1', &\n"
            f"         long='x', use_default='active', & ! note\n"
            f"         upfreq={'group_dyna_simple' if f in ('FATES_AUTORESP', 'FATES_NPP') else 'group_hifr_simple'}"
            f", ivar=ivar)\n" for f in dict.fromkeys(fl)))
        rst = c / "doc/source/users_guide/setting-up-and-running-a-case/history_fields_fates.rst"
        rst.parent.mkdir(parents=True)
        rst.write_text("".join(f"{f}    -    long name    unit  T\n" for f in TAPE_DAILY + TAPE_HH
                               if not f.startswith("FATES_") and f != "PCO2"))
        (c / "src/main").mkdir(parents=True)
        (c / "src/main/atm2lndType.F90").write_text("    call hist_addfld1d (fname='PCO2', units='Pa', &\n")
        hf = history_field_check(c)
        assert all(r["ok"] for r in hf["rows"]), [r for r in hf["rows"] if not r["ok"]]
        assert next(r for r in hf["rows"] if r["field"] == "PCO2")["where"] == "src/main/atm2lndType.F90"
        fh.write_text(fh.read_text().replace("vname='FATES_NEP', units='kg m-2 s-1', &\n         long='x', "
                                             "use_default='active', & ! note\n         upfreq=group_hifr_simple",
                                             "vname='FATES_NEP', units='kg m-2 s-1', &\n         long='x', "
                                             "use_default='active', & ! note\n         upfreq=group_dyna_simple"))
        bad = [(r["tape"], r["field"]) for r in history_field_check(c)["rows"] if not r["ok"]]
        assert bad == [("halfhourly", "FATES_NEP")], bad
        # B. CO2 file
        csv = d / "co2.csv"
        csv.write_text("# NOAA\n# comment\nyear,mean,unc\n1979,336.85,0.10\n1980,338.91,0.07\n1981,340.11,0.08\n")
        rows = read_noaa(csv)
        assert rows == {1979: 336.85, 1980: 338.91, 1981: 340.11}
        assert year_axis(1979, 1979) == (182.5, 0, 365) and year_axis(1980, 1979) == (548.0, 365, 731)
        assert year_axis(1752, 1750)[0] == 913.0 and year_axis(1751, 1750)[0] == 547.5   # layout file stamps
        dest = d / "co2_adopted" / "x.nc"
        r1 = install_co2(rows, dest, "abc")
        assert r1["status"] == "INSTALLED" and r1["n_years"] == 3, r1
        assert os.geteuid() == 0 or not os.access(dest, os.W_OK)
        assert json.loads(Path(r1["receipt"]).read_text())["sha256"] == r1["sha256"]
        b1 = dest.read_bytes()
        r2 = install_co2(rows, dest, "abc")
        assert r2["status"] == "EXISTING_VERIFIED" and r2["sha256"] == r1["sha256"] and dest.read_bytes() == b1
        try:
            verify_co2_file(dest, {**rows, 1981: 341.0})
            raise AssertionError("value change not detected")
        except Stop:
            pass
        from netCDF4 import Dataset
        with Dataset(str(dest)) as ds:
            assert ds.file_format == "NETCDF3_CLASSIC" and ds.variables["time"].units == "days since 1979-01-01 00:00:00"
            assert ds.variables["date"][:].tolist() == [19790702, 19800702, 19810702]
            assert ds.variables["time_bnds"][1].tolist() == [365.0, 731.0]
        st = stream_co2_stats(rows, 1980)
        assert abs(st["jan1"] - 0.5 * (336.85 + 338.91)) < 1e-9
        assert abs(st["annual_mean"] - (0.125 * 336.85 + 0.75 * 338.91 + 0.125 * 340.11)) < 1e-9
        assert abs(stream_co2_stats(rows, 1979)["jan1"] - 336.85) < 1e-9       # held before the first stamp
        # C. continuity on a fake finished case
        case = d / "cases" / "XX-Abc_FIXNC_NORMAL400"
        (case / "CaseDocs").mkdir(parents=True)
        arch = d / "archive" / case.name / "rest" / "2381-01-01-00000"
        arch.mkdir(parents=True)
        (case / "env_run.xml").write_text(
            '<file><entry id="RUN_STARTDATE" value="1981-01-01"></entry><entry id="CCSM_CO2_PPMV" value="338.91">'
            '</entry><entry id="CLM_CO2_TYPE" value="constant"></entry><entry id="DOUT_S_ROOT" value="'
            + str(d / "archive" / case.name) + '"></entry></file>')
        (case / "CaseDocs/datm.streams.xml").write_text(
            '<file id="stream"><stream_info name="presaero.clim_2000"><year_first>2000</year_first>'
            '<datafiles><file>/a.nc</file></datafiles></stream_info>'
            '<stream_info name="CLM_USRDAT.UNSET"><taxmode>cycle</taxmode><year_first>1980</year_first>'
            '<year_last>1981</year_last><year_align>1980</year_align><datafiles><file>/m/1980.nc</file>'
            '<file>/m/1981.nc</file></datafiles><datavars><var>FSDS   Faxa_swdn</var></datavars></stream_info></file>')
        cont = continuity(d / "cases", rows)
        assert len(cont) == 1 and cont[0]["first_forcing_year"] == 1980 and cont[0]["spinup_minus_noaa"] == 0.0
        assert cont[0]["jan1_minus_spinup"] == round(0.5 * (336.85 + 338.91) - 338.91, 3)
        s = datm_streams(case / "CaseDocs/datm.streams.xml")
        assert met_stream(s)[0] == "CLM_USRDAT.UNSET" and s["CLM_USRDAT.UNSET"]["vars"] == ["FSDS Faxa_swdn"]
        assert s["CLM_USRDAT.UNSET"]["files"] == ["/m/1980.nc", "/m/1981.nc"]
        # D. pure preview helpers
        nl = d / "lnd_in"
        nl.write_text("&clm_inparm\n co2_type = 'constant'\n hist_fincl1 = 'A','B',\n   'C'\n fsurdat = 'x.nc'\n/\n")
        p = parse_namelist(nl)
        assert p == {"co2_type": "'constant'", "hist_fincl1": "'A','B', 'C'", "fsurdat": "'x.nc'"}, p
        assert dict_diff(p, {**p, "co2_type": "'diagnostic'"}) == ["co2_type"]
        unl = ("! keep me\nfsurdat = 'x.nc'\nhist_fincl1 = 'TOTSOMC','TOTSOMN',\n  'TLAI'\nhist_nhtfrq = -24\n"
               "use_fates = .true.\nfinidat = '/old/AD.clm2.r.nc'\n")
        new = rewrite_user_nl_clm(unl, "/arch/N.clm2.r.2802-01-01-00000.nc", 48)
        keys = [m.group(1) for m in re.finditer(r"^([a-z_0-9]+)\s*=", new, re.M)]
        assert keys == ["fsurdat", "use_fates", "finidat", "hist_fincl1", "hist_fincl2", "hist_nhtfrq", "hist_mfilt"], keys
        assert "'TLAI'\n" not in new.split("! ---- observation")[0] and "! keep me" in new and "/old/AD" not in new
        assert "hist_mfilt = 365, 17520" in new and f"hist_fincl2 = {fincl(TAPE_HH)}" in new
        assert co2_stream_block("/c/x.nc", (1979, 2025)).splitlines()[1:] == [
            "co2tseries.cmip6_20tr:datafiles = /c/x.nc", "co2tseries.cmip6_20tr:year_first = 1979",
            "co2tseries.cmip6_20tr:year_last = 2025", "co2tseries.cmip6_20tr:year_align = 1979"]
        rcf = d / "nuopc.runconfig"
        rcf.write_text("ALLCOMP_attributes::\n     flds_co2a = .true.\n::\nCLOCK_attributes::\n"
                       "     start_ymd = 20020101\n     stop_n = 19\n::\n")
        assert parse_runconfig(rcf) == {"flds_co2a": ".true.", "start_ymd": "20020101", "stop_n": "19"}
        assert set(TAPE_DAILY[:7]) == {"TOTSOMC", "TOTSOMN", "TLAI", "FATES_GPP", "FATES_NPP", "TWS", "H2OSNO"}
    print("STAGE02 SELF-TEST PASS (source checks, history fields and upfreq, NOAA CO2 file layout / values / "
          "no-overwrite install, stream CO2 stats, continuity, namelist / user_nl / runconfig helpers; no IRIDIS)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--noaa-csv")
    ap.add_argument("--ctsm", default=str(CTSM))
    ap.add_argument("--cases-root", default=str(CASES))
    ap.add_argument("--co2-dest", default=str(CO2_DEST))
    ap.add_argument("--template-case")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.noaa_csv:
        ap.error("--noaa-csv is required")
    return run(a)


if __name__ == "__main__":
    sys.exit(main())

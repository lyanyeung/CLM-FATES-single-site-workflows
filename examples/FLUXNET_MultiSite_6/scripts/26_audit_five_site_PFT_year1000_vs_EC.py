#!/usr/bin/env python3
"""Read-only comparison for five completed FLUXNET_MultiSite_6 1000-year spin-ups.

Input (existing IRIDIS6 files only):
  - Original ICOS/EUF tower BIF per station
  - Original <SITE>_FATES_SPINUP500/CaseDocs/lnd_in and active inputs
  - Point surfdata with PCT_NAT_PFT (CLM host PFT, not FATES PFT)
  - Exactly the 1000th model calendar year CLM h0a history FATES_*_PF
  - Actual FATES .json (or legacy .nc) parameter file for candidate PFT names
  - Optional 1000-year coordinated restart; model-year clock differs by site

Five-site report and individual CSV/JSON under HOME; never modifies inputs or jobs.
Already continued 1000->3000-y model years MUST NOT be used here.
Use --include-de-hai to include the DE-Hai known reference in the comparison.
The carbon share from FATES_VEGC_PF is NOT a PFT area fraction.
FATES PFT names cannot be inferred from CLM 15/16-category indices.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, chartostring

SITES = {
    "RU-Fyo": (1998, "EUF_RU-Fyo_FLUXNET_1998-2025_v1.3_r1", "ENF"),
    "DE-Tha": (1996, "ICOS_DE-Tha_FLUXNET_1996-2026_v1.3_r1", "ENF"),
    "DK-Sor": (1996, "ICOS_DK-Sor_FLUXNET_1996-2024_v1.3_r1", "DBF"),
    "NL-Loo": (1997, "ICOS_NL-Loo_FLUXNET_1997-2026_v1.3_r1", "ENF"),
    "IL-Yat": (2000, "EUF_IL-Yat_FLUXNET_2000-2024_v1.3_r1", "ENF"),
    "DE-Hai": (2000, "ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1", "DBF"),
}
DEFAULT_FIVE = ("RU-Fyo", "DE-Tha", "DK-Sor", "NL-Loo", "IL-Yat")
SITE = "RU-Fyo"
CASE_NAME = "RU-Fyo_FATES_SPINUP500"
PKG = SITES[SITE][1]
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CASES = ROOT / "cases"
SITE_DIR = ROOT / "sites/MY_EC_SITE" / SITE
ARCH = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive") / CASE_NAME
END = 2998  # First simulated year 1998, 1000 elapsed years ends at 2998
PF_FIELDS = ("FATES_VEGC_PF", "FATES_CROWNAREA_PF", "FATES_BASALAREA_PF",
             "FATES_NPLANT_PF", "FATES_LAI_PF", "FATES_GPP_PF", "FATES_NPP_PF")
OBSERVED_FLUXNET_IGBP = "ENF"  # only a repository expectation; BIF is authoritative


def say(*parts):
    print(*parts, flush=True)


def choose_one(paths, kind, required=False):
    distinct = sorted({p.resolve() for p in paths if p.is_file()})
    if len(distinct) != 1:
        msg = f"{kind}: expected one existing candidate; got {len(distinct)}"
        if distinct:
            msg += "\n  " + "\n  ".join(map(str, distinct[:12]))
        if required:
            raise RuntimeError(msg)
        say("NOTE", msg)
        return None
    return distinct[0]


def parse_namelist(path):
    if not path.is_file():
        return {}
    out = {}
    regex = re.compile(r"^\s*([a-z_][a-z_0-9]*)\s*=\s*(.+)$", re.I)
    for line in path.read_text(errors="replace").splitlines():
        # Never decode shell variables or execute a namelist.
        m = regex.match(line)
        if m:
            token = m.group(2).split("!", 1)[0].strip().rstrip(",")
            if token[:1] in ("'", '"'):
                token = token[1:].split(token[0], 1)[0]
            out[m.group(1).lower()] = token
    return out


def resolve_model_path(raw, context):
    if not raw:
        return None
    raw = raw.strip().strip("'\"")
    raw = raw.replace("$DIN_LOC_ROOT", str(ROOT / "inputdata"))
    raw = raw.replace("\${DIN_LOC_ROOT}", str(ROOT / "inputdata"))
    p = Path(raw)
    if p.is_absolute():
        return p
    if "/" in raw:
        return context / p
    return context / p


def values(v):
    return np.ma.filled(np.ma.asarray(v[:], dtype="float64"), np.nan)


def site_pft_vector(ds):
    v = ds.variables.get("PCT_NAT_PFT")
    if v is None:
        raise RuntimeError("No PCT_NAT_PFT in selected surface.")
    axes = [i for i, d in enumerate(v.dimensions) if "pft" in d.lower()]
    if len(axes) != 1:
        raise RuntimeError(f"Ambiguous CLM PFT axis {v.dimensions}")
    a = values(v)
    other = [a.shape[i] for i in range(a.ndim) if i != axes[0]]
    if any(n != 1 for n in other):
        raise RuntimeError(f"Not a single-point surface: {v.dimensions} {a.shape}")
    x = np.moveaxis(a, axes[0], 0).reshape(-1)
    if not np.isfinite(x).all() or (x < -1e-5).any():
        raise RuntimeError("Invalid CLM surface PCT_NAT_PFT")
    return x, v.dimensions


def original_bif():
    raw = SITE_DIR / "forcing/raw" / PKG
    matches = list(raw.glob("*_FLUXNET_BIF_*.csv"))
    p = choose_one(matches, "original ICOS tower BIF", required=True)
    records = []
    with p.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for item in reader:
            key = (item.get("VARIABLE") or "").strip().upper()
            if key in ("IGBP", "LOCATION_LAT", "LOCATION_LONG") or any(
                    tag in key for tag in ("SPECIES", "VEGETATION", "CANOPY_HEIGHT",
                                          "DOMINANT", "TREE", "FOREST", "AGE")):
                records.append({"variable": key,
                                "value": (item.get("DATAVALUE") or "").strip(),
                                "date": (item.get("DATE") or "").strip(),
                                "group": (item.get("GROUP_ID") or "").strip(),
                                "source_file": str(p)})
    igbp = sorted({x["value"].upper() for x in records
                   if x["variable"] == "IGBP" and x["value"]})
    say("\n==== 1. ORIGINAL ICOS EC BIF ====")
    say("Original BIF:", p)
    say("IGBP:", igbp or "MISSING")
    if not igbp:
        say("WARNING: BIF lacks IGBP; do not infer the observed PFT.")
    elif igbp != [OBSERVED_FLUXNET_IGBP]:
        say("REVIEW: BIF IGBP differs from published FLUXNET siteinfo DBF.")
    for x in records[:70]:
        say(f"  {x['variable']:<30} {x['value']:<25} {x['date']}")
    return records, igbp


def actual_surface(nml):
    requested = resolve_model_path(nml.get("fsurdat"), CASES / CASE_NAME)
    candidates = list((SITE_DIR / "subset_data").rglob("surfdata*.nc"))
    if requested and requested.is_file():
        chosen = requested.resolve()
        say("Actual surface selected by lnd_in: VERIFIED", chosen)
    else:
        say("NOTE: lnd_in fsurdat absent/unresolved:", requested)
        chosen = choose_one(candidates, "site surface fallback", required=True)
        say("FALLBACK site surface; cannot establish it is the active surface:", chosen)
    rows = []
    land = {}
    with Dataset(chosen) as ds:
        x, dims = site_pft_vector(ds)
        for key in ("PCT_NATVEG", "PCT_CROP", "PCT_WETLAND",
                    "PCT_LAKE", "PCT_GLACIER", "PCT_URBAN"):
            if key in ds.variables:
                a = values(ds[key]).ravel()
                land[key] = float(np.nansum(a)) if key == "PCT_URBAN" else (
                    float(a[0]) if a.size else None)
        for i, val in enumerate(x):
            rows.append(dict(index_0based=i, index_1based=i+1,
                             pct_of_natural_landunit=float(val),
                             name="NOT_MAPPED_CLM_SURFACE_PFT"))
        meta = {k: str(getattr(ds, k)) for k in ds.ncattrs()
                if any(x in k.lower() for x in ("source", "creation", "title", "surf"))}
    say("\n==== 2. HOST CLM SURFACE (NOT FATES PFT) ====")
    say("Active/fallback surface:", chosen)
    say("Original source used in site generator:",
        "surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc")
    say("Actual CLM PFT dimensions:", dims, "number of classes:", len(rows))
    say("CLM PFT entries deliberately unlabelled until dimension mapping is verified.")
    say("Landunit proportions (% of site grid cell):", land)
    say("PCT_NAT_PFT sum (% of natural landunit):", round(sum(x), 5))
    for item in sorted(rows, key=lambda r: -r["pct_of_natural_landunit"])[:12]:
        if item["pct_of_natural_landunit"] > 0.001:
            say(f"  surface index {item['index_0based']:2d}: "
                f"{item['pct_of_natural_landunit']:.2f}% of natural landunit")
    return rows, land, meta, str(chosen), bool(requested and requested.is_file())


def fates_parameters(nml):
    """Read the actual parameter file, which may be JSON or NetCDF.

    FATES PFT rows are candidate functional types in the parameter file,
    NOT the PFTs proven alive at model year 1000. For Full FATES, the
    host-to-FATES fixed-biogeography map does not set the PFT area shares.
    """
    raw = nml.get("fates_paramfile")
    f = resolve_model_path(raw, CASES / CASE_NAME) if raw else None
    result = {"configured": raw, "resolved": str(f) if f else None}
    say("\n==== 3. ACTIVE FATES CONFIGURATION ====")
    for k, v in sorted(nml.items()):
        if "fates" in k or k in ("fsurdat", "finidat"):
            say(f"  {k} = {v}")
    if not f or not f.is_file():
        say("WARNING: fates_paramfile missing/unresolvable in CaseDocs/lnd_in.")
        say("PFT candidates and names cannot be established without it.")
        return result
    f = f.resolve()
    result["path"] = str(f)
    result["format"] = f.suffix.lower()
    result["full_fates_dynamic_competition_flags"] = {
        k: nml.get(k, "NOT_EXPLICITLY_LISTED")
        for k in ("use_fates", "use_fates_sp",
                  "use_fates_fixed_biogeog", "use_fates_nocomp",
                  "use_fates_ed_st3", "use_fates_ed_prescribed_phys")
    }

    def extract_parameter(entry, pft_count):
        """Extract one numeric/string value per PFT; skip multivalued dimensions."""
        if not isinstance(entry, dict) or "data" not in entry:
            return None
        dims = entry.get("dims", [])
        if dims.count("fates_pft") != 1:
            return None
        x = np.asarray(entry["data"])
        axis = dims.index("fates_pft")
        if x.ndim != len(dims) or x.shape[axis] != pft_count:
            raise RuntimeError("Parameter dimensions conflict with fates_pft: "
                               + str(dims) + " " + str(x.shape))
        x = np.moveaxis(x, axis, 0).reshape(pft_count, -1)
        if x.shape[1] != 1:
            return None  # Do not arbitrarily select one size/age/organ class.
        result_values = []
        for value in x[:, 0]:
            if isinstance(value, np.generic):
                value = value.item()
            result_values.append(value)
        return result_values

    def to_json_value(value):
        if isinstance(value, np.generic):
            return value.item()
        return value

    if f.suffix.lower() == ".json":
        with f.open(encoding="utf-8") as inp:
            doc = json.load(inp)
        dims = doc.get("dimensions")
        params = doc.get("parameters")
        if not isinstance(dims, dict) or not isinstance(params, dict):
            raise RuntimeError("FATES JSON expected top-level dimensions and parameters")
        count = dims.get("fates_pft")
        if not isinstance(count, int) or count < 1:
            raise RuntimeError("Invalid fates_pft dimension in actual FATES JSON")
        names = extract_parameter(params.get("fates_pftname"), count)
        if names is None:
            names = [f"UNNAMED_FATES_PFT_{k+1}" for k in range(count)]
        result["dimensions"] = dims
        result["pft_count"] = count
        result["parameter_count"] = len(params)
        result["pft_names"] = names
        chosen = (
            "fates_woody", "fates_leaf_slatop", "fates_leaf_long",
            "fates_leaf_vcmax25top", "fates_wood_density",
            "fates_recruit_initd", "fates_phen_evergreen",
            "fates_phen_season_decid", "fates_phen_evergreen_habit"
        )
        traits = {}
        for key in chosen:
            if key in params:
                v = extract_parameter(params[key], count)
                if v is not None:
                    traits[key] = v
        result["pft_traits"] = traits
        mapping = params.get("fates_hlm_pft_map", {})
        if isinstance(mapping, dict):
            md = mapping.get("dims", [])
            if md == ["fates_hlm_pftno", "fates_pft"]:
                result["hlm_pft_mapping_available"] = True
                result["hlm_pft_mapping_interpretation"] = (
                    "Fixed-biogeography HLM-to-FATES mapping only. "
                    "Not a Full FATES dynamic-PFT area percentage.")
            else:
                result["hlm_pft_mapping_available"] = False
    elif f.suffix.lower() in (".nc", ".nc4"):
        with Dataset(f) as ds:
            count = len(ds.dimensions["fates_pft"])
            names = [f"UNNAMED_FATES_PFT_{k+1}" for k in range(count)]
            if "fates_pftname" in ds.variables:
                x = ds["fates_pftname"][:]
                if getattr(x, "dtype", None) is not None and x.dtype.kind == "S":
                    x = chartostring(x)
                flat = np.asarray(x).reshape(-1)
                if len(flat) == count:
                    names = [v.decode().strip() if isinstance(v, bytes)
                             else str(v).strip() for v in flat]
            result["dimensions"] = {k: len(v) for k, v in ds.dimensions.items()}
            result["pft_count"] = count
            result["pft_names"] = names
            result["parameter_count"] = len(ds.variables)
            result["pft_traits"] = {}
            for key in ("fates_woody", "fates_leaf_slatop", "fates_leaf_long",
                        "fates_wood_density", "fates_recruit_initd"):
                if key not in ds.variables:
                    continue
                var = ds[key]
                if var.dimensions == ("fates_pft",):
                    result["pft_traits"][key] = [
                        to_json_value(v) for v in values(var).reshape(-1)]
    else:
        say("WARNING: FATES parameter format not supported:", f.suffix)
        say("Will continue to final-history and checkpoint checks.")
        return result

    result["pft_rows"] = []
    for i, name in enumerate(result["pft_names"]):
        row = {
            "pft_slot_1based": i + 1,
            "pft_name": str(name).strip(),
            "status": "CANDIDATE_TYPE_IN_PARAMETER_FILE_NOT_FINAL_PRESENCE",
        }
        for trait, vals in result["pft_traits"].items():
            row[trait] = to_json_value(vals[i])
        result["pft_rows"].append(row)
    say("Actual parameter file:", f)
    say("File format:", result["format"],
        "| FATES candidate PFT count:", result["pft_count"],
        "| parameters:", result["parameter_count"])
    say("PFT table (candidate types; NOT simulated end-state occupancy):")
    for row in result["pft_rows"]:
        extra = " ".join(
            f"{k.removeprefix('fates_')}={v}"
            for k, v in row.items() if k.startswith("fates_"))
        say(f"  FATES PFT {row['pft_slot_1based']:2d}: "
            f"{row['pft_name']:<43} {extra}")
    say("IMPORTANT: fates_hlm_pft_map (if present) is for fixed-biogeography,")
    say("not the current Full FATES land-cover fractions.")
    return result


def final_history():
    possible_hists = [
        ARCH / "lnd/hist",
        Path("/iridisfs/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive") /
            CASE_NAME / "lnd/hist",
        Path("/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/"
             "FLUXNET_MultiSite_6") / SITE / CASE_NAME / "archive/lnd/hist",
    ]
    # Annual tape h0a ONLY. Never use year 3000 of an extended spin-up.
    names, hist = [], None
    for candidate in possible_hists:
        found = sorted(candidate.glob(f"{CASE_NAME}.clm2.h0a.{END-1}-*.nc"))
        if found:
            names, hist = found, candidate
            break
    if not names:
        say("\n==== 4. FINAL FATES PFT HISTORY: NOT AVAILABLE ====")
        say("No year-1000 history for calendar year", END-1,
            "in scanned Scratch/RFS directories:", [str(p) for p in possible_hists])
        say("Check whether history has been transferred to Research Filestore.")
        return [], {}, None
    p = choose_one(names, "final-year history", required=False)
    if p is None:
        say("Multiple final-year files; do not randomly mix history tape types.")
        return [], {}, None
    say("\n==== 4. FULL FATES FINAL MODEL YEAR PFT OUTPUT ====")
    say("Selected archived history:", p)
    out = []
    shapes = {}
    with Dataset(p) as ds:
        available = sorted(x for x in ds.variables
                           if x.startswith("FATES_") and
                           (x.endswith("_PF") or x.endswith("_SZPF")))
        say("FATES PFT-resolved history fields present:", available[:70])
        for name in PF_FIELDS:
            if name not in ds.variables:
                continue
            var = ds[name]
            axes = [i for i, d in enumerate(var.dimensions)
                    if "pft" in d.lower()]
            time_axes = [i for i, d in enumerate(var.dimensions)
                         if d.lower() == "time"]
            if len(axes) != 1 or len(time_axes) != 1:
                say("SKIP (ambiguous axis):", name, var.dimensions)
                continue
            x = values(var)
            # Site-level _PF, other than the time & pft axes, MUST be singleton.
            extras = [x.shape[i] for i in range(x.ndim)
                      if i not in (axes[0], time_axes[0])]
            if any(k != 1 for k in extras):
                say("SKIP (non-singleton extra dimensions):", name, var.dimensions)
                continue
            y = np.nanmean(np.moveaxis(x, (time_axes[0], axes[0]), (0, 1)),
                           axis=0).reshape(-1)
            shapes[name] = {"dimensions": var.dimensions, "units": getattr(var, "units", ""),
                            "values": [None if not np.isfinite(z) else float(z) for z in y]}
            for k, v in enumerate(y, 1):
                out.append(dict(field=name, pft_slot_1based=k, mean_final_year=float(v),
                                units=getattr(var, "units", ""),
                                interpretation="Mean over last model-year records"))
            say(name, "units=", getattr(var, "units", "unknown"),
                "model year mean per FATES PFT:", np.round(y, 6).tolist())
            if name == "FATES_VEGC_PF":
                total = np.nansum(y)
                if total > 0:
                    say("  PFT fraction of *living vegetation carbon* (not area %):",
                        np.round(y / total * 100, 2).tolist())
                else:
                    say("  Total VEGC_PF zero or invalid; no meaningful carbon share.")
    if not shapes:
        say("No usable _PF site-level history field in the existing h0a file.")
        say("The historical 1000-year outputs cannot reconstruct final PFT composition.")
        say("Check FATES_VEGC_PF/FATES_NPLANT_SZPF history settings before a future run.")
    return out, shapes, str(p)


def check_1000_restart():
    stamp = f"{END}-01-01-00000"
    folder = ARCH / "rest" / stamp
    defects = []
    for comp, prefix in (("cpl", "cpl"), ("atm", "datm"), ("lnd", "clm2")):
        name = f"{CASE_NAME}.{prefix}.r.{stamp}.nc"
        file = folder / name
        ptr = folder / f"rpointer.{comp}.{stamp}"
        if not file.is_file() or file.stat().st_size < 1024:
            defects.append(f"{comp} restart missing/small")
        if not ptr.is_file():
            defects.append(f"{comp} dated pointer missing")
        elif not ptr.read_text(errors="replace").strip().removeprefix("./") == name:
            defects.append(f"{comp} dated pointer mismatch")
    return {"checkpoint_path": str(folder),
            "structurally_complete": not defects, "issues": defects}


def audit_site(report_dir):
    # Verify original CIME model clock before selecting the 1000th year.
    case = CASES / CASE_NAME
    env = case / "env_run.xml"
    if not env.is_file():
        raise RuntimeError("Missing case env_run.xml: " + str(env))
    root = ET.parse(env).getroot()
    starts = [e.get("value") for e in root.iter("entry")
              if e.get("id") == "RUN_STARTDATE"]
    expected = f"{SITES[SITE][0]}-01-01"
    if len(starts) != 1 or starts[0] != expected:
        raise RuntimeError(f"Unexpected RUN_STARTDATE {starts}, expected {expected}; "
                           "refusing to select wrong model year 1000")
    nml = parse_namelist(case / "CaseDocs/lnd_in")
    if not nml:
        raise RuntimeError("Missing case CaseDocs/lnd_in: " + str(case))
    records, igbp = original_bif()
    surfrows, land, surface_meta, surffile, active = actual_surface(nml)
    fates = fates_parameters(nml)
    pfrows, pf, histfile = final_history()
    if pfrows and fates.get("pft_names"):
        for row in pfrows:
            n = row["pft_slot_1based"] - 1
            names = fates["pft_names"]
            row["pft_name"] = names[n] if n < len(names) else "UNMAPPED_SLOT"
    else:
        for row in pfrows:
            row["pft_name"] = "NOT_VERIFIED"
    check = check_1000_restart()
    say("\n==== 5. 1000-YEAR RESTART ====")
    say(json.dumps(check, indent=2))
    if not check["structurally_complete"]:
        say("CAVEAT: Could not independently confirm final 1000-year checkpoint here.")
    say("\n==== 6. SCIENTIFIC COMPARISON ====")
    say("Observed EC BIF IGBP:", igbp or "unknown",
        "| repository expected IGBP:", OBSERVED_FLUXNET_IGBP)
    say("FATES crop settings:",
        {k:nml.get(k,"UNLISTED") for k in
         ("create_crop_landunit","use_crop","use_fates","use_fates_sp",
          "use_fates_fixed_biogeog","use_fates_nocomp")})
    say("CLM coarse surface is not a species observation.")
    say("FATES PFTs are set by fates_paramfile and model configuration,")
    say("NOT by indexing the PCT_NAT_PFT vector as FATES PFTs.")
    say("FATES vegetation carbon shares are NOT PFT fractional land cover.")
    report_dir.mkdir(parents=True, exist_ok=True)
    def csvout(name, rows, columns):
        with (report_dir / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    csvout("01_original_tower_BIF.csv", records,
           ["variable", "value", "date", "group", "source_file"])
    csvout("02_CLM_surface_natural_PFT.csv", surfrows,
           ["index_0based", "index_1based", "pct_of_natural_landunit", "name"])
    csvout("03_FATES_final_1000yr_PFT_fields.csv", pfrows,
           ["field", "pft_slot_1based", "pft_name", "mean_final_year",
            "units", "interpretation"])
    pft_rows = fates.get("pft_rows", [])
    pft_fields = ["pft_slot_1based", "pft_name", "status"]
    if pft_rows:
        pft_fields.extend(k for k in pft_rows[0] if k.startswith("fates_"))
    csvout("05_FATES_parameter_PFT_table.csv", pft_rows, pft_fields)
    report = dict(site=SITE, case=CASE_NAME, original_igbp=igbp,
                  surface_file=surffile, surface_active_path_verified=active,
                  landunits=land, surface_metadata=surface_meta,
                  fates_configuration=fates, final_history_file=histfile,
                  fates_final_fields=pf, final_restart=check,
                  warnings=["CLM surface PFT indices and FATES PFT indices differ.",
                            "An FATES carbon share is not an area share.",
                            "BIF IGBP is a landcover class, not a species/PFT trait vector.",
                            "Absence of *_PF history does not prove absence of dynamic FATES PFTs."])
    (report_dir / "04_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str)+"\n")
    say("\nREAD-ONLY completed. Small reports:", report_dir)
    say("No data, cases, NetCDF, restart files or Slurm jobs were modified.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-de-hai", action="store_true",
                        help="Include DE-Hai as a benchmark in the same six-site table")
    parser.add_argument("--sites", nargs="+", choices=list(SITES), default=None)
    parser.add_argument("--report-dir", type=Path,
                        default=Path.home() / "FLUXNET_MultiSite_6_PFT_year1000")
    args = parser.parse_args()
    selected = (args.sites if args.sites is not None else
                list(DEFAULT_FIVE) + (["DE-Hai"] if args.include_de_hai else []))
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for site in selected:
        try:
            global SITE, PKG, CASE_NAME, SITE_DIR, ARCH, END, OBSERVED_FLUXNET_IGBP
            SITE = site
            start, PKG, OBSERVED_FLUXNET_IGBP = SITES[site]
            END = start + 1000
            CASE_NAME = site + "_FATES_SPINUP500"
            SITE_DIR = ROOT / "sites/MY_EC_SITE" / site
            ARCH = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive") / CASE_NAME
            say("\n" + "="*80)
            say("SITE", SITE, "| exact 1000th year =", END - 1,
                "| do not use 3000-year continuation")
            report = audit_site(args.report_dir/site)
            config = report["fates_configuration"]
            names = config.get("pft_names", [])
            pf = report["fates_final_fields"].get("FATES_VEGC_PF", {})
            vals = pf.get("values", [])
            pairs = [(i, float(v)) for i, v in enumerate(vals)
                     if v is not None and np.isfinite(v) and v >= 0]
            if len(pairs) != len(names) or len(names) == 0:
                dominant = "UNAVAILABLE"
                share = ""
                expected_share = ""
                status = "NO_VALID_PFT_VEGC"
            elif sum(v for _, v in pairs) <= 0:
                dominant = "ZERO_CARBON"
                share = ""
                expected_share = ""
                status = "ZERO_VEGC"
            else:
                total = sum(v for _, v in pairs)
                imax, vmax = max(pairs, key=lambda x: x[1])
                dominant = names[imax]
                share = round(100*vmax/total, 2)
                expected_names = {
                    "ENF": ("needleleaf_evergreen_extratrop_tree",),
                    "DBF": ("broadleaf_colddecid_extratrop_tree",),
                }
                observed = report["original_igbp"]
                allowed = expected_names.get(observed[0], ()) if len(observed) == 1 else ()
                expected_share = (round(100*sum(v for i,v in pairs
                                                if names[i] in allowed)/total, 2)
                                  if allowed else "")
                status = ("DOMINANT_PFT_MATCHES_IGBP" if dominant in allowed
                          else "DOMINANT_PFT_DIFFERENT_OR_IGBP_UNKNOWN")
            flags = parse_namelist(CASES/CASE_NAME/"CaseDocs/lnd_in")
            merged = (flags.get("create_crop_landunit", "").lower() == ".false."
                      and flags.get("use_crop", "").lower() == ".false."
                      and flags.get("use_fates", "").lower() == ".true.")
            row = dict(site=site, BIF_IGBP=";".join(report["original_igbp"]),
                       expected_IGBP=OBSERVED_FLUXNET_IGBP,
                       PCT_NATVEG_pct=report["landunits"].get("PCT_NATVEG"),
                       PCT_CROP_pct=report["landunits"].get("PCT_CROP"),
                       crop_merged_at_init=(merged and
                            flags.get("use_fates_sp","").lower() == ".false."),
                       year1000_calendar=END-1,
                       year1000_history_found=bool(report["final_history_file"]),
                       fates_candidate_PFTs=len(names),
                       dominant_FATES_PFT=dominant,
                       dominant_VEGC_share_pct=share,
                       observed_expected_PFT_VEGC_share_pct=expected_share,
                       igbp_functional_type_status=status)
            summary.append(row)
            say("SUMMARY:", row)
        except Exception as exc:
            err = type(exc).__name__ + ": " + str(exc)
            say("ERROR", site, err)
            summary.append(dict(site=site, igbp_functional_type_status="INCOMPLETE_AUDIT",
                                error=err))
    fields = ("site BIF_IGBP expected_IGBP PCT_NATVEG_pct PCT_CROP_pct "
              "crop_merged_at_init year1000_calendar year1000_history_found "
              "fates_candidate_PFTs dominant_FATES_PFT dominant_VEGC_share_pct "
              "observed_expected_PFT_VEGC_share_pct "
              "igbp_functional_type_status error").split()
    dest = args.report_dir/"00_five_site_PFT_vs_EC_summary.csv"
    with dest.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary)
    say("\n===== FIVE-SITE YEAR-1000 RESULT =====")
    for r in summary:
        say("{site:<7} EC={BIF_IGBP:<5} crop={PCT_CROP_pct!s:<9} "
            "FATES={dominant_FATES_PFT:<42} share={dominant_VEGC_share_pct!s:<7} "
            "{igbp_functional_type_status}".format(
                site=r["site"], BIF_IGBP=r.get("BIF_IGBP","?"),
                PCT_CROP_pct=r.get("PCT_CROP_pct","?"),
                dominant_FATES_PFT=r.get("dominant_FATES_PFT","?"),
                dominant_VEGC_share_pct=r.get("dominant_VEGC_share_pct","?"),
                igbp_functional_type_status=r["igbp_functional_type_status"]))
    say("SUMMARY CSV:", dest)
    say("Interpretation: vegetation-carbon share != land-cover area. "
        "Functional type match != scientific convergence.")
    say("READ ONLY: CIME, models and Slurm jobs unchanged.")
    return 1 if any(x["igbp_functional_type_status"] == "INCOMPLETE_AUDIT"
                    for x in summary) else 0


if __name__ == "__main__":
    raise SystemExit(main())

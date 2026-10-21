#!/usr/bin/env python3
"""Read-only DE-Hai tower BIF vs CLM surface vs actual FATES PFT audit.

Input (existing IRIDIS6 files only):
  - Original ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1 BIF
  - DE-Hai_FATES_SPINUP500/CaseDocs/lnd_in and case surface/parameter paths
  - Point surfdata with PCT_NAT_PFT (CLM host PFT, not FATES PFT)
  - Optional final year archived CLM history FATES_*_PF
  - Actual FATES .json (or legacy .nc) parameter file for candidate PFT names
  - Optional coordinated 3000-01-01 restart (1000 elapsed years since 2000)

Outputs small CSV/JSON reports in HOME; never modifies inputs or jobs.
The carbon share from FATES_VEGC_PF is NOT a PFT area fraction.
FATES PFT names cannot be inferred from CLM 15/16-category indices.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np
from netCDF4 import Dataset, chartostring

SITE = "DE-Hai"
CASE_NAME = "DE-Hai_FATES_SPINUP500"
PKG = "ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CASES = ROOT / "cases"
SITE_DIR = ROOT / "sites/MY_EC_SITE" / SITE
ARCH = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive") / CASE_NAME
END = 3000  # 2000 startup + 1000 elapsed model years
PF_FIELDS = ("FATES_VEGC_PF", "FATES_CROWNAREA_PF", "FATES_BASALAREA_PF",
             "FATES_NPLANT_PF", "FATES_LAI_PF", "FATES_GPP_PF", "FATES_NPP_PF")
OBSERVED_FLUXNET_IGBP = "DBF"  # cross-check against the actual BIF; not an imposed value


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
    hist = ARCH / "lnd/hist"
    names = list(hist.glob(f"{CASE_NAME}.clm2.h0a.{END-1}-*.nc"))
    if not names:
        names = list(hist.glob(f"{CASE_NAME}.clm2.h0*.{END-1}-*.nc"))
    if not names:
        say("\n==== 4. FINAL FATES PFT HISTORY: NOT AVAILABLE ====")
        say("No final model year", END-1, "history in", hist)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-dir", type=Path,
                    default=Path.home() / "DE_Hai_PFT_comparison")
    args = ap.parse_args()
    nml = parse_namelist(CASES / CASE_NAME / "CaseDocs/lnd_in")
    if not nml:
        raise RuntimeError("Missing DE-Hai case CaseDocs/lnd_in. Do not guess case inputs.")
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
    say("Observed EC landcover:", igbp or "unknown",
        "(published FLUXNET siteinfo describes an unmanaged mature deciduous forest).")
    say("CLM coarse surface is not a species observation.")
    say("FATES PFTs are set by fates_paramfile and model configuration,")
    say("NOT by indexing the PCT_NAT_PFT vector as FATES PFTs.")
    say("FATES vegetation carbon shares are NOT PFT fractional land cover.")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    def csvout(name, rows, columns):
        with (args.report_dir / name).open("w", newline="") as f:
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
    (args.report_dir / "04_summary.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str)+"\n")
    say("\nREAD-ONLY completed. Small reports:", args.report_dir)
    say("No data, cases, NetCDF, restart files or Slurm jobs were modified.")


if __name__ == "__main__":
    main()

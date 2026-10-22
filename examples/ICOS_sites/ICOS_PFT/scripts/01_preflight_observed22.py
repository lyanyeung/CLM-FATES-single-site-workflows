#!/usr/bin/env python3
"""Read-only IRIDIS6 preflight of 22 EC sites with quantitative vegetation leads.

No input, CIME case, surface, parameter, run, archive or Slurm file is modified.
The report is an inventory, not an authorisation to submit FATES spin-ups.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1] / "38_site_PFT_evidence.csv"
NUMERIC_CLASSES = {
    "NUMERIC_SPECIES", "NUMERIC_AREA", "NUMERIC_TEMPORAL",
    "NUMERIC_BASAL_AREA", "NUMERIC_VEGETATED_COVER",
    "TOTAL_COVER_ONLY", "NUMERIC_COVER_CONFLICT",
    "NUMERIC_GROUND_COVER", "NUMERIC_CONFLICT",
}
LAND_KEYS = ("PCT_NATVEG", "PCT_CROP", "PCT_WETLAND", "PCT_LAKE",
             "PCT_GLACIER", "PCT_URBAN")
FLAG_KEYS = ("use_fates", "use_fates_sp", "use_fates_nocomp",
             "use_fates_fixed_biogeog", "use_fates_inventory_init",
             "fates_inventory_ctrl_filename")


def read_kv(path: Path) -> dict[str, str]:
    """Read simple generated Fortran namelist assignment lines without executing."""
    result = {}
    if not path.is_file():
        return result
    for line in path.read_text(errors="replace").splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*(?:!.*)?$", line)
        if match:
            result[match.group(1).lower()] = match.group(2).strip().rstrip(",").strip().strip(chr(39) + chr(34))
    return result


def abs_path(raw: str, base: Path, root: Path) -> Path | None:
    if not raw:
        return None
    x = raw.strip().strip(chr(39) + chr(34)).replace("${DIN_LOC_ROOT}", str(root / "inputdata"))
    x = x.replace("$DIN_LOC_ROOT", str(root / "inputdata"))
    if "$" in x or "{" in x:
        return None
    path = Path(x)
    return path if path.is_absolute() else base / path


def find_surfaces(nml: dict[str, str], case: Path, root: Path) -> tuple[str, dict]:
    p = abs_path(nml.get("fsurdat", ""), case, root)
    if not p:
        return "UNRESOLVED_FSURDAT", {}
    if not p.is_file():
        return "MISSING:" + str(p), {}
    try:
        from netCDF4 import Dataset
        import numpy as np
    except ImportError:
        return str(p), {"landunit_check": "NO_NETCDF4_OR_NUMPY"}
    out = {"landunit_check": "NOT_EVALUATED"}
    try:
        with Dataset(p) as ds:
            for key in LAND_KEYS:
                if key in ds.variables:
                    v = np.ma.filled(ds.variables[key][:], np.nan)
                    out[key] = round(float(np.nansum(v)) if key == "PCT_URBAN" else float(v.ravel()[0]), 4)
            if "PCT_NAT_PFT" in ds.variables:
                v = ds.variables["PCT_NAT_PFT"]
                arr = np.ma.filled(v[:], np.nan).ravel()
                out["CLM_PCT_NAT_PFT_count"] = len(arr)
                out["CLM_PCT_NAT_PFT_sum"] = round(float(np.nansum(arr)), 5)
                out["CLM_PCT_NAT_PFT_not_FATES_area"] = True
            out["landunit_check"] = "OK"
    except Exception as exc:
        out["landunit_check"] = type(exc).__name__ + ":" + str(exc)[:180]
    return str(p), out


def fates_param_report(nml: dict[str, str], case: Path, root: Path) -> dict:
    p = abs_path(nml.get("fates_paramfile", ""), case, root)
    out = {"fates_paramfile": str(p) if p else "UNRESOLVED"}
    if not p or not p.is_file():
        out["fates_params_status"] = "MISSING_OR_UNRESOLVED"
        return out
    if p.suffix.lower() != ".json":
        out["fates_params_status"] = "EXISTS_NON_JSON_REQUIRES_INDIVIDUAL_AUDIT"
        return out
    try:
        doc = json.loads(p.read_text())
        dims, pars = doc.get("dimensions", {}), doc.get("parameters", {})
        out["pft_count"] = dims.get("fates_pft", "UNKNOWN")
        names = pars.get("fates_pftname", {})
        out["pft_names_raw"] = str(names.get("data", []))[:500] if isinstance(names, dict) else "UNKNOWN"
        mapping = pars.get("fates_hlm_pft_map", {})
        out["hlm_map_dims"] = ",".join(mapping.get("dims", [])) if isinstance(mapping, dict) else "NOT_FOUND"
        out["fates_params_status"] = "JSON_READ_OK_VALIDATE_MAPPING_MANUALLY"
    except (OSError, ValueError, TypeError) as exc:
        out["fates_params_status"] = type(exc).__name__ + ":" + str(exc)[:160]
    return out


def write_csv(path: Path, records: list[dict]) -> None:
    if not records:
        return
    fields = list(dict.fromkeys(k for record in records for k in record))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for record in records:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                             for k, v in record.items()})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/iridisfs/scratch") / os.environ.get("USER", "ly3n24") / "CLM_FATES")
    parser.add_argument("--output", type=Path, default=Path.home() / "ICOS_PFT_Observed22_preflight")
    args = parser.parse_args()
    with EVIDENCE.open(encoding="utf-8-sig", newline="") as f:
        evidence = list(csv.DictReader(f))
    sites = [r for r in evidence if r["evidence_class"] in NUMERIC_CLASSES]
    if len(evidence) != 38 or len(sites) != 22 or len({r["site"] for r in sites}) != 22:
        raise SystemExit("FAIL: expected exactly 38 evidence records and 22 unique quantitative leads.")

    case_root = args.root / "cases"
    if not case_root.is_dir():
        raise SystemExit("FAIL: CIME case directory missing: " + str(case_root))
    args.output.mkdir(parents=True, exist_ok=True)
    summary, details = [], []
    for obs in sites:
        site = obs["site"]
        cases = sorted(p for p in case_root.glob(site + "_FATES*") if p.is_dir())
        # Never silently pick a historical/sensitivity case as the baseline.
        row = {
            "site": site, "batch": obs["batch"], "evidence_class": obs["evidence_class"],
            "observation_denominator": obs["observed_denominator"],
            "area_ready_for_model": "NOT_YET_VERIFIED",
            "candidate_case_count": len(cases),
            "candidate_cases": ";".join(c.name for c in cases),
            "next_gate": "VERIFY_TOWER_FOOTPRINT_AREA_AND_ACTUAL_FATES_MODE",
        }
        summary.append(row)
        for case in cases:
            nml = read_kv(case / "CaseDocs" / "lnd_in")
            surface, land = find_surfaces(nml, case, args.root)
            entry = {"site": site, "case": case.name,
                     "case_path": str(case), "generated_namelist": str(case / "CaseDocs" / "lnd_in"),
                     "namelist_exists": bool(nml), "fsurdat": surface}
            for flag in FLAG_KEYS:
                entry[flag] = nml.get(flag, "NOT_EXPLICIT_IN_GENERATED_NAMELIST")
            entry.update(land)
            entry.update(fates_param_report(nml, case, args.root))
            entry["run_action"] = "READ_ONLY_NO_SUBMISSION"
            details.append(entry)
    write_csv(args.output / "01_sites_22.tsv", summary)
    write_csv(args.output / "02_case_configurations.tsv", details)
    with (args.output / "03_manifest.json").open("w", encoding="utf-8") as f:
        json.dump({"evidence": str(EVIDENCE), "case_root": str(case_root),
                   "sites": len(sites), "case_candidates": len(details),
                   "read_only": True,
                   "warning": "Do not use PCT_NAT_PFT as FATES PFT fractions without "
                              "checking effective mode and fates_hlm_pft_map. "
                              "Quantitative forest stand shares are not ground-area shares.",
                   "no_new_cases_or_jobs": True}, f, indent=2)
    print("PRECHECK COMPLETE - READ ONLY")
    print(f"Sites: {len(sites)} | existing candidate case folders: {len(details)}")
    print("Evidence classes:")
    for cat in sorted(NUMERIC_CLASSES):
        n = sum(x["evidence_class"] == cat for x in sites)
        if n:
            print(f"  {cat}: {n}")
    print("Files:")
    for name in ("01_sites_22.tsv", "02_case_configurations.tsv", "03_manifest.json"):
        print("  " + str(args.output / name))
    print("NO surfaces, FATES parameters, forcing, cases, CIME jobs or archives changed.")


if __name__ == "__main__":
    main()

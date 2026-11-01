#!/usr/bin/env python3
"""OzFlux nine-site Stage01: read-only inventory of original L6 NetCDF metadata.

No extraction, interpolation, time shift, forcing conversion, source edits or jobs.
Requires netCDF4 on IRIDIS (e.g. conda activate clm_fates_env).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

EXPECTED = {
    "AU-ASM": 2,
    "AU-Cow": 1,
    "AU-Cpr": 1,
    "AU-DaS": 1,
    "AU-Dry": 1,
    "AU-Gin": 1,
    "AU-How": 1,
    "AU-Stp": 1,
    "AU-Tum": 1,
}
DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
IMPORTANT = ("Ta", "SH", "ps", "Fsd", "Fld", "Ws", "Precip", "GPP_LT", "NEE_LT", "time", "DateTime", "TIMESTAMP")

def manifest_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["site", "filename"]:
            raise ValueError("Manifest header must be exactly site<TAB>filename")
        rows = list(reader)
    seen = set()
    counts = {k: 0 for k in EXPECTED}
    for row in rows:
        site, name = row["site"], row["filename"]
        if site not in EXPECTED or not name.endswith(".nc") or "/" in name or "\\" in name or ".." in name:
            raise ValueError("Invalid manifest entry: " + repr(row))
        key = (site, name)
        if key in seen:
            raise ValueError("Duplicate manifest entry: " + repr(key))
        seen.add(key)
        counts[site] += 1
    if len(rows) != 10 or counts != EXPECTED:
        raise ValueError("Manifest must represent exactly 9 sites and 10 files, with 2 AU-ASM segments")
    return rows

def attr(x, name, default=None):
    try:
        return str(x.getncattr(name))[:300] if name in x.ncattrs() else default
    except Exception:
        return default

def time_probe(ds, netcdf4):
    found = []
    for name, var in ds.variables.items():
        units = attr(var, "units", "") or ""
        is_time = "time" in name.lower() or "date" in name.lower() or " since " in units.lower()
        if not is_time:
            continue
        item = {
            "name": name, "dimensions": list(var.dimensions),
            "shape": list(var.shape), "dtype": str(var.dtype),
            "units": units, "calendar": attr(var, "calendar", "standard"),
        }
        # Only read up to three scalar elements of a 1-D time coordinate.
        if var.ndim == 1 and len(var) > 0 and var.dtype.kind in "iuf":
            try:
                indexes = sorted({0, min(1, len(var) - 1), len(var) - 1})
                vals = {str(i): float(var[i]) for i in indexes}
                item["numeric_samples"] = vals
                if " since " in units.lower():
                    try:
                        item["decoded_samples"] = {
                            i: str(netcdf4.num2date(v, units, calendar=item["calendar"]))
                            for i, v in vals.items()
                        }
                    except Exception as exc:
                        item["decode_warning"] = str(exc)[:240]
            except Exception as exc:
                item["sample_warning"] = str(exc)[:240]
        found.append(item)
    return found

def inventory(path: Path):
    import netCDF4
    with netCDF4.Dataset(str(path), mode="r") as ds:
        selected_attrs = (
            "site_name", "site", "latitude", "longitude", "tower_height", "time_zone",
            "timezone", "time_coverage_start", "time_coverage_end", "title",
            "institution", "source", "history", "Conventions"
        )
        globals_out = {a: attr(ds, a) for a in selected_attrs if a in ds.ncattrs()}
        variables = {}
        for name, var in ds.variables.items():
            if name in IMPORTANT or name.lower() in {x.lower() for x in IMPORTANT}:
                variables[name] = {
                    "dimensions": list(var.dimensions),
                    "shape": list(var.shape),
                    "units": attr(var, "units"),
                    "long_name": attr(var, "long_name"),
                    "_FillValue": attr(var, "_FillValue"),
                }
        return {
            "status": "INVENTORIED",
            "bytes": path.stat().st_size,
            "format": ds.data_model,
            "dimensions": {
                name: {"size": len(dim), "unlimited": dim.isunlimited()}
                for name, dim in ds.dimensions.items()
            },
            "variable_count": len(ds.variables),
            "variable_names": list(ds.variables)[:350],
            "variable_names_truncated": len(ds.variables) > 350,
            "important_variables": variables,
            "global_attributes_selected": globals_out,
            "groups": list(ds.groups),
            "time_coordinates": time_probe(ds, netCDF4),
        }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    output = {
        "cohort": "OzFlux_MultiSite_09", "stage": "Stage01",
        "mode": "READ_ONLY_NO_MODEL_NO_INTERPOLATION",
        "site_count_expected": 9, "file_count_expected": 10,
        "root": str(args.root), "files": [],
        "science_warning": "AU-ASM Mulga1/Mulga2 are separate source segments; do not concatenate before provenance/time/geometry QC.",
    }
    for row in manifest_rows(args.manifest):
        path = args.root / row["site"] / "forcing" / "raw" / row["filename"]
        item = dict(row)
        item["path"] = str(path)
        try:
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError("Missing source file or unexpected symlink")
            item.update(inventory(path))
        except Exception as exc:
            item["status"] = "ERROR"
            item["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:400])
        output["files"].append(item)
    output["inventoried_count"] = sum(x["status"] == "INVENTORIED" for x in output["files"])
    output["all_files_inventoried"] = output["inventoried_count"] == 10
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["all_files_inventoried"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

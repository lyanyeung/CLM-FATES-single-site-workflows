#!/usr/bin/env python3
"""OzFlux nine-site Stage02: source time/variable/QC audit; strictly read-only.

Original NetCDF files are opened with mode="r". Only JSON/TSV reports under
--out are created. No concatenation, time shifts, interpolation or model jobs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path

import netCDF4
import numpy as np

SITES = {
    "AU-ASM": 2, "AU-Cow": 1, "AU-Cpr": 1, "AU-DaS": 1,
    "AU-Dry": 1, "AU-Gin": 1, "AU-How": 1, "AU-Stp": 1, "AU-Tum": 1,
}
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
FORCING = ("Ta", "SH", "ps", "Fsd", "Fld", "Ws", "Precip")
EC = ("GPP_LT", "NEE_LT")
KEYS = FORCING + EC
CHUNK = 16384


def get_attr(var, name, default=None):
    if name not in var.ncattrs():
        return default
    value = var.getncattr(name)
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value[:20]]
    return str(value)[:300]


def read_manifest(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != ["site", "filename"]:
            raise ValueError("Bad manifest header")
        rows = list(reader)
    counts = dict.fromkeys(SITES, 0)
    unique = set()
    for r in rows:
        site, name = r["site"], r["filename"]
        if site not in SITES or not name.endswith(".nc") or any(c in name for c in ("/", "\\", "..")):
            raise ValueError("Unsafe or unlisted source: " + str(r))
        if (site, name) in unique:
            raise ValueError("Duplicate manifest source: " + str(r))
        unique.add((site, name))
        counts[site] += 1
    if len(rows) != 10 or counts != SITES:
        raise ValueError("Expected 9 OzFlux sites and 10 exact source files (AU-ASM has 2)")
    return rows


def time_scale_seconds(units):
    unit = units.split(" since ", 1)[0].strip().lower()
    if unit in ("day", "days", "d"):
        return 86400.0
    if unit in ("hour", "hours", "hr", "hrs", "h"):
        return 3600.0
    if unit in ("minute", "minutes", "min", "mins"):
        return 60.0
    if unit in ("second", "seconds", "sec", "secs", "s"):
        return 1.0
    raise ValueError("Unrecognised numeric time units: " + repr(units))


def to_dates(values, units, calendar):
    return [str(x) for x in netCDF4.num2date(values, units, calendar=calendar)]


def examine_time(ds):
    if "time" not in ds.variables:
        raise ValueError("Missing time coordinate")
    v = ds.variables["time"]
    if len(v.dimensions) != 1:
        raise ValueError("Time coordinate is not 1-D")
    units = get_attr(v, "units", "")
    calendar = get_attr(v, "calendar", "standard")
    if " since " not in units.lower():
        raise ValueError("Time coordinate has no numeric 'since' units")
    scale = time_scale_seconds(units.lower())
    vals = np.ma.asarray(v[:]).astype(float).filled(np.nan)
    if vals.ndim != 1 or not len(vals):
        raise ValueError("Empty or malformed time coordinate")
    finite = np.isfinite(vals)
    if not finite.all():
        raise ValueError("Non-finite time records: " + str(int((~finite).sum())))
    delta = np.diff(vals) * scale
    positive = delta[delta > 0]
    if len(vals) > 1 and len(positive) == 0:
        raise ValueError("No increasing timestamps")
    typical = float(np.median(positive)) if len(positive) else None
    if typical is not None:
        tolerance = max(1.0, typical * 0.001)
        irregular = np.flatnonzero(np.abs(delta - typical) > tolerance)
    else:
        tolerance, irregular = 1.0, np.empty(0, dtype=int)
    backward = int(np.sum(delta < 0))
    duplicates = int(np.sum(delta == 0))
    first, last = to_dates([float(vals[0]), float(vals[-1])], units, calendar)

    examples = []
    for j in irregular[:15]:
        i = int(j)
        dates = to_dates([float(vals[i]), float(vals[i+1])], units, calendar)
        examples.append({
            "index_before": i, "from": dates[0], "to": dates[1],
            "delta_seconds": round(float(delta[i]), 4),
            "typical_seconds": round(typical, 4) if typical else None,
        })

    # Count timestamp rows by calendar year without converting a half-million
    # individual records to Python datetime objects.
    years = []
    sorted_vals = np.sort(vals)  # counts remain valid even with out-of-order time
    first_year, last_year = int(first[:4]), int(last[:4])
    if last_year < first_year or last_year - first_year > 150:
        raise ValueError("Unexpected time span")
    for year in range(first_year, last_year+1):
        lo = netCDF4.date2num(dt.datetime(year, 1, 1), units, calendar=calendar)
        hi = netCDF4.date2num(dt.datetime(year+1, 1, 1), units, calendar=calendar)
        n = int(np.searchsorted(sorted_vals, hi, "left") -
                np.searchsorted(sorted_vals, lo, "left"))
        nominal = int(round(((hi-lo)*scale)/typical)) if typical else None
        whole_year = (float(vals[0]) <= float(lo) + tolerance/scale
                      and float(vals[-1]) >= float(hi) - typical/scale - tolerance/scale
                      if typical else False)
        years.append({"year": year, "records": n,
                      "nominal_full_year_records": nominal,
                      "whole_year_window": bool(whole_year),
                      "difference_if_whole_year": (n-nominal if whole_year and nominal else None)})
    return {
        "time_name": "time", "units": units, "calendar": calendar,
        "time_dimension": v.dimensions[0],
        "n_records": int(len(vals)), "first": first, "last": last,
        "first_step_seconds": (float(delta[0]) if len(delta) else None),
        "median_positive_step_seconds": typical,
        "duplicate_steps": duplicates, "backward_steps": backward,
        "noncanonical_steps": int(len(irregular)),
        "irregular_examples": examples,
        "year_counts": years,
        # No timezone transformation: archive-native time labels only.
        "timezone_status": "UNVERIFIED_FROM_METADATA",
    }


def physical_bounds(key, units):
    u = (units or "").lower().replace(" ", "").replace("_", "")
    if key == "Ta":
        if u in ("degc", "degreecelsius", "degreescelsius", "celsius", "c", "degreec"):
            return (-55.0, 65.0)
        if u in ("k", "kelvin"):
            return (218.15, 338.15)
    if key == "SH":
        if u in ("kg/kg", "kgkg-1", "kgkg^-1", "kgkg"):
            return (0.0, 0.055)
        if u in ("g/kg", "gkg-1", "gkg^-1"):
            return (0.0, 55.0)
    if key == "ps":
        if u in ("kpa",):
            return (45.0, 115.0)
        if u in ("pa",):
            return (45000.0, 115000.0)
        if u in ("hpa", "mbar"):
            return (450.0, 1150.0)
    if key in ("Fsd", "Fld") and any(token in u for token in ("wm-2", "w/m^2", "w/m2", "wm^-2", "wm**-2")):
        return ((-50.0, 1600.0) if key == "Fsd" else (0.0, 850.0))
    if key == "Ws" and u in ("m/s", "ms-1", "ms^-1"):
        return (-0.1, 65.0)
    if key == "Precip":
        return (0.0, None)  # Negative rain always flagged; no unit assumptions
    return None


def audit_field(var, key, n_time, time_dim):
    units = get_attr(var, "units", "")
    info = {
        "variable": var.name, "canonical_candidate": key,
        "units": units,
        "dimensions": list(var.dimensions), "shape": list(var.shape),
        "height": get_attr(var, "height"),
        "coverage_L6": get_attr(var, "coverage_L6"),
        "long_name": get_attr(var, "long_name"),
        "_FillValue": get_attr(var, "_FillValue"),
        "flag_meanings": get_attr(var, "flag_meanings"),
        "qc_semantics_approved": False,
        "numeric_bounds": physical_bounds(key, units),
    }
    positions = [i for i, d in enumerate(var.dimensions) if d == time_dim]
    if len(positions) != 1 or var.shape[positions[0]] != n_time:
        info["audit_status"] = "HOLD_SHAPE_NOT_SINGLE_TIME"
        return info
    t_idx = positions[0]
    if any(v != 1 for i, v in enumerate(var.shape) if i != t_idx):
        info["audit_status"] = "HOLD_MULTIPLE_SPATIAL_OR_EXTRA_LAYERS"
        return info
    if getattr(var.dtype, "kind", "") not in "iuf":
        info["audit_status"] = "HOLD_NOT_NUMERIC"
        return info

    valid = missing = outlier = 0
    minimum, maximum = math.inf, -math.inf
    bad_examples = []
    bounds = physical_bounds(key, units)
    for start in range(0, n_time, CHUNK):
        selection = [slice(None)] * var.ndim
        selection[t_idx] = slice(start, min(start+CHUNK, n_time))
        raw = np.ma.asarray(var[tuple(selection)]).astype(np.float64)
        x = np.asarray(raw.filled(np.nan)).reshape(-1)
        # Common raw OzFlux sentinel values; source mask and metadata take priority.
        bad = ~np.isfinite(x) | (x <= -9990.0)
        good = x[~bad]
        missing += int(bad.sum())
        valid += len(good)
        if len(good):
            minimum = min(minimum, float(np.min(good)))
            maximum = max(maximum, float(np.max(good)))
            if bounds:
                low, high = bounds
                bad_physics = (good < low)
                if high is not None:
                    bad_physics |= (good > high)
                outlier += int(bad_physics.sum())
                if len(bad_examples) < 8 and np.any(bad_physics):
                    bad_examples.extend([float(z) for z in good[bad_physics][:8-len(bad_examples)]])
    info.update({
        "audit_status": "AUDITED",
        "total_rows": int(n_time), "finite_nonfill": valid, "missing_or_fill": missing,
        "finite_fraction": round(valid / n_time, 6) if n_time else None,
        "min": (minimum if valid else None), "max": (maximum if valid else None),
        "broad_physical_alarm_count": outlier if bounds else None,
        "broad_physical_alarm_values_first8": bad_examples,
        "bounds_status": ("SCREENED_NOT_AUTOFIX" if bounds else "UNITS_UNKNOWN_NO_RANGE_ASSERTION"),
    })
    return info


def source_inventory(path):
    with netCDF4.Dataset(str(path), "r") as ds:
        t = examine_time(ds)
        dim = t["time_dimension"]
        vars_ = list(ds.variables)
        lower = {name.lower(): name for name in vars_}
        result = {"time": t, "variable_count": len(vars_),
                  "globals": {key: get_attr(ds, key) for key in ds.ncattrs()
                              if any(x in key.lower() for x in
                                     ("time", "site", "latitude", "longitude", "height",
                                      "tower", "vegetat", "fluxnet", "license", "altitude"))},
                  "fields": {}, "qc_candidates": {},
                  "all_variable_names": vars_}
        for key in KEYS:
            actual = key if key in ds.variables else lower.get(key.lower())
            related = [v for v in vars_ if v.lower().startswith(key.lower()+"_")
                       and any(tok in v.lower() for tok in ("qc", "flag", "coverage", "gap", "source"))]
            result["qc_candidates"][key] = [
                {"name": name, "units": get_attr(ds.variables[name], "units"),
                 "long_name": get_attr(ds.variables[name], "long_name"),
                 "flag_values": get_attr(ds.variables[name], "flag_values"),
                 "flag_meanings": get_attr(ds.variables[name], "flag_meanings")}
                for name in related[:35]]
            if actual is None:
                alternatives = [v for v in vars_
                                if v.lower().startswith(key.lower()+"_")][:25]
                result["fields"][key] = {"audit_status": "MISSING_EXACT",
                                         "alternatives_not_approved": alternatives}
            else:
                result["fields"][key] = audit_field(ds.variables[actual], key, t["n_records"], dim)
        return result


def write_tsv(path, rows, columns):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    if out == root or root in out.parents:
        raise ValueError("Audit output must not be inside any source site tree")
    if args.out.is_symlink():
        raise ValueError("Audit output may not be a symlink")
    rows = read_manifest(args.manifest)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "cohort": "OzFlux_MultiSite_09", "stage": "Stage02_SOURCE_QC",
        "mode": "READ_ONLY_SOURCE; OUTPUT_REPORTS_ONLY; NO_FORCING; NO_JOBS",
        "status_definition": "AUDITED means numeric/data inventory only, NOT scientific approval",
        "root": str(root), "files": []}
    compact, yearly, fields = [], [], []
    for row in rows:
        site, name = row["site"], row["filename"]
        path = root / site / "forcing" / "raw" / name
        entry = {"site": site, "filename": name, "source_path": str(path)}
        try:
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError("Missing or symlinked original file")
            entry.update(source_inventory(path))
            entry["status"] = "AUDITED_SOURCE_ONLY"
            t = entry["time"]
            compact.append({
                "site": site, "filename": name, "status": entry["status"],
                "n": t["n_records"], "first": t["first"], "last": t["last"],
                "first_step_seconds": t["first_step_seconds"],
                "median_step_seconds": t["median_positive_step_seconds"],
                "duplicates": t["duplicate_steps"], "backwards": t["backward_steps"],
                "noncanonical_steps": t["noncanonical_steps"],
                "variable_count": entry["variable_count"]})
            for x in t["year_counts"]:
                yearly.append({"site": site, "filename": name, **x})
            for key, x in entry["fields"].items():
                fields.append({"site": site, "filename": name, "candidate": key,
                               "status": x["audit_status"], "name": x.get("variable"),
                               "units": x.get("units"), "finite_fraction": x.get("finite_fraction"),
                               "missing_or_fill": x.get("missing_or_fill"),
                               "min": x.get("min"), "max": x.get("max"),
                               "broad_physical_alarm_count": x.get("broad_physical_alarm_count")})
        except Exception as exc:
            entry.update({"status": "ERROR", "error": type(exc).__name__+": "+str(exc)[:500]})
            compact.append({"site": site, "filename": name, "status": "ERROR"})
        report["files"].append(entry)
    report["audited_file_count"] = sum(x["status"] == "AUDITED_SOURCE_ONLY" for x in report["files"])
    report["all_sources_readable"] = report["audited_file_count"] == 10
    (out/"stage02_source_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_tsv(out/"stage02_file_summary.tsv", compact,
              ["site","filename","status","n","first","last","first_step_seconds",
               "median_step_seconds","duplicates","backwards","noncanonical_steps","variable_count"])
    write_tsv(out/"stage02_year_counts.tsv", yearly,
              ["site","filename","year","records","nominal_full_year_records",
               "whole_year_window","difference_if_whole_year"])
    write_tsv(out/"stage02_variable_summary.tsv", fields,
              ["site","filename","candidate","status","name","units",
               "finite_fraction","missing_or_fill","min","max","broad_physical_alarm_count"])
    for x in compact:
        print(x["site"],x["filename"],x["status"], "n=",x.get("n","?"),
              "step_seconds=",x.get("median_step_seconds","?"),
              "noncanonical=",x.get("noncanonical_steps","?"),
              "duplicates=",x.get("duplicates","?"))
    print("AUDITED",report["audited_file_count"],"/10")
    print("REPORT_DIR",out)
    print("SCIENCE APPROVAL: NOT GRANTED. No forcing generated, no model jobs submitted.")
    return 0 if report["all_sources_readable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

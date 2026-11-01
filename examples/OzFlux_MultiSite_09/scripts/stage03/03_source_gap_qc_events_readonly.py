#!/usr/bin/env python3
"""OzFlux Stage03: read-only source gaps, physical alarms, and QC provenance.

All original L6 .nc files opened in mode="r". No conversion, interpolation,
timestamp shifts, merging, replacement, ERA injection, or Slurm submission.
QC codes are reported as observed, never automatically interpreted as QC0.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import netCDF4
import numpy as np

EXPECTED = {
    "AU-ASM": 2, "AU-Cow": 1, "AU-Cpr": 1, "AU-DaS": 1,
    "AU-Dry": 1, "AU-Gin": 1, "AU-How": 1, "AU-Stp": 1, "AU-Tum": 1,
}
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
MET = ("Ta", "SH", "ps", "Fsd", "Fld", "Ws", "Precip")
EC = ("GPP_LT", "NEE_LT")
ALL = MET + EC
MAX_EVENTS_IN_JSON = 50
MAX_FLAG_CODES = 40


def manifest(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames != ["site", "filename"]:
            raise ValueError("Invalid source manifest header")
        rows = list(reader)
    counts = dict.fromkeys(EXPECTED, 0)
    seen = set()
    for r in rows:
        site, name = r["site"], r["filename"]
        if site not in EXPECTED or not name.endswith(".nc") or any(t in name for t in ("/", "\\", "..")):
            raise ValueError("Unexpected source: " + str(r))
        if (site, name) in seen:
            raise ValueError("Duplicate source")
        seen.add((site, name))
        counts[site] += 1
    if len(rows) != 10 or counts != EXPECTED:
        raise ValueError("Manifest must contain ten exact files over nine sites")
    return rows


def attr(v, name):
    if name not in v.ncattrs():
        return None
    a = v.getncattr(name)
    if isinstance(a, np.ndarray):
        a = a.tolist()
    if isinstance(a, (list, tuple)):
        return [str(x) for x in a[:40]]
    return str(a)[:450]


def values(v, time_dim, n):
    """Read scalar spatial/vertical singleton dimensions, preserving source masks."""
    if time_dim not in v.dimensions or v.dimensions.count(time_dim) != 1:
        return None
    if any(d != time_dim and v.shape[i] != 1 for i, d in enumerate(v.dimensions)):
        return None
    if not np.issubdtype(v.dtype, np.number):
        return None
    a = np.ma.asarray(v[:], dtype=np.float64).filled(np.nan).reshape(-1)
    if len(a) != n:
        return None
    return a


def runs(mask):
    # Inclusive first, exclusive stop. Handles full-record or zero-record runs.
    padded = np.concatenate(([False], np.asarray(mask, dtype=bool), [False]))
    change = np.diff(padded.astype(np.int8))
    begins = np.flatnonzero(change == 1)
    ends = np.flatnonzero(change == -1)
    return [(int(a), int(b)) for a, b in zip(begins, ends)]


def unit_bounds(name, units):
    u = (units or "").lower().replace(" ", "").replace("_", "")
    if name == "Ta":
        if u in ("degc", "degreecelsius", "degreescelsius", "c", "celsius"):
            return (-55, 65)
        if u in ("k", "kelvin"):
            return (218.15, 338.15)
    if name == "SH":
        if u in ("kg/kg", "kgkg-1", "kgkg^-1", "kgkg"):
            return (0, 0.055)
        if u in ("g/kg", "gkg-1", "gkg^-1"):
            return (0, 55)
    if name == "ps":
        if u in ("kpa",):
            return (45, 115)
        if u in ("pa",):
            return (45000, 115000)
        if u in ("hpa", "mbar"):
            return (450, 1150)
    if name in ("Fsd", "Fld") and u in ("w/m^2", "w/m2", "wm-2", "wm^-2", "wm**-2", "watt/m2", "watt/m^2"):
        return (-50, 1600) if name == "Fsd" else (0, 850)
    if name == "Ws" and u in ("m/s", "ms-1", "ms^-1"):
        return (-0.1, 65)
    if name == "Precip" and u in ("mm", "mm/30min", "mm/h", "mmhr-1", "mmhour-1"):
        return (0, None)
    return None


def time_label(t, units, cal, idx):
    try:
        return str(netCDF4.num2date(float(t[idx]), units, calendar=cal))
    except Exception as e:
        return "DECODE_ERROR:" + str(e)[:90]


def qc_candidates(ds, source_name):
    lower = source_name.lower()
    ordered = []
    for k in ds.variables:
        z = k.lower()
        if z == lower + "_qcflag" or z == lower + "_qc" or z == lower + "_flag":
            ordered.insert(0, k)
        elif (z.startswith(lower + "_") and any(x in z for x in ("qc", "flag", "source", "method"))):
            ordered.append(k)
    return list(dict.fromkeys(ordered))[:15]


def distribution(q):
    if q is None:
        return None
    finite = q[np.isfinite(q)]
    unique, count = np.unique(finite, return_counts=True)
    ranking = np.argsort(-count)
    top = ranking[:MAX_FLAG_CODES]
    return {
        "finite_count": int(len(finite)),
        "nonfinite_count": int(len(q)-len(finite)),
        "distinct_codes": int(len(unique)),
        "most_common_codes": [
            {"value": float(unique[i]), "count": int(count[i])}
            for i in top],
        "truncated": bool(len(unique) > MAX_FLAG_CODES),
    }


def event_records(mask, label, source, t, t_units, cal, x, flags, name, fname, site):
    groups = runs(mask)
    # All grouped intervals in TSV; detailed context capped in JSON.
    rows = []
    for a, b in groups:
        rows.append({
            "site": site, "filename": fname, "variable": name,
            "event_type": label, "first_index": a, "last_index": b-1,
            "n_records": b-a, "first_time": time_label(t,t_units,cal,a),
            "last_time": time_label(t,t_units,cal,b-1)
        })
    selected = sorted(groups, key=lambda p: (-(p[1]-p[0]), p[0]))[:MAX_EVENTS_IN_JSON]
    details = []
    for a, b in selected:
        indices = sorted({i for edge in (a, b-1)
                          for i in range(max(0, edge-2), min(len(x), edge+3))})
        context = []
        for i in indices:
            val = float(x[i])
            c = {"index": i, "time": time_label(t,t_units,cal,i),
                 "source_value": val if np.isfinite(val) else None}
            for flagname, q in flags.items():
                if q is not None:
                    v = float(q[i])
                    c[flagname] = v if np.isfinite(v) else None
            context.append(c)
        details.append({"first_index": a, "last_index": b-1, "n_records": b-a,
                        "first_time": time_label(t,t_units,cal,a),
                        "last_time": time_label(t,t_units,cal,b-1),
                        "context_before_during_after": context})
    return rows, {"total_episodes": len(groups),
                  "examples_longest_first": details,
                  "examples_truncated": len(groups) > MAX_EVENTS_IN_JSON}


def audit_file(path, site, fname):
    with netCDF4.Dataset(str(path), "r") as ds:
        if "time" not in ds.variables:
            raise ValueError("No time variable")
        vtime = ds.variables["time"]
        if vtime.ndim != 1:
            raise ValueError("Time must be 1-D")
        t = np.ma.asarray(vtime[:], dtype=np.float64).filled(np.nan)
        if not len(t) or not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
            raise ValueError("Invalid or non-increasing source time; refer back to Stage02")
        units = str(vtime.units)
        cal = getattr(vtime, "calendar", "standard")
        time_dim = vtime.dimensions[0]
        all_vars = list(ds.variables)
        lower = {n.lower(): n for n in all_vars}
        report = {"site": site, "filename": fname, "path": str(path),
                  "status": "AUDITED_PROVENANCE_NOT_APPROVED",
                  "records": len(t), "time_calendar": str(cal),
                  "first": time_label(t,units,cal,0),
                  "last": time_label(t,units,cal,len(t)-1),
                  "native_time_units": units,
                  "fields": {}}
        event_rows = []
        for name in ALL:
            exact = name if name in ds.variables else lower.get(name.lower())
            if exact is None:
                report["fields"][name] = {"status": "HOLD_MISSING_EXACT_NAME"}
                continue
            v = ds.variables[exact]
            x = values(v, time_dim, len(t))
            if x is None:
                report["fields"][name] = {"status": "HOLD_NON_SCALAR_TIME_SHAPE",
                                           "shape": list(v.shape), "dimensions": list(v.dimensions)}
                continue
            u = attr(v,"units")
            missing = (~np.isfinite(x)) | (x <= -9990)
            bounds = unit_bounds(name,u)
            alarm = np.zeros(len(x),dtype=bool)
            if bounds is not None:
                lo,hi = bounds
                alarm = (~missing) & (x < lo)
                if hi is not None:
                    alarm |= (~missing) & (x > hi)

            qcs = {}
            qmeta = {}
            for qname in qc_candidates(ds, exact):
                qvar = ds.variables[qname]
                q = values(qvar,time_dim,len(t))
                qcs[qname] = q
                qmeta[qname] = {
                    "units": attr(qvar,"units"),
                    "long_name": attr(qvar,"long_name"),
                    "flag_values": attr(qvar,"flag_values"),
                    "flag_meanings": attr(qvar,"flag_meanings"),
                    "distribution_uninterpreted": distribution(q),
                    "compatible_time_shape": bool(q is not None),
                }
            ev_missing, m = event_records(missing,"MISSING",exact,t,units,cal,x,qcs,name,fname,site)
            ev_physical, p = event_records(alarm,"PHYSICAL_ALARM",exact,t,units,cal,x,qcs,name,fname,site)
            event_rows.extend(ev_missing)
            event_rows.extend(ev_physical)
            report["fields"][name] = {
                "status": "SCREENED_NOT_APPROVED", "source_variable": exact,
                "units": u, "height": attr(v,"height"),
                "coverage_L6": attr(v,"coverage_L6"),
                "missing_records": int(missing.sum()),
                "physical_alarm_records": int(alarm.sum()) if bounds else None,
                "physical_bounds_applied": list(bounds) if bounds else None,
                "source_qc_candidates": qmeta,
                "source_qc_codes_not_automatically_interpreted": True,
                "missing_episodes": m, "physical_alarm_episodes": p,
            }
        return report, event_rows


def self_test():
    assert runs(np.array([False, True, True, False, True, False])) == [(1,3),(4,5)]
    assert runs(np.array([True, True, True])) == [(0,3)]
    assert runs(np.array([False, False])) == []
    assert unit_bounds("Fsd", "W/m^2") == (-50,1600)
    assert unit_bounds("Fld", "W/m^2") == (0,850)
    assert unit_bounds("SH", "kg/kg") == (0,0.055)
    assert unit_bounds("Ta", "degC") == (-55,65)
    assert unit_bounds("Precip", "mm") == (0,None)
    q = distribution(np.array([0,0,1,1,1,np.nan]))
    assert q["finite_count"] == 5 and q["distinct_codes"] == 2
    print("STAGE03 SELF-TEST PASS: interval grouping, native radiation units, humidity bounds, QC code histogram; NO SOURCE WRITES")


def main():
    if sys.argv[1:] == ['--self-test']:
        self_test()
        return 0
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--root", type=Path, default=ROOT)
    a = p.parse_args()
    root, out = a.root.resolve(), a.out.resolve()
    if out == root or root in out.parents or a.out.is_symlink():
        raise ValueError("Output must be a new HOME report directory, not source tree or symlink")
    inputs = manifest(a.manifest)
    if out.exists():
        raise FileExistsError("Output already exists; use a new timestamped directory: " + str(out))
    out.mkdir(parents=True)
    report = {"stage":"OzFlux Stage03 gap events + source flag provenance",
              "mode":"SOURCE_READ_ONLY_NO_AUTOFILL_NO_FORCING_NO_SLURM",
              "science_approval":False,
              "description":"L6 may include gapfilled data; flag values need source-specific interpretation",
              "files":[]}
    events, compact = [], []
    for row in inputs:
        site, fname = row["site"], row["filename"]
        path = root / site / "forcing" / "raw" / fname
        try:
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError("Source file missing or symlinked")
            result, ev = audit_file(path,site,fname)
            events.extend(ev)
            compact.append({"site":site,"filename":fname,"status":result["status"],
                            "records":result["records"],"missing_met_fields":
                            ",".join(k for k in MET if
                                     result["fields"][k].get("missing_records",0)>0),
                            "physical_alarm_met_fields":
                            ",".join(k for k in MET if
                                     result["fields"][k].get("physical_alarm_records",0)>0)})
            report["files"].append(result)
            print("AUDITED",site,fname,"source records",result["records"])
        except Exception as e:
            report["files"].append({"site":site,"filename":fname,"status":"ERROR",
                                    "error":type(e).__name__+": "+str(e)[:500]})
            compact.append({"site":site,"filename":fname,"status":"ERROR"})
            print("ERROR",site,fname,type(e).__name__,str(e)[:250])
    report["audited"] = sum(f["status"]=="AUDITED_PROVENANCE_NOT_APPROVED" for f in report["files"])
    (out/"stage03_source_gap_qc.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    with (out/"stage03_event_ledger.tsv").open("w",newline="",encoding="utf-8") as h:
        cols = ("site","filename","variable","event_type","first_index","last_index",
                "n_records","first_time","last_time")
        w = csv.DictWriter(h,delimiter="\t",fieldnames=cols)
        w.writeheader()
        w.writerows(events)
    with (out/"stage03_summary.tsv").open("w",newline="",encoding="utf-8") as h:
        cols = ("site","filename","status","records","missing_met_fields",
                "physical_alarm_met_fields")
        w = csv.DictWriter(h,delimiter="\t",fieldnames=cols)
        w.writeheader()
        w.writerows(compact)
    print("AUDITED",report["audited"],"/10; MISSING_AND_ALARM_EPISODES",len(events))
    print("REPORT_DIR",out)
    print("SOURCE FLAG CODES UNINTERPRETED; NO AUTOMATIC REPAIR OR MODEL SUBMISSION")
    return 0 if report["audited"]==10 else 1

if __name__=="__main__":
    raise SystemExit(main())

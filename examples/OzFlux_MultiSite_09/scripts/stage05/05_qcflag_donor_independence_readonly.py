#!/usr/bin/env python3
"""OzFlux Stage05: read-only PyFluxPro source-flag and backup-sensor comparisons.

All original NetCDF files opened strictly in mode "r". A numeric candidate is
NOT a scientifically approved substitution. No gap filling, no UTC adjustment,
no output NetCDF, no model jobs, no replacement of original source files.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import netCDF4
import numpy as np

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITES = {"AU-ASM": 2, "AU-Cow": 1, "AU-Cpr": 1, "AU-DaS": 1,
         "AU-Dry": 1, "AU-Gin": 1, "AU-How": 1, "AU-Stp": 1, "AU-Tum": 1}
MET = ("Ta", "SH", "ps", "Fsd", "Fld", "Ws", "Precip")
QC_SOURCE_HINT = {
    400: "PyFluxPro GapFillFromAlternate default",
    410: "PyFluxPro GapFillFromAlternate AWS",
    420: "PyFluxPro GapFillFromAlternate ACCESS",
    430: "PyFluxPro GapFillFromAlternate ERA-Interim",
    440: "PyFluxPro GapFillFromAlternate ERA5",
}
REFERENCE = "https://github.com/OzFlux/PyFluxPro/blob/main/scripts/pfp_gf.py"
FIELDS = ("long_name", "units", "height", "instrument", "source",
          "description_L1", "description_L2", "description_L3",
          "description_L4", "description_L5", "description_L6",
          "coverage_L6", "flag_meanings", "flag_values")
DETAIL_COLUMNS = [
    "site", "filename", "target", "donor", "index", "native_time",
    "target_value", "target_qc", "donor_value", "donor_qc",
    "source_primary_previous", "source_primary_next",
]
SUMMARY_COLUMNS = [
    "site", "filename", "target", "donor", "missing_target_rows",
    "donor_valid_at_gaps", "donor_qc0_at_gaps", "donor_nonzero_qc_at_gaps",
    "donor_qc_missing_at_gaps", "donor_gt20_at_gaps_if_Fsd",
    "all_valid_overlap_n", "both_qc0_overlap_n",
    "mean_donor_minus_main_both_qc0",
    "rmse_both_qc0", "median_abs_error_both_qc0",
    "p95_abs_error_both_qc0", "day_proxy_overlap_n_if_Fsd",
    "day_proxy_rmse_if_Fsd", "decision"
]


def rows_manifest(path):
    with path.open(encoding="utf-8-sig", newline="") as h:
        reader = csv.DictReader(h, delimiter="\t")
        if reader.fieldnames != ["site", "filename"]:
            raise ValueError("Invalid manifest columns")
        rows = list(reader)
    counts = {x: 0 for x in SITES}
    seen = set()
    for r in rows:
        site, name = r["site"], r["filename"]
        if site not in counts or not name.endswith(".nc") or any(x in name for x in ("/", "\\", "..")):
            raise ValueError("Unsafe manifest entry: " + repr(r))
        if (site, name) in seen:
            raise ValueError("Duplicate manifest entry")
        counts[site] += 1
        seen.add((site, name))
    if len(rows) != 10 or counts != SITES:
        raise ValueError("Expected 10 files across 9 exact station IDs")
    return rows


def metadata(v):
    obj = {}
    for name in FIELDS:
        if name in v.ncattrs():
            val = v.getncattr(name)
            if hasattr(val, "tolist"):
                val = val.tolist()
            obj[name] = str(val)[:1000]
    return obj


def timeseries(v, time_dim, n):
    if not np.issubdtype(v.dtype, np.number):
        return None
    if v.dimensions.count(time_dim) != 1:
        return None
    if v.shape[v.dimensions.index(time_dim)] != n:
        return None
    if any(d != time_dim and v.shape[i] != 1 for i, d in enumerate(v.dimensions)):
        return None
    z = np.ma.asarray(v[:], dtype=np.float64).filled(np.nan).reshape(-1)
    return z if len(z) == n else None


def valid(z):
    return np.isfinite(z) & (z > -9990)


def qc_hist(q):
    if q is None:
        return None
    z = q[np.isfinite(q)]
    v, n = np.unique(z, return_counts=True)
    return {str(int(value)) if value.is_integer() else str(value): int(cnt)
            for value, cnt in zip(v, n)}


def qc_subset(q, ix):
    if q is None:
        return None
    return qc_hist(q[ix])


def difference_stats(x, y, mask):
    delta = y[mask] - x[mask]
    if not len(delta):
        return {"n": 0, "mean": None, "rmse": None,
                "median_abs": None, "p95_abs": None}
    absdelta = np.abs(delta)
    return {"n": int(len(delta)), "mean": float(np.mean(delta)),
            "rmse": float(np.sqrt(np.mean(delta * delta))),
            "median_abs": float(np.median(absdelta)),
            "p95_abs": float(np.percentile(absdelta, 95))}


def utc_unverified_label(ds, index):
    t = ds.variables["time"]
    return str(netCDF4.num2date(float(t[index]), t.units,
                                calendar=getattr(t, "calendar", "standard")))


def audit_source(ds, row, candidate_data):
    site, filename = row["site"], row["filename"]
    time = ds.variables["time"]
    n = len(time)
    if time.ndim != 1:
        raise ValueError("Unexpected source time coordinate")
    time_dim = time.dimensions[0]
    out = {"site": site, "filename": filename, "records": n,
           "status": "QC_PROVENANCE_SCREENED_NOT_APPROVED",
           "flag_code_source_reference": REFERENCE,
           "flag_code_400_mapping_is_a_hypothesis_not_site_source_proof": QC_SOURCE_HINT,
           "native_time_not_assumed_UTC": True,
           "main_meteorological": {}, "donor_comparisons": []}
    main_arrays = {}
    main_flags = {}
    for name in MET:
        if name not in ds.variables:
            out["main_meteorological"][name] = {"status": "SOURCE_MISSING"}
            continue
        main = ds.variables[name]
        x = timeseries(main, time_dim, n)
        qname = name + "_QCFlag"
        q = timeseries(ds.variables[qname], time_dim, n) if qname in ds.variables else None
        main_arrays[name], main_flags[name] = x, q
        out["main_meteorological"][name] = {
            "metadata": metadata(main),
            "qc_variable": qname if q is not None else None,
            "qc_metadata": metadata(ds.variables[qname]) if qname in ds.variables else None,
            "qc_count_all_records_uninterpreted": qc_hist(q),
            "qc_count_finite_data_only": qc_hist(q[valid(x)]) if x is not None and q is not None else None,
            "n_missing": int(np.sum(~valid(x))) if x is not None else None,
        }

    detailed = []
    summary = []
    for candidate in candidate_data:
        target = candidate["target_variable"]
        donor = candidate["candidate"]
        if target not in main_arrays or main_arrays[target] is None:
            continue
        if donor not in ds.variables:
            raise ValueError("Stage04 donor missing from source: " + donor)
        main = main_arrays[target]
        qmain = main_flags[target]
        obj = ds.variables[donor]
        d = timeseries(obj, time_dim, n)
        qunits = out["main_meteorological"][target]["metadata"].get("units")
        dunits = metadata(obj).get("units")
        exact_units = bool(qunits and dunits and qunits.strip().lower() == dunits.strip().lower())
        entry = {
            "target": target, "donor": donor,
            "donor_metadata": metadata(obj),
            "donor_qc_metadata": metadata(ds.variables[donor+"_QCFlag"])
            if donor+"_QCFlag" in ds.variables else None,
            "unit_match_strict": exact_units,
            "stage04_reported_valid_at_target_missing": candidate.get("valid_at_target_missing"),
            "sciencedecision": "HOLD_SENSOR_INDEPENDENCE_AND_PROVENANCE",
        }
        if d is None or not exact_units:
            entry["reason"] = "Shape/numeric or units not strictly compatible"
            out["donor_comparisons"].append(entry)
            continue

        qname = donor+"_QCFlag"
        qdonor = timeseries(ds.variables[qname], time_dim, n) if qname in ds.variables else None
        gaps = ~valid(main)
        atgap = np.flatnonzero(gaps & valid(d))
        if candidate.get("valid_at_target_missing") is not None and len(atgap) != int(candidate["valid_at_target_missing"]):
            raise ValueError("Stage04 and Stage05 candidate mismatch; source or processing changed")

        both = valid(main) & valid(d)
        both_qc0 = (both & (qmain == 0) & (qdonor == 0)
                    if qmain is not None and qdonor is not None
                    else np.zeros(n, dtype=bool))
        stats_all = difference_stats(main, d, both)
        stats_qc0 = difference_stats(main, d, both_qc0)
        daylight = (both_qc0 & (main > 20) & (d > 20)) if target == "Fsd" else np.zeros(n,dtype=bool)
        stats_day = difference_stats(main, d, daylight)
        valid_at_gap = valid(d[atgap])
        assert valid_at_gap.all()
        qc0gap = int(np.sum(qdonor[atgap] == 0)) if qdonor is not None else None
        unknown_qcgap = int(np.sum(~np.isfinite(qdonor[atgap]))) if qdonor is not None else len(atgap)
        nonzero_qcgap = int(np.sum(np.isfinite(qdonor[atgap]) & (qdonor[atgap] != 0))) if qdonor is not None else None
        entry.update({
            "source_target_missing_count": int(np.sum(gaps)),
            "donor_valid_at_target_missing_count": int(len(atgap)),
            "donor_qc0_at_gap_count": qc0gap,
            "donor_nonzero_qc_at_gap_count": nonzero_qcgap,
            "donor_qc_nonfinite_at_gap_count": unknown_qcgap,
            "donor_qc_at_gap_histogram_uninterpreted": qc_subset(qdonor, atgap),
            "target_qc_at_gap_histogram_uninterpreted": qc_subset(qmain, atgap),
            "source_donor_QC0_overlap_is_comparison_stratum_not_observation_proof": True,
            "all_finite_overlap_stats": stats_all,
            "both_qc0_overlap_stats": stats_qc0,
            "Fsd_two_positive_gt20_overlapping_qc0_proxy_stats": stats_day if target == "Fsd" else None,
            "Fsd_donor_gt20_at_gap": int(np.sum(d[atgap] > 20)) if target == "Fsd" else None,
        })
        out["donor_comparisons"].append(entry)
        summary.append({
            "site": site, "filename": filename, "target": target, "donor": donor,
            "missing_target_rows": entry["source_target_missing_count"],
            "donor_valid_at_gaps": len(atgap),
            "donor_qc0_at_gaps": qc0gap,
            "donor_nonzero_qc_at_gaps": nonzero_qcgap,
            "donor_qc_missing_at_gaps": unknown_qcgap,
            "donor_gt20_at_gaps_if_Fsd": entry["Fsd_donor_gt20_at_gap"],
            "all_valid_overlap_n": stats_all["n"], "both_qc0_overlap_n": stats_qc0["n"],
            "mean_donor_minus_main_both_qc0": stats_qc0["mean"],
            "rmse_both_qc0": stats_qc0["rmse"],
            "median_abs_error_both_qc0": stats_qc0["median_abs"],
            "p95_abs_error_both_qc0": stats_qc0["p95_abs"],
            "day_proxy_overlap_n_if_Fsd": stats_day["n"] if target=="Fsd" else None,
            "day_proxy_rmse_if_Fsd": stats_day["rmse"] if target=="Fsd" else None,
            "decision": entry["sciencedecision"],
        })
        for i in atgap:
            i = int(i)
            detailed.append({
                "site": site, "filename": filename, "target": target, "donor": donor,
                "index": i, "native_time": utc_unverified_label(ds, i),
                "target_value": float(main[i]) if np.isfinite(main[i]) else None,
                "target_qc": float(qmain[i]) if qmain is not None and np.isfinite(qmain[i]) else None,
                "donor_value": float(d[i]),
                "donor_qc": float(qdonor[i]) if qdonor is not None and np.isfinite(qdonor[i]) else None,
                "source_primary_previous": float(main[i-1]) if i>0 and valid(main[i-1:i])[0] else None,
                "source_primary_next": float(main[i+1]) if i+1<n and valid(main[i+1:i+2])[0] else None,
            })
    return out, summary, detailed


def write_tsv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, delimiter="\t", fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def self_test():
    z = np.array([np.nan, -9999.0, -0.1, 12.0])
    assert valid(z).tolist() == [False, False, True, True]
    m = np.array([1.0, 2.0, 3.0, 4.0])
    d = np.array([2.0, 2.0, 2.0, 4.0])
    q = np.array([0.0, 0.0, 420.0, 440.0])
    mask = q == 0
    s = difference_stats(m,d,mask)
    assert s["n"]==2 and s["mean"]==0.5 and s["rmse"]>0
    assert qc_hist(q)=={"0":2,"420":1,"440":1}
    assert QC_SOURCE_HINT[410].endswith("AWS")
    assert QC_SOURCE_HINT[420].endswith("ACCESS")
    assert QC_SOURCE_HINT[440].endswith("ERA5")
    print("STAGE05 SELF-TEST PASS: missing/QC handling, codebook and QC0 comparison; read-only")


def main():
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        return 0
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--stage04", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--root", type=Path, default=ROOT)
    a = p.parse_args()
    root, out = a.root.resolve(), a.out.resolve()
    if a.out.is_symlink() or out == root or root in out.parents:
        raise ValueError("Refusing report output inside the original source tree")
    if out.exists():
        raise FileExistsError("Output directory exists; choose new timestamp")
    source_rows = rows_manifest(a.manifest)
    stage04_file = a.stage04/"stage04_evidence.json"
    with stage04_file.open(encoding="utf-8") as h:
        prev = json.load(h)
    if prev.get("audited") != 10 or prev.get("science_approval") is not False:
        raise ValueError("Stage04 must be complete, unapproved and unchanged")
    index = {(f["site"], f["filename"]):f for f in prev["files"]}
    if set(index) != {(r["site"],r["filename"]) for r in source_rows}:
        raise ValueError("Stage04 file inventory does not match manifest")
    out.mkdir(parents=True)
    entries, summaries, detailed = [], [], []
    for row in source_rows:
        site, filename = row["site"], row["filename"]
        path = root/site/"forcing"/"raw"/filename
        try:
            if path.is_symlink() or not path.is_file():
                raise FileNotFoundError("Original file missing/symlinked")
            with netCDF4.Dataset(str(path),mode="r") as ds:
                report, s, d = audit_source(ds, row, index[(site,filename)].get("candidate_donors",[]))
            entries.append(report)
            summaries.extend(s)
            detailed.extend(d)
            print("AUDITED",site,filename,"DONORS",len(report["donor_comparisons"]),
                  "GAP_VALUES",len(d))
        except Exception as exc:
            entries.append({"site":site,"filename":filename,"status":"ERROR",
                            "error":type(exc).__name__+": "+str(exc)[:400]})
            print("ERROR",site,filename,type(exc).__name__,str(exc)[:250])
    output = {
        "stage":"OzFlux Stage05 native QC flag and sensor donor verification",
        "science_approval":False, "source_read_only":True,
        "external_codebook_origin":REFERENCE,
        "mapping_source_hints_not_measurement_provenance_proof":QC_SOURCE_HINT,
        "files":entries,
        "audited":sum(x["status"]=="QC_PROVENANCE_SCREENED_NOT_APPROVED" for x in entries),
    }
    (out/"stage05_qc_provenance.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    write_tsv(out/"stage05_donor_comparison.tsv",summaries,SUMMARY_COLUMNS)
    write_tsv(out/"stage05_candidate_gap_values.tsv",detailed,DETAIL_COLUMNS)
    print("AUDITED",output["audited"],"/10","DONOR_COMPARISONS",len(summaries),"CANDIDATE_ROWS",len(detailed))
    print("REPORT_DIR",out)
    print("NO SOURCE EDITS, NO QC APPROVAL, NO FORCING OR SLURM")
    return 0 if output["audited"]==10 else 1


if __name__=="__main__":
    raise SystemExit(main())

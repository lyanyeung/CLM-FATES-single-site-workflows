#!/usr/bin/env python3
"""OzFlux 9-site Stage06A: targeted donor lineage and gap physics, READ ONLY.

For AU-Cpr Ta, AU-Gin Fsd, and AU-How Fsd. Authorisation: science audit only.
No modifications to source NetCDFs, no gap fills, no interpolation, no
timezone transformation, no DATM, and no Slurm.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import netCDF4
import numpy as np

DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EXPECTED = {
    "AU-ASM": 2, "AU-Cow": 1, "AU-Cpr": 1, "AU-DaS": 1,
    "AU-Dry": 1, "AU-Gin": 1, "AU-How": 1, "AU-Stp": 1, "AU-Tum": 1,
}
TARGETS = {
    "AU-Cpr": {"Ta": ("Ta_HMP_2m", "Ta_SONIC_Av")},
    "AU-Gin": {"Fsd": ("Fsd_1", "Fsd_7m")},
    "AU-How": {"Fsd": ("Fsd_ARM",)},
}
METADATA_KEYS = (
    "units", "long_name", "height", "instrument", "source",
    "description_L1", "description_L2", "description_L3",
    "description_L4", "description_L5", "description_L6",
    "coverage_L6", "flag_meanings", "flag_values",
)
SUMMARY_COLS = (
    "site", "filename", "target", "donor", "source_gap_count",
    "donor_finite_at_gap", "donor_qc0_at_gap",
    "donor_below_equal_20_at_gap", "donor_above_20_at_gap",
    "donor_min_at_gap", "donor_max_at_gap",
    "both_finite_overlap", "both_QC0_overlap",
    "both_QC0_identical_n", "both_QC0_identical_fraction",
    "both_QC0_RMSE", "both_QC0_day_proxy_n",
    "both_QC0_day_proxy_RMSE", "science_decision",
)
RECORD_COLS = (
    "site", "filename", "target", "donor", "source_index",
    "native_time_unverified_timezone", "target_raw_value",
    "target_QCFlag", "donor_raw_value", "donor_QCFlag",
    "previous_target_raw_value", "next_target_raw_value",
    "previous_donor_raw_value", "next_donor_raw_value",
)


def source_manifest(path):
    with path.open(encoding="utf-8-sig", newline="") as h:
        reader = csv.DictReader(h, delimiter="\t")
        if reader.fieldnames != ["site", "filename"]:
            raise ValueError("Bad manifest header")
        rows = list(reader)
    counts = dict.fromkeys(EXPECTED, 0)
    keys = set()
    for row in rows:
        site, name = row["site"], row["filename"]
        if site not in EXPECTED or not name.endswith(".nc") or any(x in name for x in ("/", "\\", "..")):
            raise ValueError("Unsafe or unexpected source manifest row")
        if (site, name) in keys:
            raise ValueError("Duplicate source manifest row")
        counts[site] += 1
        keys.add((site, name))
    if len(rows) != 10 or counts != EXPECTED:
        raise ValueError("Stage06 requires exact nine-site/ten-file manifest")
    return rows


def attrs(v):
    result = {}
    for key in METADATA_KEYS:
        if key in v.ncattrs():
            value = v.getncattr(key)
            if hasattr(value, "tolist"):
                value = value.tolist()
            result[key] = str(value)[:1000]
    return result


def numeric(ds, name, timedim, n):
    if name not in ds.variables:
        raise KeyError("Missing source NetCDF field: " + name)
    v = ds.variables[name]
    if not np.issubdtype(v.dtype, np.number):
        raise ValueError(name + " is not numeric")
    if v.dimensions.count(timedim) != 1:
        raise ValueError(name + " has no unique time dimension")
    if v.shape[v.dimensions.index(timedim)] != n:
        raise ValueError(name + " time length inconsistent")
    if any(d != timedim and v.shape[i] != 1 for i, d in enumerate(v.dimensions)):
        raise ValueError(name + " has non-singleton non-time dimensions")
    result = np.ma.asarray(v[:], dtype=float).filled(np.nan).reshape(-1)
    if len(result) != n:
        raise ValueError(name + " unexpected reshaping")
    return result


def is_valid(v):
    return np.isfinite(v) & (v > -9990.0)


def display_number(v):
    return float(v) if np.isfinite(v) else None


def histogram(v):
    if v is None:
        return None
    x = v[np.isfinite(v)]
    codes, counts = np.unique(x, return_counts=True)
    return {
        (str(int(c)) if float(c).is_integer() else str(float(c))): int(k)
        for c, k in zip(codes, counts)
    }


def comparisons(a, b, mask):
    diff = b[mask] - a[mask]
    if not len(diff):
        return {"n": 0, "identical_n": 0, "identical_fraction": None,
                "rmse": None, "mean_diff": None, "median_abs_diff": None,
                "p95_abs_diff": None}
    identical = np.isclose(a[mask], b[mask], atol=1e-9, rtol=0)
    return {
        "n": int(len(diff)),
        "identical_n": int(identical.sum()),
        "identical_fraction": float(identical.mean()),
        "rmse": float(np.sqrt(np.mean(diff**2))),
        "mean_diff": float(np.mean(diff)),
        "median_abs_diff": float(np.median(np.abs(diff))),
        "p95_abs_diff": float(np.percentile(np.abs(diff), 95)),
    }


def timestamp(t, i, units, calendar):
    return str(netCDF4.num2date(float(t[i]), units, calendar=calendar))


def one_file(path, site, filename, prior):
    expected_targets = TARGETS[site]
    with netCDF4.Dataset(str(path), mode="r") as ds:
        if "time" not in ds.variables:
            raise ValueError("Missing time")
        time_var = ds.variables["time"]
        if time_var.ndim != 1:
            raise ValueError("Invalid time dimension")
        time = np.ma.asarray(time_var[:], dtype=float).filled(np.nan)
        if not len(time) or not np.isfinite(time).all() or np.any(np.diff(time) <= 0):
            raise ValueError("Invalid time axis")
        units = str(time_var.units)
        calendar = getattr(time_var, "calendar", "standard")
        dim, n = time_var.dimensions[0], len(time)
        output = {
            "site": site, "filename": filename,
            "mode": "SOURCE_READ_ONLY_SCIENCE_HOLD",
            "raw_root": str(path),
            "native_time_units": units, "native_calendar": str(calendar),
            "timezone_not_confirmed": True,
            "global_timezone_attrs": {
                key: str(ds.getncattr(key))[:400]
                for key in ds.ncattrs()
                if any(x in key.lower() for x in ("time_zone", "timezone", "time_step"))
            },
            "comparisons": [],
        }
        summaries, records = [], []
        prior_index = {(x["target"], x["donor"]): x
                       for x in prior.get("donor_comparisons", [])}
        for target, donors in expected_targets.items():
            main = numeric(ds, target, dim, n)
            qm = numeric(ds, target + "_QCFlag", dim, n)
            gaps = ~is_valid(main)
            gap_count = int(gaps.sum())
            for donor in donors:
                if (target, donor) not in prior_index:
                    raise ValueError("Missing earlier Stage05 donor: "+target+"/"+donor)
                d = numeric(ds, donor, dim, n)
                qd = numeric(ds, donor+"_QCFlag", dim, n)
                if attrs(ds.variables[target]).get("units") != attrs(ds.variables[donor]).get("units"):
                    raise ValueError("Main and donor reported units differ: "+target+"/"+donor)
                available = np.flatnonzero(gaps & is_valid(d))
                prior_n = prior_index[(target, donor)].get(
                    "donor_valid_at_target_missing_count")
                if prior_n is None or int(prior_n) != len(available):
                    raise ValueError("Stage05 candidate coverage mismatch: "+donor)
                if prior_index[(target, donor)].get("source_target_missing_count") != gap_count:
                    raise ValueError("Stage05 main gap count mismatch")
                both = is_valid(main) & is_valid(d)
                both0 = both & (qm == 0) & (qd == 0)
                day_proxy = (
                    both0 & (main > 20) & (d > 20)
                    if target == "Fsd" else np.zeros(n, dtype=bool)
                )
                bothstats = comparisons(main,d,both)
                exactstats = comparisons(main,d,both0)
                daystats = comparisons(main,d,day_proxy)
                usable = d[available]
                nlow = int(np.sum(usable <= 20))
                nhigh = int(np.sum(usable > 20))
                nqc0 = int(np.sum(qd[available] == 0))
                donor_info = {
                    "target":target, "donor":donor,
                    "source_missing_count":gap_count,
                    "valid_donor_rows_on_missing_target":int(len(available)),
                    "target_flag_at_covered_gaps":histogram(qm[available]),
                    "donor_flag_at_covered_gaps":histogram(qd[available]),
                    "all_main_gap_flag_distribution":histogram(qm[gaps]),
                    "donor_main_metadata":attrs(ds.variables[target]),
                    "donor_metadata":attrs(ds.variables[donor]),
                    "main_qc_metadata":attrs(ds.variables[target+"_QCFlag"]),
                    "donor_qc_metadata":attrs(ds.variables[donor+"_QCFlag"]),
                    "overlap_all_finite":bothstats,
                    "overlap_both_native_QC0":exactstats,
                    "overlap_both_QC0_and_both_values_gt20_wm2_proxy_if_Fsd":(
                        daystats if target=="Fsd" else None),
                    "donor_at_missing_min":(float(np.min(usable)) if len(usable) else None),
                    "donor_at_missing_max":(float(np.max(usable)) if len(usable) else None),
                    "donor_at_missing_le20":nlow if target=="Fsd" else None,
                    "donor_at_missing_gt20":nhigh if target=="Fsd" else None,
                    "low_Fsd_is_NOT_proof_of_nighttime":True,
                    "QC0_is_NOT_proof_of_independent_source":True,
                    "science_decision":"HOLD_UNTIL_SENSOR_LINEAGE_AND_TIMEZONE_REVIEW",
                }
                output["comparisons"].append(donor_info)
                summaries.append({
                    "site":site, "filename":filename, "target":target,"donor":donor,
                    "source_gap_count":gap_count, "donor_finite_at_gap":len(available),
                    "donor_qc0_at_gap":nqc0,
                    "donor_below_equal_20_at_gap":nlow if target=="Fsd" else None,
                    "donor_above_20_at_gap":nhigh if target=="Fsd" else None,
                    "donor_min_at_gap":donor_info["donor_at_missing_min"],
                    "donor_max_at_gap":donor_info["donor_at_missing_max"],
                    "both_finite_overlap":bothstats["n"],
                    "both_QC0_overlap":exactstats["n"],
                    "both_QC0_identical_n":exactstats["identical_n"],
                    "both_QC0_identical_fraction":exactstats["identical_fraction"],
                    "both_QC0_RMSE":exactstats["rmse"],
                    "both_QC0_day_proxy_n":daystats["n"] if target=="Fsd" else None,
                    "both_QC0_day_proxy_RMSE":daystats["rmse"] if target=="Fsd" else None,
                    "science_decision":donor_info["science_decision"],
                })
                for i in available:
                    i=int(i)
                    records.append({
                        "site":site, "filename":filename, "target":target, "donor":donor,
                        "source_index":i,
                        "native_time_unverified_timezone":timestamp(time,i,units,calendar),
                        "target_raw_value":display_number(main[i]),
                        "target_QCFlag":display_number(qm[i]),
                        "donor_raw_value":display_number(d[i]),
                        "donor_QCFlag":display_number(qd[i]),
                        "previous_target_raw_value":display_number(main[i-1]) if i else None,
                        "next_target_raw_value":display_number(main[i+1]) if i+1<n else None,
                        "previous_donor_raw_value":display_number(d[i-1]) if i else None,
                        "next_donor_raw_value":display_number(d[i+1]) if i+1<n else None,
                    })
        return output, summaries, records


def write_tsv(path, rows, cols):
    with path.open("w", encoding="utf-8", newline="") as h:
        writer=csv.DictWriter(h, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def self_test():
    a=np.array([1.0,2.0,3.0,np.nan])
    b=np.array([1.0,2.0,4.0,9.0])
    q=np.array([0.0,0.0,0.0,50.0])
    z=comparisons(a,b,is_valid(a)&is_valid(b)&(q==0))
    assert z["n"]==3 and z["identical_n"]==2
    assert abs(z["rmse"]-np.sqrt(1/3))<1e-12
    assert histogram(np.array([0,0,50,np.nan]))=={"0":2,"50":1}
    assert (~is_valid(np.array([-9999.,-0.1,0,0.1]))).tolist()==[True,False,False,False]
    print("STAGE06 SELF-TEST PASS: exact-match lineage, missing-sentinel, histogram; NO SOURCE WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        self_test()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--stage05",required=True,type=Path)
    p.add_argument("--root",type=Path,default=DEFAULT_ROOT)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    root,out=a.root.resolve(),a.out.resolve()
    if a.out.is_symlink() or out==root or root in out.parents:
        raise ValueError("Reports may not reside in source NetCDF tree")
    if out.exists():
        raise FileExistsError("Output already exists. Use a NEW timestamp")
    rows=source_manifest(a.manifest)
    prior_json=a.stage05/"stage05_qc_provenance.json"
    with prior_json.open(encoding="utf-8") as h:
        prior=json.load(h)
    if prior.get("audited")!=10 or prior.get("science_approval") is not False:
        raise ValueError("Stage05 must show 10/10 and no scientific approval")
    prior_index={(x["site"],x["filename"]):x for x in prior["files"]}
    if len(prior_index)!=10 or set(prior_index)!={(r["site"],r["filename"]) for r in rows}:
        raise ValueError("Stage05 provenance does not match exact source manifest")

    reports=[]
    summaries=[]
    records=[]
    for row in rows:
        site,filename=row["site"],row["filename"]
        if site not in TARGETS:
            continue
        path=root/site/"forcing"/"raw"/filename
        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError("Original source missing or symlinked: "+str(path))
        one,ss,rr=one_file(path,site,filename,prior_index[(site,filename)])
        reports.append(one)
        summaries.extend(ss)
        records.extend(rr)
        print("TARGET_SOURCE",site,"DONOR_COMPARISONS",len(ss),"CANDIDATE_ROWS",len(rr))

    if len(reports)!=3 or len(summaries)!=5:
        raise ValueError("Expected exactly three site files and five candidate donor comparisons")
    out.mkdir(parents=True)
    output={
        "stage":"OzFlux Stage06A targeted source sensor lineage evidence",
        "read_only_source":True, "science_approval":False,
        "source_codebook_note":"QC0 not guaranteed native observation; gapfilled L6 can carry source-specific flags",
        "files":reports,
        "target_site_count":len(reports),
        "donor_comparison_count":len(summaries),
        "candidate_record_count":len(records),
    }
    (out/"stage06_lineage_evidence.json").write_text(
        json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    write_tsv(out/"stage06_donor_lineage_summary.tsv",summaries,SUMMARY_COLS)
    write_tsv(out/"stage06_exact_candidate_records.tsv",records,RECORD_COLS)
    print("STAGE06_AUDIT PASS",len(reports),"SOURCE_FILES",len(summaries),"DONORS",len(records),"CANDIDATE_ROWS")
    print("REPORT_DIR",out)
    print("NO NETCDF MODIFIED; NO AUTOMATIC REPAIR; NO MODEL JOBS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

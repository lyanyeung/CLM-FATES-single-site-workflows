#!/usr/bin/env python3
"""Stage08d: provenance and severity of 1924 winter VPD humidity blockers.

Uses previously verified Stage08c evidence (NOT new raw forcing); checks report
lineage and whether primary and companion ERA TA/VPD resemble each other.
No correction or replacement is authorized. --check writes nothing.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE08 = BASE / "raw_RH_sensitivity_20261022T025645Z_3c43eb8b"
STAGE08B = BASE / "reports/stage08b_rh_cause_20261022T030908Z_f8927638"
STAGE08C = BASE / "reports/stage08c_era_humidity_20261022T031437Z_512e8731"
COUNTS = {"US-Kon":229, "US-MMS":18, "US-Me2":4, "US-Me6":1,
          "US-MtB":15, "US-NR1":173, "US-NR3":1484}
NEEDED = ["site","time","source_csv_row","VPD_original_QC",
          "TA_before_fallback_C","VPD_before_fallback_hPa",
          "TA_ERA_C","VPD_ERA_hPa","ERA_RH_pct",
          "rejection_primary_reason"]

def hashfile(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1048576), b""):
            h.update(data)
    return h.hexdigest()

def numbers(frame,col):
    x = pd.to_numeric(frame[col],errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x) | (x <= -9990)] = np.nan
    return x

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args = parser.parse_args()
    for folder in (BASE, STAGE08, STAGE08B, STAGE08C):
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Missing or unsafe evidence directory: "+str(folder))
    if not (STAGE08 / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file():
        raise ValueError("Stage08 incomplete marker missing")
    scope = json.loads((STAGE08C/"evidence_scope.json").read_text(encoding="utf-8"))
    if (Path(scope["stage08_root"]).resolve()!=STAGE08
            or Path(scope["stage08b_report"]).resolve()!=STAGE08B
            or scope["residual_records"]!=1924
            or hashfile(STAGE08/"output_sha256.json")!=scope["stage08_sha256_manifest"]
            or hashfile(STAGE08B/"unresolved_rh_records.csv")!=scope["stage08b_unresolved_csv_sha256"]):
        raise ValueError("Stage08c report lineage/hash mismatch")
    f = STAGE08C/"era_humidity_residual_details.csv"
    if f.is_symlink() or not f.is_file():
        raise ValueError("Missing Stage08c residual details")
    df = pd.read_csv(f,dtype=str,keep_default_na=False)
    if (len(df)!=1924 or any(x not in df.columns for x in NEEDED)
            or set(df.site)!=set(COUNTS)
            or not df.rejection_primary_reason.eq("ERA_RH_BELOW_MINUS2_PCT").all()):
        raise ValueError("Stage08c row count, schema or rejection causes changed")
    for site,count in COUNTS.items():
        subset = df[df.site.eq(site)]
        if len(subset)!=count or subset.source_csv_row.duplicated().any():
            raise ValueError("Invalid site row ID / count: "+site)
    timestamps = pd.to_datetime(df.time,errors="raise")
    if timestamps.duplicated().all():
        raise ValueError("Unexpected duplicated event timestamps")
    ts = numbers(df,"TA_before_fallback_C")
    vs = numbers(df,"VPD_before_fallback_hPa")
    te = numbers(df,"TA_ERA_C")
    ve = numbers(df,"VPD_ERA_hPa")
    rh = numbers(df,"ERA_RH_pct")
    qc = numbers(df,"VPD_original_QC")
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        es_e = 6.112*np.exp(np.clip(17.67*te/(te+243.5),-40,40))
        es_s = 6.112*np.exp(np.clip(17.67*ts/(ts+243.5),-40,40))
        rhcheck = 100*(es_e-ve)/es_e
    finite = np.isfinite(rh) & np.isfinite(rhcheck)
    if not np.allclose(rh[finite],rhcheck[finite],atol=1e-6,rtol=1e-8):
        raise ValueError("ERA RH no longer matches ERA TA/VPD")
    if finite.sum()!=1924:
        raise ValueError("Some ERA RH values unexpectedly nonfinite")
    rawQC = sorted(set(qc[np.isfinite(qc)].astype(int)))
    if (qc==0).any():
        raise ValueError("Original VPD QC0 unexpectedly present")

    detail = df[NEEDED].copy()
    detail["year"] = timestamps.dt.year
    detail["month"] = timestamps.dt.month
    detail["delta_TA_site_minus_ERA_C"] = ts-te
    detail["delta_VPD_site_minus_ERA_hPa"] = vs-ve
    detail["ERA_saturation_water_hPa"] = es_e
    detail["ERA_VPD_over_es"] = ve/es_e
    detail["ERA_excess_VPD_over_es_hPa"] = ve-es_e
    detail["site_excess_VPD_over_es_hPa"] = vs-es_s
    detail["ERA_RH_recomputed_pct"] = rhcheck
    detail["original_VPD_QC"] = qc
    detail["TA_nearly_same_0p05C"] = np.isfinite(ts)&np.isfinite(te)&(abs(ts-te)<=0.05)
    detail["VPD_nearly_same_0p05hPa"] = np.isfinite(vs)&np.isfinite(ve)&(abs(vs-ve)<=0.05)
    detail["TA_VPD_both_nearly_same"] = detail.TA_nearly_same_0p05C & detail.VPD_nearly_same_0p05hPa
    detail["ERA_RH_below_minus_10pct"] = rh < -10
    detail["ERA_RH_below_minus_100pct"] = rh < -100
    detail["site_TA_below_minus10C"] = ts < -10
    detail["ERA_TA_below_minus10C"] = te < -10

    summary = []
    for site in COUNTS:
        sub = detail.loc[detail.site.eq(site)]
        originalQC = sub.original_VPD_QC
        summary.append(dict(site=site, records=len(sub),
            QC0=int((originalQC==0).sum()),
            QC1=int((originalQC==1).sum()), QC2=int((originalQC==2).sum()),
            QC_missing=int(originalQC.isna().sum()),
            both_TA_VPD_nearly_identical=int(sub.TA_VPD_both_nearly_same.sum()),
            TA_nearly_same=int(sub.TA_nearly_same_0p05C.sum()),
            VPD_nearly_same=int(sub.VPD_nearly_same_0p05hPa.sum()),
            ERA_RH_min=float(sub.ERA_RH_recomputed_pct.min()),
            ERA_RH_median=float(sub.ERA_RH_recomputed_pct.median()),
            ERA_RH_max=float(sub.ERA_RH_recomputed_pct.max()),
            ERA_VPD_over_es_median=float(sub.ERA_VPD_over_es.median()),
            ERA_excess_VPD_over_es_max_hPa=float(sub.ERA_excess_VPD_over_es_hPa.max()),
            temp_site_below_minus10C=int(sub.site_TA_below_minus10C.sum()),
            temp_ERA_below_minus10C=int(sub.ERA_TA_below_minus10C.sum()),
            flagged_months=",".join(str(m) for m in sorted(sub.month.unique())),
        ))
    by_site=pd.DataFrame(summary)
    by_ym = detail.groupby(["site","year","month"]).agg(
        records=("site","size"),RH_ERA_min=("ERA_RH_recomputed_pct","min"),
        RH_ERA_median=("ERA_RH_recomputed_pct","median"),
        paired_TA_VPD_nearly_same=("TA_VPD_both_nearly_same","sum")).reset_index()

    # Native consecutive-interval episodes. A leap-day calendar boundary
    # starts a new episode; duration is still correct for contiguous records.
    runs=[]
    for site in COUNTS:
        sub=detail[detail.site.eq(site)].copy()
        sub["_when"]=pd.to_datetime(sub.time)
        sub=sub.sort_values("_when")
        step=60 if site=="US-MMS" else 30
        grp=sub["_when"].diff().ne(pd.Timedelta(minutes=step)).cumsum()
        for _,part in sub.groupby(grp):
            runs.append(dict(site=site,first_timestamp=part.time.iloc[0],
                last_timestamp=part.time.iloc[-1],native_minutes=step,
                records=len(part),hours=len(part)*step/60,
                min_ERA_RH_pct=float(part.ERA_RH_recomputed_pct.min()),
                QC1=int((part.original_VPD_QC==1).sum()),
                QC2=int((part.original_VPD_QC==2).sum())))
    runframe=pd.DataFrame(runs).sort_values(["hours","site"],ascending=[False,True])
    print("STAGE08D: Stage08c/08b/08 immutable report lineage verified")
    print("PRIMARY VPD QC present codes:",rawQC)
    print("\nWINTER VPD PROVENANCE BY SITE")
    print(by_site.to_string(index=False))
    print("\nLONGEST CONSECUTIVE BLOCKER EPISODES")
    print(runframe.head(12).to_string(index=False))
    print("\nSTAGE08D PREFLIGHT: 1924/1924 event pairs classified; no replacement or forcing changes")
    if args.check:
        print("CHECK ONLY: no report files created")
        return
    root=BASE/"reports"
    out=root/("stage08d_vpd_provenance_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    detail.to_csv(out/"winter_vpd_events.csv",index=False)
    by_site.to_csv(out/"site_vpd_provenance_summary.csv",index=False)
    by_ym.to_csv(out/"monthly_vpd_events.csv",index=False)
    runframe.to_csv(out/"consecutive_vpd_episodes.csv",index=False)
    (out/"provenance.json").write_text(json.dumps({
        "source_evidence":str(STAGE08C),
        "stage08c_scope_sha256":hashfile(STAGE08C/"evidence_scope.json"),
        "stage08c_details_sha256":hashfile(f),
        "records":1924,
        "interpretation":"Numerical evidence only: similar original/ERA data are NOT independent corroboration",
        "changes":"No changes to raw, QCv5, DATM, surfaces, cases, Slurm or source reports",
        "scientific_hold":"All seven humidity-blocked cases remain incomplete; obtain independent meteorological evidence for cold-season water vapor."},indent=2)+"\n")
    print("STAGE08D SUMMARY: 1924/1924 provenance records; report_only=True")
    print("REPORT DIR:",out)

if __name__=="__main__":
    main()

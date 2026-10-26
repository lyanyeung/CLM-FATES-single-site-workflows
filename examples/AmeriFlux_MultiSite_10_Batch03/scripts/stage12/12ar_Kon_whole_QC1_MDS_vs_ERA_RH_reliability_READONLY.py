#!/usr/bin/env python3
"""Stage12ar — Five complete US-Kon original VPD_F_QC1 time runs.

Stage12aq identified 31 original QC1/MDS neighbor samples in five unique
unbroken QC1 sequences. Stage12ar analyses ALL native half hours in these
five sequences, not only the 31 cherry-picked repair-adjacent samples.
Independent benchmark: strictly original TA_F_QC0 and VPD_F_QC0 pairs
against their same-time companion ERA TA_ERA and VPD_ERA within 14 days
of each run. Both the full local QC0 distribution and a comparable
ERA-temperature subsample are shown. No truth/causality claims.

--self-test: synthetic checks only; no external reads or writes
--check: SHA-signed original audit/source, full in-memory analysis; NO WRITES
--run: same plus new isolated SHA-signed report tables; NO MODEL WRITES
48 missing centers, 31 existing QC1 neighbors, seven failed events and two
special source T holds remain unapproved. No automatic replacements.
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION="batch03-stage12ar-v1-20261026-Kon-five-full-QC1-runs-original-MDS-ERA"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AQ=R/"reports/stage12aq_Kon_full_QC1_run_and_14day_QC0_ERA_RH_review_20261026T113539Z_dcadacde"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
AQ_ROWS="31_original_QC1_MDS_full_run_and_nearby_QC0_ERA_RH.csv"
AQ_SUMMARY="affected_episodes_QC0_native_ERA_RH_skill_summary.csv"
AQ_NOTE="SCIENCE_HOLD_NO_OPERATOR_APPROVAL_NO_MODEL_INPUT"
SPECIAL={"201102220900","201109291830"}
N_RUNS=5
N_NEIGHBORS=31
WINDOW=pd.Timedelta(days=14)

def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Signed immutable file absent or symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def number(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask(x<=-9990)

def rh(t,v):
    t=np.asarray(t,dtype=float)
    v=np.asarray(v,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        sat=6.112*np.exp(17.67*t/(t+243.5))
        z=100*(1-v/sat)
    return np.where((t>-85)&(t<55),z,np.nan)

def selftest():
    ix=pd.date_range("2011-10-17 23:00",periods=3,freq="30min")
    assert list(ix.strftime("%Y%m%d%H%M"))==[
        "201110172300","201110172330","201110180000"]
    assert np.isclose(float(rh(20,0)),100)
    assert np.isnan(float(rh(np.nan,3)))
    assert len(SPECIAL)==2 and N_RUNS==5 and N_NEIGHBORS==31
    print("STAGE12AR SELF-TEST PASS | complete QC1 runs + QC0 reference, no writes",flush=True)

def verify():
    receipt=json.loads(safe(AQ/"stage12aq_QC1_QC0_ERA_skill_SHA_receipt.json").read_text())
    if not (receipt.get("version")==
            "batch03-stage12aq-v1-20261026-Kon-QC1-run-nearby-QC0-ERA-RH-skill"
            and receipt.get("original_QC1_MDS_rows")==31
            and receipt.get("original_48_center_research_only") is True
            and receipt.get("seven_failed_events_unchanged") is True
            and receipt.get("special_two_temperature_holds_preserved") is True
            and receipt.get("operator_approved") is False
            and receipt.get("DATM_ready") is False
            and receipt.get("spinup_authorized") is False):
        raise ValueError("Upstream Stage12aq signed scientific gate changed")
    for name in (AQ_ROWS,AQ_SUMMARY,AQ_NOTE):
        if receipt.get("output_SHA256",{}).get(name)!=sha(AQ/name):
            raise ValueError("Upstream Stage12aq signed file changed: "+name)
    mf=json.loads(safe(S/"exact_input_manifest.json").read_text())
    site=next((x for x in mf["sites"] if x["site"]=="US-Kon"),None)
    if site is None:raise ValueError("Kon absent from signed original manifest")
    pin={str(Path(p).resolve()):v for p,v in mf["input_sha256"].items()}
    for kind in ("primary","era"):
        path=safe(site[kind])
        if sha(path)!=pin.get(str(path.resolve())):
            raise ValueError("Original "+kind+" source SHA mismatch")
    return site

def source(site):
    a=pd.read_csv(safe(site["primary"]),
       usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_MDS","VPD_F_QC"],
       dtype={"TIMESTAMP_START":str},low_memory=False)
    b=pd.read_csv(safe(site["era"]),
       usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
       dtype={"TIMESTAMP_START":str},low_memory=False)
    for f in (a,b):
        f["native_time"]=pd.to_datetime(
            f.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        if f.native_time.duplicated().any():
            raise ValueError("Native source timestamps duplicated")
        f.drop(columns="TIMESTAMP_START",inplace=True)
        f.set_index("native_time",inplace=True)
        for name in f.columns:f[name]=number(f[name])
    merged=a.join(b,how="left",validate="one_to_one").sort_index()
    if len(merged)!=len(a):raise ValueError("Native input row count changed")
    return merged

def stats(x):
    a=np.asarray(x,dtype=float)
    a=a[np.isfinite(a)]
    if not len(a):
        return {"n":0,"median":np.nan,"mae":np.nan,"p90_abs":np.nan}
    return {"n":len(a),"median":float(np.median(a)),
            "mae":float(np.mean(np.abs(a))),
            "p90_abs":float(np.quantile(np.abs(a),.9))}

def audit():
    site=verify()
    originals=pd.read_csv(safe(AQ/AQ_ROWS),dtype={
        "native_key":str,"full_native_QC1_run_start":str,
        "full_native_QC1_run_end":str},low_memory=False)
    if len(originals)!=N_NEIGHBORS or originals.native_key.duplicated().any() \
       or set(originals.native_key)&SPECIAL \
       or not originals.source_VPD_F_equals_MDS.astype(str).str.lower().eq("true").all():
        raise ValueError("31 signed QC1/MDS identities changed")
    original_runs=originals.groupby(
        ["full_native_QC1_run_start","full_native_QC1_run_end"],
        dropna=False,sort=True)
    if original_runs.ngroups!=N_RUNS:
        raise ValueError("Expected exactly five source-native QC1 spans")
    d=source(site)
    source_details=[]
    summaries=[]
    selected_checks=0
    for id_num,((key_start,key_end),members) in enumerate(original_runs,1):
        begin=pd.to_datetime(key_start,format="%Y%m%d%H%M")
        end=pd.to_datetime(key_end,format="%Y%m%d%H%M")
        if end<begin:raise ValueError("Reversed source time range")
        times=pd.date_range(begin,end,freq="30min")
        run=d.reindex(times)
        if len(run)!=int(members.full_native_QC1_run_halfhours.iloc[0]) \
           or run.isna().all(axis=1).any() or not run.VPD_F_QC.eq(1).all():
            raise ValueError("Full QC1 run no longer continuous/native/QC1")
        names=set(times.strftime("%Y%m%d%H%M"))
        if not set(members.native_key).issubset(names):
            raise ValueError("31 targeted source-neighbor rows not within their QC1 run")
        if set(members.native_key)&SPECIAL:raise ValueError("Protected hard T hold crossed")
        selected_checks+=len(members)
        ta=run.TA_F.to_numpy(dtype=float)
        va=run.VPD_F.to_numpy(dtype=float)
        md=run.VPD_F_MDS.to_numpy(dtype=float)
        tea=run.TA_ERA.to_numpy(dtype=float)
        vea=run.VPD_ERA.to_numpy(dtype=float)
        rr=rh(ta,va)
        er=rh(tea,vea)
        valid_t=np.isfinite(ta)&run.TA_F_QC.eq(0).to_numpy()
        phys=np.isfinite(rr)&np.isfinite(er)&(rr>=0)&(rr<=100)&(er>=0)&(er<=100)
        qmatch=np.isfinite(va)&np.isfinite(md)&np.isclose(va,md,atol=1e-6,rtol=0)
        paired=phys&valid_t
        delta=rr-er
        # Also retain physically impossible original RH, never silently discard it.
        raw_valid=np.isfinite(rr)&np.isfinite(er)
        for j,t in enumerate(times):
            source_details.append({
              "run_id":id_num,"native_key":t.strftime("%Y%m%d%H%M"),
              "is_among_31_stage12an_finite_neighbor_proposals":
                    t.strftime("%Y%m%d%H%M") in set(members.native_key),
              "original_VPD_F_QC":float(run.VPD_F_QC.iat[j]),
              "original_TA_F_QC":float(run.TA_F_QC.iat[j]),
              "original_tower_T_C":float(ta[j]),
              "original_MDS_VPD_hPa":float(va[j]),
              "original_source_VPD_F_MDS_hPa":float(md[j]),
              "original_VPD_F_matches_VPD_F_MDS":bool(qmatch[j]),
              "original_ERA_T_C":float(tea[j]),
              "original_ERA_VPD_hPa":float(vea[j]),
              "original_QC1_MDS_derived_RH_pct":float(rr[j]),
              "original_ERA_derived_RH_pct":float(er[j]),
              "original_MDS_minus_ERA_RH_pp":float(delta[j]),
              "source_QC0_tower_T":bool(valid_t[j]),
              "original_MDS_RH_physically_in_0_to_100":bool(np.isfinite(rr[j]) and 0<=rr[j]<=100),
              "operator_approved":False})
        # Benchmark actual observed paired QC0 humidity, not the nearby QC1 fill.
        context=d.loc[(d.index>=begin-WINDOW)&(d.index<=end+WINDOW)].copy()
        obs=rh(context.TA_F.to_numpy(),context.VPD_F.to_numpy())
        refer=rh(context.TA_ERA.to_numpy(),context.VPD_ERA.to_numpy())
        measured=(context.TA_F_QC.eq(0).to_numpy()&
                  context.VPD_F_QC.eq(0).to_numpy()&
                  np.isfinite(obs)&np.isfinite(refer)&
                  (obs>=0)&(obs<=100)&(refer>=0)&(refer<=100))
        rc=np.asarray(context.TA_ERA,dtype=float)
        run_era_t=tea[np.isfinite(tea)]
        # Predeclared comparable original ERA temperature range; still only
        # a regional/time-window skill diagnostic, never a truth label.
        if len(run_era_t):
            low=float(np.quantile(run_era_t,.1)-2)
            high=float(np.quantile(run_era_t,.9)+2)
            regime=(rc>=low)&(rc<=high)
        else:
            low=high=np.nan
            regime=np.zeros(len(context),dtype=bool)
        temperature_agreement=(
            np.abs(context.TA_F.to_numpy(dtype=float)-rc)<=5)
        refer_all=stats((obs-refer)[measured])
        refer_regime=stats((obs-refer)[measured&regime&temperature_agreement])
        selected_idx=times.strftime("%Y%m%d%H%M").isin(members.native_key)
        selected_pair=selected_idx & raw_valid
        full_pair_stats=stats(delta[raw_valid])
        selected_abs=np.abs(delta[selected_pair])
        # Ratio is descriptive only. 14d QC0 errors are temporally correlated
        # and cannot be interpreted as a p-value or an independent truth test.
        p90=refer_regime["p90_abs"]
        count_exceed=int(np.sum(selected_abs>p90)) if np.isfinite(p90) else -1
        summaries.append({
          "run_id":id_num,"source_run_begin":key_start,"source_run_end":key_end,
          "original_run_halfhours":len(run),"original_run_hours":len(run)/2,
          "stage12an_selected_finite_neighbor_records":len(members),
          "original_QC1_VPD_MDS_numerically_equal_N":int(qmatch.sum()),
          "original_QC1_VPD_MDS_numeric_coverage_pct":float(100*qmatch.mean()),
          "source_T_QC0_N":int(valid_t.sum()),
          "full_run_source_and_ERA_RH_both_finite_N":int(raw_valid.sum()),
          "full_run_RH_both_physical_N":int(phys.sum()),
          "full_run_T_QC0_and_RH_both_physical_N":int(paired.sum()),
          "full_run_original_RH_lt5_N":int(np.sum(np.isfinite(rr)&(rr<5))),
          "full_run_original_RH_lt10_N":int(np.sum(np.isfinite(rr)&(rr<10))),
          "full_run_original_RH_lt20_N":int(np.sum(np.isfinite(rr)&(rr<20))),
          "full_run_original_RH_lt0_N":int(np.sum(np.isfinite(rr)&(rr<0))),
          "full_run_original_RH_gt100_N":int(np.sum(np.isfinite(rr)&(rr>100))),
          "full_run_original_RH_median_pct":float(np.median(rr[np.isfinite(rr)])) if np.isfinite(rr).any() else np.nan,
          "full_run_ERA_RH_median_pct":float(np.median(er[np.isfinite(er)])) if np.isfinite(er).any() else np.nan,
          "full_run_original_minus_ERA_RH_median_pp":full_pair_stats["median"],
          "QC0_14day_both_measured_rh_and_era_N":refer_all["n"],
          "QC0_14day_both_measured_rh_ERA_MAE_pp":refer_all["mae"],
          "QC0_14day_regime_Tmin_ERA_C":low,
          "QC0_14day_regime_Tmax_ERA_C":high,
          "QC0_14day_regime_Twithin5C_original_tower_N":refer_regime["n"],
          "QC0_14day_regime_obs_minus_ERA_RH_median_pp":refer_regime["median"],
          "QC0_14day_regime_obs_minus_ERA_RH_MAE_pp":refer_regime["mae"],
          "QC0_14day_regime_obs_minus_ERA_RH_abs_P90_pp":p90,
          "selected_neighbors_abs_MDS_minus_ERA_RH_gt_local_QC0_P90_N":count_exceed,
          "local_reference_descriptive_not_independent_truth":True,
          "operator_approved":False})
    detail=pd.DataFrame(source_details)
    runs=pd.DataFrame(summaries)
    if not (len(runs)==5 and selected_checks==31 and
            int(runs.stage12an_selected_finite_neighbor_records.sum())==31 and
            detail.native_key.nunique()==len(detail)):
        raise ValueError("Expected exactly five disjoint continuous source runs and 31 selected neighbors")
    return detail,runs

def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    for option in ("self-test","check","run"):
        group.add_argument("--"+option,action="store_true")
    args=ap.parse_args()
    print("STAGE12AR WHOLE ORIGINAL QC1 RUN vs ERA-RH LOCAL QC0 SOURCE AUDIT | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    rows,runs=audit()
    print("\n====== FIVE COMPLETE ORIGINAL QC1 RUNS ======",flush=True)
    print(runs.round(5).to_string(index=False),flush=True)
    print("STAGE12AR QC1 FULL NATIVE HALF-HOURS",len(rows),
          "RUNS",len(runs),
          "ORIGINAL QC1/MDS NEIGHBOR PROPOSALS",31,
          "CENTERS STILL UNAPPROVED",48,
          "SEVEN EVENTS HELD, TWO HARD SOURCE-T HOLDS PROTECTED",flush=True)
    if args.check:
        print("STAGE12AR CHECK ONLY; ZERO REPORT, ORIGINAL, FORCING OR MODEL WRITES",flush=True)
        return
    folder=R/"reports"/("stage12ar_Kon_five_full_QC1_run_MDS_vs_ERA_science_review_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    output={
      "five_QC1_run_all_original_native_halhours_MDS_vs_ERA.csv":rows,
      "five_run_original_MDS_vs_ERA_RH_and_local_QC0_error_summary.csv":runs}
    for name,tab in output.items():tab.to_csv(folder/name,index=False)
    note="SCIENTIFIC_HOLD_NO_APPROVAL_NO_DATM"
    (folder/note).write_text(
        "Science-only original source QC1/MDS full-run diagnostic. "
        "Nearby measured original QC0 vs companion ERA error windows "
        "are contextual checks; overlapping observations are temporally "
        "dependent and cannot establish event-time truth or statistical p-values. "
        "No automatic replacement of 31 original QC1 neighbors or 48 held centers. "
        "Seven blocked episodes and two source-T exception timestamps remain held. "
        "Original tower/forcing/timestamps/Slurm/CIME/DATM/model inputs untouched.\n")
    hashes={f:sha(folder/f) for f in [*output,note]}
    (folder/"stage12ar_five_original_QC1_runs_SHA_receipt.json").write_text(
        json.dumps({
          "version":VERSION,
          "upstream_signed_stage12aq_SHA256":sha(
            AQ/"stage12aq_QC1_QC0_ERA_skill_SHA_receipt.json"),
          "full_native_QC1_runs":5,
          "full_source_QC1_halfhours":len(rows),
          "source_QC1_MDS_selected_neighbor_replacements_unapproved":31,
          "stage12an_centers_research_unapproved":48,
          "seven_events_still_held":True,
          "two_special_temperature_holds_protected":True,
          "operator_approval":False,"Postv5_approved":False,
          "DATM_ready":False,"spinup_authorized":False,
          "output_SHA256":hashes},indent=2)+"\n")
    print("STAGE12AR SOURCE-NATIVE SCIENCE REPORT DIR:",folder,flush=True)
    print("NO ORIGINAL SOURCE, CLOCK, PRIOR TRIAL, DATM OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AR STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage13h US-MOz source QC1 warm Jan-2005 run: discover FULL contiguous
anomalous interval at native 30 minutes (never assume 05:00 is true start),
compare original tower and paired FLUXNET ERA5 provenance, calculate *only
a preview* of joint ERA5 TA/VPD/QBOT correction.

CRITICAL: ERA5 companion is not necessarily independently produced.
Original tower and Stage07/Stage13g forcing candidates stay immutable.
--check prints source and bounded episode; NO WRITES.
--run writes only isolated signed CSV/report, not a new forcing, not DATM.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage13h-v1-20261026-source-QC1-warm-run-boundary-and-ERA-paired-preview"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13E=ROOT/"reports/stage13e_MOz_six_approved_09T_recheck_20261026T174412Z_3e98ca6c"
S13G=ROOT/"science_trials/stage13g_US_MOz_approved_native_T_VPD_20261026T180756Z_f75518a5"
SOURCE_CANDIDATE=S07/"US-MOz/forcing/processed_v5/US-MOz_CLM_forcing_2004_2021.csv"
SHADOW=S13G/"US-MOz_CLM_forcing_2004_2021_STG13G_RESEARCH_SHADOW.csv"
NEAR=pd.Timestamp("2005-01-06 09:00")
EXPECTED_START=pd.Timestamp("2005-01-06 05:00")
TOLERANCE=8.0
SEGMENT_LIMIT_HH=672
HALFHOUR=pd.Timedelta(minutes=30)
SITE="US-MOz"

def valid(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise RuntimeError("No source / symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with valid(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def sat(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def original_csv(p,fields):
    df=pd.read_csv(valid(p),usecols=["TIMESTAMP_START",*fields],
                   dtype={"TIMESTAMP_START":str},low_memory=False)
    ts=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    valid_times=ts.dt.year.between(2004,2021)&~((ts.dt.month==2)&(ts.dt.day==29))
    df=df.loc[valid_times].copy()
    df.index=pd.DatetimeIndex(ts.loc[valid_times],name="native_time")
    df.drop(columns=["TIMESTAMP_START"],inplace=True)
    if df.index.has_duplicates or df.index.hasnans or not df.index.is_monotonic_increasing:
        raise RuntimeError("Original native timestamps not unique/ordered")
    for col in fields:
        df[col]=pd.to_numeric(df[col],errors="coerce")
        df.loc[df[col]<=-9990,col]=np.nan
    return df

def candidate_csv(p):
    df=pd.read_csv(valid(p),dtype={"time":str},low_memory=False)
    d=pd.to_datetime(df.time,errors="raise")
    df.index=pd.DatetimeIndex(d,name="native_time")
    if len(df)!=315360 or df.index.has_duplicates or df.index.hasnans:
        raise RuntimeError("NOLEAP Stage13g selected forcing length/timestamps invalid")
    if df.index[0]!=pd.Timestamp("2004-01-01") or df.index[-1]!=pd.Timestamp("2021-12-31 23:30"):
        raise RuntimeError("Stage13g selected forcing exact range changed")
    needed=("TA_USE","VPD_USE","QBOT","TBOT","PSRF")
    if any(x not in df.columns for x in needed):
        raise RuntimeError("Missing required Stage13g model input")
    for col in needed:df[col]=pd.to_numeric(df[col],errors="coerce")
    if not bool(np.isfinite(df[list(needed)].to_numpy(float)).all()):
        raise RuntimeError("Existing selected forcing is nonfinite")
    return df

def selftest():
    d=pd.date_range("2005-01-06 05:00",periods=10,freq="30min")
    assert d[8]==NEAR and d[0]==EXPECTED_START
    t=-6.
    es=sat(t)
    assert 0<1.6<es and 0 < 100*(es-1.6)/es <100
    assert pd.Timedelta(minutes=30)==HALFHOUR
    print("STAGE13H SELF TEST PASS | native QC1 episode, paired ETA/VPD preview; NO WRITES",flush=True)

def preflight():
    prev=json.loads(valid(S13G/"stage13g_MOz_approved_T_VPD_science_shadow_SHA_receipt.json").read_text())
    if prev.get("approved_model_field_edit_rows")!=9 or \
       prev.get("source_review",{}).get("2005_Jan06_05_09_source_HOLD_unchanged") is not True or \
       prev.get("source_review",{}).get("spinup_authorized") is not False:
        raise RuntimeError("Stage13g science HOLD state/approval changed")
    if sha(SHADOW)!=prev["all_output_SHA256"].get(SHADOW.name):
        raise RuntimeError("Stage13g sealed research shadow changed")
    if sha(SOURCE_CANDIDATE)!=prev["source_review"].get("original_Stage07_selected_SHA256"):
        raise RuntimeError("Original Stage07 source candidate changed")
    e=json.loads(valid(S13E/"stage13e_moz_six_scope_and_09T_science_SHA_receipt.json").read_text())
    if sha(S13E/"2005Jan06_09T_original_Tower_ERA_stage07_surrounding_4h.csv") != \
       e["output_SHA256"]["2005Jan06_09T_original_Tower_ERA_stage07_surrounding_4h.csv"]:
        raise RuntimeError("Previously approved original Jan2005 source ±4h evidence changed")
    source=json.loads(valid(S07/"exact_input_manifest.json").read_text())
    spec=next(x for x in source["sites"] if x["site"]==SITE)
    expected={str(Path(p).resolve()):h for p,h in source["input_sha256"].items()}
    for k in ("primary","era"):
        p=valid(spec[k])
        if sha(p)!=expected.get(str(p.resolve())):
            raise RuntimeError("Raw primary/ERA companion source was modified "+k)
    return spec,prev

def discover_and_preview():
    spec,receipt=preflight()
    tower=original_csv(spec["primary"],("TA_F","TA_F_QC","VPD_F","VPD_F_QC"))
    era=original_csv(spec["era"],("TA_ERA","VPD_ERA"))
    selected=candidate_csv(SHADOW)
    if len(tower)!=315360 or not selected.index.equals(tower.index):
        raise RuntimeError("Original native tower and Stage13g candidate clocks inconsistent")
    if not era.index.equals(tower.index):
        raise RuntimeError("Standalone original ERA native timestamps inconsistent")
    data=tower.join(era,validate="one_to_one").join(
         selected[["time","TA_USE","VPD_USE","QBOT","TBOT","PSRF"]],validate="one_to_one")
    if not bool(np.isfinite(data.loc[NEAR,["TA_F","TA_ERA","TA_USE","VPD_F","VPD_ERA"]].to_numpy(float)).all()):
        raise RuntimeError("Target episode 09:00 lacks original TA/VPD references")
    # Only source-QC1 and real native >8C discrepancies; do not mistake QC2
    # copied ERA values for independently confirming their own validity.
    sus=(data.TA_F_QC.eq(1) & np.isfinite(data.TA_ERA) &
         (data.TA_F-data.TA_ERA).abs().gt(TOLERANCE))
    if not bool(sus.loc[NEAR]) or not bool(sus.loc[EXPECTED_START]):
        raise RuntimeError("Previously verified QC1 source episode no longer anomalous")
    ix=data.index.get_loc(NEAR)
    left,right=ix,ix
    vals=sus.to_numpy(bool)
    while left>0 and vals[left-1] and data.index[left]-data.index[left-1]==HALFHOUR:
        left-=1
        if ix-left>SEGMENT_LIMIT_HH:raise RuntimeError("Suspect episode >14d; extended research required")
    while right+1<len(vals) and vals[right+1] and data.index[right+1]-data.index[right]==HALFHOUR:
        right+=1
        if right-ix>SEGMENT_LIMIT_HH:raise RuntimeError("Suspect episode >14d; extended research required")
    start,end=data.index[left],data.index[right]
    if not(start<=EXPECTED_START<=NEAR<=end):
        raise RuntimeError("2005 full source QC1 high T episode discontinuous or missing")
    complete=data.iloc[left:right+1].copy()
    # All original paired references should be numeric for a real ERA+VPD
    # repair hypothesis; any missing data MUST remain a science HOLD.
    candidate_era_valid=(
       np.isfinite(complete[["TA_ERA","VPD_ERA","PSRF"]].to_numpy(float)).all(axis=1)
       & (complete.VPD_ERA.to_numpy(float)>0)
       & (complete.VPD_ERA.to_numpy(float)<sat(complete.TA_ERA.to_numpy(float))))
    if not candidate_era_valid.all():
        print("STAGE13H WARNING: paired ERA preview has",sum(~candidate_era_valid),
              "nonphysical/missing source slots; no mass replacement authorized",flush=True)
    es=sat(complete.TA_ERA.to_numpy(float))
    vapour=(es-complete.VPD_ERA.to_numpy(float))*100
    psrf=complete.PSRF.to_numpy(float)
    qbot=0.622*vapour/(psrf-0.378*vapour)
    preview=pd.DataFrame({
       "source_native_time":complete.index.astype(str),
       "source_tower_original_TA_C":complete.TA_F.to_numpy(float),
       "source_tower_TA_QC":complete.TA_F_QC.to_numpy(float),
       "source_tower_original_VPD_hPa":complete.VPD_F.to_numpy(float),
       "source_tower_VPD_QC":complete.VPD_F_QC.to_numpy(float),
       "paired_standalone_ERA_TA_C":complete.TA_ERA.to_numpy(float),
       "paired_standalone_ERA_VPD_hPa":complete.VPD_ERA.to_numpy(float),
       "Stage13g_current_selected_TA_C":complete.TA_USE.to_numpy(float),
       "Stage13g_current_selected_VPD_hPa":complete.VPD_USE.to_numpy(float),
       "Stage13g_current_QBOT_kgkg":complete.QBOT.to_numpy(float),
       "unapproved_ERA_pair_preview_TA_C":complete.TA_ERA.to_numpy(float),
       "unapproved_ERA_pair_preview_VPD_hPa":complete.VPD_ERA.to_numpy(float),
       "unapproved_preview_QBOT_kgkg":qbot,
       "unapproved_preview_RH_water_pct":100*vapour/(es*100),
       "preview_pass_water_RH_and_QBOT":candidate_era_valid & np.isfinite(qbot) & (qbot>0) & (qbot<0.08),
       "operator_approved":False
    })
    # ±2h boundaries and 24h day to expose transition to native QC2 source.
    around_start=max(0,left-4);around_end=min(len(data)-1,right+4)
    boundary=data.iloc[around_start:around_end+1].copy()
    boundary["source_native_time"]=boundary.index.astype(str)
    boundary["TA_tower_minus_ERA_C"]=boundary.TA_F-boundary.TA_ERA
    boundary["source_QC1_warm_run"]=sus.loc[boundary.index]
    day=data.loc["2005-01-06"].copy()
    day["source_native_time"]=day.index.astype(str)
    day["TA_tower_minus_ERA_C"]=day.TA_F-day.TA_ERA
    day["source_QC1_warm_run"]=sus.loc[day.index]
    status={
       "site":SITE,"source_start":str(start),"source_end":str(end),
       "source_duration_HH":len(complete),
       "duration_hours":len(complete)/2,
       "source_QC1_all":bool(complete.TA_F_QC.eq(1).all()),
       "original_tower_minus_ERA_TA_min_C":float((complete.TA_F-complete.TA_ERA).min()),
       "original_tower_minus_ERA_TA_max_C":float((complete.TA_F-complete.TA_ERA).max()),
       "paired_ERA_T_VPD_physical_preview_pass_count":int(preview.preview_pass_water_RH_and_QBOT.sum()),
       "paired_ERA_T_VPD_physical_preview_fail_count":int((~preview.preview_pass_water_RH_and_QBOT).sum()),
       "source_original_files_verified_and_unchanged":True,
       "stage13g_candidate_SHA_verified_and_unchanged":True,
       "new_ERA_T_VPD_preview_applied_to_any_forcing":False,
       "source_ERA_not_proven_independent":True,
       "operator_approval_required":True,
       "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False
    }
    return preview,boundary,day,status

def show(preview,boundary,day,status):
    print("=== FULL SOURCE-QC1 WARM EPISODE DISCOVERED ===",flush=True)
    for key,value in status.items():print(key,value,flush=True)
    print("\n=== FULL 2005-01-06 ORIGINAL tower / companion ERA5 half-hour context ===",flush=True)
    subset=day[["source_native_time","TA_F","TA_F_QC","TA_ERA",
        "VPD_F","VPD_F_QC","VPD_ERA","TA_USE","VPD_USE","TA_tower_minus_ERA_C","source_QC1_warm_run"]]
    print(subset.to_string(index=False,float_format=lambda z:f"{z:.3f}"),flush=True)
    print("\n=== AUTO-DISCOVERED EPISODE BOUNDARY HEAD/TAIL (4 native halfhours) ===",flush=True)
    selection=pd.concat([boundary.head(8),boundary.tail(8)]).drop_duplicates()
    print(selection[["source_native_time","TA_F","TA_F_QC","TA_ERA",
        "VPD_F","VPD_F_QC","VPD_ERA","TA_tower_minus_ERA_C","source_QC1_warm_run"]].to_string(
         index=False,float_format=lambda z:f"{z:.3f}"),flush=True)
    print("\n=== ERA PAIRED SOURCE T/VPD/QBOT SCIENCE PREVIEW (first/last 6 records, full CSV if --run) ===",flush=True)
    if len(preview)>12:show=pd.concat([preview.head(6),preview.tail(6)])
    else:show=preview
    print(show[["source_native_time","source_tower_original_TA_C",
        "paired_standalone_ERA_TA_C","source_tower_original_VPD_hPa",
        "paired_standalone_ERA_VPD_hPa","unapproved_preview_QBOT_kgkg",
        "unapproved_preview_RH_water_pct","preview_pass_water_RH_and_QBOT"]].to_string(
            index=False,float_format=lambda z:f"{z:.4f}"),flush=True)
    print("ALL PREVIEW VALUES UNAPPROVED. Stage13g original remains unchanged.",flush=True)

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):mode.add_argument("--"+x,action="store_true")
    a=p.parse_args()
    print("STAGE13H US-MOz 2005 QC1 MULTI-HOUR SOURCE EPISODE | "+VERSION,flush=True)
    selftest()
    if a.self_test:return
    preview,boundary,day,status=discover_and_preview()
    show(preview,boundary,day,status)
    if a.check:
        print("STAGE13H CHECK ONLY | ZERO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13h_MOz_Jan2005_full_source_run_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    names={
      "jan2005_full_QC1_warm_episode_ERA_paired_science_preview_NOT_APPLIED.csv":preview,
      "jan2005_full_QC1_warm_episode_original_transition_boundaries.csv":boundary.reset_index(drop=True),
      "2005Jan06_all_48_original_HH_with_ERA_QC_and_stage13g.csv":day.reset_index(drop=True)}
    for n,d in names.items():d.to_csv(out/n,index=False)
    note="SCIENCE_HOLD_2005_QC1_WARM_RUN_NOT_ERA_APPROVED"
    (out/note).write_text(
       "The operator did not approve any 2005 Jan 6 source correction. "
       "The full original QC1 discrepant episode was discovered rather than "
       "pre-assuming 05:00 start. Paired ERA temperature/VPD replacements "
       "are an independent SCIENCE PREVIEW ONLY; no existing original "
       "or selected Stage13g forcing/case/PFT/time/Slurm was changed.\n")
    receipt={
      "version":VERSION,
      "stage13g_signed_receipt_SHA256":sha(S13G/
          "stage13g_MOz_approved_T_VPD_science_shadow_SHA_receipt.json"),
      "stage13g_source_model_candidate_SHA256":sha(SHADOW),
      "original_stage07_source_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
      "science":status,
      "output_SHA256":{n:sha(out/n) for n in [*names,note]}
    }
    (out/"stage13h_MOz_2005_QC1_episode_source_SHA_receipt.json").write_text(
          json.dumps(receipt,indent=2)+"\n")
    print("STAGE13H READONLY SOURCE SCIENCE REPORT",out,flush=True)
    print("NO MODIFIED RAW, ERA, STAGE07/STAGE13G FORCING, ZBOT, PFT, CIME, SLURM",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13H STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

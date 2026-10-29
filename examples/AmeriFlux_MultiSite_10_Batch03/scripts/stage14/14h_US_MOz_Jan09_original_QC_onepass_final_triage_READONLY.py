#!/usr/bin/env python3
"""US-MOz Batch03 one-pass final Jan09 original QC classification, READ ONLY.

Actual 14G QC1->QC1 19:30 bridge is retained: no reinterpolation.
Use pinned SHA receipts and the exact original FLUXMET/companion ERA source.
Review Jan03-10 (384 native HH) as ONE family, count QC0/QC1/QC2,
physical original and selected pairs, contiguous QC1 and source-vs-ERA
temperature sign reversals, all 30min original-quality transition edges.
No automatic numeric repairs, no ERA download, case/DATM/AD400 or Slurm.
--run writes a NEW report directory only; --check no files.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VERSION="batch03-MOz-Jan09-final-onepass-QC-science-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
G=R/"science_trials/US_MOz_14G_QC1_LEFT_EDGE_ONE_HH_SENSITIVITY_20261029T042521Z_dcda1a16"
GCSV="US-MOz_315360_27ERA_plus1QC1bridge_and40approved_RESEARCH.csv"
GREC="US_MOz_QC1_bridge_SHA_receipt.json"
START=pd.Timestamp("2005-01-03 00:00:00")
STOP=pd.Timestamp("2005-01-11 00:00:00")
STEP=pd.Timedelta(minutes=30)
FIELD=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
def need(x,msg):
    if not bool(x):raise RuntimeError("MOz 14H STOP WITHOUT SOURCE EDIT: "+str(msg))
def safe(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"missing pinned source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def es(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def eice(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))
def selftest():
    need(len(pd.date_range(START,STOP-STEP,freq="30min"))==384,
         "eight native Jan03-10 days must be 384 HH")
    need(es(-20)>eice(-20) and pd.Series(["a",None]).equals(pd.Series(["a",None])),
         "water/ice or mixed text time source regression")
    print("US-MOz JAN09 QC ONEPASS SELF-TEST PASS",flush=True)
def inputs():
    grect=json.loads(safe(G/GREC).read_text())
    need(grect.get("version")=="US-MOz-QC1-1HH-operator-interpolate-T-e-v1-20261029"
         and grect.get("science_approved") is False
         and grect.get("source_Stage14F") and grect.get("source_Stage13L"),
         "actual 14G bridge or ancestor source receipt changed")
    for fn,h in grect["output_SHA256"].items():
        need(sha(G/fn)==h,"14G signed output hash mismatch "+fn)
    mg=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    sites=[s for s in mg["sites"] if s["site"]=="US-MOz"]
    need(len(sites)==1 and int(sites[0]["native_minutes"])==30
         and int(sites[0]["first_year"])==2004
         and int(sites[0]["last_year"])==2021,
         "original US-MOz metadata/release source drift")
    ss=sites[0]
    for col in ("primary","era"):
        f=safe(ss[col])
        need(mg["input_sha256"].get(str(f.resolve()))==sha(f),
             "original "+col+" SHA changed")
    return ss,grect
def source_window(path,fields):
    f=pd.read_csv(safe(path),usecols=["TIMESTAMP_START",*fields],
                  dtype={"TIMESTAMP_START":str},low_memory=False)
    need(f.TIMESTAMP_START.is_unique and
         f.TIMESTAMP_START.str.fullmatch(r"\d{12}").all(),
         "native original time not exact/unique")
    times=pd.to_datetime(f.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    f=f.loc[(times>=START)&(times<STOP)].copy()
    f.index=pd.DatetimeIndex(times.loc[f.index])
    f.drop(columns=["TIMESTAMP_START"],inplace=True)
    need(len(f)==384 and f.index.is_unique and f.index.is_monotonic_increasing,
         "original Jan03-10 window truncated")
    for k in fields:
        f[k]=pd.to_numeric(f[k],errors="coerce")
        f.loc[f[k]<=-9990,k]=np.nan
    return f
def contiguous_runs(x,condition,label):
    mask=np.asarray(condition,dtype=bool)
    idx=np.flatnonzero(mask)
    out=[]
    if not len(idx):return out
    groups=[];a=b=int(idx[0])
    for k in idx[1:]:
        k=int(k)
        if k!=b+1 or x.index[k]-x.index[b]!=STEP:
            groups.append((a,b));a=k
        b=k
    groups.append((a,b))
    for a,b in groups:
        segment=x.iloc[a:b+1]
        if segment.index[-1]<pd.Timestamp("2005-01-09") or segment.index[0]>=pd.Timestamp("2005-01-11"):
            continue
        diff=segment.T_minus_ERA.to_numpy(float)
        finite=diff[np.isfinite(diff)]
        out.append(dict(source_run_class=label,
            original_start=str(x.index[a]),original_end=str(x.index[b]),
            native_halfhours=b-a+1,
            tower_QC0_pair_count=int((segment.TA_F_QC.eq(0)&segment.VPD_F_QC.eq(0)).sum()),
            tower_TQC1_count=int(segment.TA_F_QC.eq(1).sum()),
            tower_VPDQC1_count=int(segment.VPD_F_QC.eq(1).sum()),
            TminusERA_min_C=float(finite.min()) if len(finite) else np.nan,
            TminusERA_max_C=float(finite.max()) if len(finite) else np.nan,
            source_science_repair_approved=False))
    return out
def assess():
    ss,rec=inputs()
    raw=source_window(ss["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=source_window(ss["era"],["TA_ERA","VPD_ERA"])
    selected=pd.read_csv(safe(G/GCSV),dtype={"time":str},low_memory=False)
    need(len(selected)==315360 and list(selected)==FIELD,
         "14G selected source full 315360-row 10-field schema drift")
    ti=pd.to_datetime(selected.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    need(ti.is_unique and ti.is_monotonic_increasing and
         not bool(((ti.dt.month==2)&(ti.dt.day==29)).any()),
         "14G selected original NOLEAP native time invalid")
    selected.index=pd.DatetimeIndex(ti)
    s=selected.loc[(selected.index>=START)&(selected.index<STOP),FIELD].copy()
    need(len(s)==384 and s.index.equals(raw.index) and s.index.equals(era.index),
         "US-MOz source and completed trial original timestamps differ")
    d=raw.join(era,validate="one_to_one").join(s.drop(columns="time"),validate="one_to_one")
    d["T_minus_ERA"]=d.TA_F-d.TA_ERA
    d["source_water_RH_pct"]=100*(1-d.VPD_F/es(d.TA_F))
    d["ERA_water_RH_pct"]=100*(1-d.VPD_ERA/es(d.TA_ERA))
    d["selected_water_RH_pct"]=100*(1-d.VPD_USE/es(d.TA_USE))
    d["selected_ice_RH_pct"]=100*(es(d.TA_USE)-d.VPD_USE)/eice(d.TA_USE)
    d["pair_is_original_measured_QC0"]=d.TA_F_QC.eq(0)&d.VPD_F_QC.eq(0)
    d["pair_is_original_QC1"]=d.TA_F_QC.eq(1)&d.VPD_F_QC.eq(1)
    d["source_type"]=d.TA_F_QC.fillna(-1).astype(int).astype(str)+"/"+d.VPD_F_QC.fillna(-1).astype(int).astype(str)
    d["source_water_negative"]=d.source_water_RH_pct<0
    d["selected_T_diff_from_original"]=~np.isclose(d.TA_USE,d.TA_F,rtol=0,atol=1e-8)
    d["selected_VPD_diff_from_original"]=~np.isclose(d.VPD_USE,d.VPD_F,rtol=0,atol=1e-8)
    d["selected_e_hPa"]=es(d.TA_USE)-d.VPD_USE
    d["selected_Q_expected"]=.622*100*d.selected_e_hPa/(d.PSRF-.378*100*d.selected_e_hPa)
    d["selected_water_physics"]=(
        np.isfinite(d.selected_Q_expected)&(d.selected_e_hPa>0)&
        (d.VPD_USE>=0)&(d.VPD_USE<es(d.TA_USE))&
        np.isclose(d.QBOT,d.selected_Q_expected,atol=1e-8,rtol=1e-6))
    d["dT_selected_30m"]=d.TA_USE.diff()
    d["dVPD_selected_30m"]=d.VPD_USE.diff()
    d["source_T_QC_before"]=d.TA_F_QC.shift()
    d["source_VPD_QC_before"]=d.VPD_F_QC.shift()
    d["T_QC_transition"]=d.source_T_QC_before.astype("Int64").astype(str)+"->"+d.TA_F_QC.astype("Int64").astype(str)
    d["VPD_QC_transition"]=d.source_VPD_QC_before.astype("Int64").astype(str)+"->"+d.VPD_F_QC.astype("Int64").astype(str)
    d["original_T_ERA_GT5"]=d.T_minus_ERA.abs()>5
    d["original_T_ERA_GT8"]=d.T_minus_ERA.abs()>8
    d["extreme_negative_original_T_ERA"]=d.T_minus_ERA< -5
    d["extreme_positive_original_T_ERA"]=d.T_minus_ERA>5
    d["classification"]=np.select([
       d.pair_is_original_measured_QC0,
       d.pair_is_original_QC1 & d.extreme_negative_original_T_ERA,
       d.pair_is_original_QC1 & d.extreme_positive_original_T_ERA,
       d.pair_is_original_QC1,
       d.TA_F_QC.eq(2)|d.VPD_F_QC.eq(2)],
       ["MEASURED_QC0_KEEP",
        "QC1_NEGATIVE_ERA_DISCREPANCY_REVIEW",
        "QC1_POSITIVE_ERA_DISCREPANCY_REVIEW",
        "QC1_WITHIN_5C_NOT_INDEPENDENT",
        "QC2_ERA_DEPENDENT_NOT_MEASURED"],
       default="MIXED_SOURCE_QC_REVIEW")
    need(d.selected_water_physics.all(),"latest research source has physical errors on Jan03-10")
    jan9=d.loc["2005-01-09"].copy()
    need(len(jan9)==48,"Jan09 exactly 48 HH expected")
    run=[]
    run+=contiguous_runs(d,d.TA_F_QC.eq(1),"SOURCE_T_QC1_CONTIGUOUS")
    run+=contiguous_runs(d,d.pair_is_original_QC1,"SOURCE_T_AND_VPD_QC1_CONTIGUOUS")
    run+=contiguous_runs(d,d.TA_F_QC.eq(1)&d.extreme_negative_original_T_ERA,
                          "QC1_T_MINUS_ERA_LESS_THAN_MINUS5C")
    run+=contiguous_runs(d,d.TA_F_QC.eq(1)&d.extreme_positive_original_T_ERA,
                          "QC1_T_MINUS_ERA_MORE_THAN_PLUS5C")
    runs=pd.DataFrame(run)
    view=d.loc["2005-01-08":"2005-01-10"].copy()
    view=view.reset_index(names="native_time")
    selected_cols=["native_time","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
      "TA_ERA","VPD_ERA","TA_USE","VPD_USE","QBOT","PSRF",
      "T_minus_ERA","source_water_RH_pct","ERA_water_RH_pct",
      "selected_water_RH_pct","source_type",
      "selected_T_diff_from_original","selected_VPD_diff_from_original",
      "dT_selected_30m","dVPD_selected_30m",
      "T_QC_transition","VPD_QC_transition","classification"]
    view=view[selected_cols]
    change=d.loc["2005-01-08":"2005-01-10"].copy()
    cond=(change.TA_F_QC.ne(change.source_T_QC_before)|
          change.VPD_F_QC.ne(change.source_VPD_QC_before)|
          (change.dT_selected_30m.abs()>4)|
          (change.dVPD_selected_30m.abs()>4))
    edges=change.loc[cond].reset_index(names="native_time")[selected_cols]
    summary={
      "version":VERSION,"site":"US-MOz",
      "actual_previous_stage14g_source":str(G/GCSV),
      "prior_14G_receipt_SHA256":sha(G/GREC),
      "source_original_tower_SHA256":sha(ss["primary"]),
      "source_original_ERA_SHA256":sha(ss["era"]),
      "Jan03_10_8day_native_halfhours":len(d),
      "Jan09_native_halfhours":len(jan9),
      "Jan09_source_T_QC0":int(jan9.TA_F_QC.eq(0).sum()),
      "Jan09_source_T_QC1":int(jan9.TA_F_QC.eq(1).sum()),
      "Jan09_source_T_QC2":int(jan9.TA_F_QC.eq(2).sum()),
      "Jan09_source_VPD_QC0":int(jan9.VPD_F_QC.eq(0).sum()),
      "Jan09_source_T_VPD_measured_both_QC0":int(jan9.pair_is_original_measured_QC0.sum()),
      "Jan09_T_minus_ERA_C_min":float(jan9.T_minus_ERA.min()),
      "Jan09_T_minus_ERA_C_max":float(jan9.T_minus_ERA.max()),
      "Jan09_T_QC1_minus_ERA_less_than_minus5C":int((jan9.TA_F_QC.eq(1)&jan9.extreme_negative_original_T_ERA).sum()),
      "Jan09_T_QC1_minus_ERA_more_than_plus5C":int((jan9.TA_F_QC.eq(1)&jan9.extreme_positive_original_T_ERA).sum()),
      "Jan09_original_implied_negative_water_RH":int(jan9.source_water_negative.sum()),
      "Jan09_selected_physics_failures":int((~jan9.selected_water_physics).sum()),
      "Jan08_10_selected_step_T_gt4C":int((change.dT_selected_30m.abs()>4).sum()),
      "Jan08_10_selected_step_VPD_gt4hPa":int((change.dVPD_selected_30m.abs()>4).sum()),
      "Jan09_QC_not_independent_observation":True,
      "Jan09_new_repair_approvals":0,
      "all_originals_and_14G_trial_unchanged":True,
      "model_PFT_ZBOT_DATM_AD400_not_audited":True
    }
    print("\nUS-MOz JAN09 48-HH SOURCE ORIGINAL QC CLASSIFICATION:")
    print(jan9[["TA_F_QC","VPD_F_QC","T_minus_ERA","TA_USE",
       "VPD_USE","dT_selected_30m","dVPD_selected_30m","classification"]].to_string(),flush=True)
    print("\nUS-MOz QC1 SOURCE REGIME RUNS INTERSECTING JAN09:")
    print(runs.to_string(index=False) if len(runs) else "NONE",flush=True)
    print("\nUS-MOz NATIVE QC0/QC1/QC2 TRANSITIONS AND >4C/hPa BOUNDARY FLAGS Jan08-10:")
    print(edges.to_string(index=False) if len(edges) else "NONE",flush=True)
    print("\nUS-MOz JAN09 ONEPASS SOURCE SUMMARY:")
    print(json.dumps(summary,indent=2),flush=True)
    print("US-MOz JAN09 FINAL QC CLASSIFICATION COMPLETE | NO ORIGINAL FORCING, CASE, DATM, SLURM WRITES",flush=True)
    return summary,runs,view,edges
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    summary,runs,detail,edges=assess()
    if args.check:
        print("US-MOz JAN09 READONLY CHECK SUCCESS | NO WRITES",flush=True)
        return
    out=R/"reports"/("US_MOz_14H_Jan09_full_source_QC_onepass_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    docs={
      "US_MOz_Jan09_original_source_QC_contiguous_runs.csv":runs,
      "US_MOz_Jan08_10_original_source_QC_ERA_selected_native.csv":detail,
      "US_MOz_Jan08_10_QC_transition_boundary_flags.csv":edges}
    hashes={}
    for name,df in docs.items():
        df.to_csv(out/name,index=False,float_format="%.17g")
        hashes[name]=sha(out/name)
    (out/"US_MOz_Jan09_final_QC_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    hashes["US_MOz_Jan09_final_QC_summary.json"]=sha(out/"US_MOz_Jan09_final_QC_summary.json")
    (out/"NO_NEW_MET_REPAIRS_APPROVED").write_text(
       "Native Jan09 original source QC labels and sign-reversed T/ERA biases are assessed. "
       "This is a final consolidated QC gate, not a new observational temperature or VPD. "
       "Existing Stage14G and approved Stage13L data remain unchanged. "
       "No Post-v5, DATM, AD400 or Slurm approval.\n")
    hashes["NO_NEW_MET_REPAIRS_APPROVED"]=sha(out/"NO_NEW_MET_REPAIRS_APPROVED")
    (out/"US_MOz_14H_READONLY_SHA_receipt.json").write_text(json.dumps(
       {"version":VERSION,"inputs":summary["actual_previous_stage14g_source"],
        "outputs_SHA256":hashes,"no_source_modified":True,
        "DATM":False,"AD400":False,"Slurm":False},indent=2)+"\n")
    print("US-MOz JAN09 SOURCE QC REPORT:",out,flush=True)
    print("US-MOz JAN09 14H ONEPASS COMPLETE | NO FORCING CHANGES",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("US-MOz JAN09 QC ONEPASS FAIL CLOSED:",exc,file=sys.stderr,flush=True)
        raise

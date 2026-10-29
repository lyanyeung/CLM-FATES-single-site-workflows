#!/usr/bin/env python3
"""Stage13AQ US-Me6: empirical original QC0 30-minute e/QBOT edge analogues.

Sign-check successful Stage13AP original source science report and full
Stage13AI 45-missing shadow. Compare left/right original 19-HH preview
mixed with unchanged original QC2 boundaries vs hypothetical ERA-RH and
QC0-calibrated border VPD. Search the actual 2010-2025 original tower
TA_F_QC=0 and VPD_F_QC=0 half-hour PAIRS, not individual timestamps,
for winter matched temperatures, warming/cooling and ERA T anomalies.
Compute measured actual water vapour e change and QBOT change distributions.
No interpolated QC2 substitute is treated as observed. Zero matched QC0
pairs is a strict evidence shortage, never a statistical endorsement.
Only signed scientific reports in reports/: no original DATM/shadow writes.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13aq-v1-20261029-Me6-30min-QC0-pair-vapour-e-QBOT-edges"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AP_CODE=HERE/"13ap_Me6_2015_original_QC2_ERA_RH_border_donor_skill_READONLY.py"
AP_GIT="0c03987a8ef9324826beb809cafab438b9dbf7c6"
AP_DIR=ROOT/"reports/stage13ap_Me6_19HH_two_QC2_border_ERA_RH_QC0_READONLY_20261029T000329Z_12da9d39"
AP_REC="stage13ap_source_science_READONLY_SHA_receipt.json"
AP_SUM="stage13ap_border_ERA_RH_science_summary.json"
AP_GROUP="two_border_original_vs_ERA_RH_vs_QC0_border_vapour_QBOT.csv"
AP_EXPECT={
 "27HH_original_QC2_ERA_VPD_vs_RH_at_tower_T_NO_REPAIR.csv",
 "two_border_native_QC0_joint_T_ERA_donor_skill_NO_APPROVAL.csv",
 AP_GROUP,
 "each_border_original_measured_QC0_donor_rows.csv",
 AP_SUM,
 "NO_ORIGINAL_QC2_BORDER_HUMIDITY_REPAIR_OR_19HH_MODEL_APPROVAL"}
AP_VER="batch03-stage13ap-v1-20261028-Me6-QC2-boundary-ERA-RH-mapped-QC0-donor"
AI_SHA="b193388d4f82b47a7727c6ef9b2fdc25b37a56e4867d319224d1fc9327326f40"
START=pd.Timestamp("2014-12-31 23:30")
END=pd.Timestamp("2015-01-01 08:30")
LEFT=START-pd.Timedelta(minutes=30)
RIGHT=END+pd.Timedelta(minutes=30)
EVENT=pd.date_range(START,END,freq="30min")
STEP=pd.Timedelta(minutes=30)
def need(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AQ ORIGINAL SCIENCE HOLD: "+str(msg))
def must(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for c in iter(lambda:f.read(1<<20),b""):h.update(c)
    return h.hexdigest()
def gitblob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def moisture(t,v,p):
    t=np.asarray(t,float);v=np.asarray(v,float);p=np.asarray(p,float)
    e=es(t)-v
    with np.errstate(invalid="ignore",divide="ignore"):
        q=.622*(100*e)/(p-.378*100*e)
        rh=100*e/es(t)
    valid=(np.isfinite([t,v,p,e,q]).all(axis=0)&
           (v>0)&(v<es(t))&(q>0)&(q<.08)&
           (p>50000)&(p<110000))
    return e,q,rh,valid
def test():
    need(len(EVENT)==19 and LEFT==pd.Timestamp("2014-12-31 23:00") and
         RIGHT==pd.Timestamp("2015-01-01 09:00"),"original 19HH native clock")
    e,q,rh,ok=moisture([-17.], [.4],[95000])
    need(bool(ok[0]) and .7<e[0]<1.4 and 50<rh[0]<100 and 0<q[0]<.01,
         "water physical and QBOT unit self-test")
    ids=pd.date_range("2020-01-01", periods=3,freq="30min")
    need(len(ids[1:])==2 and ((ids[1:]-ids[:-1])==STEP).all(),
         "pair halfhour clock selftest")
    print("STAGE13AQ SELF-TEST PASS | original 19HH edge QC0 30min measured PAIRS and water vapour/QBOT; NO WRITES",flush=True)
def audit():
    need(gitblob(AP_CODE)==AP_GIT,
         "Stage13AP actual original source Git blob drift")
    receipt=json.loads(must(AP_DIR/AP_REC).read_text())
    need(receipt.get("site")=="US-Me6" and receipt.get("version")==AP_VER and
         receipt.get("new_science_approval") is False and
         receipt.get("original_source_or_forcing_written") is False and
         set(receipt.get("outputs_SHA256",{}))==AP_EXPECT,
         "actual Stage13AP successful report signed science inventory changed")
    for name,h in receipt["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and
             sha(AP_DIR/name)==h,
             "Stage13AP original QC0 source report changed: "+name)
    science=json.loads(must(AP_DIR/AP_SUM).read_text())
    need(science.get("original_current_research_shadow_missing_VPD_QBOT_HH")==45
         and science.get("immediate_edges_source_VPD_QC2") is True
         and science.get("original_19HH_event_candidate_science_approved") is False
         and science.get("source_or_forcing_or_shadow_written") is False
         and science.get("original_Stage13AI_shadow_SHA256")==AI_SHA,
         "Stage13AP prior 19HH original source science HOLD changed")
    groups=pd.read_csv(must(AP_DIR/AP_GROUP))
    need(len(groups)==6 and groups.do_not_replace_original_QC2_border_or_19HH.eq(True).all(),
         "actual source two-border three-hypothesis comparisons differ")
    spec=importlib.util.spec_from_file_location("stage13ap_for_stage13aq",must(AP_CODE))
    need(spec is not None and spec.loader is not None,"Stage13AP original source cannot load")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER==AP_VER,"Stage13AP original source method changed")
    al,raw,site,_,_=mod.verify()
    need(raw.index.equals(site.index) and len(raw)==280320
         and raw.index.min().year==2010 and raw.index.max().year==2025
         and site.VPD_USE.isna().sum()==45 and site.QBOT.isna().sum()==45
         and site.loc[EVENT,"VPD_USE"].isna().all()
         and raw.loc[LEFT:RIGHT,"VPD_F_QC"].eq(2).all(),
         "original full native source or 45 missing science HOLD changed")
    return raw,site,groups,science
def run():
    raw,site,groups,science=audit()
    idx=raw.index
    t=raw.TA_F.to_numpy(float)
    tq=raw.TA_F_QC.to_numpy(float)
    v=raw.VPD_F.to_numpy(float)
    vq=raw.VPD_F_QC.to_numpy(float)
    et=raw.TA_ERA.to_numpy(float)
    site_t=site.TA_USE.to_numpy(float)
    site_v=site.VPD_USE.to_numpy(float)
    pressure=site.PSRF.to_numpy(float)
    e,q,rh,ok=moisture(t,v,pressure)
    valid=(ok&(tq==0)&(vq==0)&
           np.isclose(t,site_t,rtol=0,atol=1e-7)&
           np.isclose(v,site_v,rtol=0,atol=1e-7)&
           np.isfinite(et)&idx.month.isin((12,1,2))&
           ~((idx>=pd.Timestamp("2014-12-30"))&
             (idx<pd.Timestamp("2015-01-03"))))
    # Half-hour index adjacency verified, never leap or missing intervals.
    leftidx=np.arange(len(idx)-1)
    rightidx=leftidx+1
    adjacent=(idx[1:]-idx[:-1])==STEP
    pair=adjacent&valid[:-1]&valid[1:]
    # Measured original source QC0 only at both endpoints.
    rows=[]; donor_rows=[]; comparisons=[]
    contexts={
      "LEFT":(LEFT,START),
      "RIGHT":(END,RIGHT)}
    for side,(t0,t1) in contexts.items():
        orig0=raw.loc[t0];orig1=raw.loc[t1]
        target_before=float(site.at[t0,"TA_USE"])
        target_after=float(site.at[t1,"TA_USE"])
        deltaT=target_after-target_before
        mismatch_before=float(orig0.TA_F-orig0.TA_ERA)
        mismatch_after=float(orig1.TA_F-orig1.TA_ERA)
        need((side=="LEFT" and abs(deltaT+9.757)<1e-8) or
             (side=="RIGHT" and abs(deltaT-2.76)<1e-8),
             "actual original source temperature switch changed")
        for label,tol,dttol,eratol in (
            ("STRICT_T3_DELTA1_ERA3",3.,1.,3.),
            ("MODERATE_T3_DELTA2_ERA3",3.,2.,3.),
            ("BROAD_T5_DELTA3_ERA5",5.,3.,5.),
            ("TEMP_ONLY_T5_DELTA3",5.,3.,None)):
            mask=(pair&
                  (abs(t[leftidx]-target_before)<=tol)&
                  (abs(t[rightidx]-target_after)<=tol)&
                  (abs((t[rightidx]-t[leftidx])-deltaT)<=dttol))
            if eratol is not None:
                mask=(mask&
                      (abs((t[leftidx]-et[leftidx])-mismatch_before)<=eratol)&
                      (abs((t[rightidx]-et[rightidx])-mismatch_after)<=eratol))
            a=leftidx[mask];b=rightidx[mask]
            de=e[b]-e[a];dq=q[b]-q[a]
            day_count=int(idx[b].normalize().nunique()) if len(b) else 0
            year_count=int(np.unique(idx[b].year).size) if len(b) else 0
            # >=30 native pairs, >=5 days, >=3 source years: EXPLORATORY
            # observational support screen, not a scientific acceptance.
            supported=(len(b)>=30 and day_count>=5 and year_count>=3)
            metric={"side":side,"match_label":label,
              "native_original_measured_QC0_paired_HH":int(len(b)),
              "source_QC0_native_dates":day_count,
              "source_QC0_distinct_years":year_count,
              "target_edge_original_T_before_C":target_before,
              "target_edge_original_T_after_C":target_after,
              "target_native_temperature_change_C":deltaT,
              "target_tower_minus_ERA_T_before_C":mismatch_before,
              "target_tower_minus_ERA_T_after_C":mismatch_after,
              "observed_QC0_actual_e_delta_median_hPa":
                float(np.median(de)) if len(de) else None,
              "observed_QC0_actual_e_delta_p05_hPa":
                float(np.percentile(de,5)) if len(de) else None,
              "observed_QC0_actual_e_delta_p95_hPa":
                float(np.percentile(de,95)) if len(de) else None,
              "observed_QC0_QBOT_delta_median_kgkg":
                float(np.median(dq)) if len(dq) else None,
              "observed_QC0_QBOT_delta_p05_kgkg":
                float(np.percentile(dq,5)) if len(dq) else None,
              "observed_QC0_QBOT_delta_p95_kgkg":
                float(np.percentile(dq,95)) if len(dq) else None,
              "independent_original_QC0_pair_support_screen":bool(supported),
              "scientific_method_or_model_approved":False}
            rows.append(metric)
            for j,k in zip(a,b):
                donor_rows.append({
                  "side":side,"match_label":label,
                  "native_before":str(idx[j]),"native_after":str(idx[k]),
                  "original_before_T_QC":0,"original_after_T_QC":0,
                  "original_before_VPD_QC":0,"original_after_VPD_QC":0,
                  "original_before_tower_T_C":float(t[j]),
                  "original_after_tower_T_C":float(t[k]),
                  "original_before_tower_minus_ERA_T_C":float(t[j]-et[j]),
                  "original_after_tower_minus_ERA_T_C":float(t[k]-et[k]),
                  "original_measured_actual_e_change_hPa":float(e[k]-e[j]),
                  "original_measured_QBOT_change_kgkg":float(q[k]-q[j]),
                  "original_source_or_forcing_unchanged":True})
            tested=groups.loc[groups.edge.eq(side)]
            need(len(tested)==3 and tested.border_hypothesis.nunique()==3,
                 "three actual signed Stage13AP source border scenarios missing")
            for _,option in tested.iterrows():
                proposed=float(option["30min_actual_water_vapour_e_signed_change_hPa"])
                proposed_q=float(option["30min_QBOT_signed_change_kgkg"])
                comparisons.append({
                  "side":side,"match_label":label,
                  "border_hypothesis":str(option.border_hypothesis),
                  "QC0_pairs":int(len(de)),"QC0_days":day_count,"QC0_years":year_count,
                  "QC0_pair_support_screen":bool(supported),
                  "border_hypothesis_e_delta_hPa":proposed,
                  "border_hypothesis_QBOT_delta_kgkg":proposed_q,
                  "measured_QC0_e_delta_5th_95th_range_contains_hypothesis":
                     bool(np.percentile(de,5)<=proposed<=np.percentile(de,95))
                     if supported else None,
                  "measured_QC0_QBOT_delta_5th_95th_range_contains_hypothesis":
                     bool(np.percentile(dq,5)<=proposed_q<=np.percentile(dq,95))
                     if supported else None,
                  "empirical_percentile_of_candidate_e_delta":
                     float(100*np.mean(de<=proposed)) if supported else None,
                  "no_QC2_source_or_model_change":True})
    populations=pd.DataFrame(rows)
    sample=pd.DataFrame(donor_rows)
    ranked=pd.DataFrame(comparisons)
    need(len(populations)==8 and len(ranked)==24
         and ranked.no_QC2_source_or_model_change.all() and
         populations.scientific_method_or_model_approved.eq(False).all(),
         "two source edge QC0 source-population conditional screens changed")
    info={
      "version":VER,"site":"US-Me6",
      "2010_2025_original_native_16_years":True,
      "signed_parent_Stage13AP_receipt_SHA256":sha(AP_DIR/AP_REC),
      "original_source_19_HH_QC2_HOLD":19,
      "original_Stage13AI_site_VPD_QBOT_missing_HH":45,
      "original_two_adjacent_VPD_QC2_untouched":True,
      "original_measured_QC0_pairs_both_T_and_VPD_QC0":True,
      "actual_QC0_conditional_analogue_populations":rows,
      "sample_QC0_matches_do_not_prove_event_truth":True,
      "no_source_or_forcing_or_research_shadow_written":True,
      "scientific_method_or_candidate_approved":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AQ ACTUAL ORIGINAL TOWER QC0 NATIVE 30MIN PAIRED EDGE SUPPORT",flush=True)
    print(populations.to_string(index=False),flush=True)
    print("STAGE13AQ ORIGINAL MEASURED QC0 PAIR EMPIRICAL e/QBOT HYPOTHESIS RANGE",flush=True)
    print(ranked.to_string(index=False),flush=True)
    print("STAGE13AQ STRICT 19HH SCIENCE HOLD SOURCE SUMMARY",json.dumps(info,indent=2),flush=True)
    return populations,sample,ranked,info
def main():
    p=argparse.ArgumentParser()
    opts=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","run"):opts.add_argument("--"+k,action="store_true")
    a=p.parse_args()
    test()
    if a.self_test:return
    populations,details,comparisons,summary=run()
    if a.check:
        print("STAGE13AQ ORIGINAL SOURCE MEASURED QC0 30MIN EDGE PAIR AUDIT READONLY CHECK PASS; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13aq_Me6_QC0_30min_vapour_pairs_original_READONLY_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
      "8_actual_source_QC0_paired_regime_support.csv":populations,
      "original_source_QC0_halfhour_pair_provenance.csv":details,
      "24_comparisons_actual_source_QC0_pairs_vs_three_QC2_border_hypotheses.csv":comparisons}
    for name,df in docs.items():df.to_csv(out/name,index=False,float_format="%.17g")
    summaryfn="stage13aq_source_measured_QC0_30min_edge_science_summary.json"
    marker="NO_19HH_OR_QC2_BOUNDARY_FORCING_SCIENCE_APPROVAL"
    (out/summaryfn).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text("Read-only original source measured QC0 T+VPD pairs; not"
        " contemporaneous event measurements; no forcing/shadow/DATM/Slurm.\n")
    receipt={"version":VER,"site":"US-Me6","scientific_method_approved":False,
      "source_or_shadow_or_forcing_written":False,
      "outputs_SHA256":{nm:sha(out/nm) for nm in [*docs,summaryfn,marker]}}
    (out/"stage13aq_READONLY_science_SHA_receipt.json").write_text(
      json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AQ READONLY SCIENCE REPORT DIR:",out,flush=True)
    print("STAGE13AQ 19HH TWO QC2 BORDERS ORIGINAL QC0 MEASURED PAIR REVIEW COMPLETE; NO SOURCE/SHADOW/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AQ SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

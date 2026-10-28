#!/usr/bin/env python3
"""US-Me6 Stage13AI: one physically impossible VPD in a sole missing native HH.

Only 2015-11-11 09:00 original QC1 VPD=7.121 hPa at measured TA=2.05C:
e_s,w(TA)=7.0835 hPa, VPD>e_s implies negative vapour pressure in
the retained site forcing. Stage13AH independently reports two stable
original VPD QC1 anchors, 5.393 and 6.069 hPa, giving 5.731 hPa.
Produce a separate 280320-row research shadow ONLY after exact signed
Stage13AH and parent Stage13AF full-schema and physics gates. Neither
QC1 source nor earlier approved trials is overwritten.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ai-v1-20261028-Me6-one-physically-invalid-QC1-native-0900"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AH=ROOT/"reports/stage13ah_US-Me6_46_native_humidity_missing_tower_ERA_context_READONLY_20261028T193402Z_6f75ea9d"
AH_RECEIPT="stage13ah_readonly_sha_receipt.json"
AH_SUM="stage13ah_exact_46_source_science_summary.json"
AH_DATA="ALL_46_original_tower_ERA_current_VPD_QBOT_no_approval.csv"
AH_NEIGHBORS="ALL_46_original_before_after_2h_each_ERA_and_tower.csv"
AH_GROUPS="46_missing_source_run_and_science_method_review_counts.csv"
AH_CLUSTERS="46_missing_contiguous_original_native_clusters.csv"
AH_EXPECT={AH_DATA,AH_NEIGHBORS,AH_GROUPS,AH_CLUSTERS,AH_SUM,
 "NO_NEW_OPERATOR_APPROVAL_NO_SOURCE_OR_FORCING_MODEL_WRITES"}
AH_VER="batch03-stage13ah-v3-20261028-Me6-independent-tower-ERA-calendar-coverage"
AF=ROOT/"science_trials/stage13af_Me6_20151112_1330_originalQC1_single_spike_RESEARCH_ONLY_20261028T172815Z_c5ca5d8d"
AF_CSV="US-Me6_STAGE13AF_20151112_1330_Run14_oneQC1_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AF_RECEIPT="stage13af_one_QC1_science_shadow_SHA_receipt.json"
AF_SHA="3df2fd258157f2a70d8d0b6dd0de865980bf6505c4da0e6a58e6058e2610b1b0"
AD_SHA="8ea065e690b35cdbf2722c436211ab43627dfdcb2e202f159be9d22a7396241b"
S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
TARGET=pd.Timestamp("2015-11-11 09:00:00")
HH=pd.Timedelta(minutes=30)
FIVE=pd.date_range(TARGET-2*HH,periods=5,freq="30min")
SOURCE_V=7.121
SOURCE_T=2.05
PREV=5.393
NEXT=6.069
INTERPOLATED=(PREV+NEXT)/2
PROTECTED=set(pd.date_range("2015-09-26 05:00",periods=4,freq="30min")) | \
 set(pd.date_range("2017-07-04 06:00",periods=5,freq="30min")) | \
 {pd.Timestamp("2017-07-04 12:00"),pd.Timestamp("2015-11-12 13:30")}
def need(x,msg):
    if not bool(x):raise RuntimeError("STAGE13AI EXACT SCIENCE HOLD: "+str(msg))
def must(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"file missing/symlink: "+str(p));return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def es(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(t+243.5)) if np.isfinite(t) else np.nan
def specific(v,t,p):
    v,t,p=float(v),float(t),float(p)
    sat=es(t);e=(sat-v)*100
    den=p-.378*e
    q=.622*e/den if np.isfinite(den) and den!=0 else np.nan
    ok=bool(np.isfinite([v,t,p,sat,e,den,q]).all() and
            50000<p<110000 and 0<v<sat and 0<q<0.08 and den>0)
    return q,ok
def idx(series):
    v=series.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
    x=pd.DatetimeIndex(pd.to_datetime(v,format="%Y%m%d%H%M",errors="raise"))
    need(len(x)==280320 and x.is_unique and x.is_monotonic_increasing and
         not ((x.month==2)&(x.day==29)).any(),
         "original 16-year research NOLEAP clock changed")
    return x
def selftest():
    need(len(PROTECTED)==11 and len(FIVE)==5 and FIVE[2]==TARGET
         and np.isclose(INTERPOLATED,5.731,atol=1e-10,rtol=0)
         and SOURCE_V>es(SOURCE_T) and not specific(SOURCE_V,SOURCE_T,95000)[1]
         and specific(INTERPOLATED,SOURCE_T,95000)[1]
         and TARGET not in PROTECTED,
         "exact physically invalid QC1 source, one single native linear center")
    print("STAGE13AI SELF-TEST PASS | original QC1 VPD above site water saturation, two QC1 native flanks, protected 11 HH; NO WRITES",flush=True)
def source_audit():
    ar=json.loads(must(AH/AH_RECEIPT).read_text())
    need(ar.get("version")==AH_VER and ar.get("site")=="US-Me6"
         and ar.get("new_method_approved") is False
         and ar.get("source_or_forcing_written") is False
         and set(ar.get("outputs_SHA256",{}))==AH_EXPECT,
         "signed 46 source-science report inventory or policy mismatch")
    for name,digest in ar["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AH/name)==digest,
             "source-science SHA changed "+name)
    summary=json.loads(must(AH/AH_SUM).read_text())
    need(summary.get("site")=="US-Me6"
         and summary.get("last_census_stage13af_vpd_missing_HH")==46
         and summary.get("within_five_held_original_QC1_runs_missing_HH")==17
         and summary.get("outside_five_held_original_QC1_runs_missing_HH")==29
         and summary.get("missing_clusters")==20
         and summary.get("latest_AF_research_shadow_SHA256")==AF_SHA
         and summary.get("original_unmodified_stage13s_SHA256")==S_SHA
         and summary.get("isolated_linear_only_research_review_count")==1
         and summary.get("no_automatic_user_science_approval") is True
         and summary.get("original_files_modified") is False,
         "actual original Stage13AH 46/20 original-source science report mismatch")
    need(summary.get("original_source_time_coverage",{}).get("tower",{}).get("missing_native_rows_in_original_source")==0
         and summary.get("original_source_time_coverage",{}).get("era",{}).get("missing_native_rows_in_original_source")==0,
         "exact source-native ERA and tower clock coverage changed")
    events=pd.read_csv(must(AH/AH_DATA),dtype={"native_time":str},low_memory=False)
    context=pd.read_csv(must(AH/AH_NEIGHBORS),
                        dtype={"missing_center":str,"neighbor_native_time":str},low_memory=False)
    groups=pd.read_csv(must(AH/AH_CLUSTERS),low_memory=False)
    need(len(events)==46 and events.native_time.is_unique
         and len(context)==46*9 and len(groups)==20
         and (events.science_review_category=="REVIEW_ISOLATED_LINEAR_ONLY_NO_APPROVAL").sum()==1,
         "original 46 center/414 context/20 cluster row coverage or single-center gate changed")
    z=events.loc[events.native_time==str(TARGET)]
    need(len(z)==1,"exact native 2015 QC1 center not in missing science report")
    a=z.iloc[0]
    need(str(a.run_scope)=="14" and
         float(a.source_tower_VPD_F_QC)==1 and float(a.source_tower_TA_F_QC)==0
         and np.isclose(float(a.source_tower_VPD_F_hPa),SOURCE_V,atol=1e-8,rtol=0)
         and np.isclose(float(a.source_tower_TA_F_C),SOURCE_T,atol=1e-8,rtol=0)
         and np.isclose(float(a.before_30min_tower_VPD_hPa),PREV,atol=1e-8,rtol=0)
         and np.isclose(float(a.after_30min_tower_VPD_hPa),NEXT,atol=1e-8,rtol=0)
         and np.isclose(float(a.hypothetical_isolated_linear_VPD_hPa),INTERPOLATED,atol=1e-8,rtol=0)
         and a.science_review_category=="REVIEW_ISOLATED_LINEAR_ONLY_NO_APPROVAL"
         and bool(a.original_tower_T_all_five_measured_QC0_and_stable)
         and bool(a.original_VPD_neighbor_qc0_or_qc1_not_always_measured_QC0)
         and bool(a.hypothetical_single_center_linear_gate_PASS)
         and not bool(a.operator_new_approval),
         "signed original QC1 / five measured tower T and flanking original values mismatch")
    five=context.loc[context.missing_center==str(TARGET)].sort_values("relative_30min_steps")
    need(len(five)==9 and five.relative_30min_steps.tolist()==list(range(-4,5))
         and five.original_tower_time_exists.all()
         and five.original_companion_ERA_time_exists.all(),
         "exact original ±2h tower/ERA source flanks absent")
    five=five.loc[five.relative_30min_steps.isin([-2,-1,0,1,2])]
    need(len(five)==5 and
         pd.DatetimeIndex(pd.to_datetime(five.neighbor_native_time)).equals(FIVE)
         and np.all(five.tower_TA_F_QC.to_numpy(float)==0)
         and np.isin(five.tower_VPD_F_QC.to_numpy(float),[0,1]).all()
         and five.tower_VPD_F_QC.iloc[2]==1
         and np.isclose(five.tower_VPD_F_hPa.iloc[1],PREV,atol=1e-8,rtol=0)
         and np.isclose(five.tower_VPD_F_hPa.iloc[2],SOURCE_V,atol=1e-8,rtol=0)
         and np.isclose(five.tower_VPD_F_hPa.iloc[3],NEXT,atol=1e-8,rtol=0),
         "5-node native original tower source and temperature/QC changed")
    vals=five.tower_VPD_F_hPa.to_numpy(float)
    temps=five.tower_TA_F_C.to_numpy(float)
    need(np.max(abs(np.diff(temps)))<=3.5 and
         abs(vals[1]-vals[0])<=2 and abs(vals[4]-vals[3])<=2
         and abs(vals[3]-vals[1])<=2 and
         np.max(abs(np.diff([vals[0],vals[1],INTERPOLATED,vals[3],vals[4]])))<=4,
         "5-node physically stable source flanks lost")
    afr=json.loads(must(AF/AF_RECEIPT).read_text())
    need(afr.get("site")=="US-Me6" and
         afr.get("separate_research_only_shadow") is True and
         afr.get("source_or_production_forcing_written") is False and
         afr.get("original_Stage13AD_SHA256")==AD_SHA
         and afr.get("outputs_SHA256",{}).get(AF_CSV)==AF_SHA
         and sha(AF/AF_CSV)==AF_SHA,
         "parent exact source Stage13AF SHA/content lineage mismatch")
    before=pd.read_csv(must(AF/AF_CSV),dtype={"time":str},low_memory=False)
    before.index=idx(before.time)
    need(all(x in before.columns for x in ("VPD_USE","QBOT","TA_USE","PSRF"))
         and set(FIVE).issubset(before.index),
         "approved complete original NOLEAP source clock/schema differs")
    need(np.isnan(float(before.at[TARGET,"VPD_USE"]))
         and np.isnan(float(before.at[TARGET,"QBOT"])),
         "the exact original 2015 target is no longer an unfilled site record")
    need(np.isfinite(before.TA_USE.to_numpy(float)).all()
         and np.isfinite(before.PSRF.to_numpy(float)).all()
         and np.isclose(float(before.at[TARGET,"TA_USE"]),SOURCE_T,atol=1e-7,rtol=0),
         "source original measured tower T and site pressure are not preserved")
    for j in (0,1,3,4):
        ti=FIVE[j]
        need(np.isclose(before.at[ti,"VPD_USE"],vals[j],atol=1e-7,rtol=0)
             and np.isclose(before.at[ti,"TA_USE"],temps[j],atol=1e-7,rtol=0)
             and specific(vals[j],temps[j],before.at[ti,"PSRF"])[1],
             "native prior site vs original tower five flanks or water physics mismatch")
    pp=float(before.at[TARGET,"PSRF"])
    new_q,ok=specific(INTERPOLATED,SOURCE_T,pp)
    need(ok and 0<new_q<.08 and SOURCE_V>es(SOURCE_T)
         and not specific(SOURCE_V,SOURCE_T,pp)[1],
         "center original source must have invalid water vapour and new interpolated center valid")
    out=before.copy(deep=True)
    out.at[TARGET,"VPD_USE"]=INTERPOLATED
    out.at[TARGET,"QBOT"]=new_q
    for col in before.columns:
        if col=="time":
            need(before[col].equals(out[col]),"site original native time changed")
            continue
        old=before[col].to_numpy(float);now=out[col].to_numpy(float)
        changed=set(before.index[~np.isclose(old,now,rtol=0,atol=1e-12,equal_nan=True)])
        if col in ("VPD_USE","QBOT"):
            need(changed=={TARGET},"only exact original 2015 QC1 target VPD/QBOT may change: "+col)
        else:need(not changed,"original or other site forcing field changed: "+col)
    for timestamp in PROTECTED:
        need(before.loc[timestamp].equals(out.loc[timestamp]),
             "previously user approved source time changed "+str(timestamp))
    old_missing=~np.isfinite(before.VPD_USE.to_numpy(float))
    new_missing=~np.isfinite(out.VPD_USE.to_numpy(float))
    need(old_missing.sum()==46 and new_missing.sum()==45 and
         np.array_equal(new_missing,~np.isfinite(out.QBOT.to_numpy(float))),
         "parent 46 missing must become exactly 45, no other missing change")
    details={
       "version":VER,"site":"US-Me6","run":14,"native_time":str(TARGET),
       "original_source_QC_VPD":1,"original_tower_TA_F_QC":0,
       "original_VPD_hPa":SOURCE_V,"tower_TA_F_C":SOURCE_T,
       "site_e_sat_water_hPa":es(SOURCE_T),
       "original_source_VPD_excess_above_site_water_sat_hPa":SOURCE_V-es(SOURCE_T),
       "preceding_native_tower_VPD_hPa":PREV,
       "following_native_tower_VPD_hPa":NEXT,
       "two_bookend_VPD_QC_both_directly_measured_QC0":False,
       "new_research_VPD_hPa":INTERPOLATED,
       "new_rederived_QBOT_kgkg":new_q,
       "original_Stage13AH_receipt_SHA256":sha(AH/AH_RECEIPT),
       "parent_Stage13AF_SHA256":AF_SHA,
       "original_Stage13S_SHA256":S_SHA,
       "prior_2015_2017_operator_approved_original_11_HH_unchanged":True,
       "original_full_site_missing_VPD_QBOT_HH_before":46,
       "separate_research_shadow_missing_after":45,
       "unchanged_all_other_held_runs":True,
       "source_ERA_tower_and_time_unchanged":True,
       "forcings_production_written":False,
       "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    return before,out,details
def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","apply"):modes.add_argument("--"+mode,action="store_true")
    args=parser.parse_args()
    selftest()
    if args.self_test:return
    before,after,details=source_audit()
    print("STAGE13AI EXACT PHYSICALLY INVALID ORIGINAL QC1 ONE-HH REVIEW",
          json.dumps(details,indent=2),flush=True)
    if args.check:
        print("STAGE13AI EXACT 46->45 MISSING READONLY SCIENCE CHECK PASS | NO WRITES",flush=True)
        return
    dest=ROOT/"science_trials"/("stage13ai_Me6_20151111_0900_VPD_GT_ESphysically_invalid_QC1_SINGLE_RESEARCH_ONLY_"+
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    guard=dest/"INCOMPLETE_NO_DATM_OR_MODEL_USE"
    guard.write_text("Never treat this trial as a production forcing.\n")
    outname="US-Me6_STAGE13AI_Run14_20151111_0900_physically_invalid_QC1_SINGLE_ONLY_NOLEAP.csv"
    after.to_csv(dest/outname,index=False,float_format="%.17g")
    reread=pd.read_csv(must(dest/outname),dtype={"time":str},low_memory=False)
    need(list(reread.columns)==list(before.columns)
         and reread.time.tolist()==before.time.tolist()
         and len(reread)==len(before),
         "output source full 16year 280320 NOLEAP schema/time mismatch")
    for col in before.columns:
        if col=="time":continue
        need(np.allclose(reread[col].to_numpy(float),after[col].to_numpy(float),
                         rtol=1e-14,atol=1e-12,equal_nan=True),
             "output exact physics numeric roundtrip differs "+col)
    need(sha(AF/AF_CSV)==AF_SHA,
         "previous successful Stage13AF SHA source altered during science output")
    infoname="stage13ai_one_invalid_VPD_QC1_science_scope.json"
    note="RESEARCH_ONLY_ONE_PHYSICALLY_INVALID_QC1_HH_NEIGHBOR_QC1_NOT_OBSERVED_QC0"
    (dest/infoname).write_text(json.dumps(details,indent=2)+"\n")
    (dest/note).write_text("One exact physically impossible native VPD at original"
          " measured site T; original/source metadata preserved, interpolation"
          " constrained by original QC1 neighbors and original five measured"
          " tower T. Not a large-amplitude isolated-spike criterion."
          " Not a full Run14, Run15–18, whole site or model release."
          " 45 native missing HH remain. No DATM/AD400/Slurm.\n")
    receipt={"version":VER,"site":"US-Me6","parent_Stage13AF_SHA256":AF_SHA,
          "separate_research_shadow":True,"production_forcing_or_source_written":False,
          "output_SHA256":{name:sha(dest/name) for name in (outname,infoname,note)}}
    (dest/"stage13ai_one_invalid_source_HH_SHA_receipt.json").write_text(
       json.dumps(receipt,indent=2)+"\n")
    guard.unlink()
    print("STAGE13AI NEW SINGLE ONLY RESEARCH SHADOW:",dest,flush=True)
    print("STAGE13AI EXACT PHYSICS-INVALID SINGLE QC1 RESEARCH SHADOW COMPLETE; 45 HOLD REMAIN; NO DATM/AD400/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AI SOURCE SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

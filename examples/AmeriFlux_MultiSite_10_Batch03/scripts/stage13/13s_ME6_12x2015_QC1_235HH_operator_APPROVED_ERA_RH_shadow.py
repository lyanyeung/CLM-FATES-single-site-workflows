#!/usr/bin/env python3
"""Stage13s US-Me6 — operator-approved 12 original 2015 source QC1 full runs.

Source scope is EXACT Stage13r full-run IDs 1..11 + 13 = 235 native 30min
QC1 times; 17 old method-approved centers + 218 newly operator-authorized
QC1 neighbours. Paired original ERA RH at immutable original Stage12ac
site TA_USE/PSRF -> recompute VPD_USE/QBOT only at those exact times.

All 12 runs require original tower/ERA/Stage12ac/Stage13q/Stage13r signed
SHA; measured QC0 both ends; original QC1 VPD and measured QC0 TA
everywhere, ERA RH and site RH/QBOT physics, all 30min steps <=4hPa.
On any failure HOLD entire group and produce NO new forcing. Previously
approved 5 Jul2017 Stage12ac values and the 6 held full source runs are
fully excluded; NO Slurm, DATM, AD400, model or original source writes.

--self-test no file reads/writes; --check only reads; --apply verifies
again and writes new signed separate research-only complete NOLEAP CSV.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage13s-v1-20261027-Me6-12-full-2015-QC1-runs-235HH"
HERE=Path(__file__).resolve().parent
R_SCRIPT=HERE/"13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
R_SCRIPT_BLOB="5a8dc69f5fb65015a9b7c9096153935684f466a8"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
Q=ROOT/"reports/stage13q_Me6_33_original_ERA_RH_group_source_review_20261027T002737Z_445444f6"
RR=ROOT/"reports/stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_20261027T004033Z_5eefea7b"
AC=ROOT/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
AC_FILE="US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv"
RR_RECEIPT="stage13r_source_original_QC1_SHA_receipt.json"
RR_GROUPS="US-Me6_source_original_full_QC1_runs_grouped_OPERATOR_APPROVAL_NEEDED.csv"
RR_DETAIL="US-Me6_each_QC1_fullrun_ERA_RH_T_QBOT_source_native_preview_READONLY.csv"
APPROVAL_SCHEMA="batch03-stage13s-operator-approved-Me6-12-full-original-QC1-2015-runs-v1"
PROPOSAL_BLOB="84b8f8a2d228ba2816e7632030fa6e5e0793feeb"
IDS=(1,2,3,4,5,6,7,8,9,10,11,13)
EXCLUDED_IDS=(12,14,15,16,17,18)
EXPECTED_NUM=235
PREV_REVIEWED=17
NEW_NEIGHBORS=218
SOURCE_NATIVE_STEP=pd.Timedelta(minutes=30)
MAX_JUMP=4.0
MODEL_OUT="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
STAGE12AC_FIVE={pd.Timestamp("2017-07-04 06:00")+SOURCE_NATIVE_STEP*i for i in range(5)}

def must(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Stage13s signed original source missing/symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as fh:
        for x in iter(lambda:fh.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()

def need(ok,msg):
    if not bool(ok):
        raise RuntimeError("STAGE13S WHOLE-RUN SCIENCE HOLD: "+str(msg))

def ts(s):
    return pd.Timestamp(str(s))

def datekey(s):
    return pd.to_datetime(s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12),
                          format="%Y%m%d%H%M",errors="raise")

def near(a,b,atol=1e-8):
    return bool(np.isfinite([float(a),float(b)]).all() and
                np.isclose(float(a),float(b),rtol=0,atol=atol))

def selftest():
    need(len(IDS)==12 and len(EXCLUDED_IDS)==6 and not set(IDS)&set(EXCLUDED_IDS),
         "approved and held source original runs overlap")
    need(EXPECTED_NUM==PREV_REVIEWED+NEW_NEIGHBORS,
         "17 previous +218 extra source times are not 235")
    need(len(STAGE12AC_FIVE)==5 and all(t.year==2017 for t in STAGE12AC_FIVE),
         "existing July2017 Stage12ac source must be preserved")
    es=6.112*np.exp(17.67*5/(5+243.5))
    r=100*(1-2/es)
    target=es*(1-r/100)
    q=.622*(es-target)*100/(95000-.378*(es-target)*100)
    need(near(target,2) and 0<r<100 and 0<q<.08,"ERA RH / water saturation science maths")
    native=pd.date_range("2015-01-01 01:30",periods=9,freq="30min")
    need(len(native)==9 and all(native[i+1]-native[i]==SOURCE_NATIVE_STEP for i in range(8)),
         "source native cadence is not 30min")
    print("STAGE13S SELF-TEST PASS | twelve exact 2015 source runs, 235 native QC1 HH, 2017 five protected, NO WRITES",flush=True)

def load_original_stage13r():
    p=must(R_SCRIPT)
    blob=subprocess.run(["git","hash-object",str(p)],capture_output=True,
                        text=True,check=True).stdout.strip()
    need(blob==R_SCRIPT_BLOB,"historical Stage13r original science module Git blob changed")
    spec=importlib.util.spec_from_file_location("stage13r_pinned_for_stage13s",p)
    need(spec is not None and spec.loader is not None,
         "original Stage13r module cannot be imported")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    need(mod.VER=="batch03-stage13r-v1-20261027-Me6-original-full-QC1-run-survey",
         "Stage13r historical source method changed")
    need(mod.ROOT==ROOT and mod.RR if hasattr(mod,"RR") else mod.ROOT==ROOT,
         "source site original experiment root changed")
    return mod

def approval(path):
    d=json.loads(must(path).read_text())
    need(d.get("schema")==APPROVAL_SCHEMA and d.get("site")=="US-Me6" and
         d.get("status","").startswith("OPERATOR_APPROVED_EXACT_TWELVE"),
         "exact signed Stage13s operator approval not active")
    need(d.get("source_stage13s_proposal_original_git_blob")==PROPOSAL_BLOB and
         d.get("source_stage13r_actual_readonly_report")==str(RR) and
         d.get("source_stage13q_actual_readonly_report")==str(Q),
         "operator SHA/proposal/site original source paths changed")
    need(d.get("postv5_approved") is False and
         d.get("DATM_ready") is False and
         d.get("Slurm_jobs_authorized") is False and
         d.get("spinup_authorized") is False,
         "user has not approved model/Postv5/Slurm")
    scope=d.get("approved_scope_aggregate",{})
    need(scope.get("original_VPD_F_QC1_HH")==235 and
         scope.get("previously_method_approved_centers")==17 and
         scope.get("new_original_QC1_neighbours_authorized")==218 and
         scope.get("source_QC0_bookends_that_must_remain")==24 and
         scope.get("affected_year")==2015,
         "operator exact 235 source-native / 24 measured QC0 boundary scope altered")
    items=d.get("approved_source_native_QC1_full_runs",[])
    need(len(items)==12 and
         tuple(int(x.get("original_stage13r_full_run_id")) for x in items)==IDS,
         "signed operator exact 12 original source group IDs missing")
    need(sum(int(x["original_native_30min_records"]) for x in items)==EXPECTED_NUM and
         sum(int(x["old_method_approved_center_count"]) for x in items)==PREV_REVIEWED and
         sum(int(x["new_QC1_neighbour_scope_authorized"]) for x in items)==NEW_NEIGHBORS,
         "signed operator source group counts altered")
    excluded=d.get("excluded_six_source_full_runs",[])
    need(len(excluded)==6 and
         tuple(int(x.get("run_id")) for x in excluded)==EXCLUDED_IDS and
         sum(int(x["new_neighbour_QC1_unapproved"]) for x in excluded)==761,
         "six original source HOLD runs were not protected")
    need(set(d.get("original_preserved_2017_07_04_Stage12ac_five",[]))==
         {t.strftime("%Y%m%d%H%M") for t in STAGE12AC_FIVE},
         "approved original five Stage12ac source records not protected")
    return d

def verified_science(module):
    # Stage13r verified() chains original tower and ERA SHA from Stage07,
    # original Stage12ac approved input+receipt, original Stage13q 33 source
    # and 31 HOLD report receipts.
    src,centers,_,qrec=module.verified()
    receipt=json.loads(must(RR/RR_RECEIPT).read_text())
    need(receipt.get("version")==VERSION.replace("stage13s-v1-20261027-Me6-12-full-2015-QC1-runs-235HH",
         "stage13r-v1-20261027-Me6-original-full-QC1-run-survey") and
         receipt.get("site")=="US-Me6" and
         receipt.get("original_33_source_centers")==33 and
         receipt.get("source_full_original_QC1_runs")==18 and
         receipt.get("new_operator_authority_granted") is False and
         receipt.get("model_forcing_written") is False,
         "existing Stage13r signed original QC1 full run receipt not correct")
    need(receipt.get("source_original_Stage13q_actual_report_SHA256")==
         sha(Q/"stage13q_readonly_original_source_SHA_receipt.json") and
         receipt.get("source_original_Stage12ac_approved_forcing_SHA256")==sha(AC/AC_FILE) and
         receipt.get("source_original_paired_FLUXMET_tower_SHA256")==sha(src["primary"]) and
         receipt.get("source_original_companion_ERA_SHA256")==sha(src["era"]),
         "Stage13r signed original source SHA mismatched current")
    outputs=receipt.get("outputs_SHA256",{})
    expected={RR_GROUPS,RR_DETAIL,"stage13r_summary_all_33_original_hold_centers.json",
              "READONLY_OPERATOR_NEW_SCOPE_APPROVAL_REQUIRED"}
    need(set(outputs)==expected,
         "Stage13r original source evidence output set changed")
    for name,digest in outputs.items():
        need("/" not in name and "\\" not in name and sha(RR/name)==digest,
             "Stage13r original SHA-sealed ledger corrupted "+name)
    signed_summary=pd.read_csv(must(RR/RR_GROUPS),low_memory=False)
    signed_detail=pd.read_csv(must(RR/RR_DETAIL),low_memory=False)
    need(len(signed_summary)==18 and
         set(signed_summary.source_full_run_id.astype(int))==set(IDS)|set(EXCLUDED_IDS),
         "Original Stage13r 18 source full run identities altered")
    selected=signed_summary.loc[signed_summary.source_full_run_id.isin(IDS)]
    need(len(selected)==12 and
         selected.full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview.astype(bool).all() and
         selected.left_measured_original_source_QC0.astype(bool).all() and
         selected.right_measured_original_source_QC0.astype(bool).all() and
         selected.original_QC1_halfhour_count.sum()==235 and
         selected.previously_method_approved_source_centers.sum()==17 and
         selected.new_source_QC1_neighbors_requiring_new_operator_authorization.sum()==218,
         "Stage13r original 2015 source science PASS preview/group counts changed")
    held=signed_summary.loc[signed_summary.source_full_run_id.isin(EXCLUDED_IDS)]
    need(len(held)==6 and
         not held.full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview.astype(bool).any() and
         held.new_source_QC1_neighbors_requiring_new_operator_authorization.sum()==761,
         "six original source failed groups inadvertently included")
    # Re-run original Stage13r audit to establish actual original native
    # source QC, site TA/PSRF/ERA physics on this host, not only old CSV.
    sink=io.StringIO()
    with contextlib.redirect_stdout(sink):
        fresh_summary,fresh_detail,agg,other_spec,_=module.audit()
    need(len(fresh_summary)==18 and
         agg.get("source_full_runs_passing_synthetic_full_run_RH_QBOT_VPD_preview")==12 and
         agg.get("new_QC1_neighbors_requiring_fresh_operator_authorization")==979 and
         agg.get("original_policy_approved_33_centers")==33,
         "current rerun original 18-group science changed")
    for run_id in IDS:
        old=signed_summary.loc[signed_summary.source_full_run_id.eq(run_id)]
        new=fresh_summary.loc[fresh_summary.source_full_run_id.eq(run_id)]
        need(len(old)==len(new)==1,"Stage13r run missing "+str(run_id))
        for c in ("source_original_QC1_start","source_original_QC1_end",
                  "original_QC1_halfhour_count","previously_method_approved_source_centers",
                  "new_source_QC1_neighbors_requiring_new_operator_authorization",
                  "full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview"):
            need(str(old.iloc[0][c])==str(new.iloc[0][c]),
                 "fresh original source scientific run identity changed "+str(run_id)+" "+c)
        need(near(float(old.iloc[0].max_30min_VPD_step_hPa_ERA_RH_full_run_preview),
                  float(new.iloc[0].max_30min_VPD_step_hPa_ERA_RH_full_run_preview),1e-7),
             "original source 30min full-run continuous preview changed "+str(run_id))
    return src,centers,signed_summary,signed_detail,receipt

def audit(approval_path):
    operator=approval(approval_path)
    original_mod=load_original_stage13r()
    src,centers,groups,ledger,receipt=verified_science(original_mod)
    base=pd.read_csv(must(AC/AC_FILE),dtype={"time":str},low_memory=False)
    keys=pd.DatetimeIndex(datekey(base.time),name="native_time")
    need(len(base)>=17520 and len(base)%17520==0 and keys.is_unique and
         keys.is_monotonic_increasing and keys.year.min()<=2015 and keys.year.max()>=2017 and
         all((keys.month!=2)|(keys.day!=29)),
         "original Stage12ac NOLEAP full source years/timestamps invalid")
    need(set(STAGE12AC_FIVE).issubset(set(keys)),
         "previous 5 operator-approved Jul2017 Me6 source times missing")
    base.index=keys
    primary=pd.read_csv(must(src["primary"]),usecols=[
         "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
         dtype={"TIMESTAMP_START":str},low_memory=False)
    companion=pd.read_csv(must(src["era"]),usecols=[
         "TIMESTAMP_START","TA_ERA","VPD_ERA"],
         dtype={"TIMESTAMP_START":str},low_memory=False)
    primary=primary.loc[primary.TIMESTAMP_START.str[:4].eq("2015")].copy()
    companion=companion.loc[companion.TIMESTAMP_START.str[:4].eq("2015")].copy()
    need(len(primary)==len(companion)==17520 and
         primary.TIMESTAMP_START.is_unique and companion.TIMESTAMP_START.is_unique and
         primary.TIMESTAMP_START.tolist()==companion.TIMESTAMP_START.tolist(),
         "signed 2015 original site tower and companion ERA native source differ")
    source=pd.merge(primary,companion,on="TIMESTAMP_START",validate="one_to_one")
    source.index=pd.DatetimeIndex(pd.to_datetime(source.TIMESTAMP_START,
                              format="%Y%m%d%H%M"),name="native_time")
    need(source.index.is_unique and source.index.is_monotonic_increasing and
         source.index.isin(keys).all(),
         "2015 source native index/site selected NOLEAP clock changed")
    for col in source.columns:
        if col=="TIMESTAMP_START":continue
        source[col]=pd.to_numeric(source[col],errors="coerce")
        source.loc[source[col]<=-9990,col]=np.nan

    science=[]
    candidate=base.copy(deep=True)
    targeted=set()
    protected={t:base.loc[t].copy(deep=True) for t in STAGE12AC_FIVE}
    by_run={}
    reviewed={pd.to_datetime(k,format="%Y%m%d%H%M") for k in centers.native_key}
    for record in operator["approved_source_native_QC1_full_runs"]:
        run_id=int(record["original_stage13r_full_run_id"])
        start=ts(record["first"]);end=ts(record["last"])
        sample=pd.date_range(start,end,freq="30min")
        need(len(sample)==int(record["original_native_30min_records"]) and
             start.year==end.year==2015 and run_id in IDS,
             "operator exact original 2015 QC1 full native scope wrong "+str(run_id))
        need(int(record["old_method_approved_center_count"])==
             len(set(sample).intersection(reviewed)) and
             int(record["new_QC1_neighbour_scope_authorized"])==
             len(set(sample).difference(reviewed)),
             "operator prior and new exact QC1 record counts changed "+str(run_id))
        stored=groups.loc[groups.source_full_run_id.eq(run_id)]
        need(len(stored)==1 and
             start==ts(stored.iloc[0].source_original_QC1_start) and
             end==ts(stored.iloc[0].source_original_QC1_end) and
             len(sample)==int(stored.iloc[0].original_QC1_halfhour_count),
             "Stage13r SHA-signed source actual full QC1 bounds differ "+str(run_id))
        before=start-SOURCE_NATIVE_STEP
        after=end+SOURCE_NATIVE_STEP
        need(before in source.index and after in source.index and
             sample.isin(source.index).all() and sample.isin(candidate.index).all(),
             "original site native source internal / both boundary records missing "+str(run_id))
        need(before not in targeted and after not in targeted,
             "operator 2015 run overlaps an earlier scope boundary")
        need(int(source.at[before,"VPD_F_QC"])==0 and
             int(source.at[after,"VPD_F_QC"])==0,
             "original source VPD QC0 observations not both sides "+str(run_id))
        anchor=[]
        for boundary in (before,after):
            measured=float(source.at[boundary,"VPD_F"])
            selected=float(base.at[boundary,"VPD_USE"])
            need(np.isfinite([measured,selected]).all() and near(measured,selected,1e-7),
                 "Stage12ac original actually measured QC0 boundary changed "+str(boundary))
            anchor.append({"time":str(boundary),"source_VPD_F_QC":0,
                           "original_measured_VPD_hPa":measured,
                           "retained_Stage12ac_VPD_hPa":selected})
        vals=[]
        for time in sample:
            need(time not in targeted and time not in STAGE12AC_FIVE and
                 time.year==2015,"off-source allowed native scope overlap "+str(time))
            s=source.loc[time]
            need(float(s.VPD_F_QC)==1 and float(s.TA_F_QC)==0 and
                 np.isfinite([s.TA_F,s.VPD_F,s.TA_ERA,s.VPD_ERA]).all(),
                 "original source VPD QC1 or measured tower T/source ERA invalid "+str(time))
            T=float(base.at[time,"TA_USE"])
            P=float(base.at[time,"PSRF"])
            need(np.isfinite([T,P]).all() and near(T,s.TA_F,1e-7),
                 "original site tower temperature not retained at "+str(time))
            v,q,rh,ph=original_mod.src_rh_at_site(
                T,P,float(s.TA_ERA),float(s.VPD_ERA))
            need(ph=="PASS" and 0<rh<100 and 0<v<original_mod.water_es(T)
                 and 0<q<.08 and abs(T-float(s.TA_ERA))<=8,
                 "original source ERA RH, site VPD/QBOT water science failed "+str(time))
            signed=ledger.loc[(ledger.full_run.eq(run_id))&
                              (ledger.native_time.eq(str(time)))]
            need(len(signed)==1 and
                 signed.iloc[0].operator_status in (
                     "PREVIOUS_33_METHOD_APPROVED_CENTER",
                     "NEW_UNAPPROVED_QC1_NEIGHBOR_HYPOTHETICAL") and
                 near(v,float(signed.iloc[0].hypothetical_at_site_T_VPD_hPa),1e-8) and
                 near(q,float(signed.iloc[0].hypothetical_at_site_T_QBOT_kgkg),1e-10),
                 "original signed Stage13r complete source candidate VPD/QBOT changed "+str(time))
            existingV=float(base.at[time,"VPD_USE"])
            existingQ=float(base.at[time,"QBOT"])
            candidate.at[time,"VPD_USE"]=v
            candidate.at[time,"QBOT"]=q
            targeted.add(time)
            vals.append(v)
            science.append({
                "original_stage13r_run_id":run_id,
                "native_time":str(time),"source_2015_QC1":1,
                "source_original_T_QC0":0,
                "operator_previously_method_approved_center":bool(time in reviewed),
                "operator_authorized_20261027":True,
                "retained_tower_TA_USE_C":T,
                "retained_original_PSRF_Pa":P,
                "original_ERA_TA_C":float(s.TA_ERA),
                "original_ERA_VPD_hPa":float(s.VPD_ERA),
                "paired_ERA_RH_at_ERA_T_pct":rh,
                "original_Stage12ac_VPD_USE_hPa":existingV,
                "new_ERA_RH_VPD_USE_hPa":v,
                "original_Stage12ac_QBOT_kgkg":existingQ,
                "new_ERA_RH_QBOT_kgkg":q,
                "scientific_center_source_QC_RH_QBOT_PASS":True})
        joined=np.asarray([float(base.at[before,"VPD_USE"]),*vals,
                           float(base.at[after,"VPD_USE"])],dtype=float)
        steps=np.abs(np.diff(joined))
        need(len(steps)==len(sample)+1 and np.isfinite(steps).all() and
             np.all(steps<=MAX_JUMP+1e-12),
             "whole original QC1 source run VPD 30min continuity failed "+str(run_id)+
             " max="+str(float(np.nanmax(steps))))
        by_run[run_id]={
            "run_id":run_id,"native_first":str(start),"native_last":str(end),
            "source_QC1_native_halfhours":len(sample),
            "previously_method_approved_center_count":
                len(set(sample).intersection(reviewed)),
            "new_original_QC1_neighbour_authorized":
                len(set(sample).difference(reviewed)),
            "two_retained_original_QC0_bookends":anchor,
            "max_native_30min_step_VPD_hPa":float(steps.max()),
            "all_site_RH_QBOT_physics_pass":True,
            "source_sci_all_pass":True}
    need(len(targeted)==EXPECTED_NUM and len(science)==EXPECTED_NUM and
         set(t.year for t in targeted)=={2015} and
         sum(s["previously_method_approved_center_count"] for s in by_run.values())==17 and
         sum(s["new_original_QC1_neighbour_authorized"] for s in by_run.values())==218,
         "actual 235 source times, 17 centers + 218 other originals mis-scoped")
    need(set(by_run)==set(IDS),"one of approved 12 full source runs not audited")
    need(not set(STAGE12AC_FIVE)&targeted,
         "previous 2017 operator-approved Stage12ac source changed")
    for time in STAGE12AC_FIVE:
        need(candidate.loc[time].equals(protected[time]),
             "operator-approved 2017-07-04 original five source rows changed")
    for col in base.columns:
        if col=="time": continue
        b=pd.to_numeric(base[col],errors="coerce").to_numpy(dtype=float)
        c=pd.to_numeric(candidate[col],errors="coerce").to_numpy(dtype=float)
        actual_change=~np.isclose(b,c,rtol=0,atol=1e-12,equal_nan=True)
        touched=set(candidate.index[actual_change])
        if col in ("VPD_USE","QBOT"):
            need(touched.issubset(targeted),"forbidden source time edited in "+col)
        else:
            need(not touched,"forbidden variable edited "+col)
    need(base.time.equals(candidate.time),"original native full time column changed")
    need(len(base)==len(candidate) and len(base)%17520==0,
         "complete original NOLEAP forcing length altered")
    change_counts={}
    newly_finite={}
    for col in ("VPD_USE","QBOT"):
        old=base[col].to_numpy(dtype=float)
        new=candidate[col].to_numpy(dtype=float)
        changed=~np.isclose(old,new,rtol=0,atol=1e-12,equal_nan=True)
        change_counts[col]=int(changed.sum())
        newly_finite[col]=int(np.sum(np.isnan(old)&np.isfinite(new)))
        need(change_counts[col]>=17 and change_counts[col]<=235,
             "source VPD/QBOT numeric delta unexpectedly outside approved 235")
    return base,candidate,pd.DataFrame(science),[by_run[k] for k in IDS],{
       "site":"US-Me6","version":VERSION,
       "signed_operator_Stage13s_approval_SHA256":sha(approval_path),
       "previous_Stage13r_readonly_signed_receipt_SHA256":sha(RR/RR_RECEIPT),
       "previous_Stage13q_readonly_signed_receipt_SHA256":
           sha(Q/"stage13q_readonly_original_source_SHA_receipt.json"),
       "original_Stage12ac_approved_selected_source_SHA256":sha(AC/AC_FILE),
       "original_tower_source_SHA256":sha(src["primary"]),
       "original_companion_ERA_SHA256":sha(src["era"]),
       "source_original_2015_full_QC1_runs_approved":12,
       "source_original_QC1_2015_HH_science_PASS":235,
       "previous_17_source_method_approved_centers_included":17,
       "additional_218_original_QC1_source_neighbours_authorized":218,
       "original_source_measured_QC0_bookends_preserved":24,
       "other_2015_2017_original_QC1_held_runs_unchanged":6,
       "other_761_unapproved_QC1_neighbours_unchanged":True,
       "previous_Stage12ac_five_2017_source_rows_unchanged":True,
       "source_315360_or_other_exact_multiple_NOLEAP_rows":len(base),
       "actual_updated_field_value_counts":change_counts,
       "newly_filled_old_HOLD_source_values":newly_finite,
       "operator_has_NOT_approved_D_model_schemes":True,
       "original_data_changed":False,"postv5_approved":False,
       "DATM_ready":False,"Slurm_jobs_submitted":False,
       "status":"ALL_12_OPERATOR_APPROVED_2015_SOURCE_QC1_RUNS_SCIENCE_PASS_RESEARCH_ONLY"
       }

def apply(approval_path,base,candidate,ledger,groups,report):
    folder=ROOT/"science_trials"/(
        "stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    marker=folder/"INCOMPLETE_EXPORT_NOT_MODEL_FORCING"
    marker.write_text("Source science export in progress; original Stage12ac preserved.\n")
    candidate.to_csv(folder/MODEL_OUT,index=False,float_format="%.17g")
    reopened=pd.read_csv(must(folder/MODEL_OUT),dtype={"time":str},low_memory=False)
    need(len(reopened)==len(base) and
         list(reopened.columns)==list(base.columns) and
         reopened.time.equals(base.time.reset_index(drop=True)),
         "Stage13s entire site native NOLEAP CSV readback changed")
    for column in candidate.columns:
        if column=="time":continue
        a=candidate[column].to_numpy(dtype=float)
        b=pd.to_numeric(reopened[column],errors="coerce").to_numpy(dtype=float)
        need(np.allclose(a,b,rtol=1e-14,atol=1e-12,equal_nan=True),
             "Stage13s on-disk CSV value changed beyond roundtrip "+column)
    led="235_original_QC1_operator_approved_site_ERA_RH_VPD_QBOT.csv"
    summary="12_complete_2015_original_QC1_run_science_PASS.json"
    brief="stage13s_Me6_scientific_source_and_field_delta_summary.json"
    ledger.to_csv(folder/led,index=False,float_format="%.17g")
    (folder/summary).write_text(json.dumps(groups,indent=2)+"\n")
    (folder/brief).write_text(json.dumps(report,indent=2)+"\n")
    notice="RESEARCH_ONLY_NOT_POSTV5_DATM_AD400_SLURM"
    (folder/notice).write_text(
        "Exact user-approved 2015 US-Me6 12 original full source QC1 runs"
        " containing 235 original halfhour RH/VPD records science checked."
        " Retained previous 2017 Stage12ac user-approved five halfhours."
        " No unapproved 2015/2017 other held full source runs are repaired."
        " The original ERA RH is reanalysis, not tower RH observation."
        " Full site CSV still has unrelated unresolved source HOLDs."
        " No original source, PFT/ZBOT, CIME/DATM, AD400/Normal400,"
        " Slurm or model configuration changed.\n")
    outputs=(MODEL_OUT,led,summary,brief,notice)
    need(sha(AC/AC_FILE)==report["original_Stage12ac_approved_selected_source_SHA256"],
         "original source Stage12ac SHA unexpectedly changed after new forcing export")
    receipt={
       "version":VERSION,"site":"US-Me6",
       "operator_decision_SHA256":sha(approval_path),
       "immutable_original_Stage12ac_SHA256":sha(AC/AC_FILE),
       "immutable_original_Stage13r_readonly_SHA256":sha(RR/RR_RECEIPT),
       "all_12_entire_native_2015_original_QC1_runs_science_PASS":True,
       "approved_original_source_halfhours":235,
       "new_218_original_source_QC1_neighbor_scope":218,
       "original_QC0_24_boundaries_retained":True,
       "existing_2017_Stage12ac_five_source_values_preserved":True,
       "model_field_cell_change_counts":report["actual_updated_field_value_counts"],
       "Postv5":False,"DATM":False,"AD400":False,"Slurm":False,
       "output_SHA256":{name:sha(folder/name) for name in outputs}}
    (folder/"stage13s_Me6_operator_235HH_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    marker.unlink()
    print("STAGE13S ALL 12 SOURCE RUNS PASS; 235 ORIGINAL QC1 HH OPERATOR APPROVED RESEARCH SHADOW SUCCESS",folder,flush=True)
    print("STAGE13S 2015 exact 235 native records; SOURCE-VPD/QBOT actual field delta",
          report["actual_updated_field_value_counts"],"old H0 fills",
          report["newly_filled_old_HOLD_source_values"],flush=True)
    print("STAGE13S ORIGINAL Stage12ac 2017 5 VALUES & 6 SOURCE HELD RUNS PRESERVED; NO Slurm/DATM/AD400",flush=True)

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","apply"):mode.add_argument("--"+x,action="store_true")
    p.add_argument("--approval",type=Path)
    args=p.parse_args()
    print("STAGE13S USER-APPROVED Me6 TWELVE 2015 ORIGINAL QC1 RUNS | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    if not args.approval:p.error("--approval signed operator Stage13s JSON required")
    base,new,ledger,groups,report=audit(args.approval)
    print("\nSTAGE13S SCIENCE VERIFIED 12 FULL ORIGINAL QC1 SEGMENTS",flush=True)
    for r in groups:
        print(json.dumps({"run":r["run_id"],"n":r["source_QC1_native_halfhours"],
                          "max_VPD_jump":r["max_native_30min_step_VPD_hPa"],
                          "QC0_bookends":2,"ERA_RH_QBOT":"PASS"}),flush=True)
    print("STAGE13S SOURCE RESULT",json.dumps(report,indent=2),flush=True)
    if args.check:
        print("STAGE13S READONLY CHECK PASS | all twelve whole QC1 runs, 235 native HH, 24 original QC0 bookends, 2017 protected; NO WRITES",flush=True)
        return
    apply(args.approval,base,new,ledger,groups,report)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13S SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

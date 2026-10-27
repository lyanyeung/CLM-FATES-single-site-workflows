#!/usr/bin/env python3
"""US-Me6 Stage13u: BATCH science triage of ALL 6 remaining original QC1 runs.

After successful Stage13s (12x2015 full runs) and Stage13t (2015-Sep26
4HH ERA mismatch), identify all 6 preserved Stage13r full source QC1
HOLD episodes (782 native HH, 16 earlier center-method-reviewed,
5 existing 2017 Stage12ac protected, 761 other unapproved QC1 slots).

Strictly signed original Stage13r / Stage13s / Stage13t receipts and
original FLUXMET+ERA sources. For each original native source halfhour:
measured T QC, retained T, paired ERA RH/QBOT, original 2017 protection,
retained Stage13s VPD/QBOT, full-run native joins / QC0 anchors;
nearest other measured VPD QC0 on either side (within 14 days).
Whole full-episode candidate ERA replacement and, ONLY for tiny fully
QC0-bounded runs, QC0-anchored line are DIAGNOSTICS, never acceptance.

--self-test no source reads; --check read-only; --run generates only
SHA-signed evidence tables. Never update forcing, originals or model.
Do not extend prior human approval; ask for one BATCH scope decision
after source evidence, not repeated single time decisions.
"""
import argparse,hashlib,importlib.util,json,subprocess,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VER="batch03-stage13u-v1-20261027-Me6-six-original-QC1-held-runs-batch-triage"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
MOD=HERE/"13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
MOD_BLOB="5a8dc69f5fb65015a9b7c9096153935684f466a8"
RR=ROOT/"reports/stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_20261027T004033Z_5eefea7b"
RT=ROOT/"reports/stage13t_Me6_20150926_four_QC1_original_QC0_ERA_RH_READONLY_20261027T071247Z_a30c3a4e"
RS=ROOT/"science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105"
AC=ROOT/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
RS_CSV="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
AC_CSV="US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv"
RR_GROUPS="US-Me6_source_original_full_QC1_runs_grouped_OPERATOR_APPROVAL_NEEDED.csv"
RR_REC="stage13r_source_original_QC1_SHA_receipt.json"
RS_REC="stage13s_Me6_operator_235HH_SHA_receipt.json"
RT_REC="stage13t_Me6_four_QC1_original_QC0_SHA_receipt.json"
HELD_IDS=(12,14,15,16,17,18)
PASS_IDS=(1,2,3,4,5,6,7,8,9,10,11,13)
HH=pd.Timedelta(minutes=30)
MAX_STEP=4.
QC0_SEARCH_HH=14*48
SOURCE_COUNTS={"original_QC1":782,"prior_method_centers":16,
               "five_2017_protected":5,"other_unapproved":761}
EXISTING_FIVE={pd.Timestamp("2017-07-04 06:00")+i*HH for i in range(5)}

def must(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("signed original source/report missing/symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def require(ok,message):
    if not bool(ok):
        raise RuntimeError("STAGE13U READONLY SOURCE HOLD: "+str(message))

def near(a,b,eps=1e-8):
    return bool(np.isfinite([float(a),float(b)]).all() and
                np.isclose(float(a),float(b),atol=eps,rtol=0))

def check_receipt(folder,rec_name,digest_field):
    d=json.loads(must(folder/rec_name).read_text())
    output=d.get(digest_field,{})
    require(isinstance(output,dict) and len(output)>=2,
            "receipt does not have signed output set "+str(folder))
    for k,v in output.items():
        require("/" not in k and "\\" not in k and sha(folder/k)==v,
                "source science receipt output SHA mismatch "+k)
    return d

def load_prev():
    m=must(MOD)
    b=subprocess.run(["git","hash-object",str(m)],capture_output=True,
                     text=True,check=True).stdout.strip()
    require(b==MOD_BLOB,"prior original Stage13r scientific code blob changed")
    spec=importlib.util.spec_from_file_location("me6_stage13r_signed_stage13u",m)
    require(spec is not None and spec.loader is not None,"signed source science cannot load")
    x=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(x)
    require(x.VER=="batch03-stage13r-v1-20261027-Me6-original-full-QC1-run-survey"
            and x.ROOT==ROOT and x.AC==AC and
            x.Q==ROOT/"reports/stage13q_Me6_33_original_ERA_RH_group_source_review_20261027T002737Z_445444f6",
            "original Stage13r method/site and source inputs changed")
    return x

def selftest():
    q=np.asarray([0.,1.,1.,1.,1.,0.])
    require(len(HELD_IDS)==6 and len(PASS_IDS)==12 and
            len(set(HELD_IDS)&set(PASS_IDS))==0,
            "scientific hold and passed original group IDs overlapped")
    require(SOURCE_COUNTS["original_QC1"]==
            SOURCE_COUNTS["prior_method_centers"]+
            SOURCE_COUNTS["five_2017_protected"]+
            SOURCE_COUNTS["other_unapproved"],"fixed 782 original source scopes do not sum")
    require(len(EXISTING_FIVE)==5 and np.sum(q==1)==4,
            "test group original source QC1/QC0 pattern changed")
    p0=5.413;p1=6.468
    line=np.linspace(p0,p1,6)
    require(near(float(max(abs(np.diff(line)))),.211,1e-10),
            "2015 Sep26 example should be diagnostic only")
    print("STAGE13U SELF-TEST PASS | 6 HOLD groups=782 QC1 including 761 not approved + 5 protected; no forcing writes",flush=True)

def forcing(p):
    df=pd.read_csv(must(p),dtype={"time":str},low_memory=False)
    index=pd.to_datetime(df.time.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12],
                         format="%Y%m%d%H%M",errors="raise")
    require(len(df)==280320 and index.is_unique and index.is_monotonic_increasing and
            not ((index.month==2)&(index.day==29)).any(),
            "original 16y Me6 NOLEAP selected site forcing invalid")
    df.index=pd.DatetimeIndex(index,name="native_time")
    return df

def nearest_qc0(source,index,edge,direction):
    # Search original native VPD_F_QC0 measured and finite, never QC1/2.
    p=source.index.get_loc(edge)
    for step in range(1,QC0_SEARCH_HH+1):
        i=p+(step if direction>0 else -step)
        if not 0<=i<len(source):break
        if abs((source.index[i]-edge)/HH)!=step:break
        row=source.iloc[i]
        if row["VPD_F_QC"]==0 and np.isfinite(row["VPD_F"]):
            return source.index[i],step,float(row["VPD_F"])
    return None,None,None

def audit():
    mod=load_prev()
    source_spec,centers,_,_=mod.verified()
    r=check_receipt(RR,RR_REC,"outputs_SHA256")
    s=check_receipt(RS,RS_REC,"output_SHA256")
    t=check_receipt(RT,RT_REC,"files_SHA256")
    require(r.get("version")==mod.VER and
            r.get("source_full_original_QC1_runs")==18 and
            r.get("original_33_source_centers")==33 and
            r.get("model_forcing_written") is False,
            "actual Stage13r signed original full runs not established")
    require(s.get("version")=="batch03-stage13s-v1-20261027-Me6-12-full-2015-QC1-runs-235HH" and
            s.get("approved_original_source_halfhours")==235 and
            s.get("all_12_entire_native_2015_original_QC1_runs_science_PASS") is True and
            s.get("immutable_original_Stage12ac_SHA256")==sha(AC/AC_CSV) and
            s.get("original_QC0_24_boundaries_retained") is True,
            "signed successful Stage13s selected forcing source changed")
    require(s["output_SHA256"].get(RS_CSV)==sha(RS/RS_CSV) and
            s.get("existing_2017_Stage12ac_five_source_values_preserved") is True,
            "signed prior approved Stage13s site candidate mutated")
    require(t.get("version")=="batch03-stage13t-v1-20261027-Me6-four-20150926-QC1-QC0-source-science" and
            t.get("stage13s_signed_existing_shadow_SHA256")==sha(RS/RS_CSV) and
            t.get("new_science_or_operator_repair_authorization") is False and
            t.get("new_model_forcing_written") is False,
            "actual Stage13t operator HOLD or signed output different")
    g=pd.read_csv(must(RR/RR_GROUPS),low_memory=False)
    held=g.loc[g.source_full_run_id.isin(HELD_IDS)].copy()
    other=g.loc[g.source_full_run_id.isin(PASS_IDS)].copy()
    require(len(g)==18 and len(held)==6 and len(other)==12 and
            tuple(held.source_full_run_id.astype(int))==HELD_IDS and
            not held.full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview.astype(bool).any() and
            int(held.original_QC1_halfhour_count.sum())==782 and
            int(held.previously_method_approved_source_centers.sum())==16 and
            int(held.new_source_QC1_neighbors_requiring_new_operator_authorization.sum())==761,
            "six scientific held source run scopes/aggregate changed")
    latest=forcing(RS/RS_CSV)
    previous=forcing(AC/AC_CSV)
    require(latest.time.equals(previous.time) and
            list(latest.columns)==list(previous.columns),
            "2017 source chronology or columns have changed")
    for v in EXISTING_FIVE:
        for c in latest.columns:
            if c=="time":
                require(latest.at[v,c]==previous.at[v,c],"protected original 2017 clock")
            else:
                a,b=float(latest.at[v,c]),float(previous.at[v,c])
                require((np.isnan(a) and np.isnan(b)) or
                        np.isclose(a,b,rtol=1e-14,atol=1e-12),
                        "previously approved 2017 July04 original field altered "+c)
    # Full 2015/2017 native original sources, no site changes and no source writes.
    tcols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    ecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
    yr=("2015","2017")
    tt=pd.read_csv(must(source_spec["primary"]),dtype={"TIMESTAMP_START":str},
                   usecols=tcols,low_memory=False)
    ee=pd.read_csv(must(source_spec["era"]),dtype={"TIMESTAMP_START":str},
                   usecols=ecols,low_memory=False)
    tt=tt.loc[tt.TIMESTAMP_START.str[:4].isin(yr)].copy()
    ee=ee.loc[ee.TIMESTAMP_START.str[:4].isin(yr)].copy()
    require(len(tt)==len(ee)==2*17520 and
            tt.TIMESTAMP_START.is_unique and ee.TIMESTAMP_START.is_unique and
            tt.TIMESTAMP_START.tolist()==ee.TIMESTAMP_START.tolist(),
            "signed 2015+2017 original tower vs paired ERA native time mismatch")
    source=tt.merge(ee,on="TIMESTAMP_START",validate="one_to_one")
    source.index=pd.DatetimeIndex(pd.to_datetime(
        source.TIMESTAMP_START,format="%Y%m%d%H%M"),name="native_time")
    require(source.index.is_unique and source.index.is_monotonic_increasing,
            "source site original 2015/2017 native time monotonicity")
    for c in tcols[1:]+ecols[1:]:
        source[c]=pd.to_numeric(source[c],errors="coerce")
        source.loc[source[c]<=-9990,c]=np.nan
    center_set={pd.to_datetime(x,format="%Y%m%d%H%M") for x in centers.native_key}
    records=[]
    groups=[]
    held_times=set()
    for item in held.itertuples():
        id=int(item.source_full_run_id)
        first=pd.Timestamp(item.source_original_QC1_start)
        last=pd.Timestamp(item.source_original_QC1_end)
        native=pd.date_range(first,last,freq="30min")
        require(len(native)==int(item.original_QC1_halfhour_count),
                "historical original full run length changed ID"+str(id))
        require(native.isin(source.index).all() and native.isin(latest.index).all() and
                not held_times.intersection(native),
                "original source full run missing or overlaps"+str(id))
        held_times.update(native)
        protected=set(native)&EXISTING_FIVE
        reviewed=set(native)&center_set
        additional=set(native)-center_set-EXISTING_FIVE
        require(len(additional)==int(item.new_source_QC1_neighbors_requiring_new_operator_authorization),
                "original 761 unapproved source neighbor count differs for run"+str(id))
        before=first-HH;after=last+HH
        require(before in source.index and after in source.index and
                before in latest.index and after in latest.index,
                "native QC0/QC2 source bookends not available "+str(id))
        leftQC=float(source.at[before,"VPD_F_QC"])
        rightQC=float(source.at[after,"VPD_F_QC"])
        measured_both=leftQC==0 and rightQC==0
        computed=[]
        phys=0
        t_measure=0
        t_approved=0
        qc1=0
        selected_old_missing=0
        for x in native:
            row=source.loc[x]
            model=latest.loc[x]
            qc_ok=float(row.VPD_F_QC)==1
            qc1+=int(qc_ok)
            preserved=x in EXISTING_FIVE
            origT=float(model.TA_USE)
            t0=bool(float(row.TA_F_QC)==0 and
                    np.isfinite(row.TA_F) and
                    np.isfinite(origT) and
                    near(origT,float(row.TA_F),1e-7))
            t_measure+=int(t0)
            t_approved+=int(preserved)
            v,q,rh,status=mod.src_rh_at_site(
                 origT,float(model.PSRF),float(row.TA_ERA),float(row.VPD_ERA))
            valid=(status=="PASS" and (t0 or preserved) and qc_ok)
            phys+=int(valid)
            oldV=float(model.VPD_USE)
            selected_old_missing+=int(not np.isfinite(oldV))
            value=oldV if preserved else v
            computed.append(float(value))
            records.append({
                "full_run_id":id,"native_time":str(x),
                "original_source_QC1":bool(qc_ok),
                "original_TA_F_QC":float(row.TA_F_QC),
                "original_measured_tower_T_C":float(row.TA_F),
                "retained_stage13s_site_T_C":origT,
                "source_tower_T_QC0_matches_retained":t0,
                "original_tower_VPD_F_hPa":float(row.VPD_F),
                "original_paired_ERA_T_C":float(row.TA_ERA),
                "original_paired_ERA_VPD_hPa":float(row.VPD_ERA),
                "paired_ERA_RH_percent":rh,
                "stage13s_retained_site_PSRF_Pa":float(model.PSRF),
                "hypothetical_ERA_RH_at_site_VPD_hPa":v,
                "hypothetical_ERA_RH_at_site_QBOT_kgkg":q,
                "source_physics_and_retained_T_gate_PASS":bool(valid),
                "protected_existing_2017_Stage12ac_value_not_changed":preserved,
                "previously_method_approved_center":bool(x in reviewed),
                "additional_QC1_neighbor_operator_approval_absent":bool(x in additional),
                "unchanged_stage13s_VPD_USE_hPa":oldV,
                "unchanged_stage13s_QBOT_kgkg":float(model.QBOT),
                "hypothetical_ERA_candidate_VPD_or_preserved_2017":value,
                "new_forcing_or_operator_approval":False})
        require(qc1==len(native),"original QC1 source run changed "+str(id))
        joined=[float(latest.at[before,"VPD_USE"]),*computed,
                float(latest.at[after,"VPD_USE"])]
        edges=np.abs(np.diff(np.asarray(joined,dtype=float)))
        era_max=float(edges.max()) if np.isfinite(edges).all() else None
        era_edges_fail=int(np.sum(edges>MAX_STEP)) if np.isfinite(edges).all() else None
        near_left=nearest_qc0(source,source.index,before,-1)
        near_right=nearest_qc0(source,source.index,after,1)
        # First/last source QC0 bookends often QC2 in 2017: nearest measured
        # QC0 may be many hours away. Never invent a direct boundary.
        linear_max=None
        linear_physics_pass=None
        if len(native)<=8 and measured_both and np.isfinite(joined[0]) and np.isfinite(joined[-1]):
            line=np.linspace(joined[0],joined[-1],len(native)+2)
            linear_max=float(np.max(np.abs(np.diff(line))))
            physical=[]
            for j,x in enumerate(native):
                T=float(latest.at[x,"TA_USE"]);P=float(latest.at[x,"PSRF"])
                es=mod.water_es(T)
                q=.622*(es-float(line[j+1]))*100/(P-.378*(es-float(line[j+1]))*100)
                physical.append(np.isfinite([T,P,q]).all() and 0<float(line[j+1])<es and 0<q<.08)
            linear_physics_pass=bool(all(physical))
        groups.append({
          "full_source_run_id":id,"original_source_QC1_start":str(first),
          "original_source_QC1_end":str(last),"original_QC1_native_HH":len(native),
          "previously_method_approved_source_centers":len(reviewed),
          "previously_Stage12ac_approved_2017_native_rows":len(protected),
          "new_QC1_neighbours_NOT_OPERATOR_APPROVED":len(additional),
          "source_original_VPD_QC1_confirmed_HH":qc1,
          "source_original_tower_T_QC0_matches_retained_HH":t_measure,
          "source_ERA_RH_VPD_QBOT_and_valid_T_HH":phys,
          "source_no_longer_missing_old_VPD_HH":len(native)-selected_old_missing,
          "source_STILL_MISSING_old_VPD_HH":selected_old_missing,
          "native_pre_boundary_VPD_QC":leftQC,
          "native_post_boundary_VPD_QC":rightQC,
          "both_direct_bookends_original_measured_QC0":bool(measured_both),
          "nearest_further_measured_QC0_before":str(near_left[0]) if near_left[0] is not None else None,
          "native_HH_to_nearest_measured_QC0_before":near_left[1],
          "nearest_further_measured_QC0_after":str(near_right[0]) if near_right[0] is not None else None,
          "native_HH_to_nearest_measured_QC0_after":near_right[1],
          "ERA_candidate_full_run_max_30min_VPD_step_hPa":era_max,
          "ERA_candidate_native_VPD_edges_gt4hPa":era_edges_fail,
          "HYPOTHETICAL_SHORT_QC0_ANCHOR_LINEAR_VPD_max_step_hPa":linear_max,
          "HYPOTHETICAL_SHORT_LINEAR_physical_QBOT_pass":linear_physics_pass,
          "no_repair_method_or_new_neighbors_operator_approved":True,
          "source_science_status":"HOLD_REQUIRES_BATCH_HUMAN_APPROVAL_AND_EXTRA_SOURCE_VERIFICATION"
        })
    out=pd.DataFrame(groups)
    data=pd.DataFrame(records)
    require(len(out)==6 and len(data)==782 and
            int(out.new_QC1_neighbours_NOT_OPERATOR_APPROVED.sum())==761 and
            int(out.previously_method_approved_source_centers.sum())==16 and
            int(out.previously_Stage12ac_approved_2017_native_rows.sum())==5,
            "signed six whole original source runs 782/16/5/761 provenance mismatch")
    agg={
      "site":"US-Me6","version":VER,"original_full_runs_held":6,
      "original_source_QC1_native_halfhours_examined":782,
      "previously_method_reviewed_center_records":16,
      "operator_previously_approved_Stage12ac_five_2017_records_protected":5,
      "additional_QC1_neighbours_not_authorized":761,
      "source_original_T_QC0_retained_count":int(out.source_original_tower_T_QC0_matches_retained_HH.sum()),
      "source_paired_ERA_RH_QBOT_physical_and_T_gate_count":int(out.source_ERA_RH_VPD_QBOT_and_valid_T_HH.sum()),
      "source_original_both_measured_QC0_direct_bookend_runs":int(out.both_direct_bookends_original_measured_QC0.sum()),
      "short_source_QC0_anchor_linear_method_hypothetical_ONLY":True,
      "signature_original_stage13r_SHA256":sha(RR/RR_REC),
      "signature_actual_stage13s_CSV_SHA256":sha(RS/RS_CSV),
      "signature_actual_stage13t_SHA256":sha(RT/RT_REC),
      "original_tower_FLUXMET_SHA256":sha(source_spec["primary"]),
      "original_native_ERA_SHA256":sha(source_spec["era"]),
      "reanalysis_RH_not_observed_tower_RH":True,
      "operator_batch_scope_not_yet_granted":True,
      "source_forcing_or_original_files_changed":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False
    }
    print("\nSTAGE13U REMAINING SIX SOURCE QC1 RUNS ORIGINAL SCIENCE BATCH TRIAGE",flush=True)
    cols=["full_source_run_id","original_QC1_native_HH",
          "new_QC1_neighbours_NOT_OPERATOR_APPROVED",
          "source_original_tower_T_QC0_matches_retained_HH",
          "source_ERA_RH_VPD_QBOT_and_valid_T_HH",
          "native_pre_boundary_VPD_QC","native_post_boundary_VPD_QC",
          "native_HH_to_nearest_measured_QC0_before",
          "native_HH_to_nearest_measured_QC0_after",
          "ERA_candidate_full_run_max_30min_VPD_step_hPa",
          "ERA_candidate_native_VPD_edges_gt4hPa",
          "HYPOTHETICAL_SHORT_QC0_ANCHOR_LINEAR_VPD_max_step_hPa"]
    print(out[cols].to_string(index=False),flush=True)
    print("STAGE13U READONLY BATCH SOURCE SUMMARY",json.dumps(agg,indent=2),flush=True)
    return data,out,agg

def main():
    ap=argparse.ArgumentParser()
    commands=ap.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"): commands.add_argument("--"+x,action="store_true")
    a=ap.parse_args()
    print("STAGE13U SIX SOURCE QC1 HOLD EPISODES | "+VER,flush=True)
    selftest()
    if a.self_test:return
    details,summary,totals=audit()
    if a.check:
        print("STAGE13U READONLY CHECK PASS | six original held runs, batch QC0/ERA RH/TA/QBOT triage; NO FORCING OR MODEL WRITES",flush=True)
        return
    folder=ROOT/"reports"/("stage13u_Me6_six_held_source_QC1_runs_BATCH_SCIENCE_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    a="six_held_original_source_QC1_runs_GROUPED_review.csv"
    b="782_original_native_QC1_records_tower_ERA_PSRF_RH_QBOT_review.csv"
    c="stage13u_Me6_six_runs_grouped_approval_decision_evidence.json"
    d="SOURCE_EVIDENCE_ONLY_NO_OPERATOR_APPROVAL_OR_MODEL_FORCING"
    summary.to_csv(folder/a,index=False,float_format="%.17g")
    details.to_csv(folder/b,index=False,float_format="%.17g")
    (folder/c).write_text(json.dumps(totals,indent=2)+"\n")
    (folder/d).write_text(
        "Stage13u is source-only batch triage, not original QC1 production"
        " QC assignment, no 761 source native neighbors human authorized."
        " Original ERA RH, source-anchored tiny-run linear method are research"
        " hypotheses only, no broad >300HH interpolation or 2017 QC2 boundary"
        " promotion, preserve existing five 2017 operator approvals."
        " This code never writes any forcing / DATM / AD400 / Slurm.\n")
    receipt={
       "version":VER,"site":"US-Me6",
       "original_source_stage13r_SHA":sha(RR/RR_REC),
       "original_source_stage13s_success_sha":sha(RS/RS_CSV),
       "original_source_stage13t_diagnostic_sha":sha(RT/RT_REC),
       "entire_six_held_source_runs_audited":6,
       "unapproved_source_neighbors_still_unapproved":761,
       "forcings_generated":False,"DATM":False,"Slurm":False,
       "outputs_SHA256":{name:sha(folder/name) for name in (a,b,c,d)}
    }
    (folder/"stage13u_six_held_source_runs_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13U READONLY BATCH REPORT DIR:",folder,flush=True)
    print("STAGE13U ALL SIX HELD SOURCE RUNS BATCH SCIENCE REPORT COMPLETE; NO FORCING OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13U STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

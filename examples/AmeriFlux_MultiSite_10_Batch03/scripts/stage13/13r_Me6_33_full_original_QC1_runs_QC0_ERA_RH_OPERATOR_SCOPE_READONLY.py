#!/usr/bin/env python3
"""Stage13r US-Me6 source QC1-run survey AFTER actual Stage13q 0/31 holds.

Uses Stage13q SHA-sealed actual IRIDIS6 output + immutable Stage12ac/source.
For exactly 33 original-native VPD QC1/HOLD source centers, find maximal
ORIGINAL consecutive VPD_F_QC=1 runs, true observed original QC0 bookends
(where available), sign and evidence of any native other QC1 slots that
would be required for a full episode; compare entire source-paired ERA-RH
at retained site T, QBOT, old native forcing and VPD/QBOT continuity.

No other native source time is operator-approved here. No source or forcing
writes. This is a future single grouped operator-review proposal, not permission.
Existing Stage12ac 2017-07-04 five approved source times protected.

--self-test standalone source-free, no writes
--check original pinned source and Stage13q receipt and output, no writes
--run same + independent SHA-signed READONLY reports only
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np

sys.dont_write_bytecode=True
VER="batch03-stage13r-v1-20261027-Me6-original-full-QC1-run-survey"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
Q=ROOT/"reports/stage13q_Me6_33_original_ERA_RH_group_source_review_20261027T002737Z_445444f6"
AC=ROOT/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
QREC="stage13q_readonly_original_source_SHA_receipt.json"
QCENTERS="US-Me6_33_original_native_source_QC_ERA_RH_VPD_QBOT.csv"
QGROUPS="US-Me6_33_contiguous_original_source_QC1_episode_group_PASS_HOLD.csv"
ACCSV="US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv"
ACREC="stage12ac_user_approved_5HH_SHA_receipt.json"
EXISTING_PROTECTED={pd.Timestamp("2017-07-04 06:00")+pd.Timedelta(minutes=30*i)
                    for i in range(5)}
HH=pd.Timedelta(minutes=30)
MAX_STEP=4.
MAX_PREVIEW_HH=300

def must(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing original signed source or unsafe symlink "+str(p))
    return p

def digest(p):
    h=hashlib.sha256()
    with must(p).open("rb") as stream:
        for data in iter(lambda:stream.read(1<<20),b""):
            h.update(data)
    return h.hexdigest()

def need(cond,msg):
    if not bool(cond):
        raise RuntimeError("STAGE13R ORIGINAL SOURCE SCIENCE STOP: "+str(msg))

def source_times(series):
    return pd.to_datetime(series,format="%Y%m%d%H%M",errors="raise")

def source_key(ts):
    return pd.Timestamp(ts).strftime("%Y%m%d%H%M")

def water_es(temp):
    return 6.112*np.exp(17.67*float(temp)/(float(temp)+243.5))

def src_rh_at_site(site_t,p,era_t,era_v):
    vals=[site_t,p,era_t,era_v]
    if not np.isfinite(vals).all() or not(50000.<p<110000.):
        return np.nan,np.nan,np.nan,"SOURCE_MISSING_T_P"
    satERA=water_es(era_t)
    RH=100*(1-era_v/satERA)
    satSite=water_es(site_t)
    v=satSite*(1-RH/100)
    partial=(satSite-v)*100
    q=.622*partial/(p-.378*partial)
    ok=(np.isfinite([RH,v,q]).all() and 0<RH<100 and
        0<v<satSite and 0<q<.08 and
        abs(site_t-era_t)<=8)
    return float(v),float(q),float(RH),("PASS" if ok else "HOLD_ERA_RH_T_PHYSICS")

def full_run(idx,qc,pos):
    # Exact original-source VPD_F_QC=1 only; do not bridge QC0/QC2.
    need(qc[pos]==1,"source center not original QC1")
    a=b=pos
    while a>0 and qc[a-1]==1 and idx[a]-idx[a-1]==HH:a-=1
    while b+1<len(idx) and qc[b+1]==1 and idx[b+1]-idx[b]==HH:b+=1
    return a,b

def selftest():
    ts=pd.date_range("2015-01-01 00:00",periods=7,freq="30min")
    qc=np.array([0,1,1,1,0,1,0])
    assert full_run(ts,qc,2)==(1,3)
    assert full_run(ts,qc,5)==(5,5)
    v,q,r,why=src_rh_at_site(5,95000,4,2)
    assert why=="PASS" and 0<r<100 and 0<q<.08
    assert src_rh_at_site(5,95000,4,200)[-1]=="HOLD_ERA_RH_T_PHYSICS"
    assert len(EXISTING_PROTECTED)==5
    print("STAGE13R SELF-TEST PASS | original QC1 full-run bounds, true QC0 source, no edits",flush=True)

def verified():
    rec=json.loads(must(Q/QREC).read_text())
    need(rec.get("version")=="batch03-stage13q-v1-20261026-Me6-33-original-ERA-RH-episodes-readonly" and
         rec.get("site")=="US-Me6" and
         rec.get("33_source_original_native_provenance_cases_reviewed")==33 and
         rec.get("total_episodic_group_count")==31 and
         rec.get("science_preview_groups_PASS")==0 and
         rec.get("model_or_forcing_written") is False,
         "Previous actual Stage13q signed 33 physical PASS / 31 continuity HOLD missing")
    files=rec.get("output_SHA256",{})
    need(files.get(QCENTERS)==digest(Q/QCENTERS) and
         files.get(QGROUPS)==digest(Q/QGROUPS),
         "Stage13q report two source ledgers missing or changed")
    for name,s in files.items():
        need("/" not in name and "\\" not in name and digest(Q/name)==s,
             "Stage13q readonly source output mutated "+str(name))
    ac=json.loads(must(AC/ACREC).read_text())
    need(ac.get("version")=="batch03-stage12ac-v1-20261025-operator-approved-five-HH-ERA-RH" and
         ac.get("output_SHA256",{}).get(ACCSV)==digest(AC/ACCSV) and
         rec.get("original_Stage12ac_approved_source_SHA256")==digest(AC/ACCSV),
         "Approved original Stage12ac 2017 five times not preserved")
    manifest=json.loads(must(S07/"exact_input_manifest.json").read_text())
    sites=[x for x in manifest["sites"] if x.get("site")=="US-Me6"]
    need(len(sites)==1 and sites[0].get("native_minutes")==30,
         "Original source-native time cadence missing")
    pins={str(Path(p).resolve()):v for p,v in manifest["input_sha256"].items()}
    original=sites[0]
    for key,which in (("primary","original_published_primary_tower_SHA256"),
                      ("era","original_published_companion_ERA_SHA256")):
        p=must(original[key])
        need(digest(p)==pins.get(str(p.resolve())) and digest(p)==rec.get(which),
             "Signed original tower / paired ERA source changed "+key)
    centers=pd.read_csv(must(Q/QCENTERS),dtype={"native_key":str},low_memory=False)
    groups=pd.read_csv(must(Q/QGROUPS),low_memory=False)
    need(len(centers)==33 and centers.native_key.is_unique and
         centers.individual_source_qc_thermo_pass.astype(bool).all() and
         len(groups)==31 and not groups.source_science_could_be_applied_as_whole_group.astype(bool).any(),
         "Source 33 original-QC1 centers or 31 actual continuity HOLDs altered")
    return original,centers,ac,rec

def audit():
    spec,centers,acrec,qrec=verified()
    # We examine all source-native rows only for implicated 2015 / 2017
    # years. Original full-file raw SHA was verified above.
    want_centers={pd.to_datetime(k,format="%Y%m%d%H%M") for k in centers.native_key}
    years=sorted({t.year for t in want_centers})
    rawcols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    ERAcols=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
    tower=pd.read_csv(must(spec["primary"]),usecols=rawcols,
                      dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(must(spec["era"]),usecols=ERAcols,
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    tower=tower.loc[tower.TIMESTAMP_START.str[:4].isin([str(x) for x in years])].copy()
    era=era.loc[era.TIMESTAMP_START.str[:4].isin([str(x) for x in years])].copy()
    need(len(tower)>5000 and len(era)>5000 and
         tower.TIMESTAMP_START.is_unique and era.TIMESTAMP_START.is_unique,
         "Original site source 2015/2017 years incomplete")
    src=tower.merge(era,on="TIMESTAMP_START",validate="one_to_one")
    idx=pd.DatetimeIndex(source_times(src.TIMESTAMP_START),name="native_time")
    need(idx.is_unique and idx.is_monotonic_increasing and
         idx.equals(pd.DatetimeIndex(source_times(tower.TIMESTAMP_START))),
         "Original site native tower and paired ERA time coverage differs")
    src.index=idx
    for col in rawcols[1:]+ERAcols[1:]:
        src[col]=pd.to_numeric(src[col],errors="coerce")
        src.loc[src[col]<=-9990,col]=np.nan
    original=pd.read_csv(must(AC/ACCSV),dtype={"time":str},low_memory=False)
    forcekey=original.time.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
    fid=pd.DatetimeIndex(source_times(forcekey),name="native_time")
    need(len(original)>100000 and fid.is_unique and fid.is_monotonic_increasing,
         "Original Stage12ac site NOLEAP model time not valid")
    original.index=fid
    need(want_centers.issubset(set(src.index)) and want_centers.issubset(set(original.index)),
         "Some exact original 33 source native center times missing")
    qc=src.VPD_F_QC.to_numpy(float)
    candidates={}
    for t in sorted(want_centers):
        position=src.index.get_loc(t)
        a,b=full_run(src.index,qc,position)
        tag=(src.index[a],src.index[b])
        candidates.setdefault(tag,set()).add(t)
    need(sum(len(x) for x in candidates.values())==33 and len(candidates)<=31,
         "Original source native full QC1 run grouping overlap or centers missing")
    summaries=[]
    detail=[]
    for i,((start,end),specific) in enumerate(sorted(candidates.items()),1):
        a=src.index.get_loc(start);b=src.index.get_loc(end)
        left=src.index[a-1] if a>0 and src.index[a]-src.index[a-1]==HH else None
        right=src.index[b+1] if b+1<len(src) and src.index[b+1]-src.index[b]==HH else None
        record_count=b-a+1
        original_before_QC=float(src.at[left,"VPD_F_QC"]) if left is not None else np.nan
        original_after_QC=float(src.at[right,"VPD_F_QC"]) if right is not None else np.nan
        targets=src.index[a:b+1]
        new_source_times=set(targets).difference(want_centers)
        protected_2017=set(targets).intersection(EXISTING_PROTECTED)
        reasons=[]
        if left is None or right is None:
            reasons.append("MISSING_30MIN_SOURCE_BOUNDARY")
        if not (original_before_QC==0 and original_after_QC==0):
            reasons.append("BOTH_ENDPOINTS_NOT_MEASURED_VPD_QC0")
        if record_count>MAX_PREVIEW_HH:
            reasons.append("LARGE_QC1_RUN_MANUAL_SOURCE_SCOPE_AND_EXTERNAL_REANALYSIS_REQUIRED")
        if protected_2017:
            reasons.append("OVERLAPS_ALREADY_APPROVED_STAGE12AC_FIVE_2017_JULY_SOURCE_TIMES")
        actual_vpd=[]
        all_physics=True
        measured_t_count=0
        preview_end=min(b,a+MAX_PREVIEW_HH-1)
        for ts in src.index[a:preview_end+1]:
            siteT=float(original.at[ts,"TA_USE"])
            pressure=float(original.at[ts,"PSRF"])
            old=float(original.at[ts,"VPD_USE"])
            sc=src.loc[ts]
            v,q,rh,phys=src_rh_at_site(
                siteT,pressure,float(sc.TA_ERA),float(sc.VPD_ERA))
            t_measured=(float(sc.TA_F_QC)==0 and
                        np.isfinite(sc.TA_F) and
                        np.isclose(float(sc.TA_F),siteT,rtol=0,atol=1e-7))
            measured_t_count+=int(t_measured)
            all_physics=all_physics and phys=="PASS" and t_measured
            if ts in EXISTING_PROTECTED:
                candidate_v=old
                selection="PRESERVE_ALREADY_APPROVED_STAGE12AC"
            else:
                candidate_v=v
                selection=("PREVIOUS_33_METHOD_APPROVED_CENTER" if ts in want_centers
                          else "NEW_UNAPPROVED_QC1_NEIGHBOR_HYPOTHETICAL")
            actual_vpd.append(float(candidate_v))
            detail.append({
               "full_run":i,"native_time":str(ts),
               "original_source_VPD_QC":float(sc.VPD_F_QC),
               "original_source_TA_QC":float(sc.TA_F_QC),
               "original_tower_TA_C":float(sc.TA_F),
               "original_tower_VPD_hPa":float(sc.VPD_F),
               "original_site_TA_USE_C":siteT,
               "original_site_PSRF_Pa":pressure,
               "selected_before_VPD_hPa":old,
               "original_paired_ERA_T_C":float(sc.TA_ERA),
               "original_paired_ERA_VPD_hPa":float(sc.VPD_ERA),
               "ERA_RH_pct":rh,"hypothetical_at_site_T_VPD_hPa":v,
               "hypothetical_at_site_T_QBOT_kgkg":q,
               "original_source_T_measurement_QC0":bool(t_measured),
               "paired_ERA_RH_site_thermodynamics":phys,
               "preview_VPD_hPa_with_protected_Stage12ac":candidate_v,
               "operator_status":selection,
               "extra_neighbor_requires_explicit_approval":bool(
                   ts not in want_centers and ts not in EXISTING_PROTECTED)
            })
        if measured_t_count<min(record_count,MAX_PREVIEW_HH):
            reasons.append("SOURCE_T_ORIGINAL_MEASURED_QC0_NOT_VERIFIED_FOR_WHOLE_RUN")
        if not all_physics:
            reasons.append("SOME_ORIGINAL_T_OR_ERA_RH_QBOT_PHYSICS_HOLD")
        maxjump=np.nan
        if record_count<=MAX_PREVIEW_HH and left is not None and right is not None:
            full=[float(original.at[left,"VPD_USE"]),
                  *actual_vpd,float(original.at[right,"VPD_USE"])]
            delta=np.abs(np.diff(np.asarray(full,dtype=float)))
            if np.isfinite(delta).all():
                maxjump=float(np.max(delta))
                if maxjump>MAX_STEP:
                    reasons.append("FULL_QC1_ERA_RH_INTERVAL_STILL_HAS_GT4HPA_VPD_TRANSITION")
            else:
                reasons.append("FULL_QC1_ERA_RH_INTERVAL_HAS_MISSING_SELECTED_BOUNDARY")
        if left is not None and original_before_QC==0:
            if not np.isclose(float(src.at[left,"VPD_F"]),float(original.at[left,"VPD_USE"]),
                              atol=1e-7,rtol=0):
                reasons.append("LEFT_MEASURED_SOURCE_QC0_NOT_RETAINED_IN_STAGE12AC")
        if right is not None and original_after_QC==0:
            if not np.isclose(float(src.at[right,"VPD_F"]),float(original.at[right,"VPD_USE"]),
                              atol=1e-7,rtol=0):
                reasons.append("RIGHT_MEASURED_SOURCE_QC0_NOT_RETAINED_IN_STAGE12AC")
        summaries.append({
            "source_full_run_id":i,
            "source_original_QC1_start":str(start),
            "source_original_QC1_end":str(end),
            "original_QC1_halfhour_count":record_count,
            "previously_method_approved_source_centers":len(specific),
            "new_source_QC1_neighbors_requiring_new_operator_authorization":
                len(new_source_times.difference(EXISTING_PROTECTED)),
            "all_new_source_QC1_neighbor_start_end_only_after_science_check":True,
            "previously_approved_stage12ac_2017_times_inside":
                len(protected_2017),
            "left_measured_original_source_QC0":bool(original_before_QC==0),
            "right_measured_original_source_QC0":bool(original_after_QC==0),
            "left_boundary_native_time":str(left) if left is not None else None,
            "right_boundary_native_time":str(right) if right is not None else None,
            "max_30min_VPD_step_hPa_ERA_RH_full_run_preview":maxjump,
            "original_T_QC0_and_ERA_RH_physics_checked_preview_HH":min(record_count,MAX_PREVIEW_HH),
            "full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview":
                not reasons,
            "HOLD_reasons":";".join(reasons) if reasons else "NONE",
            "operator_extra_QC1_neighbors_approved":False,
            "model_forcing_written":False
        })
    summary=pd.DataFrame(summaries)
    rows=pd.DataFrame(detail)
    need(len(summary)==len(candidates) and
         summary.previously_method_approved_source_centers.sum()==33 and
         all(t in src.index and t in original.index for t in want_centers),
         "Full Q1 source runs did not cover exact 33 source held centers")
    print("\nSTAGE13R ME6 SOURCE FULL ORIGINAL QC1 CONTIGUOUS RUNS",flush=True)
    print(summary[[
       "source_full_run_id","source_original_QC1_start","source_original_QC1_end",
       "original_QC1_halfhour_count","previously_method_approved_source_centers",
       "new_source_QC1_neighbors_requiring_new_operator_authorization",
       "left_measured_original_source_QC0","right_measured_original_source_QC0",
       "max_30min_VPD_step_hPa_ERA_RH_full_run_preview",
       "full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview",
       "HOLD_reasons"]].to_string(index=False),flush=True)
    aggregated={
       "original_policy_approved_33_centers":33,
       "distinct_full_original_source_VPD_QC1_runs":len(summary),
       "new_QC1_neighbors_requiring_fresh_operator_authorization":
           int(summary.new_source_QC1_neighbors_requiring_new_operator_authorization.sum()),
       "source_full_QC1_runs_with_measured_QC0_both_ends":
           int((summary.left_measured_original_source_QC0&
                summary.right_measured_original_source_QC0).sum()),
       "source_full_runs_passing_synthetic_full_run_RH_QBOT_VPD_preview":
           int(summary.full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview.sum()),
       "full_source_run_overlaps_existing_stage12ac_approved_times":
           int(summary.previously_approved_stage12ac_2017_times_inside.sum()),
       "original_model_forcing_written":False,
       "extra_QC1_operator_decision_needed":True,
       "model_DATM_AD400_Slurm_authorized":False
    }
    print("STAGE13R READONLY SCIENCE STATUS",json.dumps(aggregated,indent=2),flush=True)
    return summary,rows,aggregated,spec,qrec

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):mode.add_argument("--"+x,action="store_true")
    a=p.parse_args()
    print("STAGE13R ME6 FULL ORIGINAL QC1 EPISODE SOURCE SCIENCE | "+VER,flush=True)
    selftest()
    if a.self_test:return
    summary,detail,aggregation,spec,previous=audit()
    if a.check:
        print("STAGE13R READONLY CHECK PASS | no source/forcing writes; source group scientific HOLDs retained",flush=True)
        return
    folder=ROOT/"reports"/("stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    a="US-Me6_source_original_full_QC1_runs_grouped_OPERATOR_APPROVAL_NEEDED.csv"
    b="US-Me6_each_QC1_fullrun_ERA_RH_T_QBOT_source_native_preview_READONLY.csv"
    c="stage13r_summary_all_33_original_hold_centers.json"
    d="READONLY_OPERATOR_NEW_SCOPE_APPROVAL_REQUIRED"
    summary.to_csv(folder/a,index=False,float_format="%.17g")
    detail.to_csv(folder/b,index=False,float_format="%.17g")
    (folder/c).write_text(json.dumps(aggregation,indent=2)+"\n")
    (folder/d).write_text(
        "Read-only science report. The original 33 US-Me6 center values"
        " have an earlier operator-method approval, but NO surrounding"
        " source QC1 records are newly authorized. Source ERA humidity"
        " is reanalysis, not tower measured RH. Original 2017-07-04"
        " five halfhours already approved in Stage12ac kept unchanged."
        " No source data/forcing/US-Kon/NR1/PFT/model edits.\n")
    receipt={
        "version":VER,"site":"US-Me6",
        "source_original_Stage13q_actual_report_SHA256":digest(Q/QREC),
        "source_original_Stage12ac_approved_forcing_SHA256":digest(AC/ACCSV),
        "source_original_paired_FLUXMET_tower_SHA256":digest(spec["primary"]),
        "source_original_companion_ERA_SHA256":digest(spec["era"]),
        "original_33_source_centers":33,
        "source_full_original_QC1_runs":len(summary),
        "new_operator_authority_granted":False,
        "model_forcing_written":False,"DATM_ready":False,"Slurm_jobs":False,
        "outputs_SHA256":{f:digest(folder/f) for f in (a,b,c,d)}}
    (folder/"stage13r_source_original_QC1_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13R READONLY REPORT DIR:",folder,flush=True)
    print("STAGE13R ORIGINAL QC1 FULL RUN SCIENCE EVIDENCE COMPLETE; NO FORCING/MODEL WRITES",flush=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("STAGE13R STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage13n: read-only scientific explanation of 3 Stage13m US-Mpj VPD HOLDs.

Operator's Stage13m check found candidate source physics PASS 3/3 but every
native +/-30min adjacent VPD jump exceeds 4hPa (left 7.23/7.03/7.28).
The first two have only original QC1 source humidity on both sides. This
program never overrides the approved 3 center values or proposes automatic
expanded source replacement. It tests full original QC0/QC1/QC2 tower and
paired source ERA provenance, plus diagnostics for event-coherent QC1
humidity repairs anchored to unchanged source-native neighbors.

--self-test: synthetic math / control, no file access or writes.
--check: full original SHA-pinned Stage13m science + +/-6h episode
         and source ERA-RH preview, read-only, NO writes.
--run: same audit, one new independently SHA-sealed RESEARCH REPORT ONLY.
No original forcing, Stage07/13m, PFT, DATM, Slurm, model edits.
"""
import argparse,hashlib,importlib.util,json,subprocess,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage13n-v1-20261026-Mpj-original-QC1-VPD-segment-review"
HERE=Path(__file__).resolve().parent
PREVIOUS=HERE/"13m_US_Mpj_3_approved_2014_VPD_two_2018_PRESERVE_source_scoped.py"
PREVIOUS_GIT_BLOB="2eae8663e64739db78ce9dd305ae3aa4b840b06d"
RADIUS_H=6
SOURCE_NATIVE_CADENCE=pd.Timedelta(minutes=30)
CENTER_TIMES=(
 "2014-10-11T02:30:00",
 "2014-10-11T04:30:00",
 "2014-10-21T08:30:00")
SOURCE_LIMIT=8.0 # original Stage07 <=8C source/ERA comparison for RH reconstruction
JUMP_LIMIT=4.0
WINDOW=pd.Timedelta(hours=RADIUS_H)

def must(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing original trusted source or symlink "+str(p))
    return p

def hash_file(path):
    h=hashlib.sha256()
    with must(path).open("rb") as stream:
        for x in iter(lambda:stream.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()

def source_module():
    p=must(PREVIOUS)
    chk=subprocess.run(["git","hash-object",str(p)],capture_output=True,
                        text=True,check=True).stdout.strip()
    if chk!=PREVIOUS_GIT_BLOB:
        raise RuntimeError("Original pinned Stage13m source Git blob changed")
    spec=importlib.util.spec_from_file_location("batch03_stage13m_verified",p)
    if not spec or not spec.loader:
        raise RuntimeError("Stage13m source module unavailable")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.VER!="batch03-stage13m-v1-20261026-three-Mpj-2014-manual-source-gate":
        raise RuntimeError("Unexpected predecessor science version")
    if tuple(x[0] for x in mod.SCOPED)!=CENTER_TIMES or len(mod.PRESERVE)!=2:
        raise RuntimeError("Operator source scope unexpected")
    return mod

def finite(a):
    return bool(np.isfinite(float(a)))

def reason(a):
    return ";".join(a) if a else "NONE"

def selftest():
    assert len(CENTER_TIMES)==3 and len(set(CENTER_TIMES))==3
    assert all(pd.Timestamp(x).minute in (0,30) for x in CENTER_TIMES)
    assert SOURCE_NATIVE_CADENCE==pd.Timedelta(minutes=30)
    assert JUMP_LIMIT==4.0 and SOURCE_LIMIT==8
    x=np.array([5.0,6.0]);v=np.array([2.0,3.0]);p=np.array([94000.,94100.])
    sat=6.112*np.exp(17.67*x/(x+243.5))
    rh=100*(1-v/sat)
    e=(sat-v)*100
    qb=.622*e/(p-.378*e)
    assert np.all((rh>0)&(rh<100)&(qb>0)&(qb<.08))
    # 2014-10-11 original neighbor 8.263 hPa versus approved 1.032049.
    assert abs(8.263-1.032049)>JUMP_LIMIT
    print("STAGE13N SELF-TEST PASS | original QC1 neighborhood, ERA RH and physical source gates, no writes",flush=True)

def contiguous_qc1(idx,qc,ts):
    """Find maximal consecutive original VPD_F_QC=1 interval containing center."""
    if ts not in idx:return {"status":"NO_CENTER"}
    position=idx.get_loc(ts)
    q=np.asarray(qc,dtype=float)
    if float(q[position])!=1:
        return {"status":"ORIGINAL_CENTER_QC_NOT_1","QC":float(q[position])}
    l=position
    r=position
    while l>0 and q[l-1]==1 and idx[l]-idx[l-1]==SOURCE_NATIVE_CADENCE:
        l-=1
    while r+1<len(idx) and q[r+1]==1 and idx[r+1]-idx[r]==SOURCE_NATIVE_CADENCE:
        r+=1
    return {
       "status":"QC1_RUN_VERIFIED",
       "source_start":str(idx[l]),"source_end":str(idx[r]),
       "source_QC1_HH":int(r-l+1),
       "source_QC1_hours":(r-l+1)/2,
       "QC_before_run":float(q[l-1]) if l>0 else None,
       "QC_after_run":float(q[r+1]) if r+1<len(idx) else None,
       "start_time_before_QC1":str(idx[l-1]) if l>0 else None,
       "end_time_after_QC1":str(idx[r+1]) if r+1<len(idx) else None
    }

def parse(approval,prior):
    m=source_module()
    selected,review,protected,summary=m.audit(approval,prior)
    if (len(review)!=3 or int(summary["passed_science_adoptions"])!=0
        or int(summary["held_candidate_events"])!=3 or
        summary["original_2018_low_RH_protected_unchanged"]!=2):
        raise RuntimeError("Predecessor Stage13m actual 0/3 approved source HOLD changed")
    spec=m.signed_sources(prior)
    tower=m.raw(spec["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=m.raw(spec["era"],["TA_ERA","VPD_ERA"])
    if not selected.index.equals(tower.index) or not selected.index.equals(era.index):
        raise RuntimeError("Raw tower, companion ERA and signed Stage07 timestamps mismatch")
    if not ((selected.index.to_series().diff().dropna()==SOURCE_NATIVE_CADENCE) |
            (selected.index.to_series().diff().dropna()==pd.Timedelta(days=1,minutes=30))).all():
        # NOLEAP one-day-plus-half-hour Feb28->Mar01 leap-year jump
        raise RuntimeError("Unexpected source-native NOLEAP missing/duplicate interval")
    return m,selected,review,protected,summary,tower,era,spec

def frame_window(m,selected,tower,era,center):
    ix=pd.date_range(center-WINDOW,center+WINDOW,freq="30min")
    if not ix.isin(selected.index).all():
        raise RuntimeError("Native selected source failed exact full context coverage")
    rows=[]
    for t in ix:
        sourceT=float(tower.at[t,"TA_F"])
        sourceV=float(tower.at[t,"VPD_F"])
        sourceQC=float(tower.at[t,"VPD_F_QC"])
        sourceTQC=float(tower.at[t,"TA_F_QC"])
        pairedT=float(era.at[t,"TA_ERA"])
        pairedV=float(era.at[t,"VPD_ERA"])
        selectedT=float(selected.at[t,"TA_USE"])
        selectedV=float(selected.at[t,"VPD_USE"])
        pressure=float(selected.at[t,"PSRF"])
        satT=float(m.sat(selectedT))
        satPaired=float(m.sat(pairedT)) if finite(pairedT) else float("nan")
        pairedRH=100*(1-pairedV/satPaired)
        preRH=100*(1-sourceV/float(m.sat(sourceT))) if finite(sourceT) and finite(sourceV) else float("nan")
        selectedRH,selectedQ=m.rh_q(selectedT,selectedV,pressure)
        proposedV=satT*(1-pairedRH/100)
        newRH,newQ=m.rh_q(selectedT,proposedV,pressure)
        phys=bool(
           np.isfinite([selectedT,pressure,pairedT,pairedV,pairedRH,
                        proposedV,newRH,newQ]).all() and
           0<pairedRH<100 and 0<newRH<100 and 0<proposedV<satT and
           0<newQ<.08 and 45000<pressure<111000 and
           abs(selectedT-pairedT)<=SOURCE_LIMIT)
        reasons=[]
        if sourceQC!=1:reasons.append("NO_QC1_FOR_HYPOTHETICAL_EXTENSION")
        if not phys:reasons.append("SOURCE_ERA_T_RH_PHYSICS_HOLD")
        if sourceTQC==0 and abs(sourceT-pairedT)>SOURCE_LIMIT:
            reasons.append("MEASURED_QC0_T_SOURCE_CONFLICT")
        rows.append({
          "native_time":t,
          "is_one_of_three_operator_approved_centers":str(t).replace(" ","T") in CENTER_TIMES,
          "is_other_unapproved_native_time":str(t).replace(" ","T") not in CENTER_TIMES,
          "original_tower_TA_C":sourceT,
          "original_tower_TA_F_QC":sourceTQC,
          "original_tower_VPD_hPa":sourceV,
          "original_tower_VPD_F_QC":sourceQC,
          "original_tower_RH_pct":preRH,
          "companion_ERA_T_C":pairedT,
          "companion_ERA_VPD_hPa":pairedV,
          "companion_ERA_RH_pct":pairedRH,
          "retained_Stage07_T_C":selectedT,
          "retained_Stage07_VPD_hPa":selectedV,
          "retained_Stage07_RH_pct":selectedRH,
          "retained_Stage07_QBOT_kgkg":float(selected.at[t,"QBOT"]),
          "ERA_RH_transferred_at_towerT_HYPOTHETICAL_VPD_hPa":proposedV,
          "ERA_RH_transferred_HYPOTHETICAL_RH_pct":newRH,
          "ERA_RH_transferred_HYPOTHETICAL_QBOT_kgkg":newQ,
          "tower_minus_ERA_T_C":sourceT-pairedT,
          "source_original_VPD_minus_ERA_RH_candidate_hPa":sourceV-proposedV,
          "QC1_and_source_science_meets_basic_preview":sourceQC==1 and phys,
          "is_original_observation_QC0_for_humidity":sourceQC==0,
          "hypothetical_replacement_NOT_OPERATOR_APPROVED":True,
          "not_approved_reasons":reason(reasons)
        })
    data=pd.DataFrame(rows).set_index("native_time")
    if len(data)!=25 or not data.index.is_unique:
        raise RuntimeError("Expected exactly 25 source-native half-hours per center +/-6h")
    datanative=data.index
    # Compact but compare whole episode if desired.
    oldV=data.retained_Stage07_VPD_hPa.to_numpy(float)
    newV=data.ERA_RH_transferred_at_towerT_HYPOTHETICAL_VPD_hPa.to_numpy(float)
    data["selected_Stage07_prev_jump_hPa"]=np.r_[np.nan,np.abs(np.diff(oldV))]
    data["hypothetical_all_ERA_RH_prev_jump_hPa"]=np.r_[np.nan,np.abs(np.diff(newV))]
    return data

def closest_qc0(tower,ts,kind):
    if kind=="VPD":
        selected=tower.index[tower.VPD_F_QC.eq(0)]
    elif kind=="TA+VPD":
        selected=tower.index[tower.VPD_F_QC.eq(0)&tower.TA_F_QC.eq(0)]
    else:raise RuntimeError("Unknown source QC0 type")
    before=selected[selected<ts]
    after=selected[selected>ts]
    a=before[-1] if len(before) else None
    b=after[0] if len(after) else None
    return {"before":str(a) if a is not None else None,
            "after":str(b) if b is not None else None,
            "hours_before":float((ts-a).total_seconds()/3600) if a is not None else None,
            "hours_after":float((b-ts).total_seconds()/3600) if b is not None else None}

def candidate_episode(data,center):
    """Diagnostic-only minimal QC1 ERA-RH episode search, bounded +/-6h.

    Only candidate rows that are original VPD QC1 and pass source T/RH
    physics can ever be imagined as rewritten. All outside original Stage07
    rows remain as-is. The scan is strictly *hypothetical*, not permission.
    A SOURCE QC0 boundary must remain fixed, no adjacent edit to other events.
    For every interval require <=4hPa jumps throughout and at both edges.
    Choose fewest newly proposed noncenter source edits first.
    """
    ix=data.index
    loc=ix.get_loc(center)
    base=data.retained_Stage07_VPD_hPa.to_numpy(float)
    hypot=data.ERA_RH_transferred_at_towerT_HYPOTHETICAL_VPD_hPa.to_numpy(float)
    eligible=data.QC1_and_source_science_meets_basic_preview.to_numpy(bool)
    if not eligible[loc]:
        return {"status":"HOLD_CENTER_ERA_RH_BASIC_SCIENCE_FAIL","center":str(center)}
    candidates=[]
    for first in range(1,loc+1):
        for last in range(loc,len(ix)-1):
            if not eligible[first:last+1].all():continue
            if any(data.is_one_of_three_operator_approved_centers.iloc[i]
                   for i in range(first,last+1) if i!=loc):
                # Do not conflate two separately approved centers, both may
                # be jointly reviewed at operator's explicit request later.
                continue
            vals=base.copy()
            vals[first:last+1]=hypot[first:last+1]
            inside=np.abs(np.diff(vals[first-1:last+2]))
            if not np.isfinite(inside).all() or not (inside<=JUMP_LIMIT).all():continue
            proposed_time=ix[first:last+1]
            candidates.append({
               "status":"DIAGNOSTIC_ONLY_DO_NOT_APPLY",
               "start_native_time":str(ix[first]),
               "end_native_time":str(ix[last]),
               "source_QC1_records_in_candidate":last-first+1,
               "other_source_records_beyond_operator_approved_center":last-first,
               "max_result_VPD_step_hPa":float(inside.max()),
               "source_QC0_VPD_inside_candidate":int(
                    data.original_tower_VPD_F_QC.iloc[first:last+1].eq(0).sum()),
               "operator_approved_for_whole_segment":False,
               "candidate_source_times":[str(x) for x in proposed_time]
            })
    if not candidates:
        return {"status":"HOLD_NO_BOUNDED_QC1_ERA_RH_CONNECTED_EPISODE_WITHIN_6H",
                "center":str(center),
                "next":"review true measured QC0 source anchors, additional gridded source and full QC1 segment; no expansion authorized"}
    candidates.sort(key=lambda x:(x["other_source_records_beyond_operator_approved_center"],
                                  x["max_result_VPD_step_hPa"]))
    return candidates[0]

def run_audit(approval,prior):
    m,selected,review,protected,summary,tower,era,spec=parse(approval,prior)
    rows=[]
    findings=[]
    for center_str in CENTER_TIMES:
        center=pd.Timestamp(center_str)
        frame=frame_window(m,selected,tower,era,center)
        frame.insert(0,"approved_center_native_time",center_str)
        rows.append(frame.reset_index())
        observed=contiguous_qc1(tower.index,tower.VPD_F_QC.to_numpy(float),center)
        scen=candidate_episode(frame,center)
        if scen.get("status")=="DIAGNOSTIC_ONLY_DO_NOT_APPLY":
            # Endpoints of broadened candidate remain unapproved:
            assert scen["operator_approved_for_whole_segment"] is False
        origin=review.loc[review.native_time.eq(center_str)].iloc[0].to_dict()
        prev=frame.loc[center-SOURCE_NATIVE_CADENCE]
        next_=frame.loc[center+SOURCE_NATIVE_CADENCE]
        findings.append({
          "center":center_str,
          "original_stage13m_adoption":bool(origin["conditional_OPERATOR_ADOPTION"]),
          "center_tower_VPD_QC":int(tower.at[center,"VPD_F_QC"]),
          "before_tower_VPD_QC":int(tower.at[center-SOURCE_NATIVE_CADENCE,"VPD_F_QC"]),
          "after_tower_VPD_QC":int(tower.at[center+SOURCE_NATIVE_CADENCE,"VPD_F_QC"]),
          "center_stage07_VPD":float(selected.at[center,"VPD_USE"]),
          "left_Stage07_30min_jump":float(origin["edge_left_jump_hPa"]),
          "right_Stage07_30min_jump":float(origin["edge_right_jump_hPa"]),
          "stage13m_hold_reason":str(origin["HOLD_reason"]),
          "original_source_QC1_contiguous_run":observed,
          "nearest_source_QC0_VPD":closest_qc0(tower,center,"VPD"),
          "nearest_source_QC0_T_AND_VPD":closest_qc0(tower,center,"TA+VPD"),
          "local_6h_QC1_count":int(frame.original_tower_VPD_F_QC.eq(1).sum()),
          "local_6h_QC0_count":int(frame.original_tower_VPD_F_QC.eq(0).sum()),
          "local_6h_QC2_count":int(frame.original_tower_VPD_F_QC.eq(2).sum()),
          "source_QC1_and_ERA_RH_valid_preview_count":int(
              frame.QC1_and_source_science_meets_basic_preview.sum()),
          "original_tower_RH_lt0_count_in_6h":int(
              frame.original_tower_RH_pct.lt(0).sum()),
          "original_tower_RH_lt1_count_in_6h":int(
              frame.original_tower_RH_pct.lt(1).sum()),
          "hypothetical_bounded_ERA_RH_QC1_episode":scen,
          "science_disposition":"HOLD_PENDING_OPERATOR_EPISODE_SCOPE_NOT_CURRENTLY_APPROVED"
        })
    report=pd.concat(rows,ignore_index=True)
    if len(report)!=75 or len(findings)!=3:
        raise RuntimeError("Three complete 25-HH source context sets required")
    report["native_time"]=report.native_time.astype(str)
    return m,report,findings,summary,spec

def main():
    ap=argparse.ArgumentParser()
    opts=ap.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):
        opts.add_argument("--"+x,action="store_true")
    ap.add_argument("--approval",type=Path)
    ap.add_argument("--prior-qc0-approval",type=Path)
    a=ap.parse_args()
    print("STAGE13N MPJ THREE CENTERS + SOURCE QC1 VPD EPISODES | "+VERSION,flush=True)
    selftest()
    if a.self_test:return
    if a.approval is None or a.prior_qc0_approval is None:
        ap.error("Require original --approval Stage13m JSON and --prior-qc0-approval Stage13d JSON")
    m,table,events,status,spec=run_audit(a.approval,a.prior_qc0_approval)
    for r in events:
        print("\n=== SOURCE EPISODE "+r["center"]+" ===",flush=True)
        for key in ("before_tower_VPD_QC","center_tower_VPD_QC","after_tower_VPD_QC",
                    "left_Stage07_30min_jump","right_Stage07_30min_jump",
                    "local_6h_QC1_count","local_6h_QC0_count","local_6h_QC2_count",
                    "original_tower_RH_lt0_count_in_6h","original_tower_RH_lt1_count_in_6h",
                    "source_QC1_and_ERA_RH_valid_preview_count"):
            print(key,r[key],flush=True)
        print("FULL ORIGINAL CONTIGUOUS QC1",json.dumps(
              r["original_source_QC1_contiguous_run"],default=str),flush=True)
        print("NEAREST ACTUAL SOURCE QC0 VPD",json.dumps(
              r["nearest_source_QC0_VPD"],default=str),flush=True)
        print("ERA-RH HYPOTHETICAL MINIMAL BOUNDED EPISODE",
              json.dumps(r["hypothetical_bounded_ERA_RH_QC1_episode"],default=str),flush=True)
        subset=table.loc[table.approved_center_native_time.eq(r["center"])]
        print("\nORIGINAL +/-3h CONTEXT, SOURCE QC & ERA-RH PREVIEW",flush=True)
        near=subset.loc[(pd.to_datetime(subset.native_time) >=pd.Timestamp(r["center"])-pd.Timedelta(hours=3))&
                        (pd.to_datetime(subset.native_time) <=pd.Timestamp(r["center"])+pd.Timedelta(hours=3))]
        print(near[["native_time","original_tower_TA_C","original_tower_VPD_hPa",
                    "original_tower_VPD_F_QC","original_tower_RH_pct",
                    "companion_ERA_RH_pct","retained_Stage07_VPD_hPa",
                    "ERA_RH_transferred_at_towerT_HYPOTHETICAL_VPD_hPa",
                    "QC1_and_source_science_meets_basic_preview"]].to_string(
                    index=False,float_format=lambda x:f"{x:.4f}"),flush=True)
    print("\nSTAGE13N HUMAN DECISION NEEDED: three centers held, 2018 preserved, source QC1 unapproved beyond 3 centers",flush=True)
    if a.check:
        print("STAGE13N READONLY CHECK PASS | zero source / forcing / case writes",flush=True)
        return
    dest=m.ROOT/"reports"/("stage13n_Mpj_original_QC1_ERA_RH_episode_READONLY_"+
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    f1="THREE_original_native_VPD_centers_6h_source_QC_and_ERA_RH.csv"
    f2="THREE_source_original_QC1_full_run_and_unapproved_ERA_RH_episodes.json"
    f3="stage13m_original_holds_summary.json"
    table.to_csv(dest/f1,index=False)
    (dest/f2).write_text(json.dumps(events,indent=2)+"\n")
    (dest/f3).write_text(json.dumps(status,indent=2)+"\n")
    warning="RESEARCH_ONLY_NO_APPROVAL_BEYOND_THREE_CENTERS"
    (dest/warning).write_text(
        "Signed source audit only. A Stage13n hypothetical bounded ERA-RH"
        " episode is not a source measurement and not operator approved."
        " Do not expand repairs to original QC1 neighbors, alter the two"
        " protected 2018 QC2 points, use Stage11h, promote DATM or submit Slurm.\n")
    inputs={"Stage13m_source_Git_blob":PREVIOUS_GIT_BLOB,
            "operator_stage13m_decision_SHA256":hash_file(a.approval),
            "operator_stage13d_decision_SHA256":hash_file(a.prior_qc0_approval),
            "original_FLUXMET_SHA256":hash_file(spec["primary"]),
            "original_companion_ERA_SHA256":hash_file(spec["era"]),
            "original_selected_Stage07_SHA256":hash_file(m.ORIGINAL)}
    receipt={"version":VERSION,"operator_conditionally_approved_centers":3,
             "science_passed_stage13m":0,"new_forcing_written":False,
             "original_2018_source_preserved":True,
             "model_jobs_submitted":False,
             "input_SHA256":inputs,
             "output_SHA256":{x:hash_file(dest/x) for x in [f1,f2,f3,warning]}}
    (dest/"stage13n_READONLY_source_evidence_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13N READONLY EVIDENCE REPORT",dest,flush=True)
    print("NO FORCING REPAIRS. HUMAN APPROVAL REQUIRED FOR ADDITIONAL QC1 TIMES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("STAGE13N STOP:",ex,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

#!/usr/bin/env python3
"""US-Kon Stage14N: exactly THREE original both-QC0-bracketed RH candidates.

Input is ACTUAL SHA-sealed Stage14M original FLUXMET QC0 source evidence
(2026-10-29 06:28 UTC) plus ACTUAL Stage14K least-modified 68-source
research tape. Never reclassify source VPD QC1 as measured QC0.
Three native slots ONLY: 201110230730, 201202251030, 201208050900.
The other six original scientist-protected source HOLDs remain NaN.

Each hypothesis linearly interpolates WATER RH between two genuinely
both-QC0 original tower endpoints (not from independent RH observed at
the target itself), reconstructs VPD/QBOT using unchanged Stage14K site
TA/PSRF, tests both adjacent 30min joins for physical closure and
VPD <=4hPa, water RH <=20pp, QBOT <=0.003kg/kg, and compares ERA-RH
provenance. Any failed target stays original missing. Writes isolated
NOT-APPROVED research trial and human decision tables ONLY. NO writes
to originals or any existing trials, PFT, DATM, CIME, Slurm or AD400.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-Kon-14N-only-3-true-QC0-RH-bracketed-research-v1-20261029"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
K = ROOT/"science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_20261029T044949Z_ebbfd739"
M = ROOT/"reports/US_Kon_14M_original_QC0_9HOLD_44edges_20261029T062839Z_4d82e789"
KF = "US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv"
KR = "US_Kon_68_9_SHA_receipt.json"
MR = "US_Kon_14M_READONLY_SHA_receipt.json"
MT = "US_Kon_nine_protected_hard_source_original_QC0.csv"
ME = "US_Kon_all_gt10hPa_remaining_source_native_joins.csv"
COLS = ["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
TARGETS = ["201110230730","201202251030","201208050900"]
HARD9 = {"201102220830","201102220900","201102220930","201105261100",
         "201109291830","201110150730","201110230730",
         "201202251030","201208050900"}
MAX_ANCHOR_H = 3.0
MAX_ANCHOR_RH_SPAN = 20.0
MAX_JOIN_VPD = 4.0
MAX_JOIN_RH = 20.0
MAX_JOIN_QBOT = 0.003

def must(ok, message):
    if not bool(ok):
        raise RuntimeError("US-Kon Stage14N FAIL CLOSED (NO INPUT WRITES): "+str(message))

def fpath(path):
    path=Path(path)
    must(path.is_file() and not path.is_symlink(), "missing signed file "+str(path))
    return path

def sha(path):
    digest=hashlib.sha256()
    with fpath(path).open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):
            digest.update(c)
    return digest.hexdigest()

def esw(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*t/(t+243.5))

def esi(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(22.46*t/(t+272.62))

def get_e_rh(t,v):
    saturation=float(esw(t))
    e=saturation-v
    return e,100*e/saturation

def get_q(e,p):
    return 0.622*100*e/(p-0.378*100*e)

def native(times):
    return times.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def test():
    must(len(TARGETS)==3 and len(HARD9)==9 and
         set(TARGETS)<HARD9 and
         abs(float(esw(-20))-float(esi(-20)))>0.1 and
         np.isclose(get_q(8.0,100000),0.005,atol=0.00002),
         "three candidate, nine hard, water/ice and QBOT synthetic test")
    print("US-Kon Stage14N SELF-TEST PASS | THREE TRUE QC0 RH CANDIDATES ONLY",flush=True)

def signed_inputs():
    kr=json.loads(fpath(K/KR).read_text())
    mr=json.loads(fpath(M/MR).read_text())
    must(kr.get("version")=="batch03-US-Kon-68ERA-RH-research-9HOLD-v1-20261029" and
         kr.get("DATM_ready") is False and
         kr.get("postv5_authorized") is False, "Stage14K original science gate or receipt altered")
    must(mr.get("version")=="batch03-Kon-stage14m-QC0-original-source-evidence-v1-20261029" and
         mr.get("science_approved") is False and
         mr.get("model_job_submitted") is False and
         mr.get("source_Stage14K")==sha(K/KF),
         "actual Stage14M observed tower QC0 report ancestry/approval changed")
    for folder,rec,field in ((K,kr,"output_SHA256"),(M,mr,"outputs_SHA256")):
        must(bool(rec.get(field)), "missing signed original SHA list "+str(folder))
        for filename,expected_sha in rec[field].items():
            must(sha(folder/filename)==expected_sha,
                 "source evidence SHA mismatch "+str(folder/filename))
    km=pd.read_csv(fpath(K/KF),dtype={"time":str},low_memory=False)
    holds=pd.read_csv(fpath(M/MT),dtype={"native_key":str,
            "previous_real_both_QC0_key":str,"next_real_both_QC0_key":str},low_memory=False)
    serious=pd.read_csv(fpath(M/ME),dtype={"left_native":str,"right_native":str},low_memory=False)
    must(len(km)==280320 and list(km.columns)==COLS and len(holds)==9 and
         holds.native_key.is_unique and set(holds.native_key)==HARD9 and
         len(serious)==11, "actual Stage14K/M 280320, nine hard source, or 11 severe edge census differs")
    keys=native(km.time)
    timeline=pd.to_datetime(keys,format="%Y%m%d%H%M",errors="raise")
    must(keys.is_unique and timeline.is_monotonic_increasing and
         keys.iat[0]=="200401010000" and keys.iat[-1]=="201912312330" and
         not ((timeline.dt.month==2)&(timeline.dt.day==29)).any(),
         "signed 2004-2019 native NOLEAP source timestamp mismatch")
    missing=set(keys[km.VPD_USE.isna()])
    must(missing==HARD9 and missing==set(keys[km.QBOT.isna()]),
         "nine original paired source held humidity slots changed")
    holds=holds.set_index("native_key")
    pos={key:i for i,key in enumerate(keys)}
    return km,keys,timeline,holds,serious,pos

def row_physics(km,index,v=None,q=None):
    r=km.iloc[index]
    t=float(r.TA_USE);p=float(r.PSRF)
    v=float(r.VPD_USE) if v is None else float(v)
    q=float(r.QBOT) if q is None else float(q)
    if not np.isfinite([t,p,v,q]).all():
        return None
    sw=float(esw(t));e=sw-v
    if not (50000<p<110000 and -70<t<65 and 0<=v<sw and e>0 and 0<q<0.08):
        return None
    qexpected=float(get_q(e,p))
    if not np.isclose(q,qexpected,atol=1e-8,rtol=1e-6):
        return None
    return dict(T_C=t,PSRF_Pa=p,VPD_hPa=v,QBOT_kgkg=q,
        e_hPa=e,RHwater_pct=100*e/sw,RHice_pct=(100*e/float(esi(t)) if t<0 else np.nan))

def candidate_check(km,keys,clock,holds,pos,key):
    i=pos[key]
    obs=holds.loc[key]
    reasons=[]
    must(int(float(obs.original_tower_T_QC))==0 and
         int(float(obs.original_VPD_QC))==1,
         "three shortlisted exact source target QC0-temperature QC1-VPD identity changed "+key)
    prev_key=obs.previous_real_both_QC0_key
    next_key=obs.next_real_both_QC0_key
    must(isinstance(prev_key,str) and isinstance(next_key,str) and
         prev_key in pos and next_key in pos and
         pos[prev_key]<i<pos[next_key],
         "true measured two-side source QC0 observation time no longer brackets "+key)
    t0=clock.iat[pos[prev_key]];t1=clock.iat[pos[next_key]];tc=clock.iat[i]
    hours0=(tc-t0).total_seconds()/3600
    hours1=(t1-tc).total_seconds()/3600
    must(abs(hours0-float(obs.previous_QC0_gap_hours))<1e-8 and
         abs(hours1-float(obs.next_QC0_gap_hours))<1e-8,
         "original measured QC0 anchor temporal evidence altered "+key)
    r0=float(obs.previous_QC0_RH_pct)
    r1=float(obs.next_QC0_RH_pct)
    must(np.isfinite([r0,r1]).all() and 0<=r0<=100 and 0<=r1<=100,
         "original source both-QC0 anchor water RH impossible "+key)
    span_h=hours0+hours1
    weight=hours0/span_h
    rh_interp=r0+(r1-r0)*weight
    t=float(km.TA_USE.iat[i]);p=float(km.PSRF.iat[i])
    e=float(esw(t))*rh_interp/100
    v=float(esw(t))-e
    q=float(get_q(e,p))
    if max(hours0,hours1)>MAX_ANCHOR_H:
        reasons.append("QC0_ANCHOR_DISTANCE_GT3H")
    if abs(r1-r0)>MAX_ANCHOR_RH_SPAN:
        reasons.append("QC0_ANCHOR_RH_DIFFERENCE_GT20PP")
    if abs(float(obs.original_selected_T_C)-float(obs.original_tower_T_C))>0.001:
        reasons.append("SELECTED_T_DIFFERS_FROM_ORIGINAL_T_QC0")
    if abs(float(obs.selected_T_minus_ERA_C))>5:
        reasons.append("TOWER_ERA_T_DIFFERENCE_GT5C")
    # Both half-hour physical contacts must already exist on immutable K.
    joins=[]
    valid=row_physics(km,i,v,q)
    if valid is None:
        reasons.append("INTERPOLATED_SOURCE_WATER_OR_QBOT_INVALID")
    elif np.isfinite(valid["RHice_pct"]) and valid["RHice_pct"]>102:
        reasons.append("ICE_PHASE_SUPERSATURATION_GT102PCT")
    for side,j in (("left",i-1),("right",i+1)):
        item=dict(side=side,neighbor_native=keys.iat[j] if 0<=j<len(km) else None)
        if not (0<=j<len(km)) or abs((clock.iat[max(i,j)]-clock.iat[min(i,j)]).total_seconds()-1800)>1e-6:
            reasons.append(side+"_NATIVE_30MIN_NEIGHBOR_MISSING")
            item["status"]="NO_NATIVE_30MIN";joins.append(item);continue
        neighbor=row_physics(km,j)
        if neighbor is None or valid is None:
            reasons.append(side+"_NEIGHBOR_NOT_PHYSICALLY_COMPLETE")
            item["status"]="UNPHYSICAL_OR_MISSING_ANCHOR";joins.append(item);continue
        delta_v=abs(valid["VPD_hPa"]-neighbor["VPD_hPa"])
        delta_r=abs(valid["RHwater_pct"]-neighbor["RHwater_pct"])
        delta_q=abs(valid["QBOT_kgkg"]-neighbor["QBOT_kgkg"])
        fail=[]
        if delta_v>MAX_JOIN_VPD:fail.append("VPD_GT4")
        if delta_r>MAX_JOIN_RH:fail.append("RH_GT20PP")
        if delta_q>MAX_JOIN_QBOT:fail.append("QBOT_GT0p003")
        item.update(status=("PASS" if not fail else ";".join(fail)),
                    dVPD_hPa=delta_v,dRHwater_pp=delta_r,dQBOT_kgkg=delta_q,
                    original_neighbor_VPD_hPa=neighbor["VPD_hPa"],
                    original_neighbor_RHwater_pct=neighbor["RHwater_pct"])
        if fail:reasons.append(side+"_CONTACT_"+item["status"])
        joins.append(item)
    e_t=float(obs.source_companion_ERA_T_C)
    e_v=float(obs.source_companion_ERA_VPD_hPa)
    era_rh=100*(1-e_v/float(esw(e_t))) if np.isfinite([e_t,e_v]).all() else np.nan
    accepted=len(reasons)==0
    main=dict(native_key=key,source_T_QC=0,source_VPD_QC=1,
              old_humidity_status="NINE_PROTECTED_NAN",
              QC0_prior_native=prev_key,QC0_next_native=next_key,
              hours_prior=hours0,hours_next=hours1,
              measured_QC0_prior_RHwater_pct=r0,measured_QC0_next_RHwater_pct=r1,
              measured_QC0_endpoint_RH_difference_pp=abs(r1-r0),
              interpolated_RHwater_pct=rh_interp,
              ERA_source_RHwater_pct=era_rh,
              interpolation_minus_ERA_RH_pp=rh_interp-era_rh,
              original_tower_T_C=float(obs.original_tower_T_C),
              selected_T_C=t,T_minus_ERA_C=float(obs.selected_T_minus_ERA_C),
              new_30min_VPD_hPa=v,new_30min_QBOT=q,
              phase_ice_RH_pct=float(valid["RHice_pct"]) if valid else np.nan,
              eligible_numerical_research_trial=accepted,
              source_science_independently_validated=False,
              decision="TRIAL_QC0_RH_INTERPOLATION_ONLY" if accepted else "HOLD_SOURCE_QC_OR_BOUNDARY",
              block_reasons=";".join(reasons),
              Postv5_DATM_AD400_approved=False)
    for row in joins:
        row["held_native"]=key
        row["candidate_eligible"]=accepted
    return main,joins

def review():
    km,keys,clock,holds,serious,pos=signed_inputs()
    cases=[];edges=[]
    for key in TARGETS:
        a,b=candidate_check(km,keys,clock,holds,pos,key)
        cases.append(a);edges.extend(b)
    detail=pd.DataFrame(cases)
    boundaries=pd.DataFrame(edges)
    accepted=set(detail.loc[detail.eligible_numerical_research_trial,"native_key"])
    trial=km.copy(deep=True)
    for r in cases:
        if r["native_key"] in accepted:
            i=pos[r["native_key"]]
            trial.at[i,"VPD_USE"]=r["new_30min_VPD_hPa"]
            trial.at[i,"QBOT"]=r["new_30min_QBOT"]
    # Strict in-memory scope, no QC0 sensor data, source T or other input touched.
    for c in COLS:
        if c in ("VPD_USE","QBOT"):
            selector=~keys.isin(accepted)
            must(km.loc[selector,c].reset_index(drop=True).equals(
                 trial.loc[selector,c].reset_index(drop=True)),
                 "selected original non-target source humidity changed "+c)
        else:
            must(km[c].equals(trial[c]),
                 "selected source nonhumidity variable or native clock changed "+c)
    left=set(keys[trial.VPD_USE.isna()])
    must(left==HARD9-accepted and
         left==set(keys[trial.QBOT.isna()]),
         "original nine HOLD missing-set incorrectly released")
    for t in accepted:
        i=pos[t]
        must(row_physics(trial,i) is not None,
             "selected newly inserted QC0-RH estimate T/VPD/QBOT not physical")
    # Other 11 severe source discontinuities remain untouched; do not
    # pretend any of the unmodified original QC1/QC2 is a true RH sensor.
    summary=dict(version=VERSION,site="US-Kon",original_native_halfhours=len(km),
        original_Stage14K_SHA256=sha(K/KF),
        original_Stage14M_QC0_receipt_SHA256=sha(M/MR),
        original_measured_both_QC0_bracketed_candidates=len(TARGETS),
        exact_three_candidates=TARGETS,
        candidate_numerical_contact_PASS=int(detail.eligible_numerical_research_trial.sum()),
        candidate_remaining_HOLD=int(3-detail.eligible_numerical_research_trial.sum()),
        original_hard_science_HOLD=9,
        after_trial_hard_science_HOLD=len(left),
        other_six_protected_HOLD_unchanged=True,
        serious_11_original_QC1_QC2_source_edges_unchanged=True,
        original_Stage14L_not_promoted=True,
        candidate_observational_source_validation=False,
        no_source_or_model_input_overwrites=True,
        DATM_Postv5_AD400_Slurm_approved=False)
    print("\nUS-Kon NINE ORIGINAL QC0/EVIDENCE HOLDS: only 3 numerical candidates",flush=True)
    print(detail.to_string(index=False),flush=True)
    print("\nUS-Kon SIX ADJACENT NATIVE SOURCE CONTACTS:",flush=True)
    print(boundaries.to_string(index=False),flush=True)
    print("\nUS-Kon ONEPASS THREE QC0-RH CANDIDATE SUMMARY:",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("US-Kon STAGE14N THREE CANDIDATE SOURCE ASSESSMENT COMPLETE | OTHER SIX SCIENCE HOLDS PROTECTED | NO INPUT/MODEL WRITES",flush=True)
    return trial,detail,boundaries,serious,summary

def main():
    p=argparse.ArgumentParser()
    modes=p.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","run"):modes.add_argument("--"+m,action="store_true")
    flags=p.parse_args()
    test()
    if flags.self_test:return
    trial,detail,edges,serious,summary=review()
    if flags.check:
        print("US-Kon Stage14N READONLY SOURCE CHECK PASS; no files written",flush=True)
        return
    out=ROOT/"science_trials"/("US_Kon_14N_3_NEARBY_QC0_RH_RESEARCH_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    products={
        "US_Kon_280320_68ERA_plus_selected_QC0_RH_trial_6plus_HOLD_NOT_DATM.csv":trial,
        "US_Kon_original_three_QC0_RH_ERA_candidate_science_gate.csv":detail,
        "US_Kon_three_QC0_RH_six_local_30min_contacts.csv":edges,
        "US_Kon_11_original_gt10hPa_source_QC_events_UNCHANGED.csv":serious
    }
    outputs={}
    for filename,table in products.items():
        table.to_csv(out/filename,index=False,float_format="%.17g")
        outputs[filename]=sha(out/filename)
    output=pd.read_csv(out/list(products)[0])
    must(len(output)==280320 and list(output.columns)==COLS and
         int(output.VPD_USE.isna().sum())==summary["after_trial_hard_science_HOLD"] and
         int(output.QBOT.isna().sum())==summary["after_trial_hard_science_HOLD"],
         "saved trial missing masks/columns differ from numerical decisions")
    (out/"US_Kon_14N_three_holds_source_summary.json").write_text(
        json.dumps(summary,indent=2)+"\n")
    outputs["US_Kon_14N_three_holds_source_summary.json"]=sha(
        out/"US_Kon_14N_three_holds_source_summary.json")
    (out/"RESEARCH_ONLY_NOT_APPROVED_FOR_DATM_AD400").write_text(
        "Only up to 3 original VPD-QC1/TA-QC0 humidity-source NaN times are "
        "tested using timestamp-weighted genuine both-QC0 WATER RH endpoints. "
        "Even a passing estimate is NOT a measured RH at that timestamp. "
        "Other six high-risk source science holds stay NaN, all 68 original "
        "Stage14K ERA-RH routine candidates unchanged, Stage14L 7-neighbour "
        "alternative not promoted, severe 11 QC source discontinuities not "
        "edited. Never submit incomplete source to production DATM/AD400.\n")
    outputs["RESEARCH_ONLY_NOT_APPROVED_FOR_DATM_AD400"]=sha(
        out/"RESEARCH_ONLY_NOT_APPROVED_FOR_DATM_AD400")
    (out/"US_Kon_14N_RESEARCH_SHA_receipt.json").write_text(
        json.dumps(dict(version=VERSION,
            signed_Stage14K_parent=summary["original_Stage14K_SHA256"],
            signed_Stage14M_parent=summary["original_Stage14M_QC0_receipt_SHA256"],
            output_SHA256=outputs,science_approved=False,
            DATM_ready=False,Slurm_submitted=False),indent=2)+"\n")
    print("US-Kon Stage14N INDEPENDENT RESEARCH OUTPUT:",out,flush=True)
    print("US-Kon Stage14N 3 QC0 RH SOURCE TRIALS EVALUATED; EXACT OTHER SIX SCIENCE HOLDS PROTECTED; NO SLURM",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("US-Kon STAGE14N SCIENCE STOP:",error,file=sys.stderr,flush=True)
        raise

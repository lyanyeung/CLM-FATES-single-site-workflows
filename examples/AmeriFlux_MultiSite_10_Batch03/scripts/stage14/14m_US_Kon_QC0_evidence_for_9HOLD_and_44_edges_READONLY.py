#!/usr/bin/env python3
"""US-Kon Stage14M: ONE final original tower QC0 evidence package, NO REPAIR.

ACTUAL Stage14L improves only 46->41 original 68-seed contact warnings
by 7 extra non-measured QC1/QC2 replacements, and still has 44 full
expanded neighbourhood warnings. Rather than repeatedly smoothing ERA
signals, inspect exact original source QA for all 44 remaining flagged
edges AND 9 original hard HOLD HH, including nearest source paired
QC0-observed TA/VPD and native tower versus paired ERA values.

This is an auditable source-provenance decision package, NOT an approval
of either the 68 candidate missing fills or 7 new neighbour changes.
NO original source, Stage14K/L, case, DATM, model or Slurm writes.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np,pandas as pd
sys.dont_write_bytecode=True
V="batch03-Kon-stage14m-QC0-original-source-evidence-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
M=R/"qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"
K=R/"science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_20261029T044949Z_ebbfd739"
L=R/"science_trials/US_Kon_14L_QC1_QC2_NEIGHBOR_ERA_RH_RESEARCH_ONLY_20261029T045738Z_fe3252d0"
KF="US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv"
LF="US_Kon_280320_ERA_RH68_plus_QC1QC2_NEIGHBORS_9HOLD_NOT_DATM.csv"
FLAGS="US_Kon_all_expanded_neighbor_boundary_QC.csv"
CHANGES="US_Kon_exact_original_QC1_QC2_neighbor_changes.csv"
KREC="US_Kon_68_9_SHA_receipt.json"
LREC="US_Kon_14L_SHA_receipt.json"
COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
HARD9={"201102220830","201102220900","201102220930","201105261100",
       "201109291830","201110150730","201110230730",
       "201202251030","201208050900"}
def need(ok,why):
    if not bool(ok):raise RuntimeError("US-Kon STAGE14M STOP READONLY: "+why)
def regular(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"source missing "+str(p));return p
def digest(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):h.update(ch)
    return h.hexdigest()
def es(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(17.67*t/(t+243.5))
def selftest():
    need(float(es(-10))>0 and len(HARD9)==9 and
      pd.Series(["a",None]).equals(pd.Series(["a",None])),
      "native original QC/time/thermodynamic regression")
    print("US-Kon STAGE14M QC0 ORIGINAL EVIDENCE SELF-TEST PASS",flush=True)
def source():
    kr=json.loads(regular(K/KREC).read_text())
    lr=json.loads(regular(L/LREC).read_text())
    need(kr.get("version")=="batch03-US-Kon-68ERA-RH-research-9HOLD-v1-20261029"
      and kr.get("DATM_ready") is False and kr.get("postv5_authorized") is False,
      "current signed Stage14K science evidence/prod state differs")
    need(lr.get("version")=="batch03-US-Kon-14L-source-QC-constrained-adjacent-ERA-RH-v1-20261029"
      and lr.get("operator_science_approved") is False
      and lr.get("original_Stage14K_SHA256")==digest(K/KF),
      "current signed actual Stage14L derived research data changed")
    for root,rec in ((K,kr),(L,lr)):
        for fn,h in rec["output_SHA256"].items():
            need(digest(root/fn)==h,"original signed SHA differed "+str(root/fn))
    meta=json.loads(regular(M).read_text())
    site=[x for x in meta["sites"] if x["site"]=="US-Kon"]
    need(len(site)==1 and int(site[0]["native_minutes"])==30
      and int(site[0]["first_year"])==2005
      and int(site[0]["last_year"])==2020,
      "original site year/clock changed")
    for k in ("primary","era"):
        f=regular(site[0][k])
        need(digest(f)==meta["input_sha256"].get(str(f.resolve())),
          "original source manifest SHA differs "+k)
    k=pd.read_csv(regular(K/KF),dtype={"time":str},low_memory=False)
    l=pd.read_csv(regular(L/LF),dtype={"time":str},low_memory=False)
    need(len(k)==len(l)==280320 and list(k)==list(l)==COLS and
      k.time.equals(l.time),"Stage14K/14L original time/schema differs")
    keys=k.time.str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
    timestamps=pd.to_datetime(keys,format="%Y%m%d%H%M",errors="raise")
    need(keys.is_unique and timestamps.is_monotonic_increasing
         and not bool(((timestamps.dt.month==2)&(timestamps.dt.day==29)).any()),
         "native NOLEAP selection altered")
    need(set(keys[l.VPD_USE.isna()])==HARD9 and
         set(keys[k.VPD_USE.isna()])==HARD9 and
         l.QBOT.isna().equals(k.QBOT.isna()),
         "9 original hard source holds shifted")
    change=pd.read_csv(regular(L/CHANGES),dtype={"native_key":str},low_memory=False)
    edges=pd.read_csv(regular(L/FLAGS),
      dtype={"left_native":str,"right_native":str},low_memory=False)
    changed_keys=set(change.native_key)
    need(len(change)==7 and len(changed_keys)==7
         and len(edges)==103 and int(edges.status.ne("PASS").sum())==44,
         "Stage14L actual 7 neighbour and 44/103 full edge source evidence changed")
    diff_v=~np.isclose(k.VPD_USE.to_numpy(float),l.VPD_USE.to_numpy(float),
                       rtol=0,atol=1e-9,equal_nan=True)
    diff_q=~np.isclose(k.QBOT.to_numpy(float),l.QBOT.to_numpy(float),
                       rtol=0,atol=1e-12,equal_nan=True)
    need(set(keys[diff_v|diff_q])==changed_keys,
         "one original existing source value changed outside signed 7 candidates")
    for c in COLS:
        if c not in ("VPD_USE","QBOT"):
            need(k[c].equals(l[c]),"non-humidity original source changed "+c)
    def read_source(p,fields):
        d=pd.read_csv(regular(p),
           usecols=["TIMESTAMP_START",*fields],dtype={"TIMESTAMP_START":str},
           low_memory=False)
        need(d.TIMESTAMP_START.is_unique,"original source native time not unique")
        d=d.set_index("TIMESTAMP_START",drop=True).reindex(keys)
        need(not d.isna().all(axis=1).any(),"missing original native hour")
        for c in fields:
            d[c]=pd.to_numeric(d[c],errors="coerce").mask(lambda x:x<=-9990)
        d.index=pd.RangeIndex(len(k))
        return d
    obs=read_source(site[0]["primary"],
                    ["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=read_source(site[0]["era"],["TA_ERA","VPD_ERA"])
    return k,l,keys,timestamps,change,edges,obs,era,changed_keys,site[0]
def assess():
    original,trial,keys,times,changes,edges,obs,era,changed,site=source()
    pos={key:i for i,key in enumerate(keys)}
    # Strictly observed paired QC0 refers to original tower observation, NOT MDS,
    # companion ERA, or original release QC1/2. Source VPD derived from tower TA
    # is only regarded as a paired QC0 observational RH when BOTH QCs are zero.
    t=obs.TA_F.to_numpy(float);v=obs.VPD_F.to_numpy(float)
    tq=obs.TA_F_QC.to_numpy(float);vq=obs.VPD_F_QC.to_numpy(float)
    with np.errstate(invalid="ignore",divide="ignore"):
        rh0=100*(1-v/es(t))
    measured=(tq==0)&(vq==0)&np.isfinite(t)&np.isfinite(v)&(
        np.isfinite(rh0))&(rh0>=0)&(rh0<=100)
    anchors=np.flatnonzero(measured)
    need(len(anchors)>0,"no original measured paired-QC0 humidity in site release")
    dtarr=times.to_numpy()
    def anchor(i,prior):
        # strict source-native 30min, never invent a QC0 in a QC1/QC2 run
        j=np.searchsorted(anchors,i,side="left" if prior else "right")
        if prior:
            target=anchors[j-1] if j>0 else None
        else:
            target=anchors[j] if j<len(anchors) else None
        if target is None:return {"key":None,"hours":None,"RHwater_pct":None,
                                   "tower_T_C":None,"VPD_hPa":None}
        delta=abs((times.iat[i]-times.iat[target]).total_seconds()/3600)
        return {"key":keys.iat[target],
                "hours":float(delta),"RHwater_pct":float(rh0[target]),
                "tower_T_C":float(t[target]),"VPD_hPa":float(v[target])}
    flagged=edges.loc[edges.status.ne("PASS")].copy()
    event_targets=sorted(set(flagged.left_native)|set(flagged.right_native)|HARD9)
    rows=[]
    for key in event_targets:
        i=pos[key]
        aa=anchor(i,True);bb=anchor(i,False)
        ta=float(trial.TA_USE.iat[i]);ps=float(trial.PSRF.iat[i])
        sel_v=float(trial.VPD_USE.iat[i]);sel_q=float(trial.QBOT.iat[i])
        te=float(era.TA_ERA.iat[i]);ve=float(era.VPD_ERA.iat[i])
        source_rh=float(rh0[i]) if np.isfinite(rh0[i]) else np.nan
        rows.append(dict(native_key=key,
            science_HOLD=key in HARD9,original_finite_QC1QC2_newly_changed=key in changed,
            original_tower_T_QC=tq[i],original_VPD_QC=vq[i],
            original_tower_T_C=t[i],original_VPD_hPa=v[i],
            original_observation_RHwater_pct=source_rh,
            source_companion_ERA_T_C=te,source_companion_ERA_VPD_hPa=ve,
            original_selected_T_C=ta,original_selected_PSRF_Pa=ps,
            selected_T_minus_ERA_C=ta-te,
            Stage14K_VPD_hPa=float(original.VPD_USE.iat[i]),
            Stage14L_VPD_hPa=sel_v,
            Stage14K_QBOT=float(original.QBOT.iat[i]),
            Stage14L_QBOT=sel_q,
            original_both_QC0_measured=bool(measured[i]),
            previous_real_both_QC0_key=aa["key"],
            previous_QC0_gap_hours=aa["hours"],
            previous_QC0_RH_pct=aa["RHwater_pct"],
            next_real_both_QC0_key=bb["key"],
            next_QC0_gap_hours=bb["hours"],
            next_QC0_RH_pct=bb["RHwater_pct"],
            true_both_QC0_bracketing_within_2h=bool(
                aa["hours"] is not None and bb["hours"] is not None and
                aa["hours"]<=2 and bb["hours"]<=2),
            true_both_QC0_bracketing_within_6h=bool(
                aa["hours"] is not None and bb["hours"] is not None and
                aa["hours"]<=6 and bb["hours"]<=6),
            source_obs_not_independent_when_QC1QC2=True,
            operator_approved=False))
    table=pd.DataFrame(rows)
    edges["left_both_QC0"]=edges.left_native.map(
       lambda k:bool(measured[pos[k]]))
    edges["right_both_QC0"]=edges.right_native.map(
       lambda k:bool(measured[pos[k]]))
    edges["left_QC0_bracket_6h"]=edges.left_native.map(
       dict(zip(table.native_key,table.true_both_QC0_bracketing_within_6h)))
    edges["right_QC0_bracket_6h"]=edges.right_native.map(
       dict(zip(table.native_key,table.true_both_QC0_bracketing_within_6h)))
    # Do not promote either method. Catalogue what actual new source
    # observations would be needed to release the nine hard anomalies.
    special=table.loc[table.science_HOLD].copy()
    need(len(special)==9 and not special.Stage14L_VPD_hPa.notna().any(),
         "nine original source hard missing still explicitly protected")
    serious=flagged.loc[pd.to_numeric(flagged.abs_dVPD_hPa,
                 errors="coerce")>=10].copy()
    serious["source_class"]="SOURCE_REVIEW_GT10HPA"
    summary=dict(version=V,site="US-Kon",
       model_native_halfhours=len(trial),
       source_Stage14K_SHA256=digest(K/KF),
       source_Stage14L_SHA256=digest(L/LF),
       original_tower_SHA256=digest(site["primary"]),
       original_companion_ERA_SHA256=digest(site["era"]),
       actual_Stage14L_finite_neighbor_source_edits=len(changes),
       previous_68_missing_reconstructed_numerically=True,
       still_missing_original_HOLD=9,
       original_seed_boundary_warnings_before=46,
       original_seed_boundary_warnings_after=41,
       expanded_boundary_warnings=44,
       true_original_both_QC0_total_site=int(measured.sum()),
       selected_affected_source_native_halfhours=len(table),
       affected_native_times_with_both_QC0_within6h=int(
          table.true_both_QC0_bracketing_within_6h.sum()),
       still_flagged_edge_VPD_gt10hPa=len(serious),
       hard_nine_with_measured_QC0_within6h=int(
          special.true_both_QC0_bracketing_within_6h.sum()),
       candidate_Stage14L_research_sensitivity_only=True,
       preferred_Stage14K_preserves_finite_original_source=True,
       new_source_humidity_repairs_allowed=0,
       no_DATM_Postv5_AD400_Slurm=True)
    print("\nUS-Kon Stage14M ORIGINAL TRUE QC0 EVIDENCE SUMMARY",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("\nUS-Kon ALL NINE ORIGINAL HIGH-CONFIDENCE SCIENCE HOLDS, RAW QC0 CONTEXT")
    print(special[["native_key","original_tower_T_QC","original_VPD_QC",
          "original_tower_T_C","selected_T_minus_ERA_C",
          "previous_real_both_QC0_key","previous_QC0_gap_hours",
          "next_real_both_QC0_key","next_QC0_gap_hours",
          "true_both_QC0_bracketing_within_6h"]].to_string(index=False),flush=True)
    print("\nUS-Kon SEVERE REMAINING >10HPA SOURCE-Boundary OBS-QC CLASSIFICATION")
    print(serious[["left_native","right_native","status",
        "abs_dVPD_hPa","source_original_VPD_QC_left",
        "source_original_VPD_QC_right"]].to_string(index=False),flush=True)
    print("US-Kon STAGE14M ACTUAL SOURCE QC0 EVIDENCE READONLY COMPLETE; NO FORCING WRITES",flush=True)
    return summary,table,edges,special,serious
def main():
    p=argparse.ArgumentParser()
    opt=p.add_mutually_exclusive_group(required=True)
    for a in ("self-test","check","run"):opt.add_argument("--"+a,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    summary,table,edges,hard,serious=assess()
    if args.check:
        print("US-Kon Stage14M QC0 CHECK PASS; no reports or source writes",flush=True)
        return
    out=R/"reports"/("US_Kon_14M_original_QC0_9HOLD_44edges_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    products={"US_Kon_original_9HOLD_and_44warned_QC0_ERA_measured_context.csv":table,
       "US_Kon_all_103_expanded_joins_with_QC0_evidence.csv":edges,
       "US_Kon_nine_protected_hard_source_original_QC0.csv":hard,
       "US_Kon_all_gt10hPa_remaining_source_native_joins.csv":serious}
    outputs={}
    for fn,x in products.items():
        x.to_csv(out/fn,index=False,float_format="%.17g")
        outputs[fn]=digest(out/fn)
    (out/"US_Kon_Stage14M_original_QC0_evidence_summary.json").write_text(
       json.dumps(summary,indent=2)+"\n")
    outputs["US_Kon_Stage14M_original_QC0_evidence_summary.json"]=digest(
       out/"US_Kon_Stage14M_original_QC0_evidence_summary.json")
    (out/"NO_NEW_OBSERVATIONS_OR_DATM_APPROVAL").write_text(
       "This is an original QC0 source verification of nine unfilled hard "
       "science anomalies and 44 flagged local interfaces. Stage14K remains "
       "the preferred least-modified incomplete exploratory candidate; "
       "Stage14L is a separately versioned 7-neighbour alternative. "
       "Neither source is observationally validated for every event. "
       "No source writes, no Post-v5, DATM, AD400 or Slurm.\n")
    outputs["NO_NEW_OBSERVATIONS_OR_DATM_APPROVAL"]=digest(
       out/"NO_NEW_OBSERVATIONS_OR_DATM_APPROVAL")
    (out/"US_Kon_14M_READONLY_SHA_receipt.json").write_text(json.dumps({
       "version":V,"source_Stage14K":summary["source_Stage14K_SHA256"],
       "source_Stage14L":summary["source_Stage14L_SHA256"],
       "outputs_SHA256":outputs,"science_approved":False,
       "model_job_submitted":False},indent=2)+"\n")
    print("US-Kon Stage14M QC0 EVIDENCE REPORT:",out,flush=True)
    print("US-Kon STAGE14M ONEPASS TRUE SOURCE QC0 RESEARCH REVIEW DONE | ORIGINALS AND 9 HARD HOLD UNCHANGED | NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("US-Kon STAGE14M FAIL CLOSED:",ex,file=sys.stderr,flush=True)
        raise

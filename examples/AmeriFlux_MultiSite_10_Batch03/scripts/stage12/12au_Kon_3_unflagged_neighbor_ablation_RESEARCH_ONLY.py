#!/usr/bin/env python3
"""Stage12au: research-only three-row ablation of US-Kon Stage12an.

Ablation = restore ONLY three preselected original QC1/MDS finite VPD/QBOT
values from signed Stage12ak into the Stage12an 79-row shadow simulation,
and reassess both immediate 30-minute VPD edges and humidity physics.

The 3 positions have INSUFFICIENT independent evidence for ERA replacement:
  201104051030: original T QC0 but relative difference below severe-dry gate
  201110170230: original T QC1
  201110172330: original T QC1

Compare 5 numeric scenarios in memory: original Stage12an, three separate
one-row reversions, all-three reversion. Reversion is NOT approval to use
original MDS or ERA as ground truth. NO forcing CSVs are output.
Original 7 held events and two hard temperature conflicts remain held.

--self-test: synthetic; no files/no writes.
--check: full signed inputs, SHA/research audit; NO WRITES.
--run: same check + isolated science tables & SHA receipt ONLY.
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage12au-v1-20261026-Kon-three-unflagged-neighbor-ablation"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AT=ROOT/"reports/stage12at_Kon_37_invalid_source_RH_three_exceptions_science_20261026T120300Z_2a63d73c"
AK=ROOT/"science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AN=ROOT/"science_trials/stage12an_Kon_55_center_connected_ERA_RH_science_only_20261026T040913Z_277a0364"
AK_CSV="US-Kon_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
AN_CSV="US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
AN_PATCH="research_candidate_native_QC1_QC2_humidity_event_changes.csv"
AT_EXCEPTION="three_unflagged_original_QC1_neighbor_exceptions.csv"
AT_37="37_original_QC1_MDS_invalid_RH_vs_selected_stage12ak_stage12an.csv"
SPECIAL={"201102220900","201109291830"}
TARGETS={
  "201104051030":("SOURCE_QC0_T_BUT_MODERATE_ORIGINAL_ERA_DISAGREEMENT",10),
  "201110170230":("ORIGINAL_T_QC1_SOURCE_INDEPENDENCE_HOLD",15),
  "201110172330":("ORIGINAL_T_QC1_SOURCE_INDEPENDENCE_HOLD",17),
}
MAX_JUMP_HPA=4.0

def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise RuntimeError("Pinned input unavailable/symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def native(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def boolcol(x):
    return x.astype(str).str.strip().str.lower().eq("true")

def satw(t):
    if not np.isfinite(t) or not (-85<t<55):
        return np.nan
    return 6.112*np.exp(17.67*t/(243.5+t))

def conditions(t,v,q):
    if not np.isfinite([t,v,q]).all() or not 0<q<0.08:
        return False,"NONFINITE_OR_QBOT_PHYSICS"
    sv=satw(t)
    if not np.isfinite(sv) or not 0<=v<=sv:
        return False,"NEGATIVE_VPD_OR_RH_OUTSIDE_0_TO_100"
    return True,"FINITE_PHYSICAL_ONLY_NOT_APPROVED"

def halfhour(a,b):
    return (pd.Timestamp(b)-pd.Timestamp(a))==pd.Timedelta(minutes=30)

def selftest():
    assert conditions(20,4,0.006)[0]
    assert not conditions(20,np.nan,0.006)[0]
    assert not conditions(20,100,0.006)[0]
    assert halfhour("2011-10-17 23:30","2011-10-18 00:00")
    assert len(TARGETS)==3 and len(SPECIAL)==2
    print("STAGE12AU SELF-TEST PASS | one-row ablation, 4hPa edges and water-vapor physics; NO WRITES",flush=True)

def verified():
    at=json.loads(safe(AT/"stage12at_reconciliation_SHA_receipt.json").read_text())
    ak=json.loads(safe(AK/"stage12ak_research_proposal_SHA_receipt.json").read_text())
    an=json.loads(safe(AN/"stage12an_research_only_55_source_event_SHA_receipt.json").read_text())
    if not (at.get("version")=="batch03-stage12at-v1-20261026-Kon-37-invalid-3-exceptions-reconcile"
       and at.get("source_invalid_RH_rows")==37
       and at.get("original_finite_neighbor_unflagged_exceptions")==3
       and at.get("Stage12an_missing_centers_proposals_unapproved")==48
       and at.get("Stage12an_finite_QC1_neighbor_proposals_unapproved")==31
       and at.get("seven_blocked_events_preserved") is True
       and at.get("two_source_T_special_holds_preserved") is True
       and at.get("operator_approved") is False
       and at.get("DATM_ready") is False
       and at.get("spinup_authorized") is False
       and an.get("research_center_pass_numerical")==48
       and an.get("original_finite_QC1_QC2_neighbor_source_humidity_changes")==31
       and an.get("numerical_event_trial_PASSED")==19
       and an.get("numerical_event_trial_HELD")==7
       and set(an.get("source_t_disagreement_hard_holds",[]))==SPECIAL
       and an.get("operator_humidity_approval") is False
       and an.get("DATM_ready") is False
       and an.get("spinup_authorized") is False):
        raise RuntimeError("Signed approval/inventory gate or original 79-row trial changed")
    for name in (AT_EXCEPTION,AT_37,
            "26_original_connected_episode_strict_science_review_routes.csv",
            "31_original_finite_neighbor_episode_source_evidence.csv",
            "SCIENTIFIC_HOLD_ALL_79_NO_POSTV5_DATM"):
        if at.get("output_SHA256",{}).get(name)!=sha(AT/name):
            raise RuntimeError("Stage12at signed output altered: "+name)
    for name in (AN_CSV,AN_PATCH,
            "connected_episode_pass_and_source_hold_reasons.csv"):
        if an.get("output_SHA256",{}).get(name)!=sha(AN/name):
            raise RuntimeError("Stage12an signed output altered: "+name)
    if ak.get("output_SHA256",{}).get(AK_CSV)!=sha(AK/AK_CSV):
        raise RuntimeError("Stage12ak shadow CSV altered")

def audit():
    verified()
    exceptions=pd.read_csv(safe(AT/AT_EXCEPTION),dtype={"native_key":str},
                           low_memory=False)
    original37=pd.read_csv(safe(AT/AT_37),dtype={"native_key":str},
                           low_memory=False)
    if len(exceptions)!=3 or set(exceptions.native_key)!=set(TARGETS) \
       or len(original37)!=37 or original37.native_key.duplicated().any():
        raise RuntimeError("Three specified exceptions or 37 original invalid RH lineage changed")
    q1=exceptions.set_index("native_key").loc["201104051030","original_TA_F_QC"]
    q2=exceptions.set_index("native_key").loc["201110170230","original_TA_F_QC"]
    q3=exceptions.set_index("native_key").loc["201110172330","original_TA_F_QC"]
    if (q1,q2,q3)!=(0,1,1):
        raise RuntimeError("Original special-source temperature QC gate changed")
    # Recount 37 original invalid to avoid conflating them with 31 existing
    # source-humidity entries; Stage12ak is a research-only predecessor too.
    at_status=original37.Stage12ak_source_status
    an_status=original37.Stage12an_source_status
    if not (int(at_status.eq("RETAINED_HUMIDITY_MISSING").sum())==9
        and int(an_status.eq("RETAINED_HUMIDITY_MISSING").sum())==1
        and int(at_status.eq("RESEARCH_SELECTED_FINITE_PHYSICAL_NOT_APPROVED").sum())==28
        and int(an_status.eq("RESEARCH_SELECTED_FINITE_PHYSICAL_NOT_APPROVED").sum())==36
        and int(original37.Stage12an_numerically_changed_this_row.astype(str).str.lower().eq("true").sum())==8
        and original37.loc[an_status.eq("RETAINED_HUMIDITY_MISSING"),"native_key"].tolist()==["201105261100"]):
        raise RuntimeError("37 invalid source row reconciliation differs from Stage12at")
    fields=["time","TA_USE","VPD_USE","QBOT"]
    base=pd.read_csv(safe(AK/AK_CSV),usecols=fields,
                     dtype={"time":str},low_memory=False)
    trial=pd.read_csv(safe(AN/AN_CSV),usecols=fields,
                      dtype={"time":str},low_memory=False)
    if len(base)!=280320 or len(trial)!=280320:
        raise RuntimeError("Selected Kon original NOLEAP 280320 rows missing")
    keys=native(base.time)
    if keys.duplicated().any() or not keys.equals(native(trial.time)):
        raise RuntimeError("Source-native 30min clock changed/reordered")
    if not np.array_equal(base.TA_USE.to_numpy(),trial.TA_USE.to_numpy(),equal_nan=True):
        raise RuntimeError("Stage12an altered protected original selected temperature")
    patch=pd.read_csv(safe(AN/AN_PATCH),dtype={"native_key":str},low_memory=False)
    signed=patch.loc[boolcol(patch.episode_numerical_pass)].copy()
    if len(signed)!=79 or signed.native_key.duplicated().any() or \
       set(signed.native_key)&SPECIAL or \
       not set(TARGETS).issubset(set(signed.native_key)) or \
       not signed.loc[signed.native_key.isin(TARGETS),"kind"].eq(
            "NEIGHBOR_ORIGINAL_VPD_QC1_QC2_PROPOSAL").all():
        raise RuntimeError("Stage12an signed 79 science proposals changed")
    jmap=pd.Series(np.arange(len(keys)),index=keys.to_numpy())
    base_v=base.VPD_USE.to_numpy(dtype=float)
    base_q=base.QBOT.to_numpy(dtype=float)
    trial_v=trial.VPD_USE.to_numpy(dtype=float)
    trial_q=trial.QBOT.to_numpy(dtype=float)
    ts=trial.TA_USE.to_numpy(dtype=float)
    changed=(~np.isclose(base_v,trial_v,rtol=0,atol=1e-10,equal_nan=True) |
             ~np.isclose(base_q,trial_q,rtol=0,atol=1e-12,equal_nan=True))
    if set(keys.iloc[np.flatnonzero(changed)])!=set(signed.native_key):
        raise RuntimeError("Signed Stage12an differences are not exactly 79 proposals")
    details=[]
    variants=[
        ("FULL_STAGE12AN_RESEARCH",set()),
        *[("RESTORE_ONLY_"+k,{k}) for k in TARGETS],
        ("RESTORE_ALL_THREE",set(TARGETS))
    ]
    for name,restored in variants:
        # ZERO full candidate outputs: only values around 3 affected positions.
        for k,(reason,episode) in TARGETS.items():
            j=int(jmap[k])
            if j<1 or j+1>=len(keys):
                raise RuntimeError("Cannot audit both half-hour sides of "+k)
            if not (halfhour(pd.to_datetime(keys.iat[j-1],format="%Y%m%d%H%M"),
                             pd.to_datetime(k,format="%Y%m%d%H%M"))
                and halfhour(pd.to_datetime(k,format="%Y%m%d%H%M"),
                             pd.to_datetime(keys.iat[j+1],format="%Y%m%d%H%M"))):
                raise RuntimeError("Not an exact 30min original sequence at "+k)
            v=float(base_v[j] if k in restored else trial_v[j])
            q=float(base_q[j] if k in restored else trial_q[j])
            t=float(ts[j])
            if not (np.isfinite([base_v[j],base_q[j],trial_v[j],trial_q[j]]).all()):
                raise RuntimeError("One of the three signed finite originals/candidates absent")
            p=abs(v-float(trial_v[j-1])) if np.isfinite(trial_v[j-1]) else np.nan
            n=abs(float(trial_v[j+1])-v) if np.isfinite(trial_v[j+1]) else np.nan
            # Another exceptional position could be immediately adjacent
            # in a general variant; currently all three are separate days/hours.
            for side,index in (("prev",j-1),("next",j+1)):
                neighbor_key=keys.iat[index]
                vv=float(base_v[index]) if neighbor_key in restored else float(trial_v[index])
                if side=="prev":p=abs(v-vv) if np.isfinite(vv) else np.nan
                else:n=abs(vv-v) if np.isfinite(vv) else np.nan
            good,why=conditions(t,v,q)
            both=np.isfinite([p,n]).all() and p<=MAX_JUMP_HPA and n<=MAX_JUMP_HPA
            status=("LOCAL_EDGES_AND_PHYSICS_PASS_NUMERIC_ONLY" if good and both else
                    "LOCAL_EDGE_NONFINITE_NEIGHBOR" if not np.isfinite([p,n]).all() else
                    "LOCAL_EDGE_GT4HPA" if p>MAX_JUMP_HPA or n>MAX_JUMP_HPA else
                    "LOCAL_HUMIDITY_PHYSICS_FAIL")
            details.append({
                "variant":name,"native_key":k,"episode":episode,
                "source_science_reason":reason,
                "original_selected_temperature_C":t,
                "original_selected_VPD_hPa":float(base_v[j]),
                "Stage12an_candidate_VPD_hPa":float(trial_v[j]),
                "ablation_used_VPD_hPa":v,
                "original_selected_QBOT_kgkg":float(base_q[j]),
                "Stage12an_candidate_QBOT_kgkg":float(trial_q[j]),
                "ablation_used_QBOT_kgkg":q,
                "restored_original_QC1_MDS":bool(k in restored),
                "ablation_RH_pct":100*(1-v/satw(t)),
                "VPD_jump_prev_30min_hPa":p,
                "VPD_jump_next_30min_hPa":n,
                "both_30min_edges_finite_and_at_most_4hPa":bool(both),
                "VPD_QBOT_physics":why,
                "physics_ok":bool(good),
                "local_reversion_science_gate":status,
                "operator_approval":False
            })
    summary=pd.DataFrame(details)
    unique=summary.loc[summary.variant.eq("RESTORE_ALL_THREE")]
    if len(summary)!=15 or len(unique)!=3:
        raise RuntimeError("Exactly three source neighbors times five ablations required")
    if set(unique.native_key)!=set(TARGETS) or len(summary.variant.unique())!=5:
        raise RuntimeError("Unapproved source finite-neighbor research gate altered")
    counts=pd.DataFrame([{
      "variant":v,"restored_original_finite_source_neighbors":len(
          set(TARGETS)&next(x for n,x in variants if n==v)),
      "physically_valid_neighbor_rows":int(g.physics_ok.sum()),
      "both_edges_within4_hPa_count":int(g.both_30min_edges_finite_and_at_most_4hPa.sum()),
      "local_numeric_pass_N":int(
          g.local_reversion_science_gate.eq("LOCAL_EDGES_AND_PHYSICS_PASS_NUMERIC_ONLY").sum()),
      "local_nonpass_N":int(
          (~g.local_reversion_science_gate.eq("LOCAL_EDGES_AND_PHYSICS_PASS_NUMERIC_ONLY")).sum()),
      "operator_approval":False,
    } for v,g in summary.groupby("variant",sort=False)])
    return summary,counts

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):
        g.add_argument("--"+name,action="store_true")
    a=p.parse_args()
    print("STAGE12AU Kon 3 ORIGINAL QC1 NEIGHBOR REVERT ABLATIONS | "+VERSION,flush=True)
    selftest()
    if a.self_test:return
    table,overall=audit()
    print("\n===== THREE ROWS x FIVE RESEARCH ABLATION SCENARIOS =====",flush=True)
    print(table.to_string(index=False),flush=True)
    print("\n===== ABLATION LOCAL SCIENCE BOUNDARY SUMMARY =====",flush=True)
    print(overall.to_string(index=False),flush=True)
    print("37 ORIGINAL INVALID RH: Stage12ak 28 PHYSICAL/9 MISSING;",
          "Stage12an 36 PHYSICAL/1 MISSING (201105261100 STILL HOLD).",flush=True)
    print("3 ORIGINAL FINITE QC1 NEIGHBORS | 79 Stage12an RESEARCH PROPOSALS",
          "| 48 CENTERS + 31 FINITE | 7 FAILED EVENTS + 2 SPECIAL T SOURCE HOLDS",
          "| ZERO PRODUCTION APPROVAL",flush=True)
    if a.check:
        print("STAGE12AU CHECK ONLY | NO FILE WRITES",flush=True)
        return
    dest=ROOT/"reports"/("stage12au_Kon_3_original_QC1_neighbor_ablation_science_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
          "_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    outputs={
       "three_finite_QC1_neighbors_five_reversion_ablation_edge_physics.csv":table,
       "three_unflagged_neighbor_reversion_scenario_summary.csv":overall}
    for n,df in outputs.items():
        df.to_csv(dest/n,index=False)
    note="RESEARCH_ONLY_NO_INPUT_NO_APPROVAL"
    (dest/note).write_text(
        "Ablation is a local science diagnostic, not a proposed model input. "
        "A physics/boundary numeric PASS cannot establish true relative "
        "humidity or approve restoration of original MDS values. "
        "The 48 missing-center fills, 31 original finite-neighbor "
        "replacements, seven failed events and the two hard source-temperature "
        "holds remain all unapproved. The original selected forcing is neither "
        "overwritten nor written as a derivative. No Slurm, DATM, CIME, "
        "spinup or model inputs written.\n")
    checks={f:sha(dest/f) for f in [*outputs,note]}
    (dest/"stage12au_three_neighbor_ablation_SHA_receipt.json").write_text(
      json.dumps({
        "version":VERSION,
        "signed_stage12at_SHA256":sha(AT/"stage12at_reconciliation_SHA_receipt.json"),
        "signed_stage12an_SHA256":sha(
          AN/"stage12an_research_only_55_source_event_SHA_receipt.json"),
        "stage12an_original_finite_neighbors_tested":3,
        "original_37_invalid_RH_stage12an_physical_finite":36,
        "original_37_invalid_RH_stage12an_missing":1,
        "unresolved_native_key":"201105261100",
        "original_48_center_fills_unapproved":True,
        "original_31_finite_neighbor_replacements_unapproved":True,
        "seven_blocked_episodes_preserved":True,
        "two_special_source_T_holds_preserved":True,
        "operator_approved":False,"Postv5_approved":False,
        "DATM_ready":False,"spinup_authorized":False,
        "output_SHA256":checks},indent=2)+"\n")
    print("STAGE12AU SIGNED READONLY RESEARCH REPORT DIR:",dest,flush=True)
    print("NO ORIGINAL SOURCE, PREVIOUS TRIAL, MODEL, DATM OR FORCING WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12AU STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

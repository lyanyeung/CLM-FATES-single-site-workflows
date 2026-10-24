#!/usr/bin/env python3
"""Batch03 Stage11f — event-grouped human scientific review queue, NOT approval.

Reads only SHA-sealed Stage11e-v2 and Stage11d reports plus Stage07 hold marker:
  62 unique review events, 6 originally QC0 temperature changes,
  38 source QC1 VPD changes in consecutive 30-min episodes,
  5 positive RH<1% candidates and 4 unmodified manual notices.

Outputs a NEW, unsigned review worksheet, episode inventory and QC0 neighbor
evidence. Even a complete numerical pass DOES NOT authorize any forcing.
No time offset, PFT/CO2, Post-v5, DATM or spinup is accepted automatically.

Modes:
--self-test  synthetic rows only; never read IRIDIS files, never write files
--check      validate SHA, joins and counts, display queue (no writes)
--run        create a NEW reports/stage11f_* directory containing
             CSV review worksheets, immutable evidence and SHA receipt
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11f-v1-20261024-manual-scientific-review-queue"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11D=ROOT/"reports/stage11d_priority_source_context_20261024T072456Z_8e3c6249"
S11E=ROOT/"reports/stage11e_science_triage_20261024T074227Z_062db11d"
FILES11E={
  "62_priority_event_physics_and_science_review.csv",
  "6_QC0_temperature_neighbor_evidence.csv",
  "38_QC1_VPD_ERA_replacement_physics.csv",
  "38_original_source_physics_category_counts.csv",
  "5_positive_extreme_dry_events.csv",
  "three_site_final_triage_summary.csv",
  "SCIENTIFIC_DECISION_HOLD.md",
}
REVIEW_ID=["site","native_key","variable"]
SITES={"US-MOz":1,"US-Mpj":6,"US-NC2":55}


def safe_file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink input file: "+str(p))
    return p


def safe_dir(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing/symlink input directory: "+str(p))
    return p


def sha256(path):
    h=hashlib.sha256()
    with safe_file(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def js(path):
    return json.loads(safe_file(path).read_text(encoding="utf-8"))


def read_csv(path):
    return pd.read_csv(safe_file(path),dtype={"native_key":str},low_memory=False)


def dates_from_key(values):
    s=pd.Series(values,dtype=str)
    if not s.str.fullmatch(r"\d{12}").all():
        raise ValueError("Expected native YYYYMMDDHHMM string with no time shift")
    t=pd.to_datetime(s,format="%Y%m%d%H%M",errors="raise")
    if t.isna().any():
        raise ValueError("Invalid native timestamp")
    return t


def boolean(df,name):
    x=df[name].astype(str).str.strip().str.lower()
    if not x.isin(("true","false","1","0")).all():
        raise ValueError("Unexpected boolean evidence: "+name)
    return x.isin(("true","1")).to_numpy(dtype=bool)


def require_ids(df,expected,desc):
    if len(df)!=expected or not set(REVIEW_ID)<=set(df.columns):
        raise ValueError(desc+" expected count or keys changed")
    if df.duplicated(REVIEW_ID).any():
        raise ValueError(desc+" duplicate event IDs")
    if not df.native_key.astype(str).str.fullmatch(r"\d{12}").all():
        raise ValueError(desc+" malformed native timestamp")


def preflight():
    for p in (ROOT,S07,S11D,S11E):
        safe_dir(p)
    safe_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    e=js(S11E/"scientific_hold_receipt.json")
    d=js(S11D/"read_only_provenance.json")
    if (e.get("version")!="stage11e-v2-20261024-synthetic-scope-guard"
        or e.get("source_target_records")!=62
        or e.get("original_QC0_T_change_records")!=6
        or e.get("native_VPD_QC1_ERA_substitutions")!=38
        or e.get("positive_extreme_dry_records")!=5
        or e.get("scientific_repair_approvals")!=0
        or e.get("Postv5_approvals")!=0
        or e.get("DATM_ready")!=0
        or e.get("spinup_authorizations")!=0
        or e.get("Stage07_INCOMPLETE_marker_retained") is not True
        or e.get("upstream_provenance_SHA256",{}).get("stage11d_receipt_SHA256")
             !=sha256(S11D/"read_only_provenance.json")
        or e.get("upstream_provenance_SHA256",{}).get("stage07_manifest_SHA256")
             !=sha256(S07/"exact_input_manifest.json")
        or d.get("unmodified_manual_records")!=4
        or d.get("zero_approval") is not True
        or set(e.get("outputs_SHA256",{}))!=FILES11E):
        raise ValueError("Stage11e-v2 scientific hold/provenance differs")
    for name in FILES11E:
        if sha256(S11E/name)!=e["outputs_SHA256"][name]:
            raise ValueError("Stage11e report modified: "+name)
    dfile="four_unmodified_manual_holds.csv"
    if sha256(S11D/dfile)!=d.get("output_sha256",{}).get(dfile):
        raise ValueError("Stage11d unchanged-manual evidence changed")
    review=read_csv(S11E/"62_priority_event_physics_and_science_review.csv")
    qc0=read_csv(S11E/"6_QC0_temperature_neighbor_evidence.csv")
    vpd=read_csv(S11E/"38_QC1_VPD_ERA_replacement_physics.csv")
    dry=read_csv(S11E/"5_positive_extreme_dry_events.csv")
    unchanged=read_csv(S11D/dfile)
    require_ids(review,62,"Stage11e review")
    require_ids(vpd,38,"Stage11e source QC1")
    if review.site.value_counts().to_dict()!=SITES:
        raise ValueError("Expected 1/6/55 per-site review records")
    if len(qc0)!=6 or qc0.duplicated(["site","native_key"]).any():
        raise ValueError("Six source QC0 temperature changes changed")
    if len(dry)!=5 or dry.duplicated(REVIEW_ID).any():
        raise ValueError("Five positive RH<1% events changed")
    if len(unchanged)!=4:
        raise ValueError("Four unmodified manual records changed")
    review_id=set(map(tuple,review[REVIEW_ID].to_numpy()))
    for desc,df in (("QC1 VPD",vpd),("low RH",dry)):
        if not set(map(tuple,df[REVIEW_ID].to_numpy()))<=review_id:
            raise ValueError(desc+" event IDs not within 62-target review")
    if not set(map(tuple,qc0[["site","native_key"]].assign(
            variable="TA_F")[REVIEW_ID].to_numpy()))<=review_id:
        raise ValueError("Measured QC0 temperature event ID missing")
    if boolean(review,"approved_correction").any():
        raise ValueError("Stage11e unexpected approved forcing events")
    if not (vpd.original_T_VPD_physics.eq("NONPOSITIVE_IMPLIED_EA").all()
        and vpd.source_VPD_QC.eq(1).all()
        and vpd.site.eq("US-NC2").all()
        and (pd.to_numeric(vpd.source_implied_ea_hPa,errors="coerce")<0).all()):
        raise ValueError("38 source QC1 VPD physical failures changed")
    source_qc0=pd.to_numeric(qc0.source_T_QC0,errors="coerce")
    if not source_qc0.eq(0).all():
        raise ValueError("Six original QC0 source flags changed")
    if not np.isclose(pd.to_numeric(qc0.candidate_minus_neighbor_mean_C),
                      0,atol=1e-8,rtol=0).all():
        raise ValueError("Six immediate-neighbor means are not preserved")
    if not ((pd.to_numeric(dry.candidate_water_RH_pct)>0)&
            (pd.to_numeric(dry.candidate_water_RH_pct)<1)&
            (pd.to_numeric(dry.candidate_T_C)>0)).all():
        raise ValueError("Original five warm positive RH<1% values changed")
    return review,qc0,vpd,dry,unchanged,{
        "Stage11e_receipt_SHA256":sha256(S11E/"scientific_hold_receipt.json"),
        "Stage11d_receipt_SHA256":sha256(S11D/"read_only_provenance.json"),
        "Stage07_manifest_SHA256":sha256(S07/"exact_input_manifest.json")
    }


def group_vpd_episodes(data):
    """One episode per exact 30-minute contiguous span, zero guessed offsets."""
    z=data.sort_values(["site","native_key"],kind="mergesort").copy()
    if z.duplicated(REVIEW_ID).any():
        raise ValueError("Duplicate VPD episode event identity")
    t=dates_from_key(z.native_key)
    z["__timestamp"]=t.to_numpy()
    chunks=[]
    rows=[]
    for site,g in z.groupby("site",sort=True):
        last=None
        for _,r in g.iterrows():
            instant=r["__timestamp"]
            if last is None or instant-last!=pd.Timedelta(minutes=30):
                chunks.append([])
            chunks[-1].append(r)
            last=instant
        for number,chunk in enumerate(
                [chunk for chunk in chunks if chunk[0]["site"]==site],start=1):
            frame=pd.DataFrame(chunk)
            id_=f"{site}_QC1_VPD_{number:02d}"
            rows.append({
                "episode_id":id_,"site":site,
                "start_native_key":str(frame.native_key.iloc[0]),
                "end_native_key":str(frame.native_key.iloc[-1]),
                "half_hour_events":len(frame),
                "duration_hours":len(frame)*0.5,
                "min_original_implied_ea_hPa":float(pd.to_numeric(
                    frame.source_implied_ea_hPa).min()),
                "max_original_VPD_hPa":float(pd.to_numeric(
                    frame.source_VPD_hPa).max()),
                "median_candidate_RH_water_pct":float(pd.to_numeric(
                    frame.candidate_water_RH_pct).median()),
                "review_outcome":"HOLD_QC1_SOURCE_AND_ERA_REPLACEMENT_VALIDATION",
                "accepted_forcing":False
            })
    if not rows:
        raise ValueError("No contiguous review episodes")
    result=pd.DataFrame(rows)
    if result.half_hour_events.sum()!=len(z):
        raise ValueError("Episode partition lost or duplicated QC1 source events")
    return result


def decision_template(review,qc0,vpd,dry,unchanged):
    temp_ids=set(zip(qc0.site,qc0.native_key))
    vpd_ids=set(map(tuple,vpd[REVIEW_ID].to_numpy()))
    dry_ids=set(map(tuple,dry[REVIEW_ID].to_numpy()))
    manual_ids=set((str(r.site),
                    pd.Timestamp(r.time).strftime("%Y%m%d%H%M"),str(r.variable))
                    for r in unchanged.itertuples(index=False))
    prior=[]
    for r in review.itertuples(index=False):
        key=(r.site,r.native_key,r.variable)
        p="P1_MANUAL_HUMIDITY_SOURCE_REVIEW"
        if (r.site,r.native_key) in temp_ids and r.variable=="TA_F":
            p="P0_CHANGED_MEASURED_QC0_T"
        elif key in vpd_ids:
            p="P0_ORIGINAL_NONPOSITIVE_VAPOUR_QC1_VPD"
        elif key in dry_ids:
            p="P1_POSITIVE_NEAR_ZERO_RH"
        prior.append({
            "site":r.site,
            "native_key":r.native_key,
            "variable":r.variable,
            "science_review_priority":p,
            "original_stage11e_reasons":r.reasons,
            "native_ERA_same_time_approved":False,
            "original_QC0_modified":p=="P0_CHANGED_MEASURED_QC0_T",
            "original_VPD_QC1_physics_conflict":key in vpd_ids,
            "positive_RH_below_1pct":key in dry_ids,
            "unchanged_manual_review":key in manual_ids,
            "candidate_implied_ea_hPa":r.candidate_implied_ea_hPa,
            "candidate_water_RH_pct":r.candidate_water_RH_pct,
            "original_source_physics":r.original_T_VPD_physics,
            "reanalysis_is_independent_tower_truth":False,
            "science_status":"PENDING_SOURCE_INSTRUMENT_OR_METADATA_REVIEW",
            "post_v5_approved":False,
            "DATM_ready":False,
            "spinup_authorized":False,
            # These fields are intentionally empty; human review belongs in a
            # separate versioned follow-up, NEVER in the SHA-sealed output.
            "proposed_action_for_separate_review":"",
            "reviewer_reference":"",
            "reviewer_evidence_uri":"",
            "reviewer_rationale":"",
        })
    table=pd.DataFrame(prior)
    if len(table)!=len(review) or table.duplicated(REVIEW_ID).any():
        raise ValueError("Decision template duplicated or omitted a source ID")
    return table


def self_test():
    demo=pd.DataFrame({
        "site":["US-NC2"]*5,
        "native_key":["202503211930","202503212000","202503220100",
                      "202503230900","202503230930"],
        "variable":["VPD_F"]*5,
        "source_implied_ea_hPa":[-1.,-2.,-3.,-2.,-4.],
        "source_VPD_hPa":[10.,11.,12.,13.,14.],
        "candidate_water_RH_pct":[20.,22.,23.,25.,30.]
    })
    grouped=group_vpd_episodes(demo)
    assert len(grouped)==3 and grouped.half_hour_events.tolist()==[2,1,2]
    assert grouped.duration_hours.sum()==2.5
    assert grouped.accepted_forcing.eq(False).all()
    assert dates_from_key(["202503211930"]).dt.hour.iloc[0]==19
    try:
        dates_from_key(["2025-03-21T19:30:00"])
    except ValueError:
        pass
    else:
        raise AssertionError("Human-readable timestamps must not enter native key")
    print("STAGE11F SELF-TEST PASS: exact 30-minute episodes, gap splitting, native-clock keys, zero approvals",
          flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11F — HUMAN SCIENCE SIGNOFF QUEUE | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    review,qc0,vpd,dry,unchanged,pins=preflight()
    episodes=group_vpd_episodes(vpd)
    queue=decision_template(review,qc0,vpd,dry,unchanged)
    science_hold=(queue.post_v5_approved.astype(str).str.lower().eq("false").all()
                  and queue.DATM_ready.astype(str).str.lower().eq("false").all()
                  and queue.spinup_authorized.astype(str).str.lower().eq("false").all())
    if not science_hold:
        raise ValueError("Unexpected automatic science/model approval")
    if len(episodes)!=4 or episodes.half_hour_events.sum()!=38:
        raise ValueError("Expected four contiguous US-NC2 QC1 VPD conflict episodes")
    if not (int(queue.original_QC0_modified.sum())==6
            and int(queue.original_VPD_QC1_physics_conflict.sum())==38
            and int(queue.positive_RH_below_1pct.sum())==5
            and int(queue.unchanged_manual_review.sum())==4):
        raise ValueError("Review priority class counts differ from prior evidence")
    print("\n========== SIX QC0 TEMPERATURE CHANGES: ADJACENT SOURCE QC ==========",flush=True)
    cols=["site","native_key","original_source_T_C",
          "previous_source_T_C","previous_source_T_QC",
          "next_source_T_C","next_source_T_QC",
          "candidate_T_C","neighbors_are_source_QC0"]
    print(qc0[cols].to_string(index=False),flush=True)
    print("\n========== CONTIGUOUS US-NC2 QC1 VPD PHYSICS EPISODES ==========",flush=True)
    print(episodes.to_string(index=False),flush=True)
    print("\n========== FIVE POSITIVE RH BELOW 1 PERCENT ==========",flush=True)
    print(dry[["site","native_key","source_VPD_QC","candidate_T_C",
               "candidate_water_RH_pct"]].to_string(index=False),flush=True)
    print("\n========== HUMAN SCIENCE REVIEW QUEUE BY SITE AND PRIORITY ==========",flush=True)
    print(queue.groupby(["site","science_review_priority"]).size().to_string(),flush=True)
    print(f"\nSTAGE11F SUMMARY: review_events={len(queue)}/62 "
          f"original_QC0_T_changes={int(queue.original_QC0_modified.sum())}/6 "
          f"QC1_VPD_conflicts={int(queue.original_VPD_QC1_physics_conflict.sum())}/38 "
          f"QC1_consecutive_episodes={len(episodes)}/4 "
          f"positive_RH_lt1={int(queue.positive_RH_below_1pct.sum())}/5 "
          "postv5_approved=0 DATM_ready=0 spinup_authorizations=0",flush=True)
    if args.check:
        print("CHECK ONLY: zero report or forcing writes.",flush=True)
        return
    out=ROOT/"reports"/("stage11f_human_science_review_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    output={
        "62_human_scientific_review_queue.csv":queue,
        "4_US-NC2_QC1_VPD_episodes.csv":episodes,
        "6_original_QC0_T_neighbor_QC_detail.csv":qc0,
        "5_positive_RH_below_1pct_source_reviews.csv":dry,
        "4_unmodified_manual_records.csv":unchanged
    }
    for name,df in output.items():
        df.to_csv(out/name,index=False)
    instructions="""# Stage11f HUMAN SCIENTIFIC REVIEW REQUIRED — no write approval

This is a frozen, checksum-protected review-queue template, NOT a signoff.
All 62 native-timestamp event IDs remain on scientific hold. Review the six
modified source-QC0 air temperatures with actual left/right source QC, site
clock, sensor and instrument metadata. One source QC0 mismatch in isolation
can be evidence for a sensor error, but interpolation is not automatically
accepted as observational truth.

All 38 original US-NC2 VPD_F QC1 gapfilled values have paired-source nonpositive
implied water vapour pressure. They occur in four 30-minute contiguous
episodes in March 2025; automatic Stage07 ERA replacement fixed mathematical
water-RH signs, but did not independently establish tower humidity accuracy.

Five water-relative RH values strictly between zero and one percent occurred
at positive temperatures. Assess plausible atmospheric extremes, QC source,
relative humidity or dewpoint measurements if independently available; do
not clip them by threshold or treat ice saturation as the main obstacle.
Four unchanged manual warnings remain open. Some categories overlap.

For human decisions, copy the blank review template to a NEW, independently
versioned location. Record reviewer, independent evidence, rationale,
accepted/rejected/hold per event, timestamp/height/pressure conventions and
uncertainty; do not edit these SHA-sealed outputs or change approval booleans
without a separate reviewed documented decision process. After that,
scientific PFT/surface, CO2, full-annual Post-v5, DATM and spinup gates remain.

DO NOT DELETE Stage07 INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP.
No source, ERA, QCv5, Post-v5, DATM, CIME or Slurm modifications authorized.
"""
    (out/"SCIENTIFIC_HUMAN_SIGNOFF_GUIDE.md").write_text(instructions,encoding="utf-8")
    provenance={
        "version":VERSION,
        "input_sha256":pins,
        "stage11e_exact_events":62,
        "changed_original_measured_QC0":6,
        "source_QC1_VPD_physics_conflicts":38,
        "source_QC1_VPD_contiguous_episodes":4,
        "positive_RH_below_1pct":5,
        "unchanged_manual_notices":4,
        "signed_scientific_decisions":0,
        "post_v5_approvals":0,"DATM_ready":0,"spinup_authorizations":0,
        "stage07_incomplete_hold_retained":True,
        "output_sha256":{name:sha256(out/name) for name in [*output,"SCIENTIFIC_HUMAN_SIGNOFF_GUIDE.md"]}
    }
    (out/"read_only_scientific_hold_receipt.json").write_text(
        json.dumps(provenance,indent=2)+"\n",encoding="utf-8")
    print("STAGE11F REPORT DIR:",out,flush=True)
    print("NO ORIGINAL SOURCE, FORCING, POST-V5, DATM, CASE, RESTART OR SLURM MODIFICATIONS.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE11F STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

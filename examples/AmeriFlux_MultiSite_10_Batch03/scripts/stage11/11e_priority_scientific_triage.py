#!/usr/bin/env python3
"""Batch03 Stage11e: final 62-target thermodynamics + adjacent-observation triage.

INPUT: sealed Stage11d 62 targets and 558 native half-hour context rows.
OUTPUT: detailed numeric evidence for 6 source QC0 T changes, 38 QC1 VPD
replacements, 5 RH<1% values and 4 unchanged manual-review records.
All statistics are diagnostic. SCIENCE APPROVALS REMAIN ZERO.

--self-test: entirely synthetic tests; no IRIDIS accesses.
--check: re-hash pinned Stage11d evidence and compute summaries in memory only.
--run: one new reports/stage11e_* audit directory (CSV + hashes).
Never overwrite original data / forcing / Stage07 candidate, nor DATM/Slurm.
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
VERSION="stage11e-v1-20261024-final-priority-science-triage"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11C=ROOT/"reports/stage11c_qc0_manual_review_20261024T071530Z_ce6fdbb8"
S11D=ROOT/"reports/stage11d_priority_source_context_20261024T072456Z_8e3c6249"
FILE11D={
    "priority_review_target_index.csv",
    "plus_minus_2h_native_source_ERA_candidate_context.csv",
    "six_measured_QC0_changes.csv",
    "38_ERA_replacements_evidence.csv",
    "38_ERA_replacements_reason_counts.csv",
    "four_unmodified_manual_holds.csv",
    "three_site_review_target_summary.csv",
    "SCIENTIFIC_HOLD.md",
}
FILE11C={
    "105_exact_source_to_candidate_changes.csv",
    "6_original_QC0_modified_events.csv",
    "18_manual_review_entries.csv",
    "positive_RH_below_1pct_diagnostics.csv",
    "three_site_change_source_summary.csv",
    "SCIENTIFIC_REVIEW_REQUIRED.md",
}
KEY=["site","native_key","variable"]
PANEL_KEY=["target_site","target_native_time","target_variable"]
COUNTS={"US-MOz":1,"US-Mpj":6,"US-NC2":55}


def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink source: "+str(p))
    return p


def directory(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or symlink input folder: "+str(p))
    return p


def sha256(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def jsonfile(p):
    return json.loads(regular(p).read_text(encoding="utf-8"))


def numeric(df,key):
    if key not in df:
        raise ValueError("Missing required numerical field "+key)
    a=pd.to_numeric(df[key],errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a)|(a<=-9990)]=np.nan
    return a


def water_es(temp):
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*temp/(temp+243.5))


def ice_es(temp):
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(22.46*temp/(temp+272.62))


def read_verified():
    for p in (ROOT,S07,S11C,S11D):
        directory(p)
    regular(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    d=jsonfile(S11D/"read_only_provenance.json")
    c=jsonfile(S11C/"read_only_scientific_hold_receipt.json")
    if (d.get("version")!="stage11d-v1-20261024-priority-context"
        or d.get("stage11c_receipt_sha256")!=sha256(S11C/"read_only_scientific_hold_receipt.json")
        or d.get("Stage07_manifest_SHA256")!=sha256(S07/"exact_input_manifest.json")
        or d.get("original_measured_QC0_changes")!=6
        or d.get("ERA_replacements")!=38
        or d.get("manual_records")!=18
        or d.get("unmodified_manual_records")!=4
        or d.get("residual_RH_lt1_records")!=5
        or d.get("unique_priority_targets")!=62
        or d.get("zero_approval") is not True
        or d.get("postv5_approved")!=0 or d.get("DATM_ready")!=0
        or set(d.get("output_sha256",{}))!=FILE11D
        or c.get("approved_repairs")!=0 or c.get("approved_Postv5")!=0):
        raise ValueError("Stage11d/11c scientific hold and lineage differ")
    for file in FILE11D:
        if sha256(S11D/file)!=d["output_sha256"][file]:
            raise ValueError("Stage11d SHA has changed: "+file)
    if set(c.get("output_sha256",{}))!=FILE11C:
        raise ValueError("Stage11c source files changed")
    for file in FILE11C:
        if sha256(S11C/file)!=c["output_sha256"][file]:
            raise ValueError("Stage11c SHA changed: "+file)
    # The native timestamp is a string, never a numeric float or a timezone.
    target=pd.read_csv(regular(S11D/"priority_review_target_index.csv"),
                       dtype={"native_key":str},keep_default_na=False,low_memory=False)
    panel=pd.read_csv(regular(S11D/"plus_minus_2h_native_source_ERA_candidate_context.csv"),
                      dtype={"target_native_time":str,"context_native_time":str},
                      low_memory=False)
    if (len(target)!=62 or target.duplicated(KEY).any()
        or target.site.value_counts().to_dict()!=COUNTS or len(panel)!=558
        or panel[PANEL_KEY+["context_native_time"]].duplicated().any()
        or panel.offset_half_hours.isna().any()):
        raise ValueError("Expected 62 unique native targets and 558 context records")
    if target.accepted_forcing.astype(str).str.lower().ne("false").any():
        raise ValueError("Scientific approval found in target index")
    targetids=set(map(tuple,target[KEY].to_numpy()))
    panelids=set(map(tuple,panel[PANEL_KEY].to_numpy()))
    if targetids!=panelids:
        raise ValueError("Target/context identities do not match exactly")
    counts=panel.groupby(PANEL_KEY,sort=False).size()
    if len(counts)!=62 or not counts.eq(9).all():
        raise ValueError("Each of 62 contexts must have exactly nine +/-2h rows")
    offsets=panel.groupby(PANEL_KEY,sort=False).offset_half_hours.agg(list)
    if not all(sorted(map(int,x))==list(range(-4,5)) for x in offsets):
        raise ValueError("Context offsets differ from expected native +/-2h")
    centres=panel.loc[panel.offset_half_hours.eq(0)].copy()
    if len(centres)!=62 or centres[PANEL_KEY].duplicated().any():
        raise ValueError("Each target must have one centre row")
    centre_key=centres[PANEL_KEY].to_numpy()
    if len(set(map(tuple,centre_key)))!=62:
        raise ValueError("Duplicate centre rows")
    if not centres.ERA_exact_timestamp_available.astype(str).str.lower().eq("true").all():
        raise ValueError("Unmatched companion ERA at a source event time")
    return target,panel,centres,{
        "stage11c_receipt_SHA256":sha256(S11C/"read_only_scientific_hold_receipt.json"),
        "stage11d_receipt_SHA256":sha256(S11D/"read_only_provenance.json"),
        "stage07_manifest_SHA256":sha256(S07/"exact_input_manifest.json")
    }


def classify_original_humidity(ta,vpd):
    es=water_es(ta)
    ea=es-vpd
    with np.errstate(divide="ignore",invalid="ignore"):
        rh=100*ea/es
    classification=np.full(len(ta),"PHYSICALLY_PLAUSIBLE_WATER",dtype=object)
    invalid=~(np.isfinite(ta)&np.isfinite(vpd)&np.isfinite(es)&np.isfinite(ea))
    classification[invalid]="MISSING_OR_NONFINITE"
    classification[~invalid&(ea<=0)]="NONPOSITIVE_IMPLIED_EA"
    classification[~invalid&(ea>0)&(vpd < -1e-7)]="NEGATIVE_VPD_SUPERSATURATION"
    classification[~invalid&(ea>0)&(vpd>=-1e-7)&(rh>100.05)]="RH_WATER_ABOVE_100"
    return es,ea,rh,classification


def triage(target,panel,centres):
    primary=target.merge(centres,left_on=KEY,right_on=PANEL_KEY,how="left",
                         validate="one_to_one",indicator=True)
    if (len(primary)!=62 or not primary["_merge"].eq("both").all()
        or primary.duplicated(KEY).any()):
        raise ValueError("Target-centre merge lost or duplicated a review record")
    primary=primary.drop(columns="_merge")
    raw_t=numeric(primary,"source_TA_C")
    raw_v=numeric(primary,"source_VPD_hPa")
    cand_t=numeric(primary,"candidate_TA_C")
    cand_v=numeric(primary,"candidate_VPD_hPa")
    era_t=numeric(primary,"ERA_TA_C")
    era_v=numeric(primary,"ERA_VPD_hPa")
    source_es,source_ea,source_rh,classification=classify_original_humidity(raw_t,raw_v)
    _,final_ea,final_rh,final_class=classify_original_humidity(cand_t,cand_v)
    _,era_ea,era_rh,era_class=classify_original_humidity(era_t,era_v)
    if not (np.isfinite(cand_t)&np.isfinite(cand_v)&np.isfinite(final_ea)
        &(final_ea>0)&np.isfinite(final_rh)&(final_rh>0)
        &(final_rh<=100.05)).all():
        raise ValueError("Physically invalid final Stage07 candidate at a priority event")
    review=primary[KEY+["reasons","n_reason_flags"]].copy()
    review["source_T_C"]=raw_t
    review["source_T_QC"]=numeric(primary,"source_TA_QC")
    review["source_VPD_hPa"]=raw_v
    review["source_VPD_QC"]=numeric(primary,"source_VPD_QC")
    review["source_water_es_hPa"]=source_es
    review["source_implied_ea_hPa"]=source_ea
    review["source_water_RH_pct"]=source_rh
    review["original_T_VPD_physics"]=classification
    review["candidate_T_C"]=cand_t
    review["candidate_VPD_hPa"]=cand_v
    review["candidate_implied_ea_hPa"]=final_ea
    review["candidate_water_RH_pct"]=final_rh
    review["candidate_physics"]=final_class
    review["companion_ERA_T_C"]=era_t
    review["companion_ERA_VPD_hPa"]=era_v
    review["companion_ERA_implied_ea_hPa"]=era_ea
    review["companion_ERA_water_RH_pct"]=era_rh
    review["companion_ERA_physics"]=era_class
    with np.errstate(all="ignore"):
        final_ice_sat=np.where(cand_t<0,ice_es(cand_t),water_es(cand_t))
        review["candidate_RH_relative_to_ice_pct"]=100*final_ea/final_ice_sat
    review["source_minus_candidate_VPD_hPa"]=raw_v-cand_v
    review["candidate_minus_source_T_C"]=cand_t-raw_t
    review["science_review_route"]=np.select([
        review.reasons.str.contains("CHANGED_ORIGINAL_QC0",regex=False),
        review.reasons.str.contains("ERA_SOURCE_REPLACEMENT",regex=False),
        review.reasons.str.contains("POSITIVE_RH_BELOW_1PCT",regex=False)
    ],["MEASURED_QC0_T_SOURCE_REVIEW",
       "QC1_VPD_SOURCE_PHYSICS_AND_ERA_REVIEW",
       "POSITIVE_EXTREME_DRY_HUMIDITY_REVIEW"],default="MANUAL_OTHER_REVIEW")
    review["approved_correction"]=False
    review["science_reviewer"]=""
    review["science_notes"]=""
    # Do NOT infer a decision from a numerical check.
    return review


def qc0_neighbor_review(review,panel):
    q=review.loc[review.reasons.str.contains("CHANGED_ORIGINAL_QC0",regex=False)].copy()
    if len(q)!=6 or set(q.variable)!={"TA_F"} or not np.all(q.source_T_QC.eq(0)):
        raise ValueError("Exactly six original TA QC0 changes required")
    lookup={}
    for stamp,g in panel.groupby(PANEL_KEY,sort=False):
        indexed=g.set_index("offset_half_hours",verify_integrity=True)
        lookup[tuple(stamp)]=indexed
    records=[]
    for r in q.itertuples(index=False):
        g=lookup[(r.site,r.native_key,r.variable)]
        left=g.loc[-1];right=g.loc[1]
        t_left=float(left.source_TA_C);t_right=float(right.source_TA_C)
        t_new=float(r.candidate_T_C)
        neighbor_mean=(t_left+t_right)/2
        q_left=float(left.source_TA_QC) if np.isfinite(left.source_TA_QC) else np.nan
        q_right=float(right.source_TA_QC) if np.isfinite(right.source_TA_QC) else np.nan
        records.append({
            "site":r.site,"native_key":r.native_key,
            "source_T_QC0":r.source_T_QC,
            "original_source_T_C":r.source_T_C,
            "candidate_T_C":t_new,
            "ERA_T_C":r.companion_ERA_T_C,
            "previous_source_T_C":t_left,
            "next_source_T_C":t_right,
            "previous_source_T_QC":q_left,
            "next_source_T_QC":q_right,
            "neighbor_mean_T_C":neighbor_mean,
            "candidate_minus_neighbor_mean_C":t_new-neighbor_mean,
            "raw_deviation_from_neighbor_mean_C":r.source_T_C-neighbor_mean,
            "candidate_minus_ERA_C":t_new-r.companion_ERA_T_C,
            "neighbors_are_source_QC0":bool(q_left==0 and q_right==0),
            "raw_neighbor_values_finite":bool(np.isfinite(t_left)&np.isfinite(t_right)),
            "science_decision":"HOLD_UNTIL_MEASURED_QC0_CHANGE_REVIEW"
        })
    return pd.DataFrame(records)


def source_era_replacement_review(review):
    z=review.loc[review.reasons.str.contains("ERA_SOURCE_REPLACEMENT",regex=False)].copy()
    if len(z)!=38 or not z.site.eq("US-NC2").all() or not z.variable.eq("VPD_F").all():
        raise ValueError("Stage11d ERA replacement scope changed")
    if not z.source_VPD_QC.eq(1).all():
        raise ValueError("Expected all 38 original VPD_F QC1 sources")
    z["ERA_vs_final_VPD_abs_diff_hPa"]=(
        z.candidate_VPD_hPa-z.companion_ERA_VPD_hPa).abs()
    z["physical_screen_pass_only"]=z.candidate_implied_ea_hPa.gt(0)
    z["source_was_native_QC1_gapfilled"]=True
    z["review_status"]="HOLD_COMPARE_ORIGINAL_QC1_PAIR_VS_ERA_PHYSICS"
    return z


def summarize(review,era,qc0):
    out=review.groupby("site",sort=True).agg(
        distinct_targets=("variable","size"),
        changed_QC0_temperature=("science_review_route",
            lambda x:int(x.eq("MEASURED_QC0_T_SOURCE_REVIEW").sum())),
        original_source_negative_or_zero_ea=("original_T_VPD_physics",
            lambda x:int(x.eq("NONPOSITIVE_IMPLIED_EA").sum())),
        original_source_negative_VPD=("original_T_VPD_physics",
            lambda x:int(x.eq("NEGATIVE_VPD_SUPERSATURATION").sum())),
        candidate_positive_water_ea=("candidate_implied_ea_hPa",
            lambda x:int(x.gt(0).sum())),
        source_VPD_QC1=("source_VPD_QC",lambda x:int(x.eq(1).sum())),
        low_rh_below_1pct=("candidate_water_RH_pct",
            lambda x:int(x.lt(1).sum()))
    ).reset_index()
    qtypes=era.original_T_VPD_physics.value_counts(dropna=False).rename_axis(
        "original_source_physics").reset_index(name="records")
    return out,qtypes


def self_test():
    t=np.array([-20.,10.,5.,5.])
    v=np.array([3.,1.,-1.,np.nan])
    _,ea,_,cat=classify_original_humidity(t,v)
    assert cat.tolist()==["NONPOSITIVE_IMPLIED_EA","PHYSICALLY_PLAUSIBLE_WATER",
                         "NEGATIVE_VPD_SUPERSATURATION","MISSING_OR_NONFINITE"]
    assert ea[0]<0 and ea[1]>0
    grid=pd.DataFrame({
        "site":["US-MOz"],"native_key":["201601010000"],"variable":["TA_F"],
        "reasons":["CHANGED_ORIGINAL_QC0"],"n_reason_flags":[1]
    })
    panel=pd.DataFrame({
        "target_site":["US-MOz"]*3,
        "target_native_time":["201601010000"]*3,
        "target_variable":["TA_F"]*3,
        "offset_half_hours":[-1,0,1],
        "source_TA_C":[8.,-20.,10.],
        "source_TA_QC":[0.,0.,0.],
        "source_VPD_hPa":[1.,1.,1.],
        "source_VPD_QC":[1.,1.,1.],
        "candidate_TA_C":[8.,9.,10.],
        "candidate_VPD_hPa":[1.,1.,1.],
        "ERA_TA_C":[8.,9.,10.],
        "ERA_VPD_hPa":[1.,1.,1.]
    })
    centre=panel.loc[panel.offset_half_hours.eq(0)]
    review=triage(grid,panel,centre)
    assert len(review)==1 and review.science_review_route.iloc[0]=="MEASURED_QC0_T_SOURCE_REVIEW"
    assert review.approved_correction.eq(False).all()
    print("STAGE11E SELF-TEST PASS: water physics classes, QC0 priority and zero-approval",flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11E — FINAL 62-RECORD SCIENCE TRIAGE | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    targets,panels,centres,pins=read_verified()
    review=triage(targets,panels,centres)
    qc0=qc0_neighbor_review(review,panels)
    era=source_era_replacement_review(review)
    site_summary,qc1_physics=summarize(review,era,qc0)
    five_dry=review.loc[review.reasons.str.contains(
        "POSITIVE_RH_BELOW_1PCT",regex=False)].copy()
    if len(five_dry)!=5 or not (five_dry.candidate_water_RH_pct>0).all():
        raise ValueError("Original five positive extreme-dry targets changed")
    if (len(review)!=62 or len(qc0)!=6 or len(era)!=38
        or review.approved_correction.any()
        or int(site_summary.distinct_targets.sum())!=62):
        raise ValueError("Stage11e science inventory changed")
    print("\n========== SIX QC0 TEMPERATURE NEIGHBOR CHECKS ==========",flush=True)
    print(qc0[["site","native_key","original_source_T_C",
               "previous_source_T_C","next_source_T_C",
               "candidate_T_C","candidate_minus_neighbor_mean_C",
               "neighbors_are_source_QC0"]].to_string(index=False),flush=True)
    print("\n========== 38 US-NC2 QC1 VPD ORIGINAL PHYSICS CLASSES ==========",flush=True)
    print(qc1_physics.to_string(index=False),flush=True)
    print("\n========== 38 QC1 SOURCE VPD REPLACEMENT DETAILS ==========",flush=True)
    print(era[["site","native_key","source_T_C","source_VPD_hPa",
        "source_VPD_QC","original_T_VPD_physics",
        "source_implied_ea_hPa","candidate_VPD_hPa",
        "candidate_water_RH_pct"]].to_string(index=False),flush=True)
    print("\n========== FIVE EXTREMELY LOW BUT POSITIVE RH EVENTS ==========",flush=True)
    print(five_dry[["site","native_key","source_VPD_QC","candidate_T_C",
       "candidate_VPD_hPa","candidate_water_RH_pct",
       "candidate_RH_relative_to_ice_pct"]].to_string(index=False),flush=True)
    print("\n========== SITE CLOSEOUT TRIAGE (NOT APPROVAL) ==========",flush=True)
    print(site_summary.to_string(index=False),flush=True)
    print(f"\nSTAGE11E SUMMARY: review_targets={len(review)}/62 "
          f"original_QC0_T_changes={len(qc0)}/6 "
          f"QC1_VPD_ERA_replacements={len(era)}/38 "
          f"positive_RH_lt1={len(five_dry)}/5 "
          "approved_repairs=0 approved_postv5=0 DATM_ready=0 spinup_authorized=0",flush=True)
    print("SCIENCE HOLD: numerical source inconsistency is not independent proof of a proper replacement.",flush=True)
    if args.check:
        print("CHECK ONLY: no report outputs or source edits.",flush=True)
        return
    foldername="stage11e_science_triage_"+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=ROOT/"reports"/foldername
    out.mkdir(exist_ok=False)
    frames={
        "62_priority_event_physics_and_science_review.csv":review,
        "6_QC0_temperature_neighbor_evidence.csv":qc0,
        "38_QC1_VPD_ERA_replacement_physics.csv":era,
        "38_original_source_physics_category_counts.csv":qc1_physics,
        "5_positive_extreme_dry_events.csv":five_dry,
        "three_site_final_triage_summary.csv":site_summary,
    }
    for name,table in frames.items():
        table.to_csv(out/name,index=False)
    guide="""# Batch03 Stage11e — human-reviewed scientific gate remains CLOSED

All reported original versus ERA vs Stage07 processed_v5 statistics and
neighbor checks are read-only evidence, not an instruction to retain or
revert a measured QC0 modification, use ERA as tower truth or interpolate.

For 6 originally QC0 air temperature values, inspect the upstream tower
instrument, native timestamps, neighbor QC, source-vs-ERA height and potential
bias before any retrospective scientific sign-off.
For 38 US-NC2 original VPD QC1 (MDS/gapfilled) replaced by ERA, inspect the
original source T/VPD joint phase-consistent algebra and reliability of the
downscaled ERA humidity, not only a candidate's mathematical RH positivity.
For 5 water-relative RH <1%, preserve the recorded positive value until
validated instrumentation/metadata/independent humidity evidence justifies
any change. Relative-to-ice values here use a diagnostic phase convention.
Do NOT infer a real water vapour pressure from water/ice algebra alone.

A complete Post-v5 review also includes native clock, site height/elevation,
forest PFT/surface suitability, fixed-vs-historical CO2 strategy, forcing
5-year loop, NO_LEAP, DATM conversion and explicit model science review.
The original Stage07 INCOMPLETE marker stays in place. No new
forcing/Post-v5 or model jobs are authorized by this script.
"""
    (out/"SCIENTIFIC_DECISION_HOLD.md").write_text(guide,encoding="utf-8")
    receipt={
        "version":VERSION,
        "upstream_provenance_SHA256":pins,
        "source_target_records":62,
        "original_QC0_T_change_records":6,
        "native_VPD_QC1_ERA_substitutions":38,
        "positive_extreme_dry_records":5,
        "scientific_repair_approvals":0,"Postv5_approvals":0,
        "DATM_ready":0,"spinup_authorizations":0,
        "Stage07_INCOMPLETE_marker_retained":True,
        "outcome":"SOURCE_PHYSICS_SCIENTIFIC_REVIEW_REQUIRED",
        "outputs_SHA256":{name:sha256(out/name)
                          for name in [*frames,"SCIENTIFIC_DECISION_HOLD.md"]}
    }
    (out/"scientific_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11E REPORT DIR:",out,flush=True)
    print("NO SOURCE, QCv5, POST-V5, DATM, CASE, RESTART OR SLURM MODIFICATIONS.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE11E STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

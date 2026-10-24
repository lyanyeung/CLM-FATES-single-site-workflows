#!/usr/bin/env python3
"""Stage11k: NO-WRITE user review of uncorrected neighbouring RH in Stage11j.

Source: exact 52 original/ERA/Stage07/Stage11h half-hours from the SHA-sealed
Stage11j four-event context file. A review-only *screen* selects source
water RH <10% while paired companion RH >=20% and >=20 percentage points
higher, source VPD QC1/QC2. Distinguishes records ALREADY repaired by
Stage07/Stage11h from ORIGINAL-VPD values unchanged by both.

This threshold is an operator diagnostic to identify possible missed
neighbours, NOT a source-QC rejection or authorisation to ERA5-replace them.
Source companion ERA data are not independently validated tower RH.

--self-test synthetic data only
--check     full SHA read-only audit, prints exactly 11 review suggestions
--run       NEW report CSV and SHA receipt only, NEVER edits forcing.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11k-v1-20261024-11-unchanged-source-neighbour-review"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
S11J=ROOT/"reports/stage11j_four_jump_original_ERA_context_20261024T092017Z_5fc4bfd6"
CONTEXT="52_halfhours_four_events_plus_minus_3h_context.csv"
FOUR="four_human_review_source_ERA_and_shadows.csv"
EXPECTED_CENTRES={
    ("US-Mpj","201802021730"),
    ("US-NC2","202503181900"),
    ("US-NC2","202503231230"),
    ("US-NC2","202503250900")
}
EXPECTED_UNCHANGED={
    ("US-NC2","202503181830"),("US-NC2","202503181930"),
    ("US-NC2","202503231300"),("US-NC2","202503231330"),
    ("US-NC2","202503231400"),("US-NC2","202503231430"),
    ("US-NC2","202503231500"),
    ("US-NC2","202503250800"),("US-NC2","202503250830"),
    ("US-NC2","202503250930"),("US-NC2","202503251000")
}
EXPECTED_ALREADY_STAGE07={
    ("US-Mpj","201802021800"),
    ("US-Mpj","201802021830"),
    ("US-NC2","202503251030")
}
REQUIRED_HASHES={FOUR,CONTEXT,"SCIENTIFIC_HOLD.md"}


def checked_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink input: "+str(p))
    return p


def checked_directory(path):
    p=Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing/symlink input directory: "+str(p))
    return p


def sha(path):
    h=hashlib.sha256()
    with checked_file(path).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()


def sat(temp):
    return 6.112*np.exp(17.67*temp/(temp+243.5))


def implied(temp,vpd):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        es=sat(temp)
        ea=es-vpd
        rh=100*ea/es
    return ea,rh


def source_data():
    for p in (ROOT,S07,S11H,S11J):
        checked_directory(p)
    checked_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    checked_file(S11H/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    seal=json.loads(checked_file(S11J/"read_only_four_event_receipt.json").read_text(encoding="utf-8"))
    if (seal.get("version")!="stage11j-v1-20261024-four-introduced-VPD-jumps-context"
        or seal.get("hotspot_records")!=4
        or seal.get("context_rows")!=52
        or seal.get("introduced_jump_over5hPa")!=2
        or seal.get("scientific_decisions_signed")!=0
        or seal.get("clock_offsets_approved")!=0
        or seal.get("Postv5_approved")!=0
        or seal.get("DATM_ready")!=0
        or seal.get("spinup_authorizations")!=0
        or seal.get("Stage11h_sha_receipt_SHA256")!=sha(S11H/"sha_sealed_shadow_trial_receipt.json")
        or seal.get("Stage07_manifest_SHA256")!=sha(S07/"exact_input_manifest.json")
        or set(seal.get("output_sha256",{}))!=REQUIRED_HASHES):
        raise ValueError("Stage11j sealed provenance or no-approval gate differs")
    for filename,expected in seal["output_sha256"].items():
        if sha(S11J/filename)!=expected:
            raise ValueError("Stage11j SHA differs: "+filename)
    context=pd.read_csv(checked_file(S11J/CONTEXT),
        dtype={"centre_native_key":str,"native_key":str},low_memory=False)
    centres=pd.read_csv(checked_file(S11J/FOUR),
        dtype={"native_key":str},low_memory=False)
    if len(context)!=52 or len(centres)!=4:
        raise ValueError("Stage11j number of context/central records changed")
    centre_set=set(zip(centres.site,centres.native_key))
    if centre_set!=EXPECTED_CENTRES or set(zip(context.centre_site,context.centre_native_key))!=EXPECTED_CENTRES:
        raise ValueError("Four reviewed native centres changed")
    if context.duplicated(["centre_site","centre_native_key","offset_half_hours"]).any():
        raise ValueError("Duplicate half-hour source context")
    for (site,key),g in context.groupby(["centre_site","centre_native_key"]):
        if sorted(g.offset_half_hours.astype(int).tolist())!=list(range(-6,7)):
            raise ValueError("Missing context offsets "+site+" "+key)
        t0=pd.to_datetime(key,format="%Y%m%d%H%M")
        for rec in g.itertuples(index=False):
            expected=(t0+pd.Timedelta(minutes=int(rec.offset_half_hours)*30)).strftime("%Y%m%d%H%M")
            if rec.native_key!=expected:
                raise ValueError("Source-native half-hour clock misaligned "+site+" "+key)
    return context,seal


def evaluate(context):
    x=context.copy(deep=True)
    for name in ["original_TA_F_C","original_VPD_F_hPa",
        "original_VPD_F_QC","companion_ERA_T_C","companion_ERA_VPD_hPa",
        "companion_ERA_RH_water_pct","stage07_candidate_VPD_hPa",
        "Stage11h_trial_VPD_hPa","original_implied_ea_hPa",
        "original_implied_RH_water_pct"]:
        x[name]=pd.to_numeric(x[name],errors="coerce")
    ea,rh=implied(x.original_TA_F_C.to_numpy(dtype=float),
                  x.original_VPD_F_hPa.to_numpy(dtype=float))
    era_ea,era_rh=implied(x.companion_ERA_T_C.to_numpy(dtype=float),
        x.companion_ERA_VPD_hPa.to_numpy(dtype=float))
    if (not np.isfinite(ea).all() or not np.isfinite(rh).all()
        or not np.isfinite(era_ea).all() or not np.isfinite(era_rh).all()
        or not np.allclose(ea,x.original_implied_ea_hPa.to_numpy(),rtol=0,atol=1e-7)
        or not np.allclose(rh,x.original_implied_RH_water_pct.to_numpy(),rtol=0,atol=1e-6)
        or not np.allclose(era_rh,x.companion_ERA_RH_water_pct.to_numpy(),rtol=0,atol=1e-6)):
        raise ValueError("Stage11j source and ERA relative humidity recomputation differs")
    x["science_original_source_water_RH_pct"]=rh
    x["science_companion_ERA_water_RH_pct"]=era_rh
    x["ERA_minus_original_RH_percentage_points"]=era_rh-rh
    x["Stage07_VPD_same_as_original"]=np.isclose(
        x.original_VPD_F_hPa.to_numpy(),x.stage07_candidate_VPD_hPa.to_numpy(),
        rtol=0,atol=1e-7)
    x["Stage11h_VPD_same_as_original"]=np.isclose(
        x.original_VPD_F_hPa.to_numpy(),x.Stage11h_trial_VPD_hPa.to_numpy(),
        rtol=0,atol=1e-7)
    x["Stage11h_modified_from_Stage07"]=~np.isclose(
        x.stage07_candidate_VPD_hPa.to_numpy(),x.Stage11h_trial_VPD_hPa.to_numpy(),
        rtol=0,atol=1e-7)
    screen=((rh<10)&(era_rh>=20)&((era_rh-rh)>=20)&
        x.original_VPD_F_QC.ge(1).to_numpy()&
        x.original_VPD_F_QC.le(2).to_numpy())
    x["review_only_source_ERA_humidity_discrepancy_screen"]=screen
    x["review_proposed_source_original_unchanged"]=(
        screen & x.Stage07_VPD_same_as_original.to_numpy() &
        x.Stage11h_VPD_same_as_original.to_numpy())
    x["review_source_previously_repaired_by_Stage07"]=(
        screen & ~x.Stage07_VPD_same_as_original.to_numpy() &
        ~x.Stage11h_modified_from_Stage07.to_numpy())
    x["scientific_acceptance"]="HOLD_CONTEXT_ONLY_NO_AUTOMATIC_REPAIR"
    fresh=x.loc[x.review_proposed_source_original_unchanged].copy()
    fixed=x.loc[x.review_source_previously_repaired_by_Stage07].copy()
    if (len(fresh)!=11 or len(fixed)!=3 or int(screen.sum())!=18):
        # Four corrected centres also pass screen. 11+3+4=18.
        raise ValueError("Expected Stage11j review flag census 11 uncorrected + 3 Stage07 + 4 Stage11h")
    if (set(zip(fresh.centre_site,fresh.native_key))!=EXPECTED_UNCHANGED or
        set(zip(fixed.centre_site,fixed.native_key))!=EXPECTED_ALREADY_STAGE07):
        raise ValueError("Unexpected neighbour native keys in Stage11k science screen")
    # At the 4 centres, Stage11h must differ from Stage07; they are NOT new neighbours.
    centres=x.loc[x.offset_half_hours.eq(0)]
    if len(centres)!=4 or not centres.Stage11h_modified_from_Stage07.all():
        raise ValueError("One of four Stage11j centre changes is absent")
    return x,fresh,fixed,centres


def self_test():
    t=np.array([15.,10.,5.])
    v=np.array([15.,5.,10.])
    ea,rh=implied(t,v)
    assert len(rh)==3 and ea[2]<0 and np.isfinite(rh).all()
    assert np.isclose(float(implied(np.array([20.]),np.array([0.]))[1][0]),100.)
    print("STAGE11K SELF-TEST PASS: source/ERA liquid-water RH, modified/unmodified separation and held scientific gate",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE11K — FOUR-EVENT NEIGHBOUR SOURCE HUMIDITY HOLD | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    raw,seal=source_data()
    detail,new,already,centres=evaluate(raw)
    print("\n========== 11 UNMODIFIED NEIGHBOUR SOURCE RH DISCREPANCIES ==========",flush=True)
    print(new[["centre_site","native_key","original_VPD_F_QC",
        "science_original_source_water_RH_pct",
        "science_companion_ERA_water_RH_pct",
        "ERA_minus_original_RH_percentage_points"]].to_string(index=False),
        flush=True)
    print("\n========== 3 ALREADY STAGE07 REPAIRED NEIGHBOURS — DO NOT REWRITE ==========",flush=True)
    print(already[["centre_site","native_key","original_VPD_F_QC",
        "science_original_source_water_RH_pct",
        "science_companion_ERA_water_RH_pct",
        "stage07_candidate_VPD_hPa"]].to_string(index=False),flush=True)
    print("\n========== FOUR STAGE11H CORRECTED CENTRES — ALREADY HANDLED ==========",flush=True)
    print(centres[["centre_site","native_key","stage07_candidate_VPD_hPa",
        "Stage11h_trial_VPD_hPa"]].to_string(index=False),flush=True)
    print(f"\nSTAGE11K SUMMARY: source_context=52/52 source_discrepancy_flags=18 "
          f"unmodified_neighbour_science_review=11 "
          f"already_Stage07_repaired=3 already_Stage11h_centres=4 "
          "new_repair_approvals=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: NO new report, source, forcing or model writes.",flush=True)
        return
    report=ROOT/"reports"/("stage11k_four_event_neighbour_RH_review_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    report.mkdir(exist_ok=False)
    outputs={
        "all_52_original_vs_ERA_RH_source_context.csv":detail,
        "11_unmodified_neighbour_science_holds.csv":new,
        "3_already_Stage07_corrected_neighbour_comparisons.csv":already,
        "4_previously_user_selected_Stage11h_centres.csv":centres
    }
    for name,frame in outputs.items():
        frame.to_csv(report/name,index=False)
    note="""# Stage11k read-only 11 neighbouring-source humidity science HOLD

The 11 flagged original QC1/QC2 source timestamps had original water RH
<10%, release companion site-downscaled ERA RH >=20%, and a >=20 percentage
point discrepancy, and were unchanged by Stage07 and Stage11h. Three
other flagged source timestamps were already amended by Stage07; four
were Stage11h-corrected centres. No extra VPD/QBOT values were written.

These are diagnostic *suggestions*, NOT evidence that the reanalysis RH
is tower ground truth. They are not automatically adopted into the
previous human-approved 53 selected humidity source points. Before
changing one of the 11, the user must independently inspect contiguous
source QC, instrument/clock/height/source issues, and choose a new
explicit versioned review decision. Keep both original Stage07 and
Stage11h INCOMPLETE markers, never start DATM, CIME or Slurm.
"""
    (report/"SCIENTIFIC_HOLD_README.md").write_text(note,encoding="utf-8")
    receipt={
        "version":VERSION,
        "Stage11j_receipt_sha256":sha(S11J/"read_only_four_event_receipt.json"),
        "Stage11h_receipt_sha256":sha(S11H/"sha_sealed_shadow_trial_receipt.json"),
        "Stage07_manifest_sha256":sha(S07/"exact_input_manifest.json"),
        "context_rows":52,"source_humidity_discrepancy_flags":18,
        "new_unmodified_neighbour_review":11,
        "previously_Stage07_repaired":3,
        "previously_Stage11h_centres":4,
        "scientific_repair_approvals":0,"Postv5_approved":0,
        "DATM_ready":0,"spinup_authorized":0,
        "output_sha256":{name:sha(report/name) for name in [
            *outputs,"SCIENTIFIC_HOLD_README.md"]}
    }
    (report/"stage11k_read_only_scientific_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11K REVIEW REPORT DIR:",report,flush=True)
    print("NO SOURCES, STAGE07/STAGE11H, DATM/CIME/SLURM MODIFIED.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("STAGE11K STOP:",str(e),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

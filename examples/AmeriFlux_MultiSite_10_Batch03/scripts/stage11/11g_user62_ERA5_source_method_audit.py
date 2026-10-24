#!/usr/bin/env python3
"""Batch03 Stage11g: SHA-backed human decisions + paired ERA5 source/method audit.

No meteorological output data are changed. This script does not assume that
the FLUXNET site-downscaled, release-paired ERA companion is the same as a
separately downloaded ERA5-Land T2m/Td2m product. It tests available
companion-ERA VPD in two DIFFERENT ways, with exact source-native keys:
 (A) direct source companion ERA VPD at preserved Stage07 tower TA;
 (B) ERA-companion *RH* transferred to preserved Stage07 tower TA,
     reconstructing VPD and physically consistent QBOT with Stage07 PSRF.
Neither method is automatically selected or approved. The user's request
"ERA5-based humidity" remains method/source-validation pending until a
documented product and reconstruction rule are explicitly frozen.

Other decisions: six Stage07 TA candidates and three Stage07 VPD candidates
are retained as *user-selected choices*, NOT new forcing, QC changes or
full Post-v5 approval. The seven other sites are OUT OF SCOPE.

--self-test : synthetic temperature/humidity/QBOT test only; NO IRIDIS input.
--check     : SHA checks, native-source pairing and 62-decision reconciliation;
              printed summaries, NO outputs.
--run       : isolated reports/stage11g_* diagnostic CSV + SHA receipt ONLY.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11g-v1-20261024-user62-ERA5-companion-methods"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11F=ROOT/"reports/stage11f_human_science_review_20261024T074958Z_6ae6d5d7"
REPO=Path.home()/"CLM-FATES-single-site-workflows"
BASE=REPO/"examples/AmeriFlux_MultiSite_10_Batch03"
LEDGER=BASE/"docs/STAGE11F_ALL62_USER_DECISIONS_2026-10-24.csv"
LEDGER_BLOB="335c87e12d357714580018f8bab34fa4dde23446"
UPSTREAM=BASE/"scripts/stage11/11c_qc0_manual_era_change_review.py"
UPSTREAM_BLOB="2e7402fc67fabe34aeeb990d98117730bcbbddfa"
SITES=("US-MOz","US-Mpj","US-NC2")
ID=("site","native_key","variable")
TA_RULE="KEEP_EXISTING_STAGE07_CANDIDATE_TA"
VPD_ERA_RULE="ERA5_BASED_HUMIDITY_METHOD_SELECTED"
VPD_KEEP_RULE="KEEP_EXISTING_STAGE07_CANDIDATE_VPD"
CATEGORIES={
    "QC0_T_CHANGED":6,
    "SOURCE_NONPOSITIVE_IMPLIED_EA":49,
    "FINAL_POSITIVE_RH_BELOW_1PCT":4,
    "ORIGINAL_POSITIVE_NEAR_ZERO_EA":3
}

def checked_file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink file: "+str(p))
    return p


def checked_dir(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or symlink directory: "+str(p))
    return p


def sha256(p):
    h=hashlib.sha256()
    with checked_file(p).open("rb") as f:
        for buf in iter(lambda:f.read(1<<20),b""):
            h.update(buf)
    return h.hexdigest()


def blob(p):
    contents=checked_file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(contents)).encode()+b"\0"+contents).hexdigest()


def jsonfile(p):
    return json.loads(checked_file(p).read_text(encoding="utf-8"))


def num(v):
    try:
        x=float(v)
    except (TypeError,ValueError):
        return float("nan")
    if not np.isfinite(x) or x<=-9990:
        return float("nan")
    return x


def es_water(t):
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*np.asarray(t)/(np.asarray(t)+243.5))


def physical_candidate(ta_c,pa,era_t,era_vpd):
    """Physics ONLY; input VPD in hPa and PSRF in Pa.

    A: source companion VPD copied at preserved candidate site TA;
    B: companion ERA-water-RH transferred to site TA. No clipping/floors.
    """
    ta,pressure,te,ve=map(num,(ta_c,pa,era_t,era_vpd))
    es_site=float(es_water(ta)) if np.isfinite(ta) else float("nan")
    es_era=float(es_water(te)) if np.isfinite(te) else float("nan")
    if np.isfinite(es_era) and es_era>0 and np.isfinite(ve):
        rh_era=(es_era-ve)/es_era
    else:
        rh_era=float("nan")
    direct_ea=es_site-ve
    direct_rh_pct=100*direct_ea/es_site if es_site>0 else float("nan")
    direct_pass=bool(
        np.isfinite([es_site,ve,direct_ea,direct_rh_pct,pressure]).all()
        and 0<direct_ea<=es_site*1.0005 and 0<=ve and 49000<=pressure<=111000)
    # Do NOT clamp source negative RH, and NEVER make 1% a floor.
    era_pair_pass=bool(np.isfinite(rh_era) and 0<rh_era<=1)
    transfer_vpd=es_site*(1-rh_era) if era_pair_pass else float("nan")
    ea_site=es_site*rh_era if era_pair_pass else float("nan")
    ea_pa=ea_site*100
    denominator=pressure-0.378*ea_pa
    q=0.622*ea_pa/denominator if np.isfinite(denominator) and denominator>0 else float("nan")
    transfer_pass=bool(era_pair_pass and
        np.isfinite([ta,pressure,transfer_vpd,ea_pa,q]).all()
        and 49000<=pressure<=111000 and 0<=transfer_vpd<es_site
        and 0<q<0.08)
    if not transfer_pass:
        transfer_vpd=float("nan")
        q=float("nan")
    return {
        "paired_ERA_es_water_hPa":es_era,
        "paired_ERA_source_water_RH_pct":rh_era*100,
        "paired_ERA_pair_has_positive_ea":era_pair_pass,
        "direct_companion_VPD_at_candidate_T_ea_hPa":direct_ea,
        "direct_companion_VPD_at_candidate_T_RH_pct":direct_rh_pct,
        "direct_copy_water_physics_pass":direct_pass,
        "RH_transfer_water_physics_pass":transfer_pass,
        "RH_transfer_VPD_hPa_preview":transfer_vpd,
        "RH_transfer_QBOT_kgkg_preview":q
    }


def get_stage11c():
    if blob(UPSTREAM)!=UPSTREAM_BLOB:
        raise ValueError("Stage11c source blob differs from science-verified version")
    spec=importlib.util.spec_from_file_location("batch03_source_11c",UPSTREAM)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger_and_seal():
    for p in (ROOT,S07,S11F,BASE):
        checked_dir(p)
    checked_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    if blob(LEDGER)!=LEDGER_BLOB:
        raise ValueError("GitHub 62-choice ledger blob differs; download pinned CSV")
    f=jsonfile(S11F/"read_only_scientific_hold_receipt.json")
    if (f.get("version")!="stage11f-v1-20261024-manual-scientific-review-queue"
        or f.get("stage11e_exact_events")!=62
        or f.get("signed_scientific_decisions")!=0
        or f.get("post_v5_approvals")!=0
        or f.get("DATM_ready")!=0
        or f.get("spinup_authorizations")!=0
        or f.get("stage07_incomplete_hold_retained") is not True):
        raise ValueError("Stage11f sealed receipt changed or user gate already modified")
    source=S11F/"62_human_scientific_review_queue.csv"
    if sha256(source)!=f.get("output_sha256",{}).get(source.name):
        raise ValueError("Stage11f original 62-row SHA has changed")
    decisions=pd.read_csv(LEDGER,dtype={"native_key":str},keep_default_na=False)
    orig=pd.read_csv(source,dtype={"native_key":str},keep_default_na=False)
    if (len(decisions)!=62 or len(orig)!=62
        or decisions.duplicated(list(ID)).any() or orig.duplicated(list(ID)).any()):
        raise ValueError("Stage11f decision or sealed source count/ID mismatch")
    if set(map(tuple,decisions[list(ID)].to_numpy()))!=set(
         map(tuple,orig[list(ID)].to_numpy())):
        raise ValueError("User ledger IDs differ from sealed Stage11f IDs")
    if decisions.science_class.value_counts().to_dict()!=CATEGORIES:
        raise ValueError("62 user science-class census changed")
    counts=decisions.human_decision.value_counts().to_dict()
    if counts!={TA_RULE:6,VPD_ERA_RULE:53,VPD_KEEP_RULE:3}:
        raise ValueError("User decisions must be 6/53/3")
    if (decisions[["post_v5_approved","DATM_ready","spinup_authorized"]]
        .apply(lambda s:s.astype(str).str.lower().ne("false").any()).any()):
        raise ValueError("User science method choices do not grant model approval")
    detailed=decisions.merge(orig,on=list(ID),how="left",validate="one_to_one",
                             indicator=True,suffixes=("","_sealed"))
    if not detailed["_merge"].eq("both").all():
        raise ValueError("Decision to source join is not one-to-one")
    detailed.drop(columns="_merge",inplace=True)
    for r in detailed.itertuples(index=False):
        if (r.science_class=="QC0_T_CHANGED" and
            (r.variable!="TA_F" or r.human_decision!=TA_RULE)):
            raise ValueError("Measured QC0 T user method mismatch")
        if (r.science_class=="SOURCE_NONPOSITIVE_IMPLIED_EA" and
            (r.original_source_physics!="NONPOSITIVE_IMPLIED_EA"
            or r.variable!="VPD_F" or r.human_decision!=VPD_ERA_RULE)):
            raise ValueError("Original physically invalid vapor category mismatch")
        if (r.science_class=="FINAL_POSITIVE_RH_BELOW_1PCT" and
            (r.variable!="VPD_F" or not (0<float(r.candidate_water_RH_pct)<1)
            or r.human_decision!=VPD_ERA_RULE)):
            raise ValueError("Positive extreme-dry category mismatch")
        if (r.science_class=="ORIGINAL_POSITIVE_NEAR_ZERO_EA" and
            (r.original_source_physics!="PHYSICALLY_PLAUSIBLE_WATER"
            or r.variable!="VPD_F" or r.human_decision!=VPD_KEEP_RULE)):
            raise ValueError("Three retained source-positive VPD ids changed")
    key3=set(map(tuple,detailed.loc[detailed.human_decision.eq(VPD_KEEP_RULE),
                          ["site","native_key"]].to_numpy()))
    expected3={("US-Mpj","201410210830"),
       ("US-NC2","202503220130"),("US-NC2","202503270730")}
    if key3!=expected3:
        raise ValueError("Three expressly retained Stage07 VPD choices mismatch")
    return detailed,orig,f


def paired_site_audit(c,rows,specs,pins,outputs):
    records=[]
    for site in SITES:
        raw,force,era,changes,manual,lowrh,lowdec,status,audit=c.read_site(
             site,specs[site],pins,outputs)
        primary_idx=raw.set_index("native_key",verify_integrity=True)
        force_idx=force.set_index("native_key",verify_integrity=True)
        era_idx=era.set_index("TIMESTAMP_START",verify_integrity=True)
        for r in rows.loc[rows.site.eq(site)].itertuples(index=False):
            key=r.native_key
            if not (key in primary_idx.index and
                    key in force_idx.index and key in era_idx.index):
                raise ValueError("Exact native source/ERA/Stage07 time mismatch: "+site+" "+key)
            a,b,e=primary_idx.loc[key],force_idx.loc[key],era_idx.loc[key]
            ta=num(b["TA_USE"])
            vpd=num(b["VPD_USE"])
            pressure=num(b["PSRF"])
            q_current=num(b["QBOT"])
            sat=float(es_water(ta))
            ea=sat-vpd
            q_math=0.622*(ea*100)/(pressure-0.378*(ea*100))
            if not (np.isfinite([ta,vpd,pressure,q_current,q_math]).all()
                and 0<ea<=sat*1.0005 and abs(q_math-q_current)<1e-8):
                raise ValueError("Existing Stage07 forcing physics inconsistent: "+site+" "+key)
            ex=physical_candidate(ta,pressure,e["TA_ERA"],e["VPD_ERA"])
            record={
                "site":site,"native_key":key,"variable":r.variable,
                "user_decision":r.human_decision,
                "science_class":r.science_class,
                "source_TA_F_C":num(a["TA_F"]),
                "source_TA_QC":num(a["TA_F_QC"]),
                "source_VPD_F_hPa":num(a["VPD_F"]),
                "source_VPD_QC":num(a["VPD_F_QC"]),
                "stage07_candidate_TA_C":ta,
                "stage07_candidate_VPD_hPa":vpd,
                "stage07_candidate_RH_pct":100*ea/sat,
                "stage07_candidate_QBOT":q_current,
                "stage07_PSFR_Pa":pressure,
                "paired_companion_ERA_T_C":num(e["TA_ERA"]),
                "paired_companion_ERA_VPD_hPa":num(e["VPD_ERA"]),
                "ERA5_Land_grid_dewpoint_method":"NOT_EVALUATED_NO_PINNED_SITE_GRID_T_Td_PRODUCT",
                "selected_final_ERA5_method":"UNSPECIFIED_PENDING_USER_SOURCE_AND_METHOD_REVIEW",
                **ex
            }
            record["candidate_method_comparison"] = (
                "KEEP_STAGE07_AS_SELECTED" if r.human_decision in (TA_RULE,VPD_KEEP_RULE)
                else ("COMPANION_RH_TRANSFER_NUMERIC_PASS_ONLY" if ex[
                  "RH_transfer_water_physics_pass"] else
                  "COMPANION_RH_TRANSFER_FAIL_OR_MISSING"))
            record["human_science_choice_recorded"]=True
            record["post_v5_approved"]=False
            record["DATM_ready"]=False
            record["spinup_authorized"]=False
            records.append(record)
        print(f"STAGE11G VERIFIED SOURCE {site}: records="
              f"{len(rows.loc[rows.site.eq(site)])} native keys, SHA and QBOT OK",flush=True)
    out=pd.DataFrame(records)
    if len(out)!=62 or out.duplicated(list(ID)).any():
        raise ValueError("Lost/duplicate record after native-source/ERA method audit")
    return out


def self_test():
    ok=physical_candidate(10,101325,10,5)
    assert ok["paired_ERA_pair_has_positive_ea"]
    assert ok["direct_copy_water_physics_pass"]
    assert ok["RH_transfer_water_physics_pass"]
    assert 0<ok["RH_transfer_QBOT_kgkg_preview"]<0.08
    # Passing physical constraints is NOT an approval of the source.
    bad=physical_candidate(5,101325,5,30)
    assert not bad["paired_ERA_pair_has_positive_ea"]
    assert not bad["RH_transfer_water_physics_pass"]
    assert np.isnan(bad["RH_transfer_VPD_hPa_preview"])
    mismatch=physical_candidate(-15,101325,20,20)
    assert not mismatch["direct_copy_water_physics_pass"]
    print("STAGE11G SELF-TEST PASS: positive and invalid ERA source RH, source VPD at retained T, QBOT algebra, NO REPAIRS",flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11G — 62 USER DECISIONS + ACTUAL ERA5-COMPANION SCIENCE | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    c=get_stage11c()
    ledger,orig,receipt=ledger_and_seal()
    specs,pins,outputs,_=c.load_and_verify_inputs()
    paired=paired_site_audit(c,ledger,specs,pins,outputs)
    vpd=paired.loc[paired.user_decision.eq(VPD_ERA_RULE)].copy()
    retained=paired.loc[~paired.user_decision.eq(VPD_ERA_RULE)].copy()
    if len(vpd)!=53 or len(retained)!=9:
        raise ValueError("ERA5 and retained candidates changed from 53/9 decision scope")
    passed=int(vpd.RH_transfer_water_physics_pass.sum())
    direct=int(vpd.direct_copy_water_physics_pass.sum())
    failures=vpd.loc[~vpd.RH_transfer_water_physics_pass].copy()
    print("\n========== 62 USER METHOD CHOICES ==========",flush=True)
    print(paired.groupby(["site","user_decision"]).size().to_string(),flush=True)
    print("\n========== 53 ERA5 HUMIDITY METHOD OPTIONS, NUMERIC ONLY ==========",flush=True)
    print(f"RETAIN TOWER TA + COPY COMPANION ERA VPD: physical_pass={direct}/53")
    print(f"RETAIN TOWER TA + TRANSFER COMPANION ERA RH: physical_pass={passed}/53")
    print(f"TRANSFER NUMERIC FAILURE/NO-VALID-ERA PAIR={len(failures)}/53")
    print("SEPARATELY DOWNLOADED ERA5-LAND GRID T2m/Td2m: NOT EVALUATED OR APPROVED")
    print("ERA5 PRODUCT/METHOD SCIENTIFIC ACCEPTANCE: 0; source clock/height unresolved")
    if len(failures):
        print("\n========== ERA RH TRANSFER FAILING RECORDS ==========",flush=True)
        print(failures[["site","native_key","paired_companion_ERA_T_C",
            "paired_companion_ERA_VPD_hPa",
            "paired_ERA_source_water_RH_pct"]].to_string(index=False),flush=True)
    print("\n========== KEEP THREE EXISTING STAGE07 VPD ==========",flush=True)
    print(retained.loc[retained.user_decision.eq(VPD_KEEP_RULE),[
         "site","native_key","stage07_candidate_VPD_hPa",
         "stage07_candidate_RH_pct","stage07_candidate_QBOT"]].to_string(index=False),flush=True)
    print(f"\nSTAGE11G SUMMARY: decisions={len(paired)}/62 candidate_TA_kept=6/6 "
          f"ERA5_method_selected=53/53 Stage07_VPD_kept=3/3 "
          "approved_Postv5=0 DATM_ready=0 spinup_authorizations=0",flush=True)
    if args.check:
        print("CHECK ONLY: no new reports, source, forcing or model modifications.",flush=True)
        return
    dest=ROOT/"reports"/("stage11g_user62_ERA5_method_validation_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    dest.mkdir(exist_ok=False)
    docs={
        "62_user_choice_source_companion_preview.csv":paired,
        "53_ERA5_humidity_method_comparisons.csv":vpd,
        "ERA_RH_transfer_failures_review.csv":failures,
        "9_retained_Stage07_TA_and_VPD_checks.csv":retained
    }
    for name,table in docs.items():
        table.to_csv(dest/name,index=False)
    note="""# Stage11g: numerical ERA5 companion methods, NOT approved forcing

User selected: six Stage07 temperature candidates; 53 ERA5-based humidity
replacements (original negative/nonpositive implied vapour or RH<1%); three
Stage07 existing humidity candidates. All 62 are represented exactly once.

The **two distinct ERA companion methods** are compared using the
SHA-pinned site-downscaled ERA5_HH companion and release-specific
TIMESTAMP_START, NOT an independently downloaded ERA5-Land product:
- Direct VPD_ERA paired with preserved site temperature.
- Transfer ERA relative humidity inferred from companion TA_ERA/VPD_ERA
  to preserved site temperature; infer VPD and QBOT at Stage07 PSRF.
Any nonpositive ERA RH, VPD outside water-saturation, missing values
or pressure-specific-humidity failures are marked, never silently clipped.
No extrapolation or alignment by row number is permitted.
Numerical success alone is not tower meteorology validation.
A separately sourced ERA5-Land grid T and dewpoint method requires
its own pinned files, exact clock, elevation and independent review.

Stage07 sealed INCOMPLETE marker MUST remain; no raw files or source-
preserved trial / DATM / CIME / Slurm changed. Three KEEP_STAGE07 VPD
choices and six TA choices remain the existing values, NOT approval to
alter a sealed source file. Before any forcing change: freeze source
product, conversion and QC uncertainty; review whole site-year forcing,
source clock, PFT/surface and CO2 strategy, and create a new isolated
candidate with explicit signed science gate.
"""
    (dest/"METHOD_SELECTION_HOLD.md").write_text(note,encoding="utf-8")
    receipt_out={
        "version":VERSION,
        "git_decisions_csv_blob":LEDGER_BLOB,
        "GitHub_decision_csv_SHA256":sha256(LEDGER),
        "Stage11f_receipt_SHA256":sha256(S11F/"read_only_scientific_hold_receipt.json"),
        "Stage07_exact_manifest_SHA256":sha256(S07/"exact_input_manifest.json"),
        "decisions":62,"keep_Stage07_TA":6,"ERA5_method_choice":53,
        "keep_Stage07_VPD":3,"companion_ERA_RH_transfer_numeric_pass":passed,
        "companion_ERA_direct_VPD_numeric_pass":direct,
        "ERA5_Land_grid_product_verified":False,
        "selected_ERA5_source_method_frozen":False,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorizations":0,
        "stage07_incomplete_marker_retained":True,
        "outputs_sha256":{name:sha256(dest/name) for name in [
            *docs,"METHOD_SELECTION_HOLD.md"]}
    }
    (dest/"read_only_ERA5_method_receipt.json").write_text(
        json.dumps(receipt_out,indent=2)+"\n",encoding="utf-8")
    print("STAGE11G REPORT DIR:",dest,flush=True)
    print("NO ORIGINAL/PROCESSED FORCING, STAGE07/11F, DATM, CASE OR SLURM CHANGES.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE11G STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

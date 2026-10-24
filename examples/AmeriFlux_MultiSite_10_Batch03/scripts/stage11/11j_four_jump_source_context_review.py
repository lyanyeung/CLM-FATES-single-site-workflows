#!/usr/bin/env python3
"""Stage11j — SHA-protected 4-event VPD discontinuity SOURCE context review.

Reads existing SHA-sealed Stage07 and Stage11h CSVs and the exact-release
FLUXMET/companion ERA source, using verified Stage11i and Stage11c readers.
Finds the FOUR newly increased >2hPa VPD-jump event IDs independently
and collects +/-3 hours native (NO clock shift) at all four events.

--self-test  synthetic classification and source pair RH
--check      full read-only audit; prints 4 event table
--run        only NEW reports/stage11j_* CSVs and SHA receipt
Never touches input/forcing, existing Stage07/11h, DATM/CIME/Slurm.
"""
import argparse
from datetime import datetime,timezone
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
VERSION="stage11j-v1-20261024-four-introduced-VPD-jumps-context"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
REPO=Path.home()/"CLM-FATES-single-site-workflows"/"examples/AmeriFlux_MultiSite_10_Batch03"/"scripts"/"stage11"
STAGE11I=REPO/"11i_three_site_shadow_impact_audit.py"
STAGE11I_BLOB="4504ceacf056ec6d51346d15cf51feaedfb89bba"
STAGE11C=REPO/"11c_qc0_manual_era_change_review.py"
STAGE11C_BLOB="2e7402fc67fabe34aeeb990d98117730bcbbddfa"
HOTSPOTS={
    ("US-Mpj","201802021730"):("QC2_SOURCE_EXTREME_DRY",2.286140),
    ("US-NC2","202503181900"):("SOURCE_NEGATIVE_VAPOR_AND_DRY",3.706716),
    ("US-NC2","202503231230"):("POSITIVE_EXTREME_DRY_AT_38_EVENT_BOUNDARY",9.761132),
    ("US-NC2","202503250900"):("POSITIVE_EXTREME_DRY",8.227839),
}
SITES=("US-Mpj","US-NC2")


def safe_file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/unsafe file: "+str(p))
    return p


def sha(p):
    h=hashlib.sha256()
    with safe_file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def blob(p):
    b=safe_file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()


def load_module(path,blob_expected,name):
    if blob(path)!=blob_expected:
        raise ValueError("Verified module changed: "+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def numeric(v):
    try:
        z=float(v)
        return z if np.isfinite(z) and z>-9990 else float("nan")
    except (TypeError,ValueError):
        return float("nan")


def water_sat(temp):
    return 6.112*np.exp(17.67*temp/(temp+243.5)) if np.isfinite(temp) else float("nan")


def source_pair(temp,vpd):
    if not np.isfinite(temp) or not np.isfinite(vpd):
        return float("nan"),float("nan")
    s=water_sat(temp)
    ea=s-vpd
    return ea,100*ea/s


def synthetic_test():
    a,b=source_pair(20.,5.)
    assert a>0 and 0<b<100
    a,b=source_pair(0.,12.)
    assert a<0 and b<0
    table=pd.DataFrame({"site":["US-NC2"]*3,
                        "native_key":["202503181900","202503231230","202503250900"],
                        "max_ADDED_adjacent_jump_hPa":[3.706716,9.761132,8.227839]})
    assert len(table.loc[table.max_ADDED_adjacent_jump_hPa.gt(5)])==2
    assert set(zip(table.site,table.native_key))=={
        x for x in HOTSPOTS if x[0]=="US-NC2"}
    print("STAGE11J SELF-TEST PASS: source vapour signs, four-event identity and 2 over 5 hPa flags",flush=True)


def audit():
    i=load_module(STAGE11I,STAGE11I_BLOB,"stage11i_verified_for_11j")
    c=load_module(STAGE11C,STAGE11C_BLOB,"stage11c_verified_for_11j")
    evidence,_,seal,_=i.safe_preflight()
    specs,pins,output_seals,_=c.load_and_verify_inputs()
    if set(HOTSPOTS)!={
         ("US-Mpj","201802021730"),
         ("US-NC2","202503181900"),
         ("US-NC2","202503231230"),
         ("US-NC2","202503250900")}:
        raise ValueError("Four reviewed native targets changed")
    contexts=[]
    review=[]
    for site in SITES:
        old,shadow=i.full_site(site,seal)
        impact,_,metrics=i.phase_audit(site,old,shadow,evidence)
        top=impact.loc[impact.max_ADDED_adjacent_jump_hPa.gt(2.0)].copy()
        these={t for t in HOTSPOTS if t[0]==site}
        found=set(zip(top.site,top.native_key))
        if found!=these:
            raise ValueError("Actual >2hPa added-jump IDs differ: "+site+" "+str(found))
        # Same SHA-proven source parsing/matching previously validated by Stage11g.
        raw,v5,era,_,_,_,_,_,_=c.read_site(site,specs[site],pins,output_seals)
        if len(raw)!=len(old):
            raise ValueError("Raw/Stage07 timeline row count differs at "+site)
        native=raw.native_key.astype(str).to_numpy()
        if not np.array_equal(native,i.literal_keys(old,site)):
            raise ValueError("Raw Stage07 native keys unequal: "+site)
        if len(era)!=len(era.TIMESTAMP_START.unique()):
            raise ValueError("ERA companion source timestamp duplicated: "+site)
        era_lookup=era.set_index("TIMESTAMP_START")
        v5_values=i.values(old,"VPD_USE")
        shadow_values=i.values(shadow,"VPD_USE")
        raw_t=i.values(old,"TA_USE")
        oldrh,_=i.physics(old)
        newrh,_=i.physics(shadow)
        index={key:j for j,key in enumerate(native)}
        for _,event in top.iterrows():
            key=str(event.native_key)
            centre=index[key]
            prior=numeric(era_lookup.loc[key].TA_ERA)
            era_vpd=numeric(era_lookup.loc[key].VPD_ERA)
            era_e,era_rh=source_pair(prior,era_vpd)
            row={
                "site":site,"native_key":key,
                "initial_stage11i_reanalysis_event_category":HOTSPOTS[(site,key)][0],
                "source_F_TA_C":numeric(raw.TA_F.iloc[centre]),
                "source_F_TA_QC":numeric(raw.TA_F_QC.iloc[centre]),
                "source_F_VPD_hPa":numeric(raw.VPD_F.iloc[centre]),
                "source_F_VPD_QC":numeric(raw.VPD_F_QC.iloc[centre]),
                "source_original_implied_ea_hPa":source_pair(
                    numeric(raw.TA_F.iloc[centre]),
                    numeric(raw.VPD_F.iloc[centre]))[0],
                "ERA_companion_T_C":prior,
                "ERA_companion_VPD_hPa":era_vpd,
                "ERA_companion_implied_ea_hPa":era_e,
                "ERA_companion_RH_water_pct":era_rh,
                "stage07_VPD_hPa":float(v5_values[centre]),
                "stage11h_shadow_VPD_hPa":float(shadow_values[centre]),
                "stage07_RH_water_pct":float(oldrh[centre]),
                "stage11h_shadow_RH_water_pct":float(newrh[centre]),
                "Stage11i_max_added_jump_hPa":float(event.max_ADDED_adjacent_jump_hPa),
                "Stage11i_old_prior_jump_hPa":float(event.original_previous_halfhour_jump_hPa),
                "Stage11i_shadow_prior_jump_hPa":float(event.shadow_previous_halfhour_jump_hPa),
                "Stage11i_old_next_jump_hPa":float(event.original_next_halfhour_jump_hPa),
                "Stage11i_shadow_next_jump_hPa":float(event.shadow_next_halfhour_jump_hPa),
                "human_followup":"REVIEW_INSTRUMENT_CLOCK_AND_BOTH_BOUNDARIES",
                "post_v5_approved":False
            }
            review.append(row)
            for offset in range(-6,7):
                j=centre+offset
                if not (0<=j<len(native)):
                    raise ValueError("Context goes outside expected original file")
                k=native[j]
                if k not in era_lookup.index:
                    raise ValueError("Exact-time companion ERA missing "+site+" "+k)
                ra=raw.iloc[j]
                er=era_lookup.loc[k]
                et=numeric(er["TA_ERA"])
                ev=numeric(er["VPD_ERA"])
                ea_e,rh_e=source_pair(et,ev)
                ea_r,rh_r=source_pair(numeric(ra.TA_F),numeric(ra.VPD_F))
                contexts.append({
                    "centre_site":site,
                    "centre_native_key":key,
                    "offset_half_hours":offset,
                    "native_key":k,
                    "original_TA_F_C":numeric(ra.TA_F),
                    "original_TA_F_QC":numeric(ra.TA_F_QC),
                    "original_VPD_F_hPa":numeric(ra.VPD_F),
                    "original_VPD_F_QC":numeric(ra.VPD_F_QC),
                    "original_implied_ea_hPa":ea_r,
                    "original_implied_RH_water_pct":rh_r,
                    "companion_ERA_T_C":et,
                    "companion_ERA_VPD_hPa":ev,
                    "companion_ERA_implied_ea_hPa":ea_e,
                    "companion_ERA_RH_water_pct":rh_e,
                    "stage07_candidate_T_C":float(raw_t[j]),
                    "stage07_candidate_VPD_hPa":float(v5_values[j]),
                    "stage07_candidate_RH_water_pct":float(oldrh[j]),
                    "Stage11h_trial_VPD_hPa":float(shadow_values[j]),
                    "Stage11h_trial_RH_water_pct":float(newrh[j]),
                    "Stage11h_minus_v5_VPD_hPa":float(shadow_values[j]-v5_values[j]),
                    "source_native_only_no_offset_approved":True
                })
        print(f"STAGE11J SOURCE {site}: {len(top)} high-jump cases, "
              f"{len(top)*13} exact native +/-3h rows, original SHA and Stage11i QA PASS",
              flush=True)
    rows=pd.DataFrame(review).sort_values(["site","native_key"],kind="stable")
    panel=pd.DataFrame(contexts).sort_values(
        ["centre_site","centre_native_key","offset_half_hours"],kind="stable")
    if (len(rows)!=4 or len(panel)!=52 or
        panel.duplicated(["centre_site","centre_native_key","offset_half_hours"]).any() or
        not np.array_equal(np.unique(panel.offset_half_hours),np.arange(-6,7)) or
        int(rows.Stage11i_max_added_jump_hPa.gt(5).sum())!=2):
        raise ValueError("Context record count, 4 event scope or 2 severe events changed")
    return rows,panel,i


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11J — FOUR HIGH ADDED-JUMP EVENT SOURCE CONTEXT | "+VERSION,flush=True)
    synthetic_test()
    if args.self_test:
        return
    hotspots,context,i=audit()
    print("\n========== FOUR SOURCE/ERA/STAGE07/STAGE11H HUMAN REVIEW EVENTS ==========",flush=True)
    print(hotspots[[
        "site","native_key","source_F_VPD_QC","source_original_implied_ea_hPa",
        "ERA_companion_RH_water_pct","stage07_RH_water_pct",
        "stage11h_shadow_RH_water_pct","Stage11i_max_added_jump_hPa"
    ]].to_string(index=False),flush=True)
    print("\n========== EXACT +/-3H FULL SOURCE AND SHADOW CONTEXT ==========",flush=True)
    print(context[[
        "centre_site","centre_native_key","offset_half_hours","native_key",
        "original_TA_F_C","original_VPD_F_hPa","original_VPD_F_QC",
        "companion_ERA_RH_water_pct","stage07_candidate_VPD_hPa",
        "Stage11h_trial_VPD_hPa","Stage11h_minus_v5_VPD_hPa"
    ]].to_string(index=False),flush=True)
    print(f"\nSTAGE11J SUMMARY: hotspot_records={len(hotspots)}/4 "
          f"context_rows={len(context)}/52 added_jump_gt5hPa=2 "
          "source_clock_approved=0 Postv5_approved=0 DATM_ready=0 spinup=0",
          flush=True)
    if args.check:
        print("CHECK ONLY: NO source, report, forcing or model writes.",flush=True)
        return
    report=ROOT/"reports"/(
        "stage11j_four_jump_original_ERA_context_"+datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    report.mkdir(exist_ok=False)
    outputs={
        "four_human_review_source_ERA_and_shadows.csv":hotspots,
        "52_halfhours_four_events_plus_minus_3h_context.csv":context
    }
    for filename,df in outputs.items():
        df.to_csv(report/filename,index=False)
    hold="""# Stage11j four-event read-only humidity context

The four events were independently selected because the new Stage11h
shadow candidates increase an adjacent half-hour VPD jump by >2 hPa
relative to SHA-sealed Stage07; two increase it by >5 hPa.
Original \`VPD_F_QC\` is preserved; companion ERA5 source is FLUXNET
release site-downscaled ERA companion, not standalone ERA5-Land.

Inspect the native +/-3h time series, both sides of each discontinuity,
possible isolated 1-sample spikes and sustained episodes, source QC,
ERA companion source RH, T2m vs retained tower TA and pressure/height,
season, solar hour and station clock. The ERA-VPD and ERA-RH-transfer
methods are NOT independent tower measurements. Any decision to retain
or reject one of these shadow candidates requires a separately reviewed
human science ledger with explicit evidence, not automatic thresholding.

Post-v5, DATM, CIME, spinup and all clock approvals remain ZERO.
Do not modify Stage07 source or the Stage11h INCOMPLETE marker.
"""
    (report/"SCIENTIFIC_HOLD.md").write_text(hold,encoding="utf-8")
    receipt={
        "version":VERSION,
        "verified_Stage11i_Git_blob_SHA":STAGE11I_BLOB,
        "verified_Stage11c_Git_blob_SHA":STAGE11C_BLOB,
        "Stage11h_sha_receipt_SHA256":sha(i.TRIAL/"sha_sealed_shadow_trial_receipt.json"),
        "Stage07_manifest_SHA256":sha(i.S07/"exact_input_manifest.json"),
        "hotspot_records":4,
        "context_rows":52,
        "introduced_jump_over5hPa":2,
        "scientific_decisions_signed":0,
        "clock_offsets_approved":0,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorizations":0,
        "output_sha256":{filename:sha(report/filename)
                         for filename in [*outputs,"SCIENTIFIC_HOLD.md"]}
    }
    (report/"read_only_four_event_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11J REPORT DIR:",report,flush=True)
    print("SOURCE/SEALED V5/SHADOW FORCING UNCHANGED; NO DATM/CIME/SLURM.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE11J STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage12y SCIENCE ONLY: 2017-07-04 two-gap original native VPD bridge
and 13 existing Stage12g original SHA-sealed gridded ERA5-Land candidates.

Inputs: original Stage12x (68 missing / 13 finite warning), Stage12w,
signed Stage12g source repair ledger and native shadow, original Stage07
FLUXMET/ERA SHA manifest. Audits 06:30 07:00 07:30 08:00 consecutive
half-hour candidate transitions plus exact +/-6h context; never
mistake 07:00 -> 08:00 nonadjacent 60min difference for a 30min jump.
For 13 already-finite G historical values verify original Stage12g
ERA5-Land repaired VPD/QBOT and inspect its signed grid source attributes
vs Stage12w different original-companion hypothetical VPD.

--self-test mathematical / time tests with NO filesystem reads or writes
--check full-source SHAs and native-time audit, ZERO WRITES
--run SAME then ONLY a new isolated, SHA-receipted SCIENCE REPORT
Never edit original sources, historic shadow or model forcing.
"""
import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION="batch03-stage12y-v1-20261025-July04-two-gap-and-13-G-grid-provenance"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
X=ROOT/"reports/stage12x_68missing_13historic_finite_stage12w_cross_candidate_20261025T193514Z_fc1729a4"
W=ROOT/"reports/stage12w_355_original_MDS_VPD_companion_ERA_RH_physics_triage_20261025T192422Z_10358cc7"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
X_RECEIPT="stage12x_source_history_SHA_receipt.json"
W_RECEIPT="stage12w_355_MDS_ERA_RH_science_report_SHA_receipt.json"
G_RECEIPT="stage12g_research_only_sha_receipt.json"
X_13="13_original_MDS_QC1_G_finite_other_hypothetical_candidate_warnings.csv"
X_68="68_original_MDS_QC1_rejected_G_missing_native_with_CDEG_hold_ledger.csv"
W_DETAIL="355_original_QC1_MDS_VPD_ERA_RH_cautionary_candidate_evidence.csv"
G_CAND="new_ERA5Land_year_source_RH_repair_candidates.csv"
G_SHADOW="US-Me6_STAGE12G_INCOMPLETE_NOLEAP.csv"
F= ("201707040630", "201707040700", "201707040730", "201707040800")
CENTER="201707040700"
SCIENCE_PASS="DIAGNOSTIC_PHYSICS_AND_AVAILABLE_EDGE_TEST_PASS_NOT_APPROVED"

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/symlink SHA-sealed original source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as stream:
        for b in iter(lambda:stream.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def numeric(series):
    a=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a)|(a<=-9990)]=np.nan
    return a

def close(x,y,eps=1.e-6):
    if pd.isna(x) or pd.isna(y):
        return pd.isna(x) and pd.isna(y)
    return abs(float(x)-float(y))<=eps

def flag(x):
    return str(x).strip().lower() in ("true","1")

def datekey(ts):
    return ts.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def edge(v1,v2):
    return abs(v2-v1) if np.isfinite(v1) and np.isfinite(v2) else np.nan

def selftest():
    keys=pd.to_datetime(list(F),format="%Y%m%d%H%M")
    assert list(np.diff(keys.to_numpy()).astype("timedelta64[m]").astype(int))==[30,30,30]
    assert abs(edge(3.974495,5.154795)-1.1803)<1e-5
    assert edge(np.nan,5)==edge(np.nan,5) if False else np.isnan(edge(np.nan,5))
    assert flag("True") and not flag("False")
    assert datekey(pd.Series(["2017-07-04 07:00:00"])).iat[0]==CENTER
    print("STAGE12Y SELF-TEST PASS: original native 4-point 30min bridge, distinct ERA provenance, no writes",flush=True)

def verify():
    rx=json.loads(safe(X/X_RECEIPT).read_text())
    rw=json.loads(safe(W/W_RECEIPT).read_text())
    rg=json.loads(safe(G/G_RECEIPT).read_text())
    if (rx.get("version")!="batch03-stage12x-v2-20261025-68missing-13oldfinite-immutable-CDEG"
        or rx.get("exact_68_missing_G") is not True
        or rx.get("exact_13_older_finite_G_candidate_warnings") is not True
        or rx.get("exact_1_pass_but_missing_G") is not True
        or rx.get("original_86_and_233_holds_preserved") is not True
        or rx.get("new_forcing_repairs")!=0
        or rx.get("stage12w_SHA256")!=sha(W/W_RECEIPT)):
        raise ValueError("Pinned Stage12x source lineage or original science hold changed")
    if (rw.get("version")!="batch03-stage12w-v2-20261025-355-MDS-bad-VPD-ERA-RH-guarded-diagnostics"
        or rw.get("verified_stage12g_source_receipt_sha256")!=sha(G/G_RECEIPT)
        or rw.get("new_source_or_forcing_repairs")!=0):
        raise ValueError("Pinned Stage12w companion candidate ancestry changed")
    if (rg.get("original_233_physics_holds_untouched") is not True
        or rg.get("original_six_site_T_P_native_clock_unchanged") is not True
        or rg.get("all_original_Stage12e_finite_humidity_untouched") is not True
        or rg.get("INCOMPLETE_marker_present") is not True):
        raise ValueError("Original Stage12g trial protection differs")
    for receipt in (rx,rw,rg):
        if (receipt.get("Postv5_approved")!=0
            or receipt.get("DATM_ready")!=0 or receipt.get("spinup_authorized")!=0):
            raise ValueError("Previous immutable data were model-approved: STOP")
    safe(G/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    for root,receipt in ((X,rx),(W,rw),(G,rg)):
        for name,digest in receipt["output_SHA256" if root in (X,W) else "output_sha256"].items():
            if sha(root/name)!=digest:
                raise ValueError("Original report/Stage12g value SHA mismatch "+name)
    manifest=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    specs={x["site"]:x for x in manifest["sites"]}
    orig=specs["US-Me6"]
    pins={str(Path(f).resolve()):digest for f,digest in manifest["input_sha256"].items()}
    for k in ("primary","era"):
        p=safe(orig[k])
        if sha(p)!=pins.get(str(p.resolve())):
            raise ValueError("Original FLUXMET / ERA native source SHA changed "+k)
    return orig

def source_context(spec,keys):
    primary=pd.read_csv(safe(spec["primary"]),usecols=[
        "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
        dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(safe(spec["era"]),usecols=[
        "TIMESTAMP_START","TA_ERA","VPD_ERA"],
        dtype={"TIMESTAMP_START":str},low_memory=False)
    a=primary.loc[primary.TIMESTAMP_START.isin(keys)].copy()
    b=era.loc[era.TIMESTAMP_START.isin(keys)].copy()
    if (len(a)!=len(keys) or len(b)!=len(keys)
        or a.TIMESTAMP_START.duplicated().any()
        or b.TIMESTAMP_START.duplicated().any()):
        raise ValueError("Original native source context keys not exactly present")
    out=a.merge(b,on="TIMESTAMP_START",validate="one_to_one")
    for name in ("TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"):
        out[name]=numeric(out[name])
    return out.set_index("TIMESTAMP_START")

def audit():
    spec=verify()
    warnings=pd.read_csv(safe(X/X_13),dtype={"native_key":str},low_memory=False)
    missing=pd.read_csv(safe(X/X_68),dtype={"native_key":str},low_memory=False)
    w=pd.read_csv(safe(W/W_DETAIL),dtype={"native_key":str},low_memory=False)
    gtable=pd.read_csv(safe(G/G_CAND),dtype={"native_key":str},low_memory=False)
    if (len(warnings)!=13 or len(missing)!=68 or len(w)!=355
        or not warnings.site.eq("US-Me6").all()
        or warnings.native_key.duplicated().any()
        or gtable.duplicated(["site","native_key"]).any()
        or w.duplicated(["site","native_key"]).any()):
        raise ValueError("Original X 68/13 and W 355 / G candidate native keys changed")
    gselect=gtable.loc[
        gtable.site.eq("US-Me6")
        & gtable.native_key.isin(warnings.native_key)].copy()
    if len(gselect)!=13:
        raise ValueError("Not all 13 FIRST_FINITE_IN_STAGE12G values have original G grid ledger")
    combined=warnings.merge(
        gselect,on=["site","native_key"],how="left",validate="one_to_one")
    if not all(close(old,new) for old,new in zip(
        combined.historical_Stage12g_VPD_hPa,
        combined.candidate_VPD_hPa)):
        raise ValueError("13 Stage12g values not equal signed native ERA5-Land gridded provenance")
    if not all(flag(x)==False for x in combined.UTC_clock_approved):
        raise ValueError("Stage12g original source UTC clock hypothesis is no longer unapproved")
    # Original Stage12g grid candidate at same native timestamp is compared to
    # a distinct, signed Stage12w original companion ERA-RH hypothetical candidate.
    combined["difference_original_companion_minus_signed_G_grid_VPD_hPa"]=(
        combined.Stage12w_hypothetical_original_companion_VPD_hPa
        -combined.candidate_VPD_hPa)
    combined["grid_T_minus_original_tower_T_C"]=(
        combined.ERA5Land_T2M_C-combined.original_EC_TA_C)
    combined["grid_P_minus_site_P_Pa"]=(
        combined.ERA5Land_SPRF_Pa-combined.original_EC_PSRF_Pa)
    if not all(close(x,y) for x,y in zip(
        combined.difference_original_companion_minus_signed_G_grid_VPD_hPa,
        combined.Stage12w_hypothetical_minus_preexisting_G_VPD_hPa)):
        raise ValueError("Original 13 Stage12x versus Stage12g difference values changed")
    if not (combined.source_origin_class.isin(["BOTH_FINITE_DIFFER","RAW_ONLY_FINITE"]).all()
            if "source_origin_class" in combined else True):
        raise ValueError("Unexpected original source origin state")
    target=missing.loc[missing.site.eq("US-Me6")
         &missing.native_key.eq(CENTER)
         &missing.Stage12w_diagnostic_group_NOT_APPROVED.eq(SCIENCE_PASS)]
    if len(target)!=1:
        raise ValueError("Only Stage12x single 2017-07-04 07:00 diagnostic pass/missing expected")
    gm=pd.read_csv(safe(G/G_SHADOW),usecols=[
        "time","TA_USE","PSRF","VPD_USE","QBOT"],
        dtype={"time":str},low_memory=False)
    gm["native_key"]=datekey(gm.time)
    if gm.native_key.duplicated().any():
        raise ValueError("Source Stage12g native timestamps duplicated")
    pos={key:i for i,key in enumerate(gm.native_key)}
    if CENTER not in pos:
        raise ValueError("Original Stage12g 07:00 native key missing")
    i=pos[CENTER]
    if i<12 or i+12>=len(gm):
        raise ValueError("Stage12g +/-6h at target out of bounds")
    win=gm.iloc[i-12:i+13].copy()
    clk=pd.to_datetime(win.native_key,format="%Y%m%d%H%M")
    if (len(win)!=25
        or not (np.diff(clk.to_numpy()).astype("timedelta64[m]").astype(int)==30).all()):
        raise ValueError("Original G 25 native source +/-6-hour window is irregular")
    if not all(k in set(win.native_key) for k in F):
        raise ValueError("Original four-point bridge missing from full native window")
    for name in ("TA_USE","PSRF","VPD_USE","QBOT"):
        win[name]=numeric(win[name])
    keys=set(win.native_key)
    context=source_context(spec,keys)
    wsite=w.loc[w.site.eq("US-Me6")&w.native_key.isin(keys)].set_index("native_key")
    joined=[]
    for row in win.itertuples(index=False):
        key=row.native_key
        old=context.loc[key]
        wc=wsite.loc[key] if key in wsite.index else None
        cv=float(wc.trial_VPD_USE_hPa) if wc is not None else np.nan
        base=bool(wc.site_T_physical and wc.site_P_physical and
            wc.ERA_RH_source_physical and wc.ERA_T_within_5C_of_tower_T and
            wc.source_ice_phase_allowed and wc.candidate_VPD_QBOT_closure) if wc is not None else False
        if wc is not None and (
            abs(float(wc.original_unchanged_QC0_tower_T_C)-float(old.TA_F))>1e-7
            or abs(float(wc.retained_Stage12g_PSRF_Pa)-float(row.PSRF))>1e-7):
            raise ValueError("Original native source and Stage12w candidate T/P mismatch "+key)
        joined.append({
          "site":"US-Me6","native_key":key,"source_time":str(row.time),
          "relative_minutes_to_0700":int((pd.Timestamp(key)-pd.Timestamp(CENTER)).total_seconds()/60)
            if False else int((pd.to_datetime(key,format="%Y%m%d%H%M")-
                pd.to_datetime(CENTER,format="%Y%m%d%H%M")).total_seconds()/60),
          "original_TA_F_C":float(old.TA_F),
          "original_TA_F_QC":float(old.TA_F_QC),
          "original_VPD_F_hPa":float(old.VPD_F),
          "original_VPD_F_QC":float(old.VPD_F_QC),
          "original_native_TA_ERA_C":float(old.TA_ERA),
          "original_native_VPD_ERA_hPa":float(old.VPD_ERA),
          "signed_G_TA_USE_C":float(row.TA_USE),
          "signed_G_PSRF_Pa":float(row.PSRF),
          "signed_G_VPD_USE_hPa":float(row.VPD_USE),
          "signed_G_QBOT_kgkg":float(row.QBOT),
          "signed_Stage12w_candidate_available":wc is not None,
          "Stage12w_original_ERA_RH_trial_VPD_hPa":cv,
          "Stage12w_base_rh_t_pressure_ice_closure_and_5C_guard_pass":base,
          "Stage12w_diagnostic_class":str(wc.screen_group_NOT_MODEL_APPROVAL)
            if wc is not None else "NO_SIGNED_355_CANDIDATE",
          "four_point_bridge_segment":key in F,
          "no_imputation_or_release":True
        })
    context=pd.DataFrame(joined)
    bridge=context.loc[context.native_key.isin(F)].copy()
    bridge=bridge.set_index("native_key").loc[list(F)].reset_index()
    trial=[]
    for row in bridge.itertuples(index=False):
        if np.isfinite(row.signed_G_VPD_USE_hPa):
            choice=float(row.signed_G_VPD_USE_hPa)
            source="SIGNED_STAGE12G_EXISTING"
            gate=True
        elif row.signed_Stage12w_candidate_available:
            choice=float(row.Stage12w_original_ERA_RH_trial_VPD_hPa)
            source="HYPOTHETICAL_STAGE12W_COMPANION_NOT_APPLIED"
            gate=bool(row.Stage12w_base_rh_t_pressure_ice_closure_and_5C_guard_pass)
        else:
            choice=np.nan
            source="MISSING_NO_SIGNED_CANDIDATE"
            gate=False
        trial.append((choice,source,gate))
    bridge["hypothetical_hybrid_VPD_hPa"]=[q[0] for q in trial]
    bridge["hypothetical_hybrid_source"]=[q[1] for q in trial]
    bridge["hypothetical_hybrid_base_pass"]=[q[2] for q in trial]
    e=[]
    for k in range(3):
        a=bridge.iloc[k];b=bridge.iloc[k+1]
        j=edge(float(a.hypothetical_hybrid_VPD_hPa),
               float(b.hypothetical_hybrid_VPD_hPa))
        e.append({
          "site":"US-Me6","source_native_start":a.native_key,
          "source_native_end":b.native_key,"native_step_minutes":30,
          "stage12g_existing_VPD_from_hPa":float(a.signed_G_VPD_USE_hPa),
          "stage12g_existing_VPD_to_hPa":float(b.signed_G_VPD_USE_hPa),
          "hypothetical_source_from":a.hypothetical_hybrid_source,
          "hypothetical_source_to":b.hypothetical_hybrid_source,
          "hypothetical_VPD_from_hPa":float(a.hypothetical_hybrid_VPD_hPa),
          "hypothetical_VPD_to_hPa":float(b.hypothetical_hybrid_VPD_hPa),
          "hypothetical_abs_30min_jump_hPa":j,
          "both_endpoint_base_source_screens_pass":bool(
              a.hypothetical_hybrid_base_pass and
              b.hypothetical_hybrid_base_pass),
          "hypothetical_jump_gt4hPa":bool(np.isfinite(j) and j>4),
          "unassessed_missing_edge":bool(not np.isfinite(j)),
          "native_historical_science_holds_released":False
        })
    edges=pd.DataFrame(e)
    if (len(context)!=25 or len(bridge)!=4 or len(edges)!=3
        or len(combined)!=13 or not edges.native_step_minutes.eq(30).all()
        or not close(bridge.iloc[0].signed_G_VPD_USE_hPa,3.974495)
        or not close(bridge.iloc[1].Stage12w_original_ERA_RH_trial_VPD_hPa,5.154795)
        or not close(bridge.iloc[3].signed_G_VPD_USE_hPa,21.391)):
        raise ValueError("Original signed 13 grid candidates or 4-point native bridge differs")
    return combined,context,bridge,edges

def main():
    p=argparse.ArgumentParser(description=__doc__)
    x=p.add_mutually_exclusive_group(required=True)
    for op in ("self-test","check","run"):
        x.add_argument("--"+op,action="store_true")
    args=p.parse_args()
    print("STAGE12Y — 13 ORIGINAL G GRID SOURCES + 2017-07-04 NATIVE 4-POINT TWO-GAP BRIDGE | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    table,context,bridge,edges=audit()
    print("\n========== 13 HISTORICAL STAGE12G VALUE = SIGNED GRID ERA5-LAND PROVENANCE ==========",flush=True)
    print(table[["site","native_key","candidate_VPD_hPa",
           "Stage12w_hypothetical_original_companion_VPD_hPa",
           "difference_original_companion_minus_signed_G_grid_VPD_hPa",
           "ERA5Land_water_RH_pct",
           "grid_T_minus_original_tower_T_C",
           "grid_P_minus_site_P_Pa",
           "original_source_native_UTC_offset_hypothesis",
           "UTC_clock_approved"]].to_string(index=False),flush=True)
    print("\n========== 2017-07-04 06:30 07:00 07:30 08:00, NO REPAIRS ==========",flush=True)
    print(bridge[["native_key","original_VPD_F_QC","original_VPD_F_hPa",
            "signed_G_VPD_USE_hPa","Stage12w_original_ERA_RH_trial_VPD_hPa",
            "Stage12w_base_rh_t_pressure_ice_closure_and_5C_guard_pass",
            "Stage12w_diagnostic_class","hypothetical_hybrid_VPD_hPa",
            "hypothetical_hybrid_source"]].to_string(index=False),flush=True)
    print("\n========== EXACT THREE CONSECUTIVE ORIGINAL 30MIN TRIAL EDGES ==========",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("\nSTAGE12Y SUMMARY: 13_old_G_first_finite_provenance=VERIFIED "
          "2017-07-04_bridge_four_keys=TRUE three_adjacent_30min_edges=TRUE "
          "all_source_holds_86_plus_233_preserved=TRUE "
          "new_source_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12Y CHECK ONLY: ZERO SOURCE, REPORT, FORCING OR MODEL WRITES.",flush=True)
        return
    dest=ROOT/"reports"/(
        "stage12y_13_G_grid_provenance_and_Me6_20170704_bridge_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    tables={
      "13_existing_G_grid_ERA5Land_vs_original_companion_source.csv":table,
      "Me6_20170704_original_source_signed_G_pm6h_window.csv":context,
      "Me6_20170704_four_native_halfhour_hypothetical_bridge.csv":bridge,
      "Me6_20170704_exact_three_adjacent_30min_edges.csv":edges,
    }
    for name,frame in tables.items():frame.to_csv(dest/name,index=False)
    (dest/"SCIENCE_HOLD.md").write_text(
        "Stage12y science forensic study ONLY: two hypothetical candidate "
        "values at 07:00/07:30 are never written to original 12g data. "
        "The 13 historical Stage12g first-finite values are SHA-signed "
        "gridded ERA5-Land RH candidates, under explicitly UNAPPROVED "
        "source clock hypotheses, not independent measured tower VPD. "
        "Native 30-minute jumps and >4 hPa limits and ERA 5C/ice/QBOT "
        "gates remain unchanged. The original 86+233 science holds, "
        "source/data/forcing/PFT/CIME/DATM/spinup remain protected.\n")
    sig={name:sha(dest/name) for name in [*tables,"SCIENCE_HOLD.md"]}
    receipt={
      "version":VERSION,
      "stage12x_report_SHA256":sha(X/X_RECEIPT),
      "stage12w_report_SHA256":sha(W/W_RECEIPT),
      "stage12g_source_receipt_SHA256":sha(G/G_RECEIPT),
      "original_13_G_grid_provenance_preserved":True,
      "original_native_four_point_bridge_report_only":True,
      "original_86_plus_233_science_holds_preserved":True,
      "source_T_VPD_P_native_clock_unchanged":True,
      "new_repairs":0,"Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":sig
    }
    (dest/"stage12y_grid_bridge_science_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12Y SOURCE-ONLY SCIENCE REPORT DIR:",dest,flush=True)
    print("ZERO ORIGINAL SOURCE, PREVIOUS SHADOW, FORCING, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12Y STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

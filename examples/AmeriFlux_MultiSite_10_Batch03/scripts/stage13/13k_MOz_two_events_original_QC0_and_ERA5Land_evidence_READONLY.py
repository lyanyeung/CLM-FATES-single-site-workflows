#!/usr/bin/env python3
"""Stage13k: diagnose *why* US-MOz Stage13j fails source-science conditions.

Compares exact 67 source-native halfhours with already downloaded, SHA-pinned
ERA5-Land; separately inventories nearest original measured TA_F_QC=0 and
VPD_F_QC=0 observations on both sides of each event, ±6/12/24/48/72h,
with companion source ERA and QC2 provenance. Scans every candidate T,
VPD, RH, PSRF, QBOT and edge transition and produces research-only
evidence, NEVER a repair recommendation with automatic authority.

No source, Stage07, Stage13g, Stage13j, PFT, DATM or Slurm edits.
--self-test no I/O; --check full audit NO WRITES; --run isolated report only.
The separately downloaded CDS ERA5-Land is ERA5-dependent, not ground truth.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION="batch03-stage13k-v1-20261026-QC0-source-edge-ERA5Land-evidence"
THIS = Path(__file__).resolve()
STAGE13J = THIS.with_name("13j_conditional_two_US_MOz_QC1_ERA5Land_SCOPED.py")
J_BLOB="9283b411b49500428e7534b5f12041c71190e93b"
EXPECTED_UTC=-6
RADII_HOURS=(6,12,24,48,72)
FREQUENCY=pd.Timedelta(minutes=30)
BOUND=pd.Timestamp("2005-01-06T10:00")
EVENTS=(
    ("2005-01-05T20:00:00","2005-01-06T09:00:00",27),
    ("2005-01-06T14:00:00","2005-01-07T09:30:00",40),
)

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def sibling():
    if not STAGE13J.is_file() or STAGE13J.is_symlink():
        raise RuntimeError("Missing pinned adjacent Stage13j source script "+str(STAGE13J))
    import subprocess
    # Git hash-object fingerprint of the exact reviewed Stage13j v4 from repo.
    result=subprocess.run(["git","hash-object",str(STAGE13J)],
                          capture_output=True,text=True,check=True)
    if result.stdout.strip()!=J_BLOB:
        raise RuntimeError("Untrusted Stage13j file changed; expected Git blob "+J_BLOB)
    spec=importlib.util.spec_from_file_location("batch03_stg13j_verified",STAGE13J)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load signed Stage13j source")
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    if (obj.SCOPE!=EVENTS or obj.SITE!="US-MOz"
            or obj.VER!="batch03-stage13j-v4-20261026-UTC-coverage-QC0-edge-census"):
        raise RuntimeError("Stage13j scientific scope/version changed")
    return obj

def number(x):
    try: return float(x)
    except (TypeError,ValueError):return float("nan")

def nearby(index, t, center, direction, col, hours):
    if direction=="before":
        cand=index[(index<center)&(index>=center-pd.Timedelta(hours=hours))]
        if len(cand): return cand[-1]
    else:
        cand=index[(index>center)&(index<=center+pd.Timedelta(hours=hours))]
        if len(cand): return cand[0]
    return None

def closest(index,center,direction):
    if direction=="before":
        x=index[index<center]
        return x[-1] if len(x) else None
    x=index[index>center]
    return x[0] if len(x) else None

def selftest():
    assert sum(n for a,b,n in EVENTS)==67
    assert all(len(pd.date_range(a,b,freq="30min"))==n for a,b,n in EVENTS)
    idx=pd.DatetimeIndex(pd.to_datetime(["2005-01-05 08:30",
          "2005-01-05 09:00","2005-01-06 10:00","2005-01-07 10:00"]))
    assert nearby(idx,None,pd.Timestamp("2005-01-05 20:00"),"before","T",12)==idx[1]
    assert nearby(idx,None,pd.Timestamp("2005-01-05 20:00"),"before","T",6) is None
    assert closest(idx,pd.Timestamp("2005-01-05 20:00"),"after")==idx[2]
    print("STAGE13K SELF-TEST PASS | nearest measured QC0/QC2 source anchors, no writes",flush=True)

def metrics(x):
    arr=np.asarray(x,dtype=float)
    vals=arr[np.isfinite(arr)]
    return {
        "n_valid":len(vals),
        "mean":float(np.mean(vals)) if len(vals) else None,
        "median":float(np.median(vals)) if len(vals) else None,
        "mean_abs":float(np.mean(np.abs(vals))) if len(vals) else None,
        "max_abs":float(np.max(np.abs(vals))) if len(vals) else None
    }

def audit(decision):
    j=sibling()
    spec,t,era,forcing,segments=j.load_native(decision)
    meta=j.metadata(spec)
    if int(meta["utc_offset_hours"])!=EXPECTED_UTC:
        raise RuntimeError("BIF official UTC offset changed")
    downloaded,receipt=j.evidence_filename()
    grid=j.nc_data(downloaded,meta)
    # Use original tower/QC=0 measured points only for ground-anchor evidence.
    science_window=t.loc["2005-01-03":"2005-01-10"].copy()
    idx=science_window.index
    observedT=t.index[t.TA_F_QC.eq(0)]
    observedV=t.index[t.VPD_F_QC.eq(0)]
    both=t.index[t.TA_F_QC.eq(0) & t.VPD_F_QC.eq(0)]
    observedT2=t.index[t.TA_F_QC.eq(2)]
    observedV2=t.index[t.VPD_F_QC.eq(2)]
    anchors=[]
    for start,end,count in EVENTS:
        a=pd.Timestamp(start);b=pd.Timestamp(end)
        for category,idx_ in (
              ("QC0_both_measured_T_VPD",both),
              ("QC0_measured_T_only",observedT),
              ("QC0_measured_VPD_only",observedV),
              ("QC2_T_gapfill_from_companion_ERA_NOT_MEASURED",observedT2),
              ("QC2_VPD_gapfill_from_companion_ERA_NOT_MEASURED",observedV2)):
            for direction,center in (("before",a),("after",b)):
                nearest=closest(idx_,center,direction)
                rec={
                  "event_start":start,"event_end":end,
                  "anchor_quality":category,"side":direction,
                  "nearest_original_native_timestamp":str(nearest) if nearest is not None else "",
                  "distance_hours":(abs((nearest-center).total_seconds())/3600.
                                    if nearest is not None else None),
                  "anchor_source_tower_T_C":number(t.at[nearest,"TA_F"]) if nearest is not None else None,
                  "anchor_source_tower_T_QC":number(t.at[nearest,"TA_F_QC"]) if nearest is not None else None,
                  "anchor_source_tower_VPD_hPa":number(t.at[nearest,"VPD_F"]) if nearest is not None else None,
                  "anchor_source_tower_VPD_QC":number(t.at[nearest,"VPD_F_QC"]) if nearest is not None else None,
                  "companion_ERA_T_C":number(era.at[nearest,"TA_ERA"]) if nearest is not None else None,
                  "companion_ERA_VPD_hPa":number(era.at[nearest,"VPD_ERA"]) if nearest is not None else None,
                }
                for rad in RADII_HOURS:
                    k=nearby(idx_,None,center,direction,category,rad)
                    rec["present_within_"+str(rad)+"h"]=bool(k is not None)
                if nearest is not None:
                    try:
                        near_grid=j.at_native(grid,pd.DatetimeIndex([nearest]),EXPECTED_UTC).iloc[0]
                        rec["ERA5Land_T_C"]=float(near_grid.grid_T_C)
                        rec["ERA5Land_VPD_hPa"]=float(near_grid.grid_VPD_hPa)
                        rec["source_tower_minus_ERA5Land_T_C"]=float(t.at[nearest,"TA_F"]-near_grid.grid_T_C)
                        rec["source_tower_minus_ERA5Land_VPD_hPa"]=float(t.at[nearest,"VPD_F"]-near_grid.grid_VPD_hPa)
                    except RuntimeError:
                        # This can occur outside the separately downloaded Jan03-Jan11
                        # window, not a scientific pass or missing source.
                        rec["ERA5Land_T_C"]=None
                        rec["ERA5Land_VPD_hPa"]=None
                        rec["source_tower_minus_ERA5Land_T_C"]=None
                        rec["source_tower_minus_ERA5Land_VPD_hPa"]=None
                anchors.append(rec)
    anchortable=pd.DataFrame(anchors)

    # All original unmodified and ERA vs CDS comparisons for BOTH whole
    # events, without the QC0 preflight short-circuit in the Stage13j v4 code.
    event_rows=[]
    by_event=[]
    for ((a,b,n),ts) in zip(EVENTS,segments):
        g=j.at_native(grid,ts,EXPECTED_UTC)
        cent_t=t.loc[ts]
        cent_e=era.loc[ts]
        candidate=forcing.loc[ts]
        tland=g.grid_T_C.to_numpy(dtype=float)
        vland=g.grid_VPD_hPa.to_numpy(dtype=float)
        torig=cent_t.TA_F.to_numpy(dtype=float)
        vorig=cent_t.VPD_F.to_numpy(dtype=float)
        te=cent_e.TA_ERA.to_numpy(dtype=float)
        ve=cent_e.VPD_ERA.to_numpy(dtype=float)
        sat_grid=j.saturation(tland)
        rh_grid=100*(1-vland/sat_grid)
        rh_era=100*(1-ve/j.saturation(te))
        vapor=(sat_grid-vland)*100
        press=candidate.PSRF.to_numpy(dtype=float)
        q=0.622*vapor/(press-0.378*vapor)
        physical=(np.isfinite(q)&np.isfinite(rh_grid)&np.isfinite(press)&
             (rh_grid>0)&(rh_grid<100)&(q>0)&(q<0.08)&(vland>0)&(vland<sat_grid))
        checkT=(np.abs(tland-te)<=3.5)
        checkRH=(np.abs(rh_grid-rh_era)<=15)
        checkP=(np.abs(g.sp.to_numpy(dtype=float)-press)<=12000)
        begin=ts[0]-FREQUENCY
        finish=ts[-1]+FREQUENCY
        edget=np.asarray([abs(float(forcing.at[begin,"TA_USE"])-tland[0]),
                          abs(float(forcing.at[finish,"TA_USE"])-tland[-1])])
        edgev=np.asarray([abs(float(forcing.at[begin,"VPD_USE"])-vland[0]),
                          abs(float(forcing.at[finish,"VPD_USE"])-vland[-1])])
        for i,time in enumerate(ts):
            event_rows.append({
              "event_start":a,"event_end":b,"original_native_time":str(time),
              "original_tower_T_C":torig[i],
              "original_source_T_QC":cent_t.TA_F_QC.iloc[i],
              "original_tower_VPD_hPa":vorig[i],
              "original_source_VPD_QC":cent_t.VPD_F_QC.iloc[i],
              "companion_ERA_T_C":te[i],"companion_ERA_VPD_hPa":ve[i],
              "current_Stage13g_T_C":candidate.TA_USE.iloc[i],
              "current_Stage13g_VPD_hPa":candidate.VPD_USE.iloc[i],
              "signed_distinct_CDS_ERA5Land_T_C":tland[i],
              "signed_CDS_ERA5Land_VPD_hPa":vland[i],
              "CDS_grid_Tminus_companion_ERA_C":tland[i]-te[i],
              "CDS_grid_RH_pct":rh_grid[i],
              "companion_ERA_RH_pct":rh_era[i],
              "CDS_grid_RHminus_ERA_pct":rh_grid[i]-rh_era[i],
              "CDS_grid_surface_pressure_Pa":float(g.sp.iloc[i]),
              "model_PSRF_Pa":press[i],
              "CDS_reconstructed_QBOT_preview_kgkg":q[i],
              "paired_ERA_T_agree_le3p5C":bool(checkT[i]),
              "paired_ERA_RH_agree_le15pct":bool(checkRH[i]),
              "source_grid_pressure_agree_le12kPa":bool(checkP[i]),
              "preview_physics_pass":bool(physical[i]),
              "operator_approved_conditional":True,
              "source_replacement_applied":False})
        event_stats={
          "start":a,"end":b,"HH":n,
          "original_source_QC1_T_and_VPD_all":bool(cent_t.TA_F_QC.eq(1).all() and cent_t.VPD_F_QC.eq(1).all()),
          "CDS_grid_vs_companion_T_C":metrics(tland-te),
          "CDS_grid_vs_companion_RH_pct":metrics(rh_grid-rh_era),
          "original_source_tower_vs_CDS_grid_T_C":metrics(torig-tland),
          "original_source_tower_vs_CDS_grid_VPD_hPa":metrics(vorig-vland),
          "CDS_pair_physics_pass":int(physical.sum()),
          "CDS_vs_companion_T_gate_pass":int(checkT.sum()),
          "CDS_vs_companion_RH_gate_pass":int(checkRH.sum()),
          "CDS_vs_current_model_pressure_gate_pass":int(checkP.sum()),
          "nearest_stage13g_T_external_boundary_abs_C":edget.tolist(),
          "nearest_stage13g_VPD_external_boundary_abs_hPa":edgev.tolist(),
          "boundary_4C_T_4hPa_VPD_pass":bool((edget<=4).all() and (edgev<=4).all()),
          "QC0_both_sides_within_6h":False,
          "source_clock_offset_approved_by_existing_Stage13j_gate":False,
          "science_event_approved_to_apply":False,
          "overall_status":"HOLD_SOURCE_QC0_CLOCK_AND_BOUNDARIES",
        }
        by_event.append(event_stats)
    exact=pd.DataFrame(event_rows)
    if len(exact)!=67 or exact.original_native_time.duplicated().any():
        raise RuntimeError("Original exactly 67 native time rows changed unexpectedly")
    both_bounds=anchortable.loc[anchortable.anchor_quality.eq("QC0_both_measured_T_VPD")]
    if both_bounds["present_within_6h"].any():
        # If source data changed since earlier observed Stage13j v4, stop
        # rather than relying on the previous 0/0 condition.
        raise RuntimeError("Earlier observed missing both-QC0 event boundaries changed; re-run Stage13j science gate")
    offsets=[]
    measured=t.loc["2005-01-03":"2005-01-10"]
    measured=measured.loc[measured.TA_F_QC.eq(0)&measured.VPD_F_QC.eq(0)]
    if len(measured)!=29:
        raise RuntimeError("Earlier Stage13j 29 measured QC0 analogue count changed")
    for offset in (-7,-6,-5):
        selected_grid=j.at_native(grid,measured.index,offset)
        dt=measured.TA_F.to_numpy(dtype=float)-selected_grid.grid_T_C.to_numpy(dtype=float)
        dv=measured.VPD_F.to_numpy(dtype=float)-selected_grid.grid_VPD_hPa.to_numpy(dtype=float)
        offsets.append({
          "proposed_standard_UTC_OFFSET_hours":offset,
          "published_bif":offset==-6,
          "measured_both_QC0_n":len(measured),
          "tower_minus_CDS_T":metrics(dt),
          "tower_minus_CDS_VPD":metrics(dv),
          "Stage13j_prior_strict_1C_superiority_gate_pass":False,
        })
    stats={str(x["proposed_standard_UTC_OFFSET_hours"]):x for x in offsets}
    if not(stats["-6"]["tower_minus_CDS_T"]["mean_abs"]<
           stats["-7"]["tower_minus_CDS_T"]["mean_abs"] and
           stats["-6"]["tower_minus_CDS_T"]["mean_abs"]<
           stats["-5"]["tower_minus_CDS_T"]["mean_abs"]):
        raise RuntimeError("Prior Stage13j -6 clock MAE rank no longer reproduces")
    summary={
      "version":VERSION,"site":"US-MOz",
      "original_BIF":{"latitude":meta["latitude"],"longitude":meta["longitude"],
                      "published_utc_offset_hours":meta["utc_offset_hours"],
                      "source_sha256":meta["bif_sha256"]},
      "operator_authorized_scoped_halfhours":67,
      "condition_passed_and_repaired_halfhours":0,
      "unapproved_2005_Jan09_negative_bias_HOLD":True,
      "source_QC0_T_VPD_both_near_both_edges":False,
      "source_clock_1degC_superiority_validated":False,
      "CDS_ERA5Land_SHA":sha(downloaded),
      "CDS_ERA5Land_is_ERA5_driven_not_independent_tower_measurement":True,
      "Stage13g_sha":sha(j.CURRENT),
      "all_67_original_source_halfhours_remain_untouched":True,
      "no_model_or_DATM_or_PFT_or_ZBOT_change":True,
      "Postv5_ready":False,"DATM_ready":False,"spinup_ready":False,
      "next_science_gate":"Original measured QC0 absent within 6h of both events and strict offset evidence fails; do not relax without explicit operator review. This report is not repair authority."}
    return anchortable,exact,pd.DataFrame(offsets),by_event,summary

def main():
    p=argparse.ArgumentParser()
    choose=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):
        choose.add_argument("--"+opt,action="store_true")
    p.add_argument("--decision",type=Path)
    args=p.parse_args()
    print("STAGE13K ORIGINAL QC0 AND INDEPENDENT CDS EVIDENCE READONLY | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    if args.decision is None:p.error("Stage13j exact signed user decision must be supplied")
    anchors,comparisons,offsets,events,summary=audit(args.decision)
    print("\n=== NEAREST TRUE ORIGINAL QC0/QC2 ANCHORS BY EVENT AND SIDE ===",flush=True)
    cols=["event_start","anchor_quality","side","nearest_original_native_timestamp",
          "distance_hours","present_within_6h","present_within_12h","present_within_24h",
          "present_within_48h","present_within_72h",
          "source_tower_minus_ERA5Land_T_C","source_tower_minus_ERA5Land_VPD_hPa"]
    print(anchors[cols].to_string(index=False,float_format=lambda x:f"{x:.3f}"),flush=True)
    print("\n=== EXACT CDS CLOCK 29 SOURCE-MEASURED QC0 ANALOGUE METRICS ===",flush=True)
    for row in offsets.to_dict("records"):
        print(row["proposed_standard_UTC_OFFSET_hours"],
              "published",row["published_bif"],
              "measuredQC0",row["measured_both_QC0_n"],
              "TA_MAE",row["tower_minus_CDS_T"]["mean_abs"],
              "VPD_MAE",row["tower_minus_CDS_VPD"]["mean_abs"],flush=True)
    print("\n=== TWO COMPLETE 27+40 EVENT SCIENCE PREVIEW COUNTS (NO ACTUAL PATCH) ===",flush=True)
    for row in events:print(json.dumps(row,ensure_ascii=False,sort_keys=True),flush=True)
    print("\n=== FAIL-CLOSED DECISION ===",flush=True)
    for key,value in summary.items():print(key,value,flush=True)
    if args.check:
        print("STAGE13K CHECK PASS / SOURCE SCIENCE HOLD: ZERO FILE WRITES",flush=True)
        return
    j=sibling()
    out=j.ROOT/"reports"/("stage13k_MOz_Jan2005_QC0_extended_and_CDS_comparison_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    filename={
       "source_nearest_original_QC0_QC2_by_event_both_edges.csv":anchors,
       "all_67_unapproved_CDS_vs_FLUXNET_source_event_comparison.csv":comparisons,
       "published_BIF_offset_vs_plus_minus_1h_measuredQC0_29_samples.json":offsets.to_dict("records"),
       "both_approved_scoped_event_science_HOLD_summary.json":events,
    }
    for name,obj in filename.items():
        full=out/name
        if isinstance(obj,pd.DataFrame):obj.to_csv(full,index=False)
        else:full.write_text(json.dumps(obj,indent=2)+"\n")
    (out/"source_science_decision.json").write_text(json.dumps(summary,indent=2)+"\n")
    marker="NO_REPLACEMENTS_QC0_6H_BOTH_EVENTS_FAIL"
    (out/marker).write_text("Study-only original measured QC0/QC2 and independent CDS evidence."
        " Neither event fulfilled previously operator-required measured QC0 both-end"
        " and -6 offset confidence criteria. No original/Stage13g forcing changed."
        " Next operator decision must explicitly address missing QC0, not silently"
        " substitute gapfilled QC2 or extrapolate.\n")
    paths=[*filename,"source_science_decision.json",marker]
    seal={"version":VERSION,
          "operator_Stage13j_decision_SHA256":sha(args.decision),
          "original_Stage13g_SHA256":sha(j.CURRENT),
          "CDS_external_evidence_SHA256":sha(j.evidence_filename()[0]),
          "output_SHA256":{name:sha(out/name) for name in paths},
          "science":summary}
    (out/"stage13k_original_QC0_ERA5Land_science_SHA_receipt.json").write_text(
          json.dumps(seal,indent=2)+"\n")
    print("STAGE13K REPORT ONLY",out,flush=True)
    print("NO NEW FORCING; NO SOURCE, GRID, CASE, DATM, SLURM WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13K STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

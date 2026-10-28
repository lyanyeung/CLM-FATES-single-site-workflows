#!/usr/bin/env python3
"""Stage13AO: US-Me6 19-HH original QC2 borders: temperature/vapour physics.

Scientific HOLD only. Verify original signed Stage13AN boundary report and
Stage13AM 165 measured QC0 donor candidate. Decompose native 30min VPD
jumps into original temperature-change saturation, actual water vapour e,
QBOT, RHwater and RHice without changing raw QC2 borders or 19 candidate. This is NOT a 19-HH
repair, ERA5-Land verification, new research shadow, model or Slurm run.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ao-v1-20261028-Me6-19HH-QC2-T-vapour-e-QBOT-edges"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AM_CODE=HERE/"13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py"
AM_GIT="df561eb8904b0147fc4a5aa0f977a5ec66545477"
AM_DIR=ROOT/"reports/stage13am_Me6_19HH_QC0biasERA_water_ice_EDGES_PREVIEW_ONLY_20261028T233826Z_da8b711e"
AM_REC="stage13am_READONLY_source_science_SHA_receipt.json"
AM_SUM="stage13am_19HH_joint_QC0_bias_source_science_summary.json"
AM_EVENT="19HH_calibrated_ERA_water_RH_candidate_QBOT_PREVIEW_NOT_APPROVED.csv"
AM_EDGE="19HH_original_plusminus2h_boundary_before_after_NO_REPAIR.csv"
AM_YEAR="165_actual_measured_QC0_donor_residual_bias_by_year.csv"
AM_FLAG="NO_PRODUCTION_FORCING_OR_SHADOW_REPAIR_APPROVED"
AM_NAMES={AM_SUM, AM_EVENT, AM_EDGE, AM_YEAR, AM_FLAG}
AM_VER="batch03-stage13am-v1-20261028-Me6-19HH-joint-QC0-calibrated-donor-PREVIEW"
AN_DIR=ROOT/"reports/stage13ao_Me6_19HH_QC2_vapour_e_QBOT_RH_source_READONLY_20261028T234506Z_1ed4316a"
AN_REC="stage13ao_source_science_READONLY_sha_receipt.json"
AN_SUM="stage13an_original_19HH_boundary_QC0_science_summary.json"
AN_CONTEXT="original_19HH_QC2_flanks_plusminus2h_tower_ERA_water_physics.csv"
AN_NEAREST="nearest_original_measured_QC0_tower_T_VPD_each_side.csv"
AN_STABILITY="11year_one_year_out_165_QC0_donor_bias_sensitivity_NO_APPROVAL.csv"
AN_FLAG="ORIGINAL_QC2_BORDERS_NOT_MEASURED_QC0_OR_APPROVED_DONORS"
AN_EXPECT={AN_SUM,AN_CONTEXT,AN_NEAREST,AN_STABILITY,AN_FLAG}
AN_VER="batch03-stage13an-v1-20261028-Me6-19HH-QC2-boundary-nearest-QC0-stability"
AI_SHA="b193388d4f82b47a7727c6ef9b2fdc25b37a56e4867d319224d1fc9327326f40"
START=pd.Timestamp("2014-12-31 23:30")
END=pd.Timestamp("2015-01-01 08:30")
STEP=pd.Timedelta(minutes=30)
EVENT=pd.date_range(START, END, freq="30min")
LEFT=START-STEP
RIGHT=END+STEP
def require(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AN SIGNED ORIGINAL SOURCE HOLD: "+str(msg))
def must(p):
    p=Path(p)
    require(p.is_file() and not p.is_symlink(), "file missing/symlink "+str(p))
    return p
def digest(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def gitblob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def skill(e):
    x=np.asarray(e,dtype=float)
    x=x[np.isfinite(x)]
    return {"n":int(len(x)),
       "MAE_hPa":float(np.mean(np.abs(x))) if len(x) else None,
       "P90_abs_hPa":float(np.percentile(np.abs(x),90)) if len(x) else None}
def selftest():
    require(len(EVENT)==19 and EVENT[0]==START and EVENT[-1]==END,
            "original 19 HH event chronology")
    require(es([-17.7])[0]<1.7 and es([-17.7])[0]>1.4,
            "cold site saturation physics")
    x=[.9,.95,.91];biases=[.4,.5,.6]
    require(np.allclose(np.array(x)-np.median(biases),[.4,.45,.41]),
            "median QC0 systematic donor bias independent of original source")
    print("STAGE13AO SELF-TEST PASS | 19HH source QC2 border and water-vapour decomposition, NO WRITES",flush=True)
def review():
    anreceipt=json.loads(must(AN_DIR/AN_REC).read_text())
    require(anreceipt.get("site")=="US-Me6" and
            anreceipt.get("version")==AN_VER and
            anreceipt.get("original_science_method_approved") is False and
            anreceipt.get("source_or_forcing_written") is False and
            set(anreceipt.get("outputs_SHA256",{}))==AN_EXPECT,
            "actual Stage13AN signed QC2 source boundary receipt changed")
    for name, expected_digest in anreceipt["outputs_SHA256"].items():
        require("/" not in name and "\\" not in name and
                digest(AN_DIR/name)==expected_digest,
                "actual original Stage13AN file SHA changed: "+name)
    ansummary=json.loads(must(AN_DIR/AN_SUM).read_text())
    require(ansummary.get("current_Stage13AI_research_shadow_missing_VPD_QBOT_HH")==45
            and ansummary.get("direct_tower_VPD_QC0_on_immediate_left") is False
            and ansummary.get("direct_tower_VPD_QC0_on_immediate_right") is False
            and ansummary.get("left_boundary_source_VPD_F_QC")==2
            and ansummary.get("right_boundary_source_VPD_F_QC")==2
            and ansummary.get("19HH_candidates_model_science_approved") is False,
            "signed previous QC2 source boundary science HOLD differs")
    require(gitblob(AM_CODE)==AM_GIT,"Stage13AM exact Python source Git blob changed")
    spec=importlib.util.spec_from_file_location("us_me6_stage13am_for_13an",must(AM_CODE))
    require(spec is not None and spec.loader is not None,"Stage13AM signed source import unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    require(mod.VER==AM_VER,"Stage13AM original science version changed")
    receipt=json.loads(must(AM_DIR/AM_REC).read_text())
    require(receipt.get("site")=="US-Me6" and receipt.get("version")==AM_VER
            and receipt.get("model_or_method_approved") is False
            and receipt.get("original_source_or_research_shadow_written") is False
            and set(receipt.get("outputs_SHA256",{}))==AM_NAMES,
            "actual Stage13AM signed report policy or file inventory changed")
    for name,h in receipt["outputs_SHA256"].items():
        require("/" not in name and "\\" not in name and digest(AM_DIR/name)==h,
                "actual Stage13AM scientific report SHA mismatch "+name)
    summary=json.loads(must(AM_DIR/AM_SUM).read_text())
    require(summary.get("site")=="US-Me6" and summary.get("event_original_HH")==19
            and summary.get("actual_2010_2025_original_QC0_joint_TandTdiff_hh")==165
            and summary.get("original_QC0_distinct_years")==11
            and summary.get("PREVIEW_19HH_water_physically_valid_count")==19
            and summary.get("PREVIEW_19HH_ice_supersaturation_count")==0
            and summary.get("PREVIEW_existing_19HH_site_VPD_QBOT_not_filled") is True
            and summary.get("model_input_or_science_method_approved") is False
            and summary.get("latest_Stage13AI_research_shadow_SHA256")==AI_SHA,
            "actual Stage13AM 19HH preview report not as user validated")
    source_event=pd.read_csv(must(AM_DIR/AM_EVENT),dtype={"native_time":str})
    edges=pd.read_csv(must(AM_DIR/AM_EDGE),dtype={"native_time":str})
    yearly=pd.read_csv(must(AM_DIR/AM_YEAR))
    require(len(source_event)==19 and
            pd.DatetimeIndex(pd.to_datetime(source_event.native_time)).equals(EVENT)
            and len(edges)==27 and len(yearly)==11,
            "Stage13AM native 19 event / original +/-2h source context coverage changed")
    al, raw, site, info, donors, band = mod.verify()
    require(raw.index.equals(site.index) and site.VPD_USE.isna().sum()==45
            and site.QBOT.isna().sum()==45 and site.loc[EVENT,"VPD_USE"].isna().all(),
            "actual latest Stage13AI 45 missing and original source time drift")
    biases=donors.donor_minus_original_measured_VPD_error_hPa.to_numpy(float)
    yrs=pd.to_datetime(donors.native_original_time).dt.year.to_numpy(int)
    require(len(biases)==165 and np.isfinite(biases).all()
            and np.unique(yrs).size==11, "actual original source QC0 donor population changed")
    overall=float(np.median(biases))
    require(np.isclose(overall,summary["donor_residual_median_to_subtract_hPa"],
                       rtol=0,atol=1e-8),
            "recomputed original 165 QC0 donor residual median differs from Stage13AM")
    model_t=site.loc[EVENT,"TA_USE"].to_numpy(float)
    companion_t=raw.loc[EVENT,"TA_ERA"].to_numpy(float)
    companion_v=raw.loc[EVENT,"VPD_ERA"].to_numpy(float)
    original_era_transfer=es(model_t)*companion_v/es(companion_t)
    original_trial=source_event.PREVIEW_calibrated_water_VPD_hPa.to_numpy(float)
    require(np.allclose(original_trial,original_era_transfer-overall,
                        rtol=0,atol=1e-8),
            "original signed 19HH measured QC0 corrected VPD preview changed")
    # Immediate unedited source edge and selected current VPD; check BOTH,
    # preserving QC2 and invalid water physics without claiming observed anchors.
    points=pd.date_range(LEFT-3*STEP, RIGHT+3*STEP, freq="30min")
    original=raw.loc[points]
    existing=site.loc[points]
    boundary=pd.DataFrame({
      "native_time":[str(t) for t in points],
      "location_role":["LEFT_ADJACENT" if t==LEFT else
                       "RIGHT_ADJACENT" if t==RIGHT else
                       "19HH_ORIGINAL_HOLD" if t in EVENT else
                       "EXTRA_2H_SOURCE_CONTEXT" for t in points],
      "original_tower_TA_F_C":original.TA_F.to_numpy(float),
      "original_tower_TA_F_QC":original.TA_F_QC.to_numpy(float),
      "original_tower_VPD_F_hPa":original.VPD_F.to_numpy(float),
      "original_tower_VPD_F_QC":original.VPD_F_QC.to_numpy(float),
      "original_companion_TA_ERA_C":original.TA_ERA.to_numpy(float),
      "original_companion_VPD_ERA_hPa":original.VPD_ERA.to_numpy(float),
      "original_source_VPD_equals_companion_ERA":np.isclose(original.VPD_F.to_numpy(float),
         original.VPD_ERA.to_numpy(float),atol=1e-8,rtol=0),
      "existing_site_TA_USE_C":existing.TA_USE.to_numpy(float),
      "existing_site_VPD_USE_hPa":existing.VPD_USE.to_numpy(float),
      "site_water_saturation_hPa":es(existing.TA_USE.to_numpy(float)),
      "source_original_VPD_water_physically_valid":
         (original.VPD_F.to_numpy(float)>0)&
         (original.VPD_F.to_numpy(float)<es(existing.TA_USE.to_numpy(float))),
      "existing_site_VPD_water_physically_valid":
         (existing.VPD_USE.to_numpy(float)>0)&
         (existing.VPD_USE.to_numpy(float)<es(existing.TA_USE.to_numpy(float))),
      "has_direct_tower_VPD_QC0_and_T_QC0":
         original.VPD_F_QC.eq(0).to_numpy() & original.TA_F_QC.eq(0).to_numpy(),
      "method_or_model_approved":False})
    first=boundary.loc[boundary.location_role.eq("LEFT_ADJACENT")].iloc[0]
    last=boundary.loc[boundary.location_role.eq("RIGHT_ADJACENT")].iloc[0]
    require(np.isclose(float(first.existing_site_VPD_USE_hPa),2.012,atol=1e-8)
            and np.isclose(float(last.existing_site_VPD_USE_hPa),1.814,atol=1e-8),
            "original two selected boundary native VPD values changed")
    # Find nearest actually measured BOTH T and VPD QC0 in the source
    # (not processed QC2 VPD or synthetic model interpolation).
    dates=raw.index
    q0=(raw.TA_F_QC.eq(0)&raw.VPD_F_QC.eq(0)&
        np.isfinite(raw[["TA_F","VPD_F"]]).all(axis=1)&
        (raw.VPD_F.to_numpy(float)>0)&
        (raw.VPD_F.to_numpy(float)<es(raw.TA_F.to_numpy(float)))&
        np.isclose(raw.TA_F.to_numpy(float),site.TA_USE.to_numpy(float),
                   rtol=0,atol=1e-7)&
        np.isclose(raw.VPD_F.to_numpy(float),site.VPD_USE.to_numpy(float),
                   rtol=0,atol=1e-7))
    nearest=[]
    for side,t,mask in (
        ("BEFORE",LEFT,(dates<START)),
        ("AFTER",RIGHT,(dates>END))):
        ids=dates[q0 & mask]
        if len(ids):
            choice=ids[-1] if side=="BEFORE" else ids[0]
            rr=raw.loc[choice]
            nearest.append({"side":side,"native_boundary_time":str(t),
              "nearest_actual_tower_VPD_and_T_QC0":str(choice),
              "distance_from_boundary_hours":float(abs(choice-t).total_seconds()/3600),
              "nearest_tower_T_C":float(rr.TA_F),"nearest_tower_VPD_hPa":float(rr.VPD_F),
              "nearest_tower_VPD_QC":float(rr.VPD_F_QC),"nearest_tower_T_QC":float(rr.TA_F_QC),
              "whether_a_direct_QC0_immediate_boundary":bool(choice==t)})
        else:
            nearest.append({"side":side,"native_boundary_time":str(t),
               "nearest_actual_tower_VPD_and_T_QC0":None,
               "distance_from_boundary_hours":None,
               "nearest_tower_T_C":None,"nearest_tower_VPD_hPa":None,
               "nearest_tower_VPD_QC":None,"nearest_tower_T_QC":None,
               "whether_a_direct_QC0_immediate_boundary":False})
    nearest=pd.DataFrame(nearest)
    experiments=[]
    for yr in sorted(set(yrs.tolist())):
        retain=yrs!=yr
        require(retain.sum()>=100 and np.unique(yrs[retain]).size>=9,
                "full-year withheld original QC0 donor insufficient")
        bias=float(np.median(biases[retain]))
        vv=original_era_transfer-bias
        q,ok=mod.qp(vv,model_t,site.loc[EVENT,"PSRF"].to_numpy(float))
        hi=100*(es(model_t)-vv)/mod.esi(model_t)
        left_jump=abs(vv[0]-float(first.existing_site_VPD_USE_hPa))
        right_jump=abs(float(last.existing_site_VPD_USE_hPa)-vv[-1])
        experiments.append({
          "held_out_original_QC0_source_year":int(yr),
          "source_train_QC0_HH":int(retain.sum()),
          "train_median_donor_bias_hPa":bias,
          "19HH_min_candidate_VPD_hPa":float(np.min(vv)),
          "19HH_max_candidate_VPD_hPa":float(np.max(vv)),
          "19HH_water_physically_valid_count":int(ok.sum()),
          "19HH_ice_supersaturation_count":int((hi>100).sum()),
          "left_boundary_abs_jump_hPa":float(left_jump),
          "right_boundary_abs_jump_hPa":float(right_jump),
          "largest_boundary_abs_jump_hPa":float(max(left_jump,right_jump)),
          "new_approval":False})
    stability=pd.DataFrame(experiments)
    require(len(boundary)==27 and len(nearest)==2 and len(stability)==11
            and stability.new_approval.eq(False).all(),
            "exact 27 HH original context, nearest QC0 and 11 year holdouts")
    # Independent vapour-pressure decomposition of exactly 27 original
    # halfhours. Only 19 missing entries receive values in an in-memory
    # preview; all 8 original QC2 context records are unchanged.
    signed_context=pd.read_csv(must(AN_DIR/AN_CONTEXT),dtype={"native_time":str})
    require(len(signed_context)==27 and
            signed_context.native_time.tolist()==boundary.native_time.tolist() and
            np.allclose(signed_context.original_tower_TA_F_C.to_numpy(float),
                        boundary.original_tower_TA_F_C.to_numpy(float),rtol=0,atol=1e-8) and
            np.allclose(signed_context.original_tower_VPD_F_hPa.to_numpy(float),
                        boundary.original_tower_VPD_F_hPa.to_numpy(float),rtol=0,atol=1e-8),
            "signed Stage13AN 27 exact original tower source records changed")
    t=existing.TA_USE.to_numpy(float)
    p=existing.PSRF.to_numpy(float)
    original_v=original.VPD_F.to_numpy(float)
    site_v=existing.VPD_USE.to_numpy(float)
    preview_v=site_v.copy()
    event_mask=points.isin(EVENT)
    preview_v[event_mask]=original_trial
    satw=es(t)
    sati=6.112*np.exp(22.46*t/(t+272.62))
    original_e=satw-original_v
    actual_e=satw-preview_v
    with np.errstate(invalid="ignore",divide="ignore"):
        qb=.622*(actual_e*100)/(p-.378*(actual_e*100))
        rwater=100*actual_e/satw
        rice=100*actual_e/sati
    physical=(np.isfinite(qb)&(qb>0)&(qb<.08)&
              (preview_v>0)&(preview_v<satw)&
              (p>50000)&(p<110000))
    require(len(points)==27 and np.isfinite([*t,*p,*preview_v,*actual_e,*qb]).all()
            and physical[event_mask].all()
            and (original_v[event_mask]>satw[event_mask]).all()
            and np.allclose(
                 qb[event_mask],
                 source_event.PREVIEW_calibrated_QBOT_kgkg.to_numpy(float),
                 atol=1e-8,rtol=0),
            "original 19 source VPD-water physics or signed 19 candidate QBOT changed")
    physics=pd.DataFrame({
      "native_time":[str(i) for i in points],
      "is_original_19HH_QC2_HOLD":event_mask,
      "original_tower_T_C":t,
      "original_tower_T_QC":original.TA_F_QC.to_numpy(float),
      "original_tower_VPD_hPa":original_v,
      "original_tower_VPD_QC":original.VPD_F_QC.to_numpy(float),
      "original_site_VPD_USE_hPa":site_v,
      "water_saturation_es_hPa":satw,
      "original_VPD_if_water_actual_vapour_e_hPa":original_e,
      "original_VPD_if_water_physically_valid":
          (original_v>0)&(original_v<satw),
      "mixed_QC2_borders_plus_19_PREVIEW_VPD_hPa":preview_v,
      "mixed_QC2_borders_plus_19_PREVIEW_actual_vapour_e_hPa":actual_e,
      "mixed_QC2_borders_plus_19_PREVIEW_QBOT_kgkg":qb,
      "mixed_QC2_borders_plus_19_PREVIEW_RHwater_pct":rwater,
      "mixed_QC2_borders_plus_19_PREVIEW_RHice_pct":rice,
      "mixed_QC2_borders_plus_19_PREVIEW_water_physics_valid":physical,
      "source_or_forcing_written":False})
    edge_rows=[]
    for label,before,after in (("LEFT",LEFT,START),("RIGHT",END,RIGHT)):
        i=points.get_loc(before);j=points.get_loc(after)
        require(j==i+1,"original immediate source boundary must be adjacent")
        edge_rows.append({
          "edge":label,"native_before":str(before),"native_after":str(after),
          "original_before_T_QC":float(original.TA_F_QC.iloc[i]),
          "original_after_T_QC":float(original.TA_F_QC.iloc[j]),
          "original_before_VPD_QC":float(original.VPD_F_QC.iloc[i]),
          "original_after_VPD_QC":float(original.VPD_F_QC.iloc[j]),
          "30min_T_change_C":float(t[j]-t[i]),
          "30min_water_saturation_es_change_hPa":float(satw[j]-satw[i]),
          "30min_mixed_preview_VPD_change_hPa":float(preview_v[j]-preview_v[i]),
          "30min_mixed_preview_actual_water_vapour_e_change_hPa":float(actual_e[j]-actual_e[i]),
          "30min_mixed_preview_QBOT_change_kgkg":float(qb[j]-qb[i]),
          "30min_mixed_preview_RHwater_change_percentage_points":float(rwater[j]-rwater[i]),
          "30min_mixed_preview_RHice_change_percentage_points":float(rice[j]-rice[i]),
          "both_original_tower_T_and_VPD_direct_QC0":False,
          "method_or_forcing_approved":False})
    edges=pd.DataFrame(edge_rows)
    require(np.isclose(edges.loc[0,"30min_T_change_C"],-9.757,atol=1e-7,rtol=0)
            and np.isclose(edges.loc[1,"30min_T_change_C"],2.760,atol=1e-7,rtol=0)
            and float(original.TA_F_QC.loc[LEFT])==2 and
            float(original.TA_F_QC.loc[START])==1 and
            original.loc[EVENT[1]:END,"TA_F_QC"].eq(0).all() and
            original.loc[LEFT:RIGHT,"VPD_F_QC"].eq(2).all(),
            "actual source temperature splice/QC2 borders or event QC changed")
    verdict={
      "version":VER,"site":"US-Me6",
      "actual_parent_stage13am_receipt_sha256":digest(AM_DIR/AM_REC),
      "source_years":"2010-2025",
      "current_Stage13AI_research_shadow_missing_VPD_QBOT_HH":45,
      "source_original_19HH_QC2_ERA_VPD_remain_HOLD":True,
      "direct_tower_VPD_QC0_on_immediate_left":bool(first.has_direct_tower_VPD_QC0_and_T_QC0),
      "direct_tower_VPD_QC0_on_immediate_right":bool(last.has_direct_tower_VPD_QC0_and_T_QC0),
      "left_boundary_source_VPD_F_QC":float(first.original_tower_VPD_F_QC),
      "right_boundary_source_VPD_F_QC":float(last.original_tower_VPD_F_QC),
      "left_boundary_source_water_physically_valid":
          bool(first.source_original_VPD_water_physically_valid),
      "right_boundary_source_water_physically_valid":
          bool(last.source_original_VPD_water_physically_valid),
      "source_165_QC0_median_ERA_transfer_bias_hPa":overall,
      "event_ERA_T_deviation_exceeds_8C":True,
      "19HH_candidates_model_science_approved":False,
      "source_or_model_data_modified":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    verdict["actual_parent_Stage13AN_receipt_sha256"]=digest(AN_DIR/AN_REC)
    verdict["nineteen_original_QC2_source_VPD_invalid_under_water_saturation_HH"]=19
    verdict["nineteen_19HH_mixed_source_preview_water_physical_count"]=int(physical[event_mask].sum())
    verdict["edge_temperature_VPD_es_actual_e_QBOT_RH_explanatory_transitions"]=edge_rows
    verdict["no_QC2_boundary_anchoring_or_event_humidity_repair"]=True
    print("STAGE13AO EXACT 27HH ORIGINAL SOURCE TEMPERATURE AND WATER VAPOUR PROFILE")
    print(physics.to_string(index=False))
    print("STAGE13AO 30MIN TEMPERATURE, VPD, ACTUAL VAPOUR e, QBOT, RH BOUNDARY DECOMPOSITION")
    print(edges.to_string(index=False))
    print("STAGE13AO ORIGINAL IMMEDIATE BOUNDARIES AND +/-2H SCIENCE CONTEXT")
    print(boundary.to_string(index=False))
    print("STAGE13AN NEAREST REAL MEASURED T AND VPD QC0 ON EACH SIDE")
    print(nearest.to_string(index=False))
    print("STAGE13AN EXACT 11 ORIGINAL QC0 WHOLE-YEAR-WITHHELD BIAS STABILITY")
    print(stability.to_string(index=False))
    print("STAGE13AN SCIENCE HOLD SUMMARY",json.dumps(verdict,indent=2))
    return boundary,nearest,stability,physics,edges,verdict
def main():
    ap=argparse.ArgumentParser()
    modes=ap.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","run"):modes.add_argument("--"+m,action="store_true")
    args=ap.parse_args()
    selftest()
    if args.self_test:return
    boundary,nearest,stability,physics,edges,summary=review()
    if args.check:
        print("STAGE13AO 19HH WATER VAPOUR SOURCE QC2 EDGE DECOMPOSITION READONLY CHECK PASS; NO WRITES")
        return
    out=ROOT/"reports"/("stage13an_Me6_19HH_QC2_boundary_QC0_anchor_source_READONLY_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
      "original_19HH_QC2_flanks_plusminus2h_tower_ERA_water_physics.csv":boundary,
      "nearest_original_measured_QC0_tower_T_VPD_each_side.csv":nearest,
      "11year_one_year_out_165_QC0_donor_bias_sensitivity_NO_APPROVAL.csv":stability,
      "27HH_original_source_water_vapour_and_mixed_preview_not_written.csv":physics,
      "two_30min_source_T_es_VPD_actual_e_QBOT_RH_edge_changes.csv":edges}
    for name,d in docs.items():d.to_csv(out/name,index=False,float_format="%.17g")
    summ="stage13ao_original_19HH_boundary_QC2_physics_summary.json"
    flag="NO_19HH_HUMIDITY_SOURCE_OR_QC2_BORDER_REPAIR_OR_MODEL_APPROVAL"
    (out/summ).write_text(json.dumps(summary,indent=2)+"\n")
    (out/flag).write_text("Stage13AO vapour physics explanatory audit only. Original tower/ERA and"
       " research shadow, model or scientific acceptance modification.\n")
    receipt={"version":VER,"site":"US-Me6","original_science_method_approved":False,
      "source_or_forcing_written":False,
      "outputs_SHA256":{name:digest(out/name) for name in [*docs,summ,flag]}}
    (out/"stage13an_source_science_READONLY_sha_receipt.json").write_text(
      json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AO READONLY SCIENCE REPORT DIR:",out)
    print("STAGE13AO 19HH QC2 VAPOUR PRESSURE AND QBOT EDGE DECOMPOSITION COMPLETE | NO REPAIR/DATM/SLURM")
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AO SOURCE SCIENCE HOLD:",exc,file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(2)

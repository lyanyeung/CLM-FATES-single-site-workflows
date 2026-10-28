#!/usr/bin/env python3
"""Stage13AM, US-Me6 2014/15 19-HH site-specific calibrated donor PREVIEW.

SHA-verifies actual Stage13AL's 2010-2025 true measured QC0 joint match:
tower T within ±3C of the original event median AND tower-minus-companion
ERA T within ±3C of the exceptional event median. Recompute the median
raw ERA-RH-transfer VPD bias of precisely those measured QC0 original rows.
No elevation correction, no ERA5-Land independence claim. Compute each
19-HH candidate physical water/ice humidity, QBOT and original boundary
jumps, with leave-one-year-out QC0 skill. Read-only report: NO correction
to even a separate trial/production forcing and NO automatic approval.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13am-v1-20261028-Me6-19HH-joint-QC0-calibrated-donor-PREVIEW"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AL_CODE=HERE/"13al_Me6_19HH_joint_cold_and_ERA_Tbias_QC0_leave_year_out_READONLY.py"
AL_GIT="440e02cd7fd54d2a3fc9661a977d55125c513dde"
AL_REPORT=ROOT/"reports/stage13al_Me6_19HH_2010_2025_joint_QC0_TandTdiff_READONLY_20261028T224805Z_7adf6189"
AL_RECEIPT="stage13al_READONLY_science_SHA_receipt.json"
AL_SUMMARY="stage13al_science_joint_temperature_donor_support_summary.json"
AL_BANDS="8_conditioned_actual_measured_QC0_ERA_RH_skill_LOYO.csv"
AL_DONORS="actual_source_QC0_joint_matched_native_ERA_donor_records.csv"
AL_MARKER="NO_HUMIDITY_REPAIR_OR_DONOR_SCIENCE_APPROVAL"
AL_NAMES={AL_SUMMARY,AL_BANDS,AL_DONORS,AL_MARKER}
AL_VER="batch03-stage13al-v1-20261028-Me6-joint-cold-ERA-deltaT-QC0-LOYO"
AI_SHA="b193388d4f82b47a7727c6ef9b2fdc25b37a56e4867d319224d1fc9327326f40"
START=pd.Timestamp("2014-12-31 23:30")
END=pd.Timestamp("2015-01-01 08:30")
H=pd.Timedelta(minutes=30)
EVENT=pd.date_range(START,END,freq="30min")
T_TOL=3.
DELTA_T_TOL=3.
def need(condition,msg):
    if not bool(condition):raise RuntimeError("STAGE13AM SIGNED SCIENCE HOLD: "+str(msg))
def must(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"file missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def gitblob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def esw(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def esi(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))
def qp(v,t,p):
    v=np.asarray(v,float);t=np.asarray(t,float);p=np.asarray(p,float)
    e=100*(esw(t)-v)
    den=p-.378*e
    with np.errstate(invalid="ignore",divide="ignore"):
        q=.622*e/den
    ok=(np.isfinite(q)&(v>0)&(v<esw(t))&(q>0)&(q<.08)&
       (p>50000)&(p<110000)&(den>0))
    return q,ok
def errors(e):
    a=np.asarray(e,float)
    a=a[np.isfinite(a)]
    return {"n":len(a),
            "bias_hPa":float(np.mean(a)) if len(a) else None,
            "median_bias_hPa":float(np.median(a)) if len(a) else None,
            "MAE_hPa":float(np.mean(abs(a))) if len(a) else None,
            "P90_abs_hPa":float(np.percentile(abs(a),90)) if len(a) else None}
def selftest():
    need(len(EVENT)==19 and np.isclose(np.median([.5,.7,.9]),.7)
         and np.isclose((.93-.59),.34)
         and bool(qp([.34],[-17.3],[95000])[1][0])
         and not bool(qp([-1],[-17.3],[95000])[1][0]),
         "exact event 19 HH, positive physical VPD and no unphysical donor values")
    print("STAGE13AM SELF-TEST PASS | 19 native HH, 165 original QC0 joint donors, water/ice and boundary report only; NO WRITES",flush=True)
def verify():
    need(gitblob(AL_CODE)==AL_GIT,"source Stage13AL Python Git SHA mismatch")
    spec=importlib.util.spec_from_file_location("stage13al_for_13am",must(AL_CODE))
    need(spec is not None and spec.loader is not None,"Stage13AL original source import unavailable")
    al=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(al)
    need(al.VER==AL_VER,"original Stage13AL version mismatch")
    receipt=json.loads(must(AL_REPORT/AL_RECEIPT).read_text())
    need(receipt.get("site")=="US-Me6" and receipt.get("version")==AL_VER
         and receipt.get("new_method_approved") is False
         and receipt.get("source_or_forcing_written") is False
         and set(receipt.get("output_SHA256",{}))==AL_NAMES,
         "actual Stage13AL original donor report signed inventory mismatch")
    for fn,hashval in receipt["output_SHA256"].items():
        need("/" not in fn and "\\" not in fn and sha(AL_REPORT/fn)==hashval,
             "original source QC0 donor report SHA mismatch "+fn)
    info=json.loads(must(AL_REPORT/AL_SUMMARY).read_text())
    need(info.get("site")=="US-Me6" and
         info.get("actual_model_original_years")=="2010–2025" and
         info.get("event_tower_minus_source_ERA_T_median_C")==-9.529 and
         info.get("event_tower_T_median_C")==-17.76 and
         info.get("current_research_shadow_VPD_QBOT_missing_HH")==45 and
         info.get("actual_16year_measured_QC0_original_rows")==247416 and
         info.get("study_has_not_established_safe_repair") is True and
         info.get("new_method_approval") is False,
         "actual Stage13AL accepted 19HH empirical source facts changed")
    bands=pd.read_csv(must(AL_REPORT/AL_BANDS),low_memory=False)
    donor=pd.read_csv(must(AL_REPORT/AL_DONORS),
                      dtype={"native_original_time":str},low_memory=False)
    need(len(bands)==8 and bands.may_use_for_missing_humidity_or_model.eq(False).all(),
         "Stage13AL source joint QC0 bins or approval status changed")
    specific=bands.loc[
      np.isclose(bands.tower_temperature_match_plusminus_C,T_TOL,rtol=0)&
      np.isclose(bands.tower_minus_ERA_temperature_match_plusminus_C,DELTA_T_TOL,rtol=0)]
    need(len(specific)==1 and int(specific.iloc[0].real_QC0_source_rows)==165
         and int(specific.iloc[0].real_QC0_unique_days)==28
         and int(specific.iloc[0].real_QC0_years)==11
         and int(specific.iloc[0].bias_adjustment_LOYO_test_HH)==165
         and np.isclose(specific.iloc[0].bias_adjustment_LOYO_MAE_hPa,.095807,atol=.00001)
         and np.isclose(specific.iloc[0].bias_adjustment_LOYO_p90_abs_hPa,.227903,atol=.00001)
         and bool(specific.iloc[0].joint_original_QC0_support_adequate_for_method_assessment),
         "exact signed 165 source real QC0 bin or LOYO empirical results changed")
    dd=donor.loc[
      np.isclose(donor.bin_siteT_tolerance_C,T_TOL,rtol=0)&
      np.isclose(donor.bin_site_minus_ERA_T_tolerance_C,DELTA_T_TOL,rtol=0)].copy()
    need(len(dd)==165 and dd.native_original_time.is_unique
         and len(pd.to_datetime(dd.native_original_time).dt.normalize().unique())==28
         and pd.to_datetime(dd.native_original_time).dt.year.nunique()==11
         and dd.source_tower_VPD_QC.eq(0).all() and dd.source_tower_T_QC.eq(0).all(),
         "actual Stage13AL 165 measured original QC0 source donor details changed")
    need(dd.original_source_and_model_unchanged.eq(True).all(),"source provenance flag changed")
    raw,site,_,_=al.audit()
    need(raw.index.equals(site.index) and site.VPD_USE.isna().sum()==45
         and site.QBOT.isna().sum()==45
         and site.loc[EVENT,"VPD_USE"].isna().all()
         and (raw.loc[EVENT,"VPD_F_QC"]==2).all(),
         "original source full site and Stage13AI 45 missing or winter HOLD drift")
    donor_idx=pd.DatetimeIndex(pd.to_datetime(dd.native_original_time))
    orig=raw.loc[donor_idx]
    site_obs=site.loc[donor_idx]
    need(np.all(orig.TA_F_QC.to_numpy(float)==0) and
         np.all(orig.VPD_F_QC.to_numpy(float)==0) and
         np.allclose(orig.TA_F.to_numpy(float),dd.tower_original_TA_F_C.to_numpy(float),rtol=0,atol=1e-8) and
         np.allclose(orig.VPD_F.to_numpy(float),dd.tower_original_VPD_F_hPa.to_numpy(float),rtol=0,atol=1e-8) and
         np.allclose(orig.TA_ERA.to_numpy(float),dd.companion_ERA_TA_C.to_numpy(float),rtol=0,atol=1e-8) and
         np.allclose(orig.VPD_ERA.to_numpy(float),dd.companion_ERA_VPD_hPa.to_numpy(float),rtol=0,atol=1e-8) and
         np.allclose(site_obs.VPD_USE.to_numpy(float),orig.VPD_F.to_numpy(float),rtol=0,atol=1e-8),
         "not all 165 donor original tower/ERA/site QC0 times are independent measured values")
    reconstructed=esw(orig.TA_F.to_numpy(float))*(
       orig.VPD_ERA.to_numpy(float)/esw(orig.TA_ERA.to_numpy(float)))
    need(np.allclose(reconstructed,
          dd.raw_ERA_RH_transferred_site_VPD_hPa.to_numpy(float),rtol=0,atol=1e-7) and
         np.allclose(reconstructed-orig.VPD_F.to_numpy(float),
          dd.donor_minus_original_measured_VPD_error_hPa.to_numpy(float),rtol=0,atol=1e-7),
         "source joint-QC0 residuals do not match original native observations")
    return al,raw,site,info,dd,specific.iloc[0]
def inspect():
    al,raw,site,summary,donor,binrow=verify()
    biases=donor.donor_minus_original_measured_VPD_error_hPa.to_numpy(float)
    years=pd.to_datetime(donor.native_original_time).dt.year.to_numpy(int)
    median_bias=float(np.median(biases))
    mean_bias=float(np.mean(biases))
    leftover,folds=al.loyo(years,biases)
    need(folds==11 and np.isfinite(leftover).all() and
         np.isclose(np.mean(abs(leftover)),binrow.bias_adjustment_LOYO_MAE_hPa,rtol=0,atol=1e-7),
         "actual signed 11-year source-only out-of-year validation changed")
    event=raw.loc[EVENT]
    ss=site.loc[EVENT]
    towerT=event.TA_F.to_numpy(float)
    et=event.TA_ERA.to_numpy(float)
    ev=event.VPD_ERA.to_numpy(float)
    originalV=event.VPD_F.to_numpy(float)
    modelT=ss.TA_USE.to_numpy(float)
    psrf=ss.PSRF.to_numpy(float)
    trial=esw(modelT)*ev/esw(et)
    adjusted=trial-median_bias
    baseq,basegood=qp(trial,modelT,psrf)
    correctedq,correctedgood=qp(adjusted,modelT,psrf)
    vapour=esw(modelT)-adjusted
    rhi=100*vapour/esi(modelT)
    rwh=100*vapour/esw(modelT)
    prev_time=START-H
    next_time=END+H
    need(prev_time in site.index and next_time in site.index
         and event.VPD_F_QC.eq(2).all()
         and np.allclose(originalV,ev,rtol=0,atol=1e-8)
         and np.allclose(event.TA_F.to_numpy(float),modelT,rtol=0,atol=1e-7),
         "19 exact held original tower/ERA source or nearest boundary absent")
    before=float(site.at[prev_time,"VPD_USE"])
    after=float(site.at[next_time,"VPD_USE"])
    values=[before,*adjusted.tolist(),after]
    steps=np.diff(values)
    eventout=pd.DataFrame({
       "native_time":[str(t) for t in EVENT],
       "original_tower_T_QC":event.TA_F_QC.to_numpy(float),
       "original_tower_T_C":modelT,
       "original_tower_VPD_QC":event.VPD_F_QC.to_numpy(float),
       "original_tower_VPD_hPa_HOLD":originalV,
       "source_companion_ERA_T_C":et,
       "original_site_minus_ERA_T_C":modelT-et,
       "source_companion_ERA_VPD_hPa":ev,
       "unadjusted_ERA_RH_transfer_VPD_hPa":trial,
       "donor_165_QC0_median_bias_subtracted_hPa":np.repeat(median_bias,19),
       "PREVIEW_calibrated_water_VPD_hPa":adjusted,
       "PREVIEW_calibrated_QBOT_kgkg":correctedq,
       "PREVIEW_calibrated_water_RH_pct":rwh,
       "PREVIEW_calibrated_ice_RH_pct":rhi,
       "PREVIEW_calibrated_water_physics_valid":correctedgood,
       "PREVIEW_calibrated_ice_supersaturation":rhi>100,
       "original_TA_USE_PSRF_and_source_ERA_unchanged":True,
       "new_research_shadow_or_model_approved":False})
    yearwise=pd.DataFrame({
       "source_year":sorted(set(years.tolist()))})
    yearwise["measured_QC0_HH"]=[int((years==y).sum()) for y in yearwise.source_year]
    yearwise["median_ERA_RH_transfer_minus_original_QC0_VPD_hPa"]=[
       float(np.median(biases[years==y])) for y in yearwise.source_year]
    yearwise["mean_ERA_RH_transfer_minus_original_QC0_VPD_hPa"]=[
       float(np.mean(biases[years==y])) for y in yearwise.source_year]
    boundaries=raw.loc[START-4*H:END+4*H,
                       ["TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"]].copy()
    boundaries.insert(0,"native_time",[str(t) for t in boundaries.index])
    model=site.reindex(boundaries.index)
    boundaries["existing_Stage13AI_site_VPD_hPa"]=model.VPD_USE.to_numpy(float)
    boundaries["existing_Stage13AI_QBOT_kgkg"]=model.QBOT.to_numpy(float)
    boundaries["inside_19_HH_no_model_replacement"]=boundaries.index.isin(EVENT)
    need(len(eventout)==19 and len(boundaries)==27 and yearwise.measured_QC0_HH.sum()==165,
         "19 event / 27 source boundaries / 165 donor population invariant")
    summary_out={
      "version":VER,"site":"US-Me6",
      "event_original_HH":19,
      "original_event_native_time_begin":str(START),
      "original_event_native_time_end":str(END),
      "actual_2010_2025_original_QC0_joint_TandTdiff_hh":165,
      "original_QC0_source_days":28,"original_QC0_distinct_years":11,
      "original_QC0_ERA_water_RH_transfer_error":errors(biases),
      "bias_corrected_measured_QC0_LOYO_error":errors(leftover),
      "bias_subtraction_training_estimator":"median of original joint 165 measured QC0 donor residuals, NOT trained on event",
      "donor_residual_median_to_subtract_hPa":median_bias,
      "donor_residual_mean_hPa":mean_bias,
      "source_event_ERA_RHwater_transferred_19H_hPa_min":float(np.min(trial)),
      "source_event_ERA_RHwater_transferred_19H_hPa_max":float(np.max(trial)),
      "PREVIEW_calibrated_19H_VPD_min":float(np.min(adjusted)),
      "PREVIEW_calibrated_19H_VPD_max":float(np.max(adjusted)),
      "PREVIEW_19HH_water_physically_valid_count":int(correctedgood.sum()),
      "PREVIEW_19HH_ice_supersaturation_count":int(np.sum(rhi>100)),
      "PREVIEW_19HH_ERA_T_absGT8":int(np.sum(abs(modelT-et)>8)),
      "PREVIEW_before_edge_existing_VPD_hPa":before,
      "PREVIEW_after_edge_existing_VPD_hPa":after,
      "PREVIEW_left_edge_abs_jump_hPa":float(abs(steps[0])),
      "PREVIEW_right_edge_abs_jump_hPa":float(abs(steps[-1])),
      "PREVIEW_max_native_step_over_edges_hPa":float(np.nanmax(abs(steps))),
      "PREVIEW_edges_both_finite":bool(np.isfinite([before,after]).all()),
      "PREVIEW_existing_19HH_site_VPD_QBOT_not_filled":True,
      "model_input_or_science_method_approved":False,
      "parent_Stage13AL_SHA_receipt":sha(AL_REPORT/AL_RECEIPT),
      "latest_Stage13AI_research_shadow_SHA256":AI_SHA,
      "original_tower_ERA_and_all_research_shadows_unchanged":True,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AM 19 NATIVE SOURCE 165 QC0 MEDIAN-BIAS-CORRECTED WATER/ICE PREVIEW",flush=True)
    print(eventout.to_string(index=False),flush=True)
    print("STAGE13AM 11 ORIGINAL QC0 SOURCE YEAR-BY-YEAR RESIDUAL BIASES",flush=True)
    print(yearwise.to_string(index=False),flush=True)
    print("STAGE13AM ORIGINAL 19HH SOURCE AND ADJACENT EDGE SCIENCE SUMMARY",json.dumps(summary_out,indent=2),flush=True)
    return eventout,boundaries,yearwise,summary_out
def main():
    p=argparse.ArgumentParser()
    opts=p.add_mutually_exclusive_group(required=True)
    for o in ("self-test","check","run"):opts.add_argument("--"+o,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    table,edges,yearwise,science=inspect()
    if args.check:
        print("STAGE13AM EXACT 19HH AND 165 QC0 DONORS PREVIEW READONLY CHECK PASS | ZERO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13am_Me6_19HH_QC0biasERA_water_ice_EDGES_PREVIEW_ONLY_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
       "19HH_calibrated_ERA_water_RH_candidate_QBOT_PREVIEW_NOT_APPROVED.csv":table,
       "19HH_original_plusminus2h_boundary_before_after_NO_REPAIR.csv":edges,
       "165_actual_measured_QC0_donor_residual_bias_by_year.csv":yearwise}
    for name,data in outputs.items():
        data.to_csv(out/name,index=False,float_format="%.17g")
    name="stage13am_19HH_joint_QC0_bias_source_science_summary.json"
    marker="NO_PRODUCTION_FORCING_OR_SHADOW_REPAIR_APPROVED"
    (out/name).write_text(json.dumps(science,indent=2)+"\n")
    (out/marker).write_text("Original data and all historical research"
       " shadows intact. Scientifically calibrated candidate values are"
       " DIAGNOSTIC ONLY; no new method approval, DATM, AD400, or Slurm.\n")
    receipt={"version":VER,"site":"US-Me6","model_or_method_approved":False,
       "original_source_or_research_shadow_written":False,
       "outputs_SHA256":{k:sha(out/k) for k in [*outputs,name,marker]}}
    (out/"stage13am_READONLY_source_science_SHA_receipt.json").write_text(
         json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AM READONLY SCIENCE REPORT DIR:",out,flush=True)
    print("STAGE13AM NINETEEN HH JOINT QC0 BIAS PREVIEW COMPLETE; NO SHADOW/FORCING/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AM ORIGINAL SOURCE SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

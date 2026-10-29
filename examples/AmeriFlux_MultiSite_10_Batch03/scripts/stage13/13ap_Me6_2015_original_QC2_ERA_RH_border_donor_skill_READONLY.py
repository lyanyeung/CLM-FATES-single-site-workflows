#!/usr/bin/env python3
"""US-Me6 Stage13AP: inspect ERA VPD vs ERA RH mapped to tower T on QC2 borders.

Verify exact successful Stage13AO 27 original source and 19HH preview via
signed SHA report, Stage13AM and latest Stage13AI source. Compare original
QC2 directly-used ERA VPD vs physically reconstructed ERA water RH at both
borders; verify site-specific T and T-ERA-T matched original measured QC0
skill for each border independently, including leave-year-out correction.
No approved model input/selected forcing, trial shadow or data is modified.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ap-v1-20261028-Me6-QC2-boundary-ERA-RH-mapped-QC0-donor"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AM_CODE=HERE/"13am_Me6_19HH_joint_QC0_bias_corrected_ERA_RH_event_PREVIEW_READONLY.py"
AM_GIT="df561eb8904b0147fc4a5aa0f977a5ec66545477"
AO=ROOT/"reports/stage13ao_Me6_19HH_QC2_vapour_e_QBOT_RH_source_READONLY_20261028T235737Z_a8d182d2"
AO_REC="stage13ao_source_science_READONLY_sha_receipt.json"
AO_SUM="stage13ao_original_19HH_boundary_QC2_physics_summary.json"
AO_MIX="27HH_original_source_water_vapour_and_mixed_preview_not_written.csv"
AO_NAMES={
 "original_19HH_QC2_flanks_plusminus2h_tower_ERA_water_physics.csv",
 "nearest_original_measured_QC0_tower_T_VPD_each_side.csv",
 "11year_one_year_out_165_QC0_donor_bias_sensitivity_NO_APPROVAL.csv",
 AO_MIX,
 "two_30min_source_T_es_VPD_actual_e_QBOT_RH_edge_changes.csv",
 AO_SUM,"NO_19HH_HUMIDITY_SOURCE_OR_QC2_BORDER_REPAIR_OR_MODEL_APPROVAL"}
AO_VER="batch03-stage13ao-v2-20261028-Me6-correct-signed-stage13an-paths-and-output"
AI_SHA="b193388d4f82b47a7727c6ef9b2fdc25b37a56e4867d319224d1fc9327326f40"
START=pd.Timestamp("2014-12-31 23:30")
END=pd.Timestamp("2015-01-01 08:30")
STEP=pd.Timedelta(minutes=30)
EVENT=pd.date_range(START,END,freq="30min")
LEFT=START-STEP
RIGHT=END+STEP
T_TOL=3.
DELTA_T_TOL=3.
def need(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AP ORIGINAL SOURCE SCIENCE HOLD: "+str(msg))
def must(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def gitblob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    t=np.asarray(t,float)
    with np.errstate(divide="ignore",over="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def physical(v,t,p):
    v=np.asarray(v,float);t=np.asarray(t,float);p=np.asarray(p,float)
    esat=es(t); e=esat-v; pa=e*100
    with np.errstate(divide="ignore",invalid="ignore"):
        q=.622*pa/(p-.378*pa)
        rh=100*e/esat
    good=(np.isfinite(v)&np.isfinite(t)&np.isfinite(p)&
          np.isfinite(q)&(v>0)&(v<esat)&(q>0)&(q<.08)&
          (p>50000)&(p<110000))
    return e,q,rh,good
def describe(errors):
    x=np.asarray(errors,float)
    x=x[np.isfinite(x)]
    n=len(x)
    return {"n":n,"mean_bias_hPa":float(np.mean(x)) if n else None,
      "median_bias_hPa":float(np.median(x)) if n else None,
      "MAE_hPa":float(np.mean(abs(x))) if n else None,
      "P90_abs_hPa":float(np.percentile(abs(x),90)) if n else None}
def selftest():
    need(len(EVENT)==19 and LEFT==pd.Timestamp("2014-12-31 23:00")
         and RIGHT==pd.Timestamp("2015-01-01 09:00"),
         "exact 19 original HH and native borders")
    t=-13.87;te=-8.517;v=1.814
    mapped=float(es(t)*v/es(te))
    e,q,rh,ok=physical([mapped],[t],[95000])
    need(abs(mapped-1.1837552713683563)<1e-6 and
         bool(ok[0]) and abs(e[0]-.9183918755740614)<1e-6,
         "independent ERA RH mapping and moisture amount self test")
    print("STAGE13AP SELF-TEST PASS | original QC2 ERA-VPD vs ERA-RH tower-T conversion, QC0 border donor scientific HOLD; NO WRITES",flush=True)
def verify():
    r=json.loads(must(AO/AO_REC).read_text())
    need(r.get("site")=="US-Me6" and r.get("version")==AO_VER
         and r.get("original_science_method_approved") is False
         and r.get("source_or_forcing_written") is False
         and set(r.get("outputs_SHA256",{}))==AO_NAMES,
         "actual Stage13AO 27-source original signed source receipt changed")
    for name,expected in r["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and
             sha(AO/name)==expected,
             "actual signed Stage13AO 27-source file checksum changed "+name)
    science=json.loads(must(AO/AO_SUM).read_text())
    need(science.get("site")=="US-Me6" and
         science.get("current_Stage13AI_research_shadow_missing_VPD_QBOT_HH")==45
         and science.get("nineteen_original_QC2_source_VPD_invalid_under_water_saturation_HH")==19
         and science.get("nineteen_19HH_mixed_source_preview_water_physical_count")==19
         and science.get("no_QC2_boundary_anchoring_or_event_humidity_repair") is True
         and science.get("Postv5") is False and
         science.get("DATM") is False and
         science.get("Slurm") is False,
         "actual Stage13AO 19 HH scientifically-held facts changed")
    need(gitblob(AM_CODE)==AM_GIT,
         "original Stage13AM source code Git blob changed")
    spec=importlib.util.spec_from_file_location("stage13am_for_stage13ap",must(AM_CODE))
    need(spec is not None and spec.loader is not None,
         "source Stage13AM module cannot be loaded")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    al,raw,site,_,donor,_=mod.verify()
    need(raw.index.equals(site.index) and len(raw)==280320
         and site.VPD_USE.isna().sum()==45
         and site.QBOT.isna().sum()==45
         and site.loc[EVENT,"VPD_USE"].isna().all(),
         "latest actual Stage13AI missing/HOLD site forcing changed")
    src=pd.read_csv(must(AO/AO_MIX),dtype={"native_time":str})
    idx=pd.DatetimeIndex(pd.to_datetime(src.native_time))
    expected_idx=pd.date_range(LEFT-3*STEP,RIGHT+3*STEP,freq="30min")
    need(len(src)==27 and idx.equals(expected_idx),
         "original Stage13AO all 27 HH context missing or reordered")
    measured=raw.loc[idx];current=site.loc[idx]
    need(np.allclose(src.original_tower_T_C.to_numpy(float),
          measured.TA_F.to_numpy(float),atol=1e-8,rtol=0) and
         np.allclose(src.original_tower_VPD_hPa.to_numpy(float),
          measured.VPD_F.to_numpy(float),atol=1e-8,rtol=0) and
         measured.VPD_F_QC.eq(2).all(),
         "all 27 Stage13AO signed VPD original tower native values drift")
    return al,raw,site,src,science
def evaluate():
    al,raw,site,src,prior=evaluate_context=verify()
    idx=pd.DatetimeIndex(pd.to_datetime(src.native_time))
    native=raw.loc[idx];selected=site.loc[idx]
    T=selected.TA_USE.to_numpy(float)
    Te=native.TA_ERA.to_numpy(float)
    Ver=native.VPD_ERA.to_numpy(float)
    old=native.VPD_F.to_numpy(float)
    P=selected.PSRF.to_numpy(float)
    mapped=es(T)*Ver/es(Te)
    raw_e,raw_q,raw_rh,raw_ok=physical(old,T,P)
    map_e,map_q,map_rh,map_ok=physical(mapped,T,P)
    existing=src.mixed_QC2_borders_plus_19_PREVIEW_VPD_hPa.to_numpy(float)
    em,qm,rhm,okm=physical(existing,T,P)
    need(np.all(np.isfinite([*T,*Te,*Ver,*P])) and
         np.allclose(old,Ver,atol=1e-8,rtol=0) and
         np.allclose(src.mixed_QC2_borders_plus_19_PREVIEW_actual_vapour_e_hPa,
                     em,atol=1e-7,rtol=0) and
         np.allclose(src.mixed_QC2_borders_plus_19_PREVIEW_QBOT_kgkg,
                     qm,atol=1e-8,rtol=0) and
         okm.all(),
         "original Stage13AO water-vapour accounting changed, reject candidates")
    report=pd.DataFrame({
      "native_time":[str(x) for x in idx],
      "original_tower_T_C":T,
      "original_tower_T_QC":native.TA_F_QC.to_numpy(float),
      "original_companion_ERA_T_C":Te,
      "original_tower_minus_ERA_T_C":T-Te,
      "original_VPD_F_QC":native.VPD_F_QC.to_numpy(float),
      "original_ERA_equal_source_VPD_hPa":old,
      "existing_mixed_19HH_PREVIEW_VPD_hPa":existing,
      "original_raw_QC2_direct_ERA_VPD_physical":raw_ok,
      "original_raw_QC2_direct_ERA_VPD_RHwater_pct":raw_rh,
      "original_raw_QC2_direct_ERA_VPD_actual_e_hPa":raw_e,
      "SOURCE_ERA_RH_at_original_tower_T_VPD_hPa":mapped,
      "SOURCE_ERA_RH_at_original_tower_T_physical":map_ok,
      "SOURCE_ERA_RH_at_original_tower_T_RHwater_pct":map_rh,
      "SOURCE_ERA_RH_at_original_tower_T_actual_e_hPa":map_e,
      "SOURCE_ERA_RH_at_original_tower_T_QBOT_kgkg":map_q,
      "source_ERA_relative_humidity_not_measured_tower_RH":True,
      "research_candidate_or_model_approved":False})
    years=raw.index.year.to_numpy()
    ta=raw.TA_F.to_numpy(float)
    tq=raw.TA_F_QC.to_numpy(float)
    vap=raw.VPD_F.to_numpy(float)
    vqc=raw.VPD_F_QC.to_numpy(float)
    era_t=raw.TA_ERA.to_numpy(float)
    era_v=raw.VPD_ERA.to_numpy(float)
    site_t=site.TA_USE.to_numpy(float)
    site_v=site.VPD_USE.to_numpy(float)
    site_p=site.PSRF.to_numpy(float)
    era_map=es(ta)*era_v/es(era_t)
    _,_,_,okraw=physical(vap,ta,site_p)
    _,_,_,okmap=physical(era_map,ta,site_p)
    mask=((tq==0)&(vqc==0)&okraw&okmap&
          np.isfinite([ta,era_t,era_v,vap,site_t,site_v,site_p]).all(axis=0)&
          np.isclose(ta,site_t,atol=1e-7,rtol=0)&
          np.isclose(vap,site_v,atol=1e-7,rtol=0)&
          raw.index.month.isin((12,1,2))&
          ~((raw.index>=pd.Timestamp("2014-12-30"))&
            (raw.index<pd.Timestamp("2015-01-03"))))
    rows=[]; donor_records=[]
    boundary_ids={"LEFT":idx.get_loc(LEFT),"RIGHT":idx.get_loc(RIGHT)}
    for side,k in boundary_ids.items():
        target_t=T[k];target_diff=T[k]-Te[k]
        m=mask & (abs(ta-target_t)<=T_TOL) & (
                  abs((ta-era_t)-target_diff)<=DELTA_T_TOL)
        source_err=era_map[m]-vap[m]
        yr=years[m]
        n=int(m.sum())
        days=int(raw.index[m].normalize().nunique())
        ny=int(np.unique(yr).size)
        cv, cv_years=al.loyo(yr,source_err)
        cv= cv[np.isfinite(cv)]
        # Empirical scientific skill *screen* only, never an approval.
        enough=n>=96 and days>=5 and ny>=3 and len(cv)==n
        bias=float(np.median(source_err)) if n else np.nan
        raw_v=float(old[k])
        mapped_v=float(mapped[k])
        corrected_v=mapped_v-bias if n else np.nan
        _,_,_,corrected_ok=physical([corrected_v],[T[k]],[P[k]])
        rows.append({
          "edge":side,
          "original_border_time":str(idx[k]),
          "original_tower_T_C":float(T[k]),
          "original_tower_T_QC":float(native.TA_F_QC.iloc[k]),
          "original_tower_minus_ERA_T_C":float(target_diff),
          "original_VPD_QC":float(native.VPD_F_QC.iloc[k]),
          "raw_source_ERA_VPD_hPa":raw_v,
          "source_ERA_RH_transferred_at_tower_T_VPD_hPa":mapped_v,
          "raw_vs_RH_transferred_difference_hPa":mapped_v-raw_v,
          "matched_real_QC0_winter_HH":n,
          "matched_real_QC0_distinct_days":days,
          "matched_real_QC0_years":ny,
          "matched_real_QC0_raw_ERA_RH_error_mean_hPa":
              float(np.mean(source_err)) if n else None,
          "matched_real_QC0_raw_ERA_RH_error_median_hPa":
              float(bias) if n else None,
          "matched_real_QC0_raw_ERA_RH_error_MAE_hPa":
              float(np.mean(abs(source_err))) if n else None,
          "matched_real_QC0_LOYO_evaluated_HH":len(cv),
          "matched_real_QC0_LOYO_test_years":cv_years,
          "matched_real_QC0_LOYO_MAE_hPa":
              float(np.mean(abs(cv))) if len(cv) else None,
          "exploratory_median_calibrated_border_VPD_hPa":
              float(corrected_v) if np.isfinite(corrected_v) else None,
          "exploratory_median_calibrated_border_physically_valid":
              bool(corrected_ok[0]),
          "matched_QC0_screen_has_minimum_support":bool(enough),
          "do_not_repair_original_border_or_model":True})
        for j in np.where(m)[0]:
            donor_records.append({
              "target_edge":side,
              "original_QC0_native_time":str(raw.index[j]),
              "measured_original_TA_F_QC":0,
              "measured_original_VPD_F_QC":0,
              "tower_T_C":float(ta[j]),
              "tower_minus_companion_ERA_T_C":float(ta[j]-era_t[j]),
              "original_measured_VPD_hPa":float(vap[j]),
              "source_ERA_RH_at_tower_T_VPD_hPa":float(era_map[j]),
              "source_original_measured_QC0_error_hPa":float(era_map[j]-vap[j]),
              "source_or_selected_forcing_written":False})
    borders=pd.DataFrame(rows)
    donors=pd.DataFrame(donor_records)
    contrasts=[]
    for side,at,before,after in (("LEFT",LEFT,LEFT,START),
                                ("RIGHT",RIGHT,END,RIGHT)):
        edge=borders.loc[borders.edge.eq(side)].iloc[0]
        i=idx.get_loc(before);j=idx.get_loc(after)
        need(j==i+1,"original immediate 30min native clocks not adjacent")
        held_side=i if before in EVENT else j
        border_side=i if at==before else j
        modelV=existing[held_side]
        candidate_options=[
          ("existing_original_QC2_boundary",float(old[border_side])),
          ("original_ERA_RH_transferred_to_border_tower_T",float(mapped[border_side]))]
        if edge.matched_QC0_screen_has_minimum_support and edge.exploratory_median_calibrated_border_physically_valid:
            candidate_options.append(("exploratory_border_QC0_median_calibrated",
                                      float(edge.exploratory_median_calibrated_border_VPD_hPa)))
        for scenario,borderV in candidate_options:
            whole=existing.copy()
            whole[border_side]=borderV
            ee,qq,rr,good=physical(whole,T,P)
            contrasts.append({
              "edge":side,"border_hypothesis":scenario,
              "original_border_native_time":str(idx[border_side]),
              "original_border_VPD_QC":float(native.VPD_F_QC.iloc[border_side]),
              "event_19HH_interior_calibration_unmodified":True,
              "border_hypothetical_VPD_hPa":borderV,
              "border_hypothetical_RHwater_pct":float(rr[border_side]),
              "30min_VPD_abs_jump_hPa":float(abs(whole[j]-whole[i])),
              "30min_actual_water_vapour_e_signed_change_hPa":float(ee[j]-ee[i]),
              "30min_actual_water_vapour_e_abs_jump_hPa":float(abs(ee[j]-ee[i])),
              "30min_QBOT_signed_change_kgkg":float(qq[j]-qq[i]),
              "30min_RHwater_signed_change_pp":float(rr[j]-rr[i]),
              "hypothesis_both_edge_values_water_physically_valid":
                  bool(good[i] and good[j]),
              "do_not_replace_original_QC2_border_or_19HH":True})
    comparison=pd.DataFrame(contrasts)
    need(len(borders)==2 and len(comparison)>=4 and
         comparison.do_not_replace_original_QC2_border_or_19HH.eq(True).all(),
         "two original native QC2 borders + two physical comparator hypotheses")
    summary={
      "version":VER,"site":"US-Me6",
      "original_2010_2025_site_tower_and_ERA_source_no_replacement":True,
      "original_19HH_QC2_VPD_invalid_under_site_water_saturation":19,
      "original_current_research_shadow_missing_VPD_QBOT_HH":45,
      "immediate_edges_source_VPD_QC2":True,
      "source_processed_ERA_RH_IS_NOT_INDEPENDENT_ERA5LAND":True,
      "original_Stage13AO_report_SHA256":sha(AO/AO_REC),
      "original_Stage13AI_shadow_SHA256":AI_SHA,
      "QC0_joint_matched_border_error":rows,
      "QC0_local_border_bias_method_automatically_approved":False,
      "original_19HH_event_candidate_science_approved":False,
      "source_or_forcing_or_shadow_written":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AP ORIGINAL 27-HH TOWER/ERA VPD TEMPERATURE CONSISTENCY",flush=True)
    print(report.to_string(index=False),flush=True)
    print("STAGE13AP TWO QC2 BORDER ORIGINAL QC0 EMPIRICAL DONOR SKILL",flush=True)
    print(borders.to_string(index=False),flush=True)
    print("STAGE13AP 30MIN VPD VAPOUR E QBOT EDGE-HYPOTHESIS CONTRASTS",flush=True)
    print(comparison.to_string(index=False),flush=True)
    print("STAGE13AP ORIGINAL SOURCE SCIENCE SUMMARY",json.dumps(summary,indent=2),flush=True)
    return report,borders,comparison,donors,summary
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    for option in ("self-test","check","run"):
        group.add_argument("--"+option,action="store_true")
    a=p.parse_args()
    selftest()
    if a.self_test:return
    report,borders,comparison,donors,summary=evaluate()
    if a.check:
        print("STAGE13AP SOURCE QC2 BORDERS ERA RH AND ORIGINAL QC0 REVIEW READONLY CHECK PASS; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13ap_Me6_19HH_two_QC2_border_ERA_RH_QC0_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
      "27HH_original_QC2_ERA_VPD_vs_RH_at_tower_T_NO_REPAIR.csv":report,
      "two_border_native_QC0_joint_T_ERA_donor_skill_NO_APPROVAL.csv":borders,
      "two_border_original_vs_ERA_RH_vs_QC0_border_vapour_QBOT.csv":comparison,
      "each_border_original_measured_QC0_donor_rows.csv":donors}
    for name,df in docs.items():df.to_csv(out/name,index=False,float_format="%.17g")
    name="stage13ap_border_ERA_RH_science_summary.json"
    marker="NO_ORIGINAL_QC2_BORDER_HUMIDITY_REPAIR_OR_19HH_MODEL_APPROVAL"
    (out/name).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text("Only independent original source QC0 statistical evidence."
       " No alterations to source, prior research-only shadows, DATM or Slurm.\n")
    receipt={"version":VER,"site":"US-Me6","new_science_approval":False,
      "original_source_or_forcing_written":False,
      "outputs_SHA256":{k:sha(out/k) for k in [*docs,name,marker]}}
    (out/"stage13ap_source_science_READONLY_SHA_receipt.json").write_text(
      json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AP READONLY SCIENCE REPORT DIR:",out,flush=True)
    print("STAGE13AP TWO ORIGINAL QC2 BORDER ERA RH AND QC0 SKILL REVIEW COMPLETE; NO SHADOW/FORCING/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AP SOURCE SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

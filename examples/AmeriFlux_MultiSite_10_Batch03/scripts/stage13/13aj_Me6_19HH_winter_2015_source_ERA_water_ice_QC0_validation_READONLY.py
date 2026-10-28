#!/usr/bin/env python3
"""Stage13AJ: US-Me6 2014-12-31/2015-01-01 19HH cold multi-gap REVIEW ONLY.

SHA-pin Stage13AH source calendar/alignment, actual Stage13AI 45-missing
research shadow and Stage13AH 46 original center+source-context report.
At each original time show independent tower T/QC, original VPD/QC, paired
source ERA T/VPD (NOT independent ERA5-Land), water/ice saturation, unmodified
source VPD plausibility, physical ERA RH transferred to site TA/PSRF and
candidate QBOT. Evaluate accuracy on separate true source VPD_F_QC0,
TA_F_QC0 observations in nearby winter data, with no gap filling.
No source repairs, approval, DATM, Slurm, production or trial shadow writes.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13aj-v1-20261028-Me6-19HH-2015-cold-water-ice-QC0"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AH_CODE=HERE/"13ah_Me6_46_remaining_native_missing_source_ERA_context_READONLY.py"
AH_BLOB="c0b7f0429d352c82a10becf8d59d8a5d62987edf"
AH=ROOT/"reports/stage13ah_US-Me6_46_native_humidity_missing_tower_ERA_context_READONLY_20261028T193402Z_6f75ea9d"
AH_REC="stage13ah_readonly_sha_receipt.json"
AH_SUM="stage13ah_exact_46_source_science_summary.json"
AH_DETAIL="ALL_46_original_tower_ERA_current_VPD_QBOT_no_approval.csv"
AH_CONTEXT="ALL_46_original_before_after_2h_each_ERA_and_tower.csv"
AH_CLUSTERS="46_missing_contiguous_original_native_clusters.csv"
AH_GROUP="46_missing_source_run_and_science_method_review_counts.csv"
AH_EXPECT={AH_SUM,AH_DETAIL,AH_CONTEXT,AH_CLUSTERS,AH_GROUP,
           "NO_NEW_OPERATOR_APPROVAL_NO_SOURCE_OR_FORCING_MODEL_WRITES"}
AI=ROOT/"science_trials/stage13ai_Me6_20151111_0900_VPD_GT_ESphysically_invalid_QC1_SINGLE_RESEARCH_ONLY_20261028T193928Z_0eaab8b2"
AI_CSV="US-Me6_STAGE13AI_Run14_20151111_0900_physically_invalid_QC1_SINGLE_ONLY_NOLEAP.csv"
AI_REC="stage13ai_one_invalid_source_HH_SHA_receipt.json"
AI_SCOPE="stage13ai_one_invalid_VPD_QC1_science_scope.json"
AI_NOTE="RESEARCH_ONLY_ONE_PHYSICALLY_INVALID_QC1_HH_NEIGHBOR_QC1_NOT_OBSERVED_QC0"
AI_VER="batch03-stage13ai-v1-20261028-Me6-one-physically-invalid-QC1-native-0900"
AF=ROOT/"science_trials/stage13af_Me6_20151112_1330_originalQC1_single_spike_RESEARCH_ONLY_20261028T172815Z_c5ca5d8d"
AF_CSV="US-Me6_STAGE13AF_20151112_1330_Run14_oneQC1_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AF_SHA="3df2fd258157f2a70d8d0b6dd0de865980bf6505c4da0e6a58e6058e2610b1b0"
OLD_T=pd.Timestamp("2015-11-11 09:00")
START=pd.Timestamp("2014-12-31 23:30")
END=pd.Timestamp("2015-01-01 08:30")
H=pd.Timedelta(minutes=30)
EVENT=pd.date_range(START,END,freq="30min")
OBS_RADIUS=pd.Timedelta(days=21)
TEMP_BAND=3.0
def need(ok,message):
    if not bool(ok):raise RuntimeError("STAGE13AJ ORIGINAL SOURCE/SCIENCE HOLD: "+str(message))
def must(x):
    p=Path(x)
    need(p.is_file() and not p.is_symlink(),"source file absent or symlink "+str(p))
    return p
def sha(x):
    h=hashlib.sha256()
    with must(x).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def gitblob(x):
    b=must(x).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def ew(temp):
    t=np.asarray(temp,dtype=float)
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp((17.67*t)/(t+243.5))
def ei(temp):
    t=np.asarray(temp,dtype=float)
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp((22.46*t)/(t+272.62))
def qfrom(v,t,p):
    v=np.asarray(v,float);t=np.asarray(t,float);p=np.asarray(p,float)
    es=ew(t);e=100*(es-v);den=p-.378*e
    with np.errstate(divide="ignore",invalid="ignore"):
        q=.622*e/den
    good=(np.isfinite(q)&np.isfinite(es)&np.isfinite(v)&np.isfinite(p)
       &(p>50000)&(p<110000)&(v>0)&(v<es)&(q>0)&(q<.08)&(den>0))
    return q,good
def native(s):
    idx=pd.DatetimeIndex(pd.to_datetime(s.astype(str).str.replace(
        r"[^0-9]","",regex=True).str[:12],format="%Y%m%d%H%M",errors="raise"))
    need(len(idx)==280320 and idx.is_unique and idx.is_monotonic_increasing
         and not ((idx.month==2)&(idx.day==29)).any(),
         "original exact full NOLEAP timeline")
    return idx
def selftest():
    need(len(EVENT)==19 and EVENT[0]==START and EVENT[-1]==END,
         "one exact 19-half-hour across-year source episode")
    need(float(ew(-17.3))<2.1 and float(ew(-17.3))>1.5
         and float(ei(-17.3))<float(ew(-17.3))
         and not bool(qfrom([2.2],[-17.3],[95000])[1][0]),
         "cold water-vs-ice saturation and negative absolute vapour guard")
    q,ok=qfrom([.9],[-17.3],[95000])
    need(bool(ok[0]) and q[0]>0,"cold ERA relative humidity hypothesis not physically tested")
    print("STAGE13AJ SELF-TEST PASS | exactly 19 cold native HH, source VPD water/ice diagnostics, no retrospective data edits; NO WRITES",flush=True)
def verify():
    need(gitblob(AH_CODE)==AH_BLOB,
         "signed exact full-source original Stage13AH Python changed")
    spec=importlib.util.spec_from_file_location("stage13ah_for_stage13aj",must(AH_CODE))
    need(spec is not None and spec.loader is not None,"Stage13AH source module unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER=="batch03-stage13ah-v3-20261028-Me6-independent-tower-ERA-calendar-coverage",
         "signed native tower/ERA read scope changed")
    raw,old,runs,prov,coverage=mod.read_confirmed()
    need(coverage["tower"]["missing_native_rows_in_original_source"]==0
         and coverage["era"]["missing_native_rows_in_original_source"]==0,
         "original 19 period tower/ERA time coverage no longer exact")
    receipt=json.loads(must(AH/AH_REC).read_text())
    need(receipt.get("site")=="US-Me6" and
         receipt.get("version")==mod.VER and
         receipt.get("new_method_approved") is False and
         receipt.get("source_or_forcing_written") is False and
         set(receipt.get("outputs_SHA256",{}))==AH_EXPECT,
         "original 46 source science signed receipt mismatch")
    for name,digest in receipt["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AH/name)==digest,
             "signed original AH science evidence changed "+name)
    summ=json.loads(must(AH/AH_SUM).read_text())
    need(summ.get("last_census_stage13af_vpd_missing_HH")==46
         and summ.get("missing_clusters")==20 and
         summ.get("latest_AF_research_shadow_SHA256")==AF_SHA,
         "actual original AH 46 / 20 science facts changed")
    d=pd.read_csv(must(AH/AH_DETAIL),dtype={"native_time":str},low_memory=False)
    c=pd.read_csv(must(AH/AH_CLUSTERS),low_memory=False)
    need(len(d)==46 and len(c)==20 and
         c.loc[c.missing_cluster_id.eq(1),"length_HH"].tolist()==[19] and
         c.loc[c.missing_cluster_id.eq(1),"first_native_time"].tolist()==[str(START)] and
         c.loc[c.missing_cluster_id.eq(1),"last_native_time"].tolist()==[str(END)],
         "exact first original 19 HH source missing group changed")
    subset=d.loc[d.missing_cluster_id.eq(1)].copy()
    need(len(subset)==19 and
         pd.DatetimeIndex(pd.to_datetime(subset.native_time)).equals(EVENT)
         and set(subset.science_review_category)=={"HOLD_MULTI_OR_NEIGHBOR_MISSING_SOURCE"}
         and subset.source_tower_VPD_F_QC.eq(2).all(),
         "actual first 19 original source event identities/QC changed")
    ai=json.loads(must(AI/AI_REC).read_text())
    need(ai.get("site")=="US-Me6" and ai.get("version")==AI_VER
         and ai.get("parent_Stage13AF_SHA256")==AF_SHA
         and ai.get("separate_research_shadow") is True
         and ai.get("production_forcing_or_source_written") is False
         and set(ai.get("output_SHA256",{}))=={AI_CSV,AI_SCOPE,AI_NOTE},
         "actual one-point Stage13AI source/receipt changed")
    for name,digest in ai["output_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AI/name)==digest,
             "latest actual one-point research shadow receipt SHA changed "+name)
    science=json.loads(must(AI/AI_SCOPE).read_text())
    need(science.get("original_full_site_missing_VPD_QBOT_HH_before")==46
         and science.get("separate_research_shadow_missing_after")==45
         and science.get("source_ERA_tower_and_time_unchanged") is True
         and science.get("prior_2015_2017_operator_approved_original_11_HH_unchanged") is True
         and science.get("forcings_production_written") is False,
         "original Stage13AI actual 46->45/approved record scope drift")
    current=pd.read_csv(must(AI/AI_CSV),dtype={"time":str},low_memory=False)
    current.index=native(current.time)
    need(old.index.equals(current.index)
         and set(EVENT).issubset(current.index),
         "original model/source NOLEAP native clock changed")
    parent=pd.read_csv(must(AF/AF_CSV),dtype={"time":str},low_memory=False)
    parent.index=native(parent.time)
    need(sha(AF/AF_CSV)==AF_SHA and
         list(parent.columns)==list(current.columns) and
         parent.index.equals(current.index),
         "original parent Stage13AF full source schema/clock altered")
    for col in parent.columns:
        if col=="time":
            need(parent[col].equals(current[col]),"source NOLEAP time rewritten")
            continue
        x=parent[col].to_numpy(float);y=current[col].to_numpy(float)
        changed=set(parent.index[~np.isclose(x,y,rtol=0,atol=1e-12,equal_nan=True)])
        if col in ("VPD_USE","QBOT"):
            need(changed=={OLD_T},"exact one Stage13AI prior approved source time missing")
        else:need(not changed,"forbidden site forcing modification "+col)
    missv=~np.isfinite(current.VPD_USE.to_numpy(float))
    missq=~np.isfinite(current.QBOT.to_numpy(float))
    need(int(missv.sum())==45 and np.array_equal(missv,missq)
         and missv[current.index.get_indexer(EVENT)].all(),
         "current latest research shadow 45 missing / 19 held site rows identity changed")
    # Verify each original tower/ERA VPD/T agrees with the independently
    # produced signed 46-record source report. Never use parent forcing
    # VPD to infer an original station observation.
    rr=raw.loc[EVENT]
    for k,cols in (("TA_F","source_tower_TA_F_C"),
                   ("TA_F_QC","source_tower_TA_F_QC"),
                   ("VPD_F","source_tower_VPD_F_hPa"),
                   ("VPD_F_QC","source_tower_VPD_F_QC"),
                   ("TA_ERA","source_companion_ERA_TA_C"),
                   ("VPD_ERA","source_companion_ERA_VPD_hPa")):
        need(np.allclose(rr[k].to_numpy(float),subset[cols].to_numpy(float),
                         rtol=0,atol=1e-7,equal_nan=True),
             "original native 19 time tower+companion ERA no longer matches signed AH: "+k)
    return raw,current,prov,coverage,science
def diagnostics():
    raw,site,prov,coverage,science=verify()
    z=raw.loc[EVENT];x=site.loc[EVENT]
    t=z.TA_F.to_numpy(float);v=z.VPD_F.to_numpy(float)
    qc=z.VPD_F_QC.to_numpy(float); tq=z.TA_F_QC.to_numpy(float)
    et=z.TA_ERA.to_numpy(float);ev=z.VPD_ERA.to_numpy(float)
    st=x.TA_USE.to_numpy(float);p=x.PSRF.to_numpy(float)
    es_era=ew(et)
    with np.errstate(invalid="ignore",divide="ignore"):
        era_rh=100*(1-ev/es_era)
        pred=ew(st)*(1-era_rh/100)
        actual_e=ew(st)-pred
        rhi=100*actual_e/ei(st)
    pred_q,pred_ph=qfrom(pred,st,p)
    orig_q,orig_ph=qfrom(v,st,p)
    temp_match=np.isfinite(t)&np.isfinite(st)&np.isclose(t,st,atol=1e-7,rtol=0)
    need(np.isfinite([*st,*p]).all() and np.isfinite([*t,*v,*et,*ev]).all()
         and np.all(qc==2) and
         np.all(x.VPD_USE.isna()) and np.all(x.QBOT.isna()),
         "site T/P, tower/ERA native values or 19-HH original QC changed")
    event=pd.DataFrame({
      "native_time":[str(ti) for ti in EVENT],
      "source_original_TA_F_C":t,
      "source_original_TA_F_QC":tq,
      "current_site_TA_USE_C":st,
      "current_site_original_T_matches_tower_T":temp_match,
      "current_site_PSRF_Pa":p,
      "source_original_VPD_F_hPa":v,
      "source_original_VPD_F_QC":qc,
      "source_companion_TA_ERA_C":et,
      "source_companion_VPD_ERA_hPa":ev,
      "source_VPD_equals_companion_ERA_VPD":np.isclose(v,ev,atol=1e-8,rtol=0),
      "site_esat_water_hPa":ew(st),
      "site_esat_ice_hPa":ei(st),
      "source_water_actual_vapour_e_hPa_if_VPD_defined_water":ew(st)-v,
      "source_VPD_implies_negative_vapour_under_water_definition":v>ew(st),
      "source_q_if_water_definition_kgkg_DIAGNOSTIC_ONLY":orig_q,
      "original_source_VPD_site_water_physically_valid":orig_ph,
      "source_companion_ERA_RHwater_pct":era_rh,
      "candidate_ERA_RHwater_transferred_site_VPD_hPa":pred,
      "candidate_ERA_RHwater_transferred_site_QBOT_kgkg":pred_q,
      "candidate_transferred_site_RHice_pct":rhi,
      "candidate_supersaturated_wrt_ice":rhi>100,
      "candidate_ERA_RHtransfer_water_physically_valid":pred_ph,
      "absolute_source_to_companion_ERA_T_difference_C":abs(t-et),
      "absolute_current_site_to_companion_ERA_T_difference_C":abs(st-et),
      "has_QC0_direct_measured_site_T":tq==0,
      "new_candidate_operator_approved":False})
    # Nearby independent ORIGINAL tower VPD QC0 analogue validation.
    # Exclude both whole held days and ±1 day; do not train on reconstruction.
    near=(raw.index>=START-OBS_RADIUS)&(raw.index<=END+OBS_RADIUS)
    available=raw.loc[near]
    selected=site.reindex(available.index)
    qc0=(available.VPD_F_QC.eq(0)&available.TA_F_QC.eq(0)&
         np.isfinite(available[["TA_F","VPD_F","TA_ERA","VPD_ERA"]]).all(axis=1)&
         np.isfinite(selected[["TA_USE","VPD_USE","PSRF"]]).all(axis=1)&
         np.isclose(available.TA_F,selected.TA_USE,atol=1e-7,rtol=0)&
         np.isclose(available.VPD_F,selected.VPD_USE,atol=1e-7,rtol=0))
    day=available.index.normalize()
    # Strict ±1-day event embargo. No calibration, so this is an
    # independent direct observation assessment, not a fitted model CV.
    qc0=qc0 & ((day<pd.Timestamp("2014-12-30")) |
               (day>pd.Timestamp("2015-01-02")))
    a=available.loc[qc0].copy()
    obsT=a.TA_F.to_numpy(float);obsV=a.VPD_F.to_numpy(float)
    eraT=a.TA_ERA.to_numpy(float);eraV=a.VPD_ERA.to_numpy(float)
    siteP=selected.loc[qc0,"PSRF"].to_numpy(float)
    with np.errstate(invalid="ignore",divide="ignore"):
        obs_rh=100*(1-obsV/ew(obsT))
        ar=100*(1-eraV/ew(eraT))
        ppred=ew(obsT)*(1-ar/100)
        errors=ppred-obsV
    pq,physical=qfrom(ppred,obsT,siteP)
    cold=np.isfinite(obsT)&(abs(obsT-float(np.median(st)))<=TEMP_BAND)
    match=np.isfinite(errors)&np.isfinite(ar)&np.isfinite(obs_rh)&physical&(
          (obs_rh>0)&(obs_rh<100)&(ar>0)&(ar<100))
    analogue=pd.DataFrame({
       "native_time":[str(i) for i in a.index],
       "tower_original_VPD_F_QC0_hPa":obsV,
       "tower_original_TA_F_QC0_C":obsT,
       "paired_source_ERA_T_C":eraT,
       "paired_source_ERA_VPD_hPa":eraV,
       "original_tower_RHwater_pct":obs_rh,
       "paired_source_ERA_RHwater_pct":ar,
       "candidate_transferred_to_tower_VPD_hPa":ppred,
       "candidate_QBOT_kgkg_DIAGNOSTIC":pq,
       "actual_candidate_minus_original_QC0_VPD_hPa":errors,
       "matches_19HH_ambient_cold_T_within_3C":cold,
       "water_physics_and_observed_QC0_valid":match,
       "all_original_source_QC0_unchanged":True})
    def metrics(ok):
        eligible=analogue.loc[ok]
        err=eligible.actual_candidate_minus_original_QC0_VPD_hPa.to_numpy(float)
        n=len(err)
        return {"matched_source_QC0_HH":n,
          "matched_original_QC0_native_dates":int(pd.to_datetime(eligible.native_time).dt.normalize().nunique()) if n else 0,
          "MAE_hPa":float(np.mean(abs(err))) if n else None,
          "median_abs_error_hPa":float(np.median(abs(err))) if n else None,
          "P90_abs_error_hPa":float(np.percentile(abs(err),90)) if n else None,
          "fraction_abs_error_GT_0p5hPa":float(np.mean(abs(err)>.5)) if n else None,
          "signed_bias_hPa":float(np.mean(err)) if n else None}
    scores={"all_within_21days_QC0":metrics(match),
      "cold_QC0_within_3C_of_19HH_median_site_T":metrics(match&cold)}
    bfirst=START-4*H;blast=END+4*H
    bb=raw.loc[bfirst:blast]
    xx=site.reindex(bb.index)
    boundary=bb[["TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"]].copy()
    boundary.insert(0,"native_time",[str(ti) for ti in bb.index])
    boundary["within_19HH_source_episode"]=bb.index.isin(EVENT)
    boundary["after_Stage13AI_site_T_C"]=xx.TA_USE.to_numpy(float)
    boundary["after_Stage13AI_site_VPD_hPa"]=xx.VPD_USE.to_numpy(float)
    boundary["after_Stage13AI_site_QBOT_kgkg"]=xx.QBOT.to_numpy(float)
    need(len(event)==19 and len(boundary)==27 and
         len(analogue)==int(qc0.sum()) and
         set(EVENT)==set(pd.to_datetime(event.native_time)),
         "full exact 19 HH + 2hour edge or eligible original QC0 row scope not matched")
    summary={"version":VER,"site":"US-Me6",
      "original_native_event_start":str(START),"original_native_event_end":str(END),
      "original_native_HH":19,"remaining_original_VPD_QBOT_missing_HH_after_Stage13AI":45,
      "nineteen_original_VPD_F_QC2_HH":int(np.sum(qc==2)),
      "nineteen_source_tower_temperature_QC0_HH":int(np.sum(tq==0)),
      "nineteen_original_source_VPD_equal_companion_ERA_hh":
           int(event.source_VPD_equals_companion_ERA_VPD.sum()),
      "nineteen_original_VPD_invalid_at_site_temperature_wrt_water_count":
           int((~orig_ph).sum()),
      "hypothetical_ERA_RHwater_transfer_physically_valid_count":
           int(pred_ph.sum()),
      "hypothetical_ERA_RHwater_transfer_ice_supersaturated_count":
           int((rhi>100).sum()),
      "QC0_independent_source_temperature_conditioned_validation":scores,
      "empirical_ERA_transfer_science_method_passed":False,
      "source_companion_ERA_is_not_independent_ERA5_land":True,
      "water_vs_ice_saturation_formula_approximation_only":True,
      "original_site_model_native_clock_unchanged":True,
      "preexisting_Stage13AI_full_source_SHA256":sha(AI/AI_CSV),
      "new_repair_or_approval":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AJ 19 ORIGINAL TOWER + ERA SOURCE NATIVE WATER/ICE PHYSICS",flush=True)
    cols=["native_time","source_original_TA_F_C","source_original_TA_F_QC",
          "current_site_TA_USE_C","source_original_VPD_F_hPa",
          "source_companion_TA_ERA_C","source_companion_VPD_ERA_hPa",
          "site_esat_water_hPa","site_esat_ice_hPa",
          "source_VPD_implies_negative_vapour_under_water_definition",
          "source_companion_ERA_RHwater_pct",
          "candidate_ERA_RHwater_transferred_site_VPD_hPa",
          "candidate_transferred_site_RHice_pct",
          "candidate_ERA_RHtransfer_water_physically_valid"]
    print(event[cols].to_string(index=False),flush=True)
    print("STAGE13AJ SOURCE QC0 COLD-ANALOGUE VALIDATION",
          json.dumps(scores,indent=2),flush=True)
    print("STAGE13AJ SCIENCE SUMMARY",json.dumps(summary,indent=2),flush=True)
    return event,boundary,analogue,summary
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","run"):group.add_argument("--"+m,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    e,b,a,summary=diagnostics()
    if args.check:
        print("STAGE13AJ 19HH COLD SOURCE AND QC0 READONLY SCIENCE CHECK PASS | ZERO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13aj_Me6_2015_crossyear_19HH_ERA_water_ice_QC0_READONLY_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={
      "19_original_native_tower_ERA_water_ice_candidate_NOT_APPROVED.csv":e,
      "19HH_2h_before_after_source_tower_ERA_NO_REPAIR.csv":b,
      "nearby_original_QC0_independent_ERA_RH_transfer_analogues.csv":a}
    for name,df in docs.items():df.to_csv(out/name,index=False,float_format="%.17g")
    inf="stage13aj_original_19HH_science_coverage_and_QC0_summary.json"
    marker="NO_19HH_ERA_REPAIR_OR_SCIENCE_APPROVAL"
    (out/inf).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text("Original tower/companion ERA and Stage13AI full source were verified"
       " and not modified; water/ice and QC0 comparisons are diagnostic only."
       " No model code acceptance or humidity replacement verified.\n")
    rec={"version":VER,"site":"US-Me6","source_or_forcing_written":False,
      "model_approval":False,
      "outputs_SHA256":{name:sha(out/name) for name in [*docs,inf,marker]}}
    (out/"stage13aj_READONLY_science_SHA_receipt.json").write_text(json.dumps(rec,indent=2)+"\n")
    print("STAGE13AJ READONLY SCIENCE REPORT DIR:",out,flush=True)
    print("STAGE13AJ NINETEEN COLD ORIGINAL SOURCE WATER ICE QC0 SCIENCE REPORT COMPLETE | NO REPAIR/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13AJ SCIENCE HOLD:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

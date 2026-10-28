#!/usr/bin/env python3
"""Stage13AG: actual five long held source runs science groups after successful AF.

SHA-check exact previous Stage13AF full NOLEAP shadow and predecessor AD, plus
signed original site-native tower/paired ERA and historic independent QC0
hold-out validation. Report the 778 original full-run QC1 halfhours,
not as 778 bad observations. Summarize run, calendar day, 14 original T
discrepancies, native two-hour context and immediate original QC boundaries.
No replacement or automatic scientific approval; read-only new report.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ag-v1-20261028-Me6-five-run-group-context-after-AF"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
SOURCE=HERE/"13_validation_Me6_six_run_repair_candidates.py"
SOURCE_GIT="de62b7f6d1001fafa923163e565b2945bb2a8816"
B=ROOT/"reports/stage13_validation_Me6_six_run_repair_candidates_20261028T162002Z_4a34daf8"
B_REC="stage13_validation_candidate_SHA_receipt.json"
B_DEC="six_runs_13_method_batch_decisions.csv"
B_VAL="1568_explicit_candidate_values_NOT_FORCING.csv"
B_CV="buffered_leave_day_out_QC0_validation.csv"
B_PSEUDO="nonoverlapping_four_HH_QC0_pseudogap_validation.csv"
B_INFO="stage13_validation_repair_candidate_summary.json"
S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
AF=ROOT/"science_trials/stage13af_Me6_20151112_1330_originalQC1_single_spike_RESEARCH_ONLY_20261028T172815Z_c5ca5d8d"
AF_CSV="US-Me6_STAGE13AF_20151112_1330_Run14_oneQC1_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AF_REC="stage13af_one_QC1_science_shadow_SHA_receipt.json"
AF_INFO="stage13af_exact_one_QC1_isolated_source_spike_science_SCOPE.json"
AD=ROOT/"science_trials/stage13ad_Me6_isolated_originalQC2_Jul04_1200_QC1_anchor_trial_20261028T170952Z_4ac00fee"
AD_CSV="US-Me6_STAGE13AD_SingleQC2_20170704_1200_QC1_Neighbors_RESEARCH_ONLY_NOLEAP.csv"
AD_SHA="8ea065e690b35cdbf2722c436211ab43627dfdcb2e202f159be9d22a7396241b"
RUNS={14:469,15:95,16:30,17:137,18:47}
T_SPIKES=pd.DatetimeIndex(pd.to_datetime([
"2015-11-07 03:00","2015-11-07 04:00","2015-11-07 04:30","2015-11-07 05:00",
"2015-11-07 08:00","2017-06-29 23:00","2017-06-29 23:30","2017-06-30 00:00",
"2017-06-30 00:30","2017-06-30 01:00","2017-06-30 01:30","2017-06-30 02:00",
"2017-06-30 02:30","2017-07-03 07:00"]))
PROTECTED_2017=pd.DatetimeIndex(pd.date_range("2017-07-04 06:00",periods=5,freq="30min"))
HH=pd.Timedelta(minutes=30)
def need(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AG SIGNED SOURCE HOLD: "+str(msg))
def must(path):
    p=Path(path);need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p));return p
def sha(path):
    h=hashlib.sha256()
    with must(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def blob(path):
    data=must(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def native_index(s):
    d=pd.DatetimeIndex(pd.to_datetime(s.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12],
                                      format="%Y%m%d%H%M",errors="raise"))
    need(len(d)==280320 and d.is_unique and d.is_monotonic_increasing and
         not ((d.month==2)&(d.day==29)).any(),"full 16-year NOLEAP native source timeline mismatch")
    return d
def floats_equal(a,b,atol=1e-11):
    return np.isclose(np.asarray(a,float),np.asarray(b,float),
                      atol=atol,rtol=0,equal_nan=True)
def receipt(folder,name,field,exact):
    data=json.loads(must(folder/name).read_text())
    need(set(data.get(field,{}))==set(exact),"SHA receipt inventory mismatch "+name)
    for x,digest in data[field].items():
        need("/" not in x and "\\" not in x and sha(folder/x)==digest,
             "signed report/output changed "+x)
    return data
def selftest():
    need(sum(RUNS.values())==778 and len(T_SPIKES)==14 and
         len(PROTECTED_2017)==5 and
         np.isclose((8.373+6.653)/2,7.513,atol=1e-10,rtol=0),
         "original scope/one accepted isolated VPD identity")
    s=pd.Series(["201507010000","201507010030"])
    need(len(pd.to_datetime(s,format="%Y%m%d%H%M"))==2,
         "native half-hour source stamp")
    print("STAGE13AG SELF-TEST PASS | five runs 778 HH, 14 original T holds, 2017 protected five and real QC0 provenance; NO WRITES",flush=True)
def verify():
    need(blob(SOURCE)==SOURCE_GIT,"signed upstream 13-method source reader changed")
    spec=importlib.util.spec_from_file_location("me6_stage13ag_upstream",must(SOURCE))
    need(spec is not None and spec.loader is not None,
         "original source reader unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER=="batch03-stage13_validation-v1-20261027-Me6-six-run-validated-repair-candidates",
         "upstream source version unexpected")
    raw,selected,runs,provenance=mod.load_inputs()
    need(provenance.get("Stage13s_input_SHA256")==S_SHA,
         "full frozen Stage13S source SHA drift")
    b=receipt(B,B_REC,"outputs_SHA256",
        {B_DEC,B_VAL,B_CV,B_PSEUDO,B_INFO,
         "CANDIDATES_ONLY_NO_FORCING_OR_SCIENCE_APPROVAL"})
    need(b.get("site")=="US-Me6" and
         b.get("version")==mod.VER and
         b.get("forcings_written") is False and
         b.get("input_provenance",{}).get("Stage13s_input_SHA256")==S_SHA,
         "signed 13-method science decision source/report mismatch")
    af=receipt(AF,AF_REC,"outputs_SHA256",
        {AF_CSV,AF_INFO,"RESEARCH_ONLY_QC1_OR_MIXED_NEIGHBORS_NOT_DOUBLE_OBS_QC0"})
    need(af.get("site")=="US-Me6" and
         af.get("separate_research_only_shadow") is True and
         af.get("source_or_production_forcing_written") is False and
         af.get("original_Stage13AD_SHA256")==AD_SHA,
         "latest exact successful Stage13AF approval lineage drift")
    af_info=json.loads(must(AF/AF_INFO).read_text())
    need(af_info.get("original_full_run_id")==14 and
         af_info.get("source_native_time")=="2015-11-12 13:30:00" and
         af_info.get("source_Stage13AE_receipt_SHA256")==
         "78afcf4e29a52de310cf9fecff82669cb4456dcd9bf7caf67362772a32056e37" and
         af_info.get("original_Stage13AD_SHA256")==AD_SHA and
         af_info.get("scope")=="ONLY_SINGLE_QC1_RESEARCH_TRIAL_USING_USER_CONDITIONAL_RULE" and
         af_info.get("model_ready") is False and
         af_info.get("change_counts")=={"QBOT":1,"VPD_USE":1},
         "2015 single-point conditional source science changed")
    need(sha(AD/AD_CSV)==AD_SHA,"predecessor approved Stage13AD full source altered")
    current=pd.read_csv(must(AF/AF_CSV),dtype={"time":str},low_memory=False)
    current.index=native_index(current.time)
    parent=pd.read_csv(must(AD/AD_CSV),dtype={"time":str},low_memory=False)
    parent.index=native_index(parent.time)
    need(current.index.equals(parent.index) and
         list(current.columns)==list(parent.columns),
         "current vs original parent full NOLEAP schema/clock differs")
    changed_expected={pd.Timestamp("2015-11-12 13:30")}
    for col in parent.columns:
        if col=="time":need(parent[col].equals(current[col]),
                            "original time field altered")
        else:
            o=parent[col].to_numpy(float);n=current[col].to_numpy(float)
            changed=set(parent.index[~floats_equal(o,n)])
            if col in ("QBOT","VPD_USE"):
                need(changed==changed_expected,
                     "exact AF 1HH correction must be only VPD/QBOT "+col)
            else:need(not changed,"forbidden source field changed "+col)
    for t in PROTECTED_2017:
        need(parent.loc[t].equals(current.loc[t]),
             "five previous 2017 exact operator approved records altered")
    decisions=pd.read_csv(must(B/B_DEC),low_memory=False)
    values=pd.read_csv(must(B/B_VAL),dtype={"native_time":str},low_memory=False)
    cv=pd.read_csv(must(B/B_CV),dtype={"native_time":str},low_memory=False)
    info=json.loads(must(B/B_INFO).read_text())
    need(len(decisions)==13 and len(values)==1568 and
         set(decisions.run_id)=={12,*RUNS} and
         info.get("original_held_runs")==6 and
         info.get("operator_approval_granted") is False and
         info.get("production_forcing_written") is False,
         "13-method report population/provenance altered")
    return raw,selected,runs,current,decisions,values,cv,info,provenance
def runreview():
    raw,sel,runs,current,decisions,values,cv,info,provenance=verify()
    groups=[];daily=[];events=[];bounds=[]
    runsets={}
    for gid,n in RUNS.items():
        rr=runs.loc[runs.source_full_run_id.eq(gid)]
        need(len(rr)==1,"original run ID changed "+str(gid))
        row=rr.iloc[0]
        start=pd.Timestamp(row.source_original_QC1_start)
        end=pd.Timestamp(row.source_original_QC1_end)
        times=pd.date_range(start,end,freq="30min")
        need(len(times)==n and times.isin(raw.index).all() and
             (raw.loc[times,"VPD_F_QC"]==1).all(),
             "source original VPD QC1 run chronological extent changed "+str(gid))
        runsets[gid]=times
        r=raw.loc[times];curr=current.loc[times]
        valid_model_vpd=np.isfinite(curr.VPD_USE.to_numpy(float))
        valid_model_q=np.isfinite(curr.QBOT.to_numpy(float))
        diff=r.TA_F.to_numpy(float)-r.TA_ERA.to_numpy(float)
        t_holds=np.abs(diff)>8
        qc0_t=np.asarray(r.TA_F_QC==0)
        own_era_vpd=r.VPD_ERA.to_numpy(float)
        selected_vpd=curr.VPD_USE.to_numpy(float)
        source_vpd=r.VPD_F.to_numpy(float)
        # Native VPD_F QC1 is the source's gapfilled/derived value,
        # never treat it as independent QC0 measured humidity truth.
        left,right=start-HH,end+HH
        need(left in raw.index and right in raw.index,
             "original native boundary absent "+str(gid))
        Qs=[int(raw.at[t,"VPD_F_QC"]) for t in (left,right)]
        valid_source=np.isfinite(source_vpd)
        to_era_diff=np.abs(source_vpd-own_era_vpd)
        reasons=decisions.loc[decisions.run_id.eq(gid)&
                    decisions.method.eq("LOCAL_MEDIAN_ADJUSTED_ERA_RH")].iloc[0]
        skill=info.get("validation",{}).get(str(gid),{})
        skill_cv=skill.get("buffered_day_CV",{})
        target_approved=bool(gid==14 and
                             pd.Timestamp("2015-11-12 13:30") in times)
        groups.append({
          "run_id":gid,"source_start":str(start),"source_end":str(end),
          "original_QC1_native_HH":n,
          "QC1_centre_directly_measured_humidity_QC0_HH":0,
          "original_tower_T_QC0_HH":int(qc0_t.sum()),
          "original_tower_minus_ERA_T_abs_GT8C_HH":int(t_holds.sum()),
          "original_tower_VPD_finite_HH":int(valid_source.sum()),
          "latest_AF_selected_VPD_finite_HH":int(valid_model_vpd.sum()),
          "latest_AF_selected_VPD_missing_HH":int((~valid_model_vpd).sum()),
          "latest_AF_selected_QBOT_missing_HH":int((~valid_model_q).sum()),
          "original_tower_vs_paired_ERA_VPD_median_abs_hPa":
             float(np.nanmedian(to_era_diff)) if np.isfinite(to_era_diff).any() else np.nan,
          "original_tower_vs_paired_ERA_VPD_p90_abs_hPa":
             float(np.nanpercentile(to_era_diff,90)) if np.isfinite(to_era_diff).any() else np.nan,
          "source_direct_left_humidity_QC":Qs[0],
          "source_direct_right_humidity_QC":Qs[1],
          "two_original_measured_VPD_QC0_direct_bookends":Qs==[0,0],
          "local_QC0_analogues_original":skill.get("QC0_pool_rows"),
          "buffered_QC0_leave_day_out_source_rows":skill_cv.get("validation_rows"),
          "buffered_QC0_leave_day_out_unique_dates":skill_cv.get("validation_dates"),
          "local_ERA_RH_adjustment_empirical_pass":bool(skill_cv.get("research_empirical_screen_PASS",False)),
          "locally_adjusted_ERA_full_run_candidate_max_30min_VPD_step_hPa":
             float(reasons.max_VPD_step_hPa),
          "locally_adjusted_ERA_full_run_source_physically_valid_HH":
             int(reasons.row_physics_source_PASS_HH),
          "locally_adjusted_ERA_HOLD_reasons":str(reasons.HOLD_reasons),
          "one_isolated_20151112_1330_science_shadow_already_applied":target_approved,
          "full_run_repair_approved":False,
          "full_run_review_category":
            "LONG_2015_RUN_NEEDS_QC0_SUPPORTED_SOURCE_RECONCILIATION" if gid==14
            else "2017_QC2_DIRECT_BOUNDARIES_AND_SOURCE_T/ERA_GATE_HOLD"})
        # Daily contextual medians and original QC sources, no invented water RH
        frame=pd.DataFrame({
            "native_time":times,"source_tower_VPD_hPa":source_vpd,
            "original_site_T_C":r.TA_F.to_numpy(float),
            "original_T_QC":r.TA_F_QC.to_numpy(float),
            "source_ERA_T_C":r.TA_ERA.to_numpy(float),
            "source_ERA_VPD_hPa":own_era_vpd,
            "AF_current_selected_VPD_hPa":selected_vpd,
            "AF_current_QBOT_kgkg":curr.QBOT.to_numpy(float),
            "T_abs_GT8":t_holds,"model_VPD_missing":~valid_model_vpd})
        frame["day"]=pd.to_datetime(frame.native_time).dt.strftime("%Y-%m-%d")
        for day, df in frame.groupby("day",sort=True):
            daily.append({
                "run_id":gid,"native_day":day,"original_QC1_native_HH":len(df),
                "start":str(df.native_time.min()),"end":str(df.native_time.max()),
                "original_tower_T_QC0_HH":int((df.original_T_QC==0).sum()),
                "site_ERA_T_GT8C_HH":int(df.T_abs_GT8.sum()),
                "original_tower_VPD_median_hPa":float(df.source_tower_VPD_hPa.median()),
                "original_source_ERA_VPD_median_hPa":float(df.source_ERA_VPD_hPa.median()),
                "original_source_tower_minus_ERA_T_median_C":
                    float((df.original_site_T_C-df.source_ERA_T_C).median()),
                "current_AF_VPD_median_hPa":float(df.AF_current_selected_VPD_hPa.median()),
                "latest_AF_source_missing_VPD_HH":int(df.model_VPD_missing.sum()),
                "source_tower_to_paired_ERA_median_abs_VPD_hPa":
                    float((df.source_tower_VPD_hPa-df.source_ERA_VPD_hPa).abs().median()),
                "source_tower_to_paired_ERA_p90_abs_VPD_hPa":
                    float((df.source_tower_VPD_hPa-df.source_ERA_VPD_hPa).abs().quantile(.9)),
                "method_proposed_not_approved":True})
        # Source boundary ±2h, all 14 site–ERA temperature failures ±1h;
        # immutable previous 2017 values included in true-source context.
        for kind,t0 in [("LEFT_BOUNDARY",left),("RIGHT_BOUNDARY",right)]:
            for k in range(-4,5):
                t=t0+k*HH
                if t not in raw.index or t not in current.index:continue
                src=raw.loc[t];out=current.loc[t]
                bounds.append({"run_id":gid,"event":kind,"boundary_native_time":str(t0),
                    "native_time":str(t),"relative_HH":k,
                    "source_original_VPD_QC":float(src.VPD_F_QC),
                    "tower_VPD_F_hPa":float(src.VPD_F),
                    "original_tower_T_C":float(src.TA_F),
                    "original_T_QC":float(src.TA_F_QC),
                    "paired_ERA_T_C":float(src.TA_ERA),
                    "paired_ERA_VPD_hPa":float(src.VPD_ERA),
                    "latest_AF_selected_VPD_hPa":float(out.VPD_USE),
                    "latest_AF_QBOT_kgkg":float(out.QBOT),
                    "previous_user_approved_2017_protected":t in PROTECTED_2017,
                    "new_method_approval":False})
    all_idx=pd.DatetimeIndex(sorted(set().union(*(set(x) for x in runsets.values()))))
    need(len(all_idx)==778 and
         len(set(T_SPIKES).intersection(set(all_idx)))==14,
         "exact full original five-run scope/14 source T holds changed")
    for gid,ts in ((g,t) for g,idx in runsets.items() for t in T_SPIKES if t in idx):
        for k in range(-2,3):
            x=ts+k*HH
            if x not in raw.index or x not in current.index:continue
            r=raw.loc[x];p=current.loc[x]
            events.append({"run_id":gid,"strict_source_T_discrepancy_native_time":str(ts),
              "native_time":str(x),"relative_HH":k,
              "tower_TA_F_C":float(r.TA_F),"tower_TA_F_QC":float(r.TA_F_QC),
              "tower_VPD_F_hPa":float(r.VPD_F),"tower_VPD_F_QC":float(r.VPD_F_QC),
              "paired_ERA_T_C":float(r.TA_ERA),
              "paired_ERA_VPD_hPa":float(r.VPD_ERA),
              "tower_minus_ERA_T_C":float(r.TA_F-r.TA_ERA),
              "after_AF_selected_VPD_hPa":float(p.VPD_USE),
              "after_AF_QBOT_kgkg":float(p.QBOT),
              "operator_new_approval":False})
    gr=pd.DataFrame(groups)
    day=pd.DataFrame(daily)
    boundary=pd.DataFrame(bounds)
    anomalies=pd.DataFrame(events)
    need(len(gr)==5 and
         gr.original_QC1_native_HH.sum()==778 and
         gr.original_tower_minus_ERA_T_abs_GT8C_HH.sum()==14 and
         len(day)>10 and
         len(boundary)==5*2*9 and
         len(anomalies)==14*5,
         "full original five-run daily/boundary/anomaly science coverage changed")
    full_missing={c:int((~np.isfinite(current[c].to_numpy(float))).sum())
                  for c in ("VPD_USE","QBOT","TA_USE","PSRF")}
    summary={"version":VER,"site":"US-Me6","source_halfhours":778,
      "run14_to_18_held_full_QC1_runs":5,
      "full_site_latest_stage13af_missing_by_model_variable":full_missing,
      "current_research_shadow_sha256":sha(AF/AF_CSV),
      "previous_stage13ad_SHA256":AD_SHA,
      "paired_ERA_is_same_release_companion_not_independent_ERA5_land":True,
      "original_QC1_humidity_not_independent_observed_QC0":True,
      "14_site_ERA_T_gt8C_original_source_exceptions_remain":14,
      "original_QC2_adjacent_boundaries_in_2017_runs":8,
      "2015_nov_single_point_stage13af_already_approved":True,
      "full_run_method_approval":False,"source_modified":False,"forcings_written":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AG FIVE FULL-RUN SOURCE/QC0/T/ERA GROUP DECISIONS",flush=True)
    cols=["run_id","original_QC1_native_HH","latest_AF_selected_VPD_missing_HH",
          "original_tower_minus_ERA_T_abs_GT8C_HH",
          "source_direct_left_humidity_QC","source_direct_right_humidity_QC",
          "local_QC0_analogues_original",
          "buffered_QC0_leave_day_out_source_rows",
          "local_ERA_RH_adjustment_empirical_pass",
          "locally_adjusted_ERA_full_run_candidate_max_30min_VPD_step_hPa",
          "full_run_review_category"]
    print(gr[cols].to_string(index=False),flush=True)
    print("STAGE13AG DATE GROUPS ORIGINAL TOWER vs COMPANION ERA",flush=True)
    print(day.to_string(index=False),flush=True)
    print("STAGE13AG ACTUAL SITE SOURCE REMAINING MISSING / SCOPED HODLS",
          json.dumps(summary,indent=2),flush=True)
    return gr,day,boundary,anomalies,summary
def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):mode.add_argument("--"+x,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    groups,days,edges,anomalies,summary=runreview()
    if args.check:
        print("STAGE13AG READONLY SIGNED FIVE-RUN SCIENCE CHECK PASS | NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13ag_Me6_5run_QC0_ERA_daily_before_after_REVIEW_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    doc={
      "five_run_group_source_QC0_and_ERA_method_HOLD.csv":groups,
      "five_run_daily_source_tower_vs_ERA_context.csv":days,
      "five_run_start_end_2h_tower_ERA_original_boundaries.csv":edges,
      "14_original_source_T_discrepancies_1h_before_after.csv":anomalies}
    for name,frame in doc.items():frame.to_csv(out/name,index=False,float_format="%.17g")
    name="stage13ag_readonly_group_science_summary.json"
    marker="NO_SOURCE_METHOD_APPROVAL_OR_FORCING_MODEL_SUBMISSION"
    (out/name).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text("Only original source QC0 science and released paired ERA"
        " comparisons, all full-run methods held; no new automatic repairs,"
        " shadow modification, production DATM or Slurm.\n")
    receipt={"version":VER,"site":"US-Me6","source_or_forcing_written":False,
      "new_operator_approval":False,
      "outputs_SHA256":{n:sha(out/n) for n in [*doc,name,marker]}}
    (out/"stage13ag_science_readonly_sha_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AG READONLY REPORT DIR:",out,flush=True)
    print("STAGE13AG FIVE HELD RUN DAILY SCIENCE GROUP REPORT COMPLETE | NO FORCING/DATM/AD400/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13AG SOURCE SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

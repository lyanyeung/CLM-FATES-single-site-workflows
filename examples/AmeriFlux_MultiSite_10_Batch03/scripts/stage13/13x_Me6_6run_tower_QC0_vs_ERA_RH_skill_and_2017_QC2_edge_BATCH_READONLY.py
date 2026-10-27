#!/usr/bin/env python3
"""Stage13x US-Me6: measured original QC0 empirical RH skill around six HOLDs.

Check SHA-signed ACTUAL Stage13w + Stage13r/Stage13s original source
provenance; compare original tower VPD_F_QC=0 humidity with same-native
companion ERA RH at original measured tower TA_F, both local +/-48h and
+/-14d outside each original QC1 HOLD run. Compare four 2017 original
QC2 immediate edges, source QC, ERA RH and retained Stage13s selected
VPD; no remote measured QC0 is represented as an immediate anchor.

No model patches, no alteration of Stage13s 235 approved 2015 source
records or Stage12ac July04 protected 5, no UTC offset guess,
no relaxation of 8C site-ERA T / 4hPa VPD bound. All output RESEARCH
READONLY source comparison, NOT a replacement or operator approval.

--self-test standalone/no source IO
--check pinned SHA source/read-only science; no writes
--run same plus new SHA-sealed reports under reports/, NO forcing.
"""
import argparse,importlib.util,hashlib,json,subprocess,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13x-v1-20261027-Me6-QC0-ERA-RH-reliability-and-2017-QC2"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
PREV=HERE/"13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
PREV_BLOB="5a8dc69f5fb65015a9b7c9096153935684f466a8"
W=ROOT/"reports/stage13w_Me6_14_exact_physics_causes_and_2017_QC2_BOUNDARIES_READONLY_20261027T085711Z_f6efb289"
W_REC="stage13w_readonly_science_SHA_receipt.json"
W_FAIL="14_original_native_QC1_exact_ERA_RH_T_QBOT_science_failures.csv"
W_EDGES="four_2017_original_source_QC2_edges_no_immediate_QC0.csv"
W_SUMMARY="stage13w_original_source_batch_decision_support.json"
S=ROOT/"science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105"
S_REC="stage13s_Me6_operator_235HH_SHA_receipt.json"
S_CSV="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
R=ROOT/"reports/stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_20261027T004033Z_5eefea7b"
R_REC="stage13r_source_original_QC1_SHA_receipt.json"
R_GROUP="US-Me6_source_original_full_QC1_runs_grouped_OPERATOR_APPROVAL_NEEDED.csv"
IDS=(12,14,15,16,17,18)
COUNT={12:4,14:469,15:95,16:30,17:137,18:47}
FAIL_COUNTS={14:5,15:8,17:1}
HH=pd.Timedelta(minutes=30)
MAX_TDIFF=8.0
WINDOWS=(48,336)  # hours, not records
PROTECTED={pd.Timestamp("2017-07-04 06:00")+i*HH for i in range(5)}

def require(ok,what):
    if not bool(ok):raise RuntimeError("STAGE13X ORIGINAL SOURCE SCIENCE HOLD: "+str(what))

def file(p):
    p=Path(p)
    require(p.is_file() and not p.is_symlink(),"missing/symlink original source "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def es(temp):
    return 6.112*np.exp(17.67*float(temp)/(float(temp)+243.5))

def near(a,b,eps=1e-8):
    return bool(np.isfinite([float(a),float(b)]).all() and
                np.isclose(float(a),float(b),rtol=0,atol=eps))

def selftest():
    assert len(IDS)==6 and sum(COUNT.values())==782
    assert sum(FAIL_COUNTS.values())==14 and len(PROTECTED)==5
    t=10.;v=4.;rt=10.;rv=3.
    ob=100*(1-v/es(t));era=100*(1-rv/es(rt))
    assert near(es(t)*(1-era/100),3) and 0<ob<100 and 0<era<100
    k=pd.DatetimeIndex(pd.to_datetime(pd.Series(["201501010000","201701010030"]),
                        format="%Y%m%d%H%M"))
    assert k.year.tolist()==[2015,2017] and k.month.tolist()==[1,1]
    print("STAGE13X SELF-TEST PASS | six native source runs, QC0 RH truth-vs-ERA and QC2 distinction, NO WRITES",flush=True)

def predecessor():
    p=file(PREV)
    blob=subprocess.run(["git","hash-object",str(p)],
                        capture_output=True,text=True,check=True).stdout.strip()
    require(blob==PREV_BLOB,"Stage13r original source module Git blob changed")
    spec=importlib.util.spec_from_file_location("original_stage13r_science_source",p)
    require(spec is not None and spec.loader is not None,"Stage13r source cannot be loaded")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    require(m.VER=="batch03-stage13r-v1-20261027-Me6-original-full-QC1-run-survey" and
            m.ROOT==ROOT and
            m.Q==ROOT/"reports/stage13q_Me6_33_original_ERA_RH_group_source_review_20261027T002737Z_445444f6",
            "original stage13r time/site/source guard altered")
    return m

def signed():
    previous=predecessor()
    src,centers,_,_=previous.verified()
    w=json.loads(file(W/W_REC).read_text())
    expected={W_FAIL,W_EDGES,W_SUMMARY,"NO_OPERATOR_APPROVAL_NO_FORCING_OR_MODEL_JOBS"}
    require(w.get("version")=="batch03-stage13w-v1-20261027-Me6-14-physics-fail-2017-QC2-boundary"
            and w.get("site")=="US-Me6"
            and w.get("forcings_written") is False
            and w.get("operator_approved") is False and
            set(w.get("outputs_SHA256",{}))==expected,
            "Stage13w actual original read-only signed receipt mismatch")
    for name,dig in w["outputs_SHA256"].items():
        require("/" not in name and "\\" not in name and sha(W/name)==dig,
                "Stage13w original signed output SHA changed "+name)
    report=json.loads(file(W/W_SUMMARY).read_text())
    require(report.get("original_source_782_QC1_halfhours")==782 and
            report.get("original_source_14_physics_failed_HH")==14 and
            report.get("original_2017_runs_both_native_edges_QC2")==4 and
            report.get("previously_approved_Stage12ac_2017_time_rows_protected")==5 and
            report.get("other_original_QC1_neighbors_not_authorized")==761,
            "Stage13w original site source figures changed")
    s=json.loads(file(S/S_REC).read_text())
    require(s.get("version")=="batch03-stage13s-v1-20261027-Me6-12-full-2015-QC1-runs-235HH"
            and s.get("approved_original_source_halfhours")==235 and
            s.get("existing_2017_Stage12ac_five_source_values_preserved") is True
            and s.get("all_12_entire_native_2015_original_QC1_runs_science_PASS") is True
            and s.get("output_SHA256",{}).get(S_CSV)==sha(S/S_CSV),
            "previously approved Stage13s original full site research-only input drift")
    r=json.loads(file(R/R_REC).read_text())
    require(r.get("version")==previous.VER and
            r.get("source_full_original_QC1_runs")==18 and
            r.get("original_33_source_centers")==33 and
            r.get("outputs_SHA256",{}).get(R_GROUP)==sha(R/R_GROUP),
            "historical Stage13r original source group evidence differs")
    runs=pd.read_csv(file(R/R_GROUP),low_memory=False)
    failed=pd.read_csv(file(W/W_FAIL),dtype={"native_time":str},low_memory=False)
    edges=pd.read_csv(file(W/W_EDGES),low_memory=False)
    require(len(failed)==14 and failed.native_time.is_unique and len(edges)==4
            and tuple(edges.source_2017_full_run_id.astype(int))==(15,16,17,18),
            "actual Stage13w 14 failed source time or QC2 edge records differ")
    return src,runs,failed,edges

def audit():
    src,runs,failed,old_edges=signed()
    # Original tower and ERA source original site native 2015/2017 recorded
    # SHA were independently verified in Stage13r. No calendar shift.
    src_cols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    era_cols=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
    tower=pd.read_csv(file(src["primary"]),dtype={"TIMESTAMP_START":str},
                      usecols=src_cols,low_memory=False)
    era=pd.read_csv(file(src["era"]),dtype={"TIMESTAMP_START":str},
                    usecols=era_cols,low_memory=False)
    years=("2015","2017")
    tower=tower.loc[tower.TIMESTAMP_START.str[:4].isin(years)].copy()
    era=era.loc[era.TIMESTAMP_START.str[:4].isin(years)].copy()
    require(len(tower)==len(era)==2*17520 and
            tower.TIMESTAMP_START.is_unique and era.TIMESTAMP_START.is_unique and
            tower.TIMESTAMP_START.tolist()==era.TIMESTAMP_START.tolist(),
            "original two years' native tower and ERA source time identity mismatch")
    raw=tower.merge(era,on="TIMESTAMP_START",validate="one_to_one")
    raw.index=pd.DatetimeIndex(pd.to_datetime(raw.TIMESTAMP_START,
                                format="%Y%m%d%H%M",errors="raise"),
                                name="native_time")
    require(raw.index.is_unique and raw.index.is_monotonic_increasing,
            "source site years not original chronological order")
    for col in [*src_cols[1:],*era_cols[1:]]:
        raw[col]=pd.to_numeric(raw[col],errors="coerce")
        raw.loc[raw[col]<=-9990,col]=np.nan
    readsite=pd.read_csv(file(S/S_CSV),
                        dtype={"time":str},
                        usecols=["time","TA_USE","VPD_USE","QBOT","PSRF"],
                        low_memory=False)
    date_index=pd.DatetimeIndex(
        pd.to_datetime(readsite.time.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12],
                       format="%Y%m%d%H%M",errors="raise"),name="native_time")
    require(len(readsite)==280320 and date_index.is_unique and
            date_index.is_monotonic_increasing and raw.index.isin(date_index).all(),
            "successful Stage13s protected NOLEAP entire site chronology changed")
    readsite.index=date_index
    # Original measured QC0 VPD and observed QC0 TA; water RH inferred
    # from original tower VPD/TA, versus original paired native ERA RH.
    obs=[]
    for ts,site in raw.iterrows():
        TA=float(site.TA_F);v=float(site.VPD_F)
        et=float(site.TA_ERA);ev=float(site.VPD_ERA)
        if not(np.isfinite([TA,v,et,ev]).all()
            and float(site.TA_F_QC)==0 and float(site.VPD_F_QC)==0):continue
        sat=es(TA);esERA=es(et)
        RH=100*(1-v/sat);eraRH=100*(1-ev/esERA)
        if not(0<RH<100 and 0<eraRH<100):continue
        selected=float(readsite.at[ts,"VPD_USE"])
        modelT=float(readsite.at[ts,"TA_USE"])
        if not(near(modelT,TA,1e-7) and near(selected,v,1e-7)):continue
        obs.append({
            "native_time":ts,
            "original_measured_site_T_C":TA,
            "original_ERA_T_C":et,
            "abs_source_site_ERA_T_C":abs(TA-et),
            "original_measured_site_VPD_QC0_hPa":v,
            "source_measured_RH_implied_pct":RH,
            "same_native_paired_ERA_RH_pct":eraRH,
            "original_measured_minus_ERA_RH_percentage_points":RH-eraRH,
            "original_measured_minus_ERA_RH_at_tower_T_VPD_hPa":
                v-sat*(1-eraRH/100),
            "original_QC0_observed_and_preserved":True
        })
    observed=pd.DataFrame(obs)
    require(len(observed)>10 and observed.native_time.is_unique and
            observed.original_QC0_observed_and_preserved.all(),
            "No independently measurable QC0 source RH skill available")
    contexts=[]
    qc0samples=[]
    nearings=[]
    for run in IDS:
        row=runs.loc[runs.source_full_run_id.eq(run)]
        require(len(row)==1 and int(row.iloc[0].original_QC1_halfhour_count)==COUNT[run],
                "Stage13r signed original source full-run identity changed "+str(run))
        start=pd.Timestamp(row.iloc[0].source_original_QC1_start)
        end=pd.Timestamp(row.iloc[0].source_original_QC1_end)
        expected_native=pd.date_range(start,end,freq="30min")
        require(len(expected_native)==COUNT[run] and expected_native.isin(raw.index).all()
                and (raw.loc[expected_native,"VPD_F_QC"]==1).all(),
                "original site source QC1 full time window changed "+str(run))
        for whours in WINDOWS:
            window=pd.Timedelta(hours=whours)
            local=observed.loc[
                ((observed.native_time>=start-window)&(observed.native_time<start)) |
                ((observed.native_time>end)&(observed.native_time<=end+window))
            ].copy()
            strict=local.loc[local.abs_source_site_ERA_T_C<=MAX_TDIFF]
            for label,sub in (("ALL_MEASURED_QC0",local),
                              ("QC0_WITH_SOURCE_SITE_ERA_TEMP_DELTA_LE8C",strict)):
                e=sub.original_measured_minus_ERA_RH_percentage_points.to_numpy(float)
                d=sub.original_measured_minus_ERA_RH_at_tower_T_VPD_hPa.to_numpy(float)
                contexts.append({
                    "original_full_source_QC1_run_id":run,
                    "nearest_QC0_window_hours_before_and_after":whours,
                    "source_QC0_subset":label,
                    "original_tower_measured_QC0_count":len(sub),
                    "original_measured_minus_ERA_RH_median_pp":
                        float(np.median(e)) if len(e) else np.nan,
                    "original_measured_minus_ERA_RH_MAE_pp":
                        float(np.mean(abs(e))) if len(e) else np.nan,
                    "original_measured_minus_ERA_RH_abs_p90_pp":
                        float(np.percentile(abs(e),90)) if len(e) else np.nan,
                    "original_measured_minus_ERA_VPD_at_towerT_MAE_hPa":
                        float(np.mean(abs(d))) if len(d) else np.nan,
                    "original_measured_QC0_used_only_for_source_skill":True,
                    "distant_QC0_not_immediate_original_run_boundary":True
                })
                if whours==48 and label=="QC0_WITH_SOURCE_SITE_ERA_TEMP_DELTA_LE8C":
                    for _,item in sub.iterrows():
                        qc0samples.append({"full_run_id":run,
                            "native_time":str(item.native_time),
                            "source_QC0_original_measured_VPD_hPa":
                                item.original_measured_site_VPD_QC0_hPa,
                            "original_measured_minus_ERA_RH_pp":
                                item.original_measured_minus_ERA_RH_percentage_points,
                            "original_QC0_observation_not_interpolation_anchor":True})
        if run in (15,16,17,18):
            for when,offset,side in ((start-HH,-1,"PRE"),(end+HH,1,"POST")):
                original=raw.loc[when]
                require(float(original.VPD_F_QC)==2,
                        "original 2017 immediate original VPD_F_QC2 edge changed "+str(run))
                t=float(readsite.at[when,"TA_USE"])
                p=float(readsite.at[when,"PSRF"])
                et=float(original.TA_ERA)
                ev=float(original.VPD_ERA)
                sourceRH=100*(1-ev/es(et)) if np.isfinite([et,ev]).all() else np.nan
                v=es(t)*(1-sourceRH/100) if np.isfinite([t,sourceRH]).all() else np.nan
                nearings.append({
                    "original_full_QC1_run_id":run,
                    "immediate_original_source_QC2_side":side,
                    "immediate_source_native_time":str(when),
                    "original_source_VPD_F_QC":2,
                    "original_source_tower_VPD_F_hPa":float(original.VPD_F),
                    "original_source_tower_TA_F_QC":float(original.TA_F_QC),
                    "retained_Stage13s_original_VPD_USE_hPa":
                        float(readsite.at[when,"VPD_USE"]),
                    "original_paired_ERA_RH_percent":sourceRH,
                    "hypothetical_source_ERA_RH_at_stage13s_T_VPD_hPa":v,
                    "abs_old_selected_VPD_minus_hypothetical_ERA_hPa":
                        abs(float(readsite.at[when,"VPD_USE"])-v)
                        if np.isfinite(v) and np.isfinite(float(readsite.at[when,"VPD_USE"]))
                        else np.nan,
                    "remote_QC0_not_measured_direct_source_edge":True,
                    "QC2_source_neighbour_substitution_UNAPPROVED":True})
    # signed fourteen events from W are included as a separate measured vs
    # ERA T companion science scoreboard, WITHOUT relaxing 8C tolerance.
    stage14=pd.read_csv(file(W/W_FAIL),dtype={"native_time":str},low_memory=False)
    require(len(stage14)==14 and stage14.native_time.is_unique
            and np.all(stage14.abs_site_minus_ERA_T_C.to_numpy(float)>MAX_TDIFF),
            "actual Stage13w 14 exact temperature source failures changed")
    coverage=pd.DataFrame(contexts)
    edges=pd.DataFrame(nearings)
    require(len(coverage)==24 and len(edges)==8 and
            set(edges.original_full_QC1_run_id)=={15,16,17,18},
            "six-run QC0 skill and four 2017 QC2 source edge count differs")
    summary={
        "version":VER,"site":"US-Me6",
        "original_Stage13w_signed_receipt_sha256":sha(W/W_REC),
        "original_Stage13r_receipt_sha256":sha(R/R_REC),
        "unchanged_successful_Stage13s_selected_forcing_sha256":sha(S/S_CSV),
        "original_tower_source_sha256":sha(src["primary"]),
        "original_companion_ERA_source_sha256":sha(src["era"]),
        "six_remaining_full_source_QC1_runs_checked":6,
        "14_original_source_site_ERA_temperature_GT8C_HOLD_untouched":14,
        "original_QC0_observed_RH_skill_windows_hours":list(WINDOWS),
        "original_QC0_valid_site_tower_native_source_records":len(observed),
        "2017_original_immediate_VPD_QC2_edges_reviewed":8,
        "original_source_ERA_RH_not_tower_observed":True,
        "source_UTC_offset_adjustments_applied":False,
        "new_QC1_QC2_operator_repair_approvals":False,
        "Stage13s_235HH_preserved":True,"Stage12ac_2017_five_preserved":True,
        "source_or_forcing_modified":False,
        "postv5_approved":False,"DATM":False,"AD400":False,"Slurm":False
    }
    print("STAGE13X ME6 ORIGINAL TOWER QC0 VS COMPANION ERA RH SCIENCE RELIABILITY",flush=True)
    print(coverage.to_string(index=False),flush=True)
    print("STAGE13X ME6 FOUR 2017 SOURCE QC2 IMMEDIATE EDGE PAIRS",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("STAGE13X READONLY SCIENCE SUMMARY",json.dumps(summary,indent=2),flush=True)
    return coverage,edges,stage14,pd.DataFrame(qc0samples),summary

def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):a.add_argument("--"+mode,action="store_true")
    args=p.parse_args()
    print("STAGE13X ME6 MEASURED QC0-ERA RH VALIDATION | "+VER,flush=True)
    selftest()
    if args.self_test:return
    skills,edges,holds,sourceQc0,summary=audit()
    if args.check:
        print("STAGE13X READONLY CHECK PASS | 6 source runs, 14 original T>8C cases, native QC0 validation and 8 QC2 edges; NO FORCING WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13x_Me6_QC0_ERA_RH_empirical_skill_and_2017_QC2_edges_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    frames={
       "six_original_source_runs_QC0_observed_vs_ERA_RH_skill_windows.csv":skills,
       "eight_2017_original_source_QC2_immediate_edge_original_vs_ERA.csv":edges,
       "14_original_site_ERA_Tdelta_GT8C_science_HOLD_preserved.csv":holds,
       "nearby_48h_original_measured_QC0_skill_context.csv":sourceQc0
    }
    for n,df in frames.items():df.to_csv(out/n,index=False,float_format="%.17g")
    report="stage13x_six_run_source_skill_summary.json"
    marker="READONLY_QC0_CONTEXT_NOT_2017_QC2_SOURCE_APPROVAL"
    (out/report).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text(
        "All tower QC0 and ERA RH comparisons reflect source reliability only."
        " They do not authorize interpolation from remote QC0 across a 2017 QC2"
        " boundary or relaxation of source T >8C, VPD jump >4hPa. Original"
        " Stage13s 235 approved source halfhours and Stage12ac five 2017 values"
        " remain immutable; NO new forcing, Postv5, DATM or Slurm.\n")
    manifest={"version":VER,"site":"US-Me6",
        "original_Stage13w_source_receipt_SHA256":sha(W/W_REC),
        "original_Stage13s_research_forcing_SHA256":sha(S/S_CSV),
        "research_report_only":True,"operator_science_approval":False,
        "output_SHA256":{n:sha(out/n) for n in [*frames,report,marker]}}
    (out/"stage13x_original_QC0_ERA_RH_reliability_SHA_receipt.json").write_text(
       json.dumps(manifest,indent=2)+"\n")
    print("STAGE13X READONLY SOURCE-SKILL REPORT DIR:",out,flush=True)
    print("STAGE13X QC0 MEASURED RH VS ERA SOURCE SKILL AND 2017 QC2 EDGES REPORT COMPLETE; NO FORCING/MODEL",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13X SOURCE SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

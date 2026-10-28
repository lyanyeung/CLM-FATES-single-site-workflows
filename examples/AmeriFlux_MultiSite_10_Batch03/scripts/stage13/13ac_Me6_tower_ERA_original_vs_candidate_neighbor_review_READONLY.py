#!/usr/bin/env python3
"""Stage13AC: exact original tower and companion ERA before/after review.

SOURCE TRUTH: source AmeriFlux FLUXMET TA_F, VPD_F and QC; the accompanying
TA_ERA, VPD_ERA (not independently asserted to be ERA5-Land); the SHA sealed
Stage13S and the user's executed Stage13AA four-HH shadow, and actual
Stage13AB/Stage13-validation hypothetical raw and adjusted ERA candidates.

For 14 temperature discrepancies, nine DISTINCT >4hPa 30-minute edges,
and the start/end of all five still held source runs, print the original
before/after records plus ±2h native source contexts. ALL Run14-18
candidate values are PROPOSALS, not written to the approved shadow.
No source/model writes; only a new reports/ review directory.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ac-v1-20261028-Me6-14T-9unique-edges-5run-original-compare"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
SC=HERE/"13_validation_Me6_six_run_repair_candidates.py"
SC_BLOB="de62b7f6d1001fafa923163e565b2945bb2a8816"
B=ROOT/"reports/stage13_validation_Me6_six_run_repair_candidates_20261028T162002Z_4a34daf8"
A=ROOT/"reports/stage13ab_Me6_14_T_exceptions_QC2_and_4hPa_REVIEW_ONLY_20261028T163021Z_65ad5c8b"
AA=ROOT/"science_trials/stage13aa_Me6_Run12_4HH_QC0_LINEAR_APPROVED_RESEARCH_ONLY_20261028T162945Z_25df5b3a"
AA_CSV="US-Me6_STAGE13AA_Run12_4HH_APPROVED_QC0_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AA_REC="stage13aa_run12_approved_shadow_SHA_receipt.json"
AA_MAN="stage13aa_user_approved_run12_shadow_manifest.json"
A_REC="stage13ab_readonly_SHA_receipt.json"
A_FAIL="14_T_GT8C_two_method_science_review.csv"
A_EDGE="2017_candidate_30min_VPD_edges_GT4hPa_review.csv"
A_QC2="four_original_QC2_bounded_runs_no_direct_measured_QC0.csv"
B_REC="stage13_validation_candidate_SHA_receipt.json"
B_VALUES="1568_explicit_candidate_values_NOT_FORCING.csv"
B_DEC="six_runs_13_method_batch_decisions.csv"
S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
H=pd.Timedelta(minutes=30)
WINDOW=4 # ±4 halfhours (2 hours)
RUNS={14:469,15:95,16:30,17:137,18:47}
PROTECTED={pd.Timestamp("2017-07-04 06:00")+i*H for i in range(5)}
METHODS=("RAW_NATIVE_ERA_RH","LOCAL_MEDIAN_ADJUSTED_ERA_RH")
def need(t,msg):
    if not bool(t):raise RuntimeError("STAGE13AC ORIGINAL REVIEW HOLD: "+str(msg))
def must(p):
    p=Path(p); need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p));return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def blob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def receipt(folder,name,field,expected):
    doc=json.loads(must(folder/name).read_text())
    got=doc.get(field,{})
    need(set(got)==set(expected),"SHA receipt output inventory changed "+name)
    for n,d in got.items():
        need("/" not in n and "\\" not in n and sha(folder/n)==d,
             "SHA receipt file mismatch "+n)
    return doc
def native(col):
    x=col.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
    idx=pd.DatetimeIndex(pd.to_datetime(x,format="%Y%m%d%H%M",errors="raise"))
    need(idx.is_unique and idx.is_monotonic_increasing,"source time/duplicates")
    return idx
def es(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(t+243.5)) if np.isfinite(t) else np.nan
def vpd_to_rh(v,t):
    sat=es(t)
    return 100*(1-float(v)/sat) if np.isfinite([v,sat]).all() and sat>0 else np.nan
def fd(v):
    try:return float(v)
    except (TypeError,ValueError):return np.nan
def selftest():
    need(len(RUNS)==5 and sum(RUNS.values())==778 and len(PROTECTED)==5,
         "exact remaining 778 original source HH")
    d=pd.date_range("2017-07-04 07:00",periods=2,freq="30min")
    need(d[1]-d[0]==H and len(pd.date_range(d[0]-4*H,d[-1]+4*H,freq="30min"))==10,
         "native context endpoints")
    need(np.isclose(vpd_to_rh(5,10),100*(1-5/es(10))) and np.isnan(vpd_to_rh(np.nan,10)),
         "tower RH only derived from finite tower QC eligible inputs")
    print("STAGE13AC SELF-TEST PASS | 14 source T exceptions, nine edges, 5 runs; NO WRITES",flush=True)
def verified():
    need(blob(SC)==SC_BLOB,"pinned Stage13 validation code blob changed")
    spec=importlib.util.spec_from_file_location("me6_13validation_readonly_for_13ac",must(SC))
    need(spec is not None and spec.loader is not None,"source-provenance reader unavailable")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER=="batch03-stage13_validation-v1-20261027-Me6-six-run-validated-repair-candidates",
         "original 13-method provenance code not identical")
    # Original tower and companion ERA read from exact SHA-pinned original
    # source independently through Stage13r -> Stage13x -> 13validation.
    raw,before,runs,prov=mod.load_inputs()
    need(prov.get("Stage13s_input_SHA256")==S_SHA,
         "original 235HH Stage13S chosen source changed")
    b=receipt(B,B_REC,"outputs_SHA256",[
        B_VALUES,B_DEC,"buffered_leave_day_out_QC0_validation.csv",
        "nonoverlapping_four_HH_QC0_pseudogap_validation.csv",
        "stage13_validation_repair_candidate_summary.json",
        "CANDIDATES_ONLY_NO_FORCING_OR_SCIENCE_APPROVAL"])
    need(b.get("site")=="US-Me6" and b.get("forcings_written") is False
         and b.get("input_provenance",{}).get("Stage13s_input_SHA256")==S_SHA,
         "13-method candidate source SHA or research-only status changed")
    a=receipt(A,A_REC,"output_SHA256",[
        A_FAIL,A_EDGE,A_QC2,"stage13ab_manual_source_review_summary.json",
        "NO_SOURCE_METHOD_APPROVAL_NO_FORCING_OR_JOBS"])
    need(a.get("site")=="US-Me6" and a.get("forcings_written") is False
         and a.get("operator_new_approval") is False,
         "review table should not grant methods")
    aa=receipt(AA,AA_REC,"outputs_SHA256",[
        AA_CSV,"four_original_QC1_operator_approved_QC0_linear_VPD_QBOT.csv",
        AA_MAN,"RESEARCH_ONLY_NO_POSTV5_DATM_AD400_SLURM"])
    manifest=json.loads(must(AA/AA_MAN).read_text())
    need(aa.get("site")=="US-Me6" and aa.get("original_Stage13S_SHA256")==S_SHA
         and aa.get("operator_approved_4HH") is True
         and aa.get("postv5") is False and aa.get("DATM") is False
         and manifest.get("immutable_prior_Stage13S_forcing_SHA256")==S_SHA
         and manifest.get("other_unapproved_original_runs_still_HOLD")==[14,15,16,17,18],
         "exact approved Run12 shadow source status drift")
    after=pd.read_csv(must(AA/AA_CSV),dtype={"time":str},
                      usecols=["time","TA_USE","PSRF","VPD_USE","QBOT"],low_memory=False)
    after.index=native(after.time)
    need(len(after)==len(before)==280320
         and after.index.equals(before.index),
         "stage13AA shadow native noleap chronology differs")
    for c in ("TA_USE","PSRF"):
        need(np.allclose(after[c],before[c],equal_nan=True,atol=1e-12,rtol=0),
             "original tower temperature or pressure altered "+c)
    for c in ("VPD_USE","QBOT"):
        mask=~np.isclose(after[c],before[c],equal_nan=True,atol=1e-12,rtol=0)
        changed=set(after.index[mask])
        approved=set(pd.date_range("2015-09-26 05:00",periods=4,freq="30min"))
        need(changed==approved,"new research shadow contains unauthorized times "+c)
    values=pd.read_csv(must(B/B_VALUES),dtype={"native_time":str},low_memory=False)
    values["native_time"]=pd.to_datetime(values.native_time,errors="raise")
    events=pd.read_csv(must(A/A_FAIL),dtype={"native_time":str},low_memory=False)
    steps=pd.read_csv(must(A/A_EDGE),low_memory=False)
    qc2=pd.read_csv(must(A/A_QC2),low_memory=False)
    need(len(events)==28 and len(steps)==18 and len(qc2)==4,
         "14 anomaly x2 methods, 18 edge x2 methods, four source QC2 runs drift")
    errs=events.loc[events.method.eq(METHODS[1])].copy()
    need(len(errs)==14 and errs.native_time.nunique()==14
         and errs.groupby("run_id").size().to_dict()=={14:5,15:8,17:1},
         "unique original source temperature anomaly identities changed")
    pairs=steps[["run_id","from_native_time","to_native_time"]].drop_duplicates()
    need(len(pairs)==9,"actual 9 distinct VPD >4hPa candidate edges changed")
    need(len(values)==1568 and values.run_id.isin([12,*RUNS]).all(),
         "actual 1568 candidate comparison rows drift")
    return raw,before,after,runs,values,errs,steps,qc2,prov

def review():
    raw,before,after,runs,values,errs,steps,qc2,prov=verified()
    candidates=values.set_index(["method","native_time"],drop=False)
    # Most reviewers need exactly one row per native time with BOTH methods
    # aligned side by side, so we pivot by source run before merging.
    wide=values.loc[values.run_id.isin(RUNS) & values.method.isin(METHODS)]\
        .pivot(index="native_time",columns="method",
               values=["candidate_VPD_hPa","candidate_QBOT_kgkg",
                       "candidate_RH_percent","row_source_physics_PASS"])
    wide.columns=[f"{item}__{method}" for item,method in wide.columns]
    wide.index=pd.DatetimeIndex(wide.index)
    startends=[]
    for gid,n in RUNS.items():
        z=runs.loc[runs.source_full_run_id.eq(gid)]
        need(len(z)==1 and int(z.iloc[0].original_QC1_halfhour_count)==n,
             "original full QC1 run does not match expected "+str(gid))
        first=pd.Timestamp(z.iloc[0].source_original_QC1_start)
        last=pd.Timestamp(z.iloc[0].source_original_QC1_end)
        startends.extend([dict(run_id=gid,kind="RUN_START",stamp=first),
                          dict(run_id=gid,kind="RUN_END",stamp=last)])
    # Uniquely keyed event contexts, not separate duplicated reviews for
    # consecutive T outliers and two-method descriptions of the same edge.
    failtimes=[pd.Timestamp(x) for x in errs.native_time]
    pairs=steps[["run_id","from_native_time","to_native_time"]].drop_duplicates()
    edgetimes=[]
    for e in pairs.itertuples(index=False):
        edgetimes += [pd.Timestamp(e.from_native_time),pd.Timestamp(e.to_native_time)]
    runendtimes=[r["stamp"] for r in startends]
    def neighborhood(centers):
        out=set()
        for t in centers:
            for k in range(-WINDOW,WINDOW+1):out.add(t+k*H)
        return sorted(out)
    def source_table(stamps):
        rows=[]
        for t in stamps:
            need(t in raw.index and t in before.index and t in after.index,
                 "required original native neighboring time not found "+str(t))
            src=raw.loc[t]
            old=before.loc[t];new=after.loc[t]
            tq=fd(src.TA_F_QC);vq=fd(src.VPD_F_QC)
            t_tower=fd(src.TA_F);v_tower=fd(src.VPD_F)
            t_era=fd(src.TA_ERA);v_era=fd(src.VPD_ERA)
            rh_tower=vpd_to_rh(v_tower,t_tower) if tq==0 and vq==0 else np.nan
            rec={"native_time":str(t),
                "tower_TA_F_C":t_tower,"tower_TA_F_QC":tq,
                "tower_VPD_F_hPa_source":v_tower,"tower_VPD_F_QC":vq,
                "tower_RH_pct_ONLY_IF_TA_VPD_BOTH_QC0":rh_tower,
                "paired_ERA_TA_ERA_C":t_era,"paired_ERA_VPD_ERA_hPa":v_era,
                "paired_ERA_RH_pct_derived_from_T_ERA_VPD_ERA":vpd_to_rh(v_era,t_era),
                "tower_minus_ERA_T_C":t_tower-t_era if np.isfinite([t_tower,t_era]).all() else np.nan,
                "before_Stage13S_TA_USE_C":fd(old.TA_USE),
                "before_Stage13S_PSRF_Pa":fd(old.PSRF),
                "before_Stage13S_VPD_USE_hPa":fd(old.VPD_USE),
                "before_Stage13S_QBOT_kgkg":fd(old.QBOT),
                "after_APPROVED_Stage13AA_VPD_USE_hPa":fd(new.VPD_USE),
                "after_APPROVED_Stage13AA_QBOT_kgkg":fd(new.QBOT),
                "previously_protected_2017_five":t in PROTECTED,
                "other_Run14_18_candidate_NOT_APPLIED":True}
            for method,label in [("RAW_NATIVE_ERA_RH","rawERA"),
                                 ("LOCAL_MEDIAN_ADJUSTED_ERA_RH","adjERA")]:
                for srcname,dest in [
                     ("candidate_VPD_hPa","VPD_hPa"),
                     ("candidate_QBOT_kgkg","QBOT_kgkg"),
                     ("candidate_RH_percent","RH_pct"),
                     ("row_source_physics_PASS","source_physics_PASS")]:
                    col=f"{srcname}__{method}"
                    rec[f"hypothetical_{label}_{dest}"]= (
                        wide.at[t,col] if t in wide.index else np.nan)
            rows.append(rec)
        return pd.DataFrame(rows)
    problem_context=source_table(neighborhood(failtimes))
    edge_context=source_table(neighborhood(edgetimes))
    boundary_context=source_table(neighborhood(runendtimes))
    centers=source_table(sorted(set(failtimes)))
    need(len(centers)==14 and (centers.tower_minus_ERA_T_C.abs()>8).all(),
         "exact 14 original source tower ERA T discrepancy invariant")
    # One logical edge + both methods, displayed with true source
    # before-after tower, ERA and previous-selected values at BOTH ends.
    edge_print=[]
    for p in pairs.itertuples(index=False):
        gid=int(p.run_id);a=pd.Timestamp(p.from_native_time);b=pd.Timestamp(p.to_native_time)
        need(b-a==H,"native 30-minute candidate jump time alignment")
        aa=source_table([a,b])
        for method in METHODS:
            r=steps.loc[steps.run_id.eq(gid)&steps.method.eq(method)
                &steps.from_native_time.eq(str(a))&steps.to_native_time.eq(str(b))]
            need(len(r)==1,"each method/native edge must be unique")
            z=r.iloc[0]
            col=("hypothetical_rawERA_VPD_hPa" if method==METHODS[0]
                 else "hypothetical_adjERA_VPD_hPa")
            # Method value outside its original source QC1 interval is
            # unchanged research shadow, not a hypothetical proposal.
            vv=[fd(aa.iloc[k][col]) for k in (0,1)]
            for j in (0,1):
                if not np.isfinite(vv[j]):vv[j]=fd(aa.iloc[j].after_APPROVED_Stage13AA_VPD_USE_hPa)
            calc=abs(vv[1]-vv[0])
            need(np.isfinite(calc) and np.isclose(calc,fd(z.VPD_step_hPa),atol=1e-6,rtol=0),
                 "candidate edge reconstruction must reproduce signed prior edge "+str((gid,a,b,method)))
            edge_print.append({
                "run":gid,"candidate_method":method,
                "from_native":str(a),"to_native":str(b),
                "from_tower_TA_F_C":fd(aa.iloc[0].tower_TA_F_C),
                "to_tower_TA_F_C":fd(aa.iloc[1].tower_TA_F_C),
                "from_tower_VPD_F_QC":fd(aa.iloc[0].tower_VPD_F_QC),
                "to_tower_VPD_F_QC":fd(aa.iloc[1].tower_VPD_F_QC),
                "from_tower_VPD_F_source":fd(aa.iloc[0].tower_VPD_F_hPa_source),
                "to_tower_VPD_F_source":fd(aa.iloc[1].tower_VPD_F_hPa_source),
                "from_paired_ERA_T_C":fd(aa.iloc[0].paired_ERA_TA_ERA_C),
                "to_paired_ERA_T_C":fd(aa.iloc[1].paired_ERA_TA_ERA_C),
                "from_paired_ERA_VPD_hPa":fd(aa.iloc[0].paired_ERA_VPD_ERA_hPa),
                "to_paired_ERA_VPD_hPa":fd(aa.iloc[1].paired_ERA_VPD_ERA_hPa),
                "from_selected_before_hPa":fd(aa.iloc[0].after_APPROVED_Stage13AA_VPD_USE_hPa),
                "to_selected_before_hPa":fd(aa.iloc[1].after_APPROVED_Stage13AA_VPD_USE_hPa),
                "from_unapproved_candidate_hPa":vv[0],
                "to_unapproved_candidate_hPa":vv[1],
                "candidate_jump_hPa":calc,
                "source_edge_classification":str(z.source_boundary_class),
                "new_humidity_method_approved":False})
    edge_details=pd.DataFrame(edge_print)
    need(len(edge_details)==18 and edge_details.candidate_jump_hPa.gt(4).all(),
         "exact 9 native edge x2 candidate methods")
    summary={"version":VER,"site":"US-Me6",
         "independent_source_provenance":prov,
         "Stage13S_original_235HH_SHA256":S_SHA,
         "Stage13AA_approved_4HH_shadow_SHA256":sha(AA/AA_CSV),
         "Stage13AB_actual_review_receipt_SHA256":sha(A/A_REC),
         "Stage13Validation_actual_candidate_receipt_SHA256":sha(B/B_REC),
         "exact_14_site_ERA_T_gt8C_HH":len(centers),
         "unique_30min_jump_edges":9,
         "candidate_edge_method_pairs":18,
         "five_held_run_boundaries":10,
         "source_context_interval_minutes":30,
         "context_each_side_HH":WINDOW,
         "candidate_data_not_applied_to_Run14_18":True,
         "paired_TA_ERA_VPD_ERA_origin":"AmeriFlux source companion ERA; not independently reverified as a separate ERA5-Land download",
         "tower_VPD_QC1_not_accepted_as_measured_QC0":True,
         "source_modified":False,"shadow_modified":False,
         "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AC EXACT 14 T DISCREPANCIES | TOWER, PAIRED ERA, OLD SELECTED, HYPOTHETICAL",flush=True)
    cols=["native_time","tower_TA_F_C","tower_TA_F_QC",
          "tower_VPD_F_hPa_source","tower_VPD_F_QC",
          "paired_ERA_TA_ERA_C","paired_ERA_VPD_ERA_hPa",
          "paired_ERA_RH_pct_derived_from_T_ERA_VPD_ERA",
          "before_Stage13S_VPD_USE_hPa","after_APPROVED_Stage13AA_VPD_USE_hPa",
          "hypothetical_rawERA_VPD_hPa","hypothetical_adjERA_VPD_hPa"]
    print(centers[cols].to_string(index=False),flush=True)
    print("STAGE13AC EXACT NINE UNIQUE >4hPa 30MIN EDGES | BOTH METHODS AND ORIGINAL ENDPOINTS",flush=True)
    print(edge_details.to_string(index=False),flush=True)
    print("STAGE13AC FIVE HELD RUN START/END ±2H SOURCE PREV/NEXT QC CONTEXT",flush=True)
    print(boundary_context[[
        "native_time","tower_TA_F_C","tower_VPD_F_hPa_source","tower_VPD_F_QC",
        "paired_ERA_TA_ERA_C","paired_ERA_VPD_ERA_hPa",
        "after_APPROVED_Stage13AA_VPD_USE_hPa",
        "hypothetical_rawERA_VPD_hPa","hypothetical_adjERA_VPD_hPa"
        ]].to_string(index=False),flush=True)
    print("STAGE13AC SUMMARY",json.dumps(summary,indent=2),flush=True)
    return centers,problem_context,edge_details,edge_context,boundary_context,summary

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","run"):mode.add_argument("--"+m,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    center,problem,edges,context,boundary,report=review()
    if args.check:
        print("STAGE13AC READONLY CHECK PASS | tower+paired ERA exact source and ±2h contexts; no writes",flush=True)
        return
    out=ROOT/"reports"/("stage13ac_Me6_original_tower_ERA_prepost_14T_9edges_5runs_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={
        "14_exact_source_T_abnormal_original_tower_ERA_and_both_candidates.csv":center,
        "14_T_abnormal_2h_before_after_tower_ERA_original_candidate.csv":problem,
        "9_unique_30min_VPD_jump_edges_original_vs_two_candidates.csv":edges,
        "9_unique_jump_edges_2h_before_after_tower_ERA_original_candidate.csv":context,
        "5_held_runs_start_end_2h_before_after_QC2_tower_ERA.csv":boundary}
    for name,df in files.items():df.to_csv(out/name,index=False,float_format="%.17g")
    inf="stage13ac_science_review_summary.json"
    marker="READONLY_NO_REPAIR_APPROVAL_OR_FORCING"
    (out/inf).write_text(json.dumps(report,indent=2)+"\n")
    (out/marker).write_text("This is source review only; 'after' is the already "
       "approved Run12 research shadow. All Run14-18 ERA candidates are hypothetical "
       "and have NOT been applied. Paired ERA fields are source companion, not a "
       "separately validated independent ERA5-Land download. NO model jobs.\n")
    rece={"version":VER,"site":"US-Me6","source_or_forcing_written":False,
          "new_science_approval":False,
          "outputs_SHA256":{n:sha(out/n) for n in [*files,inf,marker]}}
    (out/"stage13ac_readonly_SHA_receipt.json").write_text(json.dumps(rece,indent=2)+"\n")
    print("STAGE13AC READONLY REPORT DIR:",out,flush=True)
    print("STAGE13AC TOWER ERA ORIGINAL/HYPOTHETICAL COMPARISON COMPLETE | NO FORCING/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AC SOURCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

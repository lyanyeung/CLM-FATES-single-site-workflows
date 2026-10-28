#!/usr/bin/env python3
"""Stage13AB: extract actual US-Me6 Run14-18 manual-review rows, READONLY.

From SHA-sealed actual 13-method validation, Stage13W 14 source T exceptions,
and Stage13S original forcing; produce compact per-event/edge review tables.
No method approval, no forcing, no Post-v5, no Slurm.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ab-v1-20261028-Me6-14T-QC2-4hPa-review"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
B=ROOT/"reports/stage13_validation_Me6_six_run_repair_candidates_20261028T162002Z_4a34daf8"
W=ROOT/"reports/stage13w_Me6_14_exact_physics_causes_and_2017_QC2_BOUNDARIES_READONLY_20261027T085711Z_f6efb289"
S=ROOT/"science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105"
SFILE="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
WREC="stage13w_readonly_science_SHA_receipt.json"
W_SHA="d0774c5d56df3dc8e640f26c1a8901c724f9b9e97b874d8f23fec9271f3f4023"
WFAIL="14_original_native_QC1_exact_ERA_RH_T_QBOT_science_failures.csv"
WEDGES="four_2017_original_source_QC2_edges_no_immediate_QC0.csv"
BREC="stage13_validation_candidate_SHA_receipt.json"
DEC="six_runs_13_method_batch_decisions.csv"
VAL="1568_explicit_candidate_values_NOT_FORCING.csv"
BIN="stage13_validation_repair_candidate_summary.json"
EXPECTED={12:4,14:469,15:95,16:30,17:137,18:47}
FAILED={14:5,15:8,17:1}
PROTECTED={pd.Timestamp("2017-07-04 06:00")+i*pd.Timedelta(minutes=30) for i in range(5)}
HH=pd.Timedelta(minutes=30)
PREF=("LOCAL_MEDIAN_ADJUSTED_ERA_RH","RAW_NATIVE_ERA_RH")

def need(b,msg):
    if not bool(b):raise RuntimeError("STAGE13AB REVIEW SOURCE HOLD: "+str(msg))
def file(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"signed report absent/symlink "+str(p));return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def bools(s):
    z=s.astype(str).str.strip().str.lower()
    need(z.isin(("true","false")).all(),"invalid historical source bool")
    return z.eq("true").to_numpy()

def selftest():
    need(sum(EXPECTED.values())==782 and sum(FAILED.values())==14
         and len(PROTECTED)==5,"original historical source counts")
    x=pd.Timestamp("2017-06-30 00:30")
    need(x-HH==pd.Timestamp("2017-06-30 00:00"),"native halfhour time")
    print("STAGE13AB SELF-TEST PASS | source 14 exceptions, 2017 QC2 and boundary 4hPa, NO WRITES",flush=True)

def audit():
    need(sha(S/SFILE)==S_SHA,"prior user-approved Stage13S 235HH changed")
    need(sha(W/WREC)==W_SHA,"Stage13W actual 14 source-T mechanism receipt changed")
    wr=json.loads(file(W/WREC).read_text())
    need(wr.get("site")=="US-Me6" and wr.get("forcings_written") is False
         and wr.get("operator_approved") is False,"Stage13W must remain readonly")
    for n,d in wr.get("outputs_SHA256",{}).items():
        need("/" not in n and "\\" not in n and sha(W/n)==d,
             "Stage13W original signed source output changed: "+n)
    br=json.loads(file(B/BREC).read_text())
    need(br.get("version")=="batch03-stage13_validation-v1-20261027-Me6-six-run-validated-repair-candidates"
         and br.get("site")=="US-Me6" and br.get("forcings_written") is False
         and br.get("input_provenance",{}).get("Stage13s_input_SHA256")==S_SHA
         and br.get("input_provenance",{}).get("Stage13w_receipt_SHA256")==W_SHA,
         "actual six-run read-only candidate report source/provenance missing")
    expected={DEC,VAL,"buffered_leave_day_out_QC0_validation.csv",
              "nonoverlapping_four_HH_QC0_pseudogap_validation.csv",
              BIN,"CANDIDATES_ONLY_NO_FORCING_OR_SCIENCE_APPROVAL"}
    need(set(br.get("outputs_SHA256",{}))==expected,
         "candidate source report signed outputs inventory changed")
    for n,d in br["outputs_SHA256"].items():
        need("/" not in n and "\\" not in n and sha(B/n)==d,
             "candidate source report SHA mismatch "+n)
    decisions=pd.read_csv(file(B/DEC),low_memory=False)
    values=pd.read_csv(file(B/VAL),dtype={"native_time":str},low_memory=False)
    fail=pd.read_csv(file(W/WFAIL),dtype={"native_time":str},low_memory=False)
    edges=pd.read_csv(file(W/WEDGES),low_memory=False)
    need(len(decisions)==13 and len(values)==1568 and len(fail)==14
         and len(edges)==4 and values.run_id.isin(EXPECTED).all(),
         "actual candidate scientific review row count unexpected")
    need(fail.native_time.is_unique
         and fail.groupby("source_original_full_run_id").size().to_dict()==FAILED
         and set(edges.source_2017_full_run_id.astype(int))=={15,16,17,18},
         "original strict source 14 / four 2017 QC2 identities changed")
    need((fail.abs_site_minus_ERA_T_C.to_numpy(float)>8).all(),
         "exact signed 14 source temperature differences no longer >8C")
    need((decisions.batch_decision.eq("CANDIDATE_FOR_GROUPED_REVIEW").sum()==1)
         and decisions.loc[decisions.batch_decision.eq("CANDIDATE_FOR_GROUPED_REVIEW"),"run_id"].tolist()==[12],
         "actual source method approvals changed from only Run12 review candidate")
    # Exactly one native time per source method. Never count 1568 as new records.
    need(values.groupby(["run_id","method"]).size().sum()==1568,
         "method candidate counts differ")
    for (run,method),sub in values.groupby(["run_id","method"]):
        need(len(sub)==EXPECTED[int(run)] and sub.native_time.is_unique
             and pd.DatetimeIndex(pd.to_datetime(sub.native_time)).is_monotonic_increasing,
             "original distinct native source timestamps drift "+str((run,method)))
    # 14 independent source-T discrepancies with both candidate numerical estimates.
    problems=[]
    for p in fail.itertuples(index=False):
        gid=int(p.source_original_full_run_id)
        for method in PREF:
            r=values.loc[values.run_id.eq(gid)&values.method.eq(method)
                         &values.native_time.eq(str(p.native_time))]
            need(len(r)==1,"candidate missing exact original 14 T exception "+str(p.native_time))
            v=r.iloc[0]
            problems.append({
                "review_priority":"P0_SOURCE_SITE_ERA_T_GT8C",
                "run_id":gid,"native_time":str(p.native_time),"method":method,
                "retained_site_T_C":float(p.retained_site_T_C),
                "paired_ERA_T_C":float(p.original_ERA_T_C),
                "abs_site_minus_ERA_T_C":float(p.abs_site_minus_ERA_T_C),
                "source_ERA_RH_pct":float(p.reconstructed_ERA_RH_percent),
                "retained_VPD_hPa":float(v.before_VPD_hPa),
                "candidate_VPD_hPa":float(v.candidate_VPD_hPa),
                "candidate_QBOT_kgkg":float(v.candidate_QBOT_kgkg),
                "candidate_RH_pct":float(v.candidate_RH_percent),
                "native_left_VPD_step_hPa":float(v.native_left_VPD_step_hPa),
                "native_right_VPD_step_hPa":float(v.native_right_VPD_step_hPa),
                "source_row_physics_pass":bool(str(v.row_source_physics_PASS).lower()=="true"),
                "reason":str(p.exact_physics_HOLD_causes),
                "user_method_approval":False
            })
    issues=pd.DataFrame(problems)
    need(len(issues)==28 and not issues.source_row_physics_pass.any(),
         "14 exact original source strict failures must remain blocked")
    # Each >4hPa source-candidate discontinuity: compare both external edges
    # and internal native edges; de-duplicate 30min connections.
    step_records=[]
    for (gid,method),data in values.groupby(["run_id","method"],sort=True):
        if int(gid)==12:continue
        data=data.sort_values("native_time")
        for r in data.itertuples(index=False):
            t=pd.Timestamp(str(r.native_time))
            for side,edge_ts,amount in (
                ("LEFT",t-HH,float(r.native_left_VPD_step_hPa)),
                ("RIGHT",t+HH,float(r.native_right_VPD_step_hPa))):
                if not(np.isfinite(amount) and amount>4):continue
                first=min(t,edge_ts);last=max(t,edge_ts)
                start=pd.Timestamp(str(data.iloc[0].native_time))
                end=pd.Timestamp(str(data.iloc[-1].native_time))
                outer=first<start or last>end
                step_records.append({"run_id":int(gid),"method":str(method),
                     "from_native_time":str(first),"to_native_time":str(last),
                     "VPD_step_hPa":amount,
                     "source_boundary_class":"SOURCE_QC2_EDGE_2017" if outer and int(gid) in (15,16,17,18)
                         else "INTERNAL_OR_PROTECTED_SOURCE_EDGE",
                     "candidate_30min_step_gt4hPa":True,"scientific_HOLD":True})
    step=pd.DataFrame(step_records)
    if len(step):
        step=step.sort_values(["run_id","method","from_native_time","to_native_time"])
        # Duplicates are the two descriptions of the same native edge.
        check=step.groupby(["run_id","method","from_native_time","to_native_time"]).VPD_step_hPa
        need((check.max()-check.min()<=1e-6).all(),
             "same 30min edge differs between left/right candidate sides")
        step=step.drop_duplicates(["run_id","method","from_native_time","to_native_time"])
    need(len(step)>0,"candidate six-run report unexpectedly lacks flagged >4hPa edges")
    need(set(step.run_id.astype(int)).issubset({15,16,17,18}),
         "Run14 unexpectedly had a >4hPa edge despite actual table max <4")
    boundary=edges.copy()
    boundary["new_operator_approval"]=False
    summary={
        "version":VER,"site":"US-Me6",
        "original_Stage13S_forcing_SHA256":S_SHA,
        "actual_stage13_validation_receipt_SHA256":sha(B/BREC),
        "actual_stage13w_source_receipt_SHA256":W_SHA,
        "method_comparisons":13,"candidate_value_rows_not_distinct_fixes":1568,
        "remaining_run_ids":[14,15,16,17,18],
        "exact_strict_source_T_gt8C_unique_HH":14,
        "two_ERA_methods_per_failed_HH":len(issues),
        "2017_original_QC2_source_runs":4,
        "2017_source_direct_QC2_edges":8,
        "candidate_30min_VPD_gt4hPa_distinct_method_edges":len(step),
        "only_approved_science_method":"Run12 four native 2015-09-26 HH QC0 linear",
        "other_repair_method_approval":False,
        "source_forcing_modified":False,"Postv5":False,"DATM":False,
        "AD400":False,"Slurm":False
    }
    print("STAGE13AB 14 ORIGINAL SCIENTIFIC-TEMPERATURE EXCEPTIONS (ONE ROW EACH)",flush=True)
    print(issues.loc[issues.method.eq(PREF[0]),
        ["run_id","native_time","retained_site_T_C","paired_ERA_T_C",
         "abs_site_minus_ERA_T_C","candidate_VPD_hPa","reason"]].to_string(index=False),flush=True)
    print("STAGE13AB CANDIDATE >4hPa 30MIN EDGE REVIEW",flush=True)
    print(step.to_string(index=False),flush=True)
    print("STAGE13AB ORIGINAL 2017 QC2 BOUNDARIES",flush=True)
    print(boundary.to_string(index=False),flush=True)
    print("STAGE13AB MANUAL REVIEW SUMMARY",json.dumps(summary,indent=2),flush=True)
    return issues,step,boundary,summary

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):mode.add_argument("--"+name,action="store_true")
    a=p.parse_args()
    selftest()
    if a.self_test:return
    issues,step,edges,summary=audit()
    if a.check:
        print("STAGE13AB READONLY CHECK PASS | 14 exact T holds, QC2 source edges, >4hPa candidates; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13ab_Me6_14_T_exceptions_QC2_and_4hPa_REVIEW_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={"14_T_GT8C_two_method_science_review.csv":issues,
          "2017_candidate_30min_VPD_edges_GT4hPa_review.csv":step,
          "four_original_QC2_bounded_runs_no_direct_measured_QC0.csv":edges}
    for name,df in docs.items():df.to_csv(out/name,index=False,float_format="%.17g")
    info="stage13ab_manual_source_review_summary.json"
    marker="NO_SOURCE_METHOD_APPROVAL_NO_FORCING_OR_JOBS"
    (out/info).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text("Signed original source and candidate comparisons only. "
        "No unapproved humidity source, QC2 boundary, production forcing or model jobs altered.\n")
    receipt={"version":VER,"site":"US-Me6","forcings_written":False,
             "operator_new_approval":False,"output_SHA256":{
                name:sha(out/name) for name in [*docs,info,marker]}}
    (out/"stage13ab_readonly_SHA_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AB READONLY REPORT DIR:",out,flush=True)
    print("STAGE13AB MANUAL REVIEW REPORT COMPLETE; NO FORCING/DATM/AD400/SLURM",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13AB SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

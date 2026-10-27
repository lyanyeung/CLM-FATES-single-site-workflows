#!/usr/bin/env python3
"""Batch03 Me6 Stage13v: signed Stage13u 14 failures + valid group review.
Strictly diagnostic, never authority to fix original QC1, QC2 or forcing.
--self-test no sources; --check read-only; --run SHA-signed REPORT only.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VER="batch03-stage13v-v1-Me6-14-exact-original-science-failures"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
U=ROOT/"reports/stage13u_Me6_six_held_source_QC1_runs_BATCH_SCIENCE_ONLY_20261027T074748Z_9e23952f"
REC="stage13u_six_held_source_runs_SHA_receipt.json"
DETAIL="782_original_native_QC1_records_tower_ERA_PSRF_RH_QBOT_review.csv"
GROUP="six_held_original_source_QC1_runs_GROUPED_review.csv"
SUMMARY="stage13u_Me6_six_runs_grouped_approval_decision_evidence.json"
IDS=(12,14,15,16,17,18)
N={12:4,14:469,15:95,16:30,17:137,18:47}
FAIL={12:0,14:5,15:8,16:0,17:1,18:0}
HH=pd.Timedelta(minutes=30)
PROTECT={pd.Timestamp("2017-07-04 06:00")+i*HH for i in range(5)}

def guard(ok,why):
    if not bool(ok): raise RuntimeError("STAGE13V SCIENCE HOLD: "+str(why))

def file(p):
    p=Path(p)
    guard(p.is_file() and not p.is_symlink(),"source missing/symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()

def flag(col):
    x=col.astype(str).str.strip().str.lower()
    guard(x.isin(("true","false")).all(),"unexpected source signed boolean")
    return x.eq("true").to_numpy()

def chunk(times,ok):
    chunks=[];active=[]
    for t,yes in zip(times,ok):
        if yes:
            if active and t-active[-1]!=HH: chunks.append(active);active=[]
            active.append(t)
        elif active: chunks.append(active);active=[]
    if active:chunks.append(active)
    return chunks

def test():
    t=pd.date_range("2015-01-01",periods=5,freq="30min")
    guard([len(x) for x in chunk(t,[True,True,False,True,True])]==[2,2],
          "source native group split")
    guard(flag(pd.Series(["True","FALSE"])).tolist()==[True,False],"CSV bool")
    guard(sum(N.values())==782 and sum(FAIL.values())==14 and len(PROTECT)==5,
          "source original six runs")
    print("STAGE13V SELF-TEST PASS | 6 runs, 14 source failures, no writes",flush=True)

def audit():
    rec=json.loads(file(U/REC).read_text())
    guard(rec.get("version")=="batch03-stage13u-v1-20261027-Me6-six-original-QC1-held-runs-batch-triage"
          and rec.get("site")=="US-Me6"
          and rec.get("entire_six_held_source_runs_audited")==6
          and rec.get("unapproved_source_neighbors_still_unapproved")==761
          and rec.get("forcings_generated") is False,
          "actual original Stage13u receipt not verified")
    dig=rec.get("outputs_SHA256",{})
    guard(set(dig)=={DETAIL,GROUP,SUMMARY,
          "SOURCE_EVIDENCE_ONLY_NO_OPERATOR_APPROVAL_OR_MODEL_FORCING"},
          "source original Stage13u receipt content set changed")
    for name,value in dig.items():
        guard("/" not in name and "\\" not in name and sha(U/name)==value,
              "actual Stage13u science evidence altered "+name)
    totals=json.loads(file(U/SUMMARY).read_text())
    guard(totals.get("original_source_QC1_native_halfhours_examined")==782 and
          totals.get("source_paired_ERA_RH_QBOT_physical_and_T_gate_count")==768 and
          totals.get("source_original_T_QC0_retained_count")==782 and
          totals.get("source_forcing_or_original_files_changed") is False,
          "Stage13u 768/782 actual source science status changed")
    data=pd.read_csv(file(U/DETAIL),dtype={"native_time":str},low_memory=False)
    groups=pd.read_csv(file(U/GROUP),low_memory=False)
    guard(len(data)==782 and len(groups)==6 and
          tuple(groups.full_source_run_id.astype(int))==IDS and
          data.native_time.is_unique,"six original group identities changed")
    failed=[]; proposals=[]; groupout=[]
    for run in IDS:
        rows=data.loc[data.full_run_id.eq(run)].copy()
        g=groups.loc[groups.full_source_run_id.eq(run)]
        guard(len(g)==1 and len(rows)==N[run] and
              int(g.iloc[0].original_QC1_native_HH)==N[run],
              "original full run count altered "+str(run))
        ix=pd.DatetimeIndex(pd.to_datetime(rows.native_time,
             format="%Y-%m-%d %H:%M:%S",errors="raise"))
        guard(ix.is_unique and ix.is_monotonic_increasing and
              all(ix[i+1]-ix[i]==HH for i in range(len(ix)-1)),
              "original QC1 native source chronology "+str(run))
        ok=flag(rows.source_physics_and_retained_T_gate_PASS)
        protected=flag(rows.protected_existing_2017_Stage12ac_value_not_changed)
        new=flag(rows.additional_QC1_neighbor_operator_approval_absent)
        guard(int((~ok).sum())==FAIL[run] and
              set(ix[protected])==set(ix)&PROTECT and
              int(new.sum())==int(g.iloc[0].new_QC1_neighbours_NOT_OPERATOR_APPROVED),
              "source signed 14 failures / 2017 protected provenance "+str(run))
        for row in rows.loc[~ok].itertuples(index=False):
            fields=("original_paired_ERA_T_C","original_paired_ERA_VPD_hPa",
                    "paired_ERA_RH_percent","hypothetical_ERA_RH_at_site_VPD_hPa",
                    "hypothetical_ERA_RH_at_site_QBOT_kgkg")
            missing=[f for f in fields if not np.isfinite(float(getattr(row,f)))]
            rh=float(row.paired_ERA_RH_percent)
            badrh=np.isfinite(rh) and not (0<rh<100)
            failed.append(dict(run_id=run,native_time=row.native_time,
                original_site_T_C=row.retained_stage13s_site_T_C,
                original_source_T_QC=row.original_TA_F_QC,
                ERA_T_C=row.original_paired_ERA_T_C,
                ERA_VPD_hPa=row.original_paired_ERA_VPD_hPa,
                ERA_RH_percent=row.paired_ERA_RH_percent,
                ERA_at_site_VPD_hPa=row.hypothetical_ERA_RH_at_site_VPD_hPa,
                ERA_at_site_QBOT_kgkg=row.hypothetical_ERA_RH_at_site_QBOT_kgkg,
                source_failure_reason=(";".join(missing) if missing else
                    "ERA_RH_OUT_OF_RANGE" if badrh else
                    "SOURCE_ERA_SITE_T_WATER_PHYSICS_HOLD"),
                preserved_without_repair=True))
        cuts=chunk(list(ix),ok & ~protected)
        for num,ts in enumerate(cuts,1):
            sub=rows.loc[rows.native_time.isin({str(t) for t in ts})]
            v=sub.hypothetical_ERA_RH_at_site_VPD_hPa.to_numpy(dtype=float)
            steps=np.abs(np.diff(v))
            guard(len(sub)==len(ts),"native group time ambiguity")
            l=ix.get_loc(ts[0]);r=ix.get_loc(ts[-1])
            proposals.append(dict(run_id=run,group_id=num,
                source_native_start=str(ts[0]),source_native_end=str(ts[-1]),
                source_native_30min_HH=len(ts),
                paired_ERA_physics_and_internal_VPD_le_4hPa=
                    bool(np.isfinite(v).all() and (steps<=4).all()),
                max_INTERNAL_VPD_step_hPa=float(steps.max()) if len(steps) else 0.,
                left_internal_original_QC1_neighbor=bool(l>0),
                right_internal_original_QC1_neighbor=bool(r<len(ix)-1),
                both_original_DIRECT_QC0_boundaries_verified=bool(
                    l==0 and r==len(ix)-1 and
                    g.iloc[0].both_direct_bookends_original_measured_QC0),
                human_authorization_for_new_original_QC1_source=False))
        groupout.append(dict(run_id=run,original_QC1_native_HH=len(rows),
            paired_ERA_source_physics_PASS=int(ok.sum()),
            source_science_failure_HH=int((~ok).sum()),
            protected_Stage12ac_2017_native_HH=int(protected.sum()),
            valid_unapproved_subepisodes=len(cuts),
            new_source_QC1_neighbors_still_unapproved=int(new.sum()),
            original_two_immediate_VPD_QC0_anchors=bool(
                g.iloc[0].both_direct_bookends_original_measured_QC0)))
    f=pd.DataFrame(failed);c=pd.DataFrame(proposals);g=pd.DataFrame(groupout)
    guard(len(f)==14 and g.source_science_failure_HH.sum()==14 and
          g.paired_ERA_source_physics_PASS.sum()==768 and
          g.protected_Stage12ac_2017_native_HH.sum()==5 and
          g.new_source_QC1_neighbors_still_unapproved.sum()==761,
          "original six-run 14/768/5/761 scope drift")
    report=dict(version=VER,site="US-Me6",
        stage13u_actual_SHA256=sha(U/REC),
        failed_original_ERA_source_native_HH=14,
        source_ERA_physics_PASS_HH=768,all_6_full_run_source_QC1_HH=782,
        unapproved_QC1_neighbors=761,existing_2017_protected=5,
        contiguous_source_valid_subepisodes_for_scientific_review=len(c),
        subepisodes_two_original_measured_QC0_anchors=int(
            c.both_original_DIRECT_QC0_boundaries_verified.sum()),
        no_repair_science_authorized=True,forcing_written=False,
        DATM_ready=False,Slurm_jobs=False)
    print("STAGE13V SOURCE 14 FAILED TIMESTAMPS",flush=True)
    print(f[["run_id","native_time","source_failure_reason"]].to_string(index=False),
          flush=True)
    print("STAGE13V SIX RUNS GROUPED",flush=True)
    print(g.to_string(index=False),flush=True)
    print("STAGE13V SUMMARY",json.dumps(report,indent=2),flush=True)
    return f,c,g,report

def main():
    a=argparse.ArgumentParser()
    m=a.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):m.add_argument("--"+mode,action="store_true")
    cmd=a.parse_args()
    print("STAGE13V ME6 FOURTEEN SOURCE FAILURES BATCH | "+VER,flush=True)
    test()
    if cmd.self_test:return
    fail,parts,groups,summary=audit()
    if cmd.check:
        print("STAGE13V READONLY CHECK PASS | 14 failed original source HH, no forcing writes",flush=True)
        return
    out=ROOT/"reports"/("stage13v_Me6_14_source_QC1_failures_BATCH_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={"14_original_source_failed_ERA_physics_HH.csv":fail,
           "science_valid_QC1_contiguous_groups_PROPOSALS_ONLY.csv":parts,
           "six_remaining_source_QC1_full_runs_science_HOLD.csv":groups}
    for n,frame in files.items():frame.to_csv(out/n,index=False,float_format="%.17g")
    reportname="stage13v_science_review_summary.json"
    (out/reportname).write_text(json.dumps(summary,indent=2)+"\n")
    marker="SOURCE_ONLY_NO_QC1_NEIGHBOR_APPROVAL_OR_FORCING"
    (out/marker).write_text("Signed read-only evidence only. Do not promote source candidates or submit DATM, AD400, Slurm.\n")
    receipt=dict(version=VER,site="US-Me6",
        stage13u_source_receipt_SHA256=sha(U/REC),
        forcing_generated=False,operator_new_approval=False,
        outputs_SHA256={n:sha(out/n) for n in [*files,reportname,marker]})
    (out/"stage13v_sha_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13V SOURCE REVIEW DIR:",out,flush=True)
    print("STAGE13V FOURTEEN ORIGINAL SOURCE FAILURES AND GROUP PROPOSALS REPORT COMPLETE; NO FORCING/MODEL",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13V SCIENCE STOP",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

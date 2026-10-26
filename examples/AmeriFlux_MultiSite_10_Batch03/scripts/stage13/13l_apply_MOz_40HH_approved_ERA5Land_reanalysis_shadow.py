#!/usr/bin/env python3
"""Stage13L: exact operator-approved 40 half-hour US-MOz 2005-01-06/07
ERA5-Land paired TA/VPD with thermodynamic TBOT/QBOT in a NEW research
forcing shadow; never a release to Post-v5, DATM, AD400 or Slurm.

This is a NEW explicit operator-approved alternative source policy.
It does not alter Stage13j's original QC0 rule for the other 27 events.
Original signed Stage13k evidence, CDS binary, BIF, Stage07 and Stage13g
are strictly pinned. The source ERA5-Land grid is ERA5-dependent, not
independent ground truth; no measured QC0 within ±6h is falsely claimed.

--self-test: pure synthetic test; NO SOURCE READ/WRITES
--check: exact signed full-source scientific verification; NO WRITES
--apply: same verification; write one NEW SHA-sealed full 18y research
         shadow only after all 40/40 source/boundary/physics gates PASS.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage13l-v2-20261026-numpy-physical-gate-safe"
HERE=Path(__file__).resolve().parent
J=HERE/"13j_conditional_two_US_MOz_QC1_ERA5Land_SCOPED.py"
J_BLOB="9283b411b49500428e7534b5f12041c71190e93b"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE13K=ROOT/"reports/stage13k_MOz_Jan2005_QC0_extended_and_CDS_comparison_20261026T192412Z_5fb1be73"
STAGE13K_RECEIPT=STAGE13K/"stage13k_original_QC0_ERA5Land_science_SHA_receipt.json"
START=pd.Timestamp("2005-01-06T14:00:00")
END=pd.Timestamp("2005-01-07T09:30:00")
OLD27_START=pd.Timestamp("2005-01-05T20:00:00")
OLD27_END=pd.Timestamp("2005-01-06T09:00:00")
NUMBER=40
FIELDS=("TA_USE","VPD_USE","TBOT","QBOT")
CANON_NAME="US-MOz_CLM_forcing_2004_2021_STG13L_40HH_REANALYSIS_SHADOW.csv"
APPROVAL_SCHEMA="batch03-stage13l-operator-approved-40HH-reanalysis-alternative-v1"

def must(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise RuntimeError("Missing/unsafe required original source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def close(a,b,tol=1e-8):
    return bool(np.isclose(float(a),float(b),atol=tol,rtol=0))

def physical_gate(qbot, rh, vpd, es, temperature, external_pressure, local_pressure):
    """Independent, explicitly parenthesised *boolean* NumPy masks.

    Critical: `& np.abs(external_pressure-local_pressure)<=12000`
    parses as a bitwise operation involving float values before comparison.
    Always place `(np.abs(...) <= 12000)` inside boolean conjunctions.
    Fail closed on NaN, nonphysical vapor pressure or invalid pressure.
    """
    arrays=[np.asarray(a,dtype=float) for a in
           (qbot,rh,vpd,es,temperature,external_pressure,local_pressure)]
    if any(x.shape!=(NUMBER,) for x in arrays):
        raise RuntimeError("Science gate requires exactly 40 native 30min samples")
    q,rh,v,es,temp,extp,localp=arrays
    checks=[
      np.isfinite(q), (q>0), (q<0.08),
      np.isfinite(rh), (rh>0), (rh<100),
      np.isfinite(v), (v>0), (v<es),
      np.isfinite(temp), np.isfinite(es), (es>0),
      np.isfinite(extp), np.isfinite(localp),
      (localp>45000), (localp<111000),
      (extp>45000), (extp<111000),
      (np.abs(extp-localp)<=12000)
    ]
    result=np.logical_and.reduce(checks)
    if result.shape!=(NUMBER,) or result.dtype!=np.bool_:
        raise RuntimeError("Physics gate returned non-bool or wrong shape")
    return result

def module_J():
    if subprocess.run(["git","hash-object",str(must(J))],
       check=True,capture_output=True,text=True).stdout.strip()!=J_BLOB:
        raise RuntimeError("Stage13j verified scientific source Git blob changed")
    spec=importlib.util.spec_from_file_location("batch03_stage13j_pinned",J)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load verified scientific helper module")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.VER!="batch03-stage13j-v4-20261026-UTC-coverage-QC0-edge-census":
        raise RuntimeError("Wrong scientific helper revision")
    if (mod.SCOPE[0]!=(str(OLD27_START).replace(" ","T"),
                          str(OLD27_END).replace(" ","T"),27)
        or mod.SCOPE[1]!=(str(START).replace(" ","T"),
                          str(END).replace(" ","T"),40)):
        raise RuntimeError("Existing operator event definitions changed")
    return mod

def approval_doc(path,j):
    obj=json.loads(must(path).read_text())
    if obj.get("schema")!=APPROVAL_SCHEMA or obj.get("site")!="US-MOz":
        raise RuntimeError("Not a signed Stage13L operator 40-slot waiver")
    ev=obj.get("selected_native_interval",{})
    if (ev.get("first")!="2005-01-06T14:00:00" or
        ev.get("last")!="2005-01-07T09:30:00" or
        ev.get("half_hours")!=NUMBER or ev.get("step_minutes")!=30):
        raise RuntimeError("Operator approval scope drift")
    s=obj.get("evidence_pinned",{})
    if (s.get("original_stage13g_selected_sha256")!=sha(j.CURRENT) or
        s.get("original_CDS_ERA5Land_binary_sha256")!=sha(j.evidence_filename()[0]) or
        s.get("stage13k_report_dir")!=str(STAGE13K) or
        s.get("bif_utc_offset_hours")!=-6):
        raise RuntimeError("Operator pinned evidence does not match original source")
    declined=obj.get("explicitly_not_approved",{})
    if (declined.get("first_event_27_HH")!=
        ["2005-01-05T20:00:00","2005-01-06T09:00:00"] or
        declined.get("January_09_negative_bias_source_QC1") is not True or
        declined.get("submit_Slurm_jobs") is not False or
        declined.get("modify_Stage13g") is not False or
        declined.get("release_Postv5_or_DATM_or_AD400_or_Normal400") is not False):
        raise RuntimeError("Explicit science hold scope is missing")
    return obj

def original_stage13k_seal(j,old_decision,grid_path):
    doc=json.loads(must(STAGE13K_RECEIPT).read_text())
    if (doc.get("version")!="batch03-stage13k-v1-20261026-QC0-source-edge-ERA5Land-evidence" or
        doc.get("operator_Stage13j_decision_SHA256")!=sha(old_decision) or
        doc.get("original_Stage13g_SHA256")!=sha(j.CURRENT) or
        doc.get("CDS_external_evidence_SHA256")!=sha(grid_path) or
        doc.get("science",{}).get("condition_passed_and_repaired_halfhours")!=0):
        raise RuntimeError("Original Stage13k signed 67-slot evidence does not match")
    expected={
        "source_nearest_original_QC0_QC2_by_event_both_edges.csv",
        "all_67_unapproved_CDS_vs_FLUXNET_source_event_comparison.csv",
        "published_BIF_offset_vs_plus_minus_1h_measuredQC0_29_samples.json",
        "both_approved_scoped_event_science_HOLD_summary.json",
        "source_science_decision.json",
        "NO_REPLACEMENTS_QC0_6H_BOTH_EVENTS_FAIL",
    }
    if set(doc.get("output_SHA256",{}))!=expected:
        raise RuntimeError("Unexpected Stage13k original science evidence inventory")
    for name,digest in doc["output_SHA256"].items():
        if sha(STAGE13K/name)!=digest:
            raise RuntimeError("Signed Stage13k science output modified: "+name)
    reports=json.loads(must(STAGE13K/
        "both_approved_scoped_event_science_HOLD_summary.json").read_text())
    if len(reports)!=2:
        raise RuntimeError("Stage13k signed source report no longer has two exact events")
    second=[r for r in reports if r.get("start")=="2005-01-06T14:00:00"]
    first=[r for r in reports if r.get("start")=="2005-01-05T20:00:00"]
    if (len(second)!=1 or len(first)!=1 or
        int(second[0].get("HH",-1))!=40 or
        int(first[0].get("HH",-1))!=27 or
        int(second[0].get("CDS_pair_physics_pass",-1))!=40 or
        int(second[0].get("CDS_vs_companion_T_gate_pass",-1))!=40 or
        int(second[0].get("CDS_vs_companion_RH_gate_pass",-1))!=40 or
        int(second[0].get("CDS_vs_current_model_pressure_gate_pass",-1))!=40 or
        second[0].get("boundary_4C_T_4hPa_VPD_pass") is not True or
        first[0].get("boundary_4C_T_4hPa_VPD_pass") is not False):
        raise RuntimeError("Stage13k science demonstrated PASS/HOLD results changed")
    return doc,first[0],second[0]

def regression():
    t=pd.date_range(START,END,freq="30min")
    assert len(t)==40 and t.is_unique and t[0]==START and t[-1]==END
    assert OLD27_END<START
    assert pd.Timestamp("2005-01-06T10:00:00") not in t
    assert pd.Timestamp("2005-01-09T00:00:00") not in t
    es=6.112*np.exp(17.67*0/(0+243.5))
    e=(es-1.5)*100
    q=0.622*e/(101325-0.378*e)
    assert 0<q<0.01
    arr=lambda x:np.full(NUMBER,float(x),dtype=float)
    g=physical_gate(arr(q),arr(50),arr(1.5),arr(es),
                    arr(0),arr(101325),arr(100000))
    assert g.dtype==np.bool_ and g.shape==(NUMBER,) and int(g.sum())==NUMBER
    p=arr(101325);p[7]=126000
    fail=physical_gate(arr(q),arr(50),arr(1.5),arr(es),
                       arr(0),p,arr(100000))
    assert int(fail.sum())==NUMBER-1 and not fail[7]
    z=arr(50);z[12]=np.nan
    bad=physical_gate(arr(q),z,arr(1.5),arr(es),
                      arr(0),arr(101325),arr(100000))
    assert int(bad.sum())==NUMBER-1 and not bad[12]
    print("STAGE13L SELF-TEST PASS | 40-only scope; all physical-gate float-array precedence, pressure, NaN tests PASS",flush=True)

def scientific_check(approval,previous):
    j=module_J()
    doc=approval_doc(approval,j)
    spec,t,e,c,scope=j.load_native(previous)
    if len(scope)!=2 or len(scope[0])!=27 or len(scope[1])!=40:
        raise RuntimeError("Stage13j source 67-slot scope changed")
    meta=j.metadata(spec)
    if (meta["utc_offset_hours"]!=-6 or
        not close(meta["latitude"],38.7441,1e-6) or
        not close(meta["longitude"],-92.2,1e-6)):
        raise RuntimeError("Original specific BIF UTC-6 and source site identity mismatch")
    grid_path,grid_receipt=j.evidence_filename()
    signed,first,second=original_stage13k_seal(j,previous,grid_path)
    grid=j.nc_data(grid_path,meta)
    # Independent measured original QC0 analogues use the documented BIF
    # offset: UTC -6 has the best observed-QC0 tower T MAE; the previous
    # strict 1C superiority and nearby 6h QC0 anchors are waived only here.
    analogues=t.loc["2005-01-03":"2005-01-10"]
    analogues=analogues.loc[analogues.TA_F_QC.eq(0)&analogues.VPD_F_QC.eq(0)]
    if len(analogues)!=29:
        raise RuntimeError("Stage13k original 29 paired-measured QC0 analogues changed")
    offset_qa={}
    for delta in (-7,-6,-5):
        src=j.at_native(grid,analogues.index,delta)
        dt=np.abs(analogues.TA_F.to_numpy(float)-src.grid_T_C.to_numpy(float))
        dv=np.abs(analogues.VPD_F.to_numpy(float)-src.grid_VPD_hPa.to_numpy(float))
        offset_qa[str(delta)]={"T_MAE_C":float(dt.mean()),"VPD_MAE_hPa":float(dv.mean())}
    if not(offset_qa["-6"]["T_MAE_C"]<offset_qa["-7"]["T_MAE_C"] and
           offset_qa["-6"]["T_MAE_C"]<offset_qa["-5"]["T_MAE_C"] and
           offset_qa["-6"]["T_MAE_C"]<1 and
           offset_qa["-6"]["VPD_MAE_hPa"]<1):
        raise RuntimeError("Original BIF -6h source-QC0 analogue evidence unexpectedly changed")
    ts=scope[1]
    if ts[0]!=START or ts[-1]!=END:
        raise RuntimeError("Authorised source-native interval differs")
    g=j.at_native(grid,ts,meta["utc_offset_hours"])
    original=t.loc[ts]
    comp=e.loc[ts]
    old=c.loc[ts]
    gridT=g.grid_T_C.to_numpy(float)
    gridV=g.grid_VPD_hPa.to_numpy(float)
    compT=comp.TA_ERA.to_numpy(float)
    compV=comp.VPD_ERA.to_numpy(float)
    compRH=100*(1-compV/j.saturation(compT))
    gridES=j.saturation(gridT)
    gridRH=100*(1-gridV/gridES)
    gridEA=(gridES-gridV)*100
    psrf=old.PSRF.to_numpy(float)
    qbot=0.622*gridEA/(psrf-0.378*gridEA)
    cdsp=g.sp.to_numpy(float)
    physical=physical_gate(qbot,gridRH,gridV,gridES,gridT,cdsp,psrf)
    compare=(np.abs(gridT-compT)<=3.5)&(np.abs(gridRH-compRH)<=15)
    sourceQC=(original.TA_F_QC.to_numpy(float)==1)&(
                 original.VPD_F_QC.to_numpy(float)==1)
    sourceErr=np.abs(original.TA_F.to_numpy(float)-compT)>5
    retained=(np.isclose(old.TA_USE.to_numpy(float),original.TA_F.to_numpy(float),atol=1e-8,rtol=0)&
              np.isclose(old.VPD_USE.to_numpy(float),original.VPD_F.to_numpy(float),atol=1e-8,rtol=0))
    allpass=physical&compare&sourceQC&sourceErr&retained
    if not np.all(allpass):
        raise RuntimeError("HOLD: one of the 40 original source, ERA cross-check or pressure/thermodynamic gates failed: "+
                           str(np.flatnonzero(~allpass).tolist()))
    left=ts[0]-pd.Timedelta(minutes=30)
    right=ts[-1]+pd.Timedelta(minutes=30)
    boundaries=[]
    for ti,T,V in ((left,gridT[0],gridV[0]),(right,gridT[-1],gridV[-1])):
        dT=abs(float(c.at[ti,"TA_USE"])-float(T))
        dV=abs(float(c.at[ti,"VPD_USE"])-float(V))
        boundaries.append({"retained_neighbor_native_time":str(ti),
                           "original_neighbor_TA_C":float(c.at[ti,"TA_USE"]),
                           "new_episode_edge_TA_C":float(T),
                           "absolute_TA_jump_C":dT,
                           "absolute_VPD_jump_hPa":dV})
        if dT>4 or dV>4:
            raise RuntimeError("HOLD: new proposed event source boundary fails T/VPD continuity")
    original_report=pd.read_csv(must(STAGE13K/
         "all_67_unapproved_CDS_vs_FLUXNET_source_event_comparison.csv"),
         dtype={"original_native_time":str},low_memory=False)
    keep=original_report.loc[original_report.event_start.eq("2005-01-06T14:00:00")]
    if len(keep)!=40 or not pd.DatetimeIndex(pd.to_datetime(keep.original_native_time)).equals(ts):
        raise RuntimeError("Original Stage13k signed 40-slot independent trace changed")
    if (not np.allclose(keep.signed_distinct_CDS_ERA5Land_T_C.to_numpy(float),gridT,atol=1e-9,rtol=0) or
        not np.allclose(keep.signed_CDS_ERA5Land_VPD_hPa.to_numpy(float),gridV,atol=1e-9,rtol=0)):
        raise RuntimeError("CDS source preview differs from original Stage13k signed grid comparison")
    old27_idx=scope[0]
    assert OLD27_START==old27_idx[0] and OLD27_END==old27_idx[-1]
    modified=pd.DataFrame({
       "source_native_time":[str(v) for v in ts],
       "operator_approved_scope":"JAN06_14_TO_JAN07_0930_40HH_ONLY",
       "original_Stage13g_TA_USE_C":old.TA_USE.to_numpy(float),
       "new_TA_USE_C":gridT,
       "original_Stage13g_VPD_USE_hPa":old.VPD_USE.to_numpy(float),
       "new_VPD_USE_hPa":gridV,
       "original_Stage13g_TBOT_K":old.TBOT.to_numpy(float),
       "new_TBOT_K":gridT+273.15,
       "original_Stage13g_QBOT_kgkg":old.QBOT.to_numpy(float),
       "new_QBOT_kgkg":qbot,
       "original_source_TA_F_QC":original.TA_F_QC.to_numpy(float),
       "original_source_VPD_F_QC":original.VPD_F_QC.to_numpy(float),
       "original_FLUXNET_ERA_T_C":compT,
       "original_FLUXNET_ERA_VPD_hPa":compV,
       "CDS_ERA5Land_model_T_C":gridT,
       "CDS_ERA5Land_model_VPD_hPa":gridV,
       "CDS_and_companion_ERA_abs_T_C":np.abs(gridT-compT),
       "CDS_and_companion_ERA_abs_RH_percentpoints":np.abs(gridRH-compRH),
       "CDS_RH_liquid_water_pct":gridRH,
       "CDS_surface_pressure_Pa":cdsp,
       "retained_Stage13g_PSRF_Pa":psrf,
       "all_reanalysed_science_fields_PASS":allpass,
    })
    summary={
       "version":VERSION,"site":"US-MOz",
       "operator_approved_native_slots":NUMBER,
       "original_Stage13k_zero_repairs_verified":True,
       "CDS_time":str(grid.index.min())+" to "+str(grid.index.max()),
       "original_stage13g_sha256":sha(j.CURRENT),
       "stage13k_signed_receipt_sha256":sha(STAGE13K_RECEIPT),
       "CDS_binary_sha256":sha(grid_path),
       "source_BIF_utc_offset_hours":-6,
       "measured_tower_QC0_analogue_N":29,
       "source_UTC_offset_comparison":offset_qa,
       "QC0_six_hour_both_event_edges_waived_by_explicit_operator_decision":True,
       "ERA5Land_not_independent_measured_tower_truth":True,
       "first_27_HH_HOLD":True,
       "2005Jan09_all_HOLD":True,
       "per_row_source_physics_ERA_pressure_checks_passed":int(allpass.sum()),
       "both_boundary_continuity_pass":True,
       "boundary_checks":boundaries,
       "postv5_approved":False,"DATM_ready":False,
       "spinup_authorized":False,"Slurm_jobs_submitted":False,
       "science_state":"APPROVED_40HH_NEW_SHADOW_ONLY_PENDING_EXPORT"}
    return j,c,modified,summary

def apply(j,c,modified,summary,approval,old_decision):
    times=pd.DatetimeIndex(pd.to_datetime(modified.source_native_time),name="native_time")
    if len(times)!=NUMBER or times.min()!=START or times.max()!=END or times.has_duplicates:
        raise RuntimeError("Wrong event time list at export")
    result=c.copy(deep=True)
    for when,row in zip(times,modified.itertuples(index=False)):
        result.at[when,"TA_USE"]=float(row.new_TA_USE_C)
        result.at[when,"VPD_USE"]=float(row.new_VPD_USE_hPa)
        result.at[when,"TBOT"]=float(row.new_TBOT_K)
        result.at[when,"QBOT"]=float(row.new_QBOT_kgkg)
    # Check all 18y columns and every 30min source-native timestamp.
    changed_counts={}
    eligible=pd.Series(c.index.isin(times),index=c.index)
    for col in c.columns:
        if col in FIELDS:
            old=pd.to_numeric(c[col],errors="coerce").to_numpy(float)
            new=pd.to_numeric(result[col],errors="coerce").to_numpy(float)
            diff=~np.isclose(old,new,rtol=0,atol=1e-12,equal_nan=True)
            if bool((diff&~eligible.to_numpy(bool)).any()):
                raise RuntimeError("UNAPPROVED native timestamp changed: "+col)
            changed_counts[col]=int(diff.sum())
        elif not c[col].equals(result[col]):
            raise RuntimeError("UNAPPROVED meteorology field / original source time changed: "+col)
    if any(changed_counts.get(col,0)!=NUMBER for col in FIELDS):
        raise RuntimeError("Expected exactly 40 real numeric changes in each of four fields "+str(changed_counts))
    for col in FIELDS:
        if not c.loc[~eligible,col].equals(result.loc[~eligible,col]):
            raise RuntimeError("Unapproved source value changed on non-40 native time "+col)
    if sha(j.CURRENT)!=summary["original_stage13g_sha256"]:
        raise RuntimeError("Original signed Stage13g source mutated while in memory")
    dest=j.ROOT/"science_trials"/("stage13l_US_MOz_40HH_user_approved_CDSEra5Land_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    incomplete=dest/"INCOMPLETE_EXPORT_NO_DATM_OR_SPINUP"
    incomplete.write_text("Stage13L isolated candidate export in progress. Do NOT use.\n")
    result.reset_index(drop=True).to_csv(dest/CANON_NAME,index=False,float_format="%.17g")
    # Reparse the entire 315360-row exported output; ensure every field/time.
    reopened=j.forcing(dest/CANON_NAME)
    if not reopened.index.equals(c.index):
        raise RuntimeError("Export changed 18y NOLEAP native chronology")
    for col in c.columns:
        if col in FIELDS:
            if not np.allclose(
                 pd.to_numeric(reopened[col],errors="coerce").to_numpy(float),
                 pd.to_numeric(result[col],errors="coerce").to_numpy(float),
                 atol=1e-9,rtol=0,equal_nan=True):
                raise RuntimeError("Full source CSV exported field is not exactly expected "+col)
        elif pd.api.types.is_numeric_dtype(c[col]):
            old_vals=pd.to_numeric(c[col],errors="raise").to_numpy(dtype=float)
            new_vals=pd.to_numeric(reopened[col],errors="raise").to_numpy(dtype=float)
            if not np.allclose(old_vals,new_vals,rtol=1e-14,atol=1e-12,equal_nan=True):
                raise RuntimeError("Export changed protected source values beyond 17-digit CSV roundtrip "+col)
        elif not c[col].equals(reopened[col]):
            raise RuntimeError("Export altered an unapproved original source time/string field "+col)
    modified.to_csv(dest/"exact_40_operator_approved_native_ERA5Land_T_VPD_TBOT_QBOT_edits.csv",index=False)
    receipt_path=dest/"stage13l_science_summary.json"
    receipt_path.write_text(json.dumps({**summary,
        "new_actual_modified_field_counts":changed_counts,
        "science_state":"40HH_SHADOW_CREATED_NOT_POSTV5_OR_DATM"},indent=2)+"\n")
    marker="NOT_POSTV5_DATM_AD400_NORMAL400_OR_SLURM_APPROVED"
    (dest/marker).write_text(
        "Only 2005-01-06 14:00 through 2005-01-07 09:30 (40 exact native"
        " halfhours) operator-approved paired ERA5-Land TA/VPD and TBOT/QBOT."
        " First 27 source QC1 episodes and Jan09 negative discrepancy untouched."
        " Original Stage07/Stage13g forcing and tower FLUXMET untouched."
        " No locally measured source QC0 anchors existed within 6h."
        " This is an explicitly operator-approved reanalysis-backed"
        " independent RESEARCH SHADOW, not a Post-v5, DATM, CIME or Slurm"
        " production approval.\n")
    files=[CANON_NAME,"exact_40_operator_approved_native_ERA5Land_T_VPD_TBOT_QBOT_edits.csv",
           "stage13l_science_summary.json",marker]
    sealed={
       "version":VERSION,"operator_Stage13L_decision_SHA256":sha(approval),
       "previous_Stage13J_operator_decision_SHA256":sha(old_decision),
       "original_Stage13G_source_SHA256":sha(j.CURRENT),
       "original_Stage07_source_SHA256":sha(j.ORIGINAL),
       "original_Stage13k_report_receipt_SHA256":sha(STAGE13K_RECEIPT),
       "CDS_ERA5Land_original_binary_SHA256":sha(j.evidence_filename()[0]),
       "operator_approved_source_native_events_modified":NUMBER,
       "original_first27_and_Jan09_unchanged":True,
       "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
       "output_SHA256":{name:sha(dest/name) for name in files}
    }
    (dest/"stage13l_MOz_40HH_science_SHA_receipt.json").write_text(
        json.dumps(sealed,indent=2)+"\n")
    incomplete.unlink()
    if sha(j.CURRENT)!=summary["original_stage13g_sha256"]:
        raise RuntimeError("Source Stage13g SHA changed during export; mark output invalid")
    print("STAGE13L 40/40 OPERATOR APPROVED SCIENCE SHADOW SUCCESS:",dest,flush=True)
    print("SOURCE NOLEAP ROWS",len(reopened),"ACTUAL NEW MODEL FIELD EDIT COUNTS",
          changed_counts,flush=True)
    print("NO RAW, STAGE07, STAGE13G, PFT, ZBOT, DATM, AD400, SLURM CHANGES",flush=True)

def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    for key in ("self-test","check","apply"):
        mode.add_argument("--"+key,action="store_true")
    ap.add_argument("--approval",type=Path)
    ap.add_argument("--previous-decision",type=Path)
    args=ap.parse_args()
    print("STAGE13L OPERATOR APPROVED 40HH ERA5LAND ALTERNATIVE | "+VERSION,flush=True)
    regression()
    if args.self_test:return
    if args.approval is None or args.previous_decision is None:
        ap.error("--approval Stage13L and --previous-decision Stage13J JSON required")
    j,c,modified,summary=scientific_check(args.approval,args.previous_decision)
    print("STAGE13L SCIENCE PREVIEW",json.dumps(summary,indent=2),flush=True)
    print("STAGE13L EXACT FIRST & LAST APPROVED ROWS",flush=True)
    print(pd.concat([modified.head(2),modified.tail(2)]).to_string(index=False),flush=True)
    if args.check:
        print("STAGE13L READONLY CHECK PASS | 40/40 required source, CDS/ERA, humidity and both boundaries PASS",flush=True)
        print("NO FORCING WRITES",flush=True)
        return
    apply(j,c,modified,summary,args.approval,args.previous_decision)

if __name__=="__main__":
    try:main()
    except Exception as error:
        print("STAGE13L SCIENCE STOP:",error,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage11m: read-only original/ERA/Stage07/11h/11l four-boundary audit.

Verifies SHA-sealed Stage11l isolated US-NC2 science successor, including
full 367920-row VPD/QBOT-only change mask; loads SHA-proven original
FLUXMET and site-downscaled ERA via previously verified Stage11c reader.
Displays full source-native +/-2h (10 rows) context for exactly 4
remaining high-impact VPD half-hour transitions.

--self-test: no IRIDIS data or writes
--check: all SHA/source/physics and contexts, ZERO writes
--run: same checks then NEW standalone reports/stage11m_* CSVs with SHA
        receipt ONLY, never a changed forcing or Post-v5 approval.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11m-v1-20261024-four-boundary-no-forcing-write"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows"/"examples/AmeriFlux_MultiSite_10_Batch03"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
L=ROOT/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
C=BASE/"scripts/stage11/11c_qc0_manual_era_change_review.py"
C_BLOB="2e7402fc67fabe34aeeb990d98117730bcbbddfa"
LEDGER=BASE/"docs/STAGE11L_USER_APPROVED_11_US_NC2_NEIGHBOUR_RH_ADDITIONS_2026-10-24.csv"
LEDGER_BLOB="53912c25c5da32347e46739dd6ebf11036664683"
SOURCE_V5_COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
H_NAME="US-NC2_shadow_companion_ERA_RH_NOLEAP.csv"
L_NAME="US-NC2_humidity_only_new_shadow_NOLEAP.csv"
L_FILES={
    L_NAME,
    "11_new_user_RH_event_differences.csv",
    "11_new_target_adjacent_jump_changes.csv",
    "6_old_vs_new_event_outer_boundaries.csv",
    "US-NC2_yearly_impact.csv",
    "two_unchanged_Stage11h_site_SHA_refs.json",
    "SCIENTIFIC_HOLD.md",
}
TARGETS={
 "202503181830","202503181930",
 "202503231300","202503231330","202503231400",
 "202503231430","202503231500",
 "202503250800","202503250830","202503250930","202503251000"
}
EDGES=[
 ("MAR18_NEW_START","202503181800","202503181830",1.310000,4.997141),
 ("MAR23_OLD_START","202503230830","202503230900",9.467392,9.467392),
 ("MAR23_NEW_END","202503231500","202503231530",2.053000,4.812737),
 ("MAR25_NEW_END","202503251000","202503251030",0.051500,5.859252),
]

def checked_file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Absent or symlink source file "+str(p))
    return p

def checked_dir(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Absent or symlink source dir "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with checked_file(p).open("rb") as f:
        for z in iter(lambda:f.read(1<<20),b""):
            h.update(z)
    return h.hexdigest()

def git_blob(p):
    b=checked_file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load_module():
    if git_blob(C)!=C_BLOB:
        raise ValueError("Stage11c source module blob is not the reviewed one")
    spec=importlib.util.spec_from_file_location("stage11c_pinned_for_11m",C)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def saturation(t):
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*np.asarray(t,dtype=float)/
                            (np.asarray(t,dtype=float)+243.5))

def rh(t,v):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        s=saturation(t)
        return 100*(s-np.asarray(v,dtype=float))/s

def verify_receipts():
    for p in (ROOT,S07,H,L,BASE):
        checked_dir(p)
    for p in (S07,H,L):
        checked_file(p/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    if git_blob(LEDGER)!=LEDGER_BLOB:
        raise ValueError("New user approved eleven-event ledger Git blob mismatch")
    l=json.loads(checked_file(L/"stage11l_scientific_hold_receipt.json").read_text())
    h=json.loads(checked_file(H/"sha_sealed_shadow_trial_receipt.json").read_text())
    if (l.get("version")!="stage11l-v1-20261024-11-humidity-only-successor"
        or l.get("new_user_11_Git_blob")!=LEDGER_BLOB
        or l.get("Stage11h_source_receipt_SHA256")!=sha(H/"sha_sealed_shadow_trial_receipt.json")
        or l.get("added_neighbour_events")!=11
        or l.get("newly_different_VPD")!=11
        or l.get("cumulative_old_ERA_RH_target_count")!=53
        or l.get("combined_ERA_RH_target_count")!=64
        or l.get("noleap_US_NC2_rows")!=367920
        or l.get("reviewed_episode_outer_boundaries")!=6
        or l.get("retained_EC_tower_TA_and_TBOT") is not True
        or l.get("other_two_site_files_unchanged") is not True
        or l.get("Postv5_approved")!=0
        or l.get("DATM_ready")!=0 or l.get("spinup_authorized")!=0
        or l.get("INCOMPLETE_marker_present") is not True
        or set(l.get("output_sha256",{}))!=L_FILES):
        raise ValueError("Stage11l sealed science trial receipt does not match approved scope")
    for name,expected in l["output_sha256"].items():
        if sha(L/name)!=expected:
            raise ValueError("Stage11l output file SHA mismatch "+name)
    if (h.get("version")!="stage11h-v1-20261024-53-ERA-RH-isolated-trial"
        or h.get("ERA_RH_selected_target_rows")!=53
        or h.get("human_decisions")!=62
        or h.get("actually_different_VPD_values")!=43
        or h.get("Postv5_approved")!=0
        or h.get("DATM_ready")!=0 or h.get("spinup_authorizations")!=0):
        raise ValueError("Stage11h sealed source receipt differs")
    if sha(H/H_NAME)!=h["output_sha256"][H_NAME]:
        raise ValueError("Old Stage11h US-NC2 CSV SHA mismatch")
    refs=json.loads(checked_file(L/"two_unchanged_Stage11h_site_SHA_refs.json").read_text())
    for site in ("US-MOz","US-Mpj"):
        name=f"{site}_shadow_companion_ERA_RH_NOLEAP.csv"
        if (refs.get(site,{}).get("file")!=str(H/name)
            or refs.get(site,{}).get("SHA256")!=h["output_sha256"][name]
            or sha(H/name)!=h["output_sha256"][name]):
            raise ValueError("Stage11l other-site original file reference SHA mismatch")
    d=pd.read_csv(checked_file(LEDGER),dtype={"native_key":str})
    if (len(d)!=11 or set(d.native_key)!=TARGETS or
        d.duplicated(["site","native_key","variable"]).any() or
        d.site.ne("US-NC2").any() or d.variable.ne("VPD_F").any() or
        d.human_decision.ne("APPROVE_STAGE11L_ISOLATED_SHADOW_RH_TRANSFER").any()):
        raise ValueError("11 newly user-selected timestamp IDs differ from signed choice")
    return d,l,h

def full_data():
    ledger,lreceipt,hreceipt=verify_receipts()
    c=load_module()
    specs,pins,outputs,_=c.load_and_verify_inputs()
    raw,force,era,*_=c.read_site("US-NC2",specs["US-NC2"],pins,outputs)
    h=pd.read_csv(checked_file(H/H_NAME),low_memory=False)
    l=pd.read_csv(checked_file(L/L_NAME),low_memory=False)
    for x in (h,l):
        if len(x)!=367920 or list(x.columns)!=SOURCE_V5_COLS:
            raise ValueError("Full-year Stage11h/Stage11l source schema differs")
    if not (len(force)==len(h)==len(l)==len(raw)==367920):
        raise ValueError("Forcing/source NOLEAP 367920 row count mismatch")
    ts=raw.native_key.astype(str).to_numpy()
    for x in (force,h,l):
        parsed=pd.to_datetime(x.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
        observed=parsed.dt.strftime("%Y%m%d%H%M").to_numpy()
        if not np.array_equal(ts,observed):
            raise ValueError("Stage07, 11h or 11l source clock mismatch")
    if np.any(pd.Series(ts).duplicated()):
        raise ValueError("Source native keys duplicate")
    ids={key:i for i,key in enumerate(ts)}
    if not TARGETS.issubset(ids):
        raise ValueError("New user timestamp(s) missing from verified original forcing")
    modified=np.zeros(len(h),dtype=bool)
    modified[[ids[k] for k in TARGETS]]=True
    for col in SOURCE_V5_COLS:
        if col=="time":
            if not h[col].equals(l[col]):
                raise ValueError("Native timestamp strings changed")
        elif col in ("VPD_USE","QBOT"):
            a=h[col].to_numpy(dtype=float)
            b=l[col].to_numpy(dtype=float)
            if not np.allclose(a[~modified],b[~modified],rtol=1e-12,atol=1e-11):
                raise ValueError("Non-target humidity field modified "+col)
        else:
            if not np.allclose(h[col].to_numpy(dtype=float),
                               l[col].to_numpy(dtype=float),
                               rtol=1e-12,atol=1e-11):
                raise ValueError("Forbidden EC tower temperature/pressure/other change "+col)
    actual=np.flatnonzero(~np.isclose(h.VPD_USE.to_numpy(dtype=float),
                                l.VPD_USE.to_numpy(dtype=float),rtol=1e-10,atol=1e-10))
    if len(actual)!=11 or set(actual)!=set(np.flatnonzero(modified)):
        raise ValueError("New Stage11l actual VPD changes differ from 11 approved source keys")
    for df in (h,l):
        t=df.TA_USE.to_numpy(dtype=float)
        p=df.PSRF.to_numpy(dtype=float)
        v=df.VPD_USE.to_numpy(dtype=float)
        vapor=saturation(t)-v
        specific=0.622*vapor*100/(p-0.378*vapor*100)
        humidity=rh(t,v)
        if (not np.isfinite(specific).all() or
            not np.isfinite(humidity).all() or
            not np.all(vapor>0) or not np.all(humidity>0) or
            not np.all(humidity<=100.05) or
            not np.allclose(specific,df.QBOT.to_numpy(dtype=float),
                            rtol=1e-9,atol=1e-10)):
            raise ValueError("Full-site preserved/altered QBOT water physics invalid")
    eraidx=era.set_index("TIMESTAMP_START",verify_integrity=True)
    return ids,raw,force,eraidx,h,l,ledger

def inspect():
    ids,raw,force,era,h,l,ledger=full_data()
    old=h.VPD_USE.to_numpy(dtype=float)
    new=l.VPD_USE.to_numpy(dtype=float)
    base=force.VPD_USE.to_numpy(dtype=float)
    boundaries=[]
    contexts=[]
    for label,left,right,expected_old,expected_new in EDGES:
        i,j=ids[left],ids[right]
        if j!=i+1:
            raise ValueError("Boundary half-hours not consecutive")
        o=abs(old[j]-old[i]);n=abs(new[j]-new[i])
        if abs(o-expected_old)>1e-5 or abs(n-expected_new)>1e-5:
            raise ValueError("Known user-reported Stage11l boundary not reproduced "+label)
        boundaries.append({
            "boundary_id":label,"site":"US-NC2",
            "left_key":left,"right_key":right,
            "Stage11h_old_abs_jump_hPa":o,
            "Stage11l_new_abs_jump_hPa":n,
            "ADDED_jump_hPa":n-o,
            "new_jump_over_4hPa":bool(n>4),
            "added_jump_over_2hPa":bool(n-o>2),
            "human_science_review":"HOLD_BOUNDARY_SOURCE_CLOCK_INSTRUMENT",
        })
        # Two preceding hours and two following hours, including the two
        # half-hour endpoints: exactly 10 records per boundary ID.
        if i<4 or j+4>=len(old):
            raise ValueError("Boundaries outside full-site source windows")
        for position in range(i-4,j+5):
            key=str(raw.native_key.iloc[position])
            if key not in era.index:
                raise ValueError("Missing original paired ERA timestamp "+key)
            sr=raw.iloc[position]
            er=era.loc[key]
            srcT=float(sr.TA_F);srcV=float(sr.VPD_F)
            eraT=float(er.TA_ERA);eraV=float(er.VPD_ERA)
            towerT=float(l.TA_USE.iloc[position])
            sourceRH=float(rh(srcT,srcV))
            eraRH=float(rh(eraT,eraV))
            oldRH=float(rh(towerT,old[position]))
            newRH=float(rh(towerT,new[position]))
            contexts.append({
                "boundary_id":label,"site":"US-NC2",
                "position_relative_to_LEFT_halfhours":position-i,
                "native_key":key,
                "original_TA_F_C":srcT,
                "original_TA_F_QC":float(sr.TA_F_QC),
                "original_VPD_F_hPa":srcV,
                "original_VPD_F_QC":float(sr.VPD_F_QC),
                "original_actual_vapour_ea_hPa":float(saturation(srcT)-srcV),
                "original_implied_RH_water_pct":sourceRH,
                "companion_ERA_T_C":eraT,
                "companion_ERA_VPD_hPa":eraV,
                "companion_ERA_RH_water_pct":eraRH,
                "retained_EC_tower_TA_C":towerT,
                "Stage07_VPD_hPa":float(base[position]),
                "Stage11h_VPD_hPa":float(old[position]),
                "Stage11l_VPD_hPa":float(new[position]),
                "Stage11h_RH_water_pct":oldRH,
                "Stage11l_RH_water_pct":newRH,
                "Stage07_VPD_changed_from_source":bool(
                    abs(base[position]-srcV)>1e-7),
                "Stage11h_VPD_changed_from_Stage07":bool(
                    abs(old[position]-base[position])>1e-7),
                "Stage11l_VPD_changed_from_Stage11h":bool(
                    abs(new[position]-old[position])>1e-7),
                "Stage11l_QBOT_kgkg":float(l.QBOT.iloc[position]),
                "human_review_status":"HOLD_NO_ADDITIONAL_REPAIR_APPROVED",
            })
    boundaries=pd.DataFrame(boundaries)
    context=pd.DataFrame(contexts)
    if (len(boundaries)!=4 or len(context)!=40 or
        context.duplicated(["boundary_id","native_key"]).any() or
        int(boundaries.new_jump_over_4hPa.sum())!=4 or
        int(boundaries.added_jump_over_2hPa.sum())!=3):
        # For these four boundaries, only 3 are newly increased >2 hPa:
        # MAR23_OLD_START retains 9.467392 hPa from Stage11h.
        raise ValueError("Four-boundary source context/count unexpectedly changed")
    return boundaries,context

def self_test():
    assert len(EDGES)==4 and len(TARGETS)==11
    x=rh(20.,5.)
    assert np.isfinite(x) and 0<x<100
    assert float(rh(0.,20.))<0
    for label,left,right,ov,nv in EDGES:
        t1=pd.to_datetime(left,format="%Y%m%d%H%M")
        t2=pd.to_datetime(right,format="%Y%m%d%H%M")
        assert t2-t1==pd.Timedelta(minutes=30)
        assert nv>4
    print("STAGE11M SELF-TEST PASS: source RH, 4 native 30min boundaries, strict no-write hold",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11M — STAGE11L FOUR RESIDUAL VPD BOUNDARY SCIENCE CHECK | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    boundaries,contexts=inspect()
    print("\n========== FOUR STAGE11L HIGH VPD-JUMP BOUNDARIES ==========",flush=True)
    print(boundaries.to_string(index=False),flush=True)
    print("\n========== 40 EXACT NATIVE SOURCE/ERA/STAGE07/11H/11L CONTEXT ROWS ==========",flush=True)
    print(contexts[["boundary_id","native_key","original_TA_F_C","original_VPD_F_QC",
        "original_VPD_F_hPa","original_implied_RH_water_pct",
        "companion_ERA_RH_water_pct","retained_EC_tower_TA_C",
        "Stage07_VPD_hPa","Stage11h_VPD_hPa","Stage11l_VPD_hPa",
        "Stage11l_RH_water_pct","Stage07_VPD_changed_from_source",
        "Stage11h_VPD_changed_from_Stage07",
        "Stage11l_VPD_changed_from_Stage11h"]].to_string(index=False),flush=True)
    print("\nSTAGE11M SUMMARY: source_site_rows=367920 new_Stage11l_events=11 "
        "four_residual_jump_boundaries=4 contexts=40 "
        "unchanged_EC_tower_T=True new_human_repair_approvals=0 "
        "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: NO report, forcing, DATM, CIME or Slurm writes.",flush=True)
        return
    out=ROOT/"reports"/("stage11m_stage11l_four_boundary_context_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    outputs={
        "4_high_jump_boundary_differences.csv":boundaries,
        "40_halfhours_original_ERA_Stage07_Stage11h_Stage11l_context.csv":contexts
    }
    for name,frame in outputs.items():
        frame.to_csv(out/name,index=False)
    hold="""# Read-only Stage11m source science boundary HOLD

Stage11l already passed a numerical humidity-only 11-event shadow trial.
Four residual >4 hPa half-hour jumps need a human decision after inspection
of tower sensor and QC, original FLUXMET water vapour pressure, companion
site-downscaled ERA5 temperature/RH, Stage07/Stage11h/Stage11l candidates
and native source clock. An introduced VPD jump alone is not evidence
that the humidity replacement is invalid. Do not change any target mask
or QC record by automatic interpolation or threshold, and never edit
Stage07, Stage11h or Stage11l original/isolated forcing.
All Post-v5, DATM, CIME and spinup approvals remain ZERO.
"""
    (out/"SCIENTIFIC_HOLD.md").write_text(hold,encoding="utf-8")
    receipt={
        "version":VERSION,
        "source_Stage11l_receipt_SHA256":sha(L/"stage11l_scientific_hold_receipt.json"),
        "source_Stage11h_receipt_SHA256":sha(H/"sha_sealed_shadow_trial_receipt.json"),
        "source_Stage07_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
        "boundary_transitions":4,"original_native_context_rows":40,
        "new_repair_approvals":0,"Postv5_approved":0,
        "DATM_ready":0,"spinup_authorizations":0,
        "input_forcing_unmodified":True,
        "output_sha256":{n:sha(out/n) for n in [*outputs,"SCIENTIFIC_HOLD.md"]}
    }
    (out/"stage11m_read_only_boundary_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11M REVIEW REPORT DIR:",out,flush=True)
    print("NO STAGE07, STAGE11H, STAGE11L, DATM, CIME OR SLURM MODIFIED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("STAGE11M STOP:",str(e),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

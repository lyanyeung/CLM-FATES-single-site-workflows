#!/usr/bin/env python3
"""Stage12d: rescue additional Stage12c six-site humidity gaps in isolated shadows.

Stage12c applied 1687 source/grid RH event patches and intentionally held 233
original physics-conflict records. It revealed 8164 further source humidity
holes. Stage07 completed numerical candidates at only THREE sites; the six
sites here have no verified complete Stage07 base forcing.

Use ONLY exact release-paired source timestamp TA_ERA/VPD_ERA to calculate
water RH, then rebuild VPD/QBOT at UNCHANGED Stage12c TA_USE and PSRF.
Try only Stage12c missing-humidity rows NOT in the original 233 scientific
holds. Original FLUXMET VPD_F QC must be 1 or 2; never overwrite QC0 or
unknown-QC humidity. Reject paired source with invalid physical RH,
temperature mismatch >5C, or implied ice supersaturation for T<0C.
Reject additional source candidates with a new adjacent absolute VPD
jump >4 hPa (including exact neighbouring recovered candidate rows).
Maintain the original 233 explicit held humidity rows as NaN ALWAYS.

READ-ONLY --check. --run writes ONLY a NEW separately SHA-sealed
science-trials directory: six full original NOLEAP timeline CSVs,
source evidence and unresolved/retained holds. No DATM or spinup.
Previously sealed Stage07/12b/12c/11h/11l/11q never change.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12d-v1-20261024-six-site-matched-companion-RH-gap-rescue"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S12B=ROOT/"science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893"
S12C=ROOT/"science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e"
SIX=("US-NR3","US-Kon","US-NR1","US-MMS","US-MtB","US-Me6")
EXPECTED_PATCH={"US-NR3":1312,"US-Kon":227,"US-NR1":116,
                "US-MMS":17,"US-MtB":14,"US-Me6":1}
EXPECTED_HOLDS={"US-NR3":172,"US-Kon":2,"US-NR1":57,
                "US-MMS":1,"US-MtB":1,"US-Me6":0}
COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND",
      "PRECTmms","TA_USE","VPD_USE"]
SEALED_C={
    *(site+"_STAGE12C_NOT_MODEL_READY_NOLEAP.csv" for site in SIX),
    "6_site_full_timeline_and_hold_counts.csv",
    "1687_exact_native_RH_patch_provenance.csv",
    "all_remaining_shadow_missing_or_held_rows.csv",
    "all_1687_patch_adjacent_source_boundary_checks.csv",
    "SCIENTIFIC_HOLD.md"
}
SEALED_B={
    "six_site_humidity_only_event_patch_candidates.csv",
    "seven_site_science_holds_including_US-Me2.csv",
    "seven_site_patch_and_hold_counts.csv","SCIENTIFIC_HOLD.md"}

def safe_file(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/symlink original evidence file: "+str(p))
    return p

def sha(path):
    h=hashlib.sha256()
    with safe_file(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def number(series):
    a=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a)|(a<=-9990)]=np.nan
    return a

def es_water(c):
    c=np.asarray(c,dtype=float)
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*c/(c+243.5))

def es_ice(c):
    c=np.asarray(c,dtype=float)
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(22.46*c/(c+272.62))

def humid(ta,pressure,rh):
    sat=es_water(ta)
    vap=sat*np.asarray(rh,dtype=float)/100.
    vpd=sat-vap
    ea=100*vap
    q=.622*ea/(np.asarray(pressure,dtype=float)-.378*ea)
    return vpd,q

def self_test():
    assert len(SIX)==6 and sum(EXPECTED_PATCH.values())==1687
    assert sum(EXPECTED_HOLDS.values())==233
    v,q=humid(-10.,90000.,60.)
    assert 0<v<es_water(-10.) and 0<q<.08
    assert es_ice(-10.)<es_water(-10.)
    assert len(SEALED_C)==11 and len(SEALED_B)==4
    print("STAGE12D SELF-TEST PASS: six original native timelines, 233 hard holds, humidity transfer at unchanged TA/PSRF, zero writes",flush=True)

def inputs():
    for x in (ROOT,S07,S12B,S12C):
        if not x.is_dir() or x.is_symlink():
            raise ValueError("Missing/symlink sealed source tree: "+str(x))
    for folder in (S07,S12B,S12C):
        safe_file(folder/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    rc=json.loads(safe_file(S12C/"stage12c_research_shadow_SHA_receipt.json").read_text())
    rb=json.loads(safe_file(S12B/"stage12b_numeric_candidate_receipt.json").read_text())
    if (rc.get("version")!="batch03-stage12c-v1-20261024-six-time-complete-science-hold-shadows"
        or rc.get("stage12b_receipt_SHA256")!=sha(S12B/"stage12b_numeric_candidate_receipt.json")
        or rc.get("stage07_manifest_SHA256")!=sha(S07/"exact_input_manifest.json")
        or rc.get("research_only_six_full_native_timeline_sites")!=6
        or rc.get("original_ERA5Land_source_grid_RH_candidate_patch_times")!=1687
        or rc.get("physically_held_times_intentionally_missing")!=233
        or rc.get("new_source_clock_approvals")!=0
        or rc.get("Postv5_approved")!=0 or rc.get("DATM_ready")!=0
        or rc.get("spinup_authorized")!=0
        or rc.get("INCOMPLETE_marker_present") is not True
        or rc.get("model_ready") is not False
        or set(rc.get("output_sha256",{}))!=SEALED_C):
        raise ValueError("Stage12c six site full-source SHA input receipt differs")
    for name,sig in rc["output_sha256"].items():
        if sha(S12C/name)!=sig:
            raise ValueError("Stage12c input file SHA differs: "+name)
    if (rb.get("version")!="batch03-stage12b-v1-20261024-six-site-bulk-humidity-numeric-patch"
        or rb.get("numeric_bulk_candidate_rows")!=1687
        or rb.get("original_science_physics_holds")!=233
        or rb.get("original_source_clock_holds")!=4
        or rb.get("additional_math_holds")!=0
        or rb.get("Postv5_approved")!=0 or rb.get("DATM_ready")!=0
        or rb.get("spinup_authorized")!=0
        or set(rb.get("output_sha256",{}))!=SEALED_B):
        raise ValueError("Stage12b source repair/hold science gate differs")
    for name,sig in rb["output_sha256"].items():
        if sha(S12B/name)!=sig:
            raise ValueError("Stage12b input SHA differs "+name)
    manifest=json.loads(safe_file(S07/"exact_input_manifest.json").read_text())
    specs={rec["site"]:rec for rec in manifest["sites"]}
    if len(specs)!=10 or not set(SIX)<set(specs):
        raise ValueError("Stage07 original ten site inventory changed")
    pins={str(Path(name).resolve()):v for name,v in manifest["input_sha256"].items()}
    for site in SIX:
        for kind in ("primary","era"):
            src=safe_file(specs[site][kind])
            if sha(src)!=pins.get(str(src.resolve())):
                raise ValueError("Original FLUXMET/companion era source SHA changed: "+str(src))
    ledger=pd.read_csv(safe_file(S12B/"seven_site_science_holds_including_US-Me2.csv"),
                       dtype={"site":str},low_memory=False)
    if (len(ledger)!=237 or ledger.site.value_counts().to_dict()!={**{
        k:v for k,v in EXPECTED_HOLDS.items() if v},"US-Me2":4}):
        raise ValueError("Exactly 233 Stage12b scientific holds and 4 US-Me2 clock holds required")
    return specs,ledger

def read_native(site,spec):
    first,last,minutes=int(spec["first_year"]),int(spec["last_year"]),int(spec["native_minutes"])
    if minutes!=(60 if site=="US-MMS" else 30):
        raise ValueError("Native interval mismatch: "+site)
    fpath=safe_file(spec["primary"])
    epath=safe_file(spec["era"])
    header=set(pd.read_csv(fpath,nrows=0).columns)
    qcol="VPD_F_QC"
    if not {"TIMESTAMP_START","VPD_F"}<=header:
        raise ValueError("Missing original FLUXMET VPD metadata: "+site)
    cols=["TIMESTAMP_START","VPD_F"]+([qcol] if qcol in header else [])
    raw=pd.read_csv(fpath,usecols=cols,dtype={"TIMESTAMP_START":str},low_memory=False)
    if qcol not in raw:raw[qcol]=np.nan
    companion=pd.read_csv(epath,usecols=[
        "TIMESTAMP_START","TA_ERA","VPD_ERA"],dtype={"TIMESTAMP_START":str},low_memory=False)
    for d in (raw,companion):
        times=pd.to_datetime(d.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        mask=times.dt.year.between(first,last)&~((times.dt.month==2)&(times.dt.day==29))
        d.drop(index=d.index[~mask],inplace=True)
        d.reset_index(drop=True,inplace=True)
    expected=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                 freq=f"{minutes}min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if (len(raw)!=len(expected) or len(companion)!=len(expected) or
        not np.array_equal(raw.TIMESTAMP_START.to_numpy(),
                           expected.strftime("%Y%m%d%H%M")) or
        not raw.TIMESTAMP_START.equals(companion.TIMESTAMP_START)):
        raise ValueError("Raw/companion native time source exact chronology mismatch: "+site)
    return raw,companion

def one_site(site,spec,ledger):
    oldpath=S12C/(site+"_STAGE12C_NOT_MODEL_READY_NOLEAP.csv")
    orig=pd.read_csv(safe_file(oldpath),low_memory=False)
    raw,companion=read_native(site,spec)
    if len(orig)!=len(raw) or list(orig.columns)!=COLS:
        raise ValueError("Stage12c full native forcing shape changed: "+site)
    native=pd.to_datetime(orig.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    keys=native.dt.strftime("%Y%m%d%H%M").to_numpy()
    if not np.array_equal(keys,raw.TIMESTAMP_START.to_numpy()):
        raise ValueError("Stage12c full original time keys differ from SHA FLUXMET")
    n=len(orig)
    index={key:i for i,key in enumerate(keys)}
    holds=ledger.loc[ledger.site.eq(site)]
    protected=np.zeros(n,dtype=bool)
    for rec in holds.itertuples(index=False):
        key=pd.Timestamp(rec.time).strftime("%Y%m%d%H%M")
        if key not in index or protected[index[key]]:
            raise ValueError("Duplicate or missing original 233 physics hold time: "+site+" "+key)
        protected[index[key]]=True
    if int(protected.sum())!=EXPECTED_HOLDS[site]:
        raise ValueError("Stage12c original held times count mismatch: "+site)
    if np.isfinite(orig.VPD_USE.to_numpy(dtype=float)[protected]).any() or \
       np.isfinite(orig.QBOT.to_numpy(dtype=float)[protected]).any():
        raise ValueError("Stage12c protected humidity science hold was unexpectedly filled")

    t=orig.TA_USE.to_numpy(dtype=float)
    p=orig.PSRF.to_numpy(dtype=float)
    oldv=orig.VPD_USE.to_numpy(dtype=float)
    oldq=orig.QBOT.to_numpy(dtype=float)
    wet=np.isnan(oldv)|np.isnan(oldq)
    newable=wet &~protected
    qc=number(raw.VPD_F_QC)
    e_t=number(companion.TA_ERA)
    e_v=number(companion.VPD_ERA)
    sat=es_water(e_t)
    with np.errstate(divide="ignore",invalid="ignore"):
        era_rh=100*(sat-e_v)/sat
        source_ea=sat-e_v
        ice_rel=era_rh*es_water(t)/es_ice(t)
    valid_site=np.isfinite(t)&(t>=-80)&(t<=65)&np.isfinite(p)&(p>=50000)&(p<=110000)
    valid_ERA=np.isfinite(e_t)&np.isfinite(e_v)&np.isfinite(era_rh)&(
        (era_rh>0)&(era_rh<=100)&(source_ea>0)&(e_v>=0))
    align=np.isfinite(e_t)&np.isfinite(t)&(np.abs(t-e_t)<=5)
    valid_phase=(t>=0)|np.isfinite(ice_rel)&(ice_rel<=100.)
    recoverable=newable&np.isin(qc,[1.,2.])&valid_site&valid_ERA&align&valid_phase
    nv,nq=humid(t,p,era_rh)
    recoverable&=np.isfinite(nv)&np.isfinite(nq)&(nv>=0)&(nv<es_water(t))&(nq>0)&(nq<.08)
    # Keep all severe/uncertain candidate source events held. No Qc0
    # changed or authorizations added. Remove new high discontinuity
    # only at candidate borders; no iterative arbitrary smoothing.
    reasons=np.full(n,"",dtype=object)
    reasons[newable&~np.isin(qc,[1.,2.])]="SOURCE_VPD_QC0_OR_UNKNOWN_HOLD"
    reasons[newable&np.isin(qc,[1.,2.])&~valid_site]="TOWER_TEMP_PRESSURE_INVALID"
    reasons[newable&np.isin(qc,[1.,2.])&valid_site&~valid_ERA]="COMPANION_ERA_RH_INVALID"
    reasons[newable&np.isin(qc,[1.,2.])&valid_site&valid_ERA&~align]="COMPANION_ERA_T_MISMATCH_GT5C"
    reasons[newable&np.isin(qc,[1.,2.])&valid_site&valid_ERA&align&~valid_phase]="WATER_RH_IMPLIES_ICE_SUPERSATURATION"
    reasons[newable&np.isin(qc,[1.,2.])&valid_site&valid_ERA&align&valid_phase&~recoverable]="INVALID_VPD_QBOT_PHYSICS"
    protected_orig=recoverable.copy()
    trial=orig.copy(deep=True)
    # Protected Stage12b event patch VPD/QBOT remain numerically identical.
    trial.loc[recoverable,"VPD_USE"]=nv[recoverable]
    trial.loc[recoverable,"QBOT"]=nq[recoverable]

    # A candidate's immediately adjacent edge must remain <=4 hPa.
    # If flagged, do not "move" errors: return that timestamp to a
    # source-metadata HOLD rather than smoothing/editing its neighbour.
    for _ in range(5):
        curr=trial.VPD_USE.to_numpy(dtype=float)
        bad=np.zeros(n,dtype=bool)
        for i in np.flatnonzero(recoverable):
            for j in (i-1,i+1):
                if j<0 or j>=n or not np.isfinite(curr[j]):
                    continue
                if abs(curr[j]-curr[i])>4:
                    bad[i]=True
        if not bad.any():break
        recoverable[bad]=False
        reasons[bad]="NEW_EDGE_JUMP_GT4HPA_HOLD"
        trial.loc[bad,"VPD_USE"]=np.nan
        trial.loc[bad,"QBOT"]=np.nan
    else:
        raise ValueError("Iterative new humidity jump guard failed to settle: "+site)
    if (not trial["TBOT"].equals(orig["TBOT"]) or
        not trial["TA_USE"].equals(orig["TA_USE"]) or
        not trial["PSRF"].equals(orig["PSRF"]) or
        not trial["time"].equals(orig["time"])):
        raise ValueError("Stage12d attempted to rewrite tower TA, pressure or native clock")
    for col in COLS:
        if col not in ("VPD_USE","QBOT") and not orig[col].equals(trial[col]):
            raise ValueError("Stage12d illegally changed other forcing variable: "+col)
    if not np.array_equal(
        orig.VPD_USE.to_numpy(dtype=float)[~recoverable],
        trial.VPD_USE.to_numpy(dtype=float)[~recoverable],equal_nan=True):
        raise ValueError("Stage12d changed off-target pre-existing humidity")
    if not np.array_equal(
        orig.QBOT.to_numpy(dtype=float)[~recoverable],
        trial.QBOT.to_numpy(dtype=float)[~recoverable],equal_nan=True):
        raise ValueError("Stage12d changed off-target pre-existing QBOT")
    vals=trial.VPD_USE.to_numpy(dtype=float);qq=trial.QBOT.to_numpy(dtype=float)
    computed=(es_water(t)-vals)*100
    ref=.622*computed/(p-.378*computed)
    physical=np.isfinite(vals)&np.isfinite(qq)
    if (not np.isfinite(ref[physical]).all() or
        not np.allclose(ref[physical],qq[physical],rtol=1e-8,atol=1e-10) or
        not (qq[physical]>0).all() or
        not (qq[physical]<.08).all()):
        raise ValueError("Stage12d full-site preserved candidate QBOT closure failed: "+site)
    if (not np.isnan(vals[protected]).all() or
        not np.isnan(qq[protected]).all()):
        raise ValueError("Original Stage12b protected physical holds overwritten")

    rowmask=newable&~recoverable
    details=[]
    for i in np.flatnonzero(recoverable):
        details.append({"site":site,"native_key":keys[i],
            "VPD_F_original_QC":int(qc[i]),
            "source_companion_ERA_T_C":e_t[i],
            "source_companion_ERA_VPD_hPa":e_v[i],
            "source_companion_ERA_RH_pct":era_rh[i],
            "retained_EC_TA_C":t[i],"retained_site_PSRF_Pa":p[i],
            "new_VPD_USE_hPa":vals[i],"new_QBOT":qq[i],
            "time_shift_applied":False,"user_per_event_approved":False,
            "Postv5_approved":False})
    holdsnew=[]
    for i in np.flatnonzero(rowmask):
        holdsnew.append({"site":site,"native_key":keys[i],
            "original_QC":qc[i],
            "candidate_RH_from_companion_pct":era_rh[i],
            "source_companion_T_C":e_t[i],
            "retained_EC_TA_C":t[i],
            "hold_reason":str(reasons[i] or "PHYSICS_UNKNOWN"),
            "new_humidity_repair_approved":False})
    count_new=int(recoverable.sum())
    unfilled=int(rowmask.sum())
    missing_all=int(trial.drop(columns=["time"]).isna().any(axis=1).sum())
    total_valid=int(~trial.drop(columns=["time"]).isna().any(axis=1).sum()) if False else len(trial)-missing_all
    stats={"site":site,
        "native_rows":n,
        "prior_Stage12b_selected_RH_patches":EXPECTED_PATCH[site],
        "prior_Stage12b_science_holds_kept_NaN":int(protected.sum()),
        "Stage12c_other_missing_humidity_rows":int(newable.sum()),
        "Stage12d_new_companion_ERA_RH_auto_numeric_repairs":count_new,
        "Stage12d_remaining_other_humidity_holds":unfilled,
        "full_record_rows_with_remaining_missing":missing_all,
        "complete_finite_rows":total_valid,
        "unreviewed_official_QC0_replaced":0,
        "EC_tower_T_and_clock_changed":False,
        "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False}
    return trial,pd.DataFrame(details),pd.DataFrame(holdsnew),stats

def build():
    specs,ledger=inputs()
    outputs={};details=[];holds=[];summary=[]
    for site in SIX:
        print("SITE BUILD:",site,flush=True)
        result,paper,hold,state=one_site(site,specs[site],ledger)
        outputs[site]=result
        if len(paper):details.append(paper)
        if len(hold):holds.append(hold)
        summary.append(state)
    result=pd.DataFrame(summary)
    proof=pd.concat(details,ignore_index=True) if details else pd.DataFrame()
    unresolved=pd.concat(holds,ignore_index=True) if holds else pd.DataFrame()
    if int(result.prior_Stage12b_science_holds_kept_NaN.sum())!=233 or \
       int(result.prior_Stage12b_selected_RH_patches.sum())!=1687:
        raise ValueError("Stage12d original scientific source count changed")
    if int(result.Stage12d_new_companion_ERA_RH_auto_numeric_repairs.sum())!=len(proof):
        raise ValueError("Stage12d new numeric candidate count reconciliation failed")
    if int(result.Stage12d_remaining_other_humidity_holds.sum())!=len(unresolved):
        raise ValueError("Stage12d source holds reconciliation failed")
    return outputs,proof,unresolved,result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    flags=ap.add_mutually_exclusive_group(required=True)
    flags.add_argument("--self-test",action="store_true")
    flags.add_argument("--check",action="store_true")
    flags.add_argument("--run",action="store_true")
    mode=ap.parse_args()
    print("STAGE12D — EXACT NATIVE COMPANION ERA HUMIDITY GAP RESCUE | "+VERSION,flush=True)
    self_test()
    if mode.self_test:
        return
    output,proof,unresolved,status=build()
    print("\n========== SIX-SITE STAGE12D ADDITIONAL HUMIDITY RESCUE ==========",flush=True)
    print(status.to_string(index=False),flush=True)
    print("\n========== NEW REMAINING HUMIDITY HOLD REASONS ==========",flush=True)
    print(unresolved.groupby(["site","hold_reason"]).size().to_string() if len(unresolved) else "NONE",flush=True)
    print("\nSTAGE12D SUMMARY: source_Stage12b_RH_selected=1687 "
          "source_original_science_holds=233 "
          f"additional_humidity_gaps={int(status.Stage12c_other_missing_humidity_rows.sum())} "
          f"new_research_ERA_companion_numeric_repairs={len(proof)} "
          f"new_other_humidity_remaining={len(unresolved)} "
          f"all_sites_remaining_missing_rows={int(status.full_record_rows_with_remaining_missing.sum())} "
          "tower_temperature_changed=0 time_shifts=0 source_writes=0 "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if mode.check:
        print("CHECK ONLY: NO REPORTS, FORCING OR MODEL WRITES.",flush=True)
        return
    folder=ROOT/"science_trials"/("stage12d_six_site_companion_RH_gap_recovery_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(exist_ok=False,parents=True)
    (folder/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Six original full-native source chronologies with numerical companion ERA RH only at guarded sites. Still science HOLD.\n")
    digests={}
    for site,frame in output.items():
        name=site+"_STAGE12D_NOT_MODEL_READY_NOLEAP.csv"
        frame.to_csv(folder/name,index=False)
        reread=pd.read_csv(safe_file(folder/name),low_memory=False)
        if len(reread)!=len(frame) or list(reread)!=list(frame):
            raise ValueError("Serialized research successor schema/length mismatch")
        digests[name]=sha(folder/name)
    reports={
        "guarded_companion_ERA_RH_auto_candidate_timestamps.csv":proof,
        "remaining_other_humidity_science_holds.csv":unresolved,
        "six_site_gap_recovery_summary.csv":status}
    for name,frame in reports.items():
        frame.to_csv(folder/name,index=False)
        digests[name]=sha(folder/name)
    notes=("All Stage12c original 233 physics holds stay NaN (no overwrite). "
        "New Stage12d only applies to Stage12c additional humidity gaps "
        "whose source VPD QC is 1/2 and source companion ERA humidity "
        "and unchanged tower site T/PSRF are physically consistent, "
        "within +/-5C source ERA T, ice-saturation and local VPD jump "
        "guards. Unavailable/QC0/off-clock/bad-humidity cases remain "
        "missing; this is NOT an approved new tower RH observation, "
        "not complete forcing, and no model or DATM use is authorised.\n")
    (folder/"SCIENTIFIC_HOLD.md").write_text(notes)
    digests["SCIENTIFIC_HOLD.md"]=sha(folder/"SCIENTIFIC_HOLD.md")
    receipt={
        "version":VERSION,
        "prior_Stage12c_SHA256":sha(S12C/"stage12c_research_shadow_SHA_receipt.json"),
        "original_Stage07_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
        "six_research_successor_sites":6,"prior_1687_grid_RH_events_unchanged":True,
        "original_233_physics_holds_as_NaN":True,
        "new_companion_ERA_RH_events":int(len(proof)),
        "remaining_new_humidity_held":int(len(unresolved)),
        "site_natively_time_complete":True,
        "temperature_pressure_time_unchanged":True,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "INCOMPLETE_marker_present":True,"output_sha256":digests}
    (folder/"stage12d_research_shadow_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12D SIX-SITE SCIENCE SHADOW DIR:",folder,flush=True)
    print("NO SEALED STAGE07/12B/12C OR MODEL JOBS MODIFIED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("STAGE12D STOP:",str(e),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

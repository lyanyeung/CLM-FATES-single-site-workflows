#!/usr/bin/env python3
"""Batch03 Stage12e -- research-only alternative ERA5-Land RH rescue.

Stage12d filled 3792 of 8164 extra humidity gaps at 6 Batch03 sites,
preserving 233 earlier source/temperature/ice physics holds. Stage12e
tries the EXISTING SHA-verifiable Stage09f external ERA5-Land yearly T2m,
dewpoint and pressure products at ADDITIONAL still-missing native events
where paired source ERA fails. Grid-to-site native UTC offsets are still
hypothetical: never overwrite/change original clock, site temperature,
pressure, or existing VPD/QBOT.

Only original VPD QC1/2, previously unresolved and non-protected times
may receive automatically screened *isolated research candidate* RH.
At every case: verify source file SHA and year, interpolate T2M/D2M/SP
at native *midpoint* using original published BIF offset hypothesis;
check ERA5-Land vapour physics, site-grid temperature abs diff <=5C,
surface pressure abs diff <=15000 Pa, subfreezing water->ice RH <=100,
and calculate QBOT at unchanged original TA_USE and PSRF.
Any induced adjacent jump >4 hPa disqualifies that case. No invented
ERA5-Land series for unrequested site-years, no CDS requests.

--self-test: synthetic algebra, no disk inputs or writes.
--check: full sealed SHA science+source preflight, 6-site in-memory
         reassessment and counts, ZERO output writes.
--run: identical verification then ONE isolated SHA-receipted research
       successor with 6 entire native-time CSVs, event ledger, reason
       totals and INCOMPLETE marker. NEVER model ready or DATM.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage12e-v1-20261024-existing-yearly-ERA5Land-RH-source-rescue"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
D=ROOT/"science_trials/stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee"
B=ROOT/"science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
D_SCRIPT=BASE/"scripts/stage12/12d_native_companion_RH_bulk_gap_rescue.py"
D_BLOB="7c877c40f308ef350d6c3388af26a766911e2031"
T_SCRIPT=BASE/"scripts/stage10/10b_audit_external_humidity_1924.py"
T_BLOB="0bb3b2657c6a79c8ead68d81354f6c0b526d930a"
SITES=("US-NR3","US-Kon","US-NR1","US-MMS","US-MtB","US-Me6")
PRIOR_NEW={"US-NR3":1,"US-Kon":551,"US-NR1":699,
           "US-MMS":8,"US-MtB":2353,"US-Me6":180}
PRIOR_UNRESOLVED={"US-NR3":455,"US-Kon":717,"US-NR1":241,
                  "US-MMS":20,"US-MtB":2856,"US-Me6":83}
PRIOR_HOLDS={"US-NR3":172,"US-Kon":2,"US-NR1":57,
             "US-MMS":1,"US-MtB":1,"US-Me6":0}
EXPECTED_D_SHA_SET={
    *(f"{site}_STAGE12D_NOT_MODEL_READY_NOLEAP.csv" for site in SITES),
    "guarded_companion_ERA_RH_auto_candidate_timestamps.csv",
    "remaining_other_humidity_science_holds.csv",
    "six_site_gap_recovery_summary.csv","SCIENTIFIC_HOLD.md"
}
EXPECTED_COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS",
               "WIND","PRECTmms","TA_USE","VPD_USE"]

def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink source "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def blob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load(p,pin,name):
    if blob(p)!=pin:
        raise ValueError("Pinned upstream verified code Git blob changed: "+str(p))
    spec=importlib.util.spec_from_file_location(name,p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def es(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def e_ice(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))

def replacement(t,p,relative_humidity):
    frac=np.asarray(relative_humidity,dtype=float)/100.
    vap=es(t)*frac
    vpd=es(t)-vap
    vap_pa=vap*100.
    q=.622*vap_pa/(np.asarray(p,dtype=float)-.378*vap_pa)
    return vpd,q

def self_test():
    assert len(SITES)==6
    assert sum(PRIOR_NEW.values())==3792
    assert sum(PRIOR_UNRESOLVED.values())==4372
    assert sum(PRIOR_HOLDS.values())==233
    assert sum(PRIOR_NEW.values())+sum(PRIOR_UNRESOLVED.values())==8164
    v,q=replacement(-10.,90000.,55.)
    assert 0<v<es(-10.) and 0<q<.08 and e_ice(-10.)<es(-10.)
    assert len(EXPECTED_D_SHA_SET)==10
    print("STAGE12E SELF-TEST PASS: 6 source-site original clocks, 3792 retained repairs, 4372 extra holds, 233 immutable physics holds; NO WRITES",flush=True)

def verify():
    for directory in (ROOT,D,B,S07):
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("Missing or symlink immutable source folder: "+str(directory))
    for directory in (D,B,S07):
        regular(directory/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    receipt=json.loads(regular(D/"stage12d_research_shadow_SHA_receipt.json").read_text())
    if (receipt.get("version")!="batch03-stage12d-v1-20261024-six-site-matched-companion-RH-gap-rescue"
        or receipt.get("prior_Stage12c_SHA256") is None
        or receipt.get("original_Stage07_manifest_SHA256")!=sha(S07/"exact_input_manifest.json")
        or receipt.get("six_research_successor_sites")!=6
        or receipt.get("prior_1687_grid_RH_events_unchanged") is not True
        or receipt.get("original_233_physics_holds_as_NaN") is not True
        or receipt.get("new_companion_ERA_RH_events")!=3792
        or receipt.get("remaining_new_humidity_held")!=4372
        or receipt.get("site_natively_time_complete") is not True
        or receipt.get("temperature_pressure_time_unchanged") is not True
        or receipt.get("Postv5_approved")!=0 or receipt.get("DATM_ready")!=0
        or receipt.get("spinup_authorized")!=0
        or receipt.get("INCOMPLETE_marker_present") is not True
        or set(receipt.get("output_sha256",{}))!=EXPECTED_D_SHA_SET):
        raise ValueError("Stage12d science shadow source receipt changed")
    for name,expected in receipt["output_sha256"].items():
        if sha(D/name)!=expected:
            raise ValueError("Stage12d immutable original SHA mismatch: "+name)
    t=load(T_SCRIPT,T_BLOB,"stage10b_source_pinned_for_stage12e")
    d=load(D_SCRIPT,D_BLOB,"stage12d_source_pinned_for_stage12e")
    # Re-check original 32 yearly ERA5-Land CD S SHA receipts,
    # published BIF offset metadata, Stage07 original sources.
    joined,manifest,items,_,_=t.preflight()
    if len(items)!=32 or len(joined)!=1924 or len(manifest)!=10:
        raise ValueError("Original 32 gridded ERA5-Land years not verified")
    specs,ledger=d.inputs()
    if len(ledger)!=237:
        raise ValueError("Original 233 scientific physics holds plus US-Me2 clock source differed")
    data=pd.read_csv(regular(D/"six_site_gap_recovery_summary.csv"))
    if (len(data)!=6 or
        data.set_index("site").Stage12d_new_companion_ERA_RH_auto_numeric_repairs.to_dict()!=PRIOR_NEW or
        data.set_index("site").Stage12d_remaining_other_humidity_holds.to_dict()!=PRIOR_UNRESOLVED):
        raise ValueError("Stage12d six-site exact science status changed")
    catalog={}
    for plan,meta in items:
        site,year=plan["site"],int(plan["year"])
        if site not in SITES:continue
        catalog[(site,year)]=(plan,meta)
    return t,d,specs,ledger,catalog,receipt

def one_site(site,spec,held,catalog,stage10):
    orig=pd.read_csv(regular(D/(site+"_STAGE12D_NOT_MODEL_READY_NOLEAP.csv")),
                     low_memory=False)
    if list(orig)!=EXPECTED_COLS:
        raise ValueError("Stage12d original site schema mismatch "+site)
    raw_file=regular(spec["primary"])
    qc_col="VPD_F_QC"
    rawheader=set(pd.read_csv(raw_file,nrows=0).columns)
    if qc_col not in rawheader:
        raw=pd.read_csv(raw_file,usecols=["TIMESTAMP_START"],
                        dtype={"TIMESTAMP_START":str})
        raw[qc_col]=np.nan
    else:
        raw=pd.read_csv(raw_file,usecols=["TIMESTAMP_START",qc_col],
                        dtype={"TIMESTAMP_START":str})
    first,last,step=map(int,(spec["first_year"],spec["last_year"],spec["native_minutes"]))
    dt=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    raw=raw.loc[dt.dt.year.between(first,last)&
          ~((dt.dt.month==2)&(dt.dt.day==29))].reset_index(drop=True)
    native=pd.to_datetime(orig.time,format="%Y-%m-%d %H:%M:%S",
                          errors="raise")
    keys=native.dt.strftime("%Y%m%d%H%M").to_numpy()
    if (len(raw)!=len(orig) or
        not np.array_equal(keys,raw.TIMESTAMP_START.to_numpy()) or
        len(set(keys))!=len(keys)):
        raise ValueError("Unmatched full site source-native event clock "+site)
    index={key:i for i,key in enumerate(keys)}
    protect=np.zeros(len(orig),dtype=bool)
    for row in held.loc[held.site.eq(site)].itertuples(index=False):
        key=pd.Timestamp(row.time).strftime("%Y%m%d%H%M")
        if key not in index or protect[index[key]]:
            raise ValueError("Scientific hold original identity collision "+site)
        protect[index[key]]=True
    if int(protect.sum())!=PRIOR_HOLDS[site]:
        raise ValueError("233 original six-site scientific hold tally mismatched")
    oldv=orig.VPD_USE.to_numpy(dtype=float)
    oldq=orig.QBOT.to_numpy(dtype=float)
    if np.isfinite(oldv[protect]).any() or np.isfinite(oldq[protect]).any():
        raise ValueError("Forbidden original 233 held humidity was filled: "+site)
    qc=pd.to_numeric(raw[qc_col],errors="coerce").to_numpy(dtype=float)
    t_site=orig.TA_USE.to_numpy(dtype=float)
    p_site=orig.PSRF.to_numpy(dtype=float)
    holes=(~np.isfinite(oldv)|~np.isfinite(oldq))&~protect
    if int(holes.sum())!=PRIOR_UNRESOLVED[site]:
        raise ValueError("Previous Stage12d residual record count mismatch "+site)
    select=np.zeros(len(orig),dtype=bool)
    candidate_v=np.full(len(orig),np.nan)
    candidate_q=np.full(len(orig),np.nan)
    land_rh=np.full(len(orig),np.nan)
    land_t=np.full(len(orig),np.nan)
    land_d=np.full(len(orig),np.nan)
    year_source=np.full(len(orig),"",dtype=object)
    reasons=np.full(len(orig),"",dtype=object)
    reasons[holes]="NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR"
    for year in sorted(native[holes].dt.year.unique()):
        sub=np.flatnonzero(holes&(native.dt.year.to_numpy()==year))
        if (site,year) not in catalog:
            continue
        plan,meta=catalog[(site,year)]
        path=ROOT/"external_evidence/era5land_timeseries"/site/str(year)/meta["name"]
        if sha(path)!=meta["sha256"]:
            raise ValueError("ERA5-Land original yearly source SHA changed: "+str(path))
        loc=plan["request"]["location"]
        coords=(float(loc["latitude"]),float(loc["longitude"]))
        hours,grid,_=stage10.grid_fields(path,year,coords)
        offset=stage10.PROVISIONAL_OFFSET[site]
        # Match the SAME original native-year MIDPOINT convention
        # as Stage10b. No original source timestamps are shifted.
        utc=native.iloc[sub]+pd.Timedelta(minutes=step/2)-pd.Timedelta(hours=offset)
        land_t[sub]=stage10.interpolate(hours,grid["t2m"],utc)-273.15
        land_d[sub]=stage10.interpolate(hours,grid["d2m"],utc)-273.15
        grid_pa=stage10.interpolate(hours,grid["sp"],utc)
        rh=100*es(land_d[sub])/es(land_t[sub])
        land_rh[sub]=rh
        year_source[sub]=meta["sha256"]
        candidates=(np.isin(qc[sub],[1.,2.]) &
            np.isfinite(t_site[sub])&np.isfinite(p_site[sub]) &
            (t_site[sub]>=-80)&(t_site[sub]<=65)&
            (p_site[sub]>=50000)&(p_site[sub]<=110000))
        reasons[sub]="HOLD_ORIGINAL_SOURCE_QC_OR_TOWER_T_P"
        okgrid=(np.isfinite(land_t[sub])&np.isfinite(land_d[sub])&
            np.isfinite(grid_pa)&np.isfinite(rh)&
            (land_d[sub]<=land_t[sub]+.1)&
            (rh>0)&(rh<=100)&(grid_pa>40000)&
            (grid_pa<110000))
        reasons[sub[candidates&~okgrid]]="HOLD_ERA5LAND_GRID_PHYSICS"
        candidates&=okgrid
        tempagree=(np.abs(t_site[sub]-land_t[sub])<=5)
        passpress=(np.abs(p_site[sub]-grid_pa)<=15000)
        reasons[sub[candidates&~tempagree]]="HOLD_ERA5LAND_TOWER_T_DELTA_GT5C"
        candidates&=tempagree
        reasons[sub[candidates&~passpress]]="HOLD_ERA5LAND_SURFACE_PRESSURE_MISMATCH"
        candidates&=passpress
        with np.errstate(invalid="ignore",divide="ignore"):
            ice_rel=rh*es(t_site[sub])/e_ice(t_site[sub])
        phase=(t_site[sub]>=0)|(np.isfinite(ice_rel)&(ice_rel<=100))
        reasons[sub[candidates&~phase]]="HOLD_ICE_PHASE_WATER_RH_SUPERSATURATION"
        candidates&=phase
        vv,qq=replacement(t_site[sub],p_site[sub],rh)
        valid=(np.isfinite(vv)&np.isfinite(qq)&
               (vv>=0)&(vv<es(t_site[sub]))&(qq>0)&(qq<.08))
        reasons[sub[candidates&~valid]]="HOLD_ERA5LAND_VPD_QBOT_PHYSICS"
        candidates&=valid
        choice=sub[candidates]
        select[choice]=True
        candidate_v[choice]=vv[candidates]
        candidate_q[choice]=qq[candidates]
        reasons[choice]=""
    trial=orig.copy(deep=True)
    trial.loc[select,"VPD_USE"]=candidate_v[select]
    trial.loc[select,"QBOT"]=candidate_q[select]
    # All adjacent edges modified by source patches are inspected,
    # not merely a few visually chosen endpoints. Any new absolute
    # >4hPa jump disqualifies its newly patched endpoint; preserves old.
    for _ in range(8):
        arr=trial.VPD_USE.to_numpy(dtype=float)
        bad=np.zeros(len(arr),dtype=bool)
        for i in np.flatnonzero(select):
            for j in (i-1,i+1):
                if j<0 or j>=len(arr) or not np.isfinite(arr[j]):
                    continue
                if abs(arr[j]-arr[i])>4.0:
                    bad[i]=True
        if not bad.any():break
        select[bad]=False
        reasons[bad]="HOLD_NEW_ADJACENT_VPD_JUMP_OVER4HPA"
        trial.loc[bad,"VPD_USE"]=np.nan
        trial.loc[bad,"QBOT"]=np.nan
    else:
        raise ValueError("Unresolved Stage12e adjacent candidate jump loop")
    # All old valid humidity, all 233 original physics held rows, and
    # all non-humidity source fields must be bitwise unchanged.
    if not np.array_equal(oldv[~select],
                          trial.VPD_USE.to_numpy(dtype=float)[~select],
                          equal_nan=True):
        raise ValueError("Stage12e altered off-target earlier VPD: "+site)
    if not np.array_equal(oldq[~select],
                          trial.QBOT.to_numpy(dtype=float)[~select],
                          equal_nan=True):
        raise ValueError("Stage12e altered off-target earlier QBOT: "+site)
    for col in EXPECTED_COLS:
        if col in ("QBOT","VPD_USE"):continue
        if not orig[col].equals(trial[col]):
            raise ValueError("Forbidden EC tower T/pressure/clock/other modification: "+site+" "+col)
    vap=(es(t_site)-trial.VPD_USE.to_numpy(dtype=float))*100
    qcalc=.622*vap/(p_site-.378*vap)
    finite=np.isfinite(trial.VPD_USE.to_numpy(dtype=float)) & np.isfinite(
        trial.QBOT.to_numpy(dtype=float))
    if (not np.isfinite(qcalc[finite]).all() or
        not np.allclose(qcalc[finite],trial.QBOT.to_numpy(dtype=float)[finite],
                        rtol=1e-8,atol=1e-10)):
        raise ValueError("Final full-site water vapour/QBOT closure failed "+site)
    if int(select.sum())+int((holes&~select).sum())!=PRIOR_UNRESOLVED[site]:
        raise ValueError("Original Stage12d extra humidity hold count did not close")
    if not np.isnan(trial.VPD_USE.to_numpy(dtype=float)[protect]).all():
        raise ValueError("Original 233 science holds were overwritten")
    selected=[]
    for i in np.flatnonzero(select):
        selected.append({
          "site":site,"native_key":keys[i],"original_VPD_F_QC":int(qc[i]),
          "original_site_T_C_preserved":t_site[i],
          "original_site_PSRF_Pa_preserved":p_site[i],
          "ERA5Land_t2m_C":land_t[i],"ERA5Land_dewpoint_C":land_d[i],
          "ERA5Land_water_RH_pct":land_rh[i],
          "isolated_candidate_VPD_hPa":candidate_v[i],
          "isolated_candidate_QBOT":candidate_q[i],
          "yearly_external_SHA256":year_source[i],
          "native_source_UTC_offset_approved":False,
          "human_event_approved":False,"Postv5_approved":False})
    other=[]
    for i in np.flatnonzero(holes&~select):
        other.append({
          "site":site,"native_key":keys[i],
          "original_QC":qc[i],"site_T_C":t_site[i],
          "ERA5Land_t2m_C":land_t[i],
          "ERA5Land_dewpoint_C":land_d[i],
          "ERA5Land_RH_pct":land_rh[i],
          "science_hold_reason":str(reasons[i]),
          "production_approved":False})
    remaining=int(trial.drop(columns=["time"]).isna().any(axis=1).sum())
    state={
      "site":site,"native_rows":len(trial),
      "prior_companion_ERA_repaired_Stage12d":PRIOR_NEW[site],
      "prior_Stage12b_gridRH_patched":int({
          "US-NR3":1312,"US-Kon":227,"US-NR1":116,
          "US-MMS":17,"US-MtB":14,"US-Me6":1}[site]),
      "prior_scientific_233_holds_unchanged":int(protect.sum()),
      "other_Stage12d_remaining_humidity":int(holes.sum()),
      "new_Stage12e_grid_RH_research_repair":int(select.sum()),
      "remaining_new_humidity_hold":int((holes&~select).sum()),
      "rows_with_any_missing_after":remaining,
      "EC_tower_temperature_unchanged":True,
      "Postv5_approved":False,"DATM_ready":False,
      "spinup_authorized":False}
    return trial,pd.DataFrame(selected),pd.DataFrame(other),state

def calculate():
    stage10,stage12d,specs,ledger,year_catalog,receipt=verify()
    products={};selected=[];held=[];states=[]
    for site in SITES:
        print("STAGE12E SITE:",site,flush=True)
        out,detail,remain,stat=one_site(site,specs[site],ledger,year_catalog,stage10)
        products[site]=out;states.append(stat)
        if len(detail):selected.append(detail)
        if len(remain):held.append(remain)
    detail=pd.concat(selected,ignore_index=True) if selected else pd.DataFrame()
    remains=pd.concat(held,ignore_index=True) if held else pd.DataFrame()
    status=pd.DataFrame(states)
    if (status.prior_scientific_233_holds_unchanged.sum()!=233 or
        status.other_Stage12d_remaining_humidity.sum()!=4372 or
        status.new_Stage12e_grid_RH_research_repair.sum()!=len(detail) or
        status.remaining_new_humidity_hold.sum()!=len(remains)):
        raise ValueError("Batch03 six-site Stage12e 233+4372 source partition failed")
    return products,detail,remains,status

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    opts=ap.add_mutually_exclusive_group(required=True)
    opts.add_argument("--self-test",action="store_true")
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--run",action="store_true")
    arg=ap.parse_args()
    print("STAGE12E — VERIFIED YEARLY ERA5-LAND RH RESCUE OF POST12D GAPS | "+VERSION,flush=True)
    self_test()
    if arg.self_test:return
    output,selected,remains,status=calculate()
    print("\n========== SIX SITE ALTERNATIVE RH SOURCE SUCCESS ==========",flush=True)
    print(status.to_string(index=False),flush=True)
    print("\n========== REMAINING SECOND-SOURCE SCIENCE HOLDS ==========",flush=True)
    print(remains.groupby(["site","science_hold_reason"]).size().to_string()
          if len(remains) else "NONE",flush=True)
    print("\nSTAGE12E SUMMARY:",
      "prior_grid_RH_patches=1687 prior_native_ERA_RH_patches=3792",
      "prior_immutable_science_holds=233",
      "other_Stage12d_humidity_holds=4372",
      f"new_independent_grid_RH_candidate_patches={len(selected)}",
      f"remaining_new_humidity_holds={len(remains)}",
      f"total_rows_with_missing={int(status.rows_with_any_missing_after.sum())}",
      "EC_tower_T_pressure_native_time_changes=0",
      "new_clock_offset_approvals=0 Postv5_approved=0 DATM_ready=0 spinup=0",
      flush=True)
    if arg.check:
        print("CHECK ONLY: ZERO NEW REPORT OR FORCING WRITES.",flush=True)
        return
    out=ROOT/"science_trials"/("stage12e_six_site_verified_yearly_gridRH_shadows_"+
      datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Existing ERA5-Land year-source humidity at unchanged EC T. No clock or production science authorization.\n")
    digests={}
    for site,frame in output.items():
        name=site+"_STAGE12E_INCOMPLETE_NOLEAP.csv"
        frame.to_csv(out/name,index=False)
        if len(pd.read_csv(regular(out/name)))!=len(frame):
            raise ValueError("Serialized site model-disabled time series row count mismatch: "+site)
        digests[name]=sha(out/name)
    reports={
      "new_site_year_gridRH_repair_candidates.csv":selected,
      "remaining_4372_source_second_ERA5Land_holds.csv":remains,
      "six_site_post_stage12e_humidity_status.csv":status}
    for name,table in reports.items():
        table.to_csv(out/name,index=False)
        digests[name]=sha(out/name)
    (out/"SCIENTIFIC_HOLD.md").write_text(
        "Stage12e is a new isolated research-only successor. Stage12b/12c/12d remain fully SHA-sealed. "
        "ERA5-Land data are ERA5-driven gridded evidence at an UNAPPROVED source native-to-UTC "
        "midpoint offset hypothesis, not an independent tower sensor measurement or formal "
        "tower clock correction. It was applied only when verified yearly evidence, "
        "T and pressure compatibility, water and ice humidity, original QC1/QC2 and "
        "local boundaries permitted a numeric research candidate. 233 original physics "
        "holds and all other unresolved records remain missing. No Post-v5/DATM/spinup.\n")
    digests["SCIENTIFIC_HOLD.md"]=sha(out/"SCIENTIFIC_HOLD.md")
    receipt={
      "version":VERSION,
      "source_Stage12d_receipt_SHA256":sha(D/"stage12d_research_shadow_SHA_receipt.json"),
      "prior_1687_grid_RH_patches_unchanged":True,
      "prior_3792_native_ERA_RH_patches_unchanged":True,
      "original_233_science_holds_unchanged":True,
      "new_alternative_yearly_grid_RH_patches":int(len(selected)),
      "original_unresolved_additional":4372,
      "remaining_unresolved_additional":int(len(remains)),
      "six_full_native_ERA5Land_research_shadows":6,
      "site_T_P_time_unchanged":True,
      "source_UTC_offset_approved":False,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "INCOMPLETE_marker_present":True,
      "output_sha256":digests}
    (out/"stage12e_research_only_sha_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12E ISOLATED SIX-SITE SCIENCE DIR:",out,flush=True)
    print("NO SOURCE, STAGE12B/12C/12D, DATM, CIME OR SLURM MODIFIED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE12E STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

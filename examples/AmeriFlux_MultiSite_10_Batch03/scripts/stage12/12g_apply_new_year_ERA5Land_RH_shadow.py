#!/usr/bin/env python3
"""Stage12g: use VERIFIED new Stage12f site-year ERA5-Land evidence as RH shadow.

The existing Stage12e six-site full NOLEAP research forcing is SHA-sealed.
Stage12f newly obtains separate year/site external gridded evidence for
2,810 missing-source records (3 years / 1,038 records at first run).
Stage12g uses ONLY original Stage12e no-source half-hours for which
the newly downloaded Stage12f year/site has a checked source receipt.

- Full SHA and UTC time/CF-unit/point/physics check of each Stage12f file.
- Original source VPD_F_QC must be exactly 1 or 2 (not QC0 or unknown).
- Stage10b original BIF source UTC offsets remain HYPOTHESES, not approvals.
- Interpolate ERA5-Land hourly T2m & dewpoint to unchanged source-native
  MIDPOINT; derive water RH, then VPD/QBOT at unmodified EC TA_USE/PSRF.
- Enforce gridded T vs tower <=5 C, pressure <=15000 Pa, water RH within
  (0,100], subzero ice phase <=100%, VPD and QBOT closure.
- Reject new VPD transitions >4 hPa, including adjacent new candidates.
- Never touch 233 originally held physics events or ANY existing finite
  Stage12e humidity; no other site forcing columns may change.
- --check: source checks and complete in-memory 6-site audit, zero writes.
- --run: a NEW isolated SHA-receipted, INCOMPLETE six-site scientific trial.
  No overwrites and no DATM/CIME/Slurm/PFT/surface/postv5/spinup.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12g-v1-20261025-sha-verified-new-year-gridRH"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
E=ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
B=ROOT/"science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893"
F_SCRIPT=BASE/"scripts/stage12/12f_missing_year_ERA5Land_download_queue.py"
F_BLOB="690e9757b2e1f8536b8002c4ede43a6d9a6a2609"
E_SCRIPT=BASE/"scripts/stage12/12e_six_site_independent_ERA5Land_gap_rescue.py"
E_BLOB="cb5b38257d9a34fefc974678dadc67fe93eac9f1"
SITES=("US-NR3","US-Kon","US-NR1","US-MMS","US-MtB","US-Me6")
PRIOR_HOLD={"US-NR3":172,"US-Kon":2,"US-NR1":57,"US-MMS":1,"US-MtB":1,"US-Me6":0}
PRIOR_GAP={"US-NR3":66,"US-Kon":486,"US-NR1":180,"US-MMS":15,"US-MtB":2842,"US-Me6":81}
FIELDS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
REASON="NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR"
SOURCE_LEDGER="remaining_4372_source_second_ERA5Land_holds.csv"
def file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlinked source input: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as stream:
        for b in iter(lambda:stream.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def blob(p):
    data=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def load(path,expected,name):
    if blob(path)!=expected:
        raise ValueError("Pinned GitHub module SHA unexpectedly differs: "+str(path))
    spec=importlib.util.spec_from_file_location(name,str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def esw(celsius):
    t=np.asarray(celsius,dtype=float)
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def esi(celsius):
    t=np.asarray(celsius,dtype=float)
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))

def calculate_humidity(site_T,site_P,rh):
    frac=np.asarray(rh,dtype=float)/100.
    ea=esw(site_T)*frac
    VPD=esw(site_T)-ea
    vapor_pa=ea*100
    QBOT=0.622*vapor_pa/(np.asarray(site_P,dtype=float)-0.378*vapor_pa)
    return VPD,QBOT

def self_test():
    assert len(SITES)==6 and sum(PRIOR_HOLD.values())==233
    assert sum(PRIOR_GAP.values())==3670
    t=-9.;p=90000.;rh=44.
    v,q=calculate_humidity(t,p,rh)
    assert 0<v<esw(t) and 0<q<.08 and esi(t)<esw(t)
    assert len(FIELDS)==10
    assert REASON=="NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR"
    assert (408+328+302)==1038
    assert 2810-1038==1772
    print("STAGE12G SELF-TEST PASS: 6 site source clocks, 233 immutable science holds, fixed tower T/P and water/ice RH/QBOT formulas; NO WRITES",flush=True)

def sources():
    if not E.is_dir() or E.is_symlink() or not B.is_dir() or B.is_symlink():
        raise ValueError("Missing verified Stage12e or Stage12b source trial")
    for p in (E/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP",
              B/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"):
        file(p)
    f=load(F_SCRIPT,F_BLOB,"source_stage12f_12g")
    e=load(E_SCRIPT,E_BLOB,"source_stage12e_12g")
    # First checks original seven-site SHA-pinned 32 source-years and
    # Stage12e's SHA of every single pre-existing six-site source file.
    original_plan,stage10,pilot,receipte=f.evidence()
    _,_,specs,original_holds,_,receipt=e.verify()
    all_holds=pd.read_csv(file(E/SOURCE_LEDGER),dtype={"site":str,"native_key":str})
    if (len(all_holds)!=3670 or
        all_holds.duplicated(["site","native_key"]).any()
        or set(all_holds.site)!=set(SITES)):
        raise ValueError("Stage12e remaining 3670 source-native event IDs differ")
    missing=all_holds.loc[all_holds.science_hold_reason.eq(REASON)].copy()
    if len(missing)!=2810:
        raise ValueError("Missing 2810 Stage12f source-backed humidity targets")
    missing["year"]=pd.to_datetime(missing.native_key,format="%Y%m%d%H%M",
                                    errors="raise").dt.year
    counts=missing.groupby(["site","year"]).size()
    if sum(x["unresolved_humidity"] for x in original_plan)!=2810:
        raise ValueError("Stage12f missing-original-year plan differs")
    catalog={}
    missing_inventory=[]
    for request in original_plan:
        site,year=request["site"],int(request["year"])
        if int(counts.get((site,year),0))!=int(request["unresolved_humidity"]):
            raise ValueError("Original Stage12e/source-year event identity mismatch "+str((site,year)))
        status,metadata=f.status(request,stage10)
        if status=="VERIFIED":
            catalog[(site,year)]=(request,metadata)
        elif status=="MISSING":
            missing_inventory.append(request)
        else:
            raise ValueError("Unexpected Stage12f source status "+str(status))
    if not catalog:
        raise ValueError("No Stage12f source-years verified; run Stage12f downloads first")
    if sum(int(counts.get((s,y),0)) for s,y in catalog)>2810:
        raise ValueError("Selected source site-year count exceeds source-review population")
    if (not set(catalog).isdisjoint({(x["site"],x["year"]) for x in missing_inventory})
        or len(catalog)+len(missing_inventory)!=len(original_plan)):
        raise ValueError("Source downloaded/missing year partition inconsistent")
    return stage10,specs,original_holds,missing,catalog,missing_inventory

def site_original_qc(site,spec,shadow):
    raw=file(spec["primary"])
    header=pd.read_csv(raw,nrows=0).columns
    if not {"TIMESTAMP_START","VPD_F"}<=set(header):
        raise ValueError("Original FLUXMET VPD source QC fields absent "+site)
    cols=["TIMESTAMP_START"]+(["VPD_F_QC"] if "VPD_F_QC" in header else [])
    df=pd.read_csv(raw,usecols=cols,dtype={"TIMESTAMP_START":str},low_memory=False)
    if "VPD_F_QC" not in df:df["VPD_F_QC"]=np.nan
    dt=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    first,last=int(spec["first_year"]),int(spec["last_year"])
    mask=dt.dt.year.between(first,last)&~((dt.dt.month==2)&(dt.dt.day==29))
    df=df.loc[mask].reset_index(drop=True)
    keys=pd.to_datetime(shadow.time,format="%Y-%m-%d %H:%M:%S",
                        errors="raise").dt.strftime("%Y%m%d%H%M").to_numpy()
    if len(df)!=len(shadow) or not np.array_equal(df.TIMESTAMP_START.to_numpy(),keys):
        raise ValueError("Exact original native timestamps differ from Stage12e source "+site)
    return keys,pd.to_numeric(df.VPD_F_QC,errors="coerce").to_numpy(dtype=float)

def one(site,spec,held,missing,catalog,stage10):
    orig=pd.read_csv(file(E/(site+"_STAGE12E_INCOMPLETE_NOLEAP.csv")),
                     low_memory=False)
    if list(orig.columns)!=FIELDS:
        raise ValueError("Stage12e original site columns changed: "+site)
    keys,qc=site_original_qc(site,spec,orig)
    if len(keys)!=len(set(keys)):
        raise ValueError("Duplicate site native source time "+site)
    index={k:i for i,k in enumerate(keys)}
    protected=np.zeros(len(orig),dtype=bool)
    for event in held.loc[held.site.eq(site)].itertuples(index=False):
        native=pd.Timestamp(event.time).strftime("%Y%m%d%H%M")
        if native not in index or protected[index[native]]:
            raise ValueError("Missing or duplicated immutable physics hold "+site+" "+native)
        protected[index[native]]=True
    if int(protected.sum())!=PRIOR_HOLD[site]:
        raise ValueError("Original source 233 physics hold count changed "+site)
    oldv=orig.VPD_USE.to_numpy(dtype=float)
    oldq=orig.QBOT.to_numpy(dtype=float)
    if np.isfinite(oldv[protected]).any() or np.isfinite(oldq[protected]).any():
        raise ValueError("Protected source physics hold previously overwritten "+site)
    t=orig.TA_USE.to_numpy(dtype=float)
    p=orig.PSRF.to_numpy(dtype=float)
    pending=missing.loc[missing.site.eq(site)]
    if len(pending)!=({"US-NR3":6,"US-Kon":211,"US-NR1":135,
                      "US-MMS":15,"US-MtB":2363,"US-Me6":80}[site]):
        raise ValueError("Source-native Stage12e missing-year target counts changed "+site)
    status=np.full(len(orig),"",dtype=object)
    requested=np.zeros(len(orig),dtype=bool)
    selected=np.zeros(len(orig),dtype=bool)
    newv=np.full(len(orig),np.nan)
    newq=np.full(len(orig),np.nan)
    rh=np.full(len(orig),np.nan)
    tgrid=np.full(len(orig),np.nan)
    dgrid=np.full(len(orig),np.nan)
    grid_p=np.full(len(orig),np.nan)
    src_sha=np.full(len(orig),"",dtype=object)
    for row in pending.itertuples(index=False):
        native=row.native_key
        if native not in index:
            raise ValueError("Missing Stage12e pending native time in source "+site+" "+native)
        i=index[native]
        if requested[i]:
            raise ValueError("Duplicate Stage12g source target native ID")
        requested[i]=True
        if (np.isfinite(oldv[i]) or np.isfinite(oldq[i]) or protected[i]):
            raise ValueError("Stage12g intends to modify original existing finite/held forcing "+site+" "+native)
        status[i]="MISSING_VERIFIED_STAGE12F_SOURCE_YEAR"
    date=pd.to_datetime(orig.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    step=int(spec["native_minutes"])
    if step!=(60 if site=="US-MMS" else 30):
        raise ValueError("Original source-native step changed")
    for year in sorted(date.dt.year[requested].unique()):
        target=np.flatnonzero(requested&(date.dt.year.to_numpy()==year))
        if (site,int(year)) not in catalog:continue
        plan,metadata=catalog[(site,int(year))]
        gridfile=file(metadata["path"])
        if sha(gridfile)!=metadata["sha256"]:
            raise ValueError("Stage12f external year data SHA changed during run")
        loc=plan["request"]["location"]
        dt,fields,coord=stage10.grid_fields(
            gridfile,int(year),(float(loc["latitude"]),float(loc["longitude"])))
        # Stage10b grid/native midpoint join. This is an explicitly
        # unapproved published source UTC offset hypothesis.
        offset=stage10.BIF_OFFSET[site]
        utc=date.iloc[target]+pd.Timedelta(minutes=step/2)-pd.Timedelta(hours=offset)
        tgrid[target]=stage10.interpolate(dt,fields["t2m"],utc)-273.15
        dgrid[target]=stage10.interpolate(dt,fields["d2m"],utc)-273.15
        grid_p[target]=stage10.interpolate(dt,fields["sp"],utc)
        with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
            rh[target]=100*esw(dgrid[target])/esw(tgrid[target])
        src_sha[target]=metadata["sha256"]
        validqc=np.isin(qc[target],[1.,2.])
        siteok=np.isfinite(t[target])&np.isfinite(p[target])&(
            (t[target]>=-80)&(t[target]<=65)&(p[target]>=50000)&(p[target]<=110000))
        gridok=(np.isfinite(tgrid[target])&np.isfinite(dgrid[target])&
            np.isfinite(grid_p[target])&np.isfinite(rh[target])&
            (dgrid[target]<=tgrid[target]+.1)&(rh[target]>0)&
            (rh[target]<=100)&(grid_p[target]>=50000)&(grid_p[target]<=110000))
        taok=np.abs(t[target]-tgrid[target])<=5.
        paok=np.abs(p[target]-grid_p[target])<=15000.
        with np.errstate(divide="ignore",invalid="ignore"):
            icefrac=rh[target]*esw(t[target])/esi(t[target])
        iceok=(t[target]>=0)|(np.isfinite(icefrac)&(icefrac<=100.))
        vv,qq=calculate_humidity(t[target],p[target],rh[target])
        finalok=(np.isfinite(vv)&np.isfinite(qq)&(vv>=0)&(vv<esw(t[target]))&
                 (qq>0)&(qq<.08))
        eligible=validqc&siteok&gridok&taok&paok&iceok&finalok
        status[target]="HOLD_ORIGINAL_QC_OR_SITE_T_P"
        status[target[validqc&siteok&~gridok]]="HOLD_STAGE12F_GRID_TD_SP_PHYSICS"
        status[target[validqc&siteok&gridok&~taok]]="HOLD_SITE_GRID_T_DIFF_GT5C"
        status[target[validqc&siteok&gridok&taok&~paok]]="HOLD_PRESSURE_DIFF_GT15000PA"
        status[target[validqc&siteok&gridok&taok&paok&~iceok]]="HOLD_ICE_SUPERSATURATION"
        status[target[validqc&siteok&gridok&taok&paok&iceok&~finalok]]="HOLD_VPD_QBOT_PHYSICS"
        good=target[eligible]
        status[good]=""
        selected[good]=True
        newv[good]=vv[eligible]
        newq[good]=qq[eligible]
    trial=orig.copy(deep=True)
    trial.loc[selected,"VPD_USE"]=newv[selected]
    trial.loc[selected,"QBOT"]=newq[selected]
    # For all new candidate edges, reject both end-points of a
    # candidate pair when they jointly form an excessive new jump.
    for _ in range(10):
        v=trial.VPD_USE.to_numpy(dtype=float)
        reject=np.zeros(len(v),dtype=bool)
        for i in np.flatnonzero(selected):
            for j in (i-1,i+1):
                if 0<=j<len(v) and np.isfinite(v[j]) and abs(v[i]-v[j])>4.:
                    reject[i]=True
        if not reject.any():break
        selected[reject]=False
        status[reject]="HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"
        trial.loc[reject,"VPD_USE"]=np.nan
        trial.loc[reject,"QBOT"]=np.nan
    else:
        raise ValueError("Stage12g adjacent VPD jump guard not converged")
    for column in FIELDS:
        if column not in ("VPD_USE","QBOT") and not orig[column].equals(trial[column]):
            raise ValueError("EC tower TA, time, pressure or other forcing changed "+site+":"+column)
    for col in ("VPD_USE","QBOT"):
        if not np.array_equal(orig[col].to_numpy(dtype=float)[~selected],
                              trial[col].to_numpy(dtype=float)[~selected],equal_nan=True):
            raise ValueError("Existing Stage12e humidity value edited outside new mask "+col)
    if not np.isnan(trial.QBOT.to_numpy(dtype=float)[protected]).all() or \
       not np.isnan(trial.VPD_USE.to_numpy(dtype=float)[protected]).all():
        raise ValueError("Original Stage12b scientific humidity held record filled")
    actual=trial.VPD_USE.to_numpy(dtype=float)
    q=trial.QBOT.to_numpy(dtype=float)
    ea=100*(esw(t)-actual)
    qb=.622*ea/(p-.378*ea)
    finite=np.isfinite(actual)&np.isfinite(q)
    if (not np.isfinite(qb[finite]).all() or
        not np.allclose(qb[finite],q[finite],rtol=1e-8,atol=1e-10) or
        not (q[finite]>0).all() or not (q[finite]<.08).all()):
        raise ValueError("Stage12g final entire site QBOT physics failed "+site)
    cover=int((requested & (status!="MISSING_VERIFIED_STAGE12F_SOURCE_YEAR")).sum())
    added=int(selected.sum())
    pending_missing=int((requested & (status=="MISSING_VERIFIED_STAGE12F_SOURCE_YEAR")).sum())
    previously_unrelated=PRIOR_GAP[site]-int(requested.sum())
    if int(requested.sum())!=( {"US-NR3":6,"US-Kon":211,"US-NR1":135,
                                "US-MMS":15,"US-MtB":2363,"US-Me6":80}[site]):
        raise ValueError("Stage12g site source year total mismatched")
    repairs=[]
    for i in np.flatnonzero(selected):
        repairs.append({
            "site":site,"native_key":keys[i],
            "source_VPD_F_QC":int(qc[i]),
            "original_EC_TA_C":t[i],"original_EC_PSRF_Pa":p[i],
            "ERA5Land_T2M_C":tgrid[i],"ERA5Land_DEW2M_C":dgrid[i],
            "ERA5Land_SPRF_Pa":grid_p[i],"ERA5Land_water_RH_pct":rh[i],
            "candidate_VPD_hPa":newv[i],"candidate_QBOT_kgkg":newq[i],
            "SHA_verified_new_ERA5Land_year_source":src_sha[i],
            "original_source_native_UTC_offset_hypothesis":int(stage10.BIF_OFFSET[site]),
            "UTC_clock_approved":False,"Postv5_approved":False})
    holds=[]
    for i in np.flatnonzero(requested &~selected):
        holds.append({"site":site,"native_key":keys[i],"QC_VPD_F":qc[i],
          "grid_T2M_C":tgrid[i],"original_tower_T_C":t[i],
          "grid_water_RH_pct":rh[i],"reason":str(status[i]),
          "scientific_production_approved":False})
    rows_missing=int(trial.drop(columns=["time"]).isna().any(axis=1).sum())
    return trial,pd.DataFrame(repairs),pd.DataFrame(holds),{
        "site":site,"year_source_missing_original_total":int(requested.sum()),
        "new_site_year_verified_event_coverage":cover,
        "new_humidity_only_numeric_research_repairs":added,
        "site_years_still_without_external_evidence":pending_missing,
        "new_downloaded_year_humidity_holds":cover-added,
        "original_other_unrelated_humidity_holds":previously_unrelated,
        "original_233_phys_science_holds_unchanged":int(protected.sum()),
        "total_rows_with_some_missing_after":rows_missing,
        "original_EC_T_P_time_unchanged":True,
        "model_ready":False,
        "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False
    }

def calculate():
    stage10,specs,original_held,missing,catalog,miss_inventory=sources()
    frames={}; repaired=[]; unrepaired=[]; stats=[]
    for site in SITES:
        print("STAGE12G SITE:",site,flush=True)
        frame,ok,held,state=one(site,specs[site],original_held,missing,catalog,stage10)
        frames[site]=frame
        if len(ok):repaired.append(ok)
        if len(held):unrepaired.append(held)
        stats.append(state)
    success=pd.concat(repaired,ignore_index=True) if repaired else pd.DataFrame()
    held=pd.concat(unrepaired,ignore_index=True) if unrepaired else pd.DataFrame()
    stats=pd.DataFrame(stats)
    if (stats.year_source_missing_original_total.sum()!=2810 or
        stats.original_233_phys_science_holds_unchanged.sum()!=233 or
        stats.new_humidity_only_numeric_research_repairs.sum()!=len(success) or
        stats.new_site_year_verified_event_coverage.sum()!=
          (sum(x["unresolved_humidity"] for (x,_) in catalog.values()))):
        raise ValueError("Stage12g new-source/readiness event counts disagree")
    if (stats.new_downloaded_year_humidity_holds.sum()+
        stats.new_humidity_only_numeric_research_repairs.sum()+
        stats.site_years_still_without_external_evidence.sum()!=2810 or
        len(held)+len(success)!=2810):
        raise ValueError("Stage12g full source-native 2810 holds and changed events did not reconcile")
    return frames,success,held,stats,catalog

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--check",action="store_true")
    group.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12G — NEW STAGE12F YEARLY ERA5-LAND RH SOURCE-ONLY SHADOW | "+VERSION,flush=True)
    self_test()
    if args.self_test:return
    frames,success,held,stats,catalog=calculate()
    print("\n========== SIX SITE SOURCE AND HUMIDITY REPAIR STATUS ==========",flush=True)
    print(stats.to_string(index=False),flush=True)
    print("\n========== UNRESOLVED SOURCE-YEAR / SCIENCE HOLDS ==========",flush=True)
    print(held.groupby(["site","reason"]).size().to_string() if len(held) else "NONE",flush=True)
    print("\nSTAGE12G SUMMARY:",
        f"new_source_site_years_verified={len(catalog)}",
        f"new_source_native_event_coverage={int(stats.new_site_year_verified_event_coverage.sum())}",
        f"new_ERA5Land_RH_only_research_repairs={len(success)}",
        f"new_source_year_physics_QC_holds={int(stats.new_downloaded_year_humidity_holds.sum())}",
        f"still_missing_external_source_year_rows={int(stats.site_years_still_without_external_evidence.sum())}",
        f"full_six_site_rows_with_missing_any_field={int(stats.total_rows_with_some_missing_after.sum())}",
        "old_233_science_holds_preserved=TRUE",
        "original_tower_T_P_clock_unchanged=TRUE",
        "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: ZERO NEW REPORT OR FORCING WRITES.",flush=True)
        return
    out=ROOT/"science_trials"/("stage12g_six_site_new_year_gridRH_science_"+
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage12g numerical humidity shadow only: 233 physics holds, uncertain clock, no model authorisation.\n")
    outputs={}
    for site,frame in frames.items():
        filename=site+"_STAGE12G_INCOMPLETE_NOLEAP.csv"
        frame.to_csv(out/filename,index=False)
        reread=pd.read_csv(file(out/filename))
        if len(reread)!=len(frame) or list(reread)!=list(frame):
            raise ValueError("Stage12g serialised NOLEAP shadow row/schema differed "+site)
        outputs[filename]=sha(out/filename)
    reports={
        "new_ERA5Land_year_source_RH_repair_candidates.csv":success,
        "2810_original_missing_year_source_review_after_stage12g.csv":held,
        "six_site_stage12g_science_status.csv":stats,
    }
    for filename,data in reports.items():
        data.to_csv(out/filename,index=False)
        outputs[filename]=sha(out/filename)
    note=("Stage12g source/forcing science hold. Exact Stage12e site and source SHA "
          "preserved; only previously missing ERA5-Land year evidence from "
          "Stage12f permitted new humidity-only research candidates at "
          "original EC tower TA and site PSRF without changing clock. "
          "No QC0 or unknown VPD source, no original 233 science holds, "
          "no invalid ERA5-Land physics, water/ice inconsistencies, "
          "tower-grid temperature >5C or pressure >15000 Pa, and no "
          "new >4 hPa neighbouring jumps may enter research shadow. "
          "Native time-to-UTC offsets are still unapproved hypotheses, "
          "and ERA5-driven gridded source is not tower truth. "
          "Not a Post-v5/DATM/CIME/Slurm/spinup-ready forcing.\n")
    (out/"SCIENTIFIC_HOLD.md").write_text(note)
    outputs["SCIENTIFIC_HOLD.md"]=sha(out/"SCIENTIFIC_HOLD.md")
    provenance={site+":"+str(year):{
        "source_file":meta["path"],"original_source_sha256":meta["sha256"],
        "unresolved_Stage12e_records":int(plan["unresolved_humidity"])
    } for (site,year),(plan,meta) in sorted(catalog.items())}
    (out/"new_external_ERA5Land_SHA_manifest.json").write_text(
        json.dumps(provenance,indent=2)+"\n")
    outputs["new_external_ERA5Land_SHA_manifest.json"]=sha(out/"new_external_ERA5Land_SHA_manifest.json")
    receipt={
        "version":VERSION,
        "pinned_Stage12e_SHA256":sha(E/"stage12e_research_only_sha_receipt.json"),
        "source_Stage12f_script_Git_blob":F_BLOB,
        "new_sha_verified_source_site_years":len(catalog),
        "new_covered_original_missing_year_events":int(stats.new_site_year_verified_event_coverage.sum()),
        "new_numerical_ERA5Land_RH_only_research_repairs":len(success),
        "original_233_physics_holds_untouched":True,
        "original_six_site_T_P_native_clock_unchanged":True,
        "all_original_Stage12e_finite_humidity_untouched":True,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "INCOMPLETE_marker_present":True,"output_sha256":outputs}
    (out/"stage12g_research_only_sha_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12G SIX-SITE SCIENCE SHADOW DIR:",out,flush=True)
    print("NO SOURCE OR PREVIOUS STAGE12B/12C/12D/12E, CIME, DATM, OR SLURM MODIFICATIONS.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as err:
        print("STAGE12G STOP:",str(err),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

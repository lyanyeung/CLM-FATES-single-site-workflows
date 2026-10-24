#!/usr/bin/env python3
"""Stage12c — six-site full NO_LEAP chronology with Stage12b RH-only numeric patches.

This creates six complete *TIME-INDEXED* (NOT MODEL-READY) research shadow CSVs
from Stage07 SHA-pinned original FLUXMET and standalone site ERA companions.
- No good observed TA_F is ever replaced: 1687 Stage12b RH cases transfer
  ERA5-Land gridded RH at verified original TA and site pressure.
- Non-humidity source gaps use exact-time companion ERA values only when
  physically valid; every such non-tower fallback is recorded separately.
- All 233 science physics/ice/temperature holds (and US-Me2's four
  clock holds, EXCLUDED as a site) remain unpatched.
- Held humidity rows are explicitly NaN VPD_USE/QBOT, not silent or
  visually plausible unapproved values. Other unphysical source humidity
  and other forcing gaps are also flagged, never fabricated.
- All 1687 patch timestamps matched, full forcing years checked; physical
  closure, complete native chronology, and affected-boundary jumps reported.
- No archived Stage07, Stage11h/l/q, source data, DATM, CIME, Slurm changes.

--self-test formula/calendar/guard only, no input/writes
--check full six-site in-memory build + source SHA gates, NO writes
--run same checks then NEW, SHA-receipted science_trial with six time-complete
      INCOMPLETE research shadows, valid-data masks and scientific hold ledgers.
No production acceptance is granted by program success.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage12c-v1-20261024-six-time-complete-science-hold-shadows"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
SOURCE=BASE/"scripts/stage11/11a_science_decision_matrix.py"
SOURCE_BLOB="a83de59a907179429c1747977c1043ae01f9a7cf"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
B=ROOT/"science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893"
SIX=("US-NR3","US-Kon","US-NR1","US-MMS","US-MtB","US-Me6")
COUNTS={"US-NR3":1312,"US-Kon":227,"US-NR1":116,
        "US-MMS":17,"US-MtB":14,"US-Me6":1}
HOLD_COUNTS={"US-NR3":172,"US-Kon":2,"US-NR1":57,
             "US-MMS":1,"US-MtB":1,"US-Me6":0,"US-Me2":4}
FIELDS=("TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
ERAFIELDS={name:name.removesuffix("_F")+"_ERA" for name in FIELDS}
HARD={"TA_F":(-80.,65.),"VPD_F":(0.,125.),"PA_F":(50.,110.),
      "SW_IN_F":(-5.,1600.),"LW_IN_F":(60.,800.),
      "WS_F":(-.1,75.),"P_F":(-.001,300.)}
COLUMNS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
B_FILES={"six_site_humidity_only_event_patch_candidates.csv",
         "seven_site_science_holds_including_US-Me2.csv",
         "seven_site_patch_and_hold_counts.csv","SCIENTIFIC_HOLD.md"}

def file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlink immutable input: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def blob(p):
    b=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def numeric(series):
    x=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    x[(~np.isfinite(x))|(x<=-9990)]=np.nan
    return x

def sat(ta):
    t=np.asarray(ta,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def qbot(t,v,p):
    ea=100*(sat(t)-v)
    with np.errstate(divide="ignore",invalid="ignore"):
        return .622*ea/(p-.378*ea)

def load_stage11a():
    if blob(SOURCE)!=SOURCE_BLOB:
        raise ValueError("Pinned Stage11a verified source Git blob differs")
    spec=importlib.util.spec_from_file_location("batch03_stage12c_11a",SOURCE)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def preflight():
    if not B.is_dir() or B.is_symlink():
        raise ValueError("Missing Stage12b isolated patch candidate directory")
    file(B/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    b=json.loads(file(B/"stage12b_numeric_candidate_receipt.json").read_text())
    if (b.get("version")!="batch03-stage12b-v1-20261024-six-site-bulk-humidity-numeric-patch"
        or b.get("original_source_total")!=1924
        or b.get("numeric_bulk_candidate_rows")!=1687
        or b.get("original_science_physics_holds")!=233
        or b.get("original_source_clock_holds")!=4
        or b.get("additional_math_holds")!=0
        or b.get("not_complete_site_forcing") is not True
        or b.get("ec_tower_T_and_P_preserved") is not True
        or b.get("ERA5Land_time_offset_approved") is not False
        or b.get("Postv5_approved")!=0 or b.get("DATM_ready")!=0
        or b.get("spinup_authorized")!=0
        or b.get("INCOMPLETE_marker_present") is not True
        or set(b.get("output_sha256",{}))!=B_FILES):
        raise ValueError("Stage12b original source patch SHA receipt policy mismatch")
    for name,dig in b["output_sha256"].items():
        if sha(B/name)!=dig: raise ValueError("Stage12b sealed source content differs: "+name)
    a=load_stage11a()
    d,h,k,pins=a.preflight()   # Verifies SHA for original Stage07 ten-site manifest and 20 raw sources
    events,years,batch=a.analyze(d,h,k)
    if len(events)!=1924 or len(years)!=32 or len(batch)!=10:
        raise ValueError("Stage11a 10-site source scientific gate differs")
    if b.get("original_source_evidence_SHA256")!=pins:
        raise ValueError("Stage12b root source SHA inputs differ from Stage11a")
    manifest=json.loads(file(S07/"exact_input_manifest.json").read_text())
    choices={r["site"]:r for r in manifest["sites"]}
    if len(choices)!=10 or not set(SIX)<set(choices):
        raise ValueError("Stage07 source inventory site mismatch")
    repairs=pd.read_csv(file(B/"six_site_humidity_only_event_patch_candidates.csv"),
                        dtype={"site":str,"exact_source_native_timestamp":str,
                               "source_csv_row":str},low_memory=False)
    holds=pd.read_csv(file(B/"seven_site_science_holds_including_US-Me2.csv"),
                      dtype={"site":str,"source_csv_row":str},low_memory=False)
    if (len(repairs)!=1687 or len(holds)!=237
        or repairs.site.value_counts().to_dict()!=COUNTS
        or holds.site.value_counts().to_dict()!={k:v for k,v in HOLD_COUNTS.items() if v}
        or repairs.duplicated(["site","exact_source_native_timestamp"]).any()
        or repairs.model_air_temperature_modification.astype(str).str.lower().eq("true").any()
        or repairs.assumed_UTC_offset_approved.astype(str).str.lower().eq("true").any()
        or repairs.patch_status.ne("AUTO_NUMERIC_RESEARCH_CANDIDATE_NO_FORCING_WRITE").any()):
        raise ValueError("Stage12b exact candidate/held event inventory changed")
    patches_key=set(zip(repairs.site,repairs.time))
    hold_key=set(zip(holds.site,holds.time))
    if patches_key & hold_key or len(patches_key|hold_key)!=1924:
        raise ValueError("Stage12b candidates and held original source key overlap")
    return choices,repairs,holds,manifest

def read_native(site,info):
    first,last,step=int(info["first_year"]),int(info["last_year"]),int(info["native_minutes"])
    if step!=(60 if site=="US-MMS" else 30):
        raise ValueError("Site original timestamp resolution differs: "+site)
    raw_file=file(info["primary"]);era_file=file(info["era"])
    rawcols=["TIMESTAMP_START",*FIELDS]
    eracols=["TIMESTAMP_START",*ERAFIELDS.values()]
    if not set(rawcols)<=set(pd.read_csv(raw_file,nrows=0).columns):
        raise ValueError("Missing official source FLUXMET columns: "+site)
    if not set(eracols)<=set(pd.read_csv(era_file,nrows=0).columns):
        raise ValueError("Missing companion ERA fields: "+site)
    primary=pd.read_csv(raw_file,usecols=rawcols,dtype={"TIMESTAMP_START":str},low_memory=False)
    external=pd.read_csv(era_file,usecols=eracols,dtype={"TIMESTAMP_START":str},low_memory=False)
    def select(data):
        t=pd.to_datetime(data.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        good=t.dt.year.between(first,last)&~((t.dt.month==2)&(t.dt.day==29))
        data=data.loc[good].copy()
        data["native"]=pd.to_datetime(data.TIMESTAMP_START,format="%Y%m%d%H%M")
        data=data.sort_values("native").reset_index(drop=True)
        if data.native.duplicated().any():raise ValueError("Source native timestamp duplicated: "+site)
        return data
    primary=select(primary)
    external=select(external)
    expected=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
            freq=f"{step}min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if (len(primary)!=len(expected) or len(external)!=len(expected)
        or not np.array_equal(primary.native.to_numpy(),expected.to_numpy())
        or not np.array_equal(external.native.to_numpy(),expected.to_numpy())):
        raise ValueError("Exact-time FLUXMET+ERA full source NO_LEAP coverage incomplete: "+site)
    return primary,external,first,last,step

def process_site(site,info,sitepatch,sitehold):
    p,e,first,last,step=read_native(site,info)
    n=len(p)
    native=p.TIMESTAMP_START.to_numpy(dtype=str)
    ix={key:i for i,key in enumerate(native)}
    if len(ix)!=n:raise ValueError("Source native key collisions")
    values={};fall={}
    # Reconstruct base *from verified immutable raw source*,
    # only fallback on MISSING/physically impossible non-humidity source.
    # Original TA_F is NEVER replaced if it is a finite in-range tower input.
    for name in FIELDS:
        current=numeric(p[name]); back=numeric(e[ERAFIELDS[name]])
        low,high=HARD[name]
        sourcegood=np.isfinite(current)&(current>=low)&(current<=high)
        eragood=np.isfinite(back)&(back>=low)&(back<=high)
        baseline=current.copy()
        use_fallback=~sourcegood&eragood
        baseline[~sourcegood]=np.nan
        baseline[use_fallback]=back[use_fallback]
        # Historical tiny negative near rounding corrections, explicit:
        tiny=(np.isfinite(baseline)&(baseline<0)&(
            ((name=="SW_IN_F")&(baseline>=-5.))|
            ((name=="WS_F")&(baseline>=-.1))|
            ((name=="P_F")&(baseline>=-.001))))
        baseline[tiny]=0.
        values[name]=baseline
        fall[name]=use_fallback
    # VPD source/ERA companion may be mutually thermodynamically
    # inconsistent in cold periods; never silently clip negative EA.
    # Preserve these as review holes unless one of 1687 pinned RH events.
    temperature=values["TA_F"]
    pressure=values["PA_F"]*1000.
    vpd=values["VPD_F"].copy()
    es=sat(temperature)
    sourcehumidity=(np.isfinite(temperature)&np.isfinite(vpd)&
                    np.isfinite(pressure)&(pressure>49000)&
                    (vpd>=0)&(vpd<es))
    vpd[~sourcehumidity]=np.nan
    repairmask=np.zeros(n,dtype=bool)
    holdmask=np.zeros(n,dtype=bool)
    evidence=[]
    for r in sitepatch.itertuples(index=False):
        key=r.exact_source_native_timestamp
        if key not in ix:raise ValueError("Patch timestamp missing from original "+site+" "+key)
        i=ix[key]
        if repairmask[i]:raise ValueError("Duplicate selected source timestamp")
        # Stage12b source TA/P must match EXACT source-native FLUXMET at
        # target; never use/overwrite time-shifted ERA temperature.
        orig_t=numeric(pd.Series([p.TA_F.iloc[i]]))[0]
        orig_p=numeric(pd.Series([p.PA_F.iloc[i]]))[0]*1000
        if (not np.isfinite([orig_t,orig_p]).all() or
            not np.isclose(orig_t,float(r.EC_tower_TA_C_preserved),atol=1e-7) or
            not np.isclose(orig_p,float(r.EC_tower_PSRF_Pa_preserved),atol=1e-4) or
            fall["TA_F"][i] or fall["PA_F"][i]):
            raise ValueError("Stage12b patch T/P not equal untouched original tower input: "+site+" "+key)
        rh=float(r.research_ERA5Land_grid_RH_pct)
        candidate=es[i]*(1-rh/100)
        candidate_q=qbot(orig_t,candidate,orig_p)
        if (not 0<rh<=100 or
            not np.isfinite([candidate,candidate_q]).all()
            or not np.isclose(candidate,float(r.humidity_only_candidate_VPD_hPa),
                              atol=1e-7,rtol=1e-7) or
            not np.isclose(candidate_q,float(r.humidity_only_candidate_QBOT_kgkg),
                           atol=1e-9,rtol=1e-7) or
            not 0<=candidate<es[i]):
            raise ValueError("Pinned Stage12b candidate VPD/QBOT physics changed: "+site+" "+key)
        vpd[i]=candidate
        repairmask[i]=True
        evidence.append({"site":site,"native_key":key,"source_csv_row":r.source_csv_row,
            "source_ERA5Land_RH_pct":rh,"retained_site_TA_C":orig_t,
            "site_pressure_Pa":orig_p,"corrected_VPD_hPa":candidate,
            "corrected_QBOT_kgkg":candidate_q,
            "clock_approved":False,"postv5_approved":False})
    for r in sitehold.itertuples(index=False):
        key=pd.Timestamp(r.time).strftime("%Y%m%d%H%M")
        if key not in ix:raise ValueError("Held source timestamp absent: "+site+" "+key)
        i=ix[key]
        if repairmask[i] or holdmask[i]:raise ValueError("Held/patch timestamp overlap")
        holdmask[i]=True
        # Explicit missing humidity at unresolved physically held times.
        vpd[i]=np.nan
    if int(repairmask.sum())!=COUNTS[site] or int(holdmask.sum())!=HOLD_COUNTS[site]:
        raise ValueError("Site held/repair selected count mismatch")
    # All non-held rows physically checked; further holes are reported,
    # never filled from an unvalidated or unshifted ERA RH assumption.
    humidityfinite=np.isfinite(vpd)&np.isfinite(temperature)&np.isfinite(pressure)
    ea=es-vpd
    goodrh=(humidityfinite&(vpd>=0)&(ea>0)&(ea<=es*1.0005))
    vpd[~goodrh]=np.nan
    humidity=qbot(temperature,vpd,pressure)
    humidity[~np.isfinite(vpd)]=np.nan
    sane=(np.isfinite(humidity)&(humidity>0)&(humidity<.08))
    humidity[~sane]=np.nan
    vpd[~sane]=np.nan
    if (not np.isfinite(vpd[repairmask]).all() or
        not np.isfinite(humidity[repairmask]).all()):
        raise ValueError("Previously verified Stage12b source patch was unexpectedly invalid")
    forcing=pd.DataFrame({
        "time":p.native.dt.strftime("%Y-%m-%d %H:%M:%S"),
        "TBOT":temperature+273.15,
        "QBOT":humidity,
        "PSRF":pressure,
        "FSDS":np.where(values["SW_IN_F"]>=0,values["SW_IN_F"],np.nan),
        "FLDS":values["LW_IN_F"],
        "WIND":np.where(values["WS_F"]>=0,values["WS_F"],np.nan),
        "PRECTmms":np.where(values["P_F"]>=0,values["P_F"]/(step*60),np.nan),
        "TA_USE":temperature,
        "VPD_USE":vpd,
    })
    if len(forcing)!=n or list(forcing)!=COLUMNS:
        raise ValueError("Complete source-native full-year shadow schema failure")
    mandatory_holds=holdmask|~np.isfinite(forcing.to_numpy()[:,1:].astype(float)).all(axis=1)
    diagnostics=[]
    for i in np.flatnonzero(mandatory_holds):
        diagnostics.append({
            "site":site,"native_key":native[i],
            "source_science_held_Stage12b":bool(holdmask[i]),
            "nonhumidity_source_fallback_any":bool(any(f[i] for k,f in fall.items() if k!="VPD_F")),
            "TBOT_missing":bool(pd.isna(forcing.TBOT.iloc[i])),
            "QBOT_missing":bool(pd.isna(forcing.QBOT.iloc[i])),
            "other_meteo_missing":bool(forcing.iloc[i][["PSRF","FSDS","FLDS","WIND","PRECTmms"]].isna().any()),
            "production_approved":False
        })
    # Entire time series is complete, but missing/held rows render it
    # intentionally not executable as model forcing.
    # Compare affected boundaries to original numeric source wherever possible;
    # first & last neighbor checked without changing neighbors.
    edges=[]
    prev=numeric(p.VPD_F)
    for i in np.flatnonzero(repairmask):
        for a,b in ((i-1,i),(i,i+1)):
            if not 0<=a<b<n:raise ValueError("Patch on source time boundary")
            oldjump=abs(prev[b]-prev[a]) if np.isfinite(prev[[a,b]]).all() else np.nan
            newjump=abs(vpd[b]-vpd[a]) if np.isfinite(vpd[[a,b]]).all() else np.nan
            edges.append({"site":site,"left_native_key":native[a],
                "right_native_key":native[b],
                "source_original_VPD_jump_hPa":oldjump,
                "new_shadow_VPD_jump_hPa":newjump,
                "new_jump_over4hPa":bool(np.isfinite(newjump) and newjump>4.),
                "added_jump_over2hPa":bool(np.isfinite([oldjump,newjump]).all()
                                             and newjump-oldjump>2.),
                "boundary_missing_source_data":bool(not np.isfinite(newjump))})
    edges=pd.DataFrame(edges).drop_duplicates(["site","left_native_key","right_native_key"])
    if edges.empty:raise ValueError("No touched native edge rows")
    stats={"site":site,"years":f"{first}-{last}","native_minutes":step,
       "noleap_source_rows":n,"Stage12b_RH_numeric_patches_applied":int(repairmask.sum()),
       "Stage12b_science_humidity_holds":int(holdmask.sum()),
       "total_rows_with_any_missing_held_variable":int(mandatory_holds.sum()),
       "other_humidity_missing_or_invalid_rows":int(
         (np.isnan(vpd)&~holdmask).sum()),
       "non_humidity_source_or_ERA_gap_rows":int(
         forcing[["TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms"]].isna().any(axis=1).sum()),
       "valid_physical_forcing_rows":int((~mandatory_holds).sum()),
       "source_TA_ERA_fallback_rows":int(fall["TA_F"].sum()),
       "source_P_ERA_fallback_rows":int(fall["PA_F"].sum()),
       "source_precip_ERA_fallback_rows":int(fall["P_F"].sum()),
       "adjacent_modified_edges_checked":len(edges),
       "new_edge_gt4hPa":int(edges.new_jump_over4hPa.sum()),
       "added_edge_gt2hPa":int(edges.added_jump_over2hPa.sum()),
       "scientific_hold":True,"Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False}
    return forcing,pd.DataFrame(evidence),pd.DataFrame(diagnostics),edges,stats

def calculate():
    meta,patch,holds,manifest=preflight()
    products={};patches=[];missing=[];edges=[];summaries=[]
    for site in SIX:
        p=patch.loc[patch.site.eq(site)]
        h=holds.loc[holds.site.eq(site)]
        force,proof,holes,edge,state=process_site(site,meta[site],p,h)
        products[site]=force
        patches.append(proof)
        if len(holes):missing.append(holes)
        edges.append(edge);summaries.append(state)
    states=pd.DataFrame(summaries)
    if (int(states.Stage12b_RH_numeric_patches_applied.sum())!=1687 or
        int(states.Stage12b_science_humidity_holds.sum())!=233
        or len(products)!=6):
        raise ValueError("Six-site original 1687/233 Stage12b partition differs")
    proof=pd.concat(patches,ignore_index=True)
    problems=pd.concat(missing,ignore_index=True) if missing else pd.DataFrame()
    nearby=pd.concat(edges,ignore_index=True)
    return products,states,proof,problems,nearby

def self_test():
    assert len(SIX)==6 and sum(COUNTS.values())==1687 and sum(HOLD_COUNTS.values())==237
    assert len(FIELDS)==7
    t=20.;p=101325.;rh=40.
    v=float(sat(t))*(1-rh/100.)
    assert abs(float(qbot(t,v,p))-
               float(.622*(100*sat(t)*rh/100.)/(p-.378*100*sat(t)*rh/100.)))<1e-12
    assert v>0
    print("STAGE12C SELF-TEST PASS: six source native timelines, 1687 RH patches, 233 source holds, site T unchanged at targets; no writes",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    opts=ap.add_mutually_exclusive_group(required=True)
    opts.add_argument("--self-test",action="store_true")
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12C — SIX COMPLETE-TIMELINE RESEARCH SHADOWS; HELD HUMIDITY IS NaN | "+VERSION,flush=True)
    self_test()
    if args.self_test:return
    products,stats,patched,holes,edges=calculate()
    print("\n========== SIX SHADOW SITE STATUS ==========",flush=True)
    print(stats.to_string(index=False),flush=True)
    print("\n========== UNRESOLVED SITE ROWS ==========",flush=True)
    print(holes.groupby("site").size().to_string() if len(holes) else "NONE",flush=True)
    print("\nSTAGE12C SUMMARY:",
      "time_complete_shadow_sites=6", "new_selected_RH_records=1687",
      "preserved_original_science_humidity_holds=233",
      "total_new_unresolved_row_flags="+str(len(holes)),
      "new_large_boundary_jumps="+str(int(stats.new_edge_gt4hPa.sum())),
      "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: ZERO FILE WRITES.",flush=True)
        return
    out=ROOT/"science_trials"/("stage12c_six_site_noleap_hold_shadows_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Native time-complete, SCIENTIFIC HOLD; intentionally includes NaN humidity and other source gaps; NEVER model-run.\n")
    paths={}
    for site,df in products.items():
        name=site+"_STAGE12C_NOT_MODEL_READY_NOLEAP.csv"
        df.to_csv(out/name,index=False)
        if len(pd.read_csv(file(out/name)))!=len(df):
            raise ValueError("Stage12c serialized site row count changed: "+site)
        paths[name]=sha(out/name)
    tables={
        "6_site_full_timeline_and_hold_counts.csv":stats,
        "1687_exact_native_RH_patch_provenance.csv":patched,
        "all_remaining_shadow_missing_or_held_rows.csv":holes,
        "all_1687_patch_adjacent_source_boundary_checks.csv":edges
    }
    for name,d in tables.items():
        d.to_csv(out/name,index=False)
        paths[name]=sha(out/name)
    note="""# Stage12c is a NOT MODEL READY full-native-time research shadow
Original source and Stage07 files are SHA verified and immutable.
Each site has a full NO_LEAP native 30/60 minute timeline, but files
INTENTIONALLY CONTAIN NaNs at previously held humidity source times and
any other unvalidated source gaps. There are 1687 exactly matched bulk
source-native ERA5-Land grid RH research patches at untouched original
TA_F and original PA_F. All timestamp/clock offsets are STILL provisional.
Not a replacement for earlier Stage07 QC-v5 full algorithm. In particular,
ERA-backed non-humidity fill is a transparent provisional source fallback,
not a confirmed tower observation or model approval.
Flag all boundary shifts; do not auto interpolate held physics or
declare source clock resolved. No DATM/CIME/Slurm or spinup allowed.
"""
    (out/"SCIENTIFIC_HOLD.md").write_text(note)
    paths["SCIENTIFIC_HOLD.md"]=sha(out/"SCIENTIFIC_HOLD.md")
    receipt={"version":VERSION,
        "stage12b_receipt_SHA256":sha(B/"stage12b_numeric_candidate_receipt.json"),
        "stage07_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
        "research_only_six_full_native_timeline_sites":6,
        "original_ERA5Land_source_grid_RH_candidate_patch_times":1687,
        "physically_held_times_intentionally_missing":233,
        "new_source_clock_approvals":0,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "INCOMPLETE_marker_present":True,"model_ready":False,
        "output_sha256":paths}
    (out/"stage12c_research_shadow_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12C SIX-SITE INCOMPLETE SHADOW DIR:",out,flush=True)
    print("NO SEALED SOURCE, STAGE07, STAGE11h/l/q, DATM, CIME OR SLURM WRITES.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12C STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

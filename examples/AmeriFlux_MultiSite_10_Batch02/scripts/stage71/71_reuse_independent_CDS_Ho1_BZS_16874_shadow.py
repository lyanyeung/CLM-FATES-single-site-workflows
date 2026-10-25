#!/usr/bin/env python3
"""Stage71: existing independently verified CDS ERA5 coverage for 16874 Ho1/BZS VPD hard records.

Read only except an isolated, source-checksummed Stage71 report. Reuse existing
Stage15/18/50/62 CDS ERA5 grid-year t2m/d2m/sp receipts only after original
payload SHA256, NetCDF SHA256, UTC calendar, coordinate and units checks. NEVER
mistake original FLUXNET product's VPD_ERA/TA_ERA for independent CDS ERA5.

Use user-supplied BIF US-Ho1 -5, US-BZS -9 and original Stage68 shadow UTC as
*provisional* historical clock mappings, not model approval. For verified CDS
years compute water RH on the ERA5 t2m/d2m basis, interpolate hourly water RH
to exact tower half-hour UTC, preserve source TA_F/PA and form VPD/QBOT.
One-to-one source row/time identity, original physical QC, and |Ttower-Tera5|
are audited. Keep ALL 16874 source events under HOLD pending historic clock
and science gates; do not overwrite original, ERA5, DATM, CIME or model files.
"""
import argparse,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
ERA_MODULE=BASE/"scripts/stage50/50_prepare_unified_CDS_ERA5_RH_zero_gt100.py"
ERA_BLOB="757452798582dc0aaf6d2c78f23999e653247469"
BIF=BASE/"data/official_BIF_20261025/official_two_site_BIF_time_evidence.json"
BIF_BLOB="444889041c37cdaa6b79d149053e5299756fdb8c"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
R=ROOT/"reports"
S70=R/"stage70_Ho1_BZS_original_VPD_product_lineage_20261025T082409Z_59c37277"
F70="16874_original_F_VPD_ERA_MDS_exact_source_lineage.csv"
COUNTS={"US-Ho1":16788,"US-BZS":86}
OFFSETS={"US-Ho1":-5,"US-BZS":-9}

CACHE_DIRS=(
    Path.home()/"AmeriFlux_Batch02_Stage62_external_CDS_ERA5",
    Path.home()/"AmeriFlux_Batch02_Stage62_external_CDS_ERA5/isolated_original_payload_SHA256_conflict_recovery_v1",
    Path.home()/"AmeriFlux_Batch02_Stage50_external_CDS_ERA5",
    Path.home()/"AmeriFlux_Batch02_ERA5_missing_grid_years",
)
STAGE15=Path.home()/"AmeriFlux_Batch02_ERA5_five_one_year_controls"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for p in iter(lambda:f.read(1<<20),b""):h.update(p)
    return h.hexdigest()

def gitblob(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Expected existing non-symlink source "+str(p))
    s=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(s)).encode()+b"\0"+s).hexdigest()

def load_era():
    if gitblob(ERA_MODULE)!=ERA_BLOB:
        raise ValueError("Stage50 independent CDS scientific reader changed")
    spec=util.spec_from_file_location("pinned_batch02_stage50",ERA_MODULE)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def load_original():
    m=json.loads((S70/"stage70_original_VPD_source_manifest.json").read_text())
    if ((S70/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE70_HO1_BZS_ORIGINAL_VPD_F_ERA_MDS_PRODUCT_PROVENANCE_v1" or
        m.get("n_original_VPD_events_exactly_scoped")!=16874 or
        m.get("original_Ho1_events")!=16788 or
        m.get("original_BZS_events")!=86 or
        m.get("same_FLUXNET_processed_VPD_ERA_not_independent") is not True or
        m.get("independent_CDS_ERA5_Ho1_BZS_not_yet_joined") is not True or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage70 proven source or science gate changed")
    for name,digest in m["output_sha256"].items():
        if sha(S70/name)!=digest:
            raise ValueError("Stage70 SHA256 manifest evidence differs: "+name)
    if gitblob(BIF)!=BIF_BLOB:
        raise ValueError("Official source BIF extraction Git blob differs")
    raw=json.loads(BIF.read_text())
    if (raw.get("schema")!="BATCH02_USER_UPLOADED_ORIGINAL_AMERIFLUX_BIF_EXTRACT_v1"
        or raw.get("approved_for_DATM") is not False):
        raise ValueError("Official BIF source extract science status changed")
    stations={q["site_id"]:q for q in raw["sites"]}
    if set(stations)!=set(COUNTS):
        raise ValueError("Unexpected BIF site count")
    for site in COUNTS:
        q=stations[site]
        if (float(q["utc_offset_hours"])!=OFFSETS[site] or
            q.get("offset_history_coverage_verified") is not False or
            q.get("model_time_join_approved") is not False or
            q.get("utc_offset_date_start") is not None):
            raise ValueError("Official published BIF date/offset gate changed "+site)
    events=pd.read_csv(S70/F70,dtype={"site":str,"source_csv_row":str,
                                      "tower_local_start":str,
                                      "timestamp_start":str,"shadow_UTC_START":str})
    if (len(events)!=16874 or
        Counter(events["site"])!=Counter(COUNTS) or
        events.duplicated(["site","tower_local_start"]).any() or
        events.duplicated(["site","source_csv_row"]).any() or
        events.duplicated(["site","shadow_UTC_START"]).any()):
        raise ValueError("Source Stage70 16874 event/time uniqueness failed")
    required=["TA_C","PA_kPa","TA_original_QC","VPD_hPa","shadow_UTC_START",
              "source_sha256","tower_year","source_csv_row"]
    if not set(required).issubset(events.columns):
        raise ValueError("Stage70 missing original fields "+str(set(required)-set(events.columns)))
    expected=events.groupby(["site","VPD_original_QC"]).size().to_dict()
    if expected!={("US-BZS",1):18,("US-BZS",2):68,
                 ("US-Ho1",1):50,("US-Ho1",2):16738}:
        raise ValueError("Stage70 VPD original source QC census differs")
    return events,stations,m

def receipt_candidates(mod,key,site):
    folder=mod.grid_name(key)
    out=[p/folder/"verified_receipt.json" for p in CACHE_DIRS]
    out.append(STAGE15/(site+"_"+str(key[2]))/"verified_receipt.json")
    return out

def checked_receipt(mod,key,site):
    """Report failed receipts without silently calling a corrupt payload verified."""
    issues=[]
    for p in receipt_candidates(mod,key,site):
        if not p.exists():continue
        if p.is_symlink():
            issues.append(str(p)+": SYMLINK_BLOCKED")
            continue
        try:
            r=mod.read_receipt(p,key,[site])
            if r is None:raise ValueError("Receipt absent after existence check")
            return dict(status="VERIFIED_INDEPENDENT_CDS_REUSE",path=str(p),
                receipt=r,issues=issues)
        except (ValueError,KeyError,FileNotFoundError,OSError,
                TypeError,AssertionError) as exc:
            issues.append(str(p)+": "+type(exc).__name__+" "+str(exc)[:300])
    return dict(status="HOLD_NO_VERIFIED_CDS_GRIDYEAR",
                path="",receipt=None,issues=issues)

def build(events,station,mod):
    result=[]
    report=[]
    verified={}
    for (site,year),sub in events.groupby(["site","tower_year"],sort=True):
        year=int(year)
        lat=float(station[site]["latitude"])
        lon=float(station[site]["longitude"])
        grid=mod.grid_of(lat,lon)
        key=(*grid,year)
        match=checked_receipt(mod,key,site)
        resultrow={"site":site,"original_tower_year":year,
            "n_original_hard":len(sub),
            "ERA5_grid_lat":grid[0],"ERA5_grid_lon":grid[1],
            "ERA5_gridyear_key":mod.grid_name(key),
            "published_BIF_UTC_offset":OFFSETS[site],
            "CDS_status":match["status"],
            "CDS_verified_receipt":match["path"],
            "CDS_problem_count":len(match["issues"]),
            "CDS_source_errors":match["issues"],
            "n_shadow_numeric_physical_candidate":0,
            "n_TA_QC_or_ERA_delta_HOLD":0,
            "n_CDS_physics_HOLD":0,
            "historical_time_approval":False}
        frame=sub.copy()
        frame["provisional_CDS_gridyear"]=mod.grid_name(key)
        frame["published_BIF_UTC_offset"]=OFFSETS[site]
        frame["CDS_verified_receipt"]=match["path"]
        frame["CDS_dataset"]=mod.DATASET
        frame["CDS_netcdf_sha256"]=""
        frame["CDS_ERA5_RH_water_pct"]=np.nan
        frame["CDS_ERA5_T2M_C"]=np.nan
        frame["CDS_ERA5_Td2M_C"]=np.nan
        frame["CDS_ERA5_surface_pressure_Pa"]=np.nan
        frame["source_tower_minus_independent_ERA5_T_C"]=np.nan
        frame["shadow_VPD_water_hPa"]=np.nan
        frame["shadow_QBOT_kgkg"]=np.nan
        frame["science_status"]="HOLD_NO_VERIFIED_CDS_GRIDYEAR"
        frame["historical_BIF_time_source_verified"]=False
        frame["approved_for_DATM"]=False
        if match["receipt"] is not None:
            verified[key]=match["path"]
            receipt=match["receipt"]
            frame["CDS_netcdf_sha256"]=receipt["netcdf_sha256"]
            times,era_t,era_td,era_p,era_rh=mod.verify_nc(
                receipt["netcdf_path"],year,grid)
            source_utc=pd.to_datetime(frame["shadow_UTC_START"],
                    format="%Y%m%d%H%M",errors="raise")
            tnum=times.asi8/1e9
            points=source_utc.astype("int64").to_numpy()/1e9
            if not (points.min()>=tnum.min() and points.max()<=tnum.max()):
                raise ValueError("Verified CDS calendar lacks source UTC for "+site+":"+str(year))
            new_t=np.interp(points,tnum,era_t)
            new_td=np.interp(points,tnum,era_td)
            new_p=np.interp(points,tnum,era_p)
            new_rh=np.interp(points,tnum,era_rh)
            ta=pd.to_numeric(frame["TA_C"],errors="raise").to_numpy(float)
            pa=pd.to_numeric(frame["PA_kPa"],errors="raise").to_numpy(float)
            qc=pd.to_numeric(frame["TA_original_QC"],errors="coerce").to_numpy(float)
            with np.errstate(all="ignore"):
                sat=mod.es(ta)
                vapor=sat*new_rh/100.
                vpd=sat-vapor
                den=pa*1000-.378*vapor*100
                qbot=.622*vapor*100/den
            physically=(np.isfinite(ta)&(ta>-80)&(ta<65)&
               np.isfinite(pa)&(pa>50)&(pa<110)&
               np.isfinite(new_rh)&(new_rh>0)&(new_rh<=100.05)&
               np.isfinite(vpd)&(vpd>=-0.005)&
               np.isfinite(qbot)&(qbot>0)&(qbot<0.08))
            context=physically&(qc==0)&(np.abs(ta-new_t)<=8)
            status=np.where(~physically,"HOLD_PHYSICS_CDS_OR_ORIGINAL_T_PA",
                np.where(qc!=0,"HOLD_ORIGINAL_TA_QC_NONZERO",
                    np.where(np.abs(ta-new_t)>8,
                       "HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C",
                       "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD")))
            frame["CDS_ERA5_RH_water_pct"]=new_rh
            frame["CDS_ERA5_T2M_C"]=new_t
            frame["CDS_ERA5_Td2M_C"]=new_td
            frame["CDS_ERA5_surface_pressure_Pa"]=new_p
            frame["source_tower_minus_independent_ERA5_T_C"]=ta-new_t
            frame["shadow_VPD_water_hPa"]=np.where(context,vpd,np.nan)
            frame["shadow_QBOT_kgkg"]=np.where(context,qbot,np.nan)
            frame["science_status"]=status
            resultrow["n_shadow_numeric_physical_candidate"]=int(context.sum())
            resultrow["n_TA_QC_or_ERA_delta_HOLD"]=int(
                 (physically&~context).sum())
            resultrow["n_CDS_physics_HOLD"]=int((~physically).sum())
            if int(context.sum())+int((physically&~context).sum())+int(
                   (~physically).sum())!=len(sub):
                raise ValueError("Subpopulation physics completeness broken")
        result.append(frame)
        report.append(resultrow)
        print("SITE YEAR",site,year,"n",len(sub),
             "CDS",match["status"],
             "shadow_numeric",resultrow["n_shadow_numeric_physical_candidate"],
             "issues",len(match["issues"]),flush=True)
    output=pd.concat(result,ignore_index=True)
    report=pd.DataFrame(report)
    if len(output)!=16874 or Counter(output["site"])!=Counter(COUNTS):
        raise ValueError("Source 16874 holds changed")
    if (output["approved_for_DATM"].any() or
        output["historical_BIF_time_source_verified"].any()):
        raise ValueError("No historical clock or DATM approval allowed")
    count=output["science_status"].value_counts(dropna=False).to_dict()
    print("STAGE71 VERIFIED CDS GRIDYEARS",len(verified),"/",len(report))
    print("STAGE71 ORIGINAL 16874 SOURCE SHADOW STATUS",count)
    print("STAGE71 BIF HISTORICAL DATE / INDEPENDENT CDSE5 SCIENCE HOLDS ARE NOT RELEASED")
    return output,report,verified

def self_test():
    lat,lon=45.2040,-68.7402
    assert (round(lat*4)/4,round(lon*4)/4)==(45.25,-68.75)
    assert (round(64.6963*4)/4,round(-148.3235*4)/4)==(64.75,-148.25)
    assert sum(COUNTS.values())==16874
    stamp=pd.Timestamp("2000-12-31 23:30")
    assert (stamp-pd.Timedelta(hours=-5)).strftime("%Y%m%d%H%M")=="200101010430"
    assert (stamp-pd.Timedelta(hours=-9)).strftime("%Y%m%d%H%M")=="200101010830"
    print("STAGE71 SELF-TEST PASS | official BIF 0.25-degree grids, year rollover, 16874 immutable original hard")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    mod=load_era()
    events,stations,m70=load_original()
    rows,plan,receipts=build(events,stations,mod)
    if a.check:
        print("STAGE71 CHECK PASS | independently checksum+calendar verified ERA5 reuse; zero output/source writes")
        return
    out=R/("stage71_Ho1_BZS_independent_CDS_verified_reuse_shadow_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("CDS source/clock candidate only; not DATM approved.\n")
    files={
      "16874_original_hard_independent_CDS_water_humidity_SHADOW.csv":rows,
      "Ho1_BZS_original_hard_gridyear_CDS_coverage.csv":plan}
    sha_files={}
    for name,df in files.items():
        f=out/name;df.to_csv(f,index=False);sha_files[name]=sha(f)
    manifest={
      "schema":"STAGE71_HO1_BZS_INDEPENDENT_CDS_VERIFIED_RECEIPT_SHADOW_v1",
      "n_original_hard_total":16874,
      "n_Ho1":16788,"n_BZS":86,
      "n_verified_CDS_gridyears":len(receipts),
      "n_requested_CDS_gridyears":len(plan),
      "n_num_valid_only":int(rows["science_status"].eq(
        "SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD").sum()),
      "n_remaining_HOLD":16874,
      "historical_BIF_offset_date_verified":False,
      "independent_CDS_same_as_FLUXNET_VPD_ERA":False,
      "prior_Stage64_9389_numeric_candidates_untouched":True,
      "approved_for_DATM":False,"approved_for_spinup":False,
      "source_SHA256":{
         "Stage70_events":sha(S70/F70),
         "Stage70_manifest":sha(S70/"stage70_original_VPD_source_manifest.json"),
         "original_user_BIF_evidence_SHA256":sha(BIF),
         "Stage50_reader_gitblob":ERA_BLOB},
      "output_sha256":sha_files,
      "no_existing_source_or_model_writes":True}
    (out/"stage71_source_science_manifest.json").write_text(json.dumps(
         manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE71 AUDIT PASS | independent CDS Ho1/BZS coverage and source-physics shadow inventoried")
    print("REPORT",out)
    print("NO ORIGINAL, CDS, STAGE64-70, NETCDF, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage23: audit US-EML's 63 A-tier Stage22 candidates with nearby tower QC0.

Reads unchanged original AmeriFlux tower FLUXMET and verified Stage18 ERA5.
Compares QC0-derived tower RH to ERA5 RH at ACTUAL QC0 timestamps (not merely
nearby anomaly timestamps), checks before/after coverage, and groups episodes.

QC0 indicates a product quality flag, NOT proven independent RH observation.
This is a review-only pilot: never approve, interpolate forcing, or run CIME.
--check writes no files; --write-report creates isolated HOME CSV/JSON reports.
"""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import xarray as xr

ROOT=Path.home()/"AmeriFlux_Batch02_stage22_risk_screen_20261023T022558Z_a69b89d2"
ROOT19=Path.home()/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
ROOT18=Path.home()/"AmeriFlux_Batch02_ERA5_missing_grid_years"
BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
ST11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
GRID=(64.0,-149.25)
OFFSET=-9
PIN17="84f680fb67030d374bb8a02abd4fce5a4a2c5d4abe7c59a30acf7bb5948488d4"
FOCUS_YEARS={2012:29,2016:1,2017:14,2019:8,2020:4,2021:1,2022:6}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def esw(tc):
    tc=np.asarray(tc,float)
    return 6.112*np.exp(17.67*tc/(tc+243.5))

def raw_time(s):
    return pd.to_datetime(s.astype(str).str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")

def safe_num(s):
    a=pd.to_numeric(s,errors="coerce")
    return a.mask((a<=-9990)|~np.isfinite(a))

def grid_dir(year):
    lat,lon=GRID
    return ROOT18/f"ERA5_{year}_lat{lat:+07.2f}_lon{lon:+08.2f}"

def load_pilot():
    m22=json.loads((ROOT/"manifest.json").read_text())
    if not (ROOT/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file() or (
        m22.get("n_candidates")!=3947 or m22.get("n_holds")!=937 or
        m22.get("n_approved")!=0 or m22.get("model_ready") is not False):
        raise ValueError("Unexpected Stage22 review status")
    stage21=Path.home()/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
    if sha(stage21/"manifest.json")!=m22["stage21_manifest_sha256"] or (
       sha(stage21/"all_4884_stage21_repair_decision_ledger.csv")!=m22["stage21_ledger_sha256"]):
        raise ValueError("Pinned Stage21 review inputs changed")
    a=pd.read_csv(ROOT/"4884_risk_decisions_NOT_FOR_DATM.csv",parse_dates=["local"])
    if len(a)!=4884 or a.duplicated(["site","local"]).any():
        raise ValueError("Stage22 identity differs")
    pilot=a.loc[a.site.eq("US-EML")&a.risk_tier.eq("A_QC0_NEARBY")].copy()
    pilot.sort_values("local",inplace=True)
    if len(pilot)!=63 or pilot.groupby("year").size().to_dict()!=FOCUS_YEARS:
        raise ValueError("Unexpected US-EML A-tier year distribution")
    if not pilot.scientific_approval.astype(str).str.lower().eq("false").all():
        raise ValueError("Pilot approvals unexpectedly changed")
    if not pilot.model_forcing_ready.astype(str).str.lower().eq("false").all():
        raise ValueError("Pilot model-ready status unexpectedly changed")
    m19=json.loads((ROOT19/"manifest.json").read_text())
    if m19.get("scientific_status")!="NUMERICAL_SENSITIVITY_ONLY_ALL_ROWS_HOLD":
        raise ValueError("Stage19 science status differs")
    m11=json.loads((ST11/"manifest.json").read_text())
    if sha(ST11/"manifest.json")!=m19["stage11_manifest_sha256"]:
        raise ValueError("Stage11 manifest SHA changed")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    source={x["site"]:x for x in m08["sites"]}
    raw=Path(source["US-EML"]["primary"]).resolve(strict=True)
    if sha(raw)!=m19["original_source_sha256"]["US-EML"] or (
       sha(raw)!=m11["input_hashes"].get(str(raw))):
        raise ValueError("Original US-EML meteorology checksum differs")
    bifs=sorted(raw.parent.glob("*_BIF_*.csv"))
    if len(bifs)!=1:raise ValueError("US-EML BIF ambiguous")
    offsets=[]
    with bifs[0].open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            if row.get("VARIABLE","").strip()=="UTC_OFFSET":
                offsets.append(float(row["DATAVALUE"]))
    if offsets!=[OFFSET]:raise ValueError("Original UTC offset changed")
    fields=["TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"]
    head=set(pd.read_csv(raw,nrows=0).columns)
    if not set(fields).issubset(head):raise ValueError("Missing raw tower QC fields")
    if "RH" in head:fields+=["RH"]
    if "RH_QC" in head:fields+=["RH_QC"]
    tower=pd.read_csv(raw,usecols=fields,dtype={"TIMESTAMP_START":str})
    tower["local"]=raw_time(tower.TIMESTAMP_START)
    if tower.local.duplicated().any():raise ValueError("Duplicate raw tower timestamps")
    for field in fields[1:]:tower[field]=safe_num(tower[field])
    tower.sort_values("local",inplace=True)
    tower["tower_RH_from_T_VPD_pct"]=100*(1-tower.VPD_F/esw(tower.TA_F))
    valid=(tower.TA_F_QC.eq(0)&tower.VPD_F_QC.eq(0)&
           tower.tower_RH_from_T_VPD_pct.gt(0)&
           tower.tower_RH_from_T_VPD_pct.le(100.05))
    good=tower.loc[valid].copy()
    return pilot,good,raw,m19

def get_era(year,m19):
    folder=grid_dir(year)
    r=json.loads((folder/"verified_receipt.json").read_text())
    if r.get("schema")!="STAGE18_VERIFIED_GRIDYEAR_v1" or (
        r.get("year")!=year or r.get("stage17_plan_sha256")!=PIN17 or
        tuple(r.get("grid_year_key",[]))!=(GRID[0],GRID[1],year) or
        r.get("science_approved") is not False):
        raise ValueError("Stage18 year receipt differs")
    nc=Path(r["netcdf_path"]).resolve(strict=True)
    payload=Path(r["original_payload_path"]).resolve(strict=True)
    if sha(nc)!=r["netcdf_sha256"] or sha(payload)!=r["original_payload_sha256"]:
        raise ValueError("ERA5 CDS file SHA changed")
    if m19["verified_netcdf_sha256"].get(str(nc))!=r["netcdf_sha256"]:
        raise ValueError("Stage19 ERA5 checksum differs")
    with xr.open_dataset(nc,engine="netcdf4") as ds:
        if set(ds.data_vars)!={"t2m","d2m","sp"}:raise ValueError("Wrong ERA5 variables")
        ti=pd.to_datetime(ds.valid_time.values,utc=True).tz_localize(None)
        t=np.asarray(ds.t2m.values,float)-273.15
        d=np.asarray(ds.d2m.values,float)-273.15
        grid=(float(np.ravel(ds.latitude.values)[0]),
              float(np.ravel(ds.longitude.values)[0]))
    exp=pd.date_range(f"{year-1}-12-29 00:00",
                      f"{year+1}-01-03 23:00",freq="h")
    if grid!=GRID or len(ti)!=len(exp) or (
        not np.array_equal(ti.values,exp.values)):
        raise ValueError("ERA5 grid or UTC hours wrong")
    rh=100*esw(d)/esw(t)
    if not (np.isfinite(rh)&(rh>0)&(rh<=100.05)).all():
        raise ValueError("Invalid ERA5 RH")
    return ti,rh

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--check",action="store_true")
    m.add_argument("--write-report",action="store_true")
    args=p.parse_args()
    pilot,good,source,m19=load_pilot()
    years={}
    details=[]
    for year,sub in pilot.groupby("year"):
        ti,rh=get_era(int(year),m19)
        years[int(year)]=(ti,rh)
        # +/-24h QC0 observations; neither interpolation nor nearby QC0 proves
        # that a target is independently observed.
        for _,row in sub.iterrows():
            t0=row.local
            g=good.loc[(good.local>=t0-pd.Timedelta(hours=24))&
                       (good.local<=t0+pd.Timedelta(hours=24))].copy()
            before=g.local.lt(t0)
            after=g.local.gt(t0)
            if len(g)==0:raise ValueError("Stage22 A-tier lacks QC0 neighbors")
            query_utc=g.local-pd.Timedelta(hours=OFFSET)
            x=(ti.astype("int64")//10**9).to_numpy(float)
            xx=(query_utc.astype("int64")//10**9).to_numpy(float)
            if xx.min()<x.min() or xx.max()>x.max():
                raise ValueError("QC0 neighbor not covered by ERA5 UTC buffers")
            near_rh=np.interp(xx,x,rh)
            observed=g.tower_RH_from_T_VPD_pct.to_numpy(float)
            gap=near_rh-observed
            nearest=np.min(np.abs((g.local-t0).dt.total_seconds().to_numpy()))/60
            details.append(dict(site="US-EML",local=t0,year=int(year),
                candidate_ERA5_RH_pct=float(row.ERA5_RH_water_pct),
                candidate_VPD_hPa=float(row.sensitivity_VPD_hPa),
                temperature_gap_ERA_minus_tower_C=float(row.ERA_minus_tower_T_C),
                candidate_ice_supersaturation_caution=bool(row.ice_supersaturation_caution),
                QC0_neighbors_24h=len(g),
                QC0_before_n=int(before.sum()),
                QC0_after_n=int(after.sum()),
                nearest_QC0_minutes=float(nearest),
                QC0_tower_RH_median_pct=float(np.median(observed)),
                QC0_ERA5_RH_median_pct=float(np.median(near_rh)),
                QC0_ERA5_minus_tower_RH_median_pp=float(np.median(gap)),
                QC0_ERA5_minus_tower_RH_median_abs_pp=float(np.median(np.abs(gap))),
                QC0_RH_at_same_time_comparison_only=True,
                science_approval=False,model_forcing_ready=False))
    x=pd.DataFrame(details).sort_values("local").reset_index(drop=True)
    if len(x)!=63 or not x.local.equals(pilot.local.reset_index(drop=True)):
        raise ValueError("US-EML A63 candidate join mismatch")
    # Distinct episodes separated by more than 2 hours.
    x["episode_id"]=(x.local.diff().gt(pd.Timedelta(hours=2)).fillna(True)).cumsum()+1
    episodes=x.groupby("episode_id").agg(
        year=("year","first"),start=("local","min"),end=("local","max"),
        candidate_records=("local","size"),
        QC0_neighbors_min=("QC0_neighbors_24h","min"),
        both_sides_QC0=("QC0_before_n",lambda s:True),
        median_abs_neighbor_ERA5_minus_tower_RH_pp=(
            "QC0_ERA5_minus_tower_RH_median_abs_pp","median")).reset_index()
    both=x.assign(both=x.QC0_before_n.gt(0)&x.QC0_after_n.gt(0)).groupby(
        "episode_id").both.all()
    episodes["both_sides_QC0"]=episodes.episode_id.map(both).astype(bool)
    print("========== STAGE23 US-EML QC0 EVENT EVIDENCE ==========")
    print("PILOT:",len(x),"/63; YEARS:",len(years),"; EPISODES:",len(episodes))
    print("Candidates with QC0 on BOTH sides:",
          int((x.QC0_before_n.gt(0)&x.QC0_after_n.gt(0)).sum()),"/63")
    print("Ice supersaturation cautions:",
          int(x.candidate_ice_supersaturation_caution.sum()),"/63")
    print("Median |ERA5 - QC0-derived tower RH| at ACTUAL QC0 times:",
          round(float(x.QC0_ERA5_minus_tower_RH_median_abs_pp.median()),3),
          "percentage points (candidate-weighted)")
    print("QC0 observations represent product flags, not established independent sensor provenance")
    print(episodes[["year","start","end","candidate_records","both_sides_QC0",
                    "median_abs_neighbor_ERA5_minus_tower_RH_pp"]].to_string(index=False))
    print("APPROVED: 0; MODEL READY: 0")
    if args.check:
        print("CHECK ONLY: no files written or source changed")
        return 0
    out=Path.home()/("AmeriFlux_Batch02_stage23_US_EML_A63_QC0_evidence_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    if out.exists():raise ValueError("Report directory exists")
    out.mkdir(parents=True,exist_ok=False)
    (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage23 QC0 temporal evidence only; zero scientific approvals.\n")
    x.to_csv(out/"US_EML_63_candidate_QC0_context.csv",index=False)
    episodes.to_csv(out/"US_EML_candidate_event_windows.csv",index=False)
    (out/"manifest.json").write_text(json.dumps(dict(
        stage22_manifest_sha256=sha(ROOT/"manifest.json"),
        stage22_risk_csv_sha256=sha(ROOT/"4884_risk_decisions_NOT_FOR_DATM.csv"),
        original_US_EML_sha256=sha(source),
        script_sha256=sha(Path(__file__)),
        n_pilot=63,n_years=7,n_approved=0,model_ready=False,
        scientific_status="QC0_CONTEXT_ONLY_NO_FORCING_APPROVAL"),indent=2)+"\n")
    print("STAGE23 REPORT:",out)
    print("No original forcing, DATM, CIME, Slurm, or CDS files modified")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

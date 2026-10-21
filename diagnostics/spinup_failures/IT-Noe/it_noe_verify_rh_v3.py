#!/usr/bin/env python3
"""Read-only verifier for the IT-Noe RH-cap v3 forcing candidate.

Checks all 22 SHA256s, provenance and 20 edited rows; confirms only QBOT
changed versus v2, validates RH from NetCDF, and reports annual/cycle seams.
NO production approval, forcing edits, CIME changes or Slurm submission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from netCDF4 import Dataset

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
V2 = BASE / "datm_11_IT-Noe_QC_v2_candidate_20261021_224700"
FIELDS = ("TBOT", "QBOT", "PSRF")

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    return h.hexdigest()

def read_nc(path):
    with Dataset(path) as ds:
        arrays={name:np.ma.asarray(var[:]).filled(np.nan).copy()
                for name,var in ds.variables.items()}
        attributes=dict(ds.__dict__)
        units=getattr(ds.variables["time"],"units","")
    return arrays,attributes,units

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--forcing",type=Path,required=True)
    ap.add_argument("--parent",type=Path,default=V2)
    args=ap.parse_args()
    errors=[];warnings=[];stats=[];seams=[]
    candidate=args.forcing
    manifest_path=candidate/"CANDIDATE_PROVENANCE.json"
    parent_manifest=args.parent/"CANDIDATE_PROVENANCE.json"
    if not manifest_path.is_file() or not parent_manifest.is_file():
        ap.error("Missing parent or candidate provenance")
    man=json.loads(manifest_path.read_text())
    oldman=json.loads(parent_manifest.read_text())
    if (man.get("status")!="UNAPPROVED_RH_CAP_CANDIDATE"
        or oldman.get("status")!="UNAPPROVED_QC_SENSITIVITY"):
        errors.append("Candidate / parent status does not match expected lineage")
    if (Path(man.get("parent","/missing")).resolve()!=args.parent.resolve()
        or Path(man.get("forcing_directory","/missing")).resolve()!=candidate.resolve()
        or man.get("parent_manifest_sha256")!=sha256(parent_manifest)):
        errors.append("Parent path, candidate path, or manifest hash mismatch")
    if (man.get("source_review_complete") is not False
        or man.get("boundary_review_complete") is not False
        or man.get("full_cycle_qc_complete") is not False):
        errors.append("Unexpected science-review flags: require a separate source review")
    if (man.get("rh_capped_rows")!=20 or man.get("cap_pct")!=99.9
        or man.get("threshold_pct")!=100.01):
        errors.append("Unexpected RH-cap policy or row count")
    hashes=man.get("year_sha256",{})
    parent_hashes=oldman.get("year_sha256",{})
    years={str(y) for y in range(2004,2026)}
    if set(hashes)!=years or set(parent_hashes)!=years:
        errors.append("Full 22-year hashes missing")
    log_path=candidate/"rh_cap_edits.csv"
    annual_path=candidate/"annual_rh_cap_qc.csv"
    if not log_path.is_file() or not annual_path.is_file():
        ap.error("Missing v3 RH-cap row or annual ledger")
    log=pd.read_csv(log_path,parse_dates=["timestamp"])
    annual=pd.read_csv(annual_path)
    if len(log)!=20 or log.timestamp.duplicated().any():
        errors.append("RH-cap ledger must contain exactly 20 unique times")
    if set(log.year)!={2010,2025} or len(log.loc[log.year==2010])!=15 or len(log.loc[log.year==2025])!=5:
        errors.append("Expected 2010=15 and 2025=5 RH-cap records")
    if not log.empty and (log.year!=log.timestamp.dt.year).any():
        errors.append("RH-cap log timestamp-year mismatch")
    if set(annual.year)!=set(range(2004,2026)):
        errors.append("Annual QC years missing or duplicated")
    previous_last=None
    first_value=None
    for year in range(2004,2026):
        filename=f"IT-Noe_DATM_{year}.nc"
        target=candidate/filename
        parent=args.parent/filename
        try:
            if target.is_symlink() or not target.is_file() or not parent.is_file():
                raise ValueError("Missing file or unexpected symlink")
            if sha256(target)!=hashes.get(str(year)) or sha256(parent)!=parent_hashes.get(str(year)):
                raise ValueError("SHA256 hash mismatch")
            arr,attr,units=read_nc(target)
            old,oldattr,oldunits=read_nc(parent)
            if attr.get("provenance_status")!="UNAPPROVED_RH_CAP_CANDIDATE":
                raise ValueError("Missing v3 NetCDF provenance")
            if attr.get("parent_candidate_sha256")!=parent_hashes[str(year)]:
                raise ValueError("Incorrect parent NetCDF hash attribute")
            if set(arr)!=set(old) or f"{year}-01-01" not in str(units):
                raise ValueError("Unexpected variables or time units")
            if not np.array_equal(arr["time"],old["time"],equal_nan=True):
                raise ValueError("Time axis changed")
            if len(arr["time"])!=17520 or not np.allclose(arr["time"],np.arange(17520)/48,atol=1e-5):
                raise ValueError("Not 17520 half-hourly records")
            for name in old:
                if name!="QBOT" and not np.array_equal(arr[name],old[name],equal_nan=True):
                    raise ValueError("Non-QBOT variable changed: "+name)
            v={name:np.asarray(arr[name],float).reshape(-1) for name in FIELDS}
            qold=np.asarray(old["QBOT"],float).reshape(-1)
            if any(np.shape(v[name])!=(17520,) or not np.isfinite(v[name]).all() for name in FIELDS):
                raise ValueError("Nonfinite/wrong-shape forcing field")
            year_log=log.loc[log.year==year].copy()
            index=pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="30min",inclusive="left")
            index=index[~((index.month==2)&(index.day==29))]
            locations=index.get_indexer(year_log.timestamp)
            if (locations<0).any() or len(np.unique(locations))!=len(locations):
                raise ValueError("Ledger timestamps invalid")
            touched=np.zeros(17520,dtype=bool);touched[locations]=True
            if not np.array_equal(v["QBOT"][~touched],qold[~touched]):
                raise ValueError("QBOT changed outside the 20 listed times")
            if len(locations) and not np.allclose(v["QBOT"][locations],
                                                   year_log.QBOT_after,rtol=1e-5,atol=1e-7):
                raise ValueError("Recorded new QBOT differs from file")
            if (v["QBOT"]<=0).any() or (v["PSRF"]<50000).any():
                raise ValueError("Nonphysical QBOT or PSRF")
            t=v["TBOT"]-273.15
            es=611.2*np.exp(17.67*t/(t+243.5))
            ea=v["QBOT"]*v["PSRF"]/(0.622+0.378*v["QBOT"])
            rh=100*ea/es
            if not np.isfinite(rh).all() or rh.min()<=0 or rh.max()>100.01:
                raise ValueError(f"Input RH outside 0..100.01%: min={rh.min()}, max={rh.max()}")
            jump=np.max(np.abs(np.diff(t)))
            if jump>8.0001:
                raise ValueError(f"Half-hour temperature jump exceeds 8C: {jump:.4f}")
            # This is an informational seam; calendar years/cycle may be discontinuous.
            if previous_last is not None:
                seams.append((f"{year-1}->{year}",abs(float(t[0]-previous_last))))
            if first_value is None:first_value=float(t[0])
            previous_last=float(t[-1])
            summary=annual.loc[annual.year==year]
            if len(summary)!=1 or int(summary.iloc[0].supersaturated_rows)!=len(locations):
                raise ValueError("Annual RH-cap ledger disagrees with row ledger")
            stats.append(dict(year=year,cap_rows=len(locations),
                    rh_min=round(float(rh.min()),4),rh_max=round(float(rh.max()),4),
                    halfhour_jump_max=round(float(jump),4)))
        except Exception as exc:
            errors.append(f"{year}: {exc}")
    if previous_last is not None and first_value is not None:
        seams.append(("2025->2004 forcing cycle",abs(previous_last-first_value)))
    print("IT-Noe v3 read-only verification")
    print(pd.DataFrame(stats).to_string(index=False))
    print("YEAR/CYCLE SEAMS (temperature change, C; information only):")
    print(pd.DataFrame(seams,columns=["seam","abs_TA_change_C"]).to_string(index=False))
    warnings.append("Liquid-water input RH is not CLM-diagnosed 2m RH; this is NOT a numerical model test")
    warnings.append("All 208 source-event decisions are still unapproved; derived v3 has no production approval")
    warnings.append("The 2054 Restart retains states from earlier forcing; direct continuation may not equal fully corrected spinup")
    for note in warnings:print("CAUTION:",note)
    for err in errors:print("FAIL:",err)
    print("INTEGRITY_GATE="+("PASS" if not errors else "FAIL"))
    print("READY_FOR_PRODUCTION=NO; scientific review and case-stream change remain outstanding")
    print("NO original/candidate files, CIME, restart or Slurm changed")
    return 1 if errors else 0

if __name__=="__main__":
    sys.exit(main())

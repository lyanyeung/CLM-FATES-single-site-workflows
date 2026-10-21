#!/usr/bin/env python3
"""Audit IT-Noe forcing RH supersaturation and optionally build a NEW RH-cap candidate.

DRY RUN by default. --write-candidate copies all 22 NetCDFs into a NEW
directory, adjusts QBOT only when reconstructed input RH exceeds the
specified threshold, and retains a row-by-row correction ledger.
Neither option approves production forcing or modifies CIME/Slurm/restarts.
The RH approximation uses saturation over liquid water as in the earlier QC.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
DEFAULT = ROOT / "datm_11_IT-Noe_QC_v2_candidate_20261021_224700"
ORIGINAL = ROOT / "datm_11_provisional_dynamic_zbot_v1"

def digest(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for c in iter(lambda:f.read(1048576),b""):
            h.update(c)
    return h.hexdigest()

def calc(t, q, p):
    tc = t - 273.15
    es = 611.2 * np.exp(17.67 * tc / (tc + 243.5))
    ea = q * p / (0.622 + 0.378*q)
    rh = 100 * ea / es
    q_sat = 0.622 * es / (p - 0.378*es)
    return rh, q_sat

def load(path):
    with Dataset(path) as nc:
        result = {k: np.asarray(nc.variables[k][:,0,0],float) for k in ("TBOT","QBOT","PSRF")}
        time = np.asarray(nc.variables["time"][:],float)
        status = getattr(nc,"provenance_status","")
    if len(time)!=17520 or not np.allclose(time,np.arange(17520)/48,atol=1e-5):
        raise ValueError("Invalid no-leap time axis: "+str(path))
    if any(v.shape != (17520,) or not np.isfinite(v).all() for v in result.values()):
        raise ValueError("Invalid forcing data: "+str(path))
    return result,status

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,default=DEFAULT)
    p.add_argument("--original",type=Path,default=ORIGINAL)
    p.add_argument("--out",type=Path,help="NEW candidate directory (required for --write-candidate)")
    p.add_argument("--threshold-pct",type=float,default=100.01)
    p.add_argument("--cap-pct",type=float,default=99.9)
    p.add_argument("--write-candidate",action="store_true")
    a=p.parse_args()
    if not (100 <= a.threshold_pct <= 105 and 95 <= a.cap_pct <= 100):
        p.error("Threshold must be 100..105%, cap 95..100%")
    if a.write_candidate and a.out is None:
        p.error("--write-candidate requires --out")
    if a.out is not None:
        if a.out.exists() or Path(str(a.out)+".building").exists():
            p.error("Output/staging already exists; use unique --out")
        if a.out.resolve() in (a.input.resolve(), a.original.resolve()):
            p.error("Output must differ from input and original")
    if not a.input.is_dir() or not a.original.is_dir():
        p.error("Missing original or v2 forcing")
    receipt_file = a.input / "CANDIDATE_PROVENANCE.json"
    if not receipt_file.is_file():
        p.error("Missing v2 candidate provenance")
    receipt=json.loads(receipt_file.read_text())
    if receipt.get("status")!="UNAPPROVED_QC_SENSITIVITY":
        p.error("Input forcing status is not the original unapproved v2 candidate")
    expected=receipt.get("year_sha256",{})
    if set(expected)!={str(y) for y in range(2004,2026)}:
        p.error("V2 provenance missing 22 NetCDF hashes")
    editlog=pd.read_csv(a.input/"edited_rows.csv",parse_dates=["time"])
    if len(editlog)!=4097 or editlog.time.duplicated().any():
        p.error("v2 modification ledger unexpected")
    rows=[]
    annual=[]
    replacements={}
    original_status=set()
    print("========== IT-Noe RH supersaturation investigation ==========")
    print("METHOD: RH over liquid water; CAP is a hypothetical QC sensitivity choice.")
    for year in range(2004,2026):
        file=a.input/f"IT-Noe_DATM_{year}.nc"
        source=a.original/file.name
        if not file.is_file() or not source.is_file() or file.is_symlink():
            p.error(f"{year}: original / candidate forcing missing or symlinked")
        if digest(file)!=expected[str(year)]:
            p.error(f"{year}: v2 NetCDF SHA256 mismatch")
        v, status=load(file)
        old,_=load(source)
        original_status.add(status)
        rh,qsat=calc(v["TBOT"],v["QBOT"],v["PSRF"])
        original_rh,_=calc(old["TBOT"],old["QBOT"],old["PSRF"])
        bad=np.flatnonzero(rh>a.threshold_pct)
        time=pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="30min",inclusive="left")
        time=time[~((time.month==2)&(time.day==29))]
        touched=time.isin(editlog.loc[editlog.time.dt.year==year,"time"])
        if len(time)!=17520:
            p.error(f"{year}: unexpected time length")
        q_new=v["QBOT"].copy()
        q_new[bad]=qsat[bad]*(a.cap_pct/100.0)
        rh_new,_=calc(v["TBOT"],q_new,v["PSRF"])
        if not (np.isfinite(q_new).all() and np.isfinite(rh_new).all() and
                np.all(q_new>0) and np.all(rh_new>0) and
                (not len(bad) or rh_new[bad].max()<=a.cap_pct+0.01)):
            p.error(f"{year}: failed post-cap physical check")
        annual.append({"year":year,"supersaturated_rows":len(bad),
                       "in_v2_edited_region":int(touched[bad].sum()),
                       "max_RH_before_pct":round(float(rh.max()),5),
                       "max_RH_after_pct":round(float(rh_new.max()),5),
                       "max_RH_original_pct":round(float(original_rh.max()),5)})
        for idx in bad:
            rows.append({"year":year,"timestamp":str(time[idx]),
                "v2_edited_record":bool(touched[idx]),
                "RH_original_pct":round(float(original_rh[idx]),5),
                "RH_v2_before_pct":round(float(rh[idx]),5),
                "RH_after_pct":round(float(rh_new[idx]),5),
                "TBOT_K":round(float(v["TBOT"][idx]),5),
                "PSRF_Pa":round(float(v["PSRF"][idx]),5),
                "QBOT_before":float(v["QBOT"][idx]),
                "QBOT_after":float(q_new[idx])})
        replacements[year]=q_new
        if bad.size:
            print(f"{year}: ABOVE_{a.threshold_pct}%={len(bad)} "
                  f"original_max={original_rh.max():.3f}% "
                  f"v2_max={rh.max():.3f}% after_max={rh_new.max():.3f}%")
    if original_status!={"UNAPPROVED_QC_SENSITIVITY"}:
        p.error("Unexpected NetCDF v2 provenance attribute")
    changed=pd.DataFrame(rows)
    print("SUPER_SAT_RECORDS="+str(len(changed)))
    if len(changed):
        print("FIRST_RECORDS:")
        print(changed.head(25).to_string(index=False))
    print("NO model-diagnosed RH or physics solver result is established here.")
    if not a.write_candidate:
        print("PREFLIGHT ONLY: no NetCDF or Slurm changes.")
        return
    stage=Path(str(a.out)+".building")
    stage.mkdir(parents=True)
    result_hashes={}
    for year in range(2004,2026):
        src=a.input/f"IT-Noe_DATM_{year}.nc"
        dst=stage/src.name
        shutil.copy2(src,dst)
        with Dataset(dst,"r+") as nc:
            nc.variables["QBOT"][:,0,0]=replacements[year].astype("f4")
            nc.provenance_status="UNAPPROVED_RH_CAP_CANDIDATE"
            nc.parent_candidate_sha256=expected[str(year)]
            nc.rh_cap_threshold_percent=a.threshold_pct
            nc.rh_cap_target_percent=a.cap_pct
            nc.sync()
        after,_=load(dst)
        if not np.allclose(after["QBOT"],replacements[year],rtol=1e-5,atol=1e-7):
            raise RuntimeError(f"{year}: postwrite QBOT mismatch")
        result_hashes[str(year)]=digest(dst)
    pd.DataFrame(annual).to_csv(stage/"annual_rh_cap_qc.csv",index=False)
    changed.to_csv(stage/"rh_cap_edits.csv",index=False)
    metadata={"site":"IT-Noe","status":"UNAPPROVED_RH_CAP_CANDIDATE",
        "forcing_directory":str(a.out),"parent":str(a.input),
        "parent_manifest_sha256":digest(receipt_file),
        "year_sha256":result_hashes,
        "threshold_pct":a.threshold_pct,"cap_pct":a.cap_pct,
        "rh_capped_rows":len(changed),
        "source_review_complete":False,
        "boundary_review_complete":False,
        "full_cycle_qc_complete":False,
        "note":"Physically constrained RH candidate only. Not valid model or science approval."}
    (stage/"CANDIDATE_PROVENANCE.json").write_text(json.dumps(metadata,indent=2)+"\n")
    stage.rename(a.out)
    print("NEW_CANDIDATE="+str(a.out))
    print("STATUS=UNAPPROVED_RH_CAP_CANDIDATE")
    print("No original forcing, CIME, checkpoint or Slurm jobs changed.")

if __name__=="__main__":
    sys.exit(main())

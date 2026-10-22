#!/usr/bin/env python3
"""Read-only audit of Batch03 US-NR3 2022 ERA5-Land pilot ZIP/NetCDF.

Checks archived receipt, checksum, ZIP integrity, NetCDF variables and
time coverage. Does NOT infer success from CDS request status. No extraction,
download, forcing edits, DATM or Slurm. Requires netCDF4 in clm_fates_env.
"""
import hashlib, json, zipfile, io
from pathlib import Path
import numpy as np
from netCDF4 import Dataset, num2date

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
DIR=BASE/"external_evidence/era5land_timeseries/US-NR3/2022"
NAME="ERA5Land_US-NR3_2022_t2m_d2m_sp"
ZIP=DIR/(NAME+".zip")
RECEIPT=DIR/(NAME+".receipt.json")
WANTED={"2m_temperature","2m_dewpoint_temperature","surface_pressure"}
EXPECTED_START="2021-12-29"
EXPECTED_END="2023-01-03"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()

def dates_from_var(var):
    arr=np.asarray(var[:]).reshape(-1)
    units=getattr(var,"units",None)
    calendar=getattr(var,"calendar","standard")
    if not units:
        return None
    if "since" in str(units):
        vals=num2date(arr,units,calendar=calendar,
                      only_use_cftime_datetimes=False,
                      only_use_python_datetimes=True)
        return [str(x) for x in vals]
    return None

def main():
    receipt=json.loads(RECEIPT.read_text())
    if (not ZIP.is_file() or ZIP.is_symlink() or
        receipt["response_sha256"]!=sha(ZIP) or
        Path(receipt["response_file"]).resolve()!=ZIP):
        raise RuntimeError("Pilot ZIP checksum or receipt mismatch")
    print("ZIP HASH PASS",ZIP.name,"bytes",ZIP.stat().st_size)
    req=receipt["request"]
    print("REQUEST DATES:",req["date"])
    print("EXPECTED COVERAGE:",EXPECTED_START,"through",EXPECTED_END)
    total_nt=0
    foundvars=set()
    with zipfile.ZipFile(ZIP) as zf:
        if zf.testzip() is not None: raise RuntimeError("ZIP CRC failed")
        infos=[x for x in zf.infolist() if x.filename.lower().endswith(".nc")]
        if not infos: raise RuntimeError("No NetCDF members")
        for info in infos:
            if info.file_size>800_000_000: raise RuntimeError("Member too large for in-memory audit")
            print("\nNETCDF MEMBER:",info.filename,"uncompressed bytes",info.file_size)
            data=zf.read(info)
            with Dataset("inmemory.nc",mode="r",memory=data) as ds:
                print("DIMENSIONS:",{k:len(v) for k,v in ds.dimensions.items()})
                print("VARIABLES:",list(ds.variables))
                for key,v in ds.variables.items():
                    name=key.lower()
                    standard=str(getattr(v,"standard_name","")).lower()
                    longname=str(getattr(v,"long_name","")).lower()
                    if name in ("t2m","d2m","sp","2m_temperature","2m_dewpoint_temperature","surface_pressure"):
                        print("MET FIELD:",key,"units=",getattr(v,"units",None),"shape=",v.shape)
                        foundvars.add(key)
                    if name in ("time","valid_time","datetime") or standard=="time":
                        dates=dates_from_var(v)
                        print("TIME AXIS:",key,"units=",getattr(v,"units",None),"length=",len(v))
                        if dates:
                            total_nt+=len(dates)
                            print("TIME FIRST:",dates[0],"LAST:",dates[-1])
                            if len(dates)>=2:
                                print("FIRST FEW:",dates[:3])
                        else:
                            print("TIME: non-CF or missing units; manual inspection required")
                    if name in ("latitude","longitude","lat","lon"):
                        sample=np.asarray(v[:]).reshape(-1)
                        print("COORD:",key,"first=",sample[:5].tolist(),
                              "units=",getattr(v,"units",None))
    print("\nCOVERAGE FINDING: reported time-axis entries across members =",total_nt)
    print("FIELD NAMES FOUND:",sorted(foundvars))
    if total_nt<8700:
        print("HOLD_INCOMPLETE: fewer than 8700 hourly entries; this is NOT a validated full-year pilot")
    else:
        print("REVIEW: >=8700 time entries exist; validate uniqueness, full UTC range and variable-specific coverage before use")
    print("AUDIT ONLY: no source files or candidate data modified")

if __name__=="__main__":main()

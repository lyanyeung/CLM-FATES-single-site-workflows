#!/usr/bin/env python3
"""OzFlux Stage14: preserve Stage12 files; write NEW provisional FSDS0 variants.

--preview: ONLY report JSON/TSV; --write-candidate: requires exact confirmation,
copies all six known Stage12 files to a fresh HOME directory and zeroes exactly
360 source-audited negative-FSDS half-hours. No source edits or model submission.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import netCDF4
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SOURCE=ROOT/"AU-ASM/forcing/raw/AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc"
SHA="b9381c4ed0744d03ae609cfbf3805e30bbb9223851a05f4e5b63b149dd0b10eb"
BASE=Path("/iridisfs/home/ly3n24/ozflux_ASM_PROVISIONAL_DATM_20261101T182517Z")
STAGE13=Path("/iridisfs/home/ly3n24/ozflux_stage13_20261102T010205Z")
YEARS=tuple(range(2013,2019))
CONFIRM="CREATE_ONLY_AU_ASM_360_NIGHT_FSDS_ZERO_CANDIDATES"
VARS=("time","lat","lon","LATIXY","LONGXY","ZBOT",
      "TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms")
COLS=("year","candidate_index","source_index","original_FSDS_Wm2",
      "replacement_FSDS_Wm2","source_Fsd_QCFlag",
      "solar_elevation_hypothesis_deg","regime","delta_Jm2")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def records(p):
    with p.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def values(ds,key):
    return np.ma.asarray(ds.variables[key][:],dtype=np.float32).filled(np.nan)

def selftest():
    assert float(np.float32(-7.257902999373263))==-7.257903099060059
    assert Counter(["deep"]*345+["twilight"]*15)=={"deep":345,"twilight":15}
    assert len(VARS)==13 and len(YEARS)==6
    print("STAGE14 SELF-TEST PASS: exact float32 and 360-row negative-only rules; NO WRITES")

def source_audit(candidates,stage13):
    d=json.loads((stage13/"stage13_ASM_candidate_QC_summary.json").read_text())
    if (d.get("source_file_sha256")!=SHA or d.get("science_approval") is not False
        or d.get("number_of_candidate_files")!=6
        or d.get("number_of_negative_FSDS_records")!=360):
        raise ValueError("Stage13 exact source provenance not verified")
    manifest=json.loads((candidates/"stage12_ASM_candidate_manifest.json").read_text())
    expected={str(candidates/f"AU-ASM_PROVISIONAL_DATM_{y}.nc") for y in YEARS}
    if (manifest.get("source_sha256")!=SHA
        or manifest.get("operation")!="PROVISIONAL_NETCDF_WRITTEN"
        or manifest.get("science_approval") is not False
        or manifest.get("model_submission_authorised") is not False
        or set(manifest.get("provisional_DATM_files",[]))!=expected):
        raise ValueError("Stage12 exact six-file candidate manifest not verified")
    stage_rows=records(stage13/"stage13_ASM_360_negative_FSDS.tsv")
    if len(stage_rows)!=360:
        raise ValueError("Stage13 source ledger not 360 rows")
    corrections={y:{} for y in YEARS}
    reg=Counter()
    qc=Counter()
    energy={y:0. for y in YEARS}
    ledger=[]
    for r in stage_rows:
        y=int(r["year"]);i=int(r["candidate_index"])
        if y not in corrections or not 0<=i<17520 or i in corrections[y]:
            raise ValueError("Invalid or repeated source-index mapping")
        old=float(r["candidate_FSDS_Wm2"])
        source=float(r["source_Fsd_Wm2"])
        flag=int(float(r["source_Fsd_QCFlag"]))
        elev=float(r["solar_elevation_deg_under_hypothesis"])
        regime=r["solar_regime_hypothesis"]
        expected_regime=("below_minus6" if elev<=-6 else
                         "minus6_to0" if elev<=0 else "above0")
        if not (-8<=old<0 and old==float(np.float32(source)) and elev<0
                and regime==expected_regime):
            raise ValueError("Value, source relationship or solar evidence changed")
        if not ((y==2014 and flag==420) or (y==2016 and flag==50)):
            raise ValueError("Unexpected original source Fsd QCFlag")
        corrections[y][i]=np.float32(old)
        reg[regime]+=1;qc[(y,flag)]+=1
        change=-old*1800
        energy[y]+=change
        ledger.append({
            "year":y,"candidate_index":i,"source_index":int(r["source_index"]),
            "original_FSDS_Wm2":old,"replacement_FSDS_Wm2":0.,
            "source_Fsd_QCFlag":flag,"solar_elevation_hypothesis_deg":elev,
            "regime":regime,"delta_Jm2":change})
    if (qc!={(2014,420):359,(2016,50):1}
        or reg!={"below_minus6":345,"minus6_to0":15}):
        raise ValueError("Science gate: year/QC/night-twilight counts changed")
    if (abs(energy[2014]/1e6-3.0701117704868315)>1e-6
        or abs(energy[2016]/1e6-0.013064225578308105)>1e-7):
        raise ValueError("Stage13 independently reported energy deltas disagree")
    hashes={}
    for year in YEARS:
        file=candidates/f"AU-ASM_PROVISIONAL_DATM_{year}.nc"
        if file.is_symlink() or not file.is_file():
            raise FileNotFoundError(file)
        hashes[str(year)]=sha256(file)
        with netCDF4.Dataset(str(file),"r") as ds:
            if (getattr(ds,"source_sha256",None)!=SHA
                or getattr(ds,"science_approval",None)!="FALSE"
                or getattr(ds,"model_submission_authorised",None)!="FALSE"
                or int(ds.forcing_year)!=year):
                raise ValueError("Stage12 source/approval provenance inconsistent")
            if len(ds.dimensions["time"])!=17520 or ds.variables["time"].calendar!="noleap":
                raise ValueError("Time/cadence length discrepancy")
            if not all(v in ds.variables for v in VARS):
                raise ValueError("Incomplete DATM variables")
            fsds=values(ds,"FSDS").reshape(-1)
            if not np.isfinite(fsds).all():
                raise ValueError("Nonfinite source FSDS")
            actual=np.flatnonzero(fsds<0)
            expected_ix=np.array(sorted(corrections[year]),dtype=int)
            if not np.array_equal(actual,expected_ix):
                raise ValueError("Correction would touch undocumented negative FSDS")
            for i,original in corrections[year].items():
                if fsds[i]!=original:
                    raise ValueError("Source FSDS differs from Stage13 original")
    return corrections, energy, hashes, ledger

def write_new_files(folder,original,corrections,hashes):
    outputs=[]
    for year in YEARS:
        src=original/f"AU-ASM_PROVISIONAL_DATM_{year}.nc"
        dest=folder/f"AU-ASM_FSDS0_PROVISIONAL_DATM_{year}.nc"
        if dest.exists():raise FileExistsError(dest)
        shutil.copyfile(src,dest)
        indices=np.array(sorted(corrections[year]),dtype=int)
        with netCDF4.Dataset(str(dest),"r+") as new:
            if len(indices):
                new.variables["FSDS"][indices,0,0]=np.float32(0)
            new.setncattr("stage14_FSDS0_is_provisional","TRUE")
            new.setncattr("stage14_negative_FSDS0_count",len(indices))
            new.setncattr("stage14_original_candidate_sha256",hashes[str(year)])
            new.setncattr("stage14_source_ledger","Stage13 360 native-source FSDS negatives, all solar elevation <0")
            new.setncattr("science_approval","FALSE")
            new.setncattr("model_submission_authorised","FALSE")
        with netCDF4.Dataset(str(src),"r") as before, netCDF4.Dataset(str(dest),"r") as after:
            for name in VARS:
                x=values(before,name)
                z=values(after,name)
                if name=="FSDS":
                    x=np.array(x,copy=True)
                    if len(indices):x[indices,0,0]=np.float32(0)
                    if np.any(z<0):
                        raise ValueError("New candidate still has negative FSDS")
                if x.shape!=z.shape or not np.array_equal(x,z):
                    raise ValueError(f"{year}: unexpected modification of {name}")
            if (getattr(after,"source_sha256",None)!=SHA
                or getattr(after,"science_approval",None)!="FALSE"
                or getattr(after,"model_submission_authorised",None)!="FALSE"):
                raise ValueError("Output provenance missing")
        if sha256(src)!=hashes[str(year)]:
            raise ValueError("Original source-faithful candidate changed")
        print("VERIFIED",year,"FSDS_ZEROED",len(indices),"ALL_OTHER_VARIABLES_EXACT")
        outputs.append({"year":year,"path":str(dest),"sha256":sha256(dest),
                        "negative_FSDS_zeroed":len(indices)})
    return outputs

def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--original-candidates",type=Path,default=BASE)
    p.add_argument("--stage13",type=Path,default=STAGE13)
    p.add_argument("--out",type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview",action="store_true")
    mode.add_argument("--write-candidate",action="store_true")
    p.add_argument("--confirm")
    a=p.parse_args()
    src=a.source.resolve()
    original=a.original_candidates.resolve()
    stage13=a.stage13.resolve()
    out=a.out.resolve()
    root=ROOT.resolve()
    if (a.out.is_symlink() or out.exists() or out==src or out==root
        or root in out.parents or out==original or original in out.parents
        or out==stage13 or stage13 in out.parents):
        raise ValueError("Output must be unused and outside all source/report/candidate trees")
    if a.write_candidate and a.confirm!=CONFIRM:
        raise ValueError("Explicit user approval required: --confirm "+CONFIRM)
    if a.source.is_symlink() or not src.is_file() or sha256(src)!=SHA:
        raise ValueError("Original L6 source SHA256 invalid")
    corrections,energy,hashes,ledger=source_audit(original,stage13)
    out.mkdir(parents=True,exist_ok=False)
    generated=write_new_files(out,original,corrections,hashes) if a.write_candidate else []
    with (out/"stage14_exact_360_FSDS0_ledger.tsv").open("w",newline="",encoding="utf-8") as fd:
        writer=csv.DictWriter(fd,fieldnames=COLS,delimiter="\t",extrasaction="ignore")
        writer.writeheader();writer.writerows(ledger)
    result={
        "stage":"OzFlux AU-ASM Stage14",
        "mode":"WRITTEN_NEW_PROVISIONAL_FILES" if generated else "PREVIEW_REPORT_ONLY",
        "science_approval":False,"model_submission_authorised":False,
        "original_L6_sha256":SHA,
        "original_Stage12_candidate_sha256":hashes,
        "original_sources_untouched":True,
        "unapproved_time_basis":"Australia/Darwin local END minus 585 minutes to UTC center",
        "FSDS0_only_under_modelled_solar_below_horizon":True,
        "negative_counts_by_year":{str(y):len(corrections[y]) for y in YEARS},
        "additional_shortwave_energy_MJ_m2":{str(y):energy[y]/1e6 for y in YEARS},
        "correction_rows":len(ledger),"new_outputs":generated,
        "PFT_soil_surface_NOT_approved":True,
    }
    (out/"stage14_FSDS0_provisional_manifest.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    if sha256(src)!=SHA or any(
        sha256(original/f"AU-ASM_PROVISIONAL_DATM_{y}.nc")!=hashes[str(y)] for y in YEARS
    ):
        raise ValueError("Read-only input integrity check failed after audit")
    print("STAGE14",result["mode"],len(generated),"NEW_NETCDF",len(ledger),"CORRECTIONS")
    print("ENERGY_DELTA_MJ_M2",result["additional_shortwave_energy_MJ_m2"])
    print("SCIENCE_APPROVAL FALSE; NO MODEL JOBS; ORIGINAL FILES UNCHANGED")
    print("REPORT_DIR",out)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

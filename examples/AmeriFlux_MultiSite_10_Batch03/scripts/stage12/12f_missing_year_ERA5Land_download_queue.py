#!/usr/bin/env python3
"""Stage12f — SHA-pinned NEW yearly ERA5-Land evidence queue for 2810 US Batch03 holds.

Precisely the 2810/3670 Stage12e still-held source-native humidity events
with reason NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR. Aggregate by station,
calendar year, and rank expected benefit. Reuse the 32 verified original
Stage09a site/year products and their exact original point coordinates.

--self-test : synthetic controls and exact source counts, no disk/API writes.
--check     : full SHA verification for Stage12e report/source/Stage09a point
              coordinates; inspect missing-year CDS queue; NO writes/API.
--download --max-new 1..3 : download up to 3 highest-benefit MISSING new
              site-years, each in separate NEW external evidence directory.
              Verify complete 2-year-edge padded hourly T2M/D2M/SP
              NetCDF, gridded point coordinate, physical bounds and SHA.
              Never overwrite a partial, receipt or original input.

This is ONLY new unpaired ERA5-Land external evidence. It does not select
the site's true clock, fix source temperatures, convert site timestamps,
apply VPD/QBOT, alter Stage12e or create any model job.
"""
import argparse, hashlib, importlib.util, json, os, sys, traceback
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VERSION="batch03-stage12f-v1-20261024-2810-missing-source-year-CDS-queue"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
E=ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
OUT=ROOT/"external_evidence/era5land_timeseries_stage12f_missing_years"
E_SCRIPT=BASE/"scripts/stage12/12e_six_site_independent_ERA5Land_gap_rescue.py"
E_BLOB="cb5b38257d9a34fefc974678dadc67fe93eac9f1"
B_SCRIPT=BASE/"scripts/stage09/09b_download_era5land_pilot.py"
B_BLOB="b087fdc0e0eb7435d25c382d17bd8e1c85b7f000"
SITES=("US-NR3","US-Kon","US-NR1","US-MMS","US-MtB","US-Me6")
EXPECT={"US-NR3":6,"US-Kon":211,"US-NR1":135,
        "US-MMS":15,"US-MtB":2363,"US-Me6":80}
ALLOWED={"2m_temperature","2m_dewpoint_temperature","surface_pressure"}
REASON="NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR"
SOURCE_FILE="remaining_4372_source_second_ERA5Land_holds.csv"
DATASET="reanalysis-era5-land-timeseries"
PREVIOUS_KEYS={
    "new_site_year_gridRH_repair_candidates.csv",
    SOURCE_FILE,"six_site_post_stage12e_humidity_status.csv","SCIENTIFIC_HOLD.md"
}

def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink immutable source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def gitblob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load(path,digest,name):
    if gitblob(path)!=digest:
        raise ValueError("Previously reviewed Git blob unexpectedly changed: "+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def self_test():
    assert sum(EXPECT.values())==2810 and set(EXPECT)==set(SITES)
    assert len(PREVIOUS_KEYS)==4 and len(ALLOWED)==3
    assert "2025-03-01"==datetime.strptime("20250301","%Y%m%d").strftime("%Y-%m-%d")
    # Regression: original seven-site Stage09a has 32 years, while
    # Stage12e returns only the subset of six-site source-years.
    fake=[{"site":"US-NR3","year":year} for year in range(1990,2021)]
    fake.append({"site":"US-Me2","year":2022})
    six={(r["site"],r["year"]):("verified",{}) for r in fake if r["site"] in SITES}
    assert checked_six_site_catalog(fake,six)==31
    try:
        checked_six_site_catalog(fake,{})
    except ValueError:
        pass
    else:
        raise AssertionError("Unverified six-site evidence unexpectedly accepted")
    print("STAGE12F SELF-TEST PASS: six sites 2810 missing-source holds, seven-site vs six-site catalog regression, max 3 CDS requests, untouched site time/T, zero writes",flush=True)

def checked_six_site_catalog(original_seven_site_plan,verified_six_site_catalog):
    if len(original_seven_site_plan)!=32:
        raise ValueError("Original SHA-pinned Stage09a source plan no longer lists 32 seven-site years")
    full=[(p["site"],int(p["year"])) for p in original_seven_site_plan]
    if len(set(full))!=32:
        raise ValueError("Original Stage09a seven-site source-year identities duplicated")
    if not any(site=="US-Me2" for site,_ in full):
        raise ValueError("Original Stage09a source-year plan unexpectedly excludes US-Me2")
    expected={key for key in full if key[0] in SITES}
    observed=set(verified_six_site_catalog)
    if observed!=expected:
        missing=sorted(expected-observed)
        extra=sorted(observed-expected)
        raise ValueError("Six-site SHA-verified catalog differs from 32-year Stage09a plan; missing="+str(missing)+" extra="+str(extra))
    return len(expected)

def evidence():
    if not E.is_dir() or E.is_symlink():
        raise ValueError("Sealed Stage12e research trial missing")
    regular(E/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    receipt=json.loads(regular(E/"stage12e_research_only_sha_receipt.json").read_text())
    if (receipt.get("version")!="batch03-stage12e-v1-20261024-existing-yearly-ERA5Land-RH-source-rescue"
        or receipt.get("new_alternative_yearly_grid_RH_patches")!=702
        or receipt.get("original_unresolved_additional")!=4372
        or receipt.get("remaining_unresolved_additional")!=3670
        or receipt.get("original_233_science_holds_unchanged") is not True
        or receipt.get("six_full_native_ERA5Land_research_shadows")!=6
        or receipt.get("site_T_P_time_unchanged") is not True
        or receipt.get("source_UTC_offset_approved") is not False
        or receipt.get("Postv5_approved")!=0 or receipt.get("DATM_ready")!=0
        or receipt.get("spinup_authorized")!=0
        or receipt.get("INCOMPLETE_marker_present") is not True
        or not PREVIOUS_KEYS<=set(receipt.get("output_sha256",{}))):
        raise ValueError("Stage12e source receipt data/gates unexpected")
    for filename,digest in receipt["output_sha256"].items():
        if sha(E/filename)!=digest:
            raise ValueError("Previous SHA-sealed Stage12e result modified: "+filename)
    e_mod=load(E_SCRIPT,E_BLOB,"stage12e_pinned_12f")
    pilot=load(B_SCRIPT,B_BLOB,"stage09b_pinned_12f")
    t,d,specs,ledger,years,rec=e_mod.verify()
    # Stage10b/09f originally verified ALL 32 seven-site source-years;
    # Stage12e.verify() deliberately returns a CATALOG FILTERED TO SIX
    # target sites, excluding US-Me2. A six-site catalog is NOT 32 rows.
    priorplan=t.load_queue().read_source()
    checked_six_site_catalog(priorplan,years)
    positions={}
    for x in priorplan:
        site=x["site"]
        if site not in SITES:continue
        loc=x["request"]["location"]
        coords=(float(loc["latitude"]),float(loc["longitude"]))
        if site in positions and positions[site]!=coords:
            raise ValueError("Original SHA-pinned Stage09a location disagreement at "+site)
        positions[site]=coords
    if set(positions)!=set(SITES):
        raise ValueError("Original Stage09a request cannot ground locations for all six sites")
    holds=pd.read_csv(regular(E/SOURCE_FILE),dtype={"site":str,"native_key":str},
                      low_memory=False)
    if (len(holds)!=3670 or holds.duplicated(["site","native_key"]).any() or
        set(holds.site)!=set(SITES) or
        holds.loc[holds.science_hold_reason.eq(REASON),"site"].value_counts().to_dict()!=EXPECT):
        raise ValueError("New Stage12e 2810 missing-year source identity/count differs")
    missing=holds.loc[holds.science_hold_reason.eq(REASON)].copy()
    dt=pd.to_datetime(missing.native_key,format="%Y%m%d%H%M",errors="raise")
    missing["year"]=dt.dt.year.astype(int)
    # Reject Stage10b existing fully verified site-year mistakenly reported
    # as no source: fail closed, do not download duplicates.
    groups=missing.groupby(["site","year"]).size().sort_values(ascending=False)
    if any((site,int(year)) in years for site,year in groups.index):
        raise ValueError("No-verified-year stage12e reason conflicts with existing 32-year source")
    expectedplan=[]
    for (site,year),n in groups.items():
        if not 1990<=int(year)<=2026 or int(n)<=0:
            raise ValueError("Unexpected source calendar year / count")
        lat,lon=positions[site]
        request={
            "variable":["2m_temperature","2m_dewpoint_temperature","surface_pressure"],
            "date":[f"{int(year)-1}-12-29",f"{int(year)+1}-01-03"],
            "location":{"latitude":lat,"longitude":lon},
            "data_format":"netcdf"
        }
        expectedplan.append({"site":site,"year":int(year),"unresolved_humidity":int(n),
            "request":request,"hypothesized_published_UTC_offset":int(t.BIF_OFFSET[site]),
            "clock_approved":False,"humidity_correction_approved":False,
            "grounded_source":"SHA-PINNED_STAGE09A_LOCATION"})
    assert sum(x["unresolved_humidity"] for x in expectedplan)==2810
    return expectedplan,t,pilot,receipt

def validate_physics(variables):
    if set(variables)!={"t2m","d2m","sp"}:
        raise ValueError("ERA5-Land source variables missing")
    ta=np.asarray(variables["t2m"],dtype=float)
    td=np.asarray(variables["d2m"],dtype=float)
    pa=np.asarray(variables["sp"],dtype=float)
    if (not (np.isfinite(ta).all() and np.isfinite(td).all()
             and np.isfinite(pa).all())
        or not ((ta>=160)&(ta<=340)).all()
        or not ((td>=160)&(td<=340)).all()
        or not ((td<=ta+0.1)).all()
        or not ((pa>=50000)&(pa<=110000)).all()):
        raise ValueError("Downloaded ERA5-Land humidity/temperature/pressure physical QA failed")

def target(item):
    folder=OUT/item["site"]/str(item["year"])
    stem="ERA5Land_"+item["site"]+"_"+str(item["year"])+"_stage12f_t2m_d2m_sp"
    return folder,stem

def status(item,t):
    folder,stem=target(item)
    if folder.is_symlink():
        raise ValueError("Unsafe source folder symlink: "+str(folder))
    nc=folder/(stem+".nc")
    z=folder/(stem+".zip")
    receipt=folder/(stem+".receipt.json")
    partial=folder/(stem+".download.partial")
    stage=folder/(stem+".validation.nc")
    stagezip=folder/(stem+".validation.zip")
    forbidden=[x for x in (partial,stage,stagezip) if x.exists()]
    existing=[x for x in (nc,z) if x.exists()]
    if not existing and not receipt.exists() and not forbidden:
        return "MISSING",None
    if forbidden or len(existing)!=1 or not receipt.is_file() or receipt.is_symlink():
        raise ValueError("Incomplete or ambiguous earlier CDS request; manual file inspection: "+str(folder))
    result=regular(existing[0])
    r=json.loads(receipt.read_text())
    if (r.get("version")!=VERSION
        or r.get("site")!=item["site"] or int(r.get("year",-1))!=item["year"]
        or r.get("request")!=item["request"]
        or r.get("dataset")!=DATASET or r.get("artifact_sha256")!=sha(result)
        or r.get("source_Stage12e_receipt_SHA256")!=sha(E/"stage12e_research_only_sha_receipt.json")
        or r.get("artifact_path")!=str(result)
        or r.get("tower_clock_approved") is not False
        or r.get("scientific_repair_approved") is not False):
        raise ValueError("Previously downloaded Stage12f source receipt SHA/request mismatch")
    pos=item["request"]["location"]
    years,fields,coords=t.grid_fields(result,item["year"],
                             (pos["latitude"],pos["longitude"]))
    if not len(years)>8760:
        raise ValueError("Downloaded source missing expected UTC hourly coverage")
    validate_physics(fields)
    return "VERIFIED",{"path":str(result),"sha256":sha(result),
                        "utc_hours":len(years),"grid":coords}

def download(item,t,pilot,stage12e_receipt_sha):
    state,meta=status(item,t)
    if state!="MISSING":
        raise RuntimeError("Refusing new download for non-missing year: "+str((item["site"],item["year"])))
    if importlib.util.find_spec("cdsapi") is None:
        raise RuntimeError("Missing cdsapi; install in current environment")
    if not ((Path.home()/".cdsapirc").is_file() or os.getenv("CDSAPI_KEY")):
        raise RuntimeError("CDS credentials absent; no API request made")
    import cdsapi
    folder,stem=target(item)
    folder.mkdir(parents=True,exist_ok=True)
    if folder.is_symlink():
        raise RuntimeError("Refusing output symlink")
    temp=folder/(stem+".download.partial")
    if temp.exists():raise RuntimeError("Partial preexists: "+str(temp))
    print("STAGE12F CDS REQUEST:",item["site"],item["year"],
        item["unresolved_humidity"],item["request"]["date"],flush=True)
    cdsapi.Client().retrieve(DATASET,item["request"]).download(str(temp))
    ext,meta=pilot.classify_response(temp)
    validation=folder/(stem+".validation"+ext)
    temp.rename(validation)
    pos=item["request"]["location"]
    dt,fields,cell=t.grid_fields(validation,item["year"],
                                (pos["latitude"],pos["longitude"]))
    validate_physics(fields)
    datafile=folder/(stem+ext)
    if datafile.exists():raise FileExistsError("Unexpected destination conflict")
    validation.rename(datafile)
    receipt={
        "version":VERSION,
        "site":item["site"],"year":item["year"],
        "original_missing_humidity_rows":item["unresolved_humidity"],
        "dataset":DATASET,"request":item["request"],
        "source_Stage12e_receipt_SHA256":stage12e_receipt_sha,
        "artifact_path":str(datafile),"artifact_sha256":sha(datafile),
        "utc_hours_verified":len(dt),"grid_latlon":list(cell),
        "tower_clock_approved":False,"scientific_repair_approved":False,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "created_utc":datetime.now(timezone.utc).isoformat()
    }
    output=folder/(stem+".receipt.json")
    with output.open("x") as f:
        json.dump(receipt,f,indent=2)
        f.write("\n")
    verified,_=status(item,t)
    if verified!="VERIFIED":raise ValueError("CDS response did not complete SHA source verification")
    print("STAGE12F NEW SOURCE VERIFIED:",item["site"],item["year"],
          "utc_hours",len(dt),"sha256",sha(datafile),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--download",action="store_true")
    p.add_argument("--max-new",type=int,default=3)
    p.add_argument("--site",choices=list(SITES),default=None)
    a=p.parse_args()
    print("STAGE12F — EXTRA 2810 MISSING ERA5-LAND SITE/YEAR SOURCE INVENTORY | "+VERSION,flush=True)
    self_test()
    if a.self_test:return
    if not 1<=a.max_new<=3:
        raise ValueError("At most 3 new CDS requests per invocation")
    source,t,pilot,rc=evidence()
    states=[]
    for item in source:
        typ,meta=status(item,t)
        states.append((item,typ,meta))
    ready=[row for row,kind,_ in states if kind=="MISSING"
           and (a.site is None or row["site"]==a.site)]
    ready.sort(key=lambda x:(-x["unresolved_humidity"],x["site"],x["year"]))
    selected=ready[:a.max_new]
    print("\n========== NEW SOURCE YEAR PRIORITY ==========",flush=True)
    print("Missing ERA5-Land native half-hours:",sum(x["unresolved_humidity"] for x in source),
          "site_years:",len(source),
          "verified_stage12f_years:",sum(kind=="VERIFIED" for _,kind,_ in states),
          "still_missing_stage12f_years:",sum(kind=="MISSING" for _,kind,_ in states),flush=True)
    print(pd.DataFrame([{
        "site":x["site"],"year":x["year"],
        "affected_native_halfhours":x["unresolved_humidity"],
        "state":kind,
        "existing_sha256":meta["sha256"] if meta else "-"
    } for x,kind,meta in states]).sort_values(
        "affected_native_halfhours",ascending=False).to_string(index=False),flush=True)
    print("\n========== NEXT DOWNLOADS ==========",flush=True)
    for row in selected:
        print("NEXT:",row["site"],row["year"],
              "affected_native_halfhours",row["unresolved_humidity"],
              "date",row["request"]["date"],flush=True)
    print("WARNING: derived source native UTC offsets are unapproved hypotheses.",
          "No site temperature/clock/forcing edits.",flush=True)
    if a.check:
        print("CHECK ONLY: zero CDS requests, zero file writes.",flush=True)
        return
    if not selected:
        print("STAGE12F NO NEW REQUESTS REQUIRED FOR SELECTED SCOPE.",flush=True)
        return
    for row in selected:
        download(row,t,pilot,sha(E/"stage12e_research_only_sha_receipt.json"))
    print("STAGE12F BATCH SUMMARY: verified_new_source_site_years="+str(len(selected)),
          "no_forcing_writes=True clock_approved=0 Postv5_approved=0 DATM_ready=0 spinup=0",
          flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12F STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

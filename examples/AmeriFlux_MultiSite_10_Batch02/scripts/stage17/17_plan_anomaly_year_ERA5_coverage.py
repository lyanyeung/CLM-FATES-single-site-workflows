#!/usr/bin/env python3
"""Stage17 READ-ONLY: plan the ERA5 years required by the 4,884 exact Stage11 anomalies.

Choose only SITE/YEAR combinations containing original Stage08 unresolved RH.
Pin Stage11 and Stage13 manifests, Stage15 verified-year receipts, full raw
product checksums and site-local time-offset metadata. Reuse already retrieved
Stage15 five site-years without downloading again.

--check: reads and prints an audit, creates NO files.
--write-plan: creates an isolated reviewed plan under HOME only.
No CDS downloads, forcing modifications, DATM/CIME cases, or Slurm jobs.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pandas as pd

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE11 = BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
STAGE13 = Path.home()/"AmeriFlux_Batch02_stage13_plan_20261022T023406Z_7614f826"/"request_plan.json"
STAGE15 = Path.home()/"AmeriFlux_Batch02_ERA5_five_one_year_controls"
STAGE16 = Path.home()/"AmeriFlux_Batch02_stage16_yearly_dewpoint_20261022T033326Z_b3a24377"
PLAN13_SHA = "0785bb8b85b5e8c9fee7b64d6f63016e58e12db03e31cf53c20e265e803f9523"
YEARS = {"US-EML": (2008, 2023), "US-GLE": (2005, 2020),
         "US-Ho1": (1996, 2023), "US-ICh": (2007, 2025),
         "US-ICt": (2007, 2025)}
FOCUS = {"US-EML":2009, "US-GLE":2005, "US-Ho1":1996,
         "US-ICh":2007, "US-ICt":2007}
BIF_UTC = {"US-EML":-9, "US-GLE":-7, "US-ICh":-9, "US-ICt":-9}

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def load():
    if digest(STAGE13)!=PLAN13_SHA:
        raise ValueError("Original Stage13 plan checksum differs")
    stage13=json.loads(STAGE13.read_text())
    if stage13.get("schema")!="Stage13_ERA5_TD2M_REQUEST_PLAN_v1" or \
       stage13.get("science_status")!="RETRIEVAL_PLAN_ONLY_NO_HUMIDITY_APPROVAL":
        raise ValueError("Stage13 plan contract differs")
    metadata={x["site"]:x for x in stage13["sites"]}
    if set(metadata)!=set(YEARS):
        raise ValueError("Stage13 five-site set changed")
    if not (STAGE11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage11 science HOLD marker missing")
    m=json.loads((STAGE11/"manifest.json").read_text())
    if m.get("n_target_rows")!=4884 or m.get("scientific_status")!="HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Stage11 target scope differs")
    info=json.loads((Path(m["source_stage08"])/"exact_input_manifest.json").read_text())
    sources={x["site"]:x for x in info["sites"]}
    for site in YEARS:
        if (sources[site]["first_year"],sources[site]["last_year"])!=YEARS[site]:
            raise ValueError("Stage08 first/last year changed: "+site)
        raw=Path(sources[site]["primary"]).resolve()
        if m["input_hashes"].get(str(raw))!=digest(raw):
            raise ValueError("Original meteorology source checksum changed: "+site)
        if site in BIF_UTC:
            bifs=sorted(raw.parent.glob("*_BIF_*.csv"))
            if len(bifs)!=1:raise ValueError("Missing or ambiguous BIF: "+site)
            vals=[]
            with bifs[0].open(encoding="utf-8-sig",newline="") as f:
                for row in csv.DictReader(f):
                    if row.get("VARIABLE","").strip().upper()=="UTC_OFFSET":
                        if row.get("SITE_ID","").strip() not in ("",site):
                            raise ValueError("BIF SITE_ID mismatch: "+site)
                        vals.append(float(row["DATAVALUE"]))
            if vals!=[BIF_UTC[site]]:
                raise ValueError("Unexpected BIF UTC_OFFSET: "+site)
    if not (STAGE15/"STAGE15_PARTIAL_OR_COMPLETE_REVIEW_ONLY").is_file():
        raise ValueError("Stage15 one-year pilot receipts not marked review-only")
    config=json.loads((STAGE15/"config.json").read_text())
    if config.get("stage13_plan_sha256")!=PLAN13_SHA or config.get("focus_years")!=FOCUS:
        raise ValueError("Stage15 focus year config differs")
    if not (STAGE16/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage16 completed review marker missing")
    sm=json.loads((STAGE16/"manifest.json").read_text())
    if sm.get("scientific_status")!="ANNUAL_NUMERICAL_DIAGNOSTICS_ONLY":
        raise ValueError("Stage16 science marker differs")
    return sources,metadata,m

def stage15_receipt(site,year):
    if year!=FOCUS[site]:
        return None
    p=STAGE15/f"{site}_{year}"/"verified_receipt.json"
    r=json.loads(p.read_text())
    if r.get("site")!=site or r.get("year")!=year or \
       r.get("stage13_plan_sha256")!=PLAN13_SHA or r.get("science_approval") is not False:
        raise ValueError("Stage15 receipt metadata differs: "+site)
    for pathkey,hashkey in (("netcdf_path","netcdf_sha256"),
                            ("original_payload_path","original_payload_sha256")):
        path=Path(r[pathkey]).resolve()
        if STAGE15.resolve() not in path.parents or digest(path)!=r[hashkey]:
            raise ValueError("Stage15 byte hash does not match: "+site+" "+pathkey)
    return dict(receipt_path=str(p),receipt_sha256=digest(p),
                netcdf_path=r["netcdf_path"],
                netcdf_sha256=r["netcdf_sha256"])

def main():
    a=argparse.ArgumentParser(description=__doc__)
    mode=a.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--write-plan",action="store_true")
    a.add_argument("--output-root",type=Path)
    args=a.parse_args()
    sources,meta,stage11=load()
    pp=STAGE11/"cold_humidity_repair_proposals.csv"
    if not pp.is_file():raise ValueError("Missing Stage11 proposals CSV")
    table=pd.read_csv(pp)
    if len(table)!=4884 or set(table.site)!=set(YEARS):
        raise ValueError("Stage11 rows/site set differs")
    if table.duplicated(["site","time"]).any():raise ValueError("Stage11 duplicate target timestamp")
    if table.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()!=14 or \
       table.decision.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED").sum()!=4870:
        raise ValueError("Stage11 decision distribution differs")
    table["year"]=pd.to_datetime(table.time,errors="raise").dt.year
    for site,(begin,end) in YEARS.items():
        if not table.loc[table.site.eq(site),"year"].between(begin,end).all():
            raise ValueError("Stage11 anomaly outside tower release coverage: "+site)
    rows=[]
    for (site,year),group in table.groupby(["site","year"],sort=True):
        site=str(site); year=int(year)
        coordinate=meta[site]["metadata"]
        lat=float(coordinate["latitude"]);lon=float(coordinate["longitude"])
        grid=(round(4*lat)/4,round(4*lon)/4)
        prior=stage15_receipt(site,year)
        request=dict(data_format="netcdf",
            date=[f"{year-1}-12-29",f"{year+1}-01-03"],
            location={"latitude":lat,"longitude":lon},
            variable=["2m_temperature","2m_dewpoint_temperature","surface_pressure"])
        rows.append(dict(site=site,year=year,
            n_stage11_targets=len(group),
            n_stage11_provisional=int(group.decision.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED").sum()),
            n_stage11_holds=int(group.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()),
            raw_release=sources[site]["release"],
            year_in_release=True,
            native_minutes=sources[site]["native_minutes"],
            UTC_offset_local_minus_UTC=BIF_UTC.get(site,-5),
            offset_evidence=("ORIGINAL_RELEASE_BIF" if site in BIF_UTC
                             else "EXTERNAL_EASTERN_STANDARD_TIME_HO1_BADM_PENDING"),
            ERA_grid_lat_expected=grid[0],ERA_grid_lon_expected=grid[1],
            existing_Stage15_verified=(prior is not None),
            original_stage15_receipt=prior,
            CDS_dataset="reanalysis-era5-single-levels-timeseries",
            CDS_request=request,
            status="REVIEW_PLAN_ONLY"))
    if sum(r["n_stage11_targets"] for r in rows)!=4884:
        raise ValueError("Incorrect anomaly year partition")
    if sum(r["n_stage11_holds"] for r in rows)!=14:
        raise ValueError("Original fourteen HOLDs not accounted for")
    done=[r for r in rows if r["existing_Stage15_verified"]]
    missing=[r for r in rows if not r["existing_Stage15_verified"]]
    gridyears={(r["ERA_grid_lat_expected"],r["ERA_grid_lon_expected"],r["year"])
               for r in rows}
    print("========== STAGE17 READ-ONLY ANOMALY-YEAR PLAN ==========")
    print("Original Stage11 records: 4884 = 4870 provisional + 14 HOLD")
    print("Site-years containing anomalies:",len(rows))
    print("Verified Stage15 site-years already covered:",len(done))
    print("Original anomalies already covered by Stage15:",
          sum(r["n_stage11_targets"] for r in done))
    print("Site-years needing new ERA5 data:",len(missing))
    print("Distinct nearest ERA5-grid/year combinations:",len(gridyears))
    print("US-ICh and US-ICt share the same grid (NOT independent observations).")
    for site in YEARS:
        subset=[r for r in rows if r["site"]==site]
        ready=[r for r in subset if r["existing_Stage15_verified"]]
        print("SITE",site,"site-years=",len(subset),"already_downloaded=",len(ready),
              "to_download=",len(subset)-len(ready),
              "anomaly_records=",sum(r["n_stage11_targets"] for r in subset),
              "HOLD=",sum(r["n_stage11_holds"] for r in subset))
    print("\nNEXT 12 UNCOVERED SITE-YEARS BY ANOMALY COUNT")
    for row in sorted(missing,key=lambda r:(-r["n_stage11_targets"],r["site"],r["year"]))[:12]:
        print(row["site"],row["year"],"anomalies=",row["n_stage11_targets"],
              "expected ERA5 grid=",row["ERA_grid_lat_expected"],row["ERA_grid_lon_expected"])
    print("IMPORTANT: Stage17 is a RETRIEVAL PLAN, not quality approval, and downloads nothing.")
    if args.check:
        print("CHECK ONLY: no files written")
        return 0
    out=args.output_root.expanduser().resolve() if args.output_root else (
        Path.home()/("AmeriFlux_Batch02_stage17_anomaly_year_plan_"+
                    datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
                    "_"+uuid4().hex[:8]))
    if out.exists() or any(out==b or out in b.parents or b in out.parents
                            for b in (BASE,STAGE15,STAGE16,STAGE11,STAGE13.parent)):
        raise ValueError("Existing or unsafe output root")
    out.mkdir(parents=True,exist_ok=False)
    with (out/"CDS_anomaly_site_year_plan.json").open("x") as f:
        json.dump(dict(schema="STAGE17_ANOMALY_YEAR_RETRIEVAL_PLAN_v1",
            source_stage11=str(STAGE11),
            original_stage11_sha256=digest(pp),
            original_stage11_manifest_sha256=digest(STAGE11/"manifest.json"),
            stage13_plan_sha256=PLAN13_SHA,
            stage15_existing_site_years=len(done),
            stage11_total=4884,stage11_holds=14,
            site_years=rows,
            science_status="ONLY_RETRIEVAL_PLAN_NO_DATM_APPROVAL",
            no_download_or_model_output=True),f,indent=2)
        f.write("\n")
    pd.DataFrame([{k:v for k,v in r.items()
                   if k not in ("original_stage15_receipt","CDS_request")}
                  for r in rows]).to_csv(out/"site_year_coverage.csv",index=False)
    (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage17 retrieval plan only. No forcing, DATM, CIME or spin-up approved.\n")
    print("STAGE17 PLAN:",out/"CDS_anomaly_site_year_plan.json")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

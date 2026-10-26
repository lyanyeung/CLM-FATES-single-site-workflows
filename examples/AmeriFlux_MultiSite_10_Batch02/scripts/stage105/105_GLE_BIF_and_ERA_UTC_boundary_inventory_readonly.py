#!/usr/bin/env python3
"""Stage105 GLE 2005 UTC/2004 local 7h backfill source proof (read only).

Checks original Stage07 independent ERA5 source file, authentic source-local
timestamps, exact 2004 Dec31 local 17:00-23:30 half-hours, GLE actual NC
coordinates vs 2026 BIF new tower metadata. Writes ONLY evidence reports.
Does not infer ERA UTC from locally aligned ERA5_HH or alter model/NC.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import netCDF4 as nc
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S7=R/"qcv5_native_trial_20261022T010124Z_dfae01c2"
S102=R/"reports/stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_20261026T114427Z_e63d3051"
S104=R/"reports/stage104_GLE_CIME_seam_quantiles_READONLY_20261026T121303Z_166e2732"
BIF_LAT=41.3665
BIF_LON=-106.2399
BIF_SHA="9012ac6594cc10d0beb102abb8ee189837835b06ff0d595b122bacd17f231279"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def verify():
    a=read(S102/"manifest.json")
    b=read(S104/"manifest.json")
    if (a["NC_technical_preview_count"]!=16 or
        a["CIME_DATM_approved"] is not False or
        a["source_cyclic_wrap_halfhours"]!=14 or
        b["stage102_sha256"]!=sha(S102/"manifest.json") or
        b["production_DATM_approved"] is not False or
        b["Slurm_jobs_submitted"] is not False):
        raise ValueError("Original Stage102/104 GLE source and scientific HOLD changed")
    for name,v in b["output_SHA256"].items():
        if sha(S104/name)!=v:raise ValueError("Stage104 receipt SHA mismatch")
    orig=read(S7/"exact_input_manifest.json")
    info={x["site"]:x for x in orig["sites"]}["US-GLE"]
    era=Path(info["era"])
    known=orig["input_sha256"].get(str(era.resolve()))
    if not known or not era.is_file() or sha(era)!=known:
        raise ValueError("Exact Stage07 ERA companion missing or SHA mismatched")
    first=next(x for x in read(S102/"16_year_UTC_midpoint_NC_source_manifest.json")
               if x["year"]==2005)
    if sha(first["new"])!=first["sha256"]:raise ValueError("Source GLE 2005 UTC NC changed")
    with nc.Dataset(first["new"]) as f:
        lat=float(f.variables["LATIXY"][0,0])
        lon=float(f.variables["LONGXY"][0,0])
    return era,lat,lon

def inventory(era,lat,lon):
    old=[(datetime(2004,12,31,17)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(14)]
    local2005=[(datetime(2005,1,1)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(14)]
    present=set()
    with era.open(newline="",encoding="utf-8-sig") as f:
        rdr=csv.DictReader(f)
        fields=rdr.fieldnames or []
        if "TIMESTAMP_START" not in fields:raise ValueError("ERA comparison source local timestamp absent")
        early=[];last=[]
        for i,row in enumerate(rdr):
            t=str(row["TIMESTAMP_START"]).strip().removesuffix(".0")
            present.add(t) if t in old or t in local2005 else None
            if i<3:early.append(t)
            last.append(t)
            if len(last)>3:last.pop(0)
    coords={"GLE_current_BIF_lat_lon":[BIF_LAT,BIF_LON],
        "source_NC_lat_lon":[lat,lon],
        "delta_lat_lon":[lat-BIF_LAT,lon-BIF_LON],
        "BIF_location_comment":"Change reflects location of new tower",
        "historic_tower_relocation_reconciled":False}
    result={"original_comparison_csv":str(era),"sha256":sha(era),
        "headers":fields,"first_times":early,"last_times":last,
        "original_missing_2004_local_halfhours":[x for x in old if x not in present],
        "current_comparison_file_2005_local_halfhours":sum(x in present for x in local2005),
        "ERA_comparison_source_2005_local_is_PROVEN_2005_UTC":False,
        "required_external_reanalysis":"ERA5 or ERA5-Land 2005-01-01 UTC 00:00-07:00",
        "science_authorized_backfill":False}
    print("STAGE105 ORIGINAL_ERA_SOURCE",era,flush=True)
    print("STAGE105 SOURCE_FIRST_LAST",early,last,flush=True)
    print("STAGE105 MISSING_2004_LOCAL_EVENING",len(result["original_missing_2004_local_halfhours"]),"/14",flush=True)
    print("STAGE105 2005_LOCAL_COMPANION",result["current_comparison_file_2005_local_halfhours"],
          "/14 | NOT PROVEN UTC PREHISTORY",flush=True)
    print("STAGE105 SOURCE_COORD",lat,lon,"BIF_CURRENT_COORD",BIF_LAT,BIF_LON,
          "TOWER_RELOCATION_HOLD",flush=True)
    print("STAGE105 BIF_PFT ENF | species notes spruce 85pct, fir 15pct;",
          "beetle outbreak peaked 2008, mortality 85pct FOREST BASAL AREA",flush=True)
    return result,coords

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","audit"):g.add_argument("--"+x,action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert datetime(2004,12,31,17)+timedelta(hours=7)==datetime(2005,1,1)
        print("STAGE105 SELF-TEST PASS | 2004 local evening = 2005 Jan1 UTC, no writes")
        return
    era,lat,lon=verify()
    data,coords=inventory(era,lat,lon)
    if a.check:
        print("STAGE105 CHECK PASS | source metadata and exact UTC gap inventory; no writes")
        return
    out=R/"reports"/("stage105_GLE_BIF_2005_UTC_backfill_readonly_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    for name,payload in (("official_GLE_BIF_vs_NC_coords.json",coords),
                         ("source_ERA5_local_timestamp_provenance.json",data)):
        (out/name).write_text(json.dumps(payload,indent=2)+"\n")
    request={"dataset":"reanalysis-era5-land","year":"2005",
        "month":"01","day":"01",
        "time_UTC":[f"{h:02}:00" for h in range(0,15)],
        "original_tower_location_BIF":[BIF_LAT,BIF_LON],
        "required_variables":["2m_temperature","2m_dewpoint_temperature","surface_pressure",
          "10m_u_component_of_wind","10m_v_component_of_wind",
          "surface_solar_radiation_downwards","surface_thermal_radiation_downwards",
          "total_precipitation"],
        "CAUTION":"Review CDS request syntax, UTC provenance, accumulated flux deaccumulation, grid/orography pressure, 10m wind versus tower 22.65m, boundary meteorology and overlap before generating a candidate",
        "CDS_download_executed":False}
    (out/"2005_ERA5_Land_UTC_download_spec_REVIEW_ONLY.json").write_text(
        json.dumps(request,indent=2)+"\n")
    meta={"schema":"STAGE105_GLE_BIF_2005_UTC_GAP_AUDIT_v1",
        "Stage104_manifest_sha256":sha(S104/"manifest.json"),
        "official_BIF_XLSX_SHA256":BIF_SHA,"source_original_2004_local_missing_records":14,
        "production_DATM_approved":False,"ERA_backfill_generated":False,
        "site_FATES_PFT_approved":False,"source_and_case_modified":False,
        "Slurm_submitted":False,
        "output_sha256":{q.name:sha(q) for q in out.iterdir()}}
    (out/"manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    print("STAGE105 REPORT",out,flush=True)
    print("STAGE105 PASS | official BIF and exact 2005 UTC data availability needs verified ERA; NO NC/CIME/SLURM",flush=True)

if __name__=="__main__":main()

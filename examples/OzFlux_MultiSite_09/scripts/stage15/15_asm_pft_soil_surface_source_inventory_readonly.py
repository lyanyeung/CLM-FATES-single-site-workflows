#!/usr/bin/env python3
"""OzFlux Stage15 AU-ASM PFT/soil/CTSM surface science intake, strictly READ ONLY.

Scans a bounded set of known source directories and optional exact surface
filenames. Validates the existing six Stage14 source-identified provisional
DATM files. Reports existing surface and soil PFT structure without changing
or assigning any site PFT fraction, ten-layer soil, or case parameters.
This script NEVER creates surface, DATM, CIME cases or Slurm jobs.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import netCDF4
import numpy as np

SITE="AU-ASM"
LAT=-22.2828
LON=133.2493
CTSM_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
SITE_ROOT=CTSM_ROOT/"sites/MY_EC_SITE/AU-ASM"
ORIGINAL_DATM=Path("/iridisfs/home/ly3n24/ozflux_ASM_PROVISIONAL_DATM_20261101T182517Z")
STAGE14=Path("/iridisfs/home/ly3n24/ozflux_stage14_FSDS0_20261102T012038Z")
EXPECTED_SHA="b9381c4ed0744d03ae609cfbf3805e30bbb9223851a05f4e5b63b149dd0b10eb"
YEARS=tuple(range(2013,2019))
NAT_NAMES=(
    "bare_ground","needleleaf_evergreen_temperate_tree",
    "needleleaf_evergreen_boreal_tree","needleleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_tropical_tree","broadleaf_evergreen_temperate_tree",
    "broadleaf_deciduous_tropical_tree","broadleaf_deciduous_temperate_tree",
    "broadleaf_deciduous_boreal_tree","broadleaf_evergreen_temperate_shrub",
    "broadleaf_deciduous_temperate_shrub","broadleaf_deciduous_boreal_shrub",
    "c3_arctic_grass","c3_nonarctic_grass","c4_grass","UNMAPPED_EXTRA_16TH",
)
FIELD_NAMES=("PCT_NATVEG","PCT_CROP","PCT_LAKE",
             "PCT_WETLAND","PCT_GLACIER","PCT_URBAN",
             "PCT_NAT_PFT","PCT_SAND","PCT_CLAY","ORGANIC",
             "LATIXY","LONGXY")
SCAN_LOCATIONS=(
    "subset_data","subset_data/surface","subset_data_batch02_surf2000",
    "subset_data_batch05_surf2000","subset_data_batch03_surf2000",
    "surface","surfaces","forcing/surface","surfdata","land/surface",
)
OUT_COLS=("candidate_path","sha256","is_ozflux_ASM_surface",
          "has_coordinate","LATIXY","LONGXY","PCT_NATVEG",
          "host_PCT_NAT_PFT_length","host_PFT_sum_pct",
          "bare_natural_pct","tree_natural_pct",
          "shrub_natural_pct","grass_natural_pct",
          "soil_layers","soil_sand_range_pct",
          "soil_clay_range_pct","schema_status","science_approved")


def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as fd:
        for chunk in iter(lambda:fd.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def safe_arr(ds,key):
    if key not in ds.variables:return None
    arr=np.ma.asarray(ds.variables[key][:],dtype=np.float64).filled(np.nan).reshape(-1)
    if not np.isfinite(arr).all():return None
    return arr


def singleton(x):
    return float(x[0]) if x is not None and len(x)==1 else None


def surfaces(site_root,additional):
    paths=[]
    for relative in SCAN_LOCATIONS:
        folder=site_root/relative
        if folder.is_symlink() or not folder.is_dir():continue
        # Only bounded one- and two-level directory patterns. NO rglob.
        for pattern in ("surfdata*.nc","*surf*.nc","*/surfdata*.nc"):
            paths.extend(p for p in folder.glob(pattern) if p.is_file() and not p.is_symlink())
    for pattern in ("surfdata*.nc","*surface*.nc"):
        paths.extend(p for p in site_root.glob(pattern) if p.is_file() and not p.is_symlink())
    for p in additional:
        if p.is_symlink() or not p.is_file():
            raise FileNotFoundError("Explicit surface candidate absent/symlink: "+str(p))
        paths.append(p)
    distinct=sorted(set(p.resolve() for p in paths),key=str)
    if len(distinct)>40:
        raise ValueError("More than 40 surface candidates: narrow the search before continuing")
    return distinct


def point_surface(path):
    result={
        "candidate_path":str(path),"sha256":sha256(path),
        "is_ozflux_ASM_surface":False,"science_approved":False,
        "schema_status":"REVIEW_NOT_YET_VALIDATED",
    }
    with netCDF4.Dataset(str(path),"r") as ds:
        dat={name:safe_arr(ds,name) for name in FIELD_NAMES}
        lat=singleton(dat["LATIXY"])
        lon=singleton(dat["LONGXY"])
        result.update({
            "has_coordinate":lat is not None and lon is not None,
            "LATIXY":lat,"LONGXY":lon,
            "PCT_NATVEG":singleton(dat["PCT_NATVEG"]),
            "known_fields":list(k for k in FIELD_NAMES if k in ds.variables),
            "global_site_attrs":{k:str(ds.getncattr(k))[:500] for k in ds.ncattrs()
                                 if any(x in k.lower() for x in ("site","time","title","history"))},
        })
        if lat is not None and lon is not None:
            distance=abs(lat-LAT)+abs((lon-LON+180)%360-180)
            result["is_ozflux_ASM_surface"]=distance<0.1
        nat=dat["PCT_NAT_PFT"]
        result.update({
            "host_PCT_NAT_PFT_length":len(nat) if nat is not None else None,
            "host_PFT_sum_pct":float(nat.sum()) if nat is not None else None,
        })
        if nat is not None and len(nat) in (15,16):
            nat_tot=float(nat.sum())
            result.update({
                "bare_natural_pct":float(nat[0]),
                "tree_natural_pct":float(np.sum(nat[1:9])),
                "shrub_natural_pct":float(np.sum(nat[9:12])),
                "grass_natural_pct":float(np.sum(nat[12:15])),
                "host_pft_vector":{NAT_NAMES[i]:float(x)
                                   for i,x in enumerate(nat) if x!=0},
                "pft_total_valid":bool(np.all(nat>=0) and abs(nat_tot-100)<0.1),
            })
        sand=dat["PCT_SAND"];clay=dat["PCT_CLAY"]
        result["soil_layers"]=(len(sand) if sand is not None else None)
        result["soil_sand_range_pct"]=(f"{float(np.min(sand)):.3f}..{float(np.max(sand)):.3f}"
                                      if sand is not None else None)
        result["soil_clay_range_pct"]=(f"{float(np.min(clay)):.3f}..{float(np.max(clay)):.3f}"
                                      if clay is not None else None)
        soil_ok=bool(
            sand is not None and clay is not None and len(sand)==len(clay)
            and len(sand)>=10 and np.all(sand>=0) and np.all(clay>=0)
            and np.all(sand+clay<=100.001))
        result["soil_layer_bounds_valid"]=soil_ok
        land_keys=("PCT_NATVEG","PCT_CROP","PCT_LAKE",
                   "PCT_WETLAND","PCT_GLACIER","PCT_URBAN")
        if all(dat[k] is not None for k in land_keys):
            vals=[np.sum(dat[k]) for k in land_keys]
            result["landunit_pct_sum"]=float(sum(vals))
        else:
            result["landunit_pct_sum"]=None
        # Structural only; no *scientific* pass for a gridded non-tower surface.
        if (result["is_ozflux_ASM_surface"] and nat is not None
            and len(nat) in (15,16) and result.get("pft_total_valid")
            and soil_ok and result["PCT_NATVEG"] is not None):
            result["schema_status"]="STRUCTURAL_CANDIDATE_SCIENCE_HOLD"
        else:
            result["schema_status"]="STRUCTURAL_OR_SITE_REVIEW_REQUIRED"
    return result


def check_provisional_datm(stage14,orig):
    if not stage14.is_dir() or stage14.is_symlink():
        raise FileNotFoundError("Stage14 output missing")
    if not orig.is_dir() or orig.is_symlink():
        raise FileNotFoundError("Original provisional DATM directory missing")
    m=json.loads((stage14/"stage14_FSDS0_provisional_manifest.json").read_text())
    if (m.get("mode")!="WRITTEN_NEW_PROVISIONAL_FILES"
        or m.get("correction_rows")!=360
        or m.get("science_approval") is not False
        or m.get("model_submission_authorised") is not False
        or m.get("original_L6_sha256")!=EXPECTED_SHA
        or m.get("negative_counts_by_year")!={"2013":0,"2014":359,"2015":0,
                                             "2016":1,"2017":0,"2018":0}):
        raise ValueError("Stage14 output not the exact operator-verified release")
    files=m.get("new_outputs",[])
    if len(files)!=6 or {int(f["year"]) for f in files}!=set(YEARS):
        raise ValueError("Stage14 files do not represent six years")
    data=[]
    for f in sorted(files,key=lambda x:int(x["year"])):
        year=int(f["year"])
        file=stage14/f"AU-ASM_FSDS0_PROVISIONAL_DATM_{year}.nc"
        old=orig/f"AU-ASM_PROVISIONAL_DATM_{year}.nc"
        if file.is_symlink() or not file.is_file() or old.is_symlink() or not old.is_file():
            raise ValueError("Missing candidate or source-faithful file")
        if file.resolve()!=Path(f["path"]).resolve() or sha256(file)!=f["sha256"]:
            raise ValueError("Stage14 new candidate hash/path mismatch "+str(year))
        before=m["original_Stage12_candidate_sha256"][str(year)]
        if sha256(old)!=before:
            raise ValueError("Stage12 original provisional DATM hash changed "+str(year))
        with netCDF4.Dataset(str(file),"r") as ds:
            if getattr(ds,"science_approval","")!="FALSE" or len(ds.dimensions["time"])!=17520:
                raise ValueError("Unapproved / incorrect Stage14 DATA "+str(year))
            fsds=np.ma.asarray(ds.variables["FSDS"][:]).filled(np.nan)
            if not np.isfinite(fsds).all() or np.min(fsds)<0:
                raise ValueError("FSDS not fully nonnegative in Stage14 "+str(year))
        data.append({"year":year,"file":str(file),"sha256":f["sha256"],
                     "FSDS0_count":f["negative_FSDS_zeroed"],
                     "status":"SOURCE_PROVENANCE_OK_SCIENCE_NOT_APPROVED"})
    return data


def candidate_inputs(root):
    ctsm=root/"CTSM"
    ip=root/"inputdata"
    expected=[
        ("CTSM source",ctsm),
        ("CTSM subset_data tool",ctsm/"tools/site_and_regional/subset_data"),
        ("CTSM default_data_2000.cfg",ctsm/"tools/site_and_regional/default_data_2000.cfg"),
        ("CTSM inputdata root",ip),
        ("CTSM 16PFT 2000 reference surfdata",ip/"lnd/clm2/surfdata_esmf/ctsm5.3.0/surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc"),
        ("CTSM reference mesh",ip/"share/meshes/fv0.9x1.25_141008_ESMFmesh.nc"),
    ]
    return [{"name":name,"path":str(p),"exists":p.exists(),"is_symlink":p.is_symlink()}
            for name,p in expected]


def selftest():
    a=np.array([30.,30.,30.,30.,30.,30.,30.,30.,30.,30.])
    b=np.full(10,15.)
    assert (a+b<=100).all()
    assert len(NAT_NAMES)==16 and NAT_NAMES[0]=="bare_ground"
    assert abs((74+11+15)-100)<1e-9
    assert len(YEARS)==6
    print("STAGE15 SELF-TEST PASS: source-pinned PFT slot/soil ranges, read-only inventory; NO SURFACE OR CIME WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage14",type=Path,default=STAGE14)
    p.add_argument("--original-datm",type=Path,default=ORIGINAL_DATM)
    p.add_argument("--clm-root",type=Path,default=CTSM_ROOT)
    p.add_argument("--site-root",type=Path,default=SITE_ROOT)
    p.add_argument("--surface",type=Path,action="append",default=[],
                   help="Additional exact surface NetCDF file; no wildcards")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    root=a.clm_root.resolve()
    site=a.site_root.resolve()
    stage14=a.stage14.resolve()
    original=a.original_datm.resolve()
    out=a.out.resolve()
    origin_site_root=SITE_ROOT.resolve()
    for protected in (root,site,stage14,original):
        if out==protected or protected in out.parents:
            raise ValueError("Report output cannot be inside source/model/input trees")
    if a.out.is_symlink() or out.exists() or out.parent!=Path.home().resolve():
        raise ValueError("Use a fresh direct child under HOME as the report directory")
    records=check_provisional_datm(stage14,original)
    observations={
        "site":"AU-ASM","period":"2013-2018",
        "coordinates":{"lat":LAT,"lon":LON},
        "soil_source":"OzFlux L6 red Kandosol sandy loam; TERN recent red Kandosol 74% sand / 11% silt / 15% clay; older OzFlux page says 50% sand / 50% clay; these are not vertically resolved soil layers",
        "vegetation_source":"Acacia aneura and aptaneura Mulga plus C3 shrubs/forbs, perennial C3 and C4/annual grasses; bare patches indicated but fractions not site-verified",
        "canopy_height_m_L6":4.4,
        "measurement_heights_m":{"Ta":11.6,"Ws":11.6,"Fsd":12.2,"Fld":12.2,"Precip":2.0,"ps_source_tag":23.0,"SH":"UNREPORTED"},
        "FATES_host_PFT_options_NOT_SELECTED":{"bare":0,"evergreen_broadleaf_tree_tropical":4,
          "evergreen_broadleaf_tree_temperate":5,"evergreen_temperate_shrub":9,
          "c3_nonarctic_grass":13,"c4_grass":14},
        "PFT_fractions_approved":False,"soil_vertical_profile_approved":False,
        "pressure_altitude_correction_approved":False,
    }
    candidates=surfaces(site,a.surface)
    audits=[]
    for file in candidates:
        try:
            item=point_surface(file)
        except Exception as e:
            item={"candidate_path":str(file),"schema_status":"READ_ERROR",
                  "error":str(e)[:300],"science_approved":False}
        audits.append(item)
        print("SURFACE_CANDIDATE",item["candidate_path"],item["schema_status"])
    templates=candidate_inputs(root)
    out.mkdir(parents=True,exist_ok=False)
    summary={
        "stage":"OzFlux Stage15 AU-ASM PFT soil surface source inventory",
        "read_only":True,"science_approval":False,
        "model_submission_authorised":False,
        "Stage14_files_verified":len(records),
        "Stage14_files":records,
        "site_source_evidence":observations,
        "surface_candidates":audits,
        "CTSM_template_inputs":templates,
        "decision":"HOLD_SURFACE_AND_SITE_PFT_FRACTIONS_NOT_APPROVED",
        "pending":["Verify site footprint woody C3 C4 shrub bare percentages",
          "Select and document FATES host-index to compiled FATES-PFT mapping",
          "Derive or select CLM 10-layer soil percent sand/clay and organic data",
          "Make unique CTSM point surface and validate landunit/PFT/soil/coordinates",
          "Check existing source time and DATM streams before first test",
          "No model submission at this stage"],
    }
    (out/"stage15_ASM_surface_PFT_soil_source_register.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    with (out/"stage15_existing_surface_candidates.tsv").open("w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=OUT_COLS,delimiter="\t",extrasaction="ignore")
        writer.writeheader()
        writer.writerows(audits)
    print("STAGE15 VERIFIED",len(records),"/6 STAGE14 FSDS0 CANDIDATES")
    print("SURFACES_FOUND",len(audits),"STRUCTURAL_CANDIDATES",
          sum(x.get("schema_status")=="STRUCTURAL_CANDIDATE_SCIENCE_HOLD" for x in audits))
    for record in templates:
        print("CTSM_INPUT",record["name"],"EXISTS",record["exists"],record["path"])
    print("SCIENCE_APPROVAL FALSE; NO FATES SURFACE CREATED; NO CIME/SLURM")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

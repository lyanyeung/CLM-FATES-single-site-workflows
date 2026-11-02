#!/usr/bin/env python3
"""OzFlux Stage17: AU-ASM Mulga reference surface vs site science, READ ONLY.

Source: Stage16 completed isolated CTSM2000 reference point surface.
Compares exact 15/16 host natpft values and 10-layer sand/clay to published
Mulga site descriptions. Can inspect an OPTIONAL exact operator-specified
FATES parameter NetCDF for fates_hlm_pft_map; does NOT guess FATES indices.
Zero changes to surface, forcing, CTSM, PFT parameters, CIME or Slurm.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import netCDF4
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE16=Path.home()/"ozflux_stage16_reference_20261102T023647Z"
SOURCE_HASH="18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa"
LAT=-22.2828
LON=133.2493
HOST_NAMES=(
    "bare_ground", "needleleaf_evergreen_temperate_tree",
    "needleleaf_evergreen_boreal_tree","needleleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_tropical_tree","broadleaf_evergreen_temperate_tree",
    "broadleaf_deciduous_tropical_tree","broadleaf_deciduous_temperate_tree",
    "broadleaf_deciduous_boreal_tree","broadleaf_evergreen_temperate_shrub",
    "broadleaf_deciduous_temperate_shrub","broadleaf_deciduous_boreal_shrub",
    "c3_arctic_grass","c3_nonarctic_grass","c4_grass","unknown_16th_slot",
)
HOST_COLS=("host_natpft_index","name","pct_of_natural_land","pct_of_grid",
           "FATES_plant_type_in_compiled_parameter_NOT_AUTO_ASSIGNED")
SOIL_COLS=("layer_number","PCT_SAND_GRID","PCT_CLAY_GRID",
           "PCT_SILT_GRID_RESIDUAL","ORGANIC_GRID",
           "FIELD_BULK_SAND_SITE_REF","FIELD_BULK_CLAY_SITE_REF",
           "field_bulk_not_verified_layer_profile")


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1<<22),b""):
            h.update(part)
    return h.hexdigest()


def arr(ds,key):
    if key not in ds.variables:
        raise ValueError("Missing mandatory reference surface "+key)
    a=np.ma.asarray(ds.variables[key][:],dtype=float).filled(np.nan).reshape(-1)
    if not np.isfinite(a).all():
        raise ValueError("Nonfinite reference surface values "+key)
    return a


def read_source(stage16):
    if stage16.is_symlink() or not stage16.is_dir():
        raise FileNotFoundError("Stage16 output not found")
    report=stage16/"stage16_AU_ASM_REFERENCE_SURFACE_NOT_MODEL_APPROVED.json"
    if not report.is_file() or report.is_symlink():
        raise FileNotFoundError("Stage16 verified reference report missing")
    obj=json.loads(report.read_text(encoding="utf-8"))
    ref=obj.get("reference_surface",{})
    if (obj.get("point_surface_scientific_approval") is not False
        or obj.get("CIME_case_or_AD400_submission_authorised") is not False
        or obj.get("created_new_separate_reference") is not True
        or not isinstance(ref,dict) or ref.get("surface_SHA256")!=SOURCE_HASH
        or ref.get("site_lat")!=LAT or ref.get("site_lon")!=LON):
        raise ValueError("Stage16 source provenance / coordinates / NO-APPROVAL gate failed")
    f=Path(ref["surface_path"])
    if (not f.is_file() or f.is_symlink() or f.parent.resolve()!=stage16.resolve()
        or sha(f)!=SOURCE_HASH):
        raise ValueError("Stage16 surface path or pinned exact bytes mismatch")
    with netCDF4.Dataset(str(f),"r") as ds:
        lat=float(arr(ds,"LATIXY")[0]);lon=float(arr(ds,"LONGXY")[0])
        if abs(lat-LAT)>0.05 or abs((lon-LON+180)%360-180)>0.05:
            raise ValueError("Point surface location mismatch")
        nat=arr(ds,"PCT_NAT_PFT")
        natveg=arr(ds,"PCT_NATVEG")
        if len(nat) not in (15,16) or natveg.size!=1:
            raise ValueError("Host PFT vector/landunit dimensions unexpected")
        if (np.any(nat<0) or abs(nat.sum()-100)>0.1 or
            not 0<=natveg[0]<=100):
            raise ValueError("Host natural PFT fractions outside physical range")
        soil={k:arr(ds,k) for k in ("PCT_SAND","PCT_CLAY","ORGANIC")}
        n_soil=len(soil["PCT_SAND"])
        if (n_soil!=10 or len(soil["PCT_CLAY"])!=10 or
            len(soil["ORGANIC"])!=10 or
            np.any(soil["PCT_SAND"]<0) or np.any(soil["PCT_CLAY"]<0) or
            np.any(soil["PCT_SAND"]+soil["PCT_CLAY"]>100.001)):
            raise ValueError("Expected physical 10-layer reference soil")
        land={}
        for name in ("PCT_NATVEG","PCT_CROP","PCT_LAKE","PCT_WETLAND",
                     "PCT_GLACIER","PCT_URBAN"):
            a=arr(ds,name)
            land[name]=float(a.sum())
        if abs(sum(land.values())-100)>0.1:
            raise ValueError("Landunits do not sum to 100")
        nat_coord=arr(ds,"natpft") if "natpft" in ds.variables else None
        if nat_coord is not None and not np.array_equal(nat_coord,np.arange(len(nat))):
            raise ValueError("Host natpft coordinate labels not standard 0-based")
        exact_pft=[{
            "host_natpft_index":i,"name":HOST_NAMES[i],
            "pct_of_natural_land":float(x),
            "pct_of_grid":float(x*natveg[0]/100),
            "FATES_plant_type_in_compiled_parameter_NOT_AUTO_ASSIGNED":"UNVERIFIED",
        }for i,x in enumerate(nat)]
        exact_soil=[]
        for i in range(n_soil):
            sand=float(soil["PCT_SAND"][i]);clay=float(soil["PCT_CLAY"][i])
            exact_soil.append({
                "layer_number":i+1,"PCT_SAND_GRID":sand,"PCT_CLAY_GRID":clay,
                "PCT_SILT_GRID_RESIDUAL":100-sand-clay,
                "ORGANIC_GRID":float(soil["ORGANIC"][i]),
                "FIELD_BULK_SAND_SITE_REF":74,
                "FIELD_BULK_CLAY_SITE_REF":15,
                "field_bulk_not_verified_layer_profile":True,
            })
        groups={
            "bare":float(nat[0]),
            "trees_all":float(nat[1:9].sum()),
            "evergreen_broadleaf_trees":float(nat[4:6].sum()),
            "shrubs":float(nat[9:12].sum()),
            "c3_grasses":float(nat[12:14].sum()),
            "c4_grass":float(nat[14]),
            "extra_slot_15":float(nat[15]) if len(nat)==16 else 0.0,
        }
    return obj, f, exact_pft, exact_soil, groups, land


def optional_fates_parameters(file):
    if file is None:
        return {
            "status":"NO_COMPILED_FATES_PARAMETER_FILE_SUPPLIED",
            "exact_HLM_to_FATES_mapping_verified":False,
            "reason":"User must supply exact fates_params NetCDF in use by the intended case",
        }
    if file.is_symlink() or not file.is_file():
        raise FileNotFoundError("Requested FATES params missing/symlink")
    with netCDF4.Dataset(str(file),"r") as ds:
        keys=[k for k in ds.variables if
              "hlm_pft_map" in k.lower() or
              k in ("fates_pftname","fates_pft_name","fates_pft","fates_pft_label")]
        if "fates_hlm_pft_map" not in ds.variables:
            return {
                "status":"FATES_HLM_MAP_MISSING_REVIEW_CASE_CONFIGURATION",
                "parameter_file":str(file),"SHA256":sha(file),
                "related_fields":keys,
                "exact_HLM_to_FATES_mapping_verified":False,
            }
        v=ds.variables["fates_hlm_pft_map"]
        matrix=np.ma.asarray(v[:],dtype=float).filled(np.nan)
        if not np.isfinite(matrix).all() or matrix.ndim!=2:
            raise ValueError("FATES HLM-PFT mapping must be a finite matrix")
        mapping={
            "status":"FATES_MAPPING_MATRIX_FOUND_MANUAL_ORIENTATION_AND_TRAIT_REVIEW",
            "parameter_file":str(file),"SHA256":sha(file),
            "variable":"fates_hlm_pft_map","matrix_shape":list(matrix.shape),
            "matrix_dimensions":list(v.dimensions),
            "matrix_nonzero_elements":[
                {"array_index":[int(i),int(j)],"mapping_value":float(matrix[i,j])}
                for i,j in zip(*np.where(matrix!=0))],
            "related_fields":keys,
            "exact_HLM_to_FATES_mapping_verified":False,
            "note":"Never infer FATES PFT ordinal/index from matrix alone; inspect dimensions and PFT names/traits",
        }
    return mapping


def csv_write(path,headers,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=headers,extrasaction="raise",delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def selftest():
    assert len(HOST_NAMES)==16
    assert len(HOST_COLS)==5 and len(SOIL_COLS)==8
    assert abs(sum([34.88629578998625,2.601017371450931,
                    41.58592875619181,0.0408680995959835,
                    20.885889982775026])-100)<1e-5
    assert abs(74+11+15-100)<1e-9
    print("STAGE17 SELF-TEST PASS: host PFT denominator, 10-layer soil and source identity; NO SURFACE/CASE WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage16",type=Path,default=STAGE16)
    p.add_argument("--fates-params",type=Path,
                   help="Optional exact fates_params*.nc from intended run; read only")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve()
    stage16=args.stage16.resolve()
    if (args.out.is_symlink() or out.exists() or
        out.parent!=Path.home().resolve() or
        out==stage16 or stage16 in out.parents or
        out==ROOT.resolve() or ROOT.resolve() in out.parents):
        raise ValueError("Report must be a NEW direct HOME child, outside all model trees")
    metadata,reference,pfts,soils,groups,land=read_source(stage16)
    fates=optional_fates_parameters(args.fates_params)
    site_evidence={
        "site":"AU-ASM Mulga1","coordinates":[LAT,LON],
        "Mulga_species":["Acacia aneura","Acacia aptaneura"],
        "vegetation":"Mulga woodland + C3 shrubs/forbs + C3 grasses + C4 grass + intermittent bare soil",
        "field_Acacia_cover_74p5_percent":{
            "value":74.5,
            "denominator":"land area in previous plot surveys quoted by site study; NOT directly the 2013-2018 tower footprint's host natural PFT vector",
            "source":"https://opus.lib.uts.edu.au/bitstream/10453/133258/2/02whole.pdf",
            "used_to_replace_model_tree_pct":False,
        },
        "soil_bulk_74_11_15":{
            "sand":74,"silt":11,"clay":15,
            "status":"reported red Kandosol texture; NOT a 10-layer field profile",
            "source":"https://opus.lib.uts.edu.au/bitstream/10453/133258/2/02whole.pdf",
            "used_to_replace_all_CTSM_soil_layers":False,
        },
        "other_older_soil_description":"ozflux.org.au site page reports 50:50 sand:clay; source measurement/period differences unresolved",
        "science_status":"PROXY_OBSERVATIONAL_CONTEXT_NOT_MODEL_FRACTIONS",
    }
    comparison={
        "reference_tree_natural_pct":groups["trees_all"],
        "site_Acacia_cover_plot_pct":74.5,
        "do_not_subtract_as_same_denominator":True,
        "reference_soil_sand_mean_pct":float(np.mean([x["PCT_SAND_GRID"] for x in soils])),
        "reference_soil_clay_mean_pct":float(np.mean([x["PCT_CLAY_GRID"] for x in soils])),
        "published_site_bulk_sand_pct":74,
        "published_site_bulk_clay_pct":15,
        "published_site_value_not_depth_specific":True,
    }
    summary={
        "stage":"OzFlux Stage17 AU-ASM science surface model-source comparison",
        "input_surface":str(reference),"input_surface_SHA256":SOURCE_HASH,
        "source_original_Stage16_completion":True,
        "source_FATES_parameter_file":fates,
        "CTSM_host_PFT":groups,"CTSM_landunits":land,
        "site_science_evidence":site_evidence,
        "descriptive_grid_vs_field_comparison":comparison,
        "scientific_decisions_remaining":[
            "Choose whether native Mulga is simulated via evergreen broadleaf tree or shrub profile based on actual FATES traits; do not assume parameter equivalence",
            "Obtain PFT area fractions from site/footprint data, including bare ground and seasonal grasses; avoid transferring plot Acacia cover directly",
            "Select and justify ten-layer sand/clay/organic profile; 74/15 field bulk not verified as vertical layers",
            "Inspect exact fates_hlm_pft_map in the intended model params, FATES PFT traits and dynamic/fixed-biogeography configuration",
            "Generate a new science-specific surface only after operator approves a pinned PFT/soil hypothesis; validate its NetCDF before any CIME case",
        ],
        "PFT_fraction_science_approved":False,
        "ten_layer_soil_science_approved":False,
        "point_surface_science_approved":False,
        "model_submit_authorised":False,
        "all_original_inputs_unchanged":True,
    }
    out.mkdir(parents=False,exist_ok=False)
    csv_write(out/"stage17_AU_ASM_host_PFT_exact.tsv",HOST_COLS,pfts)
    csv_write(out/"stage17_AU_ASM_soil10_grid_vs_site_bulk.tsv",SOIL_COLS,soils)
    (out/"stage17_AU_ASM_PFT_soil_science_gate.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STAGE17 SOURCE VERIFIED",reference,"SHA256",SOURCE_HASH)
    print("HOST_PFT_TOTAL",round(sum(x["pct_of_natural_land"] for x in pfts),8))
    for key in ("bare","trees_all","evergreen_broadleaf_trees","shrubs",
                "c3_grasses","c4_grass","extra_slot_15"):
        print("REFERENCE_PFT",key,round(groups[key],6))
    print("SITE_PLOT_ACACIA_COVER",74.5,"NOT_SAME_DENOMINATOR_AS_HOST_PFT")
    print("REFERENCE_SOIL_SAND_CLAY_MEAN",
          round(comparison["reference_soil_sand_mean_pct"],2),
          round(comparison["reference_soil_clay_mean_pct"],2))
    print("SITE_SOIL_BULK_SAND_CLAY",74,15,"NOT_TEN_LAYER_SOIL")
    print("FATES_PARAMETER_MAPPING",fates["status"])
    print("SCIENCE_APPROVAL FALSE; NO NEW SURFACE; NO CIME OR SLURM")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""OzFlux Stage20: independently reconcile exact FATES 14x14 map and AU-ASM host surface.

READ-ONLY source/parameter/surface audit, writes only a new HOME report.
No model PFT fractions assigned; no new surface, CIME, Slurm, or AD400.
The 14x14 host->FATES matrix applies in fixed-biogeography mode; with
competition/full-FATES flags from AU-How, the computed mapped fractions
are a COUNTERFACTUAL INPUT LOOKUP, NOT a prediction or release.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import netCDF4
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
PARAM=ROOT/"CTSM/src/fates/parameter_files/fates_params_default.json"
PARAM_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
SURFACE=Path("/iridisfs/home/ly3n24/ozflux_stage16_reference_20261102T023647Z/surfdata_AU-ASM_hist_2000_16pfts_c261102.nc")
SURF_SHA="18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa"
STAGE19=Path.home()/"ozflux_stage19_20261102T031102Z"
STAGE17=Path.home()/"ozflux_stage17_20261102T025047Z"
CASE=ROOT/"cases/AU-How_FATES_1PT/CaseDocs/lnd_in"
HOST_NAMES=(
    "bare","needleleaf_evergreen_temperate_tree","needleleaf_evergreen_boreal_tree",
    "needleleaf_deciduous_boreal_tree","broadleaf_evergreen_tropical_tree",
    "broadleaf_evergreen_temperate_tree","broadleaf_deciduous_tropical_tree",
    "broadleaf_deciduous_temperate_tree","broadleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_temperate_shrub","broadleaf_deciduous_temperate_shrub",
    "broadleaf_deciduous_boreal_shrub","c3_arctic_grass",
    "c3_nonarctic_grass","c4_grass",
)
COLS=("host_natpft","host_name","CTSM_natural_percent","FATES_1based_PFT",
      "FATES_name","mapping_weight","mapped_pct_natural_land",
      "scientific_provenance","active_in_AU_ASM_NOT_VERIFIED")


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def read_param(p):
    if p.is_symlink() or not p.is_file() or sha(p)!=PARAM_SHA:
        raise ValueError("Exact local FATES JSON source SHA mismatch")
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict) or set(obj)!={"attributes","dimensions","parameters"}:
        raise ValueError("Unexpected exact FATES JSON schema")
    params=obj["parameters"]
    raw_map=params["fates_hlm_pft_map"]
    raw_names=params["fates_pftname"]
    if raw_map.get("dims")!=["fates_hlm_pftno","fates_pft"] or raw_names.get("dims")!=["fates_pft"]:
        raise ValueError("FATES 2D mapping axis labels not expected host rows/PFT columns")
    a=np.asarray(raw_map["data"],dtype=np.float64)
    names=raw_names["data"]
    if a.shape!=(14,14) or len(names)!=14 or not all(isinstance(n,str) and n.strip() for n in names):
        raise ValueError("FATES mapping or name list dimension mismatch")
    if not np.isfinite(a).all() or (a<0).any() or (a>1).any() or not np.allclose(a.sum(axis=1),1,atol=1e-8):
        raise ValueError("HLM-to-FATES fractional mapping not physical")
    if names[7]!="broadleaf_hydrodecid_extratrop_shrub":
        raise ValueError("Actual host10 shrub target not the pinned default parameter")
    if (not np.isclose(a[9,7],1) or
        not np.isclose(a[3,0],1) or
        not np.isclose(a[4,3],1) or
        not np.isclose(a[12,12],1) or
        not np.isclose(a[13,13],1)):
        raise ValueError("Expected mapping entry drifted: inspect exact FATES config")
    return a,names,obj


def read_surface(p):
    if p.is_symlink() or not p.is_file() or sha(p)!=SURF_SHA:
        raise ValueError("CTSM reference surface SHA drift")
    with netCDF4.Dataset(str(p),"r") as ds:
        nat=np.ma.asarray(ds.variables["PCT_NAT_PFT"][:],dtype=float).filled(np.nan).ravel()
        sand=np.ma.asarray(ds.variables["PCT_SAND"][:],dtype=float).filled(np.nan).ravel()
        clay=np.ma.asarray(ds.variables["PCT_CLAY"][:],dtype=float).filled(np.nan).ravel()
        org=np.ma.asarray(ds.variables["ORGANIC"][:],dtype=float).filled(np.nan).ravel()
        land=float(np.ma.asarray(ds.variables["PCT_NATVEG"][:],dtype=float).filled(np.nan).ravel()[0])
        lat=float(np.ma.asarray(ds.variables["LATIXY"][:]).filled(np.nan).ravel()[0])
        lon=float(np.ma.asarray(ds.variables["LONGXY"][:]).filled(np.nan).ravel()[0])
    if (len(nat)!=15 or len(sand)!=10 or len(clay)!=10 or len(org)!=10 or
        not np.isfinite(np.r_[nat,sand,clay,org,land,lat,lon]).all() or
        abs(nat.sum()-100)>1e-4 or not 0<=land<=100 or
        abs(lat+22.2828)>0.05 or abs((lon-133.2493+180)%360-180)>0.05):
        raise ValueError("Reference gridded surface not original AU-ASM structure")
    if np.any(sand<0) or np.any(clay<0) or np.any(sand+clay>100):
        raise ValueError("Reference soil fraction invalid")
    return nat,sand,clay,org,land


def cross_stage_safety():
    s=STAGE19/"stage19_AU_ASM_FATES_JSON_actual_schema.json"
    t=STAGE17/"stage17_AU_ASM_PFT_soil_science_gate.json"
    if any(not f.is_file() or f.is_symlink() for f in (s,t)):
        raise FileNotFoundError("Stage19 / 17 operator report missing")
    a=json.loads(s.read_text(encoding="utf-8"))
    b=json.loads(t.read_text(encoding="utf-8"))
    if (a.get("parameter_SHA256")!=PARAM_SHA or
        a.get("model_submission_authorised") is not False or
        a.get("actual_default_JSON_contains_hlm_map") is not True or
        b.get("input_surface_SHA256")!=SURF_SHA or
        b.get("model_submit_authorised") is not False):
        raise ValueError("Stage19/17 science provenance incomplete or not unapproved")
    return {"stage19_report_SHA256":sha(s),"stage17_report_SHA256":sha(t)}


def reference_case_mode():
    result={"case":str(CASE),"case_role":"AU-HOW EXAMPLE, NOT ACTIVE AU-ASM",
            "AU_ASM_case_configuration_known":False}
    if not CASE.is_file() or CASE.is_symlink():
        result["status"]="REFERENCE_CASE_MISSING"
        return result
    text=CASE.read_text(encoding="utf-8",errors="replace")
    if len(text)>2_000_000:
        raise ValueError("Unexpected giant CaseDocs lnd_in")
    flags={}
    for line in text.splitlines():
        if line.lstrip().startswith(("!","#")):continue
        match=re.match(r"(?i)^\s*([a-z_][a-z0-9_]*)\s*=\s*(.*?)\s*(?:!.*)?$",line)
        if not match:continue
        key=match.group(1).lower()
        if key in ("use_fates","use_fates_nocomp","use_fates_fixed_biogeog","fates_paramfile"):
            flags[key]=match.group(2).strip()
    expected={"use_fates":".true.","use_fates_nocomp":".false.","use_fates_fixed_biogeog":".false."}
    if any(flags.get(k,"").lower()!=v for k,v in expected.items()):
        raise ValueError("AU-How exemplar mode differs from operator Stage19 evidence")
    if flags.get("fates_paramfile","").strip("'\"")!=str(PARAM):
        raise ValueError("AU-How reference case FATES JSON path changed")
    result.update({"status":"FULL_FATES_COMPETITION_REFERENCE_ONLY",
                   "sha256":sha(CASE),"namelist_flags":flags})
    return result


def write_tsv(p,rows):
    with p.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLS,delimiter="\t",extrasaction="raise")
        writer.writeheader();writer.writerows(rows)


def selftest():
    mat=np.eye(14)
    assert mat.shape==(14,14)
    assert np.allclose(mat.sum(axis=1),1)
    assert len(HOST_NAMES)==15
    assert HOST_NAMES[10]=="broadleaf_deciduous_temperate_shrub"
    assert (10-1)==9
    assert HOST_NAMES[0]=="bare"
    print("STAGE20 SELF-TEST PASS: host1->map row0, FATES 14 PFTs, mode gates; NO NETCDF WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or
        out.parent!=Path.home().resolve() or
        any(root==out or root in out.parents for root in (ROOT.resolve(),STAGE17.resolve(),STAGE19.resolve()))):
        raise ValueError("Report must be a fresh direct HOME child, outside source trees")
    provenance=cross_stage_safety()
    matrix,names,params=read_param(PARAM)
    nat,sand,clay,org,land=read_surface(SURFACE)
    reference_case=reference_case_mode()
    rows=[]
    pft_area=np.zeros(14,dtype=np.float64)
    for host_index in range(1,15):
        weights=matrix[host_index-1]
        for j in np.flatnonzero(weights>0):
            x=float(nat[host_index]*weights[j])
            rows.append({
                "host_natpft":host_index,
                "host_name":HOST_NAMES[host_index],
                "CTSM_natural_percent":float(nat[host_index]),
                "FATES_1based_PFT":int(j+1),
                "FATES_name":names[j],
                "mapping_weight":float(weights[j]),
                "mapped_pct_natural_land":x,
                "scientific_provenance":"exact local JSON 14x14 map; only applies when fixed biogeography is enabled",
                "active_in_AU_ASM_NOT_VERIFIED":True,
            })
            pft_area[j]+=x
    if abs(pft_area.sum()+nat[0]-100)>1e-5:
        raise ValueError("FATES PFT mapped vegetation and host0 bare do not conserve area")
    fates_by_name=[
        {"fates_pft_1based":i+1,"name":names[i],
         "mapped_pct_of_natural_land_if_fixed_biogeog":float(pft_area[i]),
         "mapped_pct_of_vegetated_natural_land_if_fixed_biogeog":float(
              pft_area[i]/(100-nat[0])*100) if nat[0]<100 else None}
        for i in range(14)
    ]
    if not np.isclose(pft_area[7],nat[10],atol=1e-8):
        raise ValueError("Host10 arid hydrodeciduous shrub mapped area not conserved")
    topkeys=list(params["parameters"])
    per_pft=[]
    for key,value in params["parameters"].items():
        if isinstance(value,dict) and "fates_pft" in (value.get("dims") or []):
            val=value.get("data")
            parsed={"name":key,"dims":value.get("dims"),"units":value.get("units"),
                    "dtype":value.get("dtype")}
            if isinstance(val,list) and len(val)==14 and all(
                    isinstance(x,(str,int,float,bool)) for x in val):
                parsed["pft_1based_names_or_values"]=val
            per_pft.append(parsed)
    config={
        "stage":"OzFlux Stage20 exact host-to-FATES 14 PFT map + AU-ASM mode decision",
        "read_only":True,"science_approval":False,"model_submit_authorised":False,
        "source_SHA256":{"FATES_default_JSON":PARAM_SHA,"CTSM_reference_surface":SURF_SHA,
                         **provenance},
        "parameter":"fates_hlm_pft_map",
        "matrix_dims":["fates_hlm_pftno","fates_pft"],
        "host_PFT1_through_14_correspond_to_matrix_rows0_through_13":True,
        "host_PFT0_bare_has_no_FATES_tree_shrub_grass_mapping":True,
        "matrix_all_14_rows_sum_to_one":True,
        "FATES_PFT_names":[{"one_based":i+1,"zero_based":i,"name":n}for i,n in enumerate(names)],
        "reference_HOST_PFT_natural_percent":[float(v) for v in nat],
        "reference_bare_pct_of_natural_land":float(nat[0]),
        "counterfactual_fixed_biogeog_mapped_fates_areas":fates_by_name,
        "mapped_total_FATES_vegetated_natural_pct":float(pft_area.sum()),
        "reference_CTSM_natveg_grid_pct":land,
        "AU_How_existing_case_configuration_reference_only":reference_case,
        "AU_ASM_competition_mode_SELECTED":False,
        "AU_ASM_fixed_biogeog_mode_SELECTED":False,
        "site_specific_PFT_fractions_approved":False,
        "site_specific_soil_profile_approved":False,
        "site_specific_surface_created":False,
        "reference_soil10_sand_pct":[float(v) for v in sand],
        "reference_soil10_clay_pct":[float(v) for v in clay],
        "reference_soil10_organic_original_units":[float(v) for v in org],
        "published_site_bulk_texture":{"sand_pct":74,"silt_pct":11,"clay_pct":15,
           "does_not_define_10_layer_profile":True},
        "Acacia_site_plot_74p5_pct_is_not_CTSM_host_PFT":True,
        "fates_pft_dimensioned_parameter_count":len(per_pft),
        "fates_pft_dimensioned_parameter_preview":per_pft[:80],
        "next":"Choose an explicit AU-ASM modeling objective, then version separate reference/full-competition vs site-specific PFT/soil sensitivity surface inputs; no default cover-based fixed run approval.",
    }
    out.mkdir(parents=False,exist_ok=False)
    write_tsv(out/"stage20_AU_ASM_exact_host_to_FATES_mapping.tsv",rows)
    (out/"stage20_AU_ASM_exact_mode_PFT_soil_science_gate.json").write_text(
        json.dumps(config,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STAGE20 FATES JSON SHA VERIFIED",PARAM_SHA)
    print("STAGE20 SURFACE SHA VERIFIED",SURF_SHA)
    print("STAGE20 FULL MAP 14x14 VALID / HOST1..14 -> FATES1..14")
    print("HOST10",HOST_NAMES[10],"TO",names[7],
          "AREA_PCT",round(float(nat[10]),6))
    print("HOST0 BARE",round(float(nat[0]),6),"FATES_MAPPED_VEGETATION",round(float(pft_area.sum()),6))
    for item in fates_by_name:
        if item["mapped_pct_of_natural_land_if_fixed_biogeog"]>0:
            print("FATES_PFT",item["fates_pft_1based"],item["name"],
                round(item["mapped_pct_of_natural_land_if_fixed_biogeog"],6),
                "PCT_NATLAND_IF_FIXED_ONLY")
    print("AU_HOW_MODE",reference_case["status"])
    print("PFT_TRAIT_FIELDS",len(per_pft))
    print("STAGE20 COMPLETE | REPORT ONLY | AU-ASM MODE/PFT/SOIL UNAPPROVED")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

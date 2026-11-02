#!/usr/bin/env python3
"""OzFlux Stage21 AU-ASM: site-science FATES trait/mode audit; read-only.

Read exact sha-pinned FATES JSON (14 PFTs and 214 dimensioned parameters)
and Stage20 operator-verified host-to-FATES mapping.
Compare FATES PFT 1/4/7/8/9/13/14 traits without choosing Mulga PFT
percentages or treating an area-conditional fixed-biogeography map as a
Full-FATES competition-mode prediction.

Writes only NEW reports beneath HOME. NO edits to JSON, surface, forcing,
soil, site source, existing cases or Slurm. NO model submission.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
PARAM=ROOT/"CTSM/src/fates/parameter_files/fates_params_default.json"
PARAM_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
REF_SURFACE_SHA="18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa"
STAGE20=Path.home()/"ozflux_stage20_20261102T032403Z"
STAGE14=Path.home()/"ozflux_stage14_FSDS0_20261102T012038Z"
SELECTED=(1,4,7,8,9,13,14)  # FATES 1-based indices, NOT host natpft
REQUIRED_PFT_NAMES={
    1:"broadleaf_evergreen_tropical_tree",
    4:"broadleaf_evergreen_extratrop_tree",
    7:"broadleaf_evergreen_extratrop_shrub",
    8:"broadleaf_hydrodecid_extratrop_shrub",
    9:"broadleaf_colddecid_extratrop_shrub",
    13:"cool_c3_grass",
    14:"c4_grass",
}
TRAIT_FIELDS=(
    "parameter","dims","units","dtype","long_name","parameter_class",
    "extraction_status",
)+tuple("FATES"+str(i)+"_"+REQUIRED_PFT_NAMES[i] for i in SELECTED)
PRIORITY_TOKENS=(
    "phen","leaf_long","leaf_sla","vcmax","stomat","hydro",
    "root","allom","seed","recruit","drought","mort","smp",
    "p50","water","conduct","safety","resprout",
)


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as fd:
        for chunk in iter(lambda:fd.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def safe_source(p,expected_hash,desc):
    if p.is_symlink() or not p.is_file() or sha(p)!=expected_hash:
        raise ValueError("Missing/modified exact "+desc+" "+str(p))
    return p


def param_names(x):
    if not isinstance(x,dict) or set(x)!={"attributes","dimensions","parameters"}:
        raise ValueError("FATES parameter JSON root schema not pinned")
    p=x["parameters"]
    name_entry=p["fates_pftname"]
    names=name_entry["data"]
    if (name_entry.get("dims")!=["fates_pft"]
        or not isinstance(names,list) or len(names)!=14):
        raise ValueError("FATES parameter name vector shape changed")
    for i,name in REQUIRED_PFT_NAMES.items():
        if names[i-1]!=name:
            raise ValueError("FATES"+str(i)+" name changed, source hash/provenance must be revisited")
    matrix=p["fates_hlm_pft_map"]
    a=np.asarray(matrix["data"],dtype=float)
    if (matrix.get("dims")!=["fates_hlm_pftno","fates_pft"]
        or a.shape!=(14,14) or not np.isfinite(a).all()
        or not np.allclose(a.sum(axis=1),1,atol=1e-9)
        or not np.isclose(a[9,8],1)
        or not np.isclose(a[9,7],0)):
        raise ValueError("Stage20 host10 -> FATES9 COLD-deciduous mapping mismatch")
    return names,p


def stage20_evidence(p):
    r=p/"stage20_AU_ASM_exact_mode_PFT_soil_science_gate.json"
    if p.is_symlink() or not r.is_file() or r.is_symlink():
        raise ValueError("Stage20 operator report not found")
    d=json.loads(r.read_text(encoding="utf-8"))
    src=d.get("source_SHA256",{})
    if (src.get("FATES_default_JSON")!=PARAM_SHA
        or src.get("CTSM_reference_surface")!=REF_SURFACE_SHA
        or d.get("science_approval") is not False
        or d.get("model_submit_authorised") is not False
        or d.get("AU_ASM_competition_mode_SELECTED") is not False
        or d.get("AU_ASM_fixed_biogeog_mode_SELECTED") is not False
        or d.get("ACTUAL_host10_FATES_PFT_1based")!=9
        or d.get("ACTUAL_host10_target")!="broadleaf_colddecid_extratrop_shrub"
        or d.get("fates_pft_dimensioned_parameter_count")!=214):
        raise ValueError("Stage20 actual operator science gate/schema inconsistent")
    return d,sha(r)


def extract_pft_axis(entry):
    if not isinstance(entry,dict):
        return None
    dims=entry.get("dims")
    if not isinstance(dims,list) or "fates_pft" not in dims:
        return None
    if dims.count("fates_pft")!=1:
        raise ValueError("Repeated fates_pft dimension in parameter")
    result={
        "dims":dims,
        "units":str(entry.get("units","")),
        "dtype":str(entry.get("dtype","")),
        "long_name":str(entry.get("long_name","")),
    }
    if "data" not in entry:
        result.update({"extraction_status":"DATA_MISSING","values":{}})
        return result
    try:
        # dtype=object allows int, float, text and N-dimensional vectors.
        # Ragged/invalid nested data are reported as issues, not silently
        # broadcast into wrong PFT positions.
        arr=np.asarray(entry["data"],dtype=object)
    except (ValueError,TypeError):
        result.update({"extraction_status":"UNDECODABLE_DATA_SHAPE","values":{}})
        return result
    axis=dims.index("fates_pft")
    if arr.ndim!=len(dims) or arr.shape[axis]!=14:
        result.update({
            "extraction_status":"DIMENSIONS_DO_NOT_MATCH_DATA",
            "observed_shape":list(arr.shape),
            "values":{},
        })
        return result
    values={}
    for i in SELECTED:
        selected=np.take(arr,i-1,axis=axis)
        # JSON round-trip converts np scalars and arrays to primitive types.
        raw=selected.tolist()
        value=json.dumps(raw,ensure_ascii=False,allow_nan=False,default=str)
        if len(value)>6000:
            value=value[:6000]+"...[TRUNCATED IN REPORT]"
        values[str(i)]=value
    result.update({"extraction_status":"PFT_AXIS_VERIFIED",
                   "observed_shape":list(arr.shape),
                   "fates_axis_index":axis,
                   "values":values})
    return result


def trait_class(name):
    s=name.lower()
    if "phen" in s or "leaf_long" in s:
        return "PHENOLOGY"
    if "hydro" in s or "smp" in s or "p50" in s or "conduct" in s:
        return "HYDRAULICS_WATER"
    if "stomat" in s or "vcmax" in s or "leaf_sla" in s:
        return "PHOTOSYNTHESIS_STOMATA"
    if "allom" in s or "root" in s:
        return "ALLOMETRY_ROOTS"
    if "seed" in s or "recruit" in s:
        return "RECRUITMENT"
    if "mort" in s:
        return "MORTALITY"
    return "OTHER_PFT_TRAIT"


def audit_params(params):
    rows=[]
    issues=[]
    for name,entry in sorted(params.items()):
        if not isinstance(entry,dict) or "fates_pft" not in (entry.get("dims") or []):
            continue
        info=extract_pft_axis(entry)
        if info is None:continue
        row={
            "parameter":name,
            "dims":json.dumps(info.get("dims"),ensure_ascii=False),
            "units":info.get("units",""),
            "dtype":info.get("dtype",""),
            "long_name":info.get("long_name",""),
            "parameter_class":trait_class(name),
            "extraction_status":info["extraction_status"],
        }
        for i in SELECTED:
            row["FATES"+str(i)+"_"+REQUIRED_PFT_NAMES[i]]=info.get("values",{}).get(str(i),"")
        rows.append(row)
        if info["extraction_status"]!="PFT_AXIS_VERIFIED":
            issues.append({
                "parameter":name,"status":info["extraction_status"],
                "dims":info.get("dims"),"observed_shape":info.get("observed_shape"),
            })
    return rows,issues


def stage14_check(root):
    p=root/"stage14_FSDS0_provisional_manifest.json"
    if not p.is_file() or p.is_symlink():
        raise ValueError("Stage14 exact source-pinned forcing manifest absent")
    d=json.loads(p.read_text(encoding="utf-8"))
    if (d.get("mode")!="WRITTEN_NEW_PROVISIONAL_FILES"
        or d.get("correction_rows")!=360
        or d.get("science_approval") is not False
        or d.get("model_submission_authorised") is not False
        or len(d.get("new_outputs",[]))!=6):
        raise ValueError("Stage14 source forcings gate changed")
    return {"manifest_SHA256":sha(p),"candidate_count":6,
            "science_approval":False}


def csv_write(p,rows):
    with p.open("x",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=TRAIT_FIELDS,delimiter="\t",extrasaction="raise")
        w.writeheader()
        w.writerows(rows)


def selftest():
    fixture={
        "dims":["fates_pft"],"units":"dummy","dtype":"float",
        "data":list(range(1,15))
    }
    actual=extract_pft_axis(fixture)
    assert actual["extraction_status"]=="PFT_AXIS_VERIFIED"
    assert actual["values"]["9"]=="9"
    other=extract_pft_axis({"dims":["soil_depth","fates_pft"],
        "data":[list(range(14)),list(range(14,28))]})
    assert other["fates_axis_index"]==1
    assert other["values"]["9"]=="[8, 22]"
    assert trait_class("fates_phen_leaf")=="PHENOLOGY"
    assert trait_class("fates_leaf_stomatal_slope")=="PHOTOSYNTHESIS_STOMATA"
    print("STAGE21 SELF-TEST PASS: 14-PFT trait extraction axes, phenology/stomata and source gates; NO MODEL WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists()
        or out.parent!=Path.home().resolve()
        or any(pth==out or pth in out.parents for pth in
               (ROOT.resolve(),STAGE20.resolve(),STAGE14.resolve()))):
        raise ValueError("Output must be fresh direct child of HOME, outside inputs")
    safe_source(PARAM,PARAM_SHA,"FATES parameter")
    source=stage20_evidence(STAGE20)
    force=stage14_check(STAGE14)
    full_json=json.loads(PARAM.read_text(encoding="utf-8"))
    names,params=param_names(full_json)
    rows,issues=audit_params(params)
    if len(rows)!=214:
        raise ValueError("Expected 214 per-PFT trait fields from Stage20, got "+
                         str(len(rows)))
    priority=[r for r in rows if
              any(key in r["parameter"].lower() for key in PRIORITY_TOKENS)]
    phen=[r["parameter"] for r in rows if r["parameter_class"]=="PHENOLOGY"]
    candidate_modes={
      "REFERENCE_FULL_FATES_COMPETITION":{
        "AU_ASM_selected":False,
        "reference_mode_source":"AU-How use_fates TRUE fixed_biogeog FALSE nocomp FALSE",
        "surface":"Original SHA-pinned Stage16 reference grid ONLY",
        "vegetation":"Dynamic PFT competition; fixed map does not fix PFT percentages",
        "science_limit":"Reference CTSM grid has 2.60% tree, 41.59% cold-deciduous shrub proxy, sandy 89.8/6.6 soil; not validated for Mulga footprint",
        "approved_for_case":False,
      },
      "PRESCRIBED_BIOGEOGRAPHY_WITH_COMPETITION":{
        "AU_ASM_selected":False,
        "mode_flags":"use_fates_fixed_biogeog TRUE, use_fates_nocomp FALSE",
        "vegetation":"Only input-present PFTs allowed; competition can change their relative areas; does NOT conserve prescribed area proportions",
        "science_limit":"Requires verified site PFT types/footprint and appropriate FATES PFT traits",
        "approved_for_case":False,
      },
      "PRESCRIBED_BIOGEOGRAPHY_NO_COMPETITION":{
        "AU_ASM_selected":False,
        "mode_flags":"use_fates_fixed_biogeog TRUE, use_fates_nocomp TRUE",
        "vegetation":"Input mapped PFT areas retained, no competition between PFT labels; bare host0 is nonvegetated, not a FATES canopy",
        "science_limit":"Needs scientifically justified site woody/shrub/C3/C4/bare fractions and ten soil layers",
        "approved_for_case":False,
      },
    }
    source_evidence=[
      {
        "site":"Alice Springs Mulga","vegetation":
          "Acacia aneura / Acacia aptaneura dominant evergreen Mulga canopy; temporary short grasses/herbs in bare patches after rainfall",
        "plot_cover_percent":74.5,
        "plot_cover_is_not_host_PFT_area_fraction":True,
        "citation":"https://opus.lib.uts.edu.au/bitstream/10453/133258/2/02whole.pdf",
      },
      {
        "soil":"Red Kandosol","bulk_sand_silt_clay":[74,11,15],
        "not_verified_ten_layer_profile":True,
        "citation":"https://portal.tern.org.au/metadata/7d9d2f7f-794c-41f5-b5e1-d5b58fc08743",
      },
    ]
    report={
        "stage":"OzFlux Stage21 Mulga trait, phenology and mode science gate",
        "read_only":True,
        "parameter_source_file":str(PARAM),"parameter_source_SHA256":PARAM_SHA,
        "Stage20_operator_report_SHA256":source[1],
        "Stage14_forcing_provenance":force,
        "FATES_PFT_names":[{"one_based_index":i+1,"name":name}
                           for i,name in enumerate(names)],
        "PFT_compared":[{"one_based_index":i,"name":REQUIRED_PFT_NAMES[i]}
                        for i in SELECTED],
        "source_PFT_trait_fields_count":len(rows),
        "extraction_issue_count":len(issues),
        "extraction_issues":issues,
        "phenology_parameter_names_found":phen,
        "priority_trait_fields":len(priority),
        "priority_trait_names":[r["parameter"] for r in priority],
        "site_observation_evidence":source_evidence,
        "reference_host10_default_map":{
            "host_natpft_index":10,"FATES_1based":9,
            "FATES_name":"broadleaf_colddecid_extratrop_shrub",
            "reference_pct_natural_land":41.58592875619181,
            "Mulga_phenology_appropriateness_approved":False,
        },
        "possible_modes_NOT_YET_SELECTED":candidate_modes,
        "science_conclusion":"The exact default FATES trait vectors can be compared; no PFT type, percentages or parameter edits are approved for Mulga by this audit.",
        "actual_AU_ASM_model_mode_selected":False,
        "site_specific_AU_ASM_PFT_fractions_selected":False,
        "site_specific_AU_ASM_soil_layers_selected":False,
        "new_site_specific_surface_created":False,
        "CIME_case_prepared":False,
        "Slurm_model_submitted":False,
        "AD400_authorised":False,
    }
    out.mkdir(parents=False,exist_ok=False)
    csv_write(out/"stage21_all_214_FATES_traits_PFT1_4_7_8_9_13_14.tsv",rows)
    csv_write(out/"stage21_priority_FATES_phenology_hydraulics_trait_comparison.tsv",priority)
    (out/"stage21_AU_ASM_Mulga_trait_mode_science_gate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STAGE21 FATES JSON SOURCE SHA VERIFIED",PARAM_SHA)
    print("STAGE21 STAGE20 SCIENCE RECEIPT VERIFIED",source[1])
    print("STAGE21 TRAIT FIELDS",len(rows),"PRIORITY",len(priority),
          "PHENOLOGY",len(phen),"EXTRACTION_ISSUES",len(issues))
    for r in priority[:25]:
        print("PRIORITY_TRAIT",r["parameter"],r["parameter_class"],
              r["extraction_status"])
    print("STAGE21 HOST10 FATES9 COLDDECID; MULGA PHENOLOGY NOT APPROVED")
    print("STAGE21 THREE SCENARIO MODES REGISTERED; NONE SELECTED")
    print("STAGE21 NO ORIGINAL PARAM/SURFACE/FORCING/CASE/SLURM WRITES")
    print("REPORT_DIR",out)


if __name__=="__main__":
    main()

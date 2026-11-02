#!/usr/bin/env python3
"""AU-ASM Stage23: read-only FATES4 vs FATES7 allometry/hydraulic code forensics.

Uses EXACT original Stage21 trait TSV, Stage22 science report and the
SHA-pinned FATES JSON. Gathers hmode/h_allom evidence from installed
CTSM/FATES Fortran when available. No height curves are calculated unless
the actual function implementation is independently verified.
External Acacia aneura hydraulic P50 paper is recorded as a benchmark,
NOT treated as equivalent to the FATES node or gs parameters.
No forcing/surface/params/case/Slurm writes. Output: fresh HOME only.
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

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
FATES_JSON=ROOT/"CTSM/src/fates/parameter_files/fates_params_default.json"
FATES_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
STAGE21=HOME/"ozflux_stage21_20261102T105344Z"
STAGE22=HOME/"ozflux_stage22_20261102T112126Z"
STAGE21_TRAIT_SHA="2ce8e2e0eba38bf284b67ddb73ffc54f4392105c6a35de0eeb44e49ec1c7b85d"
PFT={4:"broadleaf_evergreen_extratrop_tree",
     7:"broadleaf_evergreen_extratrop_shrub",
     8:"broadleaf_hydrodecid_extratrop_shrub",
     9:"broadleaf_colddecid_extratrop_shrub"}
NAMES=(
 "fates_allom_hmode",
 "fates_allom_d2h1","fates_allom_d2h2","fates_allom_d2h3",
 "fates_allom_dbh_maxheight",
 "fates_allom_lmode","fates_allom_rmode",
 "fates_allom_fnrt_prof_mode","fates_allom_fnrt_prof_a","fates_allom_fnrt_prof_b",
 "fates_allom_zroot_min_z","fates_allom_zroot_max_z",
 "fates_allom_zroot_min_dbh","fates_allom_zroot_max_dbh",
 "fates_hydro_p50_gs","fates_hydro_p50_node",
 "fates_hydro_kmax_node",
 "fates_leaf_stomatal_btran_model",
 "fates_leaf_stomatal_slope_medlyn",
 "fates_leaf_vcmax25top","fates_leaf_slatop",
)
MODE_GUIDE={
 1:"O'Brien height allometry, requires verification in local Fortran",
 2:"Poorter height allometry, requires verification in local Fortran",
 3:"2-parameter power law, requires exact function and unit verification",
 4:"Chave height allometry, requires verification in local Fortran",
 5:"Martinez-Cano height allometry, requires verification in local Fortran",
}
FIELDS=("parameter","units","description","dimensions",
        "FATES4_evergreen_tree","FATES7_evergreen_shrub",
        "FATES8_hydro_shrub","FATES9_cold_shrub",
        "interpretation_status")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(2**22),b""):h.update(x)
    return h.hexdigest()

def read_source():
    t=STAGE21/"stage21_all_214_FATES_traits_PFT1_4_7_8_9_13_14.tsv"
    r=STAGE22/"stage22_AU_ASM_Mulga_evergreen_PFT_science_gate.json"
    for p in (t,r,FATES_JSON):
        if not p.is_file() or p.is_symlink():
            raise ValueError("Required original source missing or symlink: "+str(p))
    if sha(t)!=STAGE21_TRAIT_SHA or sha(FATES_JSON)!=FATES_SHA:
        raise ValueError("Stage21 TSV or original FATES JSON sha mismatch")
    receipt=json.loads(r.read_text(encoding="utf-8"))
    src=receipt.get("source_provenance_SHA256",{})
    if (src.get("stage21_traits_TSV_SHA256")!=STAGE21_TRAIT_SHA or
        src.get("original_FATES_default_JSON_SHA256")!=FATES_SHA or
        receipt.get("AD400_or_Normal400_authorised") is not False or
        receipt.get("new_surface_created") is not False or
        receipt.get("selected_trait_parameters")!=35):
        raise ValueError("Stage22 science receipt failed validation")
    with t.open("r",encoding="utf-8",newline="") as fd:
        rows=list(csv.DictReader(fd,delimiter="\t"))
    if len(rows)!=214 or len(set(x["parameter"] for x in rows))!=214:
        raise ValueError("Stage21 original 214 parameter entries changed")
    lookup={x["parameter"]:x for x in rows}
    if any(x["extraction_status"]!="PFT_AXIS_VERIFIED" for x in rows):
        raise ValueError("Stage21 PFT axis not verified")
    return lookup,{"Stage21_traits_TSV_SHA256":STAGE21_TRAIT_SHA,
                  "Stage22_receipt_SHA256":sha(r),
                  "FATES_default_JSON_SHA256":FATES_SHA}

def exact_traits(lookup):
    present={k:lookup[k] for k in NAMES if k in lookup}
    missing=sorted(set(NAMES)-set(present))
    if missing:
        # Missing optional mode is a real scientific blocker; record it, do
        # not silently assume a height/allometric mode.
        pass
    result=[]
    raw={}
    for k,row in present.items():
        values={}
        for i,name in PFT.items():
            field=f"FATES{i}_{name}"
            if not row.get(field):
                raise ValueError("Missing exact FATES value "+k+" / "+field)
            values[i]=json.loads(row[field])
        raw[k]=values
        result.append({
            "parameter":k,
            "units":row["units"],"description":row["long_name"],
            "dimensions":row["dims"],
            "FATES4_evergreen_tree":json.dumps(values[4]),
            "FATES7_evergreen_shrub":json.dumps(values[7]),
            "FATES8_hydro_shrub":json.dumps(values[8]),
            "FATES9_cold_shrub":json.dumps(values[9]),
            "interpretation_status":"SOURCE_VERIFIED_DO_NOT_ASSUME_ACTIVE_PROCESS",
        })
    if "fates_allom_dbh_maxheight" not in raw:
        raise ValueError("Source height cap diameter parameter missing")
    if raw["fates_allom_dbh_maxheight"][7]!=3.0:
        raise ValueError("Stage22 FATES7 dbh_maxheight not 3 cm; review source")
    if raw["fates_allom_dbh_maxheight"][4]!=1000.0:
        raise ValueError("Stage22 FATES4 dbh_maxheight not 1000 cm; review source")
    return result,raw,missing

def source_fortran(extra):
    # Do not recurse the whole scratch or other model cases; evidence may
    # be absent for a different FATES version or checkout structure.
    dirs=[
        ROOT/"CTSM/src/fates/biogeochem",
        ROOT/"CTSM/src/fates/biogeophys",
        ROOT/"CTSM/src/fates",
        ROOT/"CTSM/src/external_models/fates/biogeochem",
        ROOT/"CTSM/src/external_models/fates/biogeophys",
    ]
    expected=("FatesAllometryMod.F90","FatesAllometryFunctionsMod.F90")
    paths=[]
    for d in dirs:
        for name in expected:
            p=d/name
            if p.is_file() and not p.is_symlink():
                paths.append(p)
    for p in extra:
        if not p.is_file() or p.is_symlink() or p.suffix.lower()!=".f90":
            raise FileNotFoundError("Specified source Fortran missing/invalid: "+str(p))
        paths.append(p)
    unique=sorted(set(x.resolve() for x in paths),key=str)
    if len(unique)>15:
        raise ValueError("Unexpected number of source files")
    found=[]
    for p in unique:
        if p.stat().st_size>600_000:
            raise ValueError("Unexpected oversized FATES Fortran file")
        lines=p.read_text(encoding="utf-8",errors="replace").splitlines()
        markers=("subroutine h_allom","subroutine d2h_2pwr",
                 "call d2h_2pwr","case (3)","allom_hmode","dbh_maxh",
                 "subroutine d2h_poorter","subroutine d2h_obrien",
                 "function d2h_2pwr")
        hits=[{"line":i+1,"text":s[:280]}
              for i,s in enumerate(lines) if any(m in s.lower() for m in
                          tuple(k.lower() for k in markers))]
        found.append({"file":str(p),"sha256":sha(p),
                      "source_lines":len(lines),
                      "matching_line_excerpts":hits[:100],
                      "actual_height_function_verified":False,
                      "do_not_transfer_mainline_code_without_checkout_verification":True})
    return found,{"searched_directories":[str(x) for x in dirs],
                  "candidate_function_names":list(expected)}

def selftest():
    assert len(PFT)==4 and PFT[4]=="broadleaf_evergreen_extratrop_tree"
    assert MODE_GUIDE[3].startswith("2-parameter")
    assert "fates_allom_hmode" in NAMES
    sample=json.loads('[[-999.0,3.0,-999.0,-999.0]]')
    assert sample[0][1]==3.0
    assert len(STAGE21_TRAIT_SHA)==64
    print("STAGE23 SELF-TEST PASS: FATES actual trait provenance, hmode and source-code bounded scans; READ ONLY")

def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--local-source",type=Path,action="append",default=[],
                   help="Optional exact local Fortran allometry module path")
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or
        out.parent!=HOME.resolve() or
        any(pth==out or pth in out.parents for pth in
            (ROOT.resolve(),STAGE21.resolve(),STAGE22.resolve()))):
        raise ValueError("Report must be a new DIRECT child of HOME")
    lookup,receipts=read_source()
    rows,raw,missing=exact_traits(lookup)
    fortran,source_search=source_fortran(a.local_source)
    modes={}
    for i in PFT:
        v=raw.get("fates_allom_hmode",{}).get(i)
        modes[str(i)]={"hmode_value":v,
                       "public_upstream_mode_description":MODE_GUIDE.get(v),
                       "active_local_source_formula_verified":False,
                       "model_predicted_height_m":None}
    p50=raw.get("fates_hydro_p50_node")
    report={
      "stage":"OzFlux AU-ASM Stage23 actual PFT4/PFT7 allometry, hydraulics, height source forensics",
      "read_only":True,"source_SHA256":receipts,
      "actual_FATES_height_allometry_modes":modes,
      "FATES_code_candidates":fortran,"code_search":source_search,
      "science_targets_missing_from_parameter":missing,
      "no_predicted_height_without_exact_local_model_formula":True,
      "Acacia_aneura_measured_hydraulic_Psi50_MPa":{
        "leaf":-5.84,"stem":-8.46,"root":-8.16,
        "publication":"Creek et al. (2018), Plant Cell & Environment",
        "doi":"10.1111/pce.13418",
        "source":"https://onlinelibrary.wiley.com/doi/full/10.1111/pce.13418",
        "site_match_to_AU_ASM_not_established":True,
        "FATES_hydro_node_equals_observed_organ_NOT_ESTABLISHED":True,
        "research_comparator_not_model_parameter_override":True,
      },
      "default_FATES_hydro_p50_node_MPa":p50,
      "default_FATES_hydro_p50_gs_MPa":raw.get("fates_hydro_p50_gs"),
      "explanation_dbh_maxheight":"Parameter is DBH in cm at height plateau, NOT canopy height in cm",
      "FATES7_dbh_maxheight_cm":3.0,
      "FATES4_dbh_maxheight_cm":1000.0,
      "negative_sentinel_values_in_source_not_physically_interpreted":True,
      "root_depth_100m_not_a_verified_actual_rooting_depth":True,
      "Mulga_evergreen_FATES4_preferred_candidate_NOT_APPROVED":True,
      "Mulga_evergreen_FATES7_structural_alternative_NOT_APPROVED":True,
      "FATES_active_hydraulic_mode_not_yet_verified":True,
      "AU_ASM_mode_and_PFT_fractions_approved":False,
      "AU_ASM_soil_profile_approved":False,
      "new_surface_or_FATES_param_created":False,
      "model_job_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(parents=False,exist_ok=False)
    with (out/"stage23_AU_ASM_PFT4_7_8_9_allometry_hydraulic_traits.tsv").open(
        "x",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=FIELDS,delimiter="\t",extrasaction="raise")
        w.writeheader();w.writerows(rows)
    (out/"stage23_AU_ASM_actual_allometry_source_science_hold.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),
        encoding="utf-8")
    print("STAGE23 SOURCE VERIFIED",receipts["Stage21_traits_TSV_SHA256"])
    print("STAGE23 ACTUAL FATES JSON SHA VERIFIED",FATES_SHA)
    print("STAGE23 TRAITS",len(rows),"MISSING_TARGET_NAMES",missing)
    for i,m in modes.items():
        print("FATES_PFT",i,"ALL0M_HMODE",m["hmode_value"],
              "MEANING",m["public_upstream_mode_description"])
    print("STAGE23 LOCAL FORTRAN FILES FOUND",len(fortran))
    for item in fortran:
        print("LOCAL_FATES_SOURCE",item["file"],"SHA",item["sha256"])
    print("STAGE23 ACACIA P50 BENCHMARK is literature context; not matched to model nodes")
    print("STAGE23 NO HEIGHT CURVES CALCULATED; NO MULGA PFT/SOIL APPROVAL; NO CIME/SLURM")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

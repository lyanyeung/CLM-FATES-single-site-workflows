#!/usr/bin/env python3
"""OzFlux AU-ASM Stage22: exact trait-value review from verified Stage21 TSV.

Only read original Stage21 TSV + JSON and optionally re-verify original
FATES default JSON checksum. Compare FATES4 (evergreen tree),
FATES7 (evergreen shrub), FATES8 (hydro-deciduous shrub) and
FATES9 (cold-deciduous shrub). No source modification, CIME/Slurm,
new point surface, area allocation or soil-profile substitution.
All decisions remain exploratory and operator-science unapproved.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE21=HOME/"ozflux_stage21_20261102T105344Z"
ORIGINAL=ROOT/"CTSM/src/fates/parameter_files/fates_params_default.json"
PARAM_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
STAGE20_SHA="76397fa3c93df57a99d57ca0cc1ee4c4c093d7e10c13493060b4d65507246ab9"
SELECTED={
  4:"broadleaf_evergreen_extratrop_tree",
  7:"broadleaf_evergreen_extratrop_shrub",
  8:"broadleaf_hydrodecid_extratrop_shrub",
  9:"broadleaf_colddecid_extratrop_shrub",
}
PHEN={
 "fates_phen_cold_size_threshold",
 "fates_phen_drought_threshold",
 "fates_phen_flush_fraction",
 "fates_phen_fnrt_drop_fraction",
 "fates_phen_leaf_habit",
 "fates_phen_mindaysoff",
 "fates_phen_moist_threshold",
 "fates_phen_stem_drop_fraction",
}
TARGET={
 "fates_leaf_vcmax25top","fates_leaf_vcmaxha",
 "fates_leaf_vcmaxhd","fates_leaf_vcmaxse",
 "fates_leaf_stomatal_btran_model",
 "fates_leaf_stomatal_intercept",
 "fates_leaf_stomatal_slope_ballberry",
 "fates_leaf_stomatal_slope_medlyn",
 "fates_leaf_slatop","fates_leaf_slamax",
 "fates_hydro_p50_gs","fates_hydro_p50_node",
 "fates_hydro_kmax_node","fates_hydro_k_lwp",
 "fates_allom_d2h1","fates_allom_d2h2","fates_allom_d2h3",
 "fates_allom_dbh_maxheight",
 "fates_allom_fnrt_prof_a","fates_allom_fnrt_prof_b",
 "fates_allom_fnrt_prof_mode",
 "fates_allom_zroot_max_z","fates_allom_zroot_min_z",
 "fates_allom_zroot_max_dbh","fates_allom_zroot_min_dbh",
 "fates_nonhydro_smpsc","fates_nonhydro_smpso",
}
COLUMNS=("group","parameter","units","description","dimensions",
         "FATES4_evergreen_tree","FATES7_evergreen_shrub",
         "FATES8_hydro_deciduous_shrub","FATES9_cold_deciduous_shrub",
         "value_interpretation_status")


def sha(file):
    h=hashlib.sha256()
    with file.open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def load_tsv(file):
    if not file.is_file() or file.is_symlink():
        raise FileNotFoundError("Stage21 TSV not found")
    with file.open("r",encoding="utf-8",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        fieldnames=r.fieldnames or []
        wanted={"parameter","units","long_name","dims",
                "parameter_class","extraction_status"}
        wanted.update("FATES"+str(i)+"_"+name for i,name in SELECTED.items())
        if not wanted.issubset(set(fieldnames)):
            raise ValueError("Stage21 TSV expected columns missing: "+
                             repr(sorted(wanted-set(fieldnames))))
        rows=list(r)
    if len(rows)!=214 or len({row["parameter"] for row in rows})!=214:
        raise ValueError("Stage21 214 distinct PFT parameters not present")
    if any(row["extraction_status"]!="PFT_AXIS_VERIFIED" for row in rows):
        raise ValueError("Unverified Stage21 PFT dimension extraction")
    return {row["parameter"]:row for row in rows}


def decoded(row,pft):
    source_col="FATES"+str(pft)+"_"+SELECTED[pft]
    raw=row[source_col]
    if raw=="":
        raise ValueError("Unexpected empty Stage21 trait field "+row["parameter"]+" "+source_col)
    value=json.loads(raw)
    if isinstance(value,float) and not (-1e300<value<1e300):
        raise ValueError("Unreasonable FATES trait scalar "+row["parameter"])
    return value


def source_checks(input_dir):
    meta=input_dir/"stage21_AU_ASM_Mulga_trait_mode_science_gate.json"
    traits=input_dir/"stage21_all_214_FATES_traits_PFT1_4_7_8_9_13_14.tsv"
    if input_dir.is_symlink() or not meta.is_file() or meta.is_symlink():
        raise FileNotFoundError("Stage21 receipt unavailable")
    record=json.loads(meta.read_text(encoding="utf-8"))
    if (record.get("parameter_source_SHA256")!=PARAM_SHA
        or record.get("Stage20_operator_report_SHA256")!=STAGE20_SHA
        or record.get("source_PFT_trait_fields_count")!=214
        or record.get("priority_trait_fields")!=126
        or record.get("extraction_issue_count")!=0
        or record.get("AD400_authorised") is not False
        or record.get("new_site_specific_surface_created") is not False):
        raise ValueError("Stage21 provenance or science gate drift")
    if (not ORIGINAL.is_file() or ORIGINAL.is_symlink()
        or sha(ORIGINAL)!=PARAM_SHA):
        raise ValueError("Underlying original FATES JSON does not match Stage21")
    return load_tsv(traits),{"stage21_manifest_SHA256":sha(meta),
                              "stage21_traits_TSV_SHA256":sha(traits),
                              "original_FATES_default_JSON_SHA256":PARAM_SHA,
                              "stage20_receipt_SHA256":STAGE20_SHA}


def convert_table_row(group,name,row):
    values={i:decoded(row,i) for i in SELECTED}
    return {
        "group":group,"parameter":name,
        "units":row["units"],"description":row["long_name"],
        "dimensions":row["dims"],
        "FATES4_evergreen_tree":json.dumps(values[4],ensure_ascii=False),
        "FATES7_evergreen_shrub":json.dumps(values[7],ensure_ascii=False),
        "FATES8_hydro_deciduous_shrub":json.dumps(values[8],ensure_ascii=False),
        "FATES9_cold_deciduous_shrub":json.dumps(values[9],ensure_ascii=False),
        "value_interpretation_status":"SOURCE_NUMBERS_ONLY_MECHANISM_NOT_YET_VERIFIED",
    }


def build_comparison(rows):
    absent=sorted((PHEN|TARGET)-set(rows))
    if absent:
        raise ValueError("Missing expected FATES scientific target parameters: "+str(absent))
    groupnames={}
    for key in sorted(PHEN|TARGET):
        if key in PHEN:g="PHENOLOGY"
        elif key.startswith(("fates_leaf_vcmax","fates_leaf_sla")):g="PHOTOSYNTHESIS_LEAF"
        elif key.startswith("fates_leaf_stomatal"):g="STOMATAL_BTRAN"
        elif key.startswith("fates_hydro"):g="HYDRAULIC_TRAITS"
        elif key.startswith("fates_allom"):g="ALLOMETRY_ROOTS"
        else:g="NONHYDRO_SOIL_WATER_STRESS"
        groupnames[key]=g
    target_rows=[convert_table_row(groupnames[key],key,rows[key])
                 for key in sorted(groupnames,key=lambda k:(groupnames[k],k))]
    habit={i:decoded(rows["fates_phen_leaf_habit"],i) for i in SELECTED}
    if habit!={4:1,7:1,8:3,9:2}:
        raise ValueError("FATES PFT habit codes not equal operator-verified 1,1,3,2")
    flush={i:decoded(rows["fates_phen_flush_fraction"],i) for i in SELECTED}
    if not (flush[4] is None and flush[7] is None
            and flush[8]==0.5 and flush[9]==0.5):
        raise ValueError("Leaf-flush parameter differs from supplied Stage21 source")
    for key,expected in (
       ("fates_phen_drought_threshold",-152957.4),
       ("fates_phen_moist_threshold",-122365.9),
    ):
        if any(decoded(rows[key],i)!=expected for i in SELECTED):
            raise ValueError("Pinned phenology water-potential value changed "+key)
    distinct_4_7=[]
    for key in sorted(groupnames):
        a=decoded(rows[key],4); b=decoded(rows[key],7)
        if a!=b:
            distinct_4_7.append(key)
    return target_rows, habit, flush, distinct_4_7


def selftest():
    cols={f"FATES{i}_{name}":json.dumps(value)
          for i,name,value in ((4,SELECTED[4],1),
                               (7,SELECTED[7],1),
                               (8,SELECTED[8],3),
                               (9,SELECTED[9],2))}
    fixture={"parameter":"fates_phen_leaf_habit",**cols}
    assert [decoded(fixture,i) for i in SELECTED]==[1,1,3,2]
    cols_null={f"FATES{i}_{name}":("null" if i in (4,7) else "0.5")
               for i,name in SELECTED.items()}
    assert decoded({"parameter":"flush",**cols_null},4) is None
    assert decoded({"parameter":"flush",**cols_null},8)==0.5
    assert len(PHEN)==8
    assert all(i in SELECTED for i in (4,7,8,9))
    print("STAGE22 SELF-TEST PASS: PFT4/7/8/9 habit 1,1,3,2; null flush; verified-TSV guards, no original writes")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage21",type=Path,default=STAGE21)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    stage21=args.stage21.resolve();out=args.out.resolve()
    if (args.out.is_symlink() or out.exists() or
        out.parent!=HOME.resolve() or
        out==stage21 or stage21 in out.parents or
        out==ROOT.resolve() or ROOT.resolve() in out.parents):
        raise ValueError("Output must be a fresh DIRECT HOME child folder")
    rows,checks=source_checks(stage21)
    target,habit,flush,distinct=build_comparison(rows)
    decision={
        "stage":"OzFlux Stage22 AU-ASM evergreen tree vs evergreen shrub actual FATES traits",
        "source_provenance_SHA256":checks,
        "all_214_PFT_parameters_read_and_checked":True,
        "selected_trait_parameters":len(target),
        "leaf_habit_by_FATES_PFT_1based":{str(k):v for k,v in habit.items()},
        "leaf_flush_fraction_by_FATES_PFT_1based":{str(k):v for k,v in flush.items()},
        "trait_names_differing_between_FATES4_and_FATES7":distinct,
        "trait_difference_not_the_same_as_parameter_quality":True,
        "external_site_evidence":{
            "tower":"AU-ASM Mulga1","canopy":"Acacia aneura/Acacia aptaneura",
            "median_canopy_height_m":4.3,
            "height_does_not_fix_a_FATES_allometry_by_itself":True,
            "soil_red_Kandosol_bulk_sand_silt_clay_percent":[74,11,15],
            "bulk_soil_texture_does_not_set_ten_soil_layers":True,
            "sources":[
                "https://portal.tern.org.au/metadata/TERN/608dca79-0ec8-412d-9f13-71f7714affac",
                "https://data.ozflux.org.au/pub/viewDatasetData.jspx?collection.id=152&collection.owner.id=101&dataset.id=3181165&viewType=anonymous",
            ],
        },
        "phenology_science_candidates":{
            "FATES4":"evergreen extratropical tree, leaf habit 1; PRIORITY structural canopy hypothesis only",
            "FATES7":"evergreen extratropical shrub, leaf habit 1; alternative woody growth form only",
            "FATES8":"hydro-deciduous extratropical shrub, leaf habit 3; stress-deciduous comparator",
            "FATES9":"cold-deciduous extratropical shrub, leaf habit 2; default host10 mapping but inappropriate to assert as evergreen Acacia",
        },
        "scientific_unknowns":[
            "Acacia site-specific crown area/cover vs host natural PFT percentage denominators",
            "FATES4 vs FATES7 crown-height allometry compatibility with AU-ASM 4.3m median canopy",
            "Root depth and hydraulic P50 suitability, linked to site soil profile and available climate",
            "PFT-specific Vcmax25, Medlyn g1, photosynthetic C3 traits and seasonal water stress",
            "Seasonally variable C3/C4 grass fraction versus bare-ground 34.89% coarse reference",
            "Appropriate 10-layer Red Kandosol site soil profiles and uncertainties",
            "Actual AU-ASM mode selection and complete physics/forcing approval",
        ],
        "scenario_A_full_competition_reference_science_approved":False,
        "scenario_B_fixed_biogeography_science_approved":False,
        "site_specific_PFT_fraction_science_approved":False,
        "site_specific_soil_profile_science_approved":False,
        "new_surface_created":False,
        "CIME_case_or_Slurm_modified":False,
        "AD400_or_Normal400_authorised":False,
    }
    out.mkdir(parents=False,exist_ok=False)
    with (out/"stage22_actual_FATES4_7_8_9_trait_comparison.tsv").open(
        "x",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=COLUMNS,delimiter="\t",
                              extrasaction="raise")
        writer.writeheader();writer.writerows(target)
    (out/"stage22_AU_ASM_Mulga_evergreen_PFT_science_gate.json").write_text(
        json.dumps(decision,indent=2,ensure_ascii=False),encoding="utf-8")
    print("STAGE22 STAGE21 TSV/SOURCE SHA VERIFIED",checks["stage21_traits_TSV_SHA256"])
    print("STAGE22 TARGET TRAITS",len(target),"PHENOLOGY",len(PHEN))
    print("STAGE22 EVERGREEN FATES4/FATES7 LEAF_HABIT",habit[4],habit[7])
    print("STAGE22 FATES8 HYDRO/FATES9 COLD LEAF_HABIT",habit[8],habit[9])
    print("STAGE22 FATES4_VS_7 DIFFERENT TRAIT FIELDS",len(distinct))
    for key in distinct:
        print("DIFFERENT",key,"FATES4",decoded(rows[key],4),
              "FATES7",decoded(rows[key],7))
    print("STAGE22 NO NEW PFT FRACTIONS OR TEN-LAYER SOIL; NO MODEL SUBMISSION")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

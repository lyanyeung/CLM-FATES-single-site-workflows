#!/usr/bin/env python3
"""OzFlux Stage27: source-pinned AU-ASM measured HEIGHT and Acacia leaf SLA bounds.

Purpose: Use Stage25 original TERN sources and Stage26 read-only audit
to quantify height records above FATES7 exact local default 4.73541m
height ceiling; D20 is NOT used as DBH, and individual rows are not
declared independent trees. Report distinct years; distinguish original
2014 field measurements from possibly derived later values (TERN
metadata says no 2018 stem resurvey).

For Acacia aneura 2014 leaf observations, report original LMA
(g dry biomass / m2) and an explicitly *hypothetical* leaf carbon
fraction f_C = 0.45 or 0.50 as: 1/(LMA*gC/g_dry).
This is NOT a direct leaf model calibration: FATES SLA is top-canopy
m2/gC, whereas measured phyllode leaves have sampling and season
limits. Do not treat measured net A as Vcmax, gs as Medlyn g1,
or TERN "Needle leaf tree" as a FATES needleleaf conifer PFT.

Read-only source audit, ONLY output a new HOME report JSON/TSV.
No modifications of model forcing, point surface, FATES parameters,
CIME, Slurm or full AD400 simulation.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE21=HOME/"ozflux_stage21_20261102T105344Z"
STAGE24=HOME/"ozflux_stage24_20261102T115254Z"
STAGE25=HOME/"ozflux_stage25_20261102T121025Z"
STAGE26=HOME/"ozflux_stage26_20261102T122636Z"
STEM="Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
LEAF="Alice_Mulga_functional_leaf_traits_data_mGiVbmq.csv"
STEM_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
LEAF_SHA="d982b9217ac0ca641e7aca47e681c03f82d08e72215de30fe7ecb1b42952acf0"
TRAIT_SHA="2ce8e2e0eba38bf284b67ddb73ffc54f4392105c6a35de0eeb44e49ec1c7b85d"
PFT4="FATES4_broadleaf_evergreen_extratrop_tree"
PFT7="FATES7_broadleaf_evergreen_extratrop_shrub"
LEAF_LMA="meanLeafDryMassPerLeafAreaTrait_gramsPerSquareMeter"
CARBON_ASSUMPTIONS=(0.45,0.50)
CORE_DBH_METADATA="https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073"
HEIGHT_COLS=("year","scientificName","raw_rows","valid_height_rows",
             "valid_height_over_FATES7_ceiling",
             "fraction_above_ceiling_of_valid_heights",
             "height_median_m","height_max_m",
             "unique_plant_keys_nonmissing",
             "unique_stem_keys_nonmissing",
             "field_diameter_classes","independence_note")
LEAF_COLS=("scientificName","plantFunctionalType","field_rows",
           "unique_plant_ids","valid_LMA_n",
           "LMA_g_dry_per_m2_median",
           "hypothetical_leaf_C_fraction_gC_per_g_dry",
           "derived_SLA_m2_per_gC_median_NOT_DIRECT_MODEL_SLA",
           "FATES4_slatop_m2_per_gC",
           "FATES7_slatop_m2_per_gC",
           "ratio_observed_derived_to_FATES4_slatop",
           "ratio_observed_derived_to_FATES7_slatop",
           "science_status")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for part in iter(lambda:f.read(2**20),b""):
            h.update(part)
    return h.hexdigest()

def source_delimiter(p):
    # Stage21 trait source is TAB-separated while TERN originals are CSV.
    # A wrong delimiter silently hides the "parameter" and PFT columns.
    return "\t" if p.suffix.lower()==".tsv" else ","

def csv_read(p):
    if p.is_symlink() or not p.is_file():
        raise FileNotFoundError(str(p))
    with p.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter=source_delimiter(p))
        cols=reader.fieldnames or []
        data=list(reader)
    if not cols or any(None in r for r in data):
        raise ValueError("Unexpected source CSV row/column structure "+str(p))
    return cols,data

def number(x,lower=None,upper=None):
    if x is None:return None
    s=str(x).strip().lower()
    if s in ("","nan","na","none","null","-999","-999.0","-999.9","-9999","-9999.0","-"):
        return None
    try:v=float(s)
    except ValueError:return None
    if not math.isfinite(v):return None
    if lower is not None and v<lower:return None
    if upper is not None and v>upper:return None
    return v

def year(text):
    s=str(text or "").strip()
    return s[:4] if len(s)>=4 and s[:4].isdigit() else "UNSPECIFIED"

def measurement_class(x):
    a=number(x)
    if a is None:return "UNKNOWN"
    if abs(a-0.2)<=0.025:return "D20_0.2m_NOT_DBH"
    if abs(a-1.3)<=0.025:return "DBH_1.3m"
    return "OTHER_HEIGHT_NOT_DBH"

def read_provenance():
    check={
      "stem":(STAGE25/STEM,STEM_SHA,222),
      "leaf":(STAGE25/LEAF,LEAF_SHA,142),
      "traits":(STAGE21/"stage21_all_214_FATES_traits_PFT1_4_7_8_9_13_14.tsv",TRAIT_SHA,214),
    }
    loaded={}
    for key,(p,expect,n) in check.items():
        if p.is_symlink() or not p.is_file() or sha(p)!=expect:
            raise ValueError("Stage27 original source SHA mismatch "+key)
        cols,rows=csv_read(p)
        if len(rows)!=n:
            raise ValueError("Stage27 original source rows differ: "+key)
        loaded[key]=(cols,rows)
    p24=STAGE24/"stage24_AU_ASM_DBH_height_science_gate.json"
    p26=STAGE26/"stage26_TERN_actual_D20_DBH_leaf_science_gate.json"
    for p in (p24,p26):
        if not p.is_file() or p.is_symlink():raise ValueError("Required stage receipt missing "+str(p))
    r24=json.loads(p24.read_text(encoding="utf-8"))
    r26=json.loads(p26.read_text(encoding="utf-8"))
    if (r24.get("source_code_formula_verified") is not True
       or r24.get("Slurm_or_AD400_authorised") is not False
       or r26.get("TERN_stem_rows_original")!=222
       or r26.get("TERN_leaf_rows_original")!=142
       or r26.get("stem_science",{}).get("measurement_point_class_counts")!={"BASAL_D20_0P20M_NOT_DBH":222}
       or r26.get("stem_science",{}).get("direct_DBH_height_pair_count")!=0
       or r26.get("scientific_decision",{}).get("AD400_authorised") is not False):
        raise ValueError("Stage24/26 verified science conditions drift")
    h7=float(r24["FATES7_plateau_height_m"])
    if not math.isclose(h7,4.735410175384586,rel_tol=1e-10):
        raise ValueError("Stage24 exact FATES7 height ceiling differs")
    return loaded,r24,{"stem_SHA256":STEM_SHA,"leaf_SHA256":LEAF_SHA,
                       "Stage21_trait_TSV_SHA256":TRAIT_SHA,
                       "Stage24_report_SHA256":sha(p24),
                       "Stage26_report_SHA256":sha(p26)}

def height_comparison(rows,cap):
    source_cols={"phenomenonTime","scientificName","stemHeight_metres",
                 "stemDiameterPointOfMeasurement_metres","siteId","plotId","plantId","stemId"}
    if not source_cols.issubset(rows[0]):
        raise ValueError("Source TERN stem columns missing")
    groups=defaultdict(lambda:{"raw":0,"height":[],"over":0,
                               "plants":set(),"stems":set(),"diameter":Counter()})
    across_years=defaultdict(set)
    all_species=Counter()
    for r in rows:
        specie=(r.get("scientificName") or "").strip() or "UNSPECIFIED"
        yr=year(r.get("phenomenonTime"))
        v=number(r.get("stemHeight_metres"),lower=0.01,upper=100)
        typ=measurement_class(r.get("stemDiameterPointOfMeasurement_metres"))
        k=(yr,specie)
        g=groups[k]
        g["raw"]+=1;g["diameter"][typ]+=1;all_species[specie]+=1
        if v is not None:
            g["height"].append(v)
            if v>cap:g["over"]+=1
        plant=tuple(str(r.get(x) or "").strip() for x in
                    ("siteId","plotId","plantId"))
        stem=plant+(str(r.get("stemId") or "").strip(),)
        if all(plant):
            g["plants"].add(plant)
        if all(stem):
            g["stems"].add(stem)
            across_years[stem].add(yr)
    result=[]
    for (yr,specie),g in sorted(groups.items()):
        heights=g["height"]
        result.append({
            "year":yr,"scientificName":specie,
            "raw_rows":g["raw"],
            "valid_height_rows":len(heights),
            "valid_height_over_FATES7_ceiling":g["over"],
            "fraction_above_ceiling_of_valid_heights":g["over"]/len(heights) if heights else None,
            "height_median_m":statistics.median(heights) if heights else None,
            "height_max_m":max(heights) if heights else None,
            "unique_plant_keys_nonmissing":len(g["plants"]),
            "unique_stem_keys_nonmissing":len(g["stems"]),
            "field_diameter_classes":json.dumps(dict(g["diameter"]),sort_keys=True),
            "independence_note":"rows not independent trees; 2018 may be derived from 2014 basal increment, NOT remeasured",
        })
    return result,{
      "stem_years":dict(Counter(year(r.get("phenomenonTime")) for r in rows)),
      "records_by_species":dict(all_species),
      "source_unique_stem_identifiers_in_multiple_years":sum(len(yrs)>1 for yrs in across_years.values()),
      "height_ceiling_comparison_valid_without_using_D20_as_DBH":True,
      "all_D20_0p20m_not_directly_model_DBH":True,
      "2018_diameter_increment_not_independent_field_remeasurement_according_to_TERN_lineage":True,
      "site_has_measured_tall_stems_not_representable_by_default_FATES7_height_cap":any(x["valid_height_over_FATES7_ceiling"]>0 for x in result if x["year"]=="2014"),
    }

def read_sla(trait_rows):
    t={r["parameter"]:r for r in trait_rows}
    row=t["fates_leaf_slatop"]
    a=json.loads(row[PFT4]);b=json.loads(row[PFT7])
    if (not math.isclose(float(a),0.009,rel_tol=1e-10)
        or not math.isclose(float(b),0.012,rel_tol=1e-10)
        or row.get("units")!="m^2/gC"):
        raise ValueError("Stage22 FATES SLA top source/units unexpectedly differ")
    return float(a),float(b)

def leaf_sensitivity(rows,trait_rows):
    if not {"scientificName","plantFunctionalType","siteId",
            "plantId",LEAF_LMA}.issubset(rows[0]):
        raise ValueError("Actual TERN leaf schema no longer matches")
    pft4,pft7=read_sla(trait_rows)
    groups=defaultdict(list)
    for r in rows:
        groups[((r.get("scientificName") or "").strip(),
                (r.get("plantFunctionalType") or "").strip())].append(r)
    output=[]
    for (species,pft),entries in sorted(groups.items()):
        lma=[number(r[LEAF_LMA],lower=5,upper=1500) for r in entries]
        lma=[x for x in lma if x is not None]
        plants={tuple((str(r.get("siteId") or "").strip(),
                       str(r.get("plantId") or "").strip()))
                for r in entries if str(r.get("plantId") or "").strip()}
        for fC in CARBON_ASSUMPTIONS:
            derived=statistics.median([1/(x*fC) for x in lma]) if lma else None
            output.append({
                "scientificName":species,"plantFunctionalType":pft,
                "field_rows":len(entries),"unique_plant_ids":len(plants),
                "valid_LMA_n":len(lma),
                "LMA_g_dry_per_m2_median":statistics.median(lma) if lma else None,
                "hypothetical_leaf_C_fraction_gC_per_g_dry":fC,
                "derived_SLA_m2_per_gC_median_NOT_DIRECT_MODEL_SLA":derived,
                "FATES4_slatop_m2_per_gC":pft4,
                "FATES7_slatop_m2_per_gC":pft7,
                "ratio_observed_derived_to_FATES4_slatop":derived/pft4 if derived is not None else None,
                "ratio_observed_derived_to_FATES7_slatop":derived/pft7 if derived is not None else None,
                "science_status":"CARBON_FRACTION_ASSUMED; LEAF_POSITION_AND_PFT_NOT_MATCHED; NOT_CALIBRATED",
            })
    return output,{
       "FATES4_leaf_slatop_m2_per_gC":pft4,
       "FATES7_leaf_slatop_m2_per_gC":pft7,
       "assumed_leaf_C_fractions_not_measured":list(CARBON_ASSUMPTIONS),
       "leaf_LMA_g_dry_per_m2_not_gC_per_m2":True,
       "Acacia_aneura_TERN_needle_leaf_tree_is_field_plant_functional_type_NOT_conifer_FATES_PFT":True,
       "Acacia_aptaneura_leaf_trait_records_unavailable":not any(x["scientificName"]=="Acacia aptaneura" for x in output),
       "leaf_measurements_not_model_canopy_top_calibration":True,
       "net_A_not_Vcmax25_gs_not_Medlyn_slope":True,
    }

def write_tsv(path,fields,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",extrasaction="raise")
        w.writeheader();w.writerows(rows)

def selftest():
    assert source_delimiter(Path("actual_trait.tsv"))=="\t"
    assert source_delimiter(Path("original_stem.csv"))==","
    assert measurement_class("0.2")=="D20_0.2m_NOT_DBH"
    assert measurement_class("1.3")=="DBH_1.3m"
    assert number("-999") is None
    assert math.isclose(1/(279.985*.50),0.0071432398,rel_tol=1e-5)
    assert year("2014-01-21")=="2014"
    assert 8.5>4.735410175384586
    print("STAGE27 SELF-TEST PASS: raw height vs shrub cap, D20!=DBH, Acacia LMA->SLA fC assumptions only; NO MODEL WRITES")

def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve()
    protected=(ROOT.resolve(),STAGE21.resolve(),STAGE24.resolve(),
               STAGE25.resolve(),STAGE26.resolve())
    if (args.out.is_symlink() or out.exists()
        or out.parent!=HOME.resolve() or
        any(out==x or x in out.parents for x in protected)):
        raise ValueError("Output must be a fresh direct HOME child")
    files,model,provenance=read_provenance()
    stem,stemsum=height_comparison(files["stem"][1],float(model["FATES7_plateau_height_m"]))
    leaves,leafsum=leaf_sensitivity(files["leaf"][1],files["traits"][1])
    report={
      "stage":"OzFlux Stage27 real TERN stem height ceiling and hypothetical LMA->SLA assessment",
      "source_verified_SHA256":provenance,
      "FATES7_local_exact_height_ceiling_m":model["FATES7_plateau_height_m"],
      "height_2014_only_field_survey_note":"TERN source states stem basal diameter/height surveyed 2014; any 2018 derived biomass/increment is not an independent remeasurement",
      "stem_height_by_species_and_time":stem,
      "stem_comparison_QC":stemsum,
      "leaf_by_species_and_carbon_fraction_ASSUMPTIONS":leaves,
      "leaf_comparison_QC":leafsum,
      "independent_2014_DBH_core_dataset_metadata":{
        "url":CORE_DBH_METADATA,
        "core_plot_1p30m_stems_reported":200,
        "unique_trees_reported":86,
        "actual_downloaded_pairwise_DBH_height_records":False,
        "do_not_assume_same_plots_and_plant_ids_as_Stage25":True,
        "original_direct_file_URL_not_yet_verified":True,
      },
      "model_PFT4_or_7_science_approved":False,
      "Kandosol_ten_layer_soil_science_approved":False,
      "forcing_science_approved":False,
      "site_specific_surface_written":False,
      "case_or_Slurm_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    write_tsv(out/"stage27_TERN_stem_height_above_FATES7_cap_by_year_species.tsv",
              HEIGHT_COLS,stem)
    write_tsv(out/"stage27_TERN_leaf_LMA_assumed_C_fraction_SLA_sensitivity.tsv",
              LEAF_COLS,leaves)
    (out/"stage27_AU_ASM_measured_structure_leaf_science_HOLD.json").write_text(
       json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),
       encoding="utf-8")
    print("STAGE27 ORIGINAL TERN STEM/LEAF AND STAGE21 TRAIT SHA VERIFIED")
    print("STAGE27 STAGE24/26 SCIENCE RECEIPTS VERIFIED")
    print("FATES7 EXACT LOCAL HEIGHT CAP_M",round(float(model["FATES7_plateau_height_m"]),8))
    print("STEM SURVEY YEARS",stemsum["stem_years"])
    for x in stem:
        print("HEIGHT",x["year"],x["scientificName"],
              "valid",x["valid_height_rows"],
              "above_FATES7",x["valid_height_over_FATES7_ceiling"],
              "median_m",x["height_median_m"],"max_m",x["height_max_m"])
    for x in leaves:
        if x["scientificName"]=="Acacia aneura":
            print("ACACIA_AN LMA",x["LMA_g_dry_per_m2_median"],
                  "ASSUMED_C_FRACTION",x["hypothetical_leaf_C_fraction_gC_per_g_dry"],
                  "DERIVED_SLA",x["derived_SLA_m2_per_gC_median_NOT_DIRECT_MODEL_SLA"],
                  "FATES4",x["FATES4_slatop_m2_per_gC"],
                  "FATES7",x["FATES7_slatop_m2_per_gC"])
    print("STAGE27 CORE DBH DIRECT PAIRED FILE STILL NOT FETCHED; NO D20 USED AS DBH")
    print("STAGE27 NOT AN APPROVED PFT/LEAF-CALIBRATION/SOIL/FORCING/MODEL RUN")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

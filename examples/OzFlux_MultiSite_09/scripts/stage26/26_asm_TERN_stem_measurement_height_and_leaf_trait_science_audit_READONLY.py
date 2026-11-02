#!/usr/bin/env python3
"""AU-ASM Stage26: exact public TERN stem-height and leaf trait audit.

Source is the four Stage25 operator-verified downloaded files.
Preserves critical science distinctions:
  - diameter at 0.20m (D20) is NEVER treated as breast-height DBH;
  - only directly recorded 1.30m diameters can be compared to
    the source-validated FATES4 and FATES7 H(DBH) curves;
  - field A_net, gs and LMA are not model Vcmax25/Medlyn g1/SLA
    by themselves, and rows/branches/stems are not independent trees.
Reports exploratory observation summaries and genuine measured-pair
residuals only if measurement-point criterion is satisfied.
Nothing is overwritten except new files under a fresh HOME report
directory. No NetCDF/param/surface/case/Slurm writes.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE25=HOME/"ozflux_stage25_20261102T121025Z"
STAGE24=HOME/"ozflux_stage24_20261102T115254Z"

SOURCES={
 "stem2014_data":(
  "Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv",
  "7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55",222),
 "stem2014_dictionary":(
  "Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv",
  "82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe",21),
 "leaf2014_data":(
  "Alice_Mulga_functional_leaf_traits_data_mGiVbmq.csv",
  "d982b9217ac0ca641e7aca47e681c03f82d08e72215de30fe7ecb1b42952acf0",142),
 "leaf2014_dictionary":(
  "Alice_Mulga_functional_trait_data_dictionary_S0G8tsI.csv",
  "1a6520517e6e2d694477ca45342c769d7ce275681d080d11b4e9aba79e387288",45),
}
STEM_COLUMNS=(
 "siteId","plotId","plantId","stemId","scientificName","stemStatus",
 "phenomenonTime","diameter_point_m","measurement_class",
 "stemDiameter_centimeters","stemHeight_metres",
 "same_row_valid_diameter_height",
 "FATES4_height_from_DBH_m_ONLY_IF_DIRECT_1p30m",
 "FATES7_height_from_DBH_m_ONLY_IF_DIRECT_1p30m",
 "FATES4_observed_minus_model_m","FATES7_observed_minus_model_m",
 "exclusion_or_caveat",
)
LEAF_COLUMNS=(
 "scientificName","plantFunctionalType","rows",
 "unique_plant_identifiers","unique_branch_identifiers",
 "LMA_g_per_m2_n","LMA_g_per_m2_median",
 "inverse_LMA_m2_per_g_dry_median_NOT_model_SLA",
 "light_saturated_net_photosynthesis_umol_m2_s_n",
 "light_saturated_net_photosynthesis_umol_m2_s_median_NOT_Vcmax25",
 "stomatal_conductance_mol_m2_s_n",
 "stomatal_conductance_mol_m2_s_median_NOT_Medlyn_g1",
 "PAR_umol_m2_s_median",
 "leaf_VPD_kPa_median",
 "season_labels","date_years",
)
LEAF_FIELDS={
 "lma":"meanLeafDryMassPerLeafAreaTrait_gramsPerSquareMeter",
 "anet":"meanLeafLightSaturatedNetPhotosynthesis_micromolsPerMetreSquaredPerSecond",
 "gs":"meanLeafStomatalConductance_molsPerMetreSquaredPerSecond",
 "par":"meanPhotosyntheticActiveRadiation_micromolsPerMetreSquaredPerSecond",
 "vpd":"meanVapourPressureDeficitBasedOnLeafTemperature_kilopascal",
}
STEM_REQUIRED={
 "siteId","plotId","plantId","stemId","scientificName",
 "stemDiameter_centimeters","stemHeight_metres",
 "stemDiameterPointOfMeasurement_metres","phenomenonTime",
}
LEAF_REQUIRED={
 "siteId","plantId","branchId","scientificName","season",
 "phenomenonTime","plantFunctionalType",*LEAF_FIELDS.values(),
}
MISSING={"","na","n/a","nan","null","none","-","--",
         "-999","-999.0","-999.9","-9999","-9999.0"}
DBH_POINT_M=1.30
D20_POINT_M=0.20
POINT_TOLERANCE=0.025


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def read_csv(path,required=()):
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("CSV source not found "+str(path))
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames or []
        if not set(required).issubset(set(cols)):
            raise ValueError("Actual original CSV missing fields "+
                             repr(sorted(set(required)-set(cols))))
        rows=list(reader)
    if any(None in r for r in rows):
        raise ValueError("Unexpected extra CSV fields in original source")
    return rows,cols


def number(raw):
    if raw is None:return None
    s=str(raw).strip().lower()
    if s in MISSING:return None
    try:v=float(s)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None


def positive(raw,upper):
    v=number(raw)
    if v is None or not (0<v<upper):
        return None
    return v


def median(values):
    return statistics.median(values) if values else None


def quantiles(values):
    if not values:return {"n":0,"min":None,"median":None,"max":None}
    return {"n":len(values),"min":min(values),
            "median":median(values),"max":max(values)}


def source_checks():
    receipt=STAGE25/"stage25_AU_ASM_TERN_stem_leaf_intake_science_HOLD.json"
    if STAGE25.is_symlink() or not receipt.is_file() or receipt.is_symlink():
        raise ValueError("Stage25 original manifest missing")
    x=json.loads(receipt.read_text(encoding="utf-8"))
    if (x.get("numeric_source_verified_count")!=4
        or x.get("numeric_source_expected_count")!=4
        or x.get("AD400_or_CIME_or_Slurm_authorised") is not False
        or x.get("actual_field_DBH_vs_FATES4_7_fit_computed") is not False):
        raise ValueError("Actual Stage25 provenance/science gate mismatch")
    records={r["key"]:r for r in x.get("source_inspections",[])}
    files={}
    for key,(filename,digest,n) in SOURCES.items():
        p=STAGE25/filename
        if (not p.is_file() or p.is_symlink() or sha(p)!=digest or
            key not in records or
            records[key].get("download",{}).get("sha256")!=digest or
            records[key].get("status")!="DOWNLOADED_AND_SCHEMATICALLY_INSPECTED_NOT_SCIENCE_APPROVED"):
            raise ValueError("Original TERN file/source SHA provenance mismatch "+key)
        rows,headers=read_csv(p)
        if len(rows)!=n:
            raise ValueError("TERN original "+key+" record count drift "+str(len(rows)))
        files[key]={"path":p,"rows":rows,"headers":headers,"sha256":digest}
    s24=STAGE24/"stage24_AU_ASM_DBH_height_science_gate.json"
    if STAGE24.is_symlink() or not s24.is_file() or s24.is_symlink():
        raise ValueError("Stage24 exact structural model report missing")
    model=json.loads(s24.read_text(encoding="utf-8"))
    if (model.get("source_code_formula_verified") is not True
        or model.get("Slurm_or_AD400_authorised") is not False
        or model.get("source_hashes",{}).get("local_FATES_allometry_Fortran")!=
          "8ad6c9eaaa9f5c40036f8aa099f6435b80f2a8e7248a48b6ddb3a978db3c7f16"
        or model.get("source_hashes",{}).get("original_FATES_param_JSON")!=
          "0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"):
        raise ValueError("Stage24 exact height formulas were not source-verified")
    return files,model,{"stage25_manifest":sha(receipt),
                        "stage24_height_receipt":sha(s24),
                        "original_TERN_files":{k:v["sha256"] for k,v in files.items()}}


def h4(dbh,m):
    p=m["active_per_PFT_height_parameters"]
    a=float(p["fates_allom_d2h1"]["4"])
    b=float(p["fates_allom_d2h2"]["4"])
    c=float(p["fates_allom_d2h3"]["4"])
    cap=float(p["fates_allom_dbh_maxheight"]["4"])
    d=min(dbh,cap)
    return a*d**b/(c+d**b)


def h7(dbh,m):
    p=m["active_per_PFT_height_parameters"]
    a=float(p["fates_allom_d2h1"]["7"])
    b=float(p["fates_allom_d2h2"]["7"])
    cap=float(p["fates_allom_dbh_maxheight"]["7"])
    return 10**(a*math.log10(min(dbh,cap))+b)


def point_class(value):
    if value is None:return "UNKNOWN_MEASUREMENT_POINT"
    if abs(value-DBH_POINT_M)<=POINT_TOLERANCE:return "DIRECT_DBH_1P30M"
    if abs(value-D20_POINT_M)<=POINT_TOLERANCE:return "BASAL_D20_0P20M_NOT_DBH"
    return "OTHER_HEIGHT_NOT_DBH"


def clean_species(row):
    name=str(row.get("scientificName","") or "").strip()
    return name if name else "UNSPECIFIED_SCIENTIFIC_NAME"


def identity(row,kind):
    keys=["siteId","plotId","plantId"] if kind=="stem" else ["siteId","plantId"]
    if any(not str(row.get(k,"") or "").strip() for k in keys):
        return None
    return tuple(str(row[k]).strip() for k in keys)


def year(text):
    s=str(text or "").strip()
    return s[:4] if len(s)>=4 and s[:4].isdigit() else "UNSPECIFIED"


def analyze_stems(rows,model):
    counts=Counter()
    point_examples=defaultdict(Counter)
    stem_table=[]
    groups=defaultdict(lambda:{"diameters":[],"heights":[],
                               "paired_resid4":[],"paired_resid7":[],
                               "plants":set(),"stem_pairs":set()})
    years=Counter()
    for src in rows:
        point=number(src["stemDiameterPointOfMeasurement_metres"])
        cls=point_class(point)
        d=positive(src["stemDiameter_centimeters"],500)
        h=positive(src["stemHeight_metres"],100)
        species=clean_species(src)
        years[year(src["phenomenonTime"])]+=1
        counts[cls]+=1
        if point is not None:point_examples[cls][str(point)]+=1
        valid=d is not None and h is not None
        group=groups[(species,cls)]
        if d is not None:group["diameters"].append(d)
        if h is not None:group["heights"].append(h)
        ident=identity(src,"stem")
        if ident is not None:group["plants"].add(ident)
        if (ident is not None and str(src.get("stemId","")).strip()):
            group["stem_pairs"].add(ident+(str(src["stemId"]).strip(),))
        predicted4=predicted7=error4=error7=None
        if cls=="DIRECT_DBH_1P30M" and valid:
            predicted4=h4(d,model)
            predicted7=h7(d,model)
            error4=h-predicted4
            error7=h-predicted7
            group["paired_resid4"].append(error4)
            group["paired_resid7"].append(error7)
        note=(
            "MODEL_COMPARISON_ONLY_DIRECT_1P30M; PLOT/DATE/HEIGHT_QC_REQUIRED"
            if cls=="DIRECT_DBH_1P30M" and valid else
            "D20_BASAL_NOT_DBH_DO_NOT_APPLY_MODEL_H_DBH"
            if cls=="BASAL_D20_0P20M_NOT_DBH" else
            "MISSING_OR_NON_DBH_OR_UNPAIRED_FIELD_MEASUREMENT")
        stem_table.append({
          "siteId":src.get("siteId"),"plotId":src.get("plotId"),
          "plantId":src.get("plantId"),"stemId":src.get("stemId"),
          "scientificName":species,
          "stemStatus":src.get("stemStatus"),
          "phenomenonTime":src["phenomenonTime"],
          "diameter_point_m":point,"measurement_class":cls,
          "stemDiameter_centimeters":d,"stemHeight_metres":h,
          "same_row_valid_diameter_height":valid,
          "FATES4_height_from_DBH_m_ONLY_IF_DIRECT_1p30m":predicted4,
          "FATES7_height_from_DBH_m_ONLY_IF_DIRECT_1p30m":predicted7,
          "FATES4_observed_minus_model_m":error4,
          "FATES7_observed_minus_model_m":error7,
          "exclusion_or_caveat":note,
        })
    summary=[]
    for (species,cls),g in sorted(groups.items()):
        r4=g["paired_resid4"];r7=g["paired_resid7"]
        summary.append({
          "scientificName":species,"measurement_class":cls,
          "diameter_cm":quantiles(g["diameters"]),
          "height_m":quantiles(g["heights"]),
          "paired_direct_DBH_height_n":len(r4),
          "FATES4_exploratory_MAE_m":sum(map(abs,r4))/len(r4) if r4 else None,
          "FATES7_exploratory_MAE_m":sum(map(abs,r7))/len(r7) if r7 else None,
          "unique_plant_keys_within_site_plot":len(g["plants"]),
          "unique_stem_keys_within_site_plot":len(g["stem_pairs"]),
          "MAE_not_validated_for_multistem_pseudoreplication":True,
        })
    return stem_table,summary,{
      "record_count":len(rows),
      "measurement_point_class_counts":dict(counts),
      "actual_measurement_point_values_by_class":{
        k:dict(v) for k,v in point_examples.items()},
      "year_counts_from_phenomenonTime":dict(years),
      "direct_DBH_height_pair_count":sum(x["paired_direct_DBH_height_n"] for x in summary),
      "direct_DBH_height_comparisons_applied_only_to_1p30m":True,
      "basal_D20_never_used_as_DBH":True,
    }


def summarize_leaves(rows):
    groups=defaultdict(lambda:{"rows":[],"plants":set(),"branches":set(),
                               "season":Counter(),"years":Counter()})
    counts=Counter()
    for src in rows:
        key=(clean_species(src),str(src.get("plantFunctionalType","") or "").strip())
        g=groups[key]
        g["rows"].append(src)
        ids=identity(src,"leaf")
        if ids:g["plants"].add(ids)
        branch=str(src.get("branchId","") or "").strip()
        if ids and branch:g["branches"].add(ids+(branch,))
        g["season"][str(src.get("season","") or "").strip()]+=1
        g["years"][year(src.get("phenomenonTime"))]+=1
        counts[clean_species(src)]+=1
    table=[]
    for (species,pft),g in sorted(groups.items()):
        vectors={}
        for k,col in LEAF_FIELDS.items():
            values=[number(x[col]) for x in g["rows"]]
            if k=="lma":
                values=[v for v in values if v is not None and 5<v<1500]
            elif k=="vpd":
                values=[v for v in values if v is not None and 0<=v<25]
            elif k=="par":
                values=[v for v in values if v is not None and 0<=v<4000]
            elif k=="gs":
                values=[v for v in values if v is not None and 0<=v<5]
            else:
                values=[v for v in values if v is not None and -100<v<150]
            vectors[k]=values
        lma=vectors["lma"]
        # 1/[g dry mass/m2] = m2/g dry mass, NOT FATES m2/gC.
        dry_sla=[1/v for v in lma]
        table.append({
          "scientificName":species,
          "plantFunctionalType":pft,
          "rows":len(g["rows"]),
          "unique_plant_identifiers":len(g["plants"]),
          "unique_branch_identifiers":len(g["branches"]),
          "LMA_g_per_m2_n":len(lma),
          "LMA_g_per_m2_median":median(lma),
          "inverse_LMA_m2_per_g_dry_median_NOT_model_SLA":median(dry_sla),
          "light_saturated_net_photosynthesis_umol_m2_s_n":len(vectors["anet"]),
          "light_saturated_net_photosynthesis_umol_m2_s_median_NOT_Vcmax25":median(vectors["anet"]),
          "stomatal_conductance_mol_m2_s_n":len(vectors["gs"]),
          "stomatal_conductance_mol_m2_s_median_NOT_Medlyn_g1":median(vectors["gs"]),
          "PAR_umol_m2_s_median":median(vectors["par"]),
          "leaf_VPD_kPa_median":median(vectors["vpd"]),
          "season_labels":json.dumps(dict(g["season"]),ensure_ascii=False),
          "date_years":json.dumps(dict(g["years"]),ensure_ascii=False),
        })
    return table,{"row_count":len(rows),"species_counts":dict(counts),
                  "leaf_rows_not_unique_independent_plants":True,
                  "LMA_units_g_dry_matter_per_m2":True,
                  "inverse_LMA_is_m2_per_g_dry_not_m2_per_gC":True,
                  "net_photosynthesis_is_not_Vcmax25":True,
                  "stomatal_conductance_is_not_Medlyn_g1":True}


def dictionary_review(rows):
    selected=[]
    for r in rows:
        txt=" ".join(str(x or "") for x in r.values())
        if any(term in txt.lower() for term in
               ("stemdiameter","stemheight","measurement","lma","dry mass",
                "photosynth","stomatal","leaf area","biomass","plantid",
                "scientificname","light saturated")):
            selected.append({k:(v[:1100] if isinstance(v,str) else v)
                             for k,v in r.items()})
    return selected


def tsv(path,columns,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=columns,delimiter="\t",extrasaction="raise")
        writer.writeheader();writer.writerows(rows)


def selftest():
    assert point_class(0.2)=="BASAL_D20_0P20M_NOT_DBH"
    assert point_class(1.3)=="DIRECT_DBH_1P30M"
    assert point_class(None)=="UNKNOWN_MEASUREMENT_POINT"
    assert point_class(0.5)=="OTHER_HEIGHT_NOT_DBH"
    assert number("-999.9") is None
    assert positive("4.3",100)==4.3
    p={"active_per_PFT_height_parameters":{
      "fates_allom_d2h1":{"4":104.3586841,"7":0.64},
      "fates_allom_d2h2":{"4":1.1146973,"7":0.37},
      "fates_allom_d2h3":{"4":160.6835089,"7":-999.9},
      "fates_allom_dbh_maxheight":{"4":1000.0,"7":3.0}}}
    assert math.isclose(h7(3,p),h7(20,p),rel_tol=1e-12)
    assert math.isclose(h4(5.660263445289735,p),4.3,rel_tol=1e-10)
    assert len(SOURCES)==4
    print("STAGE26 SELF-TEST PASS: D20 vs DBH height, model H(DBH) ONLY 1.30m, inverse LMA dry-mass units, no original writes")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(q==out or q in out.parents for q in
               (STAGE25.resolve(),STAGE24.resolve(),ROOT.resolve()))):
        raise ValueError("Output must be a fresh direct child of HOME")
    files,model,receipts=source_checks()
    s=files["stem2014_data"];l=files["leaf2014_data"]
    if not STEM_REQUIRED.issubset(set(s["headers"])):
        raise ValueError("Original TERN stem schema mismatch")
    if not LEAF_REQUIRED.issubset(set(l["headers"])):
        raise ValueError("Original TERN leaf schema mismatch")
    stems,grouped,stemqc=analyze_stems(s["rows"],model)
    leaves,leafqc=summarize_leaves(l["rows"])
    dictionary={
      "stem_dictionary_relevant_entries":dictionary_review(files["stem2014_dictionary"]["rows"]),
      "leaf_dictionary_relevant_entries":dictionary_review(files["leaf2014_dictionary"]["rows"]),
      "dictionary_science_approval":False,
    }
    report={
      "stage":"OzFlux AU-ASM Stage26 real TERN D20/DBH and 2014 leaf science",
      "source_SHA256":receipts,
      "TERN_stem_rows_original":222,
      "TERN_leaf_rows_original":142,
      "stem_science":stemqc,
      "stem_by_species_and_measurement_height":grouped,
      "leaf_science":leafqc,
      "leaf_by_species_PFT":leaves,
      "TERNS_dictionary_relevant_entries":dictionary,
      "FATES7_default_height_plateau_m":model["FATES7_plateau_height_m"],
      "FATES4_tree_height_curve_formula_verified":True,
      "scientific_decision":{
        "field_stem_diameter_measurement_point_controls_comparison":True,
        "D20_must_not_be_used_as_DBH":True,
        "field_height_data_and_PFT4_7_allometry_science_approved":False,
        "structural_MAE_is_exploratory_with_multistem_pseudoreplication":True,
        "field_LMA_is_not_yet_FATES_m2_per_gC_SLA":True,
        "leaf_net_photosynthesis_is_not_FATES_Vcmax25":True,
        "leaf_gs_is_not_Medlyn_g1":True,
        "time_period_and_footprint_compatibility_NOT_VALIDATED":True,
        "PFT4_or_PFT7_selected":False,
        "PFT_fraction_science_approved":False,
        "Kandosol_ten_layer_soil_approved":False,
        "forcing_science_approved":False,
        "new_surface_created":False,
        "CIME_or_Slurm_job_submitted":False,
        "AD400_authorised":False,
      }
    }
    out.mkdir(parents=False,exist_ok=False)
    tsv(out/"stage26_all_TERN_stem_rows_height_measurement_class.tsv",STEM_COLUMNS,stems)
    tsv(out/"stage26_TERN_leaf_species_trait_summaries.tsv",LEAF_COLUMNS,leaves)
    (out/"stage26_TERN_actual_D20_DBH_leaf_science_gate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),
        encoding="utf-8")
    print("STAGE26 ORIGINAL 4 TERN FILE HASHES VERIFIED")
    print("STAGE26 STEM ROWS",len(stems),"HEIGHT CLASS COUNTS",
          stemqc["measurement_point_class_counts"])
    print("STAGE26 ACTUAL 1.30m DBH/HEIGHT PAIRS",
          stemqc["direct_DBH_height_pair_count"])
    for item in grouped:
        print("STEM_GROUP",item["scientificName"],item["measurement_class"],
              "HEIGHT",item["height_m"],"DBH_PAIR_N",item["paired_direct_DBH_height_n"],
              "MAE4",item["FATES4_exploratory_MAE_m"],
              "MAE7",item["FATES7_exploratory_MAE_m"])
    print("STAGE26 LEAF ROWS",len(l["rows"]),"SPECIES GROUPS",len(leaves))
    for item in leaves:
        print("LEAF_GROUP",item["scientificName"],
              item["plantFunctionalType"],"N",item["rows"],
              "LMA",item["LMA_g_per_m2_median"],
              "ANET_NOT_VCMAX",item["light_saturated_net_photosynthesis_umol_m2_s_median_NOT_Vcmax25"],
              "GS_NOT_MEDLYN",item["stomatal_conductance_mol_m2_s_median_NOT_Medlyn_g1"])
    print("STAGE26 SCIENCE HOLD: no DBH conversion from D20; no trait parameter auto-edit; no CIME/Slurm")
    print("REPORT_DIR",out)


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""AU-ASM Stage25: provenance-safe TERN site stem and leaf trait data intake.

Download public research CSVs ONLY into a fresh direct HOME directory.
Capture original file SHA256 and CSV schema; do not guess D20==DBH,
net Amax==Vcmax25, LMA==SLA, or mean 6.5m==median 4.3m.
If remote download fails, write a full source/error report for manual
download follow-up, without claiming numerical trait evidence.
Never touch original AU-ASM forcing, Stage16 surface, FATES JSON,
existing CIME case or Slurm. NO AD400.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import urllib.request
import urllib.error

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE24=HOME/"ozflux_stage24_20261102T115254Z"
SOURCE_SHA="8ad6c9eaaa9f5c40036f8aa099f6435b80f2a8e7248a48b6ddb3a978db3c7f16"
PARAM_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
FILE_BASE="https://shared.tern.org.au/attachment"
DATASETS=[
 {
  "key":"stem2014_data",
  "filename":"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv",
  "url":FILE_BASE+"/c2968de2-1e8b-4a05-919f-46744b3171ed/Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv",
  "source":"https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed",
  "citation":"Cleverly J. (2022), Alice Mulga Stem Diameter, Height and Aboveground Woody Biomass Data",
  "field_measurement":"D20 basal diameter 20cm above ground as described in TERN lineage; NOT DBH",
 },
 {
  "key":"stem2014_dictionary",
  "filename":"Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv",
  "url":FILE_BASE+"/c2968de2-1e8b-4a05-919f-46744b3171ed/Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv",
  "source":"https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed",
  "citation":"Cleverly J. (2022), same release's field data dictionary",
  "field_measurement":"Definitions and units; inspect before conversion",
 },
 {
  "key":"leaf2014_data",
  "filename":"Alice_Mulga_functional_leaf_traits_data_mGiVbmq.csv",
  "url":FILE_BASE+"/5e4f379d-0be6-4e40-b52c-9fa3e1e71a00/Alice_Mulga_functional_leaf_traits_data_mGiVbmq.csv",
  "source":"https://portal.tern.org.au/metadata/5e4f379d-0be6-4e40-b52c-9fa3e1e71a00",
  "citation":"Atkin O. & Bloomfield K. (2022), Alice Mulga Leaf Functional Trait Data, 2014",
  "field_measurement":"2014 dry season; net photosynthesis, LMA, stomata; NOT Vcmax25 or FATES-specific trait by assumption",
 },
 {
  "key":"leaf2014_dictionary",
  "filename":"Alice_Mulga_functional_trait_data_dictionary_S0G8tsI.csv",
  "url":FILE_BASE+"/5e4f379d-0be6-4e40-b52c-9fa3e1e71a00/Alice_Mulga_functional_trait_data_dictionary_S0G8tsI.csv",
  "source":"https://portal.tern.org.au/metadata/5e4f379d-0be6-4e40-b52c-9fa3e1e71a00",
  "citation":"Atkin O. & Bloomfield K. (2022), same release's trait data dictionary",
  "field_measurement":"Definitions and units; inspect before conversion",
 },
]
MAX_BYTES=18*1024*1024
LIMITED_HEADER=130
MAX_SAMPLE=3


def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):
            digest.update(x)
    return digest.hexdigest()


def stage24_compatibility():
    p=STAGE24/"stage24_AU_ASM_DBH_height_science_gate.json"
    if STAGE24.is_symlink() or not p.is_file() or p.is_symlink():
        raise FileNotFoundError("Actual operator Stage24 report missing")
    obj=json.loads(p.read_text(encoding="utf-8"))
    sources=obj.get("source_hashes",{})
    if (sources.get("local_FATES_allometry_Fortran")!=SOURCE_SHA
        or sources.get("original_FATES_param_JSON")!=PARAM_SHA
        or obj.get("source_code_formula_verified") is not True
        or obj.get("Slurm_or_AD400_authorised") is not False
        or obj.get("FATES7_crown_structure_science_approved") is not False):
        raise ValueError("Stage24 science context differs or was approved")
    p7=float(obj["FATES7_plateau_height_m"])
    d4=float(obj["FATES4_MartinezCano_DBH_cm_for_4p3m"])
    if abs(p7-4.735410175384586)>1e-6 or abs(d4-5.660263445289735)>1e-6:
        raise ValueError("Stage24 local structural outputs changed")
    return {"stage24_report_SHA256":sha(p),
            "FATES7_default_max_height_m":p7,
            "FATES4_default_DBH_cm_to_4p3m":d4}


def fetch_one(url,path):
    req=urllib.request.Request(
        url,headers={"User-Agent":"Mozilla/5.0 (research; citation TERN public data)",
                     "Accept":"text/csv,application/octet-stream,*/*"})
    with urllib.request.urlopen(req,timeout=75) as response:
        final=response.geturl()
        http_status=getattr(response,"status",None)
        media=response.headers.get("Content-Type","")
        if not final.lower().startswith("https://"):
            raise ValueError("Unexpected non-HTTPS TERN redirect")
        if path.exists() or path.is_symlink():
            raise ValueError("Destination not new")
        n=0
        with path.open("xb") as f:
            while True:
                block=response.read(256*1024)
                if not block:break
                n+=len(block)
                if n>MAX_BYTES:
                    raise ValueError("TERN public source exceeds bounded MAX_BYTES")
                f.write(block)
    if n<8:
        raise ValueError("Empty/short downloaded file")
    start=path.open("rb").read(256)
    if start.lstrip().startswith((b"<!DOCTYPE",b"<html",b"<?xml",b"{")):
        raise ValueError("Remote returned HTML/XML/JSON rather than CSV")
    return {"bytes":n,"sha256":sha(path),"final_url":final,
            "http_status":http_status,"content_type":media}


def inspect_csv(path):
    if not path.is_file() or path.is_symlink():raise ValueError("Source not a regular file")
    with path.open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
        sample=f.read(16384)
        if "\x00" in sample:
            raise ValueError("Downloaded file looks binary")
        f.seek(0)
        try:delim=csv.Sniffer().sniff(sample,delimiters=",;\t|").delimiter
        except csv.Error:delim=","
        r=csv.reader(f,delimiter=delim)
        headers=next(r,[])
        if len(headers)<2 or len(headers)>LIMITED_HEADER:
            raise ValueError("Unexpected number of CSV columns; inspect manually")
        examples=[]
        total=0
        inconsistent=0
        for row in r:
            if not row or all(not x.strip() for x in row):continue
            total+=1
            if len(row)!=len(headers):inconsistent+=1
            if len(examples)<MAX_SAMPLE:
                examples.append(row[:min(len(headers),15)])
            if total>500000:raise ValueError("TERN CSV unexpectedly has >500k records")
        return {
          "delimiter":delim,"headers":headers,"column_count":len(headers),
          "nonempty_data_rows":total,"inconsistent_column_rows":inconsistent,
          "sample_rows_first_15_columns":examples,
          "fields_hinting_DBH":[x for x in headers
                                 if "dbh" in x.lower() or "breast" in x.lower()],
          "fields_hinting_basal_D20":[x for x in headers
                                      if "d20" in x.lower() or "basal" in x.lower()],
          "fields_hinting_height":[x for x in headers if "height" in x.lower() or "ht"==x.lower()],
          "fields_hinting_photosynthesis":[x for x in headers
                                           if any(k in x.lower() for k in
                                                  ("photo","amax","pmax","vcmax","gs","sla","lma"))],
        }


def selftest():
    assert len(DATASETS)==4
    assert all(s["url"].startswith("https://shared.tern.org.au/attachment/") for s in DATASETS)
    assert all(s["filename"].endswith(".csv") for s in DATASETS)
    assert len({s["key"] for s in DATASETS})==4
    assert 8.9>4.735410175384586
    assert not math.isclose(4.3,6.5)
    print("STAGE25 SELF-TEST PASS: exact public TERN file links, basal D20 != DBH, LMA != SLA without units, bounded HOME-only downloads")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve()
    if (args.out.is_symlink() or out.exists() or
        out.parent!=HOME.resolve() or
        out==STAGE24.resolve() or STAGE24.resolve() in out.parents or
        out==ROOT.resolve() or ROOT.resolve() in out.parents):
        raise ValueError("Out must be fresh direct HOME child, never model tree")
    reference=stage24_compatibility()
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    reports=[]
    for s in DATASETS:
        file=out/s["filename"]
        item={k:v for k,v in s.items() if k!="filename"}
        item["local_filename"]=s["filename"]
        try:
            item["download"]=fetch_one(s["url"],file)
            item["inspection"]=inspect_csv(file)
            item["status"]="DOWNLOADED_AND_SCHEMATICALLY_INSPECTED_NOT_SCIENCE_APPROVED"
            print("SOURCE",s["key"],"OK",file,"SHA256",item["download"]["sha256"])
            print("COLUMNS",s["key"],item["inspection"]["headers"])
        except Exception as e:
            item["status"]="NOT_VERIFIED_ACCESS_OR_CSV_SCHEMA"
            item["error"]=type(e).__name__+": "+str(e)[:400]
            # A partial newly created file can remain as a clearly
            # quarantined failed download, never silently used.
            if file.exists():
                item["partial_or_unverified_local_file"]={
                    "path":str(file),"bytes":file.stat().st_size,"sha256":sha(file)}
            print("SOURCE",s["key"],"UNAVAILABLE",item["error"])
        reports.append(item)
    downloaded=sum(x["status"].startswith("DOWNLOADED") for x in reports)
    summary={
      "stage":"OzFlux Stage25 TERN 2014 field stem/leaf trait intake",
      "source_exact_Stage24":reference,
      "site":"AU-ASM Alice Springs Mulga",
      "field_release_stem_metadata":"https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed",
      "field_release_leaf_metadata":"https://portal.tern.org.au/metadata/5e4f379d-0be6-4e40-b52c-9fa3e1e71a00",
      "supplementary_2014_1ha_core_stem_DBH_metadata":"https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073",
      "numeric_source_verified_count":downloaded,
      "numeric_source_expected_count":len(DATASETS),
      "source_inspections":reports,
      "science_evidence_limits":{
        "TERN_median_canopy_height_m":4.3,
        "TERN_tallest_observed_tree_m":8.9,
        "historical_OzFlux_mean_canopy_height_m":6.5,
        "TERN_standing_biomass_t_ha":32.5,
        "standing_biomass_not_assumed_equivalent_to_model_cAGB":True,
        "height_statistics_not_same_sample_and_period":True,
        "FATES7_default_height_cap_m":reference["FATES7_default_max_height_m"],
        "FATES7_default_cannot_fit_tallest_tree":True,
        "D20_at_20cm_from_ground_is_NOT_DBH":True,
        "separate_2014_core_DBH_survey_reports_200_stems_not_yet_downloaded":True,
        "site_net_photosynthesis_is_NOT_Vcmax25":True,
        "site_LMA_is_inverse_of_SLA_only_after_validating_same_units":True,
        "2014_dry_season_leaf_traits_not_year_round_canonical_parameters":True,
      },
      "actual_field_DBH_vs_FATES4_7_fit_computed":False,
      "actual_site_leaf_trait_vs_FATES4_7_calibration_computed":False,
      "new_surface_created":False,
      "site_PFT_or_soil_approved":False,
      "AD400_or_CIME_or_Slurm_authorised":False,
      "next":"Review downloaded CSV headers+data dictionaries, verify D20 versus DBH, species and units before calculating any height or trait residuals.",
    }
    (out/"stage25_AU_ASM_TERN_stem_leaf_intake_science_HOLD.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print("STAGE25 TERN SOURCES DOWNLOADED",downloaded,"OF",len(DATASETS))
    print("STAGE25 D20 IS NOT DBH; NET PHOTOSYNTHESIS IS NOT VCMAX25")
    print("STAGE25 NO INPUT MODEL OR SCIENCE APPROVAL; NO CIME/SLURM")
    print("REPORT_DIR",out)


if __name__=="__main__":
    main()

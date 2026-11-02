#!/usr/bin/env python3
"""AU-ASM Stage33: publisher-linked original TERN site-level woody biomass intake.

Download only the TERN public site-level biomass CSV into a BRAND-NEW
direct HOME folder; preserve original bytes and SHA256. Inspect all
actual headers, counts, year/time and potential biomass/unit/area
fields without guessing that values are t/ha or directly comparable
to 111 D20-source stems. Preserve HTTP access failures in manifest.

Provenance gates: original 222-row stem source SHA, 21-row dictionary
SHA, verified Stage31 and Stage32 operator receipts. No modification
to original source/forcing/surface/FATES, no CIME or Slurm.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urlsplit

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE25=HOME/"ozflux_stage25_20261102T121025Z"
STAGE31=HOME/"ozflux_stage31_20261102T183333Z"
STAGE32=HOME/"ozflux_stage32_20261102T185340Z"
RAW=STAGE25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
RAW_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
DICT=STAGE25/"Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv"
DICT_SHA="82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe"
G31=STAGE31/"stage31_AU_ASM_derived_AGB_join_formula_science_HOLD.json"
G32=STAGE32/"stage32_AU_ASM_source_AGB_allometric_consistency_science_HOLD.json"
META_URL="https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed"
ATTACHMENT_NAME="Alice_Mulga_site_level_biomass_data_v3pQRMW.csv"
SOURCE_URL=("https://shared.tern.org.au/attachment/"
            "c2968de2-1e8b-4a05-919f-46744b3171ed/"+ATTACHMENT_NAME)
MAX_BYTES=24*1024*1024
MAX_ROWS=100000
HEADERS_LIMIT=200
SAMPLE_LIMIT=8

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()

def verified_readonly_inputs():
    expected={RAW:RAW_SHA,DICT:DICT_SHA}
    for p,h in expected.items():
        if not p.is_file() or p.is_symlink() or sha(p)!=h:
            raise ValueError("Original TERN source file SHA mismatch: "+str(p))
    for p in (G31,G32):
        if not p.is_file() or p.is_symlink():
            raise ValueError("Verified prior science gate not found: "+str(p))
    x=json.loads(G31.read_text(encoding="utf-8"))
    y=json.loads(G32.read_text(encoding="utf-8"))
    if (x.get("n_unique_stems")!=111 or
        x.get("operator_stage30_flagged_stem_count")!=48 or
        x.get("source_hashes",{}).get("original_TERN_SHA256")!=RAW_SHA or
        x.get("AD400_authorised") is not False or
        x.get("AGB_2018_science_approved") is not False or
        y.get("unique_stems")!=111 or
        y.get("source_sha256",{}).get("original_TERN_SHA256")!=RAW_SHA or
        y.get("AD400_authorised") is not False or
        y.get("2018_AGB_science_approved") is not False):
        raise ValueError("Stage31/32 operator or source gate unexpected")
    with DICT.open("r",newline="",encoding="utf-8-sig") as f:
        dr=list(csv.DictReader(f))
    if len(dr)!=21:raise ValueError("Original dictionary count changed")
    return {
        "original_TERN_stem_SHA256":RAW_SHA,
        "original_TERN_dictionary_SHA256":DICT_SHA,
        "Stage31_success_receipt_SHA256":sha(G31),
        "Stage32_success_receipt_SHA256":sha(G32),
        "stem_rows_2014_and_2018":222,
        "unique_stems":111,
    },dr

def get_public_source(url,dest):
    if dest.exists() or dest.is_symlink():
        raise ValueError("Never overwrite source download")
    req=urllib.request.Request(url,headers={
       "User-Agent":"Mozilla/5.0 (University research; TERN CC BY 4.0)",
       "Accept":"text/csv,application/octet-stream,*/*"})
    with urllib.request.urlopen(req,timeout=80) as response:
        final_url=response.geturl()
        parsed=urlsplit(final_url)
        if parsed.scheme!="https" or parsed.hostname not in (
              "shared.tern.org.au","object-store.rc.nectar.org.au"):
            raise ValueError("Unexpected redirected site-level data host")
        status=getattr(response,"status",None)
        content_type=response.headers.get("Content-Type","")
        count=0
        with dest.open("xb") as f:
            while True:
                b=response.read(256*1024)
                if not b:break
                count+=len(b)
                if count>MAX_BYTES:
                    raise ValueError("Site-level source unexpectedly exceeds 24MB bound")
                f.write(b)
    if count<12:raise ValueError("Site-level TERN download empty/short")
    with dest.open("rb") as f:head=f.read(512).lstrip().lower()
    if any(head.startswith(x) for x in (b"<!doctype",b"<html",b"<?xml",b"{")):
        raise ValueError("Remote source returned HTML/XML/JSON, not CSV")
    return {"bytes":count,"sha256":sha(dest),"final_url":final_url,
            "http_status":status,"content_type":content_type}

def parse_rows(fp):
    if not fp.is_file() or fp.is_symlink():raise ValueError("Expected regular CSV")
    with fp.open("r",newline="",encoding="utf-8-sig",errors="replace") as f:
        initial=f.read(12000)
        if "\x00" in initial:raise ValueError("Source appears binary")
        try:delimiter=csv.Sniffer().sniff(initial,delimiters=",;\t|").delimiter
        except csv.Error:delimiter=","
        f.seek(0)
        reader=csv.DictReader(f,delimiter=delimiter)
        cols=reader.fieldnames or []
        if not (2<=len(cols)<=HEADERS_LIMIT):
            raise ValueError("Original site CSV column count unexpected")
        records=[]
        for row in reader:
            if not any(v and str(v).strip() for v in row.values()):continue
            if None in row:raise ValueError("Unexpected extra fields in source CSV")
            records.append(row)
            if len(records)>MAX_ROWS:raise ValueError("Site-level rows exceed safety bound")
    return cols,records,delimiter

def identify_fields(fields,rows):
    tests={
      "date_or_year":("year","date","time","visit","season","period"),
      "biomass":("biomass","agb","wood","carbon","stem"),
      "area":("area","hectare","plot","subplot"),
      "unit":("unit","tonne","t_ha","kg_ha","g_m2","kg_m2"),
      "site_or_species":("site","scientificname","species","taxon","vegetation"),
    }
    candidates={k:[x for x in fields if any(p in x.lower().replace(" ","")
                     for p in parts)] for k,parts in tests.items()}
    samples=[]
    for row in rows[:SAMPLE_LIMIT]:
        samples.append({k:row.get(k) for k in fields})
    column_value_examples={col:list(dict.fromkeys(
        str(row.get(col) or "").strip() for row in rows))[:20]
        for col in fields if col in set(sum(candidates.values(),[]))}
    missing_counts={col:sum(not str(r.get(col) or "").strip() for r in rows)
                    for col in fields}
    return {
      "potential_columns_not_validated":candidates,
      "first_8_complete_rows":samples,
      "candidate_field_distinct_values_first_20":column_value_examples,
      "missing_cell_counts_by_field":missing_counts,
    }

def science_input_scan(headers,rows,dictionary):
    inspection=identify_fields(headers,rows)
    dictionary_rows=[]
    for entry in dictionary:
        txt=" ".join(str(v or "") for v in entry.values()).lower()
        if any(x in txt for x in ("biomass","hectare","tonne","area","plot","date")):
            dictionary_rows.append(entry)
    inspection["original_21_row_stem_dictionary_relevant_entries"]=dictionary_rows
    inspection["source_site_years_VERIFIED"]=False
    inspection["site_AGB_unit_VERIFIED"]=False
    inspection["area_per_plot_VERIFIED"]=False
    inspection["site_footprint_identical_to_111_field_stems_VERIFIED"]=False
    inspection["site_AGB_direct_comparison_with_stem_kg_authorised"]=False
    return inspection

def selftest():
    assert SOURCE_URL.startswith("https://shared.tern.org.au/attachment/")
    assert SOURCE_URL.endswith("Alice_Mulga_site_level_biomass_data_v3pQRMW.csv")
    assert len(ATTACHMENT_NAME)>10
    assert all(word in ("2014", "2018") for word in ("2014", "2018"))
    fake=[{"year":"2014","aboveGroundWoodyBiomass_tonnesPerHectare":"7.1",
           "plotId":"A"}]
    actual=identify_fields(list(fake[0]),fake)
    assert actual["potential_columns_not_validated"]["date_or_year"]==["year"]
    assert "aboveGroundWoodyBiomass_tonnesPerHectare" in actual["potential_columns_not_validated"]["biomass"]
    assert "plotId" in actual["potential_columns_not_validated"]["area"]
    print("STAGE33 SELF-TEST PASS: pinned official TERN attachment, CSV column discovery, strict provenance, no kg-to-t/ha comparison, HOME-only")

def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(p==out or p in out.parents for p in (
             ROOT.resolve(),STAGE25.resolve(),STAGE31.resolve(),STAGE32.resolve()))):
        raise ValueError("Output must be NEW direct HOME child; never model tree")
    provenance,dictionary=verified_readonly_inputs()
    out.mkdir(parents=False,mode=0o700,exist_ok=False)
    final=out/ATTACHMENT_NAME
    report={
      "stage":"OzFlux Stage33 public TERN site-level biomass source intake",
      "publisher_metadata_url":META_URL,
      "original_public_CSV_url":SOURCE_URL,
      "original_source_science_provenance":provenance,
      "source_download_status":"NOT_YET_RETRIEVED",
      "original_source_verified_hash":None,
      "site_level_analysis_approved":False,
      "source_2014_AGB_is_allometric_not_direct_weighed":True,
      "source_2018_AGB_is_derived_not_repeat_field_survey":True,
      "site_area_units_and_footprint_not_assumed":True,
      "2018_AGB_science_approved":False,
      "PFT_or_ten_layer_soil_or_final_forcing_approved":False,
      "new_surface_or_FATES_params_written":False,
      "CIME_or_Slurm_submitted":False,
      "AD400_authorised":False,
    }
    try:
        downloaded=get_public_source(SOURCE_URL,final)
        columns,rows,delimiter=parse_rows(final)
        report["download"]=downloaded
        report["original_source_verified_hash"]=downloaded["sha256"]
        report["source_download_status"]="CSV_BYTES_VERIFIED_SCHEMA_INSPECTED_NOT_SCIENCE_APPROVED"
        report["column_names"]=columns
        report["csv_delimiter"]=delimiter
        report["row_count"]=len(rows)
        report["inspection"]=science_input_scan(columns,rows,dictionary)
        print("STAGE33 OFFICIAL SITE-LEVEL CSV DOWNLOADED",len(rows),"ROWS",len(columns),"COLS")
        print("STAGE33 SHA256",downloaded["sha256"])
        print("STAGE33 HEADERS",columns)
        print("STAGE33 POTENTIAL TIME/AGB/UNIT/AREA",report["inspection"]["potential_columns_not_validated"])
        for row in rows[:SAMPLE_LIMIT]:print("ORIGINAL_SITE_LEVEL_ROW",json.dumps(row,ensure_ascii=False))
    except Exception as exc:
        report["source_download_status"]="SOURCE_UNAVAILABLE_OR_SCHEMA_NOT_VALIDATED"
        report["failure"]=type(exc).__name__+": "+str(exc)[:400]
        if final.is_file():
            report["unverified_download_file"]={
               "bytes":final.stat().st_size,"sha256":sha(final)}
        print("STAGE33 SITE LEVEL SOURCE NOT VERIFIED",report["failure"])
    (out/"stage33_TERN_original_site_level_biomass_intake_science_HOLD.json").write_text(
       json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),
       encoding="utf-8")
    print("STAGE33 SITE-LEVEL AGB NOT SCIENCE APPROVED; NO kg->t/ha conversion")
    print("STAGE33 NO ORIGINAL OR MODEL MODIFICATION; NO CIME/SLURM")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

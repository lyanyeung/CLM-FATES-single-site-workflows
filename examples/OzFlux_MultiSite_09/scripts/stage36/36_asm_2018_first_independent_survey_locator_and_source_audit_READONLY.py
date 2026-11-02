#!/usr/bin/env python3
"""OzFlux AU-ASM Stage36: 2018-FIRST independent survey locator + source evidence gate.

Use an independently catalogued 2018 Alice Mulga Core1ha survey
(supersite.1041, edition 5, Eamus/TERN) as PRIMARY TARGET. It says
2018 D20/height measurements and dendrometers 2011-2018, with
Paul2016/Navar2013 biomass equations, but original files have NOT yet
been verified/downloaded. Catalog evidence is NOT a field measurement.

For continuity, inventory the separately published Cleverly2022
2018-DERIVED rows as SECONDARY, SOURCE-VERIFIED ONLY and preserve all
2018 raw original fields. Those 2018 values were NOT a repeat field
survey and their 2018 AGB is SCIENCE HOLD (Stages30-35). They are
NOT allowed as independent observations for calibration.

Read-only; metadata downloads only from exact catalog URLs (never
infer/auto-follow/download arbitrary attachment URLs), new HOME
folder only. No original/source/FATES/surface/forcing/CIME/Slurm edits.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import html.parser
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urlsplit

HOME=Path.home()
S25=HOME/"ozflux_stage25_20261102T121025Z"
S33=HOME/"ozflux_stage33_20261102T191655Z"
S35=HOME/"ozflux_stage35_20261102T194156Z"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STEMS=S25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
STEMS_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
STAND=S33/"Alice_Mulga_site_level_biomass_data_v3pQRMW.csv"
STAND_SHA="f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8"
G35=S35/"stage35_Plant99_original_source_stand_biomass_science_HOLD.json"
PRIMARY_CATALOG="https://researchdata.edu.au/vegetation-data-direct-ha-2018/1340784"
LEGACY_METADATA="https://supersites.tern.org.au/knb/metacat/supersite.1041/html"
PRIMARY_IDENTIFIER="supersite.1041"
MODEL_FATES7_CAP=4.735410175384586
FIELDS=("siteId","plotId","plantId","stemId","scientificName",
        "startVisitDate","endVisitDate","phenomenonTime",
        "stemDiameterPointOfMeasurement_metres",
        "stemDiameter_centimeters","stemHeight_metres",
        "aboveGroundBiomass_kilograms","stemStatus","comment")
OUT_FIELDS=("siteId","plotId","plantId","stemId","scientificName",
            "original_2018_date","2018_D20_cm_DERIVED_NOT_DBH",
            "2018_height_m_DERIVED_NOT_NEW_FIELD",
            "2018_AGB_kg_DERIVED_SCIENCE_HOLD",
            "2018_height_above_default_FATES7_cap",
            "source_status","source_comment","evidence_tier")

def filehash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def dmy(v):
    return datetime.strptime(str(v).strip(),"%d/%m/%Y").date()

def load(p,columns,n):
    if not p.is_file() or p.is_symlink():raise ValueError("Source missing or symlink "+str(p))
    with p.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        missing=set(columns)-set(reader.fieldnames or [])
        if missing:raise ValueError("Source columns absent "+repr(sorted(missing)))
        rows=list(reader)
    if len(rows)!=n or any(None in r for r in rows):
        raise ValueError("Original source row structure/count changed")
    return rows

def verify_sources():
    for p,expect in ((STEMS,STEMS_SHA),(STAND,STAND_SHA)):
        if not p.is_file() or p.is_symlink() or filehash(p)!=expect:
            raise ValueError("Original source SHA256 mismatch "+str(p))
    if not G35.is_file() or G35.is_symlink():raise ValueError("Stage35 operator receipt not found")
    receipt=json.loads(G35.read_text(encoding="utf-8"))
    if (receipt.get("AD400_authorised") is not False
        or receipt.get("2018_AGB_science_approved") is not False
        or receipt.get("data_entry_or_source_join_error_proven") is not False
        or receipt.get("scenarios_reproducing_both_official_4dp_site_stands")!=[
            "OMIT_2014_AND_EXTRA_2014_AGB_IN_2018"]
        or receipt.get("sha256_verified",{}).get("stem_SHA256")!=STEMS_SHA
        or receipt.get("sha256_verified",{}).get("stand_SHA256")!=STAND_SHA):
        raise ValueError("Stage35 operator receipt or science gate differs")
    stems=load(STEMS,FIELDS,222)
    stand=load(STAND,("phenomenonTime","standBiomass_tonnesPerHectare"),2)
    return stems,stand,{"original_stems_sha256":STEMS_SHA,
                        "original_stand_sha256":STAND_SHA,
                        "Stage35_success_receipt_sha256":filehash(G35)}

def inventory(stems,stand):
    groups=Counter();tall=Counter();allids=set();ids2018=set()
    rows=[]
    for r in stems:
        yr=dmy(r["phenomenonTime"]).year
        if yr not in (2014,2018):raise ValueError("Not exact 2014/2018 source years")
        k=tuple(str(r[x]).strip() for x in ("siteId","plotId","plantId","stemId"))
        if not all(k):raise ValueError("Incomplete source stem key")
        allids.add(k)
        if yr!=2018:continue
        if k in ids2018:raise ValueError("Duplicate 2018 stem key")
        ids2018.add(k)
        if abs(float(r["stemDiameterPointOfMeasurement_metres"])-.2)>.025:
            raise ValueError("Some 2018 diameter not D20")
        if dmy(r["startVisitDate"]).year!=2018 or dmy(r["endVisitDate"]).year!=2018:
            raise ValueError("2018 original dates do not agree")
        species=str(r["scientificName"]).strip()
        h=float(r["stemHeight_metres"])
        exceeded=h>MODEL_FATES7_CAP
        groups[species]+=1
        if exceeded:tall[species]+=1
        rows.append({
          "siteId":k[0],"plotId":k[1],"plantId":k[2],"stemId":k[3],
          "scientificName":species,"original_2018_date":r["phenomenonTime"],
          "2018_D20_cm_DERIVED_NOT_DBH":r["stemDiameter_centimeters"],
          "2018_height_m_DERIVED_NOT_NEW_FIELD":r["stemHeight_metres"],
          "2018_AGB_kg_DERIVED_SCIENCE_HOLD":r["aboveGroundBiomass_kilograms"],
          "2018_height_above_default_FATES7_cap":exceeded,
          "source_status":r["stemStatus"],
          "source_comment":r["comment"],
          "evidence_tier":"SECONDARY_2018_DERIVED_FROM_2014_NO_INDEPENDENT_FIELD_MEASUREMENT",
        })
    if len(rows)!=111 or len(allids)!=111 or ids2018!=allids:
        raise ValueError("2018 source 111-stem cohort differs")
    if groups["Acacia aneura"]!=43 or groups["Acacia aptaneura"]!=60:
        raise ValueError("2018 source Acacia species counts differ")
    if tall["Acacia aneura"]!=9 or tall["Acacia aptaneura"]!=18:
        raise ValueError("2018 source height cap counts differ")
    site2018=[r for r in stand if dmy(r["phenomenonTime"]).year==2018]
    if len(site2018)!=1 or site2018[0]["standBiomass_tonnesPerHectare"]!="44.6277":
        raise ValueError("2018 official stand source numerical value changed")
    return rows,{
      "2018_source_derived_rows":len(rows),
      "2018_stem_by_species":dict(groups),
      "2018_height_above_FATES7_cap_by_species":dict(tall),
      "2018_published_derived_stand_AGB_t_ha_NOT_APPROVED":"44.6277",
      "underlying_stem_metadata_sampling_area_ha":"0.06",
      "2018_stem_measurements_independent_field_survey":False,
    }

def probe_metadata(url):
    # Catalog-only HTTP probe, NOT data download/discovery by following
    # arbitrary links. Explicitly allow redirects only to catalog hosts.
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (academic catalog provenance audit)"})
        with urllib.request.urlopen(req,timeout=22) as response:
            final=response.geturl()
            host=urlsplit(final).hostname
            if urlsplit(final).scheme!="https" or host not in (
                "researchdata.edu.au","supersites.tern.org.au","portal.tern.org.au"):
                return {"status":"UNTRUSTED_REDIRECT","final_url":final,"verified_data_file":False}
            raw=response.read(512*1024+1)
            if len(raw)>512*1024:return {"status":"LARGER_THAN_METADATA_LIMIT","final_url":final,"verified_data_file":False}
            body=raw.decode("utf-8","replace")
            return {"status":"METADATA_HTTP_RETURNED","final_url":final,
                    "page_sha256":hashlib.sha256(raw).hexdigest(),
                    "content_type":response.headers.get("Content-Type",""),
                    "bytes_read":len(raw),
                    "contains_identifier_supersite_1041":PRIMARY_IDENTIFIER in body,
                    "verified_data_file":False}
    except Exception as exc:
        return {"status":"METADATA_NOT_RETRIEVED","error":type(exc).__name__+": "+str(exc)[:240],
                "verified_data_file":False}

def selftest():
    assert dmy("1/6/2018").isoformat()=="2018-06-01"
    assert dmy("22/1/2014").isoformat()=="2014-01-22"
    assert PRIMARY_IDENTIFIER in LEGACY_METADATA
    assert PRIMARY_CATALOG.startswith("https://researchdata.edu.au/")
    assert MODEL_FATES7_CAP>4.7 and MODEL_FATES7_CAP<4.8
    assert "AGB_kg_DERIVED_SCIENCE_HOLD" in OUT_FIELDS[8]
    print("STAGE36 SELF-TEST PASS: 2018-first separate survey catalog, 111 source-derived rows, 2018 AGB HOLD, catalog-only URL probe; READ ONLY")

def main():
    if sys.argv[1:]==["--self-test"]:return selftest()
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(p==out or p in out.parents for p in (ROOT.resolve(),S25.resolve(),S33.resolve(),S35.resolve()))):
        raise ValueError("Fresh direct HOME folder ONLY")
    raw,site,provenance=verify_sources()
    inventory_rows,counts=inventory(raw,site)
    probes={
       "ARDC_independent_2018_catalog":probe_metadata(PRIMARY_CATALOG),
       "TERN_legacy_supersite1041_metadata":probe_metadata(LEGACY_METADATA),
    }
    report={
      "stage":"AU-ASM Stage36 2018-FIRST source priority + independent survey locator",
      "operator_priority":"2018 independent survey D20, H, dendrometer FIRST; 2018 derived stem source SECONDARY; 2014 historical only",
      "primary_2018_survey":{
         "catalog":PRIMARY_CATALOG,
         "original_legacy_TERN_metadata":LEGACY_METADATA,
         "identifier":PRIMARY_IDENTIFIER,
         "provider":"TERN Australian SuperSite Network",
         "contributor":"Derek Eamus",
         "catalog_edition":"5",
         "catalog_measurements_reported":"2018 measured D20 and height, 2011–2018 dendrometers",
         "allometry_reported":"Paul et al. 2016 and Návar et al. 2013",
         "raw_2018_independent_field_files_downloaded_and_SHA_verified":False,
         "direct_2018_measured_structure_approved":False,
         "no_raw_file_URL_verified":True,
         "catalog_HTTP_probes":probes,
      },
      "secondary_2022_product_2018_derived_rows_source_SHA":provenance,
      "secondary_2018_source_inventory":counts,
      "secondary_2018_source_AGB_science_approved":False,
      "source_D20_not_FATES_DBH":True,
      "primary_2018_source_footprint_matches_secondary_111_stems_NOT_VERIFIED":True,
      "2018_primary_vs_secondary_stem_alignment_NOT_ATTEMPTED":True,
      "case_or_surface_or_FATES_params_modified":False,
      "soil_or_forcing_science_approved":False,
      "CIME_or_Slurm_submitted":False,
      "AD400_authorised":False,
      "next":"Obtain original supersite.1041 edition5 2018 data files from TERN/archive; pin SHA256; audit real 2018 D20/height/AGB/dendrometer by site, plot, stem, date and sampling area before any FATES calibration.",
    }
    out.mkdir(mode=0o700,exist_ok=False,parents=False)
    with (out/"stage36_SECONDARY_2018_derived_111_stem_original_source_evidence.tsv").open(
         "x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=OUT_FIELDS,delimiter="\t",extrasaction="raise")
        writer.writeheader();writer.writerows(inventory_rows)
    (out/"stage36_AU_ASM_2018_first_independent_survey_source_gate.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print("STAGE36 SOURCE 111 ORIGINAL 2018-DERIVED STEMS SHA VERIFIED, AGB STILL HOLD")
    print("STAGE36 SECONDARY 2018 COUNTS",counts)
    print("STAGE36 PRIMARY 2018 independent dataset",PRIMARY_CATALOG)
    print("STAGE36 independent 2018 RAW DATA FILES VERIFIED",False)
    for label,r in probes.items():print("STAGE36 CATALOG PROBE",label,r)
    print("STAGE36 NEXT STEP: obtain actual supersite.1041 2018 field files, no auto-source download")
    print("STAGE36 NO FATES SURFACE/INPUT/MODEL CHANGES; NO AD400")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

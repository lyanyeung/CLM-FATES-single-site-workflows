#!/usr/bin/env python3
"""OzFlux AU-ASM Stage34: exact 0.06ha raw-stem vs published stand AGB audit.

The publisher states all stems were surveyed in a 0.06 ha subplot
footprint (inside a separately labelled 1ha "core1ha" plot). Its
site-level CSV provides 2014/2018 standBiomass_tonnesPerHectare.
For each year, sum original AGB kg of ONE row per unique stem, then
compare to source stand t/ha with 0.06ha * 1000 kg/t conversion.

The Stage32 prior four-species sums show opposite sign ~2.429kg
differences. Search every ORIGINAL 2014 stem AGB candidate for a
SINGLE cross-year assignment that makes BOTH official stand records
round correctly to their published 4 decimal digits; do not assume
the value or identity. Separately test whether totals pooled over
both years match. This only tests source arithmetic, NOT any
underlying biological meaning or proves a join error.

CRITICAL:
  * 2018 stems are *derived* from 2014; NOT a 2018 independent survey.
  * Site-level stand biomass is another aggregation of potentially
    the SAME stem-derived source, NOT independent field validation.
  * 0.06ha is publisher-documented subplot sample area, NOT the
    100x100m labelled core1ha site polygon area.
  * D20 basal diameter is NOT FATES DBH.
  * Do not modify any source/model/surface/forcing, Slurm, or AD400.
Only a new read-only HOME JSON and a TSV of candidate source stems.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
S25=HOME/"ozflux_stage25_20261102T121025Z"
S32=HOME/"ozflux_stage32_20261102T185340Z"
S33=HOME/"ozflux_stage33_20261102T191655Z"
STEM=S25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
STEM_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
STAND=S33/"Alice_Mulga_site_level_biomass_data_v3pQRMW.csv"
STAND_SHA="f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8"
G32=S32/"stage32_AU_ASM_source_AGB_allometric_consistency_science_HOLD.json"
G33=S33/"stage33_TERN_original_site_level_biomass_intake_science_HOLD.json"
PUBLISHER_META="https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed"
SAMPLE_HA=Decimal("0.06")
KG_PER_TONNE=Decimal("1000")
SCALE_KG_PER_THA=SAMPLE_HA*KG_PER_TONNE
SITE_4DP=Decimal("0.0001")
KEYS=("siteId","plotId","plantId","stemId")
STEM_REQUIRED=(*KEYS,"scientificName","phenomenonTime",
    "aboveGroundBiomass_kilograms","stemDiameterPointOfMeasurement_metres",
    "plotLength_metres","plotWidth_metres")
STAND_REQUIRED=("siteId","plotId","plotLength_metres","plotWidth_metres",
    "startVisitDate","endVisitDate","phenomenonTime",
    "standBiomass_tonnesPerHectare")
CAND_FIELDS=("siteId","plotId","plantId","stemId","scientificName",
    "2014_source_AGB_kg","source_2014_survey_date",
    "2014_stand_after_transferring_one_2014_value_tpha",
    "2018_stand_after_transferring_same_2014_value_tpha",
    "rounds_to_both_published_stand_values",
    "audit_note")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

def table(p,sep,required):
    if not p.is_file() or p.is_symlink():raise ValueError("Not a regular pinned original CSV "+str(p))
    with p.open("r",newline="",encoding="utf-8-sig") as f:
        rdr=csv.DictReader(f,delimiter=sep)
        miss=set(required)-set(rdr.fieldnames or [])
        if miss:raise ValueError("Missing required original source columns "+repr(sorted(miss)))
        rows=list(rdr)
    if any(None in r for r in rows):raise ValueError("Malformed original CSV row")
    return rows

def dec(v,positive=False):
    if v is None:raise ValueError("Missing source numeric")
    try:d=Decimal(str(v).strip())
    except InvalidOperation:raise ValueError("Invalid original numeric "+repr(v))
    if not d.is_finite():raise ValueError("Nonfinite source numeric")
    if positive and d<=0:raise ValueError("Source expected positive numeric "+repr(v))
    return d

def yr(s):
    raw=str(s or "").strip()
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}",raw):
        raise ValueError("Unexpected survey date not D/M/YYYY: "+repr(s))
    try:d=datetime.strptime(raw,"%d/%m/%Y").date()
    except ValueError as e:raise ValueError("Impossible date: "+raw) from e
    if d.year not in (2014,2018):raise ValueError("Source unexpected year "+str(d.year))
    return d.year

def stemkey(r):
    k=tuple(str(r.get(x) or "").strip() for x in KEYS)
    if not all(k):raise ValueError("Incomplete original stem key")
    return k

def formatted4(v):
    return v.quantize(SITE_4DP,rounding=ROUND_HALF_UP)

def numeric_strings(obj):
    if isinstance(obj,Decimal):return str(obj)
    if isinstance(obj,dict):return {k:numeric_strings(v) for k,v in obj.items()}
    if isinstance(obj,(tuple,list)):return [numeric_strings(x) for x in obj]
    return obj

def verified():
    if (not STEM.is_file() or STEM.is_symlink() or sha(STEM)!=STEM_SHA or
        not STAND.is_file() or STAND.is_symlink() or sha(STAND)!=STAND_SHA):
        raise ValueError("Original stem or site-level biomass source SHA mismatches")
    for path in (G32,G33):
        if not path.is_file() or path.is_symlink():raise ValueError("Stage32/33 science gate missing")
    a=json.loads(G32.read_text(encoding="utf-8"))
    b=json.loads(G33.read_text(encoding="utf-8"))
    if (a.get("unique_stems")!=111 or
        a.get("source_sha256",{}).get("original_TERN_SHA256")!=STEM_SHA or
        a.get("AD400_authorised") is not False or
        a.get("2018_AGB_science_approved") is not False or
        b.get("source_download_status")!="CSV_BYTES_VERIFIED_SCHEMA_INSPECTED_NOT_SCIENCE_APPROVED" or
        b.get("original_source_verified_hash")!=STAND_SHA or
        b.get("row_count")!=2 or
        b.get("site_level_analysis_approved") is not False or
        b.get("AD400_authorised") is not False):
        raise ValueError("Actual Stage32/33 receipt/source provenance mismatch")
    st=table(STEM,",",STEM_REQUIRED)
    site=table(STAND,",",STAND_REQUIRED)
    if len(st)!=222 or len(site)!=2:
        raise ValueError("Expected 222 original stem and 2 stand records")
    return st,site,{"stem_original_SHA256":STEM_SHA,"stand_original_SHA256":STAND_SHA,
                    "Stage32_receipt_SHA256":sha(G32),"Stage33_receipt_SHA256":sha(G33)}

def reconcile(stems,stands,required_stems=111):
    per_stem=defaultdict(dict)
    original_date=defaultdict(dict)
    stem_sp=defaultdict(dict)
    stem_dims=Counter()
    for row in stems:
        k=stemkey(row);y=yr(row["phenomenonTime"])
        if y in per_stem[k]:raise ValueError("Duplicate same stem/year")
        d20=dec(row["stemDiameterPointOfMeasurement_metres"])
        if abs(d20-Decimal(".2"))>Decimal(".025"):
            raise ValueError("Stem source is not original 0.2m D20")
        stem_dims[(row["plotId"],row["plotLength_metres"],row["plotWidth_metres"])]+=1
        per_stem[k][y]=dec(row["aboveGroundBiomass_kilograms"])
        original_date[k][y]=row["phenomenonTime"]
        stem_sp[k][y]=row["scientificName"]
    if len(per_stem)!=required_stems or any(set(d)!={2014,2018} for d in per_stem.values()):
        raise ValueError("Actual original stem cohort does not contain paired years")
    if any(s[2014]!=s[2018] for s in stem_sp.values()):
        raise ValueError("Species changed across source-year identical stem IDs")
    site_by_year={}
    dimensions=[]
    for row in stands:
        y=yr(row["phenomenonTime"])
        if y in site_by_year:raise ValueError("Duplicate site level year")
        if yr(row["startVisitDate"])!=y or yr(row["endVisitDate"])!=y:
            raise ValueError("Site level dates conflict")
        val=dec(row["standBiomass_tonnesPerHectare"],positive=True)
        site_by_year[y]=val
        dimensions.append({"year":y,"plotId":row["plotId"],
                           "plotLength_raw":row["plotLength_metres"],
                           "plotWidth_raw":row["plotWidth_metres"]})
    if set(site_by_year)!={2014,2018}:
        raise ValueError("Expected exactly 2014 and 2018 site-level stand AGB")
    totals={y:sum((a[y] for a in per_stem.values()),Decimal(0)) for y in (2014,2018)}
    raw_reference={y:totals[y]/SCALE_KG_PER_THA for y in (2014,2018)}
    stand_kg={y:site_by_year[y]*SCALE_KG_PER_THA for y in (2014,2018)}
    residual_kg={y:totals[y]-stand_kg[y] for y in (2014,2018)}
    pooled_raw=totals[2014]+totals[2018]
    pooled_stand=stand_kg[2014]+stand_kg[2018]
    candidates=[]
    for k in sorted(per_stem):
        # Hypothesis test: one 2014 original stem biomass value
        # hypothetically transferred from 2014 to 2018 stand aggregation.
        v=per_stem[k][2014]
        low=(totals[2014]-v)/SCALE_KG_PER_THA
        high=(totals[2018]+v)/SCALE_KG_PER_THA
        if formatted4(low)==site_by_year[2014] and formatted4(high)==site_by_year[2018]:
            candidates.append({
                "siteId":k[0],"plotId":k[1],"plantId":k[2],"stemId":k[3],
                "scientificName":stem_sp[k][2014],
                "2014_source_AGB_kg":v,
                "source_2014_survey_date":original_date[k][2014],
                "2014_stand_after_transferring_one_2014_value_tpha":low,
                "2018_stand_after_transferring_same_2014_value_tpha":high,
                "rounds_to_both_published_stand_values":True,
                "audit_note":"ARITHMETIC ONE-VALUE TRANSFER HYPOTHESIS ONLY, NOT PROVEN DATA-PROCESSING ERROR OR APPROVED REPAIR",
            })
    gap_eq=(abs(residual_kg[2014]+residual_kg[2018])<=
            SITE_4DP*SCALE_KG_PER_THA)
    site_scale={
        "publisher_reported_actual_stem_sampling_area_ha":SAMPLE_HA,
        "actual_2014_and_2018_site_stand_tonnes_per_ha":site_by_year,
        "actual_2014_and_2018_source_stem_sum_kg":totals,
        "stem_sum_divided_by_0p06ha_tonnes_per_ha":raw_reference,
        "actual_stand_implied_subsample_biomass_kg":stand_kg,
        "stem_sum_minus_site_implied_subsample_kg":residual_kg,
        "pooled_across_year_source_stem_sum_kg":pooled_raw,
        "pooled_across_year_site_implied_biomass_kg":pooled_stand,
        "pooled_two_year_difference_kg":pooled_raw-pooled_stand,
        "pooled_difference_compatible_with_two_4dp_site_roundings":gap_eq,
        "original_stem_plot_dimensions_per_row":dict(
            ((str(key[0])+" | "+str(key[1])+" x "+str(key[2])),v)
            for key,v in stem_dims.items()),
        "stand_metadata_full_core1ha_plot_dimensions":dimensions,
        "sampling_area_ha_not_equal_labelled_core1ha_area":True,
        "valid_unique_stem_pairs":len(per_stem),
        "single_2014_stem_value_transfer_candidates":len(candidates),
        "such_transfer_proves_source_join_error":False,
        "2018_source_derived_not_independent_field_observation":True,
        "2014_AGB_allometrically_estimated_not_field_weighed":True,
        "sampling_area_scale_source":"TERN official lineage: 0.06ha actual stem survey area; stand biomass scaled to tonnes/ha",
    }
    return site_scale,candidates

def test():
    assert formatted4(Decimal("37.41679278"))==Decimal("37.4168")
    assert formatted4(Decimal("44.62769596"))==Decimal("44.6277")
    assert yr("21/1/2014")==2014
    assert yr("1/6/2018")==2018
    stems=[]
    # Minimal 2-stem fixture: biomass 2014 4+2kg, 2018 5+3kg.
    # One 2014 2kg value transferred gives site 4kg and 10kg.
    for plant,agb14,agb18 in ((1,4,5),(2,2,3)):
        for year,biomass in ((2014,agb14),(2018,agb18)):
            stems.append({
                "siteId":"Alice Mulga","plotId":"core", "plantId":str(plant),"stemId":"1",
                "scientificName":"Acacia aneura",
                "phenomenonTime":("21/1/2014" if year==2014 else "1/6/2018"),
                "aboveGroundBiomass_kilograms":str(biomass),
                "stemDiameterPointOfMeasurement_metres":"0.2",
                "plotLength_metres":"10 m","plotWidth_metres":"10 m"})
    sites=[]
    for year,stand in ((2014,Decimal(4)/60),(2018,Decimal(10)/60)):
        sites.append({"siteId":"Alice Mulga","plotId":"core1ha",
           "startVisitDate":("21/1/2014" if year==2014 else "1/6/2018"),
           "endVisitDate":("22/1/2014" if year==2014 else "2/6/2018"),
           "phenomenonTime":("21/1/2014" if year==2014 else "1/6/2018"),
           "standBiomass_tonnesPerHectare":str(formatted4(stand)),
           "plotLength_metres":"100 m","plotWidth_metres":"100 m"})
    data,candidates=reconcile(stems,sites,required_stems=2)
    assert data["single_2014_stem_value_transfer_candidates"]==1
    assert candidates[0]["plantId"]=="2"
    assert data["valid_unique_stem_pairs"]==2
    assert data["pooled_difference_compatible_with_two_4dp_site_roundings"]
    print("STAGE34 SELF-TEST PASS: TERN 0.06ha vs core1ha, source kg/t/ha 4dp, single-stem year attribution arithmetic fixture, no original writes")

def main():
    if sys.argv[1:]==["--self-test"]:test();return
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(p==out or p in out.parents for p in (
              ROOT.resolve(),S25.resolve(),S32.resolve(),S33.resolve()))):
        raise ValueError("Output must be new direct HOME child")
    stem,stand,source_receipts=verified()
    result,candidates=reconcile(stem,stand)
    report={
      "stage":"AU-ASM Stage34 original 0.06ha stem vs official core1ha stand AGB arithmetic forensic",
      "source_original_SHA256":source_receipts,
      "publisher_metadata_url":PUBLISHER_META,
      "stand_arithmetic":numeric_strings(result),
      "single_2014_source_stem_candidate_transfer_to_2018_stand":numeric_strings(candidates),
      "possible_source_year_group_assignment_issue_NOT_PROVEN":True,
      "published_stand_AGB_is_not_independent_field_measurement_from_stems":True,
      "2018_AGB_science_approved":False,
      "2014_field_stem_height_science_gate_unchanged":True,
      "source_D20_not_FATES_DBH":True,
      "site_PFT_or_soil_or_forcing_science_approved":False,
      "original_input_data_or_model_modified":False,
      "CIME_or_Slurm_job_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(parents=False,mode=0o700,exist_ok=False)
    with (out/"stage34_site_2014_stem_value_transfer_arithmetic_candidates.tsv").open(
        "x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=CAND_FIELDS,delimiter="\t",extrasaction="raise")
        writer.writeheader()
        writer.writerows(numeric_strings(candidates))
    (out/"stage34_TERN_0p06ha_stem_to_site_biomass_science_HOLD.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),
        encoding="utf-8")
    print("STAGE34 SOURCE HASH VERIFIED",STEM_SHA,STAND_SHA)
    print("STAGE34 EXACT ORIGINAL 222 STEM ROWS (111 YEAR-PAIRED) AND TWO SITE YEARS VERIFIED")
    print("STAGE34 PUBLISHER 0.06ha SAMPLE SCALE KG_PER_tHa",SCALE_KG_PER_THA)
    for year in (2014,2018):
        print("YEAR",year,
              "SITE_STAND_tHa",result["actual_2014_and_2018_site_stand_tonnes_per_ha"][year],
              "STEM_AGB_KG",result["actual_2014_and_2018_source_stem_sum_kg"][year],
              "STEM_SCALED_tHa",result["stem_sum_divided_by_0p06ha_tonnes_per_ha"][year],
              "STEM_MINUS_SITE_KG",result["stem_sum_minus_site_implied_subsample_kg"][year])
    print("STAGE34 POOLED_TWO_YEAR_KG_DIFFERENCE",result["pooled_two_year_difference_kg"])
    print("STAGE34 POOLED ROUNDING COMPATIBLE",result["pooled_difference_compatible_with_two_4dp_site_roundings"])
    print("STAGE34 RAW STEM PLOT IDENTIFIERS_AND_DIMENSIONS",result["original_stem_plot_dimensions_per_row"])
    print("STAGE34 STAND 1ha CORE META DIMENSIONS",result["stand_metadata_full_core1ha_plot_dimensions"])
    print("STAGE34 SINGLE ORIGINAL 2014 STEM AGB TRANSFER ARITHMETIC CANDIDATES",len(candidates))
    for c in candidates:
        print("YEAR_ATTRIBUTION_ARITHMETIC_CANDIDATE",
              "SPECIES",c["scientificName"],
              "PLOT",c["plotId"],"PLANT",c["plantId"],"STEM",c["stemId"],
              "ORIGINAL_2014_AGB_KG",c["2014_source_AGB_kg"],
              "REPRODUCED_2014_tHa",c["2014_stand_after_transferring_one_2014_value_tpha"],
              "REPRODUCED_2018_tHa",c["2018_stand_after_transferring_same_2014_value_tpha"])
    print("STAGE34 SCIENCE HOLD: exact arithmetic hypotheses NOT proof of erroneous join; no source alteration")
    print("STAGE34 NO FATES/SURFACE/FORCING/CIME/SLURM/AD400")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

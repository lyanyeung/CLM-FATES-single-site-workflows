#!/usr/bin/env python3
"""AU-ASM Stage35: focused original-source Plant 99 stem 1b attribution audit.

Stage34 proved a unique one-value arithmetic test recreates BOTH
published 4-decimal stand biomass figures. This script compares
several deliberately different 2014/2018 inclusion/exclusion
counterfactuals, using Decimal and the ORIGINAL SHA-pinned 222 stem
rows and official 2-row TERN stand source. It records BOTH raw
original records of Plant 99 stem 1b including dates, scientificName,
stemStatus, comment, AGB, D20, height, siteId and plotId and confirms
the 21-row dictionary relevant definitions.

A numerical counterfactual is NOT a claim about TERN's real
aggregation code, source QA, sample weights, or published error.
No original changes, data repair, fitted biomass, model/surface/
forcing/CIME/Slurm/AD400. Only fresh HOME JSON/TSV evidence.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import sys

HOME=Path.home()
S25=HOME/"ozflux_stage25_20261102T121025Z"
S33=HOME/"ozflux_stage33_20261102T191655Z"
S34=HOME/"ozflux_stage34_20261102T193337Z"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
S_STEM=S25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
S_DICT=S25/"Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv"
S_STAND=S33/"Alice_Mulga_site_level_biomass_data_v3pQRMW.csv"
S_GATE=S34/"stage34_TERN_0p06ha_stem_to_site_biomass_science_HOLD.json"
S_CAND=S34/"stage34_site_2014_stem_value_transfer_arithmetic_candidates.tsv"
HASHES={
    "stem":"7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55",
    "dictionary":"82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe",
    "stand":"f4fcfe46fd5132ed040187ae443441d37822e18c8deb48c01be667af51b9fea8",
}
AREA_HA=Decimal("0.06")
KG_PER_THA=AREA_HA*Decimal("1000")
ROUND_THA=Decimal("0.0001")
KEYS=("siteId","plotId","plantId","stemId")
SELECT=("Alice Mulga","Alice Mulga, core1ha","99","1b")
SCENARIO_COLS=("scenario","2014_kg","2018_kg","2014_tHa","2018_tHa",
               "2014_4dp_matches_official","2018_4dp_matches_official",
               "both_years_match_official_4dp","hypothesis_note")


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1048576),b""):h.update(x)
    return h.hexdigest()

def read(p,sep,required,nrows):
    if not p.is_file() or p.is_symlink():
        raise ValueError("Pinned original input missing or symlink: "+str(p))
    with p.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f,delimiter=sep)
        missing=set(required)-set(reader.fieldnames or [])
        if missing:raise ValueError("Source original CSV missing fields "+repr(sorted(missing)))
        rows=list(reader)
    if len(rows)!=nrows or any(None in r for r in rows):
        raise ValueError("Original source count or schema drift "+str(p))
    return rows

def D(value):
    try:v=Decimal(str(value).strip())
    except (ValueError,InvalidOperation):raise ValueError("Original numeric parse failed "+repr(value))
    if not v.is_finite():raise ValueError("Source numeric not finite")
    return v

def key(r):
    return tuple(str(r.get(k) or "").strip() for k in KEYS)

def year(text):
    x=str(text or "").strip()
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}",x):
        raise ValueError("Only source D/M/YYYY supported: "+repr(x))
    try:date=datetime.strptime(x,"%d/%m/%Y").date()
    except ValueError as e:raise ValueError("Impossible date: "+x) from e
    if date.year not in (2014,2018):raise ValueError("Unexpected site year")
    return date.year

def q4(v):
    return v.quantize(ROUND_THA,rounding=ROUND_HALF_UP)

def dec_json(value):
    if isinstance(value,Decimal):return str(value)
    if isinstance(value,dict):return {str(k):dec_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [dec_json(v) for v in value]
    return value

def validate_sources():
    for label,p in (("stem",S_STEM),("dictionary",S_DICT),("stand",S_STAND)):
        if not p.is_file() or p.is_symlink() or sha(p)!=HASHES[label]:
            raise ValueError("Original source SHA256 mismatch "+label)
    receipt=S_GATE
    if not receipt.is_file() or receipt.is_symlink() or not S_CAND.is_file() or S_CAND.is_symlink():
        raise ValueError("Stage34 operator source-reconciliation receipt/candidate missing")
    gate=json.loads(receipt.read_text(encoding="utf-8"))
    a=gate.get("stand_arithmetic",{})
    cand=gate.get("single_2014_source_stem_candidate_transfer_to_2018_stand",[])
    if (gate.get("source_original_SHA256",{}).get("stem_original_SHA256")!=HASHES["stem"]
        or gate.get("source_original_SHA256",{}).get("stand_original_SHA256")!=HASHES["stand"]
        or a.get("valid_unique_stem_pairs")!=111
        or a.get("single_2014_stem_value_transfer_candidates")!=1
        or a.get("pooled_difference_compatible_with_two_4dp_site_roundings") is not True
        or len(cand)!=1 or str(cand[0].get("plantId"))!="99"
        or str(cand[0].get("stemId"))!="1b"
        or cand[0].get("2014_source_AGB_kg")!="2.429615547"
        or gate.get("AD400_authorised") is not False):
        raise ValueError("Stage34 actual operator receipt differs")
    stems=read(S_STEM,",",(*KEYS,"scientificName","phenomenonTime",
        "startVisitDate","endVisitDate","aboveGroundBiomass_kilograms",
        "stemDiameter_centimeters","stemDiameterPointOfMeasurement_metres",
        "stemHeight_metres","stemStatus","comment"),222)
    stands=read(S_STAND,",",("siteId","plotId","phenomenonTime",
                 "standBiomass_tonnesPerHectare"),2)
    dictionary=read(S_DICT,",",("Dictionary","URL","Description"),21)
    candidates=read(S_CAND,"\t",("siteId","plotId","plantId","stemId",
                   "2014_source_AGB_kg"),1)
    if key(candidates[0])!=SELECT or D(candidates[0]["2014_source_AGB_kg"])!=D("2.429615547"):
        raise ValueError("Stage34 candidate tabular receipt inconsistent")
    return stems,stands,dictionary,{
      "stem_SHA256":HASHES["stem"],
      "stand_SHA256":HASHES["stand"],
      "dictionary_SHA256":HASHES["dictionary"],
      "Stage34_gate_SHA256":sha(S_GATE),
      "Stage34_candidate_TSV_SHA256":sha(S_CAND),
    }

def counterfactual(stems,stands,expected_keys=None):
    pool=defaultdict(dict)
    for r in stems:
        k=key(r);y=year(r["phenomenonTime"])
        if not all(k) or y in pool[k]:raise ValueError("Duplicate/incomplete original stem/year")
        if D(r["stemDiameterPointOfMeasurement_metres"])!=Decimal(".2"):
            raise ValueError("Original field diameter not D20")
        if year(r["startVisitDate"])!=y or year(r["endVisitDate"])!=y:
            raise ValueError("Raw TERN visit/year inconsistency")
        pool[k][y]=r
    if expected_keys is not None and len(pool)!=expected_keys:
        raise ValueError("Source number of unique stems changed")
    if any(set(by)!={2014,2018} for by in pool.values()):
        raise ValueError("Not exactly one 2014 and 2018 row for every original stem")
    if SELECT not in pool:raise ValueError("Required actual Plant 99 1b key not in source")
    site={}
    for r in stands:
        y=year(r["phenomenonTime"])
        if y in site:raise ValueError("Duplicate original stand source year")
        site[y]=D(r["standBiomass_tonnesPerHectare"])
    if set(site)!={2014,2018}:raise ValueError("Missing original site stand year")
    sums={y:sum((D(by[y]["aboveGroundBiomass_kilograms"]) for by in pool.values()),Decimal("0"))
          for y in (2014,2018)}
    a=D(pool[SELECT][2014]["aboveGroundBiomass_kilograms"])
    b=D(pool[SELECT][2018]["aboveGroundBiomass_kilograms"])
    if a!=Decimal("2.429615547") and expected_keys==111:
        raise ValueError("Selected original 2014 AGB differs from real operator source")
    scenario_inputs=[
      ("ALL_STEM_ROWS_DIRECT",Decimal("0"),Decimal("0"),"No source selection change"),
      ("2014_OMIT_P99_ONLY",-a,Decimal("0"),"2014 excludes Plant99 2014 source; 2018 unmodified"),
      ("2018_EXTRA_2014_P99_ONLY",Decimal("0"),a,"2014 unmodified; 2018 includes extra copy of 2014 Plant99 AGB"),
      ("OMIT_2014_AND_EXTRA_2014_AGB_IN_2018",-a,a,
       "Both-year one-value transfer: 2014 excludes 2014 P99 and 2018 includes an extra copy of 2014 P99"),
      ("OMIT_2014_AND_REPLACE_2018_P99_WITH_2014_VALUE",-a,a-b,
       "2014 excludes 2014 P99 and 2018 replaces its already included 2018 P99 AGB by 2014 P99"),
      ("OMIT_2014_AND_EXTRA_2018_AGB_IN_2018",-a,b,
       "2014 excludes 2014 P99 and 2018 includes an extra copy of the 2018 P99 AGB"),
      ("OMIT_BOTH_YEARS_P99",-a,-b,
       "Both original P99 source records excluded"),
    ]
    out=[]
    for name,delta14,delta18,note in scenario_inputs:
        x=sums[2014]+delta14;y=sums[2018]+delta18
        qx=x/KG_PER_THA;qy=y/KG_PER_THA
        m14=q4(qx)==site[2014];m18=q4(qy)==site[2018]
        out.append({
          "scenario":name,
          "2014_kg":x,"2018_kg":y,
          "2014_tHa":qx,"2018_tHa":qy,
          "2014_4dp_matches_official":m14,
          "2018_4dp_matches_official":m18,
          "both_years_match_official_4dp":m14 and m18,
          "hypothesis_note":note,
        })
    chosen={y:pool[SELECT][y] for y in (2014,2018)}
    return out,{
       "official_stand_tHa":site,
       "original_raw_stem_sums_kg":sums,
       "Plant99_2014_AGB_kg":a,
       "Plant99_2018_derived_AGB_kg":b,
       "Plant99_two_original_rows":chosen,
       "original_unique_stems":len(pool),
       "same_Plant99_stem_has_exact_2014_and_2018_raw_rows":True,
       "other_possible_hidden_area_selection_filtering_NOT_VALIDATED":True,
       "site_0p06ha_tHa_rounding_precision":str(ROUND_THA),
       "single_stem_one_value_transfer_is_arithmetic_NOT_CODE_PROVEN":True,
    }

def selftest():
    assert q4(D("37.41679278265"))==D("37.4168")
    assert q4(D("44.627695962966"))==D("44.6277")
    assert year("22/1/2014")==2014 and year("1/6/2018")==2018
    src=[]
    # Keep the exact selected Plant99 key in synthetic fixture.
    for y,biomass in ((2014,"2.429615547"),(2018,"3.713499951")):
        src.append(dict(zip(KEYS,SELECT))|{
          "scientificName":"Eremophila latrobei ssp glabra",
          "phenomenonTime":"22/1/2014" if y==2014 else "1/6/2018",
          "startVisitDate":"21/1/2014" if y==2014 else "1/6/2018",
          "endVisitDate":"22/1/2014" if y==2014 else "2/6/2018",
          "stemDiameterPointOfMeasurement_metres":"0.2",
          "aboveGroundBiomass_kilograms":biomass,
        })
    sites=[{"phenomenonTime":"21/1/2014","standBiomass_tonnesPerHectare":"0.0000"},
           {"phenomenonTime":"1/6/2018","standBiomass_tonnesPerHectare":"0.0000"}]
    cases,meta=counterfactual(src,sites,expected_keys=1)
    assert len(cases)==7
    assert meta["original_unique_stems"]==1
    assert meta["Plant99_2014_AGB_kg"]==D("2.429615547")
    assert len({x["scenario"] for x in cases})==7
    assert sum(x["both_years_match_official_4dp"] for x in cases)==0
    assert cases[3]["2014_kg"]==Decimal("0")
    print("STAGE35 SELF-TEST PASS: exact original P99 key and 2 source years, seven distinct Decimal attribution scenarios, 0.06ha stand 4dp, no source write")

def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(p==out or p in out.parents for p in (
              ROOT.resolve(),S25.resolve(),S33.resolve(),S34.resolve()))):
        raise ValueError("Out must be fresh direct HOME child, never original/model folder")
    stems,stands,dictionary,hashes=validate_sources()
    cases,details=counterfactual(stems,stands,expected_keys=111)
    ok=[x["scenario"] for x in cases if x["both_years_match_official_4dp"]]
    if ok!=["OMIT_2014_AND_EXTRA_2014_AGB_IN_2018"]:
        raise ValueError("Exact source 2014/2018 scenarios no longer isolate single expected arithmetic match")
    relevant=[]
    for e in dictionary:
        txt=" ".join(str(x or "") for x in e.values()).lower()
        if any(word in txt for word in ("biomass","stemstatus","comment","phenomenon","stemid","date","species","diameter")):
            relevant.append(e)
    report={
      "stage":"OzFlux Stage35 exact Plant99 stem1b original AGB year inclusion and seven counterfactual scenarios",
      "sha256_verified":hashes,
      "source_publisher":"https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed",
      "site_area_ha":"0.06",
      "original_Plant99_stem_evidence":dec_json(details),
      "original_stem_dictionary_relevant_entries":relevant,
      "seven_source_arithmetic_counterfactuals":dec_json(cases),
      "scenarios_reproducing_both_official_4dp_site_stands":ok,
      "unique_matching_scenario_among_these_seven_NOT_necessarily_unique_real_source_pipeline":True,
      "actual_publisher_grouping_source_code_unavailable":True,
      "data_entry_or_source_join_error_proven":False,
      "2018_AGB_science_approved":False,
      "source_D20_NOT_DBH":True,
      "site_PFT_or_soil_or_forcing_science_approved":False,
      "site_source_or_FATES_surface_or_params_modified":False,
      "CIME_or_Slurm_job_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(mode=0o700,exist_ok=False,parents=False)
    with (out/"stage35_Plant99_seven_AGB_year_grouping_counterfactuals.tsv").open(
       "x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=SCENARIO_COLS,delimiter="\t",extrasaction="raise")
        writer.writeheader();writer.writerows(dec_json(cases))
    (out/"stage35_Plant99_original_source_stand_biomass_science_HOLD.json").write_text(
       json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    print("STAGE35 SOURCE STEM + STAND + DICTIONARY HASHES VERIFIED")
    print("STAGE35 SOURCE P99 ORIGINAL ROWS")
    for y in (2014,2018):
        item=details["Plant99_two_original_rows"][y]
        keys=("scientificName","startVisitDate","endVisitDate","phenomenonTime",
              "stemDiameter_centimeters","stemHeight_metres",
              "aboveGroundBiomass_kilograms","stemStatus","comment")
        print("YEAR",y,{k:item.get(k) for k in keys})
    for x in cases:
        print("COUNTERFACTUAL",x["scenario"],"2014",x["2014_tHa"],
              "2018",x["2018_tHa"],"BOTH_MATCH",x["both_years_match_official_4dp"])
    print("STAGE35 MATCHING_SCENARIOS",ok)
    print("STAGE35 SOURCE ARITHMETIC IS NOT PROOF OF PUBLISHER JOIN ERROR")
    print("STAGE35 NO ORIGINAL OR MODEL WRITES, NO AD400")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

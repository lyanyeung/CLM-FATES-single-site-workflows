#!/usr/bin/env python3
"""OzFlux AU-ASM Stage29: exact D/M/YYYY dates and unique-stem 2014/2018 audit.

Strictly read the original SHA256-verified TERN 222-row D20 stem CSV,
21-row dictionary, and Stage28 operator science receipt. Parse dates as
DAY/MONTH/YEAR (e.g., 21/1/2014, 1/6/2018). Inspect exact
(siteId,plotId,plantId,stemId) longitudinal pairs, record any changes
in height, basal D20 diameter and derived above-ground biomass.

2014 is a publisher-described FIELD survey; 2018 rows are publisher-
described derived increment-based estimates, NOT new independent field
surveys. Never compare D20 to FATES DBH and never treat 111 stems as
independent plants. Data grouped at independent stem-ID level; report
results separately for 2014 field and 2018 derived measurements.
No original files or model surface/forcing/CIME/Slurm modified.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE25=HOME/"ozflux_stage25_20261102T121025Z"
STAGE28=HOME/"ozflux_stage28_20261102T124717Z"
RAW=STAGE25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
DICTIONARY=STAGE25/"Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv"
RAW_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
DICT_SHA="82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe"
CAP=4.735410175384586
DATES=("startVisitDate","endVisitDate","phenomenonTime")
KEYS=("siteId","plotId","plantId","stemId")
PFT_SPECIES=("Acacia aneura","Acacia aptaneura")
HEIGHT_FIELD="stemHeight_metres"
DIAM_FIELD="stemDiameter_centimeters"
BIOM_FIELD="aboveGroundBiomass_kilograms"
POINT_FIELD="stemDiameterPointOfMeasurement_metres"
COLUMNS=("siteId","plotId","plantId","stemId","scientificName",
         "pair_class","date_2014_start","date_2014_end","date_2014_phenomenon",
         "date_2018_start","date_2018_end","date_2018_phenomenon",
         "D20_2014_cm","D20_2018_derived_cm","D20_change_cm",
         "height_2014_m","height_2018_derived_m","height_change_m",
         "biomass_2014_kg","biomass_2018_derived_kg","biomass_change_kg",
         "height_2014_exceeds_FATES7_plateau",
         "height_2018_derived_exceeds_FATES7_plateau",
         "height_class_disagreement",
         "source_measurement_point_m","interpretation")


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def pinned_regular(p,expected,label):
    if not p.is_file() or p.is_symlink() or sha(p)!=expected:
        raise ValueError(label+" missing, symlink, or SHA mismatch: "+str(p))


def load_csv(p,required,nexpected):
    with p.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        head=reader.fieldnames or []
        if not set(required).issubset(head):
            raise ValueError("Source missing columns "+repr(sorted(set(required)-set(head))))
        rows=list(reader)
    if len(rows)!=nexpected or any(None in row for row in rows):
        raise ValueError("Original rows do not match expectation "+str(p))
    return rows


def date_dmy(raw):
    s=str(raw or "").strip()
    # Python strptime itself tolerates variable width day and month.
    # Require exactly D/M/YYYY with 1-2 digit fields, then verify
    # actual month/day through datetime parsing.
    import re
    if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}",s):
        return None
    try: dt=datetime.strptime(s,"%d/%m/%Y").date()
    except ValueError: return None
    return dt if 2000<=dt.year<=2030 else None


def valid_num(raw,lower=None,upper=None):
    if raw is None or str(raw).strip().lower() in (
        "","na","n/a","nan","none","null","-999","-999.0","-999.9","-9999","-9999.0","--"):
        return None
    try:v=float(raw)
    except (TypeError,ValueError):return None
    if not math.isfinite(v):return None
    if lower is not None and v<=lower:return None
    if upper is not None and v>=upper:return None
    return v


def rid(row):
    k=tuple(str(row.get(x) or "").strip() for x in KEYS)
    return k if all(k) else None


def date_record(row):
    ds={k:date_dmy(row.get(k)) for k in DATES}
    if any(x is None for x in ds.values()):
        return {"ok":False,"dates":ds,"reason":"UNPARSEABLE_DMY_DATE"}
    if ds["startVisitDate"]>ds["endVisitDate"]:
        return {"ok":False,"dates":ds,"reason":"END_BEFORE_START"}
    if not (ds["startVisitDate"]<=ds["phenomenonTime"]<=ds["endVisitDate"]):
        return {"ok":False,"dates":ds,"reason":"PHENOMENON_OUTSIDE_VISIT"}
    years={x.year for x in ds.values()}
    if len(years)!=1 or next(iter(years)) not in (2014,2018):
        return {"ok":False,"dates":ds,"reason":"INCONSISTENT_OR_UNEXPECTED_YEAR"}
    return {"ok":True,"dates":ds,"year":next(iter(years)),"reason":"DMY_SOURCE_DATES_VERIFIED"}


def verify_inputs():
    pinned_regular(RAW,RAW_SHA,"TERN 222-row original stem")
    pinned_regular(DICTIONARY,DICT_SHA,"TERN 21-row dictionary")
    receipt=STAGE28/"stage28_TERN_time_and_duplicate_stem_science_HOLD.json"
    if receipt.is_symlink() or not receipt.is_file():
        raise ValueError("Exact Stage28 operator report unavailable")
    d=json.loads(receipt.read_text(encoding="utf-8"))
    stats=d.get("stem_identity_and_temporal_audit",{})
    source=d.get("source_SHA256",{})
    if (source.get("stem_csv_SHA256")!=RAW_SHA
        or source.get("stem_dictionary_SHA256")!=DICT_SHA
        or stats.get("raw_rows")!=222
        or stats.get("unique_stem_keys")!=111
        or stats.get("each_stem_exactly_2_rows") is not True
        or d.get("valid_DBH_1p3m_source_rows")!=0
        or d.get("AD400_authorised") is not False
        or abs(float(d.get("verified_default_FATES7_height_cap_m",0))-CAP)>1e-10):
        raise ValueError("Stage28 actual operator science receipt mismatch")
    required=(*KEYS,"scientificName",*DATES,HEIGHT_FIELD,DIAM_FIELD,BIOM_FIELD,POINT_FIELD)
    stems=load_csv(RAW,required,222)
    dictionary=load_csv(DICTIONARY,("Dictionary","URL","Description"),21)
    if any(abs(float(r[POINT_FIELD])-.2)>.025 for r in stems):
        raise ValueError("Original stem diameter is not uniformly D20 at 0.2m")
    return stems,dictionary,{"raw_stem_sha":RAW_SHA,"dictionary_sha":DICT_SHA,
                             "stage28_receipt_sha":sha(receipt)}


def analyze(rows, expected_stems=None):
    stems=defaultdict(list)
    counts=Counter()
    for r in rows:
        key=rid(r)
        if key is None:
            raise ValueError("Original TERN stem row missing complete identifiers")
        d=date_record(r)
        counts[d.get("reason","NO_REASON")]+=1
        stems[key].append((r,d))
    # Fixtures intentionally have fewer stems than the real TERN archive.
    # Enforce the source-specific count only when explicitly requested.
    if expected_stems is not None and len(stems)!=expected_stems:
        raise ValueError(
            "Expected "+str(expected_stems)+" distinct stem identifiers, got "+
            str(len(stems)))
    results=[]
    by_species=defaultdict(list)
    temporal_classes=Counter()
    for k,items in sorted(stems.items()):
        if len(items)!=2:
            raise ValueError("Original stem no longer occurs twice")
        classified={2014:[],2018:[]}
        for raw,dated in items:
            if not dated["ok"]:
                raise ValueError("Invalid D/M/YYYY date for stem "+repr(k)+
                                 ": "+dated["reason"]+" original "+repr(
                                 {x:raw.get(x) for x in DATES}))
            classified[dated["year"]].append((raw,dated))
        if len(classified[2014])!=1 or len(classified[2018])!=1:
            raise ValueError("Each stem needs EXACT 1 row 2014 and 1 row 2018 "+
                             repr(k))
        a=classified[2014][0][0]
        b=classified[2018][0][0]
        species_a=str(a.get("scientificName") or "").strip()
        species_b=str(b.get("scientificName") or "").strip()
        if not species_a or species_a!=species_b:
            raise ValueError("Species drift across same stem "+repr(k))
        a_h=valid_num(a[HEIGHT_FIELD],0,100)
        b_h=valid_num(b[HEIGHT_FIELD],0,100)
        a_d=valid_num(a[DIAM_FIELD],0,500)
        b_d=valid_num(b[DIAM_FIELD],0,500)
        a_b=valid_num(a[BIOM_FIELD],0,100000)
        b_b=valid_num(b[BIOM_FIELD],0,100000)
        above_a=a_h>CAP if a_h is not None else None
        above_b=b_h>CAP if b_h is not None else None
        discordant=bool(above_a!=above_b) if above_a is not None and above_b is not None else None
        if a_h is None or b_h is None:cl="MISSING_HEIGHT_ONE_OR_BOTH"
        elif discordant:cl="DISCORDANT_CAP"
        else:cl="CONSISTENT_CAP_CLASS"
        temporal_classes[cl]+=1
        rec={
           "siteId":k[0],"plotId":k[1],"plantId":k[2],"stemId":k[3],
           "scientificName":species_a,"pair_class":cl,
           "date_2014_start":a["startVisitDate"],
           "date_2014_end":a["endVisitDate"],
           "date_2014_phenomenon":a["phenomenonTime"],
           "date_2018_start":b["startVisitDate"],
           "date_2018_end":b["endVisitDate"],
           "date_2018_phenomenon":b["phenomenonTime"],
           "D20_2014_cm":a_d,"D20_2018_derived_cm":b_d,
           "D20_change_cm":b_d-a_d if a_d is not None and b_d is not None else None,
           "height_2014_m":a_h,"height_2018_derived_m":b_h,
           "height_change_m":b_h-a_h if a_h is not None and b_h is not None else None,
           "biomass_2014_kg":a_b,"biomass_2018_derived_kg":b_b,
           "biomass_change_kg":b_b-a_b if a_b is not None and b_b is not None else None,
           "height_2014_exceeds_FATES7_plateau":above_a,
           "height_2018_derived_exceeds_FATES7_plateau":above_b,
           "height_class_disagreement":discordant,
           "source_measurement_point_m":0.2,
           "interpretation":"2014 field date / 2018 derived increment source row; DO NOT equate D20 with DBH",
        }
        results.append(rec)
        by_species[species_a].append(rec)
    summary=[]
    def stats(vals):
        arr=[x for x in vals if x is not None]
        return {"n":len(arr),"median":statistics.median(arr) if arr else None,
                "min":min(arr) if arr else None,"max":max(arr) if arr else None,
                "nonzero_n":sum(abs(x)>1e-10 for x in arr)}
    for species,items in sorted(by_species.items()):
        unique_plants={tuple(r[k] for k in ("siteId","plotId","plantId")) for r in items}
        groups={
          "2014_field_heights_m":stats([r["height_2014_m"] for r in items]),
          "2018_derived_heights_m":stats([r["height_2018_derived_m"] for r in items]),
          "height_deltas_m":stats([r["height_change_m"] for r in items]),
          "2014_field_D20_cm":stats([r["D20_2014_cm"] for r in items]),
          "2018_derived_D20_cm":stats([r["D20_2018_derived_cm"] for r in items]),
          "D20_deltas_cm":stats([r["D20_change_cm"] for r in items]),
          "biomass_deltas_kg":stats([r["biomass_change_kg"] for r in items]),
        }
        nvalid=sum(r["height_2014_m"] is not None for r in items)
        nexceed=sum(r["height_2014_exceeds_FATES7_plateau"] is True for r in items)
        summary.append({
            "scientificName":species,
            "unique_stem_ids":len(items),
            "unique_plant_ids":len(unique_plants),
            "2014_field_height_valid_unique_stem_ids":nvalid,
            "2014_field_stems_above_FATES7_height_cap":nexceed,
            "2014_field_proportion_of_valid_stem_ids_above_cap":nexceed/nvalid if nvalid else None,
            "2018_rows_are_derived_NOT_new_independent_survey":True,
            "cross_year_cap_discordant_stems":sum(r["height_class_disagreement"] is True for r in items),
            **groups,
        })
    # Counts derive from the *actual* input, not a magic 111/222 that
    # makes single-stem fixtures incorrectly fail or falsely pass.
    counts_by_year={"2014":len(stems),"2018":len(stems)}
    return results,summary,{"original_rows":len(rows),"unique_stem_identifiers":len(stems),
                           "calendar_source_year_counts":counts_by_year,
                           "rows_per_stem":{"2":len(stems)},
                           "longitudinal_pair_classes":dict(temporal_classes),
                           "all_111_stems_have_one_2014_and_one_2018_source_row":len(stems)==111,
                           "all_dates_parse_original_DMY_and_phenomenon_within_visit":counts==Counter({"DMY_SOURCE_DATES_VERIFIED":len(rows)}),
                           "raw_date_check_counts":dict(counts),
                           "DBH_pairs_original":0,
                           "note":"2014 field measurement vs 2018 derived/modelled increment, not two independent field measurements"}


def save_tsv(p,rows):
    with p.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS,delimiter="\t",extrasaction="raise")
        w.writeheader()
        w.writerows(rows)


def selftest():
    assert str(date_dmy("21/1/2014"))=="2014-01-21"
    assert str(date_dmy("1/6/2018"))=="2018-06-01"
    assert str(date_dmy("22/1/2014"))=="2014-01-22"
    assert date_dmy("2014-01-21") is None
    assert date_dmy("31/2/2014") is None
    assert date_dmy("1/13/2018") is None
    assert date_record({"startVisitDate":"21/1/2014","endVisitDate":"22/1/2014",
                        "phenomenonTime":"21/1/2014"})["ok"]
    assert not date_record({"startVisitDate":"21/1/2014","endVisitDate":"22/1/2014",
                        "phenomenonTime":"1/6/2018"})["ok"]
    def fixture(y,height,d):
        start,end=("21/1/2014","22/1/2014") if y==2014 else ("1/6/2018","2/6/2018")
        return dict(siteId="s",plotId="p",plantId="a",stemId="1",
                    scientificName="Acacia aneura",startVisitDate=start,endVisitDate=end,
                    phenomenonTime=start,stemHeight_metres=str(height),
                    stemDiameter_centimeters=str(d),
                    aboveGroundBiomass_kilograms="2.0",
                    stemDiameterPointOfMeasurement_metres="0.2")
    single=[fixture(2018,5,2.2),fixture(2014,5,2)]
    pairs,sp,qa=analyze(single,expected_stems=1)
    assert len(pairs)==1 and sp[0]["2014_field_stems_above_FATES7_height_cap"]==1
    assert qa["all_dates_parse_original_DMY_and_phenomenon_within_visit"]
    assert qa["original_rows"]==2 and qa["unique_stem_identifiers"]==1
    assert qa["calendar_source_year_counts"]=={"2014":1,"2018":1}
    assert qa["rows_per_stem"]=={"2":1}
    assert qa["all_111_stems_have_one_2014_and_one_2018_source_row"] is False
    assert math.isclose(pairs[0]["D20_change_cm"],0.2)
    try:
        analyze(single,expected_stems=111)
    except ValueError as exc:
        assert "Expected 111 distinct stem identifiers" in str(exc)
    else:
        raise AssertionError("Production 111-stem guard must reject 1-stem fixture")
    try:
        analyze([fixture(2014,5,2),fixture(2014,5,2.2)],expected_stems=1)
    except ValueError as exc:
        assert "EXACT 1 row 2014 and 1 row 2018" in str(exc)
    else:
        raise AssertionError("Duplicate-year stem must be rejected")
    print("STAGE29 SELF-TEST PASS: strict D/M/YYYY dates, fixture 1 stem, production 111-stem guard, one row/year, no D20=DBH; NO MODEL WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(x==out or x in out.parents for x in
               (ROOT.resolve(),STAGE25.resolve(),STAGE28.resolve()))):
        raise ValueError("Must write to fresh direct HOME report dir")
    stem,dictionary,provenance=verify_inputs()
    pairs,species,qc=analyze(stem,expected_stems=111)
    if (qc["original_rows"]!=222 or
        qc["calendar_source_year_counts"]!={"2014":111,"2018":111} or
        qc["rows_per_stem"]!={"2":111} or
        qc["all_111_stems_have_one_2014_and_one_2018_source_row"] is not True or
        qc["all_dates_parse_original_DMY_and_phenomenon_within_visit"] is not True):
        raise ValueError("Actual TERN 222 row / 111 stem exact two-year science gate not met")
    report={
      "stage":"OzFlux Stage29 exact original D/M/YYYY and 2014/2018 per-stem time reconciliation",
      "source_SHA256":provenance,
      "2014_is_publisher_field_survey":True,
      "2018_source_is_increment_DERIVED_not_new_independent_stem_survey":True,
      "actual_date_field_formats":"D/M/YYYY in startVisitDate, endVisitDate, phenomenonTime",
      "exact_original_date_and_stem_pair_QC":qc,
      "species_unique_stem_2014_field_vs_2018_derived":species,
      "observed_FATES7_default_height_cap_m":CAP,
      "PFT7_height_cap_incompatible_with_tall_2014_acacia_stems":any(
          x["scientificName"] in PFT_SPECIES and
          x["2014_field_stems_above_FATES7_height_cap"]>0 for x in species),
      "strict_original_D20_not_DBH":True,
      "separate_2014_true_DBH_survey_NOT_INGESTED":True,
      "site_PFT_fraction_science_approved":False,
      "Acacia_FATES4_vs_7_science_approved":False,
      "Kandosol_soil_profile_science_approved":False,
      "final_forcing_science_approved":False,
      "new_surface_created":False,
      "CIME_or_Slurm_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(parents=False,exist_ok=False,mode=0o700)
    save_tsv(out/"stage29_111_TERN_unique_stem_2014_measured_2018_derived_comparison.tsv",pairs)
    (out/"stage29_TERN_true_DMY_dates_and_Acacia_height_science_HOLD.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    print("STAGE29 ORIGINAL TERN STEM/DICTIONARY AND STAGE28 SHA VERIFIED")
    print("STAGE29 DMY DATE PARSING",qc["raw_date_check_counts"])
    print("STAGE29 UNIQUE STEM PAIRS",qc["unique_stem_identifiers"],
          "SOURCE YEAR ROWS",qc["calendar_source_year_counts"])
    print("STAGE29 CROSS YEAR PAIR CLASSES",qc["longitudinal_pair_classes"])
    for s in species:
        print("SPECIES",s["scientificName"],
              "UNIQUE_STEMS",s["unique_stem_ids"],
              "PLANTS",s["unique_plant_ids"],
              "2014_FIELD_HEIGHTS",s["2014_field_height_valid_unique_stem_ids"],
              "2014_TALL_ABOVE_FATES7",s["2014_field_stems_above_FATES7_height_cap"],
              "2014_FIELD_HEIGHT",s["2014_field_heights_m"],
              "2018_DERIVED_HEIGHT",s["2018_derived_heights_m"],
              "HEIGHT_DELTA",s["height_deltas_m"],
              "D20_DELTA",s["D20_deltas_cm"])
    print("STAGE29 DO NOT MISTAKE 2018 DERIVED AS SECOND INDEPENDENT TOWER SURVEY")
    print("STAGE29 NO DIRECT DBH; NO PFT/soil/forcing SCIENCE APPROVAL; NO CIME/SLURM")
    print("REPORT_DIR",out)


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""AU-ASM Stage30: independent read-only 2014 field / 2018 derived D20 and AGB review.

The original TERN publisher describes 2014 stem field measurement and
2018 diameter/biomass derived from dendrometer-informed growth assumptions,
NOT second field stem measurements. Stage29 successfully paired 111
identifiers across 2014/2018 and identified unexpected changes. Reopen
the immutable original SHA-pinned 222-row TERN CSV and independently
reconcile each original pair to Stage29's 111-row TSV; report every
unusual D20, height or biomass delta and their source-row comments.

Interpretation safeguards:
* ALL field stem diameters are measured at 0.2m (D20), not 1.3m DBH.
* Negative/large derived biomass deltas are QC CANDIDATES, not proven
  impossible or direct observed carbon loss.
* A publisher's phrase "uniform basal area increment" does NOT imply
  each stem must grow +0.7 cm in diameter.
* Unique stem identifiers are not independent trees, nor annual growth
  measurements; model parameters/surfaces/forcing/Slurm never changed.
Outputs two new TSV files and one JSON in a fresh direct HOME folder.
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
S25=HOME/"ozflux_stage25_20261102T121025Z"
S29=HOME/"ozflux_stage29_20261102T131205Z"
CSV_SOURCE=S25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
SOURCE_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
PAIR_SOURCE=S29/"stage29_111_TERN_unique_stem_2014_measured_2018_derived_comparison.tsv"
REPORT_SOURCE=S29/"stage29_TERN_true_DMY_dates_and_Acacia_height_science_HOLD.json"
KEYS=("siteId","plotId","plantId","stemId")
MODEL_CAP=4.735410175384586
COLUMNS=("siteId","plotId","plantId","stemId","scientificName",
         "2014_phenomenonTime","2018_phenomenonTime",
         "D20_2014_cm","D20_2018_derived_cm","delta_D20_cm",
         "BA_2014_cm2","BA_2018_derived_cm2","delta_BA_cm2",
         "height_2014_m","height_2018_derived_m","delta_height_m",
         "biomass_2014_kg","biomass_2018_derived_kg","delta_AGB_kg",
         "2014_height_above_FATES7_cap",
         "source_stemStatus_2014","source_stemStatus_2018",
         "source_comment_2014","source_comment_2018",
         "review_flags","requires_human_science_review")
FLAG_NAMES=("DERIVED_D20_DECREASE","DERIVED_D20_GAIN_GT_1CM",
            "DERIVED_D20_NOT_NEAR_0P7CM_SCREEN",
            "DERIVED_BASAL_AREA_DECREASE","DERIVED_HEIGHT_DIFFERS",
            "DERIVED_AGB_DECREASE","DERIVED_AGB_CHANGE_ABS_GT_50KG",
            "D20_AGB_DIRECTION_DISCORDANCE_WITH_STABLE_HEIGHT",
            "INVALID_OR_MISSING_NUMERIC_PAIR")

def sha(p):
    digest=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            digest.update(b)
    return digest.hexdigest()

def load_table(path,delim,required):
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("Missing original source or symlink "+str(path))
    with path.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f,delimiter=delim)
        missing=set(required)-set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing CSV columns "+repr(sorted(missing)))
        rows=list(reader)
    if any(None in x for x in rows):
        raise ValueError("CSV malformed extra fields "+str(path))
    return rows

def num(raw):
    if raw is None or str(raw).strip().lower() in (
        "","na","n/a","nan","none","null","-999","-999.0",
        "-999.9","-9999","-9999.0","--"):
        return None
    try:v=float(raw)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None

def same(a,b,tol=1e-7):
    return (a is None and b is None) or (
        a is not None and b is not None and math.isclose(a,b,rel_tol=tol,abs_tol=tol))

def original_year(text):
    try:
        return datetime.strptime(str(text).strip(),"%d/%m/%Y").year
    except (ValueError,TypeError):return None

def ident(r):
    v=tuple(str(r.get(k) or "").strip() for k in KEYS)
    if not all(v):raise ValueError("Original source missing stem identity")
    return v

def science_inputs():
    if sha(CSV_SOURCE)!=SOURCE_SHA or CSV_SOURCE.is_symlink():
        raise ValueError("Original 222-row TERN SHA changed")
    if REPORT_SOURCE.is_symlink() or not REPORT_SOURCE.is_file():
        raise ValueError("Stage29 operator receipt missing")
    gate=json.loads(REPORT_SOURCE.read_text(encoding="utf-8"))
    s=gate.get("exact_original_date_and_stem_pair_QC",{})
    if (gate.get("source_SHA256",{}).get("raw_stem_sha")!=SOURCE_SHA or
        s.get("unique_stem_identifiers")!=111 or
        s.get("original_rows")!=222 or
        s.get("calendar_source_year_counts")!={"2014":111,"2018":111} or
        s.get("longitudinal_pair_classes")!={"CONSISTENT_CAP_CLASS":111} or
        s.get("all_111_stems_have_one_2014_and_one_2018_source_row") is not True or
        gate.get("strict_original_D20_not_DBH") is not True or
        gate.get("AD400_authorised") is not False):
        raise ValueError("Real Stage29 science/paired-year receipt mismatch")
    raw=load_table(CSV_SOURCE,",",(*KEYS,"scientificName",
               "startVisitDate","endVisitDate","phenomenonTime",
               "stemDiameterPointOfMeasurement_metres",
               "stemDiameter_centimeters","stemHeight_metres",
               "aboveGroundBiomass_kilograms","stemStatus","comment"))
    stage29=load_table(PAIR_SOURCE,"\t",(*KEYS,
                         "D20_2014_cm","D20_2018_derived_cm",
                         "height_2014_m","height_2018_derived_m",
                         "biomass_2014_kg","biomass_2018_derived_kg"))
    if len(raw)!=222 or len(stage29)!=111:
        raise ValueError("Original source or Stage29 paired rows differ")
    return raw,stage29,{"TERN_source_SHA256":SOURCE_SHA,
                        "Stage29_receipt_SHA256":sha(REPORT_SOURCE),
                        "Stage29_pair_TSV_SHA256":sha(PAIR_SOURCE)}

def calculate(raw,stage29):
    original=defaultdict(dict)
    for r in raw:
        y=original_year(r["phenomenonTime"])
        if y not in (2014,2018):raise ValueError("Unexpected original date")
        k=ident(r)
        if y in original[k]:raise ValueError("Two original rows for same stem/year")
        if original_year(r["startVisitDate"])!=y or original_year(r["endVisitDate"])!=y:
            raise ValueError("Original visit dates year mismatch")
        point=num(r["stemDiameterPointOfMeasurement_metres"])
        if point is None or abs(point-0.2)>.025:
            raise ValueError("Original diameter at breast height or unverified point")
        original[k][y]=r
    if len(original)!=111 or any(set(years)!={2014,2018} for years in original.values()):
        raise ValueError("Source does not contain exact 111 2014/2018 paired stems")
    pair_by_key={}
    for row in stage29:
        k=ident(row)
        if k in pair_by_key:raise ValueError("Duplicate Stage29 row")
        pair_by_key[k]=row
    if set(pair_by_key)!=set(original):
        raise ValueError("Stage29 and original source stem keys not identical")
    result=[]
    for k,years in sorted(original.items()):
        a,b=years[2014],years[2018]
        p=pair_by_key[k]
        if a["scientificName"]!=b["scientificName"]:
            raise ValueError("Species mismatch for stem "+repr(k))
        vals={}
        for short,raw_name,stage29_14,stage29_18 in (
            ("D20","stemDiameter_centimeters","D20_2014_cm","D20_2018_derived_cm"),
            ("height","stemHeight_metres","height_2014_m","height_2018_derived_m"),
            ("biomass","aboveGroundBiomass_kilograms","biomass_2014_kg","biomass_2018_derived_kg"),
        ):
            v14=num(a[raw_name]);v18=num(b[raw_name])
            if not same(v14,num(p[stage29_14])) or not same(v18,num(p[stage29_18])):
                raise ValueError("Stage29 cross-checked original "+short+" differs "+repr(k))
            vals[short]=(v14,v18)
        d0,d1=vals["D20"]
        h0,h1=vals["height"]
        m0,m1=vals["biomass"]
        ba0=math.pi*d0*d0/4 if d0 is not None and d0>0 else None
        ba1=math.pi*d1*d1/4 if d1 is not None and d1>0 else None
        dd=d1-d0 if None not in (d0,d1) else None
        dh=h1-h0 if None not in (h0,h1) else None
        dm=m1-m0 if None not in (m0,m1) else None
        dba=ba1-ba0 if None not in (ba0,ba1) else None
        flags=[]
        if None in (d0,d1,h0,h1,m0,m1) or d0<=0 or d1<=0 or h0<=0 or h1<=0 or m0<0 or m1<0:
            flags.append("INVALID_OR_MISSING_NUMERIC_PAIR")
        if dd is not None:
            if dd < -1e-6:flags.append("DERIVED_D20_DECREASE")
            if dd > 1.0+1e-6:flags.append("DERIVED_D20_GAIN_GT_1CM")
            if abs(dd-.7)>.05+1e-6:flags.append("DERIVED_D20_NOT_NEAR_0P7CM_SCREEN")
        if dba is not None and dba < -1e-6:
            flags.append("DERIVED_BASAL_AREA_DECREASE")
        if dh is not None and abs(dh)>1e-6:
            flags.append("DERIVED_HEIGHT_DIFFERS")
        if dm is not None:
            if dm < -1e-6:flags.append("DERIVED_AGB_DECREASE")
            if abs(dm) > 50:flags.append("DERIVED_AGB_CHANGE_ABS_GT_50KG")
        if (dm is not None and dd is not None and dh is not None
            and abs(dh)<=1e-6 and dm*dd < -1e-5):
            flags.append("D20_AGB_DIRECTION_DISCORDANCE_WITH_STABLE_HEIGHT")
        rec={
            "siteId":k[0],"plotId":k[1],"plantId":k[2],"stemId":k[3],
            "scientificName":a["scientificName"],
            "2014_phenomenonTime":a["phenomenonTime"],
            "2018_phenomenonTime":b["phenomenonTime"],
            "D20_2014_cm":d0,"D20_2018_derived_cm":d1,"delta_D20_cm":dd,
            "BA_2014_cm2":ba0,"BA_2018_derived_cm2":ba1,"delta_BA_cm2":dba,
            "height_2014_m":h0,"height_2018_derived_m":h1,"delta_height_m":dh,
            "biomass_2014_kg":m0,"biomass_2018_derived_kg":m1,"delta_AGB_kg":dm,
            "2014_height_above_FATES7_cap":h0>MODEL_CAP if h0 is not None else None,
            "source_stemStatus_2014":a["stemStatus"],
            "source_stemStatus_2018":b["stemStatus"],
            "source_comment_2014":a["comment"],
            "source_comment_2018":b["comment"],
            "review_flags":";".join(sorted(flags)),
            "requires_human_science_review":bool(flags),
        }
        result.append(rec)
    return result

def stats(values):
    vals=[x for x in values if x is not None]
    return {"count":len(vals),"min":min(vals) if vals else None,
            "median":statistics.median(vals) if vals else None,
            "max":max(vals) if vals else None,
            "negative":sum(x < -1e-6 for x in vals),
            "zero":sum(abs(x)<=1e-6 for x in vals),
            "positive":sum(x > 1e-6 for x in vals)}

def summary(rows):
    groups=defaultdict(list)
    for r in rows:groups[r["scientificName"]].append(r)
    result={}
    for specie,rr in sorted(groups.items()):
        count=Counter(f for r in rr for f in r["review_flags"].split(";") if f)
        plantkeys={tuple(r[k] for k in ("siteId","plotId","plantId")) for r in rr}
        result[specie]={
            "unique_stem_ids":len(rr),"unique_plant_keys":len(plantkeys),
            "D20_delta_cm":stats([r["delta_D20_cm"] for r in rr]),
            "basal_area_delta_cm2":stats([r["delta_BA_cm2"] for r in rr]),
            "height_delta_m":stats([r["delta_height_m"] for r in rr]),
            "AGB_delta_kg":stats([r["delta_AGB_kg"] for r in rr]),
            "flags":dict(count),
            "stem_ids_with_any_flag":sum(bool(r["review_flags"]) for r in rr),
            "tall_2014_stem_ids":sum(r["2014_height_above_FATES7_cap"] is True for r in rr),
        }
    return result

def test():
    assert math.isclose(math.pi*4/4,math.pi)
    assert original_year("21/1/2014")==2014
    assert original_year("1/6/2018")==2018
    assert original_year("2014-01-21") is None
    assert same(None,None) and same(3,3+1e-8)
    assert not same(3,4)
    def fixture(year,d,h,m,sp="Acacia aneura"):
        return {"siteId":"au","plotId":"plot","plantId":"plant","stemId":"1",
                "scientificName":sp,"startVisitDate":f"1/6/{year}",
                "endVisitDate":f"2/6/{year}","phenomenonTime":f"1/6/{year}",
                "stemDiameterPointOfMeasurement_metres":"0.2",
                "stemDiameter_centimeters":str(d),
                "stemHeight_metres":str(h),
                "aboveGroundBiomass_kilograms":str(m),
                "stemStatus":"live","comment":"test"}
    a=fixture(2014,4,4,10);b=fixture(2018,3.5,4,8)
    paired={k:a[k] for k in KEYS}
    paired.update({"D20_2014_cm":"4","D20_2018_derived_cm":"3.5",
                   "height_2014_m":"4","height_2018_derived_m":"4",
                   "biomass_2014_kg":"10","biomass_2018_derived_kg":"8"})
    result=calculate([b,a],[paired])
    r=result[0]
    assert "DERIVED_D20_DECREASE" in r["review_flags"]
    assert "DERIVED_BASAL_AREA_DECREASE" in r["review_flags"]
    assert "DERIVED_AGB_DECREASE" in r["review_flags"]
    assert math.isclose(r["delta_D20_cm"],-.5)
    try:
        pairbad=dict(paired);pairbad["biomass_2018_derived_kg"]="999"
        calculate([b,a],[pairbad])
    except ValueError as exc:
        assert "cross-checked" in str(exc)
    else:raise AssertionError("Bad Stage29 paired source must fail closed")
    print("STAGE30 SELF-TEST PASS: 2014/2018 D20 source pairing, BASAL AREA vs diameter, negative deltas, Stage29 mismatch fail-closed; READ ONLY")

def write_table(path,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS,delimiter="\t",extrasaction="raise")
        w.writeheader();w.writerows(rows)

def main():
    if sys.argv[1:]==["--self-test"]:test();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(x==out or x in out.parents for x in (ROOT.resolve(),S25.resolve(),S29.resolve()))):
        raise ValueError("Report output must be a FRESH direct HOME child")
    raw,paired,provenance=science_inputs()
    rows=calculate(raw,paired)
    if len(rows)!=111 or sum(x["2014_height_above_FATES7_cap"] is True for x in rows if x["scientificName"] in ("Acacia aneura","Acacia aptaneura"))!=27:
        raise ValueError("111 unique stems / 27 tall Acacia receipt mismatch")
    qc=summary(rows)
    flagged=[r for r in rows if r["review_flags"]]
    report={
      "stage":"OzFlux AU-ASM Stage30 original stem-level 2018 derived D20/AGB forensic",
      "source_SHA256":provenance,
      "all_111_stem_pairs_independently_reconciled_to_original":True,
      "TERN_2014_field_stem_survey_2018_increment_DERIVED":True,
      "reference":"https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed",
      "2018_is_not_independent_stem_field_remeasurement":True,
      "2018_source_D20_changes_not_directly_observed_growth":True,
      "all_diameters_are_D20_at_0p20m_NOT_DBH":True,
      "stem_height_and_AGB_model_source_rules_unchanged":True,
      "Flag_thresholds_EXPLORATORY_NOT_AUTOMATIC_REJECTION":{
          "D20_decrease_cm":"less than -1e-6",
          "D20_gain_gt_1cm":"greater than 1 cm",
          "D20_not_near_0p7_screen":"absolute departure > 0.05 cm, screen only",
          "height_differs_m":"absolute departure > 1e-6",
          "biomass_drop_kg":"less than -1e-6 kg",
          "large_AGB_delta_kg":"absolute departure > 50 kg",
          "basal_area_difference":"pi/4*(D20_2018**2-D20_2014**2), cm2",
      },
      "species_summaries":qc,
      "n_unique_stems":len(rows),
      "n_flagged_stems":len(flagged),
      "all_flag_counts":dict(Counter(f for row in rows for f in row["review_flags"].split(";") if f)),
      "site_PFT4_or_7_science_approved":False,
      "2018_derived_increment_science_approved":False,
      "Acacia_wood_growth_model_calibrated":False,
      "new_site_surface_created":False,
      "Kandosol_ten_layer_soil_approved":False,
      "final_forcing_science_approved":False,
      "CIME_or_Slurm_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    write_table(out/"stage30_all_111_2014_field_2018_derived_original_stems.tsv",rows)
    write_table(out/"stage30_flagged_D20_BA_height_AGB_source_stems.tsv",flagged)
    (out/"stage30_AU_ASM_derived_2018_stem_increment_science_HOLD.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    print("STAGE30 ORIGINAL 222-ROW TERN SHA VERIFIED",SOURCE_SHA)
    print("STAGE30 111 UNIQUE STEMS INDEPENDENTLY RECONCILED TO STAGE29")
    print("STAGE30 FLAGGED UNIQUE STEMS",len(flagged),"FLAG COUNTS",report["all_flag_counts"])
    for specie,g in qc.items():
        print("SPECIES",specie,"STEMS",g["unique_stem_ids"],"D20_DELTA",g["D20_delta_cm"],"BA_DELTA",g["basal_area_delta_cm2"],"AGB_DELTA",g["AGB_delta_kg"],"FLAGS",g["flags"])
    for r in flagged:
        important=any(f in r["review_flags"] for f in (
            "DERIVED_D20_DECREASE","DERIVED_D20_GAIN_GT_1CM",
            "DERIVED_HEIGHT_DIFFERS","DERIVED_AGB_CHANGE_ABS_GT_50KG",
            "D20_AGB_DIRECTION_DISCORDANCE_WITH_STABLE_HEIGHT"))
        if important:
            print("SOURCE_REVIEW",r["scientificName"],"PLOT",r["plotId"],
                  "PLANT",r["plantId"],"STEM",r["stemId"],
                  "D20",r["D20_2014_cm"],r["D20_2018_derived_cm"],
                  "BA_DELTA",r["delta_BA_cm2"],
                  "HEIGHT",r["height_2014_m"],r["height_2018_derived_m"],
                  "AGB",r["biomass_2014_kg"],r["biomass_2018_derived_kg"],
                  "FLAGS",r["review_flags"])
    print("STAGE30 SCIENCE HOLD: 2018 derived not observation, no PFT/soil/forcing approval, no Slurm")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

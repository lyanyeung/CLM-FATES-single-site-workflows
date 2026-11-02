#!/usr/bin/env python3
"""OzFlux AU-ASM Stage32 — 2014 allometric baseline vs 2018 derived AGB.

All source files and Stage31 receipts are read-only. Fit a within-
species exploratory OLS log(AGB_2014_kg) ~ log(D20_2014_cm) from
publisher's 2014 original stem AGB estimates, then apply the exact
same *empirical diagnostic curve* to the 2018 derived D20 values.
These 2014 AGB values are ALREADY calculated from allometry, NOT
directly weighed biomass; in-sample fitting is NOT independent
validation and this is NOT a replacement for the Navar et al. 2013
published equation or an approved 2018 biomass correction.

Guardrails:
 - D20 at 0.20m is never model DBH at 1.30m.
 - 2018 growth/AGB are derived, not field revisits.
 - 2018 AGB ratios and cross-stem sums are exploratory, not
   observed growth, carbon flux, ecosystem C stock or t/ha.
 - Never change raw CSV, FATES parameters, surface, forcing, case or
   Slurm, and never authorize AD400.
Outputs one JSON + one TSV in fresh direct child of HOME.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
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
STAGE30=HOME/"ozflux_stage30_20261102T131841Z"
STAGE31=HOME/"ozflux_stage31_20261102T183333Z"
RAW=STAGE25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
RAW_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
G31=STAGE31/"stage31_AU_ASM_derived_AGB_join_formula_science_HOLD.json"
S31=STAGE31/"stage31_all_111_stem_AGB_join_association_screens.tsv"
S30=STAGE30/"stage30_all_111_2014_field_2018_derived_original_stems.tsv"
KEYS=("siteId","plotId","plantId","stemId")
PFT_SOURCE_STEMS={"Acacia aneura":43,"Acacia aptaneura":60,
                  "Eremophila latrobei ssp glabra":1,"Psydrax latifolia":7}
STEM_FIELDS=("scientificName","D20_2014_cm","D20_2018_derived_cm",
             "height_2014_m","height_2018_derived_m",
             "AGB_2014_kg","AGB_2018_derived_kg")
OUTPUT_FIELDS=("siteId","plotId","plantId","stemId","scientificName",
               "D20_2014_cm","D20_2018_derived_cm",
               "H_2014_m","H_2018_derived_m",
               "AGB_2014_allometric_kg","AGB_2018_derived_kg",
               "AGB_2014_baseline_fitted_kg",
               "AGB_2018_predicted_from_2014_D20_curve_kg",
               "2018_actual_divided_by_same_2014_curve_prediction",
               "2018_ln_residual_against_2014_D20_curve",
               "screen_flags","scientific_caveat")


def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path,sep,columns):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Source missing or symlink "+str(path))
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter=sep)
        missing=set(columns)-set(reader.fieldnames or [])
        if missing:raise ValueError("Missing actual source fields: "+repr(sorted(missing)))
        rows=list(reader)
    if any(None in r for r in rows):
        raise ValueError("Malformed source rows with extra fields "+str(path))
    return rows


def num(x):
    if x is None or str(x).strip().lower() in (
        "","na","n/a","nan","null","none","-999","-999.0",
        "-999.9","-9999","--"):
        return None
    try: v=float(x)
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) else None


def key(row):
    k=tuple(str(row.get(f) or "").strip() for f in KEYS)
    if not all(k):raise ValueError("Missing complete original stem ID")
    return k


def fit_ln_power(x,y,min_n=4):
    pairs=[(a,b) for a,b in zip(x,y)
           if a is not None and b is not None and a>0 and b>0]
    if len(pairs)<min_n:
        return {"n":len(pairs),"fitted":False,"reason":"INSUFFICIENT_STEMS"}
    logs=[(math.log(a),math.log(b)) for a,b in pairs]
    lx=[a for a,_ in logs];ly=[b for _,b in logs]
    meanx=statistics.mean(lx);meany=statistics.mean(ly)
    sxx=sum((a-meanx)**2 for a in lx)
    if sxx<1e-12:
        return {"n":len(pairs),"fitted":False,"reason":"DEGENERATE_LOG_DIAMETER"}
    beta=sum((a-meanx)*(b-meany) for a,b in logs)/sxx
    alpha=meany-beta*meanx
    residual=[b-(alpha+beta*a) for a,b in logs]
    sse=sum(e**2 for e in residual)
    sst=sum((b-meany)**2 for b in ly)
    r2=1-sse/sst if sst>1e-12 else None
    return {"n":len(pairs),"fitted":True,
            "log_intercept":alpha,"log_D20_slope":beta,
            "in_sample_R2_log_AGB":r2,
            "in_sample_median_absolute_log_residual":statistics.median(abs(e) for e in residual),
            "reason":"2014_ASSUMPTION_DIAGNOSTIC_NOT_INDEPENDENT_VALIDATION"}


def predict(d,fit):
    if d is None or d<=0 or not fit.get("fitted"):return None
    exponent=fit["log_intercept"]+fit["log_D20_slope"]*math.log(d)
    if exponent>700 or exponent< -700:
        return None
    return math.exp(exponent)


def summary_stats(vals):
    a=[v for v in vals if v is not None and math.isfinite(v)]
    return {"n":len(a),"median":statistics.median(a) if a else None,
            "min":min(a) if a else None,"max":max(a) if a else None}


def verify_inputs():
    if not RAW.is_file() or RAW.is_symlink() or sha(RAW)!=RAW_SHA:
        raise ValueError("Original TERN raw stem CSV fingerprint mismatch")
    if G31.is_symlink() or not G31.is_file() or S31.is_symlink() or not S31.is_file():
        raise ValueError("Actual Stage31 operator report / TSV not present")
    gate=json.loads(G31.read_text(encoding="utf-8"))
    if (gate.get("n_unique_stems")!=111
        or gate.get("operator_stage30_flagged_stem_count")!=48
        or gate.get("source_hashes",{}).get("original_TERN_SHA256")!=RAW_SHA
        or gate.get("AGB_2018_science_approved") is not False
        or gate.get("AD400_authorised") is not False):
        raise ValueError("Stage31 operator science receipt mismatch")
    raw=load(RAW,",",(*KEYS,"scientificName","phenomenonTime",
                       "stemDiameter_centimeters","aboveGroundBiomass_kilograms"))
    stem=load(S31,"\t",(*KEYS,*STEM_FIELDS))
    original30=load(S30,"\t",(*KEYS,"scientificName",
                       "D20_2014_cm","D20_2018_derived_cm",
                       "biomass_2014_kg","biomass_2018_derived_kg"))
    if len(raw)!=222 or len(stem)!=111 or len(original30)!=111:
        raise ValueError("Original 222 / Stage31 111 / Stage30 111 counts drift")
    dictionary={}
    for r in original30:
        k=key(r)
        if k in dictionary:raise ValueError("Duplicate Stage30 stem ID")
        dictionary[k]=r
    matched=set()
    for r in stem:
        k=key(r)
        if k in matched or k not in dictionary:
            raise ValueError("Stage31 stem key duplicate/missing Stage30")
        matched.add(k)
        old=dictionary[k]
        if r["scientificName"]!=old["scientificName"]:
            raise ValueError("Stage30 vs Stage31 species mismatch")
        for left,right in (("D20_2014_cm","D20_2014_cm"),
                            ("D20_2018_derived_cm","D20_2018_derived_cm"),
                            ("AGB_2014_kg","biomass_2014_kg"),
                            ("AGB_2018_derived_kg","biomass_2018_derived_kg")):
            x=num(r[left]);y=num(old[right])
            if x is None or y is None or not math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-9):
                raise ValueError("Stage31 and Stage30 values differ "+repr(k)+" "+left)
    if matched!=set(dictionary):raise ValueError("Incomplete stage31/stage30 original set")
    # Stage31 already validates raw-to-pairs; verify direct raw source too,
    # including both 2014 and 2018 original corresponding numbers.
    raw_by_key=defaultdict(dict)
    for r in raw:
        date=str(r["phenomenonTime"]).strip()
        year=2014 if date.endswith("/2014") else 2018 if date.endswith("/2018") else None
        if year is None:raise ValueError("Unexpected TERN survey date "+date)
        k=key(r)
        if year in raw_by_key[k]:raise ValueError("Duplicate source stem/year")
        raw_by_key[k][year]=r
    if set(raw_by_key)!=matched or any(set(yrs)!={2014,2018} for yrs in raw_by_key.values()):
        raise ValueError("Expected 111 original 2014/2018 stem pairs")
    for r in stem:
        k=key(r)
        for yr,d,b in (
            (2014,"D20_2014_cm","AGB_2014_kg"),
            (2018,"D20_2018_derived_cm","AGB_2018_derived_kg")):
            source=raw_by_key[k][yr]
            for target,sourcecol in ((d,"stemDiameter_centimeters"),
                                     (b,"aboveGroundBiomass_kilograms")):
                a=num(r[target]);z=num(source[sourcecol])
                if a is None or z is None or not math.isclose(a,z,rel_tol=1e-9,abs_tol=1e-9):
                    raise ValueError("Stage31 vs raw TERN stem numeric mismatch "+repr(k))
    actual=Counter(r["scientificName"] for r in stem)
    if dict(actual)!=PFT_SOURCE_STEMS:
        raise ValueError("Expected species exact 43+60+1+7 counts, got "+repr(dict(actual)))
    return stem,{"original_TERN_SHA256":RAW_SHA,
                 "Stage30_TSV_SHA256":sha(S30),
                 "Stage31_TSV_SHA256":sha(S31),
                 "Stage31_operator_receipt_SHA256":sha(G31)}


def calculate(rows):
    groups=defaultdict(list)
    for r in rows:groups[r["scientificName"]].append(r)
    output=[];reports={}
    for specie,items in sorted(groups.items()):
        d14=[num(r["D20_2014_cm"]) for r in items]
        d18=[num(r["D20_2018_derived_cm"]) for r in items]
        m14=[num(r["AGB_2014_kg"]) for r in items]
        m18=[num(r["AGB_2018_derived_kg"]) for r in items]
        regression=fit_ln_power(d14,m14)
        if specie=="Eremophila latrobei ssp glabra" and regression["fitted"]:
            raise ValueError("Do not estimate allometry on one Eremophila stem")
        ratios=[];logres=[]
        for r,d0,d1,m0,m1 in zip(items,d14,d18,m14,m18):
            expected14=predict(d0,regression)
            expected18=predict(d1,regression)
            ratio=m1/expected18 if m1 is not None and expected18 is not None and expected18>0 else None
            resid=math.log(ratio) if ratio is not None and ratio>0 else None
            flags=[]
            if not regression.get("fitted"):
                flags.append("INSUFFICIENT_2014_SPECIES_STEMS")
            if ratio is not None:
                if ratio<0.2:flags.append("2018_DERIVED_AGB_LT_0P2X_2014_DIAGNOSTIC_CURVE")
                if ratio>5:flags.append("2018_DERIVED_AGB_GT_5X_2014_DIAGNOSTIC_CURVE")
            if any(x is None or x<=0 for x in (d0,d1,m0,m1)):
                flags.append("MISSING_OR_NONPOSITIVE_STEM_INPUT")
            output.append({
              "siteId":r["siteId"],"plotId":r["plotId"],
              "plantId":r["plantId"],"stemId":r["stemId"],
              "scientificName":specie,
              "D20_2014_cm":d0,"D20_2018_derived_cm":d1,
              "H_2014_m":num(r["height_2014_m"]),
              "H_2018_derived_m":num(r["height_2018_derived_m"]),
              "AGB_2014_allometric_kg":m0,
              "AGB_2018_derived_kg":m1,
              "AGB_2014_baseline_fitted_kg":expected14,
              "AGB_2018_predicted_from_2014_D20_curve_kg":expected18,
              "2018_actual_divided_by_same_2014_curve_prediction":ratio,
              "2018_ln_residual_against_2014_D20_curve":resid,
              "screen_flags":";".join(flags),
              "scientific_caveat":"RECONSTRUCTION SCREEN ONLY; NOT APPROVED 2018 REPLACEMENT, NOT FATES DBH, NOT MEASURED AGB",
            })
            if ratio is not None:ratios.append(ratio)
            if resid is not None:logres.append(resid)
        reports[specie]={
          "n_stems":len(items),
          "regression_2014_log_AGB_vs_log_D20":regression,
          "2014_AGB_total_kg_for_original_stems_not_site_t_per_ha":sum(x for x in m14 if x is not None),
          "2018_derived_AGB_total_kg_for_same_stems_NOT_independent_field_measurement":sum(x for x in m18 if x is not None),
          "2018_to_2014_sum_ratio":sum(x for x in m18 if x is not None)/sum(x for x in m14 if x is not None)
              if all(x is not None and x>0 for x in m14) else None,
          "AGB2018_over_2014_fit_prediction_ratio":summary_stats(ratios),
          "2018_median_absolute_log_residual":statistics.median(abs(x) for x in logres) if logres else None,
          "stem_flags_vs_2014_diameter_baseline":dict(Counter(
              f for r in output if r["scientificName"]==specie for f in r["screen_flags"].split(";") if f)),
          "science_status":"DIAGNOSTIC_REFERENCE_ONLY; 2014 AGB ALREADY MODEL-ESTIMATED; 2018 NOT FIELD-MEASURED",
        }
    return output,reports


def selftest():
    x=[1,2,3,4,5]
    y=[3*v**2 for v in x]
    fit=fit_ln_power(x,y)
    assert fit["fitted"] and fit["n"]==5
    assert math.isclose(fit["log_D20_slope"],2,abs_tol=1e-12)
    assert math.isclose(fit["in_sample_R2_log_AGB"],1,abs_tol=1e-12)
    assert math.isclose(predict(6,fit),108,rel_tol=1e-12)
    assert not fit_ln_power([1],[3])["fitted"]
    assert fit_ln_power([1,1,1,1],[2,3,4,5])["reason"]=="DEGENERATE_LOG_DIAMETER"
    samples=[]
    for i,d in enumerate((1,2,3,4,5)):
        rec={"siteId":"s","plotId":"plot","plantId":str(i),"stemId":"1b",
             "scientificName":"Acacia aneura",
             "D20_2014_cm":str(d),"D20_2018_derived_cm":str(d+.7),
             "AGB_2014_kg":str(3*d*d),
             "AGB_2018_derived_kg":str(3*(d+.7)**2),
             "height_2014_m":"4","height_2018_derived_m":"4"}
        samples.append(rec)
    out,report=calculate(samples)
    assert len(out)==5
    assert all(not r["screen_flags"] for r in out)
    assert all(abs(r["2018_actual_divided_by_same_2014_curve_prediction"]-1)<1e-10 for r in out)
    assert report["Acacia aneura"]["2018_median_absolute_log_residual"]<1e-9
    print("STAGE32 SELF-TEST PASS: 2014 empirical log-allometry, 2018 no-bias synthetic series, one-stem exclusion, exact column shape; READ ONLY")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve()
    if (args.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(p==out or p in out.parents for p in
               (ROOT.resolve(),STAGE25.resolve(),STAGE30.resolve(),STAGE31.resolve()))):
        raise ValueError("Output must be a NEW direct HOME child")
    items,provenance=verify_inputs()
    rows,species=calculate(items)
    if len(rows)!=111 or Counter(r["scientificName"] for r in rows)!=Counter(PFT_SOURCE_STEMS):
        raise ValueError("Exact 111 species/unique-stem guard mismatch")
    if any(set(row)!=set(OUTPUT_FIELDS) for row in rows):
        raise ValueError("TSV output record schema mismatches expected fields")
    gate={
      "stage":"OzFlux AU-ASM Stage32 empirical original 2014 D20–AGB rank/formula reconstruction screen",
      "source_sha256":provenance,
      "fitted_2014_log_AGB_vs_log_D20_by_species":species,
      "unique_stems":111,
      "2014_AGB_is_source_allometric_estimate_NOT_direct_weighed_measurement":True,
      "2018_AGB_is_derived_NOT_new_field_observation":True,
      "2014_empirical_regression_is_in_sample_reference_NOT_validation":True,
      "2018_expected_AGB_is_diagnostic_only_NEVER_REPLACEMENT":True,
      "species_pooled_tower_biomass_or_carbon_stock_not_computed":True,
      "site_scale_aggregation_not_authorised":True,
      "source_D20_at_0p2m_is_NOT_FATES_DBH":True,
      "Navar2013_exact_formula_not_reconstructed":True,
      "2018_AGB_science_approved":False,
      "PFT4_vs_PFT7_and_area_fractions_approved":False,
      "soil_ten_layer_approved":False,
      "forcing_science_approved":False,
      "source_or_surface_or_FATES_parameter_modified":False,
      "CIME_or_Slurm_submitted":False,
      "AD400_authorised":False,
    }
    out.mkdir(parents=False,mode=0o700,exist_ok=False)
    with (out/"stage32_111_stem_2014_baseline_2018_derived_AGB_diagnostic.tsv").open(
        "x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS,delimiter="\t",extrasaction="raise")
        w.writeheader();w.writerows(rows)
    (out/"stage32_AU_ASM_source_AGB_allometric_consistency_science_HOLD.json").write_text(
        json.dumps(gate,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    print("STAGE32 ORIGINAL TERN/Stage30/Stage31 STEM SCIENCE SHA VERIFIED")
    print("STAGE32 111 STEMS; NO DIRECT DBH, NO SOURCE/MODEL WRITE")
    for specie,r in species.items():
        print("SPECIES",specie,"STEMS",r["n_stems"])
        print("2014 D20_LOG_AGB_FIT",r["regression_2014_log_AGB_vs_log_D20"])
        print("2014_SUM_AGB_KG",r["2014_AGB_total_kg_for_original_stems_not_site_t_per_ha"],
              "2018_DERIVED_SUM_AGB_KG",r["2018_derived_AGB_total_kg_for_same_stems_NOT_independent_field_measurement"])
        print("2018_OVER_2014_SUM_RATIO",r["2018_to_2014_sum_ratio"])
        print("2018_OVER_2014_FIT_EXPECTED",r["AGB2018_over_2014_fit_prediction_ratio"])
        print("2018_MEDIAN_ABSOLUTE_LOG_ERROR",r["2018_median_absolute_log_residual"])
        print("FLAGS",r["stem_flags_vs_2014_diameter_baseline"])
    for r in rows:
        if any(k in r["screen_flags"] for k in (
            "LT_0P2X_2014_DIAGNOSTIC_CURVE","GT_5X_2014_DIAGNOSTIC_CURVE")):
            print("STEM_REVIEW",r["scientificName"],"PLANT",r["plantId"],"STEM",r["stemId"],
                  "D20_2018",r["D20_2018_derived_cm"],
                  "AGB2018",r["AGB_2018_derived_kg"],
                  "2014_BASELINE_EXPECTED",r["AGB_2018_predicted_from_2014_D20_curve_kg"],
                  "OBSERVED_DIVIDED_BY_EXPECTED",r["2018_actual_divided_by_same_2014_curve_prediction"])
    print("STAGE32 SCIENCE HOLD: not a correction, no approved 2018 biomass or FATES model submission")
    print("REPORT_DIR",out)


if __name__=="__main__":
    main()

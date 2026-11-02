#!/usr/bin/env python3
"""OzFlux AU-ASM Stage31: 2018 derived stem AGB join/formula consistency forensics.

Data provenance: Stage25 immutable original 222-row D20 CSV; Stage30
operator-approved *read-only forensic* source-reconciled 111-pair TSV
and science HOLD receipt. This script tests whether the 2018
aboveGroundBiomass_kilograms values retain meaningful association
with source diameter/height, identify repeated exact values for
different diameter/height, and search for exact numerical values
present in other stems. These are *candidate* data join/allometry
issues, never proven source corruption or permission to edit AGB.

No derived 2018 biomass value is treated as actual field-observed
biomass change. No D20 as DBH, no data replacement, no model param/
surface/forcing/CIME/Slurm modification. Output: fresh HOME folder.
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
TERN=STAGE25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
TERN_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
PAIRS=STAGE30/"stage30_all_111_2014_field_2018_derived_original_stems.tsv"
GATE=STAGE30/"stage30_AU_ASM_derived_2018_stem_increment_science_HOLD.json"
KEYS=("siteId","plotId","plantId","stemId")
FIELDS={
    "d14":"D20_2014_cm","d18":"D20_2018_derived_cm",
    "h14":"height_2014_m","h18":"height_2018_derived_m",
    "b14":"biomass_2014_kg","b18":"biomass_2018_derived_kg",
    "dd":"delta_D20_cm","dm":"delta_AGB_kg",
}
SCIENCE_OUT=("siteId","plotId","plantId","stemId","scientificName",
             "D20_2014_cm","D20_2018_derived_cm","height_2014_m",
             "height_2018_derived_m","AGB_2014_kg","AGB_2018_derived_kg",
             "AGB_2018_over_2014_ratio","delta_D20_cm","delta_AGB_kg",
             "same_species_other_stems_with_exact_2018_AGB",
             "same_species_other_stems_with_exact_2014_AGB_equal_to_this_2018_AGB",
             "identical_2018_D20_height_other_stem_count",
             "identical_D20_height_other_stems_with_different_2018_AGB_count",
             "review_reasons","original_source_2014_stem_status",
             "original_source_2018_stem_status","original_source_2014_comment",
             "original_source_2018_comment")
THRESHOLD_BIG_RATIO=5.0
THRESHOLD_SMALL_RATIO=0.2


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def csv_rows(path,sep,columns):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Pinned input not regular file "+str(path))
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter=sep)
        missing=set(columns)-set(r.fieldnames or [])
        if missing:raise ValueError("Required source fields missing: "+repr(sorted(missing)))
        rows=list(r)
    if any(None in r for r in rows):raise ValueError("Malformed source row with extra columns")
    return rows


def num(value):
    if value is None or str(value).strip().lower() in (
        "","na","n/a","nan","null","none","-999","-999.9","-999.0",
        "-9999","-9999.0","--"):
        return None
    try:v=float(value)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None


def idkey(row):
    key=tuple(str(row.get(k) or "").strip() for k in KEYS)
    if not all(key):raise ValueError("Missing actual original stem identity")
    return key


def exact_numeric(value,decimals=8):
    # Rounding here is a *screen* only. Report matched original
    # numerical strings before concluding there is duplication.
    v=num(value)
    return round(v,decimals) if v is not None else None


def midranks(vals):
    if len(vals)<2: return None
    indexed=sorted(enumerate(vals),key=lambda pair:pair[1])
    ranks=[0.0]*len(vals)
    j=0
    while j<len(vals):
        k=j+1
        while k<len(vals) and indexed[k][1]==indexed[j][1]:k+=1
        mid=(j+1+k)/2
        for index,_ in indexed[j:k]:ranks[index]=mid
        j=k
    return ranks


def spearman(x,y):
    if len(x)!=len(y):raise ValueError("Cannot correlate unequal lengths")
    pairs=[(a,b) for a,b in zip(x,y) if a is not None and b is not None]
    if len(pairs)<4:return {"n":len(pairs),"spearman_rho":None,"reason":"FEWER_THAN_FOUR_VALID_PAIRS"}
    a,b=zip(*pairs)
    ra=midranks(a);rb=midranks(b)
    ma=statistics.mean(ra);mb=statistics.mean(rb)
    cross=sum((i-ma)*(j-mb) for i,j in zip(ra,rb))
    va=sum((i-ma)**2 for i in ra);vb=sum((j-mb)**2 for j in rb)
    if va<1e-14 or vb<1e-14:
        return {"n":len(pairs),"spearman_rho":None,"reason":"CONSTANT_RANK_VECTOR"}
    return {"n":len(pairs),"spearman_rho":cross/math.sqrt(va*vb),
            "reason":"EXPLORATORY_SPEARMAN_NOT_A_PROVEN_JOIN_FAULT"}


def verify():
    if not TERN.is_file() or TERN.is_symlink() or digest(TERN)!=TERN_SHA:
        raise ValueError("Original Stage25 TERN source SHA mismatch")
    if not GATE.is_file() or GATE.is_symlink() or not PAIRS.is_file() or PAIRS.is_symlink():
        raise ValueError("Actual Stage30 operator report/paired table missing")
    report=json.loads(GATE.read_text(encoding="utf-8"))
    flags=report.get("all_flag_counts",{})
    if (report.get("source_SHA256",{}).get("TERN_source_SHA256")!=TERN_SHA
        or report.get("n_unique_stems")!=111
        or report.get("n_flagged_stems")!=48
        or flags.get("D20_AGB_DIRECTION_DISCORDANCE_WITH_STABLE_HEIGHT")!=36
        or flags.get("DERIVED_AGB_DECREASE")!=37
        or flags.get("DERIVED_AGB_CHANGE_ABS_GT_50KG")!=20
        or report.get("AD400_authorised") is not False
        or report.get("2018_is_not_independent_stem_field_remeasurement") is not True):
        raise ValueError("Actual Stage30 science/flag counts differ from operator log")
    original=csv_rows(TERN,",",(*KEYS,"scientificName","phenomenonTime",
                     "stemDiameter_centimeters","stemHeight_metres",
                     "aboveGroundBiomass_kilograms","stemStatus","comment"))
    data=csv_rows(PAIRS,"\t",(*KEYS,"scientificName",*FIELDS.values()))
    if len(original)!=222 or len(data)!=111:
        raise ValueError("Stage30 or TERN field record counts differ")
    raw_by_key=defaultdict(dict)
    for r in original:
        date=str(r["phenomenonTime"]).strip()
        if date.endswith("/2014"):y=2014
        elif date.endswith("/2018"):y=2018
        else:raise ValueError("Raw TERN unexpected year format "+date)
        key=idkey(r)
        if y in raw_by_key[key]:raise ValueError("Duplicate raw year for same stem")
        raw_by_key[key][y]=r
    if len(raw_by_key)!=111 or any(set(d)!={2014,2018} for d in raw_by_key.values()):
        raise ValueError("Original data not exactly 111 pairs")
    registered=set()
    for r in data:
        key=idkey(r)
        if key in registered or key not in raw_by_key:
            raise ValueError("Paired TSV missing/duplicate original stem key "+repr(key))
        registered.add(key)
        if any(raw_by_key[key][y]["scientificName"]!=r["scientificName"]
               for y in (2014,2018)):
            raise ValueError("Species differs from original stem in 2014 or 2018")
        for y,d,h,b in ((2014,"d14","h14","b14"),(2018,"d18","h18","b18")):
            source=raw_by_key[key][y]
            for name,col in (("stemDiameter_centimeters",d),
                             ("stemHeight_metres",h),
                             ("aboveGroundBiomass_kilograms",b)):
                va=num(source[name]);vb=num(r[FIELDS[col]])
                if va is None or vb is None or not math.isclose(va,vb,rel_tol=1e-8,abs_tol=1e-8):
                    raise ValueError("Raw source / Stage30 numeric mismatch "+repr(key)+" "+name)
    if registered!=set(raw_by_key):
        raise ValueError("Stage30 paired stem IDs fail exact original-source set comparison")
    return data,raw_by_key,{
        "original_TERN_SHA256":TERN_SHA,
        "Stage30_pair_TSV_SHA256":digest(PAIRS),
        "Stage30_receipt_SHA256":digest(GATE),
    }


def analyze(rows,raw):
    by_species=defaultdict(list)
    for r in rows:by_species[r["scientificName"]].append(r)
    all_out=[]
    combined={}
    for specie,sdata in sorted(by_species.items()):
        ag18=defaultdict(set)
        ag14=defaultdict(set)
        pair_of_dh18=defaultdict(set)
        b18_by_dh18=defaultdict(set)
        for r in sdata:
            key=idkey(r)
            d18=num(r[FIELDS["d18"]]);h18=num(r[FIELDS["h18"]])
            b18=num(r[FIELDS["b18"]]);b14=num(r[FIELDS["b14"]])
            if b18 is not None:ag18[exact_numeric(b18)].add(key)
            if b14 is not None:ag14[exact_numeric(b14)].add(key)
            if d18 is not None and h18 is not None:
                dh=(exact_numeric(d18),exact_numeric(h18))
                pair_of_dh18[dh].add(key)
                if b18 is not None:b18_by_dh18[dh].add(exact_numeric(b18))
        for r in sdata:
            key=idkey(r)
            a=raw[key][2014];b=raw[key][2018]
            d14=num(r[FIELDS["d14"]]);d18=num(r[FIELDS["d18"]])
            h14=num(r[FIELDS["h14"]]);h18=num(r[FIELDS["h18"]])
            b14=num(r[FIELDS["b14"]]);b18=num(r[FIELDS["b18"]])
            dd=d18-d14 if d14 is not None and d18 is not None else None
            dm=b18-b14 if b14 is not None and b18 is not None else None
            ratio=b18/b14 if b14 is not None and b14>0 and b18 is not None else None
            same18=ag18.get(exact_numeric(b18),set())-{key}
            match14=ag14.get(exact_numeric(b18),set())-{key}
            dh=(exact_numeric(d18),exact_numeric(h18))
            same_dh=pair_of_dh18.get(dh,set())-{key}
            other_different_agb=sum(
                exact_numeric(num(u[FIELDS["b18"]]))!=exact_numeric(b18)
                for u in sdata if idkey(u) in same_dh)
            flags=[]
            if dd is None or dm is None:
                flags.append("MISSING_NUMERIC_PAIR")
            if dd is not None and dd>1e-6 and dm is not None and dm< -1e-6 and h14==h18:
                flags.append("D20_UP_STABLE_HEIGHT_AGB_DOWN")
            if ratio is not None and ratio<THRESHOLD_SMALL_RATIO:
                flags.append("AGB18_LESS_THAN_20_PERCENT_OF_AGB14")
            if ratio is not None and ratio>THRESHOLD_BIG_RATIO:
                flags.append("AGB18_GREATER_THAN_5_TIMES_AGB14")
            if same18:
                flags.append("EXACT_2018_AGB_REPEATED_FOR_OTHER_STEMS")
            if match14:
                flags.append("2018_AGB_EQUALS_OTHER_STEMS_2014_AGB")
            if other_different_agb:
                flags.append("SAME_D20_AND_HEIGHT_DIFFERENT_AGB_VALUES")
            rec={
              "siteId":key[0],"plotId":key[1],"plantId":key[2],"stemId":key[3],
              "scientificName":specie,
              "D20_2014_cm":d14,"D20_2018_derived_cm":d18,
              "height_2014_m":h14,"height_2018_derived_m":h18,
              "AGB_2014_kg":b14,"AGB_2018_derived_kg":b18,
              "AGB_2018_over_2014_ratio":ratio,
              "delta_D20_cm":dd,"delta_AGB_kg":dm,
              "same_species_other_stems_with_exact_2018_AGB":len(same18),
              "same_species_other_stems_with_exact_2014_AGB_equal_to_this_2018_AGB":len(match14),
              "identical_2018_D20_height_other_stem_count":len(same_dh),
              "identical_D20_height_other_stems_with_different_2018_AGB_count":other_different_agb,
              "review_reasons":";".join(sorted(flags)),
              "original_source_2014_stem_status":a["stemStatus"],
              "original_source_2018_stem_status":b["stemStatus"],
              "original_source_2014_comment":a["comment"],
              "original_source_2018_comment":b["comment"],
            }
            all_out.append(rec)
        vals=[x for x in all_out if x["scientificName"]==specie]
        ratio=[x["AGB_2018_over_2014_ratio"] for x in vals
               if x["AGB_2018_over_2014_ratio"] is not None]
        flags=Counter(f for x in vals for f in x["review_reasons"].split(";") if f)
        combined[specie]={
          "unique_stems":len(sdata),
          "2014_rank_corr_D20_AGB":spearman([num(x[FIELDS["d14"]]) for x in sdata],
                                            [num(x[FIELDS["b14"]]) for x in sdata]),
          "2018_derived_rank_corr_D20_AGB":spearman([num(x[FIELDS["d18"]]) for x in sdata],
                                                    [num(x[FIELDS["b18"]]) for x in sdata]),
          "2014_rank_corr_height_AGB":spearman([num(x[FIELDS["h14"]]) for x in sdata],
                                               [num(x[FIELDS["b14"]]) for x in sdata]),
          "2018_derived_rank_corr_height_AGB":spearman([num(x[FIELDS["h18"]]) for x in sdata],
                                                       [num(x[FIELDS["b18"]]) for x in sdata]),
          "AGB18_to_AGB14_ratio_median":statistics.median(ratio) if ratio else None,
          "AGB18_to_AGB14_ratio_min":min(ratio) if ratio else None,
          "AGB18_to_AGB14_ratio_max":max(ratio) if ratio else None,
          "2018_exact_AGB_values_repeated_within_species":sum(len(k)>1 for k in ag18.values()),
          "2018_identical_D20_height_groups_with_multiple_AGB_values":sum(
              len(b18_by_dh18[dh])>1 for dh in pair_of_dh18),
          "flags":dict(flags),
          "source_status_counts_2014":dict(Counter(raw[idkey(x)][2014]["stemStatus"] for x in sdata)),
          "source_status_counts_2018":dict(Counter(raw[idkey(x)][2018]["stemStatus"] for x in sdata)),
          "science_result":"ASSOCIATION_DIAGNOSTIC_ONLY; NOT PROOF OF ROW MISALIGNMENT OR INVALID ALLOMETRY",
        }
    return all_out,combined


def selftest():
    assert math.isclose(spearman([1,2,3,4],[1,2,3,4])["spearman_rho"],1)
    assert math.isclose(spearman([1,2,3,4],[4,3,2,1])["spearman_rho"],-1)
    assert spearman([1,1,1,1],[1,2,3,4])["spearman_rho"] is None
    assert spearman([1,2,3],[1,2,3])["reason"]=="FEWER_THAN_FOUR_VALID_PAIRS"
    sample=[]
    originals={}
    for i,(d,b14,b18) in enumerate(((4,3,0.1),(5,4,9),(6,5,0.1),(7,6,18))):
        key=("site","plot",f"plant{i}",f"stem{i}")
        row=dict(zip(KEYS,key))
        row.update(scientificName="Acacia aneura",D20_2014_cm=d,
              D20_2018_derived_cm=d+0.7,height_2014_m=3,
              height_2018_derived_m=3,biomass_2014_kg=b14,
              biomass_2018_derived_kg=b18)
        sample.append(row)
        originals[key]={2014:dict(stemStatus="live",comment="2014"),
                        2018:dict(stemStatus="derived",comment="2018")}
    out,by=analyze(sample,originals)
    assert len(out)==4
    assert any("AGB18_LESS_THAN_20_PERCENT_OF_AGB14" in x["review_reasons"] for x in out)
    assert any("EXACT_2018_AGB_REPEATED_FOR_OTHER_STEMS" in x["review_reasons"] for x in out)
    expected_report_keys=(
        "2014_rank_corr_D20_AGB",
        "2018_derived_rank_corr_D20_AGB",
        "2014_rank_corr_height_AGB",
        "2018_derived_rank_corr_height_AGB",
        "AGB18_to_AGB14_ratio_median",
        "2018_exact_AGB_values_repeated_within_species",
        "2018_identical_D20_height_groups_with_multiple_AGB_values",
    )
    report=by["Acacia aneura"]
    assert all(key in report for key in expected_report_keys)
    assert report["2018_derived_rank_corr_D20_AGB"]["n"]==4
    assert report["2014_rank_corr_D20_AGB"]["n"]==4
    assert report["2018_exact_AGB_values_repeated_within_species"]==1
    assert all(set(row)==set(SCIENCE_OUT) for row in out)
    print("STAGE31 SELF-TEST PASS: Spearman, extreme AGB ratios, duplicate values, all JSON/TSV report keys, synthetic 4 stems, no model writes")


def main():
    if sys.argv[1:]==["--self-test"]:selftest();return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(p==out or p in out.parents for p in
               (ROOT.resolve(),STAGE25.resolve(),STAGE30.resolve()))):
        raise ValueError("Output must be fresh direct HOME child")
    data,raw,provenance=verify()
    rows,by=analyze(data,raw)
    if len(rows)!=111 or sum(x["scientificName"] in ("Acacia aneura","Acacia aptaneura") for x in rows)!=103:
        raise ValueError("Expected exact 111 original stem IDs including 103 Acacia")
    source_gate={
      "stage":"OzFlux AU-ASM Stage31 2018 derived AGB row-join/formula-consistency audit",
      "source_hashes":provenance,
      "actual_2014_vs_2018":by,
      "n_unique_stems":111,
      "operator_stage30_flagged_stem_count":48,
      "2018_source_values_per_stem_verified_against_original":True,
      "suspected_AGB_mapping_or_allometric_formula_issue_NOT_PROVEN":True,
      "baseline_source_formula_Navar2013_specific_implementation_NOT_AVAILABLE":True,
      "Spearman_and_duplicate_value_screens_not_physical_model_reconstruction":True,
      "2018_derived_AGB_observations_not_independent_field_surveys":True,
      "AGB_2018_science_approved":False,
      "observed_2014_height_data_unchanged":True,
      "FATES4_vs_FATES7_PFT_science_approved":False,
      "source_D20_is_not_DBH":True,
      "FATES_params_or_surface_created_or_modified":False,
      "forcing_science_approved":False,
      "Slurm_or_CIME_submitted":False,
      "AD400_authorised":False,
      "next":"Inspect TERN biomass derivation/mapping and source dictionary with field authors or model, obtain independent 2018 site-level AGB and direct 2014 DBH core survey before calibration",
    }
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    with (out/"stage31_all_111_stem_AGB_join_association_screens.tsv").open(
      "x",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=SCIENCE_OUT,extrasaction="raise",delimiter="\t")
        w.writeheader();w.writerows(rows)
    (out/"stage31_AU_ASM_derived_AGB_join_formula_science_HOLD.json").write_text(
       json.dumps(source_gate,indent=2,ensure_ascii=False,allow_nan=False),
       encoding="utf-8")
    print("STAGE31 SOURCE ORIGINAL TERN SHA VERIFIED",TERN_SHA)
    print("STAGE31 STAGE30 111 SOURCE-RECONCILED STEM PAIRS AND 48 FLAGGED VERIFIED")
    for species,block in by.items():
        print("SPECIES",species,"N",block["unique_stems"])
        print("D20_AGB_SPEARMAN_2014",block["2014_rank_corr_D20_AGB"])
        print("D20_AGB_SPEARMAN_2018_DERIVED",block["2018_derived_rank_corr_D20_AGB"])
        print("HEIGHT_AGB_SPEARMAN_2014",block["2014_rank_corr_height_AGB"])
        print("HEIGHT_AGB_SPEARMAN_2018_DERIVED",block["2018_derived_rank_corr_height_AGB"])
        print("AGB_RATIO",block["AGB18_to_AGB14_ratio_min"],
              block["AGB18_to_AGB14_ratio_median"],block["AGB18_to_AGB14_ratio_max"])
        print("REPEATED_2018_VALUES",block["2018_exact_AGB_values_repeated_within_species"],
              "SAME_D20_HEIGHT_DIFFERENT_AGB_GROUPS",
              block["2018_identical_D20_height_groups_with_multiple_AGB_values"])
        print("FLAGS",block["flags"])
    flagged=[r for r in rows if (
       r["AGB_2018_over_2014_ratio"] is not None and (
       r["AGB_2018_over_2014_ratio"]<THRESHOLD_SMALL_RATIO or
       r["AGB_2018_over_2014_ratio"]>THRESHOLD_BIG_RATIO))
       or r["identical_D20_height_other_stems_with_different_2018_AGB_count"]>0]
    print("STAGE31 SOURCE REVIEW CANDIDATES",len(flagged))
    for r in flagged:
        print("AGB_ASSOCIATION_CANDIDATE",r["scientificName"],
              "PLANT",r["plantId"],"STEM",r["stemId"],
              "D20",r["D20_2014_cm"],r["D20_2018_derived_cm"],
              "HEIGHT",r["height_2018_derived_m"],
              "AGB",r["AGB_2014_kg"],r["AGB_2018_derived_kg"],
              "RATIO",r["AGB_2018_over_2014_ratio"],
              "FLAGS",r["review_reasons"])
    print("STAGE31 ASSOCIATION SCREENS NOT PROOF OF SOURCE MISALIGNMENT")
    print("STAGE31 NO FATES/PFT/SOIL/FORCING APPROVAL OR CIME/SLURM")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""AU-ASM Stage28 — original TERN stem record longitudinal/duplicate forensics.

Stage27 reported 222 rows, but 111 unique stem keys and ALL
phenomenonTime years UNSPECIFIED. Fix inference, not the original data:
 - distinguish separate raw rows, stem identities and unique plants
 - inspect phenomenonTime, startVisitDate, endVisitDate independently
 - quantify exact 2014/2018 row-level evidence vs publisher's 2014
   acquisition/2018 increment-derived lineage (not repeat surveys)
 - classify each unique stem's height records against the exact
   FATES7 allometry height cap using ALL repeated rows: all above /
   all below / discordant; missing heights separate. No arbitrary
   'first record is 2014' shortcut.
 - NEVER substitute D20 as a 1.30 m DBH, fit FATES allometry,
   write original CSV, create surface/case, or submit Slurm/AD400.
Outputs new JSON and TSV in one fresh direct child of HOME.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE25=HOME/"ozflux_stage25_20261102T121025Z"
STAGE26=HOME/"ozflux_stage26_20261102T122636Z"
STAGE27=HOME/"ozflux_stage27_20261102T123656Z"
STEM=STAGE25/"Alice_Mulga_diameter_height_biomass_data_lVZI0qg.csv"
DICT=STAGE25/"Alice_Mulga_diameter_height_biomass_data_dictionary_XcBdgzD.csv"
STEM_SHA="7a3f4efabc1c8650670bc996d25d2145cd5f5a2679f6fe8f2003d487c4a0db55"
DICT_SHA="82c2d28b8616ee31f1c687ef600f4249592827503adbdcfce73e1e06b6da44fe"
MODEL_HEIGHT_CAP=4.735410175384586
REQUIRED=("siteId","plotId","plantId","stemId","scientificName",
          "stemHeight_metres","stemDiameter_centimeters",
          "stemDiameterPointOfMeasurement_metres",
          "startVisitDate","endVisitDate","phenomenonTime")
DATE_FIELDS=("startVisitDate","endVisitDate","phenomenonTime")
STEM_COLUMNS=("siteId","plotId","plantId","stemId","scientificName",
              "raw_rows_for_stem","valid_height_rows",
              "distinct_valid_heights_m","min_height_m","max_height_m",
              "height_comparison_to_FATES7_cap",
              "raw_exceedance_rows","diameter_measurement_heights_m",
              "raw_date_values_by_field","date_classification",
              "data_caveat")
SPECIES_COLUMNS=("scientificName","raw_rows",
                 "unique_stem_keys","unique_plant_keys",
                 "raw_valid_height_rows","raw_height_exceedance_rows",
                 "independent_stem_keys_all_heights_above_cap",
                 "independent_stem_keys_all_heights_at_or_below_cap",
                 "independent_stem_keys_discordant_about_cap",
                 "independent_stem_keys_missing_all_height",
                 "height_exceedance_rate_per_unique_stem_when_unambiguous",
                 "rows_per_stem_distribution","scope_note")


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as fd:
        for b in iter(lambda:fd.read(2**20),b""):
            h.update(b)
    return h.hexdigest()


def csv_rows(p,required=()):
    if p.is_symlink() or not p.is_file():
        raise ValueError("Original source missing/symlink: "+str(p))
    with p.open("r",encoding="utf-8-sig",newline="") as fd:
        r=csv.DictReader(fd)
        h=r.fieldnames or []
        if not set(required).issubset(h):
            raise ValueError("Original TERN fields not found "+
                             repr(sorted(set(required)-set(h))))
        rows=list(r)
    if any(None in row for row in rows):
        raise ValueError("TERN original CSV has irregular extra columns")
    return rows


def numeric(raw):
    try:
        if raw is None or str(raw).strip().lower() in (
            "","na","nan","null","none","-999","-999.9","-999.0","-9999"):
            return None
        v=float(raw)
        return v if math.isfinite(v) else None
    except (TypeError,ValueError):
        return None


def datestring(s):
    text=str(s or "").strip()
    if not text:return "EMPTY"
    # ISO-like and four-digit YYYY-MM-DD forms only; reject other
    # formats rather than speculatively converting local formats.
    match=re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:[T\s].*)?$",text)
    if match:
        yr,mo,day=(int(x) for x in match.groups())
        if 1950<=yr<=2030 and 1<=mo<=12 and 1<=day<=31:
            return str(yr)
    return "UNPARSEABLE"


def stem_identity(r):
    parts=tuple(str(r.get(k) or "").strip() for k in
                ("siteId","plotId","plantId","stemId"))
    return parts if all(parts) else None


def plant_identity(r):
    parts=tuple(str(r.get(k) or "").strip() for k in
                ("siteId","plotId","plantId"))
    return parts if all(parts) else None


def verify():
    if STEM.is_symlink() or sha(STEM)!=STEM_SHA:
        raise ValueError("Stage25 222-row stem source SHA changed")
    if DICT.is_symlink() or sha(DICT)!=DICT_SHA:
        raise ValueError("Stage25 stem dictionary SHA changed")
    r26=STAGE26/"stage26_TERN_actual_D20_DBH_leaf_science_gate.json"
    r27=STAGE27/"stage27_AU_ASM_measured_structure_leaf_science_HOLD.json"
    for p in (r26,r27):
        if p.is_symlink() or not p.is_file():
            raise ValueError("Actual operator science receipt not found "+str(p))
    x=json.loads(r26.read_text(encoding="utf-8"))
    y=json.loads(r27.read_text(encoding="utf-8"))
    if (x.get("TERN_stem_rows_original")!=222 or
        x.get("stem_science",{}).get("measurement_point_class_counts")!=
          {"BASAL_D20_0P20M_NOT_DBH":222} or
        x.get("stem_science",{}).get("direct_DBH_height_pair_count")!=0 or
        x.get("scientific_decision",{}).get("AD400_authorised") is not False or
        y.get("stem_comparison_QC",{}).get("stem_years")!={"UNSPECIFIED":222} or
        not math.isclose(float(y.get("FATES7_local_exact_height_ceiling_m")),
                         MODEL_HEIGHT_CAP,rel_tol=1e-11) or
        y.get("AD400_authorised") is not False):
        raise ValueError("Stage26/27 operator receipts not those in user log")
    rows=csv_rows(STEM,REQUIRED)
    dic=csv_rows(DICT,("Dictionary","URL","Description"))
    if len(rows)!=222 or len(dic)!=21:
        raise ValueError("Original stem or dictionary row count mismatch")
    for r in rows:
        point=numeric(r["stemDiameterPointOfMeasurement_metres"])
        if point is None or not math.isclose(point,0.2,abs_tol=.025):
            raise ValueError("Stage26 original all-D20 classification changed")
    return rows,dic,{"stem_csv_SHA256":STEM_SHA,"stem_dictionary_SHA256":DICT_SHA,
                      "Stage26_report_SHA256":sha(r26),
                      "Stage27_report_SHA256":sha(r27)}


def summarize(rows):
    stems=defaultdict(list)
    missing_keys=[]
    times={field:{"classification":Counter(),"values":Counter()}
           for field in DATE_FIELDS}
    species_raw=Counter()
    for i,r in enumerate(rows):
        for field in DATE_FIELDS:
            value=str(r.get(field) or "").strip()
            times[field]["classification"][datestring(value)]+=1
            times[field]["values"][value if value else "<EMPTY>"]+=1
        species=(r.get("scientificName") or "").strip() or "UNSPECIFIED"
        species_raw[species]+=1
        key=stem_identity(r)
        if key is None:
            missing_keys.append(i+2)
            continue
        stems[key].append(r)
    per_stem=[]
    group=defaultdict(list)
    byspeciesplant=defaultdict(set)
    for key,rr in sorted(stems.items()):
        spec=Counter((r.get("scientificName") or "").strip() for r in rr)
        species=spec.most_common(1)[0][0] or "UNSPECIFIED"
        heights=[numeric(r["stemHeight_metres"]) for r in rr]
        heights=[h for h in heights if h is not None and 0<h<100]
        n_exc=sum(h>MODEL_HEIGHT_CAP for h in heights)
        if not heights:cls="NO_VALID_HEIGHT"
        elif n_exc==len(heights):cls="ALL_ABOVE"
        elif n_exc==0:cls="ALL_AT_OR_BELOW"
        else:cls="DISCORDANT_ABOVE_AND_BELOW"
        measurement_heights=sorted(set(str(r["stemDiameterPointOfMeasurement_metres"]) for r in rr))
        datevals={field:sorted(set(
                str(r.get(field) or "").strip() or "<EMPTY>" for r in rr))
                  for field in DATE_FIELDS}
        nonempty=any(v!="<EMPTY>" for vals in datevals.values() for v in vals)
        datecl="ROW_DATE_VALUES_PRESENT" if nonempty else "NO_ROW_DATES_METADATA_ONLY_2014"
        item={
          "siteId":key[0],"plotId":key[1],"plantId":key[2],"stemId":key[3],
          "scientificName":species,"raw_rows_for_stem":len(rr),
          "valid_height_rows":len(heights),
          "distinct_valid_heights_m":json.dumps(sorted(set(heights))),
          "min_height_m":min(heights) if heights else None,
          "max_height_m":max(heights) if heights else None,
          "height_comparison_to_FATES7_cap":cls,
          "raw_exceedance_rows":n_exc,
          "diameter_measurement_heights_m":json.dumps(measurement_heights),
          "raw_date_values_by_field":json.dumps(datevals,ensure_ascii=False),
          "date_classification":datecl,
          "data_caveat":"Not independent visits: 2014 source survey, 2018 derived values according to publisher; D20 not DBH",
        }
        per_stem.append(item)
        group[species].append(item)
        byspeciesplant[species].add(key[:3])
    overview=[]
    for specie,items in sorted(group.items()):
        freq=Counter(x["raw_rows_for_stem"] for x in items)
        above=sum(x["height_comparison_to_FATES7_cap"]=="ALL_ABOVE" for x in items)
        below=sum(x["height_comparison_to_FATES7_cap"]=="ALL_AT_OR_BELOW" for x in items)
        mixed=sum(x["height_comparison_to_FATES7_cap"]=="DISCORDANT_ABOVE_AND_BELOW" for x in items)
        missing=sum(x["height_comparison_to_FATES7_cap"]=="NO_VALID_HEIGHT" for x in items)
        denominator=above+below
        overview.append({
          "scientificName":specie,
          "raw_rows":species_raw[specie],
          "unique_stem_keys":len(items),
          "unique_plant_keys":len(byspeciesplant[specie]),
          "raw_valid_height_rows":sum(x["valid_height_rows"] for x in items),
          "raw_height_exceedance_rows":sum(x["raw_exceedance_rows"] for x in items),
          "independent_stem_keys_all_heights_above_cap":above,
          "independent_stem_keys_all_heights_at_or_below_cap":below,
          "independent_stem_keys_discordant_about_cap":mixed,
          "independent_stem_keys_missing_all_height":missing,
          "height_exceedance_rate_per_unique_stem_when_unambiguous":(
              above/denominator if denominator else None),
          "rows_per_stem_distribution":json.dumps(dict(sorted(freq.items()))),
          "scope_note":"unique stem IDs, NOT independent trees; may be derived duplicated records",
        })
    date_report={}
    for field,data in times.items():
        date_report[field]={
          "year_parse_class_counts":dict(data["classification"]),
          "unique_value_count":len(data["values"]),
          "top_12_original_values":[{"value":k,"rows":v}
                                   for k,v in data["values"].most_common(12)],
        }
    return per_stem,overview,{
        "raw_rows":len(rows),
        "rows_missing_complete_stem_key":len(missing_keys),
        "source_csv_row_numbers_missing_complete_stem_key":missing_keys[:25],
        "unique_stem_keys":len(stems),
        "stem_repeat_count_distribution":dict(Counter(len(x) for x in stems.values())),
        "each_stem_exactly_2_rows":bool(stems) and all(len(x)==2 for x in stems.values()),
        "dates_by_original_field":date_report,
        "row_2014_measured_vs_2018_derived_classified_by_individual_row":False,
        "2014_metadata_survey_date_not_equivalent_to_row_level_measurement_date":True,
        "2014_tall_stem_absent_conclusion_from_UNSPECIFIED_IS_INVALID":True,
        "raw_exceedance_percentage_not_independent_stem_or_tree_percentage":True,
    }


def dictionary_mentions(rows):
    result=[]
    for r in rows:
        value=" ".join(str(v or "") for v in r.values())
        if any(t in value.lower() for t in
               ("date","time","stemheight","height","diameter","plot",
                "stemid","plantid","phenomenon")):
            result.append(r)
    return result


def output_tsv(path,fields,rows):
    with path.open("x",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,delimiter="\t",fieldnames=fields,extrasaction="raise")
        w.writeheader();w.writerows(rows)


def selftest():
    assert datestring("")=="EMPTY"
    assert datestring("2014-01-21")=="2014"
    assert datestring("2018-11-21T12:15:00")=="2018"
    assert datestring("21/01/2014")=="UNPARSEABLE"
    assert stem_identity({"siteId":"x","plotId":"p","plantId":"a","stemId":"s"})==("x","p","a","s")
    assert numeric("-999.9") is None
    assert MODEL_HEIGHT_CAP>4.7 and MODEL_HEIGHT_CAP<4.8
    rows=[dict(siteId="x",plotId="p",plantId="a",stemId="1",scientificName="Acacia aneura",
               stemHeight_metres="5.5",stemDiameterPointOfMeasurement_metres="0.2",
               startVisitDate="",endVisitDate="",phenomenonTime="")]*2
    per,by,summary=summarize(rows)
    assert len(per)==1 and summary["each_stem_exactly_2_rows"]
    assert by[0]["independent_stem_keys_all_heights_above_cap"]==1
    assert summary["dates_by_original_field"]["phenomenonTime"]["year_parse_class_counts"]=={"EMPTY":2}
    print("STAGE28 SELF-TEST PASS: 2014/2018 date audit, deduplicated stem-key exceedance, no D20=DBH, false-zero protection; READ ONLY")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=HOME.resolve()
        or any(q==out or q in out.parents for q in
               (ROOT.resolve(),STAGE25.resolve(),STAGE26.resolve(),STAGE27.resolve()))):
        raise ValueError("Output must be fresh DIRECT child of HOME")
    source,dictionary,receipts=verify()
    rows,by,stats=summarize(source)
    report={
      "stage":"OzFlux Stage28 TERN 2014 stem date and duplicate source forensics",
      "source_SHA256":receipts,
      "read_only":True,
      "TERN_publisher_source":"https://portal.tern.org.au/metadata/c2968de2-1e8b-4a05-919f-46744b3171ed",
      "TERN_publisher_survey_year":2014,
      "TERN_publisher_2018_method":"2018 derived uniform basal area increment, NOT repeat independent stem survey",
      "valid_DBH_1p3m_source_rows":0,
      "verified_default_FATES7_height_cap_m":MODEL_HEIGHT_CAP,
      "stem_identity_and_temporal_audit":stats,
      "species_unique_stem_vs_row_counts":by,
      "relevant_original_TERN_stem_dictionary_entries":dictionary_mentions(dictionary),
      "independent_true_DBH_core_2014_file":{
        "metadata":"https://researchdata.edu.au/vegetation-data-direct-ha-2014/617073",
        "direct_original_download_verified":False,
        "focal_plot_86_trees_200_stems_from_metadata_ONLY":True,
      },
      "height_cap_structural_compatibility_further_supported_NOT_PFT_approval":True,
      "Acacia_PFT4_or_PFT7_science_approved":False,
      "PFT_fraction_or_Kandosol_soil_approved":False,
      "final_forcing_science_approved":False,
      "model_CIME_case_or_Slurm_created":False,
      "AD400_authorised":False,
    }
    out.mkdir(mode=0o700,parents=False,exist_ok=False)
    output_tsv(out/"stage28_TERN_unique_stem_height_and_provenance.tsv",STEM_COLUMNS,rows)
    output_tsv(out/"stage28_TERN_species_unique_stem_height_ceiling_summary.tsv",SPECIES_COLUMNS,by)
    (out/"stage28_TERN_time_and_duplicate_stem_science_HOLD.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),
        encoding="utf-8")
    print("STAGE28 SOURCE SHA VERIFIED",STEM_SHA)
    print("STAGE28 ORIGINAL 222 STEM ROWS; UNIQUE STEM KEYS",stats["unique_stem_keys"])
    print("STAGE28 STEM REPEAT DISTRIBUTION",stats["stem_repeat_count_distribution"])
    print("STAGE28 ALL STEMS REPEAT EXACTLY 2 ROWS",stats["each_stem_exactly_2_rows"])
    for field,s in stats["dates_by_original_field"].items():
        print("DATE FIELD",field,"CLASSES",s["year_parse_class_counts"],
              "VALUES",s["top_12_original_values"])
    for row in by:
        print("SPECIES",row["scientificName"],"RAW",row["raw_rows"],
              "UNIQUE_STEMS",row["unique_stem_keys"],
              "UNIQUE_PLANTS",row["unique_plant_keys"],
              "EXCEEDING_ALL_ROW_HEIGHTS",row["independent_stem_keys_all_heights_above_cap"],
              "NOT_EXCEEDING",row["independent_stem_keys_all_heights_at_or_below_cap"],
              "DISCORDANT",row["independent_stem_keys_discordant_about_cap"])
    print("STAGE28 DO NOT ASSERT TALL 2014 STEMS ABSENT WHEN NO ROW-LEVEL YEAR")
    print("STAGE28 NO DBH-HEIGHT REPAIR/NO PFT/SOIL APPROVAL/NO MODEL RUN")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""JapanFlux Stage05L — verify original per-site BIF timezone, units and QC, map 45 HOLD cells to UTC.

Only reads 5 existing Stage05K metadata JSON reports plus Stage05I HOLD TSV.
Read-only originals. Derived output includes UTC lookup labels, NEVER any
independent ERA value or approved replacement. No ZIP read, no Slurm.
If any site lacks verified original metadata, NO UTC mapping file is created.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

SITES=("JP-Fjy","JP-Khw","JP-Tef","JP-Tmd","JP-Yms")
EXPECTED_UNITS={"TA_F":"deg C","TA_ERA":"deg C",
                "PA_F":"kPa","PA_ERA":"kPa",
                "LW_IN_F":"W m-2","LW_IN_ERA":"W m-2",
                "VPD_F":"hPa"}
EXPECTED_QC=("TA_F_QC","PA_F_QC","LW_IN_F_QC","VPD_F_QC")
QC_CHECKS=(r"\b0\s*=\s*measured\b",r"\b1\s*=\s*good quality gapfill\b",
           r"\b2\s*=\s*downscaled from ERA\b")
TSV_HEADER=("site","native_start","utc_start","utc_end","utc_offset_hours",
            "variable","source_value","source_unit","original_F_QC",
            "ERA_same_release_value","screen_evidence","science_status")


def values_by_name(report: dict) -> dict:
    groups = report["BIFVARINFO_HH"]["focus_variable_groups"]
    names={}
    for group in groups:
        fields={rec["key"]:rec["value"] for rec in group["source_fields"]}
        var=fields.get("VAR_INFO_VARNAME")
        if var:
            if var in names:
                raise ValueError("Repeated original BIFVARINFO variable: "+var)
            names[var]=fields
    return names


def inspect_site(report: dict,site: str) -> dict:
    problems=[]
    if report.get("site")!=site or report.get("stage")!="JapanFlux Stage05K" or report.get("status")!="READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED":
        problems.append("wrong site/stage/status")
    all_vars=values_by_name(report)
    for var,wanted in EXPECTED_UNITS.items():
        if var not in all_vars:
            problems.append("missing BIF variable "+var)
        elif all_vars[var].get("VAR_INFO_UNIT","").strip()!=wanted:
            problems.append(var+" unexpected unit "+repr(all_vars[var].get("VAR_INFO_UNIT")))
    for var in EXPECTED_QC:
        fields=all_vars.get(var)
        if not fields:
            problems.append("missing BIF QC variable "+var)
            continue
        definition=fields.get("VAR_INFO_DEFINITION","")
        if any(not re.search(pattern,definition,re.I) for pattern in QC_CHECKS):
            problems.append(var+" incomplete/changed QC definition")
    for var in ("TA_ERA","PA_ERA","LW_IN_ERA"):
        definition=all_vars.get(var,{}).get("VAR_INFO_DEFINITION","")
        if not ("downscaled from ERA" in definition and "linearly regressed" in definition):
            problems.append(var+" ERA downscaling provenance unverified")
    offsets=set()
    readme_valid=False
    original_hints=[]
    for doc in report.get("site_metadata_and_readme",[]):
        base=Path(doc["member"]).name
        lines=doc.get("first_90_time_unit_hints",[])
        for item in lines:
            line=item["text"]
            if "GRP_UTC_OFFSET" in line and "UTC_OFFSET" in line:
                try:
                    cells=next(csv.reader([line]))
                    if len(cells)>=5 and cells[0].strip()==site and cells[2].strip()=="GRP_UTC_OFFSET" and cells[3].strip()=="UTC_OFFSET":
                        offsets.add(float(cells[4]))
                        original_hints.append({"member":base,"line":item["line"],"offset":cells[4]})
                except (ValueError, csv.Error, StopIteration):
                    problems.append("Cannot parse original UTC_OFFSET source row")
            if base.upper()=="README.TXT" and (
                "local standard time" in line.lower() and
                "without dst" in line.lower()
            ):
                readme_valid=True
                original_hints.append({"member":base,"line":item["line"],"clock_excerpt":line[:500]})
    if len(offsets)!=1:
        problems.append("Expected exactly one source BIF UTC_OFFSET, found "+repr(sorted(offsets)))
    if not readme_valid:
        problems.append("README local standard time without DST not confirmed")
    if len(offsets)==1 and next(iter(offsets))!=9:
        # Prevent assuming every Japanese package is +9 when source disagrees.
        problems.append("Original UTC offset differs from expected JST +9: "+repr(sorted(offsets)))
    return {"site":site,"status":"VERIFIED" if not problems else "HOLD_METADATA_UNVERIFIED",
            "problems":problems,
            "UTC_OFFSET_hours":next(iter(offsets)) if len(offsets)==1 else None,
            "README_local_standard_time_without_DST":readme_valid,
            "original_time_source_rows":original_hints,
            "verified_unit_variables":list(EXPECTED_UNITS),
            "verified_QC_definition_variables":list(EXPECTED_QC)}


def read_45(hold:Path)->list[dict]:
    with hold.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=45:
        raise ValueError("Expected Stage05I exactly 45 source HOLD variable entries")
    keys={(r["site"],r["native_start"],r["variable"]) for r in rows}
    if len(keys)!=45 or len({(s,t) for s,t,_ in keys})!=35:
        raise ValueError("Stage05I 45 field and 35 site×native-halfhour invariants failed")
    if set(r["site"] for r in rows)!=set(SITES) or any(r["science_status"]!="HOLD_UNAPPROVED_SOURCE_REVIEW" for r in rows):
        raise ValueError("Unexpected source site or prior science approval in Stage05I")
    return rows


def convert(rows:list[dict],statuses:dict)->list[dict]:
    converted=[]
    for r in rows:
        site=r["site"]
        offset=statuses[site]["UTC_OFFSET_hours"]
        if statuses[site]["status"]!="VERIFIED" or offset is None:
            raise ValueError("Cannot generate UTC mapping for unverified BIF site "+site)
        stamp=datetime.strptime(r["native_start"],"%Y%m%d%H%M")
        start=stamp-timedelta(hours=offset)
        field=r["variable"]
        unit={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}[field]
        converted.append({
            "site":site,"native_start":r["native_start"],
            "utc_start":start.strftime("%Y%m%d%H%M"),
            "utc_end":(start+timedelta(minutes=30)).strftime("%Y%m%d%H%M"),
            "utc_offset_hours":offset,
            "variable":field,"source_value":r["selected_F_value"],
            "source_unit":unit,"original_F_QC":r["selected_F_QC_raw"],
            "ERA_same_release_value":r["embedded_ERA_value"],
            "screen_evidence":r["screen_evidence"],
            "science_status":"HOLD_UNAPPROVED_INDEPENDENT_ERA_CHECK"})
    return sorted(converted,key=lambda x:(x["site"],x["utc_start"],x["variable"]))


def self_test()->None:
    r={"site":"JP-Khw","stage":"JapanFlux Stage05K",
       "status":"READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED",
       "BIFVARINFO_HH":{"focus_variable_groups":[]},
       "site_metadata_and_readme":[
           {"member":"JPF_JP-Khw_BIF.csv","first_90_time_unit_hints":[
               {"line":64,"text":"JP-Khw,3365,GRP_UTC_OFFSET,UTC_OFFSET,9"}]},
           {"member":"README.txt","first_90_time_unit_hints":[
               {"line":69,"text":"time is expressed in local standard time (without DST)."}]}]}
    for var,unit in EXPECTED_UNITS.items():
        r["BIFVARINFO_HH"]["focus_variable_groups"].append({
            "source_fields":[{"key":"VAR_INFO_VARNAME","value":var},
                {"key":"VAR_INFO_UNIT","value":unit},
                {"key":"VAR_INFO_DEFINITION","value":"Atmosphere downscaled from ERA, linearly regressed using measured only site data"}]})
    for var in EXPECTED_QC:
        r["BIFVARINFO_HH"]["focus_variable_groups"].append({
            "source_fields":[{"key":"VAR_INFO_VARNAME","value":var},
                {"key":"VAR_INFO_DEFINITION","value":"0 = measured; 1 = good quality gapfill; 2 = downscaled from ERA"}]})
    s=inspect_site(r,"JP-Khw")
    assert s["status"]=="VERIFIED" and s["UTC_OFFSET_hours"]==9
    dt=datetime.strptime("200508120300","%Y%m%d%H%M")-timedelta(hours=9)
    assert dt.strftime("%Y%m%d%H%M")=="200508111800"
    print("STAGE05L SELF-TEST PASS | original BIF QC/time/unit gates and JST→UTC algebra; NO WRITES")


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metadata-dir",type=Path)
    p.add_argument("--stage05i-tsv",type=Path)
    p.add_argument("--out-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not all((a.metadata_dir,a.stage05i_tsv,a.out_dir)):
        p.error("Must provide --metadata-dir, --stage05i-tsv, --out-dir")
    metadata={}
    for site in SITES:
        f=a.metadata_dir/(site+"_exact_metadata.json")
        r=json.loads(f.read_text(encoding="utf-8"))
        metadata[site]=inspect_site(r,site)
    source_rows=read_45(a.stage05i_tsv)
    all_verified=all(d["status"]=="VERIFIED" for d in metadata.values())
    summary={"stage":"JapanFlux Stage05L",
             "status":"VERIFIED_METADATA_5_OF_5_UTC_MAPPING_GENERATED" if all_verified else "HOLD_INCOMPLETE_OR_CONFLICTING_METADATA",
             "sites":metadata,"verified_sites":sum(d["status"]=="VERIFIED" for d in metadata.values()),
             "source_hold_fields":45,"source_hold_site_native_halfhours":35,
             "utc_mapping_generated":all_verified,"independent_ECMWF_ERA5_lookups":"NOT_PERFORMED",
             "original_data_changes":False,"model_forcing_approved":False}
    out=a.out_dir
    if out.resolve() in (a.metadata_dir.resolve(),a.stage05i_tsv.parent.resolve()):
        p.error("Outdir cannot equal input dir")
    out.mkdir(parents=True,exist_ok=True)
    js=out/"stage05l_source_metadata_validation.json"
    tsv=out/"stage05l_45_hold_native_to_utc.tsv"
    if js.exists() or tsv.exists():
        p.error("Output already exists; choose new directory")
    if all_verified:
        rows=convert(source_rows,metadata)
        with tsv.open("x",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,delimiter="\t",fieldnames=TSV_HEADER)
            w.writeheader();w.writerows(rows)
    with js.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False)
        f.write("\n")
    print("STAGE05L",summary["status"],"VERIFIED",summary["verified_sites"],"/5")
    for site,info in metadata.items():
        print("SITE",site,info["status"],"UTC_OFFSET",info["UTC_OFFSET_hours"],
              "ISSUES",info["problems"])
    if all_verified:
        print("UTC_EVENT_LOOKUP",tsv)
        print("FIELD_RECORDS",len(rows))
    else:
        print("NO UTC JOIN GENERATED: FIX ORIGINAL METADATA PROVENANCE FIRST")
    print("METADATA_REPORT",js)
    print("NO ORIGINAL SOURCE WRITES OR APPROVED REPLACEMENTS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

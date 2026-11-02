#!/usr/bin/env python3
"""Stage05O: 3-site verified UTC lookup; 2-site 'local solar' time HOLD.

NO ZIP, NO SLURM, NO SOURCE/MODEL EDITS. Inputs: actual Stage05L metadata
result, Stage05N SHA-verified full README log, Stage05I 45-record HOLD TSV.
Never infer JP-Tef or JP-Tmd UTC from the unresolved README conflict.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path

VERIFIED=("JP-Fjy","JP-Khw","JP-Yms")
UNRESOLVED=("JP-Tef","JP-Tmd")
EXPECTED_COUNT={"JP-Fjy":6,"JP-Khw":11,"JP-Tef":4,"JP-Tmd":14,"JP-Yms":10}
BAD_README_SHA="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
MAP_FIELDS=("site","native_start","utc_start","utc_end","variable","selected_F","ERA_in_same_release","raw_F_QC","unit","source_status")
HOLD_FIELDS=("site","native_start","utc_start","variable","selected_F","ERA_in_same_release","raw_F_QC","unit","source_status")
UNIT={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}

def tsv_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def verify_inputs(meta,raw_readme,rows):
    r=json.loads(meta.read_text(encoding="utf-8"))
    sites=r.get("sites",{})
    if r.get("stage")!="JapanFlux Stage05L" or set(sites)!=set(EXPECTED_COUNT):
        raise ValueError("Unexpected Stage05L source validation")
    if r.get("status")!="HOLD_INCOMPLETE_OR_CONFLICTING_METADATA" or r.get("verified_sites")!=3 or r.get("utc_mapping_generated") is not False:
        raise ValueError("Require actual 3/5 source metadata HOLD, no earlier UTC mapping")
    for site in VERIFIED:
        s=sites[site]
        if s.get("status")!="VERIFIED" or s.get("UTC_OFFSET_hours")!=9 or s.get("problems") or s.get("README_local_standard_time_without_DST") is not True:
            raise ValueError("Original BIF/README standard-time evidence incomplete: "+site)
    for site in UNRESOLVED:
        s=sites[site]
        if s.get("status")!="HOLD_METADATA_UNVERIFIED" or s.get("UTC_OFFSET_hours")!=9 or s.get("problems")!=["README local standard time without DST not confirmed"]:
            raise ValueError("Unreviewed source metadata change: "+site)
    text=raw_readme.read_text(encoding="utf-8")
    for phrase in (
        "STAGE05N SOURCE README BYTE VALIDATION PASS",
        "ORIGINAL_SITE JP-Tef",
        "MATCHING_SAVED_SOURCE_SITES JP-Tef,JP-Tmd",
        "README_SHA256 "+BAD_README_SHA,
        "README_LINE_COUNT 75",
        "EXACT_SAME_BYTES_FOR_TEF_AND_TMD_SAVED_METADATA True",
        "README:064 The data are in ASCII format, comma delimited, with first row as header. Missing data are indicated as -9999 and time is expressed in local solar time (without DST).",
    ):
        if phrase not in text:
            raise ValueError("Missing original Stage05N solar-time README proof: "+phrase)
    if len(rows)!=45:
        raise ValueError("Expected exactly 45 Stage05I source HOLD variable records")
    keys=set()
    counts=Counter()
    for rec in rows:
        site=rec["site"]; v=rec["variable"]; stamp=rec["native_start"]
        k=(site,stamp,v)
        if k in keys or site not in EXPECTED_COUNT or v not in UNIT:
            raise ValueError("Duplicate/unexpected site, time or variable: "+repr(k))
        keys.add(k); counts[site]+=1
        if rec["science_status"]!="HOLD_UNAPPROVED_SOURCE_REVIEW" or rec["selected_F_QC_raw"]!="2":
            raise ValueError("Stage05I scientific source HOLD gate failed")
        datetime.strptime(stamp,"%Y%m%d%H%M")
    if dict(counts)!=EXPECTED_COUNT or len({(x[0],x[1]) for x in keys})!=35:
        raise ValueError("Unexpected 45-field, 35-time source scope")

def build(rows):
    mapped=[];pending=[]
    mapped_times=set();pending_times=set()
    for r in rows:
        site=r["site"];native=r["native_start"];v=r["variable"]
        basic={"site":site,"native_start":native,"variable":v,
               "selected_F":r["selected_F_value"],
               "ERA_in_same_release":r["embedded_ERA_value"],
               "raw_F_QC":r["selected_F_QC_raw"],"unit":UNIT[v]}
        if site in VERIFIED:
            dt=datetime.strptime(native,"%Y%m%d%H%M")-timedelta(hours=9)
            mapped.append({**basic,"utc_start":dt.strftime("%Y%m%d%H%M"),
                "utc_end":(dt+timedelta(minutes=30)).strftime("%Y%m%d%H%M"),
                "source_status":"HOLD_INDEPENDENT_ERA_CHECK_NOT_REPAIR_APPROVED"})
            mapped_times.add((site,native))
        else:
            pending.append({**basic,"utc_start":"UNRESOLVED",
                "source_status":"HOLD_LOCAL_SOLAR_VS_STANDARD_TIME_PROVENANCE"})
            pending_times.add((site,native))
    if (len(mapped),len(pending),len(mapped_times),len(pending_times))!=(27,18,21,14):
        raise ValueError("Expected exact 27/18 field and 21/14 unique time splits")
    return (sorted(mapped,key=lambda x:(x["site"],x["native_start"],x["variable"])),
            sorted(pending,key=lambda x:(x["site"],x["native_start"],x["variable"])))

def write_tsv(path,fields,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        writer.writeheader();writer.writerows(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage05l-summary",type=Path)
    p.add_argument("--stage05n-log",type=Path)
    p.add_argument("--stage05i-tsv",type=Path)
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert (datetime.strptime("200508120300","%Y%m%d%H%M")-timedelta(hours=9)).strftime("%Y%m%d%H%M")=="200508111800"
        assert sum(EXPECTED_COUNT.values())==45
        print("STAGE05O SELF-TEST PASS | 3/2 time-provenance gate, UTC arithmetic, NO WRITES")
        return
    if any(x is None for x in (a.stage05l_summary,a.stage05n_log,a.stage05i_tsv,a.output_dir)):
        p.error("Require --stage05l-summary --stage05n-log --stage05i-tsv --output-dir")
    rows=tsv_rows(a.stage05i_tsv)
    verify_inputs(a.stage05l_summary,a.stage05n_log,rows)
    mapped,pending=build(rows)
    out=a.output_dir
    if out.exists():
        p.error("Output already exists; choose a new directory")
    out.mkdir(parents=True)
    m=out/"stage05o_verified3_27_UTC_LOOKUP_HOLD.tsv"
    q=out/"stage05o_unresolved2_18_NATIVE_ONLY_HOLD.tsv"
    s=out/"stage05o_scoped_timebase_summary.json"
    write_tsv(m,MAP_FIELDS,mapped)
    write_tsv(q,HOLD_FIELDS,pending)
    with s.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05O","status":"3_SITE_SCOPED_UTC_ONLY",
          "verified_local_standard_sites":list(VERIFIED),
          "unresolved_original_local_solar_README_sites":list(UNRESOLVED),
          "mapped_field_records":27,"mapped_unique_site_halfhours":21,
          "unresolved_field_records":18,"unresolved_unique_site_halfhours":14,
          "total_field_records":45,"total_unique_site_halfhours":35,
          "independent_ERA5_checked":False,"repair_approved":False,
          "original_source_or_model_modified":False},f,indent=2)
        f.write("\n")
    print("STAGE05O SCOPED READ-ONLY PASS | NO ZIP / NO SLURM / NO REPAIR")
    print("LST_VERIFIED 3 /5 | UTC_LOOKUP 27 FIELDS / 21 SITE-HALFHOURS")
    print("SOLAR_README_CONFLICT 2 /5 | NATIVE_ONLY_HOLD 18 FIELDS / 14 SITE-HALFHOURS")
    print("UTC_TABLE",m)
    print("NATIVE_ONLY_HOLD",q)
    print("SUMMARY",s)
    print("NO AUTOMATIC +9 MAPPING OF JP-Tef/JP-Tmd; NO SCIENTIFIC APPROVAL")

if __name__=="__main__":
    main()

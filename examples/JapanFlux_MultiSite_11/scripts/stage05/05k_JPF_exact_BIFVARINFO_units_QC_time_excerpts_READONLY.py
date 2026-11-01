#!/usr/bin/env python3
"""JapanFlux Stage05K: extract exact JPF BIFVARINFO_HH variable records and site time metadata.

Reads ONLY SMALL METADATA CSV/TXT members of a single site source ZIP.
The nested ZIP is buffered in RAM (bounded); raw meteorological data rows are
NEVER opened. No Slurm, no source writes, no ERA replacement, no model.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

SITES=("JP-Api","JP-Fhk","JP-Fjy","JP-Khw","JP-Spp","JP-Tak","JP-Tef","JP-Tmd","JP-Yms")
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
FOCUS={"TA_F","TA_F_MDS","TA_F_MDS_QC","TA_F_QC","TA_ERA",
       "PA_F","PA_F_QC","PA_F_MDS","PA_ERA",
       "LW_IN_F","LW_IN_F_QC","LW_IN_F_MDS","LW_IN_F_MDS_QC","LW_IN_ERA",
       "VPD_F","VPD_F_QC","VPD_F_MDS","VPD_F_MDS_QC","VPD_ERA"}
TIME=re.compile(r"\b(?:UTC|JST|GMT|time.?zone|local.?standard|daylight|hour.?offset|time.?shift|UTC.?offset|timestamp)\b",re.I)
UNITS=re.compile(r"\b(?:unit|kpa|pascal|deg.?c|w.?m.?2|pressure|time.?zone)\b",re.I)

def small_text(z:zipfile.ZipFile,info:zipfile.ZipInfo,cap:int)->tuple[str,str]:
    if info.file_size>cap:
        raise ValueError(f"Metadata too large: {info.filename}: {info.file_size}")
    with z.open(info) as f:
        data=f.read(cap+1)
    if len(data)>cap:
        raise ValueError("Metadata read cap exceeded")
    return data.decode("utf-8-sig",errors="replace"),hashlib.sha256(data).hexdigest()

def exact_members(z:zipfile.ZipFile, pred)->list[zipfile.ZipInfo]:
    return [i for i in z.infolist() if not i.is_dir() and pred(Path(i.filename).name)]

def variable_groups(content:str)->tuple[list[dict],dict]:
    groups=defaultdict(list)
    header=[]
    for line,row in enumerate(csv.reader(io.StringIO(content)),1):
        if not row:
            continue
        if len(row)<5:
            if len(header)<5: header.append({"line":line,"cells":row[:8]})
            continue
        if row[1].strip().upper()=="GROUP_ID" or row[3].strip().upper() in ("VARIABLE","FIELD"):
            continue
        site,group,kind,key=row[:4]
        value=",".join(row[4:]).strip()
        groups[(site.strip(),group.strip(),kind.strip())].append(
            {"line":line,"key":key.strip(),"value":value})
    out=[]
    found=set()
    for (site,group,kind),records in sorted(groups.items(),
                                             key=lambda kv:(kv[0][1],kv[0][2])):
        hits=sorted({r["value"] for r in records if r["value"] in FOCUS})
        if not hits:
            # Variable labels may be represented as 'VAR_INFO_VARNAME=TA_F'
            # or embedded in a BIFVARINFO key/value string.
            hits=sorted({v for v in FOCUS if any(
                re.search(r"(?<![A-Z0-9_])"+re.escape(v)+r"(?![A-Z0-9_])",
                          r["value"],flags=re.I) for r in records)})
        if not hits:
            continue
        found.update(hits)
        out.append({"site":site,"group_id":group,"group_type":kind,
                    "matching_names":hits,"source_fields":records})
    return out, {"target_variable_count":len(FOCUS),
                 "matched_target_variables":sorted(found),
                 "not_matched":sorted(FOCUS-found),
                 "unparsed_short_rows_preview":header}

def metadata_excerpts(z:zipfile.ZipFile,info:zipfile.ZipInfo,cap:int)->dict:
    content,digest=small_text(z,info,cap)
    matches=[]
    for idx,line in enumerate(content.splitlines(),1):
        if TIME.search(line) or (UNITS.search(line) and
                                  any(term in line.upper() for term in ("PA","TA","LW","SITE"))):
            if len(matches)<90:
                matches.append({"line":idx,"text":line[:600]})
    return {"member":info.filename,"sha256":digest,
            "line_count":len(content.splitlines()),
            "time_unit_hint_count":len(matches),
            "first_90_time_unit_hints":matches}

def inspect(root:Path,site:str,package:str,max_inner:int,max_meta:int)->dict:
    original=root/site/"forcing"/"packages"/(package+".zip")
    if not original.is_file() or original.is_symlink():
        raise ValueError("Missing or symlink source ZIP")
    with zipfile.ZipFile(original) as outer:
        nested=[i for i in outer.infolist()
                if i.filename==package+".zip" and not i.is_dir()]
        if len(nested)!=1:
            raise ValueError("Expected exactly one nested source release")
        if nested[0].file_size>max_inner:
            raise ValueError("Nested source exceeds configured memory limit")
        with io.BytesIO() as buffer:
            with outer.open(nested[0]) as f:
                n=0
                while True:
                    b=f.read(4*1024*1024)
                    if not b:break
                    n+=len(b)
                    if n>max_inner:raise ValueError("Nested data exceeded byte cap")
                    buffer.write(b)
            buffer.seek(0)
            with zipfile.ZipFile(buffer) as inner:
                allnames=[i.filename for i in inner.infolist() if not i.is_dir()]
                varinfos=exact_members(inner,lambda base:
                    "_BIFVARINFO_HH_" in base and base.endswith(".csv"))
                if len(varinfos)!=1:
                    raise ValueError("One and only one JPF BIFVARINFO_HH metadata CSV required")
                content,sha=small_text(inner,varinfos[0],max_meta)
                grouped,detail=variable_groups(content)
                secondary=exact_members(inner,lambda base:
                    ("_FLUXNET_BIF_" in base and base.endswith(".csv"))
                    or base.upper()=="README.TXT"
                    or ("POLICY" in base.upper() and base.lower().endswith(".txt")))
                if len(secondary)>8:
                    raise ValueError("Unexpectedly many metadata files")
                metas=[metadata_excerpts(inner,i,max_meta) for i in secondary]
    return {"stage":"JapanFlux Stage05K",
            "site":site,"status":"READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED",
            "archive":str(original),"source_files_modified":False,
            "meteorological_rows_read":0,"model_inputs_modified":False,
            "BIFVARINFO_HH":{"member":varinfos[0].filename,"sha256":sha,
                             "focus_variable_groups":grouped,
                             "coverage":detail},
            "site_metadata_and_readme":metas,
            "independent_ERA5":"NOT_ACQUIRED_OR_COMPARED",
            "timezone_claim":"UNVERIFIED_ONLY_ORIGINAL_METADATA_EXCERPTS",
            "QC_claim":"VERIFY_PRODUCT_BIFVARINFO_HH_DIRECTLY",
            "original_release_members_count":len(allnames)}

def self_test()->None:
    content=("\n".join([
        "SITE_ID,GROUP_ID,VARIABLE_GROUP,VARIABLE,VALUE",
        "JP-Khw,4,GRP_VAR_INFO,VAR_INFO_VARNAME,PA_F",
        "JP-Khw,4,GRP_VAR_INFO,VAR_INFO_UNIT,kPa",
        'JP-Khw,4,GRP_VAR_INFO,VAR_INFO_DEFINITION,"Consolidated pressure from ERA"',
        "JP-Khw,5,GRP_VAR_INFO,VAR_INFO_VARNAME,PA_F_QC",
        "JP-Khw,5,GRP_VAR_INFO,VAR_INFO_DEFINITION,0 = measured; 1 = fill; 2 = ERA",
    ])+"\n")
    with io.BytesIO() as mem:
        with zipfile.ZipFile(mem,"w") as z:
            z.writestr("JPF_JP-Khw_FLUXNET_BIFVARINFO_HH_2000-2021.csv",content)
            z.writestr("README.txt","Station timestamps local standard time UTC offset +09\n")
        mem.seek(0)
        with zipfile.ZipFile(mem) as z:
            c,h=small_text(z,z.infolist()[0],100000)
            group,detail=variable_groups(c)
            assert len(group)==2 and "PA_F" in detail["matched_target_variables"]
            assert any(r["value"]=="kPa" for r in group[0]["source_fields"])
            assert metadata_excerpts(z,z.infolist()[1],100000)["time_unit_hint_count"]==1
    print("STAGE05K SELF-TEST PASS | BIF group-unit-QC-time evidence parsing, NO SOURCE WRITES")

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--manifest",type=Path)
    p.add_argument("--site",choices=SITES)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--max-nested-mib",type=int,default=256)
    p.add_argument("--max-metadata-mib",type=int,default=4)
    a=p.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.manifest or not a.site:
        p.error("Must supply --manifest and --site")
    if not 64<=a.max_nested_mib<=512 or not 1<=a.max_metadata_mib<=8:
        p.error("Safety limits out of range")
    with a.manifest.open(encoding="utf-8-sig",newline="") as f:
        m=list(csv.DictReader(f,delimiter="\t"))
    d={v["site"]:v for v in m}
    if len(m)!=11 or len(d)!=11 or a.site not in d:
        p.error("Invalid 11-site manifest")
    r=inspect(a.root,a.site,d[a.site]["package"],
              a.max_nested_mib*1024*1024,a.max_metadata_mib*1024*1024)
    print(json.dumps(r,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

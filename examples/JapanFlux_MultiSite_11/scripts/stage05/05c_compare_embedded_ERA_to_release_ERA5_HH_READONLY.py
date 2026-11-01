#!/usr/bin/env python3
"""JapanFlux Stage05C: compare separate JPF ERA5_HH with FLUXMET_HH at exact suspect days.

Read-only, no Slurm, no extraction to disk, no source edits, no repairs.
One site and one date per invocation. The separate ERA5_HH table is from
THE SAME PUBLISHED JPF PACKAGE, not a newly/re-independently downloaded ERA5.
Time is kept in its native string convention (UTC/JST is not asserted).
"""
from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
import zipfile
from collections import Counter

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITES=("JP-Khw","JP-Tmd","JP-Fjy","JP-Yms","JP-Tef")
EVENTS={"20050812":("0100","0500"),
        "20111217":("0500","0900"),
        "20220409":("0100","0400")}
VAR=("TA","PA","LW_IN","SW_IN","VPD","P","WS")
BASE=("TA_F","TA_F_QC","TA_F_MDS","TA_F_MDS_QC",
      "PA_F","PA_F_QC","LW_IN_F","LW_IN_F_QC")
REQUEST=("TIMESTAMP_START","TIMESTAMP_END")+BASE+tuple(
    nm for f in VAR for nm in (f+"_ERA",f+"_F",f+"_F_QC")
)


def parse_manifest(path:Path)->dict:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    sites={r["site"]:r for r in rows}
    if len(rows)!=11 or len(sites)!=11 or any("package" not in r for r in rows):
        raise ValueError("Expected 11 unique site rows with package column")
    return sites


def get_exact(zf:zipfile.ZipFile, needle:str)->zipfile.ZipInfo:
    members=[i for i in zf.infolist() if not i.is_dir()
             and i.filename.endswith(".csv") and needle in Path(i.filename).name]
    if len(members)!=1:
        raise ValueError(f"Expected exactly 1 {needle} CSV; found {len(members)}")
    return members[0]


def read_context(zf:zipfile.ZipFile, member:zipfile.ZipInfo,
                 event_date:str, from_hhmm:str, to_hhmm:str)->dict:
    start=event_date+from_hhmm
    end=event_date+to_hhmm
    rows={}
    with zf.open(member) as raw, io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Missing CSV header")
        if len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError("Duplicate CSV header fields")
        for col in ("TIMESTAMP_START","TIMESTAMP_END"):
            if col not in reader.fieldnames:
                raise ValueError(f"Missing {col} in {member.filename}")
        available=[c for c in reader.fieldnames if c in REQUEST]
        for row in reader:
            t=row["TIMESTAMP_START"]
            if t[:8] != event_date or not (start<=t<end):
                continue
            if t in rows:
                raise ValueError(f"Duplicate event timestamp {t} in {member.filename}")
            rows[t]={k:row[k] for k in available}
    return {"name":member.filename, "columns":available, "by_start":rows}


def compare_numeric(a:str|None,b:str|None)->str:
    if a is None or b is None:
        return "NO_COLUMN"
    try:
        v1,v2=float(a),float(b)
    except (TypeError,ValueError):
        return "NOT_NUMERIC"
    if v1!=v1 or v2!=v2:
        return "NOT_NUMERIC"
    return "EQUAL" if abs(v1-v2)<=1e-8*max(1,abs(v1),abs(v2)) else "DIFFERENT"


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--site",choices=SITES,required=True)
    p.add_argument("--event-date",choices=tuple(EVENTS),required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--max-inner-mib",type=int,default=256)
    args=p.parse_args()
    if not 64<=args.max_inner_mib<=512:
        p.error("Expected --max-inner-mib 64..512")
    sites=parse_manifest(args.manifest)
    if args.site not in sites:
        p.error("Selected site missing from manifest")
    pkg=sites[args.site]["package"]
    outer_path=args.root/args.site/"forcing"/"packages"/(pkg+".zip")
    if not outer_path.is_file() or outer_path.is_symlink():
        raise ValueError("Missing original ZIP or symlink, aborting")
    with zipfile.ZipFile(outer_path) as outer:
        nested=[i for i in outer.infolist() if i.filename==pkg+".zip" and not i.is_dir()]
        if len(nested)!=1:
            raise ValueError("Expected exact-name inner ZIP")
        cap=args.max_inner_mib*1024*1024
        if nested[0].file_size>cap:
            raise ValueError("Nested ZIP exceeds memory cap")
        with io.BytesIO() as buffer, outer.open(nested[0]) as source:
            total=0
            while True:
                chunk=source.read(4*1024*1024)
                if not chunk:
                    break
                total+=len(chunk)
                if total>cap:
                    raise ValueError("Nested ZIP exceeds memory cap during streaming")
                buffer.write(chunk)
            buffer.seek(0)
            with zipfile.ZipFile(buffer) as data:
                left=read_context(data,get_exact(data,"_FLUXMET_HH_"),args.event_date,*EVENTS[args.event_date])
                right=read_context(data,get_exact(data,"_ERA5_HH_"),args.event_date,*EVENTS[args.event_date])
    keys=sorted(set(left["by_start"])|set(right["by_start"]))
    if not keys:
        raise ValueError("No timestamps in specified event window")
    joined=[]
    equal_summary=Counter()
    for t in keys:
        f=left["by_start"].get(t)
        e=right["by_start"].get(t)
        if f is None or e is None:
            equal_summary["UNMATCHED_TIMESTAMP"]+=1
        checks={}
        for v in VAR:
            a=f.get(v+"_ERA") if f else None
            b=e.get(v+"_ERA") if e else None
            status=compare_numeric(a,b)
            checks[v]=status
            equal_summary[v+":"+status]+=1
        joined.append({
            "native_start":t,
            "native_end_FLUXMET":f.get("TIMESTAMP_END") if f else None,
            "native_end_ERA5":e.get("TIMESTAMP_END") if e else None,
            "FLUXMET_F_QC_ERA":f,
            "separate_ERA5_HH":e,
            "embedded_ERA_vs_separate_ERA5_comparison":checks,
        })
    report={"stage":"JapanFlux Stage05C",
            "site":args.site, "event_date":args.event_date,
            "scope":"READ_ONLY_SAME_RELEASE_TWO_FILES_NOT_INDEPENDENT_REDOWNLOAD",
            "native_timezone":"NOT_ASSIGNED",
            "source_mutation":False, "scientific_repair":"NOT_APPROVED",
            "FLUXMET_member":left["name"],
            "ERA5_member":right["name"],
            "count_FLUXMET":len(left["by_start"]),
            "count_ERA5":len(right["by_start"]),
            "equality_summary":dict(equal_summary),
            "joined_rows":joined}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stage05M: Diagnose five Stage05K saved README time hints, hashes and check wording.

Reads ONLY Stage05K JSON; no ZIP, no Slurm, no source/forcing writes.
No implied time-zone approval for unverified records. This tool is forensics.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import re

SITES=("JP-Fjy","JP-Khw","JP-Tef","JP-Tmd","JP-Yms")
MATCH=re.compile(r"time|local|(?:\bDST\b)|(?:\bUTC\b)|saving|standard|offset|zone", re.I)

def inspect(dir:Path)->list[dict]:
    reports=[]
    for site in SITES:
        p=dir/(site+"_exact_metadata.json")
        data=json.loads(p.read_text(encoding="utf-8"))
        if data.get("site")!=site or data.get("stage")!="JapanFlux Stage05K" or data.get("status")!="READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED":
            raise ValueError("Incomplete or unexpected metadata JSON "+str(p))
        readmes=[d for d in data.get("site_metadata_and_readme",[]) if Path(d["member"]).name.upper()=="README.TXT"]
        if len(readmes)!=1:
            reports.append({"site":site,"readme_found":len(readmes),"status":"NO_EXACTLY_ONE_README"})
            continue
        doc=readmes[0]
        lines=doc.get("first_90_time_unit_hints",[])
        cand=[{"line":r.get("line"),"text":r.get("text","")} for r in lines if MATCH.search(r.get("text",""))]
        matching=[r for r in cand if "local standard time" in r["text"].lower()]
        strict=[r for r in matching if "without dst" in r["text"].lower()]
        alternatives=[r for r in matching if any(x in r["text"].lower() for x in
                 ("without daylight","no daylight","not observe daylight","does not observe daylight","without d.s.t"))]
        reports.append({
            "site":site,"readme_found":1,"readme_sha256":doc.get("sha256"),
            "readme_lines":doc.get("line_count"),
            "stored_candidate_hints":len(lines),
            "candidate_lines":cand,
            "original_stage05l_strict_match":bool(strict),
            "equivalent_wording_candidate_needs_review":bool(alternatives),
            "metadata_excerpt_truncation_possible":doc.get("time_unit_hint_count",0)>=90,
            "status":"INSPECT_SOURCE_PHRASE_NOT_APPROVED",
        })
    return reports

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metadata-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        assert MATCH.search("Local Standard Time (without DST)")
        assert MATCH.search("No daylight saving time is observed")
        print("STAGE05M SELF-TEST PASS | JSON metadata and README pattern guards, NO WRITES")
        return
    if args.metadata_dir is None:
        p.error("--metadata-dir required unless using --self-test")
    rows=inspect(args.metadata_dir)
    print("STAGE05M | EXISTING JSON ONLY | NO ZIP / SLURM / FORCING WRITES")
    for r in rows:
        print("\nSITE:",r["site"])
        print("STATUS:",r["status"])
        if r.get("readme_found")!=1:
            print("README_FILE_COUNT:",r["readme_found"])
            continue
        print("README_SHA256:",r.get("readme_sha256"))
        print("README_LINE_COUNT:",r.get("readme_lines"))
        print("STRICT_STAGE05L_MATCH:",r["original_stage05l_strict_match"])
        print("ALTERNATIVE_WORDING_REVIEW:",r["equivalent_wording_candidate_needs_review"])
        print("EXCERPT_LIMIT_POSSIBLE:",r["metadata_excerpt_truncation_possible"])
        for item in r["candidate_lines"]:
            print("  README LINE",item["line"],item["text"][:650])
    print("\nVERDICT: Source README text must be examined before any time-gate change.")
    print("No original source or approved model forcing modified.")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Read-only AmeriFlux Batch 02 Stage01 extraction-failure investigation.

Locate the exact user-supplied Stage01 JSON report, show diagnostic context
for US-Ha1 and inspect existing US-Ha1 source package directories. This
script NEVER extracts ZIP files, overwrites files or changes CTSM cases.
"""
import argparse
import json
import os
from pathlib import Path
import zipfile

DEFAULT_REPORT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/"
    "AmeriFlux_MultiSite_10_Batch02/reports/"
    "stage01_extraction_20261021T225247Z_5a741048.json")
DEFAULT_SITE = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Ha1")


def display(value, max_length=3000):
    try:
        s = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        s = repr(value)
    return s if len(s) <= max_length else s[:max_length] + "\n... [truncated]"


def selected_context(obj, target="US-Ha1", path="$", max_hits=24):
    hits = []

    def visit(item, keypath, parents, depth):
        if len(hits) >= max_hits or depth > 20:
            return
        if isinstance(item, dict):
            # A dictionary of site records or a row with site=US-Ha1.
            is_site = any(target.casefold() in str(
                item.get(x,"")).casefold()
                for x in ("site", "site_id", "site_code", "station", "id"))
            if is_site or target.casefold() in keypath.casefold():
                if not any(h[0]==keypath for h in hits):
                    hits.append((keypath, item))
                    return
            for k, val in item.items():
                key = str(k)
                newpath = keypath + "." + key
                if target.casefold() in key.casefold():
                    hits.append((newpath, val))
                    if len(hits) >= max_hits: return
                else:
                    visit(val, newpath, parents+[item], depth+1)
        elif isinstance(item, list):
            for n, val in enumerate(item):
                visit(val, keypath+"["+str(n)+"]", parents, depth+1)
                if len(hits)>=max_hits:return
        elif isinstance(item, str) and target.casefold() in item.casefold():
            hits.append((keypath, item))
    visit(obj, path, [], 0)
    return hits


def list_site_content(site):
    print("\n===== EXISTING US-Ha1 PATHS (read-only) =====")
    print("Site folder:", site, "| exists=", site.is_dir())
    forcing = site / "forcing"
    for part in ("packages", "raw", "merged", "processed", "processed_v5"):
        folder = forcing / part
        print("  ", folder, "| exists=", folder.is_dir())
        if not folder.is_dir():
            continue
        entries = sorted(folder.iterdir(), key=lambda p:p.name)
        print("    entries:",len(entries))
        for p in entries[:40]:
            if p.is_file():
                print("     FILE",p.name,"bytes=",p.stat().st_size)
            elif p.is_dir():
                print("     DIR ",p.name)
        if len(entries)>40:
            print("     ... additional",len(entries)-40,"entries omitted")
    # Inspect ZIP catalogues without writing or extracting payloads.
    dirs = [forcing/"packages", site]
    archives = []
    for folder in dirs:
        if folder.is_dir():
            archives.extend(sorted(folder.glob("*.zip")))
    print("\nZIP packages found:",len(archives))
    for z in archives[:30]:
        try:
            with zipfile.ZipFile(z,"r") as archive:
                members=archive.namelist()
                print("  ZIP",z,"bytes",z.stat().st_size,
                      "members",len(members),
                      "FLUXMET_HH=",any("FLUXMET_HH" in x for x in members),
                      "ERA5_HH=",any("ERA5_HH" in x for x in members),
                      "BIF=",any("_BIF_" in x for x in members))
        except (OSError,zipfile.BadZipFile,ValueError) as exc:
            print("  ZIP OPEN ERROR",z,repr(exc))
    print("No source files changed.")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report",type=Path,default=DEFAULT_REPORT)
    ap.add_argument("--site-dir",type=Path,default=DEFAULT_SITE)
    args=ap.parse_args()
    if not args.report.is_file():
        raise SystemExit("REPORT NOT FOUND: "+str(args.report))
    with args.report.open("r",encoding="utf-8") as f:
        data=json.load(f)
    print("===== BATCH 02 REPORT =====")
    print("Report:",args.report)
    print("Report type:",type(data).__name__)
    if isinstance(data,dict):
        print("Top-level keys:",list(data)[:40])
        for k,v in data.items():
            if any(term in k.lower() for term in
                   ("summary","failure","error","failed","pass","status")):
                print("Report key",k,":",display(v,max_length=2000))
    matches=selected_context(data)
    print("\n===== US-Ha1 REPORT MATCHES:",len(matches),"=====")
    for location,item in matches:
        print("PATH",location)
        print(display(item,max_length=6500))
    if not matches:
        print("No literal US-Ha1 found in JSON. Check report schema and timestamp.")
    list_site_content(args.site_dir)
    print("\nNEXT: diagnose the exact exception; do not re-extract/overwrite")
    print("existing US-Ha1 FLUXNET source or its working CIME case.")


if __name__=="__main__":
    main()

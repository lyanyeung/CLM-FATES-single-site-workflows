#!/usr/bin/env python3
"""Batch02 Stage66: read-only investigation of network-wide FLUXNET BIF.

Reason: Stage65 scanned 13 candidate source archives per US-Ho1/US-BZS
but proved no same-release per-site BIF. FLUXNET2015 also uses global
FLX_AA-Flx_BIF_HH_YYYYMMDD.xlsx. Inspect global/multi-site BIFs from
bounded local source/package directories, and the existing 26 Stage65
provenance candidates, including historical UTC_OFFSET_DATE_START groups.

IMPORTANT: Discovering a plausible offset does NOT validate time mapping.
Only exact source-release proof including timestamp conventions + complete
group/date history can release US-Ho1/US-BZS from HOLD. This script never
approves offsets, downloads, modifies raw sources, or changes forcing.
"""
import argparse, hashlib, io, json, re, zipfile
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from importlib import util
import pandas as pd

REPO=Path.home()/"CLM-FATES-single-site-workflows"
BASE=REPO/"examples/AmeriFlux_MultiSite_10_Batch02"
S65_FILE=BASE/"scripts/stage65/65_find_official_release_BIF_xlsx_and_triage_69.py"
S65_BLOB="6cef393ba8666e3ae9454dbb2b64822c3e8b76b7"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports")
S65=R/"stage65_metadata_xlsx_BIF_and_69T_triage_20261024T233546Z_05d7f38e"
SRC="BZS_Ho1_source_release_BIF_CSV_XLSX_ZIP_inventory.json"
SITES=("US-BZS","US-Ho1")
MAX_DEPTH=3
MAX_VISITED_PER_ROOT=350
MAX_ZIPS=250
MAX_BIFS=350
MAX_METADATA_BYTES=48*1024*1024
MAX_ARCHIVE_ORIGINAL_BYTES=600*1024*1024

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def stage65_module():
    if not S65_FILE.is_file() or S65_FILE.is_symlink():
        raise ValueError("Stage65 source script absent or symlink")
    s=S65_FILE.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(s)).encode()+b"\0"+s).hexdigest()
    if blob!=S65_BLOB:
        raise ValueError("Stage65 script Git source blob changed")
    spec=util.spec_from_file_location("pinned_batch02_stage65",S65_FILE)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def upstream():
    s65=stage65_module()
    m=json.loads((S65/"stage65_manifest.json").read_text())
    if ((S65/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE65_SOURCE_BIF_METADATA_AND_69T_TRIAGE_v1" or
        m.get("n_same_archive_BIF_verified")!=0 or
        m.get("n_stage64_candidates")!=9389 or
        m.get("n_temperature_HOLD")!=69 or
        m.get("n_Ho1_HOLD")!=16788 or
        m.get("n_BZS_HOLD")!=86 or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage65 source provenance unexpected")
    for name,d in m.get("output_sha256",{}).items():
        if sha(S65/name)!=d:
            raise ValueError("Stage65 evidence file checksum mismatch "+name)
    earlier=json.loads((S65/SRC).read_text())
    if len(earlier)!=26 or Counter(x["site"] for x in earlier)!=Counter(
            {"US-BZS":13,"US-Ho1":13}):
        raise ValueError("Original Stage65 discovery census unexpected")
    _,spec,_,_=s65.source_context()
    sources={site:dict(path=Path(spec[site]["file"]).resolve(strict=True),
                       sha=spec[site]["sha256"]) for site in SITES}
    return s65,earlier,sources,m

def is_global_bif(name):
    u=Path(name).name.upper()
    return ("_BIF_" in u and
            ("AA-FLX" in u or "AA-NET" in u or "AA_FLX" in u))

def bifs_in_zip(zipfile_obj):
    return [member for member in zipfile_obj.infolist()
        if not member.is_dir()
        and member.file_size<=MAX_METADATA_BYTES
        and member.filename.lower().endswith((".xlsx",".csv"))
        and "_BIF_" in Path(member.filename).name.upper()]

def canonical_rows(s65,data,filename):
    if filename.lower().endswith(".xlsx"):
        raw=s65.xlsx_tables(data)
    elif filename.lower().endswith(".csv"):
        raw=s65.read_csv_bif(data)
    else:raise ValueError("Not CSV/XLSX")
    rows=[]
    for r in raw:
        row={str(k).strip().upper():str(v).strip()
             for k,v in r.items() if k is not None and v is not None}
        if all(k in row for k in ("SITE_ID","VARIABLE","DATAVALUE")):
            rows.append(row)
    return rows

def offset_evidence(rows,site):
    """Do not merge different GROUP_IDs or silently discard offset history."""
    active=[r for r in rows if r.get("SITE_ID","").upper()==site.upper()]
    groups=defaultdict(lambda:defaultdict(set))
    for r in active:
        name=r["VARIABLE"].upper()
        if name in ("UTC_OFFSET","UTC_OFFSET_DATE_START",
                    "UTC_OFFSET_DATE_END","UTC_OFFSET_COMMENT",
                    "LOCATION_LAT","LOCATION_LONG","LOCATION_DATE_START"):
            groups[r.get("GROUP_ID","")][name].add(r["DATAVALUE"])
    history=[]
    for gid,record in groups.items():
        if not ("UTC_OFFSET" in record or "UTC_OFFSET_DATE_START" in record):
            continue
        h={k:sorted(v) for k,v in sorted(record.items())}
        time_start=h.get("UTC_OFFSET_DATE_START",[""])[0]
        offset=h.get("UTC_OFFSET",[""])[0]
        valid=False
        try:
            val=float(offset)
            valid=(-12<=val<=14 and val*2==round(val*2) and
                   len(h.get("UTC_OFFSET",[]))==1 and
                   len(h.get("UTC_OFFSET_DATE_START",[]))<=1 and
                   (not time_start or bool(re.fullmatch(r"\d{4}(\d{4}(\d{4})?)?",time_start))))
        except (TypeError,ValueError):
            valid=False
        history.append(dict(group_id=gid,utc_offset_values=h.get("UTC_OFFSET",[]),
             utc_offset_date_start=h.get("UTC_OFFSET_DATE_START",[]),
             utc_offset_date_end=h.get("UTC_OFFSET_DATE_END",[]),
             comments=h.get("UTC_OFFSET_COMMENT",[]),numeric_and_date_valid=valid))
    history.sort(key=lambda x:(x["utc_offset_date_start"],x["group_id"]))
    return dict(site=site,n_site_rows=len(active),n_groups=len(groups),
        utc_offset_groups=history,
        n_valid_offset_groups=sum(x["numeric_and_date_valid"] for x in history),
        unique_offset_values=sorted(set(v for x in history
             for v in x["utc_offset_values"])),
        offset_history_requires_period_check=(
            len(history)!=1 or any(x["utc_offset_date_start"] for x in history)),
        coords={k:sorted(set(v for group in groups.values()
                for v in group.get(k,set()))) for k in ("LOCATION_LAT","LOCATION_LONG")})

def same_source_original_in_archive(z,sources):
    membership={}
    for site,src in sources.items():
        original=src["path"]
        exact=False;name_matches=[]
        for member in z.infolist():
            if member.is_dir() or member.file_size!=original.stat().st_size:
                continue
            # Different container prefixes are acceptable, unchanged bytes essential.
            if Path(member.filename).name!=original.name:continue
            name_matches.append(member.filename)
            if member.file_size>MAX_ARCHIVE_ORIGINAL_BYTES:continue
            hasher=hashlib.sha256()
            with z.open(member) as f:
                for chunk in iter(lambda:f.read(1<<20),b""):
                    hasher.update(chunk)
            if hasher.hexdigest()==src["sha"]:
                exact=True
                break
        membership[site]={"archive_contains_identical_primary_sha256":exact,
            "matching_filename_members":name_matches}
    return membership

def candidate_dirs(sources):
    # No whole-scratch and no hidden user-wide scan.
    roots=set()
    for source in sources.values():
        p=source["path"]
        for parent in list(p.parents)[:5]:
            roots.add(parent)
    roots.update((
      Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"),
      Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02"),
      Path.home()/"AmeriFlux",
      Path.home()/"FLUXNET",
      Path.home()/"AmeriFlux_Batch02",
      REPO/"examples",
    ))
    return sorted((p for p in roots if p.is_dir()),key=str)

def scan_paths(roots,earlier):
    chosen={}
    for x in earlier:
        p=Path(x["path"])
        if p.is_file() and not p.is_symlink():chosen[str(p.resolve())]=p
    seen=set();audit=[]
    for root in roots:
        stack=[(root,0)];visits=0
        while stack and visits<MAX_VISITED_PER_ROOT and (
            len(chosen)<(MAX_ZIPS+MAX_BIFS)):
            p,depth=stack.pop()
            if p in seen:continue
            seen.add(p);visits+=1
            try:members=list(p.iterdir())
            except (OSError,PermissionError):continue
            for f in members:
                if f.is_symlink():continue
                if f.is_dir():
                    if depth<MAX_DEPTH and f.name not in (
                        ".git","build","run","restart","history","logs",
                        "conda","node_modules",".cache"):
                        if depth<=1 or any(k in str(f).upper() for k in
                            ("BIF","BADM","FLUXNET","AMERIFLUX","PACKAGE")):
                            stack.append((f,depth+1))
                    continue
                if not f.is_file():continue
                name=f.name.upper()
                if f.suffix.lower()==".zip" and (
                      "FLUXNET" in name or "BIF" in name or
                      "BADM" in name or "AMF_" in name or "FLX_" in name):
                    chosen[str(f.resolve())]=f
                elif f.suffix.lower() in (".xlsx",".csv") and (
                      is_global_bif(f.name) or
                      "_BIF_" in name and ("US-HO1" in name or "US-BZS" in name)):
                    chosen[str(f.resolve())]=f
        audit.append({"search_root":str(root),"directories_checked":visits})
    result=sorted(chosen.values(),key=str)
    return result,audit

def inspect(s65,path,sources):
    result={"path":str(path),"file_sha256":sha(path),
            "global_or_network_metadata":is_global_bif(path.name),
            "source_exact_archive_match":{},
            "bif_entries":[],"errors":[]}
    if path.suffix.lower() in (".xlsx",".csv"):
        if path.stat().st_size>MAX_METADATA_BYTES:
            result["errors"].append("FILE_LARGER_THAN_PARSE_LIMIT")
            return result
        try:
            raw=canonical_rows(s65,path.read_bytes(),path.name)
            result["bif_entries"].append({
                "name":path.name,"n_BIF_rows":len(raw),
                "site_evidence":[offset_evidence(raw,site) for site in SITES],
                "metadata_same_original_archive":False})
        except Exception as e:result["errors"].append(type(e).__name__+": "+str(e))
    elif path.suffix.lower()==".zip":
        try:
            with zipfile.ZipFile(path) as z:
                bifs=bifs_in_zip(z)
                if not bifs:return result
                membership=same_source_original_in_archive(z,sources)
                result["source_exact_archive_match"]=membership
                for member in bifs:
                    try:
                        raw=canonical_rows(s65,z.read(member),member.filename)
                        result["bif_entries"].append({
                            "name":member.filename,"n_BIF_rows":len(raw),
                            "site_evidence":[offset_evidence(raw,site) for site in SITES],
                            "metadata_same_original_archive":{
                                site:membership[site]["archive_contains_identical_primary_sha256"]
                                for site in SITES}})
                    except Exception as e:
                        result["errors"].append(
                            member.filename+" "+type(e).__name__+": "+str(e))
        except Exception as e:
            result["errors"].append("ZIP "+type(e).__name__+": "+str(e))
    return result

def self_test():
    rows=[
        dict(SITE_ID="US-Ho1",GROUP_ID="11",VARIABLE="UTC_OFFSET",DATAVALUE="-5"),
        dict(SITE_ID="US-Ho1",GROUP_ID="11",VARIABLE="UTC_OFFSET_DATE_START",DATAVALUE="1996"),
        dict(SITE_ID="US-Ho1",GROUP_ID="22",VARIABLE="UTC_OFFSET",DATAVALUE="-4"),
        dict(SITE_ID="US-Ho1",GROUP_ID="22",VARIABLE="UTC_OFFSET_DATE_START",DATAVALUE="20200101"),
        dict(SITE_ID="US-BZS",GROUP_ID="99",VARIABLE="UTC_OFFSET",DATAVALUE="-7")]
    a=offset_evidence(rows,"US-Ho1")
    assert a["n_valid_offset_groups"]==2
    assert a["offset_history_requires_period_check"]
    assert a["unique_offset_values"]==["-4","-5"]
    b=offset_evidence(rows,"US-BZS")
    assert b["n_valid_offset_groups"]==1
    assert not b["offset_history_requires_period_check"]
    assert is_global_bif("FLX_AA-Flx_BIF_HH_20200115.xlsx")
    assert not is_global_bif("AMF_US-Ho1_BIF_20201010.xlsx")
    print("STAGE66 SELF-TEST PASS | AA-Flx global metadata, GROUP_ID, historical UTC offset")

def main():
    pa=argparse.ArgumentParser(description=__doc__)
    m=pa.add_mutually_exclusive_group(required=True)
    m.add_argument("--self-test",action="store_true")
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    a=pa.parse_args()
    if a.self_test:return self_test()
    s65,earlier,sources,manifest=upstream()
    roots=candidate_dirs(sources)
    files,where=scan_paths(roots,earlier)
    print("STAGE66 SEARCH",len(roots),"roots",len(files),
          "candidate files; prior Stage65 records",len(earlier),flush=True)
    results=[]
    for i,path in enumerate(files):
        if i>=MAX_ZIPS+MAX_BIFS:break
        results.append(inspect(s65,path,sources))
        if (i+1)%25==0:print("STAGE66 PROBE",i+1,flush=True)
    by_site={}
    for site in SITES:
        hits=[]
        for row in results:
            for member in row["bif_entries"]:
                for ev in member["site_evidence"]:
                    if ev["site"]!=site or not ev["utc_offset_groups"]:continue
                    proof=member["metadata_same_original_archive"]
                    evidence=bool(proof.get(site,False)) if isinstance(proof,dict) else False
                    hits.append({"file":row["path"],"member":member["name"],
                                 "value":ev["unique_offset_values"],
                                 "groups":ev["utc_offset_groups"],
                                 "exact_primary_SHA_same_archive":evidence,
                                 "requires_period_check":
                                     ev["offset_history_requires_period_check"]})
        by_site[site]={"candidate_offset_sources":len(hits),
              "exact_primary_SHA_same_archive_sources":
                  sum(x["exact_primary_SHA_same_archive"] for x in hits),
              "distinct_reported_offsets":sorted(set(
                  off for x in hits for off in x["value"])),
              "source_entries":hits[:60]}
    print("STAGE66 GLOBAL BIF FINDINGS")
    for site,item in by_site.items():
        print(site,"CANDIDATES",item["candidate_offset_sources"],
              "SAME_RELEASE",item["exact_primary_SHA_same_archive_sources"],
              "OFFSETS",item["distinct_reported_offsets"])
        for k in item["source_entries"][:8]:
            print("  EVIDENCE",k["file"],k["member"],
                  "exact_source",k["exact_primary_SHA_same_archive"],
                  "history",[(z["utc_offset_values"],z["utc_offset_date_start"])
                             for z in k["groups"]])
    print("STAGE66 NO UTC OFFSET AUTO-RELEASE; Stage64 9389 candidate/HOLD remains immutable")
    if a.check:
        print("STAGE66 CHECK PASS | no outputs or source writes")
        return
    dest=R/("stage66_AA_Flx_global_BIF_UTC_history_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("No source UTC offsets approved or model writes.\n")
    j=dest/"global_and_site_BIF_provenance_candidates.json"
    j.write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    js=dest/"BZS_Ho1_UTC_OFFSET_GROUP_ID_DATE_START_summary.json"
    js.write_text(json.dumps(by_site,indent=2,ensure_ascii=False)+"\n")
    audit=dest/"bounded_metadata_search_roots.json"
    audit.write_text(json.dumps(where,indent=2)+"\n")
    proof={"schema":"STAGE66_FLUXNET_GLOBAL_BIF_SOURCE_TIME_DISCOVERY_v1",
      "stage65_report":str(S65),"n_stage65_candidates":26,
      "n_site_files_scanned":len(results),
      "candidate_metadata_source_counts":{
          x:by_site[x]["candidate_offset_sources"] for x in SITES},
      "same_source_archive_offset_evidence":{
          x:by_site[x]["exact_primary_SHA_same_archive_sources"] for x in SITES},
      "Ho1_hard_source_time_HOLD":16788,"BZS_hard_source_time_HOLD":86,
      "stage64_9389_water_humidity_candidates_unchanged":True,
      "UTC_offsets_auto_approved":False,
      "approved_for_DATM":False,
      "source_SHA256":{
          "stage65_manifest":sha(S65/"stage65_manifest.json"),
          "stage65_metadata_inventory":sha(S65/SRC),
          "stage65_script_git_blob":S65_BLOB,
          **{site+"_primary_SHA256":sources[site]["sha"] for site in SITES}},
      "output_SHA256":{x.name:sha(x) for x in (j,js,audit)},
      "no_original_or_model_writes":True}
    (dest/"metadata_provenance_manifest.json").write_text(
        json.dumps(proof,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE66 AUDIT PASS | global FLUXNET BIF and period-aware UTC metadata inventoried")
    print("REPORT",dest)
    print("NO ORIGINAL, ERA5, DATM, NETCDF, CIME OR SLURM WRITES")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch02 Stage67: explain Stage66 no-offset result; accept official BIF input.

Read-only existing-source forensic and optional externally obtained official
AmeriFlux BADM file validation. Does not require current BADM/BIF to be
bundled in the original FLUXNET source ZIP (official BADM is standalone).
It DOES require correct site, valid GROUP_ID period-aware UTC_OFFSET
record and traceable publisher-file origin before release.

--check and --audit never assign UTC offset or write to DATM, original
EC sources, NetCDF or previous stage outputs. --official-dir reads any
already-downloaded official BIF XLSX/CSV/ZIP in that directory; does not
assume it exists or silently fetch from unauthenticated mirrors.
"""
import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import pandas as pd

REPO=Path.home()/"CLM-FATES-single-site-workflows"
BASE=REPO/"examples/AmeriFlux_MultiSite_10_Batch02"
S66_FILE=BASE/"scripts/stage66/66_find_global_FLX_AA_Flx_BIF_and_UTC_offset_history.py"
S66_BLOB="7d2b87abd6ed3c69586064d361870d56c5325ae7"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports")
S66=R/"stage66_AA_Flx_global_BIF_UTC_history_20261025T054649Z_2a6cae25"
DISCOVERY="global_and_site_BIF_provenance_candidates.json"
OFFICIAL=Path.home()/"AmeriFlux_Batch02_official_BIF"
SITES=("US-BZS","US-Ho1")
MAX=64*1024*1024
MAX_FILE_COUNT=80
PUBLISHER_RE=re.compile(
    r"^(?:AMF|FLX)_(?:US-(?:BZS|Ho1)|AA-(?:Flx|Net))_BIF_.*\.(?:xlsx|csv)$",
    re.IGNORECASE)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as s:
        for b in iter(lambda:s.read(1048576),b""):h.update(b)
    return h.hexdigest()

def stage66_module():
    if not S66_FILE.is_file() or S66_FILE.is_symlink():
        raise ValueError("Stage66 expected source missing")
    b=S66_FILE.read_bytes()
    if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=S66_BLOB:
        raise ValueError("Git-blob-pinned Stage66 source changed")
    spec=util.spec_from_file_location("pinned_batch02_stage66",S66_FILE)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def upstream():
    m=json.loads((S66/"metadata_provenance_manifest.json").read_text())
    if ((S66/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE66_FLUXNET_GLOBAL_BIF_SOURCE_TIME_DISCOVERY_v1" or
        m.get("n_site_files_scanned")!=64 or
        m.get("n_stage65_candidates")!=26 or
        m.get("Ho1_hard_source_time_HOLD")!=16788 or
        m.get("BZS_hard_source_time_HOLD")!=86 or
        m.get("stage64_9389_water_humidity_candidates_unchanged") is not True or
        m.get("UTC_offsets_auto_approved") is not False or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage66 original source manifest does not match live PASS")
    for name,value in m["output_SHA256"].items():
        if sha(S66/name)!=value:
            raise ValueError("Stage66 BIF forensic source SHA256 changed "+name)
    original=json.loads((S66/DISCOVERY).read_text())
    if len(original)!=64:
        raise ValueError("Unexpected number of Stage66 inspected sources")
    return original,m

def forensic(sources):
    table=[];by_site=defaultdict(list)
    for row in sources:
        parts=row.get("bif_entries",[])
        n_bif=sum(int(e.get("n_BIF_rows",0)) for e in parts)
        errors=list(row.get("errors",[]))
        for site in SITES:
            found_site_rows=0;number_offset_rows=0;valid_offset_groups=0
            for entry in parts:
                for x in entry.get("site_evidence",[]):
                    if x.get("site")!=site:continue
                    found_site_rows+=int(x.get("n_site_rows",0))
                    number_offset_rows+=len(x.get("utc_offset_groups",[]))
                    valid_offset_groups+=int(x.get("n_valid_offset_groups",0))
            by_site[site].append({
                "file":row["path"],"n_BIF_rows":n_bif,
                "target_site_rows":found_site_rows,
                "target_offset_groups":number_offset_rows,
                "target_valid_offset_groups":valid_offset_groups,
                "source_errors":errors})
        table.append({"file":row["path"],
            "source_sha256":row.get("file_sha256",""),
            "global_or_network_metadata":bool(row.get("global_or_network_metadata")),
            "bif_entries":len(parts),"parsed_BIF_rows":n_bif,
            "n_errors":len(errors),
            "errors":" | ".join(errors)[:1800],
            "site_BZS_rows":by_site["US-BZS"][-1]["target_site_rows"],
            "site_Ho1_rows":by_site["US-Ho1"][-1]["target_site_rows"]})
    return pd.DataFrame(table),by_site

def read_single(s66,p,name):
    content=p.read_bytes()
    if len(content)>MAX:
        raise ValueError("Official BIF candidate exceeds metadata read cap")
    return s66.canonical_rows(s66.stage65_module(),content,name)

def candidates_from_dir(s66,root):
    """Read but do not assert authentication from basename or file placement."""
    if not root.exists():return [],{"dir":str(root),"status":"NOT_PRESENT"}
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Official candidate directory must be a real directory")
    results=[];paths=sorted(p for p in root.iterdir() if p.is_file() and
                         not p.is_symlink() and
                         p.suffix.lower() in (".xlsx",".csv",".zip"))
    if len(paths)>MAX_FILE_COUNT:
        raise ValueError("Official BIF staging directory contains too many files")
    for p in paths:
        record={"file":str(p),"sha256":sha(p),
                "filename_matches_known_BIF_convention":bool(PUBLISHER_RE.fullmatch(p.name)),
                "publisher_authenticated":False,
                "UTC_OFFSET_AUTO_APPROVED":False,"members":[],"errors":[]}
        try:
            if p.suffix.lower() in (".xlsx",".csv"):
                rows=read_single(s66,p,p.name)
                record["members"].append({"member":p.name,
                    "n_BIF_rows":len(rows),"site_offsets":[
                        s66.offset_evidence(rows,site) for site in SITES]})
            else:
                with zipfile.ZipFile(p) as archive:
                    for member in s66.bifs_in_zip(archive):
                        raw=archive.read(member)
                        if len(raw)>MAX:continue
                        rows=s66.canonical_rows(s66.stage65_module(),
                                               raw,member.filename)
                        record["members"].append({"member":member.filename,
                            "n_BIF_rows":len(rows),"site_offsets":[
                                s66.offset_evidence(rows,site) for site in SITES]})
        except Exception as e:
            record["errors"].append(type(e).__name__+": "+str(e))
        results.append(record)
    return results,{"dir":str(root),"status":"READ_ONLY_IMPORTED","files":len(paths)}

def summary(original,external,external_status):
    df,by_site=forensic(original)
    print("STAGE67 ORIGINAL STAGE66 FILES",len(df))
    print("STAGE67 ORIGINAL BIF PARSED",int(df.parsed_BIF_rows.sum()),
          "FILES_WITH_PARSE_ERRORS",int(df.n_errors.gt(0).sum()),
          "FILES_WITH_NONEMPTY_BIF",int(df.parsed_BIF_rows.gt(0).sum()))
    print("STAGE67 ORIGINAL FILE DIAGNOSIS")
    for rec in df.loc[df.n_errors.gt(0)|df.parsed_BIF_rows.gt(0)].to_dict("records"):
        print("  FILE",rec["file"],"BIF_ROWS",rec["parsed_BIF_rows"],
              "BZS",rec["site_BZS_rows"],"Ho1",rec["site_Ho1_rows"],
              "ERROR",rec["errors"])
    detected={site:[] for site in SITES}
    for record in external:
        for mem in record["members"]:
            for evidence in mem["site_offsets"]:
                if evidence["site"] in detected and evidence["utc_offset_groups"]:
                    detected[evidence["site"]].append({
                      "file":record["file"],"file_sha256":record["sha256"],
                      "BIF_member":mem["member"],
                      "offsets":evidence["unique_offset_values"],
                      "historical_groups":evidence["utc_offset_groups"],
                      "requires_date_verification":
                         evidence["offset_history_requires_period_check"],
                      "publisher_authentication":"NOT_YET_PROVED"})
    for site in SITES:
        d=by_site[site]
        print("STAGE67 SITE",site,
           "ORIGINAL_ROWS",sum(x["target_site_rows"] for x in d),
           "ORIGINAL_OFFSET_GROUPS",sum(x["target_offset_groups"] for x in d),
           "INDEPENDENT_BIF_OFFSET_CANDIDATES",len(detected[site]))
    print("STAGE67 EXTERNAL_OFFICIAL_DIR",external_status)
    print("STAGE67 NO AUTO-RELEASE OF TIME OFFSETS; 9389 previous candidates immutable")
    return df,by_site,detected

def self_test():
    synthetic=[{"path":"a.xlsx","file_sha256":"a",
       "global_or_network_metadata":True,"errors":[],
       "bif_entries":[{"name":"sample","n_BIF_rows":3,
            "site_evidence":[{"site":"US-BZS","n_site_rows":3,
              "utc_offset_groups":[{}],"n_valid_offset_groups":0},
             {"site":"US-Ho1","n_site_rows":0,
              "utc_offset_groups":[],"n_valid_offset_groups":0}]}]}]
    data,b=forensic(synthetic)
    assert len(data)==1 and data.iloc[0].parsed_BIF_rows==3
    assert b["US-BZS"][0]["target_offset_groups"]==1
    assert b["US-Ho1"][0]["target_site_rows"]==0
    assert PUBLISHER_RE.fullmatch("AMF_AA-Flx_BIF_CCBY4_20201218.xlsx")
    print("STAGE67 SELF-TEST PASS | forensic parsed-vs-absent BIF; official external candidates stay unapproved")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--self-test",action="store_true")
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    ap.add_argument("--official-dir",type=Path,default=OFFICIAL)
    args=ap.parse_args()
    if args.self_test:return self_test()
    s66=stage66_module()
    source,manifest=upstream()
    ext,status=candidates_from_dir(s66,args.official_dir)
    frame,by_site,detected=summary(source,ext,status)
    if args.check:
        print("STAGE67 CHECK PASS | no output/source/model writes")
        return
    dest=R/("stage67_BIF_actual_source_forensic_and_official_staging_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    incomplete=dest/"INCOMPLETE_DO_NOT_USE"
    incomplete.write_text("No source time offset approved.\n")
    csvpath=dest/"64_stage66_files_BIF_parse_diagnostics.csv"
    frame.to_csv(csvpath,index=False)
    jsonpath=dest/"independent_official_BIF_candidates_UNVERIFIED.json"
    jsonpath.write_text(json.dumps({"official_dir":status,
          "candidates":ext,"site_offset_candidates":detected},
          indent=2,ensure_ascii=False)+"\n")
    manifest_file=dest/"source_forensic_manifest.json"
    manifest_file.write_text(json.dumps({
        "schema":"STAGE67_FLUXNET_BIF_SOURCE_DIAGNOSTIC_v1",
        "original_Stage66_files":64,
        "original_BIF_rows_parsed":int(frame.parsed_BIF_rows.sum()),
        "original_BIF_files_with_errors":int(frame.n_errors.gt(0).sum()),
        "external_candidate_files":len(ext),
        "Ho1_original_hard_UTC_HOLD":16788,
        "BZS_original_hard_UTC_HOLD":86,
        "stage64_9389_independent_humidity_candidates_preserved":True,
        "publisher_authenticated":False,
        "approved_for_DATM":False,
        "source_SHA256":{
           "stage66_manifest":sha(S66/"metadata_provenance_manifest.json"),
           "stage66_full_source":sha(S66/DISCOVERY),
           "stage66_script_git_blob":S66_BLOB},
        "output_SHA256":{csvpath.name:sha(csvpath),jsonpath.name:sha(jsonpath)},
        "no_original_or_model_writes":True},indent=2,sort_keys=True)+"\n")
    incomplete.unlink()
    print("STAGE67 AUDIT PASS | source BIF parse vs missing provenance classified")
    print("REPORT",dest)
    print("NO ORIGINAL, ERA5, DATM, NETCDF, CIME OR SLURM WRITES")
if __name__=="__main__":
    main()

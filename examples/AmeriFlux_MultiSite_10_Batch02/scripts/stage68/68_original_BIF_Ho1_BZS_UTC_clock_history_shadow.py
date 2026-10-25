#!/usr/bin/env python3
"""Stage68 - source-check official site BIF offsets and shadow local->UTC.

Uses extracted evidence from two original AmeriFlux BIF XLSX uploads:
US-Ho1 UTC-5; US-BZS UTC-9, with original XLSX SHA256 provenance.

Important: BADM XLSX contains one reported offset per site but *does not*
include UTC_OFFSET_DATE_START. That is a usable published site-clock
candidate, NOT proof the offset held throughout 1996-2023 / 2010-2024.
The source FLUXNET product version and the BIF's BASE DOI are different
product types. Never demand equal versions, but independently check
source timestamp convention and historical date coverage before any
final ERA5 replacement. This script is READ ONLY except for its
isolated SHA256-linked report. No DATM/forcing/source modifications.
"""
import argparse, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from uuid import uuid4
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
R=ROOT/"reports"
S64=R/"stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94"
S67=R/"stage67_BIF_actual_source_forensic_and_official_staging_20261025T064647Z_d9f88c35"
GITHUB_BIF=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02/data/official_BIF_20261025/official_two_site_BIF_time_evidence.json"
EXPECTED_GIT_BLOB="444889041c37cdaa6b79d149053e5299756fdb8c"
SITES={"US-Ho1":(16788,-5,"1996","2023"),"US-BZS":(86,-9,"2010","2024")}
EXPECTED_SHA={
 "US-Ho1":"24fd0a35cf5f39e49cb70fa63af6fb962cfc1bd71652aec51bd29843593ba6f1",
 "US-BZS":"9f7c46d81528505ef1586600fb68fb67fb87f88dc61cbbf04e8d0e4c17b48fac"}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def git_blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def evidence(bif_dir=None):
    if git_blob(GITHUB_BIF)!=EXPECTED_GIT_BLOB:
        raise ValueError("Official source extracted evidence Git blob mismatch")
    parsed=json.loads(GITHUB_BIF.read_text())
    if (parsed.get("schema")!="BATCH02_USER_UPLOADED_ORIGINAL_AMERIFLUX_BIF_EXTRACT_v1"
        or parsed.get("approved_for_DATM") is not False
        or parsed.get("official_source_url_not_independently_verified") is not True
        or len(parsed.get("sites",[]))!=2):
        raise ValueError("Uploaded BIF structured evidence schema altered")
    site={x["site_id"]:x for x in parsed["sites"]}
    if set(site)!=set(SITES):
        raise ValueError("BIF source site set unexpected")
    reread={}
    for name,(n,off,ymin,ymax) in SITES.items():
        e=site[name]
        if (float(e["utc_offset_hours"])!=off or
            e["source_workbook_sha256"]!=EXPECTED_SHA[name] or
            e["offset_history_coverage_verified"] is not False or
            e["model_time_join_approved"] is not False or
            e.get("utc_offset_date_start") is not None or
            e.get("utc_offset_date_end") is not None or
            not(-90<=float(e["latitude"])<=90) or
            not(-180<=float(e["longitude"])<=180)):
            raise ValueError("BIF offset/coordinate/date science gate changed "+name)
        orig=Path(bif_dir)/e["source_original_workbook"] if bif_dir else None
        reread[name]=False
        if orig and orig.is_file():
            if orig.is_symlink() or sha(orig)!=EXPECTED_SHA[name]:
                raise ValueError("Original official BIF XLSX bytes SHA mismatch "+name)
            reread[name]=True
    return site,reread

def upstream():
    m64=json.loads((S64/"unified_source_provenance_and_hold_manifest.json").read_text())
    m67=json.loads((S67/"source_forensic_manifest.json").read_text())
    if ((S64/"INCOMPLETE_DO_NOT_USE").exists() or
        (S67/"INCOMPLETE_DO_NOT_USE").exists() or
        m64.get("schema")!="STAGE64_ORIGINAL_HARD_FULL_CENSUS_9389_CANDIDATES_16943_HOLD_v1" or
        m64.get("total_selected_candidate_rows")!=9389 or
        m64.get("remaining_hard_HOLD")!=16943 or
        m64.get("approved_for_DATM") is not False or
        m67.get("schema")!="STAGE67_FLUXNET_BIF_SOURCE_DIAGNOSTIC_v1" or
        m67.get("Ho1_original_hard_UTC_HOLD")!=16788 or
        m67.get("BZS_original_hard_UTC_HOLD")!=86 or
        m67.get("publisher_authenticated") is not False or
        m67.get("approved_for_DATM") is not False):
        raise ValueError("Stage64 or Stage67 original source provenance altered")
    for folder,manifest in ((S64,m64),(S67,m67)):
        k="output_sha256" if folder==S64 else "output_SHA256"
        for name,expected in manifest[k].items():
            if sha(folder/name)!=expected:
                raise ValueError("Upstream Stage output SHA256 changed "+name)
    csv=S64/"16943_original_hard_events_still_HOLD.csv"
    events=pd.read_csv(csv,dtype={"site":str,"tower_local_start":str,
                                  "timestamp_start":str,"source_sha256":str})
    if len(events)!=16943 or events.duplicated(["site","tower_local_start"]).any():
        raise ValueError("Stage64 full original HOLD event census changed")
    return events,m64,m67

def compute_clock(held,source):
    rows=[];year_rows=[];critical=Counter()
    for site,(expected,offset,first,last) in SITES.items():
        g=held.loc[held.site.eq(site)].copy()
        if len(g)!=expected:
            raise ValueError("Original held source count mismatch "+site)
        if site=="US-Ho1" and not g.repair_status.eq("HOLD_HO1_SOURCE_RELEASE_UTC_NOT_VERIFIED").all():
            raise ValueError("Original source count/route mismatch "+site)
        if site=="US-BZS" and not g.repair_status.eq("HOLD_BZS_SOURCE_RELEASE_BIF_NOT_VERIFIED").all():
            raise ValueError("BZS original offset-HOLD route changed")
        if g.tower_local_start.isna().any():
            raise ValueError("Missing tower time")
        clock=pd.to_datetime(g.tower_local_start.str.strip(),format="%Y%m%d%H%M",errors="raise")
        if (clock.dt.year.min()<int(first) or clock.dt.year.max()>int(last) or
            clock.duplicated().any()):
            raise ValueError("Source tower clock out of original FLUXNET year bounds "+site)
        utc=clock-pd.Timedelta(hours=offset)
        assert len(utc)==len(clock)
        if not (utc+pd.Timedelta(hours=offset)).eq(clock).all():
            raise ValueError("Time shift not bijective")
        g["provisional_local_utc_offset_hours"]=offset
        g["shadow_UTC_START"]=utc.dt.strftime("%Y%m%d%H%M")
        g["shadow_UTC_year"]=utc.dt.year
        g["current_BIF_observed_offset_group_id"]=source[site]["utc_offset_group_id"]
        g["source_BIF_workbook_sha256"]=source[site]["source_workbook_sha256"]
        g["BIF_DATE_START_absent"]=True
        g["historical_offset_coverage_verified"]=False
        g["independent_ERA5_time_join_approved"]=False
        g["DATM_forcing_approved"]=False
        rows.append(g)
        flags=Counter(flag for s in g["flags"].fillna("").astype(str)
                      for flag in s.split("|") if flag)
        critical[site]=dict(flags)
        for year,sub in g.groupby(clock.dt.year,sort=True):
            year_rows.append(dict(site=site,original_tower_year=int(year),
                hard_events=len(sub),
                nominal_utc_offset_hours=offset,
                nominal_UTC_first=sub.shadow_UTC_START.min(),
                nominal_UTC_last=sub.shadow_UTC_START.max(),
                original_BADM_no_offset_start_date=True,
                source_time_convention_audit_pending=True,
                independence_grid_year_not_claimed=True))
    shadow=pd.concat(rows,ignore_index=True)
    if len(shadow)!=16874 or shadow.duplicated(["site","shadow_UTC_START"]).any():
        raise ValueError("Shadow source clock crosswalk not one-to-one")
    return shadow,pd.DataFrame(year_rows),critical

def self_test():
    t=pd.Timestamp("2001-12-31 23:30")
    assert (t-pd.Timedelta(hours=-5)).strftime("%Y%m%d%H%M")=="200201010430"
    assert (t-pd.Timedelta(hours=-9)).strftime("%Y%m%d%H%M")=="200201010830"
    assert 16788+86==16874
    assert 9389+16874+69==26332
    print("STAGE68 SELF-TEST PASS | BIF -5/-9 source clock and 16874 original hard offset holds")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    p.add_argument("--bif-dir",type=Path,
         help="Optional local directory with byte-identical original 2026 XLSX")
    args=p.parse_args()
    if args.self_test:return self_test()
    site,local_bytes=evidence(args.bif_dir)
    held,m64,m67=upstream()
    shadow,years,flags=compute_clock(held,site)
    print("STAGE68 BIF OFFICIAL SITE SOURCE",{
        x:dict(UTC_offset=site[x]["utc_offset_hours"],
            no_historical_date_in_BIF=True,
            original_xlsx_sha256=site[x]["source_workbook_sha256"],
            original_XLSX_reverified_locally=local_bytes[x]) for x in SITES})
    print("STAGE68 YEAR_HARD_COUNTS",years.to_string(index=False))
    print("STAGE68 ORIGINAL_HARD_FLAGS",json.dumps(flags,sort_keys=True))
    print("STAGE68 PROVISIONAL UTC CENSUS",dict(Counter(shadow.site)))
    print("STAGE68 HISTORICAL CLOCK VALIDATION REQUIRED | no Stage64 HOLD released")
    if args.check:
        print("STAGE68 CHECK PASS | no output/source/model writes")
        return
    dest=R/("stage68_official_uploaded_BIF_Ho1_BZS_UTC_shadow_"+
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
            "_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Diagnostic official BIF clock offsets only. No time release.\n")
    files={
      "16874_Ho1_BZS_original_hard_BIF_local_to_UTC_SHADOW.csv":shadow,
      "Ho1_BZS_yearly_original_hard_UTC_shadow.csv":years}
    output={}
    for name,data in files.items():
        f=dest/name;data.to_csv(f,index=False);output[name]=sha(f)
    flagfile=dest/"original_humidity_hard_reason_flag_counts.json"
    flagfile.write_text(json.dumps(flags,indent=2,sort_keys=True)+"\n")
    output[flagfile.name]=sha(flagfile)
    if sha(S64/"16943_original_hard_events_still_HOLD.csv")!=m64[
      "output_sha256"]["16943_original_hard_events_still_HOLD.csv"]:
        raise ValueError("Original held CSV mutated while building audit")
    manifest={
      "schema":"STAGE68_OFFICIAL_BIF_HO1_BZS_HISTORICAL_CLOCK_SHADOW_v1",
      "Ho1_nominal_BIF_offset_hours":-5,"BZS_nominal_BIF_offset_hours":-9,
      "Ho1_original_hard_clock_shadow":16788,
      "BZS_original_hard_clock_shadow":86,
      "total_source_HOLD_shadow_only":16874,
      "stage64_numeric_water_humidity_candidates_unchanged":9389,
      "historical_UTC_offset_coverage_verified":False,
      "independent_CDS_ERA5_Ho1_BZS_gridyears_verified_complete":False,
      "BIF_byte_for_byte_reverified_on_cluster":local_bytes,
      "original_uploaded_BIF_excel_artifact_git_hash":EXPECTED_GIT_BLOB,
      "source_SHA256":{
        "official_user_upload_BIF_JSON":sha(GITHUB_BIF),
        "stage64_manifest":sha(S64/"unified_source_provenance_and_hold_manifest.json"),
        "stage67_manifest":sha(S67/"source_forensic_manifest.json")},
      "output_sha256":output,"DATM_approved":False,
      "no_original_or_model_writes":True}
    (dest/"stage68_source_and_science_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE68 AUDIT PASS | original Ho1 16788 + BZS 86 BIF clock shadow; historical source HOLD retained")
    print("REPORT",dest)
    print("NO ORIGINAL, ERA5, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

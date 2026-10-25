#!/usr/bin/env python3
"""Stage12l — prioritize the five NON-US-MtB Batch03 humidity evidence gaps.

Stage12k verified that US-MtB GRID_RH's measured QC0 science gate failed:
1,035 native humidity holds are NOT authorised. Do not exhaust CDS
requests on the remaining US-MtB years. The other five sites contain
447 previously held RH events categorized by verified Stage12e as
"NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR".

Re-use SHA-PINNED Stage12f original Stage09/10 source receipts and exact
download implementation; select only US-Kon, US-NR1, US-Me6, US-MMS,
US-NR3 and rank by the number of still unpaired source-native events
per site-year. No invented sites, years or coordinates.

--self-test : local model/source-count regression, no file writes or API.
--check     : verify upstream Stage12k and Stage12f source SHAs, print
              exact five-site queue (read-only), NO FILE OR CDS WRITES.
--download --max-new N: call the original SHA-pinned Stage12f safety
              downloader for up to N=1..3 highest-priority unverified
              year/site sources. Only new external ERA5-Land evidence
              source, NOT site humidity repair, DATM, model, QC0 or T/P.

After downloading, use the existing Stage12g source-only SHADOW to test
the actual physical RH repair counts before obtaining further years.
This does not alter the US-MtB scientific rejection or original holds.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path

import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12l-v1-20261025-five-nonMtB-447-missing-source-year-priority"
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
SCRIPT_F=BASE/"scripts/stage12/12f_missing_year_ERA5Land_download_queue.py"
BLOB_F="690e9757b2e1f8536b8002c4ede43a6d9a6a2609"
STAGEK=ROOT/"reports/stage12k_US-MtB_GRID_RH_QC0_error_regime_20261025T070844Z_8ffe36dc"
FIVE={"US-Kon":211,"US-NR1":135,"US-Me6":80,"US-MMS":15,"US-NR3":6}
MTB=2363
EXPECTED_K_FILES={
    "three_year_QC0_GRID_RH_reproduced_gate.csv",
    "cold_QC0_observed_error_by_month.csv",
    "cold_QC0_observed_error_by_tower_temperature.csv",
    "cold_QC0_observed_error_by_original_VPD.csv",
    "QC0_HIGH2_contiguous_native_halfhour_episodes.csv",
    "held_1035_tower_temperature_and_month_analogue_coverage.csv",
    "three_year_QC0_cold_physics_disposition.csv",
    "SCIENCE_HOLD.md"
}

def file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Immutable source missing or symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as handle:
        for data in iter(lambda:handle.read(1<<20),b""):
            h.update(data)
    return h.hexdigest()

def blob(p):
    data=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def get_f():
    if blob(SCRIPT_F)!=BLOB_F:
        raise ValueError("Stage12f source year queue code changed from exact reviewed Git blob")
    spec=importlib.util.spec_from_file_location("batch03_pinned_Stage12f_for_12l",SCRIPT_F)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def guard_k():
    if not STAGEK.is_dir() or STAGEK.is_symlink():
        raise ValueError("Stage12k v2 verified diagnostic report folder absent")
    k=json.loads(file(STAGEK/"stage12k_source_error_regime_SHA_receipt.json").read_text())
    if (k.get("version")!="batch03-stage12k-v1-20261025-US-MtB-verified-GRID_RH-QC0-tail"
        or k.get("original_target_1035_holds_unchanged") is not True
        or k.get("previous_science_gate_failed") is not True
        or k.get("new_humidity_repair_count")!=0
        or k.get("measurements_original_QC0_unchanged") is not True
        or k.get("source_clock_approved") is not False
        or k.get("Postv5_approved")!=0 or k.get("DATM_ready")!=0
        or k.get("spinup_authorized")!=0
        or set(k.get("output_sha256",{}))!=EXPECTED_K_FILES):
        raise ValueError("Stage12k original measured QC0 science HOLD receipt policy differs")
    for name,digest in k["output_sha256"].items():
        if sha(STAGEK/name)!=digest:
            raise ValueError("SHA-sealed Stage12k source analysis changed "+name)
    counts=pd.read_csv(file(STAGEK/"held_1035_tower_temperature_and_month_analogue_coverage.csv"))
    if (int(counts.held_target_N.sum())!=1035
        or int(counts.loc[counts.QC0_cold_analogue_N.lt(20),"held_target_N"].sum())!=323
        or int(counts.loc[counts.temperature_bin.eq(">5"),"held_target_N"].sum())!=15):
        raise ValueError("Stage12k verified exact 1035/323/15 source regimes changed")
    print("STAGE12L PINNED STAGE12K VERIFIED: US-MtB 1035 holds; 323 weak analogue; 15 warm; ZERO release",flush=True)

def selftest():
    assert sum(FIVE.values())==447
    assert sum(FIVE.values())+MTB==2810
    assert len(FIVE)==5 and "US-MtB" not in FIVE
    fake=[{"site":"US-Kon","year":2020,"unresolved_humidity":10},
          {"site":"US-NR1","year":2022,"unresolved_humidity":4},
          {"site":"US-MtB","year":2024,"unresolved_humidity":408}]
    filtered=choose_nonmtb(fake)
    assert len(filtered)==2 and sum(x["unresolved_humidity"] for x in filtered)==14
    assert filtered[0]["site"]=="US-Kon"
    print("STAGE12L SELF-TEST PASS: original 2810 = 2363 excluded US-MtB + 447 five-site events; no requests or writes",flush=True)

def choose_nonmtb(plan):
    return sorted(
        [x for x in plan if x["site"] in FIVE],
        key=lambda x:(-int(x["unresolved_humidity"]),x["site"],int(x["year"]))
    )

def build():
    guard_k()
    f=get_f()
    plan,t,pilot,source_receipt=f.evidence()
    if (sum(x["unresolved_humidity"] for x in plan)!=2810
        or sum(x["unresolved_humidity"] for x in plan if x["site"]=="US-MtB")!=MTB):
        raise ValueError("Stage12f all-seven-source-year history differs")
    target=choose_nonmtb(plan)
    counted=pd.Series({site:sum(p["unresolved_humidity"] for p in target if p["site"]==site)
                        for site in FIVE})
    if counted.to_dict()!=FIVE:
        raise ValueError("Stage12f originally source-missing 447 five-site targets changed")
    states=[]
    for item in target:
        status,meta=f.status(item,t)
        if status not in ("MISSING","VERIFIED"):
            raise ValueError("Unknown original source year status "+status)
        states.append((item,status,meta))
    pending=[x for x,status,_ in states if status=="MISSING"]
    total_verified=sum(x["unresolved_humidity"] for x,status,_ in states if status=="VERIFIED")
    if sum(x["unresolved_humidity"] for x in pending)+total_verified!=447:
        raise ValueError("Five-site existing-year source count fails scientific gate")
    pending=choose_nonmtb(pending)
    return f,t,pilot,states,pending,total_verified

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--download",action="store_true")
    parser.add_argument("--max-new",type=int,default=3)
    args=parser.parse_args()
    print("STAGE12L — FIVE NON-MTB SITE VERIFIED GRID EVIDENCE PRIORITY | "+VERSION,flush=True)
    selftest()
    if args.self_test:
        return
    if not 1<=args.max_new<=3:
        raise ValueError("Request limit: 1..3 new CDS year sources per invocation")
    f,t,pilot,states,pending,verified=build()
    print("\n========== FIVE NON-MTB SITE/YEAR SOURCE STATUS ==========",flush=True)
    frame=pd.DataFrame([
      {"site":i["site"],"year":i["year"],
       "original_missing_humidity_rows":i["unresolved_humidity"],
       "source_status":state,
       "original_source_SHA256":metadata["sha256"] if metadata else "-"}
       for i,state,metadata in states])
    if len(frame):
        print(frame.sort_values(["original_missing_humidity_rows","site"],
              ascending=[False,True]).to_string(index=False),flush=True)
    else:
        raise ValueError("Original 447 five-site events unexpectedly have no site-years")
    chosen=pending[:args.max_new]
    print("\nSTAGE12L FIVE-SITE SUMMARY:",
          "source_events_original=447",
          "verified_new_source_events="+str(verified),
          "still_missing_year_source_events="+str(447-verified),
          "five_site_years="+str(len(states)),
          "unverified_five_site_years="+str(len(pending)),
          "US-MtB_years_selected=0",
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    print("\n========== TOP THREE MISSING NON-MTB SOURCE YEARS ==========",flush=True)
    for item in chosen:
        print("NEXT:",item["site"],item["year"],
             "source_missing_halfhours",item["unresolved_humidity"],
             "CDS_year_window",item["request"]["date"],flush=True)
    if args.check:
        print("STAGE12L CHECK ONLY: zero CDS requests, zero files, forcing or model writes.",flush=True)
        return
    if not chosen:
        print("STAGE12L NO MISSING FIVE-SITE YEARS TO DOWNLOAD.",flush=True)
        return
    for item in chosen:
        # Original SHA-pinned Stage12f enforces no overwrite, no partial
        # source reuse, original source coordinates and physics SHA checks.
        f.download(item,t,pilot,sha(f.E/"stage12e_research_only_sha_receipt.json"))
    print("STAGE12L DOWNLOAD SUCCESS: new_five_site_years="+str(len(chosen)),
          "US-MtB_new_downloads=0",
          "new_forcing_values=0",
          "original_tower_T_P_clock_changed=FALSE",
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12L STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

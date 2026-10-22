#!/usr/bin/env python3
"""Shared AmeriFlux Stage32: inspect two remaining multi-layer ZBOT mappings.

Expected snapshot SHA256 is pinned. For CA-Cbo and CA-Man report all original
TA/WS sensor names, heights, instrument types, and source comments. Generate
NO automatic choice, but rank explicit ABOVE_CANOPY_TEXT / TA-near-WS-height
candidate EVIDENCE for scientific consideration, clearly labelled unverified.

Read Stage31 provisional JSON only for checking (it is never edited). Keep
static/dynamic candidates from other eight stations unchanged; compare partial
date alternatives separately using Stage31's existing annual sensitivity.

An empty BASE Start_Date means "applies at beginning of site's full data
record" per official AmeriFlux Measurement Height documentation, not "missing
metadata." It is still not proof of FLUXNET TA_F source-variable crosswalk.

No forcing, surface, ZBOT series, NetCDF, CIME, Slurm or source files modified.
"""
from __future__ import annotations

import argparse,csv,hashlib,re
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
BASE=REPO/"metadata"/"BASE_MeasurementHeight_20260908.csv"
SITES=("CA-Cbo","CA-Man")
SHA="1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a"
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SITE_PAGES={
  "CA-Cbo":"https://ameriflux.lbl.gov/sites/siteinfo/CA-Cbo",
  "CA-Man":"https://ameriflux.lbl.gov/sites/siteinfo/CA-Man",
}
KEYS=("Site_ID","Variable","Start_Date","Height","Instrument_Model","Comment")


def checksum(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    return h.hexdigest()


def read_csv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames:raise RuntimeError("Header missing "+str(path))
        return list(reader.fieldnames),list(reader)


def write_csv(path,rows,fields):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)


def asheight(s):
    try:
        v=float(s)
        return v if .5<=v<=150 else None
    except (ValueError,TypeError):return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    p.add_argument("--height-csv",type=Path,default=BASE)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    a=p.parse_args()
    if checksum(a.height_csv)!=SHA:raise RuntimeError("Unpinned BASE CSV SHA256")
    columns,rows=read_csv(a.height_csv)
    if not set(KEYS)<=set(columns):
        raise RuntimeError("Required BASE metadata fields missing")
    by=defaultdict(list)
    for r in rows:
        if r["Site_ID"] in SITES and r["Variable"].upper().startswith(("TA","WS")):
            by[r["Site_ID"]].append(r)
    for site in SITES:
        if not any(r["Variable"].startswith("TA") for r in by[site]):
            raise RuntimeError(site+": no TA-family source data")
    print("STAGE32 PREFLIGHT: 2/2 multi-layer sites; BASE SHA256=",SHA,flush=True)
    if a.check:
        print("CHECK ONLY. No ZBOT approval or reports created.")
        return

    evidence=[];selection=[];ws_reference={}
    for site in SITES:
        ta=[r for r in by[site] if r["Variable"].upper().startswith("TA")]
        ws=[r for r in by[site] if r["Variable"].upper().startswith("WS")]
        heights=[asheight(x["Height"]) for x in ws]
        ws_heights=sorted({x for x in heights if x is not None})
        ws_reference[site]=ws_heights
        for r in ta+ws:
            h=asheight(r["Height"])
            if h is None:raise RuntimeError(site+": invalid sensor measurement height")
            is_ta=r["Variable"].upper().startswith("TA")
            comment=r.get("Comment","")
            above=bool(re.search(r"ABV.?CNPY|ABOVE.?CANOPY|ABV.?CN",comment,re.I))
            ws_diff=min([abs(h-w) for w in ws_heights],default=float("inf"))
            flags=[]
            if above:flags.append("COMMENT_REFERENCES_ABOVE_CANOPY_PROFILE")
            if is_ta and ws_diff<=3.0:flags.append("TA_SENSOR_WITHIN_3M_OF_WS_HEIGHT")
            if r["Start_Date"].strip()=="":
                flags.append("BASE_BLANK_START_DATE_SITE_RECORD_START")
            evidence.append(dict(site=site,
                family="TA" if is_ta else "WS",
                BASE_variable=r["Variable"],height_m=h,
                Start_Date=r["Start_Date"],height_start_interpretation=(
                    "START_OF_SITE_FULL_RECORD" if not r["Start_Date"].strip()
                    else "DATED_EPOCH"),
                Instrument_Model=r.get("Instrument_Model",""),
                Comment=comment,
                nearest_WS_height_m=min(ws_heights,key=lambda w:abs(h-w))
                    if is_ta and ws_heights else "",
                TA_to_WS_height_difference_m=round(ws_diff,2) if is_ta and ws_heights else "",
                evidence_flags="|".join(flags),
                FLUXNET_TA_F_match_verified="NO",
                scientific_decision="UNRESOLVED_MAPPING_REQUIRES_SOURCE_PROOF"))
        ta_options=sorted(set(asheight(r["Height"]) for r in ta))
        for h in ta_options:
            related=[r for r in ta if asheight(r["Height"])==h]
            above=any(re.search(r"ABV.?CNPY|ABOVE.?CANOPY",r.get("Comment",""),re.I) for r in related)
            near=min((abs(h-w) for w in ws_heights),default=float("inf"))
            # These are *candidate-review priorities*, NOT a height selection.
            priority=("P1_ABOVE_CANOPY_COMMENT" if above else
                      "P2_NEAR_WS_HEIGHT" if near<=3 else
                      "P3_MULTILEVEL_ALTERNATIVE")
            selection.append(dict(site=site,candidate_height_m=h,
                source_TA_variables=";".join(sorted({r["Variable"] for r in related})),
                highest_evidence_priority=priority,
                TA_sensor_comment_matches_above_canopy=bool(above),
                closest_WS_height_difference_m=round(near,2) if near<float("inf") else "",
                BASE_start_dates=";".join(sorted({r["Start_Date"] for r in related})),
                source_evidence_url=SITE_PAGES[site],
                FLUXNET_TA_F_source_crosswalk="UNVERIFIED",
                proposed_ZBOT_height_m="",
                selected_by_scientist="",
                decision="HOLD_DO_NOT_WRITE_ZBOT"))
        print("  %-7s TA_heights=%s  WS_heights=%s reviewed_options=%d"%
              (site,",".join(f"{v:g}" for v in ta_options),
               ",".join(f"{v:g}" for v in ws_heights),len(ta_options)),flush=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=a.report_root/("stage32_CA_Cbo_CA_Man_height_decision_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/"01_all_original_TA_WS_sensor_metadata.csv",evidence,list(evidence[0]))
    write_csv(out/"02_suggested_sensor_height_evidence_priorities_NOT_APPROVED.csv",
              selection,list(selection[0]))
    write_csv(out/"03_blank_scientific_decision_template.csv",[
        dict(site=site,selected_BASE_TA_variable="",selected_ZBOT_static_height_m="",
             evidence_FLUXNET_TA_F_mapping="",
             source_historical_height_assumption="",
             independent_site_instrument_log_or_paper="",
             approved_by="",science_state="HOLD") for site in SITES],
        ["site","selected_BASE_TA_variable","selected_ZBOT_static_height_m",
         "evidence_FLUXNET_TA_F_mapping",
         "source_historical_height_assumption",
         "independent_site_instrument_log_or_paper",
         "approved_by","science_state"])
    print("STAGE32 SUMMARY: sites=2, candidate_height_options=%d, approved=0"%
          len(selection),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("MULTI-LAYER SOURCE EVIDENCE ONLY. No assignment to FLUXNET TA_F or ZBOT.")


if __name__=="__main__":
    main()

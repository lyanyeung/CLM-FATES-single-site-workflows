#!/usr/bin/env python3
"""Stage70B: human-readable CA-Man 36-event temperature review — NO REPAIR.

--list     prints all 36 reviewed event groups and the 17 separate RH holds.
--episode  prints a selected event's original/base/FLUXMET/ERA5 and time window.
--export   creates a NEW review-only directory with one 36-row editable decision
           sheet, independent RH sheet, and a text report; no forcing edits.
Scientific approval is never inferred or written by this program.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import Counter,defaultdict
from datetime import datetime, timezone
from pathlib import Path

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
REVIEW_ROOT="stage70a_human_science_review_docket_20261024T074257864136Z"
SOURCE61="stage61_P1_source_evidence_20261024T053231392029Z"
SOURCE65="stage65_BASE_TA_source_evidence_20261024T064545094737Z"
SOURCE67="stage67_native_temperature_crosswalk_20261024T070833236985Z"
SOURCE69="stage69_CA-Man_shadow_science_assessment_20261024T072405849089Z"

FIELDS=[
 "site","episode_id","event_time","review_group","original_step_C",
 "original_T_before_C","original_T_at_C","FLUXMET_T_before_C",
 "FLUXMET_T_at_C","ERA5_T_before_C","ERA5_T_at_C",
 "FLUXMET_QC_transition","BASE_native_T_before_JSON",
 "BASE_native_T_at_JSON","BASE_sensor_match_count_before",
 "Stage68_shadow_T_C","original_RH_pct","shadow_RH_pct",
 "original_VPD_hPa","shadow_VPD_hPa","delta_RH_pp",
 "delta_VPD_hPa","science_status","human_decision","human_evidence_notes"
]

def load(path,required):
    if not path.is_file():raise RuntimeError("Missing source: "+str(path))
    with path.open(newline="",encoding="utf-8-sig") as f:
        r=csv.DictReader(f)
        names=r.fieldnames or []
        if len(names)!=len(set(names)) or not set(required).issubset(names):
            raise RuntimeError("CSV source schema mismatch: "+str(path)+
                               "; missing "+str(set(required)-set(names)))
        return list(r)

def uniquely_index(rows,label):
    d={}
    for r in rows:
        key=(r["site"],r["episode_id"])
        if key in d:raise RuntimeError("Duplicate "+label+" event "+repr(key))
        d[key]=r
    return d

def native(x):
    if not x:return ""
    try:v=json.loads(x)
    except (TypeError,ValueError):return "INVALID_NATIVE_JSON"
    if not isinstance(v,dict):return "INVALID_NATIVE_JSON"
    # Preserve all channel names; do not invent a sensor selection.
    keys=sorted(k for k in v if k=="TA" or
                (k.startswith("TA_") and not k.endswith("_QC")))
    return json.dumps({k:v[k] for k in keys},ensure_ascii=False,sort_keys=True)

def maybe(x):
    try:
        z=float(x)
        return z if math.isfinite(z) and z > -9990 else None
    except (TypeError,ValueError):return None

def fmt(x,nd=1):
    v=maybe(x)
    return f"{v:.{nd}f}" if v is not None else "NA"

def build(reports):
    r70=load(reports/REVIEW_ROOT/"36_CA-Man_QC0_to_QC1_review.csv",
             {"site","episode_id","largest_step_timestamp","manual_review_group",
              "max_abs_step_C"})
    r67=uniquely_index(load(reports/SOURCE67/"CA-Man_36_gapfill_boundaries.csv",
             {"site","episode_id","timestamp","candidate_T_before_C",
              "candidate_T_current_C","FLUXMET_T_before_C","FLUXMET_T_current_C",
              "ERA5_T_before_C","ERA5_T_current_C",
              "native_before_agrees_with_FLUXMET_count_1C"}),"stage67")
    r65=uniquely_index([r for r in load(
              reports/SOURCE65/"targeted_60_temperature_events.csv",
              {"site","episode_id","timestamp","BASE_TA_30min_before_JSON",
               "BASE_TA_at_event_JSON"}) if r["site"]=="CA-Man"],"stage65")
    r69=uniquely_index(load(reports/SOURCE69/"all_19_shadow_T_RH_VPD_impacts.csv",
             {"site","episode_id","timestamp","shadow_T_C","original_RH_pct",
              "shadow_RH_pct","original_VPD_hPa","shadow_VPD_hPa",
              "delta_RH_pp","delta_VPD_hPa"}),"stage69")
    if len(r70)!=36 or len(r67)!=36 or len(r65)!=36 or len(r69)!=19:
        raise RuntimeError("Stage70A/67/65/69 baseline count mismatch (36/36/36/19)")
    rows=[]
    for a in r70:
        key=(a["site"],a["episode_id"])
        if key not in r67 or key not in r65:raise RuntimeError("Missing event source "+str(key))
        s,b=r67[key],r65[key]
        when=a["largest_step_timestamp"]
        if s["timestamp"]!=when or b["timestamp"]!=when:
            raise RuntimeError("Mismatched report timestamps "+str(key))
        h=r69.get(key,{})
        if h and h["timestamp"]!=when:
            raise RuntimeError("Stage69 time mismatch "+str(key))
        group=a["manual_review_group"]
        if group not in ("CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD",
                         "CA_MAN_15_FIXED_Q_PHYSICS_REJECTED",
                         "CA_MAN_2_ANCHOR_DISAGREEMENT"):
            raise RuntimeError("Unexpected classification "+group)
        if bool(h)!=(group=="CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD"):
            raise RuntimeError("Shadow row vs review category mismatch "+str(key))
        previous=maybe(s["candidate_T_before_C"])
        at=maybe(s["candidate_T_current_C"])
        rows.append(dict(
            site="CA-Man",episode_id=a["episode_id"],event_time=when,
            review_group=group,original_step_C=round(at-previous,4)
                         if at is not None and previous is not None else "",
            original_T_before_C=s["candidate_T_before_C"],
            original_T_at_C=s["candidate_T_current_C"],
            FLUXMET_T_before_C=s["FLUXMET_T_before_C"],
            FLUXMET_T_at_C=s["FLUXMET_T_current_C"],
            ERA5_T_before_C=s["ERA5_T_before_C"],
            ERA5_T_at_C=s["ERA5_T_current_C"],
            FLUXMET_QC_transition="0->1",
            BASE_native_T_before_JSON=native(b["BASE_TA_30min_before_JSON"]),
            BASE_native_T_at_JSON=native(b["BASE_TA_at_event_JSON"]),
            BASE_sensor_match_count_before=s["native_before_agrees_with_FLUXMET_count_1C"],
            Stage68_shadow_T_C=h.get("shadow_T_C",""),
            original_RH_pct=h.get("original_RH_pct",""),
            shadow_RH_pct=h.get("shadow_RH_pct",""),
            original_VPD_hPa=h.get("original_VPD_hPa",""),
            shadow_VPD_hPa=h.get("shadow_VPD_hPa",""),
            delta_RH_pp=h.get("delta_RH_pp",""),
            delta_VPD_hPa=h.get("delta_VPD_hPa",""),
            science_status="HOLD_UNTIL_INDEPENDENT_EVIDENCE",
            human_decision="",human_evidence_notes=""
        ))
    counts=Counter(x["review_group"] for x in rows)
    if (counts["CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD"],
        counts["CA_MAN_15_FIXED_Q_PHYSICS_REJECTED"],
        counts["CA_MAN_2_ANCHOR_DISAGREEMENT"])!=(19,15,2):
        raise RuntimeError("19/15/2 partition changed")
    rank={"CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD":0,
          "CA_MAN_15_FIXED_Q_PHYSICS_REJECTED":1,
          "CA_MAN_2_ANCHOR_DISAGREEMENT":2}
    rows.sort(key=lambda r:(rank[r["review_group"]],
                            -abs(float(r["original_step_C"] or 0)),r["event_time"]))
    low=load(reports/REVIEW_ROOT/"17_unresolved_low_RH_review.csv",
             {"site","timestamp","RH_percent"})
    if len(low)!=17:raise RuntimeError("RH unresolved count mismatch")
    return rows,low

def printed_summary(events,low):
    print("STAGE70B | HUMAN REVIEW OF 36 CA-MAN EVENTS | NO REPAIRS")
    print("Review categories:",dict(Counter(r["review_group"] for r in events)))
    print("Number of independent humidity observations verified: 0")
    print("All 36 events (T in deg C, humidity shifts are percentage points):")
    print(f"{'N':>2} {'time':19} {'group':9} {'step':>7} {'TA_before':>9} "
          f"{'TA_at':>7} {'shadow_T':>9} {'dRH':>7} {'dVPD':>8}")
    for i,r in enumerate(events,1):
        label=("SHADOW" if "19_SHADOW" in r["review_group"] else
               "PHYS_FAIL" if "15_FIXED" in r["review_group"] else "ANCHOR")
        print(f"{i:2d} {r['event_time']:19} {label:9} {fmt(r['original_step_C']):>7} "
              f"{fmt(r['original_T_before_C']):>9} {fmt(r['original_T_at_C']):>7} "
              f"{fmt(r['Stage68_shadow_T_C']):>9} {fmt(r['delta_RH_pp']):>7} "
              f"{fmt(r['delta_VPD_hPa']):>8}")
    print("Unresolved low-RH records:",len(low),
          "by site:",dict(Counter(r["site"] for r in low)))
    print("To inspect one event: use --episode <FULL_EPISODE_ID> or --episode <NUMBER 1..36>.")

def detail(r,reports):
    print("\n"+"="*102)
    print(r["episode_id"],r["event_time"],r["review_group"])
    print("Original TA before/at:",r["original_T_before_C"],r["original_T_at_C"],
          "FLUXMET before/at:",r["FLUXMET_T_before_C"],r["FLUXMET_T_at_C"],
          "ERA5 before/at:",r["ERA5_T_before_C"],r["ERA5_T_at_C"])
    print("Raw BASE before:",r["BASE_native_T_before_JSON"])
    print("Raw BASE at event:",r["BASE_native_T_at_JSON"])
    print("Base/FLUXMET matched before-side sensor count:",r["BASE_sensor_match_count_before"])
    print("Shadow T/RH/VPD:",r["Stage68_shadow_T_C"],r["shadow_RH_pct"],r["shadow_VPD_hPa"])
    print("Original RH/VPD (Stage69):",r["original_RH_pct"],r["original_VPD_hPa"])
    print("NOTE: BASE/FLUXMET/ERA source clock and sensor identity still UNVERIFIED.")
    context=load(reports/SOURCE61/"P1_context_source_comparisons.csv",
                 {"site","episode_id","timestamp","candidate_TA_C",
                  "FLUXMET_TA_F_C","FLUXMET_TA_F_QC","ERA5_TA_ERA_C"})
    matched=[x for x in context if (x["site"],x["episode_id"])==("CA-Man",r["episode_id"])]
    matched.sort(key=lambda x:x["timestamp"])
    print("Stage61 +/-4h context:")
    print(f"{'time':19} {'TA_forcing':>10} {'TA_FLUXMET':>10} {'QC':>3} {'TA_ERA5':>9}")
    for row in matched:
        print(f"{row['timestamp']:19} {fmt(row['candidate_TA_C']):>10} "
              f"{fmt(row['FLUXMET_TA_F_C']):>10} "
              f"{row['FLUXMET_TA_F_QC']:>3} {fmt(row['ERA5_TA_ERA_C']):>9}")
    print("DECISION: HOLD; this diagnostic cannot certify or implement a repair.")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-root",type=Path,default=EXP/"reports")
    parser.add_argument("--episode",help="Full episode ID or row number 1..36")
    parser.add_argument("--export",action="store_true",
                        help="Write only a new HUMAN_REVIEW CSV directory")
    a=parser.parse_args()
    reports=a.reports_root.resolve(strict=True)
    events,low=build(reports)
    printed_summary(events,low)
    if a.episode:
        if a.episode.isdecimal():
            index=int(a.episode)-1
            if not 0<=index<len(events):parser.error("Episode number must be 1..36")
            selected=events[index]
        else:
            found=[x for x in events if x["episode_id"]==a.episode]
            if len(found)!=1:parser.error("Unknown episode ID")
            selected=found[0]
        detail(selected,reports)
    if a.export:
        dest=reports/("stage70b_CA-Man_human_review_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        dest.mkdir(exist_ok=False)
        with (dest/"36_CA-Man_review_EDIT_DECISIONS_MANUALLY.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS)
            w.writeheader();w.writerows(events)
        with (dest/"17_unresolved_RH_review.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(low[0]))
            w.writeheader();w.writerows(low)
        (dest/"README.txt").write_text(
            "Manual science-review sheets only. Fill human_decision and human_evidence_notes "
            "after inspecting verified tower data; do not use these CSVs to change forcing. "
            "No event is science-approved by this script.\n",encoding="utf-8")
        print("REVIEW SHEETS:",dest)
        print("Only review CSVs/README created. Forcing untouched.")
    else:
        print("READ-ONLY COMPLETE: no files created.")

if __name__=="__main__":
    main()

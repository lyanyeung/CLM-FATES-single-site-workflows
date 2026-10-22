#!/usr/bin/env python3
"""AmeriFlux Batch01 Stage24: read-only science-review decision queues.

Consumes completed Stage21 numeric audit and Stage22 extreme/source audit.
No meteorological source, QCv5 candidate, DATM, surface or CIME changes.

This is an *organizing* step, not new QC physics and NOT science approval.
It groups QC0 edits, low-positive RH, temporal jumps, extremes, and
TA-vs-ERA differences into site-specific event queues. All uncertain records
remain HOLD. A difference from ERA5 is not proof the tower is erroneous.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
STAGE21=ROOT/"stage21_ten_site_post_qcv5_20261021T235034313539Z"
STAGE22=ROOT/"stage22_science_extreme_qc_20261022T011147021399Z"
SITES=("BR-Ma2","CA-Ca3","CA-Cbo","CA-LP1","CA-Man",
       "CA-TP1","CA-TP3","CA-TP4","US-Aud","US-Bar")
CRITICAL={"RH_NONPOSITIVE","QBOT_OUTSIDE_0_TO008"}
ELEVATED={"NEW_TA_30MIN_JUMP_GT8C","TA_QC_SOURCE_SWITCH_WITH_JUMP",
          "ISOLATED_TA_SPIKE_GT8C","TA_EXTREME_LT_MINUS25_OR_GT45",
          "PSRF_30MIN_JUMP_GT5000PA","POSITIVE_RH_LT1PCT",
          "QC0_MEASURED_EDIT"}
CONTEXT={"CANDIDATE_TA_30MIN_JUMP_GT8C","TA_VS_ERA_GT15C",
         "VPD_30MIN_JUMP_GT5HPA","PRECIP_GT18MM_PER_30MIN"}


def read_csv(path):
    if not path.is_file():
        raise RuntimeError("Missing input report: "+str(path))
    with path.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path,rows,columns):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def intfield(row,name):
    try:
        return int(float(row[name]))
    except (KeyError,ValueError,TypeError) as exc:
        raise RuntimeError("Invalid numeric field "+name+": "+repr(row)) from exc


def priority(flags):
    if flags&CRITICAL:return "P0_NUMERIC_GATE_FAILURE"
    if flags&ELEVATED:return "P1_TARGETED_SCIENCE_REVIEW"
    if flags&CONTEXT:return "P2_CONTEXT_SOURCE_REVIEW"
    return "P3_OTHER_REVIEW"


def validate_reports(a,b):
    s21=read_csv(a/"site_independent_numeric_and_science_gates.csv")
    s22=read_csv(b/"site_extremes_and_sources_summary.csv")
    if len(s21)!=10 or len(s22)!=10:
        raise RuntimeError("Expected 10 records in each report")
    by21={r["site"]:r for r in s21}
    by22={r["site"]:r for r in s22}
    if set(by21)!=set(SITES) or set(by22)!=set(SITES):
        raise RuntimeError("Stage21/22 site inventory differs")
    for site in SITES:
        if by21[site].get("numerical_gate")!="PASS":
            raise RuntimeError(site+": Stage21 numerical gate not PASS")
        if intfield(by21[site],"changed_QC0_measured")!=intfield(by22[site],"QC0_edits"):
            raise RuntimeError(site+": Stage21/22 QC0 event totals disagree")
        for field in ("RH_NONPOSITIVE","NEW_TA_30MIN_JUMP_GT8C"):
            if intfield(by22[site],field)!=0:
                raise RuntimeError(site+": nonzero "+field+"; stop and review data")
        if intfield(by21[site],"residual_RH_le_zero")!=0:
            raise RuntimeError(site+": Stage21 residual RH invalid")
    if sum(intfield(x,"QC0_edits") for x in s22)!=518:
        raise RuntimeError("QC0=518 cross-check failed for this pinned report set")
    if sum(intfield(x,"POSITIVE_RH_LT1PCT") for x in s22)!=27:
        raise RuntimeError("RH<1=27 cross-check failed")
    if sum(intfield(x,"CANDIDATE_TA_30MIN_JUMP_GT8C") for x in s22)!=894:
        raise RuntimeError("TA jumps 894 cross-check failed")
    if sum(intfield(x,"TA_VS_ERA_GT15C") for x in s22)!=2306:
        raise RuntimeError("TA/ERA 2306 cross-check failed")
    return by21,by22


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage21-dir",type=Path,default=STAGE21)
    p.add_argument("--stage22-dir",type=Path,default=STAGE22)
    p.add_argument("--report-root",type=Path,default=ROOT)
    op=p.add_mutually_exclusive_group(required=True)
    op.add_argument("--check",action="store_true",help="Verify reports, write nothing")
    op.add_argument("--run",action="store_true",help="Write science-review QUEUES only")
    args=p.parse_args()

    by21,by22=validate_reports(args.stage21_dir,args.stage22_dir)
    events=read_csv(args.stage22_dir/"timestamped_event_context.csv")
    qc0=read_csv(args.stage22_dir/"all_518_original_QC0_edits.csv")
    if len(qc0)!=518:
        raise RuntimeError("Expected exactly 518 separately logged official-QC0 edits")
    expected_events=sum(intfield(row,"review_timestamps") for row in by22.values())
    if len(events)!=expected_events:
        raise RuntimeError("Stage22 event context count differs from site summaries")
    for row in qc0:
        if row["site"] not in by22:raise RuntimeError("Unknown QC0 site")
    print("STAGE24 PREFLIGHT: sites=10; Stage21 numeric_PASS=10;"
          " Stage22 events=%d; QC0 edits=518" % len(events),flush=True)
    if args.check:
        print("CHECK ONLY; no report files written.")
        return

    annotated=[]
    episode_map=defaultdict(list)
    seen=set()
    priority_counts=defaultdict(Counter)
    for row in events:
        site=row["site"]
        if site not in by22:raise RuntimeError("Unexpected Stage22 event site")
        key=(site,row["timestamp_local"])
        if key in seen:
            raise RuntimeError("Duplicate site/time in Stage22 event context: "+str(key))
        seen.add(key)
        flags=set(filter(None,row.get("review_flags","").split("|")))
        pri=priority(flags)
        priority_counts[site][pri]+=1
        new=dict(row,priority=pri,science_action="HOLD_MANUAL_EVIDENCE_REVIEW",
                 proposed_replacement="NONE",
                 reason_not_auto_approved="ERA_MATCH_IS_NOT_GROUND_TRUTH")
        annotated.append(new)
        episode_map[(site,row["episode_id"])].append(new)

    contexts=[]
    for (site,ep),subset in episode_map.items():
        reasons=Counter(f for row in subset for f in
                        filter(None,row["review_flags"].split("|")))
        pr=min((row["priority"] for row in subset))
        times=sorted(row["timestamp_local"] for row in subset)
        contexts.append(dict(site=site,episode_id=ep,
             first_time=times[0],last_time=times[-1],n_review_timestamps=len(subset),
             priority=pr,distinct_flags="|".join(sorted(reasons)),
             QC0_edited_timepoints=sum(int(row["QC0_modification_count"])>0 for row in subset),
             positive_RH_below1_timepoints=reasons["POSITIVE_RH_LT1PCT"],
             TA_vs_ERA_gt15_timepoints=reasons["TA_VS_ERA_GT15C"],
             existing_TA_jump_timepoints=reasons["CANDIDATE_TA_30MIN_JUMP_GT8C"],
             next_action="INVESTIGATE_NEARBY_RECORDS_SOURCE_AND_BIF_CONTEXT",
             decision="HOLD_NOT_APPROVED"))
    contexts.sort(key=lambda r:(r["priority"],-r["QC0_edited_timepoints"],
                                -r["positive_RH_below1_timepoints"],
                                -r["n_review_timestamps"],r["site"]))

    qc0_by_site=Counter(row["site"] for row in qc0)
    table=[]
    for site in SITES:
        r=by21[site];q=by22[site];counts=priority_counts[site]
        if qc0_by_site[site]!=intfield(q,"QC0_edits"):
            raise RuntimeError(site+": QC0 list count contradicts summary")
        table.append(dict(
            site=site,numeric_gate="PASS",
            review_timepoints=intfield(q,"review_timestamps"),
            review_episodes=intfield(q,"review_episodes"),
            qc0_modified_variable_time_records=intfield(q,"QC0_edits"),
            manual_review_log_records=intfield(r,"manual_review_records"),
            candidate_TA_jump_gt8=intfield(q,"CANDIDATE_TA_30MIN_JUMP_GT8C"),
            newly_created_TA_jump_gt8=intfield(q,"NEW_TA_30MIN_JUMP_GT8C"),
            candidate_TA_ERA_diff_gt15=intfield(q,"TA_VS_ERA_GT15C"),
            positive_RH_below1=intfield(q,"POSITIVE_RH_LT1PCT"),
            nonpositive_RH=intfield(q,"RH_NONPOSITIVE"),
            P1_review_timepoints=counts["P1_TARGETED_SCIENCE_REVIEW"],
            P2_review_timepoints=counts["P2_CONTEXT_SOURCE_REVIEW"],
            highest_review_priority=(
                "P1_TARGETED_SCIENCE_REVIEW" if counts["P1_TARGETED_SCIENCE_REVIEW"]
                else "P2_CONTEXT_SOURCE_REVIEW" if counts["P2_CONTEXT_SOURCE_REVIEW"]
                else "NO_STAGE22_EVENT_FLAGS"),
            science_status="HOLD_PENDING_SOURCE_CONTEXT_OR_ECOLOGY",
            next_step=(
                "CHECK_QC0_EDITS_AND_WINTER_EXTREMES" if site=="CA-LP1"
                else "CHECK_QC0_AND_TA_VPD_PAIRING" if site=="CA-Man"
                else "CHECK_USBAR_QC2_WINTER_RH_SENSITIVITY" if site=="US-Bar"
                else "CHECK_FOREST_GRID_PFT_AND_TA" if site in
                    ("CA-Cbo","CA-TP1","CA-TP3","CA-TP4")
                else "CHECK_DRY_GRASSLAND_LOW_RH_AND_PFT" if site=="US-Aud"
                else "CHECK_REVIEW_EPISODES_THEN_ZBOT_AND_PFT")
        ))
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output=args.report_root/("stage24_postv5_science_review_queue_"+stamp)
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/"ten_site_science_gate_matrix.csv",table,list(table[0]))
    write_csv(output/"ranked_review_episodes.csv",contexts,list(contexts[0]))
    write_csv(output/"ranked_timestamp_context.csv",
              sorted(annotated,key=lambda r:(r["priority"],r["site"],r["timestamp_local"])),
              list(annotated[0]))
    write_csv(output/"qc0_measurement_edits_for_manual_decision.csv",
              qc0,list(qc0[0]))

    print("STAGE24 SUMMARY: sites=10; episodes=%d; annotated_timesteps=%d; QC0=%d"%
          (len(contexts),len(annotated),len(qc0)),flush=True)
    for row in table:
        print("  %-7s QC0_edits=%4d episodes=%4d low_RH_lt1=%3d"
              " TA_jumps=%4d TA_ERA_diff=%4d"%
              (row["site"],row["qc0_modified_variable_time_records"],
               row["review_episodes"],row["positive_RH_below1"],
               row["candidate_TA_jump_gt8"],row["candidate_TA_ERA_diff_gt15"]),flush=True)
    print("REPORT DIR:",output,flush=True)
    print("GATE=HOLD_SCIENCE. Reports only; no candidate edits or DATM.")
    print("Do not automatically replace QC0 observations or arid-site low RH.")


if __name__=="__main__":
    main()

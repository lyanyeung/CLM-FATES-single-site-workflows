#!/usr/bin/env python3
"""Stage 13: rank UNAPPLIED VPD candidate episodes for scientific review.

Inputs are existing Stage12 candidate/episode CSVs and Stage07 paired event CSV.
This read-only report measures both boundary and internal 30-minute VPD
continuity, source/ERA context, and proposed RH. ALL candidates remain HOLD.
No raw FLUXMET, ERA5, NetCDF, forcing, surface, CIME or Slurm files are edited.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
STEP = timedelta(minutes=30)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def num(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def required_num(row, field):
    result = num(row.get(field))
    if result is None:
        raise ValueError("Missing/nonfinite %s in record %s" %
                         (field, row.get("timestamp_local", row.get("episode"))))
    return result


def timestamp(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def find_dir(root, pattern, required, explicit):
    if explicit is not None:
        p = explicit.expanduser()
        if not (p / required).is_file():
            raise RuntimeError("Missing report file: " + str(p / required))
        return p
    folders = sorted(x for x in root.glob(pattern)
                     if x.is_dir() and (x / required).is_file())
    if not folders:
        raise RuntimeError("Cannot find %s/%s in %s" %
                           (pattern, required, root))
    return folders[-1]


def source_qc_code(row, variable):
    code = num(row.get("source_" + variable + "_QC"))
    if code is None:
        return "UNAVAILABLE"
    return str(int(code)) if code in (0, 1, 2) else "OTHER"


def path_variation(data, col):
    return sum(abs(required_num(b, col) - required_num(a, col))
               for a, b in zip(data, data[1:]))


def path_max_step(data, col):
    return max((abs(required_num(b, col) - required_num(a, col))
                for a, b in zip(data, data[1:])), default=0.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", default="CA-Man")
    ap.add_argument("--report-root", type=Path, default=ROOT)
    ap.add_argument("--stage12-dir", type=Path)
    ap.add_argument("--stage07-dir", type=Path)
    ap.add_argument("--edge-worsen-hpa", type=float, default=2.0)
    ap.add_argument("--total-worsen-hpa", type=float, default=5.0)
    ap.add_argument("--step-alert-hpa", type=float, default=5.0)
    ap.add_argument("--low-rh-pct", type=float, default=10.0)
    args = ap.parse_args()
    if min(args.edge_worsen_hpa,args.total_worsen_hpa,
           args.step_alert_hpa,args.low_rh_pct) < 0:
        ap.error("All review thresholds must be nonnegative")

    stage12 = find_dir(args.report_root,
                       "stage12_candidate_context_" + args.site + "_*",
                       "candidate_episode_boundary_review.csv",
                       args.stage12_dir)
    stage07 = find_dir(args.report_root, "stage07_counterpart_*",
                       "paired_anomaly_events.csv", args.stage07_dir)
    candidates = read_csv(stage12 / "source_verified_unapplied_vpd_proposals.csv")
    episodes = read_csv(stage12 / "candidate_episode_boundary_review.csv")
    paired = read_csv(stage07 / "paired_anomaly_events.csv")
    if not candidates or not episodes:
        raise RuntimeError("Empty Stage12 candidate or episode CSV")
    paired_by_stamp = {}
    for row in paired:
        if row["site"] != args.site or row["source_flagged"] != "FLUXMET_HH":
            continue
        key = row["timestamp"]
        if key in paired_by_stamp:
            raise RuntimeError("Duplicate Stage07 site/source/time " + key)
        paired_by_stamp[key] = row

    candidates_by_stamp = {}
    for row in candidates:
        if row["site"] != args.site:
            raise RuntimeError("Unexpected site in Stage12 candidates: " + row["site"])
        key = row["timestamp_local"]
        if key in candidates_by_stamp:
            raise RuntimeError("Duplicate candidate timestamp " + key)
        counterpart = paired_by_stamp.get(key)
        if counterpart is None:
            raise RuntimeError("Candidate missing Stage07 source comparison: " + key)
        if not math.isclose(required_num(row, "proposed_VPD_hPa"),
                            required_num(counterpart, "other_VPD"),
                            rel_tol=1e-8, abs_tol=1e-6):
            raise RuntimeError("Candidate not equal to counterpart ERA VPD at "+key)
        if not math.isclose(required_num(row, "source_VPD_hPa"),
                            required_num(counterpart, "source_VPD"),
                            rel_tol=1e-8, abs_tol=1e-6):
            raise RuntimeError("Original VPD does not match Stage07 at "+key)
        if required_num(row, "original_QC") != 1:
            raise RuntimeError("Candidate not sourced from VPD QC=1 at "+key)
        candidates_by_stamp[key] = row

    annotated = []
    episode_records = []
    assigned = set()
    for er in episodes:
        if er["site"] != args.site:
            raise RuntimeError("Unexpected episode site "+er["site"])
        start, end = timestamp(er["first_local"]), timestamp(er["last_local"])
        subset = sorted(
            (timestamp(k), r) for k, r in candidates_by_stamp.items()
            if start <= timestamp(k) <= end
        )
        expected = int(required_num(er, "candidate_halfhours"))
        if len(subset) != expected:
            raise RuntimeError("Episode %s expected %d candidates, got %d" %
                               (er["episode"],expected,len(subset)))
        if any(b[0]-a[0] != STEP for a,b in zip(subset,subset[1:])):
            raise RuntimeError("Episode %s not consecutive half-hours" % er["episode"])
        if not subset or subset[0][0] != start or subset[-1][0] != end:
            raise RuntimeError("Episode %s endpoints mismatch" % er["episode"])
        rows = [r for _,r in subset]
        for dt, r in subset:
            key = r["timestamp_local"]
            if key in assigned:
                raise RuntimeError("Candidate belongs to multiple episodes: "+key)
            assigned.add(key)

        internal_old = path_variation(rows,"source_VPD_hPa")
        internal_new = path_variation(rows,"proposed_VPD_hPa")
        internal_delta = internal_new - internal_old
        max_old = path_max_step(rows,"source_VPD_hPa")
        max_new = path_max_step(rows,"proposed_VPD_hPa")
        edge_old = num(er.get("sum_boundary_jump_original_hPa"))
        edge_new = num(er.get("sum_boundary_jump_proposal_hPa"))
        edge_delta = edge_new - edge_old if edge_old is not None and edge_new is not None else None
        total_old = edge_old + internal_old if edge_old is not None else None
        total_new = edge_new + internal_new if edge_new is not None else None
        total_delta = total_new - total_old if total_old is not None and total_new is not None else None
        min_rh = min(required_num(r,"proposed_RH_pct") for r in rows)
        max_rh = max(required_num(r,"proposed_RH_pct") for r in rows)
        qc_ta = Counter()
        qc_pa = Counter()
        mismatch_ta = []
        mismatch_pa = []
        for r in rows:
            p = paired_by_stamp[r["timestamp_local"]]
            qc_ta[source_qc_code(p,"TA")] += 1
            qc_pa[source_qc_code(p,"PA")] += 1
            src_ta, era_ta = num(p.get("source_TA")), num(p.get("other_TA"))
            src_pa, era_pa = num(p.get("source_PA")), num(p.get("other_PA"))
            if src_ta is not None and era_ta is not None:
                mismatch_ta.append(abs(src_ta-era_ta))
            if src_pa is not None and era_pa is not None:
                mismatch_pa.append(abs(src_pa-era_pa))

        reasons = []
        if edge_delta is None:
            reasons.append("BOUNDARY_DATA_INCOMPLETE")
        elif edge_delta >= args.edge_worsen_hpa:
            reasons.append("BOUNDARY_SUM_INCREASE_GE_THRESHOLD")
        if total_delta is not None and total_delta >= args.total_worsen_hpa:
            reasons.append("TOTAL_VARIATION_INCREASE_GE_THRESHOLD")
        if max_new >= args.step_alert_hpa:
            reasons.append("PROPOSAL_INTERNAL_STEP_GE_THRESHOLD")
        if min_rh < args.low_rh_pct:
            reasons.append("PROPOSAL_RH_BELOW_THRESHOLD")
        if qc_ta["2"] or qc_pa["2"]:
            reasons.append("SOURCE_TA_OR_PA_QC2")
        if not reasons:
            reasons = ["GENERAL_MANUAL_REVIEW"]
        risk = ("ELEVATED_CONTEXT_REVIEW" if reasons != ["GENERAL_MANUAL_REVIEW"]
                else "ROUTINE_CONTEXT_REVIEW")
        item = dict(
            site=args.site,episode=er["episode"],
            start_local=er["first_local"],end_local=er["last_local"],
            halfhours=len(rows),duration_hours=len(rows)*0.5,
            boundary_sum_old_hPa=edge_old,boundary_sum_candidate_hPa=edge_new,
            boundary_delta_hPa=edge_delta,
            internal_variation_old_hPa=internal_old,
            internal_variation_candidate_hPa=internal_new,
            internal_delta_hPa=internal_delta,
            full_path_variation_old_hPa=total_old,
            full_path_variation_candidate_hPa=total_new,
            full_path_delta_hPa=total_delta,
            max_internal_step_old_hPa=max_old,
            max_internal_step_candidate_hPa=max_new,
            min_candidate_RH_pct=min_rh,max_candidate_RH_pct=max_rh,
            max_abs_TA_difference_vs_ERA_C=max(mismatch_ta,default=None),
            max_abs_PA_difference_vs_ERA_kPa=max(mismatch_pa,default=None),
            source_TA_QC_counts=";".join("%s:%d"%(k,v) for k,v in sorted(qc_ta.items())),
            source_PA_QC_counts=";".join("%s:%d"%(k,v) for k,v in sorted(qc_pa.items())),
            priority=risk,reasons="|".join(reasons),
            approval="HOLD_NOT_APPROVED_NOT_APPLIED")
        episode_records.append(item)
        for r in rows:
            annotated.append(dict(
                site=args.site,episode=er["episode"],
                timestamp_local=r["timestamp_local"],
                source_VPD_hPa=r["source_VPD_hPa"],
                candidate_VPD_hPa=r["proposed_VPD_hPa"],
                source_TA_C=r["source_TA_C"],
                candidate_RH_pct=r["proposed_RH_pct"],
                episode_priority=risk,episode_reasons="|".join(reasons),
                approval="HOLD_NOT_APPROVED_NOT_APPLIED"))

    if assigned != set(candidates_by_stamp):
        raise RuntimeError("%d candidate rows not assigned to an episode" %
                           len(set(candidates_by_stamp)-assigned))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = args.report_root / ("stage13_episode_risks_" + args.site + "_" + stamp)
    folder.mkdir(parents=True,exist_ok=False)
    episode_records.sort(key=lambda x:(
        x["priority"] != "ELEVATED_CONTEXT_REVIEW",
        -(x["full_path_delta_hPa"] if x["full_path_delta_hPa"] is not None else -1e99),
        -x["halfhours"]))
    write_csv(folder/"episode_context_risk_ranking.csv",episode_records,list(episode_records[0]))
    write_csv(folder/"all_candidate_rows_with_episode_risks.csv",annotated,list(annotated[0]))
    write_csv(folder/"elevated_episode_review_queue.csv",
              [r for r in episode_records if r["priority"]=="ELEVATED_CONTEXT_REVIEW"],
              list(episode_records[0]))

    category = Counter(r["priority"] for r in episode_records)
    increased_edges = sum(r["boundary_delta_hPa"] is not None and
                          r["boundary_delta_hPa"] >= args.edge_worsen_hpa
                          for r in episode_records)
    increased_paths = sum(r["full_path_delta_hPa"] is not None and
                          r["full_path_delta_hPa"] >= args.total_worsen_hpa
                          for r in episode_records)
    print("STAGE13 SUMMARY: site=%s verified_candidates=%d episodes=%d" %
          (args.site,len(annotated),len(episode_records)))
    print("Episode review priorities:",dict(category))
    print("Boundary sum increased by >= %.1f hPa: %d episodes" %
          (args.edge_worsen_hpa,increased_edges))
    print("Full-path total variation increased by >= %.1f hPa: %d episodes" %
          (args.total_worsen_hpa,increased_paths))
    print("Longest episode:",max(r["halfhours"] for r in episode_records),"halfhours")
    print("Top episode contexts for manual inspection:")
    for r in episode_records[:12]:
        print("  %s -> %s n=%d edge_delta=%s full_path_delta=%s min_RH=%.2f%% %s" %
              (r["start_local"],r["end_local"],r["halfhours"],
               "%.2f"%r["boundary_delta_hPa"] if r["boundary_delta_hPa"] is not None else "NA",
               "%.2f"%r["full_path_delta_hPa"] if r["full_path_delta_hPa"] is not None else "NA",
               r["min_candidate_RH_pct"],r["reasons"]))
    print("REPORT DIR:",folder)
    print("ALL candidate changes remain HOLD. No forcing/source/model changes.")
    print("Thresholds rank manual reviews only; they do not approve correction.")


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""AmeriFlux Batch 01 Stage 09: read-only severity, QC and episode audit.

Input: Stage07 paired_anomaly_events.csv, NOT raw FLUXMET/ERA5 packages.
This is an exploratory physical screen (RH relative to liquid water), not
evidence that ERA5 is an independent truth source or a replacement policy.

No original source, surface, DATM or CIME data are modified.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPORTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
MET = ("TA", "VPD", "PA", "SW_IN", "LW_IN", "WS", "P")
HUM_FLAGS = {"EA_NONPOSITIVE", "SUPERSATURATION", "Q_SPECIFIC_INVALID",
             "HUMIDITY_UNCOMPUTABLE"}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, data, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def num(value):
    try:
        out = float(value)
    except (ValueError, TypeError):
        return None
    return out if math.isfinite(out) else None


def flagset(value):
    return {x for x in (value or "").split("|") if x}


def qc_status(value):
    v = num(value)
    if v is None:
        return "QC_UNAVAILABLE"
    if v == 0:
        return "QC0_MEASURED"
    if v == 1:
        return "QC1_GAPFILLED"
    if v == 2:
        return "QC2_ERA_BASED"
    return "QC_OTHER"


def severity(flags, rh):
    if any(x.endswith("_RANGE") for x in flags):
        return "RANGE_FAIL"
    if "EA_NONPOSITIVE" in flags or (rh is not None and rh <= 0):
        return "RH_NONPOSITIVE"
    if rh is not None and rh > 105:
        return "RH_SUPERSAT_GT105"
    if rh is not None and rh > 102:
        return "RH_SUPERSAT_102_TO105"
    if rh is not None and rh > 101:
        return "RH_SUPERSAT_101_TO102"
    if "Q_SPECIFIC_INVALID" in flags:
        return "Q_PHYSICAL_OUTSIDE_RANGE"
    if "HUMIDITY_UNCOMPUTABLE" in flags:
        return "HUMIDITY_UNCOMPUTABLE"
    return "OTHER_FLAGGED_EVENT"


def exact_core_match(row):
    """Equality of the three humidity drivers is evidence of shared values,
    NOT proof of identical data lineage."""
    for v in ("TA", "VPD", "PA"):
        a, b = num(row.get("source_"+v)), num(row.get("other_"+v))
        if a is None or b is None or not math.isclose(a, b, abs_tol=1e-8, rel_tol=0):
            return False
    return True


def affected_qc(row, flags):
    vars_ = set()
    if flags & HUM_FLAGS:
        vars_.update(("TA", "VPD", "PA"))
    for v in MET:
        if v+"_RANGE" in flags:
            vars_.add(v)
    return {v:qc_status(row.get("source_"+v+"_QC")) for v in sorted(vars_)}


def report_dir(reports, explicit):
    if explicit:
        source = explicit.expanduser()
    else:
        choices = sorted(p for p in reports.glob("stage07_counterpart_*")
                         if (p / "paired_anomaly_events.csv").is_file())
        if not choices:
            raise RuntimeError("Stage07 paired report missing in "+str(reports))
        source = choices[-1]
    if not (source / "paired_anomaly_events.csv").is_file():
        raise RuntimeError("Stage07 paired_anomaly_events.csv missing at "+str(source))
    return source


def analyze(rows):
    event_rows = []
    grouped = defaultdict(list)
    by_site = defaultdict(Counter)
    qc_tally = Counter()
    source_flags = Counter()
    severity_counts = Counter()
    all_keys = set()
    paired_site_times = defaultdict(set)

    for row in rows:
        site = row["site"]
        source = row["source_flagged"]
        timestamp = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M")
        key = (site, source, timestamp)
        if key in all_keys:
            raise RuntimeError("Duplicate Stage07 source event: "+str(key))
        all_keys.add(key)
        paired_site_times[(site, timestamp)].add(source)
        flags = flagset(row["flagged_categories"])
        other_flags = flagset(row["counterpart_categories"])
        rh = num(row.get("source_RH_pct"))
        rh_other = num(row.get("other_RH_pct"))
        grade = severity(flags, rh)
        qcs = affected_qc(row, flags)
        core_same = exact_core_match(row)
        comp = row["comparison_class"]
        counterpart_pass = comp == "COUNTERPART_PASSES_SAME_CHECKS"
        qc2_humidity = any(qcs.get(v) == "QC2_ERA_BASED"
                           for v in ("TA","VPD","PA"))
        # Context only: no automatic replacement follows from this label.
        review = ("SHARED_SOURCE_ALERT" if comp=="SAME_PHYSICAL_FLAG_IN_BOTH"
                  else "ORIGINAL_VS_COUNTERPART_UNRESOLVED")
        if core_same:
            review += "|IDENTICAL_TA_VPD_PA"
        if qc2_humidity:
            review += "|FLUXMET_QC2_OR_COMPANION_ERA_QC2"
        if rh is not None and rh < 0:
            review += "|NEGATIVE_RH"
        if counterpart_pass:
            review += "|COUNTERPART_NOT_FLAGGED"
        rec = {
            "site":site, "source":source,
            "timestamp_local":timestamp.strftime("%Y-%m-%d %H:%M"),
            "severity":grade, "flags":"|".join(sorted(flags)),
            "counterpart_flags":"|".join(sorted(other_flags)),
            "comparison_class":comp,
            "RH_source_pct":rh if rh is not None else "",
            "RH_counterpart_pct":rh_other if rh_other is not None else "",
            "RH_delta_percentage_points":(rh-rh_other if rh is not None and
                                           rh_other is not None else ""),
            "same_TA_VPD_PA_values":str(core_same),
            "TA_QC":qcs.get("TA","NOT_TRIGGERED"),
            "VPD_QC":qcs.get("VPD","NOT_TRIGGERED"),
            "PA_QC":qcs.get("PA","NOT_TRIGGERED"),
            "other_affected_QC":";".join(v+"="+qc for v,qc in qcs.items()
                                         if v not in ("TA","VPD","PA")),
            "triage":review,
            "decision":"HOLD_SCIENTIFIC_REVIEW_NO_AUTO_REPLACEMENT",
        }
        event_rows.append(rec)
        grouped[(site,source)].append((timestamp,rec))
        counts = by_site[(site,source)]
        counts["EVENTS"] += 1
        counts[grade] += 1
        if core_same: counts["IDENTICAL_CORE"] += 1
        if comp=="SAME_PHYSICAL_FLAG_IN_BOTH": counts["SHARED_PHYSICAL"] += 1
        if counterpart_pass: counts["COUNTERPART_PASSES_SCREEN"] += 1
        if qc2_humidity: counts["QC2_HUMIDITY_DRIVER"] += 1
        for v, status in qcs.items():
            qc_tally[(site,source,v,status)] += 1
        source_flags.update(flags)
        severity_counts[grade] += 1

    episodes = []
    for (site,source), events in sorted(grouped.items()):
        events.sort(key=lambda x:x[0])
        run = []
        def append_episode(batch):
            if not batch:
                return
            grades = Counter(r["severity"] for _,r in batch)
            episodes.append({
                "site":site, "source":source,
                "start_local":batch[0][0].strftime("%Y-%m-%d %H:%M"),
                "end_local":batch[-1][0].strftime("%Y-%m-%d %H:%M"),
                "consecutive_flagged_halfhours":len(batch),
                "duration_hours_as_steps":len(batch)*0.5,
                "severity_counts":";".join(k+":"+str(v)
                                            for k,v in sorted(grades.items())),
            })
        for tm, rec in events:
            if run and tm - run[-1][0] != timedelta(minutes=30):
                append_episode(run)
                run = []
            run.append((tm,rec))
        append_episode(run)

    site_rows = []
    for (site,source), counts in sorted(by_site.items()):
        site_rows.append({
            "site":site, "source":source, "events":counts["EVENTS"],
            "rh_nonpositive":counts["RH_NONPOSITIVE"],
            "rh_supersat_101_102":counts["RH_SUPERSAT_101_TO102"],
            "rh_supersat_102_105":counts["RH_SUPERSAT_102_TO105"],
            "rh_supersat_gt105":counts["RH_SUPERSAT_GT105"],
            "q_invalid_other":counts["Q_PHYSICAL_OUTSIDE_RANGE"],
            "hard_range":counts["RANGE_FAIL"],
            "identical_TA_VPD_PA":counts["IDENTICAL_CORE"],
            "counterpart_passes_screen":counts["COUNTERPART_PASSES_SCREEN"],
            "both_physical_flagged":counts["SHARED_PHYSICAL"],
            "affected_humidity_has_QC2":counts["QC2_HUMIDITY_DRIVER"],
        })
    n_double = sum(len(sources)==2 for sources in paired_site_times.values())
    if len(rows) != len(paired_site_times)+n_double:
        raise RuntimeError("Site-time/source pairing count mismatch")
    return (event_rows, site_rows, episodes, qc_tally, severity_counts,
            source_flags, n_double, len(paired_site_times))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    p.add_argument("--stage07-dir",type=Path)
    p.add_argument("--top-episodes",type=int,default=12)
    args = p.parse_args()
    source = report_dir(args.report_root,args.stage07_dir)
    rows = read_csv(source/"paired_anomaly_events.csv")
    if not rows:
        raise RuntimeError("Stage07 report contains no events")
    needed = {"site","timestamp","source_flagged","comparison_class",
              "flagged_categories","counterpart_categories"}
    if not needed.issubset(rows[0]):
        raise RuntimeError("Stage07 missing fields: "+str(needed-set(rows[0])))
    result = analyze(rows)
    (events, sites, episodes, qc_tally, sev, flag_counts,
     both, unique_times) = result
    now=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder=args.report_root/("stage09_humidity_severity_"+now)
    folder.mkdir(parents=True,exist_ok=False)
    write_csv(folder/"event_severity_and_source_qc.csv",events,list(events[0]))
    write_csv(folder/"site_source_summary.csv",sites,list(sites[0]))
    episodes.sort(key=lambda r:(-r["consecutive_flagged_halfhours"],
                                r["site"],r["source"],r["start_local"]))
    write_csv(folder/"consecutive_anomaly_episodes.csv",episodes,list(episodes[0]))
    qc_rows=[dict(site=s,source=src,variable=v,qc_label=q,events=n)
             for (s,src,v,q),n in sorted(qc_tally.items())]
    write_csv(folder/"affected_variable_qc_provenance.csv",qc_rows,
              ["site","source","variable","qc_label","events"])
    print("STAGE09 SUMMARY: %d flagged source rows; %d site-local timestamps; "
          "%d both-source-flagged timepoints" % (len(rows),unique_times,both))
    print("RH severity and physical-range categories:",dict(sev))
    print("Original source flags (non-exclusive):",dict(flag_counts))
    print("CONTIGUOUS EPISODES:",len(episodes),"longest",episodes[0]["consecutive_flagged_halfhours"],
          "half-hours" if episodes else "")
    for rec in episodes[:args.top_episodes]:
        print("  %-7s %-11s %5d halfhours %s to %s (%s)" %
              (rec["site"],rec["source"],rec["consecutive_flagged_halfhours"],
               rec["start_local"],rec["end_local"],rec["severity_counts"]))
    for rec in sites:
        print("  %-7s %-11s events=%4d RH<=0=%4d RH>105=%3d range=%3d QC2humidity=%4d identical_core=%4d" %
              (rec["site"],rec["source"],rec["events"],rec["rh_nonpositive"],
               rec["rh_supersat_gt105"],rec["hard_range"],
               rec["affected_humidity_has_QC2"],rec["identical_TA_VPD_PA"]))
    print("REPORT DIR:",folder)
    print("READ ONLY. Every event remains HOLD; no automatic ERA substitution.")
    print("RH uses the original liquid-water VPD convention, not an ice-corrected diagnosis.")


if __name__=="__main__":
    main()

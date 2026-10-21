#!/usr/bin/env python3
"""Stage 11: conservative AmeriFlux FLUXMET VPD-repair CANDIDATE screening.

READ-ONLY to science/model input: consumes Stage07 paired anomaly report, and
writes only small CSV decision tables. No raw CSV, surface, DATM, Slurm/CIME
case or forcing is edited. No candidate is approved or applied.

Scientific assumptions used ONLY for preliminary screening:
- TA degrees Celsius, VPD hPa, PA kPa, relative humidity over liquid water.
- A negative calculated vapour pressure (VPD > es(TA)) is nonphysical.
- For a proposed VPD-only sensitivity candidate, keep source FLUXMET TA/PA,
  and test ERA5_HH VPD against BOTH source TA and ERA5 TA.
- Existing source VPD must have QC=1 ("official gapfilled"); measured QC=0,
  ERA-sourced QC=2, unknown QC, small excess and shared anomalies stay HOLD.
- Both sources may share provenance: a successful screen does NOT validate ERA.

The proposed VPD from ERA is NOT written to forcing, and no RH clipping occurs.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
BOUNDS = {"TA":(-80.0,65.0),"VPD":(-0.1,125.0),"PA":(50.0,110.0),
          "SW_IN":(-5.0,1600.0),"LW_IN":(60.0,800.0),
          "WS":(-0.1,75.0),"P":(-0.001,300.0)}
SOURCE_NAMES = {"FLUXMET_HH", "ERA5_HH"}


def parse_csv(path):
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_number(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def qc_code(text):
    n = to_number(text)
    if n is None or n not in (0, 1, 2):
        return "UNKNOWN"
    return str(int(n))


def good(name, value):
    low, high = BOUNDS[name]
    return value is not None and low <= value <= high


def es_hpa(temperature):
    if temperature is None or not (-80 <= temperature <= 65):
        return None
    exponent = 17.67 * temperature / (temperature + 243.5)
    return 6.112 * math.exp(exponent)


def vapour_stats(ta, vpd, pa):
    if not good("TA", ta) or not good("PA", pa) or vpd is None:
        return None
    es = es_hpa(ta)
    ea = es - vpd
    p = pa * 1000.0
    denom = p - 0.378 * ea * 100.0
    if denom <= 0:
        return None
    q = 0.622 * ea * 100.0 / denom
    return dict(es=es, ea=ea, RH=100.0*ea/es, Q=q, excess=vpd-es)


def source_values(row, prefix):
    return {v: to_number(row.get(prefix + v)) for v in BOUNDS}


def category(row, min_excess, max_ta_diff, max_pa_diff):
    flagset = set(filter(None, row["flagged_categories"].split("|")))
    source = source_values(row, "source_")
    other = source_values(row, "other_")
    orig = vapour_stats(source["TA"], source["VPD"], source["PA"])
    comp = vapour_stats(other["TA"], other["VPD"], other["PA"])
    result = {
        "site":row["site"], "timestamp_local":row["timestamp"],
        "flagged_source":row["source_flagged"],
        "flagged_categories":row["flagged_categories"],
        "comparison_class":row["comparison_class"],
        "original_VPD_QC":qc_code(row.get("source_VPD_QC")),
        "original_TA_QC":qc_code(row.get("source_TA_QC")),
        "original_PA_QC":qc_code(row.get("source_PA_QC")),
        "counterpart_VPD_QC":qc_code(row.get("other_VPD_QC")),
        "original_TA_C":source["TA"],
        "original_PA_kPa":source["PA"],
        "original_VPD_hPa":source["VPD"],
        "counterpart_TA_C":other["TA"],
        "counterpart_PA_kPa":other["PA"],
        "counterpart_VPD_hPa":other["VPD"],
        "original_excess_hPa":orig["excess"] if orig else None,
        "original_RH_pct":orig["RH"] if orig else None,
        "original_Q_kgkg":orig["Q"] if orig else None,
        "candidate_VPD_hPa":None, "candidate_RH_pct":None,
        "candidate_Q_kgkg":None, "delta_VPD_hPa":None,
        "candidate_independent_validation":"NOT_ESTABLISHED",
        "approval":"NOT_APPROVED_NOT_APPLIED",
    }
    if row["source_flagged"] != "FLUXMET_HH":
        result["decision"]="ERA_ANOMALY_HOLD_NOT_TOWER_REPAIR"
        return result

    if any(x.endswith("_RANGE") for x in flagset):
        decision="HOLD_OTHER_VARIABLE_RANGE"
    elif not orig:
        decision="HOLD_ORIGINAL_CORE_INVALID"
    elif orig["ea"] > 0:
        decision="HOLD_NOT_EA_NONPOSITIVE"
    elif orig["excess"] <= min_excess:
        decision="REVIEW_NEAR_SATURATION_BOUNDARY"
    elif result["original_VPD_QC"] != "1":
        decision="REVIEW_VPD_QC_NOT_GAPFILLED"
    elif result["original_TA_QC"] == "2" or result["original_PA_QC"] == "2":
        decision="REVIEW_ORIGINAL_TA_PA_ERA_DERIVED"
    elif row["comparison_class"] != "COUNTERPART_PASSES_SAME_CHECKS":
        decision="HOLD_COUNTERPART_PHYSICAL_FLAG"
    elif not all(good(v, other[v]) for v in ("TA","PA","VPD")) or comp is None:
        decision="HOLD_COUNTERPART_CORE_INVALID"
    elif other["VPD"] < 0 or comp["ea"] <= 0 or comp["Q"] < 0 or comp["Q"] > .08:
        decision="HOLD_COUNTERPART_HUMIDITY_INVALID"
    elif abs(source["TA"]-other["TA"]) > max_ta_diff:
        decision="REVIEW_LARGE_TEMPERATURE_DISAGREEMENT"
    elif abs(source["PA"]-other["PA"]) > max_pa_diff:
        decision="REVIEW_LARGE_PRESSURE_DISAGREEMENT"
    else:
        alternate = vapour_stats(source["TA"], other["VPD"], source["PA"])
        if not alternate or alternate["ea"] <= 0 or alternate["Q"] < 0 or alternate["Q"] > .08:
            decision="HOLD_ERA_VPD_INVALID_WITH_TOWER_TA"
        else:
            decision="PROPOSAL_VPD_ONLY_MANUAL_APPROVAL_REQUIRED"
            result["candidate_VPD_hPa"]=other["VPD"]
            result["candidate_RH_pct"]=alternate["RH"]
            result["candidate_Q_kgkg"]=alternate["Q"]
            result["delta_VPD_hPa"]=other["VPD"]-source["VPD"]
    result["decision"]=decision
    return result


def write_csv(path, entries, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)


def select_report(root, chosen):
    if chosen:
        folder=chosen.expanduser()
    else:
        dirs=sorted(p for p in root.glob("stage07_counterpart_*")
                    if (p/"paired_anomaly_events.csv").is_file())
        if not dirs:
            raise RuntimeError("No Stage07 counterpart report under " + str(root))
        folder=dirs[-1]
    if not (folder/"paired_anomaly_events.csv").is_file():
        raise RuntimeError("Missing Stage07 paired CSV: "+str(folder))
    return folder


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root",type=Path,default=DEFAULT_ROOT)
    parser.add_argument("--stage07-dir",type=Path)
    parser.add_argument("--min-excess-hpa",type=float,default=0.1,
                        help="Near-boundary humidity excess <= this remains review only")
    parser.add_argument("--max-ta-diff-c",type=float,default=8.0)
    parser.add_argument("--max-pa-diff-kpa",type=float,default=15.0)
    args=parser.parse_args()
    if args.min_excess_hpa<0 or args.max_ta_diff_c<0 or args.max_pa_diff_kpa<0:
        parser.error("Thresholds must be nonnegative")
    source=select_report(args.report_root,args.stage07_dir)
    rows=parse_csv(source/"paired_anomaly_events.csv")
    if not rows:
        raise RuntimeError("Empty Stage07 report")
    required={"site","timestamp","source_flagged","flagged_categories",
              "comparison_class","source_VPD","source_TA","source_PA",
              "other_VPD","other_TA","other_PA"}
    if not required.issubset(rows[0]):
        raise RuntimeError("Missing required Stage07 fields: "+str(required-set(rows[0])))
    ledger=[]
    by_site=defaultdict(Counter)
    decisions=Counter()
    seen=set()
    for row in rows:
        key=(row["site"],row["timestamp"],row["source_flagged"])
        if key in seen:
            raise RuntimeError("Duplicate source event key: "+str(key))
        seen.add(key)
        if row["source_flagged"] not in SOURCE_NAMES:
            raise RuntimeError("Unexpected source: "+row["source_flagged"])
        decision=category(row,args.min_excess_hpa,
                          args.max_ta_diff_c,args.max_pa_diff_kpa)
        ledger.append(decision)
        by_site[row["site"]][decision["decision"]]+=1
        by_site[row["site"]][row["source_flagged"]]+=1
        decisions[decision["decision"]]+=1
    # Stage07 has one row per flagged source/site/timestamp. A proposal is
    # always preliminary: NO edits to the recorded meteorology are performed.
    proposals=[x for x in ledger if x["decision"]==
               "PROPOSAL_VPD_ONLY_MANUAL_APPROVAL_REQUIRED"]
    summary=[]
    for site in sorted(by_site):
        c=by_site[site]
        summary.append({
            "site":site,
            "FLUXMET_flagged":c["FLUXMET_HH"],
            "ERA5_flagged":c["ERA5_HH"],
            "VPD_only_screened_proposals":c["PROPOSAL_VPD_ONLY_MANUAL_APPROVAL_REQUIRED"],
            "near_boundary_review":c["REVIEW_NEAR_SATURATION_BOUNDARY"],
            "QC_not_gapfilled_review":c["REVIEW_VPD_QC_NOT_GAPFILLED"],
            "counterpart_holds":c["HOLD_COUNTERPART_PHYSICAL_FLAG"],
            "other_holds":c["FLUXMET_HH"] -
                c["PROPOSAL_VPD_ONLY_MANUAL_APPROVAL_REQUIRED"] -
                c["REVIEW_NEAR_SATURATION_BOUNDARY"] -
                c["REVIEW_VPD_QC_NOT_GAPFILLED"] -
                c["HOLD_COUNTERPART_PHYSICAL_FLAG"],
        })
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage11_vpd_candidates_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    fieldnames=list(ledger[0])
    write_csv(out/"all_flagged_source_event_decisions.csv",ledger,fieldnames)
    write_csv(out/"provisional_VPD_only_candidates_NOT_APPLIED.csv",proposals,fieldnames)
    write_csv(out/"site_screening_summary.csv",summary,list(summary[0]))
    print("STAGE11 SUMMARY: %d paired anomaly-source events (%d FLUXMET, %d ERA5)" %
          (len(ledger),sum(x["FLUXMET_flagged"] for x in summary),
           sum(x["ERA5_flagged"] for x in summary)))
    print("Screened VPD-only proposals (NOT approved/applied):",len(proposals))
    print("Screening thresholds: excess > %.3f hPa, |TA difference| <= %.2f C, "
          "|PA difference| <= %.2f kPa" %
          (args.min_excess_hpa,args.max_ta_diff_c,args.max_pa_diff_kpa))
    for k,v in decisions.most_common():
        print("  %-49s %d" % (k,v))
    for site in summary:
        print("  %-7s FLUXMET=%4d ERA5=%4d VPD_proposals=%4d small_excess=%4d QC_review=%4d" %
              (site["site"],site["FLUXMET_flagged"],site["ERA5_flagged"],
               site["VPD_only_screened_proposals"],site["near_boundary_review"],
               site["QC_not_gapfilled_review"]))
    print("REPORT DIR:",out)
    print("ALL events HOLD; candidates are for sensitivity planning, not approved corrections.")
    print("NO raw-source, forcing, surface, DATM, CIME case or Slurm changes.")


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage 10: READ-ONLY AmeriFlux VPD/saturation and TA-VPD-PA source-QC diagnosis.

Uses Stage07 paired_anomaly_events.csv; NO reprocessing of original large CSV.
VPD and saturation vapour pressure are in hPa, TA in Celsius, PA in kPa.
Relative humidity uses saturation over LIQUID water for consistency with the
previous Stage04-09 audit; alternative saturation schemes are not repairs.
All events remain HOLD. No input or CIME/model files are modified.
"""
import argparse
import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
MET=("TA","VPD","PA","SW_IN","LW_IN","WS","P")
HUM={"EA_NONPOSITIVE","SUPERSATURATION","Q_SPECIFIC_INVALID","HUMIDITY_UNCOMPUTABLE"}
BUCKETS=("VPD_LE_ES","EXCESS_0_0.01hPa","EXCESS_0.01_0.1hPa",
         "EXCESS_0.1_0.5hPa","EXCESS_0.5_1hPa","EXCESS_GT_1hPa","NOT_CALCULABLE")


def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path,items,fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)


def numeric(x):
    try:
        v=float(x)
    except (ValueError,TypeError):
        return None
    return v if math.isfinite(v) else None


def qc(x):
    v=numeric(x)
    return "QC"+str(int(v)) if v in (0,1,2) else ("NA" if v is None else "OTHER")


def calculate(t,vpd,pa):
    if None in (t,vpd,pa):
        return None
    try:
        es=6.112*math.exp(max(-40,min(40,17.67*t/(t+243.5))))
        ea=es-vpd
        p=pa*1000
        q=.622*(100*ea)/(p-.378*(100*ea))
        return dict(es=es,ea=ea,RH=100*ea/es,Q=q,
                    ratio=vpd/es,excess=vpd-es)
    except (ValueError,OverflowError,ZeroDivisionError):
        return None


def bucket(x):
    if x is None: return "NOT_CALCULABLE"
    if x<=0: return "VPD_LE_ES"
    if x<=.01: return "EXCESS_0_0.01hPa"
    if x<=.1: return "EXCESS_0.01_0.1hPa"
    if x<=.5: return "EXCESS_0.1_0.5hPa"
    if x<=1: return "EXCESS_0.5_1hPa"
    return "EXCESS_GT_1hPa"


def source_dir(root,explicit):
    if explicit:
        choice=explicit.expanduser()
    else:
        folders=sorted(p for p in root.glob("stage07_counterpart_*")
                       if (p/"paired_anomaly_events.csv").is_file())
        if not folders:
            raise RuntimeError("Stage07 report not found: "+str(root))
        choice=folders[-1]
    if not (choice/"paired_anomaly_events.csv").is_file():
        raise RuntimeError("Missing Stage07 event CSV: "+str(choice))
    return choice


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report-root",type=Path,default=ROOT)
    p.add_argument("--stage07-dir",type=Path)
    p.add_argument("--examples",type=int,default=12)
    a=p.parse_args()
    if a.examples<0: p.error("--examples must be >=0")
    source=source_dir(a.report_root,a.stage07_dir)
    rows=read(source/"paired_anomaly_events.csv")
    if not rows: raise RuntimeError("Stage07 event report empty")
    required={"site","source_flagged","timestamp","flagged_categories",
              "comparison_class","source_TA","source_VPD","source_PA"}
    if not required.issubset(rows[0]):
        raise RuntimeError("Stage07 missing required fields: "+str(required-set(rows[0])))

    seen=set()
    events=[]
    summaries=defaultdict(Counter)
    qc_patterns=defaultdict(Counter)
    samples=[]
    for row in rows:
        site,src,ts=row["site"],row["source_flagged"],row["timestamp"]
        unique=(site,src,ts)
        if unique in seen: raise RuntimeError("Duplicate source/timestamp: "+str(unique))
        seen.add(unique)
        flags=set(filter(None,row["flagged_categories"].split("|")))
        vals={v:numeric(row.get("source_"+v)) for v in MET}
        other={v:numeric(row.get("other_"+v)) for v in MET}
        source_calc=calculate(vals["TA"],vals["VPD"],vals["PA"])
        other_calc=calculate(other["TA"],other["VPD"],other["PA"])
        equal={v:(vals[v] is not None and other[v] is not None and
                  math.isclose(vals[v],other[v],rel_tol=0,abs_tol=1e-8))
               for v in ("TA","VPD","PA")}
        qcs={v:qc(row.get("source_"+v+"_QC")) for v in ("TA","VPD","PA")}
        triplet="|".join(qcs[v] for v in ("TA","VPD","PA"))
        qc_patterns[(site,src)][triplet]+=1
        c=summaries[(site,src)]
        c["events"]+=1
        hum=bool(flags&HUM)
        if hum: c["humidity_flagged"]+=1
        if any(f.endswith("_RANGE") for f in flags): c["range_flagged"]+=1
        b=bucket(source_calc["excess"] if source_calc else None)
        c[b]+=1
        if source_calc:
            if source_calc["RH"]<=0: c["rh_le_zero"]+=1
            if vals["TA"]<0: c["below_zero_C"]+=1
            if hum and source_calc["ratio"]>2: c["vpd_over_2x_es"]+=1
        if hum and ts[5:7] in ("12","01","02"): c["humidity_in_DJF"]+=1
        for v in equal:
            if equal[v]: c["equal_"+v]+=1
        if all(equal.values()): c["equal_all_core"]+=1
        if row["comparison_class"]=="SAME_PHYSICAL_FLAG_IN_BOTH":
            c["same_physical_flag_both"]+=1
        record=dict(
            site=site,source=src,timestamp_local=ts,
            flagged_categories=row["flagged_categories"],
            comparison_class=row["comparison_class"],
            TA_C=vals["TA"],VPD_hPa=vals["VPD"],PA_kPa=vals["PA"],
            counterpart_TA_C=other["TA"],counterpart_VPD_hPa=other["VPD"],
            TA_QC=qcs["TA"],VPD_QC=qcs["VPD"],PA_QC=qcs["PA"],
            TA_equal=equal["TA"],VPD_equal=equal["VPD"],PA_equal=equal["PA"],
            sat_vapour_pressure_hPa=(source_calc["es"] if source_calc else ""),
            actual_vapour_pressure_hPa=(source_calc["ea"] if source_calc else ""),
            RH_pct=(source_calc["RH"] if source_calc else ""),
            vpd_over_es=(source_calc["ratio"] if source_calc else ""),
            excess_vpd_hPa=(source_calc["excess"] if source_calc else ""),
            excess_bucket=b,
            other_RH_pct=(other_calc["RH"] if other_calc else ""),
            QC_triplet=triplet,
            decision="HOLD_NO_AUTOMATIC_REPLACEMENT")
        events.append(record)
        if hum and source_calc and source_calc["excess"]>0:
            samples.append(record)

    summary=[]
    for (site,src),counts in sorted(summaries.items()):
        item=dict(site=site,source=src,
                  events=counts["events"],
                  humidity=counts["humidity_flagged"],
                  ranges=counts["range_flagged"],
                  RH_le_zero=counts["rh_le_zero"],
                  source_TA_below_0C=counts["below_zero_C"],
                  vpd_greater_2x_es=counts["vpd_over_2x_es"],
                  humidity_DJF=counts["humidity_in_DJF"],
                  equal_TA=counts["equal_TA"],
                  equal_VPD=counts["equal_VPD"],
                  equal_PA=counts["equal_PA"],
                  equal_all_TA_VPD_PA=counts["equal_all_core"],
                  same_physical_flag_both=counts["same_physical_flag_both"])
        item.update({k:counts[k] for k in BUCKETS})
        summary.append(item)
    qc_rows=[dict(site=site,source=src,TA_VPD_PA_QC=pattern,events=n)
             for (site,src),patterns in sorted(qc_patterns.items())
             for pattern,n in patterns.most_common()]
    samples.sort(key=lambda x:x["excess_vpd_hPa"],reverse=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=a.report_root/("stage10_vpd_excess_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    write(out/"vpd_excess_event_diagnostics.csv",events,list(events[0]))
    write(out/"site_source_vpd_excess_summary.csv",summary,list(summary[0]))
    write(out/"TA_VPD_PA_QC_patterns.csv",qc_rows,
          ["site","source","TA_VPD_PA_QC","events"])
    write(out/"top_vpd_excess_examples.csv",samples[:200],list(events[0]))
    print("STAGE10 SUMMARY: %d source events; %d site-source groups" %
          (len(events),len(summary)))
    print("SOURCE REPORT:",source)
    for r in summary:
        print("%-7s %-11s events=%4d RH<=0=%4d excess>1hPa=%4d VPD>2*es=%4d TA<0=%4d equal(T,V,P)=(%d,%d,%d)" %
              (r["site"],r["source"],r["events"],r["RH_le_zero"],
               r["EXCESS_GT_1hPa"],r["vpd_greater_2x_es"],
               r["source_TA_below_0C"],r["equal_TA"],r["equal_VPD"],r["equal_PA"]))
    print("TOP VPD EXCESS EXAMPLES:",min(a.examples,len(samples)))
    for e in samples[:a.examples]:
        print("%s %-11s %s TA=%sC VPD=%shPa es=%.3fhPa EXCESS=%.3fhPa VPD_QC=%s other_VPD=%s" %
              (e["site"],e["source"],e["timestamp_local"],e["TA_C"],
               e["VPD_hPa"],e["sat_vapour_pressure_hPa"],
               e["excess_vpd_hPa"],e["VPD_QC"],e["counterpart_VPD_hPa"]))
    print("REPORT DIR:",out)
    print("READ-ONLY. No source meteorology, surface, DATM or Slurm modifications.")
    print("All proposed corrections remain HOLD pending site-specific review.")


if __name__=="__main__":
    main()

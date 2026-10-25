#!/usr/bin/env python3
"""Stage11: verify existing Batch05 Stage10 report-only CSV/JSON and triage.

No model, forcing, source or report writes. This only READS the existing
Stage10 output directory. Source RH is not presumed independent; a bracketed
interpolation is not proof of a valid VPD repair.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import re

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
       "US-WCr","US-Whs","US-Wjs","US-Wkg")
EXPECTED={"US-UiD":0,"US-UMB":23,"US-UMd":15,"US-Var":62,
          "US-Vcm":509,"US-Vcp":629,"US-WCr":88,"US-Whs":1,
          "US-Wjs":401,"US-Wkg":22}
REQUIRED=("time","class","RH_derived_pct","RH_original_pct","TA_F_C",
 "VPD_F_hPa","TA_F_QC","VPD_F_QC","TA_MDS_C","VPD_MDS_hPa",
 "TA_MDS_QC","VPD_MDS_QC","TA_ERA_C","VPD_ERA_hPa",
 "MDS_pair_physics","ERA_pair_physics",
 "hypothetical_ERA_e_with_tower_T_vpd_hPa",
 "left_measured_anchor_time","left_measured_anchor_vpd",
 "right_measured_anchor_time","right_measured_anchor_vpd",
 "interpolated_measured_vpd_hPa","interpolation_diagnostic",
 "SCIENCE_APPROVAL")
INTERP=("UNAPPROVED_MATH_FEASIBLE",
        "NO_BOTH_QC0_ANCHORS_WITHIN_3H",
        "INTERPOLATION_NONPHYSICAL")

def num(s):
    try:
        v=float(s)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):
        return None

def es(t):
    return 6.112*math.exp(17.67*t/(243.5+t)) if t is not None and -80<=t<=60 else None

def validate(rows,site):
    totals=Counter()
    picks=defaultdict(list)
    seen=set()
    for i,row in enumerate(rows,1):
        if any(x not in row for x in REQUIRED) or None in row or any(x is None for x in row.values()):
            raise ValueError(site+" row "+str(i)+" malformed or missing Stage10 column")
        when=row["time"]
        if not re.fullmatch(r"\d{12}",when):
            raise ValueError(site+" invalid timestamp "+repr(when))
        t=datetime.strptime(when,"%Y%m%d%H%M")
        if when in seen: raise ValueError(site+" repeated event "+when)
        seen.add(when)
        tq,vq=row["TA_F_QC"],row["VPD_F_QC"]
        if tq not in ("0","1","2") or vq not in ("0","1","2"):
            raise ValueError(site+" unknown QC at "+when)
        temperature,vpd=num(row["TA_F_C"]),num(row["VPD_F_hPa"])
        derived=num(row["RH_derived_pct"])
        saturation=es(temperature)
        if saturation is None or vpd is None or derived is None:
            raise ValueError(site+" missing original T/VPD or computed RH at "+when)
        theoretical=100*(1-vpd/saturation)
        if abs(theoretical-derived)>0.0005:
            raise ValueError(site+" derived RH formula doesn't match report "+when)
        expected_class="NEGATIVE" if theoretical<0 else "NONNEGATIVE_UNDER_1PCT"
        if not theoretical<1 or row["class"]!=expected_class:
            raise ValueError(site+" wrong low-RH event classification "+when)
        if row["SCIENCE_APPROVAL"]!="HOLD_NOT_APPROVED":
            raise ValueError(site+" unexpectedly approved Stage10 value "+when)
        state=row["interpolation_diagnostic"]
        if state not in INTERP:
            raise ValueError(site+" unexpected interpolation state "+repr(state))
        totals["events"]+=1
        totals[expected_class]+=1
        totals["QC_"+tq+"/"+vq]+=1
        totals["INTERP_"+state]+=1
        totals["ERA_"+row["ERA_pair_physics"]]+=1
        totals["MDS_"+row["MDS_pair_physics"]]+=1
        if row["RH_original_pct"]=="":
            totals["original_RH_missing"]+=1
        if tq==vq=="0":
            totals["measured_pair_events"]+=1
            if theoretical<0:
                totals["measured_pair_negative"]+=1
                if len(picks["MEASURED_PAIR_NEGATIVE"])<12:
                    picks["MEASURED_PAIR_NEGATIVE"].append(sample(site,row))
        if row["ERA_pair_physics"] in ("ERA_INTERNAL_NONPHYSICAL",
                                       "ERA_E_WITH_TOWER_T_NOT_FEASIBLE"):
            totals["ERA_HOLD_UNUSABLE_PAIR"]+=1
            if len(picks["ERA_HOLD"])<5:
                picks["ERA_HOLD"].append(sample(site,row))
        if state=="UNAPPROVED_MATH_FEASIBLE":
            interp=num(row["interpolated_measured_vpd_hPa"])
            l=num(row["left_measured_anchor_vpd"])
            r=num(row["right_measured_anchor_vpd"])
            if interp is None or l is None or r is None or not 0<=interp<=saturation:
                raise ValueError(site+" invalid proposed interpolation "+when)
            tl,tr=row["left_measured_anchor_time"],row["right_measured_anchor_time"]
            if not (re.fullmatch(r"\d{12}",tl) and re.fullmatch(r"\d{12}",tr)):
                raise ValueError(site+" invalid anchor timestamp "+when)
            left=datetime.strptime(tl,"%Y%m%d%H%M")
            right=datetime.strptime(tr,"%Y%m%d%H%M")
            if not (left<t<right and t-left<=timedelta(hours=3)
                    and right-t<=timedelta(hours=3)):
                raise ValueError(site+" interpolation outside permitted bracket "+when)
            theoretical_interp=l+(r-l)*(t-left)/(right-left)
            if abs(theoretical_interp-interp)>0.0005:
                raise ValueError(site+" interpolation formula mismatch "+when)
            if len(picks["BRACKETED_INTERPOLATION_UNAPPROVED"])<8:
                picks["BRACKETED_INTERPOLATION_UNAPPROVED"].append(sample(site,row))
        else:
            if row["interpolated_measured_vpd_hPa"]!="":
                raise ValueError(site+" unapproved interpolation numeric leak "+when)
    return dict(totals),dict(picks)

def sample(site,row):
    return {"site":site,"time":row["time"],"class":row["class"],
            "TA_F_C":row["TA_F_C"],"VPD_F_hPa":row["VPD_F_hPa"],
            "derived_RH_pct":row["RH_derived_pct"],
            "original_RH_pct":row["RH_original_pct"],
            "TA_VPD_QC":row["TA_F_QC"]+"/"+row["VPD_F_QC"],
            "MDS_QC":row["TA_MDS_QC"]+"/"+row["VPD_MDS_QC"],
            "ERA_pair":row["ERA_pair_physics"],
            "interpolation_status":row["interpolation_diagnostic"],
            "unapproved_interpolated_vpd":row["interpolated_measured_vpd_hPa"]}

def self_test():
    r=dict.fromkeys(REQUIRED,"")
    r.update({"time":"202001010030","class":"NEGATIVE","RH_derived_pct":"",
      "RH_original_pct":"","TA_F_C":"10","VPD_F_hPa":"14",
      "TA_F_QC":"0","VPD_F_QC":"0","TA_MDS_QC":"0","VPD_MDS_QC":"0",
      "ERA_pair_physics":"ERA_INTERNAL_NONPHYSICAL",
      "MDS_pair_physics":"NONPHYSICAL",
      "interpolation_diagnostic":"NO_BOTH_QC0_ANCHORS_WITHIN_3H",
      "SCIENCE_APPROVAL":"HOLD_NOT_APPROVED"})
    r["RH_derived_pct"]=str(100*(1-14/es(10)))
    out, picks=validate([r],"US-WCr")
    assert out["events"]==1 and out["measured_pair_negative"]==1
    assert out["ERA_HOLD_UNUSABLE_PAIR"]==1
    assert len(picks["MEASURED_PAIR_NEGATIVE"])==1
    s=dict(r)
    s.update({"time":"202001010100","TA_F_QC":"0","VPD_F_QC":"1",
      "left_measured_anchor_time":"202001010030",
      "right_measured_anchor_time":"202001010130",
      "left_measured_anchor_vpd":"2","right_measured_anchor_vpd":"2",
      "interpolated_measured_vpd_hPa":"2",
      "interpolation_diagnostic":"UNAPPROVED_MATH_FEASIBLE"})
    stats,_=validate([r,s],"US-WCr")
    assert stats["INTERP_UNAPPROVED_MATH_FEASIBLE"]==1
    print("STAGE11 SELF-TEST PASS | negative measured, count integrity,"
          " formula and bracket; no writes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report-dir",type=Path,required=False)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:self_test();return 0
    if not args.report_dir:p.error("--report-dir required")
    d=args.report_dir.expanduser()
    if not d.is_dir():p.error("Stage10 report folder missing "+str(d))
    summary_file=d/"audit_summary.json"
    if not summary_file.is_file() or summary_file.is_symlink():
        p.error("audit_summary.json missing/nonregular")
    summary=json.loads(summary_file.read_text(encoding="utf-8"))
    if set(summary.get("sites",{}))!=set(SITES):
        p.error("Stage10 JSON site cohort not exactly Batch05")
    results={}; combined=Counter(); priority=defaultdict(list)
    for site in SITES:
        f=d/(site+"_low_RH_review.csv")
        if not f.is_file() or f.is_symlink():
            p.error("missing/nonregular site CSV "+str(f))
        with f.open(encoding="utf-8-sig",newline="") as handle:
            reader=csv.DictReader(handle)
            if reader.fieldnames is None or set(reader.fieldnames)!=set(REQUIRED):
                raise ValueError("Stage10 review schema mismatch "+site)
            counts,picks=validate(reader,site)
        if counts.get("events",0)!=EXPECTED[site]:
            raise ValueError("Stage09 per-site event total mismatch "+site)
        recorded=summary["sites"][site]["counts"]
        for key in ("events","NEGATIVE","NONNEGATIVE_UNDER_1PCT"):
            if counts.get(key,0)!=recorded.get(key,0):
                raise ValueError(site+" original Stage10 audit_summary disagreement in "+key)
        combined.update(counts)
        results[site]=counts
        for category,examples in picks.items():
            priority[category]+=examples
        print("STAGE11_SITE",site,json.dumps(counts,sort_keys=True),flush=True)
    if (combined["events"],combined["NEGATIVE"],
        combined["NONNEGATIVE_UNDER_1PCT"])!=(1750,1559,191):
        raise ValueError("Batch05 1750/1559/191 invariant mismatch")
    for key in ("events","NEGATIVE","NONNEGATIVE_UNDER_1PCT"):
        if combined[key]!=summary["overall"].get(key,0):
            raise ValueError("Stage10 JSON and actual CSV totals disagree for "+key)
    print("STAGE11_AGGREGATE",json.dumps(dict(combined),sort_keys=True),flush=True)
    for cat in ("MEASURED_PAIR_NEGATIVE","ERA_HOLD",
                "BRACKETED_INTERPOLATION_UNAPPROVED"):
        print("STAGE11_PRIORITY_EXAMPLES",cat,
              json.dumps(priority[cat][:15],sort_keys=True),flush=True)
    print("STAGE11 SUMMARY sites=10/10 events=1750 negative=1559 "
          "nonnegative_below1=191 files_valid=10",flush=True)
    print("READ ONLY; NO REPORT MODIFICATIONS; NO FORCING REPAIR; NO SLURM")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Batch05 Stage13: READ ONLY source-context science audit; no repairs."""
import argparse,csv,json,math,re
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta
STATIONS=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
          "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
REASONS={"BRACKETED_MATH_UNAPPROVED":229,"BRACKETED_NONPHYSICAL":11,
         "MEASURED_QC00_NEGATIVE":27,"ERA_PAIR_HOLD":170}
def val(x):
    try:
        f=float(x)
        return f if math.isfinite(f) and f not in (-9999.,-6999.) else None
    except (ValueError,TypeError):return None
def sat(t):
    return 6.112*math.exp(17.67*t/(243.5+t)) if t is not None and -80<=t<=60 else None
def date(x):
    if not re.fullmatch(r"\d{12}",x or ""):raise ValueError("bad native time "+repr(x))
    return datetime.strptime(x,"%Y%m%d%H%M")
def read_csv(path,fields):
    if not path.is_file() or path.is_symlink():raise ValueError("missing report "+str(path))
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not fields.issubset(reader.fieldnames or []):raise ValueError("missing columns "+str(path))
        result=list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in result):
            raise ValueError("malformed report CSV "+str(path))
        return result
def qc0_anchor(r):
    t=val(r["TA_F_C"]);v=val(r["VPD_F_hPa"]);rh=val(r["RH_original"])
    s=sat(t)
    if s is None or v is None:return False
    derived=100*(1-v/s)
    return (r["TA_F_QC"]=="0" and r["VPD_F_QC"]=="0" and
            1<=derived<=100 and (rh is None or 0<=rh<=100 and abs(rh-derived)<=5))
def assess(targets,contexts):
    context=defaultdict(dict)
    for r in contexts:
        key=(r["site"],r["target_time"])
        try: off=int(r["offset_half_hours"])
        except ValueError:raise ValueError("non-integer offset")
        if off not in range(-6,7) or off in context[key]:
            raise ValueError("duplicate or out-of-range source window offset")
        if date(r["native_time"])!=date(key[1])+timedelta(minutes=30*off):
            raise ValueError("native printed-time mismatch")
        context[key][off]=r
    seen=set();tot=Counter();by_site=defaultdict(Counter);priority=[]
    for r in targets:
        key=(r["site"],r["target_time"])
        if key in seen or key[0] not in STATIONS:raise ValueError("duplicate/invalid site-time")
        seen.add(key)
        blocks=context.get(key,{})
        if set(blocks)!=set(range(-6,7)):raise ValueError("incomplete original 13 HH around "+str(key))
        if any(blocks[o]["target_reasons"]!=r["priority_tags"] for o in blocks):
            raise ValueError("different original target reasons in context")
        tags=r["priority_tags"].split("|")
        if len(set(tags))!=len(tags) or not tags or not set(tags).issubset(REASONS):
            raise ValueError("duplicate/unknown review category")
        if r["decision"]!="HOLD_MANUAL_REVIEW_ONLY":
            raise ValueError("forbidden automatic scientific adoption")
        center=blocks[0]
        t=val(center["TA_F_C"]);v=val(center["VPD_F_hPa"])
        s=sat(t)
        if t is None or v is None or s is None:raise ValueError("missing target original met")
        calculated=100*(1-v/s)
        claimed=val(r["RH_derived_pct"])
        if claimed is None or abs(claimed-calculated)>0.001 or calculated>=1:
            raise ValueError("target water RH not independently reproduced")
        for k in ("TA_F_C","VPD_F_hPa"):
            if abs(val(center[k])-val(r[k]))>0.002:raise ValueError("source disagreement "+k)
        for k in ("TA_F_QC","VPD_F_QC"):
            if center[k]!=r[k]:raise ValueError("QC mismatch "+k)
        if (calculated<0)!=(r["source_class"]=="NEGATIVE"):
            raise ValueError("incorrect negative/nonnegative RH class")
        if center["at_target"]!="1":raise ValueError("wrong target center flag")
        site=r["site"]
        tot["priority_unique"]+=1;tot["context_rows"]+=len(blocks)
        by_site[site]["priority_unique"]+=1;by_site[site]["context_rows"]+=len(blocks)
        for label in tags:
            tot[label]+=1;by_site[site][label]+=1
        if "MEASURED_QC00_NEGATIVE" in tags:
            if r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="0" or calculated>=0:
                raise ValueError("measured negative not proven")
            rh=val(center["RH_original"])
            diff=abs(rh-calculated) if rh is not None else None
            if diff is not None and diff<=0.2:tot["QC00_RH_WATER_DIFFERENCE_AT_MOST_0P2PP"]+=1
            priority.append({"site":site,"time":r["target_time"],
                "type":"MEASURED_NEGATIVE","RH_original":rh,
                "water_RH":round(calculated,5),"abs_difference_pp":diff})
        if "ERA_PAIR_HOLD" in tags and r["ERA_pair_physics"] not in (
            "ERA_INTERNAL_NONPHYSICAL","ERA_E_WITH_TOWER_T_NOT_FEASIBLE"):
            raise ValueError("unverified ERA hold classification")
        if "BRACKETED_MATH_UNAPPROVED" in tags or "BRACKETED_NONPHYSICAL" in tags:
            left,right=date(r["left_anchor"]),date(r["right_anchor"])
            center_time=date(r["target_time"])
            if not (left<center_time<right and center_time-left<=timedelta(hours=3)
                    and right-center_time<=timedelta(hours=3)):
                raise ValueError("source anchors outside allowed 3h")
            li=int((left-center_time).total_seconds()/1800)
            ri=int((right-center_time).total_seconds()/1800)
            lrow,rrow=blocks[li],blocks[ri]
            if not qc0_anchor(lrow) or not qc0_anchor(rrow):
                raise ValueError("invalid measured bracketing source")
            if lrow["at_left_anchor"]!="1" or rrow["at_right_anchor"]!="1":
                raise ValueError("source anchor flag inconsistent")
            estimate=val(lrow["VPD_F_hPa"])+(val(rrow["VPD_F_hPa"])-val(lrow["VPD_F_hPa"]))*(
                (center_time-left)/(right-left))
            claim=val(r["unapproved_interpolated_VPD"])
            valid=0<=estimate<=s
            if "BRACKETED_MATH_UNAPPROVED" in tags:
                if not valid or claim is None or abs(claim-estimate)>0.0005:
                    raise ValueError("interpolation not replicated from original source")
                tot["INTERPOLATION_REVERIFIED"]+=1
                priority.append({"site":site,"time":r["target_time"],
                    "type":"UNAPPROVED_INTERPOLATION",
                    "original_vpd":v,"candidate_vpd":round(estimate,5),
                    "signed_candidate_minus_original_hPa":round(estimate-v,5),
                    "anchor_gap_hours":(right-left).total_seconds()/3600})
            else:
                if valid or claim is not None:
                    raise ValueError("nonphysical interpolation unexpectedly feasible")
                tot["INTERPOLATION_REJECTED_AS_NONPHYSICAL"]+=1
    if seen!=set(context):raise ValueError("orphan original context target")
    return tot,by_site,priority
def selftest():
    center=datetime(2020,1,1,6)
    target={"site":"US-UMB","target_time":"202001010600","priority_tags":"BRACKETED_MATH_UNAPPROVED",
      "decision":"HOLD_MANUAL_REVIEW_ONLY","source_class":"NEGATIVE",
      "TA_F_C":"10","VPD_F_hPa":"14","RH_derived_pct":str(100*(1-14/sat(10))),
      "TA_F_QC":"0","VPD_F_QC":"1","left_anchor":"202001010530",
      "right_anchor":"202001010630","unapproved_interpolated_VPD":"2"}
    contexts=[]
    for off in range(-6,7):
        row={"site":"US-UMB","target_time":target["target_time"],
         "offset_half_hours":str(off),
         "native_time":(center+timedelta(minutes=30*off)).strftime("%Y%m%d%H%M"),
         "target_reasons":target["priority_tags"],
         "TA_F_C":"10","VPD_F_hPa":"14" if off==0 else "2",
         "RH_original":"-9999" if off==0 else "83.71",
         "TA_F_QC":"0","VPD_F_QC":"1" if off==0 else "0",
         "at_target":str(int(off==0)),
         "at_left_anchor":str(int(off==-1)),
         "at_right_anchor":str(int(off==1))}
        contexts.append(row)
    summary,_,_=assess([target],contexts)
    assert summary["priority_unique"]==1 and summary["INTERPOLATION_REVERIFIED"]==1
    print("STAGE13 SELF-TEST PASS | independent 13-HH context and original QC0 anchors; no writes")
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage12-dir",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:selftest();return
    if args.stage12_dir is None:ap.error("--stage12-dir required")
    folder=args.stage12_dir.expanduser()
    needed_targets={"site","target_time","priority_tags","decision",
      "source_class","TA_F_C","VPD_F_hPa","RH_derived_pct",
      "TA_F_QC","VPD_F_QC","left_anchor","right_anchor",
      "unapproved_interpolated_VPD","ERA_pair_physics"}
    needed_context={"site","target_time","offset_half_hours",
      "native_time","target_reasons","TA_F_C","VPD_F_hPa","RH_original",
      "TA_F_QC","VPD_F_QC","at_target","at_left_anchor","at_right_anchor"}
    targets=read_csv(folder/"stage12_priority_targets.csv",needed_targets)
    contexts=read_csv(folder/"stage12_original_native_context.csv",needed_context)
    jsonpath=folder/"stage12_summary.json"
    if not jsonpath.is_file() or jsonpath.is_symlink():raise ValueError("missing Stage12 summary")
    meta=json.loads(jsonpath.read_text(encoding="utf-8"))
    totals,by_site,priority=assess(targets,contexts)
    if totals["priority_unique"]!=382 or totals["context_rows"]!=4966:
        raise ValueError("Stage12 382/4966 counts mismatch")
    if any(totals.get(k,0)!=v for k,v in REASONS.items()):
        raise ValueError("Stage11 source category count mismatch")
    if meta.get("priority_unique_events")!=382 or meta.get("context_rows")!=4966:
        raise ValueError("Stage12 source JSON count mismatch")
    if meta.get("decision")!="ALL_CANDIDATES_UNAPPROVED":
        raise ValueError("Stage12 scientific approval state changed")
    if set(meta.get("sites",{}))!=set(STATIONS):
        raise ValueError("Stage12 missing Batch05 station")
    for s in STATIONS:
        got=by_site[s];src=meta["sites"][s]
        if got["priority_unique"]!=src["priority_unique_events"] or got["context_rows"]!=src["context_rows"]:
            raise ValueError("site original context mismatch "+s)
        print("STAGE13_SITE",s,json.dumps(dict(got),sort_keys=True),flush=True)
    print("STAGE13_TOTALS",json.dumps(dict(totals),sort_keys=True),flush=True)
    measured=[x for x in priority if x["type"]=="MEASURED_NEGATIVE"]
    interp=[x for x in priority if x["type"]=="UNAPPROVED_INTERPOLATION"]
    interp.sort(key=lambda x:abs(x["signed_candidate_minus_original_hPa"]),reverse=True)
    print("STAGE13_MEASURED_NEGATIVE_27",json.dumps(measured,sort_keys=True),flush=True)
    print("STAGE13_LARGEST_UNAPPROVED_VPD_CHANGE_TOP20",
          json.dumps(interp[:20],sort_keys=True),flush=True)
    print("STAGE13 SUMMARY sites=10/10 priority=382 context=4966 "
          "interpolations_reverified=229 approved=0",flush=True)
    print("NO REPORT OR SOURCE WRITES; NO MODEL/FORCING MODIFICATIONS; NO SLURM")
if __name__=="__main__":main()

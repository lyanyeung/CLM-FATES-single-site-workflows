#!/usr/bin/env python3
"""Stage71 read-only screening of CA-Man point ERA replacement vs entire QC1 gap.

Uses Stage61 30-minute candidate/FLUXMET/ERA context and Stage70B human
review CSV. NO temperature, humidity, forcing or job edits. This screening is
clock-UNVERIFIED; FLUXNET TA_ERA need not be raw gridded ERA5.
"""
from __future__ import annotations
import argparse,csv,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
S61=EXP/"reports/stage61_P1_source_evidence_20261024T053231392029Z"
S70B=EXP/"reports/stage70b_CA-Man_human_review_20261024T075415647388Z"

def read(path,needed):
    with path.open(newline="",encoding="utf-8-sig") as stream:
        reader=csv.DictReader(stream)
        hdr=reader.fieldnames or []
        if not set(needed).issubset(hdr) or len(hdr)!=len(set(hdr)):
            raise RuntimeError("Source schema mismatch: "+str(path))
        return list(reader)

def number(value):
    try:
        x=float(value)
        return x if math.isfinite(x) and x>-9990 else None
    except (ValueError,TypeError):
        return None

def qc(value):
    return str(value).strip().removesuffix(".0")

def dt(value):
    return datetime.fromisoformat(value.strip())

def at(d,t,col):
    row=d.get(t)
    return number(row.get(col)) if row else None

def bound_step(first,second):
    return abs(second-first) if first is not None and second is not None else None

def screen(event,context):
    stamp=dt(event["event_time"])
    p=stamp-timedelta(minutes=30)
    n=stamp+timedelta(minutes=30)
    temperature="candidate_TA_C"
    reference="ERA5_TA_ERA_C"
    orig=at(context,stamp,temperature)
    era=at(context,stamp,reference)
    before=at(context,p,temperature)
    after=at(context,n,temperature)
    if orig is None or era is None or before is None:
        raise RuntimeError("Missing necessary at-time original/ERA/before context: "+event["episode_id"])
    if abs(orig-float(event["original_T_at_C"]))>.03 or abs(era-float(event["ERA5_T_at_C"]))>.03:
        raise RuntimeError("Stage70B and Stage61 source mismatch: "+event["episode_id"])
    point_before=bound_step(before,era)
    point_after=bound_step(era,after)
    # The entire source-QC1 gap is examined ONLY if both QC0 bracket values
    # and all ERA source temperatures are within the retained Stage61 context.
    if qc(context.get(stamp,{}).get("FLUXMET_TA_F_QC",""))!="1":
        raise RuntimeError("Unexpected non-QC1 event "+event["episode_id"])
    run=[]
    cursor=stamp
    while (cursor in context and
           qc(context[cursor].get("FLUXMET_TA_F_QC",""))=="1"):
        run.append(cursor)
        cursor+=timedelta(minutes=30)
    full_window = (qc(context.get(p,{}).get("FLUXMET_TA_F_QC",""))=="0"
                   and cursor in context
                   and qc(context[cursor].get("FLUXMET_TA_F_QC",""))=="0")
    missing_era=any(at(context,x,reference) is None for x in run)
    window_max=None
    if full_window and not missing_era:
        proposal=[before]+[at(context,x,reference) for x in run]+[at(context,cursor,temperature)]
        if all(x is not None for x in proposal):
            window_max=max(abs(b-a) for a,b in zip(proposal,proposal[1:]))
    return dict(
        n=0,id=event["episode_id"],time=event["event_time"],
        group=event["review_group"].split("_")[2] if event["review_group"].startswith("CA_MAN_") else "",
        old_entry=bound_step(before,orig),point_entry=point_before,
        old_exit=bound_step(orig,after),point_exit=point_after,
        next_QC=qc(context.get(n,{}).get("FLUXMET_TA_F_QC","NA")),
        QC1_run_length_in_context=len(run),
        whole_QC1_window="BOUNDED" if full_window else "UNBOUNDED_OR_TRUNCATED",
        all_QC1_ERA_available=not missing_era,
        whole_QC1_window_max_step=window_max,
        original_T=orig,ERA_T=era,
    )

def selftest():
    target=datetime(2000,1,1,12)
    d={}
    for k,(a,b,c) in enumerate([(10,10,0),(10,10,0),(25,10,1),
                                 (10,10,0),(10,10,0)]):
        t=target+timedelta(minutes=30*(k-2))
        d[t]={"candidate_TA_C":str(a),"ERA5_TA_ERA_C":str(b),
              "FLUXMET_TA_F_QC":str(c)}
    e={"event_time":str(target),"episode_id":"demo","original_T_at_C":"25",
       "ERA5_T_at_C":"10","review_group":"CA_MAN_19_SHADOW_ONLY_MOISTURE_HOLD"}
    r=screen(e,d)
    assert r["old_entry"]==15 and r["point_entry"]==0 and r["point_exit"]==0
    assert r["whole_QC1_window"]=="BOUNDED" and r["whole_QC1_window_max_step"]==0
    assert r["QC1_run_length_in_context"]==1
    print("SELF-TEST PASS: point entry/exit and two-QC0-bounded QC1 sequence, zero writes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage61-dir",type=Path,default=S61)
    p.add_argument("--stage70b-dir",type=Path,default=S70B)
    a=p.parse_args()
    if a.self_test:selftest();return
    e=read(a.stage70b_dir/"36_CA-Man_review_EDIT_DECISIONS_MANUALLY.csv",
           {"site","episode_id","event_time","review_group","original_T_at_C","ERA5_T_at_C"})
    c=read(a.stage61_dir/"P1_context_source_comparisons.csv",
           {"site","episode_id","timestamp","candidate_TA_C",
            "ERA5_TA_ERA_C","FLUXMET_TA_F_QC"})
    if len(e)!=36 or len({x["episode_id"] for x in e})!=36:
        raise RuntimeError("Expected precisely 36 unique human review events")
    by=defaultdict(dict)
    for row in c:
        if row["site"]!="CA-Man":continue
        key=row["episode_id"]
        t=dt(row["timestamp"])
        if t in by[key]:raise RuntimeError("Duplicate time in "+key)
        by[key][t]=row
    review=[]
    for event in e:
        if event["site"]!="CA-Man":raise RuntimeError("Foreign site in review")
        review.append(screen(event,by[event["episode_id"]]))
    review.sort(key=lambda x:x["time"])
    print("CA-Man 36 | ERA point-only vs entire QC1 window | NO FORCING EDITS")
    print("SOURCE CLOCK and TA_ERA processing remain UNVERIFIED")
    print(f"{'date':19} {'old_in':>7} {'ERA_in':>7} {'ERA_out':>8} "
          f"{'QC_next':>7} {'QC1_len':>7} {'window':>12} {'max_dT':>7}")
    for x in review:
        def f(z):return f"{z:.1f}" if z is not None else "NA"
        print(f"{x['time']:19} {f(x['old_entry']):>7} {f(x['point_entry']):>7} "
              f"{f(x['point_exit']):>8} {x['next_QC']:>7} "
              f"{x['QC1_run_length_in_context']:7d} "
              f"{x['whole_QC1_window']:>12} "
              f"{f(x['whole_QC1_window_max_step']):>7}")
    print("Point-only: entry >10C",sum(x["point_entry"] is not None and x["point_entry"]>10 for x in review),
          "exit >10C",sum(x["point_exit"] is not None and x["point_exit"]>10 for x in review),
          "post-context absent",sum(x["point_exit"] is None for x in review))
    print("Whole QC1 window BOUNDED",
          sum(x["whole_QC1_window"]=="BOUNDED" for x in review),
          "bounded with ERA",
          sum(x["whole_QC1_window_max_step"] is not None for x in review),
          "bounded but >10C step",
          sum(x["whole_QC1_window_max_step"] is not None and x["whole_QC1_window_max_step"]>10 for x in review))
    print("READ-ONLY COMPLETE: no forcing, reports, humidity or jobs modified.")

if __name__=="__main__":main()

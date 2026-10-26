#!/usr/bin/env python3
"""Batch05 Stage21: operator-ready remaining 57 P1 + three boundary review.

Original Stage18 and Stage20 reports are READ ONLY. Science approvals NONE.
Print all 57 remaining original tower/ERA rows and exact before-after context;
export measured QC0, ERA QC2 with/without source RH, and 3 boundary checks.
"""
import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REQ_ORIG={"site","time_native","is_P1","episode","TA_F_C","VPD_F_hPa",
          "RH_original_pct","TA_F_QC","VPD_F_QC","TA_ERA_C",
          "VPD_ERA_hPa","ERA_RH_Magnus_water_pct",
          "TA_MDS_C","VPD_MDS_hPa"}
REQ_CAND={"site","time_native","candidate_RH_pct",
          "candidate_VPD_hPa_with_original_TA"}
REQ_HOLD={"site","time_native"}
FIELDS=("class","episode","site","time_native","TA_F_C","TA_F_QC",
        "VPD_F_hPa","VPD_F_QC","RH_original_pct","TA_ERA_C",
        "VPD_ERA_hPa","ERA_RH_Magnus_water_pct","TA_MDS_C",
        "VPD_MDS_hPa","proposed_RH_pct","proposed_VPD_hPa",
        "VPD_delta_hPa","decision")
SECTIONS=(
 ("A","44 QC0/QC0 measured very-low original RH (ERA RH with tower TA)"),
 ("B","11 QC2/QC2 low-RH ERA fill with valid native RH (rebuild VPD from original RH)"),
 ("C","2 QC2/QC2 ERA fill missing original RH (HOLD only)")
)
BOUNDARY=(
 ("WCr_START","US-WCr","202508251230","202508251300"),
 ("WCr_END","US-WCr","202508260130","202508260200"),
 ("Vcm_Oct2025_END","US-Vcm","202510141100","202510141130")
)
def num(x):
    try:
        z=float(x)
        if math.isfinite(z) and z not in (-9999.,-6999.):return z
    except (ValueError,TypeError):pass
    return None
def es(t):
    if t is None or not -80<=t<=60:return None
    return 6.112*math.exp(17.67*t/(t+243.5))
def ts(s):
    return datetime.strptime(s,"%Y%m%d%H%M")
def sdatetime(d):
    return d.strftime("%Y%m%d%H%M")
def csvread(path,necessary):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing non-symlink original report "+str(path))
    with path.open(newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f)
        cols=rd.fieldnames or []
        if not necessary.issubset(cols) or len(cols)!=len(set(cols)):
            raise ValueError("Missing or repeated original report columns "+str(path))
        records=list(rd)
    if any(None in r or any(v is None for v in r.values()) for r in records):
        raise ValueError("Malformed source report "+str(path))
    return records
def indexed(records):
    d={}
    for r in records:
        key=r["site"],r["time_native"]
        if key in d:raise ValueError("repeated site/time "+str(key))
        d[key]=r
    return d
def load(d18,d20):
    summary18=json.loads((d18/"stage18_summary.json").read_text())
    summary20=json.loads((d20/"stage20_summary.json").read_text())
    if (summary18.get("P1_episodes")!=39 or summary18.get("P1_original_HH")!=176
        or summary18.get("context_rows")!=775 or summary18.get("science_approved")!=0):
        raise ValueError("Stage18 source cohort mismatch")
    if (summary20.get("candidate_rows")!=117 or summary20.get("unresolved_rows")!=34
        or summary20.get("forcing_written")!=False):
        raise ValueError("Stage20 provenance/cohort mismatch")
    context=indexed(csvread(d18/"stage18_all_p1_original_6hour_context.csv",REQ_ORIG))
    flagged=indexed(csvread(d18/"stage18_all_p1_original_flagged_HH.csv",REQ_ORIG))
    proposals=indexed(csvread(d20/"stage20_approved_scope_candidate_TA_RH_VPD.csv",REQ_CAND))
    held=indexed(csvread(d20/"stage20_original_RH_missing_and_QC1_context_holds.csv",REQ_HOLD))
    if (len(context),len(flagged),len(proposals),len(held))!=(775,176,117,34):
        raise ValueError("Read-only input population mismatch")
    if not set(flagged).issubset(context) or not set(proposals).issubset(context):
        raise ValueError("Stage20 target outside Stage18 original evidence")
    p1_cand=set(flagged)&set(proposals)
    if len(p1_cand)!=85 or set(held)&set(proposals):
        raise ValueError("Prior 85 P1 candidate rows or overlap mismatch")
    if not set(held).issubset(set(flagged)):
        raise ValueError("Hold map not original P1")
    left=set(flagged)-set(proposals)-set(held)
    if len(left)!=57:
        raise ValueError("Remaining P1 !=57, got "+str(len(left)))
    return context,flagged,proposals,held,left
def compute(context,flagged,left):
    result=[]
    for site,time in sorted(left):
        r=flagged[(site,time)]
        if site!="US-Vcm":raise ValueError("Unexpected site of remaining P1: "+site)
        tq,vq=r["TA_F_QC"],r["VPD_F_QC"]
        T,V,sourceRH,eraRH=(num(r[k]) for k in
            ("TA_F_C","VPD_F_hPa","RH_original_pct","ERA_RH_Magnus_water_pct"))
        if T is None or V is None or es(T) is None:
            raise ValueError("Missing original numerical tower pair")
        if (tq,vq)==("0","0"):
            kind="A"
            target=eraRH
            decision="HUMAN_APPROVAL_REQUIRED_ERA_RH_ON_TOWER_T"
        elif (tq,vq)==("2","2") and sourceRH is not None:
            kind="B"
            target=sourceRH
            decision="HUMAN_APPROVAL_REQUIRED_NATIVE_RH_ON_SELECTED_T"
        elif (tq,vq)==("2","2") and sourceRH is None:
            kind="C"
            target=None
            decision="HOLD_NO_NATIVE_RH_OR_PHYSICAL_ERA_REPLACEMENT"
        else:
            raise ValueError("Remaining event has unexpected QC class "+str((site,time,tq,vq)))
        if target is not None and not (0<=target<=100):
            raise ValueError("Candidate source RH outside physical bounds "+str((site,time)))
        vnew=es(T)*(1-target/100) if target is not None else None
        if vnew is not None and not (0<=vnew<=es(T)+1e-9):
            raise ValueError("Derived candidate VPD nonphysical "+str((site,time)))
        result.append(dict(
           **{k:r.get(k,"") for k in (
              "episode","site","time_native","TA_F_C","TA_F_QC",
              "VPD_F_hPa","VPD_F_QC","RH_original_pct",
              "TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_water_pct",
              "TA_MDS_C","VPD_MDS_hPa")},
           **{"class":kind,"proposed_RH_pct":round(target,6) if target is not None else "",
              "proposed_VPD_hPa":round(vnew,6) if vnew is not None else "",
              "VPD_delta_hPa":round(vnew-V,6) if vnew is not None else "",
              "decision":decision}))
    if Counter(x["class"] for x in result)!=Counter({"A":44,"B":11,"C":2}):
        raise ValueError("Expected 44 measured / 11 original RH / 2 missing RH")
    return result
def pair_check(context,proposals):
    result=[]
    for name,site,a,b in BOUNDARY:
        for moment in (a,b):
            original=context.get((site,moment))
            if original is None:raise ValueError("Original neighbor missing "+str((site,moment)))
            p=proposals.get((site,moment))
            origv=num(original["VPD_F_hPa"])
            usev=(num(p["candidate_VPD_hPa_with_original_TA"])
                 if p is not None else origv)
            userh=(num(p["candidate_RH_pct"]) if p is not None else
                   num(original["RH_original_pct"]))
            result.append(dict(boundary=name,site=site,time_native=moment,
                  phase="STAGE20_CANDIDATE" if p else "ORIGINAL_UNTOUCHED",
                  TA_F_C=original["TA_F_C"],TA_F_QC=original["TA_F_QC"],
                  original_VPD_hPa=original["VPD_F_hPa"],
                  VPD_F_QC=original["VPD_F_QC"],
                  source_RH_pct=original["RH_original_pct"],
                  ERA_T_C=original["TA_ERA_C"],
                  ERA_VPD_hPa=original["VPD_ERA_hPa"],
                  ERA_RH_pct=original["ERA_RH_Magnus_water_pct"],
                  selected_RH_pct=userh if userh is not None else "",
                  selected_VPD_hPa=round(usev,6)))
    for i in range(0,len(result),2):
        start,end=result[i:i+2]
        jump=end["selected_VPD_hPa"]-start["selected_VPD_hPa"]
        for r in (start,end):r["post_candidate_30min_jump_hPa"]=round(jump,6)
    return result
def line(r):
    ks=("time_native","TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC",
        "RH_original_pct","TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_water_pct",
        "proposed_RH_pct","proposed_VPD_hPa")
    return " | ".join(str(r.get(k,"")).replace("|","/") for k in ks)
def cards(result,context):
    markdown=["# Stage21 remaining 57 P1 — all original half-hour tower vs ERA, before/P1/after",
    "All times original native tower time (NOT UTC). Units TA°C, VPD hPa, RH%.",
    "Original TA_F/VPD_F are **measured only if variable QC=0**; QC1=MDS, QC2=ERA source fill.",
    "TA_ERA / VPD_ERA are original FLUXMET processed ERA fields, NOT independently downloaded ERA5-Land.",
    "Computed ERA RH is only source processed pair diagnostic (water Magnus).",
    "Candidate RH/VPD are ONLY offered for human review. No forcing files changed.",""]
    headers=("time_native","TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC",
             "RH_original_pct","TA_ERA_C","VPD_ERA_hPa",
             "ERA_RH_Magnus_water_pct","proposed_RH_pct","proposed_VPD_hPa")
    for name,description in SECTIONS:
        subset=[r for r in result if r["class"]==name]
        markdown += ["## "+name+": "+description, "Source flagged HH "+str(len(subset)),
                     "### Flagged rows with directly calculated potential candidate","",
                     "| "+" | ".join(headers)+" |",
                     "| "+" | ".join("---" for _ in headers)+" |"]
        for r in subset:markdown.append("| "+line(r)+" |")
        markdown += ["","### Source episode windows including original ±3h neighbors",""]
        episodes=sorted(set(r["episode"] for r in subset))
        for ep in episodes:
            x=[r for r in subset if r["episode"]==ep]
            site=x[0]["site"]
            aa=min(ts(r["time_native"]) for r in x)-timedelta(hours=3)
            bb=max(ts(r["time_native"]) for r in x)+timedelta(hours=3)
            raw=sorted((r for (s,t),r in context.items()
                        if s==site and aa<=ts(t)<=bb),key=lambda r:r["time_native"])
            flagged={r["time_native"]:r for r in x}
            markdown += ["#### "+ep+" · "+sdatetime(aa)+" to "+sdatetime(bb),
                         "| phase | "+" | ".join(headers)+" |",
                         "| --- | "+" | ".join("---" for _ in headers)+" |"]
            for r in raw:
                row=dict(r)
                derived=flagged.get(r["time_native"])
                if derived:row.update(derived)
                else:
                    row["proposed_RH_pct"]=""
                    row["proposed_VPD_hPa"]=""
                phase="P1_TARGET" if derived else ("OTHER_P1" if r["is_P1"]=="1" else "CONTEXT")
                markdown.append("| "+phase+" | "+line(row)+" |")
            markdown.append("")
        markdown += ["**Operator decision for "+name+"**: "+
          ("Use processed ERA RH with original measured tower T to reconstruct VPD? (YES/NO)" if name=="A"
          else "Use valid original native RH with selected source T and transition review? (YES/NO)" if name=="B"
          else "HOLD pending independent verified weather reference (YES)."),""]
    return "\n".join(markdown)+"\n"
def fmtline(r):
    return (f'{r["class"]} {r["time_native"]} {r["episode"]:<14} '
      f'TA={r["TA_F_C"]:>8}/QC{r["TA_F_QC"]} '
      f'VPD={r["VPD_F_hPa"]:>7}/QC{r["VPD_F_QC"]} '
      f'RH={r["RH_original_pct"]:>10} '
      f'ERA_T={r["TA_ERA_C"]:>8} ERA_VPD={r["VPD_ERA_hPa"]:>7} '
      f'ERA_RH={r["ERA_RH_Magnus_water_pct"]:>10} '
      f'PROP_RH={str(r["proposed_RH_pct"]):>10} '
      f'PROP_VPD={str(r["proposed_VPD_hPa"]):>10}')
def test():
    for t,rh in [(10,70),(-12,50)]:
        v=es(t)*(1-rh/100)
        assert 0<=v<=es(t)
        assert abs(100*(1-v/es(t))-rh)<1e-9
    assert len(BOUNDARY)==3
    print("STAGE21 SELF-TEST PASS | 57 remaining P1 split + 3 boundary source-pair checks; NO WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage18-dir",type=Path)
    p.add_argument("--stage20-dir",type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    if args.self_test:test();return
    if args.stage18_dir is None or args.stage20_dir is None or args.out is None:
        p.error("need --stage18-dir --stage20-dir --out")
    d18=args.stage18_dir.expanduser().resolve()
    d20=args.stage20_dir.expanduser().resolve()
    dest=args.out.expanduser().resolve()
    if not (d18.is_dir() and d20.is_dir() and dest.parent.is_dir()):
        p.error("existing source directories and target parent required")
    if dest.exists() or any(dest==p or dest in p.parents or p in dest.parents for p in (d18,d20)):
        p.error("new report output required; must be disjoint from source")
    context,flagged,proposals,held,left=load(d18,d20)
    result=compute(context,flagged,left)
    boundaries=pair_check(context,proposals)
    dest.mkdir(exist_ok=False)
    with (dest/"stage21_remaining_57_original_ERA_candidate_comparison.csv").open(
          "x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(result)
    with (dest/"stage21_three_boundaries_before_after.csv").open(
          "x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(boundaries[0]));w.writeheader();w.writerows(boundaries)
    (dest/"stage21_remaining_57_original_and_3h_context.md").write_text(
        cards(result,context),encoding="utf-8")
    meta={"original_flagged_p1":176,"stage20_p1_candidate_intersection":85,
          "stage20_holds":34,"remaining_p1":57,
          "remaining_measured":44,"remaining_era_source_RH_present":11,
          "remaining_era_source_RH_missing":2,
          "repair_candidates_unapproved":True,"forcing_written":False,
          "source_reanalysis":"original processed TA_ERA/VPD_ERA, not separately extracted ERA5-Land"}
    (dest/"stage21_summary.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("STAGE21 SUCCESS | original P1=176 prior P1 candidate=85 held=34 remaining=57",flush=True)
    for cls,description in SECTIONS:
        print("\n### REVIEW",cls,description,flush=True)
        for row in result:
            if row["class"]==cls:print(fmtline(row),flush=True)
    print("\n### THREE BEFORE/AFTER BOUNDARIES",flush=True)
    for i in range(0,len(boundaries),2):
        pair=boundaries[i:i+2]
        print("BOUNDARY",pair[0]["boundary"],
              "post_candidate_VPD_30min_jump_hPa",
              pair[0]["post_candidate_30min_jump_hPa"],flush=True)
        for r in pair:
            print(" ",r["time_native"],r["phase"],
                  "T",r["TA_F_C"],"QC",r["TA_F_QC"],"/",r["VPD_F_QC"],
                  "original_VPD",r["original_VPD_hPa"],
                  "orig_RH",r["source_RH_pct"],
                  "ERA_T",r["ERA_T_C"],"ERA_VPD",r["ERA_VPD_hPa"],
                  "ERA_RH",r["ERA_RH_pct"],
                  "selected_VPD",r["selected_VPD_hPa"],flush=True)
    print("STAGE21_REVIEW_FILE="+str(dest/"stage21_remaining_57_original_and_3h_context.md"))
    print("STAGE21_SUMMARY remaining_P1=57 A=44 B=11 C=2 boundaries=3 source/forcing/model/Slurm_WRITES=0")
if __name__=="__main__":main()

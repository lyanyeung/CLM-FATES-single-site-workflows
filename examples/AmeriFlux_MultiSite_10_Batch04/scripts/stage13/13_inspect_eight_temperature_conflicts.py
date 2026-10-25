#!/usr/bin/env python3
"""Batch04 Stage13: exact numerical evidence for EIGHT unresolved Stage12 T problems.

READ ONLY. No requests, no writes or mutation of original or derived data.
Pin Stage12 final output receipt; check the 8 actual science-decision HOLD
timestamps; compare original FLUXMET vs latest 10-site selected derived file,
adjacent original tower TA/QC and physically validated independent ERA5-Land
hourly T, dewpoint-derived RH and pressure. Do not blindly replace native QC0.
Import pinned Stage12 and Stage10 methods from this same local directory.
"""
import argparse
import csv
from collections import Counter,defaultdict
from datetime import datetime,timedelta
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S12=ROOT/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
S13SITES={"US-SP1":6,"US-SRG":1,"US-Seg":1}
WINDOW_HH=12
STAGE12_SCRIPT=Path(__file__).resolve().with_name("12_repair_non_syv_science_holds.py")
PENDING={
("US-SP1","200010091800"),("US-SP1","200010091830"),
("US-SP1","200710151730"),("US-SP1","200801160800"),
("US-SP1","200801160830"),("US-SP1","200802030800"),
("US-SRG","201903191200"),("US-Seg","201612271800")
}
EXPECTED_REASON="NEIGHBOUR_OR_GRID_TEMPERATURE_NOT_CONFIRMED"

def load_stage12():
    if STAGE12_SCRIPT.is_symlink() or not STAGE12_SCRIPT.is_file():
        raise RuntimeError("Download pinned Stage12 Python beside Stage13 before inspection")
    spec=importlib.util.spec_from_file_location("batch04_stage12_for_13",str(STAGE12_SCRIPT))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def rows(p,sep=","):
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/non-regular input file "+str(p))
    with p.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter=sep)
        if not r.fieldnames:raise ValueError("Unusable CSV header "+str(p))
        return list(r)

def stamp(s):
    return datetime.strptime(s,"%Y%m%d%H%M")

def one_file(p,keys,expected):
    wanted=set()
    for k in keys:
        t=stamp(k)
        wanted.update((t+timedelta(minutes=30*j)).strftime("%Y%m%d%H%M")
                      for j in range(-WINDOW_HH,WINDOW_HH+1))
    found={}
    n=0
    with p.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        need={"TIMESTAMP_START","TIMESTAMP_END","TA_F","TA_F_QC",
              "VPD_F","VPD_F_QC","PA_F"}
        if not rd.fieldnames or not need.issubset(rd.fieldnames):
            raise ValueError("Original/latest tower columns missing "+str(p))
        for r in rd:
            n+=1
            k=r["TIMESTAMP_START"]
            if k in wanted:
                if k in found:raise ValueError("Duplicate source half-hour "+k)
                found[k]=r
    if n!=expected or not set(keys).issubset(found):
        raise ValueError("Count or target timestamp mismatch "+str(p))
    return found

def number(x):
    if x is None:return None
    try:v=float(x)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) and v not in (-9999,-6999) else None

def fmt(x):
    return "NA" if x is None else "%.3f"%x

def allowed_t(r):
    t=number(r.get("TA_F"))
    return (t if t is not None and -55<=t<=52
            and r.get("TA_F_QC","").strip() in ("0","1") else None)

def bracketing(native,t):
    target=stamp(t)
    left=[]
    right=[]
    for key,r in native.items():
        dt=stamp(key)
        a=allowed_t(r)
        if a is None:continue
        offset=(dt-target).total_seconds()/1800
        if -WINDOW_HH<=offset<0:left.append((dt,a,r.get("TA_F_QC")))
        elif 0<offset<=WINDOW_HH:right.append((dt,a,r.get("TA_F_QC")))
    left=sorted(left,reverse=True)[:3]
    right=sorted(right)[:3]
    if not left or not right:return left,right,None
    ltime,lt,_=left[0];rtime,rt,_=right[0]
    frac=(target-ltime).total_seconds()/(rtime-ltime).total_seconds()
    inferred=lt+(rt-lt)*frac
    return left,right,{"tower_interpolated_T_C":inferred,
        "left_offset_HH":int((ltime-target).total_seconds()/1800),
        "right_offset_HH":int((rtime-target).total_seconds()/1800),
        "bracket_T_range_C":abs(lt-rt),
        "bracket_nearest_left_T_C":lt,
        "bracket_nearest_right_T_C":rt,
        "first_three_left":[(x[0].strftime("%Y%m%d%H%M"),x[1],x[2]) for x in left],
        "first_three_right":[(x[0].strftime("%Y%m%d%H%M"),x[1],x[2]) for x in right]}

def temp_at(grid,utc):
    """Linear in exact continuous UTC hours. Do not use a nonadjacent hour."""
    p=(utc-grid["start_utc"]).total_seconds()/3600
    i=math.floor(p)
    if i<0 or i+1>=len(grid["values"]["t2m"]):return None
    f=p-i
    arr=grid["values"]["t2m"]
    x=float(arr[i])-273.15
    y=float(arr[i+1])-273.15
    return x*(1-f)+y*f if all(math.isfinite(z) for z in (x,y)) else None

def classification(r,bracket,grid_t,orig):
    t=number(r.get("TA_F"))
    oqc=(orig.get("TA_F_QC") or "").strip()
    otemp=number(orig.get("TA_F"))
    if bracket is None:
        return "HOLD_NO_TWO_SIDED_QC01_TOWER_ANCHORS"
    near=bracket["tower_interpolated_T_C"]
    length=max(abs(bracket["left_offset_HH"]),abs(bracket["right_offset_HH"]))
    if bracket["bracket_T_range_C"]>4 or length>12:
        return "HOLD_TOWER_BRACKETS_NOT_STABLE"
    if t is not None and -55<=t<=52 and oqc=="0":
        if abs(t-near)<=4:
            return "TOWER_QC0_AND_EXTENDED_NEIGHBOURS_AGREE_CHECK_OTHER_VARIABLES"
        return "HOLD_QC0_CONFLICT_REQUIRES_SCIENCE_JUDGEMENT"
    if grid_t is not None and abs(grid_t-near)<=5:
        return "HIGH_CONFIDENCE_TWO_SIDED_TOWER_AND_GRID_T_REPAIR_CANDIDATE"
    return "HOLD_GRID_VERSUS_TOWER_CONTEXT_DISAGREES"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--inspect",action="store_true")
    a=p.parse_args()
    assert len(PENDING)==8 and sum(S13SITES.values())==8
    assert (("US-SP1","200010091800") in PENDING and ("US-Seg","201612271800") in PENDING)
    print("STAGE13 SELF-TEST PASS: exact 8 timestamps, immutable source, no downloads or writes")
    if a.self_test:return
    if not a.inspect:p.error("Specify --inspect")
    s12=load_stage12()
    external=s12.helper()
    rec=json.loads((S12/"stage12_receipt.json").read_text(encoding="utf-8"))
    if rec.get("target_unique_non_Syv_events")!=156 or rec.get("successfully_resolved")!=148 or rec.get("unresolved")!=8:
        raise ValueError("Exact Stage12 last successful receipt != 148/156")
    decision=rows(S12/"stage12_science_decisions.tsv",sep="\t")
    pending={(r["site"],r["TIMESTAMP_START"]):r for r in decision
             if not r["status"].startswith("RESOLVED")}
    if len(decision)!=156 or set(pending)!=PENDING or any(
            r["status"]!=EXPECTED_REASON for r in pending.values()):
        raise ValueError("Stage12 exact 8 unresolved timepoints/reasons changed")
    latest={r["site"]:r for r in rows(S12/"stage12_repaired_source_candidates.tsv",sep="\t")}
    if set(latest)!=s12.EXPECTED_SITES:
        raise ValueError("Stage12 latest 10 site selection mismatched")
    selections,old_targets,grouping,original_sources=s12.get_inputs()
    findings=[]
    for site in S13SITES:
        times=sorted(k for s,k in PENDING if s==site)
        point=s12.point_for(site,original_sources[site]["native"])
        latestpath=Path(latest[site]["source_path"])
        if s12.sha(latestpath)!=latest[site]["source_SHA256"]:
            raise ValueError("Latest site SHA mismatch "+site)
        n=int(latest[site]["rows"])
        original=one_file(original_sources[site]["native"],times,n)
        current=one_file(latestpath,times,n)
        yearset=sorted({int(k[:4]) for k in times})
        grids={}
        for year in yearset:
            fp=external.response_receipt(site,year)
            if fp is None:raise ValueError("Expected verified independent ERA5Land already downloaded "+site+" "+str(year))
            grids[year]=external.grid_read(fp,year,point)
        for k in times:
            r=current[k];native=original[k]
            utc=external.local_to_utc(k,point["offset_hours"])
            grid_t=temp_at(grids[int(k[:4])],utc)
            grid_rh=external.rh_hour(grids[int(k[:4])],utc)
            left,right,br=bracketing(original,k)
            t=number(r["TA_F"]);vp=number(r["VPD_F"])
            decision_code=classification(r,br,grid_t,native)
            print("\n=== STAGE13 TOWER / ERA5LAND ===",site,k)
            print("Original TA",native["TA_F"],"QC",native["TA_F_QC"],
                  "VPD",native["VPD_F"],"VPD_QC",native["VPD_F_QC"])
            print("Latest TA",r["TA_F"],"QC",r["TA_F_QC"],
                  "VPD",r["VPD_F"],"VPD_QC",r["VPD_F_QC"],
                  "PA",r["PA_F"],"RH",r.get("RH","(not present)"))
            print("Grid UTC",utc.isoformat(),"T2M_C",fmt(grid_t),
                  "RH_water_pct",fmt(grid_rh))
            print("Nearest QC0/1 tower +/-6h",br)
            print("Latest tower T/VPD physically valid",s12.physics(t,vp))
            print("Recommendation",decision_code,
                  "old_STATUS",pending[site,k]["status"])
            findings.append((site,k,decision_code))
    print("\nSTAGE13 SUMMARY:")
    print("total",len(findings))
    for k,v in sorted(Counter(x[2] for x in findings).items()):print(k,v)
    print("READ ONLY; NO SOURCE / STAGE12 / MODEL / ERA WRITES")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch04 next four original tower-T science HOLDs: concise, read-only review.

Read SHA-pinned ORIGINAL FLUXNET half-hour met: US-SP1 (Jan/Feb 2008)
and US-Seg (Dec 2016). Print all 30-min values in the 3 exact extended
windows, four HOLD marks, TA_ERA comparison, original TA/VPD QC and
QC0 long negative-bias run lengths. Does not apply 2007 daily-offset
recipe to physically different 2008/2016 low-temperature events.
No Stage14, candidate, forcing, CIME or model writes.
"""
import argparse
import csv
import hashlib
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
META={
 "US-SP1":{
  "period":"2000-2020",
  "sha":"d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963",
  "total":368208},
 "US-Seg":{
  "period":"2007-2025",
  "sha":"2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d",
  "total":333120}
}
WINDOWS=[
 ("JAN2008_US_SP1","US-SP1","200801151700","200801171400"),
 ("FEB2008_US_SP1","US-SP1","200802021800","200802041200"),
 ("DEC2016_US_SEG","US-Seg","201612271500","201612281000")
]
HOLDS={
 "US-SP1":{
  "200801160800":-8.211,
  "200801160830":-4.365,
  "200802030800":-3.613},
 "US-Seg":{"201612271800":0.015}
}
COLS=("TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC")

def check(p,msg):
    if not p:raise ValueError(msg)
def numeric(x):
    try:a=float(x)
    except (ValueError,TypeError):return None
    return a if math.isfinite(a) and a not in (-9999,-6999) else None
def original(site):
    period=META[site]["period"]
    p=ROOT/site/"forcing"/"raw"/f"AMF_{site}_FLUXNET_{period}_v1.3_r1"/f"AMF_{site}_FLUXNET_FLUXMET_HH_{period}_v1.3_r1.csv"
    check(p.is_file() and not p.is_symlink(),"Original source missing / linked "+str(p))
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):h.update(block)
    check(h.hexdigest()==META[site]["sha"],"Source SHA mismatch "+site)
    return p
def read_site(site):
    win=[(nm,a,b) for nm,s,a,b in WINDOWS if s==site]
    rows={nm:{} for nm,a,b in win}
    count=0
    with original(site).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        check(r.fieldnames is not None and set(COLS).issubset(r.fieldnames),
              "Original FLUXMET schema missing "+site)
        for line in r:
            count+=1;k=line["TIMESTAMP_START"]
            for nm,a,b in win:
                if a<=k<=b:
                    check(k not in rows[nm],"Duplicated original native HH "+k)
                    rows[nm][k]={x:line[x] for x in COLS}
    check(count==META[site]["total"],"Original native source row count changed "+site)
    for nm,a,b in win:
        start=datetime.strptime(a,"%Y%m%d%H%M")
        end=datetime.strptime(b,"%Y%m%d%H%M")
        times=[(start+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
               for i in range(int((end-start).total_seconds()/1800)+1)]
        check(set(rows[nm])==set(times),"Original expected time window incomplete "+nm)
    for k,t in HOLDS[site].items():
        associated=[x for x in rows.values() if k in x]
        check(len(associated)==1,"Original four-HOLD timestamp not unique "+k)
        d=associated[0][k]
        check(d["TA_F_QC"]=="0" and numeric(d["TA_F"]) is not None and
              abs(numeric(d["TA_F"])-t)<0.002,
              "Original HOLD QC0/temperature anchor changed "+k)
    print("ORIGINAL SOURCE VERIFIED",site,
          "SHA256",META[site]["sha"],"ALL_NATIVE_HH",count)
    return rows
def inspect_window(name,site,records):
    times=sorted(records)
    full=[records[k] for k in times]
    diffs=[]
    qc=Counter()
    runs=[]
    current=[]
    for r in full:
        qc[r["TA_F_QC"]]+=1
        t=numeric(r["TA_F"]);era=numeric(r["TA_ERA"])
        bad=r["TA_F_QC"]=="0" and t is not None and era is not None and t-era<=-10
        if bad:current.append(r["TIMESTAMP_START"])
        elif current:
            runs.append(current);current=[]
        if t is not None and era is not None:diffs.append(t-era)
    if current:runs.append(current)
    print("\n=== ORIGINAL SCIENCE REVIEW",name,site,"===")
    print("WHOLE_WINDOW_SOURCE_RECORDS",len(times),"QC_counts",dict(qc))
    print("TA_MINUS_TA_ERA_MEAN_C",round(sum(diffs)/len(diffs),3) if diffs else "NA",
          "MIN_C",round(min(diffs),3) if diffs else "NA",
          "MAX_C",round(max(diffs),3) if diffs else "NA")
    print("CONTIGUOUS_QC0_T_MINUS_ERA_LE_-10C_RUNS",len(runs))
    for run in sorted(runs,key=lambda z:(-len(z),z[0]))[:8]:
        print("RUN_START",run[0],"RUN_END",run[-1],
              "HALF_HOURS",len(run),"HOURS",len(run)*0.5)
    print("NATIVE_LOCAL_STANDARD_TIME TA_F_C TA_F_QC TA_ERA_C T_MINUS_ERA_C VPD_F_hPa VPD_F_QC MARK")
    for r in full:
        k=r["TIMESTAMP_START"];t=numeric(r["TA_F"]);era=numeric(r["TA_ERA"])
        delta=t-era if t is not None and era is not None else None
        fmt=lambda z:f"{z:.3f}" if z is not None else "NA"
        mark="***HUMAN_HOLD***" if k in HOLDS[site] else ""
        print(k,fmt(t),r["TA_F_QC"],fmt(era),fmt(delta),
              fmt(numeric(r["VPD_F"])),r["VPD_F_QC"],mark)
    print("=== END",name,"===")
def selftest():
    check(len(HOLDS["US-SP1"])+len(HOLDS["US-Seg"])==4,"Four hold contract invalid")
    check(len(WINDOWS)==3,"Three extended windows required")
    check(all(len(x["sha"])==64 for x in META.values()),"SHA identifiers truncated")
    check(numeric("-9999") is None and numeric("nan") is None,"Missing TA parser invalid")
    print("NEXT FOUR HOLD SELF-TEST PASS: two original SHA-pinned FLUXMET sources, three windows, 4 exact original QC0 holds; NO WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--review",action="store_true")
    a=p.parse_args()
    selftest()
    if a.self_test:return
    allrows={s:read_site(s) for s in META}
    for name,site,_,_ in WINDOWS:
        inspect_window(name,site,allrows[site][name])
    print("\nNEXT FOUR SOURCE SCIENCE HOLDS INSPECTED: 4/4, NATIVE TEMPERATURE UNCHANGED")
    print("NOTE: original TA_ERA is processed FLUXNET ERA, NOT an independent raw tower thermometer or stand-alone ERA5-Land.")
    print("REVIEW ONLY: NO original, Stage14, validated SP1 137-HH trial, US-SRG trial, Post-v5/DATM/CIME/SLURM/spinup writes.")
if __name__=="__main__":main()

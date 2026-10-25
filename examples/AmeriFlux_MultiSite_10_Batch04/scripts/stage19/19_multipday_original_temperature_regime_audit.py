#!/usr/bin/env python3
"""Batch04 Stage19: read-only multi-day native-temperature anomaly characterisation.

Scope: six held original-QC0 native HH events (SP1 x4, SRG x1, Seg x1).
Use only SHA-pinned original FLUXMET and original BIF, Stage12 science
receipt and eight-HOLD ledger, Stage14 eight-HOLD receipt.
Evaluate actual continuous QC0 segments, ERA-derived temperature differences
and a narrow repeated-value band at SP1 Oct 2007. QC2 is an ERA-derived
consolidated value, NEVER an independent tower anchor.
No ERA/CDS download, no repairs, no output files, no Post-v5/DATM/CIME/Slurm.
"""
import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S12=EXP/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
S14=EXP/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
EXPECTED={
 "US-SP1":{"200710151730":11.150,"200801160800":-8.211,
           "200801160830":-4.365,"200802030800":-3.613},
 "US-SRG":{"201903191200":0.718},
 "US-Seg":{"201612271800":0.015},
}
ROWS={"US-SP1":368208,"US-SRG":315600,"US-Seg":333120}
SHA={
 "US-SP1":"d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963",
 "US-SRG":"bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567",
 "US-Seg":"2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d",
}
PENDING={(s,k) for s,e in EXPECTED.items() for k in e}|{
 ("US-SP1","200010091800"),("US-SP1","200010091830")}
WINDOW_DAYS=3
def ts(s):
    return datetime.strptime(s,"%Y%m%d%H%M")
def txt(t):
    return t.strftime("%Y%m%d%H%M")
def number(x):
    try: v=float(x)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) and v not in (-9999,-6999) else None
def fmt(x):
    return "NA" if x is None else "%.3f"%x
def fetch12():
    import importlib.util
    p=Path(__file__).resolve().with_name("12_repair_non_syv_science_holds.py")
    if not p.is_file() or p.is_symlink():
        raise ValueError("Download the pinned Stage12 helper beside Stage19")
    spec=importlib.util.spec_from_file_location("batch04_stage19_stage12",str(p))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
def tsv(m,p):
    with m.regular(p).open(encoding="utf-8-sig",newline="") as f:
        d=csv.DictReader(f,delimiter="\t")
        if not d.fieldnames or len(d.fieldnames)!=len(set(d.fieldnames)):
            raise ValueError("Invalid decision ledger")
        return list(d)
def native_window(m,p,site):
    bounds=[]
    for k in EXPECTED[site]:
        d=ts(k)
        bounds.append((txt(d-timedelta(days=WINDOW_DAYS)),
                       txt(d+timedelta(days=WINDOW_DAYS))))
    result={};n=0
    with m.regular(p).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        fields=set(reader.fieldnames or [])
        needed={"TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS",
                "TA_F_MDS_QC","TA_ERA","VPD_F","VPD_F_QC"}
        if not needed.issubset(fields):
            raise ValueError("Missing expected original FLUXMET T lineage fields")
        for row in reader:
            n+=1
            k=row["TIMESTAMP_START"]
            if any(lo<=k<=hi for lo,hi in bounds):
                if k in result:raise ValueError("Duplicate original HH: "+k)
                result[k]=row
    if n!=ROWS[site] or not set(EXPECTED[site]).issubset(result):
        raise ValueError("Wrong native rows/required clocks: "+site)
    return result,n
def runs(samples,predicate):
    """Contiguous native 30-min intervals only; gap breaks the sequence."""
    pieces=[];start=None;previous=None;length=0;values=[]
    for clock,row in samples:
        qualifies=predicate(row)
        if qualifies:
            if previous is None or clock-previous!=timedelta(minutes=30):
                if length: pieces.append((start,previous,length,list(values)))
                start=clock;length=0;values=[]
            length+=1;values.append(number(row["TA_F"]))
            previous=clock
        else:
            if length:pieces.append((start,previous,length,list(values)))
            start=None;previous=None;length=0;values=[]
    if length:pieces.append((start,previous,length,list(values)))
    return sorted(pieces,key=lambda x:(-x[2],x[0]))
def review(site,event,whole):
    center=ts(event)
    subset=sorted((ts(k),r) for k,r in whole.items()
                  if abs((ts(k)-center).total_seconds())<=WINDOW_DAYS*86400)
    valid=[(d,r) for d,r in subset if r["TA_F_QC"].strip()=="0" and
           number(r["TA_F"]) is not None and number(r["TA_ERA"]) is not None]
    qc=Counter(r["TA_F_QC"].strip() for _,r in subset)
    def cold(row):
        a=number(row["TA_F"]);b=number(row["TA_ERA"])
        return row["TA_F_QC"].strip()=="0" and a is not None and b is not None and a-b<=-10
    def plateau(row):
        a=number(row["TA_F"])
        return row["TA_F_QC"].strip()=="0" and a is not None and abs(a-11.15)<=.05
    cold_runs=runs(subset,cold)
    plateau_runs=runs(subset,plateau)
    record=whole[event]
    t=number(record["TA_F"])
    if (t is None or abs(t-EXPECTED[site][event])>.002 or
        record["TA_F_QC"].strip()!="0" or
        record["TA_F_MDS_QC"].strip()!="0" or
        abs(number(record["TA_F_MDS"])-t)>.002):
        raise ValueError("Original event TA/MDS/QC0 source contract changed: "+site+" "+event)
    print("\nSTAGE19 EVENT",site,event,
          "native_T_C",fmt(t),"TA_ERA_C",fmt(number(record["TA_ERA"])),
          "TA_minus_ERA_C",fmt(t-number(record["TA_ERA"])),
          "native_VPD_hPa",record["VPD_F"],"VPD_QC",record["VPD_F_QC"])
    print("STAGE19 +/-3d rows",len(subset),
          "QC_counts",dict(sorted(qc.items())),"QC0_with_numeric_ERA_T",len(valid))
    for name,pieces in (("QC0_T_minus_TA_ERA_LE_-10C",cold_runs),
                        ("QC0_T_within_11p15_plusminus_0p05C",plateau_runs)):
        count=sum(x[2] for x in pieces)
        print("STAGE19 RUN FAMILY",name,"matched_HH",count,
              "episodes",len(pieces))
        for start,end,n,values in pieces[:6]:
            print("STAGE19 RUN",name,"start",txt(start),"end",txt(end),
                  "HH",n,"min_C",fmt(min(values)),"max_C",fmt(max(values)))
    for shift in (-2,-1,0,1,2):
        k=txt(center+timedelta(days=shift))
        row=whole.get(k)
        print("STAGE19 SAME_CLOCK_DAY",shift,k,
              "TA_F",fmt(number(row["TA_F"])) if row else "MISSING",
              "TA_QC",row["TA_F_QC"] if row else "MISSING",
              "TA_ERA",fmt(number(row["TA_ERA"])) if row else "MISSING")
    if site=="US-SRG":
        pre=whole.get(txt(center-timedelta(minutes=30)))
        post=whole.get(txt(center+timedelta(minutes=30)))
        if pre is None or post is None:raise ValueError("SRG flanking HH not found")
        for label,row in (("BEFORE",pre),("AFTER",post)):
            a=number(row["TA_F"]);b=number(row["TA_ERA"])
            if row["TA_F_QC"].strip()!="2" or a is None or b is None or abs(a-b)>.002:
                raise ValueError("Expected two ERA-derived SRG QC2 flank values absent")
            print("STAGE19 SRG",label,"QC2 TA_F_C",fmt(a),"TA_ERA_C",fmt(b),
                  "NOT INDEPENDENT TOWER OBSERVATION")
    if site=="US-Seg":
        print("STAGE19 SEG: adjacent original QC0 cooling is NOT proof of bad temperature")
    print("STAGE19 SCIENCE HOLD: no production T update")
def selftest():
    assert sum(map(len,EXPECTED.values()))==6 and len(PENDING)==8
    assert all(len(x)==64 for x in SHA.values())
    assert txt(ts("200710151730")+timedelta(days=1))=="200710161730"
    fake=[(ts("200710151700"),{"TA_F":"11.149","TA_F_QC":"0"}),
          (ts("200710151730"),{"TA_F":"11.150","TA_F_QC":"0"}),
          (ts("200710151800"),{"TA_F":"23.22","TA_F_QC":"0"})]
    assert len(runs(fake,lambda row:abs(number(row["TA_F"])-11.15)<=.05))==1
    assert runs(fake,lambda row:abs(number(row["TA_F"])-11.15)<=.05)[0][2]==2
    print("STAGE19 SELF-TEST PASS: six pinned events, ±3d QC0 runs, source/clock constraints; read-only")
def audit():
    m=fetch12()
    r12=json.loads(m.regular(S12/"stage12_receipt.json").read_text())
    r14=json.loads(m.regular(S14/"stage14_receipt.json").read_text())
    if (r12.get("target_unique_non_Syv_events")!=156 or
        r12.get("successfully_resolved")!=148 or r12.get("unresolved")!=8 or
        r12.get("Postv5_approved") is not False or
        r14.get("humidity_physical_candidate_count")!=8 or
        r14.get("still_unresolved_tower_temperature_science_hold_count")!=8):
        raise ValueError("Stage12/Stage14 source receipts inconsistent")
    decisions=tsv(m,S12/"stage12_science_decisions.tsv")
    held={(r["site"],r["TIMESTAMP_START"]) for r in decisions
          if not r["status"].startswith("RESOLVED")}
    if len(decisions)!=156 or held!=PENDING:
        raise ValueError("Original eight temperature-hold timestamps drifted")
    selections,targets,reasons,originals=m.get_inputs()
    count=0
    for site,evs in EXPECTED.items():
        raw=originals[site]["native"]
        if m.sha(raw)!=SHA[site]:
            raise ValueError("Pinned original FLUXMET SHA changed: "+site)
        point=m.point_for(site,raw)
        prior=r12["original_native_BIF_points"][site]
        if m.sha(Path(prior["BIF_file"]))!=prior["BIF_sha256"]:
            raise ValueError("Original BIF SHA changed: "+site)
        for k in ("latitude","longitude","offset_hours"):
            if abs(point[k]-prior[k])>1e-4:
                raise ValueError("Original BIF site geometry changed")
        records,n=native_window(m,raw,site)
        print("\nSTAGE19 SITE",site,"original_FLUXMET_SHA",SHA[site],
              "source_rows",n,"BIF_offset_hours",point["offset_hours"])
        for k in evs:
            review(site,k,records)
            count+=1
    if count!=6:raise ValueError("Expected exactly six investigations")
    print("\nSTAGE19 RESULT: 6/6 MULTI-DAY NATIVE TEMPERATURE REGIMES REVIEWED; 8/8 T SCIENCE HOLDS PRESERVED")
    print("STAGE19 US-Syv 606 SCIENCE HOLDS AND 10 STAGE07 SKIPPED ERA EDGES DEFERRED")
    print("STAGE19 READ ONLY: ZERO SOURCE, QC, CDS, POST-v5, DATM, CIME, SLURM OR MODEL WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--audit",action="store_true")
    args=p.parse_args()
    selftest()
    if args.audit:audit()
if __name__=="__main__":
    main()

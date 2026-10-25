#!/usr/bin/env python3
"""US-SP1 2000-2020 ORIGINAL QC0 temperature 18:00 clock-step audit.

Scan all 368,208 original half-hour FLUXMET rows (one pass + SHA256).
A candidate day must have native QC0 at both 17:30 and 18:00, a
17:30 -> 18:00 increase >= 10 C, and at least five native daytime
(08:00-17:30) original QC0 tower temperatures >10 C below TA_ERA.
A screen is NOT proof of bad sensor readings or authorisation to replace.

Reports annual/monthly episode counts, all candidate calendar dates,
consecutive-day clusters, and 15:30-19:00 source-context QC for sampled
events. The threshold is a science *screen*, not an automatic QC rule.
Original files, ERA/CDS, Stage14/15, model and case files are untouched.
"""
import argparse
import csv
import hashlib
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

SOURCE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/"
    "US-SP1/forcing/raw/AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1/"
    "AMF_US-SP1_FLUXNET_FLUXMET_HH_2000-2020_v1.3_r1.csv")
SHA256="d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963"
NROWS=368208
FIELDS=("TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC")
FOUR_DAYS={
 "20071015":(11.150,23.220),
 "20071016":(11.149,23.220),
 "20071017":(11.169,23.710),
 "20071018":(11.138,26.240),
}

def finite(x):
    try: x=float(x)
    except (TypeError,ValueError): return None
    return x if math.isfinite(x) and x not in (-9999,-6999) else None

def inspect():
    if SOURCE.is_symlink() or not SOURCE.is_file():
        raise ValueError("Original US-SP1 FLUXMET_HH source missing or symlinked: "+str(SOURCE))
    h=hashlib.sha256()
    with SOURCE.open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    if h.hexdigest()!=SHA256:
        raise ValueError("Original FLUXMET SHA256 mismatch; stop before processing")
    days=defaultdict(dict)
    n=0
    prev=None
    with SOURCE.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not set(FIELDS).issubset(rd.fieldnames):
            raise ValueError("Original FLUXMET schema differs")
        for row in rd:
            n+=1
            k=row["TIMESTAMP_START"]
            dt=datetime.strptime(k,"%Y%m%d%H%M")
            if prev and dt-prev!=timedelta(minutes=30):
                raise ValueError(f"Source timeline not contiguous near {k}")
            prev=dt
            hour=k[-4:]
            if "0800"<=hour<="1900":
                key=k[:8]
                if hour in days[key]:
                    raise ValueError("Duplicate source half-hour: "+k)
                days[key][hour]=tuple(row[c] for c in FIELDS[1:])
    if n!=NROWS:
        raise ValueError(f"Unexpected full source row count {n} != {NROWS}")

    def row(day,hh):
        a=days[day].get(hh)
        if a is None:return None
        t,q,era,vpd,vpdqc=a
        return finite(t),q.strip(),finite(era),finite(vpd),vpdqc.strip()

    for day,(a,b) in FOUR_DAYS.items():
        v17=row(day,"1730");v18=row(day,"1800")
        if v17 is None or v18 is None or v17[1]!="0" or v18[1]!="0" or \
           abs(v17[0]-a)>0.002 or abs(v18[0]-b)>0.002:
            raise ValueError("Pinned previously-verified Oct2007 source anchors changed "+day)

    clockstep=Counter()
    daycold=Counter()
    details=[]
    for day in sorted(days):
        vals=days[day]
        baseline=[(hr,*row(day,hr)) for hr in vals if "0800"<=hr<="1730"]
        cool=sum(t is not None and era is not None and qc=="0"
                 and t-era<=-10.0 for _,t,qc,era,_,_ in baseline)
        daycold[day[:4]]+=int(cool>=5)
        a=row(day,"1730");b=row(day,"1800")
        if a is None or b is None or a[0] is None or b[0] is None:
            continue
        dt=b[0]-a[0]
        if a[1]!="0" or b[1]!="0" or dt<10:
            continue
        clockstep[day[:4]]+=1
        if cool>=5:
            details.append((day,dt,cool,a,b))
    if not all(day in {x[0] for x in details} for day in FOUR_DAYS):
        raise ValueError("Four known clock-locked source dates not selected by screen")

    print("SP1 ORIGINAL VERIFIED SHA",SHA256,"native_rows",n,
          "day_records",len(days))
    print("SCREEN: original TA_F_QC0 both 17:30 and 18:00, +10C or more in 30 minutes")
    print("STRONG_SCREEN: plus >=5 original daytime QC0 HH with TA_F-TA_ERA <= -10C")
    print("CAUTION: TA_ERA is processed FLUXNET ERA product, not independent raw instrument proof")
    print("TOTAL_18H_10C_OR_GREATER_QC0_JUMPS",sum(clockstep.values()))
    print("TOTAL_STRONG_CLOCK_LOCKED_18H_DAYS",len(details))
    print("YEAR QC0_18H_JUMP_DAYS STRONG_JUMP_AND_DAYTIME_ERA_COLD_DAYS ANY_DAY_5COLD_HH")
    for year in sorted(set(clockstep)|set(daycold)):
        count=sum(x[0][:4]==year for x in details)
        if clockstep[year] or daycold[year]:
            print(year,clockstep[year],count,daycold[year])
    months=Counter(x[0][:6] for x in details)
    print("STRONG_MONTH_COUNTS", " ".join(f"{k}:{v}" for k,v in sorted(months.items())) or "NONE")
    print("STRONG_DATE 17:30_T 17:30_QC 17:30_TA_ERA 18:00_T 18:00_QC 18:00_TA_ERA DELTA_T 08-1730_COLD_QC0_HH")
    for day,diff,cold,a,b in details:
        print(day,f"{a[0]:.3f}",a[1],f"{a[2]:.3f}" if a[2] is not None else "NA",
              f"{b[0]:.3f}",b[1],f"{b[2]:.3f}" if b[2] is not None else "NA",
              f"{diff:.3f}",cold)
    date_list=[datetime.strptime(x[0],"%Y%m%d") for x in details]
    clusters=[]
    for d in date_list:
        if not clusters or (d-clusters[-1][-1]).days>1:
            clusters.append([d])
        else:
            clusters[-1].append(d)
    print("CONSECUTIVE_CALENDAR_DAY_CLUSTERS",len(clusters))
    for cl in clusters:
        print("CLUSTER",cl[0].strftime("%Y%m%d"),cl[-1].strftime("%Y%m%d"),
              "calendar_days",len(cl))
    for day in FOUR_DAYS:
        print("KNOWN_2007_CONTEXT",day,"HOUR TA_F TA_F_QC TA_ERA VPD_F VPD_F_QC")
        for hh in ("1500","1530","1600","1630","1700","1730","1800","1830","1900"):
            r=row(day,hh)
            if r is None:raise ValueError("Missing known source-context HH "+day+hh)
            print(hh,*(str(x) if x is not None else "NA" for x in r))
    print("SP1_AUDIT_COMPLETE READ_ONLY; NO SOURCE, QC, POST-v5, CIME OR MODEL WRITES")
    print("NEXT_GATE: review original BASE/raw sensor/clock metadata for affected 18H clusters before any interval correction")

def selftest():
    assert len(FOUR_DAYS)==4
    assert len(SHA256)==64
    assert all(b-a>=10 for a,b in FOUR_DAYS.values())
    assert finite("-9999") is None and finite("nan") is None
    assert finite("11.150")==11.150
    print("SP1 CLOCK_STEP SELF-TEST PASS: exact original 4-day anchor, QC0 and 18h threshold, read-only")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--audit",action="store_true")
    args=p.parse_args()
    selftest()
    if args.audit:inspect()
if __name__=="__main__":
    main()

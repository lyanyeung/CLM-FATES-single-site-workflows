#!/usr/bin/env python3
"""Batch04 operator-requested extended original TA/TA_ERA/QC windows. READ ONLY.

Show hourly and half-hour native QC status for US-SP1 Oct 2007 (including
BEFORE 15:30), longer Jan/Feb 2008 cold regimes and US-Seg AFTER 20:00.
Print original TA_F, TA_F_QC, TA_F_MDS_QC and original FLUXNET TA_ERA.
TA_ERA is the FLUXNET processed ERA variable, NOT independent tower TA.
Reads SHA-verified original FLUXNET release files; stdout only.
"""
import argparse, csv, hashlib
from datetime import datetime
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
RELEASES={
 "US-SP1":"2000-2020",
 "US-Seg":"2007-2025",
}
SHA={
 "US-SP1":"d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963",
 "US-Seg":"2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d",
}
ROWS={"US-SP1":368208,"US-Seg":333120}
WINDOWS=(
 ("SP1_2007_OCT15_BEFORE_1530","US-SP1","200710150500","200710152100"),
 ("SP1_2007_OCT16_DAY","US-SP1","200710160800","200710162000"),
 ("SP1_2007_OCT17_DAY","US-SP1","200710170800","200710172000"),
 ("SP1_2007_OCT18_DAY","US-SP1","200710180800","200710182000"),
 ("SP1_2008_JAN_CONTINUOUS","US-SP1","200801151700","200801171400"),
 ("SP1_2008_FEB_CONTINUOUS","US-SP1","200802021800","200802041200"),
 ("SEG_2016_AFTER_2000","US-Seg","201612271500","201612281000"),
)
FIELDS=("TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS","TA_F_MDS_QC","TA_ERA","VPD_F","VPD_F_QC")
def source(site):
    y=RELEASES[site]
    pkg=f"AMF_{site}_FLUXNET_{y}_v1.3_r1"
    p=ROOT/site/"forcing"/"raw"/pkg/f"AMF_{site}_FLUXNET_FLUXMET_HH_{y}_v1.3_r1.csv"
    if p.is_symlink() or not p.is_file():
        raise ValueError("Original source missing or symlinked "+str(p))
    return p
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for part in iter(lambda:fh.read(4<<20),b""):h.update(part)
    return h.hexdigest()
def scan(site):
    path=source(site)
    observed=digest(path)
    if observed!=SHA[site]:raise ValueError("Immutable original SHA mismatch for "+site)
    windows=[(name,a,b) for name,s,a,b in WINDOWS if s==site]
    collected={name:[] for name,a,b in windows}
    n=0
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError("Original native FLUXMET schema changed")
        for r in reader:
            n+=1
            time=r["TIMESTAMP_START"]
            for name,lo,hi in windows:
                if lo<=time<=hi:
                    collected[name].append({f:r[f] for f in FIELDS})
    if n!=ROWS[site]:raise ValueError("Original FLUXMET row count differs")
    for name,lo,hi in windows:
        expected=int((datetime.strptime(hi,"%Y%m%d%H%M")-
                      datetime.strptime(lo,"%Y%m%d%H%M")).total_seconds()/1800)+1
        vals=collected[name]
        if len(vals)!=expected or vals[0]["TIMESTAMP_START"]!=lo or vals[-1]["TIMESTAMP_START"]!=hi:
            raise ValueError(f"Window missing native half-hour(s): {name}, got {len(vals)}, expected {expected}")
        print(f"\n=== {name} | {site} | {lo} to {hi} | {expected} half-hours ===")
        print("TIMESTAMP_START TA_F_C TA_F_QC TA_F_MDS_C TA_F_MDS_QC TA_ERA_C VPD_F_hPa VPD_F_QC")
        for row in vals:
            print(" ".join(row[f] for f in FIELDS))
        print("=== END",name,"===")
    print("SOURCE VERIFIED",site,"original_SHA256",observed,"full_HH_rows",n)
def self_test():
    assert len(WINDOWS)==7
    assert all(len(k)==64 for k in SHA.values())
    assert WINDOWS[0][2]<"200710151530"
    assert WINDOWS[-1][3]>"201612272000"
    assert datetime.strptime("200801170800","%Y%m%d%H%M").year==2008
    print("MANUAL EXTENDED T SELF-TEST PASS: 7 original windows, 2 immutable native sources; no writes")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--inspect",action="store_true")
    args=p.parse_args()
    self_test()
    if args.inspect:
        for site in RELEASES:scan(site)
        print("\nMANUAL EXTENDED T DONE: READ ONLY; NO ORIGINAL/QC/ERA/MODEL FILE WRITES")
if __name__=="__main__":
    main()

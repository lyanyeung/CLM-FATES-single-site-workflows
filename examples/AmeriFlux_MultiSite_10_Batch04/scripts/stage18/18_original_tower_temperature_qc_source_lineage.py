#!/usr/bin/env python3
"""Batch04 Stage18: read-only ORIGINAL FLUXMET temperature source/QC lineage.

For six Stage17 unresolved events, inspect the original product's T-related
columns and 30-min provenance before considering temperature sensitivity
alternatives. Compare ±2 h native half-hours and exact local HH +/-1,2 days.
Show neighbouring TA_F_QC codes; QC2 must not be treated as independent
tower observations. Zero grid requests, forcing edits, output files, model jobs.
Requires Stage12 and its existing Stage11/07/08 original provenance inputs.
"""
import argparse
import csv
import importlib.util
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
STAGE12=ROOT/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
STAGE14=ROOT/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
EVENTS={
 "US-SP1":{"200710151730":11.150,"200801160800":-8.211,
           "200801160830":-4.365,"200802030800":-3.613},
 "US-SRG":{"201903191200":0.718},
 "US-Seg":{"201612271800":0.015},
}
EXPECTED_ROWS={"US-SP1":368208,"US-SRG":315600,"US-Seg":333120}
ORIGINAL_SHA={
 "US-SP1":"d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963",
 "US-SRG":"bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567",
 "US-Seg":"2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d",
}
STAGE14_SHA={
 "US-SP1":"3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806",
 "US-SRG":"57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39",
 "US-Seg":"22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6",
}
EIGHT={(s,t) for s,d in EVENTS.items() for t in d} | {
 ("US-SP1","200010091800"),("US-SP1","200010091830")}
CORE={"TIMESTAMP_START","TIMESTAMP_END","TA_F","TA_F_QC","VPD_F","VPD_F_QC"}

def stage12():
    p=Path(__file__).resolve().with_name("12_repair_non_syv_science_holds.py")
    if not p.is_file() or p.is_symlink():
        raise ValueError("Stage12 pinned code missing next to Stage18")
    spec=importlib.util.spec_from_file_location("batch04_stage18_stage12",str(p))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def read_tsv(m,path):
    with m.regular(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):
            raise ValueError("Manifest schema invalid")
        return list(reader)

def num(raw):
    try: v=float(raw)
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) and v not in (-9999.0,-6999.0) else None

def disp(raw):
    n=num(raw)
    return "NA" if n is None else f"{n:.3f}"

def shift(k,half_hours):
    return (datetime.strptime(k,"%Y%m%d%H%M")+
            timedelta(minutes=half_hours*30)).strftime("%Y%m%d%H%M")

def source_scan(m,path,site):
    wanted={shift(k,h) for k in EVENTS[site]
            for h in list(range(-8,9))+[-96,-48,48,96]}
    found={};count=0
    with m.regular(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        fields=list(reader.fieldnames or ())
        if not CORE.issubset(fields) or len(fields)!=len(set(fields)):
            raise ValueError("Original FLUXMET lacks expected native column schema")
        temp_fields=[k for k in fields if k.upper().startswith(("TA","T_AIR"))]
        if "TA_F" not in temp_fields or "TA_F_QC" not in temp_fields:
            raise ValueError("Original temperature provenance lost")
        for row in reader:
            count+=1
            k=row["TIMESTAMP_START"]
            if k in wanted:
                if k in found:raise ValueError("Duplicate original event clock "+k)
                found[k]=row
    if count!=EXPECTED_ROWS[site] or not all(k in found for k in EVENTS[site]):
        raise ValueError("Original source row/time contract differs")
    return found,temp_fields,count

def selftest():
    assert sum(map(len,EVENTS.values()))==6 and len(EIGHT)==8
    assert len(EXPECTED_ROWS)==3
    assert all(len(v)==64 for v in ORIGINAL_SHA.values())
    assert all(len(v)==64 for v in STAGE14_SHA.values())
    assert shift("201903191200",1)=="201903191230"
    assert shift("201903191200",-1)=="201903191130"
    assert num("-9999")==None and num("0.718")==.718
    print("STAGE18 SELF-TEST PASS: six original events, time window clocks, QC2 provenance not presumed tower")

def audit():
    m=stage12()
    r12=json.loads(m.regular(STAGE12/"stage12_receipt.json").read_text())
    r14=json.loads(m.regular(STAGE14/"stage14_receipt.json").read_text())
    if (r12.get("target_unique_non_Syv_events")!=156 or
        r12.get("successfully_resolved")!=148 or r12.get("unresolved")!=8 or
        r12.get("Postv5_approved") is not False or
        r14.get("humidity_physical_candidate_count")!=8 or
        r14.get("still_unresolved_tower_temperature_science_hold_count")!=8):
        raise ValueError("Original Stage12/14 science gates changed")
    dec=read_tsv(m,STAGE12/"stage12_science_decisions.tsv")
    held={(r["site"],r["TIMESTAMP_START"]) for r in dec
          if not r["status"].startswith("RESOLVED")}
    if len(dec)!=156 or held!=EIGHT:
        raise ValueError("Eight pinned QC0 science HOLDs changed")
    stage14_manifest=STAGE14/"stage14_latest_ten_candidate_manifest.tsv"
    if m.sha(stage14_manifest)!=r14["latest_ten_manifest_sha256"]:
        raise ValueError("Stage14 ten-site manifest SHA invalid")
    selected=read_tsv(m,stage14_manifest)
    bysite={r["site"]:r for r in selected}
    if len(selected)!=10 or set(bysite)!=m.EXPECTED_SITES:
        raise ValueError("Wrong ten-site Stage14 manifest")
    selections,targets,reasons,originals=m.get_inputs()
    total=0
    for site,events in EVENTS.items():
        raw=originals[site]["native"]
        if m.sha(raw)!=ORIGINAL_SHA[site]:
            raise ValueError("Original FLUXMET SHA changed: "+site)
        s14=bysite[site]
        if (int(s14["rows"])!=EXPECTED_ROWS[site] or
            s14["source_SHA256"]!=STAGE14_SHA[site] or
            m.sha(Path(s14["source_path"]))!=STAGE14_SHA[site]):
            raise ValueError("Stage14 source not pinned: "+site)
        point=m.point_for(site,raw)
        oldpoint=r12["original_native_BIF_points"][site]
        if m.sha(Path(oldpoint["BIF_file"]))!=oldpoint["BIF_sha256"]:
            raise ValueError("Stage12 original BIF SHA changed")
        for key in ("latitude","longitude","offset_hours"):
            if abs(point[key]-oldpoint[key])>1e-4:
                raise ValueError("Original BIF location/clock changed")
        rows,ta_fields,n=source_scan(m,raw,site)
        print(f"\nSTAGE18 SITE {site} original_native_SHA={ORIGINAL_SHA[site]} rows={n}")
        print("STAGE18 ORIGINAL PRODUCT TA-RELATED COLUMNS:",", ".join(ta_fields) or "NONE")
        era_cols=[x for x in ta_fields if x not in ("TA_F","TA_F_QC")]
        for key,t0 in events.items():
            original=rows[key]
            t=num(original["TA_F"])
            if t is None or abs(t-t0)>.002 or original["TA_F_QC"].strip()!="0":
                raise ValueError("Pinned original T/QC0 changed: "+site+" "+key)
            v=num(original["VPD_F"])
            if m.physics(t,v):
                raise ValueError("Previously impossible original VPD now appears valid")
            total+=1
            print(f"\nSTAGE18 EVENT {site} {key} original_T_C={disp(t)} QC0 "
                  f"original_VPD_hPa={disp(v)} original_VPD_QC={original['VPD_F_QC']}")
            print("STAGE18 EXTRA SAME-ROW T SOURCE FIELDS:",
                  " ".join(f"{field}={original.get(field,'')}" for field in era_cols[:16]) or "NONE")
            print("  hh native_time TA_F_C TA_F_QC VPD_F_hPa VPD_F_QC TA_ERA_if_present")
            for step in range(-4,5):
                k=shift(key,step)
                row=rows.get(k)
                if row is None:
                    print(f"  {step:+3d} {k} MISSING_NATIVE_ROW")
                    continue
                print(f"  {step:+3d} {k} {disp(row['TA_F']):>8} "
                      f"{row['TA_F_QC']:>7} {disp(row['VPD_F']):>10} "
                      f"{row['VPD_F_QC']:>8} {disp(row.get('TA_ERA')):>18}")
            pre=rows.get(shift(key,-1));post=rows.get(shift(key,1))
            dt_pre=(t-num(pre["TA_F"])) if pre and num(pre["TA_F"]) is not None else None
            dt_post=(num(post["TA_F"])-t) if post and num(post["TA_F"]) is not None else None
            print("STAGE18 HALF-HOUR DELTA PRE->EVENT_C",disp(dt_pre),
                  "EVENT->POST_C",disp(dt_post),
                  "PRE_QC",pre.get("TA_F_QC") if pre else "MISSING",
                  "POST_QC",post.get("TA_F_QC") if post else "MISSING")
            for day in (-2,-1,1,2):
                p=rows.get(shift(key,day*48))
                print("STAGE18 SAME-CLOCK DAY",day,
                      "TA_C",disp(p.get("TA_F")) if p else "MISSING",
                      "QC",p.get("TA_F_QC") if p else "MISSING",
                      "TA_ERA",disp(p.get("TA_ERA")) if p else "MISSING")
            print("STAGE18 HOLD: QC2 neighbors are not independent raw-tower proof; no T revision")
    if total!=6:raise ValueError("Incorrect number of reviewed events")
    print("\nSTAGE18 RESULT: 6/6 NATIVE FLUXMET PROVENANCE WINDOWS AUDITED; 8/8 ORIGINAL T SCIENCE HOLDS PRESERVED")
    print("STAGE18 US-Syv 606 OLD HOLDS + 10 STAGE07 ERA JUMP SKIPS DEFERRED")
    print("STAGE18 READ ONLY: NO ORIGINAL/DERIVED SOURCE, CDS, DATM, CIME, SLURM OR MODEL WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    selftest()
    if args.audit:audit()

if __name__=="__main__":
    main()

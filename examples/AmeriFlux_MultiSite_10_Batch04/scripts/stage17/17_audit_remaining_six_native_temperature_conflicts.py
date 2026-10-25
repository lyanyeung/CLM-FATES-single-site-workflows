#!/usr/bin/env python3
"""Batch04 Stage17: READ-ONLY investigation of the six OTHER QC0-T disagreements.

Compare original native tower half-hours and Stage14 temperature-retained
candidate with already downloaded, verified ERA5-Land hourly T2m (mapped
with the original BIF UTC offset). Show +/-2h profiles and +/-6h baseline
tower-minus-grid anomalies, separately for each unresolved event.

This is evidence collection, NOT an automated tower-temperature correction.
--audit prints to stdout only; never downloads, makes forcing, changes a QC,
creates a DATM/CIME case, or submits SLURM. Requires pinned Stage13/Stage12/
Stage10 scripts beside this file, and immutable Stage12/14 outputs on IRIDIS.
"""
import argparse
import csv
import importlib.util
import json
import math
import statistics
from datetime import timedelta
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S12=ROOT/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
S14=ROOT/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
EVENTS={
 ("US-SP1","200710151730"):11.150,
 ("US-SP1","200801160800"):-8.211,
 ("US-SP1","200801160830"):-4.365,
 ("US-SP1","200802030800"):-3.613,
 ("US-SRG","201903191200"):0.718,
 ("US-Seg","201612271800"):0.015,
}
SITE_ROWS={"US-SP1":368208,"US-SRG":315600,"US-Seg":333120}
STAGE14_SHA={
 "US-SP1":"3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806",
 "US-SRG":"57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39",
 "US-Seg":"22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6",
}
ALL_EIGHT=set(EVENTS)|{("US-SP1","200010091800"),("US-SP1","200010091830")}

def load13():
    p=Path(__file__).resolve().with_name("13_inspect_eight_temperature_conflicts.py")
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing pinned Stage13 helper beside Stage17 script")
    spec=importlib.util.spec_from_file_location("b04_stage17_13",str(p))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def tsv(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing or linked manifest "+str(path))
    with path.open(encoding="utf-8-sig",newline="") as h:
        d=csv.DictReader(h,delimiter="\t")
        if not d.fieldnames or len(d.fieldnames)!=len(set(d.fieldnames)):
            raise ValueError("Invalid manifest fields")
        return list(d)

def near(a,b,atol=.002):
    return a is not None and b is not None and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=atol

def fmt(v):
    return "NA" if v is None or not math.isfinite(v) else f"{v:.3f}"

def selftest():
    assert len(EVENTS)==6
    assert set(s for s,_ in EVENTS)==set(SITE_ROWS)
    assert len(ALL_EIGHT)==8
    assert all(len(k)==12 and k.isdigit() for _,k in EVENTS)
    assert all(len(v)==64 for v in STAGE14_SHA.values())
    assert near(-8.211,-8.211)
    assert not near(-8.211,8.173)
    print("STAGE17 SELF-TEST PASS: six unique native conflicts, eight science HOLDs preserved; read-only")

def audit():
    s13=load13()
    s12=s13.load_stage12()
    ext=s12.helper()
    r12=json.loads(s12.regular(S12/"stage12_receipt.json").read_text())
    r14=json.loads(s12.regular(S14/"stage14_receipt.json").read_text())
    if (r12.get("target_unique_non_Syv_events")!=156 or
        r12.get("successfully_resolved")!=148 or r12.get("unresolved")!=8 or
        r12.get("Postv5_approved") is not False or
        r14.get("humidity_physical_candidate_count")!=8 or
        r14.get("still_unresolved_tower_temperature_science_hold_count")!=8):
        raise ValueError("Stage12 or Stage14 science gates changed")

    decision=tsv(S12/"stage12_science_decisions.tsv")
    held={(x["site"],x["TIMESTAMP_START"]) for x in decision
          if not x["status"].startswith("RESOLVED")}
    if len(decision)!=156 or held!=ALL_EIGHT:
        raise ValueError("Stage12 original eight unresolved exact timestamps changed")

    manifest=S14/"stage14_latest_ten_candidate_manifest.tsv"
    if s12.sha(manifest)!=r14["latest_ten_manifest_sha256"]:
        raise ValueError("Stage14 complete ten-site manifest SHA mismatch")
    mrows=tsv(manifest)
    m={x["site"]:x for x in mrows}
    if len(mrows)!=10 or set(m)!=s12.EXPECTED_SITES:
        raise ValueError("Stage14 manifest does not have exact ten sites")
    selections, oldtargets, grouping, originals=s12.get_inputs()

    print("STAGE17 SIX UNRESOLVED QC0 T SCIENCE EVENTS; Stage14 source T unchanged")
    for site in SITE_ROWS:
        path=Path(m[site]["source_path"])
        if (path.parent!=S14 or int(m[site]["rows"])!=SITE_ROWS[site] or
            m[site]["source_SHA256"]!=STAGE14_SHA[site] or
            s12.sha(path)!=STAGE14_SHA[site]):
            raise ValueError("Stage14 independently verified source mismatch: "+site)

        native=originals[site]["native"]
        n_sha=s12.sha(native)
        point=r12["original_native_BIF_points"][site]
        if s12.sha(Path(point["BIF_file"]))!=point["BIF_sha256"]:
            raise ValueError("Original BIF source integrity differs: "+site)
        independent_point=s12.point_for(site,native)
        for key in ("latitude","longitude","offset_hours"):
            if abs(float(point[key])-float(independent_point[key]))>1e-4:
                raise ValueError("Stage12 BIF location/offset discrepancy: "+site)

        targets=sorted(k for s,k in EVENTS if s==site)
        obs=s13.one_file(native,targets,SITE_ROWS[site])
        candidate=s13.one_file(path,targets,SITE_ROWS[site])
        years={int(s13.stamp(k).year) for k in targets}
        grids={}
        for year in sorted(years):
            gr=ext.response_receipt(site,year)
            if gr is None:
                raise ValueError(f"No previously SHA-verified ERA5-Land source {site} {year}; download is NOT authorised")
            grids[year]=ext.grid_read(gr,year,point)
        print(f"\nSTAGE17 SITE {site} original_native_SHA256={n_sha} stage14_SHA256={STAGE14_SHA[site]}")
        for stamp in targets:
            original=obs[stamp]
            derived=candidate[stamp]
            temp=s13.number(original["TA_F"])
            revised=s13.number(derived["TA_F"])
            if (not near(temp,EVENTS[site,stamp]) or not near(revised,temp) or
                original["TA_F_QC"].strip()!="0" or
                derived["TA_F_QC"].strip()!="0"):
                raise ValueError("Original or Stage14 QC0 target T changed: "+site+" "+stamp)
            if original["TIMESTAMP_END"]!=derived["TIMESTAMP_END"]:
                raise ValueError("Target native clock changed")
            native_time=s13.stamp(stamp)
            samples=[]
            for hh in range(-12,13):
                ts=native_time+timedelta(minutes=30*hh)
                key=ts.strftime("%Y%m%d%H%M")
                row=obs.get(key)
                if row is None:continue
                t=s13.number(row["TA_F"])
                q=(row.get("TA_F_QC") or "").strip()
                utc=ext.local_to_utc(key,point["offset_hours"])
                grid=s13.temp_at(grids[int(stamp[:4])],utc)
                residual=t-grid if t is not None and grid is not None else None
                samples.append((hh,key,t,q,grid,residual))
            target=next((x for x in samples if x[0]==0),None)
            if target is None or target[4] is None or target[5] is None:
                raise ValueError("Missing exact target hour grid comparison")
            baseline=[x[5] for x in samples if x[0]!=0 and
                      (site,x[1]) not in ALL_EIGHT and
                      x[3] in ("0","1") and x[5] is not None]
            med=statistics.median(baseline) if baseline else None
            mad=statistics.median(abs(x-med) for x in baseline) if baseline else None
            dist=target[5]-med if med is not None else None
            v_original=s13.number(original["VPD_F"])
            v_stage14=s13.number(derived["VPD_F"])
            saturation=s12.sat_c(temp) if hasattr(s12,"sat_c") else 6.112*math.exp(17.67*temp/(temp+243.5))
            if v_original is None or v_original<=saturation:
                raise ValueError("Target source VPD is not the expected impossible VPD")
            if not s12.physics(revised,v_stage14):
                raise ValueError("Stage14 numerical VPD closure failed")
            print(f"STAGE17 EVENT {site} {stamp} original_QC0_T_C={fmt(temp)} "
                  f"original_VPD_hPa={fmt(v_original)} stage14_VPD_hPa={fmt(v_stage14)} "
                  f"ERA5Land_T_C={fmt(target[4])} T_minus_grid_C={fmt(target[5])} "
                  f"baseline_n={len(baseline)} baseline_median_TminusGrid_C={fmt(med)} "
                  f"baseline_MAD_C={fmt(mad)} residual_outlier_from_baseline_C={fmt(dist)}")
            print("  HHoffset native_local_time tower_T_C native_T_QC grid_T_C tower_minus_grid_C")
            for hh,key,t,q,g,d in samples:
                if abs(hh)<=4:
                    print(f"  {hh:+3d} {key} {fmt(t):>10} {q:>11} {fmt(g):>9} {fmt(d):>18}")
            print("STAGE17 HOLD: numerical closure only; sensor validity not independently resolved")
    print("\nSTAGE17 RESULT: 6/6 ORIGINAL QC0 T CONFLICTS DIAGNOSED, 0 OFFICIAL SCIENCE HOLDS CLEARED")
    print("STAGE17 DEFERRED: two Stage15 temperature trial times remain science HOLD; US-Syv 606 old HOLDs + 10 ERA jump skips")
    print("STAGE17 READ ONLY: NO SOURCE/FLUXMET/DATM/CIME/SLURM WRITES OR CDS REQUESTS")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--audit",action="store_true")
    args=p.parse_args()
    selftest()
    if args.audit:audit()

if __name__=="__main__":
    main()

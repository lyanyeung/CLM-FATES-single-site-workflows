#!/usr/bin/env python3
"""Batch05 Stage09 — event-level 1750 low derived-water-RH source triage.

A scientific evidence ledger, NOT a repair. For all original native half-hours:
find water-formula derived RH <1%; distinguish RH<0 physically impossible from
0<=RH<1 extreme-but-not-impossible; compare RH provenance, consolidated F QC
and intermediate MDS QC, ERA's own humidity consistency, and hypothetical
tower-T + ERA implied vapour pressure. No clocks, data, model, or queue changes.

Assumptions only for screening: TA in deg C; VPD in hPa; Buck/Magnus-like
es_water=6.112 exp(17.67*T/(T+243.5)) in hPa. The released VPD phase and
elevation adjustment remain to be independently documented.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re

DEFAULT_ROOT=Path(os.environ.get("FLUXNET_SITES_ROOT",
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
SITES={
    "US-UiD":"2008-2024_v1.3_r1","US-UMB":"FULLSET_2007-2021_3-5",
    "US-UMd":"2007-2025_v1.3_r1","US-Var":"2000-2025_v1.3_r1",
    "US-Vcm":"2007-2025_v1.3_r1","US-Vcp":"2007-2025_v1.3_r1",
    "US-WCr":"1999-2025_v1.3_r1","US-Whs":"2007-2025_v1.3_r1",
    "US-Wjs":"2007-2025_v1.3_r1","US-Wkg":"2004-2025_v1.3_r1"}
SOURCE_SHA={
    "US-UiD":"130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318",
    "US-UMB":"ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6",
    "US-UMd":"e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2",
    "US-Var":"664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2",
    "US-Vcm":"c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c",
    "US-Vcp":"eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42",
    "US-WCr":"f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506",
    "US-Whs":"653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca",
    "US-Wjs":"9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6",
    "US-Wkg":"f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"}
COLUMNS=("TIMESTAMP_START","TA_F","VPD_F","RH","TA_F_QC","VPD_F_QC",
         "TA_F_MDS","VPD_F_MDS","TA_F_MDS_QC","VPD_F_MDS_QC",
         "TA_ERA","VPD_ERA")


def number(s):
    try:
        n=float(s)
    except (ValueError,TypeError):
        return None
    return n if math.isfinite(n) and n not in (-9999.,-6999.) else None


def es(t):
    if t is None or not -80<=t<=60:
        return None
    return 6.112*math.exp(17.67*t/(243.5+t))


def phys_humidity(t,vpd):
    saturation=es(t)
    if saturation is None or vpd is None:
        return "MISSING"
    if vpd < 0 or vpd > saturation:
        return "NONPHYSICAL"
    return "MATH_FEASIBLE"


def era_pair(t_tower,era_t,era_vpd):
    s=es(era_t)
    native_sat=es(t_tower)
    if s is None or era_vpd is None or native_sat is None:
        return "ERA_OR_T_MISSING"
    e=s-era_vpd
    if not 0<=e<=s:
        return "ERA_INTERNAL_NONPHYSICAL"
    if 0<=e<=native_sat:
        return "ERA_E_TOWER_T_MATH_FEASIBLE"
    return "ERA_E_TOWER_T_NOT_FEASIBLE"


def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def assess(stream):
    r=csv.DictReader(stream)
    names=r.fieldnames or []
    if len(names)!=len(set(names)) or not set(COLUMNS).issubset(names):
        raise ValueError("missing/duplicate required source columns: "+str(set(COLUMNS)-set(names)))
    counts=Counter()
    by_source=defaultdict(Counter)
    examples=defaultdict(list)
    annual=defaultdict(Counter)
    long_events=[]
    active=None
    prev_time=None
    total=0

    def close_episode():
        nonlocal active
        if active:
            long_events.append(active)
            active=None

    for total,row in enumerate(r,1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed CSV row "+str(total))
        stamp=row["TIMESTAMP_START"]
        if not re.fullmatch(r"\d{12}",stamp):
            raise ValueError("invalid timestamp "+repr(stamp))
        at=datetime.strptime(stamp,"%Y%m%d%H%M")
        if prev_time is not None and at-prev_time!=timedelta(minutes=30):
            raise ValueError("non-30minute source chronology: "+stamp)
        prev_time=at
        v={n:number(row[n]) for n in
           ("TA_F","VPD_F","RH","TA_F_MDS","VPD_F_MDS","TA_ERA","VPD_ERA")}
        ta,vpd=v["TA_F"],v["VPD_F"]
        saturation=es(ta)
        derived=100*(1-vpd/saturation) if saturation is not None and vpd is not None else None
        if derived is None or derived>=1:
            close_episode()
            continue
        qta,qv=row["TA_F_QC"].strip(),row["VPD_F_QC"].strip()
        qtm,qvm=row["TA_F_MDS_QC"].strip(),row["VPD_F_MDS_QC"].strip()
        if qta not in ("0","1","2") or qv not in ("0","1","2"):
            raise ValueError("unknown consolidated QC at "+stamp)
        if qtm not in ("0","1","2","3","-9999") or qvm not in ("0","1","2","3","-9999"):
            raise ValueError("unknown intermediate MDS QC at "+stamp)
        group=qta+"/"+qv
        typ="NEGATIVE_DERIVED_RH" if derived<0 else "NONNEGATIVE_BELOW_1PCT"
        qpair=qtm+"/"+qvm
        mds=phys_humidity(v["TA_F_MDS"],v["VPD_F_MDS"])
        era_self=phys_humidity(v["TA_ERA"],v["VPD_ERA"])
        hypot=era_pair(ta,v["TA_ERA"],v["VPD_ERA"])
        rh=v["RH"]
        if rh is None:
            rh_status="ORIGINAL_RH_MISSING"
        elif rh<0 or rh>100:
            rh_status="ORIGINAL_RH_OUTSIDE_0_100"
        elif rh<1:
            rh_status="ORIGINAL_RH_LT1"
        elif rh<5:
            rh_status="ORIGINAL_RH_1_TO_LT5"
        else:
            rh_status="ORIGINAL_RH_GE5"
        if qv=="2":
            origin="ERA_VPD"
        elif qv=="1":
            origin="GOOD_MDS_VPD"
        else:
            origin="MEASURED_VPD"
        count_labels=(typ,group,"MDS_"+mds,"ERA_"+era_self,hypot,
                      rh_status,origin,"MDS_QC_"+qpair)
        counts["LOW_DERIVED_RH_LT1"]+=1
        counts["TYPE_"+typ]+=1
        if qv=="2":
            counts["VPD_F_QC2"]+=1
            if qvm in ("2","3"):
                counts["QC2_HAS_LOWER_QUALITY_MDS"]+=1
        if qta=="0" and qv=="0":
            counts["BOTH_MEASURED_QC0"]+=1
        for lab in count_labels:
            counts[lab]+=1
        by_source[group][typ]+=1
        by_source[group]["MDS_"+mds]+=1
        by_source[group][hypot]+=1
        annual[stamp[:4]][typ]+=1
        key=(typ,group,mds,era_self,hypot,rh_status)
        if len(examples[str(key)])<3:
            examples[str(key)].append({
                "time":stamp,"T":ta,"VPD_F":vpd,"RH_derived":round(derived,5),
                "RH_original":rh,"TA_F_QC":qta,"VPD_F_QC":qv,
                "TA_MDS_QC":qtm,"VPD_MDS_QC":qvm,
                "TA_MDS":v["TA_F_MDS"],"VPD_MDS":v["VPD_F_MDS"],
                "TA_ERA":v["TA_ERA"],"VPD_ERA":v["VPD_ERA"],
                "MDS_pair":mds,"ERA_pair":era_self,
                "ERA_e_with_tower_T":hypot})
        if active is not None:
            active["half_hours"]+=1
            active["end"]=stamp
            active["negative"]+=int(derived<0)
        else:
            active=dict(start=stamp,end=stamp,half_hours=1,negative=int(derived<0))
    close_episode()
    if total==0:
        raise ValueError("empty native source")
    long_events.sort(key=lambda e:(-e["half_hours"],e["start"]))
    return {"rows":total,"counts":dict(counts),
            "by_TA_VPD_source_QC":{k:dict(v) for k,v in sorted(by_source.items())},
            "by_year":{k:dict(v) for k,v in sorted(annual.items())},
            "low_RH_episode_count":len(long_events),
            "longest_episodes":long_events[:8],
            "representative_records":dict(examples)}


def inspect_site(site,root):
    package="AMF_"+site+"_FLUXNET_"+SITES[site]
    directory=root/site/"forcing"/"raw"/package
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("missing/unsafe original folder "+str(directory))
    kind="FULLSET" if site=="US-UMB" else "FLUXMET"
    pat=re.compile("AMF_"+re.escape(site)+"_FLUXNET_"+kind+r"_(HH|HR)_.+[.]csv",re.I)
    found=[p for p in directory.iterdir() if pat.fullmatch(p.name)]
    if len(found)!=1 or found[0].is_symlink() or not found[0].is_file():
        raise ValueError("expected exactly one regular original HH/HR source file")
    f=found[0]
    expected=SOURCE_SHA[site]
    actual=sha256(f)
    if actual!=expected:
        raise ValueError("STOP source fingerprint changed "+site+": "+actual)
    before=(f.stat().st_size,f.stat().st_mtime_ns)
    with f.open(encoding="utf-8-sig",newline="") as stream:
        report=assess(stream)
    if before!=(f.stat().st_size,f.stat().st_mtime_ns):
        raise ValueError("source file changed during audit")
    print("STAGE09_VERIFIED",site,actual,flush=True)
    print("STAGE09_LOW_RH_Triage",site,json.dumps(report,sort_keys=True),flush=True)
    print("SITE_STAGE09_DONE",site,flush=True)


def self_test():
    import io
    header=",".join(COLUMNS)+"\n"
    sample=[
        "200701170400,-14.254,2.387,89.08,2,2,-10.306,2.237,2,2,-14.254,2.387",
        "200701170430,-3.424,6.643,-9999,0,2,-3.424,8.991,0,2,7.022,6.643",
        "200701170500,10,12.3,-9999,0,1,10,12.3,0,1,10,5",
        "200701170530,20,0,100,0,0,20,0,0,0,20,5",
        "200701170600,20,23.2,0.7,0,0,20,23.2,0,0,20,4"
    ]
    r=assess(io.StringIO(header+"\n".join(sample)+"\n"))
    c=r["counts"]
    assert r["rows"]==5
    assert c["LOW_DERIVED_RH_LT1"]==4
    assert c["TYPE_NEGATIVE_DERIVED_RH"]==3
    assert c["TYPE_NONNEGATIVE_BELOW_1PCT"]==1
    assert c["VPD_F_QC2"]==2
    assert c["BOTH_MEASURED_QC0"]==1
    assert c["ERA_NONPHYSICAL"]==1 and c["ERA_INTERNAL_NONPHYSICAL"]==1
    assert c["MDS_NONPHYSICAL"]>=2
    assert r["low_RH_episode_count"]==2
    print("STAGE09 SELF-TEST PASS | zero/negative physical split;"
          " MDS/ERA shadow, RH provenance holds, episodes; NO WRITES")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root",type=Path,default=DEFAULT_ROOT)
    p.add_argument("--sites",nargs="+",choices=list(SITES))
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        self_test()
        return 0
    selected=args.sites or list(SITES)
    if len(set(selected))!=len(selected):
        p.error("duplicate site")
    print("STAGE09 | low-RH complete original-source triage | READ ONLY")
    print("Negative RH is physically impossible under assumed water formula;"
          " 0<=RH<1% extreme but not automatically impossible.")
    print("MDS math feasible is not MDS quality approval; any QC2/3 remains HOLD.")
    print("ERA pair/tower-T compatibility is hypothetical, not approved humidity forcing.")
    failures=[]
    for s in selected:
        print("========== "+s+" ==========",flush=True)
        try:
            inspect_site(s,args.sites_root.expanduser())
        except (OSError,ValueError,KeyError,csv.Error) as e:
            failures.append(s)
            print("SITE_STAGE09_FAILED",s,repr(e),flush=True)
    print("STAGE09 SUMMARY audited={}/{} failed={}".format(
        len(selected)-len(failures),len(selected),",".join(failures) or "none"))
    print("NO ORIGINAL OR FORCING WRITES; NO AUTOMATIC REPLACEMENT; NO CLOCK SHIFT; NO SLURM")
    return bool(failures)


if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Batch05 Stage07: verify FLUXNET consolidated-variable QC source provenance.

READ-ONLY, all original half-hours, focus on inconsistent humidity records.
Official FLUXNET FLUXMET/FULLSET convention for TA_F_QC/VPD_F_QC at HH:
  0 measured, 1 good-quality MDS gapfill, 2 downscaled ERA.
The label convention is local standard time. This script does NOT convert
timestamps, infer RH sensor origin, or approve use of reanalysis.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re

ROOT=Path(os.environ.get("FLUXNET_SITES_ROOT",
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
SUFFIXES={
    "US-UiD":"2008-2024_v1.3_r1",
    "US-UMB":"FULLSET_2007-2021_3-5",
    "US-UMd":"2007-2025_v1.3_r1",
    "US-Var":"2000-2025_v1.3_r1",
    "US-Vcm":"2007-2025_v1.3_r1",
    "US-Vcp":"2007-2025_v1.3_r1",
    "US-WCr":"1999-2025_v1.3_r1",
    "US-Whs":"2007-2025_v1.3_r1",
    "US-Wjs":"2007-2025_v1.3_r1",
    "US-Wkg":"2004-2025_v1.3_r1"
}
EXPECTED_SOURCE_SHA={
    "US-UiD":"130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318",
    "US-UMB":"ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6",
    "US-UMd":"e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2",
    "US-Var":"664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2",
    "US-Vcm":"c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c",
    "US-Vcp":"eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42",
    "US-WCr":"f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506",
    "US-Whs":"653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca",
    "US-Wjs":"9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6",
    "US-Wkg":"f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"
}
# Printed values generally at 0.001 precision. This threshold is a test for
# copying/rounding only, not a tolerance for scientifically agreeing data.
ROUNDTRIP_TOL_HPA=0.002
ROUNDTRIP_TOL_DEGC=0.002

def num(raw):
    try:
        v=float(raw)
        if math.isfinite(v) and v not in (-9999., -6999.):
            return v
    except (TypeError,ValueError):
        pass
    return None

def es(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -80<=t<=60 else None

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda: fd.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def label_parse(label):
    if not re.fullmatch(r"\d{12}",label or ""):
        raise ValueError("bad timestamp: "+repr(label))
    datetime.strptime(label,"%Y%m%d%H%M")
    return label

def select_file(folder, site, category):
    patt=re.compile(r"AMF_"+re.escape(site)+r"_FLUXNET_"+
                    category+r"_(HH|HR)_.+[.]csv",re.I)
    candidates=[p for p in folder.iterdir() if patt.fullmatch(p.name)]
    if len(candidates)!=1 or candidates[0].is_symlink() or not candidates[0].is_file():
        raise ValueError("expected 1 regular "+category+" HH CSV, got "+str(len(candidates)))
    return candidates[0]

def native_events(stream):
    r=csv.DictReader(stream)
    fields=r.fieldnames or []
    if len(fields)!=len(set(fields)) or "TIMESTAMP_START" not in fields:
        raise ValueError("invalid native CSV header")
    needed=("TA_F","VPD_F","RH","TA_F_QC","VPD_F_QC")
    missing=[x for x in needed if x not in fields]
    if missing:
        raise ValueError("missing native required columns: "+str(missing))
    optional=("TA_F_MDS","VPD_F_MDS","TA_F_MDS_QC","VPD_F_MDS_QC",
              "TA_ERA","VPD_ERA","RH_QC","TA","VPD")
    avail={k:(k in fields) for k in optional}
    events={}
    overall=Counter()
    flag_by_qc=defaultdict(Counter)
    mds_match=Counter()
    count=0
    for count,row in enumerate(r,1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("native row width error "+str(count))
        t=label_parse(row["TIMESTAMP_START"])
        ta,vpd,rh=num(row["TA_F"]),num(row["VPD_F"]),num(row["RH"])
        tq,vq=row["TA_F_QC"].strip(),row["VPD_F_QC"].strip()
        if tq not in ("0","1","2") or vq not in ("0","1","2"):
            raise ValueError("unexpected TA_F/VPD_F QC at "+t+": "+tq+"/"+vq)
        qc=tq+"/"+vq
        overall["total_rows"]+=1
        overall["qc_pair_"+qc]+=1
        sat=es(ta)
        d=100*(1-vpd/sat) if sat is not None and vpd is not None else None
        flags=[]
        if d is not None and d<1:
            flags.append("DERIVED_RH_LT1")
        if rh is not None and (rh<0 or rh>100):
            flags.append("NATIVE_RH_OUTSIDE_0_100")
        if rh is not None and 0<=rh<=100 and d is not None and abs(rh-d)>10:
            flags.append("RH_DISAGREEMENT_GT10PP")
        if vpd is not None and vpd<0:
            flags.append("NEGATIVE_VPD")
        if flags:
            if t in events:
                raise ValueError("duplicate native flagged timestamp: "+t)
            ev={"time":t,"flags":flags,"qc_ta":tq,"qc_vpd":vq,
                "TA_F":ta,"VPD_F":vpd,"RH_original":rh,
                "RH_derived":d}
            for candidate in optional:
                if avail[candidate]:
                    ev[candidate]=num(row[candidate]) if not candidate.endswith("_QC") else row[candidate]
            events[t]=ev
            overall["unique_source_flags"]+=1
            for f in flags:
                overall["flag_"+f]+=1
                flag_by_qc[f][qc]+=1
            if avail["TA_F_MDS"] and tq in ("0","1"):
                aa=num(row["TA_F_MDS"])
                mds_match["TA_QC01_MDS_available"]+=int(aa is not None)
                mds_match["TA_QC01_MDS_equal"]+=int(aa is not None and ta is not None and
                    abs(ta-aa)<=ROUNDTRIP_TOL_DEGC)
            if avail["VPD_F_MDS"] and vq in ("0","1"):
                vv=num(row["VPD_F_MDS"])
                mds_match["VPD_QC01_MDS_available"]+=int(vv is not None)
                mds_match["VPD_QC01_MDS_equal"]+=int(vv is not None and vpd is not None and
                    abs(vpd-vv)<=ROUNDTRIP_TOL_HPA)
    if count==0:
        raise ValueError("empty source")
    return events,{"rows":count,"optional_header_inventory":avail,
        "total_flag_counts":dict(overall),
        "flags_by_TA_VPD_QC":{k:dict(v) for k,v in flag_by_qc.items()},
        "MDS_lineage_shadow":dict(mds_match)}

def era_event_join(stream,events):
    r=csv.DictReader(stream)
    fields=r.fieldnames or []
    needed=("TIMESTAMP_START","TA_ERA","VPD_ERA")
    if len(fields)!=len(set(fields)) or not set(needed).issubset(fields):
        raise ValueError("ERA CSV missing unique timestamp TA_ERA VPD_ERA")
    seen=set()
    counts=Counter()
    byflag=defaultdict(Counter)
    examples=defaultdict(list)
    rows=0
    for rows,row in enumerate(r,1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("ERA CSV row-width error "+str(rows))
        t=label_parse(row["TIMESTAMP_START"])
        if t not in events:
            continue
        if t in seen:
            raise ValueError("ERA duplicate event timestamp "+t)
        seen.add(t)
        e=events[t]
        et,ev=num(row["TA_ERA"]),num(row["VPD_ERA"])
        tc,vc=e["qc_ta"],e["qc_vpd"]
        counts["ERA_exact_label_match"]+=1
        observations={}
        for variable,orig,other,q in [
            ("TA",e["TA_F"],et,tc),
            ("VPD",e["VPD_F"],ev,vc)]:
            if q!="2":
                continue
            key=variable+"_QC2"
            counts[key+"_tested"]+=1
            tol=ROUNDTRIP_TOL_DEGC if variable=="TA" else ROUNDTRIP_TOL_HPA
            if orig is not None and other is not None and abs(orig-other)<=tol:
                counts[key+"_matches_ERA"]+=1
                observations[key]="MATCHES_ERA"
            else:
                counts[key+"_differs_or_missing_ERA"]+=1
                observations[key]="NOT_VERIFIED"
        sat=es(et)
        if sat is None or ev is None or not (0<=ev<=sat):
            counts["ERA_internal_humidity_unusable_under_water_formula"]+=1
            observations["ERA_humidity"]="UNUSABLE_WATER_FORMULA"
        for f in e["flags"]:
            byflag[f]["matched"]+=1
            for key,value in observations.items():
                if key.endswith("QC2") and value=="MATCHES_ERA":
                    byflag[f][key+"_matches_ERA"]+=1
                if key=="ERA_humidity":
                    byflag[f][value]+=1
            if len(examples[f])<5:
                examples[f].append({
                    "time":t,"original":{"TA_F":e["TA_F"],"VPD_F":e["VPD_F"],
                        "RH":e["RH_original"],"TA_F_QC":tc,"VPD_F_QC":vc},
                    "era":{"TA_ERA":et,"VPD_ERA":ev},
                    "lineage_screen":observations
                })
    counts["ERA_event_unmatched"]=len(events)-len(seen)
    return {"ERA_rows":rows,"counts":dict(counts),
       "counts_by_source_flag":{k:dict(v) for k,v in byflag.items()},
       "examples":dict(examples)}

def audit_site(site,root):
    pkg="AMF_"+site+"_FLUXNET_"+SUFFIXES[site]
    folder=root/site/"forcing"/"raw"/pkg
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("expected extracted regular source folder "+str(folder))
    source=select_file(folder,site,"FULLSET" if site=="US-UMB" else "FLUXMET")
    era=select_file(folder,site,"ERA5")
    expected=EXPECTED_SOURCE_SHA[site]
    actual=sha(source)
    if actual!=expected:
        raise ValueError("original CSV SHA changed, stop: "+site+" "+actual)
    before=tuple((p.stat().st_size,p.stat().st_mtime_ns) for p in [source,era])
    with source.open(encoding="utf-8-sig",newline="") as fd:
        events,original=native_events(fd)
    with era.open(encoding="utf-8-sig",newline="") as fd:
        related=era_event_join(fd,events)
    after=tuple((p.stat().st_size,p.stat().st_mtime_ns) for p in [source,era])
    if before!=after:
        raise ValueError("original input changed during audit")
    if related["counts"].get("ERA_event_unmatched",0)>0:
        raise ValueError("event timestamps not all matched at native printed label")
    print("SITE_STAGE07_SOURCE",site,source.name,actual,era.name,flush=True)
    print("STAGE07_NATIVE_LINEAGE",site,json.dumps(original,sort_keys=True),flush=True)
    print("STAGE07_ERA_LINEAGE",site,json.dumps(related,sort_keys=True),flush=True)
    print("SITE_STAGE07_DONE",site,flush=True)

def self_test():
    native=("TIMESTAMP_START,TA_F,VPD_F,RH,TA_F_QC,VPD_F_QC,TA_F_MDS,VPD_F_MDS\n"
       "200701170400,-14.254,2.387,89.08,2,2,-9999,-9999\n"
       "200701170430,-3.424,6.643,-9999,0,2,-3.424,-9999\n"
       "200701170500,10,4,90,1,1,10,4\n"
       "200701170530,10,4,67.5,0,0,10,4\n")
    era=("TIMESTAMP_START,TA_ERA,VPD_ERA\n"
       "200701170400,-14.254,2.387\n"
       "200701170430,7.022,6.643\n"
       "200701170500,11,2\n"
       "200701170530,12,3\n")
    flagged,s=native_events(io.StringIO(native))
    m=era_event_join(io.StringIO(era),flagged)
    c=m["counts"]
    assert s["total_flag_counts"]["unique_source_flags"]==3
    assert s["total_flag_counts"]["flag_DERIVED_RH_LT1"]==2
    assert s["total_flag_counts"]["flag_RH_DISAGREEMENT_GT10PP"]==2
    assert c["ERA_exact_label_match"]==3
    assert c["TA_QC2_matches_ERA"]==1
    assert c["VPD_QC2_matches_ERA"]==2
    assert c["ERA_internal_humidity_unusable_under_water_formula"]==1
    assert s["MDS_lineage_shadow"]["VPD_QC01_MDS_equal"]==1
    print("STAGE07 SELF-TEST PASS | QC2=ERA inheritance,"
          " QC1=MDS header shadow, QC0 measured category;"
          " no source writes")

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--sites-root",type=Path,default=ROOT)
    a.add_argument("--sites",nargs="+",choices=list(SUFFIXES))
    a.add_argument("--self-test",action="store_true")
    args=a.parse_args()
    if args.self_test:
        self_test()
        return 0
    sites=args.sites or list(SUFFIXES)
    if len(set(sites))!=len(sites):
        a.error("site names must be unique")
    print("STAGE07 READ-ONLY QC 0 measured / QC 1 MDS / QC 2 ERA lineage")
    print("Uses official FLUXNET consolidated HH QC meaning; site release still needs metadata review.")
    print("Exact printed-label event joins are for source lineage; no timezone shift.")
    failed=[]
    for site in sites:
        print("==========",site,"==========",flush=True)
        try:
            audit_site(site,args.sites_root.expanduser())
        except (OSError,ValueError,KeyError,csv.Error) as e:
            failed.append(site)
            print("SITE_STAGE07_FAILED",site,repr(e),flush=True)
    print("STAGE07 SUMMARY audited={}/{} failed={}".format(
        len(sites)-len(failed),len(sites),",".join(failed) or "none"))
    print("NO WRITES; NO ERA REPAIR; NO RH ADOPTION; NO UTC CONVERSION; NO SLURM")
    return int(bool(failed))

if __name__=="__main__":
    raise SystemExit(main())

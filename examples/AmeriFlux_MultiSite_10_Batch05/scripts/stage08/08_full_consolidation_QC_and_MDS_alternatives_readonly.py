#!/usr/bin/env python3
"""Batch05 Stage08: FULL-row consolidated QC provenance and MDS alternative screen.

Read-only. Unlike Stage07 (events only), tests FLUXNET *_F source selection for
EVERY native half-hour: QC 0/1 -> F_MDS, QC 2 -> ERA; simultaneously inspect
*_F_MDS_QC (0 measured, 1 good, 2 medium, 3 poor) when F_QC=2.

No proposed replacement may be applied automatically, especially not by
promoting poor-quality MDS (code 2/3) or assuming the RH column is measured.
The reanalysis values in the native source are diagnostic only; no clocks are
shifted. Diagnostic water es(T) assumes deg C and VPD hPa.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re

ROOT=Path(os.environ.get("FLUXNET_SITES_ROOT",
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
SITES={
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
EXPECTED_SHA={
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
NEEDED=("TIMESTAMP_START","TA_F","VPD_F","RH",
        "TA_F_QC","VPD_F_QC",
        "TA_F_MDS","VPD_F_MDS",
        "TA_F_MDS_QC","VPD_F_MDS_QC",
        "TA_ERA","VPD_ERA")
TOL=0.002

def num(x):
    try:
        v=float(x)
        if math.isfinite(v) and v not in (-9999.0,-6999.0):
            return v
    except (ValueError,TypeError):
        pass
    return None

def es(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -80<=t<=60 else None

def same(a,b):
    return a is not None and b is not None and abs(a-b)<=TOL

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def audit(stream):
    r=csv.DictReader(stream)
    cols=r.fieldnames or []
    if len(cols)!=len(set(cols)) or not set(NEEDED).issubset(cols):
        raise ValueError("missing or ambiguous Stage08 required original columns: "+
                         str(sorted(set(NEEDED)-set(cols))))
    counts=Counter()
    by_event=defaultdict(Counter)
    by_vpdqc=defaultdict(Counter)
    examples=defaultdict(list)
    total=0
    for total,row in enumerate(r,1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed CSV source row "+str(total))
        label=row["TIMESTAMP_START"]
        if not re.fullmatch(r"\d{12}",label):
            raise ValueError("invalid timestamp "+repr(label))
        datetime.strptime(label,"%Y%m%d%H%M")
        data={k:num(row[k]) for k in
              ("TA_F","VPD_F","RH","TA_F_MDS","VPD_F_MDS",
               "TA_ERA","VPD_ERA")}
        tq=row["TA_F_QC"].strip()
        vq=row["VPD_F_QC"].strip()
        tmq=row["TA_F_MDS_QC"].strip()
        vmq=row["VPD_F_MDS_QC"].strip()
        if tq not in ("0","1","2") or vq not in ("0","1","2"):
            raise ValueError("unexpected consolidated F_QC code at "+label)
        counts["rows"]+=1
        counts["qc_pair_"+tq+"/"+vq]+=1
        for kind,q,mq in (("TA",tq,tmq),("VPD",vq,vmq)):
            f=data[kind+"_F"]
            m=data[kind+"_F_MDS"]
            e=data[kind+"_ERA"]
            counts[kind+"_F_QC_"+q]+=1
            counts[kind+"_MDS_QC_"+mq]+=1
            if q in ("0","1"):
                counts[kind+"_QC01_tested"]+=1
                if same(f,m):
                    counts[kind+"_QC01_MDS_equal"]+=1
                else:
                    counts[kind+"_QC01_MDS_mismatch_or_missing"]+=1
                if mq not in ("0","1"):
                    counts[kind+"_QC01_MDS_QC_not01"]+=1
            else:
                counts[kind+"_QC2_tested"]+=1
                if same(f,e):
                    counts[kind+"_QC2_ERA_equal"]+=1
                else:
                    counts[kind+"_QC2_ERA_mismatch_or_missing"]+=1
                if mq in ("0","1"):
                    counts[kind+"_QC2_MDS_QC01_selection_contradiction"]+=1
                if mq in ("2","3"):
                    counts[kind+"_QC2_MDS_QC23_lower_quality"]+=1
                if m is not None:
                    counts[kind+"_QC2_MDS_value_present"]+=1
        ta,vpd,rh=(data[k] for k in ("TA_F","VPD_F","RH"))
        sat=es(ta)
        calc=100*(1-vpd/sat) if vpd is not None and sat is not None else None
        flags=[]
        if calc is not None and calc<1:
            flags.append("RH_DERIVED_LT1")
        if rh is not None and (rh<0 or rh>100):
            flags.append("RH_NATIVE_OUTSIDE_0_100")
        if rh is not None and 0<=rh<=100 and calc is not None and abs(calc-rh)>10:
            flags.append("RH_CONFLICT_GT10PP")
        if vpd is not None and vpd<0:
            flags.append("VPD_NEGATIVE")
        if not flags:
            continue
        counts["unique_flagged"]+=1
        ma, mv=(data[k] for k in ("TA_F_MDS","VPD_F_MDS"))
        m_sat=es(ma)
        m_pair=(m_sat is not None and mv is not None and 0<=mv<=m_sat)
        if m_sat is None or mv is None:
            m_state="MDS_PAIR_MISSING"
        elif m_pair:
            m_state="MDS_PAIR_MATH_FEASIBLE"
        else:
            m_state="MDS_PAIR_MATH_NONPHYSICAL"
        # This is a physical check, NOT data quality approval.
        for flag in flags:
            by_event[flag]["events"]+=1
            by_event[flag]["QC_"+tq+"/"+vq]+=1
            by_event[flag][m_state]+=1
            by_event[flag]["TA_MDS_QC_"+tmq]+=1
            by_event[flag]["VPD_MDS_QC_"+vmq]+=1
            if tq=="2" or vq=="2":
                by_event[flag]["ONE_OR_BOTH_F_QC2"]+=1
                if tmq in ("2","3") or vmq in ("2","3"):
                    by_event[flag]["LOWER_QUALITY_MDS_PRESENT_DO_NOT_AUTO_ADOPT"]+=1
            if len(examples[flag])<5:
                examples[flag].append({
                    "time":label,"qc":tq+"/"+vq,
                    "TA_F":ta,"VPD_F":vpd,"RH_original":rh,
                    "RH_water_calc":calc,
                    "TA_MDS":ma,"VPD_MDS":mv,
                    "TA_MDS_QC":tmq,"VPD_MDS_QC":vmq,
                    "MDS_pair":m_state,
                    "TA_ERA":data["TA_ERA"],"VPD_ERA":data["VPD_ERA"]})
        if tq=="2" or vq=="2":
            by_vpdqc[vq]["FLAGGED_QC2_COMBINATION"]+=1
            by_vpdqc[vq][m_state]+=1
            by_vpdqc[vq]["TA_MDS_QC_"+tmq]+=1
            by_vpdqc[vq]["VPD_MDS_QC_"+vmq]+=1
    if total==0:
        raise ValueError("empty native source")
    return {
        "counts":dict(counts),
        "by_source_alarm":{k:dict(v) for k,v in sorted(by_event.items())},
        "among_flagged_at_least_one_QC2_by_VPD_F_QC":{
            k:dict(v) for k,v in sorted(by_vpdqc.items())},
        "examples":dict(examples)
    }

def site(site,root):
    release="AMF_"+site+"_FLUXNET_"+SITES[site]
    folder=root/site/"forcing"/"raw"/release
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("source extraction folder missing or symlink "+str(folder))
    kind="FULLSET" if site=="US-UMB" else "FLUXMET"
    pat=re.compile("AMF_"+re.escape(site)+
                   "_FLUXNET_"+kind+r"_(HH|HR)_.+[.]csv",re.I)
    matches=[p for p in folder.iterdir() if pat.fullmatch(p.name)]
    if len(matches)!=1 or matches[0].is_symlink() or not matches[0].is_file():
        raise ValueError("expected exactly one regular original HH/HR source")
    p=matches[0]
    digest=sha(p)
    if digest!=EXPECTED_SHA[site]:
        raise ValueError("Stage07 original input checksum mismatch "+digest)
    before=p.stat().st_size,p.stat().st_mtime_ns
    with p.open(encoding="utf-8-sig",newline="") as stream:
        report=audit(stream)
    after=p.stat().st_size,p.stat().st_mtime_ns
    if before!=after:
        raise ValueError("native file changed during read-only scan")
    print("STAGE08_SOURCE",site,p.name,digest,flush=True)
    print("STAGE08_SITE_FULL_QC",site,json.dumps(report,sort_keys=True),flush=True)
    print("SITE_STAGE08_DONE",site,flush=True)

def self_test():
    import io
    raw=("TIMESTAMP_START,TA_F,VPD_F,RH,TA_F_QC,VPD_F_QC,TA_F_MDS,VPD_F_MDS,TA_F_MDS_QC,VPD_F_MDS_QC,TA_ERA,VPD_ERA\n"
         "200701170400,-14.254,2.387,89.08,2,2,-15,0.5,2,3,-14.254,2.387\n"
         "200804091100,-3.424,6.643,-9999,0,2,-3.424,0.1,0,2,7.022,6.643\n"
         "200804091130,10,4,90,1,1,10,4,1,1,11,2\n"
         "200804091200,10,4,67.5,0,0,10,4,0,0,12,3\n"
         "200804091230,10,14,60,2,2,10,1,0,1,10,14\n")
    x=audit(io.StringIO(raw));c=x["counts"]
    assert c["rows"]==5
    assert c["unique_flagged"]==4
    assert c["TA_QC2_tested"]==2 and c["TA_QC2_ERA_equal"]==2
    assert c["VPD_QC2_tested"]==3 and c["VPD_QC2_ERA_equal"]==3
    assert c["VPD_QC2_MDS_QC23_lower_quality"]==2
    assert c["TA_QC2_MDS_QC01_selection_contradiction"]==1
    assert c["VPD_QC2_MDS_QC01_selection_contradiction"]==1
    assert x["by_source_alarm"]["RH_CONFLICT_GT10PP"]["events"]==2
    print("STAGE08 SELF-TEST PASS | entire-row consolidation; QC2 poor MDS;"
          " source-selection inconsistencies; no original writes")

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--sites-root",type=Path,default=ROOT)
    a.add_argument("--sites",nargs="+",choices=list(SITES))
    a.add_argument("--self-test",action="store_true")
    args=a.parse_args()
    if args.self_test:
        self_test()
        return 0
    wanted=args.sites or list(SITES)
    if len(set(wanted))!=len(wanted):
        a.error("duplicate sites")
    print("STAGE08 | FULL-ROW QC 0/1 -> MDS and QC2 -> ERA source-selection audit")
    print("MDS_QC 2/3 is LOW QUALITY, never approved as a replacement")
    print("READ ONLY, NO CLOCK SHIFT, NO RH PROVENANCE INFERENCE")
    fail=[]
    for s in wanted:
        print("==========",s,"==========",flush=True)
        try:
            site(s,args.sites_root.expanduser())
        except (OSError,ValueError,KeyError,csv.Error) as exc:
            fail.append(s)
            print("SITE_STAGE08_FAILED",s,repr(exc),flush=True)
    print("STAGE08 SUMMARY audited={}/{} failed={}".format(
        len(wanted)-len(fail),len(wanted),",".join(fail) or "none"))
    print("NO WRITES; NO MDS/ERA PROMOTION; NO ORIGINAL RH ADOPTION; NO SLURM")
    return bool(fail)

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stage48 | Ten-site native FLUXNET VPD/RH triage and external-ERA repair eligibility.

This is an immutable-source, READ-ONLY policy implementation. It reviews the
exact Stage04b source_inventory.json (20 primary/companion release records)
for all ten Batch02 sites and SHA256-verifies each primary before counting.

Physically problematic:
 - water-basis VPD below -0.005 hPa (large negative; tolerance for rounding)
 - native raw RH <0 or >100%; RH exactly zero also severe
 - implied actual vapour pressure <=0 or derived water RH <0 or >101
 Extreme dryness:
 - 0 < raw RH <1%: high-priority review; NOT automatic invalid observation
 - RH 1-5% and 5-10%: lower priority, retain unless corroborated
Tiny -0.005<=VPD<0: rounding/supersaturation review, NOT evidence enough
to replace site air temperature. Inferred RH from TA/VPD is NOT independent
sensor evidence and is labelled separately.

After external CDS ERA5 or CDS ERA5-Land 2m T, 2m dewpoint, and surface
pressure have been verified at the SAME station/time, it is possible to
create a conditional humidity-only repair candidate at retained TA:
  RH_ext = es(Td_ext)/es(T_ext)
  VPD_site = es(T_site)*(1-RH_ext)
  QBOT_site = 0.622*e_site/(P_site-0.378*e_site)
This code only prints the proposal when the independent source, UTC,
elevation and station metadata are explicitly verified; it NEVER edits
TA, VPD, QBOT, CSV, NetCDF or DATM, and does not certify site truth.
If TA is QC2 or itself inconsistent (Ho1 example), require manual joint
T/humidity review. Do NOT treat FLUXNET in-package *_ERA as independent CDS.

Modes:
 --self-test : synthetic policy and psychrometric tests (no files)
 --check --inventory ... : inspect existing Stage04b 10-site snapshot
 --audit --inventory ... : independently checksum raw primary files and
                           scan all native HH/HR records; reports stdout ONLY.
 --example : print a hypothetical pair using the same validation function.

No archive extraction, outputs, overwrites, downloads, Slurm jobs or model
change. This does not override the 4,884 Stage08 science HOLD records.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

SITES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1",
       "US-Ho1","US-Ho2","US-Ho3","US-ICh","US-ICt")
SITE_STEPS={site:(60 if site=="US-Ha1" else 30) for site in SITES}
LABELS=(
 "WATER_NEG_VPD_SEVERE","WATER_NEG_VPD_TINY","RH_RAW_NEGATIVE",
 "RH_RAW_ZERO","RH_RAW_GT100","RH_RAW_LT1_POS","RH_RAW_1_TO5",
 "RH_RAW_5_TO10","RH_INFERRED_LT0","RH_INFERRED_GT101",
 "ACTUAL_VAPOR_NONPOSITIVE","HARD_PHYSICS_UNION",
 "EXTREME_DRY_REVIEW_UNION","HARD_WITH_TA_QC0",
 "HARD_WITH_VPD_QC0","RH_FIELD_MISSING_RECORDS"
)
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EPS_HPA=0.005
MIN_RH=1.0

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def number(series):
    arr=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float,na_value=np.nan)
    arr[(~np.isfinite(arr)) | (arr<=-9990)]=np.nan
    return arr

def es_water_hpa(tc):
    x=np.asarray(tc,dtype=float)
    with np.errstate(all="ignore"):
        return 6.112*np.exp(np.clip(17.67*x/(x+243.5),-45,45))

def classify(temp_c,vpd_hpa,press_kpa,rh_raw=None,ta_qc=None,vpd_qc=None):
    t=np.asarray(temp_c,dtype=float);v=np.asarray(vpd_hpa,dtype=float)
    p=np.asarray(press_kpa,dtype=float)
    if t.shape!=v.shape or v.shape!=p.shape:raise ValueError("Shape mismatch")
    n=len(t)
    r=np.full(n,np.nan) if rh_raw is None else np.asarray(rh_raw,dtype=float)
    tq=np.full(n,np.nan) if ta_qc is None else np.asarray(ta_qc,dtype=float)
    vq=np.full(n,np.nan) if vpd_qc is None else np.asarray(vpd_qc,dtype=float)
    if any(len(x)!=n for x in (r,tq,vq)):raise ValueError("QC/RH length mismatch")
    with np.errstate(all="ignore"):
        sat=es_water_hpa(t)
        vap=sat-v
        inferred=100*vap/sat
    valid=np.isfinite(t)&np.isfinite(v)&np.isfinite(p)&(p>50)&(p<110)&(t>-80)&(t<65)
    humid=valid&np.isfinite(sat)&(sat>0)
    rvalid=np.isfinite(r)
    neg=humid&(v<-EPS_HPA)
    tiny=humid&(v<0)&(v>=-EPS_HPA)
    rawnegative=rvalid&(r<0)
    rawzero=rvalid&(r==0)
    rawgt100=rvalid&(r>100)
    rawlt1=rvalid&(r>0)&(r<1)
    raw1to5=rvalid&(r>=1)&(r<5)
    raw5to10=rvalid&(r>=5)&(r<10)
    implied_lt0=humid&np.isfinite(inferred)&(inferred<0)
    implied_gt101=humid&np.isfinite(inferred)&(inferred>101)
    vap0=humid&np.isfinite(vap)&(vap<=0)
    hard=neg|rawnegative|rawzero|rawgt100|implied_lt0|implied_gt101|vap0
    dry=rawlt1
    masks=dict(zip(LABELS[:11],(neg,tiny,rawnegative,rawzero,rawgt100,
             rawlt1,raw1to5,raw5to10,implied_lt0,implied_gt101,vap0)))
    masks["HARD_PHYSICS_UNION"]=hard
    masks["EXTREME_DRY_REVIEW_UNION"]=dry
    masks["HARD_WITH_TA_QC0"]=hard&np.isfinite(tq)&(tq==0)
    masks["HARD_WITH_VPD_QC0"]=hard&np.isfinite(vq)&(vq==0)
    masks["RH_FIELD_MISSING_RECORDS"]=~rvalid
    return masks,inferred

def era_humidity_candidate(t_site_c,p_site_pa,t_era_k,td_era_k,
                           source,provenance_ok=False,utc_ok=False,
                           elevation_ok=False,ta_qc=None):
    """Propose only; output cannot be used as an authorization to write forcing."""
    allowed=("CDS_ERA5","CDS_ERA5_LAND")
    if source not in allowed:
        return dict(status="HOLD_NOT_INDEPENDENT_CDS_SOURCE")
    if not (provenance_ok and utc_ok and elevation_ok):
        return dict(status="HOLD_EXTERNAL_SOURCE_TIME_OR_HEIGHT_UNVERIFIED")
    vals=(t_site_c,p_site_pa,t_era_k,td_era_k)
    if not all(np.isfinite(x) for x in vals):
        return dict(status="HOLD_NONFINITE_MET")
    if not (190<t_era_k<340 and 190<td_era_k<340 and
            50000<p_site_pa<110000 and -80<t_site_c<65):
        return dict(status="HOLD_MET_RANGE")
    if td_era_k>t_era_k:
        return dict(status="HOLD_ERA_SUPERSAT_OR_PHASE_REVIEW")
    if ta_qc!=0 or abs(t_site_c-(t_era_k-273.15))>8:
        return dict(status="MANUAL_T_AND_HUMIDITY_JOINT_REVIEW")
    ext_rh=es_water_hpa(td_era_k-273.15)/es_water_hpa(t_era_k-273.15)
    if not (0<ext_rh<=1):return dict(status="HOLD_BAD_EXTERNAL_RH")
    sat_site=float(es_water_hpa(t_site_c))
    ea=sat_site*float(ext_rh)
    denom=p_site_pa-0.378*ea*100
    if denom<=0:return dict(status="HOLD_INVALID_SPECIFIC_HUMIDITY")
    q=0.622*ea*100/denom
    new_vpd=sat_site*(1-float(ext_rh))
    if not (np.isfinite(q) and 0<q<0.08 and np.isfinite(new_vpd) and new_vpd>=0):
        return dict(status="HOLD_RECONSTRUCTION")
    return dict(status="CONDITIONAL_ERA_HUMIDITY_CANDIDATE_ONLY",
                source=source,TA_C_unchanged=t_site_c,
                VPD_hPa_candidate=round(new_vpd,6),
                QBOT_kg_kg_candidate=round(q,10),
                RH_external_pct=round(100*float(ext_rh),5),
                source_verified=True,
                requires_original_QC_lineage_and_final_independent_review=True)

def load_inventory(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    completed=data.get("completed",[])
    failed=data.get("failures",[])
    if failed or len(completed)!=20:
        raise ValueError("Stage04b must have 20/20 completed and no failures")
    by_site={s:[] for s in SITES}
    for item in completed:
        site=item.get("site");src=item.get("source","")
        if site not in by_site or src not in ("FULLSET_HH","FULLSET_HR",
                                               "FLUXMET_HH","FLUXMET_HR",
                                               "ERA5_HH","ERA5_HR"):
            raise ValueError("Unexpected Stage04b inventory site or source")
        by_site[site].append(item)
    if any(len(group)!=2 or sum(x["source"].startswith("ERA5") for x in group)!=1
           for group in by_site.values()):
        raise ValueError("Every site must have primary and ERA5 companion entry")
    result=[]
    for site in SITES:
        spec=next(x for x in by_site[site] if not x["source"].startswith("ERA5"))
        if spec.get("interval_minutes")!=SITE_STEPS[site]:
            raise ValueError("Native site interval mismatch: "+site)
        path=Path(spec["file"])
        if not path.is_file() or path.is_symlink() or not path.name.startswith("AMF_"+site+"_"):
            raise ValueError("Original primary path invalid: "+str(path))
        if not spec.get("sha256") or len(spec["sha256"])!=64:
            raise ValueError("Original Stage04b primary SHA256 missing")
        if set(("TA","VPD","PA"))-set(spec.get("columns",{})):
            raise ValueError("Original temperature/VPD/pressure mappings missing")
        result.append(spec)
    return result

def scan_one(spec,chunksize=100000):
    path=Path(spec["file"])
    expected=spec["sha256"]
    original=sha256(path)
    if original!=expected:
        raise ValueError("Original Stage04b primary SHA changed: "+spec["site"])
    header=pd.read_csv(path,nrows=0).columns.tolist()
    cmap=spec["columns"];qcmap=spec.get("qc_columns",{})
    cols=["TIMESTAMP_START","TIMESTAMP_END",cmap["TA"],cmap["VPD"],cmap["PA"]]
    rhcolumn="RH" if "RH" in header else None
    if rhcolumn:cols.append(rhcolumn)
    for qcol in (qcmap.get("TA"),qcmap.get("VPD")):
        if qcol and qcol in header:cols.append(qcol)
    cols=list(dict.fromkeys(cols))
    counts=Counter()
    examples={}
    seen=set()
    previous=None
    for chunk in pd.read_csv(path,usecols=cols,dtype="string",chunksize=chunksize):
        raw=chunk["TIMESTAMP_START"].astype("string").str.strip().str.replace(
            r"\.0$","",regex=True)
        ends=chunk["TIMESTAMP_END"].astype("string").str.strip().str.replace(
            r"\.0$","",regex=True)
        start=pd.to_datetime(raw,format="%Y%m%d%H%M",errors="coerce")
        end=pd.to_datetime(ends,format="%Y%m%d%H%M",errors="coerce")
        if start.isna().any() or end.isna().any() or (
                (end-start).dt.total_seconds()!=SITE_STEPS[spec["site"]]*60).any():
            raise ValueError("Malformed original native timestamp interval")
        if (start.dt.year<int(spec["first_year"])).any() or (
                start.dt.year>int(spec["last_year"])).any():
            raise ValueError("Original source timestamp outside release years")
        if previous is not None and start.iloc[0]<=previous:
            raise ValueError("Source data non-monotonic across chunks")
        if (start.diff().dropna()<=pd.Timedelta(0)).any():
            raise ValueError("Non-monotonic or duplicate source times")
        previous=start.iloc[-1]
        tc=number(chunk[cmap["TA"]]);v=number(chunk[cmap["VPD"]])
        p=number(chunk[cmap["PA"]])
        rh=number(chunk[rhcolumn]) if rhcolumn else None
        tq=number(chunk[qcmap["TA"]]) if qcmap.get("TA") in chunk else None
        vq=number(chunk[qcmap["VPD"]]) if qcmap.get("VPD") in chunk else None
        flags,inferred=classify(tc,v,p,rh,tq,vq)
        # Do not add independent-evidence claims: inferred RH uses the
        # exact same TA/VPD and is recorded as derived, not observed.
        for name,mask in flags.items():
            n=int(mask.sum())
            counts[name]+=n
            if n and name not in examples:
                ix=int(np.flatnonzero(mask)[0])
                examples[name]=dict(time=str(raw.iloc[ix]),TA_C=float(tc[ix]),
                                    VPD_hPa=float(v[ix]),
                                    RH_raw_pct=None if rh is None or
                                    not np.isfinite(rh[ix]) else float(rh[ix]),
                                    RH_derived_pct=None if
                                    not np.isfinite(inferred[ix]) else
                                    round(float(inferred[ix]),4))
        counts["TOTAL_SOURCE_ROWS"]+=len(chunk)
        counts["NATIVE_NOLEAP_ROWS"]+=int(
            ((start.dt.month!=2)|(start.dt.day!=29)).sum())
    if counts["TOTAL_SOURCE_ROWS"]!=int(spec["source_records"]):
        raise ValueError("Stage04b original source row count changed")
    return counts,examples,original,rhcolumn

def test():
    ta=np.array([10,10,10,10,10,10,10],dtype=float)
    v=np.array([-1.,-0.0001,12.25,10.,12.27,0.5,1.0])
    p=np.full(7,98.)
    raw=np.array([50.,50.,-1.,0.,0.2,2.,7.])
    f,i=classify(ta,v,p,raw,np.array([0,2,0,0,0,0,0]))
    assert f["WATER_NEG_VPD_SEVERE"].tolist()==[True,False,False,False,False,False,False]
    assert f["WATER_NEG_VPD_TINY"].tolist()==[False,True,False,False,False,False,False]
    assert int(f["RH_RAW_NEGATIVE"].sum())==1
    assert int(f["RH_RAW_ZERO"].sum())==1
    assert int(f["RH_RAW_LT1_POS"].sum())==1
    assert int(f["RH_RAW_1_TO5"].sum())==1
    assert int(f["RH_RAW_5_TO10"].sum())==1
    ok=era_humidity_candidate(12.,95000.,285.15,280.15,
                              "CDS_ERA5",True,True,True,0)
    assert ok["status"]=="CONDITIONAL_ERA_HUMIDITY_CANDIDATE_ONLY"
    assert 0<ok["RH_external_pct"]<100
    assert ok["VPD_hPa_candidate"]>0 and ok["QBOT_kg_kg_candidate"]>0
    bad=era_humidity_candidate(-20.,95000.,285.15,280.15,
                               "CDS_ERA5",True,True,True,2)
    assert bad["status"]=="MANUAL_T_AND_HUMIDITY_JOINT_REVIEW"
    assert era_humidity_candidate(12.,95000.,285.15,280.15,
                  "IN_PACKAGE_TA_ERA",True,True,True,0)["status"]=="HOLD_NOT_INDEPENDENT_CDS_SOURCE"
    print("STAGE48 SELF-TEST PASS | physical RH/VPD bins, neg VPD tolerance,")
    print("external-CDS candidate psychrometrics, and Ho1 QC2 fail-closed")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    args=ap.add_mutually_exclusive_group(required=True)
    args.add_argument("--self-test",action="store_true")
    args.add_argument("--check",action="store_true")
    args.add_argument("--audit",action="store_true")
    args.add_argument("--example",action="store_true")
    ap.add_argument("--inventory",type=Path,
                    help="EXACT existing Stage04b source_inventory.json")
    ap.add_argument("--chunksize",type=int,default=100000)
    opt=ap.parse_args()
    if opt.self_test:
        test();return
    if opt.example:
        print("HYPOTHETICAL ONLY, NOT A SITE DATA REPAIR:")
        print(era_humidity_candidate(12.,95000.,285.15,280.15,
              "CDS_ERA5",True,True,True,0));return
    if opt.inventory is None:
        ap.error("--inventory required for --check / --audit")
    if opt.chunksize<1000:
        ap.error("--chunksize must be >=1000")
    specs=load_inventory(opt.inventory)
    print("STAGE48 TEN-SITE ORIGINAL STAGE04B INVENTORY",opt.inventory)
    print("All original primary paths: exact source and 10 unique HH/HR sites.")
    print("NO FORCING APPROVED. In-package FLUXNET ERA is NOT independent CDS ERA5.")
    if opt.check:
        for spec in specs:
            print("READY",spec["site"],spec["source"],"step",
                  SITE_STEPS[spec["site"]],"SHA256 LEDGER",spec["sha256"])
        print("STAGE48 CHECK PASS | inventory only; original file data not scanned")
        return
    total=Counter()
    for spec in specs:
        counts,examples,sha,rhname=scan_one(spec,opt.chunksize)
        total.update(counts)
        print("\nSITE",spec["site"],"NATIVE_MIN",SITE_STEPS[spec["site"]],
              "SOURCE_SHA256",sha,"RH_COLUMN",rhname or "ABSENT")
        print("SCREENS:",{key:counts[key] for key in LABELS})
        print("EVENT EXAMPLES:",examples)
        print("SCIENCE CLASS: mandatory review; no candidate forcing emitted")
    print("\nSTAGE48 TEN-SITE TOTAL RAW PRIMARY SOURCE PHYSICAL SCREEN")
    print({key:total[key] for key in LABELS})
    print("SOURCE ROW TOTAL",total["TOTAL_SOURCE_ROWS"],
          "NOLEAP ROW TOTAL",total["NATIVE_NOLEAP_ROWS"])
    print("Counts are STAGE48 ORIGINAL RAW-PRIMARY SCREENS, NOT the")
    print("4,884 Stage08 HOLD cohort and not actual approved ERA repairs.")
    print("Duplicate conditions and different variables can overlap.")
    print("For conditional ERA5/ERA5-L humidity-only repair, confirmed UTC,")
    print("independent external T2m/Td2m/PSRF, original QC and height are required.")
    print("RH <1% POSITIVE = MANUAL EXTREME DRY, not unconditional replacement.")
    print("If source TA is QC2 or doubtful, require a separately reviewed")
    print("joint T and humidity replacement; never silently preserve bad Ho1 TA.")
    print("All Stage08 4,884 science HOLD; approved repairs=0.")
    print("READ ONLY: NO files/NetCDF/DATM/CIME/Slurm outputs or changes.")

if __name__=="__main__":
    main()

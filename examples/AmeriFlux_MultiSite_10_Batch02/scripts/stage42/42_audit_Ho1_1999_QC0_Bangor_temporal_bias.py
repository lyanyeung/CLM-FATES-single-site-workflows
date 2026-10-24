#!/usr/bin/env python3
"""Stage42 | US-Ho1 1999 measured-QC0 / Bangor temporal alignment audit.

Study ONLY the immutable 3,005 original Ho1 TA_F_QC=0 temperatures from
Oct-Dec 1999, together with the 25 February 1999 QC2 failure timestamps.

- Report measured-QC0 Bangor-source-QC temperature bias/error at hypothetical
  local-minus-UTC offsets -7,-6,-5,-4,-3 hours; compare errors on a STRICT
  common-support set rather than comparing different matches.
- Decompose NOMINAL UTC-5 October/November/December controls, local clock-hour
  groups, unique NOAA reports and uninterrupted large-error sequences.
- For the 25 February failure timestamps, compare Ho1 QC2 vs Bangor across
  offsets (do NOT compare an off-nominal Bangor time to fixed-UTC CDS ERA5).
- NOAA data are read into memory and pinned to prior source hash; no output
  files. Full prior Stage08/19/20/21 and 319-event evidence gates reused.

A reduced error at a trial offset is NOT official UTC_OFFSET certification.
Seasonally unmatched autumn QC0 controls CANNOT prove February site-airport
equivalence. No forcing, NetCDF, DATM, CIME, SLURM, scientific approvals.
"""
import argparse
from bisect import bisect_left
from collections import Counter
from datetime import timedelta
import hashlib
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

BLOBS={
    "39_probe_NOAA_GHCNh_Bangor_history.py":"849d22af0f32ac4e54f10b834cb77a710da1d98f",
    "40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py":"8767dbcad2c3c6cd431b37968e867838eac01d87",
    "41_audit_NOAA_event_dependence_Ho1_QC0_calibration.py":"be41d1c6f21d83f95820bc02ffc804bcc24a0f3a",
}
OFFSETS=(-7,-6,-5,-4,-3)
STATION_YEAR=1999
CONTROL_COUNT=3005
CONTROL_MONTHS={10:77,11:1440,12:1488}
EXPECTED_NOMINAL_MATCHES=2986
EXPECTED_NOMINAL_UNIQUE=1498
EXPECTED_NOMINAL_MAE=5.024
FEB_EVENTS=25

def git_blob(path):
    blob=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

def load_verified_stages():
    here=Path(__file__).resolve().parent
    mods=[]
    for i,(name,want) in enumerate(BLOBS.items()):
        path=here/name
        if not path.is_file():raise FileNotFoundError("Pinned prerequisite missing: "+str(path))
        actual=git_blob(path)
        if actual!=want:raise ValueError(name+" Git blob changed: "+actual+" expected "+want)
        spec=importlib.util.spec_from_file_location("stage42_parent_"+str(i),path)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot load pinned parent "+name)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        mods.append(module)
        print("PREREQUISITE VERIFIED",name,actual,flush=True)
    m,p,s41=mods
    if m.STATION!="USW00014606" or p.STATION!=m.STATION or \
       m.YEARS!={1998:64,1999:25,2001:230}:
        raise ValueError("Original NOAA station/study scope changed")
    return m,p,s41

def fast_select(rows,times,target):
    """Identical to Stage40 select(), using precomputed times; no interpolation."""
    lo=target-timedelta(minutes=30)
    i=bisect_left(times,lo)
    available=[]
    for rec in rows[i:]:
        dt=(rec[0]-target).total_seconds()/60.
        if dt>30:break
        if abs(dt)<=30:available.append((abs(dt),rec))
    if not available:return "NO_NUMERIC_30MIN",None
    qc=[(d,r) for d,r in available if r[6]]
    if not qc:return "NO_SOURCE_QC_PASS_30MIN",None
    mind=min(d for d,_ in qc)
    tied=[r for d,r in qc if abs(d-mind)<1e-8]
    if max(r[1] for r in tied)-min(r[1] for r in tied)>.001:
        return "CONFLICTING_EQUIDISTANT_REPORTS",None
    return "PROVISIONAL_SOURCE_QC",tied[0]

def build_match(raw,rows,times,offset):
    out=[]
    for rec in raw.itertuples(index=False):
        nominal=rec.local.to_pydatetime()-timedelta(hours=offset)
        status,noaa=fast_select(rows,times,nominal)
        out.append(dict(local=rec.local,
                        offset=offset,
                        matched=status=="PROVISIONAL_SOURCE_QC",
                        status=status,
                        noaa_utc=noaa[0] if noaa is not None else pd.NaT,
                        noaa_t=noaa[1] if noaa is not None else np.nan,
                        noaa_source=noaa[2] if noaa is not None else None,
                        noaa_qc=noaa[3] if noaa is not None else None,
                        ho1_t=float(rec.TA_F),
                        hour_local=int(rec.local.hour)))
    frame=pd.DataFrame(out)
    if frame.local.duplicated().any() or len(frame)!=len(raw):
        raise ValueError("Timestamp pairing lost original row identities")
    return frame

def report_error(frame,title):
    pair=frame.loc[frame.matched].copy()
    if pair.empty:
        print(title,"NO SOURCE-QC-SCREENED REPORTS")
        return
    delta=pair.noaa_t-pair.ho1_t
    unique=pair[["noaa_utc","noaa_source"]].drop_duplicates().shape[0]
    print(title,"n_targets",len(pair),"distinct_NOAA",unique,
          "Bangor_minus_Ho1_mean_C",round(float(delta.mean()),3),
          "median_C",round(float(delta.median()),3),
          "MAE_C",round(float(delta.abs().mean()),3),
          "P95_abs_C",round(float(delta.abs().quantile(.95)),3),
          "abs_error_gt5C",int(delta.abs().gt(5).sum()),
          "abs_error_gt10C",int(delta.abs().gt(10).sum()))
    return pair

def contiguous_outliers(frame,cutoff=10):
    z=frame.loc[frame.matched &
                (frame.noaa_t-frame.ho1_t).abs().gt(cutoff)].sort_values("local").copy()
    if z.empty:return pd.DataFrame()
    z["block"]=z.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    z["difference"]=z.noaa_t-z.ho1_t
    return z.groupby("block").agg(first=("local","min"),last=("local","max"),
                                    n=("local","size"),
                                    median_delta_C=("difference","median"),
                                    max_abs_delta_C=("difference",lambda x:float(x.abs().max()))
                                  ).sort_values("n",ascending=False).head(12)

def measured_control(m,p,stage41):
    target,ctrl=stage41.check_gate(m)
    if len(ctrl)!=CONTROL_COUNT or \
       ctrl.local.dt.month.value_counts().sort_index().to_dict()!=CONTROL_MONTHS:
        raise ValueError("Historical Stage41 Ho1 measured-QC0 control changed")
    feb=target.loc[target.local.dt.year.eq(1999),["local","utc_candidate"]].copy()
    if len(feb)!=FEB_EVENTS:raise ValueError("Historical 1999 February target count differs")
    full=pd.read_csv(m.S20/"all_4884_phase_transfer_QC_sensitivity.csv",
                     usecols=["site","local","retained_TA_C"],parse_dates=["local"])
    full=full.loc[full.site.eq("US-Ho1"),["local","retained_TA_C"]]
    feb=feb.merge(full,on="local",how="left",validate="one_to_one",indicator=True)
    if not feb._merge.eq("both").all() or not np.isfinite(feb.retained_TA_C).all():
        raise ValueError("Stage20 1999 February Ho1 QC2 source join differs")
    feb=feb[["local","retained_TA_C"]].rename(columns={"retained_TA_C":"TA_F"})
    return ctrl[["local","TA_F"]],feb

def run_audit(m,p,ctrl,feb):
    rows,_,invalid,total=p.fetch_year(m,STATION_YEAR)
    times=[r[0] for r in rows]
    # Assert accelerated nearest-neighbour selection has the original
    # Stage40 behavior, including ambiguous ties and QC exclusions.
    tests=[ctrl.local.iloc[0],ctrl.local.iloc[100],ctrl.local.iloc[-1],
           feb.local.iloc[0],feb.local.iloc[-1]]
    for stamp in tests:
        for off in OFFSETS:
            request=stamp.to_pydatetime()-timedelta(hours=off)
            orig=p.select(rows,request)
            fast=fast_select(rows,times,request)
            if orig!=fast:raise ValueError("Optimized matching differs from Stage40 selection")
    table={offset:build_match(ctrl,rows,times,offset) for offset in OFFSETS}
    base=table[-5]
    if int(base.matched.sum())!=EXPECTED_NOMINAL_MATCHES:
        raise ValueError("Stage41 nominal 1999 QC0 paired count changed")
    distinct=base.loc[base.matched,["noaa_utc","noaa_source"]].drop_duplicates()
    if len(distinct)!=EXPECTED_NOMINAL_UNIQUE or \
       abs(float((base.loc[base.matched,"noaa_t"]-
                  base.loc[base.matched,"ho1_t"]).abs().mean())-
           EXPECTED_NOMINAL_MAE)>.006:
        raise ValueError("Stage41 1999 measured-QC0 baseline MAE/uniques differs")

    print("\n"+"="*110)
    print("STAGE42 | Ho1 ORIGINAL 1999 QC0 CONTROL / Bangor OFFSET AND BIAS SENSITIVITY")
    print("Original Ho1 QC0=3,005 (Oct-Dec only); NOAA PSV exact Stage39 SHA256")
    print("NO source repair, no official UTC_OFFSET certification")
    print("="*110)
    print("\nALL OFFSETS, UNRESTRICTED MATCHED RECORDS (different sample sizes):")
    allstats=[]
    for off,t in table.items():
        f=t.loc[t.matched]
        delta=f.noaa_t-f.ho1_t
        allstats.append(dict(offset_local_minus_UTC=off,pairs=len(f),
            unique_NOAA=f[["noaa_utc","noaa_source"]].drop_duplicates().shape[0],
            bias=round(float(delta.mean()),3) if len(f) else np.nan,
            median=round(float(delta.median()),3) if len(f) else np.nan,
            mae=round(float(delta.abs().mean()),3) if len(f) else np.nan))
    print(pd.DataFrame(allstats).to_string(index=False))

    # Pairwise comparisons must use exactly the SAME tower timestamps.
    common=set(ctrl.local)
    for t in table.values():
        common.intersection_update(t.loc[t.matched,"local"])
    print("\nCOMMON-SUPPORT, ALL FIVE OFFSETS QC PASS: records",len(common))
    if len(common)<2500:
        raise ValueError("Insufficient common-support 1999 observed-QC0 controls; hold inference")
    commonstats=[]
    for off,t in table.items():
        q=t.loc[t.local.isin(common)].copy()
        if len(q)!=len(common) or not q.matched.all():
            raise ValueError("Common-support pairing incomplete")
        d=q.noaa_t-q.ho1_t
        commonstats.append(dict(offset=off,n=len(q),
            unique_NOAA=q[["noaa_utc","noaa_source"]].drop_duplicates().shape[0],
            mean_bias_C=round(float(d.mean()),3),
            median_bias_C=round(float(d.median()),3),
            mae_C=round(float(d.abs().mean()),3),
            p95_abs_C=round(float(d.abs().quantile(.95)),3)))
    print(pd.DataFrame(commonstats).to_string(index=False))
    print("Lowest observed common-support MAE is NOT BADM UTC_OFFSET proof.")

    print("\nNOMINAL UTC-5 BY MONTH (QC0 SOURCE OBSERVATIONS):")
    for month,q in base.groupby(base.local.dt.month):
        report_error(q,"MONTH "+str(month))
    print("\nNOMINAL UTC-5 LOCAL CLOCK HOUR: night 00-05, daytime 06-17, evening 18-23")
    for label,test in [
        ("NIGHT_00_05",base.hour_local.lt(6)),
        ("CLOCK_06_17",base.hour_local.ge(6)&base.hour_local.lt(18)),
        ("EVENING_18_23",base.hour_local.ge(18))]:
        report_error(base.loc[test],label)
    print("\nNOMINAL UTC-5 long runs with |Bangor-Ho1| >10C:")
    spells=contiguous_outliers(base)
    print(spells.to_string(index=False) if len(spells) else "None")
    if len(spells):
        print("CAUTION: long runs may reflect fronts, microclimate, QC provenance or clock issues.")

    print("\nFEB 1999 FAILURE EPISODES, OFFSET SENSITIVITY: NOAA vs original Ho1 QC2 ONLY")
    for off in OFFSETS:
        z=build_match(feb,rows,times,off)
        if off==-5 and int(z.matched.sum())!=25:
            raise ValueError("Stage40 February 1999 QC-screened source count changed")
        report_error(z,"FEB_FAILURE_OFFSET "+str(off))
    print("NO cross-offset comparison against Stage20 CDS T: its UTC mapping was nominal -5.")
    print("\nInterpretation: a period of poor Bangor-vs-QC0 agreement in late 1999")
    print("does not prove the actual forest air temperature for February 1999,")
    print("nor distinguish sensor representativeness, time metadata and tower QC.")
    print("All Ho1 319 missing-neighbour-QC0 events and 4,884 Batch02 remain HOLD.")
    print("NO DATA WRITES / NO NETCDF, FORCING, DATM, CIME OR SLURM CHANGES.")

def selftest():
    # Check optimized selection vs Stage40's exact logic on synthetic tuples.
    from datetime import datetime
    t0=datetime(1999,2,13,4,0)
    t1=datetime(1999,2,13,5,0)
    ok=(t0,8.0,"223","1","ICAO-KBGR","",True)
    other=(t1,9.0,"223","1","ICAO-KBGR","",True)
    rows=[ok,other]
    times=[r[0] for r in rows]
    assert fast_select(rows,times,t0)==("PROVISIONAL_SOURCE_QC",ok)
    assert fast_select(rows,times,t0+timedelta(minutes=30))[0]=="CONFLICTING_EQUIDISTANT_REPORTS"
    unknown=(t0,6.0,"335","1","726088-14606","",False)
    assert fast_select([unknown],[t0],t0)[0]=="NO_SOURCE_QC_PASS_30MIN"
    sample=pd.DataFrame({"local":pd.to_datetime([
        "1999-10-01 00:00","1999-10-01 00:30","1999-10-01 05:00"
    ]),"TA_F":[1.,2.,3.]})
    for off in OFFSETS:
        check=sample.local.iloc[0].to_pydatetime()-timedelta(hours=off)
        assert (check-sample.local.iloc[0].to_pydatetime()).total_seconds()/3600==-off
    print("STAGE42 SELF-TEST PASS | source-QC filtering, exact-time tie, UTC offset algebra")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true",help="Reads one pinned NOAA PSV into RAM")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        return
    m,p,s41=load_verified_stages()
    control,feb=measured_control(m,p,s41)
    print("STAGE42 PREFLIGHT PASS: Ho1 1999 QC0=3005, February failures=25,",
          "all 319 Stage39/41 source and target SHA gates satisfied")
    if args.check:
        print("CHECK ONLY. NOAA not contacted. No files/model changes.")
        return
    run_audit(m,p,control,feb)

if __name__=="__main__":
    main()

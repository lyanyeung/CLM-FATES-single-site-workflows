#!/usr/bin/env python3
"""AmeriFlux Batch 01 Stage17: complete, read-only pre-repair gate for 10 sites.

Reuse evidence-driven ideas from ICOS FLUXNET_MultiSite_6/8/11/13:
  1. The official FLUXMET_HH *_F meteorology is *already* merged/gapfilled
     upstream (QC0 measured, QC1 MDS good fill, QC2 downscaled reanalysis).
     DO NOT mislabel this as a user's newly run short interpolation.
  2. Independent ERA5-Land coverage, units and clocks are NOT automatically
     established by the presence of official ERA5_HH in the FLUXNET ZIP.
  3. Audit ALL seven drivers, source QC counts and QC-run lengths; resolve
     TA/VPD/PA physically as a set, monitor low positive RH, time jumps,
     source seams and the moisture variables used by CLM-FATES.
  4. Screening against official ERA5_HH at the original site temperature is
     a *provisional* scenario, NOT an independent validated repair.
  5. Fail closed, do not silently edit QC0 or cap real arid-site RH.

READ-ONLY source and surface files: ONLY timestamped diagnostics under reports.
No DATM, independent meteorology downloads, forcing CSV, model or Slurm writes.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_SITES=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
MANIFEST=Path(__file__).resolve().parents[2]/"sites.tsv"
VARS=("TA","VPD","PA","SW_IN","LW_IN","WS","P")
RANGES={"TA":(-80,65),"VPD":(-0.1,125),"PA":(50,110),
        "SW_IN":(-5,1600),"LW_IN":(60,800),"WS":(-0.1,75),"P":(-.001,300)}
CORE=("TA","VPD","PA")
QC_LABELS={0:"MEASURED",1:"MDS_GAPFILL",2:"DOWNSCALED_REANALYSIS"}


def manifest():
    with MANIFEST.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=10 or len({r["site"] for r in rows})!=10:
        raise RuntimeError("Expected exactly 10 distinct pinned release sites")
    return rows


def exact_csv(folder,token):
    found=sorted(f for f in folder.glob("*.csv") if token in f.name.upper())
    if len(found)!=1:
        raise RuntimeError("Expected exactly one "+token+" CSV in "+str(folder))
    return found[0]


def header(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return next(csv.reader(f))


def load_met(path,variables):
    d=pd.read_csv(path,usecols=variables,
                  dtype={"TIMESTAMP_START":"string"},low_memory=False)
    stamp=d["TIMESTAMP_START"].str.strip().str.replace(r"\.0$","",regex=True)
    ts=pd.to_datetime(stamp,format="%Y%m%d%H%M",errors="raise")
    d.drop(columns=["TIMESTAMP_START"],inplace=True)
    for col in d.columns:
        v=pd.to_numeric(d[col],errors="coerce")
        d[col]=v.where(np.isfinite(v)&(v>-9990))
    d.insert(0,"time",ts)
    return d


def noleap_check(d,start,end,kind):
    d=d.loc[d.time.dt.year.between(start,end)]
    d=d.loc[~((d.time.dt.month==2)&(d.time.dt.day==29))].reset_index(drop=True)
    expected=pd.date_range(f"{start}-01-01",
                           f"{end+1}-01-01",freq="30min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(d)!=len(expected) or not np.array_equal(d.time.to_numpy(),expected.to_numpy()):
        raise RuntimeError(kind+" differs from full NO_LEAP half-hour timeline")
    return d


def numeric(a):
    return a.to_numpy(dtype=float)


def sat_hpa(ta):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-40,40))


def source_run_stats(qc,code):
    x=(qc==code)
    if not np.any(x):
        return 0,0,0
    starts=np.flatnonzero(x & ~np.r_[False,x[:-1]])
    ends=np.flatnonzero(x & ~np.r_[x[1:],False])
    lengths=ends-starts+1
    return int(x.sum()),int(len(lengths)),int(lengths.max())


def stage15_summary(reports):
    folders=sorted(p for p in reports.glob("stage15_fullcycle_10sites_*")
                   if (p/"site_science_gate_summary.csv").is_file())
    if not folders:raise RuntimeError("Stage15 full-cycle review missing")
    with (folders[-1]/"site_science_gate_summary.csv").open(newline="") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=10:raise RuntimeError("Stage15 report not 10 sites")
    return folders[-1],{r["site"]:r for r in rows}


def era_land_local(site,root):
    if root is None:return "NOT_SPECIFIED_NOT_VERIFIED"
    folder=root/site
    if not folder.is_dir():return "NO_SITE_DIRECTORY"
    available=[]
    # This is ONLY a presence inventory; no assertion of independent meteorology.
    for pattern in ("*.nc","*.csv","*.parquet","*.zarr"):
        available.extend(folder.glob(pattern))
    return "FILES_PRESENT_UNVERIFIED:"+str(len(available)) if available else "NO_TOP_LEVEL_DATA_FILES"


def calc_repair(ta,vpd,pa,era_t,era_v,era_pa,qc,ta_step,pa_step,prev_v,next_v):
    if not (np.isfinite(ta) and np.isfinite(vpd) and np.isfinite(pa)
            and np.isfinite(era_t) and np.isfinite(era_v)
            and np.isfinite(era_pa)):
        return "HOLD_CORE_MISSING",np.nan,np.nan,np.nan
    if not (RANGES["TA"][0]<=ta<=RANGES["TA"][1] and
            RANGES["PA"][0]<=pa<=RANGES["PA"][1] and
            RANGES["TA"][0]<=era_t<=RANGES["TA"][1] and
            RANGES["PA"][0]<=era_pa<=RANGES["PA"][1]):
        return "HOLD_TA_PA_RANGE",np.nan,np.nan,np.nan
    es=float(sat_hpa(np.array([era_t]))[0])
    era_rh=100*(es-era_v)/es
    if not (0<=era_v<=RANGES["VPD"][1] and 5<=era_rh<=100):
        return "HOLD_ERA_SOURCE_RH_INVALID_OR_TOO_LOW",np.nan,era_rh,np.nan
    if not (qc in (0,1,2)):
        return "HOLD_UNKNOWN_VPD_QC",np.nan,era_rh,np.nan
    if qc==0:
        return "HOLD_QC0_MEASURED",np.nan,era_rh,np.nan
    if abs(ta-era_t)>8:
        return "HOLD_TA_ERA_DISAGREEMENT_GT8C",np.nan,era_rh,np.nan
    if abs(pa-era_pa)>15:
        return "HOLD_PA_ERA_DISAGREEMENT_GT15KPA",np.nan,era_rh,np.nan
    if ta_step or pa_step:
        return "HOLD_TA_PA_ABRUPT_CHANGE",np.nan,era_rh,np.nan
    candidate=float(sat_hpa(np.array([ta]))[0])*(1-era_rh/100)
    if not (np.isfinite(candidate) and candidate>=0):
        return "HOLD_RECONSTRUCTION_UNPHYSICAL",np.nan,era_rh,np.nan
    jumps=[abs(candidate-n) for n in (prev_v,next_v) if np.isfinite(n)]
    large=(len(jumps)>0 and max(jumps)>5)
    if large:
        return "REVIEW_CANDIDATE_NEIGHBOUR_JUMP_GT5HPA",candidate,era_rh,max(jumps)
    # For QC2 the substitute is still from related reanalysis, not independent.
    if qc==2:
        return "QC2_ERA_RH_PROPOSAL_NEEDS_INDEPENDENT_EVIDENCE",candidate,era_rh,max(jumps,default=np.nan)
    return "QC1_ERA_RH_PROPOSAL_NEEDS_INDEPENDENT_EVIDENCE",candidate,era_rh,max(jumps,default=np.nan)


def audit_one(site,flux,era,met_cols,era_cols,args):
    first,last=int(site["first_year"]),int(site["last_year"])
    m=noleap_check(load_met(flux,met_cols),first,last,"FLUXMET "+site["site"])
    e=noleap_check(load_met(era,era_cols),first,last,"ERA5 "+site["site"])
    if not np.array_equal(m.time.to_numpy(),e.time.to_numpy()):
        raise RuntimeError(site["site"]+": timestamps differ between FLUXMET and ERA5")
    ta=numeric(m["TA_F"]);vpd=numeric(m["VPD_F"]);pa=numeric(m["PA_F"])
    era_t=numeric(e["TA_ERA"]);era_v=numeric(e["VPD_ERA"]);era_pa=numeric(e["PA_ERA"])
    es=sat_hpa(ta);ea=es-vpd;rh=100*ea/es
    good=np.isfinite(ta)&np.isfinite(vpd)&np.isfinite(pa)
    negative=good&(ea<=0)
    low=good&(ea>0)&(rh<10)
    ta_step=np.r_[False,np.abs(np.diff(ta))>8] | np.r_[np.abs(np.diff(ta))>8,False]
    pa_step=np.r_[False,np.abs(np.diff(pa))>5] | np.r_[np.abs(np.diff(pa))>5,False]
    records=[]
    counts=Counter()
    provenance=[]
    met_qc={}
    for var in VARS:
        x=numeric(m[var+"_F"])
        qc_arr=numeric(m[var+"_F_QC"]) if var+"_F_QC" in m else np.full(len(m),np.nan)
        met_qc[var]=qc_arr
        for code in (0,1,2):
            n,runs,longest=source_run_stats(qc_arr,code)
            provenance.append(dict(site=site["site"],variable=var,QC=code,
                      meaning=QC_LABELS[code],records=n,runs=runs,
                      max_run_halfhours=longest,
                      max_run_hours=longest*.5))
        provenance.append(dict(site=site["site"],variable=var,QC="MISSING",
                   meaning="MISSING_OR_NONFINITE",
                   records=int(np.count_nonzero(~np.isfinite(x))),
                   runs="",max_run_halfhours="",max_run_hours=""))
        counts[var+"_missing"]=int((~np.isfinite(x)).sum())
        lo,hi=RANGES[var]
        counts[var+"_range"]=int((np.isfinite(x)&((x<lo)|(x>hi))).sum())
    qc_vpd=met_qc["VPD"]
    counts["all_rh_nonpositive"]=int(negative.sum())
    counts["low_positive_rh_lt10"]=int(low.sum())
    counts["low_positive_qc0"]=int((low&(qc_vpd==0)).sum())
    counts["low_positive_qc1"]=int((low&(qc_vpd==1)).sum())
    counts["low_positive_qc2"]=int((low&(qc_vpd==2)).sum())
    counts["ta_30min_gt8"]=int((np.abs(np.diff(ta))>8).sum())
    counts["ta_era_difference_gt15"]=int((np.abs(ta-era_t)>15).sum())
    counts["pa_30min_gt5"]=int((np.abs(np.diff(pa))>5).sum())
    years=m.time.dt.year.to_numpy()
    for i in np.flatnonzero(negative):
        prior=vpd[i-1] if i>0 else np.nan
        after=vpd[i+1] if i+1<len(m) else np.nan
        status,new,rh_era,jump=calc_repair(
            ta[i],vpd[i],pa[i],era_t[i],era_v[i],era_pa[i],
            qc_vpd[i],bool(ta_step[i]),bool(pa_step[i]),prior,after)
        counts[status]+=1
        records.append(dict(
            site=site["site"],timestamp_local=m.time.iat[i].strftime("%Y-%m-%d %H:%M"),
            year=int(years[i]),issue="EA_NONPOSITIVE",original_RH_pct=float(rh[i]),
            original_TA_C=float(ta[i]),original_VPD_hPa=float(vpd[i]),
            original_PA_kPa=float(pa[i]),VPD_F_QC=qc_vpd[i],
            ERA_TA_C=era_t[i],ERA_VPD_hPa=era_v[i],
            ERA_PA_kPa=era_pa[i],ERA_RH_pct=rh_era,
            hypothetical_VPD_hPa=new,step_or_source_context_warning=bool(ta_step[i] or pa_step[i]),
            proposed_max_neighbour_jump_hPa=jump,
            category=status,decision="NOT_APPROVED_NOT_APPLIED"))
    status=dict(site=site["site"],start=first,end=last,rows=len(m),
                independent_ERA5_Land=era_land_local(site["site"],args.era5_land_root),
                confirmed_self_short_gap_interpolation="NOT_RUN",
                confirmed_self_long_gap_ERA5_fill="NOT_RUN",
                source_official_F_gapfilled="YES",final_forcing="NOT_CREATED",
                science_gate="HOLD")
    status.update(counts)
    return status,records,provenance


def output_csv(path,items,cols=None):
    if cols is None:
        cols=list(dict.fromkeys(k for row in items for k in row))
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        w.writeheader()
        w.writerows(items)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites-root",type=Path,default=DEFAULT_SITES)
    ap.add_argument("--report-root",type=Path,default=DEFAULT_REPORTS)
    ap.add_argument("--era5-land-root",type=Path,
                    help="Optional per-site folder ROOT/SITE containing ERA5-Land files; presence only")
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true",
                       help="Paths/headers and prior reports only; no new files")
    group.add_argument("--audit",action="store_true",
                       help="Scan sources; output versioned QC reports only")
    args=ap.parse_args()
    entries=manifest()
    report,stage15=stage15_summary(args.report_root)
    files=[]
    for site in entries:
        name=site["site"]
        if name not in stage15:
            raise RuntimeError("Stage15 did not include "+name)
        raw=args.sites_root/name/"forcing"/"raw"/site["package"]
        flux=exact_csv(raw,"FLUXMET_HH")
        era=exact_csv(raw,"ERA5_HH")
        flux_header=header(flux)
        era_header=header(era)
        need_flux=["TIMESTAMP_START"]+[v+"_F" for v in VARS]
        if not set(need_flux).issubset(flux_header):
            raise RuntimeError(name+": missing source columns "+
                               str(set(need_flux)-set(flux_header)))
        need_era=["TIMESTAMP_START","TA_ERA","VPD_ERA","PA_ERA"]
        if not set(need_era).issubset(era_header):
            raise RuntimeError(name+": missing ERA reference columns "+
                               str(set(need_era)-set(era_header)))
        qc=[v+"_F_QC" for v in VARS if v+"_F_QC" in flux_header]
        met_cols=need_flux+qc
        files.append((site,flux,era,met_cols,need_era))
        print("CHECK OK %-7s FLUXMET_QC=%d/7 ERA5_land=%s"%
              (name,len(qc),era_land_local(name,args.era5_land_root)),flush=True)
    print("STAGE17 PREFLIGHT: %d/10 releases; Stage15 report=%s"%
          (len(files),report),flush=True)
    if args.check:
        print("READ ONLY CHECK. Official *_F data already gapfilled, no separate short/long fill verified.")
        print("ERA5_HH != independently validated ERA5-Land; no scientific repairs applied.")
        return
    all_status=[];all_anomalies=[];all_provenance=[]
    for site,flux,era,met_cols,era_cols in files:
        print("AUDIT:",site["site"],flush=True)
        status,anomalies,provenance=audit_one(site,flux,era,met_cols,era_cols,args)
        expected=int(float(stage15[site["site"]]["negative_or_zero_EA"]))
        if status["all_rh_nonpositive"]!=expected:
            raise RuntimeError(site["site"]+": Stage15 EA<=0 count mismatch: Stage17 %d != %d"%
                               (status["all_rh_nonpositive"],expected))
        all_status.append(status)
        all_anomalies.extend(anomalies)
        all_provenance.extend(provenance)
        print("  EA<=0=%d low_positive_RH=%d QC0_positive_low=%d"
              " TA_jump_gt8=%d TA_vs_ERA_gt15=%d"%
              (status["all_rh_nonpositive"],status["low_positive_rh_lt10"],
               status["low_positive_qc0"],status["ta_30min_gt8"],
               status["ta_era_difference_gt15"]),flush=True)
    time=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage17_all_gaps_repairs_"+time)
    out.mkdir(parents=True,exist_ok=False)
    output_csv(out/"ten_site_pre_repair_gate.csv",all_status)
    output_csv(out/"official_F_QC_provenance_and_runs.csv",all_provenance)
    output_csv(out/"nonphysical_humidity_repair_screen_NOT_APPLIED.csv",
               all_anomalies)
    summary=Counter(row["category"] for row in all_anomalies)
    print("\nSTAGE17 SUMMARY: 10/10 sites; EA<=0=%d; provisional screen rows=%d"%
          (sum(x["all_rh_nonpositive"] for x in all_status),len(all_anomalies)),
          flush=True)
    print("Humidity issue categories (NEVER automatically applied):")
    for key,val in summary.most_common():
        print("  %-54s %d"%(key,val),flush=True)
    for s in all_status:
        print("  %-7s bad_RH=%4d low_pos_RH=%5d QC0_low=%5d TA_step_gt8=%4d"%
              (s["site"],s["all_rh_nonpositive"],s["low_positive_rh_lt10"],
               s["low_positive_qc0"],s["ta_30min_gt8"]),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("NO independent ERA5-Land validation unless separately checked.")
    print("NO source changes. NO interpolated, gapfilled, candidate or DATM forcing saved.")


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Read-only Stage19: investigate US-Bar's three QC-v5 humidity blockers.

Compares the EXACT original pinned FLUXMET_HH and ERA5_HH, native QC and
surrounding records. Screens short-gap interpolation and ERA-derived-RH
sensitivity for the specific 2004-01-14 08:00–09:00 local-timestamp block;
neither is applied. Ice-saturation RH is reported for context only.

ALL 9 successful Stage18 QC-v5 sites and its incomplete marker are untouched.
NO raw data, forcing, DATM, surface, CIME, or Slurm files are modified.
"""
import argparse
import csv
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SITE = "US-Bar"
TARGET = ("2004-01-14 08:00", "2004-01-14 08:30", "2004-01-14 09:00")
SITE_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
HERE = Path(__file__).resolve().parents[2]
MET = ("TA","VPD","PA","SW_IN","LW_IN","WS","P")


def num(value):
    try:
        out=float(value)
    except (TypeError,ValueError):
        return None
    return out if math.isfinite(out) and out>-9990 else None


def check_file(folder,kind):
    matches=sorted(f for f in folder.glob("*.csv") if kind in f.name.upper())
    if len(matches)!=1:
        raise RuntimeError("Expected 1 exact-release %s, found %d in %s" %
                           (kind,len(matches),folder))
    return matches[0]


def get_sources(root):
    with (HERE/"sites.tsv").open(newline="",encoding="utf-8") as f:
        manifest=list(csv.DictReader(f,delimiter="\t"))
    entry=next((x for x in manifest if x["site"]==SITE),None)
    if entry is None or len(manifest)!=10:
        raise RuntimeError("Expected 10-site pinned manifest including "+SITE)
    folder=root/SITE/"forcing"/"raw"/entry["package"]
    return check_file(folder,"FLUXMET_HH"),check_file(folder,"ERA5_HH")


def df_for_site(path,suffix):
    header=pd.read_csv(path,nrows=0).columns.tolist()
    required=["TIMESTAMP_START"]+[x+suffix for x in MET]
    missing=[x for x in required if x not in header]
    if missing:
        raise RuntimeError("Columns absent from "+str(path)+": "+str(missing))
    qcs=[v+suffix+"_QC" for v in MET if v+suffix+"_QC" in header]
    d=pd.read_csv(path,usecols=required+qcs,
                  dtype={"TIMESTAMP_START":"string"},low_memory=False)
    time=pd.to_datetime(
        d["TIMESTAMP_START"].str.strip().str.replace(r"\.0$","",regex=True),
        format="%Y%m%d%H%M",errors="raise")
    d.drop(columns="TIMESTAMP_START",inplace=True)
    d.insert(0,"time",time)
    d=d.loc[d.time.dt.year.between(2004,2023)]
    d=d.loc[~((d.time.dt.month==2)&(d.time.dt.day==29))].copy()
    d.reset_index(drop=True,inplace=True)
    if d.time.duplicated().any() or not d.time.is_monotonic_increasing:
        raise RuntimeError("Source timestamps duplicate or unordered: "+str(path))
    for col in d.columns:
        if col=="time":continue
        x=pd.to_numeric(d[col],errors="coerce")
        d[col]=x.where(np.isfinite(x)&(x>-9990))
    return d


def es_water(t):
    if t is None or t<=-80 or t>=65:return None
    return 6.112*math.exp(17.67*t/(t+243.5))


def es_ice(t):
    if t is None or t<=-80 or t>=65:return None
    return 6.112*math.exp(22.46*t/(t+272.62)) if t<0 else es_water(t)


def humid(t,vpd,pa,ice=False):
    if None in (t,vpd,pa):return None
    es=es_ice(t) if ice else es_water(t)
    if es is None:return None
    ea=es-vpd
    denom=pa*1000-.378*ea*100
    if denom==0:return None
    q=.622*ea*100/denom
    return dict(sat_hpa=es,ea_hpa=ea,RH_pct=100*ea/es,q_kgkg=q)


def source_qc(rec,var):
    n=num(rec.get(var+"_F_QC"))
    return str(int(n)) if n in (0,1,2) else "UNKNOWN"


def simple_output(path,rows,columns):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root",type=Path,default=SITE_ROOT)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    p.add_argument("--context-hours",type=int,default=24)
    args=p.parse_args()
    if args.context_hours<2 or args.context_hours>72:
        p.error("--context-hours must be 2..72")
    flux,era=get_sources(args.sites_root)
    d1=df_for_site(flux,"_F")
    d2=df_for_site(era,"_ERA")
    if not np.array_equal(d1.time.to_numpy(),d2.time.to_numpy()):
        raise RuntimeError("FLUXMET and ERA5 exact-release timestamps misaligned")
    d=d1.merge(d2,on="time",how="one_to_one" if False else "inner",
               validate="one_to_one")
    if len(d)!=len(d1):
        raise RuntimeError("Source merge lost timestamps")
    ts=pd.to_datetime(list(TARGET),format="%Y-%m-%d %H:%M")
    indices=d.index[d.time.isin(ts)].tolist()
    if len(indices)!=3:
        raise RuntimeError("Three exact QC-v5 blocker timestamps are not available")
    if any(indices[j+1]-indices[j]!=1 for j in range(2)):
        raise RuntimeError("Blocker timestamps are not consecutive indices")
    if any(d.at[i,"time"]!=ts[j] for j,i in enumerate(indices)):
        raise RuntimeError("Blocker record alignment changed")
    # Use original source and companion context, not the 9 completed Stage18
    # derived forcing outputs. No guess about time zones or site climate.
    context_start=ts[0]-timedelta(hours=args.context_hours)
    context_end=ts[-1]+timedelta(hours=args.context_hours)
    frame=d.loc[(d.time>=context_start)&(d.time<=context_end)]
    context=[]
    counts=Counter()
    for row in frame.to_dict("records"):
        t,v,p=(num(row.get("TA_F")),num(row.get("VPD_F")),num(row.get("PA_F")))
        te,ve,pe=(num(row.get("TA_ERA")),num(row.get("VPD_ERA")),num(row.get("PA_ERA")))
        h=humid(t,v,p)
        hi=humid(t,v,p,ice=True)
        he=humid(te,ve,pe)
        same=(t is not None and te is not None and
              v is not None and ve is not None and
              p is not None and pe is not None and
              all(math.isclose(x,y,rel_tol=0,abs_tol=1e-8)
                  for x,y in zip((t,v,p),(te,ve,pe))))
        status=("SOURCE_EA_NONPOSITIVE" if h and h["ea_hpa"]<=0
                else "SOURCE_EA_POSITIVE" if h else "SOURCE_HUMIDITY_MISSING")
        counts[status]+=1
        context.append(dict(
            timestamp_local=row["time"].strftime("%Y-%m-%d %H:%M"),
            in_blocker=str(row["time"] in list(ts)),
            TA_F_C=t,VPD_F_hPa=v,PA_F_kPa=p,
            TA_F_QC=source_qc(row,"TA"),
            VPD_F_QC=source_qc(row,"VPD"),
            PA_F_QC=source_qc(row,"PA"),
            TA_ERA_C=te,VPD_ERA_hPa=ve,PA_ERA_kPa=pe,
            source_RH_water_pct=h["RH_pct"] if h else None,
            source_RH_ice_pct=hi["RH_pct"] if hi else None,
            ERA_RH_water_pct=he["RH_pct"] if he else None,
            source_ea_water_hPa=h["ea_hpa"] if h else None,
            ERA_ea_water_hPa=he["ea_hpa"] if he else None,
            identical_core_TA_VPD_PA=str(same),
            source_physics_class=status,
        ))

    # A conservative *candidate screen*, for exactly these 3 points:
    # interpolation only if both adjacent boundaries are physically valid
    # and are from the same calendar year; do not use a bad ERA-only value.
    first,last=indices[0],indices[-1]
    left=first-1
    right=last+1
    if left<0 or right>=len(d):
        raise RuntimeError("No bracketing half-hours around blocker")
    left_row=d.loc[left];right_row=d.loc[right]
    left_h=humid(num(left_row.TA_F),num(left_row.VPD_F),num(left_row.PA_F))
    right_h=humid(num(right_row.TA_F),num(right_row.VPD_F),num(right_row.PA_F))
    boundary_ok=(left_h is not None and right_h is not None and
                 left_h["ea_hpa"]>0 and right_h["ea_hpa"]>0 and
                 2004==left_row.time.year==right_row.time.year and
                 0<=num(left_row.VPD_F)<=125 and 0<=num(right_row.VPD_F)<=125)
    decisions=[]
    for j,i in enumerate(indices,1):
        row=d.loc[i]
        t,v,pa=[num(row[x]) for x in ("TA_F","VPD_F","PA_F")]
        et,ev,ep=[num(row[x]) for x in ("TA_ERA","VPD_ERA","PA_ERA")]
        original=humid(t,v,pa)
        model=humid(et,ev,ep)
        interpolated=(num(left_row.VPD_F)+j*(num(right_row.VPD_F)-
                      num(left_row.VPD_F))/4) if boundary_ok else None
        interpolation_h=humid(t,interpolated,pa)
        interp_ok=(interpolation_h is not None and
                   interpolated>=0 and interpolation_h["ea_hpa"]>0 and
                   0<=interpolation_h["q_kgkg"]<=.08)
        era_derived=(es_water(t)*(1-model["RH_pct"]/100)
                     if t is not None and model is not None and
                     1<=model["RH_pct"]<=100 and
                     et is not None and abs(t-et)<=8 else None)
        era_h=humid(t,era_derived,pa)
        era_ok=(era_h is not None and era_h["ea_hpa"]>0 and
                0<=era_h["q_kgkg"]<=.08)
        decisions.append(dict(
            site=SITE,timestamp_local=row.time.strftime("%Y-%m-%d %H:%M"),
            VPD_source_QC=source_qc(row,"VPD"),
            TA_source_QC=source_qc(row,"TA"),
            original_TA_C=t,original_VPD_hPa=v,
            original_RH_pct=original["RH_pct"] if original else None,
            ERA_TA_C=et,ERA_VPD_hPa=ev,
            ERA_RH_pct=model["RH_pct"] if model else None,
            interpolation_valid_boundaries=boundary_ok,
            interpolation_VPD_hPa=interpolated if interp_ok else None,
            interpolation_RH_pct=interpolation_h["RH_pct"] if interp_ok else None,
            ERA_RH_based_VPD_hPa=era_derived if era_ok else None,
            ERA_RH_based_resulting_RH_pct=era_h["RH_pct"] if era_ok else None,
            candidates_compared_not_applied="YES",
            decision="HOLD_FOR_PROVENANCE_CONTEXT_MANUAL_REVIEW",
        ))

    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage19_US-Bar_QCv5_blocker_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    simple_output(out/"source_and_ERA_context.csv",context,list(context[0]))
    simple_output(out/"three_blocker_candidate_screens_NOT_APPLIED.csv",
                  decisions,list(decisions[0]))
    print("STAGE19 SUMMARY: US-Bar exact QC-v5 blockers=3;"
          " context_records=%d"%len(context))
    print("Original FLUXMET:",flux)
    print("Original ERA5:",era)
    print("Neighbouring original FLUXMET humidity:"
          " prev_RH=%s next_RH=%s" %
          (left_h["RH_pct"] if left_h else None,
           right_h["RH_pct"] if right_h else None))
    print("Short (3 half-hour) gap has physically valid interpolation boundaries:",
          boundary_ok)
    print("Context source physics:",dict(counts))
    for rec in decisions:
        print("  %s TA=%s VPD=%s QC=(%s,%s) original_RH=%s ERA_RH=%s "
              "interp_candidate=%s ERA_RH_candidate=%s"%
              (rec["timestamp_local"],rec["original_TA_C"],
               rec["original_VPD_hPa"],rec["TA_source_QC"],
               rec["VPD_source_QC"],rec["original_RH_pct"],
               rec["ERA_RH_pct"],rec["interpolation_VPD_hPa"],
               rec["ERA_RH_based_VPD_hPa"]))
    print("REPORT DIR:",out)
    print("READ ONLY. DO NOT overwrite incomplete Stage18 experiment;"
          " all candidates remain unapplied and unapproved.")
    print("Ice-based saturation differs from liquid-water; do not use as auto-fix.")


if __name__=="__main__":
    main()

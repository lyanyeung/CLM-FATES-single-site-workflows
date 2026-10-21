#!/usr/bin/env python3
"""Stage 15: read-only full-cycle AmeriFlux 10-site scientific meteorology gate.

Reuse the *diagnostic* lessons of ICOS eight-site QC v5, CH-Aws and IT-Noe:
look beyond RH<=0 at low positive RH, unusual TA=0/VPD~6.110 plateaus,
temperature jumps, tower/ERA disagreement, pressure and longwave anomalies,
QC 0/1/2 lineage, and clusters of flags up to two hours apart.

This script NEVER invokes the older v5 *repair* routine, never clips RH,
never substitutes ERA and never writes source/processed forcing, DATM,
surface, CIME or Slurm files. Its reports live ONLY under experiment/reports.
A screening flag is NOT scientific evidence of a faulty tower measurement.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
MANIFEST=Path(__file__).resolve().parents[2]/"sites.tsv"
VARS=("TA","VPD","PA","SW_IN","LW_IN","WS","P")
MET_REQUIRED=["TIMESTAMP_START"]+[v+"_F" for v in VARS]
ERA_REQUIRED=["TIMESTAMP_START","TA_ERA","VPD_ERA","PA_ERA"]


def load_manifest():
    with MANIFEST.open("r",newline="",encoding="utf-8") as f:
        entries=list(csv.DictReader(f,delimiter="\t"))
    required={"site","package","first_year","last_year"}
    if len(entries)!=10 or len({x["site"] for x in entries})!=10:
        raise RuntimeError("Expected exactly 10 unique AmeriFlux stations")
    if any(set(x)!=required for x in entries):
        raise RuntimeError("Unexpected sites.tsv header: expected "+str(required))
    return entries


def exact_source(raw,pattern):
    result=sorted(p for p in raw.glob("*.csv") if pattern in p.name.upper())
    if len(result)!=1:
        raise RuntimeError("Expected one %s CSV in %s, found %d" %
                           (pattern,raw,len(result)))
    return result[0]


def preflight(site,root):
    raw=root/site["site"]/"forcing"/"raw"/site["package"]
    if not raw.is_dir():
        raise RuntimeError("Missing pinned raw release directory "+str(raw))
    flux=exact_source(raw,"FLUXMET_HH")
    era=exact_source(raw,"ERA5_HH")
    with flux.open("r",encoding="utf-8-sig",newline="") as f:
        fh=next(csv.reader(f))
    with era.open("r",encoding="utf-8-sig",newline="") as f:
        eh=next(csv.reader(f))
    if not set(MET_REQUIRED).issubset(fh):
        raise RuntimeError("FLUXMET missing "+str(set(MET_REQUIRED)-set(fh)))
    if not set(ERA_REQUIRED).issubset(eh):
        raise RuntimeError("ERA5 missing "+str(set(ERA_REQUIRED)-set(eh)))
    return flux,era,fh


def times(col):
    raw=col.astype("string").str.strip().str.replace(r"\.0$","",regex=True)
    return pd.to_datetime(raw,format="%Y%m%d%H%M",errors="raise")


def read_product(path, cols, first,last):
    d=pd.read_csv(path,usecols=cols,dtype={"TIMESTAMP_START":"string"},
                  low_memory=False)
    d["time"]=times(d["TIMESTAMP_START"])
    d=d.loc[d.time.dt.year.between(first,last)].copy()
    d=d.loc[~((d.time.dt.month==2)&(d.time.dt.day==29))].copy()
    if d.time.isna().any() or d.time.duplicated().any():
        raise RuntimeError("Invalid/duplicate source timestamps in "+str(path))
    d.sort_values("time",inplace=True)
    d.reset_index(drop=True,inplace=True)
    d.drop(columns=["TIMESTAMP_START"],inplace=True)
    for col in cols:
        if col=="TIMESTAMP_START":continue
        vals=pd.to_numeric(d[col],errors="coerce")
        d[col]=vals.where(np.isfinite(vals)&(vals>-9990))
    return d


def boolmask(series):
    return series.fillna(False).to_numpy(dtype=bool)


def series_stat(value):
    return float(value) if pd.notna(value) else None


def episodes(indices,timestamps,flagged,largest_gap="2h"):
    if not len(indices):
        return [],np.empty(0,dtype=int)
    spans=[]
    flags=flagged.iloc[indices].copy()
    ep=(flags.time.diff().gt(pd.Timedelta(largest_gap)).fillna(True).cumsum()+1).astype(int)
    for eid,group in flags.groupby(ep,sort=True):
        spans.append((int(eid),group))
    return spans,ep.to_numpy(dtype=int)


def analyze(site,flux,era,header):
    name=site["site"]
    first,last=int(site["first_year"]),int(site["last_year"])
    qcs=[v+"_F_QC" for v in VARS if v+"_F_QC" in header]
    met=read_product(flux,MET_REQUIRED+qcs,first,last)
    ref=read_product(era,ERA_REQUIRED,first,last)
    # Validate complete declared NO_LEAP half-hour chronology *before*
    # source-context comparison, without guessing time zone or DST.
    expected=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                           freq="30min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(met)!=len(expected) or not np.array_equal(met.time.to_numpy(),expected.to_numpy()):
        raise RuntimeError(name+": FLUXMET timeline is not complete NO_LEAP 30-min")
    if len(ref)!=len(expected) or not np.array_equal(ref.time.to_numpy(),expected.to_numpy()):
        raise RuntimeError(name+": ERA5 companion timeline is not complete NO_LEAP 30-min")
    d=met.merge(ref,on="time",how="left",validate="one_to_one")
    t=d["TA_F"];v=d["VPD_F"];p=d["PA_F"]
    era_t=d["TA_ERA"];era_v=d["VPD_ERA"];era_p=d["PA_ERA"]
    with np.errstate(all="ignore"):
        es=6.112*np.exp(np.clip(17.67*t/(t+243.5),-40,40))
        ea=es-v
        rh=100*ea/es
        esr=6.112*np.exp(np.clip(17.67*era_t/(era_t+243.5),-40,40))
        ear=esr-era_v
        rhr=100*ear/esr
    criteria={
        "EA_NONPOSITIVE":(ea<=0)&t.notna()&v.notna(),
        "RH_POSITIVE_0_TO1":(rh>0)&(rh<1),
        "RH_POSITIVE_1_TO5":(rh>=1)&(rh<5),
        "RH_POSITIVE_5_TO10":(rh>=5)&(rh<10),
        "TA_ZERO_VPD_6110":t.abs().le(.0005)&(v-6.110).abs().le(.008),
        "TA_30MIN_JUMP_GT8C":t.diff().abs()>8,
        "TA_VS_ERA_DIFF_GT15C":(t-era_t).abs()>15,
        "PA_30MIN_JUMP_GT5KPA":p.diff().abs()>5,
        "PA_OUTSIDE_50_110KPA":(p<50)|(p>110),
        "LW_OUTSIDE_60_800":(d["LW_IN_F"]<60)|(d["LW_IN_F"]>800),
        "ERA_HUMIDITY_NONPOSITIVE":(ear<=0)&era_t.notna()&era_v.notna(),
    }
    # Cross-year discontinuities can be real or due to source boundaries;
    # keep flagged for review. Long plateau is a stricter CH-Aws-inspired flag.
    plateau=boolmask(criteria["TA_ZERO_VPD_6110"])
    runs=np.cumsum(np.r_[True,plateau[1:]!=plateau[:-1]])
    sizes=pd.Series(runs[plateau]).value_counts()
    long_ids=set(sizes[sizes>=6].index)
    criteria["ZERO_TA_VPD_PLATEAU_3HR"]=pd.Series(
        plateau & np.isin(runs,list(long_ids)),index=d.index)
    mask=np.zeros(len(d),dtype=bool)
    for key,x in criteria.items():
        if key!="ERA_HUMIDITY_NONPOSITIVE":
            mask |= boolmask(x)
    n=int(mask.sum())
    annual=[]
    for year in range(first,last+1):
        chosen=d.time.dt.year.eq(year).to_numpy()
        counts={k:int((chosen & boolmask(z)).sum()) for k,z in criteria.items()}
        annual.append(dict(site=name,year=year,
                           screened_timesteps=int(chosen.sum()),
                           any_site_review_flags=int((chosen&mask).sum()),
                           **counts))
    sel=np.flatnonzero(mask)
    enriched=pd.DataFrame({
        "time":d.time, "site":name, "TA_F_C":t,"VPD_F_hPa":v,
        "PA_F_kPa":p, "RH_implied_pct":rh,
        "EA_implied_hPa":ea, "TA_ERA_C":era_t,
        "VPD_ERA_hPa":era_v,"PA_ERA_kPa":era_p,
        "ERA_RH_implied_pct":rhr,
        "TA_diff_ERA_C":t-era_t,
    })
    for var in ("TA","VPD","PA","LW_IN"):
        if var+"_F_QC" in d:
            enriched[var+"_F_QC"]=d[var+"_F_QC"]
        else:
            enriched[var+"_F_QC"]=np.nan
    for key,series in criteria.items():
        enriched[key]=boolmask(series)
    grouped,ids=episodes(sel,d.time,enriched)
    if len(ids)!=len(sel):
        raise RuntimeError("Episode grouping lost flagged half-hours")
    flagged=enriched.iloc[sel].copy()
    flagged.insert(0,"episode_id",ids)
    episodes_out=[]
    for eid,group in grouped:
        reasons=[key for key in criteria if key!="ERA_HUMIDITY_NONPOSITIVE"
                 and group[key].any()]
        # Only a triage label. No repairs are approved by these flags.
        elevated=any(group[key].any() for key in (
            "EA_NONPOSITIVE","ZERO_TA_VPD_PLATEAU_3HR",
            "TA_30MIN_JUMP_GT8C","TA_VS_ERA_DIFF_GT15C",
            "PA_30MIN_JUMP_GT5KPA","PA_OUTSIDE_50_110KPA",
            "LW_OUTSIDE_60_800"))
        episode_status=("ELEVATED_SCIENCE_REVIEW" if elevated
                        else "LOW_RH_OR_SOURCE_REVIEW")
        episodes_out.append(dict(
            site=name,episode_id=eid,
            start_local=str(group.time.iloc[0]),
            end_local=str(group.time.iloc[-1]),
            n_flagged=len(group),duration_span_hours=float(
                (group.time.iloc[-1]-group.time.iloc[0]).total_seconds()/3600+.5),
            flagged_reasons="|".join(reasons),priority=episode_status,
            min_RH_pct=series_stat(group.RH_implied_pct.min()),
            max_abs_TA_ERA_diff_C=series_stat(group.TA_diff_ERA_C.abs().max()),
            decision="PENDING_SCIENTIFIC_REVIEW_NO_EDITS"))
    summary=dict(site=name,years=last-first+1,
                 source_rows=len(d),fluxmet_flagged=n,
                 low_positive_RH_lt10=int(sum(boolmask(criteria[key]).sum()
                     for key in ("RH_POSITIVE_0_TO1","RH_POSITIVE_1_TO5",
                                 "RH_POSITIVE_5_TO10"))),
                 negative_or_zero_EA=int(boolmask(criteria["EA_NONPOSITIVE"]).sum()),
                 temperature_jump_gt8=int(boolmask(criteria["TA_30MIN_JUMP_GT8C"]).sum()),
                 temp_vs_era_gt15=int(boolmask(criteria["TA_VS_ERA_DIFF_GT15C"]).sum()),
                 QC2_VPD_in_flagged=int(flagged["VPD_F_QC"].eq(2).sum()),
                 episodes=len(episodes_out),
                 evidence_status="REVIEW_NOT_APPROVED_FOR_DATM")
    return summary,annual,flagged,episodes_out


def write(path,table):
    if isinstance(table,pd.DataFrame):
        table.to_csv(path,index=False)
        return
    df=pd.DataFrame(table)
    df.to_csv(path,index=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    parser.add_argument("--report-root",type=Path,default=REPORTS)
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true",help="Check paths/headers only; write nothing")
    g.add_argument("--run",action="store_true",help="Read full sources, save small QC reports")
    parser.add_argument("--sites",nargs="+",
                        help="Optional subset from the 10 pinned manifest sites")
    args=parser.parse_args()
    manifest=load_manifest()
    if args.sites:
        unknown=set(args.sites)-{s["site"] for s in manifest}
        if unknown: parser.error("Unknown site(s): "+repr(sorted(unknown)))
        manifest=[r for r in manifest if r["site"] in args.sites]
    preflighted=[]
    for site in manifest:
        try:
            flux,era,header=preflight(site,args.root)
            preflighted.append((site,flux,era,header))
            print("CHECK OK %-7s %s to %s" %
                  (site["site"],site["first_year"],site["last_year"]),flush=True)
        except Exception as e:
            raise SystemExit("CHECK FAILED "+site["site"]+": "+str(e))
    print("STAGE15 PREFLIGHT: %d/%d pinned releases ready" %
          (len(preflighted),len(manifest)))
    if args.check:
        print("CHECK ONLY: No data or reports written.");return
    # Reports exclusively under experiment/reports; require an absent
    # timestamped directory to avoid accidental overwrites or collisions.
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage15_fullcycle_10sites_"+stamp)
    if args.root in out.parents or out==args.root:
        raise RuntimeError("Refusing to write diagnostic output inside MY_EC_SITE")
    out.mkdir(parents=True,exist_ok=False)
    totals=[];all_years=[];all_episodes=[]
    for site,flux,era,header in preflighted:
        name=site["site"]
        print("AUDITING:",name,flush=True)
        try:
            summary,years,flags,episode_data=analyze(site,flux,era,header)
            write(out/(name+"_flagged_review_times.csv"),flags)
            totals.append(summary)
            all_years.extend(years)
            all_episodes.extend(episode_data)
            print("  %s flagged=%d low_RH_0to10=%d RH<=0=%d TA_jumps=%d episodes=%d"%
                  (name,summary["fluxmet_flagged"],summary["low_positive_RH_lt10"],
                   summary["negative_or_zero_EA"],summary["temperature_jump_gt8"],
                   summary["episodes"]),flush=True)
        except Exception as e:
            (out/"INCOMPLETE_FAIL_CLOSED.txt").write_text(
                "Site failed: "+name+"\n"+repr(e)+"\n",encoding="utf-8")
            raise
    write(out/"site_science_gate_summary.csv",totals)
    write(out/"annual_science_gate_counts.csv",all_years)
    write(out/"two_hour_review_episode_ledger.csv",all_episodes)
    print("\nSTAGE15 SUMMARY: audited=%d/%d sites; scanned=%d half-hours;"
          " REVIEW half-hours=%d; episodes=%d" %
          (len(totals),len(manifest),
           sum(int(x["source_rows"]) for x in totals),
           sum(int(x["fluxmet_flagged"]) for x in totals),
           len(all_episodes)),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("GATE=OPEN_NOT_APPROVED. REPORTS ONLY. NO model/forcing edits.",flush=True)
    print("Next: review source/QC and full-cycle RH<10%, TA/PA anomalies,"
          " physical/temporal provenance, BIF height and surface-PFT.",flush=True)


if __name__=="__main__":
    main()

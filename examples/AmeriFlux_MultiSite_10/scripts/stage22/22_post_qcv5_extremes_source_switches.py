#!/usr/bin/env python3
"""Stage22: independent, read-only extreme-meteorology QC of all ten v5 candidates.

Lessons: ES-LJu's extreme TA/QC0 and paired TA/VPD mismatch; IT-Noe's
half-hour jumps, adjacent context and source switches; CH-Aws's low positive
RH; and 13-site rainfall provenance. All findings are scientific review flags,
not instructions to change measurements or to use ERA as independent truth.

Input: Stage18's nine candidates and Stage20's isolated US-Bar sensitivity.
Output: timestamped report CSVs ONLY under experiment/reports. No raw, v5
candidate, surface, DATM, CIME or Slurm modifications.
"""
import argparse
import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SITE_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
STAGE22_BUILD = "20261022_stage22_end_year_fix_v2"
MANIFEST=Path(__file__).resolve().parents[2]/"sites.tsv"
MET=("TA","VPD","PA","SW_IN","LW_IN","WS","P")
FINAL=("TA_USE","VPD_USE","PSRF","FSDS","FLDS","WIND","PRECTmms","QBOT")


def records(path,delimiter=","):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter=delimiter))


def save(path,data,fields):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def exact_file(folder,token):
    results=sorted(p for p in folder.glob("*.csv") if token in p.name.upper())
    if len(results)!=1:
        raise RuntimeError("Expected one "+token+" in "+str(folder))
    return results[0]


def frame(path,columns,first,last,raw):
    timecol="TIMESTAMP_START" if raw else "time"
    header=set(pd.read_csv(path,nrows=0).columns)
    if not set(columns).issubset(header):
        raise RuntimeError("Missing columns from "+str(path)+": "+str(set(columns)-header))
    d=pd.read_csv(path,usecols=columns,dtype={timecol:"string"},low_memory=False)
    stamp=d.pop(timecol).str.strip()
    if raw:
        stamp=stamp.str.replace(r"\.0$","",regex=True)
        tm=pd.to_datetime(stamp,format="%Y%m%d%H%M",errors="raise")
    else:
        tm=pd.to_datetime(stamp,errors="raise")
    d.insert(0,"time",tm)
    mask=d.time.dt.year.between(first,last)&~(
        d.time.dt.month.eq(2)&d.time.dt.day.eq(29))
    d=d.loc[mask].reset_index(drop=True)
    reference=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                            freq="30min",inclusive="left")
    reference=reference[~((reference.month==2)&(reference.day==29))]
    if len(d)!=len(reference) or not np.array_equal(
        d.time.to_numpy(),reference.to_numpy()):
        raise RuntimeError("Wrong NOLEAP timestamps in "+str(path))
    for col in columns:
        if col==timecol:continue
        a=pd.to_numeric(d[col],errors="coerce")
        d[col]=a.where(np.isfinite(a)&(a>-9990))
    return d


def jumps(series,threshold):
    dv=np.diff(series)
    return np.r_[False,np.isfinite(dv)&(np.abs(dv)>threshold)]


def peaks(series,threshold):
    left=np.r_[np.nan,np.diff(series)]
    right=np.r_[np.diff(series),np.nan]
    return (np.isfinite(left)&np.isfinite(right)&
            (np.abs(left)>threshold)&(np.abs(right)>threshold)&
            (np.sign(left)!=np.sign(right)))


def run(site,origpath,erapath,finalpath,eventpath,first,end_year):
    qcs=[v+"_F_QC" for v in MET]
    origin=frame(origpath,["TIMESTAMP_START"]+
                 [v+"_F" for v in MET]+qcs,first,end_year,True)
    era=frame(erapath,["TIMESTAMP_START","TA_ERA","VPD_ERA","PA_ERA"],first,end_year,True)
    final=frame(finalpath,["time",*FINAL],first,end_year,False)
    if not np.array_equal(origin.time.to_numpy(),era.time.to_numpy()) or not np.array_equal(
        origin.time.to_numpy(),final.time.to_numpy()):
        raise RuntimeError(site+": source and candidate timestamps differ")
    old_t=origin["TA_F"].to_numpy(float)
    new_t=final["TA_USE"].to_numpy(float)
    era_t=era["TA_ERA"].to_numpy(float)
    old_v=origin["VPD_F"].to_numpy(float)
    new_v=final["VPD_USE"].to_numpy(float)
    qc_t=origin["TA_F_QC"].to_numpy(float)
    qc_v=origin["VPD_F_QC"].to_numpy(float)
    pressure=final["PSRF"].to_numpy(float)
    rain=final["PRECTmms"].to_numpy(float)*1800
    with np.errstate(all="ignore"):
        es=6.112*np.exp(np.clip(17.67*new_t/(new_t+243.5),-40,40))
        rh=100*(es-new_v)/es
    old_jump=jumps(old_t,8)
    new_jump=jumps(new_t,8)
    qcchange=np.r_[False,(qc_t[1:]!=qc_t[:-1])&
                     np.isfinite(qc_t[1:])&np.isfinite(qc_t[:-1])]
    flags={
        "NEW_TA_30MIN_JUMP_GT8C":new_jump&~old_jump,
        "CANDIDATE_TA_30MIN_JUMP_GT8C":new_jump,
        "ISOLATED_TA_SPIKE_GT8C":peaks(new_t,8),
        "TA_VS_ERA_GT15C":np.isfinite(new_t)&np.isfinite(era_t)&(np.abs(new_t-era_t)>15),
        "TA_EXTREME_LT_MINUS25_OR_GT45":(new_t< -25)|(new_t>45),
        "TA_QC_SOURCE_SWITCH_WITH_JUMP":qcchange&new_jump,
        "VPD_30MIN_JUMP_GT5HPA":jumps(new_v,5),
        "PSRF_30MIN_JUMP_GT5000PA":jumps(pressure,5000),
        "PRECIP_GT18MM_PER_30MIN":rain>18,
        "POSITIVE_RH_LT1PCT":(rh>0)&(rh<1),
        "RH_NONPOSITIVE":rh<=0,
        "QBOT_OUTSIDE_0_TO008":(final["QBOT"].to_numpy(float)<0)|
                               (final["QBOT"].to_numpy(float)>0.08),
    }
    ev=records(eventpath)
    qc0=[r for r in ev if str(r.get("official_qc","")).strip() in ("0","0.0")]
    event_by_time=defaultdict(list)
    for r in ev:
        ts=pd.Timestamp(r["time"]).strftime("%Y-%m-%d %H:%M:%S")
        event_by_time[ts].append(r)
    qc0_by_time=defaultdict(list)
    for r in qc0:
        ts=pd.Timestamp(r["time"]).strftime("%Y-%m-%d %H:%M:%S")
        qc0_by_time[ts].append(r)
    times=final.time.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy()
    valid_times=set(times)
    if not set(event_by_time).issubset(valid_times):
        raise RuntimeError(site+": candidate modification ledger has unknown timestamps")
    mask=np.zeros(len(final),dtype=bool)
    for x in flags.values():mask|=np.asarray(x,dtype=bool)
    mask|=np.isin(times,list(qc0_by_time))
    selected=np.flatnonzero(mask)
    detailed=[]
    episode=0
    last_flagged_time=None  # Never shadow `last` (the site end year).
    for i in selected:
        when=final.time.iloc[i]
        if (last_flagged_time is None or
                (when-last_flagged_time).total_seconds()>2*3600):
            episode+=1
        last_flagged_time=when
        ts=times[i]
        reasons=[k for k,m in flags.items() if m[i]]
        if ts in qc0_by_time:reasons.append("QC0_MEASURED_EDIT")
        detailed.append(dict(
            site=site,episode_id=episode,timestamp_local=ts,
            review_flags="|".join(reasons),
            original_TA_C=old_t[i],candidate_TA_C=new_t[i],ERA_TA_C=era_t[i],
            original_TA_QC=qc_t[i],original_VPD_QC=qc_v[i],
            original_VPD_hPa=old_v[i],candidate_VPD_hPa=new_v[i],
            candidate_RH_pct=rh[i],candidate_PSRF_Pa=pressure[i],
            candidate_rain_mm_halfhour=rain[i],
            modification_variables="|".join(sorted(r.get("variable","")
                for r in event_by_time.get(ts,[]))),
            QC0_modification_count=len(qc0_by_time.get(ts,[])),
            science_decision="HOLD_NO_AUTOMATIC_REPLACEMENT"))
    qc0_detail=[
        dict(site=site,timestamp_local=pd.Timestamp(r["time"]).strftime("%Y-%m-%d %H:%M:%S"),
             variable=r.get("variable",""),original_value=r.get("original_value",""),
             replacement_value=r.get("final_value",""),reason=r.get("reason",""),
             official_qc=r.get("official_qc",""),
             science_decision="HOLD_QC0_ORIGINAL_MEASUREMENT_CHANGE")
        for r in qc0]
    stats={k:int(np.asarray(v,dtype=bool).sum()) for k,v in flags.items()}
    stats.update(dict(site=site,records=len(final),QC0_edits=len(qc0),
                      review_timestamps=len(detailed),review_episodes=episode,
                      original_TA_jumps_gt8=int(old_jump.sum()),
                      science_status="HOLD_PRE_DATM"))
    byyear=[]
    years=final.time.dt.year.to_numpy()
    for year in range(first,end_year+1):
        chosen=years==year
        byyear.append(dict(site=site,year=year,**{
            key:int((np.asarray(val,dtype=bool)&chosen).sum())
            for key,val in flags.items()}))
    return stats,detailed,qc0_detail,byyear


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage18-root",type=Path,required=True)
    p.add_argument("--stage20-root",type=Path,required=True)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    args=p.parse_args()
    rows=records(MANIFEST,"\t")
    if len(rows)!=10 or len({r["site"] for r in rows})!=10:
        raise RuntimeError("Expected exact ten-site manifest")
    old=args.stage18_root.resolve()
    bar=args.stage20_root.resolve()
    if old==bar or not old.is_dir() or not bar.is_dir():
        raise RuntimeError("Stage18 and Stage20 must be different existing folders")
    if not (bar/"COMPLETE_SENSITIVITY_NOT_SCIENCE_APPROVED").is_file():
        raise RuntimeError("Stage20 is not a completed isolated numeric sensitivity")
    jobs=[]
    for r in rows:
        site=r["site"];first=int(r["first_year"]);last=int(r["last_year"])
        source=SITE_ROOT/site/"forcing"/"raw"/r["package"]
        trial=bar if site=="US-Bar" else old
        paths=[exact_file(source,"FLUXMET_HH"),
               exact_file(source,"ERA5_HH"),
               trial/site/"forcing"/"processed_v5"/
               f"{site}_CLM_forcing_{first}_{last}.csv",
               trial/site/"forcing"/"qc_v5"/
               f"{site}_replacement_events.csv"]
        for path in paths:
            if not path.is_file():raise RuntimeError("Missing required input: "+str(path))
        jobs.append((site,paths,first,last))
        print("CHECK OK %-7s %s" %(site,trial.name),flush=True)
    print("STAGE22 BUILD:", STAGE22_BUILD, flush=True)
    print("STAGE22 PREFLIGHT: 10/10 candidates",flush=True)
    if args.check:
        print("CHECK ONLY; no changes");return
    stats=[];flagged=[];allqc0=[];annual=[]
    for site,files,first,last in jobs:
        s,e,q,a=run(site,*files,first,last)
        stats.append(s);flagged.extend(e);allqc0.extend(q);annual.extend(a)
        print("  %-7s QC0_edits=%4d candidate_TA_jump=%4d new_jump=%4d TA_vs_ERA=%5d positive_RH_lt1=%3d"%
              (site,s["QC0_edits"],s["CANDIDATE_TA_30MIN_JUMP_GT8C"],
               s["NEW_TA_30MIN_JUMP_GT8C"],s["TA_VS_ERA_GT15C"],
               s["POSITIVE_RH_LT1PCT"]),flush=True)
    if len(allqc0)!=518:
        raise RuntimeError("QC0 event count differs from Stage21 518; abort")
    if sum(s["RH_NONPOSITIVE"] for s in stats)!=0:
        raise RuntimeError("Residual negative humidity detected; abort")
    dest=args.report_root/("stage22_science_extreme_qc_"+datetime.now(
        timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    dest.mkdir(parents=True,exist_ok=False)
    save(dest/"site_extremes_and_sources_summary.csv",stats,list(stats[0]))
    save(dest/"timestamped_event_context.csv",flagged,list(flagged[0]))
    save(dest/"all_518_original_QC0_edits.csv",allqc0,list(allqc0[0]))
    save(dest/"annual_extreme_counts.csv",annual,list(annual[0]))
    print("\nSTAGE22 SUMMARY: sites=10 QC0_edits=518"
          " candidate_TA_jumps_gt8=%d new_TA_jumps_gt8=%d"
          " candidate_TA_vs_ERA_gt15=%d RH_nonpositive=%d"%
          (sum(x["CANDIDATE_TA_30MIN_JUMP_GT8C"] for x in stats),
           sum(x["NEW_TA_30MIN_JUMP_GT8C"] for x in stats),
           sum(x["TA_VS_ERA_GT15C"] for x in stats),
           sum(x["RH_NONPOSITIVE"] for x in stats)),flush=True)
    print("REPORT DIR:",dest,flush=True)
    print("No source, forcing, DATM, surface, CIME or Slurm file modified.")
    print("Flags rank scientific review only; QC0 and legitimate extremes not auto-replaced.")


if __name__=="__main__":
    main()

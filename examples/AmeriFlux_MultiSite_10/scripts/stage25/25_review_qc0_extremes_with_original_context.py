#!/usr/bin/env python3
"""Batch01 Stage25: targeted scientific evidence for 518 QC0 edits and extremes.

Read the COMPLETED Stage24 decision queue and original pinned AmeriFlux
FLUXMET_HH / companion ERA5_HH / Stage18+20 QCv5 candidate CSVs. Reconstruct
TA/VPD/PA physical plausibility, compare source and final before/after 30-min
changes, retain a +/-4h context, and issue a *science-review recommendation*
for each changed-QC0 or risky event. This is not an auto-repair procedure.

Science rules: ERA and official QC2 are not independent in some releases;
a discrepancy from ERA does NOT prove tower measurement is wrong. Never
blanket-floor low positive RH; do not infer DATM/FATES suitability from QBOT.
No source, forcing, DATM, surface, CIME, or job files are changed.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BATCH=Path(__file__).resolve().parents[2]
SOURCE_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EXPERIMENTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
DEFAULT24=EXPERIMENTS/"reports/stage24_postv5_science_review_queue_20261022T012619832055Z"
TRIAL18=EXPERIMENTS/"qcv5_trial_20261021T232839Z"
TRIAL20=EXPERIMENTS/"usbar_scoped_trial_20261021T234357Z"
SELECT_FLAGS={
    "QC0_MEASURED_EDIT","POSITIVE_RH_LT1PCT",
    "ISOLATED_TA_SPIKE_GT8C","TA_EXTREME_LT_MINUS25_OR_GT45",
    "TA_QC_SOURCE_SWITCH_WITH_JUMP","CANDIDATE_TA_30MIN_JUMP_GT8C",
    "TA_VS_ERA_GT15C","PSRF_30MIN_JUMP_GT5000PA",
    "VPD_30MIN_JUMP_GT5HPA"
}
# Heavy rain is reviewed in Stage24, but not mistaken for a humidity/TA error.
SOURCES=("TA_F","VPD_F","PA_F","TA_F_QC","VPD_F_QC","PA_F_QC")
ERA=("TA_ERA","VPD_ERA","PA_ERA")
CANDIDATE=("TA_USE","VPD_USE","PSRF","QBOT")


def csv_rows(path,sep=","):
    if not path.is_file():raise RuntimeError("Missing: "+str(path))
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter=sep))


def out_csv(path,records,fields):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def exactly_one(folder,needle):
    candidates=sorted(p for p in folder.glob("*.csv") if needle in p.name.upper())
    if len(candidates)!=1:
        raise RuntimeError("Expected exactly one "+needle+" in "+str(folder))
    return candidates[0]


def get_input_locations(site_entry,source_root,stage18,stage20):
    site=site_entry["site"]
    raw=source_root/site/"forcing"/"raw"/site_entry["package"]
    chosen=stage20 if site=="US-Bar" else stage18
    first,last=site_entry["first_year"],site_entry["last_year"]
    return (exactly_one(raw,"FLUXMET_HH"), exactly_one(raw,"ERA5_HH"),
            chosen/site/"forcing"/"processed_v5"/
            f"{site}_CLM_forcing_{first}_{last}.csv")


def parse_met(path,fields,first,last,is_raw):
    timecol="TIMESTAMP_START" if is_raw else "time"
    header=set(pd.read_csv(path,nrows=0).columns)
    required=[timecol,*fields]
    if not set(required).issubset(header):
        raise RuntimeError(str(path)+": missing "+str(set(required)-header))
    d=pd.read_csv(path,usecols=required,dtype={timecol:"string"},low_memory=False)
    raw=d.pop(timecol).str.strip()
    if is_raw:
        raw=raw.str.replace(r"\.0$","",regex=True)
        dates=pd.to_datetime(raw,format="%Y%m%d%H%M",errors="raise")
    else:
        dates=pd.to_datetime(raw,errors="raise")
    d.insert(0,"time",dates)
    d=d.loc[d.time.dt.year.between(first,last)&
            ~((d.time.dt.month==2)&(d.time.dt.day==29))].reset_index(drop=True)
    expected=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                           freq="30min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(d)!=len(expected) or not np.array_equal(
            d.time.to_numpy(),expected.to_numpy()):
        raise RuntimeError(str(path)+": NO_LEAP coverage/date mismatch")
    for col in fields:
        n=pd.to_numeric(d[col],errors="coerce")
        d[col]=n.where(np.isfinite(n)&(n>-9990))
    return d


def saturate(temp):
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(np.clip(17.67*temp/(temp+243.5),-40,40))


def calc_rh(t,vpd):
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 100*(saturate(t)-vpd)/saturate(t)


def scalar(x):
    v=float(x)
    return v if np.isfinite(v) else None


def evidence_class(flags,old_rh,new_rh,qct,qcv,ta,ta_era,ta0,ta_before,ta_after):
    """Order: source physics, QC0 edits, impossible low RH, TA patterns, context."""
    t_diff=abs(ta-ta_era) if np.isfinite(ta) and np.isfinite(ta_era) else np.nan
    source_impossible=np.isfinite(old_rh) and old_rh<=0
    edit="QC0_MEASURED_EDIT" in flags
    low="POSITIVE_RH_LT1PCT" in flags
    spike="ISOLATED_TA_SPIKE_GT8C" in flags
    extreme="TA_EXTREME_LT_MINUS25_OR_GT45" in flags
    err_ctx="TA_QC_SOURCE_SWITCH_WITH_JUMP" in flags
    if edit and source_impossible:
        return "P0_SOURCE_PHYSICS_QC0_CHANGED","REVIEW_QC0_PHYSICAL_CONTRADICTION_WITH_INDEPENDENT_EVIDENCE"
    if edit:
        return "P1_QC0_CHANGED","REVIEW_SOURCE_AND_REPLACEMENT_PROVENANCE"
    if extreme and np.isfinite(t_diff) and t_diff>15:
        return "P1_ESLJU_STYLE_EXTREME_TA","COMPARE_TA_VPD_PAIR_AND_INDEPENDENT_STATION"
    if spike or err_ctx:
        return "P1_ITNOE_STYLE_TA_DISCONTINUITY","VERIFY_LOCAL_NEIGHBOURS_QC_AND_SOURCE_SWITCH"
    if low:
        return "P1_CHAWS_STYLE_LOW_RH","VERIFY_INDEPENDENT_HUMIDITY_AND_TA_CONTEXT"
    if extreme:
        return "P1_EXTREME_TA","REVIEW_CONTEXT_AND_SITE_CLIMATOLOGY"
    if np.isfinite(t_diff) and t_diff>15:
        return "P2_TA_ERA_DIVERGENCE","CHECK_MEASUREMENT_PROVENANCE_AND_TIME_ALIGNMENT"
    if "CANDIDATE_TA_30MIN_JUMP_GT8C" in flags:
        return "P2_EXISTING_TA_JUMP","CHECK_REAL_WEATHER_OR_DATA_DISCONTINUITY"
    return "P2_OTHER_CONTEXT","REVIEW_SOURCE_AND_NEIGHBOURS"


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--run",action="store_true")
    p.add_argument("--stage24-dir",type=Path,default=DEFAULT24)
    p.add_argument("--sites-root",type=Path,default=SOURCE_ROOT)
    p.add_argument("--stage18-root",type=Path,default=TRIAL18)
    p.add_argument("--stage20-root",type=Path,default=TRIAL20)
    p.add_argument("--report-root",type=Path,default=EXPERIMENTS/"reports")
    p.add_argument("--context-hours",type=int,default=4)
    args=p.parse_args()
    if not 1<=args.context_hours<=12:
        p.error("--context-hours must be 1..12")

    entries=csv_rows(BATCH/"sites.tsv","\t")
    matrix=csv_rows(args.stage24_dir/"ten_site_science_gate_matrix.csv")
    events=csv_rows(args.stage24_dir/"ranked_timestamp_context.csv")
    edits=csv_rows(args.stage24_dir/"qc0_measurement_edits_for_manual_decision.csv")
    sites={r["site"]:r for r in entries}
    matrix_site={r["site"]:r for r in matrix}
    if len(sites)!=10 or len(matrix)!=10 or set(sites)!=set(matrix_site):
        raise RuntimeError("10-site pinned manifest/Stage24 matrix mismatch")
    if len(edits)!=518 or len(events)!=41104:
        raise RuntimeError("Selected Stage24 snapshot counts changed")
    if sum(int(float(x["positive_RH_below1"])) for x in matrix)!=27:
        raise RuntimeError("Stage24 low-positive RH counts differ")
    checks={}
    for r in entries:
        site=r["site"]
        paths=get_input_locations(r,args.sites_root,args.stage18_root,args.stage20_root)
        for path in paths:
            if not path.is_file():raise RuntimeError("Missing pinned "+site+": "+str(path))
        checks[site]=paths
        print("CHECK OK %-7s %s" %(site,paths[2].parent.parent.parent.name),flush=True)
    print("STAGE25 PREFLIGHT 10/10 original+ERA+QCv5; 518 QC0 edits;"
          " 41104 source-review timestamps.",flush=True)
    if args.check:
        print("CHECK ONLY; no repairs or reports written.")
        return

    rows_by_site=defaultdict(list)
    for r in events:rows_by_site[r["site"]].append(r)
    qc0_by_site=defaultdict(list)
    for r in edits:qc0_by_site[r["site"]].append(r)
    total_review=[];total_context=[];qc0_review=[];summary=[];class_counts=Counter()
    step=int(2*args.context_hours)
    for r in entries:
        site=r["site"];first=int(r["first_year"]);last=int(r["last_year"])
        src,comp,forc=checks[site]
        original=parse_met(src,SOURCES,first,last,True)
        era=parse_met(comp,ERA,first,last,True)
        candidate=parse_met(forc,CANDIDATE,first,last,False)
        if not (np.array_equal(original.time.to_numpy(),era.time.to_numpy()) and
                np.array_equal(original.time.to_numpy(),candidate.time.to_numpy())):
            raise RuntimeError(site+": sources/candidate not time aligned")
        stamps=candidate.time.dt.strftime("%Y-%m-%d %H:%M").to_numpy()
        idx={s:i for i,s in enumerate(stamps)}
        original_t=original.TA_F.to_numpy(float)
        original_v=original.VPD_F.to_numpy(float)
        new_t=candidate.TA_USE.to_numpy(float)
        new_v=candidate.VPD_USE.to_numpy(float)
        e_t=era.TA_ERA.to_numpy(float)
        e_v=era.VPD_ERA.to_numpy(float)
        rh0=calc_rh(original_t,original_v)
        rh=calc_rh(new_t,new_v)
        rhe=calc_rh(e_t,e_v)
        source_qct=original.TA_F_QC.to_numpy(float)
        source_qcv=original.VPD_F_QC.to_numpy(float)
        # Select only high-impact science flags, not all rainfall-only reviews.
        selected=set()
        for row in rows_by_site[site]:
            flags=set(filter(None,row["review_flags"].split("|")))
            if flags&SELECT_FLAGS:
                selected.add(row["timestamp_local"][:16])
        for row in qc0_by_site[site]:
            selected.add(row["timestamp_local"][:16])
        missing=selected-set(idx)
        if missing:
            raise RuntimeError(site+": review time not found "+str(sorted(missing)[:3]))
        original_event_flags={row["timestamp_local"][:16]:
            set(filter(None,row["review_flags"].split("|")))
            for row in rows_by_site[site]}
        event_rows=[]
        context_ix=set()
        for stamp in sorted(selected):
            i=idx[stamp]
            flags=original_event_flags.get(stamp,set())
            qct=source_qct[i];qcv=source_qcv[i]
            before=new_t[i-1] if i>0 else np.nan
            after=new_t[i+1] if i+1<len(new_t) else np.nan
            category,action=evidence_class(flags,rh0[i],rh[i],
                qct,qcv,new_t[i],e_t[i],original_t[i],before,after)
            class_counts[(site,category)]+=1
            record=dict(site=site,timestamp_local=stamp,
                        flags="|".join(sorted(flags)),
                        priority=category,scientific_next_action=action,
                        original_TA_C=scalar(original_t[i]),
                        candidate_TA_C=scalar(new_t[i]),
                        ERA_TA_C=scalar(e_t[i]),
                        candidate_minus_ERA_TA_C=scalar(new_t[i]-e_t[i]),
                        original_VPD_hPa=scalar(original_v[i]),
                        candidate_VPD_hPa=scalar(new_v[i]),
                        ERA_VPD_hPa=scalar(e_v[i]),
                        original_RH_pct=scalar(rh0[i]),
                        candidate_RH_pct=scalar(rh[i]),
                        ERA_RH_pct=scalar(rhe[i]),
                        original_TA_QC=scalar(qct),
                        original_VPD_QC=scalar(qcv),
                        candidate_QBOT=scalar(candidate.QBOT.iloc[i]),
                        prev_candidate_TA_C=scalar(before),
                        next_candidate_TA_C=scalar(after),
                        before_TA_30min_delta_C=scalar(new_t[i]-before),
                        after_TA_30min_delta_C=scalar(after-new_t[i]),
                        source_companion_TA_equal=(
                            bool(np.isclose(original_t[i],e_t[i],atol=1e-6)) if
                            np.isfinite(original_t[i]) and np.isfinite(e_t[i]) else False),
                        source_companion_VPD_equal=(
                            bool(np.isclose(original_v[i],e_v[i],atol=1e-6)) if
                            np.isfinite(original_v[i]) and np.isfinite(e_v[i]) else False),
                        human_decision="HOLD_NOT_APPROVED",
                        validated_independent_ERA5_Land="NO")
            event_rows.append(record)
            context_ix.update(range(max(0,i-step),min(len(stamps),i+step+1)))
        total_review.extend(event_rows)
        # Context includes immediate +/- context, unique sorted indices.
        for i in sorted(context_ix):
            total_context.append(dict(
                site=site,timestamp_local=stamps[i],
                review_target=stamps[i] in selected,
                original_TA_C=scalar(original_t[i]),
                candidate_TA_C=scalar(new_t[i]),
                ERA_TA_C=scalar(e_t[i]),
                original_VPD_hPa=scalar(original_v[i]),
                candidate_VPD_hPa=scalar(new_v[i]),
                ERA_VPD_hPa=scalar(e_v[i]),
                original_TA_QC=scalar(source_qct[i]),
                original_VPD_QC=scalar(source_qcv[i]),
                original_RH_pct=scalar(rh0[i]),
                candidate_RH_pct=scalar(rh[i]),
                ERA_RH_pct=scalar(rhe[i])))
        perqc0=[]
        for row in qc0_by_site[site]:
            stamp=row["timestamp_local"][:16]
            i=idx[stamp]
            enriched=dict(row,
                          original_RH_pct=scalar(rh0[i]),
                          candidate_RH_pct=scalar(rh[i]),
                          original_TA_QC=scalar(source_qct[i]),
                          original_VPD_QC=scalar(source_qcv[i]),
                          ERA_TA_C=scalar(e_t[i]),
                          TA_candidate_minus_ERA_C=scalar(new_t[i]-e_t[i]),
                          original_humidity_nonphysical=bool(np.isfinite(rh0[i]) and rh0[i]<=0),
                          confidence="HOLD_FOR_MEASURED_QC0_EVIDENCE",
                          automatic_repair_authorized="NO")
            perqc0.append(enriched)
        qc0_review.extend(perqc0)
        summary.append(dict(site=site,
             selected_science_timepoints=len(event_rows),
             contextual_4h_records=len(context_ix),
             qc0_changed_variable_time_records=len(perqc0),
             original_nonphysical_humidity_among_QC0_edits=
                 sum(bool(x["original_humidity_nonphysical"]) for x in perqc0),
             source_rh_nonpositive_selected=int(sum(
                 np.isfinite(rh0[idx[t]]) and rh0[idx[t]]<=0 for t in selected)),
             candidate_rh_nonpositive_selected=int(sum(
                 np.isfinite(rh[idx[t]]) and rh[idx[t]]<=0 for t in selected)),
             original_QC0_science_state="HOLD_NOT_APPROVED",
             proposed_global_ERA_replacement="NONE"))
        print("  %-7s targets=%5d context=%5d QC0=%3d QC0_bad_source_RH=%3d"
              % (site,len(event_rows),len(context_ix),len(perqc0),
                 summary[-1]["original_nonphysical_humidity_among_QC0_edits"]),
              flush=True)
    if len(qc0_review)!=518:
        raise RuntimeError("QC0 ledger count after context analysis != 518")
    selected_by_site=Counter(row["site"] for row in total_review)
    for site in sites:
        if selected_by_site[site]!=next(x for x in summary if x["site"]==site)["selected_science_timepoints"]:
            raise RuntimeError("Selected events summary mismatch "+site)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage25_targeted_science_evidence_"+stamp)
    if out.exists():raise RuntimeError("Output already exists "+str(out))
    out.mkdir(parents=True,exist_ok=False)
    out_csv(out/"site_science_triage.csv",summary,list(summary[0]))
    out_csv(out/"all_518_QC0_evidence.csv",qc0_review,list(qc0_review[0]))
    out_csv(out/"selected_temporal_and_humidity_reviews.csv",
            total_review,list(total_review[0]))
    out_csv(out/"selected_context_plus_minus_4h.csv",
            total_context,list(total_context[0]))
    reason_rows=[dict(site=s,priority=k,timepoints=n) for (s,k),n in class_counts.items()]
    out_csv(out/"reason_priority_counts.csv",reason_rows,
            ["site","priority","timepoints"])
    print("\nSTAGE25 SUMMARY: stations=10; targeted_science_records=%d;"
          " QC0_evidence=518; expanded_context=%d"%
          (len(total_review),len(total_context)),flush=True)
    for level in ("P0_SOURCE_PHYSICS_QC0_CHANGED","P1_QC0_CHANGED",
                  "P1_ESLJU_STYLE_EXTREME_TA","P1_ITNOE_STYLE_TA_DISCONTINUITY",
                  "P1_CHAWS_STYLE_LOW_RH","P2_TA_ERA_DIVERGENCE"):
        print("  %-45s %d"%(level,sum(
            n for (site,cat),n in class_counts.items() if cat==level)),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("SCIENTIFIC GATE HOLD. This script makes NO automatic repairs.")
    print("ERA5 / QC2 provenance is not independent tower validation.")


if __name__=="__main__":
    main()

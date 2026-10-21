#!/usr/bin/env python3
"""Stage21: independent, read-only audit of all 10 AmeriFlux QCv5 candidate outputs.

Inputs:
  9 successful original-QCv5 candidates in the INCOMPLETE Stage18 trial;
  US-Bar in the separate, scientifically UNAPPROVED Stage20 sensitivity.
The Stage18 incomplete marker is EXPECTED and MUST NOT be removed here.

Validate noleap chronology, all seven converted forcing fields, QBOT computed
independently from TA_USE/VPD_USE/PSRF, source/event-level change provenance,
official source QC0 changes, residual RH bins, TA/PSRF half-hour jumps,
manual reviews, and source/candidate file SHA256. Fail closed on missing,
unlogged, duplicate or inconsistent changes. All QC/low RH screens are only
scientific review indicators; no automatic DATM/spinup approval.

Never modifies inputs. Writes ONLY small timestamped reports.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
HERE=Path(__file__).resolve().parents[2]
VARS=("TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
OUTPUT=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")
RANGES={"TBOT":(180,340),"QBOT":(0,0.08),"PSRF":(49000,111000),
        "FSDS":(0,1600),"FLDS":(0,800),"WIND":(0,75),
        "PRECTmms":(0,300/1800)}
CONVERSIONS={"TA_F":"TA_USE","VPD_F":"VPD_USE","PA_F":"PSRF",
             "SW_IN_F":"FSDS","LW_IN_F":"FLDS","WS_F":"WIND","P_F":"PRECTmms"}


def csv_rows(path, delimiter=","):
    with path.open("r",newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f,delimiter=delimiter))


def save(path, rows, columns):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()


def filename(site,first,last,trial):
    stem=f"{site}_CLM_forcing_{first}_{last}.csv"
    return trial/site/"forcing"/"processed_v5"/stem


def manifest():
    entries=csv_rows(HERE/"sites.tsv","\t")
    if len(entries)!=10 or len({r["site"] for r in entries})!=10:
        raise RuntimeError("Expected ten distinct pinned-release sites")
    return entries


def provenance_paths(site,base):
    qc=base/site/"forcing"/"qc_v5"
    return (qc/(site+"_replacement_events.csv"),
            qc/(site+"_manual_review.csv"),
            qc/(site+"_status.json"))


def read_header(path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        return next(csv.reader(f))


def exact_raw(entry,root):
    folder=root/entry["site"]/"forcing"/"raw"/entry["package"]
    matches=sorted(x for x in folder.glob("*.csv") if "FLUXMET_HH" in x.name.upper())
    if len(matches)!=1:
        raise RuntimeError("Expected exact pinned FLUXMET_HH in "+str(folder))
    return matches[0]


def read_series(path, cols, field="time"):
    frame=pd.read_csv(path,usecols=cols,
                      dtype={field:"string"},low_memory=False)
    if field=="TIMESTAMP_START":
        stamp=frame[field].str.strip().str.replace(r"\.0$","",regex=True)
        time=pd.to_datetime(stamp,format="%Y%m%d%H%M",errors="raise")
    else:
        time=pd.to_datetime(frame[field],format="%Y-%m-%d %H:%M:%S",errors="raise")
    frame=frame.drop(columns=[field])
    frame.insert(0,"time",time)
    for col in cols:
        if col==field:continue
        x=pd.to_numeric(frame[col],errors="coerce")
        frame[col]=x.where(np.isfinite(x) & (x>-9990))
    return frame


def valid_calendar(original,candidate,first,last):
    o=original.loc[original.time.dt.year.between(first,last)].copy()
    o=o.loc[~((o.time.dt.month==2)&(o.time.dt.day==29))].reset_index(drop=True)
    expected=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                           freq="30min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(o)!=len(expected) or len(candidate)!=len(expected):
        raise RuntimeError("NOLEAP source/candidate row count mismatch")
    if not np.array_equal(o.time.to_numpy(),expected.to_numpy()) or not np.array_equal(
            candidate.time.to_numpy(),expected.to_numpy()):
        raise RuntimeError("NOLEAP timestamp mismatch or duplicate/order issue")
    return o


def reconstructed_values(force):
    return {
        "TA_F":force["TA_USE"].to_numpy(dtype=float),
        "VPD_F":force["VPD_USE"].to_numpy(dtype=float),
        "PA_F":force["PSRF"].to_numpy(dtype=float)/1000,
        "SW_IN_F":force["FSDS"].to_numpy(dtype=float),
        "LW_IN_F":force["FLDS"].to_numpy(dtype=float),
        "WS_F":force["WIND"].to_numpy(dtype=float),
        "P_F":force["PRECTmms"].to_numpy(dtype=float)*1800,
    }


def flagged_step(values,ts,limit):
    gap=(np.diff(ts.to_numpy(dtype="datetime64[m]")).astype(
        "timedelta64[m]").astype("int64")==30)
    dv=np.abs(np.diff(values))
    return int((gap & np.isfinite(dv) & (dv>limit)).sum())


def inspect(entry,trial,rawroot,verify_hash):
    site=entry["site"];first=int(entry["first_year"]);last=int(entry["last_year"])
    forcing=filename(site,first,last,trial)
    events_file,review_file,status_file=provenance_paths(site,trial)
    raw=exact_raw(entry,rawroot)
    for p in (forcing,events_file,review_file,status_file):
        if not p.is_file():raise RuntimeError("Required file missing "+str(p))
    source_required={"TIMESTAMP_START"}|set(VARS)
    if not source_required.issubset(read_header(raw)):
        raise RuntimeError("Source missing original FLUXMET fields")
    required={"time"}|set(OUTPUT)
    if not required.issubset(read_header(forcing)):
        raise RuntimeError("Candidate forcing missing required DATM-prep fields")
    original=read_series(raw,["TIMESTAMP_START",*VARS],field="TIMESTAMP_START")
    force=read_series(forcing,["time",*OUTPUT])
    original=valid_calendar(original,force,first,last)
    candidate=reconstructed_values(force)
    n=len(force)
    anomalies=[]
    for v in OUTPUT:
        if not np.isfinite(force[v].to_numpy(dtype=float)).all():
            anomalies.append("NONFINITE_FINAL_"+v)
    for col,(lo,hi) in RANGES.items():
        x=force[col].to_numpy(dtype=float)
        if (np.isfinite(x)&((x<lo)|(x>hi))).any():
            anomalies.append("RANGE_FINAL_"+col)
    ta=candidate["TA_F"];vpd=candidate["VPD_F"]
    pa=force["PSRF"].to_numpy(dtype=float)
    with np.errstate(all="ignore"):
        es=6.112*np.exp(np.clip(17.67*ta/(ta+243.5),-40,40))
        ea=(es-vpd)*100
        q=.622*ea/(pa-.378*ea)
        rh=100*(es-vpd)/es
    qrecord=force["QBOT"].to_numpy(dtype=float)
    inconsistent=np.isfinite(q)&np.isfinite(qrecord)&(
        ~np.isclose(q,qrecord,rtol=1e-6,atol=1e-10))
    if inconsistent.any():
        anomalies.append("QBOT_RECONSTRUCTION_MISMATCH_"+str(int(inconsistent.sum())))
    rh_bad=np.isfinite(rh)&(rh<=0)
    qbad=np.isfinite(q)&((q<0)|(q>.08))
    if rh_bad.any():anomalies.append("EA_NONPOSITIVE_"+str(int(rh_bad.sum())))
    if qbad.any():anomalies.append("QBOT_OUTSIDE_PHYSICAL_"+str(int(qbad.sum())))
    if ((es-vpd)<0).any():
        anomalies.append("NEGATIVE_VAPOUR_PRESSURE")
    changed={}
    row_changed=0
    for v in VARS:
        a=original[v].to_numpy(dtype=float)
        b=candidate[v]
        changed[v]=~np.isclose(a,b,atol=1e-6,rtol=1e-8,equal_nan=True)
        row_changed+=int(changed[v].sum())
    events=csv_rows(events_file)
    reviews=csv_rows(review_file)
    with status_file.open(encoding="utf-8") as f:status=json.load(f)
    if status.get("site")!=site or status.get("status") not in ("PASS","REVIEW"):
        anomalies.append("SITE_STATUS_NOT_PASS_REVIEW")
    if int(status.get("changes",-1))!=len(events):
        anomalies.append("STATUS_VS_EVENT_COUNT_MISMATCH")
    if int(status.get("manual_review_records",-1))!=len(reviews):
        anomalies.append("STATUS_VS_MANUAL_COUNT_MISMATCH")
    if len(events)!=row_changed:
        anomalies.append("RAW_VS_EVENT_DIFFERENCE_"+str(row_changed-len(events)))
    expected_by_var=Counter()
    qc0_events=0
    origin=Counter()
    reason=Counter()
    failed_events=[]
    seen=set()
    parsed_time={t.strftime("%Y-%m-%d %H:%M:%S"):i
                 for i,t in enumerate(force.time)}
    for event in events:
        var=event.get("variable")
        ts=str(event.get("time",""))
        ts=ts.replace("T"," ")[:19]
        key=(ts,var)
        if key in seen:failed_events.append("DUPLICATE_EVENT:"+str(key))
        seen.add(key)
        expected_by_var[var]+=1
        qc=str(event.get("official_qc","")).strip()
        if qc in ("0","0.0"):qc0_events+=1
        origin[event.get("final_source","")] +=1
        reason[event.get("reason","")] +=1
        if var not in VARS or ts not in parsed_time:
            failed_events.append("UNKNOWN_EVENT:"+str(key))
            continue
        index=parsed_time[ts]
        if not changed[var][index]:
            failed_events.append("UNMODIFIED_LOG_EVENT:"+str(key))
        val=event.get("final_value")
        try:
            event_value=float(val)
        except (ValueError,TypeError):
            failed_events.append("NONNUMERIC_EVENT:"+str(key));continue
        if not np.isclose(event_value,candidate[var][index],atol=1e-6,rtol=1e-8):
            failed_events.append("EVENT_FINAL_DIFFERS_FROM_FORCING:"+str(key))
    if failed_events:
        anomalies.append("EVENT_RECONCILIATION_FAILED_"+str(len(failed_events)))
    for v in VARS:
        if expected_by_var[v]!=int(changed[v].sum()):
            anomalies.append("EVENT_VAR_COUNT_MISMATCH_"+v)
    statusvalue="AUDIT_NUMERIC_OK_SCIENCE_REVIEW" if not anomalies else "AUDIT_FAIL"
    flags=dict(
        site=site,original_algorithm=("STAGE20_THREE_TIME_SENSITIVITY" if site=="US-Bar"
                                     else "STAGE18_ORIGINAL_QCV5"),
        source_range=f"{first}-{last}",noleap_halfhours=n,
        status=statusvalue,source_qc_v5_status=status.get("status"),
        changed_variable_records=row_changed,
        logged_replacements=len(events),
        manual_review_records=len(reviews),
        changed_QC0_measured=qc0_events,
        source_events_ERA_replacement=origin["secondary_era_replacement"],
        source_events_short_interpolation=origin["local_short_interpolation"],
        source_events_reconstructed_rh=origin["era_rh_reconstructed_at_tower_TA"],
        residual_RH_le_zero=int(rh_bad.sum()),
        positive_RH_lt1=int((np.isfinite(rh)&(rh>0)&(rh<1)).sum()),
        positive_RH_1to5=int((np.isfinite(rh)&(rh>=1)&(rh<5)).sum()),
        positive_RH_5to10=int((np.isfinite(rh)&(rh>=5)&(rh<10)).sum()),
        final_RH_min=float(np.nanmin(rh)),
        final_RH_max=float(np.nanmax(rh)),
        final_QBOT_min=float(np.nanmin(qrecord)),
        final_QBOT_max=float(np.nanmax(qrecord)),
        TA_30min_step_gt8=flagged_step(ta,force.time,8),
        PSRF_30min_step_gt5000Pa=flagged_step(pa,force.time,5000),
        site_trial_path=str(trial),
        source_FLUXMET_path=str(raw),
        forcing_path=str(forcing),
        flagged_issues=";".join(anomalies),
        numerical_gate=("FAIL" if anomalies else "PASS"),
        science_gate="HOLD_NOT_APPROVED",
        ERA5_Land_independent="NOT_VERIFIED",
        ZBOT="NOT_VERIFIED",
        surface_PFT="NOT_SCIENCE_APPROVED")
    sha=[]
    if verify_hash:
        sha=[{"site":site,"file_kind":"pinned_FLUXMET","file":str(raw),"sha256":digest(raw)},
             {"site":site,"file_kind":"qcv5_candidate","file":str(forcing),"sha256":digest(forcing)},
             {"site":site,"file_kind":"replacement_events","file":str(events_file),"sha256":digest(events_file)}]
    qc_detail=[dict(site=site,reason=name,events=n) for name,n in reason.most_common()]
    return flags,qc_detail,sha,failed_events[:30]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage18-root",type=Path,required=True)
    p.add_argument("--stage20-root",type=Path,required=True)
    p.add_argument("--sites-root",type=Path,default=ROOT)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--audit",action="store_true")
    p.add_argument("--skip-sha256",action="store_true",help="Skip full file hashes")
    args=p.parse_args()
    m=manifest()
    old=args.stage18_root.expanduser().resolve()
    bar=args.stage20_root.expanduser().resolve()
    root=args.sites_root.expanduser().resolve()
    if not old.is_dir() or not bar.is_dir() or old==bar:
        raise RuntimeError("Stage18 and Stage20 must be distinct, existing directories")
    if not (old/"qc_v5_adaptation_run_summary.csv").is_file():
        raise RuntimeError("Stage18 adaptation summary missing")
    stage18=csv_rows(old/"qc_v5_adaptation_run_summary.csv")
    states={r["site"]:r["status"] for r in stage18}
    if len(stage18)!=10 or set(states)!={r["site"] for r in m}:
        raise RuntimeError("Stage18 batch summary missing or duplicate sites")
    if states.get("US-Bar")!="FAIL":
        raise RuntimeError("Expected US-Bar blocked in Stage18, select actual matching trial")
    if any(states.get(r["site"]) not in ("PASS","REVIEW")
           for r in m if r["site"]!="US-Bar"):
        raise RuntimeError("Stage18 nine-station statuses not PASS/REVIEW")
    if not (bar/"COMPLETE_SENSITIVITY_NOT_SCIENCE_APPROVED").is_file():
        raise RuntimeError("Stage20 complete sensitivity marker missing")
    selected=[]
    for r in m:
        site=r["site"]
        chosen=bar if site=="US-Bar" else old
        needed=[
            filename(site,int(r["first_year"]),int(r["last_year"]),chosen),
            *provenance_paths(site,chosen),
            exact_raw(r,root),
        ]
        for f in needed:
            if not f.is_file():
                raise RuntimeError("Missing pinned Stage21 input: "+str(f))
        selected.append((r,chosen))
        print("CHECK OK %-7s candidate=%s" % (site,chosen),flush=True)
    print("STAGE21 PREFLIGHT: %d/10 candidates, nine from Stage18,"
          " one from Stage20" % len(selected),flush=True)
    print("Stage18 INCOMPLETE marker is EXPECTED; this script never clears it.")
    if args.check:
        print("CHECK ONLY; no new data written.")
        return
    results=[];reasons=[];hashes=[];event_failures=[]
    for r,chosen in selected:
        print("AUDIT",r["site"],flush=True)
        try:
            stats,site_reasons,site_hashes,fail=inspect(
                r,chosen,root,not args.skip_sha256)
            results.append(stats)
            reasons.extend(site_reasons)
            hashes.extend(site_hashes)
            event_failures.extend([{"site":r["site"],"issue":x} for x in fail])
            print("  %-7s numeric=%-5s modifications=%4d logged=%4d"
                  " reviews=%4d QC0_changes=%4d RH<=0=%d RH<1pos=%d" %
                  (r["site"],stats["numerical_gate"],
                   stats["changed_variable_records"],
                   stats["logged_replacements"],
                   stats["manual_review_records"],
                   stats["changed_QC0_measured"],
                   stats["residual_RH_le_zero"],
                   stats["positive_RH_lt1"]),flush=True)
        except Exception as exc:
            print("  AUDIT FAILURE",r["site"],repr(exc),flush=True)
            results.append(dict(site=r["site"],status="AUDIT_FAIL",
                                numerical_gate="FAIL",flagged_issues=repr(exc),
                                science_gate="HOLD_NOT_APPROVED"))
    out=args.report_root/("stage21_ten_site_post_qcv5_"+datetime.now(
         timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    out.mkdir(parents=True,exist_ok=False)
    save(out/"site_independent_numeric_and_science_gates.csv",
         results,list(dict.fromkeys(k for x in results for k in x)))
    save(out/"replacement_reasons_by_site.csv",reasons,
         ["site","reason","events"])
    save(out/"source_candidate_sha256_manifest.csv",hashes,
         ["site","file_kind","file","sha256"])
    save(out/"replacement_event_mismatch_examples.csv",event_failures,
         ["site","issue"])
    failed=[r["site"] for r in results if r["numerical_gate"]!="PASS"]
    print("\nSTAGE21 SUMMARY: candidate sites=%d numeric_PASS=%d FAIL=%d" %
          (len(results),len(results)-len(failed),len(failed)),flush=True)
    for key in ("changed_variable_records","logged_replacements",
                "manual_review_records","changed_QC0_measured",
                "residual_RH_le_zero","positive_RH_lt1"):
        print("  TOTAL %-34s %d" %
              (key,sum(int(r.get(key,0)) for r in results if r.get(key) is not None)),flush=True)
    if failed:
        print("FAILED:",", ".join(failed),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("READ ONLY. NO source or candidate changes; no complete combined"
          " forcing, no DATM, ZBOT or spinup.")
    print("Numerical PASS does not approve QC0 changes, US-Bar RH floor,"
          " winter low-RH, PFT or ZBOT.",flush=True)
    return 2 if failed else 0


if __name__=="__main__":
    raise SystemExit(main())

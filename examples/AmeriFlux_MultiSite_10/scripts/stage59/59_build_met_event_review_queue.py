#!/usr/bin/env python3
"""Stage59 - site-specific, evidence-first Batch01 meteorology review queue.

Uses Stage58's EXACT 10 selected candidates. --check is strictly read-only.
--audit writes ONLY new, timestamped reports. No forcing replacement, QC edits,
DATM, CIME, surface, PFT, model or Slurm actions. All events are REVIEW FLAGS;
not evidence of an error. FLUXNET ERA5_HH is not independent ground truth.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import runpy
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

STAGE58 = Path(__file__).resolve().parents[1] / "stage58" / "58_audit_selected_forcing_candidates.py"
EXPERIMENT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
RAW_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
MANIFEST = Path(__file__).resolve().parents[2] / "sites.tsv"
SELECTED_HASHES = {
    "BR-Ma2": "b99fd5e2d8953d23df1b7421630fa0ec36b8ff6796580fe05e206b61fca8a462",
    "CA-Ca3": "fe2fc8f9d1671cfde3b59a1de4c7e4e07e53f27f4640b4fa4231bd43102d4810",
    "CA-Cbo": "9549891a920b2992b6017b0f0d5fb35dc666c3c531cec15fe4333da3a36ae954",
    "CA-LP1": "75c27b07875b70b640cadbafb0ef453dd409edfb4c151059621cb0ce4727eb09",
    "CA-Man": "fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705",
    "CA-TP1": "8658c172c50474548eefb72be2648f028f646281b0b4b432aeb4457d57a4d0a3",
    "CA-TP3": "080b09e3a2bc5fb56a38d10af18406e336a7d6c9c16a85ffc6b0a9ba8865430f",
    "CA-TP4": "2cf0e04babe3369b9dc0b98a35d3aae3c9064f913c75e4d023f39de072756e5a",
    "US-Aud": "8d2e62b7f474f304966feab37f2d6c6cd89621ef9e88ea411e46692721a28b9a",
    "US-Bar": "b4cbdbbee716d246e4b4fb12c6ce465bc57f12a07fc15b519d75e53c5accce6a",
}
EXPECTED_RH = {"BR-Ma2":0, "CA-Ca3":7, "CA-Cbo":2, "CA-LP1":0,
               "CA-Man":1, "CA-TP1":0, "CA-TP3":0, "CA-TP4":0,
               "US-Aud":0, "US-Bar":8}
EXPECTED_JUMP = {"BR-Ma2":0, "CA-Ca3":5, "CA-Cbo":31, "CA-LP1":37,
                 "CA-Man":185, "CA-TP1":11, "CA-TP3":11, "CA-TP4":14,
                 "US-Aud":22, "US-Bar":106}
RISK_TIME = datetime(2007,7,3,20)
FIELDNAMES = ["site","event_type","timestamp","priority","review_scope",
              "event_class","temperature_C","RH_percent","QBOT","PSRF",
              "VPD_USE","delta_T_C","next_delta_T_C","recovered_C",
              "episode_id","source_FLUXMET_TA_F_C","source_FLUXMET_TA_QC",
              "source_FLUXMET_VPD_F_hPa","source_ERA5_TA_ERA_C",
              "source_ERA5_VPD_ERA_hPa","source_alignment",
              "recommendation"]

def numeric(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (TypeError,ValueError):
        return None

def stamp(x):
    return datetime.fromisoformat(str(x).strip())

def details(row):
    tk,q,p = (numeric(row.get(x)) for x in ("TBOT","QBOT","PSRF"))
    if None in (tk,q,p) or not (180 < tk < 340 and 0 < q < 0.05 and 50000 < p < 120000):
        raise ValueError("Invalid core meteorology at " + str(row.get("time")))
    tc=tk-273.15
    es=6.112*math.exp(17.67*tc/(tc+243.5))
    e=q*(p/100)/(0.622+0.378*q)
    return tc,100*e/es

def read_sites():
    with MANIFEST.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    names=[r["site"] for r in rows]
    if len(rows)!=10 or set(names)!=set(SELECTED_HASHES):
        raise RuntimeError("Ten-site manifest mismatch")
    return {r["site"]:r for r in rows}

def locate_source(rawroot,site,package,kind):
    folder=rawroot/site/"forcing"/"raw"/package
    options=sorted(x for x in folder.glob("*.csv") if kind in x.name.upper())
    return options[0] if len(options)==1 else None

def obtain_source(path, stamps, columns):
    if path is None: return {}, "SOURCE_NOT_UNIQUE_OR_MISSING"
    matched={}
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if "TIMESTAMP_START" not in (reader.fieldnames or []):
            return {}, "SOURCE_NO_TIMESTAMP_START"
        for row in reader:
            key=(row.get("TIMESTAMP_START") or "").strip().removesuffix(".0")
            if key in stamps:
                if key in matched:
                    raise RuntimeError("Duplicate source time "+str(path)+" "+key)
                matched[key]={c:row.get(c,"") for c in columns}
    return matched, "EXACT_TIMESTAMP_START_MATCH_ONLY_CLOCK_UNVERIFIED"

def scan_events(path,site):
    events=[]
    prior_time=None
    prior_tc=None
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        required={"time","TBOT","QBOT","PSRF","VPD_USE"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError("Missing forcing columns: "+str(path))
        for row in reader:
            t=stamp(row["time"])
            tc,rh=details(row)
            base={"site":site,"timestamp":t.strftime("%Y-%m-%d %H:%M:%S"),
                  "temperature_C":round(tc,5),"RH_percent":round(rh,6),
                  "QBOT":row["QBOT"],"PSRF":row["PSRF"],
                  "VPD_USE":row["VPD_USE"],"_time":t}
            if 0 < rh < 1:
                accepted=site=="CA-Man" and t==RISK_TIME
                event=dict(base,event_type="RH_LT1",
                           event_class="ACCEPTED_RISK_RECHECK" if accepted else "LOW_RH_MANUAL",
                           review_scope="MANUAL_1_EVENT",priority="P2_EXISTING_RISK" if accepted else "P0_HUMIDITY",
                           recommendation=("Preserve documented decision; recheck scientific support" if accepted
                                           else "Check exact source TA/VPD/PA, QC, time alignment; do not blanket-floor RH"))
                events.append(event)
            if prior_time is not None and t-prior_time==timedelta(minutes=30):
                delta=tc-prior_tc
                if abs(delta)>10:
                    event=dict(base,event_type="TA_STEP_GT10",
                               delta_T_C=round(delta,5),_previous_temp=prior_tc,
                               event_class="UNCLASSIFIED",
                               priority="P1_TEMPERATURE",
                               review_scope="BATCH_EPISODE",
                               recommendation="Inspect paired reversals, QC/source switches, independent evidence before repair")
                    events.append(event)
            prior_time,prior_tc=t,tc
    return events

def context_and_rebounds(path,events,hours):
    stamps=set()
    for event in events:
        t=event["_time"]
        for half_hour in range(-2*hours,2*hours+1):
            p=t+timedelta(minutes=30*half_hour)
            if p.month==2 and p.day==29:
                continue
            stamps.add(p)
    context={}
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        for row in reader:
            t=stamp(row["time"])
            if t in stamps:
                tc,rh=details(row)
                context[t]={"temperature_C":round(tc,5),"RH_percent":round(rh,6),
                            "QBOT":row["QBOT"],"PSRF":row["PSRF"],
                            "VPD_USE":row.get("VPD_USE","")}
    for event in events:
        if event["event_type"]!="TA_STEP_GT10":continue
        t=event["_time"]
        nxt=context.get(t+timedelta(minutes=30))
        if nxt is None:
            event["event_class"]="NO_NEXT_CONTEXT"
            continue
        current=float(event["temperature_C"])
        delta=float(event["delta_T_C"])
        rebound=float(nxt["temperature_C"])-current
        event["next_delta_T_C"]=round(rebound,5)
        previous=float(event["_previous_temp"])
        recovery=abs(float(nxt["temperature_C"])-previous)
        event["recovered_C"]=round(recovery,5)
        if delta*rebound<0 and abs(rebound)>=0.7*abs(delta) and recovery<=5:
            event["event_class"]="RAPID_REVERSAL_CANDIDATE"
        else:
            event["event_class"]="SUSTAINED_OR_UNRESOLVED_STEP"
    return context

def episode_ids(events):
    ordered=sorted(events,key=lambda e:(e["site"],e["event_type"],e["_time"]))
    previous={}
    n=Counter()
    for e in ordered:
        key=e["site"],e["event_type"]
        t=e["_time"]
        if key not in previous or t-previous[key]>timedelta(hours=2):
            n[key]+=1
        e["episode_id"]=f"{e['site']}_{e['event_type']}_{n[key]:04d}"
        previous[key]=t

def save_csv(path,records,fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    ap.add_argument("--experiment-root",type=Path,default=EXPERIMENT)
    ap.add_argument("--raw-root",type=Path,default=RAW_ROOT)
    ap.add_argument("--context-hours",type=int,default=4)
    args=ap.parse_args()
    if args.context_hours<1 or args.context_hours>12:
        ap.error("context-hours must be between 1 and 12")
    if not STAGE58.is_file():raise SystemExit("Missing Stage58 dependency: "+str(STAGE58))
    m58=runpy.run_path(str(STAGE58))
    root=args.experiment_root.resolve(strict=True)
    paths=m58["file_list"]()
    stations=read_sites()
    for site in SELECTED_HASHES:
        p=root/paths[(site,"selected")]
        if not p.is_file() or not p.resolve().is_relative_to(root):
            raise SystemExit("Missing or outside experiment: "+str(p))
        print("FOUND",site,p,flush=True)
    ledger=root/"stage56_batch01_met_triage/CA-Man_2007_accepted_risk.json"
    if not ledger.is_file():raise SystemExit("Missing Stage56 risk ledger")
    risk=json.loads(ledger.read_text(encoding="utf-8"))
    if (risk.get("site"),risk.get("timestamp"),risk.get("decision"),
        risk.get("candidate_sha256"))!=(
        "CA-Man","2007-07-03 20:00:00","ACCEPTED_RISK",SELECTED_HASHES["CA-Man"]):
        raise SystemExit("Stage56 risk evidence mismatch")
    if args.check:
        print("CHECK PASS: ten pinned candidates and CA-Man risk ledger present; NOTHING WRITTEN.")
        return
    all_events=[]
    contexts=[]
    provenance={}
    summary={}
    for site in SELECTED_HASHES:
        p=root/paths[(site,"selected")]
        digest=m58["sha256"](p)
        if digest!=SELECTED_HASHES[site]:
            raise SystemExit("STOP SHA mismatch "+site+" "+digest)
        events=scan_events(p,site)
        counts=Counter(e["event_type"] for e in events)
        if (counts["RH_LT1"],counts["TA_STEP_GT10"])!=(EXPECTED_RH[site],EXPECTED_JUMP[site]):
            raise SystemExit(f"STOP Stage58 event count mismatch {site}: {dict(counts)}")
        context=context_and_rebounds(p,events,args.context_hours)
        source_map={}
        target_stamps={t.strftime("%Y%m%d%H%M") for t in context}
        for kind,cols in (
            ("FLUXMET_HH",("TA_F","TA_F_QC","VPD_F")),
            ("ERA5_HH",("TA_ERA","VPD_ERA"))
        ):
            source=locate_source(args.raw_root,site,stations[site]["package"],kind)
            matched,status=obtain_source(source,target_stamps,cols)
            source_map[kind]=(matched,status)
            provenance[kind+"_"+site]={"path":str(source) if source else "NOT_FOUND",
                                      "match_count":len(matched),"status":status}
        for e in events:
            key=e["_time"].strftime("%Y%m%d%H%M")
            flux,fs=source_map["FLUXMET_HH"]
            era,es=source_map["ERA5_HH"]
            q=flux.get(key,{})
            w=era.get(key,{})
            e.update(source_FLUXMET_TA_F_C=q.get("TA_F",""),
                     source_FLUXMET_TA_QC=q.get("TA_F_QC",""),
                     source_FLUXMET_VPD_F_hPa=q.get("VPD_F",""),
                     source_ERA5_TA_ERA_C=w.get("TA_ERA",""),
                     source_ERA5_VPD_ERA_hPa=w.get("VPD_ERA",""),
                     source_alignment=("EXACT_START_ONLY_NOT_VALIDATED"
                                       if q or w else "NO_SOURCE_EXACT_MATCH"))
            all_events.append(e)
        tagged={e["_time"] for e in events}
        for t,val in sorted(context.items()):
            contexts.append(dict(site=site,timestamp=t.strftime("%Y-%m-%d %H:%M:%S"),
                                 flagged_at_time="YES" if t in tagged else "NO",**val))
        summary[site]={
            "low_rh":counts["RH_LT1"],
            "ta_step_gt10":counts["TA_STEP_GT10"],
            "rapid_reversal_step_flags":sum(e["event_class"]=="RAPID_REVERSAL_CANDIDATE" for e in events),
            "selected_sha256":digest,
            "selected_path":str(paths[(site,"selected")]),
        }
        print("SITE",site,"RH",counts["RH_LT1"],"TA",counts["TA_STEP_GT10"],
              "REVERSAL",summary[site]["rapid_reversal_step_flags"],flush=True)
    episode_ids(all_events)
    all_events.sort(key=lambda e:(e["site"],e["_time"],e["event_type"]))
    if (sum(e["event_type"]=="RH_LT1" for e in all_events),
        sum(e["event_type"]=="TA_STEP_GT10" for e in all_events))!=(18,422):
        raise SystemExit("STOP unexpected 10-site counts")
    dest=root/"reports"/("stage59_met_event_review_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if not dest.parent.is_dir():
        raise SystemExit("Missing reports directory; refusing to create experiment structure")
    dest.mkdir(exist_ok=False)
    save_csv(dest/"all_flagged_events.csv",all_events,FIELDNAMES)
    save_csv(dest/"event_context_4h.csv",contexts,
             ["site","timestamp","flagged_at_time","temperature_C","RH_percent","QBOT","PSRF","VPD_USE"])
    review=[e for e in all_events if e["event_type"]=="RH_LT1"]
    save_csv(dest/"manual_low_rh_review.csv",review,FIELDNAMES)
    bulk=[e for e in all_events if e["event_type"]=="TA_STEP_GT10"]
    save_csv(dest/"bulk_temperature_review.csv",bulk,FIELDNAMES)
    (dest/"manifest.json").write_text(json.dumps({
        "stage":"59","science_gate":"HOLD_NOT_APPROVED","input_provenance":provenance,
        "selected_candidates":summary,"low_rh_total":18,"low_rh_unaccepted":17,
        "ta_step_total":422,"CA-Man_risk_ledger_sha256":m58["sha256"](ledger),
        "source_timestamp_alignment":"PROVISIONAL",
        "auto_repair_performed":False,
        "report_files":["all_flagged_events.csv","event_context_4h.csv",
                        "manual_low_rh_review.csv","bulk_temperature_review.csv"]
    },indent=2)+"\n",encoding="utf-8")
    print("REPORT:",dest)
    print("RH 18 including CA-Man documented risk; remaining manual scientific review 17.")
    print("TA 422 flags grouped by episodes; paired reversals are SUSPICIONS only.")
    print("Only new reports written; NO forcing/model/source changes or Slurm jobs.")

if __name__=="__main__":
    main()

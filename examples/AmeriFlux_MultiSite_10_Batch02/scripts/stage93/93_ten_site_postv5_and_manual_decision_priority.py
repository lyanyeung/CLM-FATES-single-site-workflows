#!/usr/bin/env python3
"""Batch02 Stage93 — REAL unified Post-v5 science/source review for all 10.

Read exact Stage87 117 NC and Stage92 98 NC candidate manifests, all raw
FLUXNET primary and independent ERA companions, and exact Stage07/Stage92
source-variable event ledgers. Import original Stage09 science_review for
uniform 10-site post-v5 extremes/source flags; derive full, grouped original
QC0 variable edits, native neighbor evidence and high-priority manual queues.
No science approval, no source/forcing/NetCDF/CIME/Slurm changes.
"""
import argparse,csv,hashlib,importlib.util,json,math,re,sys
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timedelta,timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
S87=ROOT/"reports/stage87_five_site_DATM_NetCDF_technical_preview_20261026T003934Z_30692f63"
S92=ROOT/"reports/stage92_five_site_complete_forcing_candidates_20261026T023951Z_ca1243de"
READY=("US-BZS","US-CMW","US-Ha1","US-Ho2","US-Ho3")
FIVE=("US-EML","US-GLE","US-Ho1","US-ICh","US-ICt")
YEAR_COUNTS={"US-BZS":15,"US-CMW":21,"US-Ha1":35,"US-Ho2":27,"US-Ho3":19,
             "US-EML":16,"US-GLE":16,"US-Ho1":28,"US-ICh":19,"US-ICt":19}
QC0_EXPECT={"US-BZS":1,"US-CMW":2,"US-Ha1":2,"US-Ho2":19,"US-Ho3":0,
            "US-EML":3,"US-GLE":0,"US-Ho1":5,"US-ICh":0,"US-ICt":90}
ALL_EXPECT=sum(QC0_EXPECT.values())
POST=Path(__file__).with_name("09_post_qcv5_batch02.py")
POST_BLOB="b2353089ff15b95b6a25c5c0e2fcf4e7be2671c7"
KEY_FIELDS=("TA_F","VPD_F","LW_IN_F")
EPS=1e-9

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()
def blob(p):
    b=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def loadj(p):return json.loads(Path(p).read_text())
def isofmt(v):return str(pd.Timestamp(v))
def n(v):
    try:
        val=float(v)
        return val if math.isfinite(val) and val>-9990 else float("nan")
    except (ValueError,TypeError):return float("nan")
def fmt(v):
    val=n(v)
    return "NA" if not math.isfinite(val) else ("%.5f"%val).rstrip("0").rstrip(".")
def keytime(value):
    digits=re.sub("[^0-9]","",str(value))
    if len(digits)<12:raise ValueError("Invalid source native clock "+str(value))
    return digits[:12]
def write_csv(path, rows, columns):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise ValueError("Cannot import pinned "+str(path))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def verify_inputs():
    if not POST.is_file() or blob(POST)!=POST_BLOB:
        raise ValueError("Stage09 original uniform post-v5 module Git blob missing/mismatch")
    original=loadj(S07/"exact_input_manifest.json")
    st07hash=loadj(S07/"output_sha256.json")
    info={x["site"]:x for x in original["sites"]}
    if set(info)!=set(YEAR_COUNTS) or not (S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").exists():
        raise ValueError("Original Stage07 exact 10-site manifest/marker changed")
    m87=loadj(S87/"manifest.json")
    m92=loadj(S92/"manifest.json")
    if (m87.get("netcdf_year_files")!=117 or m87.get("sites_built")!=5
        or m87.get("scientific_release") is not False
        or m92.get("annual_netcdf_preview_built")!=98
        or m92.get("complete_forcing_sites")!=5
        or m92.get("scientific_release") is not False
        or (S87/"INCOMPLETE_DO_NOT_USE").exists()
        or (S92/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").exists()):
        raise ValueError("Stage87/92 actual built ten-site preview state mismatch")
    h87={r["site"]:r for r in m87["sites"]}
    h92={r["site"]:r for r in m92["sites"]}
    if set(h87)!=set(READY) or set(h92)!=set(FIVE):
        raise ValueError("117+98 NetCDF site identities not disjoint as required")
    if sum(len(r["yearly_netcdf_files"]) for r in h87.values())!=117 or sum(
            len(r["netcdf_year_files"]) for r in h92.values())!=98:
        raise ValueError("NetCDF site/year count mismatch")
    issues=[]
    jobs=[]
    for site in sorted(YEAR_COUNTS):
        item=info[site]
        if item["native_minutes"]!=(60 if site=="US-Ha1" else 30):
            raise ValueError("Native source HH/HR interval drift "+site)
        first,last=int(item["first_year"]),int(item["last_year"])
        if last-first+1!=YEAR_COUNTS[site]:
            raise ValueError("Site-year source window drift "+site)
        for var in ("primary","era"):
            p=Path(item[var]).resolve()
            expected=original["input_sha256"].get(str(p))
            if not expected or sha(p)!=expected:
                raise ValueError("Original raw source changed: "+str(p))
        trial=S07 if site in READY else S92
        forcing=trial/site/"forcing/processed_v5"/f"{site}_CLM_forcing_{first}_{last}.csv"
        status=trial/site/"forcing/qc_v5"/f"{site}_status.json"
        events=trial/site/"forcing/qc_v5"/f"{site}_replacement_events.csv"
        if not all(p.is_file() for p in (forcing,status,events)):
            raise ValueError("Candidate source/event ledger absent: "+site)
        state=loadj(status)
        if (state["site"]!=site or state["noleap_rows"]!=YEAR_COUNTS[site]*(365*1440//item["native_minutes"])):
            raise ValueError("Candidate original native timeline/source status drift "+site)
        if site in READY:
            s=h87[site]
            if (str(Path(s["original_stage07_forcing"]).resolve())!=str(forcing.resolve())
                or sha(forcing)!=s["original_stage07_forcing_sha256"]):
                raise ValueError("117 NC Stage87 source forcing hash changed "+site)
            rkey=str(forcing.relative_to(S07))
            if st07hash.get(rkey)!=sha(forcing):
                raise ValueError("Preserved Stage07 original hash receipt changed "+site)
            ncs=s["yearly_netcdf_files"]
        else:
            s=h92[site]
            if not s.get("forcing_done") or not s.get("netcdf_done") or s.get("netcdf_years")!=YEAR_COUNTS[site]:
                raise ValueError("Stage92 candidate not complete: "+site)
            if str(Path(s["forcing_csv"]).resolve())!=str(forcing.resolve()):
                raise ValueError("Stage92 candidate forcing path not aligned "+site)
            ncs=s["netcdf_year_files"]
        if len(ncs)!=YEAR_COUNTS[site]:
            raise ValueError("Missing annual NC preview for "+site)
        for obj in ncs:
            y=int(obj["year"])
            if y<first or y>last or Path(obj["path"]).name!=str(y)+".nc":
                raise ValueError("NC year identity mismatch "+site)
            p=Path(obj["path"]).resolve()
            if not p.is_file() or sha(p)!=obj["sha256"]:
                raise ValueError("Annual NC checksum changed: "+str(p))
        if {int(z["year"]) for z in ncs}!=set(range(first,last+1)):
            raise ValueError("Annual NC missing or duplicate source year "+site)
        print("STAGE93 SOURCE CHECK PASS",site,"years",len(ncs),
            "native_minutes",item["native_minutes"],"status",state["status"],flush=True)
        jobs.append((site,item,trial,forcing,events))
    holds=S92/"source_row_holds_stage64_stage74.csv"
    if sha(holds)!=m92.get("source_row_holds_sha256") or m92.get("source_row_holds")!=2:
        raise ValueError("Exact two Stage92 invalid independent RH source HOLDs altered")
    if sum(YEAR_COUNTS.values())!=215 or ALL_EXPECT!=122:
        raise ValueError("Site-level year/QC0 expected census changed")
    print("STAGE93 VERIFY PASS | ten raw+ERA source pairs, 215 annual NC SHA, actual 10 forcing CSV")
    return jobs

def raw_neighbors(item,qc0):
    """Review exact original QC0 variable records, ±1 native observation each."""
    if qc0.empty:return []
    p=Path(item["primary"])
    columns=set(pd.read_csv(p,nrows=0).columns)
    use=["TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"]
    add=[v for v in KEY_FIELDS if v in columns]
    use=list(dict.fromkeys(k for k in use+add if k in columns))
    raw=pd.read_csv(p,usecols=use,dtype={"TIMESTAMP_START":str},low_memory=False)
    raw["key"]=raw["TIMESTAMP_START"].str.strip().str.replace(r"\\.0$","",regex=True)
    # Source raw chronology already source-audited at Stage07. Native prev/next
    # are accepted ONLY if their timestamps are exactly ±native interval.
    hits={}
    for i,k in enumerate(raw["key"]):
        if k in hits:raise ValueError("Original source duplicate native timestamp "+k)
        hits[k]=i
    rows=[]
    for r in qc0.to_dict("records"):
        stamp=keytime(r["time"])
        if stamp not in hits:raise ValueError("QC0 modification does not exist in original FLUXNET source "+stamp)
        k=hits[stamp]
        var=str(r["variable"])
        if var not in columns:raise ValueError("Changed QC0 field missing in raw "+var)
        observed=n(raw.at[k,var])
        before=after=float("nan")
        center=pd.to_datetime(stamp,format="%Y%m%d%H%M")
        native=int(item["native_minutes"])
        if k>0 and pd.to_datetime(raw.at[k-1,"key"],format="%Y%m%d%H%M")==center-timedelta(minutes=native):
            before=n(raw.at[k-1,var])
        if k+1<len(raw) and pd.to_datetime(raw.at[k+1,"key"],format="%Y%m%d%H%M")==center+timedelta(minutes=native):
            after=n(raw.at[k+1,var])
        old_t=n(raw.at[k,"TA_F"])
        old_v=n(raw.at[k,"VPD_F"])
        es=(6.112*math.exp(17.67*old_t/(old_t+243.5))
            if math.isfinite(old_t) and -80<old_t<65 else float("nan"))
        implied=(100*(es-old_v)/es if math.isfinite(es) and es>0 and math.isfinite(old_v) else float("nan"))
        final=n(r["final_value"])
        reference=n(r.get("era_reference"))
        delta=final-observed
        mid=(before+after)/2 if math.isfinite(before) and math.isfinite(after) else float("nan")
        original_isolated=(math.isfinite(mid) and math.isfinite(observed) and
                           abs(observed-mid)>=8 and abs(before-after)<6)
        if var=="TA_F":
            priority="P0_QC0_TEMPERATURE_CHANGED" if abs(delta)>=5 else "P1_QC0_TEMPERATURE_CHANGED"
        elif var=="VPD_F" and math.isfinite(implied) and implied<0:
            priority="P1_ORIGINAL_NEGATIVE_RH_VPD"
        elif var=="LW_IN_F" and original_isolated:
            priority="P2_LW_ISOLATED_NEIGHBOR_SUPPORTED"
        else:
            priority="P1_QC0_VALID_OR_UNCERTAIN_SOURCE_CHANGED"
        rows.append({
            "site":r["site"],"time":isofmt(r["time"]),"variable":var,
            "source_QC":"0","original_value":fmt(observed),
            "candidate_value":fmt(final),"delta":fmt(delta),
            "ERA_reference":fmt(reference),"raw_previous":fmt(before),
            "raw_next":fmt(after),"original_TA_C":fmt(old_t),
            "original_VPD_hPa":fmt(old_v),
            "original_implied_RH_pct":fmt(implied),
            "original_isolated_spike":str(original_isolated),
            "reason":r.get("reason",""),"candidate_source":r.get("final_source",""),
            "priority":priority,
            "operator_decision":"PENDING_REVIEW_NOT_PRODUCTION_APPROVED"})
    if len(rows)!=len(qc0):
        raise ValueError("QC0 edit native-neighbor count mismatch")
    return rows

def group_episodes(rows):
    """Group exact per-variable QC0 edits on uninterrupted native clock grid."""
    by=defaultdict(list)
    for r in rows:by[(r["site"],r["variable"])].append(r)
    episodes=[]
    for (site,var), records in sorted(by.items()):
        step=60 if site=="US-Ha1" else 30
        records.sort(key=lambda x:x["time"])
        groups=[]; current=[]
        for record in records:
            t=pd.Timestamp(record["time"])
            if current and t-pd.Timestamp(current[-1]["time"])!=timedelta(minutes=step):
                groups.append(current);current=[]
            current.append(record)
        if current:groups.append(current)
        for group in groups:
            severity=min([x["priority"] for x in group]) # P0 first, then P1, P2
            max_change=max(abs(n(x["delta"])) for x in group)
            keyreasons=dict(Counter(x["reason"] for x in group))
            episodes.append({
                "site":site,"variable":var,"first":group[0]["time"],
                "last":group[-1]["time"],"native_records":len(group),
                "max_abs_change":fmt(max_change),
                "priority":severity,
                "raw_negative_RH_count":sum(n(x["original_implied_RH_pct"])<0 for x in group),
                "isolated_spikes":sum(x["original_isolated_spike"]=="True" for x in group),
                "reasons":";".join(f"{k}:{v}" for k,v in keyreasons.items()),
                "human_decision":"PENDING (approve exact replacement / keep source / alternate source)",
                "production_DATM_allowed":"NO"})
    order={"P0":0,"P1":1,"P2":2}
    episodes.sort(key=lambda x:(order.get(x["priority"][:2],3),-x["native_records"],
                                x["site"],x["first"]))
    return episodes

def ho1_boundary(item,forcing):
    raw=Path(item["primary"])
    columns=set(pd.read_csv(raw,nrows=0).columns)
    selected=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    if not set(selected).issubset(columns):
        raise ValueError("Ho1 original source boundary field missing")
    d=pd.read_csv(raw,usecols=selected,dtype={"TIMESTAMP_START":str})
    d["t"]=d["TIMESTAMP_START"].str.strip().str.replace(r"\\.0$","",regex=True)
    ff=pd.read_csv(forcing,usecols=["time","TA_USE","VPD_USE","TBOT","QBOT"])
    ff["key"]=ff["time"].str.replace(r"[^0-9]","",regex=True).str[:12]
    chosen=["200012270800","200012270830","200012270900",
            "200012270930","200012271000","200012271030",
            "200012312330","200101010000"]
    a=d.loc[d.t.isin(chosen)].set_index("t")
    b=ff.loc[ff.key.isin(chosen)].set_index("key")
    if any(k not in a.index or k not in b.index for k in chosen):
        raise ValueError("Ho1 Dec27/Jan01 source boundary raw/forcing timestamps missing")
    rows=[]
    for k in chosen:
        original=a.loc[k];final=b.loc[k]
        rows.append({"site":"US-Ho1","timestamp":k,
            "original_TA_C":fmt(original.TA_F),
            "original_TA_F_QC":fmt(original.TA_F_QC),
            "original_VPD_hPa":fmt(original.VPD_F),
            "original_VPD_F_QC":fmt(original.VPD_F_QC),
            "selected_TA_C":fmt(final.TA_USE),
            "selected_VPD_hPa":fmt(final.VPD_USE),
            "selected_QBOT_kgkg":fmt(final.QBOT),
            "source_TA_equals_selected":str(abs(n(original.TA_F)-n(final.TA_USE))<=1e-7),
            "science_status":"ORIGINAL_NON_QC0_T_SOURCE_HOLD" if n(original.TA_F_QC)!=0 else "ORIGINAL_QC0_MEASURED"})
    if not (abs(n(a.loc["200012270900","TA_F"])-(-15.4))<0.05 and
            abs(n(a.loc["200012270930","TA_F"])-3.346)<0.05):
        raise ValueError("Ho1 historical 18.746 C original QC1->QC2 source switch changed")
    return rows

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert sum(YEAR_COUNTS.values())==215 and ALL_EXPECT==122
        assert sum(QC0_EXPECT[s] for s in FIVE)==98
        assert len(group_episodes([{"site":"US-EML","variable":"TA_F",
              "time":"2010-01-01 00:00:00","delta":"12","priority":"P0_QC0_TEMPERATURE_CHANGED",
              "original_implied_RH_pct":"NA","original_isolated_spike":"True",
              "reason":"test"},{"site":"US-EML","variable":"TA_F",
              "time":"2010-01-01 00:30:00","delta":"9","priority":"P1_QC0_TEMPERATURE_CHANGED",
              "original_implied_RH_pct":"NA","original_isolated_spike":"True",
              "reason":"test"}]))==1
        assert blob(POST)==POST_BLOB if POST.is_file() else True
        print("STAGE93 SELF-TEST PASS | 10-site/215-NC, 122 exact QC0 scope, episode grouping; no writes")
        return
    jobs=verify_inputs()
    if a.check:
        print("STAGE93 CHECK PASS | source/annual NC hashes verified; no writes")
        return
    post=module(POST,"stage93_uniform_stage09_science")
    output=ROOT/"reports"/("stage93_ten_site_postv5_QC0_manual_triage_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    marker=output/"INCOMPLETE_DO_NOT_USE_FOR_MODEL"
    marker.write_text("Ten-site unified post-v5 source and original QC0 triage not yet scientifically approved.\n")
    summary_rows=[]; original_qc0=[]; all_episodes=[]; anomalies=[]; failures=[]
    ho1=[]
    for site,item,trial,forcing,events_path in jobs:
        print("\nSTAGE93 UNIFIED POST-V5",site,"begin",flush=True)
        try:
            summary, details, qc0, annual=post.science_review(item,trial,forcing)
            if summary["QC0_edits"]!=QC0_EXPECT[site]:
                raise ValueError("Exact source original QC0 modification count drift: "+
                                 str(summary["QC0_edits"])+" != "+str(QC0_EXPECT[site]))
            if summary["RH_NONPOSITIVE"] or summary["QBOT_OUTSIDE_0_TO008"]:
                raise ValueError("Post-v5 selected final candidate remains physically invalid")
            extra=raw_neighbors(item,qc0)
            if len(extra)!=QC0_EXPECT[site]:
                raise ValueError("QC0 original source review count mismatch")
            original_qc0.extend(extra)
            group=group_episodes(extra)
            all_episodes.extend(group)
            summary_rows.append(summary)
            for r in annual:
                anomalies.append(r)
            if site=="US-Ho1":
                ho1=ho1_boundary(item,forcing)
            print("STAGE93 REVIEW PASS",site,
                  "QC0",len(extra),"episodes",len(group),
                  "new_TA_jumps",summary["NEW_TA_NATIVE_STEP_RATE_GT16C_H"],
                  "TA_gt15C_vs_ERA",summary["TA_VS_ERA_GT15C"],
                  "review_times",summary["review_timestamps"],flush=True)
        except Exception as exc:
            failures.append({"site":site,"error":str(exc)})
            print("STAGE93 REVIEW FAILURE",site,str(exc),flush=True)
    cols_summary=sorted(set(k for r in summary_rows for k in r))
    cols_qc=("site","time","variable","source_QC","original_value","candidate_value",
         "delta","ERA_reference","raw_previous","raw_next","original_TA_C",
         "original_VPD_hPa","original_implied_RH_pct","original_isolated_spike",
         "reason","candidate_source","priority","operator_decision")
    cols_ep=("site","variable","first","last","native_records","max_abs_change",
       "priority","raw_negative_RH_count","isolated_spikes","reasons",
       "human_decision","production_DATM_allowed")
    cols_ho1=("site","timestamp","original_TA_C","original_TA_F_QC",
              "original_VPD_hPa","original_VPD_F_QC","selected_TA_C",
              "selected_VPD_hPa","selected_QBOT_kgkg","source_TA_equals_selected",
              "science_status")
    cols_annual=sorted(set(k for row in anomalies for k in row))
    group=group_episodes(original_qc0)
    outputs={
        "ten_site_postv5_extreme_summary.csv":(summary_rows,cols_summary),
        "all_122_QC0_original_source_candidate_nearest_neighbors.csv":(original_qc0,cols_qc),
        "QC0_human_review_priority_episodes.csv":(group,cols_ep),
        "US-Ho1_2000_temperature_QC_transition_boundary.csv":(ho1,cols_ho1),
        "annual_postv5_extreme_counts.csv":(anomalies,cols_annual),
        "site_failures.csv":(failures,("site","error"))}
    for name,(rows,cols) in outputs.items():
        write_csv(output/name,rows,cols)
    digest={name:sha(output/name) for name in outputs}
    result={"schema":"STAGE93_TEN_SITE_UNIFIED_POSTV5_AND_ORIGINAL_QC0_TRIAGE_v1",
       "numerically_reviewed_sites":len(summary_rows),"site_failures":len(failures),
       "expected_annual_NC":215,"original_QC0_changed_variable_records":len(original_qc0),
       "QC0_operator_review_episodes":len(group),
       "review_timestamps_all_flags":sum(r["review_timestamps"] for r in summary_rows),
       "production_DATM_approved":False,
       "Stage87_manifest_sha256":sha(S87/"manifest.json"),
       "Stage92_manifest_sha256":sha(S92/"manifest.json"),
       "Stage07_manifest_sha256":sha(S07/"exact_input_manifest.json"),
       "original_input_or_forcing_modified":False,
       "out_sha256":digest}
    (output/"manifest.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("\n=== STAGE93 HUMAN DECISION PRIORITY ===",flush=True)
    for r in group[:35]:
        print("HUMAN_EPISODE",r["priority"],r["site"],r["variable"],
              r["first"],"to",r["last"],"HH",r["native_records"],
              "max_abs_delta",r["max_abs_change"],flush=True)
    print("HUMAN_QC0_BY_SITE",dict(Counter(x["site"] for x in original_qc0)),flush=True)
    print("HUMAN_EPISODES",len(group),"QC0_records",len(original_qc0),
          "other flagged times",
          sum(r["review_timestamps"] for r in summary_rows),flush=True)
    if len(summary_rows)==10 and len(original_qc0)==122 and not failures and len(ho1)==8:
        marker.unlink()
        print("STAGE93 TEN SITE POSTV5 AUDIT PASS | all 10 numeric/physics passes, 122 QC0 exact native decisions; human review NOT yet approved",flush=True)
    else:
        print("STAGE93 PARTIAL/HOLD | failures",len(failures),"completed",len(summary_rows),
              "QC0",len(original_qc0),"retained incomplete marker",flush=True)
    print("STAGE93 REPORT",output,flush=True)
    print("NO SOURCE/FORCING/NETCDF/CIME/SLURM WRITES",flush=True)
    return 0 if len(summary_rows)==10 and len(original_qc0)==122 and not failures and len(ho1)==8 else 2

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""AmeriFlux Batch03 Stage10e — P0/P1 raw-event flanking-window review.

This is NOT another forcing repair. It extracts ORIGINAL (Stage07 SHA-pinned)
tower meteorology within +/-6 hours of the highest-priority Stage10d clusters,
including VPD_F/TA_F, their original QC, optional RH/MDS and implied RH.
It reports the nearest usable native VPD/TA observations before and after
clusters, with QC0 distinguished from merely finite/gap-filled fields.

--check validates the immutable chain and row identities; no writes.
--run also creates a NEW, isolated Stage10e report ONLY.
No source edits, DATM, case or job submissions; zero repair approvals.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE10C = ROOT / "reports/stage10c_independent_cold_humidity_20261024T041355Z_36d578f4"
STAGE10D = ROOT / "reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
COUNTS = {"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
          "US-MtB":15,"US-NR1":173,"US-NR3":1484}
KEYS = ("site", "source_csv_row", "time")
NEIGHBOR_HOURS = 6
OUTPUTS_10D = {
    "all_1924_manual_review.csv", "site_triage_summary.csv",
    "consecutive_event_clusters.csv", "P0_high_priority_events.csv",
    "B_ice_supersaturation_78.csv", "A_water_failure_27.csv",
}


def checked_dir(p):
    p = Path(p)
    if not p.is_dir() or p.is_symlink():
        raise ValueError("Required regular directory absent or symlink: " + str(p))
    return p


def checked_file(p):
    p = Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlink input: " + str(p))
    return p


def sha256(p):
    h = hashlib.sha256()
    with checked_file(p).open("rb") as stream:
        for part in iter(lambda: stream.read(1024*1024), b""):
            h.update(part)
    return h.hexdigest()


def load_json(p):
    return json.loads(checked_file(p).read_text(encoding="utf-8"))


def bfield(df, col):
    s = df[col].astype(str).str.lower().str.strip()
    if not s.isin(("true", "false", "1", "0")).all():
        raise ValueError("Non-boolean field: " + col)
    return s.isin(("true", "1")).to_numpy(dtype=bool)


def num(series):
    x = pd.to_numeric(series, errors="coerce")
    return x.where(np.isfinite(x) & (x > -9990))


def water_es(t):
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        return 6.112 * np.exp(17.67 * t / (t + 243.5))


def ice_es(t):
    with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
        return 6.112 * np.exp(22.46 * t / (t + 272.62))


def preflight():
    for path in (ROOT, STAGE07, STAGE10C, STAGE10D):
        checked_dir(path)
    checked_file(STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    d_policy = load_json(STAGE10D / "read_only_provenance.json")
    if (d_policy.get("events") != 1924 or
            d_policy.get("no_replacement_approved") is not True or
            d_policy.get("priorities_are_approval") is not False or
            Path(d_policy.get("source_stage10c", "")).resolve() != STAGE10C or
            d_policy.get("source_stage10c_receipt_sha256") !=
                sha256(STAGE10C / "provenance_and_science_hold.json") or
            set(d_policy.get("output_sha256", {})) != OUTPUTS_10D):
        raise ValueError("Stage10d provenance/science-hold receipt changed")
    for name in OUTPUTS_10D:
        if sha256(STAGE10D / name) != d_policy["output_sha256"][name]:
            raise ValueError("Stage10d output SHA changed: " + name)

    ledger = pd.read_csv(
        STAGE10D / "all_1924_manual_review.csv",
        dtype={key: str for key in KEYS},
        keep_default_na=False, low_memory=False)
    clusters = pd.read_csv(
        STAGE10D / "consecutive_event_clusters.csv", low_memory=False)
    if (len(ledger) != 1924 or ledger.duplicated(list(KEYS)).any()
            or ledger.site.value_counts().to_dict() != COUNTS
            or ledger.duplicated(["site","time"]).any()
            or len(clusters) != 183
            or clusters.cluster.duplicated().any()
            or clusters.records.sum() != 1924):
        raise ValueError("Stage10d event keys/site totals/clusters no longer match")
    if (not all(ledger.review_priority.astype(str).str.startswith(("P0_","P1_","P2_","P3_","P4_")))
            or int(ledger.review_priority.str.startswith("P0_").sum()) != 31
            or int(ledger.review_priority.str.startswith("P1_").sum()) != 58):
        raise ValueError("Expected 31 P0 and 58 P1 records")
    if (bfield(ledger,"candidate_A_approved").any() or
            bfield(ledger,"candidate_B_approved").any() or
            not bfield(ledger,"scientific_hold_required").all()):
        raise ValueError("This workflow requires all candidates on scientific hold")
    cluster_keys = set(zip(clusters.site.astype(str), clusters.cluster.astype(str)))
    if not set(zip(ledger.site.astype(str), ledger.event_cluster_id.astype(str))) <= cluster_keys:
        raise ValueError("Stage10d event cluster references no longer match")
    cluster_counts = ledger.groupby(["site","event_cluster_id"]).size()
    for item in clusters.itertuples(index=False):
        if cluster_counts.get((item.site, item.cluster), 0) != int(item.records):
            raise ValueError("Stage10d cluster record count differs: " + item.cluster)

    doc = load_json(STAGE07 / "exact_input_manifest.json")
    sources = {d["site"]: d for d in doc["sites"]}
    pins = {str(Path(p).resolve()): d for p,d in doc["input_sha256"].items()}
    if len(sources) != 10 or not set(COUNTS) <= set(sources):
        raise ValueError("Stage07 release inventory missing Batch03 stations")
    for site in COUNTS:
        info = sources[site]
        if int(info["native_minutes"]) != (60 if site == "US-MMS" else 30):
            raise ValueError("Unexpected native interval at " + site)
        path = checked_file(Path(info["primary"]))
        if path.parent.name != info["release"] or path.parent.parent.name != "raw":
            raise ValueError("Unexpected original release path " + str(path))
        if sha256(path) != pins.get(str(path.resolve()), ""):
            raise ValueError("Stage07 original primary SHA mismatch: " + str(path))
        print("SHA ORIGINAL PASS:",site,path.name,flush=True)
    high = ledger.review_priority.astype(str).str.startswith(("P0_","P1_"))
    selected_ids = set(ledger.loc[high,"event_cluster_id"])
    # cluster names include the site, but compare explicit keys for safety
    selected_keys = set(zip(ledger.loc[high, "site"],ledger.loc[high,"event_cluster_id"]))
    work = clusters.loc[
        [((str(r.site),str(r.cluster)) in selected_keys)
         for r in clusters.itertuples(index=False)]].copy()
    if len(work)==0 or len(work)>183 or len(selected_ids)>183:
        raise ValueError("No valid high-priority cluster selection")
    if len(work)!=len(selected_keys):
        raise ValueError("P0/P1 cluster selection incomplete")
    return ledger,work,sources,d_policy


def load_raw(site, info):
    source = checked_file(Path(info["primary"]))
    header = set(pd.read_csv(source, nrows=0).columns)
    required = {"TIMESTAMP_START","TA_F","VPD_F"}
    if not required.issubset(header):
        raise ValueError("Original tower source missing required fields: "+site)
    requested = [
        "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
        "PA_F","PA_F_QC","SW_IN_F","SW_IN_F_QC",
        "RH","RH_QC","RH_F","RH_F_QC",
        "VPD_F_MDS","VPD_F_MDS_QC","TA_F_MDS","TA_F_MDS_QC",
    ]
    cols = [x for x in requested if x in header]
    data = pd.read_csv(source, usecols=cols,
                       dtype={"TIMESTAMP_START":str}, low_memory=False)
    data["native_local"] = pd.to_datetime(
        data.TIMESTAMP_START, format="%Y%m%d%H%M", errors="raise")
    if data.native_local.duplicated().any():
        raise ValueError("Original native tower times have duplicates: "+site)
    if not data.native_local.is_monotonic_increasing:
        raise ValueError("Tower source time no longer strictly ascending: "+site)
    data["raw_tower_T_C"] = num(data["TA_F"])
    data["raw_tower_VPD_hPa"] = num(data["VPD_F"])
    data["raw_water_es_hPa"] = water_es(data["raw_tower_T_C"])
    data["raw_water_ea_hPa"] = data["raw_water_es_hPa"]-data["raw_tower_VPD_hPa"]
    data["raw_water_RH_pct"] = 100*data["raw_water_ea_hPa"]/data["raw_water_es_hPa"]
    es_i = ice_es(data["raw_tower_T_C"])
    data["raw_ice_RH_pct"] = 100*data["raw_water_ea_hPa"]/es_i
    data["raw_water_physical"] = (
        data["raw_tower_T_C"].between(-80,65) &
        data["raw_tower_VPD_hPa"].between(0,125) &
        data["raw_water_RH_pct"].gt(0) &
        data["raw_water_RH_pct"].le(100.05)
    )
    if "VPD_F_QC" in cols:
        data["raw_VPD_QC0"] = num(data["VPD_F_QC"]).eq(0)
    else:
        data["raw_VPD_QC0"] = False
    data["raw_valid_QC0_pair"] = data["raw_water_physical"] & data["raw_VPD_QC0"]
    return data


def nearest(before_after, side, boundary):
    if before_after.empty:
        return {"{}_flank_valid".format(side):False,
                "{}_flank_QC0".format(side):False}
    valid = before_after.loc[before_after.raw_water_physical]
    qc0 = before_after.loc[before_after.raw_valid_QC0_pair]
    if valid.empty:
        return {"{}_flank_valid".format(side):False,
                "{}_flank_QC0".format(side):False}
    pick = (valid.iloc[-1] if side == "before" else valid.iloc[0])
    result = {
        side+"_flank_valid":True,
        side+"_flank_QC0":not qc0.empty,
        side+"_flank_T_C":float(pick["raw_tower_T_C"]),
        side+"_flank_VPD_hPa":float(pick["raw_tower_VPD_hPa"]),
        side+"_flank_RH_water_pct":float(pick["raw_water_RH_pct"]),
        side+"_flank_minutes_to_boundary":
            float(abs((boundary-pick["native_local"]).total_seconds())/60),
    }
    if not qc0.empty:
        best=qc0.iloc[-1] if side=="before" else qc0.iloc[0]
        result[side+"_QC0_nearest_minutes"] = float(
            abs((boundary-best["native_local"]).total_seconds())/60)
        result[side+"_QC0_RH_water_pct"] = float(best["raw_water_RH_pct"])
    return result


def context_analysis(ledger, chosen, sources):
    frames=[]
    summaries=[]
    used_keys=set()
    for site in sorted(COUNTS):
        groups=chosen.loc[chosen.site.eq(site)]
        if groups.empty:
            continue
        raw=load_raw(site,sources[site])
        observed=set(raw.TIMESTAMP_START)
        native_step=int(sources[site]["native_minutes"])
        site_ledger=ledger.loc[ledger.site.eq(site)].copy()
        timestamps=pd.to_datetime(site_ledger.time,errors="raise")
        event_codes=set(timestamps.dt.strftime("%Y%m%d%H%M"))
        if len(event_codes)!=len(site_ledger) or not event_codes.issubset(observed):
            raise ValueError("One or more Stage10d blocker timestamps missing in raw tower source: "+site)
        site_ledger["native_local"] = timestamps
        annotations = site_ledger[[
            "native_local","source_csv_row","review_priority","event_cluster_id",
            "flag_A_water_failure","flag_A_ice_supersaturation",
            "flag_B_ice_supersaturation","flag_tower_grid_T_gt5C",
            "VPD_before_fallback_hPa","absolute_vpd_at_tower_T_hPa",
            "relative_vpd_at_tower_T_hPa","independent_A_ice_RH_pct",
            "independent_B_ice_RH_pct","grid_temperature_C",
        ]]
        for r in groups.itertuples(index=False):
            ident=str(r.cluster)
            key=(site,ident)
            if key in used_keys:
                raise ValueError("Repeated site and cluster identity")
            used_keys.add(key)
            start=pd.Timestamp(r.start_local)
            end=pd.Timestamp(r.end_local)
            if end<start:
                raise ValueError("Cluster end precedes start")
            events=site_ledger.loc[site_ledger.event_cluster_id.eq(ident)]
            if len(events)!=int(r.records):
                raise ValueError("Event cluster count mismatched")
            expected_span=(end-start)/pd.Timedelta(minutes=native_step)+1
            if abs(float(expected_span)-len(events))>0.00001:
                raise ValueError("Original Stage10d event cluster not native-contiguous")
            dt=raw.native_local
            context=raw.loc[
                (dt>=start-pd.Timedelta(hours=NEIGHBOR_HOURS)) &
                (dt<=end+pd.Timedelta(hours=NEIGHBOR_HOURS))
            ].copy()
            if context.empty:
                raise ValueError("Empty flanking-window tower context")
            expected_interval=((context.native_local.diff().dropna()
                                / pd.Timedelta(minutes=1)).to_numpy())
            if np.any(expected_interval!=native_step):
                raise ValueError("Raw source flanking timestamps not native-continuous at "+ident)
            context=context.merge(
                annotations,on="native_local",how="left",validate="one_to_one")
            context["site"]=site
            context["selected_cluster"]=ident
            context["window_phase"]=np.where(
                context.native_local<start,"BEFORE",
                np.where(context.native_local>end,"AFTER","INSIDE"))
            pre=context.loc[context.window_phase.eq("BEFORE")]
            post=context.loc[context.window_phase.eq("AFTER")]
            inside=context.loc[context.window_phase.eq("INSIDE")]
            if len(inside)!=len(events):
                raise ValueError("Missing original native rows within target cluster")
            flanks={**nearest(pre,"before",start),**nearest(post,"after",end)}
            high_priority=events.review_priority.astype(str).str.startswith(("P0_","P1_"))
            summary = {
                "site":site,"cluster":ident,
                "events":len(events),
                "P0_events":int(events.review_priority.astype(str).str.startswith("P0_").sum()),
                "P1_events":int(events.review_priority.astype(str).str.startswith("P1_").sum()),
                "start_local":str(start),"end_local":str(end),
                "native_minutes":native_step,
                "flank_hours":NEIGHBOR_HOURS,
                "before_raw_rows":len(pre),
                "after_raw_rows":len(post),
                "before_valid_raw_T_VPD":int(pre.raw_water_physical.sum()),
                "after_valid_raw_T_VPD":int(post.raw_water_physical.sum()),
                "before_valid_QC0_T_VPD":int(pre.raw_valid_QC0_pair.sum()),
                "after_valid_QC0_T_VPD":int(post.raw_valid_QC0_pair.sum()),
                "inside_raw_water_physical":int(inside.raw_water_physical.sum()),
                "inside_raw_VPD_QC0":int(inside.raw_VPD_QC0.sum()),
                "A_fail_count":int(events.flag_A_water_failure.astype(str).str.lower().eq("true").sum()),
                "B_ice_count":int(events.flag_B_ice_supersaturation.astype(str).str.lower().eq("true").sum()),
                "high_priority_events":int(high_priority.sum()),
                "raw_VPD_field_is_raw_not_corrected":True,
                "science_status":"MANUAL_REVIEW_NO_REPAIR_APPROVED",
                **flanks
            }
            flank_qc=(bool(flanks.get("before_flank_QC0"))+
                      bool(flanks.get("after_flank_QC0")))
            summary["flank_evidence_class"] = (
                "QC0_BOTH_SIDES" if flank_qc==2 else
                "QC0_ONE_SIDE" if flank_qc==1 else
                "NO_VALID_QC0_FLANK_BOTH_SIDES")
            summaries.append(summary)
            # Keep the event fields and every raw point +/-6h; overlap is
            # intentionally retained per cluster for review, not counted as
            # additional independent source observations.
            frames.append(context)
        print(f"SITE CONTEXT: {site} high_priority_clusters={len(groups)} "
              f"raw_timestamps={len(raw)} source_sha_verified=True",flush=True)
    if len(summaries)!=len(chosen) or len(set(used_keys))!=len(chosen):
        raise ValueError("Not all selected P0/P1 clusters were analyzed")
    details=pd.concat(frames,ignore_index=True)
    clustered=pd.DataFrame(summaries)
    return clustered,details


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choices=parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--check",action="store_true")
    choices.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE10E — ORIGINAL TOWER EVENT CONTEXT / P0+P1", flush=True)
    ledger, chosen, sources, provenance = preflight()
    print(f"STAGE10E PREFLIGHT: 1924/1924 event keys and 183 cluster/source"
          f" SHA verified, P0=31 P1=58, selected_clusters={len(chosen)}",flush=True)
    if args.check:
        print("CHECK ONLY: no changes to reports or source, forcing, DATM or jobs.")
        return
    summary,context=context_analysis(ledger,chosen,sources)
    print("\n========== HIGH-PRIORITY CLUSTER CONTEXT BY SITE ==========",flush=True)
    print(summary.groupby("site",sort=True).agg(
        clusters=("cluster","size"),
        P0_events=("P0_events","sum"),
        P1_events=("P1_events","sum"),
        QC0_both_flanks=("flank_evidence_class",lambda x:sum(x=="QC0_BOTH_SIDES")),
        QC0_one_flank=("flank_evidence_class",lambda x:sum(x=="QC0_ONE_SIDE")),
        QC0_neither_flank=("flank_evidence_class",lambda x:sum(x=="NO_VALID_QC0_FLANK_BOTH_SIDES"))
    ).to_string(),flush=True)
    print(f"\nSTAGE10E SUMMARY: source_events=1924/1924 "
          f"selected_priority_events=89/89 selected_clusters={len(summary)} "
          f"window_rows={len(context)} event_approvals=0",flush=True)
    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    report=ROOT/"reports"/("stage10e_priority_flank_context_"+tag)
    report.mkdir(exist_ok=False)
    exports={
        "P0_P1_cluster_flank_summary.csv":summary,
        "P0_P1_raw_native_context_6h.csv":context
    }
    for name,frame in exports.items():
        frame.to_csv(report/name,index=False)
    receipt = {
        "source_stage10d":str(STAGE10D),
        "source_stage10d_receipt_sha256":sha256(STAGE10D/"read_only_provenance.json"),
        "source_stage07_trial":str(STAGE07),
        "event_scope":1924,
        "P0":31,"P1":58,"selected_high_priority_clusters":len(summary),
        "raw_original_no_modifications":True,
        "no_approved_candidate":True,
        "flanking_window_hours_each_side":NEIGHBOR_HOURS,
        "limitations":[
            "Flank numerical values are RAW tower products, not independent certified observations.",
            "QC0 is a native source label; it does not settle cross-variable provenance.",
            "Source temperatures and Stage10d retained temperatures may differ after QCv5.",
            "No raw data, Stage07/10b/10c/10d reports, DATM or case modified.",
            "No clock-offset, PFT or humidity replacement approved."
        ],
        "output_SHA256":{name:sha256(report/name) for name in exports}
    }
    (report/"read_only_provenance.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE10E REPORT DIR:",report,flush=True)
    print("SCIENTIFIC HOLD: examine flank observations and provenance before any repair.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10E STOP:",str(exc),file=sys.stderr,flush=True)
        raise SystemExit(2)

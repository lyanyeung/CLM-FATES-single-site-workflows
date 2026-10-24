#!/usr/bin/env python3
"""Batch02 Stage57: detailed READ-ONLY evidence for 63 original TA_F - CDS ERA5 >8C.

Only three sites: US-EML 27, US-GLE 6, US-ICt 30. Audit original same-
release FLUXNET TA_F/T-QC at the exact Stage56 native tower timestamp;
sample original half-hourly temperatures at ±30/60/120 minutes and
nearby QC0 reference points; identify time clusters and isolated spikes.
All 63 remain scientific HOLD; no forcing, stage outputs or raw edits.

Run --self-test, --check (stdout all 63), --audit (isolated new reports).
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11=EXP/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S56=EXP/"reports/stage56_original_T_if_ERA5_delta_le8C_20261024T104425Z_044e977d"
SRC56="4884_keep_original_TA_under8C_with_ERA5_RH_VPD_QBOT.csv"
SITES={"US-EML":27,"US-GLE":6,"US-ICt":30}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def numeric(series):
    v=pd.to_numeric(series,errors="coerce")
    return v.mask(v.le(-9990)|~np.isfinite(v))

def local_timestamps(series):
    return pd.to_datetime(series.astype(str).str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")

def parse_result_local(series):
    v=pd.to_datetime(series.astype(str),errors="raise")
    if v.isna().any() or v.dt.tz is not None:
        raise ValueError("Invalid native tower local timestamp")
    return v

def read_and_pin():
    if (S56/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage56 report incomplete")
    m56=json.loads((S56/"policy_manifest.json").read_text())
    if (m56.get("schema")!="STAGE56_ORIGINAL_TA_UNDER8C_CDS_ERA5_POLICY_v1"
        or m56.get("n_records")!=4884
        or m56.get("temperature_abs_difference_threshold_C")!=8.0
        or m56.get("approved_for_DATM") is not False
        or m56.get("all_science_forcing_HOLD") is not True
        or m56.get("no_original_or_forcing_changes") is not True
        or m56.get("source_STAGE19") is None
        or m56.get("source_STAGE55") is None):
        raise ValueError("Stage56 policy/scientific provenance differs")
    for f,digest in m56.get("output_sha256",{}).items():
        if sha(S56/f)!=digest:
            raise ValueError("Stage56 output was changed: "+f)
    paths={
        "stage55_manifest_sha256":EXP/"reports/stage55_4884_existing_ERA5_science_triage_20261024T102824Z_8a2c5021/science_triage_manifest.json",
        "stage55_rows_sha256":EXP/"reports/stage55_4884_existing_ERA5_science_triage_20261024T102824Z_8a2c5021/4884_existing_ERA5_candidates_science_routes.csv",
        "stage19_rows_sha256":Path(m56["source_STAGE19"])/"all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv",
        "stage19_manifest_sha256":Path(m56["source_STAGE19"])/"manifest.json",
        "stage11_rows_sha256":S11/"cold_humidity_repair_proposals.csv",
        "stage54_manifest_sha256":EXP/"reports/stage54_444_vs_4884_timestamp_crosswalk_20261024T101940Z_bac3a939/crosswalk_manifest.json",
    }
    for key,path in paths.items():
        if sha(path)!=m56["source_sha256"][key]:
            raise ValueError("Stage56 pinned input changed: "+key)
    m11=json.loads((S11/"manifest.json").read_text())
    stage08=Path(m11["source_stage08"])/"exact_input_manifest.json"
    m08=json.loads(stage08.read_text())
    primary={r["site"]:Path(r["primary"]).resolve(strict=True)
             for r in m08["sites"]}
    tower={}
    for site in SITES:
        p=primary[site]
        if sha(p)!=m11["input_hashes"].get(str(p)):
            raise ValueError("Original FLUXNET tower primary changed "+site)
        headers=pd.read_csv(p,nrows=0).columns.tolist()
        needed=["TIMESTAMP_START","TA_F","TA_F_QC"]
        if any(v not in headers for v in needed):
            raise ValueError("Original tower required TA/TQC columns missing "+site)
        optional=[v for v in ("PA_F","VPD_F","VPD_F_QC","RH","RH_QC") if v in headers]
        d=pd.read_csv(p,usecols=needed+optional,dtype={"TIMESTAMP_START":str})
        d["local_time"]=local_timestamps(d["TIMESTAMP_START"])
        if d.local_time.duplicated().any():
            raise ValueError("Original tower timestamp duplicate "+site)
        for col in needed[1:]+optional:
            d[col]=numeric(d[col])
        tower[site]=d.set_index("local_time").sort_index()
    df=pd.read_csv(S56/SRC56,dtype={"site":str,"local":str})
    if len(df)!=4884:
        raise ValueError("Unexpected Stage56 4884 records")
    df["local_time"]=parse_result_local(df["local"])
    if df.duplicated(["site","local_time"]).any():
        raise ValueError("Duplicate Stage56 site/time")
    subset=df[df.temp_decision.eq("HOLD_TA_DIFF_FROM_ERA5_GT8C")].copy()
    if len(subset)!=63 or Counter(subset.site)!=Counter(SITES):
        raise ValueError("Unexpected >8C site/event counts")
    subset.sort_values(["site","local_time"],inplace=True)
    if not np.isfinite(pd.to_numeric(subset.ERA5_T2M_C,errors="coerce")).all():
        raise ValueError("External ERA5 T2m invalid")
    return subset,tower,{"stage56_csv_sha256":sha(S56/SRC56),
         "stage56_manifest_sha256":sha(S56/"policy_manifest.json"),
         "source_stage11_manifest_sha256":sha(S11/"manifest.json"),
         "stage08_manifest_sha256":sha(stage08),
         "raw_tower_primary_sha256":{s:sha(primary[s]) for s in SITES}}

def row_context(event,raw):
    ts=event["local_time"]
    if ts not in raw.index:
        raise ValueError("Original tower event local time missing "+str(ts))
    current=raw.loc[ts]
    t=float(event["TA_F"])
    if not np.isfinite(current["TA_F"]) or abs(current["TA_F"]-t)>1e-8:
        raise ValueError("Stage56 TA_F not identical to original tower at "+str(ts))
    qc=float(event["TA_F_QC"])
    if not np.isclose(current["TA_F_QC"],qc,equal_nan=True):
        raise ValueError("Stage56 source T QC differs at "+str(ts))
    res={}
    for mins,alias in [(-120,"m120"),(-60,"m60"),(-30,"m30"),
                       (30,"p30"),(60,"p60"),(120,"p120")]:
        key=ts+pd.Timedelta(minutes=mins)
        if key in raw.index:
            v=raw.loc[key]
            res["TA_"+alias+"_C"]=v["TA_F"]
            res["QC_"+alias]=v["TA_F_QC"]
        else:
            res["TA_"+alias+"_C"]=np.nan
            res["QC_"+alias]=np.nan
    prev,next_=res["TA_m30_C"],res["TA_p30_C"]
    res["tower_both_30min_neighbors_valid"]=bool(
        np.isfinite(prev) and np.isfinite(next_))
    res["tower_linear_30min_interp_C"]=float((prev+next_)/2) if (
        res["tower_both_30min_neighbors_valid"]) else np.nan
    res["tower_minus_30min_neighbor_mean_C"]=(
        t-res["tower_linear_30min_interp_C"] if res[
          "tower_both_30min_neighbors_valid"] else np.nan)
    res["neighbors_30min_difference_C"]=(
        float(abs(next_-prev)) if res["tower_both_30min_neighbors_valid"]
        else np.nan)
    res["isolated_tower_spike_candidate"]=bool(
        res["tower_both_30min_neighbors_valid"] and
        abs(res["tower_minus_30min_neighbor_mean_C"])>5 and
        res["neighbors_30min_difference_C"]<=3)
    res["neighbor_continuity_with_tower_within3C"]=bool(
        res["tower_both_30min_neighbors_valid"] and
        abs(t-prev)<=3 and abs(t-next_)<=3)
    # Tower QC0 nearest observation within +/- 6 h, evidence only.
    nearby=raw.loc[(raw.index>=ts-pd.Timedelta(hours=6))&
                   (raw.index<=ts+pd.Timedelta(hours=6))]
    good=nearby.loc[(nearby.TA_F_QC==0)&
                    np.isfinite(nearby.TA_F)&
                    (nearby.TA_F>-80)&(nearby.TA_F<65)]
    if len(good):
        times=np.abs((good.index-ts).total_seconds()/60)
        i=int(np.argmin(times))
        res["nearest_QC0_minutes_away"]=float(times[i])
        res["nearest_QC0_T_C"]=float(good.iloc[i].TA_F)
    else:
        res["nearest_QC0_minutes_away"]=np.nan
        res["nearest_QC0_T_C"]=np.nan
    # Local daily source context, no guessed seasons or climates.
    same=raw.loc[raw.index.normalize()==ts.normalize()]
    valid=same.TA_F[np.isfinite(same.TA_F)&
                    (same.TA_F>-80)&(same.TA_F<65)]
    res["same_day_tower_T_median_C"]=float(valid.median()) if len(valid) else np.nan
    res["same_day_T_minus_median_C"]=(
        t-res["same_day_tower_T_median_C"] if len(valid) else np.nan)
    return res

def event_report(df,tower):
    rows=[]
    for _,record in df.iterrows():
        site=record["site"]
        ctx=row_context(record,tower[site])
        raw_t=float(record["TA_F"])
        era_t=float(record["ERA5_T2M_C"])
        delta=raw_t-era_t
        if not np.isfinite(delta) or abs(delta)<=8:
            raise ValueError("Expected exact >8C discrepancy missing")
        rows.append(dict(site=site,local=record["local_time"].strftime("%Y-%m-%d %H:%M"),
           TA_F_C=raw_t,ERA5_T2M_C=era_t,TA_minus_ERA5_C=delta,
           abs_delta_C=abs(delta),TA_F_QC=record["TA_F_QC"],
           original_VPD_F_hPa=record.get("VPD_F",np.nan),
           original_VPD_F_QC=record.get("VPD_F_QC",np.nan),
           ERA5_RH_water_pct=record["ERA5_RH_water_pct"],
           retained_TA_C=record["retained_TA_C"],
           source_decision=record["temp_decision"],
           **ctx))
    out=pd.DataFrame(rows).sort_values(["site","local"]).reset_index(drop=True)
    out["cluster_id"]=""
    group=0
    for site,ix in out.groupby("site",sort=False).groups.items():
        last=None
        for i in ix:
            now=pd.Timestamp(out.at[i,"local"])
            if last is None or (now-last)>pd.Timedelta(hours=2):
                group+=1
            out.at[i,"cluster_id"]=f"{site}-G{group:03d}"
            last=now
    out["human_review_status"]="HOLD_NEEDS_MANUAL_SOURCE_AND_METEOROLOGY_REVIEW"
    out["auto_replace_T_with_ERA5"]=False
    out["approved_for_DATM"]=False
    return out

def self_test():
    idx=pd.date_range("2008-01-02 00:00",periods=5,freq="30min")
    src=pd.DataFrame({"TA_F":[1,1,12,1,1],"TA_F_QC":[0,0,2,0,0]},
                     index=idx)
    evt={"local_time":idx[2],"TA_F":12,"TA_F_QC":2}
    evidence=row_context(evt,src)
    assert evidence["isolated_tower_spike_candidate"]
    assert abs(evidence["tower_minus_30min_neighbor_mean_C"]-11)<1e-9
    assert not evidence["neighbor_continuity_with_tower_within3C"]
    assert sum(SITES.values())==63
    print("STAGE57 SELF-TEST PASS | original tower neighbors, jumps, QC0 and 63 rows")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    flags=p.add_mutually_exclusive_group(required=True)
    flags.add_argument("--self-test",action="store_true")
    flags.add_argument("--check",action="store_true")
    flags.add_argument("--audit",action="store_true")
    p.add_argument("--output-root",type=Path,default=EXP/"reports")
    a=p.parse_args()
    if a.self_test:return self_test()
    subset,tower,pins=read_and_pin()
    evidence=event_report(subset,tower)
    print("STAGE57 SOURCE CHECK PASS | original EC tower + Stage56 + independent ERA5; exactly 63")
    counts=[]
    for site in SITES:
        d=evidence.loc[evidence.site.eq(site)]
        summary=dict(site=site,n=len(d),
             T_QC_counts={str(k):int(v) for k,v in Counter(d.TA_F_QC).items()},
             median_abs_diff_C=round(float(d.abs_delta_C.median()),2),
             max_abs_diff_C=round(float(d.abs_delta_C.max()),2),
             tower_warmer_ERA5=int(d.TA_minus_ERA5_C.gt(0).sum()),
             tower_colder_ERA5=int(d.TA_minus_ERA5_C.lt(0).sum()),
             isolated_jump_candidates=int(d.isolated_tower_spike_candidate.sum()),
             neighbor_continuity_within3C=int(d.neighbor_continuity_with_tower_within3C.sum()),
             n_clusters=int(d.cluster_id.nunique()))
        counts.append(summary)
        print("SITE",summary)
    print("=== ALL 63 ORIGINAL TOWER VS INDEPENDENT ERA5: MANUAL-REVIEW EVIDENCE ===")
    view=["site","local","TA_F_C","ERA5_T2M_C","TA_minus_ERA5_C",
          "TA_F_QC","TA_m30_C","TA_p30_C","tower_minus_30min_neighbor_mean_C",
          "isolated_tower_spike_candidate","neighbor_continuity_with_tower_within3C",
          "cluster_id"]
    print(evidence[view].round(2).to_string(index=False))
    print("DIAGNOSTIC FLAGS ARE NOT SCIENTIFIC APPROVALS")
    if a.check:
        print("STAGE57 CHECK PASS | no writes")
        return
    root=a.output_root.resolve()
    if root==S56 or S56 in root.parents:
        raise ValueError("Output root overlaps Stage56")
    dest=root/("stage57_manual_63_T_gt8C_original_tower_review_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Not a scientific approval or valid model input.\n")
    cluster=evidence.groupby(["site","cluster_id"],as_index=False).agg(
        n=("local","size"),start=("local","min"),end=("local","max"),
        max_abs_temp_diff_C=("abs_delta_C","max"),
        isolated_jump_candidates=("isolated_tower_spike_candidate","sum"))
    outputs={"63_original_tower_temperature_source_neighbor_evidence.csv":evidence,
             "three_site_temperature_anomaly_groups.csv":cluster,
             "three_site_review_summary.csv":pd.DataFrame([{
                 **{k:v for k,v in x.items() if k!="T_QC_counts"},
                 "TA_F_QC_counts_json":json.dumps(x["T_QC_counts"],sort_keys=True)}
                 for x in counts])}
    hashes={}
    for name,data in outputs.items():
        f=dest/name
        data.to_csv(f,index=False)
        hashes[name]=sha(f)
    if sha(S56/SRC56)!=pins["stage56_csv_sha256"]:
        raise ValueError("Upstream Stage56 changed while writing report")
    (dest/"review_manifest.json").write_text(json.dumps({
        "schema":"STAGE57_63_ORIGINAL_TA_ERA5_DIFF_REVIEW_v1",
        "count":63,"counts_by_site":SITES,
        "source_sha256":pins,"output_sha256":hashes,
        "all_rows_HOLD":True,"no_original_or_model_changes":True,
        "scientific_approval_count":0},indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE57 AUDIT PASS | exact 63 >8C tower-vs-ERA5 manual-review evidence")
    print("REPORT",dest)
    print("NO ORIGINAL, STAGE56, DATM, CIME, FORCING OR SLURM CHANGES")
if __name__=="__main__":
    main()

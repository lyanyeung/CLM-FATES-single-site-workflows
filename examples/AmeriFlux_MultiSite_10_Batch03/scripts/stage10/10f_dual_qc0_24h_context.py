#!/usr/bin/env python3
"""Batch03 Stage10f: independent 6h/24h dual-QC0 audit at 19 P0/P1 clusters.

Scientific correction to Stage10e interpretation: Stage10e's
raw_valid_QC0_pair tests original VPD_F_QC==0 and *numeric* TA_F/VPD_F
plausibility, not simultaneously TA_F_QC==0. This script explicitly
distinguishes VPD-QC0 from DUAL TA+VPD QC0, independently checks the
Stage10e 6h report and searches original Stage07 SHA-pinned native source
within 24h on either side of each of 19 high-priority clusters.

This reports evidence only: QC0 source fields do not alone establish
independent atmospheric humidity measurement. No replacement, timestamp
adjustment, physical clipping, new climate forcing, DATM or model tasks.
--check: read-only full calculation and console summary.
--run: same calculation + NEW isolated Stage10f report; no source edits.
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
STAGE10D = ROOT / "reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
STAGE10E = ROOT / "reports/stage10e_priority_flank_context_20261024T043136Z_557ade35"
EXPECTED = {"US-Kon": 229, "US-MMS": 18, "US-Me2": 4, "US-Me6": 1,
            "US-MtB": 15, "US-NR1": 173, "US-NR3": 1484}
KEYS = ["site", "source_csv_row", "time"]
PRIMARY_COLS = [
    "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC", "PA_F", "PA_F_QC",
    "SW_IN_F", "SW_IN_F_QC", "RH", "RH_QC", "RH_F", "RH_F_QC",
    "TA_F_MDS", "TA_F_MDS_QC", "VPD_F_MDS", "VPD_F_MDS_QC",
]


def normal_file(p):
    p = Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or unsafe evidence file: " + str(p))
    return p


def normal_dir(p):
    p = Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or unsafe evidence folder: " + str(p))
    return p


def checksum(path):
    h = hashlib.sha256()
    with normal_file(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(normal_file(path).read_text(encoding="utf-8"))


def boolean(series):
    s = series.astype(str).str.strip().str.lower()
    if not s.isin(["true", "false", "1", "0"]).all():
        raise ValueError("Corrupted boolean field in evidence")
    return s.isin(["true", "1"]).to_numpy(dtype=bool)


def numeric(series):
    x = pd.to_numeric(series, errors="coerce")
    return x.where(np.isfinite(x) & (x > -9990))


def water_es(t):
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return 6.112 * np.exp(17.67 * t / (t + 243.5))


def rowkeys(df):
    return set(map(tuple, df[KEYS].to_numpy()))


def evidence():
    for d in (ROOT, STAGE07, STAGE10D, STAGE10E):
        normal_dir(d)
    normal_file(STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    dmeta = read_json(STAGE10D / "read_only_provenance.json")
    emeta = read_json(STAGE10E / "read_only_provenance.json")
    if (dmeta.get("events") != 1924 or dmeta.get("no_replacement_approved") is not True or
            dmeta.get("priorities_are_approval") is not False):
        raise ValueError("Stage10d scientific-hold lineage changed")
    d_required = {
        "all_1924_manual_review.csv", "site_triage_summary.csv",
        "consecutive_event_clusters.csv", "P0_high_priority_events.csv",
        "B_ice_supersaturation_78.csv", "A_water_failure_27.csv",
    }
    if set(dmeta.get("output_sha256", {})) != d_required:
        raise ValueError("Unexpected Stage10d output receipt")
    for p in d_required:
        if checksum(STAGE10D/p) != dmeta["output_sha256"][p]:
            raise ValueError("Stage10d pinned file modified: " + p)
    if (Path(emeta.get("source_stage10d", "")).resolve() != STAGE10D or
            emeta.get("source_stage10d_receipt_sha256") != checksum(STAGE10D/"read_only_provenance.json") or
            emeta.get("event_scope") != 1924 or emeta.get("P0") != 31 or
            emeta.get("P1") != 58 or
            emeta.get("raw_original_no_modifications") is not True or
            emeta.get("no_approved_candidate") is not True or
            emeta.get("flanking_window_hours_each_side") != 6):
        raise ValueError("Stage10e receipt changed or no longer scientific hold")
    e_required = {"P0_P1_cluster_flank_summary.csv","P0_P1_raw_native_context_6h.csv"}
    if set(emeta.get("output_SHA256", {})) != e_required:
        raise ValueError("Stage10e output receipt differs")
    for p in e_required:
        if checksum(STAGE10E/p) != emeta["output_SHA256"][p]:
            raise ValueError("Stage10e SHA changed: " + p)

    ledger = pd.read_csv(normal_file(STAGE10D/"all_1924_manual_review.csv"),
        dtype={k:str for k in KEYS},keep_default_na=False,low_memory=False)
    groups = pd.read_csv(normal_file(STAGE10D/"consecutive_event_clusters.csv"))
    oldsummary = pd.read_csv(normal_file(STAGE10E/"P0_P1_cluster_flank_summary.csv"))
    oldwindow = pd.read_csv(normal_file(STAGE10E/"P0_P1_raw_native_context_6h.csv"))
    if (len(ledger)!=1924 or ledger.duplicated(KEYS).any() or
            ledger.site.value_counts().to_dict()!=EXPECTED or
            len(groups)!=183 or groups.cluster.duplicated().any() or
            int(groups.records.sum())!=1924 or
            len(oldsummary)!=19 or oldsummary.cluster.duplicated().any() or
            len(oldwindow)!=773):
        raise ValueError("Unexpected Stage10d–e event, window or cluster counts")
    high=ledger.loc[ledger.review_priority.astype(str).str.startswith(("P0_","P1_"))].copy()
    if (len(high)!=89 or
            int(high.review_priority.str.startswith("P0_").sum())!=31 or
            int(high.review_priority.str.startswith("P1_").sum())!=58):
        raise ValueError("Expected exactly 31 P0 plus 58 P1 events")
    selected=set(zip(high.site,high.event_cluster_id))
    old_clusters=set(zip(oldsummary.site,oldsummary.cluster))
    if len(selected)!=19 or selected!=old_clusters:
        raise ValueError("Stage10e cluster selection differs from Stage10d")
    if not set(zip(oldwindow.site,oldwindow.selected_cluster)).issubset(selected):
        raise ValueError("Stage10e native window has unknown clusters")
    if not {"site", "selected_cluster", "window_phase", "native_local"}.issubset(oldwindow.columns):
        raise ValueError("Stage10e window schema changed")
    inside=oldwindow.loc[oldwindow.window_phase=="INSIDE"]
    if not set(zip(inside.site,inside.selected_cluster))==selected:
        raise ValueError("Stage10e window incomplete within target clusters")
    doc=read_json(STAGE07/"exact_input_manifest.json")
    original={row["site"]:row for row in doc["sites"]}
    hashes={str(Path(p).resolve()):value for p,value in doc["input_sha256"].items()}
    if len(original)!=10 or not set(EXPECTED).issubset(original):
        raise ValueError("Stage07 source selection inconsistent")
    for site in sorted(set(high.site)):
        spec=original[site]
        if int(spec["native_minutes"])!=(60 if site=="US-MMS" else 30):
            raise ValueError("Unexpected timestamp resolution: "+site)
        path=normal_file(spec["primary"])
        if (path.parent.name!=spec["release"] or path.parent.parent.name!="raw" or
                checksum(path)!=hashes.get(str(path.resolve()))):
            raise ValueError("Stage07 source SHA mismatch for: "+site)
        print("ORIGINAL SOURCE SHA PASS:",site,flush=True)
    return high, groups, oldsummary, oldwindow,original, dmeta, emeta


def load_tower(spec):
    path=normal_file(spec["primary"])
    raw_header=set(pd.read_csv(path,nrows=0).columns)
    if not {"TIMESTAMP_START","TA_F","VPD_F"}.issubset(raw_header):
        raise ValueError("Selected original meteorology missing required variables")
    cols=["TIMESTAMP_START"]+[x for x in PRIMARY_COLS if x in raw_header]
    df=pd.read_csv(path,usecols=cols,dtype={"TIMESTAMP_START":str},low_memory=False)
    df["native_time"]=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    if df.native_time.duplicated().any() or not df.native_time.is_monotonic_increasing:
        raise ValueError("Original source timestamps not unique and increasing")
    df["T_C"]=numeric(df["TA_F"])
    df["VPD_hPa"]=numeric(df["VPD_F"])
    es=water_es(df["T_C"])
    df["RH_water_pct"]=(es-df["VPD_hPa"])*100.0/es
    df["water_valid"]= (
        df.T_C.between(-80,65) & df.VPD_hPa.between(0,125) &
        df.RH_water_pct.gt(0) & df.RH_water_pct.le(100.05))
    df["TA_QC0"]=numeric(df["TA_F_QC"]).eq(0) if "TA_F_QC" in cols else False
    df["VPD_QC0"]=numeric(df["VPD_F_QC"]).eq(0) if "VPD_F_QC" in cols else False
    df["VPD_only_QC0_valid"]=df.water_valid & df.VPD_QC0
    df["DUAL_QC0_valid"]=df.water_valid & df.TA_QC0 & df.VPD_QC0
    return df,("TA_F_QC" in cols),("VPD_F_QC" in cols)


def metric(frame, condition, reference, side):
    subset=frame.loc[frame[condition]]
    if subset.empty:
        return {
            side+"_count_"+condition:0,
            side+"_closest_"+condition+"_minutes":np.nan,
            side+"_closest_"+condition+"_RH_water_pct":np.nan,
        }
    chosen=subset.iloc[-1] if side=="before" else subset.iloc[0]
    return {
        side+"_count_"+condition:len(subset),
        side+"_closest_"+condition+"_minutes":
            float(abs((chosen.native_time-reference).total_seconds())/60.0),
        side+"_closest_"+condition+"_RH_water_pct":float(chosen.RH_water_pct),
    }


def compute(high,groups,oldsummary,original):
    selected=set(zip(high.site,high.event_cluster_id))
    target=groups.loc[
        [((str(x.site),str(x.cluster)) in selected) for x in groups.itertuples(index=False)]
    ].copy().sort_values(["site","start_local"])
    results=[]
    event_rows=[]
    updated_windows=[]
    for site in sorted(target.site.unique()):
        raw,ta_has_qc,vpd_has_qc=load_tower(original[site])
        if not (ta_has_qc and vpd_has_qc):
            print(f"QC SOURCE MISSING {site}: TA_F_QC={ta_has_qc} VPD_F_QC={vpd_has_qc} "
                  "(missing QC will NOT be treated as QC0)",flush=True)
        step=int(original[site]["native_minutes"])
        site_anchors=high.loc[high.site==site].copy()
        site_anchors["native_time"]=pd.to_datetime(site_anchors.time,errors="raise")
        cols=["native_time","TA_F","VPD_F","T_C","VPD_hPa",
              "RH_water_pct","water_valid","TA_QC0","VPD_QC0",
              "DUAL_QC0_valid","VPD_only_QC0_valid"]
        for col in ("TA_F_QC","VPD_F_QC","PA_F","PA_F_QC","RH","RH_QC","VPD_F_MDS","VPD_F_MDS_QC"):
            if col in raw.columns:cols.append(col)
        events=site_anchors.merge(raw[cols],on="native_time",
                                  how="left",validate="one_to_one")
        if len(events)!=len(site_anchors) or events.T_C.isna().all():
            raise ValueError("Site high-priority original time join failed: "+site)
        if not events.native_time.isin(raw.native_time).all():
            raise ValueError("At least one original source event timestamp missing")
        events["raw_QC0_pair_is_original_label_only"]=True
        events["offset_approved"]=False
        events["forcing_approved"]=False
        event_rows.append(events)
        for r in target.loc[target.site==site].itertuples(index=False):
            start=pd.Timestamp(r.start_local)
            end=pd.Timestamp(r.end_local)
            group_events=events.loc[events.event_cluster_id.eq(r.cluster)]
            if group_events.empty or len(group_events)!=int(r.records) and len(group_events)<int(r.P0_events)+int(r.P1_events) if False else False:
                pass
            if group_events.empty:
                raise ValueError("No high priority records within selected cluster")
            if not (group_events.native_time.between(start,end)).all():
                raise ValueError("Selected high-priority event outside cluster interval")
            window=raw.loc[
                (raw.native_time>=start-pd.Timedelta(hours=24)) &
                (raw.native_time<=end+pd.Timedelta(hours=24))
            ].copy()
            before=window.loc[window.native_time<start]
            after=window.loc[window.native_time>end]
            prior6=oldsummary.loc[
                oldsummary.site.eq(site)&oldsummary.cluster.eq(r.cluster)]
            if len(prior6)!=1:
                raise ValueError("Missing historical Stage10e 6h summary for cluster")
            row={"site":site,"cluster":r.cluster,"start_local":str(start),
                 "end_local":str(end),"native_minutes":step,
                 "high_priority_events":len(group_events),
                 "P0_events":int(group_events.review_priority.str.startswith("P0_").sum()),
                 "P1_events":int(group_events.review_priority.str.startswith("P1_").sum()),
                 "TA_QC_field_available":ta_has_qc,"VPD_QC_field_available":vpd_has_qc,
                 "Stage10e_VPDonly_QC0_both_flanks":str(prior6.iloc[0]["flank_evidence_class"])=="QC0_BOTH_SIDES",
                 "observation_qc_not_proven_independent":True,
                 "decision":"REVIEW_HOLD_NO_FORCING_APPROVAL"}
            for hours in (6,24):
                for side,reference,frame in (("before",start,before),("after",end,after)):
                    near=frame.loc[(reference-frame.native_time).abs()<=pd.Timedelta(hours=hours)]
                    for field in ("water_valid","VPD_only_QC0_valid","DUAL_QC0_valid"):
                        for key,value in metric(near,field,reference,side).items():
                            row[f"{hours}h_{key}"]=value
                    if hours==24:
                        keep=near.copy()
                        keep["site"]=site
                        keep["cluster"]=r.cluster
                        keep["window_side"]=side
                        keep["within_6h"]=(reference-keep.native_time).abs()<=pd.Timedelta(hours=6)
                        updated_windows.append(keep)
            # Stage10e "QC0" counted VPD QC0 only. Independently verify that
            # field matches Stage10e original 6h summary, not new dual-QC0.
            for side in ("before","after"):
                old_count=int(prior6.iloc[0][f"{side}_valid_QC0_T_VPD"])
                new_count=int(row[f"6h_{side}_count_VPD_only_QC0_valid"])
                if new_count!=old_count:
                    raise ValueError(
                        f"Historical Stage10e VPD-only QC0 mismatch {site} {r.cluster} "
                        f"{side}: original={old_count} recalculated={new_count}")
            results.append(row)
        print(f"SITE REVIEW {site}: clusters={sum(target.site==site)} "
              f"TA_QC_column={ta_has_qc} VPD_QC_column={vpd_has_qc}",flush=True)
    result=pd.DataFrame(results).sort_values(["site","start_local"]).reset_index(drop=True)
    detailed=pd.concat(event_rows,ignore_index=True)
    context=pd.concat(updated_windows,ignore_index=True) if updated_windows else pd.DataFrame()
    if len(result)!=19 or len(detailed)!=89 or detailed.duplicated(KEYS).any():
        raise ValueError("19 clusters or 89 high-priority events not preserved")
    for side in ("before","after"):
        for hours in (6,24):
            col=f"{hours}h_{side}_count_DUAL_QC0_valid"
            if col not in result:
                raise ValueError("Missing independent dual-QC0 calculation")
    return result,detailed,context


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE10F — INDEPENDENT DUAL TA/VPD QC0 SOURCE EVIDENCE",flush=True)
    high,groups,oldsummary,oldwindow,sources,dmeta,emeta=evidence()
    results,anchors,context=compute(high,groups,oldsummary,sources)
    b6=(results["6h_before_count_DUAL_QC0_valid"]>0) & (results["6h_after_count_DUAL_QC0_valid"]>0)
    b24=(results["24h_before_count_DUAL_QC0_valid"]>0) & (results["24h_after_count_DUAL_QC0_valid"]>0)
    single24=((results["24h_before_count_DUAL_QC0_valid"]>0) |
              (results["24h_after_count_DUAL_QC0_valid"]>0))
    print("\n========== DUAL-QC0 FLANK EVIDENCE BY SITE ==========")
    summary=results.assign(dual_both_6h=b6,dual_both_24h=b24,dual_one_or_both_24h=single24).groupby("site").agg(
        clusters=("cluster","size"),P0=("P0_events","sum"),P1=("P1_events","sum"),
        dual_both_6h=("dual_both_6h","sum"),
        dual_both_24h=("dual_both_24h","sum"),
        dual_any_24h=("dual_one_or_both_24h","sum")).reset_index()
    print(summary.to_string(index=False),flush=True)
    print(f"\nSTAGE10F SUMMARY: high_priority_events={len(anchors)}/89 "
          f"clusters={len(results)}/19 dual_QC0_both_6h={int(b6.sum())} "
          f"dual_QC0_both_24h={int(b24.sum())} "
          f"dual_QC0_any_24h={int(single24.sum())} "
          f"approved_replacements=0",flush=True)
    print("NOTE: source QC0 does not prove independent measured humidity; "
          "clock metadata, winter physics and gridded elevation still need review.",flush=True)
    if args.check:
        print("CHECK ONLY: no new files/reports, DATM, cases or jobs.")
        return

    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=ROOT/"reports"/("stage10f_dual_qc0_24h_"+tag)
    out.mkdir(exist_ok=False)
    datafiles={
        "19_cluster_dual_QC0_evidence.csv":results,
        "89_high_priority_source_events.csv":anchors,
        "24h_flanking_original_native_records.csv":context,
        "site_QC0_evidence_summary.csv":summary,
    }
    for name,frame in datafiles.items():
        frame.to_csv(out/name,index=False)
    policy={
        "stage10d_report":str(STAGE10D),
        "stage10d_receipt_sha256":checksum(STAGE10D/"read_only_provenance.json"),
        "stage10e_report":str(STAGE10E),
        "stage10e_receipt_sha256":checksum(STAGE10E/"read_only_provenance.json"),
        "source_exact_release":"Stage07 exact_input_manifest.json; source SHA rechecked",
        "selected_events":89,"selected_clusters":19,
        "time_windows_hours":[6,24],
        "science_policy":"Original TA_F_QC==0 AND VPD_F_QC==0 AND water-based TA/VPD physical screen. QC0 provenance not equivalent to independent humidity measurement.",
        "all_clocks_approved":False,"all_replacements_approved":False,
        "no_changes_to_model_sources":True,
        "output_sha256":{name:checksum(out/name) for name in datafiles}
    }
    (out/"read_only_provenance.json").write_text(
        json.dumps(policy,indent=2)+"\n",encoding="utf-8")
    print("STAGE10F REPORT DIR:",out,flush=True)
    print("SCIENTIFIC HOLD: nothing approved or written to forcing.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as ex:
        print("STAGE10F STOP:",str(ex),file=sys.stderr,flush=True)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Batch03 Stage10g-v2 — investigate SOURCE QC0 availability across 7-day windows.

Read-only audit using Stage10f's already pinned Stage07 tower sources and exact
Stage10d high-priority cluster/event ledger. For each of the 19 P0/P1
clusters, report original TA_F/VPD_F joint-QC0 within 24h/72h/7d BEFORE and
AFTER, and distance to nearest joint-QC0 on each side anywhere in release.
Report year-specific QC0 coverage and finite/physically consistent pairs.

CAUTION: QC0 does not establish independence; +/-7 days is for identifying
long QC gaps, NEVER approval to interpolate 7 days. UTC offsets, elevation,
reanalysis dependence and cold-season phase convention remain unapproved.

--check: all validations and calculations, console only (no report writes).
--run: creates ONE new isolated reports/stage10g_* folder containing CSV
diagnostics and SHA receipt. Never modifies original, candidate forcing, DATM,
CIME, Slurm or prior reports. No repair approval.
"""
import argparse
import traceback
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE10D = ROOT/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
STAGE10E = ROOT/"reports/stage10e_priority_flank_context_20261024T043136Z_557ade35"
STAGE10F = ROOT/"reports/stage10f_dual_qc0_24h_20261024T043720Z_8df51a8c"
STAGE10F_SCRIPT = Path(__file__).with_name("10f_dual_qc0_24h_context.py")
EVIDENCE_NAMES = {
    "19_cluster_dual_QC0_evidence.csv",
    "89_high_priority_source_events.csv",
    "24h_flanking_original_native_records.csv",
    "site_QC0_evidence_summary.csv",
}
WINDOWS_H = (24, 72, 168)
VERSION = "stage10g-v2.1-20261024-ast-selftest"


def safe_file(p):
    p = Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/nonregular input: " + str(p))
    return p


def sha256(p):
    h = hashlib.sha256()
    with safe_file(p).open("rb") as stream:
        for b in iter(lambda: stream.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def read_json(p):
    return json.loads(safe_file(p).read_text(encoding="utf-8"))


def import_stage10f():
    safe_file(STAGE10F_SCRIPT)
    spec = importlib.util.spec_from_file_location("batch03_stage10f_dependency", STAGE10F_SCRIPT)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import published Stage10f diagnostic source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance():
    for p in (ROOT, STAGE07, STAGE10D, STAGE10E, STAGE10F):
        if p.is_symlink() or not p.is_dir():
            raise ValueError("Missing/unsafe pinned report directory: " + str(p))
    safe_file(STAGE07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    meta = read_json(STAGE10F/"read_only_provenance.json")
    if (meta.get("selected_events") != 89
        or meta.get("selected_clusters") != 19
        or meta.get("time_windows_hours") != [6,24]
        or meta.get("all_clocks_approved") is not False
        or meta.get("all_replacements_approved") is not False
        or meta.get("no_changes_to_model_sources") is not True
        or Path(meta.get("stage10d_report","")).resolve() != STAGE10D
        or Path(meta.get("stage10e_report","")).resolve() != STAGE10E
        or meta.get("stage10d_receipt_sha256") != sha256(STAGE10D/"read_only_provenance.json")
        or meta.get("stage10e_receipt_sha256") != sha256(STAGE10E/"read_only_provenance.json")
        or set(meta.get("output_sha256",{})) != EVIDENCE_NAMES):
        raise ValueError("Stage10f receipt changed / approval state differs")
    for name in EVIDENCE_NAMES:
        if sha256(STAGE10F/name) != meta["output_sha256"][name]:
            raise ValueError("Stage10f verified output SHA mismatch: "+name)
    previous = pd.read_csv(safe_file(STAGE10F/"19_cluster_dual_QC0_evidence.csv"))
    anchors = pd.read_csv(safe_file(STAGE10F/"89_high_priority_source_events.csv"),
                          dtype={"site":str,"source_csv_row":str,"time":str}, low_memory=False)
    required_10f = {"site", "cluster", "start_local", "end_local",
                    "high_priority_events", "P0_events", "P1_events",
                    "24h_before_count_DUAL_QC0_valid",
                    "24h_after_count_DUAL_QC0_valid"}
    if not required_10f.issubset(previous.columns):
        raise ValueError("Stage10f cluster review lacks required literal columns: " +
                         str(sorted(required_10f - set(previous.columns))))
    if (len(previous) != 19 or previous.cluster.duplicated().any()
            or len(anchors) != 89 or anchors.duplicated(["site","source_csv_row","time"]).any()
            or int(previous.P0_events.sum()) != 31
            or int(previous.P1_events.sum()) != 58):
        raise ValueError("Stage10f event or cluster identity/count changed")
    return previous, anchors, meta


def closest(raw, boundary, side, hours=None):
    if side == "before":
        selected = raw.loc[(raw.native_time < boundary) & raw.DUAL_QC0_valid]
        if hours is not None:
            selected = selected.loc[selected.native_time >= boundary-pd.Timedelta(hours=hours)]
        return (selected.iloc[-1] if not selected.empty else None)
    selected = raw.loc[(raw.native_time > boundary) & raw.DUAL_QC0_valid]
    if hours is not None:
        selected = selected.loc[selected.native_time <= boundary+pd.Timedelta(hours=hours)]
    return (selected.iloc[0] if not selected.empty else None)


def analyse(mod, previous, anchors, original_sources):
    groups = []
    year_rows = []
    for site, target in previous.groupby("site", sort=True):
        spec = original_sources[site]
        raw, ta_qc, vpd_qc = mod.load_tower(spec)
        if not ta_qc or not vpd_qc:
            raise ValueError("Source TA_F_QC and VPD_F_QC both required for "+site)
        step = int(spec["native_minutes"])
        if raw.native_time.diff().dropna().ne(pd.Timedelta(minutes=step)).any():
            raise ValueError("Original full source native clock is not continuous: "+site)
        site_events=anchors.loc[anchors.site==site]
        all_times=set(raw.native_time)
        event_times=pd.to_datetime(site_events.time, errors="raise")
        if len(event_times)!=len(site_events) or not event_times.isin(raw.native_time).all():
            raise ValueError("Stage10f exact high-priority timestamps missing: "+site)
        t_qc = pd.to_numeric(raw["TA_F_QC"], errors="coerce")
        v_qc = pd.to_numeric(raw["VPD_F_QC"], errors="coerce")
        years = sorted(event_times.dt.year.unique())
        for year in years:
            one=raw.loc[raw.native_time.dt.year==year]
            n=len(one)
            ta0 = t_qc.loc[one.index].eq(0)
            v0 = v_qc.loc[one.index].eq(0)
            year_rows.append({
                "site":site,"year":int(year),"native_minutes":step,"source_rows":n,
                "TA_F_QC0":int(ta0.sum()),"VPD_F_QC0":int(v0.sum()),
                "TA_and_VPD_QC0_code_only":int((ta0&v0).sum()),
                "physically_valid_T_VPD":int(one.water_valid.sum()),
                "physically_valid_and_dual_QC0":int(one.DUAL_QC0_valid.sum()),
                "valid_dual_QC0_fraction":float(one.DUAL_QC0_valid.mean()) if n else np.nan,
                "QC0_semantics":"Native source QC0; not a validated independent RH observation"
            })
        # Stage10f columns include names starting with a number (e.g. 24h_*).
        # itertuples() silently renames these, so retain literal column names.
        for _, r in target.iterrows():
            start=pd.Timestamp(r.start_local)
            end=pd.Timestamp(r.end_local)
            parts = site_events.loc[site_events.event_cluster_id==r.cluster]
            if (len(parts)!=int(r.high_priority_events)
                or not pd.to_datetime(parts.time).between(start,end).all()):
                raise ValueError("Stage10f high-priority cluster identities mismatch")
            record={
                "site":site,"cluster":r.cluster,
                "native_minutes":step,"start_local":str(start),"end_local":str(end),
                "P0_events":int(r.P0_events),"P1_events":int(r.P1_events),
                "high_priority_events":len(parts),
                "clock_approved":False,"repair_approved":False,
            }
            for side,boundary in (("before",start),("after",end)):
                all_close=closest(raw,boundary,side)
                record[side+"_nearest_dual_QC0_any_distance_h"]=(
                    float(abs((all_close.native_time-boundary).total_seconds())/3600)
                    if all_close is not None else np.nan)
                record[side+"_nearest_dual_QC0_any_time"]=(
                    str(all_close.native_time) if all_close is not None else "NO_QC0_IN_RELEASE_SIDE")
                for hours in WINDOWS_H:
                    if side=="before":
                        window=raw.loc[(raw.native_time<start)&
                           (raw.native_time>=start-pd.Timedelta(hours=hours))]
                    else:
                        window=raw.loc[(raw.native_time>end)&
                           (raw.native_time<=end+pd.Timedelta(hours=hours))]
                    count=int(window.DUAL_QC0_valid.sum())
                    record[f"{side}_dual_QC0_{hours}h_count"]=count
                    record[f"{side}_VPD_QC0_{hours}h_count"]=int(window.VPD_only_QC0_valid.sum())
                    record[f"{side}_physically_valid_{hours}h_count"]=int(window.water_valid.sum())
                    record[f"{side}_native_rows_{hours}h"]=len(window)
                old_count=int(r[f"24h_{side}_count_DUAL_QC0_valid"])
                if old_count!=record[f"{side}_dual_QC0_24h_count"]:
                    raise ValueError("Stage10g 24h and Stage10f 24h QC0 counts disagree: "+str(r.cluster))
            record["both_sides_24h"]=(
                record["before_dual_QC0_24h_count"]>0 and record["after_dual_QC0_24h_count"]>0)
            record["both_sides_72h"]=(
                record["before_dual_QC0_72h_count"]>0 and record["after_dual_QC0_72h_count"]>0)
            record["both_sides_168h"]=(
                record["before_dual_QC0_168h_count"]>0 and record["after_dual_QC0_168h_count"]>0)
            record["any_side_168h"]=(
                record["before_dual_QC0_168h_count"]>0 or record["after_dual_QC0_168h_count"]>0)
            record["bracketing_QC0_time_gap_days"]=(
                (pd.Timestamp(record["after_nearest_dual_QC0_any_time"])-
                 pd.Timestamp(record["before_nearest_dual_QC0_any_time"])).total_seconds()/86400
                if ("NO_QC0" not in record["after_nearest_dual_QC0_any_time"]
                    and "NO_QC0" not in record["before_nearest_dual_QC0_any_time"]) else np.nan
            )
            record["review_status"]=(
                "BOTH_SIDES_WITHIN_7D_REVIEW_PROVENANCE_NO_INTERPOLATION_APPROVED"
                if record["both_sides_168h"] else
                "ONE_SIDE_WITHIN_7D_NO_LOCAL_BRACKETING"
                if record["any_side_168h"] else
                "NO_VALID_DUAL_QC0_WITHIN_7D_REQUIRE_EXTERNAL_EVIDENCE"
            )
            groups.append(record)
        print("STAGE10G SITE:",site,"clusters=",len(target),
              "source_rows=",len(raw),
              "years=",",".join(map(str,years)),flush=True)
    output=pd.DataFrame(groups).sort_values(["site","start_local"]).reset_index(drop=True)
    annual=pd.DataFrame(year_rows).sort_values(["site","year"]).reset_index(drop=True)
    if (len(output)!=19 or output.high_priority_events.sum()!=89
            or output.P0_events.sum()!=31 or output.P1_events.sum()!=58):
        raise ValueError("Stage10g did not preserve 19 selected clusters and 89 events")
    return output,annual


def self_test():
    """No IRIDIS inputs needed: verify literal 24h_* column access works."""
    rows=pd.DataFrame([{
        "site":"TEST","start_local":"2026-01-01 00:00:00",
        "24h_before_count_DUAL_QC0_valid":4,
        "24h_after_count_DUAL_QC0_valid":7,
    }])
    for _, item in rows.iterrows():
        assert item["24h_before_count_DUAL_QC0_valid"] == 4
        assert item["24h_after_count_DUAL_QC0_valid"] == 7
    # The broken approach is prohibited; its error is replicated by itertuples:
    legacy=next(rows.itertuples(index=False))
    assert not hasattr(legacy, "24h_before_count_DUAL_QC0_valid")
    # Scan only the AST of the scientific analysis function.
    # v2 scanned its own self-test string literal and always flagged itself.
    import ast
    tree=ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions=[node for node in tree.body
               if isinstance(node, ast.FunctionDef) and node.name=="analyse"]
    if len(functions)!=1:
        raise ValueError("Stage10g analysis function missing or duplicated")
    analysis=functions[0]
    target_iterrows=[
        node for node in ast.walk(analysis)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Call)
        and isinstance(node.iter.func, ast.Attribute)
        and node.iter.func.attr=="iterrows"
        and isinstance(node.iter.func.value, ast.Name)
        and node.iter.func.value.id=="target"
    ]
    if len(target_iterrows)!=1:
        raise ValueError("Stage10g analysis must use literal-key-safe target.iterrows()")
    if any(isinstance(node, ast.Call)
           and isinstance(node.func, ast.Name)
           and node.func.id=="getattr"
           for node in ast.walk(analysis)):
        raise ValueError("Stage10g analysis still uses unsafe getattr() field access")
    print(f"STAGE10G SELF-TEST: PASS version={VERSION}",flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    opts=parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--self-test",action="store_true",
                      help="Regression test without any IRIDIS inputs or file writes")
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print(f"STAGE10G — SOURCE QC0 GAP AUDIT — {VERSION}",flush=True)
    print("SCRIPT PATH:",Path(__file__).resolve(),flush=True)
    self_test()
    if args.self_test:
        return
    old,anchors,receipt=provenance()
    prior=import_stage10f()
    high,clusters,_,_,sources,_,_=prior.evidence()
    if (set(zip(anchors.site,anchors.source_csv_row.astype(str),anchors.time.astype(str)))
        != set(zip(high.site,high.source_csv_row.astype(str),high.time.astype(str)))):
        raise ValueError("Stage10f events disagree with pinned Stage10d P0+P1 event keys")
    result,annual=analyse(prior,old,anchors,sources)
    site=result.groupby("site",sort=True).agg(
        clusters=("cluster","size"),P0=("P0_events","sum"),P1=("P1_events","sum"),
        QC0_both_24h=("both_sides_24h","sum"),
        QC0_both_72h=("both_sides_72h","sum"),
        QC0_both_7d=("both_sides_168h","sum"),
        QC0_any_7d=("any_side_168h","sum")
    ).reset_index()
    print("\n========== 19-CLUSTER SOURCE QUALITY SUMMARY ==========")
    print(site.to_string(index=False),flush=True)
    print("\n========== SOURCE QC0 COVERAGE IN AFFECTED YEARS ==========")
    print(annual.to_string(index=False),flush=True)
    print(f"\nSTAGE10G SUMMARY: events=89/89 clusters=19/19 "
          f"both_24h={int(result.both_sides_24h.sum())}/19 "
          f"both_72h={int(result.both_sides_72h.sum())}/19 "
          f"both_7d={int(result.both_sides_168h.sum())}/19 "
          f"any_7d={int(result.any_side_168h.sum())}/19 "
          "scientific_repair_approvals=0",flush=True)
    print("CAUTION: 7-day QC0 presence NEVER permits 7-day humidity interpolation or forced replacement.")
    if args.check:
        print("CHECK ONLY: all checks/calculations read-only; no output changes.",flush=True)
        return
    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=ROOT/"reports"/("stage10g_source_qc0_7day_"+tag)
    out.mkdir(exist_ok=False)
    written={
        "19_cluster_QC0_24_72_168h.csv":result,
        "affected_years_raw_QC_coverage.csv":annual,
        "site_QC0_gap_summary.csv":site,
    }
    for name,frame in written.items():
        frame.to_csv(out/name,index=False)
    r={
        "source_stage10f":str(STAGE10F),
        "source_stage10f_receipt_sha256":sha256(STAGE10F/"read_only_provenance.json"),
        "source_stage10f_script_sha256":sha256(STAGE10F_SCRIPT),
        "original_stage07_manifest_sha256":sha256(STAGE07/"exact_input_manifest.json"),
        "science_gate":"NO TIMES/CLOCKS/REPAIRS APPROVED",
        "selected_events":89,"clusters":19,"window_horizons_hours":list(WINDOWS_H),
        "outputs_sha256":{name:sha256(out/name) for name in written},
        "interpretation":"QC0 may indicate native quality class; not proof of independent humidity measurement. 7d gap review does not authorize interpolation."
    }
    (out/"read_only_provenance.json").write_text(json.dumps(r,indent=2)+"\n")
    print("STAGE10G REPORT DIR:",out)
    print("NO SOURCE, FORCING, QCv5, DATM, CASE OR JOB MODIFICATIONS.")


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("STAGE10G STOP:",str(e),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""AmeriFlux Batch03 Stage10h-v2 — original FLUXMET provenance with timestamp-keyed ERA evidence.

For 1,924 SHA-pinned Stage10d winter humidity blockers, join native timestamps
to the ORIGINAL Stage07-pinned primary FLUXMET/FULLSET and companion ERA5 CSVs.
Count TA_F_QC / VPD_F_QC origin classes 0/1/2 separately at every affected
year and at the exact blocker rows. Numeric availability is never considered
an independent tower observation; companion ERA and ERA5-Land can be related.

For native FLUXNET FLUXMET/FULLSET:
*_F_QC=0 measured; =1 good-quality gapfill; =2 downscaled ERA.
MDS *_F_MDS_QC=0 measured, 1 good, 2 medium, 3 poor quality gapfill.
These labels are **source-product claims**, not a tower-level validation.

--self-test: pure in-memory regression test; no IRIDIS access/writes.
--check: all pinned provenance checks and science analysis; stdout only.
--run: new isolated summary/row CSVs and SHA receipt. No model/forcing edits.

This script never approves clocks, humidity correction, Post-v5, DATM or spinup.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07 = ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S10D = ROOT/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
S10G = ROOT/"reports/stage10g_source_qc0_7day_20261024T045334Z_691519c6"
COUNT = {"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
         "US-MtB":15,"US-NR1":173,"US-NR3":1484}
KEYS = ["site","source_csv_row","time"]
EXPECTED_10D = {
    "all_1924_manual_review.csv","site_triage_summary.csv",
    "consecutive_event_clusters.csv","P0_high_priority_events.csv",
    "B_ice_supersaturation_78.csv","A_water_failure_27.csv"
}
EXPECTED_10G = {
    "19_cluster_QC0_24_72_168h.csv","affected_years_raw_QC_coverage.csv",
    "site_QC0_gap_summary.csv"
}
VERSION="stage10h-v2-20261024-timestamp-keyed"


def required_file(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing/unsafe pinned file: "+str(path))
    return path


def required_dir(path):
    path=Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Missing/unsafe pinned directory: "+str(path))
    return path


def sha(path):
    h=hashlib.sha256()
    with required_file(path).open("rb") as inp:
        for piece in iter(lambda:inp.read(1<<20),b""):
            h.update(piece)
    return h.hexdigest()


def doc(path):
    return json.loads(required_file(path).read_text(encoding="utf-8"))


def numeric(series):
    x=pd.to_numeric(series,errors="coerce")
    return x.where(np.isfinite(x)&(x>-9990))


def qc_counts(df,name):
    q=numeric(df[name])
    return {f"{name}_QC{k}":int(q.eq(k).sum()) for k in (0,1,2)}, {
        f"{name}_other_or_missing":int((~q.isin([0,1,2])).sum())
    }


def counts(df,site,year=None):
    ta=numeric(df["TA_F_QC"])
    vpd=numeric(df["VPD_F_QC"])
    measured=ta.eq(0)&vpd.eq(0)
    source_era=ta.eq(2)&vpd.eq(2)
    v=numeric(df["VPD_F"])
    e=numeric(df["VPD_ERA"])
    finite_pair=np.isfinite(v)&np.isfinite(e)
    v_qc2=vpd.eq(2)&finite_pair
    delta=(v-e).abs()
    match=v_qc2&delta.le(0.01)
    summary={
        "site":site,"rows":len(df),
        "TA_QC0_measured":int(ta.eq(0).sum()),
        "TA_QC1_gapfilled":int(ta.eq(1).sum()),
        "TA_QC2_ERA":int(ta.eq(2).sum()),
        "TA_QC_other_or_missing":int((~ta.isin([0,1,2])).sum()),
        "VPD_QC0_measured":int(vpd.eq(0).sum()),
        "VPD_QC1_gapfilled":int(vpd.eq(1).sum()),
        "VPD_QC2_ERA":int(vpd.eq(2).sum()),
        "VPD_QC_other_or_missing":int((~vpd.isin([0,1,2])).sum()),
        "TA_VPD_both_QC0":int(measured.sum()),
        "TA_VPD_both_QC2":int(source_era.sum()),
        "VPD_QC2_with_finite_companion_ERA":int(v_qc2.sum()),
        "VPD_QC2_close_to_companion_ERA_within_0p01_hPa":int(match.sum()),
        "VPD_QC2_abs_diff_median_hPa":float(delta[v_qc2].median()) if v_qc2.any() else None,
        "source_label_not_independence_proof":True
    }
    if year is not None:
        summary["year"]=int(year)
    for col in ("TA_F_MDS_QC","VPD_F_MDS_QC"):
        if col in df:
            m=numeric(df[col])
            for k in (0,1,2,3):
                summary[f"{col}_{k}"]=int(m.eq(k).sum())
            summary[f"{col}_other_or_missing"]=int((~m.isin([0,1,2,3])).sum())
    return summary


def self_test():
    raw=pd.DataFrame({
        "TIMESTAMP_START":["201701010000","201701010030","201701010100"],
        "TA_F_QC":[0,1,2],"VPD_F_QC":[0,2,2],
        "VPD_F":[1.0,2.0,3.0],"VPD_ERA":[1.1,2.0,3.0]
    })
    result=counts(raw,"US-TEST",2017)
    assert result["VPD_QC0_measured"]==1
    assert result["VPD_QC2_ERA"]==2
    assert result["TA_VPD_both_QC0"]==1
    assert result["TA_VPD_both_QC2"]==1
    assert result["VPD_QC2_close_to_companion_ERA_within_0p01_hPa"]==2
    event=pd.DataFrame({"site":["US-TEST"],"source_csv_row":["2"],"time":["2017-01-01 00:30:00"]})
    raw["native_local"]=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M")
    event["native_local"]=pd.to_datetime(event.time)
    merged=event.merge(raw,on="native_local",how="left",validate="one_to_one",indicator=True)
    assert len(merged)==1 and merged._merge.iloc[0]=="both" and int(merged.VPD_F_QC.iloc[0])==2
    # Regression: ERA starts one native step later and ends one step later.
    # A positional join would silently assign incorrect companion physics.
    primary=pd.DataFrame({
        "TIMESTAMP_START":["201701010000","201701010030","201701010100"],
        "TA_F_QC":[0,1,2],"VPD_F_QC":[0,2,2],
        "VPD_F":[1.,2.,3.]
    })
    era=pd.DataFrame({
        "TIMESTAMP_START":["201701010030","201701010100","201701010130"],
        "TA_ERA":[270.,271.,272.],"VPD_ERA":[20.,30.,40.]
    })
    joined,meta=exact_timestamp_pair(primary,era,"US-TEST",30)
    assert meta["exact_timestamp_matches"]==2
    assert meta["primary_only_timestamps"]==1
    assert meta["ERA_only_timestamps"]==1
    assert pd.isna(joined.loc[0,"VPD_ERA"])
    assert float(joined.loc[1,"VPD_ERA"])==20
    assert float(joined.loc[2,"VPD_ERA"])==30
    assert joined.companion_ERA_timestamp_exact.tolist()==[False,True,True]
    # Completely disjoint UTC/local-looking axes must not be shifted or fused.
    separate=era.copy()
    separate["TIMESTAMP_START"]=["201702010000","201702010030","201702010100"]
    independent,off=exact_timestamp_pair(primary,separate,"US-TEST-NO-OVERLAP",30)
    assert off["exact_timestamp_matches"]==0
    assert independent["VPD_ERA"].isna().all()
    # Duplicates must fail loudly (no many-to-many time merges).
    repeated=era.copy()
    repeated.loc[1,"TIMESTAMP_START"]=repeated.loc[0,"TIMESTAMP_START"]
    try:
        exact_timestamp_pair(primary,repeated,"US-TEST-DUPLICATE",30)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate companion time should be rejected")
    print("STAGE10H SELF-TEST: PASS — QC classes, exact nonpositional timestamp "
          "alignment, disjoint coverage and duplicate rejection")


def verify_upstream():
    for f in (ROOT,S07,S10D,S10G):
        required_dir(f)
    required_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    d=doc(S10D/"read_only_provenance.json")
    g=doc(S10G/"read_only_provenance.json")
    if (d.get("events")!=1924 or d.get("no_replacement_approved") is not True or
        d.get("priorities_are_approval") is not False or
        set(d.get("output_sha256",{}))!=EXPECTED_10D):
        raise ValueError("Stage10d scope or scientific hold changed")
    for f in EXPECTED_10D:
        if sha(S10D/f)!=d["output_sha256"][f]:
            raise ValueError("Stage10d SHA mismatch: "+f)
    if (g.get("selected_events")!=89 or g.get("clusters")!=19 or
        g.get("science_gate")!="NO TIMES/CLOCKS/REPAIRS APPROVED" or
        g.get("window_horizons_hours")!=[24,72,168] or
        set(g.get("outputs_sha256",{}))!=EXPECTED_10G):
        raise ValueError("Stage10g scope/science gate changed")
    for f in EXPECTED_10G:
        if sha(S10G/f)!=g["outputs_sha256"][f]:
            raise ValueError("Stage10g SHA mismatch: "+f)
    if sha(S07/"exact_input_manifest.json")!=g["original_stage07_manifest_sha256"]:
        raise ValueError("Stage07 manifest differs from Stage10g receipt")
    ledger=pd.read_csv(required_file(S10D/"all_1924_manual_review.csv"),
        dtype={k:str for k in KEYS},keep_default_na=False,low_memory=False)
    if (len(ledger)!=1924 or ledger.duplicated(KEYS).any() or
        ledger.site.value_counts().to_dict()!=COUNT or
        ledger.duplicated(["site","time"]).any()):
        raise ValueError("Stage10d 1924 source records or identities have changed")
    subset=ledger.review_priority.astype(str).str.startswith(("P0_","P1_"))
    if (subset.sum()!=89 or
        ledger.review_priority.astype(str).str.startswith("P0_").sum()!=31):
        raise ValueError("Stage10d high priority scope changed")
    group_g=pd.read_csv(S10G/"19_cluster_QC0_24_72_168h.csv")
    if len(group_g)!=19 or group_g.cluster.duplicated().any():
        raise ValueError("Stage10g selected cluster scope changed")
    if (group_g.high_priority_events.sum()!=89 or
        group_g.P0_events.sum()!=31 or group_g.P1_events.sum()!=58):
        raise ValueError("Stage10g priority event scope changed")
    stage07=doc(S07/"exact_input_manifest.json")
    sources={r["site"]:r for r in stage07["sites"]}
    pins={str(Path(p).resolve()):h for p,h in stage07["input_sha256"].items()}
    if len(sources)!=10 or not set(COUNT)<=set(sources):
        raise ValueError("Stage07 exact releases unavailable")
    return ledger,sources,pins


def validate_clock(df,site,kind,step):
    """Validate each immutable input's own exact native timestamp sequence."""
    if "TIMESTAMP_START" not in df:
        raise ValueError(f"{site} {kind} missing TIMESTAMP_START")
    key=df["TIMESTAMP_START"]
    if len(key)==0 or key.isna().any() or not key.astype(str).str.fullmatch(r"\d{12}").all():
        raise ValueError(f"{site} {kind} timestamps absent or not YYYYMMDDHHMM")
    if key.duplicated().any():
        raise ValueError(f"{site} {kind} has duplicate native timestamps")
    dt=pd.to_datetime(key,format="%Y%m%d%H%M",errors="raise")
    if not dt.is_monotonic_increasing or dt.diff().dropna().ne(
            pd.Timedelta(minutes=step)).any():
        raise ValueError(f"{site} {kind} does not have continuous native {step}min chronology")
    return dt


def exact_timestamp_pair(primary,era,site,step):
    """NEVER pair by row number or infer any time shift.

    Primary and companion each pass independent native chronology checks.
    A primary time lacking its precise ERA time is carried with NaN ERA data.
    Companion-only time steps are counted separately; they are not discarded
    from provenance summaries or misused in source event comparisons.
    """
    validate_clock(primary,site,"PRIMARY",step)
    validate_clock(era,site,"ERA",step)
    p0,p1=primary.TIMESTAMP_START.iloc[0],primary.TIMESTAMP_START.iloc[-1]
    e0,e1=era.TIMESTAMP_START.iloc[0],era.TIMESTAMP_START.iloc[-1]
    companion_cols=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
    result=primary.merge(
        era[companion_cols],on="TIMESTAMP_START",how="left",
        sort=False,validate="one_to_one",indicator="_source_era_merge")
    if len(result)!=len(primary) or not result.TIMESTAMP_START.equals(primary.TIMESTAMP_START):
        raise ValueError("Primary source order/identity lost during timestamp-only join")
    result["native_local"]=pd.to_datetime(
        result.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    result["companion_ERA_timestamp_exact"]=result["_source_era_merge"].eq("both")
    for field in ("TA_ERA","VPD_ERA"):
        result[field]=numeric(result[field])
    match=int(result["companion_ERA_timestamp_exact"].sum())
    primary_only=len(primary)-match
    era_only=int((~era.TIMESTAMP_START.isin(primary.TIMESTAMP_START)).sum())
    coverage={
        "site":site,"primary_rows":len(primary),"ERA_rows":len(era),
        "primary_first":p0,"primary_last":p1,"ERA_first":e0,"ERA_last":e1,
        "exact_timestamp_matches":match,"primary_only_timestamps":primary_only,
        "ERA_only_timestamps":era_only,
        "overlap_fraction_primary":float(match/len(primary)),
        "alignment":"EXACT_TIMESTAMP_ONLY_NO_SHIFT",
        "humidity_or_clock_approved":False
    }
    if match==0:
        print(f"STAGE10H CLOCK REVIEW: {site} has ZERO exact primary/ERA "
              "timestamp overlaps. Original QC can still be audited; "
              "ERA comparisons unavailable, no shift assumed.",flush=True)
    elif primary_only or era_only:
        print(f"STAGE10H CLOCK COVERAGE: {site} primary={len(primary)} ERA={len(era)} "
              f"exact={match} primary_only={primary_only} ERA_only={era_only} "
              f"primary={p0}..{p1} ERA={e0}..{e1}",flush=True)
    else:
        print(f"STAGE10H CLOCK COVERAGE: {site} exact={match}/{len(primary)} "
              "both spans identical",flush=True)
    return result,coverage


def read_pinned_data(info,pins):
    paths=[required_file(info["primary"]),required_file(info["era"])]
    for file in paths:
        if pins.get(str(file.resolve()))!=sha(file):
            raise ValueError("Original source SHA mismatch: "+str(file))
        if file.parent.name!=info["release"] or file.parent.parent.name!="raw":
            raise ValueError("Original source is not in expected release folder: "+str(file))
    first,companion=paths
    hdr_primary=set(pd.read_csv(first,nrows=0).columns)
    hdr_era=set(pd.read_csv(companion,nrows=0).columns)
    must1={"TIMESTAMP_START","TA_F_QC","VPD_F_QC","VPD_F"}
    must2={"TIMESTAMP_START","VPD_ERA","TA_ERA"}
    if not must1<=hdr_primary or not must2<=hdr_era:
        raise ValueError("Missing exact required source/ERA fields: "+
            str(must1-hdr_primary)+" "+str(must2-hdr_era))
    optional=["TA_F","TA_F_MDS","TA_F_MDS_QC","VPD_F_MDS","VPD_F_MDS_QC"]
    use1=sorted(must1|({x for x in optional if x in hdr_primary}))
    use2=sorted(must2)
    primary=pd.read_csv(first,usecols=use1,dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(companion,usecols=use2,dtype={"TIMESTAMP_START":str},low_memory=False)
    step=int(info["native_minutes"])
    if step not in (30,60):
        raise ValueError("Unexpected native step")
    return exact_timestamp_pair(primary,era,info["site"],step)


def analyze(ledger,sources,pins):
    summaries=[]
    event_rows=[]
    time_coverage=[]
    for site in sorted(COUNT):
        info=sources[site]
        source,scope=read_pinned_data(info,pins)
        time_coverage.append(scope)
        events=ledger.loc[ledger.site.eq(site),
            ["site","source_csv_row","time","review_priority","event_cluster_id"]].copy()
        events["native_local"]=pd.to_datetime(events.time,errors="raise")
        source["__joined"]=True
        merged=events.merge(source,on="native_local",how="left",validate="one_to_one",indicator=True)
        if (len(merged)!=COUNT[site] or not merged["_merge"].eq("both").all()
            or merged.duplicated(KEYS).any()):
            raise ValueError("Stage10d event timestamps fail one-to-one original-source join: "+site)
        merged=merged.drop(columns=["_merge","__joined"])
        merged["site"]=site
        merged["year"]=merged.native_local.dt.year
        merged["TA_F_QC_raw"]=numeric(merged["TA_F_QC"])
        merged["original_ERA_timestamp_matched"]=merged["companion_ERA_timestamp_exact"].astype(bool)
        merged["VPD_F_QC_raw"]=numeric(merged["VPD_F_QC"])
        merged["TA_source_class"]=merged["TA_F_QC_raw"].map({
             0:"QC0_MEASURED",1:"QC1_GOOD_GAPFILL",2:"QC2_DOWNSCALED_ERA"}).fillna("OTHER_OR_MISSING")
        merged["VPD_source_class"]=merged["VPD_F_QC_raw"].map({
             0:"QC0_MEASURED",1:"QC1_GOOD_GAPFILL",2:"QC2_DOWNSCALED_ERA"}).fillna("OTHER_OR_MISSING")
        merged["VPD_F_minus_companion_ERA_hPa"]=numeric(merged["VPD_F"])-numeric(merged["VPD_ERA"])
        merged["VPD_original_is_measured_QC0"]=merged["VPD_F_QC_raw"].eq(0)
        merged["VPD_original_is_ERA_downscaled_QC2"]=merged["VPD_F_QC_raw"].eq(2)
        merged["TA_original_is_ERA_downscaled_QC2"]=merged["TA_F_QC_raw"].eq(2)
        merged["independently_validated_replacement"]=False
        merged["note"]="QC origin labels do not authorize time offset or humidity replacement"
        event_rows.append(merged)
        years=sorted(merged.year.unique())
        for year in years:
            raw_year=source.loc[source.native_local.dt.year.eq(year)]
            rows=merged.loc[merged.year.eq(year)]
            details=counts(raw_year,site,year)
            flagged=counts(rows,site,year)
            details["source_ERA_exact_timestamp_matched"]=int(raw_year.companion_ERA_timestamp_exact.sum())
            details["source_ERA_exact_timestamp_missing"]=int((~raw_year.companion_ERA_timestamp_exact).sum())
            details["at_blockers_ERA_exact_timestamp_matched"]=int(rows.original_ERA_timestamp_matched.sum())
            details["at_blockers_ERA_exact_timestamp_missing"]=int((~rows.original_ERA_timestamp_matched).sum())
            for key,value in flagged.items():
                if key not in ("site","year","source_label_not_independence_proof"):
                    details["at_blockers_"+key]=value
            details["blocker_events"]=len(rows)
            if site=="US-NR3" and year in (2017,2018,2023):
                if details["TA_QC0_measured"]!=0 or details["VPD_QC0_measured"]!=0:
                    raise ValueError("US-NR3 Stage10g zero-QC0 year mismatch")
            summaries.append(details)
        print(f"STAGE10H ORIGINAL: {site} original_sha_pass=True "
              f"events={len(merged)} affected_years={years} "
              f"VPD_blocker_QC2={int(merged.VPD_original_is_ERA_downscaled_QC2.sum())}",flush=True)
    all_event=pd.concat(event_rows,ignore_index=True).sort_values(KEYS).reset_index(drop=True)
    byyear=pd.DataFrame(summaries).sort_values(["site","year"]).reset_index(drop=True)
    if (len(all_event)!=1924 or all_event.duplicated(KEYS).any() or
        all_event.site.value_counts().to_dict()!=COUNT or
        int(byyear.blocker_events.sum())!=1924 or len(byyear)!=32):
        raise ValueError("Stage10h lost original event rows or affected site-years")
    clock_df=pd.DataFrame(time_coverage).sort_values("site").reset_index(drop=True)
    return all_event,byyear,clock_df


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print(f"STAGE10H — SOURCE FLUXMET/ERA PROVENANCE | {VERSION}",flush=True)
    self_test()
    if args.self_test:
        return
    ledger,sources,pins=verify_upstream()
    events,annual,clock=analyze(ledger,sources,pins)
    print("\n========== PRIMARY vs COMPANION EXACT TIMESTAMP COVERAGE ==========")
    print(clock.to_string(index=False),flush=True)
    print("\n========== SOURCE QC CLASS DISTRIBUTION AT 1,924 BLOCKERS ==========")
    shown=["site","blocker_events","at_blockers_TA_QC0_measured",
           "at_blockers_TA_QC1_gapfilled","at_blockers_TA_QC2_ERA",
           "at_blockers_VPD_QC0_measured","at_blockers_VPD_QC1_gapfilled",
           "at_blockers_VPD_QC2_ERA",
           "at_blockers_ERA_exact_timestamp_matched",
           "at_blockers_ERA_exact_timestamp_missing",
           "at_blockers_VPD_QC2_close_to_companion_ERA_within_0p01_hPa"]
    report=annual.groupby("site",as_index=False)[shown[1:]].sum(numeric_only=True)
    print(report.to_string(index=False),flush=True)
    print("\n========== US-NR3 2017 / 2018 / 2023 FULL-YEAR SOURCE QC ==========")
    important=annual.loc[annual.site.eq("US-NR3")&annual.year.isin([2017,2018,2023])]
    display=["site","year","rows","TA_QC0_measured","TA_QC1_gapfilled",
             "TA_QC2_ERA","VPD_QC0_measured","VPD_QC1_gapfilled",
             "VPD_QC2_ERA","blocker_events","at_blockers_VPD_QC2_ERA"]
    print(important[display].to_string(index=False),flush=True)
    total=int(events.VPD_original_is_ERA_downscaled_QC2.sum())
    event_era_matches=int(events.original_ERA_timestamp_matched.sum())
    event_era_missing=len(events)-event_era_matches
    print(f"\nSTAGE10H SUMMARY: event_join=1924/1924 affected_site_years=32/32 "
          f"VPD_QC2_at_blockers={total}/1924 "
          f"exact_companion_ERA_event_matches={event_era_matches}/1924 "
          f"missing_exact_ERA_events={event_era_missing}/1924 "
          "all_offsets_approved=0 repairs_approved=0",flush=True)
    print("NOTE: VPD_F_QC=2 means source FLUXNET used downscaled ERA; ERA5-Land is not independent.")
    if args.check:
        print("CHECK ONLY: no reports, forcing, DATM, case or Slurm writes.",flush=True)
        return
    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    output=ROOT/"reports"/("stage10h_original_source_provenance_"+tag)
    output.mkdir(exist_ok=False)
    files={
       "original_qc_source_classes_at_1924_blockers.csv":events,
       "affected_years_source_qc_distributions.csv":annual,
       "US-NR3_2017_2018_2023_source_qc.csv":important,
       "site_blocker_source_qc_summary.csv":report,
       "primary_vs_ERA_timestamp_coverage.csv":clock,
    }
    for name,frame in files.items():
        frame.to_csv(output/name,index=False)
    receipt={
        "stage10d_provenance_sha256":sha(S10D/"read_only_provenance.json"),
        "stage10g_provenance_sha256":sha(S10G/"read_only_provenance.json"),
        "stage07_input_manifest_sha256":sha(S07/"exact_input_manifest.json"),
        "selected_events":1924,
        "selected_site_years":32,
        "source_era_alignment":"EXACT_TIMESTAMP_ONLY_NO_POSITIONAL_JOIN_NO_TIME_SHIFT",
        "unmatched_ERA_events":event_era_missing,
        "field_definitions":"FLUXNET *_F_QC0 measured; QC1 gapfilled; QC2 downscaled ERA. MDS QC1 good, QC2 medium and QC3 poor gapfill.",
        "scientific_status":"READ-ONLY SOURCE PROVENANCE; ALL 1924 REPAIRS UNAPPROVED",
        "external_ERA_is_independent":False,
        "output_sha256":{p:sha(output/p) for p in files},
    }
    (output/"read_only_provenance.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE10H REPORT DIR:",output,flush=True)
    print("NO RAW/CANDIDATE FORCING/DATM/CIME/MODEL JOB MODIFICATIONS.")


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10H STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

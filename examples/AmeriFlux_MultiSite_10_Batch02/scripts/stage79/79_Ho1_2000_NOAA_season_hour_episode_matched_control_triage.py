#!/usr/bin/env python3
"""Stage79: source-immutable 2000 Ho1 measured-QC0 winter temperature triage.

After Stage78 checked 505 measured-QC0 original Ho1 2000 cold anomalies,
6,006 source-QC0 same-month non-hard VPD controls and a pinned original
NOAA Bangor year-2000 archive. Stage78's common-483 five-offset check
showed large ~14C NOAA-airport minus Ho1 T discrepancy at ALL trial
clock offsets. This stage does NOT assert sensor bias or release data.

Read only Stage78 SHA-verified 32,555 source-rows across -7,-6,-5,-4,-3;
at the published nominal -5 offset, assess month, three-hour local
clock bin, individual 30min-consecutive source-event episodes, and
exploratory matched controls (same MONTH, local clock +-1 hour,
calendar time +-7 days, native QC0, source non-hard-VPD observations).
A control need not be "correct"; controls may differ in weather,
canopy and local exposure. They are explicitly NOT used as replacement
temperature or an approved calibration model.

Report NOAA report-unique MAE to avoid treating two half-hours reusing
one source report as independent. Same-MONTH/hour-bin diagnostic
balances some seasonal/diurnal confounding but does not prove
station representativeness. No external calls, original/forcing writes
or alteration of original source/clock HOLD status.

--self-test: source-free invariants.
--check: exact Stage78 complete report and NOAA provenance SHA; no writes.
--audit: generate new isolated Stage79 CSV/manifest only.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
UPSTREAM=REPORT/"stage78_Ho1_2000_measured_QC0_NOAA_controls_clock_sensitivity_20261025T180347Z_0a9449e9"
MAIN="Ho1_2000_505_QC0_and_same_month_controls_all_offset_NOAA.csv"
SUMMARY="Ho1_2000_NOAA_temperature_offset_source_unique_summary.csv"
MONTHS="Ho1_2000_NOAA_nominal_month_control_source_unique_summary.csv"
STAGE77_RAW_SHA="2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620"
HOLDS="HOLD_505_QC0"
CONTROLS="SAME_MONTH_MEASURED_QC0_NONHARD_CONTROL"
OFFSETS={-7,-6,-5,-4,-3}
EXPECTED_HOLDS=505
EXPECTED_CONTROLS=6006

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def read_source():
    m=json.loads((UPSTREAM/"stage78_source_science_manifest.json").read_text())
    if ((UPSTREAM/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE78_HO1_2000_505_QC0_NOAA_CONTROL_AND_CLOCK_SENSITIVITY_v1" or
        m.get("n_original_measured_QC0_temperature_delta_HOLD")!=EXPECTED_HOLDS or
        m.get("n_same_calendar_month_QC0_nonhard_humidity_controls")!=EXPECTED_CONTROLS or
        m.get("common_support_all_trial_offsets_original_HOLD_HH")!=483 or
        m.get("NOAA_year2000_source_report_SHA256")!=STAGE77_RAW_SHA or
        m.get("official_BIF_UTC_offset_historical_validity_approved") is not False or
        m.get("source_QC_screener_preserves_original_NOAA_code") is not True or
        m.get("NOAA_airport_not_Ho1_canopy_ground_truth") is not True or
        m.get("absolute_CDS_ERA_temperature_compared_at_off_nominal_offsets") is not False or
        m.get("all_source_Ho1_BZS_16874_original_HOLDs_retained") is not True or
        m.get("all_original_humidity_shadow_15199_numerical_only_unchanged") is not True or
        m.get("prior_stage64_9389_numeric_candidates_untouched") is not True or
        m.get("temperature_change_approved") is not False or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Pinned upstream Stage78 original science status changed")
    expected_files={MAIN,SUMMARY,MONTHS}
    if set(m.get("outputs_SHA256",{}))!=expected_files:
        raise ValueError("Stage78 expected original report files changed")
    for name,digest in m["outputs_SHA256"].items():
        if sha(UPSTREAM/name)!=digest:
            raise ValueError("Stage78 original report SHA mismatch "+name)
    x=pd.read_csv(UPSTREAM/MAIN,dtype={
        "cohort":str,"tower_local_start":str,
        "source_csv_row":str,"noaa_UTC_report":str,
        "noaa_source_station_origin":str},low_memory=False)
    req={"cohort","tower_local_start","source_csv_row","original_T_C",
         "original_T_QC","offset_local_minus_UTC","noaa_pair_status",
         "noaa_UTC_report","noaa_source_station_origin","noaa_airport_T_C",
         "noaa_minus_tower_C","matched_NOAA_source_QC",
         "BIF_historical_UTC_approved","model_T_change_approved",
         "approved_for_DATM"}
    if not req.issubset(x.columns) or len(x)!=(505+6006)*5:
        raise ValueError("Stage78 complete exact source-HH audit rows changed")
    if (not set(x["cohort"])=={HOLDS,CONTROLS} or
        not set(x["offset_local_minus_UTC"])==OFFSETS or
        x.duplicated(["cohort","offset_local_minus_UTC","tower_local_start"]).any() or
        not x["tower_local_start"].str.fullmatch(r"\d{12}").all()):
        raise ValueError("Original native source time/cohort/offest nonunique or malformed")
    x["native_T_QC"]=pd.to_numeric(x["original_T_QC"],errors="raise")
    if not x["native_T_QC"].eq(0).all():
        raise ValueError("Native original Ho1 temperature QC0 controls changed")
    for off in OFFSETS:
        part=x.loc[x["offset_local_minus_UTC"].eq(off)]
        counts=part["cohort"].value_counts().to_dict()
        if counts!={HOLDS:505,CONTROLS:6006}:
            raise ValueError("Stage78 cohort row counts changed at offset "+str(off))
    mask=x["matched_NOAA_source_QC"].astype(str).str.lower().eq("true")
    x["matched"]=mask
    x["local_dt"]=pd.to_datetime(x["tower_local_start"],format="%Y%m%d%H%M",
                                 errors="raise")
    x["month"]=x["local_dt"].dt.month
    x["hour"]=x["local_dt"].dt.hour
    x["hour_bin_3h"]=(x["hour"]//3)*3
    if (set(x.loc[x["cohort"].eq(HOLDS),"month"])!={1,2,3,11,12}
        or set(x.loc[x["cohort"].eq(CONTROLS),"month"])!={1,2,3,11,12}):
        raise ValueError("Ho1 2000 winter source month scope changed")
    if (x["BIF_historical_UTC_approved"].astype(str).str.lower().eq("true").any()
        or x["model_T_change_approved"].astype(str).str.lower().eq("true").any()
        or x["approved_for_DATM"].astype(str).str.lower().eq("true").any()):
        raise ValueError("Upstream original source approval unexpectedly true")
    for col in ("original_T_C","noaa_airport_T_C","noaa_minus_tower_C"):
        x[col]=pd.to_numeric(x[col],errors="coerce")
    if (x["original_T_C"].isna().any()
        or x.loc[mask,["noaa_airport_T_C","noaa_minus_tower_C"]].isna().any().any()
        or not np.allclose(
            x.loc[mask,"noaa_airport_T_C"]-x.loc[mask,"original_T_C"],
            x.loc[mask,"noaa_minus_tower_C"],atol=0.00011,rtol=0)):
        raise ValueError("Recorded source NOAA vs original T mismatch")
    nominal=x.loc[x["offset_local_minus_UTC"].eq(-5)].copy()
    n=nominal.groupby("cohort")["matched"].sum().astype(int).to_dict()
    if n!={HOLDS:498,CONTROLS:5945}:
        raise ValueError("Upstream nominal -5 original NOAA QC coverage changed")
    n_noaa=nominal.loc[nominal["matched"]].groupby(
        "cohort")["noaa_UTC_report"].nunique().to_dict()
    if n_noaa!={HOLDS:306,CONTROLS:3605}:
        raise ValueError("Stage78 original distinct NOAA report counts changed")
    return m,x,nominal

def metric(g):
    q=g.loc[g["matched"]]
    if not len(q):
        return {"matched_source_HH":0,"unique_NOAA_station_reports":0,
                "HH_MAE_C":np.nan,"station_unique_report_equal_MAE_C":np.nan,
                "median_signed_NOAA_minus_Ho1_C":np.nan,
                "QC0_Ho1_T_median_C":np.nan,"NOAA_T_median_C":np.nan}
    grouping=q.groupby("noaa_UTC_report",sort=True)
    weighted=grouping["noaa_minus_tower_C"].apply(lambda z:z.abs().mean())
    return {"matched_source_HH":int(len(q)),
            "unique_NOAA_station_reports":int(len(weighted)),
            "HH_MAE_C":float(q["noaa_minus_tower_C"].abs().mean()),
            "station_unique_report_equal_MAE_C":float(weighted.mean()),
            "median_signed_NOAA_minus_Ho1_C":float(
                q["noaa_minus_tower_C"].median()),
            "QC0_Ho1_T_median_C":float(q["original_T_C"].median()),
            "NOAA_T_median_C":float(q["noaa_airport_T_C"].median())}

def source_strata(nominal):
    entries=[]
    for (cohort,month,bucket),frame in nominal.groupby(
            ["cohort","month","hour_bin_3h"],sort=True):
        entries.append({
           "cohort":cohort,"source_month":int(month),"local_3h_bin_start":int(bucket),
           "n_original_QC0_native_HH":int(len(frame)),
           **metric(frame),"time_historical_approved":False,
           "temperature_correction_approved":False})
    blocks=pd.DataFrame(entries)
    pairs=[]
    for (month,bucket),g in blocks.groupby(["source_month","local_3h_bin_start"]):
        if set(g["cohort"])!={HOLDS,CONTROLS}:continue
        a=g.loc[g.cohort.eq(HOLDS)].iloc[0]
        b=g.loc[g.cohort.eq(CONTROLS)].iloc[0]
        if a["matched_source_HH"]<3 or b["matched_source_HH"]<6:
            continue
        pairs.append({"source_month":int(month),"local_3h_bin_start":int(bucket),
          "hold_QC0_matched_HH":int(a["matched_source_HH"]),
          "control_QC0_matched_HH":int(b["matched_source_HH"]),
          "hold_unique_NOAA_reports":int(a["unique_NOAA_station_reports"]),
          "control_unique_NOAA_reports":int(b["unique_NOAA_station_reports"]),
          "hold_NOAA_minus_Ho1_signed_median_C":float(
                a["median_signed_NOAA_minus_Ho1_C"]),
          "control_NOAA_minus_Ho1_signed_median_C":float(
                b["median_signed_NOAA_minus_Ho1_C"]),
          "hold_minus_control_signed_median_delta_C":float(
                a["median_signed_NOAA_minus_Ho1_C"]-
                b["median_signed_NOAA_minus_Ho1_C"]),
          "descriptive_only_not_independent_seasonal_control":True,
          "approved_for_DATM":False})
    contrasts=pd.DataFrame(pairs)
    print("STAGE79 WINTER MONTH x 3H SOURCE-QC0 STRATA")
    print(blocks.to_string(index=False))
    print("STAGE79 SHARED MONTH-3H BIN DESCRIPTIVE MEDIAN CONTRAST")
    print(contrasts.to_string(index=False) if len(contrasts) else "NO COMMON SPARSE-SUPPORT BINS")
    return blocks,contrasts

def nearby_controls(nominal):
    events=nominal.loc[nominal["cohort"].eq(HOLDS)].sort_values("local_dt")
    control=nominal.loc[nominal["cohort"].eq(CONTROLS)&
                        nominal["matched"]].sort_values("local_dt")
    rows=[]
    # source-event by event nearest same-month contemporaneous, clock-matched
    # controls. Tight calendar/clock tolerance exploratory: no causal attribution.
    for z in events.itertuples(index=False):
        local=z.local_dt
        month=local.month
        elapsed=(control["local_dt"]-local).dt.total_seconds().abs()/86400
        clock=((control["local_dt"].dt.hour*60+
                control["local_dt"].dt.minute)-
                (local.hour*60+local.minute)).abs()
        clock=np.minimum(clock,1440-clock)
        eligible=control.loc[
            control["month"].eq(month)&elapsed.le(7)&clock.le(60)]
        k=eligible["noaa_minus_tower_C"].dropna()
        rows.append({"tower_local_start":z.tower_local_start,
            "source_csv_row":z.source_csv_row,
            "event_NOAA_QC_match":bool(z.matched),
            "event_original_T_C":float(z.original_T_C),
            "event_NOAA_minus_Ho1_C":float(z.noaa_minus_tower_C)
                if bool(z.matched) else np.nan,
            "n_same_month_dayplusminus7_hourplusminus1_QC0_control_HH":int(len(k)),
            "n_distinct_control_NOAA_reports":int(
                 eligible.loc[k.index,"noaa_UTC_report"].nunique()),
            "nearby_control_median_NOAA_minus_Ho1_C":
                float(k.median()) if len(k) else np.nan,
            "event_minus_matched_control_signed_airport_T_delta_C":
                float(z.noaa_minus_tower_C-k.median())
                if len(k) and bool(z.matched) else np.nan,
            "source_airport_not_local_canopy_ground_truth":True,
            "historical_UTC_approved":False,
            "DATM_approved":False})
    out=pd.DataFrame(rows)
    if len(out)!=505 or out["tower_local_start"].duplicated().any():
        raise ValueError("Stage79 505 original events changed during control comparison")
    print("STAGE79 NEARBY 7-DAY, 1-HOUR LOCAL CLOCK QC0 CONTROLS")
    print("WITH_MATCHED_CONTROLS",int(
        out["n_same_month_dayplusminus7_hourplusminus1_QC0_control_HH"].gt(0).sum()),
        "/505")
    supported=out["event_minus_matched_control_signed_airport_T_delta_C"].dropna()
    print("STAGE79 EXPLORATORY WITHIN_LOCAL_WINDOW SIGNED_T_DELTA N",len(supported),
          "MEDIAN_C",round(float(supported.median()),3) if len(supported) else "NA",
          "IQR_C",supported.quantile([.25,.75]).round(3).to_dict() if len(supported) else {})
    return out

def episodes(nominal):
    g=nominal.loc[nominal["cohort"].eq(HOLDS)].sort_values("local_dt").copy()
    g["episode_id"]=(g["local_dt"].diff()!=pd.Timedelta(minutes=30)).cumsum()
    entries=[]
    for ident,part in g.groupby("episode_id"):
        d=part["noaa_minus_tower_C"].dropna()
        entries.append({"episode_id":int(ident),
            "native_local_start":part["tower_local_start"].iloc[0],
            "native_local_end":part["tower_local_start"].iloc[-1],
            "native_QC0_temperature_source_HH":int(len(part)),
            "source_contiguous_hours":float(len(part)/2),
            "source_QC_paired_HH":int(part["matched"].sum()),
            "distinct_NOAA_station_reports":int(
                part.loc[part["matched"],"noaa_UTC_report"].nunique()),
            "NOAA_minus_Ho1_signed_median_C":
                float(d.median()) if len(d) else np.nan,
            "NOAA_minus_Ho1_abs_mean_C":
                float(d.abs().mean()) if len(d) else np.nan,
            "native_time_not_approved":True,
            "T_replacement_not_approved":True})
    out=pd.DataFrame(entries)
    if out["native_QC0_temperature_source_HH"].sum()!=505:
        raise ValueError("Source original Ho1 year-2000 episode total changed")
    out.sort_values("native_QC0_temperature_source_HH",
          ascending=False,inplace=True)
    print("STAGE79 TOP NATIVE QC0 DISAGREEMENT EPISODES")
    print(out.head(35).to_string(index=False))
    return out

def self_test():
    assert EXPECTED_HOLDS==505 and EXPECTED_CONTROLS==6006
    assert OFFSETS=={-7,-6,-5,-4,-3}
    assert 5*(505+6006)==32555
    assert (pd.Timestamp("2000-03-01 12:00")-
            pd.Timestamp("2000-02-23 12:00")).days==7
    t=pd.Series([datetime(2000,1,1,23,30),datetime(2000,1,1,0,30)])
    delta=abs((t.dt.hour*60+t.dt.minute).iloc[0]-
              (t.dt.hour*60+t.dt.minute).iloc[1])
    assert min(delta,1440-delta)==60
    print("STAGE79 SELF-TEST PASS | 505 source QC0 holds, 6006 measured controls, 5 clock offsets, no writes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","audit"):
        group.add_argument("--"+opt,action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    source,all_offsets,nominal=read_source()
    if a.check:
        print("STAGE79 CHECK PASS | upstream original Stage78 NOAA/Ho1 source manifest+CSV SHA, exact 32555 rows; NO WRITES")
        return
    blocks,contrasts=source_strata(nominal)
    controls=nearby_controls(nominal)
    runs=episodes(nominal)
    dest=REPORT/("stage79_Ho1_2000_505_QC0_source_month_hour_episode_control_triage_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    incomplete=dest/"INCOMPLETE_DO_NOT_USE"
    incomplete.write_text("NO NOAA/FLUXNET source changes; no historical UTC/forcing approval.\n")
    files={
      "Ho1_2000_QC0_NOAA_month_3hour_source_strata.csv":blocks,
      "Ho1_2000_QC0_NOAA_same_month_hour_hold_vs_control.csv":contrasts,
      "Ho1_2000_505_QC0_nearby_day_hour_source_controls.csv":controls,
      "Ho1_2000_505_QC0_source_contiguous_episodes.csv":runs}
    outputs={}
    for name,table in files.items():
        loc=dest/name;table.to_csv(loc,index=False);outputs[name]=sha(loc)
    for name,expected in source["outputs_SHA256"].items():
        if sha(UPSTREAM/name)!=expected:
            raise ValueError("Stage78 source changed during Stage79 science output")
    manifest={"schema":"STAGE79_HO1_2000_QC0_NOAA_SEASON_HOUR_EPISODE_SOURCE_TRIAGE_v1",
        "n_original_Ho1_2000_measured_TQC0_discrepancy_HH":505,
        "n_original_same_month_measured_nonhard_controls":6006,
        "nominal_minus_UTC_offset":-5,
        "clock_sensitivity_not_historical_offset_proof":True,
        "station_report_reuse_not_independent_events":True,
        "noaa_airport_not_Ho1_forest_sensor_ground_truth":True,
        "control_nonhard_VPD_not_temperature_calibration_proof":True,
        "matched_source_event_QC0_T_replacements_approved":False,
        "all_16874_original_Ho1_BZS_VPD_hard_source_HOLD":True,
        "previous_humidity_numeric_shadow_15199_unchanged":True,
        "previous_other_stage64_9389_candidates_untouched":True,
        "historical_BIF_UTC_approved":False,
        "approved_for_DATM":False,
        "source_SHA256":{"stage78_manifest":sha(
              UPSTREAM/"stage78_source_science_manifest.json"),
             "stage78_source_ALL_5_offsets":sha(UPSTREAM/MAIN),
             "stage78_NOAA_original_SHA":STAGE77_RAW_SHA},
        "outputs_SHA256":outputs,
        "no_original_FLUXNET_NOAA_ERA5_DATM_CIME_slurm_edits":True}
    (dest/"stage79_source_science_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    incomplete.unlink()
    print("STAGE79 AUDIT PASS | original Ho1 2000 505 QC0 source month/diurnal/episode/nearby-control evidence; no model approval")
    print("REPORT",dest)
    print("NO ORIGINAL SOURCE, NOAA, CDS, STAGE49-78, FORCING, DATM, CIME OR SLURM WRITES")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage13c: full SOURCE-native tower and standalone ERA5 temperature context
for all 24 actual Batch03 Stage13b manual decision records.

Six QC0 tower-TA repair events: print offsets -120,-90,-60,-30,0,+30,+60,
+90,+120 minutes, each with ORIGINAL tower TA/QC, standalone companion
ERA5 TA, and Stage07 selected TA. Every interval is native 30 min.
Also collect full +-120 min tower/ERA/selected context for each of the 18
VPD manual-review events, and print compact center/neighbor temperature
and humidity context. Source files and Stage07 trial are SHA-pinned.

No decisions, new repair values, production approval, CIME/DATM/Slurm changes.
--check prints the report, ZERO WRITES.
--run prints the report and writes only isolated signed review CSV/JSON.
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION="batch03-stage13c-v2-20261026-timestamp-keyed-original-tower-ERA-context"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13B=R/"reports/stage13b_THREE_NUMERIC_SITES_QC0_AND_MANUAL_DECISIONS_20261026T170134Z_06af8b8e"
SITE_PERIODS={"US-MOz":(2004,2021),"US-Mpj":(2008,2025),"US-NC2":(2005,2025)}
SOURCE_CHANGES={"US-MOz":1,"US-Mpj":1,"US-NC2":4}
MANUAL_COUNTS={"US-MOz":0,"US-Mpj":5,"US-NC2":13}
OFFSETS=tuple(range(-120,121,30))
QC0_CSV="THREE_numeric_site_exact_six_original_QC0_edits_TO_DECIDE.csv"
MANUAL_CSV="THREE_site_all_original_manual_review_records_TO_DECIDE.csv"
RECEIPT="stage13b_three_site_decision_SHA_receipt.json"

def valid_file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing or symlink source: "+str(p))
    return p

def sha256(p):
    h=hashlib.sha256()
    with valid_file(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def make_stamp(value):
    x=pd.Timestamp(value)
    if pd.isna(x) or x.tzinfo is not None:
        raise RuntimeError("Unexpected timezone-aware/invalid source native stamp")
    return x

def numeric(src):
    x=pd.to_numeric(src,errors="coerce")
    return x.mask(x<=-9990)

def reader(path,cols,clock_col):
    frame=pd.read_csv(valid_file(path),usecols=cols,
                      dtype={clock_col:str},low_memory=False)
    if clock_col=="TIMESTAMP_START":
        time=pd.to_datetime(frame[clock_col],format="%Y%m%d%H%M",errors="raise")
    else:
        time=pd.to_datetime(frame[clock_col],errors="raise")
    if time.isna().any() or time.duplicated().any():
        raise RuntimeError("Original native time missing or duplicated: "+str(path))
    frame=frame.drop(columns=[clock_col])
    for col in frame.columns:
        frame[col]=numeric(frame[col])
    frame.index=pd.DatetimeIndex(time,name="original_native_time")
    # Stage07 explicitly excludes Feb 29 from the original tower and ERA5
    # sources BEFORE creating its NO_LEAP forcing. Match that selection
    # exactly; keep the raw input files untouched.
    if clock_col=="TIMESTAMP_START":
        feb29=(frame.index.month==2)&(frame.index.day==29)
        frame=frame.loc[~feb29].copy()
    return frame

def selftest():
    assert len(OFFSETS)==9 and OFFSETS[0]==-120 and OFFSETS[-1]==120
    assert sum(SOURCE_CHANGES.values())==6
    assert sum(MANUAL_COUNTS.values())==18
    assert make_stamp("2016-03-17T22:00:00")==pd.Timestamp("2016-03-17 22:00")
    assert pd.Timestamp("2019-01-04 03:30")+pd.Timedelta(minutes=-30)==pd.Timestamp("2019-01-04 03:00")
    # NOAA-style source native axis may contain leap-day source rows;
    # processed Stage07 NO_LEAP axis must not.
    t=pd.to_datetime(["2016-02-28 23:30","2016-02-29 00:00","2016-03-01 00:00"])
    mask=(t.month==2)&(t.day==29)
    assert t[~mask].strftime("%Y-%m-%d").tolist()==["2016-02-28","2016-03-01"]
    one=pd.Series(["-9999","10.75"])
    assert pd.isna(numeric(one).iat[0]) and numeric(one).iat[1]==10.75
    ref=pd.DatetimeIndex(pd.to_datetime(["2020-01-01 00:00","2020-01-01 00:30"]))
    tower_test=pd.DataFrame({"TA_F":[3,4]},index=ref)
    era_test=pd.DataFrame({"TA_ERA":[5,6,7]},index=pd.DatetimeIndex(
        pd.to_datetime(["2019-12-31 23:30","2020-01-01 00:00","2020-01-01 00:30"])))
    assert not tower_test.index.equals(era_test.index)
    assert np.array_equal(era_test.reindex(ref).TA_ERA.to_numpy(),[6,7])
    era_short=pd.DataFrame({"TA_ERA":[6]},index=ref[:1])
    assert pd.isna(era_short.reindex(ref).TA_ERA.iat[1])
    print("STAGE13C SELF-TEST PASS | 6 QC0 +18 VPD; native 30m ±2h; NO WRITES",flush=True)

def preflight():
    receipt=json.loads(valid_file(S13B/RECEIPT).read_text())
    if not (receipt.get("version")=="batch03-stage13b-v2-20261026-empty-manual-ledger-safe"
        and receipt.get("qc0_rows")==6
        and receipt.get("total_manual_ledger_records")==18
        and receipt.get("all_original_QC0_and_manual_science_approved") is False
        and receipt.get("DATM_ready") is False
        and receipt.get("spinup_authorized") is False):
        raise RuntimeError("Exact 6 QC0 / 18 manual source records or science HOLD changed")
    for f in (QC0_CSV,MANUAL_CSV,
              "THREE_site_true_manual_review_summary.csv",
              "THREE_site_manual_review_reason_counts.csv",
              "NO_PRODUCTION_APPROVAL_QC0_OR_MANUAL_HOLDS"):
        if sha256(S13B/f)!=receipt["output_SHA256"].get(f):
            raise RuntimeError("Stage13b source evidence SHA mismatch "+f)
    prior=pd.read_csv(valid_file(S13B/QC0_CSV),dtype={"time":str},low_memory=False)
    man=pd.read_csv(valid_file(S13B/MANUAL_CSV),dtype={"time":str},low_memory=False)
    if (len(prior)!=6 or len(man)!=18 or
        prior.site.value_counts().to_dict()!=SOURCE_CHANGES or
        man.site.value_counts().to_dict()!={s:v for s,v in MANUAL_COUNTS.items() if v}):
        raise RuntimeError("Original six TA QC0 and 18 manual VPD identities changed")
    if not prior.variable.eq("TA_F").all() or not man.variable.eq("VPD_F").all():
        raise RuntimeError("Original manual action scope no longer exact six TA / 18 VPD")
    if pd.to_numeric(prior.official_qc,errors="coerce").ne(0).any():
        raise RuntimeError("Original QC0 central events not marked measured QC0")
    if prior[["site","time"]].duplicated().any() or man[["site","time","variable"]].duplicated().any():
        raise RuntimeError("Duplicate original center time in manual ledger")
    if prior.get("operator_decision",pd.Series([""]*len(prior))).eq("APPROVED").any():
        raise RuntimeError("Original QC0 manually approved unexpectedly")
    selected=json.loads(valid_file(S07/"exact_input_manifest.json").read_text())
    if len(selected.get("sites",[]))!=10:
        raise RuntimeError("Stage07 source manifest not the exact original 10 sites")
    specs={x["site"]:x for x in selected["sites"]}
    if not set(SITE_PERIODS).issubset(specs):
        raise RuntimeError("Stage07 manifest is missing three chosen sites")
    sourcehash={str(Path(p).resolve()):h for p,h in selected["input_sha256"].items()}
    outputs=json.loads(valid_file(S07/"output_sha256.json").read_text())
    if not valid_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"):
        raise RuntimeError("Source Stage07 is no longer marked incomplete")
    return prior,man,specs,sourcehash,outputs

def analyze():
    original,manual,specs,input_sha,output_sha=preflight()
    context=[]
    event_centers=[]
    for site in SITE_PERIODS:
        spec=specs[site]
        if int(spec["native_minutes"])!=30:
            raise RuntimeError("Unexpected non-30min source from selected site "+site)
        for type_ in ("primary","era"):
            source=valid_file(spec[type_])
            if sha256(source)!=input_sha.get(str(source.resolve())):
                raise RuntimeError("Stage07 pinned original "+type_+" source changed "+site)
        start,end=SITE_PERIODS[site]
        selected=S07/site/"forcing"/"processed_v5"/(
            f"{site}_CLM_forcing_{start}_{end}.csv")
        if sha256(selected)!=output_sha.get(str(selected.relative_to(S07))):
            raise RuntimeError("Stage07 selected forcing SHA changed "+site)
        tower=reader(spec["primary"],
                     ["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
                     "TIMESTAMP_START")
        era=reader(spec["era"],
                   ["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                   "TIMESTAMP_START")
        chosen=reader(selected,["time","TA_USE","VPD_USE","QBOT","PSRF"],"time")
        # Source packages may have different temporal extents. Stage07
        # performs timestamp-keyed joins, not full-file index equality.
        # Verify *source-native timestamp identity* on the Stage07 selected
        # NO_LEAP grid and independently preserve any source coverage gap.
        if not chosen.index.is_monotonic_increasing:
            raise RuntimeError("Selected candidate native timeline unordered "+site)
        if chosen.index.has_duplicates:
            raise RuntimeError("Selected candidate native timeline duplicated "+site)
        if not bool(chosen.index.to_series().diff().dt.total_seconds().iloc[1:].isin(
             [1800,1800+86400]).all()):
            raise RuntimeError("Selected candidate NO_LEAP native clock not 30-minute "+site)
        if int(((chosen.index.month==2)&(chosen.index.day==29)).sum())!=0:
            raise RuntimeError("Selected candidate unexpectedly contains leap-day "+site)
        missing_tower=chosen.index.difference(tower.index)
        missing_era=chosen.index.difference(era.index)
        print("STAGE13C SOURCE TIMELINE "+site+
              " | selected="+str(len(chosen))+
              " tower_original="+str(len(tower))+
              " ERA5_original="+str(len(era))+
              " | tower_missing_on_selected="+str(len(missing_tower))+
              " ERA5_missing_on_selected="+str(len(missing_era)),flush=True)
        if len(missing_tower):
            # Stage07 successful sites require the full original measured
            # native source grid; an absent source TIMESTAMP is not a
            # meteorological NaN.
            raise RuntimeError("Original tower missing selected NOLEAP native timestamps "+site+
                               " example="+str(missing_tower[0]))
        tower=tower.reindex(chosen.index)
        era=era.reindex(chosen.index)
        # ERA5 may cover a wider/narrower native source period; absent rows
        # are explicitly NA and never interpolated/re-timed/filled.
        # All required years from original selected manifest; NOLEAP calendars.
        site_events=[("TA_QC0_MODIFIED",e) for e in original.loc[original.site.eq(site)].to_dict("records")]
        site_events += [("VPD_MANUAL_REVIEW",e) for e in manual.loc[manual.site.eq(site)].to_dict("records")]
        for event_idx,(kind,ev) in enumerate(site_events,1):
            center=make_stamp(ev["time"])
            if center not in tower.index:
                raise RuntimeError("Center is not on original source tower clock "+site+":"+str(center))
            rc=tower.loc[center]
            ec=era.loc[center]
            cc=chosen.loc[center]
            era_center_timestamp_present=(center in era.index and
                                          center not in missing_era)
            if not era_center_timestamp_present:
                print("STAGE13C ERA MISSING AT CENTER "+site+" "+str(center)+
                      " | retain as unsupported source provenance",flush=True)
            if kind=="TA_QC0_MODIFIED":
                if rc.TA_F_QC!=0 or not np.isclose(
                    rc.TA_F,float(ev["original_value"]),atol=5e-7,rtol=0):
                    raise RuntimeError("QC0 center original tower value/provenance changed "+site+":"+str(center))
                if not np.isclose(cc.TA_USE,float(ev["final_value"]),atol=5e-7,rtol=0):
                    raise RuntimeError("Center selected repaired tower T differs from original Stage13b "+site)
                if era_center_timestamp_present and not np.isclose(
                    ec.TA_ERA,float(ev["era_reference"]),atol=5e-7,rtol=0):
                    raise RuntimeError("Center paired ERA5 T differs from original Stage13b ERA reference "+site)
            left=center-pd.Timedelta(minutes=30)
            right=center+pd.Timedelta(minutes=30)
            left_t=tower["TA_F"].get(left,np.nan)
            right_t=tower["TA_F"].get(right,np.nan)
            left_era=era["TA_ERA"].get(left,np.nan)
            right_era=era["TA_ERA"].get(right,np.nan)
            centerrow={
                "site":site,"event_kind":kind,"time":str(center),
                "variable":str(ev["variable"]),
                "reason":str(ev.get("reason","")),
                "source_TA_QC0":float(rc.TA_F_QC)==0 if np.isfinite(rc.TA_F_QC) else False,
                "ERA5_center_native_timestamp_present":bool(era_center_timestamp_present),
                "tower_TA_before_minus30_C":left_t,
                "tower_TA_center_C":rc.TA_F,
                "tower_TA_after_plus30_C":right_t,
                "ERA5_TA_before_minus30_C":left_era,
                "ERA5_TA_center_C":ec.TA_ERA,
                "ERA5_TA_after_plus30_C":right_era,
                "candidate_selected_center_TA_C":cc.TA_USE,
                "tower_VPD_center_hPa":rc.VPD_F,
                "ERA5_VPD_center_hPa":ec.VPD_ERA,
                "candidate_VPD_center_hPa":cc.VPD_USE,
                "candidate_QBOT_center_kgkg":cc.QBOT,
                "operator_approved":False,
            }
            if kind=="TA_QC0_MODIFIED":
                centerrow["center_ERA_minus_tower_C"]=ec.TA_ERA-rc.TA_F
                centerrow["tower_center_minus_adjacent_tower_mean_C"]=rc.TA_F-.5*(
                    left_t+
                    right_t)
            event_centers.append(centerrow)
            for offset in OFFSETS:
                stamp=center+pd.Timedelta(minutes=offset)
                available=stamp in chosen.index
                era_available=bool(available and stamp not in missing_era)
                if available:
                    t=tower.loc[stamp]
                    e=era.loc[stamp]
                    v=chosen.loc[stamp]
                else:
                    # A center at the first or last two hours of a release
                    # cannot have both sides; show a clearly labeled NA
                    # rather than fabricate a source halfhour.
                    t=pd.Series({"TA_F":np.nan,"TA_F_QC":np.nan,
                                 "VPD_F":np.nan,"VPD_F_QC":np.nan})
                    e=pd.Series({"TA_ERA":np.nan,"VPD_ERA":np.nan})
                    v=pd.Series({"TA_USE":np.nan,"VPD_USE":np.nan})
                context.append({
                    "original_source_native_row_present":bool(available),
                    "ERA5_source_native_row_present":bool(era_available),
                    "site":site,
                    "event_kind":kind,
                    "event_center":str(center),
                    "event_reason":str(ev.get("reason","")),
                    "offset_minutes":offset,
                    "native_time":str(stamp),
                    "source_tower_TA_C":t.TA_F,
                    "source_tower_TA_F_QC":t.TA_F_QC,
                    "standalone_ERA5_TA_C":e.TA_ERA,
                    "selected_candidate_TA_C":v.TA_USE,
                    "ERA5_minus_tower_TA_C":e.TA_ERA-t.TA_F,
                    "selected_minus_tower_TA_C":v.TA_USE-t.TA_F,
                    "original_tower_VPD_hPa":t.VPD_F,
                    "original_tower_VPD_QC":t.VPD_F_QC,
                    "standalone_ERA5_VPD_hPa":e.VPD_ERA,
                    "selected_candidate_VPD_hPa":v.VPD_USE,
                    "operator_approved":False,
                })
    detail=pd.DataFrame(context)
    centers=pd.DataFrame(event_centers)
    expected=9*(6+18)
    if len(detail)!=expected or len(centers)!=24:
        raise RuntimeError("24 events times 9 native slots mismatch: "+str(len(detail)))
    assert centers.loc[centers.event_kind.eq("TA_QC0_MODIFIED"),"site"].value_counts().to_dict()==SOURCE_CHANGES
    if centers.operator_approved.any() or detail.operator_approved.any():
        raise RuntimeError("Report accidentally approved unvalidated source changes")
    return detail,centers

def presentation(full,centers):
    print("STAGE13C ORIGINAL TA(QC0) CENTERS 6; ADDITIONAL VPD MANUAL CENTERS 18",flush=True)
    print("FIRST: SIX SOURCE-TOWER QC0 SPIKES, 9 NATIVE INTERVALS EACH (-120..+120 MIN)",flush=True)
    fmt=["offset_minutes","native_time","original_source_native_row_present","ERA5_source_native_row_present","source_tower_TA_C","source_tower_TA_F_QC",
         "standalone_ERA5_TA_C","selected_candidate_TA_C",
         "ERA5_minus_tower_TA_C"]
    for _,e in centers.loc[centers.event_kind.eq("TA_QC0_MODIFIED")].iterrows():
        print("\n===",e.site,e.time,"ORIGINAL QC0 T-SPIKE: BEFORE/AFTER TOWER & ERA5 ===",flush=True)
        subset=full.loc[(full.site==e.site)&(full.event_center==e.time)&
                        (full.event_kind=="TA_QC0_MODIFIED")]
        print(subset[fmt].to_string(index=False,float_format=lambda x:f"{x:.3f}"),
              flush=True)
        print("TOWER_MINUS_TWO_NEIGHBOR_MEAN_C",
              round(float(e.tower_center_minus_adjacent_tower_mean_C),3),
              "CENTER_ERA_MINUS_TOWER_C",round(float(e.center_ERA_minus_tower_C),3),flush=True)
    print("\n=== ALL 18 VPD MANUAL RECORDS: TOWER / ERA5 TA AT PREV30, CENTER, NEXT30 ===",flush=True)
    v=centers.loc[centers.event_kind.eq("VPD_MANUAL_REVIEW")]
    cols=["site","time","reason",
        "tower_TA_before_minus30_C","tower_TA_center_C","tower_TA_after_plus30_C",
        "ERA5_TA_before_minus30_C","ERA5_TA_center_C","ERA5_TA_after_plus30_C",
        "tower_VPD_center_hPa","ERA5_VPD_center_hPa","candidate_VPD_center_hPa"]
    print(v[cols].to_string(index=False,float_format=lambda x:f"{x:.3f}"),
          flush=True)
    print("FULL 18 VPD +/-120 MIN CONTEXT INCLUDED IN OUTPUT CSV (NOT TRUNCATED).",flush=True)
    print("NO OPERATOR APPROVAL, NO CHANGE TO QC0 ORIGINAL SOURCE OR DATM.",flush=True)

def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):
        group.add_argument("--"+x,action="store_true")
    a=p.parse_args()
    print("STAGE13C ALL 24 HUMAN REVIEW CENTERS ORIGINAL TOWER+ERA5 T | "+VERSION,flush=True)
    selftest()
    if a.self_test:return
    detail,centers=analyze()
    presentation(detail,centers)
    if a.check:
        print("STAGE13C CHECK ONLY | ZERO FILE WRITES",flush=True)
        return
    out=R/"reports"/("stage13c_24_manual_original_tower_ERA_TA_context_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    filenames={
        "SIX_QC0_temperature_events_full_2h_before_after_tower_ERA5.csv":
           detail.loc[detail.event_kind.eq("TA_QC0_MODIFIED")],
        "EIGHTEEN_VPD_review_events_full_2h_before_after_tower_ERA5.csv":
           detail.loc[detail.event_kind.eq("VPD_MANUAL_REVIEW")],
        "ALL_24_review_center_tower_ERA5_T_and_VPD_summary.csv":centers
    }
    for name,df in filenames.items():
        df.to_csv(out/name,index=False)
    notice="NO_HUMAN_APPROVAL_OR_MODEL_INPUT_UPDATE"
    (out/notice).write_text(
        "Source-native half-hour tower and standalone ERA5 companion "
        "temperatures were read and SHA checked against original Stage07. "
        "The existing selected Stage07 candidate is identified separately. "
        "Six QC0 temperature modifications and eighteen manual humidity "
        "records are NOT automatically approved. No source, clock, case, "
        "forcing, DATM, Slurm, model or PFT modifications.\n")
    receipt={
        "version":VERSION,
        "source_stage13b_SHA256":sha256(S13B/RECEIPT),
        "source_stage07_exact_manifest_SHA256":sha256(
            S07/"exact_input_manifest.json"),
        "source_QC0_T_events":6,"source_manual_VPD_events":18,
        "context_time_interval_minutes":30,
        "window_minutes_before_after":120,
        "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
        "output_SHA256":{f:sha256(out/f) for f in [*filenames,notice]}
    }
    (out/"stage13c_24_manual_original_temperature_context_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13C SOURCE-NATIVE TOWER AND ERA5 CONTEXT DIR:",out,flush=True)
    print("NO ORIGINAL SOURCE, SELECTED MODEL FORCING OR CASE WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as err:
        print("STAGE13C STOP:",err,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

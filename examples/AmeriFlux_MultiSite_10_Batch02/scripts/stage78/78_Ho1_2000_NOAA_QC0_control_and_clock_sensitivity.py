#!/usr/bin/env python3
"""Stage78 — Ho1 2000 original QC0/NOAA sensitivity with same-year controls.

Reuse the EXACT NOAA 2000 file archived in Stage77 (no network); exact Stage77
source events (505 native Ho1 QC0 T vs verified CDS T >8C); exact original
Stage49/70 FLUXNET primary Ho1 file with source SHA; and all Stage74 original
hard-humidity timestamps. The NOAA source is the *Bangor airport* station
~46 km away; its previous legacy source-code QC whitelist is diagnostic.

1. Confirm original native Ho1 physical row/time/TA_F/QC of all 505 events.
2. Compare 505 event temperatures vs independently acquired NOAA Bangor
   source-QC observations by UTC offset sensitivity (-7,-6,-5,-4,-3).
   Use only same-Ho1-event common support across offsets, and do NOT compare
   offset-shifted NOAA to CDS ERA5 (CDS was matched at nominal -5).
3. Construct measured-QC0 source controls from Ho1 2000 original primary
   HH file, EXCLUDING every Stage74 known original VPD hard event (1069),
   restricting to the SAME CALENDAR MONTHS as the 505 hold events.
   Show original-versus-airport differences for both native controls and
   held source episodes; these controls are not independently proven
   temperature sensor calibration or ground truth.
4. Count distinct physical NOAA reports instead of assuming 498 matched HH
   constitute 498 independent weather observations. Source-hourly reuse,
   serial correlation, seasonality, representativeness and historical
   time-offset applicability are all unresolved.
5. Isolated new Stage78 output only, with immutable source SHA gates. No
   source/forcing edits, no temperature replacement or DATM approval.

--self-test: pure selector/timestamp source invariants (no source dependency).
--check: verify exact Stage77/74 and original Stage49 source and archive SHA;
         no network/no write.
--audit: new isolated provenance report; reads source and archived NOAA only.
"""
import argparse
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib, importlib.util, json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
S77=REPORT/"stage77_Ho1_2000_505_QC0_NOAA_Bangor_external_T_context_20261025T094314Z_fa509a05"
S74=REPORT/"stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_20261025T090751Z_d0953fbc"
S61=REPORT/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
FILE77="505_Ho1_2000_QC0_temp_vs_NOAA_original_source.csv"
RAW77="GHCNh_USW00014606_2000_original_source.psv"
FILE74="16874_original_hard_independent_CDS_shadow_refreshed.csv"
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
STAGE40=BASE/"scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py"
BLOB40="8767dbcad2c3c6cd431b37968e867838eac01d87"
NOAA_SHA="2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620"
OFFSETS=(-7,-6,-5,-4,-3)
TARGET=505

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""): h.update(chunk)
    return h.hexdigest()

def blob_id(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Stage40 source unavailable/nonregular")
    data=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def parse_module():
    if blob_id(STAGE40)!=BLOB40:
        raise ValueError("Pinned Stage40 original NOAA QC code differs")
    sp=importlib.util.spec_from_file_location("stage40_source_QC_pinned",STAGE40)
    mod=importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    if mod.STATION!="USW00014606" or mod.ALLOWED!={
         ("223","1"):"ICAO-KBGR",("335","5"):"726088-14606"}:
        raise ValueError("Original NOAA station/QC origin whitelist changed")
    return mod

def sources():
    m77=json.loads((S77/"stage77_source_science_manifest.json").read_text())
    if ((S77/"INCOMPLETE_DO_NOT_USE").exists() or
        m77.get("schema")!="STAGE77_HO1_2000_QC0_NOAA_EXTERNAL_STATION_T_COMPARISON_v1" or
        m77.get("n_original_Ho1_2000_QC0_native_gt8C")!=505 or
        m77.get("n_source_QC_paired_halfhours")!=498 or
        m77.get("NOAA_station_id")!="USW00014606" or
        m77.get("NOAA_raw_sha256")!=NOAA_SHA or
        m77.get("historical_site_UTC_offset_effective_dates_verified") is not False or
        m77.get("automatic_tower_temperature_replacement_approved") is not False or
        m77.get("approved_for_DATM") is not False):
        raise ValueError("Stage77 original archive/science provenance changed")
    for name,digest in m77["output_SHA256"].items():
        if sha(S77/name)!=digest:
            raise ValueError("Original Stage77 archived file SHA changed: "+name)
    if (S77/RAW77).stat().st_size!=10119935:
        raise ValueError("NOAA original 2000 source byte count unexpected")
    m74=json.loads((S74/"stage74_source_science_manifest.json").read_text())
    if ((S74/"INCOMPLETE_DO_NOT_USE").exists() or
        m74.get("schema")!="STAGE74_FOUR_GENUINE_CDS_GAP_RECOVERY_SHADOW_v1" or
        m74.get("original_source_event_count")!=16874 or
        m74.get("current_independent_CDS_verified_gridyears")!=26 or
        m74.get("current_independent_ERA5_numeric_shadow")!=15199 or
        m74.get("current_no_independent_CDS_original_events")!=0 or
        m74.get("approved_for_DATM") is not False):
        raise ValueError("Stage74 full hard humidity science source changed")
    if sha(S74/FILE74)!=m74["outputs_sha256"][FILE74]:
        raise ValueError("Stage74 exact original hard source SHA changed")
    m61=json.loads((S61/"coverage_manifest.json").read_text())
    if (m61.get("schema")!="STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1"
        or m61.get("original_hard_total")!=26332):
        raise ValueError("Stage61 original primary source inventory scope changed")
    m49=json.loads((Path(m61["stage49_source"])/"provenance_and_hold.json").read_text())
    inv=Path(m49["inventory"]).resolve(strict=True)
    if sha(inv)!=m49["inventory_sha256"]:
        raise ValueError("Stage49 original inventory SHA changed")
    spec=[v for v in json.loads(inv.read_text())["completed"]
          if v.get("site")=="US-Ho1" and not str(v.get("source","")).startswith("ERA5")]
    if len(spec)!=1:raise ValueError("Ho1 original primary ambiguous")
    original=spec[0]
    raw=Path(original["file"])
    if (raw.is_symlink() or not raw.is_file()
        or sha(raw)!=original["sha256"] or
        m49["primary_sha256_by_site"].get("US-Ho1")!=original["sha256"]):
        raise ValueError("Original Ho1 FLUXNET HH SHA256 does not match Stage49")
    source=pd.read_csv(S77/FILE77,dtype={"site":str,"tower_local_start":str,
       "source_csv_row":str,"source_sha256":str,"shadow_UTC_START":str},
       low_memory=False)
    if (len(source)!=505 or source["site"].ne("US-Ho1").any() or
        source["tower_local_start"].str[:4].ne("2000").any() or
        source["source_csv_row"].duplicated().any() or
        source["tower_local_start"].duplicated().any() or
        not source["source_sha256"].eq(original["sha256"]).all() or
        source["TA_original_QC"].astype(float).ne(0).any()):
        raise ValueError("Original 505 source identity or measured TA QC0 differs")
    ho1_hard=pd.read_csv(S74/FILE74,usecols=["site","tower_local_start"],
                        dtype=str,low_memory=False)
    ho1_hard=ho1_hard.loc[ho1_hard["site"].eq("US-Ho1") &
          ho1_hard["tower_local_start"].str[:4].eq("2000")]
    if (len(ho1_hard)!=1069 or ho1_hard["tower_local_start"].duplicated().any()
        or not set(source["tower_local_start"])<=set(ho1_hard["tower_local_start"])):
        raise ValueError("Full original Ho1 2000 hard 1069 original timestamp scope changed")
    return source,ho1_hard,original,m49,m61,m74,m77,inv

def read_original_year(spec):
    f=Path(spec["file"])
    ta=spec["columns"]["TA"];qc=spec["qc_columns"]["TA"]
    cols=["TIMESTAMP_START",ta,qc]
    if not set(cols)<=set(pd.read_csv(f,nrows=0).columns):
        raise ValueError("Original Ho1 native TA_F/TA_F_QC/timestamp not in source")
    rows=[];index=0
    for chunk in pd.read_csv(f,usecols=cols,dtype="string",chunksize=120000):
        clock=chunk["TIMESTAMP_START"].str.strip()
        selected=clock.str.startswith("2000",na=False).to_numpy(dtype=bool)
        subset=chunk.loc[selected].copy()
        if len(subset):
            subset["tower_local_start"]=clock.loc[subset.index].astype(str)
            subset["source_csv_row"]=np.arange(index+2,index+2+len(chunk))[selected]
            subset["TA_C"]=pd.to_numeric(subset[ta],errors="coerce")
            subset["TA_QC"]=pd.to_numeric(subset[qc],errors="coerce")
            rows.append(subset[["tower_local_start","source_csv_row","TA_C","TA_QC"]])
        index+=len(chunk)
    if not rows:raise ValueError("Original year 2000 absent from Ho1 primary")
    df=pd.concat(rows,ignore_index=True)
    if (df["tower_local_start"].duplicated().any() or
        not df["tower_local_start"].str.fullmatch(r"\d{12}").all() or
        (df["source_csv_row"]<2).any()):
        raise ValueError("Native Ho1 2000 source row or timestamp invalid")
    return df

def verify_505(source,year):
    q=year.set_index("tower_local_start")
    merged=source.merge(year,on="tower_local_start",how="left",
       suffixes=("_stage77","_original"),validate="one_to_one")
    if len(merged)!=505 or merged["TA_C_original"].isna().any():
        raise ValueError("Ho1 original 505 missing from byte-pinned source")
    if not np.isclose(merged["TA_C_stage77"],merged["TA_C_original"],
        atol=0.00011,rtol=0).all():
        raise ValueError("Ho1 Stage77 measured temperature differs from original primary")
    if not merged["TA_QC"].eq(0).all():
        raise ValueError("Ho1 Stage77 QC0 source differs from actual original primary")
    if not (merged["source_csv_row_stage77"].astype(int).to_numpy()==
             merged["source_csv_row_original"].astype(int).to_numpy()).all():
        raise ValueError("Ho1 Stage77 physical original source CSV row differs")
    return merged

def fast_pick(recs,times,target):
    """Stage40.select exact rule, but avoids O(N) times extraction per pair."""
    i=bisect_left(times,target-timedelta(minutes=30))
    possibilities=[]
    for row in recs[i:]:
        minutes=(row[0]-target).total_seconds()/60
        if minutes>30:break
        if abs(minutes)<=30:possibilities.append((abs(minutes),row))
    if not possibilities:return ("NO_NUMERIC_30MIN",None)
    q=[(t,r) for t,r in possibilities if r[6]]
    if not q:return ("NO_SOURCE_QC_PASS_30MIN",None)
    d=min(t for t,r in q)
    tied=[r for t,r in q if abs(t-d)<1e-8]
    if max(r[1] for r in tied)-min(r[1] for r in tied)>0.001:
        return ("CONFLICTING_EQUIDISTANT_REPORTS",None)
    return ("PROVISIONAL_SOURCE_QC",tied[0])

def compare(frame,recs,times,offset,kind):
    out=[]
    for z in frame.itertuples(index=False):
        local=pd.to_datetime(z.tower_local_start,format="%Y%m%d%H%M")
        utc=(local-pd.Timedelta(hours=offset)).to_pydatetime()
        status,pair=fast_pick(recs,times,utc)
        row={"cohort":kind,"tower_local_start":z.tower_local_start,
         "source_csv_row":str(z.source_csv_row),
         "original_T_C":float(z.TA_C),
         "original_T_QC":float(z.TA_QC),
         "offset_local_minus_UTC":int(offset),
         "noaa_pair_status":status,
         "noaa_UTC_report":"",
         "noaa_source_station_origin":"",
         "noaa_airport_T_C":np.nan,
         "noaa_minus_tower_C":np.nan,
         "matched_NOAA_source_QC":False,
         "BIF_historical_UTC_approved":False,
         "model_T_change_approved":False}
        if pair is not None:
            row.update({
                "noaa_UTC_report":pair[0].isoformat(),
                "noaa_source_station_origin":pair[4],
                "noaa_airport_T_C":float(pair[1]),
                "noaa_minus_tower_C":float(pair[1])-float(z.TA_C),
                "matched_NOAA_source_QC":True})
        out.append(row)
    return pd.DataFrame(out)

def independent_summary(frame):
    k=frame.loc[frame["matched_NOAA_source_QC"]].copy()
    if not len(k):
        return {"pairs":0,"unique_NOAA":0,"station_report_mae":None,
           "pair_mae":None,"median_NOAA_minus_Ho1":None}
    per=k.groupby(["noaa_UTC_report","noaa_source_station_origin"],sort=True)
    # Equal weight per distinct original station report, not per source HH.
    station_mae=per["noaa_minus_tower_C"].apply(lambda s:s.abs().mean())
    return {"pairs":len(k),
            "unique_NOAA":len(station_mae),
            "max_report_reuses":int(per.size().max()),
            "station_report_mae":round(float(station_mae.mean()),3),
            "pair_mae":round(float(k["noaa_minus_tower_C"].abs().mean()),3),
            "median_NOAA_minus_Ho1":round(float(k["noaa_minus_tower_C"].median()),3)}

def diagnose(source,hard,original,mod,raw):
    recs,flags,invalid,nrows=mod.parse_psv(raw,2000)
    if len(recs)!=11355 or sum(r[6] for r in recs)!=11329 or nrows!=11403:
        raise ValueError("Original Stage77 NOAA year-2000 source record population changed")
    times=[r[0] for r in recs]
    if times!=sorted(times):
        raise ValueError("Original NOAA UTC station timestamps nonmonotonic")
    for t in [datetime(2000,1,10,12),datetime(2000,3,8,6),
              datetime(2000,11,2,1)]:
        if mod.select(recs,t)!=fast_pick(recs,times,t):
            raise ValueError("Stage78 optimized nearest source QC selector differs from Stage40")
    year=read_original_year(original)
    verify_505(source,year)
    hard_times=set(hard["tower_local_start"])
    event_times=set(source["tower_local_start"])
    event_months=set(source["tower_local_start"].str.slice(4,6))
    controls=year.loc[
      year["TA_QC"].eq(0) &
      year["TA_C"].between(-80,65,inclusive="neither") &
      ~year["tower_local_start"].isin(hard_times) &
      year["tower_local_start"].str.slice(4,6).isin(event_months)
    ].copy()
    events=year.loc[year["tower_local_start"].isin(event_times)].copy()
    if len(events)!=505:
        raise ValueError("Original Ho1 event 505 physical source T changed")
    print("STAGE78 MEASURED HO1 2000 QC0 native HH all",len(year),
          "same-month non-hard source controls",len(controls),
          "hold events",len(events),
          "event months",sorted(event_months))
    pair_outputs=[]
    summary=[]
    for off in OFFSETS:
        for kind,frame in (("HOLD_505_QC0",events),
                           ("SAME_MONTH_MEASURED_QC0_NONHARD_CONTROL",controls)):
            z=compare(frame,recs,times,off,kind)
            pair_outputs.append(z)
            metric=independent_summary(z)
            summary.append({"offset_local_minus_UTC":off,"cohort":kind,
                "n_native_HH":len(frame),**metric})
            print("STAGE78 OFFSET",off,"COHORT",kind,"METRICS",metric,flush=True)
    all_pairs=pd.concat(pair_outputs,ignore_index=True)
    if len(all_pairs)!=5*(505+len(controls)):
        raise ValueError("Stage78 source original/event offset census failed")
    # Common-support offset comparison: same native tower timestamps at
    # every tested offset, avoiding artificial loss-of-coverage bias.
    hold=all_pairs.loc[all_pairs.cohort.eq("HOLD_505_QC0")].copy()
    pivot=hold.pivot(index="tower_local_start",columns="offset_local_minus_UTC",
                     values="matched_NOAA_source_QC")
    common=set(pivot.index[pivot.all(axis=1)])
    common_rows=hold.loc[hold["tower_local_start"].isin(common)]
    for off,z in common_rows.groupby("offset_local_minus_UTC"):
        metric=independent_summary(z)
        print("STAGE78 STRICT SAME_505_SUPPORT OFFSET",off,
            "COMMON",len(common),"METRICS",metric)
    nominal=hold.loc[hold.offset_local_minus_UTC.eq(-5)]
    if nominal.matched_NOAA_source_QC.sum()!=498:
        raise ValueError("Stage77 source QC match count of 498 not reproduced")
    direct=nominal.loc[nominal.matched_NOAA_source_QC]
    if direct["noaa_UTC_report"].nunique()!=306:
        raise ValueError("Stage77 original 306 distinct NOAA report UTCs not reproduced")
    # Monthly independent NOAA-source report summaries for year-2000 native records
    m=all_pairs.loc[all_pairs.offset_local_minus_UTC.eq(-5)].copy()
    m["tower_month"]=m["tower_local_start"].str[4:6]
    month_summary=[]
    for (kind,month),z in m.groupby(["cohort","tower_month"],sort=True):
        month_summary.append({"cohort":kind,"tower_month":month,
            "original_HH":len(z),**independent_summary(z)})
    month_summary=pd.DataFrame(month_summary)
    sum_summary=pd.DataFrame(summary)
    # Uncertainty: airport data, serially reused reports, weather, source clocks.
    for df in (all_pairs,sum_summary,month_summary):
        if "approved_for_DATM" not in df.columns:
            df["approved_for_DATM"]=False
    return all_pairs,sum_summary,month_summary,len(controls),len(common)

def self_test():
    assert OFFSETS==(-7,-6,-5,-4,-3)
    assert TARGET==505 and NOAA_SHA.startswith("2d5756c1")
    assert datetime(2000,3,1,0,0)-timedelta(hours=-5)==datetime(2000,3,1,5,0)
    # Pandas nullable string masks must be converted to plain bool before
    # indexing a NumPy array of physical source CSV row numbers.
    mask=pd.Series(["200001010000","199912312330"],dtype="string").str.startswith(
        "2000",na=False).to_numpy(dtype=bool)
    assert np.arange(2,4)[mask].tolist()==[2]
    # Optimized nearest selection rejects equidistant disagreement.
    a=(datetime(2000,1,1,0),-3.0,"223","1","ICAO-KBGR","",True)
    b=(datetime(2000,1,1,1),3.0,"223","1","ICAO-KBGR","",True)
    assert fast_pick([a,b],[a[0],b[0]],datetime(2000,1,1,0,30))[0]==(
         "CONFLICTING_EQUIDISTANT_REPORTS")
    print("STAGE78 SELF-TEST PASS | archived NOAA raw SHA, native 505 QC0 and common-support clock offset diagnostics")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","audit"):
        g.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    if args.self_test:return self_test()
    mod=parse_module()
    frame,hard,primary,m49,m61,m74,m77,inventory=sources()
    if args.check:
        print("STAGE78 CHECK PASS | Stage77 archived NOAA and original Stage49/74/77 source SHAs, no network or writes")
        return
    raw=(S77/RAW77).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=NOAA_SHA:
        raise ValueError("NOAA in-memory raw SHA changed during Stage78")
    cases,off,months,n_control,n_common=diagnose(frame,hard,primary,mod,raw)
    target=REPORT/("stage78_Ho1_2000_measured_QC0_NOAA_controls_clock_sensitivity_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    target.mkdir(parents=True,exist_ok=False)
    marker=target/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Independent 2000 airport T source comparison only; no forcing approval.\n")
    outputs={}
    for name,df in {
      "Ho1_2000_505_QC0_and_same_month_controls_all_offset_NOAA.csv":cases,
      "Ho1_2000_NOAA_temperature_offset_source_unique_summary.csv":off,
      "Ho1_2000_NOAA_nominal_month_control_source_unique_summary.csv":months
    }.items():
        p=target/name
        df.to_csv(p,index=False)
        outputs[name]=sha(p)
    if sha(S77/RAW77)!=NOAA_SHA:
        raise ValueError("Archived raw NOAA source changed during original audit")
    manifest={
      "schema":"STAGE78_HO1_2000_505_QC0_NOAA_CONTROL_AND_CLOCK_SENSITIVITY_v1",
      "n_original_measured_QC0_temperature_delta_HOLD":505,
      "n_same_calendar_month_QC0_nonhard_humidity_controls":n_control,
      "common_support_all_trial_offsets_original_HOLD_HH":n_common,
      "NOAA_year2000_source_report_SHA256":NOAA_SHA,
      "official_BIF_UTC_offset_historical_validity_approved":False,
      "source_QC_screener_preserves_original_NOAA_code":True,
      "NOAA_airport_not_Ho1_canopy_ground_truth":True,
      "NOAA_report_reuse_and_serial_correlation_acknowledged":True,
      "absolute_CDS_ERA_temperature_compared_at_off_nominal_offsets":False,
      "all_source_Ho1_BZS_16874_original_HOLDs_retained":True,
      "all_original_humidity_shadow_15199_numerical_only_unchanged":True,
      "prior_stage64_9389_numeric_candidates_untouched":True,
      "temperature_change_approved":False,
      "approved_for_DATM":False,
      "source_SHA256":{
          "stage77_manifest":sha(S77/"stage77_source_science_manifest.json"),
          "stage77_NOAA_archive":sha(S77/RAW77),
          "stage77_original_505":sha(S77/FILE77),
          "stage74_original_hard_fullset":sha(S74/FILE74),
          "stage49_source_inventory":sha(inventory),
          "Ho1_original_FLUXNET_HH":primary["sha256"],
          "stage40_parser_git_blob":BLOB40},
      "outputs_SHA256":outputs,
      "no_original_FLUXNET_CDS_NOAA_DATM_CIME_SLURM_edits":True}
    (target/"stage78_source_science_manifest.json").write_text(
        json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE78 AUDIT PASS | Ho1 2000 505 original measured QC0 source-airport controls and clock sensitivity audited")
    print("REPORT",target)
    print("NO ORIGINAL FLUXNET, NOAA, CDS, STAGE49-77, FORCING, DATM, CIME OR SLURM EDITS")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage80: original Ho1 2000 measured-QC0 cold episodes' true source boundaries.

Stage79 had 505 selected original measured TA_F QC0 Ho1-2000 events in 35
30-minute-consecutive blocks. Jan 300, Feb 73, Mar 115, Nov 8, Dec 9.
Inspect each full episode and 6 hours of original source HH on both sides:
native TA_F/QC, VPD_F/QC, native FLUXNET reanalysis TA_ERA if available,
precisely archived NOAA Bangor airport original QC-screened temperatures.
Summarize 2h BEFORE, first 2h INSIDE, last 2h INSIDE and 2h AFTER every
episode. Distinguish naturally changing cold events from abrupt DATA
switches only as review candidates; no automated source repair.

Scientific gates: SHA-pinned Stage78 source code and original Stage49
primary source inventory; Stage79 report/output SHA; Stage77 original
year-2000 NOAA PSV SHA and historical site -5 nominal shadow.
This is *not* an independent second measured site near Ho1. NOAA/ERA5
may share assimilated weather information, and local forest microclimate
can deviate from the airport ~46 km away. Stage74 15,199 humidity numeric
shadow and all 1,675 temp and 16,874 humidity science HOLDs unchanged.

--self-test: source-free regression.
--check: source SHA and source cohort gates, no output writes/network.
--audit: isolated provenance-checked evidence-only CSV and manifest.
"""
import argparse, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
STAGE78=BASE/"scripts/stage78/78_Ho1_2000_NOAA_QC0_control_and_clock_sensitivity.py"
STAGE78_BLOB="002b6fb491b1d9dd6e570feed31a3c041f0aae2a"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
UPSTREAM=REPORT/"stage79_Ho1_2000_505_QC0_source_month_hour_episode_control_triage_20261025T181238Z_2b6cbd1f"
EPISODES="Ho1_2000_505_QC0_source_contiguous_episodes.csv"
EXPECTED_EPISODES=35
WINDOW_HH=12
BOUNDARY_HH=4
EXPECTED_MONTHLY={1:300,2:73,3:115,11:8,12:9}
SOURCE_NOAA_SHA="2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620"
HARD_T_STATUS="HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()

def blob(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Stage78 pinned source missing or symlinked")
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def get_parent():
    if blob(STAGE78)!=STAGE78_BLOB:
        raise ValueError("Stage78 verified scientific source code changed")
    sp=util.spec_from_file_location("pinned_stage78_original_2000",STAGE78)
    mod=util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod

def old_report():
    m=json.loads((UPSTREAM/"stage79_source_science_manifest.json").read_text())
    if ((UPSTREAM/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE79_HO1_2000_QC0_NOAA_SEASON_HOUR_EPISODE_SOURCE_TRIAGE_v1" or
        m.get("n_original_Ho1_2000_measured_TQC0_discrepancy_HH")!=505 or
        m.get("n_original_same_month_measured_nonhard_controls")!=6006 or
        m.get("nominal_minus_UTC_offset")!=-5 or
        m.get("noaa_airport_not_Ho1_forest_sensor_ground_truth") is not True or
        m.get("all_16874_original_Ho1_BZS_VPD_hard_source_HOLD") is not True or
        m.get("previous_humidity_numeric_shadow_15199_unchanged") is not True or
        m.get("previous_other_stage64_9389_candidates_untouched") is not True or
        m.get("historical_BIF_UTC_approved") is not False or
        m.get("matched_source_event_QC0_T_replacements_approved") is not False or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage79 original science source or HOLD changed")
    for name,digest in m["outputs_SHA256"].items():
        if sha(UPSTREAM/name)!=digest:
            raise ValueError("Stage79 source output SHA256 mismatch "+name)
    d=pd.read_csv(UPSTREAM/EPISODES,dtype={
        "native_local_start":str,"native_local_end":str})
    if (len(d)!=EXPECTED_EPISODES or
        int(d["native_QC0_temperature_source_HH"].sum())!=505 or
        d["episode_id"].duplicated().any()):
        raise ValueError("Stage79 original 35 episode/505 HH source census changed")
    for col in ("native_local_start","native_local_end"):
        if not d[col].str.fullmatch(r"\d{12}").all():
            raise ValueError("Stage79 native episode timestamps malformed")
    return d,m

def original_VPD_context(spec,original_year):
    """Read VPD native values and QC directly, retaining original physical HH timestamps."""
    original=Path(spec["file"])
    col=spec["columns"]["VPD"]
    qc=spec["qc_columns"]["VPD"]
    cols=["TIMESTAMP_START",col,qc]
    optional=["TA_ERA"]
    fields=set(pd.read_csv(original,nrows=0).columns)
    optional=[c for c in optional if c in fields]
    if not set(cols)<=fields:
        raise ValueError("Source Ho1 original TA/VPD pairing absent: "+str(set(cols)-fields))
    found=[]
    for chunk in pd.read_csv(original,usecols=cols+optional,
                             dtype="string",chunksize=120000):
        ts=chunk["TIMESTAMP_START"].str.strip()
        z=chunk.loc[ts.str.startswith("2000",na=False)].copy()
        if not len(z):continue
        z["tower_local_start"]=ts.loc[z.index].astype(str)
        z["original_VPD_F"]=pd.to_numeric(z[col],errors="coerce")
        z["original_VPD_F_QC"]=pd.to_numeric(z[qc],errors="coerce")
        if optional:
            z["original_TA_ERA_C"]=pd.to_numeric(z["TA_ERA"],errors="coerce")
        else:
            z["original_TA_ERA_C"]=np.nan
        found.append(z[["tower_local_start","original_VPD_F",
                        "original_VPD_F_QC","original_TA_ERA_C"]])
    context=pd.concat(found,ignore_index=True)
    if (len(context)!=len(original_year) or
        context.tower_local_start.duplicated().any()):
        raise ValueError("Source year original VPD context not unique/full")
    if set(context.tower_local_start)!=set(original_year.tower_local_start):
        raise ValueError("Source original TA/VPD HH timing changed")
    return context

def checked_input():
    eps,m79=old_report()
    mod78=get_parent()
    events,all_hard,spec,*_=mod78.sources()
    native=mod78.read_original_year(spec)
    if len(native)!=17568:
        raise ValueError("2000 leap-year full 17568 original 30-minute HH changed")
    mod78.verify_505(events,native)
    # This source table is native TA_F and QC, not a modeled or patched forcing.
    hard_at=set(all_hard["tower_local_start"])
    case_at=set(events["tower_local_start"])
    if (len(hard_at)!=1069 or len(case_at)!=505 or
        not case_at<=hard_at):
        raise ValueError("Original Stage74 2000 hard and Stage77 QC0 case cohort changed")
    raw=(mod78.S77/mod78.RAW77)
    if sha(raw)!=SOURCE_NOAA_SHA:
        raise ValueError("Stage77 archived NOAA original weather file mutated")
    if not (mod78.S77/mod78.RAW77).is_file():
        raise ValueError("Stage77 NOAA 2000 original source absent")
    # Compare physical native row span per episode with original 505 events.
    native["native_dt"]=pd.to_datetime(native["tower_local_start"],
              format="%Y%m%d%H%M",errors="raise")
    if not native["native_dt"].is_monotonic_increasing:
        raise ValueError("Original full year native physical HH clock out of order")
    native["original_2000_hard_VPD"]=native["tower_local_start"].isin(hard_at)
    native["original_505_T_QC0_CDS_disagreement"]=native["tower_local_start"].isin(case_at)
    monthly=events["tower_local_start"].str[4:6].astype(int).value_counts().to_dict()
    if monthly!=EXPECTED_MONTHLY:
        raise ValueError("Original original selected source months changed "+str(monthly))
    # Do not silently conflate original source TA_F units with ERA5.
    native=native.merge(original_VPD_context(spec,native),on="tower_local_start",
                        how="left",validate="one_to_one")
    episode_set=set()
    for e in eps.itertuples(index=False):
        a=pd.to_datetime(e.native_local_start,format="%Y%m%d%H%M")
        b=pd.to_datetime(e.native_local_end,format="%Y%m%d%H%M")
        within=native.loc[native.native_dt.between(a,b)]
        if (len(within)!=int(e.native_QC0_temperature_source_HH) or
            not within.original_505_T_QC0_CDS_disagreement.all() or
            not within.TA_QC.eq(0).all()):
            raise ValueError("Original Stage79 continuous 30-min measured QC0 episode differs")
        episode_set.update(within["tower_local_start"])
    if episode_set!=case_at:
        raise ValueError("Stage79 episodes do not partition exact original 505 QC0 source rows")
    return mod78,eps,m79,native

def nearest_noaa(mod78,source):
    # Load the original Stage40 screen with its Git blob checked by Stage78.
    read=mod78.parse_module()
    recs,flags,invalid,nrows=read.parse_psv(
        (mod78.S77/mod78.RAW77).read_bytes(),2000)
    if len(recs)!=11355 or sum(r[6] for r in recs)!=11329 or nrows!=11403:
        raise ValueError("NOAA archival source whitelist population changed")
    times=[r[0] for r in recs]
    rows=[]
    for d in source.itertuples(index=False):
        local=pd.Timestamp(d.native_dt)
        utc=(local+pd.Timedelta(hours=5)).to_pydatetime()
        status,pair=mod78.fast_pick(recs,times,utc)
        rows.append((status,pair[0].isoformat() if pair else "",
             float(pair[1]) if pair else np.nan))
    return rows

def summarise(mod78,eps,native):
    all_src=[]
    ledgers=[]
    for e in eps.itertuples(index=False):
        a=pd.to_datetime(e.native_local_start,format="%Y%m%d%H%M")
        b=pd.to_datetime(e.native_local_end,format="%Y%m%d%H%M")
        win=native.loc[native["native_dt"].between(
             a-pd.Timedelta(minutes=30*WINDOW_HH),
             b+pd.Timedelta(minutes=30*WINDOW_HH))].copy()
        if not len(win):
            raise ValueError("Missing episode original source window")
        win["episode_id"]=int(e.episode_id)
        win["phase"]=np.select([
            win.native_dt.lt(a),win.native_dt.gt(b)
           ],["BEFORE_6H","AFTER_6H"],default="IN_505_HOLD")
        win["source_window_center_original_QC0"]=win["native_dt"].between(a,b)
        if len(win.loc[win.phase.eq("IN_505_HOLD")])!=int(
                  e.native_QC0_temperature_source_HH):
            raise ValueError("Original 505 episode source coverage fails")
        all_src.append(win)
    timeline=pd.concat(all_src,ignore_index=True)
    # Each physical original source HH may appear in more than one episode window.
    # This is deliberate context reuse, not independent observational replication.
    noaa=nearest_noaa(mod78,timeline)
    timeline["NOAA_source_pair_status"]=[q[0] for q in noaa]
    timeline["NOAA_source_UTC_report"]=[q[1] for q in noaa]
    timeline["NOAA_Bangor_original_T_C"]=[q[2] for q in noaa]
    timeline["NOAA_minus_Ho1_original_T_C"]=(
         timeline["NOAA_Bangor_original_T_C"]-timeline["TA_C"])
    timeline["NOAA_UTC_hour_offset_used"]=-5
    timeline["historical_UTC_clock_approved"]=False
    timeline["T_source_change_approved"]=False
    timeline["approved_for_DATM"]=False
    def stats(part):
        p=part.loc[part.TA_QC.eq(0)&part.TA_C.notna()&
            part["NOAA_source_pair_status"].eq("PROVISIONAL_SOURCE_QC")]
        return {"original_QC0_source_HH":int(part.TA_QC.eq(0).sum()),
          "NOAA_source_QC_paired_HH":int(len(p)),
          "distinct_NOAA_reports":int(p.NOAA_source_UTC_report.nunique()),
          "signed_NOAA_minus_Ho1_median_C":
             float(p.NOAA_minus_Ho1_original_T_C.median()) if len(p) else np.nan,
          "original_Ho1_T_median_C":
             float(p.TA_C.median()) if len(p) else np.nan}
    for e in eps.itertuples(index=False):
        chunk=timeline.loc[timeline.episode_id.eq(int(e.episode_id))].copy()
        inside=chunk.loc[chunk.phase.eq("IN_505_HOLD")].sort_values("native_dt")
        before=chunk.loc[chunk.phase.eq("BEFORE_6H")].sort_values("native_dt")
        after=chunk.loc[chunk.phase.eq("AFTER_6H")].sort_values("native_dt")
        first=inside.head(BOUNDARY_HH)
        last=inside.tail(BOUNDARY_HH)
        prev=before.tail(BOUNDARY_HH)
        next_=after.head(BOUNDARY_HH)
        st={"episode_id":int(e.episode_id),
            "native_local_start":str(e.native_local_start),
            "native_local_end":str(e.native_local_end),
            "source_HH":len(inside),
            "source_hours":len(inside)/2,
            "native_start_T_C":float(inside.TA_C.iloc[0]),
            "native_end_T_C":float(inside.TA_C.iloc[-1]),
            "first_before_T_C":float(before.TA_C.iloc[-1]) if len(before) else np.nan,
            "first_after_T_C":float(after.TA_C.iloc[0]) if len(after) else np.nan,
            "start_30min_source_T_jump_C":
               float(inside.TA_C.iloc[0]-before.TA_C.iloc[-1]) if len(before) else np.nan,
            "end_30min_source_T_jump_C":
               float(after.TA_C.iloc[0]-inside.TA_C.iloc[-1]) if len(after) else np.nan,
            "before_2h_source_T_QC":",".join(
               str(int(v)) if pd.notna(v) else "NA" for v in prev.TA_QC),
            "after_2h_source_T_QC":",".join(
               str(int(v)) if pd.notna(v) else "NA" for v in next_.TA_QC),
            "no_unverified_source_T_replacement":True,
            "historical_BIF_UTC_approval":False,
            "DATM_approved":False}
        for tag,data in (("before_2h",prev),("start_2h",first),
                         ("end_2h",last),("after_2h",next_),
                         ("whole_episode",inside)):
            for k,v in stats(data).items():
                st[tag+"_"+k]=v
        def difference(tag_left,tag_right):
            a=st[tag_left+"_signed_NOAA_minus_Ho1_median_C"]
            b=st[tag_right+"_signed_NOAA_minus_Ho1_median_C"]
            return float(b-a) if np.isfinite(a) and np.isfinite(b) else np.nan
        st["start_change_in_signed_NOAA_minus_Ho1_C"]=difference("before_2h","start_2h")
        st["end_change_in_signed_NOAA_minus_Ho1_C"]=difference("end_2h","after_2h")
        st["start_boundary_GT8C_diagnostic_only"]=bool(
            abs(st["start_change_in_signed_NOAA_minus_Ho1_C"])>8) if np.isfinite(
            st["start_change_in_signed_NOAA_minus_Ho1_C"]) else False
        st["end_boundary_GT8C_diagnostic_only"]=bool(
            abs(st["end_change_in_signed_NOAA_minus_Ho1_C"])>8) if np.isfinite(
            st["end_change_in_signed_NOAA_minus_Ho1_C"]) else False
        ledgers.append(st)
    episodes=pd.DataFrame(ledgers)
    if (len(episodes)!=EXPECTED_EPISODES or
        episodes["source_HH"].sum()!=505 or
        not timeline.loc[timeline.phase.eq("IN_505_HOLD"),
                         "original_505_T_QC0_CDS_disagreement"].all()):
        raise ValueError("Stage80 source 505/35 episode closure failed")
    episodes.sort_values(["source_HH","native_local_start"],
                          ascending=[False,True],inplace=True)
    print("STAGE80 ORIGINAL 2000 QC0 SOURCE EPISODES",len(episodes),
          "TOTAL SELECTED HARD-HH",int(episodes.source_HH.sum()))
    print("STAGE80 2h SOURCE T/NOAA BOUNDARY REVIEW TOP 20")
    relevant=["episode_id","native_local_start","native_local_end",
        "source_HH","start_30min_source_T_jump_C",
        "end_30min_source_T_jump_C",
        "before_2h_signed_NOAA_minus_Ho1_median_C",
        "start_2h_signed_NOAA_minus_Ho1_median_C",
        "end_2h_signed_NOAA_minus_Ho1_median_C",
        "after_2h_signed_NOAA_minus_Ho1_median_C",
        "start_change_in_signed_NOAA_minus_Ho1_C",
        "end_change_in_signed_NOAA_minus_Ho1_C"]
    print(episodes[relevant].head(20).to_string(index=False))
    print("STAGE80 NOAA SOURCE BOUNDARY STRONGLY SHIFTED >8C:",
          "START",int(episodes.start_boundary_GT8C_diagnostic_only.sum()),
          "END",int(episodes.end_boundary_GT8C_diagnostic_only.sum()))
    print("STAGE80 ALL 35 ORIGINAL EPISODES AND +/-6H ORIGINAL HH SAVED; NO SOURCE TIME/T MODIFICATION")
    return timeline,episodes

def self_test():
    assert EXPECTED_MONTHLY=={1:300,2:73,3:115,11:8,12:9}
    assert sum(EXPECTED_MONTHLY.values())==505
    assert WINDOW_HH==12 and BOUNDARY_HH==4
    t=pd.Timestamp("2000-03-06 04:00")
    assert (t-pd.Timedelta(minutes=WINDOW_HH*30)).strftime("%Y%m%d%H%M")=="200003052200"
    assert (t+pd.Timedelta(hours=5)).strftime("%Y%m%d%H%M")=="200003060900"
    print("STAGE80 SELF-TEST PASS | 35 original measured QC0 continuous cold episodes, +/-6h, native NOAA source provenance")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","audit"):
        g.add_argument("--"+name,action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    mod78,eps,m79,native=checked_input()
    if a.check:
        print("STAGE80 CHECK PASS | Stage79 output/Stage78 Git/Stage49 FLUXNET/Stage77 NOAA SHA, 505 original QC0, 35 episodes; NO WRITES")
        return
    context,summary=summarise(mod78,eps,native)
    dest=REPORT/("stage80_Ho1_2000_505_QC0_episode_boundary_original_NOAA_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    flag=dest/"INCOMPLETE_DO_NOT_USE"
    flag.write_text("Original source diagnostic only; no time or T approval.\n")
    outputs={}
    files={
        "505_original_QC0_episode_plusminus6h_FLUXNET_NOAA_provenance.csv":context,
        "35_original_QC0_episode_2h_boundary_and_T_shift_review.csv":summary}
    for name,df in files.items():
        path=dest/name;df.to_csv(path,index=False);outputs[name]=sha(path)
    for name,digest in m79["outputs_SHA256"].items():
        if sha(UPSTREAM/name)!=digest:
            raise ValueError("Original Stage79 source changed during write")
    manifest={
        "schema":"STAGE80_HO1_2000_QC0_FLUXNET_NOAA_EPISODE_BOUNDARY_TRIAGE_v1",
        "source_2000_QC0_hard_T_CDS_disagreement_HH":505,
        "n_source_consecutive_episodes":EXPECTED_EPISODES,
        "original_hourly_source_full_2000_HH":17568,
        "month_counts":EXPECTED_MONTHLY,
        "original_stage74_humidity_shadow_15199_untouched":True,
        "original_1675_temperature_HOLDs_unchanged":True,
        "original_16874_humidity_HOLDs_unchanged":True,
        "official_historical_UTC_BIF_effective_date_approved":False,
        "NOAA_airport_not_Ho1_canopy_truth":True,
        "diagnostic_threshold_8C_is_not_sensor_failure_proof":True,
        "native_source_T_replacements_approved":False,
        "approved_for_DATM":False,
        "source_SHA256":{
            "stage79_manifest":sha(UPSTREAM/"stage79_source_science_manifest.json"),
            "stage79_episodes":sha(UPSTREAM/EPISODES),
            "stage78_original_script_git_blob":STAGE78_BLOB,
            "stage77_NOAA_GHCNh_2000_raw_SHA256":SOURCE_NOAA_SHA},
        "outputs_SHA256":outputs,
        "no_existing_FLUXNET_NOAA_CDS_CIME_DATM_forcing_slurm_writes":True}
    (dest/"stage80_source_science_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    flag.unlink()
    print("STAGE80 AUDIT PASS | 35 Ho1 2000 measured QC0 episode boundaries with SHA-verified original NOAA, no forcing approval")
    print("REPORT",dest)
    print("NO ORIGINAL FLUXNET, NOAA, CDS, STAGE49-79, FORCING, DATM, CIME OR SLURM WRITES")
if __name__=="__main__":
    main()

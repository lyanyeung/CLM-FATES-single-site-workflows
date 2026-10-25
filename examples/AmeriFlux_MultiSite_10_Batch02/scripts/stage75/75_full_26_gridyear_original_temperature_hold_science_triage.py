#!/usr/bin/env python3
"""Batch02 Stage75: after 26/26 independent CDS gridyears, triage 1675 source T holds.

SOURCE-IMMUTABLE, READ-ONLY except isolated new report in reports/.
Stage74 established 15199 numerical-only independent CDS water RH/VPD/QBOT
shadow candidates and 998 original non-QC0 TA_F plus 677 QC0-original
tower TA_F versus independent CDS ERA5 2m TA exceeding 8 degrees C.
No source records remain missing independent CDS years.

Do not presume that ERA-derived product TA_ERA and independent CDS t2m
are independent; they may share reanalysis ancestry. Classify first:
  - original TA_F not measured (QC1/QC2/unknown)
  - native measured TA_F QC0 but temperature versus CDS differs >8C
Report original source VPD lineage, original tower TA_F versus native
FLUXNET TA_ERA versus new independently retrieved CDS t2m, year/season,
clusters of consecutive flagged half-hours and exact timestamp rows.
No automatic air-temperature replacement, no arbitrary VPD scaling,
no forced fixes or release of official BIF historical UTC time HOLD.

US-Ho1 1996-2023 FLUXNET original, nominal -5 local standard time;
US-BZS 2010-2024 original, nominal -9 local standard time. Neither
2026 BIF contains a dated historical offset; a source clock audit and
final forcing QA remain separate downstream science decisions.
"""
import argparse,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORTS=ROOT/"reports"
SOURCE=REPORTS/"stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_20261025T090751Z_d0953fbc"
CENSUS="16874_original_hard_independent_CDS_shadow_refreshed.csv"
SOURCE_MANIFEST="stage74_source_science_manifest.json"
STATUS_NUM="SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD"
STATUS_TQC="HOLD_ORIGINAL_TA_QC_NONZERO"
STATUS_TDELTA="HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C"
EXPECTED={STATUS_NUM:15199,STATUS_TQC:998,STATUS_TDELTA:677}
SITES={"US-Ho1":(16788,-5),"US-BZS":(86,-9)}
HOLD=1675

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def input_gate():
    m=json.loads((SOURCE/SOURCE_MANIFEST).read_text())
    if ((SOURCE/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE74_FOUR_GENUINE_CDS_GAP_RECOVERY_SHADOW_v1" or
        m.get("original_source_event_count")!=16874 or
        m.get("previous_Stage73_verified_gridyears")!=22 or
        m.get("current_independent_CDS_verified_gridyears")!=26 or
        m.get("current_independent_ERA5_numeric_shadow")!=15199 or
        m.get("current_no_independent_CDS_original_events")!=0 or
        m.get("remaining_nonzero_TA_QC")!=998 or
        m.get("remaining_tower_ERA_T_gt8C")!=677 or
        m.get("all_original_hard_HOLD_retained") is not True or
        m.get("historic_site_BIF_UTC_applicability_approved") is not False or
        m.get("prior_Stage64_9389_candidates_untouched") is not True or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage74 original 26/26 independently checked science contract changed")
    for name,expected in m["outputs_sha256"].items():
        if sha(SOURCE/name)!=expected:
            raise ValueError("Stage74 output source SHA256 mismatch: "+name)
    types={"site":str,"tower_local_start":str,"shadow_UTC_START":str,
           "timestamp_start":str,"source_sha256":str,"source_csv_row":str}
    x=pd.read_csv(SOURCE/CENSUS,dtype=types,low_memory=False)
    req={"site","tower_local_start","shadow_UTC_START","source_csv_row",
         "source_sha256","science_status","TA_C","TA_original_QC",
         "VPD_original_QC","CDS_ERA5_T2M_C",
         "source_tower_minus_independent_ERA5_T_C","source_TA_ERA_C",
         "CDS_ERA5_RH_water_pct","PA_kPa",
         "historical_BIF_time_source_verified","approved_for_DATM"}
    if not req.issubset(x.columns):
        raise ValueError("Stage74 source necessary original T/ERA columns absent: "+str(req-set(x.columns)))
    if (len(x)!=16874 or Counter(x["site"])!=
        Counter({site:n for site,(n,off) in SITES.items()}) or
        x.duplicated(["site","source_csv_row"]).any() or
        x.duplicated(["site","shadow_UTC_START"]).any() or
        x.duplicated(["site","tower_local_start"]).any() or
        x["science_status"].value_counts().to_dict()!=EXPECTED or
        x["approved_for_DATM"].astype(str).str.lower().eq("true").any() or
        x["historical_BIF_time_source_verified"].astype(str).str.lower().eq("true").any()):
        raise ValueError("Exact original source-row or Stage74 HOLD cohort changed")
    x["tower_dt"]=pd.to_datetime(x["tower_local_start"].str.strip(),
        format="%Y%m%d%H%M",errors="raise")
    x["shadow_utc_dt"]=pd.to_datetime(x["shadow_UTC_START"].str.strip(),
        format="%Y%m%d%H%M",errors="raise")
    for site,(_,offset) in SITES.items():
        part=x.loc[x["site"].eq(site)]
        if not (part["shadow_utc_dt"]-
            part["tower_dt"]).eq(pd.Timedelta(hours=-offset)).all():
            raise ValueError("Stage68 original BIF nominal local->UTC shadow modified: "+site)
    for col in ("TA_C","TA_original_QC","VPD_original_QC",
                "CDS_ERA5_T2M_C","source_TA_ERA_C",
                "source_tower_minus_independent_ERA5_T_C",
                "CDS_ERA5_RH_water_pct","PA_kPa"):
        x[col]=pd.to_numeric(x[col],errors="coerce")
        if col in ("TA_C","CDS_ERA5_T2M_C","source_TA_ERA_C"):
            x[col]=x[col].mask(x[col].le(-9990))
    if (not np.isfinite(x["TA_C"]).all() or
        not np.isfinite(x["CDS_ERA5_T2M_C"]).all() or
        not np.isfinite(x["PA_kPa"]).all()):
        raise ValueError("Verified 26/26 original T/ERA/PA source evidence includes missing values")
    if not np.allclose(
        x["TA_C"]-x["CDS_ERA5_T2M_C"],
        x["source_tower_minus_independent_ERA5_T_C"],
        rtol=0,atol=1.e-5):
        raise ValueError("Stage74 tower-ERA5 temperature delta source discrepancy")
    if not x.loc[x["science_status"].eq(STATUS_TDELTA),"TA_original_QC"].eq(0).all():
        raise ValueError("T-vs-ERA5 source cohort unexpectedly non-QC0")
    if not x.loc[x["science_status"].eq(STATUS_TDELTA),
                 "source_tower_minus_independent_ERA5_T_C"].abs().gt(8).all():
        raise ValueError("T-vs-ERA5 delta HOLD screen no longer >8 C")
    if x.loc[x["science_status"].eq(STATUS_TQC),"TA_original_QC"].eq(0).any():
        raise ValueError("Original TA_F QC-nonzero cohort unexpectedly includes measured QC0")
    if not x.loc[x["science_status"].eq(STATUS_NUM),"TA_original_QC"].eq(0).all():
        raise ValueError("Original numerical source candidates not measured TA QC0")
    return x,m

def case_split(d):
    z=d.copy()
    z["tower_year"]=z["tower_dt"].dt.year
    z["tower_month"]=z["tower_dt"].dt.month
    z["tower_hour"]=z["tower_dt"].dt.hour+z["tower_dt"].dt.minute/60
    z["abs_tower_minus_CDS_ERA5_T_C"]=z[
        "source_tower_minus_independent_ERA5_T_C"].abs()
    z["original_T_minus_FLUXNET_TA_ERA_C"]=z["TA_C"]-z["source_TA_ERA_C"]
    z["FLUXNET_TA_ERA_minus_CDS_ERA5_T_C"]=(
        z["source_TA_ERA_C"]-z["CDS_ERA5_T2M_C"])
    z["FLUXNET_TA_ERA_available"]=z["source_TA_ERA_C"].notna()
    z["FLUXNET_TA_ERA_within3C_of_CDS"]=(
        z["FLUXNET_TA_ERA_available"]&
        z["FLUXNET_TA_ERA_minus_CDS_ERA5_T_C"].abs().le(3))
    z["tower_T_within3C_of_FLUXNET_TA_ERA"]=(
        z["FLUXNET_TA_ERA_available"]&
        z["original_T_minus_FLUXNET_TA_ERA_C"].abs().le(3))
    review=z.loc[z["science_status"].isin([STATUS_TQC,STATUS_TDELTA])].copy()
    if len(review)!=HOLD:
        raise ValueError("Stage75 original unresolved 1675 tower T cohort changed")
    review["diagnostic_context"]=np.select(
        [
          review["science_status"].eq(STATUS_TQC)&
            review["TA_original_QC"].eq(1),
          review["science_status"].eq(STATUS_TQC)&
            review["TA_original_QC"].eq(2),
          review["science_status"].eq(STATUS_TQC),
          review["science_status"].eq(STATUS_TDELTA)&
            review["FLUXNET_TA_ERA_within3C_of_CDS"],
          review["science_status"].eq(STATUS_TDELTA)&
            review["tower_T_within3C_of_FLUXNET_TA_ERA"],
          review["science_status"].eq(STATUS_TDELTA)
        ],[
          "HOLD_TOWER_TA_MDS_QC1_NEEDS_T_SOURCE_ASSESSMENT",
          "HOLD_TOWER_TA_ERA_QC2_NEEDS_T_SOURCE_ASSESSMENT",
          "HOLD_TOWER_TA_OTHER_QC_NEEDS_T_SOURCE_ASSESSMENT",
          "HOLD_QC0_TOWER_DISAGREES_WITH_TWO_ERA_RELATED_T_SOURCES",
          "HOLD_QC0_TOWER_AND_FLUXNET_TA_ERA_AGREE_CDS_DIFFERS",
          "HOLD_QC0_THREE_T_CONTEXT_SOURCES_DISAGREE_OR_ABSENT"
        ],default="HOLD_INTERNAL_CLASSIFICATION_ERROR")
    if review["diagnostic_context"].eq(
            "HOLD_INTERNAL_CLASSIFICATION_ERROR").any():
        raise ValueError("Stage75 original source temperature hold unclassified")
    review["independent_CDS_atmosphere_not_ground_truth"]=True
    review["FLUXNET_TA_ERA_NOT_INDEPENDENT_OF_CDS"]=True
    review["candidate_temperature_source_approved"]=False
    review["approved_for_DATM"]=False
    return z,review

def summarize(all_events,review):
    entries=[]
    for (site,year,status),grp in all_events.groupby(
        ["site","tower_year","science_status"],sort=True):
        d=grp["source_tower_minus_independent_ERA5_T_C"]
        taqc=grp["TA_original_QC"]
        entries.append(dict(
           site=site,original_tower_year=int(year),status=status,
           n_events=int(len(grp)),
           source_T_QC0=int(taqc.eq(0).sum()),
           source_T_QC1=int(taqc.eq(1).sum()),
           source_T_QC2=int(taqc.eq(2).sum()),
           original_VPD_QC1=int(grp["VPD_original_QC"].eq(1).sum()),
           original_VPD_QC2=int(grp["VPD_original_QC"].eq(2).sum()),
           original_T_below0=int(grp["TA_C"].lt(0).sum()),
           tower_minus_CDS_ERA5_T_median_C=float(d.median()),
           tower_minus_CDS_ERA5_T_abs_p90_C=float(d.abs().quantile(.9)),
           FLUXNET_TA_ERA_available=int(grp["FLUXNET_TA_ERA_available"].sum()),
           source_temperature_science_approved=False))
    yearly=pd.DataFrame(entries)
    if yearly["n_events"].sum()!=16874:
        raise ValueError("Stage75 annual status full cohort did not close")
    by_context=(review.groupby(
         ["site","diagnostic_context"],dropna=False)
         .size().reset_index(name="records"))
    if by_context.records.sum()!=1675:
        raise ValueError("Stage75 temperature HOLD diagnostic closure failed")
    episodes=[]
    for (site,status),g in review.groupby(
        ["site","science_status"],sort=True):
        g=g.sort_values("tower_dt")
        starts=(g["tower_dt"].diff()!=pd.Timedelta(minutes=30)).cumsum()
        for _,run in g.groupby(starts,sort=False):
            episodes.append(dict(site=site,original_hold_status=status,
              start_tower_local=str(run["tower_local_start"].iloc[0]),
              end_tower_local=str(run["tower_local_start"].iloc[-1]),
              n_consecutive_source_hold_HH=len(run),
              duration_hours=len(run)*.5,
              original_T_QC0=int(run["TA_original_QC"].eq(0).sum()),
              tower_ERA5_T_diff_median_C=float(
                  run["source_tower_minus_independent_ERA5_T_C"].median()),
              max_abs_tower_ERA5_T_diff_C=float(
                  run["abs_tower_minus_CDS_ERA5_T_C"].max())))
    runs=pd.DataFrame(episodes)
    if len(runs)==0 or runs.n_consecutive_source_hold_HH.sum()!=1675:
        raise ValueError("Stage75 contiguous source HOLD episode closure failed")
    runs=runs.sort_values("n_consecutive_source_hold_HH",
                         ascending=False).reset_index(drop=True)
    print("STAGE75 26/26 ORIGINAL CDS COMPLETE, NO EXTERNAL SOURCE GAP")
    print("STAGE75 SOURCE SCIENCE STATUS",dict(Counter(all_events["science_status"])))
    print("STAGE75 TEMPERATURE HOLD SCIENCE CONTEXT")
    print(by_context.to_string(index=False))
    print("STAGE75 YEAR BY STATUS COUNTS, SOURCE T QC AND ERA5 DIFFERENCES")
    print(yearly.to_string(index=False))
    print("STAGE75 LONGEST CONTIGUOUS ORIGINAL TEMPERATURE HOLD EPISODES")
    print(runs.head(25).to_string(index=False))
    print("STAGE75 NO NUMERICAL T REPLACEMENT OR SOURCE UTC/HISTORICAL BIF APPROVAL")
    return yearly,by_context,runs

def self_test():
    assert sum(EXPECTED.values())==16874
    assert EXPECTED[STATUS_TQC]+EXPECTED[STATUS_TDELTA]==1675
    assert 15199+998+677==16874
    x=pd.Timestamp("2016-01-01 00:00")
    assert (x-pd.Timedelta(hours=-5)).strftime(
        "%Y%m%d%H%M")=="201601010500"
    df=pd.DataFrame({"science_status":[STATUS_TQC,STATUS_TDELTA]})
    assert df["science_status"].isin([STATUS_TQC,STATUS_TDELTA]).sum()==2
    print("STAGE75 SELF-TEST PASS | 26 verified CDS years, 15199 numeric, 998 T_QC, 677 T_delta science holds")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","audit"):
        group.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    if args.self_test:return self_test()
    original,m=input_gate()
    all_events,review=case_split(original)
    yearly,context,runs=summarize(all_events,review)
    if args.check:
        print("STAGE75 CHECK PASS | 1675 source temperature science holds, no source/output writes")
        return
    target=REPORTS/("stage75_1675_original_TA_QC_and_T_vs_CDS_science_triage_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    target.mkdir(parents=True,exist_ok=False)
    marker=target/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Source original T QA only; no forcing/UTC approval.\n")
    files={
       "1675_Ho1_BZS_source_temperature_hold_case_review.csv":review,
       "Ho1_BZS_26year_full_original_science_status.csv":yearly,
       "1675_source_tower_T_context_class_counts.csv":context,
       "1675_original_T_hold_contiguous_HH_episodes.csv":runs}
    outputs={}
    for name,frame in files.items():
        f=target/name
        frame.to_csv(f,index=False)
        outputs[name]=sha(f)
    if sha(SOURCE/CENSUS)!=m["outputs_sha256"][CENSUS]:
        raise ValueError("Original Stage74 source changed while writing science report")
    source_manifest={
       "schema":"STAGE75_HO1_BZS_1675_NATIVE_T_QC_AND_CDS_DELTA_HOLD_TRIAGE_v1",
       "full_ERA5_gridyear_coverage":"26/26",
       "original_total_hard_humidity":16874,
       "numeric_only_humidity_candidates_unchanged":15199,
       "original_T_QC_nonzero_HOLD":998,
       "original_T_vs_CDS_gt8C_HOLD":677,
       "original_source_temperature_HOLD_total":1675,
       "missing_independent_CDS_gridyears":0,
       "prior_Stage64_9389_water_humidity_candidates_unchanged":True,
       "ERA5_temperature_is_not_tower_ground_truth":True,
       "original_FLUXNET_TA_ERA_not_independent_of_CDS":True,
       "original_T_replacements_approved":False,
       "historical_BIF_UTC_offset_coverage_approved":False,
       "DATM_approved":False,"spinup_approved":False,
       "source_SHA256":{
          "stage74_input_original_event_csv":sha(SOURCE/CENSUS),
          "stage74_manifest":sha(SOURCE/SOURCE_MANIFEST)},
       "outputs_SHA256":outputs,
       "no_original_source_CDS_forcing_CIME_slurm_writes":True}
    (target/"stage75_source_science_manifest.json").write_text(
        json.dumps(source_manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE75 AUDIT PASS | 1675 original Ho1/BZS temperature holds classified, 15199 numerical humidity candidates retained")
    print("REPORT",target)
    print("NO ORIGINAL OBS, ERA5, STAGE64-74, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

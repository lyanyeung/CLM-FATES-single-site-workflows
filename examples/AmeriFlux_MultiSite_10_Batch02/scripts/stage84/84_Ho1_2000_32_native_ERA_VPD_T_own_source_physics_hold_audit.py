#!/usr/bin/env python3
"""Stage84: US-Ho1 2000 the 32 VPD_ERA > eswater(TA_ERA) source-HOLD.

Operator Stage83 verified 17,568/17,568 VPD_F == VPD_ERA at original
primary source precision, VPD_F_QC=2 for every HH, 17,294 native TA_F_QC0,
1,068 VPD_ERA>eswater(native TA_F QC0) all physically possible when
paired with original TA_ERA, plus a DIFFERENT 32 rows exceeding
eswater(original TA_ERA); zero overlapped both. All 32 are in January.

Stage84 reads the immutable Stage83 primary-source-aligned full-year
CSV and checks its Git-pinned code, 5 output SHA256, exact 17,568 annual
rows/physical IDs; it independently recomputes both eswater and
saturation-over-ice and inspects raw ERA VPD/T and optional raw MDS,
native tower T, original TA_F_QC, NOAA context (not ground truth).
The implicit RH=100(1-VPD/es) calculation is diagnostic only;
negative RH is not a measured ERA humidity or new observation.

--self-test pure numeric tests.
--check original Stage83 SHA and 32 source cohort: NO WRITES/NETWORK.
--audit new isolated 32-event source ledger, native +/- 6h context
        (source HH may recur in windows), full-year T/source physics
        summary and contiguous 30-min ERA self-inconsistency episodes.
        Original sources, all holds and model forcing never modified.

Temperatures in C; FLUXNET VPD in hPa. All saturation calculations
over water follow previous Stage83 original. Ice sensitivity is
diagnostic, not a replacement for product thermodynamic convention.
"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
OLD=REPORT/"stage83_Ho1_2000_original_VPD_QC2_ERA_T_context_20261025T224055Z_24b5df95"
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
SCRIPT83=BASE/"scripts/stage83/83_Ho1_2000_QC2_ERA_VPD_native_source_provenance_audit.py"
PIN83="8e2bdf99a404ba27dcb8832f734028bb084a8660"
YEAR="17568_native_2000_Ho1_VPD_F_QC2_VPD_ERA_T_ERA_original_lineage.csv"
NOAA_SHA="2d5756c1de9faa1bf4e59cddc24ab39556ae167d602d80859786309601bb3620"
NATIVE=17568
N_SELF=32
N_MEASURED=17294
N_MISMATCH=1068
N_MISRECONCILED=1068

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def blob(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Original Stage83 source code missing/symlinked")
    data=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def saturation_water(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def saturation_ice(t):
    return 6.112*np.exp(22.46*t/(t+272.62))

def input_gate():
    if blob(SCRIPT83)!=PIN83:
        raise ValueError("Stage83 Git source blob changed")
    if (OLD/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage83 science audit output incomplete")
    m=json.loads((OLD/"stage83_source_science_manifest.json").read_text())
    assert_fields={
        "schema":"STAGE83_HO1_2000_PRIMARY_VPD_QC2_ERA_T_PROVENANCE_v1",
        "original_source_HH":NATIVE,
        "source_VPD_F_QC2_ERA_downscaled_HH":NATIVE,
        "original_measured_T_QC0_HH":N_MEASURED,
        "original_NOAA_QC_matched_T_HH":17140,
        "native_QC0_VPD_gt_eswater_source_HH":N_MISMATCH,
        "source_VPD_ERA_column_present":True,
        "source_VPD_F_MDS_column_present":True,
        "ERA_VPD_not_independent_tower_observation":True,
        "NOAA_not_forest_canopy_truth":True,
        "original_temperature_source_replacement_approved":False,
        "original_VPD_source_replacement_approved":False,
        "historical_BIF_UTC_offset_approved":False,
        "approved_for_DATM":False,
        "original_16874_Ho1_BZS_hard_HOLD_unchanged":True,
        "original_15199_humidity_shadow_numerical_only_unchanged":True,
        "original_1675_temperature_HOLD_unchanged":True,
        "prior_stage64_9389_other_candidates_untouched":True
    }
    for key,val in assert_fields.items():
        if m.get(key)!=val:
            raise ValueError("Stage83 immutable science contract changed: "+key)
    if (m.get("source_SHA256",{}).get("stage82_script_git_blob")!=
        "cf4cbfcf80004548f9ce48af3edd1e1e5c5d3abb"):
        raise ValueError("Stage83 source Stage82 Git provenance differs")
    needed={
       YEAR,"2000_original_VPD_ERA_T_QC0_T_ERA_source_month.csv",
       "2000_original_VPD_ERA_T_by_NOAA_signed_T_regime.csv",
       "2000_original_VPD_ERA_T_month_by_NOAA_signed_T_regime.csv",
       "1068_Ho1_2000_original_QC0_T_VPD_gt_eswater_ERA_comparison.csv"
    }
    if set(m.get("outputs_SHA256",{}))!=needed:
        raise ValueError("Stage83 source report output census changed")
    for file,digest in m["outputs_SHA256"].items():
        if sha(OLD/file)!=digest:
            raise ValueError("Stage83 output SHA changed: "+file)
    df=pd.read_csv(OLD/YEAR,dtype={"tower_local_start":str,
          "source_csv_row":str},low_memory=False)
    required={"tower_local_start","source_csv_row","native_VPD",
        "native_VPD_ERA","native_VPD_QC","native_T","native_T_QC",
        "native_T_ERA","native_VPD_MDS","native_VPD_MDS_QC",
        "native_T_MDS","native_T_MDS_QC","VPD_F_equals_source_VPD_ERA_1e_minus_4_hPa",
        "VPD_gt_es_at_native_TA_ERA","VPD_gt_es_at_native_QC0_T",
        "VPD_source_mathematically_valid_for_T_ERA_not_QC0_T",
        "VPD_gt_es_at_both_source_T","original_2000_hard_VPD",
        "original_505_T_delta_selected","science_group",
        "approved_for_DATM"}
    if (not required.issubset(df.columns) or len(df)!=NATIVE or
        df.tower_local_start.duplicated().any() or
        df.source_csv_row.duplicated().any()):
        raise ValueError("Stage83 full-year source columns/unique native physical records changed")
    native_dt=pd.to_datetime(df.tower_local_start,format="%Y%m%d%H%M",errors="raise")
    if not pd.DatetimeIndex(native_dt).equals(pd.date_range(
        "2000-01-01 00:00","2000-12-31 23:30",freq="30min")):
        raise ValueError("Stage83 native original timestamps year-2000 not continuous")
    df["native_dt"]=native_dt
    boolean=("VPD_F_equals_source_VPD_ERA_1e_minus_4_hPa",
       "VPD_gt_es_at_native_TA_ERA","VPD_gt_es_at_native_QC0_T",
       "VPD_source_mathematically_valid_for_T_ERA_not_QC0_T",
       "VPD_gt_es_at_both_source_T","original_2000_hard_VPD",
       "original_505_T_delta_selected","approved_for_DATM")
    for c in boolean:
        df[c]=df[c].astype(str).str.lower().eq("true")
    for c in ("native_VPD","native_VPD_ERA","native_VPD_QC",
              "native_T","native_T_QC","native_T_ERA",
              "native_VPD_MDS","native_VPD_MDS_QC",
              "native_T_MDS","native_T_MDS_QC"):
        df[c]=pd.to_numeric(df[c],errors="coerce")
        if c not in ("native_VPD_QC","native_T_QC"):
            df[c]=df[c].mask(df[c].le(-9990))
    if (not df.native_VPD_QC.eq(2).all() or
        not df.VPD_F_equals_source_VPD_ERA_1e_minus_4_hPa.all() or
        not np.isclose(df.native_VPD,df.native_VPD_ERA,rtol=0,
                       atol=1e-4,equal_nan=True).all() or
        int(df.native_T_QC.eq(0).sum())!=N_MEASURED or
        df.native_T_ERA.isna().any() or
        int(df.VPD_gt_es_at_native_TA_ERA.sum())!=N_SELF or
        int(df.VPD_gt_es_at_native_QC0_T.sum())!=N_MISMATCH or
        int(df.VPD_source_mathematically_valid_for_T_ERA_not_QC0_T.sum())!=N_MISRECONCILED or
        df.VPD_gt_es_at_both_source_T.any() or
        df.approved_for_DATM.any()):
        raise ValueError("Stage83 17568/year VPD_F=VPD_ERA or 32/1068 original science cohort changed")
    t=df.native_T_ERA
    es=saturation_water(t)
    recomputed=(df.native_VPD>es+1e-8)&t.between(-80,65)&df.native_VPD.notna()
    if not np.array_equal(recomputed.to_numpy(dtype=bool),
                          df.VPD_gt_es_at_native_TA_ERA.to_numpy(dtype=bool)):
        raise ValueError("Original Stage83 32 source ERA own-T discrepancy cannot be reproduced")
    if not df.loc[recomputed,"tower_local_start"].str.startswith("200001").all():
        raise ValueError("ERA-only 32 source records outside January 2000")
    # Cross-check the native-T mismatches remain a disjoint cohort.
    if (df.VPD_gt_es_at_native_TA_ERA &
        df.VPD_gt_es_at_native_QC0_T).any():
        raise ValueError("Stage83 independent T mismatch sets incorrectly overlap")
    return df,m

def events(df):
    x=df.copy()
    t=x.native_T_ERA
    esw=saturation_water(t)
    esi=saturation_ice(t)
    x["eswater_T_ERA_hPa"]=esw
    x["esice_T_ERA_hPa_when_below_0C"]=esi.where(t.lt(0))
    x["esphase_T_ERA_hPa"]=np.where(t.lt(0),esi,esw)
    x["original_ERA_VPD_minus_eswater_hPa"]=x.native_VPD-esw
    x["original_ERA_VPD_minus_esphase_hPa"]=x.native_VPD-x.esphase_T_ERA_hPa
    x["RH_percent_implied_if_same_TERA_and_VPD_water"]=(
        100*(1-x.native_VPD/esw))
    x["RH_percent_implied_if_same_TERA_and_VPD_phase"]=(
        100*(1-x.native_VPD/x.esphase_T_ERA_hPa))
    x["gt_eswater_T_ERA_recomputed"]=x[
        "original_ERA_VPD_minus_eswater_hPa"].gt(1e-8)&t.between(-80,65)
    x["gt_esphase_T_ERA_recomputed"]=x[
        "original_ERA_VPD_minus_esphase_hPa"].gt(1e-8)&t.between(-80,65)
    x["historical_offset_approved"]=False
    x["original_VPD_or_T_replacement_approved"]=False
    x["approved_for_DATM"]=False
    only=x.loc[x.gt_eswater_T_ERA_recomputed].copy()
    if len(only)!=32 or not only.tower_local_start.str.startswith("200001").all():
        raise ValueError("Complete source ERA-VPD/TA-ERA January 32 event closure failed")
    return x,only

def contiguous(only):
    z=only.sort_values("native_dt").copy()
    z["episode"]=(z.native_dt.diff()!=pd.Timedelta(minutes=30)).cumsum()
    out=[]
    for i,g in z.groupby("episode"):
        out.append({"episode":int(i),
           "native_start":str(g.tower_local_start.iloc[0]),
           "native_end":str(g.tower_local_start.iloc[-1]),
           "original_HH":len(g),"consecutive_hours":len(g)*0.5,
           "original_raw_VPD_ERA_hPa_median":float(g.native_VPD_ERA.median()),
           "original_raw_TA_ERA_C_median":float(g.native_T_ERA.median()),
           "excess_over_eswater_hPa_max":float(g.original_ERA_VPD_minus_eswater_hPa.max()),
           "implied_RHwater_pct_min":float(
               g.RH_percent_implied_if_same_TERA_and_VPD_water.min()),
           "measured_source_T_QC0_HH":int(g.native_T_QC.eq(0).sum()),
           "ERA_self_excess_NOT_evidence_of_specific_bad_variable":True,
           "DATM_approved":False})
    frame=pd.DataFrame(out)
    if frame.original_HH.sum()!=N_SELF or frame.episode.duplicated().any():
        raise ValueError("32 original exact episodes did not close")
    return frame.sort_values(["original_HH","native_start"],
                             ascending=[False,True]).reset_index(drop=True)

def context(full,chosen,hh=12):
    records=[]
    for e in chosen.itertuples(index=False):
        a=e.native_dt-pd.Timedelta(minutes=hh*30)
        b=e.native_dt+pd.Timedelta(minutes=hh*30)
        w=full.loc[full.native_dt.between(a,b)].copy()
        if not w.tower_local_start.eq(e.tower_local_start).any():
            raise ValueError("ERA source problem missing in native input context")
        w["center_problem_tower_local_start"]=e.tower_local_start
        w["center_original_csv_row"]=e.source_csv_row
        w["minutes_from_problem"]=((w.native_dt-e.native_dt).dt.total_seconds()/60)
        w["observations_may_repeat_across_windows"]=True
        records.append(w)
    return pd.concat(records,ignore_index=True)

def by_day(only):
    z=only.copy();z["source_day"]=z.tower_local_start.str[:8]
    records=[]
    for d,g in z.groupby("source_day"):
        records.append({"native_day":d,"events":len(g),
            "native_QC0_T_count":int(g.native_T_QC.eq(0).sum()),
            "original_VPD_ERA_exceed_eswater_hPa_min":float(
                g.original_ERA_VPD_minus_eswater_hPa.min()),
            "original_VPD_ERA_exceed_eswater_hPa_median":float(
                g.original_ERA_VPD_minus_eswater_hPa.median()),
            "original_VPD_ERA_exceed_eswater_hPa_max":float(
                g.original_ERA_VPD_minus_eswater_hPa.max()),
            "implied_RHwater_pct_min":float(
                g.RH_percent_implied_if_same_TERA_and_VPD_water.min()),
            "source_original_TA_ERA_C_min":float(g.native_T_ERA.min()),
            "source_original_TA_ERA_C_max":float(g.native_T_ERA.max()),
            "source_original_VPD_hPa_max":float(g.native_VPD.max()),
            "DATM_approved":False})
    return pd.DataFrame(records)

def self_test():
    assert N_SELF==32 and N_MISMATCH==1068
    assert abs(saturation_water(0)-6.112)<1e-12
    assert abs(saturation_ice(0)-6.112)<1e-12
    assert saturation_ice(-10)<saturation_water(-10)
    assert 100*(1-7/saturation_water(0))<0
    t=pd.to_datetime(["200001010000","200001010030","200001010200"],format="%Y%m%d%H%M")
    assert ((pd.Series(t).diff()!=pd.Timedelta(minutes=30)).cumsum().tolist()==[1,1,2])
    print("STAGE84 SELF-TEST PASS | 32 original January ERA VPD/TA_ERA self-consistency cases and diagnostic ice sensitivity; no writes")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    g=parser.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","audit"):
        g.add_argument("--"+mode,action="store_true")
    a=parser.parse_args()
    if a.self_test:return self_test()
    original,manifest=input_gate()
    if a.check:
        print("STAGE84 CHECK PASS | Stage83 source 5 CSV SHA and exact 17568 VPD_F==ERA, 1068 QC0-T mismatch and separate 32 ERA-T cases; NO NETWORK/WRITES")
        return
    full,chosen=events(original)
    epi=contiguous(chosen)
    windows=context(full,chosen,12)
    days=by_day(chosen)
    print("STAGE84 ALL ERA SELF-CONSISTENCY SOURCE EVENTS",len(chosen),
          "DAYS",len(days),"NATIVE EPISODES",len(epi))
    print("STAGE84 ORIGINAL 32 January VPD_ERA > eswater(original TA_ERA)")
    fields=["tower_local_start","source_csv_row",
       "native_VPD_ERA","native_T_ERA","native_T","native_T_QC",
       "eswater_T_ERA_hPa","original_ERA_VPD_minus_eswater_hPa",
       "RH_percent_implied_if_same_TERA_and_VPD_water",
       "esphase_T_ERA_hPa","RH_percent_implied_if_same_TERA_and_VPD_phase",
       "native_VPD_MDS","native_VPD_MDS_QC"]
    print(chosen[fields].to_string(index=False))
    print("STAGE84 SEPARATE 32 SOURCE EPISODES")
    print(epi.to_string(index=False))
    print("STAGE84 ALL 32 SOURCE DAY COUNTS")
    print(days.to_string(index=False))
    print("STAGE84 NOTE: implicit negative RH is calculated from unmatched ERA VPD/T product columns, NOT original direct RH measurements")
    print("STAGE84 SCIENCE HOLD: do not modify tower T, ERA VPD or forcing")
    output=REPORT/("stage84_Ho1_2000_32_raw_ERA_VPD_vs_ERA_T_source_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    mark=output/"INCOMPLETE_DO_NOT_USE"
    mark.write_text("Temperature-source and ERA VPD product mismatch diagnostic ONLY. No physical forcing approval.\n")
    files={
      "32_Ho1_2000_original_VPD_ERA_gt_eswater_TA_ERA_source_cases.csv":chosen,
      "32_Ho1_2000_ERA_source_mismatch_contiguous_episodes.csv":epi,
      "32_Ho1_2000_ERA_source_mismatch_days.csv":days,
      "32_Ho1_2000_original_ERA_VPD_T_plusminus6h_context.csv":windows
    }
    hashes={}
    for fname,frame in files.items():
        target=output/fname
        frame.to_csv(target,index=False)
        hashes[fname]=sha(target)
    if sha(OLD/YEAR)!=manifest["outputs_SHA256"][YEAR]:
        raise ValueError("Stage83 original source changed during Stage84 report creation")
    report={
       "schema":"STAGE84_HO1_2000_32_ORIGINAL_ERA_VPD_T_SOURCE_INCONSISTENCIES_v1",
       "source_17568_full_year_native_HH":NATIVE,
       "source_VPD_F_equals_VPD_ERA_17568":True,
       "source_measured_T_QC0_17294":True,
       "source_ERA_VPD_exceeds_eswater_original_T_QC0":N_MISMATCH,
       "all_previous_1068_are_consistent_at_source_TA_ERA":True,
       "separate_source_ERA_VPD_exceeds_eswater_source_TA_ERA":N_SELF,
       "joint_T_QC0_and_TERA_exceedances":0,
       "ERA_self_source_events_in_January_only":True,
       "diagnostic_implied_negative_RH_not_direct_measurement":True,
       "saturation_over_ice_sensitivity_diagnostic_only":True,
       "ERA_products_and_NOAA_not_local_tower_ground_truth":True,
       "no_automatic_RH_VPD_or_T_replacement":True,
       "source_temperature_repair_approved":False,
       "source_VPD_repair_approved":False,
       "historical_BIF_UTC_approved":False,
       "approved_for_DATM":False,
       "original_source_humidity_HOLDs_16874_unchanged":True,
       "numerical_humidity_shadow_15199_unchanged":True,
       "original_temperature_HOLDs_1675_unchanged":True,
       "other_9389_stage64_candidates_unchanged":True,
       "source_SHA256":{
            "stage83_script_git_blob":PIN83,
            "stage83_original_manifest":sha(OLD/"stage83_source_science_manifest.json"),
            "stage83_full_year_source_report":sha(OLD/YEAR),
            "original_FLUXNET_primary_HH_SHA256":manifest[
                "source_SHA256"]["Ho1_original_FLUXNET_primary_HH"],
            "stage83_source_inventory_SHA256":manifest[
                "source_SHA256"]["stage49_primary_source_inventory"],
            "NOAA_archive_SHA256":NOAA_SHA},
       "outputs_SHA256":hashes,
       "no_original_TOWER_NOAA_CDS_forcing_DATM_CIME_SLURM_changes":True
    }
    (output/"stage84_source_science_manifest.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    mark.unlink()
    print("STAGE84 AUDIT PASS | 32 exact Ho1 January 2000 ERA VPD > eswater(ERA T) original cases, no source repair")
    print("REPORT",output)
    print("NO ORIGINAL FLUXNET, NOAA, CDS, STAGE49-83, FORCING, DATM, CIME OR SLURM WRITES")

if __name__=="__main__":
    main()

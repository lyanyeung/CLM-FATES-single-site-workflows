#!/usr/bin/env python3
"""Stage12h -- source/clock and air-temperature diagnostic of US-MtB 1031 failures.

Read-only scientific diagnostic; never lower the 5C mismatch threshold.
Uses exact three newly SHA-validated Stage12f years (2020/22/24) that
covered 1038 native source RH gaps; Stage12g accepted only 3, held 1031
grid/tower T mismatch and 4 water/ice RH cases.

SOURCE CLOCK: original site-native keys are NEVER moved; compare a
predeclared sensitivity +/-6h relative to the published site BIF UTC
offset for each original native midpoint (every integer hour). The
ranking is an exploratory alignment test, NOT tower clock acceptance.
On all three whole-year original half-hour time series and separately
the 1038 target events, compare original tower TA_F, Stage12e
TA_USE (unchanged tower source), official exact-native paired TA_ERA,
and verified ERA5-Land grid T2m. Break down measurement QC0/1/2,
months/years, and spatiotemporal source offsets. Report any scientific
source unusual constant-offset or masked/quantized or unit patterns
without changing temperature, pressure or humidity.

--self-test: synthetic time-algebra checks; zero writes.
--check    : all original source SHA and Stage12g receipt checks,
             full in-memory source/temperature analysis, zero writes.
--run      : same check + isolated SHA-receipted REPORT ONLY.
No changes to FLUXMET, original ERA, Stage12e/g, PFT, DATM/CIME/Slurm.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12h-v1-20261025-US-MtB-T-source-13clock-hypotheses"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261024T233640Z_b3d74fae"
E=ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
G_SCRIPT=BASE/"scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py"
G_BLOB="14eabe09a56614808d6186d88fa5576233ed240b"
SITE="US-MtB"
YEARS=(2020,2022,2024)
EXPECTED={2024:408,2022:328,2020:302}
EXPECTED_HOLDS={"HOLD_SITE_GRID_T_DIFF_GT5C":1031,
                "HOLD_ICE_SUPERSATURATION":4}
SOURCE_FILE="2810_original_missing_year_source_review_after_stage12g.csv"
SUMMARY_FILE="six_site_stage12g_science_status.csv"
OUTPUT_SHA_FILES={
    *(site+"_STAGE12G_INCOMPLETE_NOLEAP.csv" for site in
      ("US-NR3","US-Kon","US-NR1","US-MMS","US-MtB","US-Me6")),
    "new_ERA5Land_year_source_RH_repair_candidates.csv",
    SOURCE_FILE,SUMMARY_FILE,"SCIENTIFIC_HOLD.md",
    "new_external_ERA5Land_SHA_manifest.json"
}

def regular(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlink original input: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()

def load():
    b=regular(G_SCRIPT).read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    if blob!=G_BLOB:
        raise ValueError("Stage12g audited science Python module Git blob changed")
    spec=importlib.util.spec_from_file_location("pinned_stage12g_source_for_12h",G_SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def self_test():
    assert sum(EXPECTED.values())==1038
    assert sum(EXPECTED_HOLDS.values())==1035
    assert len(YEARS)==3 and len(range(-6,7))==13
    assert len(OUTPUT_SHA_FILES)==11
    # Definition: native midpoint LST->UTC by minus published offset,
    # plus tested *relative* time shift, never source timestamp rewrite.
    native=pd.Timestamp("2020-03-18 17:30:00")
    utc=native+pd.Timedelta(minutes=15)-pd.Timedelta(hours=-7)
    assert utc==pd.Timestamp("2020-03-19 00:45:00")
    print("STAGE12H SELF-TEST PASS: 1038 target source times, 1031 T-delta & 4 ice holds, 13 no-change clock hypotheses; NO WRITES",flush=True)

def evidence():
    if not G.is_dir() or G.is_symlink() or not E.is_dir() or E.is_symlink():
        raise ValueError("Original Stage12g/12e six-site source directory missing")
    regular(G/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    receipt=json.loads(regular(G/"stage12g_research_only_sha_receipt.json").read_text())
    if (receipt.get("version")!="batch03-stage12g-v1-20261025-sha-verified-new-year-gridRH"
        or receipt.get("new_sha_verified_source_site_years")!=3
        or receipt.get("new_covered_original_missing_year_events")!=1038
        or receipt.get("new_numerical_ERA5Land_RH_only_research_repairs")!=3
        or receipt.get("original_233_physics_holds_untouched") is not True
        or receipt.get("original_six_site_T_P_native_clock_unchanged") is not True
        or receipt.get("all_original_Stage12e_finite_humidity_untouched") is not True
        or receipt.get("Postv5_approved")!=0 or receipt.get("DATM_ready")!=0
        or receipt.get("spinup_authorized")!=0
        or receipt.get("INCOMPLETE_marker_present") is not True
        or set(receipt.get("output_sha256",{}))!=OUTPUT_SHA_FILES
        or receipt.get("pinned_Stage12e_SHA256")!=sha(E/"stage12e_research_only_sha_receipt.json")):
        raise ValueError("Stage12g receipt evidence/source integrity differs")
    for name,digest in receipt["output_sha256"].items():
        if sha(G/name)!=digest:
            raise ValueError("Stage12g source output SHA changed: "+name)
    module=load()
    stage10,specs,physics_holds,missing,catalog,unavailable=module.sources()
    if SITE not in specs or set(catalog)!={(SITE,year) for year in YEARS}:
        raise ValueError("Expected exactly three validated US-MtB source years")
    held=pd.read_csv(regular(G/SOURCE_FILE),dtype={"site":str,"native_key":str},
                     low_memory=False)
    bad=held.loc[held.site.eq(SITE)&held.reason.ne("MISSING_VERIFIED_STAGE12F_SOURCE_YEAR")]
    if (bad.reason.value_counts().to_dict()!=EXPECTED_HOLDS
        or len(bad)!=1035 or bad.duplicated(["site","native_key"]).any()):
        raise ValueError("US-MtB original 1031+4 Stage12g science hold labels differ")
    fixed=pd.read_csv(regular(G/"new_ERA5Land_year_source_RH_repair_candidates.csv"),
                      dtype={"site":str,"native_key":str},low_memory=False)
    fixed=fixed.loc[fixed.site.eq(SITE)]
    if (len(fixed)!=3 or len(bad)+len(fixed)!=1038
        or set(bad.native_key)&set(fixed.native_key)):
        raise ValueError("US-MtB previous source 3 pass + 1035 holds mismatch")
    for year in YEARS:
        nb=sum(pd.to_datetime(bad.native_key,format="%Y%m%d%H%M").dt.year==year)
        npass=sum(pd.to_datetime(fixed.native_key,format="%Y%m%d%H%M").dt.year==year)
        if nb+npass!=EXPECTED[year]:
            raise ValueError("US-MtB source target count wrong year "+str(year))
    return stage10,specs[SITE],catalog,bad,fixed,module

def native(s,year):
    h=set(pd.read_csv(regular(s),nrows=0).columns)
    names=["TIMESTAMP_START","TA_F"]
    if "TA_F_QC" in h:names.append("TA_F_QC")
    if "VPD_F_QC" in h:names.append("VPD_F_QC")
    df=pd.read_csv(regular(s),usecols=names,
                   dtype={"TIMESTAMP_START":str},low_memory=False)
    if "TA_F_QC" not in df:df["TA_F_QC"]=np.nan
    if "VPD_F_QC" not in df:df["VPD_F_QC"]=np.nan
    dt=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M")
    return df.loc[(dt.dt.year==year)&~((dt.dt.month==2)&(dt.dt.day==29))].reset_index(drop=True)

def paired(s,year):
    df=pd.read_csv(regular(s),usecols=["TIMESTAMP_START","TA_ERA"],
                   dtype={"TIMESTAMP_START":str},low_memory=False)
    dt=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M")
    return df.loc[(dt.dt.year==year)&~((dt.dt.month==2)&(dt.dt.day==29))].reset_index(drop=True)

def as_numeric(series):
    a=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a))|(a<=-9990)]=np.nan
    return a

def stats(name,years,source,companion,grid,mask,source_qc):
    data=mask&np.isfinite(source)&np.isfinite(grid)
    delta=source[data]-grid[data]
    cdata=data&np.isfinite(companion)
    cdelta=source[cdata]-companion[cdata]
    if not len(delta):
        raise ValueError("No finite source + ERA5-Land temperature for "+name)
    if len(delta)>0:
        return {
            "scope":name,"year":int(years),
            "comparisons":len(delta),
            "source_minus_ERA5Land_mean_C":float(np.mean(delta)),
            "source_minus_ERA5Land_median_C":float(np.median(delta)),
            "source_minus_ERA5Land_p10_C":float(np.percentile(delta,10)),
            "source_minus_ERA5Land_p90_C":float(np.percentile(delta,90)),
            "mean_absolute_delta_C":float(np.mean(np.abs(delta))),
            "median_absolute_delta_C":float(np.median(np.abs(delta))),
            "fraction_abs_delta_gt5C":float((np.abs(delta)>5).mean()),
            "median_original_tower_TA_C":float(np.median(source[data])),
            "median_ERA5Land_t2m_C":float(np.median(grid[data])),
            "median_original_native_paired_TA_ERA_C":float(np.nanmedian(companion[data]))
                  if np.isfinite(companion[data]).any() else np.nan,
            "original_source_QC0_count":int(np.sum(source_qc[data]==0)),
            "original_source_QC1_count":int(np.sum(source_qc[data]==1)),
            "original_source_QC2_count":int(np.sum(source_qc[data]==2)),
            "MAE_source_TA_vs_native_paired_ERA_C":float(np.mean(np.abs(cdelta))) if len(cdelta) else np.nan
        }

def build():
    stage10,spec,catalog,bad,fixed,mod=evidence()
    old=pd.read_csv(regular(E/(SITE+"_STAGE12E_INCOMPLETE_NOLEAP.csv")),low_memory=False)
    g=pd.read_csv(regular(G/(SITE+"_STAGE12G_INCOMPLETE_NOLEAP.csv")),low_memory=False)
    if len(old)!=len(g) or not old.time.equals(g.time) or not old.TA_USE.equals(g.TA_USE):
        raise ValueError("Tower temperature native time changed between Stage12e and Stage12g")
    offset=int(stage10.BIF_OFFSET[SITE])
    allrows=[];summary=[];sens=[];monthly=[]
    for year in YEARS:
        print("STAGE12H SOURCE YEAR:",year,flush=True)
        p=native(spec["primary"],year)
        c=paired(spec["era"],year)
        time=pd.to_datetime(p.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        ts=pd.to_datetime(c.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        selected=old.loc[pd.to_datetime(old.time).dt.year.eq(year)].reset_index(drop=True)
        if (len(p)!=len(c) or not time.equals(ts) or len(selected)!=len(p)
            or not np.array_equal(selected.time.to_numpy(),
                      time.dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy())):
            raise ValueError("Exact original TA_F/TA_ERA/Stage12e timeline mismatch: "+str(year))
        ta=as_numeric(p.TA_F)
        used=selected.TA_USE.to_numpy(dtype=float)
        paired_t=as_numeric(c.TA_ERA)
        qc=as_numeric(p.TA_F_QC)
        if not np.allclose(ta,used,rtol=0,atol=1e-6,equal_nan=True):
            raise ValueError("Original measured TA differs from Stage12e retained source! Check official fill provenance.")
        plan,metadata=catalog[(SITE,year)]
        assert metadata["sha256"]==sha(metadata["path"])
        place=plan["request"]["location"]
        hours,field,coords=stage10.grid_fields(Path(metadata["path"]),year,
               (place["latitude"],place["longitude"]))
        half=int(spec["native_minutes"])/2
        midpoint=time+pd.Timedelta(minutes=half)
        utc_base=midpoint-pd.Timedelta(hours=offset)
        gtemp=stage10.interpolate(hours,field["t2m"],utc_base)-273.15
        key=time.dt.strftime("%Y%m%d%H%M").to_numpy()
        target=set(bad.native_key)|set(fixed.native_key)
        mask=np.isin(key,list(target))
        if mask.sum()!=EXPECTED[year]:
            raise ValueError("Per-year known source target event mismatch: "+str(year))
        for i in np.flatnonzero(mask):
            allrows.append({
                "site":SITE,"year":year,"native_key":key[i],
                "source_original_tower_TA_F_C":ta[i],
                "stage12e_retained_TA_USE_C":used[i],
                "original_native_TA_F_QC":qc[i],
                "native_paired_companion_TA_ERA_C":paired_t[i],
                "ERA5Land_T2M_C_base_offset":gtemp[i],
                "tower_minus_grid_C":ta[i]-gtemp[i],
                "tower_minus_companion_C":ta[i]-paired_t[i],
                "tower_vs_grid_gt5C":bool(abs(ta[i]-gtemp[i])>5),
                "source_tower_TA_excluded_from_modification":True,
                "Stage12g_classification":"PASS_RH_SHADOW" if key[i] in set(fixed.native_key)
                      else "HOLD_ORIGINAL_GRID_T_DIFFERENCE" if key[i] in set(
                          bad.loc[bad.reason.eq("HOLD_SITE_GRID_T_DIFF_GT5C"),"native_key"])
                      else "HOLD_ICE_SUPERSATURATION",
            })
        summary.append(stats("all_original_native_year",year,ta,paired_t,gtemp,
                            np.ones(len(p),dtype=bool),qc))
        summary.append(stats("1038_source_event_subset_by_year",year,ta,paired_t,gtemp,mask,qc))
        for month in range(1,13):
            m=(time.dt.month.to_numpy()==month)
            if (m&np.isfinite(ta)&np.isfinite(gtemp)).sum()<20:continue
            monthly.append(stats("full_month",year,ta,paired_t,gtemp,m,qc)|{"month":month})
        # Shift source native-to-UTC relationship ONLY for comparison.
        for shift in range(-6,7):
            utc=utc_base+pd.Timedelta(hours=shift)
            varied=stage10.interpolate(hours,field["t2m"],utc)-273.15
            for category,subset in (("ALL_YEAR",np.ones(len(p),dtype=bool)),
                                    ("ONLY_1038_MISSING_YEAR_EVENTS",mask),
                                    ("ORIGINAL_TA_QC0",qc==0)):
                valid=subset&np.isfinite(ta)&np.isfinite(varied)
                if not valid.any():continue
                diff=ta[valid]-varied[valid]
                sens.append({
                    "site":SITE,"year":year,"scope":category,
                    "additional_hourly_clock_shift_h":shift,
                    "published_BIF_UTC_offset_hypothesis":offset,
                    "count":int(valid.sum()),
                    "mean_difference_C":float(np.mean(diff)),
                    "median_difference_C":float(np.median(diff)),
                    "MAE_C":float(np.mean(np.abs(diff))),
                    "fraction_abs_difference_gt5C":float((np.abs(diff)>5).mean()),
                    "R2_sensitivity_of_temperature":float(
                        np.corrcoef(ta[valid],varied[valid])[0,1]**2)
                        if len(diff)>3 and np.std(ta[valid])>0 and np.std(varied[valid])>0
                        else np.nan,
                    "clock_offset_approved":False,
                    "source_air_temperature_modified":False
                })
    cases=pd.DataFrame(allrows).sort_values(["year","native_key"]).reset_index(drop=True)
    if (len(cases)!=1038 or
        cases.Stage12g_classification.value_counts().to_dict()!={"HOLD_ORIGINAL_GRID_T_DIFFERENCE":1031,"HOLD_ICE_SUPERSATURATION":4,"PASS_RH_SHADOW":3}):
        raise ValueError("Stage12h 1031/4/3 original source scientific case split mismatch")
    sensitivity=pd.DataFrame(sens)
    tempstats=pd.DataFrame(summary)
    yearmonths=pd.DataFrame(monthly)
    # Clock hypotheticals must never be silently selected.
    rankings=(sensitivity.loc[sensitivity.scope.eq("ONLY_1038_MISSING_YEAR_EVENTS")]
              .sort_values(["year","MAE_C"]).groupby("year",as_index=False).head(13))
    if len(rankings)!=39:
        raise ValueError("Expected 13 sensitivity hypotheses for each of 3 source years")
    leaders=(rankings.sort_values(["year","MAE_C"])
             .groupby("year",as_index=False).head(1).copy())
    base=rankings.loc[rankings.additional_hourly_clock_shift_h.eq(0)]
    if len(base)!=3 or len(leaders)!=3:
        raise ValueError("Complete base shift and year-level sensitivity not produced")
    return cases,tempstats,yearmonths,sensitivity,leaders

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    flags=ap.add_mutually_exclusive_group(required=True)
    flags.add_argument("--self-test",action="store_true")
    flags.add_argument("--check",action="store_true")
    flags.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12H — US-MTB FIXED-TOWER-TA VS VERIFIED GRID AND COMPANION CLOCK/T QC | "+VERSION,flush=True)
    self_test()
    if args.self_test:return
    cases,annual,monthly,offsets,best=build()
    print("\n========== VERIFIED ORIGINAL 1038 US-MTB TEMPERATURE SOURCE EVENTS ==========",flush=True)
    print(cases.groupby(["year","Stage12g_classification"]).agg(
       samples=("native_key","size"),
       median_source_T_C=("source_original_tower_TA_F_C","median"),
       median_ERA5Land_T_C=("ERA5Land_T2M_C_base_offset","median"),
       median_tower_minus_grid_C=("tower_minus_grid_C","median"),
       median_tower_minus_companion_C=("tower_minus_companion_C","median")
    ).to_string(),flush=True)
    print("\n========== ALL YEAR VS 1038 SOURCE EVENT TEMPERATURE DIAGNOSTICS ==========",flush=True)
    print(annual.to_string(index=False),flush=True)
    print("\n========== BEST EXPLORATORY CLOCK HYPOTHESIS BY YEAR (NOT APPROVED) ==========",flush=True)
    print(best[["year","count","additional_hourly_clock_shift_h",
        "MAE_C","fraction_abs_difference_gt5C","mean_difference_C"]].to_string(index=False),flush=True)
    print("\nSTAGE12H SUMMARY: examined_verified_grid_years=3 native_events=1038 "
       "T_delta_over5C_holds=1031 ice_holds=4 previous_RH_research_repairs=3 "
       "yearly_shift_hypotheses=13 temperature_unchanged=True "
       "science_clock_approved=0 RH_repairs=0 source_writes=0",flush=True)
    if args.check:
        print("STAGE12H CHECK ONLY: no output reports or source writes.",flush=True)
        return
    out=ROOT/"reports"/("stage12h_US-MtB_temperature_and_clock_three_year_diagnostics_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    reports={
        "1038_US-MtB_original_source_temperature_cases.csv":cases,
        "three_year_full_vs_events_temperature_statistics.csv":annual,
        "36_site_year_month_temperature_diagnostics.csv":monthly,
        "13_clock_hypotheses_by_year_and_original_T_QC.csv":offsets,
        "best_shift_sensitivity_not_a_clock_approval.csv":best
    }
    for name,frame in reports.items():
        frame.to_csv(out/name,index=False)
    note="""# Stage12h is a source temperature CLOCK SENSITIVITY, not a correction
All source-native original timestamps, original TA_F, Stage12e/Stage12g
site forcing and pressure remain SHA-verified and unchanged. 13 possible
clock shifts relative to the published site BIF offset are exploratory.
Their minimum MAE does not prove the source clock is incorrect, and
even an improved match does not authorize altering tower timestamps
or replacing EC tower temperature. Compare monthly/QC0 patterns to
distinguish time-zone, site meteorology, elevational differences,
original sensor artifacts and actual cold anomalies. Keep 1031
temperature holds, 4 ice phase holds, all 233 other physics holds,
and Post-v5/DATM/spinup authorizations at ZERO.
"""
    (out/"SCIENCE_HOLD.md").write_text(note)
    receipt={
       "version":VERSION,
       "Stage12g_source_receipt_SHA256":sha(G/"stage12g_research_only_sha_receipt.json"),
       "year_count":3,"source_native_target_count":1038,
       "original_Stage12g_T_delta_gt5C_holds":1031,
       "original_Stage12g_ice_holds":4,
       "original_Stage12g_valid_RH_research_changes":3,
       "new_tower_clock_approved":False,
       "new_tower_temperature_edits":0,
       "new_humidity_edits":0,"Postv5_approved":0,
       "DATM_ready":0,"spinup_authorized":0,
       "output_sha256":{name:sha(out/name) for name in [*reports,"SCIENCE_HOLD.md"]}
    }
    (out/"stage12h_temperature_source_science_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12H DIAGNOSTIC REPORT DIR:",out,flush=True)
    print("NO CLIMATE FORCING, ORIGINAL TOWER TEMPERATURE, OR MODEL INPUT WRITTEN.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE12H STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

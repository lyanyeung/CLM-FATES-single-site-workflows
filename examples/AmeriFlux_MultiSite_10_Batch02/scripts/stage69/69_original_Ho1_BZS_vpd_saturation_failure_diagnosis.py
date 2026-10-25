#!/usr/bin/env python3
"""Stage69 | Ho1/BZS original VPD>esat source-mechanism census (READ ONLY).

Requires pinned Stage64+Stage68 science outputs and exact 16,874 original
hard-physics source events. Recalculates es_water(T), actual vapor pressure,
VPD/es_water and original QC distributions; reports year/month, extremes,
consecutive HH event runs and diagnostic VPD scale sensitivity.

Important: VPD/10 and VPD/100 are UNVERIFIED SCALING HYPOTHESES, never
corrective data. No external ERA5 RH/temperature download or time alignment
approval; no original source, DATM, NetCDF, CIME or model changes.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
R=ROOT/"reports"
S64=R/"stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94"
S68=R/"stage68_official_uploaded_BIF_Ho1_BZS_UTC_shadow_20261025T075428Z_11c5b183"
F68="16874_Ho1_BZS_original_hard_BIF_local_to_UTC_SHADOW.csv"
NAMES={"US-Ho1":16788,"US-BZS":86}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def water_es(tc):
    return 6.112*np.exp(np.clip(17.67*tc/(tc+243.5),-45,45))

def numeric(s):
    x=pd.to_numeric(s,errors="coerce").astype(float)
    return x.mask((~np.isfinite(x))|(x<=-9990))

def load():
    m64=json.loads((S64/"unified_source_provenance_and_hold_manifest.json").read_text())
    m68=json.loads((S68/"stage68_source_and_science_manifest.json").read_text())
    if ((S64/"INCOMPLETE_DO_NOT_USE").exists() or
        (S68/"INCOMPLETE_DO_NOT_USE").exists() or
        m64.get("schema")!="STAGE64_ORIGINAL_HARD_FULL_CENSUS_9389_CANDIDATES_16943_HOLD_v1" or
        m64.get("total_selected_candidate_rows")!=9389 or
        m64.get("remaining_hard_HOLD")!=16943 or
        m64.get("approved_for_DATM") is not False or
        m68.get("schema")!="STAGE68_OFFICIAL_BIF_HO1_BZS_HISTORICAL_CLOCK_SHADOW_v1" or
        m68.get("total_source_HOLD_shadow_only")!=16874 or
        m68.get("historical_UTC_offset_coverage_verified") is not False or
        m68.get("DATM_approved") is not False):
        raise ValueError("Stage64/68 source gates changed")
    for folder,m in ((S64,m64),(S68,m68)):
        for n,d in m.get("output_sha256",{}).items():
            if sha(folder/n)!=d:raise ValueError("Source output SHA changed "+n)
    if m68["source_SHA256"]["stage64_manifest"]!=sha(
        S64/"unified_source_provenance_and_hold_manifest.json"):
        raise ValueError("Stage68 original Stage64 provenance mismatch")
    a=pd.read_csv(S68/F68,dtype={"site":str,"timestamp_start":str,
          "tower_local_start":str,"shadow_UTC_START":str,"source_sha256":str})
    if (len(a)!=16874 or a.duplicated(["site","tower_local_start"]).any()
       or a.duplicated(["site","shadow_UTC_START"]).any()
       or Counter(a.site)!=Counter(NAMES)):
        raise ValueError("Stage68 original source one-to-one clock crosswalk changed")
    core={"site","tower_local_start","shadow_UTC_START","TA_C","VPD_hPa",
       "PA_kPa","TA_original_QC","VPD_original_QC","RH_raw_pct","flags",
       "source_sha256","source_csv_row"}
    if not core.issubset(a.columns):
        raise ValueError("Stage68 original source physics columns absent "+str(core-set(a.columns)))
    if not a.flags.astype(str).str.contains("ACTUAL_VAPOR_NONPOSITIVE",regex=False).all():
        raise ValueError("Original 16874 no longer the Stage48 vapor nonpositive hard-event population")
    return a,m64,m68

def identify_runs(part):
    """Runs of flagged hard events separated by exactly 30 minutes (HH)."""
    x=part.sort_values("tower_dt")
    if x.tower_dt.duplicated().any():
        raise ValueError("Native tower source timestamp duplicate within site")
    breakpoints=(x.tower_dt.diff()!=pd.Timedelta(minutes=30)).cumsum()
    result=[]
    for _,run in x.groupby(breakpoints,sort=False):
        result.append({"site":run.site.iloc[0],
            "first_tower_local":run.tower_local_start.iloc[0],
            "last_tower_local":run.tower_local_start.iloc[-1],
            "n_consecutive_halfhours":len(run),
            "duration_hours":len(run)*0.5,
            "first_shadow_UTC":run.shadow_UTC_START.iloc[0],
            "median_source_T_C":float(run.TA_C.median()),
            "median_source_VPD_hPa":float(run.VPD_hPa.median()),
            "median_VPD_over_es":float(run.VPD_over_es_water.median()),
            "n_T_QC0":int(run.TA_original_QC.eq(0).sum()),
            "n_VPD_QC0":int(run.VPD_original_QC.eq(0).sum())})
    return result

def diagnose(a):
    z=a.copy()
    z["tower_dt"]=pd.to_datetime(
       z.tower_local_start.str.strip(),format="%Y%m%d%H%M",errors="raise")
    z["utc_dt"]=pd.to_datetime(
       z.shadow_UTC_START.str.strip(),format="%Y%m%d%H%M",errors="raise")
    z["TA_C"]=numeric(z.TA_C)
    z["VPD_hPa"]=numeric(z.VPD_hPa)
    z["PA_kPa"]=numeric(z.PA_kPa)
    z["RH_raw_pct"]=numeric(z.RH_raw_pct)
    z["TA_original_QC"]=numeric(z.TA_original_QC)
    z["VPD_original_QC"]=numeric(z.VPD_original_QC)
    if (z.TA_C.isna().any() or z.VPD_hPa.isna().any()
        or z.PA_kPa.isna().any() or
        (z.TA_C<=-80).any() or (z.TA_C>=65).any()
        or (z.PA_kPa<=50).any() or (z.PA_kPa>=110).any()):
        raise ValueError("Original hard-physics population outside Stage48 valid-TA/PA screen")
    sat=water_es(z.TA_C.to_numpy(float))
    z["es_water_hPa"]=sat
    z["actual_vapor_pressure_hPa"]=sat-z.VPD_hPa
    z["VPD_over_es_water"]=z.VPD_hPa/sat
    z["RH_water_derived_pct"]=100*z.actual_vapor_pressure_hPa/sat
    if (not np.isfinite(z.VPD_over_es_water).all() or
       not z.actual_vapor_pressure_hPa.le(1e-10).all() or
       not z.RH_water_derived_pct.le(1e-7).all()):
        raise ValueError("Stage48 nonpositive e = es(T) - VPD does not reproduce exactly")
    z["ratio_bin"]=pd.cut(z.VPD_over_es_water,[-np.inf,1.,1.05,1.2,1.5,
       2.,3.,5.,10.,20.,50.,100.,np.inf],
       labels=["<=1","(1,1.05]","(1.05,1.2]","(1.2,1.5]",
        "(1.5,2]","(2,3]","(3,5]","(5,10]","(10,20]","(20,50]",
        "(50,100]",">100"],include_lowest=True)
    z["source_temp_below_zero"]=z.TA_C.lt(0)
    z["RH_original_missing"]=z.RH_raw_pct.isna()
    z["QC_T_category"]=z.TA_original_QC.fillna(-1).astype(int)
    z["QC_VPD_category"]=z.VPD_original_QC.fillna(-1).astype(int)
    z["tower_year"]=z.tower_dt.dt.year
    z["tower_month"]=z.tower_dt.dt.month
    z["tower_hour"]=z.tower_dt.dt.hour+z.tower_dt.dt.minute/60
    for scale in (10,100):
        # Unverified diagnostic: could a decimal/place or unit conversion
        # make the *original* VPD physically admissible at original T?
        z[f"hypothesis_VPD_div{scale}_physical_ONLY"]=(
             z.VPD_hPa/scale<z.es_water_hPa)
    stats=[]
    for (site,year),part in z.groupby(["site","tower_year"],sort=True):
        ratio=part.VPD_over_es_water
        stats.append({"site":site,"year":int(year),"hard_events":len(part),
          "T_QC0":int(part.TA_original_QC.eq(0).sum()),
          "VPD_QC0":int(part.VPD_original_QC.eq(0).sum()),
          "original_RH_missing":int(part.RH_original_missing.sum()),
          "source_T_below0":int(part.source_temp_below_zero.sum()),
          "VPD_over_es_median":float(ratio.median()),
          "VPD_over_es_p90":float(ratio.quantile(.9)),
          "VPD_over_es_max":float(ratio.max()),
          "source_VPD_hPa_median":float(part.VPD_hPa.median()),
          "hypothesis_div10_looks_physical":int(
             part.hypothesis_VPD_div10_physical_ONLY.sum()),
          "hypothesis_div100_looks_physical":int(
             part.hypothesis_VPD_div100_physical_ONLY.sum())})
    yr=pd.DataFrame(stats)
    runs=pd.DataFrame([r for site,p in z.groupby("site",sort=True)
        for r in identify_runs(p)])
    ratios=z.groupby(["site","ratio_bin"],observed=False).size().reset_index(name="events")
    qc=z.groupby(["site","QC_T_category","QC_VPD_category"],
       dropna=False).size().reset_index(name="events")
    if yr.hard_events.sum()!=16874 or int(ratios.events.sum())!=16874:
        raise ValueError("Stage69 per-year/ratio event census does not close")
    print("STAGE69 SOURCE-REPRODUCED WATER_VAPOR_NONPOSITIVE",Counter(z.site))
    print("STAGE69 SITE QC MATRIX",qc.to_string(index=False))
    print("STAGE69 VPD_OVER_SATURATION BIN COUNTS",ratios.to_string(index=False))
    print("STAGE69 YEARLY STATUS",yr.to_string(index=False))
    print("STAGE69 LARGEST ORIGINAL CONTIGUOUS HARD EPISODES")
    print(runs.sort_values("n_consecutive_halfhours",ascending=False).head(25).to_string(index=False))
    print("STAGE69 HYPOTHESIS_ONLY scale artifacts are NOT repair candidates")
    return z,yr,qc,ratios,runs

def self_test():
    t=np.array([-30.,10.])
    s=water_es(t)
    v=np.array([s[0]*1.1,s[1]*2])
    assert np.all(v>s)
    assert np.all(100*(s-v)/s<0)
    assert sum(NAMES.values())==16874
    print("STAGE69 SELF-TEST PASS | original es_water(T)-VPD negative vapor physics")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--self-test",action="store_true")
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    original,m64,m68=load()
    z,yr,qc,ratios,runs=diagnose(original)
    if a.check:
        print("STAGE69 CHECK PASS | exact 16874 source-physics errors; no writes")
        return
    out=R/("stage69_16874_original_VPD_vs_water_es_source_diagnosis_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
       "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Original physics diagnosis ONLY, no model approval.\n")
    frames={
        "16874_original_VPD_over_es_water_diagnostics.csv":z,
        "Ho1_BZS_original_source_physics_by_year.csv":yr,
        "Ho1_BZS_original_T_VPD_QC_crosstab.csv":qc,
        "Ho1_BZS_VPD_to_saturation_ratio_bins.csv":ratios,
        "Ho1_BZS_contiguous_native_halfhour_hard_episodes.csv":runs}
    hashes={}
    for name,d in frames.items():
        path=out/name
        d.to_csv(path,index=False)
        hashes[name]=sha(path)
    source=sha(S68/F68)
    if source!=m68["output_sha256"][F68]:
        raise ValueError("Input changed during original-humidity audit")
    provenance={
      "schema":"STAGE69_HO1_BZS_ORIGINAL_HUMIDITY_PHYSICS_MECHANISM_v1",
      "n_Ho1_original_hard":16788,"n_BZS_original_hard":86,
      "n_original_nonpositive_vapor":16874,
      "prior_Stage64_humidity_candidates_unchanged":9389,
      "BIF_Ho1_minus5_BZS_minus9_shadow_only":True,
      "VPD_division_by10_and100_are_unapproved_hypotheses":True,
      "water_saturation_equation":"6.112 * exp(17.67*TA_C/(TA_C+243.5)) hPa",
      "all_original_hard_HOLD_remain_unreleased":True,
      "independent_external_ERA5_not_checked":True,
      "approved_for_DATM":False,"approved_for_spinup":False,
      "source_SHA256":{
          "stage68_events":source,
          "stage68_manifest":sha(S68/"stage68_source_and_science_manifest.json"),
          "stage64_manifest":sha(S64/"unified_source_provenance_and_hold_manifest.json")},
      "output_SHA256":hashes,
      "original_or_forcing_changes":False}
    (out/"source_science_manifest.json").write_text(json.dumps(
       provenance,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE69 AUDIT PASS | 16874 original negative vapor events physically source-explained")
    print("REPORT",out)
    print("NO ORIGINAL, CDS, STAGE64/68, NETCDF, DATM, CIME OR SLURM WRITES")
if __name__=="__main__":
    main()

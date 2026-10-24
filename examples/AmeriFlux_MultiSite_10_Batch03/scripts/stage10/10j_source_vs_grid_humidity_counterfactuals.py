#!/usr/bin/env python3
"""Batch03 Stage10j — controlled ERA source vs ERA5-Land humidity comparison.

Evidence-only cross-comparison of the same 1,924 exact Stage10i source-event
rows and Stage10b ERA5-Land-derived meteorology. No humidity replacement.

Source paired fields: source TA_ERA and VPD_ERA (hPa) from Stage10h/10i.
External evidence: Stage10b interpolated ERA5-Land T2m, dewpoint and surface P
at *provisional* UTC native-interval midpoint.

Test two counterfactual mathematical combinations, NOT replacement recipes:
  T-only:   e_s(grid T) - source VPD_ERA
  VPD-only: e_s(source TA_ERA) - [e_s(grid T) - e_s(grid Td)]
These distinguish whether replacing just the temperature or just the VPD
would remove a negative implied water vapour pressure. They do NOT identify
which upstream processing step is wrong or approve use of either combination.

FLUXNET VPD_ERA may be separately downscaled/regressed from reanalysis and
therefore need not be thermodynamically self-consistent with its separately
downscaled TA_ERA. ERA5-Land is ERA-dependent, not independent tower truth.
US-Me2 UTC-8 remains HYPOTHETICAL (no release-specific BIF).
--self-test: isolated formula/regression checks with no source reads/writes.
--check: SHA checks, all 1924 rows, computed summaries; no file writes.
--run: new isolated reports/stage10j_* folder only.
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
S10B = ROOT/"reports/stage10b_external_humidity_20261024T040142Z_be6a9d78"
S10D = ROOT/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
S10H = ROOT/"reports/stage10h_original_source_provenance_20261024T054425Z_faf342a8"
S10I = ROOT/"reports/stage10i_era_vpd_physics_20261024T055509Z_b5a44de8"
KEYS = ["site","source_csv_row","time"]
EXPECTED = {"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
            "US-MtB":15,"US-NR1":173,"US-NR3":1484}
VERSION = "stage10j-v1-20261024-algebraic-cross-comparison"


def regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Required regular file missing/symlink: "+str(path))
    return path


def folder(path):
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Required directory missing/symlink: "+str(path))
    return path


def digest(path):
    h = hashlib.sha256()
    with regular(path).open("rb") as inp:
        for chunk in iter(lambda:inp.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def doc(path):
    return json.loads(regular(path).read_text(encoding="utf-8"))


def numeric(df,name):
    if name not in df:
        raise ValueError("Missing numeric column: "+name)
    x = pd.to_numeric(df[name], errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x) | (x <= -9990)] = np.nan
    return x


def bools(df,name):
    if name not in df:
        raise ValueError("Missing flag: "+name)
    v = df[name].astype(str).str.strip().str.lower()
    if not v.isin(["true","false","1","0"]).all():
        raise ValueError("Invalid boolean values in "+name)
    return v.isin(["true","1"]).to_numpy(dtype=bool)


def water_saturation(temp_c):
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return 6.112 * np.exp(17.67*temp_c/(temp_c+243.5))


def same(field,actual,expected,atol=1e-7,rtol=1e-7):
    if not np.isclose(actual,expected,atol=atol,rtol=rtol,equal_nan=False).all():
        ix=np.flatnonzero(~np.isclose(actual,expected,atol=atol,rtol=rtol,equal_nan=False))
        raise ValueError(f"{field} disagrees with independent formula: {len(ix)} rows; first index {ix[0]}")


def pair(a,b,expected_n=1924,expected_sites=None):
    for name,frame in (("Stage10i",a),("Stage10b",b)):
        if len(frame)!=expected_n or frame.duplicated(KEYS).any():
            raise ValueError(f"{name} length/identity mismatch")
    akeys=set(map(tuple,a[KEYS].to_numpy()))
    bkeys=set(map(tuple,b[KEYS].to_numpy()))
    if akeys!=bkeys:
        raise ValueError("Stage10i vs Stage10b exact event keys differ")
    merged=a.merge(b,on=KEYS,how="inner",validate="one_to_one",suffixes=("_source","_grid"))
    counts=EXPECTED if expected_sites is None else expected_sites
    if len(merged)!=expected_n or merged.site.value_counts().to_dict()!=counts:
        raise ValueError("Stage10i/10b source event counts differ")
    return merged


def preflight():
    for path in (ROOT,S07,S10B,S10D,S10H,S10I):
        folder(path)
    regular(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    i_meta=doc(S10I/"science_provenance.json")
    b_meta=doc(S10B/"provenance_and_science_hold.json")
    h_meta=doc(S10H/"read_only_provenance.json")
    d_meta=doc(S10D/"read_only_provenance.json")
    i_file="all_1924_source_ERA_water_saturation_inconsistencies.csv"
    b_file="humidity_external_sensitivity_1924.csv"
    d_file="all_1924_manual_review.csv"
    if (i_meta.get("source_rows")!=1924 or i_meta.get("site_years")!=32
        or i_meta.get("decision")!="SCIENCE HOLD; ZERO REPAIRS AND ZERO TIME OFFSETS APPROVED"
        or i_meta.get("stage10h_v2_receipt_sha256")!=digest(S10H/"read_only_provenance.json")
        or i_meta.get("stage10b_receipt_sha256")!=digest(S10B/"provenance_and_science_hold.json")
        or i_meta.get("stage10d_ledger_sha256")!=digest(S10D/d_file)
        or b_meta.get("decision")!="ALL ROWS SCIENTIFIC HOLD; NO REPLACEMENTS APPROVED"
        or h_meta.get("selected_events")!=1924
        or h_meta.get("source_era_alignment")!="EXACT_TIMESTAMP_ONLY_NO_POSITIONAL_JOIN_NO_TIME_SHIFT"
        or d_meta.get("no_replacement_approved") is not True):
        raise ValueError("Stage10i/10h/10b/10d provenance hold or cross-reference mismatch")
    expected_i={
        "all_1924_source_ERA_water_saturation_inconsistencies.csv",
        "site_ERA_overage_summary.csv","site_year_ERA_overage_summary.csv",
        "site_year_month_ERA_overage_summary.csv",
    }
    expected_b={b_file,"site_science_review_summary.csv",
                "site_year_science_review_summary.csv"}
    if set(i_meta.get("output_sha256",{}))!=expected_i:
        raise ValueError("Stage10i output manifest changed")
    if set(b_meta.get("output_SHA256",{}))!=expected_b:
        raise ValueError("Stage10b output manifest changed")
    for name,source,receipt in [(p,S10I,i_meta["output_sha256"]) for p in expected_i] + \
            [(p,S10B,b_meta["output_SHA256"]) for p in expected_b]:
        if digest(source/name)!=receipt[name]:
            raise ValueError("Input report checksum mismatch "+name)
    if (d_meta.get("output_sha256",{}).get(d_file)!=digest(S10D/d_file)
        or i_meta.get("stage10d_ledger_sha256")!=digest(S10D/d_file)):
        raise ValueError("Stage10d source identity receipt mismatch")
    a=pd.read_csv(regular(S10I/i_file),dtype={key:str for key in KEYS},
                  keep_default_na=False,low_memory=False)
    b=pd.read_csv(regular(S10B/b_file),dtype={key:str for key in KEYS},
                  keep_default_na=False,low_memory=False)
    merged=pair(a,b)
    cols=["original_ERA_T_C","original_ERA_VPD_hPa",
          "original_ERA_water_es_hPa","original_ERA_implied_ea_hPa",
          "grid_temperature_C","grid_dewpoint_C",
          "grid_dewpoint_absolute_e_hPa","grid_relative_humidity_pct",
          "absolute_vpd_at_tower_T_hPa","relative_vpd_at_tower_T_hPa",
          "VPD_ERA_excess_over_water_es_hPa","original_F_T_minus_ERA_T_C",
          "retained_T_minus_ERA_T_C"]
    if not set(cols).issubset(merged.columns):
        raise ValueError("Stage10i+Stage10b cross-report numeric schema changed: "+str(set(cols)-set(merged.columns)))
    if not bools(merged,"ERA_pair_already_negative_vapour_pressure").all():
        raise ValueError("Stage10i ERA negative implied vapour flag unexpected")
    if bools(merged,"clock_or_humidity_approved").any() or bools(merged,"clock_approved").any():
        raise ValueError("Unexpected approval in source or grid report")
    return merged,{"stage10i_receipt_sha256":digest(S10I/"science_provenance.json"),
                   "stage10b_receipt_sha256":digest(S10B/"provenance_and_science_hold.json")}


def analyze(frame,required_n=1924):
    t_source=numeric(frame,"original_ERA_T_C")
    vpd_source=numeric(frame,"original_ERA_VPD_hPa")
    t_grid=numeric(frame,"grid_temperature_C")
    td_grid=numeric(frame,"grid_dewpoint_C")
    grid_ea_report=numeric(frame,"grid_dewpoint_absolute_e_hPa")
    es_source=water_saturation(t_source)
    es_grid=water_saturation(t_grid)
    ea_grid=water_saturation(td_grid)
    grid_vpd=es_grid-ea_grid
    same("original source es",numeric(frame,"original_ERA_water_es_hPa"),es_source)
    same("original source ea",numeric(frame,"original_ERA_implied_ea_hPa"),es_source-vpd_source)
    same("ERA5-Land dewpoint ea",grid_ea_report,ea_grid)
    same("source VPD excessive",numeric(frame,"VPD_ERA_excess_over_water_es_hPa"),vpd_source-es_source)
    if not (np.isfinite(t_source).all() and np.isfinite(vpd_source).all() and
            np.isfinite(t_grid).all() and np.isfinite(td_grid).all()):
        raise ValueError("Missing finite source/grid temperature or VPD")
    if not (td_grid <= t_grid+0.1).all():
        raise ValueError("ERA5-Land dewpoint above temperature outside allowed tolerance")
    if not np.all(grid_vpd >= -0.01):
        raise ValueError("ERA5-Land dewpoint-derived VPD is negative unexpectedly")
    if not np.all(es_source-vpd_source<0):
        raise ValueError("Original source ERA negative implied ea no longer holds")
    if len(frame)!=required_n:
        raise ValueError("Mismatch in input scope")
    source_qc2=bools(frame,"source_ERA_QC2")
    if required_n==1924 and source_qc2.sum()!=1866:
        raise ValueError("Stage10i QC2 scope changed")
    temp_only_ea=es_grid-vpd_source
    vpd_only_ea=es_source-grid_vpd
    out=frame[KEYS].copy()
    out["year"]=pd.to_datetime(frame.time,errors="raise").dt.year
    out["month"]=pd.to_datetime(frame.time,errors="raise").dt.month
    out["original_source_VPD_QC2"]=source_qc2
    out["clock_offset_provisional_hours"]=numeric(frame,"clock_offset_hours_hypothesis")
    out["clock_approved"]=False
    out["source_TA_ERA_C"]=t_source
    out["source_VPD_ERA_hPa"]=vpd_source
    out["source_es_water_hPa"]=es_source
    out["source_implied_ea_water_hPa"]=es_source-vpd_source
    out["grid_T2m_C"]=t_grid
    out["grid_Tdew_C"]=td_grid
    out["grid_es_water_hPa"]=es_grid
    out["grid_ea_dewpoint_hPa"]=ea_grid
    out["grid_VPD_dewpoint_hPa"]=grid_vpd
    out["tower_retained_T_minus_source_ERA_C"]=numeric(frame,"retained_T_minus_ERA_T_C")
    out["raw_F_T_minus_source_ERA_C"]=numeric(frame,"original_F_T_minus_ERA_T_C")
    out["delta_grid_T_minus_source_ERA_C"]=t_grid-t_source
    out["delta_grid_VPD_minus_source_ERA_hPa"]=grid_vpd-vpd_source
    out["source_VPD_excess_over_source_es_water_hPa"]=vpd_source-es_source
    out["T_only_counterfactual_ea_hPa"]=temp_only_ea
    out["VPD_only_counterfactual_ea_hPa"]=vpd_only_ea
    out["T_only_counterfactual_ea_nonnegative"]=temp_only_ea>=0
    out["VPD_only_counterfactual_ea_nonnegative"]=vpd_only_ea>=0
    out["both_grid_ea_positive"]=ea_grid>0
    out["T_only_RH_water_pct"]=100*temp_only_ea/es_grid
    out["VPD_only_RH_water_pct"]=100*vpd_only_ea/es_source
    out["grid_RH_water_pct"]=100*ea_grid/es_grid
    out["review_class"]=np.select([
        (temp_only_ea>=0)&(vpd_only_ea>=0),
        (temp_only_ea>=0)&(vpd_only_ea<0),
        (temp_only_ea<0)&(vpd_only_ea>=0),
    ],[
        "BOTH_SINGLE_INPUT_SWAPS_REMOVE_NEGATIVE_EA",
        "GRID_T_ONLY_REMOVES_NEGATIVE_EA",
        "GRID_VPD_ONLY_REMOVES_NEGATIVE_EA",
    ],default="NEITHER_SINGLE_INPUT_SWAP_REMOVES_NEGATIVE_EA")
    out["repair_approved"]=False
    out["scientific_hold_reason"]="Counterfactuals use nonindependent ERA-family sources, not tower validation; do not write forcing"
    return out


def summary(data,cols):
    return data.groupby(cols,sort=True).agg(
        events=("site","size"),
        source_QC2=("original_source_VPD_QC2","sum"),
        source_T_minus_grid_T_median_C=("delta_grid_T_minus_source_ERA_C","median"),
        grid_VPD_minus_source_VPD_median_hPa=("delta_grid_VPD_minus_source_ERA_hPa","median"),
        source_VPD_excess_median_hPa=("source_VPD_excess_over_source_es_water_hPa","median"),
        source_VPD_excess_max_hPa=("source_VPD_excess_over_source_es_water_hPa","max"),
        grid_VPD_dewpoint_median_hPa=("grid_VPD_dewpoint_hPa","median"),
        T_only_nonnegative=("T_only_counterfactual_ea_nonnegative","sum"),
        VPD_only_nonnegative=("VPD_only_counterfactual_ea_nonnegative","sum"),
    ).reset_index()


def self_test():
    a=pd.DataFrame({
        "site":["TST"],"source_csv_row":["1"],"time":["2020-01-01 00:00:00"],
        "original_ERA_T_C":[-20.0],"original_ERA_VPD_hPa":[2.0],
        "original_ERA_water_es_hPa":[float(water_saturation(np.array([-20.0]))[0])],
        "original_ERA_implied_ea_hPa":[float(water_saturation(np.array([-20.0]))[0]-2.0)],
        "VPD_ERA_excess_over_water_es_hPa":[float(2-water_saturation(np.array([-20.0]))[0])],
        "source_ERA_QC2":[True],
        "retained_T_minus_ERA_T_C":[0.0],"original_F_T_minus_ERA_T_C":[0.0],
    })
    b=pd.DataFrame({
        "site":["TST"],"source_csv_row":["1"],"time":["2020-01-01 00:00:00"],
        "grid_temperature_C":[-15.0],"grid_dewpoint_C":[-18.0],
        "grid_dewpoint_absolute_e_hPa":[float(water_saturation(np.array([-18.0]))[0])],
        "clock_offset_hours_hypothesis":[-7],
    })
    z=pair(a,b,expected_n=1,expected_sites={"TST":1})
    q=analyze(z,required_n=1)
    if not(q.source_implied_ea_water_hPa.iloc[0]<0 and q.both_grid_ea_positive.iloc[0]):
        raise ValueError("Negative source versus valid grid pressure self-test failed")
    if q.repair_approved.any() or q.clock_approved.any():
        raise ValueError("Self-test falsely approved repairs or offsets")
    print("STAGE10J SELF-TEST PASS: exact event join, source negative-ea, dewpoint positive-ea, counterfactual flags",flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=p.parse_args()
    print("STAGE10J — SOURCE ERA vs ERA5-LAND VPD/T COUNTERFACTUALS | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    joined,receipt=preflight()
    results=analyze(joined)
    sites=summary(results,["site"])
    years=summary(results,["site","year"])
    months=summary(results,["site","year","month"])
    print("\n========== SOURCE vs GRID COUNTERFACTUAL DIAGNOSIS BY SITE ==========",flush=True)
    print(sites.to_string(index=False),flush=True)
    print("\n========== COUNTERFACTUAL CLASS COUNTS ==========",flush=True)
    print(results.review_class.value_counts().to_string(),flush=True)
    print(f"\nSTAGE10J SUMMARY: examined={len(results)}/1924 site_years={len(years)}/32 "
          f"source_negative_ea={int((results.source_implied_ea_water_hPa<0).sum())}/1924 "
          f"grid_ea_positive={int(results.both_grid_ea_positive.sum())}/1924 "
          "repair_approvals=0 clock_approvals=0",flush=True)
    print("RESTRICTION: numerical input substitutions are diagnostic counterfactuals only, not a forcing repair recipe.",flush=True)
    if args.check:
        print("CHECK ONLY: no files/reports written.",flush=True)
        return
    name="stage10j_ERA_counterfactuals_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=ROOT/"reports"/name
    out.mkdir(exist_ok=False)
    outputs={
        "1924_source_vs_grid_counterfactual_events.csv":results,
        "site_counterfactual_summary.csv":sites,
        "site_year_counterfactual_summary.csv":years,
        "site_year_month_counterfactual_summary.csv":months,
    }
    for filename,table in outputs.items():
        table.to_csv(out/filename,index=False)
    manifest={
        "source_stage10i":str(S10I),
        "source_stage10b":str(S10B),
        "source_stage10i_receipt_sha256":receipt["stage10i_receipt_sha256"],
        "source_stage10b_receipt_sha256":receipt["stage10b_receipt_sha256"],
        "events":1924,"site_years":32,
        "clock_approvals":0,"repair_approvals":0,
        "method":"stage10i exact original source ERA and stage10b UTC-midpoint ERA5-Land dewpoint; water es(T) independent recomputation; hypothetical single-input swaps only",
        "warning":"ERA5-Land not independent validation; source ERA may be separately downscaled/regressed; no time shift or forcing updates",
        "output_sha256":{filename:digest(out/filename) for filename in outputs}
    }
    (out/"provenance_and_scientific_hold.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("STAGE10J REPORT DIR:",out,flush=True)
    print("NO ORIGINAL OR CANDIDATE FORCING, DATM, MODEL, CASE OR SLURM CHANGES.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10J STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

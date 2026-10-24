#!/usr/bin/env python3
"""AmeriFlux Batch03 Stage10k: exceptional-record and provenance science gate.

Audit the exact Stage10j SHA-pinned 1924-row diagnostic output; identify
the two VPD-only algebraic counterfactual failures and stratify all outcomes
by source VPD_QC2 vs other source provenance (QC1). Also report the magnitude
of source/grid VPD mismatch and original ERA temperature differences.

This explicitly DOES NOT select any ERA5-Land repair, clip negative VPD,
alter native timestamp, approve humidity/clock, or start CLM-FATES jobs.

--self-test: synthetic, no IRIDIS reads or reports.
--check: full source SHA and formula checks, no report writes.
--run: create new isolated 10k diagnostics and a SHA256 receipt ONLY.
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
S10I = ROOT/"reports/stage10i_era_vpd_physics_20261024T055509Z_b5a44de8"
S10J = ROOT/"reports/stage10j_ERA_counterfactuals_20261024T060351Z_eddc1a32"
KEYS = ["site", "source_csv_row", "time"]
SITES = {"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
         "US-MtB":15,"US-NR1":173,"US-NR3":1484}
S10J_FILES = {
    "1924_source_vs_grid_counterfactual_events.csv",
    "site_counterfactual_summary.csv",
    "site_year_counterfactual_summary.csv",
    "site_year_month_counterfactual_summary.csv",
}
VERSION = "stage10k-v1-20261024-scientific-gate"


def safe_file(p):
    p = Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink input: "+str(p))
    return p


def safe_dir(p):
    p = Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing/unsafe evidence directory: "+str(p))
    return p


def sha(path):
    h = hashlib.sha256()
    with safe_file(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    return json.loads(safe_file(path).read_text(encoding="utf-8"))


def numeric(d, col):
    if col not in d:
        raise ValueError("Missing numeric field: "+col)
    x = pd.to_numeric(d[col], errors="coerce").to_numpy(dtype=float)
    x[(~np.isfinite(x)) | (x <= -9990)] = np.nan
    return x


def flags(d, col):
    if col not in d:
        raise ValueError("Missing flag: "+col)
    x = d[col].astype(str).str.strip().str.lower()
    if not x.isin(("true","false","1","0")).all():
        raise ValueError("Unexpected boolean representation: "+col)
    return x.isin(("true","1")).to_numpy(dtype=bool)


def e_water(t):
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))


def check_equal(name, a, b):
    good = np.isclose(a,b,rtol=1e-7,atol=1e-7,equal_nan=False)
    if not good.all():
        i = np.flatnonzero(~good)
        raise ValueError(f"{name} differs: {len(i)} rows, first idx {i[0]}")


def preflight():
    for p in (ROOT,S07,S10B,S10I,S10J):
        safe_dir(p)
    safe_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    j = load_json(S10J/"provenance_and_scientific_hold.json")
    i_receipt = sha(S10I/"science_provenance.json")
    b_receipt = sha(S10B/"provenance_and_science_hold.json")
    if (j.get("events")!=1924 or j.get("site_years")!=32
        or j.get("clock_approvals")!=0 or j.get("repair_approvals")!=0
        or j.get("source_stage10i")!=str(S10I)
        or j.get("source_stage10b")!=str(S10B)
        or j.get("source_stage10i_receipt_sha256")!=i_receipt
        or j.get("source_stage10b_receipt_sha256")!=b_receipt
        or set(j.get("output_sha256",{}))!=S10J_FILES):
        raise ValueError("Stage10j provenance or scientific-hold receipt mismatch")
    for name in S10J_FILES:
        if sha(S10J/name)!=j["output_sha256"][name]:
            raise ValueError("Stage10j output SHA mismatch: "+name)
    d = pd.read_csv(safe_file(S10J/"1924_source_vs_grid_counterfactual_events.csv"),
                    dtype={k:str for k in KEYS},keep_default_na=False,low_memory=False)
    if (len(d)!=1924 or d.duplicated(KEYS).any()
        or d.site.value_counts().to_dict()!=SITES
        or int(d.groupby(["site","year"]).ngroups)!=32):
        raise ValueError("Stage10j event IDs, site/year counts or duplicates differ")
    if flags(d,"repair_approved").any() or flags(d,"clock_approved").any():
        raise ValueError("Unexpected repair/clock approval")
    return d,j


def audit(d, check_expected=True):
    t_source = numeric(d,"source_TA_ERA_C")
    t_grid = numeric(d,"grid_T2m_C")
    td_grid = numeric(d,"grid_Tdew_C")
    source_vpd = numeric(d,"source_VPD_ERA_hPa")
    reported_grid_vpd = numeric(d,"grid_VPD_dewpoint_hPa")
    grid_vpd = e_water(t_grid) - e_water(td_grid)
    source_es = e_water(t_source)
    source_ea = source_es - source_vpd
    t_only = e_water(t_grid) - source_vpd
    v_only = source_es - grid_vpd
    for name,recorded,recomputed in [
        ("source es_water",numeric(d,"source_es_water_hPa"),source_es),
        ("source implied ea",numeric(d,"source_implied_ea_water_hPa"),source_ea),
        ("grid dewpoint-derived VPD",reported_grid_vpd,grid_vpd),
        ("T-only counterfactual",numeric(d,"T_only_counterfactual_ea_hPa"),t_only),
        ("VPD-only counterfactual",numeric(d,"VPD_only_counterfactual_ea_hPa"),v_only),
    ]:
        check_equal(name,recorded,recomputed)
    if not (np.isfinite(source_ea).all() and np.isfinite(grid_vpd).all() and
            (source_ea<0).all()):
        raise ValueError("Stage10j source negative-ea constraints no longer hold")
    if not np.array_equal(flags(d,"T_only_counterfactual_ea_nonnegative"),t_only>=0):
        raise ValueError("Stage10j T-only boolean flags differ")
    if not np.array_equal(flags(d,"VPD_only_counterfactual_ea_nonnegative"),v_only>=0):
        raise ValueError("Stage10j VPD-only boolean flags differ")
    cls = np.select([
        (t_only>=0)&(v_only>=0), (t_only>=0)&(v_only<0),
        (t_only<0)&(v_only>=0)
    ], [
        "BOTH_SINGLE_INPUT_SWAPS_REMOVE_NEGATIVE_EA",
        "GRID_T_ONLY_REMOVES_NEGATIVE_EA",
        "GRID_VPD_ONLY_REMOVES_NEGATIVE_EA"
    ],default="NEITHER_SINGLE_INPUT_SWAP_REMOVES_NEGATIVE_EA")
    if not (d.review_class.astype(str).to_numpy()==cls).all():
        raise ValueError("Stage10j review category differs from independently recomputed class")
    srcqc2=flags(d,"original_source_VPD_QC2")
    if check_expected:
        summary=pd.Series(cls).value_counts().to_dict()
        expected={
            "GRID_VPD_ONLY_REMOVES_NEGATIVE_EA":1736,
            "BOTH_SINGLE_INPUT_SWAPS_REMOVE_NEGATIVE_EA":186,
            "GRID_T_ONLY_REMOVES_NEGATIVE_EA":2,
        }
        if summary!=expected or int(srcqc2.sum())!=1866:
            raise ValueError("Stage10j original run results changed from operator report")
    out = d[KEYS].copy()
    out["year"]=pd.to_datetime(d.time,errors="raise").dt.year
    out["month"]=pd.to_datetime(d.time,errors="raise").dt.month
    out["native_source_VPD_QC2"]=srcqc2
    out["native_source_VPD_other_QC1"]=~srcqc2
    out["counterfactual_category"]=cls
    out["source_ERA_T_C"]=t_source
    out["grid_T2m_C"]=t_grid
    out["source_T_minus_grid_T_C"]=t_source-t_grid
    out["source_VPD_hPa"]=source_vpd
    out["grid_VPD_dewpoint_hPa"]=grid_vpd
    out["grid_VPD_minus_source_VPD_hPa"]=grid_vpd-source_vpd
    out["source_VPD_excess_over_es_hPa"]=source_vpd-source_es
    out["grid_VPD_excess_over_source_es_hPa"]=grid_vpd-source_es
    out["source_implied_ea_hPa"]=source_ea
    out["T_only_implied_ea_hPa"]=t_only
    out["VPD_only_implied_ea_hPa"]=v_only
    out["T_only_nonnegative"]=t_only>=0
    out["VPD_only_nonnegative"]=v_only>=0
    out["source_T_below_zero"]=t_source<0
    out["clock_approval"]=False
    out["repair_approval"]=False
    out["scientific_note"]="ERA-grid mixing for decomposition only; no replacement, no demonstrated source root cause"
    return out


def summarize(df,cols):
    t = df.groupby(cols,sort=True).agg(
        records=("site","size"),
        qc2_VPD=("native_source_VPD_QC2","sum"),
        VPD_only_nonnegative=("VPD_only_nonnegative","sum"),
        T_only_nonnegative=("T_only_nonnegative","sum"),
        median_source_T_minus_grid_T_C=("source_T_minus_grid_T_C","median"),
        median_grid_VPD_minus_source_VPD_hPa=("grid_VPD_minus_source_VPD_hPa","median"),
        median_original_source_excess_hPa=("source_VPD_excess_over_es_hPa","median"),
        max_original_source_excess_hPa=("source_VPD_excess_over_es_hPa","max"),
    ).reset_index()
    for label,key in (
        ("BOTH","BOTH_SINGLE_INPUT_SWAPS_REMOVE_NEGATIVE_EA"),
        ("VPD_ONLY","GRID_VPD_ONLY_REMOVES_NEGATIVE_EA"),
        ("T_ONLY","GRID_T_ONLY_REMOVES_NEGATIVE_EA"),
    ):
        filtered=df.loc[df.counterfactual_category.eq(key)]
        counts=filtered.groupby(cols).size().rename(label)
        idx=pd.MultiIndex.from_frame(t[cols]) if len(cols)>1 else pd.Index(t[cols[0]])
        t[label]=counts.reindex(idx,fill_value=0).to_numpy(dtype=int)
    return t


def self_test():
    # Synthetic cold meteorology: source VPD exceeds saturation at source T.
    # Scenario 1: grid VPD lower than source saturation; VPD-only removes.
    # Scenario 2: grid VPD higher than source saturation; changing only VPD
    # does not remove negative ea, but grid temperature-alone can.
    t_source=np.array([-20.0,-30.0])
    t_grid=np.array([-10.0,-10.0])
    td_grid=np.array([-25.0,-11.0])
    source_vpd=np.array([2.0,1.2])
    # Check algebra identities and phase-independent source negativity.
    source_ea=e_water(t_source)-source_vpd
    grid_vpd=e_water(t_grid)-e_water(td_grid)
    assert np.all(source_ea<0)
    assert grid_vpd[0]<e_water(t_source[0])
    assert grid_vpd[1]>e_water(t_source[1])
    assert (e_water(t_grid)-source_vpd>0).all()
    assert (e_water(t_source)-grid_vpd>=0).tolist()==[True,False]
    print("STAGE10K SELF-TEST PASS: two exception regimes and water saturation algebra",flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--check",action="store_true")
    group.add_argument("--run",action="store_true")
    args=p.parse_args()
    print("STAGE10K — EXCEPTIONAL COUNTERFACTUAL SOURCE AUDIT",VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    d,receipt=preflight()
    examined=audit(d)
    sites=summarize(examined,["site"])
    years=summarize(examined,["site","year"])
    exceptions=examined.loc[examined.counterfactual_category.eq(
        "GRID_T_ONLY_REMOVES_NEGATIVE_EA")].copy()
    if len(exceptions)!=2 or not exceptions.site.eq("US-NR3").all():
        raise ValueError("Exactly 2 US-NR3 VPD-only exceptions were expected")
    print("\n========== STAGE10K SOURCE VS GRID OUTCOMES BY SITE ==========")
    print(sites.to_string(index=False),flush=True)
    print("\n========== TWO VPD-ONLY FAILURE EXCEPTIONS (US-NR3) ==========")
    cols=KEYS+["source_ERA_T_C","grid_T2m_C","source_VPD_hPa",
               "grid_VPD_dewpoint_hPa","source_VPD_excess_over_es_hPa",
               "grid_VPD_excess_over_source_es_hPa","T_only_implied_ea_hPa",
               "VPD_only_implied_ea_hPa","native_source_VPD_QC2"]
    print(exceptions[cols].to_string(index=False),flush=True)
    print("\n========== QC ORIGIN BY COUNTERFACTUAL CATEGORY ==========")
    print(pd.crosstab(examined.counterfactual_category,
                      examined.native_source_VPD_QC2).to_string(),flush=True)
    print(f"\nSTAGE10K SUMMARY: event_rows={len(examined)}/1924 "
          f"VPD_only_nonnegative={int(examined.VPD_only_nonnegative.sum())}/1924 "
          f"T_only_nonnegative={int(examined.T_only_nonnegative.sum())}/1924 "
          f"exception_rows={len(exceptions)}/2 "
          "clock_approvals=0 repair_approvals=0",flush=True)
    print("SCIENCE HOLD: input-swap diagnostic is not evidence for data replacement.")
    if args.check:
        print("CHECK ONLY: no files written.",flush=True)
        return
    dest=ROOT/"reports"/("stage10k_exception_provenance_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    dest.mkdir(exist_ok=False)
    outputs={
        "exception_2_US-NR3_events.csv":exceptions,
        "1924_counterfactual_science_gate.csv":examined,
        "site_counterfactual_qc_reconciliation.csv":sites,
        "site_year_counterfactual_qc_reconciliation.csv":years
    }
    for name,frame in outputs.items():
        frame.to_csv(dest/name,index=False)
    evidence={
        "source_stage10j":str(S10J),
        "stage10j_receipt_sha256":sha(S10J/"provenance_and_scientific_hold.json"),
        "stage10i_receipt_sha256":sha(S10I/"science_provenance.json"),
        "event_rows":1924,"exception_rows":2,
        "clock_approvals":0,"repair_approvals":0,
        "source_era5land_is_not_independent":True,
        "interpretation":"Mathematical sensitivities only; original ERA thermodynamic inconsistency origin remains unproven",
        "output_sha256":{name:sha(dest/name) for name in outputs}
    }
    (dest/"scientific_hold_receipt.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("STAGE10K REPORT DIR:",dest,flush=True)
    print("NO FORCING, SOURCE, QCv5, DATM, CASE, RESTART OR SLURM CHANGES.")


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10K STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

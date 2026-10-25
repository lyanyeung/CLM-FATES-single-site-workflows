#!/usr/bin/env python3
"""Batch03 Stage12v: verify source MDS VPD consistency under source MDS TA.

Original US-Me6 2015/2017 + US-NR1 2022, exactly 355 source QC1 VPD
that are impossible under measured source TA_F (QC0), as established in
the signed Stage12u report. Test the original VPD_F_MDS against both
tower TA_F and TA_F_MDS, describe MDS source QC values without assuming
that MDS-specific *_QC has the 0/1/2 categorical meaning of *_F_QC.
Include all 32 original held VPD neighbor sides.

Scientific provenance only. No science release of source MDS or ERA
values, no source timestamps/T, VPD or P changes, no forcing/model runs.

--self-test: synthetic tests only; zero filesystem read/write.
--check: source/lineage SHA and full study; ZERO output writes.
--run: same validation + NEW isolated SHA-sealed SCIENCE REPORT ONLY.
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
sys.dont_write_bytecode=True

VERSION="batch03-stage12v-v1-20261025-MDS-VPD-MDS-T-QC-science-only"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
U=ROOT/"reports/stage12u_original_MDS_QC1_VPD_cross_temperature_source_20261025T183511Z_57431d0b"
T=ROOT/"reports/stage12t_original_VPD_QC1_full_year_physics_episodes_20261025T181302Z_7b987cae"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
U_RECEIPT="stage12u_original_VPD_MDS_source_SHA_receipt.json"
U_355="355_original_QC1_VPD_invalid_source_MDS_ERA_evidence.csv"
U_32="32_original_QC1_VPD_held_neighbor_MDS_T_cross_checks.csv"
YEARS={("US-Me6",2015):115,("US-Me6",2017):114,("US-NR1",2022):126}

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/symlink protected original evidence: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def num(x):
    return pd.to_numeric(x,errors="coerce")

def saturation(t):
    a=np.asarray(t,dtype=float)
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        return 6.112*np.exp(17.67*a/(a+243.5))

def physical(v,t):
    v=np.asarray(v,dtype=float)
    t=np.asarray(t,dtype=float)
    sat=saturation(t)
    return np.isfinite(t)&np.isfinite(v)&np.isfinite(sat)&(v>=0)&(v<sat)

def match(x,y,atol=1.e-6):
    x=np.asarray(x,dtype=float)
    y=np.asarray(y,dtype=float)
    return np.isfinite(x)&np.isfinite(y)&np.isclose(x,y,rtol=0,atol=atol)

def true(series):
    return series.astype(str).str.lower().eq("true")

def selftest():
    assert bool(physical([2.],[20.])[0])
    assert not bool(physical([24.],[20.])[0])
    assert bool(physical([24.],[25.])[0])
    assert match([2.,3.],[2.,3.]).all()
    assert true(pd.Series([True,"True","false"])).tolist()==[True,True,False]
    assert abs(float(saturation([20.])[0])-23.3695)<.01
    print("STAGE12V SELF-TEST PASS: original MDS VPD vs source MDS TA, original QC source and signed science gate; NO WRITES",flush=True)

def verify():
    rec=json.loads(safe(U/U_RECEIPT).read_text())
    if (rec.get("version")!="batch03-stage12u-v1-20261025-original-QC1-MDS-vs-native-ERA-T"
        or rec.get("original_355_QC1_TQC0_impossible_records_preserved") is not True
        or rec.get("original_32_source_neighbor_sides_preserved") is not True
        or rec.get("original_86_and_233_science_holds_unchanged") is not True
        or rec.get("new_source_or_model_repairs")!=0
        or rec.get("Postv5_approved")!=0
        or rec.get("DATM_ready")!=0
        or rec.get("spinup_authorized")!=0
        or rec.get("stage12t_signed_source_report_SHA256") != sha(
            T/"stage12t_full_year_original_VPD_source_SHA_receipt.json")):
        raise ValueError("Pinned Stage12u scientific source provenance changed")
    for name,digest in rec.get("output_SHA256",{}).items():
        if sha(U/name)!=digest:
            raise ValueError("Signed Stage12u source report SHA failed: "+name)
    t=json.loads(safe(T/"stage12t_full_year_original_VPD_source_SHA_receipt.json").read_text())
    if (t.get("original_86_holds_preserved") is not True
        or t.get("original_233_holds_preserved") is not True
        or t.get("new_source_repairs")!=0
        or t.get("Postv5_approved")!=0
        or t.get("DATM_ready")!=0
        or t.get("spinup_authorized")!=0):
        raise ValueError("Original Stage12t science holds changed")
    manifest=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    specs={r["site"]:r for r in manifest["sites"]}
    pins={str(Path(p).resolve()):digest for p,digest in manifest["input_sha256"].items()}
    for site in ("US-Me6","US-NR1"):
        if site not in specs:raise ValueError("Source inventory no site: "+site)
        for field in ("primary","era"):
            src=safe(specs[site][field])
            if sha(src)!=pins.get(str(src.resolve())):
                raise ValueError("Original FLUXMET/ERA source bytes changed: "+site)
    return specs

def audit():
    verify()
    data=pd.read_csv(safe(U/U_355),dtype={"native_key":str},low_memory=False)
    edges=pd.read_csv(safe(U/U_32),dtype={
        "neighbor_native_key":str,"held_native_key":str},low_memory=False)
    required=[
      "site","year","native_key",
      "original_TA_F_C","original_TA_F_QC",
      "original_VPD_F_hPa","original_VPD_F_QC",
      "original_VPD_F_MDS_hPa","original_VPD_F_MDS_QC",
      "original_TA_F_MDS_C","original_TA_F_MDS_QC",
      "MDS_fields_available","VPD_F_matches_available_MDS"]
    if not set(required)<=set(data.columns):
        raise ValueError("Original Stage12u 355 source schema changed")
    if (len(data)!=355 or len(edges)!=32
        or data.duplicated(["site","native_key"]).any()
        or not data[["site","year"]].apply(tuple,axis=1).isin(YEARS).all()
        or not data.original_TA_F_QC.eq(0).all()
        or not data.original_VPD_F_QC.eq(1).all()
        or not true(data.MDS_fields_available).all()
        or not true(data.VPD_F_matches_available_MDS).all()):
        raise ValueError("Original 355 native QC1 source sides or MDS match changed")
    for (site,year),expected in YEARS.items():
        if len(data.loc[(data.site==site)&(data.year==year)])!=expected:
            raise ValueError("Signed original site-year MDS discrepancy count changed")

    src_v=num(data.original_VPD_F_hPa).to_numpy()
    mds_v=num(data.original_VPD_F_MDS_hPa).to_numpy()
    tower_t=num(data.original_TA_F_C).to_numpy()
    mds_t=num(data.original_TA_F_MDS_C).to_numpy()
    if (not match(src_v,mds_v).all()
        or physical(src_v,tower_t).any()):
        raise ValueError("Original 355 QC1 raw/MDS physical discrepancy no longer valid")
    data["original_MDS_VPD_valid_under_own_MDS_T"]=physical(mds_v,mds_t)
    data["MDS_temperature_source_finite"]=np.isfinite(mds_t)
    data["MDS_T_minus_QC0_tower_T_C"]=mds_t-tower_t
    data["original_MDS_VPD_excess_over_es_MDS_T_hPa"]=mds_v-saturation(mds_t)
    data["MDS_VPD_QC_numeric"]=num(data.original_VPD_F_MDS_QC)
    data["MDS_T_QC_numeric"]=num(data.original_TA_F_MDS_QC)
    # QC columns are source numbers, not mapped to the consolidated *_F_QC definitions.
    data["science_only_no_automatic_repair"]=True

    # 32 signed event neighbor sides may reuse native timestamp, unlike 355 unique source rows.
    if (edges.duplicated(
        ["site","held_native_key","neighbor_native_key","neighbor_side"]).any()
        or not edges.original_QC1_VPD_hPa.notna().all()):
        raise ValueError("Original signed 32 side provenance changed")
    compare=data.merge(
        edges[["site","neighbor_native_key","held_native_key",
               "neighbor_side","source_origin_class","original_QC1_VPD_hPa"]],
        how="inner",left_on=["site","native_key"],right_on=["site","neighbor_native_key"],
        validate="one_to_many")
    if (len(compare)!=32
        or not match(compare.original_VPD_F_hPa,
                     compare.original_QC1_VPD_hPa).all()):
        raise ValueError("32 source-neighbor original MDS values do not join exactly")
    overall=data.groupby(["site","year"],as_index=False).agg(
        original_QC1_impossible_count=("native_key","size"),
        MDS_T_available=("MDS_temperature_source_finite","sum"),
        MDS_VPD_valid_at_MDS_T=("original_MDS_VPD_valid_under_own_MDS_T","sum"),
        median_MDS_minus_QC0_T_C=("MDS_T_minus_QC0_tower_T_C","median"),
        max_MDS_minus_QC0_T_C=("MDS_T_minus_QC0_tower_T_C","max"),
        median_MDS_VPD_excess_above_MDS_es_hPa=(
            "original_MDS_VPD_excess_over_es_MDS_T_hPa","median"),
        MDS_VPD_QC_present=("MDS_VPD_QC_numeric","count"),
        MDS_VPD_QC_min=("MDS_VPD_QC_numeric","min"),
        MDS_VPD_QC_median=("MDS_VPD_QC_numeric","median"),
        MDS_VPD_QC_max=("MDS_VPD_QC_numeric","max"),
        MDS_T_QC_present=("MDS_T_QC_numeric","count"),
        MDS_T_QC_median=("MDS_T_QC_numeric","median"))
    focused=compare.groupby(["site","year","source_origin_class"],
        as_index=False).agg(
        signed_QC1_original_neighbor_sides=("neighbor_native_key","size"),
        MDS_VPD_physical_at_MDS_T=(
            "original_MDS_VPD_valid_under_own_MDS_T","sum"),
        MDS_T_available=("MDS_temperature_source_finite","sum"),
        median_MDS_minus_QC0_T_C=("MDS_T_minus_QC0_tower_T_C","median"))
    # Track numeric QC distributions without inventing what scores mean.
    qc_long=[]
    for field in ("MDS_VPD_QC_numeric","MDS_T_QC_numeric"):
        for (site,year),g in data.groupby(["site","year"]):
            s=g[field]
            counts=s.value_counts(dropna=False)
            for value,n in counts.items():
                qc_long.append({
                   "site":site,"year":int(year),"original_MDS_quality_field":field,
                   "exact_quality_value":value,"count_355_invalid_source_rows":int(n),
                   "no_quality_semantics_inferred":True})
    qc_table=pd.DataFrame(qc_long)
    if (int(overall.original_QC1_impossible_count.sum())!=355
        or int(focused.signed_QC1_original_neighbor_sides.sum())!=32):
        raise ValueError("Original 355/32 MDS source QA partition failed")
    return data,compare,overall,focused,qc_table

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):g.add_argument("--"+x,action="store_true")
    options=ap.parse_args()
    print("STAGE12V — ORIGINAL MDS VPD VS MDS TA AND SOURCE MDS QC | "+VERSION,flush=True)
    selftest()
    if options.self_test:return
    allbad,sides,summary,focused,qc=audit()
    print("\n========== 355 SOURCE QC1 IMPOSSIBLE VPD: ORIGINAL MDS-T COMPATIBILITY ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\n========== 32 HELD SOURCE NEIGHBOR SIDES: MDS-T COMPATIBILITY ==========",flush=True)
    print(focused.to_string(index=False),flush=True)
    print("\n========== ORIGINAL MDS QC RAW VALUE COUNTS (NO UNDOCUMENTED QC INTERPRETATION) ==========",flush=True)
    print(qc.groupby(["site","year","original_MDS_quality_field"])
           .agg(distinct_numeric_values=("exact_quality_value","nunique"),
                invalid_source_records=("count_355_invalid_source_rows","sum"))
           .to_string(),flush=True)
    print("\nSTAGE12V SUMMARY: original_355_QC1_MDS_source_values=TRUE "
          "original_32_VPD_hold_neighbor_sides=TRUE "
          "original_86_plus_233_holds_preserved=TRUE "
          "no_T_P_time_changed=TRUE new_repairs=0 "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if options.check:
        print("STAGE12V CHECK ONLY: ZERO FILE WRITES.",flush=True)
        return
    folder=ROOT/"reports"/(
        "stage12v_MDS_VPD_temperature_and_QC_source_forensics_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid4().hex[:8])
    folder.mkdir(exist_ok=False,parents=True)
    frames={
        "355_original_QC1_MDS_VPD_vs_MDS_T_source_details.csv":allbad,
        "32_original_held_VPD_neighbor_MDS_T_audit.csv":sides,
        "three_site_year_MDS_VPD_MDS_T_QC_summary.csv":summary,
        "32_original_neighbor_MDS_T_screen_summary.csv":focused,
        "MDS_quality_raw_value_distribution_NO_ASSUMED_SEMANTICS.csv":qc}
    for name,frame in frames.items():frame.to_csv(folder/name,index=False)
    (folder/"SCIENCE_HOLD.md").write_text(
        "MDS QC raw values are not automatically equivalent to *_F_QC 0/1/2 "
        "source categories. MDS temperature comparison is a test of "
        "cross-variable physics only, not source truth. Retain all "
        "86 original T/VPD holds plus protected 233 earlier physical "
        "holds. No original FLUXMET or companion ERA edits, no station "
        "clock offsets, tower T/P, trial forcing, Post-v5/DATM/spinup "
        "approval or Slurm jobs.\n")
    outputs={name:sha(folder/name) for name in [*frames,"SCIENCE_HOLD.md"]}
    receipt={
      "version":VERSION,
      "original_stage12u_SHA256":sha(U/U_RECEIPT),
      "original_355_bad_QC1_MDS_source_values_preserved":True,
      "original_32_signed_VPD_neighbor_sides_preserved":True,
      "original_86_held_events_preserved":True,
      "original_233_prior_physics_holds_preserved":True,
      "original_source_T_P_VPD_clock_unchanged":True,
      "new_repairs":0,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":outputs}
    (folder/"stage12v_MDS_source_quality_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12V SOURCE-ONLY SCIENCE REPORT DIR:",folder,flush=True)
    print("NO ORIGINAL SOURCE, FORCING, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12V STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

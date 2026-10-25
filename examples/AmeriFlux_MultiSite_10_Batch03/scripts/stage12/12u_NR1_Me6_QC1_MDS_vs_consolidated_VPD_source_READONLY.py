#!/usr/bin/env python3
"""Stage12u — original QC1 VPD MDS provenance and same-time T-source consistency.

Source-only, SHA-protected original US-Me6 2015/2017 and US-NR1 2022.
Check VPD_F consolidated against optional VPD_F_MDS, VPD_F_MDS_QC,
TA_F_MDS and measured VPD, and compare VPD_F physical consistency against
original measured TA_F and paired native TA_ERA. Original FLUXMET may
omit MDS component columns: report ABSENT, never invent product values.

Stage12t 355 original QC1 impossible VPD records + 32 signed source
edge references remain science-only. Comparative physically plausible
alternative source is NOT approved for original site forcing or clocks.

--self-test synthetic source provenance/thermodynamics; zero file reads
--check sealed source + Stage12t annual and Stage12s 32-side verification;
        no writes
--run   new isolated SHA-receipted science REPORT ONLY (not DATM-ready).
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

VERSION = "batch03-stage12u-v1-20261025-original-QC1-MDS-vs-native-ERA-T"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
T = ROOT / "reports/stage12t_original_VPD_QC1_full_year_physics_episodes_20261025T181302Z_7b987cae"
S = ROOT / "reports/stage12s_32_QC1_native_VPD_pm6h_source_context_20261025T180547Z_6a9cc5ab"
R = ROOT / "reports/stage12r_32_QC1_native_VPD_source_physics_and_ERA_RH_20261025T094639Z_a770eeb8"
S07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
YEARS = {"US-Me6": (2015, 2017), "US-NR1": (2022,)}
REQUIRED = ["TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC"]
OPTIONAL = ["VPD_F_MDS", "VPD_F_MDS_QC", "TA_F_MDS", "TA_F_MDS_QC", "VPD"]
ERA_COLS = ["TIMESTAMP_START", "TA_ERA", "VPD_ERA"]
ANNUAL_FILE = "three_site_year_original_VPD_QC_source_physics.csv"
SIDES_FILE = "32_signed_QC1_invalid_VPD_sides_episode_and_QC0_anchors.csv"
EXPECTED_QC1_INVALID = {("US-Me6",2015):115,
                        ("US-Me6",2017):114,
                        ("US-NR1",2022):126}

def safe(p):
    p = Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Signed source missing or symlink " + str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()

def number(x):
    a = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a) | (a <= -9990)] = np.nan
    return a

def es(t):
    t=np.asarray(t, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def physical(v, t):
    sat=es(t)
    return np.isfinite(v)&np.isfinite(t)&np.isfinite(sat)&(v>=0)&(v<sat)

def equal(a,b,atol=1e-7):
    if pd.isna(a) or pd.isna(b):
        return pd.isna(a) and pd.isna(b)
    return abs(float(a)-float(b))<=atol

def selftest():
    v=np.asarray([28., 2., -2., np.nan])
    t=np.asarray([20., 20., 20., 20.])
    assert physical(v,t).tolist()==[False,True,False,False]
    assert physical(v,t+8).tolist()==[True,True,False,False]
    assert equal(2., 2.+1e-8) and equal(np.nan,np.nan)
    print("STAGE12U SELF-TEST PASS: original VPD QC source, optional MDS provenance, same-time alternative T physics; NO WRITES",flush=True)

def verify():
    t=json.loads(safe(T/"stage12t_full_year_original_VPD_source_SHA_receipt.json").read_text())
    s=json.loads(safe(S/"stage12s_science_context_SHA_receipt.json").read_text())
    r=json.loads(safe(R/"stage12r_science_only_SHA_receipt.json").read_text())
    if (t.get("version")!="batch03-stage12t-v1-20261025-three-source-years-original-VPD-QC-runs"
        or t.get("stage12s_SHA256")!=sha(S/"stage12s_science_context_SHA_receipt.json")
        or t.get("signed_32_original_QC1_sides_preserved") is not True
        or t.get("original_86_holds_preserved") is not True
        or t.get("original_233_holds_preserved") is not True
        or t.get("new_source_repairs")!=0
        or s.get("original_stage12r_SHA256")!=sha(R/"stage12r_science_only_SHA_receipt.json")
        or r.get("original_32_QC1_edges") is not True):
        raise ValueError("Stage12t/s/r exact original scientific source chain changed")
    for receipt,root in ((t,T),(s,S),(r,R)):
        if (receipt.get("Postv5_approved")!=0 or receipt.get("DATM_ready")!=0
            or receipt.get("spinup_authorized")!=0):
            raise ValueError("Original scientific HOLD protection unexpectedly changed")
        for name, digest in receipt["output_SHA256"].items():
            if sha(root/name)!=digest:
                raise ValueError("Original science SHA mismatch " + str(root/name))
    manifest=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    specs={a["site"]:a for a in manifest["sites"]}
    pins={str(Path(p).resolve()): digest for p,digest in manifest["input_sha256"].items()}
    for site in YEARS:
        if site not in specs:
            raise ValueError("Missing signed source site "+site)
        for k in ("primary","era"):
            p=safe(specs[site][k])
            if sha(p)!=pins.get(str(p.resolve())):
                raise ValueError("Original source bytes changed "+site+" "+k)
    q=pd.read_csv(safe(T/ANNUAL_FILE),low_memory=False)
    f=pd.read_csv(safe(T/SIDES_FILE),dtype={
       "held_native_key":str,"neighbor_native_key":str},low_memory=False)
    if (len(q)!=12 or len(f)!=32
        or not f.source_origin_class.isin(
              ("BOTH_FINITE_DIFFER","RAW_ONLY_FINITE")).all()
        or not f.original_source_VPD_F_QC.eq(1).all()
        or not f.original_source_TA_F_QC.eq(0).all()):
        raise ValueError("Original Stage12t signed census or 32 native sides changed")
    return specs,q,f

def read_source(site, year, spec):
    p=safe(spec["primary"])
    names=set(pd.read_csv(p,nrows=0).columns)
    if not set(REQUIRED)<=names:
        raise ValueError("Missing required original FLUXMET fields " +site+" "+str(year))
    avail=[name for name in OPTIONAL if name in names]
    a=pd.read_csv(p,usecols=REQUIRED+avail,
                   dtype={"TIMESTAMP_START":str},low_memory=False)
    b=pd.read_csv(safe(spec["era"]),usecols=ERA_COLS,
                   dtype={"TIMESTAMP_START":str},low_memory=False)
    def keep(d):
        d=d.loc[d.TIMESTAMP_START.str.startswith(str(year))].copy()
        d.sort_values("TIMESTAMP_START",inplace=True)
        d.reset_index(drop=True,inplace=True)
        if (len(d)!=17520 or d.TIMESTAMP_START.duplicated().any()):
            raise ValueError("Expected exact source-native 17520 HH "+site+" "+str(year))
        times=pd.to_datetime(d.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        if (times.iloc[0]!=pd.Timestamp(year,1,1)
            or times.iloc[-1]!=pd.Timestamp(year,12,31,23,30)
            or not (times.diff().iloc[1:]==pd.Timedelta(minutes=30)).all()):
            raise ValueError("Source noleap native clock changed "+site+" "+str(year))
        return d
    a=keep(a);b=keep(b)
    if not a.TIMESTAMP_START.equals(b.TIMESTAMP_START):
        raise ValueError("Original FLUXMET/ERA source native clock differed")
    out=pd.DataFrame({"site":site,"year":year,
                       "native_key":a.TIMESTAMP_START.astype(str)})
    for c in REQUIRED[1:]:
        out[c]=number(a[c])
    for c in OPTIONAL:
        out[c]=number(a[c]) if c in names else np.full(len(a),np.nan)
    for c in ERA_COLS[1:]:
        out[c]=number(b[c])
    out.attrs["available_optional_columns"]=avail
    return out

def analyze():
    specs,old,targets=verify()
    summaries=[];badrows=[];focused=[];headers=[]
    for site,yearlist in YEARS.items():
        for year in yearlist:
            a=read_source(site,year,specs[site])
            avail=set(a.attrs["available_optional_columns"])
            headers.append({
                "site":site,"year":year,**{
                "source_column_"+c+"_available":c in avail for c in OPTIONAL}
            })
            t=a.TA_F.to_numpy(dtype=float)
            v=a.VPD_F.to_numpy(dtype=float)
            qc=a.VPD_F_QC.to_numpy(dtype=float)
            taqc=a.TA_F_QC.to_numpy(dtype=float)
            te=a.TA_ERA.to_numpy(dtype=float)
            ve=a.VPD_ERA.to_numpy(dtype=float)
            tm=a.TA_F_MDS.to_numpy(dtype=float)
            vm=a.VPD_F_MDS.to_numpy(dtype=float)
            es_t=es(t)
            invalid=np.isfinite(t)&np.isfinite(v)&(
                (v<0)|(v>=es_t))
            scope=(qc==1)&(taqc==0)&invalid
            if int(scope.sum())!=EXPECTED_QC1_INVALID[(site,year)]:
                raise ValueError("Full-year original QC1 invalid VPD count changed "+site+" "+str(year))
            qrow=old.loc[(old.site==site)&(old.year==year)]
            origq=qrow.loc[qrow.source_VPD_F_QC.eq("QC1")]
            if (len(origq)!=1 or
                int(origq.physically_invalid_with_T_QC0.iloc[0])!=int(scope.sum())):
                raise ValueError("Signed Stage12t annual source QC1 count changed")
            valid_era_temp=physical(v,te)
            valid_era_vpd_tower=physical(ve,t)
            valid_era_vpd_era=physical(ve,te)
            mds_matches=np.isfinite(vm)&np.isfinite(v)&np.isclose(
                vm,v,rtol=0,atol=1e-6)
            if "VPD_F_MDS" in avail:
                scope_with_mds=scope&np.isfinite(vm)
                scope_mds_match=scope&mds_matches
            else:
                scope_with_mds=np.zeros(len(a),dtype=bool)
                scope_mds_match=np.zeros(len(a),dtype=bool)
            sel=np.flatnonzero(scope)
            for i in sel:
                badrows.append({
                    "site":site,"year":year,"native_key":a.native_key.iat[i],
                    "original_TA_F_C":t[i],"original_TA_F_QC":taqc[i],
                    "original_VPD_F_hPa":v[i],"original_VPD_F_QC":qc[i],
                    "water_es_at_original_tower_T_hPa":es_t[i],
                    "source_VPD_excess_over_es_hPa":v[i]-es_t[i],
                    "paired_native_TA_ERA_C":te[i],
                    "paired_native_VPD_ERA_hPa":ve[i],
                    "original_VPD_F_valid_at_TA_ERA":bool(valid_era_temp[i]),
                    "native_VPD_ERA_valid_at_tower_T":bool(valid_era_vpd_tower[i]),
                    "native_VPD_ERA_valid_at_ERA_T":bool(valid_era_vpd_era[i]),
                    "original_VPD_F_MDS_hPa":vm[i],
                    "original_VPD_F_MDS_QC":a.VPD_F_MDS_QC.iat[i],
                    "original_TA_F_MDS_C":tm[i],
                    "original_TA_F_MDS_QC":a.TA_F_MDS_QC.iat[i],
                    "original_VPD_measured_field_hPa":a.VPD.iat[i],
                    "MDS_fields_available":bool("VPD_F_MDS" in avail),
                    "VPD_F_matches_available_MDS":(
                        bool(mds_matches[i]) if "VPD_F_MDS" in avail
                        else pd.NA),
                    "source_VPD_F_valid_at_optional_TA_F_MDS":(
                        bool(physical(v[i:i+1],tm[i:i+1])[0])
                        if "TA_F_MDS" in avail and np.isfinite(tm[i])
                        else pd.NA),
                    "science_hold_unchanged":True
                })
            summaries.append({
                "site":site,"year":year,
                "source_QC1_VPD_invalid_with_original_T_QC0":int(scope.sum()),
                "invalid_QC1_VPD_becomes_physically_valid_at_native_ERA_T":int(
                    (scope&valid_era_temp).sum()),
                "invalid_QC1_original_VPD_vs_valid_native_ERA_VPD_at_tower_T":int(
                    (scope&valid_era_vpd_tower).sum()),
                "invalid_QC1_native_ERA_VPD_physical_at_native_ERA_T":int(
                    (scope&valid_era_vpd_era).sum()),
                "invalid_QC1_VPD_F_MDS_available_finite":int(scope_with_mds.sum()),
                "invalid_QC1_original_VPD_F_matches_native_MDS_VPD":int(
                    scope_mds_match.sum()),
                "VPD_F_MDS_source_column_available":"VPD_F_MDS" in avail,
                "TA_F_MDS_source_column_available":"TA_F_MDS" in avail,
                "VPD_measured_source_column_available":"VPD" in avail,
                "source_or_model_repairs":0})
            lookup={k:i for i,k in enumerate(a.native_key)}
            for x in targets.loc[
                (targets.site==site)&targets.neighbor_native_key.str.startswith(str(year))
            ].itertuples(index=False):
                i=lookup.get(x.neighbor_native_key)
                if (i is None or not scope[i]
                    or not equal(v[i],x.original_source_VPD_F_hPa)
                    or not equal(t[i],x.original_source_TA_F_C)):
                    raise ValueError("Original signed Stage12t focal native side or source value changed")
                focused.append({
                    "site":site,"year":year,"held_native_key":x.held_native_key,
                    "neighbor_native_key":x.neighbor_native_key,
                    "neighbor_side":x.neighbor_side,
                    "source_origin_class":x.source_origin_class,
                    "original_QC1_VPD_hPa":v[i],
                    "original_measured_QC0_T_C":t[i],
                    "original_es_tower_T_hPa":es_t[i],
                    "paired_native_TA_ERA_C":te[i],
                    "paired_native_VPD_ERA_hPa":ve[i],
                    "MDS_VPD_component_available":"VPD_F_MDS" in avail,
                    "VPD_F_equals_MDS_when_available":(
                        bool(mds_matches[i]) if "VPD_F_MDS" in avail
                        else pd.NA),
                    "original_QC1_VPD_valid_using_native_ERA_T":bool(
                        valid_era_temp[i]),
                    "native_companion_VPD_ERA_valid_using_tower_T":bool(
                        valid_era_vpd_tower[i]),
                    "native_companion_VPD_ERA_valid_using_ERA_T":bool(
                        valid_era_vpd_era[i]),
                    "original_Stage12t_run_duration_HH":x.run_duration_HH,
                    "no_scientific_release":True})
    annual=pd.DataFrame(summaries)
    bad=pd.DataFrame(badrows)
    focus=pd.DataFrame(focused)
    fields=pd.DataFrame(headers)
    if (len(annual)!=3 or len(bad)!=355 or len(focus)!=32
        or int(annual.source_QC1_VPD_invalid_with_original_T_QC0.sum())!=355
        or int(annual.source_or_model_repairs.sum())!=0):
        raise ValueError("Stage12u strict original 355/32 source-only census changed")
    return annual,bad,focus,fields

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    for label in ("self-test","check","run"):
        mode.add_argument("--"+label,action="store_true")
    a=ap.parse_args()
    print("STAGE12U — ORIGINAL QC1 MDS CONSOLIDATED VPD VS NATIVE SOURCE TEMPERATURE | "+VERSION,flush=True)
    selftest()
    if a.self_test:return
    annual,bad,focus,fields=analyze()
    print("\n========== SOURCE ORIGINAL MDS PRODUCT COLUMN AVAILABILITY ==========",flush=True)
    print(fields.to_string(index=False),flush=True)
    print("\n========== 355 ORIGINAL QC1 VPD PHYSICAL VIOLATIONS VERSUS MDS/ERA SOURCE ==========",flush=True)
    print(annual.to_string(index=False),flush=True)
    print("\n========== 32 HELD VPD-NEIGHBOR SIDES: SOURCE TEMPERATURE CROSS-COMPARISON ==========",flush=True)
    print(focus.groupby(["site","year","source_origin_class"],
         as_index=False).agg(
         source_sides=("neighbor_native_key","size"),
         raw_QC1_VPD_physically_valid_with_ERA_T=(
             "original_QC1_VPD_valid_using_native_ERA_T","sum"),
         ERA_companion_VPD_valid_with_tower_T=(
             "native_companion_VPD_ERA_valid_using_tower_T","sum")
         ).to_string(index=False),flush=True)
    print("\nSTAGE12U SUMMARY: original_QC1_invalid_TQC0=355 "
          "source_sides=32 source_years=3 original_86_holds_preserved=TRUE "
          "original_233_holds_preserved=TRUE new_repairs=0 "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if a.check:
        print("STAGE12U CHECK ONLY: ZERO SOURCE, REPORT, FORCING OR MODEL WRITES.",flush=True)
        return
    dest=ROOT/"reports"/(
       "stage12u_original_MDS_QC1_VPD_cross_temperature_source_"
       +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
       +"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    reports={
       "three_site_year_MDS_native_source_availability.csv":fields,
       "355_original_QC1_VPD_invalid_source_MDS_ERA_evidence.csv":bad,
       "32_original_QC1_VPD_held_neighbor_MDS_T_cross_checks.csv":focus,
       "three_site_year_QC1_MDS_vs_ERA_source_summary.csv":annual
    }
    for name,data in reports.items():
        data.to_csv(dest/name,index=False)
    (dest/"SCIENCE_HOLD.md").write_text(
       "MDS provenance and cross-temperature physical plausibility ONLY. "
       "Official FLUXNET VPD_F_QC=1 means good-quality MDS gapfilled, not "
       "measured; QC0 measured; QC2 ERA-downscaled. If the original "
       "FLUXMET product lacks MDS component fields, they remain "
       "unavailable (never invented). ERA T or alternative VPD may pass "
       "a physics test but are not approved tower forcing replacements. "
       "No changes to signed original 86/233 holds, native source, "
       "T/P/clock, previous trial outputs, models or DATM/spinup.\n")
    hashes={name:sha(dest/name) for name in [*reports,"SCIENCE_HOLD.md"]}
    receipt={
       "version":VERSION,
       "stage12t_signed_source_report_SHA256":sha(
           T/"stage12t_full_year_original_VPD_source_SHA_receipt.json"),
       "original_355_QC1_TQC0_impossible_records_preserved":True,
       "original_32_source_neighbor_sides_preserved":True,
       "original_86_and_233_science_holds_unchanged":True,
       "source_T_P_VPD_native_time_unchanged":True,
       "new_source_or_model_repairs":0,
       "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
       "output_SHA256":hashes}
    (dest/"stage12u_original_VPD_MDS_source_SHA_receipt.json").write_text(
       json.dumps(receipt,indent=2)+"\n")
    print("STAGE12U SOURCE-ONLY SHA REPORT DIR:",dest,flush=True)
    print("NO ORIGINAL SOURCE, FORCING, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as err:
        print("STAGE12U STOP:",err,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

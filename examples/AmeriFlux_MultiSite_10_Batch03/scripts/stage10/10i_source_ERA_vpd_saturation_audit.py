#!/usr/bin/env python3
"""Batch03 Stage10i: diagnose subzero ERA VPD vs ERA air-temperature saturation.

Inputs (all immutable SHA checked):
  * Stage10h-v2 report: literal source QC0/1/2, exact-timestamp matched TA_ERA,
    VPD_ERA, raw TA_F/VPD_F for all 1924 Stage10d event identities.
  * Stage08c exact report: original ERA_RH_pct and reason classifications.
  * Stage10b report: SHA receipt pinning the Stage08c diagnostic data.
  * Stage10d immutable event register and Stage07 incomplete hold marker.

Independent recomputation of Stage08c's liquid-water vapour pressure:
   e_s_water(TA_ERA) [hPa] = 6.112*exp(17.67*T/(T+243.5))
   e_a_ERA [hPa] = e_s_water(TA_ERA) - VPD_ERA
   RH_ERA [%] = 100*e_a_ERA/e_s_water(TA_ERA)

Also calculates a separate ice-saturation sensitivity without treating ice
supersaturation or phase conventions as automatic correction approvals.
Rows where VPD_ERA>e_s_water(TA_ERA) have NEGATIVE implied water vapour
pressure already in the paired ERA source; tower/gridded mixture is not
necessary to create the anomaly. This is an algebraic diagnostic, not proof
of which upstream processing step generated the original inconsistency.

Never clips RH, replaces forcing, changes timestamps/PFT, or starts jobs.
--self-test: pure in-memory regression.
--check: full SHA/evidence check and output in memory, NO files written.
--run: create a NEW isolated diagnostic CSV/receipt directory only.
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

sys.dont_write_bytecode=True
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE08C=ROOT/"reports/stage08c_era_humidity_20261022T031437Z_512e8731"
STAGE10B=ROOT/"reports/stage10b_external_humidity_20261024T040142Z_be6a9d78"
STAGE10D=ROOT/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
STAGE10H=ROOT/"reports/stage10h_original_source_provenance_20261024T054425Z_faf342a8"
EXPECTED={"US-Kon":229,"US-MMS":18,"US-Me2":4,"US-Me6":1,
          "US-MtB":15,"US-NR1":173,"US-NR3":1484}
KEYS=["site","source_csv_row","time"]
H_FILES={
  "original_qc_source_classes_at_1924_blockers.csv",
  "affected_years_source_qc_distributions.csv",
  "US-NR3_2017_2018_2023_source_qc.csv",
  "site_blocker_source_qc_summary.csv",
  "primary_vs_ERA_timestamp_coverage.csv",
}
VER="stage10i-v1-20261024-era-water-vpd-diagnosis"


def file(path):
    path=Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or unsafe regular evidence file: "+str(path))
    return path


def directory(path):
    path=Path(path)
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Missing or unsafe evidence directory: "+str(path))
    return path


def sha256(path):
    h=hashlib.sha256()
    with file(path).open("rb") as inp:
        for part in iter(lambda: inp.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()


def read_json(path):
    return json.loads(file(path).read_text(encoding="utf-8"))


def getnum(df,key):
    if key not in df:
        raise ValueError("Required numeric field missing: "+key)
    x=pd.to_numeric(df[key],errors="coerce").to_numpy(dtype=float)
    x[(~np.isfinite(x))|(x<=-9990)]=np.nan
    return x


def water_es(t):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))


def ice_es(t):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))


def exact_pair(source,diagnostic):
    for a in (source,diagnostic):
        if a.duplicated(KEYS).any():
            raise ValueError("Duplicate (site,original row,time) IDs in source or diagnostic")
    if set(map(tuple,source[KEYS].to_numpy()))!=set(map(tuple,diagnostic[KEYS].to_numpy())):
        raise ValueError("Source and Stage08c event row identities differ")
    result=diagnostic.merge(source,on=KEYS,how="inner",validate="one_to_one",
                            suffixes=("_stage08c","_stage10h"))
    if len(result)!=1924 or result.site.value_counts().to_dict()!=EXPECTED:
        raise ValueError("Source matched record count differs from 1924")
    return result


def verify():
    for p in (ROOT,STAGE07,STAGE08C,STAGE10B,STAGE10D,STAGE10H):
        directory(p)
    file(STAGE07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    hb=read_json(STAGE10H/"read_only_provenance.json")
    bb=read_json(STAGE10B/"provenance_and_science_hold.json")
    db=read_json(STAGE10D/"read_only_provenance.json")
    if (hb.get("selected_events")!=1924 or hb.get("selected_site_years")!=32
        or hb.get("source_era_alignment")!="EXACT_TIMESTAMP_ONLY_NO_POSITIONAL_JOIN_NO_TIME_SHIFT"
        or hb.get("scientific_status")!="READ-ONLY SOURCE PROVENANCE; ALL 1924 REPAIRS UNAPPROVED"
        or hb.get("external_ERA_is_independent") is not False
        or set(hb.get("output_sha256",{}))!=H_FILES
        or hb.get("stage07_input_manifest_sha256")!=sha256(STAGE07/"exact_input_manifest.json")
        or hb.get("stage10d_provenance_sha256")!=sha256(STAGE10D/"read_only_provenance.json")):
        raise ValueError("Stage10h-v2 receipt/hold/lineage mismatch")
    for name in H_FILES:
        if sha256(STAGE10H/name)!=hb["output_sha256"][name]:
            raise ValueError("Stage10h SHA changed: "+name)
    cfile=STAGE08C/"era_humidity_residual_details.csv"
    if (bb.get("decision")!="ALL ROWS SCIENTIFIC HOLD; NO REPLACEMENTS APPROVED"
        or bb.get("original_provenance",{}).get("stage08c")!=sha256(cfile)):
        raise ValueError("Stage08c SHA differs from Stage10b pinned provenance")
    dfile=STAGE10D/"all_1924_manual_review.csv"
    if (db.get("events")!=1924 or db.get("no_replacement_approved") is not True
        or db.get("output_sha256",{}).get(dfile.name)!=sha256(dfile)):
        raise ValueError("Stage10d event register is not original/pinned/unapproved")

    a=pd.read_csv(file(STAGE10H/"original_qc_source_classes_at_1924_blockers.csv"),
                  dtype={k:str for k in KEYS},low_memory=False,keep_default_na=False)
    b=pd.read_csv(file(cfile),dtype={k:str for k in KEYS},
                  low_memory=False,keep_default_na=False)
    d=pd.read_csv(file(dfile),dtype={k:str for k in KEYS},
                  low_memory=False,keep_default_na=False)
    for obj in (a,b,d):
        if len(obj)!=1924 or obj.duplicated(KEYS).any():
            raise ValueError("1924-row event data or source identities altered")
    aset=set(map(tuple,a[KEYS].to_numpy()))
    if aset!=set(map(tuple,b[KEYS].to_numpy())) or aset!=set(map(tuple,d[KEYS].to_numpy())):
        raise ValueError("Stage08c/Stage10d/Stage10h 1924 event IDs differ")
    needed_a={"TA_ERA","VPD_ERA","TA_F","VPD_F","TA_F_QC_raw",
              "VPD_F_QC_raw","original_ERA_timestamp_matched"}
    needed_b={"TA_ERA_C","VPD_ERA_hPa","ERA_RH_pct","TA_before_fallback_C",
              "VPD_before_fallback_hPa","rejection_primary_reason"}
    if not needed_a<=set(a.columns) or not needed_b<=set(b.columns):
        raise ValueError("Unexpected Stage10h-v2 / Stage08c detail schema")
    if not b.rejection_primary_reason.eq("ERA_RH_BELOW_MINUS2_PCT").all():
        raise ValueError("Stage08c rejection type is not uniform as expected")
    if not a.original_ERA_timestamp_matched.astype(str).str.lower().eq("true").all():
        raise ValueError("An event lacks exact-timestamp original ERA evidence")
    return exact_pair(a,b),hb


def analyse(df):
    t_era=getnum(df,"TA_ERA_C")
    v_era=getnum(df,"VPD_ERA_hPa")
    t_era_source=getnum(df,"TA_ERA")
    v_era_source=getnum(df,"VPD_ERA")
    t_retained=getnum(df,"TA_before_fallback_C")
    t_f=getnum(df,"TA_F")
    v_f=getnum(df,"VPD_F")
    qc_t=getnum(df,"TA_F_QC_raw")
    qc_v=getnum(df,"VPD_F_QC_raw")
    recorded_rh=getnum(df,"ERA_RH_pct")

    if not (np.isfinite(t_era).all() and np.isfinite(v_era).all()
            and np.isfinite(recorded_rh).all()):
        raise ValueError("Nonfinite original ERA thermodynamic source input")
    for name,x,y in (("source-vs-Stage08c TA_ERA",t_era_source,t_era),
                     ("source-vs-Stage08c VPD_ERA",v_era_source,v_era)):
        if not np.isclose(x,y,atol=1e-7,rtol=1e-8,equal_nan=False).all():
            raise ValueError(name+" mismatch. Check original provenance before diagnostic.")
    es_era=water_es(t_era)
    rh_calc=100*(es_era-v_era)/es_era
    if not np.isclose(rh_calc,recorded_rh,atol=1e-6,rtol=1e-8).all():
        raise ValueError("Stage08c ERA_RH_pct fails independent liquid-water recalculation")
    if not (recorded_rh < -2).all():
        raise ValueError("Evidence includes nonnegative/eligible ERA relative humidity")
    if not np.all(v_era>es_era):
        raise ValueError("ERA VPD does not exceed source water saturation as expected")
    if not np.isfinite(t_retained).all():
        raise ValueError("Retained source temperatures missing; cannot compare")
    if np.any(~np.isin(qc_v,[0,1,2])) or np.any(~np.isin(qc_t,[0,1,2])):
        raise ValueError("Unexpected raw QC origin codes in residual event scope")
    if (int(np.sum(qc_v==2))!=1866 or int(np.sum(qc_v==1))!=58
            or int(np.sum(qc_v==0))!=0):
        raise ValueError("Stage10h source QC distribution differs from operator-verified 1866/58/0")

    source_match=(qc_v==2) & np.isfinite(v_f) & (np.abs(v_f-v_era)<=0.01)
    if int(source_match.sum())!=1866:
        raise ValueError("Stage10h QC2 original source VPD does not match ERA at 0.01 hPa")

    es_retained=water_es(t_retained)
    es_f=water_es(t_f)
    es_ice=ice_es(t_era)
    ea_era=es_era-v_era
    frame=df[KEYS+["rejection_primary_reason"]].copy()
    frame["year"]=pd.to_datetime(frame.time,errors="raise").dt.year
    frame["month"]=pd.to_datetime(frame.time,errors="raise").dt.month
    frame["review_priority"]=df["review_priority"].astype(str) if "review_priority" in df else "NOT_JOINED"
    frame["TA_F_QC"]=qc_t
    frame["VPD_F_QC"]=qc_v
    frame["original_ERA_T_C"]=t_era
    frame["original_ERA_VPD_hPa"]=v_era
    frame["original_ERA_water_es_hPa"]=es_era
    frame["original_ERA_implied_ea_hPa"]=ea_era
    frame["original_ERA_RH_water_pct"]=rh_calc
    frame["VPD_ERA_excess_over_water_es_hPa"]=v_era-es_era
    frame["original_ERA_ice_es_hPa"]=es_ice
    frame["VPD_ERA_excess_over_ice_es_hPa"]=v_era-es_ice
    frame["ERA_ice_implied_ea_hPa_if_VPD_unchanged"]=es_ice-v_era
    frame["raw_F_T_C"]=t_f
    frame["raw_F_VPD_hPa"]=v_f
    frame["raw_F_water_RH_pct"]=100*(es_f-v_f)/es_f
    frame["original_F_T_minus_ERA_T_C"]=t_f-t_era
    frame["retained_T_C"]=t_retained
    frame["retained_T_minus_ERA_T_C"]=t_retained-t_era
    frame["ERA_VPD_at_retained_T_water_RH_pct"]=100*(es_retained-v_era)/es_retained
    frame["source_VPD_ERA_matched_at_0p01hPa"]=source_match
    frame["source_ERA_QC2"]=qc_v==2
    frame["source_MDS_or_QC1_VPD"]=qc_v==1
    frame["ERA_pair_already_negative_vapour_pressure"]=ea_era<0
    frame["clock_or_humidity_approved"]=False
    frame["science_interpretation"]="ERA_T+VPD algebraically incompatible with liquid-water saturation; upstream cause unproven"
    return frame


def group_summary(table,columns):
    return table.groupby(columns,sort=True).agg(
       events=("site","size"),
       VPD_QC2=("source_ERA_QC2","sum"),
       QC2_close_to_ERA=("source_VPD_ERA_matched_at_0p01hPa","sum"),
       median_ERA_RH_water_pct=("original_ERA_RH_water_pct","median"),
       median_VPD_excess_over_water_es_hPa=("VPD_ERA_excess_over_water_es_hPa","median"),
       max_VPD_excess_over_water_es_hPa=("VPD_ERA_excess_over_water_es_hPa","max"),
       median_retained_T_minus_ERA_C=("retained_T_minus_ERA_T_C","median"),
       median_raw_F_T_minus_ERA_C=("original_F_T_minus_ERA_T_C","median"),
    ).reset_index()


def selftest():
    df=pd.DataFrame([{
       "site":"US-TEST","source_csv_row":"1","time":"2026-01-01 00:00:00",
       "rejection_primary_reason":"ERA_RH_BELOW_MINUS2_PCT",
       "TA_ERA_C":-20.0,"VPD_ERA_hPa":2.0,
       "TA_ERA":-20.0,"VPD_ERA":2.0,
       "TA_F":-20.0,"VPD_F":2.0,
       "TA_F_QC_raw":2,"VPD_F_QC_raw":2,
       "TA_before_fallback_C":-20.0
    }])
    s=water_es(np.array([-20.0]))[0]
    assert 0<s<2
    assert 100*(s-2)/s<0
    assert ice_es(np.array([-20.0]))[0]<s
    b=df.loc[:,KEYS].copy()
    b["ERA_RH_pct"]=100*(s-2)/s
    assert len(b)==1 and b.ERA_RH_pct.iloc[0]<-2
    c=exact_pair(df,b[KEYS])
    assert len(c)==1
    print("STAGE10I SELF-TEST PASS: subzero water/ice saturation and literal row identity",flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    choice=p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--self-test",action="store_true")
    choice.add_argument("--check",action="store_true")
    choice.add_argument("--run",action="store_true")
    args=p.parse_args()
    print("STAGE10I — SOURCE ERA SUBZERO VPD SATURATION INCONSISTENCY",VER,flush=True)
    selftest()
    if args.self_test:
        return
    matched,receipt=verify()
    result=analyse(matched)
    sites=group_summary(result,["site"])
    years=group_summary(result,["site","year"])
    months=group_summary(result,["site","year","month"])
    print("\n========== ERA LIQUID-WATER VPD OVERAGE BY SITE ==========",flush=True)
    print(sites.to_string(index=False),flush=True)
    print("\n========== SOURCE VPD ORIGIN CHECK ==========",flush=True)
    print(pd.crosstab(result.site,result.VPD_F_QC,dropna=False).to_string(),flush=True)
    print(f"\nSTAGE10I SUMMARY: rechecked={len(result)}/1924 "
          f"ERA_water_ea_negative={int(result.ERA_pair_already_negative_vapour_pressure.sum())}/1924 "
          f"original_VPD_QC2={int(result.source_ERA_QC2.sum())}/1866 "
          f"year_sites={len(years)}/32 clock_approved=0 repairs_approved=0",flush=True)
    print("CAUTION: algebraic source inconsistency does NOT prove which upstream step caused it.",flush=True)
    if args.check:
        print("CHECK ONLY: no files written.",flush=True)
        return
    out=ROOT/"reports"/("stage10i_era_vpd_physics_" +
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    outputs={
        "all_1924_source_ERA_water_saturation_inconsistencies.csv":result,
        "site_ERA_overage_summary.csv":sites,
        "site_year_ERA_overage_summary.csv":years,
        "site_year_month_ERA_overage_summary.csv":months,
    }
    for filename,frame in outputs.items():
        frame.to_csv(out/filename,index=False)
    proof={
        "stage10h_v2_receipt_sha256":sha256(STAGE10H/"read_only_provenance.json"),
        "stage10b_receipt_sha256":sha256(STAGE10B/"provenance_and_science_hold.json"),
        "stage08c_details_sha256":sha256(STAGE08C/"era_humidity_residual_details.csv"),
        "stage10d_ledger_sha256":sha256(STAGE10D/"all_1924_manual_review.csv"),
        "source_rows":1924,"site_years":32,
        "scope":"original paired ERA temperature/VPD and source QC; no time shift or source edits",
        "decision":"SCIENCE HOLD; ZERO REPAIRS AND ZERO TIME OFFSETS APPROVED",
        "nonindependence_note":"FLUXNET VPD_F QC2 derives from downscaled ERA; ERA5-Land is ERA-dependent.",
        "phase_note":"All residuals use Stage08c liquid-water saturation. Ice sensitivity is diagnostic only.",
        "output_sha256":{name:sha256(out/name) for name in outputs}
    }
    (out/"science_provenance.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
    print("STAGE10I REPORT DIR:",out,flush=True)
    print("NO FORCING, DATA, DATM, CASE OR SLURM JOB MODIFIED.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10I STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

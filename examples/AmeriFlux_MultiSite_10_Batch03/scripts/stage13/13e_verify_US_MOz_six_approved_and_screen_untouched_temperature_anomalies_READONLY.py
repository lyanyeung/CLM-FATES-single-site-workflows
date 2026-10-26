#!/usr/bin/env python3
"""Stage13e. Operator-approved US-MOz exact 6/6 Stage07 candidate changes;
independent original-tower/standalone-ERA/source-QC context around previously
UNEDITED suspicious 2005-01-06 09:00 TA +8.024 C, plus an all-years screened
inventory of OTHER large isolated candidate tower-temperature spikes.

No raw source, candidate, time, PFT, forcing, DATM, case, Slurm or approvals
are changed. --check NO WRITES, --run isolated SHA-sealed reports only.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
V="batch03-stage13e-v1-20261026-moz-6-approved-and-unmodified-09T"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13D=ROOT/"reports/stage13d_three_site_postv5_QC0_science_gates_20261026T173233Z_79eebcb0"
SITE="US-MOz"
FIRST,LAST=2004,2021
TGT=pd.Timestamp("2005-01-06 09:00:00")
MET=("TA_F","TA_F_QC","VPD_F","VPD_F_QC")
EMET=("TA_ERA","VPD_ERA")
EXACT_FIVE={
 ("2004-12-03T23:30:00","TA_F"):(2,-132.985,1.753),
 ("2004-12-04T00:00:00","TA_F"):(2,-267.868,1.608),
 ("2004-12-04T00:30:00","TA_F"):(2,-133.275,1.463),
 ("2005-01-06T10:00:00","TA_F"):(1,17.66,-7.2055),
 ("2005-01-06T10:00:00","VPD_F"):(1,4.653,1.6939598679479135)}
EXACT_PRIOR={("2016-03-17T22:00:00","TA_F"):(0,-15.213,12.1715)}

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise RuntimeError("Absent/symlink source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def check_approval(p,prior=False):
    r=json.loads(safe(p).read_text())
    if prior:
        if r.get("schema")!="batch03-stage13d-qc0-operator-approval-v1":
            raise RuntimeError("Prior six-source QC0 approval schema changed")
        ev=[e for e in r["six_approved_specific_events"] if e["site"]==SITE]
        got={(pd.Timestamp(e["native_time"]).strftime("%Y-%m-%dT%H:%M:%S"),e["variable"]):
             (e["source_original_QC"],e["original_tower_TA_C"],e["approved_selected_TA_C"]) for e in ev}
        if got!=EXACT_PRIOR:
            raise RuntimeError("The already approved US-MOz QC0 source event changed")
    else:
        if r.get("schema")!="batch03-stage13e-scoped-operator-moz-5-v1":
            raise RuntimeError("Five additional US-MOz operator decisions not authenticated")
        if r.get("scientific_boundaries",{}).get("no_automatic_09_00_2005_temperature_change") is not True:
            raise RuntimeError("09:00 extra source hold not protected")
        ev=r.get("approved_five_original_stage07_events",[])
        got={(pd.Timestamp(e["native_time"]).strftime("%Y-%m-%dT%H:%M:%S"),e["variable"]):
             (e["official_QC"],e["original_value"],e["approved_candidate_value"]) for e in ev}
        if len(ev)!=5 or got!=EXACT_FIVE:
            raise RuntimeError("Operator's original exact 5 science approvals changed")

def native_csv(p,columns,tcolumn,source=True):
    df=pd.read_csv(safe(p),usecols=[tcolumn,*columns],dtype={tcolumn:str},low_memory=False)
    if source:
        ts=pd.to_datetime(df[tcolumn],format="%Y%m%d%H%M",errors="raise")
        mask=ts.dt.year.between(FIRST,LAST) & ~((ts.dt.month==2)&(ts.dt.day==29))
        df=df.loc[mask].copy()
        ts=ts.loc[mask]
    else:
        ts=pd.to_datetime(df[tcolumn],errors="raise")
    if ts.duplicated().any() or ts.isna().any():
        raise RuntimeError("Duplicate/NaT original time source: "+str(p))
    df=df.drop(columns=[tcolumn])
    df.index=pd.DatetimeIndex(ts,name="source_native_time")
    for c in columns:
        df[c]=pd.to_numeric(df[c],errors="coerce")
        df.loc[df[c]<=-9990,c]=np.nan
    return df

def selftest():
    assert len(EXACT_FIVE)==5 and len(EXACT_PRIOR)==1
    assert (set(EXACT_FIVE)&set(EXACT_PRIOR))==set()
    assert TGT + pd.Timedelta(minutes=60)==pd.Timestamp("2005-01-06 10:00")
    assert EXACT_FIVE[("2005-01-06T10:00:00","TA_F")][-1]==-7.2055
    print("STAGE13E SELF-TEST PASS | signed six MOz candidate edits, 09:00 preserved",flush=True)

def audit(prior,new):
    check_approval(prior,True)
    check_approval(new,False)
    manifest=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    s=dict((x["site"],x) for x in manifest["sites"])
    src=s[SITE]
    checks={str(Path(k).resolve()):v for k,v in manifest["input_sha256"].items()}
    for k in ("primary","era"):
        p=safe(src[k])
        if sha(p)!=checks.get(str(p.resolve())):
            raise RuntimeError("Source tower/ERA SHA mismatch: "+k)
    output=json.loads(safe(S07/"output_sha256.json").read_text())
    def signed(p):
        if sha(p)!=output.get(str(p.relative_to(S07))):
            raise RuntimeError("Signed Stage07 file modified: "+str(p))
        return p
    folder=S07/SITE/"forcing"
    file=folder/"processed_v5"/"US-MOz_CLM_forcing_2004_2021.csv"
    evpath=folder/"qc_v5"/"US-MOz_replacement_events.csv"
    manpath=folder/"qc_v5"/"US-MOz_manual_review.csv"
    frame=native_csv(signed(file),("TA_USE","VPD_USE","QBOT","PSRF"),"time",False)
    events=pd.read_csv(signed(evpath),dtype={"time":str})
    man=pd.read_csv(signed(manpath))
    if len(events)!=6 or len(man)!=0:
        raise RuntimeError("Signed Stage07 originally six MOz modifications, zero manual list changed")
    chosen={}
    for e in events.to_dict("records"):
        key=(pd.Timestamp(e["time"]).strftime("%Y-%m-%dT%H:%M:%S"),e["variable"])
        chosen[key]=(e["official_qc"],e["original_value"],e["final_value"])
    expected={**EXACT_FIVE,**EXACT_PRIOR}
    if set(chosen)!=set(expected):
        raise RuntimeError("Six approved keys do not cover exactly all original MOz candidate event changes")
    for k,e in expected.items():
        got=chosen[k]
        if not np.allclose(got,e,rtol=0,atol=1e-7):
            raise RuntimeError("Signed Stage07 science event differs from approved value: "+str(k))
    if TGT not in frame.index:
        raise RuntimeError("US-MOz requested anomalous source timestamp missing")
    src_t=native_csv(src["primary"],MET,"TIMESTAMP_START",True)
    era_t=native_csv(src["era"],EMET,"TIMESTAMP_START",True)
    if not frame.index.equals(src_t.index):
        raise RuntimeError("Signed successful selected forcing differs from original tower NOLEAP calendar")
    if not frame.index.equals(era_t.index):
        raise RuntimeError("Original standalone ERA5 source native timestamps differ")
    joined=src_t.join(era_t,validate="one_to_one").join(frame,validate="one_to_one")
    if len(joined)!=len(frame) or len(joined)!=315360:
        raise RuntimeError("Native 18-year noleap table incomplete")
    if not (np.isclose(joined.loc[TGT,"TA_F"],8.024,atol=1e-6) and
            np.isclose(joined.loc[TGT,"TA_ERA"],-7.096,atol=1e-6)):
        raise RuntimeError("Operator's separately held 09:00 observation source no longer matches")
    if not np.isclose(joined.loc[TGT,"TA_USE"],8.024,atol=1e-6):
        raise RuntimeError("09:00 was secretly modified or altered in signed Stage07")
    if (TGT,"TA_F") in chosen:
        raise RuntimeError("09:00 is already in signed Stage07 modifications; stop")
    result=[]
    for delta in range(-240,241,30):
        t=TGT+pd.Timedelta(minutes=delta)
        if t not in joined.index:raise RuntimeError("Missing context at "+str(t))
        a=joined.loc[t]
        result.append({
            "offset_minutes":delta,"original_source_native_timestamp":t.isoformat(),
            "tower_original_TA_C":a.TA_F,"tower_TA_F_QC":a.TA_F_QC,
            "standalone_ERA5_TA_C":a.TA_ERA,
            "stage07_candidate_TA_USE_C":a.TA_USE,
            "tower_minus_ERA_TA_C":a.TA_F-a.TA_ERA,
            "stage07_minus_ERA_TA_C":a.TA_USE-a.TA_ERA,
            "tower_original_VPD_hPa":a.VPD_F,"tower_VPD_F_QC":a.VPD_F_QC,
            "standalone_ERA_VPD_hPa":a.VPD_ERA,
            "stage07_candidate_VPD_hPa":a.VPD_USE,
            "stage07_QBOT_kgkg":a.QBOT,
            "operator_approved_09_00":False,
        })
    window=pd.DataFrame(result)
    # Identical tower+ERA values are not independent validation. Summarize
    # such duplicates by year as a provenance caution.
    years=joined.index.year
    equal=np.isclose(joined.TA_F.to_numpy(float),joined.TA_ERA.to_numpy(float),
                     rtol=0,atol=1e-9,equal_nan=False)
    year_eq=pd.DataFrame({"year":years,"equal":equal}).groupby("year").agg(
        compared_rows=("equal","size"),identical_TA_rows=("equal","sum"))
    year_eq["identical_fraction"]=year_eq.identical_TA_rows/year_eq.compared_rows
    # Very conservative candidate-temperature spike screen: both adjacent
    # halfhours agree to within 6C, center is >8C from their mean, and
    # independently ERA-derived tower mismatch is >8C. Screening only.
    temp=joined.TA_USE
    before=temp.shift(1);after=temp.shift(-1)
    neighbors_same_year=(joined.index.to_series().shift(1).dt.year==years)&(
                           joined.index.to_series().shift(-1).dt.year==years)
    dist=temp-(before+after)/2
    mask=(dist.abs()>8)&((before-after).abs()<6)&(
        (temp-joined.TA_ERA).abs()>8)&neighbors_same_year
    flagged=joined.loc[mask].copy()
    flagged["offset_to_neighbor_mean_C"]=dist.loc[mask]
    flagged["year"]=flagged.index.year
    flagged["operator_approved"]=False
    flagged.index.name="native_time"
    flagged=flagged.reset_index()
    flagged=flagged[["native_time","year","TA_F","TA_F_QC","TA_ERA","TA_USE",
        "VPD_F","VPD_F_QC","VPD_ERA","VPD_USE","offset_to_neighbor_mean_C",
        "operator_approved"]].copy()
    site_flags={
        "US_MOz_exact_Stage07_modified_records":6,
        "US_MOz_exact_operator_approved_modified_records":6,
        "US_MOz_original_and_selected_SHA_verified":True,
        "2005_01_06_09_00_TA_source_anomaly_is_present_and_UNMODIFIED":True,
        "2005_01_06_09_00_authorized_to_modify":False,
        "2005_01_06_09_00_tower_TA_C":8.024,
        "2005_01_06_09_00_ERA5_TA_C":-7.096,
        "2005_01_06_09_00_tower_QC":float(joined.loc[TGT,"TA_F_QC"]),
        "2005_01_06_09_00_original_VPD_hPa":float(joined.loc[TGT,"VPD_F"]),
        "2005_01_06_09_00_selected_VPD_hPa":float(joined.loc[TGT,"VPD_USE"]),
        "remaining_large_candidate_temperature_spike_screen_count":int(len(flagged)),
        "remaining_large_candidate_temperature_spike_screen_2005_count":
             int(flagged.year.eq(2005).sum()) if len(flagged) else 0,
        "US_MOz_surface_PFT_footprint_approved":False,
        "US_MOz_ZBOT_source_measurement_height_approved":False,
        "US_MOz_DATM_ready":False,"US_MOz_spinup_authorized":False,
        "science_gate":
           "HOLD_REVIEW_ORIGINAL_09T_AND_ANY_SCREENED_ANOMALIES_PLUS_PFT_ZBOT",
    }
    return window,flagged,year_eq.reset_index(),site_flags

def main():
    p=argparse.ArgumentParser()
    m=p.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):m.add_argument("--"+x,action="store_true")
    p.add_argument("--old-approval",type=Path)
    p.add_argument("--moz-approval",type=Path)
    a=p.parse_args()
    print("STAGE13E US-MOz FINAL APPROVED SIX + PRESERVED JAN 6 09:00 ANOMALY | "+V,flush=True)
    selftest()
    if a.self_test:return
    if not a.old_approval or not a.moz_approval:
        p.error("Require BOTH exact prior six-QC0 approval and new five-MOz approval JSON paths")
    window,flagged,eq,status=audit(a.old_approval,a.moz_approval)
    cols=["offset_minutes","original_source_native_timestamp","tower_original_TA_C",
      "tower_TA_F_QC","standalone_ERA5_TA_C","stage07_candidate_TA_USE_C",
      "tower_minus_ERA_TA_C","tower_original_VPD_hPa",
      "standalone_ERA_VPD_hPa","stage07_candidate_VPD_hPa"]
    print("\n=== FULL ORIGINAL TOWER / ERA / SELECTED ±4H OF 2005-01-06 09:00 ===",flush=True)
    print(window[cols].to_string(index=False,float_format=lambda x:f"{x:.3f}"),flush=True)
    print("\n=== FULL RELEASE AUTOMATIC SCREEN OF OTHER UNCHANGED LARGE TA SPIKES ===",flush=True)
    if len(flagged):
        print("CANDIDATE SCREEN COUNT",len(flagged),flush=True)
        print(flagged.head(40).to_string(index=False,float_format=lambda x:f"{x:.3f}"),flush=True)
        if len(flagged)>40:print("ADDITIONAL",len(flagged)-40,"FLAGGED: full untruncated CSV written only with --run",flush=True)
    else:print("ZERO matched conservative 8C two-sided centered isolated-spike screen",flush=True)
    print("\n=== TOWER VS ERA EXACTLY IDENTICAL TEMPERATURE FRACTION (2004/2005) ===",flush=True)
    print(eq.loc[eq.year.isin([2004,2005])].to_string(index=False),flush=True)
    print("\n=== SCIENTIFIC ADMISSION STATE ===",flush=True)
    for k,v in status.items():print(k,v,flush=True)
    if a.check:
        print("STAGE13E CHECK ONLY | NO FILE WRITES",flush=True);return
    out=ROOT/"reports"/("stage13e_MOz_six_approved_09T_recheck_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={"2005Jan06_09T_original_Tower_ERA_stage07_surrounding_4h.csv":window,
      "all_years_other_large_isolated_temperature_spike_SCREEN_ONLY.csv":flagged,
      "original_tower_and_ERA_exact_TA_equality_by_year.csv":eq}
    for name,df in files.items():df.to_csv(out/name,index=False)
    state="US-MOz_09T_UNCHANGED_AND_REQUIRES_OPERATOR_SOURCE_SCIENCE_REVIEW"
    (out/state).write_text(
       "All six modified Stage07 US-MOz records specifically approved by operator; "
       "additional 2005-01-06 09:00 source tower 8.024 C observation remains "
       "UNMODIFIED and is NOT approved for correction. The identical tower "
       "and reanalysis values in other periods do not prove independent ERA "
       "confirmation. No Post-v5, PFT footprint, ZBOT or spinup approval. "
       "No original/candidate/clock/model writes.\n")
    receipt={
      "version":V,
      "original_operator_six_QC0_approval_SHA256":sha(a.old_approval),
      "additional_five_MOz_operator_approval_SHA256":sha(a.moz_approval),
      "exact_Stage07_source_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
      "exact_six_US_MOz_Stage07_candidate_modifications_approved":True,
      "original_09T_2005_TA_preserved":True,
      "source_original_modified":False,
      "postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
      "output_SHA256":{name:sha(out/name) for name in [*files,state]}}
    (out/"stage13e_moz_six_scope_and_09T_science_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13E REPORT ONLY:",out,flush=True)
    print("NO RAW SOURCE, STAGE07 CANDIDATE, MODEL, CIME OR DATM WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("STAGE13E STOP:",ex,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

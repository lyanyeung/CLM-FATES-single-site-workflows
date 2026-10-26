#!/usr/bin/env python3
"""Stage13f: the ONLY three extra US-MOz QC0 centered temperature spikes
remaining after Stage13e. Display ±120 min native original tower TA, VPD,
QC, separate ERA5 companions, current Stage07 TA/VPD, and proposed midpoint
only as a diagnostic, never as a forcing edit.

Uses exact hashed Stage07 original met sources and existing hashed Stage13e
three-spike review manifest. No PFT/ZBOT block created by this tool.
No original or model writes, --run only writes a separate science report.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np

sys.dont_write_bytecode=True
V="batch03-stage13f-v1-20261026-three-MOz-original-QC0-neighbors"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13E=R/"reports/stage13e_MOz_six_approved_09T_recheck_20261026T174412Z_3e98ca6c"
TARGETS={
 "2014-04-02T10:00:00":(18.110,7.879),
 "2016-04-11T13:00:00":(23.671,12.214),
 "2016-04-14T06:30:00":(17.543,6.433)
}
OFFSETS=tuple(range(-120,121,30))
def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise RuntimeError("Missing or symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def timeaxis(p,columns,stamp,first,last):
    df=pd.read_csv(safe(p),usecols=[stamp,*columns],dtype={stamp:str},low_memory=False)
    if stamp=="TIMESTAMP_START":
        ts=pd.to_datetime(df[stamp],format="%Y%m%d%H%M",errors="raise")
        keep=ts.dt.year.between(first,last)&~((ts.dt.month==2)&(ts.dt.day==29))
        df=df.loc[keep].copy()
        ts=ts.loc[keep]
    else:ts=pd.to_datetime(df[stamp],errors="raise")
    if ts.isna().any() or ts.duplicated().any():raise RuntimeError("Source timeline duplicated/NaT "+str(p))
    df=df.drop(columns=[stamp])
    df.index=pd.DatetimeIndex(ts,name="native_time")
    for c in columns:
        df[c]=pd.to_numeric(df[c],errors="coerce")
        df.loc[df[c]<=-9990,c]=np.nan
    return df
def selftest():
    assert len(TARGETS)==3 and len(OFFSETS)==9
    assert OFFSETS==( -120,-90,-60,-30,0,30,60,90,120 )
    assert all(np.isfinite(a) and np.isfinite(b) for a,b in TARGETS.values())
    print("STAGE13F SELF-TEST PASS | THREE exact MOz QC0 original T spikes, zero writes",flush=True)

def audit():
    receipt=json.loads(safe(S13E/"stage13e_moz_six_scope_and_09T_science_SHA_receipt.json").read_text())
    if receipt.get("exact_six_US_MOz_Stage07_candidate_modifications_approved") is not True or \
       receipt.get("original_09T_2005_TA_preserved") is not True or \
       receipt.get("postv5_approved") is not False:
        raise RuntimeError("Stage13e approval/science status changed")
    p=S13E/"all_years_other_large_isolated_temperature_spike_SCREEN_ONLY.csv"
    if sha(p)!=receipt["output_SHA256"].get(p.name):
        raise RuntimeError("Stage13e original three-spike science evidence SHA mismatch")
    previous=pd.read_csv(p,dtype={"native_time":str},low_memory=False)
    expected_keys={pd.Timestamp(x) for x in TARGETS}
    if len(previous)!=3 or {pd.Timestamp(x) for x in previous.native_time}!=expected_keys:
        raise RuntimeError("Stage13e three remaining original QC0 candidate events changed")
    if previous.operator_approved.astype(str).str.lower().eq("true").any():
        raise RuntimeError("Original three-screened spikes unexpectedly approved")
    source=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    inp={str(Path(x).resolve()):y for x,y in source["input_sha256"].items()}
    spec=next(x for x in source["sites"] if x["site"]=="US-MOz")
    assert spec["first_year"]==2004 and spec["last_year"]==2021 and spec["native_minutes"]==30
    for k in ("primary","era"):
        pth=safe(spec[k])
        if sha(pth)!=inp.get(str(pth.resolve())):
            raise RuntimeError("Original Stage07 tower/ERA source changed "+k)
    outsha=json.loads(safe(S07/"output_sha256.json").read_text())
    selected=S07/"US-MOz/forcing/processed_v5/US-MOz_CLM_forcing_2004_2021.csv"
    if sha(selected)!=outsha.get(str(selected.relative_to(S07))):
        raise RuntimeError("Stage07 selected candidate forcing changed")
    t=timeaxis(spec["primary"],("TA_F","TA_F_QC","VPD_F","VPD_F_QC"),
               "TIMESTAMP_START",2004,2021)
    e=timeaxis(spec["era"],("TA_ERA","VPD_ERA"),"TIMESTAMP_START",2004,2021)
    s=timeaxis(selected,("TA_USE","VPD_USE"),"time",2004,2021)
    if not(t.index.equals(e.index) and t.index.equals(s.index) and len(t)==315360):
        raise RuntimeError("Tower, standalone ERA and candidate exact source timeline changed")
    out=[]
    center_rows=[]
    for key,(tower_value,era_value) in TARGETS.items():
        cen=pd.Timestamp(key)
        if not(np.isclose(t.loc[cen,"TA_F"],tower_value,rtol=0,atol=1e-6) and
               np.isclose(e.loc[cen,"TA_ERA"],era_value,rtol=0,atol=1e-6) and
               t.loc[cen,"TA_F_QC"]==0 and
               np.isclose(s.loc[cen,"TA_USE"],tower_value,rtol=0,atol=1e-6)):
            raise RuntimeError("Current original source QC0 center differs from Stage13e "+key)
        prev=cen-pd.Timedelta(minutes=30)
        nxt=cen+pd.Timedelta(minutes=30)
        if prev not in t.index or nxt not in t.index:
            raise RuntimeError("Missing adjacent source native timestamp "+key)
        interpolation=float(.5*(t.loc[prev,"TA_F"]+t.loc[nxt,"TA_F"]))
        center_rows.append({
            "site":"US-MOz","center_native_time":key,
            "original_tower_TA_C":tower_value,
            "original_TA_QC":0,
            "paired_ERA5_TA_C":era_value,
            "tower_minus_ERA5_TA_C":tower_value-era_value,
            "preceding_tower_TA_C":float(t.loc[prev,"TA_F"]),
            "preceding_tower_TA_QC":float(t.loc[prev,"TA_F_QC"]),
            "following_tower_TA_C":float(t.loc[nxt,"TA_F"]),
            "following_tower_TA_QC":float(t.loc[nxt,"TA_F_QC"]),
            "tower_two_sided_interpolation_HYPOTHETICAL_C":interpolation,
            "interpolation_minus_ERA5_C":interpolation-era_value,
            "Stage07_center_TA_unchanged":True,
            "operator_approved":False,
            "status":"HOLD_OPERATOR_DECISION_AFTER_NATIVE_2H_CONTEXT",
        })
        for m in OFFSETS:
            at=cen+pd.Timedelta(minutes=m)
            a=t.loc[at];b=e.loc[at];c=s.loc[at]
            out.append({
                "site":"US-MOz","event_center":key,
                "relative_minutes":m,"native_source_time":at.isoformat(),
                "original_tower_TA_C":a.TA_F,"tower_TA_QC":a.TA_F_QC,
                "companion_ERA5_TA_C":b.TA_ERA,"Stage07_selected_TA_C":c.TA_USE,
                "tower_minus_ERA5_TA_C":a.TA_F-b.TA_ERA,
                "original_tower_VPD_hPa":a.VPD_F,"tower_VPD_QC":a.VPD_F_QC,
                "companion_ERA5_VPD_hPa":b.VPD_ERA,
                "Stage07_selected_VPD_hPa":c.VPD_USE,
                "operator_approved":False})
    return pd.DataFrame(out),pd.DataFrame(center_rows)

def main():
    pa=argparse.ArgumentParser()
    g=pa.add_mutually_exclusive_group(required=True)
    for x in ("self-test","check","run"):g.add_argument("--"+x,action="store_true")
    a=pa.parse_args()
    print("STAGE13F THREE US-MOz SOURCE QC0 TEMPERATURE EVENTS +/-2H | "+V,flush=True)
    selftest()
    if a.self_test:return
    context,center=audit()
    for z in center.to_dict("records"):
        print("\n=== 1 PENDING OPERATOR DECISION "+z["center_native_time"]+" ===",flush=True)
        print(context.loc[context.event_center.eq(z["center_native_time"]),
            ["relative_minutes","native_source_time","original_tower_TA_C",
             "tower_TA_QC","companion_ERA5_TA_C","Stage07_selected_TA_C",
             "original_tower_VPD_hPa","companion_ERA5_VPD_hPa"]].to_string(
                 index=False,float_format=lambda q:f"{q:.3f}"),flush=True)
        print("CENTER_NEIGHBORS",z["preceding_tower_TA_C"],
              z["following_tower_TA_C"],"HYPOTHETICAL_INTERPOLATION",
              z["tower_two_sided_interpolation_HYPOTHETICAL_C"],
              "UNMODIFIED QC0 SOURCE | OPERATOR PENDING",flush=True)
    print("\n=== ALL THREE SOURCE QC0 SCIENCE DECISIONS ===",flush=True)
    print(center.to_string(index=False,float_format=lambda q:f"{q:.3f}"),flush=True)
    if a.check:
        print("STAGE13F CHECK ONLY: NO WRITES",flush=True);return
    root=R/"reports"/("stage13f_MOz_three_extra_QC0_tower_ERA_neighbors_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    root.mkdir(parents=True,exist_ok=False)
    files={"THREE_MOz_QC0_2h_native_tower_and_ERA5_context.csv":context,
           "THREE_MOz_QC0_operator_decision_centers_NOT_APPROVED.csv":center}
    for name,df in files.items():df.to_csv(root/name,index=False)
    marker="NO_REPAIRS_APPROVED_OR_APPLIED_3_QC0_T_SPIKES"
    (root/marker).write_text(
        "Stage13e six prior Stage07 US-MOz changes are operator approved. "
        "These three extra original QC0 source temperature values have not "
        "been modified, no interpolation has been applied. The hypothetical "
        "two-neighbor estimate is diagnostic only. The 2005 Jan 6 05:00-09:00 "
        "multi-hour TA/VPD source discrepancy is a separate science HOLD. "
        "No raw source, Post-v5, surface, PFT, height, Slurm or model edits.\n")
    receipt={"version":V,"Stage13e_signed_source_SHA256":sha(S13E/
          "stage13e_moz_six_scope_and_09T_science_SHA_receipt.json"),
          "three_source_QC0_centers_operator_approved":False,
          "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
          "output_SHA256":{name:sha(root/name) for name in [*files,marker]}}
    (root/"stage13f_three_QC0_review_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13F OUTPUT REPORT ONLY",root,flush=True)
    print("ZERO ORIGINAL DATA, REANALYSIS, SELECTED CANDIDATE, SURFACE OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13F STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

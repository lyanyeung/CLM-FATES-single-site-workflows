#!/usr/bin/env python3
"""US-MOz Jan2005 first 27 unapproved QC1 source samples:
user-requested one-pass ISOLATED numerical sensitivity, NOT scientific repair.

The already applied operator-approved Stage13L 40HH is preserved. Use
preexisting SHA-signed Stage13K 67-source-event CDS ERA5-Land provenance
(2005-01-03..11) to construct only the first 27 original QC1 T/VPD pairs.
No new ERA download, no edits to previous trials, original source, CIME,
PFT, ZBOT or model jobs. No measured QC0 adjacent event validation:
NO SCIENTIFIC/POSTV5/DATM approval. Explicit hourly boundary warnings.
"""
import hashlib,json,sys,argparse
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import pandas as pd,numpy as np
sys.dont_write_bytecode=True
V="US-MOz-Jan2005-27QC1-reanalysis-numeric-sensitivity-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
G=R/"science_trials/stage13g_US_MOz_approved_native_T_VPD_20261026T180756Z_f75518a5"
L=R/"science_trials/stage13l_US_MOz_40HH_user_approved_CDSEra5Land_20261026T193902Z_95631db8"
K=R/"reports/stage13k_MOz_Jan2005_QC0_extended_and_CDS_comparison_20261026T192412Z_5fb1be73"
M=R/"external_evidence/era5land_timeseries/US-MOz/2005_stage13j/ERA5Land_US-MOz_Jan03_Jan11_2005_t2m_d2m_sp.receipt.json"
F="US-MOz_CLM_forcing_2004_2021_STG13L_40HH_REANALYSIS_SHADOW.csv"
REC="stage13l_MOz_40HH_science_SHA_receipt.json"
KREC="stage13k_original_QC0_ERA5Land_science_SHA_receipt.json"
KCSV="all_67_unapproved_CDS_vs_FLUXNET_source_event_comparison.csv"
START=pd.Timestamp("2005-01-05 20:00:00")
END=pd.Timestamp("2005-01-06 09:00:00")
START40=pd.Timestamp("2005-01-06 14:00:00")
END40=pd.Timestamp("2005-01-07 09:30:00")
COLS="time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE".split()
EDITCOL=("TA_USE","VPD_USE","TBOT","QBOT")
def need(c,msg):
    if not bool(c):raise RuntimeError("US-MOz 27HH NUMERIC SENSITIVITY STOP: "+str(msg))
def file(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"missing signed file "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as fh:
        for part in iter(lambda:fh.read(1<<20),b""):h.update(part)
    return h.hexdigest()
def ew(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(17.67*t/(t+243.5))
def eice(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(22.46*t/(t+272.62))
def qb(e,p):
    return 0.622*100*e/(p-0.378*100*e)
def selftest():
    need(len(pd.date_range(START,END,freq="30min"))==27 and
         len(pd.date_range(START40,END40,freq="30min"))==40 and
         ew(-10)>eice(-10) and
         pd.Series(["abc",None]).equals(pd.Series(["abc",None])),
         "27/40 source scope or saturation/typed exact comparison regression")
    print("US-MOz 27HH ISOLATED SCIENCE SELF-TEST PASS",flush=True)
def evidence():
    lrec=json.loads(file(L/REC).read_text())
    need(lrec.get("version")=="batch03-stage13l-v2-20261026-numpy-physical-gate-safe"
         and lrec.get("operator_approved_source_native_events_modified")==40
         and lrec.get("original_first27_and_Jan09_unchanged") is True
         and lrec.get("Postv5_approved") is False and
         lrec.get("DATM_ready") is False,"Stage13L verified actual 40 source/approval mismatch")
    need(sha(L/F)==lrec["output_SHA256"][F],"Stage13L selected forcing SHA changed")
    for k,checksum in lrec["output_SHA256"].items():
        need(sha(L/k)==checksum,"Stage13L protected output SHA changed "+k)
    s=json.loads(file(K/KREC).read_text())
    need(s.get("version")=="batch03-stage13k-v1-20261026-QC0-source-edge-ERA5Land-evidence",
         "signed Stage13K original report version drift")
    for k,checksum in s["output_sha256"].items():
        need(sha(K/k)==checksum,"Stage13K original evidence SHA differs "+k)
    need(sha(K/KREC)==lrec["original_Stage13k_report_receipt_SHA256"],
         "Stage13L ancestry to original Stage13K altered")
    need(lrec["original_Stage13G_source_SHA256"]==
         sha(G/"US-MOz_CLM_forcing_2004_2021_STG13G_RESEARCH_SHADOW.csv"),
         "Stage13G original candidate SHA differs")
    meta=json.loads(file(S07/"exact_input_manifest.json").read_text())
    info=next(x for x in meta["sites"] if x["site"]=="US-MOz")
    need(int(info["native_minutes"])==30 and
         int(info["first_year"])==2004 and int(info["last_year"])==2021,
         "release clock source identity changed")
    for kind in ("primary","era"):
        p=file(info[kind])
        need(sha(p)==meta["input_sha256"][str(p.resolve())],
             "original "+kind+" SHA changed")
    # External evidence is already downloaded and sealed, not a fresh CDS call.
    ed=json.loads(file(M).read_text())
    resp=file(ed["response_file"])
    need(sha(resp)==ed["response_sha256"] and
         sha(resp)==lrec["CDS_ERA5Land_original_binary_SHA256"],
         "pre-existing exact ERA5-Land scientific binary changed")
    return lrec,s,info
def calculate():
    lrec,kr,info=evidence()
    source=pd.read_csv(file(L/F),dtype={"time":str},low_memory=False)
    need(len(source)==315360 and list(source)==COLS,
         "full 18-year 315360 source schema changed")
    tm=pd.to_datetime(source.time,errors="raise")
    expected=pd.date_range("2004-01-01","2021-12-31 23:30",freq="30min")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    need(len(expected)==315360 and
         np.array_equal(tm.to_numpy(),expected.to_numpy()),"full NOLEAP native timeline mismatch")
    source.index=pd.DatetimeIndex(tm)
    frames=pd.read_csv(file(K/KCSV),dtype={"event_start":str,"original_native_time":str},
                       low_memory=False)
    rows=frames.loc[frames.event_start.eq("2005-01-05T20:00:00")].copy()
    rows["dt"]=pd.to_datetime(rows.original_native_time,errors="raise")
    ts=pd.date_range(START,END,freq="30min")
    rows=rows.sort_values("dt")
    need(len(rows)==27 and rows.dt.is_unique and
         np.array_equal(rows.dt.to_numpy(),ts.to_numpy()),
         "exact first 27 original signed source/HPC event identities changed")
    gt=rows.signed_distinct_CDS_ERA5Land_T_C.to_numpy(float)
    gv=rows.signed_CDS_ERA5Land_VPD_hPa.to_numpy(float)
    original=pd.read_csv(file(info["primary"]),
      usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
      dtype={"TIMESTAMP_START":str},low_memory=False)
    raw=original.loc[original.TIMESTAMP_START.isin(ts.strftime("%Y%m%d%H%M"))].copy()
    raw.index=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    raw=raw.loc[ts]
    need(len(raw)==27 and
         raw.TA_F_QC.eq(1).all() and raw.VPD_F_QC.eq(1).all(),
         "source original 27 slots not all QC1 temperature + humidity")
    original_selected=source.loc[ts].copy()
    need(np.allclose(original_selected.TA_USE.to_numpy(float),
                     raw.TA_F.to_numpy(float),atol=1e-8,rtol=0) and
         np.allclose(original_selected.VPD_USE.to_numpy(float),
                     raw.VPD_F.to_numpy(float),atol=1e-8,rtol=0),
         "original first27 expected still unchanged in user-approved Stage13L")
    ps=original_selected.PSRF.to_numpy(float)
    e=ew(gt)-gv
    q=qb(e,ps)
    with np.errstate(divide="ignore",invalid="ignore"):
        rhw=100*e/ew(gt);rhi=100*e/eice(gt)
    physics=(np.isfinite(gt)&np.isfinite(gv)&np.isfinite(ps)&
          (ps>50000)&(ps<110000)&(e>0)&(gv>=0)&(gv<ew(gt))&
          np.isfinite(q)&(q>0)&(q<0.08)&(rhw>0)&(rhw<=100))
    need(bool(physics.all()),"signed original CDS first27 physical VPD/QBOT candidate fails")
    trial=source.copy(deep=True)
    for f,values in (("TA_USE",gt),("VPD_USE",gv),
                     ("TBOT",gt+273.15),("QBOT",q)):
        trial.loc[ts,f]=values
    # Every native time and all fields outside exact 27 remain bitwise equal.
    rest=~source.index.isin(ts)
    for col in COLS:
        if col not in EDITCOL:
            need(source[col].equals(trial[col]),"non-humidity source/clock changed "+col)
        else:
            need(source.loc[rest,col].equals(trial.loc[rest,col]),
                 "off-scope source field changed "+col)
    saved40=pd.date_range(START40,END40,freq="30min")
    need(trial.loc[saved40,COLS].equals(source.loc[saved40,COLS]),
         "previous user-approved 40 Stage13L edits were not preserved exactly")
    values={c:pd.to_numeric(trial[c],errors="raise").to_numpy(float) for c in COLS[1:]}
    nt=values["TA_USE"];nv=values["VPD_USE"]
    ne=ew(nt)-nv;nq=qb(ne,values["PSRF"])
    complete=np.logical_and.reduce([np.isfinite(a) for a in values.values()])
    water=(complete&(nv>=0)&(ne>=0)&(nv<=ew(nt))&
          np.isclose(nq,values["QBOT"],atol=1e-8,rtol=1e-6))
    need(bool(complete.all() and water.all()),
         "new full 315360 water/QBOT physics or numeric completeness not closed")
    margins=[]
    for when,neighbor in ((START,START-pd.Timedelta(minutes=30)),
                          (END,END+pd.Timedelta(minutes=30))):
        a=trial.loc[when];b=trial.loc[neighbor]
        margins.append({"changed_time":str(when),"old_neighbor":str(neighbor),
          "T_change_C":float(a.TA_USE-b.TA_USE),
          "VPD_change_hPa":float(a.VPD_USE-b.VPD_USE),
          "T_boundary_over4C":bool(abs(a.TA_USE-b.TA_USE)>4),
          "VPD_boundary_over4hPa":bool(abs(a.VPD_USE-b.VPD_USE)>4),
          "true_adjacent_tower_QC0_available":False,
          "scientific_approval":False})
    boundary=pd.DataFrame(margins)
    changed=pd.DataFrame({
      "native_time":[str(x) for x in ts],
      "original_TA_QC":raw.TA_F_QC.to_numpy(int),
      "original_VPD_QC":raw.VPD_F_QC.to_numpy(int),
      "original_selected_T_C":original_selected.TA_USE.to_numpy(float),
      "new_grid_T_C":gt,
      "original_selected_VPD_hPa":original_selected.VPD_USE.to_numpy(float),
      "new_grid_VPD_hPa":gv,
      "original_selected_QBOT":original_selected.QBOT.to_numpy(float),
      "new_QBOT":q,"grid_RHwater_pct":rhw,"grid_RHice_pct":rhi,
      "postv5_approved":False,"independently_measured_tower_humidity":False})
    print("US-MOz EXACT 27 ORIGINAL QC1 SCIENTIFIC RESEARCH SCENARIO:")
    print(changed[["native_time","original_selected_T_C","new_grid_T_C",
        "original_selected_VPD_hPa","new_grid_VPD_hPa",
        "new_QBOT","grid_RHwater_pct"]].to_string(index=False),flush=True)
    print("US-MOz TWO 27HH EXTERNAL SOURCE BOUNDARIES (SCIENCE WARNINGS NOT ERA-TOWER VALIDATION):")
    print(boundary.to_string(index=False),flush=True)
    print("US-MOz ORIGINAL 40 APPROVED NATIVE ROWS PRESERVED, 27 NEW NUMERIC SCENARIO; 315360 water/QBOT PASS",flush=True)
    summ={"version":V,"site":"US-MOz","native_rows":315360,
       "original_missing":int(source[COLS[1:]].isna().any(axis=1).sum()),
       "new_missing":0,"new_unapproved_first_QC1_episode":27,
       "previous_40_operator_approved_source_records_preserved":True,
       "new_source_ERA5Land_reanalysis_not_independent_tower":True,
       "source_Stage13L_SHA":sha(L/F),
       "Stage13K_report_receipt_SHA":sha(K/KREC),
       "two_boundaries_T_over4":int(boundary.T_boundary_over4C.sum()),
       "two_boundaries_VPD_over4":int(boundary.VPD_boundary_over4hPa.sum()),
       "all_315360_water_QBOT_physics_pass":True,
       "scientific_repair_approved":False,
       "Jan09_original_QC1_unreviewed_and_preserved":True,
       "ZBOT_PFT_clock_DATM_not_approved":True,
       "Postv5_approved":False,"DATM_ready":False,"AD400":False,"Slurm":False}
    return trial.reset_index(drop=True),changed,boundary,summ
def main():
    ap=argparse.ArgumentParser()
    a=ap.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):a.add_argument("--"+mode,action="store_true")
    mode=ap.parse_args()
    selftest()
    if mode.self_test:return
    trial,changed,bounds,summary=calculate()
    if mode.check:
        print("US-MOz 27HH RESEARCH PREVIEW PASS, NO FILES WRITTEN",flush=True)
        return
    dest=R/"science_trials"/("US_MOz_Jan2005_first27_REANALYSIS_SENSITIVITY_"+
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    files={
      "US-MOz_315360_research_ONLY_27_and_previous40.csv":trial,
      "US-MOz_27_original_and_CDS_reanalysis_ledger.csv":changed,
      "US-MOz_27_first_episode_two_outer_edges.csv":bounds}
    sums={}
    for fname,df in files.items():
        df.to_csv(dest/fname,index=False,float_format="%.17g")
        sums[fname]=sha(dest/fname)
    back=pd.read_csv(file(dest/"US-MOz_315360_research_ONLY_27_and_previous40.csv"))
    need(len(back)==315360 and list(back)==COLS and
         not back[COLS[1:]].isna().any().any(),
         "new full 315360 candidate failed output serialization")
    (dest/"NOT_APPROVED_POSTV5_DATM_AD400").write_text(
      "27 first-Jan2005 QC1 event rows: external ERA5-Land numerical RESEARCH sensitivity only; original/40-approved saved. Absent ±6h source QC0 anchors, BIF UTC-6 preferred by original 29 QC0 analogue but not independently verified. Do not release to model without user final admission.\n")
    sums["NOT_APPROVED_POSTV5_DATM_AD400"]=sha(dest/"NOT_APPROVED_POSTV5_DATM_AD400")
    (dest/"US_MOz_27_science_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    sums["US_MOz_27_science_summary.json"]=sha(dest/"US_MOz_27_science_summary.json")
    (dest/"US_MOz_27_research_SHA_receipt.json").write_text(json.dumps(
      {"version":V,"source_Stage13L":summary["source_Stage13L_SHA"],
       "original_Stage13K_SHA":summary["Stage13K_report_receipt_SHA"],
       "output_SHA256":sums,"science_admission":False},indent=2)+"\n")
    print("US-MOz NEW ISOLATED 27HH RESEARCH SENSITIVITY:",dest,flush=True)
    print("US-MOz 27/27 EXPLORATORY SCENARIO COMPLETE | OLD 40 PRESERVED | ORIGINAL UNCHANGED | NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-MOz RESEARCH FAIL CLOSED:",e,file=sys.stderr,flush=True)
        raise

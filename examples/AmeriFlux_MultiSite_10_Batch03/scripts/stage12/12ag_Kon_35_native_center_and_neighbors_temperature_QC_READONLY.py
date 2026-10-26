#!/usr/bin/env python3
"""Batch03 Stage12ag read-only Kon temperature-QC and mixed-source VPD audit.

Consumes already SHA-sealed 75*5 Stage12ae native source context, prints all
34 Kon QC1/QC2 VPD held centers plus 2008-09-26 05:30 QC0 original VPD
anomaly. Show 5 original native HH original tower TA_F_QC, original tower T,
original companion ERA temperature, gridded ERA5-Land temperature, source
VPD_F_QC, source VPD and original Stage12g VPD; flag possible isolated
temperature spikes at the CENTER OR NEIGHBOR, never assume center is wrong.
No science edits, no model run, no DATM, no source rewriting.

--self-test math only.
--check rigorous source/receipt SHA, prints complete 35 cases, no writes.
--run same + one independent 35-row + all distinct native source rows
      report with receipt. STILL NO FORCING WRITES.
"""
import argparse, hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VERSION="batch03-stage12ag-v1-20261026-kon-34-event-neighbor-temp-QC"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AE=ROOT/"reports/stage12ae_all_42_pending_original_tower_ERA_ERA5Land_neighbors_20261026T011243Z_c5cc64fe"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
A=ROOT/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
CONTEXT="75_high_priority_cases_x_five_native_halfhours_all_three_source_comparisons.csv"
RECEIPT="stage12ae_review_only_SHA_receipt.json"
FRAMES=("TA_F","TA_F_QC","TA_ERA","ERA5Land_T2M_C",
        "VPD_F","VPD_F_QC","original_Stage12g_VPD_hPa",
        "paired_native_ERA_RH_pct","ERA5Land_water_RH_pct",
        "paired_native_ERA_RH_at_tower_T_VPD_hPa",
        "ERA5Land_RH_at_tower_T_VPD_hPa")

def safe(p):
    if p.is_symlink() or not p.is_file():raise ValueError("Missing or symlink SHA source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def esw(c):
    x=np.asarray(c,dtype=float)
    return 6.112*np.exp(17.67*x/(243.5+x))
def selftest():
    assert abs(np.mean([2.744,2.858])-2.801)<1e-12
    a=np.array([5.041,4.919,11.560,3.969,3.693])
    assert a[2]-np.mean([a[1],a[3]])>7
    assert esw(5.465)<15.688 and np.isfinite(esw(5.465))
    print("STAGE12AG SELF-TEST PASS: 35 Kon cases, ±2 HH, T/VPD QC source separation; NO WRITES",flush=True)

def source():
    a=json.loads(safe(AE/RECEIPT).read_text())
    if (a.get("pending_human_review")!=42 or
        a.get("Me6_previous_source_policy_approved_awaiting_application")!=33 or
        a.get("source_G_receipt_SHA256")!=sha(G/"stage12g_research_only_sha_receipt.json") or
        a.get("stage12ac_receipt_SHA256")!=sha(A/"stage12ac_user_approved_5HH_SHA_receipt.json") or
        a.get("Postv5_approved")!=0 or a.get("DATM_ready")!=0 or
        a.get("spinup_authorized")!=0 or
        sha(AE/CONTEXT)!=a["output_SHA256"][CONTEXT]):
        raise ValueError("Signed Stage12ae scientific original source report differs")
    tab=pd.read_csv(safe(AE/CONTEXT),
        dtype={"site":str,"center_native_key":str,"TIMESTAMP_START":str},
        low_memory=False)
    if len(tab)!=375 or tab.groupby(["site","center_native_key"]).ngroups!=75:
        raise ValueError("Original Stage12ae 75x5 native source context modified")
    if any(c not in tab.columns for c in FRAMES):
        raise ValueError("Original source reported QC and T/ERA fields missing")
    one=tab.loc[tab.site.eq("US-Kon")].copy()
    if (len(one)!=35*5 or one.groupby("center_native_key").ngroups!=35):
        raise ValueError("Exact 35 Kon event source cases not present")
    for c in FRAMES:
        one[c]=pd.to_numeric(one[c],errors="coerce")
    for k,part in one.groupby("center_native_key"):
        part=part.sort_values("relative_halfhours")
        if part.relative_halfhours.tolist()!=[-2,-1,0,1,2]:
            raise ValueError("Expected exact ±2 HH native neighbors "+k)
        t=pd.to_datetime(k,format="%Y%m%d%H%M")
        want=[(t+pd.Timedelta(minutes=30*d)).strftime("%Y%m%d%H%M")
              for d in (-2,-1,0,1,2)]
        if part.TIMESTAMP_START.tolist()!=want:
            raise ValueError("Original native 30min time source changed "+k)
    return one,a

def analyze():
    x,receipt=source()
    rows=[]
    for key,part in x.groupby("center_native_key",sort=True):
        p=part.set_index("relative_halfhours")
        c=p.loc[0]
        if not pd.notna(c.TA_F):
            raise ValueError("Kon center missing original TA_F; cannot review science "+key)
        center_vpd=float(c.VPD_F)
        source_invalid=center_vpd>=float(esw(c.TA_F))
        if key=="200809260530":
            if not(c.center_reason=="HOLD_ORIGINAL_QC_OR_SITE_T_P" and
                   int(c.VPD_F_QC)==0):
                raise ValueError("Protected original QC0 2008 Kon source changed")
            if not(np.isclose(float(p.loc[-1].VPD_F),2.744,atol=1e-6)
                and np.isclose(float(p.loc[1].VPD_F),2.858,atol=1e-6)
                and np.isclose(float(c.VPD_F),18.334,atol=1e-6)):
                raise ValueError("Anomalous original observed QC0 triad changed")
        else:
            if c.center_reason!="HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA":
                raise ValueError("Original Kon jump center source/hold changed "+key)
            if not source_invalid:
                raise ValueError("Expected original Kon gapfilled VPD exceeds original tower saturation "+key)
        T=p.TA_F.to_numpy(dtype=float)
        QC=p.TA_F_QC.to_numpy(dtype=float)
        tz=p.TA_ERA.to_numpy(dtype=float)
        tg=p.ERA5Land_T2M_C.to_numpy(dtype=float)
        discrepancies=np.abs(T-tz)
        grid_discrepancies=np.abs(T-tg)
        isolated=[]
        for j in (1,2,3):
            if (np.isfinite(T[j-1]) and np.isfinite(T[j]) and np.isfinite(T[j+1])
                and abs(T[j]-.5*(T[j-1]+T[j+1]))>=5.0
                and abs(T[j+1]-T[j-1])<=5.0):
                isolated.append(str(p.iloc[j].TIMESTAMP_START))
        rec={
          "site":"US-Kon","center_native_key":key,"center_reason":c.center_reason,
          "original_center_VPD_F_QC":int(c.VPD_F_QC),
          "original_center_VPD_F_hPa":center_vpd,
          "original_center_VPD_physically_invalid_at_T":source_invalid,
          "TA_F_previous_60_30_center_next30_60_C":"/".join(f"{v:.3f}" if np.isfinite(v) else "NA" for v in T),
          "TA_F_QC_previous_60_30_center_next30_60":"/".join(str(int(v)) if np.isfinite(v) else "NA" for v in QC),
          "TA_ERA_previous_60_30_center_next30_60_C":"/".join(f"{v:.3f}" if np.isfinite(v) else "NA" for v in tz),
          "grid_ERA5Land_T_previous_60_30_center_next30_60_C":"/".join(f"{v:.3f}" if np.isfinite(v) else "NA" for v in tg),
          "original_site_T_vs_pairERA_center_absdiff_C":abs(float(c.TA_F)-float(c.TA_ERA)),
          "original_site_T_vs_gridERA_center_absdiff_C":abs(float(c.TA_F)-float(c.ERA5Land_T2M_C)),
          "original_tower_T_qc0_neighbor_count":sum(v==0 for v in QC if np.isfinite(v)),
          "adjacent_30min_T_change_gt5_C":bool(abs(T[2]-T[1])>5 or abs(T[3]-T[2])>5),
          "isolated_T_spike_keys_in_center_pm30":";".join(isolated),
          "center_native_companion_RH_pct":float(c.paired_native_ERA_RH_pct),
          "center_gridERA5Land_RH_pct":float(c.ERA5Land_water_RH_pct),
          "center_companion_VPD_candidate_hPa":float(c.paired_native_ERA_RH_at_tower_T_VPD_hPa),
          "center_gridERA5Land_VPD_candidate_hPa":float(c.ERA5Land_RH_at_tower_T_VPD_hPa),
          "stage12g_VPD_previous_30_center_next30_hPa":
            "/".join(f"{float(p.loc[i].original_Stage12g_VPD_hPa):.3f}"
             if pd.notna(p.loc[i].original_Stage12g_VPD_hPa) else "HOLD"
             for i in (-1,0,1)),
          "temperature_edit_approved":False,
          "humidity_repair_approved":False
        }
        rows.append(rec)
    out=pd.DataFrame(rows)
    if len(out)!=35 or int(out.center_reason.eq("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA").sum())!=34:
        raise ValueError("Exact 34 Kon QC1/QC2 & QC0 decision review count differs")
    return out,x

def main():
    pa=argparse.ArgumentParser()
    arg=pa.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):arg.add_argument("--"+opt,action="store_true")
    mode=pa.parse_args()
    print("STAGE12AG ORIGINAL KON TEMPERATURE QC AND ERA PHYSICS | "+VERSION,flush=True)
    selftest()
    if mode.self_test:return
    summaries,context=analyze()
    cols=["center_native_key","center_reason",
          "TA_F_previous_60_30_center_next30_60_C",
          "TA_F_QC_previous_60_30_center_next30_60",
          "TA_ERA_previous_60_30_center_next30_60_C",
          "grid_ERA5Land_T_previous_60_30_center_next30_60_C",
          "isolated_T_spike_keys_in_center_pm30",
          "original_center_VPD_F_hPa","center_companion_VPD_candidate_hPa",
          "center_gridERA5Land_VPD_candidate_hPa",
          "stage12g_VPD_previous_30_center_next30_hPa"]
    print("\n===== ALL 35 KON ORIGINAL SOURCE TEMP/QC WITH +/-2 NATIVE HALF-HOURS =====",flush=True)
    print(summaries[cols].round(3).to_string(index=False),flush=True)
    print("\n===== DECISION AID — QC0 ANCHORS + POSSIBLE ISOLATED TEMPERATURE SPIKES =====",flush=True)
    print(summaries[["center_native_key","original_tower_T_qc0_neighbor_count",
       "adjacent_30min_T_change_gt5_C","isolated_T_spike_keys_in_center_pm30",
       "original_center_VPD_physically_invalid_at_T"]].to_string(index=False),flush=True)
    print("\nSTAGE12AG CONCLUSION: source original QC inspected; 34 Kon humidity centers + one original QC0 hold remain UNAPPROVED; do NOT blindly interpolate center or write forcing.",flush=True)
    if mode.check:
        print("STAGE12AG CHECK ONLY: ZERO REPORT OR MODEL WRITES.",flush=True)
        return
    out=ROOT/"reports"/("stage12ag_Kon_35_original_T_QC_native_pm2h_repair_decision_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
      "35_Kon_source_temperature_QC_and_ERA5Land_ERA_comparisons.csv":summaries,
      "175_Kon_center_pm2_native_halfhours_full_original_source_evidence.csv":context}
    for name,frame in outputs.items():frame.to_csv(out/name,index=False)
    (out/"SCIENTIFIC_HOLD_NO_EDITS.md").write_text(
      "Source-read-only scientific audit only. Do not modify original source TA_F "
      "or original source VPD QC0; do not apply temperature interpolations or "
      "choose humidity sources without operator approval and event anchor QC "
      "inspection. No Stage12g/Stage12af source writes; no DATM/Slurm/spinup.\n")
    dig={name:sha(out/name) for name in [*outputs,"SCIENTIFIC_HOLD_NO_EDITS.md"]}
    (out/"stage12ag_original_science_report_SHA_receipt.json").write_text(
      json.dumps({"version":VERSION,"Kon_34_jump_centers":34,
                  "Kon_1_protected_original_QC0":1,
                  "source_Stage12ae_SHA256":sha(AE/CONTEXT),
                  "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
                  "output_SHA256":dig},indent=2)+"\n")
    print("STAGE12AG KON TEMPERATURE-QC SCIENCE REPORT DIR:",out,flush=True)

if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("STAGE12AG STOP:",ex,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

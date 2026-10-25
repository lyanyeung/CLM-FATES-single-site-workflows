#!/usr/bin/env python3
"""Stage12n — original-source QC/companion T review of 86 NR1 and Me6 holds.

Science intent: DO NOT treat pressure-based relative site-grid height
as proof of a grid T correction. Stage12m found:
  US-NR1 2022: 19 >5C T discrepancies, 3 >4hPa VPD jump holds;
  US-Me6 2015,2017: 29 T discrepancies, 35 VPD jump holds.
Explore whether the originally published site TA_F and VPD_F have
QC0/1/2 support, and compare held original tower TA_USE (unchanged)
with exact-native published paired TA_ERA and verified Stage12m grid T.
For each jump source event, audit original QC and the two adjacent
native source and already sealed Stage12e/Stage12g VPD values.

--self-test checks synthetic source/T/QC typing, no writes.
--check reproduces signed Stage12m 86 science event identities, validates
  previous receipts and original source-native times, then prints.
--run writes ONLY new isolated SHA-receipted science tables.
No source, existing forcing, T/P, native timestamps, thresholds,
DATM, CIME, Slurm, Post-v5 or spinup modification or approval.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12n-v1-20261025-NR1-Me6-original-QC-companion-T"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
M=ROOT/"reports/stage12m_nonMtB_NRI_Me6_original_T_VPD_HOLD_diagnosis_20261025T084300Z_b0d38d29"
E=ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
M_SCRIPT=BASE/"scripts/stage12/12m_us_nr1_me6_T_and_VPD_hold_diagnosis_READONLY.py"
M_BLOB="b930c5e60a7a0726b937031725443b6d70ddc18f"
HOLD={"HOLD_SITE_GRID_T_DIFF_GT5C","HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"}
SITE_YEARS={"US-NR1":(2022,),"US-Me6":(2015,2017)}
M_FILES={"86_exact_science_held_event_source_and_neighbor_evidence.csv",
         "source_year_by_hold_reason_diagnostic.csv","SCIENCE_HOLD.md"}

def file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Immutable source is missing or symlinked: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as stream:
        for b in iter(lambda:stream.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def blob(p):
    b=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def num(v):
    a=pd.to_numeric(v,errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a))|(a<=-9990)]=np.nan
    return a

def qcategory(q):
    if not np.isfinite(q):return "MISSING"
    if q==0:return "QC0"
    if q==1:return "QC1"
    if q==2:return "QC2"
    return "OTHER_QC"

def selftest():
    assert len(SITE_YEARS)==2 and sum(len(x) for x in SITE_YEARS.values())==3
    assert qcategory(0.)=="QC0" and qcategory(2.)=="QC2"
    assert qcategory(np.nan)=="MISSING"
    assert num(pd.Series([0,-9999,"NaN",5])).tolist()[:1]==[0.]
    assert len(HOLD)==2 and len(M_FILES)==3
    print("STAGE12N SELF-TEST PASS: 86 exact historical science holds, original native TA/VPD and source QC; NO WRITES",flush=True)

def previous():
    for d in (M,E,G):
        if not d.is_dir() or d.is_symlink():
            raise ValueError("Expected prior original source report directory missing "+str(d))
    receipt=json.loads(file(M/"stage12m_science_hold_SHA_receipt.json").read_text())
    if (receipt.get("version")!="batch03-stage12m-v1-20261025-NR1-Me6-T-VPD-hold-no-writes"
        or receipt.get("nine_year_Stage12g_receipt_SHA256")!=sha(G/"stage12g_research_only_sha_receipt.json")
        or receipt.get("source_covered_for_sites")!=100
        or receipt.get("previous_stage12g_repairs_unchanged")!=14
        or receipt.get("original_science_holds_unchanged")!=86
        or receipt.get("original_tower_T_P_clock_unchanged") is not True
        or receipt.get("new_scientific_approval")!=0
        or receipt.get("Postv5_approved")!=0 or receipt.get("DATM_ready")!=0
        or receipt.get("spinup_authorized")!=0
        or set(receipt.get("output_SHA256",{}))!=M_FILES):
        raise ValueError("Stage12m original scientific source HOLD receipt differs")
    for name,digest in receipt["output_SHA256"].items():
        if sha(M/name)!=digest:
            raise ValueError("Stage12m report changed from signed source "+name)
    if blob(M_SCRIPT)!=M_BLOB:
        raise ValueError("Original Stage12m source Git blob changed")
    spec=importlib.util.spec_from_file_location("stage12m_pinned_source_for_stage12n",M_SCRIPT)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    mod,stage10,specs,catalog,held,repairs,g_receipt=m.evidence()
    details=pd.read_csv(file(M/"86_exact_science_held_event_source_and_neighbor_evidence.csv"),
                        dtype={"original_native_key":str},low_memory=False)
    if (len(details)!=86 or details.duplicated(["site","original_native_key"]).any()
        or set(details.site)!=set(SITE_YEARS) or not details.original_held_science_reason.isin(HOLD).all()):
        raise ValueError("Original exact 86 signed held source events changed")
    if (details.groupby(["site","original_held_science_reason"]).size().to_dict()
        !={("US-Me6","HOLD_SITE_GRID_T_DIFF_GT5C"):29,
           ("US-Me6","HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"):35,
           ("US-NR1","HOLD_SITE_GRID_T_DIFF_GT5C"):19,
           ("US-NR1","HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"):3}):
        raise ValueError("Original signed 48 temperature / 38 jump science partitions changed")
    return mod,specs,details

def load_source_year(path,year,need,optional):
    source=file(path)
    header=set(pd.read_csv(source,nrows=0).columns)
    if not set(need)<=header:
        raise ValueError("Original source required columns missing: "+str((source,set(need)-header)))
    cols=list(need)+[c for c in optional if c in header and c not in need]
    d=pd.read_csv(source,usecols=cols,dtype={"TIMESTAMP_START":str},low_memory=False)
    ts=pd.to_datetime(d.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    mask=ts.dt.year.eq(year)&~((ts.dt.month==2)&(ts.dt.day==29))
    d=d.loc[mask].reset_index(drop=True)
    if d.TIMESTAMP_START.duplicated().any():
        raise ValueError("Original source native timestamp duplicate "+str((source,year)))
    for c in optional:
        if c not in d.columns:d[c]=np.nan
    return d

def make():
    mod,specs,prior=previous()
    cases=[]; neighbors=[]; qc_year=[]
    for site,years in SITE_YEARS.items():
        print("STAGE12N SITE:",site,flush=True)
        original=pd.read_csv(file(E/(site+"_STAGE12E_INCOMPLETE_NOLEAP.csv")),low_memory=False)
        current=pd.read_csv(file(G/(site+"_STAGE12G_INCOMPLETE_NOLEAP.csv")),low_memory=False)
        if (len(original)!=len(current) or not original.time.equals(current.time)
            or not original.TA_USE.equals(current.TA_USE)
            or not original.PSRF.equals(current.PSRF)):
            raise ValueError("Original stage12e/g site T/P/native clock differs "+site)
        fullkeys=pd.to_datetime(current.time,format="%Y-%m-%d %H:%M:%S",
                 errors="raise").dt.strftime("%Y%m%d%H%M")
        if fullkeys.duplicated().any():raise ValueError("Stage12e has duplicate source-native clock "+site)
        idx_lookup=pd.Series(np.arange(len(fullkeys)),index=fullkeys.to_numpy())
        all_site_cases=prior.loc[prior.site.eq(site)]
        for year in years:
            print("STAGE12N SOURCE YEAR:",site,year,flush=True)
            raw=load_source_year(specs[site]["primary"],year,
                   ["TIMESTAMP_START","TA_F","VPD_F"],["TA_F_QC","VPD_F_QC"])
            paired=load_source_year(specs[site]["era"],year,
                   ["TIMESTAMP_START","TA_ERA"],["TA_ERA_QC"])
            if not raw.TIMESTAMP_START.equals(paired.TIMESTAMP_START):
                raise ValueError("Original FLUXMET vs paired TA_ERA timeline differs "+str((site,year)))
            originals=all_site_cases.loc[pd.to_datetime(
                    all_site_cases.original_native_key,
                    format="%Y%m%d%H%M",errors="raise").dt.year.eq(year)].copy()
            if len(originals)==0:
                raise ValueError("Expected original stage12m science events missing "+str((site,year)))
            tower=num(raw.TA_F);qc_t=num(raw.TA_F_QC)
            obs_vpd=num(raw.VPD_F);qc_v=num(raw.VPD_F_QC)
            comp=num(paired.TA_ERA)
            r_index=pd.Series(np.arange(len(raw)),index=raw.TIMESTAMP_START.to_numpy())
            year_original_qc0=np.isfinite(tower)&np.isfinite(comp)&(qc_t==0)
            qc_year.append({
               "site":site,"year":year,
               "original_native_year_samples":len(raw),
               "original_TA_F_QC0_with_paired_TA_ERA_N":int(year_original_qc0.sum()),
               "original_TA_F_QC0_vs_paired_TA_ERA_MAE_C":float(np.mean(
                    np.abs(tower[year_original_qc0]-comp[year_original_qc0])))
                    if year_original_qc0.any() else np.nan,
               "no_source_clock_changed":True})
            for event in originals.itertuples(index=False):
                key=str(event.original_native_key)
                if key not in r_index.index or key not in idx_lookup.index:
                    raise ValueError("Signed Stage12m event missing original source-native key "+key)
                ri=int(r_index.loc[key]);ci=int(idx_lookup.loc[key])
                original_t=float(current.TA_USE.iloc[ci])
                original_p=float(current.PSRF.iloc[ci])
                if not np.isclose(original_t,float(event.original_EC_T_C),atol=1e-6,rtol=0):
                    raise ValueError("Signed prior Stage12m original site tower T changed "+key)
                if not np.isclose(original_p,float(event.original_EC_surface_pressure_Pa),atol=1e-4,rtol=0):
                    raise ValueError("Signed prior Stage12m original site surface pressure changed "+key)
                if not np.isnan(original.VPD_USE.iloc[ci]) or not np.isnan(original.QBOT.iloc[ci]):
                    raise ValueError("Stage12n held event had original finite VPD/QBOT "+key)
                held_candidate=float(event.diagnostic_held_GRID_RH_candidate_VPD_hPa)
                if not np.isfinite(held_candidate):raise ValueError("Held candidate VPD not finite "+key)
                cases.append({
                   "site":site,"year":year,"native_key":key,
                   "original_hold_reason":event.original_held_science_reason,
                   "signed_stage12m_tower_T_C":original_t,
                   "original_FLUXMET_TA_F_C":float(tower[ri]),
                   "original_FLUXMET_TA_F_QC":float(qc_t[ri]),
                   "original_FLUXMET_TA_F_QC_class":qcategory(qc_t[ri]),
                   "native_paired_TA_ERA_C":float(comp[ri]),
                   "original_tower_minus_native_paired_TA_ERA_C":original_t-comp[ri],
                   "original_published_TA_F_minus_paired_TA_ERA_C":tower[ri]-comp[ri],
                   "signed_stage12m_ERA5Land_T_C":float(event.ERA5Land_gridded_T_C),
                   "grid_T_minus_native_paired_TA_ERA_C":float(event.ERA5Land_gridded_T_C)-comp[ri],
                   "tower_minus_grid_T_C":float(event.tower_minus_grid_T_C),
                   "original_FLUXMET_VPD_F_hPa":float(obs_vpd[ri]),
                   "original_FLUXMET_VPD_F_QC":float(qc_v[ri]),
                   "original_FLUXMET_VPD_F_QC_class":qcategory(qc_v[ri]),
                   "signed_diagnostic_rejected_candidate_VPD_hPa":held_candidate,
                   "new_humidity_repair":False,
                   "new_tower_temperature_change":False,
                   "model_ready":False})
                for neighbor in (ci-1,ci+1):
                    if not 0<=neighbor<len(fullkeys):continue
                    otherkey=str(fullkeys.iloc[neighbor])
                    if otherkey not in r_index.index:
                        # Neighbor is outside the one-year raw source subset;
                        # still preserve Stage12e/Stage12g site VPD.
                        other_ri=None
                    else:other_ri=int(r_index.loc[otherkey])
                    prev=float(original.VPD_USE.iloc[neighbor])
                    final=float(current.VPD_USE.iloc[neighbor])
                    prev=prev if np.isfinite(prev) else np.nan
                    final=final if np.isfinite(final) else np.nan
                    nqc=float(qc_v[other_ri]) if other_ri is not None else np.nan
                    nm=float(obs_vpd[other_ri]) if other_ri is not None else np.nan
                    neighbors.append({
                        "site":site,"year":year,"held_native_key":key,
                        "held_reason":event.original_held_science_reason,
                        "neighbor_native_key":otherkey,
                        "neighbor_side":"PREV" if neighbor<ci else "NEXT",
                        "original_FLUXMET_neighbor_VPD_F_hPa":nm,
                        "original_FLUXMET_neighbor_VPD_F_QC":nqc,
                        "original_FLUXMET_neighbor_VPD_F_QC_class":qcategory(nqc),
                        "original_Stage12e_neighbor_VPD_USE_hPa":prev,
                        "final_Stage12g_neighbor_VPD_USE_hPa":final,
                        "held_rejected_hypothetical_VPD_hPa":held_candidate,
                        "hypothetical_minus_final_neighbor_abs_hPa":
                            abs(held_candidate-final) if np.isfinite(final) else np.nan,
                        "final_neighbor_is_original_Stage12e_value":
                            bool(np.isfinite(final) and np.isfinite(prev)
                                 and abs(final-prev)<=1e-9),
                        "original_QC0_neighbor_agreement_not_an_approval":True
                    })
    case=pd.DataFrame(cases).sort_values(["site","year","native_key"])
    adj=pd.DataFrame(neighbors).sort_values(
                    ["site","year","held_native_key","neighbor_side"])
    if (len(case)!=86 or case.native_key.duplicated().any()
        or (case.original_hold_reason=="HOLD_SITE_GRID_T_DIFF_GT5C").sum()!=48
        or (case.original_hold_reason=="HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA").sum()!=38):
        raise ValueError("Stage12m original 86 science hold source provenance failed")
    qctab=(case.groupby(["site","year","original_hold_reason",
                         "original_FLUXMET_TA_F_QC_class"],dropna=False).agg(
          N=("native_key","size"),
          median_original_tower_minus_paired_ERA_C=(
             "original_tower_minus_native_paired_TA_ERA_C","median"),
          median_grid_minus_paired_ERA_C=("grid_T_minus_native_paired_TA_ERA_C","median"),
          median_tower_minus_grid_C=("tower_minus_grid_T_C","median"),
          median_abs_tower_minus_grid_C=("tower_minus_grid_T_C",
                                          lambda x:float(x.abs().median()))
    ).reset_index())
    jump=adj.loc[adj.held_reason.eq("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA")].copy()
    jumpsummary=jump.groupby(["site","neighbor_side","original_FLUXMET_neighbor_VPD_F_QC_class"],
                  dropna=False).agg(
        paired_neighbor_sides=("held_native_key","size"),
        candidate_vs_final_neighbor_over4hPa=(
          "hypothetical_minus_final_neighbor_abs_hPa",
          lambda x:int((x>4.).sum())),
        finite_final_neighbor=("final_Stage12g_neighbor_VPD_USE_hPa",
          lambda x:int(x.notna().sum())),
        neighbor_is_original_Stage12e_finite=(
          "final_neighbor_is_original_Stage12e_value","sum")
    ).reset_index()
    return case,adj,qctab,jumpsummary,pd.DataFrame(qc_year)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    choices=ap.add_mutually_exclusive_group(required=True)
    choices.add_argument("--self-test",action="store_true")
    choices.add_argument("--check",action="store_true")
    choices.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12N — SOURCE OBSERVATION QC0/QC1 AND NATIVE TA_ERA AUDIT | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    case,adj,groups,jump,year=make()
    print("\n========== ORIGINAL TOWER T QC AND PAIRED NATIVE TA_ERA, 86 HOLDS ==========",flush=True)
    print(groups.to_string(index=False),flush=True)
    print("\n========== FULL YEAR ORIGINAL TA_F QC0 VS PAIRED TA_ERA ==========",flush=True)
    print(year.to_string(index=False),flush=True)
    print("\n========== 38 VPD JUMP HOLDS: NEIGHBOR QC AND FINAL VPD COMPARISON ==========",flush=True)
    print(jump.to_string(index=False),flush=True)
    print("\nSTAGE12N SUMMARY: 86_original_temperature_and_VPD_science_holds_preserved=TRUE "
          "48_original_T_holds=TRUE 38_original_jump_holds=TRUE "
          "original_source_QC_checked=TRUE companion_TA_ERA_checked=TRUE "
          "new_repair_candidates=0 original_T_P_clock_unchanged=TRUE "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12N CHECK ONLY: NO REPORT, SOURCE, FORCING OR MODEL WRITES.",flush=True)
        return
    out=ROOT/"reports"/("stage12n_NR1_Me6_original_T_VPD_QC_and_companion_TA_ERA_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    tables={
      "86_held_original_source_T_and_VPD_QC.csv":case,
      "held_source_event_immediate_native_neighbors.csv":adj,
      "held_source_T_by_site_year_reason_and_QC.csv":groups,
      "38_original_jump_hold_neighbor_QC_summary.csv":jump,
      "three_year_original_TA_F_QC0_companion_TA_ERA_context.csv":year
    }
    for name,frame in tables.items():frame.to_csv(out/name,index=False)
    (out/"SCIENCE_HOLD.md").write_text(
      "READ-ONLY Stage12n original FLUXMET TA_F_QC/VPD_F_QC/TA_ERA companion "
      "source forensic diagnostic. The TA_ERA companion is not an independent "
      "tower measurement; attribution of source T discrepancy requires "
      "further evidence. The Stage12g VPD boundary test may have rejected "
      "both sides of adjacent proposed points; surviving final neighbors "
      "are not a reconstruction of original chronology. No QC0/source "
      "temperature edits, no new RH source repairs, no clock approval and "
      "no Post-v5/DATM/CIME/Slurm/spinup approval.\n")
    data={n:sha(out/n) for n in [*tables,"SCIENCE_HOLD.md"]}
    receipt={"version":VERSION,
       "source_stage12m_receipt_SHA256":sha(M/"stage12m_science_hold_SHA_receipt.json"),
       "original_86_science_holds_unmodified":True,
       "original_source_time_T_P_unmodified":True,
       "new_humidity_repairs":0,"Postv5_approved":0,
       "DATM_ready":0,"spinup_authorized":0,
       "output_SHA256":data}
    (out/"stage12n_original_source_QC_companion_T_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12N READ-ONLY REPORT DIR:",out,flush=True)
    print("NO ORIGINAL SOURCE OR PRIOR STAGE12E/G/M SCIENCE FILE MODIFICATION.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12N STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

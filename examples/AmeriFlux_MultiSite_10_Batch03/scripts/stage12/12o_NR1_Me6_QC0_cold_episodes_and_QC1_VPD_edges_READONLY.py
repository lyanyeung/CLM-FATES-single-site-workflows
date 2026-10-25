#!/usr/bin/env python3
"""Stage12o: measured temperature episode persistence & QC1 VPD edges.

Upstream Stage12n verified original tower TA_F_QC=0 for all 86 held
US-NR1/US-Me6 events, and 71/76 neighboring VPD source sides are QC1.
Neither QC0 means error-free tower temperature nor QC1 implies an
inaccurate, corrupted or independent humidity reference.

Preserve original 48 temperature mismatch holds and 38 VPD neighbor
jump holds. Compare source-native QC0 measured tower TA_F to paired
TA_ERA at the same unmodified native times for the full original site
year, identify persistent >=5C differences in half-hour sequences,
and quantify duration/context at each prior held event. Also examine
the ORIGINAL Stage12e accepted VPD boundary values against raw
FLUXMET VPD_F and its original QC0/QC1 flag; infer no approval from
numerically agreeing but possibly non-independent gapfilled VPD.

No new download, reanalysis sampling or original data writes.
--self-test: synthetic temporal interval/QA tests (no external IO)
--check: SHA-verify original Stage12n receipt, pinned script and
         original 86 science event ledger; compute metrics NO WRITES
--run: same + one new isolated SHA-receipted REPORT ONLY.
All original holds remain; no forcing, model or clock edits.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12o-v1-20261025-source-QC0-T-episode-QC1-VPD-edges"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
N=ROOT/"reports/stage12n_NR1_Me6_original_T_VPD_QC_and_companion_TA_ERA_20261025T085220Z_39e37c1b"
SCRIPT_N=BASE/"scripts/stage12/12n_NR1_Me6_original_T_VPD_QC_source_audit_READONLY.py"
BLOB_N="0683663998da33f223fefb8fa043603fb2818036"
SITES={"US-NR1":(2022,),"US-Me6":(2015,2017)}
FILES_N={
   "86_held_original_source_T_and_VPD_QC.csv",
   "held_source_event_immediate_native_neighbors.csv",
   "held_source_T_by_site_year_reason_and_QC.csv",
   "38_original_jump_hold_neighbor_QC_summary.csv",
   "three_year_original_TA_F_QC0_companion_TA_ERA_context.csv",
   "SCIENCE_HOLD.md"
}
T_HOLD="HOLD_SITE_GRID_T_DIFF_GT5C"
J_HOLD="HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"
WINDOW_HH=12

def file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Original signed source missing or symlinked: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def blob(p):
    b=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def num(series):
    a=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a))|(a<=-9990)]=np.nan
    return a
def episode_bounds(keys,flag,i):
    """Contiguous native 30-min run where central flag is true."""
    if not bool(flag[i]):return (i,i,0)
    a=b=i
    while a>0 and bool(flag[a-1]) and keys[a]-keys[a-1]==pd.Timedelta(minutes=30):
        a-=1
    while b+1<len(flag) and bool(flag[b+1]) and keys[b+1]-keys[b]==pd.Timedelta(minutes=30):
        b+=1
    return (a,b,b-a+1)
def selftest():
    ks=pd.DatetimeIndex(pd.date_range("2022-01-01",periods=7,freq="30min"))
    flag=np.array([False,True,True,True,False,True,False])
    assert episode_bounds(ks,flag,2)==(1,3,3)
    assert episode_bounds(ks,flag,0)==(0,0,0)
    assert episode_bounds(ks,flag,5)==(5,5,1)
    assert len(FILES_N)==6 and sum(len(ys) for ys in SITES.values())==3
    print("STAGE12O SELF-TEST PASS: temporal 30-minute QC0 temperature episode bounds and exact 86 source hold policy; NO WRITES",flush=True)

def previous():
    if not N.is_dir() or N.is_symlink():
        raise ValueError("Original Stage12n IRIDIS6 report absent")
    receipt=json.loads(file(N/"stage12n_original_source_QC_companion_T_SHA_receipt.json").read_text())
    if (receipt.get("version")!="batch03-stage12n-v1-20261025-NR1-Me6-original-QC-companion-T"
        or receipt.get("original_86_science_holds_unmodified") is not True
        or receipt.get("original_source_time_T_P_unmodified") is not True
        or receipt.get("new_humidity_repairs")!=0
        or receipt.get("Postv5_approved")!=0 or receipt.get("DATM_ready")!=0
        or receipt.get("spinup_authorized")!=0
        or set(receipt.get("output_SHA256",{}))!=FILES_N):
        raise ValueError("Stage12n recorded scientific source HOLD policy changed")
    for name,expected in receipt["output_SHA256"].items():
        if sha(N/name)!=expected:
            raise ValueError("Stage12n SHA-signed original source table differs "+name)
    if blob(SCRIPT_N)!=BLOB_N:
        raise ValueError("SHA-pinned Stage12n original script changed")
    spec=importlib.util.spec_from_file_location("stage12n_signed_for_12o",SCRIPT_N)
    n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
    # Covers all Stage12m + Stage12g upstream SHA checks and immutable
    # EC site/source native chronology, without calling any Stage12n writes.
    _,specs,prior=n.previous()
    cases=pd.read_csv(file(N/"86_held_original_source_T_and_VPD_QC.csv"),
                      dtype={"native_key":str},low_memory=False)
    adj=pd.read_csv(file(N/"held_source_event_immediate_native_neighbors.csv"),
                    dtype={"held_native_key":str,"neighbor_native_key":str},
                    low_memory=False)
    if (len(cases)!=86 or not (76<=len(adj)<=172) or
        cases.native_key.duplicated().any() or
        (cases.original_hold_reason.eq(T_HOLD).sum()!=48) or
        (cases.original_hold_reason.eq(J_HOLD).sum()!=38) or
        not cases.original_FLUXMET_TA_F_QC_class.eq("QC0").all()):
        raise ValueError("Stage12n verified exact 48+38 original QC0 science events changed")
    j=adj.loc[adj.held_reason.eq(J_HOLD)]
    if (len(j)!=76 or
        int(j.original_FLUXMET_neighbor_VPD_F_QC_class.eq("QC1").sum())!=71 or
        int(j.original_FLUXMET_neighbor_VPD_F_QC_class.eq("QC0").sum())!=5):
        raise ValueError("Original Stage12n QC1/QC0 held-neighbor 71/5 partition differed")
    return n,specs,cases,adj

def evaluate():
    n,specs,cases,adj=previous()
    trials=[];edge=[];baseline=[];runs=[]
    for site,years in SITES.items():
        for year in years:
            print("STAGE12O VERIFIED ORIGINAL SOURCE YEAR:",site,year,flush=True)
            raw=n.load_source_year(specs[site]["primary"],year,
                ["TIMESTAMP_START","TA_F","VPD_F"],
                ["TA_F_QC","VPD_F_QC"])
            paired=n.load_source_year(specs[site]["era"],year,
                ["TIMESTAMP_START","TA_ERA"],[])
            if not raw.TIMESTAMP_START.equals(paired.TIMESTAMP_START) or len(raw)!=17520:
                raise ValueError("Original exact noleap timestamp source chronology differs")
            dt=pd.DatetimeIndex(pd.to_datetime(raw.TIMESTAMP_START,
                    format="%Y%m%d%H%M",errors="raise"))
            if dt.has_duplicates:
                raise ValueError("Duplicate originally published native half hour")
            if not (np.diff(dt.values).astype("timedelta64[m]").astype(int)==30).all():
                # Noleap Feb28 -> Mar1 is 24h+30m in leap source years;
                # neither selected US-Me6 2015/2017 nor NR1 2022 is leap.
                raise ValueError("Original three non-leap source years not strictly 30 minute")
            ta=num(raw.TA_F);taera=num(paired.TA_ERA)
            qct=num(raw.TA_F_QC);vpd=num(raw.VPD_F)
            qcv=num(raw.VPD_F_QC)
            valid=(np.isfinite(ta)&np.isfinite(taera)&(qct==0))
            delta=ta-taera
            cutoff=valid&(delta<=-5.)
            baseline.append({
                "site":site,"year":year,
                "original_native_halfhours":len(ta),
                "source_QC0_TA_vs_TA_ERA_valid_N":int(valid.sum()),
                "source_QC0_TA_minus_companion_ERA_le_minus5_N":int(cutoff.sum()),
                "QC0_tower_minus_native_TA_ERA_mean_C":float(np.mean(delta[valid])),
                "QC0_tower_minus_native_TA_ERA_MAE_C":float(np.mean(np.abs(delta[valid]))),
                "original_tower_temperature_unchanged":True,
                "native_clock_unmodified":True
            })
            pos=pd.Series(np.arange(len(raw)),index=raw.TIMESTAMP_START.to_numpy())
            held=cases.loc[cases.site.eq(site)&cases.year.eq(year)]
            for heldrow in held.itertuples(index=False):
                key=str(heldrow.native_key)
                if key not in pos.index:
                    raise ValueError("Original QC0 held native source key vanished "+key)
                i=int(pos.loc[key])
                if qct[i]!=0 or not np.isfinite(ta[i]) or not np.isfinite(taera[i]):
                    raise ValueError("Held tower temperature was not source QC0 with native TA_ERA "+key)
                if not np.isclose(ta[i],float(heldrow.original_FLUXMET_TA_F_C),
                                  rtol=0,atol=1e-8):
                    raise ValueError("Source original measured tower T differs from Stage12n signed report "+key)
                if not np.isclose(taera[i],float(heldrow.native_paired_TA_ERA_C),
                                  rtol=0,atol=1e-8):
                    raise ValueError("Paired original TA_ERA differs from Stage12n signed source "+key)
                a,b,length=episode_bounds(dt,cutoff,i)
                lo=max(0,i-WINDOW_HH);hi=min(len(raw),i+WINDOW_HH+1)
                window_valid=valid[lo:hi]
                window_d=delta[lo:hi]
                n6=int(window_valid.sum())
                n6cold=int((cutoff[lo:hi]).sum())
                stepdelta=np.abs(np.diff(ta[max(0,i-1):min(len(raw),i+2)]))
                prev_jump=(abs(ta[i]-ta[i-1]) if i>0 and qct[i-1]==0 else np.nan)
                next_jump=(abs(ta[i+1]-ta[i]) if i+1<len(ta) and qct[i+1]==0 else np.nan)
                trials.append({
                   "site":site,"year":year,"native_key":key,
                   "prior_source_hold_reason":heldrow.original_hold_reason,
                   "original_tower_T_QC":"QC0",
                   "original_tower_T_C":float(ta[i]),
                   "paired_original_TA_ERA_C":float(taera[i]),
                   "signed_ERA5Land_grid_T_C":float(heldrow.signed_stage12m_ERA5Land_T_C),
                   "tower_minus_native_TA_ERA_C":float(delta[i]),
                   "tower_minus_ERA5Land_T_C":float(heldrow.tower_minus_grid_T_C),
                   "QC0_tower_minus_TA_ERA_le_minus5":bool(cutoff[i]),
                   "consecutive_QC0_tower_minus_paired_TA_ERA_le_minus5_halfhours":
                       length,
                   "contiguous_TA_ERA_mismatch_run_start":dt[a].strftime("%Y%m%d%H%M") if length else "",
                   "contiguous_TA_ERA_mismatch_run_end":dt[b].strftime("%Y%m%d%H%M") if length else "",
                   "QC0_native_TA_ERA_valid_in_pm6h_window":n6,
                   "QC0_tower_minus_paired_ERA_le_minus5_in_pm6h_window":n6cold,
                   "median_TA_F_minus_paired_ERA_C_in_pm6h_window":(
                       float(np.median(window_d[window_valid])) if n6 else np.nan),
                   "original_QC0_T_jump_from_PREV_C":float(prev_jump),
                   "original_QC0_T_jump_to_NEXT_C":float(next_jump),
                   "temperature_changed":False,
                   "hold_released":False
                })
            # No VPD corrections: just match each of the 76 signed
            # PREV/NEXT source neighbors against its original native source.
            neighbors=adj.loc[adj.site.eq(site)&adj.year.eq(year)&adj.held_reason.eq(J_HOLD)]
            for e in neighbors.itertuples(index=False):
                k=str(e.neighbor_native_key)
                if k not in pos.index:
                    raise ValueError("Original jump neighbor absent in same year source "+k)
                z=int(pos.loc[k])
                if n.qcategory(qcv[z])!=str(e.original_FLUXMET_neighbor_VPD_F_QC_class):
                    raise ValueError("Original 71/5 source QC shifted "+k)
                era_f=float(e.original_Stage12e_neighbor_VPD_USE_hPa)
                orig=float(vpd[z])
                edge.append({
                  "site":site,"year":year,
                  "held_native_key":str(e.held_native_key),
                  "neighbor_native_key":k,
                  "neighbor_side":str(e.neighbor_side),
                  "original_FLUXMET_VPD_F_QC":n.qcategory(qcv[z]),
                  "original_FLUXMET_VPD_F_hPa":orig,
                  "original_stage12e_repaired_neighbor_VPD_USE_hPa":era_f,
                  "final_stage12g_neighbor_VPD_USE_hPa":
                     float(e.final_Stage12g_neighbor_VPD_USE_hPa),
                  "original_FLUXMET_VPD_F_matches_prior_shadow_finite":
                     bool(np.isfinite(orig)&np.isfinite(era_f)
                          and abs(orig-era_f)<=1e-7),
                  "native_source_neighbor_valid_final_finite":
                     bool(np.isfinite(float(e.final_Stage12g_neighbor_VPD_USE_hPa))),
                  "original_QC0_source_reference":
                     bool(qcv[z]==0),
                  "new_ERA5Land_candidate_source_VPD_approved":False
                })
    out=pd.DataFrame(trials).sort_values(["site","year","native_key"])
    edges=pd.DataFrame(edge).sort_values(["site","year","held_native_key","neighbor_side"])
    if (len(out)!=86 or len(edges)!=76 or
        out.prior_source_hold_reason.eq(T_HOLD).sum()!=48 or
        out.prior_source_hold_reason.eq(J_HOLD).sum()!=38 or
        edges.original_FLUXMET_VPD_F_QC.eq("QC1").sum()!=71 or
        edges.original_FLUXMET_VPD_F_QC.eq("QC0").sum()!=5):
        raise ValueError("Stage12o exact previous 86 science holds and 76 source-side QC origins changed")
    aggregate=out.groupby(["site","year","prior_source_hold_reason"],as_index=False).agg(
       original_held_N=("native_key","size"),
       original_QC0_tower_minus_companion_ERA_le_minus5_N=(
         "QC0_tower_minus_TA_ERA_le_minus5","sum"),
       persistence_ge4_native_halfhours_N=(
         "consecutive_QC0_tower_minus_paired_TA_ERA_le_minus5_halfhours",
         lambda x:int((x>=4).sum())),
       persistence_ge12_native_halfhours_N=(
         "consecutive_QC0_tower_minus_paired_TA_ERA_le_minus5_halfhours",
         lambda x:int((x>=12).sum())),
       median_consecutive_QC0_ERA_mismatch_halfhours=(
         "consecutive_QC0_tower_minus_paired_TA_ERA_le_minus5_halfhours","median"),
       median_native_QC0_T_jump_prev_C=("original_QC0_T_jump_from_PREV_C","median"),
       median_native_QC0_T_jump_next_C=("original_QC0_T_jump_to_NEXT_C","median"))
    aggregate["hold_remains"]=True
    eaggregate=edges.groupby(
         ["site","original_FLUXMET_VPD_F_QC"],as_index=False).agg(
        adjacent_sides=("held_native_key","size"),
        original_FLUXMET_VPD_matches_original_stage12e_N=(
           "original_FLUXMET_VPD_F_matches_prior_shadow_finite","sum"),
        original_stage12g_neighbor_finite_N=(
           "native_source_neighbor_valid_final_finite","sum"),
        QC0_reference_sides=("original_QC0_source_reference","sum"))
    return out,edges,aggregate,eaggregate,pd.DataFrame(baseline)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE12O — NR1/ME6 ORIGINAL T QC0 EPISODES + VPD QC1 EDGE PROVENANCE | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    cases,neighbors,group,edges,baseline=evaluate()
    print("\n========== SOURCE QC0 TA_F VS NATIVE PAIRED TA_ERA: YEAR CONTEXT ==========",flush=True)
    print(baseline.to_string(index=False),flush=True)
    print("\n========== ORIGINAL 86 HELD T/JUMP EVENT PERSISTENCE ==========",flush=True)
    print(group.to_string(index=False),flush=True)
    print("\n========== 76 VPD JUMP NEIGHBOR SOURCE QC AND PRIOR SHADOW COMPARISON ==========",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("\nSTAGE12O SUMMARY: original_86_holds_preserved=TRUE "
        "48_T_HOLD_and_38_VPD_jump_HOLD=TRUE 71_QC1_neighbor_sides=TRUE "
        "5_QC0_neighbor_sides=TRUE new_RH_QBOT_repairs=0 "
        "original_source_T_P_clock_modified=FALSE "
        "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12O CHECK ONLY: NO NEW SOURCE, REPORT OR MODEL WRITES.",flush=True)
        return
    dest=ROOT/"reports"/("stage12o_original_QC0_T_episodes_and_QC1_VPD_edges_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    files={
        "86_original_QC0_T_persistence_events.csv":cases,
        "76_original_VPD_neighbor_QC_provenance.csv":neighbors,
        "six_site_year_hold_reason_episode_summary.csv":group,
        "original_VPD_neighbor_QC1_vs_stage12e_source_summary.csv":edges,
        "three_year_QC0_tower_native_TA_ERA_year_context.csv":baseline
    }
    for name,table in files.items():table.to_csv(dest/name,index=False)
    note=("The original EC tower TA_F_QC0 may be correct local weather; "
          "difference against native paired TA_ERA is NOT sufficient to "
          "declare instrument failure or permit replacing measured tower T. "
          "Original neighboring VPD_F_QC1 may represent gap-filled source "
          "instead of independent measurements; coincidence with Stage12e "
          "VPD does NOT prove native instrument evidence. The VPD jump "
          "science guard remains >4hPa, T-grid guard >5C, 86 holds "
          "unchanged. Zero source/forcing, clock or model modifications. "
          "Do not use report-only diagnostic for DATM, Post-v5, CIME or "
          "spinup.\n")
    (dest/"SCIENCE_HOLD.md").write_text(note)
    output_hashes={name:sha(dest/name) for name in [*files,"SCIENCE_HOLD.md"]}
    r={"version":VERSION,
       "original_Stage12n_SHA256":sha(N/"stage12n_original_source_QC_companion_T_SHA_receipt.json"),
       "original_86_holds_unchanged":True,
       "original_71_QC1_and_5_QC0_neighbour_sides":True,
       "new_humidity_repair_candidates":0,
       "original_tower_T_P_clock_unchanged":True,
       "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
       "output_SHA256":output_hashes}
    (dest/"stage12o_science_only_SHA_receipt.json").write_text(json.dumps(r,indent=2)+"\n")
    print("STAGE12O READ-ONLY SOURCE QC0 TEMP EPISODE / QC1 VPD EDGE DIR:",dest,flush=True)
    print("NO ORIGINAL QC0 OBSERVATION, FORCING, SOURCE CLOCK, STAGE12M/N OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12O STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

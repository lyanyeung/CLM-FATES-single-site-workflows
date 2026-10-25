#!/usr/bin/env python3
"""Stage12ab — exactly seven original-native US-Me6 2017-07-04 HH.
SHA-sealed Stage12aa/Stage12z evidence only. Decompose every original
companion ERA-RH-at-tower-T VPD half-hour change symmetrically into
measured tower T response and source companion RH response:
    VPD = es_water(T) * (1 - RH/100).
The symmetric exact decomposition is descriptive mathematics, never
evidence of instrument truth or causal meteorology.

--self-test: pure synthetic math, zero filesystem reads/writes
--check: immutable report provenance and exact 7/6 original HH audit,
         NO files written
--run: same checks + only a NEW separate SHA-sealed SCIENCE report

Original Stage12g VPD values, original source/clock and the 86+233
protected science holds are never modified, no production approval.
"""
import argparse, hashlib, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

VERSION="batch03-stage12ab-v1-20261025-ERA-RH-native-VPD-symmetric-physics-attribution"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AA=ROOT/"reports/stage12aa_20170704_original_QC1_QC2_native_ERA_RH_20261025T230548Z_3a2b96b6"
Z=ROOT/"reports/stage12z_0800_MDS_source_original_RH_context_20261025T225231Z_2b60b8d8"
AA_REC="stage12aa_readonly_SHA_receipt.json"
Z_REC="stage12z_source_SHA_receipt.json"
AA_SEVEN="seven_original_native_QC1_QC2_RH_and_three_scenarios.csv"
AA_EDGES="six_original_native_30min_stage12aa_source_edges.csv"
KEYS=["201707040600","201707040630","201707040700",
      "201707040730","201707040800","201707040830","201707040900"]

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlinked signed historical science source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def es(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def symmetric(t0,t1,rh0,rh1):
    f0,f1=1-rh0/100.,1-rh1/100.
    s0,s1=es(t0),es(t1)
    dt=(s1-s0)*(f0+f1)/2
    dr=(f1-f0)*(s0+s1)/2
    actual=s1*f1-s0*f0
    return float(dt),float(dr),float(actual)

def selftest():
    assert abs(float(es(18.96))-21.9052737697)<1e-6
    dt,dr,total=symmetric(15.01,17.33,69.76920611738733,52.733718243769005)
    assert abs(dt-1.05426420618)<1e-7
    assert abs(dr-3.13655054618)<1e-7
    assert abs((dt+dr)-total)<1e-12
    assert total>4 and abs(total-4.19081475)<1e-7
    timestamps=pd.to_datetime(KEYS,format="%Y%m%d%H%M")
    assert (np.diff(timestamps.to_numpy()).astype("timedelta64[m]").astype(int)==30).all()
    print("STAGE12AB SELF-TEST PASS: exact symmetric VPD T/RH decomposition and 7 original native half-hours; NO WRITES",flush=True)

def verify():
    a=json.loads(safe(AA/AA_REC).read_text())
    z=json.loads(safe(Z/Z_REC).read_text())
    if (a.get("version")!="batch03-stage12aa-v1-20261025-QC1-QC2-original-native-30min-ERA-RH"
        or a.get("original_86_plus_233_science_holds_preserved") is not True
        or a.get("new_repairs")!=0
        or a.get("Postv5_approved")!=0
        or a.get("DATM_ready")!=0
        or a.get("spinup_authorized")!=0
        or a.get("original_stage12z_SHA256")!=sha(Z/Z_REC)):
        raise ValueError("Original Stage12aa source/hold chain changed")
    if (z.get("version")!="batch03-stage12z-v1-20261025-original-Me6-0800-MDS-QC1-water-RH"
        or z.get("original_86_plus_233_holds_preserved") is not True
        or z.get("source_0800_QC1_MDS") is not True
        or z.get("new_repairs")!=0):
        raise ValueError("Original Stage12z SHA science receipt altered")
    for base,receipt in ((AA,a),(Z,z)):
        for name,digest in receipt["output_SHA256"].items():
            if sha(base/name)!=digest:
                raise ValueError("Immutable earlier report SHA changed "+name)

def audit():
    verify()
    tab=pd.read_csv(safe(AA/AA_SEVEN),dtype={"TIMESTAMP_START":str},low_memory=False)
    ed=pd.read_csv(safe(AA/AA_EDGES),
                   dtype={"native_start":str,"native_end":str},low_memory=False)
    if (len(tab)!=7 or len(ed)!=6
        or tab.TIMESTAMP_START.tolist()!=KEYS
        or tab.TIMESTAMP_START.duplicated().any()
        or not tab.TA_F_QC.eq(0).all()
        or tab.VPD_F_QC.tolist()!=[1,1,1,1,1,2,2]
        or not tab.VPD_USE.iloc[2:4].isna().all()):
        raise ValueError("Seven original signed source and Stage12g protected rows differ")
    required=["TA_F","native_companion_ERA_RH_pct","scenario_C_all_companion_RH_referenced_VPD_hPa",
              "native_companion_T_minus_original_T_C"]
    if not set(required)<=set(tab.columns):
        raise ValueError("Stage12aa signed original companion-RH schema changed")
    T=tab.TA_F.to_numpy(dtype=float)
    RH=tab.native_companion_ERA_RH_pct.to_numpy(dtype=float)
    CV=tab.scenario_C_all_companion_RH_referenced_VPD_hPa.to_numpy(dtype=float)
    if (not np.isfinite(T).all() or not np.isfinite(RH).all() or
        not np.isfinite(CV).all() or not ((RH>0)&(RH<=100)).all() or
        not np.allclose(CV,es(T)*(1-RH/100.),atol=1e-7,rtol=0) or
        not tab.native_companion_T_minus_original_T_C.abs().le(5).all()):
        raise ValueError("Original companion-RH physics or paired ERA/tower T guard changed")
    records=[]
    for i in range(6):
        start,end=KEYS[i:i+2]
        original=ed.iloc[i]
        if original.native_start!=start or original.native_end!=end:
            raise ValueError("Original signed six source-native boundary clocks changed")
        dt,dr,total=symmetric(T[i],T[i+1],RH[i],RH[i+1])
        dv=CV[i+1]-CV[i]
        signed=float(original.C_all_companion_RH_referenced_absolute_30min_jump_hPa)
        if abs(total-dv)>1e-7 or abs(abs(dv)-signed)>1e-7:
            raise ValueError("Original source candidate mathematical contribution changed")
        records.append({
            "native_start":start, "native_end":end,"exact_30min_step":True,
            "source_QC_transition":str(original.source_QC_transition),
            "original_QC0_T_start_C":T[i],"original_QC0_T_end_C":T[i+1],
            "original_tower_T_change_C":T[i+1]-T[i],
            "companion_ERA_RH_start_pct":RH[i],"companion_ERA_RH_end_pct":RH[i+1],
            "source_companion_RH_change_percentage_points":RH[i+1]-RH[i],
            "companion_RH_based_tower_VPD_change_hPa":dv,
            "T_component_hPa_symmetric_exact":dt,
            "RH_component_hPa_symmetric_exact":dr,
            "RH_component_share_of_signed_change_pct":100*dr/dv if abs(dv)>1e-10 else np.nan,
            "companion_RH_based_VPD_abs_jump_hPa":abs(dv),
            "above_original_4hPa_source_guard":abs(dv)>4,
            "excess_above_4hPa_hPa":max(0,abs(dv)-4),
            "original_VPD_source_QC1_to_QC2_switch":str(original.source_QC_transition)=="1->2",
            "original_Stage12g_values_altered":False,
            "source_native_clock_changed":False,
            "science_HOLD_released":False
        })
    detail=pd.DataFrame(records)
    selected=detail.loc[detail.native_start.eq("201707040700")&
                        detail.native_end.eq("201707040730")]
    if (len(selected)!=1 or
        int(detail.above_original_4hPa_source_guard.sum())!=1 or
        not np.isclose(selected.iloc[0].excess_above_4hPa_hPa,0.190815,atol=1e-5)):
        raise ValueError("Exactly one original-source paired ERA-RH >4hPa boundary changed")
    summary=pd.DataFrame([{
        "original_source_seven_halfhours":7,
        "original_adjacent_30min_edges":6,
        "companion_ERA_RH_candidate_edges_exceeding_original_4hPa_guard":
             int(detail.above_original_4hPa_source_guard.sum()),
        "companion_ERA_RH_candidate_edges_not_exceeding_guard":
             int((~detail.above_original_4hPa_source_guard).sum()),
        "original_one_residual_source_boundary":
             "201707040700->201707040730",
        "ERA_RH_fall_pct_points":float(-selected.iloc[0].source_companion_RH_change_percentage_points),
        "QC0_T_increase_C":float(selected.iloc[0].original_tower_T_change_C),
        "sym_T_term_hPa":float(selected.iloc[0].T_component_hPa_symmetric_exact),
        "sym_RH_term_hPa":float(selected.iloc[0].RH_component_hPa_symmetric_exact),
        "remaining_above_guard_hPa":float(selected.iloc[0].excess_above_4hPa_hPa),
        "original_86_plus_233_science_holds_unchanged":True,
        "no_repair_or_model_input_authorization":True
    }])
    return detail,summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):
        group.add_argument("--"+name,action="store_true")
    args=p.parse_args()
    print("STAGE12AB — SOURCE ERA-RH CHANGE VPD T/RH EXACT DECOMPOSITION | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    edges,summary=audit()
    print("\n========== SIX SIGNED ORIGINAL-NATIVE ERA-RH VPD CHANGES, TEMP / RH COMPONENTS ==========",flush=True)
    print(edges[["native_start","native_end","source_QC_transition",
       "original_tower_T_change_C","source_companion_RH_change_percentage_points",
       "T_component_hPa_symmetric_exact","RH_component_hPa_symmetric_exact",
       "companion_RH_based_tower_VPD_change_hPa",
       "above_original_4hPa_source_guard"]].to_string(index=False),flush=True)
    print("\n========== ONE EXACTLY-EXCEEDING 07:00→07:30 ORIGINAL SOURCE BOUNDARY ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\nSTAGE12AB SUMMARY: original_seven_native_source_rows=TRUE "
       "six_exact_30min_edges=TRUE one_RH_candidate_jump_GT4hPa=TRUE "
       "original_86_plus_233_science_holds_preserved=TRUE "
       "new_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12AB CHECK ONLY: ZERO SOURCE, REPORT, FORCING OR MODEL WRITES.",flush=True)
        return
    folder=ROOT/"reports"/(
        "stage12ab_Me6_20170704_native_ERA_RH_VPD_T_RH_decomposition_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    tables={
        "original_six_30min_ERA_RH_VPD_temperature_humidity_decomposition.csv":edges,
        "one_07h00_to_07h30_residual_source_jump_attribution.csv":summary
    }
    for name,table in tables.items():
        table.to_csv(folder/name,index=False)
    (folder/"SCIENCE_HOLD.md").write_text(
        "Original signed Stage12aa seven native half-hour science sources and "
        "source QC are unchanged. Symmetric temperature/humidity arithmetic "
        "does not validate actual observed humidity nor justify a source "
        "clock shift, relaxation of 4hPa guard, gapfill insertion, "
        "replacement of existing 08:00 Stage12g, or release of 86+233 "
        "science holds, Post-v5/DATM/spinup.\n")
    outputs={name:sha(folder/name) for name in [*tables,"SCIENCE_HOLD.md"]}
    receipt={
        "version":VERSION,
        "original_stage12aa_SHA256":sha(AA/AA_REC),
        "original_7_native_records_and_6_edges_preserved":True,
        "original_86_plus_233_science_holds_preserved":True,
        "original_source_and_Stage12g_unchanged":True,
        "new_repairs":0,"Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "output_SHA256":outputs
    }
    (folder/"stage12ab_symmetric_source_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12AB SOURCE-ONLY SCIENCE REPORT DIR:",folder,flush=True)

if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("STAGE12AB STOP:",ex,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

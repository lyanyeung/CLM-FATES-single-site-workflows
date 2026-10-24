#!/usr/bin/env python3
"""Stage11o: READ-ONLY shifted VPD-jump boundary science around Stage11n.

Stage11n shows seven hypothetical ERA-RH replacements would reduce the
four original VPD jumps, but would move two discontinuities to neighbour
intervals. This script evaluates two ADDITIONAL UNAPPROVED 'sentinel'
timestamps (US-NC2 2025-03-18 17:30 and 2025-03-25 11:00), together
with exactly the prior seven, never modifying tower/site forcing TA_USE.

The source is the SHA-sealed Stage11m native source/ERA context; prior
seven values come from SHA-pinned Stage11n code. No arbitrary smoothing,
no unreviewed writes, no independent ERA5-Land clock/source approval.

--self-test pure algebra and exact native IDs, no IRIDIS input or writes
--check     source SHA and full dataset, calculate eight what-if previews
--run       optional fresh *report only* and SHA receipt; NO forcing writes
"""
import argparse
from datetime import datetime, timezone
import hashlib, importlib.util, json
from pathlib import Path
import sys, traceback
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="stage11o-v1-20261024-two-shifted-edge-source-RH-sensitivity"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
REPO=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
N=REPO/"scripts/stage11/11n_seven_candidate_four_boundary_RH_sensitivity_READONLY.py"
N_BLOB="4a6e927e27eb237a9fb4fdfc2d93ce4235afe847"
M=ROOT/"reports/stage11m_stage11l_four_boundary_context_20261024T101551Z_e5027215"
L=ROOT/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
SENTINELS={"MAR18":"202503181730","MAR25":"202503251100"}
OLDSEVEN={
 "202503181800",
 "202503230730","202503230800","202503230830",
 "202503231530","202503231600",
 "202503251030"
}
SENTINEL_GROUP={
 "MAR18":"202503181730",
 "MAR25":"202503251100"
}
EDGES=[
 ("MAR18_BEFORE","202503181700","202503181730"),
 ("MAR18_SHIFTED","202503181730","202503181800"),
 ("MAR18_OLD","202503181800","202503181830"),
 ("MAR23_OLD_START","202503230830","202503230900"),
 ("MAR23_NEW_END","202503231500","202503231530"),
 ("MAR23_LATE_END","202503231600","202503231630"),
 ("MAR25_OLD","202503251000","202503251030"),
 ("MAR25_SHIFTED","202503251030","202503251100"),
 ("MAR25_LATE","202503251100","202503251130"),
 ("MAR25_LATER","202503251130","202503251200"),
]
SCENARIOS={
 "STAGE11L_UNCHANGED":[],
 "MAR18_18ONLY":["MAR18_18"],
 "MAR18_18PLUS_1730":["MAR18_18","MAR18_EXTRA"],
 "MAR23_FIVE_ONLY":["MAR23_5"],
 "MAR25_1030ONLY":["MAR25_1030"],
 "MAR25_1030PLUS_1100":["MAR25_1030","MAR25_EXTRA"],
 "ALL7_UNAPPROVED":["MAR18_18","MAR23_5","MAR25_1030"],
 "ALL7_PLUS_TWO_UNAPPROVED":["MAR18_18","MAR23_5","MAR25_1030",
                             "MAR18_EXTRA","MAR25_EXTRA"],
}
GROUPS={
 "MAR18_18":{"202503181800"},
 "MAR18_EXTRA":{"202503181730"},
 "MAR23_5":{"202503230730","202503230800","202503230830",
            "202503231530","202503231600"},
 "MAR25_1030":{"202503251030"},
 "MAR25_EXTRA":{"202503251100"},
}


def safe_file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink SHA source "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe_file(p).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()

def gitblob(p):
    b=safe_file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def get_stage11n():
    if gitblob(N)!=N_BLOB:
        raise ValueError("Source Stage11n Python SHA1 Git blob differs")
    spec=importlib.util.spec_from_file_location("stage11n_pinned_for_stage11o",N)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def self_test():
    assert len(OLDSEVEN)==7 and len(SENTINEL_GROUP)==2
    assert OLDSEVEN.isdisjoint(set(SENTINEL_GROUP.values()))
    assert len(EDGES)==10 and len(SCENARIOS)==8
    assert len({k for v in GROUPS.values() for k in v})==9
    for _,a,b in EDGES:
        start=pd.to_datetime(a,format="%Y%m%d%H%M")
        end=pd.to_datetime(b,format="%Y%m%d%H%M")
        assert end-start==pd.Timedelta(minutes=30)
    es=6.112*np.exp(17.67*20./(20.+243.5))
    assert es>20.
    print("STAGE11O SELF-TEST PASS: 7 prior+2 shifted-edge sentinels, 8 in-memory scenarios, fixed EC TA, no writes",flush=True)

def evaluate():
    n=get_stage11n()
    oldseven,_,_=n.audit()  # Reverify sealed Stage11m and Stage11l inputs.
    ctx=pd.read_csv(safe_file(M/"40_halfhours_original_ERA_Stage07_Stage11h_Stage11l_context.csv"),
                    dtype={"native_key":str},low_memory=False)
    if len(ctx)!=40:
        raise ValueError("Stage11m four-boundary source context no longer exact 40 rows")
    data=pd.read_csv(safe_file(L/"US-NC2_humidity_only_new_shadow_NOLEAP.csv"),
                     low_memory=False)
    if len(data)!=367920:
        raise ValueError("Full Stage11l forcing length changed")
    if not oldseven.native_key.is_unique or set(oldseven.native_key)!=OLDSEVEN:
        raise ValueError("Original 7 Stage11n independent source candidates differ")
    t=pd.to_datetime(data.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    keys=t.dt.strftime("%Y%m%d%H%M").to_numpy()
    idx={key:i for i,key in enumerate(keys)}
    if len(idx)!=367920:
        raise ValueError("Full Stage11l source-native time duplicated")
    for _,a,b in EDGES:
        if a not in idx or b not in idx or idx[b]!=idx[a]+1:
            raise ValueError("Stage11o source-native boundary not consecutive")
    source=ctx.set_index("native_key")
    if not source.index.is_unique:
        raise ValueError("Stage11m 40 original context keys unexpectedly duplicated")
    newrows=[]
    for group,key in SENTINELS.items():
        if key not in source.index or key not in idx:
            raise ValueError("One of two exact shifted-edge source timestamps missing")
        r=source.loc[key]
        i=idx[key]
        if (str(r.site)!="US-NC2" or
            bool(r.Stage07_VPD_changed_from_source) or
            bool(r.Stage11h_VPD_changed_from_Stage07) or
            bool(r.Stage11l_VPD_changed_from_Stage11h) or
            abs(float(r.Stage11l_VPD_hPa)-float(data.VPD_USE.iloc[i]))>1e-8 or
            abs(float(r.retained_EC_tower_TA_C)-float(data.TA_USE.iloc[i]))>1e-8):
            raise ValueError("One of two sentinel unmodified baseline source records differs")
        ta=float(data.TA_USE.iloc[i])
        pa=float(data.PSRF.iloc[i])
        newv,newq,erh=n.transfer(ta,pa,float(r.companion_ERA_T_C),
                                 float(r.companion_ERA_VPD_hPa))
        if abs(erh-float(r.companion_ERA_RH_water_pct))>1e-6:
            raise ValueError("ERA source RH does not match pinned Stage11m")
        newrows.append({"site":"US-NC2","group":group,"native_key":key,
            "source_original_VPD_QC":int(r.original_VPD_F_QC),
            "source_original_RH_pct":float(r.original_implied_RH_water_pct),
            "companion_ERA_RH_pct":erh,"retained_site_TA_C":ta,
            "old_Stage11l_VPD_hPa":float(data.VPD_USE.iloc[i]),
            "hypothetical_ERA_RH_VPD_hPa":newv,
            "hypothetical_QBOT":newq,
            "Stage11l_QBOT":float(data.QBOT.iloc[i]),
            "human_approval":False,
            "review_status":"HOLD_UNAPPROVED_WHAT_IF_NO_FORCING_WRITES"})
    extras=pd.DataFrame(newrows)
    # Prior 7 previously audited values are used verbatim, and the two new
    # values are recomputed from their exact source-native Stage11m records.
    preview={}
    for row in oldseven.itertuples(index=False):
        preview[row.native_key]=float(row.what_if_ERA_RH_VPD_hPa)
    for row in extras.itertuples(index=False):
        preview[row.native_key]=float(row.hypothetical_ERA_RH_VPD_hPa)
    if set(preview)!=OLDSEVEN|set(SENTINEL_GROUP.values()):
        raise ValueError("Nine exact source-native what-if targets differ")
    baseline=data.VPD_USE.to_numpy(dtype=float)
    summary=[]
    transitions=[]
    for scenario,group_names in SCENARIOS.items():
        active=set().union(*(GROUPS[g] for g in group_names)) if group_names else set()
        arr=baseline.copy()
        for key in active:
            arr[idx[key]]=preview[key]
        considered=[]
        for label,left,right in EDGES:
            i,j=idx[left],idx[right]
            oldjump=abs(baseline[j]-baseline[i])
            newjump=abs(arr[j]-arr[i])
            considered.append(newjump)
            transitions.append({
                "scenario":scenario,"boundary_id":label,
                "left_native_key":left,"right_native_key":right,
                "old_Stage11l_abs_jump_hPa":oldjump,
                "hypothetical_abs_jump_hPa":newjump,
                "change_in_abs_jump_hPa":newjump-oldjump,
                "introduced_jump_over_2hPa":bool(newjump-oldjump>2),
                "total_jump_over_4hPa":bool(newjump>4),
                "user_approved":False
            })
        summary.append({
            "scenario":scenario,"new_target_count":len(active),
            "max_of_ten_checked_jumps_hPa":max(considered),
            "sum_of_ten_checked_jumps_hPa":sum(considered),
            "jumps_over_4hPa":sum(x>4 for x in considered),
            "newly_added_jump_gt2hPa":sum(
                transitions[-10+i]["introduced_jump_over_2hPa"]
                for i in range(10)),
            "scientific_approval":"HOLD_NOT_APPROVED_NO_MODEL_RUN"
        })
    transition=pd.DataFrame(transitions)
    summary=pd.DataFrame(summary)
    if len(extras)!=2 or len(summary)!=8 or len(transition)!=80:
        raise ValueError("Stage11o source sensitivity expected 2 sentinel/8 scenario/80 edges")
    if int(summary.loc[summary.scenario.eq("STAGE11L_UNCHANGED"),
                      "new_target_count"].iloc[0])!=0:
        raise ValueError("Reference Stage11l baseline target count changed")
    return extras,oldseven,summary,transition

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--check",action="store_true")
    group.add_argument("--run",action="store_true")
    args=p.parse_args()
    print("STAGE11O — TWO SHIFTED VPD EVENT BOUNDARY SOURCE SENTINELS | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    extras,prior,summary,edges=evaluate()
    print("\n========== TWO NEW UNAPPROVED EDGE SENTINELS ==========",flush=True)
    print(extras[["native_key","source_original_VPD_QC","source_original_RH_pct",
            "companion_ERA_RH_pct","old_Stage11l_VPD_hPa",
            "hypothetical_ERA_RH_VPD_hPa"]].to_string(index=False),flush=True)
    print("\n========== EIGHT SCENARIOS MAX/MULTI-EDGE SUMMARY ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\n========== 10 EDGES - STAGE11L VS ALL7+TWO ==========",flush=True)
    focus=edges.loc[edges.scenario.eq("ALL7_PLUS_TWO_UNAPPROVED")]
    print(focus[["boundary_id","left_native_key","right_native_key",
        "old_Stage11l_abs_jump_hPa","hypothetical_abs_jump_hPa",
        "change_in_abs_jump_hPa"]].to_string(index=False),flush=True)
    print("\nSTAGE11O SUMMARY: 7 prior + 2 unapproved boundary sentinels=9 "
          "full_original_forcing_unchanged=True EC_tower_TA_unchanged=True "
          "human_new_approvals=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: no new report or forcing writes.",flush=True)
        return
    report=ROOT/"reports"/("stage11o_two_shifted_RH_boundaries_READ_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    report.mkdir(exist_ok=False)
    tables={
        "2_new_shifted_edge_source_humidity_candidates.csv":extras,
        "7_previous_human_review_candidates_no_changes.csv":prior,
        "8_hypothetical_scenarios_summary.csv":summary,
        "80_edge_comparisons_all_scenarios.csv":edges
    }
    for fname,table in tables.items():
        table.to_csv(report/fname,index=False)
    hold="""# STAGE11O — read-only review evidence, NO new user decisions
Nine source-native humidity what-if events were evaluated (7 previous
Stage11n + 2 new boundary sentinels). Source FLUXMET and paired
downscaled ERA RH are NOT an independent measurement of tower RH.
Stage07, Stage11h and Stage11l sealed forcing are unchanged. No VPD,
QBOT, TBOT, TA_USE or any other meteorological forcing value was written.
The 3 originally Stage07 corrected events must not be overwritten.
Propose an event-level scientific judgement and obtain explicit user
approval before creating ANY successor scientific forcing trial.
Post-v5/DATM/spinup approvals are ZERO.
"""
    (report/"SCIENTIFIC_HOLD.md").write_text(hold,encoding="utf-8")
    receipt={
        "version":VERSION,
        "prior_Stage11n_code_Git_blob":N_BLOB,
        "source_Stage11m_receipt_SHA256":sha(M/"stage11m_read_only_boundary_receipt.json"),
        "source_Stage11l_receipt_SHA256":sha(L/"stage11l_scientific_hold_receipt.json"),
        "new_hypothetical_only_native_times":2,
        "prior_hypothetical_only_native_times":7,
        "scenario_count":8,"boundary_comparison_rows":80,
        "new_human_approvals":0,"Postv5_approved":0,
        "DATM_ready":0,"spinup_authorized":0,
        "forcing_modified":False,
        "output_sha256":{name:sha(report/name) for name in [*tables,"SCIENTIFIC_HOLD.md"]}
    }
    (report/"stage11o_read_only_science_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11O REPORT DIR:",report,flush=True)
    print("NO STAGE07, STAGE11H, STAGE11L, DATM, CIME OR SLURM MODIFIED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE11O STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

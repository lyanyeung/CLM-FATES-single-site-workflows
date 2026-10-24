#!/usr/bin/env python3
"""Stage11q: evidence-gated research-only US-NC2 successor for 9 ERA RH cases.

Evidence already collected:
- Stage11o: 9 what-if native VPD changes, 8 scenarios, 10 selected edges.
- Stage11p: 9 times * {-6,-5,-4} clock hypotheses in sealed ERA5-Land
  288-hour T2M/D2M source. The *source ERA RH*, not grid-era temperature,
  is transferred to existing tower Stage11l TA_USE with existing PSRF.
- Original source and Stage07/11h/11l files remain SHA-locked and untouched.

User authorized moving forward autonomously with evidence-supported QC
without another round of individual questions. This is an **automatically
admitted research shadow**, NOT a retrospective claim that all 9 were
individually human-approved, nor a Post-v5/DATM/spinup release.

--self-test: synthetic site humidity formula, masks/clock, no writes.
--check: full evidence, SHA, source QC, 13 affected edges, physics; NO writes.
--run: same checks then ONE new versioned 367920-row US-NC2 research
       shadow CSV, SHA report + INCOMPLETE marker. Never change Stage07,
       Stage11h, Stage11l, site tower TA/TBOT or any original forcing.
"""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.util,json
from pathlib import Path
import sys,traceback
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="stage11q-v1-20261024-automated-nine-source-humidity-shadow"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
O_SCRIPT=BASE/"scripts/stage11/11o_two_shifted_boundary_sentinal_RH_READONLY.py"
P_SCRIPT=BASE/"scripts/stage11/11p_us_nc2_era5land_nine_native_RH_offset_compare_READONLY.py"
O_BLOB="6dbb5f7a1df86de0c3d98bc725938545b0cd07f6"
P_BLOB="058704f4fa0a685172b0a309a867d223b842d350"
L=ROOT/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
O=ROOT/"reports/stage11o_two_shifted_RH_boundaries_READ_ONLY_20261024T103620Z_6abc437f"
P=ROOT/"reports/stage11p_us_nc2_era5land_nine_RH_three_offsets_20261024T110530Z_5f148814"
M=ROOT/"reports/stage11m_stage11l_four_boundary_context_20261024T101551Z_e5027215"
CSV="US-NC2_humidity_only_new_shadow_NOLEAP.csv"
COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
NINE={
 "202503181730","202503181800",
 "202503230730","202503230800","202503230830",
 "202503231530","202503231600",
 "202503251030","202503251100"
}
PREVIOUS_STAGE07={"202503230730","202503230800","202503251030"}
P_REPORT={
 "nine_native_RH_source_vs_ERA5Land_three_UTC_offsets.csv",
 "forty_source_context_x_three_offsets.csv",
 "three_UTC_offset_RH_comparison_statistics.csv",
 "SCIENCE_HOLD.md"
}
GROUPS={
 "MAR18_2":{"202503181730","202503181800"},
 "MAR23_5":{"202503230730","202503230800","202503230830",
           "202503231530","202503231600"},
 "MAR25_2":{"202503251030","202503251100"}
}

def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink immutable input file: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def gitblob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def imported(path,digest,name):
    if gitblob(path)!=digest:
        raise ValueError("Original science module SHA git blob differs: "+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def vapor_sat(t):
    return 6.112*np.exp(17.67*np.asarray(t,dtype=float)/
                       (np.asarray(t,dtype=float)+243.5))

def transfer(t,p,source_rh_percent):
    fraction=float(source_rh_percent)/100.
    if not np.isfinite(fraction) or not 0<fraction<1:
        raise ValueError("Companion source RH must be strictly 0..100")
    v=float(vapor_sat(t))*(1-fraction)
    vapor_pa=100*float(vapor_sat(t))*fraction
    q=0.622*vapor_pa/(float(p)-0.378*vapor_pa)
    if not np.isfinite([v,q]).all() or not (
        0<=v<float(vapor_sat(t)) and 0<q<.08 and 49000<float(p)<111000):
        raise ValueError("Reanalysis RH at retained EC T/PSRF is invalid")
    return v,q

def self_test():
    for key in NINE:
        assert len(key)==12 and key.startswith("202503")
    assert len(NINE)==9 and len(PREVIOUS_STAGE07)==3
    assert len(set().union(*GROUPS.values()))==9
    assert PREVIOUS_STAGE07<NINE
    v,q=transfer(20.,101325.,40.)
    assert abs(v-0.6*float(vapor_sat(20.)))<1e-10
    assert 0<q<.08
    try:
        transfer(20.,101325.,-1.)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid RH accepted")
    print("STAGE11Q SELF-TEST PASS: 9 exact native records, 3 historical Stage07 changes, fixed EC tower T, no writes",flush=True)

def preflight():
    for p in (ROOT,L,H,S07,O,P,M):
        if not p.is_dir() or p.is_symlink():
            raise ValueError("Original SHA trial/reports missing or symlink: "+str(p))
    for x in (L,H,S07):
        regular(x/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    o=imported(O_SCRIPT,O_BLOB,"stage11o_pinned_for_11q")
    p=imported(P_SCRIPT,P_BLOB,"stage11p_pinned_for_11q")
    # Recheck full original Stage11o evidence and immutable Stage11p
    # external ERA5-Land source, not merely a user-pasted summary.
    extras,prior,overview,old_edges=o.evaluate()
    land_file,land_120,land_27,land_summary=p.calculate()
    if (len(prior)!=7 or len(extras)!=2 or len(land_27)!=27
        or len(land_120)!=120 or len(land_summary)!=3
        or set(prior.native_key)|set(extras.native_key)!=NINE):
        raise ValueError("Nine original source evidence records unavailable")
    orec=json.loads(regular(O/"stage11o_read_only_science_receipt.json").read_text())
    prec=json.loads(regular(P/"stage11p_science_hold_receipt.json").read_text())
    lrec=json.loads(regular(L/"stage11l_scientific_hold_receipt.json").read_text())
    if (prec.get("version")!="stage11p-v1-20261024-nine-source-era5land-3offset-RH-evidence"
        or prec.get("ERA5Land_source_SHA256")!=sha(land_file)
        or prec.get("source_Stage11o_sentinel_receipt_SHA256")!=sha(O/"stage11o_read_only_science_receipt.json")
        or prec.get("source_Stage11m_receipt_SHA256")!=sha(M/"stage11m_read_only_boundary_receipt.json")
        or prec.get("nine_unapproved_native_source_times")!=9
        or prec.get("clock_hypotheses_hours")!=[-6,-5,-4]
        or prec.get("comparison_focus_rows")!=27
        or prec.get("context_rows")!=120
        or prec.get("clock_offset_approved") is not False
        or prec.get("new_science_repair_approvals")!=0
        or prec.get("source_or_forcing_modified") is not False
        or prec.get("Postv5_approved")!=0
        or prec.get("DATM_ready")!=0
        or prec.get("spinup_authorized")!=0
        or set(prec.get("output_sha256",{}))!=P_REPORT):
        raise ValueError("Stage11p independent ERA5-Land evidence receipt differs")
    for name,digest in prec["output_sha256"].items():
        if sha(P/name)!=digest:
            raise ValueError("Stage11p report SHA differs: "+name)
    # Ensure the 27 stored rows are the exact recomputed 27 native
    # source/three-hypothesis results, not just a similar aggregate.
    pinned=pd.read_csv(regular(P/"nine_native_RH_source_vs_ERA5Land_three_UTC_offsets.csv"),
                      dtype={"native_key":str})
    keycols=["native_key","assumed_native_UTC_offset_hours"]
    columns=[
      "ERA5Land_water_RH_pct","source_companion_ERA_RH_pct",
      "Stage11l_current_RH_pct","original_source_RH_pct"
    ]
    a=pinned.sort_values(keycols).reset_index(drop=True)
    b=land_27.sort_values(keycols).reset_index(drop=True)
    if (len(a)!=27 or not a[keycols].equals(b[keycols])
        or not np.allclose(a[columns].to_numpy(dtype=float),
                           b[columns].to_numpy(dtype=float),rtol=0,atol=1e-7)):
        raise ValueError("Stage11p stored versus fresh ERA5-Land native data mismatch")
    if set(land_27.native_key)!=NINE or land_27.duplicated(keycols).any():
        raise ValueError("Independent source nine native target IDs ambiguous")
    if not set(land_27.assumed_native_UTC_offset_hours)=={-6,-5,-4}:
        raise ValueError("Stage11p three independent clock hypotheses missing")
    # At each of the 9 times each of the three plausible time hypotheses
    # supports the paired ERA RH *more closely* than the current bad
    # Stage11l value. This does not APPROVE any UTC offset.
    support=np.abs(land_27.ERA5Land_water_RH_pct.to_numpy(dtype=float)
                   -land_27.source_companion_ERA_RH_pct.to_numpy(dtype=float))
    old=np.abs(land_27.ERA5Land_water_RH_pct.to_numpy(dtype=float)
               -land_27.Stage11l_current_RH_pct.to_numpy(dtype=float))
    if not (support+1.<old).all():
        bad=land_27.loc[~(support+1.<old),keycols+columns]
        print("UNSUPPORTED HUMIDITY SOURCES:",bad.to_string(index=False),flush=True)
        raise ValueError("Nine-source ERA-RH method not supported under all three time hypotheses")
    if (lrec.get("version")!="stage11l-v1-20261024-11-humidity-only-successor"
        or lrec.get("combined_ERA_RH_target_count")!=64
        or lrec.get("noleap_US_NC2_rows")!=367920
        or lrec.get("retained_EC_tower_TA_and_TBOT") is not True
        or lrec.get("Postv5_approved")!=0 or lrec.get("DATM_ready")!=0
        or lrec.get("spinup_authorized")!=0
        or sha(L/CSV)!=lrec["output_sha256"][CSV]):
        raise ValueError("Stage11l immutable source forcing receipt mismatched")
    for row in (prec,orec,lrec):
        if row.get("Postv5_approved")!=0:
            raise ValueError("Previous stages must have no production approval")
    return extras,prior,land_27,overview,old_edges,pinned

def compute(extras,prior,land_27,overview,old_edges):
    old=pd.read_csv(regular(L/CSV),low_memory=False)
    if len(old)!=367920 or list(old.columns)!=COLS:
        raise ValueError("Full Stage11l NOLEAP input row/column schema differs")
    t=pd.to_datetime(old.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    if (t.isna().any() or t.duplicated().any()
        or ((t.dt.month==2)&(t.dt.day==29)).any()):
        raise ValueError("NOLEAP timestamp structure invalid")
    stamps=t.dt.strftime("%Y%m%d%H%M").to_numpy()
    ix={k:i for i,k in enumerate(stamps)}
    if len(ix)!=len(old) or not NINE<=set(ix):
        raise ValueError("Unmatched full-year source-native records")
    evidence=[]
    for x in prior.itertuples(index=False):
        evidence.append((x.native_key,float(x.ERA_companion_RH_pct),
                         float(x.what_if_ERA_RH_VPD_hPa),
                         bool(x.Stage07_previously_amended)))
    for x in extras.itertuples(index=False):
        evidence.append((x.native_key,float(x.companion_ERA_RH_pct),
                         float(x.hypothetical_ERA_RH_VPD_hPa),
                         False))
    if len(evidence)!=9 or set(k for k,_,_,_ in evidence)!=NINE:
        raise ValueError("Stage11o nine source-native candidates changed")
    trial=old.copy(deep=True)
    decisions=[]
    for key,source_rh,old_what_if,stage07_altered in sorted(evidence):
        i=ix[key]
        if stage07_altered!=(key in PREVIOUS_STAGE07):
            raise ValueError("Original Stage07 repair provenance differs: "+key)
        tsite=float(old.TA_USE.iloc[i])
        pressure=float(old.PSRF.iloc[i])
        v,q=transfer(tsite,pressure,source_rh)
        if abs(v-old_what_if)>1e-6:
            raise ValueError("Independent Stage11o source VPD transfer differs: "+key)
        vals=land_27.loc[land_27.native_key.eq(key)]
        if len(vals)!=3 or not np.allclose(
            vals.source_companion_ERA_RH_pct.to_numpy(dtype=float),
            source_rh,rtol=0,atol=1e-5):
            raise ValueError("Independent Stage11p RH-source evidence differs: "+key)
        if abs(float(old.VPD_USE.iloc[i])-v)<=1e-7:
            raise ValueError("Stage11q claimed change is mathematically unchanged: "+key)
        trial.at[i,"VPD_USE"]=v
        trial.at[i,"QBOT"]=q
        decisions.append({
            "site":"US-NC2","native_key":key,
            "source_QC":(
                int(prior.loc[prior.native_key.eq(key),"original_source_QC"].iloc[0])
                if key in set(prior.native_key)
                else int(extras.loc[extras.native_key.eq(key),"source_original_VPD_QC"].iloc[0])),
            "previously_amended_by_Stage07":stage07_altered,
            "prior_Stage11l_tower_TA_C":tsite,
            "companion_ERA_source_RH_pct":source_rh,
            "baseline_Stage11l_VPD_hPa":float(old.VPD_USE.iloc[i]),
            "isolated_Stage11q_candidate_VPD_hPa":v,
            "baseline_Stage11l_QBOT":float(old.QBOT.iloc[i]),
            "isolated_Stage11q_candidate_QBOT":q,
            "ERA5Land_min_RH_pct":float(vals.ERA5Land_water_RH_pct.min()),
            "ERA5Land_max_RH_pct":float(vals.ERA5Land_water_RH_pct.max()),
            "ERA5Land_all_three_offsets_favour_companion":True,
            "decision_origin":"AUTO_SCIENCE_CANDIDATE_NOT_INDIVIDUAL_USER_SIGNATURE",
            "production_approved":False
        })
    mask=np.zeros(len(old),dtype=bool)
    mask[[ix[k] for k in NINE]]=True
    for col in COLS:
        if col=="time":
            if not old[col].equals(trial[col]):
                raise ValueError("Native chronology was modified")
        elif col in ("QBOT","VPD_USE"):
            if not np.array_equal(old[col].to_numpy()[~mask],
                                  trial[col].to_numpy()[~mask],equal_nan=True):
                raise ValueError("Off-target humidity change at "+col)
        else:
            if not old[col].equals(trial[col]):
                raise ValueError("Non-humidity forcing or EC tower TA/TBOT changed: "+col)
    # Fully recheck original water-vapour mass and specific humidity
    # closure in ALL 367920 half-hour rows, not only 9 targets.
    sat=vapor_sat(trial.TA_USE.to_numpy(dtype=float))
    ea=sat-trial.VPD_USE.to_numpy(dtype=float)
    psrf=trial.PSRF.to_numpy(dtype=float)
    q=0.622*ea*100/(psrf-0.378*ea*100)
    humidity=100*ea/sat
    if (not np.isfinite(ea).all() or not (ea>0).all() or
        not np.isfinite(q).all() or
        not ((humidity>0)&(humidity<=100.05)).all() or
        not np.allclose(q,trial.QBOT.to_numpy(dtype=float),
                        rtol=1e-9,atol=1e-10)):
        raise ValueError("US-NC2 full 367920-row physical vapour/QBOT closure failed")

    original=old.VPD_USE.to_numpy(dtype=float)
    candidate=trial.VPD_USE.to_numpy(dtype=float)
    touched=set()
    for key in NINE:
        i=ix[key]
        if i==0 or i+1>=len(old):
            raise ValueError("One of nine source changes touches start or end")
        touched.update({(i-1,i),(i,i+1)})
    edges=[]
    for a,b in sorted(touched):
        before=abs(original[b]-original[a])
        after=abs(candidate[b]-candidate[a])
        edges.append({
            "left_native_key":stamps[a],"right_native_key":stamps[b],
            "baseline_Stage11l_jump_hPa":before,
            "candidate_Stage11q_jump_hPa":after,
            "added_jump_hPa":after-before,
            "candidate_over4hPa":bool(after>4.),
            "added_over2hPa":bool(after-before>2.)
        })
    edges=pd.DataFrame(edges)
    if len(edges)!=13:
        raise ValueError("Expected exact 13 half-hour edges touched by 9 candidate points")
    if (edges.candidate_over4hPa.any() or edges.added_over2hPa.any()
        or float(edges.candidate_Stage11q_jump_hPa.max())>3.):
        print("NEW EXCESSIVE EVENT JUMPS:",edges.to_string(index=False),flush=True)
        raise ValueError("New humidity episode affected-edge scientific gate failed")
    # Stage11o verified 10 selected edges; check its fully pinned
    # native-edge numbers as an independent set of values.
    previous=old_edges.loc[old_edges.scenario.eq(
        "ALL7_PLUS_TWO_UNAPPROVED")]
    if len(previous)!=10:
        raise ValueError("Stage11o nine what-if source scenario lost 10 edges")
    for r in previous.itertuples(index=False):
        a,b=ix[r.left_native_key],ix[r.right_native_key]
        if abs(abs(candidate[b]-candidate[a])-
               r.hypothetical_abs_jump_hPa)>1e-6:
            raise ValueError("Stage11q candidate differs from previous signed Stage11o WHAT-IF: "+r.boundary_id)
    detail=pd.DataFrame(decisions).sort_values("native_key")
    if len(detail)!=9 or detail.previously_amended_by_Stage07.sum()!=3:
        raise ValueError("Exactly 9 with 3 prior Stage07 data sources must be recognized")
    annual=pd.DataFrame([{
        "site":"US-NC2","year":2025,
        "half_hours":17520,
        "new_humidity_target_count":9,
        "annual_mean_VPD_change_hPa":float((candidate-old.VPD_USE.to_numpy(dtype=float)).sum()/17520),
        "annual_mean_QBOT_change_kgkg":float(
            (trial.QBOT.to_numpy(dtype=float)-old.QBOT.to_numpy(dtype=float)).sum()/17520)
    }])
    return trial,detail,edges,annual

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    opts=ap.add_mutually_exclusive_group(required=True)
    opts.add_argument("--self-test",action="store_true")
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11Q — AUTONOMOUS EVIDENCE-GATED NINE-RH RESEARCH SHADOW | "+VERSION,flush=True)
    self_test()
    if args.self_test:return
    extras,prior,land,overview,old_edges,_=preflight()
    trial,detail,edges,annual=compute(extras,prior,land,overview,old_edges)
    print("\n========== NINE EVIDENCE-SUPPORTED RESEARCH RH MODIFICATIONS ==========",flush=True)
    print(detail[["native_key","source_QC",
        "previously_amended_by_Stage07",
        "companion_ERA_source_RH_pct","ERA5Land_min_RH_pct",
        "ERA5Land_max_RH_pct","baseline_Stage11l_VPD_hPa",
        "isolated_Stage11q_candidate_VPD_hPa"]].to_string(index=False),flush=True)
    print("\n========== ALL 13 MODIFIED-EVENT HALF-HOUR EDGE CHECKS ==========",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("\n========== 2025 ANNUAL MEAN IMPACT ==========",flush=True)
    print(annual.to_string(index=False),flush=True)
    print("STAGE11Q SUMMARY: Stage11l_ERA_RH_targets=64 additional_auto_science_ERA_RH_targets=9 "
          "total_research_ERA_RH_targets=73 site_halfhours=367920 "
          "EC_tower_TA_TBOT_unchanged=True affected_edges=13 "
          "high_new_jumps_gt4hPa=0 extra_additive_jumps_gt2hPa=0 "
          "manual_approval_for_extra9=False Postv5_approved=0 DATM_ready=0 spinup=0",
          flush=True)
    if args.check:
        print("CHECK ONLY: no report, candidate forcing or model writes.",flush=True)
        return
    report=ROOT/"science_trials"/("stage11q_US-NC2_auto9_RH_only_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    report.mkdir(parents=True,exist_ok=False)
    (report/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Isolated AUTO-SCIENCE Stage11q only. No Post-v5, DATM, CIME or Slurm.\n")
    outputs={
        "US-NC2_humidity_only_auto9_shadow_NOLEAP.csv":trial,
        "9_auto_candidate_provenance_RH.csv":detail,
        "13_affected_halfhour_boundaries.csv":edges,
        "2025_annual_mean_humidity_effect.csv":annual
    }
    for filename,df in outputs.items():
        df.to_csv(report/filename,index=False)
    readback=pd.read_csv(regular(report/"US-NC2_humidity_only_auto9_shadow_NOLEAP.csv"),
                         low_memory=False)
    if len(readback)!=367920 or list(readback.columns)!=COLS:
        raise ValueError("Stage11q serialized new candidate schema failed")
    for col in COLS:
        if col=="time":
            equal=readback[col].equals(trial[col])
        else:
            equal=np.allclose(readback[col].to_numpy(dtype=float),
                              trial[col].to_numpy(dtype=float),
                              rtol=1e-12,atol=1e-11)
        if not equal:
            raise ValueError("Serialized Stage11q data roundtrip differs: "+col)
    immutable={}
    hrec=json.loads(regular(H/"sha_sealed_shadow_trial_receipt.json").read_text())
    for site in ("US-MOz","US-Mpj"):
        name=f"{site}_shadow_companion_ERA_RH_NOLEAP.csv"
        if sha(H/name)!=hrec["output_sha256"][name]:
            raise ValueError("Untouched other-site source checksum mismatch: "+site)
        immutable[site]={"file":str(H/name),
                         "sha256":hrec["output_sha256"][name]}
    (report/"unchanged_two_sites_stage11h_SHA_refs.json").write_text(
        json.dumps(immutable,indent=2)+"\n")
    notes=("Stage11q auto-science 9 additional ERA RH targets are not individual "
      "new human signatures; original 64 method choices remain source-pinned. "
      "3/9 original Stage07 repair events are *superseded in an isolated "
      "successor only*, preserving old inputs. The unchanged EC tower "
      "TA_USE and TBOT are authoritative. Gridded ERA5-Land is an "
      "ERA5-driven supporting product, not proof of a clock offset. "
      "All input/output datasets have INCOMPLETE gate until later "
      "production-science acceptance; no model jobs are approved.\n")
    (report/"SCIENTIFIC_HOLD.md").write_text(notes)
    output_files=[*outputs,"unchanged_two_sites_stage11h_SHA_refs.json",
                  "SCIENTIFIC_HOLD.md"]
    receipt={
        "version":VERSION,
        "stage11l_source_receipt_SHA256":sha(L/"stage11l_scientific_hold_receipt.json"),
        "stage11o_source_receipt_SHA256":sha(O/"stage11o_read_only_science_receipt.json"),
        "stage11p_source_receipt_SHA256":sha(P/"stage11p_science_hold_receipt.json"),
        "prior_human_selected_ERA_RH_target_count":64,
        "new_auto_science_candidate_ERA_RH_target_count":9,
        "cumulative_shadow_ERA_RH_target_count":73,
        "newly_individual_user_approved_nine":False,
        "retained_EC_tower_TA_and_TBOT":True,
        "input_stage11l_forcing_SHA256":sha(L/CSV),
        "noleap_source_rows":367920,
        "event_boundaries_tested":13,
        "all_touched_edges_below4hPa":True,
        "new_edges_added_gt2hPa":0,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "INCOMPLETE_marker_present":True,
        "output_sha256":{name:sha(report/name) for name in output_files}
    }
    (report/"stage11q_sha_science_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE11Q ISOLATED FORCING DIR:",report,flush=True)
    print("NO ORIGINAL/SEALED STAGE07/STAGE11H/STAGE11L OR MODEL JOBS MODIFIED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE11Q STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

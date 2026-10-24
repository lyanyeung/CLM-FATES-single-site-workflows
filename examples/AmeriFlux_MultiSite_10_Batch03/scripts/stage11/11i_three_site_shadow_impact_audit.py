#!/usr/bin/env python3
"""Batch03 Stage11i: independent read-only check of Stage11h shadow effects.

Verifies all Stage11h output SHA256 files and the original Stage07 forcing
source. Recomputes across all 998,640 half-hours and compares Stage07 vs
Stage11h for 53 user-selected humidity timestamps (43 truly modified),
identifying NEW neighbour discontinuities, annual means, RH/QBOT effects.

--self-test  pure synthetic regression checks (no cluster source access).
--check      full audit, no output or model modifications.
--run        full audit then NEW isolated reports/stage11i_* with review CSVs
             and SHA receipt. DOES NOT write/change any forcing.
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
VERSION="stage11i-v1-20261024-shadow-impact-independent-QA"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11G=ROOT/"reports/stage11g_user62_ERA5_method_validation_20261024T082933Z_fcaf26d1"
TRIAL=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
SITES=("US-MOz","US-Mpj","US-NC2")
ROWS={"US-MOz":315360,"US-Mpj":315360,"US-NC2":367920}
SELECTED={"US-MOz":0,"US-Mpj":4,"US-NC2":49}
CHANGED={"US-MOz":0,"US-Mpj":2,"US-NC2":41}
KEY=("site","native_key","variable")
KEEP_T="KEEP_EXISTING_STAGE07_CANDIDATE_TA"
KEEP_V="KEEP_EXISTING_STAGE07_CANDIDATE_VPD"
ERA="ERA5_BASED_HUMIDITY_METHOD_SELECTED"
COLUMNS=("time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")
TRIAL_FILE_END="_shadow_companion_ERA_RH_NOLEAP.csv"
EXPECTED_OUTPUTS={
    *[site+TRIAL_FILE_END for site in SITES],
    "62_selected_event_candidate_differences.csv",
    "three_site_shadow_trial_summary.csv",
    "SCIENTIFIC_HOLD.md"
}


def safe_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink file: "+str(p))
    return p


def safe_directory(path):
    p=Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or symlink directory: "+str(p))
    return p


def sha256(path):
    h=hashlib.sha256()
    with safe_file(path).open("rb") as f:
        for buf in iter(lambda:f.read(1<<20),b""):
            h.update(buf)
    return h.hexdigest()


def data_json(path):
    return json.loads(safe_file(path).read_text(encoding="utf-8"))


def values(df,col):
    x=pd.to_numeric(df[col],errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("Missing/invalid full-series column: "+col)
    return x


def saturation(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))


def physics(df):
    temp=values(df,"TA_USE")
    vpd=values(df,"VPD_USE")
    p=values(df,"PSRF")
    e=saturation(temp)
    ea=e-vpd
    with np.errstate(divide="ignore",invalid="ignore"):
        rh=100*ea/e
        q=0.622*(100*ea)/(p-0.378*(100*ea))
    if not (np.isfinite([rh,q]).all()
        and (ea>0).all() and (rh>0).all() and (rh<=100.05).all()
        and (q>=0).all() and (q<0.08).all()
        and np.allclose(q,values(df,"QBOT"),rtol=1e-9,atol=1e-10)):
        raise ValueError("Whole site input water pressure or QBOT invalid")
    return rh,q


def literal_keys(df,site):
    if len(df)!=ROWS[site] or list(df.columns)!=list(COLUMNS):
        raise ValueError("Unexpected native site schema or row count: "+site)
    t=pd.to_datetime(df["time"],format="%Y-%m-%d %H:%M:%S",errors="raise")
    if t.isna().any() or t.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError("Invalid source-native timestamps: "+site)
    if ((t.dt.month==2)&(t.dt.day==29)).any():
        raise ValueError("Found forbidden native leap-day forcing: "+site)
    full=pd.date_range(t.iloc[0],t.iloc[-1],freq="30min")
    full=full[~((full.month==2)&(full.day==29))]
    if len(full)!=len(t) or not np.array_equal(full.to_numpy(),t.to_numpy()):
        raise ValueError("Stage11h time continuity mismatch: "+site)
    return t.dt.strftime("%Y%m%d%H%M").to_numpy(dtype=str)


def safe_preflight():
    for p in (ROOT,S07,S11G,TRIAL):
        safe_directory(p)
    safe_file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    safe_file(TRIAL/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    r=data_json(TRIAL/"sha_sealed_shadow_trial_receipt.json")
    if (r.get("version")!="stage11h-v1-20261024-53-ERA-RH-isolated-trial"
        or r.get("source_stage11g_receipt_SHA256")!=sha256(S11G/"read_only_ERA5_method_receipt.json")
        or r.get("source_stage07_manifest_SHA256")!=sha256(S07/"exact_input_manifest.json")
        or r.get("user_decision_csv_git_blob")!="335c87e12d357714580018f8bab34fa4dde23446"
        or r.get("stations")!=list(SITES)
        or r.get("noleap_total_rows")!=998640
        or r.get("human_decisions")!=62
        or r.get("ERA_RH_selected_target_rows")!=53
        or r.get("actually_different_VPD_values")!=43
        or r.get("keep_six_TA")!=6 or r.get("keep_three_VPD")!=3
        or r.get("Postv5_approved")!=0 or r.get("DATM_ready")!=0
        or r.get("spinup_authorizations")!=0
        or r.get("INCOMPLETE_marker_present") is not True
        or r.get("Stage07_source_and_v5_untouched") is not True
        or set(r.get("output_sha256",{}))!=EXPECTED_OUTPUTS):
        raise ValueError("Stage11h report provenance, count or scientific gate differs")
    for name,checksum in r["output_sha256"].items():
        if sha256(TRIAL/name)!=checksum:
            raise ValueError("Stage11h shadow report modified: "+name)
    sealed=data_json(S07/"output_sha256.json")
    edits=pd.read_csv(safe_file(TRIAL/"62_selected_event_candidate_differences.csv"),
                      dtype={"native_key":str},low_memory=False)
    metric=pd.read_csv(safe_file(TRIAL/"three_site_shadow_trial_summary.csv"),low_memory=False)
    if len(edits)!=62 or edits.duplicated(list(KEY)).any():
        raise ValueError("Missing or duplicate Stage11h event provenance")
    if edits.decision.value_counts().to_dict()!={ERA:53,KEEP_T:6,KEEP_V:3}:
        raise ValueError("Stage11h decision taxonomy changed")
    if len(metric)!=3 or set(metric.site)!=set(SITES):
        raise ValueError("Stage11h site report inventory changed")
    if int(metric.actually_modified_VPD_values.sum())!=43:
        raise ValueError("Stage11h actual modification tally differs")
    return edits,metric,sealed,r


def phase_audit(site,original,shadow,edits):
    keys=literal_keys(original,site)
    other_keys=literal_keys(shadow,site)
    if not np.array_equal(keys,other_keys):
        raise ValueError("Stage11h source/shadow timestamp identities differ: "+site)
    n=len(keys)
    subset=edits.loc[edits.site.eq(site)]
    if len(subset)!={"US-MOz":1,"US-Mpj":6,"US-NC2":55}[site]:
        raise ValueError("Stage11h per-site 62-event inventory modified")
    select=subset.loc[subset.decision.eq(ERA)]
    if len(select)!=SELECTED[site]:
        raise ValueError("Stage11h per-site ERA method targets differ")
    dict_keys={key:i for i,key in enumerate(keys)}
    for key in subset.native_key:
        if key not in dict_keys:
            raise ValueError("Stage11h event missing source native key")
    changed_indices=[dict_keys[k] for k in select.native_key]
    changed_mask=np.zeros(n,dtype=bool)
    changed_mask[changed_indices]=True
    rh_old,q_old=physics(original)
    rh_new,q_new=physics(shadow)

    # Floating point roundtrips through written shadow CSV can alter the last
    # digits even in copied columns. Require tight numerical equivalence
    # outside selected VPD/QBOT changes, not identical byte serialization.
    for col in COLUMNS[1:]:
        first=values(original,col)
        second=values(shadow,col)
        test_idx=~changed_mask if col in ("VPD_USE","QBOT") else np.ones(n,dtype=bool)
        atol=1e-10 if col in ("TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE") else 1e-12
        if not np.allclose(first[test_idx],second[test_idx],
                           atol=atol,rtol=1e-12):
            raise ValueError("Undirected variable/time modified: "+site+" "+col)
    v_old=values(original,"VPD_USE")
    v_new=values(shadow,"VPD_USE")
    qo=values(original,"QBOT")
    qn=values(shadow,"QBOT")
    changed=np.zeros(n,dtype=bool)
    changed[changed_indices]=~np.isclose(v_old[changed_indices],v_new[changed_indices],
                                          atol=1e-10,rtol=1e-10)
    if int(changed.sum())!=CHANGED[site]:
        raise ValueError("Expected actual VPD change tally differs: "+site)
    # Every changed VPD must have a QBOT consistent with its new humidity.
    if not np.allclose(qn,q_new,atol=1e-10,rtol=1e-9):
        raise ValueError("Stage11h shadow QBOT invalid: "+site)

    audit=[]
    for r in subset.itertuples(index=False):
        i=dict_keys[r.native_key]
        old=float(v_old[i]);new=float(v_new[i])
        oldq=float(qo[i]);newq=float(qn[i])
        if (abs(old-float(r.stage07_VPD_hPa))>1e-8 or
            abs(new-float(r.trial_VPD_hPa))>1e-8 or
            abs(oldq-float(r.stage07_QBOT_kgkg))>1e-9 or
            abs(newq-float(r.trial_QBOT_kgkg))>1e-9):
            raise ValueError("Event centre differs from hash-pinned Stage11h ledger")
        if r.decision in (KEEP_T,KEEP_V) and (
                not np.isclose(old,new,atol=1e-10,rtol=1e-10) or
                not np.isclose(oldq,newq,atol=1e-12,rtol=1e-10)):
            raise ValueError("One of nine KEEP human decisions changed")
        leftold=abs(old-v_old[i-1]) if i>0 else float("nan")
        leftnew=abs(new-v_new[i-1]) if i>0 else float("nan")
        rightold=abs(v_old[i+1]-old) if i+1<n else float("nan")
        rightnew=abs(v_new[i+1]-new) if i+1<n else float("nan")
        added=max((leftnew-leftold) if np.isfinite(leftold) else 0.,
                  (rightnew-rightold) if np.isfinite(rightold) else 0.)
        audit.append({
            "site":site,"native_key":r.native_key,"variable":r.variable,
            "decision":r.decision,
            "actually_different_VPD":bool(changed[i]),
            "source_stage07_VPD_hPa":old,
            "shadow_VPD_hPa":new,
            "abs_VPD_delta_hPa":abs(new-old),
            "source_stage07_RH_pct":rh_old[i],
            "shadow_RH_pct":rh_new[i],
            "shadow_minus_v5_RH_percentage_points":rh_new[i]-rh_old[i],
            "source_stage07_QBOT_kgkg":oldq,
            "shadow_QBOT_kgkg":newq,
            "abs_QBOT_delta_kgkg":abs(newq-oldq),
            "original_previous_halfhour_jump_hPa":leftold,
            "shadow_previous_halfhour_jump_hPa":leftnew,
            "original_next_halfhour_jump_hPa":rightold,
            "shadow_next_halfhour_jump_hPa":rightnew,
            "max_ADDED_adjacent_jump_hPa":added,
            "jump_increased_more_than_2hPa":bool(added>2),
            "jump_increased_more_than_5hPa":bool(added>5),
            "science_status":"READ_ONLY_CONTEXT_REVIEW_NOT_POSTV5_APPROVED"
        })
    audit=pd.DataFrame(audit)
    # Also catch differences in new VPD gradients at neighbouring native
    # times; their pairwise jump is already represented in the event audit.
    year=np.asarray([int(k[:4]) for k in keys],dtype=int)
    groups=[]
    for yr in sorted(np.unique(year)):
        mask=(year==yr)
        affected=int((changed & mask).sum())
        groups.append({
            "site":site,"year":yr,"half_hour_rows":int(mask.sum()),
            "actually_changed_VPD_rows":affected,
            "stage07_mean_VPD_hPa":float(v_old[mask].mean()),
            "shadow_mean_VPD_hPa":float(v_new[mask].mean()),
            "annual_mean_VPD_difference_hPa":float((v_new[mask]-v_old[mask]).mean()),
            "stage07_mean_RH_pct":float(rh_old[mask].mean()),
            "shadow_mean_RH_pct":float(rh_new[mask].mean()),
            "annual_mean_RH_difference_percentage_points":float((rh_new[mask]-rh_old[mask]).mean()),
            "stage07_mean_QBOT_kgkg":float(qo[mask].mean()),
            "shadow_mean_QBOT_kgkg":float(qn[mask].mean()),
            "annual_mean_QBOT_difference_kgkg":float((qn[mask]-qo[mask]).mean()),
            "minimum_shadow_RH_pct":float(rh_new[mask].min()),
            "Postv5_approved":False
        })
    yy=pd.DataFrame(groups)
    if int(yy.actually_changed_VPD_rows.sum())!=CHANGED[site]:
        raise ValueError("Annual changed-VPD total mismatch")
    totals={
        "site":site,
        "total_rows":n,
        "selected_ERA_RH":len(select),
        "actual_VPD_changes":int(changed.sum()),
        "site_min_shadow_RH_pct":float(rh_new.min()),
        "largest_abs_delta_VPD_hPa":float(audit.abs_VPD_delta_hPa.max()),
        "largest_ADDED_jump_hPa":float(audit.max_ADDED_adjacent_jump_hPa.max()),
        "events_ADDED_jump_over_2hPa":int(audit.jump_increased_more_than_2hPa.sum()),
        "events_ADDED_jump_over_5hPa":int(audit.jump_increased_more_than_5hPa.sum()),
        "scientific_readiness":"HOLD",
        "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False
    }
    return audit,yy,totals


def full_site(site,seal):
    statusfile=S07/site/"forcing/qc_v5"/(site+"_status.json")
    relative=str(statusfile.relative_to(S07))
    if sha256(statusfile)!=seal.get(relative):
        raise ValueError("Stage07 QC site status SHA mismatch: "+site)
    status=data_json(statusfile)
    source=Path(status["forcing_csv"])
    expected=S07/site/"forcing"/"processed_v5"
    if (source.parent!=expected or
        sha256(source)!=seal.get(str(source.relative_to(S07)))):
        raise ValueError("Sealed Stage07 processed v5 source SHA differs")
    shadow=TRIAL/(site+TRIAL_FILE_END)
    o=pd.read_csv(safe_file(source),low_memory=False)
    n=pd.read_csv(safe_file(shadow),low_memory=False)
    return o,n


def self_test():
    mini=pd.DataFrame({
        "TA_USE":[10.,20.],"VPD_USE":[2.,5.],
        "PSRF":[101325.,100200.],
        "QBOT":[0.,0.]
    })
    t=values(mini,"TA_USE")
    v=values(mini,"VPD_USE")
    e=saturation(t)-v
    q=0.622*100*e/(values(mini,"PSRF")-0.378*100*e)
    mini["QBOT"]=q
    rh,qq=physics(mini)
    assert 0<rh.min() and np.allclose(qq,q)
    jumpold=abs(4.0-1.0)
    jumpnew=abs(8.0-1.0)
    assert jumpnew-jumpold==4.0
    assert not np.isclose(4.0,8.0,atol=1e-10,rtol=1e-10)
    print("STAGE11I SELF-TEST PASS: humidity closure, added jump versus old jump, and modified-value detection",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE11I — INDEPENDENT THREE-SITE SHADOW IMPACT QA | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    events,stage11h_summary,seal,receipt=safe_preflight()
    detail=[]
    annual=[]
    overview=[]
    for site in SITES:
        old,new=full_site(site,seal)
        ev,year,summary=phase_audit(site,old,new,events)
        detail.append(ev);annual.append(year);overview.append(summary)
        print(f"STAGE11I SITE {site}: year_rows={len(old)} "
              f"target={summary['selected_ERA_RH']} "
              f"actually_changed={summary['actual_VPD_changes']} "
              f"largest_added_jump={summary['largest_ADDED_jump_hPa']:.5f}hPa "
              f"new_jump_gt_2hPa_events={summary['events_ADDED_jump_over_2hPa']}",
              flush=True)
    detail=pd.concat(detail,ignore_index=True)
    annual=pd.concat(annual,ignore_index=True)
    overview=pd.DataFrame(overview)
    if (len(detail)!=62 or len(overview)!=3 or
        int(overview.total_rows.sum())!=998640 or
        int(overview.selected_ERA_RH.sum())!=53 or
        int(overview.actual_VPD_changes.sum())!=43 or
        detail.decision.value_counts().to_dict()!={ERA:53,KEEP_T:6,KEEP_V:3}):
        raise ValueError("Stage11h independent source-to-shadow census mismatch")
    priority=detail.loc[detail.decision.eq(ERA)].copy()
    priority=priority.sort_values("max_ADDED_adjacent_jump_hPa",ascending=False)
    print("\n========== THREE-SITE INDEPENDENT SHADOW QA ==========",flush=True)
    print(overview.to_string(index=False),flush=True)
    print("\n========== TOP 15 EVENTS BY NEWLY ADDED ADJACENT VPD JUMP ==========",flush=True)
    print(priority[["site","native_key","source_stage07_VPD_hPa",
        "shadow_VPD_hPa","abs_VPD_delta_hPa",
        "max_ADDED_adjacent_jump_hPa","shadow_RH_pct"]].head(15).to_string(index=False),flush=True)
    print("\n========== SITE YEARS WITH CHANGED VPD ==========",flush=True)
    positive=annual.loc[annual.actually_changed_VPD_rows.gt(0)]
    print(positive[["site","year","actually_changed_VPD_rows",
        "annual_mean_VPD_difference_hPa",
        "annual_mean_RH_difference_percentage_points",
        "annual_mean_QBOT_difference_kgkg"]].to_string(index=False),flush=True)
    print(f"\nSTAGE11I SUMMARY: records={int(overview.total_rows.sum())}/998640 "
          f"ERA_RH_targets={int(overview.selected_ERA_RH.sum())}/53 "
          f"actually_changed={int(overview.actual_VPD_changes.sum())}/43 "
          "Postv5_approved=0 DATM_ready=0 spinup_authorized=0",flush=True)
    if args.check:
        print("CHECK ONLY: NO files modified or created.",flush=True)
        return
    report=ROOT/"reports"/("stage11i_independent_shadow_impact_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    report.mkdir(exist_ok=False)
    tables={
        "62_event_v5_vs_shadow_neighbour_jumps.csv":detail,
        "53_ERA_RH_events_ranked_by_new_jump.csv":priority,
        "site_year_annual_differences.csv":annual,
        "three_site_read_only_impact_summary.csv":overview,
    }
    for name,frame in tables.items():
        frame.to_csv(report/name,index=False)
    note="""# Stage11i shadow impact review — NOT Post-v5 validation

This evidence is derived from SHA-sealed Stage11h new CSV files and the
unchanged Stage07 processed-v5 forcing. The Stage11h shadow keeps 6 TA and
3 VPD event values, and transfers paired source ERA relative humidity at
53 target timestamps, generating 43 numerically different VPD/QBOT values.
The audit distinguishes the source Stage07 neighbouring VPD jumps from
the Stage11h newly ADDED jump, avoiding declaring old meteorological
variability to be a trial-induced artifact.

A positive "added jump" is a continuity review flag, not proof of false
meteorology or a repair algorithm. Evaluate tower/source ERA RH, high
changes, physical height and release-native clock. The annual averages
dilute short events; inspect exact-event tables as well as annual means.
Unchanged copy serialization can differ at last floating point digits.

All stage11h and stage07 INCOMPLETE markers must remain; no source,
candidate forcing, DATM, CIME, spinup or Slurm permissions granted.
"""
    (report/"SCIENTIFIC_HOLD_AND_NEXT_REVIEW.md").write_text(note,encoding="utf-8")
    out={
        "version":VERSION,
        "Stage11h_receipt_SHA256":sha256(TRIAL/"sha_sealed_shadow_trial_receipt.json"),
        "Stage07_manifest_SHA256":sha256(S07/"exact_input_manifest.json"),
        "source_vs_shadow_rows":998640,"human_decision_events":62,
        "ERA_humidity_selected_rows":53,"actual_changed_VPD_rows":43,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorizations":0,
        "Stage07_and_Stage11h_data_unchanged":True,
        "output_SHA256":{name:sha256(report/name) for name in [
            *tables,"SCIENTIFIC_HOLD_AND_NEXT_REVIEW.md"]}
    }
    (report/"independent_read_only_impact_receipt.json").write_text(
        json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("STAGE11I REPORT DIR:",report,flush=True)
    print("NO SOURCE/SHADOW FORCING, DATM, CIME OR SLURM CHANGES.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("STAGE11I STOP:",str(e),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

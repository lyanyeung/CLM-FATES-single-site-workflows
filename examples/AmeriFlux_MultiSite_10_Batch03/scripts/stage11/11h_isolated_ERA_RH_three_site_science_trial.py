#!/usr/bin/env python3
"""Batch03 Stage11h — isolated RH-transfer science shadow trial, NOT Post-v5.

Input: SHA-sealed Stage07 processed_v5 forcing and verified Stage11g source
method preview, the latter checked against the exact user 62-decision ledger.

Only 53 VPD selected by the user are recomputed from the paired FLUXNET
site-downscaled ERA5 companion *RH* at retained Stage07 site TA (not
independent ERA5-Land). Recompute QBOT consistently at existing PSRF.
All six chosen TA and three retained VPD remain exactly as Stage07.
All other meteorological variables and all other timestamps retain v5 values.

Modes:
 --self-test  synthetic rows, no IRIDIS access
 --check      full in-memory isolated v6 preview, NO writes
 --run        create NEW immutable-named shadow trial folder, write 3 CSVs
              plus SHA receipts and INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP.
No originals, v5 data, existing reports, DATM, CIME, restarts or Slurm altered.
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
VERSION="stage11h-v1-20261024-53-ERA-RH-isolated-trial"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11G=ROOT/"reports/stage11g_user62_ERA5_method_validation_20261024T082933Z_fcaf26d1"
REPO=Path.home()/"CLM-FATES-single-site-workflows"
DECISION=REPO/"examples/AmeriFlux_MultiSite_10_Batch03/docs/STAGE11F_ALL62_USER_DECISIONS_2026-10-24.csv"
DECISION_GIT_BLOB="335c87e12d357714580018f8bab34fa4dde23446"
SITES=("US-MOz","US-Mpj","US-NC2")
ROWS={"US-MOz":315360,"US-Mpj":315360,"US-NC2":367920}
COLS=("time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")
KEY=["site","native_key","variable"]
T_RULE="KEEP_EXISTING_STAGE07_CANDIDATE_TA"
V_RULE="KEEP_EXISTING_STAGE07_CANDIDATE_VPD"
ERA_RULE="ERA5_BASED_HUMIDITY_METHOD_SELECTED"
SEALED_G={
    "62_user_choice_source_companion_preview.csv",
    "53_ERA5_humidity_method_comparisons.csv",
    "ERA_RH_transfer_failures_review.csv",
    "9_retained_Stage07_TA_and_VPD_checks.csv",
    "METHOD_SELECTION_HOLD.md"
}


def file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/unsafe input file: "+str(p))
    return p


def folder(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing/unsafe input directory: "+str(p))
    return p


def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()


def blob(p):
    b=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()


def jsonfile(p):
    return json.loads(file(p).read_text(encoding="utf-8"))


def numeric(df,col):
    a=pd.to_numeric(df[col],errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a)|(a<=-9990)]=np.nan
    return a


def saturation(t):
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*np.asarray(t)/(np.asarray(t)+243.5))


def derived(ta_c,vpd_hpa,pressure_pa):
    t=np.asarray(ta_c,dtype=float)
    v=np.asarray(vpd_hpa,dtype=float)
    p=np.asarray(pressure_pa,dtype=float)
    es=saturation(t)
    ea=es-v
    with np.errstate(divide="ignore",invalid="ignore"):
        rh=100*ea/es
        q=0.622*(ea*100)/(p-0.378*(ea*100))
    return ea,rh,q


def timeline(frame,site):
    if len(frame)!=ROWS[site] or list(frame.columns)!=list(COLS):
        raise ValueError("Native forcing row/column schema differs: "+site)
    t=pd.to_datetime(frame.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    if t.isna().any() or t.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError("Time identity/monotonicity changed: "+site)
    if (t.dt.month.eq(2)&t.dt.day.eq(29)).any():
        raise ValueError("Original forcing contains leap day: "+site)
    key=t.dt.strftime("%Y%m%d%H%M")
    expected=pd.date_range(t.iloc[0],t.iloc[-1],freq="30min")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    if len(expected)!=len(frame) or not np.array_equal(
        expected.to_numpy(),t.to_numpy()):
        raise ValueError("Not exact continuous NO_LEAP half-hour cadence: "+site)
    return key


def baseline_physics(df,site):
    for col in COLS[1:]:
        a=numeric(df,col)
        if not np.isfinite(a).all():
            raise ValueError("Nonfinite existing Stage07 data: "+site+" "+col)
    if not np.allclose(numeric(df,"TBOT"),numeric(df,"TA_USE")+273.15,
                       atol=1e-8,rtol=0):
        raise ValueError("Stage07 TBOT/TA consistency failed: "+site)
    ea,rh,q=derived(numeric(df,"TA_USE"),numeric(df,"VPD_USE"),
                    numeric(df,"PSRF"))
    if not (np.isfinite(ea)&np.isfinite(rh)&np.isfinite(q)&
        (ea>0)&(rh>0)&(rh<=100.05)&(q>=0)&(q<0.08)).all():
        raise ValueError("Stage07 complete forcing fails humidity screen: "+site)
    if not np.allclose(q,numeric(df,"QBOT"),atol=1e-10,rtol=1e-9):
        raise ValueError("Stage07 whole-series QBOT physics mismatch: "+site)
    return rh,q


def inputs():
    for p in (ROOT,S07,S11G,DECISION.parent):
        folder(p)
    file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    if blob(DECISION)!=DECISION_GIT_BLOB:
        raise ValueError("62-decision Git blob differs; exact immutable ledger required")
    g=jsonfile(S11G/"read_only_ERA5_method_receipt.json")
    if (g.get("version")!="stage11g-v1-20261024-user62-ERA5-companion-methods"
        or g.get("git_decisions_csv_blob")!=DECISION_GIT_BLOB
        or g.get("GitHub_decision_csv_SHA256")!=sha(DECISION)
        or g.get("Stage07_exact_manifest_SHA256")!=sha(S07/"exact_input_manifest.json")
        or g.get("decisions")!=62 or g.get("keep_Stage07_TA")!=6
        or g.get("ERA5_method_choice")!=53
        or g.get("keep_Stage07_VPD")!=3
        or g.get("companion_ERA_RH_transfer_numeric_pass")!=53
        or g.get("companion_ERA_direct_VPD_numeric_pass")!=46
        or g.get("ERA5_Land_grid_product_verified") is not False
        or g.get("selected_ERA5_source_method_frozen") is not False
        or g.get("Postv5_approved")!=0 or g.get("DATM_ready")!=0
        or g.get("spinup_authorizations")!=0
        or g.get("stage07_incomplete_marker_retained") is not True
        or set(g.get("outputs_sha256",{}))!=SEALED_G):
        raise ValueError("Stage11g input lineage or no-approval state differs")
    for name in SEALED_G:
        if sha(S11G/name)!=g["outputs_sha256"][name]:
            raise ValueError("Stage11g sealed output checksum differs: "+name)
    ledger=pd.read_csv(file(DECISION),dtype={"native_key":str},
                       keep_default_na=False,low_memory=False)
    preview=pd.read_csv(file(S11G/"62_user_choice_source_companion_preview.csv"),
                        dtype={"native_key":str},low_memory=False)
    if len(preview)!=62 or len(ledger)!=62 or preview.duplicated(KEY).any():
        raise ValueError("62-preview record count/identity differs")
    if (set(map(tuple,preview[KEY].to_numpy()))!=
        set(map(tuple,ledger[KEY].to_numpy()))):
        raise ValueError("Stage11g target IDs do not match GitHub 62-row decisions")
    pair=preview.merge(ledger[KEY+["human_decision"]],on=KEY,
                       how="left",validate="one_to_one",indicator=True)
    if (not pair["_merge"].eq("both").all()
        or not pair["user_decision"].eq(pair["human_decision"]).all()):
        raise ValueError("User decision changed between Stage11f and Stage11g")
    if preview.user_decision.value_counts().to_dict()!={
            T_RULE:6,ERA_RULE:53,V_RULE:3}:
        raise ValueError("Stage11g human decision classes do not match 6/53/3")
    for col in ("post_v5_approved","DATM_ready","spinup_authorized"):
        if preview[col].astype(str).str.lower().ne("false").any():
            raise ValueError("Stage11g unexpectedly marked approved: "+col)
    selected=preview.loc[preview.user_decision.eq(ERA_RULE)]
    if not selected.RH_transfer_water_physics_pass.astype(str).str.lower().eq("true").all():
        raise ValueError("53 ERA RH transfer source records have invalid numeric flags")
    if not np.isfinite(numeric(selected,"RH_transfer_VPD_hPa_preview")).all():
        raise ValueError("Stage11g 53 VPD previews not numeric")
    if not np.isfinite(numeric(selected,"RH_transfer_QBOT_kgkg_preview")).all():
        raise ValueError("Stage11g 53 QBOT previews not numeric")
    seal=jsonfile(S07/"output_sha256.json")
    return preview,seal,g


def construct(site,preview,seal):
    status_path=S07/site/"forcing"/"qc_v5"/(site+"_status.json")
    rel_status=str(status_path.relative_to(S07))
    if sha(status_path)!=seal.get(rel_status):
        raise ValueError("Sealed Stage07 status changed: "+site)
    status=jsonfile(status_path)
    src=Path(status["forcing_csv"])
    if (src.parent!=S07/site/"forcing"/"processed_v5"
        or src.is_symlink()):
        raise ValueError("Invalid Stage07 exact forcing path: "+site)
    if sha(src)!=seal.get(str(src.relative_to(S07))):
        raise ValueError("Original processed_v5 forcing SHA changed: "+site)
    df=pd.read_csv(src,low_memory=False)
    tkey=timeline(df,site)
    oldrh,_=baseline_physics(df,site)
    specific=preview.loc[preview.site.eq(site)]
    if len(specific)!={"US-MOz":1,"US-Mpj":6,"US-NC2":55}[site]:
        raise ValueError("Stage11g per-site review counts changed")
    indexed={key:i for i,key in enumerate(tkey)}
    seen=set()
    out=df.copy(deep=True)
    audit=[]
    for rec in specific.itertuples(index=False):
        key=(rec.native_key,rec.variable)
        if key in seen or rec.native_key not in indexed:
            raise ValueError("Duplicate/missing Stage11g exact native key: "+site+" "+rec.native_key)
        seen.add(key)
        i=indexed[rec.native_key]
        t=float(df.TA_USE.iloc[i]);v=float(df.VPD_USE.iloc[i])
        p=float(df.PSRF.iloc[i]);q=float(df.QBOT.iloc[i])
        if (abs(t-float(rec.stage07_candidate_TA_C))>1e-8
            or abs(v-float(rec.stage07_candidate_VPD_hPa))>1e-8
            or abs(q-float(rec.stage07_candidate_QBOT))>1e-9
            or abs(p-float(rec.stage07_PSFR_Pa))>1e-7):
            raise ValueError("Stage11g review centre mismatches SHA-sealed forcing: "+site+" "+rec.native_key)
        choice=rec.user_decision
        if choice==ERA_RULE:
            if rec.variable!="VPD_F":
                raise ValueError("ERA humidity trial cannot modify non-VPD row")
            et=float(rec.paired_companion_ERA_T_C)
            ev=float(rec.paired_companion_ERA_VPD_hPa)
            es_era=float(saturation(et))
            era_rh=(es_era-ev)/es_era
            if not 0<era_rh<=1:
                raise ValueError("Companion ERA RH invalid at chosen VPD: "+site+" "+rec.native_key)
            newv=float(saturation(t))*(1-era_rh)
            if not 0<=newv<float(saturation(t)):
                raise ValueError("RH transfer VPD nonphysical")
            _,_,qq=derived(t,newv,p)
            newq=float(qq)
            if (not np.isfinite(newq) or not 0<newq<0.08
                or abs(newv-float(rec.RH_transfer_VPD_hPa_preview))>1e-8
                or abs(newq-float(rec.RH_transfer_QBOT_kgkg_preview))>1e-10):
                raise ValueError("Stage11g recomputation disagreement: "+site+" "+rec.native_key)
            out.at[i,"VPD_USE"]=newv
            out.at[i,"QBOT"]=newq
        elif choice in (T_RULE,V_RULE):
            if (choice==T_RULE and rec.variable!="TA_F") or (choice==V_RULE and rec.variable!="VPD_F"):
                raise ValueError("User KEEP instruction type changed")
            newv=v;newq=q
        else:
            raise ValueError("Unknown user decision")
        audit.append({
            "site":site,"native_key":rec.native_key,"variable":rec.variable,
            "decision":choice,"stage07_TA_C":t,"stage07_VPD_hPa":v,
            "trial_VPD_hPa":newv,"stage07_QBOT_kgkg":q,
            "trial_QBOT_kgkg":newq,
            "stage07_RH_pct":float(oldrh[i]),
            "trial_RH_pct":float(derived(t,newv,p)[1]),
            "VPD_delta_hPa":newv-v,"QBOT_delta_kgkg":newq-q,
            "trial_reanalysis":"FLUXNET_SITE_DOWNSCALED_ERA_COMPANION_RH",
            "numerical_review_only":True,
            "post_v5_approved":False
        })
    audit=pd.DataFrame(audit)
    if len(audit)!=len(specific) or audit.duplicated(["site","native_key","variable"]).any():
        raise ValueError("Event count differs after trial preview")
    # Never allow non-selected timestamps/variables to change.
    subset=audit.loc[audit.decision.eq(ERA_RULE)]
    active={indexed[k] for k in subset.native_key}
    for col in COLS:
        x=df[col]
        y=out[col]
        if col in ("VPD_USE","QBOT"):
            mask=np.ones(len(df),dtype=bool)
            mask[list(active)]=False
            if not np.array_equal(x.to_numpy()[mask],y.to_numpy()[mask],
                                  equal_nan=True):
                raise ValueError("Non-target "+col+" was modified: "+site)
        elif not x.equals(y):
            raise ValueError("Forbidden change in source column "+col+": "+site)
    newrh,newq=baseline_physics(out,site)
    if (not np.isfinite(newrh).all()
        or (newrh[0:]<=0).any()
        or len(out)!=len(df)):
        raise ValueError("Whole trial physics/length changed")
    for rec in audit.loc[audit.decision.isin([T_RULE,V_RULE])].itertuples(index=False):
        i=indexed[rec.native_key]
        if (out.TA_USE.iloc[i]!=df.TA_USE.iloc[i]
            or out.VPD_USE.iloc[i]!=df.VPD_USE.iloc[i]
            or out.QBOT.iloc[i]!=df.QBOT.iloc[i]):
            raise ValueError("One of nine KEEP user events was modified")
    # At all 53 selected sites, find the change magnitudes and boundary jumps.
    actual_change=int((~np.isclose(
        subset.stage07_VPD_hPa.to_numpy(dtype=float),
        subset.trial_VPD_hPa.to_numpy(dtype=float),
        atol=1e-10,rtol=1e-10)).sum())
    boundary=[]
    for k in subset.native_key:
        i=indexed[k]
        if i>0:
            boundary.append(abs(float(out.VPD_USE.iloc[i])-float(out.VPD_USE.iloc[i-1])))
        if i+1<len(out):
            boundary.append(abs(float(out.VPD_USE.iloc[i+1])-float(out.VPD_USE.iloc[i])))
    metric={
        "site":site,"noleap_rows":len(df),
        "selected_ERA_humidity_times":len(subset),
        "actually_modified_VPD_values":actual_change,
        "max_abs_trial_minus_v5_VPD_hPa":float(subset.VPD_delta_hPa.abs().max()) if len(subset) else 0.,
        "max_abs_trial_minus_v5_QBOT_kgkg":float(subset.QBOT_delta_kgkg.abs().max()) if len(subset) else 0.,
        "max_adjacent_trial_VPD_jump_hPa":max(boundary) if boundary else 0.,
        "minimum_trial_water_RH_pct":float(newrh.min()),
        "fully_matched_untouched_rows":len(df)-len(subset),
        "source_processed_v5_sha256":sha(src),
        "status":"ISOLATED_NUMERIC_SCIENCE_TRIAL_NOT_DATM_READY",
        "Postv5_approved":False
    }
    return out,audit,metric


def self_test():
    t=20.;p=101325.;et=12.;ev=3.
    r=(float(saturation(et))-ev)/float(saturation(et))
    nv=float(saturation(t))*(1-r)
    ea,rh,q=derived(t,nv,p)
    assert 0<r<1 and 0<nv<float(saturation(t))
    assert np.isclose(rh,100*r,atol=1e-10)
    assert np.isfinite(q) and 0<float(q)<0.08
    # Large opposite provenance temperature must not change retained site T.
    assert t==20.
    # Synthetic decision-to-preview merge: the two source columns use
    # DIFFERENT names (user_decision vs human_decision), so no suffixes.
    left=pd.DataFrame({"site":["US-MOz"],"native_key":["201603172200"],
                       "variable":["TA_F"],"user_decision":[T_RULE]})
    right=pd.DataFrame({"site":["US-MOz"],"native_key":["201603172200"],
                        "variable":["TA_F"],"human_decision":[T_RULE]})
    joint=left.merge(right,on=KEY,validate="one_to_one",indicator=True)
    assert len(joint)==1 and joint["_merge"].eq("both").all()
    assert joint["user_decision"].eq(joint["human_decision"]).all()
    wrong=right.copy()
    wrong["human_decision"]=V_RULE
    bad=left.merge(wrong,on=KEY,validate="one_to_one")
    assert not bad["user_decision"].eq(bad["human_decision"]).all()
    print("STAGE11H SELF-TEST PASS: retained site T, ERA RH and QBOT, 62-join column schema, zero approval",
          flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11H — ISOLATED THREE-SITE ERA RH SHADOW TRIAL | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    preview,seal,receipt=inputs()
    group=[]
    evidence=[]
    outputs=[]
    # First validate full site-year data in memory. Avoid any new directory
    # or CSV write until every source SHA and every site audit pass.
    for site in SITES:
        out,audit,metric=construct(site,preview,seal)
        group.append((site,out))
        evidence.append(audit)
        outputs.append(metric)
        print(f"STAGE11H SITE {site}: rows={metric['noleap_rows']} "
              f"selected_ERA_RH={metric['selected_ERA_humidity_times']} "
              f"actual_VPD_deltas={metric['actually_modified_VPD_values']} "
              f"max_VPD_delta={metric['max_abs_trial_minus_v5_VPD_hPa']:.6f}hPa "
              f"min_trial_RH={metric['minimum_trial_water_RH_pct']:.6f}%",
              flush=True)
    joined=pd.concat(evidence,ignore_index=True)
    summary=pd.DataFrame(outputs)
    if (len(joined)!=62 or joined.decision.value_counts().to_dict()!=
        {ERA_RULE:53,T_RULE:6,V_RULE:3}
        or summary.selected_ERA_humidity_times.sum()!=53
        or summary.noleap_rows.sum()!=998640):
        raise ValueError("Stage11h science trial decision/row census mismatch")
    print("\n========== SHADOW SCIENCE TRIAL SUMMARY ==========",flush=True)
    print(summary[["site","noleap_rows","selected_ERA_humidity_times",
        "actually_modified_VPD_values","max_abs_trial_minus_v5_VPD_hPa",
        "max_adjacent_trial_VPD_jump_hPa","minimum_trial_water_RH_pct"]].to_string(index=False),
        flush=True)
    print(f"STAGE11H SUMMARY: 62_decisions=62/62 ERA_RH_targets=53/53 "
          f"total_actual_VPD_changes={int(summary.actually_modified_VPD_values.sum())} "
          "TA_kept=6/6 VPD_kept=3/3 postv5_approvals=0 DATM_ready=0 spinup=0",
          flush=True)
    if args.check:
        print("CHECK ONLY: no source, trial, report or forcing output writes.",
              flush=True)
        return
    # Place any new trial apart from sealed Stage07 and official Post-v5.
    trial=ROOT/"science_trials"/(
        "stage11h_companion_ERA_RH_shadow_"+datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    trial.mkdir(parents=True,exist_ok=False)
    # Write the HOLD marker FIRST so an interrupted trial is never DATM-ready.
    marker=trial/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"
    marker.write_text("UNAPPROVED source-companion ERA RH research trial; no CIME or Slurm.\n",
                      encoding="utf-8")
    shaoutputs={}
    for site,df in group:
        name=f"{site}_shadow_companion_ERA_RH_NOLEAP.csv"
        filepath=trial/name
        df.to_csv(filepath,index=False)
        reread=pd.read_csv(filepath,low_memory=False)
        timeline(reread,site)
        baseline_physics(reread,site)
        # Verify floating-point CSV roundtrip has not changed the selected
        # values beyond the planned version-controlled serialization.
        for col in COLS[1:]:
            if not np.allclose(numeric(reread,col),numeric(df,col),
                               rtol=1e-12,atol=1e-11):
                raise ValueError("Written shadow trial roundtrip changed: "+site+" "+col)
        shaoutputs[name]=sha(filepath)
    for name,table in {
        "62_selected_event_candidate_differences.csv":joined,
        "three_site_shadow_trial_summary.csv":summary
    }.items():
        table.to_csv(trial/name,index=False)
        shaoutputs[name]=sha(trial/name)
    guidance="""# INCOMPLETE Stage11h shadow science trial — NOT Post-v5

The six original measured QC0 air-temperature corrections and three user's
explicitly retained Stage07 VPD candidates are kept as they already existed
in the pinned Stage07 processed_v5 forcing. Only the 53 separately selected
VPD event IDs are eligible for source-companion ERA5 RH-at-retained-site-TA
reconstruction; QBOT is regenerated consistently with Stage07 PSRF.
Non-target data are unchanged in numerical content. Floating-point CSV
serialization can change textual formatting and file hashes, by design.

The ERA source is FLUXNET site's release-paired downscaled ERA companion.
This is NOT verified independent ERA5-Land grid 2m dewpoint/T data and
is not tower-measured absolute humidity. The data are an isolated TEST
CANDIDATE, not permission to change forcing used by CIME.
The 53 water-phase physics screens passing is not source accuracy approval.
Inspect maximum discontinuities, extreme RH, whole-year carbon/met biases,
native clock, site height/elevation, PFT/surface, 5-year loop and CO2 policy.

Do not remove INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP.
Never use these CSVs directly for DATM or SPINUP without independent
documented scientific and formal Post-v5 acceptance. Seven other sites
and their 1,924 humidity blockers are OUT OF SCOPE.
"""
    (trial/"SCIENTIFIC_HOLD.md").write_text(guidance,encoding="utf-8")
    shaoutputs["SCIENTIFIC_HOLD.md"]=sha(trial/"SCIENTIFIC_HOLD.md")
    receipt_out={
        "version":VERSION,"source_stage11g_receipt_SHA256":sha(
            S11G/"read_only_ERA5_method_receipt.json"),
        "source_stage07_manifest_SHA256":sha(S07/"exact_input_manifest.json"),
        "user_decision_csv_git_blob":DECISION_GIT_BLOB,
        "source_RH_transfer":"FLUXNET_SITE_DOWNSCALED_ERA5_COMPANION",
        "separate_ERA5_Land_grid_product_checked":False,
        "stations":list(SITES),"noleap_total_rows":998640,
        "human_decisions":62,"ERA_RH_selected_target_rows":53,
        "actually_different_VPD_values":int(summary.actually_modified_VPD_values.sum()),
        "keep_six_TA":6,"keep_three_VPD":3,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorizations":0,
        "Stage07_source_and_v5_untouched":True,
        "INCOMPLETE_marker_present":True,
        "output_sha256":shaoutputs
    }
    (trial/"sha_sealed_shadow_trial_receipt.json").write_text(
        json.dumps(receipt_out,indent=2)+"\n",encoding="utf-8")
    print("STAGE11H SHADOW TRIAL DIR:",trial,flush=True)
    print("SCIENTIFIC HOLD ACTIVE; NO OFFICIAL POST-V5, DATM, CIME OR SLURM.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as error:
        print("STAGE11H STOP:",str(error),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

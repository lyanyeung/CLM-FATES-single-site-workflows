#!/usr/bin/env python3
"""Stage11l: isolated US-NC2 humidity-only 11-event successor to Stage11h.

Sources are SHA-pinned Stage11k-v2 (the 11 never-repaired native neighbours),
Stage11h (entire old three-site trial), Stage11j (original/ERA provenance),
and the new 11-event GitHub user decision CSV. Only the 11 source-native
US-NC2 VPD_USE/QBOT entries may change, reconstructing companion ERA RH
at the PRESERVED EC-tower Stage11h air temperature and original PSRF.
TA_USE, TBOT and every other variable remain unchanged at all times.

--self-test: synthetic thermodynamic test, no input and no writes
--check: full in-memory SHA/physical/edge audit, NO output files
--run: create a NEW research-only Stage11l trial with ONE US-NC2 successor
       forcing and event/boundary evidence. Old US-MOz and US-Mpj remain
       referenced by original SHA. Not a Post-v5 release, DATM or spinup.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11l-v1-20261024-11-humidity-only-successor"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
SCRIPTS=BASE/"scripts/stage11"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
J=ROOT/"reports/stage11j_four_jump_original_ERA_context_20261024T092017Z_5fc4bfd6"
K=SCRIPTS/"11k_v2_four_event_unrepaired_neighbour_RH_review.py"
K_BLOB="9939d5e62a1c1fd732d080698d7e026a1af010a0"
SCRIPT_H=SCRIPTS/"11h_isolated_ERA_RH_three_site_science_trial.py"
H_BLOB="de8f6fade16ead3bf3dc6d5fecc5010a5b1c4750"
LEDGER=BASE/"docs/STAGE11L_USER_APPROVED_11_US_NC2_NEIGHBOUR_RH_ADDITIONS_2026-10-24.csv"
LEDGER_BLOB="53912c25c5da32347e46739dd6ebf11036664683"
OLD_LEDGER_BLOB="335c87e12d357714580018f8bab34fa4dde23446"
COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
SITES=("US-MOz","US-Mpj","US-NC2")
FILENAME=lambda site:f"{site}_shadow_companion_ERA_RH_NOLEAP.csv"
TARGETS={
    "202503181830","202503181930",
    "202503231300","202503231330","202503231400","202503231430","202503231500",
    "202503250800","202503250830","202503250930","202503251000"
}
EPISODES=(
    ("MAR18","202503181830","202503181930"),
    ("MAR23","202503230900","202503231500"),
    ("MAR25","202503250800","202503251030")
)

def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink input: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def blob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def load_module(p,expected,name):
    if blob(p)!=expected:
        raise ValueError("Pinned verified Python source differs: "+str(p))
    spec=importlib.util.spec_from_file_location(name,p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def es(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def derived(t,v,p):
    ea=es(t)-np.asarray(v,dtype=float)
    pressure=np.asarray(p,dtype=float)
    with np.errstate(divide="ignore",invalid="ignore"):
        rh=100*ea/es(t)
        q=0.622*ea*100/(pressure-0.378*ea*100)
    return rh,q

def transfer(ta,psrf,te,ve):
    sat=float(es(te))
    rh_era=(sat-float(ve))/sat
    if not np.isfinite(rh_era) or not 0<rh_era<=1:
        raise ValueError("Invalid ERA source RH; no clipping permitted")
    v_new=float(es(ta))*(1-rh_era)
    rh_new,q_new=derived(float(ta),v_new,float(psrf))
    rh_new,q_new=float(rh_new),float(q_new)
    if not np.isfinite([v_new,rh_new,q_new]).all() or not (
        0<=v_new<float(es(ta)) and 0<rh_new<=100 and
        0<q_new<0.08 and 49000<=psrf<=111000):
        raise ValueError("Humidity/QBOT physics failed at retained tower TA")
    return v_new,q_new,rh_new,100*rh_era

def self_test():
    v,q,rh,era=transfer(20.,101325.,10.,4.)
    assert 0<v<float(es(20)) and 0<q<.08 and abs(rh-era)<1e-9
    try:
        transfer(10.,101325.,10.,100.)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid source humidity was not rejected")
    assert len(TARGETS)==11 and sum(k.startswith("20250318") for k in TARGETS)==2
    assert sum(k.startswith("20250323") for k in TARGETS)==5
    assert sum(k.startswith("20250325") for k in TARGETS)==4
    print("STAGE11L SELF-TEST PASS: unchanged EC temperature, ERA RH/QBOT, 2+5+4 targets, NO WRITES",flush=True)

def verify_and_load():
    for p in (ROOT,S07,H,J,BASE):
        if not p.is_dir() or p.is_symlink():
            raise ValueError("Missing/symlink source directory: "+str(p))
    regular(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    regular(H/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    if blob(LEDGER)!=LEDGER_BLOB:
        raise ValueError("New 11-user-choice SHA Git blob mismatch")
    # Import audited, already executed source routines rather than deriving
    # a second and potentially inconsistent Stage11j review classification.
    k=load_module(K,K_BLOB,"stage11k_v2_pinned_for_stage11l")
    hmod=load_module(SCRIPT_H,H_BLOB,"stage11h_pinned_for_stage11l")
    hmod.inputs()  # SHA checks Stage07/11g and old human 62-decision IDs.
    context,kseal=k.source_data()
    context_all,untouched,stage07_only,stage11h_other,centres=k.evaluate(context)
    if (len(untouched)!=11 or len(stage07_only)!=3 or
        len(stage11h_other)!=7 or len(centres)!=4):
        raise ValueError("Prior verified Stage11k-v2 11/3/7/4 classification changed")
    ledger=pd.read_csv(LEDGER,dtype={"native_key":str},keep_default_na=False)
    if (len(ledger)!=11 or ledger.native_key.duplicated().any() or
        set(ledger.native_key)!=TARGETS or ledger.site.ne("US-NC2").any() or
        ledger.variable.ne("VPD_F").any() or
        ledger.human_decision.ne("APPROVE_STAGE11L_ISOLATED_SHADOW_RH_TRANSFER").any()):
        raise ValueError("Exact new 11 human choices do not match reviewed source-native target IDs")
    if not ledger.post_v5_approved.astype(str).str.lower().eq("false").all():
        raise ValueError("User choices must not approve Post-v5")
    if not ledger.DATM_ready.astype(str).str.lower().eq("false").all():
        raise ValueError("User choices must not approve DATM")
    if not ledger.spinup_authorized.astype(str).str.lower().eq("false").all():
        raise ValueError("User choices must not approve spinup")
    if set(zip(untouched.centre_site,untouched.native_key))!={
        ("US-NC2",x) for x in TARGETS}:
        raise ValueError("Eleven new user selections are not exactly original-unmodified records")
    hreceipt=json.loads(regular(H/"sha_sealed_shadow_trial_receipt.json").read_text())
    if (hreceipt.get("version")!="stage11h-v1-20261024-53-ERA-RH-isolated-trial"
        or hreceipt.get("user_decision_csv_git_blob")!=OLD_LEDGER_BLOB
        or hreceipt.get("human_decisions")!=62
        or hreceipt.get("ERA_RH_selected_target_rows")!=53
        or hreceipt.get("actually_different_VPD_values")!=43
        or hreceipt.get("Postv5_approved")!=0
        or hreceipt.get("DATM_ready")!=0
        or hreceipt.get("spinup_authorizations")!=0
        or hreceipt.get("INCOMPLETE_marker_present") is not True):
        raise ValueError("Stage11h 62-event sealed-source gate differs")
    for s in SITES:
        if sha(H/FILENAME(s))!=hreceipt["output_sha256"][FILENAME(s)]:
            raise ValueError("A sealed original Stage11h source site CSV changed: "+s)
    # Stage11k source_data above SHA-verifies Stage11j input and trial receipts.
    return ledger,untouched.set_index("native_key",verify_integrity=True),hreceipt,hmod

def compute(ledger,raw,hreceipt,hmod):
    old=pd.read_csv(regular(H/FILENAME("US-NC2")),low_memory=False)
    if len(old)!=367920 or list(old.columns)!=COLS:
        raise ValueError("Stage11h US-NC2 file row/schema mismatch")
    keys=hmod.timeline(old,"US-NC2")
    oldrh,_=hmod.baseline_physics(old,"US-NC2")
    index={t:i for i,t in enumerate(keys)}
    new=old.copy(deep=True)
    rows=[]
    for r in ledger.sort_values("native_key").itertuples(index=False):
        key=r.native_key
        if key not in index or key not in raw.index:
            raise ValueError("Requested source-native timestamp missing: "+key)
        i=index[key]
        c=raw.loc[key]
        # Verify both raw provenance and method chosen by researcher.
        rhorig=float(c.science_original_source_water_RH_pct)
        rhera=float(c.science_companion_ERA_water_RH_pct)
        if (not 0<=rhorig<10 or not rhera>=20 or
            rhera-rhorig<20 or int(c.original_VPD_F_QC) not in (1,2) or
            not bool(c.review_proposed_source_original_unchanged) or
            abs(rhorig-float(r.original_RH_water_pct))>1e-5 or
            abs(rhera-float(r.companion_ERA_RH_water_pct))>1e-5 or
            abs(float(c.original_VPD_F_hPa)-float(old.VPD_USE.iloc[i]))>1e-7):
            raise ValueError("New source candidate QC, source RH or data-frozen old VPD differ: "+key)
        ta=float(old.TA_USE.iloc[i]);p=float(old.PSRF.iloc[i])
        vnew,qnew,rhnew,era_rh=transfer(ta,p,float(c.companion_ERA_T_C),
                                       float(c.companion_ERA_VPD_hPa))
        if abs(era_rh-rhera)>1e-6:
            raise ValueError("Companion ERA T/VPD derived RH fails provenance: "+key)
        new.at[i,"VPD_USE"]=vnew
        new.at[i,"QBOT"]=qnew
        rows.append({"site":"US-NC2","native_key":key,
            "original_QC":int(c.original_VPD_F_QC),
            "original_RH_water_pct":rhorig,
            "companion_ERA_RH_water_pct":rhera,
            "retained_EC_tower_TA_C":ta,
            "old_Stage11h_VPD_hPa":float(old.VPD_USE.iloc[i]),
            "new_Stage11l_VPD_hPa":vnew,
            "old_Stage11h_QBOT":float(old.QBOT.iloc[i]),
            "new_Stage11l_QBOT":qnew,
            "new_Stage11l_RH_pct":rhnew,
            "VPD_delta_hPa":vnew-float(old.VPD_USE.iloc[i]),
            "human_method_selected":True,"Postv5_approved":False})
    # No EC tower temperature substitution, ever.
    mask=np.ones(len(old),dtype=bool)
    mask[[index[k] for k in TARGETS]]=False
    for col in COLS:
        if col in ("VPD_USE","QBOT"):
            if not np.array_equal(old[col].to_numpy()[mask],
                                  new[col].to_numpy()[mask],equal_nan=True):
                raise ValueError("Off-target "+col+" changed")
        elif not old[col].equals(new[col]):
            raise ValueError("Forbidden changed EC T, pressure, radiation, wind or precipitation: "+col)
    rhnew,_=hmod.baseline_physics(new,"US-NC2")
    changes=pd.DataFrame(rows)
    if len(changes)!=11 or changes.native_key.duplicated().any():
        raise ValueError("Eleven user targets were not applied exactly once")
    a=old.VPD_USE.to_numpy(dtype=float); b=new.VPD_USE.to_numpy(dtype=float)
    delta_rows=int(np.sum(~np.isclose(changes.old_Stage11h_VPD_hPa,
                                      changes.new_Stage11l_VPD_hPa,
                                      rtol=1e-10,atol=1e-10)))
    neighbours=[]
    for key in sorted(TARGETS):
        i=index[key]
        lo,ln=abs(a[i]-a[i-1]),abs(b[i]-b[i-1])
        ro,rn=abs(a[i+1]-a[i]),abs(b[i+1]-b[i])
        neighbours.append({"site":"US-NC2","native_key":key,
            "old_prev_jump_hPa":lo,"new_prev_jump_hPa":ln,
            "added_prev_jump_hPa":ln-lo,
            "old_next_jump_hPa":ro,"new_next_jump_hPa":rn,
            "added_next_jump_hPa":rn-ro,
            "max_added_adjacent_jump_hPa":max(ln-lo,rn-ro)})
    edges=[]
    for label,start,end in EPISODES:
        for side,left,right in (("BEFORE",index[start]-1,index[start]),
                                ("AFTER",index[end],index[end]+1)):
            lo,ln=abs(a[right]-a[left]),abs(b[right]-b[left])
            edges.append({"site":"US-NC2","event":label,"boundary":side,
                "left_key":keys[left],"right_key":keys[right],
                "old_abs_jump_hPa":lo,"new_abs_jump_hPa":ln,
                "ADDED_abs_jump_hPa":ln-lo,
                "added_over_2hPa":bool(ln-lo>2),
                "new_total_over_5hPa":bool(ln>5)})
    edges=pd.DataFrame(edges)
    if len(edges)!=6:
        raise ValueError("Missing three-event before/after edge comparisons")
    years=np.asarray([int(x[:4]) for x in keys])
    impacts=[]
    for year in sorted(np.unique(years)):
        m=years==year
        impacts.append({"year":int(year),"half_hours":int(m.sum()),
            "new_11_selected_events":sum(key.startswith(str(year)) for key in TARGETS),
            "yearly_mean_VPD_change_hPa":float((b[m]-a[m]).mean()),
            "yearly_mean_RH_change_percentage_points":float((rhnew[m]-oldrh[m]).mean()),
            "yearly_mean_QBOT_change_kgkg":float(
                (new.QBOT.to_numpy(dtype=float)[m]-old.QBOT.to_numpy(dtype=float)[m]).mean())})
    return new,changes,pd.DataFrame(neighbours),edges,pd.DataFrame(impacts),delta_rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    args=p.add_mutually_exclusive_group(required=True)
    args.add_argument("--self-test",action="store_true")
    args.add_argument("--check",action="store_true")
    args.add_argument("--run",action="store_true")
    run=p.parse_args()
    print("STAGE11L — 11 HUMAN-SELECTED US-NC2 RH EVENTS; EC TOWER TA HELD FIXED | "+VERSION,flush=True)
    self_test()
    if run.self_test:
        return
    ledger,source,hreceipt,hmod=verify_and_load()
    trial,details,neighbours,edges,annual,modified=compute(ledger,source,hreceipt,hmod)
    print("\n========== ELEVEN NEW ERA RH CANDIDATES; TOWER T UNCHANGED ==========",flush=True)
    print(details[["native_key","original_QC","original_RH_water_pct",
         "companion_ERA_RH_water_pct","retained_EC_tower_TA_C",
         "old_Stage11h_VPD_hPa","new_Stage11l_VPD_hPa"]].to_string(index=False),flush=True)
    print("\n========== SIX EVENT-OUTER BOUNDARY COMPARISONS ==========",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("\n========== ALL 11 TARGET NEW NEIGHBOUR JUMPS ==========",flush=True)
    print(neighbours.sort_values("max_added_adjacent_jump_hPa",
       ascending=False).to_string(index=False),flush=True)
    print("\n========== YEARLY IMPACT ==========",flush=True)
    print(annual.loc[annual.new_11_selected_events.gt(0)].to_string(index=False),flush=True)
    print(f"\nSTAGE11L SUMMARY: user_old=62/62 old_ERA_target=53/53 "
          f"new_ERA_target=11/11 cumulative_ERA_targets=64 "
          f"newly_changed_VPD={modified}/11 "
          "tower_TA_TBOT_unchanged=True Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if run.check:
        print("CHECK ONLY: no new trial/report files or model changes.",flush=True)
        return
    out=ROOT/"science_trials"/("stage11l_US-NC2_humidity_only_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Unapproved humidity-only science trial. No DATM, CIME or Slurm.\n")
    reports={
      "US-NC2_humidity_only_new_shadow_NOLEAP.csv":trial,
      "11_new_user_RH_event_differences.csv":details,
      "11_new_target_adjacent_jump_changes.csv":neighbours,
      "6_old_vs_new_event_outer_boundaries.csv":edges,
      "US-NC2_yearly_impact.csv":annual}
    output_hash={}
    for name,frame in reports.items():
        frame.to_csv(out/name,index=False)
        output_hash[name]=sha(out/name)
    readback=pd.read_csv(out/"US-NC2_humidity_only_new_shadow_NOLEAP.csv",
                         low_memory=False)
    hmod.timeline(readback,"US-NC2")
    hmod.baseline_physics(readback,"US-NC2")
    for c in COLS:
        if c=="time":
            good=readback[c].equals(trial[c])
        else:
            good=np.allclose(readback[c].to_numpy(dtype=float),
              trial[c].to_numpy(dtype=float),rtol=1e-12,atol=1e-11)
        if not good:
            raise ValueError("Serialized shadow roundtrip modified "+c)
    unchanged={s:{"file":str(H/FILENAME(s)),
      "SHA256":hreceipt["output_sha256"][FILENAME(s)]}
      for s in ("US-MOz","US-Mpj")}
    (out/"two_unchanged_Stage11h_site_SHA_refs.json").write_text(
        json.dumps(unchanged,indent=2)+"\n")
    output_hash["two_unchanged_Stage11h_site_SHA_refs.json"]=sha(
        out/"two_unchanged_Stage11h_site_SHA_refs.json")
    notes="""# STAGE11L IS AN UNAPPROVED SCIENCE SHADOW
Only US-NC2 new successor forcing was generated. Original Stage07 and
Stage11h remain SHA-locked and unchanged. Other two sites remain Stage11h
and are referenced by SHA in this folder (not copied or re-run).
EC tower TA_USE and TBOT were not changed at ANY half hour.
Companion ERA temperature was used ONLY to derive companion ERA RH;
no ERA temperature substituted into the EC tower temperature series.
Only 11 human-selected VPD_USE/QBOT events were eligible for writes.
New total candidate mask 53 old + 11 new = 64 source-native timestamps.
Both event start/end boundaries and each modified halfhour are documented.
No Post-v5, DATM, CIME or spinup authorisation; keep INCOMPLETE markers.
"""
    (out/"SCIENTIFIC_HOLD.md").write_text(notes)
    output_hash["SCIENTIFIC_HOLD.md"]=sha(out/"SCIENTIFIC_HOLD.md")
    receipt={
      "version":VERSION,"new_user_11_Git_blob":LEDGER_BLOB,
      "Stage11h_source_receipt_SHA256":sha(H/"sha_sealed_shadow_trial_receipt.json"),
      "Stage11j_source_receipt_SHA256":sha(J/"read_only_four_event_receipt.json"),
      "added_neighbour_events":11,"newly_different_VPD":modified,
      "cumulative_old_ERA_RH_target_count":53,"combined_ERA_RH_target_count":64,
      "noleap_US_NC2_rows":367920,"reviewed_episode_outer_boundaries":6,
      "retained_EC_tower_TA_and_TBOT":True,
      "other_two_site_files_unchanged":True,
      "new_Source_ERA_method":"source_companion_ERA_RH_at_retained_Stage11h_EC_TA",
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "INCOMPLETE_marker_present":True,"output_sha256":output_hash}
    (out/"stage11l_scientific_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE11L ISOLATED TRIAL DIR:",out,flush=True)
    print("NO original Stage07/Stage11h data or model jobs altered.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE11L STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

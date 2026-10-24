#!/usr/bin/env python3
"""Stage12b: bulk six-site numeric ERA5-Land RH patch candidates from 1,924 blockers.

Create 1687 source-native event-level research repair patches for six
Batch03 sites without repeated manual per-event checks. Only the no-clock,
no-ice, no-temperature-conflict, evidence-insufficient group is considered
for numeric humidity-only method B: grid RH at unchanged original
site air temperature and original pressure. All Stage10b site/year ERA
times are PROVISIONAL; no clock correction is adopted or implied.

Automatically separate and HOLD 233 temperature/ice/absolute-water
physics conflicts and 4 US-Me2 source clock cases. No source, existing
Stage07/11h/11l/11q forcing, DATM, CIME or Slurm case modified.

--self-test synthetic formula and row partition, NO disk reads/writes
--check source SHA and 1924 complete event+provenance, compute 1687
        research-only numeric patch candidates IN MEMORY, NO files
--run same checks then ONE NEW science_trials/stage12b_* folder with
      incomplete marker, six-site numeric event patch ledger, holds,
      summary and SHA receipts. These are event-level patches,
      NOT complete NO_LEAP site forcing and NOT model-ready.

No human scientific Post-v5 approval is inferred from a pass.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage12b-v1-20261024-six-site-bulk-humidity-numeric-patch"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
SOURCE=BASE/"scripts/stage11/11a_science_decision_matrix.py"
SOURCE_BLOB="a83de59a907179429c1747977c1043ae01f9a7cf"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S12A=ROOT/"reports/stage12a_batch03_post11q_ten_site_status_20261024T114422Z_73dd434c"
KEYS=["site","source_csv_row","time"]
BLOCKED={"US-NR3":1484,"US-Kon":229,"US-NR1":173,
         "US-MMS":18,"US-MtB":15,"US-Me6":1,"US-Me2":4}
SIX=set(BLOCKED)-{"US-Me2"}
EXPECTED_ROUTING={"EVIDENCE_INSUFFICIENT_HOLD":1687,
                  "PHYSICS_CONFLICT_HOLD":233,"CLOCK_METADATA_HOLD":4}
STAGE12A_FILES={"10_site_post_stage11q_status.csv",
 "7_blocked_sites_ranked_priorities.csv",
 "32_original_source_site_year_hold_counts.csv",
 "status_and_next_work.json","SCIENTIFIC_HOLD.md"}

def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink original evidence file: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def blob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def get_stage11a():
    if blob(SOURCE)!=SOURCE_BLOB:
        raise ValueError("Stage11a original proven source Git blob mismatch")
    spec=importlib.util.spec_from_file_location("batch03_stage11a_pin_12b",SOURCE)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def es_water(temp):
    t=np.asarray(temp,dtype=float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def q_from_RH(temp,pressure_pa,rh_pct):
    vapour_pa=100*es_water(temp)*(np.asarray(rh_pct,dtype=float)/100.)
    p=np.asarray(pressure_pa,dtype=float)
    with np.errstate(divide="ignore",invalid="ignore"):
        return .622*vapour_pa/(p-.378*vapour_pa)

def floatvals(d,col):
    if col not in d:
        raise ValueError("Original Stage10d evidence lacks "+col)
    v=pd.to_numeric(d[col],errors="coerce").to_numpy(dtype=float)
    v[(~np.isfinite(v)) | (v<=-9990)]=np.nan
    return v

def boolvals(d,col):
    if col not in d:
        raise ValueError("Original Stage10d flag absent: "+col)
    x=d[col].astype(str).str.strip().str.lower()
    if not x.isin(["true","false","0","1"]).all():
        raise ValueError("Original Stage10d flag malformed: "+col)
    return x.isin(["true","1"]).to_numpy(dtype=bool)

def preflight():
    if not S12A.is_dir() or S12A.is_symlink():
        raise ValueError("Stage12a verified ten-site report missing")
    rec=json.loads(regular(S12A/"stage12a_science_hold_receipt.json").read_text())
    if (rec.get("version")!="batch03-stage12a-v1-20261024-three-science-shadows-seven-blocked"
        or rec.get("batch_sites")!=10
        or rec.get("blocked_original_sites")!=7
        or rec.get("original_unresolved_records")!=1924
        or rec.get("existing_science_shadows")!=3
        or rec.get("postv5_approved")!=0
        or rec.get("DATM_ready")!=0
        or rec.get("spinup_authorized")!=0
        or set(rec.get("output_sha256",{}))!=STAGE12A_FILES):
        raise ValueError("Stage12a verified seven-site checkpoint receipt altered")
    for name,expect in rec["output_sha256"].items():
        if sha(S12A/name)!=expect:
            raise ValueError("Stage12a original evidence SHA mismatch: "+name)
    regular(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    a=get_stage11a()
    source,observed,alternative,prior=a.preflight() # Full original SHA verification
    events,years,batch=a.analyze(source,observed,alternative)
    if (len(events)!=1924 or len(years)!=32 or len(batch)!=10
        or events.review_route.value_counts().to_dict()!=EXPECTED_ROUTING
        or events.site.value_counts().to_dict()!=BLOCKED
        or set(map(tuple,source[KEYS].to_numpy()))!=
           set(map(tuple,events[KEYS].to_numpy()))):
        raise ValueError("Original 1924 event list or science route differs")
    if rec.get("inputs_SHA256",{}).get("Stage11a_script_Git_blob")!=SOURCE_BLOB:
        raise ValueError("Stage12a prior Stage11a source blob differs")
    return source,events,prior,rec

def compute(d,events):
    extra=KEYS+[
        "TA_before_fallback_C","PA_before_fallback_kPa",
        "VPD_before_fallback_hPa",
        "relative_vpd_at_tower_T_hPa",
        "relative_qbot_at_tower_P_kgkg",
        "relative_rh_at_tower_T_pct",
        "grid_temperature_C","grid_dewpoint_C",
        "clock_offset_hours_hypothesis","native_minutes",
        "utc_midpoint_hypothesis","external_sha256",
        "grid_relative_humidity_pct"
    ]
    if not set(extra)<=set(d):
        raise ValueError("Required proven Stage10b/Stage10d RH input missing: "+str(set(extra)-set(d)))
    merged=events[KEYS+["review_route","VPD_origin","TA_origin",
                        "review_priority","event_cluster_id",
                        "A_ice_phase_caution","B_ice_phase_caution",
                        "grid_temperature_caution"]].merge(d[extra],
                              on=KEYS,how="inner",validate="one_to_one")
    if len(merged)!=1924 or merged.duplicated(KEYS).any():
        raise ValueError("Original source identity changed on join")
    m=merged.review_route.eq("EVIDENCE_INSUFFICIENT_HOLD").to_numpy()
    clock=merged.review_route.eq("CLOCK_METADATA_HOLD").to_numpy()
    conflict=merged.review_route.eq("PHYSICS_CONFLICT_HOLD").to_numpy()
    if (m.sum()!=1687 or conflict.sum()!=233 or clock.sum()!=4
        or not merged.loc[m,"site"].isin(SIX).all()
        or not merged.loc[clock,"site"].eq("US-Me2").all()
        or not merged.VPD_origin.isin(["QC1_GAPFILLED","QC2_DOWNSCALED_ERA"]).all()):
        raise ValueError("Unambiguous original 1687/233/4 sources unexpectedly changed")
    temp=floatvals(merged,"TA_before_fallback_C")
    press=floatvals(merged,"PA_before_fallback_kPa")*1000
    rh=floatvals(merged,"relative_rh_at_tower_T_pct")
    grh=floatvals(merged,"grid_relative_humidity_pct")
    old=floatvals(merged,"VPD_before_fallback_hPa")
    candidate_v=floatvals(merged,"relative_vpd_at_tower_T_hPa")
    candidate_q=floatvals(merged,"relative_qbot_at_tower_P_kgkg")
    gridtemp=floatvals(merged,"grid_temperature_C")
    es=es_water(temp)
    vcalc=es*(1-rh/100.)
    qcalc=q_from_RH(temp,press,rh)
    selected=np.flatnonzero(m)
    selected_good=np.isfinite(np.stack([
          temp[selected],press[selected],rh[selected],grh[selected],
          candidate_v[selected],candidate_q[selected],gridtemp[selected],
          vcalc[selected],qcalc[selected]],axis=1)).all(axis=1)
    selected_good&=(
        (temp[selected]>=-80)&(temp[selected]<=65)&
        (press[selected]>=50000)&(press[selected]<=110000)&
        (rh[selected]>0)&(rh[selected]<=100)&
        (np.abs(rh[selected]-grh[selected])<1e-6)&
        (candidate_v[selected]>=0)&(candidate_v[selected]<=125)&
        (candidate_q[selected]>0)&(candidate_q[selected]<.08)&
        (np.abs(temp[selected]-gridtemp[selected])<=5)&
        np.isclose(candidate_v[selected],vcalc[selected],
                   rtol=1e-7,atol=1e-7)&
        np.isclose(candidate_q[selected],qcalc[selected],
                   rtol=1e-7,atol=1e-9))
    valid=np.zeros(len(merged),dtype=bool);valid[selected]=selected_good
    # Fail closed on uncommon source numeric disagreement: preserve instead
    # of silently overriding existing original forcing.
    selected_off=np.zeros(len(merged),dtype=bool);selected_off[selected]=~selected_good
    selected_off_count=int(selected_off.sum())
    if selected_off_count:
        print("PHYSICS_GUARD_HOLDS (subset of 1687):",selected_off_count,flush=True)

    # Avoid false scientific source clock approval: all 7 sites' ERA5-Land
    # native-midpoint offsets here are the ORIGINAL Stage10b hypotheses.
    candidate=merged.loc[valid].copy()
    candidate["exact_source_native_timestamp"]=pd.to_datetime(
        candidate.time,errors="raise").dt.strftime("%Y%m%d%H%M")
    candidate["EC_tower_TA_C_preserved"]=temp[valid]
    candidate["EC_tower_PSRF_Pa_preserved"]=press[valid]
    candidate["original_source_VPD_hPa"]=old[valid]
    candidate["research_ERA5Land_grid_RH_pct"]=rh[valid]
    candidate["humidity_only_candidate_VPD_hPa"]=candidate_v[valid]
    candidate["humidity_only_candidate_QBOT_kgkg"]=candidate_q[valid]
    candidate["model_air_temperature_modification"]=False
    candidate["assumed_UTC_offset_approved"]=False
    candidate["humidity_method"]="ERA5LAND_GRID_RH_TRANSFER_AT_ORIGINAL_TOWER_T_AND_P"
    candidate["patch_status"]="AUTO_NUMERIC_RESEARCH_CANDIDATE_NO_FORCING_WRITE"
    candidate["post_v5_approved"]=False
    candidate["DATM_ready"]=False
    candidate["spinup_authorized"]=False
    candidate=candidate.sort_values(KEYS).reset_index(drop=True)
    if candidate.duplicated(["site","exact_source_native_timestamp"]).any():
        raise ValueError("Candidate native timestamps duplicate: cannot patch reliably")
    if not candidate.native_minutes.astype(int).isin([30,60]).all():
        raise ValueError("Unexpected original site native time interval")

    hold=merged.loc[~valid].copy()
    hold["reason"]=np.select(
        [clock[~valid],selected_off[~valid],conflict[~valid]],
        ["MISSING_VERIFIED_US_ME2_RELEASE_CLOCK",
         "SOURCE_GRID_RELATIVE_HUMIDITY_NUMERIC_INCONSISTENCY",
         "TOWER_GRID_TEMPERATURE_OR_ICE_OR_SOURCE_WATER_PHYSICS_CONFLICT"],
        default="ORIGINAL_SCIENTIFIC_HOLD")
    hold["original_source_TA_C"]=temp[~valid]
    hold["original_source_pressure_Pa"]=press[~valid]
    hold["original_source_VPD_hPa"]=old[~valid]
    hold["unapproved_grid_RH_pct"]=rh[~valid]
    hold["unapproved_grid_RH_candidate_VPD_hPa"]=candidate_v[~valid]
    hold["human_science_review_required"]=True
    hold["forbidden_to_auto_modify_forcing"]=True
    hold=hold.sort_values(KEYS).reset_index(drop=True)
    if len(candidate)+len(hold)!=1924 or len(hold)!=237+selected_off_count:
        raise ValueError("Candidate/hold partition missed or duplicated source rows")
    if candidate.site.nunique()>6 or hold.site.nunique()>7:
        raise ValueError("Expected six or fewer candidate sites only")

    result=[]
    for site,n in BLOCKED.items():
        c=candidate.loc[candidate.site.eq(site)]
        h=hold.loc[hold.site.eq(site)]
        result.append({"site":site,"original_source_blockers":n,
            "numeric_RH_only_patch_rows":len(c),
            "held_physics_clock_numeric_rows":len(h),
            "site_clock_approved":False,
            "ready_to_patch_new_isolated_forcing":bool(len(c)>0),
            "original_complete_NOLEAP_forcing_available":False,
            "post_v5_approved":False,"DATM_ready":False,
            "spinup_authorized":False})
    sites=pd.DataFrame(result).sort_values(
      "original_source_blockers",ascending=False).reset_index(drop=True)
    if (sites.original_source_blockers.sum()!=1924
        or sites.numeric_RH_only_patch_rows.sum()!=len(candidate)
        or sites.held_physics_clock_numeric_rows.sum()!=len(hold)):
        raise ValueError("Bulk candidate per-site totals do not close")
    return candidate,hold,sites,selected_off_count

def self_test():
    assert len(BLOCKED)==7 and sum(BLOCKED.values())==1924 and len(SIX)==6
    assert sum(EXPECTED_ROUTING.values())==1924
    t=20.;rh=40.;p=101325
    sat=float(es_water(t));v=sat*(1-rh/100.)
    q=float(q_from_RH(t,p,rh))
    assert 0<v<sat and 0<q<0.08
    assert q_from_RH(t,p,0.)==0
    print("STAGE12B SELF-TEST PASS: seven-site partition, six-site research RH, fixed tower T/P and no output writes",flush=True)

def main():
    arg=argparse.ArgumentParser(description=__doc__)
    opts=arg.add_mutually_exclusive_group(required=True)
    opts.add_argument("--self-test",action="store_true")
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--run",action="store_true")
    run=arg.parse_args()
    print("STAGE12B — 1924 SOURCE EVENTS => SIX-SITE AUTO NUMERIC RH CANDIDATES + GUARDED HOLDS | "+VERSION,flush=True)
    self_test()
    if run.self_test:return
    d,route,pins,previous=preflight()
    patch,hold,by_site,extra=compute(d,route)
    print("\n========== SIX-SITE NUMERIC RH PATCH CANDIDATE COUNTS ==========",flush=True)
    print(by_site.to_string(index=False),flush=True)
    print("\n========== SCIENCE HOLD REASONS ==========",flush=True)
    print(hold.reason.value_counts().to_string(),flush=True)
    print("\n========== CANDIDATE SOURCE RH/T/ERA STATISTICS ==========",flush=True)
    if len(patch):
        print(patch.groupby("site").agg(
            events=("site","size"),
            mean_RH=("research_ERA5Land_grid_RH_pct","mean"),
            min_RH=("research_ERA5Land_grid_RH_pct","min"),
            mean_T=("EC_tower_TA_C_preserved","mean")
        ).to_string(),flush=True)
    print(f"\nSTAGE12B SUMMARY: original_source_humidity_blocks=1924 "
          f"bulk_research_only_numeric_ERA5Land_RH_patches={len(patch)} "
          f"physics_clock_numeric_holds={len(hold)} "
          f"unexpected_source_numeric_holds={extra} "
          "tower_T_unchanged=True forcing_writes=0 "
          "clock_approvals=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if run.check:
        print("CHECK ONLY: ZERO NEW FILES, SOURCE, FORCING OR MODEL WRITES.",flush=True)
        return
    out=ROOT/"science_trials"/("stage12b_six_site_bulk_gridRH_numeric_patches_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "EVENT-LEVEL NUMERIC RESEARCH PATCHES, NOT COMPLETE SITE FORCING.\n")
    tables={
        "six_site_humidity_only_event_patch_candidates.csv":patch,
        "seven_site_science_holds_including_US-Me2.csv":hold,
        "seven_site_patch_and_hold_counts.csv":by_site,
    }
    for name,table in tables.items():
        table.to_csv(out/name,index=False)
    note=("STAGE12B candidate patches are separate original timestamp-keyed "
          "research event records from Stage10b/10d physically screened "
          "ERA5-Land dewpoint RH. They are NOT a full NO_LEAP forcing, "
          "nor validated direct EC tower observations; native UTC offset "
          "hypotheses remain provisional and are NOT modified. "
          "No existing original, Stage07, Stage11h, Stage11l or Stage11q "
          "source files changed. 233 physics conflicts, 4 US-Me2 clock "
          "events, and any unexpected math mismatches remain held. "
          "No Post-v5/DATM/spinup release authorised.\n")
    (out/"SCIENTIFIC_HOLD.md").write_text(note)
    names=[*tables,"SCIENTIFIC_HOLD.md"]
    receipt={
      "version":VERSION,
      "upstream_stage12a_receipt_SHA256":sha(S12A/"stage12a_science_hold_receipt.json"),
      "original_source_evidence_SHA256":pins,
      "original_source_total":1924,
      "numeric_bulk_candidate_rows":len(patch),
      "original_science_physics_holds":233,
      "original_source_clock_holds":4,
      "additional_math_holds":extra,
      "not_complete_site_forcing":True,
      "ec_tower_T_and_P_preserved":True,
      "ERA5Land_time_offset_approved":False,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "INCOMPLETE_marker_present":True,
      "output_sha256":{name:sha(out/name) for name in names}
    }
    (out/"stage12b_numeric_candidate_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12B NUMERIC EVENT PATCHES DIR:",out,flush=True)
    print("NO SOURCE/SEALED FORCING CHANGED; NO MODEL JOBS CREATED.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12B STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage12ap: read-only independent review of US-Kon 31 QC1/MDS neighbor edits.

Compare source-native FLUXMET VPD_F / VPD_F_MDS and QC with original
companion ERA5-Land TA_ERA/VPD_ERA, original tower temperature, previously
selected T, and any nearby genuinely measured QC0 humidity anchors.
Characterise the provenance and temporal persistence of the 31 *existing*
values that Stage12an proposed replacing for 48 missing center repairs.
A QC1 MDS value is NOT independent measured truth. ERA5-Land is also not
independent tower truth; neither reference is an automatic approval.
No UTC shift; original half-hour clock, source QC0, original seven blocked
episodes and two special source-temperature holds are untouched.

--self-test synthetic logic, no external reads/writes
--check SHA-pin inputs, full audit, no writes
--run check + isolated SHA-receipted science tables ONLY
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-stage12ap-v1-20261026-Kon-QC1-MDS-ERA-independent-boundary-audit"
R = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AO = R / "reports/stage12ao_Kon_79_trial_source_provenance_READONLY_20261026T043141Z_a6ee3a18"
AN = R / "science_trials/stage12an_Kon_55_center_connected_ERA_RH_science_only_20261026T040913Z_277a0364"
AK = R / "science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
S = R / "qcv5_native_trial_20261022T024559Z_36c46e58"
DETAIL = "79_trial_patch_source_VPD_QC_provenance_and_magnitude.csv"
EVENTS = "26_connected_event_manual_review_priorities.csv"
BASE = "US-Kon_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
TRIAL = "US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
SPECIAL = {"201102220900", "201109291830"}
HALFHOUR = timedelta(minutes=30)

def regular(p):
    p = Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Immutable source absent or symlink: " + str(p))
    return p

def digest(p):
    h = hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def timestamps(x):
    return x.astype(str).str.replace(r"[^0-9]", "", regex=True).str.slice(0,12)

def numeric(s):
    a = pd.to_numeric(s, errors="coerce")
    return a.mask(a <= -9990)

def satwater(t):
    if not np.isfinite(t) or not (-85 < t < 55):
        return np.nan
    return 6.112 * np.exp(17.67 * t / (t + 243.5))

def relative_humidity(t, v):
    s = satwater(t)
    if not np.isfinite([s,v]).all() or s <= 0:
        return np.nan
    return 100*(1-v/s)

def step(k, n):
    return (datetime.strptime(k, "%Y%m%d%H%M") + n*HALFHOUR).strftime("%Y%m%d%H%M")

def self_test():
    assert step("201110172330", 1) == "201110180000"
    assert step("201110180000", -1) == "201110172330"
    assert abs(relative_humidity(20,0)-100) < 1e-9
    assert np.isnan(relative_humidity(20,np.nan))
    assert abs(relative_humidity(20,satwater(20)*.4)-60) < 1e-9
    assert len(SPECIAL) == 2
    print("STAGE12AP SELF-TEST PASS | QC0 anchors/native half-hours/dry RH; NO WRITES", flush=True)

def verify():
    ao=json.loads(regular(AO/"stage12ao_source_provenance_SHA_receipt.json").read_text())
    an=json.loads(regular(AN/"stage12an_research_only_55_source_event_SHA_receipt.json").read_text())
    ak=json.loads(regular(AK/"stage12ak_research_proposal_SHA_receipt.json").read_text())
    if not (ao.get("version") == "batch03-stage12ao-v1-20261026-Kon-79-patch-independent-source-audit"
            and ao.get("passed_centers_research_only")==48
            and ao.get("original_finite_QC1_QC2_neighbor_replacements_research_only")==31
            and ao.get("seven_blocked_events_unchanged") is True
            and ao.get("two_hard_source_temperature_holds_unchanged") is True
            and ao.get("operator_approval") is False
            and ao.get("DATM_ready") is False
            and ao.get("source_stage12an_receipt_SHA256") == digest(AN/"stage12an_research_only_55_source_event_SHA_receipt.json")
            and an.get("research_center_pass_numerical")==48
            and an.get("original_finite_QC1_QC2_neighbor_source_humidity_changes")==31
            and an.get("numerical_event_trial_PASSED")==19
            and an.get("numerical_event_trial_HELD")==7
            and set(an.get("source_t_disagreement_hard_holds",[]))==SPECIAL
            and an.get("operator_humidity_approval") is False
            and an.get("DATM_ready") is False):
        raise RuntimeError("Signed Stage12ao/an scientific hold/gate changed")
    for f in (DETAIL,EVENTS,"SCIENCE_HOLD.md"):
        if ao.get("output_SHA256",{}).get(f)!=digest(AO/f):
            raise RuntimeError("Unsigned Stage12ao output: "+f)
    if an.get("output_SHA256",{}).get(TRIAL)!=digest(AN/TRIAL):
        raise RuntimeError("Stage12an signed research CSV altered")
    if ak.get("output_SHA256",{}).get(BASE)!=digest(AK/BASE):
        raise RuntimeError("Stage12ak signed selected source altered")
    manifest=json.loads(regular(S/"exact_input_manifest.json").read_text())
    spec=next((r for r in manifest["sites"] if r.get("site")=="US-Kon"),None)
    if spec is None:
        raise RuntimeError("Original US-Kon source manifest missing")
    pins={str(Path(p).resolve()):v for p,v in manifest["input_sha256"].items()}
    for kind in ("primary","era"):
        p=regular(spec[kind])
        if digest(p)!=pins.get(str(p.resolve())):
            raise RuntimeError("Original source SHA changed: "+kind)
    return spec

def native_source(spec):
    needed={"TIMESTAMP_START","VPD_F","VPD_F_QC","VPD_F_MDS","TA_F","TA_F_QC"}
    src=pd.read_csv(regular(spec["primary"]),usecols=lambda x:x in needed,
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    if not needed.issubset(src.columns):
        raise RuntimeError("Original VPD_F_MDS/QC source columns absent")
    src.TIMESTAMP_START=timestamps(src.TIMESTAMP_START)
    if src.TIMESTAMP_START.duplicated().any():
        raise RuntimeError("Original FLUXMET native timestamp collision")
    src=src.set_index("TIMESTAMP_START")
    for c in src.columns:
        src[c]=numeric(src[c])
    era=pd.read_csv(regular(spec["era"]),usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    era.TIMESTAMP_START=timestamps(era.TIMESTAMP_START)
    if era.TIMESTAMP_START.duplicated().any():
        raise RuntimeError("Original ERA companion native timestamp collision")
    era=era.set_index("TIMESTAMP_START")
    for c in era.columns:
        era[c]=numeric(era[c])
    return src,era

def nearest_anchor(key,source,side,max_steps=48):
    """Find nearest same-native QC0 source T and VPD with plausible water RH.
    Directional 24h max; no borrowing an earlier/later time as a repair."""
    for n in range(1,max_steps+1):
        near=step(key,side*n)
        if near not in source.index:
            continue
        x=source.loc[near]
        if not (np.isfinite([x.TA_F,x.VPD_F,x.TA_F_QC,x.VPD_F_QC]).all()
                and int(x.TA_F_QC)==0 and int(x.VPD_F_QC)==0):
            continue
        rh=relative_humidity(float(x.TA_F),float(x.VPD_F))
        if np.isfinite(rh) and 0<=rh<=100:
            return (near,n/2,float(rh))
    return (None,np.nan,np.nan)

def qc1_run(key,src,max_side=48):
    """Contiguous source QC1 VPD run, capped at 24h in either direction."""
    def is_qc1(k):
        if k not in src.index:return False
        s=src.loc[k]
        return np.isfinite(s.VPD_F_QC) and int(s.VPD_F_QC)==1
    if not is_qc1(key):return 0
    count=1
    for side in (-1,1):
        for n in range(1,max_side+1):
            if not is_qc1(step(key,side*n)):break
            count+=1
    return count

def audit():
    spec=verify()
    src,era=native_source(spec)
    details=pd.read_csv(regular(AO/DETAIL),dtype={"native_key":str})
    summary=pd.read_csv(regular(AO/EVENTS),dtype={"seed_begin":str,"seed_end":str})
    if len(details)!=79 or len(summary)!=26 or details.native_key.duplicated().any():
        raise RuntimeError("79 exact source patches / 26 episode lineage changed")
    finite=details.loc[details.kind.eq("EXISTING_QC1_QC2_REPLACED")].copy()
    center=details.loc[details.kind.eq("CENTER_MISSING_FILL")].copy()
    if len(finite)!=31 or len(center)!=48 or set(details.native_key)&SPECIAL:
        raise RuntimeError("Protected old missing and finite source classifications changed")
    if not (finite.original_source_VPD_QC.eq(1).all()
            and finite.source_VPD_equals_MDS.astype(str).str.lower().eq("true").all()):
        raise RuntimeError("Not all 31 source references original QC1/MDS as expected")
    base=pd.read_csv(regular(AK/BASE),dtype={"time":str},
                     usecols=["time","TA_USE","VPD_USE","QBOT"],low_memory=False)
    trial=pd.read_csv(regular(AN/TRIAL),dtype={"time":str},
                      usecols=["time","TA_USE","VPD_USE","QBOT"],low_memory=False)
    if len(base)!=280320 or len(trial)!=280320:
        raise RuntimeError("Full Kon NOLEAP span changed")
    keys_base=timestamps(base.time)
    if keys_base.duplicated().any() or not keys_base.equals(timestamps(trial.time)):
        raise RuntimeError("Original native clock not preserved")
    if not np.array_equal(base.TA_USE.to_numpy(),trial.TA_USE.to_numpy(),equal_nan=True):
        raise RuntimeError("Protected selected tower T changed")
    index=pd.Series(np.arange(len(keys_base)),index=keys_base.to_numpy())
    rows=[]
    for a in finite.itertuples(index=False):
        k=a.native_key
        if k not in src.index or k not in era.index or k not in index:
            raise RuntimeError("Native source/ERA/time missing for "+k)
        s=src.loc[k]
        e=era.loc[k]
        j=int(index.loc[k])
        if not (int(s.VPD_F_QC)==1 and np.isfinite([s.TA_F,s.VPD_F,s.VPD_F_MDS,
                    s.TA_F_QC,e.TA_ERA,e.VPD_ERA]).all()):
            raise RuntimeError("Source QC1 provenance incomplete "+k)
        if not np.isclose(float(s.VPD_F),float(s.VPD_F_MDS),atol=1e-6,rtol=0):
            raise RuntimeError("Source QC1 no longer matches MDS "+k)
        rawrh=relative_humidity(float(s.TA_F),float(s.VPD_F))
        era_rh=relative_humidity(float(e.TA_ERA),float(e.VPD_ERA))
        selected_rh=relative_humidity(float(base.TA_USE.iat[j]),float(base.VPD_USE.iat[j]))
        newrh=relative_humidity(float(trial.TA_USE.iat[j]),float(trial.VPD_USE.iat[j]))
        if not (np.isfinite([rawrh,era_rh,selected_rh,newrh]).all()
                and np.isclose(era_rh,newrh,atol=1e-6,rtol=0)
                and np.isclose(newrh,float(a.paired_ERA_RH_pct),atol=1e-6,rtol=0)
                and np.isclose(selected_rh,float(a.selected_pretrial_RH_pct),atol=1e-6,rtol=0)):
            raise RuntimeError("ERA/source-RH consistency or Stage12ao provenance changed "+k)
        before=nearest_anchor(k,src,-1)
        after=nearest_anchor(k,src,1)
        rows.append({
            "episode":int(a.episode),"native_key":k,
            "original_VPD_F_QC":int(s.VPD_F_QC),
            "original_TA_F_QC":int(s.TA_F_QC),
            "original_VPD_F_equals_MDS":True,
            "original_TA_F_C":float(s.TA_F),
            "selected_TA_USE_C":float(base.TA_USE.iat[j]),
            "companion_TA_ERA_C":float(e.TA_ERA),
            "tower_minus_ERA_T_C":float(s.TA_F-e.TA_ERA),
            "source_original_VPD_F_hPa":float(s.VPD_F),
            "source_native_VPD_ERA_hPa":float(e.VPD_ERA),
            "stage12an_research_candidate_VPD_hPa":float(trial.VPD_USE.iat[j]),
            "original_source_RH_pct":rawrh,
            "original_selected_RH_pct":selected_rh,
            "companion_ERA_RH_pct":era_rh,
            "stage12an_research_RH_pct":newrh,
            "candidate_minus_original_RH_pct_points":newrh-selected_rh,
            "abs_VPD_change_hPa":float(a.abs_change_from_selected_hPa),
            "original_RH_below_5pct":bool(rawrh<5),
            "original_RH_below_10pct":bool(rawrh<10),
            "original_RH_below_20pct":bool(rawrh<20),
            "native_QC1_VPD_run_halfhours_capped_48h":qc1_run(k,src),
            "nearest_prior_both_QC0_key":before[0],
            "nearest_prior_both_QC0_hours_lookback":before[1],
            "nearest_prior_QC0_RH_pct":before[2],
            "nearest_next_both_QC0_key":after[0],
            "nearest_next_both_QC0_hours_lookahead":after[1],
            "nearest_next_QC0_RH_pct":after[2],
            "within_2h_prior_QC0_anchor":bool(np.isfinite(before[1]) and before[1]<=2),
            "within_2h_next_QC0_anchor":bool(np.isfinite(after[1]) and after[1]<=2),
            "operator_approved":False,
        })
    table=pd.DataFrame(rows).sort_values(["episode","native_key"])
    if len(table)!=31 or not table.original_VPD_F_equals_MDS.all():
        raise RuntimeError("31 neighbor source provenance conservation fails")
    group=[]
    for e in summary.itertuples(index=False):
        subset=table.loc[table.episode.eq(int(e.episode))]
        n=len(subset)
        group.append({
            "episode":int(e.episode),"seed_begin":e.seed_begin,"seed_end":e.seed_end,
            "original_missing_centers":int(e.original_centers),
            "numerical_pass":bool(str(e.numerical_pass).lower()=="true"),
            "finite_QC1_MDS_neighbors_proposed":n,
            "original_RH_lt5_N":int(subset.original_RH_below_5pct.sum()) if n else 0,
            "original_RH_lt10_N":int(subset.original_RH_below_10pct.sum()) if n else 0,
            "original_RH_lt20_N":int(subset.original_RH_below_20pct.sum()) if n else 0,
            "median_original_QC1_MDS_RH_pct":float(subset.original_selected_RH_pct.median()) if n else np.nan,
            "median_ERA_research_RH_pct":float(subset.stage12an_research_RH_pct.median()) if n else np.nan,
            "maximum_abs_replaced_VPD_hPa":float(subset.abs_VPD_change_hPa.max()) if n else np.nan,
            "source_T_QC1_count":int(subset.original_TA_F_QC.eq(1).sum()) if n else 0,
            "neighbor_both_QC0_anchor_within_2h_each_side":int(
                (subset.within_2h_prior_QC0_anchor & subset.within_2h_next_QC0_anchor).sum()) if n else 0,
            "science_priority":("HIGH_MDS_DRYNESS_AND_SCOPE" if n>=5 else
                                "QC1_MDS_DRYNESS_REVIEW" if n and subset.original_RH_below_10pct.any() else
                                "QC1_MDS_SOURCE_REVIEW" if n else
                                "CENTER_ONLY_NOT_EVIDENCE_FOR_REPLACEMENT"),
            "operator_approved":False
        })
    grouped=pd.DataFrame(group)
    if (len(grouped)!=26 or grouped.finite_QC1_MDS_neighbors_proposed.sum()!=31
        or grouped.loc[grouped.episode.isin([15,17]),"finite_QC1_MDS_neighbors_proposed"].sum()!=24
        or int(table.original_VPD_F_QC.eq(1).sum())!=31):
        raise RuntimeError("Expected event distribution/QC1 MDS source identity changed")
    return table,grouped

def main():
    ap=argparse.ArgumentParser()
    one=ap.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):
        one.add_argument("--"+name,action="store_true")
    args=ap.parse_args()
    print("STAGE12AP SOURCE-NATIVE QC1/MDS vs ERA-RH SCIENCE AUDIT | "+VERSION,flush=True)
    self_test()
    if args.self_test:return
    table,grouped=audit()
    print("\n====== QC1 / MDS FINITE NEIGHBOR SCIENCE SUMMARY ======",flush=True)
    print("31_SIGNED_FINITE_NEIGHBORS",len(table),
          "SOURCE_QC1_MDS_MATCHES",int(table.original_VPD_F_equals_MDS.sum()),
          "ORIGINAL_RH_LT5",int(table.original_RH_below_5pct.sum()),
          "ORIGINAL_RH_LT10",int(table.original_RH_below_10pct.sum()),
          "ORIGINAL_RH_LT20",int(table.original_RH_below_20pct.sum()),flush=True)
    print("ALL ORIGINAL 48 CENTERS STILL PROPOSALS, SEVEN HELD EPISODES UNCHANGED; NO APPROVAL",flush=True)
    print("\n====== EVENT / QCO ANCHOR AUDIT ======",flush=True)
    print(grouped.to_string(index=False),flush=True)
    print("\n====== 31 ORIGINAL MDS vs ERA SOURCE PAIRS ======",flush=True)
    fields=["episode","native_key","original_TA_F_QC","original_TA_F_C",
      "tower_minus_ERA_T_C","original_source_RH_pct","companion_ERA_RH_pct",
      "candidate_minus_original_RH_pct_points","abs_VPD_change_hPa",
      "native_QC1_VPD_run_halfhours_capped_48h",
      "nearest_prior_both_QC0_hours_lookback","nearest_prior_QC0_RH_pct",
      "nearest_next_both_QC0_hours_lookahead","nearest_next_QC0_RH_pct"]
    print(table[fields].round(5).to_string(index=False),flush=True)
    if args.check:
        print("STAGE12AP CHECK ONLY | NO WRITES, NO APPROVAL",flush=True)
        return
    out=R/"reports"/("stage12ap_Kon_QC1_MDS_ERA_RH_QC0_anchor_review_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    tables={
      "31_original_QC1_MDS_ERA_RH_QC0_anchor_diagnostics.csv":table,
      "26_event_MDS_dryness_scope_QC0_anchor_summary.csv":grouped
    }
    for name,d in tables.items():
        d.to_csv(out/name,index=False)
    marker="SCIENCE_ONLY_NO_HUMIDITY_APPROVAL_NO_DATM"
    (out/marker).write_text(
      "QC1/MDS is not independent measured QC0; native ERA5-Land is likewise "
      "not independent tower truth. No numerical source or RH discrepancy "
      "automatically authorizes replacing original finite VPD/QBOT. QC0 "
      "reference anchors are temporal diagnostics (up to 24h each direction), "
      "not calibration, not interpolation, and not evidence of truth between anchors. "
      "The 48 filled centers and 31 finite neighbors remain scientific research "
      "candidates. Seven events and two special source-T holds remain protected. "
      "No source, times, prior trials, production forcing or spinup edits.\n")
    sums={name:digest(out/name) for name in [*tables,marker]}
    (out/"stage12ap_QC1_MDS_ERA_science_SHA_receipt.json").write_text(json.dumps({
      "version":VERSION,
      "signed_Stage12ao_receipt_SHA256":digest(AO/"stage12ao_source_provenance_SHA_receipt.json"),
      "QC1_MDS_original_neighbors_verified":31,
      "Stage12an_research_missing_centers_unapproved":48,
      "seven_blocked_events_remain":True,"two_source_temperature_holds_remain":True,
      "original_source_QC0_unchanged":True,"operator_approved":False,
      "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
      "output_SHA256":sums
    },indent=2)+"\n")
    print("STAGE12AP READ-ONLY SOURCE QC1 MDS vs ERA-RH REPORT DIR:",out,flush=True)
    print("NO ORIGINAL OBSERVATION, Stage12ak/an/ao, CIME, DATM, OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12AP STOP:",e,file=sys.stderr,flush=True)
        raise

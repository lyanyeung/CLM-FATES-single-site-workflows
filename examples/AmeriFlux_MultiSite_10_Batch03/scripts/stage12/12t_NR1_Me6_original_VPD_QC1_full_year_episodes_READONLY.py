#!/usr/bin/env python3
"""Batch03 Stage12t: WHOLE-YEAR original VPD QC1 physical invalidity episodes.

Source-only audit for US-Me6 2015+2017 and US-NR1 2022, motivated by 32
signed Stage12r/s QC1 neighbor sides where FLUXMET VPD_F >= es_water(TA_F).
For each source-year count physically inconsistent VPD stratified by
original VPD_F_QC and TA_F_QC; detect all consecutive original QC1 VPD
bad / original QC0 T episodes, locate the 32 signed sides in those runs,
and find nearest source VPD_QC=0 and TA_QC=0 *physically valid* anchors
within +/-24 hours. These anchors are context only, not replacements.
The user must assess source product and sensor differences separately.

--self-test : synthetic numerical / run detector, zero filesystem reads
--check     : verify original S07 + Stage12s SHA; no writes
--run       : check then isolated SHA-only report, no forcing/model writes
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION = "batch03-stage12t-v1-20261025-three-source-years-original-VPD-QC-runs"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
C = ROOT / "science_trials/stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e"
R = ROOT / "reports/stage12r_32_QC1_native_VPD_source_physics_and_ERA_RH_20261025T094639Z_a770eeb8"
S = ROOT / "reports/stage12s_32_QC1_native_VPD_pm6h_source_context_20261025T180547Z_6a9cc5ab"
YEARS = {"US-Me6": (2015, 2017), "US-NR1": (2022,)}
RAW = ("TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC")
ERA = ("TIMESTAMP_START", "TA_ERA", "VPD_ERA")
S_FILE = "32_original_QC1_edge_physics_and_nearest_QC0_reference.csv"

def safe(p):
    p = Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Signed original source absent/symlinked " + str(p))
    return p

def sha(p):
    h = hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def numeric(x):
    a = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    a[~np.isfinite(a) | (a <= -9990)] = np.nan
    return a

def es(t):
    t = np.asarray(t, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return 6.112 * np.exp(17.67*t/(t+243.5))

def runs(mask):
    """Return inclusive index bounds of all true runs, no cross-year joins."""
    arr = np.asarray(mask, dtype=bool)
    change = np.diff(np.r_[False, arr, False].astype(int))
    return list(zip(np.flatnonzero(change == 1),
                    np.flatnonzero(change == -1)-1))

def equal(x, y, eps=1e-7):
    if pd.isna(x) or pd.isna(y):
        return pd.isna(x) and pd.isna(y)
    return abs(float(x)-float(y)) <= eps

def selftest():
    assert runs([False, True, True, False, True, False]) == [(1, 2), (4, 4)]
    assert runs([False, False]) == [] and runs([True, True]) == [(0, 1)]
    assert abs(float(es(20)) - 23.37) < .01
    assert float(es(5)) < float(es(20))
    assert equal(np.nan, np.nan)
    assert len(YEARS) == 2 and sum(map(len, YEARS.values())) == 3
    print("STAGE12T SELF-TEST PASS: original VPD vs water saturation, strict native QC and full-year episode counts; NO WRITES", flush=True)

def verify():
    r = json.loads(safe(R/"stage12r_science_only_SHA_receipt.json").read_text())
    s = json.loads(safe(S/"stage12s_science_context_SHA_receipt.json").read_text())
    c = json.loads(safe(C/"stage12c_research_shadow_SHA_receipt.json").read_text())
    if (r.get("original_32_QC1_edges") is not True
        or r.get("original_86_science_holds_preserved") is not True
        or s.get("version") != "batch03-stage12s-v3-20261025-QC1-VPD-QC0-physical-reference-pm6h"
        or s.get("original_stage12r_SHA256") != sha(R/"stage12r_science_only_SHA_receipt.json")
        or s.get("original_32_QC1_sides_unchanged") is not True
        or s.get("original_86_holds_unchanged") is not True
        or s.get("original_233_physics_holds_unchanged") is not True
        or s.get("new_humidity_repairs") != 0
        or c.get("physically_held_times_intentionally_missing") != 233
        or c.get("stage07_manifest_SHA256") != sha(S07/"exact_input_manifest.json")):
        raise ValueError("Stage12r/s/c science receipt changed")
    for rec, directory in ((s,S),(r,R)):
        if (rec.get("Postv5_approved") != 0
            or rec.get("DATM_ready") != 0
            or rec.get("spinup_authorized") != 0):
            raise ValueError("Prior science-only approval gate changed")
        for name, digest in rec.get("output_SHA256", {}).items():
            if sha(directory/name) != digest:
                raise ValueError("Signed Stage12r/s source report changed " + name)
    original = json.loads(safe(S07/"exact_input_manifest.json").read_text())
    specs = {record["site"]:record for record in original["sites"]}
    pins = {str(Path(p).resolve()): digest for p,digest in original["input_sha256"].items()}
    for site in YEARS:
        if site not in specs:
            raise ValueError("Original source missing " + site)
        for k in ("primary","era"):
            f = safe(specs[site][k])
            if sha(f) != pins.get(str(f.resolve())):
                raise ValueError("Original source input SHA changed " + site + " " + k)
    targets = pd.read_csv(safe(S/S_FILE), dtype={
        "held_native_key":str,"neighbor_native_key":str}, low_memory=False)
    if (len(targets) != 32 or not targets.site.isin(YEARS).all()
        or not targets.focal_source_VPD_F_QC.eq(1).all()
        or targets.duplicated(["site","held_native_key",
                               "neighbor_native_key","neighbor_side"]).any()):
        raise ValueError("Original signed 32 QC1 native side identities changed")
    if not set(targets.source_origin_class).issubset(
            {"BOTH_FINITE_DIFFER","RAW_ONLY_FINITE"}):
        raise ValueError("Stage12s original QC1 source state changed")
    return specs, targets

def year_frame(site, year, spec):
    def source(path, columns):
        x = pd.read_csv(safe(path), usecols=columns,
                        dtype={"TIMESTAMP_START":str}, low_memory=False)
        x = x.loc[x.TIMESTAMP_START.str.startswith(str(year))].copy()
        x.sort_values("TIMESTAMP_START", inplace=True)
        x.reset_index(drop=True, inplace=True)
        if (len(x) != 17520 or x.TIMESTAMP_START.duplicated().any()):
            raise ValueError("Original year must be 17,520 unique native HH " + site + " " + str(year))
        return x
    primary = source(spec["primary"], list(RAW))
    companion = source(spec["era"], list(ERA))
    if not primary.TIMESTAMP_START.equals(companion.TIMESTAMP_START):
        raise ValueError("Original paired source year clock mismatch " + site + " " + str(year))
    times = pd.DatetimeIndex(pd.to_datetime(
        primary.TIMESTAMP_START, format="%Y%m%d%H%M", errors="raise"))
    start = pd.Timestamp(year=year,month=1,day=1)
    if (times[0] != start or times[-1] != start+pd.Timedelta(days=365)-pd.Timedelta(minutes=30)
        or not (np.diff(times.to_numpy()).astype("timedelta64[m]").astype(int)==30).all()):
        raise ValueError("Source native full-year nonleap half-hour coverage mismatch " + site + " " + str(year))
    d = pd.DataFrame({"site":site, "year":year,
                      "native_key":primary.TIMESTAMP_START.copy()})
    for col in RAW[1:]:
        d[col] = numeric(primary[col])
    for col in ERA[1:]:
        d[col] = numeric(companion[col])
    d["es_hPa"] = es(d.TA_F.to_numpy(dtype=float))
    d["implied_ea_hPa"] = d.es_hPa - d.VPD_F
    valid = (np.isfinite(d.TA_F) & np.isfinite(d.VPD_F)
             & np.isfinite(d.es_hPa))
    d["physically_invalid"] = (
        valid & ((d.VPD_F<0) | (d.VPD_F>=d.es_hPa)))
    d["vpd_exceeds_es"] = valid & (d.VPD_F>=d.es_hPa)
    d["raw_vpd_qc1_ta_qc0_invalid"] = (
        d.physically_invalid & d.VPD_F_QC.eq(1) & d.TA_F_QC.eq(0))
    d["qc0_vpd_ta_physically_valid"] = (
        valid & (d.VPD_F>=0) & (d.VPD_F<d.es_hPa)
        & d.VPD_F_QC.eq(0) & d.TA_F_QC.eq(0))
    return d

def analyze():
    specs, targets = verify()
    source_summaries, episodes, focal = [],[],[]
    for site in YEARS:
        for year in YEARS[site]:
            d = year_frame(site,year,specs[site])
            qc = d.VPD_F_QC.to_numpy(dtype=float)
            tqc = d.TA_F_QC.to_numpy(dtype=float)
            vv = d.VPD_F.to_numpy(dtype=float)
            tt = d.TA_F.to_numpy(dtype=float)
            ea = d.TA_ERA.to_numpy(dtype=float)
            esrc = d.es_hPa.to_numpy(dtype=float)
            invalid = d.physically_invalid.to_numpy(dtype=bool)
            episodes_mask = d.raw_vpd_qc1_ta_qc0_invalid.to_numpy(dtype=bool)
            valid_anchor = d.qc0_vpd_ta_physically_valid.to_numpy(dtype=bool)
            keys = d.native_key.to_numpy(dtype=str)
            pos = {k:i for i,k in enumerate(keys)}
            if len(pos) != 17520:
                raise ValueError("Original native source duplicate key")
            for label, mask in (
                ("QC0",qc==0), ("QC1",qc==1),
                ("QC2",qc==2), ("QC_UNKNOWN",~np.isin(qc,[0,1,2]))):
                m = mask & np.isfinite(tt) & np.isfinite(vv)
                source_summaries.append({
                    "site":site,"year":year,"source_VPD_F_QC":label,
                    "all_native_HH":len(d),
                    "valid_T_and_VPD_count":int(m.sum()),
                    "with_original_T_QC0":int((m & (tqc==0)).sum()),
                    "physically_invalid_T_and_VPD":int((m & invalid).sum()),
                    "physically_invalid_with_T_QC0":int(
                        (m & invalid & (tqc==0)).sum()),
                    "VPD_at_or_above_es_water_with_T_QC0":int((
                        m & (vv>=esrc) & (tqc==0)).sum()),
                    "negative_VPD_with_T_QC0":int((
                        m & (vv<0) & (tqc==0)).sum()),
                    "physically_invalid_fraction_of_valid_T_VPD":(
                        float((m&invalid).sum()/m.sum()) if m.any() else np.nan)
                })
            rr = runs(episodes_mask)
            belong = np.full(len(d),-1,dtype=int)
            for ident,(a,b) in enumerate(rr):
                belong[a:b+1]=ident
                episodes.append({
                    "site":site,"year":year,"episode_index":ident,
                    "start_native_key":keys[a],
                    "end_native_key":keys[b],
                    "duration_halfhours":b-a+1,
                    "duration_hours":(b-a+1)/2,
                    "max_original_VPD_excess_over_water_es_hPa":
                        float(np.max(vv[a:b+1]-esrc[a:b+1])),
                    "median_tower_minus_native_companion_T_C":
                        float(np.nanmedian(tt[a:b+1]-ea[a:b+1]))
                        if np.isfinite(tt[a:b+1]-ea[a:b+1]).any() else np.nan,
                    "source_qc1_VPD_tower_qc0_T":True
                })
            for x in targets.loc[
                    targets.site.eq(site)
                    & targets.neighbor_native_key.str.startswith(str(year))
                    ].itertuples(index=False):
                key=x.neighbor_native_key
                if key not in pos:
                    raise ValueError("Original signed focal side missing from full year " + site+" "+key)
                i=pos[key]
                if (qc[i] != 1 or tqc[i] != 0
                    or not episodes_mask[i]
                    or not equal(vv[i],x.focal_source_VPD_F_hPa)
                    or not equal(tt[i],x.focal_source_TA_F_C)):
                    raise ValueError("Source QC1+QC0 physical invalid focal mismatch " + site+" "+key)
                segment = rr[belong[i]]
                a,b=segment
                near_left = np.flatnonzero(valid_anchor[max(0,i-48):i])
                prior = int(max(0,i-48)+near_left[-1]) if len(near_left) else None
                near_right = np.flatnonzero(valid_anchor[i+1:min(len(d),i+49)])
                after = int(i+1+near_right[0]) if len(near_right) else None
                focal.append({
                    "site":site,"year":year,
                    "held_native_key":x.held_native_key,
                    "neighbor_native_key":key,
                    "neighbor_side":x.neighbor_side,
                    "source_origin_class":x.source_origin_class,
                    "original_source_TA_F_C":tt[i],
                    "original_source_TA_F_QC":tqc[i],
                    "original_source_VPD_F_hPa":vv[i],
                    "original_source_VPD_F_QC":qc[i],
                    "water_es_at_tower_T_hPa":esrc[i],
                    "source_VPD_minus_water_es_hPa":vv[i]-esrc[i],
                    "stage12s_focal_source_excess_reconciles":equal(
                         vv[i]-esrc[i],x.focal_source_VPD_minus_es_hPa),
                    "source_QC1_VPD_physically_invalid_run_ID":int(belong[i]),
                    "run_start_native_key":keys[a],
                    "run_end_native_key":keys[b],
                    "run_duration_HH":b-a+1,
                    "run_duration_hours":(b-a+1)/2,
                    "run_hh_before_focal":i-a,
                    "run_hh_after_focal":b-i,
                    "nearest_prior_QC0_T_and_VPD_physically_valid_within24h":(
                        keys[prior] if prior is not None else ""),
                    "nearest_prior_QC0_valid_VPD_hPa":(
                        vv[prior] if prior is not None else np.nan),
                    "prior_QC0_valid_anchor_minutes_away":(
                        (i-prior)*30 if prior is not None else np.nan),
                    "nearest_next_QC0_T_and_VPD_physically_valid_within24h":(
                        keys[after] if after is not None else ""),
                    "nearest_next_QC0_valid_VPD_hPa":(
                        vv[after] if after is not None else np.nan),
                    "next_QC0_valid_anchor_minutes_away":(
                        (after-i)*30 if after is not None else np.nan),
                    "companion_TA_ERA_C":ea[i],
                    "source_T_minus_native_companion_T_C":tt[i]-ea[i],
                    "original_science_hold_released":False
                })
    results=pd.DataFrame(source_summaries)
    events=pd.DataFrame(episodes)
    sides=pd.DataFrame(focal)
    if (len(results)!=12 or len(sides)!=32
        or not sides.stage12s_focal_source_excess_reconciles.all()
        or not sides.source_VPD_minus_water_es_hPa.ge(0).all()
        or not sides.original_source_TA_F_QC.eq(0).all()
        or not sides.original_source_VPD_F_QC.eq(1).all()):
        raise ValueError("Original 3-year source QC1-VPD/TA-QC0 stage side totals changed")
    merged=events.merge(
        sides.groupby(["site","year","source_QC1_VPD_physically_invalid_run_ID"],
                      as_index=False).agg(
            signed_focal_neighbor_sides=("neighbor_native_key","count")),
        how="left",left_on=["site","year","episode_index"],
        right_on=["site","year","source_QC1_VPD_physically_invalid_run_ID"],
        validate="one_to_one")
    merged["signed_focal_neighbor_sides"]=(
        merged.signed_focal_neighbor_sides.fillna(0).astype(int))
    if merged.signed_focal_neighbor_sides.sum()!=32:
        raise ValueError("Signed 32 sides not accounted for in full-year native QC run IDs")
    linked=sides.groupby(["site","year","source_origin_class"],
        as_index=False).agg(
            signed_focal_sides=("neighbor_native_key","size"),
            median_run_duration_HH=("run_duration_HH","median"),
            longest_run_duration_HH=("run_duration_HH","max"),
            source_QC0_T_and_VPD_anchor_within24h_before=(
                "nearest_prior_QC0_T_and_VPD_physically_valid_within24h",
                lambda q:int(q.ne("").sum())),
            source_QC0_T_and_VPD_anchor_within24h_after=(
                "nearest_next_QC0_T_and_VPD_physically_valid_within24h",
                lambda q:int(q.ne("").sum()))
        )
    return results,merged,sides,linked

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for flag in ("self-test","check","run"):
        g.add_argument("--"+flag,action="store_true")
    args=p.parse_args()
    print("STAGE12T — ORIGINAL FLUXMET VPD_F_QC, TA_F_QC WHOLE-YEAR PHYSICS / EPISODES | "+VERSION,flush=True)
    selftest()
    if args.self_test:
        return
    qc,episodes,sides,link=analyze()
    print("\n========== ORIGINAL FULL-YEAR VPD QC VS WATER-PHYSICS (3 SITE-YEARS) ==========",flush=True)
    print(qc.to_string(index=False),flush=True)
    print("\n========== 32 SIGNED SIDES: ORIGINAL QC1 INVALID RUNS AND QC0 VALID ANCHORS +/-24H ==========",flush=True)
    print(link.to_string(index=False),flush=True)
    print("\n========== LONGEST QC1 INVALID WATER-VPD RUNS (ORIGINAL TA QC0) ==========",flush=True)
    print(episodes.sort_values("duration_halfhours",ascending=False).head(15).to_string(index=False),flush=True)
    print("\nSTAGE12T SUMMARY: full_native_source_halfhours=52560 "
          "site_years=3 original_QC1_held_neighbor_sides=32 "
          "original_86_held_events_preserved=TRUE "
          "original_233_phys_holds_preserved=TRUE "
          "new_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12T CHECK ONLY: NO SOURCE, REPORT OR MODEL WRITES.",flush=True)
        return
    dest=ROOT/"reports"/(
        "stage12t_original_VPD_QC1_full_year_physics_episodes_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    output={
       "three_site_year_original_VPD_QC_source_physics.csv":qc,
       "original_QC1_bad_VPD_full_year_episode_ledger.csv":episodes,
       "32_signed_QC1_invalid_VPD_sides_episode_and_QC0_anchors.csv":sides,
       "32_signed_QC1_sides_full_year_episode_summary.csv":link,
    }
    for name,frame in output.items():
        frame.to_csv(dest/name,index=False)
    (dest/"SCIENTIFIC_HOLD.md").write_text(
        "This is an ORIGINAL source-QC/year-wide water-vapour physics and "
        "run-duration diagnosis only. QC0 nearby anchors are scientific "
        "context, not approved interpolation or replacements. Original "
        "T/VPD/pressure native clock unchanged, all 86 held source science "
        "events and previous 233 protected physics cases unchanged; "
        "Post-v5, DATM, spinup and model execution prohibited.\n")
    hashes={k:sha(dest/k) for k in [*output,"SCIENTIFIC_HOLD.md"]}
    receipt={
       "version":VERSION,
       "stage12s_SHA256":sha(S/"stage12s_science_context_SHA_receipt.json"),
       "signed_32_original_QC1_sides_preserved":True,
       "original_86_holds_preserved":True,
       "original_233_holds_preserved":True,
       "original_source_T_VPD_P_clock_unchanged":True,
       "new_source_repairs":0,
       "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
       "output_SHA256":hashes
    }
    (dest/"stage12t_full_year_original_VPD_source_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12T ORIGINAL YEAR-SOURCE REPORT DIR:",dest,flush=True)
    print("NO ORIGINAL SOURCE, FORCING, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12T STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage12ao: independent source/impact audit of Stage12an's 79 Kon patches.

This does NOT accept the 48 proposed humidity-centre fills or the 31 original
finite QC1/QC2 neighbor replacements. Classify their provenance, quantify
change magnitude, identify long modified episodes and preserve seven blocked
episodes plus two hard T/source conflicts. Signed research reports only.

Usage: --self-test (no files), --check (no writes), --run (reports only).
No DATM, original observations, previously approved edits or Slurm changes.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VERSION = "batch03-stage12ao-v1-20261026-Kon-79-patch-independent-source-audit"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AK = ROOT / "science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AN = ROOT / "science_trials/stage12an_Kon_55_center_connected_ERA_RH_science_only_20261026T040913Z_277a0364"
S = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
AK_FILE = "US-Kon_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
AN_FILE = "US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
EVENTS = "connected_episode_pass_and_source_hold_reasons.csv"
PATCHES = "research_candidate_native_QC1_QC2_humidity_event_changes.csv"
EDGES = "science_only_event_VPD_30min_boundaries.csv"
MARKER = "INCOMPLETE_NUMERICAL_RESEARCH_HUMIDITY_NOT_OPERATOR_APPROVED_NO_DATM"
SPECIAL = {"201102220900", "201109291830"}
COLUMNS = ["time", "TA_USE", "PSRF", "VPD_USE", "QBOT"]

def safe(p):
    p = Path(p)
    if p.is_symlink() or not p.is_file():
        raise RuntimeError("Required immutable source absent or symlink: " + str(p))
    return p

def sha(p):
    h = hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def keys(s):
    return s.astype(str).str.replace(r"[^0-9]", "", regex=True).str.slice(0, 12)

def numeric(s):
    x = pd.to_numeric(s, errors="coerce")
    return x.mask(x <= -9990)

def satw(t):
    t = float(t)
    return 6.112 * np.exp(17.67 * t / (243.5 + t))

def rh_from_vpd(t, v):
    if not np.isfinite([t, v]).all():
        return np.nan
    return 100.0 * (1.0 - float(v) / satw(t))

def selftest():
    assert keys(pd.Series(["2011-10-17 07:30"])).iloc[0] == "201110170730"
    assert abs(rh_from_vpd(20, 0) - 100) < 1e-10
    assert np.isnan(rh_from_vpd(20, np.nan))
    assert len(SPECIAL) == 2
    assert len({15, 17}) == 2
    print("STAGE12AO SELF-TEST PASS | 79-trial provenance logic; no reads or writes", flush=True)

def verified():
    ar = json.loads(safe(AN / "stage12an_research_only_55_source_event_SHA_receipt.json").read_text())
    kr = json.loads(safe(AK / "stage12ak_research_proposal_SHA_receipt.json").read_text())
    if not (ar.get("version") == "batch03-stage12an-v1-20261026-Kon-connected-ERA-RH-55-centers"
            and ar.get("research_centers_requested") == 55
            and ar.get("research_center_pass_numerical") == 48
            and ar.get("original_finite_QC1_QC2_neighbor_source_humidity_changes") == 31
            and ar.get("numerical_event_trial_PASSED") == 19
            and ar.get("numerical_event_trial_HELD") == 7
            and ar.get("Kon_stage12an_science_trial_VPD_missing") == 341
            and set(ar.get("source_t_disagreement_hard_holds", [])) == SPECIAL
            and ar.get("operator_humidity_approval") is False
            and ar.get("DATM_ready") is False
            and ar.get("spinup_authorized") is False
            and ar.get("original_ak_science_SHA256")
            == sha(AK / "stage12ak_research_proposal_SHA_receipt.json")):
        raise RuntimeError("Stage12an science receipt/count/safety lineage mismatch")
    for f in (AN_FILE, EVENTS, PATCHES, EDGES, MARKER):
        if ar.get("output_SHA256", {}).get(f) != sha(AN / f):
            raise RuntimeError("Stage12an signed output altered: " + f)
    if kr.get("output_SHA256", {}).get(AK_FILE) != sha(AK / AK_FILE):
        raise RuntimeError("Prior Stage12ak research base altered")
    manifest = json.loads(safe(S / "exact_input_manifest.json").read_text())
    spec = next((v for v in manifest["sites"] if v["site"] == "US-Kon"), None)
    if spec is None:
        raise RuntimeError("Kon missing from original source manifest")
    orig = safe(spec["primary"])
    pins = {str(Path(k).resolve()): v for k, v in manifest["input_sha256"].items()}
    if sha(orig) != pins.get(str(orig.resolve())):
        raise RuntimeError("Original FLUXMET source SHA changed")
    return orig

def audit():
    original_source = verified()
    base = pd.read_csv(safe(AK / AK_FILE), usecols=COLUMNS, dtype={"time":str}, low_memory=False)
    trial = pd.read_csv(safe(AN / AN_FILE), usecols=COLUMNS, dtype={"time":str}, low_memory=False)
    if len(base) != 280320 or len(trial) != 280320:
        raise RuntimeError("Original full NOLEAP coverage or trial length changed")
    native = keys(base.time)
    if native.duplicated().any() or not native.equals(keys(trial.time)):
        raise RuntimeError("Trial source-native clock changed, duplicated or reordered")
    for c in ("TA_USE", "PSRF"):
        if not np.array_equal(base[c].to_numpy(), trial[c].to_numpy(), equal_nan=True):
            raise RuntimeError("Protected selected meteorology changed: " + c)
    idx = pd.Series(np.arange(len(native)), index=native.to_numpy())
    events = pd.read_csv(safe(AN / EVENTS), dtype={"seed_begin":str, "seed_end":str})
    patches = pd.read_csv(safe(AN / PATCHES), dtype={"native_key":str})
    if len(events) != 26 or int(events.seed_original_55_target_count.sum()) != 55:
        raise RuntimeError("26 episodes/55-centre signed lineage altered")
    if not (int(events.research_numerical_pass.astype(str).str.lower().eq("true").sum()) == 19
            and len(events.loc[events.research_numerical_pass.astype(str).str.lower().ne("true")]) == 7):
        raise RuntimeError("Pass/held episode status altered")
    passed = patches.loc[patches.episode_numerical_pass.astype(str).str.lower().eq("true")].copy()
    if len(passed) != 79 or passed.native_key.duplicated().any():
        raise RuntimeError("Expected exactly 79 unique passed source-native proposals")
    if set(passed.native_key) & SPECIAL:
        raise RuntimeError("One of two protected source-temperature events would be edited")
    if not set(passed.native_key).issubset(set(idx.index)):
        raise RuntimeError("Candidate not within original native clock")
    oldv = base.VPD_USE.to_numpy(dtype=float)
    newv = trial.VPD_USE.to_numpy(dtype=float)
    oldq = base.QBOT.to_numpy(dtype=float)
    newq = trial.QBOT.to_numpy(dtype=float)
    changed = ~(np.isclose(oldv, newv, rtol=0, atol=1e-10, equal_nan=True) &
                np.isclose(oldq, newq, rtol=0, atol=1e-12, equal_nan=True))
    actual = set(native.iloc[np.flatnonzero(changed)])
    proposed = set(passed.native_key)
    centers = set(passed.loc[passed.kind.eq("ORIGINAL_55_VPD_HELD_CENTER"), "native_key"])
    if not actual.issubset(proposed) or not centers.issubset(actual):
        raise RuntimeError("Trial humidity modifications cross 79 allowed rows or omit a center")
    # One of the 31 proposed finite-neighbor replacements may numerically
    # match the old value: keep it as a no-op proposal, not a verified edit.
    no_op_proposals = len(proposed - actual)
    print("STAGE12AO PROPOSED_ROWS 79 ACTUAL_NUMERIC_CHANGES",
          len(actual), "NO_OP_PROPOSALS", no_op_proposals, flush=True)
    if int(np.isnan(newv).sum()) != 341 or not np.array_equal(np.isnan(newv), np.isnan(newq)):
        raise RuntimeError("Remaining trial VPD/QBOT missing mask altered")
    src_cols = {"TIMESTAMP_START", "VPD_F", "VPD_F_QC", "VPD_F_MDS", "TA_F", "TA_F_QC"}
    src = pd.read_csv(original_source, usecols=lambda c: c in src_cols,
                      dtype={"TIMESTAMP_START":str}, low_memory=False)
    required = {"TIMESTAMP_START", "VPD_F", "VPD_F_QC", "TA_F", "TA_F_QC"}
    if not required.issubset(src.columns) or src.TIMESTAMP_START.duplicated().any():
        raise RuntimeError("Raw FLUXMET metadata missing/duplicated")
    src["TIMESTAMP_START"] = keys(src.TIMESTAMP_START)
    if src.TIMESTAMP_START.duplicated().any():
        raise RuntimeError("Raw FLUXMET native clock duplicated")
    src = src.set_index("TIMESTAMP_START")
    for c in src.columns:
        src[c] = numeric(src[c])
    if not set(passed.native_key).issubset(set(src.index)):
        raise RuntimeError("Candidate native key missing in original tower source")
    rows = []
    for p in passed.itertuples(index=False):
        k = str(p.native_key)
        j = int(idx.loc[k])
        s = src.loc[k]
        center = str(p.kind) == "ORIGINAL_55_VPD_HELD_CENTER"
        old = float(oldv[j])
        new = float(newv[j])
        new_q = float(newq[j])
        qc = int(s.VPD_F_QC)
        if qc not in (1, 2) or int(p.source_original_VPD_QC) != qc:
            raise RuntimeError("Protected QC0 humidity or changed QC classification: " + k)
        if center != bool(np.isnan(old)):
            raise RuntimeError("Center-missing vs finite-neighbor classification mismatch: " + k)
        if not (np.isfinite(new) and np.isfinite(new_q)
                and np.isclose(new, float(p.ERA_RH_research_VPD_hPa), atol=1e-9, rtol=0)
                and np.isclose(new_q, float(p.ERA_RH_research_QBOT_kgkg), atol=1e-11, rtol=0)):
            raise RuntimeError("Signed candidate changed or physically nonfinite: " + k)
        obs_vpd = float(s.VPD_F)
        mds = float(s.VPD_F_MDS) if "VPD_F_MDS" in src.columns else np.nan
        difference = abs(new - old) if np.isfinite(old) else np.nan
        rows.append({
            "episode":int(p.episode), "native_key":k,
            "kind":"CENTER_MISSING_FILL" if center else "EXISTING_QC1_QC2_REPLACED",
            "original_source_VPD_QC":qc, "original_source_TA_QC":float(s.TA_F_QC),
            "original_source_VPD_F_hPa":obs_vpd,
            "original_source_VPD_F_MDS_hPa":mds,
            "source_VPD_equals_MDS":bool(np.isfinite([obs_vpd, mds]).all()
                and np.isclose(obs_vpd, mds, atol=1e-6, rtol=0)),
            "selected_pretrial_VPD_hPa":old,
            "Stage12an_ERA_RH_candidate_VPD_hPa":new,
            "abs_change_from_selected_hPa":difference,
            "abs_change_from_source_VPD_F_hPa":abs(new - obs_vpd) if np.isfinite(obs_vpd) else np.nan,
            "selected_pretrial_RH_pct":rh_from_vpd(float(base.TA_USE.iat[j]), old),
            "Stage12an_candidate_RH_pct":rh_from_vpd(float(base.TA_USE.iat[j]), new),
            "source_native_TA_F_C":float(s.TA_F),
            "selected_unchanged_TA_USE_C":float(base.TA_USE.iat[j]),
            "paired_ERA_RH_pct":float(p.paired_native_ERA_RH_pct),
            "operator_approval":False
        })
    details = pd.DataFrame(rows).sort_values(["episode","native_key"])
    finite = details[details.kind == "EXISTING_QC1_QC2_REPLACED"]
    missing = details[details.kind == "CENTER_MISSING_FILL"]
    if len(finite) != 31 or len(missing) != 48:
        raise RuntimeError("Original 48 missing and 31 finite source provenance not conserved")
    groups = details.groupby("episode")
    summaries = []
    for e in events.itertuples(index=False):
        ep = int(e.episode)
        a = details[details.episode == ep]
        n_c = int((a.kind == "CENTER_MISSING_FILL").sum())
        n_n = int((a.kind == "EXISTING_QC1_QC2_REPLACED").sum())
        status = bool(str(e.research_numerical_pass).lower() == "true")
        if status and (n_c != int(e.seed_original_55_target_count)
                       or n_n != int(e.new_neighbors_would_change)):
            raise RuntimeError("Event patch composition mismatch for " + str(ep))
        summaries.append({
            "episode":ep, "seed_begin":e.seed_begin, "seed_end":e.seed_end,
            "original_centers":int(e.seed_original_55_target_count),
            "numerical_pass":status,
            "passed_missing_center_fills":n_c,
            "passed_existing_QC1_QC2_replacements":n_n,
            "maximum_abs_existing_VPD_change_hPa":float(
                a.abs_change_from_selected_hPa.max()) if n_n else np.nan,
            "existing_source_VPD_MDS_numeric_matches":int(
                a.loc[a.kind == "EXISTING_QC1_QC2_REPLACED", "source_VPD_equals_MDS"].sum()),
            "priority_manual_review":("HIGH_SCOPE_5PLUS_FINITE_NEIGHBORS" if n_n >= 5 else
                                      "SOURCE_PROVENANCE_REVIEW" if n_n else
                                      "CENTER_FILL_REVIEW") if status else
                                      "HELD_SOURCE_OR_BOUNDARY",
            "blocking_reasons":str(e.blocking_reasons) if not status else "",
            "operator_approval":False
        })
    summary = pd.DataFrame(summaries)
    if not (int(summary.passed_missing_center_fills.sum()) == 48
            and int(summary.passed_existing_QC1_QC2_replacements.sum()) == 31
            and int(summary.loc[summary.episode.isin([15,17]),
                 "passed_existing_QC1_QC2_replacements"].sum()) == 24):
        raise RuntimeError("Large event 15/17 source scope drifted")
    return details, summary

def main():
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    for s in ("self-test", "check", "run"):
        grp.add_argument("--" + s, action="store_true")
    a = ap.parse_args()
    print("STAGE12AO Kon ORIGINAL SOURCE & 79 PATCH SCIENCE REVIEW | " + VERSION, flush=True)
    selftest()
    if a.self_test:
        return
    details, summary = audit()
    print("\n====== 26 EPISODE REVIEW PRIORITIES ======", flush=True)
    print(summary.to_string(index=False), flush=True)
    finite = details[details.kind == "EXISTING_QC1_QC2_REPLACED"]
    print("\n====== 31 FINITE VPD SOURCE REPLACEMENTS (NOT YET APPROVED) ======", flush=True)
    print(finite.to_string(index=False), flush=True)
    print("\nSTAGE12AO SUMMARY | 48 center candidates, 31 finite QC1/QC2 neighbor replacements,",
          "24 neighbors in episodes 15+17; 7 blocked episodes, 2 hard source-T holds;",
          "0 operator approvals, 0 Post-v5/DATM/spinup releases", flush=True)
    if a.check:
        print("STAGE12AO CHECK ONLY | NO FILE WRITES", flush=True)
        return
    out = ROOT / "reports" / ("stage12ao_Kon_79_trial_source_provenance_READONLY_" +
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    files = {
        "79_trial_patch_source_VPD_QC_provenance_and_magnitude.csv":details,
        "26_connected_event_manual_review_priorities.csv":summary
    }
    for name, df in files.items():
        df.to_csv(out / name, index=False)
    note = (
        "SCIENCE REPORT ONLY, NOT A PRODUCTION FORCING FILE.\n"
        "48 prior-missing VPD/QBOT centers and 31 finite original QC1/QC2 neighbors "
        "are all still research candidates. Numerical continuity and QC1/MDS matching "
        "do not prove independent observations or justify replacement. Episodes 15 and "
        "17 account for 24/31 finite-neighbor modifications and require particular "
        "manual physical/source review. Seven events remain blocked; source-T exceptions "
        "201102220900 and 201109291830 remain protected. No Post-v5, DATM or spinup.\n"
    )
    (out / "SCIENCE_HOLD.md").write_text(note)
    digest = {name:sha(out / name) for name in [*files,"SCIENCE_HOLD.md"]}
    (out / "stage12ao_source_provenance_SHA_receipt.json").write_text(
        json.dumps({
            "version":VERSION,
            "source_stage12an_receipt_SHA256":sha(
                AN / "stage12an_research_only_55_source_event_SHA_receipt.json"),
            "passed_centers_research_only":48,
            "original_finite_QC1_QC2_neighbor_replacements_research_only":31,
            "seven_blocked_events_unchanged":True,
            "two_hard_source_temperature_holds_unchanged":True,
            "operator_approval":False, "Postv5_approved":False,
            "DATM_ready":False, "spinup_authorized":False,
            "output_SHA256":digest
        }, indent=2) + "\n")
    print("STAGE12AO SOURCE-PROVENANCE READ-ONLY REPORT DIR:", out, flush=True)
    print("NO SOURCE, PREVIOUS TRIAL, CIME, DATM OR MODEL INPUT WRITES.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE12AO STOP:", str(exc), file=sys.stderr, flush=True)
        raise

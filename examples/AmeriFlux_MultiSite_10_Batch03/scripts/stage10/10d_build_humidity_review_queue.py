#!/usr/bin/env python3
"""Batch03 Stage10d: provenance-checked, read-only prioritization of 1924 winter RH holds.

Inputs: exact Stage10c science-audit report (SHA-pinned to Stage10b and Stage08f).
Creates ranked MANUAL SCIENTIFIC REVIEW QUEUES, never forcing replacements.
--check performs in-memory checks only; --run creates a NEW isolated report.

Rank priorities are workload triage, NOT quality approval:
  P0: A transfer violates water-saturation (negative VPD or RH >100.05%);
      US-Me2 clock is also unresolved (independent clock hold).
  P1: B transfer implies >100% RH with respect to ice.
  P2: A transfer implies >100% RH with respect to ice.
  P3: abs(tower - grid temperature) >5 degC (elevation/scale caution).
  P4: any other record still needs full scientific evaluation.

Overlap among raw caution flags is preserved in separate columns.
MDS numeric availability is NOT MDS-at-retained-T physical validity or independent
tower evidence. No UTC offsets are approved by this script.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE10C = ROOT / "reports/stage10c_independent_cold_humidity_20261024T041355Z_36d578f4"
STAGE10B = ROOT / "reports/stage10b_external_humidity_20261024T040142Z_be6a9d78"
STAGE08F = ROOT / "reports/stage08f_mds_pairs_20261022T033321Z_7591f948"
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
EXPECTED = {"US-Kon": 229, "US-MMS": 18, "US-Me2": 4, "US-Me6": 1,
            "US-MtB": 15, "US-NR1": 173, "US-NR3": 1484}
KEYS = ["site", "source_csv_row", "time"]
REQUIRED = [
    "independent_A_physical_pass", "independent_B_physical_pass",
    "independent_A_ice_supersaturation_caution",
    "independent_B_ice_supersaturation_caution",
    "independent_A_ice_RH_pct", "independent_B_ice_RH_pct",
    "independent_tower_grid_delta_gt5C",
    "absolute_vpd_at_tower_T_hPa", "relative_vpd_at_tower_T_hPa",
    "absolute_rh_at_tower_T_pct", "relative_rh_at_tower_T_pct",
    "absolute_qbot_at_tower_P_kgkg", "relative_qbot_at_tower_P_kgkg",
    "TA_before_fallback_C", "grid_temperature_C", "grid_dewpoint_C",
    "grid_pressure_Pa", "PA_before_fallback_kPa", "VPD_before_fallback_hPa",
    "clock_approved", "clock_offset_hours_hypothesis",
    "utc_midpoint_hypothesis", "native_minutes",
    "MDS_VPD_valid_at_retained_TA", "MDS_pair_physical_screen_pass",
    "MDS_QC_both_0_or_1", "VPD_F_MDS",
    "scientific_hold_required", "independent_A_failure_reasons"
]


def file(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or symlink input file: " + str(path))
    return path


def folder(path):
    path = Path(path)
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Missing or symlink source directory: " + str(path))
    return path


def sha256(path):
    h = hashlib.sha256()
    with file(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def js(path):
    return json.loads(file(path).read_text(encoding="utf-8"))


def fields_bool(df, name):
    x = df[name].astype(str).str.strip().str.lower()
    if not x.isin(["true", "false", "1", "0"]).all():
        raise ValueError("Unexpected boolean field values: " + name)
    return x.isin(["true", "1"]).to_numpy(dtype=bool)


def number(df, field):
    x = pd.to_numeric(df[field], errors="coerce").to_numpy(dtype=float)
    x[(~np.isfinite(x)) | (x <= -9990)] = np.nan
    return x


def keys(frame):
    return set(map(tuple, frame[KEYS].to_numpy()))


def preflight():
    for d in (ROOT, STAGE10C, STAGE10B, STAGE08F, STAGE07):
        folder(d)
    file(STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    prior = js(STAGE10C / "provenance_and_science_hold.json")
    if (prior.get("repair_approvals") != 0
            or prior.get("all_clocks_formally_approved") is not False
            or "DO NOT WRITE FORCING" not in prior.get("science_hold", "")
            or Path(prior.get("source_10b_report", "")).resolve() != STAGE10B
            or prior.get("source_10b_manifest_sha256") !=
               sha256(STAGE10B / "provenance_and_science_hold.json")
            or prior.get("source_10b_event_sha256") !=
               sha256(STAGE10B / "humidity_external_sensitivity_1924.csv")
            or prior.get("source_08f_mds_sha256") !=
               sha256(STAGE08F / "mds_pair_at_1924_blockers.csv")):
        raise ValueError("Stage10c source provenance or scientific-hold status mismatch")
    expected_files = {
        "cold_humidity_independent_review_1924.csv",
        "absolute_transfer_27_failure_investigation.csv",
        "site_independent_science_summary.csv"
    }
    if set(prior.get("output_SHA256", {})) != expected_files:
        raise ValueError("Stage10c SHA receipt manifest differs")
    for name in expected_files:
        if sha256(STAGE10C / name) != prior["output_SHA256"][name]:
            raise ValueError("Stage10c output SHA mismatch: " + name)
    events = pd.read_csv(
        file(STAGE10C / "cold_humidity_independent_review_1924.csv"),
        dtype={name: str for name in KEYS}, low_memory=False, keep_default_na=False)
    failures = pd.read_csv(
        file(STAGE10C / "absolute_transfer_27_failure_investigation.csv"),
        dtype={name: str for name in KEYS}, low_memory=False, keep_default_na=False)
    sites = pd.read_csv(file(STAGE10C / "site_independent_science_summary.csv"))
    if not set(KEYS + REQUIRED).issubset(events.columns):
        missing = set(KEYS + REQUIRED) - set(events.columns)
        raise ValueError("Stage10c schema differs, missing: " + str(missing))
    if (len(events) != 1924 or events.duplicated(KEYS).any()
            or events.site.value_counts().to_dict() != EXPECTED
            or len(failures) != 27 or failures.duplicated(KEYS).any()
            or len(sites) != 7 or sites.blockers.sum() != 1924):
        raise ValueError("Stage10c event/failure/source count mismatch")
    a = fields_bool(events, "independent_A_physical_pass")
    b = fields_bool(events, "independent_B_physical_pass")
    ia = fields_bool(events, "independent_A_ice_supersaturation_caution")
    ib = fields_bool(events, "independent_B_ice_supersaturation_caution")
    temp = fields_bool(events, "independent_tower_grid_delta_gt5C")
    if (int((~a).sum()) != 27 or int(b.sum()) != 1924 or
            int(ia.sum()) != 170 or int(ib.sum()) != 78 or
            int(temp.sum()) != 150):
        raise ValueError("Stage10c independent physical/ice summary differs")
    if keys(failures) != keys(events.loc[~a]):
        raise ValueError("Stage10c 27-row failure file differs from A-rejected source events")
    if (fields_bool(events, "clock_approved").any()
            or not fields_bool(events, "scientific_hold_required").all()):
        raise ValueError("No future Stage10c report may proceed with clock or repair approval")
    mds = pd.read_csv(
        file(STAGE08F / "mds_pair_at_1924_blockers.csv"),
        dtype=str, keep_default_na=False)
    if (len(mds) != 1924 or mds.duplicated(KEYS).any()
            or keys(mds) != keys(events)
            or not set(KEYS+["MDS_VPD_valid_at_retained_TA",
                             "MDS_pair_physical_screen_pass",
                             "MDS_QC_both_0_or_1"]).issubset(mds.columns)):
        raise ValueError("Original Stage08f MDS event identities/source fields differ")
    for site, row in sites.set_index("site").iterrows():
        s = events.site.eq(site).to_numpy()
        if (int(row["blockers"]) != EXPECTED[site]
                or int(row["A_physical_pass"]) != a[s].sum()
                or int(row["B_physical_pass"]) != b[s].sum()
                or int(row["A_ice_RH_gt_100"]) != ia[s].sum()
                or int(row["B_ice_RH_gt_100"]) != ib[s].sum()):
            raise ValueError("Stage10c site summary and individual flags disagree")
    return events, mds, prior


def analyze(events, mds):
    # Stage10c records include finite numeric MDS VPD but that alone does NOT
    # mean a physically valid mixed MDS-tower humidity pair.
    details = events.merge(
        mds[KEYS + ["MDS_VPD_valid_at_retained_TA",
                    "MDS_pair_physical_screen_pass",
                    "MDS_QC_both_0_or_1"]],
        how="inner", on=KEYS, validate="one_to_one",
        suffixes=("", "_stage08f"))
    if len(details) != 1924:
        raise ValueError("MDS provenance join did not preserve 1924 identities")
    if not np.array_equal(
        fields_bool(details, "MDS_VPD_valid_at_retained_TA"),
        fields_bool(details, "MDS_VPD_valid_at_retained_TA_stage08f")):
        raise ValueError("Stage10c and Stage08f MDS validity disagree")
    a = fields_bool(details, "independent_A_physical_pass")
    b = fields_bool(details, "independent_B_physical_pass")
    ia = fields_bool(details, "independent_A_ice_supersaturation_caution")
    ib = fields_bool(details, "independent_B_ice_supersaturation_caution")
    temp = fields_bool(details, "independent_tower_grid_delta_gt5C")
    mdspair = fields_bool(details, "MDS_pair_physical_screen_pass")
    mdsret = fields_bool(details, "MDS_VPD_valid_at_retained_TA")
    qc01 = fields_bool(details, "MDS_QC_both_0_or_1")
    clock = details.site.eq("US-Me2").to_numpy(dtype=bool)
    if int((~a).sum()) != 27 or not b.all() or int(ib.sum()) != 78:
        raise ValueError("Stage10c review flag counts changed unexpectedly")
    conditions = [
        ~a, clock, ib, ia, temp
    ]
    names = [
        "P0_ABSOLUTE_NEGATIVE_VPD_OR_RH_GT100_WATER",
        "P0_US_ME2_RELEASE_CLOCK_UNRESOLVED",
        "P1_RELATIVE_TRANSFER_ICE_SUPERSATURATION",
        "P2_ABSOLUTE_TRANSFER_ICE_SUPERSATURATION",
        "P3_TOWER_GRID_TEMPERATURE_DIFFERENCE_GT5C",
    ]
    details["review_priority"] = np.select(
        conditions, names, default="P4_GENERAL_COLD_HUMIDITY_REVIEW")
    details["flag_A_water_failure"] = ~a
    details["flag_B_ice_supersaturation"] = ib
    details["flag_A_ice_supersaturation"] = ia
    details["flag_tower_grid_T_gt5C"] = temp
    details["flag_clock_US_Me2_unverified"] = clock
    details["mds_VPD_valid_at_retained_tower_temperature"] = mdsret
    details["mds_pair_physically_consistent"] = mdspair
    details["mds_both_QC0_or_QC1"] = qc01
    details["mds_pair_physical_and_QC01"] = mdspair & qc01
    details["candidate_A_approved"] = False
    details["candidate_B_approved"] = False
    details["decision"] = "MANUAL_SCIENCE_REVIEW_NO_FORCING_CHANGE"

    # Consecutive event clustering by original LOCAL timestamps, preserving
    # native 30/60 minute records without interpolating missing tower events.
    details = details.sort_values(["site", "time", "source_csv_row"]).reset_index(drop=True)
    details["native_local_datetime"] = pd.to_datetime(details.time, errors="raise")
    detail_parts = []
    clusters = []
    for site, group in details.groupby("site", sort=True):
        group = group.sort_values("native_local_datetime").copy()
        step = int(group.native_minutes.iloc[0])
        if not group.native_minutes.astype(int).eq(step).all():
            raise ValueError("Mixed native interval within site")
        dt = group.native_local_datetime.diff()
        start = dt.ne(pd.Timedelta(minutes=step))
        start.iloc[0] = True
        group["sequence"] = start.cumsum().astype(int)
        for seq, chunk in group.groupby("sequence", sort=True):
            ident = f"{site}_cluster_{seq:04d}"
            group.loc[chunk.index, "event_cluster_id"] = ident
            clusters.append({
                "cluster": ident, "site": site, "records": len(chunk),
                "start_local": str(chunk.native_local_datetime.min()),
                "end_local": str(chunk.native_local_datetime.max()),
                "A_fail_count": int(chunk.flag_A_water_failure.sum()),
                "B_ice_count": int(chunk.flag_B_ice_supersaturation.sum()),
                "A_ice_count": int(chunk.flag_A_ice_supersaturation.sum()),
                "T_grid_gt5C_count": int(chunk.flag_tower_grid_T_gt5C.sum()),
                "MDS_pair_physically_consistent": int(chunk.mds_pair_physically_consistent.sum()),
                "review_status": "UNAPPROVED"
            })
        detail_parts.append(group)
    detail = pd.concat(detail_parts, ignore_index=True)
    overlap = pd.crosstab(detail["flag_A_water_failure"], detail["flag_B_ice_supersaturation"])
    summary = []
    for site, frame in detail.groupby("site", sort=True):
        summary.append({
            "site":site, "events":len(frame),
            "priority_P0":int(frame.review_priority.str.startswith("P0_").sum()),
            "priority_P1":int(frame.review_priority.str.startswith("P1_").sum()),
            "priority_P2":int(frame.review_priority.str.startswith("P2_").sum()),
            "priority_P3":int(frame.review_priority.str.startswith("P3_").sum()),
            "priority_P4":int(frame.review_priority.str.startswith("P4_").sum()),
            "A_failed":int(frame.flag_A_water_failure.sum()),
            "A_ice_supersaturated":int(frame.flag_A_ice_supersaturation.sum()),
            "B_ice_supersaturated":int(frame.flag_B_ice_supersaturation.sum()),
            "tower_grid_gt5C":int(frame.flag_tower_grid_T_gt5C.sum()),
            "MDS_numeric_VPD":int(np.isfinite(number(frame, "VPD_F_MDS")).sum()),
            "MDS_VPD_valid_at_retained_T":int(frame.mds_VPD_valid_at_retained_tower_temperature.sum()),
            "MDS_pair_physical_and_QC01":int(frame.mds_pair_physical_and_QC01.sum()),
            "approved_replacements":0
        })
    triage = pd.DataFrame(summary)
    if triage.events.sum() != 1924 or sum(triage[f"priority_P{i}"].sum() for i in range(5)) != 1924:
        raise ValueError("Priority categories do not partition the 1924 records")
    if not (detail.candidate_A_approved.eq(False).all() and
            detail.candidate_B_approved.eq(False).all()):
        raise ValueError("Unexpected candidate approval")
    return detail, triage, pd.DataFrame(clusters), overlap


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = p.parse_args()
    print("STAGE10D — COLD-HUMIDITY SCIENTIFIC REVIEW TRIAGE", flush=True)
    events, mds, manifest = preflight()
    detail, summary, clusters, overlap = analyze(events, mds)
    print("STAGE10D INPUT SHA/IDENTITY PASS: 1924 events, Stage10c 27 failures,"
          " Stage10b/Stage08f provenance intact", flush=True)
    print("\nPRIORITY COUNTS BY SITE (PRIORITIES MUTUALLY EXCLUSIVE):")
    print(summary.to_string(index=False), flush=True)
    print("\nA WATER FAILURE x B ICE SUPER-SATURATION OVERLAP:")
    print(overlap.to_string(), flush=True)
    print(f"\nSTAGE10D SUMMARY: reviewed={len(detail)}/1924 "
          f"A_failed={int(detail.flag_A_water_failure.sum())}/27 "
          f"B_ice={int(detail.flag_B_ice_supersaturation.sum())}/78 "
          f"A_ice={int(detail.flag_A_ice_supersaturation.sum())}/170 "
          f"tower_grid_gt5C={int(detail.flag_tower_grid_T_gt5C.sum())}/150 "
          f"event_clusters={len(clusters)} repair_approvals=0", flush=True)
    print("SCIENTIFIC HOLD: no proven humidity correction, no approved timezone.", flush=True)
    if args.check:
        print("CHECK ONLY: no report, forcing, DATM, cases, or Slurm jobs created.",flush=True)
        return
    output = ROOT/"reports"/("stage10d_humidity_manual_triage_" +
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    output.mkdir(exist_ok=False)
    files = {
        "all_1924_manual_review.csv":detail,
        "site_triage_summary.csv":summary,
        "consecutive_event_clusters.csv":clusters,
        "P0_high_priority_events.csv":detail.loc[detail.review_priority.str.startswith("P0_")],
        "B_ice_supersaturation_78.csv":detail.loc[detail.flag_B_ice_supersaturation],
        "A_water_failure_27.csv":detail.loc[detail.flag_A_water_failure],
    }
    for name, data in files.items():
        data.to_csv(output/name, index=False)
    receipt = {
        "source_stage10c":str(STAGE10C),
        "source_stage10c_receipt_sha256":sha256(STAGE10C/"provenance_and_science_hold.json"),
        "source_stage10b":str(STAGE10B),
        "source_stage08f":str(STAGE08F),
        "events":len(detail),
        "priorities_are_approval":False,
        "no_replacement_approved":True,
        "phase_basis":"water saturation used for liquid-water transfer checks, ice RH diagnostic only",
        "source_qa":"MDS values can be gapfilled; MDS_VPD_valid_at_retained_T is not an independence guarantee",
        "review_requirement":"All 1924 require science approval; additional clock, site-height, provenance and cold-season QC review pending",
        "output_sha256":{name:sha256(output/name) for name in files}
    }
    (output/"read_only_provenance.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE10D REPORT DIR:",output,flush=True)
    print("ISOLATED REPORT ONLY: no original data, candidate forcing, model jobs or QC markers changed.")


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE10D STOP:",str(exc),file=sys.stderr,flush=True)
        raise SystemExit(2)

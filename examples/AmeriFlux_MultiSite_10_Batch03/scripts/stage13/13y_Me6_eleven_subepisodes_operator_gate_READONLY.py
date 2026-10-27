#!/usr/bin/env python3
"""Stage13Y: immutable-source decision gate for the six held US-Me6 QC1 runs.

Consumes only SHA-verified, already-run Stage13V and Stage13X science
reports. Identifies the rare fully measured-QC0 bounded candidate for
HUMAN REVIEW; never authorizes a forcing replacement, Stage13s changes,
Stage12ac changes, Post-v5, DATM, AD400 or SLURM jobs.

--self-test uses synthetic records, no IRIDIS files.
--check verifies existing reports, reads only.
--run creates only a SHA-sealed report directory under reports/.
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
VERSION = "batch03-stage13y-v1-20261027-Me6-11-subgroups-strict-operator-gate"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
V = ROOT / "reports/stage13v_Me6_14_source_QC1_failures_BATCH_READONLY_20261027T083537Z_7151cdf8"
X = ROOT / "reports/stage13x_Me6_QC0_ERA_RH_empirical_skill_and_2017_QC2_edges_20261027T140953Z_342b79ec"
V_REC = "stage13v_sha_receipt.json"
X_REC = "stage13x_original_QC0_ERA_RH_reliability_SHA_receipt.json"
V_CAND = "science_valid_QC1_contiguous_groups_PROPOSALS_ONLY.csv"
V_GROUPS = "six_remaining_source_QC1_full_runs_science_HOLD.csv"
X_HOLDS = "14_original_site_ERA_Tdelta_GT8C_science_HOLD_preserved.csv"
X_EDGES = "eight_2017_original_source_QC2_immediate_edge_original_vs_ERA.csv"
X_SKILL = "six_original_source_runs_QC0_observed_vs_ERA_RH_skill_windows.csv"
X_SUMMARY = "stage13x_six_run_source_skill_summary.json"
SOURCE_COUNTS = {12: 4, 14: 469, 15: 95, 16: 30, 17: 137, 18: 47}
FAILED_COUNTS = {14: 5, 15: 8, 17: 1}
MAX_ERA_T_DIFF_C = 8.0
MAX_VPD_JUMP_HPA = 4.0
ORIGINAL_STAGE13S_SHA = "02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"


def need(test, message):
    if not bool(test):
        raise RuntimeError("STAGE13Y SCIENCE HOLD: " + str(message))


def existing(path):
    p = Path(path)
    need(p.is_file() and not p.is_symlink(), "missing/symlink signed evidence: " + str(p))
    return p


def sha256(path):
    h = hashlib.sha256()
    with existing(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def flags(s):
    v = s.astype(str).str.strip().str.lower()
    need(v.isin(("true", "false")).all(), "unrecognized provenance boolean")
    return v.eq("true").to_numpy(dtype=bool)


def decision(both_qc0, internal_le_4, is_2017):
    if is_2017:
        return "HOLD_2017_QC2_BOUNDARY_NOT_OBSERVED_QC0"
    if not internal_le_4:
        return "HOLD_INTERNAL_30MIN_VPD_JUMP"
    if not both_qc0:
        return "HOLD_NO_TWO_DIRECT_MEASURED_QC0_BOOKENDS"
    return "ELIGIBLE_FOR_SEPARATE_HUMAN_REVIEW_NOT_APPROVED"


def selftest():
    need(sum(SOURCE_COUNTS.values()) == 782 and sum(FAILED_COUNTS.values()) == 14,
         "original source exact sample sizes")
    need(decision(True, True, False).startswith("ELIGIBLE_"),
         "strict 2015 paired QC0 candidate must be review only")
    need(decision(True, False, False).startswith("HOLD_"),
         "internal VPD discontinuity must HOLD")
    need(decision(False, True, False).startswith("HOLD_"),
         "distant QC0 is not source boundary")
    need(decision(True, True, True).startswith("HOLD_"),
         "2017 QC2 protection must override superficial QC0 flags")
    print("STAGE13Y SELF-TEST PASS | candidate review gate, 14 T holds, 8 QC2 edges; NO WRITES", flush=True)


def signed(folder, receipt_name, expected_version, outputs_key, wanted):
    receipt = json.loads(existing(folder / receipt_name).read_text())
    need(receipt.get("version") == expected_version and receipt.get("site") == "US-Me6",
         "signed original evidence version/site drift")
    outputs = receipt.get(outputs_key, {})
    need(set(outputs) == set(wanted), "signed source report inventory drift")
    for name, digest in outputs.items():
        need("/" not in name and "\\" not in name and sha256(folder / name) == digest,
             "signed original report SHA mismatch: " + name)
    return receipt


def assess():
    vr = signed(
        V, V_REC, "batch03-stage13v-v1-Me6-14-exact-original-science-failures",
        "outputs_SHA256", [
            "14_original_source_failed_ERA_physics_HH.csv", V_CAND, V_GROUPS,
            "stage13v_science_review_summary.json",
            "SOURCE_ONLY_NO_QC1_NEIGHBOR_APPROVAL_OR_FORCING",
        ])
    xr = signed(
        X, X_REC, "batch03-stage13x-v1-20261027-Me6-QC0-ERA-RH-reliability-and-2017-QC2",
        "output_SHA256", [
            X_SKILL, X_EDGES, X_HOLDS, "nearby_48h_original_measured_QC0_skill_context.csv",
            X_SUMMARY, "READONLY_QC0_CONTEXT_NOT_2017_QC2_SOURCE_APPROVAL",
        ])
    need(vr.get("operator_new_approval") is False and vr.get("forcing_generated") is False,
         "original Stage13V scope no longer a pure science review")
    need(xr.get("research_report_only") is True and xr.get("operator_science_approval") is False
         and xr.get("original_Stage13s_research_forcing_SHA256") == ORIGINAL_STAGE13S_SHA,
         "Stage13X signature or preserved Stage13s forcing SHA changed")
    summary = json.loads(existing(X / X_SUMMARY).read_text())
    need(summary.get("six_remaining_full_source_QC1_runs_checked") == 6
         and summary.get("14_original_source_site_ERA_temperature_GT8C_HOLD_untouched") == 14
         and summary.get("2017_original_immediate_VPD_QC2_edges_reviewed") == 8
         and summary.get("Stage13s_235HH_preserved") is True
         and summary.get("Stage12ac_2017_five_preserved") is True
         and summary.get("source_or_forcing_modified") is False
         and summary.get("new_QC1_QC2_operator_repair_approvals") is False,
         "Stage13X immutable original science status changed")
    cand = pd.read_csv(existing(V / V_CAND), low_memory=False)
    groups = pd.read_csv(existing(V / V_GROUPS), low_memory=False)
    holds = pd.read_csv(existing(X / X_HOLDS), dtype={"native_time": str}, low_memory=False)
    edges = pd.read_csv(existing(X / X_EDGES), low_memory=False)
    skill = pd.read_csv(existing(X / X_SKILL), low_memory=False)
    need(len(cand) == 11 and len(groups) == 6 and len(holds) == 14
         and holds.native_time.is_unique and len(edges) == 8 and len(skill) == 24,
         "11 / 6 / 14 / 8 / 24 signed source evidence record count mismatch")
    need(set(groups.run_id.astype(int)) == set(SOURCE_COUNTS)
         and dict(zip(groups.run_id.astype(int), groups.original_QC1_native_HH.astype(int)))
             == SOURCE_COUNTS
         and dict(zip(
             groups.loc[groups.source_science_failure_HH.astype(int) > 0, "run_id"].astype(int),
             groups.loc[groups.source_science_failure_HH.astype(int) > 0,
                        "source_science_failure_HH"].astype(int))) == FAILED_COUNTS,
         "historical native runs and 14 source-temperature failure identities drift")
    need(int(groups.original_QC1_native_HH.sum()) == 782
         and int(groups.paired_ERA_source_physics_PASS.sum()) == 768
         and int(groups.protected_Stage12ac_2017_native_HH.sum()) == 5
         and int(groups.new_source_QC1_neighbors_still_unapproved.sum()) == 761,
         "original 782 / 768 / 5 / 761 science counts changed")
    need(np.isfinite(holds.abs_site_minus_ERA_T_C.to_numpy(float)).all()
         and (holds.abs_site_minus_ERA_T_C.to_numpy(float) > MAX_ERA_T_DIFF_C).all()
         and holds.groupby("source_original_full_run_id").size().to_dict() == FAILED_COUNTS,
         "14 strict site-ERA T>8C original failure causes differ")
    need((edges.original_source_VPD_F_QC.astype(int) == 2).all()
         and tuple(sorted(edges.original_full_QC1_run_id.unique())) == (15, 16, 17, 18)
         and set(edges.immediate_original_source_QC2_side) == {"PRE", "POST"}
         and flags(edges.QC2_source_neighbour_substitution_UNAPPROVED).all(),
         "2017 source QC2 direct boundary status differs")

    gate = cand.copy()
    gate["run_id"] = gate.run_id.astype(int)
    need(gate.run_id.isin(SOURCE_COUNTS).all(), "unknown original source run")
    both = flags(gate.both_original_DIRECT_QC0_boundaries_verified)
    internal = flags(gate.paired_ERA_physics_and_internal_VPD_le_4hPa)
    gate["strict_review_status"] = [
        decision(bool(b), bool(i), int(run_id) in (15, 16, 17, 18))
        for b, i, run_id in zip(both, internal, gate.run_id)
    ]
    gate["operator_approved"] = False
    gate["forcing_change_allowed"] = False
    need(int(both.sum()) == 1, "signed source requires exactly one two-QC0-bounded subgroup")
    for _, row in gate.iterrows():
        start = pd.Timestamp(row.source_native_start)
        end = pd.Timestamp(row.source_native_end)
        need(end >= start and int((end - start) / pd.Timedelta(minutes=30)) + 1
             == int(row.source_native_30min_HH),
             "source subgroup original native timestamps not contiguous")
    edge = edges.copy()
    edge["delta_over_4hPa"] = (
        pd.to_numeric(edge.abs_old_selected_VPD_minus_hypothetical_ERA_hPa,
                      errors="raise") > MAX_VPD_JUMP_HPA
    )
    edge["edge_substitution_approved"] = False
    edge["gate"] = "HOLD_QC2_NOT_DIRECT_MEASURED_QC0"
    hold = holds.copy()
    hold["gate"] = "HOLD_SITE_VS_ERA_T_GT8C_NO_TEMP_OVERWRITE"
    hold["ERA_RH_override_allowed"] = False

    result = {
        "version": VERSION, "site": "US-Me6",
        "stage13v_signed_receipt_SHA256": sha256(V / V_REC),
        "stage13x_signed_receipt_SHA256": sha256(X / X_REC),
        "unchanged_Stage13s_selected_forcing_SHA256": ORIGINAL_STAGE13S_SHA,
        "original_six_QC1_run_HH": 782,
        "original_ERA_RH_and_temperature_gate_PASS_HH": 768,
        "original_site_ERA_T_GT8C_HOLD_HH": 14,
        "source_contiguous_subepisodes_reviewed": 11,
        "two_measured_QC0_bookend_subepisodes": int(both.sum()),
        "possible_2015_subepisode_human_review_only": int(
            gate.strict_review_status.str.startswith("ELIGIBLE_").sum()),
        "unapproved_new_QC1_neighbors": 761,
        "protected_Stage13s_2015_HH": 235,
        "protected_Stage12ac_2017_HH": 5,
        "2017_QC2_edges_not_authorized": len(edge),
        "2017_QC2_edges_ERA_vs_selected_delta_GT4hPa": int(edge.delta_over_4hPa.sum()),
        "all_six_original_source_full_runs_still_HOLD": True,
        "operator_science_approval": False,
        "source_or_forcing_modified": False,
        "postv5_approved": False, "DATM": False, "AD400": False, "Slurm": False,
    }
    print("STAGE13Y 11 ORIGINAL SCIENCE SUBEPISODES / STRICT REVIEW GATE", flush=True)
    print(gate[["run_id", "source_native_start", "source_native_end",
                "source_native_30min_HH", "strict_review_status"]].to_string(index=False),
          flush=True)
    print("STAGE13Y 2017 ORIGINAL QC2 EDGES / UNAPPROVED", flush=True)
    print(edge[["original_full_QC1_run_id", "immediate_original_source_QC2_side",
                "abs_old_selected_VPD_minus_hypothetical_ERA_hPa", "delta_over_4hPa"]]
          .to_string(index=False), flush=True)
    print("STAGE13Y SUMMARY", json.dumps(result, indent=2), flush=True)
    return gate, hold, edge, result


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    for m in ("self-test", "check", "run"):
        mode.add_argument("--" + m, action="store_true")
    args = parser.parse_args()
    selftest()
    if args.self_test:
        return
    gate, hold, edge, result = assess()
    if args.check:
        print("STAGE13Y READONLY CHECK PASS | immutable 11/14/8 gate; NO WRITES", flush=True)
        return
    out = ROOT / "reports" / (
        "stage13y_Me6_11subgroups_14T_8QC2_STRICT_HUMAN_GATE_READONLY_"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    frames = {
        "11_original_QC1_science_subepisodes_gate_NO_APPROVAL.csv": gate,
        "14_original_T_GT8C_strict_HOLD_no_replacement.csv": hold,
        "8_original_2017_QC2_edges_strict_HOLD_no_replacement.csv": edge,
    }
    for name, data in frames.items():
        data.to_csv(out / name, index=False, float_format="%.17g")
    report = "stage13y_immutable_repair_decision_summary.json"
    marker = "SOURCE_SCIENCE_ONLY_NO_OPERATOR_APPROVAL_OR_DATM"
    (out / report).write_text(json.dumps(result, indent=2) + "\n")
    (out / marker).write_text(
        "Potential subgroup eligibility is NOT human/operator approval. "
        "Original source QC2 borders and T-vs-ERA >8C HOLD remain unchanged. "
        "No new forcing, Post-v5, DATM, AD400 or SLURM job is authorized.\n")
    receipt = {
        "version": VERSION, "site": "US-Me6",
        "stage13v_receipt_SHA256": sha256(V / V_REC),
        "stage13x_receipt_SHA256": sha256(X / X_REC),
        "original_Stage13s_forcing_SHA256": ORIGINAL_STAGE13S_SHA,
        "new_operator_approval": False, "forcing_written": False,
        "outputs_SHA256": {n: sha256(out / n)
                           for n in [*frames, report, marker]},
    }
    (out / "stage13y_signed_READONLY_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print("STAGE13Y READONLY REPORT DIR:", out, flush=True)
    print("STAGE13Y REPORT COMPLETE | 11 groups, 14 T holds, 8 QC2 edges; NO FORCING/DATM/SLURM",
          flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE13Y SCIENCE STOP:", exc, file=sys.stderr, flush=True)
        traceback.print_exc()
        raise SystemExit(2)

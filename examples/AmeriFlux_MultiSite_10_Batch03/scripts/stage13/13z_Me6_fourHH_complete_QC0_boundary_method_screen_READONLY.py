#!/usr/bin/env python3
"""US-Me6 Batch03 Stage13Z: full-boundary method check for 2015 Run12.

The previous Stage13Y correctly allowed *human review* of the four QC1
half-hours, but its internal-edge check alone is insufficient to admit
the ERA RH replacement. The signed Stage13T established that the full
six-node ERA-at-site-T trajectory jumps 4.800355 hPa (>4).

This read-only gate compares unchanged tower QC0 bookends, old VPD,
ERA RH VPD and hypothetical QC0-anchored VPD/QBOT linear interpolation.
Source signed Stage13T + Stage13Y required. No forcing or approval.
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
VER = "batch03-stage13z-v2-20261027-Me6-source-QC1-NaN-aware-full-edge"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
T = ROOT / "reports/stage13t_Me6_20150926_four_QC1_original_QC0_ERA_RH_READONLY_20261027T071247Z_a30c3a4e"
Y = ROOT / "reports/stage13y_Me6_11subgroups_14T_8QC2_STRICT_HUMAN_GATE_READONLY_20261027T142119Z_e2ee7e1b"
T_REC = "stage13t_Me6_four_QC1_original_QC0_SHA_receipt.json"
T_CONTEXT = "original_source_QC_ERA_RH_siteT_VPD_QBOT_native_context_20150926.csv"
T_EDGES = "five_source_native_30min_edges_ERA_RH_vs_QC0_anchor_preview.csv"
T_SUMMARY = "stage13t_Sep26_four_QC1_HOLD_explanation.json"
Y_REC = "stage13y_signed_READONLY_receipt.json"
Y_GROUP = "11_original_QC1_science_subepisodes_gate_NO_APPROVAL.csv"
Y_SUMMARY = "stage13y_immutable_repair_decision_summary.json"
STAGE13S_SHA = "02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
START = pd.Timestamp("2015-09-26 05:00:00")
END = pd.Timestamp("2015-09-26 06:30:00")
TIMES = pd.date_range(START - pd.Timedelta(minutes=30),
                      END + pd.Timedelta(minutes=30), freq="30min")
TARGET = TIMES[1:-1]
MAX_STEP = 4.0


def need(cond, why):
    if not bool(cond):
        raise RuntimeError("STAGE13Z SOURCE HOLD: " + why)


def existing(p):
    p = Path(p)
    need(p.is_file() and not p.is_symlink(), "missing or unsafe original signed file: " + str(p))
    return p


def sha(p):
    h = hashlib.sha256()
    with existing(p).open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def bools(x):
    x = x.astype(str).str.lower().str.strip()
    need(x.isin(("true", "false")).all(), "invalid original booleans")
    return x.eq("true").to_numpy(dtype=bool)


def es(t):
    return 6.112 * np.exp(17.67 * t / (t + 243.5))


def q_from_vpd(v, temp_c, pressure_pa):
    sat = es(temp_c)
    ea_pa = (sat - v) * 100.0
    return .622 * ea_pa / (pressure_pa - .378 * ea_pa)


def selftest():
    need(len(TIMES) == 6 and len(TARGET) == 4, "exact original site sequence")
    need(all(TIMES[i + 1] - TIMES[i] == pd.Timedelta(minutes=30)
             for i in range(5)), "original source 30min cadence")
    t, p, v = 7., 99000., 3.
    need(0 < v < es(t) and 0 < q_from_vpd(v, t, p) < .08,
         "actual water thermodynamics at retained T / PSRF")
    need(4.800355 > MAX_STEP, "full interval source HOLD must not be relaxed")
    print("STAGE13Z SELF-TEST PASS | all 5 boundaries, 4 native QC1, physics, no writes", flush=True)


def signed(folder, receipt_name, field, version, expected):
    r = json.loads(existing(folder / receipt_name).read_text())
    need(r.get("version") == version and r.get("site") == "US-Me6",
         "old SHA receipt version/site drift")
    files = r.get(field, {})
    need(set(files) == set(expected), "old signed output inventory changed")
    for name, digest in files.items():
        need("/" not in name and "\\" not in name and sha(folder / name) == digest,
             "old scientific output SHA changed: " + name)
    return r


def audit():
    tr = signed(
        T, T_REC, "files_SHA256",
        "batch03-stage13t-v1-20261027-Me6-four-20150926-QC1-QC0-source-science",
        [T_CONTEXT, T_EDGES, T_SUMMARY,
         "READONLY_NO_FORCING_OR_2015SEP26_OPERATOR_REPAIR_APPROVAL"])
    yr = signed(
        Y, Y_REC, "outputs_SHA256",
        "batch03-stage13y-v1-20261027-Me6-11-subgroups-strict-operator-gate",
        [Y_GROUP, "14_original_T_GT8C_strict_HOLD_no_replacement.csv",
         "8_original_2017_QC2_edges_strict_HOLD_no_replacement.csv",
         Y_SUMMARY, "SOURCE_SCIENCE_ONLY_NO_OPERATOR_APPROVAL_OR_DATM"])
    need(tr.get("stage13s_signed_existing_shadow_SHA256") == STAGE13S_SHA
         and tr.get("new_science_or_operator_repair_authorization") is False
         and tr.get("new_model_forcing_written") is False
         and yr.get("original_Stage13s_forcing_SHA256") == STAGE13S_SHA
         and yr.get("new_operator_approval") is False
         and yr.get("forcing_written") is False,
         "protected previous Stage13s original or operator-approval marker differs")
    s = json.loads(existing(T / T_SUMMARY).read_text())
    sy = json.loads(existing(Y / Y_SUMMARY).read_text())
    need(s.get("original_Stage13r_held_full_run_ID") == 12
         and abs(float(s.get("source_ERA_RH_at_siteT_max_native_jump_hPa"))-4.800355)<1e-6
         and s.get("hypothetical_QC0_anchor_linear_science_method_NOT_approved") is True
         and s.get("operator_has_NOT_approved_run_12_source_4HH_repair") is True
         and sy.get("original_six_QC1_run_HH") == 782
         and sy.get("all_six_original_source_full_runs_still_HOLD") is True
         and sy.get("possible_2015_subepisode_human_review_only") == 1,
         "original source science evidence or six held runs changed")
    c = pd.read_csv(existing(T / T_CONTEXT), low_memory=False)
    e = pd.read_csv(existing(T / T_EDGES), low_memory=False)
    g = pd.read_csv(existing(Y / Y_GROUP), low_memory=False)
    need(len(c) == 18 and len(e) == 5 and len(g) == 11,
         "actual 18-context, 5-edge or 11-science grouping changed")
    c["native_time"] = pd.to_datetime(c.native_time, errors="raise")
    need(c.native_time.is_unique, "source native times duplicated")
    core = c.set_index("native_time").loc[TIMES].copy()
    need(len(core) == 6 and core.index.is_monotonic_increasing,
         "original exact measured-QC0/ERA source 6-node sequence changed")
    need(bools(core.true_measured_QC0_bookend)[[0,5]].all()
         and not bools(core.true_measured_QC0_bookend)[1:5].any(),
         "measured QC0 source anchors differ")
    need((core.original_tower_VPD_F_QC.iloc[[0,5]].to_numpy(float)==0).all()
         and (core.original_tower_VPD_F_QC.iloc[1:5].to_numpy(float)==1).all()
         and (core.original_tower_TA_F_QC.iloc[1:5].to_numpy(float)==0).all(),
         "original measured QC0 anchors/QC1 T-QC0 source provenance changed")
    need((core.in_original_4HH_QC1_HOLD_scope.to_numpy(dtype=bool)[1:5]).all(),
         "original exact 2015 four native QC1 source timestamps changed")
    gg = g.loc[g.run_id.eq(12)]
    need(len(gg)==1 and int(gg.iloc[0].source_native_30min_HH)==4
         and gg.iloc[0].strict_review_status ==
              "ELIGIBLE_FOR_SEPARATE_HUMAN_REVIEW_NOT_APPROVED",
         "Stage13Y preliminary human review scope differs")

    old = core.unchanged_Stage13s_selected_VPD_hPa.to_numpy(float)
    era = core.HYPOTHETICAL_ERA_RH_at_siteT_VPD_hPa.to_numpy(float)
    linear = core.HYPOTHETICAL_QC0_bookend_linear_VPD_hPa.to_numpy(float)
    # OLD unapproved QC1 selected values can be NaN in the original forcing.
    # That is why these four HH are under source repair review. Never use
    # those missing values as a blanket rejection of independently sampled
    # tower QC0 anchors and complete hypothetical candidate nodes.
    # Both true QC0 anchors, all six QC0-linear values and four candidate
    # ERA-RH QC1 values MUST be finite; no relaxation of any 4 hPa edge.
    old_missing_qc1 = ~np.isfinite(old[1:5])
    need(np.isfinite(old[[0, 5]]).all()
         and np.isfinite(linear).all() and np.isfinite(era[1:5]).all(),
         "non-finite true QC0 bookend or independently calculated candidate VPD")
    need(np.allclose(old[[0, 5]],
                     core.original_tower_VPD_F_hPa.to_numpy(float)[[0, 5]],
                     rtol=0, atol=1e-7),
         "old selected forcing QC0 bookends do not match original measured tower")
    need(np.allclose(linear[[0,5]], old[[0,5]], atol=1e-9, rtol=0),
         "measured QC0 anchors not exactly preserved")
    era[[0,5]] = old[[0,5]]
    era_step = np.abs(np.diff(era))
    lin_step = np.abs(np.diff(linear))
    need(np.allclose(era_step, e.candidate_ERA_RH_with_measured_QC0_step_hPa.to_numpy(float),
                     rtol=0, atol=1e-6)
         and np.allclose(lin_step, e.HYPOTHETICAL_anchor_linear_VPD_step_hPa.to_numpy(float),
                         rtol=0, atol=1e-6),
         "Stage13T signed full-boundary arithmetic mismatch")
    need(abs(era_step.max()-4.800355) < 1e-6 and era_step.max()>MAX_STEP,
         "ERA source >4hPa full-boundary HOLD cannot be overridden")
    temperatures = core.retained_original_site_TA_USE_C.to_numpy(float)
    pressure = core.retained_original_PSRF_Pa.to_numpy(float)
    q = np.array([q_from_vpd(v, t, p)
                  for v,t,p in zip(linear,temperatures,pressure)], dtype=float)
    physical = np.isfinite(q) & (q>0) & (q<.08) & \
               (linear>0) & (linear<es(temperatures)) & \
               (pressure>50000) & (pressure<110000)
    need((np.isclose(q[1:5],
              core.HYPOTHETICAL_QC0_bookend_linear_QBOT_kgkg.to_numpy(float)[1:5],
              atol=1e-9,rtol=0)).all(),
         "Stage13T stored linear QBOT and physical calculation differ")
    need(bools(core.HYPOTHETICAL_linear_VPD_QBOT_physics_PASS.iloc[1:5]).tolist()
         == physical[1:5].tolist(),
         "original source linear QC1 thermodynamic validity differs")
    eligible = bool(physical.all() and (lin_step<=MAX_STEP+1e-12).all())
    edges = pd.DataFrame({
        "native_from":[str(x) for x in TIMES[:-1]],
        "native_to":[str(x) for x in TIMES[1:]],
        "old_retained_VPD_step_hPa":np.abs(np.diff(old)),
        "ERA_RH_candidate_VPD_step_hPa":era_step,
        "QC0_anchor_linear_VPD_step_hPa":lin_step,
        "ERA_full_edge_le_4hPa":era_step<=MAX_STEP,
        "QC0_linear_full_edge_le_4hPa":lin_step<=MAX_STEP,
        "method_operator_approved":False,
    })
    rows = core.reset_index().copy()
    rows["full_edge_ERA_RH_VPD_hPa"] = era
    rows["full_edge_QC0_anchor_linear_VPD_hPa"] = linear
    rows["full_edge_QC0_anchor_linear_QBOT_kgkg"] = q
    rows["QC0_linear_physical_at_original_T_P"] = physical
    rows["original_retained_VPD_missing"] = ~np.isfinite(old)
    rows["new_forcing_approved"] = False
    stats = {
        "version":VER,"site":"US-Me6",
        "actual_Stage13T_signed_receipt_SHA256":sha(T/T_REC),
        "actual_Stage13Y_signed_receipt_SHA256":sha(Y/Y_REC),
        "preserved_original_Stage13s_SHA256":STAGE13S_SHA,
        "run_id":12,"QC1_native_halfhours":4,"true_QC0_native_bookends":2,
        "ERA_RH_full_six_node_max_step_hPa":float(era_step.max()),
        "ERA_RH_full_boundary_method_status":"REJECT_GT4HPA",
        "QC0_linear_full_six_node_max_step_hPa":float(lin_step.max()),
        "QC0_linear_all_nodes_physically_valid":bool(physical.all()),
        "original_selected_QC1_VPD_missing_HH":int(old_missing_qc1.sum()),
        "original_selected_QC1_VPD_missing_accepted_as_source_hold_only":True,
        "original_measured_QC0_bookends_verified_finite_and_unchanged":True,
        "QC0_linear_method_status":(
            "HUMAN_REVIEW_ONLY_NOT_APPROVED" if eligible
            else "HOLD_PHYSICAL_OR_BOUNDARY_GATE_FAIL"),
        "remaining_other_full_original_QC1_runs_still_HOLD":[14,15,16,17,18],
        "stage13y_14_original_site_ERA_T_differences_preserved":True,
        "stage13y_8_2017_original_QC2_source_edges_preserved":True,
        "new_operator_approval":False,
        "source_or_forcing_written":False,
        "Postv5":False,"DATM":False,"AD400":False,"Slurm":False,
    }
    print("STAGE13Z SIX ORIGINAL SOURCE NODES | 2 TOWER QC0 + 4 QC1", flush=True)
    print(rows[["native_time","original_tower_VPD_F_QC",
        "unchanged_Stage13s_selected_VPD_hPa","full_edge_ERA_RH_VPD_hPa",
        "full_edge_QC0_anchor_linear_VPD_hPa"]].to_string(index=False),flush=True)
    print("STAGE13Z COMPLETE FIVE NATIVE BOUNDARY TESTS",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("STAGE13Z SCIENCE DECISION",json.dumps(stats,indent=2),flush=True)
    return rows,edges,stats


def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    for label in ("self-test","check","run"):
        mode.add_argument("--"+label,action="store_true")
    args=ap.parse_args()
    selftest()
    if args.self_test:return
    nodes,edges,stats=audit()
    if args.check:
        print("STAGE13Z READONLY CHECK PASS | ERA 4.800355hPa HOLD; QC0 linear reviewed only; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13z_Me6_run12_full_boundary_method_GATE_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    a="six_native_2015_QC0_QC1_VPD_QBOT_method_COMPARISON.csv"
    b="five_original_full_boundary_steps_ERA_VS_QC0_linear.csv"
    c="stage13z_run12_science_decision_ONLY.json"
    marker="NO_OPERATOR_APPROVAL_NO_FORCING_REPAIR"
    nodes.to_csv(out/a,index=False,float_format="%.17g")
    edges.to_csv(out/b,index=False,float_format="%.17g")
    (out/c).write_text(json.dumps(stats,indent=2)+"\n")
    (out/marker).write_text(
        "ERA RH full six-node method fails the 4hPa boundary. "
        "Any passing QC0-anchored linear candidate remains research-only "
        "and needs separate operator science approval and protected-source "
        "whole-forcing checks before writing a new separate shadow.\n")
    receipt={"version":VER,"site":"US-Me6",
        "stage13t_signed_SHA256":sha(T/T_REC),
        "stage13y_signed_SHA256":sha(Y/Y_REC),
        "operator_approval":False,"forcing_written":False,
        "outputs_SHA256":{n:sha(out/n) for n in (a,b,c,marker)}}
    (out/"stage13z_science_SHA_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13Z READONLY REPORT DIR:",out,flush=True)
    print("STAGE13Z REPORT COMPLETE | ORIGINAL SOURCE PRESERVED; NO FORCING/DATM/AD400/SLURM",flush=True)


if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13Z SCIENCE STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

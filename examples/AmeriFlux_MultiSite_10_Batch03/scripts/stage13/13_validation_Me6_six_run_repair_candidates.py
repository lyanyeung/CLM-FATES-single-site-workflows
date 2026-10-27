#!/usr/bin/env python3
"""US-Me6 Batch method validation: concrete, validated candidates for all six held runs.

Reads the ACTUAL Stage13x receipt and original SHA-verified tower/ERA and
Stage13s input. Compares raw ERA RH, locally median-adjusted ERA RH with
buffered leave-day-out validation, and QC0-to-QC0 linear VPD ONLY for the
four-halfhour Sep26 gap. Produces candidate values and one batch decision
table, not forcing, approval, QC promotion, model input or Slurm jobs.

All empirical screens below are declared research screening choices;
passing them is not proof of true missing humidity or production approval.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
VER = "batch03-stage13_validation-v1-20261027-Me6-six-run-validated-repair-candidates"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE = Path(__file__).resolve().parent
X_CODE = HERE / "13x_Me6_6run_tower_QC0_vs_ERA_RH_skill_and_2017_QC2_edge_BATCH_READONLY.py"
X_BLOB = "734a9d988f45c9628131e77b669913d9b0f4e8ae"
X = ROOT / "reports/stage13x_Me6_QC0_ERA_RH_empirical_skill_and_2017_QC2_edges_20261027T140953Z_342b79ec"
X_REC = "stage13x_original_QC0_ERA_RH_reliability_SHA_receipt.json"
X_SUM = "stage13x_six_run_source_skill_summary.json"
X_NAMES = {
    "six_original_source_runs_QC0_observed_vs_ERA_RH_skill_windows.csv",
    "eight_2017_original_source_QC2_immediate_edge_original_vs_ERA.csv",
    "14_original_site_ERA_Tdelta_GT8C_science_HOLD_preserved.csv",
    "nearby_48h_original_measured_QC0_skill_context.csv",
    X_SUM, "READONLY_QC0_CONTEXT_NOT_2017_QC2_SOURCE_APPROVAL",
}
S_SHA = "02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
W_SHA = "d0774c5d56df3dc8e640f26c1a8901c724f9b9e97b874d8f23fec9271f3f4023"
HH = pd.Timedelta(minutes=30)
COUNTS = {12: 4, 14: 469, 15: 95, 16: 30, 17: 137, 18: 47}
PROTECTED = {pd.Timestamp("2017-07-04 06:00") + i * HH for i in range(5)}
FAILED = {
    *pd.to_datetime(["2015-11-07 03:00", "2015-11-07 04:00", "2015-11-07 04:30",
                     "2015-11-07 05:00", "2015-11-07 08:00"]),
    *pd.date_range("2017-06-29 23:00", "2017-06-30 02:30", freq="30min"),
    pd.Timestamp("2017-07-03 07:00"),
}
WINDOW = pd.Timedelta(days=14)
MAX_STEP = 4.0
MAX_TDIFF = 8.0
MIN_TRAIN = 96
MIN_CV_ROWS = 96
MIN_CV_DAYS = 5
MIN_PSEUDOGAPS = 12
MIN_PSEUDOGAP_DAYS = 5


def require(ok, message):
    if not bool(ok):
        raise RuntimeError("ME6_BATCH_VALIDATION HOLD: " + str(message))


def must(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "missing file/symlink " + str(p))
    return p


def sha(path):
    h = hashlib.sha256()
    with must(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def es(t):
    t = np.asarray(t, dtype=float)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return 6.112 * np.exp(17.67 * t / (t + 243.5))


def water(vpd, temp, pressure):
    v, t, p = np.broadcast_arrays(np.asarray(vpd, float), np.asarray(temp, float),
                                   np.asarray(pressure, float))
    sat = es(t)
    e = (sat - v) * 100
    den = p - 0.378 * e
    with np.errstate(invalid="ignore", divide="ignore"):
        q = 0.622 * e / den
        rh = 100 * (1 - v / sat)
    ok = (np.isfinite(v) & np.isfinite(t) & np.isfinite(p) & np.isfinite(q)
          & np.isfinite(rh) & (p > 50000) & (p < 110000) & (den > 0)
          & (v > 0) & (v < sat) & (q > 0) & (q < 0.08)
          & (rh > 0) & (rh < 100))
    return q, rh, ok


def native_index(values):
    keys = values.astype(str).str.replace(r"[^0-9]", "", regex=True).str[:12]
    idx = pd.DatetimeIndex(pd.to_datetime(keys, format="%Y%m%d%H%M", errors="raise"))
    require(idx.is_unique and idx.is_monotonic_increasing, "native chronology/duplicates")
    return idx


def predecessor():
    p = must(X_CODE)
    blob = subprocess.run(["git", "hash-object", str(p)], check=True,
                          text=True, capture_output=True).stdout.strip()
    require(blob == X_BLOB, "Stage13x source module blob changed")
    spec = importlib.util.spec_from_file_location("me6_stage13x_for_stage13_validation", p)
    require(spec is not None and spec.loader is not None, "Stage13x cannot load")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    require(mod.ROOT == ROOT and mod.VER ==
            "batch03-stage13x-v1-20261027-Me6-QC0-ERA-RH-reliability-and-2017-QC2",
            "Stage13x site/version changed")
    return mod


def load_inputs():
    mod = predecessor()
    source, runs, failed, _ = mod.signed()  # Original r/q/ac and original raw SHA checks.
    require(sha(mod.S / mod.S_CSV) == S_SHA and sha(mod.W / mod.W_REC) == W_SHA,
            "actual protected Stage13s/Stage13w hash changed")
    receipt = json.loads(must(X / X_REC).read_text())
    require(receipt.get("version") == mod.VER and receipt.get("site") == "US-Me6"
            and receipt.get("research_report_only") is True
            and receipt.get("operator_science_approval") is False
            and receipt.get("original_Stage13w_source_receipt_SHA256") == W_SHA
            and receipt.get("original_Stage13s_research_forcing_SHA256") == S_SHA
            and set(receipt.get("output_SHA256", {})) == X_NAMES,
            "actual Stage13x receipt schema/parent mismatch")
    for name, dig in receipt["output_SHA256"].items():
        require("/" not in name and "\\" not in name and sha(X / name) == dig,
                "Stage13x output hash changed " + name)
    info = json.loads(must(X / X_SUM).read_text())
    require(info.get("six_remaining_full_source_QC1_runs_checked") == 6
            and info.get("14_original_source_site_ERA_temperature_GT8C_HOLD_untouched") == 14
            and info.get("2017_original_immediate_VPD_QC2_edges_reviewed") == 8
            and info.get("source_or_forcing_modified") is False
            and info.get("original_tower_source_sha256") == sha(source["primary"])
            and info.get("original_companion_ERA_source_sha256") == sha(source["era"]),
            "actual Stage13x science/source summary mismatch")
    require(set(pd.to_datetime(failed.native_time)) == FAILED,
            "exact fourteen original temperature HOLD times changed")
    tcols = ["TIMESTAMP_START", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC"]
    ecols = ["TIMESTAMP_START", "TA_ERA", "VPD_ERA"]
    tower = pd.read_csv(must(source["primary"]), usecols=tcols,
                        dtype={"TIMESTAMP_START": str}, low_memory=False)
    era = pd.read_csv(must(source["era"]), usecols=ecols,
                      dtype={"TIMESTAMP_START": str}, low_memory=False)
    tower = tower.loc[tower.TIMESTAMP_START.str[:4].isin(["2015", "2017"])].copy()
    era = era.loc[era.TIMESTAMP_START.str[:4].isin(["2015", "2017"])].copy()
    require(len(tower) == len(era) == 35040 and tower.TIMESTAMP_START.is_unique
            and era.TIMESTAMP_START.is_unique
            and tower.TIMESTAMP_START.tolist() == era.TIMESTAMP_START.tolist(),
            "original native tower/ERA two-year coverage mismatch")
    raw = tower.merge(era, on="TIMESTAMP_START", validate="one_to_one")
    raw.index = native_index(raw.TIMESTAMP_START)
    for col in tcols[1:] + ecols[1:]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
        raw.loc[raw[col] <= -9990, col] = np.nan
    selected = pd.read_csv(must(mod.S / mod.S_CSV), dtype={"time": str},
                           usecols=["time", "TA_USE", "VPD_USE", "QBOT", "PSRF"],
                           low_memory=False)
    selected.index = native_index(selected.time)
    require(len(selected) == 280320 and raw.index.isin(selected.index).all()
            and not ((selected.index.month == 2) & (selected.index.day == 29)).any(),
            "Stage13s 16-year NOLEAP chronology mismatch")
    meta = {"Stage13x_receipt_SHA256": sha(X / X_REC),
            "Stage13w_receipt_SHA256": W_SHA, "Stage13s_input_SHA256": S_SHA,
            "tower_SHA256": sha(source["primary"]), "ERA_SHA256": sha(source["era"])}
    return raw, selected, runs, meta


def observations(raw, selected):
    z = raw.copy()
    z["site_T"] = selected.TA_USE.reindex(z.index)
    z["site_V"] = selected.VPD_USE.reindex(z.index)
    z["site_P"] = selected.PSRF.reindex(z.index)
    z["obs_RH"] = 100 * (1 - z.VPD_F / es(z.TA_F))
    z["era_RH"] = 100 * (1 - z.VPD_ERA / es(z.TA_ERA))
    finite = np.isfinite(z[["TA_F", "VPD_F", "TA_ERA", "VPD_ERA", "site_T", "site_V", "site_P"]]).all(axis=1)
    ok = (finite & z.TA_F_QC.eq(0) & z.VPD_F_QC.eq(0)
          & np.isclose(z.site_T, z.TA_F, atol=1e-7, rtol=0)
          & np.isclose(z.site_V, z.VPD_F, atol=1e-7, rtol=0)
          & z.obs_RH.between(0, 100, inclusive="neither")
          & z.era_RH.between(0, 100, inclusive="neither")
          & z.site_P.between(50000, 110000, inclusive="neither")
          & ((z.TA_F - z.TA_ERA).abs() <= MAX_TDIFF))
    z = z.loc[ok].copy()
    z["residual_RH_pp"] = z.obs_RH - z.era_RH
    return z


def local_pool(obs, start, end):
    return obs.loc[((obs.index >= start - WINDOW) & (obs.index < start))
                   | ((obs.index > end) & (obs.index <= end + WINDOW))].copy()


def scores(errors):
    e = np.asarray(errors, float)
    if len(e) == 0 or not np.isfinite(e).all():
        return {"MAE_hPa": None, "P90_abs_hPa": None, "RMSE_hPa": None}
    return {"MAE_hPa": float(np.mean(abs(e))),
            "P90_abs_hPa": float(np.percentile(abs(e), 90)),
            "RMSE_hPa": float(np.sqrt(np.mean(e * e)))}


def buffered_cv(pool):
    """Hold out one complete native date plus a one-day buffer on BOTH sides."""
    rows = []
    days = pool.index.normalize()
    for day in days.unique():
        test = pool.loc[days == day]
        train = pool.loc[abs(days - day) > pd.Timedelta(days=1)]
        if len(train) < MIN_TRAIN or train.index.normalize().nunique() < 3:
            continue
        bias = float(train.residual_RH_pp.median())
        pred_rh = test.era_RH.to_numpy(float) + bias  # Never clip RH.
        base = es(test.TA_F) * (1 - test.era_RH.to_numpy(float) / 100)
        pred = es(test.TA_F) * (1 - pred_rh / 100)
        for i, ts in enumerate(test.index):
            rows.append({"native_time": str(ts), "heldout_native_date": str(day.date()),
                         "training_QC0_rows": len(train),
                         "minimum_training_date_distance_days":
                         int(abs(train.index.normalize() - day).min() / pd.Timedelta(days=1)),
                         "training_bias_RH_pp": bias,
                         "raw_error_hPa": float(base[i] - test.VPD_F.iloc[i]),
                         "adjusted_error_hPa": float(pred[i] - test.VPD_F.iloc[i]),
                         "adjusted_RH_valid": bool(0 < pred_rh[i] < 100)})
    cv = pd.DataFrame(rows)
    valid_days = cv.heldout_native_date.nunique() if len(cv) else 0
    raw = scores(cv.raw_error_hPa if len(cv) else [])
    adjusted = scores(cv.adjusted_error_hPa if len(cv) else [])
    support = (len(cv) >= MIN_CV_ROWS and valid_days >= MIN_CV_DAYS
               and bool(cv.adjusted_RH_valid.all())
               and adjusted["MAE_hPa"] <= raw["MAE_hPa"]
               and adjusted["P90_abs_hPa"] <= raw["P90_abs_hPa"])
    return cv, {"validation_rows": len(cv), "validation_dates": valid_days,
                "raw_ERA": raw, "adjusted_ERA": adjusted,
                "research_empirical_screen_PASS": bool(support)}


def pseudogaps(pool, start, length=4):
    """Nonoverlapping observed 6-HH windows; hide only middle four VPD values.

    Match native start hour to within 3 hours of the real gap. Both anchors
    and four truth values must all be actual preserved source QC0. Each
    complete six-record window is used once; no interpolation across dates
    absent from the native source. An invalid prediction is retained as a
    failure rather than dropped from the score.
    """
    rows = []
    last_end = None
    target_minute = start.hour * 60 + start.minute
    for a in pool.index:
        middle = a + HH
        minute = middle.hour * 60 + middle.minute
        distance = min(abs(minute - target_minute), 1440 - abs(minute - target_minute))
        stamps = pd.date_range(a, periods=length + 2, freq="30min")
        if distance > 180 or (last_end is not None and a <= last_end):
            continue
        if not stamps.isin(pool.index).all():
            continue
        z = pool.loc[stamps]
        predicted = np.linspace(float(z.VPD_F.iloc[0]), float(z.VPD_F.iloc[-1]), length + 2)[1:-1]
        base = es(z.TA_F.iloc[1:-1]) * (1 - z.era_RH.iloc[1:-1].to_numpy(float) / 100)
        true = z.VPD_F.iloc[1:-1].to_numpy(float)
        _, _, phys = water(predicted, z.TA_F.iloc[1:-1], z.site_P.iloc[1:-1])
        for j, ts in enumerate(stamps[1:-1]):
            rows.append({"pseudo_gap_start": str(middle), "native_time": str(ts),
                         "date": str(middle.date()), "truth_QC0_VPD_hPa": float(true[j]),
                         "linear_error_hPa": float(predicted[j] - true[j]),
                         "raw_ERA_error_hPa": float(base[j] - true[j]),
                         "linear_physics_PASS": bool(phys[j])})
        last_end = stamps[-1]
    frame = pd.DataFrame(rows)
    n = frame.pseudo_gap_start.nunique() if len(frame) else 0
    nd = frame.date.nunique() if len(frame) else 0
    linear = scores(frame.linear_error_hPa if len(frame) else [])
    era = scores(frame.raw_ERA_error_hPa if len(frame) else [])
    support = (n >= MIN_PSEUDOGAPS and nd >= MIN_PSEUDOGAP_DAYS
               and bool(frame.linear_physics_PASS.all())
               and linear["MAE_hPa"] <= era["MAE_hPa"]
               and linear["P90_abs_hPa"] <= era["P90_abs_hPa"]
               and linear["P90_abs_hPa"] <= MAX_STEP)
    return frame, {"nonoverlapping_pseudo_gaps": n, "validation_dates": nd,
                   "linear": linear, "raw_ERA": era,
                   "research_empirical_screen_PASS": bool(support)}


def candidates(raw, selected, runs):
    obs = observations(raw, selected)
    decisions, details, cv_rows, gap_rows, validation = [], [], [], [], {}
    all_native = set()
    for gid, n in COUNTS.items():
        row = runs.loc[runs.source_full_run_id.eq(gid)]
        require(len(row) == 1, "run identity " + str(gid))
        r = row.iloc[0]
        start, end = pd.Timestamp(r.source_original_QC1_start), pd.Timestamp(r.source_original_QC1_end)
        stamps = pd.date_range(start, end, freq="30min")
        left, right = start - HH, end + HH
        require(len(stamps) == n == int(r.original_QC1_halfhour_count)
                and stamps.isin(raw.index).all() and stamps.isin(selected.index).all()
                and left in raw.index and right in raw.index
                and left in selected.index and right in selected.index
                and (raw.loc[stamps, "VPD_F_QC"] == 1).all()
                and not all_native.intersection(stamps), "exact six-run native scope " + str(gid))
        all_native.update(stamps)
        z = raw.loc[stamps]
        s = selected.loc[stamps]
        temp, pressure = s.TA_USE.to_numpy(float), s.PSRF.to_numpy(float)
        measured = (z.TA_F_QC.eq(0).to_numpy() & np.isfinite(temp)
                    & np.isclose(temp, z.TA_F, atol=1e-7, rtol=0))
        protected = np.array([ts in PROTECTED for ts in stamps])
        era_rh = 100 * (1 - z.VPD_ERA.to_numpy(float) / es(z.TA_ERA))
        pool = local_pool(obs, start, end)
        cv, skill = buffered_cv(pool)
        if len(cv):
            cv.insert(0, "run_id", gid)
            cv_rows.append(cv)
        bias = float(pool.residual_RH_pp.median()) if len(pool) >= MIN_TRAIN else np.nan
        validation[str(gid)] = {"QC0_pool_rows": len(pool), "bias_RH_pp":
                               float(bias) if np.isfinite(bias) else None, "buffered_day_CV": skill}
        methods = [("RAW_NATIVE_ERA_RH", np.asarray(era_rh), None),
                   ("LOCAL_MEDIAN_ADJUSTED_ERA_RH", np.asarray(era_rh) + bias,
                    skill["research_empirical_screen_PASS"])]
        if gid == 12:
            require(start == pd.Timestamp("2015-09-26 05:00")
                    and end == pd.Timestamp("2015-09-26 06:30"), "four-HH source scope changed")
            pg, pgskill = pseudogaps(pool, start)
            if len(pg):
                gap_rows.append(pg)
            validation[str(gid)]["shortgap_validation"] = pgskill
            line = np.linspace(float(raw.at[left, "VPD_F"]), float(raw.at[right, "VPD_F"]), n + 2)[1:-1]
            methods.append(("DIRECT_QC0_SHORTGAP_LINEAR_VPD", line,
                            pgskill["research_empirical_screen_PASS"]))
        for method, values, empirical in methods:
            is_line = method == "DIRECT_QC0_SHORTGAP_LINEAR_VPD"
            vpd = np.asarray(values, float) if is_line else es(temp) * (1 - values / 100)
            q, rh, physical = water(vpd, temp, pressure)
            donor_pass = np.ones(n, bool) if is_line else np.asarray(
                np.isfinite(z.TA_ERA) & np.isfinite(z.VPD_ERA)
                & (np.asarray(era_rh) > 0) & (np.asarray(era_rh) < 100)
                & (abs(temp - z.TA_ERA.to_numpy(float)) <= MAX_TDIFF), dtype=bool)
            # Protected five values remain exact old numbers in EVERY trial.
            vpd = np.where(protected, s.VPD_USE, vpd)
            q = np.where(protected, s.QBOT, q)
            _, rh, physical_after = water(vpd, temp, pressure)
            row_pass = measured & (protected | (physical & donor_pass)) & physical_after
            q_consistent = np.isclose(q, water(vpd, temp, pressure)[0], atol=1e-12, rtol=1e-10)
            row_pass &= q_consistent
            edge_vpd = np.r_[float(selected.at[left, "VPD_USE"]), vpd,
                             float(selected.at[right, "VPD_USE"])]
            steps = abs(np.diff(edge_vpd))
            finite_edges = bool(np.isfinite(steps).all())
            step_pass = finite_edges and bool((steps <= MAX_STEP).all())
            boundaries_qc0 = all(float(raw.at[t, "VPD_F_QC"]) == 0 for t in (left, right))
            if boundaries_qc0:
                boundaries_qc0 = all(np.isclose(float(raw.at[t, "VPD_F"]),
                                                float(selected.at[t, "VPD_USE"]),
                                                atol=1e-7, rtol=0) for t in (left, right))
            reasons = []
            if not row_pass.all(): reasons.append("ROW_T_SOURCE_OR_WATER_PHYSICS_HOLD")
            if not step_pass: reasons.append("NATIVE_VPD_EDGE_GT4HPA_OR_MISSING")
            if n > 300: reasons.append("LONG_RUN_INDEPENDENT_SOURCE_REVIEW_REQUIRED")
            if not boundaries_qc0: reasons.append("IMMEDIATE_SOURCE_BOUNDARIES_NOT_PRESERVED_QC0")
            if is_line and n != 4: reasons.append("NOT_EXACT_FOUR_HH_SHORTGAP")
            if empirical is not True: reasons.append("LOCAL_HELDOUT_SUPPORT_NOT_ESTABLISHED")
            numerical = bool(row_pass.all() and step_pass)
            decision = "CANDIDATE_FOR_GROUPED_REVIEW" if not reasons else "HOLD"
            decisions.append({"run_id": gid, "method": method, "native_HH": n,
                              "candidate_nonprotected_HH": int((~protected).sum()),
                              "protected_2017_HH": int(protected.sum()),
                              "row_physics_source_PASS_HH": int(row_pass.sum()),
                              "original_ERA_Tdelta_GT8C_HH": int((abs(temp - z.TA_ERA) > MAX_TDIFF).sum()),
                              "boundary_source_VPD_QC_before": float(raw.at[left, "VPD_F_QC"]),
                              "boundary_source_VPD_QC_after": float(raw.at[right, "VPD_F_QC"]),
                              "max_VPD_step_hPa": float(steps.max()) if finite_edges else np.nan,
                              "VPD_edges_GT4hPa": int((steps > MAX_STEP).sum()),
                              "numerical_checks_PASS": numerical,
                              "empirical_screen_PASS": empirical is True,
                              "batch_decision": decision, "HOLD_reasons": ";".join(reasons),
                              "operator_approved": False, "production_admitted": False})
            for i, ts in enumerate(stamps):
                details.append({"run_id": gid, "method": method, "native_time": str(ts),
                                "original_VPD_QC": float(z.VPD_F_QC.iloc[i]),
                                "retained_TA_C": float(temp[i]), "retained_PSRF_Pa": float(pressure[i]),
                                "before_VPD_hPa": float(s.VPD_USE.iloc[i]),
                                "before_QBOT_kgkg": float(s.QBOT.iloc[i]),
                                "candidate_VPD_hPa": float(vpd[i]), "candidate_QBOT_kgkg": float(q[i]),
                                "candidate_RH_percent": float(rh[i]),
                                "row_source_physics_PASS": bool(row_pass[i]),
                                "protected_2017_value_preserved": bool(protected[i]),
                                "native_left_VPD_step_hPa": float(steps[i]),
                                "native_right_VPD_step_hPa": float(steps[i + 1]),
                                "batch_decision": decision, "operator_approved": False})
    require(len(all_native) == 782 and PROTECTED.issubset(all_native), "782/5 scope changed")
    return (pd.DataFrame(decisions), pd.DataFrame(details),
            pd.concat(cv_rows, ignore_index=True) if cv_rows else pd.DataFrame(),
            pd.concat(gap_rows, ignore_index=True) if gap_rows else pd.DataFrame(), validation)


def selftest():
    q, rh, ok = water([5.624, 5.835, 6.046, 6.257], [15] * 4, [95000] * 4)
    require(ok.all() and np.isfinite(q).all() and (rh > 0).all(), "shortgap physics")
    require(not water([100, np.nan], [10, 10], [95000, 95000])[2].any(),
            "invalid saturation/NaN accepted")
    require(len(FAILED) == 14 and sum(COUNTS.values()) == 782 and len(PROTECTED) == 5,
            "six-run protected scope")
    idx = native_index(pd.Series(["201509260500", "201509260530"]))
    require(isinstance(idx, pd.DatetimeIndex) and (idx.month == 9).all(), "DatetimeIndex regression")
    print("ME6_BATCH_VALIDATION SELF-TEST PASS | exact six-run scope, no clipping, strict water and native time", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    for key in ("self-test", "check", "run"):
        mode.add_argument("--" + key, action="store_true")
    args = p.parse_args()
    selftest()
    if args.self_test:
        return
    raw, selected, runs, provenance = load_inputs()
    decisions, values, cv, gaps, validation = candidates(raw, selected, runs)
    require(len(decisions) == 13 and len(values) == 1568, "batch method/row count changed")
    print("ME6_BATCH_VALIDATION SIX-RUN REPAIR CANDIDATE TABLE", flush=True)
    print(decisions[["run_id", "method", "row_physics_source_PASS_HH", "native_HH",
                     "max_VPD_step_hPa", "empirical_screen_PASS", "batch_decision", "HOLD_reasons"]]
          .to_string(index=False), flush=True)
    summary = {"version": VER, "site": "US-Me6", "input_provenance": provenance,
               "original_held_runs": 6, "original_QC1_HH": 782,
               "compared_run_methods": len(decisions), "candidate_value_rows": len(values),
               "methods_ready_for_grouped_review": int(decisions.batch_decision.eq("CANDIDATE_FOR_GROUPED_REVIEW").sum()),
               "protected_Stage13s_235HH_unchanged": True, "protected_Stage12ac_5HH_unchanged": True,
               "production_forcing_written": False, "operator_approval_granted": False,
               "QC2_neighbours_changed": False, "temperature_threshold_C": MAX_TDIFF,
               "VPD_step_threshold_hPa": MAX_STEP, "validation": validation,
               "screening_choices_not_proof_of_missing_value_accuracy": True,
               "DATM": False, "AD400": False, "Slurm": False}
    # Recheck immutable main input after calculation; reports cannot promote it.
    mod = predecessor()
    require(sha(mod.S / mod.S_CSV) == S_SHA, "protected Stage13s changed during calculation")
    if args.check:
        print("ME6_BATCH_VALIDATION CHECK PASS | 6 runs, 13 method comparisons, immutable input; NO WRITES", flush=True)
        return
    out = ROOT / "reports" / ("stage13_validation_Me6_six_run_repair_candidates_" +
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    outputs = {"six_runs_13_method_batch_decisions.csv": decisions,
               "1568_explicit_candidate_values_NOT_FORCING.csv": values,
               "buffered_leave_day_out_QC0_validation.csv": cv,
               "nonoverlapping_four_HH_QC0_pseudogap_validation.csv": gaps}
    for name, frame in outputs.items():
        frame.to_csv(out / name, index=False, float_format="%.17g")
    info = "stage13_validation_repair_candidate_summary.json"
    (out / info).write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    marker = "CANDIDATES_ONLY_NO_FORCING_OR_SCIENCE_APPROVAL"
    (out / marker).write_text("Explicit repair candidates and held-out comparisons only. "
                             "No source values, QC2 neighbours, Stage13s input or model jobs changed.\n")
    names = [*outputs, info, marker]
    receipt = {"version": VER, "site": "US-Me6", "input_provenance": provenance,
               "forcings_written": False, "outputs_SHA256": {n: sha(out / n) for n in names}}
    (out / "stage13_validation_candidate_SHA_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("ME6_BATCH_VALIDATION REPORT DIR:", out, flush=True)
    print("ME6_BATCH_VALIDATION SIX-RUN CANDIDATE COMPARISON COMPLETE; NO FORCING OR SLURM", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ME6_BATCH_VALIDATION STOP:", exc, file=sys.stderr, flush=True)
        raise SystemExit(2)

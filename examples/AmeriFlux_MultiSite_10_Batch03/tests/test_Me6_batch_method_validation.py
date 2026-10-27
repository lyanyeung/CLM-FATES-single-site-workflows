"""Source-free numerical and batch regression tests for the Me6 repair plan."""
import importlib.util
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/stage13/13_validation_Me6_six_run_repair_candidates.py"
spec = importlib.util.spec_from_file_location("stage13_validation_tested", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    idx = pd.date_range("2015-09-01", "2015-12-01", freq="30min", inclusive="left").append(
        pd.date_range("2017-06-01", "2017-08-01", freq="30min", inclusive="left"))
    # Linear daily signal in each morning: interpolation should outperform
    # a deliberately biased reanalysis on independent four-HH pseudo gaps.
    hour = idx.hour.to_numpy() + idx.minute.to_numpy() / 60
    v = 5 + 0.15 * hour
    temp = np.full(len(idx), 20.)
    rh = 100 * (1 - v / m.es(temp))
    era_rh = rh + 4
    raw = pd.DataFrame({"TA_F": temp, "TA_F_QC": 0., "VPD_F": v,
                        "VPD_F_QC": 0., "TA_ERA": temp,
                        "VPD_ERA": m.es(temp) * (1 - era_rh / 100)}, index=idx)
    q = m.water(v, temp, 95000)[0]
    selected = pd.DataFrame({"TA_USE": temp, "VPD_USE": v, "QBOT": q,
                             "PSRF": 95000.}, index=idx)
    ranges = {
        12: ("2015-09-26 05:00", "2015-09-26 06:30"),
        14: ("2015-11-04 13:00", "2015-11-14 07:00"),
        15: ("2017-06-28 17:00", "2017-06-30 16:00"),
        16: ("2017-06-30 17:00", "2017-07-01 07:30"),
        17: ("2017-07-01 12:00", "2017-07-04 08:00"),
        18: ("2017-07-04 12:30", "2017-07-05 11:30"),
    }
    runs = []
    for gid, (first, last) in ranges.items():
        stamps = pd.date_range(first, last, freq="30min")
        assert len(stamps) == m.COUNTS[gid]
        raw.loc[stamps, "VPD_F_QC"] = 1
        # A wrong retained QC1 value cannot be used as validation truth.
        selected.loc[stamps, "VPD_USE"] += 0.1
        selected.loc[stamps, "QBOT"] = m.water(selected.loc[stamps, "VPD_USE"], 20., 95000.)[0]
        if gid >= 15:
            raw.loc[[stamps[0] - m.HH, stamps[-1] + m.HH], "VPD_F_QC"] = 2
        runs.append({"source_full_run_id": gid, "source_original_QC1_start": first,
                     "source_original_QC1_end": last, "original_QC1_halfhour_count": len(stamps)})
    # Exact fourteen original donor-mismatch events stay strict HOLD.
    raw.loc[list(m.FAILED), "TA_ERA"] = 11.5
    return raw, selected, pd.DataFrame(runs)


class RepairCandidateTests(unittest.TestCase):
    def test_full_batch_values_scope_and_preservation(self):
        raw, selected, runs = fixture()
        before = selected.copy(deep=True)
        source_before = raw.copy(deep=True)
        decisions, values, cv, gaps, validation = m.candidates(raw, selected, runs)
        self.assertEqual(len(decisions), 13)
        self.assertEqual(len(values), 1568)
        self.assertEqual(values.native_time.nunique(), 782)
        self.assertEqual(set(values.original_VPD_QC), {1.})
        self.assertFalse(values.operator_approved.any())
        self.assertFalse(decisions.production_admitted.any())
        pd.testing.assert_frame_equal(before, selected)
        pd.testing.assert_frame_equal(source_before, raw)
        protected = values.loc[values.protected_2017_value_preserved]
        self.assertEqual(len(protected), 10)  # two methods, five original times
        np.testing.assert_array_equal(protected.before_VPD_hPa, protected.candidate_VPD_hPa)
        np.testing.assert_array_equal(protected.before_QBOT_kgkg, protected.candidate_QBOT_kgkg)
        line = decisions.loc[decisions.method.eq("DIRECT_QC0_SHORTGAP_LINEAR_VPD")].iloc[0]
        self.assertEqual(line.run_id, 12)
        self.assertEqual(line.batch_decision, "CANDIDATE_FOR_GROUPED_REVIEW")
        self.assertTrue(line.empirical_screen_PASS)
        self.assertTrue((cv.minimum_training_date_distance_days >= 2).all())
        self.assertGreaterEqual(gaps.pseudo_gap_start.nunique(), 12)
        # Strict JSON output remains serializable, including empty/held scores.
        json.dumps(validation, allow_nan=False)

    def test_no_temperature_threshold_relaxation_or_qc2_promotion(self):
        raw, selected, runs = fixture()
        decisions, values, _, _, _ = m.candidates(raw, selected, runs)
        era = values.loc[~values.method.eq("DIRECT_QC0_SHORTGAP_LINEAR_VPD")]
        failed = era.loc[pd.to_datetime(era.native_time).isin(m.FAILED)]
        self.assertEqual(len(failed), 28)
        self.assertFalse(failed.row_source_physics_PASS.any())
        held = decisions.loc[decisions.run_id.ge(15)]
        self.assertTrue(held.batch_decision.eq("HOLD").all())
        self.assertTrue(held.HOLD_reasons.str.contains("BOUNDARIES_NOT_PRESERVED_QC0").all())
        long = decisions.loc[decisions.run_id.eq(14)]
        self.assertTrue(long.HOLD_reasons.str.contains("LONG_RUN").all())

    def test_buffered_cv_excludes_adjacent_days(self):
        raw, selected, _ = fixture()
        obs = m.observations(raw, selected)
        pool = m.local_pool(obs, pd.Timestamp("2015-09-26 05:00"), pd.Timestamp("2015-09-26 06:30"))
        cv, skill = m.buffered_cv(pool)
        self.assertTrue(skill["research_empirical_screen_PASS"])
        self.assertTrue((cv.minimum_training_date_distance_days > 1).all())
        self.assertLess(skill["adjusted_ERA"]["MAE_hPa"], 1e-12)
        self.assertGreater(skill["raw_ERA"]["MAE_hPa"], 0.9)

    def test_small_or_empty_validation_cannot_pass(self):
        raw, selected, _ = fixture()
        obs = m.observations(raw, selected)
        for pool in (obs.iloc[:0], obs.iloc[:80]):
            _, skill = m.buffered_cv(pool)
            _, gap_skill = m.pseudogaps(pool, pd.Timestamp("2015-09-26 05:00"))
            self.assertFalse(skill["research_empirical_screen_PASS"])
            self.assertFalse(gap_skill["research_empirical_screen_PASS"])
            json.dumps([skill, gap_skill], allow_nan=False)

    def test_no_observed_qc0_or_changed_selected_truth_enters_validation(self):
        raw, selected, _ = fixture()
        ts = pd.Timestamp("2015-09-03 05:00")
        selected.at[ts, "VPD_USE"] += 1
        self.assertNotIn(ts, m.observations(raw, selected).index)
        ts2 = pd.Timestamp("2015-09-03 06:00")
        raw.at[ts2, "TA_F_QC"] = 1
        self.assertNotIn(ts2, m.observations(raw, selected).index)

    def test_bad_native_scope_stops(self):
        raw, selected, runs = fixture()
        raw.at[pd.Timestamp("2015-09-26 05:30"), "VPD_F_QC"] = 0
        with self.assertRaisesRegex(RuntimeError, "exact six-run native scope"):
            m.candidates(raw, selected, runs)
        with self.assertRaisesRegex(RuntimeError, "chronology/duplicates"):
            m.native_index(pd.Series(["201509260500", "201509260500"]))

    def test_saturation_and_unclipped_extremes_fail(self):
        _, rh, ok = m.water([30, -1, np.nan], [10] * 3, [95000] * 3)
        self.assertFalse(ok.any())
        self.assertTrue(rh[0] < 0)
        self.assertTrue(rh[1] > 100)


if __name__ == "__main__":
    unittest.main()

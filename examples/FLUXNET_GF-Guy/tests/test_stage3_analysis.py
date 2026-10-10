"""Synthetic regression tests. No IRIDIS access or real EC files required."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
import xarray as xr

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EC = import_file("gf_guy_stage3_ec", SCRIPTS / "14_compare_final_cycle_ec.py")
CV = import_file("gf_guy_stage3_convergence", SCRIPTS / "13_plot_spinup300_convergence.py")


class Stage3Tests(unittest.TestCase):
    def test_noleap_calendar_order(self):
        self.assertEqual(EC._noleap_ordinal(2020, 3, 1) - EC._noleap_ordinal(2020, 2, 28), 1)
        self.assertEqual(EC._noleap_ordinal(2317, 1, 1) - EC._noleap_ordinal(2316, 1, 1), 365)

    def test_model_efficiency_is_not_correlation_squared(self):
        result = EC.metrics([1, 2, 3], [2, 3, 4])
        self.assertAlmostEqual(result["R"], 1)
        self.assertAlmostEqual(result["R2"], -0.5)
        self.assertAlmostEqual(result["Bias"], 1)

    def test_explicit_hh_preferred_over_other_resolutions(self):
        with tempfile.TemporaryDirectory() as t:
            site = Path(t)
            raw = site / "forcing/raw/ICOSETC_GF-Guy_ARCHIVE_L2"
            raw.mkdir(parents=True)
            (raw / "ICOSETC_GF-Guy_FLUXNET_HH_L2.csv").write_text("TIMESTAMP_START,GPP_DT_VUT_REF,NEE_VUT_REF\n")
            (raw / "ICOSETC_GF-Guy_FLUXNET_DD_L2.csv").write_text("TIMESTAMP_START,GPP_DT_VUT_REF,NEE_VUT_REF\n")
            found = EC.resolve_obs(None, site, "NEE_VUT_REF", "auto")
            self.assertEqual(found.name, "ICOSETC_GF-Guy_FLUXNET_HH_L2.csv")

    def test_fates_date_mapping_and_ec_monthly(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            hist = d / "hist"
            hist.mkdir()
            days = pd.date_range("2001-01-01", "2001-12-31", freq="D")
            phase = np.arange(365)
            gpp = (2 + np.sin(2 * np.pi * phase / 365.0)) * 1e-7
            nep = (1 + .5 * np.cos(2 * np.pi * phase / 365.0)) * 1e-7
            for model_year in range(2312, 2317):
                t_end = np.arange(1, 366, dtype=float)
                bnds = np.c_[t_end - 1, t_end]
                ds = xr.Dataset(
                    {
                        "FATES_GPP": (("time", "lndgrid"), gpp[:, None], {"units": "kg m-2 s-1"}),
                        "FATES_NEP": (("time", "lndgrid"), nep[:, None], {"units": "kg m-2 s-1"}),
                        "time_bounds": (("time", "nbnd"), bnds),
                    },
                    coords={"time": ("time", t_end, {"units": f"days since {model_year}-01-01 00:00:00", "calendar": "noleap", "bounds": "time_bounds"}),
                            "lndgrid": [0]},
                )
                f = hist / f"GF-Guy_FATES_SPINUP300_CO2405.clm2.h0a.{model_year}-01-02-00000.nc"
                ds.to_netcdf(f, engine="scipy")
            mapped = EC.model_daily(hist)
            self.assertEqual(len(mapped), 1825)
            self.assertEqual(str(mapped.date.iloc[0].date()), "2017-01-01")
            self.assertEqual(str(mapped.date.iloc[-1].date()), "2021-12-31")
            self.assertFalse((mapped.date == pd.Timestamp("2020-02-29")).any())

            ec_rows = []
            for y in range(2017, 2022):
                for idx, day in enumerate(pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D")):
                    if day.month == 2 and day.day == 29:
                        continue
                    for h in range(48):
                        ec_rows.append((day + pd.Timedelta(minutes=30 * h),
                            gpp[idx if y != 2020 or day < pd.Timestamp('2020-03-01') else idx-1] * EC.FATES_FACTOR / EC.EC_FACTOR,
                            -nep[idx if y != 2020 or day < pd.Timestamp('2020-03-01') else idx-1] * EC.FATES_FACTOR / EC.EC_FACTOR))
            # A clearer phase map using within-year position after no-leap filtering.
            obs = pd.DataFrame(ec_rows, columns=["date", "GPP_DT_VUT_REF", "NEE_VUT_REF"])
            obs["TIMESTAMP_START"] = obs["date"].dt.strftime("%Y%m%d%H%M")
            csv = d / "ICOSETC_GF-Guy_FLUXNET_HH_L2.csv"
            obs[["TIMESTAMP_START", "GPP_DT_VUT_REF", "NEE_VUT_REF"]].to_csv(csv, index=False)
            obs_daily, gppname = EC.ec_daily(csv, "auto", "NEE_VUT_REF", "auto")
            self.assertEqual(gppname, "GPP_DT_VUT_REF")
            daily = pd.merge(mapped, obs_daily, on="date", how="left")
            self.assertEqual(len(daily), 1825)
            monthly = pd.merge(EC.monthly_pair(daily, "EC_GPP", "FATES_GPP"),
                               EC.monthly_pair(daily, "EC_NEE", "FATES_NEE"), on="date")
            self.assertEqual(len(monthly), 60)
            self.assertTrue((monthly.EC_GPP_NDAY >= 28).all())
            self.assertTrue((monthly.EC_NEE_NDAY >= 28).all())
            result = EC.metrics(monthly.EC_GPP, monthly.FATES_GPP)
            self.assertAlmostEqual(result["R2"], 1.0, places=3)

    def test_percent_same_phase(self):
        x = pd.Series([100, 110, 100, 100, 100, 101])
        pc = CV.percent_delta(x, x.shift(5))
        self.assertAlmostEqual(pc.iloc[-1], 1.0)
        self.assertTrue(math.isnan(pc.iloc[0]))


if __name__ == "__main__":
    unittest.main()

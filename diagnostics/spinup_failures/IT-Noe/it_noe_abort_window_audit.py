#!/usr/bin/env python3
"""Read-only audit of the last visible IT-Noe CLM step and nearby DATM forcing.

Does NOT infer the exact abort step from the final history output. Does NOT
modify input data, NetCDF, case files, restart checkpoints, or Slurm jobs.
"""
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from netCDF4 import Dataset

SITE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing")
CASE_NAME = "IT-Noe_FATES_SPINUP500_11P"
RUN = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS") / CASE_NAME / "run"
DEFAULT_CONTEXT = Path.home() / "IT-Noe_source_diagnosis/episode_review_v1/2010_failure_context_with_ERA5.csv"
DEFAULT_OUT = Path.home() / "IT-Noe_source_diagnosis/abort_window_v1"

def noleap_step_date(nstep, start_year=2004, atm_ncpl=48):
    days, substeps = divmod(nstep, atm_ncpl)
    year, doy = divmod(days, 365)
    return (datetime(start_year + year, 1, 1) +
            timedelta(days=doy, seconds=substeps * 86400 / atm_ncpl))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    p.add_argument("--datm", type=Path, default=SITE / "datm_11_provisional_dynamic_zbot_v1/IT-Noe_DATM_2010.nc")
    p.add_argument("--log", type=Path, default=RUN / "lnd.log.4286761.261015-004831")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    for source in (args.context, args.datm, args.log):
        if not source.is_file():
            p.error("Required input missing: " + str(source))
    if args.out.exists() and any(args.out.iterdir()):
        p.error("Output not empty. Choose a new --out to protect earlier reports: " + str(args.out))

    log = args.log.read_text(errors="replace")
    steps = [int(x) for x in re.findall(r"\bnstep\s*=\s*(\d+)", log)]
    if not steps:
        p.error("No nstep found in land log")
    last_step = max(steps)
    last_time = noleap_step_date(last_step)
    abort = re.findall(r"rh\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)", log, re.I)

    context = pd.read_csv(args.context, parse_dates=["time"])
    if context["time"].isna().any() or context.time.duplicated().any():
        p.error("Invalid or duplicate timestamps in context")
    near = context.loc[(context.time >= "2010-05-27 22:00") &
                       (context.time <= "2010-05-28 03:00")].copy()
    if near.empty:
        p.error("Context file lacks requested 2010-05-27/28 window")
    if "TA_F" not in near or "TA_ERA" not in near:
        p.error("Context lacks selected and ERA temperatures")

    with Dataset(args.datm) as ds:
        t = ds.variables["time"]
        units = getattr(t, "units", "")
        cal = getattr(t, "calendar", "")
        fields = ("TBOT", "QBOT", "PSRF", "WIND", "ZBOT", "FSDS", "FLDS", "PRECTmms")
        for f in fields:
            if f not in ds.variables:
                p.error(f"DATM variable absent: {f}")
        for name in fields:
            near[name] = np.nan
        for index, row in near.iterrows():
            delta = (row.time.to_pydatetime() - datetime(2010, 1, 1)).total_seconds()
            slot = int(round(delta / 1800))
            if abs(delta - slot*1800) > 1:
                p.error("Non-half-hour context timestamp: " + str(row.time))
            if not (0 <= slot < len(t)):
                p.error("DATM 2010 time index out of bounds")
            # Stage15 annual DATM uses days since 2010-01-01, 48 steps per day.
            if "2010-01-01" not in units or abs(float(t[slot]) - slot/48) > 1e-5:
                p.error("DATM time coordinate differs from expected Stage15 30min noleap axis")
            for name in fields:
                near.at[index, name] = float(ds.variables[name][slot, 0, 0])
    temp_c = near.TBOT - 273.15
    e_sat = 611.2 * np.exp(17.67*temp_c/(temp_c+243.5))
    e_actual = near.QBOT * near.PSRF / (0.622 + 0.378*near.QBOT)
    near["DATM_RH_forcing_pct"] = 100*e_actual/e_sat
    near["DATM_TBOT_minus_CSV_C"] = temp_c - pd.to_numeric(near.TA_F)
    near["DATM_ZBOT_below_2m"] = near.ZBOT < 2.0
    args.out.mkdir(parents=True, exist_ok=True)
    near.to_csv(args.out / "pre_abort_30min_DATM_vs_ERA.csv", index=False)
    lines = [
        "Case: " + CASE_NAME,
        "Land log: " + str(args.log),
        "Largest visible nstep: " + str(last_step),
        "Approximate timestamp at *last visible output* (2004 start, 48/day noleap): " + str(last_time),
        "Log RH negative: " + (abort[-1] if abort else "not found"),
        "DATM time units: " + units,
        "DATM calendar: " + cal,
        "NOTE: Latest logged history timestep does NOT prove the exact aborted timestep.",
        "NOTE: DATM forcing RH is NOT the model-diagnosed rh_ref2m.",
        "NOTE: ZBOT below 2 m is a diagnostic configuration detail, not proof of the cause.",
        "RESULT: no forcing, CIME configuration, or restart modified.",
    ]
    (args.out / "incident_timeline.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    view = ["time", "TA_F", "TA_ERA", "TBOT", "QBOT", "PSRF",
            "DATM_RH_forcing_pct", "WIND", "ZBOT", "DATM_TBOT_minus_CSV_C"]
    print("\nPRE-ABORT SELECTED METEOROLOGY (TBOT in Kelvin)\n")
    print(near[view].to_string(index=False, float_format=lambda x: f"{x:.6g}"))
    print("\nREPORT:", args.out)

if __name__ == "__main__":
    main()

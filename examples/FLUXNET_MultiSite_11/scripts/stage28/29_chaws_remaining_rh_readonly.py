#!/usr/bin/env python3
"""CH-Aws Stage28 follow-up: read-only 68-row/18-period low-RH evidence audit.

Parent is RH25A CSV; the nine Stage28 v4 January records are already revised
in an independent 2006 NetCDF only. Do not conflate unedited RH25A CSV with v4.
No candidates or forcing files are modified. Only short HOME reports written.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
SOURCE = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
REF = (Path.home() / "FLUXNET_MultiSite_11/stage20_CH_Aws_RH_QC_expansion_audit/"
       "01_low_and_boundary_events_review.csv")
REPORT = Path.home() / "FLUXNET_MultiSite_11/stage28_CH_Aws_qc_review"
STAGE28 = pd.date_range("2006-01-14 14:30", "2006-01-14 18:30", freq="30min")

def main():
    if not SOURCE.is_file() or not REF.is_file():
        raise RuntimeError("STOP: missing RH25A source or Stage20 reference")
    names = ["time", "RH_IMPLIED_PCT", "VPD_F_SOURCE", "VPD_F_QC"]
    x = pd.read_csv(SOURCE, usecols=names, low_memory=False)
    x["time"] = pd.to_datetime(x["time"], errors="raise")
    if not x["time"].is_unique:
        raise RuntimeError("STOP: duplicate timestamps")
    x["VPD_F_QC"] = pd.to_numeric(x["VPD_F_QC"], errors="coerce")
    x["RH_IMPLIED_PCT"] = pd.to_numeric(x["RH_IMPLIED_PCT"], errors="coerce")
    x["previous_RH_pct"] = x["RH_IMPLIED_PCT"].shift(1)
    x["next_RH_pct"] = x["RH_IMPLIED_PCT"].shift(-1)
    x["previous_source"] = x["VPD_F_SOURCE"].shift(1)
    x["next_source"] = x["VPD_F_SOURCE"].shift(-1)
    mask = (x["VPD_F_SOURCE"].eq("EUF_F")
            & x["VPD_F_QC"].eq(2)
            & x["RH_IMPLIED_PCT"].lt(10))
    all77 = x.loc[mask].copy()
    if len(all77) != 77:
        raise RuntimeError(f"STOP: expected 77 reviewed RH25A rows, got {len(all77)}")
    corrected = all77["time"].isin(STAGE28)
    if corrected.sum() != 9:
        raise RuntimeError("STOP: expected nine independent v4 candidate timestamps")
    remain = all77.loc[~corrected].copy()
    if len(remain) != 68:
        raise RuntimeError("STOP: remaining screened records differ from expected 68")

    ref = pd.read_csv(REF, low_memory=False)
    ref["time"] = pd.to_datetime(ref["time_local_standard_UTCplus1"], errors="raise")
    if not ref["time"].is_unique:
        raise RuntimeError("STOP: duplicate Stage20 reference timestamps")
    fields = ["time", "era5_RH_pct", "era5_land_RH_pct",
              "era5_vs_land_diff_pp", "REF_AGREE_LE15PP"]
    remain = remain.merge(ref[fields], on="time", how="left", validate="one_to_one")
    remain["ERA5Land_minus_source_pp"] = (remain["era5_land_RH_pct"]
                                           - remain["RH_IMPLIED_PCT"])
    remain["ERA5_minus_source_pp"] = (remain["era5_RH_pct"]
                                       - remain["RH_IMPLIED_PCT"])
    remain["source_transition_before"] = (remain["VPD_F_SOURCE"]
                                            != remain["previous_source"])
    remain["source_transition_after"] = (remain["VPD_F_SOURCE"]
                                           != remain["next_source"])
    remain["reference_status"] = np.where(
        remain["era5_land_RH_pct"].notna() & remain["era5_RH_pct"].notna(),
        "CACHED_TWO_REANALYSIS_REFERENCES_NOT_OBSERVATION_QC",
        "NO_STAGE20_REFERENCE_IN_EXISTING_CACHE")
    remain = remain.sort_values("time")
    remain["period_id"] = (remain["time"].diff()
                           .ne(pd.Timedelta(minutes=30))).cumsum()
    summary = remain.groupby("period_id", as_index=False).agg(
        start=("time", "min"), end=("time", "max"),
        records=("time", "size"),
        min_RH=("RH_IMPLIED_PCT", "min"),
        mean_RH=("RH_IMPLIED_PCT", "mean"),
        mean_ERA5_RH=("era5_RH_pct", "mean"),
        mean_ERA5Land_RH=("era5_land_RH_pct", "mean"),
        n_ERA5=("era5_RH_pct", "count"),
        n_ERA5Land=("era5_land_RH_pct", "count"))
    summary["hours"] = summary["records"] / 2
    remain["review_decision"] = "UNDECIDED_DO_NOT_AUTO_REPLACE"
    REPORT.mkdir(parents=True, exist_ok=True)
    detail = REPORT / "03_remaining_68_evidence_only.csv"
    periods = REPORT / "04_remaining_periods_evidence_only.csv"
    remain.to_csv(detail, index=False)
    summary.to_csv(periods, index=False)
    print("RH25A reviewed low-RH records: 77")
    print("Already addressed by separate Stage28 v4 2006 trial: 9")
    print("Still UNRESOLVED in v4 multi-year context: 68")
    print("Remaining consecutive periods:", len(summary))
    print("\nBy year:")
    print(remain.groupby(remain["time"].dt.year).size().to_string())
    print("\nLong periods:")
    print(summary.sort_values("records", ascending=False).head(20).to_string(index=False))
    print("\nReference coverage by year:")
    print(remain.groupby(remain["time"].dt.year).agg(
        n=("time", "size"), era5=("era5_RH_pct", "count"),
        era5land=("era5_land_RH_pct", "count")).to_string())
    print("\nSaved:", detail)
    print("Saved:", periods)
    print("READ-ONLY source analysis; only report CSV files written; no model jobs")
    print("Absence of reference evidence is NOT evidence of data validity.")

if __name__ == "__main__":
    main()

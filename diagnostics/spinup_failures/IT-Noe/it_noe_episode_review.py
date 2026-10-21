#!/usr/bin/env python3
"""Read-only grouping of IT-Noe meteorological flags into review episodes.

Input: selected_years_joined_readonly.csv from it_noe_era_source_audit.py.
Never changes forcing, DATM, case, surface, or restart files.
"""
import argparse
from pathlib import Path
import pandas as pd

FLAGS = ["FLAG_TA_below_minus8C", "FLAG_TA_jump_over8C", "FLAG_TA_ERA_disagree15C", "FLAG_RH_below10pct"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path.home() / "IT-Noe_source_diagnosis/era_comparison_full_20261021/selected_years_joined_readonly.csv")
    ap.add_argument("--out", type=Path, default=Path.home() / "IT-Noe_source_diagnosis/episode_review_v1")
    ap.add_argument("--max-gap-hours", type=float, default=2.0)
    args = ap.parse_args()
    if not args.input.is_file():
        ap.error("Input not found: " + str(args.input))
    if not 0 < args.max_gap_hours <= 24:
        ap.error("--max-gap-hours must be >0 and <=24")
    if args.out.exists() and any(args.out.iterdir()):
        ap.error("Output directory is not empty: " + str(args.out))
    d = pd.read_csv(args.input, parse_dates=["time"], low_memory=False).sort_values("time")
    required = ["time", "TA_F", "TA_ERA", "RH_IMPLIED_PCT", "TA_F_SOURCE", "TA_F_QC"]
    missing = set(required).difference(d.columns)
    if missing:
        ap.error("Missing columns: " + repr(sorted(missing)))
    if d.time.isna().any() or d.time.duplicated().any():
        ap.error("Invalid or duplicate timestamps")
    d = d.reset_index(drop=True)
    d["year"] = d.time.dt.year
    for v in ("TA_F", "TA_ERA", "RH_IMPLIED_PCT", "TA_F_QC"):
        d[v] = pd.to_numeric(d[v], errors="coerce")
    d["delta_TA_C"] = d.TA_F - d.TA_ERA
    d["jump_TA_C"] = d.groupby("year").TA_F.diff()
    d[FLAGS[0]] = d.TA_F < -8
    d[FLAGS[1]] = d.jump_TA_C.abs() > 8
    d[FLAGS[2]] = d.delta_TA_C.abs() > 15
    d[FLAGS[3]] = d.RH_IMPLIED_PCT < 10
    d["ANY_REVIEW_FLAG"] = d[FLAGS].any(axis=1)
    flagged = d.loc[d.ANY_REVIEW_FLAG].copy()
    if len(flagged):
        flagged["episode_id"] = (flagged.time.diff().gt(pd.Timedelta(hours=args.max_gap_hours)).fillna(True).cumsum() + 1).astype(int)
    else:
        flagged["episode_id"] = pd.Series(dtype=int)
    records = []
    for eid, g in flagged.groupby("episode_id"):
        records.append({
            "episode_id": eid, "start": g.time.min(), "end": g.time.max(),
            "year": g.time.min().year, "flagged_halfhours": len(g),
            "selected_sources": ";".join(sorted(g.TA_F_SOURCE.dropna().astype(str).unique())),
            "maximum_abs_TA_ERA_difference_C": g.delta_TA_C.abs().max(),
            "maximum_abs_halfhour_jump_C": g.jump_TA_C.abs().max(),
            "minimum_RH_pct": g.RH_IMPLIED_PCT.min(),
            "review_status": "REVIEW_REQUIRED_NOT_APPROVED_FOR_REPLACEMENT",
            **{v: int(g[v].sum()) for v in FLAGS}
        })
    episodes = pd.DataFrame(records)
    args.out.mkdir(parents=True, exist_ok=True)
    episodes.to_csv(args.out / "meteorological_review_episodes.csv", index=False)
    flagged.to_csv(args.out / "flagged_halfhours_with_episode_ids.csv", index=False)
    d.groupby("year")[FLAGS + ["ANY_REVIEW_FLAG"]].sum().astype(int).to_csv(args.out / "yearly_flags_crosscheck.csv")
    d.loc[(d.time >= "2010-05-27 18:00") & (d.time <= "2010-05-28 10:00")].to_csv(args.out / "2010_failure_context_with_ERA5.csv", index=False)
    print("FULL RECORDS:", len(d), "FLAGGED:", len(flagged), "EPISODES:", len(episodes))
    print("\nANNUAL COUNTS\n", d.groupby("year")[FLAGS + ["ANY_REVIEW_FLAG"]].sum().to_string())
    if len(episodes):
        print("\nTOP EPISODES\n", episodes.sort_values("maximum_abs_TA_ERA_difference_C", ascending=False).head(20).to_string(index=False))
    print("\nREPORT:", args.out)
    print("READ-ONLY: NO FORCING OR RESTART CHANGED")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""AmeriFlux Stage 14: read-only CA-Man VPD repair scenario diagnostics.

Compare ORIGINAL, ROUTINE_ONLY (Stage13 routine-review episodes), and
ALL_PROPOSALS (all validated Stage12/13 candidate half-hours), strictly IN
MEMORY. No candidate is approved or applied to any persisted forcing series.

Inputs: pinned raw FLUXMET_HH and Stage13 episode/candidate CSV. Outputs:
small scenario-level and annual metrics, plus candidate/episode inventories.
No raw/processed meteorology, surfaces, DATM, NetCDF, cases, or Slurm jobs
are changed. 101/102/105% RH screens remain scientific review thresholds.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
BATCH = Path(__file__).resolve().parents[2]
APPROVAL = "UNAPPLIED_SENSITIVITY_ONLY"


def rows(path, delimiter=","):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def save(path, items, columns):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(items)


def latest_report(root, site, explicit):
    if explicit is not None:
        report = explicit.expanduser()
    else:
        matches = sorted(
            x for x in root.glob("stage13_episode_risks_" + site + "_*")
            if (x / "all_candidate_rows_with_episode_risks.csv").is_file()
        )
        if not matches:
            raise RuntimeError("No Stage13 report for " + site + " in " + str(root))
        report = matches[-1]
    need = report / "all_candidate_rows_with_episode_risks.csv"
    if not need.is_file():
        raise RuntimeError("Stage13 candidate report missing: " + str(need))
    return report


def series(path):
    columns = ["TIMESTAMP_START", "TA_F", "VPD_F", "PA_F", "VPD_F_QC"]
    # CA-Man has ~15 years of half-hour data, safely within ordinary pandas memory.
    table = pd.read_csv(path, usecols=columns, dtype={"TIMESTAMP_START": "string"})
    t = pd.to_datetime(
        table["TIMESTAMP_START"].str.strip().str.replace(
            r"\.0$", "", regex=True),
        format="%Y%m%d%H%M", errors="raise")
    if t.duplicated().any() or not t.is_monotonic_increasing:
        raise RuntimeError("Source FLUXMET timestamps duplicate or unsorted")
    for col in columns[1:]:
        values = pd.to_numeric(table[col], errors="coerce")
        table[col] = values.where(np.isfinite(values) & (values > -9990))
    return t, table


def physics(ta, pa, vpd):
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        es = 6.112 * np.exp(np.clip(
            17.67 * ta / (ta + 243.5), -40, 40))
        ea = es - vpd
        den = pa * 1000 - .378 * ea * 100
        q = .622 * ea * 100 / den
        rh = 100 * ea / es
    testable = (np.isfinite(ta) & np.isfinite(pa) & np.isfinite(vpd) &
                (ta >= -80) & (ta <= 65) & (pa >= 50) & (pa <= 110))
    ea_nonpos = testable & (ea <= 0)
    humidity_bad = testable & ((ea <= 0) | (ea > 1.01 * es) |
                               (~np.isfinite(q)) | (q < 0) | (q > .08))
    return {
        "testable":testable, "ea_nonpos":ea_nonpos,
        "humidity_bad":humidity_bad, "rh":rh, "q":q, "es":es,
    }


def count_steps(ts, vpd, select):
    # Only consecutive actual half-hour source stamps contribute. Do not
    # create spurious joins across missing timestamps, leap dates or years.
    t = ts.to_numpy(dtype="datetime64[m]")
    interval_ok = (np.diff(t).astype("timedelta64[m]").astype("int64") == 30)
    x = vpd
    good = (interval_ok & np.isfinite(x[:-1]) & np.isfinite(x[1:]) &
            select[:-1] & select[1:])
    differences = np.abs(np.diff(x))
    return (
        float(differences[good].sum()),
        float(differences[good].max()) if good.any() else None,
        int(good.sum()),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site", default="CA-Man")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--report-root", type=Path, default=REPORTS)
    p.add_argument("--stage13-dir", type=Path)
    args = p.parse_args()

    manifest = rows(BATCH / "sites.tsv", "\t")
    releases = {r["site"]:r["package"] for r in manifest}
    if len(manifest) != 10 or len(releases) != 10:
        raise RuntimeError("Expected ten unique batch sites")
    if args.site not in releases:
        p.error("Unknown site: " + args.site)

    source_dir = args.root / args.site / "forcing" / "raw" / releases[args.site]
    metfiles = sorted(x for x in source_dir.glob("*.csv")
                      if "FLUXMET_HH" in x.name.upper())
    if len(metfiles) != 1:
        raise RuntimeError("Expected one exact release FLUXMET file, found %d" %
                           len(metfiles))
    stage13 = latest_report(args.report_root,args.site,args.stage13_dir)
    candidates = rows(stage13 / "all_candidate_rows_with_episode_risks.csv")
    if not candidates:
        raise RuntimeError("Stage13 has no candidates")
    t, data = series(metfiles[0])
    time_index = pd.DatetimeIndex(t)
    candidate_stamps = pd.to_datetime(
        [r["timestamp_local"] for r in candidates],
        format="%Y-%m-%d %H:%M",errors="raise")
    if candidate_stamps.duplicated().any():
        raise RuntimeError("Duplicate Stage13 candidate timestamps")
    indices = time_index.get_indexer(candidate_stamps)
    if np.any(indices < 0):
        first = int(np.flatnonzero(indices < 0)[0])
        raise RuntimeError("Stage13 timestamp not in source: " +
                           str(candidate_stamps[first]))

    v0 = data["VPD_F"].to_numpy(dtype=float)
    ta = data["TA_F"].to_numpy(dtype=float)
    pa = data["PA_F"].to_numpy(dtype=float)
    vpd_qc = data["VPD_F_QC"].to_numpy(dtype=float)
    raw_physics = physics(ta,pa,v0)
    v_routine = v0.copy()
    v_all = v0.copy()
    routine_count = 0
    episodes = {"ROUTINE_CONTEXT_REVIEW":set(), "ELEVATED_CONTEXT_REVIEW":set()}
    track = []
    for r, idx in zip(candidates,indices):
        if r["site"] != args.site:
            raise RuntimeError("Unexpected site in Stage13 candidate inventory")
        original = float(r["source_VPD_hPa"])
        proposed = float(r["candidate_VPD_hPa"])
        if not np.isfinite(v0[idx]) or not np.isclose(
                v0[idx],original,rtol=1e-8,atol=1e-6):
            raise RuntimeError("Source VPD changed since Stage13 at " +
                               r["timestamp_local"])
        if not np.isfinite(vpd_qc[idx]) or vpd_qc[idx] != 1:
            raise RuntimeError("Stage13 candidate VPD QC is no longer 1")
        if not np.isfinite(proposed) or proposed < 0 or proposed > 125:
            raise RuntimeError("Candidate VPD invalid at " + r["timestamp_local"])
        if not raw_physics["ea_nonpos"][idx]:
            raise RuntimeError("Stage13 candidate is not original EA<=0 at " +
                               r["timestamp_local"])
        candidate_physics = physics(
            np.array([ta[idx]]),np.array([pa[idx]]),np.array([proposed]))
        if not candidate_physics["testable"][0] or candidate_physics["humidity_bad"][0]:
            raise RuntimeError("Candidate physical screen failed at " +
                               r["timestamp_local"])
        risk = r["episode_priority"]
        if risk not in episodes:
            raise RuntimeError("Unexpected Stage13 risk label: " + risk)
        episodes[risk].add(r["episode"])
        v_all[idx] = proposed
        if risk == "ROUTINE_CONTEXT_REVIEW":
            routine_count += 1
            v_routine[idx] = proposed
        track.append({
            "site":args.site, "timestamp_local":r["timestamp_local"],
            "year":candidate_stamps[len(track)].year,
            "episode":r["episode"], "episode_priority":risk,
            "original_VPD_hPa":original,"proposed_VPD_hPa":proposed,
            "applied_to_persisted_data":"NO",
        })

    actual = {"ORIGINAL":v0,
              "ROUTINE_ONLY_UNAPPLIED":v_routine,
              "ALL_PROPOSALS_UNAPPLIED":v_all}
    date_year=t.dt.year.to_numpy()
    valid_noleap=~((t.dt.month.to_numpy()==2)&(t.dt.day.to_numpy()==29))
    yearly = []
    overall = []
    for label,values in actual.items():
        qc=physics(ta,pa,values)
        for yr in sorted(np.unique(date_year)):
            scope=(date_year==yr)&valid_noleap
            total_var,max_jump,valid_steps=count_steps(t,values,scope)
            yearly.append({
                "site":args.site,"scenario":label,"year":int(yr),
                "noleap_rows":int(scope.sum()),
                "humidity_testable":int((qc["testable"]&scope).sum()),
                "ea_nonpositive":int((qc["ea_nonpos"]&scope).sum()),
                "humidity_physically_bad":int((qc["humidity_bad"]&scope).sum()),
                "valid_halfhour_step_pairs":valid_steps,
                "VPD_total_variation_hPa":round(total_var,5),
                "VPD_max_30min_jump_hPa":max_jump,
                "change_status":APPROVAL,
            })
        scope=valid_noleap
        total_var,max_jump,pairs=count_steps(t,values,scope)
        overall.append({
            "site":args.site,"scenario":label,
            "noleap_rows":int(scope.sum()),
            "humidity_testable":int((qc["testable"]&scope).sum()),
            "ea_nonpositive":int((qc["ea_nonpos"]&scope).sum()),
            "humidity_physically_bad":int((qc["humidity_bad"]&scope).sum()),
            "valid_halfhour_step_pairs":pairs,
            "VPD_total_variation_hPa":round(total_var,5),
            "VPD_max_30min_jump_hPa":max_jump,
            "hypothetical_modified_VPD_rows":(
                0 if label=="ORIGINAL" else
                routine_count if label=="ROUTINE_ONLY_UNAPPLIED" else len(track)
            ),
            "approval":APPROVAL,
        })

    if len(track) != len(candidates):
        raise RuntimeError("Lost candidate records")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder=args.report_root/("stage14_vpd_whatif_"+args.site+"_"+stamp)
    folder.mkdir(parents=True,exist_ok=False)
    save(folder/"scenario_overall_metrics.csv",overall,list(overall[0]))
    save(folder/"scenario_yearly_metrics.csv",yearly,list(yearly[0]))
    save(folder/"candidate_inventory_NO_CHANGES_APPLIED.csv",track,list(track[0]))
    print("STAGE14 SUMMARY: site=%s, total_vpd_candidates=%d,"
          " routine_candidate_rows=%d, elevated_candidate_rows=%d" %
          (args.site,len(track),routine_count,len(track)-routine_count))
    print("Stage13 episode counts: routine=%d elevated=%d" %
          (len(episodes["ROUTINE_CONTEXT_REVIEW"]),
           len(episodes["ELEVATED_CONTEXT_REVIEW"])))
    print("Pinned source:",metfiles[0])
    for r in overall:
        print("  %-26s EA<=0=%4d humidity_bad=%4d"
              " total_VPD_variation=%.3f hPa max_step=%s"
              " preview_modified=%d" %
              (r["scenario"],r["ea_nonpositive"],
               r["humidity_physically_bad"],r["VPD_total_variation_hPa"],
               str(r["VPD_max_30min_jump_hPa"]),
               r["hypothetical_modified_VPD_rows"]))
    print("REPORT DIR:",folder)
    print("READ ONLY source; NO proposed values persisted to forcing/NetCDF.")
    print("Routine-review does NOT mean approved; 107 additional CA-Man"
          " flagged source records may still require investigation.")


if __name__=="__main__":
    main()

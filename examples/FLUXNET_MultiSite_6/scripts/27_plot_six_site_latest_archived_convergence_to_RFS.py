#!/usr/bin/env python3
"""Read-only six-site CLM-FATES spin-up snapshots, saved directly to Research Filestore.

Replicates the established stage-14 carbon-pool + monthly EC comparison plots
but uses all *currently safely archived* years (possibly 1000...3000).
Also plots annual PFT vegetation carbon composition, and computes 100/250-year
trends and phase-aligned changes across the last two full DATM forcing cycles.

Examples on IRIDIS6:
    git fetch origin main
    git show origin/main:examples/FLUXNET_MultiSite_6/scripts/27_plot_six_site_latest_archived_convergence_to_RFS.py > ~/fluxnet6_latest_plots.py
    python ~/fluxnet6_latest_plots.py

All inputs (CIME, NetCDF history, original FLUXNET EC) are READ ONLY.
Creates a unique output snapshot under /research/xclimatetbm/ly3n24/
CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots/. No delete/copy of raw nc.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import traceback
import types
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset

SITES = {
    "DE-Hai": (2000, 2025, "DBF"),
    "RU-Fyo": (1998, 2025, "ENF"),
    "DE-Tha": (1996, 2025, "ENF"),
    "DK-Sor": (1996, 2024, "DBF"),
    "NL-Loo": (1997, 2025, "ENF"),
    "IL-Yat": (2000, 2024, "ENF"),
}
UID = "ly3n24"
ROOT = Path("/iridisfs/scratch") / UID / "CLM_FATES"
CASES = ROOT / "cases"
SITES_ROOT = ROOT / "sites/MY_EC_SITE"
SCRATCH_ARCH = Path("/scratch") / UID / "CTSM_FATES_OUTPUTS/archive"
ALIAS_ARCH = Path("/iridisfs/scratch") / UID / "CTSM_FATES_OUTPUTS/archive"
RESEARCH = Path("/research/xclimatetbm") / UID
RAW_RFS = RESEARCH / "CLM_FATES/Spinup_Archives/FLUXNET_MultiSite_6"
OUT_PARENT = RESEARCH / "CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots"
SCRIPT_DIR = "examples/FLUXNET_MultiSite_6/scripts"
RE_H0A = re.compile(r"\.clm2\.h0a\.(\d{4})-01-0[12]-00000\.nc$")
KEYS = ("TOTECOSYSC", "TOTVEGC", "TOTSOMC", "TOTLITC", "FATES_VEGC",
        "FATES_STOREC", "FATES_STRUCTC", "TOTROOTC", "SOILC", "TOTSOILC")
PRIMARY = ("TOTECOSYSC", "FATES_VEGC", "TOTVEGC", "TOTSOMC", "TOTLITC")
FATES_PFT_FIELD = "FATES_VEGC_PF"

def log(*a):
    print(*a, flush=True)

def git_text(repo, revision, rel):
    p = subprocess.run(["git", "-C", str(repo), "show", revision + ":" + rel],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError("Cannot load pinned GitHub plot helper " + rel +
                           "\n" + p.stderr[-900:])
    return p.stdout

def module_from_git(repo, revision, rel, name):
    source = git_text(repo, revision, rel)
    mod = types.ModuleType(name)
    mod.__file__ = str(repo / rel)
    exec(compile(source, mod.__file__, "exec"), mod.__dict__)
    return mod

def nfs_guard():
    if not RESEARCH.is_dir() or not os.access(RESEARCH, os.W_OK):
        raise RuntimeError("Research Filestore is not accessible/writable: " + str(RESEARCH))
    p = subprocess.run(["stat", "-f", "-c", "%T", str(RESEARCH)],
                       capture_output=True, text=True, check=True)
    if p.stdout.strip().lower() not in ("nfs", "nfs4"):
        raise RuntimeError("Research Filestore is not an NFS mount; refusing output.")

def index_history(site, case):
    """Union of RFS historical years + Scratch newly archived years, no run dir."""
    dirs = [
        RAW_RFS / site / case / "archive/lnd/hist",
        ALIAS_ARCH / case / "lnd/hist",
        SCRATCH_ARCH / case / "lnd/hist",
    ]
    found, location = {}, {}
    for hist in dirs:
        if not hist.is_dir():
            continue
        for p in hist.glob(case + ".clm2.h0a.*.nc"):
            m = RE_H0A.search(p.name)
            if not m:
                continue
            y = int(m.group(1))
            if p.is_file() and p.stat().st_size > 100:
                found[y], location[y] = p, str(hist)
    if not found:
        raise FileNotFoundError("No archived h0a history at RFS or Scratch: " + site)
    return found, location

def coordinated_checkpoint(case):
    """Snapshot latest three-component archived restart, not current RUN progress."""
    root = SCRATCH_ARCH / case / "rest"
    valid = []
    if not root.is_dir():
        return None
    for d in root.glob("????-01-01-00000"):
        if not d.is_dir():
            continue
        stamp = d.name
        files = [
            d / (case + "." + prefix + ".r." + stamp + ".nc")
            for prefix in ("cpl", "datm", "clm2")
        ]
        if all(x.is_file() and x.stat().st_size > 1024 for x in files):
            valid.append((int(stamp[:4]), str(d)))
    return max(valid, key=lambda t: t[0]) if valid else None

def read_bif_igbp(site):
    root = SITES_ROOT / site / "forcing/raw"
    found = []
    if root.is_dir():
        for p in root.rglob("*_BIF_*.csv"):
            if "FLUXNET" not in p.name.upper():
                continue
            with p.open(errors="replace", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    if row.get("VARIABLE", "").strip().upper() == "IGBP":
                        val = row.get("DATAVALUE", "").strip().upper()
                        if val:
                            found.append(val)
    distinct = sorted(set(found))
    return distinct

def get_param_pfts(case):
    nml = CASES / case / "CaseDocs/lnd_in"
    if not nml.is_file():
        raise FileNotFoundError("Missing effective namelist: " + str(nml))
    txt = nml.read_text(errors="replace")
    match = re.search(r"(?im)^\s*fates_paramfile\s*=\s*['\"]?([^'\"\s!]+)", txt)
    if not match:
        raise RuntimeError("Missing FATES parameter file in effective namelist: " + case)
    path = Path(match.group(1))
    if not path.is_file() or path.suffix.lower() != ".json":
        raise RuntimeError("Expected existing FATES JSON parameter file: " + str(path))
    with path.open() as f:
        j = json.load(f)
    n = int(j["dimensions"]["fates_pft"])
    names = list(j["parameters"]["fates_pftname"]["data"])
    if len(names) != n:
        raise ValueError("Mismatch between PFT names and dimension in " + str(path))
    options = ("use_fates", "use_fates_sp", "use_fates_fixed_biogeog",
               "use_fates_nocomp", "create_crop_landunit", "use_crop")
    flags = {}
    for k in options:
        m = re.search(r"(?im)^\s*" + re.escape(k) + r"\s*=\s*([^!\n]+)", txt)
        flags[k] = m.group(1).strip() if m else None
    return names, flags, str(path)

def read_all_carbon_and_pft(site, years, found, old):
    """One file-open per annual NetCDF; never sum PFT-resolved and scalar pools."""
    rows, pft_rows, units, variables = [], [], {}, None
    pft_dim = None
    for i, year in enumerate(years):
        with Dataset(found[year], "r") as ds:
            if variables is None:
                variables = []
                for name in KEYS:
                    if name not in ds.variables:
                        continue
                    v = ds[name]
                    if "time" not in v.dimensions:
                        continue
                    if any(len(ds.dimensions[d]) != 1
                           for d in v.dimensions if d != "time"):
                        continue
                    unit = str(getattr(v, "units", "")).strip()
                    factor, _, csv_unit = old.unit_type(unit)
                    units[name] = {"factor": factor, "input": unit, "output": csv_unit}
                    variables.append(name)
                if not variables:
                    raise RuntimeError("No scalar ecosystem-carbon variables in " + str(found[year]))
            record = {"Site": site, "ModelYear": year,
                      "SpinupYear": year - SITES[site][0] + 1}
            for name in variables:
                if name not in ds.variables:
                    raise RuntimeError(f"{site}: variable {name} missing at model year {year}")
                record[name] = old.point_time_mean(ds[name]) * units[name]["factor"]
            rows.append(record)
            if FATES_PFT_FIELD in ds.variables:
                v = ds[FATES_PFT_FIELD]
                axes = [d for d in v.dimensions if "pft" in d.lower()]
                time_axes = [d for d in v.dimensions if d.lower() == "time"]
                if len(axes) == 1 and len(time_axes) == 1:
                    extra = [d for d in v.dimensions
                             if d not in (axes[0], time_axes[0])]
                    if all(len(ds.dimensions[d]) == 1 for d in extra):
                        x = np.ma.asarray(v[:], dtype=np.float64).filled(np.nan)
                        a = np.moveaxis(x, [v.dimensions.index(axes[0]),
                                            v.dimensions.index(time_axes[0])], [0, 1])
                        a = a.reshape(a.shape[0], a.shape[1], -1)
                        if a.shape[2] == 1:
                            with np.errstate(invalid="ignore"):
                                vec = np.nanmean(a[:, :, 0], axis=1)
                            if pft_dim is None:
                                pft_dim = len(vec)
                            if len(vec) != pft_dim:
                                raise RuntimeError("PFT dimension changed mid-simulation")
                            pft_rows.append({"ModelYear": year,
                                             "SpinupYear": record["SpinupYear"],
                                             "pfts": vec})
        if (i + 1) % 250 == 0 or i + 1 == len(years):
            log(f"  {site}: {i+1}/{len(years)} archived annual files read")
    if not variables:
        raise RuntimeError("No recognized carbon pool outputs")
    return pd.DataFrame(rows), pft_rows, variables, units

def last_aligned_cycles(series_map, available, start, forcing_len, cap):
    """Find last two adjacent, complete, aligned forcing cycles within snapshot."""
    kmax = (cap - start) // forcing_len - 1
    for k in range(kmax, 0, -1):
        yr0 = start + k * forcing_len
        years_new = list(range(yr0, yr0 + forcing_len))
        years_old = list(range(yr0 - forcing_len, yr0))
        if all(y in available for y in years_new + years_old):
            return years_old, years_new
    return [], []

def convergence(carbon, names, units, first, forcing_len, cap):
    avail = {int(row.ModelYear): row for row in carbon.itertuples(index=False)}
    oldyears, newyears = last_aligned_cycles(None, avail, first, forcing_len, cap)
    report = []
    for name in names:
        v = carbon[["ModelYear", name]].dropna()
        byyear = dict(zip(v.ModelYear.astype(int), v[name].astype(float)))
        cur_end = min(cap - 1, max(byyear))
        base = {"Variable": name, "Units": units[name]["output"],
                "ModelYearAtSnapshot": cur_end,
                "SnapshotValue": byyear.get(cur_end, float("nan")),
                "ForcingCycleYears": forcing_len,
                "AlignedCyclePrevious": (f"{oldyears[0]}-{oldyears[-1]}" if oldyears else ""),
                "AlignedCycleLatest": (f"{newyears[0]}-{newyears[-1]}" if newyears else "")}
        for n in (100, 250):
            yy = list(range(cap - n, cap))
            if all(y in byyear for y in yy):
                x = np.arange(n, dtype=float)
                v2 = np.array([byyear[y] for y in yy])
                slope = float(np.polyfit(x, v2, 1)[0])
                mean = float(np.mean(v2))
                base[f"Last{n}y_slope_per_year"] = slope
                base[f"Last{n}y_trend_pct"] = (
                    100 * slope * n / abs(mean) if abs(mean) > 1e-10 else float("nan"))
            else:
                base[f"Last{n}y_slope_per_year"] = float("nan")
                base[f"Last{n}y_trend_pct"] = float("nan")
        if oldyears and all(y in byyear for y in oldyears + newyears):
            x = np.array([byyear[y] for y in oldyears])
            y = np.array([byyear[t] for t in newyears])
            den = max(float(np.mean(np.abs(x))), 1e-9)
            base["AlignedCycleMeanChange_pct"] = 100.0 * float((y.mean()-x.mean()))/den
            base["AlignedCycleMeanAbsChange_pct"] = 100.0 * float(np.mean(np.abs(y-x)))/den
        else:
            base["AlignedCycleMeanChange_pct"] = float("nan")
            base["AlignedCycleMeanAbsChange_pct"] = float("nan")
        rel = base.get("Last100y_trend_pct")
        cyc = base["AlignedCycleMeanAbsChange_pct"]
        base["Exploratory_1pct_100yr_and_cycle_screen"] = (
            "LOW_DRIFT" if np.isfinite(rel) and np.isfinite(cyc)
            and abs(rel) < 1 and cyc < 1 else "NOT_LOW_OR_UNDETERMINED")
        report.append(base)
    return pd.DataFrame(report)

def plot_carbon(carbon, names, units, site, out, tail=None):
    n = len(carbon)
    if tail:
        sub = carbon[carbon["SpinupYear"] >= max(1, carbon["SpinupYear"].max()-tail+1)]
        suffix = "02_carbon_pools_last250years.png"
        title = f"{site} | latest {min(tail, n)} archived model years"
    else:
        sub = carbon
        suffix = "01_carbon_pools_annual_mean.png"
        title = f"{site} | all available model years up to last complete checkpoint"
    show = [x for x in KEYS if x in names][:6]
    rows = (len(show)+1)//2
    fig, axs = plt.subplots(rows, 2, figsize=(15, 3.9*rows), sharex=True,
                            squeeze=False)
    for ax, name in zip(axs.flat, show):
        ax.plot(sub["SpinupYear"], sub[name], lw=1.35)
        ax.set_title(name)
        ax.set_ylabel(units[name]["output"])
        ax.grid(alpha=.25)
    for ax in list(axs.flat)[len(show):]:
        ax.set_visible(False)
    for ax in axs[-1]:
        ax.set_xlabel("Elapsed spin-up model years")
    fig.suptitle(title)
    fig.tight_layout()
    dest = out / (site+"_"+suffix)
    fig.savefig(dest, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return dest

def plot_pft(pft_rows, names, site, out, igbp):
    if not pft_rows or not names:
        return None, None
    x = np.array([r["SpinupYear"] for r in pft_rows])
    a = np.stack([r["pfts"] for r in pft_rows])
    if a.shape[1] != len(names):
        raise RuntimeError(f"PFT size mismatch: {a.shape[1]} outputs vs {len(names)} parameter types")
    if np.nanmin(a) < -1e-7:
        raise RuntimeError("Unexpected negative FATES_VEGC_PF")
    totals = np.nansum(a, axis=1)
    shares = np.divide(a, totals[:, None], out=np.full_like(a, np.nan),
                       where=totals[:, None] > 1e-10) * 100
    top_indices = sorted(range(len(names)), key=lambda i: float(np.nanmax(a[:, i])),
                         reverse=True)[:6]
    top_indices = [i for i in top_indices if np.nanmax(a[:, i]) > 1e-8]
    fig, ax = plt.subplots(figsize=(12.7, 5.0))
    for i in top_indices:
        ax.plot(x, shares[:, i], lw=1.5, label=f"PFT {i+1} {names[i]}")
    ax.set_ylim(0, 103)
    ax.set_xlabel("Elapsed spin-up model years")
    ax.set_ylabel("Share of FATES vegetation carbon (%)")
    ax.set_title(f"{site} | observed EC IGBP: {igbp} | evolving FATES PFT carbon shares")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=.25)
    fig.tight_layout()
    dest = out / (site+"_04_FATES_PFT_VEGC_evolution.png")
    fig.savefig(dest, dpi=220, bbox_inches="tight")
    plt.close(fig)
    data = pd.DataFrame({"SpinupYear": x})
    for i in range(len(names)):
        data[f"PFT{i+1:02d}_{names[i]}_VEGC_pct"] = shares[:, i]
    data.to_csv(out / (site+"_FATES_PFT_VEGC_annual_pct.csv"), index=False)
    final = a[-1]
    total = float(final.sum())
    maxslot = int(final.argmax()) if total > 1e-10 else None
    pft_summary = {"last_PFT_model_year": int(pft_rows[-1]["ModelYear"]),
                   "dominant_PFT_name": names[maxslot] if maxslot is not None else "NONE",
                   "dominant_PFT_slot": maxslot+1 if maxslot is not None else None,
                   "dominant_VEGC_pct": float(100*final[maxslot]/total) if maxslot is not None else None}
    return dest, pft_summary

def flux_comparison(site, found, cap, out, old, core, min_halfhour, min_days):
    first, last, _ = SITES[site]
    n = last-first+1
    limited = {y:p for y,p in found.items() if first <= y < cap}
    _, modelyears = core.latest_complete_cycle(limited, first, last)
    raw = SITES_ROOT / site / "forcing/raw"
    obsfile, gppcol = core.find_flux_file(raw, "GPP_DT_VUT_REF", None)
    model = core.fates_daily([(y,limited[y]) for y in modelyears], first, last)
    obs = core.ec_daily(obsfile, gppcol, first, last, min_halfhour)
    daily = model.merge(obs, on="date", how="left", validate="one_to_one")
    gm = core.paired_monthly(daily, "EC_GPP", "FATES_GPP", min_days)
    nm = core.paired_monthly(daily, "EC_NEE", "FATES_NEE", min_days)
    monthly = gm.merge(nm, on="date", how="outer", validate="one_to_one")
    for flux in ("GPP", "NEE"):
        if int((monthly[f"EC_{flux}"].notna() & monthly[f"FATES_{flux}"].notna()).sum()) < 2:
            raise RuntimeError(f"Insufficient comparable monthly {flux} pairs")
    monthly.to_csv(out/(site+"_monthly_FATES_vs_EC.csv"),index=False)
    metrics, plot = old.monthly_overview(monthly, site, modelyears,
                                          (first,last), out, core)
    metrics.to_csv(out/(site+"_monthly_metrics.csv"),index=False)
    return plot, modelyears, obsfile, gppcol, metrics

def process_site(site, out_root, old, core, min_halfhour, min_days):
    first, last, expect_igbp = SITES[site]
    case = site + "_FATES_SPINUP500"
    core.verify_stream(CASES/case, first, last)
    pfts, flags, paramfile = get_param_pfts(case)
    igbps = read_bif_igbp(site)
    found, provenance = index_history(site, case)
    ckpt = coordinated_checkpoint(case)
    # A complete three-component checkpoint bounds the endorsed history.
    # If no restart in active Scratch, analyse contiguous archived hist only,
    # and mark that it has NOT been checkpoint-validated.
    cap = ckpt[0] if ckpt is not None else max(found)+1
    avail = {y for y in found if first <= y < cap}
    if not avail:
        raise RuntimeError(f"{site}: no archived histories before checkpoint {cap}")
    years = sorted(avail)
    missing = sorted(set(range(first, cap))-avail)
    if missing:
        log(f"  {site}: WARNING {len(missing)} missing annual h0a model years "
            f"before checkpoint {cap}; first={missing[:12]}")
    log(f"  {site}: checkpoint={ckpt} | h0a available={len(years)} | "
        f"model-year range {min(years)}-{max(years)}")
    out = out_root/site
    out.mkdir(exist_ok=False)
    carbon, pft_rows, variables, units = read_all_carbon_and_pft(site, years, found, old)
    carbon.to_csv(out/(site+"_carbon_annual_means.csv"),index=False)
    diag = convergence(carbon, variables, units, first, last-first+1, cap)
    diag.to_csv(out/(site+"_convergence_metrics.csv"),index=False)
    plots = []
    plots.append(str(plot_carbon(carbon,variables,units,site,out)))
    plots.append(str(plot_carbon(carbon,variables,units,site,out,tail=250)))
    pft_plot, pft_summary = plot_pft(pft_rows,pfts,site,out,
                                     ",".join(igbps) if igbps else expect_igbp)
    if pft_plot:
        plots.append(str(pft_plot))
    flux_meta, flux_error = {}, None
    try:
        flplot, modelyears, obsfile, gppcol, score = flux_comparison(
            site, found, cap, out, old, core, min_halfhour, min_days)
        plots.append(str(flplot))
        flux_meta = {"cycle_model_years": [modelyears[0],modelyears[-1]],
                     "original_ec_flux_file": str(obsfile),
                     "gpp_column":gppcol,
                     "monthly_metrics":score.to_dict(orient="records")}
        log("  MONTHLY EC:",score[["Flux","N","R2","RMSE","Bias"]].to_string(index=False))
    except Exception as exc:
        flux_error = f"{type(exc).__name__}: {exc}"
        log("  WARNING EC plot unavailable:", flux_error)
    notes = {
        "site":site,"case":case,"data_assessed_at_utc":datetime.now(timezone.utc).isoformat(),
        "initial_model_start_year":first,"forcing_years":[first,last],
        "source_model_years":[years[0],years[-1]],"archived_history_count":len(years),
        "last_three_component_checkpoint":ckpt[1] if ckpt else None,
        "last_three_component_checkpoint_modelyear":ckpt[0] if ckpt else None,
        "checkpoint_verified_by_file_presence_only":ckpt is not None,
        "missing_years_before_checkpoint":missing[:50],
        "missing_years_total":len(missing),
        "IGBP_from_original_BIF":igbps,"repository_IGBP":expect_igbp,
        "fates_flags":flags,"fates_paramfile":paramfile,
        "PFT":pft_summary,"plots":plots,"flux":flux_meta,
        "flux_error":flux_error,
        "carbon_units":units,
        "important_limitations":[
            "Numerical 1%/100yr is an exploratory drift SCREEN, not an equilibrium certificate.",
            "Forcing phase alignment uses complete adjacent original DATM cycles.",
            "Observed IGBP and simulated PFT biomass percentages are different metrics.",
            "NetCDF h0a may have been moved to Research Filestore; no active run files are read.",
            "Missing checkpoints or annual histories prohibit a complete run claim.",
            "No site-specific tree inventory or harvesting was applied in the original Full FATES run."]
    }
    (out/(site+"_metadata.json")).write_text(json.dumps(notes,indent=2,ensure_ascii=False,default=str)+"\n")
    focus = diag[diag.Variable.isin(PRIMARY)]
    log("  CONVERGENCE:")
    if len(focus):
        log(focus[["Variable","Last100y_trend_pct",
                   "AlignedCycleMeanAbsChange_pct",
                   "Exploratory_1pct_100yr_and_cycle_screen"]].to_string(index=False))
    chosen = next((v for v in PRIMARY if v in set(diag.Variable)),variables[0])
    metric = diag.loc[diag.Variable==chosen].iloc[0]
    return {
        "Site":site,"Status":"OK" if not flux_error else "PARTIAL_EC_FLUX",
        "ArchivedYears":len(years),"LastModelYear":int(years[-1]),
        "LastCheckpointElapsedYears":ckpt[0]-first if ckpt else None,
        "MissingHistYears":len(missing),"BIF_IGBP":";".join(igbps),
        "DominantFATESPFT":(pft_summary or {}).get("dominant_PFT_name"),
        "DominantFATESVEGC_pct":(pft_summary or {}).get("dominant_VEGC_pct"),
        "ConvergenceFocusVariable":chosen,
        "Last100yrTrend_pct":metric.get("Last100y_trend_pct"),
        "AlignedCycleAbsChange_pct":metric.get("AlignedCycleMeanAbsChange_pct"),
        "ECFluxProblem":flux_error or "",
        "ResultsDirectory":str(out)
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.home()/"CLM-FATES-single-site-workflows")
    parser.add_argument("--sites", nargs="+", choices=tuple(SITES), default=list(SITES))
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--min-halfhour", type=int, default=40)
    parser.add_argument("--min-days", type=int, default=20)
    args = parser.parse_args()
    nfs_guard()
    repo = args.repo.resolve()
    code_sha = subprocess.run(["git","-C",str(repo),"rev-parse","origin/main"],
                              capture_output=True,text=True,check=True).stdout.strip()
    old = module_from_git(repo,code_sha,SCRIPT_DIR+"/14_plot_five_site_spinup1000.py","stage14_figures")
    core = module_from_git(repo,code_sha,SCRIPT_DIR+"/10_compare_six_site_latest_complete_cycle.py","stage10_ec_core")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = args.output_root or OUT_PARENT / (stamp+"_archive_snapshot")
    if dest.exists():
        raise RuntimeError("Refusing to overwrite existing RFS snapshot: "+str(dest))
    try:
        dest.resolve().relative_to(OUT_PARENT.resolve())
    except ValueError:
        raise RuntimeError("Output path must be inside designated Research Filestore folder")
    dest.mkdir(parents=True)
    log("RESEARCH FILESTORE OUTPUT:",dest)
    log("GitHub revision pinned:", code_sha)
    log("No inputs will be modified. Only archived h0a, no active run directory.")
    summary=[]
    for site in args.sites:
        log("\n"+"="*20+" "+site+" "+"="*20)
        try:
            summary.append(process_site(site,dest,old,core,args.min_halfhour,args.min_days))
        except Exception as exc:
            log("ERROR:",site,type(exc).__name__,str(exc))
            traceback.print_exc()
            summary.append({"Site":site,"Status":"FAILED",
                            "ECFluxProblem":f"{type(exc).__name__}: {exc}"})
    df=pd.DataFrame(summary)
    df.to_csv(dest/"six_site_latest_checkpoint_convergence_summary.csv",index=False)
    (dest/"RUN_INFO.json").write_text(json.dumps({
        "repository_sha":code_sha,"created_utc":stamp,"requested_sites":args.sites,
        "Research_Filestore_root":str(dest),
        "interpretation":"Interim exploratory convergence diagnostics of archived histories; "
                         "not proof of equilibrium or observed IGBP consistency.",
        "results":summary},indent=2,ensure_ascii=False,default=str)+"\n")
    log("\nFINAL SIX-SITE CHECKPOINT SUMMARY")
    columns=[x for x in ("Site","Status","LastCheckpointElapsedYears",
                          "ArchivedYears","MissingHistYears","DominantFATESPFT",
                          "Last100yrTrend_pct","AlignedCycleAbsChange_pct") if x in df.columns]
    log(df[columns].to_string(index=False))
    log("PLOTS AND REPORTS:",dest)
    return 1 if any(row["Status"]=="FAILED" for row in summary) else 0

if __name__=="__main__":
    raise SystemExit(main())

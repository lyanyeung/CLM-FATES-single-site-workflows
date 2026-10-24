#!/usr/bin/env python3
"""Read-only science and opt-in GitHub publication for the 36 verified-complete
FLUXNET_MultiSite_6/_8/_11/_13 sites. IT-Noe/CH-Aws are excluded.

Scientific algorithms reused unchanged from six-site stages 10, 14, 27 and
eleven-site stage 19: archived h0a annual pools, forcing-phase-aligned cycle,
FLUXNET EC GPP_DT_VUT_REF / NEE_VUT_REF, PFT-resolved vegetation carbon.

IRIDIS6:
  python3 -B 31_crossbatch_convergence_ec_36sites.py audit
  python3 -B 31_crossbatch_convergence_ec_36sites.py run --batch all --publish
  python3 -B 31_crossbatch_convergence_ec_36sites.py publish --snapshot /research/.../actual_snapshot
No model runs, case changes, forcing writes, or archive deletions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import traceback
import shutil
import types
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

UID = "ly3n24"
REPO = Path.home() / "CLM-FATES-single-site-workflows"
ROOT = Path("/iridisfs/scratch") / UID / "CLM_FATES"
SITES_ROOT = ROOT / "sites/MY_EC_SITE"
CASES = ROOT / "cases"
SCRATCH_ARCH = Path("/scratch") / UID / "CTSM_FATES_OUTPUTS/archive"
ALIAS_ARCH = Path("/iridisfs/scratch") / UID / "CTSM_FATES_OUTPUTS/archive"
RFS = Path("/research/xclimatetbm") / UID / "CLM_FATES"
HOME_OUTPUT = Path.home() / "FLUXNET36_derived"
SCRIPT6 = "examples/FLUXNET_MultiSite_6/scripts/"
SCRIPT11 = "examples/FLUXNET_MultiSite_11/scripts/"

# Original forcing-year periods from the site-specific CIME setup scripts.
# One row: site, first model/forcing year, last forcing year, actual CIME case.
ROWS = {
    "6": [
        ("DE-Hai",2000,2025,"DE-Hai_FATES_SPINUP500"),
        ("RU-Fyo",1998,2025,"RU-Fyo_FATES_SPINUP500"),
        ("DE-Tha",1996,2025,"DE-Tha_FATES_SPINUP500"),
        ("DK-Sor",1996,2024,"DK-Sor_FATES_SPINUP500"),
        ("NL-Loo",1997,2025,"NL-Loo_FATES_SPINUP500"),
        ("IL-Yat",2000,2024,"IL-Yat_FATES_SPINUP500")],
    "8": [
        ("CZ-BK1",2004,2025,"CZ-BK1_FATES_SPINUP500"),
        ("IT-Ren",1999,2025,"IT-Ren_FATES_SPINUP500"),
        ("FR-Hes",1997,2025,"FR-Hes_FATES_SPINUP500"),
        ("FR-FBn",2008,2024,"FR-FBn_FATES_SPINUP500"),
        ("DE-Hzd",2010,2025,"DE-Hzd_FATES_SPINUP500"),
        ("CH-Dav",1997,2025,"CH-Dav_FATES_SPINUP500"),
        ("BE-Vie",1996,2025,"BE-Vie_FATES_SPINUP500"),
        ("IT-Lav",2003,2020,"IT-Lav_FATES_SPINUP500")],
    "11": [
        ("BE-Bra",1996,2025,"BE-Bra_FATES_SPINUP500_11P"),
        ("FR-Fon",2005,2025,"FR-Fon_FATES_SPINUP500_11P"),
        ("GL-ZaH",2000,2025,"GL-ZaH_FATES_SPINUP500_11P"),
        ("AT-Neu",2002,2020,"AT-Neu_FATES_SPINUP500_11P"),
        ("FI-Sod",2001,2025,"FI-Sod_FATES_SPINUP500_11P"),
        ("CH-Cha",2005,2024,"CH-Cha_FATES_SPINUP500_11P"),
        ("CH-Fru",2005,2024,"CH-Fru_FATES_SPINUP500_11P"),
        ("CH-Lae",2004,2024,"CH-Lae_FATES_SPINUP500_11P"),
        ("CZ-Stn",2010,2024,"CZ-Stn_FATES_SPINUP500_11P")],
    "13": [
        ("DE-Lnf",2002,2024,"DE-Lnf_FATES_SPINUP1000_S30SHARED"),
        ("DE-Obe",2008,2025,"DE-Obe_FATES_SPINUP1000_S30SHARED"),
        ("ES-Agu",2006,2024,"ES-Agu_FATES_SPINUP1000_S30SHARED"),
        ("ES-LJu",2004,2024,"ES-LJu_FATES_SPINUP1000_S30SHARED"),
        ("IT-Col",1996,2014,"IT-Col_FATES_SPINUP1000_S30SHARED"),
        ("DE-Gri",2004,2025,"DE-Gri_FATES_SPINUP1000_S30SHARED"),
        ("DE-RuR",2011,2025,"DE-RuR_FATES_SPINUP1000_S30SHARED"),
        ("FI-Hyy",1997,2025,"FI-Hyy_FATES_SPINUP1000_S30SHARED"),
        ("FI-Let",2010,2025,"FI-Let_FATES_SPINUP1000_S30SHARED"),
        ("FR-Pue",2000,2025,"FR-Pue_FATES_SPINUP1000_S30SHARED"),
        ("GF-Guy",2004,2025,"GF-Guy_FATES_SPINUP1000_S30SHARED"),
        ("IT-MBo",2003,2025,"IT-MBo_FATES_SPINUP1000_S30SHARED"),
        ("IT-Tor",2008,2025,"IT-Tor_FATES_SPINUP1000_S30SHARED")],
}
assert sum(len(x) for x in ROWS.values()) == 36
assert len(set(s for entries in ROWS.values() for s, *_ in entries)) == 36

FIGURE_SUFFIXES = (
    "_01_carbon_pools_annual_mean.png",
    "_02_carbon_pools_last250years.png",
    "_04_FATES_PFT_VEGC_evolution.png",
    "_GPP_NEE_monthly_overview.png",
)
DATA_SUFFIXES = (
    "_carbon_annual_means.csv", "_convergence_metrics.csv",
    "_FATES_PFT_VEGC_annual_pct.csv", "_monthly_FATES_vs_EC.csv",
    "_monthly_metrics.csv", "_metadata.json",
)
SITE_SUFFIXES = FIGURE_SUFFIXES + DATA_SUFFIXES
ROOT_FILES = ("batch_convergence_summary.csv", "RUN_INFO.json")


def cmd(*args, cwd=None):
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise RuntimeError(f"{' '.join(map(str,args))}: {p.stderr[-2000:]}")
    return p.stdout.strip()


def modules():
    sha = cmd("git", "-C", str(REPO), "rev-parse", "origin/main")
    def get(rel, name):
        raw = cmd("git", "-C", str(REPO), "show", "origin/main:" + rel)
        mod = types.ModuleType(name)
        mod.__file__ = str(REPO / rel)
        exec(compile(raw, mod.__file__, "exec"), mod.__dict__)
        return mod
    stage = get(SCRIPT6+"27_plot_six_site_latest_archived_convergence_to_RFS.py", "stage27")
    old = get(SCRIPT6+"14_plot_five_site_spinup1000.py", "stage14")
    core = get(SCRIPT6+"10_compare_six_site_latest_complete_cycle.py", "stage10")
    eleven = get(SCRIPT11+"19_plot_nine_site_spinup1000.py", "stage19")
    # Stage 27's pool extraction derives elapsed years from its site dictionary.
    for entries in ROWS.values():
        for site, first, last, _ in entries:
            stage.SITES[site] = (first, last, "UNVERIFIED_IF_MISSING_BIF")
    return sha, stage, old, core, eleven


def discover(batch, site, case, first, stage):
    """Union of Scratch/RFS archived history; never read active run directories."""
    dirs = [
        RFS / "Spinup_Archives" / f"FLUXNET_MultiSite_{batch}" / site / case / "archive/lnd/hist",
        RFS / "Spinup_Archives" / f"FLUXNET_MultiSite_{batch}" / site / case / "lnd/hist",
        RFS / f"FLUXNET_MultiSite_{batch}" / "archives" / site / case / "lnd/hist",
        SCRATCH_ARCH / case / "lnd/hist",
        ALIAS_ARCH / case / "lnd/hist",
    ]
    found, loc = {}, {}
    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in directory.glob(case + ".clm2.h0a.*.nc"):
            match = stage.RE_H0A.search(path.name)
            if match and path.is_file() and path.stat().st_size > 100:
                y = int(match.group(1))
                found[y] = path
                loc[y] = str(directory)
    checkpoint = stage.coordinated_checkpoint(case)
    return found, loc, checkpoint


def horizon(batch, first, found, checkpoint, standard1000):
    if not found:
        raise RuntimeError("No archived annual h0a history found in Scratch or RFS")
    if batch == "6" and not standard1000:
        cap = checkpoint[0] if checkpoint else max(found)+1
    else:
        cap = first + 1000
        if checkpoint and checkpoint[0] < cap:
            raise RuntimeError(f"Restart only at {checkpoint[0]}, below 1000-year target {cap}")
    if cap < first + 1000:
        raise RuntimeError(f"Only {cap-first} years available (<1000)")
    expected = range(first, cap)
    missing = [y for y in expected if y not in found]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} archived annual h0a years "
                           f"within {first}-{cap-1}; first 12: {missing[:12]}")
    return cap, list(expected)


def ec_comparison(site, batch, first, last, model_years, found, old, core, eleven, out,
                  min_halfhour, min_days):
    forcing = SITES_ROOT / site / "forcing"
    if batch in ("11", "13"):
        source = eleven.locate_ec_sources(forcing, "GPP_DT_VUT_REF", None)
        obs, provenance = eleven.merged_ec_daily(core, source, first, last, min_halfhour)
    else:
        try:
            path, gpp = core.find_flux_file(forcing / "raw", "GPP_DT_VUT_REF", None)
            source = [(path, gpp)]
            obs = core.ec_daily(path, gpp, first, last, min_halfhour)
            provenance = [{"path": str(path), "gpp_column": gpp}]
        except FileNotFoundError:
            source = eleven.locate_ec_sources(forcing, "GPP_DT_VUT_REF", None)
            obs, provenance = eleven.merged_ec_daily(core, source, first, last, min_halfhour)
    model = core.fates_daily([(year, found[year]) for year in model_years], first, last)
    daily = model.merge(obs, on="date", how="left", validate="one_to_one")
    if len(daily) != (last-first+1)*365:
        raise RuntimeError("Last model forcing cycle has incomplete daily coverage")
    gpp = core.paired_monthly(daily, "EC_GPP", "FATES_GPP", min_days)
    nee = core.paired_monthly(daily, "EC_NEE", "FATES_NEE", min_days)
    monthly = gpp.merge(nee, on="date", how="outer", validate="one_to_one")
    for flux in ("GPP","NEE"):
        n = (monthly[f"EC_{flux}"].notna() & monthly[f"FATES_{flux}"].notna()).sum()
        if n < 2:
            raise RuntimeError(f"{flux}: only {n} matched monthly pairs")
    monthly.to_csv(out / (site+"_monthly_FATES_vs_EC.csv"), index=False)
    score, plot = old.monthly_overview(monthly, site, model_years, (first,last), out, core)
    score.to_csv(out/(site+"_monthly_metrics.csv"),index=False)
    return score, plot, provenance


def analyze_one(batch, entry, dest, m, args):
    _, stage, old, core, eleven = m
    site, first, last, case = entry
    print(f"\n== {batch} / {site} / {case} ==", flush=True)
    core.verify_stream(CASES / case, first, last)
    found, locations, ckpt = discover(batch, site, case, first, stage)
    cap, years = horizon(batch, first, found, ckpt, args.standard1000)
    print(f"  verified {len(years)} continuous archived h0a: {years[0]}-{years[-1]}; "
          f"restart={ckpt[0] if ckpt else 'NOT_FOUND'}", flush=True)
    if ckpt is None:
        print("  WARNING: no active-Scratch coordinated checkpoint; historical NetCDF "
              "coverage verified but restart usability not verified", flush=True)
    out = dest / site
    out.mkdir(exist_ok=False)
    pft_names, flags, paramfile = stage.get_param_pfts(case)
    igbps = stage.read_bif_igbp(site)
    carbon, pft_rows, variables, units = stage.read_all_carbon_and_pft(
        site, years, {y:found[y] for y in years}, old)
    carbon.to_csv(out/(site+"_carbon_annual_means.csv"),index=False)
    convergence = stage.convergence(carbon, variables, units,
                                    first, last-first+1, cap)
    convergence.to_csv(out/(site+"_convergence_metrics.csv"),index=False)
    stage.plot_carbon(carbon, variables, units, site, out)
    stage.plot_carbon(carbon, variables, units, site, out, tail=250)
    pftplot, pft_summary = stage.plot_pft(pft_rows, pft_names, site, out,
                                          ",".join(igbps) if igbps else "NOT_VERIFIED")
    if pftplot is None:
        raise RuntimeError("No PFT-resolved FATES_VEGC_PF; cannot create standard PFT plot")
    complete = {y:found[y] for y in years}
    _, fullcycle = core.latest_complete_cycle(complete, first, last)
    score, ecplot, ec_prov = ec_comparison(
        site, batch, first, last, fullcycle, complete,
        old, core, eleven, out, args.min_halfhour, args.min_days)
    total_cycles = (cap-first)//(last-first+1)
    meta = {
        "site":site, "batch":batch, "case":case, "status":"OK",
        "mode":"1000_YEAR_STANDARD" if (args.standard1000 or batch!="6") else "LATEST_ARCHIVED",
        "initial_model_year":first, "forcing_years":[first,last],
        "model_history_years":[years[0],years[-1]],
        "archived_history_count":len(years),
        "checkpoint_model_year":ckpt[0] if ckpt else None,
        "checkpoint_path":ckpt[1] if ckpt else None,
        "last_complete_model_forcing_cycle":[fullcycle[0],fullcycle[-1]],
        "completed_forcing_cycles":total_cycles,
        "remaining_partial_years":(cap-first) % (last-first+1),
        "raw_ec_observation_source":ec_prov,
        "GPP_column_preference":"GPP_DT_VUT_REF",
        "EC_NEE":"NEE_VUT_REF", "model_NEE":"-FATES_NEP",
        "model_GPP":"FATES_GPP", "flux_unit":"g C m-2 d-1",
        "monthly_metrics":score.to_dict(orient="records"),
        "IGBP_in_original_BIF":igbps, "dominant_FATES_PFT":pft_summary,
        "PFT_parameter_file":paramfile, "FATES_effective_flags":flags,
        "carbon_units":units,
        "original_git_revision":m[0],
        "limitations":[
            "Numerical 1% trend is a project-specific screen, not an equilibrium certificate",
            "PFT vegetation carbon share is not tower-footprint species area or cover",
            "Tower EC observations may be gap-filled FLUXNET products",
            "NetCDF coverage and checkpoint are separate forms of evidence",
            "Full FATES can have unrealistic vegetation despite a high GPP/NEE skill",
        ],
    }
    (out/(site+"_metadata.json")).write_text(json.dumps(
        meta,indent=2,ensure_ascii=False,default=str)+"\n",encoding="utf-8")
    selected=convergence[convergence.Variable.isin(stage.PRIMARY)]
    print(selected[["Variable","Last100y_trend_pct",
                    "AlignedCycleMeanAbsChange_pct",
                    "Exploratory_1pct_100yr_and_cycle_screen"]].to_string(index=False))
    print("MONTHLY ORIGINAL EC",score[["Flux","N","R2","RMSE","Bias"]].to_string(index=False))
    focus={str(r["Variable"]):r for r in convergence.to_dict("records")}
    anchors=("TOTECOSYSC","TOTSOMC","FATES_VEGC")
    all_low=all(
        focus.get(v,{}).get("Exploratory_1pct_100yr_and_cycle_screen")=="LOW_DRIFT"
        for v in anchors
    )
    trend=lambda v: focus.get(v,{}).get("Last100y_trend_pct",float("nan"))
    fluxrows={r["Flux"]:r for r in score.to_dict("records")}
    return {
        "Batch":batch,"Site":site,"Case":case,"Status":"OK","ElapsedYears":len(years),
        "Checkpoint":ckpt[0] if ckpt else "",
        "LastModelYear":years[-1],"CycleStart":fullcycle[0],"CycleEnd":fullcycle[-1],
        "PFT":(pft_summary or {}).get("dominant_PFT_name", ""),
        "TOTECOSYSC_Last100y_pct":trend("TOTECOSYSC"),
        "TOTSOMC_Last100y_pct":trend("TOTSOMC"),
        "FATES_VEGC_Last100y_pct":trend("FATES_VEGC"),
        "ExploratoryCarbonScreen":"LOW_DRIFT" if all_low else "NOT_LOW_OR_UNDETERMINED",
        "GPP_R2":float(fluxrows["GPP"]["R2"]),
        "GPP_Bias":float(fluxrows["GPP"]["Bias"]),
        "NEE_R2":float(fluxrows["NEE"]["R2"]),
        "NEE_Bias":float(fluxrows["NEE"]["Bias"]),
        "ResultDir":str(out)}


def is_writable_root(root):
    """Probe real write permission; no NFS-only test (IRIDIS mounts vary)."""
    if not root.is_dir() or not os.access(root, os.W_OK):
        return False
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".fluxnet36_write_probe_", dir=str(root), delete=True
        ) as check:
            check.write(b"rfs_preflight")
            check.flush()
        return True
    except (OSError, PermissionError):
        return False


def output_base(requested=None):
    """Prefer RFS on a login node, otherwise stage ONLY derived files in Home."""
    if requested:
        selected = requested.expanduser().resolve()
        approved = {RFS.resolve(), HOME_OUTPUT.resolve()}
        if selected not in approved:
            raise RuntimeError("Output root must be RFS or the dedicated Home staging root; "
                               f"requested {selected}")
        if selected == HOME_OUTPUT.resolve():
            selected.mkdir(parents=True, exist_ok=True)
        if not is_writable_root(selected):
            raise RuntimeError(f"Explicit analysis output root inaccessible: {selected}")
        return selected
    if is_writable_root(RFS):
        print(f"OUTPUT: Research Filestore available at {RFS}", flush=True)
        return RFS
    HOME_OUTPUT.mkdir(parents=True, exist_ok=True)
    if not is_writable_root(HOME_OUTPUT):
        raise RuntimeError("Neither Research Filestore nor dedicated Home staging is writable")
    print(f"WARNING: RFS not mounted/writable on this node: {RFS}", flush=True)
    print(f"STAGING: writing derived figures/CSVs to {HOME_OUTPUT} instead (not Scratch)", flush=True)
    print("STAGING: original archive/EC inputs remain read-only; "
          "use 'sync' later to copy verified results to RFS.", flush=True)
    return HOME_OUTPUT


def batches(which):
    return list(ROWS) if which=="all" else [which]


def batch_run(batch, m, args):
    base = output_base(args.output_base)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix="1000year" if (args.standard1000 or batch!="6") else "latest"
    dest=base / f"FLUXNET_MultiSite_{batch}" / "convergence_snapshots" / (
        f"{stamp}_Batch{batch}_{suffix}_science36")
    if dest.exists():
        raise FileExistsError(dest)
    dest.mkdir(parents=True)
    results=[]
    for entry in ROWS[batch]:
        try:
            results.append(analyze_one(batch,entry,dest,m,args))
        except Exception as e:
            print(f"ERROR {entry[0]}: {type(e).__name__}: {e}",flush=True)
            traceback.print_exc()
            results.append({"Batch":batch,"Site":entry[0],"Case":entry[3],
                            "Status":"FAILED","Problem":str(e)})
    pd.DataFrame(results).to_csv(dest/"batch_convergence_summary.csv",index=False)
    (dest/"RUN_INFO.json").write_text(json.dumps({
        "batch":batch,"created_utc":stamp,
        "pinned_repository_revision":m[0],"results":results,
        "excluded_incomplete_sites":["IT-Noe","CH-Aws"],
        "published":False,
        "warning":"Completion does not prove ecological equilibrium; check each station."
    },ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    ok=sum(r["Status"]=="OK" for r in results)
    print(f"\nBATCH {batch} SUMMARY: {ok}/{len(ROWS[batch])} fully validated; OUTPUT={dest}",flush=True)
    return dest,ok==len(ROWS[batch])


def all_files(snapshot):
    runinfo=json.loads((snapshot/"RUN_INFO.json").read_text(encoding="utf-8"))
    batch=str(runinfo["batch"])
    expected={s for s,*_ in ROWS[batch]}
    rows=list(csv.DictReader((snapshot/"batch_convergence_summary.csv").open(
        newline="",encoding="utf-8")))
    if len(rows)!=len(expected) or {r["Site"] for r in rows}!=expected:
        raise ValueError("Batch membership does not match the 36-site contract")
    if any(r["Status"]!="OK" for r in rows):
        raise RuntimeError("Cannot publish incomplete batch. Resolve failed sites first.")
    files=[snapshot/x for x in ROOT_FILES]
    for site in sorted(expected):
        data=json.loads((snapshot/site/(site+"_metadata.json")).read_text(encoding="utf-8"))
        if data.get("site")!=site or data.get("status")!="OK":
            raise ValueError(f"Bad metadata: {site}")
        if len(data.get("monthly_metrics",[]))!=2:
            raise ValueError(f"Missing GPP/NEE scores: {site}")
        if data.get("archived_history_count",0)<1000:
            raise ValueError(f"Too few spin-up years: {site}")
        if data.get("last_complete_model_forcing_cycle") is None:
            raise ValueError(f"No full forcing cycle: {site}")
        files.extend(snapshot/site/(site+x) for x in SITE_SUFFIXES)
    for path in files:
        if (path.is_symlink() or not path.is_file() or
                not 0<path.stat().st_size<30*1024*1024 or
                path.suffix not in {".png",".csv",".json"}):
            raise ValueError(f"Missing/unsafe publication artifact: {path}")
        if path.suffix==".png" and path.open("rb").read(8)!=b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Invalid PNG: {path}")
    return batch,files


def publication_files(snapshot, allow_partial=False):
    """Precisely validate completed site products; retain failures in manifest."""
    root_items=[snapshot/name for name in ROOT_FILES]
    for file in root_items:
        if file.is_symlink() or not file.is_file():
            raise ValueError(f"Missing/unsafe batch manifest: {file}")
    info=json.loads(root_items[1].read_text(encoding="utf-8"))
    batch=str(info.get("batch"))
    if batch not in ROWS:
        raise ValueError(f"Unknown batch in RUN_INFO.json: {batch}")
    expected={site:case for site,_,_,case in ROWS[batch]}
    with root_items[0].open(newline="",encoding="utf-8") as fin:
        summary=list(csv.DictReader(fin))
    if len(summary)!=len(expected) or {row.get("Site") for row in summary}!=set(expected):
        raise ValueError("Batch summary does not match exact expected stations")
    if len(info.get("results",[]))!=len(expected):
        raise ValueError("RUN_INFO result count does not match batch")
    reported={row.get("Site"):row for row in info["results"]}
    if set(reported)!=set(expected):
        raise ValueError("RUN_INFO site names do not match the batch summary")
    for row in summary:
        site=row["Site"]
        if row.get("Case")!=expected[site]:
            raise ValueError(f"Wrong case recorded for {site}")
        if row.get("Status")!=reported[site].get("Status"):
            raise ValueError(f"Conflicting result status between CSV and JSON for {site}")
    success=sorted(row["Site"] for row in summary if row.get("Status")=="OK")
    failed=sorted((row for row in summary if row.get("Status")!="OK"),
                  key=lambda row:row["Site"])
    if not success:
        raise RuntimeError("No fully analysed stations to publish")
    if failed and not allow_partial:
        raise RuntimeError(
            f"Batch {batch}: {len(success)}/{len(expected)} successful; "
            f"pass --allow-partial to publish just verified stations; "
            f"failed sites: {[r['Site'] for r in failed]}")
    files=list(root_items)
    for site in success:
        folder=snapshot/site
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError(f"Missing completed station directory: {folder}")
        datafile=folder/(site+"_metadata.json")
        if not datafile.is_file() or datafile.is_symlink():
            raise ValueError(f"Missing full station metadata: {site}")
        data=json.loads(datafile.read_text(encoding="utf-8"))
        if (data.get("site")!=site or data.get("batch")!=batch or
                data.get("case")!=expected[site] or data.get("status")!="OK"):
            raise ValueError(f"Station provenance mismatch: {site}")
        if not isinstance(data.get("archived_history_count"),int) or data["archived_history_count"]<1000:
            raise ValueError(f"Archived annual histories insufficient: {site}")
        if not isinstance(data.get("last_complete_model_forcing_cycle"),list) or len(data["last_complete_model_forcing_cycle"])!=2:
            raise ValueError(f"No complete site forcing cycle: {site}")
        scores=data.get("monthly_metrics",[])
        if len(scores)!=2 or {entry.get("Flux") for entry in scores}!={"GPP","NEE"}:
            raise ValueError(f"Incomplete observed EC flux comparison: {site}")
        if any(int(entry.get("N",0))<2 for entry in scores):
            raise ValueError(f"Insufficient matched EC months: {site}")
        files.extend(folder/(site+suffix) for suffix in SITE_SUFFIXES)
    for file in files:
        if (file.is_symlink() or not file.is_file() or
                not 0 < file.stat().st_size < 30*1024*1024 or
                file.suffix not in {".png",".csv",".json"}):
            raise ValueError(f"Missing, oversized or unsafe derived artifact: {file}")
        if file.suffix==".png":
            with file.open("rb") as fin:
                if fin.read(8)!=b"\x89PNG\r\n\x1a\n":
                    raise ValueError(f"Invalid PNG header: {file}")
    status={
        "schema":"fluxnet_crossbatch_publication_v1",
        "batch":batch,
        "analysis_snapshot":snapshot.name,
        "source_dataset":"archived annual h0a and original FLUXNET EC",
        "scope":"PARTIAL_VERIFIED" if failed else "COMPLETE_VERIFIED",
        "expected_count":len(expected),
        "published_success_count":len(success),
        "published_success_sites":success,
        "not_published_count":len(failed),
        "not_published_sites":[
            {"Site":r["Site"],"Status":r.get("Status"),"Problem":r.get("Problem","")}
            for r in failed
        ],
        "other_incomplete_sites_excluded":["IT-Noe","CH-Aws"],
        "note":"Only complete 4-PNG + CSV + JSON per-station products are published. A model reaching 1000 years does not prove convergence."
    }
    print(f"BATCH {batch}: {len(success)}/{len(expected)} fully validated stations",flush=True)
    if failed:
        for row in failed:
            print(f"EXCLUDED from publish: {row['Site']} | {row.get('Problem','unavailable')}",flush=True)
    return batch, files, status


def sha256_of(path):
    digest=hashlib.sha256()
    with path.open("rb") as fin:
        for chunk in iter(lambda:fin.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()


def publish(snapshot, dry_run, allow_partial=False):
    snapshot=snapshot.resolve(strict=True)
    allowed={RFS.resolve(),HOME_OUTPUT.resolve()}
    if snapshot.parent.name!="convergence_snapshots" or snapshot.parent.parent.parent not in allowed:
        raise ValueError("Unexpected source: only batch RFS or Home staging snapshots allowed")
    batch,files,status=publication_files(snapshot,allow_partial=allow_partial)
    target=Path(f"examples/FLUXNET_MultiSite_{batch}/figures/convergence_snapshots")/snapshot.name
    sums="\n".join(
        sha256_of(src)+"  "+src.relative_to(snapshot).as_posix()
        for src in files
    )+"\n"
    print(f"PUBLISH PREFLIGHT PASS: batch {batch}, {len(files)} derived files, {target}",flush=True)
    if dry_run:
        print("DRY RUN: no Git changes",flush=True)
        return
    remote=cmd("git","-C",str(REPO),"remote","get-url","origin")
    if "lyanyeung/CLM-FATES-single-site-workflows" not in remote:
        raise RuntimeError(f"Unexpected GitHub remote: {remote}")
    with tempfile.TemporaryDirectory(prefix=f"science36_b{batch}_",dir=str(Path.home())) as tmp:
        clone=Path(tmp)/"checkout"
        cmd("git","clone","--depth","1","--single-branch","--branch","main",remote,str(clone))
        destdir=clone/target
        if destdir.exists():
            old_manifest=destdir/"SHA256SUMS.txt"
            if old_manifest.is_file() and old_manifest.read_text(encoding="utf-8")==sums:
                print(f"GITHUB ALREADY PUBLISHED AND SHA256 VERIFIED: Batch {batch}; skipping duplicate",flush=True)
                print("GITHUB LOCATION: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/"+str(target))
                return
            raise FileExistsError("GitHub target exists with differing files; refusing to overwrite: "+str(target))
        staged=[]
        for src in files:
            rel=src.relative_to(snapshot)
            dst=destdir/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            if sha256_of(src)!=sha256_of(dst):
                raise RuntimeError(f"Checksum mismatch during preparation: {rel}")
            staged.append(str(target/rel))
        (destdir/"SHA256SUMS.txt").write_text(sums,encoding="utf-8")
        (destdir/"PUBLISH_STATUS.json").write_text(
            json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        staged += [str(target/"SHA256SUMS.txt"),str(target/"PUBLISH_STATUS.json")]
        cmd("git","add","-f","--",*staged,cwd=clone)
        actual=set(cmd("git","diff","--cached","--name-only",cwd=clone).splitlines())
        if actual!=set(staged):
            raise RuntimeError("Unexpected Git staging: "+str(sorted(actual ^ set(staged))))
        kind="PARTIAL" if status["not_published_count"] else "COMPLETE"
        cmd("git","-c","user.name=IRIDIS6 CLM-FATES",
            "-c","user.email=lyanyeung@users.noreply.github.com",
            "commit","-m",f"Publish {kind} Batch{batch} {status['published_success_count']}/{status['expected_count']} carbon/PFT/EC figures",cwd=clone)
        cmd("git","push","origin","HEAD:main",cwd=clone)
        print("GITHUB PUBLISH SUCCESS",batch,
              f"{status['published_success_count']}/{status['expected_count']}",
              kind,cmd("git","rev-parse","HEAD",cwd=clone),flush=True)
        print("GITHUB LOCATION: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/"+str(target),flush=True)


def sync_to_rfs(snapshot, dry_run=False):
    """Copy a successful derived Home snapshot to its matching RFS directory.
    Never copy, delete or modify original CIME/model/observation inputs.
    """
    snapshot = snapshot.resolve(strict=True)
    if snapshot.parent.parent.parent != HOME_OUTPUT.resolve():
        raise ValueError("Sync accepts only the dedicated Home staging snapshots")
    batch, files = all_files(snapshot)
    if not is_writable_root(RFS):
        raise RuntimeError(f"Research Filestore is not currently writable: {RFS}")
    target = RFS / f"FLUXNET_MultiSite_{batch}" / "convergence_snapshots" / snapshot.name
    print(f"SYNC PREFLIGHT PASS: {len(files)} files | Home {snapshot} -> RFS {target}", flush=True)
    if target.exists():
        raise FileExistsError(f"Refusing overwrite of existing RFS snapshot: {target}")
    if dry_run:
        print("SYNC DRY RUN: no copies made", flush=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.parent / (".transferring_" + target.name)
    if temp.exists():
        raise FileExistsError(f"Incomplete transfer already exists: {temp}")
    temp.mkdir()
    try:
        for src in files:
            rel = src.relative_to(snapshot)
            dest = temp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            h1, h2 = hashlib.sha256(), hashlib.sha256()
            for current, digest in [(src,h1),(dest,h2)]:
                with current.open("rb") as fin:
                    for chunk in iter(lambda:fin.read(1024*1024),b""):
                        digest.update(chunk)
            if h1.digest()!=h2.digest():
                raise RuntimeError(f"SHA256 mismatch after RFS copy: {rel}")
        temp.rename(target)
    except Exception:
        print(f"SYNC INCOMPLETE: leave partial files for inspection at {temp}", flush=True)
        raise
    print(f"RFS SYNC SUCCESS: {target}", flush=True)


def audit(batch, m, standard1000):
    _, stage, _, core, _ = m
    bad=0
    for b in batches(batch):
        for site,first,last,case in ROWS[b]:
            try:
                core.verify_stream(CASES/case,first,last)
                found, _, ckpt=discover(b,site,case,first,stage)
                cap,years=horizon(b,first,found,ckpt,standard1000)
                print(f"OK Batch{b:>2} {site:7} | histories {len(years):4} | cap {cap} "
                      f"| checkpoint {ckpt[0] if ckpt else 'not on Scratch'}",flush=True)
            except Exception as e:
                bad+=1
                print(f"BLOCKED Batch{b:>2} {site:7}: {e}",flush=True)
    print("AUDIT COMPLETE, blocked:",bad,flush=True)
    return bad


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",choices=["audit","run","publish","sync"])
    ap.add_argument("--batch",choices=["all","6","8","11","13"],default="all")
    ap.add_argument("--standard1000",action="store_true",
                    help="For six-site cohort, stop at exactly 1000 years for comparability")
    ap.add_argument("--min-halfhour",type=int,default=40)
    ap.add_argument("--min-days",type=int,default=20)
    ap.add_argument("--publish",action="store_true",
                    help="After each fully successful batch, commit derived products to GitHub")
    ap.add_argument("--snapshot",type=Path)
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--allow-partial",action="store_true",
                    help="Opt in to publishing only fully validated sites in an incomplete batch")
    ap.add_argument("--output-base",type=Path,
                    help="Output root (default: prefer RFS; fallback to ~/FLUXNET36_derived)")
    args=ap.parse_args()
    if args.mode in ("publish","sync"):
        if not args.snapshot:
            ap.error(args.mode+" requires --snapshot /actual/derived/snapshot")
        if args.mode=="publish":
            publish(args.snapshot,args.dry_run,args.allow_partial)
        else:
            sync_to_rfs(args.snapshot,args.dry_run)
        return 0
    m=modules()
    if args.mode=="audit":
        return int(audit(args.batch,m,args.standard1000)>0)
    failures=0
    for b in batches(args.batch):
        dest,ok=batch_run(b,m,args)
        if not ok:
            failures+=1
            print(f"BATCH {b} HAS FAILURES: publishing blocked; see {dest}",flush=True)
        elif args.publish:
            try:
                publish(dest,dry_run=False,allow_partial=args.allow_partial)
            except Exception as e:
                failures+=1
                print(f"BATCH {b} PUBLISH FAILED (RFS outputs retained): {e}",flush=True)
                traceback.print_exc()
    return int(failures>0)


if __name__=="__main__":
    raise SystemExit(main())

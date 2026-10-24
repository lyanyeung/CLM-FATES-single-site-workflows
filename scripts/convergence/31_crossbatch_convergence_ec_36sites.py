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
    return {
        "Batch":batch,"Site":site,"Case":case,"Status":"OK","ElapsedYears":len(years),
        "Checkpoint":ckpt[0] if ckpt else "",
        "LastModelYear":years[-1],"CycleStart":fullcycle[0],"CycleEnd":fullcycle[-1],
        "PFT":(pft_summary or {}).get("dominant_PFT_name", ""),
        "GPP_R2":next(float(x["R2"]) for x in score.to_dict("records") if x["Flux"]=="GPP"),
        "NEE_R2":next(float(x["R2"]) for x in score.to_dict("records") if x["Flux"]=="NEE"),
        "ResultDir":str(out)}


def safe_rfs():
    if not RFS.is_dir() or not os.access(RFS, os.W_OK):
        raise RuntimeError(f"Research Filestore not writable: {RFS}")
    mount = cmd("stat","-f","-c","%T",str(RFS))
    if mount.lower() not in ("nfs","nfs4"):
        raise RuntimeError(f"Research Filestore is not NFS ({mount})")


def batches(which):
    return list(ROWS) if which=="all" else [which]


def batch_run(batch, m, args):
    safe_rfs()
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix="1000year" if (args.standard1000 or batch!="6") else "latest"
    dest=RFS / f"FLUXNET_MultiSite_{batch}" / "convergence_snapshots" / (
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
    print(f"\nBATCH {batch} SUMMARY: {ok}/{len(ROWS[batch])} fully validated; RFS={dest}",flush=True)
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


def publish(snapshot, dry_run):
    snapshot=snapshot.resolve(strict=True)
    if snapshot.parent.name!="convergence_snapshots" or snapshot.parent.parent.parent!=RFS:
        raise ValueError("Unexpected source: only batch RFS convergence_snapshots allowed")
    batch,files=all_files(snapshot)
    target=Path(f"examples/FLUXNET_MultiSite_{batch}/figures/convergence_snapshots")/snapshot.name
    print(f"PUBLISH PREFLIGHT PASS: batch {batch}, {len(files)} derived files, {target}",flush=True)
    if dry_run:
        print("DRY RUN: no changes",flush=True)
        return
    remote=cmd("git","-C",str(REPO),"remote","get-url","origin")
    if "lyanyeung/CLM-FATES-single-site-workflows" not in remote:
        raise RuntimeError(f"Unexpected GitHub remote: {remote}")
    with tempfile.TemporaryDirectory(prefix=f"science36_b{batch}_",dir=str(Path.home())) as t:
        clone=Path(t)/"checkout"
        cmd("git","clone","--depth","1","--single-branch","--branch","main",remote,str(clone))
        if (clone/target).exists():
            raise FileExistsError(f"Refusing overwrite: {target}")
        staged=[]
        for file in files:
            rel=file.relative_to(snapshot)
            dest=clone/target/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            import shutil
            shutil.copy2(file,dest)
            staged.append(str(target/rel))
        sums=[]
        for file in files:
            h=hashlib.sha256()
            with file.open("rb") as reader:
                for part in iter(lambda:reader.read(1024*1024),b""):
                    h.update(part)
            sums.append(h.hexdigest()+"  "+file.relative_to(snapshot).as_posix())
        (clone/target/"SHA256SUMS.txt").write_text("\n".join(sums)+"\n")
        staged.append(str(target/"SHA256SUMS.txt"))
        cmd("git","add","-f","--",*staged,cwd=clone)
        actual=set(cmd("git","diff","--cached","--name-only",cwd=clone).splitlines())
        if actual!=set(staged):
            raise RuntimeError("Wrong staged files: "+str(sorted(actual ^ set(staged))))
        cmd("git","-c","user.name=IRIDIS6 CLM-FATES",
            "-c","user.email=lyanyeung@users.noreply.github.com",
            "commit","-m",f"Publish full Batch{batch} carbon/PFT/EC checkpoint comparison",cwd=clone)
        cmd("git","push","origin","HEAD:main",cwd=clone)
        print("GITHUB PUBLISH SUCCESS",batch,cmd("git","rev-parse","HEAD",cwd=clone))
        print("GITHUB LOCATION: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/"+str(target))


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
    ap.add_argument("mode",choices=["audit","run","publish"])
    ap.add_argument("--batch",choices=["all","6","8","11","13"],default="all")
    ap.add_argument("--standard1000",action="store_true",
                    help="For six-site cohort, stop at exactly 1000 years for comparability")
    ap.add_argument("--min-halfhour",type=int,default=40)
    ap.add_argument("--min-days",type=int,default=20)
    ap.add_argument("--publish",action="store_true",
                    help="After each fully successful batch, commit derived products to GitHub")
    ap.add_argument("--snapshot",type=Path)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    if args.mode=="publish":
        if not args.snapshot:
            ap.error("publish requires --snapshot /actual/RFS/snapshot")
        publish(args.snapshot,args.dry_run)
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
                publish(dest,dry_run=False)
            except Exception as e:
                failures+=1
                print(f"BATCH {b} PUBLISH FAILED (RFS outputs retained): {e}",flush=True)
                traceback.print_exc()
    return int(failures>0)


if __name__=="__main__":
    raise SystemExit(main())

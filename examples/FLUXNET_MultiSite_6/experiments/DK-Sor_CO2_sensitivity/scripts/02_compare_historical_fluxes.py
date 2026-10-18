#!/usr/bin/env python3
"""READ ONLY: compare DK-Sor historical fixed vs NOAA dynamic CO2 against EC.
Only COMPLETE and common archived historical years are used. Never edits a CIME
case or restart. Outputs are written to a separate local diagnostics directory.
Usage: python 02_compare_historical_fluxes.py --min-years 1
       python 02_compare_historical_fluxes.py --min-years 29
Requires numpy, pandas, matplotlib, netCDF4 in clm_fates_env.
"""
import argparse
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive")
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/DK-Sor")
FIXED="DK-Sor_FATES_HIST1996_2024_TEST"
DYNAMIC="DK-Sor_FATES_HIST1996_2024_NOAA_CO2"
REF=Path(__file__).resolve().parents[3]/"scripts/10_compare_six_site_latest_complete_cycle.py"
# parents[0]=scripts, parents[1]=experiment, parents[2]=experiments, parents[3]=FLUXNET_MultiSite_6

def load_ref():
    if not REF.is_file():
        raise RuntimeError("Reference comparison script missing: "+str(REF))
    spec=importlib.util.spec_from_file_location("reference_flux",str(REF))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def index(mod,name):
    # Historic years are actual model calendar years, NOT cyclic spinup years.
    found=mod.history_index(BASE,name)
    return {y:p for y,p in found.items() if 1996<=y<=2024}

def monthly_from_files(mod,found,years):
    x=mod.fates_daily([(y,found[y]) for y in years],1996,2024)
    x["month"]=x["date"].dt.to_period("M").dt.to_timestamp()
    return x.groupby("month",as_index=False)[["FATES_GPP","FATES_NEE"]].mean().rename(columns={"month":"date"})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--min-years",type=int,default=1,help="Require at least this many complete common annual h0a files (1-29)")
    ap.add_argument("--out",type=Path,default=ROOT/"validation"/"historical_fixed_vs_NOAA")
    args=ap.parse_args()
    if not 1<=args.min_years<=29: ap.error("--min-years must be 1..29")
    mod=load_ref()
    fixed=index(mod,FIXED);dynamic=index(mod,DYNAMIC)
    years=sorted(set(fixed)&set(dynamic))
    print("Fixed historical years:",sorted(fixed))
    print("NOAA historical years:",sorted(dynamic))
    print("Common years:",years)
    if len(years)<args.min_years:
        raise SystemExit("STOP: not enough archived matching historical years; wait for jobs, or run with --min-years 1 for interim.")
    # To prevent confusing coverage gaps with a continuous historical run.
    if years!=list(range(1996,1996+len(years))):
        raise SystemExit("STOP: missing interior years / not contiguous from 1996.")
    a=monthly_from_files(mod,fixed,years).rename(columns={"FATES_GPP":"Fixed_GPP","FATES_NEE":"Fixed_NEE"})
    b=monthly_from_files(mod,dynamic,years).rename(columns={"FATES_GPP":"NOAA_GPP","FATES_NEE":"NOAA_NEE"})
    m=a.merge(b,on="date",validate="one_to_one")
    obs_path,gpp_col=mod.find_flux_file(ROOT/"forcing"/"raw","GPP_DT_VUT_REF")
    obs=mod.ec_daily(obs_path,gpp_col,1996,2024,24)
    obs["date"]=obs["date"].dt.to_period("M").dt.to_timestamp()
    obs=obs.groupby("date",as_index=False)[["EC_GPP","EC_NEE"]].mean()
    m=m.merge(obs,on="date",how="left",validate="one_to_one")
    if len(m)!=len(years)*12: raise SystemExit("STOP: incomplete months in annual histories")
    args.out.mkdir(parents=True,exist_ok=True)
    m.to_csv(args.out/"monthly_comparison_LOCAL_ONLY.csv",index=False)
    rows=[]
    for flux in ("GPP","NEE"):
        for variant in ("Fixed","NOAA"):
            obscol="EC_"+flux;modcol=variant+"_"+flux
            row=mod.metrics(m[obscol],m[modcol])
            rows.append({"flux":flux,"experiment":variant,**row})
        fig,ax=plt.subplots(figsize=(13,4.5))
        for key,lab in [( "EC_","EC observation"),("Fixed_","Fixed 361.93 ppm"),("NOAA_","NOAA historical CO2")]:
            ax.plot(m["date"],m[key+flux],label=lab,linewidth=1.5)
        if flux=="NEE":ax.axhline(0,color="gray",linewidth=.7)
        ax.set_ylabel(flux+" (g C m$^{-2}$ d$^{-1}$)")
        ax.set_xlabel("Historical year")
        ax.legend();ax.grid(alpha=.2)
        fig.suptitle(f"DK-Sor {flux}, common 1996-{years[-1]}; interim" if len(years)<29 else f"DK-Sor {flux}, 1996-2024")
        fig.tight_layout()
        fig.savefig(args.out/f"DK-Sor_{flux}_Fixed_vs_NOAA.png",dpi=200);plt.close(fig)
    pd.DataFrame(rows).to_csv(args.out/"skill_metrics.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print("Output:",args.out)
    print("CAVEAT: EC monthly means use daily input means. Validate coverage, CO2 ingestion and restart shock before scientific conclusions.")
    print("DO NOT publish monthly_comparison_LOCAL_ONLY.csv containing EC time series without checking ICOS data terms.")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""FATES_VEGC multi-window stability using FULL meteorological forcing cycles.

15 sites = ICOS FLUXNET_MultiSite_6 (6) + MultiSite_11 (9 completed).
Read-only inputs: verified, previously derived annual VegC CSVs on Research Filestore.
Output: a new RFS snapshot containing 30 site figures, 2 overview figures,
       per-site full-cycle statistics, a 15-site summary, source provenance.

For target windows 100/200/300 years, use ceil(W / forcing_cycle_years)
FULL forcing cycles, ending at floor(archived_years / L)*L.
Fit a linear trend to the *mean VegC of each cycle* at its model-year midpoint.
Normalize every slope to % per 100 model years, for cross-site comparisons.
Three disjoint last ceil(100/L)-cycle blocks diagnose phase changes.
Last four phase-matched adjacent cycle pairs reveal signed drift and variability.

Important: This is a study-specific diagnostic, NOT an official FATES equilibrium
test. It does not test GPP, NEE, PFT realism or carbon closure.
Run on IRIDIS6 login node with Research Filestore mounted.
Requires adjacent 01_analyze_15site_vegc.py (validated original source reader).

  python 02_phase_aligned_15site_vegc.py --preflight
  python 02_phase_aligned_15site_vegc.py
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASEFILE = HERE / "01_analyze_15site_vegc.py"
spec = importlib.util.spec_from_file_location("existing_15site_vegc_reader", str(BASEFILE))
if spec is None or spec.loader is None:
    raise RuntimeError("Missing original 15-site script beside this one: " + str(BASEFILE))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

SITES = list(base.SIX) + list(base.NINE)
WINDOWS = (300, 200, 100)
OUTPUT_PARENT = base.OUTPUT_PARENT / "phase_aligned"
FIG_LABELS = {"300":"Long","200":"Medium","100":"Recent"}

def log(*a):
    print(*a, flush=True)

def nfs_guard():
    rfs = base.RFS
    if not rfs.is_dir() or not os.access(rfs, os.W_OK):
        raise RuntimeError("RFS is not mounted and writable: " + str(rfs))
    p = subprocess.run(["stat","-f","-c","%T",str(rfs)],
                       text=True,capture_output=True,check=True)
    if p.stdout.strip().lower() not in ("nfs","nfs4"):
        raise RuntimeError("Research Filestore is not NFS: " + p.stdout.strip())

def fit_period_means(cycle_means, L):
    y = np.asarray(cycle_means, dtype=float)
    if len(y) < 4 or not np.isfinite(y).all():
        raise ValueError("Need >=4 finite, complete cycle means for stable diagnostic")
    # x and slope measured in elapsed model years, not cycle index.
    t = np.arange(len(y),dtype=float) * L + (L + 1) / 2
    b = float(np.polyfit(t,y,1)[0])
    mu = float(np.mean(y))
    pct100 = 10000.0*b/abs(mu) if abs(mu)>1e-9 else float("nan")
    return b,pct100,mu

def cycle_statistics(entry):
    v = entry["v"]
    n,L = entry["n"],entry["L"]
    K = n // L
    if K < 20:
        raise ValueError(f"{entry['site']}: fewer than 20 full forcing cycles")
    cap = K*L
    cv = v[:cap].reshape(K,L)
    means = cv.mean(axis=1)
    row = {"Site":entry["site"],"Batch":"FLUXNET_MultiSite_"+entry["batch"],
           "ElapsedYears":n,"ForcingCycleYears":L,
           "CompleteForcingCycles":K,"LastCompleteElapsedYear":cap,
           "ExcludedPartialTailYears":n-cap}
    for W in WINDOWS:
        k=math.ceil(W/L)
        if k> K:
            raise ValueError(f"{entry['site']}: insufficient complete cycles for {W}y")
        start=(K-k)*L+1
        stop=cap
        b,pct,mu=fit_period_means(means[-k:],L)
        pre=f"W{W}"
        row[pre+"_FullCycles"]=k
        row[pre+"_ActualYears"]=k*L
        row[pre+"_StartElapsedYear"]=start
        row[pre+"_EndElapsedYear"]=stop
        row[pre+"_VegCmean_kgCm2"]=mu
        row[pre+"_Slope_gCm2_per_yr"]=1000*b
        row[pre+"_Trend_pct_per_100yr"]=pct
    k100=math.ceil(100/L)
    if 3*k100>K:
        raise ValueError(f"{entry['site']}: insufficient cycles for three independent blocks")
    for i in range(3):
        firstcycle=K-3*k100+i*k100
        y=means[firstcycle:firstcycle+k100]
        b,pct,mu=fit_period_means(y,L)
        pre=f"B{i+1}"
        row[pre+"_StartElapsedYear"]=firstcycle*L+1
        row[pre+"_EndElapsedYear"]=(firstcycle+k100)*L
        row[pre+"_ActualYears"]=k100*L
        row[pre+"_VegCmean_kgCm2"]=mu
        row[pre+"_Slope_gCm2_per_yr"]=1000*b
        row[pre+"_Trend_pct_per_100yr"]=pct
    adjacent=[]
    for prevcycle in range(K-4,K):
        prev=cv[prevcycle-1]
        curr=cv[prevcycle]
        den=float(np.mean(np.abs(prev)))
        if den<=1e-9:
            raise ValueError(f"{entry['site']}: zero VegC reference cycle")
        delta=curr-prev
        signed=float(np.mean(delta))
        absdiff=float(np.mean(np.abs(delta)))
        adjacent.append({
          "Site":entry["site"],"PreviousCycle":prevcycle,
          "CurrentCycle":prevcycle+1,"CycleYears":L,
          "PreviousElapsedStart":(prevcycle-1)*L+1,
          "CurrentElapsedStart":prevcycle*L+1,
          "SignedMeanChange_kgCm2":signed,
          "SignedMeanChange_pct":100*signed/den,
          "SignedDrift_pct_per100yr":10000*signed/(den*L),
          "PhaseMatchedMeanAbsoluteDiff_pct":100*absdiff/den,
          "MeanAbsoluteDiff_kgCm2":absdiff,
        })
    cp=pd.DataFrame(adjacent)
    row["LatestCycleMeanAbsDiff_pct"]=float(cp.PhaseMatchedMeanAbsoluteDiff_pct.iloc[-1])
    row["Max4CycleMeanAbsDiff_pct"]=float(cp.PhaseMatchedMeanAbsoluteDiff_pct.max())
    row["LatestCycleSignedDrift_pct_per100yr"]=float(cp.SignedDrift_pct_per100yr.iloc[-1])
    row["Last4CycleSignedDrift_Mean_pct_per100yr"]=float(cp.SignedDrift_pct_per100yr.mean())
    row["Last4CycleSignedDrift_MaxAbs_pct_per100yr"]=float(cp.SignedDrift_pct_per100yr.abs().max())
    for threshold in (1,2):
        slopes=np.array([row[f"W{W}_Trend_pct_per_100yr"] for W in WINDOWS])
        abs_cycle=cp.PhaseMatchedMeanAbsoluteDiff_pct.to_numpy()
        row[f"ExploratoryNestedTrendsAnd4CycleAbsUnder{threshold}pct"]=bool(
            np.isfinite(slopes).all() and (np.abs(slopes)<threshold).all()
            and np.isfinite(abs_cycle).all() and (abs_cycle<threshold).all())
    return row,cp,means

def plot_station(entry,row,pairs,means,out):
    site,n,L,K=entry["site"],entry["n"],entry["L"],len(means)
    cap=K*L
    oldstart=row["W300_StartElapsedYear"]
    xx=np.arange(oldstart,cap+1)
    v=entry["v"][oldstart-1:cap]
    cycle_num=np.arange(K)
    center=cycle_num*L+(L+1)/2
    cmap={300:"#31688e",200:"#238b45",100:"#c35d12"}
    fig,ax=plt.subplots(figsize=(12.5,5.9))
    ax.plot(xx,v,color="0.6",lw=.9,alpha=.7,label="Annual FATES VegC")
    ax.plot(center[-math.ceil(300/L):],means[-math.ceil(300/L):],
            color="0.25",marker="o",markersize=3,lw=1,label="Full forcing-cycle means")
    for W in WINDOWS:
        k=row[f"W{W}_FullCycles"]
        x=center[-k:]
        y=means[-k:]
        slope,intercept=np.polyfit(x,y,1)
        ax.plot(x,slope*x+intercept,lw=2.2,color=cmap[W],
                label=f"≥{W}yr / {k} cycles: {row[f'W{W}_Trend_pct_per_100yr']:+.2f}% / century")
    ax.set_title(f"{site}: full-cycle aligned FATES VegC trends (ends at year {cap}; tail excluded {n-cap})")
    ax.set_xlabel("Elapsed model spin-up year")
    ax.set_ylabel("FATES_VEGC (kg C m$^{-2}$)")
    ax.grid(alpha=.22)
    ax.legend(frameon=False,fontsize=9)
    fig.tight_layout()
    fig.savefig(out/(site+"_01_fullcycle_nested_VegC_trends.png"),dpi=200)
    plt.close(fig)

    fig,axes=plt.subplots(3,1,figsize=(12.5,11.4),
                           gridspec_kw={"height_ratios":[3,1.5,1.5]})
    colors=("#31688e","#238b45","#c35d12")
    k100=math.ceil(100/L)
    for i in range(3):
        ids=np.arange(K-3*k100+i*k100,K-2*k100+i*k100)
        x=center[ids]; y=means[ids]
        slope,intercept=np.polyfit(x,y,1)
        axes[0].plot(x,y,marker="o",markersize=3,lw=.85,color=colors[i],alpha=.60)
        axes[0].plot(x,slope*x+intercept,lw=2.1,color=colors[i],
           label=f"Block {i+1}, years {row[f'B{i+1}_StartElapsedYear']}-{row[f'B{i+1}_EndElapsedYear']}: "
                 f"{row[f'B{i+1}_Trend_pct_per_100yr']:+.2f}%/century")
    axes[0].set_title("Three independent, equal-length FULL-cycle blocks (~100 years each)")
    axes[0].set_xlabel("Elapsed model spin-up year")
    axes[0].set_ylabel("Mean VegC (kg C m$^{-2}$)")
    axes[0].grid(alpha=.22)
    axes[0].legend(frameon=False,fontsize=8.5)
    bx=np.arange(len(pairs))
    pair_labels=[f"{int(a)}→{int(b)}" for a,b in zip(pairs.PreviousCycle,pairs.CurrentCycle)]
    axes[1].bar(bx,pairs.SignedDrift_pct_per100yr,width=.65,color="#31688e")
    axes[1].axhline(0,color="0.3",lw=.8)
    axes[1].set_xticks(bx,pair_labels)
    axes[1].set_title("Signed VegC drift, annualized across each forcing-cycle pair")
    axes[1].set_ylabel("% per 100 years")
    axes[1].grid(axis="y",alpha=.22)
    axes[2].bar(bx,pairs.PhaseMatchedMeanAbsoluteDiff_pct,width=.65,color="#c35d12")
    axes[2].axhline(1,color="0.3",lw=1,ls="--",label="1% exploratory")
    axes[2].axhline(2,color="0.3",lw=1,ls=":",label="2% exploratory")
    axes[2].set_xticks(bx,pair_labels)
    axes[2].set_title("Phase-matched mean ABSOLUTE VegC difference")
    axes[2].set_ylabel("% of previous cycle")
    axes[2].legend(frameon=False,fontsize=8)
    axes[2].grid(axis="y",alpha=.22)
    fig.tight_layout()
    fig.savefig(out/(site+"_02_independent_blocks_and_cycle_drift.png"),dpi=200)
    plt.close(fig)

def plot_overview(df,out):
    cols=[f"W{W}_Trend_pct_per_100yr" for W in WINDOWS]+[f"B{j}_Trend_pct_per_100yr" for j in (1,2,3)]
    mat=df[cols].to_numpy(dtype=float)
    fig,ax=plt.subplots(figsize=(11.5,9))
    ax.imshow(mat,cmap="coolwarm",vmin=-10,vmax=10,aspect="auto")
    ax.set_xticks(range(6),["~300 yr","~200 yr","~100 yr","Block 1","Block 2","Block 3"])
    ax.set_yticks(range(len(df)),df.Site)
    for i in range(len(df)):
        for j in range(6):
            val=mat[i,j]
            ax.text(j,i,f"{val:+.2f}",va="center",ha="center",fontsize=9,
                    color="white" if abs(val)>6 else "black")
    ax.set_title("15-site phase-aligned FATES VegC trends (% per 100 years)\n"
                 "Exact numbers shown; colors capped at ±10%")
    fig.tight_layout()
    fig.savefig(out/"all15_01_full_cycle_trend_heatmap.png",dpi=185)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(12.1,6.1))
    ids=np.arange(len(df))
    ax.bar(ids-.2,df.LatestCycleMeanAbsDiff_pct,width=.4,label="Latest adjacent cycles")
    ax.bar(ids+.2,df.Max4CycleMeanAbsDiff_pct,width=.4,label="Maximum of last four")
    ax.axhline(1,color="0.3",ls="--",lw=1,label="1% exploratory")
    ax.axhline(2,color="0.3",ls=":",lw=1.1,label="2% exploratory")
    ax.set_xticks(ids,df.Site,rotation=30,ha="right")
    ax.set_yscale("symlog",linthresh=1)
    ax.set_ylabel("Phase-matched mean absolute VegC difference (%)")
    ax.legend(frameon=False)
    ax.set_title("Last four forcing-cycle differences: no single-pair shortcut")
    ax.grid(axis="y",alpha=.20)
    fig.tight_layout()
    fig.savefig(out/"all15_02_last4_cycle_difference.png",dpi=185)
    plt.close(fig)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preflight",action="store_true")
    p.add_argument("--six-snapshot",type=Path,default=base.SIX_ROOT)
    p.add_argument("--eleven-root",type=Path,default=base.NINE_ROOT)
    args=p.parse_args()
    inputs=[base.read_site(s,"6",args.six_snapshot) for s in base.SIX]
    inputs.extend(base.read_site(s,"11",args.eleven_root) for s in base.NINE)
    if len(inputs)!=15 or [x["site"] for x in inputs]!=SITES:
        raise AssertionError("Did not validate exactly 15 ordered sites")
    for x in inputs:
        cap=x["n"]//x["L"]*x["L"]
        log(f"VERIFIED {x['site']}: elapsed={x['n']}; forcing_cycle={x['L']}; "
            f"full_cycles={cap//x['L']}; analysis_end={cap}; partial_tail={x['n']-cap}")
        # Compute before write, so --preflight also verifies the mathematics.
        cycle_statistics(x)
    if args.preflight:
        log("PREFLIGHT PASS: 15 sites; no files written")
        return
    nfs_guard()
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out=OUTPUT_PARENT/(stamp+"_15site_FullCycle_VegC")
    if out.exists():
        raise FileExistsError("Output snapshot already exists: "+str(out))
    out.mkdir(parents=True)
    summary=[]
    provenance=[]
    for x in inputs:
        row,pairs,means=cycle_statistics(x)
        here=out/x["site"];here.mkdir()
        pd.DataFrame([row]).to_csv(here/(x["site"]+"_phase_aligned_metrics.csv"),index=False)
        pairs.to_csv(here/(x["site"]+"_last4_aligned_cycle_pairs.csv"),index=False)
        plot_station(x,row,pairs,means,here)
        summary.append(row)
        provenance.append({k:v for k,v in x.items() if k!="v"})
        log(f"RESULT {x['site']:7} | complete yrs={row['LastCompleteElapsedYear']:4d} | "
            f"300/200/100: {row['W300_Trend_pct_per_100yr']:+7.2f} "
            f"{row['W200_Trend_pct_per_100yr']:+7.2f} "
            f"{row['W100_Trend_pct_per_100yr']:+7.2f} (%/century); "
            f"last4 MAE max={row['Max4CycleMeanAbsDiff_pct']:.2f}%")
    df=pd.DataFrame(summary)
    df.to_csv(out/"all15_fullcycle_vegc_summary.csv",index=False)
    plot_overview(df,out)
    (out/"PROVENANCE_AND_METHODS.json").write_text(json.dumps({
       "created_utc":stamp,"source_files":provenance,
       "method":"Aligned to whole forcing cycles starting at elapsed year 1. "
                "Drop incomplete tail. Build >=100/200/300yr windows by ceil(target/L) "
                "full cycles, fit OLS to each cycle mean at its cycle-midpoint elapsed year. "
                "Also use 3 non-overlapping equal-size ~100yr complete-cycle blocks.",
       "metrics":"All window slopes: normalized percent per 100 years. "
                 "Four adjacent cycle pairs: signed drift in percent per 100yr and "
                 "phase-matched mean absolute difference as percent of previous cycle.",
       "thresholds":"1% and 2% screens are exploratory study choices, not official CTSM rules.",
       "limitations":"Not evidence of GPP/NEE convergence, correct PFT, or soil carbon equilibrium. "
                     "Latest ~100yr windows often include only 4 cycle means; trend has uncertainty. "
                     "Cycle means can hide within-cycle disturbances."
    },indent=2,ensure_ascii=False)+"\n")
    show=["Site","ElapsedYears","LastCompleteElapsedYear",
          "W300_ActualYears","W300_Trend_pct_per_100yr",
          "W200_ActualYears","W200_Trend_pct_per_100yr",
          "W100_ActualYears","W100_Trend_pct_per_100yr",
          "LatestCycleMeanAbsDiff_pct","Max4CycleMeanAbsDiff_pct",
          "ExploratoryNestedTrendsAnd4CycleAbsUnder1pct",
          "ExploratoryNestedTrendsAnd4CycleAbsUnder2pct"]
    log("\nFINAL 15-SITE PHASE-ALIGNED VEGC RESULTS\n"+df[show].to_string(index=False))
    log("SAVED TO RESEARCH FILESTORE:",out)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Read-only FATES vegetation-carbon stability test for six + nine ICOS sites.

Reads only derived annual FATES_VEGC CSVs already on Research Filestore.
Saves NEW figures, paired-cycle statistics, metadata and 15-site summaries on
Research Filestore. No CIME/Slurm/restart/forcing/NetCDF modifications.
Python 3.9+; numpy, pandas, matplotlib. Run on an IRIDIS6 login node.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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

RFS = Path("/research/xclimatetbm/ly3n24")
SIX_ROOT = RFS / "CLM_FATES/FLUXNET_MultiSite_6/convergence_snapshots/20261021T222202Z_archive_snapshot"
NINE_ROOT = RFS / "CLM_FATES/FLUXNET_MultiSite_11/spinup1000_final"
OUTPUT_PARENT = RFS / "CLM_FATES/Spinup_Analysis/vegc_convergence_15site"
SIX = ("DE-Hai", "RU-Fyo", "DE-Tha", "DK-Sor", "NL-Loo", "IL-Yat")
NINE = ("AT-Neu", "BE-Bra", "CH-Cha", "CH-Fru", "CH-Lae", "CZ-Stn", "FI-Sod", "FR-Fon", "GL-ZaH")


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_site(site, batch, root):
    file = root / site / (site + "_carbon_annual_means.csv")
    metadata_file = root / site / (site + "_metadata.json")
    if not file.is_file() or not metadata_file.is_file():
        raise FileNotFoundError("Missing archived analysis input: " + str(file))
    if file.is_symlink() or metadata_file.is_symlink():
        raise RuntimeError("Refusing symlink input for " + site)
    metadata = json.loads(metadata_file.read_text())
    if metadata.get("site") != site:
        raise ValueError("Metadata/site mismatch: " + site)
    units = metadata.get("carbon_units", {}).get("FATES_VEGC", {})
    if "kg" not in str(units.get("original_units", units.get("input", ""))).lower():
        raise ValueError("FATES_VEGC unit is not verified as kg C m-2 for " + site)
    yr = metadata.get("forcing_years") if batch == "6" else metadata.get("forcing_first_last")
    if not isinstance(yr, list) or len(yr) != 2:
        raise ValueError("Missing forcing-cycle years: " + site)
    length = int(yr[1]) - int(yr[0]) + 1
    if not (5 <= length <= 50):
        raise ValueError("Implausible forcing length for " + site)
    df = pd.read_csv(file, usecols=["Site", "ModelYear", "SpinupYear", "FATES_VEGC"])
    df = df.sort_values("SpinupYear").reset_index(drop=True)
    n = len(df)
    if n < 300 or (batch == "11" and n != 1000):
        raise ValueError(f"{site}: unexpected number of complete annual records ({n})")
    if not (df["Site"] == site).all():
        raise ValueError("Mixed site ID: " + site)
    if not np.array_equal(df.SpinupYear.to_numpy(), np.arange(1, n+1)):
        raise ValueError("Spin-up years not consecutive from 1: " + site)
    if not np.array_equal(df.ModelYear.to_numpy(), int(yr[0]) + np.arange(n)):
        raise ValueError("Model chronology does not match forcing start: " + site)
    v = df.FATES_VEGC.to_numpy(dtype=float)
    if not np.isfinite(v).all() or min(v) < -1e-7:
        raise ValueError("VegC invalid/negative: " + site)
    return {"site": site, "batch": batch, "n": n, "L": length, "v": v,
            "source": str(file), "sha256": checksum(file),
            "metadata": str(metadata_file), "metadata_sha256": checksum(metadata_file)}


def slope(v):
    """Return kg C/m2/year slope and normalized percentage *per 100 years*."""
    n = len(v)
    b = float(np.polyfit(np.arange(n), v, 1)[0])
    avg = float(np.mean(v))
    return b, (10000.0 * b / abs(avg)) if abs(avg) >= 1e-9 else float("nan")


def calculate(x):
    site, v, n, L = x["site"], x["v"], x["n"], x["L"]
    row = {"Site": site, "Batch": "FLUXNET_MultiSite_"+x["batch"],
           "ArchivedYears": n, "ForcingCycleYears": L}
    for w in (300, 200, 100):
        b, pct = slope(v[-w:])
        row[f"Last{w}y_slope_gCm2yr"] = 1000*b
        row[f"Last{w}y_pct_per100y"] = pct
    for k in range(3):
        start = n-300+k*100
        b, pct = slope(v[start:start+100])
        row[f"Block{k+1}_start"] = start+1
        row[f"Block{k+1}_end"] = start+100
        row[f"Block{k+1}_slope_gCm2yr"] = 1000*b
        row[f"Block{k+1}_pct_per100y"] = pct
    K = n // L
    if K < 5:
        raise ValueError(site+": at least five aligned forcing cycles needed")
    cycles = []
    for prev_num in range(K-4, K):
        previous = v[(prev_num-1)*L:prev_num*L]
        current = v[prev_num*L:(prev_num+1)*L]
        denominator = float(np.mean(np.abs(previous)))
        abs_diff = float(np.mean(np.abs(current-previous)))
        signed_diff = float(np.mean(current-previous))
        cycles.append({"Site": site, "PreviousCycle": prev_num, "CurrentCycle": prev_num+1,
                       "PrevStart": (prev_num-1)*L+1, "PrevEnd": prev_num*L,
                       "CurrentStart": prev_num*L+1, "CurrentEnd": (prev_num+1)*L,
                       "MeanAbsoluteDifference_pct": 100*abs_diff/denominator if denominator > 1e-9 else np.nan,
                       "SignedMeanDifference_pct": 100*signed_diff/denominator if denominator > 1e-9 else np.nan,
                       "EndpointDrift_gCm2yr": 1000*(current[-1]-previous[-1])/L})
    cycle_df = pd.DataFrame(cycles)
    row["LastCycleAbsDifference_pct"] = cycle_df.MeanAbsoluteDifference_pct.iloc[-1]
    row["Max4CycleAbsDifference_pct"] = cycle_df.MeanAbsoluteDifference_pct.max()
    for cut in (1, 2):
        trends = [row[f"Last{w}y_pct_per100y"] for w in (300,200,100)]
        cycle_diffs = cycle_df.MeanAbsoluteDifference_pct.to_numpy()
        row[f"ExploratoryAllWindowsAnd4CyclesUnder{cut}pct"] = bool(
            np.isfinite(trends).all() and np.all(np.abs(trends) < cut)
            and np.isfinite(cycle_diffs).all() and np.all(cycle_diffs < cut))
    return row, cycle_df


def plot_one(x, row, cycles, output):
    site, n, v = x["site"], x["n"], x["v"]
    xx = np.arange(n-299, n+1)
    cols = {300:"#31688e", 200:"#238b45", 100:"#c35d12"}
    fig, ax = plt.subplots(figsize=(12.3,5.6))
    ax.plot(xx, v[-300:], color="0.25", alpha=.78, lw=1.1, label="Annual vegetation carbon")
    for w in (300,200,100):
        xxw = np.arange(n-w+1,n+1)
        bb, aa = np.polyfit(xxw,v[-w:],1)
        p = row[f"Last{w}y_pct_per100y"]
        ax.plot(xxw,bb*xxw+aa,lw=2.2,color=cols[w],label=f"Last {w} years: {p:+.2f}% per 100 yr")
    ax.set_title(f"{site}: final 300 years of {n} archived spin-up years")
    ax.set_xlabel("Elapsed spin-up year")
    ax.set_ylabel("FATES_VEGC (kg C m$^{-2}$)")
    ax.legend(frameon=False)
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(output/(site+"_01_nested_300_200_100_VegC.png"),dpi=190)
    plt.close(fig)

    fig, (ax1,ax2) = plt.subplots(2,1,figsize=(12.3,8.4),gridspec_kw={"height_ratios":[3,2]})
    ax1.plot(xx,v[-300:],color="0.55",lw=0.85)
    for k,color in enumerate(("#31688e","#238b45","#c35d12")):
        a=n-300+k*100
        years=np.arange(a+1,a+101)
        y=v[a:a+100]
        bb,cc=np.polyfit(years,y,1)
        ax1.plot(years,bb*years+cc,color=color,lw=2.2,
                 label=f"Years {a+1}-{a+100}: {row[f'Block{k+1}_pct_per100y']:+.2f}%/100yr")
    ax1.set_title("Three non-overlapping 100-year trends")
    ax1.set_xlabel("Elapsed spin-up year")
    ax1.set_ylabel("FATES_VEGC (kg C m$^{-2}$)")
    ax1.legend(frameon=False,fontsize=9)
    ax1.grid(alpha=.22)
    labels=[f"{int(r.PreviousCycle)}→{int(r.CurrentCycle)}" for r in cycles.itertuples()]
    ax2.bar(labels,cycles.MeanAbsoluteDifference_pct,color="#648aa4")
    ax2.axhline(1,ls="--",color="#238b45",label="1% exploratory screen")
    ax2.axhline(2,ls=":",color="#b47727",label="2% exploratory screen")
    ax2.set_title(f"Four adjacent phase-matched forcing-cycle pairs ({x['L']} yr per cycle)")
    ax2.set_ylabel("Mean absolute VegC difference (%)")
    ax2.legend(frameon=False,fontsize=9)
    ax2.grid(axis="y",alpha=.22)
    fig.tight_layout()
    fig.savefig(output/(site+"_02_disjoint100_and_last4_cycles.png"),dpi=190)
    plt.close(fig)


def plot_summary(summary, output):
    fields=[f"Last{w}y_pct_per100y" for w in (300,200,100)]
    fields.extend([f"Block{k}_pct_per100y" for k in (1,2,3)])
    labels=["Last 300","Last 200","Last 100","Block 1","Block 2","Block 3"]
    mat=summary[fields].to_numpy(dtype=float)
    fig,ax=plt.subplots(figsize=(11.3,8.2))
    ax.imshow(mat,cmap="coolwarm",vmin=-10,vmax=10,aspect="auto")
    ax.set_yticks(range(len(summary)),summary.Site.tolist())
    ax.set_xticks(range(6),labels)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v=mat[i,j]
            ax.text(j,i,f"{v:+.2f}",ha="center",va="center",fontsize=9,
                    color="white" if abs(v)>6 else "black")
    ax.set_title("15-site FATES VegC multiscale trends (% per 100 years)\n"
                 "Colors saturate at ±10%; numbers show actual values")
    fig.tight_layout()
    fig.savefig(output/"all15_01_trend_heatmap.png",dpi=185)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,6.0))
    x=np.arange(len(summary))
    ax.bar(x-.2,summary.LastCycleAbsDifference_pct,width=.4,label="Last cycle pair")
    ax.bar(x+.2,summary.Max4CycleAbsDifference_pct,width=.4,label="Maximum of last four pairs")
    ax.axhline(1,color="0.4",ls="--",label="1% exploratory")
    ax.axhline(2,color="0.4",ls=":",label="2% exploratory")
    ax.set_yscale("symlog",linthresh=1)
    ax.set_xticks(x,summary.Site.tolist(),rotation=30,ha="right")
    ax.set_ylabel("Phase-matched mean absolute VegC difference (%)")
    ax.set_title("A single quiet cycle can hide vegetation-carbon variability")
    ax.legend(frameon=False)
    ax.grid(axis="y",alpha=.25)
    fig.tight_layout()
    fig.savefig(output/"all15_02_cycle_variability.png",dpi=185)
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--six-snapshot",type=Path,default=SIX_ROOT)
    p.add_argument("--eleven-root",type=Path,default=NINE_ROOT)
    p.add_argument("--preflight",action="store_true",help="Validate all 15 input annual CSVs; do not write")
    args=p.parse_args()
    samples=([read_site(site,"6",args.six_snapshot) for site in SIX] +
             [read_site(site,"11",args.eleven_root) for site in NINE])
    for s in samples:
        print(f"VERIFIED {s['site']:7}: {s['n']} years, {s['L']}-year forcing cycle",flush=True)
    if args.preflight:
        print("ALL 15 SOURCES VALIDATED. NO FILES WRITTEN.",flush=True)
        return
    typ=subprocess.run(["stat","-f","-c","%T",str(RFS)],
                       capture_output=True,text=True,check=True).stdout.strip().lower()
    if typ not in ("nfs","nfs4") or not os.access(str(RFS),os.W_OK):
        raise RuntimeError("RFS must be a writable NFS mount on the login node")
    dest=OUTPUT_PARENT/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_15site_VegC")
    if dest.exists():
        raise RuntimeError("Refuse to overwrite existing analysis: "+str(dest))
    dest.mkdir(parents=True)
    table,provenance=[],[]
    for s in samples:
        station_dir=dest/s["site"]
        station_dir.mkdir()
        row,cycle=calculate(s)
        table.append(row)
        cycle.to_csv(station_dir/(s["site"]+"_last4_cycle_pairs.csv"),index=False)
        pd.DataFrame([row]).to_csv(station_dir/(s["site"]+"_window_metrics.csv"),index=False)
        plot_one(s,row,cycle,station_dir)
        provenance.append({k:v for k,v in s.items() if k!="v"})
        print(f"{s['site']}: 300/200/100 VegC trends "
              f"{row['Last300y_pct_per100y']:+.2f}, {row['Last200y_pct_per100y']:+.2f}, "
              f"{row['Last100y_pct_per100y']:+.2f} %/100yr; "
              f"max of last 4 cycle differences {row['Max4CycleAbsDifference_pct']:.2f}%",flush=True)
    result=pd.DataFrame(table)
    result.to_csv(dest/"all15_VegC_multiscale_summary.csv",index=False)
    plot_summary(result,dest)
    (dest/"PROVENANCE_AND_METHODS.json").write_text(json.dumps({
        "sources":provenance,"records":len(result),
        "analysis_not_equilibrium_certificate":True,
        "trend_formula":"OLS VegC slope divided by mean VegC and multiplied by 10000, expressed % per 100 years",
        "windows":"last 300,200,100 yr; disjoint chronological 100 yr blocks in final 300 yr",
        "cycles":"last four adjacent pairs of complete forcing cycles (same forcing phase); ignore incomplete tail",
        "cycle_metric":"100 * mean(abs(next_forcing_cycle_year[i]-prev_forcing_cycle_year[i])) / mean(abs(prev_forcing_cycle_year[i]))",
        "screens":"Exploratory (not official CTSM): all last 100/200/300 trends abs < 1 or 2 %/100yr AND each of last four cycle differences < 1 or 2%",
        "limits":"Not an assessment of GPP, NEE, LAI, PFT composition, carbon closure or site realism; 1% and 2% are study-defined."
    },indent=2,ensure_ascii=False)+"\n")
    cols=["Site","ArchivedYears","Last300y_pct_per100y","Last200y_pct_per100y",
          "Last100y_pct_per100y","LastCycleAbsDifference_pct","Max4CycleAbsDifference_pct",
          "ExploratoryAllWindowsAnd4CyclesUnder1pct","ExploratoryAllWindowsAnd4CyclesUnder2pct"]
    print("\nFINAL 15-SITE RESULTS\n"+result[cols].to_string(index=False),flush=True)
    print("SAVED TO RESEARCH FILESTORE:",dest,flush=True)


if __name__=="__main__":
    main()

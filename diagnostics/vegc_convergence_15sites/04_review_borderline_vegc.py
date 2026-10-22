#!/usr/bin/env python3
"""Read-only deeper phase-aligned VegC diagnostics for four borderline stations.

Full forcing-cycle comparison over last ~300 years, trailing ~100/200/300
cycle-mean slopes, four adjacent signed changes, largest adjacent-cycle jump,
mean of last 4 cycles versus previous 4, optional control check.
Writes a versioned Research Filestore snapshot; never touches cases or restarts.
Requires 01_analyze_15site_vegc.py and 02_phase_aligned_15site_vegc.py beside it.
"""
from __future__ import annotations
import argparse, json, os, math, sys
from pathlib import Path
from datetime import datetime, timezone
os.environ["MPLBACKEND"]="Agg"
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import importlib.util

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,str(HERE/file))
    if spec is None or spec.loader is None:raise RuntimeError("Missing dependency "+file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load("vegcbaseread","01_analyze_15site_vegc.py")
phase=load("vegccycleread","02_phase_aligned_15site_vegc.py")
BORDER={"DE-Tha":"6","NL-Loo":"6","BE-Bra":"11","FR-Fon":"11"}
OUT=base.OUTPUT_PARENT/"borderline_second_review"

def assess(x):
    raw=x["v"]; L=x["L"]; K=x["n"]//L;means=raw[:K*L].reshape(K,L).mean(axis=1)
    allrow,pairs,_=phase.cycle_statistics(x)
    if len(means)<15:raise ValueError("Need >=15 complete forcing cycles")
    comp=[]
    for j in range(1,K):
        a,b=means[j-1],means[j]
        comp.append(dict(Site=x["site"],FromCycle=j,ToCycle=j+1,
                         FromElapsedYear=(j-1)*L+1,ToElapsedYear=(j+1)*L,
                         VegCmeanBefore_kgCm2=a,VegCmeanAfter_kgCm2=b,
                         SignedChange_kgCm2=b-a,
                         SignedChange_pct=100*(b-a)/abs(a) if abs(a)>1e-12 else float("nan"),
                         SignedDrift_pct_per100yr=10000*(b-a)/(L*abs(a)) if abs(a)>1e-12 else float("nan")))
    cds=pd.DataFrame(comp)
    final8=means[-8:];recent4=means[-4:];previous4=means[-8:-4]
    # Same number of full forcing cycles on each side of this comparison.
    delta4=100*(recent4.mean()-previous4.mean())/abs(previous4.mean()) if abs(previous4.mean())>1e-12 else np.nan
    last4=pairs.SignedMeanChange_pct.to_numpy()
    persistent=bool(np.all(last4>0) or np.all(last4<0))
    last300cycles=math.ceil(300/L)
    r={
      "Site":x["site"],"ArchivedYears":x["n"],"CompleteYears":K*L,"CycleYears":L,
      "Last300_pct_per100yr":allrow["W300_Trend_pct_per_100yr"],
      "Last200_pct_per100yr":allrow["W200_Trend_pct_per_100yr"],
      "Last100_pct_per100yr":allrow["W100_Trend_pct_per_100yr"],
      "Recent4_vs_previous4_cycleMeans_pct":delta4,
      "Last4_signed_cycle_changes_pct":",".join(f"{v:+.3f}" for v in last4),
      "Last4_signed_cycle_changes_same_direction":persistent,
      "Last4_max_phaseMatched_absDiff_pct":allrow["Max4CycleMeanAbsDiff_pct"],
      "Last300cycleMeans_min_kgCm2":float(means[-last300cycles:].min()),
      "Last300cycleMeans_max_kgCm2":float(means[-last300cycles:].max()),
      "LargestLast300_cycleMeanJump_pct":float(cds.iloc[-last300cycles:].SignedChange_pct.abs().max()),
      "LargestLast300_cycleMeanJump_to_cycle":int(cds.iloc[-last300cycles:].iloc[cds.iloc[-last300cycles:].SignedChange_pct.abs().argmax()].ToCycle),
      "Interpretation":"REQUIRES_FLUX_CHECK" if (abs(allrow["W100_Trend_pct_per_100yr"])>=2 or allrow["Max4CycleMeanAbsDiff_pct"]>=2) else "LOW_DRIFT_SCREEN",
    }
    return r,cds,means,pairs

def figure(x,entry,diffs,means,pairs,out):
    L=x["L"];K=len(means);center=(np.arange(K)+.5)*L+.5
    k=math.ceil(300/L);years=center[-k:]
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(11,7.7),sharex=False)
    ax1.plot(years,means[-k:],color="#315f7d",lw=1.2,marker="o",markersize=3)
    for w,color in [(300,"#315f7d"),(200,"#248a65"),(100,"#bd6630")]:
        n=math.ceil(w/L);y=means[-n:];t=center[-n:]
        b,a=np.polyfit(t,y,1)
        ax1.plot(t,a+b*t,lw=2,color=color,label=f"≥{w}y: {entry[f'Last{w}_pct_per100yr']:+.2f}%/100yr")
    ax1.legend(frameon=False)
    ax1.set_title(x["site"]+" — complete forcing-cycle mean FATES VegC")
    ax1.set_xlabel("Elapsed spin-up year");ax1.set_ylabel("kg C m$^{-2}$")
    ax1.grid(alpha=.2)
    sub=diffs.iloc[-k:]
    ax2.bar(sub.ToCycle.astype(str),sub.SignedChange_pct,color=["#ab5f51" if v<0 else "#39856d" for v in sub.SignedChange_pct])
    ax2.axhline(0,color="0.35",lw=.8)
    ax2.set_title("Adjacent complete-cycle mean changes (signed, % per cycle)")
    ax2.set_xlabel("Cycle index");ax2.set_ylabel("Signed change (%)")
    ax2.tick_params(axis="x",rotation=60)
    ax2.grid(axis="y",alpha=.2)
    fig.tight_layout()
    fig.savefig(out/(x["site"]+"_borderline_second_review.png"),dpi=175)
    plt.close(fig)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preflight",action="store_true")
    p.add_argument("--six-snapshot",type=Path,default=base.SIX_ROOT)
    p.add_argument("--eleven-root",type=Path,default=base.NINE_ROOT)
    args=p.parse_args()
    data=[]
    for site,batch in BORDER.items():
        root=args.six_snapshot if batch=="6" else args.eleven_root
        x=base.read_site(site,batch,root)
        row,_,_,_=assess(x);data.append(x)
        print(f"VERIFIED {site}: n={x['n']} L={x['L']} last100={row['Last100_pct_per100yr']:+.2f}%/100yr",flush=True)
    if args.preflight:
        print("PREFLIGHT PASSED: four sites; nothing written",flush=True)
        return
    phase.nfs_guard()
    out=OUT/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_four_site_review")
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for x in data:
        row,diffs,means,pairs=assess(x)
        sdir=out/x["site"];sdir.mkdir()
        diffs.to_csv(sdir/(x["site"]+"_all_complete_cycle_signed_jumps.csv"),index=False)
        pairs.to_csv(sdir/(x["site"]+"_last_four_phase_matched_pairs.csv"),index=False)
        figure(x,row,diffs,means,pairs,sdir)
        rows.append(row)
        print(f"RESULT {x['site']} last300={row['Last300_pct_per100yr']:+.2f} "
              f"last200={row['Last200_pct_per100yr']:+.2f} "
              f"last100={row['Last100_pct_per100yr']:+.2f} "
              f"4cycle-vs-prior4={row['Recent4_vs_previous4_cycleMeans_pct']:+.2f}% "
              f"sameDirection={row['Last4_signed_cycle_changes_same_direction']}",flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(out/"four_site_borderline_second_review.csv",index=False)
    (out/"METHODS_AND_PROVENANCE.json").write_text(json.dumps({
        "input_files":[{"site":x["site"],"source":x["source"],"sha256":x["sha256"]} for x in data],
        "method":"Read-only phase-aligned complete forcing cycles; compare means and signed jumps; last four versus previous four complete cycles; screening not final convergence.",
        "limitations":"No new GPP/NEE flux-stationarity test; uses VegC annual means only. Four period means are not independent climate realizations."
    },indent=2)+"\n")
    print("\nFOUR SITE REVIEW\n"+df.to_string(index=False),flush=True)
    print("SAVED:",out,flush=True)

if __name__=="__main__":
    main()

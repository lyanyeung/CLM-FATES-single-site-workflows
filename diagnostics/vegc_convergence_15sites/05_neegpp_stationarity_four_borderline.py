#!/usr/bin/env python3
"""Review four borderline spin-ups: NEE stability first, then GPP.

Modes:
  preflight: read-only inspect archive filenames + sample NetCDF units/calendar.
  extract:   read frozen history years, integrate daily fluxes to annual totals,
             calculate full-forcing-cycle and multiscale stability; save to HOME.
  publish:   login-node-only SHA256-verified copy of one HOME session to RFS.

IMPORTANT: no modifications to CIME cases, restarts, sources, or Slurm jobs.
The flux analysis compares model with its OWN earlier cycles, NOT with EC.
No official CTSM numerical flux-equilibrium threshold is assumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import sys

os.environ["MPLBACKEND"] = "Agg"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ARCHIVE = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive")
STAGING = Path.home() / "CLM_FATES_FluxStationarity" / "staging"
RFS_ROOT = Path("/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Analysis/flux_stationarity_borderline_four")
# Frozen checkpoint from 2026-10-22 VegC review; do not silently use newer states.
SITES = {
 "DE-Tha": {"start":1996, "L":30, "cap":1680, "case":"DE-Tha_FATES_SPINUP500"},
 "NL-Loo": {"start":1997, "L":29, "cap":1450, "case":"NL-Loo_FATES_SPINUP500"},
 "BE-Bra": {"start":1996, "L":30, "cap":990, "case":"BE-Bra_FATES_SPINUP500_11P"},
 "FR-Fon": {"start":2005, "L":21, "cap":987, "case":"FR-Fon_FATES_SPINUP500_11P"},
}
NEED_FIELDS = ("FATES_NEP", "FATES_GPP")
YEAR_RX = re.compile(r"\.clm2\.h0a\.(\d{4})-01-0[12]-00000\.nc$")
KGS_TO_GCS = 1000.0

class Stop(Exception):
 pass

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):
   h.update(block)
 return h.hexdigest()

def ncycle(d):
 return max(math.ceil(300/d["L"]),8)

def index_site(site):
 d=SITES[site]; hist=ARCHIVE/d["case"]/"lnd"/"hist"
 if not hist.is_dir(): raise Stop(f"{site}: missing archive {hist}")
 expected=ncycle(d)*d["L"]
 # Read last complete, phase-aligned cycles according to frozen VegC checkpoint.
 first_elapsed=d["cap"]-expected+1
 years=list(range(d["start"]+first_elapsed-1,d["start"]+d["cap"]))
 index={}
 for p in hist.glob(d["case"]+".clm2.h0a.*.nc"):
  m=YEAR_RX.search(p.name)
  if m:
   y=int(m.group(1))
   if y in years:
    if y in index: raise Stop(f"{site}: duplicate h0a for year {y}")
    index[y]=p
 missing=[y for y in years if y not in index]
 if missing: raise Stop(f"{site}: missing {len(missing)} of {len(years)} h0a files, examples {missing[:12]}")
 return d,[(y,index[y]) for y in years]

def units_factor(ds,name):
 if name not in ds.variables: raise Stop(f"{name} not in NetCDF")
 u=str(getattr(ds.variables[name],"units","")).lower().replace(" ","")
 if "kg" not in u or not any(x in u for x in ("s-1","/s","s^-1")):
  raise Stop(f"{name}: expected kg C m-2 s-1, got {u!r}")
 return 1000.0

def read_nc(path,modelyear,load=False):
 with Dataset(path) as ds:
  if "time" not in ds.variables:raise Stop(f"{path.name} missing time")
  t=ds.variables["time"]
  bounds_name=next((z for z in ("time_bounds","time_bnds") if z in ds.variables),None)
  if not bounds_name:raise Stop(f"{path.name}: no interval time bounds")
  bounds=np.asarray(ds.variables[bounds_name][:],dtype=float)
  if bounds.ndim!=2 or bounds.shape[1]!=2 or bounds.shape[0]!=365:
   raise Stop(f"{path.name}: unexpected time bounds shape {bounds.shape}")
  timeunit=str(getattr(t,"units",""))
  tu=timeunit.lower().strip()
  if tu.startswith("days since "):factor=86400.0
  elif tu.startswith("hours since "):factor=3600.0
  elif tu.startswith("seconds since "):factor=1.0
  else:raise Stop(f"{path.name}: unsupported time units {timeunit}")
  seconds=np.diff(bounds,axis=1)[:,0]*factor
  if not np.isfinite(seconds).all() or not np.allclose(seconds,86400.0,atol=1.0):
   raise Stop(f"{path.name}: not 365 daily NO_LEAP intervals, bounds durations={np.unique(seconds)[:5]}")
  dates=num2date(bounds[:,0],timeunit,calendar=str(getattr(t,"calendar","noleap")),
                 only_use_cftime_datetimes=True)
  if any(dt.year!=modelyear for dt in dates):
   raise Stop(f"{path.name}: date model year differs from filename year")
  days=[(int(dt.month),int(dt.day)) for dt in dates]
  if len(set(days))!=365 or (2,29) in days:
   raise Stop(f"{path.name}: unexpected missing, duplicate or leap days")
  for name in NEED_FIELDS:units_factor(ds,name)
  if not load:return {"units":{v:str(ds.variables[v].units) for v in NEED_FIELDS},
                      "shape":365,"calendar":getattr(t,"calendar","noleap"),
                      "time_unit":timeunit}
  data={}
  for name in NEED_FIELDS:
   var=ds.variables[name]
   if "time" not in var.dimensions:raise Stop(f"{path.name}:{name} missing time dimension")
   arr=var[:]
   if np.ma.isMaskedArray(arr):arr=arr.filled(np.nan)
   arr=np.asarray(arr,dtype=float)
   arr=np.moveaxis(arr,var.dimensions.index("time"),0)
   if arr.shape[0]!=365 or int(np.prod(arr.shape[1:]))!=1:
    raise Stop(f"{path.name}: unexpected spatial dimensions in {name}: {arr.shape}")
   arr=arr.reshape(365)
   if not np.isfinite(arr).all():
    raise Stop(f"{path.name}: invalid {name}")
   data[name]=arr*seconds*units_factor(ds,name)
  return data,days

def cycle_fit(means,L,k):
 v=np.asarray(means[-k:],dtype=float)
 if len(v)<4 or not np.isfinite(v).all():raise Stop("insufficient cycle means")
 # Physical time in model years, not cycle indices.
 t=np.arange(k,dtype=float)*L + .5*L
 return float(np.polyfit(t,v,1)[0])*100.0

def analyze_site(site,records,out):
 d=SITES[site]; L=d["L"]; K=ncycle(d)
 if len(records)!=K*L:raise Stop("record count mismatch")
 result=pd.DataFrame(records)
 result.to_csv(out/(site+"_annual_model_fluxes.csv"),index=False)
 nee=result.NEE_gCm2yr.to_numpy().reshape(K,L)
 gpp=result.GPP_gCm2yr.to_numpy().reshape(K,L)
 if not np.isfinite(nee).all() or not np.isfinite(gpp).all():raise Stop("nonfinite annual flux")
 cycles=[]
 for k in range(K):
  cycles.append({"Site":site,"CycleIndex":d["cap"]//L-K+k+1,
                 "ElapsedStart":d["cap"]-K*L+k*L+1,
                 "ElapsedEnd":d["cap"]-K*L+(k+1)*L,
                 "NEE_mean_annual_gCm2yr":float(nee[k].mean()),
                 "GPP_mean_annual_gCm2yr":float(gpp[k].mean())})
 cd=pd.DataFrame(cycles);cd.to_csv(out/(site+"_complete_cycle_means.csv"),index=False)
 pairs=[]
 for k in range(1,K):
  nprev,ncur=nee[k-1],nee[k]
  gprev,gcur=gpp[k-1],gpp[k]
  gbase=float(np.mean(np.abs(gprev)))
  if gbase<=1e-10:raise Stop(f"{site}: GPP reference too close to zero")
  pairs.append({
   "Site":site,"PreviousCycle":int(cd.CycleIndex.iloc[k-1]),
   "CurrentCycle":int(cd.CycleIndex.iloc[k]),
   "NEE_signed_mean_diff_gCm2yr":float(np.mean(ncur-nprev)),
   "NEE_phase_matched_abs_diff_gCm2yr":float(np.mean(np.abs(ncur-nprev))),
   "GPP_signed_mean_diff_gCm2yr":float(np.mean(gcur-gprev)),
   "GPP_phase_matched_abs_diff_gCm2yr":float(np.mean(np.abs(gcur-gprev))),
   "GPP_signed_diff_pct":float(100*np.mean(gcur-gprev)/gbase),
   "GPP_phase_matched_abs_diff_pct":float(100*np.mean(np.abs(gcur-gprev))/gbase)
  })
 pairs_df=pd.DataFrame(pairs);pairs_df.to_csv(out/(site+"_paired_fullcycle_flux_differences.csv"),index=False)
 last4=pairs_df.tail(4)
 r={"Site":site,"Case":d["case"],"ForcingCycleYears":L,
    "LastCompleteElapsedYear":d["cap"],"AnalyzedFullCycles":K,
    "NEE_latest_cycle_mean_gCm2yr":float(nee[-1].mean()),
    "NEE_last4_max_pair_absDiff_gCm2yr":float(last4.NEE_phase_matched_abs_diff_gCm2yr.max()),
    "NEE_last4_max_abs_signedDiff_gCm2yr":float(last4.NEE_signed_mean_diff_gCm2yr.abs().max()),
    "NEE_last4_mean_signedDiff_gCm2yr":float(last4.NEE_signed_mean_diff_gCm2yr.mean()),
    "NEE_signed_changes_same_direction":bool(np.all(last4.NEE_signed_mean_diff_gCm2yr>0) or np.all(last4.NEE_signed_mean_diff_gCm2yr<0)),
    "GPP_latest_cycle_mean_gCm2yr":float(gpp[-1].mean()),
    "GPP_last4_max_pair_absDiff_pct":float(last4.GPP_phase_matched_abs_diff_pct.max()),
    "GPP_last4_max_abs_signedDiff_pct":float(last4.GPP_signed_diff_pct.abs().max()),
    "GPP_signed_changes_same_direction":bool(np.all(last4.GPP_signed_diff_pct>0) or np.all(last4.GPP_signed_diff_pct<0))}
 for W in (100,200,300):
  k=math.ceil(W/L)
  r[f"W{W}_actual_years"]=L*k
  r[f"NEE_W{W}_slope_gCm2yr_per100yr"]=cycle_fit(nee.mean(axis=1),L,k)
  r[f"GPP_W{W}_slope_gCm2yr_per100yr"]=cycle_fit(gpp.mean(axis=1),L,k)
  gbar=np.mean(gpp.mean(axis=1)[-k:])
  r[f"GPP_W{W}_trend_pct_per100yr"]=100*r[f"GPP_W{W}_slope_gCm2yr_per100yr"]/abs(gbar) if abs(gbar)>1e-9 else np.nan
 # NO arbitrary NEE % cut-off; near-zero annual NEE makes it unreliable.
 # These are study-defined 2% GPP preliminary screens, not flux equilibration certification.
 r["GPP_exploratory_2pct_candidate"]=bool(
  all(np.isfinite(r[f"GPP_W{W}_trend_pct_per100yr"]) and
      abs(r[f"GPP_W{W}_trend_pct_per100yr"])<2 for W in (100,200,300))
  and r["GPP_last4_max_pair_absDiff_pct"]<2)
 r["Decision"]="REVIEW_NEE_FIRST_THEN_GPP"
 for flux,column in (("NEE","NEE_mean_annual_gCm2yr"),("GPP","GPP_mean_annual_gCm2yr")):
  fig,ax=plt.subplots(figsize=(10.2,4.8))
  ax.plot(cd.CycleIndex,cd[column],marker="o",markersize=3)
  ax.axvline(cd.CycleIndex.iloc[-math.ceil(100/L)],color="0.6",ls="--",label="Recent ~100y start")
  ax.set_xlabel("Complete forcing-cycle index")
  ax.set_ylabel("Mean annual "+flux+" (g C m$^{-2}$ yr$^{-1}$)")
  ax.set_title(site+" — "+flux+" stability (model only, phase-aligned)")
  ax.grid(alpha=.25);ax.legend(frameon=False)
  fig.tight_layout();fig.savefig(out/(site+"_"+flux+"_cycle_mean_stability.png"),dpi=185);plt.close(fig)
 return r

def inspect_site(site):
 d,files=index_site(site)
 samples=[files[0],files[-1]]
 details=[]
 for y,p in samples:
  check=read_nc(p,y,load=False)
  details.append({"path":str(p),"year":y,"size_bytes":p.stat().st_size,**check})
 return d,files,details

def preflight(sites):
 all_good=True
 for s in sites:
  try:
   d,f,samples=inspect_site(s)
   print(f"OK {s}: {len(f)} annual h0a; cycle={d['L']}yr; "
         f"elapsed={d['cap']-len(f)+1}..{d['cap']}; "
         f"sample_units={samples[-1]['units']}",flush=True)
  except (Stop,OSError,ValueError,RuntimeError) as e:
   print(f"MISSING_OR_INVALID {s}: {e}",flush=True);all_good=False
 if not all_good:raise Stop("preflight did not pass; extract only accessible valid sites")

def extract(sites):
 # To preserve users' Scratch quota, derive reports under Home only.
 STAGING.mkdir(parents=True,exist_ok=True)
 output=STAGING/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+str(len(sites))+"site_NEE_then_GPP")
 output.mkdir(exist_ok=False)
 rows=[];failures=[];metadata=[]
 for s in sites:
  try:
   d,files,samples=inspect_site(s)
   print(f"START {s} annual files={len(files)}",flush=True)
   vals=[]
   for ix,(yr,p) in enumerate(files):
    data,days=read_nc(p,yr,load=True)
    vals.append({"Site":s,"ModelYear":yr,"ElapsedYear":yr-d["start"]+1,
                 "NEE_gCm2yr":float(-data["FATES_NEP"].sum()),
                 "GPP_gCm2yr":float(data["FATES_GPP"].sum())})
    if (ix+1)%50==0:print(f"READ {s}: {ix+1}/{len(files)}",flush=True)
   folder=output/s;folder.mkdir()
   row=analyze_site(s,vals,folder)
   rows.append(row)
   metadata.append({"site":s,"source_case":d["case"],"checkpoint_frozen":d["cap"],
                    "history_years_analyzed":len(files),
                    "first_history":str(files[0][1]),"last_history":str(files[-1][1]),
                    "first_last_samples":samples,
                    "model_NEE":"-FATES_NEP (positive: atmosphereward)",
                    "model_GPP":"FATES_GPP (positive: uptake)",
                    "units":"g C m-2 yr-1 integrated from daily kg C m-2 s-1 using model time_bounds"})
   print(f"RESULT {s} NEE last4 max yearly abs cycle diff="
         f"{row['NEE_last4_max_pair_absDiff_gCm2yr']:.2f} gC/m2/yr; "
         f"GPP last4 max phase diff={row['GPP_last4_max_pair_absDiff_pct']:.2f}%",flush=True)
  except Exception as e:
   failures.append({"site":s,"error":str(e)})
   print(f"FAILED {s}: {type(e).__name__}: {e}",flush=True)
 pd.DataFrame(rows).to_csv(output/"four_site_flux_stationarity_summary.csv",index=False)
 (output/"PROVENANCE.json").write_text(json.dumps({"sources":metadata,"errors":failures,
   "method":"NEE evaluated before GPP; 100/200/300yr full-cycle-mean trends, same forcing-year phase differences",
   "calculation":"Daily model rates multiplied by daily time_bounds duration, 1000 kg->g; annually integrated, then cycle/year averages",
   "disclaimer":"Flux stability must be interpreted with VegC evidence; no automatic CONTINUE_RUN or case.submit; thresholds study-defined only.",
   "note":"Does not compare against EC observations or change NT/DT priority."},
   indent=2,ensure_ascii=False)+"\n")
 print("\nFOUR SITE FLUX RESULTS — NEE THEN GPP",flush=True)
 if rows:
  df=pd.DataFrame(rows)
  selected=["Site","NEE_latest_cycle_mean_gCm2yr",
    "NEE_last4_max_pair_absDiff_gCm2yr","NEE_W300_slope_gCm2yr_per100yr",
    "NEE_W200_slope_gCm2yr_per100yr","NEE_W100_slope_gCm2yr_per100yr",
    "GPP_last4_max_pair_absDiff_pct","GPP_W300_trend_pct_per100yr",
    "GPP_W200_trend_pct_per100yr","GPP_W100_trend_pct_per100yr",
    "GPP_exploratory_2pct_candidate"]
  print(df[selected].to_string(index=False),flush=True)
 print("FAILURES",json.dumps(failures,ensure_ascii=False),flush=True)
 print("HOME_RESULT",output,flush=True)
 if failures:raise Stop("Some sites failed; do not infer their flux stability")
 
def publish(folder):
 folder=Path(folder).expanduser().resolve()
 if folder.parent!=STAGING.resolve() or not folder.is_dir():
  raise Stop("publish requires an existing exact Home staging session path")
 if not (folder/"PROVENANCE.json").is_file():raise Stop("Missing PROVENANCE.json")
 p=subprocess.run(["stat","-f","-c","%T",str(RFS_ROOT.parent)],
                  capture_output=True,text=True,check=True)
 if p.stdout.strip().lower() not in ("nfs","nfs4"):
  raise Stop("Research Filestore not available as NFS. Run publish on login node.")
 RFS_ROOT.mkdir(parents=True,exist_ok=True)
 target=RFS_ROOT/folder.name
 if target.exists():raise Stop("Refusing to overwrite RFS output "+str(target))
 # Avoid moving source and deleting Home staging before checksum confirmation.
 shutil.copytree(folder,target,symlinks=False)
 a={str(p.relative_to(folder)):sha(p) for p in folder.rglob("*") if p.is_file()}
 b={str(p.relative_to(target)):sha(p) for p in target.rglob("*") if p.is_file()}
 if a!=b:raise Stop("RFS copied files have a checksum mismatch; keep Home staging")
 print(f"RFS_VERIFIED {len(a)} files, no Home data deleted: {target}",flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("mode",choices=("preflight","extract","publish"))
 p.add_argument("--sites",nargs="+",choices=list(SITES),default=list(SITES))
 p.add_argument("--session",type=Path,help="Exact HOME_RESULT directory, required for publish")
 args=p.parse_args()
 if args.mode=="preflight":preflight(args.sites)
 elif args.mode=="extract":extract(args.sites)
 else:
  if args.session is None:p.error("--session required for publish")
  publish(args.session)

if __name__=="__main__":
 try:main()
 except (Stop,ValueError,OSError,RuntimeError,subprocess.CalledProcessError) as e:
  print("STOP:",e,file=sys.stderr);sys.exit(2)

#!/usr/bin/env python3
"""FATES initialization/PFT replacement: surface input vs first model years vs frozen endpoint.

READ ONLY. Run on IRIDIS6 login with current Scratch archive.
    python 09_audit_initial_surface_vs_fates.py --preflight
    python 09_audit_initial_surface_vs_fates.py --run

Three distinct quantities:
  1. The effective CLM fsurdat host-landunit and PCT_NAT_PFT vector, NOT FATES vegetation.
  2. The actual dynamic FATES_VEGC_PF (share of living VegC) in model year 1.
  3. The same FATES variable in model years 2, 5, 20, 100 and frozen endpoint.

First-year average is AFTER model integration, NOT time-zero seed composition.
FATES PFT names are obtained from the actual fates_paramfile, never CLM indices.
Writes only to unique HOME session; never modifies CIME, archive, RFS, Slurm.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone

import numpy as np
from netCDF4 import Dataset

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
CASES=ROOT/"cases"
ARCHIVE=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive")
OUT=Path.home()/"CLM_FATES_initial_vegetation_15sites"

# Frozen snapshot ending at 2026-10-22 diagnostic, not necessarily current live run.
SITES={
 "DE-Hai":("DBF",2000,1000,"DE-Hai_FATES_SPINUP500"),
 "RU-Fyo":("ENF",1998,1690,"RU-Fyo_FATES_SPINUP500"),
 "DE-Tha":("ENF",1996,1680,"DE-Tha_FATES_SPINUP500"),
 "DK-Sor":("DBF",1996,1715,"DK-Sor_FATES_SPINUP500"),
 "NL-Loo":("ENF",1997,1460,"NL-Loo_FATES_SPINUP500"),
 "IL-Yat":("ENF",2000,1920,"IL-Yat_FATES_SPINUP500"),
 "AT-Neu":("GRA",2002,1000,"AT-Neu_FATES_SPINUP500_11P"),
 "BE-Bra":("MF",1996,1000,"BE-Bra_FATES_SPINUP500_11P"),
 "CH-Cha":("GRA",2005,1000,"CH-Cha_FATES_SPINUP500_11P"),
 "CH-Fru":("GRA",2005,1000,"CH-Fru_FATES_SPINUP500_11P"),
 "CH-Lae":("MF",2004,1000,"CH-Lae_FATES_SPINUP500_11P"),
 "CZ-Stn":("DBF",2010,1000,"CZ-Stn_FATES_SPINUP500_11P"),
 "FI-Sod":("ENF",2001,1000,"FI-Sod_FATES_SPINUP500_11P"),
 "FR-Fon":("DBF",2005,1000,"FR-Fon_FATES_SPINUP500_11P"),
 "GL-ZaH":("GRA",2000,1000,"GL-ZaH_FATES_SPINUP500_11P"),
}

def parse_namelist(p):
 if not p.is_file():return {}
 d={}
 for s in p.read_text(errors="replace").splitlines():
  m=re.match(r"^\s*([a-z][\w]*)\s*=\s*([^!]+)",s,re.I)
  if not m:continue
  k,v=m.group(1).lower(),m.group(2).strip().rstrip(",").strip()
  if v and v[0] in "'\"":
   v=v[1:].split(v[0],1)[0]
  d[k]=v
 return d

def resolve(raw):
 s=(raw or "").strip().strip("'\"")
 if not s:return None
 s=s.replace("\${DIN_LOC_ROOT}",str(ROOT/"inputdata")).replace("$DIN_LOC_ROOT",str(ROOT/"inputdata"))
 p=Path(s)
 return p if p.is_absolute() else None

def load_param_names(nml):
 path=resolve(nml.get("fates_paramfile",""))
 if path is None or not path.is_file():return None,str(path or ""), "MISSING_PARAMFILE"
 if path.suffix.lower()!=".json":return None,str(path),"PARAM_FORMAT_NEEDS_REVIEW"
 try:
  j=json.loads(path.read_text())
  n=int(j["dimensions"]["fates_pft"])
  o=j["parameters"]["fates_pftname"]
  if o["dims"]!=["fates_pft"] or len(o["data"])!=n:raise ValueError("Unexpected FATES names dims")
  return [str(x).strip() for x in o["data"]],str(path),"OK"
 except Exception as e:return None,str(path),f"INVALID_PARAM:{type(e).__name__}"

def scalar(ds,name):
 if name not in ds.variables:return None
 v=ds.variables[name][:]
 if np.ma.isMaskedArray(v):v=v.filled(np.nan)
 v=np.asarray(v,dtype=float)
 if v.size!=1 or not np.isfinite(v).all():return None
 return float(v.flat[0])

def surface_info(nml):
 p=resolve(nml.get("fsurdat",""))
 meta={"effective_fsurdat":str(p or ""),"status":"", "host_natpft_size":None,
       "dominant_host_natpft_index":None,"dominant_host_natpft_pct":None}
 component=[]
 if p is None or not p.is_file():
  meta["status"]="MISSING_EFFECTIVE_FSURDAT"
  return meta,component
 try:
  with Dataset(p) as ds:
   for name in ("PCT_NATVEG","PCT_CROP","PCT_WETLAND","PCT_LAKE","PCT_GLACIER"):
    meta[name]=scalar(ds,name)
   if "PCT_NAT_PFT" not in ds.variables:
    meta["status"]="MISSING_PCT_NAT_PFT"
    return meta,component
   var=ds.variables["PCT_NAT_PFT"]
   axes=[i for i,d in enumerate(var.dimensions) if "pft" in d.lower()]
   if len(axes)!=1:
    meta["status"]="AMBIGUOUS_HOST_PFT_DIMENSION"
    return meta,component
   x=var[:]
   if np.ma.isMaskedArray(x):x=x.filled(np.nan)
   x=np.asarray(x,dtype=float)
   x=np.moveaxis(x,axes[0],0)
   if int(np.prod(x.shape[1:]))!=1 or not np.isfinite(x).all() or (x<0).any():
    meta["status"]="INVALID_HOST_PFT_VECTOR"
    return meta,component
   v=x.reshape(x.shape[0])
   meta["host_natpft_size"]=len(v)
   meta["host_natpft_total_pct_of_natveg"]=float(v.sum())
   i=int(v.argmax())
   meta["dominant_host_natpft_index"]=i
   meta["dominant_host_natpft_pct"]=float(v[i])
   meta["status"]="HOST_INDEX_ONLY_NOT_FATES_PFT"
   # Keep raw indices. Never silently decode 15/16-index CLM class schemes.
   for i,val in enumerate(v):
    component.append({"HostCLMPFTIndex":i,"HostNaturalPFTPercent":float(val),
                      "IndexMeaning":"Effective CLM surface; class labels require input-version-specific mapping"})
  return meta,component
 except Exception as e:
  meta["status"]="SURFACE_ERROR:"+type(e).__name__+":"+str(e)[:80]
  return meta,component

def get_history(site,case,year):
 hist=ARCHIVE/case/"lnd"/"hist"
 if not hist.is_dir():return None,"MISSING_HISTORY_DIR"
 paths=list(hist.glob(f"{case}.clm2.h0a.{year}-*.nc"))
 if len(paths)!=1:return None,"MISSING_YEAR_H0A" if not paths else "DUPLICATE_YEAR_H0A"
 return paths[0],"OK"

def fates_profile(p,names):
 if p is None:return None,"NO_FILE"
 try:
  with Dataset(p) as ds:
   if "FATES_VEGC_PF" not in ds.variables:return None,"MISSING_FATES_VEGC_PF"
   var=ds.variables["FATES_VEGC_PF"]
   dims=list(var.dimensions)
   axes=[i for i,s in enumerate(dims) if "pft" in s.lower()]
   if len(axes)!=1 or "time" not in dims:return None,"AMBIGUOUS_FATES_PFT_DIMENSION"
   a=var[:]
   if np.ma.isMaskedArray(a):a=a.filled(np.nan)
   a=np.asarray(a,dtype=float)
   a=np.moveaxis(a,axes[0],0)
   remain=[dim for i,dim in enumerate(dims) if i!=axes[0]]
   tidx=remain.index("time")+1
   if any(a.shape[i]!=1 for i in range(1,a.ndim) if i!=tidx):
    return None,"NON_SINGLETON_EXTRA_DIMENSIONS"
   if names is None or a.shape[0]!=len(names):
    return None,"UNVERIFIED_FATES_PFT_NAMES"
   b=np.nanmean(a,axis=tidx).reshape(len(names),-1)
   if b.shape[1]!=1 or not np.isfinite(b).all() or (b < -1e-10).any() or b.sum()<=0:
    return None,"INVALID_FATES_VEGC"
   v=np.maximum(0,b[:,0])
   return 100*v/v.sum(),"OK"
 except Exception as e:return None,"HISTORY_ERROR:"+type(e).__name__+":"+str(e)[:100]

def process(site,save=False):
 igbp,start,n,case=SITES[site]
 c=CASES/case
 nml=parse_namelist(c/"CaseDocs/lnd_in")
 if not nml:nml=parse_namelist(c/"user_nl_clm")
 names,param,param_status=load_param_names(nml)
 surf,surf_vec=surface_info(nml)
 flags={key:nml.get(key,"UNKNOWN") for key in
        ("use_fates","use_fates_nocomp","use_fates_fixed_biogeog","use_fates_sp","create_crop_landunit","use_crop")}
 row={"Site":site,"TowerIGBP":igbp,"Case":case,"FrozenElapsedYears":n,
      "StartCalendarYear":start,"ParamFile":param,"ParamNamesStatus":param_status,
      **flags, **surf}
 times=[1,2,5,20,100,n]
 detail=[]
 for elapsed in dict.fromkeys(times):
  yr=start+elapsed-1
  path,status=get_history(site,case,yr)
  vec,actual_status=fates_profile(path,names)
  if status!="OK":actual_status=status
  pref=f"FATES_Y{elapsed}"
  row[pref+"_source"]=str(path or "")
  row[pref+"_status"]=actual_status
  if vec is not None:
   idx=int(np.argmax(vec))
   row[pref+"_dominant"]=names[idx]
   row[pref+"_dominant_VegC_pct"]=float(vec[idx])
   for i,share in enumerate(vec):
    detail.append({"Site":site,"ElapsedModelYear":elapsed,"CalendarYear":yr,
                   "FATES_PFT_Slot_1based":i+1,"FATES_PFT_Name":names[i],
                   "FATES_VEGC_share_pct":float(share),
                   "Meaning":"Year-mean percentage of living vegetation carbon; not land cover or time-zero initialization"})
  else:
   row[pref+"_dominant"]=""
   row[pref+"_dominant_VegC_pct"]=""
  if elapsed in (1,n):
   print(f"{site:7s} {pref:13s} {row[pref+'_dominant'] or 'UNKNOWN':43s} "
         f"{str(row[pref+'_dominant_VegC_pct'])[:7]:7s} {actual_status}",flush=True)
 return row,[{"Site":site,**i} for i in surf_vec],detail

def csvout(path,rows):
 if not rows:return
 with path.open("w",newline="") as f:
  keys=list(rows[0])
  writer=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore")
  writer.writeheader();writer.writerows(rows)

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 op=ap.add_mutually_exclusive_group(required=True)
 op.add_argument("--preflight",action="store_true")
 op.add_argument("--run",action="store_true")
 ap.add_argument("--sites",nargs="+",choices=list(SITES),default=list(SITES))
 args=ap.parse_args()
 rows,host,pft=[],[],[]
 for s in args.sites:
  try:
   a,b,c=process(s)
   rows.append(a);host.extend(b);pft.extend(c)
  except Exception as exc:
   print("ERROR",s,str(exc),file=sys.stderr)
   raise
 if args.preflight:
  print(f"READ_ONLY PREFLIGHT rows={len(rows)}; no output written.")
  return
 OUT.mkdir(exist_ok=True,parents=True)
 path=OUT/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_initial_surface_and_FATES")
 path.mkdir(exist_ok=False)
 csvout(path/"15_site_surface_firstyear_final_PFT.csv",rows)
 csvout(path/"15_site_original_CLM_host_PFT_vector.csv",host)
 csvout(path/"15_site_FATES_PFT_initial_and_transition.csv",pft)
 (path/"PROVENANCE.json").write_text(json.dumps({
  "analysis_utc":datetime.now(timezone.utc).isoformat(),
  "model_data":"frozen archived h0a for model years 1,2,5,20,100 and most recent frozen endpoint",
  "surface":"effective fsurdat from CaseDocs/lnd_in and PCT_NAT_PFT/PCT_NATVEG/PCT_CROP",
  "limitations":[
   "First-year PFT percentages are after integration, not the exact pre-spin-up cold-start condition.",
   "FATES_PFT shares measure vegetation carbon, not fractional area.",
   "CLM surface PCT_NAT_PFT index labels cannot be interpreted as FATES PFT types.",
   "FATES full competition may initialize all parameter-file PFTs independent of local host PFT fractions.",
   "Original source grid-cell landcover and tower footprint can differ; site botanical survey remains required.",
   "Outputs strictly to HOME; no CIME or Slurm changes."],
  "ctsm_surface_reference":"https://escomp.github.io/CTSM/tech_note/Ecosystem/CLM50_Tech_Note_Ecosystem.html",
  "fates_coldstart_reference":"https://fates-users-guide.readthedocs.io/en/latest/user/Model-Initialization-Modes.html"
 },indent=2)+"\n")
 print("SAVED",path,flush=True)

if __name__=="__main__":main()

#!/usr/bin/env python3
"""Read-only FATES final-archived PFT composition and surface suitability audit.

Use on IRIDIS6 LOGIN node with Scratch archive mounted:
    python 08_audit_actual_fates_pft_15sites.py --preflight
    python 08_audit_actual_fates_pft_15sites.py --run

Produces only small CSV/JSON in HOME. No CIME writes, git changes, Slurm
submission, surface edits, restart modifications, or automatic scientific
clearance. Explicit MISSING_PFT_HISTORY when FATES_VEGC_PF was not output.

FATES_VEGC_PF gives PFT fractions of *living vegetation carbon*, never area.
Host PCT_CROP/PCT_NAT_PFT is not actual prognostic FATES PFT occupancy.
"""
from __future__ import annotations
import argparse,csv,json,os,re,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from netCDF4 import Dataset

USER="ly3n24"
CASE_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases")
OUTROOT=Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS/archive")
RESULT=Path.home()/"CLM_FATES_PFT_15site_audit"
SITES={
 "DE-Hai":("DBF","DE-Hai_FATES_SPINUP500",2000,1000),
 "RU-Fyo":("ENF","RU-Fyo_FATES_SPINUP500",1998,1690),
 "DE-Tha":("ENF","DE-Tha_FATES_SPINUP500",1996,1680),
 "DK-Sor":("DBF","DK-Sor_FATES_SPINUP500",1996,1715),
 "NL-Loo":("ENF","NL-Loo_FATES_SPINUP500",1997,1460),
 "IL-Yat":("ENF","IL-Yat_FATES_SPINUP500",2000,1920),
 "AT-Neu":("GRA","AT-Neu_FATES_SPINUP500_11P",2002,1000),
 "BE-Bra":("MF","BE-Bra_FATES_SPINUP500_11P",1996,1000),
 "CH-Cha":("GRA","CH-Cha_FATES_SPINUP500_11P",2005,1000),
 "CH-Fru":("GRA","CH-Fru_FATES_SPINUP500_11P",2005,1000),
 "CH-Lae":("MF","CH-Lae_FATES_SPINUP500_11P",2004,1000),
 "CZ-Stn":("DBF","CZ-Stn_FATES_SPINUP500_11P",2010,1000),
 "FI-Sod":("ENF","FI-Sod_FATES_SPINUP500_11P",2001,1000),
 "FR-Fon":("DBF","FR-Fon_FATES_SPINUP500_11P",2005,1000),
 "GL-ZaH":("GRA","GL-ZaH_FATES_SPINUP500_11P",2000,1000),
}
EXPECTED={
 "ENF":("needleleaf_evergreen_extratrop_tree",),
 "DBF":("broadleaf_colddecid_extratrop_tree",),
 "GRA":("arctic_c3_grass","cool_c3_grass","c4_grass"),
 # MF requires multiple PFTs to represent a mixed forest and field inventory.
 "MF":(),
}
NAMECHECK=re.compile(r"^[A-Za-z0-9_.-]+$")
HISTORY_RX=re.compile(r"\.clm2\.h0a\.(\d{4})-01-0[12]-00000\.nc$")

def parse_nml(path):
 if not path.is_file():return {}
 out={}
 for line in path.read_text(errors="replace").splitlines():
  m=re.match(r"^\s*([a-z_][a-z_0-9]*)\s*=\s*(.+)",line,re.I)
  if not m:continue
  v=m.group(2).split("!",1)[0].strip().rstrip(",")
  if v[:1] in "'\"":v=v[1:].split(v[0],1)[0]
  out[m.group(1).lower()]=v
 return out

def absolute_path(value):
 if not value:return None
 s=str(value).strip().strip("'\"")
 s=s.replace("\${DIN_LOC_ROOT}","/iridisfs/scratch/ly3n24/CLM_FATES/inputdata")
 s=s.replace("$DIN_LOC_ROOT","/iridisfs/scratch/ly3n24/CLM_FATES/inputdata")
 p=Path(s)
 return p if p.is_absolute() else None

def param_names(value):
 p=absolute_path(value)
 if p is None or not p.is_file():return None,str(p or ""), "PARAMETER_FILE_MISSING"
 try:
  if p.suffix==".json":
   data=json.loads(p.read_text())
   n=data["dimensions"]["fates_pft"]
   row=data["parameters"].get("fates_pftname",{})
   if row.get("dims")!=["fates_pft"]:return None,str(p),"PFT_NAME_DIMS_AMBIGUOUS"
   v=row["data"]
   if len(v)!=n:return None,str(p),"PFT_NAME_COUNT_MISMATCH"
   return [str(z).strip() for z in v],str(p),""
  if p.suffix in (".nc",".nc4"):
   with Dataset(p) as nc:
    if "fates_pftname" not in nc.variables:return None,str(p),"PFT_NAMES_UNAVAILABLE"
    var=nc.variables["fates_pftname"]
    x=np.asarray(var[:])
    if x.ndim==1:names=[str(z.decode() if isinstance(z,bytes) else z).strip() for z in x]
    else:
     names=["".join(z.decode() if isinstance(z,bytes) else str(z) for z in row).strip() for row in x]
    return names,str(p),""
  return None,str(p),"UNSUPPORTED_PARAM_FORMAT"
 except Exception as exc:
  return None,str(p),f"PARAMETER_PARSE_ERROR:{type(exc).__name__}"

def surface_crop(nml):
 p=absolute_path(nml.get("fsurdat",""))
 if not p or not p.is_file():return "","NO_VALID_EFFECTIVE_SURFACE"
 try:
  with Dataset(p) as ds:
   if "PCT_CROP" not in ds.variables:return "","SURFACE_HAS_NO_PCT_CROP"
   x=np.ma.asarray(ds.variables["PCT_CROP"][:]).filled(np.nan)
   if x.size!=1 or not np.isfinite(x).all():return "","NON_SINGLETON_CROP"
   return float(x.reshape(-1)[0]),"HOST_SURFACE_ONLY_NOT_ACTIVE_FATES_PFT"
 except Exception as exc:
  return "",f"SURFACE_READ_ERROR:{type(exc).__name__}"

def pft_history(site,case,final_model_year,names):
 folder=OUTROOT/case/"lnd"/"hist"
 if not folder.is_dir():return None,"NO_HISTORY_DIRECTORY",""
 pths=list(folder.glob(f"{case}.clm2.h0a.{final_model_year}-*.nc"))
 if len(pths)!=1:return None,("MISSING_FINAL_YEAR_H0A" if not pths else "AMBIGUOUS_FINAL_YEAR_H0A"),""
 p=pths[0]
 try:
  with Dataset(p) as ds:
   if "FATES_VEGC_PF" not in ds.variables:return None,"MISSING_PFT_HISTORY_FATES_VEGC_PF",str(p)
   v=ds.variables["FATES_VEGC_PF"]
   dims=tuple(v.dimensions)
   axes=[i for i,d in enumerate(dims) if "pft" in d.lower()]
   if len(axes)!=1 or "time" not in dims:
    return None,f"AMBIGUOUS_PFT_DIMENSIONS:{dims}",str(p)
   x=v[:]
   if np.ma.isMaskedArray(x):x=x.filled(np.nan)
   x=np.asarray(x,dtype=float)
   x=np.moveaxis(x,axes[0],0)
   if "time" in dims:
    # move PFT first, average over daily/monthly model history timesteps
    rest_dims=[d for i,d in enumerate(dims) if i!=axes[0]]
    t=rest_dims.index("time")+1
    if any(x.shape[i]!=1 for i in range(1,x.ndim) if i!=t):
     return None,f"NON_SINGLETON_OTHER_AXES:{v.dimensions},{x.shape}",str(p)
    x=np.nanmean(x,axis=t)
    x=x.reshape(x.shape[0],-1)
   if x.ndim!=2 or x.shape[1]!=1 or not np.isfinite(x).all():
    return None,"INVALID_OR_AMBIGUOUS_PFT_VALUES",str(p)
   vec=x[:,0]
   if np.any(vec< -1e-10) or np.sum(vec)<=0:
    return None,"INVALID_OR_ZERO_PFT_CARBON",str(p)
   if not names or len(names)!=len(vec):
    return None,"PFT_PARAMETER_NAMES_NOT_VERIFIED",str(p)
   return 100*np.maximum(vec,0)/np.sum(np.maximum(vec,0)),"OK",str(p)
 except Exception as exc:
  return None,f"NETCDF_ERROR:{type(exc).__name__}:{str(exc)[:100]}",str(p)

def one(site):
 igbp,case,start,elapsed=SITES[site]
 casepath=CASE_ROOT/case
 nml=parse_nml(casepath/"CaseDocs/lnd_in")
 if not nml:nml=parse_nml(casepath/"user_nl_clm")
 flags={k:nml.get(k,"UNKNOWN") for k in ("use_fates","use_fates_sp","use_fates_nocomp","use_fates_fixed_biogeog","create_crop_landunit","use_crop")}
 params=nml.get("fates_paramfile","")
 names,param_path,perr=param_names(params)
 crop,crop_status=surface_crop(nml)
 final_year=start+elapsed-1
 shares,status,pftpath=pft_history(site,case,final_year,names)
 row={"Site":site,"ObservedIGBP":igbp,"Case":case,
      "FrozenArchivedElapsedYears":elapsed,"FinalModelCalendarYear":final_year,
      "FATESParamfile":param_path,"FATESParamStatus":perr,
      "EffectiveSurfaceCropPercent":crop,"SurfaceCropInterpretation":crop_status,
      "FATESVEGCPFstatus":status,"FATESVEGCPFhistory":pftpath,
      "DominantPFT":"","DominantVegCShare_pct":"","MatchingBroadPFTVegCShare_pct":"",
      "ReviewStatus":"REQUIRES_HUMAN_SCIENCE_REVIEW",
      **{f"FLAG_{k}":v for k,v in flags.items()}}
 long=[]
 if shares is not None:
  i=int(np.argmax(shares))
  row["DominantPFT"]=names[i]
  row["DominantVegCShare_pct"]=float(shares[i])
  if igbp in ("ENF","DBF"):
   row["MatchingBroadPFTVegCShare_pct"]=float(sum(v for name,v in zip(names,shares) if name in EXPECTED[igbp]))
   row["ReviewStatus"]="BROAD_PFT_MATCH" if names[i] in EXPECTED[igbp] else "BROAD_PFT_MISMATCH"
  elif igbp=="GRA":
   row["ReviewStatus"]="GRASS_PFT_PRESENT_REQUIRES_SITE_REVIEW" if names[i] in EXPECTED["GRA"] else "NON_GRASS_PFT_AT_GRASS_SITE"
  elif igbp=="MF":
   row["ReviewStatus"]="MIXED_FOREST_REQUIRES_COMPOSITION_DATA"
  for i,(name,v) in enumerate(zip(names,shares)):
   long.append({"Site":site,"PFTSlot":i+1,"FATESPFTName":name,"FinalYearVegCShare_pct":float(v),
                "Meaning":"PFT share of living vegetation carbon; NOT fraction of land area"})
 else:
  row["ReviewStatus"]="NO_VERIFIED_MODEL_PFT_COMPOSITION"
 if igbp=="GRA" and site=="GL-ZaH":
  row["SiteSpecificCaution"]="High Arctic tundra heath; generic grass classification not enough"
 elif igbp=="MF":
  row["SiteSpecificCaution"]="Mixed forest needs tree mix/fractions from site inventory"
 else:
  row["SiteSpecificCaution"]=""
 return row,long

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--preflight",action="store_true")
 parser.add_argument("--run",action="store_true")
 parser.add_argument("--sites",nargs="+",choices=list(SITES),default=list(SITES))
 args=parser.parse_args()
 if args.run==args.preflight:parser.error("specify exactly one of --preflight or --run")
 rows=[];long=[];errors=[]
 for site in args.sites:
  try:
   row,pft=one(site)
   rows.append(row);long.extend(pft)
   print(f"{site:7s} {row['ObservedIGBP']:3s} "
         f"model={row['DominantPFT'] or 'UNKNOWN':43s} "
         f"VegCshare={str(row['DominantVegCShare_pct'])[:7]:7s} "
         f"status={row['ReviewStatus']}",flush=True)
  except Exception as e:
   errors.append({"site":site,"error":str(e)})
   print("FAILED",site,type(e).__name__,e,flush=True)
 if args.preflight:
  print(f"READ_ONLY_PREFLIGHT rows={len(rows)}, failures={len(errors)}; no files written")
  return
 RESULT.mkdir(parents=True,exist_ok=True)
 dest=RESULT/(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_site_PFT_evidence")
 dest.mkdir(exist_ok=False)
 def csvout(name,items):
  if not items:return
  with (dest/name).open("w",newline="") as out:
   writer=csv.DictWriter(out,fieldnames=list(items[0]))
   writer.writeheader();writer.writerows(items)
 csvout("15_site_actual_FATES_PFT_audit.csv",rows)
 csvout("15_site_PFT_vegetation_carbon_shares.csv",long)
 (dest/"PROVENANCE.json").write_text(json.dumps({
  "at_utc":datetime.now(timezone.utc).isoformat(),"sources":"CaseDocs/lnd_in, actual fates_paramfile, effective fsurdat and frozen-year archived h0a",
  "results":len(rows),"failures":errors,
  "limitations":["Not a land-cover fraction: FATES_VEGC_PF measures relative living vegetation carbon.",
    "No FATES_VEGC_PF means unknown PFT outcome, not absence of PFT.",
    "GRA/forest classification does not establish species identity or land-cover fraction.",
    "PCT_CROP is CLM host surface only; check whether a crop landunit exists in actual model.",
    "No output or case modified. Fixed-PFT case creation is a separate experiment."]
 },indent=2)+"\n")
 print("SAVED",dest,flush=True)
 if errors:sys.exit(2)

if __name__=="__main__":main()

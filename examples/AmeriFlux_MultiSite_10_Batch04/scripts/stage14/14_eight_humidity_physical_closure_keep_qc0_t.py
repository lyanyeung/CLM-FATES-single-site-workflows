#!/usr/bin/env python3
"""Batch04 Stage14: create eight corrected VPD/RH candidates, keeping ALL tower TA_QC0.

Fix humidity physics only for the eight precise Stage12 last-HOLD records,
using independently downloaded and SHA-validated ERA5-Land humidity at the
original BIF local-standard time. The source tower TA, PA and original QC
columns remain completely unchanged. All 8 temperature SCIENCE HOLDS remain
open; a numerical VPD correction is NOT proof of temperature correctness.
Never edit old candidate directories, originals, CIME, DATM or Slurm.
Run --self-test, --check (read-only), --apply (new full derived CSVs).
Requires Stage10 helper Python script beside this script.
"""
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
BASE=EXP/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
SOURCE_EXPECT={
 ("US-SP1","200010091800"):(-6.9,4.894,101.332,"1"),
 ("US-SP1","200010091830"):(-7.1,4.927,101.357,"1"),
 ("US-SP1","200710151730"):(11.15,14.025,100.659,"2"),
 ("US-SP1","200801160800"):(-8.211,6.148,101.2,"1"),
 ("US-SP1","200801160830"):(-4.365,6.597,101.185,"1"),
 ("US-SP1","200802030800"):(-3.613,4.717,101.422,"1"),
 ("US-SRG","201903191200"):(0.718,17.133,87.368,"2"),
 ("US-Seg","201612271800"):(0.015,7.037,84.619,"2")
}
SITE_ROWS={"US-SP1":368208,"US-SRG":315600,"US-Seg":333120}
STATUS="NEIGHBOUR_OR_GRID_TEMPERATURE_NOT_CONFIRMED"

def regular(p):
 if p.is_symlink() or not p.is_file():raise ValueError("Missing/symlink source "+str(p))
 return p
def sha(p):
 h=hashlib.sha256()
 with regular(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def r_csv(p,sep=","):
 with regular(p).open(encoding="utf-8-sig",newline="") as f:
  r=csv.DictReader(f,delimiter=sep)
  if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
   raise ValueError("Malformed CSV header "+str(p))
  return list(r)
def w_csv(p,fields,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  wr=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
  wr.writeheader();wr.writerows(rows)
def num(x):
 try:v=float(x)
 except (ValueError,TypeError):return None
 return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
def fmt(x):return "%.12g"%x
def es(t):
 return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -80<=t<=65 else None
def get_exact(path,requested,expected_rows):
 values={};n=0
 with regular(path).open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  columns={"TIMESTAMP_START","TA_F","TA_F_QC","PA_F","VPD_F","VPD_F_QC"}
  if not rd.fieldnames or not columns.issubset(rd.fieldnames):raise ValueError("Missing FLUXMET fields")
  for r in rd:
   n+=1
   k=r["TIMESTAMP_START"]
   if k in requested:
    if k in values:raise ValueError("Duplicate HH timestamp")
    values[k]=r
 if n!=expected_rows or set(values)!=set(requested):raise ValueError("Source row count/time mismatch")
 return values
def helper():
 p=Path(__file__).resolve().with_name("10_era5land_independent_humidity_fill.py")
 if p.is_symlink() or not p.is_file():raise ValueError("Stage10 helper needed alongside Stage14")
 spec=importlib.util.spec_from_file_location("stage14_pinned_stage10",str(p))
 ext=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(ext)
 return ext
def grid_t(grid,utc):
 i_float=(utc-grid["start_utc"]).total_seconds()/3600
 i=math.floor(i_float);fraction=i_float-i
 a=grid["values"]["t2m"]
 if i<0 or i+1>=len(a):return None
 t0=float(a[i])-273.15;t1=float(a[i+1])-273.15
 if not all(math.isfinite(t) for t in (t0,t1)):return None
 return (1-fraction)*t0+fraction*t1
def preflight():
 receipt=json.loads(regular(BASE/"stage12_receipt.json").read_text(encoding="utf-8"))
 if (receipt.get("successfully_resolved")!=148 or receipt.get("unresolved")!=8 or
     receipt.get("target_unique_non_Syv_events")!=156 or
     receipt.get("Postv5_approved") is not False):
  raise ValueError("Expected last 148/156 Stage12 baseline")
 decisions=r_csv(BASE/"stage12_science_decisions.tsv","\t")
 problems={(r["site"],r["TIMESTAMP_START"]):r for r in decisions if not r["status"].startswith("RESOLVED")}
 if len(decisions)!=156 or set(problems)!=set(SOURCE_EXPECT) or any(r["status"]!=STATUS for r in problems.values()):
  raise ValueError("Eight unresolved native-event contract changed")
 manifest=r_csv(BASE/"stage12_repaired_source_candidates.tsv","\t")
 if len(manifest)!=10 or len({r["site"] for r in manifest})!=10:
  raise ValueError("Expected ten current Batch04 source selections")
 if sha(BASE/"stage12_repaired_source_candidates.tsv")!=receipt["receipt_sha256"]["stage12_repaired_source_candidates.tsv"]:
  raise ValueError("Stage12 original ten-site manifest receipt differs")
 indexed={r["site"]:r for r in manifest}
 ext=helper();fixes={};points=receipt["original_native_BIF_points"];grid_cache={}
 for site,n in SITE_ROWS.items():
  source=Path(indexed[site]["source_path"])
  if (int(indexed[site]["rows"])!=n or sha(source)!=indexed[site]["source_SHA256"]):
   raise ValueError("Stage12 full source SHA/rows mismatch "+site)
  wanted={k for s,k in SOURCE_EXPECT if s==site}
  raw=get_exact(source,wanted,n)
  point=points[site]
  if sha(Path(point["BIF_file"]))!=point["BIF_sha256"]:
   raise ValueError("BIF fingerprint differs "+site)
  for year in {int(k[:4]) for k in wanted}:
   file=ext.response_receipt(site,year)
   if file is None:raise ValueError("Grid data absent for "+site+" "+str(year))
   grid_cache[site,year]=(ext.grid_read(file,year,point),sha(file))
  for key in sorted(wanted):
   r=raw[key];t,oldv,pa,qc=SOURCE_EXPECT[site,key]
   if (r["TA_F_QC"].strip()!="0" or r["VPD_F_QC"].strip()!=qc or
      any(num(r[field]) is None for field in ("TA_F","VPD_F","PA_F")) or
      abs(num(r["TA_F"])-t)>0.002 or abs(num(r["VPD_F"])-oldv)>0.002 or
      abs(num(r["PA_F"])-pa)>0.002):
    raise ValueError("Source no longer matches Stage13 original observations "+site+" "+key)
   saturation=es(t)
   if saturation is None or not oldv>saturation:raise ValueError("Source target no longer supersaturated")
   if not 65<=pa<=110:raise ValueError("Invalid tower pressure")
   utc=ext.local_to_utc(key,point["offset_hours"])
   grid,gsha=grid_cache[site,int(key[:4])]
   rh=ext.rh_hour(grid,utc)
   gt=grid_t(grid,utc)
   if rh is None or gt is None or not 1<=rh<=100:
    raise ValueError("Independent hourly ERA grid input invalid")
   v=saturation*(1-rh/100)
   if not 0<=v<=saturation or abs(100*(1-v/saturation)-rh)>1e-8:
    raise ValueError("VPD-RH source closure failure")
   fixes[site,key]={"site":site,"TIMESTAMP_START":key,"TA_F_retained_C":t,
                     "old_VPD_hPa":oldv,"new_VPD_hPa":v,
                     "RH_water_pct":rh,"ERA5Land_T2m_C":gt,
                     "T_tower_minus_ERA_C":t-gt,"original_TA_QC":"0",
                     "original_VPD_QC":qc,"PA_retained_kPa":pa,
                     "matched_UTC":utc.isoformat(),"ERA_source_sha256":gsha,
                     "temperature_science_status":"HOLD_QC0_TOWER_TEMPERATURE_CONFLICT",
                     "humidity_status":"PHYSICAL_CLOSURE_CANDIDATE_ONLY"}
 if len(fixes)!=8:raise ValueError("Missing eight exact repaired humidity targets")
 return manifest,fixes
def new_file(source,dest,updates,expected):
 n=0;updated=set()
 with regular(source).open(encoding="utf-8-sig",newline="") as fi,dest.open("x",encoding="utf-8",newline="") as fo:
  rd=csv.DictReader(fi)
  if not rd.fieldnames:raise ValueError("Source has no header")
  names=list(rd.fieldnames)
  if "RH" not in names:names.append("RH")
  w=csv.DictWriter(fo,fieldnames=names);w.writeheader()
  for r in rd:
   n+=1;key=r["TIMESTAMP_START"]
   if key in updates:
    if key in updated:raise ValueError("Repeated repair time")
    updated.add(key)
    r["VPD_F"]=fmt(updates[key]["new_VPD_hPa"])
    r["RH"]=fmt(updates[key]["RH_water_pct"])
   w.writerow(r)
 if n!=expected or updated!=set(updates):raise ValueError("Derived complete file verification failed")
 return {"path":str(dest),"sha256":sha(dest),"rows":n,"repaired_humidity_times":len(updated)}
def selftest():
 assert len(SOURCE_EXPECT)==8 and len(SITE_ROWS)==3
 assert abs(es(0)-6.112)<1e-9
 assert 0<es(-7)<es(0)
 assert abs(es(10)*.5-(es(10)*(1-50/100)))<1e-9
 print("STAGE14 SELF-TEST PASS: 8 exact supersaturation times; QC0 temperature preserved")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 group=p.add_mutually_exclusive_group(required=True)
 for option in ("self-test","check","apply"):group.add_argument("--"+option,action="store_true")
 args=p.parse_args()
 selftest()
 if args.self_test:return
 manifest,fixes=preflight()
 for key in sorted(fixes):
  f=fixes[key]
  print("STAGE14",f["site"],f["TIMESTAMP_START"],
   "TA_QC0_RETAINED",fmt(f["TA_F_retained_C"]),
   "VPD_OLD",fmt(f["old_VPD_hPa"]),
   "VPD_NEW",fmt(f["new_VPD_hPa"]),
   "RH_ERA",fmt(f["RH_water_pct"]),
   "ERA_T",fmt(f["ERA5Land_T2m_C"]),
   "T_SCIENCE_HOLD",flush=True)
 if args.check:
  print("STAGE14 CHECK ONLY no writes");return
 out=EXP/"qcv5_stage14_humidity_closure_candidate"/(
     "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
 out.mkdir(parents=True,exist_ok=False)
 (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
    "Stage14 humidity numerical closure only; all 8 unresolved tower QC0 temperatures remain scientific HOLDs.\n")
 new_sources=[];files={}
 for original in manifest:
  x=dict(original);site=x["site"]
  if site in SITE_ROWS:
   repairs={k:f for (s,k),f in fixes.items() if s==site}
   path=out/(site+"_Stage14_keep_tower_TA_humidity_candidate.csv")
   files[site]=new_file(Path(x["source_path"]),path,repairs,SITE_ROWS[site])
   x["source_path"]=str(path);x["source_SHA256"]=files[site]["sha256"]
   x["latest_stage"]="STAGE14_HUMIDITY_ONLY_T_SCIENCE_HOLD"
   print("STAGE14 FULL DERIVED",site,files[site],flush=True)
  new_sources.append(x)
 ledger=[{k:fmt(v) if isinstance(v,float) else v for k,v in fixes[key].items()} for key in sorted(fixes)]
 fields=list(ledger[0])
 w_csv(out/"stage14_eight_humidity_candidates.tsv",fields,ledger)
 w_csv(out/"UNRESOLVED_EIGHT_TOWER_TEMPERATURE_HOLDS.tsv",fields,ledger)
 w_csv(out/"stage14_latest_ten_candidate_manifest.tsv",list(new_sources[0]),new_sources)
 receipt={"source_stage12_receipt_sha256":sha(BASE/"stage12_receipt.json"),
          "humidity_physical_candidate_count":8,
          "still_unresolved_tower_temperature_science_hold_count":8,
          "deferred_US_Syv_old_HOLDs":606,
          "source_TA_PA_QC_all_unchanged":True,
          "derived_full_candidate_files":files,
          "latest_ten_manifest_sha256":sha(out/"stage14_latest_ten_candidate_manifest.tsv"),
          "humidity_ledger_sha256":sha(out/"stage14_eight_humidity_candidates.tsv"),
          "Postv5_approved":False,"DATM_ready":False,"spinup":False,
          "timestamp_UTC":datetime.now(timezone.utc).isoformat()}
 (out/"stage14_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("STAGE14 NEW DERIVED FILES",out)
 print("STAGE14 RESULT: 8/8 VPD-RH physical closure candidates; 8/8 original TA QC0 scientific HOLDs remain")
 print("NO ORIGINAL OR STAGE07-13 SOURCE, DATM, CIME OR SLURM WRITES")
if __name__=="__main__":main()

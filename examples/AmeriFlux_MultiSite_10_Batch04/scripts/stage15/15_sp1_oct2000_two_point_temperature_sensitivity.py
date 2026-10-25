#!/usr/bin/env python3
"""Batch04 Stage15: defensible TWO-point temperature sensitivity candidate ONLY.

2000-10-09 US-SP1 tower TA QC0 at 18:00 and 18:30 is -6.9/-7.1 C,
while immediately flanking tower 17:30 = 11.0 C QC0, 19:00 = 17.545 C QC1,
and independent ERA5-Land 18:00/18:30 about 14.37/13.78 C.
Check flanks, neighboring temporal context, timestamp-correct grid evidence,
and source SHA BEFORE presenting a 2-point linear interpolation candidate.
Recompute VPD from retained Stage14 independent ERA5-Land RH at new TA.

--assess reads without writing; --trial creates ONE complete independent
US-SP1 sensitivity CSV (not approved) and 10-site candidate manifest.
Original FLUXMET, Stage05-14, other nine sites, DATM/CIME untouched.
Original TA_QC0 becomes QC1 only IN THIS ALTERNATIVE trial and is recorded
in a separate immutable provenance ledger: gapfilled != observed.
All eight original temperature-science disputes REMAIN open.
Requires pinned Stage10 helper beside this script; no CDS download.
"""
import argparse,csv,hashlib,importlib.util,json,math
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S14=ROOT/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
S12=ROOT/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
SITE="US-SP1"
TARGETS=("200010091800","200010091830")
CLOCK={"latitude":29.7381,"longitude":-82.2188,"offset_hours":-5}
SOURCE_SHA="3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806"
EXPECTED_ROWS=368208
def regular(p):
 if p.is_symlink() or not p.is_file():raise ValueError("Missing/non-regular file "+str(p))
 return p
def sha(p):
 h=hashlib.sha256()
 with regular(p).open("rb") as f:
  for b in iter(lambda:f.read(4<<20),b""):h.update(b)
 return h.hexdigest()
def numeric(s):
 try:x=float(s)
 except (TypeError,ValueError):return None
 return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
def es(t):return 6.112*math.exp(17.67*t/(t+243.5))
def helper():
 p=Path(__file__).resolve().with_name("10_era5land_independent_humidity_fill.py")
 if not p.is_file():raise ValueError("Download pinned Stage10 helper next to this script")
 spec=importlib.util.spec_from_file_location("b04_stage15_ext",str(p))
 a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 return a
def read_window(file):
 want={"200010091630","200010091700","200010091730",
       "200010091800","200010091830",
       "200010091900","200010091930","200010092000"}
 rows={};n=0
 with regular(file).open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","RH","PA_F"}.issubset(rd.fieldnames):
   raise ValueError("Stage14 US-SP1 columns changed")
  for row in rd:
   n+=1
   k=row["TIMESTAMP_START"]
   if k in want:
    if k in rows:raise ValueError("Duplicate tower timestamp "+k)
    rows[k]=row
 if n!=EXPECTED_ROWS or set(rows)!=want:
  raise ValueError("Source row census or tower +/-window mismatch")
 return rows
def pin(rec,manifest):
 if rec.get("humidity_physical_candidate_count")!=8 or rec.get("still_unresolved_tower_temperature_science_hold_count")!=8:
  raise ValueError("Stage14 science HOLD count changed")
 if sha(S14/"stage14_latest_ten_candidate_manifest.tsv")!=rec["latest_ten_manifest_sha256"]:
  raise ValueError("Stage14 manifest mutated")
 with regular(manifest).open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f,delimiter="\t");r=list(rd)
 if len(r)!=10 or len({x["site"] for x in r})!=10:
  raise ValueError("Expected ten newest source files")
 entry=next((x for x in r if x["site"]==SITE),None)
 if entry is None or int(entry["rows"])!=EXPECTED_ROWS:
  raise ValueError("Expected latest source rows for US-SP1")
 source=Path(entry["source_path"])
 if (source.parent!=S14 or
     entry["source_SHA256"]!=SOURCE_SHA or
     sha(source)!=SOURCE_SHA):
  raise ValueError("Stage14 US-SP1 source SHA does not match pinned result")
 return r,source
def preflight():
 receipt=json.loads(regular(S14/"stage14_receipt.json").read_text())
 manifest=S14/"stage14_latest_ten_candidate_manifest.tsv"
 rows,source=pin(receipt,manifest)
 window=read_window(source)
 def check(k,t,qc):
  a=window[k]
  actual=numeric(a["TA_F"])
  if actual is None or abs(actual-t)>.002 or a["TA_F_QC"].strip()!=qc:
   raise ValueError("Original native tower source or QC changed "+k)
 check("200010091730",11.0,"0")
 check("200010091900",17.545,"1")
 check("200010091800",-6.9,"0")
 check("200010091830",-7.1,"0")
 for key,t,qc in (
 ("200010091630",14.0,"0"),("200010091700",12.6,"0"),
 ("200010091930",17.541,"1"),("200010092000",17.536,"1")):
  check(key,t,qc)
 left=numeric(window["200010091730"]["TA_F"])
 right=numeric(window["200010091900"]["TA_F"])
 if right-left>8 or abs(right-left)>8:
  raise ValueError("Tower boundary thermal spread too wide")
 sourceclock=json.loads(regular(S12/"stage12_receipt.json").read_text())["original_native_BIF_points"][SITE]
 if any(abs(sourceclock[k]-CLOCK[k])>1e-4 for k in CLOCK):
  raise ValueError("Stage12 verified BIF station point changed")
 if sha(Path(sourceclock["BIF_file"]))!=sourceclock["BIF_sha256"]:
  raise ValueError("Original BIF SHA mismatch")
 external=helper()
 file=external.response_receipt(SITE,2000)
 if file is None:raise ValueError("Already verified 2000 independent ERA year missing")
 grid=external.grid_read(file,2000,sourceclock)
 modifications={}
 for i,k in enumerate(TARGETS,1):
  new_t=left+(right-left)*i/3
  r=window[k]
  old_t=numeric(r["TA_F"])
  rh=numeric(r["RH"])
  if rh is None or not 1<=rh<=100:
   raise ValueError("Stage14 independent humidity missing")
  utc=external.local_to_utc(k,sourceclock["offset_hours"])
  era_t=grid["values"]["t2m"]
  p=(utc-grid["start_utc"]).total_seconds()/3600
  j=math.floor(p);frac=p-j
  if not 0<=j<len(era_t)-1:raise ValueError("Independent ERA exact native time not sampled")
  temp=(float(era_t[j])*(1-frac)+float(era_t[j+1])*frac)-273.15
  if abs(new_t-temp)>2.5:
   raise ValueError("Two-sided tower interpolation disagrees with ERA >2.5 C")
  if abs(new_t-old_t)<15:
   raise ValueError("Original point is not grossly inconsistent with flank interpolation")
  v=es(new_t)*(1-rh/100)
  if not 0<=v<=es(new_t):raise ValueError("Source VPD/RH physical closure failed")
  modifications[k]={
   "original_TA_C":old_t,"new_TA_C":new_t,
   "original_VPD_hPa":numeric(r["VPD_F"]),"new_VPD_hPa":v,
   "ERA5Land_RH_pct":rh,"ERA5Land_T_C":temp,
   "flank_left_T_C":left,"flank_right_T_C":right,
   "old_TA_F_QC":"0","new_TA_F_QC":"1",
   "provenance":"EXPERIMENTAL_FLANK_INTERPOLATION_PLUS_ERA5LAND_T_CHECK"}
 return rows,source,modifications
def make_full(source,dest,mods):
 n=0;times=set()
 with regular(source).open(encoding="utf-8-sig",newline="") as a,dest.open("x",encoding="utf-8",newline="") as b:
  rd=csv.DictReader(a);cols=list(rd.fieldnames or ())
  if not cols:raise ValueError("No source CSV columns")
  wr=csv.DictWriter(b,fieldnames=cols);wr.writeheader()
  for row in rd:
   n+=1;k=row["TIMESTAMP_START"]
   if k in mods:
    if k in times:raise ValueError("Duplicate target time")
    times.add(k)
    row["TA_F"]="%.12g"%mods[k]["new_TA_C"]
    row["VPD_F"]="%.12g"%mods[k]["new_VPD_hPa"]
    row["TA_F_QC"]="1"
   wr.writerow(row)
 if n!=EXPECTED_ROWS or times!=set(TARGETS):
  raise ValueError("Failed complete full-file materialization")
 return {"rows":n,"modified_TA_VPD_half_hours":len(times),"sha256":sha(dest),"path":str(dest)}
def selftest():
 assert len(TARGETS)==2
 assert abs((11+(17.545-11)/3)-13.181666666666667)<1e-10
 assert abs((11+2*(17.545-11)/3)-15.363333333333333)<1e-10
 assert es(14)>es(-7)
 print("STAGE15 SELF-TEST PASS: strict 2 HH isolate, original QC0 provenance to trial QC1")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument("--self-test",action="store_true")
 g.add_argument("--assess",action="store_true")
 g.add_argument("--trial",action="store_true")
 args=p.parse_args()
 selftest()
 if args.self_test:return
 rows,source,changes=preflight()
 for key,c in changes.items():
  print("STAGE15 SP1 TEMP SENSITIVITY",key,
        "old_TA",round(c["original_TA_C"],3),
        "trial_TA",round(c["new_TA_C"],3),
        "ERA_T",round(c["ERA5Land_T_C"],3),
        "trial_VPD",round(c["new_VPD_hPa"],4),
        "TA_QC:0->1",flush=True)
 if args.assess:
  print("STAGE15 ASSESS ONLY: no writes, science holds remain");return
 dest=ROOT/"qcv5_stage15_sp1_two_point_temperature_sensitivity"/(
   "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
 dest.mkdir(parents=True,exist_ok=False)
 (dest/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
 "Only SP1 2-point experimental temperature alternative; eight Stage14 temperature disputes and US-Syv holds remain unapproved.\n")
 out=dest/"US-SP1_Stage15_alternative_two_TA_times_FLUXMET_HH.csv"
 result=make_full(source,out,changes)
 newrows=[]
 for entry in rows:
  e=dict(entry)
  if e["site"]==SITE:
   e["source_path"]=str(out);e["source_SHA256"]=result["sha256"]
   e["latest_stage"]="STAGE15_ALTERNATIVE_SENSITIVITY_NOT_APPROVED"
  newrows.append(e)
 fields=list(newrows[0])
 with (dest/"STAGE15_ALTERNATIVE_LATEST_TEN_MANIFEST.tsv").open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter="\t");w.writeheader();w.writerows(newrows)
 ledger=dest/"STAGE15_TWO_POINT_SCIENCE_PROVENANCE.tsv"
 with ledger.open("x",encoding="utf-8",newline="") as f:
  entries=[{"site":SITE,"TIMESTAMP_START":k,**v} for k,v in changes.items()]
  w=csv.DictWriter(f,fieldnames=list(entries[0]),delimiter="\t")
  w.writeheader();w.writerows(entries)
 receipt={
  "stage14_input_receipt_sha256":sha(S14/"stage14_receipt.json"),
  "stage14_input_full_sp1_sha256":SOURCE_SHA,
  "source_stage14_original_temperature_HOLD_count":8,
  "source_deferred_US_Syv_original_HOLD_count":606,
  "two_temperature_alternative_candidates":2,
  "remaining_unapproved_science_holds":8,
  "full_trial":result,"manifest_sha256":sha(dest/"STAGE15_ALTERNATIVE_LATEST_TEN_MANIFEST.tsv"),
  "provenance_SHA256":sha(ledger),
  "Postv5_approved":False,"DATM_ready":False,"spinup":False,
  "created_utc":datetime.now(timezone.utc).isoformat()}
 (dest/"stage15_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("STAGE15 ALTERNATIVE TWO-POINT FULL SOURCE",out)
 print("STAGE15 RESULT: 2 proposed TA/VPD changes; 8 QC0 temperature science holds remain; NO DATM/CIME")
if __name__=="__main__":main()

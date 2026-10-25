#!/usr/bin/env python3
"""Batch05 Stage10: REPORT-ONLY 1750 event manual humidity QC review ledger.

SHA-validate original tower CSVs. Export every computed-RH<1% native event
with source/QC, ERA/MDS candidate physics and physical independent measured
QC0/QC0 neighbor anchors within +/-3 h. A bracketed interpolation is a
UNAPPROVED DIAGNOSTIC, never an automatic repair. No original/forcing writes.
"""
import argparse, csv, hashlib, io, json, math, os, re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT=Path(os.getenv("FLUXNET_SITES_ROOT","/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
SITES={"US-UiD":"2008-2024_v1.3_r1","US-UMB":"FULLSET_2007-2021_3-5",
 "US-UMd":"2007-2025_v1.3_r1","US-Var":"2000-2025_v1.3_r1",
 "US-Vcm":"2007-2025_v1.3_r1","US-Vcp":"2007-2025_v1.3_r1",
 "US-WCr":"1999-2025_v1.3_r1","US-Whs":"2007-2025_v1.3_r1",
 "US-Wjs":"2007-2025_v1.3_r1","US-Wkg":"2004-2025_v1.3_r1"}
SHA={"US-UiD":"130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318",
"US-UMB":"ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6",
"US-UMd":"e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2",
"US-Var":"664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2",
"US-Vcm":"c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c",
"US-Vcp":"eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42",
"US-WCr":"f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506",
"US-Whs":"653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca",
"US-Wjs":"9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6",
"US-Wkg":"f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"}
COL=("TIMESTAMP_START","TA_F","VPD_F","RH","TA_F_QC","VPD_F_QC",
 "TA_F_MDS","VPD_F_MDS","TA_F_MDS_QC","VPD_F_MDS_QC","TA_ERA","VPD_ERA")
FIELDS=("time","class","RH_derived_pct","RH_original_pct","TA_F_C","VPD_F_hPa",
"TA_F_QC","VPD_F_QC","TA_MDS_C","VPD_MDS_hPa","TA_MDS_QC","VPD_MDS_QC",
"TA_ERA_C","VPD_ERA_hPa","MDS_pair_physics","ERA_pair_physics",
"hypothetical_ERA_e_with_tower_T_vpd_hPa","left_measured_anchor_time",
"left_measured_anchor_vpd","right_measured_anchor_time",
"right_measured_anchor_vpd","interpolated_measured_vpd_hPa",
"interpolation_diagnostic","SCIENCE_APPROVAL")
WINDOW=timedelta(hours=3)

def number(raw):
 try:
  n=float(raw)
  return n if math.isfinite(n) and n not in (-9999.0,-6999.0) else None
 except (ValueError,TypeError): return None

def es(t):
 return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -80<=t<=60 else None

def physics(t,v):
 s=es(t)
 if s is None or v is None: return "MISSING"
 return "FEASIBLE" if 0<=v<=s else "NONPHYSICAL"

def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""): h.update(chunk)
 return h.hexdigest()

def source(root,site):
 release="AMF_"+site+"_FLUXNET_"+SITES[site]
 folder=root/site/"forcing"/"raw"/release
 if not folder.is_dir() or folder.is_symlink(): raise ValueError("missing/nonregular site source directory "+str(folder))
 kind="FULLSET" if site=="US-UMB" else "FLUXMET"
 pat=re.compile("AMF_"+re.escape(site)+"_FLUXNET_"+kind+r"_(HH|HR)_.+[.]csv",re.I)
 candidates=[p for p in folder.iterdir() if pat.fullmatch(p.name)]
 if len(candidates)!=1 or candidates[0].is_symlink() or not candidates[0].is_file():
  raise ValueError("native source missing or ambiguous for "+site)
 p=candidates[0]
 actual=digest(p)
 if actual!=SHA[site]: raise ValueError("source SHA256 mismatch "+site+" "+actual)
 return p

def triage(stream):
 rows=csv.DictReader(stream); columns=rows.fieldnames or []
 if len(columns)!=len(set(columns)) or not set(COL).issubset(columns):
  raise ValueError("missing original TA/VPD/QC/MDS/ERA source columns")
 events=[]; counts=Counter(); pending=[]; prior_anchor=None; previous=None; total=0
 for total,row in enumerate(rows,1):
  if None in row or any(val is None for val in row.values()):
   raise ValueError("malformed native input row "+str(total))
  label=row["TIMESTAMP_START"]
  if not re.fullmatch(r"\d{12}",label): raise ValueError("bad timestamp "+repr(label))
  time=datetime.strptime(label,"%Y%m%d%H%M")
  if previous is not None and time-previous!=timedelta(minutes=30):
   raise ValueError("native HH chronology broken at "+label)
  previous=time
  n={k:number(row[k]) for k in
   ("TA_F","VPD_F","RH","TA_F_MDS","VPD_F_MDS","TA_ERA","VPD_ERA")}
  ta,vpd,rh=n["TA_F"],n["VPD_F"],n["RH"]
  sat=es(ta)
  rh_calc=(100*(1-vpd/sat) if sat is not None and vpd is not None else None)
  tq,vq=row["TA_F_QC"].strip(),row["VPD_F_QC"].strip()
  tmq,vmq=row["TA_F_MDS_QC"].strip(),row["VPD_F_MDS_QC"].strip()
  if tq not in ("0","1","2") or vq not in ("0","1","2"):
   raise ValueError("unexpected F QC at "+label)
  if tmq not in ("0","1","2","3","-9999") or vmq not in ("0","1","2","3","-9999"):
   raise ValueError("unexpected MDS QC at "+label)
  # Anchors require both variables measured and a physical source pair.
  # Original RH is not assumed independent, but reject discordant values.
  anchor=(tq=="0" and vq=="0" and rh_calc is not None and 1<=rh_calc<=100 and
   (rh is None or 0<=rh<=100 and abs(rh-rh_calc)<=5))
  if anchor:
   for event in pending:
    if time-event["_time"]<=WINDOW:
     event["right_measured_anchor_time"]=label
     event["right_measured_anchor_vpd"]=vpd
     event["_right"]=time
   pending=[]
   prior_anchor=(time,label,vpd)
  if rh_calc is None or rh_calc>=1: continue
  category="NEGATIVE" if rh_calc<0 else "NONNEGATIVE_UNDER_1PCT"
  counts["events"]+=1; counts[category]+=1
  counts["QC_"+tq+"/"+vq]+=1
  ms=physics(n["TA_F_MDS"],n["VPD_F_MDS"])
  era_self=physics(n["TA_ERA"],n["VPD_ERA"])
  era_sat=es(n["TA_ERA"])
  trial=None
  if era_self=="NONPHYSICAL": estate="ERA_INTERNAL_NONPHYSICAL"
  elif era_self=="MISSING" or sat is None: estate="ERA_MISSING"
  else:
   e=era_sat-n["VPD_ERA"]
   if 0<=e<=sat:
    trial=sat-e
    estate="HYPOTHETICAL_ERA_VAPOUR_PAIR_FEASIBLE"
   else: estate="ERA_E_WITH_TOWER_T_NOT_FEASIBLE"
  counts["MDS_"+ms]+=1; counts[estate]+=1
  ev=dict(zip(FIELDS,[""]*len(FIELDS)))
  ev.update(time=label, **{"class":category},
   RH_derived_pct=round(rh_calc,7),RH_original_pct=rh,
   TA_F_C=ta,VPD_F_hPa=vpd,TA_F_QC=tq,VPD_F_QC=vq,
   TA_MDS_C=n["TA_F_MDS"],VPD_MDS_hPa=n["VPD_F_MDS"],
   TA_MDS_QC=tmq,VPD_MDS_QC=vmq,TA_ERA_C=n["TA_ERA"],
   VPD_ERA_hPa=n["VPD_ERA"],MDS_pair_physics=ms,
   ERA_pair_physics=estate,
   hypothetical_ERA_e_with_tower_T_vpd_hPa=(round(trial,7) if trial is not None else ""),
   SCIENCE_APPROVAL="HOLD_NOT_APPROVED",_time=time)
  if prior_anchor is not None and time-prior_anchor[0]<=WINDOW:
   ev["left_measured_anchor_time"]=prior_anchor[1]
   ev["left_measured_anchor_vpd"]=prior_anchor[2]
   ev["_left"]=prior_anchor[0]
  events.append(ev);pending.append(ev)
 if total==0: raise ValueError("empty original native CSV")
 for ev in events:
  left,right=ev.get("_left"),ev.get("_right")
  if left is None or right is None or right<=left:
   ev["interpolation_diagnostic"]="NO_BOTH_QC0_ANCHORS_WITHIN_3H"
  else:
   f=(ev["_time"]-left)/(right-left)
   v=float(ev["left_measured_anchor_vpd"])+f*(
    float(ev["right_measured_anchor_vpd"])-float(ev["left_measured_anchor_vpd"]))
   if physics(ev["TA_F_C"],v)=="FEASIBLE":
    ev["interpolated_measured_vpd_hPa"]=round(v,7)
    ev["interpolation_diagnostic"]="UNAPPROVED_MATH_FEASIBLE"
   else: ev["interpolation_diagnostic"]="INTERPOLATION_NONPHYSICAL"
  counts[ev["interpolation_diagnostic"]]+=1
  for key in ("_time","_left","_right"): ev.pop(key,None)
 return events,dict(counts)

def selftest():
 rows=[
 "202001010000,10,2,83.71,0,0,10,2,0,0,10,2",
 "202001010030,10,14,-9999,0,1,10,14,0,1,10,2",
 "202001010100,10,2,83.71,0,0,10,2,0,0,10,2",
 "202001010130,-14.254,2.387,89.08,2,2,-10.306,2.237,2,2,-14.254,2.387",
 "202001010200,10,2,83.71,0,0,10,2,0,0,10,2",
 "202001010230,10,12.27,0.99,0,0,10,12.27,0,0,10,2"]
 data=",".join(COL)+"\n"+"\n".join(rows)+"\n"
 events,c=triage(io.StringIO(data))
 assert len(events)==3
 assert c["NEGATIVE"]==2 and c["NONNEGATIVE_UNDER_1PCT"]==1
 assert events[0]["interpolation_diagnostic"]=="UNAPPROVED_MATH_FEASIBLE"
 assert events[1]["ERA_pair_physics"]=="ERA_INTERNAL_NONPHYSICAL"
 assert events[2]["interpolation_diagnostic"]=="NO_BOTH_QC0_ANCHORS_WITHIN_3H"
 print("STAGE10 SELF-TEST PASS | original QC0 anchors, bracketed trial, ERA physics, report only")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--sites-root",type=Path,default=ROOT)
 p.add_argument("--output-dir",type=Path)
 p.add_argument("--sites",nargs="+",choices=list(SITES))
 args=p.parse_args()
 if args.self_test: selftest();return 0
 if args.output_dir is None: p.error("--output-dir required; new reports-only path")
 selected=args.sites or list(SITES)
 if len(set(selected))!=len(selected):p.error("duplicate sites")
 root=args.sites_root.expanduser().resolve()
 out=args.output_dir.expanduser().resolve()
 if out==root or root in out.parents or out in root.parents:
  p.error("report output must be outside the original forcing source tree")
 if out.exists():p.error("report output exists, refusing overwrite "+str(out))
 paths={s:source(root,s) for s in selected}
 all_events={}; summaries={}; totals=Counter()
 print("STAGE10 original native sources verified before report creation",flush=True)
 for site in selected:
  path=paths[site]
  before=(path.stat().st_size,path.stat().st_mtime_ns)
  with path.open(encoding="utf-8-sig",newline="") as src:
   ev,cnt=triage(src)
  if before!=(path.stat().st_size,path.stat().st_mtime_ns):
   raise ValueError("source changed during read "+site)
  all_events[site]=ev
  summaries[site]={"sha256":SHA[site],"source_csv":path.name,"counts":cnt}
  totals.update(cnt)
  print("STAGE10_REVIEW_ROWS",site,len(ev),flush=True)
 if len(selected)==10 and (totals["events"]!=1750 or totals["NEGATIVE"]!=1559):
  raise ValueError("Stage09 invariant 1750/1559 failed, refusing output")
 if not out.parent.exists():p.error("report parent does not exist "+str(out.parent))
 out.mkdir(exist_ok=False)
 for site in selected:
  with (out/(site+"_low_RH_review.csv")).open("x",encoding="utf-8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(all_events[site])
 meta={"schema":"Batch05 Stage10 report-only","formula":"Magnus water es(T); T degC VPD hPa",
  "clock":"unchanged FLUXNET local standard printed labels",
  "candidate_status":"UNAPPROVED; never write to forcing without further QC",
  "anchor_rule":"both F_QC0, derived RH within 1-100%, original RH if present within 5pp, +/-3h",
  "sites":summaries,"overall":dict(totals)}
 with (out/"audit_summary.json").open("x",encoding="utf-8") as f:
  json.dump(meta,f,indent=2,sort_keys=True)
 print("STAGE10 SUMMARY sites={}/{} events={} negative={} reports={}".format(
  len(selected),len(selected),totals["events"],totals["NEGATIVE"],out))
 print("ONLY REVIEW CSV/JSON WRITTEN; NO ORIGINAL/FORCING/DATM/CASE CHANGES; NO SLURM")
 return 0

if __name__=="__main__":
 raise SystemExit(main())

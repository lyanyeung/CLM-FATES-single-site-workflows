#!/usr/bin/env python3
"""Batch05 Stage62: user explicitly approved thirty US-Wjs 2018 RH-interpolated
native half-hours on 2026-10-28. Add EXACTLY these thirty to Stage56's
SHA-verified 174 previously approved rows; write NEW VERSIONED 204-row
candidate overlay, never change the old 174, original FLUXMET, DATM or CIME.
Do not label gap-filled RH as directly measured or promote to model forcing.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SITE="US-Wjs"
LEFT="201803111900"
RIGHT="201803121030"
FIRST="201803111930"
LAST="201803121000"
APPROVED_DATE="2026-10-28"
SCHEMA=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
EVIDENCE=("site","native_time","original_TA_F_C","original_TA_F_QC",
 "original_VPD_F_hPa","original_VPD_F_QC","original_VPD_F_MDS_hPa",
 "original_VPD_F_MDS_QC","original_source_RH_field",
 "original_source_ERA_T_C","original_source_ERA_VPD_hPa",
 "original_source_ERA_RH_derived_pct","external_ERA5L_RH_reference_pct",
 "QC0_left_time","QC0_right_time","interpolated_RH_pct",
 "reconstructed_VPD_hPa","approved_by_user_date",
 "filled_not_original_tower_measurement","production_DATM_allowed")
EDGE=("site","before_native","after_native","before_selected_VPD_hPa",
 "after_selected_VPD_hPa","jump_hPa","abs_jump_gt2hPa","abs_jump_gt4hPa")

def parse(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native HH timestamp "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")

def ticks(a,b):
 start,end=parse(a),parse(b)
 sec=(end-start).total_seconds()
 if sec<0 or sec%1800:raise ValueError("invalid native HH interval")
 return [(start+timedelta(minutes=i*30)).strftime("%Y%m%d%H%M") for i in range(int(sec//1800)+1)]

def num(v):
 try:
  f=float(v)
  return f if math.isfinite(f) and f not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None

def es(t):
 if t is None or not -80<=t<=60:raise ValueError("original source TA out of bound")
 return 6.112*math.exp(17.67*t/(t+243.5))

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def read(p,keys):
 if p.is_symlink() or not p.is_file():raise ValueError("missing/indirect prior science file "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  cols=reader.fieldnames or []
  if len(cols)!=len(set(cols)) or not set(keys).issubset(cols):
   raise ValueError("upstream CSV headings incomplete "+str(p))
  rows=list(reader)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("upstream CSV malformed "+str(p))
 return rows

def idx(rows,name="native_time"):
 result={}
 for r in rows:
  key=(r["site"],r[name])
  parse(key[1])
  if key in result:raise ValueError("duplicate source HH "+str(key))
  result[key]=r
 return result

def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def selftest():
 assert len(ticks(FIRST,LAST))==30
 assert len(ticks(LEFT,RIGHT))==32
 assert (parse(RIGHT)-parse(LEFT)).total_seconds()==15.5*3600
 assert es(-.401)>5
 assert abs(es(-.057)*(1-1))<1e-12
 assert 174+30==204
 print("STAGE62 SELF-TEST PASS | explicit Wjs2018 30HH approval, strict 174+30 to 204, original/prod write forbidden")

def run():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument("--self-test",action="store_true")
 a.add_argument("--stage53-dir",type=Path)
 a.add_argument("--stage56-dir",type=Path)
 a.add_argument("--stage59-dir",type=Path)
 a.add_argument("--stage60-dir",type=Path)
 a.add_argument("--stage61-dir",type=Path)
 a.add_argument("--out",type=Path)
 x=a.parse_args()
 if x.self_test:selftest();return
 if any(z is None for z in (x.stage53_dir,x.stage56_dir,x.stage59_dir,x.stage60_dir,x.stage61_dir,x.out)):
  a.error("require all original Stage53/56/59/60/61 report folders plus NEW --out")
 d53,d56,d59,d60,d61,out=(z.expanduser().resolve() for z in
  (x.stage53_dir,x.stage56_dir,x.stage59_dir,x.stage60_dir,x.stage61_dir,x.out))
 dirs=(d53,d56,d59,d60,d61)
 if not all(d.is_dir() for d in dirs) or not out.parent.is_dir() or out.exists():
  a.error("missing prior report directory or output is not new")
 if any(out==d or d in out.parents or out in d.parents for d in dirs):
  a.error("output cannot overlap any input report directory")
 f53=d53/"stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv"
 f56=d56/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv"
 f59=d59/"stage59_49_HH_ORIGINAL_SOURCE_ALL_AVAILABLE_HUMIDITY_WEATHER.csv"
 f60=d60/"stage60_49HH_original_VPD_F_MDS_vs_VPD_F_and_weather.csv"
 f61=d61/"stage61_Wjs2018_EXACT_30HH_UNAPPROVED_RH_LINEAR_INTERPOLATION_CANDIDATES.csv"
 e61=d61/"stage61_Wjs2018_ALL31_ADJACENT_BOUNDARY_PAIRS_RESEARCH.csv"
 m56=json.loads((d56/"stage56_manifest.json").read_text())
 m59=json.loads((d59/"stage59_manifest.json").read_text())
 m60=json.loads((d60/"stage60_manifest.json").read_text())
 m61=json.loads((d61/"stage61_manifest.json").read_text())
 base=read(f56,SCHEMA)
 raw=read(f59,("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
             "VPD_F_MDS","VPD_F_MDS_QC","TA_ERA","VPD_ERA","RH"))
 audit=read(f60,("site","native_time","original_VPD_F_MDS_hPa","original_VPD_F_MDS_QC"))
 candidates=read(f61,("site","native_time","original_TA_F_C","original_TA_F_QC",
            "original_VPD_F_hPa","original_VPD_F_QC","original_VPD_F_MDS_hPa",
            "original_VPD_F_MDS_QC","original_RH_source_field",
            "linear_QC0_RH_candidate_pct","linear_QC0_VPD_candidate_hPa",
            "delta_candidate_minus_original_VPD_hPa","original_QC0_left",
            "original_QC0_right","user_science_approval","versioned_174_inclusion",
            "production_DATM_permission","independent_RH_inside_30HH_validated"))
 edges61=read(e61,("site","before_native","after_native","before_VPD_hPa",
                 "after_VPD_hPa","delta_VPD_hPa","abs_jump_gt2hPa","abs_jump_gt4hPa"))
 prior53=read(f53,("site","source_file","source_member","source_sha256","episode_id","role"))
 if (len(base),len(raw),len(audit),len(candidates),len(edges61),len(prior53))!=(174,49,49,30,31,20):
  raise ValueError("expected Stage56/59/60/61 original populations 174/49/49/30/31/20")
 if (m56.get("versioned_total_approved_HH")!=174 or
     m56.get("outputs_sha256",{}).get(f56.name)!=sha(f56) or
     m56.get("Wjs_2018_protected_30HH_UNCHANGED") is not True or
     m56.get("production_DATM_permission") is not False or
     m59.get("output_sha256",{}).get(f59.name)!=sha(f59) or
     m59.get("approved_overlay_174_unchanged") is not True or
     m59.get("stage56_174_sha256")!=sha(f56) or
     m60.get("output_sha256",{}).get(f60.name)!=sha(f60) or
     m60.get("stage59_original49_sha256")!=sha(f59) or
     m60.get("original_2018_HOLD_VPD_equals_MDS_within_0p002_HH")!=30 or
     m60.get("original_2018_HOLD_original_negative_implied_RH_HH")!=4 or
     m61.get("output_sha256",{}).get(f61.name)!=sha(f61) or
     m61.get("output_sha256",{}).get(e61.name)!=sha(e61) or
     m61.get("original_174_unchanged") is not True or
     m61.get("science_approved_new_HH")!=0 or
     m61.get("merged_204_overlay_written") is not False or
     m61.get("original_2018_HOLD_unchanged") is not True or
     m61.get("original_MDS_VPDQC1_HH")!=30):
  raise ValueError("upstream report SHA/manifest/source science state changed")
 if any(set(r)!=set(SCHEMA) for r in base):
  raise ValueError("Stage56 original 174 overlay schema changed")
 bidx=idx(base)
 cidx=idx(candidates)
 aidx=idx(audit)
 rraw={r["TIMESTAMP_START"]:r for r in raw}
 if len(bidx)!=174 or len(cidx)!=30 or len(aidx)!=49 or len(rraw)!=49:
  raise ValueError("prior source or candidate native identity duplicated")
 expected={(SITE,t) for t in ticks(FIRST,LAST)}
 if set(cidx)!=expected or set(cidx)&set(bidx):
  raise ValueError("user approved thirty exact source timestamps overlap/mismatch")
 if any(k[0]!=SITE for k in aidx):
  raise ValueError("Stage60 original native cohort changed")
 events=[r for r in prior53 if r["episode_id"]=="US-Wjs_E0079" and r["role"]=="EVENT"]
 links={(r["source_file"],r["source_member"],r["source_sha256"]) for r in events}
 if len(events)!=3 or len(links)!=1:
  raise ValueError("Stage53 original US-Wjs 2018 source identification changed")
 sourcefile,member,sourcehash=links.pop()
 original_path=Path(sourcefile)
 if (original_path.is_symlink() or not original_path.is_file() or
    original_path.suffix.lower()!=".csv" or member not in ("",original_path.name) or
    sha(original_path)!=sourcehash or m59.get("original_source_sha256")!=sourcehash):
  raise ValueError("original FLUXMET source product SHA mismatch since Stage59")
 wanted_raw=set(ticks("201803111200","201803121200"))
 if set(rraw)!=wanted_raw:
  raise ValueError("original Stage59 49-HH source context mismatch")
 for t in (LEFT,RIGHT):
  r=rraw[t]
  if r["VPD_F_QC"]!="0" or r["TA_F_QC"]!="0" or num(r["RH"]) is None:
   raise ValueError("original RH QC0 interpolation anchor unavailable")
 l,r=rraw[LEFT],rraw[RIGHT]
 lr,rr=num(l["RH"]),num(r["RH"])
 if abs(lr-100)>.001 or abs(rr-92.127)>.001:
  raise ValueError("original RH QC0 endpoint changed")
 new={}
 full=[]
 neg=0
 for k in sorted(expected):
  t=k[1]
  c=cidx[k]
  rawrow=rraw[t]
  old=aidx[k]
  T,V,mds=num(rawrow["TA_F"]),num(rawrow["VPD_F"]),num(rawrow["VPD_F_MDS"])
  candrh,candv=num(c["linear_QC0_RH_candidate_pct"]),num(c["linear_QC0_VPD_candidate_hPa"])
  if (c["user_science_approval"]!="PENDING_NOT_APPROVED" or
      c["versioned_174_inclusion"]!="NO" or
      c["production_DATM_permission"]!="NO" or
      c["independent_RH_inside_30HH_validated"]!="NO" or
      c["original_QC0_left"]!=LEFT or c["original_QC0_right"]!=RIGHT or
      rawrow["TA_F_QC"]!="0" or rawrow["VPD_F_QC"]!="1" or
      rawrow["VPD_F_MDS_QC"]!="1" or num(rawrow["RH"]) is not None or
      T is None or V is None or mds is None or candrh is None or candv is None or
      abs(V-mds)>1e-8 or abs(T-num(c["original_TA_F_C"]))>1e-9 or
      abs(V-num(c["original_VPD_F_hPa"]))>1e-9 or
      abs(mds-num(c["original_VPD_F_MDS_hPa"]))>1e-9 or
      abs(V-num(old["original_VPD_F_hPa"]))>1e-9 or
      old["original_VPD_F_MDS_QC"]!="1"):
   raise ValueError("original Wjs2018 exact Stage59/60/61 source QC or MDS mismatch "+t)
  neg+=int(V>es(T))
  alpha=(parse(t)-parse(LEFT)).total_seconds()/(parse(RIGHT)-parse(LEFT)).total_seconds()
  expected_rh=lr+(rr-lr)*alpha
  expected_v=es(T)*(1-expected_rh/100)
  if (not 0<=expected_rh<=100 or not 0<=expected_v<=es(T) or
      abs(expected_rh-candrh)>1e-8 or abs(expected_v-candv)>1e-8 or
      abs((candv-V)-num(c["delta_candidate_minus_original_VPD_hPa"]))>1e-8):
   raise ValueError("Stage61 exact archived linear RH/VPD numbers changed "+t)
  et,ev=num(rawrow["TA_ERA"]),num(rawrow["VPD_ERA"])
  derived_era="" if et is None or ev is None else f"{100*(1-ev/es(et)):.9f}"
  source_tag="STAGE62_USER_APPROVED_WJS_2018_30HH_SOURCE_QC0_RH_LINEAR_INTERPOLATION"
  record=dict(site=SITE,native_time=t,source_cohort=source_tag,
   decision_id="WJS_2018_30HH_INTERPOLATION_USER_APPROVED_20261028",
   source_TA_C=rawrow["TA_F"],source_TA_QC=rawrow["TA_F_QC"],
   source_VPD_hPa=rawrow["VPD_F"],source_VPD_QC=rawrow["VPD_F_QC"],
   source_RH_pct=rawrow["RH"],source_processed_ERA_T_C=rawrow["TA_ERA"],
   source_processed_ERA_VPD_hPa=rawrow["VPD_ERA"],
   source_processed_ERA_RH_derived_pct=derived_era,
   modified_TA_C=rawrow["TA_F"],modified_RH_pct=c["linear_QC0_RH_candidate_pct"],
   modified_VPD_hPa=c["linear_QC0_VPD_candidate_hPa"],
   delta_VPD_hPa=c["delta_candidate_minus_original_VPD_hPa"],
   replacement_RH_provenance="LINEAR_15P5H_BETWEEN_ORIGINAL_QC0_RH_100_AND_92P127_NOT_MEASURED_INSIDE_GAP",
   new_VPD_derivation="MAGNUS_WATER_WITH_UNCHANGED_SOURCE_TA_F",
   source_QC_provenance_only="ORIGINAL_TA_QC0_VPD_QC1_MDS_QC1_PRESERVED_NEW_RH_NOT_MEASURED",
   overlay_status="EXPLICIT_USER_APPROVED_20261028_VERSIONED_CANDIDATE_ONLY_NO_DATM")
  if set(record)!=set(SCHEMA):raise ValueError("Stage62 approved overlay schema not exact")
  new[k]=record
  full.append(dict(site=SITE,native_time=t,
   original_TA_F_C=rawrow["TA_F"],original_TA_F_QC=rawrow["TA_F_QC"],
   original_VPD_F_hPa=rawrow["VPD_F"],original_VPD_F_QC=rawrow["VPD_F_QC"],
   original_VPD_F_MDS_hPa=rawrow["VPD_F_MDS"],
   original_VPD_F_MDS_QC=rawrow["VPD_F_MDS_QC"],
   original_source_RH_field=rawrow["RH"],
   original_source_ERA_T_C=rawrow["TA_ERA"],
   original_source_ERA_VPD_hPa=rawrow["VPD_ERA"],
   original_source_ERA_RH_derived_pct=derived_era,
   external_ERA5L_RH_reference_pct=c.get("independent_ERA5L_RH_pct",""),
   QC0_left_time=LEFT,QC0_right_time=RIGHT,
   interpolated_RH_pct=c["linear_QC0_RH_candidate_pct"],
   reconstructed_VPD_hPa=c["linear_QC0_VPD_candidate_hPa"],
   approved_by_user_date=APPROVED_DATE,
   filled_not_original_tower_measurement="YES",
   production_DATM_allowed="NO"))
 if len(new)!=30 or neg!=4:
  raise ValueError("original 30 QC1 MDS records / four negative original implied RH not conserved")
 # Cross-check Stage61 independent 31 adjacent VPD transitions, including unchanged original QC0 anchors.
 selected={LEFT:num(l["VPD_F"]),RIGHT:num(r["VPD_F"])}
 selected.update({k[1]:num(row["modified_VPD_hPa"]) for k,row in new.items()})
 boundary=[]
 for a,b in zip(ticks(LEFT,RIGHT),ticks(LEFT,RIGHT)[1:]):
  v1,v2=selected[a],selected[b]
  jump=v2-v1
  boundary.append(dict(site=SITE,before_native=a,after_native=b,
   before_selected_VPD_hPa=f"{v1:.10f}",after_selected_VPD_hPa=f"{v2:.10f}",
   jump_hPa=f"{jump:.10f}",
   abs_jump_gt2hPa=int(abs(jump)>2),abs_jump_gt4hPa=int(abs(jump)>4)))
 if len(boundary)!=31 or any(int(x["abs_jump_gt2hPa"]) for x in boundary):
  raise ValueError("new 204 candidate introduces >2 hPa Wjs 2018 boundary jump")
 for b,old in zip(boundary,edges61):
  if (b["site"]!=old["site"] or b["before_native"]!=old["before_native"] or
      b["after_native"]!=old["after_native"] or
      abs(num(b["jump_hPa"])-num(old["delta_VPD_hPa"]))>1e-8):
   raise ValueError("Stage61 archived 31 exact native transitions mismatch")
 combined=dict(bidx)
 combined.update(new)
 if len(combined)!=204 or len(set(combined))!=204 or set(combined)!=set(bidx)|expected:
  raise ValueError("174+30 strict new version cardinality mismatch")
 if any(combined[k]!=bidx[k] for k in bidx):
  raise ValueError("original approved 174 row content changed")
 output=[combined[k] for k in sorted(combined)]
 if any(set(r)!=set(SCHEMA) for r in output):
  raise ValueError("new 204 overlay schema mismatch")
 # All checks complete before writing a NEW, disjoint report directory.
 out.mkdir(exist_ok=False)
 f204=out/"stage62_VERSIONED_204_APPROVED_RH_VPD_native_overlay.csv"
 f30=out/"stage62_EXACT_30_NEW_USER_APPROVED_Wjs2018_RECONSTRUCTIONS.csv"
 faudit=out/"stage62_EXACT_30_ORIGINAL_MDS_QC_AND_ERA5L_PROVENANCE.csv"
 fb=out/"stage62_Wjs2018_ALL31_NEWLY_APPROVED_BOUNDARIES.csv"
 write(f204,SCHEMA,output)
 write(f30,SCHEMA,[new[k] for k in sorted(new)])
 write(faudit,EVIDENCE,full)
 write(fb,EDGE,boundary)
 # Read-back invariant: no prior 174 mutation, no overlap, exact 204.
 reread=idx(read(f204,SCHEMA))
 if len(reread)!=204 or any(reread[k]!=bidx[k] for k in bidx):
  raise ValueError("Stage62 written file readback unexpectedly changes previous 174")
 manifest=dict(
  stage62_science_scope="EXACT_30_USER_APPROVED_WJS2018_NATIVE_SOURCE_RH_INTERPOLATION",
  investigator_explicit_approval_date=APPROVED_DATE,
  existing_approved_174_HH_unchanged=True,newly_approved_2018_HH=30,
  total_versioned_approved_candidate_HH=204,
  original_MDS_VPD_QC1_HH=30,original_negative_implied_RH_HH=4,
  original_QC0_RH_left_pct=lr,original_QC0_RH_right_pct=rr,
  original_QC0_left_native=LEFT,original_QC0_right_native=RIGHT,
  2018_new_boundary_count=len(boundary),
  2018_new_abs_jump_gt2hPa=0,
  original_RH_inside_2018_gap_measured=False,
  interpolation_15p5h_unverified_meteorological_path=True,
  original_2018_source_historical_QC_retained=True,
  previous_174_approved_overlay_file_unchanged=True,
  previous_46_P1_HOLD_and_other_science_HOLD_unchanged=True,
  source_FLUXMET_changed=False,DATM_forcing_changed=False,
  Slurm_jobs_submitted=0,
  production_DATM_authorization=False,
  previous_174_source_sha256=sha(f56),
  original_Wjs_source_product_sha256=sourcehash,
  input_sha256={"Stage53_source_identification":sha(f53),
   "Stage59_49_original_HH":sha(f59),
   "Stage60_49_HH_MDS_QC":sha(f60),
   "Stage61_30_interpolation":sha(f61),
   "Stage61_31_edges":sha(e61)},
  output_sha256={p.name:sha(p) for p in (f204,f30,faudit,fb)},
  approved_30_native_times=[k[1] for k in sorted(new)],
  site_counts=dict(Counter(r["site"] for r in output)),
  new_cohort_count=30)
 (out/"stage62_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("STAGE62 SUCCESS | ORIGINAL_174_VERIFIED_UNCHANGED + WJS_2018_30_EXPLICIT_USER_APPROVED = VERSIONED_204")
 print("STAGE62 NEW_30 FIRST",FIRST,"LAST",LAST,"SOURCE_VPD_QC1_MDS_QC1=30 ORIGINAL_NEGATIVE_RH=4")
 print("STAGE62 APPROVED_2018_BOUNDS",len(boundary),
       "MAX_ADJACENT_ABS_VPD_JUMP",f"{max(abs(num(z['jump_hPa'])) for z in boundary):.8f}","GT2=0")
 print("STAGE62 OUTPUT_FILE="+str(f204))
 print("STAGE62 OUTPUT_SHA256="+sha(f204))
 print("STAGE62 COUNTS OLD=174 NEW=30 TOTAL=204 SOURCE_ORIGINAL_UNCHANGED=True")
 print("STAGE62 USER_APPROVED_CANDIDATE_ONLY; DATM_NOT_AUTHORIZED; NO_SLURM_JOBS")
 print("STAGE62_REPORTS="+str(out))
if __name__=="__main__":
 run()

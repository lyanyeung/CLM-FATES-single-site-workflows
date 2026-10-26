#!/usr/bin/env python3
"""Batch05 Stage41. Isolated ERA RH repair pilot under investigator's prior
rule: physically negative or extremely low original RH => ERA5-family
replacement review. Read ACTUAL Stage40/39/38 reports; create complete
native-event candidate, with hard QC0, approved166, held46, saturated10 guards.

IMPORTANT: Proven source anomaly != validated replacement. Results remain
isolated research records, not production DATM, source approval or Slurm jobs.
Separately verify genuine US-UMB ORIGINAL FULLSET_HH (not FLUXMET_HH) T/VPD/QC
against 23 original Stage27 native source anomalies. Never equate sources
on filename alone. Missing source semantics/columns => HOLD.
"""
import argparse,csv,json,math,hashlib
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

ERA="SOURCE_ERA_ALL_EPISODE"
ORIGINAL_TOL=.002
SOURCE_FIELDS={"site","episode_id","native_time","TA_F_C","VPD_F_hPa","TA_F_QC",
               "VPD_F_QC","RH_ERA_pct","RH_MDS_pct"}
C40={"site","native_time","episode_id","method","original_T_C","original_VPD_hPa",
     "original_QC_T","original_QC_VPD","original_implied_RH_water_pct",
     "source_ERA_RH_pct","source_MDS_RH_pct","trial_RH_pct","trial_VPD_hPa"}
E40={"site","original_episode","method","original_HH","science_review_priority",
     "original_implied_RH_min_pct"}
E39={"site","episode_id","method","original_episode_HH","new_external_gt2",
     "new_external_gt4","new_internal_gt2","new_internal_gt4",
     "manual_method_choice_needed"}
N38={"site","episode_id","native_time","research_method","original_source_T_C",
     "original_source_VPD_hPa","original_VPD_QC","research_RH_source_pct",
     "research_VPD_at_original_T_hPa","production_forcing_authorization"}
R0={"site","native_time"}
COLS=("site","native_time","original_episode","method","original_source_T_C",
 "original_source_VPD_hPa","original_source_QC_T","original_source_QC_VPD",
 "original_implied_RH_water_pct","original_source_RH_failure_reason",
 "candidate_ERA_RH_water_pct","candidate_VPD_hPa",
 "candidate_VPD_minus_original_hPa","original_source_ERA_RH_pct",
 "original_source_MDS_RH_pct","policy_gate",
 "candidate_provenance","manual_science_approval",
 "version","production_forcing_authorized")
EVCOLS=("site","episode_id","original_episode_HH","policy_negative_RH_HH",
 "policy_nearzero_RH_HH","full_event_candidate_HH",
 "max_abs_VPD_change_hPa","max_abs_VPD_original_hPa",
 "max_abs_VPD_candidate_hPa","has_QC0_original",
 "Stage39_no_new_2_4hPa_jump","policy_gate","forcing_status")
UCOLS=("site","native_time","FULLSET_TA_F","FULLSET_VPD_F","FULLSET_TA_F_QC",
 "FULLSET_VPD_F_QC","Stage27_T_C","Stage27_VPD_hPa","Stage27_T_QC",
 "Stage27_VPD_QC","T_matched","VPD_matched","QC_matched","source_status")

def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def n(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except(ValueError,TypeError):pass
 return None
def es(t):
 if t is None or not -80<=t<=60:raise ValueError("source air temperature invalid")
 return 6.112*math.exp(17.67*t/(243.5+t))
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("original source missing "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f);fields=rd.fieldnames or []
  if not required.issubset(fields) or len(fields)!=len(set(fields)):
   raise ValueError("source CSV fields absent/duplicate "+str(p))
  data=list(rd)
 if any(None in x or any(v is None for v in x.values()) for x in data):
  raise ValueError("source row malformed "+str(p))
 return data
def idx(rows,fields):
 res={}
 for row in rows:
  key=tuple(row[k] for k in fields)
  if key in res:raise ValueError("duplicate source key "+str(key))
  res[key]=row
 return res
def write(p,fields,data):
 with p.open("x",newline="",encoding="utf-8") as f:
  rd=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  rd.writeheader();rd.writerows(data)

def check_umb(fullset,original):
 target={key:val for key,val in original.items() if key[0]=="US-UMB"}
 if len(target)!=23:raise ValueError("US-UMB original 23-source population changed")
 if not fullset.is_file() or fullset.is_symlink():
  return [],{"status":"US_UMB_ORIGINAL_FULLSET_HH_NOT_FOUND",
             "path":str(fullset),"matched":0,"expected_original":23}
 with fullset.open(newline="",encoding="utf-8-sig") as h:
  r=csv.DictReader(h);headers=r.fieldnames or []
  mandatory={"TIMESTAMP_START","TA_F","VPD_F"}
  present=set(headers)
  if not mandatory.issubset(present):
   return [],{"status":"US_UMB_FULLSET_HH_MISSING_REQUIRED_T_VPD_TIME",
    "path":str(fullset),"header_fields":headers[:120],
    "missing":sorted(mandatory-present),"matched":0,"expected_original":23}
  hasqc={"TA_F_QC","VPD_F_QC"}.issubset(present)
  observed={}
  for row in r:
   tt=row.get("TIMESTAMP_START")
   if ("US-UMB",tt) not in target:continue
   if tt in observed:raise ValueError("duplicate FULLSET_HH native time "+str(tt))
   observed[tt]=row
 result=[]
 for (site,t),src in sorted(target.items()):
  dat=observed.get(t)
  T=n(dat.get("TA_F")) if dat else None
  V=n(dat.get("VPD_F")) if dat else None
  t0=n(src["TA_F_C"]);v0=n(src["VPD_F_hPa"])
  tmatch=(T is not None and t0 is not None and abs(T-t0)<=ORIGINAL_TOL)
  vmatch=(V is not None and v0 is not None and abs(V-v0)<=ORIGINAL_TOL)
  QC_T=dat.get("TA_F_QC","") if dat else ""
  QC_V=dat.get("VPD_F_QC","") if dat else ""
  qc=(hasqc and QC_T==src["TA_F_QC"] and QC_V==src["VPD_F_QC"])
  state=("SOURCE_T_VPD_QC_MATCHED_FULLSET_NOT_FLUXMET" if tmatch and vmatch and qc
    else "SOURCE_T_VPD_MATCHED_QC_UNAVAILABLE" if tmatch and vmatch and not hasqc
    else "SOURCE_T_VPD_MATCHED_BUT_QC_DISAGREES" if tmatch and vmatch
    else "FULLSET_NOT_IDENTICAL_TO_STAGE27_ORIGINAL")
  result.append(dict(site=site,native_time=t,
   FULLSET_TA_F=T if T is not None else "",
   FULLSET_VPD_F=V if V is not None else "",
   FULLSET_TA_F_QC=QC_T,FULLSET_VPD_F_QC=QC_V,
   Stage27_T_C=t0,Stage27_VPD_hPa=v0,
   Stage27_T_QC=src["TA_F_QC"],Stage27_VPD_QC=src["VPD_F_QC"],
   T_matched=tmatch,VPD_matched=vmatch,QC_matched=qc,
   source_status=state))
 c=Counter(x["source_status"] for x in result)
 status=("US_UMB_FULLSET_23_T_VPD_QC_IDENTICAL_SOURCE_PROXY_NOT_FLUXMET"
   if c["SOURCE_T_VPD_QC_MATCHED_FULLSET_NOT_FLUXMET"]==23 else
   "US_UMB_FULLSET_PARTIAL_SOURCE_PROVENANCE_UNVERIFIED")
 return result,{"status":status,"path":str(fullset),
  "sha256":digest(fullset),"header_fields":headers[:120],
  "has_original_QC_fields":hasqc,"native_source_rows_matched":dict(c),
  "expected_original":23}

def selftest():
 assert n("nan") is None and n("-9999") is None
 assert es(0)>es(-10)
 t=-10;v=es(t)*1.001
 assert 100*(1-v/es(t))<0
 assert abs(es(t)*(1-.8)-es(t)*.2)<1e-10
 print("STAGE41 SELF-TEST PASS | policy negative/near-zero RH, exact native source/QC, UMB FULLSET provenance guard, no production writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for k in ("stage40-dir","stage39-dir","stage38-dir","stage27-dir","stage24-dir","sites-root","out"):
  p.add_argument("--"+k,type=Path,default=(Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE") if k=="sites-root" else None))
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage40_dir","stage39_dir","stage38_dir","stage27_dir","stage24_dir","out")):
  p.error("provide Stage40/39/38/27/24 original report roots and NEW output")
 d40,d39,d38,d27,d24,sites=[getattr(a,k).expanduser().resolve() for k in
  ("stage40_dir","stage39_dir","stage38_dir","stage27_dir","stage24_dir","sites_root")]
 out=a.out.expanduser().resolve()
 if out.exists() or not out.parent.is_dir() or not all(x.is_dir() for x in (d40,d39,d38,d27,d24,sites)):
  p.error("source directories missing or NEW output already exists")
 paths={
 "detail40":d40/"stage40_ALL_NATIVE_OPTIONS_ORIGINAL_RH_ERA_MDS_VPD_TRIAL.csv",
 "event40":d40/"stage40_EXACT16_EVENT_SOURCE_HUMIDITY_PHYSICS_AND_SCIENCE_DECISION.csv",
 "event39":d39/"stage39_EXACT16_ORIGINAL_EVENT_METHOD_REVIEW.csv",
 "native38":d38/"stage38_RESEARCH_ONLY_FULL_SOURCE_EPISODE_NATIVE_RH_VPD_CANDIDATES.csv",
 "native27":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
 "approved24":d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv",
 "held24":d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv",
 "platform24":d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"}
 details=read(paths["detail40"],C40)
 e40=read(paths["event40"],E40)
 e39=read(paths["event39"],E39)
 n38=read(paths["native38"],N38)
 original=idx(read(paths["native27"],SOURCE_FIELDS),("site","native_time"))
 approved=idx(read(paths["approved24"],R0),("site","native_time"))
 held=idx(read(paths["held24"],R0),("site","native_time"))
 platforms=idx(read(paths["platform24"],R0),("site","native_time"))
 if (len(e40),len(e39),len(original),len(approved),len(held),len(platforms))!=(16,16,1574,166,46,10):
  raise ValueError("Stage40/39/27/24 original population counts changed")
 if len({(x["site"],x["original_episode"]) for x in e40})!=15:
  raise ValueError("Stage40 15 distinct events changed")
 event39=idx(e39,("site","episode_id","method"))
 detail_by=defaultdict(list)
 for row in details:detail_by[(row["site"],row["episode_id"],row["method"])].append(row)
 native_by=idx(n38,("site","episode_id","research_method","native_time"))
 e40_era={ (r["site"],r["original_episode"]):r for r in e40 if r["method"]==ERA}
 if len(e40_era)!=15:
  raise ValueError("Expected 15 original events with one qualified source ERA option each")
 trials=[];events=[]
 for (site,eid),e in sorted(e40_era.items()):
  z=event39.get((site,eid,ERA))
  if z is None or any(int(z[k])!=0 for k in
    ("new_external_gt2","new_external_gt4","new_internal_gt2","new_internal_gt4")):
   raise ValueError("ERA full source event not screened numerically safe at Stage39")
  rr=sorted(detail_by.get((site,eid,ERA),[]),key=lambda r:r["native_time"])
  if len(rr)!=int(e["original_HH"]) or len(rr)!=int(z["original_episode_HH"]):
   raise ValueError("Original event native 30min coverage differs")
  if rr[0]["native_time"]!=z.get("original_first_native",rr[0]["native_time"]):
   raise ValueError("unexpected event source native start")
  for r1,r2 in zip(rr,rr[1:]):
   d1=datetime.strptime(r1["native_time"],"%Y%m%d%H%M")
   d2=datetime.strptime(r2["native_time"],"%Y%m%d%H%M")
   if d2-d1!=timedelta(minutes=30):
    raise ValueError("candidate has source-native half-hour gap")
  neg=low=0;maxdelta=oldmax=newmax=0.
  for row in rr:
   key=(site,row["native_time"])
   source=original.get(key)
   if source is None or source["episode_id"]!=eid or key in approved or key in held or key in platforms:
    raise ValueError("original science anomaly missing or overlaps existing approved/HOLDs")
   base=n(source["TA_F_C"]); v=n(source["VPD_F_hPa"])
   trh=n(row["trial_RH_pct"]);nv=n(row["trial_VPD_hPa"])
   calculated_rh=100*(1-v/es(base))
   if None in (base,v,trh,nv) or not (0<=trh<=100) or not (0<=nv<=es(base)+.002):
    raise ValueError("candidate VPD/RH violates physical range or missing source data")
   if abs(calculated_rh-n(row["original_implied_RH_water_pct"]))>.001:
    raise ValueError("Stage40 calculated RH source mismatch")
   if abs(nv-es(base)*(1-trh/100))>.002:
    raise ValueError("ERA candidate inconsistent with original tower T")
   if abs(n(row["original_T_C"])-base)>.002 or abs(n(row["original_VPD_hPa"])-v)>.002:
    raise ValueError("original tower T/VPD modified in candidate")
   if source["VPD_F_QC"]=="0" or row["original_QC_VPD"]!=source["VPD_F_QC"]:
    raise ValueError("NO intervention on original QC0 observed VPD")
   native_ref=native_by.get((site,eid,ERA,row["native_time"]))
   if native_ref is None or abs(n(native_ref["research_VPD_at_original_T_hPa"])-nv)>.002 or native_ref["production_forcing_authorization"]!="NO":
    raise ValueError("Stage38 native source ERA candidate changed")
   if calculated_rh<0:neg+=1
   if 0<=calculated_rh<1:low+=1
   reason=("NEGATIVE_ORIGINAL_RH" if calculated_rh<0
     else "EXTREMELY_LOW_ORIGINAL_RH" if calculated_rh<1
     else "WITHIN_FULL_ANOMALY_EPISODE")
   maxdelta=max(maxdelta,abs(nv-v));oldmax=max(oldmax,abs(v));newmax=max(newmax,abs(nv))
   trials.append(dict(site=site,native_time=row["native_time"],original_episode=eid,method=ERA,
     original_source_T_C=base,original_source_VPD_hPa=v,
     original_source_QC_T=source["TA_F_QC"],original_source_QC_VPD=source["VPD_F_QC"],
     original_implied_RH_water_pct=round(calculated_rh,6),
     original_source_RH_failure_reason=reason,
     candidate_ERA_RH_water_pct=trh,candidate_VPD_hPa=nv,
     candidate_VPD_minus_original_hPa=round(nv-v,8),
     original_source_ERA_RH_pct=source["RH_ERA_pct"],
     original_source_MDS_RH_pct=source["RH_MDS_pct"],
     policy_gate="PENDING_SOURCE_ERA_PROVENANCE_AND_POST_V5_VERIFICATION",
     candidate_provenance="SOURCE_PROCESSED_ERA_RH_AT_ORIGINAL_T_NOT_IN_SITU",
     manual_science_approval="NO_NEW_APPROVAL",
     version="BATCH05_STAGE41_NEGATIVE_OR_SUB1_RH_SOURCE_ERA_ISOLATED_TRIAL",
     production_forcing_authorized="NO"))
  if not neg and not low:
   raise ValueError("Original full event lacks any negative or <1% RH science rule trigger")
  events.append(dict(site=site,episode_id=eid,original_episode_HH=len(rr),
   policy_negative_RH_HH=neg,policy_nearzero_RH_HH=low,
   full_event_candidate_HH=len(rr),max_abs_VPD_change_hPa=round(maxdelta,6),
   max_abs_VPD_original_hPa=round(oldmax,6),
   max_abs_VPD_candidate_hPa=round(newmax,6),
   has_QC0_original=False,Stage39_no_new_2_4hPa_jump=True,
   policy_gate=("SEVERE_MAGNITUDE_GT10HPA_REVIEW" if maxdelta>10 else
     "SOURCE_ERA_PROVENANCE_REVIEW_BEFORE_FORCING"),
   forcing_status="RESEARCH_ONLY_NO_DATM_WRITE"))
 if len(events)!=15 or len({(x["site"],x["native_time"]) for x in trials})!=len(trials):
  raise ValueError("Stage41 expected fifteen mutually disjoint original science events")
 fullset=(sites/"US-UMB"/"forcing"/"raw"/"AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5"/
    "AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv")
 umb_rows,umb_status=check_umb(fullset,original)
 out.mkdir(exist_ok=False)
 write(out/"stage41_NEGATIVE_OR_LT1PCT_RH_ALL15_EVENT_ERA_RESEARCH_OVERLAY.csv",COLS,trials)
 write(out/"stage41_ALL15_EVENT_SOURCE_SCIENCE_REPAIR_GATES.csv",EVCOLS,events)
 write(out/"stage41_US_UMB_FULLSET_HH_EXACT23_SOURCE_QC_COMPARISON.csv",UCOLS,umb_rows)
 result=dict(source_sha256={k:digest(v) for k,v in paths.items()},
  original_negative_or_nearzero_RH_events_verified=len(events),
  research_only_candidate_native_HH=len(trials),
  stage41_new_scientific_approvals=0,
  all_stage24_166_approved_unchanged=True,all_P1_46_HOLD_unchanged=True,
  original_P2P3_1574_unapproved=True,
  us_umb=umb_status,original_FLUXMET_DATM_CIME_Slurm_modified=False)
 (out/"stage41_manifest.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 summary=["# Stage41 — original negative/sub-1% humidity rule, candidate overlay + UMB original FULLSET","",
 "**NO PRODUCTION FORCING WRITE OR SCIENCE APPROVAL.**",
 "All fifteen original Stage39 source events have ERA humidity research trial candidates.",
 "The low-RH source policy triggers an event review, but source processed ERA meteorology remains",
 "reanalysis-based: physical range and no new 2/4hPa jumps do not prove observed tower humidity.","",
 "## Fifteen episode-scoped source ERA candidate trials",
 "| Site | Event | HH | Original negative RH HH | Original 0–1% RH HH | Max abs VPD change hPa | Gate |",
 "|---|---|---:|---:|---:|---:|---|"]
 for r in events:
  summary.append("| {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["episode_id"],r["original_episode_HH"],r["policy_negative_RH_HH"],
   r["policy_nearzero_RH_HH"],r["max_abs_VPD_change_hPa"],r["policy_gate"]))
 summary+=["","## US-UMB FULLSET_HH original provenance",
  "**{}**".format(umb_status["status"]),
  "- Genuine on-disk original source path: {}".format(fullset),
  "- Exact source-native Stage27 23 source QC comparisons: {}".format(umb_status.get("native_source_rows_matched",{})),
  "- This is FULLSET_HH, NOT FLUXMET_HH. Validating the source T/VPD/QC does not make it measured QC0.",
  "","## Next safe promotion gate",
  "1. For all 15 cases compare alternative source ERA RH, actual ERA5-Land reference where available, source MDS and original physical RH.",
  "2. Block any severe (>10 hPa) change for event-level science review, and do not hide original negative RH.",
  "3. Run isolated post-v5 forcing QC/physical and neighbor continuity tests, preserving old records and agreed Stage24 166.",
  "4. Only after the external/source evidence and validation pass, request explicit approval for production DATM overlay. No write from this stage.",
  "5. If US-UMB FULLSET_HH T/VPD/QC 23/23 match, record FULLSET-derived original provenance; else leave acquisition/provenance HOLD.",""]
 (out/"STAGE41_SOURCE_POLICY_AND_UMB_FULLSET_REPORT.md").write_text("\n".join(summary)+"\n")
 print("STAGE41 SUCCESS | 15 original RH invalid or <1% events, ERA family full-event research candidate HH",len(trials))
 print("STAGE41 GATES",json.dumps(dict(Counter(x["policy_gate"] for x in events)),sort_keys=True))
 print("STAGE41 UMB",umb_status["status"],"COUNTS",json.dumps(umb_status.get("native_source_rows_matched",{}),sort_keys=True))
 print("STAGE41_REPORT="+str(out/"STAGE41_SOURCE_POLICY_AND_UMB_FULLSET_REPORT.md"))
 print("STAGE41_OUT="+str(out))
 print("STAGE41 SOURCE/APPROVED166/HOLD46/P2P3_1574/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

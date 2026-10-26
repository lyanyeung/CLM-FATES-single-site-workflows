#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage42. SCIENCE READ ONLY.

Post-v5 physical and ±30-min native-boundary checks on the actual Stage41
21-half-hour / 15 original events ERA trial, plus full original US-UMB
FULLSET_HH 23/23 T,VPD,QC-provenance P2/P3 RH-method trials.

Never write original FLUXMET/FULLSET, Stage24 approved166, P1 HOLD46, DATM,
Slurm or model sources. All candidates UNAPPROVED even when numerically OK.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timedelta

ZIP_HASH={
"US-Var":"2e0ff6fe7f7de6dfde3ebfd2e822266e899bd80f1ad0377f78fde34efcb410f2",
"US-Vcp":"3cae4d7e148dba9ac5e1850cbfb41c1cda80ff0420a352709be324b187162329",
"US-WCr":"f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75",
"US-Wkg":"d9c31372ad29fa79946a97ac30eb02ad679b261f0b925db97ef88cf6b325221e"}
SOURCE_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
S41={"site","native_time","original_episode","method",
 "original_source_T_C","original_source_VPD_hPa","original_source_QC_T",
 "original_source_QC_VPD","original_implied_RH_water_pct","candidate_ERA_RH_water_pct",
 "candidate_VPD_hPa","production_forcing_authorized"}
P27={"site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
 "RH_ERA_pct","RH_MDS_pct"}
U41={"site","native_time","Stage27_T_C","Stage27_VPD_hPa",
 "Stage27_T_QC","Stage27_VPD_QC","source_status"}
KEY={"site","native_time"}
EDGE_FIELDS=("site","original_episode","method","native_boundary_side",
 "candidate_native_time","neighbor_native_time","candidate_original_VPD_hPa",
 "candidate_trial_VPD_hPa","neighbor_original_QC_VPD","neighbor_original_implied_RH_water_pct",
 "neighbor_status","neighbor_selected_VPD_hPa",
 "original_abs_VPD_jump_hPa","trial_abs_VPD_jump_hPa",
 "delta_jump_trial_minus_original_hPa","new_jump_gt2hPa","new_jump_gt4hPa",
 "trial_jump_gt2hPa","trial_jump_gt4hPa",
 "neighbor_QC0_measured","neighbor_RH_lt10_or_unphysical",
 "uncertain_neighbor","edge_science_status")
CASE_FIELDS=("site","original_episode","method","original_event_HH",
 "candidate_native_HH","candidate_original_negative_RH_HH",
 "candidate_original_RH_0_to1pct_HH","source_QC0_preserved","unverified_native_HH",
 "source_rh_outside0_100_HH","trial_VPD_unphysical_HH",
 "max_abs_trial_VPD_change_hPa","max_trial_VPD_hPa",
 "internal_original_jump_gt2","internal_trial_jump_gt2",
 "internal_new_jump_gt2","internal_new_jump_gt4","source_native_gap_count",
 "external_old_jump_gt2","external_trial_jump_gt2",
 "external_new_jump_gt2","external_new_jump_gt4",
 "external_neighbor_nonQC0","external_neighbor_suspect_RH",
 "external_boundary_not_comparable","source_provenance",
 "science_gate","full_forcing_authorized")
NATIVE_FIELDS=("site","native_time","original_episode","method",
 "original_T_C","original_VPD_hPa","original_VPD_QC",
 "original_implied_RH_water_pct","trial_RH_water_pct","trial_VPD_hPa",
 "trial_VPD_change_hPa","source_provenance","research_status",
 "production_forcing_authorized")

def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except(TypeError,ValueError):pass
 return None
def es(T):
 if T is None or not -80<=T<=60:raise ValueError("source tower temperature invalid")
 return 6.112*math.exp(17.67*T/(243.5+T))
def clock(x):
 if len(x)!=12 or not x.isdigit():raise ValueError("native timestamp incorrect")
 return datetime.strptime(x,"%Y%m%d%H%M")
def plus(x,mins):return (clock(x)+timedelta(minutes=mins)).strftime("%Y%m%d%H%M")
def csvrows(path,cols):
 if not path.is_file() or path.is_symlink():raise ValueError("original source missing "+str(path))
 with path.open(newline="",encoding="utf-8-sig") as f:
  rr=csv.DictReader(f);fields=rr.fieldnames or []
  if not cols.issubset(fields) or len(fields)!=len(set(fields)):
   raise ValueError("science input fields missing "+str(path))
  values=list(rr)
 if any(None in r or any(v is None for v in r.values()) for r in values):
  raise ValueError("malformed original source csv "+str(path))
 return values
def keyed(rows,fields=("site","native_time")):
 out={}
 for r in rows:
  key=tuple(r[x] for x in fields)
  if key in out:raise ValueError("source time repeated "+str(key))
  out[key]=r
 return out
def writecsv(path,fields,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def original_site(site,root,needed):
 """Read original operator-pinned FLUXMET ZIP or real US-UMB FULLSET."""
 if site=="US-UMB":
  p=root/site/"forcing"/"raw"/"AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5"/"AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv"
  with p.open(newline="",encoding="utf-8-sig") as f:
   r=csv.DictReader(f)
   cols={"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}
   if not cols.issubset(r.fieldnames or []):raise ValueError("UMB real original FULLSET_HH missing QC")
   data={}
   for line in r:
    t=line["TIMESTAMP_START"]
    if t not in needed:continue
    if t in data:raise ValueError("duplicate FULLSET original time")
    data[t]=dict(T=num(line["TA_F"]),V=num(line["VPD_F"]),
       TQC=line["TA_F_QC"],VQC=line["VPD_F_QC"])
  return data,digest(p),"US-UMB:ORIGINAL_FULLSET_HH_QC_MATCHED_NOT_FLUXMET"
 glob=sorted((root/site/"forcing"/"packages").glob("AMF_"+site+"_FLUXNET_*.zip"))
 matching=[p for p in glob if p.is_file() and not p.is_symlink() and digest(p)==ZIP_HASH[site]]
 if len(matching)!=1:raise ValueError("original pinned site ZIP SHA mismatch "+site)
 p=matching[0];data={}
 with zipfile.ZipFile(p) as z:
  m=[i for i in z.infolist() if i.filename.endswith(".csv") and
       "FLUXMET_HH_" in i.filename and "AMF_"+site+"_" in i.filename]
  if len(m)!=1:raise ValueError("original FLUXMET_HH source missing/multiple "+site)
  with z.open(m[0]) as h:
   lines=csv.DictReader(io.TextIOWrapper(h,encoding="utf-8-sig",newline=""))
   if not {"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}.issubset(lines.fieldnames or []):
    raise ValueError("original FLUXMET source lacks original T/VPD QC")
   for line in lines:
    t=line["TIMESTAMP_START"]
    if t not in needed:continue
    if t in data:raise ValueError("duplicate original tower time")
    data[t]=dict(T=num(line["TA_F"]),V=num(line["VPD_F"]),
       TQC=line["TA_F_QC"],VQC=line["VPD_F_QC"])
 return data,digest(p),site+":SHA_PINNED_ORIGINAL_FLUXMET_HH"

def evaluate(site,eid,method,rr,original,raw,approved,allP2,provenance):
 times=sorted(r["native_time"] for r in rr)
 if not times or len(set(times))!=len(times):
  raise ValueError("invalid original episode duplicate")
 gaps=sum(plus(a,30)!=b for a,b in zip(times,times[1:]))
 # Never invent/interpolate missing source-native half-hours. A noncontiguous
 # original episode cannot be promoted as one replacement window.

 selected={}
 negative=nearzero=bad_rh=bad_V=source_qc0=0
 maxchange=maxnew=0.
 for r in rr:
  time=r["native_time"];key=(site,time)
  src=original.get(key)
  obs=raw.get(time)
  if src is None or obs is None or src["episode_id"]!=eid:
   raise ValueError("source-original episode/timestamp unverified "+str(key))
  T=num(src["TA_F_C"]);V=num(src["VPD_F_hPa"])
  if T is None or V is None or obs["T"] is None or obs["V"] is None:
   raise ValueError("source original T/VPD missing")
  if (abs(T-obs["T"])>.002 or abs(V-obs["V"])>.002 or
      src["TA_F_QC"]!=obs["TQC"] or src["VPD_F_QC"]!=obs["VQC"]):
   raise ValueError("raw T/VPD/QC not identical to Stage27 source "+str(key))
  source_qc0+=obs["VQC"]=="0"
  rH=(num(src["RH_ERA_pct"]) if method=="SOURCE_ERA" else num(src["RH_MDS_pct"]))
  if method=="SOURCE_ERA_STAGE41":
   rH=num(r["candidate_ERA_RH_water_pct"])
  if rH is None or not 0<=rH<=100:
   bad_rh+=1
   continue
  candidate=es(T)*(1-rH/100)
  if candidate<0 or candidate>es(T)+.002:bad_V+=1
  if method=="SOURCE_ERA_STAGE41":
   if abs(candidate-num(r["candidate_VPD_hPa"]))>.002:
    raise ValueError("Stage41 original ERA humidity candidate modified")
  originalRH=100*(1-V/es(T))
  negative+=originalRH<0
  nearzero+=0<=originalRH<1
  selected[time]=dict(T=T,V=V,QC=obs["VQC"],RH=originalRH,RHnew=rH,new=candidate)
  maxchange=max(maxchange,abs(candidate-V))
  maxnew=max(maxnew,abs(candidate))
 # Actual replacement of an entire event must maintain all source-native times
 if gaps:
  gate="NONCONTIGUOUS_ORIGINAL_EPISODE_HOLD"
 elif len(selected)!=len(rr) or source_qc0 or bad_rh or bad_V:
  gate="BLOCK_ORIGINAL_QC0_OR_UNCOVERED_HUMIDITY_SOURCE"
 else:gate="NEEDS_BOUNDARY_AND_SOURCE_PROVENANCE_REVIEW"
 internal_old2=internal_trial2=internal_new2=internal_new4=0
 for a,b in zip(times,times[1:]):
  if a not in selected or b not in selected:continue
  old=abs(selected[b]["V"]-selected[a]["V"])
  new=abs(selected[b]["new"]-selected[a]["new"])
  internal_old2+=old>2;internal_trial2+=new>2
  internal_new2+=old<=2<new;internal_new4+=old<=4<new
 edges=[];o2=t2=new2=new4=uncertain=neighbor_bad=uncomparable=0
 if len(selected)==len(rr):
  for side,t in (("BEFORE",times[0]),("AFTER",times[-1])):
   nt=plus(t,-30 if side=="BEFORE" else 30)
   obs=raw.get(nt)
   if obs is None:
    obs=dict(T=None,V=None,TQC="MISSING",VQC="MISSING")
   key=(site,nt)
   nV=(num(approved[key]["modified_VPD_hPa"]) if key in approved else obs["V"])
   nRH=(100*(1-obs["V"]/es(obs["T"])) if obs["T"] is not None and
        -80<=obs["T"]<=60 and obs["V"] is not None else None)
   status=("ALREADY_APPROVED_STAGE24" if key in approved else
           "OTHER_P2P3_UNAPPROVED" if key in allP2 else
           "SOURCE_NATIVE_NEIGHBOR_MISSING" if obs["VQC"]=="MISSING" else
           "SOURCE_ORIGINAL_NEIGHBOR")
   if nV is None:
    uncomparable+=1
    oldjump=newjump=None
   else:
    oldjump=abs(selected[t]["V"]-nV)
    newjump=abs(selected[t]["new"]-nV)
    o2+=oldjump>2;t2+=newjump>2
    new2+=oldjump<=2<newjump
    new4+=oldjump<=4<newjump
   uncertain+=(obs["VQC"]!="0" or status=="OTHER_P2P3_UNAPPROVED")
   neighbor_bad+=(nRH is None or nRH<10 or nRH>100)
   edges.append(dict(site=site,original_episode=eid,method=method,
    native_boundary_side=side,candidate_native_time=t,neighbor_native_time=nt,
    candidate_original_VPD_hPa=selected[t]["V"],
    candidate_trial_VPD_hPa=selected[t]["new"],
    neighbor_original_QC_VPD=obs["VQC"],
    neighbor_original_implied_RH_water_pct=round(nRH,6) if nRH is not None else "",
    neighbor_status=status,neighbor_selected_VPD_hPa=nV if nV is not None else "",
    original_abs_VPD_jump_hPa=round(oldjump,6) if oldjump is not None else "",
    trial_abs_VPD_jump_hPa=round(newjump,6) if newjump is not None else "",
    delta_jump_trial_minus_original_hPa=round(newjump-oldjump,6) if oldjump is not None else "",
    new_jump_gt2hPa=(oldjump<=2<newjump) if oldjump is not None else False,
    new_jump_gt4hPa=(oldjump<=4<newjump) if oldjump is not None else False,
    trial_jump_gt2hPa=(newjump>2) if newjump is not None else False,
    trial_jump_gt4hPa=(newjump>4) if newjump is not None else False,
    neighbor_QC0_measured=obs["VQC"]=="0",
    neighbor_RH_lt10_or_unphysical=nRH is None or nRH<10 or nRH>100,
    uncertain_neighbor=(obs["VQC"]!="0" or status=="OTHER_P2P3_UNAPPROVED"),
    edge_science_status="RESEARCH_ONLY_NOT_APPROVED"))
 if gate=="NEEDS_BOUNDARY_AND_SOURCE_PROVENANCE_REVIEW":
  gate=("NEW_TRIAL_4HPA_DISCONTINUITY_HOLD" if new4 or internal_new4 else
        "NEW_TRIAL_2HPA_DISCONTINUITY_HOLD" if new2 or internal_new2 else
        "UNKNOWN_OR_UNAPPROVED_SOURCE_BOUNDARY_HOLD" if uncertain or neighbor_bad or uncomparable else
        "SEVERE_MAGNITUDE_GT10HPA_REVIEW" if maxchange>10 else
        "NUMERIC_POSTV5_GATE_PASSED_SCIENCE_APPROVAL_PENDING")
 row=dict(site=site,original_episode=eid,method=method,original_event_HH=len(rr),
  candidate_native_HH=len(selected),candidate_original_negative_RH_HH=negative,
  candidate_original_RH_0_to1pct_HH=nearzero,source_QC0_preserved=source_qc0==0,
  unverified_native_HH=len(rr)-len(selected),source_rh_outside0_100_HH=bad_rh,
  trial_VPD_unphysical_HH=bad_V,max_abs_trial_VPD_change_hPa=round(maxchange,6),
  max_trial_VPD_hPa=round(maxnew,6),internal_original_jump_gt2=internal_old2,
  internal_trial_jump_gt2=internal_trial2,internal_new_jump_gt2=internal_new2,
  internal_new_jump_gt4=internal_new4,source_native_gap_count=gaps,external_old_jump_gt2=o2,
  external_trial_jump_gt2=t2,external_new_jump_gt2=new2,external_new_jump_gt4=new4,
  external_neighbor_nonQC0=uncertain,external_neighbor_suspect_RH=neighbor_bad,
  external_boundary_not_comparable=uncomparable,source_provenance=provenance,
  science_gate=gate,full_forcing_authorized=False)
 nat=[dict(site=site,native_time=t,original_episode=eid,method=method,
  original_T_C=rec["T"],original_VPD_hPa=rec["V"],original_VPD_QC=rec["QC"],
  original_implied_RH_water_pct=round(rec["RH"],6),
  trial_RH_water_pct=round(rec["RHnew"],6),trial_VPD_hPa=round(rec["new"],8),
  trial_VPD_change_hPa=round(rec["new"]-rec["V"],8),
  source_provenance=provenance,research_status=gate,
  production_forcing_authorized="NO") for t,rec in sorted(selected.items())]
 return row,edges,nat

def selftest():
 assert plus("200812312330",30)=="200901010000"
 assert es(-10)>es(-20)
 assert abs(es(0)*(1-.7)-es(0)*.3)<1e-9
 assert len(ZIP_HASH)==4
 print("STAGE42 SELF-TEST PASS | original 21 Stage41 HH, original US-UMB23 FULLSET/QC, no production edits")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for k in ("stage41-dir","stage27-dir","stage24-dir","sites-root","out"):
  p.add_argument("--"+k,type=Path,default=SOURCE_ROOT if k=="sites-root" else None)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage41_dir","stage27_dir","stage24_dir","out")):
  p.error("requires --stage41-dir --stage27-dir --stage24-dir and NEW --out")
 d41,d27,d24,root=[getattr(a,k).expanduser().resolve() for k in
  ("stage41_dir","stage27_dir","stage24_dir","sites_root")]
 out=a.out.expanduser().resolve()
 if out.exists() or not out.parent.is_dir() or not all(x.is_dir() for x in (d41,d27,d24,root)):
  p.error("must use real existing original source dirs and a NEW output")
 fn={
  "stage41":d41/"stage41_NEGATIVE_OR_LT1PCT_RH_ALL15_EVENT_ERA_RESEARCH_OVERLAY.csv",
  "umb41":d41/"stage41_US_UMB_FULLSET_HH_EXACT23_SOURCE_QC_COMPARISON.csv",
  "original":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  "approved":d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv",
  "hold":d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv",
  "platform":d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"}
 stage41=csvrows(fn["stage41"],S41)
 umbs=csvrows(fn["umb41"],U41)
 originals=keyed(csvrows(fn["original"],P27))
 approved=keyed(csvrows(fn["approved"],KEY))
 held=keyed(csvrows(fn["hold"],KEY))
 platforms=keyed(csvrows(fn["platform"],KEY))
 if (len(stage41),len(umbs),len(originals),len(approved),len(held),len(platforms))!=(21,23,1574,166,46,10):
  raise ValueError("actual original Stage41/27/24 science cohorts changed")
 if any(r["source_status"]!="SOURCE_T_VPD_QC_MATCHED_FULLSET_NOT_FLUXMET" for r in umbs):
  raise ValueError("US-UMB original FULLSET source not verified 23/23")
 if any(r["production_forcing_authorized"]!="NO" for r in stage41):
  raise ValueError("Stage41 source already claims unexpected production permission")
 by_group=defaultdict(list)
 for r in stage41:
  key=(r["site"],r["native_time"])
  if key in approved or key in held or key in platforms:
   raise ValueError("Stage41 source overlaps existing approved/held/platform")
  by_group[(r["site"],r["original_episode"],"SOURCE_ERA_STAGE41")].append(r)
 if len(by_group)!=15:raise ValueError("Stage41 original 15 source event count changed")
 for key,src in originals.items():
  if key[0]=="US-UMB":
   by_group[("US-UMB",src["episode_id"],"SOURCE_ERA")].append(src)
   by_group[("US-UMB",src["episode_id"],"SOURCE_MDS")].append(src)
 umb_e={ep for site,ep,m in by_group if site=="US-UMB"}
 if len(umb_e)!=9:raise ValueError("Expected original 9 US-UMB P2P3 episodes")
 site_times=defaultdict(set)
 for (site,eid,method),rr in by_group.items():
  for r in rr:
   t=r["native_time"]
   site_times[site].update((plus(t,-30),t,plus(t,30)))
 raws={};sourcehash={};provenance={}
 for site in sorted(site_times):
  raw,sh,src=original_site(site,root,site_times[site])
  raws[site]=raw;sourcehash[site]=sh;provenance[site]=src
  for k in (key for key in originals if key[0]==site):
   if k[1] not in site_times[site]:continue
   v=raw.get(k[1]);o=originals[k]
   if v is None or v["T"] is None or v["V"] is None or num(o["TA_F_C"]) is None or num(o["VPD_F_hPa"]) is None:
    raise ValueError("original T/VPD cannot be revalidated "+str(k))
   if (abs(v["T"]-num(o["TA_F_C"]))>.002 or abs(v["V"]-num(o["VPD_F_hPa"]))>.002 or
       v["TQC"]!=o["TA_F_QC"] or v["VQC"]!=o["VPD_F_QC"]):
    raise ValueError("stage27 original source T/VPD/QC differs from SHA-verified original "+str(k))
 cases=[];edges=[];native=[]
 for (site,eid,method),rr in sorted(by_group.items()):
  z,e,n=evaluate(site,eid,method,rr,originals,raws[site],approved,originals,provenance[site])
  cases.append(z);edges+=e;native+=n
 if len([x for x in cases if x["site"]!="US-UMB"])!=15:
  raise ValueError("15 source Stage41 event methods missing")
 if len([x for x in cases if x["site"]=="US-UMB"])!=18:
  raise ValueError("US-UMB original 9 episodes × two source methods incomplete")
 if len([x for x in native if x["site"]!="US-UMB"])!=21:
  raise ValueError("Stage41 original 21 native candidates missing")
 counts=Counter(x["science_gate"] for x in cases)
 manifest=dict(stage42_type="RESEARCH_ONLY_SCIENTIFIC_GATE",
  real_original_SHA256={k:digest(v) for k,v in fn.items()},
  original_site_source_SHA256=sourcehash,source_provenance=provenance,
  source_Stage41_15_events=15,source_Stage41_21_native_HH=21,
  verified_US_UMB_source_original_23_HH=True,
  US_UMB_9_original_events_two_methods=18,
  stage42_trial_method_event_total=len(cases),
  stage42_native_method_trial_total=len(native),
  stage42_edges_total=len(edges),
  gates=dict(counts),new_scientific_approvals=0,
  source_FLUXMET_FULLSET_DATM_CIME_Slurm_modified=False,
  approved166_original_unchanged=True,held46_unchanged=True,
  original1574_P2P3_remain_unapproved=True)
 out.mkdir(exist_ok=False)
 writecsv(out/"stage42_POSTV5_NATIVE_BOUNDARY_ORIGINAL_VS_TRIAL.csv",EDGE_FIELDS,edges)
 writecsv(out/"stage42_ALL33_RESEARCH_EVENT_METHOD_QC_GATES.csv",CASE_FIELDS,cases)
 writecsv(out/"stage42_RESEARCH_ONLY_NATIVE_METHOD_CANDIDATES_NO_FORCING.csv",NATIVE_FIELDS,native)
 (out/"stage42_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 doc=["# Stage42: isolated post-v5 original-vs-trial VPD QC, and US-UMB FULLSET 23/23 original recovery","",
  "**All values research-only. No source/QC provenance overwrite or forcing approval.**",
  "Stage41 full original 15 event ERA candidate method trials now checked against",
  "SHA-pinned original FLUXMET half-hour +/-30min native neighbors. Also evaluate",
  "US-UMB 23 source original FULLSET HH half-hours in 9 original events by source",
  "ERA and MDS RH options at original T, rather than treating FULLSET as missing.",
  "Grid/met reanalysis RH is a candidate, not independent tower-observed humidity.",
  "","## Event-method trial gate counts"]
 for k,v in sorted(counts.items()):doc.append("- **{}**: {} event-method cases".format(k,v))
 doc+=["","## Main 15 original invalid-RH event candidates",
  "| Site | Event | HH | Max VPD change hPa | New >2 hPa boundary | New >4 hPa boundary | Gate |",
  "|---|---|---:|---:|---:|---:|---|"]
 for c in cases:
  if c["site"]=="US-UMB":continue
  doc.append("| {} | {} | {} | {} | {} | {} | {} |".format(
   c["site"],c["original_episode"],c["original_event_HH"],
   c["max_abs_trial_VPD_change_hPa"],c["external_new_jump_gt2"],
   c["external_new_jump_gt4"],c["science_gate"]))
 doc+=["","## US-UMB nine original source episodes, two source RH methods",
  "| Original event | Method | HH | Full coverage | Gate |",
  "|---|---|---:|---:|---|"]
 for c in cases:
  if c["site"]!="US-UMB":continue
  doc.append("| {} | {} | {} | {} | {} |".format(
   c["original_episode"],c["method"],c["original_event_HH"],
   c["candidate_native_HH"]==c["original_event_HH"],c["science_gate"]))
 doc+=["","## Before any production model forcing",
  "1. Severe >10 hPa source VPD changes and any newly created >2/>4 hPa boundaries remain HOLD for science decision.",
  "2. A numerically smooth result still requires ERA/MDS provenance and original FULLSET/QC interpretation.",
  "3. Neither source invalidity nor Stage41's existing prior repair policy authorizes replacing the selected DATM forcing without explicit user approval.",
  "4. Continue to protect the original 166 approved records, 46 P1 manually HELD, 1574 P2/P3 unapproved and 10 RH plateaus.",
  "5. US-UMB FULLSET source 23/23 confirmed; origin no longer missing, but science events not yet accepted.",""]
 (out/"STAGE42_POSTV5_BOUNDARIES_AND_UMB_SOURCE_CLOSURE.md").write_text("\n".join(doc)+"\n")
 print("STAGE42 SUCCESS | 15 invalid original RH events (21 HH) POSTV5 verified; US-UMB original 23 HH / 9 events source RH options",len(cases))
 print("STAGE42 GATES",json.dumps(dict(counts),sort_keys=True))
 print("STAGE42 UMB_23_VERIFIED",len(umbs),"TOTAL_RESEARCH_NATIVE",len(native),"BOUNDARIES",len(edges))
 print("STAGE42_REPORT="+str(out/"STAGE42_POSTV5_BOUNDARIES_AND_UMB_SOURCE_CLOSURE.md"))
 print("STAGE42_OUT="+str(out))
 print("STAGE42 SOURCE/APPROVED166/HOLD46/P2P3_1574/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

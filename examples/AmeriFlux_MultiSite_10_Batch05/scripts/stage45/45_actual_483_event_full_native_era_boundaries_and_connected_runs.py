#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage45 | all 1574 P2P3 HH, 483 original source episodes.

Evaluate hypothetical ERA-RH-at-original-T repairs against actual source ZIP
or (US-UMB only) independently validated FULLSET_HH before/after/within each
original episode AND contiguous clusters of *all* P2P3 native source times.
A source-invalid original RH is a reason to investigate, not automatic ERA
humidity approval. This is a READ-ONLY science screen; no DATM or source writes.
"""
import argparse,csv,hashlib,io,json,math,re,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
PINNED_ARCHIVES={
 "US-UMd":"27095ccd71a1c28cee5e730ca2ad99d0acb6fba7a4be07ffaa8cff7a41f2e3c5",
 "US-Var":"2e0ff6fe7f7de6dfde3ebfd2e822266e899bd80f1ad0377f78fde34efcb410f2",
 "US-Vcp":"3cae4d7e148dba9ac5e1850cbfb41c1cda80ff0420a352709be324b187162329",
 "US-WCr":"f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75",
 "US-Whs":"0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767",
 "US-Wkg":"d9c31372ad29fa79946a97ac30eb02ad679b261f0b925db97ef88cf6b325221e"}
REQUIRED={"site","native_time","episode_id","TA_F_C","VPD_F_hPa",
 "TA_F_QC","VPD_F_QC","RH_ERA_pct","RH_MDS_pct"}
EPI_REQUIRED={"site","episode_id","unapproved_HH","original_native_start","original_native_end"}
K={"site","native_time"}
PHYS_REQUIRED={"site","native_time","episode_id","original_RH_category",
 "source_ERA_candidate_VPD_hPa","source_ERA_humidity_valid"}
INPUT_COLS={"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}
NATIVE=("site","native_time","episode_id","original_T_C","original_VPD_hPa",
 "original_T_QC","original_VPD_QC","original_implied_RH_water_pct",
 "original_source_ERA_RH_pct","trial_ERA_VPD_hPa",
 "trial_minus_original_VPD_hPa","source_original_RH_category",
 "original_source_provenance","original_archive_SHA256",
 "can_enter_full_source_event_trial","science_approval","DATM_permission")
EVENT=("site","episode_id","original_HH","original_start_native","original_end_native",
 "original_episode_number_of_contiguous_segments","source_original_QC0_HH",
 "original_implied_negative_RH_HH","source_ERA_valid_native_HH",
 "original_full_event_ERA_covered",
 "original_internal_jump_gt2","trial_internal_jump_gt2",
 "new_internal_jump_gt2","new_internal_jump_gt4",
 "original_external_jump_gt2","trial_external_jump_gt2",
 "new_external_jump_gt2","new_external_jump_gt4",
 "external_neighbors_unmeasured_or_unapproved",
 "external_neighbors_implied_RH_below10_or_unphysical",
 "external_edges_uncomparable","max_abs_VPD_change_hPa",
 "max_abs_change_over10hPa","additional_unapproved_P2P3_adjacent",
 "risk_screen","research_trial_not_approved")
RUN=("site","connected_run_id","start_native","end_native",
 "native_HH","original_Stage27_episode_count",
 "original_QC0_VPD_HH","source_ERA_HH_valid",
 "original_internal_jump_gt2","trial_internal_jump_gt2",
 "new_internal_jump_gt2","new_internal_jump_gt4",
 "original_outer_jump_gt2","trial_outer_jump_gt2",
 "new_outer_jump_gt2","new_outer_jump_gt4",
 "outer_untrusted_neighbor_count","outer_unphysical_neighbor_RH_count",
 "outer_uncomparable_count","max_trial_delta_VPD_hPa",
 "scientific_lane","production_authorized")
EDGE=("site","context_kind","context_id","side",
 "candidate_time","neighbor_time",
 "original_candidate_VPD_hPa","trial_candidate_VPD_hPa",
 "neighbor_selected_VPD_hPa","neighbor_original_QC_VPD",
 "neighbor_kind","neighbor_implied_RH_water_pct",
 "before_jump_hPa","after_jump_hPa",
 "new_gt2","new_gt4","neighbor_untrusted","neighbor_unphysical_or_lt10",
 "comparable")
SITE=("site","original_P2P3_native_HH","original_Stage27_episodes",
 "full_source_verified","original_source_SHA256",
 "native_ERA_candidate_HH","source_ERA_complete_original_events",
 "event_low_numeric_risk_science_pending",
 "connected_ERA_source_runs","run_low_numeric_risk_science_pending",
 "new_outer_gt4_for_connected_runs",
 "original_QC0_protected","site_science_pass")
def numeric(v):
 try:
  x=float(v)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except (ValueError,TypeError):pass
 return None
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def sat(T):
 if T is None or not -80<=T<=60:return None
 return 6.112*math.exp(17.67*T/(243.5+T))
def clk(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("native source time malformed "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def nearby(t,minutes):return (clk(t)+timedelta(minutes=minutes)).strftime("%Y%m%d%H%M")
def rows(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing source "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f);names=rd.fieldnames or []
  if not required.issubset(names) or len(names)!=len(set(names)):
   raise ValueError("invalid original CSV schema "+str(p))
  data=list(rd)
 if any(None in x or any(v is None for v in x.values()) for x in data):
  raise ValueError("malformed source CSV "+str(p))
 return data
def keys(data,names=("site","native_time")):
 out={}
 for x in data:
  k=tuple(x[n] for n in names)
  if k in out:raise ValueError("duplicate source key "+str(k))
  out[k]=x
 return out
def write(p,names,data):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=names,extrasaction="raise")
  w.writeheader();w.writerows(data)
def selected_original_stream(fh,needed,site):
 r=csv.DictReader(io.TextIOWrapper(fh,encoding="utf-8-sig",newline=""))
 if not INPUT_COLS.issubset(r.fieldnames or []):
  raise ValueError("original "+site+" source missing native T/VPD/QC fields")
 out={}
 for x in r:
  t=x["TIMESTAMP_START"]
  if t not in needed:continue
  if t in out:raise ValueError("duplicate original native source time "+site+" "+t)
  out[t]=(numeric(x["TA_F"]),numeric(x["VPD_F"]),x["TA_F_QC"],x["VPD_F_QC"])
 return out
def matches_source(source,reference):
 for t,r in reference.items():
  x=source.get(t)
  if x is None or x[0] is None or x[1] is None:return False
  T=numeric(r["TA_F_C"]);V=numeric(r["VPD_F_hPa"])
  if T is None or V is None or abs(T-x[0])>.002 or abs(V-x[1])>.002:return False
  if r["TA_F_QC"]!=x[2] or r["VPD_F_QC"]!=x[3]:return False
 return True
def original_site(site,root,needed,reference):
 base=root/site/"forcing"
 if site=="US-UMB":
  p=base/"raw"/"AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5"/"AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv"
  if not p.is_file():raise ValueError("US-UMB independently verified original FULLSET missing")
  with p.open("rb") as fh:d=selected_original_stream(fh,needed,site)
  if not matches_source(d,reference):raise ValueError("FULLSET original T/VPD/QC no longer exactly matches 23 Stage27 source records")
  return d,sha(p),str(p)+"::SOURCE_FULLSET_NOT_FLUXMET"
 if not base.is_dir():raise ValueError("site forcing directory absent "+site)
 paths=sorted(set(x for x in base.rglob("*") if x.is_file() and not x.is_symlink()
  and x.suffix.lower() in (".zip",".csv")))
 if len(paths)>2500:raise ValueError("too many site source candidates")
 pattern=re.compile(r"AMF_"+re.escape(site)+r"_FLUXNET_FLUXMET_HH_.+[.]csv",re.I)
 verified=[]
 for p in paths:
  try:
   if p.suffix.lower()==".csv":
    if not pattern.fullmatch(p.name):continue
    with p.open("rb") as fh:d=selected_original_stream(fh,needed,site)
    member=p.name
   else:
    with zipfile.ZipFile(p) as z:
     mh=[m for m in z.infolist() if pattern.fullmatch(Path(m.filename).name)]
     if len(mh)!=1:continue
     if mh[0].file_size>900*1024*1024:
      raise ValueError("oversize original HH member")
     member=mh[0].filename
     with z.open(mh[0]) as fh:d=selected_original_stream(fh,needed,site)
  except (OSError,zipfile.BadZipFile,UnicodeError,ValueError):
   # A nonmatching or unreadable alternative archive cannot prevent the
   # site from using another EXACT original Stage27-matched source. Never
   # use the damaged candidate itself.
   continue
  if not matches_source(d,reference):continue
  h=sha(p)
  if site in PINNED_ARCHIVES and p.suffix.lower()==".zip" and h!=PINNED_ARCHIVES[site]:
   continue
  verified.append((p,d,h,member))
 if not verified:raise ValueError("No matching ORIGINAL FLUXMET_HH native T/VPD/QC source "+site)
 x=verified[0][1]
 if any(y[1]!=x for y in verified[1:]):
  raise ValueError("different source copies agree on selected anomalies but have different native boundaries "+site)
 verified.sort(key=lambda x:(x[0].suffix.lower()!=".zip",
  x[2]!=PINNED_ARCHIVES.get(site),len(x[0].parts),str(x[0])))
 p,d,h,member=verified[0]
 return d,h,str(p)+"::"+member

def continuous_groups(times):
 times=sorted(set(times))
 if not times:return []
 groups=[[times[0]]]
 for t in times[1:]:
  if nearby(groups[-1][-1],30)==t:groups[-1].append(t)
  else:groups.append([t])
 return groups

def assess(site,group,raw,trial,origmap,approved,kind,identity):
 ins=Counter();edges=[]
 delta=0.;qc0=0
 for t in group:
  x=raw.get(t)
  if x is None:raise ValueError("missing original candidate halfhour "+site+" "+t)
  qc0+=x[3]=="0"
  y=trial.get((site,t))
  if y is None:continue
  delta=max(delta,abs(y-x[1]))
 for a,b in zip(group,group[1:]):
  if nearby(a,30)!=b:continue
  x,y=raw[a],raw[b]
  u,v=trial.get((site,a)),trial.get((site,b))
  if u is None or v is None:continue
  before=abs(y[1]-x[1]);after=abs(v-u)
  ins["before2"]+=before>2;ins["after2"]+=after>2
  ins["new2"]+=before<=2<after;ins["new4"]+=before<=4<after
 for side,t in (("BEFORE",group[0]),("AFTER",group[-1])):
  nt=nearby(t,-30 if side=="BEFORE" else 30)
  neighbor=raw.get(nt)
  present=(site,nt) in origmap
  mode=("UNAPPROVED_P2P3" if present else
        "STAGE24_APPROVED" if (site,nt) in approved else
        "ORIGINAL_SOURCE" if neighbor else "MISSING_ORIGINAL_NEIGHBOR")
  original=raw[t][1];candidate=trial.get((site,t))
  V=(numeric(approved[(site,nt)]["modified_VPD_hPa"]) if (site,nt) in approved
     else neighbor[1] if neighbor else None)
  q=neighbor[3] if neighbor else "MISSING"
  rh=(100*(1-neighbor[1]/sat(neighbor[0])) if neighbor and
    neighbor[0] is not None and neighbor[1] is not None and
    sat(neighbor[0]) is not None else None)
  bad=(rh is None or rh<10 or rh>100)
  untrusted=(mode=="UNAPPROVED_P2P3" or q!="0")
  comparable=(candidate is not None and V is not None)
  before=abs(original-V) if comparable else None
  after=abs(candidate-V) if comparable else None
  if comparable:
   ins["ext_before2"]+=before>2;ins["ext_after2"]+=after>2
   ins["ext_new2"]+=before<=2<after;ins["ext_new4"]+=before<=4<after
  else:ins["ext_uncomparable"]+=1
  ins["ext_untrusted"]+=untrusted;ins["ext_bad_RH"]+=bad
  ins["adjacent_unapproved"]+=present
  edges.append(dict(site=site,context_kind=kind,context_id=identity,side=side,
   candidate_time=t,neighbor_time=nt,original_candidate_VPD_hPa=original,
   trial_candidate_VPD_hPa=round(candidate,6) if candidate is not None else "",
   neighbor_selected_VPD_hPa=V if V is not None else "",
   neighbor_original_QC_VPD=q,neighbor_kind=mode,
   neighbor_implied_RH_water_pct=round(rh,6) if rh is not None else "",
   before_jump_hPa=round(before,6) if before is not None else "",
   after_jump_hPa=round(after,6) if after is not None else "",
   new_gt2=(before<=2<after) if comparable else False,
   new_gt4=(before<=4<after) if comparable else False,
   neighbor_untrusted=untrusted,neighbor_unphysical_or_lt10=bad,comparable=comparable))
 return ins,edges,delta,qc0

def selftest():
 assert nearby("200812312330",30)=="200901010000"
 assert continuous_groups(["201101010100","201101010000","201101010030","201101010200"])==[
  ["201101010000","201101010030","201101010100"],["201101010200"]]
 assert sat(-10)<sat(0)
 assert len(SITES)==10
 print("STAGE45 SELF-TEST PASS | 1574 original HH / 483 events, original native ±30min before/after and joined contiguous P2P3 run logic; no writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for k in ("stage44-dir","stage27-dir","stage24-dir","sites-root","out"):
  p.add_argument("--"+k,type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE") if k=="sites-root" else None)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage44_dir","stage27_dir","stage24_dir","out")):
  p.error("provide actual --stage44-dir, --stage27-dir, --stage24-dir and new --out")
 d44,d27,d24,root=[getattr(a,x).expanduser().resolve() for x in
  ("stage44_dir","stage27_dir","stage24_dir","sites_root")]
 out=a.out.expanduser().resolve()
 if not all(x.is_dir() for x in (d44,d27,d24,root)) or not out.parent.is_dir() or out.exists() or any(
   x==out or x in out.parents or out in x.parents for x in (d44,d27,d24,root)):
  p.error("original source root missing or output must be NEW outside all source dirs")
 inputs={
  "source27":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  "episodes27":d27/"stage27_ALL483_original_P2P3_episode_science_risk.csv",
  "source44":d44/"stage44_ALL1574_NATIVE_HH_ORIGINAL_RH_AND_ERA_MDS_FIRST_PASS.csv",
  "approved24":d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv",
  "hold24":d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv",
  "platform24":d24/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv"}
 source=keys(rows(inputs["source27"],REQUIRED))
 eps=keys(rows(inputs["episodes27"],EPI_REQUIRED),("site","episode_id"))
 physical=keys(rows(inputs["source44"],PHYS_REQUIRED))
 approved=keys(rows(inputs["approved24"],K))
 hold=keys(rows(inputs["hold24"],K))
 plateau=keys(rows(inputs["platform24"],K))
 if (len(source),len(eps),len(physical),len(approved),len(hold),len(plateau))!=(1574,483,1574,166,46,10):
  raise ValueError("operator actual source 1574/483/166/46/10 cohort changed")
 if any(k in hold or k in plateau or k in approved for k in source):
  raise ValueError("Stage24 originally disjoint native science review cohorts unexpectedly overlap")
 if set(x[0] for x in source)!=set(SITES)-{"US-UiD"}:raise ValueError("original ten-site P2P3 cohort differs")
 bysite=defaultdict(dict);byepisode=defaultdict(list)
 candidate={};native=[];holds={};raw_by_site={};provenance={}
 for (site,t),r in source.items():
  bysite[site][t]=r;byepisode[(site,r["episode_id"])].append(t)
  h=physical[(site,t)]
  T=numeric(r["TA_F_C"]);V=numeric(r["VPD_F_hPa"])
  refRH=numeric(r["RH_ERA_pct"]);ess=sat(T)
  v=(ess*(1-refRH/100) if ess is not None and refRH is not None and 0<=refRH<=100 else None)
  v44=numeric(h["source_ERA_candidate_VPD_hPa"])
  if (v is None)!=(v44 is None) or (v is not None and abs(v-v44)>.003):
   raise ValueError("Stage44 actual candidate differs from source Stage27 "+site+" "+t)
  if v is not None:candidate[(site,t)]=v
 for (site,eid),ts in byepisode.items():
  ep=eps[(site,eid)]
  if len(ts)!=int(ep["unapproved_HH"]) or min(ts)!=ep["original_native_start"] or max(ts)!=ep["original_native_end"]:
   raise ValueError("original 483 source episode identity/time differs "+site+" "+eid)
 for site in SITES:
  if site=="US-UiD":continue
  ref=bysite[site]
  needed=set()
  for t in ref:needed.update((nearby(t,-30),t,nearby(t,30)))
  try:
   d,sh,name=original_site(site,root,needed,ref)
   if any(t not in d for t in ref):raise ValueError("source selected HH missing original")
   raw_by_site[site]=d;provenance[site]=dict(sha256=sh,source=name,matched_native=len(ref))
   print("STAGE45 SOURCE_VERIFIED",site,"ORIGINAL_HH",len(ref),"SHA",sh[:16],"FILE",name,flush=True)
  except (OSError,ValueError,zipfile.BadZipFile) as exc:
   holds[site]=str(exc)
   print("STAGE45 ORIGINAL_SOURCE_SITE_HOLD",site,str(exc),flush=True)
   continue
 nativekeys=[]
 for (site,t),r in sorted(source.items()):
  if site not in raw_by_site:continue
  d=raw_by_site[site][t];T,V=d[0],d[1]
  trial=candidate.get((site,t))
  originalrh=100*(1-V/sat(T)) if sat(T) is not None and V is not None else None
  nativekeys.append(dict(site=site,native_time=t,episode_id=r["episode_id"],
   original_T_C=T,original_VPD_hPa=V,original_T_QC=d[2],original_VPD_QC=d[3],
   original_implied_RH_water_pct=round(originalrh,6) if originalrh is not None else "",
   original_source_ERA_RH_pct=r["RH_ERA_pct"],
   trial_ERA_VPD_hPa=round(trial,6) if trial is not None else "",
   trial_minus_original_VPD_hPa=round(trial-V,6) if trial is not None else "",
   source_original_RH_category=physical[(site,t)]["original_RH_category"],
   original_source_provenance=provenance[site]["source"],
   original_archive_SHA256=provenance[site]["sha256"],
   can_enter_full_source_event_trial=(trial is not None and d[3]!="0"),
   science_approval="NO",DATM_permission="NO"))
 original_events=[];all_edges=[]
 for (site,eid),ts in sorted(byepisode.items()):
  if site not in raw_by_site:continue
  raw=raw_by_site[site]
  groups=continuous_groups(ts);esall=Counter();event_edges=[];peak=0;qc0=0
  for group in groups:
   x,e,delta,q=assess(site,group,raw,candidate,source,approved,
    "ORIGINAL_STAGE27_EVENT",eid)
   esall.update(x);event_edges+=e;peak=max(peak,delta);qc0+=q
  all_edges+=event_edges
  valid=sum((site,t) in candidate for t in ts)
  invalid=sum(physical[(site,t)]["original_RH_category"]=="ORIGINAL_RH_NEGATIVE_UNPHYSICAL" for t in ts)
  if qc0:gate="ORIGINAL_QC0_PROTECTED"
  elif len(groups)!=1:gate="ORIGINAL_EVENT_HAS_NATIVE_TIME_GAPS_HOLD"
  elif valid!=len(ts):gate="INCOMPLETE_ERA_RH_HOLD"
  elif esall["new4"]:gate="NEW_EXTERNAL_OR_INTERNAL_GT4HPA_HOLD"
  elif esall["new2"]:gate="NEW_EXTERNAL_OR_INTERNAL_GT2HPA_HOLD"
  elif peak>10:gate="LARGE_VPD_CHANGE_GT10HPA_REVIEW"
  elif esall["adjacent_unapproved"]:gate="ADJACENT_UNAPPROVED_P2P3_REPAIR_COMPONENT_REVIEW"
  elif esall["ext_untrusted"] or esall["ext_bad_RH"] or esall["ext_uncomparable"]:
   gate="ORIGINAL_EXTERNAL_NEIGHBOR_QC_OR_RH_UNCERTAIN"
  else:gate="NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL"
  original_events.append(dict(site=site,episode_id=eid,original_HH=len(ts),
   original_start_native=min(ts),original_end_native=max(ts),
   original_episode_number_of_contiguous_segments=len(groups),
   source_original_QC0_HH=qc0,original_implied_negative_RH_HH=invalid,
   source_ERA_valid_native_HH=valid,original_full_event_ERA_covered=valid==len(ts),
   original_internal_jump_gt2=esall["before2"],
   trial_internal_jump_gt2=esall["after2"],
   new_internal_jump_gt2=esall["new2"],new_internal_jump_gt4=esall["new4"],
   original_external_jump_gt2=esall["ext_before2"],trial_external_jump_gt2=esall["ext_after2"],
   new_external_jump_gt2=esall["ext_new2"],new_external_jump_gt4=esall["ext_new4"],
   external_neighbors_unmeasured_or_unapproved=esall["ext_untrusted"],
   external_neighbors_implied_RH_below10_or_unphysical=esall["ext_bad_RH"],
   external_edges_uncomparable=esall["ext_uncomparable"],
   max_abs_VPD_change_hPa=round(peak,6),max_abs_change_over10hPa=peak>10,
   additional_unapproved_P2P3_adjacent=esall["adjacent_unapproved"],
   risk_screen=gate,research_trial_not_approved=True))
 joined=[];run_id=0
 for site in SITES:
  if site not in raw_by_site:continue
  raw=raw_by_site[site]
  for grp in continuous_groups(bysite[site].keys()):
   run_id+=1
   ids={bysite[site][t]["episode_id"] for t in grp}
   rr,e,peak,qc0=assess(site,grp,raw,candidate,source,approved,"CONNECTED_P2P3_RUN",str(run_id))
   all_edges+=e
   coverage=sum((site,t) in candidate for t in grp)
   if qc0:gate="ORIGINAL_QC0_PROTECTED"
   elif coverage!=len(grp):gate="SOURCE_ERA_COVERAGE_INCOMPLETE"
   elif rr["new4"]:gate="NEW_GT4HPA_TRIAL_CONTINUITY_HOLD"
   elif rr["new2"]:gate="NEW_GT2HPA_TRIAL_CONTINUITY_HOLD"
   elif peak>10:gate="LARGE_GT10HPA_VPD_CHANGE_SCIENCE_REVIEW"
   elif rr["ext_untrusted"] or rr["ext_bad_RH"] or rr["ext_uncomparable"]:
    gate="OUTER_NATIVE_SOURCE_NEIGHBOR_UNTRUSTED"
   else:gate="NUMERIC_COMPONENT_LOW_RISK_STILL_UNAPPROVED"
   joined.append(dict(site=site,connected_run_id=str(run_id),
    start_native=grp[0],end_native=grp[-1],native_HH=len(grp),
    original_Stage27_episode_count=len(ids),original_QC0_VPD_HH=qc0,
    source_ERA_HH_valid=coverage,original_internal_jump_gt2=rr["before2"],
    trial_internal_jump_gt2=rr["after2"],new_internal_jump_gt2=rr["new2"],
    new_internal_jump_gt4=rr["new4"],
    original_outer_jump_gt2=rr["ext_before2"],trial_outer_jump_gt2=rr["ext_after2"],
    new_outer_jump_gt2=rr["ext_new2"],new_outer_jump_gt4=rr["ext_new4"],
    outer_untrusted_neighbor_count=rr["ext_untrusted"],
    outer_unphysical_neighbor_RH_count=rr["ext_bad_RH"],
    outer_uncomparable_count=rr["ext_uncomparable"],
    max_trial_delta_VPD_hPa=round(peak,6),
    scientific_lane=gate,production_authorized=False))
 ten=[]
 for site in SITES:
  a=[r for r in original_events if r["site"]==site]
  b=[r for r in joined if r["site"]==site]
  ten.append(dict(site=site,original_P2P3_native_HH=len(bysite[site]),
   original_Stage27_episodes=len([1 for k in byepisode if k[0]==site]),
   full_source_verified=site in raw_by_site,
   original_source_SHA256=provenance.get(site,{}).get("sha256","SOURCE_HOLD"),
   native_ERA_candidate_HH=sum((site,t) in candidate for t in bysite[site]),
   source_ERA_complete_original_events=sum(r["original_full_event_ERA_covered"] for r in a),
   event_low_numeric_risk_science_pending=sum(r["risk_screen"]=="NUMERIC_SOURCE_NATIVE_SCREEN_NO_SCIENCE_APPROVAL" for r in a),
   connected_ERA_source_runs=len(b),
   run_low_numeric_risk_science_pending=sum(r["scientific_lane"]=="NUMERIC_COMPONENT_LOW_RISK_STILL_UNAPPROVED" for r in b),
   new_outer_gt4_for_connected_runs=sum(r["new_outer_jump_gt4"] for r in b),
   original_QC0_protected=sum(r["source_original_QC0_HH"] for r in a),
   site_science_pass=False))
 out.mkdir(exist_ok=False)
 write(out/"stage45_ALL_VERIFIED_NATIVE_P2P3_AND_ERA_TRIAL.csv",NATIVE,nativekeys)
 write(out/"stage45_483_ORIGINAL_EVENTS_TRUE_NATIVE_VPD_QC.csv",EVENT,original_events)
 write(out/"stage45_CONNECTED_P2P3_CONTIGUOUS_RUN_METHOD_GATES.csv",RUN,joined)
 write(out/"stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv",EDGE,all_edges)
 write(out/"stage45_ALL10_SITE_REAL_SOURCE_BATCH_PROGRESS.csv",SITE,ten)
 manifest=dict(input_SHA256={k:sha(v) for k,v in inputs.items()},source_provenance=provenance,
  site_source_holds=holds,expected_original_P2P3_HH=1574,expected_original_events=483,
  independently_original_source_verified_native_HH=len(nativekeys),
  original_episodes_source_verified=len(original_events),
  contiguous_cross_original_episode_runs=len(joined),
  source_science_new_approvals=0,
  existing_Stage24_166_approved_46_manual_HOLD_10_platform_preserved=True,
  original_DATM_CIME_Slurm_FLUXMET_modified=False)
 (out/"stage45_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 md=["# Stage45 — all 1,574 source-native P2/P3 / 483 original episodes: real original boundary QC",
  "","**No original forcing changes or science approval.** Stage44 source ERA coverage is not a source-native boundary pass.",
  "Original FLUXMET packages and US-UMB original FULLSET_HH are compared to Stage27 native T/VPD/QC.",
  "A connected run joins only actually adjacent original P2/P3 source timestamps; it never fills gaps.",
  "ERA source processed RH remains a reanalysis-related candidate, not independent tower truth.",
  "","| Site | P2/P3 HH | Original episodes | Raw source verified | Full-source runs | Low-risk run screens | New >4hPa outer edges |",
  "|---|---:|---:|---|---:|---:|---:|"]
 for r in ten:
  md.append("| {} | {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["original_P2P3_native_HH"],r["original_Stage27_episodes"],
   r["full_source_verified"],r["connected_ERA_source_runs"],
   r["run_low_numeric_risk_science_pending"],r["new_outer_gt4_for_connected_runs"]))
 md+=["","## Original event gates"]
 for gate,count in sorted(Counter(x["risk_screen"] for x in original_events).items()):
  md.append("- **{}**: {} original source episodes".format(gate,count))
 md+=["","## Contiguous original P2P3 connected-run gates"]
 for gate,count in sorted(Counter(x["scientific_lane"] for x in joined).items()):
  md.append("- **{}**: {} native contiguous runs".format(gate,count))
 md+=["","## Original source acquisition/ambiguity holds"]
 if holds:
  for site,reason in sorted(holds.items()):md.append("- **{}**: {}".format(site,reason))
 else:md.append("- No original-source trust failures for the nine affected Batch05 sites")
 md+=["","## Next action",
  "1. Inspect candidate-created >4hPa run outer/inner jumps and temperature source QC before event-based science approval.",
  "2. Prefer connected runs where source processed ERA RH is complete, original QC0 protected and new discontinuities absent; these are still research-only.",
  "3. Keep suspect QC2/original RH<10% neighbors distinct, and do not smooth toward a physically impossible neighbor.",
  "4. Do not claim full site passes from P2P3 screen. Original 166 approved, 46 P1 human HOLD and ten RH plateaus remain.",
  "5. Changes >10hPa require external ERA5-Land or station evidence before changing official forcing.",""]
 (out/"STAGE45_ALL483_EVENT_NATIVE_ERA_BOUNDARY_REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE45 SUCCESS | 1574 original P2P3, 483 episodes, verified native",len(nativekeys),"verified events",len(original_events),"connected runs",len(joined))
 print("STAGE45 EVENT_LANES",json.dumps(dict(Counter(x["risk_screen"] for x in original_events)),sort_keys=True))
 print("STAGE45 CONNECTED_RUN_LANES",json.dumps(dict(Counter(x["scientific_lane"] for x in joined)),sort_keys=True))
 print("STAGE45 SITE_SOURCE_HOLDS",json.dumps(holds,sort_keys=True))
 print("STAGE45_REPORT="+str(out/"STAGE45_ALL483_EVENT_NATIVE_ERA_BOUNDARY_REPORT.md"))
 print("STAGE45_OUT="+str(out))
 print("STAGE45 SOURCE_166_APPROVED/46_HOLD/10_RHPLATEAUS/1574_P2P3/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

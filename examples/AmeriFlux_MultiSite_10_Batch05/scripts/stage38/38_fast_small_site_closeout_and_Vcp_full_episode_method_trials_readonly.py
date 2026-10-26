#!/usr/bin/env python3
"""Batch05 Stage38 | FAST scientific closeout triage + 65 Vcp full episode trials.

(A) 7 non-Vcp/Vcm/Wjs sites: validate all native P2/P3 original half-hours
    against immutable original FLUXMET ZIP; compare full contiguous episode
    source ERA RH and MDS RH at measured/source-selected T (research-only).
    Exactly report evidence and obstacles per site. A zero-P2P3 site is NOT
    a formal complete forcing/science/model pass.
(B) US-Vcp: for all 65 Stage37 risk episodes, compare full ORIGINAL source
    episode reconstruction vs Stage36's problematic sparse 251 trial. A full
    episode avoids sparse-fragment internal boundaries, but MUST compare
    original vs candidate full physical 30-min transitions. No interpolation
    or automatic method selection. Preserve QC0 and all stage24 statuses.

READ ONLY: original source ZIP and source reports never written. No CIME,
DATM, Slurm, versioned approved overlay mutation or RH-HOLD release.
"""
import argparse,csv,hashlib,io,json,math,re,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
SMALL=("US-UiD","US-UMB","US-UMd","US-Var","US-WCr","US-Whs","US-Wkg")
VCP_ZIP_SHA="3cae4d7e148dba9ac5e1850cbfb41c1cda80ff0420a352709be324b187162329"
P2_FIELDS={"site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC",
 "VPD_F_QC","RH_ERA_pct","RH_MDS_pct","review_lane","human_science_decision"}
EP_FIELDS={"site","episode_id","unapproved_HH","original_native_start","original_native_end"}
SITE_FIELDS={"site","original_P2P3_unapproved_HH","original_episodes"}
SOURCE_FIELDS={"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}
HOLD_FIELDS={"site","native_time"}
APPROVED_FIELDS={"site","native_time","modified_VPD_hPa"}
STAGE37_FIELDS={"site","episode_id","new_gt2_edges","new_gt4_edges",
 "external_edges_checked","number_of_contiguous_trial_segments","event_science_gate"}
STAGE35_FIELDS={"site","native_time","fresh_ERA5Land_grid_RH_pct"}
ROW_FIELDS=("site","episode_id","method","event_start_native","event_end_native",
 "original_episode_HH","native_available_HH","original_has_noncontiguous_dates",
 "method_valid_HH","method_coverage_all_original_episode","source_QC0_protected_HH",
 "source_QC2_or_not_measured_HH","source_original_missing_or_unphysical_VPD_HH",
 "candidate_negative_or_unphysical_VPD_HH","original_internal_new_jump_gt2_HH",
 "original_internal_new_jump_gt4_HH","original_external_jump_gt2",
 "candidate_external_jump_gt2","new_external_jump_gt2",
 "original_external_jump_gt4","candidate_external_jump_gt4",
 "new_external_jump_gt4","external_trial_worsening_ge0_5",
 "neighbors_QC2_or_not_measured","neighbors_are_other_P2P3_unapproved",
 "original_st37_sparse_new_gt4_edges","original_st37_sparse_new_gt2_edges",
 "candidate_range_seconds","science_gate","production_permission")
TRIAL_FIELDS=("site","native_time","episode_id","research_method",
 "original_source_T_C","original_source_VPD_hPa","original_VPD_QC",
 "research_RH_source_pct","research_VPD_at_original_T_hPa",
 "research_VPD_change_vs_original_hPa","full_original_episode_HH",
 "full_episode_science_gate","original_FLUXMET_ZIP_SHA256",
 "science_status","production_forcing_authorization")
SITE_REPORT_FIELDS=("site","source_original_P2P3_unapproved_HH",
 "source_original_P2P3_events","source_ZIP_archive_SHA256",
 "exact_native_HH_verified_against_original_ZIP","number_of_full_episode_trials",
 "full_episode_ERA_review_candidates","full_episode_MDS_review_candidates",
 "source_original_QC0_protected_HH",
 "P1_manual_HOLD_total_batch_unchanged",
 "approved166_unchanged","site_closeout_status")
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()
def num(x):
 try:
  y=float(x)
  if math.isfinite(y) and y not in (-9999.,-6999.):return y
 except (TypeError,ValueError):pass
 return None
def sat(t):
 if t is None or t<-80 or t>60:raise ValueError("source T invalid")
 return 6.112*math.exp(17.67*t/(t+243.5))
def clock(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad source LST "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def near(t,mins):return (clock(t)+timedelta(minutes=mins)).strftime("%Y%m%d%H%M")
def read(path,cols):
 if not path.is_file() or path.is_symlink():raise ValueError("missing original report "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as f:
  rr=csv.DictReader(f);fields=rr.fieldnames or []
  if not cols.issubset(fields) or len(set(fields))!=len(fields):
   raise ValueError("source report columns mismatch "+str(path))
  rows=list(rr)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed original source "+str(path))
 return rows
def keyed(rows,keys=("site","native_time")):
 d={}
 for r in rows:
  k=tuple(r[q] for q in keys)
  if k in d:raise ValueError("source duplicate "+str(k))
  d[k]=r
 return d
def wcsv(path,fields,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  wr=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  wr.writeheader();wr.writerows(rows)
def raw_data(root,site,times):
 if not times:return {},None
 packages=root/site/"forcing"/"packages"
 candidates=sorted(packages.glob("AMF_"+site+"_FLUXNET_*_v1.3_r1.zip"))
 if len(candidates)!=1 or not candidates[0].is_file() or candidates[0].is_symlink():
  raise ValueError("expect exactly 1 original site FLUXNET v1.3 r1 package: "+str(packages))
 path=candidates[0];sha=digest(path)
 if site=="US-Vcp" and sha!=VCP_ZIP_SHA:
  raise ValueError("Stage29/36 US-Vcp original ZIP SHA differs")
 found={}
 with zipfile.ZipFile(path) as z:
  matches=[m for m in z.infolist() if re.fullmatch(
   "AMF_"+re.escape(site)+r"_FLUXNET_FLUXMET_HH_.+[.]csv",
   Path(m.filename).name,re.I)]
  if len(matches)!=1 or matches[0].file_size>900*1024*1024:
   raise ValueError("original zip CSV source missing/ambiguous/oversized")
  with z.open(matches[0]) as b:
   rows=csv.DictReader(io.TextIOWrapper(b,encoding="utf-8-sig",newline=""))
   if not SOURCE_FIELDS.issubset(rows.fieldnames or []):
    raise ValueError("original FLUXMET HH lacks T/VPD/QC fields")
   for r in rows:
    t=r["TIMESTAMP_START"]
    if t in times:
     if t in found:raise ValueError("duplicate source-native half-hour "+site+" "+t)
     found[t]=dict(T=num(r["TA_F"]),V=num(r["VPD_F"]),
                   QC_T=r["TA_F_QC"],QC_V=r["VPD_F_QC"])
 return found,sha
def evaluate(site,eid,ep,rr,method,raw,allP2,approved,sparse=None,fresh=None):
 dates=sorted(r["native_time"] for r in rr)
 if len(dates)!=len(set(dates)):raise ValueError("duplicate episode half hours")
 if len(dates)!=int(ep["unapproved_HH"]):raise ValueError("source Stage27 episode count differs")
 no_gaps=all(near(a,30)==b for a,b in zip(dates,dates[1:]))
 protected=sum(r["VPD_F_QC"]=="0" for r in rr)
 selected={}
 for r in rr:
  t=r["native_time"];row=raw.get(t)
  if row is None:raise ValueError("original native time missing "+site+" "+t)
  T=num(r["TA_F_C"]);V=num(r["VPD_F_hPa"])
  if T is None or V is None or row["T"] is None or row["V"] is None:
   raise ValueError("original source T/VPD missing on P2P3 native time "+site+" "+t)
  if abs(T-row["T"])>0.002 or abs(V-row["V"])>0.002 or (r["TA_F_QC"],r["VPD_F_QC"])!=(row["QC_T"],row["QC_V"]):
   raise ValueError("Stage27 native T/VPD/QC differs from ORIGINAL ZIP "+site+" "+t)
  cand_rh=(
   num(r["RH_ERA_pct"]) if method=="SOURCE_ERA_ALL_EPISODE" else
   num(r["RH_MDS_pct"]) if method=="SOURCE_MDS_ALL_EPISODE" else
   fresh.get((site,t)) if method=="FRESH_ERA5L_ONLY_IF_FULL_REFERENCE" and fresh else None)
  if cand_rh is not None and 0<=cand_rh<=100:
   selected[t]=sat(T)*(1-cand_rh/100)
 # Cannot apply a full episode model where any source moisture is missing,
 # QC0 measured VPD exists, or the episode has missing half-hour steps.
 valid=not protected and no_gaps and len(selected)==len(rr)
 def edge(t,neighborT,original,candidate):
  nrow=raw.get(neighborT)
  if nrow is None or nrow["V"] is None:
   return None
  neighbor=(num(approved[(site,neighborT)]["modified_VPD_hPa"])
            if (site,neighborT) in approved else nrow["V"])
  if neighbor is None:return None
  return abs(original-neighbor),abs(candidate-neighbor)
 internal_old2=internal_new2=internal_new4=0
 for t1,t2 in zip(dates,dates[1:]):
  if near(t1,30)!=t2 or t1 not in selected or t2 not in selected:continue
  o1,o2=raw[t1]["V"],raw[t2]["V"]
  a=abs(o2-o1);b=abs(selected[t2]-selected[t1])
  if a>2:internal_old2+=1
  if a<=2<b:internal_new2+=1
  if a<=4<b:internal_new4+=1
 boundaries=[]
 if valid:
  for t,nb in ((dates[0],near(dates[0],-30)),(dates[-1],near(dates[-1],30))):
   pair=edge(t,nb,raw[t]["V"],selected[t])
   if pair is not None:boundaries.append((nb,*pair))
 original2=sum(a>2 for _,a,b in boundaries)
 candidate2=sum(b>2 for _,a,b in boundaries)
 new2=sum(a<=2<b for _,a,b in boundaries)
 original4=sum(a>4 for _,a,b in boundaries)
 candidate4=sum(b>4 for _,a,b in boundaries)
 new4=sum(a<=4<b for _,a,b in boundaries)
 worse=sum(b-a>=0.5 for _,a,b in boundaries)
 nbqc=sum(raw[t]["QC_V"]!="0" for t,a,b in boundaries)
 nbp2=sum((site,t) in allP2 for t,a,b in boundaries)
 gate=("NOT_FULL_SOURCE_EPISODE" if not no_gaps else
       "QC0_SENSOR_PROTECTED" if protected else
       "MISSING_SOURCE_METHOD_RH" if len(selected)!=len(rr) else
       "NEIGHBOR_MISSING_SOURCE_VPD" if len(boundaries)!=2 else
       "NEW_SEVERE_JUMP_GT4" if new4 or internal_new4 else
       "NEW_JUMP_GT2" if new2 or internal_new2 else
       "NEIGHBOR_UNAPPROVED_OR_NONMEASURED" if nbp2 or nbqc else
       "NUMERIC_CANDIDATE_REVIEW_NO_SCIENCE_APPROVAL")
 return dict(site=site,episode_id=eid,method=method,
  event_start_native=dates[0],event_end_native=dates[-1],
  original_episode_HH=len(rr),native_available_HH=len(raw),
  original_has_noncontiguous_dates=not no_gaps,
  method_valid_HH=len(selected),method_coverage_all_original_episode=valid,
  source_QC0_protected_HH=protected,
  source_QC2_or_not_measured_HH=sum(r["VPD_F_QC"]!="0" for r in rr),
  source_original_missing_or_unphysical_VPD_HH=sum(
   raw[t]["V"] is None or not 0<=raw[t]["V"]<=sat(raw[t]["T"]) for t in dates),
  candidate_negative_or_unphysical_VPD_HH=sum(not 0<=v<=sat(raw[t]["T"])+0.001 for t,v in selected.items()),
  original_internal_new_jump_gt2_HH=internal_new2,
  original_internal_new_jump_gt4_HH=internal_new4,
  original_external_jump_gt2=original2,candidate_external_jump_gt2=candidate2,
  new_external_jump_gt2=new2,original_external_jump_gt4=original4,
  candidate_external_jump_gt4=candidate4,new_external_jump_gt4=new4,
  external_trial_worsening_ge0_5=worse,
  neighbors_QC2_or_not_measured=nbqc,neighbors_are_other_P2P3_unapproved=nbp2,
  original_st37_sparse_new_gt4_edges=sparse.get("new_gt4_edges","") if sparse else "",
  original_st37_sparse_new_gt2_edges=sparse.get("new_gt2_edges","") if sparse else "",
  candidate_range_seconds=len(rr)*1800 if no_gaps else "",
  science_gate=gate,production_permission="NO_RESEARCH_ONLY")

def selftest():
 assert near("200812312330",30)=="200901010000"
 assert 0<sat(-12)<sat(-10)
 assert all(x in SITES for x in SMALL) and len(SMALL)==7
 assert "US-Wkg" in SMALL
 assert len(SITES)==10
 cases=[
  {"site":"US-Whs","episode_id":"E1","native_time":"200805241500","TA_F_C":"-10",
   "VPD_F_hPa":"1.0","TA_F_QC":"2","VPD_F_QC":"2","RH_ERA_pct":"70",
   "RH_MDS_pct":"71"},
  {"site":"US-Whs","episode_id":"E1","native_time":"200805241530","TA_F_C":"-10",
   "VPD_F_hPa":"1.1","TA_F_QC":"2","VPD_F_QC":"2","RH_ERA_pct":"72",
   "RH_MDS_pct":"73"}]
 raw={"200805241430":{"T":-10,"V":1.2,"QC_T":"2","QC_V":"2"},
      "200805241500":{"T":-10,"V":1.0,"QC_T":"2","QC_V":"2"},
      "200805241530":{"T":-10,"V":1.1,"QC_T":"2","QC_V":"2"},
      "200805241600":{"T":-10,"V":1.3,"QC_T":"2","QC_V":"2"}}
 p2={(r["site"],r["native_time"]):r for r in cases}
 epi={"unapproved_HH":"2"}
 trial=evaluate("US-Whs","E1",epi,cases,"SOURCE_ERA_ALL_EPISODE",raw,p2,{})
 assert trial["method_coverage_all_original_episode"] is True
 assert trial["method_valid_HH"]==2 and trial["new_external_jump_gt4"]==0
 assert trial["production_permission"]=="NO_RESEARCH_ONLY"
 protected=[dict(x) for x in cases]
 protected[0]["VPD_F_QC"]="0"
 raw2={k:dict(v) for k,v in raw.items()}
 raw2["200805241500"]["QC_V"]="0"
 p2x={(r["site"],r["native_time"]):r for r in protected}
 q=evaluate("US-Whs","E1",epi,protected,"SOURCE_ERA_ALL_EPISODE",raw2,p2x,{})
 assert q["source_QC0_protected_HH"]==1 and q["science_gate"]=="QC0_SENSOR_PROTECTED"
 print("STAGE38 SELF-TEST PASS | exact ten-site source inventory; source-QC0-protecting full-event ERA trials; raw neighbor VPD gates; no writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--stage37-dir",type=Path)
 p.add_argument("--stage35-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage27_dir,a.stage24_dir,a.stage37_dir,a.stage35_dir,a.out)):
  p.error("requires --stage27-dir --stage24-dir --stage37-dir --stage35-dir --out")
 d27,d24,d37,d35,root=[x.expanduser().resolve() for x in
  (a.stage27_dir,a.stage24_dir,a.stage37_dir,a.stage35_dir,a.sites_root)]
 out=a.out.expanduser().resolve()
 if (not all(x.is_dir() for x in (d27,d24,d37,d35,root)) or out.exists()
  or not out.parent.is_dir() or any(out==x or out in x.parents or x in out.parents
   for x in (d27,d24,d37,d35,root))):p.error("output NEW directory outside all source roots")
 fp2=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 fep=d27/"stage27_ALL483_original_P2P3_episode_science_risk.csv"
 fs=d27/"stage27_ALL10_site_science_conflict_status.csv"
 fa=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 fh=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 f37=d37/"stage37_65_EPISODES_BEFORE_AFTER_PRIORITIES.csv"
 f35=d35/"stage35_429_NATIVE_TOWER_VPD_TWO_ERA_METHODS_REVIEW_ONLY.csv"
 p2=read(fp2,P2_FIELDS);ep=keyed(read(fep,EP_FIELDS),("site","episode_id"))
 sites=keyed(read(fs,SITE_FIELDS),("site",))
 approved=keyed(read(fa,APPROVED_FIELDS))
 held=keyed(read(fh,HOLD_FIELDS))
 st37=keyed(read(f37,STAGE37_FIELDS),("site","episode_id"))
 data35=read(f35,STAGE35_FIELDS)
 if (len(p2),len(ep),len(sites),len(approved),len(held),len(st37),len(data35))!=(1574,483,10,166,46,65,429):
  raise ValueError("original site/science cohorts drifted")
 if set(x[0] for x in sites)!=set(SITES) or sum(int(r["original_P2P3_unapproved_HH"]) for r in sites.values())!=1574:
  raise ValueError("real Batch05 site inventory different from source")
 if any(k[0]!="US-Vcp" for k in st37):
  raise ValueError("Stage37 65 original Vcp episodes no longer exact")
 p2map=keyed(p2)
 group=defaultdict(list)
 for r in p2:group[(r["site"],r["episode_id"])].append(r)
 for k,v in group.items():
  if len(v)!=int(ep[k]["unapproved_HH"]):raise ValueError("source episode count mismatch "+str(k))
 fresh={}
 for r in data35:
  k=(r["site"],r["native_time"])
  rh=num(r["fresh_ERA5Land_grid_RH_pct"])
  if rh is not None and 0<=rh<=100.5:fresh[k]=rh
 trial_sites=list(SMALL)+["US-Vcp"]
 outputs=[];ziphash={}
 for site in trial_sites:
  ev={eid:rows for (s,eid),rows in group.items() if s==site}
  needed=set()
  for rows in ev.values():
   for r in rows:
    t=r["native_time"];needed.update((near(t,-30),t,near(t,30)))
  raw,source_sha=raw_data(root,site,needed)
  if needed and not raw:raise ValueError("no original ZIP data for "+site)
  ziphash[site]=source_sha
  for eid,rr in sorted(ev.items()):
   for method in ("SOURCE_ERA_ALL_EPISODE","SOURCE_MDS_ALL_EPISODE"):
    outputs.append(evaluate(site,eid,ep[site,eid],rr,method,raw,p2map,
                  approved,sparse=st37.get((site,eid)),fresh=fresh))
   if site=="US-Vcp":
    outputs.append(evaluate(site,eid,ep[site,eid],rr,
                 "FRESH_ERA5L_ONLY_IF_FULL_REFERENCE",raw,p2map,
                 approved,sparse=st37.get((site,eid)),fresh=fresh))
 # Materialise ONLY isolated research candidates for complete source
 # episodes without original QC0 VPD, preserving original time/T/QC.
 # Also retain blocked numeric trials in per-event matrix; no production use.
 native_trial=[]
 for item in outputs:
  if item["method_coverage_all_original_episode"] is not True or item["source_QC0_protected_HH"]:
   continue
  site,eid,method=item["site"],item["episode_id"],item["method"]
  source=group[site,eid]
  for r in source:
   T=num(r["TA_F_C"]);V=num(r["VPD_F_hPa"])
   value=(num(r["RH_ERA_pct"]) if method=="SOURCE_ERA_ALL_EPISODE" else
     num(r["RH_MDS_pct"]) if method=="SOURCE_MDS_ALL_EPISODE" else
     fresh.get((site,r["native_time"])))
   if T is None or V is None or value is None or not 0<=value<=100:
    raise ValueError("complete trial method row unexpectedly missing native physical RH")
   new=sat(T)*(1-value/100)
   native_trial.append(dict(site=site,native_time=r["native_time"],episode_id=eid,
     research_method=method,original_source_T_C=T,
     original_source_VPD_hPa=V,original_VPD_QC=r["VPD_F_QC"],
     research_RH_source_pct=round(value,8),
     research_VPD_at_original_T_hPa=round(new,8),
     research_VPD_change_vs_original_hPa=round(new-V,8),
     full_original_episode_HH=len(source),
     full_episode_science_gate=item["science_gate"],
     original_FLUXMET_ZIP_SHA256=ziphash[site],
     science_status="RESEARCH_ONLY_FULL_ORIGINAL_SOURCE_EVENT",
     production_forcing_authorization="NO"))
 # No claims of science closure based only on data QC.
 summary=[]
 for site in SITES:
  rr=[r for r in outputs if r["site"]==site]
  er=[r for r in rr if r["method"]=="SOURCE_ERA_ALL_EPISODE"]
  md=[r for r in rr if r["method"]=="SOURCE_MDS_ALL_EPISODE"]
  psite=[r for r in p2 if r["site"]==site]
  status=("P2P3_ZERO_ONLY_NOT_FULL_FORCING_PASS" if not psite else
   "SOURCE_TRIAL_NOT_RUN_HIGH_PRIORITY_SITE" if site in ("US-Vcm","US-Wjs") else
   "SOURCE_REPAIR_METHOD_REVIEW_REQUIRED")
  summary.append(dict(site=site,
   source_original_P2P3_unapproved_HH=len(psite),
   source_original_P2P3_events=len({r["episode_id"] for r in psite}),
   source_ZIP_archive_SHA256=ziphash.get(site,"NOT_SCANNED"),
   exact_native_HH_verified_against_original_ZIP=sum(
     len(group[site,eid]) for eid in {r["episode_id"] for r in psite}) if site in trial_sites else 0,
   number_of_full_episode_trials=len(rr),
   full_episode_ERA_review_candidates=sum(x["science_gate"]=="NUMERIC_CANDIDATE_REVIEW_NO_SCIENCE_APPROVAL" for x in er),
   full_episode_MDS_review_candidates=sum(x["science_gate"]=="NUMERIC_CANDIDATE_REVIEW_NO_SCIENCE_APPROVAL" for x in md),
   source_original_QC0_protected_HH=sum(r["VPD_F_QC"]=="0" for r in psite),
   P1_manual_HOLD_total_batch_unchanged=46,approved166_unchanged=True,
   site_closeout_status=status))
 if sum(r["source_original_P2P3_unapproved_HH"] for r in summary)!=1574:
  raise ValueError("site summary total inconsistent")
 out.mkdir(exist_ok=False)
 wcsv(out/"stage38_ALL_SMALL_SITE_AND_VCP_FULL_EPISODE_METHOD_TRIALS.csv",ROW_FIELDS,outputs)
 wcsv(out/"stage38_RESEARCH_ONLY_FULL_SOURCE_EPISODE_NATIVE_RH_VPD_CANDIDATES.csv",TRIAL_FIELDS,native_trial)
 wcsv(out/"stage38_TEN_SITE_PROVENANCE_AND_REMAINING_REPAIR_GATES.csv",SITE_REPORT_FIELDS,summary)
 report={"source_file_hashes":{
  "Stage27_1574":digest(fp2),"Stage27_483_episodes":digest(fep),
  "Stage27_10_sites":digest(fs),"Stage24_166_approved":digest(fa),
  "Stage24_46_P1_HOLD":digest(fh),"Stage37_65_events":digest(f37),
  "Stage35_actual_429":digest(f35)},
  "original_zip_SHA256_by_site":ziphash,
  "all_sites":list(SITES),"original_P2P3_total":1574,
  "US_Vcp_original_65_episode_methods_evaluated":sum(x["site"]=="US-Vcp" for x in outputs),
  "num_original_site_method_records":len(outputs),
  "research_only_full_event_native_candidate_rows":len(native_trial),
  "full_site_forcing_science_pass_confirmed":0,
  "P1_46_HOLD_unchanged":True,"original_166_approved_unchanged":True,
  "P2P3_1574_no_new_science_approvals":True,
  "original_FLUXMET_or_DATM_or_Slurm_modified":False}
 (out/"stage38_manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 md=["# Stage38 quick science closeout: seven smaller sites + full-episode US-Vcp alternatives","",
  "**Zero production forcing changes. All original 1574 P2/P3 remain unapproved.**",
  "Read ORIGINAL AmeriFlux FLUXMET ZIP and exact source-native QC for smaller sites",
  "and all 65 Stage37 flagged original US-Vcp episodes.",
  "A separate native-row CSV contains all full-coverage, non-QC0 hypothetical RH/VPD candidates",
  "for trial-only (even if the event has boundary concerns); production authorization NO.",
  "Testing a full episode uses its every original 30-minute source anomaly, NOT",
  "only Stage36's 251 sparse half-hours. Nothing is filled/interpolated.",
  "Missing 30-minute source periods, QC0 VPD, missing RH, suspect original neighbors",
  "and new >2/>4 hPa transitions are named as distinct BLOCKERS.",
  "ERA5-Land data may cover only part of a US-Vcp episode; full method requires",
  "every ORIGINAL anomalous HH be externally referenced. Processed source ERA",
  "and ERA5-Land are reanalysis-related and not tower-observed humidity truth.","",
  "## Exact 10-site SOURCE P2/P3 and evidence status",
  "| Site | Original P2/P3 HH | Original episodes | Original ZIP source confirmed | Full ERA method trials with numeric low-risk screen | Site science status |",
  "|---|---:|---:|---|---:|---|"]
 for r in summary:
  md.append("| {} | {} | {} | {} | {} | {} |".format(
   r["site"],r["source_original_P2P3_unapproved_HH"],
   r["source_original_P2P3_events"],
   "YES" if r["source_ZIP_archive_SHA256"]!="NOT_SCANNED" else "NOT_SCANNED",
   r["full_episode_ERA_review_candidates"],r["site_closeout_status"]))
 md+=["","## Candidate trial gate totals"]
 for label,count in sorted(Counter(r["science_gate"] for r in outputs).items()):
  md.append("- **{}**: {} method×episode research trials".format(label,count))
 md+=["","## Next human science decisions",
  "1. First target small sites with original 1/15/23 HH and zero-QC0 VPD; they require fewer event-method decisions. Nothing is auto-approved.",
  "2. For US-Vcp prioritize ORIGINAL full-episode methods that generate **zero NEW** >2 or >4 hPa jumps; do NOT fill partial ERA5-Land episodes or mutate valid source QC0.",
  "3. Severe or source-QC2 neighbors should be investigated without smoothing toward bad values.",
  "4. Once event/QC evidence supports a method, a **separate explicitly approved versioned overlay** and Post-v5 tests are still required before claiming forcing ready.",
  "5. Zero identified P2/P3 in a site is not full met/forcing or model acceptance.","",
  "NO original source ZIPs, approved166, P1 HOLD46 or production DATM/Slurm were changed.",""]
 (out/"STAGE38_SMALL_SITE_AND_FULL_VCP_EVENT_CLOSURE.md").write_text("\n".join(md)+"\n")
 print("STAGE38 SUCCESS | original 10-site 1574 P2P3; 7 smaller sites + US-Vcp full-episode methods; zero forcing writes")
 for r in summary:
  print("STAGE38 SITE",r["site"],"P2P3",r["source_original_P2P3_unapproved_HH"],
    "EVENTS",r["source_original_P2P3_events"],
    "ERA_NUMERIC_REVIEW",r["full_episode_ERA_review_candidates"],
    "SOURCE_ZIP",r["source_ZIP_archive_SHA256"][:12],
    "STATUS",r["site_closeout_status"])
 print("STAGE38 FULL_EPISODE_NATIVE_RESEARCH_CANDIDATE_ROWS",len(native_trial))
 print("STAGE38 GATES",json.dumps(dict(Counter(r["science_gate"] for r in outputs)),sort_keys=True))
 print("STAGE38_REPORT="+str(out/"STAGE38_SMALL_SITE_AND_FULL_VCP_EVENT_CLOSURE.md"))
 print("STAGE38_OUT="+str(out))
 print("STAGE38 APPROVED166/P1HOLD46/P2P3_1574/FLUXMET/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

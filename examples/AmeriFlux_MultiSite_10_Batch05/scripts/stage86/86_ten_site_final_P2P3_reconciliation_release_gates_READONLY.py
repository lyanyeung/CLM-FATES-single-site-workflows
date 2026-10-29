#!/usr/bin/env python3
"""Batch05 Stage86: final ten-site SOURCE-RECONCILIATION and release gate.
No model/DATM/CIME edits, no Slurm, no production-forcing permission.
Exact Stage27 P2P3 1574, Stage63 pending 1565, Stage84 1675 approved
research version rows, Stage85 final Whs PASS source, Stage67 51 accepted
TA candidate rows/ten original-pass source transition runs and historical
P1 46 + saturated-RH-platform 10 ledgers. Classify restored source
physical consistency, data lineage, unresolved T exceptions and proxy
humidity uncertainty. Output NEW audit files under HOME only.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp",
       "US-WCr","US-Whs","US-Wjs","US-Wkg")
PREVIOUS_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
STAGE85_KEY=("US-Whs","201205260600")
# Read-original source T cases, not claims of verified model-ready T repair.
KNOWN_T={
 ("US-Wkg","202503071230"):"QC0 source T suspect before 2025-03-07 12:30",
 ("US-Wkg","202509101300"):"QC0 abrupt source T excursion",
 ("US-Vcm","201409062330"):"QC0 original T discrepant from nearby QC1",
 ("US-Wjs","202203310330"):"QC0 T spike; adjacent source T QC1",
 ("US-Wjs","202504191600"):"QC0 T spike; adjacent source T QC1",
 ("US-Vcp","200805221530"):"QC0 T spike; adjacent QC1/QC2",
 ("US-Vcp","201404262330"):"QC0 T spike; adjacent source T QC1",
}
PENDING_SITE={"US-UiD":0,"US-UMB":22,"US-UMd":15,"US-Var":62,
 "US-Vcm":362,"US-Vcp":626,"US-WCr":62,"US-Whs":1,"US-Wjs":393,"US-Wkg":22}
DISPOSITION_EXPECT={"US-UiD":(0,0),"US-UMB":(21,1),"US-UMd":(15,0),
 "US-Var":(55,7),"US-Vcm":(336,26),"US-Vcp":(582,44),
 "US-WCr":(61,1),"US-Whs":(0,1),"US-Wjs":(379,14),"US-Wkg":(19,3)}
OVERLAY_FIELDS="site native_time source_cohort decision_id source_TA_C source_TA_QC source_VPD_hPa source_VPD_QC source_RH_pct source_processed_ERA_T_C source_processed_ERA_VPD_hPa source_processed_ERA_RH_derived_pct modified_TA_C modified_RH_pct modified_VPD_hPa delta_VPD_hPa replacement_RH_provenance new_VPD_derivation source_QC_provenance_only overlay_status".split()
SITE_FIELDS="site original_P2P3_HH stage63_remaining_P2P3_HH older_approved_P2P3_HH new_RH_repaired_HH new_original_RH_passed_HH still_unclassified_P2P3_HH new_proxy_ERA_HH new_measured_QC0_donor_HH separate_Stage67_T_candidates_HH source_T_science_exceptions_HH".split()
RISK_FIELDS="site native_time category source_QC_or_method scientific_issue source_original_T_C current_versioned_T_C current_versioned_VPD_hPa corrected_or_source_RH_pct next_action".split()
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for block in iter(lambda:stream.read(1<<20),b""):h.update(block)
 return h.hexdigest()
def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def es(T):
 if T is None or not -80<=T<=60:return None
 return 6.112*math.exp(17.67*T/(T+243.5))
def rh(T,V):
 e=es(T)
 return None if e is None or V is None else 100*(1-V/e)
def fmt(v):return "" if v is None else f"{v:.9f}"
def load(p,columns):
 if not p.is_file() or p.is_symlink():raise ValueError("missing source data "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as stream:
  rd=csv.DictReader(stream);hd=rd.fieldnames or []
  if len(hd)!=len(set(hd)) or not set(columns).issubset(hd):
   raise ValueError("original report column schema drift "+str(p))
  rows=list(rd)
 if any(None in row or any(v is None for v in row.values()) for row in rows):
  raise ValueError("source report CSV inconsistent width "+str(p))
 return rows
def indexed(rows):
 d={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in d:raise ValueError("duplicate source/approval time "+str(k))
  d[k]=r
 return d
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as stream:
  w=csv.DictWriter(stream,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert sum(PENDING_SITE.values())==1565
 assert sum(v[0] for v in DISPOSITION_EXPECT.values())==1468
 assert sum(v[1] for v in DISPOSITION_EXPECT.values())==97
 assert 1468+97==1565 and 1675-1468==207 and 207==204+3
 assert 1574-1565==9 and len(KNOWN_T)==7
 assert abs(rh(0,6.112))<1e-9 and rh(0,7)<0
 print("STAGE86 SELF-TEST PASS | 10 sites P2P3 1574: original prior9 + selected1468 repaired/97 original passed; 1675 overlay includes 204 historic +3 2016 extra T")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 for x in ("stage27","stage63","stage67","stage84","stage85"):
  ap.add_argument("--"+x,type=Path)
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 ins=[getattr(a,x) for x in ("stage27","stage63","stage67","stage84","stage85")]
 if any(x is None for x in ins) or a.out is None:
  ap.error("exact Stage27/63/67/84/85 verified report dirs and NEW output needed")
 d27,d63,d67,d84,d85=(x.expanduser().resolve() for x in ins)
 out=a.out.expanduser().resolve()
 if (not all(x.is_dir() for x in (d27,d63,d67,d84,d85))
     or out.exists() or not out.parent.is_dir()
     or any(out==x or out in x.parents or x in out.parents
        for x in (d27,d63,d67,d84,d85))):
  ap.error("valid disjoint input reports and NEW output directory required")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=PREVIOUS_SHA or
     m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=PREVIOUS_SHA or
     m84.get("previous_1093_approved_rows_exactly_preserved") is not True):
  raise ValueError("actual Stage84 1675 versioned research-approved overlay SHA incorrect")
 approved=indexed(load(f84,OVERLAY_FIELDS))
 if len(approved)!=1675 or {k[0] for k in approved}-set(SITES):
  raise ValueError("latest overlay contains unrecognized or duplicated source site/time keys")
 source27=indexed(load(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",
  ["site","native_time","episode_id","TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC"]))
 remaining63=indexed(load(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv",
  ["site","native_time","episode_id","original_tier","TA_F_QC","VPD_F_QC"]))
 if (len(source27)!=1574 or len(remaining63)!=1565 or
     set(source27)-set(remaining63)!=set(source27)-set(remaining63) or
     not set(remaining63).issubset(source27) or
     {k[0] for k in source27}-set(SITES)):
  raise ValueError("original Stage27/63 P2P3 native crosswalk drift")
 f_p1=d63/"stage63_UNCHANGED_46_P1_HOLD_SOURCE_LEDGER.csv"
 f_platform=d63/"stage63_UNCHANGED_10_RH_PLATFORM_HOLD_SOURCE_LEDGER.csv"
 p1=indexed(load(f_p1,["site","native_time","hold_reason","action","latest_status"]))
 platform=indexed(load(f_platform,["site","native_time","platform","original_RH_pct","original_VPD_QC"]))
 if len(p1)!=46 or len(platform)!=10:raise ValueError("protected P1 46 / RH platform 10 source ledgers changed")
 m63=json.loads((d63/"stage63_manifest.json").read_text())
 if (m63.get("original_P2P3_HH")!=1574 or
     m63.get("remaining_original_P2P3_HH")!=1565 or
     m63.get("manual_P1_HOLD_HH")!=46 or
     m63.get("RH_plateau_science_HOLD_HH")!=10 or
     any(m63.get("outputs_sha256",{}).get(f.name)!=sha(f) for f in
       (f_p1,f_platform,d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"))):
  raise ValueError("historical Stage63 source science cohort SHA/manifest changed")
 f67=d67/"stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv"
 e67=d67/"stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv"
 h67=d67/"stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv"
 candidates=indexed(load(f67,["site","native_time","original_source_TA_F_C",
    "candidate_TA_F_C","source_QC_unchanged","source_VPD_F_hPa_unchanged"]))
 edges=load(e67,["decision","target_run_first_native","target_run_last_native"])
 holds=load(h67,["decision","target_run_first_native","target_run_last_native"])
 m67=json.loads((d67/"stage67_manifest.json").read_text())
 if (len(candidates)!=51 or len(edges)!=30 or len(holds)!=10 or
     m67.get("final_candidate_repaired_TA_HH")!=51 or
     any(m67.get("output_sha256",{}).get(f.name)!=sha(f) for f in (f67,e67,h67))
     or any(k[0]!="US-Whs" for k in candidates)):
  raise ValueError("Stage67 versioned Whs TA 51 candidates /10 prior source holds /30 edges changed")
 f85=d85/"stage85_WHS_FINAL_ONE_P2P3_SOURCE_SCIENCE_AND_STAGE67_CROSSWALK.json"
 whs=json.loads(f85.read_text())
 if (whs.get("native_time")!=STAGE85_KEY[1] or whs.get("site")!=STAGE85_KEY[0] or
     whs.get("prior_1675_approved_SHA256")!=PREVIOUS_SHA or
     whs.get("stage67_T_candidate_overlaps") is not False or
     whs.get("stage67_pass_original_run_overlaps") is not False or
     not 0<=whs.get("original_implied_RH_pct",-1)<1 or
     not whs.get("scientific_disposition","").startswith("PASS_ORIGINAL_RH_NONNEGATIVE")):
  raise ValueError("final Stage85 US-Whs source pass / no Stage67 TA collision changed")
 oldnine=set(source27)-set(remaining63)
 if len(oldnine)!=9 or not oldnine.issubset(approved):
  raise ValueError("original pre-Stage63 nine P2P3 keys must all be previously approved")
 extra_2016={("US-WCr",t) for t in ("201610010830","201610010930","201610011030")}
 if not extra_2016.issubset(set(approved)-set(source27)):
  raise ValueError("three versioned 2016 WCr extra source T context keys disappeared")
 # Confirm every Stage63 source HH is scientifically disposed by exact source
 # RH sign and exact approved overlay key. No manual blanket approval.
 bysite=defaultdict(lambda:Counter())
 original_pass=[];failed=[];methods=Counter();science=[]
 for key,base in sorted(remaining63.items()):
  t=num(base.get("TA_F_C")) # Stage63 does not expose original TA, use Stage27
  origin=source27[key]
  T,V=num(origin["TA_F_C"]),num(origin["VPD_F_hPa"])
  R=rh(T,V)
  if R is None:raise ValueError("original source P2P3 physical T/VPD cannot be reconstructed "+str(key))
  if (origin["episode_id"]!=base["episode_id"] or
      origin["TA_F_QC"]!=base["TA_F_QC"] or
      origin["VPD_F_QC"]!=base["VPD_F_QC"]):
   raise ValueError("original P2P3 Stage27/63 site/time/episode/QC crosswalk conflict "+str(key))
  bysite[key[0]]["pending"]+=1
  if key in approved:
   if R>=0:raise ValueError("source original RH nonnegative unexpectedly overwritten "+str(key))
   r=approved[key]
   if (r["source_TA_QC"]!=origin["TA_F_QC"] or
       r["source_VPD_QC"]!=origin["VPD_F_QC"] or
       num(r["source_TA_C"]) is None or num(r["source_VPD_hPa"]) is None or
       abs(num(r["source_TA_C"])-T)>.002 or
       abs(num(r["source_VPD_hPa"])-V)>.002):
    raise ValueError("approved source original TA/VPD/QC provenance drift "+str(key))
   bysite[key[0]]["repaired"]+=1
  else:
   if R<0:raise ValueError("original physically impossible RH missing approved repair "+str(key))
   bysite[key[0]]["passed"]+=1
   original_pass.append(dict(site=key[0],native_time=key[1],
    episode_id=base["episode_id"],original_TA_C=fmt(T),
    original_VPD_hPa=fmt(V),original_derived_RH_pct=fmt(R),
    original_TA_QC=origin["TA_F_QC"],original_VPD_QC=origin["VPD_F_QC"],
    science_disposition="PASS_NONNEGATIVE_ORIGINAL_RH_NOT_A_MEASURED_HUMIDITY_VALIDATION"))
 if len(original_pass)!=97 or sum(v["repaired"] for v in bysite.values())!=1468:
  raise ValueError("Batch05 original 1565 P2P3 source 1468 negative/97 nonnegative science dispositions mismatch")
 if STAGE85_KEY not in {(r["site"],r["native_time"]) for r in original_pass}:
  raise ValueError("Stage85 Whs final original pass has not reconciled")
 for site,(nneg,npass) in DISPOSITION_EXPECT.items():
  x=bysite[site]
  if (x["pending"],x["repaired"],x["passed"])!=(PENDING_SITE[site],nneg,npass):
   raise ValueError("site source-specific P2P3 science closure not exact "+site)
 # For every 1675 versioned research reconstruction, independently verify
 # stored RH(T,VPD), original delta-VPD, and retain numeric uncertainties
 # separately; a row failing these gates BLOCKS forcing release.
 physics_issues=[];unassessable=[];qc_drift=[];proxy_by_site=Counter()
 method_by_site=defaultdict(Counter)
 for key,r in sorted(approved.items()):
  method=r.get("replacement_RH_provenance","")
  methods[method]+=1;method_by_site[key[0]][method]+=1
  if "ERA" in method.upper():proxy_by_site[key[0]]+=1
  T,V,R=(num(r.get(n)) for n in ("modified_TA_C","modified_VPD_hPa","modified_RH_pct"))
  oldT,oldV=(num(r.get(n)) for n in ("source_TA_C","source_VPD_hPa"))
  delta=num(r.get("delta_VPD_hPa"))
  if any(x is None for x in (T,V,R,oldT,oldV)):
   unassessable.append((key,"missing required original/reconstructed numeric T,VPD,RH"))
   continue
  derived=rh(T,V)
  if (derived is None or not 0<=R<=100 or not -1e-7<=V or
      abs(derived-R)>0.05 or
      (delta is not None and abs((V-oldV)-delta)>0.005)):
   physics_issues.append((key,"corrected RH/VPD/T physical or delta discrepancy"))
 # Check baseline existing nine separately and compare all other Stage27
 # overlapping overlay source values; exact original QA is key.
 for key in set(approved)&set(source27):
  row=approved[key];base=source27[key]
  for va,vb in (("source_TA_C","TA_F_C"),("source_VPD_hPa","VPD_F_hPa")):
   aa,bb=num(row[va]),num(base[vb])
   if aa is None or bb is None or abs(aa-bb)>.002:
    qc_drift.append((key,"source value "+va+" differs from original Stage27"))
  if (row["source_TA_QC"]!=base["TA_F_QC"] or
      row["source_VPD_QC"]!=base["VPD_F_QC"]):
   qc_drift.append((key,"source original QC differs from Stage27"))
 # Crossover: approved Whs native T edits have a different source scope
 # than the main moisture overlay; never silently merge them.
 collision=set(candidates)&set(approved)
 stage67_phys=[]
 for key,row in candidates.items():
  proposed=num(row["candidate_TA_F_C"]);vp=num(row["source_VPD_F_hPa_unchanged"])
  proposed_RH=rh(proposed,vp)
  combined_RH=None
  if key in approved:
   combined_RH=rh(proposed,num(approved[key]["modified_VPD_hPa"]))
  if proposed_RH is None or not 0<=proposed_RH<=100 or (combined_RH is not None and not 0<=combined_RH<=100):
   stage67_phys.append((key,proposed_RH,combined_RH))
 # Historical source P1 and RH-platform holds must not be silently treated
 # as model-ready just because they appear elsewhere in an overlay.
 held_overlap_p1=set(p1)&set(approved)
 held_overlap_platform=set(platform)&set(approved)
 risks=[]
 def add_risk(key,category,note,action):
  row=approved.get(key,{})
  origin=source27.get(key,{})
  risks.append(dict(site=key[0],native_time=key[1],
   category=category,source_QC_or_method=row.get("replacement_RH_provenance",origin.get("VPD_F_QC","")),
   scientific_issue=note,source_original_T_C=row.get("source_TA_C",origin.get("TA_F_C","")),
   current_versioned_T_C=row.get("modified_TA_C",""),
   current_versioned_VPD_hPa=row.get("modified_VPD_hPa",""),
   corrected_or_source_RH_pct=row.get("modified_RH_pct",""),
   next_action=action))
 for key,reason in sorted(KNOWN_T.items()):
  add_risk(key,"UNRESOLVED_SOURCE_T_EXCEPTION",reason,
    "LOCAL_SOURCE_T_PROVENANCE_REVIEW_BEFORE_PRODUCTION_DATM")
 for key,row in sorted(p1.items()):
  add_risk(key,"P1_HISTORICAL_HOLD",row["hold_reason"],
    "SEPARATE_P1_SOURCE_SCIENCE_POLICY_OR_KEEP_UNAPPLIED")
 for key,row in sorted(platform.items()):
  add_risk(key,"RH_SATURATION_PLATFORM_HOLD",row["platform"],
    "SEPARATE_RH_PLATFORM_SOURCE_SCIENCE_POLICY_OR_KEEP_UNAPPLIED")
 for key,issue in physics_issues:
  add_risk(key,"CORRECTED_PHYSICS_FAIL",issue,"BLOCK_DATM_UNTIL_FIXED")
 for key,issue in unassessable:
  add_risk(key,"CORRECTED_PHYSICS_UNASSESSABLE",issue,"BLOCK_DATM_UNTIL_ASSESSED")
 for key,issue in qc_drift:
  add_risk(key,"ORIGINAL_SOURCE_QC_OR_VALUE_DRIFT",issue,"BLOCK_DATM_UNTIL_FIXED")
 for key,_,_ in stage67_phys:
  add_risk(key,"STAGE67_T_CANDIDATE_VPD_PHYSICS_ISSUE",
    "Stage67 candidate T with original or overlapping approved VPD is nonphysical",
    "DO_NOT_MERGE_T_CANDIDATE_UNTIL_CROSS_VARIABLE_PHYSICS_RECONCILED")
 for key in sorted(held_overlap_p1|held_overlap_platform):
  add_risk(key,"PROTECTED_HOLD_OVERLAP_IN_RESEARCH_OVERLAY",
    "Historical P1 or RH platform HOLD overlaps a research repair row",
    "RECONCILE_OLD_HOLD_PROVENANCE_BEFORE_ANY_FORCING")
 if collision:
  for key in sorted(collision):
   add_risk(key,"STAGE67_TEMP_OVERLAPS_RH_OVERLAY",
     "Both T and VPD versioned edits target same native time; separate approval",
     "CROSS_VARIABLE_REVIEW_BEFORE_ANY_MERGE")
 overview=[]
 for site in SITES:
  v=bysite[site]
  overview.append(dict(site=site,
   original_P2P3_HH=sum(k[0]==site for k in source27),
   stage63_remaining_P2P3_HH=PENDING_SITE[site],
   older_approved_P2P3_HH=sum(k[0]==site for k in oldnine),
   new_RH_repaired_HH=v["repaired"],new_original_RH_passed_HH=v["passed"],
   still_unclassified_P2P3_HH=PENDING_SITE[site]-v["repaired"]-v["passed"],
   new_proxy_ERA_HH=sum(key[0]==site and
     "ERA" in approved[key].get("replacement_RH_provenance","").upper()
     for key in set(remaining63)&set(approved)),
   new_measured_QC0_donor_HH=sum(key[0]==site and
     ("MEASURED" in approved[key].get("replacement_RH_provenance","").upper()
      or "VPD_QC0" in approved[key].get("replacement_RH_provenance","").upper())
     for key in set(remaining63)&set(approved)),
   separate_Stage67_T_candidates_HH=sum(k[0]==site for k in candidates),
   source_T_science_exceptions_HH=sum(k[0]==site for k in KNOWN_T)))
 summary=dict(stage=86,scope="Batch05 ten original AmeriFlux sites",
  original_P2P3_HH=1574,older_P2P3_approved_before_Stage63_HH=9,
  Stage63_unapproved_P2P3_HH=1565,
  Stage63_repaired_direct_negative_RH_HH=1468,
  Stage63_nonnegative_RH_pass_original_HH=97,
  Stage63_unclassified_remaining_HH=0,original_P2P3_all_dispositioned=True,
  final_versioned_research_approved_HH=1675,original_early_overlay_HH=204,
  three_extra_versioned_WCr_temperature_context_HH=3,
  Stage67_separate_approved_TA_candidate_HH=51,
  Stage67_temperature_runs_pass_original=10,
  Stage67_T_candidate_overlapping_main_overlay_HH=len(collision),
  stage67_T_candidate_original_VPD_physics_issues=len(stage67_phys),
  historical_P1_HOLD_HH=len(p1),historical_RH_platform_HOLD_HH=len(platform),
  historical_P1_HOLD_overlap_latest_overlay_HH=len(held_overlap_p1),
  historical_RH_platform_HOLD_overlap_latest_overlay_HH=len(held_overlap_platform),
  source_T_pending_science_exception_HH=len(KNOWN_T),
  current_overlay_corrected_physics_issues=len(physics_issues),
  current_overlay_numeric_unassessable=len(unassessable),
  approved_rows_source_provenance_drift_issues=len(qc_drift),
  all_method_counts=dict(methods),site_proxy_method_counts=dict(proxy_by_site),
  current_overlay_SHA256=PREVIOUS_SHA,
  source_Stage27_SHA256=sha(d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"),
  source_Stage63_SHA256=sha(d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"),
  source_Stage67_SHA256=sha(f67),source_Stage85_report_SHA256=sha(f85),
  P2P3_source_triage_done_not_production_approval=True,
  release_gate="BLOCKED_UNTIL_RH_PROXY_SOURCE_VALIDATION_P1_PLATFORM_T_EXCEPTION_STAGE67_T_PHYSICS_RECONCILED",
  original_source_unchanged=True,original_QC_unchanged=True,
  production_DATM_CIME_unchanged=True,Slurm_submitted=0)
 # Reports are created only after input SHA/scope and all source-repair joins
 # have been evaluated; originals never mutated even in exception cases.
 out.mkdir(exist_ok=False)
 fsite=out/"stage86_TEN_SITE_P2P3_FINAL_DISPOSITION_COUNTS.csv"
 fpass=out/"stage86_97_ORIGINAL_NONNEGATIVE_P2P3_PASS_UNCHANGED.csv"
 frisk=out/"stage86_FOCUSED_SOURCE_SCIENCE_AND_RELEASE_RISKS.csv"
 fmethod=out/"stage86_ALL1675_VERSIONED_REPAIR_METHOD_COUNTS.csv"
 fsum=out/"stage86_FINAL_TEN_SITE_RESEARCH_QC_RELEASE_GATES.json"
 write(fsite,SITE_FIELDS,overview)
 write(fpass,list(original_pass[0]),original_pass)
 write(frisk,RISK_FIELDS,risks)
 write(fmethod,["method","count"],[dict(method=k,count=v) for k,v in sorted(methods.items())])
 fsum.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print("STAGE86 SUCCESS | EXACT 10 SITES ORIGINAL P2P3 1574 = ORIGINAL PRIOR9 + STAGE63 1468 REPAIRED +97 NONNEGATIVE PASSED")
 print("STAGE86 APPROVED_OVERLAY 1675=204 ORIGINAL_BASELINE +1468 P2P3 NEW +3 ORIGINAL_2016_WCR_T_EXTRA")
 print("STAGE86 VERIFIED_SHA256",PREVIOUS_SHA)
 print("STAGE86 STAGE67 Whs TA candidates",len(candidates),"separate; cross-variable overlay overlaps",len(collision),
       "T-candidate original-VPD physics issues",len(stage67_phys))
 print("STAGE86 P1_HOLD",len(p1),"RH_PLATFORM_HOLD",len(platform),
       "SOURCE_T_EXCEPTIONS",len(KNOWN_T))
 print("STAGE86 PHYSICS ISSUES",len(physics_issues),"UNASSESSABLE",len(unassessable),
       "ORIGINAL_SOURCE_PROVENANCE_DRIFT",len(qc_drift))
 print("STAGE86 METHODS",json.dumps(dict(methods),sort_keys=True))
 print("STAGE86 TEN_SITE site originalP2P3 pending repaired original_pass unclassified proxyERA QC0donor")
 for rr in overview:
  print("STAGE86 SITE",rr["site"],rr["original_P2P3_HH"],
    rr["stage63_remaining_P2P3_HH"],rr["new_RH_repaired_HH"],
    rr["new_original_RH_passed_HH"],rr["still_unclassified_P2P3_HH"],
    rr["new_proxy_ERA_HH"],rr["new_measured_QC0_donor_HH"])
 print("STAGE86 RELEASE_GATE",summary["release_gate"])
 print("STAGE86_REPORTS="+str(out))
 print("STAGE86 ALL ORIGINAL/QC/APPROVED1675/STAGE67/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

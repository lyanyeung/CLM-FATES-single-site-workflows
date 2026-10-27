#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage50 — Assistant-only, READ-ONLY source-science hypotheses.

Use confirmed Stage49 70 source-ERA numeric candidates (141 native HH), and
52 original events whose unmodified source-ERA RH introduced new VPD external
jump thresholds. Test ONLY hypothetical full-original-event *constant RH
bias* adjustments to source-processed ERA, never a forced accepted repair.
A constant offset is a numerical sensitivity device, NOT a station-derived
calibration. Preserve original tower temperature and all native QC0 values,
source Stage24 166 approved/46 P1 HOLD/10 RH plateaus, and Claude 108.
Never change originals, DATM, CIME, Slurm, or claim scientific approvals.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm","US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
E49={"site","episode_id","candidate_original_HH","source_reference_science_gate",
     "new_science_approval","production_DATM_authorized"}
H49={"site","episode_id","original_HH","Stage48_rejection_reasons",
     "boundary_science_lane","new_science_approval","production_DATM_authorized"}
B49={"site","episode_id","side","candidate_native","neighbor_native",
     "original_neighbor_QC_VPD","original_neighbor_RH_pct","neighbor_kind",
     "original_VPD_jump_hPa","ERA_trial_VPD_jump_hPa","new_crossed_gt2",
     "new_crossed_gt4","production_DATM_authorized"}
B45={"site","context_kind","context_id","side","candidate_time","neighbor_time",
     "original_candidate_VPD_hPa","trial_candidate_VPD_hPa",
     "neighbor_selected_VPD_hPa","neighbor_original_QC_VPD","neighbor_kind",
     "before_jump_hPa","after_jump_hPa"}
N44={"site","native_time","episode_id","original_T_C","original_VPD_hPa",
     "source_QC_T","source_QC_VPD","source_ERA_RH_pct",
     "source_ERA_candidate_VPD_hPa","original_implied_RH_pct"}
S27={"site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC",
     "VPD_F_QC","RH_ERA_pct"}
P48={"site","episode_id","original_event_HH","science_approval"}
F48={"site","episode_id","original_HH","science_approval"}
O48={"site","episode_id","original_event_HH","auto_repaired"}
EDGE=("site","episode_id","method","source_original_HH","first_native","last_native",
      "offset_RH_percentage_points","all_original_event_HH_covered",
      "source_native_QC0_protected","source_RH_and_VPD_physical_bounds",
      "new_internal_gt2","new_internal_gt4","new_external_gt2","new_external_gt4",
      "original_external_new_gt2","original_external_new_gt4",
      "max_abs_trial_minus_source_ERA_VPD_hPa",
      "max_abs_trial_minus_original_VPD_hPa",
      "max_original_boundary_jump_hPa","max_hypothesis_boundary_jump_hPa",
      "edge_QC0_count","edge_QC1_count","source_reference_status",
      "numerical_screen_status","science_decision","production_DATM_authorized")
NATIVE=("site","episode_id","native_time","original_T_C","original_VPD_hPa",
        "original_VPD_QC","source_ERA_RH_pct","original_source_ERA_VPD_hPa",
        "hypothesis_constant_RH_offset_pp","hypothesis_RH_pct",
        "hypothesis_VPD_hPa","hypothesis_minus_original_VPD_hPa",
        "hypothesis_minus_original_ERA_VPD_hPa","science_approval",
        "production_DATM_authorized")
PRIOR=("site","episode_id","candidate_original_HH","Stage49_source_reference_gate",
       "further_evidence_required","numeric_screen_success",
       "science_approval","DATM_permission")
SITE=("site","original_P2P3_HH","Assistant_original_events",
      "Stage49_70_reference_science_pending",
      "Stage49_52_failed_original_ERA_events",
      "Stage50_exploratory_boundary_offset_numeric_feasible",
      "Stage50_alternative_numeric_not_feasible",
      "Stage50_unverifiable_boundary_source_holds",
      "original_253_neighbor_science_HOLD","Claude_108_untouched",
      "additional_science_approvals","site_full_met_forcing_pass")

def n(x):
 try:
  f=float(x)
  if math.isfinite(f) and f not in (-9999,-6999):return f
 except(TypeError,ValueError):pass
 return None
def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("original T out of physical sensitivity range")
 return 6.112*math.exp(17.67*t/(t+243.5))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def rows(p,fields):
 if not p.is_file() or p.is_symlink():raise ValueError("original prior source report missing: "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f)
  if not fields.issubset(rd.fieldnames or []) or len(rd.fieldnames or [])!=len(set(rd.fieldnames or [])):
   raise ValueError("unexpected source report columns "+str(p))
  out=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in out):
  raise ValueError("malformed original source report "+str(p))
 return out
def index(rr,fields):
 out={}
 for r in rr:
  k=tuple(r[f] for f in fields)
  if k in out:raise ValueError("duplicate source original key "+str(k))
  out[k]=r
 return out
def write(p,cols,rs):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rs)
def stamp(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid original site native 12-digit halfhour")
 return datetime.strptime(t,"%Y%m%d%H%M")
def feasible_internal(orig,new):
 """Only count jumps newly exceeding original 2/4hPa screened thresholds."""
 gt2=gt4=0
 for x,y,u,v in zip(orig,orig[1:],new,new[1:]):
  a=abs(y-x);b=abs(v-u)
  gt2+=a<=2+1e-9 and b>2+1e-9
  gt4+=a<=4+1e-9 and b>4+1e-9
 return gt2,gt4
def offset_grid():
 # Deterministic sensitivity offsets of ±20 percentage points, grid step 0.5pp.
 return [i/2 for i in range(-40,41)]
def context_gate(x):
 return "OBSERVED_QC0_REFERENCE_SCIENCE_HOLD" if x=="JUMP_TO_MEASURED_QC0_NEIGHBOR_REQUIRES_ALTERNATE_RH" else "QC1_NEIGHBOR_SOURCE_SCIENCE_HOLD"
def selftest():
 assert feasible_internal([1,1],[1,3.5])==(1,0)
 assert feasible_internal([1,1],[1,5.5])==(1,1)
 assert feasible_internal([1,1],[1,1])==(0,0)
 assert len(offset_grid())==81 and 0 in offset_grid()
 assert 70+52+253+108==483
 print("STAGE50 SELF-TEST PASS | full-event RH-offset sensitivity only, 70 source-reference queue, 52 holds, strict numeric original-edge gates; NO APPROVAL")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 for x in ("stage49-dir","stage48-dir","stage45-dir","stage44-dir","stage27-dir","out"):
  p.add_argument("--"+x,type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 keys=("stage49_dir","stage48_dir","stage45_dir","stage44_dir","stage27_dir")
 if any(getattr(a,k) is None for k in (*keys,"out")):p.error("Stage49/48/44/27 dirs and a NEW --out required")
 d49,d48,d45,d44,d27=[getattr(a,k).expanduser().resolve() for k in keys]
 out=a.out.expanduser().resolve()
 if any(not d.is_dir() for d in (d49,d48,d45,d44,d27)) or out.exists() or not out.parent.is_dir():
  p.error("source directories must exist, output must be NEW")
 if any(out==d or out in d.parents or d in out.parents for d in (d49,d48,d45,d44,d27)):
  p.error("original reports must never be overwritten")
 paths={
  "70":d49/"stage49_70_NUMERIC_CANDIDATE_EVENT_REFERENCE_QC_GATES.csv",
  "52":d49/"stage49_52_NEW_JUMP_HOLD_EVENT_PHYSICAL_DIAGNOSIS.csv",
  "edges":d49/"stage49_104_TRUE_NATIVE_BOUNDARY_BEFORE_AFTER_DETAILS.csv",
  "49site":d49/"stage49_ALL10_SITE_ASSISTANT_REMAINING_WORK.csv",
  "49manifest":d49/"stage49_manifest.json",
  "48passed":d48/"stage48_ELIGIBLE_FULL_EVENT_SOURCE_ERA_NUMERIC_GATES.csv",
  "48rejected":d48/"stage48_INITIAL122_FAILED_SCIENCE_GATE_EVENTS.csv",
  "48holds":d48/"stage48_253_ORIGINAL_NEIGHBOR_SOURCE_HOLDS.csv",
  "45edges":d45/"stage45_TRUE_ORIGINAL_EVENT_AND_JOINED_RUN_EXTERNAL_EDGES.csv",
  "44native":d44/"stage44_ALL1574_NATIVE_HH_ORIGINAL_RH_AND_ERA_MDS_FIRST_PASS.csv",
  "27original":d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"}
 s70=rows(paths["70"],E49)
 h52=rows(paths["52"],H49)
 ed104=rows(paths["edges"],B49)
 native45=rows(paths["45edges"],B45)
 site49=rows(paths["49site"],{"site","Stage46_assistant_original_events"})
 p48=rows(paths["48passed"],P48)
 f48=rows(paths["48rejected"],F48)
 oldholds=rows(paths["48holds"],O48)
 n44=rows(paths["44native"],N44)
 s27=index(rows(paths["27original"],S27),("site","native_time"))
 m49=json.loads(paths["49manifest"].read_text(encoding="utf-8"))
 if (len(s70),len(h52),len(ed104),len(site49),len(p48),len(f48),len(oldholds),len(n44),len(s27))!=(70,52,104,10,70,52,253,1574,1574):
  raise ValueError("actual Stage49/48/44/27 70/52/104/253/1574 population changed")
 if m49.get("new_scientific_approvals")!=0 or m49.get("source_DATM_CIME_Slurm_writes")!=0:
  raise ValueError("scientific source previously changed")
 allkeys=index(s70+h52+oldholds,("site","episode_id"))
 if len(allkeys)!=375:raise ValueError("Assistant 375 exact original event ownership changed")
 if len(index(s70,("site","episode_id")))!=70 or len(index(h52,("site","episode_id")))!=52:
  raise ValueError("duplicate source research event or hold")
 if len(index(ed104,("site","episode_id","side")))!=104:
  raise ValueError("source true native original edge duplicate or missing")
 original45edges=index((r for r in native45 if r["context_kind"]=="ORIGINAL_STAGE27_EVENT"),
  ("site","context_id","side"))
 if len(original45edges)!=966:
  raise ValueError("original Stage45 483 source episodes times 2 boundaries changed")
 if set(index(p48,("site","episode_id")))!=set(index(s70,("site","episode_id"))) or set(index(f48,("site","episode_id")))!=set(index(h52,("site","episode_id"))):
  raise ValueError("Stage48 native methods no longer agree with source Stage49")
 bynative=defaultdict(list)
 for r in n44:bynative[(r["site"],r["episode_id"])].append(r)
 bdy=defaultdict(dict)
 for x in ed104:
  bdy[(x["site"],x["episode_id"])][x["side"]]=x
 ranked70=[]
 for x in sorted(s70,key=lambda z:(z["site"],z["episode_id"])):
  key=x["site"],x["episode_id"]
  if x["new_science_approval"]!="NO" or x["production_DATM_authorized"]!="NO":
   raise ValueError("70 scientific candidate already approved unexpectedly")
  ranked70.append(dict(site=key[0],episode_id=key[1],candidate_original_HH=int(x["candidate_original_HH"]),
   Stage49_source_reference_gate=x["source_reference_science_gate"],
   further_evidence_required=(
    "ORIGINAL_TOWER_QC_PLUS_SEPARATE_REFERENCE_METEO_NOT_AUTOMATIC_ERA_TRUTH"
    if x["source_reference_science_gate"]=="SOURCE_ERA_ONLY_NO_MDS_REFERENCE" else
    "ORIGINAL_TOWER_QC_AND_ERA_MDS_SOURCE_DISAGREEMENT_SCIENTIFIC_REVIEW"
    if "DISAGREEMENT" in x["source_reference_science_gate"] else
    "SOURCE_TOWER_ERA_TEMPERATURE_TIMESTAMP_UNITS_AND_SENSOR_PROVENANCE"),
   numeric_screen_success=True,science_approval="NO",DATM_permission="NO"))
 alternatives=[];counterfactual_native=[]
 for x in sorted(h52,key=lambda z:(z["site"],z["episode_id"])):
  key=x["site"],x["episode_id"]
  if x["new_science_approval"]!="NO" or x["production_DATM_authorized"]!="NO":
   raise ValueError("52 hold incorrectly approved by original source")
  rs=sorted(bynative[key],key=lambda z:z["native_time"])
  edge=bdy.get(key,{})
  if len(rs)!=int(x["original_HH"]) or set(edge)!={"BEFORE","AFTER"}:
   raise ValueError("full original source event or edge missing "+str(key))
  if any(stamp(y["native_time"])-stamp(z["native_time"])!=timedelta(minutes=30) for z,y in zip(rs,rs[1:])):
   raise ValueError("unexpected original source HH clock gap; refuse to construct counterfactual "+str(key))
  Ts=[];orig=[];RH0=[];v_era=[]
  for r in rs:
   t=r["native_time"];src=s27.get((r["site"],t))
   if src is None or src["episode_id"]!=key[1]:raise ValueError("native source T/VPD/QC identity failed")
   tval=n(r["original_T_C"]);oval=n(r["original_VPD_hPa"]);RH=n(r["source_ERA_RH_pct"])
   if None in (tval,oval,RH) or not 0<=RH<=100:
    raise ValueError("source full event ERA RH and original tower T required")
   if src["VPD_F_QC"]=="0" or r["source_QC_VPD"]=="0":
    raise ValueError("never construct a hypothetical replacement for original QC0")
   if r["source_QC_T"]!=src["TA_F_QC"] or r["source_QC_VPD"]!=src["VPD_F_QC"]:
    raise ValueError("original source QC changed")
   if abs(tval-n(src["TA_F_C"]))>.002 or abs(oval-n(src["VPD_F_hPa"]))>.002 or abs(RH-n(src["RH_ERA_pct"]))>.002:
    raise ValueError("source original native T/VPD/source ERA RH changed")
   vv=sat(tval)*(1-RH/100)
   if abs(vv-n(r["source_ERA_candidate_VPD_hPa"]))>.003:
    raise ValueError("source original ERA VPD provenance changed")
   Ts.append(tval);orig.append(oval);RH0.append(RH);v_era.append(vv)
  valid_bounds=[]
  for side in ("BEFORE","AFTER"):
   e=edge[side]
   raw=original45edges.get((key[0],key[1],side))
   if raw is None:raise ValueError("original Stage45 source signed VPD edge missing "+str(key))
   if e["production_DATM_authorized"]!="NO":
    raise ValueError("boundary production approval unexpectedly present")
   old=n(e["original_VPD_jump_hPa"]);era_jump=n(e["ERA_trial_VPD_jump_hPa"])
   neighborV=n(raw["neighbor_selected_VPD_hPa"])
   orig_candidate=n(raw["original_candidate_VPD_hPa"])
   era_candidate=n(raw["trial_candidate_VPD_hPa"])
   idx=0 if side=="BEFORE" else -1
   if None in (old,era_jump,neighborV,orig_candidate,era_candidate):
    raise ValueError("original signed source VPD from Stage45 missing")
   if (e["neighbor_native"]!=raw["neighbor_time"] or
       e["candidate_native"]!=raw["candidate_time"] or
       e["original_neighbor_QC_VPD"]!=raw["neighbor_original_QC_VPD"] or
       e["neighbor_kind"]!=raw["neighbor_kind"] or
       abs(orig_candidate-orig[idx])>.002 or
       abs(era_candidate-v_era[idx])>.003 or
       abs(abs(orig_candidate-neighborV)-old)>.003 or
       abs(abs(era_candidate-neighborV)-era_jump)>.003):
    raise ValueError("Stage49/45 original signed boundary provenance mismatch "+str(key))
   if raw["neighbor_kind"] not in ("ORIGINAL_SOURCE","STAGE24_APPROVED"):
    raise ValueError("cannot fit counterfactual to unapproved source neighbor "+str(key))
   valid_bounds.append((side,e,old,era_jump,neighborV))
  old_gt2=sum(z[2]<=2<z[3] for z in valid_bounds)
  old_gt4=sum(z[2]<=4<z[3] for z in valid_bounds)
  if old_gt2+old_gt4==0:
   raise ValueError("Stage49 rejected original source ERA candidate has no new jump")
  options=[]
  for offset in offset_grid():
   rh=[v+offset for v in RH0]
   if any(v<0 or v>100 for v in rh):continue
   vals=[sat(t)*(1-r/100) for t,r in zip(Ts,rh)]
   d2,d4=feasible_internal(orig,vals)
   new2=new4=0;largest_new=0;max_worsening=0
   for side,e,old,era_jump,neighborV in valid_bounds:
    v=vals[0 if side=="BEFORE" else -1]
    jump=abs(v-neighborV)
    new2+=old<=2+1e-9 and jump>2+1e-9
    new4+=old<=4+1e-9 and jump>4+1e-9
    largest_new=max(largest_new,jump)
    max_worsening=max(max_worsening,jump-old)
   if max(abs(v-o) for v,o in zip(vals,orig))>10+1e-9:continue
   options.append((abs(offset),max_worsening,offset,vals,rh,d2,d4,
                   new2,new4,largest_new))
  feasible=[z for z in options if z[5]==0 and z[6]==0 and z[7]==0 and z[8]==0
            and z[1]<=0.5+1e-9]
  feasible.sort(key=lambda z:(z[0],z[1],z[2]))
  picked=feasible[0] if feasible else None
  lane=("NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD"
       if picked is not None else "NO_FEASIBLE_BOUNDED_EVENT_RH_OFFSET_SCIENCE_HOLD")
  if picked is not None:
   _,_,offset,vals,rh,d2,d4,new2,new4,largest_new=picked
   for r,t,o,v,v0,rrh in zip(rs,Ts,orig,vals,v_era,rh):
    counterfactual_native.append(dict(site=key[0],episode_id=key[1],
      native_time=r["native_time"],original_T_C=t,original_VPD_hPa=o,
      original_VPD_QC=r["source_QC_VPD"],source_ERA_RH_pct=n(r["source_ERA_RH_pct"]),
      original_source_ERA_VPD_hPa=round(v0,6),
      hypothesis_constant_RH_offset_pp=offset,hypothesis_RH_pct=round(rrh,6),
      hypothesis_VPD_hPa=round(v,6),hypothesis_minus_original_VPD_hPa=round(v-o,6),
      hypothesis_minus_original_ERA_VPD_hPa=round(v-v0,6),
      science_approval="NO",production_DATM_authorized="NO"))
  alternatives.append(dict(site=key[0],episode_id=key[1],
    method="EVENTWIDE_CONSTANT_RH_OFFSET_ERA_TRUE_EXTERNAL_BOUNDARY_TRIAL",
    source_original_HH=len(rs),first_native=rs[0]["native_time"],last_native=rs[-1]["native_time"],
    offset_RH_percentage_points=picked[2] if picked is not None else "",
    all_original_event_HH_covered=True,source_native_QC0_protected=True,
    source_RH_and_VPD_physical_bounds=picked is not None,
    new_internal_gt2=picked[5] if picked is not None else "",
    new_internal_gt4=picked[6] if picked is not None else "",
    new_external_gt2=picked[7] if picked is not None else "",
    new_external_gt4=picked[8] if picked is not None else "",
    original_external_new_gt2=sum(z[2]<=2<z[3] for z in valid_bounds),
    original_external_new_gt4=sum(z[2]<=4<z[3] for z in valid_bounds),
    max_abs_trial_minus_source_ERA_VPD_hPa=round(max(abs(v-w) for v,w in zip(picked[3],v_era)),6) if picked else "",
    max_abs_trial_minus_original_VPD_hPa=round(max(abs(v-w) for v,w in zip(picked[3],orig)),6) if picked else "",
    max_original_boundary_jump_hPa=max(z[2] for z in valid_bounds),
    max_hypothesis_boundary_jump_hPa=round(picked[9],6) if picked is not None else "",
    edge_QC0_count=sum(z[1]["original_neighbor_QC_VPD"]=="0" for z in valid_bounds),
    edge_QC1_count=sum(z[1]["original_neighbor_QC_VPD"]=="1" for z in valid_bounds),
    source_reference_status=context_gate(x["boundary_science_lane"]),
    numerical_screen_status=lane,science_decision="SCIENCE_HOLD_INDEPENDENT_OBSERVATIONAL_VALIDATION_REQUIRED",
    production_DATM_authorized="NO"))
 if len(alternatives)!=52 or len(ranked70)!=70:raise ValueError("52/70 original event population no longer conserved")
 for r in alternatives:
  if r["production_DATM_authorized"]!="NO":
   raise ValueError("counterfactual must never be production approved")
  if r["numerical_screen_status"]=="NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD" and any(
    r[k]!=0 for k in ("new_internal_gt2","new_internal_gt4","new_external_gt2","new_external_gt4")):
   raise ValueError("accepted hypothetical source numeric method creates new discontinuity")
 siteout=[]
 for site in SITES:
  so=[r for r in site49 if r["site"]==site]
  if len(so)!=1:raise ValueError("ten site source evidence missing "+site)
  x=so[0]
  ea=[r for r in alternatives if r["site"]==site]
  pa=[r for r in ranked70 if r["site"]==site]
  ho=[r for r in oldholds if r["site"]==site]
  siteout.append(dict(site=site,original_P2P3_HH="",Assistant_original_events=int(x["Stage46_assistant_original_events"]),
   Stage49_70_reference_science_pending=len(pa),Stage49_52_failed_original_ERA_events=len(ea),
   Stage50_exploratory_boundary_offset_numeric_feasible=sum(r["numerical_screen_status"]=="NUMERIC_EVENTWIDE_BOUNDARIES_POSSIBLE_SCIENCE_HOLD" for r in ea),
   Stage50_alternative_numeric_not_feasible=sum(r["numerical_screen_status"]=="NO_FEASIBLE_BOUNDED_EVENT_RH_OFFSET_SCIENCE_HOLD" for r in ea),
   Stage50_unverifiable_boundary_source_holds=0,
   original_253_neighbor_science_HOLD=len(ho),Claude_108_untouched=True,
   additional_science_approvals=0,site_full_met_forcing_pass=False))
 if sum(r["Assistant_original_events"] for r in siteout)!=375:
  raise ValueError("Assistant source events not 375")
 out.mkdir(exist_ok=False)
 write(out/"stage50_70_SOURCE_REFERENCE_SCIENCE_PRIORITY.csv",PRIOR,ranked70)
 write(out/"stage50_52_EVENTWIDE_RH_OFFSET_FULL_NATIVE_BOUNDARY_RESEARCH_ONLY.csv",EDGE,alternatives)
 write(out/"stage50_EVENTWIDE_COUNTERFACTUAL_NATIVE_SOURCE_NO_FORCING.csv",NATIVE,counterfactual_native)
 write(out/"stage50_TEN_SITE_ASSISTANT_HOLD_AND_EVIDENCE_COUNTS.csv",SITE,siteout)
 metadata=dict(original_input_SHA256={k:sha(v) for k,v in paths.items()},
  candidate_70_numerical_source_events=70,candidate_native_141_HH_prior_source=True,
  original_jump_method_HOLD_events=52,original_other_neighbor_HOLD_events=253,
  counterfactual_source_native_HH=len(counterfactual_native),
  external_true_boundary_signed_VPD_checked_from_original_Stage45=True,
  new_science_approvals=0,Claude_108_unchanged=True,
  existing_166_approved_46_P1_HOLD_10_RH_platform_1574_P2P3_protected=True,
  original_FLUXMET_DATM_CIME_Slurm_modified=False)
 (out/"stage50_manifest.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n")
 md=["# Stage50 — Batch05 Assistant 70 provenance priorities, 52 RH offset exploratory sensitivities",
 "**NO official forcing changes; ALL 52 original source methods stay HOLD.**",
 "Source-processed ERA is not an independent measurement. A constant event-wide RH offset is only an uncalibrated mathematical sensitivity.",
 "Stage50 checks signed original neighbor VPD from Stage45, paired with Stage49 true native boundaries; even a numerically safe hypothesis is NOT station-grounded scientific approval.",
 "","## 70 original ERA source candidates — independent source evidence gaps"]
 for g,nn in sorted(Counter(x["Stage49_source_reference_gate"] for x in ranked70).items()):
  md.append("- {}: {} events".format(g,nn))
 md+=["","## 52 original ERA source new external jump holds — full-event source-native boundary sensitivity"]
 for g,nn in sorted(Counter(x["numerical_screen_status"] for x in alternatives).items()):
  md.append("- {}: {} original events".format(g,nn))
 md+=["","These full-event offset sensitivities use exact Stage45 signed neighbor VPD; they are artificial numerical hypotheses, not evidence of correct tower RH. Preserve approved Stage24 and observed QC0.","",
  "Never infer changes to Claude Track B: 108 separate original high-risk events remain untouched.",
  "Existing Stage24 approved 166, original P1 held 46, RH plateau 10, and source P2P3 unapproved 1574 all unchanged.",
  "Source SCIENTIFIC APPROVALS NEW: 0; Official DATM writes: 0."]
 (out/"STAGE50_ASSISTANT_REFERENCE_SCIENCE_AND_EVENTWIDE_OFFSET_LIMITS.md").write_text("\n".join(md)+"\n")
 print("STAGE50 SUCCESS | 70 source-reference pending; 52 original-new-jump HOLD, full-event source-native boundary sensitivity, 253 neighbor source holds; zero approvals")
 print("STAGE50 LOW_RISK_REFERENCE",json.dumps(dict(Counter(r["Stage49_source_reference_gate"] for r in ranked70)),sort_keys=True))
 print("STAGE50 RH_OFFSET_BOUNDARY_SENSITIVITY",json.dumps(dict(Counter(r["numerical_screen_status"] for r in alternatives)),sort_keys=True))
 print("STAGE50_OUT="+str(out))
 print("STAGE50 SOURCE/DATM/CIME/SLURM UNCHANGED CLAUDE108 UNTOUCHED")
if __name__=="__main__":main()

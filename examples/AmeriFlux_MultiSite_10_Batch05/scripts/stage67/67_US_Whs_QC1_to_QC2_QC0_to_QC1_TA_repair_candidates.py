#!/usr/bin/env python3
"""Stage67: US-Whs operator-selected original TA_F jump repairs, research overlay only.

Examine only Stage66 native 30-minute jumps >= 5 C with source lineage
1->2 (fill contiguous QC2 run between QC1 anchors) OR
0->1 (fill contiguous QC1 run between QC0-measured anchors).
Never recode source TA_F_QC. Never touch source, 204 RH/VPD overlay, VPD,
production DATM/CIME or submit Slurm. If the requested QC bracket is missing,
too long, or numerically creates another discontinuity, retain a science HOLD.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from datetime import datetime
from collections import Counter

SITE="US-Whs"
ZIP_NAME="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1.zip"
MEMBER="AMF_US-Whs_FLUXNET_FLUXMET_HH_2007-2025_v1.3_r1.csv"
ZIP_SHA="0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767"
MAX_RUN_HH=12 # At most 6h of 30-min missing/fill points, never interpolate across long data gaps.
RULES={("1","2"):"QC1_TO_QC2_INTERPOLATE_QC1_ANCHORS",
       ("0","1"):"QC0_TO_QC1_INTERPOLATE_QC0_ANCHORS"}
EV=("event_id","boundary_before_native","boundary_after_native",
    "original_TA_jump_C","source_transition","repair_target_QC","required_anchor_QC",
    "target_run_first_native","target_run_last_native","target_run_HH",
    "before_anchor_native","after_anchor_native","before_anchor_TA_C",
    "after_anchor_TA_C","original_max_abs_TA_jump_C_on_run_edges",
    "candidate_max_abs_TA_jump_C_on_run_edges","run_proposed_TA_HH",
    "decision","reason","operator_method_status","production_DATM_permission")
CO=("site","native_time","source_run_id","source_trigger_native","source_QC_unchanged",
    "original_source_TA_F_C","candidate_TA_F_C","candidate_minus_original_C",
    "source_TA_ERA_C","left_donor_native","left_donor_QC","left_donor_TA_C",
    "right_donor_native","right_donor_QC","right_donor_TA_C",
    "source_VPD_F_hPa_unchanged","source_VPD_F_QC_unchanged",
    "interpolation_method","source_science_status","DATM_permission")

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as fh:
  for b in iter(lambda:fh.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def num(v):
 try:
  f=float(v)
  return f if math.isfinite(f) and f not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None

def stamp(v):
 if len(v)!=12 or not v.isdigit():raise ValueError("bad original native timestamp "+repr(v))
 return datetime.strptime(v,"%Y%m%d%H%M")

def read(path,required):
 if not path.is_file() or path.is_symlink():
  raise ValueError("original immutable Stage66 report absent "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f)
  hd=rd.fieldnames or []
  if not set(required).issubset(hd) or len(set(hd))!=len(hd):
   raise ValueError("original Stage66 report schema drift "+str(path))
  rr=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rr):
  raise ValueError("malformed original Stage66 CSV "+str(path))
 return rr

def write(path,cols,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  writer=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  writer.writeheader();writer.writerows(rows)

def verify_stage66(stage_dir):
 f=stage_dir/"stage66_US_Whs_ALL_YEARS_original_TA_30min_jumps_ge3C.csv"
 m=stage_dir/"stage66_manifest.json"
 ms=json.loads(m.read_text())
 if (ms.get("site")!=SITE or ms.get("original_sha256")!=ZIP_SHA or
     ms.get("source_30min_jumps_ge5C")!=282 or
     ms.get("source_QC0_TA_observed")!=296559 or
     ms.get("source_QC1_MDS_fill")!=1609 or
     ms.get("source_QC2_processed_ERA_fill")!=34952 or
     ms.get("report_sha256")!=sha(f) or
     ms.get("original_source_or_QC_reclassified") is not False or
     ms.get("original_204_overlay_modified") is not False):
  raise ValueError("actual Stage66 QC/source manifest identity or SHA mismatch")
 rr=read(f,("before_native","after_native","before_QC","after_QC",
            "jump_TA_C","abs_jump_C","QC_transition",
            "before_TA","after_TA"))
 relevant=[r for r in rr if num(r["abs_jump_C"]) is not None and
            num(r["abs_jump_C"])>=5-1e-8 and
            (r["before_QC"],r["after_QC"]) in RULES]
 counts=Counter((r["before_QC"],r["after_QC"]) for r in relevant)
 if counts!=Counter({("1","2"):4,("0","1"):26}):
  raise ValueError("Stage66 requested original 1->2=4 and 0->1=26 changed: "+repr(counts))
 if len({r["after_native"] for r in relevant})!=30:
  raise ValueError("duplicate selected native jump times")
 return f, relevant

def source_stream(package):
 rows=[]
 with zipfile.ZipFile(package) as z:
  matches=[x for x in z.infolist() if Path(x.filename).name==MEMBER]
  if len(matches)!=1 or matches[0].file_size>900*1024*1024:
   raise ValueError("original source FLUXMET HH member missing, nonunique or oversize")
  with z.open(matches[0]) as f:
   with io.TextIOWrapper(f,encoding="utf-8-sig",newline="") as handle:
    rd=csv.DictReader(handle)
    cols=rd.fieldnames or []
    required={"TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC"}
    if not required.issubset(cols) or len(set(cols))!=len(cols):
     raise ValueError("original source CSV fields missing/duplicate")
    prev=None
    for r in rd:
     t=r["TIMESTAMP_START"]
     dt=stamp(t)
     if prev is not None:
      if dt<=prev:raise ValueError("source HH timestamps out of order")
     prev=dt
     rows.append({"t":t,"dt":dt,"ta":num(r["TA_F"]),"qc":r["TA_F_QC"],
                  "era":num(r["TA_ERA"]),"vpd":num(r["VPD_F"]),
                  "vpdqc":r["VPD_F_QC"]})
 if len(rows)!=333120:
  raise ValueError("US-Whs exact original source 333120 HH changed")
 return rows

def synth_interpolate(start,end,rr,max_hh=MAX_RUN_HH):
 """Given first target index (right after left anchor), exact consecutive QC run."""
 if not (0<start<len(rr)-1):raise ValueError("bad source target run")
 left=rr[start-1]
 target_qc=rr[start]["qc"]
 donor_qc=left["qc"]
 j=start
 while j<len(rr) and rr[j]["qc"]==target_qc:
  if j and (rr[j]["dt"]-rr[j-1]["dt"]).total_seconds()!=1800:
   return [],"GAP_IN_ORIGINAL_TARGET_RUN",start,j
  j+=1
 run=rr[start:j]
 right=rr[j] if j<len(rr) else None
 if right is None or right["qc"]!=donor_qc:
  return [],"NOT_BRACKETED_BY_TWO_REQUIRED_QC"+donor_qc+"_ANCHORS",start,j
 if (rr[start]["dt"]-left["dt"]).total_seconds()!=1800 or (
     right["dt"]-rr[j-1]["dt"]).total_seconds()!=1800:
  return [],"ORIGINAL_SOURCE_CLOCK_GAP",start,j
 if len(run)>max_hh:
  return [],"OVER_"+str(max_hh)+"_HALF_HOUR_DONOR_QC_BRACKET",start,j
 if any(x["ta"] is None for x in [left,right]+run):
  return [],"MISSING_NATIVE_SOURCE_TA_OR_ANCHOR",start,j
 if any(x["qc"]!=target_qc for x in run):
  return [],"UNEXPECTED_TARGET_QC_INSIDE_RUN",start,j
 if abs(right["ta"]-left["ta"])/(len(run)+1)>=5:
  return [],"INTERPOLATION_ITSELF_WOULD_CREATE_GE5C_STEP",start,j
 if min(left["ta"],right["ta"])< -80 or max(left["ta"],right["ta"])>60:
  return [],"INVALID_QC_DONOR_TEMPERATURE",start,j
 cand=[left["ta"]+(right["ta"]-left["ta"])*k/(len(run)+1)
       for k in range(1,len(run)+1)]
 return cand,"VALID_TWO_SIDED_SAME_QC_LINEAR_INTERPOLATION",start,j

def selftest():
 a=[
  dict(t="202001010000",dt=stamp("202001010000"),ta=20.,qc="1"),
  dict(t="202001010030",dt=stamp("202001010030"),ta=10.,qc="2"),
  dict(t="202001010100",dt=stamp("202001010100"),ta=9.,qc="2"),
  dict(t="202001010130",dt=stamp("202001010130"),ta=23.,qc="1")]
 o,msg,s,j=synth_interpolate(1,3,a)
 assert msg=="VALID_TWO_SIDED_SAME_QC_LINEAR_INTERPOLATION" and o==[21.,22.] and j==3
 b=[dict(x) for x in a]
 b[0]["qc"]="0";b[1]["qc"]="1";b[2]["qc"]="1";b[3]["qc"]="0"
 o,msg,s,j=synth_interpolate(1,3,b)
 assert o==[21.,22.]
 b[3]["qc"]="2"
 o,msg,s,j=synth_interpolate(1,3,b)
 assert not o and msg.startswith("NOT_BRACKETED_")
 assert len(RULES)==2 and num("-9999") is None
 print("STAGE67 SELF-TEST PASS | 1->2 use bounded QC1 anchors; 0->1 use bounded QC0; fail closed on gap/long/QC conflict; no originals modified")

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage66-dir",type=Path)
 ap.add_argument("--out",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 a=ap.parse_args()
 if a.self_test:selftest();return
 if a.stage66_dir is None or a.out is None:
  ap.error("provide --stage66-dir and NEW --out")
 d66,root,out=(x.expanduser().resolve() for x in (a.stage66_dir,a.sites_root,a.out))
 if (not d66.is_dir() or not root.is_dir() or out.exists() or not out.parent.is_dir()
     or any(out==p or out in p.parents or p in out.parents for p in (d66,root))):
  ap.error("new report directory must be disjoint from original Stage66/source")
 f66,selected=verify_stage66(d66)
 package=root/SITE/"forcing"/"packages"/ZIP_NAME
 if package.is_symlink() or not package.is_file() or sha(package)!=ZIP_SHA:
  raise ValueError("original US-Whs ZIP SHA mismatch")
 rr=source_stream(package)
 ix={r["t"]:i for i,r in enumerate(rr)}
 if len(ix)!=len(rr):raise ValueError("original native timestamps duplicate")
 events=[];candidates=[];held=[];candidate_keys=set()
 for n,r in enumerate(sorted(selected,key=lambda x:x["after_native"]),start=1):
  b,a=r["before_native"],r["after_native"]
  before_qc,after_qc=r["before_QC"],r["after_QC"]
  if (b not in ix or a not in ix or ix[a]!=ix[b]+1 or
      (rr[ix[a]]["dt"]-rr[ix[b]]["dt"]).total_seconds()!=1800):
   raise ValueError("Stage66 exact native triggering edge missing "+a)
  x,y=rr[ix[b]],rr[ix[a]]
  actual=y["ta"]-x["ta"] if x["ta"] is not None and y["ta"] is not None else None
  if (actual is None or abs(actual-num(r["jump_TA_C"]))>.002 or
      x["qc"]!=before_qc or y["qc"]!=after_qc or
      abs(x["ta"]-num(r["before_TA"]))>.002 or
      abs(y["ta"]-num(r["after_TA"]))>.002 or
      abs(actual)<5):
   raise ValueError("original Stage66 selected QC/time/TA source drift "+a)
  if (before_qc,after_qc) not in RULES:raise ValueError("not authorized QC transition")
  vals,status,start,end=synth_interpolate(ix[a],len(rr),rr)
  # synth_interpolate extends the entire contiguous *target* QC block.
  left=rr[start-1];right=rr[end] if end<len(rr) else None
  target=rr[start:end]
  decision="VERSIONED_TA_INTERPOLATION_CANDIDATE" if vals else "SOURCE_REVIEW_HOLD"
  if vals and any(t["t"] in candidate_keys for t in target):
   raise ValueError("overlapping original repair runs; refuse duplicate proposal")
  edge_before=abs(target[0]["ta"]-left["ta"]) if target and target[0]["ta"] is not None and left["ta"] is not None else None
  edge_after=abs(right["ta"]-target[-1]["ta"]) if right and target and right["ta"] is not None and target[-1]["ta"] is not None else None
  oldmax=max((q for q in (edge_before,edge_after) if q is not None),default=None)
  newmax=abs(right["ta"]-left["ta"])/(len(target)+1) if vals and right and len(target)>0 else None
  eid="WHS_STAGE67_"+str(n).zfill(3)
  events.append(dict(event_id=eid,boundary_before_native=b,boundary_after_native=a,
   original_TA_jump_C=f"{actual:.6f}",source_transition=before_qc+"->"+after_qc,
   repair_target_QC=after_qc,required_anchor_QC=before_qc,
   target_run_first_native=target[0]["t"] if target else "",
   target_run_last_native=target[-1]["t"] if target else "",
   target_run_HH=len(target),before_anchor_native=left["t"],
   after_anchor_native=right["t"] if right else "",
   before_anchor_TA_C=left["ta"] if left["ta"] is not None else "",
   after_anchor_TA_C=right["ta"] if right and right["ta"] is not None else "",
   original_max_abs_TA_jump_C_on_run_edges="" if oldmax is None else f"{oldmax:.6f}",
   candidate_max_abs_TA_jump_C_on_run_edges="" if newmax is None else f"{newmax:.6f}",
   run_proposed_TA_HH=len(vals),decision=decision,reason=status,
   operator_method_status="USER_SELECTED_RULE_NOT_PRODUCTION_AUTHORIZATION",
   production_DATM_permission="NO"))
  if not vals:
   held.append(events[-1]);continue
  for t,value in zip(target,vals):
   candidate_keys.add(t["t"])
   candidates.append(dict(site=SITE,native_time=t["t"],source_run_id=eid,
    source_trigger_native=a,source_QC_unchanged=t["qc"],
    original_source_TA_F_C=f"{t['ta']:.6f}",candidate_TA_F_C=f"{value:.6f}",
    candidate_minus_original_C=f"{value-t['ta']:.6f}",
    source_TA_ERA_C="" if t["era"] is None else f"{t['era']:.6f}",
    left_donor_native=left["t"],left_donor_QC=left["qc"],
    left_donor_TA_C=f"{left['ta']:.6f}",right_donor_native=right["t"],
    right_donor_QC=right["qc"],right_donor_TA_C=f"{right['ta']:.6f}",
    source_VPD_F_hPa_unchanged="" if t["vpd"] is None else f"{t['vpd']:.6f}",
    source_VPD_F_QC_unchanged=t["vpdqc"],interpolation_method=RULES[(before_qc,after_qc)],
    source_science_status="RESEARCH_CANDIDATE_REQUIRES_MOISTURE_AND_PHYSICS_REVIEW",
    DATM_permission="NO"))
 if len(events)!=30 or len(held)+sum(e["decision"]=="VERSIONED_TA_INTERPOLATION_CANDIDATE" for e in events)!=30:
  raise ValueError("30 source transition coverage/reconciliation error")
 if any(rr[ix[r["native_time"]]]["qc"]!=r["source_QC_unchanged"] for r in candidates):
  raise ValueError("candidate original QC changed")
 if any((r["left_donor_QC"],r["source_QC_unchanged"],r["right_donor_QC"]) not in
      (("1","2","1"),("0","1","0")) for r in candidates):
  raise ValueError("candidate donor QC provenance violated")
 out.mkdir(exist_ok=False)
 f_events=out/"stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv"
 f_cand=out/"stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv"
 f_hold=out/"stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv"
 write(f_events,EV,events)
 write(f_cand,CO,candidates)
 write(f_hold,EV,held)
 byrule={}
 for rule in ("1->2","0->1"):
  group=[e for e in events if e["source_transition"]==rule]
  byrule[rule]=dict(triggered=len(group),
   candidate_runs=sum(e["decision"]=="VERSIONED_TA_INTERPOLATION_CANDIDATE" for e in group),
   hold_runs=sum(e["decision"]=="SOURCE_REVIEW_HOLD" for e in group),
   candidate_HH=sum(e["run_proposed_TA_HH"] for e in group))
 man=dict(site=SITE,Stage66_source_SHA256=sha(f66),original_ZIP_SHA256=ZIP_SHA,
  selected_transitions_1_to_2=4,selected_transitions_0_to_1=26,
  original_jump_threshold_ge5C=True,max_interpolation_target_run_HH=MAX_RUN_HH,
  original_source_QC0_protected=True,original_source_QC1_QC2_provenance_preserved=True,
  operator_selected_strategy=byrule,final_candidate_repaired_TA_HH=len(candidates),
  scientifically_approved_for_production=False,
  source_TA_F_or_QC_modified=False,source_VPD_F_modified=False,
  existing_204_RH_VPD_overlay_modified=False,DATM_CIME_modified=False,
  Slurm_jobs_submitted=0,
  output_sha256={f.name:sha(f) for f in (f_events,f_cand,f_hold)})
 (out/"stage67_manifest.json").write_text(json.dumps(man,sort_keys=True,indent=2)+"\n")
 print("STAGE67 SUCCESS | exactly 30 source>=5C targeted edges 1->2 (4), 0->1 (26)")
 print("STAGE67 RULE_STATUS",json.dumps(byrule,sort_keys=True))
 print("STAGE67 NEW_TA_RECONSTRUCTION_CANDIDATE_HH",len(candidates),
       "SCIENCE_HOLD_EDGES",len(held))
 print("STAGE67 30_EDGES | trigger_transition firsttarget targets anchors status original_edge max_new_step")
 for e in events:
  print("STAGE67 EDGE",e["boundary_after_native"],e["source_transition"],
   e["target_run_first_native"],e["target_run_HH"],e["before_anchor_native"],e["after_anchor_native"],
   e["decision"],e["reason"],e["original_TA_jump_C"],
   e["candidate_max_abs_TA_jump_C_on_run_edges"])
 print("STAGE67 MAY2012 TA_REPAIR_CANDIDATES | time QC source_TA candidate_TA delta_C")
 for r in candidates:
  if "20120524"<=r["native_time"][:8]<="20120527":
   print("STAGE67 MAY_CANDIDATE",r["native_time"],r["source_QC_unchanged"],
    r["original_source_TA_F_C"],r["candidate_TA_F_C"],r["candidate_minus_original_C"])
 print("STAGE67_REPORTS="+str(out))
 print("STAGE67 SOURCE/204/VPD/QC/DATM/CIME/SLURM UNCHANGED; NEW TA RECONSTRUCTIONS NOT PRODUCTION AUTHORIZED")
if __name__=="__main__":
 main()

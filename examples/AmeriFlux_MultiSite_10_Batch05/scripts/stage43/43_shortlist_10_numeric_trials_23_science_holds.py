#!/usr/bin/env python3
"""Stage43: original-source checked isolated 10 event/15 HH candidate shortlist.
The research preview is NOT a science-approved or DATM input.
"""
import argparse,csv,json,math
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timedelta

OK="NUMERIC_POSTV5_GATE_PASSED_SCIENCE_APPROVAL_PENDING"
def read(p,cols):
 if not p.is_file():raise ValueError("missing "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  a=csv.DictReader(f)
  if not set(cols).issubset(a.fieldnames or []):raise ValueError("missing fields "+str(p))
  return list(a)
def keyed(rows):
 d={}
 for x in rows:
  k=x["site"],x["native_time"]
  if k in d:raise ValueError("duplicate original time")
  d[k]=x
 return d
def n(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999,-6999):return v
 except(TypeError,ValueError):pass
 return None
def es(t):
 if t is None or t< -80 or t>60:raise ValueError("bad source T")
 return 6.112*math.exp(17.67*t/(243.5+t))
def save(path,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  if not rows:raise ValueError("cannot export empty review")
  w=csv.DictWriter(f,fieldnames=list(rows[0]))
  w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 for x in ("stage42-dir","stage27-dir","stage24-dir","out"):p.add_argument("--"+x,type=Path)
 a=p.parse_args()
 if a.self_test:
  assert es(0)>es(-10)
  print("STAGE43 SELF-TEST PASS | numeric selection only, no input writes")
  return
 if any(getattr(a,x) is None for x in ("stage42_dir","stage27_dir","stage24_dir","out")):p.error("input dirs and out required")
 t,v,h=[getattr(a,k).expanduser().resolve() for k in ("stage42_dir","stage27_dir","stage24_dir")]
 out=a.out.expanduser().resolve()
 if out.exists() or not out.parent.is_dir() or not all(x.is_dir() for x in (t,v,h)):p.error("new output path required")
 c=read(t/"stage42_ALL33_RESEARCH_EVENT_METHOD_QC_GATES.csv",["site","original_episode","method","science_gate","original_event_HH","candidate_native_HH"])
 nrows=read(t/"stage42_RESEARCH_ONLY_NATIVE_METHOD_CANDIDATES_NO_FORCING.csv",["site","native_time","original_episode","method","original_T_C","original_VPD_hPa","original_VPD_QC","trial_RH_water_pct","trial_VPD_hPa"])
 original=keyed(read(v/"stage27_ALL1574_paired_source_comparisons_and_risks.csv",["site","native_time","episode_id","TA_F_C","VPD_F_hPa","VPD_F_QC","RH_ERA_pct"]))
 approved=keyed(read(h/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv",["site","native_time"]))
 held=keyed(read(h/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv",["site","native_time"]))
 plateau=keyed(read(h/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv",["site","native_time"]))
 e=read(t/"stage42_POSTV5_NATIVE_BOUNDARY_ORIGINAL_VS_TRIAL.csv",["site","original_episode","method","new_jump_gt2hPa","new_jump_gt4hPa","uncertain_neighbor"])
 if (len(c),len(original),len(approved),len(held),len(plateau))!=(33,1574,166,46,10):raise ValueError("source population drift")
 expected={OK:10,"BLOCK_ORIGINAL_QC0_OR_UNCOVERED_HUMIDITY_SOURCE":9,"NEW_TRIAL_4HPA_DISCONTINUITY_HOLD":4,"SEVERE_MAGNITUDE_GT10HPA_REVIEW":4,"UNKNOWN_OR_UNAPPROVED_SOURCE_BOUNDARY_HOLD":6}
 if dict(Counter(x["science_gate"] for x in c))!=expected:raise ValueError("Stage42 gate counts changed")
 grouped=defaultdict(list)
 for r in nrows:grouped[r["site"],r["original_episode"],r["method"]].append(r)
 edges=defaultdict(list)
 for r in e:edges[r["site"],r["original_episode"],r["method"]].append(r)
 chosen=[];events=[]
 for r in c:
  if r["science_gate"]!=OK:continue
  k=r["site"],r["original_episode"],r["method"]
  rr=sorted(grouped[k],key=lambda x:x["native_time"])
  if len(rr)!=int(r["original_event_HH"]) or len(rr)!=int(r["candidate_native_HH"]) or len(edges[k])!=2:
   raise ValueError("episode coverage missing "+str(k))
  if r["method"] not in ("SOURCE_ERA","SOURCE_ERA_STAGE41"):raise ValueError("non ERA method not selected")
  for boundary in edges[k]:
   if boundary["uncertain_neighbor"]!="False" or boundary["new_jump_gt2hPa"]!="False" or boundary["new_jump_gt4hPa"]!="False":
    raise ValueError("unexpected boundary science risk")
  for x in rr:
   q=x["site"],x["native_time"]
   o=original.get(q)
   if o is None or o["episode_id"]!=k[1] or q in approved or q in held or q in plateau or x["original_VPD_QC"]=="0":
    raise ValueError("original QC/source/approved conflict")
   T=n(x["original_T_C"]);V=n(x["original_VPD_hPa"]);RH=n(x["trial_RH_water_pct"]);N=n(x["trial_VPD_hPa"])
   if None in (T,V,RH,N) or not 0<=RH<=100 or abs(N-es(T)*(1-RH/100))>.002:
    raise ValueError("invalid RH/VPD trial")
   if abs(T-n(o["TA_F_C"]))>.002 or abs(V-n(o["VPD_F_hPa"]))>.002 or x["original_VPD_QC"]!=o["VPD_F_QC"] or abs(RH-n(o["RH_ERA_pct"]))>.002:
    raise ValueError("original Stage27 source provenance changed")
   chosen.append(dict(site=q[0],native_time=q[1],episode_id=k[1],method=k[2],source_T_C=T,original_VPD_hPa=V,
    original_VPD_QC=x["original_VPD_QC"],original_implied_RH_pct=round(100*(1-V/es(T)),5),candidate_RH_pct=RH,
    hypothetical_VPD_hPa=N,change_VPD_hPa=round(N-V,6),version="STAGE43_UNAPPROVED_V1",science_approval="NO",DATM_permission="NO"))
  if any(datetime.strptime(z["native_time"],"%Y%m%d%H%M")+timedelta(minutes=30)!=datetime.strptime(y["native_time"],"%Y%m%d%H%M") for z,y in zip(rr,rr[1:])):
   raise ValueError("noncontiguous original event")
  events.append(dict(site=k[0],episode=k[1],method=k[2],native_HH=len(rr),max_abs_VPD_change_hPa=round(max(abs(float(x["trial_VPD_hPa"])-float(x["original_VPD_hPa"])) for x in rr),6),status="NUMERIC_ONLY_SCIENCE_PENDING"))
 if len(chosen)!=15 or len(events)!=10 or len(set((x["site"],x["native_time"]) for x in chosen))!=15:raise ValueError("expected 10 original events and 15 distinct HH")
 blocked=[dict(site=x["site"],episode=x["original_episode"],method=x["method"],gate=x["science_gate"],source_HH=x["original_event_HH"],decision="HOLD_FOR_SOURCE_SCIENCE") for x in c if x["science_gate"]!=OK]
 out.mkdir(exist_ok=False)
 save(out/"stage43_UNAPPROVED_15_NATIVE_ERA_CANDIDATES.csv",chosen)
 save(out/"stage43_TEN_NUMERIC_EVENTS.csv",events)
 save(out/"stage43_23_BLOCKED_METHODS.csv",blocked)
 (out/"stage43_manifest.json").write_text(json.dumps({"numeric_events":10,"unapproved_native_HH":15,"method_holds":23,"source_approved166_held46_p2p3_1574_unchanged":True,"new_forcing_writes":0},indent=2)+"\n")
 print("STAGE43 SUCCESS | 10 numeric source events, 15 unapproved candidate HH, 23 method holds")
 print("STAGE43 SITES",json.dumps(dict(Counter(x["site"] for x in chosen)),sort_keys=True))
 print("STAGE43 HOLDS",json.dumps(dict(Counter(x["gate"] for x in blocked)),sort_keys=True))
 print("STAGE43_OUTPUT="+str(out))
if __name__=="__main__":main()

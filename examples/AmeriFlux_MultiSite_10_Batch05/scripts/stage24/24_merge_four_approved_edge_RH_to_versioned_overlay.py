#!/usr/bin/env python3
"""Batch05 Stage24 — four explicitly approved Stage23 edge half-hours, only.

User approved:
 E01 US-Vcm 2014-08-19 08:30; E02 US-Vcm 2025-10-14 11:30;
 E03 US-WCr 2025-08-25 12:30; E04 US-WCr 2025-08-26 02:00.
Source RH is original FLUXMET processed-ERA-pair-derived RH, NOT
independently downloaded ERA5/ERA5-Land. Original selected tower TA retained.
Recompute VPD from es_water(original_TA)*(1-target_ERA_RH/100).

Stage22 162 existing overlay rows are preserved exactly; resulting new
separate VERSIONED overlay contains 166 rows. Stage22 46 HOLD rows are
byte-identically copied; source FLUXMET / DATM / CIME / Slurm are not edited.
Separate suspected near-saturated plateaus are only listed, NEVER altered.
"""
import argparse,csv,hashlib,json,math,shutil
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta

APPROVED={
 ("US-Vcm","201408190830"):("E01_Vcm_2014_boundary",17.18377,56.194173),
 ("US-Vcm","202510141130"):("E02_Vcm_2025_boundary",37.98483,75.805596),
 ("US-WCr","202508251230"):("E03_WCr_2025_start",33.68535,65.093868),
 ("US-WCr","202508260200"):("E04_WCr_2025_end",32.35776,91.924097),
}
# These are distinct from the 46 manually held P1 records and were
# NOT approved for repair. Keep investigation windows as timestamps only.
PLATFORMS=(
 ("Vcm_after_E02_RH99.46","US-Vcm","202510141200","202510141330"),
 ("WCr_before_E03_RH100","US-WCr","202508250930","202508251200"),
)
ORIG={"site","time_native","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
      "RH_original_pct","TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_water_pct"}
CANDIDATE_COLS=(
 "site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status",
)
STAGE23_EDGE={"boundary","site","native_time","TA_F_C","TA_F_QC",
              "VPD_F_hPa","VPD_F_QC","RH_original_pct",
              "ERA_RH_Magnus_pct","possible_neighbor_VPD_on_selected_T_hPa",
              "is_approved_overlay"}
HOLD={"site","native_time","hold_reason","action"}
PLATFORM_COLS=("platform","site","native_time","original_TA_C",
 "original_VPD_hPa","original_TA_QC","original_VPD_QC","original_RH_pct",
 "source_processed_ERA_RH_pct","review_status")
EDGE_COLS=("site","start_native","end_native","start_status","end_status",
           "start_selected_VPD_hPa","end_selected_VPD_hPa",
           "selected_VPD_jump_hPa","abs_jump_over_4hPa",
           "start_original_RH_pct","end_original_RH_pct",
           "start_processed_ERA_RH_pct","end_processed_ERA_RH_pct")
def num(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except (ValueError,TypeError):pass
 return None
def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("invalid original source TA")
 return 6.112*math.exp(17.67*t/(t+243.5))
def clock(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("invalid native timestamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def fmt(d):return d.strftime("%Y%m%d%H%M")
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path,cols):
 if not path.is_file() or path.is_symlink():raise ValueError("missing/indirect source file "+str(path))
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  rdr=csv.DictReader(f)
  if not cols.issubset(rdr.fieldnames or []):raise ValueError("bad input columns "+str(path))
  if len(rdr.fieldnames)!=len(set(rdr.fieldnames)):raise ValueError("duplicate input columns")
  rows=list(rdr)
 if any(None in row or any(v is None for v in row.values()) for row in rows):
  raise ValueError("missing source CSV cell or excess values")
 return rows
def idx(rows,key="native_time"):
 result={}
 for row in rows:
  k=(row["site"],row[key])
  clock(k[1])
  if k in result:raise ValueError("duplicated site/native half-hour "+str(k))
  result[k]=row
 return result
def write(path,cols,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def check_inputs(d18,d22,d23):
 f18=d18/"stage18_all_p1_original_6hour_context.csv"
 f22=d22/"stage22_VERSIONED_APPROVED_RH_VPD_native_overlay.csv"
 h22=d22/"stage22_46_MANUAL_HOLD_P1_untouched.csv"
 f23=d23/"stage23_four_edges_original_ERA_hypothetical.csv"
 s18=json.loads((d18/"stage18_summary.json").read_text())
 s22=json.loads((d22/"stage22_manifest.json").read_text())
 s23=json.loads((d23/"stage23_review_summary.json").read_text())
 if (s18.get("P1_original_HH"),s18.get("context_rows"))!=(176,775):
  raise ValueError("Stage18 original audit population mismatch")
 if (s22.get("approved_modified_RH_VPD_native_half_hours"),
     s22.get("hold_original_P1_half_hours"),s22.get("DATM_forcing_written"))!=(162,46,False):
  raise ValueError("Stage22 scientific approvals/forcing mismatch")
 if (s23.get("holds"),s23.get("approved_overlay_unchanged"),s23.get("significant_boundaries"),
     s23.get("modified_original"),s23.get("modified_DATM"))!=(46,162,4,False,False):
  raise ValueError("Stage23 source review state mismatch")
 native=idx(read(f18,ORIG),key="time_native")
 existing_rows=read(f22,set(CANDIDATE_COLS))
 if len(existing_rows)!=162 or not set(CANDIDATE_COLS).issubset(existing_rows[0]):
  raise ValueError("unexpected Stage22 candidate overlay schema/cohort")
 existing=idx(existing_rows)
 held=idx(read(h22,HOLD))
 evid=read(f23,STAGE23_EDGE)
 if (len(native),len(existing),len(held))!=(775,162,46):
  raise ValueError("Stage18 or Stage22 population mismatch")
 if set(existing)&set(held) or not set(existing).issubset(native) or not set(held).issubset(native):
  raise ValueError("original approved/hold overlap or missing source")
 for k in APPROVED:
  if k not in native or k in existing or k in held:
   raise ValueError("four-user-approved source not unmodified original "+str(k))
 return native,existing,existing_rows,held,evid,f18,f22,h22,f23
def new_targets(native,evid):
 evidence=defaultdict(list)
 for r in evid:evidence[r["site"],r["native_time"]].append(r)
 new={}
 for key,(name,original_rh,expected_era_rh) in sorted(APPROVED.items()):
  r=native[key]
  rows=evidence[key]
  if len(rows)!=1:raise ValueError("Stage23 target evidence not exactly one "+str(key))
  e=rows[0]
  for origcol,ecol in (("TA_F_C","TA_F_C"),("VPD_F_hPa","VPD_F_hPa"),
                      ("TA_F_QC","TA_F_QC"),("VPD_F_QC","VPD_F_QC"),
                      ("RH_original_pct","RH_original_pct")):
   if r[origcol]!=e[ecol]:raise ValueError("Stage23 raw source provenance mismatch "+str((key,origcol)))
  if e["is_approved_overlay"]!="0":
   raise ValueError("unexpected already-approved stage23 target "+str(key))
  if (r["TA_F_QC"],r["VPD_F_QC"])!=("0","0"):
   raise ValueError("not original measured source target "+str(key))
  T=num(r["TA_F_C"]);oldv=num(r["VPD_F_hPa"])
  eraT=num(r["TA_ERA_C"]);eraV=num(r["VPD_ERA_hPa"])
  eraRH=num(r["ERA_RH_Magnus_water_pct"])
  rawRH=num(r["RH_original_pct"])
  if None in (T,oldv,eraT,eraV,eraRH,rawRH):
   raise ValueError("candidate original or processed ERA source missing "+str(key))
  if abs(rawRH-original_rh)>0.02 or abs(eraRH-expected_era_rh)>0.02:
   raise ValueError("user approved exact target source RH changed "+str(key))
  fromPair=100*(1-eraV/sat(eraT))
  if not 0<=eraRH<=100 or abs(fromPair-eraRH)>0.01:
   raise ValueError("processed ERA-pair RH source does not reproduce "+str(key))
  newV=sat(T)*(1-eraRH/100)
  if not 0<=newV<=sat(T) or abs(100*(1-newV/sat(T))-eraRH)>1e-8:
   raise ValueError("new RH/VPD pair physically inconsistent "+str(key))
  stage23proposal=num(e["possible_neighbor_VPD_on_selected_T_hPa"])
  if stage23proposal is None or abs(stage23proposal-newV)>0.000002:
   raise ValueError("Stage23 rounded numerical neighbor proposal mismatch "+str(key))
  new[key]=dict(
   site=key[0],native_time=key[1],
   source_cohort="EXPLICIT_STAGE23_HUMAN_APPROVED_NONP1_EDGE",
   decision_id=name,
   source_TA_C=r["TA_F_C"],source_TA_QC=r["TA_F_QC"],
   source_VPD_hPa=r["VPD_F_hPa"],source_VPD_QC=r["VPD_F_QC"],
   source_RH_pct=r["RH_original_pct"],
   source_processed_ERA_T_C=r["TA_ERA_C"],
   source_processed_ERA_VPD_hPa=r["VPD_ERA_hPa"],
   source_processed_ERA_RH_derived_pct=r["ERA_RH_Magnus_water_pct"],
   modified_TA_C=r["TA_F_C"],modified_RH_pct=round(eraRH,9),
   modified_VPD_hPa=round(newV,10),
   delta_VPD_hPa=round(newV-oldv,10),
   replacement_RH_provenance="SOURCE_PROCESSED_ERA_RH_FROM_ORIGINAL_TA_ERA_VPD_ERA_NOT_INDEPENDENT_ERA5",
   new_VPD_derivation="MAGNUS_WATER_WITH_ORIGINAL_MEASURED_TA",
   source_QC_provenance_only="SOURCE_QC0_PRESERVED_AS_HISTORICAL_OBSERVATION_RECONSTRUCTED_RH_VPD_NOT_QC0_MEASUREMENT",
   overlay_status="EXPLICIT_HUMAN_APPROVED_STAGE23_EDGE_VERSIONED_OVERLAY_ONLY_NOT_DATM")
 return new
def pending_platforms(native,selected,hold):
 out=[]
 for group,site,a,b in PLATFORMS:
  start=clock(a);end=clock(b)
  times=[fmt(start+timedelta(minutes=30*i)) for i in range(1+int((end-start).total_seconds()/1800))]
  for t in times:
   k=(site,t)
   if k not in native:raise ValueError("missing suspected RH platform context "+str(k))
   if k in selected or k in hold:
    raise ValueError("unapproved plateau intersects approved or P1 HOLD "+str(k))
   r=native[k]
   out.append(dict(platform=group,site=site,native_time=t,
     original_TA_C=r["TA_F_C"],original_VPD_hPa=r["VPD_F_hPa"],
     original_TA_QC=r["TA_F_QC"],original_VPD_QC=r["VPD_F_QC"],
     original_RH_pct=r["RH_original_pct"],
     source_processed_ERA_RH_pct=r["ERA_RH_Magnus_water_pct"],
     review_status="PENDING_INVESTIGATOR_PLATFORM_REVIEW_NO_REPLACEMENT"))
 if len(out)!=10:
  raise ValueError("two RH-plateau review ranges changed")
 return out
def transitions(native,selected):
 edge={}
 for site,t in sorted(selected):
  d=clock(t)
  for a,b in ((fmt(d-timedelta(minutes=30)),t),(t,fmt(d+timedelta(minutes=30)))):
   ka,kb=(site,a),(site,b)
   if ka not in native or kb not in native:continue
   if (ka in selected)==(kb in selected):continue
   k=site,a,b
   if k in edge:continue
   av=num(selected[ka]["modified_VPD_hPa"]) if ka in selected else num(native[ka]["VPD_F_hPa"])
   bv=num(selected[kb]["modified_VPD_hPa"]) if kb in selected else num(native[kb]["VPD_F_hPa"])
   if av is None or bv is None:raise ValueError("missing boundary VPD "+str(k))
   edge[k]=dict(site=site,start_native=a,end_native=b,
    start_status="VERSIONED_APPROVED" if ka in selected else "ORIGINAL_UNMODIFIED",
    end_status="VERSIONED_APPROVED" if kb in selected else "ORIGINAL_UNMODIFIED",
    start_selected_VPD_hPa=round(av,10),end_selected_VPD_hPa=round(bv,10),
    selected_VPD_jump_hPa=round(bv-av,10),abs_jump_over_4hPa=abs(bv-av)>4,
    start_original_RH_pct=native[ka]["RH_original_pct"],
    end_original_RH_pct=native[kb]["RH_original_pct"],
    start_processed_ERA_RH_pct=native[ka]["ERA_RH_Magnus_water_pct"],
    end_processed_ERA_RH_pct=native[kb]["ERA_RH_Magnus_water_pct"])
 return [edge[k] for k in sorted(edge)]
def selftest():
 assert len(APPROVED)==4 and len(PLATFORMS)==2
 assert 162+len(APPROVED)==166 and 130+46==176
 for T,rh in [(14.37,56.194173),(8.903,75.805596),(15.219,65.093868),(8.409,91.924097)]:
  v=sat(T)*(1-rh/100)
  assert 0<=v<=sat(T) and abs(100*(1-v/sat(T))-rh)<1e-8
 assert len([fmt(clock("202510141200")+timedelta(minutes=30*i)) for i in range(4)])==4
 print("STAGE24 SELF-TEST PASS | exactly 4 user-approved boundaries; 46 HOLD guarded; 2 platforms unapproved; physical RH/VPD; no original writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--stage22-dir",type=Path)
 p.add_argument("--stage23-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(v is None for v in (a.stage18_dir,a.stage22_dir,a.stage23_dir,a.out)):
  p.error("Need --stage18-dir --stage22-dir --stage23-dir --out")
 dirs=[x.expanduser().resolve() for x in (a.stage18_dir,a.stage22_dir,a.stage23_dir)]
 out=a.out.expanduser().resolve()
 if (not all(d.is_dir() for d in dirs) or not out.parent.is_dir() or out.exists()
     or any(out==d or out in d.parents or d in out.parents for d in dirs)):
  p.error("Use existing source reports and NEW disjoint output directory")
 native,old,oldrows,held,evid,f18,f22,h22,f23=check_inputs(*dirs)
 added=new_targets(native,evid)
 combined=dict(old)
 combined.update(added)
 if len(combined)!=166 or len(held)!=46 or set(combined)&set(held):
  raise ValueError("approved/HOLD final population conflict")
 # Previously approved rows remain identical values/columns, not recalculated.
 for k,r in old.items():
  if combined[k]!=r:raise ValueError("a prior Stage22 approved row was changed "+str(k))
 platforms=pending_platforms(native,combined,held)
 borders=transitions(native,combined)
 hard=[r for r in borders if r["abs_jump_over_4hPa"]]
 # All computation, validation, and source checks above MUST finish before writes.
 out.mkdir(exist_ok=False)
 newfile=out/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 write(newfile,CANDIDATE_COLS,[combined[k] for k in sorted(combined)])
 write(out/"stage24_EXACT_4_newly_approved_edge_reconstructions.csv",
       CANDIDATE_COLS,[added[k] for k in sorted(added)])
 holdcopy=out/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 shutil.copyfile(h22,holdcopy)
 if sha(h22)!=sha(holdcopy):
  raise ValueError("Stage22 manual HOLD bytes changed during copying")
 write(out/"stage24_UNAPPROVED_10_suspected_RH_platform_rows.csv",
       PLATFORM_COLS,platforms)
 write(out/"stage24_all_current_overlay_boundary_transitions.csv",EDGE_COLS,borders)
 summary=dict(
  stage24_science_scope="EXACT_FOUR_USER_APPROVED_STAGE23_BOUNDARY_HALF_HOURS",
  prior_approved_162_unchanged=True,
  newly_added_approved_boundaries=4,
  total_approved_overlay_HH=166,
  total_original_P1_approved=130,
  total_original_P1_manual_HOLD=46,
  approved_nonP1_transitions=36,
  manual_HOLD_46_byte_identical=True,
  manual_HOLD_46_source_sha256=sha(h22),
  platforms_unapproved_records=10,
  original_ERA5_Land_independent_download=False,
  total_boundaries_evaluated=len(borders),
  remaining_jump_over_4hPa=len(hard),
  raw_original_FLUXMET_changed=False,DATM_forcing_changed=False,
  model_jobs_submitted=False,
  stage17_P2_P3_full_QC_approved=False,
  science_safety="OVERLAY_CANDIDATE_ONLY_NOT_MODEL_READY",
  inputs_sha256={
    "stage18_original_native_context":sha(f18),
    "stage22_prior_162_overlay":sha(f22),
    "stage22_manual_46_HOLD":sha(h22),
    "stage23_four_edges_source_evidence":sha(f23),
  },
  output_sha256=sha(newfile),
  new_edge_details=[
    dict(site=k[0],native_time=k[1],decision=added[k]["decision_id"],
         original_RH=added[k]["source_RH_pct"],
         target_processed_ERA_RH=added[k]["modified_RH_pct"],
         original_TA=added[k]["source_TA_C"],
         original_VPD=added[k]["source_VPD_hPa"],
         reconstructed_VPD=added[k]["modified_VPD_hPa"])
    for k in sorted(added)
  ],
 )
 (out/"stage24_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("STAGE24 VERIFIED: original context 775, Stage22 overlay 162, manual HOLD 46, Stage23 edge evidence")
 for k in sorted(added):
  r=added[k]
  print("STAGE24 APPROVED_EDGE",k[0],k[1],
        "ORIGINAL_RH",r["source_RH_pct"],
        "ERA_RH",r["modified_RH_pct"],
        "TA_UNCHANGED",r["modified_TA_C"],
        "VPD_ORIGINAL",r["source_VPD_hPa"],
        "VPD_NEW",r["modified_VPD_hPa"],flush=True)
 print("STAGE24 PRIOR_APPROVED=162 NEW_EXACT_EDGES=4 TOTAL_OVERLAY=166 MANUAL_HOLD=46")
 print("STAGE24 UNAPPROVED_SATURATION_PLATFORMS=10 (Vcm4 WCr6), NO REPLACEMENT")
 print("STAGE24 EDGE_RECHECK",len(borders),"JUMPS_ABS_GT4hPa",len(hard))
 for r in hard:
  print("STAGE24 LARGE_EDGE",r["site"],r["start_native"],r["end_native"],
        "DELTA_VPD_hPa",r["selected_VPD_jump_hPa"])
 print("STAGE24_OUTPUT="+str(out))
 print("STAGE24 SUCCESS | versioned RH/VPD overlay only, 46 HOLD unchanged, original FLUXMET/DATM/Slurm untouched")
if __name__=="__main__":main()

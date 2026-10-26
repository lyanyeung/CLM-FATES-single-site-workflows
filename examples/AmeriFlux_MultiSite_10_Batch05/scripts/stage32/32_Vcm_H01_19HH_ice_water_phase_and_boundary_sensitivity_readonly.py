#!/usr/bin/env python3
"""Batch05 Stage32, Vcm H01: source-SHA-pinned science decision evidence.

Uses actual Stage31 ERA5-Land 2m T / dewpoint at exact original native 19 H01
HOLD half-hours. Distinguishes saturation over ice vs liquid at ambient T,
while deriving ACTUAL vapor pressure from dewpoint saturation OVER WATER.
This is crucial: dewpoint != frost point. Separately stress-tests transporting
ERA5-Land grid relative humidity vs grid actual vapor pressure to tower T,
native-time +30-min alignment sensitivity, and pre/post original/approved
selected VPD boundaries. ALL candidates stay UNAPPROVED RESEARCH ONLY.

No network, model, source FLUXMET, existing 166 approved overlay, 46 original
P1 HOLD, 1574 unapproved P2/P3, datm/cime/slurm edits.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from collections import Counter
from datetime import datetime,timedelta

EXPECTED_PAYLOAD="abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646"
H01A="200712152100"
H01B="200712160600"
COUNT=19
REQ31={"site","native_time","candidate_UTC","original_tower_T_C",
 "original_tower_VPD_hPa","original_tower_RH","original_T_QC","original_VPD_QC",
 "original_processed_ERA_T_C","original_processed_ERA_VPD_hPa",
 "original_processed_ERA_RH_pct","ERA5L_interpolated_T_C","ERA5L_interpolated_Td_C",
 "ERA5L_RH_water_pct","ERA5L_grid_T_VPD_water_hPa",
 "ERA5L_T_minus_tower_T_C",
 "VPD_if_ERA5L_RH_carried_to_tower_T_hPa",
 "VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa",
 "reference_alignment","science_status"}
REQ18={"site","time_native","TA_F_C","VPD_F_hPa","RH_original_pct",
 "TA_F_QC","VPD_F_QC"}
REQ24={"site","native_time","source_VPD_hPa","modified_VPD_hPa","modified_TA_C"}
REQHOLD={"site","native_time","hold_reason"}
COLS=("site","native_time","candidate_UTC","original_TA_C","original_VPD_hPa",
 "original_RH","source_processed_ERA_RH_pct",
 "reference_ERA5L_T_C","reference_ERA5L_dewpoint_C",
 "ERA5L_actual_vapor_pressure_water_dewpoint_hPa",
 "ERA5L_RH_over_water_pct","ERA5L_RH_over_ice_pct",
 "ERA5L_VPD_over_water_hPa","ERA5L_VPD_over_ice_hPa",
 "ERA5L_ice_minus_water_RH_pp",
 "ERA5L_grid_RH_water_vs_source_ERA_RH_pp",
 "reference_ERA5L_minus_tower_T_C",
 "TOWER_WATER_VPD_if_reference_RH_water_preserved_hPa",
 "TOWER_WATER_VPD_if_reference_actual_e_preserved_hPa",
 "TOWER_ICE_VPD_if_reference_RH_ice_preserved_hPa",
 "TOWER_ICE_VPD_if_reference_actual_e_preserved_hPa",
 "TOWER_RH_over_water_if_reference_actual_e_preserved_pct",
 "TOWER_RH_over_ice_if_reference_actual_e_preserved_pct",
 "tower_water_VPD_two_transfer_assumptions_diff_hPa",
 "tower_ice_VPD_two_transfer_assumptions_diff_hPa",
 "reference_RH_water_next_30min_minus_current_pp",
 "reference_RH_water_previous_30min_minus_current_pp",
 "original_TA_QC","original_VPD_QC","reference_interpolation_mode",
 "supersaturated_relative_to_ice_in_grid",
 "negative_tower_VPD_with_reference_actual_e_ice",
 "science_decision")
EDGE_COLS=("site","boundary","neighbor_native","neighbor_original_VPD_hPa",
 "neighbor_current_approved_overlay_VPD_hPa","neighbor_current_selection_status",
 "h01_native","h01_reference_trial_method","h01_reference_trial_VPD_hPa",
 "candidate_selected_VPD_jump_hPa","candidate_jump_over_4hPa",
 "original_neighbor_TA_QC","original_neighbor_VPD_QC",
 "science_status")
CTXCOL=("site","native_time","original_TA_C","original_VPD_hPa",
 "original_RH_pct","original_TA_QC","original_VPD_QC",
 "current_selection_status","currently_selected_VPD_hPa",
 "is_H01_manual_hold","science_status")
PROPOSALS=("TOWER_WATER_VPD_if_reference_RH_water_preserved_hPa",
 "TOWER_WATER_VPD_if_reference_actual_e_preserved_hPa",
 "TOWER_ICE_VPD_if_reference_RH_ice_preserved_hPa",
 "TOWER_ICE_VPD_if_reference_actual_e_preserved_hPa")

def num(x):
 try:
  v=float(x)
  if math.isfinite(v) and v not in (-9999.,-6999.):return v
 except (TypeError,ValueError):pass
 return None
def dt(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad native time "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def fmt(d):return d.strftime("%Y%m%d%H%M")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
 return h.hexdigest()
def read(path,columns):
 if not path.is_file() or path.is_symlink():raise ValueError("missing or indirect original file "+str(path))
 with path.open("r",newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f)
  if not columns.issubset(rd.fieldnames or []) or len(set(rd.fieldnames or []))!=len(rd.fieldnames or []):
   raise ValueError("wrong source schema "+str(path))
  records=list(rd)
 if any(None in row or any(v is None for v in row.values()) for row in records):
  raise ValueError("malformed source report "+str(path))
 return records
def index(rows,field):
 d={}
 for r in rows:
  k=r["site"],r[field];dt(k[1])
  if k in d:raise ValueError("duplicate original native site-time "+str(k))
  d[k]=r
 return d
def sat_water(t):
 if not -80<=t<=60:raise ValueError("water saturation temperature outside range")
 return 6.112*math.exp(17.67*t/(243.5+t))
def sat_ice(t):
 if not -65<=t<=0.01:raise ValueError("ice saturation defined here only T <=0 C")
 # NPL Magnus ice formula e_i(T) in hPa:
 return 6.112*math.exp(22.46*t/(272.62+t))
def phase_row(r):
 t=num(r["ERA5L_interpolated_T_C"])
 td=num(r["ERA5L_interpolated_Td_C"])
 tower=num(r["original_tower_T_C"])
 srcERA=num(r["original_processed_ERA_RH_pct"])
 if None in (t,td,tower,srcERA):raise ValueError("H01 source/reference missing physical value")
 if max(t,td,tower)>=0 or min(t,td,tower)<-65:
  raise ValueError("H01 not fully below zero / outside ice Magnus validity")
 if num(r["original_tower_RH"]) is not None:
  raise ValueError("original manual-held native RH unexpectedly exists")
 e=sat_water(td) # ECMWF dewpoint is defined wrt liquid water, NOT frost point.
 water_t=sat_water(t)
 ice_t=sat_ice(t)
 water_tower=sat_water(tower)
 ice_tower=sat_ice(tower)
 rhw=100*e/water_t
 rhi=100*e/ice_t
 if abs(rhw-num(r["ERA5L_RH_water_pct"]))>0.003:
  raise ValueError("Stage31 original ERA5-Land water RH mismatch "+r["native_time"])
 if abs((water_t-e)-num(r["ERA5L_grid_T_VPD_water_hPa"]))>0.002:
  raise ValueError("Stage31 gridded water VPD mismatch")
 rhw_tower=e/water_tower*100
 rhi_tower=e/ice_tower*100
 tw_rh=water_tower*(1-rhw/100)
 tw_e=water_tower-e
 ti_rh=ice_tower*(1-rhi/100)
 ti_e=ice_tower-e
 if abs(tw_rh-num(r["VPD_if_ERA5L_RH_carried_to_tower_T_hPa"]))>0.003 or abs(
    tw_e-num(r["VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa"]))>0.003:
  raise ValueError("Stage31 tower-temperature alternative VPD mismatch")
 if not 0<=rhw<=100.5:
  raise ValueError("downloaded ERA5-Land unphysical RH-water")
 return dict(
  site=r["site"],native_time=r["native_time"],candidate_UTC=r["candidate_UTC"],
  original_TA_C=r["original_tower_T_C"],original_VPD_hPa=r["original_tower_VPD_hPa"],
  original_RH=r["original_tower_RH"],
  source_processed_ERA_RH_pct=srcERA,
  reference_ERA5L_T_C=t,reference_ERA5L_dewpoint_C=td,
  ERA5L_actual_vapor_pressure_water_dewpoint_hPa=round(e,9),
  ERA5L_RH_over_water_pct=round(rhw,6),ERA5L_RH_over_ice_pct=round(rhi,6),
  ERA5L_VPD_over_water_hPa=round(water_t-e,8),
  ERA5L_VPD_over_ice_hPa=round(ice_t-e,8),
  ERA5L_ice_minus_water_RH_pp=round(rhi-rhw,6),
  ERA5L_grid_RH_water_vs_source_ERA_RH_pp=round(rhw-srcERA,6),
  reference_ERA5L_minus_tower_T_C=round(t-tower,6),
  TOWER_WATER_VPD_if_reference_RH_water_preserved_hPa=round(tw_rh,8),
  TOWER_WATER_VPD_if_reference_actual_e_preserved_hPa=round(tw_e,8),
  TOWER_ICE_VPD_if_reference_RH_ice_preserved_hPa=round(ti_rh,8),
  TOWER_ICE_VPD_if_reference_actual_e_preserved_hPa=round(ti_e,8),
  TOWER_RH_over_water_if_reference_actual_e_preserved_pct=round(rhw_tower,6),
  TOWER_RH_over_ice_if_reference_actual_e_preserved_pct=round(rhi_tower,6),
  tower_water_VPD_two_transfer_assumptions_diff_hPa=round(tw_rh-tw_e,8),
  tower_ice_VPD_two_transfer_assumptions_diff_hPa=round(ti_rh-ti_e,8),
  reference_RH_water_next_30min_minus_current_pp="",
  reference_RH_water_previous_30min_minus_current_pp="",
  original_TA_QC=r["original_T_QC"],original_VPD_QC=r["original_VPD_QC"],
  reference_interpolation_mode=r["reference_alignment"],
  supersaturated_relative_to_ice_in_grid=rhi>100,
  negative_tower_VPD_with_reference_actual_e_ice=ti_e<0,
  science_decision="P1_H01_MANUAL_HOLD_UNCHANGED_NOT_APPROVED")

def load(d31,d18,d24):
 f31=d31/"stage31_H01_19_HH_EXTERNAL_ERA5L_T_TD_RH_VPD_RESEARCH_ONLY.csv"
 mf=d31/"stage31_summary.json"
 f18=d18/"stage18_all_p1_original_6hour_context.csv"
 fa=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
 fh=d24/"stage24_UNCHANGED_46_P1_MANUAL_HOLD.csv"
 m=json.loads(mf.read_text())
 m24=json.loads((d24/"stage24_manifest.json").read_text())
 if (m.get("original_CDS_file_sha256")!=EXPECTED_PAYLOAD
  or m.get("verified_source_H01_original_HOLD_half_hours")!=19
  or m.get("hourly_reference_observations")!=96
  or m.get("H01_user_HOLD_released") is not False
  or m.get("BIF_DATE_END_verified") is not False):
  raise ValueError("Stage31 original external H01 reference provenance changed")
 if m.get("original_stage18_input_sha256")!=sha(f18) or m.get("original_stage24_hold_sha256")!=sha(fh):
  raise ValueError("Stage31 source/HOLD original SHA256 changed")
 if (m24.get("total_approved_overlay_HH"),m24.get("total_original_P1_manual_HOLD"))!=(166,46):
  raise ValueError("Stage24 original science state changed")
 source=read(f31,REQ31)
 context=index(read(f18,REQ18),"time_native")
 approved=index(read(fa,REQ24),"native_time")
 held=index(read(fh,REQHOLD),"native_time")
 if len(source)!=19 or len(context)!=775 or len(approved)!=166 or len(held)!=46:
  raise ValueError("Stage31, Stage18, Stage24 original exact native cohorts mismatched")
 if set(approved)&set(held):
  raise ValueError("unapproved HOLD intersects previous approved overlay")
 ordered=sorted(source,key=lambda x:x["native_time"])
 expected=[fmt(dt(H01A)+timedelta(minutes=30*i)) for i in range(COUNT)]
 if [r["native_time"] for r in ordered]!=expected or any(r["site"]!="US-Vcm" for r in ordered):
  raise ValueError("H01 exact 19 half-hours changed")
 for r in ordered:
  k=(r["site"],r["native_time"])
  if k not in held or k not in context or k in approved:
   raise ValueError("H01 original not preserved as manual HOLD "+str(k))
  if abs(num(r["original_tower_T_C"])-num(context[k]["TA_F_C"]))>0.002 or abs(
   num(r["original_tower_VPD_hPa"])-num(context[k]["VPD_F_hPa"]))>0.002:
   raise ValueError("Stage31 original tower source vs Stage18 changed")
  if r["original_T_QC"]!=context[k]["TA_F_QC"] or r["original_VPD_QC"]!=context[k]["VPD_F_QC"]:
   raise ValueError("Stage31 original QC source changed")
 return ordered,context,approved,held,{"Stage31_exact_H01":sha(f31),
 "Stage31_manifest":sha(mf),"Stage18_original":sha(f18),
 "Stage24_original_approved_166":sha(fa),"Stage24_original_HOLD_46":sha(fh)}

def selected_source_context(context,approved,held):
 base=dt(H01A);end=dt(H01B)
 grid=[]
 for i in range(-6,COUNT+6):
  time=fmt(base+timedelta(minutes=30*i))
  k=("US-Vcm",time)
  if k not in context:continue
  r=context[k]
  v=num(r["VPD_F_hPa"])
  if k in held:
   state="P1_MANUAL_HOLD_UNAPPROVED"
   selected=""
  elif k in approved:
   state="PREVIOUSLY_USER_APPROVED_STAGE24_OVERLAY"
   selected=approved[k]["modified_VPD_hPa"]
  else:
   state="UNMODIFIED_ORIGINAL_NOT_A_NEW_APPROVAL"
   selected=v if v is not None else ""
  grid.append(dict(site="US-Vcm",native_time=time,
   original_TA_C=r["TA_F_C"],original_VPD_hPa=r["VPD_F_hPa"],
   original_RH_pct=r["RH_original_pct"],
   original_TA_QC=r["TA_F_QC"],original_VPD_QC=r["VPD_F_QC"],
   current_selection_status=state,currently_selected_VPD_hPa=selected,
   is_H01_manual_hold=H01A<=time<=H01B,
   science_status="SOURCE_CONTEXT_ONLY_NO_NEW_SCIENCE_APPROVAL"))
 return grid
def boundaries(trials,context,approved,held):
 edges=[]
 first,last=trials[0],trials[-1]
 for side,r,neighbor in (
  ("BEFORE_H01",first,fmt(dt(H01A)-timedelta(minutes=30))),
  ("AFTER_H01",last,fmt(dt(H01B)+timedelta(minutes=30)))):
  k=("US-Vcm",neighbor)
  if k not in context:raise ValueError("missing real pre/post H01 original native neighbor")
  sr=context[k]
  if k in held:
   vs=None;status="NEIGHBOR_MANUAL_HOLD_NO_BOUNDARY_APPROVAL"
  elif k in approved:
   vs=num(approved[k]["modified_VPD_hPa"])
   status="NEIGHBOR_PREVIOUS_APPROVED_STAGE24"
  else:
   vs=num(sr["VPD_F_hPa"])
   status="NEIGHBOR_UNMODIFIED_ORIGINAL"
  for method in PROPOSALS:
   trial=num(r[method])
   delta=(trial-vs if side=="BEFORE_H01" else vs-trial) if vs is not None else None
   edges.append(dict(
    site="US-Vcm",boundary=side,neighbor_native=neighbor,
    neighbor_original_VPD_hPa=sr["VPD_F_hPa"],
    neighbor_current_approved_overlay_VPD_hPa=vs if vs is not None else "",
    neighbor_current_selection_status=status,
    h01_native=r["native_time"],h01_reference_trial_method=method,
    h01_reference_trial_VPD_hPa=trial,
    candidate_selected_VPD_jump_hPa=round(delta,8) if delta is not None else "",
    candidate_jump_over_4hPa=(abs(delta)>4) if delta is not None else "",
    original_neighbor_TA_QC=sr["TA_F_QC"],
    original_neighbor_VPD_QC=sr["VPD_F_QC"],
    science_status="EXPLORATORY_BOUNDARY_NOT_USER_APPROVED"))
 return edges

def write(path,cols,records):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(records)
def selftest():
 for t in (-30,-20,-11):
  assert sat_ice(t)<sat_water(t)
  e=sat_water(t-4)
  assert (100*e/sat_ice(t))>(100*e/sat_water(t))
  assert abs(sat_water(t)*(1-(100*e/sat_water(t))/100)-(sat_water(t)-e))<1e-12
 assert int((dt(H01B)-dt(H01A)).total_seconds()/1800)+1==19
 print("STAGE32 SELF-TEST PASS | dewpoint e over WATER, reference RH over WATER vs ICE, 19 manual HOLD boundaries, zero science writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage31-dir",type=Path)
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage31_dir,a.stage18_dir,a.stage24_dir,a.out)):
  p.error("Need --stage31-dir --stage18-dir --stage24-dir --out")
 dirs=[x.expanduser().resolve() for x in (a.stage31_dir,a.stage18_dir,a.stage24_dir)]
 out=a.out.expanduser().resolve()
 if (not all(d.is_dir() for d in dirs) or out.exists() or not out.parent.is_dir()
      or any(out==d or out in d.parents or d in out.parents for d in dirs)):
  p.error("Use existing original source reports and NEW disjoint output")
 source,context,approved,held,hashes=load(*dirs)
 trials=[phase_row(r) for r in source]
 for i,r in enumerate(trials):
  if i:
   r["reference_RH_water_previous_30min_minus_current_pp"]=round(
    trials[i-1]["ERA5L_RH_over_water_pct"]-r["ERA5L_RH_over_water_pct"],6)
  if i<len(trials)-1:
   r["reference_RH_water_next_30min_minus_current_pp"]=round(
    trials[i+1]["ERA5L_RH_over_water_pct"]-r["ERA5L_RH_over_water_pct"],6)
 contexts=selected_source_context(context,approved,held)
 edges=boundaries(trials,context,approved,held)
 if len(trials)!=19 or len(edges)!=8 or sum(r["is_H01_manual_hold"] for r in contexts)!=19:
  raise ValueError("Stage32 original science population/neighbor calculation differs")
 metrics={
  "original_reference_source_H01_19":19,
  "source_ERA5L_RH_water_min":min(r["ERA5L_RH_over_water_pct"] for r in trials),
  "source_ERA5L_RH_water_max":max(r["ERA5L_RH_over_water_pct"] for r in trials),
  "source_ERA5L_RH_ice_min":min(r["ERA5L_RH_over_ice_pct"] for r in trials),
  "source_ERA5L_RH_ice_max":max(r["ERA5L_RH_over_ice_pct"] for r in trials),
  "RH_ice_minus_RH_water_max_pp":max(r["ERA5L_ice_minus_water_RH_pp"] for r in trials),
  "max_abs_ERA5L_minus_original_tower_T_C":max(abs(r["reference_ERA5L_minus_tower_T_C"]) for r in trials),
  "max_abs_RH_water_change_per_30min_pp":max(abs(r["reference_RH_water_next_30min_minus_current_pp"]) for r in trials if r["reference_RH_water_next_30min_minus_current_pp"]!=""),
  "grid_supersaturation_over_ice_HH":sum(r["supersaturated_relative_to_ice_in_grid"] for r in trials),
  "tower_e_transfer_negative_ice_VPD_HH":sum(r["negative_tower_VPD_with_reference_actual_e_ice"] for r in trials),
  "possible_non_HOLD_neighbor_boundary_trial_gt4_hPa":sum(r["candidate_jump_over_4hPa"] is True for r in edges),
  "first_last_H01_context":(H01A,H01B),
  "neighbor_native_before":fmt(dt(H01A)-timedelta(minutes=30)),
  "neighbor_native_after":fmt(dt(H01B)+timedelta(minutes=30))}
 out.mkdir(exist_ok=False)
 write(out/"stage32_H01_19_water_ice_RH_and_four_VPD_trials_UNAPPROVED.csv",COLS,trials)
 write(out/"stage32_H01_original_plus_minus3hour_source_and_overlay_context.csv",CTXCOL,contexts)
 write(out/"stage32_H01_8_boundary_method_sensitivity_checks.csv",EDGE_COLS,edges)
 summary=dict(
  stage="Batch05 Stage32 H01 real ERA5L phase and boundary sensitivity",
  source_SHA256=hashes,
  metrics=metrics,
  source_FLUXNET_hourly_alignment_uncertainty="TIMESTAMP_START is start of 30-minute averaging; CDS hourly fields may be instantaneous at exact UTC hour; 30-minute sensitivity screening is diagnostic, not validated source/ERA phase alignment",
  source_BIF_UTC_offset_minus7_DATE_END_missing=True,
  source_REANALYSIS_NOT_IN_SITU=True,
  original_source_RH_H01_missing_all_19=True,
  actual_ERA5L_dewpoint_actual_e_uses_water_saturation=True,
  relative_humidity_over_ice_uses_water_e_and_ice_T_denominator=True,
  no_RH_ice_clipping=True,
  Stage24_166_approved_untouched=True,
  P1_original_46_HOLD_untouched=True,
  P2P3_1574_science_HOLD_unchanged=True,
  new_science_approvals=0,
  original_source_or_DATM_changed=False,
  Slurm_submitted=False)
 (out/"stage32_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 md=["# Stage32: actual ERA5-Land H01 subzero humidity phase + existing source boundary evidence","",
  "**19 original US-Vcm H01 P1 half-hour manual HOLD rows remain HOLD. Zero new repairs.**",
  "ERA5-Land near-surface dewpoint is dewpoint with respect to WATER, not frost point.",
  "Compute water vapor pressure = e_sat_water(Td). Ice-based relative humidity then",
  "uses e_sat_ice(Tgrid) as denominator; **do NOT substitute e_sat_ice(Td)**.",
  "Water formulas follow the previously used Stage31 Magnus (17.67, 243.5); ice",
  "formula follows the NPL Magnus (22.46, 272.62). Different parameterisation uncertainty",
  "is smaller than the gross negative original source ERA RH discrepancy.",
  "Reference time LST->UTC uses original BIF -7 with UTC_OFFSET_DATE_END UNVERIFIED.",
  "Original native 30-min samples are period averages while ERA5-Land hourly",
  "reference points may be instantaneous; +/-30min temporal variation is a screen not a corrected alignment.",
  "The four tower VPD reconstructions are unapproved conditional sensitivity estimates,",
  "not vegetation-model-ready data.","",
  "## Computed 19 native HH statistics"]
 for k,v in metrics.items():md.append("- **"+k+"**: "+str(v))
 md+=["","## Water-versus-ice reference and tower moisture candidates",
  "| Native LST | tower T C | ERA5L T C | ERA5L Td C | ERA5L RH water % | RH ice % | grid ice VPD hPa | tower VPD water preserving grid RH hPa | tower VPD water preserving grid e hPa |",
  "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
 for r in trials:
  md.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
   r["native_time"],r["original_TA_C"],r["reference_ERA5L_T_C"],
   r["reference_ERA5L_dewpoint_C"],r["ERA5L_RH_over_water_pct"],
   r["ERA5L_RH_over_ice_pct"],r["ERA5L_VPD_over_ice_hPa"],
   r["TOWER_WATER_VPD_if_reference_RH_water_preserved_hPa"],
   r["TOWER_WATER_VPD_if_reference_actual_e_preserved_hPa"]))
 md+=["","## Boundary continuity against EXISTING Stage24 approved or unmodified original neighbors",
  "| Edge | Native neighbor | neighbor status | method | candidate VPD hPa | VPD jump hPa |",
  "|---|---|---|---|---:|---:|"]
 for r in edges:
  md.append("| {} | {} | {} | {} | {} | {} |".format(
   r["boundary"],r["neighbor_native"],
   r["neighbor_current_selection_status"],r["h01_reference_trial_method"],
   r["h01_reference_trial_VPD_hPa"],r["candidate_selected_VPD_jump_hPa"]))
 md+=["","## Scientific decision prerequisites",
  "1. Confirm BIF UTC_OFFSET_DATE_END or independent site time standard evidence; no invented DST.",
  "2. If all four candidates and reference range are physically sensible, that is **not sufficient** to release 19 source H01 HOLD entries; assess original source provenance and grid elevation.",
  "3. Compare 19 original tower TA QC, neighboring original/approved selected VPD and both alternate water/ice vapor pressure transport assumptions.",
  "4. Check meteorological supersaturation wrt ice (may occur naturally); **do not zero-clip negative ice VPD and claim it is a measured QC0 source**.",
  "5. Source RH is missing; ERA5-Land is a gridded reference and still cannot identify observed tower RH uniquely.",
  "6. Make an explicit investigator approval of any source/time-specific repair before a new Stage24 overlay version.",
  "","**SOURCE/APPROVED166/HOLD46/P2P3_1574/DATM/MODEL UNCHANGED.**",""]
 (out/"STAGE32_H01_PHASE_BOUNDARY_SCIENCE_DECISION.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE32 SUCCESS | original H01=19 HOLD, reference ice/water + 4 tower VPD trials, boundary comparisons 8; no science approvals")
 for k,v in metrics.items():print("STAGE32 METRIC",k,v)
 for r in edges:
  print("STAGE32 EDGE",r["boundary"],r["h01_reference_trial_method"],
    "TRIAL_VPD",r["h01_reference_trial_VPD_hPa"],
    "JUMP",r["candidate_selected_VPD_jump_hPa"],
    "NEIGHBOR_STATUS",r["neighbor_current_selection_status"])
 print("STAGE32_REPORT="+str(out/"STAGE32_H01_PHASE_BOUNDARY_SCIENCE_DECISION.md"))
 print("STAGE32_OUT="+str(out))
 print("STAGE32 SOURCE/APPROVED166/P1HOLD46/P2P3_1574/DATM/SLURM UNCHANGED")
if __name__=="__main__":main()

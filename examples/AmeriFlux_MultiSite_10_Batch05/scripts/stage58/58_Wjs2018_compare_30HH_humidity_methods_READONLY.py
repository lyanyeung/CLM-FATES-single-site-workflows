#!/usr/bin/env python3
"""Batch05 Stage58: compare four RESEARCH-ONLY RH restoration hypotheses for
US-Wjs March 2018 30 consecutive native HH. This never approves a repair:
  (1) 15.5-hour straight interpolation of original QC0 RH anchors
  (2) processed-source ERA RH applied at original tower TA
  (3) independently downloaded ERA5-Land grid RH at original tower TA
  (4) ERA5-Land RH + linearly interpolated tower-minus-grid anchor RH offset,
      physically clipped to [0,100], count every clip as an evidence warning.
Original selected T, VPD, QC, source-file identity and Stage56 approved 174
are strictly preserved. No edits to original FLUXMET, overlay or DATM/Slurm.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timedelta

FIRST,LAST="201803111930","201803121000"
LEFT,RIGHT="201803111900","201803121030"
METHODS=("ORIGINAL","LINEAR_RH","SOURCE_ERA_RH","ERA5LAND_RH","ERA5LAND_BIAS_CORRECTED_RH")
FIELDS=("site","native_time","role","tower_T_C","source_TA_QC",
 "original_VPD_hPa","source_VPD_QC","source_RH",
 "source_ERA_RH","independent_ERA5Land_RH",
 "linear_RH_pct","linear_VPD_hPa",
 "source_ERA_VPD_at_tower_T_hPa",
 "ERA5Land_VPD_at_tower_T_hPa",
 "ERA5Land_bias_corrected_RH_unbounded_pct",
 "ERA5Land_bias_corrected_RH_clipped_pct",
 "ERA5Land_bias_RH_clip_flag",
 "ERA5Land_bias_corrected_VPD_hPa","science_status")
STATS=("method","left_boundary_jump_hPa","right_boundary_jump_hPa",
 "largest_abs_consecutive_jump_hPa","n_jumps_gt2hPa","n_jumps_gt4hPa",
 "min_hold_VPD_hPa","max_hold_VPD_hPa","invalid_VPD_count",
 "bias_RH_clipped_HH","physical_and_boundary_screen","science_approval")

def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def clock(x):return x.strftime("%Y%m%d%H%M")
def times(a,b):
 x,y=dt(a),dt(b)
 if y<x or (y-x).total_seconds()%1800:raise ValueError("invalid time range")
 return [clock(x+timedelta(minutes=30*i)) for i in range(1+int((y-x).total_seconds()/1800))]
def num(v):
 try:
  x=float(v)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("invalid source T")
 return 6.112*math.exp(17.67*t/(243.5+t))
def from_rh(t,rh):
 return sat(t)*(1-rh/100)
def hashfile(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def csvread(p):
 if p.is_symlink() or not p.is_file():raise ValueError("missing original "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as f:
  rdr=csv.DictReader(f)
  if not rdr.fieldnames or len(set(rdr.fieldnames))!=len(rdr.fieldnames):
   raise ValueError("invalid original CSV header")
  rows=list(rdr)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed report")
 return rows
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def fmt(v):
 if v is None or v=="":return "NA"
 if isinstance(v,(int,float)):return f"{v:.3f}"
 return str(v)
def selftest():
 assert len(times(FIRST,LAST))==30
 assert len(times(LEFT,RIGHT))==32
 assert abs((dt(RIGHT)-dt(LEFT)).total_seconds()/3600-15.5)<1e-9
 assert abs(from_rh(0,100))<1e-12
 assert round(100-66.762685,6)==33.237315
 print("STAGE58 SELF-TEST PASS | 30 original HOLD HH; 4 hypothesis families; 15.5h brackets; read-only")

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage57-dir",type=Path)
 ap.add_argument("--stage56-dir",type=Path)
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if None in (a.stage57_dir,a.stage56_dir,a.out):
  ap.error("verified --stage57-dir, --stage56-dir, new --out required")
 d57,d56,out=(v.expanduser().resolve() for v in (a.stage57_dir,a.stage56_dir,a.out))
 if not d57.is_dir() or not d56.is_dir() or not out.parent.is_dir() or out.exists():
  ap.error("existing report roots and new disjoint --out required")
 if any(out==p or out in p.parents or p in out.parents for p in (d57,d56)):
  ap.error("cannot write into original reports")
 f57=d57/"stage57_34_NATIVE_HH_TOWER_VS_REAL_ERA5L_30HH_HOLD.csv"
 m57=d57/"stage57_manifest.json"
 f56=d56/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv"
 m56=d56/"stage56_manifest.json"
 src=csvread(f57)
 original=csvread(f56)
 meta57=json.loads(m57.read_text())
 meta56=json.loads(m56.read_text())
 if (len(src)!=34 or meta57.get("output_csv_SHA256")!=hashfile(f57) or
     meta57.get("actual_2018_science_HOLD_native_HH")!=30 or
     meta57.get("production_DATM_permission") is not False or
     len(original)!=174 or meta56.get("versioned_total_approved_HH")!=174 or
     meta56.get("outputs_sha256",{}).get(f56.name)!=hashfile(f56)):
  raise ValueError("Stage57/56 original data, SHA or population mismatch")
 if (meta57.get("original_source_SHA256",{}).get("stage56_original_174_sha256")!=hashfile(f56) or
     meta57.get("BIF_UTC_OFFSET_DATE_END")!="MISSING_PROVISIONAL_LST_NO_DST"):
  raise ValueError("Stage57 actual ERA5-Land provenance/clock status drift")
 bytime={}
 allowed=set(times("201803111830","201803121100"))
 held=set(times(FIRST,LAST))
 for r in src:
  t=r["native_time"]
  if r["site"]!="US-Wjs" or t in bytime or t not in allowed:
   raise ValueError("Stage57 original Wjs site/native HH mismatch")
  bytime[t]=r
  if t in held:
   if r["role"]!="HOLD_2018" or r["original_VPD_QC"]!="1" or num(r["original_source_RH_pct"]) is not None:
    raise ValueError("30-HH original science HOLD source unexpectedly changed "+t)
  elif t in (LEFT,RIGHT):
   if r["role"]!="QC0_ANCHOR" or r["original_VPD_QC"]!="0" or r["tower_T_QC"]!="0":
    raise ValueError("original measured QC0 anchors changed")
 if set(bytime)!=allowed:raise ValueError("actual 34-HH reference incomplete")
 if any(r["site"]=="US-Wjs" and r["native_time"] in held for r in original):
  raise ValueError("2018 30-HH HOLD overlaps approved 174 rows")
 l,r=bytime[LEFT],bytime[RIGHT]
 rhL,rhR=num(l["original_source_RH_pct"]),num(r["original_source_RH_pct"])
 gridL,gridR=num(l["REAL_ERA5L_RH_water_pct"]),num(r["REAL_ERA5L_RH_water_pct"])
 if any(v is None for v in (rhL,rhR,gridL,gridR)) or not (0<=rhL<=100 and 0<=rhR<=100):
  raise ValueError("original RH source anchors invalid")
 if abs(rhL-100)>.001 or abs(rhR-92.127)>.001:
  raise ValueError("Stage57 anchored source science baseline shifted")
 biasL,biasR=rhL-gridL,rhR-gridR
 print("STAGE58 SOURCE VERIFIED | original 174 overlay unchanged, 30 held original Wjs HH")
 print("STAGE58 QC0 ANCHOR BIASES RH_pp LEFT",fmt(biasL),"RIGHT",fmt(biasR),
       "LEFT_RH",fmt(rhL),"RIGHT_RH",fmt(rhR),"SPAN_HOURS 15.5")
 samples=[]
 tracks={m:{LEFT:num(l["original_VPD_hPa"]),RIGHT:num(r["original_VPD_hPa"])} for m in METHODS}
 clipcount=0
 for t in times(FIRST,LAST):
  x=bytime[t]
  T,V=num(x["tower_T_C"]),num(x["original_VPD_hPa"])
  grid,era=num(x["REAL_ERA5L_RH_water_pct"]),num(x["source_processed_ERA_RH_derived_pct"])
  if any(v is None for v in (T,V,grid,era)) or not (0<=grid<=100.5 and 0<=era<=100):
   raise ValueError("source 2018 physical input missing at "+t)
  fraction=(dt(t)-dt(LEFT)).total_seconds()/(dt(RIGHT)-dt(LEFT)).total_seconds()
  linear_rh=rhL+(rhR-rhL)*fraction
  bias=biasL+(biasR-biasL)*fraction
  rawcorrected=grid+bias
  clipped=max(0,min(100,rawcorrected))
  flag=int(abs(rawcorrected-clipped)>1e-9)
  clipcount+=flag
  calc={
   "ORIGINAL":V,
   "LINEAR_RH":from_rh(T,linear_rh),
   "SOURCE_ERA_RH":from_rh(T,era),
   "ERA5LAND_RH":from_rh(T,grid),
   "ERA5LAND_BIAS_CORRECTED_RH":from_rh(T,clipped)}
  for method,v in calc.items():tracks[method][t]=v
  samples.append(dict(site="US-Wjs",native_time=t,role="HOLD_2018_UNAPPROVED",
   tower_T_C=x["tower_T_C"],source_TA_QC=x["tower_T_QC"],
   original_VPD_hPa=x["original_VPD_hPa"],source_VPD_QC=x["original_VPD_QC"],
   source_RH=x["original_source_RH_pct"],source_ERA_RH=x["source_processed_ERA_RH_derived_pct"],
   independent_ERA5Land_RH=x["REAL_ERA5L_RH_water_pct"],
   linear_RH_pct=f"{linear_rh:.8f}",linear_VPD_hPa=f"{calc['LINEAR_RH']:.8f}",
   source_ERA_VPD_at_tower_T_hPa=f"{calc['SOURCE_ERA_RH']:.8f}",
   ERA5Land_VPD_at_tower_T_hPa=f"{calc['ERA5LAND_RH']:.8f}",
   ERA5Land_bias_corrected_RH_unbounded_pct=f"{rawcorrected:.8f}",
   ERA5Land_bias_corrected_RH_clipped_pct=f"{clipped:.8f}",
   ERA5Land_bias_RH_clip_flag=flag,
   ERA5Land_bias_corrected_VPD_hPa=f"{calc['ERA5LAND_BIAS_CORRECTED_RH']:.8f}",
   science_status="ALL_RESEARCH_ONLY_30HH_HOLD_NO_PRODUCTION_PERMISSION"))
 stats=[]
 contiguous=times(LEFT,RIGHT)
 for method in METHODS:
  v=[tracks[method][t] for t in contiguous]
  deltas=[b-a for a,b in zip(v,v[1:])]
  invalid=sum(not math.isfinite(x) or x < -1e-8 for x in v)
  maxjump=max(abs(x) for x in deltas)
  n2=sum(abs(x)>2 for x in deltas)
  n4=sum(abs(x)>4 for x in deltas)
  stats.append(dict(method=method,left_boundary_jump_hPa=f"{deltas[0]:.8f}",
    right_boundary_jump_hPa=f"{deltas[-1]:.8f}",
    largest_abs_consecutive_jump_hPa=f"{maxjump:.8f}",
    n_jumps_gt2hPa=n2,n_jumps_gt4hPa=n4,
    min_hold_VPD_hPa=f"{min(v[1:-1]):.8f}",max_hold_VPD_hPa=f"{max(v[1:-1]):.8f}",
    invalid_VPD_count=invalid,
    bias_RH_clipped_HH=clipcount if method=="ERA5LAND_BIAS_CORRECTED_RH" else 0,
    physical_and_boundary_screen="NUMERIC_ONLY_NOT_SCIENCE" if not(invalid or n2) else "BOUNDARY_OR_PHYSICAL_HOLD",
    science_approval="NO"))
 # Data comparators are NOT observations inside the 30-HH gap;
 # passing a boundary threshold never creates an approval.
 out.mkdir(exist_ok=False)
 ftable=out/"stage58_30HH_FOUR_RESEARCH_HUMIDITY_METHODS_UNAPPROVED.csv"
 fstats=out/"stage58_METHOD_BOUNDARY_AND_RH_CLIPPING_DIAGNOSTICS.csv"
 write(ftable,FIELDS,samples)
 write(fstats,STATS,stats)
 manifest=dict(original_stage57_sha256=hashfile(f57),
  original_stage56_174_sha256=hashfile(f56),original_174_unchanged=True,
  2018_original_HOLD_HH=30,scientific_approvals_new=0,
  tower_RH_sensor_validated_inside_gap=False,ERA5Land_is_grid_reanalysis=True,
  ERA5Land_RH_anchor_bias_left_pp=biasL,ERA5Land_RH_anchor_bias_right_pp=biasR,
  science_note="RH interpolation 15.5h and gridded bias-correction are not independent original tower measurements",
  original_FLUXMET_modified=False,DATM_modified=False,Slurm_jobs_submitted=0,
  outputs_sha256={ftable.name:hashfile(ftable),fstats.name:hashfile(fstats)})
 (out/"stage58_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE58 SUCCESS | 30 held HH compared, 174 original overlay SHA preserved; no approvals")
 for x in stats:
  print("STAGE58 METHOD",x["method"],"EDGE_LEFT",x["left_boundary_jump_hPa"],
        "EDGE_RIGHT",x["right_boundary_jump_hPa"],"MAX_JUMP",x["largest_abs_consecutive_jump_hPa"],
        "GT2",x["n_jumps_gt2hPa"],"GT4",x["n_jumps_gt4hPa"],"BIAS_CLIPS",x["bias_RH_clipped_HH"])
 print("nativeHH | originalVPD | sourceERArh | realERA5Lrh | LINEAR_RH VPD | SOURCE_ERA VPD | ERA5L VPD | ERA5L_biasAdjusted_VPD | bias_RH_clipped")
 for row in samples:
  print(row["native_time"],"|",row["original_VPD_hPa"],"|",fmt(num(row["source_ERA_RH"])),
    "|",fmt(num(row["independent_ERA5Land_RH"])),"|",fmt(num(row["linear_VPD_hPa"])),
    "|",fmt(num(row["source_ERA_VPD_at_tower_T_hPa"])),"|",fmt(num(row["ERA5Land_VPD_at_tower_T_hPa"])),
    "|",fmt(num(row["ERA5Land_bias_corrected_VPD_hPa"])),"|",row["ERA5Land_bias_RH_clip_flag"])
 print("STAGE58_OUT="+str(out))
 print("STAGE58 SCIENCE HOLD 30HH; no change to 174 overlay, original source or forcing")
if __name__=="__main__":main()

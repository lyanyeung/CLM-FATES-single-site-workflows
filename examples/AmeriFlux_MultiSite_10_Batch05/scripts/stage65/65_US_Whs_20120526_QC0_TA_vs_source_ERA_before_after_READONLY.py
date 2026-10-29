#!/usr/bin/env python3
"""Batch05 Stage65: Does higher-quality US-Whs tower-measured temperature
disagree with source AmeriFlux TA_ERA near 2012-05-26 06:00 native time?
Inspect immutable original FLUXMET HH ZIP; use TA_F_QC == "0" as the
source's measured (non-MDS/non-ERA) provenance screen, NOT as a
guarantee of independent instrument calibration. Compare paired
same-timestamp TA_F against product TA_ERA, especially same clock hour.
Reports ONLY. No data repair, no DATM or Slurm submission.
"""
import argparse,csv,hashlib,io,json,math,statistics,zipfile
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Whs"
TARGET="201205260600"
ARCHIVE_HASH="0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767"
PACKAGE="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1"
CSV_NAME="AMF_US-Whs_FLUXNET_FLUXMET_HH_2007-2025_v1.3_r1.csv"
BASE_COLUMNS=("native_time","date_native","hours_from_target","TA_F_C","TA_F_QC",
 "TA_ERA_C","TA_F_minus_ERA_C","TA_source_raw_C","TA_F_MDS_C","TA_F_MDS_QC",
 "SW_IN_F","P_F","WS_F","PA_F","source_measured_TA_QC0",
 "clock_time_near_target_1h","science_status")
DAY_COLUMNS=("native_date","distance_days","total_TA_F_valid_HH",
 "original_tower_TA_QC0_HH","paired_QC0_TA_vs_ERA_HH",
 "QC0_near_06h_pm1h_HH","QC0_minus_ERA_median_C",
 "QC0_minus_ERA_min_C","QC0_minus_ERA_max_C",
 "QC0_near_06h_minus_ERA_median_C",
 "TA_F_QC1_HH","TA_F_QC2_HH")
RECENT_COLUMNS=("site","native_time","distance_hours_from_target",
 "original_TA_F_C","original_TA_F_QC","source_TA_ERA_C",
 "measured_minus_source_ERA_C",
 "same_local_clock_near_06h_pm1h","context")

def digest(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):
   h.update(b)
 return h.hexdigest()

def numeric(v):
 try:
  f=float(v)
  return f if math.isfinite(f) and f not in (-9999.0,-6999.0) else None
 except (ValueError,TypeError):
  return None

def clk(s):
 if len(s)!=12 or not s.isdigit():
  raise ValueError("invalid native HH source time "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")

def csvload(path,required):
 if path.is_symlink() or not path.is_file():
  raise ValueError("original prior report missing "+str(path))
 with path.open("r",encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  cols=rd.fieldnames or []
  if not set(required).issubset(cols) or len(cols)!=len(set(cols)):
   raise ValueError("prior report schema incomplete/duplicate")
  rows=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed prior report")
 return rows

def csvwrite(path,cols,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def med(vals):
 return statistics.median(vals) if vals else None

def fmt(v):
 return "NA" if v is None else f"{v:.3f}"

def signed_hours(dt,reference):
 return (dt-reference).total_seconds()/3600

def close_clock(dt,anchor,hrs=1.0):
 return abs((dt.hour+dt.minute/60)-(anchor.hour+anchor.minute/60))<=hrs

def selftest():
 target=clk(TARGET)
 assert (target-timedelta(hours=24)).strftime("%Y%m%d%H%M")=="201205250600"
 assert close_clock(clk("201205250630"),target)
 assert not close_clock(clk("201205251230"),target)
 assert numeric("-9999") is None
 assert med([2,5,100])==5
 assert sum(abs(signed_hours(clk("201205260600"),clk(TARGET)))<1e-8 for _ in range(1))==1
 print("STAGE65 SELF-TEST PASS | US-Whs source QC0 measured TA paired with same-timestamp ERA; 30-day local date and clock controls; READ ONLY")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage64-dir",type=Path)
 p.add_argument("--sites-root",type=Path,
   default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if a.stage64_dir is None or a.out is None:
  p.error("verified --stage64-dir and NEW --out required")
 prior=a.stage64_dir.expanduser().resolve()
 root=a.sites_root.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if not prior.is_dir() or not root.is_dir() or not out.parent.is_dir() or out.exists():
  p.error("original source roots must exist; output directory must be new")
 if any(out==q or out in q.parents or q in out.parents for q in (prior,root)):
  p.error("cannot write report under any original science data folder")
 manifest_path=prior/"stage64_manifest.json"
 prior_csv=prior/"stage64_Whs_ONE_ANOMALY_ORIGINAL_3H_BEFORE_AFTER_13HH.csv"
 pm=json.loads(manifest_path.read_text())
 old=csvload(prior_csv,("site","native_time","position","TA_F_C","TA_F_QC","TA_ERA_C"))
 if (len(old)!=13 or pm.get("original_event")!=TARGET or
     pm.get("source_original_SHA256")!=ARCHIVE_HASH or
     pm.get("original_13_HH") is not True or
     pm.get("report_sha256")!=digest(prior_csv) or
     pm.get("original_FLUXMET_changed") is not False or
     pm.get("DATM_changed") is not False):
  raise ValueError("Stage64 source provenance mismatch")
 expected=[(clk(TARGET)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
           for i in range(-6,7)]
 if [r["native_time"] for r in old]!=expected or old[6]["position"]!="TARGET_HOLD":
  raise ValueError("Stage64 13 original timestamps/center drift")
 source=root/SITE/"forcing"/"packages"/(PACKAGE+".zip")
 if source.is_symlink() or not source.is_file() or digest(source)!=ARCHIVE_HASH:
  raise ValueError("US-Whs original ZIP is absent or source SHA has drifted "+str(source))
 reference=clk(TARGET)
 lo=reference-timedelta(days=120)
 hi=reference+timedelta(days=120)
 rows={}
 headers=None
 with zipfile.ZipFile(source) as z:
  matches=[i for i in z.infolist() if Path(i.filename).name==CSV_NAME]
  if len(matches)!=1 or matches[0].file_size>900*1024*1024:
   raise ValueError("original source HH member is not uniquely recoverable")
  with z.open(matches[0]) as b:
   with io.TextIOWrapper(b,encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f)
    headers=rd.fieldnames or []
    if len(set(headers))!=len(headers) or not {"TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA"}.issubset(headers):
     raise ValueError("original product lacks TA_F/TA_F_QC/TA_ERA provenance columns")
    for r in rd:
     t=r["TIMESTAMP_START"]
     if len(t)!=12 or not t.isdigit() or not (
       lo.strftime("%Y%m%d%H%M")<=t<=hi.strftime("%Y%m%d%H%M")):
      continue
     if t in rows:
      raise ValueError("duplicate original native timestamp "+t)
     rows[t]=r
 if len(rows)<13 or any(t not in rows for t in expected):
  raise ValueError("missing original center 13HH or nearby site data")
 for historic in old:
  r=rows[historic["native_time"]]
  if (r["TA_F_QC"]!=historic["TA_F_QC"] or
      abs(numeric(r["TA_F"])-numeric(historic["TA_F_C"]))>.002 or
      abs(numeric(r["TA_ERA"])-numeric(historic["TA_ERA_C"]))>.002):
   raise ValueError("SHA-pinned Stage64 original TA/ERA comparison changed "+historic["native_time"])
 original_center=rows[TARGET]
 if original_center["TA_F_QC"]!="1":
  raise ValueError("original 2012-05-26 06:00 TA QC1 expected")
 target_T=numeric(original_center["TA_F"])
 target_ERA=numeric(original_center["TA_ERA"])
 if target_T is None or target_ERA is None:
  raise ValueError("original target T or ERA missing")
 target_delta=target_T-target_ERA
 if abs(target_delta-11.489)>.002:
  raise ValueError("original verified target +11.489C difference drifted")
 selected=[]
 valid_qc0=[]
 daily=defaultdict(list)
 for t in sorted(rows):
  dt=clk(t)
  days=abs((dt.date()-reference.date()).days)
  if days>30:
   continue
  r=rows[t]
  T,E=numeric(r.get("TA_F")),numeric(r.get("TA_ERA"))
  diff=(T-E) if T is not None and E is not None else None
  qc=r.get("TA_F_QC","")
  q0=qc=="0" and T is not None
  rec=dict(native_time=t,date_native=t[:8],
   hours_from_target=f"{signed_hours(dt,reference):.1f}",
   TA_F_C=r.get("TA_F",""),TA_F_QC=qc,TA_ERA_C=r.get("TA_ERA",""),
   TA_F_minus_ERA_C="" if diff is None else f"{diff:.6f}",
   TA_source_raw_C=r.get("TA",""),TA_F_MDS_C=r.get("TA_F_MDS",""),
   TA_F_MDS_QC=r.get("TA_F_MDS_QC",""),
   SW_IN_F=r.get("SW_IN_F",""),P_F=r.get("P_F",""),
   WS_F=r.get("WS_F",""),PA_F=r.get("PA_F",""),
   source_measured_TA_QC0="YES" if q0 else "NO",
   clock_time_near_target_1h="YES" if close_clock(dt,reference) else "NO",
   science_status="SOURCE_QC0_OBS_PROVENANCE_REVIEW_ONLY" if q0 else
     "FILLED_OR_MISSING_NOT_USED_FOR_MEASURED_ERA_BIAS")
  selected.append(rec)
  daily[t[:8]].append(rec)
  if q0:
   valid_qc0.append(rec)
 dayreport=[]
 for day_index in range(-14,15):
  d=(reference.date()+timedelta(days=day_index)).strftime("%Y%m%d")
  data=daily[d]
  qc0=[r for r in data if r["source_measured_TA_QC0"]=="YES"]
  paired=[numeric(r["TA_F_minus_ERA_C"]) for r in qc0]
  paired=[q for q in paired if q is not None]
  same=[numeric(r["TA_F_minus_ERA_C"]) for r in qc0 if r["clock_time_near_target_1h"]=="YES"]
  same=[q for q in same if q is not None]
  qccount=Counter(r["TA_F_QC"] for r in data)
  dayreport.append(dict(native_date=d,distance_days=day_index,
   total_TA_F_valid_HH=sum(numeric(r["TA_F_C"]) is not None for r in data),
   original_tower_TA_QC0_HH=len(qc0),
   paired_QC0_TA_vs_ERA_HH=len(paired),
   QC0_near_06h_pm1h_HH=len(same),
   QC0_minus_ERA_median_C="" if not paired else f"{med(paired):.6f}",
   QC0_minus_ERA_min_C="" if not paired else f"{min(paired):.6f}",
   QC0_minus_ERA_max_C="" if not paired else f"{max(paired):.6f}",
   QC0_near_06h_minus_ERA_median_C="" if not same else f"{med(same):.6f}",
   TA_F_QC1_HH=qccount["1"],TA_F_QC2_HH=qccount["2"]))
 measured=sorted(valid_qc0,key=lambda r:r["native_time"])
 pre=[r for r in measured if r["native_time"]<TARGET]
 post=[r for r in measured if r["native_time"]>TARGET]
 nearby_obs=pre[-8:]+post[:8]
 sameclock=[r for r in measured if r["clock_time_near_target_1h"]=="YES"]
 sameclock.sort(key=lambda r:abs(float(r["hours_from_target"])))
 nearest_sameclock=sameclock[:16]
 target_window=[
  r for r in selected if "201205230000"<=r["native_time"]<="201205290000"
 ]
 def records(data,tag):
  return [dict(site=SITE,native_time=r["native_time"],
   distance_hours_from_target=r["hours_from_target"],
   original_TA_F_C=r["TA_F_C"],original_TA_F_QC=r["TA_F_QC"],
   source_TA_ERA_C=r["TA_ERA_C"],
   measured_minus_source_ERA_C=r["TA_F_minus_ERA_C"],
   same_local_clock_near_06h_pm1h=r["clock_time_near_target_1h"],
   context=tag) for r in data]
 recents=records(nearby_obs,"NEAREST_QC0_IN_TIME")
 samenear=records(nearest_sameclock,"NEAREST_QC0_MATCHED_LOCAL_CLOCK_PM1H")
 subsets={}
 for days in (1,3,7,14,30):
  tested=[r for r in valid_qc0 if abs(float(r["hours_from_target"]))<=24*days
          and numeric(r["TA_F_minus_ERA_C"]) is not None]
  matched=[r for r in tested if r["clock_time_near_target_1h"]=="YES"]
  dl=[numeric(r["TA_F_minus_ERA_C"]) for r in tested]
  dm=[numeric(r["TA_F_minus_ERA_C"]) for r in matched]
  subsets[str(days)]={"QC0_TA_total":len(tested),
    "QC0_minus_ERA_median_C":med(dl),
    "QC0_minus_ERA_min_C":min(dl) if dl else None,
    "QC0_minus_ERA_max_C":max(dl) if dl else None,
    "QC0_near_06h_pm1h_total":len(matched),
    "QC0_near_06h_pm1h_minus_ERA_median_C":med(dm)}
 far=[(t,r) for t,r in rows.items() if r.get("TA_F_QC")=="0"
      and numeric(r.get("TA_F")) is not None and numeric(r.get("TA_ERA")) is not None]
 pre120=[(t,r) for t,r in far if t<TARGET]
 post120=[(t,r) for t,r in far if t>TARGET]
 stat=dict(
  site=SITE,original_event=TARGET,
  original_target_TA_QC=original_center["TA_F_QC"],
  original_target_TA_F_C=target_T,
  original_target_TA_ERA_C=target_ERA,
  original_target_QC1_T_minus_source_ERA_C=target_delta,
  original_source_ZIP_SHA256=ARCHIVE_HASH,
  source_TA_F_QC0_label="AmeriFlux source-reported observed/measurement-based input, verify station instrumentation",
  source_TA_F_QC1_label="MDS/gap-fill, NOT measured",
  source_TA_F_QC2_label="source processed ERA, NOT measured",
  matched_clock_rule="same original/native local clock ±1 hour around 06:00",
  day_counts_calendar_native_date_minus14_to_plus14=len(dayreport),
  original_TA_F_QC0_in_30_days=len(valid_qc0),
  nearest_pre_QC0_120_days=pre120[-1][0] if pre120 else None,
  nearest_post_QC0_120_days=post120[0][0] if post120 else None,
  QC0_ERA_difference_by_window=subsets,
  independent_measurement_calibration_unverified=True,
  source_ERA_not_direct_station_observation=True,
  approval_new_HH=0,existing_204_versioned_overlay_unchanged=True,
  original_SOURCE_FLUXMET_untouched=True,DATM_unchanged=True,Slurm_submitted=0,
  stage64_report_SHA256=digest(prior_csv))
 out.mkdir(exist_ok=False)
 fday=out/"stage65_US_Whs_native_daily_QC0_TA_vs_source_ERA_pm14days.csv"
 fall=out/"stage65_US_Whs_all_HH_pm30days_TA_source_QC_and_ERA.csv"
 fnear=out/"stage65_US_Whs_nearest_before_after_QC0_tower_TA.csv"
 fclock=out/"stage65_US_Whs_nearest_same_clock_QC0_tower_TA.csv"
 fshort=out/"stage65_US_Whs_pm3days_original_TA_QC_and_ERA.csv"
 csvwrite(fday,DAY_COLUMNS,dayreport)
 csvwrite(fall,BASE_COLUMNS,selected)
 csvwrite(fnear,RECENT_COLUMNS,recents)
 csvwrite(fclock,RECENT_COLUMNS,samenear)
 csvwrite(fshort,BASE_COLUMNS,target_window)
 stat["output_sha256"]={f.name:digest(f) for f in (fday,fall,fnear,fclock,fshort)}
 (out/"stage65_manifest.json").write_text(json.dumps(stat,indent=2,sort_keys=True)+"\n")
 print("STAGE65 SUCCESS | US-Whs 2012-05-26 tower QC0 measured TA vs paired source ERA, ±30 days; original unchanged")
 print("STAGE65 TARGET",TARGET,"QC",original_center["TA_F_QC"],
       "TA_F",fmt(target_T),"SOURCE_ERA",fmt(target_ERA),
       "QC1_MINUS_ERA_C",fmt(target_delta))
 print("STAGE65 NEAREST_QC0_120D BEFORE",stat["nearest_pre_QC0_120_days"] or "NONE",
       "AFTER",stat["nearest_post_QC0_120_days"] or "NONE")
 for days in (1,3,7,14,30):
  z=subsets[str(days)]
  print("STAGE65 QC0_WINDOW",days,"days",
   "PAIRED_QC0",z["QC0_TA_total"],
   "MEDIAN_QC0_MINUS_ERA",fmt(z["QC0_minus_ERA_median_C"]),
   "SAME_CLOCK_06_PM1h_QC0",z["QC0_near_06h_pm1h_total"],
   "SAME_CLOCK_MEDIAN_DELTA",fmt(z["QC0_near_06h_pm1h_minus_ERA_median_C"]))
 print("STAGE65 DAILY native_date | QC0 count | paired QC0 count | same clock QC0 count | median QC0-minus-ERA | same-clock median | QC1 count")
 for r in dayreport:
  print("STAGE65 DAY",r["native_date"],"|",r["original_tower_TA_QC0_HH"],
   "|",r["paired_QC0_TA_vs_ERA_HH"],"|",r["QC0_near_06h_pm1h_HH"],
   "|",r["QC0_minus_ERA_median_C"] or "NA",
   "|",r["QC0_near_06h_minus_ERA_median_C"] or "NA",
   "|",r["TA_F_QC1_HH"])
 print("STAGE65 MEASURED_TA_NEAREST | native | hours from target | TA_F QC0 | source ERA | measured minus ERA | matched clock ±1h")
 for r in recents:
  print("STAGE65 QC0_NEAR",r["native_time"],"|",r["distance_hours_from_target"],
    "|",r["original_TA_F_C"],"|",r["source_TA_ERA_C"],
    "|",r["measured_minus_source_ERA_C"],"|",r["same_local_clock_near_06h_pm1h"])
 print("STAGE65 MEASURED_TA_MATCHED_CLOCK nearest 16 | native | TA_F QC0 | ERA | delta")
 for r in samenear:
  print("STAGE65 QC0_06H",r["native_time"],"|",r["original_TA_F_C"],
    "|",r["source_TA_ERA_C"],"|",r["measured_minus_source_ERA_C"])
 print("STAGE65 TARGET_3DAY_CONTEXT | native | T_F | TA_QC | ERA_T | delta | SW | wind")
 for r in target_window:
  dt=clk(r["native_time"])
  if dt.date()>=reference.date()-timedelta(days=1) and dt.date()<=reference.date()+timedelta(days=1):
   if dt.hour in (5,6,7):
    print("STAGE65 CONTEXT",r["native_time"],"|",r["TA_F_C"],"|",
     r["TA_F_QC"],"|",r["TA_ERA_C"],"|",
     r["TA_F_minus_ERA_C"] or "NA","|",r["SW_IN_F"],"|",r["WS_F"])
 print("STAGE65_REPORTS="+str(out))
 print("STAGE65 NO APPROVAL/SOURCE/204/DATM/SLURM MODIFICATION")
if __name__=="__main__":
 main()

#!/usr/bin/env python3
"""Batch05 Stage57: one targeted REAL ERA5-Land CDS T2m/D2m reference for
US-Wjs 2018-03-11 19:30 to 2018-03-12 10:00 (30 native HH science HOLD).
Use existing SHA-pinned Stage31 NetCDF reference parser. Source original
FLUXMET, Stage56 174 overlay, DATM/CIME/Slurm are NEVER altered.
Grid RH and grid dewpoint are research evidence, NOT tower-observed RH.
FLUXNET native time -> UTC assumes Stage29 BIF -7 LOCAL STANDARD offset
with missing BIF UTC_OFFSET_DATE_END: still PROVISIONAL, no DST conversion.
"""
import argparse,csv,hashlib,importlib.util,json,math,tempfile
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter

SITE="US-Wjs"
LAT,LON=34.4258,-105.8617
UTC_OFFSET=-7
FIRST="201803111930"
LAST="201803121000"
LEFT="201803111900"
RIGHT="201803121030"
BEFORE="201803111830"
AFTER="201803121100"
CDS_DATASET="reanalysis-era5-land-timeseries"
CDS_REQ={"variable":["2m_temperature","2m_dewpoint_temperature"],
 "date":"2018-03-11/2018-03-13",
 "location":{"longitude":LON,"latitude":LAT},
 "data_format":"netcdf"}
COLUMNS=("site","native_time","role","provisional_UTC",
 "tower_T_C","tower_T_QC","original_VPD_hPa","original_VPD_QC",
 "original_source_RH_pct","original_RH_derived_from_T_VPD_pct",
 "source_processed_TA_ERA_C","source_processed_VPD_ERA_hPa",
 "source_processed_ERA_RH_derived_pct",
 "REAL_ERA5L_grid_T_C","REAL_ERA5L_grid_Td_C","REAL_ERA5L_RH_water_pct",
 "REAL_ERA5L_grid_VPD_hPa","REAL_ERA5L_RH_to_tower_T_VPD_hPa",
 "REAL_ERA5L_vapour_pressure_to_tower_T_VPD_hPa",
 "REAL_ERA5L_RH_minus_source_processed_ERA_RH_pp",
 "REAL_ERA5L_T_minus_tower_T_C",
 "ERA5L_clock_interpolation","reference_permission")

def native(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native source time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def render(t):return t.strftime("%Y%m%d%H%M")
def utc(t):return native(t)-timedelta(hours=UTC_OFFSET)
def sequence(a,b):
 x,y=native(a),native(b)
 if (y-x).total_seconds()%1800 or x>y:raise ValueError("invalid 30-minute source span")
 return [render(x+timedelta(minutes=30*i)) for i in range(int((y-x).total_seconds()/1800)+1)]
def n(v):
 try:
  x=float(v)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except(ValueError,TypeError):return None
def es(T):
 if T is None or not -80<=T<=60:raise ValueError("temperature out of range")
 return 6.112*math.exp(17.67*T/(243.5+T))
def rfrom(t,v):
 if t is None or v is None:return None
 return 100*(1-v/es(t))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def read(p):
 if p.is_symlink() or not p.is_file():raise ValueError("source file missing "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  r=csv.DictReader(f)
  if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):raise ValueError("bad CSV schema "+str(p))
  return list(r)
def write(p,records):
 with p.open("x",encoding="utf-8",newline="") as f:
  wr=csv.DictWriter(f,fieldnames=COLUMNS,extrasaction="raise")
  wr.writeheader();wr.writerows(records)
def load_parser(path):
 spec=importlib.util.spec_from_file_location("stage31_trusted_ERA5L_parser",path)
 if not spec or not spec.loader:raise ValueError("cannot import verified Stage31")
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module
def check_sources(d52,d53,d56):
 f52=d52/"stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv"
 f53=d53/"stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv"
 f56=d56/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv"
 m56=d56/"stage56_manifest.json"
 inv,r53,merged=read(f52),read(f53),read(f56)
 manifest=json.loads(m56.read_text())
 if len(merged)!=174 or len({(r["site"],r["native_time"]) for r in merged})!=174 or (
   manifest.get("versioned_total_approved_HH")!=174 or
   manifest.get("Wjs_2018_protected_30HH_UNCHANGED") is not True or
   manifest.get("outputs_sha256",{}).get(f56.name)!=sha(f56)):
  raise ValueError("Stage56 174 source-approved versioned overlay integrity failed")
 hold=set(sequence(FIRST,LAST))
 if len(hold)!=30 or any(r["site"]==SITE and r["native_time"] in hold for r in merged):
  raise ValueError("protected original Wjs 30 HH intersects approved 174 overlay")
 events=[r for r in r53 if r.get("episode_id")=="US-Wjs_E0079" and r.get("role")=="EVENT"]
 if len(events)!=3 or {r["native_time"] for r in events}!={"201803120900","201803120930","201803121000"}:
  raise ValueError("Stage53 2018 event provenance drift")
 keys={(r["source_file"],r["source_member"],r["source_sha256"]) for r in events}
 if len(keys)!=1:raise ValueError("Stage53 original source product mixed")
 filename,member,filehash=keys.pop()
 m=[r for r in inv if r["site"]==SITE and r["source_file"]==filename and
   r["source_member"]==member and r["source_file_SHA256"]==filehash]
 clocks={r["timestamp_column"] for r in m}
 if len(clocks)!=1:raise ValueError("Stage52 original native time not unambiguous")
 p=Path(filename)
 if p.is_symlink() or not p.is_file() or sha(p)!=filehash:
  raise ValueError("original raw US-Wjs source SHA mismatch")
 stage56p=manifest.get("source_products_SHA256",{})
 if stage56p.get(SITE)!=filehash:raise ValueError("Stage56 original Wjs source SHA does not match Stage53")
 clock=clocks.pop()
 # Original Wjs source is a FLUXMET CSV verified in Stage53; refuse unexpected source.
 if p.suffix.lower()!=".csv" or member not in ("",p.name) or "FLUXMET_HH" not in p.name:
  raise ValueError("US-Wjs source product no longer the verified source FLUXMET CSV")
 wanted=set(sequence(BEFORE,AFTER))
 values={}
 with p.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f)
  if not {clock,"TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH","TA_ERA","VPD_ERA"}.issubset(rd.fieldnames or []):
   raise ValueError("original source has missing columns")
  for r in rd:
   t=r.get(clock,"")
   if t in wanted:
    if t in values:raise ValueError("duplicate original native half-hour")
    values[t]=r
 if set(values)!=wanted:raise ValueError("original 34-HH source window missing")
 for ev in events:
  orig=values[ev["native_time"]]
  if abs(n(orig["TA_F"])-n(ev["tower_TA_C"]))>.002 or abs(n(orig["VPD_F"])-n(ev["tower_VPD_hPa"]))>.002 or orig["VPD_F_QC"]!=ev["tower_VPD_QC"]:
   raise ValueError("Stage53 original observed source drift")
 for t in hold:
  r=values[t]
  if r["VPD_F_QC"]!="1" or n(r["RH"]) is not None:
   raise ValueError("Stage56 US-Wjs 2018 original QC1/missing RH HOLD status changed")
 for t in (LEFT,RIGHT):
  r=values[t]
  if r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="0" or n(r["RH"]) is None:
   raise ValueError("Wjs 2018 exact QC0 anchor unexpectedly changed")
 return values,{"stage52_inventory_sha256":sha(f52),"stage53_original_20HH_sha256":sha(f53),
                "stage56_original_174_sha256":sha(f56),"US_Wjs_original_source_sha256":filehash}

def selftest():
 assert len(sequence(FIRST,LAST))==30
 assert len(sequence(BEFORE,AFTER))==34
 assert utc("201803111900")==datetime(2018,3,12,2)
 assert utc("201803121030")==datetime(2018,3,12,17,30)
 assert n("-9999") is None
 assert abs(rfrom(1,0)-100)<1e-12
 print("STAGE57 SELF-TEST PASS | 30 exact held HH and four original neighbor HH, -7h provisional UTC, no forcing writes")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--fetch",action="store_true",help="explicitly retrieve one public CDS ERA5-Land time-series")
 p.add_argument("--stage52-dir",type=Path)
 p.add_argument("--stage53-dir",type=Path)
 p.add_argument("--stage56-dir",type=Path)
 p.add_argument("--stage31-parser",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(z is None for z in (a.stage52_dir,a.stage53_dir,a.stage56_dir,a.stage31_parser,a.out)):
  p.error("source Stage52, Stage53, Stage56, trusted Stage31 parser and new --out required")
 if not a.fetch:p.error("use --fetch to approve exactly one research CDS download")
 d52,d53,d56=(x.expanduser().resolve() for x in (a.stage52_dir,a.stage53_dir,a.stage56_dir))
 source_parser=a.stage31_parser.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if not all(d.is_dir() for d in (d52,d53,d56)) or not out.parent.is_dir() or out.exists():
  p.error("source dirs and new report parent required; no overwrite")
 if any(out==d or out in d.parents or d in out.parents for d in (d52,d53,d56)):
  p.error("refuse to place download in original folder")
 if not source_parser.is_file() or source_parser.is_symlink():
  raise ValueError("trusted Stage31 parser unavailable")
 parserhash=sha(source_parser)
 if parserhash!="a28bde14dadcaf87abaaa2d52f2eaa785e16c89f":
  raise ValueError("Stage31 original NetCDF interpreter SHA drift")
 source,sources=check_sources(d52,d53,d56)
 print("STAGE57 SOURCE PASS | Stage56 original 174 approved rows SHA checked, US-Wjs 2018 30-HH HOLD unchanged",flush=True)
 print("STAGE57 CDS REQUEST",json.dumps(CDS_REQ,sort_keys=True),flush=True)
 out.mkdir(exist_ok=False)
 payload=out/"ERA5L_US_Wjs_20180311_13_T2M_D2M.cds_download"
 import cdsapi
 cdsapi.Client().retrieve(CDS_DATASET,CDS_REQ,str(payload))
 if not payload.is_file() or payload.stat().st_size<256:
  raise ValueError("actual CDS data not downloaded")
 with tempfile.TemporaryDirectory(prefix="stage57_ERA5L_") as t:
  parser=load_parser(source_parser)
  container,files=parser.extract_netcdfs(payload,t)
  ref,metadata,coords=parser.inspect_reference(files)
  if coords["latitude"] is not None and abs(coords["latitude"]-LAT)>.75:
   raise ValueError("CDS grid latitude far from Wjs")
  if coords["longitude"] is not None and min(abs(coords["longitude"]-LON),abs(coords["longitude"]-LON-360))>.75:
   raise ValueError("CDS grid longitude far from Wjs")
  times=[t for t,v in ref["t2m"]]
  if times[0]>utc(BEFORE) or times[-1]<utc(AFTER):
   raise ValueError("retrieved ERA5-Land does not cover exact 34 native half-hours")
  rows=[]
  for t in sequence(BEFORE,AFTER):
   r=source[t]; tower=n(r["TA_F"]);V=n(r["VPD_F"])
   te=n(r["TA_ERA"]);ve=n(r["VPD_ERA"])
   if tower is None or V is None or te is None or ve is None:
    raise ValueError("missing original Wjs T/VPD or source ERA at "+t)
   gridT,modeT=parser.interp(utc(t),ref["t2m"])
   gridD,modeD=parser.interp(utc(t),ref["d2m"])
   if modeT!=modeD:raise ValueError("air/dewpoint reference time alignment mismatch")
   T=gridT-273.15;D=gridD-273.15
   rhgrid=100*es(D)/es(T)
   if not 0<=rhgrid<=100.5:raise ValueError("ERA5L unrealistic dewpoint RH")
   vgrid=es(T)-es(D)
   vtower=es(tower)*(1-rhgrid/100)
   ve_tower=es(tower)-es(D)
   erarh=rfrom(te,ve)
   role="HOLD_2018" if FIRST<=t<=LAST else "QC0_ANCHOR" if t in (LEFT,RIGHT) else "EXTRA_CONTEXT"
   vals=dict(site=SITE,native_time=t,role=role,provisional_UTC=utc(t).strftime("%Y-%m-%dT%H:%M:%SZ"),
    tower_T_C=r["TA_F"],tower_T_QC=r["TA_F_QC"],
    original_VPD_hPa=r["VPD_F"],original_VPD_QC=r["VPD_F_QC"],
    original_source_RH_pct=r["RH"],
    original_RH_derived_from_T_VPD_pct=f"{rfrom(tower,V):.6f}",
    source_processed_TA_ERA_C=r["TA_ERA"],
    source_processed_VPD_ERA_hPa=r["VPD_ERA"],
    source_processed_ERA_RH_derived_pct=f"{erarh:.6f}",
    REAL_ERA5L_grid_T_C=f"{T:.6f}",REAL_ERA5L_grid_Td_C=f"{D:.6f}",
    REAL_ERA5L_RH_water_pct=f"{rhgrid:.6f}",REAL_ERA5L_grid_VPD_hPa=f"{vgrid:.8f}",
    REAL_ERA5L_RH_to_tower_T_VPD_hPa=f"{vtower:.8f}",
    REAL_ERA5L_vapour_pressure_to_tower_T_VPD_hPa=f"{ve_tower:.8f}",
    REAL_ERA5L_RH_minus_source_processed_ERA_RH_pp=f"{rhgrid-erarh:.6f}",
    REAL_ERA5L_T_minus_tower_T_C=f"{T-tower:.6f}",
    ERA5L_clock_interpolation=modeT,reference_permission="RESEARCH_COMPARISON_ONLY_30HH_HOLD_UNCHANGED")
   rows.append(vals)
 if len(rows)!=34 or Counter(r["role"] for r in rows)!={"HOLD_2018":30,"QC0_ANCHOR":2,"EXTRA_CONTEXT":2}:
  raise ValueError("exact original science HOLD/conservation counts failed")
 outfile=out/"stage57_34_NATIVE_HH_TOWER_VS_REAL_ERA5L_30HH_HOLD.csv"
 write(outfile,rows)
 report=[
 "# US-Wjs March 2018 — actual independent download ERA5-Land versus tower and source ERA",
 "Native half-hours 2018-03-11 18:30 to 2018-03-12 11:00. Native→UTC -7 hours provisional from BIF.",
 "ERA5-Land point timeseries T2m/Td2m is gridded reanalysis, **not** original tower RH; source ERA is an AmeriFlux processed companion.",
 "All 30 original 2018 VPD-QC1 source half hours science HOLD; no forcing modification.",
 "",
 "| Native | Role | Tower T C | Original VPD | VPD QC | Original source RH | Source ERA RH inferred | REAL ERA5L RH | REAL ERA5L VPD (RH to tower T) | ERA5L T minus tower T |",
 "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
 ]
 for r in rows:
  def show(k):
   x=n(r[k]);return "NA" if x is None else f"{x:.3f}"
  report.append("| "+" | ".join([r["native_time"],r["role"],show("tower_T_C"),
   show("original_VPD_hPa"),r["original_VPD_QC"],show("original_source_RH_pct"),
   show("source_processed_ERA_RH_derived_pct"),show("REAL_ERA5L_RH_water_pct"),
   show("REAL_ERA5L_RH_to_tower_T_VPD_hPa"),show("REAL_ERA5L_T_minus_tower_T_C")])+" |")
 report+=["","**No automatic repair. Review the observed QC0 anchor mismatch before selecting RH interpolation versus reference transfer.**",""]
 (out/"STAGE57_WJS_2018_REAL_ERA5LAND_TOWER_COMPARISON.md").write_text("\n".join(report),encoding="utf-8")
 manifest=dict(dataset=CDS_DATASET,request=CDS_REQ,payload=str(payload),
   payload_SHA256=sha(payload),payload_bytes=payload.stat().st_size,
   decoded_container_type=container,decoded_members=metadata,grid_coordinates=coords,
   original_source_SHA256=sources,stage31_parser_SHA256=parserhash,
   original_native_to_UTC_offset_hours=UTC_OFFSET,
   BIF_UTC_OFFSET_DATE_END="MISSING_PROVISIONAL_LST_NO_DST",
   actual_2018_science_HOLD_native_HH=30,adjacent_QC0_anchor_HH=2,
   extra_original_context_HH=2,independent_in_situ_RH_validated=False,
   production_DATM_permission=False,earlier_174_overlay_modified=False,
   original_source_modified=False,Slurm_jobs_submitted=0,
   output_csv_SHA256=sha(outfile))
 (out/"stage57_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("STAGE57 SUCCESS | 34 original HH, 30 Wjs-2018 HOLD, 2 QC0 anchors; 1 actual CDS ERA5-Land download",flush=True)
 for r in rows:
  if r["role"]=="QC0_ANCHOR" or r["native_time"] in ("201803111930","201803120600","201803120900","201803121000"):
   print("STAGE57 REVIEW",r["native_time"],r["role"],"towerVPD",r["original_VPD_hPa"],
    "sourceERA_RH",r["source_processed_ERA_RH_derived_pct"],"actualERA5L_RH",r["REAL_ERA5L_RH_water_pct"],
    "actualERA5L_RH_to_towerT_VPD",r["REAL_ERA5L_RH_to_tower_T_VPD_hPa"])
 print("STAGE57 REPORT="+str(out/"STAGE57_WJS_2018_REAL_ERA5LAND_TOWER_COMPARISON.md"))
 print("STAGE57_OUT="+str(out))
 print("STAGE57 NO APPROVAL OR SOURCE/174/DATM/SLURM CHANGES")
if __name__=="__main__":main()

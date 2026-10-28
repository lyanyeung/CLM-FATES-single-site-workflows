#!/usr/bin/env python3
"""Batch05 Stage59: TARGETED original-source provenance audit, US-Wjs 2018.
Exactly 49 original FLUXMET half-hours from 2018-03-11 12:00 through
2018-03-12 12:00 around 30 original VPD-QC1 missing-RH HOLD records.
Inspect any actual available RH/humidity source columns, original
precipitation, radiation, wind and 100%-RH plateau. Alternative column
names / filled products are NOT assumed to be independent tower sensors.
No science approval, no edit of original source or approved 174 overlay.
"""
import argparse,csv,hashlib,json,math,re
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Wjs"
START="201803111200"
END="201803121200"
LEFT="201803111900"
RIGHT="201803121030"
HOLD_START="201803111930"
HOLD_END="201803121000"
REQUIRED=("TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH","TA_ERA","VPD_ERA")
PREFERRED=("P_F","P_F_QC","P","P_QC","SW_IN_F","SW_IN_F_QC",
           "LW_IN_F","LW_IN_F_QC","WS_F","WS_F_QC","PA_F","PA_F_QC",
           "RH_F","RH_F_QC","H2O","H2O_F","H2O_F_QC","TD","TD_F",
           "DEW_POINT","LE_F","LE_F_QC")
HUMIDITY_RE=re.compile(r"(^RH($|_)|VPD|DEW|^TD($|_)|H2O|HUMID|VAPOU?R)",re.I)
WEATHER_RE=re.compile(r"(^P($|_)|PRECIP|RAIN|^SW_IN|^LW_IN|^WS($|_)|^LE($|_)|^PA($|_))",re.I)

def parse(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("bad source timestamp "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def seq(a,b):
 da,db=parse(a),parse(b)
 if db<da or (db-da).total_seconds()%1800:raise ValueError("invalid halfhour interval")
 return [(da+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(int((db-da).total_seconds()/1800)+1)]
def n(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def load_csv(path):
 if not path.is_file() or path.is_symlink():raise ValueError("missing regular source "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  d=csv.DictReader(f)
  if not d.fieldnames or len(d.fieldnames)!=len(set(d.fieldnames)):
   raise ValueError("bad CSV header")
  rows=list(d)
  if any(None in r or any(v is None for v in r.values()) for r in rows):
   raise ValueError("malformed source report")
 return rows
def write(p,cols,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def fmt(s):
 v=n(s)
 return "NA" if v is None else f"{v:.3f}"
def selftest():
 assert len(seq(START,END))==49
 assert len(seq(HOLD_START,HOLD_END))==30
 assert len(seq("201803111500","201803111900"))==9
 assert n("-9999") is None and HUMIDITY_RE.search("RH_F") and WEATHER_RE.search("P_F")
 print("STAGE59 SELF-TEST PASS | 49 original HH; 30 exact protected HOLD HH; dynamic original source fields; no writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage53-dir",type=Path)
 p.add_argument("--stage56-dir",type=Path)
 p.add_argument("--stage57-dir",type=Path)
 p.add_argument("--stage58-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(z is None for z in (a.stage53_dir,a.stage56_dir,a.stage57_dir,a.stage58_dir,a.out)):
  p.error("need existing Stage53/56/57/58 and NEW --out")
 d53,d56,d57,d58=(x.expanduser().resolve() for x in
    (a.stage53_dir,a.stage56_dir,a.stage57_dir,a.stage58_dir))
 out=a.out.expanduser().resolve()
 if not all(x.is_dir() for x in (d53,d56,d57,d58)) or not out.parent.is_dir() or out.exists():
  p.error("source reports must exist; output must be a new directory")
 if any(out==d or out in d.parents or d in out.parents for d in (d53,d56,d57,d58)):
  p.error("cannot put new output inside original report folders")
 f53=d53/"stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv"
 f56=d56/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv"
 f57=d57/"stage57_34_NATIVE_HH_TOWER_VS_REAL_ERA5L_30HH_HOLD.csv"
 f58=d58/"stage58_30HH_FOUR_RESEARCH_HUMIDITY_METHODS_UNAPPROVED.csv"
 prior=load_csv(f53);base=load_csv(f56);external=load_csv(f57);methods=load_csv(f58)
 m56=json.loads((d56/"stage56_manifest.json").read_text())
 m57=json.loads((d57/"stage57_manifest.json").read_text())
 m58=json.loads((d58/"stage58_manifest.json").read_text())
 if (len(base)!=174 or len(external)!=34 or len(methods)!=30 or len(prior)!=20 or
   m56.get("versioned_total_approved_HH")!=174 or
   m56.get("outputs_sha256",{}).get(f56.name)!=sha(f56) or
   m57.get("output_csv_SHA256")!=sha(f57) or
   m58.get("outputs_sha256",{}).get(f58.name)!=sha(f58) or
   m58.get("scientific_approvals_new")!=0):
  raise ValueError("verified Stage53/56/57/58 result SHA or population drift")
 protected=set(seq(HOLD_START,HOLD_END))
 if any(x["site"]==SITE and x["native_time"] in protected for x in base):
  raise ValueError("original 2018 30 HH overlap approved 174")
 events=[r for r in prior if r.get("episode_id")=="US-Wjs_E0079" and r.get("role")=="EVENT"]
 pairs={(x["source_file"],x["source_sha256"],x["source_member"]) for x in events}
 if len(events)!=3 or len(pairs)!=1:raise ValueError("Stage53 original source episode identity drift")
 sourcefile,sourcehash,member=pairs.pop()
 file=Path(sourcefile)
 if file.is_symlink() or not file.is_file() or file.suffix.lower()!=".csv" or member not in ("",file.name) or sha(file)!=sourcehash:
  raise ValueError("Stage53 pinned raw original US-Wjs source not valid")
 if (m57.get("original_source_SHA256",{}).get("US_Wjs_original_source_sha256")!=sourcehash or
     m57.get("original_source_SHA256",{}).get("stage56_original_174_sha256")!=sha(f56) or
     m58.get("original_stage57_sha256")!=sha(f57) or
     m58.get("original_stage56_174_sha256")!=sha(f56)):
  raise ValueError("original source SHA linkage from Stage57/58 invalid")
 want=set(seq(START,END))
 native={}
 with file.open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  cols=rd.fieldnames or []
  if len(set(cols))!=len(cols) or not set(REQUIRED).issubset(cols) or "TIMESTAMP_START" not in cols:
   raise ValueError("original FLUXMET source required fields absent")
  for row in rd:
   ts=row["TIMESTAMP_START"]
   if ts in want:
    if ts in native:raise ValueError("duplicate original source HH "+ts)
    native[ts]=row
 if set(native)!=want:raise ValueError("49 original HH not all available")
 for row in external:
  ts=row["native_time"]
  if ts in native and (abs(n(native[ts]["TA_F"])-n(row["tower_T_C"]))>.002 or
      abs(n(native[ts]["VPD_F"])-n(row["original_VPD_hPa"]))>.002 or
      native[ts]["VPD_F_QC"]!=row["original_VPD_QC"]):
   raise ValueError("Stage57 original tower source value changed "+ts)
 for row in methods:
  ts=row["native_time"]
  if ts not in protected or abs(n(native[ts]["VPD_F"])-n(row["original_VPD_hPa"]))>.002:
   raise ValueError("Stage58 original 30 HH source mismatch")
 for ts in protected:
  r=native[ts]
  if r["VPD_F_QC"]!="1" or n(r["RH"]) is not None or r["TA_F_QC"]!="0":
   raise ValueError("2018 30HH original VPDQC1 RH missing scope mismatch")
 for ts in (LEFT,RIGHT):
  r=native[ts]
  if r["VPD_F_QC"]!="0" or n(r["RH"]) is None:
   raise ValueError("QC0 original endpoint unavailable")
 humidity=[c for c in cols if HUMIDITY_RE.search(c)]
 weather=[c for c in cols if WEATHER_RE.search(c)]
 included=[c for c in PREFERRED if c in cols and c not in REQUIRED]
 # Include all original RH-family columns but distinguish processed/filled from measured.
 additional=[c for c in humidity if c not in REQUIRED and c not in included]
 additional=additional[:40]
 outputcols=["TIMESTAMP_START","PHASE"]+list(REQUIRED)+included+additional
 outputcols=list(dict.fromkeys(outputcols))
 samples=[]
 for ts in seq(START,END):
  phase="HOLD_QC1" if ts in protected else "LEFT_QC0_ANCHOR" if ts==LEFT else "RIGHT_QC0_ANCHOR" if ts==RIGHT else "CONTEXT"
  r=dict(native[ts]);r["PHASE"]=phase
  samples.append({key:r.get(key,"") for key in outputcols})
 counts=[]
 for k in humidity+weather:
  vals=[native[ts].get(k,"") for ts in seq(HOLD_START,HOLD_END)]
  nvalid=sum(n(v) is not None for v in vals)
  counts.append(dict(original_source_column=k,valid_in_30HH_HOLD=nvalid,
     present_in_original_FLUXMET=True,
     interpretation="FIELD_ONLY_DO_NOT_INFER_INDEPENDENT_MEASUREMENT_OR_SOURCE_QC"))
 # Contiguous saturation run going BACKWARDS from left 19:00 original QC0 anchor.
 idx=seq(START,LEFT)
 plateau=[]
 for t in reversed(idx):
  z=native[t]
  if (z["VPD_F_QC"]=="0" and z["TA_F_QC"]=="0" and
      n(z["RH"]) is not None and n(z["RH"])>=99.99 and
      n(z["VPD_F"]) is not None and n(z["VPD_F"])<=.001):
   plateau.append(t)
  else:break
 plateau.reverse()
 # Complete checks before any output creation; all reports are new only.
 out.mkdir(exist_ok=False)
 fdata=out/"stage59_49_HH_ORIGINAL_SOURCE_ALL_AVAILABLE_HUMIDITY_WEATHER.csv"
 fcounts=out/"stage59_ORIGINAL_SOURCE_FIELD_COVERAGE_IN_30HH.csv"
 write(fdata,outputcols,samples)
 write(fcounts,("original_source_column","valid_in_30HH_HOLD",
                "present_in_original_FLUXMET","interpretation"),counts)
 summary=dict(original_source_sha256=sourcehash,
  stage53_sha256=sha(f53),stage56_174_sha256=sha(f56),
  stage57_sha256=sha(f57),stage58_sha256=sha(f58),
  science_HOLD_30HH_unchanged=True,approved_overlay_174_unchanged=True,
  original_precip_radiation_and_humidity_columns=humidity+weather,
  plateau_QC0_original_source_native_start=plateau[0] if plateau else None,
  plateau_QC0_original_source_native_end=plateau[-1] if plateau else None,
  plateau_QC0_original_source_HH_within_inspected_window=len(plateau),
  source_original_RH_is_not_independently_sensor_verified=True,
  science_approvals_new=0,production_DATM_permission=False,
  original_FLUXMET_changed=False,Slurm_jobs_submitted=0,
  output_sha256={fdata.name:sha(fdata),fcounts.name:sha(fcounts)})
 (out/"stage59_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 print("STAGE59 SUCCESS | 49 raw original FLUXMET HH inspected, 30 Wjs-2018 QC1 HOLD unchanged, 174 approved unchanged")
 print("STAGE59 ORIGINAL SOURCE",file,"SHA256",sourcehash)
 print("STAGE59 ORIGINAL HUMIDITY COLUMNS",",".join(humidity))
 print("STAGE59 ORIGINAL WEATHER COLUMNS",",".join(weather))
 print("STAGE59 SATURATED_SOURCE_QC0_LEFT_PLATEAU",len(plateau),"HH",plateau[0] if plateau else "NA",plateau[-1] if plateau else "NA")
 print("STAGE59 FIELD COVERAGE valid/30 held HH (available source fields only; NOT sensor proof)")
 for z in counts:
  print("STAGE59 FIELD",z["original_source_column"],z["valid_in_30HH_HOLD"],"/30")
 focus=set(seq("201803111330","201803112030"))
 focus.update(("201803120000","201803120500","201803120600","201803120830","201803120900","201803121000","201803121030","201803121100"))
 extras=[c for c in ("P_F","SW_IN_F","WS_F","LW_IN_F","PA_F") if c in cols]
 print("STAGE59 FOCUS native | phase | T_C | T_QC | originalVPD_hPa | VPD_QC | sourceRH | "+ " | ".join(extras))
 for t in sorted(focus):
  r=native[t]
  phase="HOLD" if t in protected else "QC0_EDGE" if t in (LEFT,RIGHT) else "CONTEXT"
  print("STAGE59 ROW",t,"|",phase,"|",fmt(r["TA_F"]),"|",r["TA_F_QC"],"|",
        fmt(r["VPD_F"]),"|",r["VPD_F_QC"],"|",fmt(r["RH"]),"|",
        " | ".join(fmt(r.get(k)) for k in extras))
 print("STAGE59_OUTPUT="+str(out))
 print("STAGE59 READONLY; 2018 30HH HOLD, 174 OVERLAY, ORIGINAL SOURCES, DATM, SLURM UNCHANGED")
if __name__=="__main__":main()

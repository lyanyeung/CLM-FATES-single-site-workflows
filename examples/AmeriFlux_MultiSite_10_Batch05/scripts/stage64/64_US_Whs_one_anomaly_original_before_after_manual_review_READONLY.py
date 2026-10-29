#!/usr/bin/env python3
"""Batch05 Stage64 — ONE US-Whs original P2/P3 HH, manual weather audit.
Read Stage63 exact unapproved site/native time, Stage27 original science/QC,
and the independently SHA-pinned ORIGINAL AmeriFlux FLUXMET ZIP.
Print 3 hours before/after in original native local timestamp.
Never change source products, 204 overlay, CIME/DATM or submit Slurm.
Processed-source ERA/MDS are NOT in-situ validation.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Whs"
SOURCE_SHA256="0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767"
PKG="AMF_US-Whs_FLUXNET_2007-2025_v1.3_r1"
SOURCE_NAME="AMF_US-Whs_FLUXNET_FLUXMET_HH_2007-2025_v1.3_r1.csv"
FIELDS=("site","native_time","position","TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC",
 "original_source_RH_pct","RH_implied_from_original_T_VPD_pct",
 "TA_F_MDS_C","TA_F_MDS_QC","VPD_F_MDS_hPa","VPD_F_MDS_QC",
 "TA_ERA_C","VPD_ERA_hPa","source_ERA_pair_RH_pct",
 "source_ERA_RH_at_original_T_candidate_VPD_hPa",
 "P_F","P_F_QC","SW_IN_F","SW_IN_F_QC",
 "LW_IN_F","LW_IN_F_QC","WS_F","WS_F_QC","PA_F","PA_F_QC",
 "human_science_status")

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def numeric(v):
 try:
  x=float(v)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None

def fmt(v,decimals=3):
 x=numeric(v)
 return "NA" if x is None else f"{x:.{decimals}f}"

def sat(T):
 if T is None or not -80<=T<=60:return None
 return 6.112*math.exp(17.67*T/(T+243.5))

def rh(T,V):
 e=sat(T)
 return None if e is None or V is None else 100*(1-V/e)

def parse(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid original native HH "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")

def nearby(t,minutes):
 return (parse(t)+timedelta(minutes=minutes)).strftime("%Y%m%d%H%M")

def load(path,required):
 if path.is_symlink() or not path.is_file():raise ValueError("report missing "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  head=reader.fieldnames or []
  if not set(required).issubset(head) or len(head)!=len(set(head)):
   raise ValueError("report CSV schema missing/duplicate "+str(path))
  out=list(reader)
 if any(None in r or any(v is None for v in r.values()) for r in out):
  raise ValueError("malformed original report "+str(path))
 return out

def write(path,rows):
 with path.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise")
  w.writeheader()
  w.writerows(rows)

def selftest():
 assert nearby("202312312330",30)=="202401010000"
 assert len(FIELDS)==len(set(FIELDS))
 assert rh(0,10)<0
 assert fmt("-9999")=="NA"
 print("STAGE64 SELF-TEST PASS | US-Whs exact one original source anomaly, native ±3h, read-only")

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage63-dir",type=Path)
 p.add_argument("--stage27-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if None in (a.stage63_dir,a.stage27_dir,a.out):
  p.error("require actual --stage63-dir --stage27-dir and new --out")
 d63,d27,root,out=(x.expanduser().resolve() for x in
  (a.stage63_dir,a.stage27_dir,a.sites_root,a.out))
 source=root/SITE/"forcing"/"packages"/(PKG+".zip")
 if not all(q.is_dir() for q in (d63,d27,root)) or not out.parent.is_dir() or out.exists():
  p.error("source report roots must exist; output must be NEW")
 if any(out==q or out in q.parents or q in out.parents for q in (d63,d27,root)):
  p.error("refuse writing in science input or source folders")
 f63=d63/"stage63_REMAINING_ORIGINAL_P2P3_NATIVE_HH.csv"
 fsite=d63/"stage63_EXACT_TEN_SITE_REMAINING_AFTER_204.csv"
 f27=d27/"stage27_ALL1574_paired_source_comparisons_and_risks.csv"
 m63=json.loads((d63/"stage63_manifest.json").read_text())
 m27=json.loads((d27/"stage27_summary.json").read_text())
 for f in (f63,fsite):
  if m63.get("outputs_sha256",{}).get(f.name)!=sha(f):
   raise ValueError("latest Stage63 report SHA changed")
 if (m63.get("remaining_original_P2P3_HH")!=1565 or
     m63.get("approved_versioned_overlay_HH")!=204 or
     m27.get("source_P2P3_native_HH")!=1574 or
     m27.get("original_P2P3_episodes")!=483 or
     m27.get("FLUXMET_changed") is not False):
  raise ValueError("Stage27/63 original candidate cohort mismatch")
 all63=load(f63,("site","native_time","episode_id","original_tier","TA_F_QC","VPD_F_QC","latest_status"))
 sites=load(fsite,("site","remaining_original_P2P3_HH","remaining_original_P2P3_events"))
 all27=load(f27,("site","native_time","episode_id","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
               "RH_original_pct","RH_MDS_pct","RH_ERA_pct","review_lane","risk_flags"))
 whs=[r for r in all63 if r["site"]==SITE]
 stat=[r for r in sites if r["site"]==SITE]
 old=[r for r in all27 if r["site"]==SITE]
 if (len(all63),len(sites),len(all27),len(whs),len(stat),len(old))!=(1565,10,1574,1,1,1):
  raise ValueError("expected exact US-Whs 1 still-pending original P2/P3 HH")
 if stat[0]["remaining_original_P2P3_HH"]!="1" or stat[0]["remaining_original_P2P3_events"]!="1":
  raise ValueError("latest US-Whs remaining event count no longer one")
 event=whs[0];r27=old[0];center=event["native_time"]
 if (event["episode_id"]!=r27["episode_id"] or event["native_time"]!=r27["native_time"] or
     event["TA_F_QC"]!=r27["TA_F_QC"] or event["VPD_F_QC"]!=r27["VPD_F_QC"] or
     event["latest_status"]!="UNAPPROVED_P2P3_SCIENCE_HOLD"):
  raise ValueError("Stage63 and Stage27 original event/QC mismatch")
 if source.is_symlink() or not source.is_file() or sha(source)!=SOURCE_SHA256:
  raise ValueError("Original US-Whs ZIP absent or immutable Stage45 source SHA drift "+str(source))
 wanted=[nearby(center,30*j) for j in range(-6,7)]
 rows={}
 with zipfile.ZipFile(source) as z:
  names=[x for x in z.infolist() if Path(x.filename).name==SOURCE_NAME]
  if len(names)!=1 or names[0].file_size>900*1024*1024:
   raise ValueError("verified source member missing, nonunique or too large")
  with z.open(names[0]) as raw:
   with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f)
    header=reader.fieldnames or []
    if len(header)!=len(set(header)) or not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"}.issubset(header):
     raise ValueError("original source HH CSV required fields missing")
    for row in reader:
     t=row["TIMESTAMP_START"]
     if t in wanted:
      if t in rows:raise ValueError("original source duplicate source HH "+t)
      rows[t]=row
 if set(rows)!=set(wanted):
  raise ValueError("original US-Whs 13 HH bracket incomplete "+repr(sorted(set(wanted)-set(rows))))
 c=rows[center]
 if (abs(numeric(c["TA_F"])-numeric(r27["TA_F_C"]))>.002 or
     abs(numeric(c["VPD_F"])-numeric(r27["VPD_F_hPa"]))>.002 or
     c["TA_F_QC"]!=r27["TA_F_QC"] or c["VPD_F_QC"]!=r27["VPD_F_QC"]):
  raise ValueError("original pinned ZIP not exact Stage27 US-Whs source values")
 output=[]
 for t in wanted:
  r=rows[t]
  T,V=numeric(r["TA_F"]),numeric(r["VPD_F"])
  if T is None or V is None:raise ValueError("tower T or VPD missing in source bracket "+t)
  eta,ev=numeric(r.get("TA_ERA")),numeric(r.get("VPD_ERA"))
  era_rh=rh(eta,ev)
  candidate=sat(T)*(1-era_rh/100) if era_rh is not None else None
  pos="TARGET_HOLD" if t==center else "BEFORE" if t<center else "AFTER"
  original_rh=rh(T,V)
  output.append(dict(site=SITE,native_time=t,position=pos,
   TA_F_C=r["TA_F"],TA_F_QC=r["TA_F_QC"],
   VPD_F_hPa=r["VPD_F"],VPD_F_QC=r["VPD_F_QC"],
   original_source_RH_pct=r.get("RH",""),
   RH_implied_from_original_T_VPD_pct="" if original_rh is None else f"{original_rh:.6f}",
   TA_F_MDS_C=r.get("TA_F_MDS",""),TA_F_MDS_QC=r.get("TA_F_MDS_QC",""),
   VPD_F_MDS_hPa=r.get("VPD_F_MDS",""),VPD_F_MDS_QC=r.get("VPD_F_MDS_QC",""),
   TA_ERA_C=r.get("TA_ERA",""),VPD_ERA_hPa=r.get("VPD_ERA",""),
   source_ERA_pair_RH_pct="" if era_rh is None else f"{era_rh:.6f}",
   source_ERA_RH_at_original_T_candidate_VPD_hPa="" if candidate is None else f"{candidate:.6f}",
   P_F=r.get("P_F",""),P_F_QC=r.get("P_F_QC",""),
   SW_IN_F=r.get("SW_IN_F",""),SW_IN_F_QC=r.get("SW_IN_F_QC",""),
   LW_IN_F=r.get("LW_IN_F",""),LW_IN_F_QC=r.get("LW_IN_F_QC",""),
   WS_F=r.get("WS_F",""),WS_F_QC=r.get("WS_F_QC",""),
   PA_F=r.get("PA_F",""),PA_F_QC=r.get("PA_F_QC",""),
   human_science_status="REVIEW_ONLY_NOT_APPROVED"))
 v0=numeric(rows[wanted[5]]["VPD_F"])
 vc=numeric(rows[center]["VPD_F"])
 v1=numeric(rows[wanted[7]]["VPD_F"])
 if any(x is None for x in (v0,vc,v1)):raise ValueError("missing immediate VPD neighbor")
 out.mkdir(exist_ok=False)
 fresult=out/"stage64_Whs_ONE_ANOMALY_ORIGINAL_3H_BEFORE_AFTER_13HH.csv"
 write(fresult,output)
 print("STAGE64 SUCCESS | ONE US-Whs original P2P3 HH manual review, 13 original HH")
 print("STAGE64 EXACT TARGET",center,"EPISODE",event["episode_id"],"TIER",event["original_tier"],
       "TA_QC",event["TA_F_QC"],"VPD_QC",event["VPD_F_QC"])
 print("STAGE64 TARGET SOURCE RISK",r27["review_lane"],r27["risk_flags"])
 print("STAGE64 DIRECT NEIGHBOR VPD hPa BEFORE",fmt(v0),"TARGET",fmt(vc),"AFTER",fmt(v1),
       "JUMPS",fmt(vc-v0),fmt(v1-vc))
 print("STAGE64 ORIGINAL ZIP",str(source),"SHA256",SOURCE_SHA256)
 print("STAGE64 COLUMNS native|phase|TA_C|TA_QC|VPD_hPa|VPD_QC|RHsource|RH_implied|MDS_VPD|MDS_QC|ERA_T|ERA_VPD|ERA_RH|ERA_RH_at_T_VPD|P|SW|LW|WS|PA")
 for r in output:
  vals=[r[k] for k in ("native_time","position","TA_F_C","TA_F_QC",
   "VPD_F_hPa","VPD_F_QC","original_source_RH_pct","RH_implied_from_original_T_VPD_pct",
   "VPD_F_MDS_hPa","VPD_F_MDS_QC","TA_ERA_C","VPD_ERA_hPa",
   "source_ERA_pair_RH_pct","source_ERA_RH_at_original_T_candidate_VPD_hPa",
   "P_F","SW_IN_F","LW_IN_F","WS_F","PA_F")]
  print("STAGE64 ROW"," | ".join(map(str,vals)))
 meta=dict(site=SITE,original_event=center,original_episode_id=event["episode_id"],
  source_original_SHA256=SOURCE_SHA256,
  original_13_HH=True,source_native_clock_not_assumed_UTC=True,
  investigator_science_approved=False,prior_204_approved_unchanged=True,
  original_FLUXMET_changed=False,DATM_changed=False,Slurm_jobs_submitted=0,
  stage63_sha256=sha(f63),stage27_SHA256=sha(f27),
  report_sha256=sha(fresult))
 (out/"stage64_manifest.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
 print("STAGE64_REPORTS="+str(out))
 print("STAGE64 NO SOURCE/204/DATM/SLURM WRITES; source ERA NOT independent measured RH")
if __name__=="__main__":main()

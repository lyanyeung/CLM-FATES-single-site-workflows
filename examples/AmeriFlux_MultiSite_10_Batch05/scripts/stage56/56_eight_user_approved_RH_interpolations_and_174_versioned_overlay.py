#!/usr/bin/env python3
"""Batch05 Stage56: user-approved interpolation at EXACTLY 8 native HH,
US-UMB 2009-05-19 11:00,11:30 and US-Wjs 2021-11-02 06:00..08:30.
Protect US-Wjs 2018-03-11 19:30 through 2018-03-12 10:00 (30 HH).
SHA-verify original fullset/fluxmet plus Stage53, Stage55 and optional Stage24.
Versioned candidate only; NOT an edit to any official source, 166-row baseline,
DATM/CIME/Slurm input. RH from original QC0 anchors is an interpolation,
not an independent RH measurement. TA_ERA/VPD_ERA are source product companions.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
from datetime import datetime,timedelta

SCHEMA=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
SOURCES={"US-UMB":("200905191030","200905191200"),
         "US-Wjs":("202111020530","202111020900")}
TARGETS={"US-UMB":("200905191100","200905191130"),
         "US-Wjs":("202111020600","202111020630","202111020700",
                    "202111020730","202111020800","202111020830")}
WJS_2018=("201803111900","201803121030")
BOUNDARY_COLS=("site","before_native","after_native","before_status","after_status",
               "before_selected_VPD_hPa","after_selected_VPD_hPa",
               "selected_jump_hPa","abs_jump_gt2_hPa","abs_jump_gt4_hPa")
def parse(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid original native time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def clock(t):return t.strftime("%Y%m%d%H%M")
def sequence(a,b):
 first,last=parse(a),parse(b)
 if last<first or (last-first).total_seconds()%1800:raise ValueError("invalid HH window")
 return [clock(first+timedelta(minutes=i*30)) for i in range(int((last-first).total_seconds()/1800)+1)]
def num(v):
 try:
  x=float(v)
  return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def sat(t):
 if t is None or not -80<=t<=60:raise ValueError("invalid source TA")
 return 6.112*math.exp(17.67*t/(243.5+t))
def frompair(t,v):
 if t is None or v is None:return None
 return 100*(1-v/sat(t))
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def read(p):
 if not p.is_file() or p.is_symlink():raise ValueError("original report not regular file "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as f:
  d=csv.DictReader(f)
  if not d.fieldnames or len(set(d.fieldnames))!=len(d.fieldnames):raise ValueError("bad CSV header "+str(p))
  rows=list(d)
  if any(None in r or any(v is None for v in r.values()) for r in rows):
   raise ValueError("malformed CSV "+str(p))
  return rows
def write(p,keys,rows):
 with p.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=keys,extrasaction="raise");w.writeheader();w.writerows(rows)
def read_source(path,member,field,wanted):
 p=Path(path)
 if p.is_symlink() or not p.is_file():raise ValueError("verified raw product disappeared "+path)
 if p.suffix.lower()==".zip":
  with zipfile.ZipFile(p) as z:
   if member not in z.namelist():raise ValueError("raw ZIP member absent "+member)
   with z.open(member) as f:return parse_source(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""),field,wanted)
 with p.open(encoding="utf-8-sig",newline="") as f:return parse_source(f,field,wanted)
def parse_source(f,field,wanted):
 d=csv.DictReader(f)
 fields=d.fieldnames or []
 if not {field,"TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"}.issubset(fields) or len(fields)!=len(set(fields)):
  raise ValueError("original source product required headers missing")
 rows={}
 for r in d:
  t=r[field]
  if t in wanted:
   if t in rows:raise ValueError("duplicate original native HH "+t)
   rows[t]=r
 if set(rows)!=wanted:raise ValueError("missing original native HH "+str(sorted(wanted-set(rows))))
 return rows
def asindex(rows):
 out={}
 for r in rows:
  key=(r["site"],r["native_time"])
  if key in out:raise ValueError("overlap or duplicate native HH "+str(key))
  out[key]=r
 return out
def selftest():
 assert sum(len(v) for v in TARGETS.values())==8
 assert len(sequence(*WJS_2018))==32
 assert len(sequence("201803111930","201803121000"))==30
 assert len(sequence(*SOURCES["US-Wjs"]))==8
 assert abs(sat(8.168)*(1-(97.193+(95.568-97.193)/3)/100)-.363)<.002
 print("STAGE56 SELF-TEST PASS | exact 8 user-approved RH interpolation candidates, 30 Wjs-2018 held, no writes to original")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage52-dir",type=Path)
 p.add_argument("--stage53-dir",type=Path)
 p.add_argument("--stage55-dir",type=Path)
 p.add_argument("--stage24-dir",type=Path,default=None)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage52_dir,a.stage53_dir,a.stage55_dir,a.out)):
  p.error("Stage52/53/55 and new --out are required")
 srcdirs=[x.expanduser().resolve() for x in (a.stage52_dir,a.stage53_dir,a.stage55_dir)]
 if a.stage24_dir:srcdirs.append(a.stage24_dir.expanduser().resolve())
 out=a.out.expanduser().resolve()
 if not out.parent.is_dir() or out.exists() or not all(d.is_dir() for d in srcdirs):
  p.error("source directories must exist and output must be new")
 if any(d==out or d in out.parents or out in d.parents for d in srcdirs):
  p.error("never write into an original report or source tree")
 d52,d53,d55=srcdirs[:3]
 f52=d52/"stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv"
 f53=d53/"stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv"
 f55=d55/"stage55_USER_APPROVED_US_UMB_2HH_INTERPOLATION_VERSIONED_CANDIDATE.csv"
 m55=d55/"stage55_manifest.json"
 inv,src53,umb55=read(f52),read(f53),read(f55)
 meta55=json.loads(m55.read_text())
 if (len(src53),len(umb55))!=(20,2) or meta55.get("UMB_approved_versioned_candidate_HH")!=2:
  raise ValueError("Stage53/55 exact original population changed")
 if meta55.get("stage55_outputs_sha256",{}).get(f55.name)!=digest(f55):
  raise ValueError("Stage55 approved two-row candidate SHA mismatch")
 if any(r.get("science_approval")!="NO" or r.get("DATM_permission")!="NO" for r in src53):
  raise ValueError("Stage53 original science holds changed")
 if set((r["site"],r["native_time"]) for r in umb55)!=set(("US-UMB",t) for t in TARGETS["US-UMB"]):
  raise ValueError("Stage55 US-UMB original approval timestamps mismatch")
 product={}
 records={}
 for site,(lo,hi) in SOURCES.items():
  candidates=[r for r in src53 if r["site"]==site and r["role"]=="EVENT"]
  keys={(r["source_file"],r["source_member"],r["source_sha256"]) for r in candidates}
  if len(keys)!=1:raise ValueError("Stage53 event source product not unique "+site)
  filename,member,sha=keys.pop()
  matched=[r for r in inv if r["site"]==site and r["source_file"]==filename and
   r["source_member"]==member and r["source_file_SHA256"]==sha]
  cols={r["timestamp_column"] for r in matched}
  if len(cols)!=1:raise ValueError("Stage52 original native clock missing/ambiguous "+site)
  field=cols.pop()
  if digest(Path(filename))!=sha:raise ValueError("original immutable product SHA drift "+site)
  times=set(sequence(lo,hi))
  if site=="US-Wjs":times.update(sequence(*WJS_2018))
  product[site]={"file":filename,"member":member,"sha":sha,"timestamp_column":field}
  records[site]=read_source(filename,member,field,times)
  for r in candidates:
   row=records[site][r["native_time"]]
   T,V=num(row["TA_F"]),num(row["VPD_F"])
   if T is None or V is None or abs(T-num(r["tower_TA_C"]))>.002 or abs(V-num(r["tower_VPD_hPa"]))>.002 or row["VPD_F_QC"]!=r["tower_VPD_QC"]:
    raise ValueError("original Stage53 event source mismatch "+site+" "+r["native_time"])
 # Reject any possibility of adding a Wjs-2018 row. Preserve 30 source VPD-QC1 holds.
 holdtimes=sequence("201803111930","201803121000")
 if len(holdtimes)!=30 or any(records["US-Wjs"][t]["VPD_F_QC"]!="1" for t in holdtimes):
  raise ValueError("protected Wjs-2018 30-HH original hold source no longer matches")
 candidates=[]
 for site,(lo,hi) in SOURCES.items():
  original=records[site]
  left,right=original[lo],original[hi]
  if any(x["TA_F_QC"]!="0" or x["VPD_F_QC"]!="0" for x in (left,right)):
   raise ValueError("interpolation anchor original QC not 0")
  LR=[num(left["RH"]),num(right["RH"])]
  if any(x is None or not 0<=x<=100 for x in LR):
   raise ValueError("interpolation anchor RH source missing")
  for x in (left,right):
   if num(x["TA_F"]) is None or num(x["VPD_F"]) is None or abs(frompair(num(x["TA_F"]),num(x["VPD_F"]))-num(x["RH"]))>.07:
    raise ValueError("original anchor RH/VPD/T disagreement")
  for t in TARGETS[site]:
   r=original[t];T=num(r["TA_F"]);V=num(r["VPD_F"])
   if T is None or V is None or r["TA_F_QC"]!="0" or r["VPD_F_QC"]!="1" or num(r["RH"]) is not None:
    raise ValueError("not approved absent-RH original QC0/1 source "+site+" "+t)
   frac=(parse(t)-parse(lo)).total_seconds()/(parse(hi)-parse(lo)).total_seconds()
   targetrh=LR[0]+(LR[1]-LR[0])*frac
   targetv=sat(T)*(1-targetrh/100)
   if not 0<=targetrh<=100 or not 0<=targetv<=sat(T):raise ValueError("invalid candidate pair")
   eraT,eraV=num(r.get("TA_ERA")),num(r.get("VPD_ERA"))
   candidate=dict(site=site,native_time=t,source_cohort="STAGE56_EXPLICIT_USER_APPROVED_SOURCE_RH_INTERPOLATION",
     decision_id=("UMB_2009_TWO_HH" if site=="US-UMB" else "WJS_2021_SIX_HH"),
     source_TA_C=r["TA_F"],source_TA_QC=r["TA_F_QC"],
     source_VPD_hPa=r["VPD_F"],source_VPD_QC=r["VPD_F_QC"],
     source_RH_pct=r["RH"],source_processed_ERA_T_C=r.get("TA_ERA",""),
     source_processed_ERA_VPD_hPa=r.get("VPD_ERA",""),
     source_processed_ERA_RH_derived_pct="" if None in (eraT,eraV) else f"{frompair(eraT,eraV):.9f}",
     modified_TA_C=r["TA_F"],modified_RH_pct=f"{targetrh:.9f}",
     modified_VPD_hPa=f"{targetv:.10f}",delta_VPD_hPa=f"{targetv-V:.10f}",
     replacement_RH_provenance="LINEAR_TIME_INTERPOLATION_BETWEEN_ORIGINAL_SOURCE_QC0_ANCHOR_RH_NOT_MEASURED_TARGET_RH",
     new_VPD_derivation="MAGNUS_WATER_ES_AT_UNCHANGED_ORIGINAL_TA_F",
     source_QC_provenance_only="ORIGINAL_TA_QC0_VPD_QC1_PRESERVED_AS_HISTORIC_NOT_NEW_MEASUREMENT",
     overlay_status="EXPLICIT_USER_APPROVED_20261028_VERSIONED_CANDIDATE_ONLY_NOT_DATM")
   candidates.append(candidate)
 if len(candidates)!=8 or len(asindex(candidates))!=8:
  raise ValueError("exact 8 user-approved candidate rows drift")
 cidx=asindex(candidates)
 for r in umb55:
  k=(r["site"],r["native_time"]);c=cidx[k]
  if abs(num(c["modified_RH_pct"])-num(r["approved_interpolated_RH_pct"]))>1e-8 or abs(num(c["modified_VPD_hPa"])-num(r["approved_reconstructed_VPD_hPa"]))>2e-8:
   raise ValueError("Stage55 two approved UMB science numbers changed")
 # 8 new continuous segments: compare selected candidate vs unchanged adjacent QC0 boundaries.
 boundaries=[]
 for site,(lo,hi) in SOURCES.items():
  times=sequence(lo,hi)
  original=records[site]
  for first,last in zip(times,times[1:]):
   lk,rk=(site,first),(site,last)
   lv=num(cidx[lk]["modified_VPD_hPa"]) if lk in cidx else num(original[first]["VPD_F"])
   rv=num(cidx[rk]["modified_VPD_hPa"]) if rk in cidx else num(original[last]["VPD_F"])
   if lv is None or rv is None:raise ValueError("boundary VPD missing")
   delta=rv-lv
   boundaries.append(dict(site=site,before_native=first,after_native=last,
    before_status="APPROVED_INTERPOLATED" if lk in cidx else "UNCHANGED_QC0",
    after_status="APPROVED_INTERPOLATED" if rk in cidx else "UNCHANGED_QC0",
    before_selected_VPD_hPa=f"{lv:.10f}",after_selected_VPD_hPa=f"{rv:.10f}",
    selected_jump_hPa=f"{delta:.10f}",abs_jump_gt2_hPa=int(abs(delta)>2),
    abs_jump_gt4_hPa=int(abs(delta)>4)))
 if len(boundaries)!=10 or any(int(r["abs_jump_gt2_hPa"]) for r in boundaries):
  raise ValueError("new 8-HH interpolation causes >2hPa boundary jump")
 existing=[]
 merged=None
 stage24meta=None
 if len(srcdirs)>3:
  d24=srcdirs[3]
  f24=d24/"stage24_VERSIONED_166_approved_RH_VPD_native_overlay.csv"
  m24=d24/"stage24_manifest.json"
  stage24meta=json.loads(m24.read_text())
  existing=read(f24)
  if (len(existing)!=166 or len(asindex(existing))!=166 or
      any(set(r)!=set(SCHEMA) for r in existing) or
      stage24meta.get("total_approved_overlay_HH")!=166 or
      stage24meta.get("output_sha256")!=digest(f24) or
      stage24meta.get("raw_original_FLUXMET_changed") is not False or
      stage24meta.get("DATM_forcing_changed") is not False):
   raise ValueError("Stage24 original 166-row source or manifest not independently verified")
  baseidx=asindex(existing)
  if set(baseidx)&set(cidx):raise ValueError("new approval overlaps earlier 166")
  if any(k[0]=="US-Wjs" and k[1] in holdtimes for k in baseidx):
   raise ValueError("pre-existing overlay unexpectedly contains Wjs-2018 protected hold")
  merged=[baseidx[k] for k in sorted(baseidx)]+[cidx[k] for k in sorted(cidx)]
  merged.sort(key=lambda r:(r["site"],r["native_time"]))
  if len(merged)!=174 or any(baseidx[k]!=asindex(merged)[k] for k in baseidx):
   raise ValueError("original 166 approval rows not preserved")
 # No report writes until all provenance/count/approval/boundary gates passed.
 out.mkdir(exist_ok=False)
 write(out/"stage56_EXACT_8_USER_APPROVED_RH_INTERPOLATION_OVERLAY.csv",SCHEMA,sorted(candidates,key=lambda r:(r["site"],r["native_time"])))
 write(out/"stage56_TEN_LOCAL_INTERPOLATION_BOUNDARIES.csv",BOUNDARY_COLS,boundaries)
 if merged is not None:
  write(out/"stage56_VERSIONED_174_approved_RH_VPD_native_overlay.csv",SCHEMA,merged)
 manifest=dict(explicit_user_approval_date="2026-10-28",
  UMB_2009_approved_HH=2,Wjs_2021_approved_HH=6,
  Wjs_2018_protected_30HH_UNCHANGED=True,
  stage24_original_166_verified=(merged is not None),
  versioned_total_approved_HH=174 if merged is not None else 8,
  total_boundary_pairs=len(boundaries),new_boundary_abs_gt2=0,
  original_FLUXMET_Fullset_changed=False,
  original_Stage24_166_modified=False,
  production_DATM_permission=False,Slurm_jobs_submitted=0,
  source_stage53_SHA256=digest(f53),source_stage55_SHA256=digest(f55),
  source_products_SHA256={site:p["sha"] for site,p in product.items()},
  independent_ERA5_Land_used=False,
  source_2018_HOLD_30HH_first=holdtimes[0],source_2018_HOLD_30HH_last=holdtimes[-1],
  stage24_original_overlay_SHA256=stage24meta["output_sha256"] if stage24meta else None,
  outputs_sha256={p.name:digest(p) for p in sorted(out.glob("*.csv"))})
 (out/"stage56_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
 print("STAGE56 SUCCESS | USER APPROVED 2 US-UMB + 6 US-Wjs-2021 = 8; 2018 30 HH HOLD untouched")
 for r in sorted(candidates,key=lambda x:(x["site"],x["native_time"])):
  print("STAGE56 APPROVED",r["site"],r["native_time"],"TA",r["modified_TA_C"],
        "VPD_OLD",r["source_VPD_hPa"],"RH_INTERPOLATED",r["modified_RH_pct"],
        "VPD_NEW",r["modified_VPD_hPa"])
 print("STAGE56 BOUNDARIES",len(boundaries),"NEW_ABS_GT2",0)
 print("STAGE56 166_BASE_VERIFIED",merged is not None,"MERGED_VERSIONED_174",merged is not None)
 if merged is None:print("STAGE56 NOTE: verified stage24 166-row directory not supplied; only 8-row candidate written; NO 174-file claim")
 print("STAGE56_OUTPUT="+str(out))
 print("STAGE56 NO SOURCE FILE/PRIOR 166/2018 HOLD/DATM/CIME/SLURM CHANGED")
if __name__=="__main__":main()

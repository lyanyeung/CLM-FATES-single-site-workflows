#!/usr/bin/env python3
"""Stage95 AmeriFlux Batch05: trace Wkg Sept 10 T/rain source provenance.

Read original ZIP (BIFVARINFO_HH, README and ERA5_HH member) plus SHA-
verified Stage94 FLUXMET raw-source field audit, Stage84 approved 1675 SHA.
Do NOT treat source TA_F_MDS as independent T, source product TA_ERA /
packaged ERA5_HH as independent tower measurement, or -9999 RH as measured.
No model/forcing writes; generate compact new source-evidence reports only.
"""
import argparse,csv,hashlib,io,json,math,re,zipfile
from pathlib import Path
from datetime import datetime,timedelta

SITE="US-Wkg"
TARGET="202509101300"
RELEASE="2004-2025_v1.3_r1"
FLUXNET_PREFIX="AMF_US-Wkg_FLUXNET_"
ZIPNAME=FLUXNET_PREFIX+RELEASE+".zip"
SOURCE_SHA="f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"
OVERLAY_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
BIF=FLUXNET_PREFIX+"BIFVARINFO_HH_"+RELEASE+".csv"
ERA=FLUXNET_PREFIX+"ERA5_HH_1981-2025_v1.3_r1.csv"
FLUXMET=FLUXNET_PREFIX+"FLUXMET_HH_"+RELEASE+".csv"
CENTER=("202509101230","202509101300","202509101330")
FOCUS_FIELDS=("native_time","TA_F","TA_F_QC","TA_F_MDS","TA_ERA",
 "VPD_F","VPD_F_QC","VPD_ERA","RH","P","P_F","P_F_QC","P_ERA",
 "SW_IN_F","SW_IN_F_QC","SW_IN_ERA","H_F_MDS","LE_F_MDS")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for chunk in iter(lambda:stream.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()
def numeric(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (TypeError,ValueError):return None
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing protected report "+str(p))
 with p.open("r",encoding="utf-8-sig",newline="") as h:
  rr=csv.DictReader(h);heads=rr.fieldnames or []
  if len(heads)!=len(set(heads)) or not set(required).issubset(heads):
   raise ValueError("report CSV column drift "+str(p))
  out=list(rr)
 if any(None in x or any(v is None for v in x.values()) for x in out):
  raise ValueError("malformed report CSV rows "+str(p))
 return out
def write(p,headers,rows):
 with p.open("x",encoding="utf-8",newline="") as h:
  w=csv.DictWriter(h,fieldnames=headers,extrasaction="raise")
  w.writeheader();w.writerows(rows)
def selftest():
 assert len(CENTER)==3 and BIF.endswith("_HH_"+RELEASE+".csv")
 assert numeric("-9999") is None and numeric("11.049")==11.049
 assert ZIPNAME=="AMF_US-Wkg_FLUXNET_2004-2025_v1.3_r1.zip"
 print("STAGE95 SELF-TEST PASS | original US-Wkg BIFVARINFO + README + archived ERA5_HH lineage; Stage94/84 SHA; no forcing edits")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage84",type=Path)
 ap.add_argument("--stage94",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage84,a.stage94,a.out)):
  ap.error("exact actual Stage84 and Stage94 report directories and NEW output required")
 d84,d94,out=(x.expanduser().resolve() for x in (a.stage84,a.stage94,a.out))
 forcing=a.sites_root.expanduser().resolve()/SITE/"forcing"
 package=forcing/"packages"/ZIPNAME
 if (not all(x.is_dir() for x in (d84,d94)) or
     not package.is_file() or package.is_symlink() or
     out.exists() or not out.parent.is_dir() or
     any(out==d or out in d.parents or d in out.parents for d in (d84,d94,forcing))):
  ap.error("input reports/archive unavailable or output directory not fresh/disjoint")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=OVERLAY_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=OVERLAY_SHA):
  raise ValueError("protected main 1675 approved research overlay SHA drift")
 fm=d94/"stage94_WKG_NATIVE_HH_ORIGINAL_T_COMPANIONS_PRECIP_SW_6H.csv"
 fmembers=d94/"stage94_WKG_SOURCE_PACKAGE_POSSIBLE_COMPANION_MEMBERS.json"
 m94=json.loads((d94/"stage94_WKG_SOURCE_LINEAGE_AND_WEATHER_EVENT_MANIFEST.json").read_text())
 if (m94.get("stage")!=94 or m94.get("native_time")!=TARGET or
     m94.get("original_source_CSV_SHA256")!=SOURCE_SHA or
     m94.get("prior_1675_overlay_SHA256")!=OVERLAY_SHA or
     m94.get("production_T_replacement_approved") is not False or
     m94.get("original_package_zip_exists") is not True or
     any(m94.get("output_SHA256",{}).get(p.name)!=sha(p) for p in (fm,fmembers))):
  raise ValueError("actual Stage94 original/source SHA and science status changed")
 previous=read(fm,["site","native_time","TA_F","TA_F_QC","TA_F_MDS","TA_ERA",
   "VPD_F","VPD_F_QC","RH","P_F","P","P_ERA","P_F_QC","SW_IN_F","SW_IN_F_QC"])
 if len(previous)!=25:
  raise ValueError("original Stage94 25 native source records no longer exact")
 previous_by_time={r["native_time"]:r for r in previous}
 if len(previous_by_time)!=25 or any(t not in previous_by_time for t in CENTER):
  raise ValueError("Stage94 event source time index missing/duplicate")
 center=previous_by_time[TARGET]
 if (center["TA_F"]!="12.89" or center["TA_F_QC"]!="0" or
     numeric(center["TA_F_MDS"])!=numeric(center["TA_F"]) or
     numeric(center["RH"]) is not None or
     center["VPD_F_QC"]!="1"):
  raise ValueError("source raw TA_F_MDS / missing RH / QC policy changed")
 packed_hash=sha(package)  # source archive fingerprint only; no writes
 selected_metadata=[]
 era_values=[]
 era_columns=[]
 era_time_col=None
 readme_text=""
 units_candidates=[]
 with zipfile.ZipFile(package,"r") as z:
  names={x.filename for x in z.infolist() if not x.is_dir()}
  if not {BIF,ERA,"README.txt",FLUXMET}.issubset(names):
   raise ValueError("original Wkg package BIF/ERA/README/FLUXMET members missing")
  # BIFVARINFO is a product variable-provenance table; do not infer units
  # unless the actual original field and unit information are present.
  with z.open(BIF) as binary:
   h=io.TextIOWrapper(binary,encoding="utf-8-sig",newline="")
   rdr=csv.DictReader(h);bifcols=rdr.fieldnames or []
   if len(bifcols)!=len(set(bifcols)):
    raise ValueError("BIFVARINFO field headings duplicated")
   allmeta=list(rdr)
  needle=re.compile(r"(?<![A-Za-z0-9_])(?:P_F|P_ERA|P|TA_F_MDS|TA_F|TA_ERA|RH|VPD_F|SW_IN_F)(?![A-Za-z0-9_])",re.I)
  for r in allmeta:
   merged=" | ".join(v for v in r.values() if isinstance(v,str))
   if needle.search(merged):
    selected_metadata.append(r)
  if len(selected_metadata)>400:raise ValueError("unreasonably large original metadata selection")
  with z.open("README.txt") as h:
   readme_text=h.read(65536).decode("utf-8-sig",errors="replace")
  if len(readme_text)>10000:raise ValueError("archive readme unexpectedly large")
  # This is a *packaged ERA5-derived companion*, not a separate tower.
  # Match native half-hour if an explicit timestamp exists; never guess.
  with z.open(ERA) as binary:
   h=io.TextIOWrapper(binary,encoding="utf-8-sig",newline="")
   rdr=csv.DictReader(h)
   era_columns=rdr.fieldnames or []
   if len(era_columns)!=len(set(era_columns)):
    raise ValueError("packaged ERA5_HH columns duplicated")
   for name in ("TIMESTAMP_START","TIMESTAMP","TIMESTAMP_END"):
    if name in era_columns:
     era_time_col=name
     break
   if era_time_col:
    wanted=set(CENTER)
    for r in rdr:
     if r.get(era_time_col) in wanted:
      if any(p["native_time"]==r[era_time_col] for p in era_values):
       raise ValueError("duplicate original packaged ERA5_HH native time")
      era_values.append({"native_time":r[era_time_col],
         **{k:v for k,v in r.items() if k!=era_time_col}})
      if len(era_values)==len(wanted):break
  # Member checks guarantee archive contains valid entries. No extraction.
  assert len(names)>0
  pack_member_info={x.filename:{"size":x.file_size,"crc":x.CRC}
    for x in z.infolist() if x.filename in (BIF,ERA,FLUXMET,"README.txt")}
 # Metadata may mention explicit units but not necessarily site sensor lineage.
 meta_json=out/"stage95_WKG_ORIGINAL_BIFVARINFO_RELEVANT_FIELDS.json"
 era_json=out/"stage95_WKG_PACKAGED_ERA5_HH_3_NATIVE_TIMES.json"
 readme=out/"stage95_WKG_ORIGINAL_ZIP_README.txt"
 center_csv=out/"stage95_WKG_THREE_NATIVE_HH_ORIGINAL_PRECIP_T_RH_FIELDS.csv"
 manifest=out/"stage95_WKG_ORIGINAL_ARCHIVE_PROVENANCE_MANIFEST.json"
 compact=[]
 for t in CENTER:
  r=previous_by_time[t]
  compact.append({k:(SITE if k=="site" else t if k=="native_time" else r.get(k,""))
    for k in FOCUS_FIELDS})
 out.mkdir(exist_ok=False)
 meta_json.write_text(json.dumps({"columns":bifcols,"relevant_rows":selected_metadata},
    indent=2,ensure_ascii=False)+"\n")
 era_json.write_text(json.dumps({"columns":era_columns,"time_column":era_time_col,
   "matching_rows":era_values},indent=2,ensure_ascii=False)+"\n")
 readme.write_text(readme_text)
 write(center_csv,FOCUS_FIELDS,compact)
 meta_field_hits=[]
 for r in selected_metadata:
  if any(re.search(r"UNIT",k,re.I) and v and v.strip() for k,v in r.items()):
   meta_field_hits.append(r)
 result=dict(stage=95,site=SITE,native_time=TARGET,
   original_zip_sha256=packed_hash,source_original_FLUXMET_HH_sha256=SOURCE_SHA,
   latest_1675_approved_overlay_sha256=OVERLAY_SHA,
   actual_Stage94_source_report_sha256=sha(fm),
   source_BIFVARINFO_member_metadata_columns=bifcols,
   matched_BIFVARINFO_rows=len(selected_metadata),
   BIFVARINFO_rows_with_explicit_UNIT_columns=len(meta_field_hits),
   packaged_ERA5_time_column=era_time_col,
   packaged_ERA5_center_rows=len(era_values),
   original_zip_member_info=pack_member_info,
   source_RH_at_center_measured=False,
   original_TA_F_MDS_is_independent_tower_T_at_center=False,
   packaged_ERA5_HH_is_independent_tower_sensor=False,
   original_T_replacement_approved=False,
   provenance_requires_science_review=True,
   original_data_and_QC_unmodified=True,
   previous_1675_unchanged=True,DATM_CIME_unmodified=True,Slurm_submitted=0,
   output_sha256={x.name:sha(x) for x in (meta_json,era_json,readme,center_csv)})
 manifest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print("STAGE95 SUCCESS | Wkg original ZIP SHA, BIFVARINFO, README, native original P/P_F/P_ERA and ERA5_HH provenance inspected")
 print("STAGE95 ORIGINAL_ZIP_SHA256",packed_hash)
 print("STAGE95 THREE_NATIVE_FIELDS time TA_F TA_F_MDS TA_ERA RH P P_F P_F_QC P_ERA SW_IN_F SW_IN_F_QC")
 for r in compact:
  print("STAGE95 NATIVE",r["native_time"],r["TA_F"],r["TA_F_MDS"],r["TA_ERA"],
    r["RH"],r["P"],r["P_F"],r["P_F_QC"],r["P_ERA"],r["SW_IN_F"],r["SW_IN_F_QC"])
 print("STAGE95 BIFVARINFO_COLUMNS",json.dumps(bifcols))
 print("STAGE95 BIFVARINFO_RELEVANT_ROWS",len(selected_metadata),
   "EXPLICIT_UNITS_COLUMNS",len(meta_field_hits))
 for r in selected_metadata[:25]:
  print("STAGE95 BIF_DETAIL",json.dumps(r,ensure_ascii=False,sort_keys=True))
 print("STAGE95 ERA5_HH_COLUMNS",json.dumps(era_columns))
 print("STAGE95 ERA5_HH_TIME_COLUMN",era_time_col,"MATCHING_ROWS",len(era_values))
 for r in era_values:
  subset={k:v for k,v in r.items() if k=="native_time" or
    re.search(r"TA|TEMP|VPD|PREC|RAIN|^P$|SW_IN",k,re.I)}
  print("STAGE95 ERA5_NATIVE",json.dumps(subset,sort_keys=True))
 for match in list(re.finditer(r"(?i)(precip|unit|fluxmet|ERA5|BIFVARINFO)",readme_text))[:6]:
  a=max(0,match.start()-65);b=min(len(readme_text),match.end()+150)
  print("STAGE95 README_CONTEXT",repr(readme_text[a:b].replace("\n"," ")))
 print("STAGE95 PROVENANCE_DECISION PACKAGED_ERA5_NOT_INDEPENDENT_TOWER_T; ORIGINAL_RH_MISSING; T_SOURCE_UNRESOLVED_NO_AUTOMATIC_FORCE_REPLACEMENT")
 print("STAGE95_REPORTS="+str(out))
 print("STAGE95 SOURCE/ORIGINAL_QC/APPROVED1675/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

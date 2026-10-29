#!/usr/bin/env python3
"""Batch05 Stage94 original US-Wkg Sept10 source-lineage inspection, READ ONLY.
Examines alternative source meteorological fields (only if actually present),
native half-hour precipitation/radiation/QC, and original package member
names that may contain additional tower raw channels. No source overwrite,
QC relabel, guessed units, proposed T approval, DATM/CIME or Slurm.
Stage93 exact source and output SHA-verified, Stage84 main 1675 immutable.
"""
import argparse,csv,hashlib,json,math,re,zipfile
from pathlib import Path
from datetime import datetime,timedelta
SITE="US-Wkg"
TIME="202509101300"
RELEASE="AMF_US-Wkg_FLUXNET_2004-2025_v1.3_r1"
RAW_SHA="f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"
MAIN_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
SOURCE_FIELDS=("TA_F","TA_F_QC","TA_F_MDS","TA","TA_ERA","TA_PI_F",
 "VPD_F","VPD_F_QC","VPD_ERA","RH","RH_F","RH_F_QC",
 "P_F","P_F_QC","P","P_ERA","SW_IN_F","SW_IN_F_QC","SW_IN_ERA",
 "H_F_MDS","LE_F_MDS")
MET_FIELDS=("site","native_time","minute_offset",
 "TA_F","TA_F_QC","TA_ERA","TA_F_MDS","TA","TA_PI_F",
 "VPD_F","VPD_F_QC","VPD_ERA","RH","RH_F","RH_F_QC",
 "P_F","P_F_QC","P","P_ERA","SW_IN_F","SW_IN_F_QC","SW_IN_ERA",
 "derived_RH_from_TA_F_VPD_F_pct")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for chunk in iter(lambda:stream.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()
def val(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def rh(t,v):
 if t is None or v is None or not -80<=t<=60:return None
 es=6.112*math.exp(17.67*t/(t+243.5))
 return 100*(1-v/es)
def fmt(x):return "" if x is None else f"{x:.9f}"
def move(t,i):
 return (datetime.strptime(t,"%Y%m%d%H%M")+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
def read(p,req):
 if not p.is_file() or p.is_symlink():raise ValueError("required prior source or report missing "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  r=csv.DictReader(h);head=r.fieldnames or []
  if len(head)!=len(set(head)) or not set(req).issubset(head):
   raise ValueError("source CSV schema drift "+str(p))
  rr=list(r)
 if any(None in row or any(v is None for v in row.values()) for row in rr):
  raise ValueError("source CSV row-width drift "+str(p))
 return rr
def write(p,cols,rr):
 with p.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="raise");w.writeheader();w.writerows(rr)
def selftest():
 assert move(TIME,-1)=="202509101230"
 assert move(TIME,1)=="202509101330"
 assert rh(0,8)<0 and abs(rh(0,6.112))<1e-8
 assert val("-9999") is None and val("29.52")==29.52
 print("STAGE94 SELF-TEST PASS | Stage93 original Wkg 13:00 source companion field inventory, precip SW QC and possible archive member metadata, no forcing")
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--stage84",type=Path)
 ap.add_argument("--stage93",type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if a.stage84 is None or a.stage93 is None or a.out is None:
  ap.error("actual Stage84 and Stage93 reports plus fresh output are required")
 d84,d93,out=(x.expanduser().resolve() for x in (a.stage84,a.stage93,a.out))
 root=a.sites_root.expanduser().resolve()/SITE/"forcing"
 folder=root/"raw"/RELEASE
 if (not all(x.is_dir() for x in (d84,d93,folder))
     or out.exists() or not out.parent.is_dir()
     or any(out==x or out in x.parents or x in out.parents
            for x in (d84,d93,folder))):
  ap.error("missing successful reports/original source or output not new/disjoint")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (sha(f84)!=MAIN_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=MAIN_SHA):
  raise ValueError("Stage84 1675 protected source SHA drift")
 f93=d93/"stage93_WKG_SEPT2025_12H_ORIGINAL_NATIVE_T_VPD_ERA_P_SW.csv"
 opt93=d93/"stage93_WKG_SEPT2025_ORIGINAL_VS_T_AND_HUMIDITY_SCENARIOS_READONLY.csv"
 m93=json.loads((d93/"stage93_WKG_SEPT2025_LOCAL_SCIENCE_MANIFEST.json").read_text())
 if (m93.get("stage")!=93 or m93.get("native_time")!=TIME or
     m93.get("source_original_CSV_SHA256")!=RAW_SHA or
     m93.get("previous_1675_approved_SHA256")!=MAIN_SHA or
     m93.get("source_T_replacement_approved") is not False or
     not isinstance(m93.get("two_T_QC0_neighbors_disagreement_C"),(float,int)) or
     abs(m93["two_T_QC0_neighbors_disagreement_C"]-6.05)>1e-6 or
     any(m93.get("output_SHA256",{}).get(p.name)!=sha(p) for p in (f93,opt93))):
  raise ValueError("Stage93 actual original Wkg SHA and unapproved science outcome changed")
 context=read(f93,["native_time","relative_minutes","source_TA_C",
  "source_VPD_hPa","TA_QC","VPD_QC","original_P_F","original_SW_IN_F"])
 if len(context)!=49 or {r["native_time"] for r in context}!={move(TIME,i) for i in range(-24,25)}:
  raise ValueError("Stage93 original Wkg full 49 context HH changed")
 reference={r["native_time"]:r for r in context}
 original=[p for p in folder.iterdir() if
  re.fullmatch(r"AMF_US-Wkg_FLUXNET_FLUXMET_(HH|HR)_.+[.]csv",p.name,re.I)]
 if len(original)!=1 or not original[0].is_file() or original[0].is_symlink() or sha(original[0])!=RAW_SHA:
  raise ValueError("native Wkg FLUXMET original SHA changed or ambiguous")
 need={move(TIME,i) for i in range(-12,13)}
 records={}
 with original[0].open(encoding="utf-8-sig",newline="") as h:
  reader=csv.DictReader(h);columns=reader.fieldnames or []
  if len(columns)!=len(set(columns)) or not {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","P_F","SW_IN_F"}.issubset(columns):
   raise ValueError("original source meteorology schema missing required fields")
  for r in reader:
   t=r["TIMESTAMP_START"]
   if t in need:
    if t in records:raise ValueError("duplicate native original timestamp "+t)
    records[t]=r
 if set(records)!=need:raise ValueError("source original ±6h HH missing")
 fields=[s for s in SOURCE_FIELDS if s in columns]
 missing=[s for s in SOURCE_FIELDS if s not in columns]
 rows=[]
 for i in range(-12,13):
  t=move(TIME,i);r=records[t];ref=reference[t]
  for rawcol,refcol in (("TA_F","source_TA_C"),("VPD_F","source_VPD_hPa"),
      ("TA_F_QC","TA_QC"),("VPD_F_QC","VPD_QC"),
      ("P_F","original_P_F"),("SW_IN_F","original_SW_IN_F")):
   a1,b1=r[rawcol],ref[refcol]
   if rawcol.endswith("_QC"):
    if a1!=b1:raise ValueError("Stage93 native QC changed "+t+" "+rawcol)
   elif val(a1) is not None and val(b1) is not None:
    if abs(val(a1)-val(b1))>.002:raise ValueError("Stage93 source value drift "+t+" "+rawcol)
   elif val(a1)!=val(b1):
    raise ValueError("Stage93 source missing-value drift "+t+" "+rawcol)
  row={name:r.get(name,"") for name in MET_FIELDS if name not in
       ("site","native_time","minute_offset","derived_RH_from_TA_F_VPD_F_pct")}
  rows.append(dict(site=SITE,native_time=t,minute_offset=i*30,**row,
      derived_RH_from_TA_F_VPD_F_pct=fmt(rh(val(r["TA_F"]),val(r["VPD_F"])))))
 pack=root/"packages"/(RELEASE+".zip")
 pack_exists=pack.is_file() and not pack.is_symlink()
 members=[]
 if pack_exists:
  with zipfile.ZipFile(pack) as z:
   for member in z.infolist():
    if re.search(r"(HH|HR|BASE|FULLSET|META|README|FLUXMET|TA)",member.filename,re.I):
     members.append(dict(name=member.filename,uncompressed_bytes=member.file_size,
        compressed_bytes=member.compress_size))
 center=records[TIME];pre=records[move(TIME,-1)];post=records[move(TIME,1)]
 diff_T_before=val(center["TA_F"])-val(pre["TA_F"])
 diff_T_after=val(post["TA_F"])-val(center["TA_F"])
 manifest=dict(stage=94,site=SITE,native_time=TIME,
   original_source_CSV_SHA256=RAW_SHA,prior_1675_overlay_SHA256=MAIN_SHA,
   stage93_original_context_SHA256=sha(f93),
   original_fluxmet_columns_count=len(columns),
   available_companion_fields=fields,unavailable_companion_fields=missing,
   candidate_independent_T_observation_field_verified=False,
   original_package_zip_exists=bool(pack_exists),
   original_package_candidate_member_count=len(members),
   before_to_center_source_T_change_C=diff_T_before,
   center_to_after_source_T_change_C=diff_T_after,
   before_original_P_F=pre.get("P_F",""),
   center_original_P_F=center.get("P_F",""),
   before_original_SW_IN_F=pre.get("SW_IN_F",""),
   center_original_SW_IN_F=center.get("SW_IN_F",""),
   precip_field_units_verified=False,
   source_ERA_companion_not_independent_reanalysis_download=True,
   original_source_and_QC_unchanged=True,prior_1675_unchanged=True,
   production_T_replacement_approved=False,
   DATM_CIME_unchanged=True,Slurm_submitted=0,
   science_status="WKG_CONVECTIVE_RAIN_SOURCE_T_EVIDENCE_INCOMPLETE_REQUIRES_INDEPENDENT_SENSOR_OR_STATION_CHECK",
   output_SHA256={})
 out.mkdir(exist_ok=False)
 f25=out/"stage94_WKG_NATIVE_HH_ORIGINAL_T_COMPANIONS_PRECIP_SW_6H.csv"
 fm=out/"stage94_WKG_SOURCE_PACKAGE_POSSIBLE_COMPANION_MEMBERS.json"
 fsum=out/"stage94_WKG_SOURCE_LINEAGE_AND_WEATHER_EVENT_MANIFEST.json"
 write(f25,MET_FIELDS,rows)
 fm.write_text(json.dumps(members,sort_keys=True,indent=2)+"\n")
 manifest["output_SHA256"]={x.name:sha(x) for x in (f25,fm)}
 fsum.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE94 SUCCESS | original Wkg 2025-09-10 source temperature alternatives/precip & SW lineage science diagnostic")
 print("STAGE94 ORIGINAL_SOURCE_COLUMNS",json.dumps({"available":fields,"unavailable":missing},sort_keys=True))
 print("STAGE94 CENTER before/center/after | source_T T_QC source_VPD VPD_QC TA_ERA P_F SW_IN_F")
 for r in (pre,center,post):
  print("STAGE94 CENTER",r["TIMESTAMP_START"],r["TA_F"],r["TA_F_QC"],
    r["VPD_F"],r["VPD_F_QC"],r.get("TA_ERA",""),
    r.get("P_F",""),r.get("SW_IN_F",""))
 print("STAGE94 SOURCE_T_JUMPS before_to_center",fmt(diff_T_before),
   "center_to_after",fmt(diff_T_after))
 print("STAGE94 OPTIONAL_SOURCE_FIELDS_13",json.dumps([
   {"native_time":records[move(TIME,i)]["TIMESTAMP_START"],
    **{c:records[move(TIME,i)].get(c,"") for c in fields if c not in ("TA_F","VPD_F","P_F","SW_IN_F")}}
    for i in range(-6,7)],sort_keys=True))
 print("STAGE94 SOURCE_PACKAGE_PRESENT",pack_exists,
   "RELEVANT_ARCHIVE_MEMBERS",json.dumps(members[:40],sort_keys=True))
 print("STAGE94 SCIENCE_DECISION",manifest["science_status"])
 print("STAGE94_REPORTS="+str(out))
 print("STAGE94 SOURCE/QC/PRIOR1675/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":
 main()

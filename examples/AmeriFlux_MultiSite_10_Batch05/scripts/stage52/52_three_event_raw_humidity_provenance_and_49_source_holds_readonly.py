#!/usr/bin/env python3
"""Batch05 Stage52 — original raw humidity provenance for 3 numerical events.

Inspect only ORIGINAL AmeriFlux FULLSET/FLUXMET half-hour files (CSV or ZIP)
for US-UMB E0003 and US-Wjs E0079/E0114, at the exact original native
half-hour timestamps. Show original source humidity/temperature/pressure and
QC columns when present, without guessing observed RH from ERA or an RH
offset. Distinguish filled/ERA fields from source observational possibilities.

Also publish event-native 49 failed-offset HOLDs and the previous 70 ERA
candidate evidence gaps without changing any science approval. No downloads,
model runs, forcing writes, source mutations, automatic acceptance, or Slurm.
"""
import argparse,csv,io,hashlib,json,os,re,zipfile
from collections import Counter,defaultdict
from pathlib import Path

TARGETS={"US-UMB":("US-UMB_E0003",),"US-Wjs":("US-Wjs_E0079","US-Wjs_E0114")}
EXPECTED={"US-UMB_E0003":1,"US-Wjs_E0079":3,"US-Wjs_E0114":4}
THREE={"site","episode_id","original_event_native_HH","first_original_native","last_original_native",
       "source_ERA_RH_offset_pp","science_state","production_DATM_authorized"}
NATIVE={"site","episode_id","native_time","original_T_C","original_VPD_hPa",
        "original_VPD_QC","original_ERA_RH_pct","hypothesis_RH_pct",
        "hypothesis_VPD_hPa","science_approval","DATM_permission"}
FORTYNINE={"site","episode_id","original_event_native_HH","native_first","native_last",
           "nearest_screen_failure_reasons","science_state","production_DATM_authorized"}
SEVENTY={"site","episode_id","reference_evidence_gap","status","DATM_permission"}
OUTPUT=("site","episode_id","native_time","source_product_type",
        "source_file","source_member","file_SHA256","product_timestamp_column",
        "product_exact_timestamp_matched","product_humidity_column",
        "product_original_value","product_column_class",
        "possible_QC_column","original_QC_value",
        "raw_product_match_original_T_VPD_QC",
        "stage51_original_T_C","stage51_original_VPD_hPa",
        "stage51_original_VPD_QC","stage51_source_ERA_RH_pct",
        "stage51_RH_offset_hypothesis_pct","validated_original_observed_humidity",
        "science_approval","DATM_permission")
FILES=("site","source_file","source_member","source_file_SHA256",
       "source_kind","timestamp_column","target_times_matched",
       "target_times_total","original_RH_or_humidity_fields",
       "source_native_T_VPD_QC_matched_HH",
       "observed_candidate_field_count",
       "product_validated_station_ground_truth",
       "science_recommendation")
EVENTS=("site","episode_id","target_original_HH",
        "native_start","native_end","matching_raw_product_count",
        "matching_direct_humidity_field_count",
        "matching_ERA_or_filled_field_count",
        "needs_station_QC_and_data_licence_review",
        "science_state","production_DATM_authorized")
HOLD=("site","episode_id","original_event_native_HH","native_first",
      "native_last","bounded_offset_family_failure_reasons",
      "next_required_evidence","science_state","DATM_permission")
QUEUE70=("site","episode_id","source_reference_gap","needs_raw_humidity_QC_or_other_reference",
         "science_state","production_DATM_authorized")
TIMEFIELDS=("TIMESTAMP_START","TIMESTAMP","TIMESTAMP_END")
HINTS=("RH","H2O","VPD","TA","PA","PRES","DEW","TDEW")
def read(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("source report missing "+str(p))
 with p.open(newline="",encoding="utf-8-sig") as f:
  rd=csv.DictReader(f);names=rd.fieldnames or []
  if not required.issubset(names) or len(names)!=len(set(names)):
   raise ValueError("source report wrong columns "+str(p))
  out=list(rd)
 if any(None in x or any(z is None for z in x.values()) for x in out):
  raise ValueError("malformed original report "+str(p))
 return out
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def write(p,cols,data):
 with p.open("x",newline="",encoding="utf-8") as f:
  rd=csv.DictWriter(f,fieldnames=cols,extrasaction="raise")
  rd.writeheader();rd.writerows(data)
def classify(field):
 u=field.upper()
 if "_ERA" in u or u.endswith("ERA"):
  return "REANALYSIS_PROCESSED_NOT_INDEPENDENT_OBS"
 if "MDS" in u or u in ("RH_F","RH_PI_F") or "_F_" in u or u.endswith("_F"):
  return "FILLED_OR_DERIVED_NOT_DIRECT_TOWER_OBSERVATION"
 if u=="RH" or u=="RH_PI" or re.fullmatch(r"RH_[0-9]+",u):
  return "POSSIBLE_UNFILLED_RH_REQUIRES_ORIGINAL_FIELD_METADATA_AND_QC"
 return "ORIGINAL_OTHER_MET_OR_QC_CONTEXT_NO_VERIFIED_RH"
def n(v):
 try:
  x=float(v)
  if x==x and abs(x)<1e10 and x not in (-9999,-6999):return x
 except (ValueError,TypeError):pass
 return None
def source_match(row,info):
 need=("TA_F","VPD_F","VPD_F_QC")
 if any(k not in row for k in need):return "INSUFFICIENT_FIELD_PROVENANCE"
 a,b,c=n(row["TA_F"]),n(row["VPD_F"]),row["VPD_F_QC"]
 T,V=n(info["original_T_C"]),n(info["original_VPD_hPa"])
 if None in (a,b,T,V):return "NONNUMERIC_OR_MISSING_SOURCE_FIELDS"
 return ("EXACT_ORIGINAL_T_VPD_QC_MATCH" if abs(a-T)<=.002 and abs(b-V)<=.002
         and c==info["original_VPD_QC"] else "CONFLICTS_WITH_VERIFIED_ORIGINAL_STAGE51")
def wanted_fields(names):
 found=[]
 for field in names:
  u=field.upper()
  if u.startswith("RH") or u.startswith("H2O") or u.startswith("VPD") or u.startswith("TA") or u.startswith("PA") or u.startswith("PRES") or "DEW" in u:
   found.append(field)
 return found[:100]
def candidate_paths(root,site):
 forcing=root/site/"forcing"
 paths=[]
 for folder in ("raw","packages"):
  sub=forcing/folder
  if not sub.is_dir():continue
  visited=0
  for current,dirs,files in os.walk(sub):
   visited+=1
   if visited>2500:raise ValueError("too many raw source subfolders for "+site)
   dirs[:]=[x for x in dirs if not x.startswith(".") and x not in ("plots","reports","stage","simulation")]
   for name in files:
    lo=name.lower()
    if not name.startswith("AMF_"+site+"_"):continue
    if lo.endswith(".zip") or (lo.endswith(".csv") and ("fullset_hh" in lo or "fluxmet_hh" in lo or "auxmet_hh" in lo)):
     p=Path(current)/name
     if p.is_symlink():continue
     paths.append(p)
   if len(paths)>180:raise ValueError("unexpected original source file candidate explosion "+site)
 return sorted(set(paths),key=lambda p:(p.suffix.lower()!=".csv",len(p.parts),str(p)))
def read_product(fh,need,site,filename,sha256,member,kind,expected_rows):
 rd=csv.DictReader(io.TextIOWrapper(fh,encoding="utf-8-sig",newline=""))
 cols=rd.fieldnames or []
 tcol=next((f for f in TIMEFIELDS if f in cols),None)
 if tcol is None or len(cols)!=len(set(cols)):
  return [],dict(site=site,source_file=filename,source_member=member,
   source_file_SHA256=sha256,source_kind=kind,timestamp_column="MISSING",
   target_times_matched=0,target_times_total=len(need),
   original_RH_or_humidity_fields="",observed_candidate_field_count=0,
   source_native_T_VPD_QC_matched_HH=0,
   product_validated_station_ground_truth=False,
   science_recommendation="NO_SOURCE_TIMESTAMP_OR_DUPLICATE_COLUMNS")
 found=wanted_fields(cols);rows={};seen=0
 for r in rd:
  t=r.get(tcol,"")
  if t not in need:continue
  if t in rows:raise ValueError("duplicate original HH target timestamp "+site+" "+t+" in "+member)
  rows[t]=r;seen+=1
 # Only exact 12-digit native matches, no time shifting or interpolating
 row_out=[]
 for t in sorted(need):
  info=expected_rows[t]
  event=info["episode_id"]
  values=rows.get(t)
  if values is None:
   row_out.append(dict(site=site,episode_id=event,native_time=t,
    source_product_type=kind,source_file=filename,source_member=member,
    file_SHA256=sha256,product_timestamp_column=tcol,
    product_exact_timestamp_matched=False,product_humidity_column="",
    product_original_value="",product_column_class="NO_EXACT_NATIVE_TIMESTAMP",
    possible_QC_column="",original_QC_value="",
    raw_product_match_original_T_VPD_QC="NO_TIMESTAMP_MATCH",
    stage51_original_T_C=info["original_T_C"],
    stage51_original_VPD_hPa=info["original_VPD_hPa"],
    stage51_original_VPD_QC=info["original_VPD_QC"],
    stage51_source_ERA_RH_pct=info["original_ERA_RH_pct"],
    stage51_RH_offset_hypothesis_pct=info["hypothesis_RH_pct"],
    validated_original_observed_humidity=False,
    science_approval="NO",DATM_permission="NO"))
   continue
  for field in found:
   cu=field.upper()
   possible=[field+"_QC",field+"_F_QC",field.split("_")[0]+"_F_QC"]
   qc=next((x for x in possible if x in cols),None)
   row_out.append(dict(site=site,episode_id=event,native_time=t,
    source_product_type=kind,source_file=filename,source_member=member,
    file_SHA256=sha256,product_timestamp_column=tcol,
    product_exact_timestamp_matched=True,product_humidity_column=field,
    product_original_value=values.get(field,""),
    product_column_class=classify(field),
    possible_QC_column=qc or "",original_QC_value=values.get(qc,"") if qc else "",
    raw_product_match_original_T_VPD_QC=source_match(values,info),
    stage51_original_T_C=info["original_T_C"],
    stage51_original_VPD_hPa=info["original_VPD_hPa"],
    stage51_original_VPD_QC=info["original_VPD_QC"],
    stage51_source_ERA_RH_pct=info["original_ERA_RH_pct"],
    stage51_RH_offset_hypothesis_pct=info["hypothesis_RH_pct"],
    validated_original_observed_humidity=False,
    science_approval="NO",DATM_permission="NO"))
 file_out=dict(site=site,source_file=filename,source_member=member,
  source_file_SHA256=sha256,source_kind=kind,timestamp_column=tcol,
  target_times_matched=seen,target_times_total=len(need),
  original_RH_or_humidity_fields=";".join(found),
  source_native_T_VPD_QC_matched_HH=sum(source_match(rows[t],expected_rows[t])=="EXACT_ORIGINAL_T_VPD_QC_MATCH" for t in rows),
  observed_candidate_field_count=sum(classify(c).startswith("POSSIBLE_UNFILLED_RH") for c in found),
  product_validated_station_ground_truth=False,
  science_recommendation="CHECK_SOURCE_FIELD_METADATA_AND_RH_QC_BEFORE_SCIENCE_APPROVAL")
 return row_out,file_out
def inspect_source(p,site,need,reference):
 result=[];files=[];digest=sha(p)
 if p.suffix.lower()==".csv":
  if p.stat().st_size>750*1024*1024:return [],[]
  with p.open("rb") as f:
   a,b=read_product(f,need,site,str(p),digest,p.name,"DIRECT_SOURCE_CSV",reference)
   result+=a;files.append(b)
 elif p.suffix.lower()==".zip":
  try:
   with zipfile.ZipFile(p) as z:
    members=[m for m in z.infolist() if not m.is_dir() and
     any(x in Path(m.filename).name.upper() for x in ("FULLSET_HH","FLUXMET_HH","AUXMET_HH")) and m.filename.lower().endswith(".csv")]
    for m in members[:8]:
     if m.file_size>750*1024*1024:continue
     with z.open(m) as f:
      a,b=read_product(f,need,site,str(p),digest,m.filename,"ORIGINAL_SOURCE_ZIP_MEMBER",reference)
      result+=a;files.append(b)
  except (OSError,zipfile.BadZipFile,UnicodeError,ValueError) as e:
   return [],[dict(site=site,source_file=str(p),source_member="",
    source_file_SHA256=digest,source_kind="ORIGINAL_ZIP_UNREADABLE",
    timestamp_column="",target_times_matched=0,target_times_total=len(need),
    original_RH_or_humidity_fields="",observed_candidate_field_count=0,
    source_native_T_VPD_QC_matched_HH=0,
    product_validated_station_ground_truth=False,science_recommendation=str(e)[:200])]
 return result,files
def selftest():
 assert classify("RH")=="POSSIBLE_UNFILLED_RH_REQUIRES_ORIGINAL_FIELD_METADATA_AND_QC"
 assert classify("RH_ERA")=="REANALYSIS_PROCESSED_NOT_INDEPENDENT_OBS"
 assert classify("RH_F")=="FILLED_OR_DERIVED_NOT_DIRECT_TOWER_OBSERVATION"
 assert sum(EXPECTED.values())==8 and len(TARGETS)==2
 print("STAGE52 SELF-TEST PASS | exact original 3 events/8 native HH, raw FULLSET/FLUXMET field inventory, zero source/model writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage51-dir",type=Path)
 p.add_argument("--sites-root",type=Path,default=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if a.stage51_dir is None or a.out is None:p.error("specify source Stage51 dir and NEW output")
 root=a.sites_root.expanduser().resolve();d=a.stage51_dir.expanduser().resolve();out=a.out.expanduser().resolve()
 if not root.is_dir() or not d.is_dir() or out.exists() or not out.parent.is_dir() or out in d.parents or d in out.parents or out in root.parents or root in out.parents:
  p.error("source path inaccessible or output must be NEW and disjoint")
 files={
  "three":d/"stage51_THREE_NUMERIC_EVENT_HYPOTHESES_NEED_TOWER_VALIDATION.csv",
  "native":d/"stage51_THREE_EVENT_ALL_NATIVE_HH_UNAPPROVED_EVIDENCE.csv",
  "fortynine":d/"stage51_FORTYNINE_NO_FEASIBLE_BOUNDED_OFFSET_GATE_DIAGNOSIS.csv",
  "seventy":d/"stage51_SEVENTY_REFERENCE_GAP_SCIENCE_QUEUE.csv",
  "manifest":d/"stage51_manifest.json"}
 three=read(files["three"],THREE);nat=read(files["native"],NATIVE)
 failed=read(files["fortynine"],FORTYNINE);q70=read(files["seventy"],SEVENTY)
 manifest=json.loads(files["manifest"].read_text())
 if (len(three),len(nat),len(failed),len(q70))!=(3,8,49,70):
  raise ValueError("original Stage51 3/8/49/70 source population mismatch")
 if manifest.get("scientific_approvals_new")!=0 or manifest.get("production_DATM_CIME_Slurm_or_original_source_writes")!=0:
  raise ValueError("source Stage51 unexpected science/data mutation")
 if {(x["site"],x["episode_id"]) for x in three}!={(site,eid) for site,ids in TARGETS.items() for eid in ids}:
  raise ValueError("original three source episode IDs unexpectedly changed")
 kk={(x["site"],x["native_time"]):x for x in nat}
 if len(kk)!=8 or any(x["science_approval"]!="NO" or x["DATM_permission"]!="NO" for x in nat):
  raise ValueError("original unapproved source native trial identity/status mismatch")
 for x in three:
  if int(x["original_event_native_HH"])!=EXPECTED[x["episode_id"]]:
   raise ValueError("actual source original event HH count drift")
  if x["science_state"]!="NUMERIC_ONLY_MUST_VALIDATE_ORIGINAL_STATION_METEO" or x["production_DATM_authorized"]!="NO":
   raise ValueError("Stage51 RH offset falsely promoted")
 gathered=[];products=[];issues=[]
 for site in TARGETS:
  wanted={x["native_time"]:x for x in nat if x["site"]==site}
  probes=candidate_paths(root,site)
  if not probes:issues.append(site+": original FULLSET/FLUXMET CSV/ZIP paths not found")
  for f in probes:
   try:
    rr,meta=inspect_source(f,site,wanted,wanted)
    gathered.extend(rr);products.extend(meta)
   except (OSError,ValueError,UnicodeError,csv.Error) as e:
    issues.append(site+": "+str(f)+": "+str(e)[:180])
  print("STAGE52 ORIGINAL_SOURCE_PRODUCTS",site,len(probes),
        "matched",sum(x["target_times_matched"]>0 for x in products if x["site"]==site),flush=True)
 three_report=[]
 for x in three:
  exact=[r for r in products if r["site"]==x["site"] and r["target_times_matched"]>0]
  count=sum(r["observed_candidate_field_count"] for r in exact)
  era=sum("ERA" in r["original_RH_or_humidity_fields"] for r in exact)
  three_report.append(dict(site=x["site"],episode_id=x["episode_id"],
   target_original_HH=x["original_event_native_HH"],native_start=x["first_original_native"],
   native_end=x["last_original_native"],matching_raw_product_count=len(exact),
   matching_direct_humidity_field_count=count,
   matching_ERA_or_filled_field_count=era,
   needs_station_QC_and_data_licence_review=True,
   science_state="RAW_PRODUCT_FIELD_PROVENANCE_REVIEW_NO_SCIENTIFIC_APPROVAL",
   production_DATM_authorized="NO"))
 q49=[]
 for x in failed:
  q49.append(dict(site=x["site"],episode_id=x["episode_id"],
   original_event_native_HH=x["original_event_native_HH"],native_first=x["native_first"],
   native_last=x["native_last"],
   bounded_offset_family_failure_reasons=x["nearest_screen_failure_reasons"],
   next_required_evidence="ORIGINAL_NATIVE_METEO_RH_QC_OR_REANALYSIS_PROVENANCE_NOT_NUMERIC_SMOOTHING",
   science_state="STILL_SOURCE_SCIENCE_HOLD_NOT_ALL_METHODS_TESTED",
   DATM_permission="NO"))
 queue70=[dict(site=x["site"],episode_id=x["episode_id"],
  source_reference_gap=x["reference_evidence_gap"],
  needs_raw_humidity_QC_or_other_reference=True,science_state="NOT_SCIENCE_APPROVED",
  production_DATM_authorized="NO") for x in q70]
 out.mkdir(exist_ok=False)
 write(out/"stage52_THREE_SOURCE_RAW_ORIGINAL_FIELD_VALUES_NOT_VALIDATED.csv",OUTPUT,gathered)
 write(out/"stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv",FILES,products)
 write(out/"stage52_THREE_NUMERIC_EVENT_ORIGINAL_METEO_EVIDENCE_GAPS.csv",EVENTS,three_report)
 write(out/"stage52_49_NONFEASIBLE_OFFSET_NEED_SOURCE_EVIDENCE.csv",HOLD,q49)
 write(out/"stage52_70_ERA_REFERENCE_PENDING_SOURCE_EVIDENCE.csv",QUEUE70,queue70)
 outmeta=dict(input_SHA256={k:sha(v) for k,v in files.items()},
  source_product_inventory_count=len(products),
  exact_matched_source_products=sum(x["target_times_matched"]>0 for x in products),
  native_hypothetical_events=3,original_native_hh=8,
  offset_family_no_feasible_events=49,
  earlier_ERA_original_candidate_events=70,
  earlier_neighbor_source_holds=253,Claude_exclusive_source_events=108,
  file_read_warnings=issues,source_FLUXMET_FULLSET_DATM_CIME_Slurm_mutated=False,
  new_science_approvals=0)
 (out/"stage52_manifest.json").write_text(json.dumps(outmeta,indent=2,sort_keys=True)+"\n")
 lines=["# Stage52: Batch05 original raw humidity provenance for three mathematically feasible RH offsets",
  "","All science/HOLD statuses unchanged. **No station humidity has been approved**.",
  "The three Stage51 mathematical hypotheses span 8 original half-hours, not 8 validated repairs.",
  "Original FULLSET/FLUXMET raw fields require exact original tower T/VPD/QC provenance matches, field definitions and humidity QC before scientific use.",
  "ERA/MDS/filled RH and ERA5-Land are not independent original tower humidity evidence.","",
  "## Source product exact-native matches"]
 for x in three_report:
  lines.append("- {} {}: {} native HH, {} raw source product files matched at least one site-native clock, {} observation-like RH column appearances (not quality-validated)".format(
   x["site"],x["episode_id"],x["target_original_HH"],x["matching_raw_product_count"],x["matching_direct_humidity_field_count"]))
 lines+=["","## Next scientifically warranted action",
  "1. Inspect whether any original field has true unfilled tower RH, its instrument details, timestamp basis, units and native source QC. Do not infer ground truth from a filled RH_F value.",
  "2. Compare each of the three eventwise RH-offset hypotheses to the field evidence at the same original local standard half-hour, or explicitly HOLD when no actual original observed humidity exists.",
  "3. For the 49 no-feasible fixed-offset events, seek actual meteorological evidence or documented ERA5-Land provenance before testing different event-complete methods; do not expand offset grids just to hide measured QC0 boundary discontinuities.",
  "4. Keep the previous 70 numeric candidates source-unapproved, 253 original source neighbor HOLD, and Claude 108 independent cases untouched. No source/forcing edits.",""]
 if issues:lines+=["## Source file read warnings"]+["- "+x for x in issues]
 (out/"STAGE52_THREE_ORIGINAL_HUMIDITY_SOURCE_AUDIT_AND_NEXT_EVIDENCE.md").write_text("\n".join(lines)+"\n")
 print("STAGE52 SUCCESS | 3 events 8 original native HH; raw source products",len(products),
       "source target-matched",sum(x["target_times_matched"]>0 for x in products),
       "49 offset-family holds,70 ERA evidence gaps,253 older neighbor holds,Claude108 untouched")
 print("STAGE52 PROVENANCE",json.dumps({x["episode_id"]:{"products_matched":x["matching_raw_product_count"],
    "RH_field_appearances":x["matching_direct_humidity_field_count"]} for x in three_report},sort_keys=True))
 print("STAGE52 WARNINGS",json.dumps(issues[:10]))
 print("STAGE52_OUT="+str(out))
 print("STAGE52 SOURCE,166 APPROVED,46 P1 HOLD,10 RH PLATFORM,1574 P2P3,DATM,CIME,SLURM UNCHANGED")
if __name__=="__main__":
 main()

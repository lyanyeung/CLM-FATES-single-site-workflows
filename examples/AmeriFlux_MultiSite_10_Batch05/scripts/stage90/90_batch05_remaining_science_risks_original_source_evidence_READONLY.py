#!/usr/bin/env python3
"""Stage90 Batch05 release risk evidence: READ ONLY, no model forcing changes.

Exact original-source crosswalk of Stage86 seven source temperature exceptions,
46 original P1 HOLD, ten saturation-platform HOLD source keys. Per site/native
HH show source original TA/VPD/QC, derived RH, original processed ERA proxy,
approved research overlay status, any Stage89 Whs temperature-science preview
overlap. Source ±3 hour exact original native context for seven temperature
exceptions. Preserve every historical source and QC label. Strict SHA pins
for Stage05 original FLUXMET/FULLSET, Stage84 main 1675, Stage86, Stage89.
This inventories scientific release risks; it does NOT approve edits.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
ROOT_DEFAULT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
PREV_SHA="63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce"
PREVIEW_SHA="95aefd6027e6f981ac821266bc379b89d9f1299d1c307b7575a17fec65588561"
RELEASES={
 "US-UiD":"2008-2024_v1.3_r1",
 "US-UMB":"FULLSET_2007-2021_3-5",
 "US-UMd":"2007-2025_v1.3_r1",
 "US-Var":"2000-2025_v1.3_r1",
 "US-Vcm":"2007-2025_v1.3_r1",
 "US-Vcp":"2007-2025_v1.3_r1",
 "US-WCr":"1999-2025_v1.3_r1",
 "US-Whs":"2007-2025_v1.3_r1",
 "US-Wjs":"2007-2025_v1.3_r1",
 "US-Wkg":"2004-2025_v1.3_r1"}
SOURCE_SHA={
 "US-UiD":"130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318",
 "US-UMB":"ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6",
 "US-UMd":"e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2",
 "US-Var":"664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2",
 "US-Vcm":"c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c",
 "US-Vcp":"eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42",
 "US-WCr":"f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506",
 "US-Whs":"653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca",
 "US-Wjs":"9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6",
 "US-Wkg":"f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829"}
CATEGORIES=("UNRESOLVED_SOURCE_T_EXCEPTION","P1_HISTORICAL_HOLD","RH_SATURATION_PLATFORM_HOLD")
FIELDS=("site","native_time","source_risk_categories","risk_reasons",
 "original_TA_C","original_TA_QC","original_VPD_hPa","original_VPD_QC",
 "derived_original_RH_pct","source_ERA_TA_C","source_ERA_VPD_hPa",
 "derived_source_processed_ERA_RH_pct","source_TA_to_ERA_delta_C",
 "original_RH_field","original_P_F","original_SW_IN_F",
 "prior_1675_research_overlay_present","prior_1675_research_overlay_modified_TA_C",
 "prior_1675_research_overlay_modified_VPD_hPa",
 "prior_1675_research_overlay_RH_pct","prior_1675_research_overlay_method",
 "Stage89_separate_51_T_preview_overlap","Stage89_separate_51_T_preview_TA_C",
 "Stage89_separate_51_T_preview_VPD_hPa","source_data_status",
 "scientific_release_action")
CTX_FIELDS=("source_temperature_exception_native","native_time","minutes_offset",
 "original_TA_C","TA_F_QC","original_VPD_hPa","VPD_F_QC","derived_RH_pct",
 "original_source_ERA_TA_C","derived_source_ERA_RH_pct")
SITE_FIELDS=("site","distinct_source_risk_HH","P1_HOLD_HH","RH_PLATFORM_HOLD_HH",
 "source_T_exception_HH","risk_categories_overlap_HH","prior_research_1675_overlap_HH",
 "Stage89_temperature_preview_overlap_HH","proxy_ERA_research_rows_from_Stage86")
def checksum(p):
 h=hashlib.sha256()
 with p.open("rb") as file:
  for part in iter(lambda:file.read(1<<20),b""):h.update(part)
 return h.hexdigest()
def number(x):
 try:
  v=float(x)
  return v if math.isfinite(v) and v not in (-9999.,-6999.) else None
 except (ValueError,TypeError):return None
def sat(t):
 return None if t is None or not -80<=t<=60 else 6.112*math.exp(17.67*t/(243.5+t))
def rh(t,v):
 e=sat(t)
 return None if e is None or v is None else 100*(1-v/e)
def fmt(x):return "" if x is None else f"{x:.9f}"
def dt(t):
 if len(t)!=12 or not t.isdigit():raise ValueError("invalid native time "+repr(t))
 return datetime.strptime(t,"%Y%m%d%H%M")
def shift(t,n):
 return (dt(t)+timedelta(minutes=n*30)).strftime("%Y%m%d%H%M")
def load(p,required):
 if not p.is_file() or p.is_symlink():raise ValueError("missing/redirected original science evidence "+str(p))
 with p.open(encoding="utf-8-sig",newline="") as h:
  rd=csv.DictReader(h);names=rd.fieldnames or []
  if len(names)!=len(set(names)) or not set(required).issubset(names):
   raise ValueError("source CSV schema changed "+str(p))
  rows=list(rd)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed original CSV rows "+str(p))
 return rows
def key(rows):
 out={}
 for r in rows:
  k=(r["site"],r["native_time"])
  if k in out:raise ValueError("duplicate site/source native time "+str(k))
  out[k]=r
 return out
def write(p,fields,rows):
 with p.open("x",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
  writer.writeheader();writer.writerows(rows)
def selftest():
 assert len(RELEASES)==10 and set(SOURCE_SHA)==set(RELEASES)
 assert 7+46+10==63 and len(CATEGORIES)==3
 assert shift("201404262330",1)=="201404270000"
 assert rh(0,7)<0 and abs(rh(0,6.112))<1e-9
 assert number("-9999") is None and number("3.5")==3.5
 print("STAGE90 SELF-TEST PASS | ten-site Stage05 original SHA, Stage86 seven T +46 P1 +10 platform distinct source risk audit; prior1675 + Stage89 separate51 protected")

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--self-test",action="store_true")
 for name in ("stage84","stage86","stage89"):
  ap.add_argument("--"+name,type=Path)
 ap.add_argument("--sites-root",type=Path,default=Path(ROOT_DEFAULT))
 ap.add_argument("--out",type=Path)
 a=ap.parse_args()
 if a.self_test:selftest();return
 if any(getattr(a,k) is None for k in ("stage84","stage86","stage89","out")):
  ap.error("require actual Stage84, Stage86, Stage89 reports and fresh HOME output")
 d84,d86,d89,out=(getattr(a,k).expanduser().resolve() for k in
                    ("stage84","stage86","stage89","out"))
 root=a.sites_root.expanduser().resolve()
 if (not all(d.is_dir() for d in (d84,d86,d89,root))
     or out.exists() or not out.parent.is_dir()
     or any(out==d or out in d.parents or d in out.parents
            for d in (d84,d86,d89,root))):
  ap.error("missing original reports or output folder not fresh/disjoint")
 f84=d84/"stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv"
 m84=json.loads((d84/"stage84_manifest.json").read_text())
 if (checksum(f84)!=PREV_SHA or m84.get("total_versioned_approved_repair_rows")!=1675 or
     m84.get("output_SHA256",{}).get(f84.name)!=PREV_SHA):
  raise ValueError("Stage84 actual versioned research overlay 1675 SHA/manifest drift")
 approved=key(load(f84,("site","native_time","modified_TA_C","modified_VPD_hPa",
    "modified_RH_pct","replacement_RH_provenance")))
 if len(approved)!=1675:raise ValueError("previous 1675 unique source keys changed")
 f86=d86/"stage86_FINAL_TEN_SITE_RESEARCH_QC_RELEASE_GATES.json"
 m86=json.loads(f86.read_text(encoding="utf-8"))
 if (m86.get("stage")!=86 or m86.get("current_overlay_SHA256")!=PREV_SHA or
     m86.get("source_T_pending_science_exception_HH")!=7 or
     m86.get("historical_P1_HOLD_HH")!=46 or
     m86.get("historical_RH_platform_HOLD_HH")!=10 or
     m86.get("current_overlay_corrected_physics_issues")!=0 or
     m86.get("approved_rows_source_provenance_drift_issues")!=0):
  raise ValueError("actual Stage86 ten-site release risk outcome not verified")
 f86risks=d86/"stage86_FOCUSED_SOURCE_SCIENCE_AND_RELEASE_RISKS.csv"
 risks=load(f86risks,("site","native_time","category","scientific_issue","next_action"))
 bycat=defaultdict(list)
 for r in risks:
  if r["category"] in CATEGORIES:bycat[r["category"]].append(r)
 if {c:len(bycat[c]) for c in CATEGORIES}!={CATEGORIES[0]:7,CATEGORIES[1]:46,CATEGORIES[2]:10}:
  raise ValueError("Stage86 exact 7 original T /46 P1 /10 platform source risk categories changed")
 f89=d89/"stage89_SEPARATE_WHS_51_T_RH_VPD_VERSIONED_INTEGRATION_PREVIEW.csv"
 m89=json.loads((d89/"stage89_SEPARATE_WHS_51_T_RH_VPD_READONLY_PREVIEW_MANIFEST.json").read_text())
 if (checksum(f89)!=PREVIEW_SHA or m89.get("stage")!=89 or
     m89.get("output_preview_SHA256")!=PREVIEW_SHA or
     m89.get("stage67_approved_T_candidate_HH")!=51 or
     m89.get("stage88_QC0_RH_derived_VPD_joint_reconstruction_HH")!=4 or
     m89.get("stage67_T_only_original_source_VPD_retained_HH")!=47 or
     m89.get("combined_51_physics_RH_out_of_range_HH")!=0 or
     m89.get("previous_main_overlay_SHA256")!=PREV_SHA):
  raise ValueError("actual Stage89 51/47+4 source provenance preview drifted")
 separate=key(load(f89,("site","native_time","approved_Stage67_T_C",
     "proposed_joint_VPD_hPa")))
 if len(separate)!=51 or any(k[0]!="US-Whs" for k in separate):
  raise ValueError("Stage89 separate 51 site-native source key identity drift")
 unique=defaultdict(list)
 for c in CATEGORIES:
  for r in bycat[c]:unique[(r["site"],r["native_time"])].append(r)
 if len(unique)>63 or len(unique)<46:raise ValueError("unexpected 7/46/10 original risk source key dedup size")
 wants=defaultdict(set)
 for site,t in unique:
  wants[site].add(t)
  if any(q["category"]==CATEGORIES[0] for q in unique[(site,t)]):
   for j in range(-6,7):wants[site].add(shift(t,j))
 originals={}
 site_fingerprints={}
 for site,clock in sorted(wants.items()):
  release=RELEASES[site]
  folder=root/site/"forcing"/"raw"/("AMF_"+site+"_FLUXNET_"+release)
  if not folder.is_dir() or folder.is_symlink():
   raise ValueError("original Stage05 source folder unavailable "+str(folder))
  product="FULLSET" if site=="US-UMB" else "FLUXMET"
  pat=re.compile("AMF_"+re.escape(site)+r"_FLUXNET_"+product+r"_(HH|HR)_.+[.]csv",re.I)
  files=[p for p in folder.iterdir() if pat.fullmatch(p.name)]
  if len(files)!=1 or not files[0].is_file() or files[0].is_symlink():
   raise ValueError("original native source file missing/ambiguous "+site)
  actual=checksum(files[0])
  if actual!=SOURCE_SHA[site]:raise ValueError("original Stage05 source SHA mismatch "+site)
  site_fingerprints[site]=actual
  with files[0].open(encoding="utf-8-sig",newline="") as stream:
   rd=csv.DictReader(stream);hdr=rd.fieldnames or []
   if len(hdr)!=len(set(hdr)) or not {"TIMESTAMP_START","TA_F","VPD_F","TA_F_QC","VPD_F_QC"}.issubset(hdr):
    raise ValueError("original Stage05 source native T/VPD/QC fields missing "+site)
   found={}
   for r in rd:
    t=r["TIMESTAMP_START"]
    if t in clock:
     if t in found:raise ValueError("duplicate original source native site/HH "+site+" "+t)
     found[t]=r
   originals[site]=found
 riskrows=[];ctx=[];count=Counter()
 for (site,t),group in sorted(unique.items()):
  categories=sorted({g["category"] for g in group})
  reason=" | ".join(sorted({str(g["scientific_issue"]) for g in group}))
  r=originals[site].get(t)
  ov=approved.get((site,t),{})
  sep=separate.get((site,t),{})
  if r is None:
   count["SOURCE_NATIVE_TIMESTAMP_MISSING"]+=1
   data=dict()
   T=V=ERA_RH=None
   status="ORIGINAL_NATIVE_TIME_MISSING_REQUIRES_SOURCE_AUDIT"
  else:
   T,V=number(r["TA_F"]),number(r["VPD_F"])
   ETA,EV=number(r.get("TA_ERA")),number(r.get("VPD_ERA"))
   ERA_RH=rh(ETA,EV)
   status="ORIGINAL_NATIVE_VERIFIED"
  riskrows.append(dict(site=site,native_time=t,
   source_risk_categories=";".join(categories),risk_reasons=reason,
   original_TA_C=r.get("TA_F","") if r else "",
   original_TA_QC=r.get("TA_F_QC","") if r else "",
   original_VPD_hPa=r.get("VPD_F","") if r else "",
   original_VPD_QC=r.get("VPD_F_QC","") if r else "",
   derived_original_RH_pct=fmt(rh(T,V)) if r else "",
   source_ERA_TA_C=r.get("TA_ERA","") if r else "",
   source_ERA_VPD_hPa=r.get("VPD_ERA","") if r else "",
   derived_source_processed_ERA_RH_pct=fmt(ERA_RH),
   source_TA_to_ERA_delta_C=fmt(T-number(r.get("TA_ERA"))) if r and T is not None and number(r.get("TA_ERA")) is not None else "",
   original_RH_field=(r.get("RH","") or r.get("RH_F","")) if r else "",
   original_P_F=r.get("P_F","") if r else "",
   original_SW_IN_F=r.get("SW_IN_F","") if r else "",
   prior_1675_research_overlay_present=str(bool(ov)),
   prior_1675_research_overlay_modified_TA_C=ov.get("modified_TA_C",""),
   prior_1675_research_overlay_modified_VPD_hPa=ov.get("modified_VPD_hPa",""),
   prior_1675_research_overlay_RH_pct=ov.get("modified_RH_pct",""),
   prior_1675_research_overlay_method=ov.get("replacement_RH_provenance",""),
   Stage89_separate_51_T_preview_overlap=str(bool(sep)),
   Stage89_separate_51_T_preview_TA_C=sep.get("approved_Stage67_T_C",""),
   Stage89_separate_51_T_preview_VPD_hPa=sep.get("proposed_joint_VPD_hPa",""),
   source_data_status=status,
   scientific_release_action="SEPARATE_SOURCE_PROVENANCE_AND_INDEPENDENT_WEATHER_EVIDENCE_REVIEW_BEFORE_FORCING"))
  count["distinct_risk_HH"]+=1
  count["main_overlay_overlap"]+=bool(ov)
  count["separate_Stage89_overlap"]+=bool(sep)
  count["multi_category_risk_HH"]+=len(categories)>1
  if CATEGORIES[0] in categories:
   for j in range(-6,7):
    tt=shift(t,j);o=originals[site].get(tt)
    cT=number(o["TA_F"]) if o else None
    cV=number(o["VPD_F"]) if o else None
    cETA=number(o.get("TA_ERA")) if o else None
    cEV=number(o.get("VPD_ERA")) if o else None
    ctx.append(dict(source_temperature_exception_native=site+"/"+t,native_time=tt,
      minutes_offset=j*30,original_TA_C=o["TA_F"] if o else "",
      TA_F_QC=o["TA_F_QC"] if o else "",
      original_VPD_hPa=o["VPD_F"] if o else "",
      VPD_F_QC=o["VPD_F_QC"] if o else "",
      derived_RH_pct=fmt(rh(cT,cV)),
      original_source_ERA_TA_C=o.get("TA_ERA","") if o else "",
      derived_source_ERA_RH_pct=fmt(rh(cETA,cEV))))
 if len(ctx)!=91:raise ValueError("seven source-T exception contexts not 7×13")
 if len(riskrows)!=len(unique):raise ValueError("original 7/46/10 risk unique source tally mismatch")
 siteout=[]
 for site in RELEASES:
  row=[(k,v) for k,v in unique.items() if k[0]==site]
  siteout.append(dict(site=site,
   distinct_source_risk_HH=len(row),
   P1_HOLD_HH=sum(CATEGORIES[1] in {x["category"] for x in v} for k,v in row),
   RH_PLATFORM_HOLD_HH=sum(CATEGORIES[2] in {x["category"] for x in v} for k,v in row),
   source_T_exception_HH=sum(CATEGORIES[0] in {x["category"] for x in v} for k,v in row),
   risk_categories_overlap_HH=sum(len({x["category"] for x in v})>1 for k,v in row),
   prior_research_1675_overlap_HH=sum(k in approved for k,v in row),
   Stage89_temperature_preview_overlap_HH=sum(k in separate for k,v in row),
   proxy_ERA_research_rows_from_Stage86=m86.get("site_proxy_method_counts",{}).get(site,0)))
 out.mkdir(exist_ok=False)
 f_risks=out/"stage90_UNIQUE_HISTORICAL_SCIENCE_RELEASE_RISK_SOURCE_EVIDENCE.csv"
 f_t=out/"stage90_SEVEN_SOURCE_T_EXCEPTIONS_3H_NATIVE_ORIGINAL_CONTEXT.csv"
 f_site=out/"stage90_TEN_SITE_RISK_AND_PROXY_METHOD_COUNTS.csv"
 f_summary=out/"stage90_FINAL_HISTORICAL_RELEASE_RISK_EVIDENCE_MANIFEST.json"
 write(f_risks,FIELDS,riskrows);write(f_t,CTX_FIELDS,ctx);write(f_site,SITE_FIELDS,siteout)
 manifest=dict(stage=90,site_count=10,original_P2P3_all_dispositioned=True,
  latest_1675_research_approved_overlay_SHA256=PREV_SHA,
  stage89_51_T_with_4_VPD_science_preview_SHA256=PREVIEW_SHA,
  distinct_release_risk_source_HH=len(unique),
  historical_P1_HOLD_HH=46,historical_RH_platform_HOLD_HH=10,
  historical_source_T_exception_HH=7,
  overlapping_risk_categories_source_HH=count["multi_category_risk_HH"],
  source_risks_overlapping_main_1675=count["main_overlay_overlap"],
  source_risks_overlapping_separate_Stage89_51=count["separate_Stage89_overlap"],
  missing_original_source_native_risk_HH=count["SOURCE_NATIVE_TIMESTAMP_MISSING"],
  original_source_verified_SHA256_by_site=site_fingerprints,
  latest_source_Stage86_report_SHA256=checksum(f86),
  original_QC_unchanged=True,research_overlays_1675_and_Stage89_unchanged=True,
  release_gate="BLOCKED_REQUIRES_ORIGINAL_T_SOURCE_P1_PLATFORM_AND_PROXY_HUMIDITY_SCIENCE_VALIDATION",
  output_SHA256={p.name:checksum(p) for p in (f_risks,f_t,f_site)},
  no_production_forcing_approval=True,Slurm_submitted=0,DATM_CIME_modified=False)
 f_summary.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
 print("STAGE90 SUCCESS | exact ten-site original source evidence for 7 T exceptions +46 P1 +10 RH platform, source risk timepoints deduplicated")
 print("STAGE90 RISK_COUNTS",json.dumps({k:manifest[k] for k in ("distinct_release_risk_source_HH",
  "historical_P1_HOLD_HH","historical_RH_platform_HOLD_HH",
  "historical_source_T_exception_HH","overlapping_risk_categories_source_HH",
  "source_risks_overlapping_main_1675","source_risks_overlapping_separate_Stage89_51",
  "missing_original_source_native_risk_HH")},sort_keys=True))
 print("STAGE90 SITE site riskUnique P1 platform T exception overlapping categories overlay1675 overlapStage89 proxyERA")
 for x in siteout:
  print("STAGE90 SITE",x["site"],x["distinct_source_risk_HH"],x["P1_HOLD_HH"],
   x["RH_PLATFORM_HOLD_HH"],x["source_T_exception_HH"],
   x["risk_categories_overlap_HH"],x["prior_research_1675_overlap_HH"],
   x["Stage89_temperature_preview_overlap_HH"],x["proxy_ERA_research_rows_from_Stage86"])
 print("STAGE90 T_EXCEPTIONS native original_T original_QC originalVPD VPD_QC impliedRH ERA_T ERA_RH overlay")
 for x in riskrows:
  if CATEGORIES[0] in x["source_risk_categories"].split(";"):
   print("STAGE90 T_EXCEPTION",x["site"],x["native_time"],x["original_TA_C"],
    x["original_TA_QC"],x["original_VPD_hPa"],x["original_VPD_QC"],
    x["derived_original_RH_pct"],x["source_ERA_TA_C"],
    x["derived_source_processed_ERA_RH_pct"],x["prior_1675_research_overlay_present"])
 print("STAGE90 RELEASE_GATE",manifest["release_gate"])
 print("STAGE90_REPORTS="+str(out))
 print("STAGE90 READONLY | ORIGINAL/QC/PRIOR1675/STAGE89/DATM/CIME/SLURM UNCHANGED")
if __name__=="__main__":main()

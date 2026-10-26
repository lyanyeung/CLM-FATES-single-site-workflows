#!/usr/bin/env python3
"""Batch04 SYVH10: post-SYVH9 validated 10-site DATM Gate-1 technical metadata.

Read-only input sources, no NetCDF/DATM/CIME/Slurm or model writes.
Latest actual operator SYVH9 result: 12 independent ERA5-Land STRD HH,
5 site full source SHA, 10 of 10 native 7 met + NOLEAP Gate-0 PASS.
This script will NOT re-run or rewrite that scientific source QC.
Instead crosscheck:
- exact final SYVH9 ten-site source selection (all ten SHA256), receipt and
  latest full seven-met Gate-0 results JSON
- original provenance Stage05 3 sites + Stage08 7, original BIF site IDs,
  LAT, LON, UTC_OFFSET; original BIF SHA
- inventory (but do NOT guess/assign) instrument-specific heights for ZBOT;
  BIF canopy/flux/sonic height are not interchangeable. All real ZBOT
  remains NOT VERIFIED until a signed station observation-height source.
- point surface candidate/coordinates LONGXY/LATIXY and ambiguity, and
  potential domain-file inventory. Do not invent domain or surface choice.
- source time is LOCAL STANDARD START with 30-min record width; do not
  claim this implies actual active CIME DATM time-centered conventions.
- explicit native VPD source-quantization 3HH exceptions needing OUTPUT-
  ONLY saturated e=0 policy if/when building PREVIEW. Never edit source.

--self-test: numerical + fixed-site group checks, no writes
--check: only read source inputs, print metadata evidence
--report: same; write compact new UTC-stamped JSON/TSV under HOME only.

The Batch01 81_build_DATM_from_Stage80.py is reference precedent, NOT
permission to use its Stage80 source manifest, site ZBOT or case config for
this Batch04 project. Gate-1 statuses are NOT production approvals.
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
from uuid import uuid4
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=ROOT/"qcv5_stage05_candidates/candidate_20261024T103113Z/report.json"
S08=ROOT/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z/report.json"
SITES_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SYVH3_SHA="9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa"
EXPECTED={"US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
          "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf"}
THREE={"US-SP1","US-Syv","US-Ton"}
SEVEN=EXPECTED-THREE
FIVE_CORRECTED={"US-SP1","US-Slt","US-Syv","US-Ton","US-Uaf"}
SITE_FIELD_KEYS=("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET")
HEIGHThints=("HEIGHT","ZBOT","MEAS","SENSOR","SONIC","INSTRUMENT","HEIGHTC","TOWER")
VPD_ROUND_HH={("US-Rpf","200802060700"),
              ("US-Rpf","200802060900"),
              ("US-Syv","200803091300")}
NOLEAP_ROWS=365*48

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Missing/symlink source "+str(p))
    return p
def hashfile(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def jread(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def table(p,fields,sep="\t"):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter=sep)
        ck(rd.fieldnames is not None and set(fields).issubset(rd.fieldnames)
           and len(rd.fieldnames)==len(set(rd.fieldnames)),
           "Required scientific metadata schema not verified "+str(p))
        return list(rd)
def number(v):
    try:
        r=float(v)
        return r if math.isfinite(r) else None
    except (ValueError,TypeError):return None
def normlong(x):return (x+180)%360-180
def original_site_bif(spec,site):
    source=Path(spec["paths"]["native"])
    original=spec["source_provenance"]["native"]["sha256"]
    ck(hashfile(source)==original,"Original Stage05/08 native source SHA changed "+site)
    root=source.parent
    matches=list(root.glob("AMF_"+site+"_FLUXNET_BIF_*.csv"))
    ck(len(matches)==1,"Ambiguous/missing BIF station metadata "+site)
    p=regular(matches[0])
    r=table(p,("VARIABLE","DATAVALUE","GROUP_ID"),sep=",")
    coords={x:set() for x in SITE_FIELD_KEYS};heights=[]
    for z in r:
        ck(z.get("SITE_ID",site).strip() in ("",site),"BIF unrelated site "+site)
        k=z["VARIABLE"].strip().upper()
        if k in coords:
            v=number(z["DATAVALUE"])
            if v is not None:coords[k].add(v)
        if any(h in k for h in HEIGHThints):
            heights.append({"variable":z["VARIABLE"],
                            "value":z["DATAVALUE"],
                            "group_id":z["GROUP_ID"]})
    ck(all(len(y)==1 for y in coords.values()),
       "Nonunique actual native BIF station location/UTC offset "+site)
    lat=next(iter(coords["LOCATION_LAT"]))
    lon=next(iter(coords["LOCATION_LONG"]))
    offset=next(iter(coords["UTC_OFFSET"]))
    ck(-90<=lat<=90 and -180<=lon<=180 and
       offset.is_integer() and -12<=offset<=14,
       "BIF station/clock values impossible "+site)
    return {"tower_lat":lat,"tower_lon":lon,"UTC_OFFSET_hours":int(offset),
            "BIF_path":str(p),"BIF_SHA256":hashfile(p),
            "instrument_height_candidates_not_assigned_to_ZBOT":heights[:120],
            "height_candidate_count":len(heights),
            "site_native_original_SHA256":original}
def surface(site,point):
    folder=SITES_ROOT/site/"subset_data"
    sources=list(folder.glob("surfdata*.nc")) if folder.is_dir() else []
    response={"site":site,"candidate_count":len(sources),
              "surface_path":None,"surface_SHA256":None,
              "point_surface_coordinates":None,
              "surface_vs_BIF_lat_diff_degrees":None,
              "surface_vs_BIF_lon_diff_degrees":None,
              "status":"REQUIRES_POINT_SURFACE_REVIEW"}
    if len(sources)!=1:
        response["status"]="SURFACE_MISSING_OR_MULTIPLE"
        response["surface_candidate_files"]=[str(q) for q in sources[:20]]
        return response
    p=regular(sources[0]);response["surface_path"]=str(p)
    response["surface_SHA256"]=hashfile(p)
    try:
        import numpy as np
        from netCDF4 import Dataset
        with Dataset(str(p),"r") as ds:
            ck(all(k in ds.variables for k in ("LONGXY","LATIXY")),
               "Existing point surface has no LONGXY/LATIXY "+site)
            la=np.ma.asarray(ds.variables["LATIXY"][:]).filled(np.nan).reshape(-1)
            lo=np.ma.asarray(ds.variables["LONGXY"][:]).filled(np.nan).reshape(-1)
        ck(len(la)==len(lo)==1 and
           math.isfinite(float(la[0])) and math.isfinite(float(lo[0])),
           "Expected 1x1 finite point surface coordinates "+site)
        lat,lon=float(la[0]),normlong(float(lo[0]))
        response["point_surface_coordinates"]={"lat":lat,"lon":lon}
        response["surface_vs_BIF_lat_diff_degrees"]=round(abs(lat-point["tower_lat"]),6)
        response["surface_vs_BIF_lon_diff_degrees"]=round(
            abs(normlong(lon-point["tower_lon"])),6)
        response["status"]="POINT_SURFACE_COORDINATES_READABLE_NOT_YET_CASE_APPROVED"
    except ImportError:
        response["status"]="POINT_SURFACE_PRESENT_NETCDF4_NOT_INSTALLED"
    return response
def domains(site):
    root=SITES_ROOT/site
    paths=[]
    for folder in (root,root/"subset_data"):
        if folder.is_dir():
            paths += [str(p) for p in folder.glob("*domain*.nc") if p.is_file()]
    return sorted(set(paths))[:25]
def audit(folder):
    source=jread(folder/"SYVH9_SCIENCE_RECEIPT.json")
    ck(source.get("stage")=="SYVH9_INDEPENDENT_ERA5LAND_DEACCUMULATED_STRD" and
       source.get("independently_retrieved_source_hh")==12 and
       source.get("research_only") is True and
       source.get("model_ready") is False and
       source.get("Postv5_ready") is False,
       "SYVH9 independently repaired 12HH source not research-only PASS")
    manifest=folder/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    ck(Path(source["new_manifest_path"])==manifest and
       hashfile(manifest)==source["new_manifest_sha256"],
       "Newest operator approved research-only ten-site source manifest SHA changed")
    m=table(manifest,("site","source_path","source_SHA256","latest_stage"))
    ck(len(m)==10 and {x["site"] for x in m}==EXPECTED,
       "Final 10 source selections missing/duplicated")
    result=jread(folder/"SYVH9_TEN_SITE_GATE0_READONLY_RESULTS.json")
    ck(result["numeric_gate0_pass"] is True and
       not result["blocked"] and
       result["native_VPD_source_rounding_HH"]==3 and
       {r["site"] for r in result["ten_sites"]}==EXPECTED and
       all(not r["numeric_blockers"] for r in result["ten_sites"]),
       "Operator SYVH9 seven-met NOLEAP numeric 10/10 gate evidence changed")
    stage5=jread(S05);stage8=jread(S08)
    ck(set(stage5["sites"])==THREE and set(stage8["sites"])==SEVEN,
       "Stage05 three-site and Stage08 seven-site source metadata group changed")
    original=stage5["sites"]|stage8["sites"]
    newsha=source["new_selected_site_SHAs"]
    ck(set(newsha)==FIVE_CORRECTED,
       "Unexpected count of 5 independently longwave-corrected files")
    sitechecks={r["site"]:r for r in result["ten_sites"]}
    allout=[]
    for x in sorted(m,key=lambda d:d["site"]):
        site=x["site"];file=Path(x["source_path"])
        ck(hashfile(file)==x["source_SHA256"],
           "Complete selected source SHA changed "+site)
        if site in FIVE_CORRECTED:
            ck(file.parent==folder and
               x["source_SHA256"]==newsha[site],
               "Five original independent-LW corrected sites source version changed "+site)
        bif=original_site_bif(original[site],site)
        sf=surface(site,bif)
        related=domains(site)
        summary=sitechecks[site]
        ck(summary["source_halfhours"]>10000 and
           summary["numeric_gate_no_blockers"] is True and
           summary["SHA256"]==x["source_SHA256"] and
           summary["model_noleap_halfhours"]%NOLEAP_ROWS==0,
           "Site complete NOAA/NOLEAP/QBOT source checksum drift "+site)
        note={
          "site":site,"source_SHA256":x["source_SHA256"],
          "source_path":str(file),"source_processing_stage":x["latest_stage"],
          "BIF":bif,"point_surface":sf,
          "domain_candidates_not_approved":related,
          "Gate0_native_source_rows":summary["source_halfhours"],
          "Gate0_noleap_rows":summary["model_noleap_halfhours"],
          "source_years":summary["source_years"],
          "Gate0_source_rounding_HH":summary[
             "conservative_nonproduction_policy_flags"].get(
                  "VPD_NATIVE_THREE_DECIMAL_ROUNDING",0),
          "source_7met_numeric_OK":True,
          "DATM_time_centering_verified":False,
          "ZBOT_sensor_height_verified":False,
          "active_CIME_field_map_verified":False,
          "site_point_surface_domain_approved":False,
          "source_scientific_production_release":False}
        allout.append(note)
        print("GATE1 SITE",site,"BIF_LAT",bif["tower_lat"],
              "BIF_LON",bif["tower_lon"],"UTC_OFFSET",bif["UTC_OFFSET_hours"],
              "MET_YEARS",summary["source_years"],
              "GATE0_SOURCE_SHA",x["source_SHA256"],
              "SURFACE",sf["status"],
              "SURFACE_DELTA_LAT_LON",
              [sf["surface_vs_BIF_lat_diff_degrees"],
               sf["surface_vs_BIF_lon_diff_degrees"]],
              "HEIGHT_METADATA_CANDIDATES",bif["height_candidate_count"],
              "DOMAINS_UNVERIFIED",len(related),
              "ROUNDING_HH",note["Gate0_source_rounding_HH"])
        if bif["height_candidate_count"]:
            print("BIF HEIGHT ATTRIBUTES NEED SENSOR SPECIFIC EVIDENCE",site,
                  bif["instrument_height_candidates_not_assigned_to_ZBOT"][:8])
    ck(sum(x["Gate0_source_rounding_HH"] for x in allout)==3,
       "Final VPD three-decimal provenance changed")
    return {"source_dir":str(folder),"source_manifest_SHA256":source["new_manifest_sha256"],
            "ten_full_source_sha_verified":True,"source_12_independent_LW_applied":True,
            "ten_noleap_met_gate0_pass":True,"sites":allout,
            "all_ZBOT_verified":False,"all_time_centering_verified":False,
            "all_active_CIME_mapping_verified":False,
            "all_source_production_science_approved":False,
            "postv5_technical_preflight_only":True,
            "DATM_ready":False,"model_jobs_submitted":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-dir",required=False,
       default=str(ROOT/"manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f"))
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--report",action="store_true")
    a=p.parse_args()
    ck(len(EXPECTED)==10 and len(THREE)==3 and len(SEVEN)==7 and
       len(FIVE_CORRECTED)==5 and len(VPD_ROUND_HH)==3 and
       (datetime(2004,2,29)+timedelta(days=1)).date().isoformat()=="2004-03-01",
       "SYVH10 source roster, noleap or rounding self-test failed")
    print("SYVH10 SELF-TEST PASS exact ten site source provenance, 3+7, 5 corrected, 3 VPD rounding, NO WRITES")
    if a.self_test:return
    folder=Path(a.candidate_dir)
    ck(folder.is_dir() and not folder.is_symlink(),
       "Actual operator final SYVH9 research-only source directory absent")
    summary=audit(folder)
    print("SYVH10 SOURCE PROVENANCE AND POSTV5 DATM METADATA GATE1 AUDIT COMPLETE")
    print("GATE1 10_SITE_MET_NUMERIC",summary["ten_noleap_met_gate0_pass"],
          "ZBOT_VERIFIED",summary["all_ZBOT_verified"],
          "TIMECENTER_VERIFIED",summary["all_time_centering_verified"],
          "ACTIVE_CASE_MAPPING_VERIFIED",summary["all_active_CIME_mapping_verified"],
          "SCIENCE_RELEASE",summary["all_source_production_science_approved"])
    print("DATM/CIME/SLURM/MODEL SPINUP NOT AUTHORISED; NO SOURCE OR CASE WRITES")
    if a.report:
        out=Path.home()/"ameriflux_batch04_manual_review"
        out.mkdir(parents=True,exist_ok=True)
        tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
        js=out/("Batch04_SYVH10_Postv5_10site_DATM_metadata_"+tag+".json")
        ts=out/("Batch04_SYVH10_Postv5_10site_DATM_metadata_"+tag+".tsv")
        js.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        with ts.open("x",newline="",encoding="utf-8") as f:
            w=csv.writer(f,delimiter="\t")
            w.writerow(["site","UTC_OFFSET_hours","BIF_Lat","BIF_Lon",
                       "BIF_height_attributes","surface_status",
                       "surface_delta_lat","surface_delta_lon",
                       "domain_candidates","ZBOT_approved","time_centering_approved",
                       "SHA256"])
            for r in summary["sites"]:
                b=r["BIF"];surf=r["point_surface"]
                w.writerow([r["site"],b["UTC_OFFSET_hours"],
                   b["tower_lat"],b["tower_lon"],b["height_candidate_count"],
                   surf["status"],surf["surface_vs_BIF_lat_diff_degrees"],
                   surf["surface_vs_BIF_lon_diff_degrees"],
                   len(r["domain_candidates_not_approved"]),False,False,
                   r["source_SHA256"]])
        print("SYVH10 METADATA REPORT",js,"SHA",hashfile(js))
        print("SYVH10 METADATA TSV",ts,"SHA",hashfile(ts))
if __name__=="__main__":main()

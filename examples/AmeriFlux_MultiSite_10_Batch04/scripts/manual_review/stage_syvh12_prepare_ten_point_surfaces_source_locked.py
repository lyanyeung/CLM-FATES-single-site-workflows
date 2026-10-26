#!/usr/bin/env python3
"""Batch04 SYVH12 — optional CREATE of 10 isolated, provisional CTSM surfaces.

Use only the USER-VERIFIED SYVH9 final ten meteorology research manifest and
Stage05 (3) / Stage08 (7) original FLUXNET BIF source provenance. Reuse
previously user-approved US-Seg GROUP_ID=1495 (coordinate_decisions.tsv).

--self-test : synthetic metadata/template routing, no writes
--preflight : verify all ten source SHAs, site BIF coordinates/approval,
              local CTSM subset_data CLI, inputdata, config; no writes
--build     : same preflight, then create ten NEW, ISOLATED provisional point
              surface+user_mods candidates under experiment stage12 folder.
              Never overwrite original surface, existing source, production
              user_mods, NetCDF/DATM/CIME cases, or run Slurm.
              Fail closed if the configured CTSM data template differs from
              the exact archived six-site reference policy.

The background grid YEAR 2000 is an EXPLORATORY technical surface source,
not a validation of real tower PFT/soil/topography. Each surface and its
metadata must be audited separately before model approval. Does not choose
ZBOT, invent meteorological height, infer FATES observed PFT, or write domain
configuration. Candidate outputs are not active in any CIME case.
"""
import argparse,csv,hashlib,json,math,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
EXP=ROOT/"experiments/AmeriFlux_MultiSite_10_Batch04"
FINAL=EXP/("manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_"
            "research_not_approved/candidate_20261026T121123Z_a8b8146f")
STAGE05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z/report.json"
STAGE08=EXP/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z/report.json"
SITES=ROOT/"sites/MY_EC_SITE"
CTSM=ROOT/"CTSM"
INPUTDATA=ROOT/"inputdata"
CMD=CTSM/"tools/site_and_regional/subset_data"
TEMPLATE=CTSM/"tools/site_and_regional/default_data_2000.cfg"
COORD_FILE=Path(__file__).resolve().with_name("Batch04_approved_coordinate_decisions.tsv")
DEST=EXP/"stage12_provisional_ctsm_point_surfaces_RESEARCH_ONLY"
EXACT_SITES=("US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
             "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf")
PRIORITY={"US-SP1","US-Syv","US-Ton"}
HEIGHT_NOT_AVAILABLE=True
LON_TOL_DEG=.7501
LAT_TOL_DEG=.5501
APPROVED={"site":"US-Seg","package":"AMF_US-Seg_FLUXNET_2007-2025_v1.3_r1",
          "group_id":"1495","latitude":"34.3623","longitude":"-106.7020",
          "elevation_m":"1596","location_date_start":"200701010000",
          "approval":"APPROVED_BY_USER"}
SIX_SITE_CFG_REFERENCE={
  "surfdat_16pft":"surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc",
  "mesh_surf":"fv0.9x1.25_141008_ESMFmesh.nc"}
EXPECTED_INPUT_N=10

def ck(ok,msg):
    if not ok:raise RuntimeError(msg)
def f(p):
    ck(p.is_file() and not p.is_symlink(),"Source path missing or symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with f(p).open("rb") as x:
        for chunk in iter(lambda:x.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()
def meta(p):return json.loads(f(p).read_text(encoding="utf-8"))
def csvread(p,needed,sep=","):
    with f(p).open(encoding="utf-8-sig",newline="") as x:
        rd=csv.DictReader(x,delimiter=sep)
        ck(rd.fieldnames is not None and
           set(needed).issubset(rd.fieldnames),"Unexpected source fields "+str(p))
        return list(rd)
def num(x):
    try:
        y=float(x)
        return y if math.isfinite(y) and y!=-9999 else None
    except (TypeError,ValueError):return None
def approves():
    rows=csvread(COORD_FILE,tuple(APPROVED),"\t")
    ck(len(rows)==1 and rows[0]==APPROVED,
       "The unique signed user US-Seg 1495 original BIF approval changed")
    return rows[0]
def station_coords(p,site,approved):
    rows=csvread(p,("VARIABLE","DATAVALUE","GROUP_ID"))
    coord={key:set() for key in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET")}
    selected={key:set() for key in
        ("LOCATION_LAT","LOCATION_LONG","LOCATION_ELEV","LOCATION_DATE_START")}
    for row in rows:
        ck((row.get("SITE_ID") or site).strip() in ("",site),
           "Foreign SITE_ID in original BIF "+site)
        name=(row["VARIABLE"] or "").strip().upper()
        text=(row.get("DATAVALUE") or "").strip()
        value=num(text)
        if name in coord and value is not None:coord[name].add(value)
        if (site=="US-Seg" and row["GROUP_ID"].strip()=="1495"
              and name in selected and text and text!="-9999"):
            selected[name].add(text)
    ck(len(coord["UTC_OFFSET"])==1,"Missing/multiple site UTC offsets "+site)
    offset=next(iter(coord["UTC_OFFSET"]))
    if site=="US-Seg":
        ck({num(v) for v in selected["LOCATION_LAT"]}=={34.3623} and
           {num(v) for v in selected["LOCATION_LONG"]}=={-106.7020} and
           {num(v) for v in selected["LOCATION_ELEV"]}=={1596.} and
           selected["LOCATION_DATE_START"]=={"200701010000"},
           "Original BIF approved US-Seg group1495 coordinates changed")
        lat,lon=34.3623,-106.702
        ck(lat in coord["LOCATION_LAT"] and lon in coord["LOCATION_LONG"]
            and offset==-7,"US-Seg exact approved BIF/offset conflict")
    else:
        ck(len(coord["LOCATION_LAT"])==1 and
           len(coord["LOCATION_LONG"])==1,
           "Unapproved BIF location ambiguity "+site)
        lat=next(iter(coord["LOCATION_LAT"]))
        lon=next(iter(coord["LOCATION_LONG"]))
    ck(-90<=lat<=90 and -180<=lon<=180 and
       float(offset).is_integer() and -12<=offset<=14,
       "Invalid BIF coordinates or local-standard UTC offset "+site)
    return {"site":site,"lat":lat,"lon":lon,"UTC_OFFSET":int(offset),
            "original_BIF":str(p),"original_BIF_SHA256":sha(p),
            "approval":"PREVIOUS_USER_APPROVED_BIF_1495" if site=="US-Seg"
                       else "SINGLE_UNIQUE_ORIGINAL_BIF"}
def verify_inputs():
    receipt=meta(FINAL/"SYVH9_SCIENCE_RECEIPT.json")
    ck(receipt.get("stage")=="SYVH9_INDEPENDENT_ERA5LAND_DEACCUMULATED_STRD" and
       receipt.get("independently_retrieved_source_hh")==12 and
       receipt.get("research_only") is True and
       receipt.get("model_ready") is False,
       "Operator SYVH9 original final source not research-only numeric PASS")
    manifest=FINAL/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    ck(sha(manifest)==receipt["new_manifest_sha256"],
       "Final operator selected 10-site manifest SHA mismatch")
    rows=csvread(manifest,("site","source_path","source_SHA256","latest_stage"),"\t")
    ck(len(rows)==10 and {r["site"] for r in rows}==set(EXACT_SITES),
       "Final source site roster differs from operator SYVH9")
    for row in rows:
        ck(sha(Path(row["source_path"]))==row["source_SHA256"],
           "Original site seven-met source SHA changed "+row["site"])
    gate=meta(FINAL/"SYVH9_TEN_SITE_GATE0_READONLY_RESULTS.json")
    ck(gate["numeric_gate0_pass"] is True and not gate["blocked"] and
       gate["native_VPD_source_rounding_HH"]==3,
       "SYVH9 complete 10-site seven-met numerical Gate-0 no longer PASS")
    before=meta(STAGE05)["sites"];later=meta(STAGE08)["sites"]
    ck(set(before)==PRIORITY and
       set(later)==set(EXACT_SITES)-PRIORITY,
       "Original full BIF provenance Stage05 3 / Stage08 7 changed")
    approval=approves()
    selected=[]
    for site in EXACT_SITES:
        spec=before[site] if site in PRIORITY else later[site]
        source=Path(spec["paths"]["native"])
        ck(sha(source)==spec["source_provenance"]["native"]["sha256"],
           "Original FLUXMET provenance SHA mismatch "+site)
        bifs=list(source.parent.glob("AMF_"+site+"_FLUXNET_BIF_*.csv"))
        ck(len(bifs)==1,"Original BIF source not unique "+site)
        p=station_coords(bifs[0],site,approval)
        selected.append(p)
        print("SYVH12 PINNED",site,"LAT",p["lat"],"LON",p["lon"],
              "UTC_OFFSET",p["UTC_OFFSET"],"BIF_SHA",p["original_BIF_SHA256"])
    print("SYVH12 TEN FINAL SOURCE SHA AND ORIGINAL BIF COORDINATES PASS")
    return selected,sha(manifest)
def cfg_text(text):
    # Archive six-site technical base, no PFT or soil site customisation.
    # Refuse silent changes of the global CTSM grid template.
    src=text
    src=src.replace("dir = lnd/clm2/surfdata_esmf/ctsm5.4.0",
                    "dir = lnd/clm2/surfdata_esmf/ctsm5.3.0")
    for var,new in SIX_SITE_CFG_REFERENCE.items():
        rexp=rf"(?m)^(\s*{var}\s*=\s*)([^\n]+)$"
        matches=list(re.finditer(rexp,src))
        ck(len(matches)==1,"Unexpected CTSM site config "+var+" lines")
        src=re.sub(rexp,lambda m:m.group(1)+new,src,count=1)
    ck(all(re.search(rf"(?m)^\s*{name}\s*=\s*{re.escape(value)}\s*$",src)
           for name,value in SIX_SITE_CFG_REFERENCE.items()),
       "CTSM six-site-compatible surface and mesh base config not verified")
    return src
def live_preflight():
    ck(CTSM.is_dir() and INPUTDATA.is_dir() and SITES.is_dir(),
       "Missing CTSM, inputdata or MY_EC_SITE root")
    ck(CMD.is_file() and not CMD.is_symlink(),
       "CTSM site/regional subset_data point executable not found")
    ck(TEMPLATE.is_file() and not TEMPLATE.is_symlink(),
       "CTSM default_data_2000.cfg reference absent")
    cfg=cfg_text(f(TEMPLATE).read_text(encoding="utf-8"))
    ck("surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc" in cfg and
       "fv0.9x1.25_141008_ESMFmesh.nc" in cfg,
       "Reference six-site original CTSM gridded source changed")
    return cfg
def surface_audit(output,lat,lon):
    matches=[p for p in output.rglob("*.nc") if
             p.is_file() and not p.is_symlink() and "surfdata" in p.name.lower()]
    ck(len(matches)==1,
       "Expected exactly 1 provisional surface under new site output "+
       str(output)+", saw "+repr(matches[:6]))
    p=matches[0]
    import numpy as np
    from netCDF4 import Dataset
    with Dataset(str(p),"r") as ds:
        ck("LATIXY" in ds.variables and "LONGXY" in ds.variables,
           "No point surface coordinate fields "+str(p))
        la=np.ma.asarray(ds.variables["LATIXY"][:]).filled(np.nan).reshape(-1)
        lo=np.ma.asarray(ds.variables["LONGXY"][:]).filled(np.nan).reshape(-1)
        ck(len(la)==len(lo)==1 and np.isfinite(la[0]) and
           np.isfinite(lo[0]),"Not 1x1 site point surface")
        x,y=float(la[0]),(float(lo[0])+180)%360-180
        diff=(abs(lat-x),abs((lon-y+180)%360-180))
        ck(diff[0]<=LAT_TOL_DEG and diff[1]<=LON_TOL_DEG,
           "Site surface gridded center differs too far from tower "+repr(diff))
        fieldlist=list(ds.variables)
        ck(any(q in fieldlist for q in ("PCT_NATVEG","PCT_NAT_PFT")),
           "Gridded site surface has no natural land/PFT variables")
    return {"surfdata_path":str(p),"SHA256":sha(p),
            "point_surface_center":[x,y],
            "tower_vs_surface_center_deg":list(diff),
            "fields":fieldlist}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--preflight",action="store_true")
    modes.add_argument("--build",action="store_true")
    args=p.parse_args()
    ck(len(EXACT_SITES)==EXPECTED_INPUT_N and len(PRIORITY)==3 and
       len(set(EXACT_SITES)-PRIORITY)==7 and
       APPROVED["group_id"]=="1495" and
       cfg_text("dir = lnd/clm2/surfdata_esmf/ctsm5.4.0\n"+
            "surfdat_16pft = old.nc\nmesh_surf = oldmesh.nc\n"
          ).count("ctsm5.3.0")==1,
       "SYVH12 exact ten/Stage05+08/approved Seg and sample config test failed")
    print("SYVH12 SYNTHETIC SELF-TEST PASS exact sites, source policy, no writes")
    if args.self_test:return
    sites,manifestsha=verify_inputs()
    cfg=live_preflight()
    print("SYVH12 LIVE CTSM/INPUTDATA/SUBSET_DATA DEFAULT 2000 MESH AND SURF PRECHECK PASS")
    if args.preflight:return
    ck(not DEST.is_symlink(),"Unsafe research output root symlink")
    if not DEST.exists():DEST.mkdir(parents=True)
    # Only generate to a completely new named candidate. Failed partial
    # outputs are retained for forensic inspection, never overwritten.
    output=DEST/("candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
                 "_"+uuid4().hex[:8])
    output.mkdir(parents=False,exist_ok=False)
    (output/"RESEARCH_ONLY_NO_CIME_SLURM_SOURCE_WRITES").write_text(
        "Site surface YEAR2000 default gridded 16-PFT. Requires PFT, soil, domain and ZBOT science review before model.\n")
    results=[]
    for station in sites:
        site=station["site"]
        work=output/site
        work.mkdir(exist_ok=False)
        cf=work/(site+"_CTSM_default_2000_stage12.cfg")
        cf.write_text(cfg,encoding="utf-8")
        out=work/"subset_data"
        out.mkdir(exist_ok=False)
        argv=[str(CMD),"point","--lat",str(station["lat"]),
              "--lon",str(station["lon"]),"--lon-type","180",
              "--site",site,"--surf-year","2000",
              "--create-surface","--create-user-mods",
              "--inputdata-dir",str(INPUTDATA),"--cfg-file",str(cf),
              "--outdir",str(out)]
        print("SYVH12 GENERATE ISOLATED RESEARCH SURFACE",site,
              "COMMAND",argv,flush=True)
        log=work/(site+"_subset_data_stdout_stderr.log")
        with log.open("x",encoding="utf-8") as stream:
            proc=subprocess.run(argv,cwd=str(CTSM),stdout=stream,
                                stderr=subprocess.STDOUT,check=False)
        ck(proc.returncode==0,"CTSM subset_data failed for "+site+
           " see "+str(log)+" — partial output retained, NO overwrites")
        x=surface_audit(out,station["lat"],station["lon"])
        result={**station,**x,"case_or_production_approved":False,
                "site_surface_is_generated_from_gridded_year_2000":True,
                "PFT_site_representation_science_approved":False,
                "ZBOT_observation_height_m":None,"ZBOT_verified":False,
                "active_domain":None,"active_case":None,
                "config_SHA256":sha(cf),"log_SHA256":sha(log)}
        results.append(result)
        print("SYVH12 GENERATED SURFACE POINT SHA VERIFIED",site,
              x["SHA256"],"GRID_CENTER",x["point_surface_center"],
              "TOWER_VS_CENTER_DEG",x["tower_vs_surface_center_deg"],flush=True)
    ck(len(results)==10,"Ten site generation did not complete")
    receipt={"stage":"SYVH12_ISOLATED_GRIDDed_POINT_SURFACES_RESEARCH_ONLY",
             "original_SYVH9_met_manifest_SHA256":manifestsha,
             "selected_sites":results,"n_site_surfaces_sha_verified":10,
             "user_original_BIF_coordinate_decision_SHA":sha(COORD_FILE),
             "CTSM_template_original_SHA":sha(TEMPLATE),
             "surface_reference_year":2000,
             "source_gridded_PFT_validated_at_EC_tower":False,
             "source_soil_PFT_science_validated":False,
             "postv5_approved":False,"CIME_or_DATM_ready":False,
             "ZBOT_verified":False,"domain_approved":False,
             "submitted_Slurm_jobs":False}
    rec=output/"SYVH12_RESEARCH_SURFACES_RECEIPT.json"
    rec.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("SYVH12 TEN ISOLATED POINT SURFACE CANDIDATES CREATED 10/10",output)
    print("SYVH12 SCIENCE/INPUT GRID SURFACE AUDIT REQUIRED BEFORE APPROVAL")
    print("SYVH12 NO ORIGINAL/BIF/SURFACE/CASE/DATM/CIME/SLURM SOURCE WRITES")
if __name__=="__main__":main()

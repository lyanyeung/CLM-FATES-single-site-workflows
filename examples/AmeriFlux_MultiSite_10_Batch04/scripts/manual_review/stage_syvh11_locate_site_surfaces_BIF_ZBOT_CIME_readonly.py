#!/usr/bin/env python3
"""Batch04 SYVH11 — bounded discovery of actual surface/domain, BIF TA/WS
sensor-height histories, and existing CIME/DATM case configuration.

Operates only on source-verified SYVH9/SYVH10 operator receipts and original
Stage05+Stage08 raw BIF files. Does not choose or generate surface or ZBOT;
does not edit original files, CIME cases or any sources. Optional --report
writes only a small JSON/TSV under $HOME.

Why: SYVH10 only checked MY_EC_SITE/$SITE/subset_data/surfdata*.nc at
ONE directory level; "SURFACE_MISSING_OR_MULTIPLE" cannot prove global
absence. Search bounded per-site paths plus likely local cases, never walk
all of scratch recursively and never perform unbounded rglob.

Height evidence comes only from original BIF pairs
  VAR_INFO_VARNAME, VAR_INFO_HEIGHT, VAR_INFO_DATE
grouped by VARIABLE_GROUP + GROUP_ID, following verified FLUXNET_MultiSite_6
BIF extraction precedent. HEIGHTC is CANOPY height and NEVER a ZBOT.
TA vs WS measurements / dates may differ; inventory, do not choose a
height nor extrapolate before first observation.

--self-test: exact site roster & synthetic grouped BIF tests, no FS changes
--check: all reads, console inventory, no FS writes
--report: same plus small timestamped HOME report files.
"""
import argparse,csv,hashlib,json,math,os,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
EXP=ROOT/"experiments/AmeriFlux_MultiSite_10_Batch04"
FINAL=EXP/("manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_"
          "research_not_approved/candidate_20261026T121123Z_a8b8146f")
SITES_BASE=ROOT/"sites/MY_EC_SITE"
S05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z/report.json"
S08=EXP/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z/report.json"
SITE_NAMES=("US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
            "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf")
THREE={"US-SP1","US-Syv","US-Ton"}
FIVE={"US-SP1","US-Slt","US-Syv","US-Ton","US-Uaf"}
CASE_BASES=(ROOT/"cases",
            Path("/scratch/ly3n24/CLM_FATES/cases"),
            Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases"))
ALL_META_KEYS=("VAR_INFO_VARNAME","VAR_INFO_HEIGHT","VAR_INFO_DATE")
SURFACE_SUBDIRS=("subset_data","subset_data/output","forcing","forcing/surface",
                 "surface","surface_data","inputdata","")
SURF_PATTERN=re.compile(r"(?:surfdata|surfdat)[^/]*\.nc$",re.I)
DOMAIN_PATTERN=re.compile(r"(?:domain|mesh)[^/]*\.nc$",re.I)
RELEVANT_CONFIG=re.compile(r"fsurdat|domain|meshfile|streams|zbot|dtlimit|time|file_path|atm_in|lnd_in",re.I)
MAX_CASES_PER_SITE=8
MAX_DISCOVERED_PER_SITE=40
MAX_CONFIG_BYTES=4_000_000

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def file(path):
    ck(path.is_file() and not path.is_symlink(),"Missing/unsafe source file "+str(path))
    return path
def sha(path):
    h=hashlib.sha256()
    with file(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()
def j(path):return json.loads(file(path).read_text(encoding="utf-8"))
def tsv(path,columns,sep="\t"):
    with file(path).open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream,delimiter=sep)
        ck(reader.fieldnames and
           set(columns).issubset(reader.fieldnames) and
           len(reader.fieldnames)==len(set(reader.fieldnames)),
           "Unexpected metadata file field layout "+str(path))
        return list(reader)
def float_or_none(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v!=-9999 else None
    except (TypeError,ValueError):return None
def kind(variable):
    var=(variable or "").strip().upper()
    for name in ("SW_IN","LW_IN","WIND","VPD","TA","WS","RH","PA","P"):
        if (var==name or var.startswith(name+"_")) and
           not var.endswith(("_F_QC","_ERA")):
            return name
    return None
def read_grouped_height_rows(rows,site):
    group=defaultdict(dict);canopy=[];good=[]
    for r in rows:
        ck((r.get("SITE_ID") or site).strip() in ("",site),"BIF SITE_ID mismatch "+site)
        key=((r.get("VARIABLE_GROUP") or "").strip().upper(),
             (r.get("GROUP_ID") or "").strip())
        field=(r.get("VARIABLE") or "").strip().upper()
        val=(r.get("DATAVALUE") or "").strip()
        # Reject conflicting metadata rows inside the exact original group.
        if field in ALL_META_KEYS and field in group[key] and
           group[key][field]!=val:
            group[key].setdefault("_GROUP_CONFLICTS",[]).append(
                (field,group[key][field],val))
        if field in ALL_META_KEYS:group[key][field]=val
        if field=="HEIGHTC":
            h=float_or_none(val)
            if h is not None and 0<=h<=150:
                canopy.append({"height_m":h,"group_id":key[1],
                               "variable_group":key[0]})
    for (groupname,gid),r in group.items():
        v=r.get("VAR_INFO_VARNAME","")
        k=kind(v)
        h=float_or_none(r.get("VAR_INFO_HEIGHT"))
        if k:
            good.append({"site":site,"source_BIF_group":gid,
                         "variable_group":groupname,"variable":v,
                         "kind":k,"height_m":h,
                         "source_height_raw":r.get("VAR_INFO_HEIGHT",""),
                         "source_date":r.get("VAR_INFO_DATE",""),
                         "metadata_conflicts":r.get("_GROUP_CONFLICTS",[])})
    met={x:sorted({float(z["height_m"]) for z in good
                   if z["kind"]==x and z["height_m"] is not None and
                   .5<=z["height_m"]<=150})
         for x in ("TA","WS","WIND","RH","VPD")}
    return good,canopy,met
def site_bif(site,spec):
    native=Path(spec["paths"]["native"])
    ck(sha(native)==spec["source_provenance"]["native"]["sha256"],
       "Stage05/Stage08 original native source SHA mismatch "+site)
    bifs=sorted(native.parent.glob("AMF_"+site+"_FLUXNET_BIF_*.csv"))
    ck(len(bifs)==1,"Expected one exact original site BIF "+site)
    bif=bifs[0]
    rows=tsv(bif,("VARIABLE","DATAVALUE","GROUP_ID"),sep=",")
    met,canopy,summary=read_grouped_height_rows(rows,site)
    return {"path":str(bif),"sha256":sha(bif),"sensor_metadata":met,
            "canopy_HEIGHTC_not_ZBOT":canopy,"heights_by_variable":summary,
            "atmospheric_TA_height_unique":len(summary["TA"])==1,
            "ZBOT_authorized":False,"ZBOT_value_m":None}
def safe_children(root,site):
    if not root.is_dir() or root.is_symlink():return []
    # Keep this deliberately bounded. Never recurse into global inputdata.
    dirs=[root]
    for part in SURFACE_SUBDIRS[:-1]:
        sub=root/part
        if sub.is_dir() and not sub.is_symlink():dirs.append(sub)
    results=[]
    for d in dirs:
        try:
            for child in d.iterdir():
                if len(results)>=MAX_DISCOVERED_PER_SITE:break
                if child.is_symlink() or not child.is_file():continue
                if (SURF_PATTERN.search(child.name) or
                    DOMAIN_PATTERN.search(child.name)):
                    results.append(child)
        except (PermissionError,OSError):continue
    return list(dict.fromkeys(results))
def surfaces(site,point):
    roots=[SITES_BASE/site,
           ROOT/"sites"/"MY_EC_SITE"/site,
           ROOT/"sites"/site]
    files={}
    for root in dict.fromkeys(roots):
        for p in safe_children(root,site):
            files[str(p)]=p
    summary=[]
    for p in sorted(files.values(),key=str):
        info={"path":str(p),"type":
             "surface" if SURF_PATTERN.search(p.name) else "domain",
              "SHA256":sha(p),"point_lat_lon":None,
              "delta_lat_lon_degrees":None}
        try:
            import numpy as np
            from netCDF4 import Dataset
            with Dataset(str(p),"r") as ds:
                akey="LATIXY" if "LATIXY" in ds.variables else "lat"
                bkey="LONGXY" if "LONGXY" in ds.variables else "lon"
                if akey in ds.variables and bkey in ds.variables:
                    la=np.asarray(np.ma.asarray(ds.variables[akey][:]).filled(np.nan)).reshape(-1)
                    lo=np.asarray(np.ma.asarray(ds.variables[bkey][:]).filled(np.nan)).reshape(-1)
                    if len(la)==len(lo)==1 and np.isfinite(la[0]) and np.isfinite(lo[0]):
                        lat=float(la[0]);lon=(float(lo[0])+180)%360-180
                        info["point_lat_lon"]=[lat,lon]
                        if point is not None:
                            info["delta_lat_lon_degrees"]=[
                                round(abs(lat-point[0]),6),
                                round(abs(((lon-point[1])+180)%360-180),6)]
        except (ImportError,OSError,ValueError,RuntimeError) as exc:
            info["coordinate_read_status"]=type(exc).__name__+" "+str(exc)[:160]
        summary.append(info)
    return summary
def cime_cases(site):
    hits=[];considered=set()
    # Strictly one directory level in case roots; do not walk all of scratch.
    pat=re.compile(r"(?<![A-Za-z0-9])"+re.escape(site)+r"(?![A-Za-z0-9])")
    for root in CASE_BASES:
        if not root.is_dir() or root.is_symlink():continue
        try:
            for p in root.iterdir():
                if len(hits)>=MAX_CASES_PER_SITE:break
                if not p.is_dir() or p.is_symlink() or
                   not pat.search(p.name) or str(p) in considered:
                    continue
                considered.add(str(p))
                config=[]
                for d in (p/"CaseDocs",p):
                    if not d.is_dir() or d.is_symlink():continue
                    for name in ("lnd_in","atm_in","datm_in","drv_in",
                                 "env_run.xml","user_nl_clm",
                                 "user_nl_datm","user_nl_datm_streams"):
                        target=d/name
                        if not target.is_file() or target.is_symlink() or
                           target.stat().st_size>MAX_CONFIG_BYTES:
                            continue
                        text=target.read_text(encoding="utf-8",errors="replace")
                        matches=[v.strip()[:300] for v in text.splitlines()
                                 if RELEVANT_CONFIG.search(v)]
                        config.append({"path":str(target),
                                       "SHA256":sha(target),
                                       "relevant_lines":matches[:22]})
                hits.append({"case_path":str(p),
                             "case_config_evidence":config})
        except (PermissionError,OSError):continue
    return hits
def report(folder):
    receipt=j(folder/"SYVH9_SCIENCE_RECEIPT.json")
    ck(receipt.get("stage")=="SYVH9_INDEPENDENT_ERA5LAND_DEACCUMULATED_STRD" and
       receipt.get("independently_retrieved_source_hh")==12 and
       receipt.get("research_only") is True and
       receipt.get("model_ready") is False,
       "SYVH9 source science receipt changed")
    manifest=folder/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    ck(sha(manifest)==receipt["new_manifest_sha256"],
       "Final SYVH9 source manifest SHA mismatch")
    latest=tsv(manifest,("site","source_path","source_SHA256","latest_stage"))
    ck(len(latest)==10 and {x["site"] for x in latest}==set(SITE_NAMES),
       "Final operator ten-site source roster changed")
    stage5=j(S05)["sites"];stage8=j(S08)["sites"]
    ck(set(stage5)==THREE and
       set(stage8)==set(SITE_NAMES)-THREE,
       "Original Stage05/Stage08 source provenance split changed")
    allmeta=stage5|stage8
    status=[]
    print("SYVH11 SOURCE PIN PASS final manifest",sha(manifest))
    for row in sorted(latest,key=lambda x:x["site"]):
        site=row["site"]
        # Batch04 Gate-0 and Gate-1 fully checked these selected source SHAs.
        # Repeat exact full site SHA to prevent stale source path recency errors.
        ck(sha(Path(row["source_path"]))==row["source_SHA256"],
           "Research selected source SHA changed "+site)
        bif=site_bif(site,allmeta[site])
        # Actual earlier user-approved US-Seg coordinate, all other BIF sites
        # use precise original source coordinates from operator SYVH10.
        tower={
          "US-Rpf":(65.1198,-147.429),"US-SP1":(29.7381,-82.2188),
          "US-SRG":(31.7894,-110.8277),"US-SRM":(31.8214,-110.8661),
          "US-Seg":(34.3623,-106.7020),"US-Ses":(34.3349,-106.7442),
          "US-Slt":(39.9138,-74.596),"US-Syv":(46.242,-89.3477),
          "US-Ton":(38.4309,-120.966),"US-Uaf":(64.8663,-147.8555)
        }[site]
        surf=surfaces(site,tower)
        cases=cime_cases(site)
        datum={"site":site,
               "source_sha256":row["source_SHA256"],
               "original_BIF":bif,
               "surface_and_domain_candidates":surf,
               "nearby_existing_site_CIME_cases":cases,
               "surface_selection_approved":False,
               "domain_selection_approved":False,
               "ZBOT_verified":False,
               "DATM_time_centering_verified":False,
               "actual_case_stream_mappings_verified":False,
               "science_production_release":False}
        status.append(datum)
        print("SYVH11 SITE",site,
              "BIF_TA_HEIGHTS",bif["heights_by_variable"]["TA"],
              "BIF_WS_HEIGHTS",bif["heights_by_variable"]["WS"],
              "BIF_WIND_HEIGHTS",bif["heights_by_variable"]["WIND"],
              "CANOPY_HEIGHTS",sorted({x["height_m"] for x in
                                    bif["canopy_HEIGHTC_not_ZBOT"]}),
              "SURFACE_DOMAIN_FILES",len(surf),
              "CASE_CANDIDATES",len(cases),
              "MODEL_GATE","NOT_APPROVED")
        for c in surf[:10]:
            print("SURFACE/DOMAIN CANDIDATE",site,c["path"],c["SHA256"],
                  c["point_lat_lon"],c["delta_lat_lon_degrees"])
        for c in cases[:4]:
            print("EXISTING CASE CANDIDATE",site,c["case_path"],
                  "CONFIG_SOURCES",[v["path"] for v in
                                     c["case_config_evidence"]])
        if bif["sensor_metadata"]:
            print("BIF SENSOR-HEIGHT EVIDENCE",site,
                  bif["sensor_metadata"][:12])
    print("SYVH11 METADATA INVENTORY DONE. NO ZBOT/SURFACE/DOMAIN/STREAM HAS BEEN APPROVED.")
    return {"manifest_sha256":sha(manifest),
            "gate0_seven_met_all_sites_pass":True,
            "candidate_is_research_only":True,
            "site_results":status,
            "ZBOT_and_active_model_stream_authorized":False,
            "model_jobs_submitted":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-dir",default=str(FINAL))
    q=p.add_mutually_exclusive_group(required=True)
    q.add_argument("--self-test",action="store_true")
    q.add_argument("--check",action="store_true")
    q.add_argument("--report",action="store_true")
    a=p.parse_args()
    # Synthetic BIF: VAR_INFO_HEIGHT is a real measurement; HEIGHTC
    # does not count, and VAR_INFO_HEIGHT must be paired to variable name.
    toy=[{"VARIABLE_GROUP":"MET","GROUP_ID":"3","VARIABLE":"VAR_INFO_VARNAME","DATAVALUE":"TA_F"},
         {"VARIABLE_GROUP":"MET","GROUP_ID":"3","VARIABLE":"VAR_INFO_HEIGHT","DATAVALUE":"7.5"},
         {"VARIABLE_GROUP":"MET","GROUP_ID":"3","VARIABLE":"VAR_INFO_DATE","DATAVALUE":"20050101"},
         {"VARIABLE_GROUP":"LAND","GROUP_ID":"4","VARIABLE":"HEIGHTC","DATAVALUE":"24.2"}]
    hh,cc,mm=read_grouped_height_rows(toy,"TEST")
    ck(len(SITE_NAMES)==10 and
       len(hh)==1 and mm["TA"]==[7.5] and len(cc)==1 and
       len(FIVE)==5 and len(THREE)==3,
       "SYVH11 synthetic grouped BIF height inventory/self-test failed")
    print("SYVH11 SELF-TEST PASS exact 10 sites, grouped BIF TA/WS height sources, canopy separate, no writes")
    if a.self_test:return
    folder=Path(a.candidate_dir)
    ck(folder.is_dir() and not folder.is_symlink(),
       "Exact operator final SYVH9 candidate root missing")
    findings=report(folder)
    if a.report:
        home=Path.home()/"ameriflux_batch04_manual_review"
        home.mkdir(parents=True,exist_ok=True)
        name=("Batch04_SYVH11_existing_surface_CIME_ZBOT_BIF_"+
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
        dest=home/(name+".json");tableout=home/(name+".tsv")
        dest.write_text(json.dumps(findings,ensure_ascii=False,indent=2)+"\n")
        with tableout.open("x",encoding="utf-8",newline="") as f:
            w=csv.writer(f,delimiter="\t")
            w.writerow(["site","BIF_TA_heights","BIF_WS_heights",
                        "BIF_WIND_heights","source_canopy_heights",
                        "surface_domain_files","candidate_CIME_cases",
                        "ZBOT_authorized","science_released"])
            for d in findings["site_results"]:
                z=d["original_BIF"]["heights_by_variable"]
                canopy=sorted({c["height_m"] for c in
                    d["original_BIF"]["canopy_HEIGHTC_not_ZBOT"]})
                w.writerow([d["site"],",".join(map(str,z["TA"])),
                            ",".join(map(str,z["WS"])),
                            ",".join(map(str,z["WIND"])),
                            ",".join(map(str,canopy)),
                            len(d["surface_and_domain_candidates"]),
                            len(d["nearby_existing_site_CIME_cases"]),
                            False,False])
        print("SYVH11 REPORT",dest,"SHA256",sha(dest))
        print("SYVH11 SUMMARY TSV",tableout,"SHA256",sha(tableout))
    print("NO SOURCE/SURFACE/DOMAIN/CASE/DATM/CIME/SLURM WRITES")
if __name__=="__main__":main()

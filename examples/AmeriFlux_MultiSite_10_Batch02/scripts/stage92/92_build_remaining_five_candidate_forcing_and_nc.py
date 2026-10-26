#!/usr/bin/env python3
"""Batch02 Stage92: actually build five missing site-year forcing/NetCDF PREVIEWS.

No production DATM/CIME/Slurm writes. Reuse original SHA-pinned Stage07 QC-v5
logic with Stage92 fork adding SOURCE-PINNED 9389 Stage64 numeric humidity
candidates, 15199 Stage74 verified independent CDS humidity shadows, and
Stage85 operator APPROVED Ho1-2000 measured-QC0 temperatures / 1068 VPD.
Don't mistake a source shadow for a scientific approval. Those which cannot be
reconciled remain hard failure/HOLD. Successful site source CSVs, original-to-
candidate event ledgers, and NetCDF previews are made under isolated folder.
"""
import argparse,csv,hashlib,importlib.util,json,re,sys
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
STAGE64=ROOT/"reports/stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94"
STAGE74=ROOT/"reports/stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_20261025T090751Z_d0953fbc"
STAGE85=ROOT/"reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954"
STAGE91=ROOT/"reports/stage91_five_site_98year_source_integration_worklist_20261026T013148Z_f736ae1d"
FIVE={"US-EML":16,"US-GLE":16,"US-Ho1":28,"US-ICh":19,"US-ICt":19}
READY={"US-BZS","US-CMW","US-Ha1","US-Ho2","US-Ho3"}
N_HIST={"US-EML":1327,"US-GLE":295,"US-Ho1":937,"US-ICh":169,"US-ICt":2176}
F64="9389_original_tower_time_unified_CDS_ERA5_humidity_candidates.csv"
F74="16874_original_hard_independent_CDS_shadow_refreshed.csv"
F85="17568_Ho1_2000_tower_T_preserved_humidity_candidate.csv"
F91="98_missing_netcdf_year_source_worklist.csv"
STAGE74_NUMERIC="SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD"
EXT_ENGINE=Path(__file__).with_name("qcv5_stage92_integrate_external_RH_sources.py")
STAGE87_PIN="4f62ba03f52b41b98d7b6db3e89af2bf10bee8a1"
EXPECTED_QC0_2000=17294

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
    return h.hexdigest()

def gitblob(p):
    data=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()

def j(p):return json.loads(Path(p).read_text())
def csvrows(p):
    with Path(p).open(newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))
def stamp(s):
    digits=re.sub(r"[^0-9]","",str(s))
    if len(digits)<12:raise ValueError("Invalid native timestamp "+str(s))
    return digits[:12]
def number(v):
    try:
        x=float(v)
        if np.isfinite(x) and x>-9990:return x
    except (TypeError,ValueError):pass
    return float("nan")

def verify(folder,manifest,field,expected):
    if (folder/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Unfinished source ledger "+str(folder))
    d=j(folder/manifest)
    if expected not in d[field]:raise ValueError("Source receipt missing "+expected)
    for filename,digest in d[field].items():
        p=folder/filename
        if not p.is_file() or sha(p)!=digest:
            raise ValueError("Immutable original ledger SHA mismatch: "+str(p))
    return d

def library():
    old=j(STAGE07/"exact_input_manifest.json")
    if old.get("algorithm")!="HISTORICAL_QCV5_NATIVE_HH_HR_ADAPTATION":
        raise ValueError("Original Stage07 algorithm changed")
    if not (STAGE07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Original Stage07 preserved incomplete scope changed")
    specs={x["site"]:x for x in old["sites"]}
    if set(specs)!=set(FIVE)|READY:raise ValueError("Historical source site selection changed")
    receipt=old["input_sha256"]
    pinned={str(Path(p).resolve()):dig for p,dig in receipt.items()}
    for site in FIVE:
        r=specs[site]
        for field in ("primary","era"):
            p=str(Path(r[field]).resolve())
            if p not in pinned:raise ValueError("Missing historical source pin "+p)
            print("STAGE92 ORIGINAL SHA CHECK",site,field,flush=True)
            if sha(p)!=pinned[p]:raise ValueError("Source product modified "+p)
        if r["native_minutes"]!=30:
            raise ValueError("Stage92 five original blocked sites all expected HH "+site)
        if int(r["last_year"])-int(r["first_year"])+1!=FIVE[site]:
            raise ValueError("Site year span mismatch "+site)
    m64=verify(STAGE64,"unified_source_provenance_and_hold_manifest.json","output_sha256",F64)
    m74=verify(STAGE74,"stage74_source_science_manifest.json","outputs_sha256",F74)
    m85=verify(STAGE85,"stage85_source_decision_manifest.json","outputs_SHA256",F85)
    m91=j(STAGE91/"manifest.json")
    if (m91.get("missing_NC_year_count")!=98 or
        m91.get("already_built_NC_technical_years")!=117 or
        sha(STAGE91/F91)!=m91["out_sha256"][F91]):
        raise ValueError("Stage91 actual operator approved integration worklist missing")
    if (m64.get("approved_for_DATM") is not False or
        m74.get("approved_for_DATM") is not False or
        m85.get("active_forcing_or_DATM_approved") is not False):
        raise ValueError("A source shadow's scientific approval status changed unexpectedly")
    if m85.get("original_measured_T_QC0_preserved_count")!=EXPECTED_QC0_2000 or m85.get("VPD_modified_humidity_only_count")!=1068:
        raise ValueError("Stage85 manual Ho1 temperature/humidity source changed")
    r64=csvrows(STAGE64/F64)
    r74=csvrows(STAGE74/F74)
    r85=csvrows(STAGE85/F85)
    if len(r64)!=9389 or len(r74)!=16874 or len(r85)!=17568:
        raise ValueError("Stage64/74/85 exact source population drift")
    shadow=Counter(x["science_status"] for x in r74)
    if shadow[STAGE74_NUMERIC]!=15199:raise ValueError("Stage74 independent numerical source census drift")
    replacements=defaultdict(dict)
    origin=Counter()
    for row in r64:
        site=row["site"]; time=stamp(row["tower_local_start"])
        if site not in FIVE:continue
        rh=number(row["replacement_RH_water_pct"])
        t=number(row["original_TA_C_kept"])
        p=number(row["original_PA_kPa_kept"])
        if not (0.01<=rh<=100 and -80<t<65 and 50<p<110):
            raise ValueError("Stage64 numerical source claimed physical but is invalid "+site+" "+time)
        if time in replacements[site]:raise ValueError("Stage64 original duplicated")
        replacements[site][time]=(rh,"STAGE64_INDEPENDENT_ERA5_WATER_RH",t,p,"STAGE64_PHYSICAL_CANDIDATE")
        origin["Stage64"]+=1
    for row in r74:
        site=row["site"];time=stamp(row["tower_local_start"])
        if site not in FIVE:continue
        if row["science_status"]!=STAGE74_NUMERIC:
            origin["Stage74_TEMP_SCIENCE_HOLD_SKIP"]+=1
            continue
        rh=number(row["CDS_ERA5_RH_water_pct"])
        t=number(row["TA_C"])
        p=number(row["PA_kPa"])
        if not (0.01<=rh<=100 and -80<t<65 and 50<p<110):
            raise ValueError("Stage74 physical RH shadow bounds violated "+site+" "+time)
        if time in replacements[site]:raise ValueError("Stage64/74 source timestamp overlap; reconcile before build")
        replacements[site][time]=(rh,"STAGE74_CDS_INDEPENDENT_WATER_RH",t,p,row["science_status"])
        origin["Stage74"]+=1

    ho1={}
    for row in r85:
        time=stamp(row["tower_local_start"])
        if time[:4]!="2000" or time in ho1:raise ValueError("Stage85 exact year/time duplicate")
        ho1[time]=row
    if len(ho1)!=17568:raise ValueError("Stage85 source time census differs")
    q0=[r for r in r85 if number(r.get("native_TA_F_original_QC"))==0]
    if len(q0)!=EXPECTED_QC0_2000:
        raise ValueError("Stage85 original measured-source T approvals changed")
    print("STAGE92 SOURCE LEDGERS VERIFIED 9389/16874/17568; scoped external numerical",
          dict(origin),"site source sizes",{site:len(val) for site,val in replacements.items()},flush=True)
    return specs,replacements,ho1,old

def load_module(path,name):
    m=importlib.util.spec_from_file_location(name,path)
    if not m or not m.loader:raise ValueError("Cannot load source "+str(path))
    mod=importlib.util.module_from_spec(m)
    m.loader.exec_module(mod)
    return mod

def build(specs,replacements,ho1,old,netcdf_path,no_nc=False):
    if not EXT_ENGINE.is_file():raise ValueError("Missing GitHub Stage92 engine placed beside driver")
    engine=load_module(EXT_ENGINE,"stage92_external_engine")
    if engine.INTERPOLATE!={"TA_F":4,"VPD_F":4,"PA_F":4,
      "SW_IN_F":2,"LW_IN_F":4,"WS_F":4,"P_F":0}:
        raise ValueError("Original QCv5 interpolation/science policy changed")
    net=None
    if not no_nc:
        if not netcdf_path.is_file() or gitblob(netcdf_path)!=STAGE87_PIN:
            raise ValueError("Stage87 pinned NetCDF builder source missing/hash altered")
        net=load_module(netcdf_path,"stage87_verified_nc_builder")
    helperpath=[Path(k) for k in old["input_sha256"] if Path(k).name=="07_build_batch02_qcv5_candidates.py"]
    if len(helperpath)!=1:
        raise ValueError("Original Stage07 source audit helper absent in pinned manifest")
    helperpath=helperpath[0]
    if sha(helperpath)!=old["input_sha256"][str(helperpath)]:
        raise ValueError("Stage07 original independent source audit helper SHA changed")
    helper=load_module(helperpath,"stage92_pinned_independent_checker")
    engine.SITE_YEARS={s:(int(r["first_year"]),int(r["last_year"])) for s,r in specs.items() if s in FIVE}
    def exact(raw,pattern):
        site=raw.parent.parent.name
        if site not in FIVE:raise ValueError("Not in five-site Stage92 source cohort "+site)
        if pattern=="*FLUXMET_HH*.csv":return Path(specs[site]["primary"])
        if pattern=="*ERA5_HH*.csv":return Path(specs[site]["era"])
        raise ValueError("Unapproved companion source "+pattern)
    engine.get_one=exact
    engine.STAGE92_SCOPED={site:{"rh":replacements[site],
        "ho1_2000":ho1 if site=="US-Ho1" else {}}
        for site in FIVE}

    out=ROOT/"reports"/("stage92_five_site_complete_forcing_candidates_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"
    marker.write_text("SCIENTIFIC SHADOW ONLY. Do not activate DATM; complete site Post-v5 and source-clock reviews.\\n")
    results=[]
    summaries=[]
    for site,n_years in FIVE.items():
        info=specs[site]
        print("\\n=== STAGE92 ACTUAL BUILD",site,"YEARS",n_years,"===",flush=True)
        status={"site":site,"num_years":n_years,"native_minutes":info["native_minutes"],
                "forcing_done":False,"netcdf_done":False,"status":"FAIL","error":""}
        try:
            engine.parse_site(site,Path(info["primary"]).parents[4],out,
                native_minutes=info["native_minutes"],standalone_era=True)
            evidence=helper.independent_audit(info,out)
            if evidence["status"]!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
                raise ValueError("Stage92 independent source scientific review marker missing")
            status.update({"forcing_done":True,
                           "forcing_csv":evidence["forcing_csv"],
                           "numeric_audit":evidence,
                           "status":"NUMERIC_CANDIDATE_REVIEW_REQUIRED"})
            print("STAGE92 COMPLETE FORCE CSV + INDEPENDENT AUDIT PASS",site,
                 "rows",evidence["noleap_rows"],"original_QC0_edits",
                 evidence["changed_QC0_records"],flush=True)
            if net is not None:
                entry={"site":site,"first_year":info["first_year"],
                    "last_year":info["last_year"],"step":info["native_minutes"],
                    "source":Path(evidence["forcing_csv"]),
                    "sha256":sha(evidence["forcing_csv"])}
                surf,surf_sha,lat,lon=net.point_surface(site)
                dest=out/site/"technical_nc_years"
                dest.mkdir(parents=True,exist_ok=False)
                files=[]
                for year,data in net.site_years(entry):
                    target=dest/(str(year)+".nc")
                    net.save_nc(target,entry,year,data,lat,lon,surf_sha)
                    with net.nc.Dataset(target) as d:
                        if len(d.dimensions["time"])!=365*1440//int(entry["step"]):
                            raise ValueError("Stage92 annual NetCDF time count invalid")
                        if d.variables["time"].calendar!="noleap" or any(
                            k not in d.variables for k in net.NC_FIELDS):
                            raise ValueError("Stage92 annual NetCDF data fields invalid")
                    files.append({"year":year,"path":str(target),"sha256":sha(target)})
                if len(files)!=n_years:raise ValueError("Stage92 annual NC count mismatch")
                template=net.make_template(dest,site,range(int(info["first_year"]),int(info["last_year"])+1))
                status.update({"netcdf_done":True,"netcdf_years":len(files),
                    "netcdf_year_files":files,"stream_template_not_activated":str(template),
                    "surface_source_sha256":surf_sha})
                print("STAGE92 TECHNICAL NETCDF BUILT",site,n_years,"years, TEMPLATE NOT ACTIVATED",flush=True)
        except Exception as exc:
            status["error"]=str(exc)
            status["status"]="FAIL"
            print("STAGE92 SITE HOLD/FAIL",site,str(exc),flush=True)
        results.append(status)
        (out/"site_build_summary.json").write_text(json.dumps(results,indent=2,default=str)+"\\n")
    print("\\nSTAGE92 ORIGINAL SOURCE SHA RECHECK",flush=True)
    changed=[k for k,digest in old["input_sha256"].items() if sha(Path(k))!=digest]
    if changed:raise ValueError("Original Stage07 sources changed during stage92 build: "+str(changed))
    complete=sum(x["forcing_done"] for x in results)
    built=sum(int(x.get("netcdf_years",0)) for x in results)
    manifest={"schema":"STAGE92_FIVE_SITE_NUMERIC_CANDIDATES_NOT_DATM_SCIENCE_RELEASE",
        "requested_five_sites":5,"complete_forcing_sites":complete,
        "missing_annual_netcdf_requested":98,
        "annual_netcdf_preview_built":built,
        "original_source_modified":False,"active_DATM_modified":False,
        "CIME_Slurm_model_changed":False,"postv5_scheduled":False,
        "scientific_release":False,
        "original_stage07_manifest_sha256":sha(STAGE07/"exact_input_manifest.json"),
        "stage64_manifest_sha256":sha(STAGE64/"unified_source_provenance_and_hold_manifest.json"),
        "stage74_manifest_sha256":sha(STAGE74/"stage74_source_science_manifest.json"),
        "stage85_manifest_sha256":sha(STAGE85/"stage85_source_decision_manifest.json"),
        "stage91_manifest_sha256":sha(STAGE91/"manifest.json"),
        "engine_sha256":sha(EXT_ENGINE),
        "original_source_SHA_unchanged":not changed,"sites":results}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,default=str)+"\\n")
    if complete==5 and (no_nc or built==98):
        marker.unlink()
        print("STAGE92 FIVE SITE CANDIDATE PASS | five original-source audited forcing CSV; NC preview years",built)
    else:
        print("STAGE92 FIVE SITE PARTIAL/FAIL | numeric sites",complete,"/5; annual NC",built,"/98; INCOMPLETE marker retained")
    print("REPORT",out)
    print("NO ORIGINAL DATA/ACTIVE DATM/CIME/SLURM CHANGES; SCIENTIFIC STATUS REVIEW ONLY")
    return 0 if complete==5 and (no_nc or built==98) else 2

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--build",action="store_true")
    parser.add_argument("--netcdf-module",type=Path,default=Path(__file__).with_name(
         "87_build_five_verified_Stage07_DATM_noleap_technical_preview.py"))
    parser.add_argument("--forcing-only",action="store_true",
        help="Build only forcing first, without 98 technical NetCDF files")
    args=parser.parse_args()
    if args.self_test:
        assert sum(FIVE.values())==98
        assert len(READY)==5 and sum(N_HIST.values())==4904
        assert stamp("2000-12-27T09:30:00")=="200012270930"
        assert np.isclose(number("75.0"),75.0)
        assert np.isnan(number("-9999"))
        assert EXT_ENGINE.name=="qcv5_stage92_integrate_external_RH_sources.py"
        print("STAGE92 SELF-TEST PASS | five blocked, 98 NC, source-provenance guarded; no writes")
        return
    if args.forcing_only and not args.build:
        parser.error("--forcing-only requires --build")
    specs,replacements,ho1,old=library()
    print("STAGE92 PREFLIGHT VERIFIED | five original raw source pairs + 3 SHA ledgers + Stage91 98-year list")
    if args.check:
        print("STAGE92 CHECK PASS | no candidate/source/NetCDF writes")
        return
    return build(specs,replacements,ho1,old,args.netcdf_module,args.forcing_only)

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stage96: audited READ-ONLY Batch02 ten-site DATM/CIME evidence preflight.

Reads the real Stage95 complete 215 annual versioned NC files and provenance,
the original FLUXNET release CSV clock fields and BIF VAR_INFO_HEIGHT,
and the actual Stage03 subset point surfaces. No time phase guessed from
longitude; no ZBOT invented; no substitution of FATES PFT using CLM natural
PFT. Produces per-site scientific/technical HOLD and evidence inventory.
No modifications to any forcing, NetCDF, model case, streams, or Slurm.
"""
import argparse,csv,hashlib,json,math
from collections import defaultdict,Counter
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4

import numpy as np
import netCDF4 as nc
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S95=ROOT/"reports/stage95_ten_site_122_user_approved_versioned_forcing_215NC_20261026T034516Z_f4afa348"
SITESROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
STAGE07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
YEARS={"US-BZS":15,"US-CMW":21,"US-EML":16,"US-GLE":16,
       "US-Ha1":35,"US-Ho1":28,"US-Ho2":27,"US-Ho3":19,
       "US-ICh":19,"US-ICt":19}
REQUIRED=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms")
LANDUNITS=("PCT_NATVEG","PCT_CROP","PCT_LAKE","PCT_WETLAND","PCT_GLACIER","PCT_URBAN")
QC0={"US-BZS":1,"US-CMW":2,"US-EML":3,"US-GLE":0,"US-Ha1":2,
     "US-Ho1":5,"US-Ho2":19,"US-Ho3":0,"US-ICh":0,"US-ICt":90}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
    return h.hexdigest()
def j(p):return json.loads(Path(p).read_text())
def vals(v):return np.asarray(np.ma.filled(v[:],np.nan),dtype=float).ravel()
def fl(v):
    try:
        x=float(v)
        if math.isfinite(x):return x
    except (TypeError,ValueError):pass
    return float("nan")
def writecsv(p,rows,cols):
    with Path(p).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def verify_versioned_manifest():
    m=j(S95/"manifest.json")
    if (m.get("schema")!="STAGE95_BATCH02_VERSIONED_122_ORIGINAL_QC0_APPROVED_10SITE_215_NC_v1"
        or m.get("site_pass")!=10
        or m.get("annual_netcdf_generated_and_readback_verified")!=215
        or m.get("source_forcing_sha256_unchanged") is not True
        or m.get("production_DATM_approved") is not False
        or m.get("Slurm_jobs_submitted") is not False
        or not (S95/"SCIENCE_HOLD_DO_NOT_ACTIVATE_DATM_OR_SUBMIT").is_file()
        or (S95/"INCOMPLETE_DO_NOT_USE").exists()):
        raise ValueError("Stage95 completed-but-science-HOLD source contract changed")
    original=j(STAGE07/"exact_input_manifest.json")
    specs={r["site"]:r for r in original["sites"]}
    sites={r["site"]:r for r in m["sites"]}
    if set(sites)!=set(YEARS) or set(specs)!=set(YEARS):
        raise ValueError("Stage95 ten-site IDs/source pair roster differs")
    return m,specs,sites

def read_bif_heights(site,site_root):
    """Read official BIF GROUP_ID/VARIABLE blocks, no interpretation of unknown units."""
    paths=sorted((site_root/"forcing/raw").rglob("*BIF*.csv"))
    histories={"TA_F":defaultdict(set),"WS_F":defaultdict(set)}
    parsed=0
    errors=[]
    for p in paths:
        with p.open("r",encoding="utf-8-sig",errors="replace",newline="") as stream:
            reader=csv.DictReader(stream)
            if not reader.fieldnames or not {"VARIABLE","DATAVALUE","GROUP_ID"}.issubset(reader.fieldnames):
                continue
            parsed+=1
            groups=defaultdict(dict)
            for row in reader:
                k=(str(row.get("VARIABLE_GROUP","")),str(row.get("GROUP_ID","")))
                var=str(row.get("VARIABLE","")).strip().upper()
                if var:groups[k][var]=str(row.get("DATAVALUE","")).strip()
            for block in groups.values():
                variable=block.get("VAR_INFO_VARNAME","").upper()
                if variable not in histories:continue
                try:
                    dt=pd.to_datetime(block["VAR_INFO_DATE"],format="%Y%m%d%H%M",errors="raise")
                    height=fl(block["VAR_INFO_HEIGHT"])
                    if not 0.5<=height<=150:
                        raise ValueError("ZBOT must be plausible 0.5..150m")
                    histories[variable][str(dt)].add(float(height))
                except (KeyError,TypeError,ValueError) as exc:
                    errors.append(f"{variable}:invalid_BIF_height_or_date:{type(exc).__name__}")
    result={}
    for variable,dated in histories.items():
        conflicts={t:sorted(v) for t,v in dated.items() if len(v)!=1}
        hist=sorted((t,next(iter(v))) for t,v in dated.items() if len(v)==1)
        result[variable]={"entries":len(hist),"history":hist[:100],
                           "conflict_count":len(conflicts),
                           "conflicts":conflicts}
        if not hist:errors.append(variable+":MISSING_EXACT_BIF_HEIGHT_HISTORY")
        if conflicts:errors.append(variable+":CONFLICTING_BIF_HEIGHT_HISTORY")
    return {"bif_csv_file_count":len(paths),"valid_bif_csv_count":parsed,
            "height_histories":result,"warnings":errors}

def surface_evidence(site):
    roots=list((SITESROOT/site/"subset_data_batch02_surf2000").glob("surfdata*.nc"))
    if len(roots)!=1:raise ValueError("Requires exactly one Batch02 point surface "+site)
    p=roots[0]
    with nc.Dataset(p) as d:
        land={}
        for name in LANDUNITS:
            if name in d.variables:
                v=vals(d[name])
                if not np.isfinite(v).all():raise ValueError(site+" invalid surface "+name)
                land[name]=float(v.sum()) if name=="PCT_URBAN" else float(v[0])
            elif name in ("PCT_NATVEG","PCT_CROP"):
                raise ValueError(site+" required landunit absent "+name)
        raw_pft=vals(d["PCT_NAT_PFT"]) if "PCT_NAT_PFT" in d.variables else np.array([])
        if len(raw_pft)==0 or not np.isfinite(raw_pft).all():
            raise ValueError("Missing/invalid original natural PFT composition "+site)
        if not 99.0<=float(raw_pft.sum())<=101.0:
            raise ValueError("Natural PFT composition does not sum to ~100% "+site)
        if not 99.0<=sum(land.values())<=101.0:
            raise ValueError("Landunits do not sum to ~100% "+site)
        xy={}
        for name in ("LATIXY","LONGXY"):
            if name not in d.variables:raise ValueError(site+" original surface coordinate absent "+name)
            vec=vals(d[name])
            if len(vec)!=1 or not np.isfinite(vec[0]):
                raise ValueError(site+" original surface is not a point")
            xy[name]=float(vec[0])
    return {"path":str(p),"sha256":sha(p),"landunits_pct":land,
            "clm_natural_pft_values_pct":raw_pft.tolist(),
            "clm_natural_pft_sum_pct":float(raw_pft.sum()),
            "coordinate":xy}

def source_clock_evidence(site,spec):
    path=Path(spec["primary"])
    raw=pd.read_csv(path,nrows=0)
    cols=set(raw.columns)
    if "TIMESTAMP_START" not in cols:
        raise ValueError("Original FLUXNET time start column missing "+site)
    use=["TIMESTAMP_START"]
    if "TIMESTAMP_END" in cols:use.append("TIMESTAMP_END")
    first=pd.read_csv(path,usecols=use,nrows=3,dtype=str)
    # The original release may use TIMESTAMP_START local labels with an
    # independently unknown UTC alignment; numeric suffix means start label
    # only. End timestamps establish source interval direction but not UTC.
    step=int(spec["native_minutes"])
    example=[]
    for row in first.to_dict("records"):
        start=str(row["TIMESTAMP_START"]).strip().removesuffix(".0")
        finish=str(row.get("TIMESTAMP_END","")).strip().removesuffix(".0")
        record={"source_start":start,"source_end":finish}
        if finish:
            try:
                a=datetime.strptime(start,"%Y%m%d%H%M")
                b=datetime.strptime(finish,"%Y%m%d%H%M")
                record["end_minus_start_min"]=(b-a).total_seconds()/60
                if record["end_minus_start_min"]!=step:
                    raise ValueError("Original native source start/end interval mismatched "+site)
            except ValueError as ex:
                raise ValueError("Original source paired timestamp parse failed "+site) from ex
        example.append(record)
    return {"source_primary":str(path),"source_primary_sha256":sha(path),
            "native_minutes":step,"original_timestamp_columns":use,
            "source_examples":example,
            "original_FLUXNET_local_to_UTC_offset_verified":False,
            "DATM_interval_start_vs_center_semantics_approved":False,
            "no_clock_offset_inferred_from_longitude":True}

def nc_evidence(site,report):
    products=report["NC_technical_preview_files"]
    if len(products)!=YEARS[site]:raise ValueError("Stage95 NC coverage changed "+site)
    variables=set()
    startlabel=set()
    years=set()
    ntimes=set()
    zbot_flags=set()
    missing_units=set()
    coords=set()
    for row in products:
        yr=int(row["year"])
        p=Path(row["path"])
        if not p.is_file() or sha(p)!=row["sha256"]:
            raise ValueError("Stage95 actual versioned NC checksum failed "+str(p))
        years.add(yr)
        with nc.Dataset(p) as d:
            if d.getncattr("science_approval")!="FALSE_TECHNICAL_PREVIEW_ONLY":
                raise ValueError("A preview NC was mislabeled production science-approved "+site)
            if getattr(d,"production_DATM_release","")!="NO_Ho1_nonQC0_2000_and_clock_ZBOT_pending":
                raise ValueError("Original Stage95 scientific HOLD metadata missing "+site)
            if not set(REQUIRED).issubset(d.variables):
                raise ValueError("Missing canonical forcing variable "+site)
            variables|=set(d.variables)
            t=d.variables["time"]
            if t.calendar!="noleap" or t.units!=f"days since {yr}-01-01 00:00:00":
                raise ValueError("Wrong NOLEAP calendar/units "+site)
            n=len(d.dimensions["time"])
            expected=365*1440//(60 if site=="US-Ha1" else 30)
            if n!=expected:raise ValueError("Wrong native NC time dimension "+site)
            clock=np.asarray(t[:],dtype=float)
            if not np.allclose(clock,np.arange(n,dtype=float)*(60 if site=="US-Ha1" else 30)/1440,
                               atol=1e-8,rtol=0):
                raise ValueError("Original local-label time coordinate changed "+site)
            if any(getattr(d.variables[v],"units","")=="" for v in REQUIRED):
                missing_units.add(str(yr))
            xy=(float(vals(d.variables["LATIXY"])[0]),float(vals(d.variables["LONGXY"])[0]))
            coords.add(xy)
            zbot_flags.add("PRESENT" if "ZBOT" in d.variables else "ABSENT")
            startlabel.add(getattr(t,"long_name",""))
            ntimes.add(n)
    if len(years)!=YEARS[site] or len(coords)!=1:raise ValueError("NC yearly coverage/spatial coordinates drift "+site)
    return {"annual_nc_years":len(years),"year_start":min(years),"year_end":max(years),
            "native_records_per_year":sorted(ntimes),
            "ZBOT_variable_states":sorted(zbot_flags),
            "time_long_name_values":sorted(startlabel),
            "source_geo":dict(lat=next(iter(coords))[0],lon=next(iter(coords))[1]),
            "missing_unit_years":sorted(missing_units),
            "canonical_variables_present":sorted(variables & set(REQUIRED))}

def audit():
    m,specs,sites=verify_versioned_manifest()
    rows=[];details={}
    for site in sorted(YEARS):
        source=specs[site]
        out=sites[site]
        problems=[]
        try:
            surf=surface_evidence(site)
            ncs=nc_evidence(site,out)
            orig=source_clock_evidence(site,source)
            bif=read_bif_heights(site,SITESROOT/site)
            pft_crop=surf["landunits_pct"].get("PCT_CROP",0)
            if pft_crop>15:
                problems.append("CROP_GT15_PERCENT_REQUIRES_FOOTPRINT_PFT_REVIEW")
            if "ABSENT" in ncs["ZBOT_variable_states"]:
                problems.append("ZBOT_MISSING_FROM_NEW_PREVIEW_NC")
            if bif["warnings"]:
                problems+=bif["warnings"]
            for v in ("TA_F","WS_F"):
                if bif["height_histories"][v]["entries"]>0:
                    first=datetime.strptime(bif["height_histories"][v]["history"][0][0],"%Y-%m-%d %H:%M:%S")
                    start=datetime(int(source["first_year"]),1,1)
                    if first>start:problems.append(v+"_BIF_HEIGHT_REQUIRES_PREHISTORY_DECISION")
            if ncs["missing_unit_years"]:
                problems.append("CANONICAL_NC_UNITS_MISSING")
            if (abs(surf["coordinate"]["LATIXY"]-ncs["source_geo"]["lat"])>1e-5 or
                abs(surf["coordinate"]["LONGXY"]-ncs["source_geo"]["lon"])>1e-5):
                problems.append("SURFACE_AND_NC_COORDINATE_MISMATCH")
            # This must be demonstrated using the source metadata + actual
            # active CIME DATM/CDEPS forcing convention; not inferred.
            problems.append("CLOCK_UTC_OFFSET_AND_INTERVAL_PHASE_NOT_YET_VERIFIED")
            problems.append("FATES_PFT_AND_SITE_FOOTPRINT_NOT_SCIENCE_APPROVED")
            problems.append("CIME_DATM_CDEPS_FORMAT_SMOKE_TEST_PENDING")
            if site=="US-Ho1":
                problems.append("HO1_QC1_QC2_2000_DEC27_18P746C_T_SOURCE_SCIENCE_HOLD")
            detail={"site":site,"source_clock":orig,"bif":bif,
                    "surface":surf,"new_nc":ncs,"blocking_science_and_technical":problems}
            status="READONLY_INPUT_STRUCTURAL_PASS_REVIEW_REQUIRED"
        except Exception as err:
            status="INPUT_TECHNICAL_FAIL"
            detail={"site":site,"error":str(err)}
            problems.append("TECHNICAL_FAIL_"+type(err).__name__)
        details[site]=detail
        rows.append({"site":site,"annual_nc":YEARS[site],
          "input_status":status,
          "operator_approved_QC0_variable_changes":QC0[site],
          "surface_crop_pct":round(detail.get("surface",{}).get("landunits_pct",{}).get("PCT_CROP",float("nan")),4),
          "BIF_TA_height_entries":detail.get("bif",{}).get("height_histories",{}).get("TA_F",{}).get("entries",0),
          "BIF_WS_height_entries":detail.get("bif",{}).get("height_histories",{}).get("WS_F",{}).get("entries",0),
          "DATM_clock_UTC_verified":"NO",
          "ZBOT_approved":"NO",
          "PFT_site_footprint_approved":"NO",
          "production_DATM_permitted":"NO",
          "issues":"|".join(problems)})
        print("STAGE96",site,status,
              "NC",YEARS[site],"TAheight",rows[-1]["BIF_TA_height_entries"],
              "WSheight",rows[-1]["BIF_WS_height_entries"],
              "CROP",rows[-1]["surface_crop_pct"],
              "ISSUES",";".join(problems),flush=True)
    return m,rows,details

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    for flag in ("self-test","check","audit"):
        mode.add_argument("--"+flag,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert sum(YEARS.values())==215 and sum(QC0.values())==122
        assert len(YEARS)==10 and "US-Ho1" in YEARS
        assert (datetime.strptime("202001010030","%Y%m%d%H%M")-
                datetime.strptime("202001010000","%Y%m%d%H%M"))==timedelta(minutes=30)
        print("STAGE96 SELF-TEST PASS | all 10 sites 215 NC; no science invent/production write",flush=True)
        return 0
    manifest,rows,details=audit()
    ntech=sum(x["input_status"]=="INPUT_TECHNICAL_FAIL" for x in rows)
    if a.check:
        print("STAGE96 CHECK FINISHED | technical failures",ntech,
              "10 sites checked; science clock, ZBOT, PFT and Ho1 hold NOT waived",flush=True)
        return 2 if ntech else 0
    path=ROOT/"reports"/("stage96_batch02_DATM_clock_ZBOT_surface_readonly_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    path.mkdir(parents=True,exist_ok=False)
    cols=list(rows[0])
    writecsv(path/"10_site_readiness_gates.csv",rows,cols)
    (path/"original_source_BIF_surface_NC_evidence.json").write_text(
        json.dumps(details,indent=2,default=str)+chr(10))
    m96={"schema":"STAGE96_BATCH02_DATM_CIME_METADATA_PREFLIGHT_READONLY",
         "stage95_manifest_sha256":sha(S95/"manifest.json"),
         "sites_audited":len(rows),
         "annual_NC_source_total":sum(x["annual_nc"] for x in rows),
         "numeric_source_QC0_operator_approved":sum(QC0.values()),
         "structural_failed_sites":ntech,
         "no_model_run_or_case_submission":True,
         "ho1_source_science_hold_waived":False,
         "time_phase_ZBOT_PFT_production_approval":False,
         "outputs_sha256":{k:sha(path/k) for k in (
            "10_site_readiness_gates.csv",
            "original_source_BIF_surface_NC_evidence.json")}}
    (path/"manifest.json").write_text(json.dumps(m96,indent=2)+chr(10))
    print("STAGE96 REPORT",path,flush=True)
    print("STAGE96 RESULT |",len(rows),"/10 sites; 215 NC; structural_fail",
          ntech,"; SCIENCE HOLD applies to DATM clock/ZBOT/PFT; Ho1 additional QC1/QC2 HOLD",flush=True)
    print("NO SOURCE/FORCING/NC/CASE/CIME/SLURM MODIFICATIONS",flush=True)
    return 2 if ntech else 0

if __name__=="__main__":
    raise SystemExit(main())

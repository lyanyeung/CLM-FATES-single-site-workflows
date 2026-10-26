#!/usr/bin/env python3
"""Stage101: GLE solar time-phase and real GF-Guy CIME source READ-ONLY forensic.

Validate immutable Stage99 16 NC and Stage100 actual 8-field CIME mapping.
Compare source-local START FSDS solar geometry against source-label-as-UTC
versus original site BIF UTC_OFFSET=-7 and START/MIDPOINT/END placement.
Read historical GF-Guy CaseDocs as source evidence. No CIME/NC/Slurm writes;
physical daylight consistency is NOT an automatic DATM timestamp approval.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import netCDF4 as nc

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S99=ROOT/"reports/stage99_GLE_23p4m_source_ZBOT_16yr_TECHNICAL_ONLY_20261026T043117Z_c311a7a5"
S100=ROOT/"reports/stage100_GLE_CIME_field_and_clock_preview_READONLY_20261026T111919Z_715b01ee"
REF=Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases/GF-Guy_FATES_SURF2000_CO2405_1PT")
SAMPLE_YEARS=(2005,2010,2015,2020)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())

def verify():
    a=load(S100/"manifest.json");b=load(S99/"manifest.json")
    if (a.get("schema")!="STAGE100_GLE_EIGHT_CIME_FIELDS_16_NC_READONLY_PREVIEW_v1"
        or a.get("annual_NC_verified")!=16 or a.get("CIME_variables_verified")!=8
        or a.get("stage99_manifest_sha256")!=sha(S99/"manifest.json")
        or a.get("QBOT_to_Sa_shum_verified_from_prior_workflow") is not True
        or a.get("field_mappings",{}).get("ZBOT")!="Sa_z"
        or a.get("actual_case_stream_accepted") is not False
        or a.get("run_clock_UTC_and_phase_approved") is not False
        or a.get("Slurm_jobs_submitted") is not False
        or b.get("new_NC_years")!=16
        or b.get("production_DATM_approved") is not False
        or not (S99/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").exists()):
        raise ValueError("Stage99/100 exact source/CIME contract changed")
    for f,h in a["report_sha256"].items():
        if sha(S100/f)!=h:raise ValueError("Stage100 evidence receipt altered "+f)
    files=load(S99/"16_year_GLE_NC_manifest.json")
    if len(files)!=16 or {int(x["year"]) for x in files}!=set(range(2005,2021)):
        raise ValueError("Stage99 16 GLE years changed")
    return {int(x["year"]):x for x in files}

def coszen(doy,localhour,lat,lon,hours_ahead):
    utc_abs=(np.asarray(doy,dtype=float)-1)*24+np.asarray(localhour,dtype=float)+hours_ahead
    index=np.floor(utc_abs/24)
    hour=utc_abs-24*index
    day=np.mod(index,365)+1
    g=2*np.pi/365*(day-1+(hour-12)/24)
    eq=229.18*(0.000075+0.001868*np.cos(g)-0.032077*np.sin(g)
                -0.014615*np.cos(2*g)-0.040849*np.sin(2*g))
    dec=(0.006918-0.399912*np.cos(g)+0.070257*np.sin(g)
         -0.006758*np.cos(2*g)+0.000907*np.sin(2*g)
         -0.002697*np.cos(3*g)+0.00148*np.sin(3*g))
    hourangle=np.deg2rad(np.mod(hour*60+eq+4*lon,1440)/4-180)
    latitude=np.deg2rad(lat)
    return np.sin(latitude)*np.sin(dec)+np.cos(latitude)*np.cos(dec)*np.cos(hourangle)

def get_samples(files):
    sampled=[];sitecoords=set();source=[]
    for year in SAMPLE_YEARS:
        row=files[year];p=Path(row["with_ZBOT"])
        if not p.is_file() or sha(p)!=row["sha256"]:
            raise ValueError("Original GLE yearly NC SHA changed "+str(p))
        with nc.Dataset(p) as d:
            if (d.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY"
                or d.stage99_clock_offset_correction!="NONE_SOURCE_LOCAL_START_LABEL_UNCHANGED"
                or float(d.air_temperature_sensor_BIF_height_m)!=23.4
                or float(d.wind_sensor_BIF_height_m)!=22.65):
                raise ValueError("GLE original clock/ZBOT state changed")
            if d.variables["time"].calendar!="noleap" or len(d.dimensions["time"])!=17520:
                raise ValueError("GLE annual time dimension changed")
            t=np.asarray(d.variables["time"][:],dtype=float)
            if not np.allclose(t,np.arange(17520)/48,rtol=0,atol=1e-8):
                raise ValueError("GLE native 30min local-start time changed")
            sw=np.ma.filled(d.variables["FSDS"][:],np.nan).astype(float).ravel()
            if not np.isfinite(sw).all() or np.min(sw)<0:
                raise ValueError("GLE original FSDS invalid")
            lat=float(d.variables["LATIXY"][0,0]);lon=float(d.variables["LONGXY"][0,0])
            sitecoords.add((lat,lon))
            sampled.append((np.floor(t).astype(int)+1,(t-np.floor(t))*24,sw))
            source.append({"year":year,"path":str(p),"sha256":row["sha256"]})
    if len(sitecoords)!=1:raise ValueError("GLE source coordinates inconsistent")
    return next(iter(sitecoords)),sampled,source

def solar_comparison(coordinates,samples):
    lat,lon=coordinates;results=[]
    hypotheses=(("SOURCE_LABEL_ASSUMED_UTC",0),
                ("LST_TO_UTC_START",7.0),
                ("LST_TO_UTC_MIDPOINT",7.25),
                ("LST_TO_UTC_END",7.5))
    for name,hours in hypotheses:
        nday=0;nbad=0;dark_energy=0.;total_energy=0.;n=0
        for doy,localhr,fsds in samples:
            solar=coszen(doy,localhr,lat,lon,hours)
            dark=solar<-0.052336  # Sun below -3 degrees; conservative.
            bright=fsds>50
            nday+=int(np.count_nonzero(bright))
            nbad+=int(np.count_nonzero(bright&dark))
            dark_energy+=float(np.maximum(fsds[dark],0).sum())
            total_energy+=float(fsds.sum())
            n+=len(fsds)
        results.append({"hypothesis":name,"hours_ahead_of_original_local_START":hours,
                        "tested_years":"2005;2010;2015;2020",
                        "source_samples":n,"FSDS_gt50_samples":nday,
                        "FSDS_gt50_when_sun_below_minus3_degrees":nbad,
                        "false_night_bright_fraction":nbad/max(nday,1),
                        "shortwave_energy_at_solar_dark_fraction":dark_energy/max(total_energy,1),
                        "production_approved":"NO"})
    return results

def read_original_case():
    out={"reference_case":str(REF),"present":REF.is_dir(),"xmlquery_executed":False,
         "CaseDocs":{}}
    regex=re.compile(r"DATM|CDEPS|time|year_align|year_first|year_last|taxmode|tintalgo|QBOT|SHUM|ZBOT|Sa_z|offset|run_startdate|FSDS",re.I)
    for name in ("CaseStatus","user_nl_datm_streams","CaseDocs/atm_in",
                 "CaseDocs/datm_in","CaseDocs/lnd_in","env_run.xml","env_case.xml"):
        p=REF/name
        if not p.is_file():
            out["CaseDocs"][name]={"exists":False};continue
        lines=p.read_text(errors="replace").splitlines()
        out["CaseDocs"][name]={"exists":True,"sha256":sha(p),
            "relevant_lines":[{"line":i+1,"snippet":s[:200]} for i,s in enumerate(lines)
                              if regex.search(s)][:50]}
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    q=ap.add_mutually_exclusive_group(required=True)
    for key in ("self-test","check","audit"):q.add_argument("--"+key,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        noon=coszen(np.array([172]),np.array([12.]),40,-105,7.25)[0]
        incorrect=coszen(np.array([172]),np.array([12.]),40,-105,0)[0]
        assert noon>0.9 and noon>incorrect+0.4
        print("STAGE101 SELF-TEST PASS | solar longitude vs local standard time +7h clock geometry; no writes")
        return 0
    files=verify();coordinates,samples,proof=get_samples(files)
    scores=solar_comparison(coordinates,samples)
    case=read_original_case()
    for x in scores:
        print("STAGE101 SOLAR",x["hypothesis"],"NIGHT_BRIGHT",
              x["FSDS_gt50_when_sun_below_minus3_degrees"],"/",
              x["FSDS_gt50_samples"],"FRACTION",
              "%.6f"%x["false_night_bright_fraction"],"DARK_SW_ENERGY",
              "%.6f"%x["shortwave_energy_at_solar_dark_fraction"],flush=True)
    best=min(scores,key=lambda x:x["false_night_bright_fraction"])
    print("STAGE101 BEST_DAYLIGHT_CONSISTENCY_DIAGNOSTIC",best["hypothesis"],
          "| NEVER AUTO_APPROVE_CLOCK_PHASE",flush=True)
    print("STAGE101 CASEDOCS_FOUND",
          ",".join(x for x,v in case["CaseDocs"].items() if v["exists"]),flush=True)
    print("STAGE101 SOURCE CLOCK HOLD | BIF offset -7, source LOCAL interval START, model CIME UTC/phase not signed off",flush=True)
    if a.check:
        print("STAGE101 CHECK PASS | actual GLE solar/CDM source evidence, NO SOURCE/CASE WRITES",flush=True)
        return 0
    out=ROOT/"reports"/("stage101_GLE_DATM_solar_clock_phase_readonly_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    with (out/"solar_F​​SDS_clock_four_hypotheses.csv".replace("\u200b","")).open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
    (out/"GF_Guy_CIME_CaseDocs_original_readonly.json").write_text(json.dumps(case,indent=2)+"\n")
    (out/"GLE_yearly_NC_SHA_used_for_clock_test.json").write_text(json.dumps(proof,indent=2)+"\n")
    holds=[
      ("TIME_LST_UTC","Official -7 source start → UTC candidate +7 hours; verify CIME and interval midpoint; year-wrap required"),
      ("WIND_TA_ZBOT","23.4m air versus 22.65m wind; single Sa_z model reference needs decision"),
      ("PFT_FOOTPRINT","US-GLE actual tower PFT/footprint versus CTSM original gridded surface not signed off"),
      ("CIME_CASE","Only GF-Guy historical CaseDocs read; no user GLE case/setup/submit attempted")]
    with (out/"GLE_science_and_CIME_action_gates.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.writer(f);w.writerow(("issue","status","detail"))
        w.writerows((k,"HOLD",v) for k,v in holds)
    manifest={"schema":"STAGE101_GLE_SOLAR_CLOCK_ORIGINAL_CIME_READONLY",
         "stage100_manifest_sha256":sha(S100/"manifest.json"),
         "sampled_years":list(SAMPLE_YEARS),"source_lat":coordinates[0],"source_lon":coordinates[1],
         "most_solar_consistent_DIAGNOSTIC_only":best["hypothesis"],
         "CIME_source_time_shift_approved":False,"interval_phase_approved":False,
         "case_modified":False,"netCDF_modified":False,"Slurm_submitted":False,
         "science_HOLD":True,
         "output_sha256":{f.name:sha(f) for f in out.iterdir() if f.is_file()}}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("STAGE101 REPORT",out,flush=True)
    print("STAGE101 PASS | four solar clock diagnostics and historical CIME CaseDocs read-only; NO NC/CIME/SLURM CHANGES",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

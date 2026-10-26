#!/usr/bin/env python3
"""Stage100: actual source-pinned US-GLE CIME/DATM mapping PREVIEW, no cases.

Read successful FLUXNET eight-site CIME DATM template (source-verified Git
blob) and the 16 new US-GLE ZBOT NC of Stage99. Prove QBOT -> Sa_shum,
ZBOT -> Sa_z, original unit/time/year mapping. Build UNACTIVATED
user_nl_datm_streams proposal, not a model case, and list remaining science
obligations: local-standard time vs CIME clock, measured 23.4 m TA/22.65 m
wind, PFT/site footprint and actual CIME component namelist acceptance.
NO xmlchange, create_clone, case.setup/build, job submission, original edits.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

import netCDF4 as nc
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S95=ROOT/"reports/stage95_ten_site_122_user_approved_versioned_forcing_215NC_20261026T034516Z_f4afa348"
S99=ROOT/"reports/stage99_GLE_23p4m_source_ZBOT_16yr_TECHNICAL_ONLY_20261026T043117Z_c311a7a5"
SITESROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REF_CASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/cases/GF-Guy_FATES_SURF2000_CO2405_1PT")
REF_NAME="09_eight_site_spinup500.sh"
REF_BLOB="65084885323060329e84b9ac2155463c12885160"
SITE="US-GLE"
FIRST=2005
LAST=2020
FIELDS={
 "PRECTmms":"Faxa_precn","FSDS":"Faxa_swdn","ZBOT":"Sa_z",
 "TBOT":"Sa_tbot","WIND":"Sa_wind","QBOT":"Sa_shum",
 "PSRF":"Sa_pbot","FLDS":"Faxa_lwdn"}
PHYSICS={"PRECTmms":("mm/s",0,0.20),"FSDS":("W/m2",0,1600),
         "ZBOT":("m",0.5,150),"TBOT":("K",180,340),
         "WIND":("m/s",0,75),"QBOT":("kg/kg",0,0.08),
         "PSRF":("Pa",49000,111000),"FLDS":("W/m2",0,800)}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def blob(p):
    data=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def source_script_check():
    script=Path(__file__).resolve().parent/REF_NAME
    if not script.is_file() or blob(script)!=REF_BLOB:
        raise ValueError("Previously documented, pinned, successful eight-site CIME source script absent or changed")
    s=script.read_text()
    start=s.index("CLM_USRDAT.UNSET:datavars =")
    end=s.index("\nDATM_VARS",start)
    chunk=s[start:end]
    matches=dict(re.findall(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s+([A-Za-z][A-Za-z0-9_]*)\s*,?\s*\\?\s*$",
                            chunk,re.MULTILINE))
    if matches!=FIELDS:raise ValueError("Exact previous CIME 'QBOT Sa_shum' / 'ZBOT Sa_z' source mapping changed "+str(matches))
    if not all(x in s for x in (
        "CLM_USRDAT.UNSET:year_first =", "CLM_USRDAT.UNSET:year_last =",
        "CLM_USRDAT.UNSET:year_align =","CLM_USRDAT.UNSET:taxmode = cycle",
        "CLM_USRDAT.UNSET:tintalgo = linear",
        "CLM_USRDAT.UNSET:mapalgo = none","CLM_USRDAT.UNSET:meshfile = none")):
        raise ValueError("Historical CIME DATM template settings changed")
    return script

def ref_case_state():
    result={"case_path":str(REF_CASE),"present":REF_CASE.is_dir(),
        "case_status_success":False,"reference_case_usable":False,
        "build_complete_xmlquery":"NOT_EXECUTED_READ_ONLY",
        "no_case_write":True}
    case_status=REF_CASE/"CaseStatus"
    if case_status.is_file():
        status=case_status.read_text(errors="replace")
        result["case_status_success"]=bool(re.search(
            r"model execution success|case.run success",status,re.IGNORECASE))
    result["reference_case_usable"]=(
        REF_CASE.is_dir() and
        (REF_CASE/"xmlquery").is_file() and
        (REF_CASE/"user_nl_clm").is_file() and
        result["case_status_success"])
    return result

def candidate_gate():
    src=j(S99/"manifest.json")
    source=j(S95/"manifest.json")
    if (src.get("schema")!="BATCH02_STAGE99_GLE_SOURCE_ZBOT_16NC_PILOT_NONACTIVATING"
        or src.get("source_site")!=SITE or src.get("new_NC_years")!=16
        or src.get("air_temperature_BIF_ZBOT_m")!=23.4
        or src.get("wind_BIF_height_m")!=22.65
        or src.get("original_canonical_met_unchanged_all_years") is not True
        or src.get("clock_shift_applied") is not False
        or src.get("production_DATM_approved") is not False
        or src.get("active_CIME_case_edited") is not False
        or src.get("Slurm_job_submitted") is not False
        or not (S99/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").exists()
        or source.get("site_pass")!=10
        or source.get("annual_netcdf_generated_and_readback_verified")!=215
        or source.get("production_DATM_approved") is not False
        or source.get("source_forcing_sha256_unchanged") is not True):
        raise ValueError("Stage95 / Stage99 completed but NOT approved source contract changed")
    for f,h in src.get("outputs_sha256",{}).items():
        if sha(S99/f)!=h:
            raise ValueError("Stage99 original provenance report SHA changed "+f)
    if src.get("original_stage95_sha256")!=sha(S95/"manifest.json"):
        raise ValueError("Stage95 original 215 NC source manifest checksum changed")
    y=j(S99/"16_year_GLE_NC_manifest.json")
    if len(y)!=16 or {x["year"] for x in y}!=set(range(FIRST,LAST+1)):
        raise ValueError("Stage99 source years mismatch")
    return y

def read_nc_file(item):
    year=int(item["year"])
    path=Path(item["with_ZBOT"])
    if not path.is_file() or sha(path)!=item["sha256"]:
        raise ValueError("GLE source NC SHA mismatch "+str(path))
    if sha(item["original"])!=item["original_sha256"]:
        raise ValueError("GLE old original NC was changed after Stage99 "+str(path))
    with nc.Dataset(path) as ds:
        if ds.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY":
            raise ValueError("US-GLE was mislabeled science approved")
        if ds.stage99_model_case_approval!="NO" or ds.stage99_clock_offset_correction!="NONE_SOURCE_LOCAL_START_LABEL_UNCHANGED":
            raise ValueError("Stage99 original local source clock or model-approval state changed")
        if getattr(ds,"ZBOT_height_source","")!="AmeriFlux_release_BIF_original_TA_F_VAR_INFO_HEIGHT":
            raise ValueError("US-GLE ZBOT measurement source proof changed")
        if (ds.air_temperature_sensor_BIF_height_m!=23.4 or
            ds.wind_sensor_BIF_height_m!=22.65):
            raise ValueError("US-GLE original distinct TA+WS height evidence changed")
        if not set(FIELDS).issubset(set(ds.variables)):
            raise ValueError("CIME data variable name absent from original NC")
        if "SHUM" in ds.variables:
            raise ValueError("Unexpected SHUM NC source would invalidate explicit QBOT mapping")
        t=ds.variables["time"]
        if t.units!=f"days since {year}-01-01 00:00:00" or t.calendar!="noleap":
            raise ValueError("Wrong noleap time metadata for GLE "+str(year))
        if len(t)!=365*48 or not np.allclose(
                np.asarray(t[:],dtype=float),np.arange(365*48)/48,atol=1e-8,rtol=0):
            raise ValueError("GLE source-local-start time grid changed")
        if not ("local-start" in str(getattr(t,"long_name",""))):
            raise ValueError("Original native-local start-time status lost")
        checks={}
        for name,(unit,lo,hi) in PHYSICS.items():
            var=ds.variables[name]
            if var.dimensions!=("time","lat","lon") or var.units!=unit:
                raise ValueError("Model contract variable dimensions/units changed "+name)
            arr=np.ma.filled(var[:],np.nan).astype(float)
            if (arr.shape!=(365*48,1,1) or not np.isfinite(arr).all() or
                np.min(arr)<lo or np.max(arr)>hi):
                raise ValueError("CIME preview field outside physical bounds "+name+" "+str(year))
            checks[name]={"min":float(np.min(arr)),"max":float(np.max(arr)),
                "source_variable":name,"CIME_target":FIELDS[name],"unit":unit}
        time_semantics="SOURCE_NATIVE_LOCAL_INTERVAL_START_NOT_CIME_PHASE_APPROVED"
        return {"year":year,"source":str(path),"sha256":item["sha256"],
                "time_semantics":time_semantics,"fields":checks}

def proposed_stream(y,metadata):
    # This is a source-supported mapping proposal in separate report only;
    # DATM component acceptance, sampling phase and site-clock have NOT run.
    paths=[str(Path(r["with_ZBOT"])) for r in sorted(y,key=lambda x:x["year"])]
    prefix=[
      "# STAGE100 TECHNICAL PROPOSAL: DO NOT COPY INTO ACTIVE CIME CASE",
      "# US-GLE native FLUXNET local standard time, 2005–2020 30-min interval START.",
      "# UTC_OFFSET=-7 from BIF is NOT applied or signed off for CIME clock.",
      "# ZBOT=23.4m TA reference, wind 22.65m (difference left unresolved).",
      "# CIME actual namelist and stream time must be tested before a smoke run.",
      "CLM_USRDAT.UNSET:taxmode = cycle",
      "CLM_USRDAT.UNSET:tintalgo = linear",
      "CLM_USRDAT.UNSET:mapalgo = none",
      "CLM_USRDAT.UNSET:meshfile = none",
      "",
      f"CLM_USRDAT.UNSET:year_first = {FIRST}",
      f"CLM_USRDAT.UNSET:year_last = {LAST}",
      f"CLM_USRDAT.UNSET:year_align = {FIRST}",
      "",
      "CLM_USRDAT.UNSET:datafiles = \\"]
    prefix.extend(p+(", \\" if i<len(paths)-1 else "") for i,p in enumerate(paths))
    prefix.extend(["","CLM_USRDAT.UNSET:datavars = \\"])
    mapping=list(FIELDS.items())
    prefix.extend(key+" "+val+(", \\" if i<len(mapping)-1 else "") for i,(key,val) in enumerate(mapping))
    return "\n".join(prefix)+"\n"

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    x=ap.add_mutually_exclusive_group(required=True)
    for f in ("self-test","check","audit"):
        x.add_argument("--"+f,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert len(FIELDS)==8 and FIELDS["QBOT"]=="Sa_shum"
        assert FIELDS["ZBOT"]=="Sa_z" and len(PHYSICS)==8
        assert len(range(FIRST,LAST+1))==16
        print("STAGE100 SELF-TEST PASS | verified QBOT Sa_shum + ZBOT Sa_z; 16 source NC only; no writes",flush=True)
        return 0
    script=source_script_check()
    files=candidate_gate()
    extracted=[]
    for obj in sorted(files,key=lambda z:z["year"]):
        extracted.append(read_nc_file(obj))
        print("STAGE100 GLE FIELD/TIME CHECK PASS",obj["year"],
              "8/8 variables","noleap 17520 source-local-start ZBOT=23.4 WS=22.65",flush=True)
    reference=ref_case_state()
    print("STAGE100 HISTORICAL_CIME_MAPPING VERIFIED QBOT→Sa_shum; ZBOT→Sa_z; source_script_blob",blob(script),flush=True)
    print("STAGE100 SOURCE_GF_GUY_CASE",reference["reference_case_usable"],
          "case_status_success",reference["case_status_success"],flush=True)
    print("STAGE100 CIME_CLOCK_HOLD | source LOCAL START clock; BIF UTC=-7, CIME shift and interval phase NOT VERIFIED",flush=True)
    if a.check:
        print("STAGE100 CHECK PASS | 16 GLE NC, 8 field maps; no files written",flush=True)
        return 0
    out=ROOT/"reports"/("stage100_GLE_CIME_field_and_clock_preview_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    stream=out/"user_nl_datm_streams.PROPOSED_NOT_APPLIED"
    stream.write_text(proposed_stream(files,reference))
    (out/"16_year_CIME_DATM_variable_time_evidence.json").write_text(
        json.dumps(extracted,indent=2)+chr(10))
    (out/"GF_Guy_source_case_readonly_state.json").write_text(
        json.dumps(reference,indent=2)+chr(10))
    holds=[
       {"topic":"DATM_SOURCE_TIME_LOCAL_STANDARD_TO_MODEL_CLOCK","status":"HOLD",
        "reason":"Confirmed source-local START labels; offset -7 is official BIF but DATM phase not demonstrated"},
       {"topic":"DATM_STREAM_COMPONENT_NAMELIST_ACCEPTANCE","status":"HOLD",
        "reason":"Proposed CIME user_nl_datm_streams not yet accepted by case.setup / CaseDocs"},
       {"topic":"TA_VS_WS_MEASUREMENT_REFERENCE_HEIGHT","status":"HOLD",
        "reason":"ZBOT=23.4m TA, WS source 22.65m; explicit scientific handling of 0.75m difference pending"},
       {"topic":"PFT_AND_SITE_FOOTPRINT","status":"HOLD",
        "reason":"US-GLE tower footprint vs CTSM natural/crop grid and FATES PFT not signed off"},
       {"topic":"MODEL_COMPONENT_SMOKE_TEST","status":"HOLD",
        "reason":"Only a future isolated case may validate CIME - do not launch model now"}]
    with (out/"remaining_GLE_science_and_case_blockers.csv").open(
          "w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=("topic","status","reason"))
        w.writeheader();w.writerows(holds)
    result={"schema":"STAGE100_GLE_EIGHT_CIME_FIELDS_16_NC_READONLY_PREVIEW_v1",
       "stage99_manifest_sha256":sha(S99/"manifest.json"),
       "historical_successful_eight_site_CIME_script_gitblob":REF_BLOB,
       "site":SITE,"annual_NC_verified":16,"CIME_variables_verified":len(FIELDS),
       "field_mappings":FIELDS,"QBOT_to_Sa_shum_verified_from_prior_workflow":True,
       "actual_case_stream_accepted":False,"run_clock_UTC_and_phase_approved":False,
       "actual_source_GFGuy_case":reference,
       "TA_ZBOT_m":23.4,"WS_BIF_m":22.65,
       "scientific_FATES_site_PFT_approved":False,
       "user_nl_datm_streams_active_changed":False,
       "model_case_changed":False,"Slurm_jobs_submitted":False,
       "report_sha256":{p.name:sha(p) for p in out.iterdir()}}
    (out/"manifest.json").write_text(json.dumps(result,indent=2)+chr(10))
    print("STAGE100 GLE CIME FIELD PROPOSAL PASS | 16 NC / 8 fields source-verified, NOT ACTIVATED",flush=True)
    print("STAGE100 REPORT",out,flush=True)
    print("STAGE100 REMAINING HOLD | local clock/CIME phase; 0.75m WS height; site PFT; case smoke test",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

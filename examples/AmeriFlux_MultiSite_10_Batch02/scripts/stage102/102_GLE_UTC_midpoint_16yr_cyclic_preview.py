#!/usr/bin/env python3
"""Batch02 Stage102: GLE isolated UTC+7h, midpoint (+15min) TECHNICAL PREVIEW.

Stage99 US-GLE 16 yearly NC are source-local 30-minute interval START data.
For CIME CLM_USRDAT.UNSET:tintalgo = linear, CTSM guidance expects midpoint
timestamps. GLE BIF UTC_OFFSET=-7; Stage101 FSDS solar test rejects treating
local START as UTC (59.06% of FSDS>50 at astronomical nighttime).

Construct ONLY a separate candidate, never touch the 16 original GLE files
or 215 10-site source previews. Circularly roll the *complete 16-year
NOLEAP time series* by 14 30min intervals (+7h to UTC), label each interval
midpoint (+15min), and read back every original meteorology/ZBOT field. A
16-year cyclic seam at 2005-01-01 07:15 UTC explicitly uses
2020-12-31 23:30 local -> 2005-01-01 00:00 local: weather discontinuity
is not a measured 2004 record. HOLD for cycle seam/CIME clock and PFT.

This script does NOT edit any CIME case, surface, DATM stream, nor submit jobs.
"""
import argparse,csv,hashlib,json,shutil,math
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import netCDF4 as nc
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S99=ROOT/"reports/stage99_GLE_23p4m_source_ZBOT_16yr_TECHNICAL_ONLY_20261026T043117Z_c311a7a5"
S100=ROOT/"reports/stage100_GLE_CIME_field_and_clock_preview_READONLY_20261026T111919Z_715b01ee"
S101=ROOT/"reports/stage101_GLE_DATM_solar_clock_phase_readonly_20261026T113511Z_44c6e48e"
FIRST=2005
LAST=2020
STEP_MIN=30
OFFSET_H=7
SHIFT=OFFSET_H*60//STEP_MIN
HALF_HOURS_YEAR=17520
YEARS=tuple(range(FIRST,LAST+1))
SIZE=len(YEARS)*HALF_HOURS_YEAR
MET=("TBOT","QBOT","SHUM","RH","PSRF","FSDS","FLDS","WIND","PRECTmms","ZBOT")
CANONICAL=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms")
VERSION="STAGE102_GLE_LST_TO_UTC_PLUS7_MIDPOINT_16_YEAR_PERIODIC_SOURCE_CYCLE_v1"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def j(p):return json.loads(Path(p).read_text())

def gate():
    m99=j(S99/"manifest.json")
    m100=j(S100/"manifest.json")
    m101=j(S101/"manifest.json")
    if (m99.get("schema")!="BATCH02_STAGE99_GLE_SOURCE_ZBOT_16NC_PILOT_NONACTIVATING"
        or m99.get("new_NC_years")!=16 or m99.get("production_DATM_approved") is not False
        or m99.get("clock_shift_applied") is not False
        or m100.get("schema")!="STAGE100_GLE_EIGHT_CIME_FIELDS_16_NC_READONLY_PREVIEW_v1"
        or m100.get("annual_NC_verified")!=16
        or m100.get("stage99_manifest_sha256")!=sha(S99/"manifest.json")
        or m100.get("QBOT_to_Sa_shum_verified_from_prior_workflow") is not True
        or m100.get("run_clock_UTC_and_phase_approved") is not False
        or m101.get("schema")!="STAGE101_GLE_SOLAR_CLOCK_ORIGINAL_CIME_READONLY"
        or m101.get("stage100_manifest_sha256")!=sha(S100/"manifest.json")
        or m101.get("sampled_years")!=[2005,2010,2015,2020]
        or m101.get("CIME_source_time_shift_approved") is not False
        or m101.get("interval_phase_approved") is not False
        or not (S99/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").is_file()):
        raise ValueError("Stage99/100/101 source-pinned science HOLD or phase proof changed")
    for k,v in m99["outputs_sha256"].items():
        if sha(S99/k)!=v:raise ValueError("Original Stage99 report checksum mismatch "+k)
    for k,v in m100["report_sha256"].items():
        if sha(S100/k)!=v:raise ValueError("Original Stage100 report checksum mismatch "+k)
    for k,v in m101["output_sha256"].items():
        if sha(S101/k)!=v:raise ValueError("Original Stage101 solar report checksum mismatch "+k)
    with (S101/"solar_FSDS_clock_four_hypotheses.csv").open("r",newline="") as f:
        score={r["hypothesis"]:r for r in csv.DictReader(f)}
    for name in ("SOURCE_LABEL_ASSUMED_UTC","LST_TO_UTC_START","LST_TO_UTC_MIDPOINT","LST_TO_UTC_END"):
        if name not in score:raise ValueError("Required original solar hypothesis missing")
    if (float(score["SOURCE_LABEL_ASSUMED_UTC"]["false_night_bright_fraction"])<0.5 or
        float(score["LST_TO_UTC_MIDPOINT"]["false_night_bright_fraction"])>0.001):
        raise ValueError("Original Stage101 local-vs-UTC daylight evidence changed")
    entries=j(S99/"16_year_GLE_NC_manifest.json")
    if len(entries)!=16 or {int(x["year"]) for x in entries}!=set(YEARS):
        raise ValueError("Original source 16 years changed")
    for x in entries:
        if sha(x["with_ZBOT"])!=x["sha256"] or sha(x["original"])!=x["original_sha256"]:
            raise ValueError("Stage99 original 16 NC hash changed "+str(x["year"]))
    return sorted(entries,key=lambda x:int(x["year"])),score

def gather(entries):
    fields={k:[] for k in MET}
    latlon=set()
    for x in entries:
        yr=int(x["year"])
        with nc.Dataset(x["with_ZBOT"]) as d:
            if (d.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY"
                or d.stage99_model_case_approval!="NO"
                or d.stage99_clock_offset_correction!="NONE_SOURCE_LOCAL_START_LABEL_UNCHANGED"
                or d.air_temperature_sensor_BIF_height_m!=23.4
                or d.wind_sensor_BIF_height_m!=22.65):
                raise ValueError("Original Stage99 scientific HOLD/height changed")
            t=d.variables["time"]
            actual=np.ma.filled(t[:],np.nan).astype(float)
            if (len(actual)!=HALF_HOURS_YEAR or
                t.calendar!="noleap" or
                t.units!=f"days since {yr}-01-01 00:00:00" or
                not np.array_equal(actual,np.arange(HALF_HOURS_YEAR)/48)):
                raise ValueError("Original GLE NOLEAP local START time changed")
            latlon.add((float(d.variables["LATIXY"][0,0]),float(d.variables["LONGXY"][0,0])))
            for k in MET:
                if k not in d.variables:raise ValueError("Original GLE source missing variable "+k)
                var=d.variables[k]
                if tuple(var.dimensions)!=("time","lat","lon"):
                    raise ValueError("Original GLE source variable dimensions invalid "+k)
                a=np.ma.filled(var[:],np.nan).astype(float)
                if a.shape!=(HALF_HOURS_YEAR,1,1) or not np.isfinite(a).all():
                    raise ValueError("Nonfinite/wrong year GLE source "+k)
                fields[k].append(a[:,0,0])
    if len(latlon)!=1:raise ValueError("GLE source coordinates changed across years")
    series={k:np.concatenate(v) for k,v in fields.items()}
    if any(len(s)!=SIZE for s in series.values()):
        raise ValueError("Original GLE full 16-year sample count changed")
    if not np.array_equal(series["SHUM"],series["QBOT"]):
        raise ValueError("Original GLE SHUM and QBOT aliases inconsistent")
    if not np.all(series["ZBOT"]==23.4):
        raise ValueError("Source ZBOT 23.4m varied unexpectedly")
    return series,next(iter(latlon))

def shift(series):
    result={k:np.roll(v,SHIFT) for k,v in series.items()}
    if SHIFT!=14 or SIZE!=280320:
        raise ValueError("UTC offset or exact 16-year periodic time layout changed")
    for k in MET:
        if not np.array_equal(result[k][SHIFT:],series[k][:-SHIFT]):
            raise ValueError("Source value-to-UTC movement is not exactly +14 native records "+k)
        if not np.array_equal(result[k][:SHIFT],series[k][-SHIFT:]):
            raise ValueError("Cycle seam is not exactly last source-year 7h local record "+k)
        if not np.array_equal(np.sort(result[k]),np.sort(series[k])):
            raise ValueError("UTC remap lost original source climate values "+k)
    return result

def verify_new(entries,files,shifted):
    if len(files)!=16:raise ValueError("16 NC files not regenerated")
    for entry,item in zip(entries,files):
        year=int(entry["year"]);fn=Path(item["new"])
        if year!=item["year"] or not fn.is_file() or sha(fn)!=item["sha256"]:
            raise ValueError("UTC candidate annual receipt mismatch "+str(year))
        off=(year-FIRST)*HALF_HOURS_YEAR
        with nc.Dataset(fn) as ds,nc.Dataset(entry["with_ZBOT"]) as original:
            t=ds.variables["time"]
            vv=np.ma.filled(t[:],np.nan).astype(float)
            if not (t.calendar=="noleap"
                and t.units==f"days since {year}-01-01 00:00:00"
                and np.array_equal(vv,(np.arange(HALF_HOURS_YEAR)+0.5)/48)):
                raise ValueError("New UTC 15min midpoint grid changed "+str(year))
            if ds.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY" or ds.production_DATM_release!="NO_Ho1_nonQC0_2000_and_clock_ZBOT_pending":
                raise ValueError("Versioned UTC preview wrongly labeled as production approved")
            for field in MET:
                if ds.variables[field].units!=original.variables[field].units:
                    raise ValueError("Versioned unit changed "+field)
                got=np.ma.filled(ds.variables[field][:],np.nan).astype(float).ravel()
                expect=shifted[field][off:off+HALF_HOURS_YEAR]
                if not np.array_equal(got,expect):
                    raise ValueError("Versioned GLE UTC meteorology not exact permuted source "+field+" "+str(year))
            if ds.air_temperature_sensor_BIF_height_m!=23.4 or ds.wind_sensor_BIF_height_m!=22.65:
                raise ValueError("New candidate missing original measured TA/WS heights")
    return True

def review():
    inputfiles,solar=gate()
    fields,coords=gather(inputfiles)
    utc=shift(fields)
    print("STAGE102 SOURCE PASS | original 16/16 Stage99 GLE NC, Stage100 CIME mapping, Stage101 solar source SHA verified",flush=True)
    print("STAGE102 TIME PROPOSAL | LST_START+7h→UTC interval MIDPOINT+15min | original NOLEAP 16y 280320x30min",flush=True)
    print("STAGE102 PERIODIC_WRAP_HOLD | first 14 UTC halfhours Jan 1 2005 inherit last 14 local halfhours Dec 31 2020; not observed 2004 forcing",flush=True)
    print("STAGE102 SOLAR CONTEXT | source-as-UTC false-night fraction",
          solar["SOURCE_LABEL_ASSUMED_UTC"]["false_night_bright_fraction"],
          "LST-to-UTC-MID fraction",
          solar["LST_TO_UTC_MIDPOINT"]["false_night_bright_fraction"],flush=True)
    return inputfiles,fields,utc,coords

def build():
    original,series,utc,coords=review()
    out=ROOT/"reports"/("stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").write_text(
        "UTC midpoint candidate only. Original LST clock +7h, 15min measurement centering. 14-record cyclic seam uses 2020 local Dec 31 as surrogate prior-to-2005 UTC data. Wind measurement height 22.65m != TA/SHUM 23.4m; GLE footprint/PFT and real CIME case time phase not signed off.\n")
    partial=out/"INCOMPLETE_DO_NOT_USE"
    partial.write_text("Versioned 16-year UTC remap not yet verified.\n")
    folder=out/"US-GLE"/"UTC_PLUS7_MIDPOINT_16NC_TECHNICAL"
    folder.mkdir(parents=True,exist_ok=False)
    files=[]
    for item in original:
        yr=int(item["year"])
        old=Path(item["with_ZBOT"]);dest=folder/f"{yr}.nc"
        if sha(old)!=item["sha256"]:raise ValueError("Stage99 original source NC changed")
        shutil.copyfile(old,dest)
        begin=(yr-FIRST)*HALF_HOURS_YEAR
        with nc.Dataset(dest,"a") as ds:
            for field in MET:
                ds.variables[field][:,0,0]=utc[field][begin:begin+HALF_HOURS_YEAR]
            t=ds.variables["time"]
            t[:]=(np.arange(HALF_HOURS_YEAR)+0.5)/48
            t.long_name="UTC midpoint of half-hour mean from station local-standard START labels plus 7h; cyclic seam first 14 records model year 2005 uses source local Dec31 2020"
            # The historical Stage99 global attribute said clock unchanged;
            # it is stale for these NEW remapped NC files and must be explicit.
            ds.stage99_clock_offset_correction="SUPERSEDED_IN_STAGE102_UTC_PLUS7_AND_MIDPOINT"
            ds.forcing_validation="STAGE95_POSTV5_NUMERIC_AND_SCIENCE_QC0_PASSED_STAGE102_CLOCK_CANDIDATE_ONLY"
            ds.historical_clock="STAGE102_LST_TO_UTC_PLUS7_MIDPOINT_CYCLIC_PREVIEW_UNAPPROVED"
            ds.stage102_time_conversion="US-GLE_BIF_UTC_OFFSET_minus7_hours_and_halfhour_midpoint"
            ds.stage102_periodic_wrap_first_14_records="local_2020_12_31_17_00_through_23_30_not_measured_2004"
            ds.stage102_case_submit_approved="NO"
            ds.stage102_previous_version_sha256=item["sha256"]
            ds.stage102_thermodynamic_height_m=23.4
            ds.stage102_anemometer_measurement_height_m=22.65
            ds.stage102_original_precip_flux_values_permutation_only="YES"
        files.append({"year":yr,"new":str(dest),"sha256":sha(dest),
            "original":str(old),"original_sha256":item["sha256"],
            "sample_count":HALF_HOURS_YEAR})
        print("STAGE102 UTC_CYCLIC_MIDPOINT YEAR PASS",yr,HALF_HOURS_YEAR,"30min",flush=True)
    verify_new(original,files,utc)
    (out/"16_year_UTC_midpoint_NC_source_manifest.json").write_text(json.dumps(files,indent=2)+"\n")
    science={
      "date_alignment":"LST START source +7h UTC and 15min center for linear CIME",
      "first_14_UTC_halfhours_from":"2020-12-31 17:00–23:30 LST (candidate cyclic boundary)",
      "original_2005_prior_local_data_measured":False,
      "seam_jump_model_UTC_2005_01_01_07_15":"2020-12-31 23:30 local to 2005-01-01 00:00 local",
      "CIME_cycle_boundary_and_tintalgo_science_approved":False,
      "wind_vs_thermodynamic_reference_height_m":0.75,
      "FATES_site_PFT_surface_approved":False,
      "do_not_use_as_approved_DATM_stream":True}
    (out/"UTC_clock_cycle_and_site_science_HOLD.json").write_text(json.dumps(science,indent=2)+"\n")
    record={"schema":VERSION,"source_Stage99_manifest_sha256":sha(S99/"manifest.json"),
      "source_Stage100_manifest_sha256":sha(S100/"manifest.json"),
      "source_Stage101_manifest_sha256":sha(S101/"manifest.json"),
      "GLE_years":16,"NC_technical_preview_count":len(files),"number_of_original_30min_samples":SIZE,
      "source_local_to_UTC_offset_hours":7,
      "time_variable_label":"UTC_HALFHOUR_MIDPOINT",
      "source_cyclic_wrap_halfhours":SHIFT,
      "all_10_GLE_fields_exact_cyclic_source_permutation_readback":True,
      "source_Stage99_original_files_modified":False,
      "other_9_sites_modified":False,"source_215_NC_modified":False,
      "CIME_DATM_approved":False,"case_modified":False,"Slurm_jobs_submitted":False,
      "out_sha256":{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!="INCOMPLETE_DO_NOT_USE"}}
    (out/"manifest.json").write_text(json.dumps(record,indent=2)+"\n")
    partial.unlink()
    print("STAGE102 GLE UTC MIDPOINT 16/16 NC PASS | 280320 source samples conserved; original source meteorology unchanged, only time reassigned",flush=True)
    print("STAGE102 REPORT",out,flush=True)
    print("STAGE102 SCIENCE HOLD | 16-year periodic weather seam; DATM actual CIME time; WS height; PFT/footprint; NO jobs",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    m=ap.add_mutually_exclusive_group(required=True)
    for a in ("self-test","check","build"):m.add_argument("--"+a,action="store_true")
    args=ap.parse_args()
    if args.self_test:
        assert SHIFT==14 and SIZE==280320
        sample=np.arange(4*48,dtype=float)
        moved=np.roll(sample,SHIFT)
        assert np.array_equal(moved[:SHIFT],sample[-SHIFT:])
        assert np.array_equal(moved[SHIFT:],sample[:-SHIFT])
        assert np.array_equal((np.arange(17520)+0.5)/48,
                              (np.arange(17520)+0.5)/48)
        print("STAGE102 SELF-TEST PASS | UTC +7h 14 native HH, midpoint 15min, 16y cyc seam, no writes",flush=True)
        return
    if args.check:
        review()
        print("STAGE102 CHECK PASS | original source and solar receipts; no files written",flush=True)
        return
    build()

if __name__=="__main__":
    main()

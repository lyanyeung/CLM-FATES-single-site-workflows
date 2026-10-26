#!/usr/bin/env python3
"""Stage106 US-GLE: replace artificial 2020 weather seam with REAL dated
2004-12-31 17:00–23:30 LST ERA companion (=2005-01-01 00:00–06:30 UTC).

Source: original SHA-pinned AmeriFlux FLUXNET ERA5_HH 1981-2025, with
site-aligned LOCAL-STANDARD time stamps. The seven ERA fields are exactly
the same variable/units as the original Batch02 Stage07 native engine.
NO timestamp UTC guessing, ERA5 CDS download, new climate interpolation,
case modification, raw source edit or model submission.

--check: source SHA/14 timestamps/physics/joins; READ-ONLY.
--build: new independent 16 annual NetCDF copies, replace FIRST 14 slots
of 2005 only with the dated 2004-LST ERA records. Validate all meteorology,
humidity aliases, source-provenance and realistic temperature/pressure seam;
retain SCIENCE_HOLD for site PFT, 23.4m TA vs 22.65m WS, CIME model run.
"""
import argparse,csv,hashlib,json,math,shutil
from datetime import datetime,timedelta,timezone
from pathlib import Path
from uuid import uuid4
import netCDF4 as nc
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S7=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
S102=ROOT/"reports/stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_20261026T114427Z_e63d3051"
S104=ROOT/"reports/stage104_GLE_CIME_seam_quantiles_READONLY_20261026T121303Z_166e2732"
S105=ROOT/"reports/stage105_GLE_BIF_2005_UTC_backfill_readonly_20261026T122307Z_b6d23393"
VARS=("TBOT","QBOT","SHUM","RH","PSRF","FSDS","FLDS","WIND","PRECTmms","ZBOT")
RAW=("TA_ERA","VPD_ERA","PA_ERA","SW_IN_ERA","LW_IN_ERA","WS_ERA","P_ERA")
YEAR_LEN=17520
REPLACE_N=14
YEARS=tuple(range(2005,2021))
SRC_TIMES=tuple((datetime(2004,12,31,17)+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(REPLACE_N))
VERSION="BATCH02_STAGE106_GLE_TRUE_DATED_ERA_LST_PREHISTORY_16UTC_MID_NC"
PHYS={"TBOT":(180,340),"QBOT":(0,.08),"RH":(0,100),
      "PSRF":(49000,111000),"FSDS":(0,1600),"FLDS":(0,800),
      "WIND":(0,75),"PRECTmms":(0,.1667),"ZBOT":(.5,150)}
SOURCE_COOR=(41.3665,-106.2399)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def js(p):return json.loads(Path(p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,default=str)+"\n")
def finite(x):
    try:
        v=float(x)
        return v if math.isfinite(v) and v>-9990 else None
    except (ValueError,TypeError):return None

def source_gate():
    m102,m104,m105=js(S102/"manifest.json"),js(S104/"manifest.json"),js(S105/"manifest.json")
    if (m102.get("NC_technical_preview_count")!=16 or
        m102.get("number_of_original_30min_samples")!=280320 or
        m102.get("source_cyclic_wrap_halfhours")!=14 or
        m102.get("CIME_DATM_approved") is not False or
        m104.get("stage102_sha256")!=sha(S102/"manifest.json") or
        m104.get("production_DATM_approved") is not False or
        m105.get("Stage104_manifest_sha256")!=sha(S104/"manifest.json") or
        m105.get("production_DATM_approved") is not False or
        m105.get("ERA_backfill_generated") is not False or
        not (S102/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").exists()):
        raise ValueError("Stage102/104/105 exact source or SCIENCE_HOLD mismatch")
    for root,table in ((S102,"out_sha256"),(S104,"output_SHA256"),(S105,"output_sha256")):
        m=js(root/"manifest.json")
        for name,h in m[table].items():
            if sha(root/name)!=h:
                raise ValueError("Prior immutable science receipt changed "+str(root/name))
    original=js(S7/"exact_input_manifest.json")
    g={r["site"]:r for r in original["sites"]}["US-GLE"]
    if int(g["first_year"])!=2005 or int(g["last_year"])!=2020 or g["native_minutes"]!=30:
        raise ValueError("GLE original source period/native 30min interval differs")
    src=Path(g["era"]).resolve()
    if not src.is_file() or sha(src)!=original["input_sha256"].get(str(src)):
        raise ValueError("US-GLE exact FLUXNET 1981-2025 ERA source SHA missing/mismatch")
    prov=js(S105/"source_ERA5_local_timestamp_provenance.json")
    if (str(src)!=prov["original_comparison_csv"] or
        prov["sha256"]!=sha(src) or
        prov["original_missing_2004_local_halfhours"]!=[]):
        raise ValueError("Stage105 historical 2004 local 14/14 provenance changed")
    # The immutable Stage105 MANIFEST unfortunately names its 14 expected
    # source slots 'source_original_2004_local_missing_records'. That old
    # count describes the expected 14 slots, NOT true missing rows.
    # Only the exact independently checked missing-list [] proves 14/14.
    if m105.get("source_original_2004_local_missing_records")!=14:
        raise ValueError("Original Stage105 expected-slot count changed")
    files=sorted(js(S102/"16_year_UTC_midpoint_NC_source_manifest.json"),key=lambda x:x["year"])
    if len(files)!=16 or {x["year"] for x in files}!=set(YEARS):
        raise ValueError("Source 16 annual NC list changed")
    for x in files:
        if sha(x["new"])!=x["sha256"] or sha(x["original"])!=x["original_sha256"]:
            raise ValueError("Stage102/99 original annual GLE source changed "+str(x["year"]))
    return src,files

def extract_exact_rows(era):
    wanted=set(SRC_TIMES)
    found={}
    with era.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not {"TIMESTAMP_START",*RAW}.issubset(reader.fieldnames or []):
            raise ValueError("Original ERA companion lacks required 7 ERA fields")
        if "TIMESTAMP_END" not in reader.fieldnames:
            raise ValueError("Original AmeriFlux ERA interval-END time column absent")
        for row in reader:
            stamp=str(row["TIMESTAMP_START"]).strip().removesuffix(".0")
            if stamp not in wanted:continue
            if stamp in found:raise ValueError("ERA companion duplicate source timestamp "+stamp)
            vals={x:finite(row[x]) for x in RAW}
            if any(v is None for v in vals.values()):
                raise ValueError("ERA source missing/sentinel 2004 record "+stamp)
            dt=datetime.strptime(stamp,"%Y%m%d%H%M")
            expected=(dt+timedelta(minutes=30)).strftime("%Y%m%d%H%M")
            if row["TIMESTAMP_END"].strip().removesuffix(".0")!=expected:
                raise ValueError("ERA source raw interval not 30min "+stamp)
            found[stamp]=vals
    if set(found)!=wanted:
        raise ValueError("ERA historical local-standard 14 records not complete")
    return [found[x] for x in SRC_TIMES]

def convert(samples):
    back=[]
    for k,row in enumerate(samples):
        t,vpd,pa,sw,lw,ws,prec=[row[f] for f in RAW]
        # Verified Stage07 site-to-CLM model conventions:
        # TA °C -> K; VPD hPa + PA kPa -> humidity kg/kg
        # PA kPa -> Pa; P mm per native 1800s -> mm/s
        es=611.2*math.exp(17.67*t/(t+243.5))
        ea=es-100*vpd
        rh=100*ea/es
        pressure=pa*1000
        q=.622*ea/(pressure-.378*ea)
        values={"TBOT":t+273.15,"QBOT":q,"SHUM":q,"RH":rh,
                "PSRF":pressure,"FSDS":max(0,sw),"FLDS":lw,
                "WIND":max(0,ws),"PRECTmms":max(0,prec)/1800,
                "ZBOT":23.4}
        if (not (0<rh<=100) or vpd<0 or
            any(not math.isfinite(x) for x in values.values()) or
            any(not lo<=values[name]<=hi for name,(lo,hi) in PHYS.items())):
            raise ValueError("ERA source historical met/humidity physical HOLD at "+SRC_TIMES[k])
        if sw<0 or ws<0 or prec<0:
            raise ValueError("ERA negative source met; requires explicit review "+SRC_TIMES[k])
        back.append(values)
    return back

def read_seam_source(files,back):
    p=next(Path(x["new"]) for x in files if x["year"]==2005)
    with nc.Dataset(p) as ds:
        if (ds.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY"
            or ds.stage102_case_submit_approved!="NO"
            or ds["time"].calendar!="noleap"):
            raise ValueError("Source data scientifically approved unexpectedly")
        lat=float(ds["LATIXY"][0,0]);lon=float(ds["LONGXY"][0,0])
        normalized_lon=(lon+180)%360-180
        if (abs(lat-SOURCE_COOR[0])>1e-5 or
            abs(normalized_lon-SOURCE_COOR[1])>1e-5):
            raise ValueError("GLE original BIF and NC coordinates DIFFER materially")
        old={n:np.ma.filled(ds[n][:REPLACE_N+1,0,0],np.nan).astype(float)
             for n in VARS}
    result={}
    for name in VARS:
        newlast=back[-1][name]
        nextval=float(old[name][REPLACE_N])
        oldlast=float(old[name][REPLACE_N-1])
        result[name]=dict(
            source_2020_last_to_2005_original_jump=nextval-oldlast,
            new_2004_ERA_last_to_2005_original_jump=nextval-newlast,
            old_abs_jump=abs(nextval-oldlast),new_abs_jump=abs(nextval-newlast),
            last_ERA_2004_local=back[-1][name],
            first_observed_2005_UTC_0715=nextval,
            UTC_first_timestamp="2005-01-01 00:15",
            UTC_seam_timestamp="2005-01-01 07:15",
            source_BIF_lat_lon_normalized_match=True)
    return result

def source_review():
    era,files=source_gate()
    samples=extract_exact_rows(era)
    converted=convert(samples)
    result=read_seam_source(files,converted)
    for n,row in result.items():
        print("STAGE106 JOIN",n,"OLD_ABS",format(row["old_abs_jump"],".9g"),
              "ERA_BACKFILL_ABS",format(row["new_abs_jump"],".9g"),flush=True)
    print("STAGE106 SOURCE MATCH | 14/14 2004 local LST ERA records, original source SHA PASS",
          "longitude 253.7601E == -106.2399",flush=True)
    # New ERA transition need not be smaller for ALL variables; however a
    # worse-than-original temperature or pressure seam needs science review,
    # not automatic production activation.
    problem=[n for n in ("TBOT","PSRF") if
        result[n]["new_abs_jump"]>result[n]["old_abs_jump"]]
    print("STAGE106 BOUNDARY EVALUATION",("IMPROVED_TBOT_PSRF" if not problem else
          "REVIEW_WORSENED_"+",".join(problem)),
          "NO_IMPLICIT_SCIENCE_APPROVAL",flush=True)
    return files,converted,result,problem,era

def build():
    files,values,joins,issues,era=source_review()
    out=ROOT/"reports"/("stage106_GLE_ERA_2004LST_14HH_backfilled_UTCmid_16NC_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"SCIENCE_HOLD_NO_CIME_MODEL_OR_SPINUP").write_text(
        "Stage106 source-dated ERA prehistory 14 original 2004 LST halfhours; replacing unobserved 2020 proxy, test CIME model timing and real site PFT/WS elevation prior to production.\n")
    (out/"INCOMPLETE_DO_NOT_USE").write_text("16 NC rebuild incomplete\n")
    folder=out/"US-GLE"/"ERA_2004_LST_TO_2005_UTC_HALFHOUR_MID"
    folder.mkdir(parents=True,exist_ok=False)
    output=[]
    for x in files:
        year=x["year"];inp=Path(x["new"]);dst=folder/f"{year}.nc"
        if sha(inp)!=x["sha256"]:raise ValueError("Stage102 original changed")
        shutil.copyfile(inp,dst)
        if year==2005:
            with nc.Dataset(dst,"a") as ds:
                for n in VARS:
                    src=np.array([r[n] for r in values],dtype=float)
                    ds[n][:REPLACE_N,0,0]=src
                ds.stage106_boundary_origin="FLUXNET_ERA5_HH_2004_12_31_LOCAL_17_00_to_23_30"
                ds.stage106_ERA_source_SHA256=sha(era)
                ds.stage106_values_changed_first_14_only="YES"
                ds.stage106_2004_ERA_source_time_not_raw_UTC="YES_LOCAL_STANDARD_TIME"
                ds.stage106_longitude_normalized="253.7601E_identical_to_minus106.2399"
                ds.stage106_CIME_science_approved="NO"
        with nc.Dataset(dst) as ds,nc.Dataset(inp) as original:
            for n in VARS:
                a=np.ma.filled(original[n][:],np.nan).astype(float)
                b=np.ma.filled(ds[n][:],np.nan).astype(float)
                if year==2005:
                    if not np.array_equal(a[REPLACE_N:],b[REPLACE_N:]):
                        raise ValueError("Outside exact first14 historical ERA slots changed "+n)
                    v=np.array([r[n] for r in values])
                    if not np.allclose(b[:REPLACE_N,0,0],v,rtol=1e-7,atol=1e-9):
                        raise ValueError("Historical ERA slot conversion/write mismatch "+n)
                elif not np.array_equal(a,b):
                    raise ValueError("Non-2005 NC unexpectedly changed "+str(year))
            if (ds.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY" or
                ds["time"].calendar!="noleap" or
                not np.array_equal(np.asarray(ds["time"][:]),np.asarray(original["time"][:]))):
                raise ValueError("Model UTC midpoint time/tech preview status changed")
        output.append({"year":year,"new":str(dst),"sha256":sha(dst),
                       "source_Stage102":str(inp),"source_sha256":x["sha256"],
                       "changed_original_samples":14 if year==2005 else 0})
        print("STAGE106 NC VERIFICATION",year,"PASS",flush=True)
    with (out/"2004_ERA_LOCAL_14HH_to_2005_UTC_model_native_fields.csv").open("w",newline="") as f:
        cols=["original_ERA_source_timestamp_local",*VARS]
        w=csv.DictWriter(f,cols);w.writeheader()
        for t,r in zip(SRC_TIMES,values):
            w.writerow({"original_ERA_source_timestamp_local":t,**r})
    write(out/"2005_ERA_vs_2020_cyclic_internal_seam_changes.json",joins)
    write(out/"16_year_independent_NC_receipts.json",output)
    manifest={"schema":VERSION,
        "stage102_manifest_SHA256":sha(S102/"manifest.json"),
        "stage105_manifest_SHA256":sha(S105/"manifest.json"),
        "source_ERA_SHA256":sha(era),
        "16_year_new_NC_count":len(output),"2004_LST_ERA_replaced_UTC_first_slots":14,
        "all_original_2005_later_and_other_15_year_values_unchanged":True,
        "1981_2025_ERA_source_present_and_exact14":True,
        "surface_coords_normalized_to_2026_BIF_match":True,
        "seam_temperature_pressure_worsened":bool(issues),
        "source_2020_synthetic_weather_seam_removed":True,
        "model_CIME_clock_runtime_verified":False,
        "FATES_PFT_tower_footprint_approved":False,
        "distinct_wind_air_height_approved":False,
        "science_DATM_approved":False,"Slurm_jobs_submitted":False,
        "original_stage102_NC_modified":False,
        "out_sha256":{p.name:sha(p) for p in out.iterdir()
                      if p.is_file() and p.name!="INCOMPLETE_DO_NOT_USE"}}
    write(out/"manifest.json",manifest)
    (out/"INCOMPLETE_DO_NOT_USE").unlink()
    print("STAGE106 GLE 16/16 ERA PREHISTORY NC PASS | original 2004 LST 14 halfhours",
          "replaced 2020 cycle proxies; 280320 original timeline conserved",flush=True)
    print("STAGE106 REPORT",out,flush=True)
    print("STAGE106 SCIENCE HOLD | actual CIME read, ENF FATES tower PFT/footprint, TA/WS heights;",
          "NO SPINUP",flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","build"):g.add_argument("--"+name,action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert len(SRC_TIMES)==14 and SRC_TIMES[0]=="200412311700" and SRC_TIMES[-1]=="200412312330"
        assert datetime(2004,12,31,17)+timedelta(hours=7)==datetime(2005,1,1)
        assert (253.7601+180)%360-180>-106.24001
        assert len(VARS)==10
        print("STAGE106 SELF-TEST PASS | original 14 source LST halfhours, 7 ERA fields, 10 NC fields, no writes")
        return
    if a.check:
        source_review()
        print("STAGE106 CHECK PASS | 14 source exact timestamps, humidity/pressure conversion, no writes")
        return
    build()

if __name__=="__main__":main()

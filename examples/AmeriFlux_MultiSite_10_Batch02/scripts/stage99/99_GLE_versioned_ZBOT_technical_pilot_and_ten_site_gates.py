#!/usr/bin/env python3
"""Batch02 Stage99: US-GLE 16-year ZBOT TECHNICAL PILOT + ten-site gates.

Operator Stage98 proves GLE original dated BIF TA_F 23.4m and WS_F 22.65m
from 2005-01-01, and independent ten-site Stage95 generated 215 annual NC.
Copy GLE's 16 already-checked NC to a NEW VERSION; preserve every existing
field bit-for-bit, add ZBOT based on measured TA_F reference height only,
retain *different* wind sensor height in evidence/global metadata. Audit all.
DO NOT infer other sites' prehistory, normalize UTC clocks, assume CIME
DATM QBOT/SHUM mapping, activate a stream, or submit Slurm jobs.
"""
import argparse,csv,hashlib,json,math,shutil
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

import netCDF4 as nc
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S95=ROOT/"reports/stage95_ten_site_122_user_approved_versioned_forcing_215NC_20261026T034516Z_f4afa348"
S98=ROOT/"reports/stage98_batch02_BIF_date_precision_and_height_prehistory_20261026T040850Z_cc68e832"
SITES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1","US-Ho1","US-Ho2","US-Ho3","US-ICh","US-ICt")
CANONICAL=("time","lat","lon","LATIXY","LONGXY","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms")
ZBOT_TA=23.4
HEIGHT_WS=22.65
GLE_YEARS=tuple(range(2005,2021))
SITE="US-GLE"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def j(p):return json.loads(Path(p).read_text())
def readcsv(p):
    with Path(p).open("r",newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))
def writecsv(p,rows,columns):
    with Path(p).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader();w.writerows(rows)

def gate():
    m95=j(S95/"manifest.json")
    m98=j(S98/"manifest.json")
    if (m95.get("site_pass")!=10 or
        m95.get("annual_netcdf_generated_and_readback_verified")!=215 or
        m95.get("production_DATM_approved") is not False or
        m95.get("source_forcing_sha256_unchanged") is not True or
        not (S95/"SCIENCE_HOLD_DO_NOT_ACTIVATE_DATM_OR_SUBMIT").exists() or
        (S95/"INCOMPLETE_DO_NOT_USE").exists()):
        raise ValueError("Stage95 ten-site source/215NC science-HOLD changed")
    if (m98.get("schema")!="BATCH02_STAGE98_BADM_DATE_PRECISION_FIX_AND_HEIGHT_GAPS_v1"
        or m98.get("site_count")!=10 or
        m98.get("production_DATM_permitted") is not False or
        m98.get("ZBOT_or_NC_changed") is not False):
        raise ValueError("Stage98 precision/source provenance changed")
    for filename,hashvalue in m98["out_sha256"].items():
        if sha(S98/filename)!=hashvalue:
            raise ValueError("Stage98 original metadata receipt SHA differs: "+filename)
    histories=j(S98/"site_historical_height_evidence.json")
    if set(histories)!=set(SITES):raise ValueError("Original 10-site metadata inventory differed")
    g=histories[SITE]["TA_and_WS_height_evidence"]
    for v,height in (("TA_F",ZBOT_TA),("WS_F",HEIGHT_WS)):
        x=g[v]
        if (x["status"]!="PREHISTORY_COVERED_BIF_HEIGHT_CANDIDATE_ONLY" or
            x["prehistory_missing_days"]!=0 or
            x["distinct_heights_m"]!=[height] or
            x["unique_dated_height_events"]!=1 or
            len(x["exact_dated_height_events"])!=1 or
            x["exact_dated_height_events"][0]["date_label"]!="2005-01-01 00:00:00" or
            x["exact_dated_height_events"][0]["height_m"]!=height or
            x["exact_dated_height_events"][0]["precision"]!="MINUTE"):
            raise ValueError("GLE original BIF measured height not exact/constant for full 2005-2020 forcing: "+v)
    if histories[SITE]["UTC_BIF_hours_candidates"]!=[-7.0]:
        raise ValueError("Original GLE official BIF UTC offset changed")
    site_records={x["site"]:x for x in m95["sites"]}
    if set(site_records)!=set(SITES):raise ValueError("Stage95 site roster changed")
    gle=site_records[SITE]
    files=gle["NC_technical_preview_files"]
    if len(files)!=16 or {int(x["year"]) for x in files}!=set(GLE_YEARS):
        raise ValueError("GLE year inventory differs from 16 continuous original NC")
    for f in files:
        p=Path(f["path"])
        if not p.is_file() or sha(p)!=f["sha256"]:
            raise ValueError("Original Stage95 GLE NC source SHA mismatch "+str(p))
    return histories,site_records,files

def inspect_clock_and_mapping(samples):
    with nc.Dataset(Path(samples[0]["path"])) as dataset:
        variables=set(dataset.variables)
        if not {"QBOT","time","WIND","TBOT"}.issubset(variables):
            raise ValueError("GLE original NC expected source climate variables absent")
        time=dataset.variables["time"]
        if time.calendar!="noleap" or "local-start" not in time.long_name:
            raise ValueError("Stage95 GLE original native-local-time labels altered")
        return {"netcdf_qbot_variable_exists":True,"netcdf_shum_variable_exists":"SHUM" in variables,
                "requires_explicit_stream_QBOT_to_SHUM_mapping":True,
                "source_original_local_start_not_UTC":True,
                "official_bif_utc_offset_hours":-7.0,
                "allow_automated_model_utc_shift":False,
                "stream_sampling_phase_approved":False}

def diff_verification(old,new,year):
    with nc.Dataset(old) as a,nc.Dataset(new) as b:
        expected=365*48
        if (len(a.dimensions["time"])!=expected or
            len(b.dimensions["time"])!=expected or
            set(CANONICAL)-set(b.variables) or
            tuple(b.variables["ZBOT"].dimensions)!=("time","lat","lon") or
            getattr(b.variables["ZBOT"],"units",None)!="m"):
            raise ValueError("GLE original/native NetCDF layout changed "+str(year))
        za=np.asarray(b.variables["ZBOT"][:],dtype=float)
        if za.shape!=(expected,1,1) or not np.allclose(za,ZBOT_TA,rtol=0,atol=0):
            raise ValueError("GLE newly written ZBOT array not exact original TA_F 23.4 m")
        for name in CANONICAL:
            aa=np.asarray(a.variables[name][:])
            bb=np.asarray(b.variables[name][:])
            if aa.shape!=bb.shape or not np.array_equal(aa,bb,equal_nan=True):
                raise ValueError("Existing original NC changed in versioned GLE ZBOT pilot: "+name)
        if (b.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY" or
            b.production_DATM_release!="NO_Ho1_nonQC0_2000_and_clock_ZBOT_pending" or
            b.ZBOT_height_source!="AmeriFlux_release_BIF_original_TA_F_VAR_INFO_HEIGHT"):
            raise ValueError("Preview had incorrect science approval or ZBOT source")
        if (b.wind_sensor_BIF_height_m!=HEIGHT_WS or
            b.air_temperature_sensor_BIF_height_m!=ZBOT_TA):
            raise ValueError("GLE separate wind and TA reference height lost")

def site_gate_rows(histories):
    rows=[]
    for site in SITES:
        d=histories[site]["TA_and_WS_height_evidence"]
        ta=d["TA_F"]; ws=d["WS_F"]
        if site=="US-GLE":
            lane="ZBOT_TA_ONLY_TECHNICAL_PILOT_ELIGIBLE"
            decision="23.4m TA reference vs 22.65m wind reference; exact DATM height mapping needs approval"
        elif site in ("US-BZS","US-Ho1"):
            lane="MISSING_OFFICIAL_BOTH_HEIGHT_HISTORIES"
            decision="Retrieve official BASE Measurement Height source tied to this FLUXNET release; never invent constant ZBOT"
        else:
            lane="BEFORE_FIRST_OFFICIAL_HEIGHT_DATA_GAP"
            decision="Locate earlier dated native heights; otherwise request explicit bounded prehistory policy before any candidate model run"
        if site=="US-Ho1":
            decision+="; separate 2000-12-27 QC1→QC2 18.746 C source T HOLD"
        rows.append({"site":site,"status":lane,
            "TA_first":ta["first_height_date"] or "",
            "TA_heights_m":",".join(map(str,ta["distinct_heights_m"])),
            "TA_gap_days":ta["prehistory_missing_days"],
            "WS_first":ws["first_height_date"] or "",
            "WS_heights_m":",".join(map(str,ws["distinct_heights_m"])),
            "WS_gap_days":ws["prehistory_missing_days"],
            "UTC_BIF_hours":",".join(map(str,histories[site]["UTC_BIF_hours_candidates"])),
            "recommended_next":decision,"CIME_DATM_release":"NO"})
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","build"):
        g.add_argument("--"+k,action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert len(GLE_YEARS)==16 and GLE_YEARS[0]==2005 and GLE_YEARS[-1]==2020
        assert len(SITES)==10 and ZBOT_TA!=HEIGHT_WS
        assert set(CANONICAL)>={"TBOT","QBOT","WIND"}
        print("STAGE99 SELF-TEST PASS | original TA vs WS heights distinct; 16 NC candidate, no writes")
        return 0
    histories,sites,files=gate()
    mapping=inspect_clock_and_mapping(files)
    rows=site_gate_rows(histories)
    print("STAGE99 VERIFIED | 10-site heights, 215 original NC retained, GLE TA=23.4m, WS=22.65m, official UTC=-7 but NOT SHIFTED",flush=True)
    for r in rows:
        print("STAGE99 SITE",r["site"],r["status"],
              "TA_gap_days",r["TA_gap_days"],"WS_gap_days",r["WS_gap_days"],flush=True)
    print("STAGE99 STREAM WARNING | original NC QBOT name differs from previous template SHUM; explicit QBOT-to-SHUM mapping and CIME phase review needed",flush=True)
    if a.check:
        print("STAGE99 CHECK PASS | 16 source NC verified; NO ZBOT FILES WRITTEN",flush=True)
        return 0
    out=ROOT/"reports"/("stage99_GLE_23p4m_source_ZBOT_16yr_TECHNICAL_ONLY_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"SCIENCE_HOLD_NO_CIME_CASE_OR_DATM_ACTIVATION").write_text(
        "GLE versioned ZBOT=23.4m TA_F only; WIND source height=22.65m separately, time label/local-vs-UTC and DATM phase NOT approved, FATES PFT/landunits, CIME stream QBOT→SHUM and smoke test pending."+chr(10))
    folder=out/"US-GLE"/"TECHNICAL_16NC"
    folder.mkdir(parents=True,exist_ok=False)
    results=[]
    for src in sorted(files,key=lambda x:int(x["year"])):
        yr=int(src["year"]);old=Path(src["path"]);new=folder/f"{yr}.nc"
        if sha(old)!=src["sha256"]:raise ValueError("GLE immutable source NC changed during Stage99")
        shutil.copyfile(old,new)
        with nc.Dataset(new,"a") as d:
            if "ZBOT" in d.variables:
                raise ValueError("Original GLE NC already has a ZBOT: don't overwrite")
            z=d.createVariable("ZBOT","f8",("time","lat","lon"),zlib=True,complevel=2)
            z.units="m"
            z.long_name="Air temperature and humidity forcing reference height from site original TA_F BIF; wind measured at a distinct height"
            z[:,0,0]=np.full((365*48,),ZBOT_TA)
            d.ZBOT="SOURCE_VERIFIED_TA_F_REFERENCE_HEIGHT_BUT_DATM_NOT_APPROVED"
            d.ZBOT_height_source="AmeriFlux_release_BIF_original_TA_F_VAR_INFO_HEIGHT"
            d.air_temperature_sensor_BIF_height_m=ZBOT_TA
            d.wind_sensor_BIF_height_m=HEIGHT_WS
            d.wind_height_difference_not_normalized_m=ZBOT_TA-HEIGHT_WS
            d.stage99_original_versioned_stage95_sha256=src["sha256"]
            d.stage99_new_variable_only="ZBOT"
            d.stage99_clock_offset_correction="NONE_SOURCE_LOCAL_START_LABEL_UNCHANGED"
            d.stage99_model_case_approval="NO"
        diff_verification(old,new,yr)
        results.append({"year":yr,"original":str(old),"original_sha256":sha(old),
                        "with_ZBOT":str(new),"sha256":sha(new),
                        "air_temperature_BIF_m":ZBOT_TA,
                        "wind_source_BIF_m":HEIGHT_WS,
                        "unchanged_original_meteorology_fields":"PASS"})
        print("STAGE99 GLE ZBOT NC VERIFIED",yr,"TA_REF_m",ZBOT_TA,"WIND_REF_m",HEIGHT_WS,flush=True)
    writecsv(out/"ten_site_manual_height_decision_queue.csv",rows,list(rows[0]))
    (out/"CIME_FIELD_AND_TIME_MAPPING_HOLD.json").write_text(
        json.dumps(mapping,indent=2)+chr(10))
    (out/"16_year_GLE_NC_manifest.json").write_text(
        json.dumps(results,indent=2)+chr(10))
    receipt={"schema":"BATCH02_STAGE99_GLE_SOURCE_ZBOT_16NC_PILOT_NONACTIVATING",
        "original_stage95_sha256":sha(S95/"manifest.json"),
        "original_stage98_sha256":sha(S98/"manifest.json"),
        "source_site":"US-GLE","new_NC_years":len(results),
        "air_temperature_BIF_ZBOT_m":ZBOT_TA,"wind_BIF_height_m":HEIGHT_WS,
        "original_canonical_met_unchanged_all_years":True,
        "clock_shift_applied":False,"ZBOT_wind_height_discrepancy_resolved_for_model":False,
        "production_DATM_approved":False,
        "active_CIME_case_edited":False,"Slurm_job_submitted":False,
        "outputs_sha256":{x.name:sha(x) for x in out.iterdir() if x.is_file()}}
    (out/"manifest.json").write_text(json.dumps(receipt,indent=2)+chr(10))
    if len(results)!=16:raise ValueError("GLE ZBOT NC 16-year completion failed")
    print("STAGE99 GLE 16/16 TECHNICAL NC WITH SOURCE ZBOT PASS | original meteorology unchanged; wind height separately retained",flush=True)
    print("STAGE99 REPORT",out,flush=True)
    print("STAGE99 SCIENCE HOLD | 9 other sites prehistory and GLE UTC/DATM phase, QBOT→SHUM, distinct WS height, PFT and CIME remain; NO model submissions",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

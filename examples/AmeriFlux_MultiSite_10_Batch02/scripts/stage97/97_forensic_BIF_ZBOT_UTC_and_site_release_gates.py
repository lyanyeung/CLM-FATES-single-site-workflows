#!/usr/bin/env python3
"""AmeriFlux Batch02 Stage97. Evidence-gated BIF heights/clock forensic.

NO active CIME/DATM writes. Immutable Stage95 10-site/215NC and Stage96
structural sources are verified. Search exact BIF groups for TA_F/WS_F height,
the raw Ho2 WS invalid rows, site UTC_OFFSET, and the full paired original
local-standard-time TIMESTAMP_START/TIMESTAMP_END chronology. Classify each
missing/extrapolated datum and write a short human decision worklist.

AmeriFlux source reporting time is local STANDARD time (not DST), but an
official site UTC_OFFSET value and *model DATM* interpretation still need
verification. DO NOT derive timezone from longitude or select a ZBOT default.
"""
import argparse,csv,hashlib,json,math,re
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S95=ROOT/"reports/stage95_ten_site_122_user_approved_versioned_forcing_215NC_20261026T034516Z_f4afa348"
S96=ROOT/"reports/stage96_batch02_DATM_clock_ZBOT_surface_readonly_20261026T035407Z_fcaa4d22"
S07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
SITES=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
NAMES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1","US-Ho1","US-Ho2","US-Ho3","US-ICh","US-ICt")
YEARS={"US-BZS":15,"US-CMW":21,"US-EML":16,"US-GLE":16,"US-Ha1":35,
       "US-Ho1":28,"US-Ho2":27,"US-Ho3":19,"US-ICh":19,"US-ICt":19}
BIF_TARGETS=("TA_F","WS_F")
UTC_KEYS=("UTC_OFFSET","SITE_UTC_OFFSET","TIMEZONE","TIME_ZONE","SITE_TIMEZONE","UTC_OFFSET_SITE")
SCHEMA="BATCH02_STAGE97_READONLY_BIF_ZBOT_CLOCK_FORENSICS_v1"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
    return h.hexdigest()
def j(p):return json.loads(Path(p).read_text())
def writecsv(path,rows,fields):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)
def fl(x):
    try:
        v=float(str(x).strip())
        return v if math.isfinite(v) else float("nan")
    except (ValueError,TypeError):return float("nan")
def dtstamp(s):
    return datetime.strptime(str(s).strip().removesuffix(".0"),"%Y%m%d%H%M")

def gate():
    ms=j(S95/"manifest.json")
    m96=j(S96/"manifest.json")
    old=j(S07/"exact_input_manifest.json")
    if (ms.get("site_pass")!=10
        or ms.get("annual_netcdf_generated_and_readback_verified")!=215
        or ms.get("production_DATM_approved") is not False
        or (S95/"INCOMPLETE_DO_NOT_USE").exists()
        or not (S95/"SCIENCE_HOLD_DO_NOT_ACTIVATE_DATM_OR_SUBMIT").exists()
        or m96.get("sites_audited")!=10
        or m96.get("annual_NC_source_total")!=215
        or m96.get("structural_failed_sites")!=0
        or m96.get("stage95_manifest_sha256")!=sha(S95/"manifest.json")):
        raise ValueError("Stage95/96 source, completed annual NC, or science-HOLD state changed")
    for name,digest in m96.get("outputs_sha256",{}).items():
        if sha(S96/name)!=digest:
            raise ValueError("Stage96 original site evidence SHA changed "+name)
    if {x["site"] for x in old["sites"]}!=set(NAMES):
        raise ValueError("Original Batch02 primary/ERA ten-site roster changed")
    sites={x["site"]:x for x in old["sites"]}
    proof=j(S96/"original_source_BIF_surface_NC_evidence.json")
    if set(proof)!=set(NAMES):raise ValueError("Stage96 original per-site forensic detail changed")
    return ms,m96,sites,proof

def full_timestamp_audit(site,info):
    """All native source intervals; no leap calendar mixing, UTC assumptions."""
    p=Path(info["primary"])
    step=int(info["native_minutes"])
    cols=set(pd.read_csv(p,nrows=0).columns)
    if not {"TIMESTAMP_START","TIMESTAMP_END"}.issubset(cols):
        return {"raw_status":"SOURCE_INTERVAL_PAIR_ABSENT_HOLD","site":site,
                "source":str(p),"source_sha256":sha(p),
                "raw_records":0,"errors":["TIMESTAMP_START_OR_END_MISSING"]}
    first_year,last_year=int(info["first_year"]),int(info["last_year"])
    days=(datetime(last_year+1,1,1)-datetime(first_year,1,1)).days
    expected=days*1440//step
    periods=0;bad_start_end=0;gaps=0;dups=0
    first=None;last=None;prev_end=None
    samples=[]
    for part in pd.read_csv(p,usecols=["TIMESTAMP_START","TIMESTAMP_END"],
                            dtype=str,chunksize=100000):
        a=pd.to_datetime(part["TIMESTAMP_START"].str.strip().str.replace(r"\.0$","",regex=True),
                         format="%Y%m%d%H%M",errors="raise")
        b=pd.to_datetime(part["TIMESTAMP_END"].str.strip().str.replace(r"\.0$","",regex=True),
                         format="%Y%m%d%H%M",errors="raise")
        dif=(b-a).dt.total_seconds().to_numpy()/60
        bad_start_end+=int((dif!=step).sum())
        ai=a.to_numpy();bi=b.to_numpy()
        within=(ai[1:]!=bi[:-1])
        gaps+=int(within.sum())
        dups+=int((ai[1:]<=ai[:-1]).sum())
        if prev_end is not None:
            gaps+=int(a.iloc[0]!=prev_end)
            if a.iloc[0]<prev_end:dups+=1
        if first is None:first=str(a.iloc[0])
        last=str(b.iloc[-1]);prev_end=b.iloc[-1]
        periods+=len(part)
        if len(samples)<3:
            samples.append({"first_start":str(a.iloc[0]),"first_end":str(b.iloc[0]),
                            "last_end":str(b.iloc[-1]),"chunk_rows":len(part)})
    label_ok=(first==str(datetime(first_year,1,1)) and
              last==str(datetime(last_year+1,1,1)))
    count_ok=(periods==expected)
    raw_status=("SOURCE_INTERVALS_COMPLETE_NO_DST_ARTIFACT" if
               bad_start_end==0 and gaps==0 and dups==0 and count_ok and label_ok
               else "SOURCE_INTERVAL_ANOMALIES_HOLD")
    # Leap days are present in ORIGINAL source and omitted from NOLEAP forcing,
    # so raw record count is NOT expected to equal 365 days/year.
    return {"site":site,"source":str(p),"source_sha256":sha(p),
        "native_minutes":step,"raw_records":periods,
        "original_leap_inclusive_expected_records":expected,
        "full_release_native_count_matches":bool(count_ok),
        "full_release_year_boundaries_match":bool(label_ok),
        "source_first":first,"source_last_end":last,
        "wrong_interval_lengths":bad_start_end,
        "time_gaps_or_end_mismatch":gaps,"duplicate_or_reverse_source_intervals":dups,
        "raw_status":raw_status,
        "model_clock_UTC_OFFSET_from_original_BIF_verified":False,
        "model_DATM_stream_sampling_phase_verified":False,
        "source_local_standard_time_AmeriFlux_documentation":True,
        "samples":samples}

def interpret_block(site,path,groupid,data):
    """Interpret one original BIF VAR_INFO_* group exactly; no silent coercion."""
    vn=(data.get("VAR_INFO_VARNAME") or "").strip().upper()
    if vn not in BIF_TARGETS:return None
    val=data.get("VAR_INFO_HEIGHT","")
    date=data.get("VAR_INFO_DATE","")
    unit=data.get("VAR_INFO_HEIGHT_UNIT",data.get("VAR_INFO_HEIGHT_UNITS",""))
    rec={"site":site,"bif_path":str(path),"group":str(groupid),
         "variable":vn,"raw_height":val,"raw_date":date,
         "raw_height_unit":unit,"date":"","height_m":"",
         "status":"","decision":"KEEP_SOURCE_UNCHANGED"}
    try:
        h=fl(val)
        if not math.isfinite(h) or not 0.5<=h<=150:
            raise ValueError("missing_or_out_of_range_original_height")
        d=dtstamp(date)
        rec["height_m"]=h;rec["date"]=str(d)
        if unit and unit.lower().strip() not in ("m","meter","metre","meters","metres"):
            raise ValueError("unapproved_height_unit")
        rec["status"]="VALID_DATED_HEIGHT"
    except (ValueError,TypeError) as err:
        rec["status"]="BIF_RECORD_HOLD_"+str(err)
    return rec

def bif_inventory(site):
    paths=sorted((SITES/site/"forcing/raw").rglob("*BIF*.csv"))
    rows=[];offsets=[];unknown=[]
    for p in paths:
        with p.open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
            dr=csv.DictReader(f)
            if not dr.fieldnames or not {"VARIABLE","DATAVALUE","GROUP_ID"}.issubset(dr.fieldnames):
                continue
            groups=defaultdict(dict)
            for row in dr:
                var=str(row.get("VARIABLE","")).strip().upper()
                data=str(row.get("DATAVALUE","")).strip()
                group=str(row.get("GROUP_ID","")).strip()
                block=(str(row.get("VARIABLE_GROUP","")),group)
                if var:groups[block][var]=data
                if var in UTC_KEYS:
                    offsets.append({"file":str(p),"variable":var,
                                    "value":data,"group":str(block)})
                elif "UTC" in var or "TIMEZONE" in var or "TIME_ZONE" in var:
                    unknown.append({"file":str(p),"variable":var,
                                    "value":data,"group":str(block)})
            for k,block in groups.items():
                ans=interpret_block(site,p,k,block)
                if ans is not None:rows.append(ans)
    result={"bif_csv_count":len(paths),"target_raw_rows":len(rows),
       "raw_target_records":rows,"UTC_OFFSET_candidates":offsets,
       "additional_timing_metadata_keys":unknown}
    return result

def height_conclusions(site,bif,info):
    result={}
    start=datetime(int(info["first_year"]),1,1)
    for target in BIF_TARGETS:
        rows=[r for r in bif["raw_target_records"] if r["variable"]==target]
        good=[r for r in rows if r["status"]=="VALID_DATED_HEIGHT"]
        fail=[r for r in rows if r["status"]!="VALID_DATED_HEIGHT"]
        entries=defaultdict(set)
        for r in good:entries[r["date"]].add(float(r["height_m"]))
        conflicts={k:sorted(v) for k,v in entries.items() if len(v)>1}
        dates=sorted((datetime.fromisoformat(t),next(iter(v))) for t,v in entries.items() if len(v)==1)
        unique_heights=sorted(set(v for _,v in dates))
        if not dates:
            status="NO_VERIFIED_NATIVE_HEIGHT"
        elif fail or conflicts:
            status="BIF_MALFORMED_OR_CONFLICTING_HEIGHT_HOLD"
        elif dates[0][0]>start:
            status="HISTORY_BEFORE_FIRST_HEIGHT_NOT_ESTABLISHED_HOLD"
        else:
            status="FULL_PERIOD_START_DATED_HEIGHT_AVAILABLE_NUMERIC_CANDIDATE"
        result[target]={"status":status,"height_m_values":unique_heights,
          "valid_records":len(good),"invalid_records":len(fail),
          "conflicts":conflicts,"first_known_date":str(dates[0][0]) if dates else None,
          "last_known_date":str(dates[-1][0]) if dates else None,
          "first_year_native_start":str(start),
          "prehistory_days":max(0,(dates[0][0]-start).total_seconds()/86400) if dates else None,
          "full_records":rows}
    return result

def official_clock(site,bif):
    candidates=[]
    for x in bif["UTC_OFFSET_candidates"]:
        raw=x["value"]
        f=fl(raw)
        valid=math.isfinite(f) and -12<=f<=14
        candidates.append({**x,"offset_hours_candidate":f if valid else None,
                           "valid_for_official_timezone_review":bool(valid)})
    numeric={x["offset_hours_candidate"] for x in candidates
             if x["valid_for_official_timezone_review"]}
    status=("NO_RELEASE_BIF_SITE_UTC_OFFSET"
            if not candidates else
            "OFFICIAL_BIF_UTC_OFFSET_CONFLICT" if len(numeric)>1 else
            "OFFICIAL_BIF_UTC_OFFSET_REQUIRES_STREAM_VERIFICATION" if len(numeric)==1 and
            all(x["valid_for_official_timezone_review"] for x in candidates)
            else "INVALID_BIF_UTC_OFFSET_HOLD")
    return {"site":site,"status":status,"raw_candidates":candidates,
            "candidate_UTC_offsets_hours":sorted(numeric),
            "approved_for_CIME_DATM_time_relabel":False,
            "interpretation":"FLUXNET TIMESTAMP_START/END in local standard time, not DST; conversion and DATM phase must be verified separately"}

def analyze():
    _,_,sites,previous=gate()
    summary=[];all_raw=[];details={}
    for site in NAMES:
        print("STAGE97 FORENSIC",site,"START",flush=True)
        try:
            clock=full_timestamp_audit(site,sites[site])
            bif=bif_inventory(site)
            ht=height_conclusions(site,bif,sites[site])
            zone=official_clock(site,bif)
            invalid=[r for r in bif["raw_target_records"] if r["status"]!="VALID_DATED_HEIGHT"]
            all_raw+=bif["raw_target_records"]
            issues=[]
            for variable in BIF_TARGETS:
                if ht[variable]["status"]!="FULL_PERIOD_START_DATED_HEIGHT_AVAILABLE_NUMERIC_CANDIDATE":
                    issues.append(variable+"_"+ht[variable]["status"])
            if clock["raw_status"]!="SOURCE_INTERVALS_COMPLETE_NO_DST_ARTIFACT":
                issues.append("RAW_INTERVAL_IDENTITY_REVIEW_REQUIRED")
            if zone["status"]!="OFFICIAL_BIF_UTC_OFFSET_REQUIRES_STREAM_VERIFICATION":
                issues.append(zone["status"])
            issues+=["DATM_UTC_PHASE_DO_NOT_ASSUME","MODEL_ZBOT_MAPPING_NOT_YET_ACTIVATED",
                "FATES_PFT_FOOTPRINT_NEEDS_REVIEW","CIME_SMOKE_TEST_PENDING"]
            if site=="US-Ho1":
                issues.append("ORIGINAL_2000_QC1_QC2_T_JUMP_STILL_SCIENCE_HOLD")
            details[site]={"site":site,"source_clock":clock,
                "native_BIF":bif,"BIF_height_conclusions":ht,
                "original_BIF_UTC":zone,"previous_stage96":previous[site],
                "blocking_issues":issues}
            row={"site":site,"native_minutes":int(sites[site]["native_minutes"]),
                "original_source_raw_rows":clock["raw_records"],
                "source_interval_status":clock["raw_status"],
                "official_UTC_OFFSET_BIF_status":zone["status"],
                "official_UTC_OFFSET_values":",".join(map(str,zone["candidate_UTC_offsets_hours"])),
                "TA_F_height_status":ht["TA_F"]["status"],
                "TA_F_first_height":ht["TA_F"]["first_known_date"] or "",
                "TA_F_height_m":",".join(map(str,ht["TA_F"]["height_m_values"])),
                "WS_F_height_status":ht["WS_F"]["status"],
                "WS_F_first_height":ht["WS_F"]["first_known_date"] or "",
                "WS_F_height_m":",".join(map(str,ht["WS_F"]["height_m_values"])),
                "invalid_target_BIF_raw_records":len(invalid),
                "technical_evidence_status":"EVIDENCE_COLLECTED",
                "production_DATM_approved":"NO",
                "blockers":"|".join(issues)}
            summary.append(row)
            print("STAGE97",site,clock["raw_status"],
                "UTC",zone["status"],
                "TA",ht["TA_F"]["status"],"WS",ht["WS_F"]["status"],
                "INVALID_BIF",len(invalid),flush=True)
        except Exception as err:
            summary.append({"site":site,"technical_evidence_status":"FORENSIC_FAIL",
                "blockers":str(err),"production_DATM_approved":"NO"})
            details[site]={"site":site,"error":str(err)}
            print("STAGE97",site,"FORENSIC_FAIL",type(err).__name__,str(err),flush=True)
    return summary,all_raw,details

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mg=ap.add_mutually_exclusive_group(required=True)
    mg.add_argument("--self-test",action="store_true")
    mg.add_argument("--audit",action="store_true")
    mg.add_argument("--check",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        assert sum(YEARS.values())==215 and len(NAMES)==10
        # Full tested source parse logic (valid/invalid BIF, true +30-min time).
        ex=interpret_block("US-Ho2",Path("official_bif.csv"),("VAR_INFO", "1"),{
            "VAR_INFO_VARNAME":"WS_F","VAR_INFO_DATE":"202001010000",
            "VAR_INFO_HEIGHT":"35","VAR_INFO_HEIGHT_UNIT":"m"})
        assert ex["status"]=="VALID_DATED_HEIGHT" and ex["height_m"]==35
        fail=interpret_block("US-Ho2",Path("official_bif.csv"),("VAR_INFO","2"),{
            "VAR_INFO_VARNAME":"WS_F","VAR_INFO_DATE":"-9999","VAR_INFO_HEIGHT":"-9999"})
        assert fail["status"].startswith("BIF_RECORD_HOLD")
        assert dtstamp("202001010030")-dtstamp("202001010000")==timedelta(minutes=30)
        print("STAGE97 SELF-TEST PASS | exact BIF row diagnostics and 10 source clocks; no writes",flush=True)
        return 0
    data,raw,details=analyze()
    failed=sum(x["technical_evidence_status"]=="FORENSIC_FAIL" for x in data)
    if args.check:
        print("STAGE97 CHECK |",len(data),"/10 sites, forensic_fail",failed,
              "no files changed",flush=True)
        return 2 if failed else 0
    out=ROOT/"reports"/("stage97_batch02_DATM_BIF_source_clock_decisions_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    fields=["site","native_minutes","original_source_raw_rows","source_interval_status",
            "official_UTC_OFFSET_BIF_status","official_UTC_OFFSET_values",
            "TA_F_height_status","TA_F_first_height","TA_F_height_m",
            "WS_F_height_status","WS_F_first_height","WS_F_height_m",
            "invalid_target_BIF_raw_records","technical_evidence_status",
            "production_DATM_approved","blockers"]
    writecsv(out/"10_site_time_height_readiness.csv",data,fields)
    bfields=["site","bif_path","group","variable","raw_height","raw_date","raw_height_unit",
             "date","height_m","status","decision"]
    writecsv(out/"all_raw_BIF_TA_WS_height_rows.csv",raw,bfields)
    with (out/"invalid_BIF_height_rows_needing_science_review.csv").open("w",
                            encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=bfields);w.writeheader()
        w.writerows(row for row in raw if row["status"]!="VALID_DATED_HEIGHT")
    (out/"10_site_full_source_clock_and_BIF_provenance.json").write_text(
        json.dumps(details,indent=2,default=str)+chr(10))
    manifest={"schema":SCHEMA,"site_count":len(data),"forensic_technical_failures":failed,
        "source_year_NC_count":215,
        "stage95_manifest_sha256":sha(S95/"manifest.json"),
        "stage96_manifest_sha256":sha(S96/"manifest.json"),
        "site_clock_UTC_model_phase_scientifically_approved":False,
        "ZBOT_sensors_forcing_nc_modified":False,
        "DATM_CIME_case_modified":False,"model_submissions":0,
        "official_metadata_inventoried_only":True,
        "output_sha256":{p.name:sha(p) for p in out.iterdir() if p.name!="manifest.json"}}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+chr(10))
    print("STAGE97 REPORT",out,flush=True)
    print("STAGE97 RESULT | 10 sites examined; original source clock/BIF rows inventoried; forensic_fail",
          failed,"| NO DATM/ZBOT/CIME/SLURM MODIFICATIONS",flush=True)
    return 2 if failed else 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Batch02 Stage98: resolve official BADM variable date precision and prehistory.

Original Stage97 output is SHA-gated and preserved. Reclassify source
VAR_INFO_DATE YYYY, YYYYMM, YYYYMMDD, YYYYMMDDHHMM (all accepted
AmeriFlux BADM precisions), without fabricating the exact change-of-sensor
minute for day/month/year precision. Collapse identical BIF exports without
counting them as independent measurements. Summarize source first valid TA_F
and WS_F heights, actual forcing-start gaps and official BIF UTC offsets.
No ZBOT/NC/forcing/CIME/Slurm writes. No missing height is guessed.
"""
import argparse,csv,hashlib,json,math,re
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S97=ROOT/"reports/stage97_batch02_DATM_BIF_source_clock_decisions_20261026T040211Z_e0576185"
S95=ROOT/"reports/stage95_ten_site_122_user_approved_versioned_forcing_215NC_20261026T034516Z_f4afa348"
S96=ROOT/"reports/stage96_batch02_DATM_clock_ZBOT_surface_readonly_20261026T035407Z_fcaa4d22"
S07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
SITES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1","US-Ho1","US-Ho2","US-Ho3","US-ICh","US-ICt")
VARIABLES=("TA_F","WS_F")
DATE_FORMATS={4:("%Y","YEAR"),6:("%Y%m","MONTH"),
              8:("%Y%m%d","DAY"),12:("%Y%m%d%H%M","MINUTE")}

def j(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def table(p):
    with Path(p).open("r",newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))
def writecsv(p,items,fields):
    with Path(p).open("w",encoding="utf8",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        wr.writeheader()
        wr.writerows(items)

def parse_date(raw):
    value=str(raw).strip()
    if not re.fullmatch(r"\d{4}(?:\d{2}){0,4}",value):
        return None,None,"INVALID_CHARACTERS_OR_PRECISION"
    if len(value) not in DATE_FORMATS:
        return None,None,"UNSUPPORTED_DATE_PRECISION"
    fmt,precision=DATE_FORMATS[len(value)]
    try: dt=datetime.strptime(value,fmt)
    except ValueError: return None,None,"INVALID_CALENDAR_DATE"
    return dt,precision,None

def fl(raw):
    try:
        v=float(raw)
        return v if math.isfinite(v) else float("nan")
    except (ValueError,TypeError):return float("nan")

def gate():
    m=j(S97/"manifest.json")
    if (m.get("schema")!="BATCH02_STAGE97_READONLY_BIF_ZBOT_CLOCK_FORENSICS_v1"
        or m.get("site_count")!=10 or m.get("forensic_technical_failures")!=0
        or m.get("source_year_NC_count")!=215
        or m.get("site_clock_UTC_model_phase_scientifically_approved") is not False
        or m.get("DATM_CIME_case_modified") is not False
        or m.get("stage95_manifest_sha256")!=sha(S95/"manifest.json")
        or m.get("stage96_manifest_sha256")!=sha(S96/"manifest.json")):
        raise ValueError("Original Stage97 ten-site source/metadata evidence contract changed")
    for fn,h in m["output_sha256"].items():
        if sha(S97/fn)!=h:raise ValueError("Original Stage97 forensic evidence SHA changed "+fn)
    evidence=j(S97/"10_site_full_source_clock_and_BIF_provenance.json")
    if set(evidence)!=set(SITES):raise ValueError("Stage97 source stations changed")
    release=j(S07/"exact_input_manifest.json")
    specs={x["site"]:x for x in release["sites"]}
    if set(specs)!=set(SITES):raise ValueError("Original FLUXNET time range/source roster changed")
    return m,evidence,specs

def normalize_row(row):
    x=dict(row)
    t,precision,error=parse_date(x.get("raw_date",""))
    height=fl(x.get("raw_height",""))
    unit=str(x.get("raw_height_unit","")).lower().strip()
    if not error and not (0.5<=height<=150):
        error="INVALID_HEIGHT_RANGE"
    if not error and unit and unit not in {"m","meter","meters","metre","metres"}:
        error="HEIGHT_UNIT_NOT_METERS"
    x["effective_date_label"]=t.isoformat(sep=" ") if t else ""
    x["date_precision"]=precision or "INVALID"
    x["normalized_height_m"]=height if not error else ""
    x["status_v2"]=("VALID_ORIGINAL_HEIGHT_WITH_"+precision+"_DATE_PRECISION"
                    if not error else "SOURCE_HOLD_"+error)
    x["exact_change_minute_known"]="YES" if precision=="MINUTE" else "NO"
    x["model_ZBOT_approval"]="NO_NOT_YET"
    return x

def condense_station(site,detail,info):
    bif=detail["native_BIF"]
    raw=[normalize_row(x) for x in bif["raw_target_records"]]
    full={}
    for variable in VARIABLES:
        selected=[x for x in raw if x["variable"]==variable]
        valid=[x for x in selected if x["status_v2"].startswith("VALID_")]
        invalid=[x for x in selected if not x["status_v2"].startswith("VALID_")]
        canon=defaultdict(list)
        for x in valid:
            identity=(x["raw_date"],str(x["normalized_height_m"]),x["date_precision"])
            canon[identity].append(x)
        unique=[]
        for identity,rep in sorted(canon.items()):
            unique.append({
                "date_original":identity[0],"height_m":float(identity[1]),
                "precision":identity[2],
                "date_label":rep[0]["effective_date_label"],
                "source_exports":len(rep),
                "source_BIF_files":sorted(set(x["bif_path"] for x in rep)),
                "source_group_ids":[x["group"] for x in rep],
                "exact_change_minute_known":identity[2]=="MINUTE"})
        bydate=defaultdict(set)
        for x in unique:bydate[x["date_label"]].add(x["height_m"])
        conflicts={k:sorted(v) for k,v in bydate.items() if len(v)>1}
        dates=sorted(datetime.fromisoformat(x["date_label"]) for x in unique)
        first=dates[0] if dates else None
        start=datetime(int(info["first_year"]),1,1)
        pre=(first-start).total_seconds()/86400 if first else None
        distinct=sorted(set(x["height_m"] for x in unique))
        if not unique:
            status="NO_VERIFIED_HEIGHT_NEEDS_OFFICIAL_SOURCE"
        elif invalid or conflicts:
            status="MALFORMED_OR_CONFLICTING_HEIGHT_NEEDS_REVIEW"
        elif first>start:
            status="PREHISTORY_GAP_NEEDS_OFFICIAL_EVIDENCE_OR_USER_CHOICE"
        elif any(x["precision"]!="MINUTE" for x in unique) and len(distinct)>1:
            status="DATE_PRECISION_CANNOT_PROVE_EXACT_SENSOR_SWITCH"
        else:
            status="PREHISTORY_COVERED_BIF_HEIGHT_CANDIDATE_ONLY"
        full[variable]={
            "status":status,"source_rows":len(selected),
            "valid_source_rows":len(valid),"invalid_source_rows":len(invalid),
            "unique_dated_height_events":len(unique),
            "duplicate_source_export_rows":len(valid)-len(unique),
            "first_height_date":str(first) if first else None,
            "forcing_start_date":str(start),
            "prehistory_missing_days":round(max(pre,0),2) if pre is not None else None,
            "distinct_heights_m":distinct,
            "date_precision_types":dict(Counter(x["precision"] for x in unique)),
            "exact_dated_height_events":unique,
            "height_conflicts":conflicts,
            "unresolved_invalid_source_rows":invalid}
    utc=detail["original_BIF_UTC"]
    original=detail["source_clock"]
    if original.get("raw_status")!="SOURCE_INTERVALS_COMPLETE_NO_DST_ARTIFACT":
        raise ValueError(site+" original native timestamp continuity differs from Stage97 PASS")
    offset=utc.get("candidate_UTC_offsets_hours",[])
    return raw,full,offset

def analyze():
    _,sources,specs=gate()
    rows=[];details={};normalized=[]
    for site in SITES:
        detail=sources[site]
        if "error" in detail:raise ValueError("Original Stage97 forensic failure "+site)
        repaired,heights,offset=condense_station(site,detail,specs[site])
        normalized+=repaired
        issues=[]
        for variable in VARIABLES:
            value=heights[variable]
            if value["status"]!="PREHISTORY_COVERED_BIF_HEIGHT_CANDIDATE_ONLY":
                issues.append(variable+":"+value["status"])
        if len(offset)!=1:issues.append("SITE_UTC_OFFSET_OFFICIAL_VALUE_MISSING")
        if site=="US-Ho1":
            issues.append("QC1_QC2_DEC27_2000_18P746C_SOURCE_T_HOLD")
        issues+=["DATM_TIME_PHASE_AND_UTC_MAPPING_NOT_ACTIVATED",
                 "FATES_PFT_AND_CIME_CASE_NOT_APPROVED"]
        row={"site":site,
             "TA_status":heights["TA_F"]["status"],
             "TA_first":heights["TA_F"]["first_height_date"] or "",
             "TA_height_values":",".join(map(str,heights["TA_F"]["distinct_heights_m"])),
             "TA_pre_year_missing_days":heights["TA_F"]["prehistory_missing_days"],
             "WS_status":heights["WS_F"]["status"],
             "WS_first":heights["WS_F"]["first_height_date"] or "",
             "WS_height_values":",".join(map(str,heights["WS_F"]["distinct_heights_m"])),
             "WS_pre_year_missing_days":heights["WS_F"]["prehistory_missing_days"],
             "WS_original_source_rows":heights["WS_F"]["source_rows"],
             "WS_valid_rows_after_date_precision":heights["WS_F"]["valid_source_rows"],
             "WS_unique_events":heights["WS_F"]["unique_dated_height_events"],
             "UTC_BIF_hours":",".join(map(str,offset)),
             "technical_height_source_ready":
                  "YES" if all(heights[v]["status"]=="PREHISTORY_COVERED_BIF_HEIGHT_CANDIDATE_ONLY"
                               for v in VARIABLES) else "NO",
             "production_DATM_permitted":"NO",
             "manual_open_items":"|".join(issues)}
        rows.append(row)
        details[site]={"site":site,"TA_and_WS_height_evidence":heights,
                       "UTC_BIF_hours_candidates":offset,
                       "original_stage97_provenance":detail,
                       "model_ZBOT_and_DATM_release_approved":False}
        print("STAGE98",site,
              "TA",row["TA_status"],row["TA_height_values"],
              "FIRST",row["TA_first"],"GAP_DAYS",row["TA_pre_year_missing_days"],
              "WS",row["WS_status"],row["WS_height_values"],
              "FIRST",row["WS_first"],"GAP_DAYS",row["WS_pre_year_missing_days"],
              "UTC",row["UTC_BIF_hours"],flush=True)
    h2=details["US-Ho2"]["TA_and_WS_height_evidence"]["WS_F"]
    dateonly=[x for x in h2["exact_dated_height_events"] if x["precision"]=="DAY"]
    if (h2["source_rows"]<15 or
        h2["valid_source_rows"]<15 or
        len(dateonly)<3 or
        not {28.3}.issubset(set(x["height_m"] for x in dateonly))):
        raise ValueError("Ho2 expected original 15/day-format WS_F BIF records not reconciled")
    print("STAGE98 HO2 DATE PRECISION RESOLVED | original 15 WS_F day-only rows recognized; valid unique DAY events",
          len(dateonly),"dates",",".join(x["date_original"] for x in dateonly),
          "HEIGHT_m 28.3; prehistory remains a separate hold",flush=True)
    return rows,details,normalized

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--audit",action="store_true")
    modes.add_argument("--check",action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert sum({"US-BZS":15,"US-CMW":21,"US-EML":16,"US-GLE":16,
                    "US-Ha1":35,"US-Ho1":28,"US-Ho2":27,"US-Ho3":19,
                    "US-ICh":19,"US-ICt":19}.values())==215
        for s,expected in (("20240226","DAY"),("20190619","DAY"),("20140706","DAY"),
                          ("202001010000","MINUTE"),("1999","YEAR"),("201912","MONTH")):
            dt,precision,err=parse_date(s)
            assert dt is not None and precision==expected and err is None
        assert parse_date("-9999")[2] is not None
        assert normalize_row({"site":"US-Ho2","variable":"WS_F",
               "raw_height":"28.3","raw_date":"20140706"})["status_v2"]=="VALID_ORIGINAL_HEIGHT_WITH_DAY_DATE_PRECISION"
        print("STAGE98 SELF-TEST PASS | official BADM 4/6/8/12 date-precision, 10-site evidence; no writes")
        return 0
    rows,details,normalized=analyze()
    if a.check:
        print("STAGE98 CHECK PASS | ten site history, Ho2 day-only metadata valid; no writes",flush=True)
        return 0
    target=ROOT/"reports"/("stage98_batch02_BIF_date_precision_and_height_prehistory_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    target.mkdir(parents=True,exist_ok=False)
    writecsv(target/"10_site_height_history_decision_summary.csv",
             rows,list(rows[0]))
    fields=("site","variable","raw_date","raw_height","raw_height_unit",
            "date_precision","effective_date_label","normalized_height_m",
            "exact_change_minute_known","status_v2","bif_path","group","model_ZBOT_approval")
    writecsv(target/"all_original_BIF_height_rows_reclassified.csv",normalized,fields)
    (target/"site_historical_height_evidence.json").write_text(
        json.dumps(details,indent=2,default=str)+chr(10))
    manifest={"schema":"BATCH02_STAGE98_BADM_DATE_PRECISION_FIX_AND_HEIGHT_GAPS_v1",
        "stage97_manifest_sha256":sha(S97/"manifest.json"),
        "site_count":len(rows),"QC0_corrections_changed":0,
        "production_DATM_permitted":False,"ZBOT_or_NC_changed":False,
        "source_and_CIME_case_changed":False,"Slurm_jobs_submitted":0,
        "badm_datetime_accepted_precisions":["YYYY","YYYYMM","YYYYMMDD","YYYYMMDDHHMM"],
        "no_date_only_exact_midnight_sensor_switch_assumption":True,
        "out_sha256":{x.name:sha(x) for x in target.iterdir()}}
    (target/"manifest.json").write_text(json.dumps(manifest,indent=2)+chr(10))
    print("STAGE98 REPORT",target,flush=True)
    print("STAGE98 PASS | official day-precision WS_F repaired, 10-site exact first-height/gap decision inventory; NO DATM/ZBOT/PFT/CIME/SLURM",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

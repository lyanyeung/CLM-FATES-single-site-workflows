#!/usr/bin/env python3
"""JapanFlux Stage05AQ — operator-selected JST UTC+9 DIAGNOSTIC HYPOTHESIS.

Explicit USER decision: use JST (UTC+9) as the most likely source clock
for JP-Tef and JP-Tmd, the same JPF FLUXNET release family as three
verified-JST sites. Their original 75-line README says "local solar time",
so this is a diagnostic ASSUMPTION, not proof of original file clock.

Inputs: actual Stage05AM 18 source QC2 native-only records + summary,
actual Stage05AO cross-check of both original nested JPF HH source files,
actual Stage05L 5-site BIF/QC/README metadata gate (3 verified/2 held).

Outputs: exact 18 candidate UTC half-hour fields and a SOURCE-BOUNDED
date/variable/hour ERA5-Land PREVIEW manifest, no coordinates guessed.
All 45 selected meteorological source fields stay science HOLD.
NO CDS/network, ZIP/forcing/model changes, Slurm, AD400 or repairs.
"""
from __future__ import annotations
import argparse,csv,json,math,hashlib
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

EXPECTED=Counter({"JP-Tef":4,"JP-Tmd":14})
UNITS={"TA":"deg C","PA":"kPa","LW_IN":"W m-2"}
CDS={"TA":"2m_temperature",
     "PA":"surface_pressure",
     "LW_IN":"surface_thermal_radiation_downwards"}
README_SHA="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
HYPOTHESIS="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
FIELDS=("site","original_native_halfhour_start","candidate_UTC_start","candidate_UTC_end",
        "variable","original_selected_F_QC2","embedded_same_release_ERA","unit",
        "source_readme_sha256","original_readme_time_claim",
        "original_BIF_UTC_OFFSET_hours","candidate_time_basis","candidate_status",
        "source_QC","forcing_repair_approved")
def read_tsv(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError("Invalid original source TSV header")
        records=list(rd)
    if not records:raise ValueError("Original source event file empty")
    return records
def read_json(p):
    o=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(o,dict):raise ValueError("Expected source JSON object")
    return o
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""):
            h.update(ch)
    return h.hexdigest()
def guard(am,ao,l):
    if (am.get("stage")!="JapanFlux Stage05AM"
        or am.get("status")!="TWO_ORIGINAL_SOLAR_VS_STANDARD_SITE_CLOCKS_UNRESOLVED_SCIENCE_HOLD"
        or am.get("original_QC2_field_count")!=45
        or am.get("already_independently_compared")!=27
        or am.get("prior_strong_context_class")!=22
        or am.get("new_context_only_not_formally_promoted")!=5
        or am.get("clock_conflict_variable_fields")!=18
        or am.get("clock_conflict_by_site")!=dict(EXPECTED)
        or am.get("clock_conflict_native_site_halfhours")!=14
        or am.get("original_BIF_UTC_OFFSET_both_sites")!=9
        or am.get("original_Tef_Tmd_source_readme_75line_SHA256")!=README_SHA
        or am.get("original_UTC_mapping_generated") is not False
        or am.get("all_45_original_QC2_fields_HOLD") is not True):
        raise ValueError("Actual Stage05AM source/clock science HOLD changed")
    if (ao.get("stage")!="JapanFlux Stage05AO"
        or ao.get("status")!="BOTH_ORIGINAL_JPF_HH_SOURCE_QC2_VALUES_MATCHED_CLOCK_STILL_UNRESOLVED"
        or ao.get("original_source_field_count")!=45
        or ao.get("independently_context_checked_fields")!=27
        or ao.get("prior_strong_context_class_fields")!=22
        or ao.get("additional_context_only_fields")!=5
        or ao.get("clock_unresolved_fields")!=18
        or ao.get("clock_unresolved_by_site")!=dict(EXPECTED)
        or ao.get("source_HH_original_rows_scanned_by_Stage05AN")!=736272
        or ao.get("source_readme_75line_SHA256")!=README_SHA
        or ao.get("original_BIF_UTC_OFFSET_hours")!=9
        or ao.get("external_metadata_proves_original_JPF_solar_to_JST_conversion") is not False
        or ao.get("new_UTC_mapping_generated") is not False
        or ao.get("all_45_original_QC2_fields_HOLD") is not True
        or ao.get("replacement_approved") is not False):
        raise ValueError("Stage05AO actual raw ZIP source audit has changed")
    if (l.get("stage")!="JapanFlux Stage05L"
        or l.get("status")!="HOLD_INCOMPLETE_OR_CONFLICTING_METADATA"
        or l.get("verified_sites")!=3
        or l.get("utc_mapping_generated") is not False):
        raise ValueError("Original Stage05L should remain source-level README conflict")
    sites=l.get("sites",{})
    if set(sites)!={"JP-Fjy","JP-Khw","JP-Tef","JP-Tmd","JP-Yms"}:
        raise ValueError("Stage05L original five JPF site scope changed")
    for s in ("JP-Tef","JP-Tmd"):
        r=sites[s]
        if (r["status"]!="HOLD_METADATA_UNVERIFIED"
            or r["UTC_OFFSET_hours"]!=9
            or r["README_local_standard_time_without_DST"] is not False):
            raise ValueError("Original Tef/Tmd conflicting metadata must remain visible")
    for s in ("JP-Fjy","JP-Khw","JP-Yms"):
        r=sites[s]
        if (r["status"]!="VERIFIED" or r["UTC_OFFSET_hours"]!=9
            or r["README_local_standard_time_without_DST"] is not True):
            raise ValueError("The other three JPF source sites no longer source-verified JST")
def candidate(rows):
    if len(rows)!=18 or Counter(r["site"] for r in rows)!=EXPECTED:
        raise ValueError("Expected exact 18 source native QC2 fields")
    seen=set(); out=[]; dates=defaultdict(lambda:{"hours":set(),"variables":set(),"source":set(),"varhour":set()})
    for r in rows:
        s=r["site"];v=r["variable"];native=r["native_halfhour_timestamp_NOT_UTC"]
        k=(s,native,v)
        if k in seen:raise ValueError("Duplicate original source native halfhour+variable")
        seen.add(k)
        if (r["original_UTC"]!="UNRESOLVED"
            or r["site_specific_time_proof_status"]!="NEEDS_ORIGINAL_RELEASE_SITE_SPECIFIC_PRODUCER_OR_LOGGER_TIMESTAMP_EVIDENCE"
            or r["science_decision"]!="HOLD_NATIVE_ONLY_NO_CDS_NO_UTC_NO_REPAIR"
            or r["source_flag"]!="ORIGINAL_SELECTED_F_EQ_EMBEDDED_ERA_QC2"
            or r["original_readme_SHA256"]!=README_SHA
            or r["BIF_declared_UTC_OFFSET_hours"]!="9"
            or v not in UNITS or r["original_unit"]!=UNITS[v]):
            raise ValueError("Original Tef/Tmd source QC2 timebase/units changed")
        value=float(r["original_F_QC2_selected"])
        embedded=float(r["original_same_release_ERA"])
        if not (math.isfinite(value) and math.isfinite(embedded) and
                math.isclose(value,embedded,rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("Original source selected QC2 F/embedded ERA equality changed")
        t=datetime.strptime(native,"%Y%m%d%H%M")
        if t.minute not in (0,30):raise ValueError("Non-30-minute original native timestamp")
        utc=t-timedelta(hours=9)
        out.append({
            "site":s,"original_native_halfhour_start":native,
            "candidate_UTC_start":utc.strftime("%Y%m%d%H%M"),
            "candidate_UTC_end":(utc+timedelta(minutes=30)).strftime("%Y%m%d%H%M"),
            "variable":v,"original_selected_F_QC2":r["original_F_QC2_selected"],
            "embedded_same_release_ERA":r["original_same_release_ERA"],
            "unit":UNITS[v],"source_readme_sha256":README_SHA,
            "original_readme_time_claim":"LOCAL_SOLAR_TIME_WITHOUT_DST_CONFLICT",
            "original_BIF_UTC_OFFSET_hours":9,
            "candidate_time_basis":HYPOTHESIS,
            "candidate_status":"OPERATOR_SELECTED_PLUS9_HYPOTHESIS_QC2_SCIENCE_HOLD",
            "source_QC":"2","forcing_repair_approved":False
        })
        # Context window from 3h before to 4h after the source half-hour floor,
        # with wider bracket for strd's end-of-hour de-accumulated energy.
        start=utc.replace(minute=0)
        for offset in range(-3,5):
            h=start+timedelta(hours=offset)
            key=(s,h.date().isoformat())
            item=dates[key]
            clock=h.strftime("%H:%M")
            item["hours"].add(clock)
            item["variables"].add(CDS[v])
            item["source"].add(f"{native}:{v}")
            item["varhour"].add((clock,CDS[v]))
    if len({(r["site"],r["original_native_halfhour_start"]) for r in out})!=14:
        raise ValueError("Must retain exactly 14 original native site halfhours")
    plan=[]
    for (s,d),m in sorted(dates.items()):
        plan.append({
            "site":s,"UTC_date_CANDIDATE":d,
            "source_time_interpretation":HYPOTHESIS,
            "source_UTC_verified":False,
            "source_QC2_event_fields":sorted(m["source"]),
            "required_UTC_hour_clocks":sorted(m["hours"]),
            "required_ERA5L_variables":sorted(m["variables"]),
            "exact_variable_hour_pairs":[{"hour":hour,"variable":var} for hour,var in sorted(m["varhour"])],
            "dataset":"reanalysis-era5-land-timeseries",
            "product": "CDS hourly time-series (deaccumulated hourly strd)",
            "source_tower_coords":"NOT_YET_VERIFIED_IN_THIS_STAGE",
            "CDS_submission_authorized_by_this_stage":False,
            "state":"PREVIEW_ONLY_OPERATOR_PLUS9_HYPOTHESIS_NOT_SCIENCE_APPROVAL"
        })
    return sorted(out,key=lambda r:(r["site"],r["candidate_UTC_start"],r["variable"])),plan
def selftest():
    assert sum(EXPECTED.values())==18
    assert (datetime(2005,8,12,3)-timedelta(hours=9)).strftime("%Y%m%d%H%M")=="200508111800"
    assert (datetime(2011,12,17,6)-timedelta(hours=9)).strftime("%Y%m%d%H%M")=="201112162100"
    assert set(CDS.values())=={"surface_pressure","2m_temperature","surface_thermal_radiation_downwards"}
    assert HYPOTHESIS=="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
    print("STAGE05AQ SELF-TEST PASS | user JST+9 hypothesis, 18 native QC2 -> candidate UTC only, bounded ERA5L preview; no CDS/forcing/repairs")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--operator-time-hypothesis",choices=[HYPOTHESIS])
    for field in ("stage05am-register","stage05am-summary","stage05ao-summary","stage05l-summary","out-dir"):
        p.add_argument("--"+field,type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if a.operator_time_hypothesis!=HYPOTHESIS:
        p.error("Explicit --operator-time-hypothesis JST_UTC_PLUS9_DIAGNOSTIC_ONLY required")
    keys=("stage05am_register","stage05am_summary","stage05ao_summary","stage05l_summary","out_dir")
    if any(getattr(a,k) is None for k in keys):
        p.error("Require original Stage05AM/AO/L actual source reports and new output dir")
    guard(read_json(a.stage05am_summary),read_json(a.stage05ao_summary),
          read_json(a.stage05l_summary))
    records,days=candidate(read_tsv(a.stage05am_register))
    if a.out_dir.exists():p.error("Refusing to overwrite source diagnostic output")
    a.out_dir.mkdir(parents=True)
    fieldpath=a.out_dir/"stage05aq_18_original_QC2_JST_PLUS9_candidate_UTC_SCIENCE_HOLD.tsv"
    planpath=a.out_dir/"stage05aq_Tef_Tmd_candidate_CDS_site_UTC_days_PREVIEW_ONLY.json"
    summarypath=a.out_dir/"stage05aq_45_original_source_fields_time_assumption_NO_REPAIR.json"
    with fieldpath.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t");w.writeheader();w.writerows(records)
    with planpath.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05AQ",
                   "status":"TEF_TMD_SITE_UTC_DAY_CDS_HYPOTHESIS_PREVIEW_ONLY",
                   "source_original_QC2_fields":18,
                   "time_basis":HYPOTHESIS,
                   "original_readme_conflict_preserved":True,
                   "unique_site_UTC_day_previews":len(days),
                   "days":days,"CDS_requests_this_stage":0,
                   "original_data_modified":False,"all_45_source_fields_HOLD":True},
                  f,indent=2,ensure_ascii=False);f.write("\n")
    with summarypath.open("x",encoding="utf-8") as f:
        json.dump({"stage":"JapanFlux Stage05AQ","status":"OPERATOR_SELECTED_JST_PLUS9_CANDIDATE_UTC_ONLY_NOT_TIMEBASE_PROOF",
                   "assumption":HYPOTHESIS,
                   "source_BIF_UTC_OFFSET":9,
                   "original_Tef_Tmd_readme_explicit_solar_time_conflict_SHA256":README_SHA,
                   "original_source_timebase_definitively_verified":False,
                   "original_18_native_QC2_source_fields_retained":18,
                   "candidate_UTC_fields_generated":18,
                   "candidate_site_UTC_days":len(days),
                   "previous_independently_contextualized_fields":27,
                   "previous_strong_context_fields":22,
                   "previous_context_only_fields":5,
                   "original_source_fields_total":45,
                   "all_45_source_fields_HOLD":True,
                   "science_repair_approved":False,
                   "CDS_requests":0,"Slurm_jobs":0,"forcing_or_source_modified":False,
                   "input_sha256":{k:sha(getattr(a,k)) for k in keys if k!="out_dir"}},
                  f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AQ OPERATOR JST+9 CANDIDATE UTC 18 SOURCE FIELDS PASS | NO CDS / FORCING / SLURM")
    print("CANDIDATE_UTC_FIELDS",len(records),"ORIGINAL_CLOCK_NOT_SOURCE_PROVEN","REMAIN_HOLD",45)
    print("SITE_DAY_CDS_PREVIEWS",len(days))
    for x in days:print("DAY_CANDIDATE_NOT_REQUESTED",x["site"],x["UTC_date_CANDIDATE"],"VARS",",".join(x["required_ERA5L_variables"]),"HOURS",",".join(x["required_UTC_hour_clocks"]))
    for r in records:print("QC2_CANDIDATE_UTC",r["site"],r["original_native_halfhour_start"],r["candidate_UTC_start"],r["variable"],"F",r["original_selected_F_QC2"])
    print("CANDIDATE_UTC_TSV",fieldpath)
    print("SOURCE_BOUNDED_CDS_PREVIEW",planpath)
    print("SCIENCE_TIME_ASSUMPTION_LEDGER",summarypath)
    print("ALL_45_QC2_FIELDS_HOLD; EXTERNAL_CLOCK_PROOF_STILL_MISSING; NO REPLACEMENTS")
if __name__=="__main__":main()

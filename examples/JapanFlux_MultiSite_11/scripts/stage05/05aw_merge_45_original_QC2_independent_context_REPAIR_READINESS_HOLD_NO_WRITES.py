#!/usr/bin/env python3
"""Stage05AW: exact 45 original selected F=embedded ERA QC2 source fields.
Merge observed actual Stage05AL (27 fields), Stage05AT (Tef2011 2),
Stage05AU (Tmd2005 8), Stage05AV (final Tef/Tmd 8) and original
Stage05AQ 18 native source records into one read-only SCIENCE HOLD ledger.

Gives source-vs-independent ERA5-Land conservative hourly envelope,
original source clock provenance and candidate repair FEASIBILITY route.
DOES NOT generate halfhour repair values, change original ZIP/forcing,
request CDS, submit Slurm, or change model. Distinguishes 22
source-proven-UTC strong-context from 23 CONTEXT_ONLY (five Yms + 18
operator JST+9 original solar-time README conflict). All 45 HOLD.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

SITES=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10,"JP-Tef":4,"JP-Tmd":14})
VARS=Counter({"PA":27,"TA":6,"LW_IN":12})
UNITS={"PA":"kPa","TA":"deg C","LW_IN":"W m-2"}
CLOCK="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
SOLAR_SHA="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
FIELDS=("site","native_source_halfhour_start","variable","original_source_F_QC2",
 "original_same_release_ERA","unit","original_QC","reference_candidate_UTC_start",
 "time_basis_provenance","source_clock_conflict","independent_ERA5L_hourly_min",
 "independent_ERA5L_hourly_max","outside_independent_hourly_envelope",
 "evidence_tier","original_source_validated",
 "repair_feasibility_next_step","candidate_replacement_value",
 "science_approval_status")
def js(path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict):raise ValueError("Expected science source JSON report")
    return d
def tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError("Missing/duplicate original ledger TSV column")
        rows=list(rd)
    if not rows:raise ValueError("Empty source data table")
    return rows
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def eq(x,y):
    return math.isclose(float(x),float(y),abs_tol=1e-6,rel_tol=1e-10)
def report_gates(al,at,au,av):
    if (al.get("stage")!="JapanFlux Stage05AL"
        or al.get("status")!="27_ORIGINAL_QC2_FIELDS_INDEPENDENT_CONTEXT_OUTSIDE_HOURLY_ENVELOPES_18_CLOCK_HOLD_NO_REPAIR"
        or al.get("original_selected_F_ERA_QC2_variable_fields")!=45
        or al.get("independently_hourly_context_reviewed_fields")!=27
        or al.get("independently_context_outside_fields")!=27
        or al.get("previously_strong_label_independent_context_fields")!=22
        or al.get("new_Stage05AK_context_only_not_strong_label_approved_fields")!=5
        or al.get("clock_unresolved_original_source_fields")!=18
        or al.get("all_45_original_source_fields_HOLD") is not True
        or al.get("physical_repair_values_approved") is not False):
        raise ValueError("Actual Stage05AL original 27-source evidence changed")
    if (at.get("stage")!="JapanFlux Stage05AT"
        or at.get("status")!="TWO_INDEPENDENT_CDS_DAY_STRD_REFERENCE_SOURCE_VALIDATED_TWO_ORIGINAL_LW_CONTEXT_ONLY"
        or at.get("original_source_JPF_QC2_field_count")!=2
        or at.get("both_QC2_fields_outside_8h_reference_envelope") is not True
        or at.get("source_time_hypothesis")!=CLOCK
        or at.get("original_source_timebase_proven") is not False
        or at.get("all_45_original_source_QC2_fields_HOLD") is not True
        or at.get("scientific_repair_values_approved") is not False):
        raise ValueError("Stage05AT actual two Tef source LW context changed")
    if (au.get("stage")!="JapanFlux Stage05AU"
        or au.get("status")!="TMD_2005_8_ORIGINAL_QC2_SOURCES_3_INDEPENDENT_CDS_VARIABLE_HOURLY_CONTEXT_ONLY"
        or au.get("original_source_QC2_fields_reviewed_this_stage")!=8
        or au.get("outside_context_count_new_Tmd")!=8
        or au.get("total_original_source_fields_independent_context_reviewed")!=37
        or au.get("original_source_fields_not_yet_compared")!=8
        or au.get("source_time_hypothesis")!=CLOCK
        or au.get("all_45_original_QC2_source_fields_HOLD") is not True
        or au.get("scientific_30min_repair_values_approved") is not False):
        raise ValueError("Stage05AU actual eight Tmd2005 source fields changed")
    if (av.get("stage")!="JapanFlux Stage05AV"
        or av.get("status")!="EIGHT_REMAINING_SOURCE_QC2_INDEPENDENT_GRID_HOURLY_CONTEXT_REVIEWED_NOT_REPAIRED"
        or av.get("prior_original_source_QC2_fields_independently_context_reviewed")!=37
        or av.get("remaining_original_source_fields_context_reviewed_this_stage")!=8
        or av.get("total_original_source_fields_with_independent_context")!=45
        or av.get("prior_source_verified_strong_class")!=22
        or av.get("source_context_only_but_not_strong_auto_approved")!=23
        or av.get("remaining_8_outside_reference_count")!=8
        or av.get("source_UTC_time_verified_for_original_Tef_Tmd") is not False
        or av.get("time_basis")!=CLOCK
        or av.get("original_readme_local_solar_conflict_SHA256")!=SOLAR_SHA
        or av.get("original_source_fields_science_HOLD")!=45
        or av.get("original_source_field_repair_values_approved")!=0
        or av.get("original_source_ZIP_forcing_model_modified") is not False):
        raise ValueError("Stage05AV actual 45 source evidence/HOLD status changed")
def emit(site,native,var,x,y,utc,lo,hi,tier,clock):
    if site not in SITES or var not in UNITS:
        raise ValueError("Original JPF site/field not in source QC2 scope")
    x=float(x);y=float(y);lo=float(lo);hi=float(hi)
    dt=datetime.strptime(native,"%Y%m%d%H%M")
    dtutc=datetime.strptime(utc,"%Y%m%d%H%M")
    if (not eq(x,y) or not all(math.isfinite(v) for v in (x,y,lo,hi))
        or lo>hi or lo<=x<=hi or dt-dtutc!=timedelta(hours=9)
        or dt.minute not in (0,30)):
        raise ValueError("Source field F=ERA, UTC+9 or independent hourly envelope changed")
    if (clock=="ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED" and site not in ("JP-Fjy","JP-Khw","JP-Yms")) or (
        clock=="OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT" and site not in ("JP-Tef","JP-Tmd")):
        raise ValueError("Different source-clock science provenance mislabelled")
    return {"site":site,"native_source_halfhour_start":native,"variable":var,
       "original_source_F_QC2":x,"original_same_release_ERA":y,
       "unit":UNITS[var],"original_QC":"2",
       "reference_candidate_UTC_start":utc,
       "time_basis_provenance":clock,
       "source_clock_conflict":clock.startswith("OPERATOR"),
       "independent_ERA5L_hourly_min":lo,
       "independent_ERA5L_hourly_max":hi,
       "outside_independent_hourly_envelope":True,
       "evidence_tier":tier,
       "original_source_validated":True,
       "repair_feasibility_next_step":"AUDIT_ORIGINAL_SAME_VARIABLE_QC0_QC1_NEIGHBOR_HALF_HOURS_AND_PHYSICAL_JOIN_BEFORE_SHADOW_CANDIDATE",
       "candidate_replacement_value":"NOT_ESTIMATED",
       "science_approval_status":"HOLD_NO_APPROVED_30MIN_REPLACEMENT"}
def merge(alrows,aqrows,at,au,av):
    if len(alrows)!=27 or Counter(r["site"] for r in alrows)!=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10}):
        raise ValueError("Original Stage05AL verified UTC source field scope changed")
    if len(aqrows)!=18 or Counter(r["site"] for r in aqrows)!=Counter({"JP-Tef":4,"JP-Tmd":14}):
        raise ValueError("Original Stage05AQ 18 user-JST native QC2 source fields changed")
    registry={}
    for r in aqrows:
        key=(r["site"],r["original_native_halfhour_start"],r["variable"])
        if (key in registry
            or r["candidate_time_basis"]!=CLOCK
            or r["candidate_status"]!="OPERATOR_SELECTED_PLUS9_HYPOTHESIS_QC2_SCIENCE_HOLD"
            or r["original_readme_time_claim"]!="LOCAL_SOLAR_TIME_WITHOUT_DST_CONFLICT"
            or r["source_readme_sha256"]!=SOLAR_SHA
            or r["source_QC"]!="2"
            or r["forcing_repair_approved"]!="False"):
            raise ValueError("Original 18-field native source selected QC2 clock evidence changed")
        registry[key]=r
    entries={}
    for r in alrows:
        if (r["original_source_QC"]!="2" or r["repair_approval_status"]!="HOLD_NO_APPROVED_HALF_HOUR_REPLACEMENT"
            or str(r["context_outside"])!="1"
            or not eq(r["original_F_selected"],r["original_ERA_same_release"])):
            raise ValueError("AL original F=ERA/QC2 or science HOLD changed")
        tier=r["independent_context_evidence_tier"]
        if tier=="PRIOR_STAGE05AH_STRONG_CONTEXT":
            label="STRONG_CONTEXT_PREVIOUS_CLASS"
        elif tier=="STAGE05AK_CONTEXT_ONLY_NOT_YET_STRONG_LABEL_APPROVED":
            label="CONTEXT_ONLY_SOURCE_VERIFIED_JST"
        else:raise ValueError("Unknown old source evidence class: "+tier)
        utc=datetime.strptime(r["verified_source_UTC_start"],"%Y-%m-%dT%H:%MZ").strftime("%Y%m%d%H%M")
        row=emit(r["site"],r["native_halfhour_start"],r["variable"],
          r["original_F_selected"],r["original_ERA_same_release"],utc,
          r["independent_ERA5L_hourly_context_min"],
          r["independent_ERA5L_hourly_context_max"],label,
          "ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED")
        if r["unit"]!=row["unit"]:raise ValueError("Original AL source units changed")
        key=r["site"],r["native_halfhour_start"],r["variable"]
        if key in entries:raise ValueError("Original AL source duplicate")
        entries[key]=row
    def add(site,native,var,x,utc,lo,hi,tier):
        key=site,native,var
        if key not in registry or key in entries:raise ValueError("Duplicate/missing original user-JST QC2 field "+str(key))
        src=registry[key]
        if (src["candidate_UTC_start"]!=utc
            or src["unit"]!=UNITS[var]
            or not eq(src["original_selected_F_QC2"],x)
            or not eq(src["embedded_same_release_ERA"],x)):
            raise ValueError("Source selected original QC2 field differs from actual independent context report")
        entries[key]=emit(site,native,var,x,src["embedded_same_release_ERA"],utc,lo,hi,tier,
            "OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT")
    tef=at.get("original_source_two_fields",[])
    if len(tef)!=2:raise ValueError("Stage05AT JP-Tef Dec2011 context incomplete")
    for x in tef:
        if (x["site"]!="JP-Tef" or x["science_status"]!="HOLD_CONTEXT_ONLY_NO_STRONG_CLASS_AUTO_APPROVAL"
            or x["outside_conservative_8h_hourly_envelope"] is not True):
            raise ValueError("Previous Tef Dec2011 source QC2 CONTEXT_ONLY evidence changed")
        add("JP-Tef",x["native_JPF_start"],"LW_IN",x["original_LW_IN_F_QC2_W_m2"],
            x["candidate_UTC_start_JST_plus9"],
            x["nearby_independent_8h_min_W_m2"],x["nearby_independent_8h_max_W_m2"],
            "CONTEXT_ONLY_OPERATOR_JST_HYPOTHESIS")
    tmd=au.get("original_Tmd_2005_source_fields",[])
    if len(tmd)!=8:raise ValueError("Actual Tmd2005 source field context not eight")
    for x in tmd:
        if (x["site"]!="JP-Tmd" or x["outside_9h_reference_envelope"] is not True
            or x["evidence_label"]!="HOLD_CONTEXT_ONLY_OPERATOR_JST9_SOURCE_SOLAR_README_CONFLICT"
            or x["repair_approved"] is not False):
            raise ValueError("Stage05AU original Tmd 2005 source context changed")
        add("JP-Tmd",x["original_native_start"],x["variable"],
            x["source_original_selected_F_QC2"],x["candidate_UTC_start"],
            x["independent_hourly_context_min"],x["independent_hourly_context_max"],
            "CONTEXT_ONLY_OPERATOR_JST_HYPOTHESIS")
    last=av.get("remaining_8_original_source_QC2_event_comparisons",[])
    if len(last)!=8:raise ValueError("Actual last eight source context events missing")
    for x in last:
        if (x["outside_broad_hourly_reference"] is not True
            or x["science_status"]!="HOLD_CONTEXT_ONLY_NOT_REPLACEMENT"
            or x["repair_approved"] is not False):
            raise ValueError("Stage05AV final source context flags altered")
        add(x["site"],x["native_JPF_source_start"],x["variable"],
            x["original_F_QC2"],x["hypothetical_JSTminus9_UTC_start"],
            x["hourly_reference_min"],x["hourly_reference_max"],
            "CONTEXT_ONLY_OPERATOR_JST_HYPOTHESIS")
    if (len(entries)!=45 or Counter(x[0] for x in entries)!=SITES
        or Counter(x[2] for x in entries)!=VARS
        or len({(s,t) for s,t,v in entries})!=35
        or set(registry)!={k for k in entries if k[0] in ("JP-Tef","JP-Tmd")}
        or Counter(x["evidence_tier"] for x in entries.values())!=Counter({
            "STRONG_CONTEXT_PREVIOUS_CLASS":22,
            "CONTEXT_ONLY_SOURCE_VERIFIED_JST":5,
            "CONTEXT_ONLY_OPERATOR_JST_HYPOTHESIS":18})):
        raise ValueError("Unified source 45 fields /35 site-native timestamps/22+5+18 tiers not conserved")
    return sorted(entries.values(),key=lambda r:(r["site"],r["native_source_halfhour_start"],r["variable"]))
def selftest():
    assert sum(SITES.values())==45 and sum(VARS.values())==45
    assert len(UNITS)==3
    assert emit("JP-Tmd","200508120300","PA",0,0,"200508111800",99,100,
                "CONTEXT_ONLY_OPERATOR_JST_HYPOTHESIS",
                "OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT")["outside_independent_hourly_envelope"] is True
    assert emit("JP-Fjy","201112170700","PA",0,0,"201112162200",99,100,
                "STRONG_CONTEXT_PREVIOUS_CLASS",
                "ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED")["candidate_replacement_value"]=="NOT_ESTIMATED"
    try:
        emit("JP-Tmd","200508120300","PA",99,99,"200508111800",99,100,
             "CONTEXT_ONLY_OPERATOR_JST_HYPOTHESIS",
             "OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT")
    except ValueError:pass
    else:raise AssertionError("Must reject a source value within independent reference")
    print("STAGE05AW SELF-TEST PASS | exact original 45 QC2 variable fields, 35 site-native times, 22 strong+23 context, no repair values/writes")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    for key in ("stage05al-fields","stage05al-summary","stage05aq-fields",
                "stage05at-tef-summary","stage05au-tmd-summary",
                "stage05av-final-summary","out-dir"):
        p.add_argument("--"+key,type=Path)
    a=p.parse_args()
    keys=("stage05al_fields","stage05al_summary","stage05aq_fields",
          "stage05at_tef_summary","stage05au_tmd_summary",
          "stage05av_final_summary","out_dir")
    if a.self_test:selftest();return
    if any(getattr(a,k) is None for k in keys):
        p.error("Require Stage05AL 27 actual fields+summary, AQ original 18, AT2, AU8, AV8 real science reports and fresh derived outdir")
    al=js(a.stage05al_summary);at=js(a.stage05at_tef_summary)
    au=js(a.stage05au_tmd_summary);av=js(a.stage05av_final_summary)
    report_gates(al,at,au,av)
    allrows=merge(tsv(a.stage05al_fields),tsv(a.stage05aq_fields),at,au,av)
    if a.out_dir.exists():p.error("Refuse overwrite of science source evidence directory")
    a.out_dir.mkdir(parents=True)
    tab=a.out_dir/"stage05aw_45_original_JPF_F_ERA_QC2_source_vs_ERA5L_independent_context_ALL_HOLD.tsv"
    summary=a.out_dir/"stage05aw_45_original_JPF_QC2_35_source_native_times_REPAIR_READINESS_NOT_APPROVED.json"
    with tab.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t")
        w.writeheader();w.writerows(allrows)
    rec={
      "stage":"JapanFlux Stage05AW",
      "status":"ALL_45_ORIGINAL_QC2_INDEPENDENT_HOURLY_SOURCE_CONTEXT_RECONCILED_REPAIRS_UNAPPROVED",
      "original_source_selected_F_equals_same_release_ERA_QC2_variable_fields":45,
      "original_distinct_site_native_halfhours":35,
      "original_sites_by_field_count":dict(SITES),
      "original_variables_by_field_count":dict(VARS),
      "independent_context_compared_fields":45,
      "independent_context_outside_fields":45,
      "original_source_verified_JST_strong_context_fields":22,
      "original_source_verified_JST_context_only_fields":5,
      "operator_assumed_JST_source_README_solar_time_conflict_context_only_fields":18,
      "model_grid_hourly_context_not_30min_tower_reconstruction":True,
      "original_readme_solar_time_SHA256":SOLAR_SHA,
      "repair_eligibility":"NEIGHBOR_QC0_QC1_AND_PHYSCONTINUITY_NOT_YET_AUDITED",
      "science_approved_30min_replacement_values":0,
      "all_45_original_source_fields_HOLD":True,
      "original_source_ZIP_or_model_forcing_modified":False,
      "CDS_requests_this_stage":0,"Slurm_jobs":0,
      "next_action":"STAGE05AX_READ_ONLY_ORIGINAL_SELECTED_F_MDS_ERA_QC_2H_NEIGHBOR_CONTEXT",
      "input_sha256":{key:sha(getattr(a,key)) for key in keys if key!="out_dir"}
    }
    with summary.open("x",encoding="utf-8") as f:
        json.dump(rec,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AW 45 ORIGINAL JPF SELECTED F=ERA QC2 VS INDEPENDENT HOURLY ERA5L SOURCE EVIDENCE RECONCILED PASS | NO REPAIR")
    print("ORIGINAL_SOURCE_FIELD_COVERAGE 45 /45","DISTINCT_SITE_NATIVE_HALF_HOURS",35)
    print("EVIDENCE_TIERS 22 PRIOR_STRONG_CONTEXT + 5 SOURCE_JST_CONTEXT_ONLY + 18 OPERATOR_JST_CONTEXT_ONLY")
    print("ORIGINAL_SOURCE_SITES",dict(SITES),"VARIABLES",dict(VARS))
    print("INDEPENDENT_REFERENCE_OUTSIDE_ALL_45",all(r["outside_independent_hourly_envelope"] for r in allrows))
    print("UNIFIED_45_SOURCE_HOLD_TABLE",tab)
    print("REPAIR_READINESS_SUMMARY",summary)
    print("NEXT_ORIGINAL_QC0_QC1_NEIGHBOR_REVIEW_ONLY; ALL_45_SOURCE_FIELDS_HOLD; NO FORCING/MODEL/SLURM")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Batch03 Stage13d: ONE-SHOT science-gate continuation after operator's
approval of EXACT six existing source-T QC0 short-gap interpolations.

This script NEVER edits the original tower, standalone ERA5, Stage07
candidate, site surfaces, PFT fractions, clocks, case, CIME/DATM, or Slurm.
--check: all input verification + grouped science audit; NO OUTPUT FILES.
--run: same + isolated versioned SHA-receipted report only.

The six approved TA edits are scoped to six exact native timestamps and
numeric values. All other changed meteorological variables, US-Mpj / US-NC2
manual VPD review, US-NC2 2025 clock/ERA source issues, and site PFT/ZBOT
remain separately subject to scientific approval.
"""
import argparse,csv,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np

sys.dont_write_bytecode=True
VER="batch03-stage13d-v1-20261026-six-approved-QC0-postv5-gate"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13B=ROOT/"reports/stage13b_THREE_NUMERIC_SITES_QC0_AND_MANUAL_DECISIONS_20261026T170134Z_06af8b8e"
S13C=ROOT/"reports/stage13c_24_manual_original_tower_ERA_TA_context_20261026T171801Z_bed5a936"
S13A=ROOT/"reports/stage13a_Batch03_NINE_SITE_FORCING_ADMISSION_20261026T163725Z_cc70d4c8"
SITE_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITE_YEARS={"US-MOz":(2004,2021),"US-Mpj":(2008,2025),"US-NC2":(2005,2025)}
APPROVED=[
 ("US-MOz","2016-03-17T22:00:00",-15.213,12.1715,9.601),
 ("US-Mpj","2020-02-11T06:30:00",-17.667,1.1795,-3.869),
 ("US-NC2","2019-01-03T13:00:00",-6.759,13.3525,12.537),
 ("US-NC2","2019-01-04T03:30:00",-14.342,9.3935,9.524),
 ("US-NC2","2019-01-04T16:30:00",-13.804,9.5665,11.016),
 ("US-NC2","2019-01-08T03:30:00",-11.506,7.5215,10.410),
]
REQUIRED_MET=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")
FILES13B=("THREE_numeric_site_exact_six_original_QC0_edits_TO_DECIDE.csv",
          "THREE_site_all_original_manual_review_records_TO_DECIDE.csv")
FILES13C=("SIX_QC0_temperature_events_full_2h_before_after_tower_ERA5.csv",
          "EIGHTEEN_VPD_review_events_full_2h_before_after_tower_ERA5.csv",
          "ALL_24_review_center_tower_ERA5_T_and_VPD_summary.csv")

def valid(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing or symlink evidence: "+str(p))
    return p

def digest(p):
    h=hashlib.sha256()
    with valid(p).open("rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def event_key(site,time):
    return str(site)+"|"+pd.Timestamp(time).strftime("%Y-%m-%dT%H:%M:%S")

def selftest():
    assert len(APPROVED)==6 and len({event_key(x[0],x[1]) for x in APPROVED})==6
    assert {x[0] for x in APPROVED}==set(SITE_YEARS)
    assert all(np.isfinite(x[2:]).all() for x in APPROVED)
    assert event_key("US-MOz","2016-03-17 22:00")=="US-MOz|2016-03-17T22:00:00"
    print("STAGE13D SELF-TEST PASS | exactly six operator-approved QC0 temperatures; NO WRITES",flush=True)

def approved_receipt(path):
    r=json.loads(valid(path).read_text())
    if (r.get("schema")!="batch03-stage13d-qc0-operator-approval-v1" or
        r.get("decision_date")!="2026-10-26" or
        r.get("restrictions",{}).get("original_tower_files_must_remain_unchanged") is not True or
        r.get("restrictions",{}).get("DATM_ready") is not False or
        r.get("restrictions",{}).get("spinup_authorized") is not False):
        raise RuntimeError("Operator decision scope not the pinned six specific QC0 changes")
    arr=r.get("six_approved_specific_events",[])
    exp={event_key(a,b):(c,d,e) for a,b,c,d,e in APPROVED}
    if len(arr)!=6 or len({event_key(x["site"],x["native_time"]) for x in arr})!=6:
        raise RuntimeError("Approval contains missing/duplicate source time")
    for x in arr:
        if (x.get("variable")!="TA_F" or x.get("source_original_QC")!=0 or
            x.get("source_method")!="existing_stage07_local_short_interpolation" or
            x.get("decision")!="APPROVED_QC0_REPLACEMENT_ONLY"):
            raise RuntimeError("Approval scopes extra variable, QC or model state")
        vals=(x.get("original_tower_TA_C"),x.get("approved_selected_TA_C"),
              x.get("standalone_ERA5_TA_reference_C"))
        want=exp.get(event_key(x["site"],x["native_time"]))
        if want is None or not np.allclose(vals,want,rtol=0,atol=1e-9):
            raise RuntimeError("Operator approved event or physical value changed")
    return r

def provenance(decision):
    b=json.loads(valid(S13B/"stage13b_three_site_decision_SHA_receipt.json").read_text())
    c=json.loads(valid(S13C/"stage13c_24_manual_original_temperature_context_SHA_receipt.json").read_text())
    if b.get("qc0_rows")!=6 or b.get("total_manual_ledger_records")!=18 or \
       c.get("source_QC0_T_events")!=6 or c.get("source_manual_VPD_events")!=18:
        raise RuntimeError("Prior independent manual science count changed")
    if b.get("all_original_QC0_and_manual_science_approved") is not False:
        raise RuntimeError("Original historical Stage13b trial incorrectly changed into postv5")
    if b.get("DATM_ready") is not False or c.get("DATM_ready") is not False:
        raise RuntimeError("Original source trial unexpectedly marked DATM-ready")
    for name in FILES13B:
        if digest(S13B/name)!=b.get("output_SHA256",{}).get(name):
            raise RuntimeError("Stage13b signed source QC0/manual ledger changed: "+name)
    for name in FILES13C:
        if digest(S13C/name)!=c.get("output_SHA256",{}).get(name):
            raise RuntimeError("Stage13c signed original temperature context changed: "+name)
    if c.get("source_stage13b_SHA256")!=digest(
        S13B/"stage13b_three_site_decision_SHA_receipt.json"):
        raise RuntimeError("Stage13c source provenance does not match Stage13b signed receipt")
    s07=json.loads(valid(S07/"output_sha256.json").read_text())
    manifest=json.loads(valid(S07/"exact_input_manifest.json").read_text())
    if b.get("source_Stage07_output_SHA256_manifest")!=digest(S07/"output_sha256.json"):
        raise RuntimeError("Stage13b originally pinned Stage07 output has changed")
    if c.get("source_stage07_exact_manifest_SHA256")!=digest(S07/"exact_input_manifest.json"):
        raise RuntimeError("Stage13c exact source manifest changed")
    m={spec["site"]:spec for spec in manifest["sites"]}
    if len(m)!=10 or not set(SITE_YEARS).issubset(m):
        raise RuntimeError("Stage07 source manifest changed")
    source={str(Path(k).resolve()):v for k,v in manifest["input_sha256"].items()}
    return b,c,s07,m,source

def runaudit(decision):
    receipt=approved_receipt(decision)
    b,c,outputsha,specs,sources=provenance(decision)
    qc0=pd.read_csv(valid(S13B/FILES13B[0]),dtype={"time":str})
    man=pd.read_csv(valid(S13B/FILES13B[1]),dtype={"time":str})
    rawct=pd.read_csv(valid(S13C/FILES13C[2]),dtype={"time":str})
    old9=pd.read_csv(valid(S13A/"Batch03_nine_site_forcing_admission_readonly.csv"))
    if len(qc0)!=6 or len(man)!=18 or len(rawct)!=24 or len(old9)!=9:
        raise RuntimeError("Original verified manual center or nine-site source status changed")
    if not (old9.loc[old9.site.isin(SITE_YEARS),"numeric_selected_candidate_screen"]==
            "CURRENT_NUMERIC_FIELDS_PASS_ONLY").all():
        raise RuntimeError("Three Stage13a selected numeric candidates did not pass")
    sites,edits,vpd,heights,surface_records=[],[],[],[],[]
    for site,(first,last) in SITE_YEARS.items():
        spec=specs[site]
        if int(spec["native_minutes"])!=30:
            raise RuntimeError("Wrong original native 30 min source cadence "+site)
        for kind in ("primary","era"):
            p=valid(spec[kind])
            if digest(p)!=sources.get(str(p.resolve())):
                raise RuntimeError("Source originally pinned raw tower/ERA SHA mismatch "+site)
        qc=S07/site/"forcing"/"qc_v5"
        target=S07/site/"forcing"/"processed_v5"/(
          f"{site}_CLM_forcing_{first}_{last}.csv")
        needed=[qc/f"{site}_replacement_events.csv",
                qc/f"{site}_manual_review.csv",
                qc/f"{site}_independent_audit.json",
                target]
        for p in needed:
            if digest(p)!=outputsha.get(str(p.relative_to(S07))):
                raise RuntimeError("Stage07 signed output altered: "+str(p))
        changes=pd.read_csv(needed[0],dtype={"time":str},low_memory=False)
        review=pd.read_csv(needed[1],dtype={"time":str},low_memory=False)
        audit=json.loads(needed[2].read_text())
        if audit.get("site")!=site or audit.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
            raise RuntimeError("Independent Stage07 candidate audit changed "+site)
        if (len(review)!=len(man.loc[man.site.eq(site)]) or
            len(review)!=int(audit["manual_review_records"])):
            raise RuntimeError("Original source manual review counts do not agree "+site)
        approval_subset=[x for x in APPROVED if x[0]==site]
        approvedkeys={event_key(x[0],x[1]):x for x in approval_subset}
        selected_qc0=changes.loc[pd.to_numeric(changes.official_qc,errors="coerce").eq(0)]
        if len(selected_qc0)!=len(approvedkeys):
            raise RuntimeError("Signed source QC0 record count differs from 6 approved ones: "+site)
        for x in selected_qc0.to_dict("records"):
            key=event_key(site,x["time"])
            exp=approvedkeys.get(key)
            if exp is None or x.get("variable")!="TA_F":
                raise RuntimeError("Original QC0 approval invalid variable or source event")
            for column,value in (("original_value",exp[2]),
                                 ("final_value",exp[3]),
                                 ("era_reference",exp[4])):
                if not np.isclose(float(x[column]),value,atol=1e-8,rtol=0):
                    raise RuntimeError("Signed original QC0 actual value not equal approved value: "+key)
            edits.append({
                "site":site,"time":key.split("|")[1],"variable":"TA_F",
                "original_measured_QC0_tower_TA_C":exp[2],
                "approved_stage07_interpolated_TA_C":exp[3],
                "independent_ERA_TA_C":exp[4],
                "decision":"OPERATOR_APPROVED_THIS_EXACT_CHANGE",
                "original_source_changed":False,
            })
        numeric=pd.read_csv(target,usecols=["time",*REQUIRED_MET],low_memory=False)
        met=numeric[list(REQUIRED_MET)].apply(pd.to_numeric,errors="coerce")
        miss=int((~np.isfinite(met.to_numpy(dtype=float)).all(axis=1)).sum())
        if miss:
            raise RuntimeError("Selected numeric candidate now contains missing required values "+site)
        if not np.isclose(numeric.TBOT,numeric.TA_USE+273.15,rtol=1e-10,atol=1e-9).all():
            raise RuntimeError("Candidate TBOT/TA source pair no longer consistent "+site)
        # The same independent water-RH validity already passed Stage13a.
        physically=old9.loc[old9.site.eq(site)].iloc[0]
        if int(physically["candidate_physically_invalid_HH"])!=0 or \
           int(physically["candidate_missing_any_required_met_HH"])!=0:
            raise RuntimeError("Stage13a source physical validity changed "+site)
        candidate_time=pd.to_datetime(numeric.time,errors="raise")
        if candidate_time.isna().any() or candidate_time.duplicated().any() or \
           len(numeric)!=int(audit["noleap_rows"]):
            raise RuntimeError("Stage07 source-native selected model forcing time mismatch "+site)
        changed_count=int(len(changes))
        manual_changed=0
        manual_unchanged=0
        for obj in review.to_dict("records"):
            if obj.get("variable")!="VPD_F":
                raise RuntimeError("New manual review variable outside original VPD scope "+site)
            key=event_key(site,obj["time"])
            center=rawct.loc[(rawct.site==site)&
                         (pd.to_datetime(rawct.time).dt.strftime("%Y-%m-%dT%H:%M:%S")==
                          key.split("|")[1])&
                         (rawct.event_kind=="VPD_MANUAL_REVIEW")]
            if len(center)!=1:
                raise RuntimeError("Missing 24-center science provenance for source VPD "+key)
            original=float(center.iloc[0].tower_VPD_center_hPa)
            selected=float(center.iloc[0].candidate_VPD_center_hPa)
            altered=bool(not np.isclose(original,selected,rtol=0,atol=1e-9))
            manual_changed+=int(altered)
            manual_unchanged+=int(not altered)
            vpd.append({
              "site":site,"time":key.split("|")[1],
              "original_tower_VPD_hPa":original,
              "stage07_selected_VPD_hPa":selected,
              "changed":altered,"manual_reason":obj.get("reason",""),
              "operator_approved":False,
              "status":"HOLD_REPLACEMENT_SCIENCE" if altered else
                       "ORIGINAL_EXTREME_RETAINED_REVIEW_CAUTIONS"})
        # Non-QC0 variable changes remain algorithmic Stage07 candidates,
        # not implicitly approved by the operator's TA-only decision.
        n_unapproved=changed_count-len(approvedkeys)
        srow={
            "site":site,"Stage07_numeric_complete":True,
            "original_data_sha_verified":True,
            "Stage07_selected_candidate_sha_verified":True,
            "operator_approved_exact_QC0_TA_count":len(approvedkeys),
            "total_Stage07_variable_changes":changed_count,
            "other_stage07_variable_changes_NOT_APPROVED":n_unapproved,
            "original_VPD_manual_review":len(review),
            "VPD_manual_changed_needs_science":manual_changed,
            "VPD_manual_unchanged_extreme_caution":manual_unchanged,
            "required_meteorological_field_missing":miss,
            "native_source_clock_continuous":True,
            "source_UTC_metadata_formally_approved":False,
            "PFT_tower_footprint_science_approved":False,
            "ZBOT_tower_measurement_height_approved":False,
            "Postv5_all_variable_changes_approved":False,
            "DATM_ready":False,"spinup_authorized":False,
            "reason":"US-NC2 separate 2025 time/ERA and scientific humidity holds" if
              site=="US-NC2" else "Remaining forcing changes, PFT/height/time/Post-v5 gates",
        }
        # Existing structural PFT audits (not footprint science approval).
        roots=sorted((ROOT/"reports").glob("stage04a_surface_*/surface_summary.csv"))
        for path in reversed(roots):
            try:
                frame=pd.read_csv(path)
                subset=frame.loc[frame.site.eq(site)]
                if len(subset)==1:
                    a=subset.iloc[0]
                    srow["surface_report_directory"]=str(path.parent)
                    for sourcecol,outcol in (
                      ("result","structural_surface_status"),
                      ("igbp","source_IGBP_label"),
                      ("PCT_NATVEG","grid_pct_natural_vegetation"),
                      ("PCT_CROP","grid_pct_crop"),
                      ("dbf_natural_pct","grid_pct_of_natural_DBF"),
                      ("enf_natural_pct","grid_pct_of_natural_ENF"),
                      ("forest_natural_pct","grid_pct_of_natural_trees"),
                      ("grass_natural_pct","grid_pct_of_natural_grass"),
                      ("shrub_natural_pct","grid_pct_of_natural_shrub"),
                      ("review","surface_footprint_and_PFT_review")):
                        if sourcecol in frame: srow[outcol]=a[sourcecol]
                    break
            except (OSError,ValueError):
                continue
        # Original release BIF height references are evidence, not ZBOT.
        rawdir=Path(spec["primary"]).parent
        bif=sorted(p for p in rawdir.glob("*.csv") if "_BIF_" in p.name.upper())
        if len(bif)==1:
            bpath=valid(bif[0])
            height_fields=[]
            with bpath.open(encoding="utf-8-sig",newline="") as f:
                r=csv.DictReader(f)
                for record in r:
                    var=str(record.get("VARIABLE",""))
                    val=str(record.get("DATAVALUE",""))
                    if "HEIGHT" in var.upper() or "HEIGHT" in str(record.get("VARIABLENAME","")).upper():
                        height_fields.append((var,val,record.get("GROUP_ID","")))
            srow["BIF_height_record_count"]=len(height_fields)
            srow["BIF_height_source_SHA256"]=digest(bpath)
            for var,val,group in height_fields[:100]:
                heights.append({"site":site,"source_BIF":str(bpath),
                                "variable":var,"data_value":val,"group_id":group,
                                "ZBOT_approved":False})
        else:
            srow["BIF_height_record_count"]=None
        sites.append(srow)
    return pd.DataFrame(sites),pd.DataFrame(edits),pd.DataFrame(vpd),pd.DataFrame(heights)

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for o in ("self-test","check","run"):
        mode.add_argument("--"+o,action="store_true")
    p.add_argument("--decision",type=Path,
         help="download exact GitHub operator approval JSON, required except --self-test")
    a=p.parse_args()
    print("STAGE13D SIX APPROVED TA + THREE SITE POST-V5 EVIDENCE PREFLIGHT | "+VER,flush=True)
    selftest()
    if a.self_test:return
    if a.decision is None:
        p.error("Provide --decision path to exact operator-approved GitHub JSON")
    sites,edits,vpd,heights=runaudit(a.decision)
    if len(edits)!=6 or len(vpd)!=18:
        raise RuntimeError("Original six accepted TA / eighteen pending VPD scopes changed")
    print("\n=== THREE SITE POSTV5 ADMISSION SCIENCE STATUS ===",flush=True)
    cols=("site","Stage07_numeric_complete","operator_approved_exact_QC0_TA_count",
          "total_Stage07_variable_changes","other_stage07_variable_changes_NOT_APPROVED",
          "original_VPD_manual_review","VPD_manual_changed_needs_science",
          "VPD_manual_unchanged_extreme_caution","structural_surface_status",
          "source_IGBP_label","grid_pct_of_natural_DBF",
          "grid_pct_of_natural_ENF","grid_pct_of_natural_trees",
          "BIF_height_record_count","DATM_ready")
    print(sites.reindex(columns=cols).fillna("-").to_string(index=False),flush=True)
    print("\n=== PENDING VPD MANUAL SCIENCE REVIEWS (not approved by temperature decision) ===",flush=True)
    print(vpd.to_string(index=False),flush=True)
    print("\n=== ORIGINAL BIF HEIGHT REFERENCES (possible ZBOT evidence, NOT selected) ===",flush=True)
    if len(heights):
        print(heights.head(40).to_string(index=False),flush=True)
    else:print("NO BIF HEIGHT REFERENCES FOUND; ZBOT and canopy height remain HOLD",flush=True)
    print("STAGE13D SIX QC0 TEMPERATURES APPROVED | zero other science approvals or original writes",flush=True)
    if a.check:
        print("STAGE13D CHECK ONLY | ZERO FILE WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13d_three_site_postv5_QC0_science_gates_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    objects={
      "three_site_remaining_Postv5_science_gates.csv":sites,
      "six_operator_approved_TA_QC0_exact_values_verified.csv":edits,
      "eighteen_still_unapproved_VPD_review_values.csv":vpd,
      "original_BIF_height_evidence_NOT_ZBOT.csv":heights}
    for name,data in objects.items():data.to_csv(out/name,index=False)
    note="TEMPERATURE_APPROVAL_ONLY_OTHER_GATES_RETAINED"
    (out/note).write_text(
      "The operator's 2026-10-26 approval applies to exactly six signed QC0 "
      "tower-temperature interpolations from existing Stage07. No source "
      "or preexisting Stage07 forcing has been modified. Other changed "
      "variables, manual VPD concerns, source clock, tower height (ZBOT), "
      "ecological PFT/surface suitability, CIME, Post-v5 production "
      "and spinup permissions are NOT approved by this report.\n")
    receipt={
      "version":VER,
      "decision_json_sha256":digest(a.decision),
      "stage07_selected_sha256":digest(S07/"output_sha256.json"),
      "signed_stage13b_receipt_sha256":digest(
           S13B/"stage13b_three_site_decision_SHA_receipt.json"),
      "six_QC0_approved_verified":True,
      "operator_approval_scope":"SIX_EXACT_TA_SOURCE_QC0_INTERPOLATIONS_ONLY",
      "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
      "output_SHA256":{n:digest(out/n) for n in [*objects,note]}}
    (out/"stage13d_three_site_approval_scope_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13D ONE-PASS SCIENCE GATE REPORT:",out,flush=True)
    print("NO SOURCE, SELECTED FORCING, SURFACE, CASE, DATM OR SLURM WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13D STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage13a: ONE-PASS actual Batch03 other-nine-site forcing admission ledger.

Read historical Stage07 exact-input manifest and real selected QC-v5 outputs,
Stage10d pinned independent humidity review, and current source metadata.
Three historical Stage07 sites (US-MOz, US-Mpj, US-NC2) finished NUMERIC
candidates; six did not. This script independently checks current files and
never turns numeric success into production approval. US-NC2 has newer
Stage11 source/clock and 2025 ERA-L evidence that this scan does not resolve.
US-Kon is intentionally excluded (signed Stage12ay 77 missing/HOLD).
No original, Stage07 candidate, source, DATM, model, case, Slurm writes.

--self-test: synthetic tests; no user files.
--check: read all nine, print compact status; zero writes.
--run: same + isolated signed site inventory/conditions/summary, no forcing.
"""
import argparse,csv,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VER="batch03-stage13a-v2-20261026-aligned-to-original-stage07-numerical-science-gates"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE10D=R/"reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
STAGE12AY=R/"science_trials/stage12ay_Kon_FINAL_science_candidates_and_sealed_HOLDS_20261026T132804Z_87d94e7a"
SITES=("US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj",
       "US-MtB","US-NC2","US-NR1","US-NR3")
HISTORICAL_NUMERIC={"US-MOz","US-Mpj","US-NC2"}
SITE_YEARS={
 "US-Me2":(2002,2022),"US-Me6":(2010,2025),"US-MMS":(1999,2023),
 "US-MOz":(2004,2021),"US-Mpj":(2008,2025),"US-MtB":(2009,2024),
 "US-NC2":(2005,2025),"US-NR1":(1998,2025),"US-NR3":(2007,2024)}
MET=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing or symlink provenance: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def expected_rows(site):
    a,b=SITE_YEARS[site]
    return (b-a+1)*(8760 if site=="US-MMS" else 17520)

def syntest():
    assert len(SITES)==9 and len(set(SITES))==9
    assert expected_rows("US-MMS")==25*8760
    assert expected_rows("US-NR3")==18*17520
    assert not HISTORICAL_NUMERIC- set(SITES)
    print("STAGE13A SELF-TEST PASS | 9 exact sites, native HR/HH, separate production gate; no writes",flush=True)

def numeric_candidate(site,p,entry):
    report={
      "candidate_noleap_rows":None,"candidate_expected_rows":expected_rows(site),
      "candidate_missing_humidity_HH":None,"candidate_missing_any_required_met_HH":None,
      "candidate_physically_invalid_HH":None,"candidate_30min_4hPa_jumps":None,
      "candidate_TBOT_K_range_violation":None,
      "source_clock_verified":False,"candidate_file_SHA_verified":False,
      "independent_audit_verified":False,
    }
    qcdir=STAGE07/site/"forcing"/"qc_v5"
    out=STAGE07/site/"forcing"/"processed_v5"/(
        f"{site}_CLM_forcing_{SITE_YEARS[site][0]}_{SITE_YEARS[site][1]}.csv")
    audit=qcdir/f"{site}_independent_audit.json"
    checks=json.loads(safe(STAGE07/"output_sha256.json").read_text())
    rel=str(out.relative_to(STAGE07))
    if checks.get(rel)!=sha(out):
        raise RuntimeError("Stage07 exact site candidate SHA mismatch "+site)
    report["candidate_file_SHA_verified"]=True
    aj=json.loads(safe(audit).read_text())
    if aj.get("site")!=site or aj.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
        raise RuntimeError("Stage07 independent audit marker changed "+site)
    if checks.get(str(audit.relative_to(STAGE07)))!=sha(audit):
        raise RuntimeError("Stage07 independent audit SHA mismatch "+site)
    report["independent_audit_verified"]=True
    if int(aj.get("noleap_rows",-1))!=expected_rows(site):
        raise RuntimeError("Stage07 independent audit row count does not agree "+site)
    report["Stage07_audit_QC0_changed_N"]=int(aj.get("changed_QC0_records",0))
    report["Stage07_audit_ERA_RH_floor_N"]=int(aj.get("ERA_RH_floor_records",0))
    report["Stage07_audit_manual_review_N"]=int(aj.get("manual_review_records",0))
    report["Stage07_audit_min_RH_pct"]=float(aj.get("min_RH_pct",float("nan")))
    fields=["time",*MET]
    df=pd.read_csv(safe(out),usecols=fields,dtype={"time":str},
                   low_memory=False)
    report["candidate_noleap_rows"]=len(df)
    if len(df)!=expected_rows(site):
        raise RuntimeError("Current numeric candidate selected row count wrong "+site)
    ts=pd.to_datetime(df.time,errors="raise")
    if ts.isna().any() or ts.duplicated().any() or (ts.dt.month.eq(2)&ts.dt.day.eq(29)).any():
        raise RuntimeError("Nonunique time/LEAP source in candidate "+site)
    interval=ts.diff().dt.total_seconds().iloc[1:]/60
    want=60 if site=="US-MMS" else 30
    valid_deltas=(interval==want)|(interval==want+1440)
    if not valid_deltas.all():
        raise RuntimeError("Original native interval not continuous in selected forcing "+site)
    if not (ts.iloc[0]==pd.Timestamp(f"{SITE_YEARS[site][0]}-01-01") and
            ts.iloc[-1]==pd.Timestamp(f"{SITE_YEARS[site][1]}-12-31 23:{'00' if site=='US-MMS' else '30'}")):
        raise RuntimeError("Selected source original year endpoints changed "+site)
    report["source_clock_verified"]=True
    data=df[list(MET)].apply(pd.to_numeric,errors="coerce")
    report["candidate_missing_humidity_HH"]=int(
        (~np.isfinite(data[["VPD_USE","QBOT"]].to_numpy(dtype=float)).all(axis=1)).sum())
    report["candidate_missing_any_required_met_HH"]=int(
        (~np.isfinite(data.to_numpy(dtype=float)).all(axis=1)).sum())
    t=data["TA_USE"].to_numpy(float)
    v=data["VPD_USE"].to_numpy(float)
    p=data["PSRF"].to_numpy(float)
    q=data["QBOT"].to_numpy(float)
    with np.errstate(all="ignore"):
        sw=6.112*np.exp(17.67*t/(t+243.5))
        e=(sw-v)*100
        calcq=.622*e/(p-.378*e)
        rh=100*e/(sw*100)
        # Match Stage07 independent numeric physics: RH (0,100.05]%
        # is allowed, including true saturation (VPD=0). Its QC-v5
        # humidity reconstruction permits up to 0.05pp rounding excess.
        # Count these as explicit scientific cautions, not new numeric fails.
        finite=np.isfinite(np.vstack([t,v,p,q,rh,calcq])).all(axis=0)
        paired=np.isclose(q,calcq,rtol=1e-6,atol=1e-10,equal_nan=False)
        bad=(~finite)|(rh<=0)|(rh>100.05)|(q<0)|(q>.08)|(~paired)
        old_gate_bad=((~finite)|(v<=0)|(rh<=0)|(rh>100.05)|
                      (q<=0)|(q>=.08)|(~paired))
        saturation_caution=(v<=0)|(rh>100.0)|(q<=0)
    report["candidate_physically_invalid_HH"]=int(np.count_nonzero(bad))
    report["candidate_v1_extra_strict_fail_HH"]=int(np.count_nonzero(old_gate_bad & ~bad))
    report["candidate_saturation_or_roundoff_caution_HH"]=int(np.count_nonzero(saturation_caution))
    report["candidate_negative_VPD_roundoff_caution_HH"]=int(np.count_nonzero((v<0)&(rh<=100.05)))
    report["candidate_zero_VPD_saturation_HH"]=int(np.count_nonzero(v==0))
    report["candidate_RH_above100_to100p05_HH"]=int(np.count_nonzero((rh>100)&(rh<=100.05)))
    report["candidate_TBOT_K_range_violation"]=int(
        ((data.TBOT<180)|(data.TBOT>340)|~np.isfinite(data.TBOT)).sum())
    dv=np.abs(np.diff(v))
    # This 4hPa edge count is a screening diagnostic, not an automatic
    # rejection of observed environmental extremes.
    report["candidate_30min_4hPa_jumps"]=(
        int(np.sum(dv>4)) if site!="US-MMS" else None)
    return report

def audit():
    manifest=json.loads(safe(STAGE07/"exact_input_manifest.json").read_text())
    preservation=json.loads(safe(STAGE07/"input_preservation_check.json").read_text())
    if preservation.get("unchanged") is not True or preservation.get("changed_inputs")!=[]:
        raise RuntimeError("Stage07 source preservation check failed")
    if not safe(STAGE07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"):
        raise RuntimeError("Stage07 incomplete production gate has gone missing")
    if (STAGE07/"COMPLETE_NUMERIC_CANDIDATES_REVIEW_REQUIRED").exists():
        raise RuntimeError("Stage07 historically incomplete but has complete marker")
    infos={r["site"]:r for r in manifest["sites"]}
    if len(infos)!=10 or set(infos)!=(set(SITES)|{"US-Kon"}):
        raise RuntimeError("Stage07 exact ten-site source manifest changed")
    summary=pd.read_csv(safe(STAGE07/"candidate_run_summary.csv"),low_memory=False)
    if len(summary)!=10 or summary.site.duplicated().any():
        raise RuntimeError("Stage07 ten-site candidate summary missing/duplicates")
    pass_sites=set(summary.loc[summary.status.eq("CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED"),"site"])
    if pass_sites!=HISTORICAL_NUMERIC:
        raise RuntimeError("Historical three Stage07 numeric sites changed: "+str(pass_sites))
    verified_sha=json.loads(safe(STAGE07/"output_sha256.json").read_text())
    for f in ("candidate_run_summary.csv","input_preservation_check.json","exact_input_manifest.json"):
        if f!="exact_input_manifest.json" and verified_sha.get(f)!=sha(STAGE07/f):
            raise RuntimeError("Stage07 signed historical status file changed "+f)
    axreceipt=json.loads(safe(STAGE12AY/"stage12ay_FINAL_research_HOLD_SHA_receipt.json").read_text())
    if not (axreceipt.get("new_research_missing")==77 and
        axreceipt.get("nine_protected_native_science_holds")==9 and
        axreceipt.get("DATM_ready") is False and
        axreceipt.get("spinup_authorized") is False):
        raise RuntimeError("Latest US-Kon 77 source hold status changed")
    independent=pd.read_csv(safe(STAGE10D/"site_triage_summary.csv"))
    if set(independent.site)!={"US-Kon","US-Me2","US-Me6","US-MMS","US-MtB","US-NR1","US-NR3"} or \
       int(independent.events.sum())!=1924 or \
       int(independent.approved_replacements.sum())!=0:
        raise RuntimeError("Independent Stage10d 1924 source audit set changed")
    primarypins={str(Path(k).resolve()):h for k,h in manifest["input_sha256"].items()}
    records=[]
    for site in SITES:
        x=infos[site]
        a,b=SITE_YEARS[site]
        errs=[]
        if (int(x["first_year"]),int(x["last_year"]))!=(a,b):
            raise RuntimeError("Manifest source window differs "+site)
        if int(x["native_minutes"])!=(60 if site=="US-MMS" else 30):
            raise RuntimeError("Native hour/half-hour identity changed "+site)
        for kind in ("primary","era"):
            p=safe(x[kind])
            if sha(p)!=primarypins.get(str(p.resolve())):
                raise RuntimeError("Original raw source primary/ERA SHA altered "+site+":"+kind)
        old=summary.loc[summary.site.eq(site)].iloc[0]
        row={"site":site,"native_resolution_minutes":int(x["native_minutes"]),
             "first_year":a,"last_year":b,
             "raw_primary_and_companion_SHA_current_verified":True,
             "Stage07_historical_candidate_status":str(old.status),
             "Stage07_old_error":str(old.get("error","")),
             "original_VPD_clock_source_review":"REVIEW" if site=="US-Me2" else "NO_NEW_APPROVAL",
             "Stage10d_original_humidity_events":0,
             "Stage10d_priority_P0":0,"Stage10d_priority_P1":0,
             "Stage10d_priority_P2":0,"Stage10d_priority_P3":0,
             "Stage10d_priority_P4":0,"Stage10d_science_approved":False,
             "latest_known_additional_HOLD":"US-NC2_STAGE11_UNAPPROVED_CLOCK_2025_ERA" if site=="US-NC2" else
                 "US-Me2_RELEASE_CLOCK_METADATA_UNRESOLVED" if site=="US-Me2" else "",
             "Postv5_approved":False,"DATM_ready":False,
             "spinup_authorized":False}
        review=independent.loc[independent.site.eq(site)]
        if len(review):
            z=review.iloc[0]
            row["Stage10d_original_humidity_events"]=int(z.events)
            for n in range(5):row[f"Stage10d_priority_P{n}"]=int(z[f"priority_P{n}"])
        if site in pass_sites:
            try:
                row.update(numeric_candidate(site,R, x))
                row["numeric_selected_candidate_screen"]=(
                    "CURRENT_NUMERIC_FIELDS_PASS_ONLY" if
                    row["candidate_missing_any_required_met_HH"]==0 and
                    row["candidate_physically_invalid_HH"]==0 and
                    row["candidate_TBOT_K_range_violation"]==0 and
                    row["source_clock_verified"] else
                    "CURRENT_SELECTED_CANDIDATE_SCIENCE_GATE_FAIL")
            except Exception as exc:
                row["numeric_selected_candidate_screen"]="FAILED_CURRENT_INDEPENDENT_CHECK"
                row["current_validation_error"]=str(exc)
        else:
            row["numeric_selected_candidate_screen"]="STAGE07_BLOCKED_NO_COMPLETE_NUMERIC_CANDIDATE"
        records.append(row)
    return pd.DataFrame(records)

def main():
    pa=argparse.ArgumentParser()
    g=pa.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):g.add_argument("--"+mode,action="store_true")
    args=pa.parse_args()
    print("STAGE13A AMERIFLUX BATCH03 NINE-SITE SINGLE-PASS ADMISSION | "+VER,flush=True)
    syntest()
    if args.self_test:return
    report=audit()
    print("STAGE13A SOURCE VERIFIED SITES 9/9",flush=True)
    columns=["site","Stage07_historical_candidate_status",
             "numeric_selected_candidate_screen",
             "candidate_missing_any_required_met_HH",
             "candidate_physically_invalid_HH",
             "candidate_v1_extra_strict_fail_HH",
             "candidate_saturation_or_roundoff_caution_HH",
             "Stage07_audit_ERA_RH_floor_N",
             "Stage10d_original_humidity_events",
             "DATM_ready"]
    print(report.reindex(columns=columns).fillna("-").to_string(index=False),flush=True)
    print("STAGE13A SIX ORIGINAL STAGE07 BLOCKER REASONS:",flush=True)
    for row in report.loc[report.Stage07_historical_candidate_status.eq("FAIL")].to_dict("records"):
        print(row["site"],"|",str(row.get("Stage07_old_error",""))[:240],flush=True)
    print("STAGE13A THREE HISTORICAL NUMERIC-SITE CAUTIONS:",flush=True)
    for row in report.loc[report.site.isin(HISTORICAL_NUMERIC)].to_dict("records"):
        print(row["site"],"original_stage07_floor=",row.get("Stage07_audit_ERA_RH_floor_N"),
              "original_stage07_QC0_change=",row.get("Stage07_audit_QC0_changed_N"),
              "additional_saturation_or_roundoff=",row.get("candidate_saturation_or_roundoff_caution_HH"),
              "extra_v1_gate_errors=",row.get("candidate_v1_extra_strict_fail_HH"),
              "validation_error=",row.get("current_validation_error",""),flush=True)
    print("STAGE13A GATES: historical numeric candidates 3, historical humidity-blocked 6;",
          "NO Post-v5/production approvals. Kon sealed 77 humidity holds; no new model jobs.",
          flush=True)
    if args.check:
        print("STAGE13A CHECK ONLY | NO FILE WRITES",flush=True)
        return
    folder=R/"reports"/("stage13a_Batch03_NINE_SITE_FORCING_ADMISSION_"+datetime.now(timezone.utc).
                        strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    csvfile="Batch03_nine_site_forcing_admission_readonly.csv"
    report.to_csv(folder/csvfile,index=False)
    notes="BATCH03_NINE_SITES_NEITHER_POSTV5_NOR_SPINUP_APPROVED"
    (folder/notes).write_text(
        "Historical Stage07 only US-MOz, US-Mpj, US-NC2 produced numeric"
        " candidates. This independent current check cannot retroactively"
        " approve them, and US-NC2 later Stage11 science remains unresolved."
        " Six other sites were historically humidity-blocked. The exact"
        " selected temperature/source clock/terrain, native independent"
        " humidity replacement provenance, PFT suitability and Post-v5"
        " controls must be checked before DATM. Other than new reports,"
        " there are no source, selected forcing, Slurm, DATM or model edits.\n")
    receipt={
        "version":VER,
        "historical_numeric_candidates":3,
        "historical_humidity_blocked":6,
        "sites":list(SITES),
        "sealed_Kon_unresolved_VPD_QBOT":77,
        "Stage07_original_input_manifest_SHA256":sha(STAGE07/"exact_input_manifest.json"),
        "Stage12ay_Kon_final_SHA256":sha(
           STAGE12AY/"stage12ay_FINAL_research_HOLD_SHA_receipt.json"),
        "Postv5_approved":False,"DATM_ready":False,
        "spinup_authorized":False,
        "output_SHA256":{csvfile:sha(folder/csvfile),notes:sha(folder/notes)}
    }
    (folder/"stage13a_nine_site_admission_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13A AUDIT REPORT:",folder,flush=True)
    print("NO ORIGINAL, FORCING, CASE, DATM OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13A STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

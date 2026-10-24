#!/usr/bin/env python3
"""Batch03 Stage11c: read-only per-event evidence for three Stage07 QCv5 candidates.

US-MOz, US-Mpj and US-NC2 passed Stage11b Gate-0 numerical consistency.
Stage11c identifies EVERY logged source-to-v5 modification (including
original source QC0), each Stage07 manual-review row (may be unmodified),
and native positive RH<1% episodes. Join the immutable source, companion ERA
and candidate by EXACT native TIMESTAMP_START; never by row number across
two unequal-length source releases.

--self-test: synthetic event/source matching only, no IRIDIS file access.
--check: provenance, individual event/ERA/QC and low-RH checks, no writes.
--run: create a NEW isolated audit-only report folder, SHA receipt; NEVER
  changes existing candidate forcing, trial INCOMPLETE marker, DATM or Slurm.
Scientific gate: zero automated approvals even when every check passes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11c-v1-20261024-event-evidence"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11B=ROOT/"reports/stage11b_postv5_gate0_three_sites_20261024T065829Z_79a2f708"
S11A=ROOT/"reports/stage11a_science_decision_matrix_20261024T064632Z_da305a30"
SITES=("US-MOz","US-Mpj","US-NC2")
EXPECTED_CHANGES={"US-MOz":6,"US-Mpj":16,"US-NC2":83}
EXPECTED_QC0={"US-MOz":1,"US-Mpj":1,"US-NC2":4}
EXPECTED_MANUAL={"US-MOz":0,"US-Mpj":5,"US-NC2":13}
RAW_VARS=("TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
RAW_TO_FORCE={"TA_F":"TA_USE","VPD_F":"VPD_USE","PA_F":"PSRF",
              "SW_IN_F":"FSDS","LW_IN_F":"FLDS","WS_F":"WIND",
              "P_F":"PRECTmms"}
REQUIRED_EVENT={"site","time","variable","original_value","era_reference",
                "final_value","official_qc","final_source","reason"}
REQUIRED_MANUAL={"site","time","variable","final_value","era_value",
                 "difference_to_era","previous_value","next_value",
                 "official_qc","reason"}
REQUIRED_RH={"site","time","TA_final_C","VPD_final_hPa","RH_final_pct",
             "TA_QC","VPD_QC"}


def regular(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing/unsafe regular file: "+str(path))
    return path


def folder(path):
    path=Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Missing/unsafe evidence directory: "+str(path))
    return path


def digest(path):
    h=hashlib.sha256()
    with regular(path).open("rb") as fh:
        for piece in iter(lambda:fh.read(1<<20),b""):
            h.update(piece)
    return h.hexdigest()


def jsonfile(path):
    return json.loads(regular(path).read_text(encoding="utf-8"))


def number(series):
    x=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x)|(x<=-9990)]=np.nan
    return x


def equal_measure(a,b):
    return np.isclose(a,b,atol=1e-9,rtol=1e-10,equal_nan=True)


def timekey(series):
    out=pd.to_datetime(series,errors="raise")
    if out.isna().any():
        raise ValueError("Invalid native source/candidate timestamp")
    return out.dt.strftime("%Y%m%d%H%M")


def native_dt(string_series):
    dt=pd.to_datetime(string_series,format="%Y%m%d%H%M",errors="raise")
    if dt.isna().any() or dt.duplicated().any() or not dt.is_monotonic_increasing:
        raise ValueError("Missing, duplicate or out-of-order source timestamp")
    return dt


def es_water(temp_c):
    with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
        return 6.112*np.exp(17.67*temp_c/(temp_c+243.5))


def load_and_verify_inputs():
    for p in (ROOT,S07,S11A,S11B):
        folder(p)
    regular(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    b=jsonfile(S11B/"scientific_hold_receipt.json")
    if (b.get("version")!="stage11b-v1-20261024-three-numeric-site-gate0"
        or b.get("sites")!=list(SITES) or b.get("numerically_checked")!=3
        or b.get("repairs_approved")!=0 or b.get("clock_approved")!=0
        or b.get("post_v5_approved")!=0 or b.get("DATM_ready_sites")!=0
        or b.get("spinup_authorizations")!=0
        or b.get("stage07_incomplete_marker_still_required") is not True
        or b.get("source_stage07_manifest_sha256")!=digest(S07/"exact_input_manifest.json")
        or b.get("stage07_output_receipt_sha256")!=digest(S07/"output_sha256.json")
        or b.get("source_stage11a_receipt_sha256")!=digest(S11A/"scientific_hold_receipt.json")):
        raise ValueError("Stage11b and Stage11a source-provenance hold mismatch")
    if set(b.get("output_sha256",{}))!={"three_numeric_site_gate0_review.csv","REVIEW_HOLD.md"}:
        raise ValueError("Stage11b report schema modified")
    for name,checksum in b["output_sha256"].items():
        if digest(S11B/name)!=checksum:
            raise ValueError("Stage11b output modified: "+name)
    stage11b=pd.read_csv(regular(S11B/"three_numeric_site_gate0_review.csv"))
    if len(stage11b)!=3 or set(stage11b.site)!=set(SITES):
        raise ValueError("Stage11b three-site candidate inventory changed")
    for site in SITES:
        prior=stage11b.loc[stage11b.site.eq(site)]
        if (len(prior)!=1
            or int(prior.raw_to_candidate_changes.iloc[0])!=EXPECTED_CHANGES[site]
            or int(prior.changed_original_QC0_records.iloc[0])!=EXPECTED_QC0[site]
            or int(prior.manual_review_records.iloc[0])!=EXPECTED_MANUAL[site]
            or str(prior.post_v5_approved.iloc[0]).lower()!="false"):
            raise ValueError("Stage11b individual source gate changed: "+site)
    manifest=jsonfile(S07/"exact_input_manifest.json")
    specs={a["site"]:a for a in manifest["sites"]}
    if not set(SITES)<=set(specs) or len(specs)!=10:
        raise ValueError("Stage07 original source inventory changed")
    input_sha={str(Path(path).resolve()):value
               for path,value in manifest["input_sha256"].items()}
    outputs=jsonfile(S07/"output_sha256.json")
    if len(outputs)<10:
        raise ValueError("Stage07 sealed output manifest incomplete")
    return specs,input_sha,outputs,b


def checked_original(spec,input_sha,source_kind):
    p=regular(spec[source_kind])
    if p.parent.name!=spec["release"] or p.parent.parent.name!="raw":
        raise ValueError("Original source release path changed: "+str(p))
    if digest(p)!=input_sha.get(str(p.resolve())):
        raise ValueError("Original source SHA changed: "+str(p))
    return p


def sealed_stage07(path,seal):
    relative=str(path.relative_to(S07))
    if relative not in seal or digest(path)!=seal[relative]:
        raise ValueError("Stage07 candidate/evidence SHA failed: "+relative)
    return path


def read_site(site,spec,pins,outputs):
    first,last,step=map(int,(spec["first_year"],spec["last_year"],spec["native_minutes"]))
    if step!=30:
        raise ValueError("Expected native half-hour resolution at "+site)
    source=checked_original(spec,pins,"primary")
    companion=checked_original(spec,pins,"era")
    rawcols=set(pd.read_csv(source,nrows=0).columns)
    eracols=set(pd.read_csv(companion,nrows=0).columns)
    wants={"TIMESTAMP_START",*RAW_VARS}
    era_wants={"TIMESTAMP_START",*[v.replace("_F","_ERA") for v in RAW_VARS]}
    if not wants<=rawcols or not era_wants<=eracols:
        raise ValueError("Original raw/ERA field schema changed for "+site)
    qcs=sorted({v+"_QC" for v in RAW_VARS}&rawcols)
    raw=pd.read_csv(source,usecols=sorted(wants)+qcs,
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    # Native Stage07 engine explicitly allows missing optional *_F_QC
    # columns and represents them as NaN (unknown, NEVER QC0).
    for var in RAW_VARS:
        if var+"_QC" not in raw.columns:
            raw[var+"_QC"]=np.nan
    times=native_dt(raw["TIMESTAMP_START"])
    valid=(times.dt.year.between(first,last)&
           ~((times.dt.month==2)&(times.dt.day==29)))
    raw=raw.loc[valid].reset_index(drop=True)
    raw["native_key"]=raw["TIMESTAMP_START"]
    expected=pd.date_range(f"{first}-01-01",f"{last+1}-01-01",
                           freq=f"{step}min",inclusive="left")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    native_stamps=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M")
    if (len(raw)!=len(expected) or
        not np.array_equal(native_stamps.to_numpy(),expected.to_numpy())):
        raise ValueError("Source NO_LEAP chronology differs: "+site)
    base=S07/site/"forcing"
    files={
        "forcing":base/"processed_v5"/f"{site}_CLM_forcing_{first}_{last}.csv",
        "changes":base/"qc_v5"/f"{site}_replacement_events.csv",
        "manual":base/"qc_v5"/f"{site}_manual_review.csv",
        "lowrh":base/"qc_v5"/f"{site}_low_RH_diagnostic.csv",
        "lowdecisions":base/"qc_v5"/f"{site}_low_RH_decisions.csv",
        "status":base/"qc_v5"/f"{site}_status.json",
        "independent":base/"qc_v5"/f"{site}_independent_audit.json",
    }
    for p in files.values():
        sealed_stage07(regular(p),outputs)
    force=pd.read_csv(files["forcing"],low_memory=False)
    if "time" not in force:
        raise ValueError("Stage07 forcing missing time: "+site)
    force["native_key"]=timekey(force.time)
    if (len(force)!=len(raw) or
        not force.native_key.equals(raw.native_key)):
        raise ValueError("Stage07 candidate/native source chronology mismatch: "+site)
    changes=pd.read_csv(files["changes"],dtype={"time":str},low_memory=False)
    manual=pd.read_csv(files["manual"],dtype={"time":str},low_memory=False)
    lowrh=pd.read_csv(files["lowrh"],dtype={"time":str},low_memory=False)
    lowdecisions=pd.read_csv(files["lowdecisions"],dtype={"time":str},low_memory=False)
    if not REQUIRED_EVENT<=set(changes) or not REQUIRED_MANUAL<=set(manual):
        raise ValueError("Stage07 event/manual schema mismatch: "+site)
    status=jsonfile(files["status"])
    independent=jsonfile(files["independent"])
    if (status.get("site")!=site or independent.get("site")!=site
        or independent.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED"
        or len(changes)!=int(status["changes"])
        or len(manual)!=int(status["manual_review_records"])
        or len(lowrh)!=int(independent["positive_RH_lt1"])):
        raise ValueError("Stage07 status/low-RH ledger mismatch: "+site)
    if len(changes)!=EXPECTED_CHANGES[site] or len(manual)!=EXPECTED_MANUAL[site]:
        raise ValueError("Stage11b change/manual counts differ: "+site)
    erawant=sorted(era_wants)
    era=pd.read_csv(companion,usecols=erawant,dtype={"TIMESTAMP_START":str},low_memory=False)
    era_time=native_dt(era.TIMESTAMP_START)
    if era_time.diff().dropna().ne(pd.Timedelta(minutes=step)).any():
        raise ValueError("Original companion ERA native time cadence changed: "+site)
    changes["native_key"]=timekey(changes.time)
    manual["native_key"]=timekey(manual.time)
    if changes.site.ne(site).any() or manual.site.ne(site).any():
        raise ValueError("Stage07 ledger site IDs differ")
    if not changes.variable.isin(RAW_VARS).all() or not manual.variable.isin(RAW_VARS).all():
        raise ValueError("Stage07 ledger unknown variable")
    if changes.duplicated(["native_key","variable"]).any():
        raise ValueError("Duplicate Stage07 change key")
    if not changes.native_key.isin(raw.native_key).all() or not manual.native_key.isin(raw.native_key).all():
        raise ValueError("Stage07 event timestamp not present in source")
    return raw,force,era,changes,manual,lowrh,lowdecisions,status,independent


def event_audit(site,raw,force,era,changes,manual):
    lookup={key:i for i,key in enumerate(raw.native_key)}
    era_map=era.set_index("TIMESTAMP_START")
    results=[]
    for rec in changes.itertuples(index=False):
        item=rec._asdict()
        key=item["native_key"]
        var=str(item["variable"])
        i=lookup[key]
        q=float(number(pd.Series([raw.iloc[i][var+"_QC"]]))[0])
        original=number(pd.Series([raw.iloc[i][var]]))[0]
        col=RAW_TO_FORCE[var]
        step=30
        final=number(pd.Series([force.iloc[i][col]]))[0]
        if var=="PA_F": final/=1000
        if var=="P_F": final*=step*60
        if not (equal_measure(original,
                number(pd.Series([item["original_value"]]))[0])
            and equal_measure(final,number(pd.Series([item["final_value"]]))[0])
            and equal_measure(q,number(pd.Series([item["official_qc"]]))[0])):
            raise ValueError("Source vs event original/final/QC mismatch: "+
                             site+" "+key+" "+var)
        if equal_measure(original,final):
            raise ValueError("Stage07 ledger lists a mathematically unchanged row")
        eracol=var.replace("_F","_ERA")
        if key not in era_map.index:
            raise ValueError("Companion ERA missing exact event timestamp")
        eref=number(pd.Series([era_map.at[key,eracol]]))[0]
        recorded_era=number(pd.Series([item["era_reference"]]))[0]
        if not equal_measure(eref,recorded_era):
            raise ValueError("Stage07 event ERA value differs from original companion: "+
                             site+" "+key+" "+var)
        same_manual=int(((manual.native_key==key)&(manual.variable==var)).sum())
        events={
            "site":site,"time":str(item["time"]),"variable":var,
            "timestamp_start_native":key,"raw_native_row_0based":i,
            "source_value":original,"candidate_value":final,
            "original_source_QC":q,"source_ERA_same_timestamp":eref,
            "absolute_change":float(abs(final-original)) if np.isfinite(original) else np.nan,
            "event_reason":str(item["reason"]),
            "final_source":str(item["final_source"]),
            "manual_same_time_variable_count":same_manual,
            "original_QC0_modified":bool(q==0),
            "original_missing_filled":bool(not np.isfinite(original)),
            "review_route":("CHANGED_MEASURED_QC0_REVIEW" if q==0 else
                "MISSING_FILLED_SOURCE_REVIEW" if not np.isfinite(original) else
                "GAPFILL_OR_CORRECTION_SOURCE_REVIEW"),
            "independent_tower_measurement_approval":False,
            "post_v5_approved":False
        }
        results.append(events)
    out=pd.DataFrame(results)
    if len(out)!=len(changes) or out.original_QC0_modified.sum()!=EXPECTED_QC0[site]:
        raise ValueError("Detailed event evidence differs from Stage11b QC0 tally")
    return out


def manual_audit(site,raw,force,manual,changes):
    lookup={key:i for i,key in enumerate(raw.native_key)}
    changed=set(map(tuple,changes[["native_key","variable"]].to_numpy()))
    outputs=[]
    for rec in manual.itertuples(index=False):
        row=rec._asdict()
        key=row["native_key"]
        var=str(row["variable"])
        i=lookup[key]
        source_qc=number(pd.Series([raw.iloc[i][var+"_QC"]]))[0]
        ledger_qc=number(pd.Series([row["official_qc"]]))[0]
        if not equal_measure(source_qc,ledger_qc):
            raise ValueError("Original QC differs in manual note: "+site+" "+key)
        candidate=number(pd.Series([force.iloc[i][RAW_TO_FORCE[var]]]))[0]
        if var=="PA_F": candidate/=1000
        if var=="P_F": candidate*=1800
        recorded=number(pd.Series([row["final_value"]]))[0]
        outputs.append({
            "site":site,"time":str(row["time"]),"variable":var,
            "timestamp_start_native":key,
            "manual_reason":str(row["reason"]),
            "original_source_QC":source_qc,
            "original_QC0_flag":bool(source_qc==0),
            "same_variable_changed_in_final":(key,var) in changed,
            "manual_recorded_stage_value":recorded,
            "final_candidate_value":candidate,
            "manual_value_equals_final":bool(equal_measure(recorded,candidate)),
            "manual_recorded_difference_to_ERA":row["difference_to_era"],
            "scientific_status":"HOLD_REVIEW_UNAPPROVED"
        })
    return pd.DataFrame(outputs,columns=[
        "site","time","variable","timestamp_start_native","manual_reason",
        "original_source_QC","original_QC0_flag",
        "same_variable_changed_in_final","manual_recorded_stage_value",
        "final_candidate_value","manual_value_equals_final",
        "manual_recorded_difference_to_ERA","scientific_status"
    ])


def lowrh_audit(site,lowrh,force):
    lookup=force.set_index("native_key",verify_integrity=True)
    if len(lowrh)==0:
        return pd.DataFrame(columns=["site","time","RH_final_pct",
            "independently_recalculated_water_RH_pct",
            "final_T_C","final_VPD_hPa","relative_to_ice_RH_pct",
            "native_source_TA_QC","native_source_VPD_QC",
            "physics_reject","science_status"])
    if not REQUIRED_RH<=set(lowrh):
        raise ValueError("Stage07 low RH diagnostic columns changed: "+site)
    keys=timekey(lowrh.time)
    if keys.duplicated().any() or not keys.isin(lookup.index).all():
        raise ValueError("Stage07 low RH timestamps invalid")
    f=lookup.loc[keys.to_numpy()]
    t=number(f["TA_USE"])
    vpd=number(f["VPD_USE"])
    es=es_water(t)
    rh=100*(es-vpd)/es
    if not (np.isfinite(rh).all() and (rh>0).all() and (rh<1).all()):
        raise ValueError("Stage07 low-RH source contains implausible candidate values")
    if not np.isclose(number(lowrh["RH_final_pct"]),rh,
                      atol=1e-5,rtol=1e-6).all():
        raise ValueError("Stage07 low RH diagnostic not equal candidate humidity")
    if not np.isclose(number(lowrh["TA_final_C"]),t,atol=1e-8,rtol=1e-9).all():
        raise ValueError("Stage07 low RH source T differs")
    if not np.isclose(number(lowrh["VPD_final_hPa"]),vpd,atol=1e-8,rtol=1e-9).all():
        raise ValueError("Stage07 low RH source VPD differs")
    with np.errstate(divide="ignore",invalid="ignore"):
        esi=6.112*np.exp(22.46*t/(t+272.62))
        esi=np.where(t<0,esi,es)
        ea=es-vpd
        ice_rh=100*ea/esi
    return pd.DataFrame({
        "site":site,"time":lowrh.time.to_numpy(),
        "RH_final_pct":number(lowrh["RH_final_pct"]),
        "independently_recalculated_water_RH_pct":rh,
        "final_T_C":t,"final_VPD_hPa":vpd,
        "relative_to_ice_RH_pct":ice_rh,
        "native_source_TA_QC":number(lowrh["TA_QC"]),
        "native_source_VPD_QC":number(lowrh["VPD_QC"]),
        "physics_reject":False,
        "science_status":"EXTREME_DRY_RH_LT1_NEEDS_SOURCE_VALIDATION"
    })


def self_test():
    native=pd.DataFrame({
        "TIMESTAMP_START":["202001010000","202001010030"],
        "TA_F":[-10.0,5.0],"VPD_F":[np.nan,3.0],
        "TA_F_QC":[2,0],"VPD_F_QC":[2,0],
        "PA_F":[98.,98.],"PA_F_QC":[2,2],
        "SW_IN_F":[0.,5.],"SW_IN_F_QC":[2,2],
        "LW_IN_F":[250.,250.],"LW_IN_F_QC":[2,2],
        "WS_F":[1.,1.],"WS_F_QC":[2,2],
        "P_F":[0.,0.],"P_F_QC":[2,2],
        "native_key":["202001010000","202001010030"]
    })
    force=pd.DataFrame({
        "TA_USE":[-10.,5.],"VPD_USE":[0.2,2.0],
        "PSRF":[98000.,98000.],"FSDS":[0.,5.],"FLDS":[250.,250.],
        "WIND":[1.,1.],"PRECTmms":[0.,0.]
    })
    force["native_key"]=native.native_key
    companion=pd.DataFrame({
        "TIMESTAMP_START":["202001010000","202001010030"],
        **{var.replace("_F","_ERA"):[2.0,2.0] for var in RAW_VARS}
    })
    events=pd.DataFrame([{
        "site":"US-MOz","time":"2020-01-01 00:30:00",
        "native_key":"202001010030","variable":"VPD_F",
        "original_value":3.0,"era_reference":2.0,
        "final_value":2.0,"official_qc":0.0,
        "final_source":"candidate_test","reason":"test_change"
    }])
    manual=pd.DataFrame(columns=[*REQUIRED_MANUAL,"native_key"])
    detail=event_audit("US-MOz",native,force,companion,events,manual)
    assert len(detail)==1 and detail.original_QC0_modified.iloc[0]
    assert str(timekey(pd.Series(["2020-01-01T00:30:00"])).iloc[0])=="202001010030"
    assert equal_measure(np.nan,np.nan)
    assert not equal_measure(1.,2.)
    print("STAGE11C SELF-TEST PASS: literal timestamps, QC0 change, companion ERA and candidate joins",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE11C — QC0/MANUAL/ERA REPLACEMENT EVIDENCE | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    specs,pins,seal,old=load_and_verify_inputs()
    changes_out=[]
    manual_out=[]
    lowrh_out=[]
    summary=[]
    for site in SITES:
        data=read_site(site,specs[site],pins,seal)
        raw,force,era,changes,manual,lowrh,lowdecisions,status,independent=data
        event=event_audit(site,raw,force,era,changes,manual)
        man=manual_audit(site,raw,force,manual,changes)
        dry=lowrh_audit(site,lowrh,force)
        changes_out.append(event)
        manual_out.append(man)
        lowrh_out.append(dry)
        era_only=int(event.final_source.eq("secondary_era_replacement").sum())
        if era_only!=int(independent["ERA_replacement_variable_records"]):
            raise ValueError("ERA-replacement source-event tally differs: "+site)
        summary.append({
            "site":site,"changed_variables":len(event),
            "original_measured_QC0_changes":int(event.original_QC0_modified.sum()),
            "original_missing_filled":int(event.original_missing_filled.sum()),
            "manual_review_rows":len(man),
            "manual_rows_without_final_change":int((~man.same_variable_changed_in_final).sum()),
            "manual_rows_with_intermediate_vs_final_difference":int((~man.manual_value_equals_final).sum()),
            "ERA_replacement_records":era_only,
            "residual_positive_RH_lt1_records":len(dry),
            "min_RH_of_dry_records_pct":float(dry.RH_final_pct.min()) if len(dry) else np.nan,
            "numeric_gate0_passed":True,
            "science_source_signoff":False,
            "PFT_surface_approved":False,
            "post_v5_approved":False,
            "DATM_ready":False,
            "spinup_authorized":False
        })
        print(f"STAGE11C SITE {site}: changes={len(event)} "
              f"QC0={int(event.original_QC0_modified.sum())} "
              f"manual={len(man)} ERA_replacements={era_only} "
              f"positive_RH_lt1={len(dry)} "
              "approval=0",flush=True)
    events=pd.concat(changes_out,ignore_index=True)
    manual=pd.concat(manual_out,ignore_index=True)
    dry=pd.concat(lowrh_out,ignore_index=True)
    status=pd.DataFrame(summary)
    if (len(events)!=105 or len(manual)!=18 or
        int(events.original_QC0_modified.sum())!=6 or
        int(status.ERA_replacement_records.sum())!=38):
        raise ValueError("Stage11b aggregate per-event results have changed")
    flagged=events.loc[events.original_QC0_modified].copy()
    print("\n========== SIX ORIGINAL QC0 MODIFICATIONS ==========",flush=True)
    cols=["site","time","variable","source_value","candidate_value",
          "source_ERA_same_timestamp","event_reason","final_source"]
    print(flagged[cols].to_string(index=False),flush=True)
    print("\n========== MANUAL REVIEW REASON COUNTS ==========",flush=True)
    if len(manual):
        print(manual.groupby(["site","manual_reason"]).size().to_string(),flush=True)
    print("\n========== THREE SITE PROVENANCE REVIEW SUMMARY ==========",flush=True)
    print(status.to_string(index=False),flush=True)
    print(f"\nSTAGE11C SUMMARY: events={len(events)}/105 "
          f"QC0_changed={len(flagged)}/6 manual={len(manual)}/18 "
          f"ERA_replacements={int(status.ERA_replacement_records.sum())}/38 "
          "approved_repairs=0 approved_postv5=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: no outputs or source changes.",flush=True)
        return
    folder_name="stage11c_qc0_manual_review_"+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=ROOT/"reports"/folder_name
    out.mkdir(exist_ok=False)
    docs={
        "105_exact_source_to_candidate_changes.csv":events,
        "6_original_QC0_modified_events.csv":flagged,
        "18_manual_review_entries.csv":manual,
        "positive_RH_below_1pct_diagnostics.csv":dry,
        "three_site_change_source_summary.csv":status
    }
    for name,frame in docs.items():
        frame.to_csv(out/name,index=False)
    note="""# Stage11c scientific review, NOT Post-v5 approval

Stage11b passed numerical checks for US-MOz/US-Mpj/US-NC2. This record
preserves 105 modified variables, including six original QC0 source values,
18 independent manual-review notifications (some may be unmodified or
represent intermediate candidate revisions), and source low-RH <1% episodes.

QC0 source measurements changed by an automatic v5 algorithm need manual
meteorological provenance review. A zero manual-review count never means
those automatic QC0 changes were scientifically approved.

ERA-source gapfills and low but positive RH are not accepted as tower
observations merely because they pass water-phase algebra. Low-RH <1% can
be real; never silently clip or ERA-replace it. Ice-phase saturation,
exact clock definitions, PFT surface/height and CO2 protocol remain open.
The Stage07 INCOMPLETE marker MUST remain and no DATM or spinup may start.

DO NOT modify any sealed review CSV to alter an approval flag. Produce a
separate versioned human-reviewed decision and source/counterfactual
uncertainty report when evidence is sufficient.
"""
    (out/"SCIENTIFIC_REVIEW_REQUIRED.md").write_text(note,encoding="utf-8")
    receipt={
        "version":VERSION,
        "Stage11b_receipt_SHA256":digest(S11B/"scientific_hold_receipt.json"),
        "Stage07_manifest_SHA256":digest(S07/"exact_input_manifest.json"),
        "Stage07_sealed_outputs_SHA256":digest(S07/"output_sha256.json"),
        "sites":list(SITES),
        "changes":105,"source_QC0_changes":6,"manual_rows":18,
        "ERA_replacement_variable_records":38,
        "approved_repairs":0,"approved_Postv5":0,
        "DATM_ready_sites":0,"spinup_authorizations":0,
        "Stage07_incomplete_marker_retained":True,
        "output_sha256":{name:digest(out/name)
                         for name in [*docs,"SCIENTIFIC_REVIEW_REQUIRED.md"]}
    }
    (out/"read_only_scientific_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11C REPORT DIR:",out,flush=True)
    print("NO RAW FORCING, TRIAL, DATM, CASE, RESTART OR SLURM MODIFICATIONS.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE11C STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

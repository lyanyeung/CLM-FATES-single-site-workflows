#!/usr/bin/env python3
"""Stage58 Batch02: preserve 63 manually reviewed extreme-cold tower TA_F records.

User confirmed 63/63 original EC air temperatures should be retained:
EML 27 (QC0), GLE 6 (QC0), ICt 30 (QC2). Reproduce pinned Stage57
original-source neighbor evidence; require all TA_F <0 C, towers warmer
than same-source ERA5 by >8 C, smooth ±30 min tower context, no spikes.
Combine with Stage56 3904 within-8C preserved temperatures; the remaining
917 US-Ho1 retain UTC offset HOLD. Compute consistent independent CDS ERA5
RH + VPD/QBOT against ORIGINAL TA_F/PA_F only where time alignment valid.
Do not release any RH/ice-phase scientific HOLD or write DATM/forcing/model.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib
import importlib.util
import json
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPO=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
S57_SCRIPT=REPO/"scripts/stage57/57_manual_review_63_tower_T_vs_ERA5.py"
S57_GIT_BLOB="4786751fb3500b3481a2505ccd778d2a4208a118"
S56=ROOT/"reports/stage56_original_T_if_ERA5_delta_le8C_20261024T104425Z_044e977d"
S56_FILE="4884_keep_original_TA_under8C_with_ERA5_RH_VPD_QBOT.csv"
REVIEWED={"US-EML":27,"US-GLE":6,"US-ICt":30}
STAGE11_SITES={"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}
DECISION_63="KEEP_ORIGINAL_TA_F_MANUALLY_APPROVED_EXTREME_COLD_GT8C"
DECISION_3904="KEEP_ORIGINAL_TA_F_WITHIN8C"
DECISION_HO1="HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL"
SCIENCE_POLICY="USER_APPROVED_ORIGINAL_TEMPERATURE_ONLY_2026-10-24"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1048576),b""):
            h.update(part)
    return h.hexdigest()

def git_blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(
        b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def water_pair(temp_c,rh_pct,pressure_kpa):
    t=np.asarray(temp_c,dtype=float)
    r=np.asarray(rh_pct,dtype=float)/100
    p=np.asarray(pressure_kpa,dtype=float)*1000
    es=6.112*np.exp(17.67*t/(t+243.5))
    e=es*r
    return es-e,0.622*(100*e)/(p-0.378*(100*e))

def self_test():
    v,q=water_pair([20],[50],[100])
    assert 11.67<v[0]<11.70 and .007<q[0]<.008
    assert sum(REVIEWED.values())==63
    assert sum(STAGE11_SITES.values())==4884
    assert 3904+63+917==4884
    print("STAGE58 SELF-TEST PASS | 63 manual T accepted + 3904 within8C + 917 Ho1 HOLD")

def get_evidence():
    if git_blob(S57_SCRIPT)!=S57_GIT_BLOB:
        raise ValueError("Stage57 script does not match SHA-pinned manual review version")
    spec=importlib.util.spec_from_file_location("batch02_pinned_stage57",str(S57_SCRIPT))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    src,towers,pins=module.read_and_pin()
    evidence=module.event_report(src,towers)
    if len(evidence)!=63 or Counter(evidence.site)!=Counter(REVIEWED):
        raise ValueError("Exact 63 original tower manual review population changed")
    if evidence.duplicated(["site","local"]).any():
        raise ValueError("Duplicate manual-review source timestamp")
    if (not evidence.TA_F_C.lt(0).all() or
        not evidence.TA_minus_ERA5_C.gt(8).all() or
        not evidence.TA_minus_ERA5_C.gt(0).all() or
        not evidence.neighbor_continuity_with_tower_within3C.all() or
        evidence.isolated_tower_spike_candidate.any()):
        raise ValueError("Extreme-cold manual evidence does not meet approved case facts")
    if (not evidence.loc[evidence.site.isin(("US-EML","US-GLE")),
                         "TA_F_QC"].eq(0).all() or
        not evidence.loc[evidence.site.eq("US-ICt"),"TA_F_QC"].eq(2).all()):
        raise ValueError("Original QC composition changed since user's manual review")
    evidence["human_original_TA_decision"]=DECISION_63
    evidence["human_review_basis"]=SCIENCE_POLICY
    evidence["original_temperature_scientifically_accepted"]=True
    evidence["humidity_scientifically_released"]=False
    evidence["approved_for_DATM"]=False
    return evidence,pins

def combined():
    if (S56/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage56 incomplete")
    mf=S56/"policy_manifest.json"
    m=json.loads(mf.read_text())
    table=S56/S56_FILE
    if (m.get("schema")!="STAGE56_ORIGINAL_TA_UNDER8C_CDS_ERA5_POLICY_v1" or
        m.get("n_records")!=4884 or
        m.get("approved_for_DATM") is not False or
        m.get("all_science_forcing_HOLD") is not True or
        m.get("temperature_abs_difference_threshold_C")!=8 or
        m.get("output_sha256",{}).get(S56_FILE)!=sha(table)):
        raise ValueError("Stage56 immutable temperature decision ledger changed")
    for fname,digest in m.get("output_sha256",{}).items():
        if sha(S56/fname)!=digest:
            raise ValueError("Stage56 report SHA changed: "+fname)
    data=pd.read_csv(table,dtype={"site":str,"local":str})
    if len(data)!=4884 or Counter(data.site)!=Counter(STAGE11_SITES):
        raise ValueError("Stage56 source site populations changed")
    local=pd.to_datetime(data.local,errors="raise")
    if local.isna().any() or local.dt.tz is not None:
        raise ValueError("Invalid original EC local time")
    data["local_key"]=local.dt.strftime("%Y-%m-%d %H:%M")
    if data.duplicated(["site","local_key"]).any():
        raise ValueError("Duplicate Stage56 exact site/tower time")
    original_counts=Counter(data.temp_decision)
    if (original_counts.get(DECISION_3904)!=3904 or
        original_counts.get("HOLD_TA_DIFF_FROM_ERA5_GT8C")!=63 or
        original_counts.get(DECISION_HO1)!=917 or
        len(original_counts)!=3):
        raise ValueError("Stage56 pre-human-decision counts changed")
    evidence,pins=get_evidence()
    keys=set(zip(evidence.site,evidence.local))
    stage56_gt8=data.loc[data.temp_decision.eq("HOLD_TA_DIFF_FROM_ERA5_GT8C")]
    if set(zip(stage56_gt8.site,stage56_gt8.local_key))!=keys:
        raise ValueError("Manually reviewed 63 are not the exact Stage56 >8C events")
    verify=evidence.set_index(["site","local"])
    for _,z in stage56_gt8.iterrows():
        e=verify.loc[(z.site,z.local_key)]
        if (not np.isclose(float(z.TA_F),float(e.TA_F_C),atol=1e-8,rtol=0) or
            not np.isclose(float(z.ERA5_T2M_C),float(e.ERA5_T2M_C),
                           atol=1e-8,rtol=0) or
            not np.isclose(float(z.TA_F_QC),float(e.TA_F_QC),
                           atol=1e-8,rtol=0)):
            raise ValueError("Exact manual source temperature / ERA5 / QC mismatch")
    is63=pd.MultiIndex.from_frame(data[["site","local_key"]]).isin(
        pd.MultiIndex.from_frame(evidence[["site","local"]]))
    data["final_temperature_decision"]=data.temp_decision
    data.loc[is63,"final_temperature_decision"]=DECISION_63
    data["original_TA_F_retained"]=data.final_temperature_decision.isin(
        [DECISION_63,DECISION_3904])
    data["manual_T_A_approved_63"]=is63
    data["temperature_human_review_basis"]=np.where(
        is63,SCIENCE_POLICY,"STAGE56_ERA5_EIGHT_CELSIUS_SCREEN")
    data["humidity_science_HOLD"]=True
    data["phase_water_ice_caution_retained"]=data.phase_water_ice_review_required
    data["approved_for_DATM"]=False
    data["approved_for_spinup"]=False
    rh=pd.to_numeric(data.ERA5_RH_water_pct_selected,errors="coerce").to_numpy()
    t=pd.to_numeric(data.TA_F,errors="coerce").to_numpy()
    p=pd.to_numeric(data.PA_F,errors="coerce").to_numpy()
    with np.errstate(all="ignore"):
        v,q=water_pair(t,rh,p)
    eligible=data.original_TA_F_retained.to_numpy()
    numeric=(np.isfinite(v)&(v>=-0.005)&np.isfinite(q)&(q>0)&(q<.08)&
        np.isfinite(t)&(t>-80)&(t<65)&
        np.isfinite(p)&(p>50)&(p<110)&
        np.isfinite(rh)&(rh>0)&(rh<=100.05))
    if not numeric[eligible].all():
        raise ValueError("Some accepted original TA candidates have invalid RH/VPD/QBOT")
    data["temperature_accepted_RH_VPD_QBOT_numeric_candidate"]=eligible&numeric
    data["VPD_water_hPa_original_TA"]=np.where(eligible,v,np.nan)
    data["QBOT_kgkg_original_TA_PA"]=np.where(eligible,q,np.nan)
    pre=data.loc[data.temp_decision.eq(DECISION_3904)]
    if not (np.allclose(
            pre.VPD_water_hPa_original_TA,
            pd.to_numeric(pre.proposed_VPD_hPa_using_original_TA_F),
            atol=1e-7,rtol=1e-7) and
        np.allclose(
            pre.QBOT_kgkg_original_TA_PA,
            pd.to_numeric(pre.proposed_QBOT_kgkg_using_original_TA_F_PA_F),
            atol=1e-9,rtol=1e-7)):
        raise ValueError("Stage56 previously accepted original-T humidity was changed")
    counts=Counter(data.final_temperature_decision)
    if (counts.get(DECISION_3904)!=3904 or counts.get(DECISION_63)!=63
        or counts.get(DECISION_HO1)!=917 or len(counts)!=3
        or int(data.temperature_accepted_RH_VPD_QBOT_numeric_candidate.sum())!=3967):
        raise ValueError("3,967 accepted TA / 917 Ho1 HOLD balance differs")
    return data,evidence,{"stage56_csv_sha256":sha(table),
        "stage56_manifest_sha256":sha(mf),
        "stage57_original_sources":pins,
        "pinned_stage57_git_blob":S57_GIT_BLOB}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    ap.add_argument("--report-root",type=Path,default=ROOT/"reports")
    args=ap.parse_args()
    if args.self_test:return self_test()
    data,manual,pins=combined()
    summary=[]
    for site in STAGE11_SITES:
        d=data.loc[data.site.eq(site)]
        item={"site":site,"total":len(d),
            "keep_original_TA_within8C":int(d.final_temperature_decision.eq(DECISION_3904).sum()),
            "keep_original_TA_manual_extreme_cold":int(d.final_temperature_decision.eq(DECISION_63).sum()),
            "retained_original_TA_total":int(d.original_TA_F_retained.sum()),
            "still_HOLD_Ho1_provisional_UTC":int(d.final_temperature_decision.eq(DECISION_HO1).sum()),
            "numeric_RH_VPD_QBOT_candidates":int(d.temperature_accepted_RH_VPD_QBOT_numeric_candidate.sum())}
        summary.append(item)
        print("SITE",item)
    print("STAGE58 SOURCE CHECK PASS | SHA-pinned original source + Stage56 + Stage57 63 manual signoffs")
    print("TEMPERATURE_FINAL_DECISIONS",dict(Counter(data.final_temperature_decision)))
    print("TOTAL ORIGINAL EC TA_F RETAINED",int(data.original_TA_F_retained.sum()),"/4884")
    print("US-Ho1 PROVISIONAL OFFSET STILL HOLD",917)
    print("ALL HUMIDITY / WATER-ICE SCIENCE HOLD: NO FORCING APPROVAL")
    if args.check:
        print("STAGE58 CHECK PASS | no files written")
        return
    root=args.report_root.resolve()
    if root==S56 or S56 in root.parents:
        raise ValueError("Stage58 output must not be inside prior Stage56")
    dst=root/("stage58_63_manual_T_approved_3967_T_total_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dst.mkdir(parents=True,exist_ok=False)
    marker=dst/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Manual decision for original T only; no humidity/forcing release.\n")
    outputs={
       "63_original_tower_temperature_manual_acceptance.csv":manual,
       "4884_final_original_tower_temperature_policy.csv":data,
       "five_site_temperature_policy_summary.csv":pd.DataFrame(summary)}
    digests={}
    for filename,df in outputs.items():
        f=dst/filename
        df.to_csv(f,index=False)
        digests[filename]=sha(f)
    if sha(S56/S56_FILE)!=pins["stage56_csv_sha256"]:
        raise ValueError("Stage56 changed during output")
    manifest={"schema":"STAGE58_USER_MANUAL_EXTREME_COLD_TA_APPROVAL_ONLY_v1",
        "n_stage11_records":4884,"n_manual_T_approved":63,
        "n_within8C_T_retained":3904,"n_total_original_T_retained":3967,
        "n_Ho1_provisional_offset_hold":917,
        "operator_approved_temperature_review_only":True,
        "review_basis":SCIENCE_POLICY,
        "separate_stage53_444_RH_unchanged":True,
        "humidity_and_phase_science_HOLD":True,
        "approved_for_DATM":False,"approved_for_spinup":False,
        "source_sha256":pins,"report_sha256":digests,
        "no_original_or_model_forcing_edits":True}
    (dst/"manual_temperature_decision_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE58 AUDIT PASS | 63 human-accepted cold TA + 3904 prior retained = 3967")
    print("REPORT",dst)
    print("ONLY TEMPERATURE DECISIONS UPDATED IN ISOLATED LEDGER; NO FORCING CHANGES")
if __name__=="__main__":
    main()

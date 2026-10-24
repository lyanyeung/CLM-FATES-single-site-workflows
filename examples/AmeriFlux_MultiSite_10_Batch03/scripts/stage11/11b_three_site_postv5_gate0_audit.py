#!/usr/bin/env python3
"""Batch03 Stage11b — read-only Post-v5 Gate-0 audit for THREE numeric-only sites.

US-MOz, US-Mpj and US-NC2 have no Stage11a residual humidity blocker in the
seven-site 1924-event scope. This does NOT mean science sign-off or DATM ready.

Independently compare each Stage07 source-pinned native HH flux product with its
versioned processed_v5 CLM forcing candidate:
  - source and candidate hashes, audit, QC ledgers and noleap time axes;
  - original-to-final changes by meteorological field and QC0 provenance;
  - all core CLM column bounds, unit conversions, water RH and QBOT physics;
  - reported manual review, low-RH floor, ERA gapfilling and interpolations.

--self-test: pure synthetic algebra tests and failure detection, no disk access.
--check: full SHA and physical checks; stdout only, NO file changes.
--run: new isolated reports/stage11b_* folder for review CSV and SHA receipt.
NEVER removes Stage07 INCOMPLETE marker, writes forcing, approves Post-v5,
builds DATM, modifies CIME or submits Slurm jobs.
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

sys.dont_write_bytecode = True
VERSION = "stage11b-v1-20261024-three-numeric-site-gate0"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07 = ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11A = ROOT/"reports/stage11a_science_decision_matrix_20261024T064632Z_da305a30"
CLEAN = ("US-MOz","US-Mpj","US-NC2")
ALL_SITES = {"US-Kon","US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj",
             "US-MtB","US-NC2","US-NR1","US-NR3"}
RAW_VARS = ("TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
DERIVED = ("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms",
           "TA_USE","VPD_USE")
VALID_RANGES = {
    "TBOT":(180.,340.),"QBOT":(0.,0.08),"PSRF":(49000.,111000.),
    "FSDS":(0.,1600.),"FLDS":(0.,800.),"WIND":(0.,75.)
}


def file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Required regular file missing/symlink: "+str(p))
    return p


def directory(path):
    p=Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Required directory missing/symlink: "+str(p))
    return p


def sha(path):
    h=hashlib.sha256()
    with file(path).open("rb") as src:
        for block in iter(lambda:src.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def doc(path):
    return json.loads(file(path).read_text(encoding="utf-8"))


def numbers(series):
    x=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    x[(~np.isfinite(x))|(x<=-9990)]=np.nan
    return x


def checks_float(name,actual,want,rtol=1e-6,atol=1e-9):
    a=np.asarray(actual,dtype=float)
    b=np.asarray(want,dtype=float)
    ok=np.isclose(a,b,rtol=rtol,atol=atol,equal_nan=False)
    if a.shape!=b.shape or not ok.all():
        raise ValueError(f"{name} conversion mismatch: {int((~ok).sum())} records")


def noleap_times(start,end,step):
    if step not in (30,60) or start<1900 or end<start or end>2100:
        raise ValueError("Invalid source year or native interval")
    expected=pd.date_range(f"{start}-01-01",f"{end+1}-01-01",
                           freq=f"{step}min",inclusive="left")
    return expected[~((expected.month==2)&(expected.day==29))]


def humid_physics(df):
    missing=set(DERIVED)-set(df.columns)
    if missing:
        raise ValueError("Incomplete processed_v5 columns: "+str(sorted(missing)))
    v={k:numbers(df[k]) for k in DERIVED}
    n=len(df)
    for k,arr in v.items():
        if not np.isfinite(arr).all():
            raise ValueError("Nonfinite candidate forcing values: "+k)
    for k,(lo,hi) in VALID_RANGES.items():
        if not (v[k]>=lo).all() or not (v[k]<=hi).all():
            raise ValueError("Out-of-range model forcing: "+k)
    checks_float("TBOT",v["TBOT"],v["TA_USE"]+273.15,
                 rtol=1e-10,atol=1e-9)
    with np.errstate(all="ignore"):
        es=611.2*np.exp(17.67*v["TA_USE"]/(v["TA_USE"]+243.5))
        ea=es-100*v["VPD_USE"]
        rh=100*ea/es
        q=.622*ea/(v["PSRF"]-.378*ea)
    valid=np.isfinite(rh)&np.isfinite(q)&(ea>0)&(rh>0)&(rh<=100.05)
    if not valid.all():
        raise ValueError(f"Candidate negative/invalid vapour pressure or RH: {(~valid).sum()} rows")
    if (v["VPD_USE"] < -1e-9).any() or (v["PRECTmms"] < -1e-12).any():
        raise ValueError("Candidate negative VPD or precipitation")
    if not (v["PRECTmms"] <= 300/1800+1e-9).all():
        raise ValueError("Candidate precipitation rate far above native physical maximum")
    checks_float("QBOT",v["QBOT"],q,rtol=1e-6,atol=1e-10)
    if not (v["QBOT"]>=0).all():
        raise ValueError("Negative model QBOT")
    return {
        "rows":n,"min_rh_water_pct":float(np.min(rh)),
        "max_rh_water_pct":float(np.max(rh)),
        "min_implied_ea_Pa":float(np.min(ea)),
        "min_QBOT_kgkg":float(np.min(v["QBOT"])),
        "max_QBOT_kgkg":float(np.max(v["QBOT"])),
        "nonfinite_model_values":0,
        "negative_vapour_rows":0,
        "phase_convention":"liquid-water saturation only; ice-specific QC and height/clock remain scientific holds"
    },v


def validate_manifest():
    for p in (ROOT,S07,S11A):
        directory(p)
    file(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    stage11=doc(S11A/"scientific_hold_receipt.json")
    if (stage11.get("script_version")!="stage11a-v1-20261024"
        or stage11.get("events")!=1924 or stage11.get("affected_site_years")!=32
        or stage11.get("batch_sites")!=10
        or stage11.get("zero_automatic_approvals") is not True
        or stage11.get("post_v5_approvals")!=0
        or stage11.get("DATM_ready_sites")!=0
        or stage11.get("spinup_authorizations")!=0):
        raise ValueError("Stage11a latest science hold has changed")
    stage11_out=stage11.get("output_SHA256",{})
    expected_a={
       "1924_source_event_science_review.csv",
       "32_site_year_science_decision_matrix.csv",
       "10_site_post_v5_readiness.csv",
       "REVIEW_GUIDE.md"}
    if set(stage11_out)!=expected_a:
        raise ValueError("Stage11a SHA receipt schema differs")
    for name in expected_a:
        if sha(S11A/name)!=stage11_out[name]:
            raise ValueError("Stage11a sealed report SHA differs: "+name)
    snap=pd.read_csv(file(S11A/"10_site_post_v5_readiness.csv"))
    if len(snap)!=10 or snap.site.duplicated().any() or set(snap.site)!=ALL_SITES:
        raise ValueError("Stage11a ten-site status inventory differs")
    selected=snap.loc[snap.site.isin(CLEAN)].copy()
    if (len(selected)!=3 or selected.stage11a_blockers.sum()!=0
        or not selected.stage07_state.eq("NUMERIC_ONLY_CANDIDATE_POSTV5_NOT_APPROVED").all()
        or not selected.post_v5_ready.astype(str).str.lower().eq("false").all()):
        raise ValueError("Stage11a clean-candidate status changed")
    manifest=doc(S07/"exact_input_manifest.json")
    if stage11.get("input_SHA256",{}).get("Stage07_manifest")!=sha(S07/"exact_input_manifest.json"):
        raise ValueError("Stage07 input manifest not pinned to Stage11a")
    inputpins={str(Path(p).resolve()):h for p,h in manifest["input_sha256"].items()}
    specs={a["site"]:a for a in manifest["sites"]}
    if len(specs)!=10 or set(specs)!=ALL_SITES:
        raise ValueError("Original Stage07 site list differs")
    preservation=doc(S07/"input_preservation_check.json")
    if preservation.get("unchanged") is not True or preservation.get("changed_inputs")!=[]:
        raise ValueError("Stage07 originally changed input sources")
    run=pd.read_csv(file(S07/"candidate_run_summary.csv"))
    if len(run)!=10 or run.site.duplicated().any() or set(run.site)!=ALL_SITES:
        raise ValueError("Stage07 run result site inventory differs")
    for site in CLEAN:
        row=run.loc[run.site.eq(site)]
        if len(row)!=1 or row.status.iloc[0]!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
            raise ValueError("Expected Stage07 numeric result missing: "+site)
    # Stage07 seals all staged output artifacts prior to writing this manifest.
    outputs=doc(S07/"output_sha256.json")
    if not isinstance(outputs,dict) or len(outputs)==0:
        raise ValueError("Stage07 output SHA manifest missing")
    for name in ("candidate_run_summary.csv","input_preservation_check.json"):
        if sha(S07/name)!=outputs.get(name):
            raise ValueError("Stage07 main report changed: "+name)
    return specs,inputpins,outputs,stage11


def raw_compare(spec,forcing,model,events,status):
    site=spec["site"]
    first=int(spec["first_year"])
    last=int(spec["last_year"])
    step=int(spec["native_minutes"])
    path=file(spec["primary"])
    cols=set(pd.read_csv(path,nrows=0).columns)
    if not {"TIMESTAMP_START",*RAW_VARS}.issubset(cols):
        raise ValueError("Original source lacks required seven variables: "+site)
    qc_cols=[var+"_QC" for var in RAW_VARS if var+"_QC" in cols]
    raw=pd.read_csv(path,usecols=["TIMESTAMP_START",*RAW_VARS,*qc_cols],
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    native=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    subset=native.dt.year.between(first,last)&~((native.dt.month==2)&(native.dt.day==29))
    raw=raw.loc[subset].copy()
    raw["time"]=native.loc[subset]
    raw=raw.sort_values("time").reset_index(drop=True)
    expected=noleap_times(first,last,step)
    times=pd.to_datetime(forcing["time"],errors="raise")
    if (len(raw)!=len(expected) or len(forcing)!=len(expected)
        or not np.array_equal(raw.time.to_numpy(),expected.to_numpy())
        or not np.array_equal(times.to_numpy(),expected.to_numpy())):
        raise ValueError("NO_LEAP original-to-forcing chronology mismatch: "+site)
    native_source={
        "TA_F":model["TA_USE"],
        "VPD_F":model["VPD_USE"],
        "PA_F":model["PSRF"]/1000.,
        "SW_IN_F":model["FSDS"],
        "LW_IN_F":model["FLDS"],
        "WS_F":model["WIND"],
        "P_F":model["PRECTmms"]*step*60,
    }
    change={}
    changed_qc0=0
    for var in RAW_VARS:
        src=numbers(raw[var])
        dest=native_source[var]
        bad=~np.isclose(src,dest,rtol=1e-10,atol=1e-9,equal_nan=True)
        change[var]=int(bad.sum())
        if var+"_QC" in raw:
            qc=numbers(raw[var+"_QC"])
            changed_qc0+=int((bad&(qc==0)).sum())
    total=sum(change.values())
    if (total!=int(status["changes"]) or total!=len(events)
        or changed_qc0!=int(status["changed_QC0_records"])):
        raise ValueError("Unreconciled Stage07 raw-to-candidate changes: "+site)
    if "variable" not in events or events.variable.value_counts().to_dict()!={
            v:n for v,n in change.items() if n>0}:
        raise ValueError("Per-variable event ledger differs from raw-to-candidate changes")
    if len(events)>0:
        if events.duplicated(["time","variable"]).any():
            raise ValueError("Duplicate replacement event in source ledger")
        dates=set(pd.to_datetime(events.time,errors="raise"))
        if not dates.issubset(set(expected)):
            raise ValueError("Unknown replacement event time")
    return change,changed_qc0,len(raw)


def audit_site(site,spec,inputpins,outputs):
    first,last,step=(int(spec[k]) for k in ("first_year","last_year","native_minutes"))
    if step!=30 or first>last:
        raise ValueError("Unexpected native site interval in three candidates: "+site)
    for source_type in ("primary","era"):
        p=file(spec[source_type])
        if p.parent.name!=spec["release"] or p.parent.parent.name!="raw":
            raise ValueError("Source release path modified: "+str(p))
        if sha(p)!=inputpins.get(str(p.resolve()),""):
            raise ValueError("Stage07 input SHA mismatch: "+str(p))
    base=Path(site)/"forcing"
    force_name=f"{site}_CLM_forcing_{first}_{last}.csv"
    items={
        "forcing":str(base/"processed_v5"/force_name),
        "events":str(base/"qc_v5"/f"{site}_replacement_events.csv"),
        "manual":str(base/"qc_v5"/f"{site}_manual_review.csv"),
        "status":str(base/"qc_v5"/f"{site}_status.json"),
        "independent":str(base/"qc_v5"/f"{site}_independent_audit.json"),
    }
    for item in items.values():
        if item not in outputs or sha(S07/item)!=outputs[item]:
            raise ValueError("Stage07 candidate output hash not pinned: "+item)
    status=doc(S07/items["status"])
    audited=doc(S07/items["independent"])
    if (status.get("site")!=site or audited.get("site")!=site
        or audited.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED"):
        raise ValueError("Stage07 candidate status does not match: "+site)
    forced=pd.read_csv(file(S07/items["forcing"]),low_memory=False)
    if "time" not in forced:
        raise ValueError("Missing force time column")
    physics,model=humid_physics(forced)
    events=pd.read_csv(file(S07/items["events"]),low_memory=False)
    manual=pd.read_csv(file(S07/items["manual"]),low_memory=False)
    if (len(events)!=int(status["changes"]) or
        len(manual)!=int(status["manual_review_records"])):
        raise ValueError("Manual/replacement ledger differs from source status: "+site)
    change,qc0,rows=raw_compare(spec,forced,model,events,audited)
    if (rows!=int(audited["noleap_rows"]) or
        len(manual)!=int(audited["manual_review_records"]) or
        int(audited["ERA_RH_floor_records"])<0):
        raise ValueError("Stage07 independent numeric audit differs: "+site)
    floor=int(audited["ERA_RH_floor_records"])
    return {
        "site":site,"first_year":first,"last_year":last,
        "native_minutes":step,"noleap_rows":rows,
        "stage07_numeric_ok":True,
        "raw_to_candidate_changes":len(events),
        "changed_original_QC0_records":qc0,
        "manual_review_records":len(manual),
        "ERA_RH_floor_records":floor,
        "short_interpolation_variable_records":int(audited["short_interpolation_variable_records"]),
        "ERA_replacement_variable_records":int(audited["ERA_replacement_variable_records"]),
        "ERA_RH_reconstruction_variable_records":int(audited["ERA_RH_reconstruction_variable_records"]),
        "met_field_change_counts":json.dumps(change,sort_keys=True),
        "min_RH_water_pct":physics["min_rh_water_pct"],
        "max_RH_water_pct":physics["max_rh_water_pct"],
        "min_implied_ea_Pa":physics["min_implied_ea_Pa"],
        "min_QBOT_kgkg":physics["min_QBOT_kgkg"],
        "max_QBOT_kgkg":physics["max_QBOT_kgkg"],
        "full_water_physics_pass":True,
        "source_and_candidate_sha_pass":True,
        "QC0_replacement_review_required":qc0>0,
        "source_and_phase_signoff_required":True,
        "clock_metadata_approved":False,
        "ice_phase_approved":False,
        "PFT_science_approved":False,
        "CO2_protocol_approved":False,
        "post_v5_approved":False,
        "DATM_ready":False,
        "spinup_authorized":False,
        "review_outcome":"NUMERICALLY_CONSISTENT_BUT_SCIENTIFIC_REVIEW_HOLD",
        "candidate_reference":str(S07/items["forcing"])
    }


def self_test():
    t=np.array([-12.,5.])
    es=611.2*np.exp(17.67*t/(t+243.5))
    ea=np.array([120.,600.])
    v=(es-ea)/100.
    p=np.array([90000.,101000.])
    q=.622*ea/(p-.378*ea)
    df=pd.DataFrame({
        "time":["2020-01-01 00:00:00","2020-01-01 00:30:00"],
        "TA_USE":t,"VPD_USE":v,"TBOT":t+273.15,
        "PSRF":p,"QBOT":q,"FSDS":[0.,200.],
        "FLDS":[220.,320.],"WIND":[1.,2.],
        "PRECTmms":[0.,0.]
    })
    good,_=humid_physics(df)
    assert good["rows"]==2 and good["negative_vapour_rows"]==0
    broken=df.copy()
    broken.loc[0,"VPD_USE"]=15
    try:
        humid_physics(broken)
    except ValueError:
        pass
    else:
        raise AssertionError("Negative water vapour pressure not rejected")
    assert len(noleap_times(2020,2020,30))==17520
    assert len(noleap_times(2020,2020,60))==8760
    print("STAGE11B SELF-TEST PASS: subzero humidity, QBOT/TBOT, invalid VPD rejection, NO_LEAP cadence",flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    opt=ap.add_mutually_exclusive_group(required=True)
    opt.add_argument("--self-test",action="store_true")
    opt.add_argument("--check",action="store_true")
    opt.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11B — THREE-SITE POST-V5 GATE0 | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    specs,pins,outputs,receipt=validate_manifest()
    results=[]
    for site in CLEAN:
        result=audit_site(site,specs[site],pins,outputs)
        print(f"STAGE11B SITE {site}: noleap_rows={result['noleap_rows']} "
              f"changes={result['raw_to_candidate_changes']} "
              f"changed_QC0={result['changed_original_QC0_records']} "
              f"manual={result['manual_review_records']} "
              f"ERA_RH_floor={result['ERA_RH_floor_records']} "
              "numeric_pass=True post_v5_approved=False",flush=True)
        results.append(result)
    summary=pd.DataFrame(results)
    if (len(summary)!=3 or not summary.site.eq(pd.Series(CLEAN)).all()
        or summary.post_v5_approved.any() or summary.DATM_ready.any()):
        raise ValueError("Unexpected three-site Post-v5 approval or result order")
    print("\n========== THREE NUMERIC CANDIDATE GATE0 SUMMARY ==========",flush=True)
    show=["site","noleap_rows","raw_to_candidate_changes",
          "changed_original_QC0_records","manual_review_records",
          "ERA_RH_floor_records","ERA_replacement_variable_records",
          "min_RH_water_pct","post_v5_approved","DATM_ready"]
    print(summary[show].to_string(index=False),flush=True)
    print("\nSTAGE11B SUMMARY: candidate_sites=3/3 numeric_audit=3/3 "
          "postv5_approvals=0 DATM_ready=0 spinup_authorizations=0",flush=True)
    if args.check:
        print("CHECK ONLY: no new output or source writes.",flush=True)
        return
    out=ROOT/"reports"/("stage11b_postv5_gate0_three_sites_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    target="three_numeric_site_gate0_review.csv"
    summary.to_csv(out/target,index=False)
    guide="""# Post-v5 Stage11b Gate-0 — DO NOT USE FOR MODEL

This checks existing Stage07 numeric-only output at US-MOz, US-Mpj, US-NC2
against original release files and existing Stage11a science holds.

Stage07 raw changes can include QC0 changes, ERA gapfills, RH reconstructions,
and short interpolations. Every modified value requires per-event provenance
review: numeric/physical checks do not establish that the proposed value is
the true meteorology at the EC tower. Verify cold-season water-vs-ice
saturation conventions, measurements, clock offsets, site and model height,
PFT surface representation and fixed/transient CO2 policy separately.

Stage07 INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP stays present because the
other seven sites remain humidity blocked. No candidate is production ready.
No scripts in this stage write original or processed forcing.
"""
    (out/"REVIEW_HOLD.md").write_text(guide,encoding="utf-8")
    seal={
        "version":VERSION,"sites":list(CLEAN),"numerically_checked":3,
        "source_stage07_manifest_sha256":sha(S07/"exact_input_manifest.json"),
        "stage07_output_receipt_sha256":sha(S07/"output_sha256.json"),
        "source_stage11a_receipt_sha256":sha(S11A/"scientific_hold_receipt.json"),
        "repairs_approved":0,"clock_approved":0,"post_v5_approved":0,
        "DATM_ready_sites":0,"spinup_authorizations":0,
        "stage07_incomplete_marker_still_required":True,
        "output_sha256":{p:sha(out/p) for p in (target,"REVIEW_HOLD.md")}
    }
    (out/"scientific_hold_receipt.json").write_text(json.dumps(seal,indent=2)+"\n")
    print("STAGE11B REPORT DIR:",out,flush=True)
    print("REPORT ONLY — NO original/candidate forcing, DATM, CIME, restart or Slurm changes.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE11B STOP:",str(exc),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

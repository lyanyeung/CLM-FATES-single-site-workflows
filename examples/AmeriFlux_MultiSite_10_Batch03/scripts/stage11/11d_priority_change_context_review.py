#!/usr/bin/env python3
"""Batch03 Stage11d — source-grounded closeout packet for 3 Stage07 candidates.

Scope: six changed QC0 TA, 38 source-ERA replacements, five RH<1% native
rows, and all 18 manual review notes. Some events overlap. Every target is
associated with +/-2h of native FLUXMET values, source QC, companion ERA
and processed_v5 candidate. The panel does not approve any repair.

--self-test synthetic tests only (no IRIDIS reads or writes).
--check SHA chain, exact native timestamp joins, event/QC counts and context;
        never writes files.
--run   new isolated report folder and SHA receipt only.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11d-v1-20261024-priority-context"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S11C=ROOT/"reports/stage11c_qc0_manual_review_20261024T071530Z_ce6fdbb8"
UPSTREAM=Path(__file__).with_name("11c_qc0_manual_era_change_review.py")
UPSTREAM_GIT_BLOB="2e7402fc67fabe34aeeb990d98117730bcbbddfa"
SITES=("US-MOz","US-Mpj","US-NC2")
KEYS=("site","native_key","variable")
C_FILES={
    "105_exact_source_to_candidate_changes.csv",
    "6_original_QC0_modified_events.csv",
    "18_manual_review_entries.csv",
    "positive_RH_below_1pct_diagnostics.csv",
    "three_site_change_source_summary.csv",
    "SCIENTIFIC_REVIEW_REQUIRED.md"
}


def readfile(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/unsafe regular file: "+str(p))
    return p


def readdir(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing/unsafe directory: "+str(p))
    return p


def sha256(path):
    h=hashlib.sha256()
    with readfile(path).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()


def git_blob(path):
    b=readfile(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()


def get_json(path):
    return json.loads(readfile(path).read_text(encoding="utf-8"))


def load_stage11c():
    if git_blob(UPSTREAM)!=UPSTREAM_GIT_BLOB:
        raise ValueError("Local Stage11c dependency Git blob changed; download exact pinned Stage11c")
    spec=importlib.util.spec_from_file_location("batch03_stage11c_science",UPSTREAM)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.VERSION!="stage11c-v1-20261024-event-evidence":
        raise ValueError("Unrecognized Stage11c source-audit version")
    return module


def prior_gate():
    for p in (ROOT,S07,S11C):
        readdir(p)
    readfile(S07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    rec=get_json(S11C/"read_only_scientific_hold_receipt.json")
    if (rec.get("version")!="stage11c-v1-20261024-event-evidence"
        or rec.get("sites")!=list(SITES)
        or rec.get("changes")!=105 or rec.get("source_QC0_changes")!=6
        or rec.get("manual_rows")!=18
        or rec.get("ERA_replacement_variable_records")!=38
        or rec.get("approved_repairs")!=0 or rec.get("approved_Postv5")!=0
        or rec.get("DATM_ready_sites")!=0 or rec.get("spinup_authorizations")!=0
        or rec.get("Stage07_manifest_SHA256")!=sha256(S07/"exact_input_manifest.json")
        or rec.get("Stage07_sealed_outputs_SHA256")!=sha256(S07/"output_sha256.json")
        or set(rec.get("output_sha256",{}))!=C_FILES):
        raise ValueError("Stage11c SHA provenance or no-approval state differs")
    for name in C_FILES:
        if sha256(S11C/name)!=rec["output_sha256"][name]:
            raise ValueError("Stage11c report hash changed: "+name)
    def csv(name):
        return pd.read_csv(readfile(S11C/name),
                           dtype={"timestamp_start_native":str},
                           low_memory=False)
    changes=csv("105_exact_source_to_candidate_changes.csv")
    manual=csv("18_manual_review_entries.csv")
    dry=csv("positive_RH_below_1pct_diagnostics.csv")
    if (len(changes)!=105 or len(manual)!=18 or len(dry)!=5
        or changes.duplicated(["site","timestamp_start_native","variable"]).any()):
        raise ValueError("Stage11c detailed source event totals differ")
    return changes,manual,dry,rec


def key_for_time(raw_time):
    return pd.Timestamp(raw_time).strftime("%Y%m%d%H%M")


def flags_bool(df,key):
    txt=df[key].astype(str).str.lower().str.strip()
    if not txt.isin(["true","false"]).all():
        raise ValueError("Source boolean syntax changed: "+key)
    return txt.eq("true").to_numpy(dtype=bool)


def select_targets(events,manual,dry):
    """Priority flags are nonexclusive; exactly one target per site,time,variable."""
    problems=defaultdict(set)
    for r in events.itertuples(index=False):
        site=r.site;key=r.timestamp_start_native;var=r.variable
        if str(r.original_QC0_modified).lower()=="true":
            problems[(site,key,var)].add("CHANGED_ORIGINAL_QC0")
        if str(r.final_source)=="secondary_era_replacement":
            problems[(site,key,var)].add("ERA_SOURCE_REPLACEMENT")
    for r in manual.itertuples(index=False):
        problems[(r.site,key_for_time(r.time),r.variable)].add("MANUAL_REVIEW")
    for r in dry.itertuples(index=False):
        problems[(r.site,key_for_time(r.time),"VPD_F")].add("POSITIVE_RH_BELOW_1PCT")
    result=[]
    order=("CHANGED_ORIGINAL_QC0","ERA_SOURCE_REPLACEMENT",
           "POSITIVE_RH_BELOW_1PCT","MANUAL_REVIEW")
    for (site,key,var),flags in sorted(problems.items()):
        result.append(dict(site=site,native_key=key,variable=var,
            reasons="|".join(flag for flag in order if flag in flags),
            n_reason_flags=len(flags),
            scientific_status="REVIEW_REQUIRED_NO_APPROVAL",
            accepted_forcing=False))
    return pd.DataFrame(result,columns=[
        "site","native_key","variable","reasons","n_reason_flags",
        "scientific_status","accepted_forcing"
    ])


def source_value(row,name):
    try:
        x=float(row[name])
        return x if np.isfinite(x) and x>-9990 else np.nan
    except (TypeError,ValueError,KeyError):
        return np.nan


def panel(site,raw,force,era,targets,halfsteps=4):
    if len(raw)!=len(force) or not raw.native_key.equals(force.native_key):
        raise ValueError("Source and Stage07 forcing native timestamps differ")
    era_idx=era.set_index("TIMESTAMP_START",verify_integrity=True)
    index={stamp:i for i,stamp in enumerate(raw.native_key)}
    rows=[]
    for target in targets.itertuples(index=False):
        key=target.native_key
        if key not in index:
            raise ValueError("Review target missing original source time: "+site+" "+key)
        centre=index[key]
        start=max(0,centre-halfsteps)
        stop=min(len(raw),centre+halfsteps+1)
        for i in range(start,stop):
            stamp=raw.native_key.iloc[i]
            rr=raw.iloc[i]
            ff=force.iloc[i]
            original_era=era_idx.loc[stamp] if stamp in era_idx.index else None
            row={
                "target_site":site,"target_native_time":key,
                "target_variable":target.variable,"target_reasons":target.reasons,
                "offset_half_hours":i-centre,
                "context_native_time":stamp,
                "source_TA_C":source_value(rr,"TA_F"),
                "source_TA_QC":source_value(rr,"TA_F_QC"),
                "source_VPD_hPa":source_value(rr,"VPD_F"),
                "source_VPD_QC":source_value(rr,"VPD_F_QC"),
                "source_PA_kPa":source_value(rr,"PA_F"),
                "candidate_TA_C":source_value(ff,"TA_USE"),
                "candidate_VPD_hPa":source_value(ff,"VPD_USE"),
                "candidate_QBOT_kgkg":source_value(ff,"QBOT"),
                "ERA_TA_C":source_value(original_era,"TA_ERA") if original_era is not None else np.nan,
                "ERA_VPD_hPa":source_value(original_era,"VPD_ERA") if original_era is not None else np.nan,
                "ERA_exact_timestamp_available":original_era is not None,
                "accepted_forcing":False
            }
            rows.append(row)
    return pd.DataFrame(rows)


def outcome(events,manual,dry,targets,panels):
    qc0=events.loc[flags_bool(events,"original_QC0_modified")].copy()
    eras=events.loc[events.final_source.eq("secondary_era_replacement")].copy()
    if (len(qc0)!=6 or set(qc0.variable)!={"TA_F"}
        or len(eras)!=38 or len(manual)!=18 or len(dry)!=5):
        raise ValueError("Priority scope changed since Stage11c operator log")
    # Source VPD/QC and candidate met panel are evidence, not approval.
    erased_numeric=pd.to_numeric(eras.source_value,errors="coerce")
    if not np.isfinite(erased_numeric).all():
        raise ValueError("Unexpected Stage11c record has missing source: review ERA category")
    if not panels.loc[panels.offset_half_hours.eq(0),"ERA_exact_timestamp_available"].all():
        raise ValueError("One or more priority event ERA timestamps fail exact pairing")
    unchanged=manual.loc[~flags_bool(manual,"same_variable_changed_in_final")]
    if len(unchanged)!=4:
        raise ValueError("Stage11c manual unchanged count no longer four")
    totals=targets.groupby("site").agg(
        unique_review_targets=("variable","size"),
        overlap_extra_reason_flags=("n_reason_flags",lambda x:int((x-1).sum()))
    ).reset_index()
    return qc0,eras,unchanged,totals


def self_test():
    events=pd.DataFrame([{
        "site":"US-MOz","timestamp_start_native":"202001010030",
        "variable":"TA_F","original_QC0_modified":True,
        "final_source":"local_short_interpolation"
    },{
        "site":"US-MOz","timestamp_start_native":"202001010100",
        "variable":"VPD_F","original_QC0_modified":False,
        "final_source":"secondary_era_replacement"
    }])
    man=pd.DataFrame([{"site":"US-MOz","time":"2020-01-01T00:30:00",
                      "variable":"TA_F","same_variable_changed_in_final":True}])
    dry=pd.DataFrame([{"site":"US-MOz","time":"2020-01-01T01:00:00"}])
    targets=select_targets(events,man,dry)
    assert len(targets)==2 and targets.n_reason_flags.sum()==4
    assert set(targets.variable)=={"TA_F","VPD_F"}
    raw=pd.DataFrame({
        "native_key":["202001010000","202001010030","202001010100"],
        "TA_F":[4.,-20.,6.],"TA_F_QC":[0,0,0],
        "VPD_F":[1.,1.5,2.],"VPD_F_QC":[2,2,2],
        "PA_F":[98.,98.,98.]
    })
    forcing=pd.DataFrame({
        "native_key":raw.native_key,
        "TA_USE":[4.,5.,6.],"VPD_USE":[1.,1.5,0.8],
        "QBOT":[0.01]*3
    })
    era=pd.DataFrame({
        "TIMESTAMP_START":raw.native_key,
        "TA_ERA":[4.,5.,6.],"VPD_ERA":[1.,1.5,0.8]
    })
    p=panel("US-MOz",raw,forcing,era,targets,halfsteps=1)
    assert len(p)==5 and int((p.offset_half_hours==0).sum())==2
    assert p.ERA_exact_timestamp_available.all()
    assert source_value(raw.iloc[1],"TA_F")==-20.
    print("STAGE11D SELF-TEST PASS: nonexclusive target flags, native contextual rows, ERA literal joins",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=parser.parse_args()
    print("STAGE11D — THREE-SITE PRIORITY SOURCE CONTEXT | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    c=load_stage11c()
    events,manual,dry,prior=prior_gate()
    specs,pins,seals,_=c.load_and_verify_inputs()
    targets=select_targets(events,manual,dry)
    if targets.empty or targets.duplicated(list(KEYS)).any():
        raise ValueError("Duplicate or missing review targets")
    pieces=[]
    for site in SITES:
        spec=specs[site]
        raw,force,era,changes,review,lowrh,decisions,status,audit=c.read_site(
            site,spec,pins,seals)
        # Reuse the audited source/event joins; a stale local Stage11c cannot
        # silently produce a new decision if its Git blob differs.
        detailed=c.event_audit(site,raw,force,era,changes,review)
        if (len(detailed)!=len(events.loc[events.site.eq(site)])
            or int(detailed.original_QC0_modified.sum())!=int(
                flags_bool(events.loc[events.site.eq(site)],"original_QC0_modified").sum())):
            raise ValueError("Recomputed Stage11c event/QC ledger differs: "+site)
        current=targets.loc[targets.site.eq(site)]
        p=panel(site,raw,force,era,current)
        if len(p)<len(current):
            raise ValueError("Failed review context assembly: "+site)
        pieces.append(p)
        print(f"STAGE11D SOURCE {site}: targets={len(current)} "
              f"context_rows={len(p)} exact_ERA_centres="
              f"{int(p.loc[p.offset_half_hours.eq(0),'ERA_exact_timestamp_available'].sum())}",
              flush=True)
    context=pd.concat(pieces,ignore_index=True)
    qc0,era,unchanged,by_site=outcome(events,manual,dry,targets,context)
    era_reason_counts=era.groupby(["site","event_reason","original_source_QC"],
        dropna=False).size().rename("count").reset_index()
    print("\n========== SIX MEASURED QC0 TEMPERATURE CHANGES ==========",flush=True)
    print(qc0[["site","time","source_value","candidate_value",
               "source_ERA_same_timestamp","event_reason"]].to_string(index=False),flush=True)
    print("\n========== 38 ERA REPLACEMENTS: WHY SOURCE WAS OVERRIDDEN ==========",flush=True)
    print(era_reason_counts.to_string(index=False),flush=True)
    print("\n========== MANUAL REVIEW ENTRIES NOT CHANGED ==========",flush=True)
    print(unchanged[["site","time","variable","manual_reason",
                     "original_source_QC"]].to_string(index=False),flush=True)
    print("\n========== DISTINCT REVIEW TARGETS ==========",flush=True)
    print(by_site.to_string(index=False),flush=True)
    print(f"\nSTAGE11D SUMMARY: original_QC0_changes={len(qc0)}/6 "
          f"ERA_replacements={len(era)}/38 "
          f"manual_rows={len(manual)}/18 unchanged_manual={len(unchanged)}/4 "
          f"extreme_RH_lt1={len(dry)}/5 "
          f"distinct_review_targets={len(targets)} "
          "repair_approvals=0 postv5_approvals=0 DATM_ready=0",flush=True)
    if args.check:
        print("CHECK ONLY: no report files or forcing edits.",flush=True)
        return
    output=ROOT/"reports"/("stage11d_priority_source_context_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    output.mkdir(exist_ok=False)
    csvfiles={
        "priority_review_target_index.csv":targets,
        "plus_minus_2h_native_source_ERA_candidate_context.csv":context,
        "six_measured_QC0_changes.csv":qc0,
        "38_ERA_replacements_evidence.csv":era,
        "38_ERA_replacements_reason_counts.csv":era_reason_counts,
        "four_unmodified_manual_holds.csv":unchanged,
        "three_site_review_target_summary.csv":by_site
    }
    for name,df in csvfiles.items():
        df.to_csv(output/name,index=False)
    guide="""# Stage11d science review; no automated repair approval

This report preserves all six changed original measured-QC0 temperature values
and their +/-2h native meteorology, QC and companion ERA comparisons. A
larger source discrepancy is a hypothesis about isolated bad readings, not
independent certification of an interpolation-based replacement.

The 38 ERA replacement variables in US-NC2 were originally NUMERIC in the
source (as verified in Stage11c). Review event_reason, original source QC,
and why the engine invalidated/overwrote these rather than assuming source
missingness. An ERA candidate's presence is not independent tower support.

Preserve all 18 manual-review entries and five low-but-positive-RH readings;
four manual entries did not correspond to a final modified variable. Some
records overlap, and the distinct review target count is not the sum of four
categories. No flags in these sealed CSVs authorize writes or spinup.

Scientifically review source QC metadata, instrument logs if available,
tower/ERA time and elevation/height, cold-air saturation-water/ice phase,
PFT/surface, CO2 protocol and full-site forcing before Post-v5 acceptance.
Stage07 INCOMPLETE marker remains present. No DATM or CIME setup is approved.
"""
    (output/"SCIENTIFIC_HOLD.md").write_text(guide,encoding="utf-8")
    receipt={
        "version":VERSION,"stage11c_receipt_sha256":sha256(
            S11C/"read_only_scientific_hold_receipt.json"),
        "stage11c_script_git_blob":UPSTREAM_GIT_BLOB,
        "Stage07_manifest_SHA256":sha256(S07/"exact_input_manifest.json"),
        "original_measured_QC0_changes":6,"ERA_replacements":38,
        "manual_records":18,"unmodified_manual_records":4,
        "residual_RH_lt1_records":5,
        "unique_priority_targets":len(targets),
        "zero_approval":True,"postv5_approved":0,"DATM_ready":0,
        "source_or_forcing_modifications":False,
        "output_sha256":{name:sha256(output/name) for name in [*csvfiles,"SCIENTIFIC_HOLD.md"]}
    }
    (output/"read_only_provenance.json").write_text(json.dumps(receipt,indent=2)+"\n",
                                                     encoding="utf-8")
    print("STAGE11D REPORT DIR:",output,flush=True)
    print("NO SOURCE, QC-V5 FORCING, DATM, CIME CASE OR SLURM CHANGES.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as err:
        print("STAGE11D STOP:",str(err),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

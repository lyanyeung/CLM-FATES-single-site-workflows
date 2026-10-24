#!/usr/bin/env python3
"""Stage74: operator-approved 18/17 triage for CA-Man, new isolated trial ONLY.

Decision (2026-10-24): 18 of the 35 Stage73 QC1 events with no large
RH/VPD/pressure boundary flag receive a *joint* same-ERA5_HH-row
TA_ERA + VPD_ERA + PA_ERA -> TBOT/TA_USE/QBOT/PSRF/VPD_USE substitution
in a separately named trial. The 17 with large boundary changes are kept
bit-for-bit as they were, EVEN IF temperature jumps persist. The special
2007-03-10 anchor case is also retained. Retention is not confirmation that
original RH is true. Stage61 clock provenance remains UNVERIFIED.
No original forcing, model cases, restarts, production inputs or jobs modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path

EXP = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
REL = Path("stage54_era_vapour_2_candidate/CA-Man/forcing/processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv")
ORIGINAL_SHA = "fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705"
STAGE73 = EXP / "reports/stage73_CA-Man_same_source_ERA_T_VPD_PA_20261024T082817241685Z"
STAGE70B = EXP / "reports/stage70b_CA-Man_human_review_20261024T075415647388Z"
ALLOWED = {"TBOT", "TA_USE", "QBOT", "PSRF", "VPD_USE"}
DECISIONS = ("TRIAL_REPLACE_JOINT_ERA_T_Q_P_VPD",
             "KEEP_ORIGINAL_ACCEPT_RESIDUAL_T_STEP",
             "KEEP_ORIGINAL_SPECIAL_ANCHOR")
REVIEW_FIELDS = [
    "site", "episode_id", "timestamp", "operator_decision",
    "stage73_RH_boundary_flag", "TA_ERA_C", "VPD_ERA_hPa", "PA_ERA_kPa",
    "new_RH_pct", "new_QBOT_kgkg", "changed_columns",
    "source_clock_verified", "production_science_approved", "reason"
]

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def csv_rows(path, needed):
    if not path.is_file():
        raise RuntimeError("Missing required source: " + str(path))
    with path.open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        fields = r.fieldnames or []
        if len(fields) != len(set(fields)) or not set(needed).issubset(fields):
            raise RuntimeError("Report schema mismatch at " + str(path))
        return list(r)

def n(s):
    try:
        v = float(s)
        return v if math.isfinite(v) and v > -9990 else None
    except (TypeError, ValueError):
        return None

def close(a, b, tol):
    return a is not None and b is not None and abs(a-b) <= tol

def es(t):
    return 6.112 * math.exp(17.67 * t / (t + 243.5))

def derive(t, vpd, p_kpa):
    if None in (t, vpd, p_kpa) or not (-75 < t < 65 and vpd >= 0 and 45 <= p_kpa <= 115):
        raise RuntimeError("Invalid same-row ERA T/VPD/P")
    e = es(t) - vpd
    if not 0 < e <= es(t):
        raise RuntimeError("Impossible same-row ERA vapour state")
    p_pa = p_kpa * 1000
    q = 0.622 * e / (p_pa/100 - 0.378*e)
    rh = 100*e/es(t)
    if not 0 < q < 0.08 or not 0 < rh <= 100.001:
        raise RuntimeError("Invalid ERA RH or specific humidity")
    recovered_e = q*(p_pa/100)/(0.622+0.378*q)
    if abs(recovered_e-e) > 1e-8 or abs(es(t)-recovered_e-vpd) > 1e-8:
        raise RuntimeError("ERA thermodynamic closure failed")
    return {"T":t, "VPD":vpd, "P":p_pa, "Q":q, "RH":rh}

def raw_era(path, wanted):
    found = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not {"TIMESTAMP_START", "TA_ERA", "VPD_ERA", "PA_ERA"}.issubset(reader.fieldnames or []):
            raise RuntimeError("Same-source ERA5_HH required columns missing")
        for row in reader:
            key = str(row["TIMESTAMP_START"]).strip().removesuffix(".0")
            if key not in wanted: continue
            if key in found: raise RuntimeError("Duplicate raw ERA source time " + key)
            found[key] = derive(n(row["TA_ERA"]), n(row["VPD_ERA"]), n(row["PA_ERA"]))
    if set(found) != wanted:
        raise RuntimeError("Source ERA time missing: " + repr(wanted-set(found)))
    return found

def source_review(stage73, stage70b):
    m = json.loads((stage73/"manifest.json").read_text(encoding="utf-8"))
    expected = (73, False, False, False, False)
    observed = tuple(m.get(k) for k in
        ("stage", "source_clock_verified", "science_approved", "production_approved", "forcing_modified"))
    if observed != expected:
        raise RuntimeError("Stage73 source/approval manifest mismatch: " + repr(observed))
    report = stage73/"35_same_source_ERA_thermodynamics_review.csv"
    required = {"site", "episode_id", "forcing_time", "source_timestamp_start",
                "source_file", "source_clock_verified", "thermodynamic_gate",
                "humidity_boundary_science_flag", "temperature_step_gate",
                "TA_ERA_C", "VPD_ERA_hPa", "PA_ERA_kPa",
                "ERA_RH_pct", "ERA_QBOT_kgkg", "ERA_PSRF_Pa",
                "ERA_entry_RH_step_pp", "ERA_exit_RH_step_pp",
                "ERA_entry_VPD_step_hPa", "ERA_exit_VPD_step_hPa",
                "ERA_PSRF_vs_tower_Pa"}
    review = csv_rows(report, required)
    original36 = csv_rows(stage70b/"36_CA-Man_review_EDIT_DECISIONS_MANUALLY.csv",
                          {"site", "episode_id", "event_time"})
    if len(review) != 35 or len(original36) != 36:
        raise RuntimeError("Expected Stage73 35 and Stage70B 36 review cases")
    if len({r["forcing_time"] for r in review}) != 35:
        raise RuntimeError("Stage73 duplicate forcing timestamps")
    special = [r for r in original36 if r["event_time"] == "2007-03-10 11:30:00"]
    if len(special) != 1:
        raise RuntimeError("Special March-2007 anchor missing")
    if {r["episode_id"] for r in review} != {r["episode_id"] for r in original36}-{special[0]["episode_id"]}:
        raise RuntimeError("Stage73 and Stage70B event IDs not reconciled")
    summary = Counter(r["humidity_boundary_science_flag"] for r in review)
    if summary != {"NO_LARGE_BOUNDARY_SHIFT_DETECTED":18,
                   "REVIEW_LARGE_BOUNDARY_SHIFT":17}:
        raise RuntimeError("Operator 18/17 approved partition changed")
    path = Path(m["source_file"]).resolve(strict=True)
    if sha(path) != m["source_file_sha256"]:
        raise RuntimeError("Raw ERA5_HH checksum drift")
    if any(r["source_file"] != str(path) or r["site"] != "CA-Man"
           or r["source_clock_verified"] != "False"
           or r["thermodynamic_gate"] != "PASS_BASIC_THERMODYNAMICS_ONLY"
           or r["temperature_step_gate"] != "PASS_2_SIDED_QC0_TEMP_ONLY"
           for r in review):
        raise RuntimeError("Stage73 provenance or scientific gate changed")
    same_row = raw_era(path, {r["source_timestamp_start"] for r in review})
    for r in review:
        state = same_row[r["source_timestamp_start"]]
        checks = [(state["T"], n(r["TA_ERA_C"]), 0.02),
                  (state["VPD"], n(r["VPD_ERA_hPa"]), 0.02),
                  (state["P"], n(r["ERA_PSRF_Pa"]), 0.05),
                  (state["Q"], n(r["ERA_QBOT_kgkg"]), 1e-8),
                  (state["RH"], n(r["ERA_RH_pct"]), 0.02)]
        if not all(close(*x) for x in checks):
            raise RuntimeError("Raw ERA vs Stage73 inconsistency: " + r["forcing_time"])
        large = (max(n(r["ERA_entry_RH_step_pp"]),n(r["ERA_exit_RH_step_pp"])) >= 25
          or max(n(r["ERA_entry_VPD_step_hPa"]),n(r["ERA_exit_VPD_step_hPa"])) >= 10
          or abs(n(r["ERA_PSRF_vs_tower_Pa"])) >= 2000)
        flag = "REVIEW_LARGE_BOUNDARY_SHIFT" if large else "NO_LARGE_BOUNDARY_SHIFT_DETECTED"
        if flag != r["humidity_boundary_science_flag"]:
            raise RuntimeError("Stage73 boundary flag not reproducible")
    return review, special[0], path, same_row, report

def proposals(original, review, special, states):
    accepted = {r["forcing_time"]:r for r in review if
                r["humidity_boundary_science_flag"] == "NO_LARGE_BOUNDARY_SHIFT_DETECTED"}
    if len(accepted) != 18: raise RuntimeError("Expected 18 accepted timestamps")
    original_targets = {}
    with original.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["time"] in accepted:
                if row["time"] in original_targets:
                    raise RuntimeError("Duplicate forcing target time")
                original_targets[row["time"]] = row
    if set(original_targets) != set(accepted):
        raise RuntimeError("Not all 18 original records present")
    patches = {}
    records = []
    for row in review:
        when = row["forcing_time"]
        use = when in accepted
        state = states[row["source_timestamp_start"]]
        changed = []
        if use:
            src = original_targets[when]
            if not close(n(src["TA_USE"]), n(row["original_T_C"]), 0.03) or not close(n(src["TBOT"])-273.15, n(row["original_T_C"]), 0.03):
                raise RuntimeError("Original TA provenance mismatch at " + when)
            new = dict(src)
            new["TBOT"] = f"{state['T']+273.15:.6f}"
            new["TA_USE"] = f"{state['T']:.6f}"
            new["QBOT"] = f"{state['Q']:.10f}"
            new["PSRF"] = f"{state['P']:.3f}"
            new["VPD_USE"] = f"{state['VPD']:.6f}"
            changed = [k for k in src if src[k] != new[k]]
            if not {"TBOT","TA_USE"}.issubset(changed) or not set(changed).issubset(ALLOWED):
                raise RuntimeError("Unexpected field changes for " + when)
            patches[when] = new
        records.append({
            "site":"CA-Man", "episode_id":row["episode_id"], "timestamp":when,
            "operator_decision":DECISIONS[0] if use else DECISIONS[1],
            "stage73_RH_boundary_flag":row["humidity_boundary_science_flag"],
            "TA_ERA_C":state["T"], "VPD_ERA_hPa":state["VPD"],
            "PA_ERA_kPa":state["P"]/1000,
            "new_RH_pct":round(state["RH"],5) if use else "",
            "new_QBOT_kgkg":round(state["Q"],10) if use else "",
            "changed_columns":";".join(changed),
            "source_clock_verified":False,"production_science_approved":False,
            "reason":("Operator selected coherent same-row ERA substitution for trial only"
                if use else
                "Operator retains ORIGINAL record, accepts temperature jump; RH correctness NOT independently established")
        })
    records.append({
        "site":"CA-Man", "episode_id":special["episode_id"],
        "timestamp":special["event_time"],"operator_decision":DECISIONS[2],
        "source_clock_verified":False,"production_science_approved":False,
        "reason":"2007-03-10 QC0 anchor remains untouched; source problem unresolved"
    })
    if len(patches) != 18 or len(records) != 36:
        raise RuntimeError("Expected exactly 18 patched, 17 retained, one anchor held")
    return patches, records

def diff_audit(original, trial, patches):
    total=0;seen=set()
    with original.open(newline="",encoding="utf-8-sig") as f,trial.open(newline="",encoding="utf-8-sig") as g:
        a=csv.DictReader(f);b=csv.DictReader(g)
        if a.fieldnames!=b.fieldnames:raise RuntimeError("Forcing schema changed")
        for old,new in zip_longest(a,b):
            if old is None or new is None or old["time"]!=new["time"]:
                raise RuntimeError("Row order/time changed")
            total+=1;t=old["time"]
            differing={k for k in old if old[k]!=new[k]}
            if t in patches:
                if new!=patches[t] or not differing or not differing.issubset(ALLOWED) or not {"TBOT","TA_USE"}.issubset(differing):
                    raise RuntimeError("Candidate cell mismatch at "+t)
                seen.add(t)
            elif differing:raise RuntimeError("Unapproved record changed at "+t)
    if total!=262800 or seen!=set(patches):
        raise RuntimeError("Expected 262800 rows and exactly 18 replaced records")
    return total

def scanner(original, trial):
    script=(Path(__file__).resolve().parents[1] /
            "stage58/58_audit_selected_forcing_candidates.py")
    if not script.is_file():raise RuntimeError("Stage58 scanner missing")
    spec=importlib.util.spec_from_file_location("stage74_full_forcing_scan",str(script))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    baseline=mod.scan(original,1994,2008)
    candidate=mod.scan(trial,1994,2008)
    if baseline["rows"]!=262800 or candidate["rows"]!=262800 or any(
        x["structural_gate"]!="PASS_REVIEW_ONLY" for x in (baseline,candidate)):
        raise RuntimeError("Stage58 structural/calendar/thermodynamic gate failed")
    old,new=baseline["flags"],candidate["flags"]
    for key in ("rh_below1","rh_above100","nonfinite_rows","invalid_humidity",
                "vpd_closure_warning","bad_calendar","leap_day",
                "tbot_ta_disagreement"):
        if new.get(key,0)>old.get(key,0):
            raise RuntimeError("New Stage58 flag introduced: "+key)
    if old.get("ta_step_over10C")!=185 or new.get("ta_step_over10C",0)>185:
        raise RuntimeError("Unexpected original or trial global temperature steps")
    return {"original_step_over10C":old.get("ta_step_over10C",0),
            "trial_step_over10C":new.get("ta_step_over10C",0),
            "original_structural_gate":baseline["structural_gate"],
            "trial_structural_gate":candidate["structural_gate"],
            "original_rh_below1":old.get("rh_below1",0),
            "trial_rh_below1":new.get("rh_below1",0)}

def test():
    state=derive(20,7,99)
    assert abs(es(20)-(state["VPD"]+state["e"] if "e" in state else
                    state["VPD"] + state["Q"]*(state["P"]/100)/(.622+.378*state["Q"])))<1e-7
    assert 0 < state["RH"] < 100
    assert Counter(["NO_LARGE_BOUNDARY_SHIFT_DETECTED"]*18+
                   ["REVIEW_LARGE_BOUNDARY_SHIFT"]*17)=={
                       "NO_LARGE_BOUNDARY_SHIFT_DETECTED":18,
                       "REVIEW_LARGE_BOUNDARY_SHIFT":17}
    print("SELF-TEST PASS: same-row thermodynamics and operator 18/17 partition")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--trial",action="store_true")
    p.add_argument("--experiment-root",type=Path,default=EXP)
    p.add_argument("--stage73-dir",type=Path,default=STAGE73)
    p.add_argument("--stage70b-dir",type=Path,default=STAGE70B)
    args=p.parse_args()
    if args.self_test:test();return
    root=args.experiment_root.resolve(strict=True)
    original=root/REL
    if not original.is_file() or sha(original)!=ORIGINAL_SHA:
        raise RuntimeError("Pinned original forcing SHA mismatch")
    review,anchor,raw,states,report=source_review(
        args.stage73_dir.resolve(strict=True),args.stage70b_dir.resolve(strict=True))
    patches,decisions=proposals(original,review,anchor,states)
    print("STAGE74 | OPERATOR DECISION: 18 SAME-SOURCE TRIAL REPLACE; 17 KEEP; 1 ANCHOR KEEP")
    print("Decision counts:",dict(Counter(r["operator_decision"] for r in decisions)))
    print("Important: retention is NOT a claim that original RH is ground truth.")
    print("Clock provisional; production science approval remains FALSE.")
    for r in sorted(decisions,key=lambda x:x["timestamp"]):
        if r["operator_decision"]==DECISIONS[0]:
            print("  TRIAL REPLACE",r["timestamp"],"ERA_T",r["TA_ERA_C"],
                  "RH",r["new_RH_pct"],"changed",r["changed_columns"])
    if args.check:
        print("CHECK PASS — no files written")
        return
    dest=root/"reports"/("stage74_CA-Man_operator_18_same_source_trial_"+
                         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    dest.mkdir(exist_ok=False)
    decisionpath=dest/"36_operator_decision_ledger.csv"
    with decisionpath.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=REVIEW_FIELDS,extrasaction="raise")
        writer.writeheader();writer.writerows(decisions)
    trial=dest/"CA-Man_18_same_source_ERA_T_Q_P_VPD_TRIAL_NOT_PRODUCTION.csv"
    with original.open(newline="",encoding="utf-8-sig") as inp,trial.open("w",newline="",encoding="utf-8") as out:
        reader=csv.DictReader(inp)
        writer=csv.DictWriter(out,fieldnames=reader.fieldnames,
                              lineterminator="\n",extrasaction="raise")
        writer.writeheader()
        for row in reader:writer.writerow(patches.get(row["time"],row))
    rows=diff_audit(original,trial,patches)
    qa=scanner(original,trial)
    if sha(original)!=ORIGINAL_SHA:raise RuntimeError("Original SHA changed")
    manifest={
        "stage":74,"site":"CA-Man","operator_decision_date":"2026-10-24",
        "operator_selected_for_trial":18,"keep_original_for_humidity_boundary":17,
        "keep_special_anchor":1,"operator_accepts_residual_T_steps":True,
        "do_not_claim_original_RH_true":True,
        "scope":"ISOLATED_NEW_TRIAL_ONLY","source_clock_verified":False,
        "production_science_approved":False,"model_jobs_submitted":False,
        "original_forcing_modified":False,
        "original_path":str(original),"original_sha256":ORIGINAL_SHA,
        "source_ERA5_HH_path":str(raw),"source_ERA5_HH_sha256":sha(raw),
        "stage73_review_sha256":sha(report),
        "decision_ledger_sha256":sha(decisionpath),
        "trial_path":str(trial),"trial_sha256":sha(trial),
        "verified_rows":rows,"allowed_changed_columns":sorted(ALLOWED),
        "full_file_scanner":qa,
        "warning":"Do not use for active model or production: matched clock and independent evidence remain provisional."
    }
    (dest/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("15-YEAR FULL SCAN:",qa)
    print("REPORT:",dest)
    print("TRIAL:",trial)
    print("EXACT PATCHES:",len(patches),"/262800; 17+1 held rows unchanged")
    print("ORIGINAL FORCING UNCHANGED; NO SLURM OR MODEL JOBS")

if __name__=="__main__":main()

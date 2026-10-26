#!/usr/bin/env python3
"""Stage88: Batch02 priority human-science dossier, no forcing/model writes.

Reuse operator-verified Stage85 and Stage87. Collect the 24 ORIGINAL-QC0
Stage07 source edits and 274 original Ho1-2000 non-QC0 temperatures. Provide
measured-QC0 neighbors as context only, NOT inferred replacements.
Keep five Stage07 historical humidity blockers distinct from later shadows.
--check prints census without writing; --audit creates isolated new report.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S07 = ROOT / "qcv5_native_trial_20261022T010124Z_dfae01c2"
S85 = ROOT / "reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954"
S87 = ROOT / "reports/stage87_five_site_DATM_NetCDF_technical_preview_20261026T003934Z_30692f63"
GOOD = {"US-BZS": 1, "US-CMW": 2, "US-Ha1": 2, "US-Ho2": 19, "US-Ho3": 0}
BLOCKED = {"US-EML": 1327, "US-GLE": 295, "US-Ho1": 937, "US-ICh": 169, "US-ICt": 2176}
HOLD_NAME = "274_Ho1_2000_nonQC0_temperature_source_HOLD.csv"
ALL_NAME = "17568_Ho1_2000_tower_T_preserved_humidity_candidate.csv"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def require_sha(path, value):
    if not path.is_file() or sha(path) != value:
        raise ValueError("Source missing or SHA changed: " + str(path))

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def native_time(value):
    return datetime.strptime(str(value).strip(), "%Y%m%d%H%M")

def inputs():
    if not (S07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Original ten-site Stage07 incomplete marker not preserved")
    old_sha = json.loads((S07 / "output_sha256.json").read_text())
    statuses = read_csv(S07 / "candidate_run_summary.csv")
    if len(statuses) != 10 or {r["site"] for r in statuses} != set(GOOD) | set(BLOCKED):
        raise ValueError("Stage07 site census drift")
    chosen = {r["site"]: r for r in statuses}
    for site in GOOD:
        if chosen[site]["status"] != "CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
            raise ValueError("Stage07 five-site outcome drift: " + site)
    for site in BLOCKED:
        if chosen[site]["status"] != "FAIL":
            raise ValueError("Stage07 blocker changed: " + site)
        if not chosen[site].get("error", "").startswith(str(BLOCKED[site]) + " impossible humidity pairs"):
            raise ValueError("Stage07 original blocker count drift: " + site)

    qc0_edits = []
    for site, expected in GOOD.items():
        p = S07 / site / "forcing/qc_v5" / f"{site}_replacement_events.csv"
        rel = str(p.relative_to(S07))
        if rel not in old_sha:
            raise ValueError("Unpinned historical Stage07 QC0 event ledger: " + rel)
        require_sha(p, old_sha[rel])
        candidates = [r for r in read_csv(p) if number(r.get("official_qc")) == 0.0]
        if len(candidates) != expected:
            raise ValueError(f"Original QC0 edit population changed: {site}: {len(candidates)} vs {expected}")
        for r in candidates:
            r["review_status"] = "ORIGINAL_QC0_EDIT_REVIEW_REQUIRED_NOT_APPROVED"
            qc0_edits.append(r)
    if len(qc0_edits) != 24:
        raise ValueError("QC0 edits must be exactly 24")

    if (S85 / "INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage85 candidate still incomplete")
    m85 = json.loads((S85 / "stage85_source_decision_manifest.json").read_text())
    for name in (HOLD_NAME, ALL_NAME):
        require_sha(S85 / name, m85["outputs_SHA256"][name])
    if (m85["original_measured_T_QC0_preserved_count"],
        m85["VPD_modified_humidity_only_count"],
        m85["VPD_original_unchanged_ERA_self_32_count"],
        m85["nonQC0_original_T_retained_but_science_HOLD_count"]) != (17294, 1068, 32, 274):
        raise ValueError("Approved Stage85 source evidence changed")
    all_rows, hold = read_csv(S85 / ALL_NAME), read_csv(S85 / HOLD_NAME)
    if len(all_rows) != 17568 or len(hold) != 274:
        raise ValueError("Stage85 native HH census changed")
    times = [native_time(r["tower_local_start"]) for r in all_rows]
    if len(set(times)) != len(times) or times != sorted(times):
        raise ValueError("Ho1 native timestamps out of order")
    idx = {r["source_csv_row"]: i for i, r in enumerate(all_rows)}
    scored = []
    for r in hold:
        i = idx.get(r["source_csv_row"])
        if i is None or all_rows[i]["tower_local_start"] != r["tower_local_start"]:
            raise ValueError("Original Ho1 source physical row mismatch")
        if number(r["native_TA_F_original_QC"]) == 0:
            raise ValueError("Stage85 274 HOLD changed to QC0")
        z = dict(r)
        for tag, rng in (("prev", range(i-1, -1, -1)), ("next", range(i+1, len(all_rows)))):
            found = None
            for j in rng:
                t = number(all_rows[j]["native_TA_F_original_preserved_C"])
                if number(all_rows[j]["native_TA_F_original_QC"]) == 0 and t is not None:
                    found = j
                    break
            z[tag + "_nearest_original_QC0_time"] = all_rows[found]["tower_local_start"] if found is not None else ""
            z[tag + "_nearest_original_QC0_T_C"] = all_rows[found]["native_TA_F_original_preserved_C"] if found is not None else ""
            z[tag + "_QC0_gap_minutes"] = int(abs((times[i] - times[found]).total_seconds()) / 60) if found is not None else ""
        z["review_status"] = "ORIGINAL_NON_QC0_GAPFILLED_T_SOURCE_POLICY_UNAPPROVED"
        z["T_replacement_committed"] = "NO"
        scored.append(z)
    m87 = json.loads((S87 / "manifest.json").read_text())
    if (S87 / "INCOMPLETE_DO_NOT_USE").exists() or m87.get("netcdf_year_files") != 117 or m87.get("sites_built") != 5:
        raise ValueError("Stage87 expected 117-file completed preview not found")
    if m87.get("scientific_release") is not False:
        raise ValueError("Stage87 technical preview incorrectly science-released")
    summary = {
        "schema": "STAGE88_BATCH02_EXACT_PRIORITY_MANUAL_DECISIONS_v1",
        "verified_five_technical_preview_files": 117,
        "Stage07_original_QC0_changed_variable_records_not_approved": len(qc0_edits),
        "Stage07_original_QC0_by_site": GOOD,
        "Ho1_2000_original_T_QC_nonzero_records_not_approved": len(scored),
        "Ho1_2000_measured_T_QC0_keep_decision_already_approved": 17294,
        "Ho1_2000_humidity_only_edits_already_approved": 1068,
        "Ho1_2000_original_VPD_ERA_self_exceptions_already_reviewed_keep": 32,
        "historical_Stage07_blockers_not_current_remaining_HOLD_census": BLOCKED,
        "historical_Stage07_blocker_total": sum(BLOCKED.values()),
        "Stage08_complete_ten_site_selected_candidates": False,
        "Stage09_post_v5_completed": False,
        "no_numeric_correction_or_model_job_authorized": True,
        "source_checksums": {
            "stage07_output_manifest": sha(S07 / "output_sha256.json"),
            "stage85_decision_manifest": sha(S85 / "stage85_source_decision_manifest.json"),
            "stage87_technical_manifest": sha(S87 / "manifest.json"),
        }
    }
    return qc0_edits, scored, summary

def write_csv(path, rows):
    if not rows: raise ValueError("Empty review dataset")
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--audit", action="store_true")
    args = p.parse_args()
    if args.self_test:
        assert len(GOOD) == 5 and len(BLOCKED) == 5
        assert sum(GOOD.values()) == 24 and sum(BLOCKED.values()) == 4904
        assert not (set(GOOD) & set(BLOCKED))
        assert native_time("200001010000") == datetime(2000, 1, 1)
        assert number("0.0") == 0.0 and number("-9999") == -9999.0
        print("STAGE88 SELF-TEST PASS | 24 source QC0 edits, 274 Ho1 nonQC0 T, five original blockers; no writes")
        return
    edits, hold, report = inputs()
    print("STAGE88 VERIFIED | Stage87 NC 117; Stage07 ORIGINAL QC0 EDITS", len(edits),
          "| Stage85 Ho1 NONQC0 T HOLD", len(hold))
    print("STAGE88 5 HISTORICAL BLOCKERS ONLY", json.dumps(BLOCKED, sort_keys=True))
    print("STAGE88 MANUAL Ho1 nonQC0 T examples (SOURCE VALUES NOT EDITED)")
    for r in hold[:8]:
        print("  ", r["tower_local_start"], "QC", r["native_TA_F_original_QC"],
              "T", r["native_TA_F_original_preserved_C"],
              "ERA_T", r["native_T_ERA"],
              "QC0_neighbor_gap_min", r["prev_QC0_gap_minutes"], r["next_QC0_gap_minutes"])
    print("STAGE88 ORIGINAL QC0 changed records by site", json.dumps(GOOD, sort_keys=True))
    if args.check:
        print("STAGE88 CHECK PASS | source SHA verified, human decision rows prepared; NO WRITES")
        return
    out = ROOT / "reports" / ("stage88_Batch02_exact_manual_science_review_" +
                              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                              "_" + uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    marker = out / "INCOMPLETE_DO_NOT_USE"
    marker.write_text("Priority decision dossier only, not model forcing.\n")
    a = out / "24_original_QC0_modified_variable_records_REVIEW.csv"
    b = out / "274_Ho1_2000_nonQC0_temperature_neighbor_context_REVIEW.csv"
    write_csv(a, edits)
    write_csv(b, hold)
    report["output_sha256"] = {a.name: sha(a), b.name: sha(b)}
    (out / "review_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    marker.unlink()
    print("STAGE88 AUDIT PASS | 24 QC0 source edits, 274 Ho1 nonQC0 T source HOLD; NO SOURCE/MODEL WRITES")
    print("REPORT", out)

if __name__ == "__main__":
    main()

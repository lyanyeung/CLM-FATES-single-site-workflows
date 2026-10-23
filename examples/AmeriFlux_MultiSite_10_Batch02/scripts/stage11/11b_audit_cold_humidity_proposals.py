#!/usr/bin/env python3
"""Stage11b: independently recompute Batch02 provisional humidity proposals.

READ ONLY with respect to Stage07/08/11, raw FLUXMET and CIME/DATM/Slurm.
Creates a new *report* containing residual holds and risk/QC summaries.
No scientific approval, forcing overlay, or run submission.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

DEFAULT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/stage11_cold_humidity_review_20261022T020911Z_2ad6f27b")
EXPECTED = {
    "US-EML": (1327, 1326, 1),
    "US-GLE": (295, 292, 3),
    "US-Ho1": (917, 917, 0),
    "US-ICh": (169, 169, 0),
    "US-ICt": (2176, 2166, 10),
}

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1024 * 1024), b""):
            h.update(piece)
    return h.hexdigest()

def numbers(frame, columns):
    for key in columns:
        frame[key] = pd.to_numeric(frame[key], errors="coerce")
    return frame

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage11-root", type=Path, default=DEFAULT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--check", action="store_true", help="Verify and print only, no report creation")
    args = parser.parse_args()

    root = args.stage11_root.expanduser().resolve()
    if not (root / "DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("This is not a marked Stage11 review-only report")
    source_csv = root / "cold_humidity_repair_proposals.csv"
    manifest_path = root / "manifest.json"
    source_summary = root / "site_summary.csv"
    manifest = json.loads(manifest_path.read_text())
    if manifest["scientific_status"] != "HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Unexpected science status")
    if manifest["n_target_rows"] != 4884 or not manifest["no_forcing_written"]:
        raise ValueError("Unexpected Stage11 report scope")
    engine = Path(__file__).with_name("11_review_cold_humidity.py")
    if engine.exists() and sha(engine) != manifest["script_hash"]:
        raise ValueError("Stage11 script changed since proposals were created")
    raw = pd.read_csv(source_csv, dtype={"site": str, "time": str})
    if len(raw) != 4884 or set(raw.site) != set(EXPECTED):
        raise ValueError("Unexpected Stage11 row count or sites")
    if raw.duplicated(["site", "time"]).any():
        raise ValueError("Duplicated Stage11 row identity")
    nums = ["retained_TA_C", "retained_PA_kPa", "prior_VPD_hPa",
            "ERA_RH_impossible_pct", "source_VPD_QC",
            "donor_count", "donor_RH_median_pct", "donor_RH_q25_pct",
            "donor_RH_q75_pct", "proposed_VPD_hPa", "proposed_QBOT_kgkg"]
    raw = numbers(raw, nums)
    ok = raw.decision.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED")
    hold = raw.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE")
    if not (ok | hold).all():
        raise ValueError("Unknown repair proposal decision")
    if int(ok.sum()) != 4870 or int(hold.sum()) != 14:
        raise ValueError("Unexpected provisional/held counts")
    if not (raw.loc[hold, ["proposed_VPD_hPa", "proposed_QBOT_kgkg"]].isna().all().all()):
        raise ValueError("HOLD records must not have synthetic forcing values")
    if not raw.source_VPD_QC.fillna(-999).ne(0).all():
        raise ValueError("Original QC0 VPD changes require separate explicit review")
    if not raw.ERA_RH_impossible_pct.lt(-2).all():
        raise ValueError("Unexpected ERA-derived RH blocker type")
    ms = int(manifest["min_donors"])
    t = raw.loc[ok, "retained_TA_C"].to_numpy(dtype=float)
    pa = raw.loc[ok, "retained_PA_kPa"].to_numpy(dtype=float) * 1000
    rh = raw.loc[ok, "donor_RH_median_pct"].to_numpy(dtype=float)
    vpd = raw.loc[ok, "proposed_VPD_hPa"].to_numpy(dtype=float)
    q = raw.loc[ok, "proposed_QBOT_kgkg"].to_numpy(dtype=float)
    with np.errstate(all="ignore"):
        es = 6.112 * np.exp(17.67 * t / (t + 243.5))
        independent_vpd = es * (1 - rh / 100)
        independent_ea = (es - independent_vpd) * 100
        independent_q = .622 * independent_ea / (pa - .378 * independent_ea)
    if not (
        (np.isfinite(t) & (t < 0) & (t >= -80)).all()
        and (np.isfinite(pa) & (pa >= 50000) & (pa <= 110000)).all()
        and (np.isfinite(rh) & (rh >= 5) & (rh < 100)).all()
        and raw.loc[ok, "donor_count"].ge(ms).all()
        and np.isclose(vpd, independent_vpd, rtol=1e-10, atol=1e-9).all()
        and np.isclose(q, independent_q, rtol=1e-8, atol=1e-11).all()
        and (q > 0).all()
    ):
        raise ValueError("Provisional VPD/QBOT reconstruction failed independent numerical audit")
    quant = raw.loc[ok, ["donor_RH_q25_pct", "donor_RH_median_pct", "donor_RH_q75_pct"]]
    if not (quant.iloc[:, 0].le(quant.iloc[:, 1]).all() and
            quant.iloc[:, 1].le(quant.iloc[:, 2]).all()):
        raise ValueError("Invalid donor RH quartile ordering")
    actual_counts = raw.groupby("site", sort=True).agg(
        blocked=("decision", "size"),
        provisional=("decision", lambda x: x.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED").sum()),
        hold=("decision", lambda x: x.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()))
    if any(tuple(actual_counts.loc[s]) != EXPECTED[s] for s in EXPECTED):
        raise ValueError("Site-specific counts differ from operator Stage11 output")
    site_summary = pd.read_csv(source_summary).set_index("site")
    for site, vals in EXPECTED.items():
        if tuple(int(site_summary.loc[site, c]) for c in ("blocked", "provisional", "hold")) != vals:
            raise ValueError("Stage11 summary CSV differs: " + site)
    flagged = raw.loc[ok].copy()
    flagged["donor_RH_IQR_pct"] = flagged.donor_RH_q75_pct - flagged.donor_RH_q25_pct
    flagged["VPD_change_hPa"] = flagged.proposed_VPD_hPa - flagged.prior_VPD_hPa
    flagged["abs_VPD_change_hPa"] = flagged.VPD_change_hPa.abs()
    flagged["relative_change_to_es"] = flagged.abs_VPD_change_hPa / es
    flagged["review_large_donor_RH_IQR"] = flagged.donor_RH_IQR_pct.gt(40)
    flagged["review_large_VPD_change_vs_es"] = flagged.relative_change_to_es.gt(.5)
    flagged["review_low_donor_support"] = flagged.donor_count.lt(100)
    holds = raw.loc[hold].copy()
    holds["hold_reason_diagnostic"] = np.select(
        [
            holds.retained_TA_C.ge(0),
            ~holds.retained_TA_C.between(-80, 65),
            ~holds.retained_PA_kPa.between(50, 110),
            holds.donor_count.lt(ms),
            holds.donor_RH_median_pct.isna(),
            holds.donor_RH_median_pct.ge(100),
        ],
        [
            "TARGET_NOT_SUBZERO",
            "TARGET_TEMPERATURE_OUTSIDE_RANGE",
            "TARGET_PRESSURE_OUTSIDE_RANGE",
            "INSUFFICIENT_COLD_ANALOGUES",
            "NO_VALID_MONTHLY_RH_ANALOGUE",
            "SATURATED_OR_INVALID_PROXY",
        ],
        default="OTHER_OR_PHYSICAL_SCREEN",
    )
    hold_cols = ["site", "time", "source_csv_row", "retained_TA_C", "retained_PA_kPa",
                 "prior_VPD_hPa", "ERA_RH_impossible_pct", "donor_count",
                 "donor_RH_median_pct", "hold_reason_diagnostic"]
    print("========== STAGE11b INDEPENDENT AUDIT ==========")
    print("Rows:", len(raw), "provisional:", len(flagged), "held:", len(holds))
    print(actual_counts.to_string())
    print("\n14 RESIDUAL HOLDS")
    print(holds[hold_cols].to_string(index=False))
    print("\nPROVISIONAL RISK FLAGS (NOT INVALIDITY CERTIFICATIONS)")
    for col in ("review_large_donor_RH_IQR", "review_large_VPD_change_vs_es", "review_low_donor_support"):
        print(col, int(flagged[col].sum()))
    print("\nPER-SITE ABS VPD DIFFERENCE (hPa), candidate RH median, donor count")
    print(flagged.groupby("site").agg(
        median_abs_VPD_delta_hPa=("abs_VPD_change_hPa", "median"),
        max_abs_VPD_delta_hPa=("abs_VPD_change_hPa", "max"),
        median_proxy_RH_pct=("donor_RH_median_pct", "median"),
        minimum_donors=("donor_count", "min"),
        max_donor_RH_IQR_pct=("donor_RH_IQR_pct", "max")
    ).round(4).to_string())
    if args.check:
        print("AUDIT CHECK ONLY. No outputs written.")
        return 0
    out = args.output_root.expanduser().resolve() if args.output_root else (
        Path.home() / ("AmeriFlux_Batch02_stage11b_" +
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]))
    if out.exists() or root == out or out in root.parents or root in out.parents:
        raise ValueError("Unsafe/existing output location")
    out.mkdir(parents=True, exist_ok=False)
    holds[hold_cols].to_csv(out / "14_unresolved_holds.csv", index=False)
    flagged.to_csv(out / "4870_proposal_risk_audit.csv", index=False)
    actual_counts.to_csv(out / "site_counts_audited.csv")
    (out / "input_receipt.json").write_text(json.dumps({
        "stage11_report": str(root),
        "source_sha256": {str(p): sha(p) for p in (source_csv, source_summary, manifest_path)},
        "checked_vpd_qbot_numeric": True, "scientific_status": "NOT_VALIDATED_NO_DATM",
        "14_holds_preserved": True
    }, indent=2)+"\n", encoding="utf-8")
    print("\nSTAGE11b REPORT:", out)
    print("REPORT ONLY. No approved forcing or model jobs.")

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only planning manifest: 22 sites x two observed-biogeography FATES modes.

The two controlled arms are COMP (with competition) and FIXNC (no competition).
Both restrict eligible FATES PFTs to those allowed by prescribed biogeography.
This does NOT create land-use surfaces, CIME cases, binaries or Slurm jobs.
A fully unrestricted Full FATES experiment is a separate baseline, not COMP.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1] / "38_site_PFT_evidence.csv"
NUMERIC = {
    "NUMERIC_SPECIES", "NUMERIC_AREA", "NUMERIC_TEMPORAL",
    "NUMERIC_BASAL_AREA", "NUMERIC_VEGETATED_COVER",
    "TOTAL_COVER_ONLY", "NUMERIC_COVER_CONFLICT",
    "NUMERIC_GROUND_COVER", "NUMERIC_CONFLICT",
}
# Candidates for focused spatial-denominator review, NOT run permission.
AREA_LEADS = {"NL-Loo", "ES-LJu", "DE-Tha"}
MODE_SETTINGS = (
    ("COMP", ".true.", ".false."),  # fixed biogeography WITH competition
    ("FIXNC", ".true.", ".true."),  # fixed biogeography WITHOUT competition
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path,
                   default=Path.home() / "ICOS_PFT_Observed22_dual_plan.tsv")
    args = p.parse_args()
    with EVIDENCE.open(newline="", encoding="utf-8") as f:
        items = list(csv.DictReader(f))
    if len(items) != 38:
        raise SystemExit("STOP: expected 38 master evidence rows")
    rows = []
    for obs in items:
        if obs["evidence_class"] not in NUMERIC:
            continue
        site = obs["site"]
        status = ("REVIEW_AREA_DENOMINATOR" if site in AREA_LEADS
                  else "HOLD_NUMERIC_EVIDENCE_NOT_VALIDATED_AS_AREA")
        for mode, fixed_flag, nocomp_flag in MODE_SETTINGS:
            rows.append({
                "site": site,
                "batch": obs["batch"],
                "mode": mode,
                "proposed_case": site + "_OBSPFT_" + mode + "26",
                "use_fates": ".true.",
                "use_fates_sp": ".false.",
                "use_fates_fixed_biogeog": fixed_flag,
                "use_fates_nocomp": nocomp_flag,
                "area_fraction_gate": status,
                "observed_denominator": obs["observed_denominator"],
                "fates_hlm_pft_map_verified": "NO",
                "same_validated_surface_and_pft_map": "REQUIRED",
                "baseline_compset_verified": "NO",
                "case_created": "NO",
                "submission_authorized": "NO",
                "source_url": obs["literature_or_station_url"],
            })
    if len(rows) != 44 or len({r["site"] for r in rows}) != 22:
        raise SystemExit("STOP: unexpected cohort; require exactly 22 sites and 44 rows")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print("PLAN ONLY: 22 sites x 2 fixed-biogeography modes = 44 proposed cases")
    print("COMP = competition permitted among site-allowed PFTs")
    print("FIXNC = PFT area locked; within-PFT demography remains dynamic")
    print("Unrestricted FULL FATES is a separate comparison arm.")
    print("ALL cases HOLD: none approved for automatic creation or submission")
    print("No model files, existing cases, surfaces, executables, or jobs changed.")
    print(args.output)


if __name__ == "__main__":
    main()

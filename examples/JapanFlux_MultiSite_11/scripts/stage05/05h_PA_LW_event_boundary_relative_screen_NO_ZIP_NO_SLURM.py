#!/usr/bin/env python3
"""JapanFlux Stage05H — targeted PA/LW neighboring-value screen from 8 Stage05F JSONs.

NO ZIP, NO SLURM, NO MODEL, NO SOURCE EDITS, NO REPAIR OR APPROVAL.
Conservative local-reference screens are deliberately EXPLORATORY:
PA_F < 85% of both nearby flank values or LW_IN_F < 60% of both.
These are candidates for independent QC, NOT universal physical thresholds.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

SITES = ("JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp",
         "JP-Tak", "JP-Tef", "JP-Tmd", "JP-Yms")
VARS = (("PA", 0.85, 70.0), ("LW_IN", 0.60, 120.0))
FIELDS = (
    "site", "native_date", "native_start", "variable", "F_value",
    "F_QC_raw", "ERA_value", "F_MDS_value", "left_flank_F",
    "right_flank_F", "conservative_baseline_F", "F_to_baseline_ratio",
    "Stage05G_threshold_flag", "relative_context_screen",
    "screen_classification"
)


def numeric(raw: object) -> float | None:
    if raw is None:
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v) or v <= -6999:
        return None
    return v


def registered_flagged(tsv: Path) -> set[tuple[str, str, str]]:
    out = set()
    with tsv.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["selected_F_screen_nonphysical"] != "1":
                continue
            k = (r["site"], r["native_start"], r["variable"])
            if k in out:
                raise ValueError(f"Duplicate source flag in Stage05G: {k}")
            out.add(k)
    if len(out) != 41:
        raise ValueError(f"Expected actual operator Stage05G 41 selected-F flags; found {len(out)}")
    return out


def analyse(input_dir: Path, selected_tsv: Path) -> tuple[list[dict], dict]:
    known = registered_flagged(selected_tsv)
    results = []
    totals = Counter()
    unexplained = set(known)
    for site in SITES:
        file = input_dir / (site + "_impact.json")
        r = json.loads(file.read_text(encoding="utf-8"))
        if (r.get("site") != site or r.get("stage") != "JapanFlux Stage05F"
                or r.get("status") != "READONLY_SOURCE_IMPACT_SCREEN_COMPLETE"):
            raise ValueError(f"Invalid/incomplete Stage05F JSON: {file}")
        day_rows: dict[str, list[dict]] = {}
        for rr in r["rows_selected"]:
            if "native_start" not in rr or "cells" not in rr:
                raise ValueError("Incomplete Stage05F row")
            day_rows.setdefault(rr["native_start"][:8], []).append(rr)
        for date, rows in sorted(day_rows.items()):
            rows = sorted(rows, key=lambda item: item["native_start"])
            if len({row["native_start"] for row in rows}) != len(rows):
                raise ValueError(f"Duplicate native starts for {site} {date}")
            if len(rows) < 3:
                continue
            for var, relative_ratio, min_baseline in VARS:
                col = var + "_F"
                flank_start = numeric(rows[0]["cells"].get(col))
                flank_end = numeric(rows[-1]["cells"].get(col))
                if (flank_start is not None and flank_end is not None
                        and flank_start > min_baseline
                        and flank_end > min_baseline):
                    baseline = min(flank_start, flank_end)
                else:
                    baseline = None
                for rr in rows:
                    t = rr["native_start"]
                    c = rr["cells"]
                    fvalue = numeric(c.get(col))
                    existing = (site, t, var) in known
                    if existing:
                        unexplained.discard((site, t, var))
                    ratio = fvalue / baseline if baseline is not None and fvalue is not None else None
                    relative = bool(ratio is not None and ratio < relative_ratio)
                    if existing:
                        category = "ALREADY_CONFIRMED_STAGE05G_PHYSICAL_SCREEN"
                    elif relative:
                        category = "ADDITIONAL_RELATIVE_ANOMALY_REVIEW_ONLY"
                    elif baseline is None:
                        category = "NO_TWO_SUITABLE_FLANKS_NOT_ASSESSED"
                    else:
                        category = "NO_STAGE05H_RELATIVE_FLAG"
                    if relative and not existing:
                        totals[f"{var}:ADDITIONAL_RELATIVE"] += 1
                        totals[f"{site}:ADDITIONAL_RELATIVE"] += 1
                    if existing:
                        totals[f"{var}:EXISTING_FLAG"] += 1
                    results.append({
                        "site": site, "native_date": date,
                        "native_start": t, "variable": var,
                        "F_value": c.get(col, ""),
                        "F_QC_raw": c.get(var + "_F_QC", ""),
                        "ERA_value": c.get(var + "_ERA", ""),
                        "F_MDS_value": c.get(var + "_F_MDS", ""),
                        "left_flank_F": flank_start if flank_start is not None else "",
                        "right_flank_F": flank_end if flank_end is not None else "",
                        "conservative_baseline_F": baseline if baseline is not None else "",
                        "F_to_baseline_ratio": round(ratio, 6) if ratio is not None else "",
                        "Stage05G_threshold_flag": int(existing),
                        "relative_context_screen": int(relative),
                        "screen_classification": category,
                    })
    unaccounted_pa_lw = {e for e in unexplained if e[2] in ("PA", "LW_IN")}
    if unaccounted_pa_lw:
        raise ValueError(f"Stage05G existing PA/LW flags lost by Stage05H: {sorted(unaccounted_pa_lw)}")
    results.sort(key=lambda x: (x["site"], x["native_start"], x["variable"]))
    summary = {
        "stage": "JapanFlux Stage05H",
        "status": "READONLY_RELATIVE_BOUNDARY_REVIEW_COMPLETE",
        "sites": list(SITES), "source": "Existing Stage05F site JSON + Stage05G TSV only",
        "no_source_zip_read": True, "no_science_edit": True,
        "no_slurm": True, "no_approval": True,
        "existing_stage05g_41_variable_flags": len(known),
        "additional_relative_screen_counts": dict(totals),
        "context_rows": len(results),
        "relative_pa_threshold_fraction": 0.85,
        "relative_lw_threshold_fraction": 0.60,
        "rule": "Selected F is compared to the LOWER of first/last sampled selected F for that site's event day; both anchors must exceed 70 kPa PA or 120 W/m2 LW. Thresholds are exploratory review screens, not scientifically established corrections.",
        "caveats": [
            "Only timestamps saved in Stage05F event contexts were screened.",
            "No claim that other candidate meteorological values are error-free.",
            "Stage05G 41 variable threshold flags remain independent and unchanged.",
            "No timezone or independently acquired ECMWF ERA verified.",
            "Do not replace measured QC0 or derive an approved overlay from these reference values."
        ],
    }
    return results, summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage05f-dir", required=True, type=Path)
    p.add_argument("--stage05g-tsv", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    args = p.parse_args()
    rows, summary = analyse(args.stage05f_dir, args.stage05g_tsv)
    out = args.output_dir
    if out.resolve() == args.stage05f_dir.resolve():
        p.error("Output must not be the Stage05F source folder")
    out.mkdir(parents=True, exist_ok=True)
    tsv = out / "stage05h_PA_LW_relative_context_screen.tsv"
    jfile = out / "stage05h_summary.json"
    if tsv.exists() or jfile.exists():
        p.error("Output exists; use a new directory, do not overwrite")
    with tsv.open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    with jfile.open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("STAGE05H SUCCESS | 8/8 source site reports | NO ZIP, NO SLURM")
    print("STAGE05G_PREEXISTING_FLAGS", summary["existing_stage05g_41_variable_flags"])
    print("EXPLORATORY_ADDITIONAL_PA_LW_FLAGS", {
        k: v for k, v in summary["additional_relative_screen_counts"].items()
        if k.endswith(":ADDITIONAL_RELATIVE")
    })
    print("DATA", tsv)
    print("SUMMARY", jfile)
    print("NO SOURCE CHANGES, NO REPAIRS, NO AD400")


if __name__ == "__main__":
    raise SystemExit(main())

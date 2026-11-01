#!/usr/bin/env python3
"""JapanFlux Stage05F: exact-event selected forcing source impact, one JPF site.

READ-ONLY, no Slurm; consumes a Stage05D JSON to identify ERA anomaly
timestamps, then streams only the corresponding site's original FLUXMET_HH
from the original nested ZIP without extracting it to disk. Emits JSON.

Scientific LIMITS: thresholds only screen nonphysical candidate values;
QC=0/1/2 are preserved verbatim and not authoritatively decoded;
same-release ERA source remains unvalidated against independent ECMWF ERA5.
No replacements, materialized forcing, or model jobs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import io
import json
import math
from pathlib import Path
import zipfile

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
JPF = ("JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp", "JP-Tak",
       "JP-Tef", "JP-Tmd", "JP-Yms")
FLUX_FIELDS = ("TA", "PA", "LW_IN", "SW_IN", "VPD", "P", "WS")
WATCH_CELLS = ("TIMESTAMP_START", "TIMESTAMP_END") + tuple(
    col for var in FLUX_FIELDS
    for col in (var + "_F", var + "_F_QC",
                var + "_F_MDS", var + "_F_MDS_QC", var + "_ERA")
)
BAD_NUMERIC = {"", "NA", "NAN", "NULL", "NONE",
               "-9999", "-9999.0", "-6999", "-6999.0"}


def number(s: str | None) -> float | None:
    if s is None or s.strip().upper() in BAD_NUMERIC:
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    return val if math.isfinite(val) and val > -6999 else None


def screen(var: str, x: float | None) -> bool:
    return x is not None and {
        "TA": lambda v: v < -70.0,
        "PA": lambda v: v < 50.0,
        "LW_IN": lambda v: v < 50.0,
        "SW_IN": lambda v: v < -20.0,
        "VPD": lambda v: v < -1e-9,
        "P": lambda v: v < -1e-9,
        "WS": lambda v: v < 0,
    }[var](x)


def parse_event_records(stage05d: dict) -> dict:
    # Stage05D stores the first few anomaly samples per variable AND full
    # samples for three watched dates. Reject any incompletely recorded site.
    events = defaultdict(dict)
    for v, records in stage05d.get("examples_by_flag", {}).items():
        for r in records:
            events[r["start"]][v] = r["value"]
    for rows in stage05d.get("watched_dates", {}).values():
        for r in rows:
            for flag in r.get("flags", []):
                events[r["start"]][flag["variable"]] = flag["value"]
    expected = stage05d["flagged_unique_native_starts"]
    if len(events) != expected:
        raise ValueError(f"Saved event sample count {len(events)} != full count {expected}; "
                         "do not treat an incomplete Stage05D sample as exhaustive.")
    if not events:
        raise ValueError("No flagged event timestamps in selected station")
    for t in events:
        datetime.strptime(t, "%Y%m%d%H%M")
    return dict(events)


def context_times(events: dict) -> set[str]:
    starts = set()
    for t in events:
        dt = datetime.strptime(t, "%Y%m%d%H%M")
        for offset in (-30, 0, 30):
            starts.add((dt + timedelta(minutes=offset)).strftime("%Y%m%d%H%M"))
    return starts


def scan_selected(site: str, pkg: str, root: Path, target: set[str],
                  event_map: dict, max_mib: int) -> dict:
    path = root / site / "forcing" / "packages" / (pkg + ".zip")
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or symlinked exact source ZIP: " + str(path))
    output = {"site": site, "source_archive": str(path), "rows_scanned": 0,
              "rows_selected": [], "observed_ERA_event_starts": [],
              "selected_F_screen_flagged_by_field": {},
              "ERA_event_selected_F_QC_raw_histogram": {},
              "ERA_event_source_matches": {},
              "source_clock": "NATIVE_UNVERIFIED_TIMEZONE",
              "QC_interpretation": "RAW_LABELS_ONLY"}
    with zipfile.ZipFile(path) as outer:
        nested = [i for i in outer.infolist()
                  if i.filename == pkg + ".zip" and not i.is_dir()]
        if len(nested) != 1:
            raise ValueError("Expected exactly one release nested ZIP")
        cap = max_mib * 1024 * 1024
        if nested[0].file_size > cap:
            raise ValueError("Nested release larger than configured RAM cap")
        with io.BytesIO() as mem:
            with outer.open(nested[0]) as content:
                total = 0
                while True:
                    chunk = content.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > cap:
                        raise ValueError("Streaming release exceeded RAM cap")
                    mem.write(chunk)
            mem.seek(0)
            with zipfile.ZipFile(mem) as inner:
                members = [i for i in inner.infolist()
                           if not i.is_dir() and "_FLUXMET_HH_" in Path(i.filename).name
                           and i.filename.lower().endswith(".csv")]
                if len(members) != 1:
                    raise ValueError("Expected one FLUXMET_HH CSV")
                output["source_member"] = members[0].filename
                with inner.open(members[0]) as raw:
                    with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                        reader = csv.DictReader(stream)
                        headers = reader.fieldnames or []
                        if len(set(headers)) != len(headers):
                            raise ValueError("Duplicate column names")
                        if not {"TIMESTAMP_START", "TIMESTAMP_END"} <= set(headers):
                            raise ValueError("Missing native timestamps")
                        present = [name for name in WATCH_CELLS if name in headers]
                        output["available_columns"] = present
                        matched = set()
                        selected_screen = Counter()
                        qc_hist = defaultdict(Counter)
                        matches = Counter()
                        for row in reader:
                            output["rows_scanned"] += 1
                            t = row["TIMESTAMP_START"]
                            if t not in target:
                                continue
                            if t in matched:
                                raise ValueError("Duplicate native timestamp: " + t)
                            matched.add(t)
                            flagged_ERA = event_map.get(t, {})
                            f_flags = []
                            comparisons = {}
                            for var in FLUX_FIELDS:
                                f_value = number(row.get(var + "_F"))
                                e_value = number(row.get(var + "_ERA"))
                                if screen(var, f_value):
                                    selected_screen[var] += 1
                                    f_flags.append(var + "_F")
                                if var + "_ERA" in flagged_ERA:
                                    qc = row.get(var + "_F_QC", "<not available>")
                                    qc_hist[var][qc] += 1
                                    if f_value is None or e_value is None:
                                        same = "UNAVAILABLE"
                                    else:
                                        same = ("EQUAL" if math.isclose(f_value, e_value,
                                                rel_tol=1e-12, abs_tol=1e-9)
                                                else "DIFFERENT")
                                    comparisons[var] = same
                                    matches[var + ":" + same] += 1
                            output["rows_selected"].append({
                                "native_start": t,
                                "source_event_ERA_flags": flagged_ERA,
                                "selected_F_physical_flags": f_flags,
                                "selected_F_vs_embedded_ERA_when_source_flagged": comparisons,
                                "cells": {name: row[name] for name in present},
                            })
        output["rows_selected"].sort(key=lambda r: r["native_start"])
        output["observed_ERA_event_starts"] = [
            r["native_start"] for r in output["rows_selected"]
            if r["source_event_ERA_flags"]
        ]
        output["selected_F_screen_flagged_by_field"] = dict(selected_screen)
        output["ERA_event_selected_F_QC_raw_histogram"] = {
            v: dict(hist) for v, hist in qc_hist.items()
        }
        output["ERA_event_source_matches"] = dict(matches)
        output["status"] = "READONLY_SOURCE_IMPACT_SCREEN_COMPLETE"
    return output


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--stage05d-dir", type=Path, required=True)
    p.add_argument("--site", choices=JPF, required=True)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--max-nested-mib", type=int, default=256)
    args = p.parse_args()
    if not 64 <= args.max_nested_mib <= 512:
        p.error("Out-of-range maximum memory allocation")
    report_path = args.stage05d_dir / (args.site + "_ERA5_audit.json")
    r = json.loads(report_path.read_text(encoding="utf-8"))
    if (r.get("site") != args.site or r.get("stage") != "JapanFlux Stage05D"
            or r.get("status") != "ERA5_FULL_SCAN_COMPLETED"
            or r.get("read_only") is not True):
        p.error("Selected station must have a verified completed Stage05D source report")
    event_map = parse_event_records(r)
    with args.manifest.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    stations = {r["site"]: r for r in rows}
    if len(rows) != 11 or len(stations) != 11 or args.site not in stations:
        p.error("Expected exact unique 11-site manifest")
    output = scan_selected(args.site, stations[args.site]["package"], args.root,
                           context_times(event_map), event_map, args.max_nested_mib)
    output["stage"] = "JapanFlux Stage05F"
    output["ERA5_HH_unique_flagged_starts_full_period"] = r["flagged_unique_native_starts"]
    output["ERA5_event_starts_outside_FLUXMET_source"] = sorted(
        set(event_map) - set(output["observed_ERA_event_starts"])
    )
    output["ERA5_event_starts_inside_FLUXMET_source"] = len(output["observed_ERA_event_starts"])
    output["science_decision"] = "NOT_APPROVED_NO_REPLACEMENTS"
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

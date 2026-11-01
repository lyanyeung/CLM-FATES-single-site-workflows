#!/usr/bin/env python3
"""JapanFlux Stage05B: timestamp-specific JPF raw-F/QC/MDS/ERA comparisons.

Operator-controlled READ ONLY. Does not extract ZIP, modify science data, repair
or submit Slurm. Event timestamps come from an existing full Stage04 JSON file.
Runs one JPF site per invocation to limit login-node memory/CPU footprint.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import zipfile

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITES = ("JP-Khw", "JP-Tmd", "JP-Fjy", "JP-Yms", "JP-Tef")
FIELDS = ("TA", "PA", "LW_IN", "SW_IN", "VPD", "P", "WS")
PRIMARY = tuple(f"{x}_F" for x in FIELDS)
CANDIDATE = ("TIMESTAMP_START", "TIMESTAMP_END")
for _variable in FIELDS:
    CANDIDATE += (
        f"{_variable}_F", f"{_variable}_F_QC",
        f"{_variable}_F_MDS", f"{_variable}_F_MDS_QC",
        f"{_variable}_ERA",
    )

def timestamp(v: str) -> datetime:
    return datetime.strptime(v, "%Y%m%d%H%M")

def unique_event_starts(report: dict) -> dict[str, set[str]]:
    all_events = {}
    for site in report["sites"]:
        if site["site"] not in SITES:
            continue
        starts = set()
        for part in site["files"]:
            for field in part["fields"].values():
                for sample in field.get("screen_samples", []):
                    starts.add(sample["start"])
        all_events[site["site"]] = starts
    return all_events

def context_for_event_sources(events: dict[str, set[str]], padding_minutes: int) -> dict:
    source_sites = {}
    all_starts = set().union(*events.values())
    if not all_starts:
        raise ValueError("No Stage04 flagged JPF event timestamps found")
    if len(all_starts) > 500:
        raise ValueError("Unexpectedly many target timestamps; refusing broad scan")
    # Include every JPF event's native time window at every JPF site, so a
    # common processing artefact can be compared even at an unflagged station.
    target_times = set()
    for v in all_starts:
        t = timestamp(v)
        for minute in range(-padding_minutes, padding_minutes + 1, 30):
            target_times.add((t + timedelta(minutes=minute)).strftime("%Y%m%d%H%M"))
    for name in SITES:
        source_sites[name] = sorted(events.get(name, set()))
    return {"original_flagged_event_starts_by_site": source_sites,
            "unique_global_flagged_starts": len(all_starts),
            "context_target_count": len(target_times),
            "context_target_times": target_times}

def inspect_one(site: str, pkg: str, root: Path, target_times: set[str],
                max_bytes: int) -> dict:
    path = root / site / "forcing" / "packages" / (pkg + ".zip")
    result = {"site": site, "source_archive": str(path), "rows": [],
              "read_only": True, "time_basis": "NATIVE_FILE_TIMESTAMP_NOT_ASSIGNED_UTC",
              "qc_semantics": "RAW_LABELS_NOT_INTERPRETED"}
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Missing or symlinked original archive: {path}")
    with zipfile.ZipFile(path) as outer:
        found = [i for i in outer.infolist() if not i.is_dir() and
                 i.filename == pkg + ".zip"]
        if len(found) != 1:
            raise ValueError("Outer ZIP does not contain precisely one exact-name nested release")
        if found[0].file_size > max_bytes:
            raise ValueError(f"Nested ZIP above memory cap: {found[0].file_size}")
        with io.BytesIO() as memory, outer.open(found[0]) as stream:
            total = 0
            while True:
                chunk = stream.read(4 * 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Nested ZIP exceeded memory cap")
                memory.write(chunk)
            memory.seek(0)
            with zipfile.ZipFile(memory) as inner:
                files = [i for i in inner.infolist()
                         if "_FLUXMET_HH_" in i.filename and i.filename.lower().endswith(".csv")]
                if len(files) != 1:
                    raise ValueError(f"Expected exactly one FLUXMET_HH file, got {len(files)}")
                result["source_csv"] = files[0].filename
                with inner.open(files[0]) as raw:
                    with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream_csv:
                        reader = csv.reader(stream_csv)
                        headers = next(reader)
                        if len(set(headers)) != len(headers):
                            raise ValueError("Duplicate CSV columns")
                        columns = {name: idx for idx, name in enumerate(headers)}
                        if any(key not in columns for key in ("TIMESTAMP_START", "TIMESTAMP_END")):
                            raise ValueError("Missing native timestamp columns")
                        source_names = [name for name in CANDIDATE if name in columns]
                        result["available_columns"] = source_names
                        result["missing_reference_columns"] = [name for name in CANDIDATE
                                                                if name not in columns]
                        result["rows_read"] = 0
                        for line in reader:
                            result["rows_read"] += 1
                            if len(line) != len(headers):
                                raise ValueError("CSV row has unexpected number of columns")
                            st = line[columns["TIMESTAMP_START"]]
                            if st not in target_times:
                                continue
                            values = {name: line[columns[name]] for name in source_names}
                            # Preserve exact numeric strings, no auto-interpolation
                            # or reinterpretation of the source provenance.
                            result["rows"].append({"native_start": st, "cells": values})
    result["rows"].sort(key=lambda item: item["native_start"])
    result["matching_context_rows"] = len(result["rows"])
    result["status"] = "READONLY_CONTEXT_EXTRACTED"
    return result

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--stage04-json", type=Path, required=True)
    p.add_argument("--site", choices=SITES, required=True,
                   help="One JPF site at a time; avoid long login-node jobs")
    p.add_argument("--context-minutes", type=int, default=60)
    p.add_argument("--max-nested-mib", type=int, default=256)
    args = p.parse_args()
    if not 30 <= args.context_minutes <= 120 or args.context_minutes % 30:
        p.error("--context-minutes must be 30, 60, 90 or 120")
    if not 64 <= args.max_nested_mib <= 512:
        p.error("--max-nested-mib must be 64..512")
    stage04 = json.loads(args.stage04_json.read_text(encoding="utf-8"))
    if (stage04.get("stage") != "JapanFlux Stage04" or
        stage04.get("screened") != 11 or stage04.get("expected") != 11 or
        not stage04.get("full_scan_requested")):
        p.error("Expected a FULL completed 11-site Stage04 source JSON")
    events = unique_event_starts(stage04)
    targets = context_for_event_sources(events, args.context_minutes)
    with args.manifest.open(encoding="utf-8-sig", newline="") as f:
        manifest = {row["site"]: row for row in csv.DictReader(f, delimiter="\t")}
    if len(manifest) != 11:
        p.error("Expected manifest with 11 unique sites")
    result = inspect_one(args.site, manifest[args.site]["package"], ROOT,
                         targets["context_target_times"], args.max_nested_mib * (1024**2))
    result["source_event_counts"] = {k: len(v) for k, v in events.items()}
    result["global_unique_event_starts"] = targets["unique_global_flagged_starts"]
    result["global_context_target_count"] = targets["context_target_count"]
    result["operator_decision"] = "NO_REPAIR_NO_FORCING_NO_MODEL"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

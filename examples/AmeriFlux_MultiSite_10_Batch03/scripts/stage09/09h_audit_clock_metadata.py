#!/usr/bin/env python3
"""Batch03 Stage09h: read-only audit of clock metadata and raw timestamp conventions.

Checks the seven sites whose humidity blockers need external ERA5-Land evidence.
Verifies the Stage07-pinned primary and standalone ERA5 source files, reports all
BIF UTC_OFFSET records with their GROUP_ID/date fields, and scans native
TIMESTAMP_START/END coverage. US-Me2 has no release BIF in the supplied FULLSET;
the script deliberately does not infer its UTC offset from longitude or DST.

No timestamps are converted, no files are written, no forcing is changed, and no
model jobs are launched. A single published UTC_OFFSET remains pending explicit
validation and is never automatically approved by this script.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
import sys

DEFAULT_SITES_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_STAGE07 = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/"
    "AmeriFlux_MultiSite_10_Batch03/"
    "qcv5_native_trial_20261022T024559Z_36c46e58"
)
DEFAULT_PLAN = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/"
    "AmeriFlux_MultiSite_10_Batch03/reports/"
    "stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c"
)
AFFECTED = {"US-Kon", "US-MMS", "US-Me2", "US-Me6", "US-MtB", "US-NR1", "US-NR3"}
REPO_SITES = Path(__file__).resolve().parents[2] / "sites.tsv"
UTC_FIELDS = (
    "SITE_ID", "GROUP_ID", "VARIABLE", "DATAVALUE", "DATAVALUE_UNITS",
    "DATAVALUE_TYPE", "DATAVALUE_DESCRIPTION", "DATAVALUE_DATETIME",
    "DATAVALUE_DATETIME_START", "DATAVALUE_DATETIME_END", "DATAVALUE_QC",
)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_table(path, delimiter=","):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=delimiter))


def safe_json(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Required regular file missing or symlink: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def parse_timestamp(value):
    value = (value or "").strip()
    if value.endswith(".0"):
        value = value[:-2]
    return datetime.strptime(value, "%Y%m%d%H%M")


def audit_timestamp_file(path, expected_minutes):
    """Scan every row, reporting timeline defects without editing or sorting it."""
    if not path.is_file() or path.is_symlink():
        raise ValueError("Source is missing, non-regular or symlink: " + str(path))
    rows = 0
    first_start = last_start = first_end = last_end = None
    intervals = {}
    duplicate_or_reversed = 0
    discontinuities = 0
    invalid_rows = 0
    prev_start = prev_end = None
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        header = set(reader.fieldnames or [])
        if not {"TIMESTAMP_START", "TIMESTAMP_END"}.issubset(header):
            raise ValueError("Timestamp columns absent: " + str(path))
        for row in reader:
            rows += 1
            try:
                start = parse_timestamp(row.get("TIMESTAMP_START", ""))
                end = parse_timestamp(row.get("TIMESTAMP_END", ""))
                interval = int((end - start).total_seconds() / 60)
                if (end - start).total_seconds() % 60 or interval <= 0:
                    raise ValueError("non-positive or non-minute interval")
            except Exception:
                invalid_rows += 1
                continue
            intervals[interval] = intervals.get(interval, 0) + 1
            if first_start is None:
                first_start, first_end = start, end
            if prev_start is not None:
                delta = (start - prev_start).total_seconds() / 60
                if delta <= 0:
                    duplicate_or_reversed += 1
                elif delta != expected_minutes:
                    discontinuities += 1
                if prev_end is not None and start != prev_end:
                    # Separate interval-boundary discontinuity count from the
                    # start-to-start cadence count; this is diagnostic only.
                    pass
            prev_start, prev_end = start, end
            last_start, last_end = start, end
    observed = ",".join(f"{k}min:{v}" for k, v in sorted(intervals.items())) or "NONE"
    status = "PASS" if (
        rows > 0 and invalid_rows == 0 and duplicate_or_reversed == 0
        and set(intervals) == {expected_minutes}
    ) else "REVIEW"
    return {
        "status": status, "rows": rows, "first_start": str(first_start),
        "first_end": str(first_end), "last_start": str(last_start),
        "last_end": str(last_end), "interval_counts": observed,
        "invalid_rows": invalid_rows, "duplicate_or_reversed_starts": duplicate_or_reversed,
        "start_cadence_discontinuities": discontinuities,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites-root", type=Path, default=DEFAULT_SITES_ROOT)
    ap.add_argument("--stage07-root", type=Path, default=DEFAULT_STAGE07)
    ap.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN)
    args = ap.parse_args()

    stage07 = args.stage07_root.resolve()
    plan_dir = args.plan_dir.resolve()
    for folder in (args.sites_root, stage07, plan_dir):
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Required directory missing or symlink: " + str(folder))
    if not (stage07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Expected Stage07 scientific-hold marker missing; refusing audit")
    if REPO_SITES.is_symlink() or not REPO_SITES.is_file():
        raise ValueError("Repository sites.tsv missing or symlink: " + str(REPO_SITES))

    site_rows = read_table(REPO_SITES, delimiter="\t")
    site_manifest = {r["site"]: r for r in site_rows}
    if len(site_rows) != 10 or len(site_manifest) != 10:
        raise ValueError("Expected ten unique sites in repository sites.tsv")

    exact = safe_json(stage07 / "exact_input_manifest.json")
    selected = {r["site"]: r for r in exact.get("sites", [])}
    if len(selected) != 10 or not AFFECTED.issubset(selected):
        raise ValueError("Stage07 exact input manifest does not contain the expected sites")
    pins = {str(Path(p).resolve()): digest
            for p, digest in exact.get("input_sha256", {}).items()}

    clock = safe_json(plan_dir / "site_utc_offset_inventory.json")
    request_plan = safe_json(plan_dir / "era5land_request_plan.json")
    receipt = safe_json(plan_dir / "evidence_receipt.json")
    if (len(clock) != 7 or len(request_plan) != 32
            or receipt.get("requests") != 32 or receipt.get("event_count") != 1924):
        raise ValueError("Stage09a plan/receipt does not match the pinned 7-site, 32-year scope")
    clock_by_site = {r["site"]: r for r in clock}
    if set(clock_by_site) != AFFECTED:
        raise ValueError("Unexpected site set in clock inventory")

    print("=" * 118)
    print("STAGE09H — READ-ONLY CLOCK METADATA AND RAW TIMESTAMP AUDIT")
    print("Stage07 exact input manifest:", stage07 / "exact_input_manifest.json")
    print("Stage09a clock inventory:", plan_dir / "site_utc_offset_inventory.json")
    print("No UTC conversion, joins, writes, forcing changes, or model jobs.")
    print("=" * 118)

    approved = 0
    unresolved = []
    for site in sorted(AFFECTED):
        info = selected[site]
        manifest_row = site_manifest[site]
        if info.get("release") != manifest_row["package"]:
            raise ValueError("Stage07/repository release mismatch for " + site)
        raw_dir = (args.sites_root / site / "forcing" / "raw" / manifest_row["package"]).resolve()
        if raw_dir.is_symlink() or not raw_dir.is_dir():
            raise ValueError("Raw release directory missing or symlink: " + str(raw_dir))

        print(f"\n========== {site} | release={manifest_row['package']} ==========")
        for kind in ("primary", "era"):
            source = Path(info[kind]).resolve()
            if source.parent != raw_dir:
                raise ValueError(f"{site} {kind} path outside exact release: {source}")
            expected_hash = pins.get(str(source))
            if not expected_hash:
                raise ValueError(f"{site} {kind} source is not SHA-pinned in Stage07 manifest")
            actual_hash = sha256(source)
            if actual_hash != expected_hash:
                raise ValueError(f"{site} {kind} source SHA mismatch: {source}")
            result = audit_timestamp_file(source, int(info["native_minutes"]))
            print(
                f"{kind.upper()} TIMELINE: {result['status']} | {source.name}\n"
                f"  SHA256={actual_hash}\n"
                f"  rows={result['rows']} first={result['first_start']}..{result['first_end']} "
                f"last={result['last_start']}..{result['last_end']}\n"
                f"  intervals={result['interval_counts']} invalid={result['invalid_rows']} "
                f"duplicate/reversed={result['duplicate_or_reversed_starts']} "
                f"start-cadence-discontinuities={result['start_cadence_discontinuities']}"
            )

        bifs = sorted(raw_dir.glob(f"AMF_{site}_FLUXNET_BIF_*.csv"))
        published = clock_by_site[site]
        if site == "US-Me2":
            if bifs:
                print("BIF NOTE: unexpected BIF file(s) found; inspect manually:", [p.name for p in bifs])
                unresolved.append(site)
            else:
                print("UTC_OFFSET: UNRESOLVED — this exact FULLSET release has no BIF.")
                print("  Repository fallback documents coordinates/IGBP only, not UTC_OFFSET.")
                unresolved.append(site)
            continue

        if len(bifs) != 1:
            raise ValueError(f"{site}: expected exactly one release BIF, found {len(bifs)}")
        bif = bifs[0]
        expected_sources = {str(Path(r.get("source", "")).resolve())
                            for r in published.get("metadata_groups", []) if r.get("source")}
        if expected_sources != {str(bif.resolve())}:
            raise ValueError(f"{site}: current BIF path differs from Stage09a clock inventory")
        print("BIF:", bif.name, "| SHA256=", sha256(bif))
        offset_rows = []
        with bif.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not {"VARIABLE", "DATAVALUE"}.issubset(reader.fieldnames):
                raise ValueError("Malformed BIF: " + str(bif))
            for row in reader:
                if (row.get("VARIABLE") or "").strip().upper() == "UTC_OFFSET":
                    offset_rows.append({k: (v or "").strip() for k, v in row.items()
                                        if k and (v or "").strip()})
        values = sorted({r.get("DATAVALUE", "") for r in offset_rows if r.get("DATAVALUE", "")})
        print(f"UTC_OFFSET ROWS: {len(offset_rows)} | unique published values={values}")
        if not offset_rows:
            print("UTC_OFFSET: UNRESOLVED — no UTC_OFFSET row in release BIF.")
            unresolved.append(site)
        else:
            for row in offset_rows:
                useful = {k: row[k] for k in UTC_FIELDS if row.get(k)}
                print("  BIF RECORD:", json.dumps(useful or row, ensure_ascii=False, sort_keys=True))
            print("UTC_OFFSET STATUS: PUBLISHED ONLY; NOT APPROVED FOR JOIN")
            unresolved.append(site)

    print("\n" + "=" * 118)
    print(f"STAGE09H SUMMARY: sites={len(AFFECTED)} BIF_offsets_published={len(AFFECTED)-1} "
          f"offsets_approved={approved} unresolved_clock_sites={','.join(sorted(set(unresolved)))}")
    print("NEXT GATE: review BIF GROUP_ID/date scope and timestamp results; obtain a release-specific clock source for US-Me2.")
    print("READ ONLY: no new files, no UTC alignment, no forcing edits, no model jobs.")
    print("=" * 118)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STAGE09H ERROR:", str(exc), file=sys.stderr)
        raise

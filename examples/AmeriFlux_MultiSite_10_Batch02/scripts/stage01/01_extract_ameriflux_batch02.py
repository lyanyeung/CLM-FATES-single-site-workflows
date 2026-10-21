#!/usr/bin/env python3
"""Stage 01: Batch 02 recursive CSV extraction and structural inventory only.

Adapted from AmeriFlux Batch 01 / FLUXNET_MultiSite_13. Produces no forcing, DATM, CIME
cases or Slurm submissions. Supports nested ZIPs and original release folders.
"""
import argparse
import csv
import json
import hashlib
import os
import re
import stat
from datetime import datetime, timezone
from contextlib import suppress
from itertools import count
from pathlib import Path, PurePosixPath
import shutil
import sys
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile
import zlib
from uuid import uuid4

DEFAULT_ROOT = Path(os.environ.get(
    "FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
MANIFEST = Path(__file__).resolve().parents[2] / "sites.tsv"


def load_sites():
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    required = {"site", "package", "first_year", "last_year"}
    if len(rows) != 10 or any(set(row) != required for row in rows):
        raise RuntimeError("sites.tsv must contain exactly 10 releases and 4 standard columns")
    if len({row["site"] for row in rows}) != 10:
        raise RuntimeError("Duplicate site in sites.tsv")
    for row in rows:
        if (not re.fullmatch(r"US-[A-Za-z0-9]+", row["site"])
                or not re.fullmatch(r"AMF_" + re.escape(row["site"])
                                    + r"_FLUXNET_[A-Za-z0-9_.-]+", row["package"])
                or not re.fullmatch(r"\d{4}", row["first_year"])
                or not re.fullmatch(r"\d{4}", row["last_year"])):
            raise RuntimeError("Invalid manifest row: " + str(row))
    return {row["site"]: row for row in rows}


def file_sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def file_crc32(path):
    result = 0
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            result = zlib.crc32(chunk, result)
    return result & 0xffffffff


def extract_csv(src, output_dir, entry_name, expected_size, expected_crc):
    name = PurePosixPath(entry_name.replace("\\", "/")).name
    if not name.lower().endswith(".csv") or name.lower() in ("toc.csv", "!toc.csv"):
        return
    dest = output_dir / name
    if dest.is_symlink():
        raise RuntimeError("Refusing symlink destination: " + str(dest))
    if dest.exists():
        if (dest.is_file() and dest.stat().st_size == expected_size
                and file_crc32(dest) == expected_crc):
            print("  SKIP identical:", name, flush=True)
            return
        raise RuntimeError("Refusing to overwrite different CSV: " + str(dest))
    partial = output_dir / (name + ".partial")
    if partial.exists():
        raise RuntimeError("Stale .partial exists: " + str(partial))
    try:
        with partial.open("xb") as out:
            shutil.copyfileobj(src, out, length=1024 * 1024)
        if partial.stat().st_size != expected_size or file_crc32(partial) != expected_crc:
            raise RuntimeError("CSV size/CRC check failed: " + name)
        # Create without replacement even if a concurrent process created dest.
        os.link(str(partial), str(dest))
    finally:
        with suppress(FileNotFoundError):
            partial.unlink()
    print("  EXTRACTED:", name, flush=True)


def extract_zip(path, output_dir, tmp_dir, serial, depth=0):
    if depth > 8:
        raise RuntimeError("Nested ZIP depth exceeded: " + str(path))
    with ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            if stat.S_ISLNK(info.external_attr >> 16):
                raise RuntimeError("Symlink member in ZIP: " + info.filename)
            name = PurePosixPath(info.filename.replace("\\", "/")).name
            if name.lower().endswith(".zip"):
                nested = tmp_dir / ("nested_" + str(next(serial)) + ".zip")
                try:
                    print("  NESTED ZIP:", name, flush=True)
                    with archive.open(info) as src, nested.open("xb") as out:
                        shutil.copyfileobj(src, out, length=1024 * 1024)
                    extract_zip(nested, output_dir, tmp_dir, serial, depth + 1)
                finally:
                    with suppress(FileNotFoundError):
                        nested.unlink()
            elif name.lower().endswith(".csv"):
                with archive.open(info) as src:
                    extract_csv(src, output_dir, name, info.file_size, info.CRC)


def source_for(site, package, root, incoming):
    choices = [
        root / site / "forcing" / "packages" / (package + ".zip"),
        root / site / "forcing" / "packages" / package,
        incoming / (package + ".zip"),
        incoming / package,
    ]
    found = [path for path in choices if path.exists()]
    if not found:
        raise FileNotFoundError("Exact package not found in site/forcing/packages or " + str(incoming))
    if len(found) > 1:
        print("  NOTE: multiple sources found; using:", found[0], flush=True)
    if found[0].is_symlink():
        raise RuntimeError("Refusing symlink source: " + str(found[0]))
    return found[0]


def audit(site, release, raw_dir):
    if not raw_dir.is_dir() or raw_dir.is_symlink():
        raise RuntimeError("Missing raw directory or symlink: " + str(raw_dir))
    files = sorted(p for p in raw_dir.iterdir() if p.suffix.lower() == ".csv")
    if any(p.is_symlink() or not p.is_file() for p in files):
        raise RuntimeError("Non-regular CSV output found")
    # Product selection must be site-specific; inventories still list all CSVs.
    products = [p for p in files if re.search(
        r"(?:^|_)" + re.escape(site) + r"(?:_|$)", p.name, flags=re.I)]
    cats = {
        "BIF": [p for p in products if "_BIF_" in p.name.upper()],
        "FLUXMET_HH": [p for p in products if "FLUXMET_HH" in p.name.upper()],
        "ERA5_HH": [p for p in products if "ERA5_HH" in p.name.upper()],
        "FLUXES_HH": [p for p in products if "FLUXES_HH" in p.name.upper()],
        "FULLSET_HH": [p for p in products if "FULLSET_HH_" in p.name.upper()],
        "FULLSET_HR": [p for p in products if "FULLSET_HR_" in p.name.upper()],
    }
    counts = {k: len(v) for k, v in cats.items()}
    print("  AUDIT:", len(files), "CSV", counts, flush=True)
    notes = []
    fullset = "_FULLSET_" in release["package"]
    if fullset:
        met_files = cats["FULLSET_HH"] or cats["FULLSET_HR"]
        if not met_files:
            raise RuntimeError("FULLSET HH/HR CSV missing; inspect actual package structure")
        if not cats["FULLSET_HH"]:
            notes.append("Hourly FULLSET found; do not assume 30-minute resolution")
        if not cats["BIF"]:
            notes.append("FULLSET has no BIF; coordinates/metadata still needed at next stage")
        if not cats["ERA5_HH"]:
            notes.append("No separate ERA5_HH CSV; FULLSET is a distinct source format")
    else:
        if not cats["BIF"] or not cats["FLUXMET_HH"]:
            raise RuntimeError("BIF or FLUXMET_HH CSV missing; inspect package")
        met_files = cats["FLUXMET_HH"]
        if not cats["ERA5_HH"]:
            notes.append("ERA5_HH absent; companion source availability needs review")
    headers = {}
    for path in met_files:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader, [])
            sample = next(reader, [])
        if (not {"TIMESTAMP_START", "TIMESTAMP_END"}.issubset(header)
                or not sample or len(sample) != len(header)):
            raise RuntimeError("Missing timestamp columns or invalid first data row: " + path.name)
        headers[path.name] = {"columns": header, "first_timestamp_start": sample[header.index("TIMESTAMP_START")],
                              "first_timestamp_end": sample[header.index("TIMESTAMP_END")]}
        print("  MET HEADER:", path.name, "|", len(header), "columns", flush=True)
    for note in notes:
        print("  NOTE:", note, flush=True)
    return {
        "site": site, "package": release["package"],
        "source_format": "FULLSET" if fullset else "FLUXNET_v1.3",
        "status": "EXTRACTION_STRUCTURE_ONLY",
        "release_years": [release["first_year"], release["last_year"]],
        "raw_dir": str(raw_dir), "counts": counts, "notes": notes,
        "meteorology_headers": headers,
        "files": [{"name": p.name, "size_bytes": p.stat().st_size} for p in files],
    }


def process(site, release, root, source, audit_only):
    package = release["package"]
    raw = root / site / "forcing" / "raw" / package
    if not audit_only:
        if raw.is_symlink():
            raise RuntimeError("Refusing symlink raw directory: " + str(raw))
        raw.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="amf_nested_", dir=str(source.parent)) as temp:
            tmp = Path(temp)
            serial = count(1)
            if source.is_file():
                print("  SOURCE:", source, flush=True)
                extract_zip(source, raw, tmp, serial)
            elif source.is_dir():
                for entry in sorted(source.rglob("*")):
                    if entry.is_symlink():
                        raise RuntimeError("Symlink in source directory: " + str(entry))
                    if entry.is_file() and entry.suffix.lower() == ".zip":
                        extract_zip(entry, raw, tmp, serial)
                    elif entry.is_file() and entry.suffix.lower() == ".csv":
                        with entry.open("rb") as stream:
                            extract_csv(stream, raw, entry.name, entry.stat().st_size,
                                        file_crc32(entry))
            else:
                raise RuntimeError("Unexpected source type " + str(source))
    result = audit(site, release, raw)
    if source is not None:
        result["source"] = str(source)
        if source.is_file():
            result["source_sha256"] = file_sha256(source)
    return result


def main():
    sites = load_sites()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", nargs="+", choices=list(sites))
    parser.add_argument("--sites-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--incoming-dir", type=Path)
    parser.add_argument("--reports-dir", type=Path)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    root = args.sites_root.expanduser()
    incoming = args.incoming_dir.expanduser() if args.incoming_dir else root / "_incoming_zips"
    chosen = args.sites or list(sites)
    if len(set(chosen)) != len(chosen):
        parser.error("Duplicate --sites values")
    sources = {}
    # Require all selected source packages before writing any extraction output.
    if not args.audit_only:
        for site in chosen:
            sources[site] = source_for(site, sites[site]["package"], root, incoming)
        print("SOURCE PREFLIGHT: {}/{} found".format(len(sources), len(chosen)), flush=True)
    passed, failed = [], []
    for site in chosen:
        print("\n" + "=" * 62 + "\n" + site + " | " + sites[site]["package"]
              + "\n" + "=" * 62, flush=True)
        try:
            passed.append(process(site, sites[site], root, sources.get(site), args.audit_only))
            print("  PASS (EXTRACTION/STRUCTURE ONLY):", site, flush=True)
        except (OSError, ValueError, RuntimeError, BadZipFile, csv.Error, zlib.error, EOFError) as exc:
            failed.append({"site": site, "error": str(exc)})
            print("  FAILED:", site, ":", exc, flush=True)
    print("\nBATCH02 SUMMARY: {}/{} PASS (extraction/structure only); failures: {}".format(
        len(passed), len(chosen), ", ".join(f["site"] for f in failed) or "none"))
    if not args.audit_only:
        reports = args.reports_dir.expanduser() if args.reports_dir else (
            root.parent.parent / "experiments" / "AmeriFlux_MultiSite_10_Batch02" / "reports")
        reports.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
        result = reports / ("stage01_extraction_" + stamp + ".json")
        partial = result.with_suffix(".json.partial")
        if partial.exists():
            raise RuntimeError("Stale report .partial exists: " + str(partial))
        try:
            with partial.open("x", encoding="utf-8") as stream:
                json.dump({"scope": "extraction and structural inventory, not scientific QC",
                           "selected_sites": chosen, "passed": passed, "failed": failed},
                          stream, indent=2)
                stream.write("\n")
            partial.replace(result)
        finally:
            with suppress(FileNotFoundError):
                partial.unlink()
        print("REPORT:", result)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Stage 01: recursive AmeriFlux release extraction, with non-destructive CSV audits.

Based on FLUXNET_MultiSite_13 Stage 01. Produces no forcing, DATM, CIME
cases or Slurm submissions. Supports nested ZIPs and original release folders.
"""
import argparse
import csv
import json
import os
from contextlib import suppress
from itertools import count
from pathlib import Path, PurePosixPath
import shutil
import sys
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile
import zlib

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
    return {row["site"]: row for row in rows}


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
        partial.replace(dest)
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
    return found[0]


def audit(site, release, raw_dir):
    files = sorted(raw_dir.glob("*.csv"))
    cats = {
        "BIF": [p for p in files if "_BIF_" in p.name.upper()],
        "FLUXMET_HH": [p for p in files if "FLUXMET_HH" in p.name.upper()],
        "ERA5_HH": [p for p in files if "ERA5_HH" in p.name.upper()],
        "FLUXES_HH": [p for p in files if "FLUXES_HH" in p.name.upper()],
    }
    counts = {k: len(v) for k, v in cats.items()}
    print("  AUDIT:", len(files), "CSV", counts, flush=True)
    if not cats["BIF"] or not cats["FLUXMET_HH"]:
        raise RuntimeError("BIF or FLUXMET_HH CSV missing; inspect package")
    if not cats["ERA5_HH"]:
        print("  WARNING: ERA5_HH absent; check later forcing source requirements", flush=True)
    return {
        "site": site, "package": release["package"],
        "release_years": [release["first_year"], release["last_year"]],
        "raw_dir": str(raw_dir), "counts": counts,
        "files": [{"name": p.name, "size_bytes": p.stat().st_size} for p in files],
    }


def process(site, release, root, incoming, audit_only):
    package = release["package"]
    raw = root / site / "forcing" / "raw" / package
    if not audit_only:
        source = source_for(site, package, root, incoming)
        raw.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="amf_nested_", dir=str(source.parent)) as temp:
            tmp = Path(temp)
            serial = count(1)
            if source.is_file():
                print("  SOURCE:", source, flush=True)
                extract_zip(source, raw, tmp, serial)
            elif source.is_dir():
                for entry in sorted(source.rglob("*")):
                    if entry.is_file() and entry.suffix.lower() == ".zip":
                        extract_zip(entry, raw, tmp, serial)
                    elif entry.is_file() and entry.suffix.lower() == ".csv":
                        with entry.open("rb") as stream:
                            extract_csv(stream, raw, entry.name, entry.stat().st_size,
                                        file_crc32(entry))
            else:
                raise RuntimeError("Unexpected source type " + str(source))
    return audit(site, release, raw)


def main():
    sites = load_sites()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", nargs="+", choices=list(sites))
    parser.add_argument("--sites-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--incoming-dir", type=Path)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    root = args.sites_root.expanduser()
    incoming = args.incoming_dir.expanduser() if args.incoming_dir else root / "_incoming_zips"
    chosen = args.sites or list(sites)
    passed, failed = [], []
    for site in chosen:
        print("\n" + "=" * 62 + "\n" + site + " | " + sites[site]["package"]
              + "\n" + "=" * 62, flush=True)
        try:
            passed.append(process(site, sites[site], root, incoming, args.audit_only))
            print("  PASS:", site, flush=True)
        except (OSError, ValueError, RuntimeError, BadZipFile) as exc:
            failed.append({"site": site, "error": str(exc)})
            print("  FAILED:", site, ":", exc, flush=True)
    print("\nSUMMARY: {}/{} PASS; failures: {}".format(
        len(passed), len(chosen), ", ".join(f["site"] for f in failed) or "none"))
    if not args.audit_only:
        reports = root.parent.parent / "experiments" / "AmeriFlux_MultiSite_10" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        result = reports / "stage01_extraction_summary.json"
        partial = reports / "stage01_extraction_summary.json.partial"
        if partial.exists():
            raise RuntimeError("Stale report .partial exists: " + str(partial))
        try:
            with partial.open("x", encoding="utf-8") as stream:
                json.dump({"selected_sites": chosen, "passed": passed, "failed": failed},
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

#!/usr/bin/env python3
"""JapanFlux Stage02: inspect outer ZIP members/signatures without extraction.

Read-only: no writes to tower data, no nested-archive expansion and no model jobs.
Prints JSON to stdout. Redirect that output to $HOME if desired.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SAMPLE_MAX = 8192
CODECS = ("utf-8-sig", "cp932", "shift_jis", "latin-1")

def source_type(head: bytes) -> str:
    if head.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "NESTED_ZIP_SIGNATURE"
    if head.startswith(b"\x1f\x8b"):
        return "GZIP_SIGNATURE"
    if head.startswith(b"CDF"):
        return "NETCDF_CLASSIC_SIGNATURE"
    if head.startswith(b"\x89HDF\r\n\x1a\n"):
        return "HDF5_NETCDF4_SIGNATURE"
    if head.startswith(b"PAR1"):
        return "PARQUET_SIGNATURE"
    if b"\x00" in head[:1024]:
        return "BINARY_OR_UNKNOWN"
    return "POSSIBLE_TEXT"

def text_preview(head: bytes) -> dict:
    if b"\x00" in head[:1024]:
        return {}
    for enc in CODECS:
        try:
            decoded = head.decode(enc)
            lines = [line.strip()[:260] for line in decoded.splitlines() if line.strip()]
            return {"encoding_candidate": enc, "first_lines": lines[:3],
                    "comma_count_first_line": lines[0].count(",") if lines else 0,
                    "tab_count_first_line": lines[0].count("\t") if lines else 0}
        except UnicodeDecodeError:
            continue
    return {}

def safe_name(name: str) -> bool:
    posix = PurePosixPath(name.replace("\\", "/"))
    return not posix.is_absolute() and ".." not in posix.parts and not any(":" in s for s in posix.parts)

def inspect_one(site: str, package: str, root: Path, preview_limit: int) -> dict:
    path = root / site / "forcing" / "packages" / (package + ".zip")
    result = {"site": site, "package": package, "path": str(path), "members": []}
    if path.is_symlink() or not path.is_file():
        result["status"] = "MISSING_OR_SYMLINK"
        return result
    try:
        with zipfile.ZipFile(path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            result["outer_member_count"] = len(infos)
            result["zip_bytes"] = path.stat().st_size
            result["outer_uncompressed_bytes"] = sum(i.file_size for i in infos)
            for idx, info in enumerate(infos):
                member = {
                    "name": info.filename,
                    "suffix": PurePosixPath(info.filename).suffix.lower(),
                    "uncompressed_bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "safe_relative_name": safe_name(info.filename),
                    "encrypted": bool(info.flag_bits & 1),
                }
                if idx < preview_limit and info.file_size and not member["encrypted"]:
                    try:
                        with zf.open(info) as src:
                            head = src.read(SAMPLE_MAX)
                        member["signature"] = source_type(head)
                        if member["signature"] == "POSSIBLE_TEXT":
                            member.update(text_preview(head))
                    except (OSError, RuntimeError, EOFError, zipfile.BadZipFile) as exc:
                        member["preview_error"] = str(exc)
                else:
                    member["signature"] = "NOT_SAMPLED"
                result["members"].append(member)
            result["status"] = "INSPECTED"
    except (OSError, RuntimeError, zipfile.BadZipFile, ValueError) as exc:
        result["status"] = "ERROR"
        result["error"] = str(exc)
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--preview-limit", type=int, default=30)
    args = parser.parse_args()
    if not 0 <= args.preview_limit <= 100:
        parser.error("preview-limit must be between 0 and 100")
    with args.manifest.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if len(rows) != 11 or len({r["site"] for r in rows}) != 11:
        parser.error("expected 11 unique JapanFlux sites")
    report = {"stage": "JapanFlux Stage02",
              "mode": "READ_ONLY_OUTER_ZIP_MEMBERS_ONLY_NO_EXTRACTION",
              "sites": [inspect_one(r["site"], r["package"], args.root,
                                    args.preview_limit) for r in rows]}
    report["inspected_count"] = sum(s["status"] == "INSPECTED" for s in report["sites"])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["inspected_count"] == 11 else 1

if __name__ == "__main__":
    raise SystemExit(main())

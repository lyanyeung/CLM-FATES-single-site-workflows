#!/usr/bin/env python3
"""JapanFlux Stage01: read-only source archive inventory (no extraction or modification)."""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path, PurePosixPath
import zipfile

DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DATA_SUFFIXES = {".csv", ".txt", ".tsv", ".dat"}
TAGS = ("FLUXMET_HH", "FLUXMET_HR", "ERA5_HH", "FLUXMET_DD", "BIF", "FULLSET")

def read_manifest(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {"site", "package", "first_year", "last_year"}
    if len(rows) != 11 or not rows or set(rows[0]) != required:
        raise ValueError("Manifest must contain exactly 11 sites with four expected columns")
    if len({row["site"] for row in rows}) != 11:
        raise ValueError("Duplicate site in manifest")
    return rows

def preview(data: bytes):
    for encoding in ("utf-8-sig", "cp932", "shift_jis", "latin-1"):
        try:
            txt = data.decode(encoding).splitlines()
            return {"encoding": encoding, "first_line": (txt[0] if txt else "")[:250]}
        except UnicodeDecodeError:
            continue
    return {"encoding": "unknown", "first_line": ""}

def safe_member(name: str):
    name = name.replace("\\", "/")
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts and not any(":" in part for part in p.parts)

def probe_zip(path: Path, check_crc: bool):
    with zipfile.ZipFile(path) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        names = [i.filename for i in infos]
        unsafe = [n for n in names if not safe_member(n)]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        entry = {
            "kind": "zip", "members_total": len(names),
            "members": names[:300], "member_list_truncated": len(names) > 300,
            "unsafe_member_names": unsafe[:30], "duplicate_member_names": duplicates[:30],
            "zip_total_uncompressed_bytes": sum(i.file_size for i in infos),
            "tags_in_member_names": [tag for tag in TAGS if any(tag in n.upper() for n in names)],
            "sample_headers": [],
        }
        for info in infos:
            if len(entry["sample_headers"]) >= 8:
                break
            if Path(info.filename).suffix.lower() not in DATA_SUFFIXES or not safe_member(info.filename):
                continue
            if info.file_size > 0:
                with zf.open(info) as handle:
                    sample = handle.read(4096)
                entry["sample_headers"].append({"name": info.filename, **preview(sample)})
        if check_crc:
            entry["crc_test"] = "PASS" if zf.testzip() is None else "FAIL"
        else:
            entry["crc_test"] = "NOT_RUN (optional --test-crc)"
        return entry

def probe_dir(path: Path):
    members = []
    sample_headers = []
    symlinks = []
    for root, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
        for name in files:
            full = Path(root) / name
            rel = full.relative_to(path).as_posix()
            if full.is_symlink():
                symlinks.append(rel)
                continue
            members.append(rel)
            if len(sample_headers) < 8 and full.suffix.lower() in DATA_SUFFIXES:
                with full.open("rb") as handle:
                    sample_headers.append({"name": rel, **preview(handle.read(4096))})
    return {
        "kind": "directory", "members_total": len(members),
        "members": members[:300], "member_list_truncated": len(members) > 300,
        "symlinks_not_followed": symlinks[:30],
        "tags_in_member_names": [tag for tag in TAGS if any(tag in n.upper() for n in members)],
        "sample_headers": sample_headers,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--test-crc", action="store_true", help="Full ZIP CRC scan (slower)")
    args = parser.parse_args()
    output = {"stage": "JapanFlux Stage01", "mode": "READ_ONLY_NO_EXTRACTION_NO_MODEL",
              "root": str(args.root), "sites": []}
    for row in read_manifest(args.manifest):
        site, package = row["site"], row["package"]
        parent = args.root / site / "forcing" / "packages"
        zip_path = parent / (package + ".zip")
        dir_path = parent / package
        item = dict(row)
        try:
            if zip_path.is_file() and not zip_path.is_symlink():
                path, data = zip_path, probe_zip(zip_path, args.test_crc)
            elif dir_path.is_dir() and not dir_path.is_symlink():
                path, data = dir_path, probe_dir(dir_path)
            else:
                raise FileNotFoundError("Neither matching ZIP nor matching directory found")
            item.update({"status": "INVENTORIED", "source_path": str(path), "source_bytes": zip_path.stat().st_size if path == zip_path else None, **data})
        except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as exc:
            item.update({"status": "ERROR", "source_path": str(zip_path), "error": str(exc)})
        output["sites"].append(item)
    output["inventoried_count"] = sum(s["status"] == "INVENTORIED" for s in output["sites"])
    output["all_sites_inventoried"] = output["inventoried_count"] == 11
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["all_sites_inventoried"] else 1

if __name__ == "__main__":
    raise SystemExit(main())

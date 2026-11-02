#!/usr/bin/env python3
"""JapanFlux Stage05N — read the complete original alternate 75-line README, once.

Only JP-Tef OR JP-Tmd (same saved README SHA), one original nested ZIP.
Validates original README bytes against both stored Stage05K SHA256 values
and line counts; prints every README line with its original line number.
No flux/met CSV reads; no source edits, no Slurm, no time-gate relaxation.
This DOES NOT approve 45 HOLD candidate repairs or establish time basis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

SITES = ("JP-Tef", "JP-Tmd")
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")


def get_stored_readme(path: Path, site: str) -> dict:
    r = json.loads(path.read_text(encoding="utf-8"))
    if (r.get("stage") != "JapanFlux Stage05K"
            or r.get("site") != site
            or r.get("status") != "READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED"
            or r.get("source_files_modified") is not False
            or r.get("meteorological_rows_read") != 0):
        raise ValueError(f"Unexpected prior source metadata status for {site}")
    docs = [d for d in r.get("site_metadata_and_readme", [])
            if Path(d.get("member", "")).name.lower() == "readme.txt"]
    if len(docs) != 1:
        raise ValueError(f"Expected one saved README metadata record for {site}")
    d = docs[0]
    if not isinstance(d.get("sha256"), str) or len(d["sha256"]) != 64:
        raise ValueError("Missing saved original README SHA256")
    if not isinstance(d.get("line_count"), int) or d["line_count"] < 1:
        raise ValueError("Missing original README line count")
    return d


def extract_one(site: str, package: str, root: Path,
                max_inner_bytes: int, max_readme_bytes: int) -> tuple[bytes, str]:
    path = root / site / "forcing" / "packages" / (package + ".zip")
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or symlinked original package " + str(path))
    with zipfile.ZipFile(path) as outer:
        nested = [i for i in outer.infolist()
                  if not i.is_dir() and i.filename == package + ".zip"]
        if len(nested) != 1:
            raise ValueError("Expected one exact-name nested original JPF ZIP")
        if nested[0].file_size > max_inner_bytes:
            raise ValueError("Nested release would exceed bounded-memory cap")
        with io.BytesIO() as memory:
            with outer.open(nested[0]) as fp:
                n = 0
                while True:
                    block = fp.read(4 * 1024 * 1024)
                    if not block:
                        break
                    n += len(block)
                    if n > max_inner_bytes:
                        raise ValueError("Nested streaming archive exceeded cap")
                    memory.write(block)
            memory.seek(0)
            with zipfile.ZipFile(memory) as inner:
                candidates = [i for i in inner.infolist()
                              if not i.is_dir() and Path(i.filename).name.lower() == "readme.txt"]
                if len(candidates) != 1:
                    raise ValueError("Expected exactly one README.txt in original nested ZIP")
                info = candidates[0]
                if info.file_size > max_readme_bytes:
                    raise ValueError("README too large for bounded text inspection")
                with inner.open(info) as source:
                    data = source.read(max_readme_bytes + 1)
                if len(data) > max_readme_bytes:
                    raise ValueError("README exceeded actual byte cap")
    return data, info.filename


def self_test() -> None:
    payload = b"Header\r\nAnother source edition\r\nNo time convention on these lines\r\n"
    with io.BytesIO() as m:
        with zipfile.ZipFile(m, "w") as z:
            z.writestr("README.txt", payload)
        m.seek(0)
        with zipfile.ZipFile(m) as z:
            raw = z.read("README.txt")
            assert hashlib.sha256(raw).hexdigest() == hashlib.sha256(payload).hexdigest()
            assert len(raw.decode("utf-8-sig").splitlines()) == 3
    print("STAGE05N SELF-TEST PASS | exact README SHA/line handling, NO SOURCE WRITES")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--manifest", type=Path)
    p.add_argument("--stage05k-dir", type=Path)
    p.add_argument("--site", choices=SITES, default="JP-Tef")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--max-inner-mib", type=int, default=256)
    p.add_argument("--max-readme-kib", type=int, default=128)
    a = p.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.manifest or not a.stage05k_dir:
        p.error("Both --manifest and --stage05k-dir required")
    if not 64 <= a.max_inner_mib <= 512 or not 8 <= a.max_readme_kib <= 1024:
        p.error("Safety limits outside expected range")

    stored = {site: get_stored_readme(
        a.stage05k_dir / (site + "_exact_metadata.json"), site)
        for site in SITES}
    hashes = {d["sha256"] for d in stored.values()}
    if len(hashes) != 1:
        raise ValueError("JP-Tef/Tmd saved source README SHA differs; inspect each independently")
    counts = {d["line_count"] for d in stored.values()}
    if len(counts) != 1:
        raise ValueError("JP-Tef/Tmd saved README line counts differ")
    with a.manifest.open(encoding="utf-8-sig", newline="") as f:
        records = list(csv.DictReader(f, delimiter="\t"))
    manifest = {r["site"]: r for r in records}
    if len(records) != 11 or len(manifest) != 11 or a.site not in manifest:
        p.error("Expected exact 11-site original source manifest")

    data, member = extract_one(
        a.site, manifest[a.site]["package"], a.root,
        a.max_inner_mib * 1024 * 1024, a.max_readme_kib * 1024)
    digest = hashlib.sha256(data).hexdigest()
    if digest not in hashes:
        raise ValueError("Original README bytes differ from the saved Stage05K SHA256")
    original_lines = data.decode("utf-8-sig", errors="replace").splitlines()
    if len(original_lines) not in counts:
        raise ValueError("Original README line count differs from Stage05K source")
    print("STAGE05N SOURCE README BYTE VALIDATION PASS")
    print("ORIGINAL_SITE", a.site)
    print("MATCHING_SAVED_SOURCE_SITES", ",".join(SITES))
    print("ORIGINAL_MEMBER", member)
    print("README_SHA256", digest)
    print("README_LINE_COUNT", len(original_lines))
    print("EXACT_SAME_BYTES_FOR_TEF_AND_TMD_SAVED_METADATA", True)
    print("=== ORIGINAL README COMPLETE VERBATIM SOURCE LINES ===")
    for n, text in enumerate(original_lines, 1):
        print(f"README:{n:03d} {text}")
    print("=== END ORIGINAL README ===")
    print("NO ORIGINAL SOURCE MODIFICATIONS; NO UTC TIME-GATE CHANGES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

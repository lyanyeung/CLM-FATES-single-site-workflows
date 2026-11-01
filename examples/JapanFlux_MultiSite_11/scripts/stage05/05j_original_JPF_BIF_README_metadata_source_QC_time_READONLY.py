#!/usr/bin/env python3
"""JapanFlux Stage05J: inspect native JPF metadata/BIF/README, one site.

Read-only; NO Slurm, NO source modifications, NO model jobs or repairs.
Read only small text metadata members, not meteorological CSV row data.
This is an EVIDENCE search, not proof of QC semantics or time-zone origin.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import csv

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SITES = ("JP-Api", "JP-Fhk", "JP-Fjy", "JP-Khw", "JP-Spp",
         "JP-Tak", "JP-Tef", "JP-Tmd", "JP-Yms")
SUFFIXES = (".txt", ".csv", ".tsv", ".md", ".rst", ".json")
TOKENS = ("BIF", "README", "POLICY", "NOTICE", "LICENSE", "METADATA")
CONCEPTS = (
    ("TIME", re.compile(r"TIMESTAMP|TIME.?ZONE|\bUTC\b|\bJST\b|\bJAPAN.STANDARD", re.I)),
    ("QC", re.compile(r"(?:^|[^A-Z])QC(?:[^A-Z]|$)|QUALITY|GAP.?FILL|DOWNSCAL", re.I)),
    ("ERA", re.compile(r"ERA.?5|ERA.?INTERIM|\bERA\b|REANALYSIS", re.I)),
    ("MDS", re.compile(r"\bMDS\b|MARGINAL.DISTRIBUTION", re.I)),
    ("UNITS", re.compile(r"\bUNIT|KPA|PRESSURE|PASCAL|W.?M\W*2|DEGREE.?C", re.I)),
    ("VARIABLE", re.compile(r"TA_F|PA_F|LW_IN_F|VPD_F|SW_IN_F|FLUXMET", re.I)),
)


def classify(name: str) -> bool:
    p = Path(name)
    base = p.name.upper()
    if not base.lower().endswith(SUFFIXES):
        return False
    if "FLUXMET_HH" in base or "ERA5_HH" in base:
        return False
    return any(t in base for t in TOKENS)


def scan_metadata_file(z: zipfile.ZipFile, inf: zipfile.ZipInfo,
                       max_bytes: int, max_lines: int) -> dict:
    result = {"member": inf.filename, "uncompressed_bytes": inf.file_size,
              "sha256": None, "status": None, "matching_line_count": 0,
              "first_line": None, "excerpts": [], "concepts_found": []}
    if inf.file_size > max_bytes:
        result["status"] = "SKIPPED_METADATA_TOO_LARGE"
        return result
    with z.open(inf) as fp:
        raw = fp.read(max_bytes + 1)
    if len(raw) > max_bytes:
        result["status"] = "SKIPPED_METADATA_ABOVE_STREAM_CAP"
        return result
    result["sha256"] = hashlib.sha256(raw).hexdigest()
    doc = raw.decode("utf-8-sig", errors="replace")
    lines = doc.splitlines()
    result["first_line"] = lines[0][:450] if lines else None
    candidates = []
    all_concepts = set()
    for lineno, line in enumerate(lines, 1):
        tags = [key for key, regex in CONCEPTS if regex.search(line)]
        if not tags:
            continue
        result["matching_line_count"] += 1
        all_concepts.update(tags)
        # Prioritize directly informative QC/time/unit metadata, then
        # excerpts that show multiple related concepts. Retain source line IDs.
        score = (6 if "TIME" in tags else 0) + (5 if "QC" in tags else 0) + \
                (3 if "UNITS" in tags else 0) + (2 if "ERA" in tags else 0) + \
                (2 if "MDS" in tags else 0) + len(tags)
        candidates.append((score, lineno, tags, line[:500]))
    best = sorted(candidates, key=lambda v: (-v[0], v[1]))[:max_lines]
    best.sort(key=lambda v: v[1])
    result["excerpts"] = [
        {"line": line, "tags": tags, "text": content}
        for _, line, tags, content in best
    ]
    result["concepts_found"] = sorted(all_concepts)
    result["status"] = "METADATA_READ_ONLY_EXCERPT"
    return result


def inspect(site: str, pkg: str, root: Path,
            max_inner_mib: int, max_doc_mib: int, max_lines: int) -> dict:
    path = root / site / "forcing" / "packages" / (pkg + ".zip")
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Original source ZIP missing or symlinked: {path}")
    with zipfile.ZipFile(path) as outer:
        nested = [info for info in outer.infolist() if not info.is_dir()
                  and info.filename == pkg + ".zip"]
        if len(nested) != 1:
            raise ValueError("Expected exactly one nested original JPF source ZIP")
        limit = max_inner_mib * 1024 * 1024
        if nested[0].file_size > limit:
            raise ValueError("Nested release would exceed memory cap")
        with io.BytesIO() as buffer:
            with outer.open(nested[0]) as fp:
                bytes_read = 0
                while True:
                    chunk = fp.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    if bytes_read > limit:
                        raise ValueError("Nested ZIP exceeded memory cap in stream")
                    buffer.write(chunk)
            buffer.seek(0)
            with zipfile.ZipFile(buffer) as inner:
                infos = [inf for inf in inner.infolist()
                         if not inf.is_dir() and classify(inf.filename)]
                if len(infos) > 50:
                    raise ValueError("Unexpectedly many matching metadata members")
                docs = [scan_metadata_file(inner, inf, max_doc_mib * 1024 * 1024,
                                           max_lines) for inf in infos]
                inventory = [
                    {"name": inf.filename, "bytes": inf.file_size}
                    for inf in inner.infolist() if not inf.is_dir()
                    and ("BIF" in inf.filename.upper() or "README" in inf.filename.upper())
                ]
    return {
        "stage": "JapanFlux Stage05J",
        "site": site, "source_zip": str(path),
        "status": "ORIGINAL_RELEASE_METADATA_READONLY_INSPECTED",
        "nested_zip_uncompressed_bytes": nested[0].file_size,
        "candidate_metadata_member_count": len(docs),
        "metadata_inventory": inventory,
        "metadata_documents": docs,
        "source_zip_writes": 0, "source_data_rows_read": 0,
        "source_time_basis": "NOT_YET_AUTHENTICATED_BY_METADATA",
        "QC_interpretation": "EXCERPTS_ONLY_CHECK_ACTUAL_RELEASE_SPECIFICATION",
        "independent_ERA": "NOT_CHECKED",
        "model_forcing_approved": False,
    }


def self_test() -> None:
    with io.BytesIO() as mem:
        with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("BIF/DEMO_README.txt",
                       "METADATA\nTIMESTAMP_START timezone JST/UTC TBD\n"
                       "TA_F_QC sample QC source\nPA_F units kPa\n"
                       "ERA5_HH not inspected as data\n")
        mem.seek(0)
        with zipfile.ZipFile(mem) as z:
            info = z.getinfo("BIF/DEMO_README.txt")
            one = scan_metadata_file(z, info, 1024 * 1024, 10)
            assert one["status"] == "METADATA_READ_ONLY_EXCERPT"
            assert "TIME" in one["concepts_found"]
            assert "QC" in one["concepts_found"]
            assert one["sha256"]
    assert classify("JP-Fhk_BIF.csv")
    assert not classify("JPF_JP-Fhk_FLUXMET_HH_2000-2022.csv")
    print("STAGE05J SELF-TEST PASS | metadata-only synthetic nested ZIP; no source reads")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=False, type=Path)
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--max-inner-mib", type=int, default=256)
    ap.add_argument("--max-doc-mib", type=int, default=4)
    ap.add_argument("--excerpt-lines", type=int, default=16)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.manifest is None or args.site is None:
        ap.error("--manifest and --site are required without --self-test")
    if not (64 <= args.max_inner_mib <= 512 and
            1 <= args.max_doc_mib <= 8 and 1 <= args.excerpt_lines <= 50):
        ap.error("Safety limits out of bounds")
    with args.manifest.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    manifest = {r["site"]: r for r in rows}
    if len(rows) != 11 or len(manifest) != 11 or args.site not in manifest:
        ap.error("Expected original 11-site manifest")
    print(json.dumps(inspect(args.site, manifest[args.site]["package"], args.root,
                             args.max_inner_mib, args.max_doc_mib,
                             args.excerpt_lines), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

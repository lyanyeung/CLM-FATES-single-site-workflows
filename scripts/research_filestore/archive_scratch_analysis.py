#!/usr/bin/env python3
"""Archive FLUXNET figure analyses from IRIDIS6 Scratch to Research Filestore.

Modes: audit (read-only), copy (SHA256-verified, receipt on RFS),
verify (independent recheck), prune (delete ONLY receipt-verified Scratch images).
No NetCDF, CIME, forcing, raw observations, model histories or restarts touched.
Python 3.9+, standard library only; use on an IRIDIS6 LOGIN node.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RFS = Path("/research/xclimatetbm/ly3n24")
ROOT = RFS / "CLM_FATES"
SCRATCH = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
MODELS = Path("/scratch/ly3n24/CTSM_FATES_OUTPUTS")
SITES = SCRATCH / "sites/MY_EC_SITE"
BATCHES = {
    "FLUXNET_MultiSite_6": ("DE-Hai", "RU-Fyo", "DE-Tha", "DK-Sor", "NL-Loo", "IL-Yat"),
    "FLUXNET_MultiSite_8": ("CZ-BK1", "IT-Ren", "FR-Hes", "FR-FBn", "DE-Hzd", "CH-Dav", "BE-Vie", "IT-Lav"),
    "FLUXNET_MultiSite_11": ("BE-Bra", "FR-Fon", "GL-ZaH", "AT-Neu", "FI-Sod", "CH-Cha", "CH-Fru", "CH-Lae", "CZ-Stn", "IT-Noe", "CH-Aws"),
    "FLUXNET_MultiSite_13": ("DE-Lnf", "DE-Obe", "ES-Agu", "ES-LJu", "IT-Col", "DE-Gri", "DE-RuR", "FI-Hyy", "FI-Let", "FR-Pue", "GF-Guy", "IT-MBo", "IT-Tor"),
}
PICTURES = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".webp", ".tif", ".tiff"}
SUPPORT = {".csv", ".json", ".tsv", ".txt"}
SUPPORT_NAME = re.compile(r"converg|carbon|monthly|metric|summary|statistic|skill|GPP|NEE|metadata|diagnos|compare|evaluation|performance|plot", re.I)
SKIP_DIRS = {".git", "__pycache__", "run", "rest", "restart", "hist", "inputdata",
             "cases", "packages", "packages_multisource_v1", "raw", "archive",
             "recovery_backups", "tmp", "temp", "cache", ".conda"}
DISPLAY_DIRS = {"figures", "figure", "plots", "plot", "analysis", "diagnostics",
                "diagnostic", "validation", "results", "result", "reports", "report"}
DANGEROUS_PARTS = {"run", "rest", "restart", "hist", "archive", "inputdata", "cases", "raw", "packages"}
MODE_CHOICES = ("audit", "copy", "verify", "prune")


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(p):
    s = p.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        raise RuntimeError("Not ordinary non-hardlinked file: {}".format(p))
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def is_under(p, parent):
    try:
        p.relative_to(parent)
        return True
    except ValueError:
        return False


def nfs_check():
    if not RFS.is_dir() or not os.access(str(RFS), os.W_OK):
        raise RuntimeError("RFS missing/not writable on this node: {}".format(RFS))
    result = subprocess.run(["stat", "-f", "-c", "%T", str(RFS)],
                            check=True, capture_output=True, text=True).stdout.strip().lower()
    if result not in ("nfs", "nfs4"):
        raise RuntimeError("Refusing to write/delete: RFS is {} (expected NFS)".format(result))
    print("RFS NFS OK:", RFS)


def walk(root):
    if not root.is_dir() or root.is_symlink():
        return
    for folder, dirs, names in os.walk(str(root), followlinks=False):
        dirs[:] = [x for x in dirs if x.lower() not in SKIP_DIRS and
                   not (Path(folder) / x).is_symlink()]
        for name in names:
            p = Path(folder) / name
            if p.is_symlink() or p.suffix.lower() not in (PICTURES | SUPPORT):
                continue
            try:
                fingerprint(p)
            except (OSError, RuntimeError):
                continue
            yield p


def batches_for_path(p, origin):
    name = str(p)
    explicit = [b for b in BATCHES
                if b.lower() in name.lower() or
                re.search(r"FLUXNET[_-]{}(?!\d)".format(b.rsplit("_", 1)[-1]), name, re.I)]
    if len(explicit) == 1:
        return explicit
    if len(explicit) > 1:
        return []  # ambiguous: do not auto-archive to wrong experiment
    candidates = []
    for batch, sites in BATCHES.items():
        if any(re.search(r"(?<![A-Za-z0-9]){}(?![A-Za-z0-9])".format(re.escape(site)), name)
               for site in sites):
            candidates.append(batch)
    return candidates if len(candidates) == 1 else []


def roots():
    yield "experiments", SCRATCH / "experiments", None
    for batch, sites in BATCHES.items():
        for site in sites:
            yield "sites", SITES / site, batch
    for parent in ("analysis", "figures", "plots", "validation", "results", "reports", "diagnostics"):
        yield "model_outputs", MODELS / parent, None
    # Only dedicated results/analysis directories inside model cases; never scan run/ or archive/.
    if MODELS.is_dir():
        for case in MODELS.iterdir():
            if not case.is_dir() or case.is_symlink() or case.name in ("archive", "recovery_backups"):
                continue
            for part in ("analysis", "figures", "plots", "validation", "results", "diagnostics"):
                yield "model_outputs", case / part, None


def location_key(p, origin):
    if origin == "experiments":
        return Path("scratch_CLM_FATES/experiments") / p.relative_to(SCRATCH / "experiments")
    if origin == "sites":
        return Path("scratch_CLM_FATES/sites/MY_EC_SITE") / p.relative_to(SITES)
    return Path("scratch_CTSM_FATES_OUTPUTS") / p.relative_to(MODELS)


def find_items(selected, min_age):
    now_ns = datetime.now(timezone.utc).timestamp() * 1e9
    floor = min_age * 3600 * 1e9
    grouped = {}
    pic_parents = set()
    for origin, srcroot, forced in roots():
        for p in walk(srcroot):
            if p.suffix.lower() not in PICTURES:
                continue
            if any(t.lower() in DANGEROUS_PARTS for t in p.parts):
                continue
            # Under experiments, require explicit figure context or a likely plot basename.
            context = {x.lower() for x in p.parent.parts}
            if not (context & DISPLAY_DIRS) and not SUPPORT_NAME.search(p.stem):
                continue
            batches = [forced] if forced else batches_for_path(p, origin)
            if len(batches) != 1 or batches[0] not in selected:
                continue
            try:
                sig = fingerprint(p)
                if sig[2] <= 0 or now_ns - sig[3] < floor:
                    continue
            except (OSError, RuntimeError):
                continue
            batch = batches[0]
            key = (batch, origin, str(p))
            grouped[key] = (p, origin, "image")
            pic_parents.add((batch, origin, p.parent))
    for batch, origin, directory in sorted(pic_parents):
        for p in directory.iterdir():
            if p.suffix.lower() not in SUPPORT or not SUPPORT_NAME.search(p.name):
                continue
            if p.is_symlink() or not p.is_file():
                continue
            try:
                sig = fingerprint(p)
                if sig[2] <= 0 or now_ns - sig[3] < floor:
                    continue
            except (OSError, RuntimeError):
                continue
            grouped[(batch, origin, str(p))] = (p, origin, "analysis")
    output = defaultdict(list)
    for (batch, origin, _), (p, _, kind) in sorted(grouped.items()):
        output[batch].append((p, location_key(p, origin), kind))
    return output


def dest_for(batch, rel):
    return ROOT / batch / "scratch_analysis_archive" / rel


def receipt_dir(batch):
    return ROOT / batch / "scratch_analysis_archive" / "_receipts"


def no_symlink_parents(p, boundary):
    if not is_under(p, boundary):
        raise RuntimeError("Unsafe destination path: {}".format(p))
    q = p
    while q != boundary:
        if q.is_symlink():
            raise RuntimeError("Symlink in destination path: {}".format(q))
        q = q.parent


def copy_one(src, dest):
    fp0 = fingerprint(src)
    no_symlink_parents(dest, ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    hash_src = sha256(src)
    if fingerprint(src) != fp0:
        raise RuntimeError("Source changed during hashing: {}".format(src))
    if dest.exists():
        if not dest.is_file() or dest.is_symlink() or dest.stat().st_size != fp0[2] or sha256(dest) != hash_src:
            raise RuntimeError("Existing RFS destination differs, refusing overwrite: {}".format(dest))
    else:
        tmp = dest.with_name(dest.name + ".partial-" + uuid.uuid4().hex)
        try:
            with src.open("rb") as from_file, tmp.open("xb") as to_file:
                shutil.copyfileobj(from_file, to_file, 4 * 1024 * 1024)
            if sha256(tmp) != hash_src:
                raise RuntimeError("Temporary copy SHA256 differs: {}".format(src))
            os.replace(str(tmp), str(dest))
        finally:
            if tmp.exists():
                tmp.unlink()
    if fingerprint(src) != fp0 or sha256(dest) != hash_src:
        raise RuntimeError("Source/destination changed during transfer: {}".format(src))
    return {"source": str(src), "dest": str(dest), "sha256": hash_src,
            "fingerprint": fp0, "kind": "image" if src.suffix.lower() in PICTURES else "analysis"}


def save_receipt(batch, rows):
    directory = receipt_dir(batch)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = directory / "{}_{}.json".format(stamp, uuid.uuid4().hex[:8])
    doc = {"format": "fluxnet_scratch_figures_v1", "batch": batch,
           "verified_utc": datetime.now(timezone.utc).isoformat(),
           "description": "copy and SHA256 check completed; original Scratch files retained",
           "entries": rows}
    with dest.open("x", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    return dest


def read_receipt(receipt, selected):
    if receipt.is_symlink():
        raise RuntimeError("Receipt is symlink")
    p = receipt.absolute()
    if not p.is_file():
        raise RuntimeError("Receipt not found: {}".format(p))
    doc = json.loads(p.read_text(encoding="utf-8"))
    batch = doc.get("batch")
    if doc.get("format") != "fluxnet_scratch_figures_v1" or batch not in selected:
        raise RuntimeError("Receipt format/batch invalid: {}".format(receipt))
    if p.parent != receipt_dir(batch):
        raise RuntimeError("Receipt must be from standard RFS _receipts directory")
    return doc


def check_entry(batch, entry, require_source=True):
    src = Path(entry["source"])
    dest = Path(entry["dest"])
    kind = entry["kind"]
    if kind not in ("image", "analysis"):
        raise RuntimeError("Invalid receipt kind")
    if src.is_symlink() or dest.is_symlink() or not src.is_file() or not dest.is_file():
        raise RuntimeError("Missing or symlink file: {}".format(src))
    candidates = []
    if is_under(src, SCRATCH / "experiments"):
        candidates = batches_for_path(src, "experiments")
        rel = location_key(src, "experiments")
    elif is_under(src, SITES):
        site = src.relative_to(SITES).parts[0]
        candidates = [b for b, sites in BATCHES.items() if site in sites]
        rel = location_key(src, "sites")
    elif is_under(src, MODELS):
        candidates = batches_for_path(src, "model_outputs")
        rel = location_key(src, "model_outputs")
    else:
        raise RuntimeError("Source outside approved Scratch trees")
    if candidates != [batch] or dest != dest_for(batch, rel):
        raise RuntimeError("Receipt path/batch mismatch: {}".format(src))
    if any(x.lower() in DANGEROUS_PARTS for x in src.parts):
        raise RuntimeError("Source inside protected area: {}".format(src))
    no_symlink_parents(dest, ROOT)
    if kind == "image" and src.suffix.lower() not in PICTURES:
        raise RuntimeError("Non-image marked image")
    if kind == "analysis" and (src.suffix.lower() not in SUPPORT or not SUPPORT_NAME.search(src.name)):
        raise RuntimeError("Non-analysis receipt row")
    if fingerprint(src) != entry["fingerprint"]:
        raise RuntimeError("Source changed after copy: {}".format(src))
    if sha256(src) != entry["sha256"] or sha256(dest) != entry["sha256"]:
        raise RuntimeError("SHA256 mismatch: {}".format(src))
    return src


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=MODE_CHOICES)
    ap.add_argument("--batch", choices=["all"] + list(BATCHES), default="all")
    ap.add_argument("--receipt", type=Path, help="Required for verify/prune (exact RFS receipt path)")
    ap.add_argument("--confirm", default="", help="prune requires DELETE_VERIFIED_SCRATCH_IMAGES")
    ap.add_argument("--min-age-hours", type=float, default=24,
                    help="Only collect files unchanged for this many hours (default 24)")
    args = ap.parse_args()
    if args.min_age_hours < 0:
        ap.error("--min-age-hours must be >=0")
    selected = list(BATCHES) if args.batch == "all" else [args.batch]
    if args.mode in ("copy", "verify", "prune"):
        nfs_check()
    if args.mode in ("verify", "prune"):
        if not args.receipt:
            ap.error("verify/prune require --receipt /research/.../_receipts/NAME.json")
        doc = read_receipt(args.receipt, selected)
        batch = doc["batch"]
        if args.mode == "prune" and args.confirm != "DELETE_VERIFIED_SCRATCH_IMAGES":
            ap.error("prune requires --confirm DELETE_VERIFIED_SCRATCH_IMAGES")
        valid = 0
        removed = 0
        for row in doc["entries"]:
            src = check_entry(batch, row)
            valid += 1
            if args.mode == "prune" and row["kind"] == "image":
                # Recheck after hashing; never delete associated CSV/JSON/TSV.
                if fingerprint(src) != row["fingerprint"]:
                    raise RuntimeError("Source modified during check: {}".format(src))
                src.unlink()
                removed += 1
                print("REMOVED IMAGE:", src)
        print("VERIFIED: {} files | SCRATCH IMAGES REMOVED: {}".format(valid, removed))
        return 0

    data = find_items(selected, args.min_age_hours)
    total = sum(len(items) for items in data.values())
    print("MODE:", args.mode, "| found", total, "eligible files; minimum age hours:", args.min_age_hours)
    for batch in selected:
        rows = data[batch]
        pics = sum(kind == "image" for _, _, kind in rows)
        bytes_count = sum(p.stat().st_size for p, _, _ in rows)
        print("{}: {} images, {} companion analyses, {:.3f} GiB".format(
            batch, pics, len(rows)-pics, bytes_count/(1024**3)))
        if args.mode == "audit":
            for p, _, kind in rows:
                print("  {} {}".format(kind.upper(), p))
        elif rows:
            copied = []
            for i, (src, rel, kind) in enumerate(rows, 1):
                copied.append(copy_one(src, dest_for(batch, rel)))
                if i % 25 == 0:
                    print("  {} / {} transferred+SHA256".format(i, len(rows)), flush=True)
            receipt = save_receipt(batch, copied)
            print("TRANSFER VERIFIED:", len(copied), "files")
            print("RECEIPT:", receipt)
            print("To independently verify: python3 -B <script> verify --receipt '{}'".format(receipt))
            print("To delete only these verified Scratch pictures: python3 -B <script> prune --receipt '{}' --confirm DELETE_VERIFIED_SCRATCH_IMAGES".format(receipt))
    if args.mode == "audit":
        print("READ-ONLY: no files written or deleted.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)

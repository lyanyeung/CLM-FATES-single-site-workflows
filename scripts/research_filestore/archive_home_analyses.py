#!/usr/bin/env python3
"""Archive selected FLUXNET Home analyses to Research Filestore (no Home deletion).

audit: read-only; copy: verified copy + receipt stored ONLY on NFS RFS;
verify: check receipt entries and checksums. Works with IRIDIS6 Python 3.9+.
Uses a conservative allowlist; does not scan Home software installations or
Git checkouts. Supports 13-site publication snapshots if explicitly enabled.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
RFS = Path("/research/xclimatetbm/ly3n24")
DEST_BASE = RFS / "CLM_FATES"
BATCHES = tuple("FLUXNET_MultiSite_{}".format(n) for n in (6, 8, 11, 13))
IMAGES = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".tif", ".tiff", ".pdf"}
COMPANIONS = {".csv", ".tsv", ".json", ".md", ".txt"}
SKIP = {".git", "__pycache__", ".conda", ".cache", "cache", "tmp", "temp",
        "node_modules", "run", "hist", "restart", "rest", "raw", "inputdata",
        "packages", "logs"}
SNAPSHOT_PREFIX = "FLUXNET13_PUBLICATION_"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def info(path):
    if path.is_symlink():
        raise ValueError("Refusing symlink: {}".format(path))
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError("Not a regular file: {}".format(path))
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)


def is_descendant(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def nfs_guard():
    if not RFS.is_dir() or not os.access(str(RFS), os.W_OK):
        raise RuntimeError("RFS not available or not writable on login node")
    p = subprocess.run(["stat", "-f", "-c", "%T", str(RFS)],
                       capture_output=True, text=True, check=True).stdout.strip().lower()
    if p not in ("nfs", "nfs4"):
        raise RuntimeError("RFS path filesystem is {}, not NFS".format(p))
    print("RFS NFS verified:", RFS)


def allowed_sources(include_snapshots):
    """Yield (batch, source top-level directory, meaningful output roots)."""
    fixed = (
        ("FLUXNET_MultiSite_6", "six_site_spinup1000_final"),
        ("FLUXNET_MultiSite_8", "seven_site_spinup500_final"),
        ("FLUXNET_MultiSite_8", "eight_site_targeted_review"),
        ("FLUXNET_MultiSite_13", "CLM_FATES_13_checkpoint"),
    )
    for batch, name in fixed:
        top = HOME / name
        if top.is_dir() and not top.is_symlink():
            yield batch, top, [top]
    # Original eleven-site job staging; typically already copied by Stage 21.
    for top in sorted(HOME.glob("plot11_1000_HOME_*")):
        results = top / "results"
        if top.is_dir() and not top.is_symlink() and results.is_dir() and not results.is_symlink():
            yield "FLUXNET_MultiSite_11", top, [results]
    # Plot checkouts are Git trees. Archive ONLY their generated result directories,
    # never duplicate all committed figures or code.
    for top in sorted(HOME.glob("CLM-FATES-11site-plot-*")):
        if not top.is_dir() or top.is_symlink():
            continue
        sub = [top / name for name in ("results", "analysis_outputs", "plot_outputs")
               if (top / name).is_dir() and not (top / name).is_symlink()]
        if sub:
            yield "FLUXNET_MultiSite_11", top, sub
    if include_snapshots:
        for top in sorted(HOME.glob(SNAPSHOT_PREFIX + "*")):
            if top.is_dir() and not top.is_symlink():
                # Preserve the historical publication image/report snapshots,
                # but exclude any repository Git metadata.
                yield "FLUXNET_MultiSite_13", top, [top]


def iter_files(root):
    if not root.is_dir() or root.is_symlink():
        return
    for parent, dirs, names in os.walk(str(root), followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP and
                   not (Path(parent) / d).is_symlink()]
        for name in sorted(names):
            p = Path(parent) / name
            if p.suffix.lower() not in IMAGES | COMPANIONS or p.is_symlink():
                continue
            try:
                s = info(p)
                if s[2] <= 0:
                    continue
            except (OSError, ValueError):
                continue
            yield p


def collect(include_snapshots, batches):
    """Copy only figures and companions from directories that contain figures."""
    allgroups = defaultdict(list)
    seen = set()
    for batch, top, roots in allowed_sources(include_snapshots):
        if batch not in batches:
            continue
        for root in roots:
            found = list(iter_files(root))
            parents = {p.parent for p in found if p.suffix.lower() in IMAGES}
            for p in found:
                if p.suffix.lower() not in IMAGES and p.parent not in parents:
                    continue
                key = (batch, str(p))
                if key in seen:
                    continue
                seen.add(key)
                allgroups[batch].append((top, p, "image" if p.suffix.lower() in IMAGES else "analysis"))
    return allgroups


def destination(batch, top, src):
    # Preserve Home directory and relative path to distinguish analysis versions.
    return DEST_BASE / batch / "home_analysis_archive" / top.name / src.relative_to(top)


def safe_dest(path):
    if not is_descendant(path, DEST_BASE):
        raise RuntimeError("Unsafe destination: {}".format(path))
    parent = path.parent
    while parent != DEST_BASE:
        if parent.is_symlink():
            raise RuntimeError("Symlink destination parent: {}".format(parent))
        parent = parent.parent


def already_eleven_final(src, top, batch):
    # Existing eleven-site RFS final is independently verified by Stage21.
    if batch != "FLUXNET_MultiSite_11":
        return None
    try:
        rel = src.relative_to(top / "results")
    except ValueError:
        return None
    old = DEST_BASE / batch / "spinup1000_final" / rel
    if old.is_file() and not old.is_symlink() and old.stat().st_size == src.stat().st_size:
        if sha256(old) == sha256(src):
            return old
    return None


def do_copy(batch, top, src, kind):
    original = list(info(src))
    digest = sha256(src)
    if list(info(src)) != original:
        raise RuntimeError("Source changed during hashing: {}".format(src))
    old = already_eleven_final(src, top, batch)
    dest = old if old is not None else destination(batch, top, src)
    safe_dest(dest)
    if old is None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if dest.is_symlink() or not dest.is_file() or sha256(dest) != digest:
                raise RuntimeError("Existing RFS destination differs: {}".format(dest))
        else:
            tmp = dest.with_name(dest.name + ".partial-" + uuid.uuid4().hex[:8])
            try:
                with src.open("rb") as fi, tmp.open("xb") as fo:
                    shutil.copyfileobj(fi, fo, 4 * 1024 * 1024)
                if sha256(tmp) != digest:
                    raise RuntimeError("SHA256 mismatch on staged copy: {}".format(src))
                os.replace(str(tmp), str(dest))
            finally:
                if tmp.exists():
                    tmp.unlink()
    if sha256(dest) != digest or list(info(src)) != original:
        raise RuntimeError("Source/destination changed: {}".format(src))
    return {"source": str(src), "dest": str(dest), "sha256": digest,
            "fingerprint": original, "kind": kind,
            "existing_final_rfs": bool(old), "home_folder": top.name}


def save_receipt(batch, entries):
    folder = DEST_BASE / batch / "home_analysis_archive" / "_receipts"
    safe_dest(folder / "receipt.json")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = folder / "{}_{}.json".format(stamp, uuid.uuid4().hex[:8])
    content = {"format": "fluxnet_home_analyses_v1", "batch": batch,
               "verified_utc": datetime.now(timezone.utc).isoformat(),
               "entries": entries, "home_cleanup_authorized": False}
    with p.open("x", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
        f.write("\n")
    return p


def do_verify(receipt, batch_arg):
    if receipt.is_symlink() or not receipt.is_file():
        raise RuntimeError("Receipt missing or symlink")
    record = json.loads(receipt.read_text(encoding="utf-8"))
    batch = record.get("batch")
    if batch not in BATCHES or (batch_arg != "all" and batch != batch_arg):
        raise RuntimeError("Receipt batch mismatch")
    if (record.get("format") != "fluxnet_home_analyses_v1" or
            receipt.absolute().parent != DEST_BASE / batch / "home_analysis_archive" / "_receipts"):
        raise RuntimeError("Receipt location or format invalid")
    checked = 0
    for entry in record["entries"]:
        p = Path(entry["source"])
        d = Path(entry["dest"])
        top = HOME / entry["home_folder"]
        if not is_descendant(p, top) or not is_descendant(top, HOME):
            raise RuntimeError("Source outside allowed Home tree")
        valid = [x[1] for x in allowed_sources(True) if x[0] == batch]
        if top not in valid:
            raise RuntimeError("Source top-level directory not allowed")
        permitted = destination(batch, top, p)
        old = already_eleven_final(p, top, batch)
        if d != permitted and (old is None or d != old):
            raise RuntimeError("Unexpected RFS destination")
        safe_dest(d)
        if list(info(p)) != entry["fingerprint"]:
            raise RuntimeError("Source changed: {}".format(p))
        if sha256(p) != entry["sha256"] or sha256(d) != entry["sha256"]:
            raise RuntimeError("Source/destination SHA256 mismatch: {}".format(p))
        checked += 1
    print("VERIFIED:", batch, checked, "files. NO FILES DELETED.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("audit", "copy", "verify"))
    ap.add_argument("--batch", choices=["all"] + list(BATCHES), default="all")
    ap.add_argument("--include-snapshots", action="store_true",
                    help="Also archive versioned FLUXNET13_PUBLICATION_* snapshots")
    ap.add_argument("--details", action="store_true", help="List each candidate")
    ap.add_argument("--receipt", type=Path, help="Required by verify")
    args = ap.parse_args()
    if args.mode in ("copy", "verify"):
        nfs_guard()
    if args.mode == "verify":
        if not args.receipt:
            ap.error("--receipt is required for verify")
        do_verify(args.receipt, args.batch)
        return
    batches = BATCHES if args.batch == "all" else (args.batch,)
    groups = collect(args.include_snapshots, batches)
    print("MODE:", args.mode, "| SNAPSHOTS:", args.include_snapshots)
    print("Ignored unrelated Home R/, fcm/, CARDAMOM/ and Git checkouts.")
    for batch in batches:
        items = groups.get(batch, [])
        images = sum(1 for _, _, k in items if k == "image")
        total = sum(info(p)[2] for _, p, _ in items)
        print("{}: {} images, {} companion files, {:.2f} MiB".format(
            batch, images, len(items) - images, total / (1024**2)))
        if args.details:
            for top, src, k in items:
                print("  {} {}".format(k.upper(), src))
        if args.mode == "copy" and items:
            entries = []
            for i, (top, src, kind) in enumerate(items, 1):
                entries.append(do_copy(batch, top, src, kind))
                if i % 25 == 0:
                    print("  {} / {} SHA256 verified".format(i, len(items)), flush=True)
            receipt = save_receipt(batch, entries)
            already = sum(bool(x["existing_final_rfs"]) for x in entries)
            print("TRANSFER VERIFIED:", len(entries), "| already in 11-site final:", already)
            print("RECEIPT:", receipt)
    if args.mode == "audit":
        print("READ-ONLY. No files created or deleted.")
    else:
        print("ALL HOME SOURCES RETAINED. This tool NEVER deletes Home files.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)

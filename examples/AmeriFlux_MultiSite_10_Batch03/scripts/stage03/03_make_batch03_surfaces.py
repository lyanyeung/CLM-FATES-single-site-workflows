#!/usr/bin/env python3
"""Stage 03: Batch 03 CTSM year-2000 point surfaces in isolated output directories.

Default --check is read-only. --run preflights all ten sites before writing.
Reuse prior reference-surface settings; no --dompft, forcing, cases or Slurm jobs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

# Keep default check mode free of bytecode-cache writes when importing Stage 02.
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path(os.environ.get("CLM_FATES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES"))
OUTPUT = "subset_data_batch03_surf2000"
RECEIPT = "batch03_surface_receipt.json"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def snapshot(out):
    result = {}
    for path in sorted(out.rglob("*")):
        name = str(path.relative_to(out))
        if name == RECEIPT:
            continue
        if path.is_symlink():
            result[name] = {"symlink": os.readlink(path)}
        elif path.is_file():
            result[name] = {"sha256": digest(path), "bytes": path.stat().st_size}
    return result


def config_text(template):
    # Same three substitutions as AmeriFlux Batch 01 / ICOS reference workflows.
    text = template.read_text(encoding="utf-8")
    text = text.replace("dir = lnd/clm2/surfdata_esmf/ctsm5.4.0",
                        "dir = lnd/clm2/surfdata_esmf/ctsm5.3.0")
    if "dir = lnd/clm2/surfdata_esmf/ctsm5.3.0" not in text:
        raise RuntimeError("Template surfdata directory changed; inspect before generation")
    for key, value in (
            ("surfdat_16pft", "surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc"),
            ("mesh_surf", "fv0.9x1.25_141008_ESMFmesh.nc")):
        text, count = re.subn(r"(?m)^(\s*" + key + r"\s*=)[^\n]*$",
                              lambda m: m.group(1) + " " + value, text)
        if count != 1:
            raise RuntimeError("Template must have one {} key, found {}".format(key, count))
    return text


def load_metadata(sites_root):
    helper = HERE / "scripts/stage02/02_check_batch03_metadata.py"
    spec = importlib.util.spec_from_file_location("batch03_metadata", str(helper))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.table(HERE / "sites.tsv")
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        raise RuntimeError("Expected ten distinct manifest sites")
    for row in rows:
        if (not re.fullmatch(r"US-[A-Za-z0-9]+", row["site"])
                or not re.fullmatch(r"AMF_" + re.escape(row["site"])
                                    + r"_FLUXNET_[A-Za-z0-9_.-]+", row["package"])):
            raise RuntimeError("Invalid manifest site/package")
    fallback_rows = module.table(HERE / "metadata_fallbacks.tsv")
    if len(fallback_rows) != 1 or {r["site"] for r in fallback_rows} != {"US-Me2"}:
        raise RuntimeError("Expected one US-Me2 FULLSET metadata fallback")
    fallbacks = {r["site"]: r for r in fallback_rows}
    decision_rows = module.table(HERE / "coordinate_decisions.tsv")
    if len(decision_rows) != 2 or {r["site"] for r in decision_rows} != {"US-Mpj", "US-MtB"}:
        raise RuntimeError("Expected the two explicit BIF coordinate decisions")
    decisions = {r["site"]: r for r in decision_rows}
    for site, decision in decisions.items():
        matched = next((r for r in rows if r["site"] == site), None)
        if matched is None or decision["package"] != matched["package"]:
            raise RuntimeError("Coordinate decision mismatches release: " + site)
    return [module.inspect(row, sites_root, fallbacks, decisions) for row in rows]


def outputs_complete(out, site):
    surfaces = list(out.glob("surfdata*.nc"))
    mods = out / "user_mods"
    cfg = out / (site + "_data.cfg")
    if (len(surfaces) != 1 or not surfaces[0].is_file() or surfaces[0].is_symlink()
            or surfaces[0].stat().st_size == 0 or not mods.is_dir() or mods.is_symlink()
            or not any(p.is_file() for p in mods.rglob("*")) or not cfg.is_file()):
        raise RuntimeError("Missing/ambiguous surface, user_mods or config: " + str(out))
    return surfaces[0]


def config_only(out, site, expected_hash):
    cfg = out / (site + "_data.cfg")
    return (out.is_dir() and not out.is_symlink() and list(out.iterdir()) == [cfg]
            and cfg.is_file() and not cfg.is_symlink() and digest(cfg) == expected_hash)


def interpreter_preflight(subset, ctsm):
    print("PYTHON:", sys.executable, flush=True)
    print("CONDA ENV:", os.environ.get("CONDA_DEFAULT_ENV", "not reported"), flush=True)
    # Run the actual tool's imports with the SAME interpreter as this driver.
    # Do not let the tool's shebang silently select a different Python.
    result = subprocess.run([sys.executable, "-B", str(subset), "point", "--help"],
                            cwd=str(ctsm), capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError("CTSM dependency preflight failed under " + sys.executable
                           + "; no output directories created or moved.\n"
                           + result.stdout[-2000:] + result.stderr[-5000:])
    print("PYTHON/CTSM IMPORT PREFLIGHT: PASS", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--clm-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--recover-config-only", action="store_true",
                        help="Preserve and restart an incomplete directory ONLY if it contains the exact expected config and nothing else")
    args = parser.parse_args()
    root = args.clm_root.expanduser().resolve()
    ctsm, inputdata = root / "CTSM", root / "inputdata"
    sites_root = root / "sites/MY_EC_SITE"
    template = ctsm / "tools/site_and_regional/default_data_2000.cfg"
    subset = ctsm / "tools/site_and_regional/subset_data"
    if (not template.is_file() or not inputdata.is_dir() or not subset.is_file()
            or not os.access(subset, os.X_OK)):
        raise RuntimeError("Missing CTSM template, inputdata directory, or executable subset_data")
    text = config_text(template)
    interpreter_preflight(subset, ctsm)
    metadata = load_metadata(sites_root)
    plans = []
    print("MODE:", "--run" if args.run else "--check", flush=True)
    print("CTSM:", ctsm)
    for info in metadata:
        site = info["site"]
        out = sites_root / site / OUTPUT
        expected = {"batch": "AmeriFlux_MultiSite_10_Batch03", "site": site,
                    "package": info["package"], "latitude": info["latitude"],
                    "longitude": info["longitude"], "surf_year": 2000, "dompft": False,
                    "config_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "subset_data_sha256": digest(subset),
                    "metadata_inputs_sha256": {
                        key: digest(HERE / key) for key in (
                            "sites.tsv", "metadata_fallbacks.tsv", "coordinate_decisions.tsv",
                            "scripts/stage02/02_check_batch03_metadata.py")}}
        if out.is_symlink():
            raise RuntimeError("Refusing symlink output: " + str(out))
        if out.exists():
            receipt = out / RECEIPT
            if not out.is_dir() or not receipt.is_file() or receipt.is_symlink():
                if args.recover_config_only and config_only(out, site, expected["config_sha256"]):
                    status = "recover"
                else:
                    raise RuntimeError("Existing output without completion receipt; inspect: " + str(out)
                                       + ". --recover-config-only accepts only an unchanged config file, with no other entries.")
            else:
                saved = json.loads(receipt.read_text(encoding="utf-8"))
                outputs_complete(out, site)
                if saved.get("request") != expected or saved.get("files") != snapshot(out):
                    raise RuntimeError("Existing output differs from request/receipt; preserved: " + str(out))
                status = "skip"
        else:
            status = "new"
        plans.append((info, out, expected, status))
        print("{}: {} lat={} lon={} IGBP={} MET={} SOURCE={}".format(
            {"skip": "SKIP VERIFIED", "recover": "RECOVER CONFIG ONLY", "new": "READY"}[status], site, info["latitude"],
            info["longitude"], "/".join(info["igbp_codes"]) or "NOT_REPORTED",
            "/".join(m["resolution"] for m in info["meteorology"]), info["coordinate_source"]), flush=True)
    skipped = sum(p[3] == "skip" for p in plans)
    print("PREFLIGHT: {} ready + {} verified existing = 10/10".format(10 - skipped, skipped), flush=True)
    if not args.run:
        print("CHECK COMPLETE: no outputs created. --run generates the ten reference point surfaces.")
        return 0
    generated = 0
    for info, out, expected, status in plans:
        if status == "skip":
            continue
        site = info["site"]
        print("\n========== GENERATE {} ==========".format(site), flush=True)
        if status == "recover":
            if not config_only(out, site, expected["config_sha256"]):
                raise RuntimeError("Recovery directory changed after preflight; preserved: " + str(out))
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
            backup = out.with_name(out.name + ".incomplete_" + stamp)
            if backup.exists():
                raise RuntimeError("Recovery backup already exists: " + str(backup))
            out.rename(backup)
            print("PRESERVED CONFIG-ONLY ATTEMPT:", backup, flush=True)
        # Atomic directory creation also blocks a concurrent run from overwriting.
        out.mkdir()
        cfg = out / (site + "_data.cfg")
        with cfg.open("x", encoding="utf-8") as stream:
            stream.write(text)
        command = [sys.executable, "-B", str(subset), "point", "--lat", str(info["latitude"]),
                   "--lon", str(info["longitude"]), "--lon-type", "180",
                   "--site", site, "--surf-year", "2000", "--create-surface",
                   "--create-user-mods", "--inputdata-dir", str(inputdata),
                   "--cfg-file", str(cfg), "--outdir", str(out)]
        subprocess.run(command, cwd=str(ctsm), check=True)
        surface = outputs_complete(out, site)
        receipt = {"request": expected, "coordinate_source": info["coordinate_source"],
                   "metadata_source": info["source"], "igbp_labels": info["igbp_labels"],
                   "native_meteorology": info["meteorology"], "command": command,
                   "files": snapshot(out), "scope": "reference point surface; PFT/landunit QC pending"}
        with (out / RECEIPT).open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
        generated += 1
        print("CREATED:", site, surface, flush=True)
    print("\nSTAGE03 SUMMARY: created={} skipped_verified={} total={}/10".format(
        generated, skipped, generated + skipped))
    print("NEXT: audit actual landunit and PFT fractions; examine US-Kon/US-NR3 grassland, US-Mpj mixed vegetation, US-Me2 disturbance. Meteorology QC pending.")
    print("No forcing/DATM, original site surfaces, CIME cases or Slurm jobs changed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        print("ERROR:", exc, file=sys.stderr)
        print("Existing outputs are preserved. Inspect partial output before rerunning.", file=sys.stderr)
        raise SystemExit(1)

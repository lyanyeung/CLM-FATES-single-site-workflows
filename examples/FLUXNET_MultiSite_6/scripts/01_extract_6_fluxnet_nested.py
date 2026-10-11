#!/usr/bin/env python3

from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from itertools import count
import tempfile
import shutil
import zlib
import sys

ROOT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
)

PACKAGES = {
    "DE-Hai": "ICOS_DE-Hai_FLUXNET_2000-2025_v1.3_r1",
    "RU-Fyo": "EUF_RU-Fyo_FLUXNET_1998-2025_v1.3_r1",
    "DE-Tha": "ICOS_DE-Tha_FLUXNET_1996-2026_v1.3_r1",
    "DK-Sor": "ICOS_DK-Sor_FLUXNET_1996-2024_v1.3_r1",
    "NL-Loo": "ICOS_NL-Loo_FLUXNET_1997-2026_v1.3_r1",
    "IL-Yat": "EUF_IL-Yat_FLUXNET_2000-2024_v1.3_r1",
}

def crc32_file(path):
    crc = 0
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            crc = zlib.crc32(block, crc)
    return crc & 0xffffffff


def extract_recursive(zip_path, raw_dir, temp_dir, serial, depth=0):

    if depth > 5:
        raise RuntimeError("Too many nested ZIP levels")

    with ZipFile(zip_path, "r") as zf:

        for info in zf.infolist():

            if info.is_dir():
                continue

            name = PurePosixPath(
                info.filename.replace("\\", "/")
            ).name

            if not name:
                continue

            lower = name.lower()

            # Extract any ZIP found inside the current ZIP
            if lower.endswith(".zip"):

                print(
                    f"  Nested ZIP found: {name}",
                    flush=True
                )

                nested = temp_dir / f"nested_{next(serial)}.zip"

                with zf.open(info) as src:
                    with open(nested, "wb") as dst:
                        shutil.copyfileobj(src, dst)

                try:
                    extract_recursive(
                        nested,
                        raw_dir,
                        temp_dir,
                        serial,
                        depth + 1
                    )
                finally:
                    nested.unlink(missing_ok=True)

            # Extract data CSV
            elif lower.endswith(".csv"):

                if lower in ("!toc.csv", "toc.csv"):
                    continue

                dest = raw_dir / name

                # Verify existing CSV by size and CRC
                if dest.is_file():
                    if (
                        dest.stat().st_size == info.file_size
                        and crc32_file(dest) == info.CRC
                    ):
                        print(f"  SKIP existing: {name}")
                        continue

                temporary = raw_dir / (name + ".partial")

                with zf.open(info) as src:
                    with open(temporary, "wb") as dst:
                        shutil.copyfileobj(src, dst)

                if temporary.stat().st_size != info.file_size:
                    raise RuntimeError(
                        f"Incomplete extraction: {name}"
                    )

                temporary.replace(dest)

                print(
                    f"  EXTRACTED: {name}",
                    flush=True
                )


successful = []
failed = []

for site, package in PACKAGES.items():

    print("\n" + "=" * 55, flush=True)
    print(f"PROCESSING SITE: {site}", flush=True)
    print("=" * 55, flush=True)

    candidates = [
        ROOT / site / "forcing/packages" / f"{package}.zip",
        ROOT / "_incoming_zips" / f"{package}.zip",
    ]

    zip_path = next(
        (p for p in candidates if p.is_file()),
        None
    )

    if zip_path is None:
        print("ERROR: Outer ZIP not found")
        failed.append(site)
        continue

    raw_dir = ROOT / site / "forcing/raw" / package
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:

        with tempfile.TemporaryDirectory(
            prefix="nested_fluxnet_",
            dir=zip_path.parent
        ) as tmp:

            extract_recursive(
                zip_path,
                raw_dir,
                Path(tmp),
                count(1)
            )

        csv_files = list(raw_dir.glob("*.csv"))

        bif = [
            f for f in csv_files
            if "_BIF_" in f.name.upper()
        ]

        fluxmet = [
            f for f in csv_files
            if "FLUXMET_HH" in f.name.upper()
        ]

        print(f"\nCSV files: {len(csv_files)}")
        print(f"BIF files: {len(bif)}")
        print(f"FLUXMET files: {len(fluxmet)}")

        if not bif or not fluxmet:
            raise RuntimeError(
                "Expected BIF/FLUXMET CSV missing after extraction"
            )

        print(f"SUCCESS: {site}", flush=True)
        successful.append(site)

    except Exception as e:
        print(f"FAILED: {site}: {e}", flush=True)
        failed.append(site)


print("\n" + "=" * 55)
print("FINAL SUMMARY")
print("=" * 55)

print(f"Successful: {len(successful)} / 6")
print("Completed:", ", ".join(successful))
print("Failed:", ", ".join(failed) if failed else "None")

if failed:
    sys.exit(1)

print("\nALL SIX SITES EXTRACTED SUCCESSFULLY")

#!/usr/bin/env python3
"""Stage13b: inspect and optionally unpack an ERA5 CDS pilot response safely.

CDS may deliver a ZIP container even when the destination has a .nc suffix.
This tool identifies the payload by magic bytes (not extension), does not
contact CDS, never rewrites the original, and emits no model forcing.
"""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import sys
import zipfile

MAX_MEMBER_BYTES = 200 * 1024 * 1024
DEFAULT = Path.home() / "AmeriFlux_Batch02_ERA5_dewpoint_pilot" / "US-EML_ERA5_20090101_20090108.nc"


def hexdigest(path):
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            sha.update(block)
    return sha.hexdigest()


def magic(b):
    if b.startswith(b"\x89HDF\r\n\x1a\n"):
        return "NETCDF4_HDF5"
    if b.startswith(b"CDF\x01") or b.startswith(b"CDF\x02") or b.startswith(b"CDF\x05"):
        return "NETCDF3"
    if b.startswith(b"PK\x03\x04") or b.startswith(b"PK\x05\x06") or b.startswith(b"PK\x07\x08"):
        return "ZIP"
    if b.startswith(b"GRIB"):
        return "GRIB"
    if b.startswith(b"\x1f\x8b"):
        return "GZIP"
    return "UNKNOWN"


def inspect_netcdf(path):
    import numpy as np
    import pandas as pd
    import xarray as xr

    print("\n========== NETCDF DATASET ==========")
    print("PATH:", path)
    kind = magic(path.read_bytes()[:8])
    if kind not in ("NETCDF4_HDF5", "NETCDF3"):
        raise ValueError("Not a NetCDF file after extracting: " + str(path))
    engine = "netcdf4"  # Supports NetCDF4 and NetCDF3 in this environment.
    with xr.open_dataset(path, engine=engine) as ds:
        print("FILE TYPE:", kind)
        print("DIMENSIONS:", dict(ds.sizes))
        print("DATA VARIABLES:", list(ds.data_vars))
        print("COORDINATES:", list(ds.coords))
        for var in ds.data_vars:
            da = ds[var]
            print("VARIABLE:", var,
                  "units=", da.attrs.get("units", "(not supplied)"),
                  "dims=", tuple(da.dims),
                  "dtype=", str(da.dtype))
            if np.issubdtype(da.dtype, np.number):
                # 8-day pilot, a tiny amount of data; do not load a full ERA5 archive.
                arr = da.to_numpy()
                nfinite = int(np.isfinite(arr).sum())
                if nfinite:
                    print("  finite=", nfinite,
                          "min=", float(np.nanmin(arr)),
                          "max=", float(np.nanmax(arr)))
                else:
                    print("  all values missing / non-finite")
        for cname in ("time", "valid_time"):
            if cname in ds.coords:
                axis = pd.to_datetime(ds[cname].values.ravel(), errors="coerce", utc=True)
                print("TIME COORDINATE:", cname, "count=", len(axis),
                      "first_UTC=", str(axis.min()),
                      "last_UTC=", str(axis.max()),
                      "duplicates=", bool(axis.duplicated().any()))
        for cname in ("latitude", "longitude", "lat", "lon"):
            if cname in ds.coords:
                values = ds[cname].values.ravel()
                print("POINT COORDINATE:", cname,
                      values[:5].tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--inspect-only", action="store_true",
                        help="Print payload/ZIP member metadata but do not extract")
    args = parser.parse_args()

    src = args.input.expanduser().resolve(strict=True)
    if not src.is_file():
        raise ValueError("Input is not a regular file")
    print("========== CDS PILOT PAYLOAD ==========")
    print("INPUT:", src)
    print("SIZE:", src.stat().st_size)
    print("SHA256:", hexdigest(src))
    with src.open("rb") as stream:
        first = stream.read(32)
    kind = magic(first)
    print("MAGIC HEX:", first[:16].hex())
    print("FORMAT:", kind)
    if kind in ("NETCDF4_HDF5", "NETCDF3"):
        inspect_netcdf(src)
        print("\nPILOT SUCCESS: a directly readable NetCDF.")
        return 0
    if kind != "ZIP" or not zipfile.is_zipfile(src):
        raise ValueError("Not a readable NetCDF or ZIP; do not rename or reinterpret as NetCDF.")

    with zipfile.ZipFile(src, "r") as archive:
        entries = [m for m in archive.infolist() if not m.is_dir()]
        if not entries:
            raise ValueError("ZIP archive has no files")
        print("ZIP MEMBERS:", len(entries))
        for m in entries:
            print("  MEMBER:", repr(m.filename), "bytes=", m.file_size,
                  "compressed=", m.compress_size)
        members = [m for m in entries if m.filename.lower().endswith(".nc")]
        if not members:
            raise ValueError("ZIP contains no *.nc entries; preserve archive for review")
        paths = [PurePosixPath(m.filename) for m in members]
        if any(p.is_absolute() or ".." in p.parts or len(p.parts) != 1 for p in paths):
            raise ValueError("ZIP has nested/unsafe NetCDF member paths; refusing extraction")
        filenames = [p.name for p in paths]
        if len(filenames) != len(set(filenames)):
            raise ValueError("ZIP NetCDF member name collision")
        if any(m.file_size <= 0 or m.file_size > MAX_MEMBER_BYTES for m in members):
            raise ValueError("ZIP pilot member size out of bounds")
        if args.inspect_only:
            print("INSPECT-ONLY: original ZIP left unchanged; nothing extracted")
            return 0
        out = (args.output_dir.expanduser().resolve() if args.output_dir else
               src.parent / (src.stem + "_extracted"))
        if out.exists():
            raise FileExistsError("Refusing to reuse existing extraction directory: " + str(out))
        if out == src.parent or out == src or src in out.parents:
            raise ValueError("Unsafe extraction destination")
        out.mkdir(parents=True, exist_ok=False)
        extracted = []
        for member, name in zip(members, filenames):
            target = out / name
            with archive.open(member, "r") as stream:
                header = stream.read(8)
            if magic(header) not in ("NETCDF4_HDF5", "NETCDF3"):
                raise ValueError("ZIP member does not start with NetCDF magic: " + name)
            with archive.open(member, "r") as instream, target.open("xb") as outstream:
                while True:
                    chunk = instream.read(1048576)
                    if not chunk:
                        break
                    outstream.write(chunk)
            if target.stat().st_size != member.file_size:
                raise ValueError("Extracted member byte size differs: " + name)
            extracted.append(target)
            print("EXTRACTED:", target, "SHA256:", hexdigest(target))
    for path in extracted:
        inspect_netcdf(path)
    print("\nPILOT SUCCESS: ZIP unpacked into a NEW directory; original untouched.")
    print("No DATM, model forcing, tower data or Slurm jobs changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

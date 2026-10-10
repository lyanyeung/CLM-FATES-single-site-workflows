#!/usr/bin/env python3
"""Create a site-specific DATM cycling stream from a proven source case.

Only the cycling settings and the datafiles block are changed. Other stream
settings, in particular datavars, are preserved. This script validates *all*
requested forcing files and writes atomically after successful verification.
"""

import argparse
import re
import sys
from pathlib import Path


def make_stream(source_text: str, site: str, years: range, forcing_dir: Path) -> str:
    if not years:
        raise ValueError("Empty forcing years")
    if years.step != 1:
        raise ValueError("Forcing years must be consecutive")
    for year in years:
        filename = forcing_dir / f"{site}_DATM_{year}.nc"
        if not filename.is_file():
            raise FileNotFoundError(f"Missing forcing file: {filename}")

    out = source_text
    settings = {
        "taxmode": "cycle",
        "year_first": str(years.start),
        "year_last": str(years.stop - 1),
        "year_align": str(years.start),
    }
    for name, value in settings.items():
        pattern = rf"(?m)^[ \t]*CLM_USRDAT\.UNSET:{name}[ \t]*=[^\n]*"
        out, count = re.subn(pattern, f"CLM_USRDAT.UNSET:{name} = {value}", out)
        if count != 1:
            raise ValueError(f"Expected exactly one {name} DATM setting; found {count}")

    paths = [str(forcing_dir / f"{site}_DATM_{year}.nc") for year in years]
    replacement = "CLM_USRDAT.UNSET:datafiles = \\\n" + ", \\\n".join(paths) + "\n\n"
    pattern = (
        r"(?ms)^[ \t]*CLM_USRDAT\.UNSET:datafiles[ \t]*="
        r".*?(?=^[ \t]*CLM_USRDAT\.UNSET:[A-Za-z_]+[ \t]*=|\Z)"
    )
    out, count = re.subn(pattern, lambda _: replacement, out)
    if count != 1:
        raise ValueError(f"Expected exactly one datafiles block; found {count}")

    if not re.search(r"(?m)^[ \t]*CLM_USRDAT\.UNSET:datavars[ \t]*=", out):
        raise ValueError("Missing DATM datavars mapping in source")
    for year in years:
        if out.count(f"{site}_DATM_{year}.nc") != 1:
            raise ValueError(f"DATM year {year} not represented exactly once")
    found_years = set(
        int(x) for x in re.findall(rf"{re.escape(site)}_DATM_(\d{{4}})\.nc", out)
    )
    if found_years != set(years):
        raise ValueError(f"Unexpected DATM years remain: {sorted(found_years)}")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--site", default="GF-Guy")
    p.add_argument("--first", type=int, default=2017)
    p.add_argument("--last", type=int, default=2021)
    p.add_argument("--forcing-dir", type=Path, required=True)
    args = p.parse_args()

    if args.last < args.first:
        p.error("--last must be >= --first")
    if args.source.resolve() == args.output.resolve():
        p.error("Source and output cannot be the same file")
    original = args.source.read_text()
    requested = range(args.first, args.last + 1)
    out = make_stream(original, args.site, requested, args.forcing_dir)

    # Avoid silently overwriting a previous backup. Repeat calls rebuild from
    # source and are deterministic, but we protect the first target contents.
    if args.output.exists():
        backup = args.output.with_name(args.output.name + ".before_spinup")
        if not backup.exists():
            backup.write_text(args.output.read_text())
    tmp = args.output.with_name(args.output.name + ".spinup.tmp")
    tmp.write_text(out)
    tmp.replace(args.output)
    print(f"DATM cycle: {args.first}-{args.last}; {len(requested)} forcing files verified")
    for year in requested:
        print(f"  {args.forcing_dir / f'{args.site}_DATM_{year}.nc'}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

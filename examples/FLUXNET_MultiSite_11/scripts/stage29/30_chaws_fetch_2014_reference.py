#!/usr/bin/env python3
"""Get CH-Aws 2014 ERA5 and ERA5-Land hourly T/Td references only.

Cache is non-overwriting; existing files are validated. Produces no forcing,
CIME cases, source edits, or Slurm submissions. No local script installation
needed when streamed from GitHub with git show ... | python - --fetch.
"""
from __future__ import annotations
import argparse
import json
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import pandas as pd

CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
LAT, LON = 46.583111, 9.790639
API = "https://archive-api.open-meteo.com/v1/archive"
MODELS = ("era5", "era5_land")
YEAR = 2014

def validate(obj, label):
    if obj.get("error"):
        raise RuntimeError(f"{label}: API error: {obj.get('reason')}")
    if int(obj.get("utc_offset_seconds", -1)) != 0:
        raise RuntimeError(f"{label}: time is not UTC")
    hourly = obj.get("hourly", {})
    keys = ("time", "temperature_2m", "dew_point_2m")
    for key in keys:
        if key not in hourly or len(hourly[key]) != 8760:
            raise RuntimeError(f"{label}: missing/incomplete hourly {key}")
    stamps = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="raise"))
    expected = pd.date_range("2014-01-01", "2014-12-31 23:00", freq="h")
    if not stamps.equals(expected):
        raise RuntimeError(f"{label}: hourly UTC timestamps incorrect")
    for key in ("temperature_2m", "dew_point_2m"):
        if any(x is None for x in hourly[key]):
            raise RuntimeError(f"{label}: missing {key} values; inspect manually")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true", help="Read-only cache check")
    mode.add_argument("--fetch", action="store_true", help="Download missing 2014 caches only")
    args = p.parse_args()
    if args.fetch:
        CACHE.mkdir(parents=True, exist_ok=True)
    for model in MODELS:
        dest = CACHE / f"{model}_{YEAR}.json"
        if dest.exists():
            validate(json.loads(dest.read_text()), str(dest))
            print("VERIFIED EXISTING:", dest, flush=True)
            continue
        if args.audit:
            print("MISSING:", dest, flush=True)
            continue
        params = {
            "latitude": LAT, "longitude": LON,
            "start_date": "2014-01-01", "end_date": "2014-12-31",
            "hourly": "temperature_2m,dew_point_2m,relative_humidity_2m",
            "timezone": "GMT", "models": model,
        }
        req = Request(API + "?" + urlencode(params),
                      headers={"User-Agent": "CH-Aws-Stage29-research/1.0"})
        try:
            with urlopen(req, timeout=90) as response:
                raw = response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"STOP: {model} 2014 download failed: {exc}") from exc
        validate(json.loads(raw), f"{model} 2014 download")
        with tempfile.NamedTemporaryFile(dir=CACHE, prefix=f".{model}_2014_",
                                         suffix=".json", delete=False) as tmp:
            tmp.write(raw)
            temp = Path(tmp.name)
        try:
            try:
                os.link(temp, dest)  # fails rather than overwrite
            except FileExistsError as exc:
                raise RuntimeError(f"STOP: concurrent cache creation: {dest}") from exc
        finally:
            temp.unlink(missing_ok=True)
        print(f"SAVED VERIFIED: {dest} ({len(raw)} bytes)", flush=True)
    print("DONE: 2014 caches only; no forcing, cases or Slurm changes")

if __name__ == "__main__":
    main()

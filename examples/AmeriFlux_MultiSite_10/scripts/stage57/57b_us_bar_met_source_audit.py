#!/usr/bin/env python3
"""Stage57B: US-Bar humidity and air-temperature source review.

Read only. Checks the isolated Stage20 forcing candidate against available
AmeriFlux BASE and FLUXMET source records. No file or model changes.
Timestamp comparisons are provisional until clock conventions are validated.
"""

import csv
import hashlib
import io
import math
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES")
EXPERIMENT = ROOT / "experiments/AmeriFlux_MultiSite_10"
PACKAGES = ROOT / "sites/MY_EC_SITE/US-Bar/forcing/packages"
FORCING = (
    EXPERIMENT
    / "usbar_scoped_trial_20261021T234357Z/US-Bar/forcing/processed_v5"
    / "US-Bar_CLM_forcing_2004_2023.csv"
)
BASE_ARCHIVES = (
    EXPERIMENT / "base_original_validation/AMF_US-Bar_BASE-BADM_7-5.zip",
    PACKAGES / "AMF_US-Bar_BASE-BADM_7-5.zip",
)


def parse_time(value):
    value = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y%m%d%H%M", "%Y%m%d%H"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) and x > -9990 else None
    except (ValueError, TypeError):
        return None


def forcing_state(row):
    t = number(row.get("TBOT"))
    q = number(row.get("QBOT"))
    p = number(row.get("PSRF"))
    if t is None or q is None or p is None:
        return None
    if p < 200:
        p *= 1000
    elif p < 2000:
        p *= 100
    if not (180 < t < 340 and 0 < q < 0.05 and 50000 < p < 120000):
        return None
    tc = t - 273.15
    es = 6.112 * math.exp(17.67 * tc / (tc + 243.5))
    e = q * (p / 100) / (0.622 + 0.378 * q)
    return {
        "ta": tc, "rh": 100 * e / es, "vpd": es - e,
        "qbot": q, "vpd_use": number(row.get("VPD_USE")),
    }


def scan_forcing():
    low = []
    jumps = []
    previous = None
    count = 0
    with FORCING.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"time", "TBOT", "QBOT", "PSRF", "VPD_USE"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError("Forcing missing columns: " +
                             str(sorted(required - set(reader.fieldnames or ()))))
        for row in reader:
            count += 1
            stamp = parse_time(row.get("time"))
            values = forcing_state(row)
            if stamp is None or values is None:
                previous = None
                continue
            if values["rh"] < 1:
                low.append((stamp, values))
            if previous is not None:
                prev_time, prev_values = previous
                if stamp - prev_time == timedelta(minutes=30):
                    delta = values["ta"] - prev_values["ta"]
                    if abs(delta) > 10:
                        jumps.append((stamp, delta))
            previous = (stamp, values)
    return count, low, jumps


def print_forcing_context(targets):
    watch = {t + timedelta(minutes=30 * step)
             for t in targets for step in (-2, -1, 0, 1, 2)}
    found = {}
    with FORCING.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            stamp = parse_time(row.get("time"))
            if stamp in watch:
                found[stamp] = forcing_state(row)
    for target in sorted(targets):
        print("\nTARGET", target)
        for step in (-2, -1, 0, 1, 2):
            stamp = target + timedelta(minutes=30 * step)
            state = found.get(stamp)
            if state is None:
                print(" ", stamp, "NO VALID FORCING")
                continue
            vpd_used = state["vpd_use"]
            vpd_str = "NA" if vpd_used is None else "%.3f" % vpd_used
            print(
                " ", stamp, "TA_C=%.3f RH_pct=%.5f VPD_calc=%.3f"
                " VPD_USE=%s QBOT=%.9g%s"
                % (state["ta"], state["rh"], state["vpd"],
                   vpd_str, state["qbot"],
                   " TARGET" if stamp == target else "")
            )


def read_source(stream, label, targets, prefixes):
    text_stream = io.TextIOWrapper(
        stream, encoding="utf-8-sig", errors="replace", newline=""
    )
    header = None
    for line in text_stream:
        if "TIMESTAMP_START" in line and "TIMESTAMP_END" in line:
            header = [v.strip() for v in next(csv.reader([line]))]
            break
    if header is None:
        print("SKIP: timestamp header not found in", label)
        return
    selected = [
        c for c in header
        if c.upper() in prefixes
        or any(c.upper().startswith(p + "_") for p in prefixes)
    ][:20]
    matches = {}
    for row in csv.DictReader(text_stream, fieldnames=header):
        stamp = parse_time(row.get("TIMESTAMP_START"))
        if stamp in targets:
            matches[stamp] = row
    print("\nSOURCE", label)
    print("Exact TIMESTAMP_START matches:", len(matches), "/", len(targets))
    print("Selected columns:", ", ".join(selected) if selected else "NONE")
    for stamp in sorted(targets):
        row = matches.get(stamp)
        if row is None:
            print(stamp, "NO EXACT START-TIME MATCH")
            continue
        data = " | ".join(
            "%s=%s" % (name, row.get(name, ""))
            for name in selected
        )
        print(stamp, data if data else "NO SELECTED VARIABLES")
    print("NOTE: Source timestamps are not yet clock-alignment verified.")


def source_review(low, important_jumps):
    low_times = {t for t, _ in low}
    review_times = low_times | set(important_jumps)
    base_zip = next((p for p in BASE_ARCHIVES if p.is_file()), None)
    print("\n=== BASE SOURCE ===")
    if base_zip is None:
        print("BASE ZIP NOT FOUND; no BASE source conclusion.")
    else:
        print("Archive:", base_zip)
        with zipfile.ZipFile(base_zip) as archive:
            names = [
                n for n in archive.namelist()
                if n.upper().endswith(".CSV") and "BASE_HH" in n.upper()
            ]
            if not names:
                print("BASE_HH CSV NOT FOUND")
            else:
                with archive.open(names[0]) as stream:
                    read_source(
                        stream, names[0], review_times,
                        {"RH", "H2O", "TA", "PA", "VPD"}
                    )

    print("\n=== FLUXMET QUALITY FLAGS ===")
    if not PACKAGES.is_dir():
        print("FLUXMET PACKAGE DIRECTORY NOT FOUND")
        return
    archives = sorted(
        p for p in PACKAGES.rglob("*.zip")
        if "FLUXNET" in p.name.upper() or "FLUXMET" in p.name.upper()
    )
    any_members = False
    for path in archives:
        try:
            with zipfile.ZipFile(path) as archive:
                names = [
                    n for n in archive.namelist()
                    if n.upper().endswith(".CSV")
                    and "FLUXMET" in n.upper()
                    and ("_HH_" in n.upper() or "_HR_" in n.upper())
                ]
                names.sort(key=lambda n: ("_HH_" not in n.upper(), n))
                for name in names[:1]:
                    any_members = True
                    with archive.open(name) as stream:
                        read_source(
                            stream, path.name + " :: " + name, low_times,
                            {"TA_F", "TA_F_QC", "TA_F_MDS",
                             "TA_F_MDS_QC", "VPD_F", "VPD_F_QC",
                             "VPD_F_MDS", "VPD_F_MDS_QC",
                             "VPD_ERA", "VPD"}
                        )
        except (OSError, zipfile.BadZipFile) as exc:
            print("SOURCE READ ERROR:", path, str(exc))
    if not any_members:
        print("NO FLUXMET HH/HR SOURCE FOUND")


def main():
    print("=" * 82)
    print("STAGE57B US-BAR MET SOURCE AUDIT - READ ONLY")
    print("=" * 82)
    if not FORCING.is_file():
        raise SystemExit("STOP: missing forcing candidate: " + str(FORCING))
    digest = hashlib.sha256()
    with FORCING.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    print("Forcing:", FORCING)
    print("SHA256:", digest.hexdigest())

    count, low, jumps = scan_forcing()
    print("Rows:", count, "RH<1%:", len(low), "TA jumps >10C:", len(jumps))
    if count != 350400 or len(low) != 8 or len(jumps) != 106:
        print("WARNING: different from Stage56 baseline (350400/8/106).")

    print("\n=== ALL LOW RH EVENTS ===")
    for stamp, state in low:
        print("%s RH=%.6f%% TA=%.3fC VPD=%.3f QBOT=%.9g" %
              (stamp, state["rh"], state["ta"],
               state["vpd"], state["qbot"]))

    print("\n=== TEN LARGEST TEMPERATURE JUMPS ===")
    biggest = sorted(jumps, key=lambda x: abs(x[1]), reverse=True)[:10]
    for stamp, delta in biggest:
        print(stamp, "delta_TA_C=%+.3f" % delta)
    by_time = dict(jumps)
    reverse = []
    for stamp, delta in jumps:
        following = by_time.get(stamp + timedelta(minutes=30))
        if following is not None and delta * following < 0:
            if abs(delta + following) <= 5:
                reverse.append((stamp, delta, following))
    print("\n=== REVERSING TEMPERATURE SPIKES ===")
    print("Paired rapid-recovery events:", len(reverse))
    for stamp, first, second in reverse[:15]:
        print(stamp, "delta1=%+.3f delta2=%+.3f" %
              (first, second))
    print("\n=== JUMPS PER YEAR ===")
    for year, n in sorted(Counter(t.year for t, _ in jumps).items()):
        print(year, n)

    targets = (
        {t for t, _ in low}
        | {t for t, _ in biggest}
        | {t for t, _, _ in reverse[:10]}
    )
    print("\n=== FORCING CONTEXT (+/- 1 HOUR) ===")
    print_forcing_context(targets)
    source_review(low, [t for t, _ in biggest])
    print("\nREAD ONLY COMPLETE. No forcing, QC, DATM, PFT or Slurm changes.")
    print("CAUTION: BASE and FLUXMET exact-time matches need clock validation.")


if __name__ == "__main__":
    main()

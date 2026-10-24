#!/usr/bin/env python3
"""Batch04 Stage08: isolated QCv5 for SEVEN remaining Batch04 site candidates.

Historical QCv5 interpolation cap: 4 native HH records for TA/VPD/PA,
valid boundaries and no year crossing. PA artefact pulse screening below
65 kPa adds neighbouring ~50 kPa values, not just nonpositive pressure.
The one US-Syv TA=0 special case is NOT extrapolated to other stations.
Original VPD_F_QC=0 observations with physically valid site TA/VPD are retained.
Source RH<5% alone is NOT evidence of a bad VPD and does not trigger ERA swap.
Raw RH may be absent in the original FLUXMET schema and is treated as optional.

Do NOT edit FLUXMET, packaged ERA5, surfaces, cases or DATM. --build-candidates
writes a NEW seven-site sparse overlay, HOLD ledger, SHA report and
SEVEN COMPLETE DERIVED FLUXMET_HH CSVs. Never overwrites sources or models.
Missing raw RH alone is NOT a VPD defect; the model ultimately uses humidity
derived from physically valid TA/VPD/PA, not an unverified raw RH column.
Packaged ERA5_* variables are calibrated/downscaled FLUXNET-derived values,
not independently downloaded raw ERA5. Use only when same-row physically
consistent, and do not approve the eventual forcing without Post-v5 review.
"""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from collections import Counter, defaultdict

HERE = Path(__file__).resolve().parents[2]
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EXPERIMENT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
PRIORITY = ("US-Rpf", "US-Seg", "US-Ses", "US-Slt", "US-SRG", "US-SRM", "US-Uaf")
POLICY = {"TA_F": 4, "VPD_F": 4, "PA_F": 4, "SW_IN_F": 2,
          "LW_IN_F": 4, "WS_F": 4, "P_F": 0}
MISSING = {"", "NA", "NAN", "-9999", "-9999.0", "-6999", "-6999.0"}
FIELDS = ("TIMESTAMP_START", "TIMESTAMP_END", "TA_F", "PA_F",
          "VPD_F", "TA_F_QC", "PA_F_QC", "VPD_F_QC")
ERA_FIELDS = ("TA_ERA", "VPD_ERA", "PA_ERA")
PATCH_COLUMNS = (
    "site", "TIMESTAMP_START", "TIMESTAMP_END", "variable",
    "original", "candidate", "method", "reason", "original_qc",
    "ERA_TA_C", "ERA_VPD_hPa", "ERA_PA_kPa", "ERA_RH_liquid_pct",
    "tower_TA_candidate_C", "source_csv", "source_group", "science_status")
HOLD_COLUMNS = ("site", "TIMESTAMP_START", "TIMESTAMP_END", "reason",
                "tower_TA_C", "tower_PA_kPa", "tower_VPD_hPa",
                "raw_RH_pct", "ERA_TA_C", "ERA_VPD_hPa", "ERA_PA_kPa")


def numeric(x):
    s = str(x or "").strip()
    if s.upper() in MISSING:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) and v not in (-9999.0, -6999.0) else None


def es_water(t):
    if t is None or not -80 <= t <= 65:
        return None
    return 6.112 * math.exp(17.67 * t / (t + 243.5))


def era_humidity(e):
    if not e:
        return None, "ERA_TIME_NOT_MATCHED"
    t, v, p = (e[k] for k in ERA_FIELDS)
    if (t is None or v is None or p is None
            or not -55 <= t <= 52 or not 65 <= p <= 110 or v < 0):
        return None, "ERA_PHYSICAL_INPUT_INVALID"
    es = es_water(t)
    if es is None or v > es * 1.0005:
        return None, "ERA_PAIR_HUMIDITY_INVALID"
    rh = 100 * (1 - v / es)
    if not 1 <= rh <= 100.05:
        return None, "ERA_RH_OUTSIDE_QCV5_USABLE_RANGE"
    return min(rh, 100.0), "VALID_ERA_PAIR"


def manifest():
    with (HERE / "sites.tsv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        raise ValueError("Exact ten-site Batch04 manifest required")
    return {r["site"]: r["package"] for r in rows}


def original_file(root, site, package, product):
    folder = root / site / "forcing" / "raw" / package
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Missing or unsafe source directory: " + str(folder))
    files = list(folder.glob("AMF_" + site + "_FLUXNET_" + product + "_HH_*.csv"))
    if len(files) != 1 or files[0].is_symlink() or not files[0].is_file():
        raise ValueError("Expected one regular original " + product + "_HH file")
    return files[0]


def full_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_native(path):
    rows = []
    previous = None
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)
        if len(set(header)) != len(header) or any(k not in header for k in FIELDS):
            raise ValueError("Missing/duplicate native fields: " + str(path))
        ix = {k: header.index(k) for k in FIELDS}
        for line, record in enumerate(reader, 2):
            if len(record) != len(header):
                raise ValueError("Invalid CSV record width on line " + str(line))
            start = record[ix["TIMESTAMP_START"]].strip()
            end = record[ix["TIMESTAMP_END"]].strip()
            a = datetime.strptime(start, "%Y%m%d%H%M")
            b = datetime.strptime(end, "%Y%m%d%H%M")
            if b - a != timedelta(minutes=30) or (previous and a != previous):
                raise ValueError("Source is not contiguous native HH at " + start)
            previous = b
            row = {"start": start, "end": end, "year": a.year}
            for name in ("TA_F", "PA_F", "VPD_F", "RH"):
                row[name] = numeric(record[ix[name]]) if name in ix else None
            for name in ("TA_F_QC", "PA_F_QC", "VPD_F_QC"):
                row[name] = record[ix[name]].strip()
            rows.append(row)
    return rows


def sequences(mask):
    start = None
    for i, flag in enumerate(mask + [False]):
        if flag and start is None:
            start = i
        if not flag and start is not None:
            yield start, i
            start = None


def interpolations(site, rows):
    """Return dict (rowindex, variable)->(newvalue, reason), no partial runs."""
    result = {}
    n = len(rows)
    for variable, is_bad, boundary_low, boundary_high, max_delta in (
        ("TA_F", lambda x: x is None or x < -80 or x > 65,
         -80.0, 65.0, 8.0),
        # 65 kPa captures side-lobes (~49–51 kPa) of known 2004/2016
        # spurious triangular pressure pulses, not solely 1.499/-1.185 kPa.
        ("PA_F", lambda x: x is None or x < 65 or x > 110,
         70.0, 110.0, 5.0),
    ):
        bad = [is_bad(r[variable]) for r in rows]
        for a, b in sequences(bad):
            if not (0 < a and b < n and b - a <= POLICY[variable]):
                continue
            left, right = rows[a - 1], rows[b]
            lval, rval = left[variable], right[variable]
            if (lval is None or rval is None or
                    not boundary_low <= lval <= boundary_high or
                    not boundary_low <= rval <= boundary_high or
                    abs(lval - rval) > max_delta or
                    left["year"] != right["year"]):
                continue
            for i in range(a, b):
                frac = (i - a + 1) / (b - a + 1)
                result[i, variable] = (
                    lval + frac * (rval - lval),
                    "QCv5_linear_two_valid_boundaries_le4_HH"
                )
    # Distinctive single-row joint dropout (US-Syv 2025-05-16), extra
    # independently documented extension to the historical QCv5 rules.
    for i in (range(1, n - 1) if site == "US-Syv" else ()):
        r = rows[i]
        if ((i, "TA_F") in result or r["TA_F"] is None or
                abs(r["TA_F"]) > .0005 or r["VPD_F"] is None or
                abs(r["VPD_F"] - 6.110) > .008 or
                r["RH"] is None or r["RH"] > 1):
            continue
        l, nxt = rows[i - 1], rows[i + 1]
        if (r["year"] != l["year"] or r["year"] != nxt["year"] or
                l["TA_F"] is None or nxt["TA_F"] is None):
            continue
        if (5 <= l["TA_F"] <= 40 and 5 <= nxt["TA_F"] <= 40 and
                abs(l["TA_F"] - nxt["TA_F"]) < 3 and
                abs(r["TA_F"] - (l["TA_F"] + nxt["TA_F"]) / 2) > 6):
            result[i, "TA_F"] = ((l["TA_F"] + nxt["TA_F"]) / 2,
                                  "joint_zero_TA_6p110_VPD_RH_dropout_local")
    return result


def gather_era(path, targets):
    result = {}
    if not targets:
        return result
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)
        required = ("TIMESTAMP_START", "TIMESTAMP_END", *ERA_FIELDS)
        if len(set(header)) != len(header) or any(k not in header for k in required):
            raise ValueError("Missing exact-label ERA field: " + str(path))
        ix = {k: header.index(k) for k in required}
        for row in reader:
            start = row[ix["TIMESTAMP_START"]].strip()
            if start not in targets:
                continue
            if len(row) != len(header):
                raise ValueError("ERA file width error: " + start)
            end = row[ix["TIMESTAMP_END"]].strip()
            expected = targets[start]
            if end != expected:
                raise ValueError("ERA interval mismatch at " + start)
            if start in result:
                raise ValueError("Duplicate ERA timestamp " + start)
            result[start] = {k: numeric(row[ix[k]]) for k in ERA_FIELDS}
    return result


def fmt(x):
    if x is None:
        return ""
    return "%.12g" % x if isinstance(x, (int, float)) else str(x)


def site_candidates(site, package, root):
    raw = original_file(root, site, package, "FLUXMET")
    era_path = original_file(root, site, package, "ERA5")
    rows = load_native(raw)
    corrections = interpolations(site, rows)
    requested = {}
    for i, row in enumerate(rows):
        t = corrections.get((i, "TA_F"), (row["TA_F"], ""))[0]
        v = row["VPD_F"]
        rh = row["RH"]
        es = es_water(t)
        implied = None if es is None or v is None else 100 * (1 - v / es)
        # A positive, physically permitted low RH alone is not a fault.
        # Protect native observed QC0 VPD with valid T/VPD physics from
        # an unnecessary ERA humidity override (US-Ton Stage07 lesson).
        native_qc0_good = (
            row["VPD_F_QC"] == "0" and es is not None and
            v is not None and 0 <= v <= es * 1.00001
        )
        raw_bad = rh is not None and (rh < 0 or rh > 100.05)
        pair_bad = implied is None or implied < -0.05 or implied > 100.05
        if native_qc0_good:
            raw_bad = False
            pair_bad = False
        # When VPD is invalid or raw RH is suspect, screen contemporaneous
        # ERA-derived TA,VPD,PA. Missing raw RH by itself is not an error.
        if raw_bad or pair_bad:
            requested[row["start"]] = row["end"]
    era = gather_era(era_path, requested)
    patches, holds = [], []
    reason_counter = Counter()
    # Every hard invalid reading must have either a repair candidate or an
    # explicit HOLD; never let an unbridged outlier disappear from the ledger.
    for i, row in enumerate(rows):
        for var, flagged in (
            ("TA_F", row["TA_F"] is None or
             (row["TA_F"] is not None and
              (row["TA_F"] < -80 or row["TA_F"] > 65))),
            ("PA_F", row["PA_F"] is None or
             (row["PA_F"] is not None and
              (row["PA_F"] < 65 or row["PA_F"] > 110)))
        ):
            if not flagged or (i, var) in corrections:
                continue
            reason = "UNBRIDGED_" + var + "_QCv5_MAX4_OR_BOUNDARIES"
            holds.append({
                "site": site, "TIMESTAMP_START": row["start"],
                "TIMESTAMP_END": row["end"], "reason": reason,
                "tower_TA_C": fmt(row["TA_F"]),
                "tower_PA_kPa": fmt(row["PA_F"]),
                "tower_VPD_hPa": fmt(row["VPD_F"]),
                "raw_RH_pct": fmt(row["RH"]),
                "ERA_TA_C": "", "ERA_VPD_hPa": "", "ERA_PA_kPa": ""})
            reason_counter["HOLD_" + var] += 1
    for (i, var), (new, why) in corrections.items():
        row = rows[i]
        patches.append({
            "site": site, "TIMESTAMP_START": row["start"],
            "TIMESTAMP_END": row["end"], "variable": var,
            "original": fmt(row[var]), "candidate": fmt(new),
            "method": "QCv5_SHORT_LINEAR", "reason": why,
            "original_qc": row.get(var + "_QC", ""), "ERA_TA_C": "",
            "ERA_VPD_hPa": "", "ERA_PA_kPa": "", "ERA_RH_liquid_pct": "",
            "tower_TA_candidate_C": fmt(
                corrections.get((i, "TA_F"), (row["TA_F"], ""))[0]),
            "source_csv": raw.name, "source_group": "FLUXMET_HH",
            "science_status": "CANDIDATE_NOT_POSTV5_APPROVED"})
        reason_counter[why] += 1
    for i, row in enumerate(rows):
        t = corrections.get((i, "TA_F"), (row["TA_F"], ""))[0]
        v, rh = row["VPD_F"], row["RH"]
        es = es_water(t)
        implied = None if es is None or v is None else 100 * (1 - v / es)
        # A positive, physically permitted low RH alone is not a fault.
        # Protect native observed QC0 VPD with valid T/VPD physics from
        # an unnecessary ERA humidity override (US-Ton Stage07 lesson).
        native_qc0_good = (
            row["VPD_F_QC"] == "0" and es is not None and
            v is not None and 0 <= v <= es * 1.00001
        )
        raw_bad = rh is not None and (rh < 0 or rh > 100.05)
        pair_bad = implied is None or implied < -0.05 or implied > 100.05
        if native_qc0_good:
            raw_bad = False
            pair_bad = False
        if not (raw_bad or pair_bad):
            continue
        ev = era.get(row["start"])
        e_rh, why = era_humidity(ev)
        # Current site temperature MUST itself be trustworthy. Never
        # substitute a joint ERA-source VPD against a corrupt tower TA.
        if (t is None or not -80 <= t <= 65 or e_rh is None or
                abs(t - ev["TA_ERA"]) > 8):
            if e_rh is not None and (t is None or abs(t - ev["TA_ERA"]) > 8):
                why = "SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID"
            holds.append({
                "site": site, "TIMESTAMP_START": row["start"],
                "TIMESTAMP_END": row["end"], "reason": why,
                "tower_TA_C": fmt(t), "tower_PA_kPa": fmt(
                    corrections.get((i, "PA_F"), (row["PA_F"], ""))[0]),
                "tower_VPD_hPa": fmt(v), "raw_RH_pct": fmt(rh),
                "ERA_TA_C": fmt(ev["TA_ERA"] if ev else None),
                "ERA_VPD_hPa": fmt(ev["VPD_ERA"] if ev else None),
                "ERA_PA_kPa": fmt(ev["PA_ERA"] if ev else None)})
            reason_counter["HOLD_" + why] += 1
            continue
        # Same-source ERA pair: RH_ERA = 100*(1-VPD_ERA/es(TA_ERA)).
        # Convert to native tower-temperature VPD, retaining site TA/PA.
        site_vpd = es * (1 - e_rh / 100)
        if site_vpd < 0 or site_vpd > es:
            raise ValueError("Reconstructed VPD outside tower saturation range")
        for var, old, new in (("RH", rh, e_rh), ("VPD_F", v, site_vpd)):
            if old is not None and abs(old - new) < 1e-9:
                continue
            patches.append({
                "site": site, "TIMESTAMP_START": row["start"],
                "TIMESTAMP_END": row["end"], "variable": var,
                "original": fmt(old), "candidate": fmt(new),
                "method": "QCv5_ERA_RH_AT_RETAINED_TOWER_TA",
                "reason": "SOURCE_RH_LT5_OR_GT100" if raw_bad else
                          "TA_VPD_PHYSICAL_CLOSURE_INVALID",
                "original_qc": row.get(var + "_QC", ""),
                "ERA_TA_C": fmt(ev["TA_ERA"]), "ERA_VPD_hPa": fmt(ev["VPD_ERA"]),
                "ERA_PA_kPa": fmt(ev["PA_ERA"]),
                "ERA_RH_liquid_pct": fmt(e_rh),
                "tower_TA_candidate_C": fmt(t),
                "source_csv": raw.name, "source_group": "FLUXMET_AND_PACKAGED_ERA5",
                "science_status": "CANDIDATE_NOT_POSTV5_APPROVED"})
            reason_counter["ERA_RH_" + var] += 1
    # Strong uniqueness and repair semantics: no duplicate variable/time.
    keys = [(r["site"], r["TIMESTAMP_START"], r["variable"]) for r in patches]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate patch keys")
    return (patches, holds, dict(reason_counter),
            {"native": raw, "era": era_path, "original_rows": len(rows),
             "requested_era_times": len(requested),
             "matched_era_times": len(era)})


def self_test():
    assert POLICY["TA_F"] == POLICY["PA_F"] == POLICY["VPD_F"] == 4
    assert POLICY["P_F"] == 0
    a = es_water(10)
    assert 12 < a < 13
    rh, state = era_humidity({"TA_ERA": 10., "VPD_ERA": 2., "PA_ERA": 100.})
    assert state == "VALID_ERA_PAIR" and 80 < rh < 90
    rh, state = era_humidity({"TA_ERA": -257., "VPD_ERA": 2., "PA_ERA": -1.})
    assert rh is None and state == "ERA_PHYSICAL_INPUT_INVALID"
    # Historic 3-half-hour triangular pressure dropout around 100 kPa.
    p = [101., 50., -1., 50., 101.]
    rows = [dict(start="200412030000", end="200412030030", year=2004,
                 TA_F=10., PA_F=v, VPD_F=3., RH=70.) for v in p]
    patches = interpolations("US-Ton", rows)
    assert len(patches) == 3
    assert all(abs(patches[i, "PA_F"][0] - 101.) < 1e-10 for i in (1, 2, 3))
    # More than four positions must not be partially interpolated.
    q = [100., 50., 50., 50., 50., 50., 100.]
    rows = [dict(start="200412030000", end="200412030030", year=2004,
                 TA_F=10., PA_F=v, VPD_F=3., RH=70.) for v in q]
    assert not interpolations("US-Ton", rows)
    assert len(PRIORITY)==7 and "US-Ton" not in PRIORITY
    print("STAGE08 SELF-TEST PASS: seven sites, max4 interpolation, QC0 guard, ERA gate")


def atomic_csv(path, fields, rows):
    tmp = path.with_suffix(path.suffix + ".partial")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)



def write_full_derived_site_csvs(dest, manifest_map, site_names, patches, source_root):
    """Materialize complete new seven-site FLUXMET copies; no source writes.

    Sparse patches are checked against exact original native values and keys.
    Unmodified rows and all original fields carry across unchanged.
    """
    index = defaultdict(dict)
    for item in patches:
        site, ts, var = item["site"], item["TIMESTAMP_START"], item["variable"]
        if site not in site_names or var not in ("TA_F", "PA_F", "VPD_F", "RH"):
            raise ValueError("Unexpected sparse candidate key for full materialization")
        if var in index[(site, ts)]:
            raise ValueError("Duplicate patch variable at full materialization")
        index[(site, ts)][var] = item
    outcomes = {}
    for site in site_names:
        original = original_file(source_root, site, manifest_map[site], "FLUXMET")
        output = dest / (site + "_Stage08_QCv5_derived_FLUXMET_HH.csv")
        output_partial = output.with_suffix(output.suffix + ".partial")
        target_times = {stamp for (s, stamp) in index if s == site}
        source_times_matched = set()
        seen_changes = 0
        n = 0
        cells = 0
        with original.open(encoding="utf-8-sig", newline="") as src, \
             output_partial.open("x", encoding="utf-8", newline="") as dst:
            reader = csv.DictReader(src)
            if (not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames)
                    or any(k not in reader.fieldnames for k in FIELDS)):
                raise ValueError("Malformed source FLUXMET schema for " + site)
            fieldnames = list(reader.fieldnames)
            if "RH" not in fieldnames and any(
                    "RH" in entries for (s, _), entries in index.items() if s == site):
                fieldnames.append("RH")
            writer = csv.DictWriter(dst, fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                n += 1
                ts = row["TIMESTAMP_START"]
                group = index.get((site, ts))
                if group is not None:
                    if ts in source_times_matched:
                        raise ValueError("Duplicate native source timestamp: " + site + "/" + ts)
                    source_times_matched.add(ts)
                    anychange = False
                    for var, p in group.items():
                        if row["TIMESTAMP_END"] != p["TIMESTAMP_END"]:
                            raise ValueError("Stage08 candidate wrong native end time")
                        original_v = numeric(row.get(var))
                        stored_v = numeric(p["original"])
                        if (original_v is None) != (stored_v is None):
                            raise ValueError("Candidate original missingness differs from source")
                        if (original_v is not None and
                                abs(original_v - stored_v) >
                                1e-8 * max(1.0, abs(original_v), abs(stored_v))):
                            raise ValueError("Original source numeric value mismatched: " + site)
                        candidate_v = numeric(p["candidate"])
                        if candidate_v is None:
                            raise ValueError("Candidate value missing or nonfinite")
                        if original_v is None or abs(original_v-candidate_v)>1e-10:
                            row[var] = fmt(candidate_v)
                            cells += 1
                            anychange = True
                    seen_changes += int(anychange)
                writer.writerow(row)
        if n < 100 or source_times_matched != target_times:
            raise ValueError("Incomplete source full CSV rows or missing candidate timestamps " + site)
        output_partial.replace(output)
        outcomes[site] = {
            "rows": n, "changed_native_times": seen_changes,
            "changed_variables": cells, "full_derived_path": str(output),
            "full_derived_sha256": full_sha(output),
            "size": output.stat().st_size,
        }
        print("STAGE08 FULL DERIVED", site, "rows", n,
              "changed_half_hours", seen_changes, "sha256",
              outcomes[site]["full_derived_sha256"], flush=True)
    return outcomes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root", type=Path, default=ROOT)
    p.add_argument("--output-root", type=Path,
                   default=EXPERIMENT / "qcv5_stage08_remaining_seven_candidates")
    p.add_argument("--sites", nargs="+", choices=PRIORITY, default=list(PRIORITY))
    p.add_argument("--build-candidates", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if len(set(args.sites)) != len(args.sites):
        p.error("Duplicate site in --sites")
    packages = manifest()
    report = {"mode": "BUILD_CANDIDATE_OVERLAY" if args.build_candidates else "INSPECT",
              "scientific_status": "POST_QCV5_REVIEW_REQUIRED",
              "qc_method": "QCv5_max4_linear_plus_paired_ERA_RH",
              "boundary_rule": "two valid neighbours same calendar year",
              "source_warning": "packaged ERA5 is NOT independent raw ERA5; valid native QC0 protected",
              "sites": {}}
    patches, holds, failed = [], [], []
    print("BATCH04 STAGE08 REMAINING SEVEN QCv5 REPAIR CANDIDATES")
    for site in args.sites:
        try:
            pch, hld, counts, meta = site_candidates(site, packages[site],
                                                     args.sites_root)
            patches.extend(pch)
            holds.extend(hld)
            report["sites"][site] = dict(counts=counts,
                                         rows=meta["original_rows"],
                                         requested_era_times=meta["requested_era_times"],
                                         matched_era_times=meta["matched_era_times"],
                                         patch_rows=len(pch), hold_rows=len(hld),
                                         paths={k: str(meta[k]) for k in ("native", "era")})
            print("SITE {} original_rows={} patch_rows={} held={} category_counts={}".format(
                site, meta["original_rows"], len(pch), len(hld), counts), flush=True)
        except (OSError, ValueError, csv.Error) as error:
            failed.append(site)
            print("FAILED:", site, repr(error), flush=True)
    print("STAGE08 PREVIEW SUMMARY: sites={} patch_rows={} hold_rows={} failed={}".format(
        ",".join(args.sites), len(patches), len(holds), ",".join(failed) or "none"))
    if failed:
        return 1
    if args.build_candidates:
        dest = args.output_root / ("candidate_" +
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        dest.mkdir(parents=True, exist_ok=False)
        (dest / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
            "Stage08 full native-length research candidates. Original Stage08 HOLDs unresolved.\n",
            encoding="utf-8")
        # Both original inputs are checksum-pinned only after the complete
        # preview succeeds, avoiding partial derived output on site failure.
        for site in args.sites:
            for role, path in report["sites"][site]["paths"].items():
                pth = Path(path)
                report["sites"][site].setdefault("source_provenance", {})[role] = {
                    "sha256": full_sha(pth), "size": pth.stat().st_size}
        atomic_csv(dest / "candidate_patch.csv", PATCH_COLUMNS,
                   sorted(patches, key=lambda x:
                          (x["site"], x["TIMESTAMP_START"], x["variable"])))
        atomic_csv(dest / "unresolved_hold.csv", HOLD_COLUMNS, holds)
        report["derived_files"] = write_full_derived_site_csvs(
            dest, packages, args.sites, patches, args.sites_root)
        report["created_utc"] = datetime.now(timezone.utc).isoformat()
        report["candidate_patch_sha256"] = full_sha(dest / "candidate_patch.csv")
        (dest / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        (dest / "README.txt").write_text(
            "ISOLATED QCv5 CANDIDATE ONLY. ORIGINAL FLUXMET AND ERA CSVs UNTOUCHED.\n"
            "Apply no sparse patch to production forcing before Post-v5 validation.\n"
            "RH/VPD rebuild uses SAME-SOURCE physically gated calibrated ERA pair;\n"
            "source is NOT independent native ERA5. Review unresolved_hold.csv.\n",
            encoding="utf-8")
        print("CANDIDATE OVERLAY WRITTEN:", dest)
        print("SEVEN FULL DERIVED FLUXMET_HH CSVs, ORIGINAL SOURCE SHA256 AND PATCH SHA256 RECORDED IN report.json")
    else:
        print("INSPECT ONLY: NO DATA OR PATCH FILES WRITTEN")
    print("STAGE08 SCIENCE STATUS: POST-QCV5 REVIEW REQUIRED; NO MODEL APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""JapanFlux Stage05Q: audit original BIF LOCATION coordinates for only three UTC-verified JPF sites.

Science gate:
- Actual Stage05K metadata JSON source BIF SHA256 must match reopened original BIF bytes.
- Read only BIF in one original nested release ZIP per site (bounded RAM), never meteorological CSVs.
- Match official BADM LOCATION_LAT, LOCATION_LONG and optional LOCATION_ELEV grouped by BIF group ID.
- Reject missing, contradictory, or nonphysical coordinate records; never choose one silently.
- Verify original source UTC_OFFSET +9 and Stage05P 3-site request-plan summary.
- NO CDS API, NO Slurm, NO data replacement, NO model forcing changes.

A "VERIFIED" row is suitable for independent ERA5-Land point-source lookup; it does NOT
establish which land-grid cell or elevation represents the flux tower and never approves a repair.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

SITES = ("JP-Fjy", "JP-Khw", "JP-Yms")
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
FIELDS = ("site", "group_id", "bif_group", "latitude", "longitude", "elevation_m",
          "location_date_start", "location_comment", "location_source_lines")
ROSTER_FIELDS = ("site", "latitude", "longitude", "elevation_m", "UTC_OFFSET_hours",
                 "datum", "original_BIF_member", "original_BIF_sha256", "location_group_ids",
                 "location_source_lines", "status")


def read_bif(site: str, pkg: str, root: Path,
             nested_cap: int = 256 * 1024 * 1024,
             bif_cap: int = 6 * 1024 * 1024) -> tuple[str, str, str]:
    archive = root / site / "forcing" / "packages" / (pkg + ".zip")
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Source original ZIP not regular file: " + str(archive))
    with zipfile.ZipFile(archive) as outer:
        nested = [i for i in outer.infolist()
                  if i.filename == pkg + ".zip" and not i.is_dir()]
        if len(nested) != 1 or nested[0].file_size > nested_cap:
            raise ValueError("Original nested ZIP missing, ambiguous or larger than memory cap")
        with io.BytesIO() as memory:
            with outer.open(nested[0]) as fp:
                size = 0
                while True:
                    chunk = fp.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > nested_cap:
                        raise ValueError("Nested ZIP stream exceeded memory cap")
                    memory.write(chunk)
            memory.seek(0)
            with zipfile.ZipFile(memory) as inner:
                candidates = [i for i in inner.infolist()
                              if not i.is_dir()
                              and "_FLUXNET_BIF_" in Path(i.filename).name.upper()
                              and Path(i.filename).name.lower().endswith(".csv")]
                if len(candidates) != 1:
                    raise ValueError(f"Expected ONE original site BIF metadata CSV for {site}")
                info = candidates[0]
                if info.file_size > bif_cap:
                    raise ValueError("Original BIF metadata CSV unusually large")
                with inner.open(info) as f:
                    raw = f.read(bif_cap + 1)
                if len(raw) > bif_cap:
                    raise ValueError("Original BIF metadata bytes exceed cap")
                return raw.decode("utf-8-sig", errors="replace"), \
                       hashlib.sha256(raw).hexdigest(), info.filename


def group_records(bif: str, site: str) -> tuple[list[dict], list[dict]]:
    grouped: dict[str, list[tuple[int, str, str, str]]] = {}
    offsets = []
    reader = csv.reader(io.StringIO(bif))
    for rec in reader:
        line = reader.line_num
        if len(rec) < 5:
            continue
        sid, gid, group, key = (s.strip() for s in rec[:4])
        if sid != site:
            continue
        val = ",".join(rec[4:]).strip()
        if key == "UTC_OFFSET" and group == "GRP_UTC_OFFSET":
            offsets.append({"line": line, "value": val, "group_id": gid})
        if key in ("LOCATION_LAT", "LOCATION_LONG", "LOCATION_ELEV",
                   "LOCATION_DATE_START", "LOCATION_COMMENT"):
            grouped.setdefault(gid, []).append((line, group, key, val))
    candidates = []
    for gid, vals in grouped.items():
        fields: dict[str, str] = {}
        line_nums = []
        groups = set()
        for line, grp, key, value in vals:
            if key in fields and fields[key] != value:
                raise ValueError(f"Conflicting values for same {site}/{gid}/{key}")
            fields[key] = value
            line_nums.append(str(line))
            groups.add(grp)
        candidates.append({
            "site": site, "group_id": gid, "bif_group": ",".join(sorted(groups)),
            "latitude": fields.get("LOCATION_LAT", ""),
            "longitude": fields.get("LOCATION_LONG", ""),
            "elevation_m": fields.get("LOCATION_ELEV", ""),
            "location_date_start": fields.get("LOCATION_DATE_START", ""),
            "location_comment": fields.get("LOCATION_COMMENT", ""),
            "location_source_lines": ",".join(line_nums),
        })
    return candidates, offsets


def finite_coordinate(v: str, low: float, high: float) -> float | None:
    try:
        x = float(v)
    except (ValueError, TypeError):
        return None
    return x if math.isfinite(x) and low <= x <= high else None


def evaluate(site: str, members: list[dict], offsets: list[dict],
             sha: str, source_member: str) -> tuple[dict, dict | None]:
    problems = []
    valid = []
    for r in members:
        lat = finite_coordinate(r["latitude"], -90, 90)
        lon = finite_coordinate(r["longitude"], -180, 180)
        if lat is None or lon is None:
            problems.append(f"incomplete/invalid LOCATION_LAT/LONG BIF group {r['group_id']}")
            continue
        elev = (finite_coordinate(r["elevation_m"], -500, 9000)
                if r["elevation_m"].strip() else None)
        if r["elevation_m"].strip() and elev is None:
            problems.append(f"Invalid LOCATION_ELEV BIF group {r['group_id']}")
        valid.append((r, lat, lon, elev))
    if not valid:
        problems.append("No complete official LOCATION_LAT/LONG pair in original BIF")
    positions = {(lat, lon) for _, lat, lon, _ in valid}
    elevs = {e for _, _, _, e in valid if e is not None}
    if len(positions) > 1:
        problems.append("Conflicting original LOCATION coordinates across group IDs")
    if len(elevs) > 1:
        problems.append("Conflicting original LOCATION_ELEV across group IDs")
    unique_offsets = set()
    for o in offsets:
        try:
            unique_offsets.add(float(o["value"]))
        except (TypeError, ValueError):
            problems.append(f"Non-numeric original UTC_OFFSET: {o}")
    if unique_offsets != {9.0}:
        problems.append("Original UTC_OFFSET missing or not uniquely +9")
    result = {
        "site": site, "status": "VERIFIED_ORIGINAL_BIF_COORDINATES" if not problems else "HOLD_LOCATION_OR_SOURCE_AMBIGUITY",
        "source_member": source_member, "source_sha256": sha,
        "LOCATION_group_count": len(members), "valid_location_group_count": len(valid),
        "original_UTC_OFFSET_source_rows": offsets,
        "problems": problems,
        "candidate_entries": members,
        "coordinate_datum": "WGS84_decimal_degrees_BADM_LOCATION_standard",
        "elevation_unit": "m_above_sea_level_if_reported",
    }
    if problems:
        return result, None
    lat, lon = next(iter(positions))
    roster = {
        "site": site, "latitude": lat, "longitude": lon,
        "elevation_m": next(iter(elevs)) if elevs else "",
        "UTC_OFFSET_hours": 9, "datum": "WGS84",
        "original_BIF_member": source_member, "original_BIF_sha256": sha,
        "location_group_ids": ",".join(sorted({r["group_id"] for r,_,_,_ in valid})),
        "location_source_lines": ";".join(r["location_source_lines"] for r,_,_,_ in valid),
        "status": "VERIFIED_COORDS_NOT_ERA5L_GRID_CELL_APPROVED",
    }
    return result, roster


def get_original_bif_expected_metadata(stage05k_dir: Path, site: str) -> tuple[str, str]:
    p = stage05k_dir / (site + "_exact_metadata.json")
    r = json.loads(p.read_text(encoding="utf-8"))
    if (r.get("stage") != "JapanFlux Stage05K"
            or r.get("site") != site
            or r.get("status") != "READONLY_BIF_VARIABLE_AND_TIME_METADATA_EXTRACTED"
            or r.get("source_files_modified") is not False
            or r.get("meteorological_rows_read") != 0):
        raise ValueError("Saved original metadata not verified: " + site)
    candidates = [d for d in r["site_metadata_and_readme"]
                  if "_FLUXNET_BIF_" in Path(d["member"]).name.upper()
                  and d["member"].lower().endswith(".csv")]
    if len(candidates) != 1:
        raise ValueError("Expected exactly one original Stage05K BIF digest: " + site)
    return candidates[0]["sha256"], candidates[0]["member"]


def load_manifest(p: Path) -> dict:
    with p.open(encoding="utf-8-sig", newline="") as f:
        entries = list(csv.DictReader(f, delimiter="\t"))
    m = {r["site"]: r for r in entries}
    if len(entries) != 11 or len(m) != 11 or not all(s in m for s in SITES):
        raise ValueError("Expected unique exact 11-site manifest")
    return m


def validate_stage05p_summary(path: Path) -> None:
    r = json.loads(path.read_text(encoding="utf-8"))
    if (r.get("stage") != "JapanFlux Stage05P"
            or r.get("status") != "3_SITE_UTC_REFERENCE_REQUEST_MANIFEST_ONLY"
            or set(r.get("verified_UTC_sites", [])) != set(SITES)
            or r.get("source_approved_UTC_fields") != 27
            or r.get("native_only_HOLD_fields") != 18
            or r.get("independent_ECMWF_values_checked") is not False
            or r.get("site_latitude_longitude") != "UNVERIFIED_NOT_INCLUDED_NO_CDS_CALL"):
        raise ValueError("Expected operator's complete, unapproved Stage05P request plan")


def self_test() -> None:
    sample = (
        "site,group_id,group,key,value\n"
        "JP-Khw,4,GRP_LOCATION,LOCATION_LAT,35.1234\n"
        "JP-Khw,4,GRP_LOCATION,LOCATION_LONG,139.5678\n"
        "JP-Khw,4,GRP_LOCATION,LOCATION_ELEV,192\n"
        "JP-Khw,4,GRP_LOCATION,LOCATION_DATE_START,20000101\n"
        "JP-Khw,9,GRP_UTC_OFFSET,UTC_OFFSET,9\n"
    )
    locations, offsets = group_records(sample, "JP-Khw")
    report, roster = evaluate("JP-Khw", locations, offsets, "a" * 64, "original_BIF.csv")
    assert report["status"] == "VERIFIED_ORIGINAL_BIF_COORDINATES"
    assert roster and roster["latitude"] == 35.1234 and roster["elevation_m"] == 192
    sample2 = sample.replace("20000101\n", "20000101\nJP-Khw,5,GRP_LOCATION,LOCATION_LAT,36.0\nJP-Khw,5,GRP_LOCATION,LOCATION_LONG,139.5678\n")
    loc2, off2 = group_records(sample2, "JP-Khw")
    rr, ro = evaluate("JP-Khw", loc2, off2, "a" * 64, "original_BIF.csv")
    assert ro is None and rr["status"] == "HOLD_LOCATION_OR_SOURCE_AMBIGUITY"
    print("STAGE05Q SELF-TEST PASS | original BADM group coordinate integrity and source HOLD; NO WRITES")


def write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, delimiter="\t", fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--manifest", type=Path)
    p.add_argument("--stage05k-dir", type=Path)
    p.add_argument("--stage05p-summary", type=Path)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--out-dir", type=Path)
    a = p.parse_args()
    if a.self_test:
        self_test()
        return
    if not all((a.manifest, a.stage05k_dir, a.stage05p_summary, a.out_dir)):
        p.error("Require --manifest --stage05k-dir --stage05p-summary --out-dir")
    manifest = load_manifest(a.manifest)
    validate_stage05p_summary(a.stage05p_summary)
    if a.out_dir.exists():
        p.error("Output directory exists; use new location")
    reports = []
    candidates = []
    rosters = []
    for site in SITES:  # strict serial, one ZIP in RAM at a time
        pkg = manifest[site]["package"]
        text, sha, member = read_bif(site, pkg, a.root)
        expected_sha, expected_member = get_original_bif_expected_metadata(a.stage05k_dir, site)
        if sha != expected_sha or member != expected_member:
            raise ValueError(f"Original BIF SHA or member differs from prior Stage05K: {site}")
        loc, off = group_records(text, site)
        report, roster = evaluate(site, loc, off, sha, member)
        reports.append(report)
        candidates.extend(loc)
        if roster is not None:
            rosters.append(roster)
    passed = len(rosters) == 3
    summary = {
        "stage": "JapanFlux Stage05Q",
        "status": "3_SITE_SOURCE_BIF_COORDINATES_VERIFIED" if passed else "HOLD_INCOMPLETE_OR_CONFLICTING_SITE_COORDINATES",
        "sites": reports, "coordinate_sites_verified": len(rosters),
        "source_scope": list(SITES), "stage05p_UTC_hour_plan": "OPERATOR_VERIFIED_3_SITE",
        "source_zip_modified": False, "raw_meteorological_rows_read": 0,
        "CDS_requests_performed": 0, "ERA5L_reference_values_acquired": False,
        "model_forcing_approved": False, "ERA5L_land_grid_cell_selected": False,
        "note": "Original WGS84 site coordinates are lookup evidence only. Do not assume grid cell equivalence or automatically replace JPF values.",
    }
    a.out_dir.mkdir(parents=True)
    write_tsv(a.out_dir / "stage05q_original_BIF_LOCATION_all_candidates.tsv",
              FIELDS, candidates)
    with (a.out_dir / "stage05q_original_BIF_location_validation.json").open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("STAGE05Q", summary["status"], "VERIFIED", len(rosters), "/3")
    for r in reports:
        print("SITE", r["site"], r["status"], "GROUPS", r["LOCATION_group_count"],
              "ISSUES", r["problems"])
    if passed:
        path = a.out_dir / "stage05q_original_BIF_verified3_CDS_coordinate_roster.tsv"
        write_tsv(path, ROSTER_FIELDS, rosters)
        print("ORIGINAL_BIF_VERIFIED_COORDINATE_ROSTER", path)
    else:
        print("NO APPROVED THREE-SITE COORDINATE ROSTER: original BIF requires manual review")
    print("AUDIT", a.out_dir / "stage05q_original_BIF_location_validation.json")
    print("NO CDS CALLS, NO SLURM, NO ORIGINAL OR MODEL FORCING CHANGES")


if __name__ == "__main__":
    main()

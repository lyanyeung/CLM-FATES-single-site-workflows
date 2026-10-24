#!/usr/bin/env python3
"""Stage13c: read-only US-EML ERA5 dewpoint pilot versus original tower TA
and Stage11 unapproved RH analogues.

ERA5 timestamps are UTC, AmeriFlux/FLUXNET timestamps local standard time.
Alaska UTC-9 is a PROVISIONAL mapping pending site-specific BADM verification.
The pilot tests alternative UTC-8/-9/-10 hour offsets; it does not select one.
Only exact hourly timestamps are compared; no HH interpolation or forcing.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import xarray as xr

HOME = Path.home()
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE08 = ROOT / "raw_RH_sensitivity_20261022T013805Z_aadaffee"
STAGE11 = ROOT / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
PILOT = HOME / "AmeriFlux_Batch02_ERA5_dewpoint_pilot" / "US-EML_ERA5_20090101_20090108_extracted"
OFFSETS = (-10, -9, -8)  # local standard time - UTC; NOT verified for this release.

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1048576), b""):
            h.update(part)
    return h.hexdigest()

def es_water(c):
    return 6.112 * np.exp(17.67 * c / (c + 243.5))  # hPa

def timeparse(s):
    return pd.to_datetime(s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True),
                          format="%Y%m%d%H%M", errors="raise")

def pilot_read(path):
    first = path.open("rb").read(8)
    if first != b"\x89HDF\r\n\x1a\n":
        raise ValueError("Expected extracted NetCDF4/HDF5, not CDS ZIP or other data")
    with xr.open_dataset(path, engine="netcdf4") as ds:
        needed = {"t2m", "d2m", "sp"}
        if set(ds.data_vars) != needed or "valid_time" not in ds.coords:
            raise ValueError("Unexpected ERA5 variable/time schema")
        if any(ds[v].attrs.get("units") != unit
               for v, unit in (("t2m", "K"), ("d2m", "K"), ("sp", "Pa"))):
            raise ValueError("Unexpected ERA5 variable units")
        if any(tuple(ds[v].dims) != ("valid_time",) for v in needed):
            raise ValueError("Not a single-point hourly ERA5 series")
        era = pd.DataFrame({
            "utc": pd.to_datetime(ds["valid_time"].values, utc=True).tz_localize(None),
            "ERA_T_C": ds.t2m.to_numpy().astype(float) - 273.15,
            "ERA_Td_C": ds.d2m.to_numpy().astype(float) - 273.15,
            "ERA_P_Pa": ds.sp.to_numpy().astype(float)})
        lat = float(np.asarray(ds.latitude.values).ravel()[0])
        lon = float(np.asarray(ds.longitude.values).ravel()[0])
    if len(era) != 192 or era.utc.duplicated().any():
        raise ValueError("Unexpected 8-day/192-hour pilot timeline")
    expected = pd.date_range("2009-01-01", "2009-01-09", freq="h", inclusive="left")
    if not np.array_equal(era.utc.to_numpy(), expected.to_numpy()):
        raise ValueError("Pilot not 2009-01-01 through 2009-01-08 hourly UTC")
    if not ((era.ERA_T_C.between(-90, 60) &
             era.ERA_Td_C.between(-100, 60) &
             era.ERA_P_Pa.between(50000, 110000)).all()):
        raise ValueError("ERA5 physical/unit screening failed")
    era["ERA_ea_hPa"] = es_water(era.ERA_Td_C)
    era["ERA_RH_water_pct"] = 100 * era.ERA_ea_hPa / es_water(era.ERA_T_C)
    era["ERA_VPD_water_hPa"] = es_water(era.ERA_T_C) - era.ERA_ea_hPa
    era["ERA_QBOT_kgkg"] = (
        .622 * era.ERA_ea_hPa * 100 /
        (era.ERA_P_Pa - .378 * era.ERA_ea_hPa * 100))
    era["dewpoint_exceeds_temperature_C"] = era.ERA_Td_C - era.ERA_T_C
    return era, lat, lon

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot-file", type=Path)
    p.add_argument("--stage08-root", type=Path, default=STAGE08)
    p.add_argument("--stage11-root", type=Path, default=STAGE11)
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--output-root", type=Path)
    args = p.parse_args()
    files = sorted(PILOT.glob("*.nc")) if args.pilot_file is None else [args.pilot_file]
    if len(files) != 1:
        raise ValueError(f"Expected one extracted NetCDF; got {len(files)}. Specify --pilot-file")
    pilot_file = files[0].expanduser().resolve()
    s8 = args.stage08_root.expanduser().resolve()
    s11 = args.stage11_root.expanduser().resolve()
    if not (s8 / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file():
        raise ValueError("Stage08 marker missing")
    if not (s11 / "DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage11 marker missing")
    source8 = json.loads((s8 / "exact_input_manifest.json").read_text())
    source11 = json.loads((s11 / "manifest.json").read_text())
    if source11["source_stage08"] != str(s8) or source11["n_target_rows"] != 4884:
        raise ValueError("Stage08/11 provenance mismatch")
    row = next(r for r in source8["sites"] if r["site"] == "US-EML")
    primary = Path(row["primary"]).resolve()
    if sha(primary) != source11["input_hashes"].get(str(primary)):
        raise ValueError("Pinned US-EML source hash differs")
    proposals_file = s11 / "cold_humidity_repair_proposals.csv"
    proposals = pd.read_csv(proposals_file)
    eml = proposals.loc[proposals.site.eq("US-EML")].copy()
    if len(eml) != 1327:
        raise ValueError("Unexpected Stage11 US-EML repair scope")
    eml["local_standard"] = pd.to_datetime(eml.time)
    era, lat, lon = pilot_read(pilot_file)
    head = set(pd.read_csv(primary, nrows=0).columns)
    col = ["TIMESTAMP_START", "TA_F"] + (["TA_F_QC"] if "TA_F_QC" in head else [])
    tower = pd.read_csv(primary, usecols=col, dtype={"TIMESTAMP_START": str})
    tower["local_standard"] = timeparse(tower.TIMESTAMP_START)
    tower["tower_T_C"] = pd.to_numeric(tower.TA_F, errors="coerce")
    tower.loc[tower.tower_T_C <= -9990, "tower_T_C"] = np.nan
    if "TA_F_QC" in tower:
        tower["TA_QC"] = pd.to_numeric(tower.TA_F_QC, errors="coerce")
    else:
        tower["TA_QC"] = np.nan
    tower = tower.loc[tower.local_standard.dt.minute.eq(0)].copy()
    tower = tower.loc[tower.local_standard.between(
        pd.Timestamp("2008-12-30"), pd.Timestamp("2009-01-10"))]
    if tower.local_standard.duplicated().any():
        raise ValueError("Original tower timestamps are duplicated")
    cases = []
    aligned = None
    for offset in OFFSETS:
        t = tower.copy()
        t["utc"] = t.local_standard - pd.Timedelta(hours=offset)
        combined = era.merge(t[["utc", "local_standard", "tower_T_C", "TA_QC"]],
                             on="utc", how="left", validate="one_to_one")
        measured = combined.TA_QC.eq(0) & combined.tower_T_C.notna()
        available = combined.tower_T_C.notna()
        rmse = lambda x: float(np.sqrt(np.mean(np.asarray(x)**2))) if len(x) else None
        differences = combined.ERA_T_C - combined.tower_T_C
        cases.append(dict(tower_UTC_offset_hours=offset,
            expected_hourly=192,
            matched_tower_T=int(available.sum()),
            measured_T_QC0=int(measured.sum()),
            rmse_T_QC0_C=rmse(differences.loc[measured]),
            mae_T_QC0_C=float(differences.loc[measured].abs().mean()) if measured.any() else None,
            rmse_T_all_available_C=rmse(differences.loc[available]),
            caveat="Diagnostic only; tower temperature bias and interval averaging confound offset inference"))
        if offset == -9:
            aligned = combined.copy()
    if aligned is None or aligned.local_standard.notna().sum() < 100:
        raise ValueError("Insufficient hourly join for provisional Alaska local standard offset")
    assert len(era) == len(aligned) == 192
    # Match the 1,327 Stage11 targets to pilot ERA, without half-hour interpolation.
    t = eml.loc[eml.local_standard.dt.minute.eq(0)].copy()
    t["utc"] = t.local_standard + pd.Timedelta(hours=9)
    matched = t.merge(era, on="utc", how="inner", validate="many_to_one")
    if not matched.empty:
        matched["site_es_water_hPa"] = es_water(matched.retained_TA_C)
        matched["ERA_RH_applied_to_site_T_VPD_hPa"] = (
            matched.site_es_water_hPa * (1 - matched.ERA_RH_water_pct / 100))
        matched["site_RH_from_ERA_dewpoint_pct"] = (
            100 * matched.ERA_ea_hPa / matched.site_es_water_hPa)
        matched["dewpoint_site_supersaturation"] = (
            matched.site_RH_from_ERA_dewpoint_pct > 100.05)
        matched["proposal_minus_ERA_RH_at_site_T_hPa"] = (
            matched.proposed_VPD_hPa -
            matched.ERA_RH_applied_to_site_T_VPD_hPa)
        matched["review_ERA_RH_water_outside_bounds"] = (
            ~matched.ERA_RH_water_pct.between(0, 100.05))
    print("========== ERA5 PILOT DATA ==========")
    print("FILE:", pilot_file)
    print("NETCDF SHA256:", sha(pilot_file))
    print("GRID POINT:", lat, lon, "| requested station: 63.8784 -149.2536")
    print("UTC HOURS:", len(era))
    print("ERA t2m C:", f"{era.ERA_T_C.min():.3f}", "to", f"{era.ERA_T_C.max():.3f}")
    print("ERA d2m C:", f"{era.ERA_Td_C.min():.3f}", "to", f"{era.ERA_Td_C.max():.3f}")
    print("ERA RH water %:", f"{era.ERA_RH_water_pct.min():.3f}",
          "to", f"{era.ERA_RH_water_pct.max():.3f}")
    print("ERA negative RH:", int(era.ERA_RH_water_pct.lt(0).sum()),
          "| dewpoint exceeds temp >0.05C:",
          int(era.dewpoint_exceeds_temperature_C.gt(.05).sum()))
    print("\n========== TIME OFFSET SENSITIVITY (NOT AUTOMATIC SELECTION) ==========")
    print(pd.DataFrame(cases).to_string(index=False))
    print("\n========== STAGE11 BLOCKER OVERLAP, HOURLY ONLY ==========")
    print("Overlapping records:", len(matched),
          "| stage11 unresolved subset:",
          int(matched.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()))
    if len(matched):
        print("ERA-RH outside 0-100.05:",
              int(matched.review_ERA_RH_water_outside_bounds.sum()))
        print("Direct ERA-dewpoint would supersaturate at tower TA:",
              int(matched.dewpoint_site_supersaturation.sum()))
        display = ["time", "retained_TA_C", "ERA_T_C", "ERA_Td_C",
                   "ERA_RH_water_pct", "proposed_VPD_hPa",
                   "ERA_RH_applied_to_site_T_VPD_hPa",
                   "donor_count", "decision"]
        print(matched[display].head(12).to_string(index=False))
        focus = matched.loc[matched.local_standard.eq(
            pd.Timestamp("2009-01-03 11:00:00"))]
        if len(focus):
            print("\nFOCUS US-EML 2009-01-03 11:00 LOCAL STANDARD")
            print(focus[display].to_string(index=False))
    print("\nNOT SCIENTIFICALLY APPROVED: -9 offset assumed, "
          "ERA is grid-level reanalysis, and ERA humidity applied at "
          "tower temperature is a sensitivity only.")
    if not args.write_report:
        print("CHECK ONLY: no files written or modified")
        return 0
    out = args.output_root.expanduser().resolve() if args.output_root else (
        HOME / ("AmeriFlux_Batch02_stage13c_pilot_" +
                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                "_" + uuid4().hex[:8]))
    if out.exists() or any(out == x or out in x.parents or x in out.parents
                           for x in (pilot_file.parent, s8, s11)):
        raise ValueError("Unsafe/existing output")
    out.mkdir(parents=True, exist_ok=False)
    era.to_csv(out / "ERA5_dewpoint_pilot_hourly_UTC.csv", index=False)
    pd.DataFrame(cases).to_csv(out / "candidate_tower_UTC_offsets.csv", index=False)
    matched.to_csv(out / "Stage11_hourly_blockers_pilot_comparison.csv", index=False)
    receipt = dict(pilot_NC_SHA256=sha(pilot_file), raw_tower_SHA256=sha(primary),
                   stage11_proposals_SHA256=sha(proposals_file),
                   software_SHA256=sha(Path(__file__)),
                   provisional_UTC_offset=-9,
                   local_standard_convention="Provisional pending site BADM UTC offset confirmation",
                   scientific_status="PILOT_COMPARISON_ONLY_NOT_FOR_DATM",
                   matched_stage11_rows=len(matched),
                   outputs="Diagnostic CSV only; NO forcing or model changes")
    (out / "manifest.json").write_text(json.dumps(receipt, indent=2)+"\n")
    (out / "DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Pilot diagnostic only. Validate site UTC offset and humidity provenance.\n")
    print("STAGE13C REPORT:", out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

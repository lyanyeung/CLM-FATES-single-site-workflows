#!/usr/bin/env python3
"""US-NR3 first-pass source reconciliation. Read-only; stdout only.

Modes: --self-test; --raw-zip PATH (local original-package audit); --check;
--science (inventory plus grid, QC0 validation and installed-source review).
(IRIDIS6 SHA-linked Stage07/10/12G inventory). Optional --emit-missing and
--emit-anomalies print CSV to stdout. No --run/output/download/model mode.

This inventory does NOT validate a repair method or approve a clock, new
shadow, report-file write, DATM, AD400, or Slurm. Historical receipt hashes
establish content/lineage consistency, not an independent digital signature.
"""
import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

VERSION = "nr3-01-v2-20261029"
SITE = "US-NR3"
RELEASE = "AMF_US-NR3_FLUXNET_2007-2024_v1.3_r1"
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07 = "qcv5_native_trial_20261022T024559Z_36c46e58"
G = "science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
E = "science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
B = "science_trials/stage12b_six_site_bulk_gridRH_numeric_patches_20261024T115336Z_baa77893"
D = "reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa"
H = "reports/stage10h_original_source_provenance_20261024T054425Z_faf342a8"
I = "reports/stage10i_era_vpd_physics_20261024T055509Z_b5a44de8"
RAW_SHA = {
    "primary": "dbc365368a492285ea73193b1ff1dbb0336673f9448c18d734e82fb7717087a2",
    "era": "3f123994e9b4dad4d487a553ff0419b0e6919a26a75349fba7839cc5720d771b",
    "bif": "e02c9b6b97ba89ac9e1a70faeb73eeec06d96455d3b6d3dc7c537b774f578d44",
    "varinfo": "eb93ddc895e7a9e20d46d3330f10c27f94eb05eeb44c43c9c4d0bb5224bc57ee",
}
PRIMARY_NAME = "AMF_US-NR3_FLUXNET_FLUXMET_HH_2007-2024_v1.3_r1.csv"
ERA_NAME = "AMF_US-NR3_FLUXNET_ERA5_HH_1981-2025_v1.3_r1.csv"
RAW_COLS = ["TIMESTAMP_START", "TIMESTAMP_END", "TA_F", "TA_F_QC",
            "VPD_F", "VPD_F_QC", "RH", "TA_F_MDS", "TA_F_MDS_QC",
            "VPD_F_MDS", "VPD_F_MDS_QC", "PA_F", "PA_F_QC"]
ERA_COLS = ["TIMESTAMP_START", "TA_ERA", "VPD_ERA", "PA_ERA"]
READS = {}
COMPACT = False
COMPACT_OMIT = {"NR3_RELEASE_METADATA", "NR3_VARIABLE_METADATA", "NR3_RAW_YEAR_INVENTORY",
                "NR3_ANOMALY_YEAR", "NR3_ANOMALY_PRIORITIES", "NR3_MISSING_EPISODES",
                "NR3_EXTERNAL_RECEIPTS", "NR3_READ_SHA256", "NR3_SCIENCE_LIMIT"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def deny_writes(event, args):
    if event == "open":
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        mask = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & mask):
            raise RuntimeError("READONLY guard rejected file write")
    if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link",
                 "os.symlink", "os.system", "os.truncate", "os.chmod", "os.utime"} or event.startswith("subprocess."):
        raise RuntimeError("READONLY guard rejected mutation/subprocess: " + event)


def regular(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "Missing/unsafe file: " + str(path))
    return path


def digest(path):
    h = hashlib.sha256()
    with regular(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pin(path, expected=None):
    path = regular(path)
    actual = digest(path)
    require(expected is None or actual == expected, "SHA256 mismatch: " + str(path))
    READS[str(path)] = actual
    return path


def doc(path, expected=None):
    return json.loads(pin(path, expected).read_text(encoding="utf-8"))


def linked_csv(folder, receipt, name):
    require(name in receipt["output_sha256"], "CSV absent from receipt: " + name)
    return pd.read_csv(pin(folder / name, receipt["output_sha256"][name]),
                       dtype={"native_key": str, "TIMESTAMP_START": str}, low_memory=False)


def emit(label, value):
    if COMPACT and label in COMPACT_OMIT:
        return
    print(label, json.dumps(value, ensure_ascii=True, allow_nan=False, default=str), flush=True)


def emit_csv(label, frame):
    print("BEGIN_" + label, flush=True)
    print(frame.to_csv(index=False, float_format="%.9g"), end="", flush=True)
    print("END_" + label, flush=True)


def native_times(frame, column):
    """Read documented naive native times without shifts or inferred zones.

    Historical CSVs serialize the same native clock using either ISO T or
    a space. Normalize that separator only, before strict format parsing.
    Never remove a timezone, round seconds, or accept an off-grid minute.
    """
    value = frame[column].astype(str)
    if column in {"native_key", "TIMESTAMP_START"}:
        require(value.str.fullmatch(r"[0-9]{12}").all(), "Malformed native key: " + column)
        fmt = "%Y%m%d%H%M"
    else:
        require(value.str.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}").all(),
                "Native time must be naive YYYY-MM-DD[T or space]HH:MM:SS: " + column)
        value = value.str.replace("T", " ", regex=False)
        fmt = "%Y-%m-%d %H:%M:%S"
    dt = pd.to_datetime(value, format=fmt, errors="raise")
    require((dt.dt.second.eq(0) & dt.dt.minute.mod(30).eq(0)).all(),
            "Native time is off the exact 30-minute grid: " + column)
    return dt


def keys(frame, column):
    dt = native_times(frame, column)
    result = dt.dt.strftime("%Y%m%d%H%M")
    require(not result.duplicated().any(), "Duplicate native timestamps: " + column)
    return result


def esw(t):
    t = np.asarray(t, dtype=float)
    return 6.112 * np.exp(17.67 * t / (t + 243.5))


def esi(t):
    t = np.asarray(t, dtype=float)
    return 6.112 * np.exp(22.46 * t / (t + 272.62))


def attach_raw(primary, era):
    primary = primary.copy()
    primary["native_key"] = keys(primary, "TIMESTAMP_START")
    primary["source_csv_row"] = np.arange(len(primary)) + 2
    start = pd.to_datetime(primary.TIMESTAMP_START, format="%Y%m%d%H%M")
    end = pd.to_datetime(primary.TIMESTAMP_END, format="%Y%m%d%H%M")
    require((end - start).eq(pd.Timedelta(minutes=30)).all(), "Non-30-minute source intervals")
    require(start.diff().iloc[1:].eq(pd.Timedelta(minutes=30)).all(), "Primary native clock is incomplete/nonmonotonic")
    era = era.copy()
    era["native_key"] = keys(era, "TIMESTAMP_START")
    et = pd.to_datetime(era.TIMESTAMP_START, format="%Y%m%d%H%M")
    require(et.diff().iloc[1:].eq(pd.Timedelta(minutes=30)).all(), "Companion native clock is incomplete/nonmonotonic")
    merged = primary.merge(era.drop(columns="TIMESTAMP_START"), on="native_key",
                           how="left", validate="one_to_one", indicator=True)
    require(merged._merge.eq("both").all(), "Primary keys missing from companion ERA; no shifts allowed")
    merged = merged.drop(columns="_merge")
    merged["year"] = start.dt.year.to_numpy()
    merged["month"] = start.dt.month.to_numpy()
    merged["es_water_hPa"] = esw(merged.TA_ERA)
    merged["es_ice_hPa"] = esi(merged.TA_ERA)
    merged["ERA_e_water_hPa"] = merged.es_water_hPa - merged.VPD_ERA
    merged["ERA_RH_water_pct"] = 100 * merged.ERA_e_water_hPa / merged.es_water_hPa
    return merged


def raw_summary(raw):
    result = []
    for year, g in raw.groupby("year", sort=True):
        dual = g.TA_F_QC.eq(0) & g.VPD_F_QC.eq(0)
        ev = esw(g.TA_F) - g.VPD_F
        physical = g.TA_F.between(-80, 65) & g.VPD_F.ge(0) & ev.gt(0)
        result.append(dict(year=int(year), native_rows=len(g),
            TA_QC={str(k): int(v) for k, v in g.TA_F_QC.value_counts(dropna=False).items()},
            VPD_QC={str(k): int(v) for k, v in g.VPD_F_QC.value_counts(dropna=False).items()},
            dual_QC0=int(dual.sum()), physical_dual_QC0=int((dual & physical).sum()),
            RH_numeric=int(g.RH.notna().sum()),
            RH_numeric_dual_QC2=int((g.RH.notna() & g.TA_F_QC.eq(2) & g.VPD_F_QC.eq(2)).sum()),
            all_source_ERA_pair_negative_e=int(g.ERA_e_water_hPa.lt(0).sum())))
    return result


def metadata(bif, varinfo):
    b = bif.loc[bif.VARIABLE.str.contains("PRODUCT_|UTC_OFFSET|LOCATION_|IGBP|ERA_", regex=True)]
    emit("NR3_RELEASE_METADATA", b.to_dict("records"))
    ids = varinfo.loc[varinfo.VARIABLE.eq("VAR_INFO_VARNAME") &
        varinfo.DATAVALUE.isin(["TA_F", "VPD_F", "RH"]), "GROUP_ID"]
    emit("NR3_VARIABLE_METADATA", varinfo.loc[varinfo.GROUP_ID.isin(ids)].to_dict("records"))
    emit("NR3_METADATA_CAUTION", "Nominal native LST UTC-7 is source documented; model admission/UTC interpolation still unapproved. Metadata height does not prove unchanged sensor operation every year.")


def raw_zip(path):
    pin(path)
    with zipfile.ZipFile(path) as z:
        names = {"primary": PRIMARY_NAME, "era": ERA_NAME,
                 "bif": RELEASE.replace("FLUXNET_", "FLUXNET_BIF_", 1) + ".csv",
                 "varinfo": RELEASE.replace("FLUXNET_", "FLUXNET_BIFVARINFO_HH_", 1) + ".csv"}
        for role, name in names.items():
            h = hashlib.sha256()
            with z.open(name) as stream:
                for block in iter(lambda: stream.read(1 << 20), b""):
                    h.update(block)
            require(h.hexdigest() == RAW_SHA[role], "Unexpected exact-release ZIP member SHA: " + name)
            emit("NR3_RAW_MEMBER_SHA", dict(role=role, member=name, sha256=h.hexdigest()))
        primary = pd.read_csv(z.open(names["primary"]), usecols=RAW_COLS,
            na_values=-9999, dtype={"TIMESTAMP_START": str, "TIMESTAMP_END": str})
        era = pd.read_csv(z.open(names["era"]), usecols=ERA_COLS,
            na_values=-9999, dtype={"TIMESTAMP_START": str})
        metadata(pd.read_csv(z.open(names["bif"]), keep_default_na=False),
                 pd.read_csv(z.open(names["varinfo"]), keep_default_na=False))
    emit("NR3_RAW_YEAR_INVENTORY", raw_summary(attach_raw(primary, era)))
    emit("NR3_SCOPE", "RAW_ONLY; no Stage12G ledger/event-identity assertion without IRIDIS receipts")


def event_keys(frame):
    subset = frame.loc[frame.site.eq(SITE)].copy()
    subset["native_key"] = keys(subset, "native_key" if "native_key" in subset else "time")
    return subset


def reconcile_missing(selected, raw, protected, other, newyear, anomalies):
    selected = selected.copy()
    selected["native_key"] = keys(selected, "time")
    missing_fields = selected.drop(columns=["time", "native_key"]).isna()
    missing = selected.loc[missing_fields.any(axis=1)].copy()
    missing["missing_fields"] = missing_fields.loc[missing.index].apply(
        lambda r: "|".join(r.index[r].tolist()), axis=1)
    protect = set(protected.native_key)
    require(protect <= set(missing.native_key), "Protected physics HOLD became finite")
    require(not (set(other.native_key) & protect), "Protected/other HOLD populations overlap")
    reasons = other.set_index("native_key").science_hold_reason.to_dict()
    newreasons = newyear.set_index("native_key").reason.to_dict()
    ledger = missing[["native_key", "missing_fields", "TA_USE", "PSRF"]].merge(
        raw, on="native_key", how="left", validate="one_to_one", indicator=True)
    require(ledger._merge.eq("both").all(), "Selected missing row lacks exact original source")
    ledger = ledger.drop(columns="_merge")
    protected_reason = protected.set_index("native_key").reason.to_dict()
    ledger["HOLD_class"] = np.where(ledger.native_key.isin(protect),
        "PHYSICS_CONFLICT_HOLD", "EVIDENCE_INSUFFICIENT_HOLD")
    ledger["Stage12B_reason"] = ledger.native_key.map(protected_reason).fillna("")
    ledger["Stage12E_reason"] = ledger.native_key.map(reasons).fillna("")
    ledger["Stage12G_reason"] = ledger.native_key.map(newreasons).fillna("")
    ledger["in_1484_source_anomalies"] = ledger.native_key.isin(set(anomalies.native_key))
    ledger["APPROVED_FOR_NEW_VERSION"] = False
    dt = pd.to_datetime(ledger.native_key, format="%Y%m%d%H%M")
    ledger = ledger.assign(_dt=dt).sort_values("_dt").reset_index(drop=True)
    ledger["episode"] = ledger._dt.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    ledger = ledger.drop(columns="_dt")
    require(set(ledger.native_key) == protect | set(other.native_key), "238 rows differ from protected+other population")
    require(set(newyear.native_key) <= set(other.native_key), "Source-year ledger lies outside other gaps")
    require(len(ledger) == 238 and len(protect) == 172 and len(other) == 66,
            "Historical 238=172+66 changed; inspect current signed version before proceeding")
    require(len(newyear) == 6, "Narrow Stage12G source-year population changed")
    return ledger


def grid_receipts(root):
    base = root / "external_evidence/era5land_timeseries" / SITE
    rows = []
    if not base.is_dir():
        return [{"status": "NO_NR3_EXTERNAL_DIRECTORY", "path": str(base)}]
    for folder in sorted(base.iterdir()):
        if not folder.is_dir() or not folder.name.isdigit():
            continue
        for path in sorted(folder.glob("*.receipt.json")):
            obj = doc(path)
            require(obj.get("site") == SITE and int(obj.get("year", -1)) == int(folder.name),
                    "External receipt site/year mismatch: " + str(path))
            response = Path(obj["response_file"])
            require(response.resolve().parent == folder.resolve(), "External response is outside exact NR3/year directory")
            pin(response, obj["response_sha256"])
            rows.append(dict(year=int(folder.name), receipt=str(path), file=str(response),
                sha256=obj["response_sha256"], dataset=obj.get("dataset"),
                source_status=obj.get("status"), request=obj.get("request"),
                current_check="RECEIPT_AND_FILE_SHA_ONLY; CF/grid/orography test pending"))
    return rows


def audit(root, args):
    s07, g, e, b, d, h, i = [root / x for x in (S07, G, E, B, D, H, I)]
    for folder in (s07, g, e, b):
        regular(folder / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    manifest = doc(s07 / "exact_input_manifest.json")
    # The original output receipt pins the input manifest as an output.
    seal = doc(s07 / "output_sha256.json")
    require(seal["exact_input_manifest.json"] == digest(s07 / "exact_input_manifest.json"), "Stage07 manifest/output receipt mismatch")
    specs = [x for x in manifest["sites"] if x["site"] == SITE]
    require(len(specs) == 1 and specs[0]["release"] == RELEASE, "Exact NR3 release differs")
    spec = specs[0]
    emit("NR3_SOURCE_SPEC", spec)
    frames = {}
    for role, cols in (("primary", RAW_COLS), ("era", ERA_COLS)):
        path = Path(spec[role])
        expected = manifest["input_sha256"].get(str(path))
        require(expected == RAW_SHA[role], "Stage07 source SHA differs from audited local release: " + role)
        frames[role] = pd.read_csv(pin(path, expected), usecols=cols,
            dtype={"TIMESTAMP_START": str, "TIMESTAMP_END": str}, na_values=-9999)
    raw = attach_raw(frames["primary"], frames["era"])
    emit("NR3_RAW_YEAR_INVENTORY", raw_summary(raw))
    for role, token in (("bif", "_BIF_"), ("varinfo", "_BIFVARINFO_HH_")):
        found = list(Path(spec["primary"]).parent.glob("*" + token + "*.csv"))
        if len(found) != 1:
            emit("NR3_METADATA_MISSING", dict(role=role, paths=[str(x) for x in found]))
            continue
        frames[role] = pd.read_csv(pin(found[0], RAW_SHA[role]), keep_default_na=False)
    if "bif" in frames and "varinfo" in frames:
        metadata(frames["bif"], frames["varinfo"])
    gr = doc(g / "stage12g_research_only_sha_receipt.json")
    er = doc(e / "stage12e_research_only_sha_receipt.json", gr["pinned_Stage12e_SHA256"])
    br = doc(b / "stage12b_numeric_candidate_receipt.json")
    dr = doc(d / "read_only_provenance.json")
    hr = doc(h / "read_only_provenance.json")
    ir = doc(i / "science_provenance.json")
    require(hr["stage07_input_manifest_sha256"] == digest(s07 / "exact_input_manifest.json"), "Stage10H/07 lineage mismatch")
    require(hr["stage10d_provenance_sha256"] == digest(d / "read_only_provenance.json"), "Stage10H/10D lineage mismatch")
    require(ir["stage10h_v2_receipt_sha256"] == digest(h / "read_only_provenance.json"), "Stage10I/10H lineage mismatch")
    require(gr.get("Postv5_approved") == 0 and gr.get("DATM_ready") == 0
            and gr.get("spinup_authorized") == 0, "Stage12G admission status differs")
    selected = linked_csv(g, gr, SITE + "_STAGE12G_INCOMPLETE_NOLEAP.csv")
    expected = pd.date_range("2007-01-01", "2025-01-01", freq="30min", inclusive="left")
    expected = expected[~((expected.month == 2) & (expected.day == 29))]
    require(pd.DatetimeIndex(native_times(selected, "time")).equals(expected), "Stage12G NOLEAP chronology differs")
    require(len(selected) == 315360, "Unexpected Stage12G length")
    anomalies = event_keys(linked_csv(d, dr, "all_1924_manual_review.csv"))
    original_qc = event_keys(linked_csv(h, hr, "original_qc_source_classes_at_1924_blockers.csv"))
    original_thermo = event_keys(linked_csv(i, ir, "all_1924_source_ERA_water_saturation_inconsistencies.csv"))
    require(len(anomalies) == 1484 and set(anomalies.native_key) == set(original_qc.native_key)
            == set(original_thermo.native_key), "Stage10D/H/I anomaly key sets differ")
    verified = anomalies[["native_key", "source_csv_row", "review_priority"]].merge(
        raw, on="native_key", how="left", validate="one_to_one", suffixes=("_ledger", ""), indicator=True)
    require(verified._merge.eq("both").all(), "Anomaly missing from exact source time")
    verified = verified.drop(columns="_merge")
    require(np.array_equal(pd.to_numeric(verified.source_csv_row_ledger), verified.source_csv_row), "Original CSV row numbers differ")
    for role, old, columns in (("H", original_qc, {"TA_F": "TA_F", "VPD_F": "VPD_F", "TA_ERA": "TA_ERA", "VPD_ERA": "VPD_ERA", "TA_F_QC_raw": "TA_F_QC", "VPD_F_QC_raw": "VPD_F_QC"}),):
        aligned = old.set_index("native_key").loc[verified.native_key]
        for source_col, raw_col in columns.items():
            require(np.allclose(pd.to_numeric(aligned[source_col]), verified[raw_col], rtol=0, atol=1e-7), "Stage10" + role + "/raw mismatch: " + source_col)
    require(verified.VPD_F_QC.eq(2).all() and (verified.VPD_F - verified.VPD_ERA).abs().le(.01).all(), "Original anomalies are no longer exact-time QC2/ERA matches")
    require(verified.ERA_e_water_hPa.lt(0).all(), "Anomaly source water-e sign changed")
    for stamp, row in (("201802210930", 195333), ("201802211000", 195334)):
        one = verified.loc[verified.native_key.eq(stamp)]
        require(len(one) == 1 and int(one.source_csv_row.iloc[0]) == row, "Stage10K exception identity differs")
    protected = event_keys(linked_csv(b, br, "seven_site_science_holds_including_US-Me2.csv"))
    other = event_keys(linked_csv(e, er, "remaining_4372_source_second_ERA5Land_holds.csv"))
    newyear = event_keys(linked_csv(g, gr, "2810_original_missing_year_source_review_after_stage12g.csv"))
    missing = reconcile_missing(selected, raw, protected, other, newyear, verified)
    status = linked_csv(g, gr, "six_site_stage12g_science_status.csv")
    emit("NR3_STAGE12G_STATUS", status.loc[status.site.eq(SITE)].to_dict("records"))
    emit("NR3_RECONCILED_COUNTS", dict(selected_rows=len(selected), missing=len(missing),
         protected_physics=len(protected), other_gaps=len(other), narrow_source_year=len(newyear),
         original_anomalies=len(verified), overlap=int(missing.in_1484_source_anomalies.sum()),
         approvals=0, source_sha=RAW_SHA))
    emit("NR3_ANOMALY_YEAR", verified.groupby("year").agg(n=("native_key", "size"),
        negative_e_median_hPa=("ERA_e_water_hPa", "median"), RH_water_median_pct=("ERA_RH_water_pct", "median")).reset_index().to_dict("records"))
    emit("NR3_ANOMALY_PRIORITIES", {str(k): int(v) for k, v in verified.review_priority.value_counts().items()})
    emit("NR3_HOLD_REASON_COUNTS", missing.groupby(["HOLD_class", "Stage12B_reason", "Stage12E_reason", "Stage12G_reason"], dropna=False).size().rename("n").reset_index().to_dict("records"))
    emit("NR3_MISSING_EPISODES", missing.groupby("episode").agg(start=("native_key", "first"),
        end=("native_key", "last"), n=("native_key", "size"), anomaly_overlap=("in_1484_source_anomalies", "sum")).reset_index().to_dict("records"))
    external = grid_receipts(root)
    emit("NR3_EXTERNAL_RECEIPTS", external)
    if args.emit_missing:
        emit_csv("NR3_238_MISSING_LEDGER", missing)
    if args.emit_anomalies:
        emit_csv("NR3_1484_ORIGINAL_ANOMALIES", verified)
    emit("NR3_SCIENCE_LIMIT", "No independent QC0 validation, grid CF/orography verification, installed CTSM/CDEPS constraint audit or repair acceptance has yet been performed by this inventory. All original HOLDs remain; candidate/repair counts are not inferred from physical passes.")
    return raw, selected, missing, verified, external


def q_from_e(e_hpa, pressure_pa):
    epa = 100 * np.asarray(e_hpa, dtype=float)
    return .622 * epa / (np.asarray(pressure_pa, dtype=float) - .378 * epa)


def e_from_q(q, pressure_pa):
    q = np.asarray(q, dtype=float)
    return q * np.asarray(pressure_pa, dtype=float) / (.622 + .378 * q) / 100


def grid_values(t, p, tg, dg, pg):
    """Fixed uncalibrated hypotheses; no clipping, fitting or replacement."""
    water_grid_e = esw(dg)
    grid_rh = water_grid_e / esw(tg)
    return {"A_ABSOLUTE_E": water_grid_e,
            "B_WATER_RH": esw(t) * grid_rh,
            "C_SPECIFIC_Q": e_from_q(q_from_e(water_grid_e, pg), p)}


def reference_datm_esat(t_c):
    """Diagnostic only: public CDEPS blob 181eac30..., not assumed installed."""
    t = np.clip(np.asarray(t_c, dtype=float), -50., 50.)
    a = [6.107799961, .4436518521, .01428945805, .0002650648471,
         .000003031240396, .00000002034080948, .00000000006136820929]
    b = [6.109177956, .5034698970, .01886013408, .0004176223716,
         .000005824720280, .00000004838803174, .0000000001838826904]
    return np.where(np.asarray(t_c) < 0, np.polynomial.polynomial.polyval(t, b),
                    np.polynomial.polynomial.polyval(t, a))


def read_grid(record):
    # netCDF4 is already used by the historical Stage09/10 environment.
    # Import only for --science, so inventory/self-test needs no NetCDF IO.
    from netCDF4 import Dataset, num2date
    year = int(record["year"])
    expected = pd.date_range(f"{year-1}-12-29", f"{year+1}-01-03 23:00:00", freq="h")
    values, coords, static, attrs = {}, [], [], []

    def read_one(ds):
        timevar = ds.variables.get("valid_time")
        if timevar is None:
            timevar = ds.variables.get("time")
        require(timevar is not None and hasattr(timevar, "units"), "Missing CF time units")
        calendar = getattr(timevar, "calendar", "standard")
        require(calendar in {"standard", "gregorian", "proleptic_gregorian"}, "Unexpected grid calendar")
        times = num2date(timevar[:], timevar.units, calendar=calendar,
            only_use_cftime_datetimes=False, only_use_python_datetimes=True)
        actual = pd.DatetimeIndex(pd.to_datetime([str(x) for x in times]))
        require(actual.equals(expected), "Grid UTC hours differ from original padded year")
        lat = np.asarray(ds.variables["latitude"][:], dtype=float).reshape(-1)
        lon = np.asarray(ds.variables["longitude"][:], dtype=float).reshape(-1)
        require(len(lat) == len(lon) == 1, "Expected single grid coordinate")
        point = (float(lat[0]), float(lon[0]))
        location = record["request"]["location"]
        require(abs(point[0] - float(location["latitude"])) <= .151 and
                abs(point[1] - float(location["longitude"])) <= .151,
                "Grid coordinate differs from original request")
        coords.append(point)
        for field, unit in (("t2m", "K"), ("d2m", "K"), ("sp", "Pa")):
            if field not in ds.variables:
                continue
            var = ds.variables[field]
            require(field not in values and getattr(var, "units", "") == unit,
                    "Duplicate grid field or incorrect units: " + field)
            arr = np.asarray(np.ma.asarray(var[:]).filled(np.nan), dtype=float).reshape(-1)
            require(len(arr) == len(expected) and np.isfinite(arr).all(), "Nonfinite/wrong-length grid field")
            values[field] = arr
            attrs.append(dict(field=field, units=unit, dimensions=list(var.dimensions)))
        for name in ("z", "orog", "orography", "geopotential", "surface_geopotential"):
            if name in ds.variables:
                var = ds.variables[name]
                arr = np.asarray(np.ma.asarray(var[:]).filled(np.nan), dtype=float).reshape(-1)
                static.append(dict(name=name, units=getattr(var, "units", ""),
                    minimum=float(np.nanmin(arr)), maximum=float(np.nanmax(arr))))

    path = pin(Path(record["file"]), record["sha256"])
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            members = [x for x in z.infolist() if x.filename.endswith(".nc")]
            require(1 <= len(members) <= 6, "Unexpected count of NetCDF ZIP members")
            for item in members:
                require(item.file_size <= 100_000_000 and not item.filename.startswith("/")
                        and ".." not in Path(item.filename).parts, "Unsafe NetCDF member")
                # No extraction and no diskless writable dataset.
                with Dataset("readonly-memory.nc", "r", memory=z.read(item)) as ds:
                    read_one(ds)
    else:
        with Dataset(str(path), "r") as ds:
            read_one(ds)
    require(set(values) == {"t2m", "d2m", "sp"}, "Incomplete T/dewpoint/pressure grid")
    require(all(np.allclose(x, coords[0], rtol=0, atol=1e-6) for x in coords), "Grid members disagree on point")
    emit("NR3_GRID_CF", dict(year=year, utc_hours=len(expected), grid_point=coords[0],
        grid_T_C_range=[float(values["t2m"].min()-273.15), float(values["t2m"].max()-273.15)],
        grid_P_Pa_range=[float(values["sp"].min()), float(values["sp"].max())],
        dewpoint_gt_T_plus_0p1K=int((values["d2m"] > values["t2m"]+.1).sum()),
        fields=attrs, static_orography=static,
        orography_status="AVAILABLE_REQUIRES_SPATIAL_INTERPRETATION" if static else "NOT_IN_EXISTING_FILE_DO_NOT_INFER_FROM_PRESSURE"))
    return expected, values


def interpolate_grid(times, values, native):
    # Exact legacy Stage10B convention: native interval midpoint, LST UTC-7.
    # This is a documented alignment hypothesis, not a model-clock approval.
    target = native + pd.Timedelta(hours=7, minutes=15)
    x = times.asi8.astype(float) / 1e9
    y = pd.DatetimeIndex(target).asi8.astype(float) / 1e9
    require(len(y) == 0 or (y.min() >= x[0] and y.max() <= x[-1]), "Grid extrapolation is forbidden")
    result = {field: np.interp(y, x, value) for field, value in values.items()}
    result["t2m"] -= 273.15
    result["d2m"] -= 273.15
    return result


def error_summary(frame):
    if frame.empty:
        return dict(n_HH=0, dates=0, years=0)
    error = frame.error_VPD_hPa.to_numpy(dtype=float)
    daily = frame.groupby("date").error_VPD_hPa.agg(
        bias="mean", mae=lambda x: np.abs(x).mean())
    result = dict(n_HH=len(frame), dates=len(daily), years=int(frame.year.nunique()),
        MAE_hPa=float(np.abs(error).mean()), bias_hPa=float(error.mean()),
        RMSE_hPa=float(np.sqrt(np.mean(error**2))), abs_error_P95_hPa=float(np.quantile(np.abs(error), .95)),
        abs_error_gt1hPa_share=float((np.abs(error) > 1.).mean()),
        equal_date_MAE_hPa=float(daily.mae.mean()), equal_date_bias_hPa=float(daily.bias.mean()),
        e_MAE_hPa=float(np.abs(frame.error_e_hPa).mean()))
    if "prediction_water_pass" in frame:
        result["prediction_water_failure_share"] = float((~frame.prediction_water_pass).mean())
        result["prediction_ice_caution_share"] = float(frame.prediction_ice_caution.mean())
    return result


def temp_bin(t):
    return pd.cut(t, [-np.inf, -20, -10, 0, np.inf], right=False,
                  labels=["LT_MINUS20", "MINUS20_TO_MINUS10", "MINUS10_TO_ZERO", "GE_ZERO"]).astype(str)


def evaluate_qc0(raw_grid):
    # Ground truth is only simultaneous original tower QC0 T and VPD.
    # Do not screen truth by the proposed method's T-delta/ice conditions.
    truth = raw_grid.loc[raw_grid.TA_F_QC.eq(0) & raw_grid.VPD_F_QC.eq(0)].copy()
    truth["truth_e"] = esw(truth.TA_F) - truth.VPD_F
    truth = truth.loc[truth.TA_F.between(-80, 65) & truth.VPD_F.ge(0)
                      & truth.truth_e.gt(0)].copy()
    truth["date"] = truth.native_key.str[:8]
    truth["T_regime"] = temp_bin(truth.TA_F)
    methods = grid_values(truth.TA_F, truth.PA_F*1000, truth.grid_T, truth.grid_D, truth.grid_P)
    all_methods = []
    for method, e in methods.items():
        part = truth[["native_key", "year", "month", "date", "T_regime"]].copy()
        part["method"] = method
        part["error_e_hPa"] = e - truth.truth_e
        part["error_VPD_hPa"] = -part.error_e_hPa
        proposed_q = q_from_e(e, truth.PA_F*1000)
        part["prediction_water_pass"] = np.isfinite(e) & (e > 0) & (e <= esw(truth.TA_F)) & (proposed_q > 0) & (proposed_q < .08)
        part["prediction_ice_caution"] = truth.TA_F.lt(0).to_numpy() & (e > esi(truth.TA_F))
        all_methods.append(part)
        for year, group in part.groupby("year"):
            emit("NR3_QC0_YEAR_TEST", dict(method=method, held_out_source_year=int(year),
                no_fitted_parameters=True, **error_summary(group)))
        for regime, group in part.groupby("T_regime"):
            emit("NR3_QC0_T_REGIME_TEST", dict(method=method, regime=regime, **error_summary(group)))
        yearly = [error_summary(g) for _, g in part.groupby("year")]
        emit("NR3_QC0_EQUAL_YEAR_TEST", dict(method=method, n_years=len(yearly),
            equal_year_MAE_hPa=float(np.mean([x["MAE_hPa"] for x in yearly])) if yearly else None,
            equal_year_bias_hPa=float(np.mean([x["bias_hPa"] for x in yearly])) if yearly else None,
            validation_type="FIXED_UNCALIBRATED_METHOD_WHOLE_YEAR_TEST_BLOCKS_NO_RANDOM_HH_SPLIT"))
    # Two genuine QC0 variables still do not make ERA-corrected companion
    # fields out-of-sample: their product fitting may already use those data.
    emit("NR3_VALIDATION_BOUNDARY", dict(years_without_truth=[2017, 2018, 2023],
        no_reanalysis_QC2_as_truth=True, companion_ERA_fit_independence="NOT_ESTABLISHED_NOT_SCORED_AS_INDEPENDENT",
        QBOT_truth="Derived_e_with_PA_F_is_not_independently_measured_QBOT; report VPD/e errors",
        clock="NATIVE_INTERVAL_MIDPOINT_PLUS_7H_NO_TIME_SHIFT_OPTIMISATION"))
    return pd.concat(all_methods, ignore_index=True) if all_methods else pd.DataFrame()


def candidate_flags(t, p, tg, dg, pg, e):
    t, p, tg, dg, pg, e = [np.asarray(x, dtype=float) for x in (t, p, tg, dg, pg, e)]
    vpd = esw(t) - e
    q = q_from_e(e, p)
    rh = esw(dg) / esw(tg)
    site = np.isfinite(t) & np.isfinite(p) & (t >= -80) & (t <= 65) & (p >= 50000) & (p <= 110000)
    grid = np.isfinite(tg) & np.isfinite(dg) & np.isfinite(pg) & (dg <= tg+.1) & (rh > 0) & (rh <= 1) & (pg >= 50000) & (pg <= 110000)
    water = np.isfinite(vpd) & (vpd >= 0) & (vpd < esw(t)) & np.isfinite(q) & (q > 0) & (q < .08)
    ice = (t >= 0) | (e <= esi(t))
    delta_t = np.abs(t-tg) <= 5.
    delta_p = np.abs(p-pg) <= 15000.
    return dict(VPD=vpd, QBOT=q, water_pass=site & grid & water,
        ice_pass=ice, T_delta_pass=delta_t, P_delta_pass=delta_p,
        legacy_screen_pass=site & grid & water & ice & delta_t & delta_p,
        public_CDEPS_reference_would_cap=q > q_from_e(reference_datm_esat(t), p))


def reject_jumps(selected, target, proposed, eligible):
    """Evaluate all proposed missing slots jointly, in memory only."""
    selected_values = selected.VPD_USE.to_numpy(dtype=float).copy()
    accepted = np.asarray(eligible, dtype=bool).copy()
    proposed = np.asarray(proposed, dtype=float)
    for _ in range(len(target)+1):
        current = selected_values.copy()
        current[target[accepted]] = proposed[accepted]
        reject = np.zeros(len(target), dtype=bool)
        for j in np.flatnonzero(accepted):
            k = target[j]
            for neighbour in (k-1, k+1):
                if 0 <= neighbour < len(current) and np.isfinite(current[neighbour]) and abs(current[k]-current[neighbour]) > 4.:
                    reject[j] = True
        if not reject.any():
            return accepted
        accepted[reject] = False
    raise ValueError("In-memory legacy adjacent-jump test did not converge")


def installed_source_review(model_root):
    if not model_root.is_dir():
        emit("NR3_INSTALLED_MODEL_SOURCE", dict(root=str(model_root), status="NOT_FOUND_ACTIVE_CASE_UNVERIFIED"))
        return
    names = {"datm_datamode_clmncep_mod.F90", "datm_comp_mod.F90"}
    found = [x for x in model_root.rglob("datm*.F90") if x.name in names]
    require(len(found) <= 10, "Ambiguous installed DATM source inventory")
    for path in sorted(found):
        text = pin(path).read_text(encoding="utf-8", errors="strict")
        lines = text.splitlines()
        chosen = set()
        for j, line in enumerate(lines):
            if re.search(r"function\s+datm_esat", line, re.I):
                chosen.update(range(max(0, j-1), min(len(lines), j+55)))
            if re.search(r"qsat\s*<.*shum|shum.*=\s*qsat", line, re.I):
                chosen.update(range(max(0, j-5), min(len(lines), j+6)))
        emit("NR3_INSTALLED_MODEL_SOURCE", dict(path=str(path), sha256=digest(path),
            source_excerpt=[f"{j+1}: {lines[j]}" for j in sorted(chosen)],
            status="SOURCE_ONLY_ACTIVE_CASE_DATAMODE_AND_BUILD_NOT_VERIFIED"))
    if not found:
        emit("NR3_INSTALLED_MODEL_SOURCE", dict(root=str(model_root), status="DATM_SOURCE_NOT_FOUND"))


def science_review(root, data, args):
    raw, selected, missing, anomalies, external = data
    raw = raw.copy()
    for col in ("grid_T", "grid_D", "grid_P"):
        raw[col] = np.nan
    for record in external:
        require("year" in record, "NR3 external evidence directory unavailable")
        times, values = read_grid(record)
        index = raw.index[raw.year.eq(int(record["year"]))]
        grid = interpolate_grid(times, values, native_times(raw.loc[index], "TIMESTAMP_START"))
        raw.loc[index, ["grid_T", "grid_D", "grid_P"]] = np.column_stack([grid["t2m"], grid["d2m"], grid["sp"]])
    # Pressure comparison only at genuine measured site pressure.
    grid_ok = raw[["grid_T", "grid_D", "grid_P"]].notna().all(axis=1)
    for year, group in raw.loc[grid_ok & raw.TA_F_QC.eq(0)].groupby("year"):
        delta = group.TA_F - group.grid_T
        emit("NR3_MEASURED_T_VS_GRID", dict(year=int(year), n=len(group),
            mean_site_minus_grid_C=float(delta.mean()), MAE_C=float(delta.abs().mean()),
            abs_delta_P95_C=float(delta.abs().quantile(.95)), abs_delta_gt5C_share=float(delta.abs().gt(5).mean())))
    for year, group in raw.loc[grid_ok & raw.PA_F_QC.eq(0)].groupby("year"):
        delta = group.PA_F*1000 - group.grid_P
        emit("NR3_MEASURED_PRESSURE_VS_GRID", dict(year=int(year), n=len(group),
            median_site_minus_grid_Pa=float(delta.median()), abs_delta_P95_Pa=float(delta.abs().quantile(.95)),
            inference="Pressure difference is not a measured grid elevation"))
    validation = evaluate_qc0(raw.loc[grid_ok])
    selected_keys = keys(selected, "time")
    indexed = raw.set_index("native_key")
    selected_index = selected.assign(native_key=selected_keys).set_index("native_key")
    anomaly_grid = anomalies[["native_key", "source_csv_row", "TA_F", "TA_F_QC", "VPD_F", "VPD_F_QC",
        "TA_ERA", "VPD_ERA", "ERA_e_water_hPa"]].copy()
    anomaly_grid = anomaly_grid.join(indexed[["grid_T", "grid_D", "grid_P"]], on="native_key", validate="one_to_one")
    anomaly_grid = anomaly_grid.join(selected_index[["TA_USE", "PSRF", "VPD_USE", "QBOT"]], on="native_key", validate="one_to_one")
    emit("NR3_ANOMALY_CURRENT_SELECTION", dict(original_cohort=len(anomaly_grid),
        current_finite_VPD=int(anomaly_grid.VPD_USE.notna().sum()), current_missing_VPD=int(anomaly_grid.VPD_USE.isna().sum()),
        note="Existing finite values remain research candidates; finite count is not a repair-validation result"))
    anomaly_methods = grid_values(anomaly_grid.TA_USE, anomaly_grid.PSRF, anomaly_grid.grid_T, anomaly_grid.grid_D, anomaly_grid.grid_P)
    anomaly_rows = []
    for method, e in anomaly_methods.items():
        flags = candidate_flags(anomaly_grid.TA_USE, anomaly_grid.PSRF, anomaly_grid.grid_T, anomaly_grid.grid_D, anomaly_grid.grid_P, e)
        emit("NR3_ANOMALY_METHOD_SCREEN", dict(method=method, original_cohort=len(anomaly_grid),
            water_pass=int(flags["water_pass"].sum()), ice_cautions=int((~flags["ice_pass"]).sum()),
            T_delta_fail=int((~flags["T_delta_pass"]).sum()),
            combined_legacy_screen_pass=int(flags["legacy_screen_pass"].sum()),
            public_CDEPS_reference_cap_flags=int(flags["public_CDEPS_reference_would_cap"].sum()),
            approvals=0, status="DIAGNOSTIC_ONLY_NO_1484_AUTOFILL"))
        if args.emit_anomaly_science_rows:
            part = anomaly_grid.copy()
            part["method"] = method
            part["candidate_e_hPa"] = e
            part["candidate_RH_water_pct"] = 100*e/esw(part.TA_USE)
            part["candidate_RH_ice_pct"] = 100*e/esi(part.TA_USE)
            for key, value in flags.items():
                part[key] = value
            part["APPROVED_FOR_NEW_VERSION"] = False
            anomaly_rows.append(part)
    if anomaly_rows:
        emit_csv("NR3_1484_METHOD_PHYSICS", pd.concat(anomaly_rows, ignore_index=True))
    targets = missing[["native_key", "episode", "missing_fields", "TA_USE", "PSRF",
                       "HOLD_class", "Stage12B_reason", "Stage12E_reason", "Stage12G_reason"]].copy()
    targets = targets.join(indexed[["grid_T", "grid_D", "grid_P", "TA_F_QC", "VPD_F_QC", "RH", "year", "month"]], on="native_key", validate="one_to_one")
    targets["T_regime"] = temp_bin(targets.TA_USE)
    targets["scientific_disposition"] = np.where(
        targets.Stage12E_reason.eq("NO_VERIFIED_ERA5LAND_SOURCE_FOR_SITE_YEAR"),
        "EVIDENCE_INSUFFICIENT_HOLD", "PHYSICS_CONFLICT_HOLD")
    emit("NR3_SCIENCE_DISPOSITION", dict(inherited_238_preserved=True,
        reason_counts=targets.groupby(["scientific_disposition", "Stage12E_reason"], dropna=False).size().rename("n").reset_index().to_dict("records"),
        note="Retains inherited HOLD_class separately; the 41 T-delta and 19 ice failures are explicit screening conflicts, not simply unavailable evidence"))
    position = {key: j for j, key in enumerate(selected_keys)}
    locations = np.array([position[key] for key in targets.native_key], dtype=int)
    methods = grid_values(targets.TA_USE, targets.PSRF, targets.grid_T, targets.grid_D, targets.grid_P)
    potential = []
    for method, e in methods.items():
        flags = candidate_flags(targets.TA_USE, targets.PSRF, targets.grid_T, targets.grid_D, targets.grid_P, e)
        final = reject_jumps(selected, locations, flags["VPD"],
            flags["legacy_screen_pass"] & targets.VPD_F_QC.isin([1, 2]).to_numpy())
        emit("NR3_MISSING_METHOD_SCREEN", dict(method=method, cohort=238,
            external_year_available=int(targets.grid_T.notna().sum()), water_pass=int(flags["water_pass"].sum()),
            water_ice_T_P_pass=int(flags["legacy_screen_pass"].sum()), with_legacy_jump_pass=int(final.sum()),
            pass_in_protected172=int((final & targets.HOLD_class.eq("PHYSICS_CONFLICT_HOLD").to_numpy()).sum()),
            remaining_screen_fail=int((~final).sum()), public_CDEPS_reference_cap_flags=int(flags["public_CDEPS_reference_would_cap"].sum()),
            scientifically_approved_repairs=0, actual_remaining_HOLD=238,
            interpretation="Sensitivity counts only; original protected172 never promoted or written"))
        for j, row in targets.iterrows():
            group = validation.loc[validation.method.eq(method) & validation.month.eq(row.month)
                                   & validation.T_regime.eq(row.T_regime)]
            potential.append(dict(native_key=row.native_key, source_csv_row=int(indexed.loc[row.native_key, "source_csv_row"]),
                method=method, numeric_screen_pass=bool(final[j]), proposed_VPD_hPa=float(flags["VPD"][j]) if np.isfinite(flags["VPD"][j]) else None,
                same_month_T_regime_QC0_n=len(group), QC0_dates=int(group.date.nunique()), QC0_years=int(group.year.nunique()),
                same_regime_MAE_hPa=float(group.error_VPD_hPa.abs().mean()) if len(group) else None,
                same_regime_bias_hPa=float(group.error_VPD_hPa.mean()) if len(group) else None,
                target_year_has_no_dual_QC0=int(row.year) in {2017, 2018, 2023}, APPROVED_FOR_NEW_VERSION=False))
    # Small exact target cohort: print its original QC and nearest true QC0
    # brackets. Do not interpolate or label a distant anchor a repair.
    truth_e = esw(raw.TA_F) - raw.VPD_F
    truth = raw.loc[raw.TA_F_QC.eq(0) & raw.VPD_F_QC.eq(0) & truth_e.gt(0) & raw.VPD_F.ge(0)].copy()
    truth["native_dt"] = native_times(truth, "TIMESTAMP_START")
    for _, episode in missing.groupby("episode"):
        dt = native_times(episode, "native_key")
        left = truth.loc[truth.native_dt < dt.min()].tail(1)
        right = truth.loc[truth.native_dt > dt.max()].head(1)
        emit("NR3_EPISODE_QC0_BRACKETS", dict(episode=int(episode.episode.iloc[0]), start=str(dt.min()), end=str(dt.max()),
            n=len(episode), left_hours=float((dt.min()-left.native_dt.iloc[0]).total_seconds()/3600) if len(left) else None,
            right_hours=float((right.native_dt.iloc[0]-dt.max()).total_seconds()/3600) if len(right) else None))
    for year in (2017, 2018, 2023):
        group = raw.loc[raw.year.eq(year)]
        emit("NR3_UNOBSERVED_YEAR_SOURCE", dict(year=year,
            RH_numeric=int(group.RH.notna().sum()), TA_MDS_QC_counts={str(k): int(v) for k, v in group.TA_F_MDS_QC.value_counts(dropna=False).items()},
            VPD_MDS_QC_counts={str(k): int(v) for k, v in group.VPD_F_MDS_QC.value_counts(dropna=False).items()},
            status="NO_DUAL_QC0_TRUTH; RH availability alone does not supply a measured temperature pair"))
    if args.emit_science_rows:
        emit_csv("NR3_238_METHOD_SUPPORT", pd.DataFrame(potential))
    else:
        emit("NR3_METHOD_SUPPORT_SUMMARY", pd.DataFrame(potential).groupby("method").agg(
            target_rows=("native_key", "size"), with_any_matched_QC0_dates=("QC0_dates", lambda x: int(x.gt(0).sum())),
            matched_QC0_years_min=("QC0_years", "min"), matched_QC0_dates_min=("QC0_dates", "min")).reset_index().to_dict("records"))
    installed_source_review(args.model_root)
    emit("NR3_SCIENCE_GATE", dict(status="METHOD_COMPARISON_ONLY_NO_REPAIR_ACCEPTANCE", actual_remaining_HOLD=238,
        original_anomalies=1484, missing_overlap=172, approvals=0,
        grid_orography_required=True, BASE_sensor_QA_still_required=True,
        model_case_build_unverified=True, no_thresholds_relaxed=True))


def self_test():
    # Regression for the actual IRIDIS6 historical timestamp that stopped
    # v1. A separator is representation, not a native-clock adjustment.
    for stamp in ("2007-01-12T04:00:00", "2007-01-12 04:00:00"):
        require(keys(pd.DataFrame({"time": [stamp]}), "time").tolist() == ["200701120400"],
                "Historical ISO-T/space key normalization")
    mixed = pd.DataFrame({"time": ["2007-01-12T04:00:00", "2007-01-12 04:30:00"]})
    require(keys(mixed, "time").tolist() == ["200701120400", "200701120430"],
            "Mixed historical separators changed time identity")
    for times in (["2007-01-12T04:00:00", "2007-01-12 04:00:00"],
                  ["2007-01-12T04:00:00Z"], ["2007-01-12T04:00:00-07:00"],
                  ["2007-01-12T04:00:01"], ["2007-01-12T04:01:00"],
                  ["2007-02-30T04:00:00"]):
        try:
            keys(pd.DataFrame({"time": times}), "time")
        except ValueError:
            pass
        else:
            raise AssertionError("Ambiguous/duplicate/off-grid/invalid native times accepted")
    # Timestamp-keyed join must survive unequal source/ERA spans.
    primary = pd.DataFrame({"TIMESTAMP_START": ["201701010000", "201701010030"],
        "TIMESTAMP_END": ["201701010030", "201701010100"], "TA_F": [-20., -19.],
        "VPD_F": [2., 2.], "TA_F_QC": [2, 2], "VPD_F_QC": [2, 2]})
    era = pd.DataFrame({"TIMESTAMP_START": ["201612312330", "201701010000", "201701010030"],
        "TA_ERA": [-30., -20., -19.], "VPD_ERA": [3., 2., 2.]})
    joined = attach_raw(primary, era)
    require(joined.source_csv_row.tolist() == [2, 3], "CSV header row convention")
    require(joined.TA_ERA.tolist() == [-20., -19.] and joined.ERA_e_water_hPa.lt(0).all(), "Nonpositional ERA join/sign test")
    for bad in (pd.concat([era, era.iloc[[0]]], ignore_index=True), era.iloc[:1]):
        try:
            attach_raw(primary, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Duplicate/disjoint companion timestamps accepted")
    require(esi(-20) < esw(-20), "Water/ice saturation order")
    epa = float(esw(-20)) * .5 * 100
    q = .622 * epa / (66000 - .378 * epa)
    recovered = q * 66000 / (.622 + .378 * q)
    require(abs(recovered - epa) < 1e-10, "QBOT vapour pressure closure")
    hypotheses = grid_values(np.array([-20., 5.]), np.array([66000., 66000.]),
        np.array([-18., 7.]), np.array([-25., -1.]), np.array([70000., 70000.]))
    require(np.allclose(hypotheses["A_ABSOLUTE_E"], esw(np.array([-25., -1.]))), "Absolute-e hypothesis")
    require(np.allclose(hypotheses["B_WATER_RH"]/esw(np.array([-20., 5.])),
        esw(np.array([-25., -1.]))/esw(np.array([-18., 7.]))), "Grid-RH hypothesis")
    require(np.allclose(hypotheses["C_SPECIFIC_Q"], hypotheses["A_ABSOLUTE_E"]*66000/70000),
        "Specific-Q pressure transfer")
    stats_frame = pd.DataFrame({"date": ["20170101", "20170101", "20170102"],
        "year": [2017, 2017, 2017], "error_VPD_hPa": [1., 1., 3.], "error_e_hPa": [-1., -1., -3.]})
    metrics = error_summary(stats_frame)
    require(np.isclose(metrics["MAE_hPa"], 5/3) and np.isclose(metrics["equal_date_MAE_hPa"], 2.),
        "Equal-date errors must differ from pseudo-independent halfhour weighting")
    jumps = reject_jumps(pd.DataFrame({"VPD_USE": [1., np.nan, np.nan, 1.]}),
        np.array([1, 2]), np.array([2., 8.]), np.array([True, True]))
    require(jumps.tolist() == [False, False], "Adjacent proposed-pair jump rejection")
    f = candidate_flags(np.array([-20.]), np.array([66000.]), np.array([-20.]),
        np.array([-25.]), np.array([66000.]), np.array([-1.]))
    require(not f["legacy_screen_pass"].any(), "Negative e cannot pass candidate physics")
    # Exercise the actual 238=172+66 reconciliation, with the narrower six
    # source-year rows nested inside 66; these are synthetic, not site data.
    dt = pd.date_range("2017-01-01", periods=238, freq="30min")
    native = pd.Series(dt.strftime("%Y%m%d%H%M"))
    selected = pd.DataFrame({"time": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "TA_USE": np.full(238, -20.), "PSRF": np.full(238, 66000.),
        "VPD_USE": np.full(238, np.nan), "QBOT": np.full(238, np.nan)})
    raw = pd.DataFrame({"native_key": native, "TA_F": np.full(238, -20.)})
    protected = pd.DataFrame({"native_key": native.iloc[:172], "reason": "SYNTHETIC_PHYSICS"})
    other = pd.DataFrame({"native_key": native.iloc[172:], "science_hold_reason": "SYNTHETIC_GAP"})
    newyear = pd.DataFrame({"native_key": native.iloc[172:178], "reason": "SYNTHETIC_YEAR"})
    anomalies = pd.DataFrame({"native_key": native.iloc[:200]})
    ledger = reconcile_missing(selected, raw, protected, other, newyear, anomalies)
    require(len(ledger) == 238 and ledger.in_1484_source_anomalies.sum() == 200
            and ledger.episode.nunique() == 1 and not ledger.APPROVED_FOR_NEW_VERSION.any(),
            "Synthetic HOLD/overlap/episode reconciliation")
    altered = selected.copy()
    altered.loc[0, ["VPD_USE", "QBOT"]] = [1., .001]
    try:
        reconcile_missing(altered, raw, protected, other, newyear, anomalies)
    except ValueError:
        pass
    else:
        raise AssertionError("A filled protected HOLD escaped detection")
    for event, arg in (("open", ("unused", "w", os.O_WRONLY)),
                       ("os.mkdir", ("unused", 0, -1)), ("subprocess.Popen", ())):
        try:
            deny_writes(event, arg)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Read-only guard failed")
    deny_writes("open", ("unused", "r", 0))
    emit("NR3_SELF_TEST", "PASS: ISO-T/space and exact clocks, source joins, phase/QBOT algebra, A/B/C humidity transfers, date-weighted errors, joint-candidate jump rejection, 238/172/66/6 nested counts, protected HOLDs and mutation guard; no files created")


def main():
    global COMPACT
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--science", action="store_true")
    mode.add_argument("--raw-zip", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--emit-missing", action="store_true")
    parser.add_argument("--emit-anomalies", action="store_true")
    parser.add_argument("--emit-science-rows", action="store_true")
    parser.add_argument("--emit-anomaly-science-rows", action="store_true")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--model-root", type=Path,
        default=ROOT.parent.parent / "CTSM")
    args = parser.parse_args()
    COMPACT = args.compact
    sys.addaudithook(deny_writes)
    emit("NR3_AUDIT_VERSION", VERSION)
    self_test()
    if args.raw_zip:
        raw_zip(args.raw_zip)
    elif args.check or args.science:
        result = audit(args.root, args)
        if args.science:
            science_review(args.root, result, args)
    for path, expected in READS.items():
        require(digest(path) == expected, "Input changed during audit: " + path)
    emit("NR3_READ_SHA256", READS)
    if COMPACT:
        emit("NR3_PRESERVATION", dict(sha_checked_before_and_after=len(READS),
            Stage12G_selected_sha=READS.get(str(args.root / G / (SITE + "_STAGE12G_INCOMPLETE_NOLEAP.csv"))),
            source_manifest_sha=READS.get(str(args.root / S07 / "exact_input_manifest.json"))))
    emit("NR3_COMPLETE", "READONLY_PASS; stdout only; no data/shadow/report/model writes or approvals")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("NR3_STOP", type(exc).__name__ + ":", str(exc), file=sys.stderr, flush=True)
        raise SystemExit(2)

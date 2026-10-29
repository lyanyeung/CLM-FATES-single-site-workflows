#!/usr/bin/env python3
"""US-NR3 first-pass source reconciliation. Read-only; stdout only.

Modes: --self-test; --raw-zip PATH (local original-package audit); --check
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
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

VERSION = "nr3-01-v1.1-20261029"
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
    emit("NR3_EXTERNAL_RECEIPTS", grid_receipts(root))
    if args.emit_missing:
        emit_csv("NR3_238_MISSING_LEDGER", missing)
    if args.emit_anomalies:
        emit_csv("NR3_1484_ORIGINAL_ANOMALIES", verified)
    emit("NR3_SCIENCE_LIMIT", "No independent QC0 validation, grid CF/orography verification, installed CTSM/CDEPS constraint audit or repair acceptance has yet been performed by this inventory. All original HOLDs remain; candidate/repair counts are not inferred from physical passes.")


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
    emit("NR3_SELF_TEST", "PASS: historical ISO-T/space equivalence, timezone/off-grid/duplicate rejection, exact joins, unequal spans, CSV row IDs, phase/QBOT algebra, 238/172/66/6 nested counts, overlaps, filled-protected-HOLD rejection and mutation guard; no files created")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--raw-zip", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--emit-missing", action="store_true")
    parser.add_argument("--emit-anomalies", action="store_true")
    args = parser.parse_args()
    sys.addaudithook(deny_writes)
    emit("NR3_AUDIT_VERSION", VERSION)
    self_test()
    if args.raw_zip:
        raw_zip(args.raw_zip)
    elif args.check:
        audit(args.root, args)
    for path, expected in READS.items():
        require(digest(path) == expected, "Input changed during audit: " + path)
    emit("NR3_READ_SHA256", READS)
    emit("NR3_COMPLETE", "READONLY_PASS; stdout only; no data/shadow/report/model writes or approvals")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("NR3_STOP", type(exc).__name__ + ":", str(exc), file=sys.stderr, flush=True)
        raise SystemExit(2)

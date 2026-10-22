#!/usr/bin/env python3
"""Batch03 Stage08f: read-only MDS TA/VPD humidity diagnostics.

An MDS value's presence is not repair approval. Quantifies source QC, pair
physical consistency, comparison to consolidated F and ERA companion, and
where missing external meteorological evidence is still required.
--check: no outputs. --run: new reports only. No forcing edits or DATM.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

EXP = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = EXP / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE08C = EXP / "reports/stage08c_era_humidity_20261022T031437Z_512e8731"
STAGE08D = EXP / "reports/stage08d_vpd_provenance_20261022T031928Z_21f52e9c"
STAGE08E = EXP / "reports/stage08e_alternatives_20261022T032727Z_b122e5b0"
EXPECTED = {"US-Kon":229, "US-MMS":18, "US-Me2":4, "US-Me6":1,
            "US-MtB":15, "US-NR1":173, "US-NR3":1484}
VARS = ("TA_F_MDS", "VPD_F_MDS", "TA_F_MDS_QC", "VPD_F_MDS_QC",
        "TA_F", "VPD_F")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def numbers(df, key):
    vals = pd.to_numeric(df[key], errors="coerce").to_numpy(dtype=float)
    vals[(~np.isfinite(vals)) | (vals <= -9990)] = np.nan
    return vals


def saturation_water_hpa(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return 6.112 * np.exp(np.clip(17.67 * t / (t + 243.5), -40, 40))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = p.parse_args()

    for folder in (EXP, STAGE07, STAGE08C, STAGE08D, STAGE08E):
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Missing or unsafe experiment directory: " + str(folder))
    if not (STAGE07 / "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage07 incomplete marker missing")
    policy_file = STAGE08E / "evidence_policy.json"
    policy = json.loads(policy_file.read_text(encoding="utf-8"))
    if (Path(policy["stage08d_report"]).resolve() != STAGE08D or
            int(policy["records"]) != 1924 or
            digest(STAGE08C / "era_humidity_residual_details.csv") != policy["stage08c_sha256"]):
        raise ValueError("Stage08e evidence lineage/hash mismatch")

    original = pd.read_csv(STAGE08C / "era_humidity_residual_details.csv",
                           dtype=str, keep_default_na=False)
    evidence_file = STAGE08E / "raw_alternatives_at_blockers.csv"
    if evidence_file.is_symlink() or not evidence_file.is_file():
        raise ValueError("Missing Stage08e alternatives evidence")
    data = pd.read_csv(evidence_file, dtype=str, keep_default_na=False)
    if len(data) != 1924 or any(v not in data.columns for v in
             ("site", "source_csv_row", "time", *VARS)):
        raise ValueError("Unexpected Stage08e evidence shape")
    if len(original) != 1924:
        raise ValueError("Stage08c residual count mismatch")

    keys = ["site", "source_csv_row", "time"]
    if original.duplicated(keys).any() or data.duplicated(keys).any():
        raise ValueError("Duplicate event keys")
    if set(map(tuple, original[keys].to_numpy())) != set(map(tuple, data[keys].to_numpy())):
        raise ValueError("Stage08e and Stage08c source-row identities differ")
    for site, count in EXPECTED.items():
        if int(data.site.eq(site).sum()) != count:
            raise ValueError("Wrong evidence record count for " + site)

    manifest = json.loads((STAGE07 / "exact_input_manifest.json").read_text())
    pinned = manifest["input_sha256"]
    items = {r["site"]: r for r in manifest["sites"]}
    for site in EXPECTED:
        path = Path(items[site]["primary"]).resolve()
        if str(path) not in pinned or digest(path) != pinned[str(path)]:
            raise ValueError("Raw primary SHA256 not preserved for " + site)
        print("RAW SHA256 PASS:", site, flush=True)

    # Join original site pressure, both F and MDS versions, and QC codes.
    df = data.merge(original[keys + ["PA_before_fallback_kPa", "TA_before_fallback_C",
        "VPD_before_fallback_hPa", "TA_ERA_C", "VPD_ERA_hPa", "ERA_RH_pct",
        "VPD_original_QC"]], on=keys, how="inner", validate="one_to_one")
    t = numbers(df, "TA_F_MDS")
    v = numbers(df, "VPD_F_MDS")
    qt = numbers(df, "TA_F_MDS_QC")
    qv = numbers(df, "VPD_F_MDS_QC")
    tf = numbers(df, "TA_before_fallback_C")
    vf = numbers(df, "VPD_before_fallback_hPa")
    te = numbers(df, "TA_ERA_C")
    ve = numbers(df, "VPD_ERA_hPa")
    pa = numbers(df, "PA_before_fallback_kPa") * 1000.0
    haspair = np.isfinite(t) & np.isfinite(v)
    qc_good = np.isin(qt, [0,1]) & np.isin(qv, [0,1])
    qc_medium_poor = np.isin(qt, [2,3]) | np.isin(qv, [2,3])
    es = saturation_water_hpa(t)
    ea = es - v
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        q = 0.622 * (ea * 100) / (pa - 0.378 * (ea * 100))
        rh = 100.0 * ea / es
    pair_valid = (haspair & (t >= -80) & (t <= 65) & (v >= 0) & (v <= 125)
                  & np.isfinite(pa) & (pa >= 50000) & (pa <= 110000)
                  & np.isfinite(rh) & (rh > 0) & (rh <= 100.05)
                  & np.isfinite(q) & (q > 0) & (q <= .08))
    retained_es = saturation_water_hpa(tf)
    retained_ea = retained_es-v
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        rh_retained = 100*retained_ea/retained_es
        q_retained = .622*(retained_ea*100)/(pa-.378*(retained_ea*100))
    retained_vpd_valid = (haspair & np.isfinite(tf) &
                          np.isfinite(rh_retained) & (rh_retained > 0) &
                          (rh_retained <= 100.05) &
                          np.isfinite(q_retained) & (q_retained > 0) &
                          (q_retained <= .08) & (v >= 0) & (v <= 125))
    match_f_vpd = haspair & np.isfinite(vf) & np.isclose(v,vf,rtol=0,atol=.05)
    match_era_vpd = haspair & np.isfinite(ve) & np.isclose(v,ve,rtol=0,atol=.05)
    match_f_t = haspair & np.isfinite(tf) & np.isclose(t,tf,rtol=0,atol=.05)
    match_era_t = haspair & np.isfinite(te) & np.isclose(t,te,rtol=0,atol=.05)

    # Mutually exclusive, conservative review classes.
    review = np.full(len(df), "HOLD_NO_COMPLETE_MDS_PAIR", dtype=object)
    review[haspair & ~pair_valid] = "HOLD_MDS_PAIR_PHYSICALLY_INCONSISTENT"
    review[pair_valid] = "REVIEW_MDS_PAIR_VALID_QC_UNVERIFIED"
    review[pair_valid & qc_medium_poor] = "REVIEW_MDS_PAIR_VALID_QC2_OR_3"
    review[pair_valid & qc_good] = "REVIEW_MDS_PAIR_VALID_QC0_OR_1"
    # These categories are NOT permissions to replace any meteorological field.

    df["MDS_pair_present"] = haspair
    df["MDS_pair_physical_screen_pass"] = pair_valid
    df["MDS_QC_both_0_or_1"] = qc_good
    df["MDS_QC_any_2_or_3"] = qc_medium_poor
    df["MDS_VPD_valid_at_retained_TA"] = retained_vpd_valid
    df["MDS_RH_at_MDS_TA_pct"] = rh
    df["MDS_RH_at_retained_TA_pct"] = rh_retained
    df["MDS_QBOT_at_MDS_TA_kgkg"] = q
    df["MDS_VPD_near_original_F"] = match_f_vpd
    df["MDS_VPD_near_paired_ERA"] = match_era_vpd
    df["MDS_TA_near_original_F"] = match_f_t
    df["MDS_TA_near_paired_ERA"] = match_era_t
    df["review_class"] = review

    stats=[]
    for site, count in EXPECTED.items():
        g=df.loc[df.site.eq(site)]
        stats.append(dict(site=site, blockers=count,
             MDS_pair_present=int(g.MDS_pair_present.sum()),
             MDS_pair_physical_pass=int(g.MDS_pair_physical_screen_pass.sum()),
             MDS_pair_QC01_and_pass=int((g.MDS_pair_physical_screen_pass & g.MDS_QC_both_0_or_1).sum()),
             MDS_pair_QC23_and_pass=int((g.MDS_pair_physical_screen_pass & g.MDS_QC_any_2_or_3).sum()),
             MDS_VPD_valid_retained_TA=int(g.MDS_VPD_valid_at_retained_TA.sum()),
             MDS_VPD_near_F=int(g.MDS_VPD_near_original_F.sum()),
             MDS_VPD_near_ERA=int(g.MDS_VPD_near_paired_ERA.sum()),
             original_TA_near_MDS=int(g.MDS_TA_near_original_F.sum()),
             **{k:int((g.review_class==k).sum()) for k in sorted(set(review))}))
    summary=pd.DataFrame(stats)
    byclass=df.groupby(["site","review_class"],sort=True).size().rename("rows").reset_index()
    print("\nSTAGE08F: MDS PAIR SCIENCE SCREEN (no replacements)")
    print(summary.to_string(index=False))
    print("\nOVERALL REVIEW CLASSES")
    print(df.review_class.value_counts().to_string())
    print("STAGE08F PREFLIGHT: 1924/1924 source rows traced, 7/7 primary SHA256 verified")
    if args.check:
        print("CHECK ONLY: no reports written")
        return 0
    report_root = EXP/"reports"
    out=report_root/("stage08f_mds_pairs_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=False,exist_ok=False)
    summary.to_csv(out/"mds_pair_site_summary.csv",index=False)
    byclass.to_csv(out/"mds_review_classes.csv",index=False)
    df.to_csv(out/"mds_pair_at_1924_blockers.csv",index=False)
    (out/"policy.json").write_text(json.dumps({
       "stage08e_evidence":str(STAGE08E),
       "stage08e_evidence_sha256":digest(evidence_file),
       "records":1924,
       "review_only":True,
       "decision":"No MDS substitution approved. Correct pairing, physical screen, QC and independent validation remain necessary.",
       "limitations":[
           "MDS is a gapfill series, not intrinsically independent observed data.",
           "MDS QC=0 measured, 1 good gapfill, 2 medium, 3 poor; QC0/1 alone does not prove source humidity is independent.",
           "MDS pair validity checks both TA and VPD jointly; never mix incompatible TA/VPD blindly.",
           "ERA5 and FLUXNET variables can share downscaled sources.",
           "These reports do not approve DATM or change incomplete trial markers."]},indent=2)+"\n",encoding="utf-8")
    print("STAGE08F SUMMARY: 1924/1924 assessed; report_only=True")
    print("REPORT DIR:",out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())

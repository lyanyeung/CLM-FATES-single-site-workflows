#!/usr/bin/env python3
"""CH-Aws Stage34: scientifically PROVISIONAL QBOT sensitivity for 27 QC1 rows.

Based on Stage33 review: 25 records in 2007, 2 in 2008, VPD_F_QC=1
and site-inferred RH<10%, both ERA5/ERA5-Land RH>=30%, differences <=15 pp,
ERA5-Land RH >= original RH +20 pp. This is a SENSITIVITY, not evidence
that the MDS gapfill is definitely wrong; reanalyses are not station data.

Modes: --audit (default, read-only), --write --acknowledge-reanalysis-uncertainty
(new, non-overwriting v6 directory), --verify (read-only). Never submits
Slurm jobs, edits CIME cases, forces RH floors, or changes QC0 observations.
All Stage29 v5 records are preserved: only 2007/2008 QBOT changes.
All unmodified annual files are symlinks to existing v5, which in turn
may link to original RH25A v3; those parent directories must remain.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/CH-Aws/forcing")
V5 = ROOT / "datm_11_stage29_all77_rh_sensitivity_v5"
V6 = ROOT / "datm_11_stage34_qc1_27rh_sensitivity_v6"
CSV = ROOT / "merged_multisource_11_landrh25a/CH-Aws_multisource_HH_2006_2024_candidate.csv"
EVIDENCE = Path.home() / "FLUXNET_MultiSite_11/stage33_CH_Aws_QC01_evidence/01_all_96_QC01_reanalysis_review.csv"
CACHE = Path.home() / "FLUXNET_MultiSite_11/stage09_CH_Aws/raw_openmeteo"
YEARS = range(2006, 2025)
EXPECTED = {2007: 25, 2008: 2}

def require(ok, msg):
    if not ok:
        raise RuntimeError("STOP: " + msg)

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sat(tc):
    tc = np.asarray(tc, dtype=float)
    return 6.112 * np.exp(np.clip(17.67 * tc / (tc + 243.5), -100, 100))

def model_rh(model, year, desired):
    f = CACHE / f"{model}_{year}.json"
    require(f.is_file(), f"Missing cached {model}_{year}: {f}")
    j = json.loads(f.read_text())
    require(j.get("utc_offset_seconds") == 0, "Reference not UTC: " + str(f))
    hourly = j["hourly"]
    times = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="raise"))
    expected = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    require(times.equals(expected), f"{model} {year}: incomplete hourly reference")
    t = pd.to_numeric(pd.Series(hourly["temperature_2m"]),
                      errors="coerce").to_numpy(dtype=float)
    td = pd.to_numeric(pd.Series(hourly["dew_point_2m"]),
                       errors="coerce").to_numpy(dtype=float)
    z = pd.DataFrame({"T": t, "Td": td}, index=times + pd.Timedelta(hours=1))
    z = (z.reindex(z.index.union(desired)).sort_index()
         .interpolate(method="time", limit=1, limit_area="inside")
         .reindex(desired))
    require(z.notna().all().all(), f"{model} {year}: missing event reference values")
    return 100 * sat(z["Td"].to_numpy()) / sat(z["T"].to_numpy())

def annual_axis(nc, year):
    t = nc["time"]
    idx = pd.DatetimeIndex([str(x)[:19] for x in num2date(
        t[:], t.units, calendar=getattr(t, "calendar", "noleap"))])
    require(len(idx) == 17520 and idx.is_unique and (idx.year == year).all(),
            f"{year}: wrong annual noleap time axis")
    return idx

def read_evidence():
    require(V5.is_dir() and CSV.is_file() and EVIDENCE.is_file(),
            "Stage29 v5 or source CSV or Stage33 report unavailable")
    parent_meta = V5 / "stage29_manifest.json"
    require(parent_meta.is_file(), "Stage29 v5 manifest unavailable")
    m = json.loads(parent_meta.read_text())
    require(m.get("version") == "STAGE29_FULL_77_QBOT_SENSITIVITY_V5"
            and m.get("changed_vs_RH25A_v3") == 77,
            "Wrong or unexpected Stage29 v5 parent")
    for year in YEARS:
        require((V5 / f"CH-Aws_DATM_{year}.nc").is_file(),
                f"Parent annual forcing missing: {year}")
    status = CSV.parent / "status.json"
    require(status.is_file(), "RH25A CSV manifest missing")
    require(json.loads(status.read_text()).get("candidate_sha256") == sha(CSV),
            "RH25A CSV changed since original manifest")
    evidence = pd.read_csv(EVIDENCE, parse_dates=["time"], low_memory=False)
    require(evidence.time.is_unique and len(evidence) == 96,
            "Stage33 report must contain exactly 96 unique excluded records")
    evidence = evidence.set_index("time").sort_index()
    for col in ("TA_F", "PA_F", "RH_IMPLIED_PCT", "VPD_F_QC",
                "era5_RH_pct", "era5_land_RH_pct"):
        require(col in evidence, f"Missing Stage33 evidence column: {col}")
        evidence[col] = pd.to_numeric(evidence[col], errors="coerce")
    require("candidate_for_manual_review_only" in evidence,
            "Missing Stage33 review flag")
    printed_flag = (evidence["candidate_for_manual_review_only"]
                    .astype(str).str.lower().eq("true"))
    calculated_flag = (evidence.VPD_F_QC.eq(1)
                       & evidence["era5_RH_pct"].ge(30)
                       & evidence["era5_land_RH_pct"].ge(30)
                       & (evidence.era5_RH_pct-evidence.era5_land_RH_pct).abs().le(15)
                       & (evidence.era5_land_RH_pct - evidence.RH_IMPLIED_PCT).ge(20)
                       & evidence.RH_IMPLIED_PCT.lt(10)
                       & evidence.VPD_F_SOURCE.eq("EUF_F"))
    require(printed_flag.equals(calculated_flag),
            "Stage33 reviewed flags no longer match rule; stop")
    selected = evidence.loc[calculated_flag].copy()
    require(len(selected) == 27, "Expected exactly 27 selected QC1 events")
    require(selected.groupby(selected.index.year).size().to_dict() == EXPECTED,
            "Unexpected 2007/2008 QC1 distribution")
    require(pd.Timestamp("2007-05-17 13:00") in selected.index,
            "Critical May17 QC1 record unexpectedly absent")

    original = pd.read_csv(CSV, usecols=["time","TA_F","PA_F","VPD_F_SOURCE",
                                        "VPD_F_QC","RH_IMPLIED_PCT"],low_memory=False)
    original["time"] = pd.to_datetime(original.time, errors="raise")
    require(len(original)==332880 and original.time.is_unique, "RH25A CSV timeline changed")
    original = original.set_index("time").loc[selected.index]
    require((original.VPD_F_SOURCE == "EUF_F").all()
            and pd.to_numeric(original.VPD_F_QC,errors="coerce").eq(1).all(),
            "Source QC1 provenance changed")
    for key in ("TA_F","PA_F","RH_IMPLIED_PCT"):
        a = pd.to_numeric(original[key],errors="coerce").to_numpy(float)
        b = selected[key].to_numpy(float)
        require(np.isfinite(a).all() and np.allclose(a,b,rtol=0,atol=1e-5),
                f"Source CSV disagrees with Stage33 report: {key}")

    for model in ("era5", "era5_land"):
        for year in EXPECTED:
            idx = selected.index[selected.index.year == year]
            computed = model_rh(model, year, idx)
            from_evidence = selected.loc[idx, f"{model}_RH_pct"].to_numpy(float)
            require(np.allclose(computed,from_evidence,rtol=0,atol=1e-4),
                    f"Cached {model} {year} changed since Stage33")
    new_rh = selected["era5_land_RH_pct"].to_numpy(float)
    es_site_hpa = sat(selected.TA_F.to_numpy(float))
    pa_pa = selected.PA_F.to_numpy(float)*1000
    ea_pa = es_site_hpa*new_rh  # (hPa)*(percent) => Pa
    qnew = .622*ea_pa/(pa_pa-.378*ea_pa)
    require(np.isfinite(qnew).all() and ((qnew>0)&(qnew<0.08)).all(),
            "Nonphysical QBOT candidate")
    selected["QBOT_v6_kgkg"] = qnew
    selected["stage34_science_status"] = (
        "QC1_MDS_GAPFILL_REANALYSIS_SENSITIVITY_NOT_OBSERVATION_VALIDATED")
    return selected

def check_year(original, candidate, subset, year):
    with Dataset(original) as parent, Dataset(candidate) as new:
        axis = annual_axis(new, year)
        ix = axis.get_indexer(subset.index)
        require((ix>=0).all(), f"{year}: event timestamp not found")
        require(set(parent.variables) == set(new.variables),
                f"{year}: variable list changed")
        for name in parent.variables:
            if name != "QBOT":
                require(np.ma.allequal(parent[name][:],new[name][:]),
                        f"{year}: unrelated variable changed: {name}")
        p = np.asarray(parent["QBOT"][:,0,0], dtype=np.float32)
        q = np.asarray(new["QBOT"][:,0,0], dtype=np.float32)
        changed = set(np.flatnonzero(p != q))
        require(changed == set(ix), f"{year}: unexpected QBOT edits (expected {len(ix)}, got {len(changed)})")
        require(np.allclose(q[ix],subset.QBOT_v6_kgkg.to_numpy(float),
                            rtol=0,atol=1e-8),f"{year}: QBOT sensitivity mismatch")

def main(mode):
    selected = read_evidence()
    print("=== STAGE34 REVIEWED QC1 METEOROLOGY ===")
    print("QC1 candidate events:",len(selected))
    print("Years:", selected.groupby(selected.index.year).size().to_dict())
    print("QC0 observations changed: 0; other QC1 with no reference changed: 0")
    print("Source RH min:",float(selected.RH_IMPLIED_PCT.min()))
    print("Proposed RH min:",float(selected.era5_land_RH_pct.min()))
    crit = selected.loc[pd.Timestamp("2007-05-17 13:00")]
    print("2007-05-17 13:00 original RH / ERA5Land RH:",
          float(crit.RH_IMPLIED_PCT),"/",float(crit.era5_land_RH_pct))
    if mode=="audit":
        print("AUDIT ONLY. No forcing, CIME cases, or Slurm touched.")
        return
    if mode=="verify":
        require(V6.is_dir(),f"No completed Stage34 v6 directory: {V6}")
        meta=json.loads((V6/"stage34_manifest.json").read_text())
        require(meta.get("version")=="STAGE34_QC1_27ROW_SENSITIVITY_V6"
                and meta.get("modified_vs_v5")==27,"Invalid Stage34 manifest")
        for year in YEARS:
            f=V6/f"CH-Aws_DATM_{year}.nc"
            p=V5/f.name
            require(f.is_file(),f"Missing v6 forcing {year}")
            if year not in EXPECTED:
                require(f.is_symlink() and f.resolve()==p.resolve(),
                        f"Unchanged {year} not linked to v5 parent")
            else:
                require(not f.is_symlink(),f"{year}: modified annual file unexpectedly symlinked")
                subset=selected.loc[selected.index.year==year]
                check_year(p,f,subset,year)
                print(f"VERIFIED {year}: {len(subset)} QC1-only QBOT edits")
        print("VERIFY SUCCESS: exactly 27 QBOT changes vs v5; 17 annual symlinks preserved")
        return
    require(not V6.exists(),f"Stage34 v6 output already exists: {V6}")
    staging=Path(tempfile.mkdtemp(prefix=".CH_Aws_stage34_",dir=ROOT))
    try:
        ledger=staging/"stage34_27_QC1_sensitivity_ledger.csv"
        selected.to_csv(ledger,index_label="time",float_format="%.12g")
        original_sha={str(y):sha(V5/f"CH-Aws_DATM_{y}.nc") for y in EXPECTED}
        for year in YEARS:
            filename=f"CH-Aws_DATM_{year}.nc"
            parent=V5/filename
            target=staging/filename
            if year not in EXPECTED:
                target.symlink_to(parent)
                continue
            subset=selected.loc[selected.index.year==year]
            shutil.copy2(parent,target)
            with Dataset(parent) as old, Dataset(target,"r+") as new:
                axis=annual_axis(new,year)
                ix=axis.get_indexer(subset.index)
                require((ix>=0).all(),f"{year}: event timestamps missing")
                q_before=np.asarray(old["QBOT"][:,0,0],dtype=np.float32)
                t_old=np.asarray(old["TBOT"][ix,0,0],dtype=float)-273.15
                ps_old=np.asarray(old["PSRF"][ix,0,0],dtype=float)
                rh_old=100*(q_before[ix]*ps_old/(.622+.378*q_before[ix]))/(100*sat(t_old))
                require(np.allclose(rh_old,subset.RH_IMPLIED_PCT.to_numpy(float),
                                    rtol=0,atol=.05),
                        f"{year}: v5 humidity does not match QC1 source RH")
                new_q=np.asarray(new["QBOT"][:,0,0],dtype=np.float32)
                new_q[ix]=subset.QBOT_v6_kgkg.to_numpy(dtype=np.float32)
                new["QBOT"][:,0,0]=new_q
                new.setncattr("stage34_status","EXPLORATORY_QC1_REANALYSIS_SENSITIVITY")
                new.setncattr("stage34_parent_v5_sha256",original_sha[str(year)])
                new.setncattr("stage34_ledger_sha256",sha(ledger))
                new.setncattr("stage34_modified_QBOT_rows_vs_v5",int(len(subset)))
                new.setncattr("stage34_note","Only QC1 MDS gapfill humidity sensitivity; v5 variables and prior edits retained")
            check_year(parent,target,subset,year)
            print(f"VERIFIED WRITTEN {year}: {len(subset)} QC1-only QBOT edits")
        m={
            "site":"CH-Aws","version":"STAGE34_QC1_27ROW_SENSITIVITY_V6",
            "scientific_status":"EXPLORATORY_NOT_OBSERVATION_QC_APPROVED",
            "modified_vs_v5":27,"stage29_prior_QBOT_edits_vs_v3":77,
            "cumulative_candidate_QBOT_edits_vs_v3":104,
            "modified_years":EXPECTED,
            "reference_2007_2008_sha256":{
                f"{model}_{year}":sha(CACHE/f"{model}_{year}.json")
                for model in ("era5","era5_land") for year in EXPECTED
            },
            "parent_v5_modified_year_sha256":original_sha,
            "stage33_evidence_sha256":sha(EVIDENCE),
            "parent_RH25A_source_sha256":sha(CSV),
            "stage34_ledger_sha256":sha(ledger),
            "dependency":"17 annual v6 symlinks refer to v5; v5 may link to v3. Keep all parents.",
            "model_validation":"NONE; failed model RH29A is not evidence of success for v6"
        }
        (staging/"stage34_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
        os.rename(staging,V6)
        print("SUCCESS: independent Stage34 v6 overlay:",V6)
        print("Two independent 2007/2008 annual NetCDFs, 17 symlinks to v5")
        print("No v5/v4/v3 overwrites, NO new case, NO Slurm job.")
    finally:
        if staging.exists():
            shutil.rmtree(staging)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group()
    group.add_argument("--audit",action="store_true",help="Default; read-only")
    group.add_argument("--write",action="store_true",help="New output only")
    group.add_argument("--verify",action="store_true",help="Read-only compare v6 to v5")
    p.add_argument("--acknowledge-reanalysis-uncertainty",action="store_true")
    opt=p.parse_args()
    mode="write" if opt.write else "verify" if opt.verify else "audit"
    if mode=="write" and not opt.acknowledge_reanalysis_uncertainty:
        p.error("--write requires --acknowledge-reanalysis-uncertainty")
    main(mode)

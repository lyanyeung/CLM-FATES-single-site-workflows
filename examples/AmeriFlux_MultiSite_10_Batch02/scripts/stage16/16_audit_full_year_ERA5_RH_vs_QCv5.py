#!/usr/bin/env python3
"""Stage16: READ-ONLY annual ERA5 dewpoint RH vs Stage11 and tower meteo.

For the five pinned Stage15 one-year ERA5 products:
 * verify hashes, hourly UTC calendar, ERA variable units/grid, science markers
 * convert to native local-standard 30-minute tower timestamps
 * apply RH derived from internally consistent ERA5 2m T and dewpoint to the
   preserved tower temperature and pressure (diagnostic, NOT forcing)
 * compare historical Stage11 climatological RH/VPD proposals, flagged events,
   original tower RH and VPD stratified by official QC, and seasonal RH statistics
 * check US-ICh and US-ICt same-grid ERA5 data are not independent.

Only the four BIF-provided UTC offsets are metadata-supported. US-Ho1 -5 is
a PROVISIONAL assumption pending site-specific BADM. ERA is hourly: native
half-hour rows are INTERPOLATED SENSITIVITY values, not hourly observations.
No DATM, CASE, raw forcing, restart, netCDF or Slurm changes.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
import xarray as xr

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE15 = Path.home() / "AmeriFlux_Batch02_ERA5_five_one_year_controls"
STAGE11 = BASE / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
FOCUS = {"US-EML": (2009, -9), "US-GLE": (2005, -7),
         "US-Ho1": (1996, -5), "US-ICh": (2007, -9), "US-ICt": (2007, -9)}
PLAN_SHA = "0785bb8b85b5e8c9fee7b64d6f63016e58e12db03e31cf53c20e265e803f9523"

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def es(t):
    return 6.112 * np.exp(17.67 * t / (t + 243.5))  # hPa over water

def num(v):
    x = pd.to_numeric(v, errors="coerce")
    return x.mask((x <= -9990) | ~np.isfinite(x))

def timestamp(v):
    return pd.to_datetime(
        v.astype(str).str.strip().str.replace(r"\.0$", "", regex=True),
        format="%Y%m%d%H%M", errors="raise")

def verify_utc_offset(item, site, expected):
    source = Path(item["primary"])
    files = sorted(source.parent.glob("*_BIF_*.csv"))
    if site == "US-Ho1":
        if files:
            raise ValueError("US-Ho1 now has a BIF; inspect the actual UTC_OFFSET")
        return "PROVISIONAL_US_Ho1_MINUS_5_VERIFY_BADM"
    if len(files) != 1:
        raise ValueError(f"{site} must have exactly one release BIF")
    vals = []
    with files[0].open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row.get("VARIABLE", "")).strip().upper() == "UTC_OFFSET":
                if str(row.get("SITE_ID", "")).strip() not in ("", site):
                    raise ValueError("Wrong BIF site ID")
                vals.append(float(row["DATAVALUE"]))
    if len(vals) != 1 or vals[0] != expected:
        raise ValueError(f"{site} release BIF UTC_OFFSET differs from {expected}")
    return "RELEASE_BIF_UTC_OFFSET_CONFIRMED"

def era_read(path, receipt):
    with path.open("rb") as stream:
        if stream.read(8) != b"\x89HDF\r\n\x1a\n":
            raise ValueError("Expected extracted NetCDF4, not CDS ZIP")
    with xr.open_dataset(path, engine="netcdf4") as ds:
        if set(ds.data_vars) != {"t2m", "d2m", "sp"}:
            raise ValueError("Unexpected ERA5 variable list")
        for v, unit in (("t2m", "K"), ("d2m", "K"), ("sp", "Pa")):
            if ds[v].attrs.get("units") != unit or tuple(ds[v].dims) != ("valid_time",):
                raise ValueError(f"Unexpected ERA5 unit/dimension: {v}")
        times = pd.to_datetime(ds.valid_time.values, utc=True).tz_localize(None)
        ta = np.asarray(ds.t2m.values, float) - 273.15
        dew = np.asarray(ds.d2m.values, float) - 273.15
        pressure = np.asarray(ds.sp.values, float)
        lat = float(np.ravel(ds.latitude.values)[0])
        lon = float(np.ravel(ds.longitude.values)[0])
    start, end = receipt["requested_date"]
    expected = pd.date_range(start + " 00:00", end + " 23:00", freq="h")
    if not np.array_equal(times.values, expected.values) or len(times) != receipt["utc_hours"]:
        raise ValueError("ERA5 native UTC hours differ from verified receipt")
    if (lat, lon) != (receipt["grid_lat"], receipt["grid_lon"]):
        raise ValueError("ERA5 grid coordinate changed")
    with np.errstate(all="ignore"):
        rh = 100 * es(dew) / es(ta)
    if not (np.isfinite(rh) & (rh > 0) & (rh <= 100.05)).all():
        raise ValueError("Unexpected invalid ERA5 dewpoint RH")
    return pd.DataFrame({"utc": times, "ERA_T_C": ta, "ERA_Td_C": dew,
                         "ERA_P_Pa": pressure, "ERA_RH_water_pct": rh}), (lat, lon)

def native_year(primary, year):
    header = set(pd.read_csv(primary, nrows=0).columns)
    fields = ["TIMESTAMP_START", "TA_F", "PA_F", "VPD_F"]
    if not set(fields).issubset(header):
        raise ValueError("Missing original tower meteorology columns")
    fields += [x for x in ("TA_F_QC", "VPD_F_QC", "RH", "RH_QC") if x in header]
    a = pd.read_csv(primary, usecols=fields, dtype={"TIMESTAMP_START":str})
    a["local"] = timestamp(a.TIMESTAMP_START)
    a = a.loc[a.local.dt.year.eq(year)].copy()
    a = a.loc[~(a.local.dt.month.eq(2) & a.local.dt.day.eq(29))].copy()
    a.sort_values("local", inplace=True)
    if a.local.duplicated().any():
        raise ValueError("Duplicate tower local-standard timestamps")
    exp = pd.date_range(f"{year}-01-01", f"{year+1}-01-01", freq="30min", inclusive="left")
    exp = exp[~((exp.month == 2) & (exp.day == 29))]
    if len(exp) != 17520 or len(a) != 17520 or not np.array_equal(a.local.values, exp.values):
        raise ValueError("Site source year not complete NO_LEAP half-hour timeline")
    for k in fields[1:]: a[k] = num(a[k])
    for k in ("VPD_F_QC","TA_F_QC","RH","RH_QC"):
        if k not in a: a[k] = np.nan
    with np.errstate(all="ignore"):
        a["raw_vpd_RH_pct"] = 100 * (1 - a.VPD_F / es(a.TA_F))
    a["raw_vpd_RH_physically_valid"] = a.raw_vpd_RH_pct.gt(0) & a.raw_vpd_RH_pct.le(100.05)
    return a.reset_index(drop=True)

def compare(site, year, offset, era, tower, proposals):
    # Local clock offset is local_standard - UTC, from release BIF (US-Ho1 provisional).
    utc = tower.local - pd.Timedelta(hours=offset)
    x = (era.utc.astype("int64") // 10**9).to_numpy(float)
    xx = (utc.astype("int64") // 10**9).to_numpy(float)
    if (xx < x.min()).any() or (xx > x.max()).any():
        raise ValueError("ERA5 UTC buffer does not cover full tower local year")
    if era.utc.duplicated().any(): raise ValueError("Duplicate ERA UTC times")
    for name in ("ERA_T_C","ERA_Td_C","ERA_RH_water_pct","ERA_P_Pa"):
        tower[name] = np.interp(xx, x, era[name].to_numpy(float))
    tower["ERA_temporal_method"] = np.where(
        utc.dt.minute.eq(0), "ERA_EXACT_HOURLY", "ERA_HALF_HOURLY_LINEAR_INTERP_REVIEW")
    with np.errstate(all="ignore"):
        saturation = es(tower.TA_F.to_numpy(float))
        era_rh = tower.ERA_RH_water_pct.to_numpy(float)
        ea = saturation * era_rh/100
        vpd = saturation - ea
        pressure = tower.PA_F.to_numpy(float) * 1000
        q = .622 * ea * 100 / (pressure - .378 * ea * 100)
    tower["diagnostic_VPD_hPa"] = vpd
    tower["diagnostic_QBOT_kgkg"] = q
    tower["RH_at_site_T_valid"] = (
        np.isfinite(vpd) & (vpd >= -0.005) &
        np.isfinite(q) & (q > 0) & (q <= .08) &
        (era_rh > 0) & (era_rh <= 100.05))
    # Never clip negative (near-saturated) VPD or synthetic RH automatically.
    tower["site"] = site
    tower["year"] = year
    tower["UTC_offset_local_minus_UTC"] = offset
    pp = proposals.loc[proposals.site.eq(site)].copy()
    pp["local"] = pd.to_datetime(pp.time)
    pp = pp.loc[pp.local.dt.year.eq(year)].copy()
    if pp.local.duplicated().any():
        raise ValueError("Stage11 proposal duplicates")
    selected = ["local","decision","retained_TA_C","retained_PA_kPa",
                "proposed_VPD_hPa","donor_count"]
    pp = pp[selected]
    target = tower.merge(pp, on="local", how="inner", validate="one_to_one",
                         suffixes=("", "_stage11"))
    if len(target) != len(pp):
        raise ValueError("Stage11 target not exactly joined to tower source")
    if not np.isclose(target.TA_F.to_numpy(float),
                      target.retained_TA_C.to_numpy(float),
                      equal_nan=True, atol=1e-8).all():
        # Stage11 may retain QC-v5 adjusted T; expose the divergence, do not
        # silently use unprocessed original TA to make scientific approvals.
        print(f"CAUTION {site}: Stage11 retained TA differs from raw source TA at "
              f"{int((~np.isclose(target.TA_F, target.retained_TA_C, equal_nan=True)).sum())} rows")
    # Recompute the sensitivity candidate with exactly Stage11 *retained*
    # temperature/pressure, never substitute unreviewed source raw values.
    with np.errstate(all="ignore"):
        es_ = es(target.retained_TA_C.to_numpy(float))
        rh = target.ERA_RH_water_pct.to_numpy(float)
        ea_ = es_ * rh/100
        pressure_ = target.retained_PA_kPa.to_numpy(float)*1000
        vpd_ = es_-ea_
        q_ = .622*ea_*100/(pressure_-.378*ea_*100)
    target["ERA_RH_at_stage11_T_VPD_hPa"] = vpd_
    target["ERA_RH_at_stage11_T_QBOT_kgkg"] = q_
    target["ERA_stage11_retained_T_valid"] = (
        np.isfinite(vpd_)&(vpd_>=-0.005)&np.isfinite(q_)&(q_>0)&(q_<=.08))
    target["Stage11_minus_ERA_RH_VPD_hPa"] = target.proposed_VPD_hPa-vpd_
    target["Stage11_minus_ERA_RH_pct"] = (
        100 * (1-target.proposed_VPD_hPa/es_) - rh)
    return tower, target

def summarize(site, year, timezone_source, grid, a, target):
    qc0 = a.VPD_F_QC.eq(0)&a.TA_F_QC.eq(0)&a.raw_vpd_RH_physically_valid
    if not qc0.any():
        # Do not call mixed- or unknown-QC VPD "measured".
        measured_mae = None
    else:
        measured_mae = float((a.loc[qc0, "raw_vpd_RH_pct"] -
                              a.loc[qc0,"ERA_RH_water_pct"]).abs().median())
    candidates = target.decision.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED")
    delta=(target.loc[candidates, "Stage11_minus_ERA_RH_VPD_hPa"]).abs()
    monthly = a.groupby(a.local.dt.month).agg(
        record_count=("local", "size"),
        ERA_RH_min_pct=("ERA_RH_water_pct", "min"),
        ERA_RH_median_pct=("ERA_RH_water_pct", "median"),
        ERA_RH_lt5=("ERA_RH_water_pct", lambda s: int(s.lt(5).sum())),
        ERA_RH_lt15=("ERA_RH_water_pct", lambda s: int(s.lt(15).sum())),
        diagnostic_invalid=("RH_at_site_T_valid", lambda s: int((~s).sum()))
    ).reset_index().rename(columns={"local":"month"})
    monthly.insert(0,"site",site)
    result=dict(site=site,focus_year=year,UTC_offset_source=timezone_source,
        ERA_grid_lat=grid[0],ERA_grid_lon=grid[1],
        native_noleap_rows=len(a),ERA_exact_hours=int(a.ERA_temporal_method.eq("ERA_EXACT_HOURLY").sum()),
        ERA_interpolated_halfhours=int(a.ERA_temporal_method.str.startswith("ERA_HALF").sum()),
        ERA_RH_min=float(a.ERA_RH_water_pct.min()),
        ERA_RH_lt5=int(a.ERA_RH_water_pct.lt(5).sum()),
        ERA_RH_lt15=int(a.ERA_RH_water_pct.lt(15).sum()),
        diagnostic_Tbot_Qbot_invalid=int((~a.RH_at_site_T_valid).sum()),
        original_QC0_VPD_and_T_n=int(qc0.sum()),
        QC0_VPDderived_RH_median_abs_diff_to_ERA_pct=measured_mae,
        year_stage11_targets=len(target),
        year_stage11_provisional=int(candidates.sum()),
        year_stage11_holds=int((~candidates).sum()),
        stage11_provisional_minus_ERA_RH_abs_VPD_median_hPa=(
            float(delta.median()) if len(delta) else None),
        stage11_provisional_minus_ERA_RH_abs_VPD_max_hPa=(
            float(delta.max()) if len(delta) else None),
        stage11_target_ERA_reconstruction_invalid=int((~target.ERA_stage11_retained_T_valid).sum()),
        status="ONE_YEAR_DIAGNOSTIC_REVIEW_ONLY_NO_DATM")
    return result,monthly

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage15-root",type=Path,default=STAGE15)
    p.add_argument("--stage11-root",type=Path,default=STAGE11)
    p.add_argument("--write-report",action="store_true")
    p.add_argument("--output-root",type=Path)
    args=p.parse_args()
    old=args.stage15_root.expanduser().resolve()
    stage11=args.stage11_root.expanduser().resolve()
    if not (old/"STAGE15_PARTIAL_OR_COMPLETE_REVIEW_ONLY").is_file():
        raise ValueError("Stage15 source is not marked review-only")
    config=json.loads((old/"config.json").read_text())
    if config.get("stage13_plan_sha256")!=PLAN_SHA or config.get("focus_years")!={s:y for s,(y,_) in FOCUS.items()}:
        raise ValueError("Stage15 plan or year choices differ")
    if not (stage11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage11 scientific approval still required")
    m11=json.loads((stage11/"manifest.json").read_text())
    if m11.get("scientific_status")!="HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Unanticipated Stage11 approval scope")
    stage08=Path(m11["source_stage08"])
    m08=json.loads((stage08/"exact_input_manifest.json").read_text())
    source={x["site"]:x for x in m08["sites"]}
    pp_path=stage11/"cold_humidity_repair_proposals.csv"
    proposal=pd.read_csv(pp_path)
    if len(proposal)!=4884 or set(proposal.site)!=set(FOCUS):
        raise ValueError("Stage11 proposal scope mismatch")
    pins={str(pp_path):sha(pp_path),str(stage11/"manifest.json"):sha(stage11/"manifest.json"),
          str(old/"config.json"):sha(old/"config.json")}
    annual=[];monthly_all=[];event_all=[];griddata={}
    for site,(year,offset) in FOCUS.items():
        item=source[site]
        timezone_source=verify_utc_offset(item,site,offset)
        primary=Path(item["primary"]).resolve()
        if m11["input_hashes"].get(str(primary))!=sha(primary):
            raise ValueError("Pinned original source changed: "+site)
        pins[str(primary)]=sha(primary)
        receiptpath=old/f"{site}_{year}"/"verified_receipt.json"
        receipt=json.loads(receiptpath.read_text())
        if receipt["site"]!=site or receipt["year"]!=year or receipt["stage13_plan_sha256"]!=PLAN_SHA:
            raise ValueError("Unexpected Stage15 site receipt")
        nc=Path(receipt["netcdf_path"]).resolve()
        if old not in nc.parents or sha(nc)!=receipt["netcdf_sha256"]:
            raise ValueError("Missing/modified ERA5 NetCDF: "+site)
        payload=Path(receipt["original_payload_path"]).resolve()
        if old not in payload.parents or sha(payload)!=receipt["original_payload_sha256"]:
            raise ValueError("Missing/modified CDS payload: "+site)
        pins[str(nc)]=receipt["netcdf_sha256"]
        pins[str(payload)]=receipt["original_payload_sha256"]
        pins[str(receiptpath)]=sha(receiptpath)
        e,grid=era_read(nc,receipt)
        griddata[site]=(e,grid)
        tower=native_year(primary,year)
        a,targets=compare(site,year,offset,e,tower,proposal)
        stats,monthly=summarize(site,year,timezone_source,grid,a,targets)
        annual.append(stats)
        monthly_all.append(monthly)
        event_all.append(targets)
        print("STAGE16",site,year,"full-year=",len(a),
              "Stage11 targets=",len(targets),
              "provisional=",stats["year_stage11_provisional"],
              "holds=",stats["year_stage11_holds"],
              "ERA-rh-invalid-at-retained-T=",stats["stage11_target_ERA_reconstruction_invalid"],
              "QC0_T+VPD=",stats["original_QC0_VPD_and_T_n"],
              "tz=",timezone_source,flush=True)
    first,ga=griddata["US-ICh"]
    second,gb=griddata["US-ICt"]
    same=(ga==gb and
          np.array_equal(first.utc.values,second.utc.values) and
          all(np.array_equal(first[col].values,second[col].values)
              for col in ["ERA_T_C","ERA_Td_C","ERA_P_Pa"]))
    print("US-ICh / US-ICt SAME EXACT ERA5 GRID AND YEAR:",same,flush=True)
    if ga==gb and not same:
        raise ValueError("Same ERA5 grid requested but downloaded values differ")
    hold_sum=sum(r["year_stage11_holds"] for r in annual)
    print("STAGE16 SUMMARY:",len(annual),"/5 annual ERA comparisons; "
          "US-ICh and US-ICt are NOT independent ERA5 grid samples.")
    print("YEARLY STAGE11 REMAINING HOLDS:",hold_sum,"(all-year subset; not all 14 by definition)")
    print(pd.DataFrame(annual).to_string(index=False))
    if any(sha(p)!=v for p,v in pins.items()):
        raise ValueError("Input hash changed during audit")
    if not args.write_report:
        print("STAGE16 CHECK ONLY: no files written")
        return 0
    out=args.output_root.expanduser().resolve() if args.output_root else (
        Path.home()/("AmeriFlux_Batch02_stage16_yearly_dewpoint_"+
                     datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]))
    if out.exists() or any(out==r or out in r.parents or r in out.parents for r in (old,stage11,BASE)):
        raise ValueError("Existing or unsafe Stage16 output")
    out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(annual).to_csv(out/"five_yearly_site_summary.csv",index=False)
    pd.concat(monthly_all,ignore_index=True).to_csv(out/"monthly_ERA_RH_diagnostics.csv",index=False)
    pd.concat(event_all,ignore_index=True).to_csv(out/"focus_year_Stage11_vs_ERA_dewpoint.csv",index=False)
    (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Annual ERA5 RH cross-audit only; no humid forcing, time-zone or science approval.\n")
    (out/"manifest.json").write_text(json.dumps(dict(
        source_sha256=pins,script_sha256=sha(Path(__file__)),
        stage15_root=str(old),stage11_root=str(stage11),
        official_UTC_offsets_except_Ho1={s:o for s,(_,o) in FOCUS.items() if s!="US-Ho1"},
        US_Ho1_offset_status="PROVISIONAL_BADM_NOT_VERIFIED",
        ERA5_ICh_and_ICt_not_independent=same,
        scientific_status="ANNUAL_NUMERICAL_DIAGNOSTICS_ONLY",
        no_source_model_slurm_modifications=True
        ),indent=2)+"\n")
    print("STAGE16 REPORT:",out,flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Batch02 Stage13e: READ-ONLY ERA5 dewpoint vs Stage11 pilot-event audit.

Compare the previously downloaded six ERA5 windows (one US-EML, five other
windows), including ALL fourteen Stage11 HOLD records. Site UTC offsets are
HYPOTHESES pending official BADM UTC_OFFSET verification. Half-hour values are
LINEARLY INTERPOLATED FOR SENSITIVITY ONLY (ERA5 product is hourly UTC).
No approved humidity, forcing, DATM, CIME or Slurm changes are made.
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

BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE11 = BASE / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
FOUR = Path.home() / "AmeriFlux_Batch02_ERA5_four_site_pilots_20261022T025435Z_66ba30af"
EML = Path.home() / "AmeriFlux_Batch02_ERA5_dewpoint_pilot" / "US-EML_ERA5_20090101_20090108_extracted"
# Provisional site STANDARD offsets (tower local standard time - UTC).
# These must be checked against site-specific BADM UTC_OFFSET, not inferred
# from geography, DST practices, or RMSE alone.
UTC_OFFSET_HYPOTHESIS = {
    "US-EML": -9, "US-GLE": -7, "US-Ho1": -5,
    "US-ICh": -9, "US-ICt": -9,
}
EXPECTED = {
    ("US-EML", "winter_2009"): ("2009-01-01", "2009-01-08", 192),
    ("US-GLE", "winter_2005"): ("2005-12-05", "2005-12-09", 120),
    ("US-Ho1", "winter_1996"): ("1996-12-25", "1996-12-29", 120),
    ("US-ICh", "winter_2007"): ("2007-02-19", "2007-03-02", 288),
    ("US-ICt", "winter_2007_jan"): ("2006-12-31", "2007-01-04", 120),
    ("US-ICt", "mild_2007_dec"): ("2007-11-30", "2007-12-04", 120),
}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def sat(t):
    return 6.112*np.exp(17.67*t/(t+243.5))  # hPa, water convention for QC-v5 consistency

def load_nc(path, start, end, count):
    with Path(path).open("rb") as f:
        if f.read(8) != b"\x89HDF\r\n\x1a\n":
            raise ValueError("Expected extracted NetCDF4/HDF5: "+str(path))
    with xr.open_dataset(path, engine="netcdf4") as d:
        if set(d.data_vars) != {"t2m","d2m","sp"} or "valid_time" not in d:
            raise ValueError("Wrong ERA5 pilot schema")
        if any(tuple(d[v].dims) != ("valid_time",) for v in ("t2m","d2m","sp")):
            raise ValueError("Point-series expected, not ERA5 grid")
        for var, unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if d[var].attrs.get("units") != unit:
                raise ValueError("Unexpected units: "+var)
        ts=pd.to_datetime(d.valid_time.values,utc=True).tz_localize(None)
        t=d.t2m.values.astype(float)-273.15
        td=d.d2m.values.astype(float)-273.15
        p=d.sp.values.astype(float)
        lat=float(np.ravel(d.latitude.values)[0])
        lon=float(np.ravel(d.longitude.values)[0])
    expected=pd.date_range(start+"T00:00",end+"T23:00",freq="h")
    if len(ts)!=count or not np.array_equal(ts.values,expected.values):
        raise ValueError("Unexpected pilot UTC chronology")
    if not (np.isfinite(t).all() and np.isfinite(td).all()
            and np.isfinite(p).all() and ((t > -90)&(t<60)).all()
            and ((td>-100)&(td<60)).all() and ((p>49000)&(p<111000)).all()):
        raise ValueError("Invalid ERA5 physical variables")
    with np.errstate(all="ignore"):
        ea=sat(td)
        rh=100*ea/sat(t)
    if not (np.isfinite(rh).all() and (rh>0).all() and (rh<=100.05).all()):
        raise ValueError("Pilot ERA RH outside physical range")
    return pd.DataFrame(dict(utc=ts,era_t_C=t,era_td_C=td,
                             era_p_Pa=p,era_ea_hPa=ea,era_RH_pct=rh)), (lat,lon)

def sample_pilot(frame, target_utc):
    """Interpolate T/RH/ea only between bracketing ERA hours, never extrapolate."""
    xp=frame.utc.to_numpy(dtype="datetime64[ns]").astype("int64")
    x=target_utc.to_numpy(dtype="datetime64[ns]").astype("int64")
    good=(x>=xp[0]) & (x<=xp[-1])
    result={}
    for col in ["era_t_C","era_td_C","era_p_Pa","era_ea_hPa","era_RH_pct"]:
        vals=np.full(len(x),np.nan)
        vals[good]=np.interp(x[good].astype(float),xp.astype(float),
                             frame[col].to_numpy(float))
        result[col]=vals
    return good,result

def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--four-root",type=Path,default=FOUR)
    arg.add_argument("--stage11-root",type=Path,default=STAGE11)
    arg.add_argument("--eml-pilot",type=Path)
    arg.add_argument("--write-report",action="store_true")
    arg.add_argument("--output-root",type=Path)
    args=arg.parse_args()
    s11=args.stage11_root.expanduser().resolve()
    four=args.four_root.expanduser().resolve()
    if not (s11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage11 unapproved source marker not found")
    sm=json.loads((s11/"manifest.json").read_text())
    if sm["n_target_rows"]!=4884 or sm["scientific_status"]!="HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Stage11 science status/scope mismatch")
    stage11_csv=s11/"cold_humidity_repair_proposals.csv"
    rows=pd.read_csv(stage11_csv)
    if len(rows)!=4884 or rows.duplicated(["site","time"]).any():
        raise ValueError("Stage11 row identity changed")
    rows["local_standard"]=pd.to_datetime(rows.time)
    if rows.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE").sum()!=14:
        raise ValueError("Expected precisely 14 original residual HOLD records")
    if not (four/"COMPLETE_PILOT_DATA_NOT_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Four-site CDS pilots were not finalized")
    fm=json.loads((four/"manifest.json").read_text())
    manifests=fm["pilot_windows"]
    if len(manifests)!=5 or {(r["site"],r["event"]) for r in manifests}!=set(EXPECTED)-{("US-EML","winter_2009")}:
        raise ValueError("Four-site manifest windows differ")
    if fm["science_status"]!="PILOT_DIAGNOSTIC_ONLY_HUMIDITY_NOT_APPROVED":
        raise ValueError("CDS pilot science-status differs")
    eml_nc=([args.eml_pilot.expanduser().resolve()] if args.eml_pilot else
            sorted(EML.glob("*.nc")))
    if len(eml_nc)!=1:
        raise ValueError("Expected one Stage13b US-EML extracted .nc")
    pins={str(p):sha(p) for p in (stage11_csv,s11/"manifest.json",four/"manifest.json")}
    sources={("US-EML","winter_2009"):eml_nc[0]}
    for entry in manifests:
        p=Path(entry["netcdf_path"]).resolve()
        if four not in p.parents or not p.is_file() or sha(p)!=entry["netcdf_sha256"]:
            raise ValueError("Pilot NetCDF missing/outside run/changed: "+str(p))
        sources[(entry["site"],entry["event"])]=p
        pins[str(p)]=entry["netcdf_sha256"]
    pins[str(eml_nc[0])]=sha(eml_nc[0])
    outrows=[]
    summary=[]
    grid=[]
    for (site,event),(start,end,expected_hours) in EXPECTED.items():
        nc=sources[(site,event)]
        pilot,point=load_nc(nc,start,end,expected_hours)
        grid.append(dict(site=site,event=event,lat=point[0],lon=point[1]))
        offset=UTC_OFFSET_HYPOTHESIS[site]
        one=rows.loc[rows.site.eq(site)].copy()
        sample_counts={}
        for delta in (-1,0,1):
            trial_offset=offset+delta
            target_utc=one.local_standard-pd.Timedelta(hours=trial_offset)
            present,fields=sample_pilot(pilot,target_utc)
            subset=one.loc[present].copy()
            for k,v in fields.items(): subset[k]=v[present]
            subset["site_utc_offset_hypothesis"]=trial_offset
            subset["is_nominal_offset"]=delta==0
            subset["event"]=event
            subset["pilot_utc_start"]=start
            subset["pilot_utc_end"]=end
            subset["era_grid_lat"]=point[0]
            subset["era_grid_lon"]=point[1]
            subset["utc"]=target_utc.loc[present].to_numpy()
            subset["temporal_method"]=np.where(
                subset.utc.dt.minute.eq(0),
                "EXACT_ERA_HOURLY", "INTERPOLATED_BETWEEN_ERA_HOURS_REVIEW")
            with np.errstate(all="ignore"):
                es=sat(subset.retained_TA_C.to_numpy(float))
                rh=subset.era_RH_pct.to_numpy(float)
                pressure=subset.retained_PA_kPa.to_numpy(float)*1000
                eap=es*rh/100
                vpd=es-eap
                q=.622*eap*100/(pressure-.378*eap*100)
                direct_ea=subset.era_ea_hPa.to_numpy(float)
                direct_vpd=es-direct_ea
            subset["RH_preserving_VPD_hPa"]=vpd
            subset["RH_preserving_QBOT_kgkg"]=q
            subset["RH_preserving_numeric_valid"]=(
                np.isfinite(vpd)&(vpd>=0)&np.isfinite(q)&(q>0)&(q<=.08)&
                (rh>0)&(rh<=100.05))
            subset["direct_ERA_ea_at_tower_T_VPD_hPa"]=direct_vpd
            subset["direct_ERA_ea_supersaturation_at_tower_T"]=direct_vpd<-.005
            subset["stage11_minus_dewpoint_RH_preserving_VPD_hPa"]=(
                subset.proposed_VPD_hPa-subset.RH_preserving_VPD_hPa)
            outrows.append(subset)
            sample_counts[trial_offset]=len(subset)
            if delta==0:
                held=subset.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE")
                summary.append(dict(site=site,event=event,
                    grid_lat=point[0],grid_lon=point[1],
                    n_utc_hours=len(pilot),n_target_overlap=len(subset),
                    nominal_UTC_offset_hours=offset,
                    n_exact_ERA_hour=int(subset.temporal_method.eq("EXACT_ERA_HOURLY").sum()),
                    n_interpolated=int(subset.temporal_method.str.startswith("INTERPOLATED").sum()),
                    matched_original_holds=int(held.sum()),
                    holds_with_numeric_RH_candidate=int((held&subset.RH_preserving_numeric_valid).sum()),
                    direct_dewpoint_ea_supersaturation_count=int(
                        subset.direct_ERA_ea_supersaturation_at_tower_T.sum()),
                    RH_preserving_invalid_count=int((~subset.RH_preserving_numeric_valid).sum())))
        print(f"PILOT {site} {event}: grid={point}, overlap={summary[-1]['n_target_overlap']}, "
              f"original_HOLD={summary[-1]['matched_original_holds']}, "
              f"RH_reconstructed={summary[-1]['holds_with_numeric_RH_candidate']}, "
              f"offset tests={sample_counts}",flush=True)
    allrows=pd.concat(outrows,ignore_index=True)
    nom=allrows.loc[allrows.is_nominal_offset].copy()
    if nom.duplicated(["site","time"]).any():
        raise ValueError("Pilot windows overlap same Stage11 timestamp")
    holds=nom.loc[nom.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE")].copy()
    if len(holds)!=14:
        raise ValueError(f"Expected all 14 original HOLD records in pilot windows, got {len(holds)}")
    bad=holds.loc[~holds.RH_preserving_numeric_valid]
    print("\nSTAGE13e SUMMARY: 6 ERA5 windows, 960 UTC hours, "
          "14/14 original HOLD rows covered")
    print("HOLD with numerically physical RH-preserving VPD/QBOT:",
          len(holds)-len(bad),"/14")
    print("HOLD with direct ERA vapor pressure supersaturation at retained tower T:",
          int(holds.direct_ERA_ea_supersaturation_at_tower_T.sum()))
    print("\nORIGINAL 14 HOLDS, NOMINAL UNVERIFIED OFFSETS")
    show=["site","time","event","site_utc_offset_hypothesis","temporal_method",
          "retained_TA_C","era_t_C","era_td_C","era_RH_pct",
          "RH_preserving_VPD_hPa","RH_preserving_QBOT_kgkg",
          "direct_ERA_ea_at_tower_T_VPD_hPa","RH_preserving_numeric_valid"]
    print(holds[show].to_string(index=False))
    print("\nPER-WINDOW SUMMARY")
    print(pd.DataFrame(summary).to_string(index=False))
    g=pd.DataFrame(grid)
    near=g.loc[g.site.isin(["US-ICh","US-ICt"])]
    if len(set(zip(near.lat,near.lon)))==1:
        print("GRID WARNING: US-ICh and US-ICt share the same 0.25-degree ERA5 grid point.")
    else:
        print("GRID CHECK: US-ICh and US-ICt are on distinct ERA5 grid points.")
    print("IMPORTANT: Time offsets are hypotheses pending release BADM UTC_OFFSET; "
          "half-hour data were interpolated for DIAGNOSIS only.")
    changed=[k for k,v in pins.items() if sha(k)!=v]
    if changed: raise ValueError("Source SHA256 changed during comparison")
    if not args.write_report:
        print("CHECK ONLY: no files written")
        return 0
    dest=(args.output_root.expanduser().resolve() if args.output_root else
          Path.home()/("AmeriFlux_Batch02_stage13e_comparison_"+
                       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
                       "_"+uuid4().hex[:8]))
    protected=[s11,four,eml_nc[0].parent,BASE]
    if dest.exists() or any(dest==p or dest in p.parents or p in dest.parents for p in protected):
        raise ValueError("Output destination inside protected input trees or exists")
    dest.mkdir(parents=True,exist_ok=False)
    nom.to_csv(dest/"nominal_offset_pilot_comparison.csv",index=False)
    allrows.loc[~allrows.is_nominal_offset].to_csv(
        dest/"alternative_offsets_sensitivity.csv",index=False)
    holds[show].to_csv(dest/"14_original_holds_ERA_dewpoint.csv",index=False)
    pd.DataFrame(summary).to_csv(dest/"six_window_summary.csv",index=False)
    pd.DataFrame(grid).to_csv(dest/"ERA5_grid_locations.csv",index=False)
    (dest/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Only exploratory humidity comparisons; no time-zone or forcing approval.\n")
    (dest/"manifest.json").write_text(json.dumps(dict(
        source_sha256=pins,script_sha256=sha(Path(__file__)),
        hypothesised_UTC_offsets=UTC_OFFSET_HYPOTHESIS,
        original_holds_covered=len(holds),
        noleap_forcing_approved=False,scientific_status="COMPARISON_ONLY",
        native_HH_interpolation="for sensitivity, not model forcing",
        no_slurm_model_case_or_raw_changes=True),indent=2)+"\n")
    print("STAGE13e REPORT:",dest,flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

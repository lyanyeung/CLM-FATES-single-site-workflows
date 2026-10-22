#!/usr/bin/env python3
"""Batch03 Stage08e: pin raw alternatives at 1924 winter VPD blockers.

Read-only --check, report-only --run. Finds potentially useful same-release
meteorological fields without treating gap-filled or ERA values as independent
evidence. Generates external-data acquisition needs without assuming the
FLUXNET timestamp convention is UTC. Does not repair any forcing.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
STAGE07 = ROOT / "qcv5_native_trial_20261022T024559Z_36c46e58"
STAGE08 = ROOT / "raw_RH_sensitivity_20261022T025645Z_3c43eb8b"
STAGE08C = ROOT / "reports/stage08c_era_humidity_20261022T031437Z_512e8731"
STAGE08D = ROOT / "reports/stage08d_vpd_provenance_20261022T031928Z_21f52e9c"
BLOCKS = {"US-Kon":229, "US-MMS":18, "US-Me2":4, "US-Me6":1,
          "US-MtB":15, "US-NR1":173, "US-NR3":1484}
COORD = {
    "US-Kon":(39.0824,-96.5603), "US-MMS":(39.3232,-86.4131),
    "US-Me2":(44.4526,-121.5589), "US-Me6":(44.3233,-121.6078),
    "US-MtB":(32.4160,-110.7256), "US-NR1":(40.0329,-105.5464),
    "US-NR3":(40.0520,-105.5864)}
MATCH_ALT = re.compile(r"^(?:RH(?:_|$)|VPD(?:_|$)|TA(?:_|$)|TD(?:_|$)|TDEW(?:_|$)|DEW(?:_|$)|H2O(?:_|$)|Q(?:_|$)|SH(?:_|$)|EA(?:_|$)|VP(?:_|$))",re.I)
CANDIDATE = ("RH","RH_QC","RH_F","RH_F_QC","VPD","VPD_QC",
             "VPD_F_MDS","VPD_F_MDS_QC","VPD_ERA","TA_F_MDS",
             "TA_F_MDS_QC","TD","TDEW","TDEW_F","H2O",
             "H2O_F","Q","SH","EA","VP")


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1048576),b""):
            h.update(part)
    return h.hexdigest()


def numeric(value):
    try:
        v=float(value)
        return v if np.isfinite(v) and v > -9990 else np.nan
    except (TypeError,ValueError):
        return np.nan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=parser.parse_args()
    for p in (ROOT,STAGE07,STAGE08,STAGE08C,STAGE08D):
        if not p.is_dir() or p.is_symlink():
            raise ValueError("Missing/unsafe source: "+str(p))
    if not (STAGE07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage07 incomplete marker missing")
    if not (STAGE08/"INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").is_file():
        raise ValueError("Stage08 incomplete marker missing")
    stage08d=json.loads((STAGE08D/"provenance.json").read_text(encoding="utf-8"))
    stage08c_file=STAGE08C/"era_humidity_residual_details.csv"
    if (Path(stage08d["source_evidence"]).resolve()!=STAGE08C
            or sha(stage08c_file)!=stage08d["stage08c_details_sha256"]
            or sha(STAGE08C/"evidence_scope.json")!=stage08d["stage08c_scope_sha256"]):
        raise ValueError("Stage08c/08d lineage or data changed")
    original=pd.read_csv(stage08c_file,dtype=str,keep_default_na=False)
    if len(original)!=1924 or set(original.site)!=set(BLOCKS):
        raise ValueError("Unexpected Stage08c residual records")
    req={"source_csv_row","time","site","rejection_primary_reason"}
    if not req.issubset(original.columns):
        raise ValueError("Stage08c source-row fields missing")
    if not original.rejection_primary_reason.eq("ERA_RH_BELOW_MINUS2_PCT").all():
        raise ValueError("Unexpected blocker type")
    old07=json.loads((STAGE07/"exact_input_manifest.json").read_text(encoding="utf-8"))
    records={row["site"]:row for row in old07["sites"]}
    if not set(BLOCKS).issubset(records):
        raise ValueError("Stage07 site manifest incompatible")
    pinned=old07["input_sha256"]
    availability=[]
    detailed=[]
    acquisitions=[]
    for site, expected in BLOCKS.items():
        src=original[original.site.eq(site)].copy()
        if len(src)!=expected or src.source_csv_row.duplicated().any():
            raise ValueError("Residual source row duplicates/counts: "+site)
        raw=Path(records[site]["primary"]).resolve()
        if (raw.parent.name!=records[site]["release"] or raw.parent.parent.name!="raw"
                or raw.parents[3].name!=site or str(raw) not in pinned):
            raise ValueError("Raw product provenance differs: "+site)
        print("RAW SHA256 CHECK",site,raw.name,flush=True)
        if sha(raw)!=pinned[str(raw)]:
            raise ValueError("Primary raw file changed: "+site)
        header=list(pd.read_csv(raw,nrows=0).columns)
        for name in ("TIMESTAMP_START","TA_F","VPD_F","VPD_F_QC"):
            if name not in header: raise ValueError("Missing expected column "+name+" for "+site)
        candidates=[v for v in header if MATCH_ALT.search(v)]
        output_columns=list(dict.fromkeys(["TIMESTAMP_START","TA_F","VPD_F","VPD_F_QC"] + candidates))
        selected_rows={int(row.source_csv_row):row for row in src.itertuples(index=False)}
        found={}
        offset=0
        for chunk in pd.read_csv(raw,usecols=output_columns,dtype="string",
                                 chunksize=100000,keep_default_na=False):
            count=len(chunk)
            needed=[rid for rid in selected_rows if offset+2<=rid<offset+count+2]
            for rid in needed:
                j=rid-2-offset
                observed=chunk.iloc[j]
                expected_row=selected_rows[rid]
                stamp=str(observed["TIMESTAMP_START"]).strip().removesuffix(".0")
                parsed=pd.to_datetime(stamp,format="%Y%m%d%H%M",errors="raise")
                if parsed!=pd.Timestamp(expected_row.time):
                    raise ValueError("Raw timestamp/Stage08c original row mismatch: "+site+" "+str(rid))
                item={"site":site,"source_csv_row":rid,"time":expected_row.time,
                      "VPD_F_QC":numeric(observed["VPD_F_QC"]),
                      "TA_F":numeric(observed["TA_F"]),
                      "VPD_F":numeric(observed["VPD_F"])}
                for col in candidates:
                    item[col]=numeric(observed[col])
                found[rid]=item
            offset+=count
        if len(found)!=len(src):
            raise ValueError("Not all blocked timestamps found in pinned raw file: "+site)
        rows=[found[rid] for rid in sorted(found)]
        detailed.extend(rows)
        for col in candidates:
            valid=sum(int(np.isfinite(row.get(col,np.nan))) for row in rows)
            if col not in ("TA_F","VPD_F","VPD_F_QC"):
                availability.append({"site":site,"column":col,
                    "valid_at_blockers":valid,"missing_at_blockers":len(rows)-valid,
                    "total_blockers":len(rows),
                    "note":"Same-release variable only; not independent quality evidence"})
        alt=[(c,sum(int(np.isfinite(r.get(c,np.nan))) for r in rows))
             for c in CANDIDATE if c in candidates and c not in ("VPD_ERA",)]
        alt=[(c,n) for c,n in alt if n>0]
        print("ALTERNATIVES:",site,"raw_cols=",len(header),
              "present_valid_counts=",alt,flush=True)
        site_times=pd.to_datetime(src.time)
        for year,n in site_times.dt.year.value_counts().sort_index().items():
            lat,lon=COORD[site]
            acquisitions.append({"site":site,"year":int(year),
                "blocked_native_rows":int(n),"latitude":lat,"longitude":lon,
                "native_minutes":int(records[site]["native_minutes"]),
                "source_clock_basis":"UNVERIFIED_FLUXNET_LOCAL_TIME_DO_NOT_ASSUME_UTC",
                "possible_external_variables":"2m_temperature_K;2m_dewpoint_temperature_K;surface_pressure_Pa",
                "possible_provider":"Copernicus ERA5-Land timeseries (ERA5-driven; not independent)",
                "mandatory_before_alignment":"verify local standard time, UTC offset, DST policy and elevation"})
    df=pd.DataFrame(availability)
    print("\nSTAGE08E RAW ALTERNATIVE AVAILABILITY:")
    if len(df):
        print(df.pivot_table(index="site",columns="column",
            values="valid_at_blockers",aggfunc="first",fill_value=0).to_string())
    else:
        print("No additional humidity field available")
    print("\nSTAGE08E PREFLIGHT: 7/7 raw source SHA256 pinned; 1924/1924 records matched; no data replaced")
    if args.check:
        print("CHECK ONLY: no output files created")
        return 0
    out=ROOT/"reports"/("stage08e_alternatives_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    df.to_csv(out/"raw_alternative_field_availability.csv",index=False)
    pd.DataFrame(detailed).to_csv(out/"raw_alternatives_at_blockers.csv",index=False)
    pd.DataFrame(acquisitions).to_csv(out/"external_humidity_acquisition_years.csv",index=False)
    (out/"evidence_policy.json").write_text(json.dumps({
      "stage08d_report":str(STAGE08D),
      "stage08c_sha256":sha(stage08c_file),
      "records":1924,
      "scope":"Read-only raw variable inventory and external acquisition planning",
      "limitations":[
        "No alternate humidity value is validated for replacement.",
        "QC2 is a downscaled ERA-filled product; paired ERA5 is not an independent control.",
        "ERA5-Land atmospheric forcing also inherits ERA5; dewpoint can help rederive physically consistent humidity but is not fully independent.",
        "FLUXNET source timestamps must be mapped to UTC before joining externally downloaded hourly data.",
        "Tower observation measurement heights can differ from the gridded 2m temperature/dewpoint.",
        "Native HR remains 60 minutes at US-MMS; all other native products retain 30 minutes.",
        "Stage07 and Stage08 incomplete marks are retained. Do not submit DATM/spinup jobs."
      ]},indent=2)+"\n",encoding="utf-8")
    print("STAGE08E SUMMARY: 1924/1924 pinned raw rows audited; report_only=True")
    print("REPORT DIR:",out)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stage34 read-only scientific audit: US-Ho1 QC2 temperature provenance.

Diagnose 425 negative dewpoint-transfer VPD events within the 917 held
Stage19 cases, relative to FLUXNET embedded ERA temperature and independent
CDS ERA5 T/Td. Review missing measured-T years and yearwise differences.
No forcing, ERA5 download, NetCDF, DATM, CIME or Slurm modifications.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

HOME = Path.home()
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11 = BASE / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S19 = HOME / "AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
S20 = HOME / "AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
S21 = HOME / "AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
SITE = "US-Ho1"
NEGATIVE_BY_YEAR = {1998:64, 1999:25, 2001:230, 2003:1, 2004:6, 2005:60, 2007:39}

def checksum(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()

def numeric(col):
    data = pd.to_numeric(col, errors="coerce")
    return data.mask((data <= -9990) | ~np.isfinite(data))

def water_es(t):
    with np.errstate(all="ignore"):
        return 6.112 * np.exp(17.67*t/(t+243.5))

def quantiles(col):
    data = numeric(col).dropna()
    return data.quantile([0,.05,.25,.5,.75,.95,1]).round(4).to_string() if len(data) else "NONE"

def load(args):
    for base in (args.stage11_root, args.stage19_root, args.stage20_root):
        if not (base/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Scientific HOLD marker absent: "+str(base))
    m11=json.loads((args.stage11_root/"manifest.json").read_text())
    m19=json.loads((args.stage19_root/"manifest.json").read_text())
    m20=json.loads((args.stage20_root/"manifest.json").read_text())
    m21=json.loads((args.stage21_root/"manifest.json").read_text())
    if m19.get("n_target_rows")!=4884 or m19.get("scientifically_approved_rows")!=0:
        raise ValueError("Stage19 target/scientific contract changed")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED":
        raise ValueError("US-Ho1 clock provenance requires new review")
    if m20.get("number_targets")!=4884 or m20.get("number_approved")!=0:
        raise ValueError("Stage20 target/scientific contract changed")
    if Path(m20["stage19_root"]).resolve()!=args.stage19_root.resolve() or \
       checksum(args.stage19_root/"manifest.json")!=m20["stage19_manifest_sha256"]:
        raise ValueError("Stage19/20 lineage changed")
    if checksum(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv")!=m21["stage20_csv_sha256"]:
        raise ValueError("Stage20 report SHA256 not identical to Stage21 provenance")

    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    sources=[r for r in m08["sites"] if r["site"]==SITE]
    if len(sources)!=1:raise ValueError("Original US-Ho1 release absent")
    path=Path(sources[0]["primary"]).resolve(strict=True)
    expected=m19["original_source_sha256"][SITE]
    if checksum(path)!=expected or m11["input_hashes"].get(str(path))!=expected:
        raise ValueError("Original source SHA256 changed")

    rawcols=["TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC","VPD_ERA"]
    raw=pd.read_csv(path,usecols=rawcols,dtype={"TIMESTAMP_START":str})
    raw["local"]=pd.to_datetime(
        raw.TIMESTAMP_START.str.strip().str.replace(r"\.0$","",regex=True),
        format="%Y%m%d%H%M",errors="raise")
    raw.drop(columns="TIMESTAMP_START",inplace=True)
    for c in rawcols[1:]:raw[c]=numeric(raw[c])
    if raw.local.duplicated().any() or not raw.local.is_monotonic_increasing:
        raise ValueError("Original source local timestamps invalid")

    nineteen=pd.read_csv(
        args.stage19_root/"all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv",
        usecols=["site","local","retained_TA_C","ERA5_T2M_C","ERA5_Td2M_C"],
        parse_dates=["local"])
    twenty=pd.read_csv(
        args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv",
        parse_dates=["local"])
    if len(nineteen)!=4884 or len(twenty)!=4884:
        raise ValueError("Stage19/20 all-site table length changed")
    for name,data in (("Stage19",nineteen),("Stage20",twenty)):
        if data.duplicated(["site","local"]).any():
            raise ValueError(name+" duplicate timestamps")
    nineteen=nineteen.loc[nineteen.site.eq(SITE)]
    twenty=twenty.loc[twenty.site.eq(SITE)]
    if len(nineteen)!=917 or len(twenty)!=917:
        raise ValueError("US-Ho1 target count not 917")
    x=twenty.merge(nineteen,on=["site","local"],how="inner",
                   validate="one_to_one",suffixes=("","_stage19"))
    if len(x)!=917:raise ValueError("Stage19/20 site-year keys inconsistent")
    for c in ("retained_TA_C","ERA5_T2M_C","ERA5_Td2M_C"):
        if not np.allclose(numeric(x[c]),numeric(x[c+"_stage19"]),
                           atol=1e-9,rtol=0,equal_nan=True):
            raise ValueError("Stage19/20 data disagreement: "+c)
    x=x.merge(raw,on="local",how="left",validate="one_to_one",
              suffixes=("","_raw"),indicator=True)
    if not x._merge.eq("both").all():
        raise ValueError("Stage20 timestamp cannot be matched to raw FLUXMET")
    x.drop(columns="_merge",inplace=True)
    if not np.allclose(x.retained_TA_C,x.TA_F_raw,atol=1e-6,rtol=0,equal_nan=True):
        raise ValueError("Retained temperature differs from original tower source")
    for c in ("TA_F","TA_F_QC","VPD_F","VPD_F_QC"):
        if c in twenty.columns and not np.allclose(
             numeric(x[c]),numeric(x[c+"_raw"]),atol=1e-6,rtol=0,equal_nan=True):
            raise ValueError("Stage20/source mismatch for "+c)
    if [int(x.TA_F_QC_raw.eq(q).sum()) for q in (0,1,2)]!=[216,1,700]:
        raise ValueError("Original temperature QC0/QC1/QC2 counts changed")
    q2=x.TA_F_QC_raw.eq(2)
    if not (x.loc[q2,"TA_F_raw"]-x.loc[q2,"TA_ERA"]).abs().le(.001).all():
        raise ValueError("QC2 final temperature not equal to FLUXNET ERA")

    x["year"]=x.local.dt.year
    x["cds_minus_retained_T_C"]=x.ERA5_T2M_C-x.retained_TA_C
    x["cds_dewpoint_minus_retained_T_C"]=x.ERA5_Td2M_C-x.retained_TA_C
    x["Td_recomputed_VPD_hPa"]=water_es(x.retained_TA_C)-water_es(x.ERA5_Td2M_C)
    x["bad_Td"]=x.Td_recomputed_VPD_hPa.lt(-.005)
    if not np.allclose(x.Td_recomputed_VPD_hPa,x.Td_transfer_water_VPD_hPa,
                       rtol=1e-8,atol=1e-7):
        raise ValueError("Stage20 dewpoint sensitivity not reproduced")
    negative=x.loc[x.bad_Td]
    if len(negative)!=425 or not negative.TA_F_QC_raw.eq(2).all():
        raise ValueError("Stage32 425 negative-VPD QC2 baseline changed")
    if negative.groupby("year").size().to_dict()!=NEGATIVE_BY_YEAR:
        raise ValueError("Stage32 negative-year pattern changed")
    return raw,x,path

def report(raw,x):
    yrs=sorted(x.year.unique())
    raw=raw.loc[raw.local.dt.year.isin(yrs)].copy()
    raw=raw.loc[~(raw.local.dt.month.eq(2)&raw.local.dt.day.eq(29))]
    raw["year"]=raw.local.dt.year
    yearly_qc0=raw.loc[raw.TA_F_QC.eq(0)&raw.TA_F.notna()].groupby("year").size()
    rows=[]
    for year,z in x.groupby("year",sort=True):
        q2=z.TA_F_QC_raw.eq(2)
        bad=z.bad_Td
        d=z.cds_minus_retained_T_C
        rows.append(dict(
            year=int(year),held=len(z),
            held_QC0=int(z.TA_F_QC_raw.eq(0).sum()),
            held_QC2=int(q2.sum()),
            year_original_QC0=int(yearly_qc0.get(year,0)),
            Td_negative=int(bad.sum()),
            QC2_abs_Tgap_gt5C=int((q2&d.abs().gt(5)).sum()),
            QC2_abs_Tgap_gt10C=int((q2&d.abs().gt(10)).sum()),
            QC2_median_CDS_minus_FLUXNET_T_C=round(d.loc[q2].median(),3) if q2.any() else np.nan,
            bad_median_CDS_Td_minus_FLUXNET_T_C=round(z.loc[bad,"cds_dewpoint_minus_retained_T_C"].median(),3) if bad.any() else np.nan))
    table=pd.DataFrame(rows)
    print("="*104)
    print("STAGE34 | US-Ho1 TEMPERATURE GAPFILL PROVENANCE SCIENCE AUDIT")
    print("All 917 target rows on HOLD; 425 invalid Td transfers; no forced repair")
    print("="*104)
    print("\nYear-by-year QC provenance and temperature differences:")
    print(table.to_string(index=False))
    bad=x.loc[x.bad_Td]
    other=x.loc[x.TA_F_QC_raw.eq(2)&~x.bad_Td]
    print("\n425 NEGATIVE Td-TRANSFER EVENTS: independent CDS T minus FLUXNET QC2 T (C)")
    print(quantiles(bad.cds_minus_retained_T_C))
    print("\n425 EVENTS: independent CDS Td minus FLUXNET QC2 T (C)")
    print(quantiles(bad.cds_dewpoint_minus_retained_T_C))
    print("425 events with abs(CDS T - FLUXNET ERA T) >5/10/15/20C:",
          *[int(bad.cds_minus_retained_T_C.abs().gt(v).sum()) for v in (5,10,15,20)])
    print("\nQC2 WITHOUT negative Td transfer (n=",len(other),") T-difference quantiles:")
    print(quantiles(other.cds_minus_retained_T_C))
    print("\nWorst 10 Td-transfer VPD events:")
    print(bad.nsmallest(10,"Td_recomputed_VPD_hPa")[
       ["local","TA_F_raw","TA_ERA","ERA5_T2M_C","ERA5_Td2M_C",
        "cds_minus_retained_T_C","cds_dewpoint_minus_retained_T_C",
        "Td_recomputed_VPD_hPa","VPD_F_raw","VPD_F_QC_raw"]
    ].round(4).to_string(index=False))
    obs=x.loc[x.TA_F_QC_raw.eq(0)]
    f=(obs.TA_ERA-obs.TA_F_raw).abs()
    c=(obs.ERA5_T2M_C-obs.TA_F_raw).abs()
    print("\nStage30 selected observed-T QC0 anchors:",len(obs))
    print("FLUXNET ERA MAE",round(f.mean(),3),"CDS ERA5 MAE",round(c.mean(),3))
    if len(obs)!=216 or abs(f.mean()-2.804)>.006 or abs(c.mean()-1.481)>.006:
        raise ValueError("Historical Stage30 measured-temperature audit baseline changed")
    print("\nNOTICE: original QC2 data may be physically inconsistent with independent ERA5.")
    print("ERA5 temperature gap does not prove ERA5 or FLUXNET source is objectively correct.")
    print("UTC-5 best among tested offsets, but BADM UTC_OFFSET still uncertified.")
    print("All 917 US-Ho1 / all 4,884 Batch02 remain SCIENTIFIC HOLD.")
    print("NO WRITES / NO ERA5 DOWNLOAD / NO FORCING, DATM, CIME OR SLURM CHANGES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    p.add_argument("--stage11-root",type=Path,default=S11)
    p.add_argument("--stage19-root",type=Path,default=S19)
    p.add_argument("--stage20-root",type=Path,default=S20)
    p.add_argument("--stage21-root",type=Path,default=S21)
    args=p.parse_args()
    raw,x,source=load(args)
    print("STAGE34 LINEAGE PASS: ",source.name,"| held",len(x),
          "| negative dewpoint-transfer VPD",int(x.bad_Td.sum()))
    if args.check:
        print("CHECK ONLY; no files or model changes")
        return
    report(raw,x)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch02 Stage36: Howland shared-temperature-source identity audit (READ ONLY).

Compare exact original FLUXNET source TA_F/QC0 at matching native timestamps
across US-Ho1/US-Ho2/US-Ho3. Quantify identical values, contiguous identical
runs, and actual independent-timestamp coverage of the 425 US-Ho1 held
negative dewpoint-transfer VPD cases. No automatic approval or data edits.

QC0 is an observation-source code, NOT proof of separate sensor hardware.
All site local-time comparisons remain provisional until UTC_OFFSET/BADM
metadata and sensor-data lineage are independently verified.
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
DEFAULT11 = BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
DEFAULT19 = HOME/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
DEFAULT20 = HOME/"AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
DEFAULT21 = HOME/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
SITES = ("US-Ho1","US-Ho2","US-Ho3")

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(2**20),b""):
            h.update(b)
    return h.hexdigest()

def source_pinned(name, hashes, site):
    path=Path(name).resolve(strict=True)
    matches=[]
    for literal,value in hashes.items():
        try:
            same=Path(literal).resolve(strict=True)==path
        except (OSError,RuntimeError):
            same=False
        if same:
            matches.append(value)
    if not matches:
        raise ValueError(site+" original release missing from Stage08 SHA ledger")
    if len(set(matches))!=1:
        raise ValueError(site+" original SHA ledger aliases conflict")
    if digest(path)!=matches[0]:
        raise ValueError(site+" original source SHA256 changed: "+str(path))
    return path

def valid_series(series):
    a=pd.to_numeric(series,errors="coerce")
    return a.mask((a<=-9990)|~np.isfinite(a))

def water_es(t):
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def original_temperature(path):
    names=["TIMESTAMP_START","TA_F","TA_F_QC"]
    if not set(names).issubset(set(pd.read_csv(path,nrows=0).columns)):
        raise ValueError("Original source missing temperature and QC fields "+str(path))
    x=pd.read_csv(path,usecols=names,dtype={"TIMESTAMP_START":str})
    x["local"]=pd.to_datetime(x.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")
    x["TA_F"]=valid_series(x.TA_F)
    x["TA_F_QC"]=valid_series(x.TA_F_QC)
    if x.local.duplicated().any() or not x.local.is_monotonic_increasing:
        raise ValueError("Original source timestamps duplicate/nonincreasing")
    if not x.TA_F_QC.dropna().isin([0,1,2]).all():
        raise ValueError("Source release has unexpected temperature QC")
    x["measured"]=x.TA_F_QC.eq(0)&x.TA_F.notna()
    return x[["local","TA_F","TA_F_QC","measured"]]

def load(args):
    for folder in [args.stage11_root,args.stage19_root,args.stage20_root]:
        if not (folder/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Required science HOLD marker absent: "+str(folder))
    m11=json.loads((args.stage11_root/"manifest.json").read_text())
    m19=json.loads((args.stage19_root/"manifest.json").read_text())
    m20=json.loads((args.stage20_root/"manifest.json").read_text())
    m21=json.loads((args.stage21_root/"manifest.json").read_text())
    if (m19.get("n_target_rows"),m19.get("scientifically_approved_rows"))!=(4884,0):
        raise ValueError("Stage19 4,884/zero-approved contract changed")
    if (m20.get("number_targets"),m20.get("number_approved"))!=(4884,0):
        raise ValueError("Stage20 4,884/zero-approved contract changed")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED":
        raise ValueError("US-Ho1 offset status changed")
    if Path(m20["stage19_root"]).resolve()!=args.stage19_root.resolve() or \
       digest(args.stage19_root/"manifest.json")!=m20["stage19_manifest_sha256"]:
        raise ValueError("Stage20/Stage19 ancestry changed")
    if digest(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv")!=m21["stage20_csv_sha256"]:
        raise ValueError("Stage21 checksum of Stage20 differs")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    info={d["site"]:d for d in m08["sites"] if d["site"] in SITES}
    if set(info)!=set(SITES):
        raise ValueError("One or more original Howland site releases are missing")
    tables={}
    for site in SITES:
        path=source_pinned(info[site]["primary"],m08["input_sha256"],site)
        if site=="US-Ho1" and digest(path)!=m19["original_source_sha256"][site]:
            raise ValueError("US-Ho1 original is not Stage19-pinned release")
        tables[site]=original_temperature(path)
        print("SOURCE VERIFIED:",site,"raw rows",len(tables[site]),
              "QC0",int(tables[site].measured.sum()),flush=True)
    held=pd.read_csv(
        args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv",
        usecols=["site","local","retained_TA_C","TA_F_QC",
                 "ERA5_T2M_C","ERA5_Td2M_C","Td_transfer_water_VPD_hPa"],
        parse_dates=["local"])
    if len(held)!=4884 or held.duplicated(["site","local"]).any():
        raise ValueError("Stage20 site/row/timestamp structure differs")
    held=held.loc[held.site.eq("US-Ho1")].copy()
    if len(held)!=917:
        raise ValueError("Expected 917 US-Ho1 held records")
    joined=held.merge(
        tables["US-Ho1"][["local","TA_F","TA_F_QC"]],
        on="local",how="left",validate="one_to_one",
        suffixes=("","_raw"),indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Held rows not present in pinned US-Ho1 release")
    if not np.isclose(joined.retained_TA_C,joined.TA_F,
                      atol=1e-6,rtol=0,equal_nan=True).all():
        raise ValueError("Retained temperature does not reproduce Ho1 source")
    if not np.isclose(joined.TA_F_QC,joined.TA_F_QC_raw,
                      atol=0,rtol=0,equal_nan=True).all():
        raise ValueError("Stage20 temperature source QC differs from original")
    residual=water_es(joined.retained_TA_C)-water_es(joined.ERA5_Td2M_C)
    if not np.allclose(residual,joined.Td_transfer_water_VPD_hPa,
                       atol=1e-7,rtol=1e-8):
        raise ValueError("Stage20 dewpoint-transfer calculations changed")
    joined["negative_Td"]=(residual < -0.005)
    if int(joined.negative_Td.sum())!=425 or \
       not joined.loc[joined.negative_Td,"TA_F_QC"].eq(2).all():
        raise ValueError("Stage35 425 negative-VPD QC2 historical result changed")
    return tables,joined

def pair_data(table_a,table_b,site_a,site_b):
    a=table_a[["local","TA_F","measured"]].rename(
        columns={"TA_F":"temperature_a","measured":"observed_a"})
    b=table_b[["local","TA_F","measured"]].rename(
        columns={"TA_F":"temperature_b","measured":"observed_b"})
    pairs=a.merge(b,on="local",how="inner",validate="one_to_one")
    pairs=pairs.loc[pairs.observed_a & pairs.observed_b].copy()
    pairs["absolute_difference_C"]=(pairs.temperature_a-pairs.temperature_b).abs()
    pairs["year"]=pairs.local.dt.year
    print("\n"+"="*108)
    print("QC0 PAIR:",site_a,site_b,"| matched observed timestamps:",len(pairs))
    if pairs.empty:
        print("NO SIMULTANEOUS QC0 OBSERVATIONS; NO INDEPENDENCE CLAIM")
        return pairs
    annual=pairs.groupby("year").agg(
        n=("local","size"),
        identical_0p001C=("absolute_difference_C",lambda s:int(s.le(.001).sum())),
        close_0p01C=("absolute_difference_C",lambda s:int(s.le(.01).sum())),
        median_abs_C=("absolute_difference_C","median"),
        p95_abs_C=("absolute_difference_C",lambda s:float(s.quantile(.95))))
    annual["fraction_identical"]=annual.identical_0p001C/annual.n
    years=[1999,2001,2002,2003,2004,2005,2007,2009,2010,2012,2014,2017]
    print("Relevant years (QC0 source times only):")
    print(annual.reindex([y for y in years if y in annual.index]).round(4).to_string())
    print("Overall exact-within-0.001C:",int(pairs.absolute_difference_C.le(.001).sum()),
          "close-within-0.01C:",int(pairs.absolute_difference_C.le(.01).sum()))
    matched=pairs.loc[pairs.absolute_difference_C.le(.001)].copy()
    if not matched.empty:
        matched["segment"]=matched.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
        long=matched.groupby("segment").agg(
            start=("local","min"),end=("local","max"),records=("local","size"))
        long["days"]=long.records/48
        print("Longest exact-temperature sequences (30-minute adjacency):")
        print(long.sort_values("records",ascending=False).head(7).to_string(index=False))
    print("IMPORTANT: equality may indicate shared sensor, duplicated feed, rounding, or genuine close values.")
    return pairs

def negative_case_identity(tables,held):
    cohort=held.loc[held.negative_Td].copy()
    for site,suffix in (("US-Ho2","H2"),("US-Ho3","H3")):
        ref=tables[site][["local","TA_F","measured"]].rename(
            columns={"TA_F":"T_"+suffix,"measured":"Q0_"+suffix})
        cohort=cohort.merge(ref,on="local",how="left",validate="one_to_one")
        cohort["Q0_"+suffix]=(cohort["Q0_"+suffix]==True)&cohort["T_"+suffix].notna()
    h2=cohort.Q0_H2
    h3=cohort.Q0_H3
    both=h2 & h3
    unique=int((h2|h3).sum())
    print("\n"+"="*108)
    print("425 NEGATIVE Td-VPD TIMESTAMPS: NONDOUBLECOUNTED SOURCE COVERAGE")
    print("Ho2 QC0",int(h2.sum()),"Ho3 QC0",int(h3.sum()),
          "both",int(both.sum()),"Ho2 only",int((h2&~h3).sum()),
          "Ho3 only",int((h3&~h2).sum()),"neither",int((~h2&~h3).sum()),
          "unique timestamps with QC0",unique,"/425")
    if [int(h2.sum()),int(h3.sum()),int(both.sum()),unique]!=[67,106,67,106]:
        raise ValueError("Stage35 neighbour overlap unexpectedly differs")
    if int((~h2&~h3).sum())!=319:
        raise ValueError("Stage35 missing-neighbour record count differs")
    if both.any():
        z=cohort.loc[both].copy()
        diff=(z.T_H2-z.T_H3).abs()
        print("Both QC0 neighbour agreement, n",len(z))
        print("Ho2/Ho3 temperature delta <=0.001C:",int(diff.le(.001).sum()),
              "<=0.01C:",int(diff.le(.01).sum()),
              "median abs:",round(float(diff.median()),5),
              "p95 abs:",round(float(diff.quantile(.95)),5))
        for label,temp in [("Ho2",z.T_H2),("Ho3",z.T_H3)]:
            e_flux=(temp-z.retained_TA_C).abs()
            e_cds=(temp-z.ERA5_T2M_C).abs()
            print(label,"on IDENTICAL 67 timestamps: MAE vs Ho1 QC2",
                  round(float(e_flux.mean()),3),
                  "MAE vs CDS",round(float(e_cds.mean()),3))
    only3=cohort.loc[h3&~h2]
    print("HO3-only QC0 timing by year:",only3.groupby(only3.local.dt.year).size().to_dict())
    print("NO-NEIGHBOUR QC0 timing by year:",
          cohort.loc[~h2&~h3].groupby(cohort.loc[~h2&~h3].local.dt.year).size().to_dict())
    print("CROSS-SITE TA QCs ARE NOT PROOF OF SENSOR OR DATA-PROCESSING INDEPENDENCE.")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    ap.add_argument("--stage11-root",type=Path,default=DEFAULT11)
    ap.add_argument("--stage19-root",type=Path,default=DEFAULT19)
    ap.add_argument("--stage20-root",type=Path,default=DEFAULT20)
    ap.add_argument("--stage21-root",type=Path,default=DEFAULT21)
    args=ap.parse_args()
    tables,held=load(args)
    print("STAGE36 PREFLIGHT PASS | 3 SHA256-verified sources | 917 Ho1 held / 425 negative Td")
    if args.check:
        print("CHECK ONLY | NO FILES WRITTEN OR SCIENCE APPROVAL")
        return
    for a,b in (("US-Ho1","US-Ho2"),
                ("US-Ho1","US-Ho3"),
                ("US-Ho2","US-Ho3")):
        pair_data(tables[a],tables[b],a,b)
    negative_case_identity(tables,held)
    print("\nStage35 neighbour BIF files were NOT part of Stage08 pinned SHA ledger.")
    print("Do not infer certified site clocks, shared hardware or instrument independence.")
    print("All 917 US-Ho1 / 4,884 Batch02 remain SCIENTIFIC HOLD; approved repairs=0.")
    print("READ ONLY: NO SOURCE, FORCING, NETCDF, DATM, CIME OR SLURM CHANGE")

if __name__=="__main__":
    main()

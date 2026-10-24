#!/usr/bin/env python3
"""Stage37: US-Ho1 319 unanchored cold-humidity events — ERA provenance (READ ONLY).

Reproduces Stage36's 425 negative dewpoint-transfer-VPD subset and exact
three-tower observed-QC0 coverage. Only the 319 events with NEITHER Ho2
nor Ho3 QC0 temperature are investigated here: 1998 (64), 1999 (25),
and 2001 (230). At 1999/2001 timestamps, compare the existing Howland
Ho1 vs Ho2 embedded FLUXNET-downscaled ERA temperature and CDS ERA5.
Ho2 ERA is not an independent observation and is NEVER an approval.

Outputs stdout-only scientific evidence and exact event windows needed
for a FUTURE independent external observation/BADM review. No downloads,
files written, forcing edits, NetCDF changes, CIME, DATM or Slurm jobs.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
HOME = Path.home()
S11 = ROOT/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S19 = HOME/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
S20 = HOME/"AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
S21 = HOME/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
SITES=("US-Ho1","US-Ho2","US-Ho3")
UNANCHORED_BY_YEAR={1998:64,1999:25,2001:230}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(2**20),b""):
            h.update(block)
    return h.hexdigest()

def canonical_verify(file_name, ledger, label):
    path=Path(file_name).resolve(strict=True)
    matches=[]
    for source_literal,expected in ledger.items():
        try: same=Path(source_literal).resolve(strict=True)==path
        except (OSError, RuntimeError):same=False
        if same:matches.append(expected)
    if len(matches)==0:raise ValueError(label+" absent from Stage08 input hash manifest")
    if len(set(matches))!=1:raise ValueError(label+" conflicting SHA aliases")
    actual=sha(path)
    if actual!=matches[0]:
        raise ValueError(label+" raw SHA256 changed: "+str(path)+
                         " expected="+str(matches[0])+" actual="+actual)
    return path

def numbers(col):
    x=pd.to_numeric(col,errors="coerce")
    return x.mask((x<=-9990)|~np.isfinite(x))

def sat_water(t):
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def original(path, require_era):
    names={"TIMESTAMP_START","TA_F","TA_F_QC"}
    all_fields=set(pd.read_csv(path,nrows=0).columns)
    if not names<=all_fields:
        raise ValueError("FLUXMET missing original T/QC: "+str(path))
    if require_era and "TA_ERA" not in all_fields:
        raise ValueError("FLUXMET original Ho1 missing TA_ERA: "+str(path))
    want=names|({"TA_ERA"} if "TA_ERA" in all_fields else set())
    a=pd.read_csv(path,usecols=sorted(want),dtype={"TIMESTAMP_START":str})
    a["local"]=pd.to_datetime(a.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")
    if a.local.duplicated().any() or not a.local.is_monotonic_increasing:
        raise ValueError("Original timestamp identity invalid: "+str(path))
    for col in ["TA_F","TA_F_QC","TA_ERA"]:
        a[col]=numbers(a[col]) if col in a else pd.Series(np.nan,index=a.index)
    if not a.TA_F_QC.dropna().isin([0,1,2]).all():
        raise ValueError("FLUXMET unexpected original temperature QC")
    a["observed_qc0"]=a.TA_F_QC.eq(0)&a.TA_F.notna()
    return a

def source_contract(args):
    for base in (args.stage11_root,args.stage19_root,args.stage20_root):
        if not (base/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Missing scientific HOLD marker: "+str(base))
    m11=json.loads((args.stage11_root/"manifest.json").read_text())
    m19=json.loads((args.stage19_root/"manifest.json").read_text())
    m20=json.loads((args.stage20_root/"manifest.json").read_text())
    m21=json.loads((args.stage21_root/"manifest.json").read_text())
    if (m19.get("n_target_rows"),m19.get("scientifically_approved_rows"))!=(4884,0):
        raise ValueError("Stage19 4884 / 0 approval contract differs")
    if (m20.get("number_targets"),m20.get("number_approved"))!=(4884,0):
        raise ValueError("Stage20 4884 / 0 approval contract differs")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED":
        raise ValueError("US-Ho1 clock metadata changed: do not assume -5")
    if Path(m20["stage19_root"]).resolve()!=args.stage19_root.resolve() or \
       sha(args.stage19_root/"manifest.json")!=m20["stage19_manifest_sha256"]:
        raise ValueError("Stage20 does not match pinned Stage19 manifest")
    if sha(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv")!=m21["stage20_csv_sha256"]:
        raise ValueError("Stage21 hash no longer matches Stage20 table")

    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    site_info={r["site"]:r for r in m08["sites"] if r["site"] in SITES}
    if set(site_info)!=set(SITES):
        raise ValueError("Stage08 original source inventory missing a Howland site")
    source={}
    for site in SITES:
        raw=canonical_verify(site_info[site]["primary"],m08["input_sha256"],site)
        if site=="US-Ho1" and sha(raw)!=m19["original_source_sha256"][site]:
            raise ValueError("Stage19 US-Ho1 raw SHA256 mismatch")
        source[site]=original(raw,require_era=site=="US-Ho1")
        print("ORIGINAL SHA256 VERIFIED",site,raw.name,
              "records",len(source[site]),"measured QC0",int(source[site].observed_qc0.sum()),
              "TA_ERA_available",int(source[site].TA_ERA.notna().sum()),flush=True)

    table=pd.read_csv(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv",
        usecols=["site","local","retained_TA_C","TA_F_QC",
                 "ERA5_T2M_C","ERA5_Td2M_C","Td_transfer_water_VPD_hPa"],
        parse_dates=["local"])
    if len(table)!=4884 or table.duplicated(["site","local"]).any():
        raise ValueError("Stage20 target rows/identities changed")
    x=table.loc[table.site.eq("US-Ho1")].copy()
    if len(x)!=917:raise ValueError("Ho1 hold not 917")
    h1=source["US-Ho1"][["local","TA_F","TA_F_QC","TA_ERA"]]
    x=x.merge(h1,on="local",how="left",validate="one_to_one",
              suffixes=("","_raw"),indicator=True)
    if not x._merge.eq("both").all():raise ValueError("Held times missing original source")
    if not np.isclose(x.retained_TA_C,x.TA_F,atol=1e-6,rtol=0,equal_nan=True).all():
        raise ValueError("Stage20 retained TA not original Ho1 TA")
    if not np.isclose(x.TA_F_QC,x.TA_F_QC_raw,atol=0,rtol=0,equal_nan=True).all():
        raise ValueError("Stage20 original QC code changed")
    if [int(x.TA_F_QC.eq(q).sum()) for q in (0,1,2)]!=[216,1,700]:
        raise ValueError("Ho1 temperature source groups no longer 216/1/700")
    qc2=x.TA_F_QC.eq(2)
    if not (x.loc[qc2,"TA_F"]-x.loc[qc2,"TA_ERA"]).abs().le(.001).all():
        raise ValueError("Ho1 QC2 temperature differs from original TA_ERA")
    pred=sat_water(x.retained_TA_C)-sat_water(x.ERA5_Td2M_C)
    if not np.allclose(pred,x.Td_transfer_water_VPD_hPa,atol=1e-7,rtol=1e-8):
        raise ValueError("Stage20 retained-T/Td VPD reproducibility mismatch")
    x["negative_td"]=pred.lt(-.005)
    if int(x.negative_td.sum())!=425 or not x.loc[x.negative_td,"TA_F_QC"].eq(2).all():
        raise ValueError("Stage36 425 negative QC2 count differs")

    for site,short in (("US-Ho2","H2"),("US-Ho3","H3")):
        z=source[site][["local","TA_F","TA_F_QC","TA_ERA","observed_qc0"]]
        rename={"TA_F":short+"_T","TA_F_QC":short+"_QC","TA_ERA":short+"_ERA",
                "observed_qc0":short+"_observed"}
        x=x.merge(z.rename(columns=rename),on="local",how="left",validate="one_to_one")
        x[short+"_observed"]=x[short+"_observed"].eq(True)&x[short+"_T"].notna()
    bad=x.loc[x.negative_td].copy()
    h2=bad.H2_observed
    h3=bad.H3_observed
    if [int(h2.sum()),int(h3.sum()),int((h2&h3).sum())]!=[67,106,67]:
        raise ValueError("Stage36 Ho2/Ho3 observed overlap differs")
    bad["no_observed_neighbor"]=~(h2|h3)
    unanchored=bad.loc[bad.no_observed_neighbor].copy()
    unanchored["year"]=unanchored.local.dt.year
    if len(unanchored)!=319 or unanchored.groupby("year").size().to_dict()!=\
        UNANCHORED_BY_YEAR:
        raise ValueError("Stage36 319 missing-independent-anchor event identity changed")
    return x,unanchored

def qs(series):
    a=numbers(series).dropna()
    if a.empty:return "NO VALID NUMERICAL VALUES"
    return a.quantile([0,.05,.25,.5,.75,.95,1]).round(4).to_string()

def consecutive_spells(a):
    if a.empty:return pd.DataFrame()
    s=a.sort_values("local").copy()
    s["episode"]=s.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    return s.groupby("episode").agg(
        first=("local","min"),last=("local","max"),records=("local","size"),
        min_Td_VPD_hPa=("Td_transfer_water_VPD_hPa","min"),
        median_CDS_minus_Ho1_T_C=("CDS_minus_Ho1_T_C","median")
    ).sort_values("records",ascending=False).head(12)

def report(x,missing):
    print("\n"+"="*110)
    print("STAGE37 | US-Ho1 319 NO-NEIGHBOUR-QC0 HUMIDITY BLOCKERS")
    print("Numerical source provenance only. NO new independent observations.")
    print("="*110)
    print("319:",missing.groupby("year").size().to_dict())
    missing=missing.copy()
    missing["CDS_minus_Ho1_T_C"]=missing.ERA5_T2M_C-missing.retained_TA_C
    missing["CDS_Td_minus_Ho1_T_C"]=missing.ERA5_Td2M_C-missing.retained_TA_C
    print("\nCDS T - original Ho1 QC2 T, among 319 (C):\n"+qs(missing.CDS_minus_Ho1_T_C))
    print("\nCDS Td - original Ho1 QC2 T, among 319 (C):\n"+qs(missing.CDS_Td_minus_Ho1_T_C))
    print("\nNO-QC0 timestamp duration by year:")
    for year,z in missing.groupby("year",sort=True):
        s=z.sort_values("local")
        have_era=s.H2_ERA.notna()
        qc_counts=s.H2_QC.value_counts(dropna=False).to_dict()
        print("\nYEAR",year,"events",len(z),"first",s.local.min(),
              "last",s.local.max(),"Ho2 FLUXNET-ERA T available",
              int(have_era.sum()),"Ho2 original final-T QC distribution",qc_counts)
        print("Ho1 QC2 vs independent CDS T (C), quantiles:\n"+qs(s.CDS_minus_Ho1_T_C))
        print("Monthly events:",s.groupby(s.local.dt.month).size().to_dict())
        if not have_era.any():
            print("NO simultaneous Ho2 ERA field. Independent station / BASE data required.")
            continue
        q=s.loc[have_era].copy()
        q["Ho2_ERA_minus_Ho1_ERA_C"]=q.H2_ERA-q.TA_ERA
        q["Ho2_ERA_minus_CDS_C"]=q.H2_ERA-q.ERA5_T2M_C
        q["Ho1_ERA_minus_CDS_C"]=q.TA_ERA-q.ERA5_T2M_C
        print("HO2 FLUXNET-ERA vs HO1 FLUXNET-ERA T difference (C):\n"+
              qs(q.Ho2_ERA_minus_Ho1_ERA_C))
        print("HO2 FLUXNET-ERA vs CDS ERA5 T difference (C):\n"+
              qs(q.Ho2_ERA_minus_CDS_C))
        print("ERA T same <=0.001/0.1/1.0C (Ho1 vs Ho2):",
              *[int(q.Ho2_ERA_minus_Ho1_ERA_C.abs().le(v).sum())
                for v in (.001,.1,1.)],"/",len(q))
        print("Both FLUXNET ERA temperatures >5C colder than CDS:",
              int(((q.TA_ERA-q.ERA5_T2M_C).lt(-5)&
                   (q.H2_ERA-q.ERA5_T2M_C).lt(-5)).sum()),"/",len(q))
        print("IMPORTANT: both FLUXNET ERA columns are processed gridded estimates, NOT QC0.")

    print("\nLongest consecutive 30-minute episodes within missing 319:")
    print(consecutive_spells(missing).round(4).to_string(index=False))
    print("\nWorst 12 unanchored Td-VPD physical conflicts:")
    print(missing.nsmallest(12,"Td_transfer_water_VPD_hPa")[
        ["local","retained_TA_C","ERA5_T2M_C","ERA5_Td2M_C",
         "Td_transfer_water_VPD_hPa","H2_ERA","H2_QC"]]
          .round(4).to_string(index=False))
    print("\nRECOMMENDED EXTERNAL EVIDENCE (NOT ACQUIRED BY THIS SCRIPT)")
    print("1. Authoritative Howland BASE temperature/metadata and PI instrument provenance, 1998/1999/2001.")
    print("   https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1")
    print("2. NOAA NCEI Global Hourly weather-station observations covering these times,")
    print("   selecting suitable stations with known UTC times, distance/altitude and QC,")
    print("   e.g. inspect Bangor and Millinocket coverage before any comparisons.")
    print("   https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database")
    print("3. Compare only independently measured air temperature,")
    print("   not Ho2/Ho1 ERA products and not CDS/RH-derived physical consistency.")
    print("4. All records SCIENTIFIC HOLD; no blanket TA or VPD replacement is authorised.")
    print("\nNO FILES WRITTEN / NO DOWNLOAD / NO FORCING, NETCDF, DATM, CIME OR SLURM CHANGES")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--audit",action="store_true")
    parser.add_argument("--stage11-root",type=Path,default=S11)
    parser.add_argument("--stage19-root",type=Path,default=S19)
    parser.add_argument("--stage20-root",type=Path,default=S20)
    parser.add_argument("--stage21-root",type=Path,default=S21)
    args=parser.parse_args()
    x,missing=source_contract(args)
    print("STAGE37 PREFLIGHT PASS: 3 original SHA256 pins, Ho1 917/425,",
          "unique unanchored 319 = 1998:64,1999:25,2001:230")
    if args.check:
        print("CHECK ONLY | NO WRITES OR APPROVAL")
        return
    report(x,missing)

if __name__=="__main__":
    main()

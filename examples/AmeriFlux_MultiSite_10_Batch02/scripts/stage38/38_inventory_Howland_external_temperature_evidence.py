#!/usr/bin/env python3
"""Stage38 | External measured-temperature evidence inventory for Ho1 (READ ONLY).

Scope: exactly 319 Stage37 unanchored US-Ho1 timestamps (1998:64,
1999:25, 2001:230). Check original Stage08/19/20/21 SHA256 lineage,
then inventory bounded, local US-Ho1 BASE/BADM archives and report
exact local/PROVISIONAL UTC-5 anomaly windows.

Display NOAA GHCNh candidate station/year PSV URL patterns for independent
HISTORICAL OBSERVATION review, without downloading or treating the URLs
as proof of hourly coverage. NOAA station data must later be authenticated
and QC screened before comparisons. No external network access here.

Strictly stdout only: do not alter sources, forcing, NetCDF, DATM, CIME,
Slurm, previously downloaded ERA5, or scientific approval status.
"""
import argparse
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

H=Path.home()
BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S19=H/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
S20=H/"AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
S21=H/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
SITES=("US-Ho1","US-Ho2","US-Ho3")
MISSING_BY_YEAR={1998:64,1999:25,2001:230}
NOAA_STATION="USW00014606"   # Bangor airport candidate, GHCN-daily metadata; hourly must be checked

def sha(path):
    d=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):d.update(chunk)
    return d.hexdigest()

def valid(x):
    a=pd.to_numeric(x,errors="coerce")
    return a.mask((a<=-9990)|~np.isfinite(a))

def es(t):
    with np.errstate(all="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def pinned(path,ledger,site):
    p=Path(path).resolve(strict=True)
    values=[]
    for name,digest in ledger.items():
        try: same=Path(name).resolve(strict=True)==p
        except (OSError, RuntimeError): same=False
        if same:values.append(digest)
    if not values:raise ValueError(site+" source not in checksum ledger: "+str(p))
    if len(set(values))!=1:raise ValueError(site+" conflicting hash ledger aliases")
    if sha(p)!=values[0]:raise ValueError(site+" original source SHA256 differs")
    return p

def read_temperature(path):
    cols=["TIMESTAMP_START","TA_F","TA_F_QC"]
    if not set(cols)<=set(pd.read_csv(path,nrows=0).columns):
        raise ValueError("Original release missing native T or QC: "+str(path))
    x=pd.read_csv(path,usecols=cols,dtype={"TIMESTAMP_START":str})
    x["local"]=pd.to_datetime(x.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")
    if x.local.duplicated().any() or not x.local.is_monotonic_increasing:
        raise ValueError("Raw site local clock duplicate/out-of-order")
    x["TA_F"]=valid(x.TA_F)
    x["TA_F_QC"]=valid(x.TA_F_QC)
    if not x.TA_F_QC.dropna().isin([0,1,2]).all():
        raise ValueError("Unknown original source TA_F_QC")
    x["QC0"]=x.TA_F_QC.eq(0)&x.TA_F.notna()
    return x

def sources(args):
    for path in (args.stage11_root,args.stage19_root,args.stage20_root):
        if not (path/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Missing immutable scientific HOLD marker: "+str(path))
    m11=json.loads((args.stage11_root/"manifest.json").read_text())
    m19=json.loads((args.stage19_root/"manifest.json").read_text())
    m20=json.loads((args.stage20_root/"manifest.json").read_text())
    m21=json.loads((args.stage21_root/"manifest.json").read_text())
    if (m19.get("n_target_rows"),m19.get("scientifically_approved_rows"))!=(4884,0):
        raise ValueError("Stage19 scientific target contract changed")
    if (m20.get("number_targets"),m20.get("number_approved"))!=(4884,0):
        raise ValueError("Stage20 scientific target contract changed")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED" or \
       m19.get("UTC_offsets_local_minus_UTC",{}).get("US-Ho1")!=-5:
        raise ValueError("US-Ho1 nominal offset/provenance status differs")
    if Path(m20["stage19_root"]).resolve()!=args.stage19_root.resolve() or \
       sha(args.stage19_root/"manifest.json")!=m20["stage19_manifest_sha256"]:
        raise ValueError("Stage20/Stage19 manifest lineage differs")
    if sha(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv")!=m21["stage20_csv_sha256"]:
        raise ValueError("Stage21/Stage20 table SHA256 lineage differs")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    records={r["site"]:r for r in m08["sites"] if r["site"] in SITES}
    if set(records)!=set(SITES):raise ValueError("Missing original Howland site")
    paths={};tables={}
    for site in SITES:
        path=pinned(records[site]["primary"],m08["input_sha256"],site)
        if site=="US-Ho1" and sha(path)!=m19["original_source_sha256"][site]:
            raise ValueError("Original Ho1 source not Stage19 pinned")
        paths[site]=path
        tables[site]=read_temperature(path)
        print("SOURCE SHA256 VERIFIED",site,path.name,
              "rows",len(tables[site]),"QC0",int(tables[site].QC0.sum()),flush=True)
    full=pd.read_csv(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv",
        usecols=["site","local","retained_TA_C","TA_F_QC",
                 "ERA5_T2M_C","ERA5_Td2M_C","Td_transfer_water_VPD_hPa"],
        parse_dates=["local"])
    if len(full)!=4884 or full.duplicated(["site","local"]).any():
        raise ValueError("Stage20 all-site exact target set changed")
    x=full.loc[full.site.eq("US-Ho1")].copy()
    if len(x)!=917:raise ValueError("Stage20 held Ho1 count differs")
    x=x.merge(tables["US-Ho1"][["local","TA_F","TA_F_QC"]],on="local",
              how="left",validate="one_to_one",suffixes=("","_raw"),indicator=True)
    if not x._merge.eq("both").all():raise ValueError("Missing Stage20/source join")
    if not np.isclose(x.retained_TA_C,x.TA_F,rtol=0,atol=1e-6,equal_nan=True).all():
        raise ValueError("Original Ho1 retained T changed")
    if not np.isclose(x.TA_F_QC,x.TA_F_QC_raw,rtol=0,atol=0,equal_nan=True).all():
        raise ValueError("Original Ho1 TA_F_QC changed")
    x["negative_td"]=(es(x.retained_TA_C)-es(x.ERA5_Td2M_C)).lt(-.005)
    if not np.allclose(es(x.retained_TA_C)-es(x.ERA5_Td2M_C),
                       x.Td_transfer_water_VPD_hPa,rtol=1e-8,atol=1e-7):
        raise ValueError("Stage20 dewpoint-sensitivity baseline changed")
    if int(x.negative_td.sum())!=425 or not x.loc[x.negative_td,"TA_F_QC"].eq(2).all():
        raise ValueError("Stage34-37 Ho1 425 all-QC2 baseline changed")
    for site,short in (("US-Ho2","Ho2"),("US-Ho3","Ho3")):
        b=tables[site][["local","TA_F","QC0"]].rename(
            columns={"TA_F":short+"_TA_F","QC0":short+"_QC0"})
        x=x.merge(b,on="local",how="left",validate="one_to_one")
        x[short+"_QC0"]=x[short+"_QC0"].eq(True)&x[short+"_TA_F"].notna()
    bad=x.loc[x.negative_td].copy()
    a,b=bad.Ho2_QC0,bad.Ho3_QC0
    if [int(a.sum()),int(b.sum()),int((a&b).sum())]!=[67,106,67]:
        raise ValueError("Stage36 observed tower coverage differs")
    unknown=bad.loc[~a&~b].copy()
    unknown["year"]=unknown.local.dt.year
    if len(unknown)!=319 or unknown.groupby("year").size().to_dict()!=MISSING_BY_YEAR:
        raise ValueError("Stage37 319 source timestamp identity changed")
    return paths,tables,unknown

def events(x):
    a=x.sort_values("local").copy()
    a["episode"]=a.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    result=a.groupby("episode").agg(
        first_local=("local","min"),last_local=("local","max"),
        records=("local","size"),min_transferred_vpd_hPa=("Td_transfer_water_VPD_hPa","min"))
    result["first_nominal_UTC"]=(result.first_local+pd.Timedelta(hours=5))
    result["last_nominal_UTC"]=(result.last_local+pd.Timedelta(hours=5))
    return result.sort_values(["first_local"])

def site_root(path):
    for p in path.parents:
        if p.name=="US-Ho1":return p
    raise ValueError("Cannot locate pinned US-Ho1 site directory from "+str(path))

def local_archive_inventory(site):
    # Fixed small-depth inspection; do NOT walk scratch or unzip source archives.
    roots=[site,site/"forcing"]
    force=site/"forcing"
    if force.is_dir():
        roots += [p for p in force.iterdir() if p.is_dir() and
                  (p.name.lower().startswith("packages") or
                   "original" in p.name.lower() or
                   "base" in p.name.lower() or
                   "badm" in p.name.lower())]
    seen=set()
    entries=[]
    for root in roots:
        if not root.is_dir():continue
        for f in root.iterdir():
            if not f.is_file() or f.suffix.lower() not in {".zip",".csv",".tsv",".json"}:
                continue
            if f.name.lower().startswith(("amf_us-ho1","us-ho1")) or \
               any(token in f.name.upper() for token in ("BASE","BADM","BIF")):
                if f.resolve() not in seen:
                    seen.add(f.resolve())
                    entries.append(f)
    entries.sort(key=lambda p:str(p))
    print("\nEXISTING Ho1 SOURCE PACKAGE/METADATA FILE INVENTORY (NO EXTRACTION)")
    if not entries:
        print("No relevant files found within the bounded site folders; other locations not checked.")
    for f in entries[:60]:
        category=("POTENTIAL_BASE_OR_BADM" if
                  any(z in f.name.upper() for z in ("BASE","BADM","BIF"))
                  else "FLUXNET_OR_OTHER_NOT_INDEPENDENT")
        print("FILE",category,"size_bytes",f.stat().st_size,"path",f)
        if category=="POTENTIAL_BASE_OR_BADM":
            print("  UNVERIFIED NEW SOURCE SHA256",sha(f))
        if f.suffix.lower()==".zip":
            try:
                with zipfile.ZipFile(f,"r") as archive:
                    names=archive.namelist()
                    print("  ZIP members",len(names),"sample",names[:12])
                    print("  CONTAINS BASE/BADM/BIF NAMES",
                          [n for n in names if any(z in n.upper() for z in ("BASE","BADM","BIF"))][:15])
            except (zipfile.BadZipFile,OSError) as e:
                print("  ZIP INSPECTION FAILED",str(e))
    if len(entries)>60:
        print("Additional candidate files not displayed:",len(entries)-60)
    print("CAUTION: Published BASE may still share instruments with FLUXNET; review original variable QC and metadata.")

def report(paths,unknown):
    print("\n"+"="*110)
    print("STAGE38 | 319 US-Ho1 EXTERNAL MEASURED-TEMPERATURE EVIDENCE PRECHECK")
    print("SCIENCE HOLD | NO NETWORK ACCESS | NO EXTERNAL DATA YET VERIFIED")
    print("="*110)
    for year,g in unknown.groupby("year",sort=True):
        ev=events(g)
        print("\nYEAR",year,"timestamps",len(g),
              "episodes",len(ev),"nominal local-minus-UTC=-5 (PROVISIONAL)")
        print("ALL contiguous episodes (time windows for new source acquisition):")
        print(ev.to_string())
        print("TEMPERATURE: CDS minus original Ho1 (C) median",
              round(float((g.ERA5_T2M_C-g.retained_TA_C).median()),3))
    local_archive_inventory(site_root(paths["US-Ho1"]))
    print("\nRECOMMENDED INDEPENDENT OBSERVATION SOURCE PRIORITY")
    print("1. Published US-Ho1 AmeriFlux BASE/BASE-BADM for historical 1998, 1999, 2001.")
    print("   Review site temperature variable identities, QC, instrument and UTC offset;")
    print("   BASE may share physical observations with prior FLUXNET release, so independence is NOT assumed.")
    print("   https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1")
    print("2. NOAA GHCNh historical measured-temperature station/year products.")
    print("   New NOAA-recommended source; previous ISD service was retired/relocated in 2026.")
    print("   https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly")
    print("   Bangor airport candidate ID USW00014606 (ID known from NOAA daily station metadata).")
    print("   IMPORTANT: hourly station ID, hourly 1998/1999/2001 temperature coverage,")
    print("   source QC and distance/representativeness NOT confirmed.")
    url="https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-year"
    for year in MISSING_BY_YEAR:
        print("   CANDIDATE NOAA GHCNh PSV",year,":",
              f"{url}/{year}/psv/GHCNh_{NOAA_STATION}_{year}.psv")
    print("   URLs are official format patterns, NOT verified file availability or downloaded data.")
    print("3. Verify station location, elevation, UTC time stamp convention, measurement source and")
    print("   accuracy/QC flags before evaluating even a single temperature comparison.")
    print("4. Do not compare gapfilled Ho2 ERA temperature as independent measured evidence.")
    print("\nNO FILES WRITTEN / NO DOWNLOAD / NO FORCING, NETCDF, DATM, CIME OR SLURM MODIFICATION")
    print("ALL 319 and parent 4,884 remain SCIENTIFIC HOLD; approved replacements=0.")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    p.add_argument("--stage11-root",type=Path,default=S11)
    p.add_argument("--stage19-root",type=Path,default=S19)
    p.add_argument("--stage20-root",type=Path,default=S20)
    p.add_argument("--stage21-root",type=Path,default=S21)
    args=p.parse_args()
    paths,tables,unknown=sources(args)
    print("STAGE38 PREFLIGHT PASS: original Ho1/Ho2/Ho3 SHA256 verified;",
          "319 unanchored rows=1998:64,1999:25,2001:230")
    if args.check:
        print("CHECK ONLY | zero files written and no approved edits")
        return
    report(paths,unknown)

if __name__=="__main__":
    main()

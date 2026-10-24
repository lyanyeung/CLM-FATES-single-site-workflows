#!/usr/bin/env python3
"""Stage47 | Ho1 temperature MDS/QC provenance and error-concentration audit.

READ-ONLY science audit. Stage46 compared all 274,148 original Ho1 QC0
temperature records to the distributed, already site-downscaled TA_ERA:
empirical RMSE 7.7346 deg C vs AUXMETEO ERA_RMSE 4.66, though overall
Pearson r 0.71944 roughly equals reported ERA_CORRELATION 0.72.

First verify unchanged Stage46 script (exact Git blob), original release
source/ZIP/AUXMETEO SHA256, 319 Stage39 unanchored held targets, and all
predecessor provenance. Examine original FULLSET_HH TA_F_MDS, TA_F_MDS_QC
alongside TA_F, TA_F_QC, TA_ERA at EXACT native timestamps.

FLUXNET defines TA_F_MDS_QC=0 as measured and 1/2/3 as gapfill quality.
TA_F is the consolidated product, which uses MDS and ERA. These origins
are related, NOT independent temperature station measurements.

Report:
  - Crosstab consolidated TA_F_QC versus MDS TA_F_MDS_QC across all years
  - QC0 value identities measured-coded TA_F vs MDS and MDS-QC states
  - All QC0 ERA error bins and SQUARED-error concentration (>5/>10/>20C)
  - Year-by-year QC0 ERA RMSE and MDS agreement, focused 1999 months
  - 319 held QC2 events MDS flag coverage and MDS-vs-ERA numerical distances

No reconstructed raw ERA input, no original calibration-window inference.
MDS or consolidated products are not external truth. No edits/downloads/
writes to original ZIP, forcing, NetCDF, DATM, CIME or Slurm. All 4,884
Batch02 records SCIENTIFIC HOLD and approved replacements=0.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

ST46_NAME="46_recompute_Ho1_QC0_vs_ERA_AUXMETEO_diagnostics.py"
ST46_BLOB="1b098fe13e69dea0a895970603b9077b1fe7002a"
EXPECTED_RECORDS=490896
EXPECTED_QC0=274148
EXPECTED_1999_QC0=3005
HELD_COUNTS={1998:64,1999:25,2001:230}
ORIG_TOL=.001

def git_blob(path):
    src=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(src)).encode()+b"\0"+src).hexdigest()

def pinned_parent():
    path=Path(__file__).resolve().with_name(ST46_NAME)
    if not path.is_file():
        raise FileNotFoundError("Download pinned Stage39-46 scripts together beside Stage47")
    sha=git_blob(path)
    if sha!=ST46_BLOB:
        raise ValueError("Stage46 Git blob changed: "+sha+" wanted "+ST46_BLOB)
    spec=importlib.util.spec_from_file_location("pinned_stage46",path)
    if spec is None or spec.loader is None:
        raise ValueError("Pinned Stage46 import failed")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("STAGE46 ORIGINAL SCRIPT PIN VERIFIED",sha,flush=True)
    return mod

def load_mds(original):
    need=["TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS",
          "TA_F_MDS_QC","TA_ERA"]
    data=pd.read_csv(original,usecols=need,dtype={"TIMESTAMP_START":str})
    if len(data)!=EXPECTED_RECORDS:
        raise ValueError("Ho1 original FULLSET_HH row count differs")
    data["native"]=data.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True)
    if data.native.duplicated().any() or not data.native.is_monotonic_increasing:
        raise ValueError("Original native timestamps not unique/ordered")
    for field in need[1:]:
        data[field]=pd.to_numeric(data[field],errors="coerce")
        data.loc[data[field]<=-9990,field]=np.nan
    data["year"]=data.native.str.slice(0,4).astype(int)
    data["month"]=data.native.str.slice(4,6).astype(int)
    if int(data.TA_F_QC.eq(0).sum())!=EXPECTED_QC0:
        raise ValueError("Stage46 original measured-coded QC0 count differs")
    if int(data.loc[data.year.eq(1999),"TA_F_QC"].eq(0).sum())!=EXPECTED_1999_QC0:
        raise ValueError("Stage46 original 1999 QC0 count differs")
    return data

def errors(frame,col1="TA_F",col2="TA_ERA"):
    x=pd.to_numeric(frame[col1],errors="coerce")
    y=pd.to_numeric(frame[col2],errors="coerce")
    z=(x-y)[x.notna()&y.notna()]
    if z.empty:return dict(n=0)
    return dict(n=int(len(z)),
                mae=round(float(z.abs().mean()),4),
                rmse=round(float(np.sqrt(np.mean(np.square(z)))),4),
                median=round(float(z.median()),4),
                abs_gt5=int((z.abs()>5).sum()),
                abs_gt10=int((z.abs()>10).sum()))

def qc_summary(data):
    def label(x):
        return "MISSING" if pd.isna(x) else str(int(x)) if float(x).is_integer() else str(x)
    frame=data.copy()
    frame["consolidated_QC"]=frame.TA_F_QC.map(label)
    frame["MDS_QC"]=frame.TA_F_MDS_QC.map(label)
    print("ORIGINAL FULLSET TIME-IDENTITY CROSSTAB, QC LABELS ONLY:")
    print(pd.crosstab(frame.consolidated_QC,frame.MDS_QC,dropna=False).to_string())
    print("Original TA_F_QC distribution",frame.consolidated_QC.value_counts().to_dict())
    print("Original TA_F_MDS_QC distribution",frame.MDS_QC.value_counts().to_dict())

def residual_energy(q):
    r=(q.TA_ERA-q.TA_F).to_numpy(float)
    if not np.isfinite(r).all():
        raise ValueError("Original Ho1 QC0 temperature pair contains missing values")
    a=np.abs(r)
    s=np.square(r)
    total=s.sum()
    print("ORIGINAL QC0 TEMPERATURE RESIDUAL SQUARED-ERROR DECOMPOSITION:")
    for low,high,name in [
        (0,2,"[0,2) C"),(2,5,"[2,5) C"),(5,10,"[5,10) C"),
        (10,20,"[10,20) C"),(20,np.inf,"[20,infinity) C")
    ]:
        mask=(a>=low)&(a<high)
        print(name,"records",int(mask.sum()),
              "share_records_pct",round(float(100*mask.mean()),3),
              "share_total_squared_error_pct",round(float(100*s[mask].sum()/total),3))
    for cap in (5,10,20):
        kept=q.loc[a<=cap]
        print("DESCRIPTIVE RESIDUAL-SELECTED SUBSET |abs(ERA-QC0)| <=",cap,
              "C: n",len(kept),"RMSE",errors(kept)["rmse"],
              "(CANNOT infer true skill from selecting on outcome)")
    print("All-QC0 RMSE",errors(q)["rmse"],
          "AUXMETEO RELEASED ERA_RMSE=4.66 uses UNKNOWN fitting population")

def mds_qc0_identity(q):
    available=q.TA_F_MDS.notna()
    qc0=q.TA_F_MDS_QC.eq(0)
    same=available&(q.TA_F_MDS-q.TA_F).abs().le(ORIG_TOL)
    print("CONSOLIDATED QC0 vs MDS temperature identity:")
    print("consolidated QC0 total",len(q),
          "numeric MDS temperature",int(available.sum()),
          "MDS own quality flag=0",int(qc0.sum()),
          "measured_QC0 same within 0.001 C",int(same.sum()),
          "MDS own QC0 AND numeric identical",int((qc0&same).sum()),
          "MDS QC0 but numeric differs >0.001 C",
          int((qc0&available&~same).sum()),
          "MDS QC nonzero among consolidated QC0",
          int((q.TA_F_MDS_QC.notna()&~qc0).sum()))
    print("MDS minus consolidated-original QC0 stats:",errors(q,"TA_F_MDS","TA_F"))
    print("MDS QC0 intersections can share source data; not independent T.")

def held_mds(data,m):
    opts=argparse.Namespace(s11=m.S11,s19=m.S19,s20=m.S20,s21=m.S21)
    selected=m.gate(opts)
    selected["native"]=selected.local.dt.strftime("%Y%m%d%H%M")
    merge=selected.merge(data[["native","TA_F","TA_F_QC","TA_F_MDS",
                               "TA_F_MDS_QC","TA_ERA"]],
                         on="native",how="left",validate="one_to_one",
                         indicator=True)
    if len(merge)!=319 or not merge._merge.eq("both").all():
        raise ValueError("Unanchored 319 exact Stage39 records changed")
    if merge.local.dt.year.value_counts().sort_index().to_dict()!=HELD_COUNTS:
        raise ValueError("Original held annual counts changed")
    if not merge.TA_F_QC.eq(2).all() or not np.allclose(
            merge.TA_F,merge.TA_ERA,rtol=0,atol=ORIG_TOL):
        raise ValueError("Original 319 held no longer consolidated QC2 ERA")
    for year,g in merge.groupby(merge.local.dt.year,sort=True):
        print("HELD YEAR",year,"n",len(g),
              "MDS finite",int(g.TA_F_MDS.notna().sum()),
              "MDS quality distribution",
              g.TA_F_MDS_QC.value_counts(dropna=False).to_dict(),
              "MDS minus TA_ERA",errors(g,"TA_F_MDS","TA_ERA"))
    print("MDS gapfills do NOT constitute independent tower temperature observations")

def audit(st46,st45,st44,m,src):
    aux=st46.authenticated_aux(st45,st44,m)
    data=load_mds(src)
    q=data.loc[data.TA_F_QC.eq(0)].copy()
    if not np.isfinite(q[["TA_F","TA_ERA"]].to_numpy(float)).all():
        raise ValueError("All measured-coded original QC0 values must be numeric")
    if errors(q)["rmse"]!=7.7346 or len(q)!=EXPECTED_QC0:
        raise ValueError("Stage46 empirical QC0 RMSE/source scope did not reproduce")
    if aux["ERA_RMSE"]!="4.66" or aux["ERA_CORRELATION"]!="0.72":
        raise ValueError("Stage45 AUXMETEO original TA metadata differs")
    print("\n"+"="*107)
    print("STAGE47 | HO1 MDS/CONSOLIDATED ERA PROVENANCE AND RESIDUAL CONCENTRATION")
    print("Original FULLSET rows",len(data),"Ho1 measured-coded QC0",len(q))
    print("Original AUXMETEO ERA_RMSE",aux["ERA_RMSE"],"ERA_CORRELATION",aux["ERA_CORRELATION"])
    print("Stage46 empirical QC0-vs-distributed-downscaled-ERA RMSE",errors(q)["rmse"])
    print("="*107)
    qc_summary(data)
    mds_qc0_identity(q)
    residual_energy(q)
    print("\nQC0 YEARLY SECTIONS (measured-coded target vs distributed TA_ERA):")
    for year,g in q.groupby("year",sort=True):
        print("YEAR",int(year),
              "TA_F vs TA_ERA",errors(g),
              "MDS vs measured-coded TA_F",errors(g,"TA_F_MDS","TA_F"))
    print("\n1999 OCT–DEC QC0 MONTHLY MDS/QC CONSISTENCY:")
    for month,g in q.loc[q.year.eq(1999)].groupby("month",sort=True):
        print("MONTH",int(month),"n",len(g),
              "MDS-QC labels",g.TA_F_MDS_QC.value_counts(dropna=False).to_dict(),
              "QC0 vs ERA",errors(g),
              "QC0 vs MDS",errors(g,"TA_F_MDS","TA_F"))
    print("\n319 HELD ORIGINAL QC2 CASES:")
    held_mds(data,m)
    print("\nNO ORIGINAL RAW ERA FIT WINDOW OR SENSOR PROVENANCE RECONSTRUCTED.")
    print("Official FLUXNET describes TA_F_MDS_QC 0 as measured and 1-3 as MDS")
    print("gapfill qualities; all distributed TA products share processing history.")
    print("AUXMETEO fit RMSE cannot be equated to empirical QC0 RMSE without")
    print("matching original calibration population and statistical definition.")
    print("Original 4,884 Stage08 Batch02 records remain SCIENTIFIC HOLD, approvals=0.")
    print("READ ONLY | NO FILES WRITTEN; no source/forcing/NetCDF/DATM/CIME/Slurm changes")

def selftest():
    sample=pd.DataFrame({
        "TA_F":[1.,3.,6.,8.],
        "TA_ERA":[1.,7.,2.,10.],
        "TA_F_MDS":[1.,3.,5.,8.],
        "TA_F_QC":[0.,0.,0.,2.],
        "TA_F_MDS_QC":[0.,0.,1.,2.],
        "year":[1999]*4,
        "month":[11]*4
    })
    q=sample.loc[sample.TA_F_QC.eq(0)]
    assert errors(q)["n"]==3
    assert errors(q)["mae"]==round(8/3,4)
    assert (q.TA_F_MDS-q.TA_F).abs().le(.001).sum()==2
    # Every temperature series remains related, not independent evidence.
    assert sample.loc[sample.TA_F_QC.eq(2),"TA_F_MDS_QC"].iloc[0]==2
    print("STAGE47 SELF-TEST PASS | MDS QC origin, 0.001-C identity, error bins")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    opt=ap.add_mutually_exclusive_group(required=True)
    opt.add_argument("--self-test",action="store_true")
    opt.add_argument("--check",action="store_true")
    opt.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        selftest()
        return
    st46=pinned_parent()
    st45=st46.load_stage45()
    st44=st45.load_stage44()
    m,p,control,feb=st44.prior()
    if len(control)!=EXPECTED_1999_QC0 or len(feb)!=25:
        raise ValueError("Earlier Stage43 1999 controls and FEB cohort changed")
    src=st46.source_gate(st45,st44,m)
    if args.check:
        print("STAGE47 CHECK PASS | staged script/SHA256 source gates, no network/writes")
        return
    audit(st46,st45,st44,m,src)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage46 | Recompute Ho1 observed-coded QC0 / downscaled TA_ERA fit diagnostics.

READ-ONLY provenance diagnostic. Stage45 authenticated a 32-row AUXMETEO table
inside the ORIGINAL Ho1 FULLSET ZIP, TA metadata:
  ERA_SLOPE=1.00, ERA_INTERCEPT=-0.00,
  ERA_RMSE=4.66, ERA_CORRELATION=0.72.
Published values are rounded to 2 decimals, TIME=-9999 is metadata (not
a valid observation timestamp), and the fitting/calibration period is unknown.

This script computes a *new* empirical pairing of available ORIGINAL Ho1
measured-coded TA_F_QC=0 records with the distributed downscaled TA_ERA,
stratified by year and with focused Oct-Dec 1999 details. It checks
whether the empirical QC0-vs-TA_ERA RMSE, Pearson r and regression of
TA_F on TA_ERA are numerically like the AUXMETEO metadata. It does NOT
assume this reproduces FLUXNET's regression or that the released original
ERA reanalysis input is reconstructible from TA_ERA.

3 modes:
  --self-test  Synthetic regressions only; no access to scientific files.
  --check      Pinned Stage45 and Stage08/19/20/21... source gates + ZIP
               member provenance; no full observational recomputation.
  --audit      additionally verifies exact ZIP SHA256, FULLSET_HH member SHA,
               original 1,002-byte AUXMETEO SHA and analyses native QC0 rows.

All outputs are stdout ONLY. NO downloaded data, no files created/extracted,
no changes to forcing, NetCDF, DATM, CIME, Slurm, or approved repairs.
All Batch02 4,884 records remain SCIENTIFIC HOLD.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

ST45_FILE="45_audit_Ho1_AUXMETEO_metadata_provenance.py"
ST45_GIT_BLOB="98bc24b94421e922e153694914674b824bb1eedd"
EXPECTED_ALL_HO1_ROWS=490896
EXPECTED_ALL_QC0=274148
EXPECTED_1999_QC0=3005
EXPECTED_QC0_MONTHS_1999={10:77,11:1440,12:1488}
EXPECTED_HO1_HELD={1998:64,1999:25,2001:230}
EXPECTED_TA_METADATA={
    "ERA_SLOPE":"1.00",
    "ERA_INTERCEPT":"-0.00",
    "ERA_RMSE":"4.66",
    "ERA_CORRELATION":"0.72",
}

def git_blob(path):
    x=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def load_stage45():
    p=Path(__file__).resolve().with_name(ST45_FILE)
    if not p.is_file():
        raise FileNotFoundError("Download pinned Stage39-45 Python sources alongside Stage46")
    actual=git_blob(p)
    if actual!=ST45_GIT_BLOB:
        raise ValueError("Stage45 source Git blob differs: "+actual)
    spec=importlib.util.spec_from_file_location("batch02_verified_stage45",p)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import pinned Stage45")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("PREREQUISITE STAGE45 SOURCE VERIFIED",actual,flush=True)
    return mod

def diagnostics(q):
    """Direct matched original TA_F measured-coded vs processed TA_ERA.
    These are descriptive statistics only and not proof of original fit."""
    if q.empty:return dict(n=0)
    a=q[["TA_F","TA_ERA"]].apply(pd.to_numeric,errors="coerce")
    valid=np.isfinite(a.TA_F.to_numpy())&np.isfinite(a.TA_ERA.to_numpy())
    a=a.loc[valid]
    if a.empty:return dict(n=0)
    x=a.TA_ERA.to_numpy(float)
    y=a.TA_F.to_numpy(float)
    error=x-y
    out=dict(n=len(a),
       mean_era_minus_observed_C=round(float(error.mean()),4),
       median_era_minus_observed_C=round(float(np.median(error)),4),
       rmse_C=round(float(np.sqrt(np.mean(error*error))),4),
       mae_C=round(float(np.mean(np.abs(error))),4),
       abs_gt10C=int(np.sum(np.abs(error)>10)),
       abs_gt5C=int(np.sum(np.abs(error)>5)))
    if len(a)>=3 and np.std(x)>1e-10 and np.std(y)>1e-10:
        slope,intercept=np.polyfit(x,y,1)  # measured = slope*distributed_ERA + intercept
        out["r_ERA_vs_measured"]=round(float(np.corrcoef(x,y)[0,1]),5)
        out["ols_slope_measured_on_downscaled_ERA"]=round(float(slope),5)
        out["ols_intercept_measured_on_downscaled_ERA_C"]=round(float(intercept),5)
    return out

def source_gate(st45,st44,m):
    orig=st44.source_path(m)
    if st44.sha_file(orig)!=st45.PINNED_HH_SHA256:
        raise ValueError("Stage08 original Ho1 FULLSET HH source SHA256 changed")
    zf,hh,era,aux=st44.zip_info()
    try:
        if aux.file_size!=st45.AUX_SIZE or aux.CRC!=st45.AUX_CRC32:
            raise ValueError("Stage45 original AUXMETEO member identity changed")
        print("STAGE46 OFFLINE SOURCE GATE PASS | pinned Ho1 HH and AUXMETEO ZIP identity")
    finally:
        zf.close()
    return orig

def authenticated_aux(st45,st44,m):
    orig=st44.source_path(m)
    if st44.sha_file(st44.ZIP_PATH)!=st45.OBSERVED_ZIP_SHA256:
        raise ValueError("Original full ZIP differs from Stage44 observed SHA256")
    zf,hh,era,aux=st44.zip_info()
    try:
        if st44.sha_member(zf,hh)!=st45.PINNED_HH_SHA256:
            raise ValueError("Original FULLSET_HH archived member not Stage08 source")
        if aux.file_size!=st45.AUX_SIZE or aux.CRC!=st45.AUX_CRC32:
            raise ValueError("AUXMETEO metadata file size/CRC differ")
        with zf.open(aux,"r") as f:
            raw=f.read(st45.MAX_AUX_BYTES+1)
        if len(raw)!=st45.AUX_SIZE:
            raise ValueError("AUXMETEO uncompressed byte count differs")
        hh_sha=st44.sha_file(orig)
        if hh_sha!=st45.PINNED_HH_SHA256:
            raise ValueError("Original site HH SHA no longer verified")
        checksum=hashlib.sha256(raw).hexdigest()
        if checksum!="95b858307606a1db67b59b68021047650be5910b599128a9a23ae25c5a9a5b8f":
            raise ValueError("AUXMETEO Stage45 observed SHA256 changed")
        records=st45.aux_rows(raw)
        ta=[r for r in records if r["VARIABLE"]=="TA"]
        if len(records)!=32 or len(ta)!=4 or len(set(r["PARAMETER"] for r in ta))!=4:
            raise ValueError("Original 32-row AUXMETEO or 4-row TA metadata changed")
        observed={r["PARAMETER"]:r["VALUE"] for r in ta}
        if observed!=EXPECTED_TA_METADATA or any(r["TIMESTAMP"]!="-9999" for r in ta):
            raise ValueError("Released AUXMETEO TA summary values/time tag differ")
        print("STAGE46 ORIGINAL AUXMETEO SHA256 VERIFIED",checksum)
        print("AUXMETEO TA summary: ",observed,"TIMESTAMP=-9999")
        return observed
    finally:
        zf.close()

def original_temperature_rows(src):
    a=pd.read_csv(src,usecols=["TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA"],
                  dtype={"TIMESTAMP_START":str})
    if len(a)!=EXPECTED_ALL_HO1_ROWS:
        raise ValueError("Ho1 native row count differs from Stage39")
    a["native"]=a.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True)
    if a.native.duplicated().any() or not a.native.is_monotonic_increasing:
        raise ValueError("Ho1 timestamps duplicate or not chronological")
    a["year"]=a.native.str.slice(0,4).astype(int)
    a["month"]=a.native.str.slice(4,6).astype(int)
    for field in ("TA_F","TA_ERA","TA_F_QC"):
        a[field]=pd.to_numeric(a[field],errors="coerce")
        a.loc[a[field]<=-9990,field]=np.nan
    count=int(a.TA_F_QC.eq(0).sum())
    if count!=EXPECTED_ALL_QC0:
        raise ValueError("Original Ho1 measured QC0 count differs: "+str(count))
    q=a.loc[a.TA_F_QC.eq(0),["year","month","native","TA_F","TA_ERA"]].copy()
    if q[["TA_F","TA_ERA"]].isna().any().any():
        raise ValueError("Original Ho1 measured-coded QC0 contains missing T or ERA")
    s=q.loc[q.year.eq(1999)]
    if len(s)!=EXPECTED_1999_QC0 or s.month.value_counts().sort_index().to_dict()!=EXPECTED_QC0_MONTHS_1999:
        raise ValueError("Stage41 1999 QC0 seasonal coverage differs")
    if q.loc[q.year.isin([1998,2001])].shape[0]!=0:
        raise ValueError("Original Ho1 measured QC0 now available in 1998/2001; review")
    return a,q

def target_gate(m,a):
    opts=argparse.Namespace(s11=m.S11,s19=m.S19,s20=m.S20,s21=m.S21)
    focus=m.gate(opts)
    focus["native"]=focus.local.dt.strftime("%Y%m%d%H%M")
    x=focus.merge(a[["native","TA_F_QC","TA_F","TA_ERA"]],
                  on="native",how="left",validate="one_to_one",indicator=True)
    if len(x)!=319 or not x._merge.eq("both").all():
        raise ValueError("Original 319 target timestamps do not match Ho1 HH")
    if not x.TA_F_QC.eq(2).all() or not np.allclose(x.TA_F,x.TA_ERA,
                                                  atol=0.001,rtol=0):
        raise ValueError("Original 319 QC2 ERA replacement premise changed")
    if x.local.dt.year.value_counts().sort_index().to_dict()!=EXPECTED_HO1_HELD:
        raise ValueError("Original 319 yearly targets changed")
    print("STAGE46 VERIFIED 319 anomalies: Ho1 original TA_F_QC=2, TA_F equals TA_ERA")
    return x

def audit(st45,st44,m,source):
    aux=authenticated_aux(st45,st44,m)
    original,observed=original_temperature_rows(source)
    focus=target_gate(m,original)
    print("\n"+"="*106)
    print("STAGE46 | ORIGINAL Ho1 QC0 / distributed TA_ERA DIAGNOSTIC vs AUXMETEO")
    print("Original Ho1 rows",len(original),"QC0 measured-coded",len(observed))
    print("Printed AUXMETEO parameters are two-decimal summaries; their original")
    print("calibration population / fitting direction has NOT been established.")
    print("="*106)
    total=diagnostics(observed)
    print("ALL ORIGINAL MEASURED-CODED QC0 PAIRS:",total)
    print("RELEASED AUXMETEO TA RMSE:",aux["ERA_RMSE"],
          "CORRELATION:",aux["ERA_CORRELATION"],
          "SLOPE:",aux["ERA_SLOPE"],"INTERCEPT:",aux["ERA_INTERCEPT"])
    print("\nQC0 PAIRS BY YEAR (DO NOT CONFLATE WITH ORIGINAL REGRESSION FIT WINDOW):")
    for yr,g in observed.groupby("year",sort=True):
        print("YEAR",int(yr),diagnostics(g))
    print("\n1999 ORIGINAL QC0 OCT–DEC MONTH DETAILS:")
    for month,g in observed.loc[observed.year.eq(1999)].groupby("month"):
        print("1999 MONTH",int(month),diagnostics(g))
    print("\n1999 FEBRUARY anomalous Ho1 QC2 records n",int(focus.local.dt.year.eq(1999).sum()))
    print("1998 / 2001 anomalous-year local measured-coded QC0 counts: both zero.")
    print("\nIMPORTANT: New OLS fit uses the released, already downscaled TA_ERA as")
    print("predictor and TA_F_QC0 as measured-coded response; this regression")
    print("CANNOT reconstruct the original raw ERA input or prove the original")
    print("FLUXNET fitting interval, coefficient fallback, or raw sensor quality.")
    print("Do NOT attribute site anomalies to coefficients without BASE/BADM")
    print("instrument, measured-data provenance and original pipeline metadata.")
    print("319 Ho1 physical blockers and 4,884 Batch02 targets remain SCIENTIFIC HOLD.")
    print("NO FILE WRITES / NO FORCING, NetCDF, DATM, CIME, SLURM, OR APPROVAL.")

def selftest():
    f=pd.DataFrame({"TA_F":[1.,3.,5.],"TA_ERA":[2.,4.,6.]})
    z=diagnostics(f)
    assert z["n"]==3 and z["rmse_C"]==1.0 and z["mae_C"]==1.0
    assert z["r_ERA_vs_measured"]==1.0
    assert z["ols_slope_measured_on_downscaled_ERA"]==1.0
    assert z["ols_intercept_measured_on_downscaled_ERA_C"]==-1.0
    g=pd.DataFrame({"TA_F":[1.],"TA_ERA":[4.]})
    assert diagnostics(g)["n"]==1
    assert "r_ERA_vs_measured" not in diagnostics(g)
    print("STAGE46 SELF-TEST PASS | independent QC0-vs-ERA RMSE, correlation,")
    print("regression orientation and insufficient-observation controls")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    flags=ap.add_mutually_exclusive_group(required=True)
    flags.add_argument("--self-test",action="store_true")
    flags.add_argument("--check",action="store_true")
    flags.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        selftest()
        return
    st45=load_stage45()
    st44=st45.load_stage44()
    m,p,control,feb=st44.prior()  # pins stage43->stage39 + sources
    if len(control)!=EXPECTED_1999_QC0 or len(feb)!=25:
        raise ValueError("Stage43 original 1999 control or February scope differs")
    src=source_gate(st45,st44,m)
    if args.check:
        print("STAGE46 CHECK PASS | ORIGINAL SHA pinned, no network/writes/approvals")
        return
    audit(st45,st44,m,src)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage44 | Ho1 FULLSET ZIP ERA5_HH / AUXMETEO provenance (READ ONLY).

Audit the original 149,847,335-byte US-Ho1 FLUXNET FULLSET ZIP found in
Stage38, especially its _ERA5_HH_ and _AUXMETEO_ members. Distinguish an
upstream ERA5 grid field from an already site-calibrated/downscaled FLUXNET
ERA companion: do NOT infer provenance from the string "ERA5" in a filename.

Stage39/40/41/42/43 source identities and Stage08/19/20/21 original-input
SHA256 gates must pass first. Stage43 QC0=3005/FEB QC2=25 gates are reused.
For full --audit, also byte-hash the ZIP HH member and compare to Stage08
pinned extracted original HH source. Then scan the ERA5_HH CSV inside ZIP
directly (no extraction), inspect its temperature columns and, ONLY if it
contains TIMESTAMP_START and TA_ERA, compare with original Ho1 TA_ERA on
matched native timestamps in 1998/1999/2001, including the 319 held cases.

An ERA5_HH TA_ERA matching FULLSET_HH is a duplicate processed product,
NOT independent original grid ERA5. Unknown headers do not get guessed.
ZIP archive SHA256 is first observed here, not a Stage08 ledger input.

Modes: --self-test (synthetic in-memory CSV), --check (offline source + ZIP
headers), --audit (offline full ZIP provenance, streaming one ERA5_HH
member). NO network access, NO file creation/writes, no model, forcing,
NetCDF, DATM, CIME, Slurm or scientific approval.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

ST43_NAME = "43_audit_Ho1_1999_QC0_vs_two_ERA_Bangor.py"
ST43_BLOB = "b0289cd15f0057b32b1c436f0453a266dfe96229"
ZIP_PATH = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/"
    "US-Ho1/forcing/packages/AMF_US-Ho1_FLUXNET_FULLSET_1996-2023_3-6.zip"
)
ZIP_EXPECTED_BYTES = 149847335
YEARS = {1998,1999,2001}
EXPECTED_UNANCHORED = {1998:64,1999:25,2001:230}
MAX_ERA5_UNCOMPRESSED = 1200 * 1024 * 1024
MAX_ERA5_ROWS = 1500000
MAX_YEAR_ROWS = 18000

def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def sha_member(zf,info):
    h = hashlib.sha256()
    with zf.open(info,"r") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def git_blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()

def prior():
    path=Path(__file__).resolve().with_name(ST43_NAME)
    if not path.is_file():
        raise FileNotFoundError("Download pinned Stage39-43 beside Stage44")
    actual=git_blob(path)
    if actual!=ST43_BLOB:
        raise ValueError("Stage43 Git blob mismatch "+actual+
                         " expected "+ST43_BLOB)
    spec=importlib.util.spec_from_file_location("batch02_stage43",path)
    if spec is None or spec.loader is None:
        raise ValueError("Stage43 prerequisite import failed")
    parent=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    print("STAGE43 SCRIPT GIT BLOB VERIFIED",actual,flush=True)
    t42=parent.stage42_module()
    m,p,_,control,feb=parent.gate(t42)
    if len(control)!=3005 or len(feb)!=25:
        raise ValueError("Pinned Stage43 1999 cohort size changed")
    return m,p,control,feb

def source_path(m):
    m11=json.loads((m.S11/"manifest.json").read_text())
    ledger=json.loads(
        (Path(m11["source_stage08"])/"exact_input_manifest.json").read_text()
    )
    matches=[r for r in ledger["sites"] if r["site"]=="US-Ho1"]
    if len(matches)!=1:
        raise ValueError("Original Stage08 US-Ho1 unique source not found")
    path=m.verify(
        matches[0]["primary"],ledger["input_sha256"],"US-Ho1 original FULLSET HH"
    )
    return path

def select_members(zf):
    infos=zf.infolist()
    if len(infos)!=12:
        raise ValueError("Expected Stage38 ZIP inventory of 12 original members")
    def get(token):
        selected=[i for i in infos if token in i.filename.upper()
                  and i.filename.lower().endswith(".csv")
                  and not i.is_dir()]
        if len(selected)!=1:
            raise ValueError("Expected one original ZIP member matching "+token+
                             "; found "+str([i.filename for i in selected]))
        return selected[0]
    hh=get("_FULLSET_HH_")
    era=get("_ERA5_HH_")
    aux=get("_AUXMETEO_")
    return hh,era,aux

def header_preview(zf,member,n=2):
    with zf.open(member,"r") as h:
        text=io.TextIOWrapper(h,encoding="utf-8-sig",newline="")
        csvrows=csv.reader(text)
        header=next(csvrows,None)
        if not header:
            raise ValueError("Empty ZIP CSV member "+member.filename)
        if len(header)!=len(set(header)):
            raise ValueError("Duplicated CSV column names in "+member.filename)
        examples=[]
        for _ in range(n):
            sample=next(csvrows,None)
            if sample is None:break
            examples.append(sample)
    return header,examples

def parse_era_csv(stream,allow_empty=True):
    """Scan ERA5_HH stream without writing it; return selected years only.

    If native timestamp column is not START, do not automatically join
    same-named clock times to original FULLSET's TIMESTAMP_START.
    """
    wrapper=io.TextIOWrapper(stream,encoding="utf-8-sig",newline="")
    reader=csv.DictReader(wrapper)
    columns=reader.fieldnames or []
    if not columns or len(columns)!=len(set(columns)):
        raise ValueError("Missing/duplicate original ERA5_HH CSV headers")
    stamp=next((f for f in ("TIMESTAMP_START","TIMESTAMP","TIMESTAMP_END")
                if f in columns),None)
    ta_candidates=[f for f in columns if
                   f.upper()=="TA" or f.upper().startswith("TA_") or
                   f.lower() in ("t2m","temperature")]
    print("ERA5_HH ORIGINAL CSV HEADERS",columns[:70])
    print("ERA5_HH TEMPERATURE-LIKE HEADERS",ta_candidates)
    print("ERA5_HH TIMESTAMP COLUMN",stamp,"(no implicit UTC/START conversion)")
    selected=[]
    count=0
    invalid=0
    year_count={year:0 for year in YEARS}
    for rec in reader:
        count+=1
        if count>MAX_ERA5_ROWS:
            raise ValueError("ERA5_HH scanned rows exceed hard safety cap")
        if stamp is None:continue
        raw=(rec.get(stamp) or "").strip().replace(".0","")
        if len(raw)!=12 or not raw.isdigit():
            invalid+=1
            if invalid>5:
                raise ValueError("ERA5_HH invalid native timestamp strings")
            continue
        year=int(raw[:4])
        if year not in YEARS:continue
        year_count[year]+=1
        if year_count[year]>MAX_YEAR_ROWS:
            raise ValueError("ERA5_HH target year exceeds expected HH bounds")
        if "TA_ERA" in columns:
            t=rec.get("TA_ERA","")
            try:value=float(t)
            except (TypeError,ValueError):value=float("nan")
            if not np.isfinite(value) or value<=-9990:
                value=float("nan")
            selected.append((raw,value))
    print("ERA5_HH TOTAL CSV ROWS",count,"target year rows",year_count,
          "malformed stamps",invalid)
    return dict(columns=columns,stamp=stamp,ta_candidates=ta_candidates,
                year_counts=year_count,total=count,
                values=pd.DataFrame(selected,columns=["native","companion_TA_ERA"]))

def zip_info():
    if not ZIP_PATH.is_file():
        raise FileNotFoundError("Stage38 Ho1 FULLSET ZIP not found: "+str(ZIP_PATH))
    size=ZIP_PATH.stat().st_size
    if size!=ZIP_EXPECTED_BYTES:
        raise ValueError("Stage38 Ho1 ZIP size changed: "+str(size)+
                         " expected "+str(ZIP_EXPECTED_BYTES))
    zf=zipfile.ZipFile(ZIP_PATH,"r")
    try:
        hh,era,aux=select_members(zf)
        if era.file_size>MAX_ERA5_UNCOMPRESSED:
            raise ValueError("ERA5_HH uncompressed member beyond read-only cap")
        print("FULLSET ORIGINAL ZIP",ZIP_PATH,"size",size,"members",len(zf.infolist()))
        for x in (hh,era,aux):
            print("ZIP MEMBER",x.filename,"uncompressed",x.file_size,
                  "compressed",x.compress_size,"CRC32",hex(x.CRC))
            fields,examples=header_preview(zf,x)
            print("  HEADER COLUMNS",len(fields),"names",fields[:75])
            print("  TEMPERATURE-RELATED",[
                col for col in fields
                if "TA" in col.upper() or "TEMP" in col.upper()
            ][:35])
            # Avoid emitting thousands of raw fields; first row timestamp only.
            if examples:print("  first TIMESTAMP raw",examples[0][0])
        return zf,hh,era,aux
    except BaseException:
        zf.close()
        raise

def original_era(m,raw_source):
    fields=["TIMESTAMP_START","TA_ERA","TA_F","TA_F_QC"]
    src=pd.read_csv(raw_source,usecols=fields,dtype={"TIMESTAMP_START":str})
    src["native"]=src.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True
    )
    src=src.loc[src.native.str.slice(0,4).isin(
        [str(year) for year in YEARS])].copy()
    if src.native.duplicated().any():
        raise ValueError("Duplicated Ho1 FULLSET native timestamps")
    for col in ("TA_ERA","TA_F","TA_F_QC"):
        src[col]=pd.to_numeric(src[col],errors="coerce")
        src.loc[src[col]<=-9990,col]=np.nan
    print("Ho1 original source year counts",
          src.native.str.slice(0,4).value_counts().sort_index().to_dict())
    return src

def comparison(m,src,parsed):
    if parsed["stamp"]!="TIMESTAMP_START" or "TA_ERA" not in parsed["columns"]:
        print("NO DIRECT TA_ERA comparison: companion TIME definition or")
        print("temperature field differs. Inspect inventory; do not infer alias.")
        return
    era=parsed["values"]
    if era.empty or era.native.duplicated().any():
        raise ValueError("Companion TA_ERA not available/unique on selected years")
    joined=src.merge(era,on="native",how="inner",validate="one_to_one")
    if joined.empty:
        raise ValueError("ERA5_HH timestamp intersection is empty")
    if joined.TA_ERA.notna().sum()==0 or joined.companion_TA_ERA.notna().sum()==0:
        raise ValueError("No numeric original vs companion TA_ERA values")
    print("EXACT TIMESTAMP_START ALIAS COMPARISON; BOTH MAY BE DOWN-SCALED")
    for year,g in joined.groupby(joined.native.str.slice(0,4),sort=True):
        valid=g.TA_ERA.notna() & g.companion_TA_ERA.notna()
        z=g.loc[valid]
        e=z.companion_TA_ERA-z.TA_ERA
        print("YEAR",year,"joined",len(g),"numeric both",len(z),
              "exact-within-0.001C",int(e.abs().le(.001).sum()),
              "MAE",round(float(e.abs().mean()),5),
              "median",round(float(e.median()),5),
              "max_abs",round(float(e.abs().max()),5))
        for qc,q in z.groupby("TA_F_QC"):
            diff=(q.companion_TA_ERA-q.TA_ERA).abs()
            print("  Ho1 source TA_F_QC",qc,"n",len(q),
                  "companion_vs_ho1ERA_MAE",round(float(diff.mean()),5))
    # Exact 319 fixed anomalous targets from pinned Stage39 (no new science).
    options=argparse.Namespace(s11=m.S11,s19=m.S19,s20=m.S20,s21=m.S21)
    missing=m.gate(options)
    missing["native"]=missing.local.dt.strftime("%Y%m%d%H%M")
    focus=missing.merge(joined,on="native",how="left",validate="one_to_one",
                        indicator=True)
    if len(focus)!=319:
        raise ValueError("Stage39 319 unanchored focus lost")
    print("STAGE39 319 TARGETS WITH SAME-TIME ERA5_HH companion:",
          int(focus._merge.eq("both").sum()),"/319")
    for year,g in focus.groupby("year",sort=True):
        d=g.companion_TA_ERA-g.TA_ERA
        d=d.dropna()
        print("HELD_YEAR",year,"joined_valid",len(d),
              "same_to_0.001C",int(d.abs().le(.001).sum()),
              "median_companion_minus_Ho1_TA_ERA",
              round(float(d.median()),5) if len(d) else "UNAVAILABLE",
              "MAE",round(float(d.abs().mean()),5) if len(d) else "UNAVAILABLE")
    total=(joined.companion_TA_ERA-joined.TA_ERA).dropna()
    print("OVERLAP 3 YEARS matched aliases; total",len(total),
          "fraction within .001C",round(float(total.abs().le(.001).mean()),6))
    print("An identical file-level TA_ERA series indicates shared processed")
    print("downscaled data, NOT validation by uncalibrated original ERA5.")

def selftest():
    synthetic=("TIMESTAMP_START,TA_ERA,SW_IN_ERA\n"
               "199811210430,-1.2,0\n"
               "199902130100,-12.561,3\n"
               "200112140100,-5.0,4\n"
               "200201010000,0,0\n").encode("utf-8")
    a=parse_era_csv(io.BytesIO(synthetic))
    assert a["stamp"]=="TIMESTAMP_START"
    assert len(a["values"])==3
    assert a["year_counts"]=={1998:1,1999:1,2001:1}
    assert abs(a["values"].iloc[1].companion_TA_ERA+12.561)<1e-8
    odd=("TIMESTAMP_END,TA_ERA\n199901010030,3.0\n").encode()
    b=parse_era_csv(io.BytesIO(odd))
    assert b["stamp"]=="TIMESTAMP_END"
    print("STAGE44 SELF-TEST PASS | streaming CSV, year selection,")
    print("native timestamp semantics and no automatic END/START alias")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        return
    m,p,control,feb=prior()
    original=source_path(m)
    print("ORIGINAL HH SHA256 VERIFIED",original.name,sha_file(original))
    zipfile_handle,hh,era,aux=zip_info()
    try:
        if args.check:
            print("STAGE44 CHECK PASS; metadata-only; no archive extraction,")
            print("no network, no file writes and no model jobs.")
            return
        sha_archive=sha_file(ZIP_PATH)
        sha_extracted=sha_file(original)
        sha_zip_hh=sha_member(zipfile_handle,hh)
        print("ORIGINAL ARCHIVE SHA256 (NEW UNPINNED SOURCE):",sha_archive)
        print("ZIP HH MEMBER SHA256:",sha_zip_hh)
        print("STAGE08 ORIGINAL EXTRACTED HH SHA256:",sha_extracted)
        if sha_zip_hh!=sha_extracted:
            raise ValueError("ZIP FULLSET_HH differs from Stage08 verified source")
        print("ZIP HH / Stage08 extracted original FULLSET_HH BYTE IDENTITY PASS")
        with zipfile_handle.open(era,"r") as stream:
            parsed=parse_era_csv(stream)
        src=original_era(m,original)
        comparison(m,src,parsed)
        print("STAGE44 SCIENCE AUDIT DONE. AUXMETEO/ERA5_HH source metadata")
        print("MUST be checked before calling any column uncalibrated ERA5.")
        print("All 4,884 Batch02 records HOLD, zero approved forcing changes.")
        print("READ ONLY: NO SOURCE, FORCING, NETCDF, DATM, CIME OR SLURM CHANGES")
    finally:
        zipfile_handle.close()

if __name__=="__main__":
    main()

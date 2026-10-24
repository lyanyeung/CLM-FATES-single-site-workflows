#!/usr/bin/env python3
"""Stage45 | US-Ho1 original AUXMETEO processing-parameter provenance (READ ONLY).

Stage44 established byte-for-byte identity of FULLSET_HH and ERA5_HH TA_ERA
at 52,560 half-hours in 1998, 1999, 2001, including all 319 held anomaly
timestamps. Hence _ERA5_HH is not an independent temperature check.

Inspect the original, 1,002-byte _AUXMETEO_ CSV in the SHA256-observed
original 149,847,335-byte Ho1 FULLSET ZIP. Report EXACT metadata rows with
ID, VARIABLE, PARAMETER, VALUE, TIMESTAMP, while neither inventing regression
units nor inferring meaning from column/parameter names. Group TA-related
rows and other variable labels for later source documentation assessment.

Prerequisite Stage44 Git blob SHA1 is fixed; it checks Stage43, Stage42,
Stage41, Stage40, Stage39, Stage08/19/20/21 lineages. Only --audit reads
AUXMETEO bytes and original ZIP SHA256, all INTO MEMORY. Does not download,
extract, write any files, alter temperature/dewpoint, start simulations,
modify CIME/DATM/NetCDF/Slurm, or approve scientific repairs.

--self-test: synthetic AUXMETEO parser only, fully offline.
--check: original sources / ZIP metadata gates, no file writes.
--audit: repeat gates, SHA256 ZIP, FULLSET_HH member, read AUXMETEO only.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
from collections import Counter
from pathlib import Path
import sys

sys.dont_write_bytecode=True

ST44_NAME="44_audit_Ho1_FLUXNET_ERA5_companion_provenance.py"
ST44_BLOB="3d0cbf981eafe192c0bbac1b1887a33c092812ea"
OBSERVED_ZIP_SHA256="2be21ee2c3b45f0c405e6eb33ef656b72d0ead9d6488f18782bcb78e07155e53"
PINNED_HH_SHA256="519a3376161fc58ff0d9534de0b1f92a2460a8a2069b45cfb2254bb8f3b7655f"
AUX_SIZE=1002
AUX_CRC32=0x03a6a839
AUX_REQUIRED=["ID","VARIABLE","PARAMETER","VALUE","TIMESTAMP"]
MAX_AUX_BYTES=1024*1024

def git_blob(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load_stage44():
    p=Path(__file__).resolve().with_name(ST44_NAME)
    if not p.is_file():
        raise FileNotFoundError("Download original pinned Stage39-44 scripts next to Stage45")
    actual=git_blob(p)
    if actual!=ST44_BLOB:
        raise ValueError("Stage44 script Git blob differs: "+actual+" expected "+ST44_BLOB)
    spec=importlib.util.spec_from_file_location("batch02_stage44_pinned",p)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot import verified Stage44")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("STAGE44 SCRIPT PIN VERIFIED",actual,flush=True)
    return mod

def aux_rows(content):
    if len(content)>MAX_AUX_BYTES:
        raise ValueError("AUXMETEO data exceeds safety limit")
    decoded=content.decode("utf-8-sig",errors="strict")
    reader=csv.DictReader(io.StringIO(decoded))
    header=reader.fieldnames or []
    if header!=AUX_REQUIRED:
        raise ValueError("Unexpected original AUXMETEO header: "+repr(header))
    rows=[]
    for i,row in enumerate(reader,1):
        if i>5000:
            raise ValueError("AUXMETEO row safety limit exceeded")
        if None in row or set(row)!=set(AUX_REQUIRED):
            raise ValueError("Malformed CSV AUXMETEO row "+str(i))
        if all((row.get(k) or "").strip()=="" for k in AUX_REQUIRED):
            continue
        rows.append({k:(row.get(k) or "").strip() for k in AUX_REQUIRED})
    if not rows:
        raise ValueError("AUXMETEO contains no metadata rows")
    return rows

def inspect(m,st44,audit):
    original=st44.source_path(m)  # original Stage08 ledger SHA256 checked
    if st44.sha_file(original)!=PINNED_HH_SHA256:
        raise ValueError("Stage08 HH source SHA256 has changed")
    zf,hh,era,aux=st44.zip_info()
    try:
        if aux.file_size!=AUX_SIZE or aux.CRC!=AUX_CRC32:
            raise ValueError("Original AUXMETEO 1002-byte member size/CRC changed")
        print("STAGE45 ORIGINAL AUXMETEO MEMBER",aux.filename,
              "bytes",aux.file_size,"CRC32",hex(aux.CRC))
        if not audit:
            print("STAGE45 CHECK PASS | read-only ZIP inventory and original source checks")
            return
        zhash=st44.sha_file(st44.ZIP_PATH)
        if zhash!=OBSERVED_ZIP_SHA256:
            raise ValueError("Whole original ZIP SHA256 differs from Stage44 observed release")
        hhhash=st44.sha_member(zf,hh)
        if hhhash!=PINNED_HH_SHA256:
            raise ValueError("ZIP HH member differs from Stage08 original HH")
        with zf.open(aux,"r") as stream:
            data=stream.read(MAX_AUX_BYTES+1)
        if len(data)!=AUX_SIZE:
            raise ValueError("AUXMETEO member decompressed byte count changed")
        meta=aux_rows(data)
        print("\n"+"="*100)
        print("STAGE45 | ORIGINAL US-Ho1 FLUXNET AUXMETEO PARAMETERS")
        print("FULL ZIP SHA256",zhash)
        print("ORIGINAL FULLSET_HH SHA256",hhhash)
        print("AUXMETEO SHA256",hashlib.sha256(data).hexdigest())
        print("Original CSV field names",AUX_REQUIRED)
        print("AUXMETEO DATA ROWS",len(meta))
        print("VARIABLE COUNTS",dict(Counter(r["VARIABLE"] for r in meta)))
        print("PARAMETER COUNTS",dict(Counter(r["PARAMETER"] for r in meta)))
        print("\nALL SOURCE METADATA ROWS (verbatim CSV field values):")
        for i,rec in enumerate(meta,1):
            print("ROW",i," | ".join(k+"="+repr(rec[k]) for k in AUX_REQUIRED))
        print("\nTA / AIR TEMPERATURE RELATED ROWS (names only; interpretation pending):")
        ta=[r for r in meta if
            "TA" in r["VARIABLE"].upper() or
            "TEMP" in r["VARIABLE"].upper() or
            "TA" in r["PARAMETER"].upper() or
            "TEMP" in r["PARAMETER"].upper()]
        if not ta:print("No explicit TA/TEMP label found in original AUXMETEO table")
        else:
            for rec in ta:
                print("TA-CANDIDATE"," | ".join(k+"="+repr(rec[k]) for k in AUX_REQUIRED))
        print("\nDO NOT interpret VALUE as slope/intercept/timezone without FLUXNET")
        print("AUXMETEO/BADM published metadata, method and units.")
        print("This inspection is not independent raw ERA or canopy validation.")
        print("ALL 319 US-Ho1 temperature blockers and 4,884 Batch02 remain HOLD.")
        print("NO FILE WRITES, NO SOURCE/FORCING/NETCDF/DATM/CIME/SLURM CHANGES; approvals=0")
    finally:
        zf.close()

def selftest():
    sample=("ID,VARIABLE,PARAMETER,VALUE,TIMESTAMP\n"
            "1,TA,unit,degC,1\n"
            "2,TA,intercept,-3.1,2\n"
            "3,SW_IN,method,mock,3\n").encode()
    rows=aux_rows(sample)
    assert len(rows)==3
    assert rows[0]["VARIABLE"]=="TA" and rows[1]["VALUE"]=="-3.1"
    assert Counter(r["VARIABLE"] for r in rows)=={"TA":2,"SW_IN":1}
    try:
        aux_rows(b"ID,VARIABLE,BAD,VALUE,TIMESTAMP\n1,TA,2,3,4\n")
    except ValueError as err:
        assert "header" in str(err)
    else:
        raise AssertionError("Malformed AUXMETEO header accepted")
    print("STAGE45 SELF-TEST PASS | exact AUXMETEO fields, row count and malformed-header rejection")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        selftest()
        return
    stage44=load_stage44()
    m,p,control,feb=stage44.prior()  # all earlier source lineage and 25/3005 checks
    if len(control)!=3005 or len(feb)!=25:
        raise ValueError("Original Stage43 control/failure scope changed")
    inspect(m,stage44,args.audit)

if __name__=="__main__":
    main()

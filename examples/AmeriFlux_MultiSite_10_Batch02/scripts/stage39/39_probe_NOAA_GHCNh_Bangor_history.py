#!/usr/bin/env python3
"""Stage39: NOAA GHCNh Bangor historical air-temperature availability (READ ONLY).

--self-test: in-memory parser test, no data/network
--check: original Stage08/19/20/21 SHA256 and 319 timestamp gate, offline
--probe: fetch ONLY GHCNh Bangor 1998/1999/2001 PSV files to RAM from NOAA,
         report actual date and numeric-temperature coverage/QC fields.

No output files, downloads to disk, forcing, NetCDF, DATM, CIME or Slurm
changes. GHCNh report availability is NOT quality approval or model approval.
"""
import argparse
from bisect import bisect_left
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

H=Path.home()
B=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11=B/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S19=H/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
S20=H/"AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
S21=H/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
YEARS={1998:64,1999:25,2001:230}
SITES=("US-Ho1","US-Ho2","US-Ho3")
STATION="USW00014606"
URL_ROOT="https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/access/by-year"
LIMIT=32*1024*1024

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def verify(path,ledger,site):
    p=Path(path).resolve(strict=True)
    matches=[]
    for name,digest in ledger.items():
        try:same=Path(name).resolve(strict=True)==p
        except (OSError,RuntimeError):same=False
        if same:matches.append(digest)
    if not matches or len(set(matches))!=1:
        raise ValueError(site+" absent/ambiguous original SHA ledger")
    if sha(p)!=matches[0]:raise ValueError(site+" original SHA256 differs")
    return p

def numeric(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask((x<=-9990)|~np.isfinite(x))

def esw(t):
    with np.errstate(over="ignore",invalid="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def raw_tower(path):
    wanted=["TIMESTAMP_START","TA_F","TA_F_QC"]
    a=pd.read_csv(path,usecols=wanted,dtype={"TIMESTAMP_START":str})
    a["local"]=pd.to_datetime(a.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M")
    if a.local.duplicated().any() or not a.local.is_monotonic_increasing:
        raise ValueError("Original timestamps invalid")
    a["TA_F"]=numeric(a.TA_F)
    a["TA_F_QC"]=numeric(a.TA_F_QC)
    a["QC0"]=a.TA_F_QC.eq(0)&a.TA_F.notna()
    return a

def gate(args):
    for path in (args.s11,args.s19,args.s20):
        if not (path/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Missing scientific HOLD marker "+str(path))
    m11=json.loads((args.s11/"manifest.json").read_text())
    m19=json.loads((args.s19/"manifest.json").read_text())
    m20=json.loads((args.s20/"manifest.json").read_text())
    m21=json.loads((args.s21/"manifest.json").read_text())
    if (m19.get("n_target_rows"),m19.get("scientifically_approved_rows"))!=(4884,0):
        raise ValueError("Stage19 source/approval changed")
    if (m20.get("number_targets"),m20.get("number_approved"))!=(4884,0):
        raise ValueError("Stage20 source/approval changed")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED" or \
       m19.get("UTC_offsets_local_minus_UTC",{}).get("US-Ho1")!=-5:
        raise ValueError("Ho1 UTC offset/metadata status changed")
    if Path(m20["stage19_root"]).resolve()!=args.s19.resolve() or \
       sha(args.s19/"manifest.json")!=m20["stage19_manifest_sha256"]:
        raise ValueError("Stage19/20 manifest SHA lineage changed")
    if sha(args.s20/"all_4884_phase_transfer_QC_sensitivity.csv")!=m21["stage20_csv_sha256"]:
        raise ValueError("Stage20/21 provenance changed")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    items={r["site"]:r for r in m08["sites"] if r["site"] in SITES}
    if set(items)!=set(SITES):raise ValueError("Missing Howland original site")
    sources={}
    for site in SITES:
        p=verify(items[site]["primary"],m08["input_sha256"],site)
        if site=="US-Ho1" and sha(p)!=m19["original_source_sha256"][site]:
            raise ValueError("Ho1 original not equal Stage19 pinned source")
        sources[site]=raw_tower(p)
        print("ORIGINAL SHA VERIFIED",site,"rows",len(sources[site]),
              "QC0",int(sources[site].QC0.sum()),flush=True)
    x=pd.read_csv(args.s20/"all_4884_phase_transfer_QC_sensitivity.csv",
        usecols=["site","local","TA_F_QC","retained_TA_C",
                 "ERA5_Td2M_C","Td_transfer_water_VPD_hPa"],parse_dates=["local"])
    if len(x)!=4884 or x.duplicated(["site","local"]).any():
        raise ValueError("Stage20 original 4884 target identities differ")
    x=x.loc[x.site.eq("US-Ho1")].copy()
    if len(x)!=917:raise ValueError("Expected Ho1 917 records")
    x=x.merge(sources["US-Ho1"][["local","TA_F","TA_F_QC"]],
              on="local",how="left",validate="one_to_one",
              suffixes=("","_raw"),indicator=True)
    if not x._merge.eq("both").all():raise ValueError("Original Ho1 times absent")
    if not np.allclose(x.retained_TA_C,x.TA_F,atol=1e-6,rtol=0,equal_nan=True) or \
       not np.allclose(x.TA_F_QC,x.TA_F_QC_raw,atol=0,rtol=0,equal_nan=True):
        raise ValueError("Stage20 original Ho1 TA/QC mismatch")
    calc=esw(x.retained_TA_C)-esw(x.ERA5_Td2M_C)
    if not np.allclose(calc,x.Td_transfer_water_VPD_hPa,rtol=1e-8,atol=1e-7):
        raise ValueError("Stage20 Td-transfer baseline changed")
    x=x.loc[calc.lt(-.005)].copy()
    if len(x)!=425 or not x.TA_F_QC.eq(2).all():
        raise ValueError("Stage34 425 QC2 cases changed")
    for site,short in (("US-Ho2","H2"),("US-Ho3","H3")):
        observed=sources[site][["local","QC0"]].rename(columns={"QC0":short})
        x=x.merge(observed,on="local",how="left",validate="one_to_one")
        x[short]=x[short].eq(True)
    if (int(x.H2.sum()),int(x.H3.sum()),int((x.H2&x.H3).sum()))!=(67,106,67):
        raise ValueError("Stage36 neighbouring QC0 coverage changed")
    missing=x.loc[~(x.H2|x.H3),["local"]].copy()
    missing["year"]=missing.local.dt.year
    if len(missing)!=319 or missing.groupby("year").size().to_dict()!=YEARS:
        raise ValueError("Stage38 exact 319 timestamps changed")
    missing["utc_candidate"]=missing.local+pd.Timedelta(hours=5)
    print("STAGE39 PREFLIGHT PASS | 319=1998:64,1999:25,2001:230; Ho1 UTC-5 provisional")
    return missing

def utc_time(raw):
    try:d=datetime.fromisoformat(str(raw).strip().replace("Z","+00:00"))
    except ValueError:return None
    if d.tzinfo:return d.astimezone(timezone.utc).replace(tzinfo=None)
    return d

def parse_psv(blob,year):
    source=blob.decode("utf-8-sig")
    if "|" not in source[:1024] or "<html" in source[:1024].lower():
        raise ValueError("NOAA reply not pipe-separated station data")
    reader=csv.DictReader(io.StringIO(source),delimiter="|")
    names=reader.fieldnames or []
    fields={n.strip().lower():n for n in names}
    needed={"date","temperature"}
    if not needed<=set(fields) or not ({"station","station_id"}&set(fields)):
        missing=needed-set(fields)
        if not ({"station","station_id"}&set(fields)):
            missing.add("station OR station_id")
        raise ValueError("Unknown GHCNh schema (missing "+str(missing)+
                         "), header sample="+str(names[:16]))
    # NOAA's real station/year PSV files use STATION; earlier synthetic tests
    # used Station_ID. Accept either without weakening the ID equality check.
    station_field=fields.get("station") or fields.get("station_id")
    qcfields=[f for f in names if "temperature" in f.lower() and
              any(z in f.lower() for z in ("quality","measurement","source","code"))]
    counts={}
    timestamps=[]
    samples=[]
    n=0
    other_ids=set()
    for row in reader:
        n+=1
        ident=(row.get(station_field) or "").strip()
        if ident!=STATION:
            other_ids.add(ident)
            if len(other_ids)>5:raise ValueError("NOAA PSV has inconsistent station identifiers")
            continue
        stamp=utc_time(row.get(fields["date"]))
        if stamp is None or stamp.year!=year:continue
        raw_t=(row.get(fields["temperature"]) or "").strip()
        try:
            val=float(raw_t)
            plausible=np.isfinite(val) and -80<=val<=60
        except ValueError:plausible=False
        if plausible:
            timestamps.append(stamp)
            if len(samples)<3:
                samples.append((stamp.isoformat(),raw_t,
                    {key:row.get(key) for key in qcfields[:4]}))
        for f in qcfields:
            key=(f,(row.get(f) or "").strip())
            counts[key]=counts.get(key,0)+1
    if other_ids:raise ValueError("Unexpected NOAA station identifiers: "+str(other_ids))
    timestamps.sort()
    return names,qcfields,counts,timestamps,n,samples

def nearest(minutes,stamp):
    if not minutes:return None
    i=bisect_left(minutes,stamp)
    nearby=[abs((minutes[j]-stamp).total_seconds())/60
            for j in (i-1,i) if 0<=j<len(minutes)]
    return min(nearby) if nearby else None

def candidate_url(y):
    return f"{URL_ROOT}/{y}/psv/GHCNh_{STATION}_{y}.psv"

def probe(year,targets):
    url=candidate_url(year)
    req=urllib.request.Request(url,headers={"User-Agent":"CLM-FATES scientific read-only Stage39","Accept":"text/plain,text/csv,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=30) as response:
            final=urllib.parse.urlsplit(response.geturl())
            if final.scheme!="https" or final.hostname not in ("www.ncei.noaa.gov","ncei.noaa.gov"):
                raise ValueError("Unexpected redirect for NOAA source")
            blob=response.read(32*1024*1024+1)
    except urllib.error.HTTPError as e:raise RuntimeError("NOAA HTTP "+str(e.code)+" "+url) from e
    except urllib.error.URLError as e:raise RuntimeError("NOAA network unavailable: "+str(e)) from e
    if len(blob)>32*1024*1024:raise ValueError("NOAA PSV exceeds 32MiB memory cap")
    cols,qc,cnts,times,n,samples=parse_psv(blob,year)
    print("\nNOAA IN-MEMORY SOURCE",year,"url",url)
    print("RESPONSE BYTES",len(blob),"SHA256",hashlib.sha256(blob).hexdigest())
    print("PSV rows",n,"plausible numeric-temperature rows",len(times),
          "columns",len(cols),"QC/source field names",qc[:14])
    print("SOURCE/QC CODES UNINTERPRETED:",sorted(cnts.items(),key=lambda i:-i[1])[:16])
    print("SAMPLE RAW OBSERVATIONS:",samples)
    near=[nearest(times,t) for t in targets]
    for maxgap in (30,60,90):
        print("NOMINAL UTC targets within",maxgap,"minutes of raw numeric T:",
              sum(x is not None and x<=maxgap for x in near),"/",len(targets))
    print("NO numerical comparison or NOAA QC approval.")
    return len(times)

def test():
    # Regression reproduces the *actual* NOAA header reported on IRIDIS6.
    actual_header=("STATION|Station_name|DATE|Year|Month|Day|Hour|Minute|"
                   "LATITUDE|LONGITUDE|ELEVATION|temperature|"
                   "temperature_Measurement_Code|temperature_Quality_Code|"
                   "temperature_Report_Type|temperature_Source_Code\n")
    rows=("USW00014606|BANGOR|1999-02-13T04:00:00|1999|2|13|4|0|"
          "44.8|-68.8|58|8.0|A|C|FM-16|X\n"
          "USW00014606|BANGOR|1999-02-13T05:00:00|1999|2|13|5|0|"
          "44.8|-68.8|58|8.5|A|C|FM-16|X\n")
    a,b,c,times,n,sm=parse_psv((actual_header+rows).encode(),1999)
    assert n==2 and len(times)==2
    assert {"temperature_Quality_Code","temperature_Source_Code",
            "temperature_Measurement_Code"}<=set(b)
    assert nearest(times,datetime(1999,2,13,4,30))==30
    assert c[("temperature_Quality_Code","C")]==2
    # Preserve the legacy alias, without requiring it in NOAA's actual PSV.
    old=("Station_ID|DATE|temperature|temperature_Quality_Code\n"
         "USW00014606|1999-02-13T04:00:00|8.0|C\n")
    _,old_qc,_,old_times,old_n,_=parse_psv(old.encode(),1999)
    assert old_n==1 and len(old_times)==1 and old_qc==["temperature_Quality_Code"]
    # Never silently accept a mismatched station identifier.
    wrong=actual_header+rows.replace("USW00014606","USW00014607")
    try:
        parse_psv(wrong.encode(),1999)
    except ValueError as err:
        assert "station identifiers" in str(err)
    else:
        raise AssertionError("Unexpected station identity was accepted")
    # Regression: np.allclose produces a scalar bool, not an array with .all().
    measured=np.array([2.5,np.nan,3.0])
    same=np.array([2.5,np.nan,3.0])
    altered=np.array([2.5,np.nan,4.0])
    assert np.allclose(measured,same,atol=1e-6,rtol=0,equal_nan=True)
    assert not np.allclose(measured,altered,atol=1e-6,rtol=0,equal_nan=True)
    print("STAGE39 SELF-TEST PASS | actual NOAA STATION PSV, station-ID rejection, legacy alias, UTC, QC fields, and np.allclose guard")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--probe",action="store_true",help="NOAA HTTPS, memory-only")
    for key,default in (("s11",S11),("s19",S19),("s20",S20),("s21",S21)):
        p.add_argument("--"+key,type=Path,default=default)
    args=p.parse_args()
    if args.self_test:return test()
    target=gate(args)
    if args.check:
        for y,g in target.groupby("year"):
            print("YEAR",y,"n",len(g),"UTC candidate first/last",
                  g.utc_candidate.min(),g.utc_candidate.max())
        print("CHECK ONLY | 0 writes/downloads/approvals")
        return
    failures=[]
    for y,g in target.groupby("year"):
        try:probe(int(y),[t.to_pydatetime() for t in g.utc_candidate])
        except (RuntimeError,ValueError,UnicodeError,csv.Error) as e:
            failures.append(int(y))
            print("YEAR",y,"NOAA PROBE STOPPED:",str(e))
    print("\nUNVERIFIED NOAA YEARS:",failures)
    print("NOAA numeric-T presence does not imply valid measured-T QC.")
    print("ALL 4,884 Stage08 held; zero approved replacements; no files written.")
    if failures:raise SystemExit(2)

if __name__=="__main__":main()

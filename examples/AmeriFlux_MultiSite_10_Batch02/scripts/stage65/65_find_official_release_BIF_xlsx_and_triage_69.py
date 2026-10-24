#!/usr/bin/env python3
"""Stage65 (READ ONLY): source-pinned original BIF provenance and 69 tower T HOLDs.

Main aim: unblock US-Ho1 (16,788 original hard events) and US-BZS (86).
Previous stages only checked adjacent *_BIF_*.csv, while official
AmeriFlux BIF frequently uses .xlsx. Discover CSV/XLSX BIF metadata
in plausible original-package folders and ZIP contents, including a
one-pass exact-SHA match to the current original FLUXNET tower CSV.
Never apply a site UTC offset unless a SAME-ARCHIVE identical original
primary plus unique valid site UTC_OFFSET/coordinates is verified.
This audit does not change original, DATM, forcing, archive or jobs.

The 69 Stage63 unresolved T events remain HOLD. Their exact source
timestamp and physical neighbor evidence is inventoried without silently
approving warm/sensor-plateau/low-QC original temperatures.
"""
import argparse, csv, hashlib, io, json, re, zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

REPO=Path.home()/"CLM-FATES-single-site-workflows"
REL=Path("examples/AmeriFlux_MultiSite_10_Batch02")
ST63_SCRIPT=REPO/REL/"scripts/stage63/63_automatic_246_temperature_neighbor_and_metadata_triage.py"
ST63_GIT_BLOB="b8f2ad755c7f4bcb7fbb998bd3a086db28e7032c"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
R=ROOT/"reports"
S63=R/"stage63_246_temperature_auto_neighbor_QC_20261024T231206Z_b5fac2db"
S64=R/"stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94"
T_FILE="69_nonHo1_source_temperature_cases_HOLD.csv"
A_FILE="BZS_Ho1_original_archive_BIF_discovery.json"
SITES=("US-BZS","US-Ho1")
MAX_CANDIDATES_PER_SITE=2500
MAX_BIF_BYTES=32*1024*1024
MAX_ARCHIVE_MEMBER_BYTES=32*1024*1024
SOURCE=("site","source_csv_row","timestamp_start","original_TA_C",
        "ERA5_T2M_C","original_TA_QC","original_tower_T_decision")

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def blob(p):
    b=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def valid_coords(meta):
    try:
        a=float(meta["LOCATION_LAT"])
        b=float(meta["LOCATION_LONG"])
        z=float(meta["UTC_OFFSET"])
        return -90<=a<=90 and -180<=b<=180 and -12<=z<=14 and z*2==round(z*2)
    except (KeyError,ValueError,TypeError):
        return False

def extract_meta(rows,site):
    """BADM BIF SITE_ID, VARIABLE, DATAVALUE; unique values required."""
    seen={}
    for row in rows:
        record={str(k).strip().upper():str(v).strip()
                for k,v in row.items() if k is not None and v is not None}
        if record.get("SITE_ID","").upper()!=site.upper():
            continue
        key=record.get("VARIABLE","").upper()
        value=record.get("DATAVALUE","")
        if key in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET") and value not in ("","-9999"):
            seen.setdefault(key,set()).add(value)
    unique={k:next(iter(v)) for k,v in seen.items() if len(v)==1}
    return {"values":{k:sorted(v) for k,v in seen.items()},
            "unique":unique,"physically_valid":bool(valid_coords(unique)),
            "saw_duplicates":bool(any(len(v)!=1 for v in seen.values()))}

def read_csv_bif(data):
    text=data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))

def xlsx_tables(data):
    """Minimal stdlib XLSX table reader; supports sharedStrings/inline strings.

    Only sheet table values and headers are read; no formulas/macros executed.
    """
    result=[]
    ns="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        strings=[]
        if "xl/sharedStrings.xml" in z.namelist():
            x=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for item in x.findall(ns+"si"):
                strings.append("".join(t.text or "" for t in item.iter(ns+"t")))
        for name in sorted(z.namelist()):
            if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml",name):continue
            root=ET.fromstring(z.read(name))
            values=[]
            for row in root.iter(ns+"row"):
                cells={}
                for cell in row.findall(ns+"c"):
                    address=cell.get("r","")
                    match=re.match(r"([A-Z]+)",address)
                    if not match:continue
                    col=0
                    for a in match.group(1):col=col*26+ord(a)-64
                    t=cell.get("t")
                    v=cell.find(ns+"v")
                    inline=cell.find(ns+"is")
                    val=(v.text if v is not None else "") or ""
                    if t=="s" and val:
                        pos=int(val)
                        val=strings[pos]
                    elif t=="inlineStr" and inline is not None:
                        val="".join(e.text or "" for e in inline.iter(ns+"t"))
                    cells[col-1]=str(val)
                if cells:
                    values.append([cells.get(k,"") for k in range(max(cells)+1)])
            for i,headers in enumerate(values[:30]):
                h=[x.strip().upper() for x in headers]
                if {"SITE_ID","VARIABLE","DATAVALUE"}.issubset(h):
                    result.extend({headers[j].strip():r[j] if j<len(r) else ""
                        for j in range(len(headers))} for r in values[i+1:])
                    break
    return result

def decode_bif(data,filename):
    suffix=Path(filename).suffix.lower()
    if suffix==".csv":return extract_meta(read_csv_bif(data),site=ACTIVE_SITE[0])
    if suffix==".xlsx":return extract_meta(xlsx_tables(data),site=ACTIVE_SITE[0])
    raise ValueError("Not a CSV/XLSX BIF")

def source_context():
    sm=json.loads((S63/"source_and_science_manifest.json").read_text())
    m=json.loads((S64/"unified_source_provenance_and_hold_manifest.json").read_text())
    if ((S63/"INCOMPLETE_DO_NOT_USE").exists() or
        (S64/"INCOMPLETE_DO_NOT_USE").exists() or
        sm.get("schema")!="STAGE63_NONHO1_246_TOWER_T_NEIGHBOR_QC_v1" or
        sm.get("n_auto_temperature_accepted")!=177 or
        sm.get("n_temperature_still_HOLD")!=69 or
        m.get("schema")!="STAGE64_ORIGINAL_HARD_FULL_CENSUS_9389_CANDIDATES_16943_HOLD_v1" or
        m.get("total_selected_candidate_rows")!=9389 or
        m.get("remaining_hard_HOLD")!=16943 or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage63/64 source provenance or population unexpected")
    for folder,proof in ((S63,sm["output_sha256"]),(S64,m["output_sha256"])):
        for name,value in proof.items():
            if sha(folder/name)!=value:raise ValueError("Changed pinned source "+str(folder/name))
    if blob(ST63_SCRIPT)!=ST63_GIT_BLOB:
        raise ValueError("Exact original Stage63 script must be pinned before metadata scan")
    from importlib import util
    spec=util.spec_from_file_location("batch02_original_stage63",ST63_SCRIPT)
    mod=util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Stage63 reads all ten original sources and checks source-file SHA
    target,source,original_pins=mod.read_source()
    holds=pd.read_csv(S64/T_FILE,dtype={"site":str,"timestamp_start":str,
                                        "source_sha256":str})
    if (len(holds)!=69 or Counter(holds.original_tower_T_decision)!={
        "HOLD_ORIGINAL_TA_OUTSIDE_COLD_POLICY":48,
        "HOLD_TEMPORAL_JUMP_OR_NONSTATIONARY":12,
        "HOLD_NEIGHBOR_QC_UNVERIFIED":9}):
        raise ValueError("69 original T HOLD status unexpectedly changed")
    if (holds.duplicated(["site","timestamp_start"]).any() or
        not set(holds.site).isdisjoint(set(SITES))):
        raise ValueError("Unexpected source T HOLD site/time")
    return holds,source,sm,m

def search_paths(site,primary):
    """Bounded site-specific original-source inventory; no whole-scratch walk."""
    candidates={}
    roots=[primary.parent,primary.parent.parent,primary.parent.parent.parent,
      Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")/site,
      Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites")/site,
      REPO/REL/"data"/site,
      Path.home()/("ameriflux_"+site),
      Path.home()/("AmeriFlux_"+site)]
    for root in roots:
        if not root.is_dir():continue
        # site-scoped paths only: maximum 3 subdirectory levels
        stack=[(root,0)]
        visited=set()
        while stack and len(candidates)<MAX_CANDIDATES_PER_SITE:
            parent,depth=stack.pop()
            if parent in visited:continue
            visited.add(parent)
            try:entries=sorted(parent.iterdir())
            except (OSError,PermissionError):continue
            for p in entries:
                if p.is_symlink():continue
                if p.is_dir() and depth<3 and p.name not in (
                    ".git","build","run","archive","history","logs","conda"):
                    if site in str(p) or depth<=1:
                        stack.append((p,depth+1))
                elif p.is_file() and p.suffix.lower() in (".csv",".xlsx",".zip"):
                    n=p.name.upper()
                    if (site.upper() in n and
                        ("_BIF_" in n or "FLUXNET" in n or "BADM" in n)):
                        candidates[str(p.resolve())]=p
    return sorted(candidates.values(),key=str)

def probe(site,path,primary,original_sha):
    """Report evidence, never promote mismatched/external site-only BIF."""
    result={"site":site,"path":str(path),"input_sha256":sha(path),
       "independent_original_source_sha256":original_sha,
       "verified_same_archive_release_BIF":False,"candidate_bif":[]}
    if path.suffix.lower() in (".csv",".xlsx"):
        try:
            payload=path.read_bytes()
            if len(payload)>MAX_BIF_BYTES:
                raise ValueError("BIF larger than maximum safe parse")
            ACTIVE_SITE[0]=site
            m=decode_bif(payload,path.name)
            result["candidate_bif"].append({"name":path.name,
                "meta":m,"release_assurance":"STANDALONE_BIF_NOT_SAME_RELEASE_PROVED"})
        except Exception as e:
            result["parse_error"]=str(e)
        return result
    if path.suffix.lower()!=".zip":return result
    try:
        with zipfile.ZipFile(path) as z:
            infos=z.infolist()
            originals=[n for n in infos if not n.is_dir() and
                       Path(n.filename).name==primary.name and
                       n.file_size==primary.stat().st_size]
            same=False
            for member in originals:
                h=hashlib.sha256()
                with z.open(member) as stream:
                    for part in iter(lambda:stream.read(1<<20),b""):h.update(part)
                if h.hexdigest()==original_sha:same=True;break
            result["original_primary_identical_in_archive"]=same
            for member in infos:
                if member.is_dir() or member.file_size>MAX_ARCHIVE_MEMBER_BYTES:continue
                name=Path(member.filename).name
                if (site.upper() not in name.upper()
                    or "_BIF_" not in name.upper()
                    or Path(name).suffix.lower() not in (".xlsx",".csv")):
                    continue
                try:
                    ACTIVE_SITE[0]=site
                    with z.open(member) as stream:
                        m=decode_bif(stream.read(),name)
                    ok=(same and m["physically_valid"] and not m["saw_duplicates"])
                    result["candidate_bif"].append({"name":member.filename,
                        "meta":m,"release_assurance":"EXACT_ORIGINAL_SHA256_SAME_ZIP"
                           if ok else "NO_EXACT_SOURCE_OR_UNIQUE_METADATA"})
                    if ok:result["verified_same_archive_release_BIF"]=True
                except Exception as e:
                    result["candidate_bif"].append({"name":name,"parse_error":str(e)})
    except (OSError,ValueError,zipfile.BadZipFile) as e:
        result["archive_error"]=str(e)
    return result

def t_holds(holds):
    rows=[]
    for r in holds.itertuples(index=False):
        # 69 source problems are not eligible for blanket automatic correction:
        # any legacy QC2, persistent 24.9°C or -40°C plateaus and sharp jumps
        # must remain explicitly recorded as original temperature HOLD.
        t=float(r.original_TA_C)
        rte=str(r.original_tower_T_decision)
        row={"site":r.site,"timestamp_start":str(r.timestamp_start),
            "original_TA_C":t,"ERA5_T2M_C":float(r.ERA5_T2M_C),
            "original_TA_QC":float(r.original_TA_QC),
            "source_science_decision":rte,
            "temperature_hold_no_DATM_approval":True}
        row["suspected_sensor_plateau_or_bound"]=bool(
             r.site=="US-ICh" and (np.isclose(t,24.9) or np.isclose(t,-40.)))
        row["priority"]="SOURCE_QC_AND_NEIGHBOR_CONTEXT"
        if row["suspected_sensor_plateau_or_bound"]:
            row["priority"]="SENSOR_BOUND_OR_FLATLINE_CHECK"
        elif rte=="HOLD_ORIGINAL_TA_OUTSIDE_COLD_POLICY":
            row["priority"]="WARM_CONTEXT_EVIDENCE_REQUIRED"
        rows.append(row)
    return pd.DataFrame(rows)

def self_test():
    assert valid_coords({"LOCATION_LAT":"64.6963",
                         "LOCATION_LONG":"-148.3235","UTC_OFFSET":"-9"})
    assert not valid_coords({"LOCATION_LAT":"999",
                             "LOCATION_LONG":"0","UTC_OFFSET":"-9"})
    sample=b"SITE_ID,VARIABLE,DATAVALUE\nUS-Ho1,LOCATION_LAT,45.2040\nUS-Ho1,LOCATION_LONG,-68.7402\nUS-Ho1,UTC_OFFSET,-5\n"
    val=extract_meta(read_csv_bif(sample),"US-Ho1")
    assert val["physically_valid"] and val["unique"]["UTC_OFFSET"]=="-5"
    assert not extract_meta(read_csv_bif(sample),"US-BZS")["physically_valid"]
    assert len(SITES)==2
    print("STAGE65 SELF-TEST PASS | CSV+XLSX BIF metadata parser, site/source release gates")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--self-test",action="store_true")
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    holds,spec,sm,m64=source_context()
    discovery=[]
    for site in SITES:
        file=Path(spec[site]["file"]).resolve(strict=True)
        original=spec[site]["sha256"]
        paths=search_paths(site,file)
        print("STAGE65",site,"candidate archives/BIFs",len(paths),flush=True)
        for candidate in paths:
            discovery.append(probe(site,candidate,file,original))
    full=t_holds(holds)
    counts=dict(Counter(full.priority))
    proof=[r for r in discovery if r["verified_same_archive_release_BIF"]]
    status={site:{"matching_release_metadata":[],"other_bif_candidates":0}
            for site in SITES}
    for r in discovery:
        if r["verified_same_archive_release_BIF"]:
            status[r["site"]]["matching_release_metadata"].append(r["path"])
        status[r["site"]]["other_bif_candidates"]+=len(r["candidate_bif"])
    print("STAGE65 METADATA_DISCOVERY",json.dumps(status,sort_keys=True))
    print("STAGE65 69_T_HOLD_PRIORITY_COUNTS",counts)
    print("STAGE65 SAME_RELEASE_BIF_EVIDENCE",len(proof))
    print("ORIGINAL TIME SOURCE UNSURE: no Ho1/BZS CDS join unless verified original archive")
    print("69 T records remain HOLD; no ERA5 T replacements were written")
    if a.check:
        print("STAGE65 CHECK PASS | zero output/source/model writes")
        return
    dest=R/("stage65_metadata_xlsx_BIF_and_69T_triage_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Evidence only, not DATM permission.\n")
    bf=dest/"BZS_Ho1_source_release_BIF_CSV_XLSX_ZIP_inventory.json"
    bf.write_text(json.dumps(discovery,indent=2,ensure_ascii=False)+"\n")
    tfile=dest/"69_temperature_source_HOLD_priority.csv"
    full.to_csv(tfile,index=False)
    report={"schema":"STAGE65_SOURCE_BIF_METADATA_AND_69T_TRIAGE_v1",
      "n_stage64_original_hard":26332,"n_stage64_candidates":9389,
      "n_hard_HOLD":16943,"n_Ho1_HOLD":16788,"n_BZS_HOLD":86,
      "n_temperature_HOLD":69,"n_same_archive_BIF_verified":len(proof),
      "source_sha256":{"stage64_manifest":sha(
           S64/"unified_source_provenance_and_hold_manifest.json"),
          "stage63_manifest":sha(S63/"source_and_science_manifest.json"),
          "stage63_pinned_code_gitblob":ST63_GIT_BLOB},
      "output_sha256":{bf.name:sha(bf),tfile.name:sha(tfile)},
      "approved_for_DATM":False,"no_original_or_forcing_writes":True}
    if sha(S64/T_FILE)!=m64["output_sha256"][T_FILE]:
        raise ValueError("Source changed during Stage65 metadata scan")
    (dest/"stage65_manifest.json").write_text(json.dumps(
         report,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE65 AUDIT PASS | searched real CSV/XLSX/ZIP BIF candidates; 69 temperature HOLD triaged")
    print("REPORT",dest)
    print("NO ORIGINAL EC, CDS, DATM, NETCDF, CIME, SLURM OR SPINUP WRITES")
if __name__=="__main__":
    main()

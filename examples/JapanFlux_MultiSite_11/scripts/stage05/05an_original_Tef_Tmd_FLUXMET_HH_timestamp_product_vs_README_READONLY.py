#!/usr/bin/env python3
"""JapanFlux Stage05AN — original nested JPF Tef/Tmd HH timestamp provenance.

Unlike generic FLUXNET standards, inspect the exact source release's nested
ZIP README and FLUXMET_HH CSV (streamed) for timestamp columns, first/last
half-hour stamps, and the original Stage05AM 18 clock-HOLD QC2 event records.

A station-specific ICOS FLUXNET product may publish a UTC acquisition range
and local non-DST TIMESTAMP_END, while the exact original JPF README claims
local solar time. This read-only inspector does NOT infer which convention
was actually used for particular timestamps from archive CSV appearance.
No guessed UTC mapping, solar correction, CDS, forcing changes or repair.

Run ONE site per invocation to cap transient memory; derived reports only.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path,PurePosixPath

SITES={
    "JP-Tef":"JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1",
    "JP-Tmd":"JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1"
}
EXPECTED={"JP-Tef":4,"JP-Tmd":14}
ORIGINAL_README_SHA="17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SELECT_FIELDS=("site","native_start","variable","source_flag","matched_original_CSV_source",
    "original_F_value","original_embedded_ERA_value","actual_F_CSV_value",
    "actual_ERA_CSV_value","actual_F_CSV_QC","TIMESTAMP_START_original_native",
    "TIMESTAMP_END_original_native","original_native_timestamp_aligned_to_CSV_START",
    "source_timebase_resolution")

def load_tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError("Malformed source site manifest or Stage05AM register TSV")
        return list(r)

def load_json(path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict):raise ValueError("Expected source JSON dictionary")
    return d

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validated_inputs(site,manifest,register,report):
    if len(manifest)!=11 or len({r["site"] for r in manifest})!=11:
        raise ValueError("Stage00 exact 11-site original manifest changed")
    matches=[r for r in manifest if r["site"]==site]
    if len(matches)!=1 or matches[0]["package"]!=SITES[site]:
        raise ValueError("JP-Tef/Tmd original nested source package mismatch")
    if (report.get("stage")!="JapanFlux Stage05AM"
        or report.get("status")!="TWO_ORIGINAL_SOLAR_VS_STANDARD_SITE_CLOCKS_UNRESOLVED_SCIENCE_HOLD"
        or report.get("original_QC2_field_count")!=45
        or report.get("already_independently_compared")!=27
        or report.get("clock_conflict_variable_fields")!=18
        or report.get("clock_conflict_by_site")!=EXPECTED
        or report.get("clock_conflict_native_site_halfhours")!=14
        or report.get("original_Tef_Tmd_source_readme_75line_SHA256")!=ORIGINAL_README_SHA
        or report.get("original_BIF_UTC_OFFSET_both_sites")!=9
        or report.get("original_UTC_mapping_generated") is not False
        or report.get("all_45_original_QC2_fields_HOLD") is not True):
        raise ValueError("Real Stage05AM 18 source native clock-HOLD summary changed")
    if len(register)!=18 or Counter(r["site"] for r in register)!=Counter(EXPECTED):
        raise ValueError("Original Stage05AM 4/14 native source variable fields changed")
    events={}
    for r in register:
        if r["site"]!=site:continue
        key=(r["native_halfhour_timestamp_NOT_UTC"],r["variable"])
        if (key in events
            or r["original_UTC"]!="UNRESOLVED"
            or r["science_decision"]!="HOLD_NATIVE_ONLY_NO_CDS_NO_UTC_NO_REPAIR"
            or r["original_readme_SHA256"]!=ORIGINAL_README_SHA
            or r["source_flag"]!="ORIGINAL_SELECTED_F_EQ_EMBEDDED_ERA_QC2"):
            raise ValueError("JP-Tef/Tmd exact source native-QC2 HOLD flags changed")
        datetime.strptime(key[0],"%Y%m%d%H%M")
        events[key]=r
    if len(events)!=EXPECTED[site]:
        raise ValueError("Original site event counts differ from Stage05AM 4 or 14")
    return matches[0]["package"],events

def inspect_original(site,package,events,root,max_inner_mib):
    outer=root/site/"forcing"/"packages"/(package+".zip")
    if not outer.is_file() or outer.is_symlink():
        raise ValueError("Missing/nonregular original outer JPF ZIP: "+str(outer))
    nested_name=package+".zip"
    # Keep one original source inner release in bounded memory, one site/run.
    with zipfile.ZipFile(outer) as source:
        inner=[i for i in source.infolist() if i.filename==nested_name and not i.is_dir()]
        if len(inner)!=1 or not 0<inner[0].file_size<=max_inner_mib*1024*1024:
            raise ValueError("Original exact nested JPF release ZIP absent or oversized")
        b=io.BytesIO()
        with source.open(inner[0]) as stream:
            used=0
            for chunk in iter(lambda:stream.read(2*1024*1024),b""):
                used+=len(chunk)
                if used>max_inner_mib*1024*1024:
                    raise ValueError("Original inner ZIP memory cap exceeded")
                b.write(chunk)
    b.seek(0)
    found={};first=[];last=[];row_count=0;header=[];readme_hash=None
    sample_keys=set();seen_start=set()
    with zipfile.ZipFile(b) as z:
        names=[i for i in z.infolist() if not i.is_dir()]
        readmes=[i for i in names if PurePosixPath(i.filename).name.lower()=="readme.txt"]
        hh=[i for i in names
            if PurePosixPath(i.filename).name==
            f"JPF_{site}_FLUXNET_FLUXMET_HH_{package.split('_FLUXNET_')[1]}.csv"]
        if len(readmes)!=1 or len(hh)!=1:
            raise ValueError("Exact original README or one HH CSV member not found in nested source")
        readme=z.read(readmes[0])
        readme_hash=digest(readme)
        text=readme.decode("utf-8-sig",errors="replace").splitlines()
        if (readme_hash!=ORIGINAL_README_SHA or len(text)!=75
            or "time is expressed in local solar time (without DST)" not in text[63]):
            raise ValueError("Original Tef/Tmd site README exact 75-line solar-time claim changed")
        # The original HH member is streamed to EOF below: zipfile verifies
        # this member's CRC on completion. Avoid extracting/checking all
        # irrelevant years/variables twice on an IRIDIS6 login node.
        with z.open(hh[0]) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as handle:
                reader=csv.DictReader(handle)
                header=reader.fieldnames or []
                if (len(header)!=len(set(header))
                    or not {"TIMESTAMP_START","TIMESTAMP_END","PA_F","PA_ERA","PA_F_QC","TA_F","TA_ERA","TA_F_QC","LW_IN_F","LW_IN_ERA","LW_IN_F_QC"}<=set(header)):
                    raise ValueError("Actual source FLUXMET_HH CSV timestamp/QC2 variable columns incompatible")
                stamps={t for t,var in events}
                for row in reader:
                    row_count+=1
                    stamp=row["TIMESTAMP_START"]
                    if len(stamp)!=12 or not stamp.isdigit():
                        raise ValueError("Original HH source TIMESTAMP_START not 12-digit native time")
                    start=datetime.strptime(stamp,"%Y%m%d%H%M")
                    end=datetime.strptime(row["TIMESTAMP_END"],"%Y%m%d%H%M")
                    if end-start!=timedelta(minutes=30):
                        raise ValueError("Original HH timestamp START/END not 30min consecutive")
                    if row_count<=3:
                        first.append({"start":stamp,"end":row["TIMESTAMP_END"]})
                    if len(last)>=3:last.pop(0)
                    last.append({"start":stamp,"end":row["TIMESTAMP_END"]})
                    if stamp in stamps:
                        for (native,var),r in events.items():
                            if native!=stamp:continue
                            key=(native,var)
                            if key in found:raise ValueError("Duplicate source original flagged timestamp")
                            val=float(row[var+"_F"])
                            embedded=float(row[var+"_ERA"])
                            qc=row[var+"_F_QC"]
                            old=float(r["original_F_QC2_selected"])
                            old_era=float(r["original_same_release_ERA"])
                            if (not all(math.isfinite(x) for x in (val,embedded,old,old_era))
                                or not math.isclose(val,old,rel_tol=1e-12,abs_tol=1e-6)
                                or not math.isclose(embedded,old_era,rel_tol=1e-12,abs_tol=1e-6)
                                or qc!="2"):
                                raise ValueError("Original JPF source HH QC2 value differs from Stage05AM: "+str(key))
                            found[key]={
                                "site":site,"native_start":native,"variable":var,
                                "source_flag":r["source_flag"],
                                "matched_original_CSV_source":hh[0].filename,
                                "original_F_value":r["original_F_QC2_selected"],
                                "original_embedded_ERA_value":r["original_same_release_ERA"],
                                "actual_F_CSV_value":row[var+"_F"],
                                "actual_ERA_CSV_value":row[var+"_ERA"],
                                "actual_F_CSV_QC":qc,
                                "TIMESTAMP_START_original_native":stamp,
                                "TIMESTAMP_END_original_native":row["TIMESTAMP_END"],
                                "original_native_timestamp_aligned_to_CSV_START":"YES",
                                "source_timebase_resolution":"UNRESOLVED_SOLAR_VS_STANDARD"
                            }
    if set(found)!=set(events):
        raise ValueError("Some actual original Tef/Tmd source QC2 halfhours not found: "+repr(sorted(set(events)-set(found))))
    return {"original_outer_zip":str(outer),"nested_member":nested_name,
            "source_FLUXMET_HH_CSV_member":hh[0].filename,
            "source_README_member":readmes[0].filename,
            "original_README_SHA256":readme_hash,"original_README_claim_line64":text[63],
            "source_HH_csv_rows_scanned":row_count,"CSV_headers_in_order":header,
            "first_3_original_native_HH_timestamps":first,
            "last_3_original_native_HH_timestamps":last,
            "original_source_flagged_QC2_fields_matched":len(found),
            "original_source_flagged_native_times_matched":len({t for t,v in found}),
            "read_only_source_fields":list(found.values())}

def selftest():
    assert SITES["JP-Tmd"]=="JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1"
    assert SITES["JP-Tef"]=="JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1"
    assert sum(EXPECTED.values())==18
    a=datetime.strptime("200508120700","%Y%m%d%H%M")
    assert (a+timedelta(minutes=30)).strftime("%Y%m%d%H%M")=="200508120730"
    assert len(ORIGINAL_README_SHA)==64
    print("STAGE05AN SELF-TEST PASS | exact JPF nested ZIP original README+FLUXMET_HH timestamp and event values only, NO SOURCE WRITES/UTC/CDS/REPAIR")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--site",choices=tuple(SITES))
    p.add_argument("--manifest",type=Path)
    p.add_argument("--stage05am-register",type=Path)
    p.add_argument("--stage05am-summary",type=Path)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--max-inner-mib",type=int,default=320)
    p.add_argument("--out-dir",type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(x is None for x in (a.site,a.manifest,a.stage05am_register,a.stage05am_summary,a.out_dir)):
        p.error("Need exact JP-Tef or JP-Tmd, original 11-site manifest, Stage05AM actual register+summary, and fresh output dir")
    if not 160<=a.max_inner_mib<=512: p.error("bounded source inner archive MiB 160–512")
    package,events=validated_inputs(a.site,load_tsv(a.manifest),
                                    load_tsv(a.stage05am_register),
                                    load_json(a.stage05am_summary))
    analysis=inspect_original(a.site,package,events,a.root,a.max_inner_mib)
    if a.out_dir.exists():p.error("Derived output folder must not exist")
    a.out_dir.mkdir(parents=True)
    base=a.site.replace("-","_")
    report=a.out_dir/(f"stage05an_{base}_original_HH_release_timestamp_READONLY.json")
    rows=a.out_dir/(f"stage05an_{base}_original_4or14_QC2_HH_source_match_NO_UTC.tsv")
    analysis.update({"stage":"JapanFlux Stage05AN",
        "site":a.site,"status":"ORIGINAL_JPF_FLUXMET_HH_NATIVE_TIMESTAMP_QC2_VALUES_MATCHED_BUT_UTC_STILL_UNRESOLVED",
        "original_product_release":package,
        "ICOS_public_product_time_metadata_corroboration":"EXTERNAL_STANDARD_TIME_METADATA_CONTEXT_NOT_YET_SOURCE_SPECIFIC_PROOF",
        "new_original_UTC_mapping_approved":False,
        "original_45_QC2_source_fields_HOLD":True,
        "scientific_30minute_replacements_approved":False,
        "CDS_requests_this_stage":0,"original_source_ZIP_or_forcing_modified":False,
        "Slurm_jobs":0})
    with report.open("x",encoding="utf-8") as f:
        json.dump(analysis,f,indent=2,ensure_ascii=False);f.write("\n")
    with rows.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,delimiter="\t",fieldnames=SELECT_FIELDS)
        w.writeheader();w.writerows(sorted(analysis["read_only_source_fields"],
            key=lambda r:(r["native_start"],r["variable"])))
    print("STAGE05AN ORIGINAL JPF "+a.site+" SOURCE HH QC2 TIMESTAMP REVIEW PASS | NO CDS/UTC/SLURM/REPAIR")
    print("PACKAGE",package,"MEMBER",analysis["source_FLUXMET_HH_CSV_member"])
    print("README_SHA256",analysis["original_README_SHA256"])
    print("SOURCE_HH_ROWS_SCANNED",analysis["source_HH_csv_rows_scanned"])
    print("FIRST_SOURCE_TIME_SAMPLES",analysis["first_3_original_native_HH_timestamps"])
    print("LAST_SOURCE_TIME_SAMPLES",analysis["last_3_original_native_HH_timestamps"])
    print("SOURCE_ORIGINAL_QC2_FIELDS_MATCHED",analysis["original_source_flagged_QC2_fields_matched"],
          "NATIVE_SITE_HALFHOURS",analysis["original_source_flagged_native_times_matched"])
    print("TIMESTAMP_COLUMN_NAMES",",".join(analysis["CSV_headers_in_order"][:5]))
    print("SOURCE_EVENT_MATCH_TABLE",rows)
    print("SOURCE_CLOCK_PROVENANCE_REPORT",report)
    print("RETAIN_ORIGINAL_SOLAR_VS_STANDARD_CONFLICT UTC=UNRESOLVED; ALL 45 SOURCE QC2 FIELDS HOLD")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Batch04 Stage20: read-only original BIF temperature-instrument provenance.

Three sites / six original scientific temperature conflicts. Audits original
AmeriFlux BIF VARIABLE/DATAVALUE/GROUP_ID records, including all records in
groups whose values or variables reference air temperature, TA, T_AIR or
sensor/instrument fields. Outputs only provenance *candidates*, not proof
that an entry describes the specific sensor used at the problem timestamps.

Requires Stage12 helper alongside this file. Reads only immutable original
FLUXMET, BIF, Stage12 receipt and eight-HOLD ledger; never changes forcing,
downloads meteorology, clears science HOLDs, or submits jobs.
"""
import argparse
import csv
import json
import re
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S12=ROOT/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
CASES={
 "US-SP1":["200710151730","200801160800","200801160830","200802030800"],
 "US-SRG":["201903191200"],
 "US-Seg":["201612271800"],
}
ORIGINAL_SHA={
 "US-SP1":"d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963",
 "US-SRG":"bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567",
 "US-Seg":"2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d",
}
EIGHT={(s,k) for s,values in CASES.items() for k in values}|{
 ("US-SP1","200010091800"),("US-SP1","200010091830")}
AIR_TEMP=re.compile(r"(?<![A-Z0-9])(?:TA(?:_[A-Z0-9]+)*|T_AIR|AIR[\s_-]*TEMP(?:ERATURE)?)(?![A-Z0-9])",re.I)
META=re.compile(r"INSTRUMENT|SENSOR|HEIGHT|MEASUR|DATE_START|DATE_END|VAR_INFO|VAR_NAME|EQUIP|MANUFACTUR|MODEL|LOGGER",re.I)
MAX_GROUPS=30
MAX_ROWS_PER_GROUP=45

def dep():
    import importlib.util
    file=Path(__file__).resolve().with_name("12_repair_non_syv_science_holds.py")
    if not file.is_file() or file.is_symlink():
        raise ValueError("Pinned Stage12 helper missing beside Stage20")
    spec=importlib.util.spec_from_file_location("b04_stage20_dependency",str(file))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def records(m,file):
    with m.regular(file).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not {"VARIABLE","DATAVALUE","GROUP_ID"}.issubset(reader.fieldnames):
            raise ValueError("Original BIF missing VARIABLE, DATAVALUE or GROUP_ID")
        out=list(reader)
    if not out:
        raise ValueError("Original BIF is empty")
    return out

def summarize(site,rows):
    groups=defaultdict(list)
    for r in rows:
        groups[(r.get("GROUP_ID") or "").strip()].append(r)
    relevant=set()
    for gid,recs in groups.items():
        for r in recs:
            var=(r.get("VARIABLE") or "").strip()
            value=(r.get("DATAVALUE") or "").strip()
            if AIR_TEMP.search(var) or AIR_TEMP.search(value):
                relevant.add(gid)
                break
    selected=sorted(relevant)
    print(f"\nSTAGE20 BIF SITE {site} total_rows={len(rows)} groups={len(groups)} air_temp_candidate_groups={len(selected)}")
    counts=Counter((r.get("VARIABLE") or "").strip() for r in rows if META.search(r.get("VARIABLE") or ""))
    print("STAGE20 BIF METADATA FIELD INVENTORY",site," ".join(f"{k}:{v}" for k,v in sorted(counts.items())[:55]) or "NONE")
    if not selected:
        print("STAGE20 NO EXPLICIT AIR-TEMPERATURE GROUP FOUND; EVIDENCE INSUFFICIENT, not sensor absent")
    for gid in selected[:MAX_GROUPS]:
        group=groups[gid]
        print(f"STAGE20 POSSIBLE TEMPERATURE BIF GROUP site={site} GROUP_ID={gid or '(empty)'} rows={len(group)}")
        priority=[r for r in group if META.search(r.get("VARIABLE") or "") or
                  AIR_TEMP.search(r.get("VARIABLE") or "") or AIR_TEMP.search(r.get("DATAVALUE") or "")]
        shown=priority[:MAX_ROWS_PER_GROUP]
        for r in shown:
            var=(r.get("VARIABLE") or "").strip()
            val=(r.get("DATAVALUE") or "").strip().replace("\n"," ").replace("\r"," ")
            print("  BIF",var,"=",val[:200])
        if len(priority)>len(shown):
            print("  BIF more relevant rows omitted",len(priority)-len(shown))
        print("  STAGE20 GROUP_STATUS: CANDIDATE_METADATA_ONLY, instrument/time association not independently proven")
    if len(selected)>MAX_GROUPS:
        print("STAGE20 additional air-temp metadata candidate groups omitted",len(selected)-MAX_GROUPS)
    print("STAGE20 SITE CONCLUSION:",site,
          "raw independent sensor/timestamp QC must be obtained or evidence remains insufficient")
    return len(selected)

def selftest():
    assert len(EIGHT)==8 and sum(map(len,CASES.values()))==6
    assert all(len(v)==64 for v in ORIGINAL_SHA.values())
    assert AIR_TEMP.search("TA_F") and AIR_TEMP.search("TA_1_1_1")
    assert AIR_TEMP.search("Air temperature")
    assert not AIR_TEMP.search("LOCATION_LAT")
    assert META.search("VAR_INFO_HEIGHT")
    print("STAGE20 SELF-TEST PASS: six source events, metadata token filter, eight unchanged holds; read-only")

def audit():
    m=dep()
    receipt=json.loads(m.regular(S12/"stage12_receipt.json").read_text(encoding="utf-8"))
    if (receipt.get("target_unique_non_Syv_events")!=156 or
        receipt.get("successfully_resolved")!=148 or receipt.get("unresolved")!=8 or
        receipt.get("Postv5_approved") is not False):
        raise ValueError("Stage12 science state changed")
    ledger=records_for_decision(m,S12/"stage12_science_decisions.tsv")
    held={(r["site"],r["TIMESTAMP_START"]) for r in ledger
          if not r["status"].startswith("RESOLVED")}
    if len(ledger)!=156 or held!=EIGHT:
        raise ValueError("Eight original temperature science HOLDs changed")
    selections,targets,reasons,originals=m.get_inputs()
    group_counts={}
    for site in CASES:
        src=originals[site]["native"]
        if m.sha(src)!=ORIGINAL_SHA[site]:
            raise ValueError("Original immutable FLUXMET SHA does not match "+site)
        point=m.point_for(site,src)
        prior=receipt["original_native_BIF_points"][site]
        if m.sha(Path(prior["BIF_file"]))!=prior["BIF_sha256"]:
            raise ValueError("Original BIF SHA changed: "+site)
        for label in ("latitude","longitude","offset_hours"):
            if abs(point[label]-prior[label])>1e-4:
                raise ValueError("Original BIF geometry or time offset changed: "+site)
        if Path(point["BIF_file"])!=Path(prior["BIF_file"]):
            raise ValueError("BIF source path changed: "+site)
        print("\nSTAGE20 SOURCE VERIFIED",site,
              "FLUXMET_SHA",ORIGINAL_SHA[site],
              "BIF_SHA",prior["BIF_sha256"],
              "BIF_LOCAL_STANDARD_UTC_OFFSET",point["offset_hours"],
              "events",",".join(CASES[site]))
        group_counts[site]=summarize(site,records(m,Path(point["BIF_file"])))
    print("\nSTAGE20 RESULT: 3/3 ORIGINAL SITE BIF METADATA INVENTORIED, 6/6 EVENT SOURCE CONTRACTS PINNED")
    print("STAGE20 TEMPERATURE_METADATA_CANDIDATE_GROUP_COUNTS",group_counts)
    print("STAGE20 SCIENCE DECISION: 0 OFFICIAL T HOLDS CLEARED; 8/8 PRESERVED")
    print("STAGE20 US-Syv 606 OLD SCIENCE HOLDS + 10 STAGE07 ERA EDGE SKIPS DEFERRED")
    print("STAGE20 READ ONLY: NO SOURCE/QC/CDS/POST-v5/DATM/CIME/SLURM/MODEL WRITES")

def records_for_decision(m,path):
    with m.regular(path).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames:return []
        return list(rd)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--audit",action="store_true")
    a=p.parse_args()
    selftest()
    if a.audit:audit()

if __name__=="__main__":
    main()

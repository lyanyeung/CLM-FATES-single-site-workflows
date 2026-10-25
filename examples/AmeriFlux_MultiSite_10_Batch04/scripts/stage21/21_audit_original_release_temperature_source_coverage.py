#!/usr/bin/env python3
"""Batch04 Stage21 — FINAL internal-only temperature source availability gate.

Read-only original release inventory for US-SP1, US-SRG, US-Seg. Inspect every
extracted original package CSV *header* to identify whether any raw,
unprocessed, independently QC'd tower air-temperature channel was actually
supplied, versus FLUXMET consolidated/MDS, ERA/ERA5 and BIF products.

No presumed independent data: names are candidates ONLY and scientific source
verification is still required. The script does not auto-repair, download,
write output products, contact site PIs, clear any HOLD, or run CIME/SLURM.
Its intended output is a bounded terminal-only provenance evidence inventory.
"""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

EXP = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
STAGE12 = EXP/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
EVENTS = {
    "US-SP1": ("200710151730","200801160800","200801160830","200802030800"),
    "US-SRG": ("201903191200",),
    "US-Seg": ("201612271800",),
}
ORIG_SHA = {
    "US-SP1":"d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963",
    "US-SRG":"bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567",
    "US-Seg":"2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d",
}
BIF_SHA = {
    "US-SP1":"7d8be284cacb1d4b8e503fb15ba354beabb8db4ed82c0225a50f3d5e77081890",
    "US-SRG":"68d2a977e11919d298e6df46b60d05ff6d8c1e06fb4771cf7a749c7710a7e64a",
    "US-Seg":"29be3a4e5c216eb8749cb36273c7e8678936ca3f207518266abd8579c4412ae3",
}
EIGHT={(s,t) for s,events in EVENTS.items() for t in events}|{
    ("US-SP1","200010091800"),("US-SP1","200010091830")
}
TEMP_COL=re.compile(r"^(?:TA(?:_|$)|T_AIR(?:_|$)|AIR_TEMP(?:_|$)|TEMP(?:_|$))",re.I)
INSTRUMENT_COL=re.compile(r"^(?:TA|T_AIR|AIR_TEMP|TEMP)_(?:[1-9][0-9]*(?:_|$)|RAW(?:_|$)|OBS(?:_|$))",re.I)
DATA_PRODUCT_FIELDS={"TA_F","TA_F_QC","TA_F_MDS","TA_F_MDS_QC","TA_ERA","TA_ERA_QC"}
BIF_KEYS=("FLUX_MEASUREMENTS_VARIABLE","FLUX_MEASUREMENTS_METHOD","FLUX_MEASUREMENTS_DATE_START","FLUX_MEASUREMENTS_OPERATIONS")
def helper():
    import importlib.util
    path=Path(__file__).resolve().with_name("12_repair_non_syv_science_holds.py")
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("Pinned Stage12 dependency missing beside Stage21 script")
    spec=importlib.util.spec_from_file_location("batch04_stage21_stage12",str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def csv_header(m,path):
    with m.regular(path).open(encoding="utf-8-sig",newline="") as fh:
        reader=csv.reader(fh)
        header=next(reader,None)
    if not header or len(header)!=len(set(header)):
        raise ValueError("Empty or duplicate native file header "+str(path))
    return header
def native_inventory(m,site,native,bif):
    d=native.parent
    if not d.is_dir() or d.is_symlink():
        raise ValueError("Original raw release directory absent or symlinked "+site)
    files=sorted(d.glob("*.csv"),key=lambda x:x.name)
    if len(files)!=16:
        raise ValueError(f"Original Stage01 16-file CSV release expectation changed {site}: {len(files)}")
    if native not in files or bif not in files:
        raise ValueError("Original FLUXMET/BIF files missing from release CSV inventory "+site)
    kinds=Counter()
    possible_sensor=[]
    for file in files:
        if file.is_symlink() or not file.is_file():
            raise ValueError("Original CSV is not a regular file "+str(file))
        name=file.name
        if not name.startswith(f"AMF_{site}_FLUXNET_"):
            raise ValueError("Foreign site file in original release "+name)
        label=("BIF" if "_BIF_" in name else
               "FLUXMET" if "_FLUXMET_" in name else
               "ERA5" if "_ERA5_" in name else
               "OTHER")
        kinds[label]+=1
        columns=csv_header(m,file)
        ts=[x for x in columns if TEMP_COL.search(x)]
        potential=[x for x in ts if INSTRUMENT_COL.search(x)]
        if potential:
            possible_sensor.append((name,potential))
        print("STAGE21 ORIGINAL CSV",site,name,"class",label,
              "columns",len(columns),
              "T_FIELD_CANDIDATES",",".join(ts[:35]) or "NONE",
              "EXTRA_T_FIELDS_OMITTED",max(len(ts)-35,0))
        if "_FLUXMET_HH_" in name:
            for standard in DATA_PRODUCT_FIELDS - {"TA_ERA_QC"}:
                if standard not in columns:
                    raise ValueError("Expected native FLUXMET temperature field missing "+standard)
    if kinds["BIF"]!=1 or kinds["FLUXMET"]<1 or kinds["ERA5"]<1:
        raise ValueError("Expected original BIF, FLUXMET and ERA5 product families "+site)
    print("STAGE21 PRODUCT COUNTS",site,dict(sorted(kinds.items())))
    print("STAGE21 POSSIBLE INSTRUMENT-CHANNEL COLUMN CANDIDATES",site,
          possible_sensor if possible_sensor else "NONE_DETECTED_IN_RELEASE_HEADERS")
    print("STAGE21 IMPORTANT: a candidate column name does not prove independently measured, native sensor-verified values")
    return len(possible_sensor)
def bif_flux_notes(m,site,bif):
    found={}
    with m.regular(bif).open(encoding="utf-8-sig",newline="") as h:
        reader=csv.DictReader(h)
        if not reader.fieldnames or not {"VARIABLE","DATAVALUE","GROUP_ID"}.issubset(reader.fieldnames):
            raise ValueError("Original BIF schema changed")
        for row in reader:
            field=(row.get("VARIABLE") or "").strip()
            if field in BIF_KEYS:
                gid=(row.get("GROUP_ID") or "").strip()
                found.setdefault(gid,{})[field]=(row.get("DATAVALUE") or "").strip()
    print("STAGE21 BIF FLUX_MEASUREMENTS GROUPS",site,len(found))
    for gid,item in sorted(found.items()):
        var=item.get("FLUX_MEASUREMENTS_VARIABLE","")
        method=item.get("FLUX_MEASUREMENTS_METHOD","")
        start=item.get("FLUX_MEASUREMENTS_DATE_START","")
        print("STAGE21 BIF FLUX GROUP",site,"GROUP_ID",gid,
              "FLUX_MEASUREMENTS_VARIABLE",var[:100] or "MISSING",
              "FLUX_MEASUREMENTS_METHOD",method[:100] or "MISSING",
              "FLUX_MEASUREMENTS_DATE_START",start[:100] or "MISSING")
    print("STAGE21 BIF NOTE: FLUX_MEASUREMENTS metadata are not assumed air-temperature instrument evidence")
def decisions(m):
    path=STAGE12/"stage12_science_decisions.tsv"
    with m.regular(path).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames:return []
        return list(rd)
def selftest():
    assert len(EIGHT)==8 and sum(map(len,EVENTS.values()))==6
    assert all(len(v)==64 for v in ORIG_SHA.values())
    assert all(len(v)==64 for v in BIF_SHA.values())
    assert TEMP_COL.search("TA_F") and TEMP_COL.search("TA_1_1_1")
    assert not INSTRUMENT_COL.search("TA_F") and INSTRUMENT_COL.search("TA_1_1_1")
    assert not TEMP_COL.search("SW_IN_F") and not TEMP_COL.search("TAU")
    print("STAGE21 SELF-TEST PASS: source families, raw-channel candidate distinction, 8 science holds; read-only")
def audit():
    m=helper()
    receipt=json.loads(m.regular(STAGE12/"stage12_receipt.json").read_text(encoding="utf-8"))
    if (receipt.get("target_unique_non_Syv_events")!=156 or receipt.get("successfully_resolved")!=148 or
        receipt.get("unresolved")!=8 or receipt.get("Postv5_approved") is not False):
        raise ValueError("Pinned Stage12 science state changed")
    ds=decisions(m)
    held={(r["site"],r["TIMESTAMP_START"]) for r in ds if not r["status"].startswith("RESOLVED")}
    if len(ds)!=156 or held!=EIGHT:
        raise ValueError("Original eight science holds changed")
    sel,targets,reasons,originals=m.get_inputs()
    candidates={}
    for site,events in EVENTS.items():
        native=originals[site]["native"]
        if m.sha(native)!=ORIG_SHA[site]:
            raise ValueError("Original SHA mismatch "+site)
        point=m.point_for(site,native)
        bif=Path(point["BIF_file"])
        oldpoint=receipt["original_native_BIF_points"][site]
        if m.sha(bif)!=BIF_SHA[site] or oldpoint["BIF_sha256"]!=BIF_SHA[site]:
            raise ValueError("Original BIF source SHA changed "+site)
        for key in ("latitude","longitude","offset_hours"):
            if abs(float(point[key])-float(oldpoint[key]))>1e-4:
                raise ValueError("BIF original site coordinate/time offset mismatched "+site)
        print("\nSTAGE21 SOURCE VERIFIED",site,"native_SHA",ORIG_SHA[site],
              "BIF_SHA",BIF_SHA[site],"original_events",",".join(events))
        candidates[site]=native_inventory(m,site,native,bif)
        bif_flux_notes(m,site,bif)
        print("STAGE21 SCIENCE HOLD: original QC0 temperature remains unadjudicated",site)
    print("\nSTAGE21 RESULT: 3/3 ORIGINAL 16-FILE RELEASES INVENTORIED, 6/6 ORIGINAL T EVENT CONTRACTS RETAINED")
    print("STAGE21 SENSOR-LIKE COLUMN FILE COUNTS",candidates)
    print("STAGE21 DECISION: THIS IS A SOURCE-AVAILABILITY INVENTORY, NOT A SENSOR VALIDATION")
    print("STAGE21 IF NO INDEPENDENT RAW SENSOR+TIMESTAMP QC IDENTIFIED: STOP INTERNAL-ONLY ESCALATION; REQUEST ORIGINAL SITE RECORDS")
    print("STAGE21 8/8 ORIGINAL T SCIENCE HOLDS PRESERVED; US-Syv 606 OLD HOLDS + 10 STAGE07 ERA EDGE SKIPS DEFERRED")
    print("STAGE21 READ ONLY: NO SOURCE/QA/QC/CDS/POST-v5/DATM/CIME/SLURM/MODEL WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--audit",action="store_true")
    args=p.parse_args()
    selftest()
    if args.audit:audit()
if __name__=="__main__":
    main()

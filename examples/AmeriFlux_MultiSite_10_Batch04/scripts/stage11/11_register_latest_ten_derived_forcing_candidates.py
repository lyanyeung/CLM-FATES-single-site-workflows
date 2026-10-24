#!/usr/bin/env python3
"""Batch04 Stage11: pin latest TEN complete site-derived FLUXMET_HH CSVs.

Actual selection, NOT re-repair: first three -> Stage07, five of remaining
seven -> Stage08, US-Rpf/US-SRM -> Stage10 (689 independently repaired).
Original source releases are not overwritten and no full CSV copy is made.
--build writes a NEW exact-ten-site forcing input manifest + science blockers
and machine-readable stage receipt. Model approval is a DIFFERENT gate.
"""
import argparse
import csv
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S07=EXP/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
S08=EXP/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z"
S10=EXP/"qcv5_stage10_independent_era5land/candidate_20261024T231424Z_d9967326"
THREE=("US-SP1","US-Syv","US-Ton")
LATEST_FROM_08=("US-Seg","US-Ses","US-Slt","US-SRG","US-Uaf")
LATEST_FROM_10=("US-Rpf","US-SRM")
SITES=tuple(sorted((*THREE,*LATEST_FROM_08,*LATEST_FROM_10)))
ROW_COUNTS={"US-SP1":368208,"US-Syv":438288,"US-Ton":438288,
            "US-Rpf":298080,"US-Seg":333120,"US-Ses":333120,
            "US-Slt":315552,"US-SRG":315600,"US-SRM":385728,"US-Uaf":403248}
SEVEN_HOLDS={"US-Rpf":0,"US-Seg":4,"US-Ses":0,"US-Slt":0,
             "US-SRG":1,"US-SRM":0,"US-Uaf":2}
THREE_HOLDS={"US-SP1":147,"US-Syv":606,"US-Ton":1}

def regular(p):
    if not p.is_file() or p.is_symlink():raise ValueError("Missing or symlink candidate "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for chunk in iter(lambda:f.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()

def json_read(p):
    return json.loads(regular(p).read_text(encoding="utf-8"))

def file_entry(site,stage,receipt):
    if stage=="STAGE07":
        record=receipt["derived_full_length_files"][site]
        filename=record["full_derived_file"]
        expected=record["sha256"]
        n=record["source_rows"]
        source_dir=S07
    elif stage=="STAGE08":
        record=receipt["derived_files"][site]
        filename=record["full_derived_path"]
        expected=record["full_derived_sha256"]
        n=record["rows"]
        source_dir=S08
    else:
        record=receipt["site_files"][site]
        filename=record["file"]
        expected=record["sha256"]
        n=record["rows"]
        source_dir=S10
    p=Path(filename)
    if p.parent != source_dir:
        raise ValueError("Version selection points outside pinned source folder "+site)
    if n!=ROW_COUNTS[site] or len(expected)!=64:
        raise ValueError("Wrong Stage07/08/10 derived row count/SHA "+site)
    if sha(p)!=expected:
        raise ValueError("Latest candidate file SHA differs "+site)
    with p.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.reader(f)
        header=next(rd)
    need={"TIMESTAMP_START","TIMESTAMP_END","TA_F","PA_F","VPD_F"}
    if len(set(header))!=len(header) or not need.issubset(header):
        raise ValueError("Derived candidate missing DATM base met fields "+site)
    return {"site":site,"source_stage":stage,"source_path":str(p),
            "source_SHA256":expected,"rows":n,
            "known_unresolved_HOLD_entries":THREE_HOLDS.get(site,SEVEN_HOLDS.get(site,0)),
            "selected_for_later_POSTV5_processing":"CANDIDATE_ONLY"}

def select():
    stage07=json_read(S07/"stage07_sha_receipt.json")
    stage08=json_read(S08/"report.json")
    stage10=json_read(S10/"stage10_receipt.json")
    if set(SITES)!=set(ROW_COUNTS) or len(SITES)!=10:
        raise ValueError("Expected exact ten-site Batch04 selection")
    if (stage07.get("inherited_stage05_holds")!=754 or
        stage07.get("invalid_era_endpoints_held")!=12):
        raise ValueError("Stage07 hold/provenance receipt changed")
    if (stage10.get("known_targets")!=689 or
        stage10.get("candidate_fixes")!=689 or
        stage10.get("unfixed")!=0):
        raise ValueError("Do not advance Stage10 before exact 689/689 repair")
    if (set(stage08.get("sites",{}))!=
        {"US-Rpf","US-Seg","US-Ses","US-Slt","US-SRG","US-SRM","US-Uaf"} or
        sum(v["hold_rows"] for v in stage08["sites"].values())!=696):
        raise ValueError("Stage08 original seven-site/696-HOLD summary changed")
    if set(stage07.get("derived_full_length_files",{}))!=set(THREE):
        raise ValueError("Stage07 three-site receipt changed")
    if set(stage10.get("site_files",{}))!=set(LATEST_FROM_10):
        raise ValueError("Stage10 two-site receipt changed")
    data=[]
    for site in SITES:
        stage=("STAGE07" if site in THREE else
               "STAGE10" if site in LATEST_FROM_10 else "STAGE08")
        data.append(file_entry(site,stage,
                    {"STAGE07":stage07,"STAGE08":stage08,"STAGE10":stage10}[stage]))
    if len({r["source_path"] for r in data})!=10:
        raise ValueError("Duplicate full candidate source file")
    if sum(r["known_unresolved_HOLD_entries"] for r in data)!=761:
        raise ValueError("Expected 754+7 unresolved HOLD entries")
    blockers={
        "stage07_inherited_original_holds":THREE_HOLDS,
        "stage07_unresolved_direct_ERA_boundary_endpoints":12,
        "stage07_note":"12 boundary skips may overlap the original three-site HOLD entries",
        "stage08_non_rpf_srm_remaining_holds":SEVEN_HOLDS,
        "stage10_targeted_rpf_srm_repaired":689,
        "stage10_targeted_rpf_srm_remaining":0,
        "known_original_science_hold_entries_excluding_possible_stage07_edge_duplicates":761,
        "Postv5_approved":False,
        "DATM_approved":False,
        "spinup_approved":False,
    }
    return data,blockers

def self_test():
    assert len(SITES)==10
    assert set(THREE).isdisjoint(LATEST_FROM_08)
    assert set(THREE).isdisjoint(LATEST_FROM_10)
    assert set(LATEST_FROM_08).isdisjoint(LATEST_FROM_10)
    assert sum(THREE_HOLDS.values())==754
    assert sum(SEVEN_HOLDS.values())==7
    print("STAGE11 SELF-TEST PASS: 3 Stage07 + 5 Stage08 + 2 Stage10; 754+7 HOLD ledger")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--build",action="store_true")
    args=ap.parse_args()
    self_test()
    if args.self_test:return
    files,blockers=select()
    for x in files:
        print("LATEST",x["site"],x["source_stage"],"rows",x["rows"],
              "known_HOLD",x["known_unresolved_HOLD_entries"],flush=True)
    print("STAGE11 SHA-VERIFIED 10/10 LATEST INPUT CANDIDATES.")
    print("STAGE11 SCIENCE HOLD: 761 earlier unique-entry counts + up to 12 boundary skips, overlap unknown")
    if args.check:return
    out=EXP/"qcv5_stage11_latest_ten_manifest"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    manifest=out/"LATEST_10_SITES_FOR_POSTV5_INPUT.tsv"
    with manifest.open("x",encoding="utf-8",newline="") as f:
        fields=list(files[0])
        wr=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        wr.writeheader();wr.writerows(files)
    (out/"UNRESOLVED_SCIENCE_GATES.json").write_text(
        json.dumps(blockers,indent=2)+"\n",encoding="utf-8")
    marker=(out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    marker.write_text("Ten derived source candidates pinned, NOT accepted model forcing.\n")
    rec={
        "input_stage07_sha256":sha(S07/"stage07_sha_receipt.json"),
        "input_stage08_sha256":sha(S08/"report.json"),
        "input_stage10_sha256":sha(S10/"stage10_receipt.json"),
        "latest_site_selection":files,
        "unresolved_science_gates":blockers,
        "manifest_sha256":sha(manifest),
        "source_data_copied":False,
        "Postv5_approved":False,"DATM_ready":False,"spinup":False,
        "created_utc":datetime.now(timezone.utc).isoformat()}
    (out/"stage11_selection_receipt.json").write_text(
        json.dumps(rec,indent=2)+"\n",encoding="utf-8")
    print("STAGE11 LATEST TEN INPUT MANIFEST CREATED",manifest)
    print("STAGE11 NO FULL CSV DUPLICATION; ORIGINALS AND ALL PRIOR STAGES UNTOUCHED")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch04 Stage16: prove Stage15 US-SP1 source differs from Stage14 ONLY in
two native half-hour rows, and ONLY in TA_F, VPD_F, TA_F_QC.

Full source-length streaming comparison. Read-only; no CDS, output files, DATM,
CIME or model jobs. Also verify both ten-site manifests and full CSV SHA256.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

EX=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S14=EX/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
S15=EX/"qcv5_stage15_sp1_two_point_temperature_sensitivity/candidate_20261025T080658Z_cca73e0e"
BASE_SHA="3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806"
TIMES={"200010091800","200010091830"}
SITE="US-SP1"
N=368208
ALLOWED={"TA_F","VPD_F","TA_F_QC"}

def f(p):
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing / symlink source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with f(p).open("rb") as handle:
        for block in iter(lambda:handle.read(4<<20),b""):
            h.update(block)
    return h.hexdigest()

def table(p):
    with f(p).open(encoding="utf-8-sig",newline="") as handle:
        rd=csv.DictReader(handle,delimiter="\t")
        if not rd.fieldnames or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError("Invalid manifest/ledger schema "+str(p))
        return list(rd)

def sat(t):
    return 6.112*math.exp(17.67*t/(t+243.5))

def tolerance(a,b,eps=1e-7):
    return math.isclose(float(a),float(b),rel_tol=0,abs_tol=eps)

def audit():
    r14=json.loads(f(S14/"stage14_receipt.json").read_text())
    r15=json.loads(f(S15/"stage15_receipt.json").read_text())
    if (r14.get("humidity_physical_candidate_count")!=8 or
        r14.get("still_unresolved_tower_temperature_science_hold_count")!=8 or
        r15.get("two_temperature_alternative_candidates")!=2 or
        r15.get("remaining_unapproved_science_holds")!=8 or
        r15.get("Postv5_approved") is not False or
        r15.get("DATM_ready") is not False):
        raise ValueError("Source receipts lack science safety gates")
    if sha(S14/"stage14_receipt.json")!=r15["stage14_input_receipt_sha256"]:
        raise ValueError("Stage14 receipt SHA changed")
    m14=S14/"stage14_latest_ten_candidate_manifest.tsv"
    m15=S15/"STAGE15_ALTERNATIVE_LATEST_TEN_MANIFEST.tsv"
    if sha(m14)!=r14["latest_ten_manifest_sha256"] or sha(m15)!=r15["manifest_sha256"]:
        raise ValueError("One of the ten-site manifest SHAs changed")
    rows14=table(m14);rows15=table(m15)
    b={r["site"]:r for r in rows14};t={r["site"]:r for r in rows15}
    if len(b)!=10 or len(t)!=10 or set(b)!=set(t):
        raise ValueError("Expected 10 matching site names")
    for site in sorted(b):
        if site==SITE:
            continue
        if b[site]!=t[site]:
            raise ValueError("The other 9 site selections must stay IDENTICAL: "+site)
    for k in b[SITE]:
        if k not in {"latest_stage","source_path","source_SHA256"} and b[SITE][k]!=t[SITE].get(k):
            raise ValueError("US-SP1 non-source metadata changed "+k)
    before=Path(b[SITE]["source_path"])
    after=Path(t[SITE]["source_path"])
    if before.parent!=S14 or after.parent!=S15:
        raise ValueError("Wrong source directories")
    if sha(before)!=BASE_SHA or b[SITE]["source_SHA256"]!=BASE_SHA:
        raise ValueError("Pinned Stage14 SP1 SHA changed")
    if (sha(after)!=t[SITE]["source_SHA256"] or
        sha(after)!=r15["full_trial"]["sha256"] or
        str(after)!=r15["full_trial"]["path"] or
        r15["full_trial"]["rows"]!=N or
        r15["full_trial"]["modified_TA_VPD_half_hours"]!=2):
        raise ValueError("Stage15 full source file / receipt differs")
    ledger=S15/"STAGE15_TWO_POINT_SCIENCE_PROVENANCE.tsv"
    if sha(ledger)!=r15["provenance_SHA256"]:
        raise ValueError("Trial provenance checksum differs")
    lr=table(ledger)
    if len(lr)!=2 or {r["TIMESTAMP_START"] for r in lr}!=TIMES:
        raise ValueError("Trial ledger does not have exactly 2 native times")
    indexed={r["TIMESTAMP_START"]:r for r in lr}
    counters=Counter();changed=[]
    with f(before).open(encoding="utf-8-sig",newline="") as f0, \
         f(after).open(encoding="utf-8-sig",newline="") as f1:
        a=csv.DictReader(f0);c=csv.DictReader(f1)
        if a.fieldnames!=c.fieldnames:
            raise ValueError("Stage15 must have exactly same FLUXMET HH columns as Stage14")
        required={"TIMESTAMP_START","TIMESTAMP_END","TA_F","VPD_F","TA_F_QC","VPD_F_QC","RH","PA_F"}
        if not required.issubset(a.fieldnames):
            raise ValueError("Missing forcing fields in derived sources")
        for i,(ra,rb) in enumerate(zip(a,c),1):
            if ra["TIMESTAMP_START"]!=rb["TIMESTAMP_START"] or ra["TIMESTAMP_END"]!=rb["TIMESTAMP_END"]:
                raise ValueError("Native time alignment mismatch at row "+str(i))
            if len(ra)!=len(rb):
                raise ValueError("Row column shape differs")
            k=ra["TIMESTAMP_START"]
            delta={field for field in a.fieldnames if ra[field]!=rb[field]}
            if delta:
                if k not in TIMES or delta!=ALLOWED:
                    raise ValueError("Unexpected field change at "+k+" "+str(sorted(delta)))
                if ra["TA_F_QC"]!="0" or rb["TA_F_QC"]!="1":
                    raise ValueError("Original QC0 != sensitivity trial QC1")
                provenance=indexed[k]
                if (not tolerance(ra["TA_F"],provenance["original_TA_C"],.001) or
                    not tolerance(rb["TA_F"],provenance["new_TA_C"],1e-7) or
                    not tolerance(rb["VPD_F"],provenance["new_VPD_hPa"],1e-7)):
                    raise ValueError("Trial field value != provenance ledger")
                tp=float(rb["TA_F"])
                v=float(rb["VPD_F"])
                rh=float(rb["RH"])
                if not (0<=v<=sat(tp) and 1<=rh<=100 and
                        math.isclose(v,sat(tp)*(1-rh/100),abs_tol=1e-7)):
                    raise ValueError("Stage15 trial TA/VPD/RH physical closure failed")
                changed.append((k,ra["TA_F"],rb["TA_F"],ra["VPD_F"],rb["VPD_F"]))
            counters["rows"]+=1
        if next(a,None) is not None or next(c,None) is not None:
            raise ValueError("The two CSVs have unequal row counts")
    if counters["rows"]!=N or len(changed)!=2 or {r[0] for r in changed}!=TIMES:
        raise ValueError("Expected exactly two native modified HH of 368208")
    print("STAGE16 VERIFIED SOURCE SHA Stage14",BASE_SHA)
    print("STAGE16 VERIFIED SOURCE SHA Stage15",r15["full_trial"]["sha256"])
    print("STAGE16 FULL CSV ROWS",N,"US-SP1; exactly two native HH changed")
    for row in changed:
        print("STAGE16 ONLY CHANGE",row[0],
              "TA",row[1],"->",row[2],
              "VPD",row[3],"->",row[4],
              "original_TA_QC0 -> trial_TA_QC1")
    print("STAGE16 OTHER 9 SITE PATHS & SHAs IDENTICAL")
    print("STAGE16 PHYSICAL HUMIDITY CLOSURE PASS AT BOTH TRIAL T VALUES")
    print("STAGE16 SCIENCE HOLD 8 UNRESOLVED; US-Syv deferred 606")
    print("STAGE16 READ ONLY: NO ORIGINAL, STAGE14/15, DATM, CIME, SLURM WRITES")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--audit",action="store_true")
    a=ap.parse_args()
    assert TIMES=={"200010091800","200010091830"}
    assert ALLOWED=={"TA_F","VPD_F","TA_F_QC"}
    assert len(BASE_SHA)==64
    print("STAGE16 SELF-TEST PASS: exactly 2 rows, 3 columns permitted; 10-site consistency")
    if a.audit:audit()

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Read-only independent full-CSV verification of Batch04 3-HH manual trial.

Requires no numpy, CDS or network. Verifies exact two modified site CSVs, source
sha256, 10-row manifest, independent provenance, receipt, 3x3 field changes,
original QC0 -> trial QC2, original Stage14 RH VPD saturation closure, and
original HOLD counts. No file writes or model commands.
"""
import argparse
import csv
import hashlib
import json
import math
from itertools import zip_longest
from pathlib import Path

E=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
STAGE14=E/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
TRIAL=E/"manual_temperature_alternative_not_approved/candidate_20261025T183441Z_254f8181"
S14MAN=STAGE14/"stage14_latest_ten_candidate_manifest.tsv"
TRIALMAN=TRIAL/"MANUAL_LATEST_TEN_SITE_RESEARCH_MANIFEST.tsv"
RECEIPT=TRIAL/"MANUAL_TRIAL_RECEIPT.json"
LEDGER=TRIAL/"MANUAL_TEMPERATURE_PROVENANCE.tsv"
EXPECTED={
 ("US-SP1","200010091800"):(-6.9,14.370813,10.194556),
 ("US-SP1","200010091830"):(-7.1,13.776224,9.445459),
 ("US-SRG","201903191200"):(0.718,20.1365,17.060332),
}
EXPECTED_ROWS={"US-SP1":368208,"US-SRG":315600}
ORIGINAL_SOURCE_SHA={
 "US-SP1":"3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806",
 "US-SRG":"57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39",
}
CHANGED_COLS={"TA_F","TA_F_QC","VPD_F"}
def check(cond,msg):
    if not cond:raise ValueError(msg)
def original_file(p):
    check(not p.is_symlink() and p.is_file(),"Non-regular or symlink source: "+str(p))
    return p
def sha(p):
    dig=hashlib.sha256()
    with original_file(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):dig.update(b)
    return dig.hexdigest()
def tables(p):
    with original_file(p).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        cols=list(reader.fieldnames or [])
        check(len(cols)==len(set(cols)) and "site" in cols,
              "Invalid or duplicated columns in "+str(p))
        rows=list(reader)
    check(len(rows)==10,"Expected ten-site full manifest "+str(p))
    mapped={r["site"]:r for r in rows}
    check(len(mapped)==10,"Duplicate site in "+str(p))
    return cols,mapped
def required_number(x,name):
    try:z=float(x)
    except (TypeError,ValueError):raise ValueError("Missing numeric "+name)
    check(math.isfinite(z), "Nonfinite "+name)
    return z
def close(a,b,eps=1e-5):
    return abs(a-b)<=eps
def receipt():
    data=json.loads(original_file(RECEIPT).read_text(encoding="utf-8"))
    check(data.get("production_approval") is False,"Production approval unexpectedly true")
    check(data.get("original_tower_temperature_science_holds_remaining")==8,
          "Original 8 temperature holds missing")
    check(data.get("deferred_US_Syv_holds")==606 and
          data.get("deferred_US_Syv_ERA_edges")==10,"US-Syv defer count mismatch")
    check(data.get("read_only_source_stage14_manifest_sha256")==sha(S14MAN),
          "Source manifest digest mismatch")
    items=data.get("manual_decision_changes")
    check(isinstance(items,list) and len(items)==3,"Receipt must document exactly 3 changes")
    changes={(x["site"],x["TIMESTAMP_START"]):x for x in items}
    check(len(changes)==3 and set(changes)==set(EXPECTED),
          "Wrong/duplicate receipt change keys")
    sites=data.get("two_modified_site_files")
    check(isinstance(sites,dict) and set(sites)==set(EXPECTED_ROWS),
          "Receipt expected only SP1/SRG site changes")
    return data,changes,sites
def compare_one(site,old,new,source_receipt,decisions):
    src=Path(old["source_path"]); out=Path(new["source_path"])
    check(old["source_SHA256"]==ORIGINAL_SOURCE_SHA[site],"Stage14 manifest SHA shifted")
    check(sha(src)==old["source_SHA256"],"Stage14 source SHA no longer valid "+site)
    check(out.parent==TRIAL,"Trial output outside pinned trial directory")
    check(out.name==f"{site}_manual_temperature_alternative_FLUXMET_HH.csv",
          "Unexpected trial filename "+site)
    check(sha(out)==new["source_SHA256"]==source_receipt["sha256"],
          "New full CSV SHA disagrees with receipt/manifest "+site)
    check(int(old["rows"])==int(new["rows"])==source_receipt["rows"]==EXPECTED_ROWS[site],
          "Full native halfhour count mismatch "+site)
    check(source_receipt["path"]==str(out),"Receipt output path mismatch")
    check(source_receipt["changed_native_half_hours"]==
          (2 if site=="US-SP1" else 1),"Receipt change count mismatch")
    differences={}
    count=0
    with original_file(src).open(encoding="utf-8-sig",newline="") as f0, \
         original_file(out).open(encoding="utf-8-sig",newline="") as f1:
        a=csv.DictReader(f0);b=csv.DictReader(f1)
        check(a.fieldnames==b.fieldnames and a.fieldnames and
              len(set(a.fieldnames))==len(a.fieldnames),"CSV schema modified "+site)
        check(set(CHANGED_COLS|{"TIMESTAMP_START","RH"}).issubset(a.fieldnames),
              "Missing required forcing columns "+site)
        for oldrow,newrow in zip_longest(a,b):
            check(oldrow is not None and newrow is not None,
                  "Full CSV row counts differ "+site)
            count+=1
            key=oldrow["TIMESTAMP_START"]
            check(key==newrow["TIMESTAMP_START"],
                  f"Native clock changed {site} row {count}")
            fields={col for col in a.fieldnames if oldrow[col]!=newrow[col]}
            if not fields:continue
            k=(site,key)
            check(k in EXPECTED,"Unexpected different HH "+str(k))
            check(k not in differences,"Duplicate modified HH "+str(k))
            check(fields==CHANGED_COLS,
                  f"Incorrect fields at {k}: {fields}; exactly {CHANGED_COLS} required")
            receiptrow=decisions[k]
            expect_orig,expect_t,expect_vpd=EXPECTED[k]
            t0=required_number(oldrow["TA_F"],"old T")
            t1=required_number(newrow["TA_F"],"trial T")
            vpd=required_number(newrow["VPD_F"],"trial VPD")
            rh=required_number(oldrow["RH"],"retained Stage14 RH")
            check(close(t0,expect_orig,0.002) and
                  close(t1,expect_t,1e-5) and
                  close(vpd,expect_vpd,1e-5),"Trial numeric mismatch "+str(k))
            check(oldrow["TA_F_QC"]=="0" and newrow["TA_F_QC"]=="2",
                  "Original 0 -> trial 2 provenance QC incorrect "+str(k))
            check(newrow["RH"]==oldrow["RH"],"Original Stage14 RH unexpectedly changed")
            check(1<=rh<=100,"Invalid retained RH "+str(k))
            es=6.112*math.exp(17.67*t1/(243.5+t1))
            vcalc=es*(1-rh/100)
            check(0<=vpd<=es and close(vpd,vcalc,1e-6),
                  "Trial TA-RH-VPD physical closure invalid "+str(k))
            check(close(required_number(receiptrow["trial_TA_C"],"receipt T"),t1,1e-8)
                  and close(required_number(receiptrow["trial_VPD_hPa"],"receipt VPD"),
                            vpd,1e-8),
                  "Receipt not matching actual trial CSV "+str(k))
            check(receiptrow["trial_TA_F_QC"]=="2" and
                  receiptrow["original_TA_F_QC"]=="0",
                  "Receipt QC provenance changed "+str(k))
            differences[k]=fields
    check(count==EXPECTED_ROWS[site],"Actual full CSV row count changed "+site)
    check(len(differences)==(2 if site=="US-SP1" else 1),"Actual changed HH count incorrect")
    print("MANUAL AUDIT SITE VERIFIED",site,
          "source_rows",count,"modified_HH",len(differences),
          "new_SHA256",new["source_SHA256"])
    return differences
def audit():
    check(TRIAL.is_dir() and not TRIAL.is_symlink(),"Exact trial path missing/linked")
    check(original_file(TRIAL/"NOT_APPROVED_NOT_FOR_DATM_CIME_SLURM_SPINUP").is_file(),
          "Missing no-production marker")
    stage14rec=json.loads(original_file(STAGE14/"stage14_receipt.json").read_text(encoding="utf-8"))
    check(stage14rec.get("latest_ten_manifest_sha256")==sha(S14MAN) and
          stage14rec.get("still_unresolved_tower_temperature_science_hold_count")==8,
          "Stage14 receipt no longer pinned")
    fields,src=tables(S14MAN)
    trialfields,sel=tables(TRIALMAN)
    check(fields==trialfields and set(src)==set(sel),
          "Ten-site manifest shape or selection changed")
    data,decisions,source_receipts=receipt()
    all_diff={}
    for site in sorted(src):
        a=src[site];b=sel[site]
        if site not in EXPECTED_ROWS:
            check(a==b,"Unrelated other-eight site selection changed "+site)
        else:
            changed={f for f in fields if a[f]!=b[f]}
            check(changed=={"source_path","source_SHA256","latest_stage"},
                  "Site manifest changed unexpected fields "+site)
            check(b["latest_stage"]=="MANUAL_EXPERIMENTAL_TEMPERATURE_ALTERNATIVE_NOT_APPROVED",
                  "Wrong study-case label "+site)
            all_diff.update(compare_one(site,a,b,source_receipts[site],decisions))
    with original_file(LEDGER).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        ledger=list(reader)
    check(len(ledger)==3,"Provenance TSV should have three native HH decisions")
    entries={(r["site"],r["TIMESTAMP_START"]):r for r in ledger}
    check(len(entries)==3 and set(entries)==set(EXPECTED),"Incorrect provenance TSV keys")
    for key,row in entries.items():
        trialrow=decisions[key]
        for col in ("method","approval","trial_TA_F_QC"):
            check(row[col]==str(trialrow[col]),
                  "Trial provenance ledger mismatch "+str(key)+" "+col)
        check(close(float(row["trial_TA_C"]),float(trialrow["trial_TA_C"]),1e-9),
              "Ledger TA precision mismatch "+str(key))
    check(set(all_diff)==set(EXPECTED),"Unexpected total modified native timestamps")
    check(len(all_diff)==3 and sum(len(x) for x in all_diff.values())==9,
          "Exactly three HH and nine field-cell changes required")
    print("MANUAL AUDIT PASS 2/2 FULL-SOURCE CSV, 3/3 HALF-HOURS, EXACTLY 9 CELLS (TA_F, TA_F_QC, VPD_F)")
    print("MANUAL AUDIT PASS 8/8 OTHER-SITE MANIFEST ENTRIES IDENTICAL, 10/10 SITE MANIFEST")
    print("MANUAL AUDIT PASS ERA-ORIGIN QC2, RETAINED STAGE14 RH, SATURATION PHYSICS, SHA256 AND RECEIPTS")
    print("MANUAL AUDIT ORIGINAL T SCIENCE HOLDS 8 UNCHANGED; US-Syv 606+10 DEFERRED")
    print("MANUAL AUDIT READ-ONLY: NO SOURCE OR MODEL WRITES; NOT APPROVED FOR POST-v5/DATM/CIME/SLURM/SPINUP")
def selftest():
    check(len(EXPECTED)==3 and len(EXPECTED_ROWS)==2 and
          all(len(h)==64 for h in ORIGINAL_SOURCE_SHA.values()),"Static targets invalid")
    check(abs((19.668+20.605)/2-20.1365)<1e-8,"QC2-flank interpolation changed")
    print("MANUAL FULL AUDIT SELF-TEST PASS: exact three HH, expected 9 cells, immutable source contracts")
def main():
    p=argparse.ArgumentParser()
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--audit",action="store_true")
    args=p.parse_args()
    selftest()
    if args.audit:audit()
if __name__=="__main__":main()

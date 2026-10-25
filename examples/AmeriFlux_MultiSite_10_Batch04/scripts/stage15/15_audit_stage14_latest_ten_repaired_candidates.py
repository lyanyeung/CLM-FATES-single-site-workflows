#!/usr/bin/env python3
"""Batch04 Stage15: read-only SHA, ten-site version and eight-row difference audit.

Checks the latest Stage14 3 full derived FLUXMET HH source candidates plus
7 upstream full derived candidates. For each of the 8 VPD/RH fixes, enforces
physical humidity closure, original TA/PA/QC untouched, and a separate
unresolved tower-temperature science hold. For the 3 edited sites compares
EVERY native half-hour row against its Stage12 baseline: differences are
permitted ONLY for VPD_F and RH at the 8 predefined exact timestamps.
Other 7 sites have no file modifications in this Stage14 update.
No output writes, CDS requests, DATM, Slurm jobs or model approval.
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from itertools import zip_longest
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S12=ROOT/"qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c"
S14=ROOT/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
COUNTS={"US-Rpf":298080,"US-SP1":368208,"US-SRG":315600,
        "US-SRM":385728,"US-Seg":333120,"US-Ses":333120,
        "US-Slt":315552,"US-Syv":438288,"US-Ton":438288,"US-Uaf":403248}
EDIT_COUNTS={"US-SP1":6,"US-SRG":1,"US-Seg":1}
HOLD_TIMES={
("US-SP1","200010091800"),("US-SP1","200010091830"),
("US-SP1","200710151730"),("US-SP1","200801160800"),
("US-SP1","200801160830"),("US-SP1","200802030800"),
("US-SRG","201903191200"),("US-Seg","201612271800")
}

def require(p):
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/untrusted file: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with require(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()

def csv_rows(p,delimiter="\t"):
    with require(p).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter=delimiter)
        if not reader.fieldnames:raise ValueError("Missing CSV header")
        return list(reader)

def value(v):
    try:f=float(v)
    except (TypeError,ValueError):return None
    return f if math.isfinite(f) and f not in (-9999,-6999) else None

def sat(t):
    if t is None or not -80<=t<=65:return None
    return 6.112*math.exp(17.67*t/(243.5+t))

def read_receipts():
    rec14=json.loads(require(S14/"stage14_receipt.json").read_text())
    rec12=json.loads(require(S12/"stage12_receipt.json").read_text())
    if not (rec14.get("humidity_physical_candidate_count")==8 and
        rec14.get("still_unresolved_tower_temperature_science_hold_count")==8 and
        rec14.get("source_TA_PA_QC_all_unchanged") is True and
        rec14.get("Postv5_approved") is False and
        rec14.get("DATM_ready") is False and
        rec14.get("spinup") is False and
        rec12.get("successfully_resolved")==148 and
        rec12.get("unresolved")==8 and
        rec12.get("target_unique_non_Syv_events")==156):
        raise ValueError("Expected Stage12 148+8 and Stage14 source flags differ")
    if sha(S12/"stage12_receipt.json")!=rec14["source_stage12_receipt_sha256"]:
        raise ValueError("Stage12 receipt changed")
    current=S14/"stage14_latest_ten_candidate_manifest.tsv"
    if sha(current)!=rec14["latest_ten_manifest_sha256"]:
        raise ValueError("Stage14 latest-ten manifest receipt differs")
    old=S12/"stage12_repaired_source_candidates.tsv"
    if sha(old)!=rec12["receipt_sha256"]["stage12_repaired_source_candidates.tsv"]:
        raise ValueError("Stage12 ten-site manifest receipt differs")
    ledger=S14/"stage14_eight_humidity_candidates.tsv"
    holds=S14/"UNRESOLVED_EIGHT_TOWER_TEMPERATURE_HOLDS.tsv"
    if sha(ledger)!=rec14["humidity_ledger_sha256"]:
        raise ValueError("Eight humidity numerical-closure ledger SHA differs")
    if len(csv_rows(holds))!=8 or sha(ledger)!=sha(holds):
        raise ValueError("Separate eight source-temperature HOLD receipt differs")
    if not (S14/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Source science gate warning marker absent")
    latest={r["site"]:r for r in csv_rows(current)}
    prior={r["site"]:r for r in csv_rows(old)}
    if set(latest)!=set(COUNTS) or set(prior)!=set(COUNTS):
        raise ValueError("Stage14/12 latest cohort must be identical ten-site set")
    for site in sorted(COUNTS):
        row=latest[site]
        if int(row["rows"])!=COUNTS[site]:raise ValueError("Wrong native row count "+site)
        src=Path(row["source_path"])
        if src.is_symlink() or src.parent != (S14 if site in EDIT_COUNTS
                                          else Path(prior[site]["source_path"]).parent):
            raise ValueError("Unexpected candidate source folder "+site)
        if site not in EDIT_COUNTS and row["source_path"]!=prior[site]["source_path"]:
            raise ValueError("Unchanged site source path must stay pinned "+site)
        if sha(src)!=row["source_SHA256"]:
            raise ValueError("Candidate source SHA mismatch "+site)
        if site not in EDIT_COUNTS and row["source_SHA256"]!=prior[site]["source_SHA256"]:
            raise ValueError("No source changes allowed on untouched sites "+site)
    rows=csv_rows(ledger)
    fixes={(r["site"],r["TIMESTAMP_START"]):r for r in rows}
    holds_exact={(r["site"],r["TIMESTAMP_START"]) for r in csv_rows(holds)}
    if set(fixes)!=HOLD_TIMES or holds_exact!=HOLD_TIMES:
        raise ValueError("Eight exact correction/science-HOLD timestamps differ")
    for site in EDIT_COUNTS:
        r=rec14["derived_full_candidate_files"][site]
        if r["sha256"]!=latest[site]["source_SHA256"] or r["rows"]!=COUNTS[site] or r["repaired_humidity_times"]!=EDIT_COUNTS[site]:
            raise ValueError("Stage14 full output metadata inconsistent "+site)
    return latest,prior,fixes

def verify_edited_site(site,latest,prior,fixes):
    a=Path(prior[site]["source_path"])
    b=Path(latest[site]["source_path"])
    target_keys={k for (s,k) in fixes if s==site}
    verified=set();count=0;alterations=Counter()
    with require(a).open(encoding="utf-8-sig",newline="") as fa, \
         require(b).open(encoding="utf-8-sig",newline="") as fb:
        x=csv.DictReader(fa);y=csv.DictReader(fb)
        if not x.fieldnames or not y.fieldnames:raise ValueError("Missing FLUXMET header")
        old=set(x.fieldnames);new=set(y.fieldnames)
        if not (old<=new and new-old<= {"RH"}):
            raise ValueError("Stage14 changed column schema beyond optional RH "+site)
        if len(new)!=len(y.fieldnames):
            raise ValueError("Stage14 duplicate field name")
        for left,right in zip_longest(x,y):
            if left is None or right is None:raise ValueError("Stage14 row mismatch "+site)
            count+=1
            key=left.get("TIMESTAMP_START")
            if key!=right.get("TIMESTAMP_START"):
                raise ValueError("Native halfhour ordering changed "+site)
            is_target=key in target_keys
            if is_target:
                if key in verified:raise ValueError("Stage14 repeated target "+site)
                verified.add(key)
            for field in new:
                before=left.get(field,"") if field in old else ""
                after=right.get(field,"")
                if before==after:continue
                if not (is_target and field in ("VPD_F","RH")):
                    raise ValueError("Changed forbidden source cell: "+site+" "+key+" "+field+" "+repr((before,after)))
                alterations[field]+=1
            if is_target:
                record=fixes[site,key]
                t=value(right.get("TA_F"))
                pa=value(right.get("PA_F"))
                vp=value(right.get("VPD_F"))
                rh=value(right.get("RH"))
                e=sat(t)
                if any(v is None for v in (t,pa,vp,rh,e)):
                    raise ValueError("Missing target values "+site+" "+key)
                if not (1<=rh<=100 and 0<=vp<=e+1e-9 and
                        abs(vp-e*(1-rh/100))<1e-7):
                    raise ValueError("Target VPD/RH not physically consistent "+site+" "+key)
                if (abs(t-value(record["TA_F_retained_C"]))>1e-8 or
                    abs(pa-value(record["PA_retained_kPa"]))>1e-8 or
                    abs(vp-value(record["new_VPD_hPa"]))>1e-7 or
                    abs(rh-value(record["RH_water_pct"]))>1e-7 or
                    right.get("TA_F_QC")!="0"):
                    raise ValueError("TA/PA/QC or humidity receipt mismatch "+site+" "+key)
                if record["temperature_science_status"]!="HOLD_QC0_TOWER_TEMPERATURE_CONFLICT":
                    raise ValueError("Missing disputed TA science HOLD "+site+" "+key)
    if count!=COUNTS[site] or verified!=target_keys:
        raise ValueError("Full CSV rows/targets mismatch "+site)
    if alterations["VPD_F"]!=EDIT_COUNTS[site] or alterations["RH"]!=EDIT_COUNTS[site]:
        raise ValueError("Not exactly two humidity cells changed per target "+site)
    print("STAGE15 EXACT FULL ROW COMPARISON",site,"PASS",count,
          "rows; VPD cell changes",alterations["VPD_F"],
          "RH cell changes",alterations["RH"],
          "TA/PA/all QC and other timestamps UNCHANGED")

def self_test():
    assert len(COUNTS)==10 and len(HOLD_TIMES)==8
    assert sum(EDIT_COUNTS.values())==8
    assert abs(sat(0)-6.112)<1e-10
    print("STAGE15 SELF-TEST PASS: exact site cohort and numeric VPD-RH closure test")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--audit",action="store_true")
    args=parser.parse_args()
    self_test()
    if args.self_test:return
    latest,prior,fixes=read_receipts()
    for site in sorted(COUNTS):
        print("STAGE15 SHA PIN",site,latest[site]["latest_stage"],COUNTS[site],
              latest[site]["source_SHA256"],flush=True)
    for site in sorted(EDIT_COUNTS):
        verify_edited_site(site,latest,prior,fixes)
    print("STAGE15 10/10 CURRENT SOURCES VERIFIED; EXACT 8/8 HUMIDITY REPAIRS VERIFIED")
    print("STAGE15 SCIENCE GATES: 8/8 original QC0 tower T disputes OPEN, US-Syv 606 inherited HOLD entries PLUS up to 10 jump edge skips DEFERRED")
    print("STAGE15 FINAL STATE: NOT Post-v5 approved, NOT DATM, NOT spinup")
    print("STAGE15 READ ONLY: no CSV, NetCDF, ERA, SOURCE, CASE OR SLURM WRITES")
if __name__=="__main__":main()

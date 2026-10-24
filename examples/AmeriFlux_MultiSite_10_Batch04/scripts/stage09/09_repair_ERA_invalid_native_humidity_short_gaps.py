#!/usr/bin/env python3
"""Batch04 Stage09: APPLY bounded native-tower humidity fixes at ERA-invalid times.

Targets: Stage08 US-Rpf (688) and US-SRM (1) ERA_PAIR_HUMIDITY_INVALID
HOLD entries. For valid original TA/VPD keep VPD; if RH invalid derive RH
from existing native T/VPD. For physically invalid/missing native VPD runs
of 1..4 exact HH, interpolate original VPD between two good tower QC0/QC1
neighbours of the SAME YEAR and with consistent T/VPD; derive paired RH.
Long/bad-boundary runs stay HOLD. NO invalid paired ERA substitution.

Outputs TWO NEW COMPLETE DERIVED FLUXMET CSVs plus SHA ledgers, not just
another audit. Seven-site Stage08, original releases, Stage07, DATM/CIME
and model cases are NEVER modified. Not yet science-approved Post-v5.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
STAGE08=ROOT/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z"
EXPECTED={"US-Rpf":{"rows":298080,"holds":688,"patches":0},
          "US-SRM":{"rows":385728,"holds":1,"patches":4}}
SITES=tuple(EXPECTED)
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
EVENT_REASON="ERA_PAIR_HUMIDITY_INVALID"
INPUT_FIELDS=("TIMESTAMP_START","TIMESTAMP_END","TA_F","VPD_F","VPD_F_QC")
MAX_GAP=4
BOUNDARY_MAX_T_DIFF_C=8.
BOUNDARY_MAX_VPD_DIFF_HPA=5.

def require_file(p):
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/unsafe input file: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with require_file(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def num(x):
    s=str(x if x is not None else "").strip()
    if s.upper() in MISSING:return None
    v=float(s)
    return v if math.isfinite(v) else None

def fmt(v):
    return "%.12g"%v

def sat(t):
    if t is None or not -80<=t<=65:return None
    return 6.112*math.exp(17.67*t/(t+243.5))

def physical(t,v):
    es=sat(t)
    return es is not None and v is not None and 0<=v<=es*1.00001

def rh_at(t,v):
    if not physical(t,v):return None
    return max(0.,min(100.,100*(1-v/sat(t))))

def start_date(k):
    return datetime.strptime(k,"%Y%m%d%H%M")

def check_stage08():
    report=json.loads(require_file(STAGE08/"report.json").read_text())
    if (report.get("mode")!="BUILD_CANDIDATE_OVERLAY" or
        report.get("scientific_status")!="POST_QCV5_REVIEW_REQUIRED" or
        set(report.get("sites",{}))!=
        {"US-Rpf","US-Seg","US-Ses","US-Slt","US-SRG","US-SRM","US-Uaf"}):
        raise ValueError("Stage08 report site/mode differs")
    if sha(STAGE08/"candidate_patch.csv")!=report["candidate_patch_sha256"]:
        raise ValueError("Stage08 patch SHA256 changed")
    holds=[]
    with require_file(STAGE08/"unresolved_hold.csv").open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        need=("site","TIMESTAMP_START","TIMESTAMP_END","reason")
        if not reader.fieldnames or not set(need).issubset(reader.fieldnames):
            raise ValueError("Stage08 unresolved HOLD schema changed")
        holds=list(reader)
    if len(holds)!=696:raise ValueError("Expected 696 Stage08 holds")
    for site,d in EXPECTED.items():
        info=report["sites"][site]
        if info["rows"]!=d["rows"] or info["hold_rows"]!=d["holds"] or info["patch_rows"]!=d["patches"]:
            raise ValueError("Stage08 input census changed "+site)
        if sum(x["site"]==site for x in holds)!=d["holds"]:
            raise ValueError("Site HOLD count changed "+site)
        original=Path(info["paths"]["native"])
        if sha(original)!=info["source_provenance"]["native"]["sha256"]:
            raise ValueError("Original immutable native SHA changed: "+site)
        candidate=Path(report["derived_files"][site]["full_derived_path"])
        if not str(candidate).startswith(str(STAGE08)+"/") or candidate.is_symlink():
            raise ValueError("Stage08 full candidate path unexpected")
        if sha(candidate)!=report["derived_files"][site]["full_derived_sha256"]:
            raise ValueError("Existing full-length candidate SHA changed: "+site)
    return report,holds

def source_minimal(path, expected_rows):
    rows=[]
    with require_file(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(INPUT_FIELDS).issubset(reader.fieldnames):
            raise ValueError("Native temperature/VPD/timestamp/QC schema missing")
        previous=None
        for row in reader:
            k=row["TIMESTAMP_START"]
            dt=start_date(k)
            if (row["TIMESTAMP_END"]!=
                 (dt+timedelta(minutes=30)).strftime("%Y%m%d%H%M") or
                (previous is not None and dt!=previous)):
                raise ValueError("Discontinuous native half-hours "+k)
            previous=dt+timedelta(minutes=30)
            rows.append({
                "key":k,"year":dt.year,"t":num(row["TA_F"]),
                "v":num(row["VPD_F"]), "rh":num(row.get("RH")),
                "qc":str(row["VPD_F_QC"]).strip()
            })
    if len(rows)!=expected_rows:
        raise ValueError("Stage08 full source row total changed")
    return rows

def select_replacements(rows, requested):
    """Return new fields by time, remaining error notes and grouped episodes."""
    positions={r["key"]:i for i,r in enumerate(rows)}
    if len(positions)!=len(rows):raise ValueError("Duplicate source native half-hour")
    if not requested.issubset(positions):
        raise ValueError("Missing Stage08 exact HOLD timestamps")
    patches={}
    unresolved={}
    counts=Counter()
    invalid=[]
    for k in sorted(requested):
        r=rows[positions[k]]
        if physical(r["t"],r["v"]):
            # Preserve valid native VPD (including original QC0).
            target_rh=rh_at(r["t"],r["v"])
            if r["rh"] is None or r["rh"]<0 or r["rh"]>100.05:
                patches[k]={"RH":target_rh}
                counts["derived_RH_from_valid_native_VPD"]+=1
            else:
                counts["native_VPD_already_valid_no_change"]+=1
            continue
        invalid.append(positions[k])
        unresolved[k]="NATIVE_VPD_PHYSICALLY_INVALID_AWAIT_SHORT_GAP_CHECK"
    episodes=[]
    i=0
    while i<len(invalid):
        a=invalid[i];b=a+1;i+=1
        while i<len(invalid) and invalid[i]==b:
            b+=1;i+=1
        n=b-a
        reason=""
        valid_bounds=a>0 and b<len(rows) and n<=MAX_GAP
        if not valid_bounds:
            reason="LONG_GAP_GT4_OR_SITE_EDGE"
        else:
            l,r=rows[a-1],rows[b]
            if (l["year"]!=r["year"] or
                any(rows[j]["year"]!=l["year"] for j in range(a,b))):
                reason="CROSSES_CALENDAR_YEAR"
            elif not (
                physical(l["t"],l["v"]) and physical(r["t"],r["v"]) and
                l["qc"] in {"0","1"} and r["qc"] in {"0","1"} and
                -55<=l["t"]<=52 and -55<=r["t"]<=52 and
                abs(l["t"]-r["t"])<=BOUNDARY_MAX_T_DIFF_C and
                abs(l["v"]-r["v"])<=BOUNDARY_MAX_VPD_DIFF_HPA):
                reason="BAD_OR_UNTRUSTWORTHY_TOWER_BOUNDARY"
        if not reason:
            lv=rows[a-1]["v"];rv=rows[b]["v"]
            proposed=[]
            for j in range(a,b):
                t=rows[j]["t"]
                v=lv+(rv-lv)*(j-a+1)/(n+1)
                if not physical(t,v) or t is None or not -55<=t<=52:
                    reason="INTERPOLATED_VPD_EXCEEDS_SATURATION_OR_BAD_T"
                    break
                proposed.append((rows[j]["key"],v,rh_at(t,v)))
            if not reason:
                for k,v,rh in proposed:
                    patches[k]={"VPD_F":v,"RH":rh}
                    unresolved.pop(k)
                    counts["interpolated_VPD_short_gap_halfhours"]+=1
                counts["interpolated_episodes"]+=1
        if reason:
            for j in range(a,b):unresolved[rows[j]["key"]]=reason
            counts["unresolved_invalid_VPD_halfhours"]+=n
        episodes.append({
            "first_native_key":rows[a]["key"],
            "last_native_key":rows[b-1]["key"],
            "n_halfhours":n,
            "action":"QCv5_SHORT_VPD_INTERPOLATED" if not reason else reason
        })
    if counts["interpolated_VPD_short_gap_halfhours"]+counts["unresolved_invalid_VPD_halfhours"]!=len(invalid):
        raise ValueError("Invalid-VPD event partition is not exhaustive")
    if len(patches)+len(unresolved)>len(requested):
        raise ValueError("Proposed edits+HOLD partition unexpectedly larger than source")
    if (set(patches)&set(unresolved)) or (set(patches)|set(unresolved))!=requested-{rows[positions[k]]["key"] for k in requested if physical(rows[positions[k]]["t"],rows[positions[k]]["v"]) and k not in patches}:
        raise ValueError("HOLD/patch target coverage inconsistent")
    counts["ERA_pair_invalid_source_targets"]=len(requested)
    counts["original_VPD_invalid_source_targets"]=len(invalid)
    counts["RH_only_repaired"]=sum(set(v)=={"RH"} for v in patches.values())
    return patches,unresolved,episodes,counts

def materialize(full_input, full_output, updates, expected_rows):
    modified_rows=0; modified_cells=0;matched=set();n=0
    with require_file(full_input).open(encoding="utf-8-sig",newline="") as fi, \
         full_output.open("x",encoding="utf-8",newline="") as fo:
        reader=csv.DictReader(fi)
        if not reader.fieldnames or not set(INPUT_FIELDS).issubset(reader.fieldnames):
            raise ValueError("Missing derived input schema")
        fields=list(reader.fieldnames)
        if "RH" not in fields and any("RH" in d for d in updates.values()):
            fields.append("RH")
        writer=csv.DictWriter(fo,fieldnames=fields)
        writer.writeheader()
        for row in reader:
            n+=1;k=row["TIMESTAMP_START"]
            if k in updates:
                if k in matched:raise ValueError("Duplicate target timestamp")
                matched.add(k)
                changing=False
                for var,v in updates[k].items():
                    old=num(row.get(var))
                    if old is None or abs(old-v)>1e-10:
                        row[var]=fmt(v)
                        modified_cells+=1;changing=True
                modified_rows+=int(changing)
            writer.writerow(row)
    if n!=expected_rows or matched!=set(updates):
        raise ValueError("Incomplete new full site file")
    return {"original_rows":n,"modified_halfhours":modified_rows,
            "modified_variable_cells":modified_cells,
            "derived_file":str(full_output),"sha256":sha(full_output)}

def table(path,rows,fields):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)

def self_test():
    t=10;v=3
    assert physical(t,v) and rh_at(t,v)>0
    assert not physical(t,40) and not physical(t,-1)
    good=[{"key":"202501010000","year":2025,"t":10,"v":2,"qc":"0","rh":80},
          {"key":"202501010030","year":2025,"t":10,"v":18,"qc":"2","rh":-5},
          {"key":"202501010100","year":2025,"t":10,"v":4,"qc":"0","rh":70}]
    patch,hold,ep,counts=select_replacements(good,{"202501010030"})
    assert not hold and abs(patch["202501010030"]["VPD_F"]-3)<1e-9
    assert ep[0]["action"]=="QCv5_SHORT_VPD_INTERPOLATED"
    valid=[{"key":"202501010000","year":2025,"t":10,"v":0,"qc":"0","rh":102}]
    p,h,e,_=select_replacements(valid,{"202501010000"})
    assert not h and set(p["202501010000"])=={"RH"} and p["202501010000"]["RH"]==100
    print("STAGE09 SELF-TEST PASS: exact short-gap native VPD repair and native QC0 preservation")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--apply",action="store_true")
    args=p.parse_args()
    self_test()
    if args.self_test:return
    report,holds=check_stage08()
    keys={}
    for site in SITES:
        filtered=[h for h in holds if h["site"]==site]
        if len(filtered)!=EXPECTED[site]["holds"] or any(
                h["reason"]!=EVENT_REASON for h in filtered):
            raise ValueError("Unexpected original held humidity reason: "+site)
        if len({h["TIMESTAMP_START"] for h in filtered})!=len(filtered):
            raise ValueError("Duplicate HOLD time at "+site)
        keys[site]={h["TIMESTAMP_START"] for h in filtered}
    before={}
    patches={}
    unresolved={}
    episodes={}
    counts={}
    for site in SITES:
        info=report["derived_files"][site]
        before[site]=Path(info["full_derived_path"])
        rows=source_minimal(before[site],EXPECTED[site]["rows"])
        patches[site],unresolved[site],episodes[site],counts[site]=select_replacements(rows,keys[site])
        print("STAGE09 CANDIDATES",site,dict(counts[site]),
              "remaining_HOLD",len(unresolved[site]),flush=True)
    out=ROOT/"qcv5_stage09_native_humidity_fallback"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage09 derived tower-interpolated/consistent RH candidate; unresolved native humidity holds remain.\n")
    allchanges=[]
    remaining=[]
    all_episodes=[]
    derived={}
    for site in SITES:
        for k,group in sorted(patches[site].items()):
            for var,new in group.items():
                allchanges.append({"site":site,"TIMESTAMP_START":k,"variable":var,
                    "new_candidate":fmt(new),
                    "method":"INTERPOLATE_NATIVE_VPD_MAX4_PLUS_DERIVED_RH"
                             if "VPD_F" in group else "NATIVE_VPD_RETAINED_DERIVE_RH"})
        for k,reason in sorted(unresolved[site].items()):
            remaining.append({"site":site,"TIMESTAMP_START":k,"reason":reason})
        for e in episodes[site]:
            all_episodes.append({"site":site,**e})
        destination=out/(site+"_Stage09_native_humidity_repaired_FLUXMET_HH.csv")
        derived[site]=materialize(before[site],destination,patches[site],EXPECTED[site]["rows"])
        print("STAGE09 DERIVED",site,"SHA256",derived[site]["sha256"],flush=True)
    # The other five stations' Stage08 holds remain as written.
    for h in holds:
        if h["site"] not in SITES:
            remaining.append({"site":h["site"],"TIMESTAMP_START":h["TIMESTAMP_START"],
                              "reason":h["reason"]})
    table(out/"stage09_applied_humidity_changes.csv",allchanges,
          ("site","TIMESTAMP_START","variable","new_candidate","method"))
    table(out/"stage09_remaining_stage08_holds.csv",remaining,
          ("site","TIMESTAMP_START","reason"))
    table(out/"stage09_native_invalid_VPD_episode_groups.csv",all_episodes,
          ("site","first_native_key","last_native_key","n_halfhours","action"))
    receipt={
        "source_stage08":str(STAGE08),
        "source_stage08_report_sha256":sha(STAGE08/"report.json"),
        "source_stage08_holds_sha256":sha(STAGE08/"unresolved_hold.csv"),
        "stage08_holds_total":len(holds),
        "targeted_original_holds":sum(len(keys[x]) for x in SITES),
        "target_site_counts":{x:dict(counts[x]) for x in SITES},
        "new_variable_patches":len(allchanges),
        "unresolved_remaining_stage08_holds":len(remaining),
        "native_invalid_VPD_episode_groups":len(all_episodes),
        "derived_files":derived,
        "original_and_stage08_unchanged":True,
        "model_approval":False,"Postv5_approved":False,"DATM_ready":False,
        "created_utc":datetime.now(timezone.utc).isoformat(),
    }
    receipt["file_sha256"]={f.name:sha(f) for f in (
        out/"stage09_applied_humidity_changes.csv",
        out/"stage09_remaining_stage08_holds.csv",
        out/"stage09_native_invalid_VPD_episode_groups.csv")}
    (out/"stage09_sha_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE09 SUCCESS:",out)
    print("STAGE09 APPLIED",len(allchanges),"variable patches, unresolved Stage08 HOLDs",
          len(remaining),"of previous",len(holds))
    print("NO ORIGINAL, STAGE07, STAGE08, DATM OR SLURM WRITES.")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch04 US-Syv: group 606 inherited science holds + 10 Stage07 bad ERA endpoints.

This is a REPORT, not any form of automated repair or model approval.
Reads only SHA-receipted Stage05/Stage06/Stage07 sources & complete
original native and Stage07 candidate tower series (438,288 HH each).
Prints physical status, reason groups, deduplicated exact timestamps,
contiguous episodes and short before/during/after context for the 12
highest-priority episodes. Paired TA_ERA/VPD_ERA is the downscaled
FLUXNET ERA product, NOT separately downloaded ERA5-Land.
Output to stdout only (operator can tee a log under HOME).
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S06=EXP/"reports/stage06_qcv5_candidate_effects_20261024T105030Z_8cc1f59c"
S07=EXP/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
SITE="US-Syv";NROWS=438288
TOWER_KEYS=("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH")
ERA_KEYS=("TIMESTAMP_START","TA_ERA","VPD_ERA")
MISS={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
def ck(ok,msg):
    if not ok:raise ValueError(msg)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Missing or symlinked verified source: "+str(p))
    return p
def digest(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def readjson(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def readtable(p,req):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        ck(r.fieldnames is not None and set(req).issubset(r.fieldnames),"Schema mismatch "+str(p))
        return list(r)
def num(z):
    z=str(z if z is not None else "").strip()
    if z.upper() in MISS:return None
    try:v=float(z)
    except ValueError:return None
    return v if math.isfinite(v) else None
def sat(t):
    if t is None or t<=-60 or t>=65:return None
    return 6.112*math.exp(17.67*t/(t+243.5))
def validity(r):
    if not r:return "MISSING"
    t=num(r.get("TA_F"));v=num(r.get("VPD_F"));rh=num(r.get("RH"))
    e=sat(t)
    if e is None:return "TA_INVALID"
    if v is None:return "VPD_MISSING"
    if v<0:return "VPD_NEGATIVE"
    if v>e+1e-8:return "VPD_ABOVE_ES_AT_TA"
    if rh is not None and (rh<0 or rh>100):return "RH_INVALID"
    return "TA_VPD_PHYS_VALID"
def episodes(times):
    groups=[]
    for k in sorted(times):
        now=datetime.strptime(k,"%Y%m%d%H%M")
        if not groups or now-datetime.strptime(groups[-1][-1],"%Y%m%d%H%M")>timedelta(minutes=30):
            groups.append([k])
        else:
            groups[-1].append(k)
    return groups
def collect(p,fields,need,expected_rows=None):
    wanted={}
    count=0
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        ck(r.fieldnames is not None and set(fields).issubset(r.fieldnames),
           "Wrong native or ERA source schema "+str(p))
        for row in r:
            count+=1
            k=row["TIMESTAMP_START"]
            if k in need:
                ck(k not in wanted,"Duplicated native HH "+k)
                wanted[k]={c:row[c] for c in fields}
    if expected_rows is not None:ck(count==expected_rows,"Native full row count changed "+str(p))
    ck(set(need).issubset(wanted),"Target/neighbor native HH missing from "+str(p))
    return wanted
def source_contract():
    report=readjson(S05/"report.json")
    r06=readjson(S06/"stage06_readonly_science_receipt.json")
    r07=readjson(S07/"stage07_sha_receipt.json")
    ck(report.get("mode")=="BUILD_CANDIDATE_OVERLAY","Stage05 science report mode changed")
    ck(r07.get("inherited_stage05_holds")==754 and
       r07.get("invalid_era_endpoints_held")==12,"Stage07 original inherited HOLD count changed")
    ck(digest(S05/"report.json")==r07["source_stage05_report_sha256"],
       "Stage07 pinned Stage05 report SHA changed")
    ck(digest(S05/"unresolved_hold.csv")==r06["stage05_holds_sha256"],
       "Stage06 pinned Stage05 hold-file SHA changed")
    ck(digest(S07/"stage07_unsafe_ERA_target_holds.csv")==
       r07["new_receipts_sha256"]["stage07_unsafe_ERA_target_holds.csv"],
       "Stage07 unsafe target receipt mismatch")
    meta=report["sites"][SITE]
    ck(meta.get("rows")==NROWS and meta.get("hold_rows")==606,
       "US-Syv original site rows/HOLD count changed")
    original=Path(meta["paths"]["native"])
    era=Path(meta["paths"]["era"])
    ck(digest(original)==meta["source_provenance"]["native"]["sha256"],
       "Original tower SHA mismatch")
    ck(digest(era)==meta["source_provenance"]["era"]["sha256"],
       "Original packaged ERA SHA mismatch")
    candidate_meta=r07["derived_full_length_files"][SITE]
    candidate=Path(candidate_meta["full_derived_file"])
    ck(digest(candidate)==candidate_meta["sha256"] and
       candidate_meta["source_rows"]==NROWS,
       "Stage07 US-Syv full CSV not source verified")
    return original,era,candidate
def triage():
    raw,grid,current=source_contract()
    allholds=readtable(S05/"unresolved_hold.csv",
                       ("site","TIMESTAMP_START","reason"))
    syv=[r for r in allholds if r["site"]==SITE]
    ck(len(allholds)==754 and len(syv)==606,"Original Stage05 606 science holds shifted")
    allskip=readtable(S07/"stage07_unsafe_ERA_target_holds.csv",
                      ("site","TIMESTAMP_START","reason"))
    skipped=[r for r in allskip if r["site"]==SITE]
    ck(len(allskip)==12 and len(skipped)==10,"Stage07 10 invalid ERA boundary endpoints changed")
    state=defaultdict(lambda:{"legacy":[],"skip":[]})
    for a in syv:state[a["TIMESTAMP_START"]]["legacy"].append(a["reason"])
    for a in skipped:state[a["TIMESTAMP_START"]]["skip"].append(a["reason"])
    keys=set(state)
    overlap=sum(bool(v["legacy"]) and bool(v["skip"]) for v in state.values())
    ck(606<=len(keys)<=616,"US-Syv deduplicated hold union outside expected range")
    context=set(keys)
    for k in keys:
        d=datetime.strptime(k,"%Y%m%d%H%M")
        for offset in (-2,-1,1,2):
            context.add((d+timedelta(minutes=30*offset)).strftime("%Y%m%d%H%M"))
    print("US-SYV SOURCE INTEGRITY PASSED: Stage05 + Stage06 + Stage07 receipts, original FLUXMET/paired ERA, stage07 derived HH")
    print("US-SYV ORIGINAL_HOLD_ENTRIES",len(syv),"STAGE07_SKIPPED_ENDPOINT_ENTRIES",
          len(skipped),"OVERLAP_EXACT_HH",overlap,"UNIQUE_HH_UNION",len(keys))
    print("LEGACY_HOLD_REASON_COUNTS",dict(Counter(y for r in syv for y in [r["reason"]])))
    print("STAGE07_SKIPPED_REASON_COUNTS",dict(Counter(y for r in skipped for y in [r["reason"]])))
    # Check both full native sources, only sample the exact 606/10 HH plus 1h flanks.
    native=collect(raw,TOWER_KEYS,context,expected_rows=NROWS)
    derived=collect(current,TOWER_KEYS,context,expected_rows=NROWS)
    paired=collect(grid,ERA_KEYS,context)
    print("SOURCE_CONTEXT_VERIFIED",len(context),"native HH and their +/-1hour flanks; paired ERA same-native keys")
    vals=Counter(validity(derived[k]) for k in keys)
    print("STAGE07_CANDIDATE_PHYSICAL_STATUS_AT_UNRESOLVED_HH",dict(vals))
    rawvals=Counter(validity(native[k]) for k in keys)
    print("ORIGINAL_SOURCE_PHYSICAL_STATUS_AT_UNRESOLVED_HH",dict(rawvals))
    print("STAGE07_CURRENT_HOLD_HH_WITH_VALID_TA_AND_VPD",
          sum(validity(derived[k])=="TA_VPD_PHYS_VALID" for k in keys),
          "(VALID PHYSICS DOES NOT MEAN SCIENTIFIC SOURCE HOLD APPROVED)")
    groups=episodes(keys)
    print("UNIQUE_CONTIGUOUS_HOLD_EPISODES",len(groups),
          "LONGEST_HH",max(map(len,groups)) if groups else 0,
          "OVER_24_HH",sum(len(g)>24 for g in groups))
    ranked=sorted(groups,key=lambda z:(
        -sum(validity(derived[k])!="TA_VPD_PHYS_VALID" for k in z),
        -sum(bool(state[k]["skip"]) for k in z),-len(z),z[0]))
    print("EPISODE_START EPISODE_END HH HOURS ORIG_HOLDS SKIPPED_ERA_STAGE07 PHYS_INVALID_CANDIDATE HOLD_REASONS")
    for group in ranked[:40]:
        hold=sum(bool(state[k]["legacy"]) for k in group)
        skip=sum(bool(state[k]["skip"]) for k in group)
        bad=sum(validity(derived[k])!="TA_VPD_PHYS_VALID" for k in group)
        reasons=Counter(z for k in group for z in set(state[k]["legacy"]+state[k]["skip"]))
        print(group[0],group[-1],len(group),len(group)*0.5,hold,skip,bad,
              ";".join(k+":"+str(v) for k,v in reasons.most_common(3)))
    print("\nPRIORITY_CONTEXT_FOR_TOP_12_EPISODES: original vs Stage07 candidate and SAME-NATIVE packaged ERA")
    fmt=lambda z:f"{z:.3f}" if z is not None else "NA"
    for ix,group in enumerate(ranked[:12],1):
        selection={group[0],group[-1],group[len(group)//2]}
        for t in (group[0],group[-1]):
            d=datetime.strptime(t,"%Y%m%d%H%M")
            selection.update((d+timedelta(minutes=30*k)).strftime("%Y%m%d%H%M") for k in (-2,-1,1,2))
        print("=== EPISODE",ix,group[0],"to",group[-1],"HH",len(group),"===")
        print("TIME FLAG RAW_T QC RAW_VPD QC STAGE07_T QC STAGE07_VPD QC STAGE07_RH PACKAGED_TA_ERA PACKAGED_VPD_ERA STAGE07_PHYS")
        for k in sorted(selection):
            if k not in native or k not in derived or k not in paired:continue
            a,b,c=native[k],derived[k],paired[k]
            print(k,"HOLD" if k in keys else "CONTEXT",
                  fmt(num(a["TA_F"])),a["TA_F_QC"],fmt(num(a["VPD_F"])),a["VPD_F_QC"],
                  fmt(num(b["TA_F"])),b["TA_F_QC"],fmt(num(b["VPD_F"])),b["VPD_F_QC"],
                  fmt(num(b["RH"])),fmt(num(c["TA_ERA"])),fmt(num(c["VPD_ERA"])),
                  validity(b))
    print("US-SYV READ_ONLY COMPLETE; NO SOURCE, REPAIR, DATM, CIME, SLURM OR MODEL WRITES")
    print("MANUAL NEXT GATE: inspect only ambiguous clustered episodes; do not demand 606 individual manual votes")
def selftest():
    assert len(episodes(["201001010000","201001010030","201001010130"]))==2
    assert validity({"TA_F":"10","VPD_F":"-0.1","RH":""})=="VPD_NEGATIVE"
    assert validity({"TA_F":"20","VPD_F":"5","RH":""})=="TA_VPD_PHYS_VALID"
    assert len("201001010000")==12
    print("US-SYV TRIAGE SELF-TEST PASS: 606 + 10 with dedup; SHA receipt and physical source checks; read only")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    a=p.add_mutually_exclusive_group(required=True)
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--triage",action="store_true")
    opts=p.parse_args();selftest()
    if opts.triage:triage()
if __name__=="__main__":main()

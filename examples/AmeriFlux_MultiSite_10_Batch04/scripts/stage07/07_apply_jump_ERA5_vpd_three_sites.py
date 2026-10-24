#!/usr/bin/env python3
"""Batch04 Stage07: create REAL derived FLUXMET candidates with exact-time ERA5 VPD.

User decision: replace both endpoints of Stage06's 210 flagged jump edges
with the SAME-TIMESTAMP packaged FLUXNET ERA5 VPD, when physically valid.
Recompute RH from direct ERA VPD and the retained (native/Stage05) tower TA.
At other timestamps protect physically valid original US-Ton VPD QC0.
Retain Stage05 temperature/pressure short-gap fixes and other humidity repairs.
US-Syv invalid ERA cases remain HOLD. Original releases, Stage05/Stage06 and
existing model inputs are NEVER overwritten.

--self-test: synthetic physics, no file reads or writes.
--apply: write NEW full-length three-site derived CSVs, replacement ledger,
         skipped-invalid ERA target ledger, and SHA256 provenance receipt.
Do NOT feed these incomplete candidates to CIME until remaining HOLDs cleared.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=ROOT/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S06=ROOT/"reports/stage06_qcv5_candidate_effects_20261024T105030Z_8cc1f59c"
EXACT={"US-SP1":(368208,87,147,19),"US-Syv":(438288,534,606,12),
       "US-Ton":(438288,4715,1,179)}
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
HEADS=("TIMESTAMP_START","TIMESTAMP_END","TA_F","PA_F","VPD_F","RH",
       "TA_F_QC","PA_F_QC","VPD_F_QC")
ERAS=("TA_ERA","VPD_ERA","PA_ERA")
FIELDS=("site","TIMESTAMP_START","TIMESTAMP_END","variable","original",
        "candidate","method","reason","original_qc")
SOURCE_WARNING="FLUXNET paired/downscaled ERA5, NOT independent ERA5-Land grid truth"

def require(p):
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing or symlink source: "+str(p))
    return p

def sha(p):
    d=hashlib.sha256()
    with require(p).open("rb") as f:
        for c in iter(lambda:f.read(1<<20),b""):d.update(c)
    return d.hexdigest()

def read_csv(p, fields):
    with require(p).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not set(fields).issubset(reader.fieldnames):
            raise ValueError("Unexpected columns: "+str(p))
        return list(reader)

def num(x):
    s=str(x if x is not None else "").strip()
    if s.upper() in MISSING:return None
    try:v=float(s)
    except ValueError:return None
    return v if math.isfinite(v) else None

def fmt(v):
    if v is None: return ""
    return "%.12g"%v

def sat(t):
    if t is None or not -80<=t<=65:return None
    return 6.112*math.exp(17.67*t/(t+243.5))

def next_key(s,steps=1):
    return (datetime.strptime(s,"%Y%m%d%H%M")+
            timedelta(minutes=30*steps)).strftime("%Y%m%d%H%M")

def physical_site(t,v):
    es=sat(t)
    return es is not None and v is not None and 0<=v<=es*1.00001

def direct_era(t_site, era):
    """Direct ERA VPD at EXACT native time; fail closed on physical mismatch."""
    if era is None:return None,"ERA_EXACT_TIME_MISSING"
    et,ev,ep=(num(era.get(x)) for x in ERAS)
    if (et is None or ev is None or ep is None or not -55<=et<=52 or
            not 65<=ep<=110 or ev<0):
        return None,"ERA_SOURCE_INVALID"
    es_e=sat(et)
    es_site=sat(t_site)
    if es_e is None or ev>es_e*1.00001:
        return None,"ERA_PAIR_NEGATIVE_VAPOUR_PRESSURE"
    if es_site is None or ev>es_site*1.00001:
        return None,"ERA_VPD_EXCEEDS_SATURATION_AT_RETAINED_TOWER_T"
    rh=100*(1-ev/es_site)
    if not -0.001<=rh<=100.001:return None,"RECONSTRUCTED_RH_OUTSIDE_0_100"
    return (ev,max(0.0,min(100.0,rh))),"DIRECT_ERA_VPD_VALID"

def verify_inputs():
    m=json.loads(require(S05/"report.json").read_text())
    r=json.loads(require(S06/"stage06_readonly_science_receipt.json").read_text())
    if (m.get("mode")!="BUILD_CANDIDATE_OVERLAY" or
        m.get("scientific_status")!="POST_QCV5_REVIEW_REQUIRED" or
        set(m.get("sites",{}))!=set(EXACT) or
        r.get("patch_records")!=5336 or r.get("hold_records")!=754 or
        r.get("boundary_review_rows")!=210):
        raise ValueError("Stage05/Stage06 provenance summary differs")
    if sha(S05/"candidate_patch.csv")!=m.get("candidate_patch_sha256"):
        raise ValueError("Stage05 patch checksum changed")
    if (sha(S05/"candidate_patch.csv")!=r["stage05_patch_sha256"] or
        sha(S05/"unresolved_hold.csv")!=r["stage05_holds_sha256"] or
        sha(S05/"report.json")!=r["stage05_report_sha256"] or
        sha(S06/"candidate_VPD_jumps_for_review.csv")!=
           r["output_sha256"]["candidate_VPD_jumps_for_review.csv"]):
        raise ValueError("Stage06 SHA receipt differs")
    for site,(total,npatch,nhold,nedge) in EXACT.items():
        it=m["sites"][site]
        if (it.get("rows"),it.get("patch_rows"),it.get("hold_rows"))!=(
             total,npatch,nhold):
            raise ValueError("Original source record counts changed: "+site)
        for role in ("native","era"):
            p=Path(it["paths"][role])
            if str(p).startswith(str(ROOT)):
                raise ValueError("Original source cannot reside in experiment output")
            if sha(p)!=it["source_provenance"][role]["sha256"]:
                raise ValueError("Original source SHA mismatch: "+str(p))
    return m

def sites_edges():
    rows=read_csv(S06/"candidate_VPD_jumps_for_review.csv",
                  ("site","left_time","right_time","candidate_jump_hPa","added_jump_hPa"))
    per=Counter(x["site"] for x in rows)
    if len(rows)!=210 or any(per[site]!=EXACT[site][3] for site in EXACT):
        raise ValueError("210 boundary inventory changed")
    endpoint=defaultdict(set)
    for item in rows:
        site,a,b=item["site"],item["left_time"],item["right_time"]
        if site not in EXACT or next_key(a)!=b:
            raise ValueError("Bad flagged edge")
        endpoint[site].update((a,b))
    return rows,endpoint

def first_pass(meta,patches,holds,targets):
    """Stream original once per site. Keep only needed native values and neighbours."""
    lookup={}
    for site in EXACT:
        need=set(targets[site])
        need.update(x["TIMESTAMP_START"] for x in patches if x["site"]==site)
        for hold in holds:
            if hold["site"]!=site or hold["reason"]!="SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID":
                continue
            t=hold["TIMESTAMP_START"]
            need.update((t,next_key(t,-1),next_key(t,1)))
        orig=Path(meta["sites"][site]["paths"]["native"])
        found={}
        n=0
        with orig.open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if not reader.fieldnames or not set(HEADS).issubset(reader.fieldnames):
                raise ValueError("Native missing fields: "+site)
            for row in reader:
                n+=1
                k=row["TIMESTAMP_START"]
                if k in need:
                    if k in found:raise ValueError("Duplicated original native timestamp "+k)
                    found[k]={x:row[x] for x in HEADS}
        if n!=EXACT[site][0] or not targets[site].issubset(found):
            raise ValueError("Source row count/missing boundaries: "+site)
        lookup[site]=found
        print("NATIVE READ",site,"rows",n,"selected_times",len(found),flush=True)
    return lookup

def era_pass(meta,targets):
    data={}
    for site in EXACT:
        found={}
        p=Path(meta["sites"][site]["paths"]["era"])
        with p.open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            req=("TIMESTAMP_START","TIMESTAMP_END",*ERAS)
            if not reader.fieldnames or not set(req).issubset(reader.fieldnames):
                raise ValueError("ERA source schema incorrect")
            for row in reader:
                key=row["TIMESTAMP_START"]
                if key in targets[site]:
                    if key in found:raise ValueError("Duplicate ERA target "+key)
                    if row["TIMESTAMP_END"]!=next_key(key):
                        raise ValueError("ERA clock end differs for "+key)
                    found[key]={x:row[x] for x in ERAS}
        data[site]=found
        print("EXACT-TIME ERA",site,"matched",len(found),"/",len(targets[site]),flush=True)
    return data

def neighbor_ta_decisions(holds,source,base_patch):
    result=Counter()
    for h in holds:
        if h["reason"]!="SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID":continue
        site,k=h["site"],h["TIMESTAMP_START"]
        current=source[site].get(k)
        before=source[site].get(next_key(k,-1))
        after=source[site].get(next_key(k,1))
        t=num(current["TA_F"]) if current else None
        ta=num(before["TA_F"]) if before else None
        tb=num(after["TA_F"]) if after else None
        if ((site,k,"TA_F") in base_patch):
            t=num(base_patch[site,k,"TA_F"]["candidate"])
        if all(x is not None and -55<=x<=52 for x in (t,ta,tb)) and (
            abs(ta-tb)<=6 and abs(t-ta)<=4 and abs(t-tb)<=4):
            result["KEEP_TOWER_TA_NEIGHBOUR_SUPPORTED"]+=1
        else:
            result["TEMPERATURE_STILL_AMBIGUOUS"]+=1
    return result

def make_patch_index(items):
    out={}
    for p in items:
        site,k,var=p["site"],p["TIMESTAMP_START"],p["variable"]
        if site not in EXACT or var not in ("TA_F","PA_F","VPD_F","RH"):
            raise ValueError("Unexpected Stage05 patch key")
        key=(site,k,var)
        if key in out:raise ValueError("Duplicate Stage05 patch")
        out[key]=dict(p)
    if len(out)!=5336:raise ValueError("Stage05 patch count changed")
    return out

def stage07_build(m,patches,holds,edges,endpoints,source,era):
    initial=make_patch_index(patches)
    candidate={k:dict(v) for k,v in initial.items()}
    retained_qc0=Counter()
    direct_success=Counter()
    unsafe=[]
    # Retain native US-Ton physically valid QC0 away from explicit jump endpoints.
    for (site,k,var),p in list(candidate.items()):
        if site!="US-Ton" or var not in ("RH","VPD_F") or k in endpoints[site]:
            continue
        native=source[site][k]
        if native["VPD_F_QC"].strip()=="0" and physical_site(
                num(native["TA_F"]),num(native["VPD_F"])):
            for x in ("VPD_F","RH"):
                candidate.pop((site,k,x),None)
            retained_qc0["US-Ton"]+=1 if var=="VPD_F" else 0
    # User explicitly requested the SAME-TIMESTAMP packaged ERA VPD for
    # BOTH endpoints of every Stage06 high-jump boundary.
    for site in EXACT:
        for k in sorted(endpoints[site]):
            native=source[site][k]
            tpatch=candidate.get((site,k,"TA_F"))
            t=num(tpatch["candidate"]) if tpatch else num(native["TA_F"])
            result,status=direct_era(t,era[site].get(k))
            if result is None:
                unsafe.append({"site":site,"TIMESTAMP_START":k,"reason":status,
                    "native_VPD_F":native["VPD_F"],
                    "original_VPD_QC":native["VPD_F_QC"],
                    "ERA_VPD_hPa":era[site].get(k,{}).get("VPD_ERA","")})
                # Do not retain a Stage05 humidity patch at the unsafe edge:
                # restores original value where physically defensible; else HOLD.
                for v in ("RH","VPD_F"):
                    candidate.pop((site,k,v),None)
                continue
            vpd,rh=result
            direct_success[site]+=1
            for var,value in (("VPD_F",vpd),("RH",rh)):
                key=(site,k,var)
                p=dict(candidate.get(key,{}))
                p.update({"site":site,"TIMESTAMP_START":k,
                    "TIMESTAMP_END":native["TIMESTAMP_END"],
                    "variable":var,"original":native[var],"candidate":fmt(value),
                    "method":"USER_APPROVED_DIRECT_PACKAGED_ERA5_VPD_AT_NATIVE_TIME",
                    "reason":"STAGE06_HIGH_JUMP_EDGE_BOTH_ENDPOINTS",
                    "original_qc":native.get(var+"_QC",""),
                    "science_status":"DERIVED_STAGE07_NOT_POSTV5_APPROVED",
                    "ERA_TA_C":era[site][k]["TA_ERA"],
                    "ERA_VPD_hPa":era[site][k]["VPD_ERA"],
                    "ERA_PA_kPa":era[site][k]["PA_ERA"],
                    "tower_TA_candidate_C":fmt(t)})
                candidate[key]=p
    # Keep explicit unresolved original Stage05 holds.
    decisions=neighbor_ta_decisions(holds,source,initial)
    if len(unsafe)>2*len(edges):
        raise ValueError("Unexpected number of direct ERA failures")
    return candidate,unsafe,retained_qc0,direct_success,decisions

def stream_full_csv(meta,candidate,out):
    patch_by_site=defaultdict(dict)
    for (site,k,var),p in candidate.items():
        patch_by_site[site].setdefault(k,{})[var]=p
    summary={}
    for site in EXACT:
        raw=Path(meta["sites"][site]["paths"]["native"])
        output=out/(site+"_Stage07_ERA_VPD_repaired_FLUXMET_HH.csv")
        n=0; changed=0; variable_change=0
        with raw.open(encoding="utf-8-sig",newline="") as inp,output.open(
                "x",encoding="utf-8",newline="") as dest:
            reader=csv.DictReader(inp)
            if not reader.fieldnames or not set(HEADS).issubset(reader.fieldnames):
                raise ValueError("Wrong FLUXMET source schema")
            writer=csv.DictWriter(dest,fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                n+=1
                here=patch_by_site[site].get(row["TIMESTAMP_START"])
                if here:
                    changed_here=False
                    for var,item in here.items():
                        original=num(row[var])
                        declared=num(item["original"])
                        if (original is None)!=(declared is None) or (
                            original is not None and
                            abs(original-declared)>1e-5*max(1,abs(original))):
                            raise ValueError("Source old value mismatch "+site+" "+var)
                        new=num(item["candidate"])
                        if new is None:raise ValueError("Candidate not numeric")
                        if original is None or abs(original-new)>1e-10:
                            row[var]=fmt(new)
                            variable_change+=1
                            changed_here=True
                    changed+=int(changed_here)
                writer.writerow(row)
        if n!=EXACT[site][0]:
            raise ValueError("Derived full CSV row count changed "+site)
        summary[site]={"source_rows":n,"changed_native_times":changed,
                      "changed_variable_cells":variable_change,
                      "full_derived_file":str(output),"sha256":sha(output),
                      "bytes":output.stat().st_size}
        print("DERIVED FILE",site,"rows",n,"modified_times",changed,
              "sha256",summary[site]["sha256"],flush=True)
    return summary

def write_table(p,rows,columns):
    with p.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def self_test():
    assert next_key("200105180530")=="200105180600"
    assert direct_era(15,{"TA_ERA":"15","VPD_ERA":"3","PA_ERA":"100"})[0][0]==3
    assert direct_era(0,{"TA_ERA":"20","VPD_ERA":"15","PA_ERA":"100"})[0] is None
    assert direct_era(10,{"TA_ERA":"-250","VPD_ERA":"2","PA_ERA":"100"})[0] is None
    assert physical_site(10,0) and not physical_site(1,25)
    print("STAGE07 SELF-TEST PASS: exact half-hours; native QC0; direct ERA/VPD/RH physics")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--apply",action="store_true")
    args=p.parse_args()
    self_test()
    if args.self_test:return
    meta=verify_inputs()
    edges,endpoints=sites_edges()
    patches=read_csv(S05/"candidate_patch.csv",FIELDS)
    holds=read_csv(S05/"unresolved_hold.csv",
                   ("site","TIMESTAMP_START","TIMESTAMP_END","reason"))
    if len(patches)!=5336 or len(holds)!=754:
        raise ValueError("Stage05 candidate/HOLD version mismatch")
    original=first_pass(meta,patches,holds,endpoints)
    era=era_pass(meta,endpoints)
    selected,unsafe,protected,success,temps=stage07_build(
        meta,patches,holds,edges,endpoints,original,era)
    destination=ROOT/"qcv5_stage07_applied"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    destination.mkdir(parents=True,exist_ok=False)
    (destination/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Derived scientific candidate only. 754 original Stage05 HOLDs not silently repaired.\n")
    allkeys=("site","TIMESTAMP_START","TIMESTAMP_END","variable","original",
             "candidate","method","reason","original_qc","science_status",
             "ERA_TA_C","ERA_VPD_hPa","ERA_PA_kPa","tower_TA_candidate_C")
    write_table(destination/"stage07_applied_changes.csv",
                [p for _,p in sorted(selected.items())],allkeys)
    write_table(destination/"stage07_unsafe_ERA_target_holds.csv",unsafe,
                ("site","TIMESTAMP_START","reason","native_VPD_F",
                 "original_VPD_QC","ERA_VPD_hPa"))
    # Retain immutable Stage05 HOLDs in the new release directory.
    write_table(destination/"stage07_inherited_754_holds.csv",holds,
                tuple(holds[0].keys()))
    outputs=stream_full_csv(meta,selected,destination)
    receipt={
        "user_selection":"Stage06 high-jump endpoints -> direct same-time packaged ERA5 VPD",
        "era_source_warning":SOURCE_WARNING,
        "source_stage05_report_sha256":sha(S05/"report.json"),
        "source_stage05_patch_sha256":sha(S05/"candidate_patch.csv"),
        "source_stage06_receipt_sha256":sha(S06/"stage06_readonly_science_receipt.json"),
        "source_stage06_edges_sha256":sha(S06/"candidate_VPD_jumps_for_review.csv"),
        "original_stage06_flagged_boundaries":len(edges),
        "requested_unique_boundary_endpoints":{x:len(endpoints[x]) for x in EXACT},
        "successfully_direct_era_replaced_endpoints":dict(success),
        "invalid_era_endpoints_held":len(unsafe),
        "protected_US_Ton_original_QC0_outside_boundaries":dict(protected),
        "tower_temperature_neighbour_case_classification":dict(temps),
        "inherited_stage05_holds":len(holds),
        "derived_full_length_files":outputs,
        "derived_not_postv5_approved":True,"DATM_ready":False,"spinup":False,
        "new_receipts_sha256":{
            name:sha(destination/name) for name in (
                "stage07_applied_changes.csv",
                "stage07_unsafe_ERA_target_holds.csv","stage07_inherited_754_holds.csv")},
        "created_utc":datetime.now(timezone.utc).isoformat(),
    }
    (destination/"stage07_sha_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE07 FINISHED new derived data:",destination,flush=True)
    print("STAGE07 210 edges; direct ERA endpoints",
          dict(success),"invalid pairs held",len(unsafe),
          "US-Ton QC0 protected outside edges",dict(protected))
    print("STAGE07 SOURCE FLUXMET/ERA + STAGE05/STAGE06 INTACT.")
    print("STAGE07 HOLD: 754 inherited +",len(unsafe),
          "direct-era invalid targets; no DATM or spinup.")

if __name__=="__main__":
    main()

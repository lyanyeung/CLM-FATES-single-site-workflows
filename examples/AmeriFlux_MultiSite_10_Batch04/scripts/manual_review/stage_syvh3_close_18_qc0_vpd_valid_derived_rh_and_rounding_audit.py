#!/usr/bin/env python3
"""Batch04 US-Syv SYVH3: reconcile last 18 inherited ERA-humidity source flags.

Operator source-verified: 433 original non-T science holds, 415 repaired by
independent ERA5-Land humidity, last 18: ORIGINAL T QC0 and VPD QC0, VPD
strictly physically valid but derived RH misses current T/VPD closure by
0.787..1.497 percentage points. Keep all original TA, TA_QC, VPD, VPD_QC,
pressure, time, all 297 user-approved T changes and all 415 new humidity
repairs. Update DERIVED RH ONLY at precisely 18 old source-HOLD native HH.
NEVER edit original tower FLUXMET files or archival source-HOLD ledger.

Operator-run SYVH2 FULL FILE scan also found exactly one isolated source
VPD rounding difference: 2008-03-09 13:00, T=-6.234C, VPD=3.842 hPa,
es(T)=3.8419768 hPa, positive difference just 0.0000232 hPa. This is
within 0.0005 hPa input precision of source VPD saved to 3 decimals.
Retain native VPD without clipping/replacing; record a precision exception
with exact source evidence and FAIL if any larger global oversaturation.

--self-test : synthetic scientific numeric tests; NO SOURCES/WRITES
--assess    : full 438288 HH source and provenance read-only; NO WRITES
--apply     : new 438288 HH US-Syv candidate; only 18 derived RH cells may
              differ. Recheck full original and all nine other site selection
              SHA/pointers, independent full-file audit and source ledger.
No Post-v5/DATM/CIME/Slurm/CLM model jobs or production release.
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from itertools import zip_longest
from uuid import uuid4

E=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
PARENT=E/"manual_US_Syv_stage_SYVH1_433_humidity_era5land_candidate_not_approved/candidate_20261026T033139Z_a8699ac8"
PARENT_SHA="265d92fc7d3cc8c3d3dff6b93067d9fc380969131ab044c08bd192c1ceb9b1cc"
S05=E/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=E/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
PRIOR106=E/"manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved/candidate_20261026T010755Z_591ef88f"
PRIOR191=E/"manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_20261026T024759Z_6e1e07ad"
N=438288
ROUNDING_KEY="200803091300"
ROUNDING_TEMP=-6.234
ROUNDING_VPD=3.842
ROUNDING_VPD_MAX_EXCESS_HPA=0.0005
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Missing/symlink verified source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def j(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def table(p,fields,delim=","):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter=delim)
        ck(rd.fieldnames is not None and set(fields).issubset(rd.fieldnames),
           "Required immutable input schema missing "+str(p))
        return rd.fieldnames,list(rd)
def val(x):
    z=str(x if x is not None else "").strip()
    if z.upper() in MISSING:return None
    try:v=float(z)
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) else None
def sat(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -60<t<60 else None
def strict_physical(t,v):
    es=sat(t)
    return es is not None and v is not None and 0<=v<=es
def derived_rh(t,v):
    ck(strict_physical(t,v),"Can't derive source RH from physically invalid original T/VPD")
    return 100*(1-v/sat(t))
def fmt(x):return f"{x:.12g}"
def historical():
    m=j(S05/"report.json")
    r=j(S07/"stage07_sha_receipt.json")
    ck(m["sites"]["US-Syv"]["rows"]==N and
       m["sites"]["US-Syv"]["hold_rows"]==606 and
       sha(S05/"report.json")==r["source_stage05_report_sha256"],
       "Original source-HOLD provenance has changed")
    _,olds=table(S05/"unresolved_hold.csv",("site","TIMESTAMP_START","reason"))
    _,edges=table(S07/"stage07_unsafe_ERA_target_holds.csv",
                   ("site","TIMESTAMP_START","reason"))
    holds={x["TIMESTAMP_START"]:x["reason"] for x in olds if x["site"]=="US-Syv"}
    edge={x["TIMESTAMP_START"]:x["reason"] for x in edges if x["site"]=="US-Syv"}
    ck(len(olds)==754 and len(holds)==606 and len(edge)==10 and
       not set(holds)&set(edge),"Source original 606+10 receipt changed")
    prior=set()
    for path,expected in (
      (PRIOR106/"SIX_OPERATOR_106_HH_ERA_T_FULL_PROVENANCE.tsv",106),
      (PRIOR191/"NEW_SOURCE_TA_ERA_REPAIR_LEDGER.tsv",191)):
        _,data=table(path,("TIMESTAMP_START",),"\t")
        keys={z["TIMESTAMP_START"] for z in data}
        ck(len(data)==expected and len(keys)==expected and
           not prior.intersection(keys),"Old operator T approval/source ledger changed")
        prior.update(keys)
    ck(len(prior)==297,"User-approved T changed HH not exact 297")
    remaining=(set(holds)|set(edge))-prior
    ck(len(remaining)==433,"Prior original humidity source HOLD count not 433")
    return holds,edge,remaining,prior
def source():
    rec=j(PARENT/"SYVH1_SCIENCE_RECEIPT.json")
    parent=Path(rec["candidate_path"])
    ck(parent.parent==PARENT and
       sha(parent)==rec["new_candidate_sha256"]==PARENT_SHA and
       rec["parent_full_sha256"]==
       "508295cfb64d5cfd116e4e6f91acc304b15ee16d3c6fab4673e07680137592ad" and
       rec["native_rows"]==N and
       rec["actually_modified_source_HH"]==415 and
       rec["legacy_HOLD_remaining_not_numerically_repaired"]==18 and
       rec["production_approval"] is False,
       "Operator finished full Syv SYVH1 parent SHA/science receipt changed")
    fields,mf=table(PARENT/"RESEARCH_TEN_SITE_MANIFEST.tsv",
                    ("site","source_path","source_SHA256","latest_stage"),"\t")
    ck(len(mf)==10 and len({x["site"] for x in mf})==10,
       "Parent manifest not exact ten unique sites")
    selected=[x for x in mf if x["site"]=="US-Syv"]
    ck(len(selected)==1 and
       Path(selected[0]["source_path"])==parent and
       selected[0]["source_SHA256"]==PARENT_SHA,
       "Parent research manifest Syv selection doesn't match SHA")
    _,repair=table(PARENT/"SYVH1_HUMIDITY_SOURCE_PROVENANCE.tsv",
                   ("TIMESTAMP_START",),"\t")
    solved={x["TIMESTAMP_START"] for x in repair}
    ck(len(repair)==415 and len(solved)==415,"Independent ERA5Land full repairs count changed")
    holds,edge,all433,tapproved=historical()
    left=all433-solved
    ck(len(left)==18 and
       left.issubset(set(holds)) and
       not left.intersection(tapproved),
       "Expected 18 unmodified original VPD QC0 source HOLDs only")
    _,prior_manifest=table(PRIOR191/"RESEARCH_TEN_SITE_MANIFEST.tsv",
                   ("site","source_path","source_SHA256","latest_stage"),"\t")
    ck([x for x in mf if x["site"]!="US-Syv"]==
       [x for x in prior_manifest if x["site"]!="US-Syv"],
       "One of nine other selected full research sites changed")
    return parent,fields,mf,holds,edge,left,solved
def scan(parent,left,holds):
    count=0;got={};nativeqc=Counter()
    bad_count=0;small_quantisation=[];major=[]
    with regular(parent).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        ck(rd.fieldnames is not None and
           {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH","PA_F"}.issubset(rd.fieldnames),
           "Final source site input lacks TA/VPD/RH/pressure columns")
        for row in rd:
            count+=1;k=row["TIMESTAMP_START"]
            t=val(row["TA_F"]);v=val(row["VPD_F"])
            nativeqc[row["TA_F_QC"]]+=1
            if k in left:
                ck(k not in got,"Duplicate source hold native timestamp "+k)
                got[k]=dict(row)
            es=sat(t)
            if es is None or v is None or v<0 or v>es:
                bad_count+=1
                if (es is not None and v is not None and
                    v>es and v-es<=ROUNDING_VPD_MAX_EXCESS_HPA):
                    small_quantisation.append((k,t,v,es,v-es,row["TA_F_QC"],row["VPD_F_QC"]))
                elif len(major)<12:
                    major.append((k,t,v,es,row["TA_F_QC"],row["VPD_F_QC"]))
    ck(count==N and set(left)==set(got),
       "Full 438288 source and 18 remaining native-HH completeness failed")
    ck(bad_count==1 and len(small_quantisation)==1 and not major,
       "Unexpected full site uncorrected VPD physics failure; NO WRITES "+str(major))
    k,t,v,es,excess,taqc,vqc=small_quantisation[0]
    ck(k==ROUNDING_KEY and abs(t-ROUNDING_TEMP)<1e-9 and
       abs(v-ROUNDING_VPD)<1e-9 and excess>0,
       "Global source rounding exception changed, no silent repair")
    ck(abs(excess)<0.0005 and t<0,"Rounding exception larger than native VPD input resolution")
    changes={};baseline=Counter()
    for k in sorted(left):
        row=got[k];t=val(row["TA_F"]);v=val(row["VPD_F"]);old_rh=val(row["RH"])
        ck(row["TA_F_QC"]=="0" and row["VPD_F_QC"]=="0",
           "Last 18 native T and VPD must both be QC0 observed source "+k)
        new_rh=derived_rh(t,v)
        ck(old_rh is not None and 0<=old_rh<=100 and
           0<=new_rh<=100,
           "Original QC0 observed humidity missing / invalid "+k)
        diff=abs(new_rh-old_rh)
        ck(.5<=diff<=2.0,
           "Unexpected source RH closure discrepancy or RH definition changed "+k+" "+str(diff))
        baseline[holds[k]]+=1
        changes[k]={"site":"US-Syv","TIMESTAMP_START":k,
           "source_legacy_HOLD_reason":holds[k],
           "original_TA_F_C":row["TA_F"],"original_TA_F_QC":row["TA_F_QC"],
           "original_VPD_F_hPa":row["VPD_F"],"original_VPD_F_QC":row["VPD_F_QC"],
           "old_derived_RH_pct":row["RH"],"new_derived_RH_pct":new_rh,
           "difference_new_minus_old_RH_percentage_points":new_rh-old_rh,
           "source_correction":"DERIVED_RH_FROM_PHYS_VALID_NATIVE_QC0_T_AND_NATIVE_QC0_VPD",
           "temperature_preserved":True,"vpd_preserved":True,
           "original_ERA_pair_HOLD_immutable":True,"production_approval":False}
        print("ORIGINAL_QC0_CLOSE",k,"TA",row["TA_F"],"VPD",row["VPD_F"],
              "OLD_RH",row["RH"],"NEW_DERIVED_RH",fmt(new_rh),
              "DELTA_RH",fmt(new_rh-old_rh),"OLD_REASON",holds[k])
    ck(len(changes)==18 and
       baseline["ERA_PAIR_HUMIDITY_INVALID"]==17 and
       baseline["ERA_RH_OUTSIDE_QCV5_USABLE_RANGE"]==1,
       "Last 18 original reason breakdown changed")
    print("SYVH3 PREFLIGHT PASS 18 original source QC0 VPD & TA retained; RH-only reconciliation")
    print("LAST_18_OLD_SOURCE_REASONS",dict(baseline))
    print("FULL_SITE_STRICT_PHYSICS_EXCEPTIONS",bad_count,
          "ROUNDING_ONLY",small_quantisation,
          "ALL_OTHER_HH_PHYSICALLY_VALID",count-bad_count)
    return changes,small_quantisation[0],nativeqc
def materialize(parent,target,changes):
    n=0;seen=set()
    with regular(parent).open(encoding="utf-8-sig",newline="") as f, \
         target.open("x",encoding="utf-8",newline="") as out:
        r=csv.DictReader(f)
        ck(r.fieldnames is not None and {"TIMESTAMP_START","RH"}.issubset(r.fieldnames),
           "Final source schema unexpected")
        w=csv.DictWriter(out,fieldnames=r.fieldnames);w.writeheader()
        for row in r:
            n+=1;k=row["TIMESTAMP_START"]
            if k in changes:
                ck(k not in seen,"Repeated source key "+k)
                seen.add(k);row["RH"]=fmt(changes[k]["new_derived_RH_pct"])
            w.writerow(row)
    ck(n==N and seen==set(changes),"SYVH3 incomplete/full source HH unexpected")
    return sha(target)
def independent_audit(old,new,changes,expected_quantized):
    n=0;seen=set();changed_cells=0;strict_failure=[]
    with regular(old).open(encoding="utf-8-sig",newline="") as f, \
         regular(new).open(encoding="utf-8-sig",newline="") as g:
        x=csv.DictReader(f);y=csv.DictReader(g)
        ck(x.fieldnames==y.fieldnames,"Changed full source schema")
        for a,b in zip_longest(x,y):
            ck(a is not None and b is not None and
               a["TIMESTAMP_START"]==b["TIMESTAMP_START"],
               "Altered native timestamp or order")
            n+=1;k=a["TIMESTAMP_START"]
            diffs={col for col in x.fieldnames if a[col]!=b[col]}
            if k in changes:
                ck(k not in seen and diffs=={"RH"} and
                   a["TA_F"]==b["TA_F"] and
                   a["TA_F_QC"]==b["TA_F_QC"] and
                   a["VPD_F"]==b["VPD_F"] and
                   a["VPD_F_QC"]==b["VPD_F_QC"] and
                   a["PA_F"]==b["PA_F"],"Non-RH change or unchanged source RH "+k)
                seen.add(k)
                t=val(b["TA_F"]);v=val(b["VPD_F"])
                ck(abs(val(b["RH"])-derived_rh(t,v))<=1e-8,
                   "Native QC0 humidity recalculated closure failed "+k)
                changed_cells+=1
            else:ck(not diffs,"Non-user/algorithm RH target modified "+k)
            t=val(b["TA_F"]);v=val(b["VPD_F"]);es=sat(t)
            if es is None or v is None or v<0 or v>es:
                excess=None if es is None or v is None else v-es
                strict_failure.append((k,t,v,es,excess))
    ck(n==N and seen==set(changes) and changed_cells==18 and
       len(strict_failure)==1 and strict_failure[0][0]==ROUNDING_KEY and
       0<strict_failure[0][4]<=ROUNDING_VPD_MAX_EXCESS_HPA,
       "Full final science source audit failed, unexpected physics points")
    print("SYVH3 INDEPENDENT WHOLE SITE 438288 ROW DIFF AUDIT PASS",
          "exact_RH_only_reconciliations",changed_cells,
          "allowed_native_VPD_three_decimal_rounding",strict_failure)
    return changed_cells
def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--assess",action="store_true")
    modes.add_argument("--apply",action="store_true")
    args=p.parse_args()
    ck(abs(sat(-6.234)-3.841976803313088)<1e-10 and
       abs(derived_rh(-27.817,.595)-4.926341871648299)<1e-10 and
       not strict_physical(-6.234,3.842),
       "Synthetic water vapour source closure/rounding self-test failed")
    print("SYVH3 SELF-TEST PASS RH closure from native QC0 source VPD, 0.0005 hPa rounding, no writes")
    if args.self_test:return
    parent,fields,mf,holds,edges,left,solved=source()
    changes,quant,nativeqc=scan(parent,left,holds)
    if args.assess:
        print("SYVH3 ASSESS COMPLETE READ-ONLY; no candidate/science/model files written")
        return
    out=E/"manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved"/(
       "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_NOT_POSTV5_DATM_CIME_SLURM_SPINUP").write_text(
       "Research only; QC0 T and VPD preserved, 18 derived RH adjustments, one native VPD rounding provenance exception.\n")
    new=out/"US-Syv_SYVH3_18_derived_RH_closure_438288_HH.csv"
    hashnew=materialize(parent,new,changes)
    cells=independent_audit(parent,new,changes,quant)
    updated=[]
    for x in mf:
        r=dict(x)
        if r["site"]=="US-Syv":
            r["source_path"]=str(new)
            r["source_SHA256"]=hashnew
            r["latest_stage"]="SYVH3_18_QC0_VPD_PRESERVED_DERIVED_RH_CLOSURE_RESEARCH_ONLY"
        updated.append(r)
    ck([x for x in mf if x["site"]!="US-Syv"]==
       [x for x in updated if x["site"]!="US-Syv"],
       "Nine other research sites changed in selection")
    mfpath=out/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    with mfpath.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader();w.writerows(updated)
    ledger=out/"SYVH3_QC0_DERIVED_RH_SOURCE_CLOSURE_18.tsv"
    with ledger.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(next(iter(changes.values()))),delimiter="\t")
        w.writeheader();w.writerows(changes[k] for k in sorted(changes))
    rounding_k,round_t,round_v,round_es,round_ex,round_tqc,round_vqc=quant
    receipt={
      "site":"US-Syv","operator_science_policy":"KEEP QC0 VPD AND T; RECOMPUTE DERIVED RH AT 18 HISTORICAL GRID-HUMIDITY FLAGS",
      "source_original_HOLD_archives":"IMMUTABLE",
      "numeric_original_HOLD_left_unreconciled_in_research_candidate":0,
      "source_606_plus_10_prior_holds_not_removed":True,
      "independent_ERA5LAND_415_prior_repaired_humidity_HH_preserved":True,
      "manual_106_plus_191_temperature_HH_preserved":True,
      "parent_full_SHA256":PARENT_SHA,"new_full_SHA256":hashnew,
      "new_full_candidate_path":str(new),"full_site_rows":N,
      "QC0_T_and_VPD_preserved_HH":18,"derived_RH_only_repaired_HH":18,
      "precision_only_boundary_exception":{
           "timestamp":rounding_k,"temperature_C":round_t,
           "source_native_TA_QC":round_tqc,"native_VPD_QC":round_vqc,
           "VPD_hPa":round_v,"water_saturation_hPa":round_es,
           "difference_hPa":round_ex,
           "input_three_decimal_half_ulp_hPa":ROUNDING_VPD_MAX_EXCESS_HPA,
           "decision":"RETAIN_NATIVE_VPD_AS_ROUNDING_COMPATIBLE_NOT_A_PHYSICAL_INVALID_DATA_REPLACEMENT"},
      "strict_global_invalid_HH":1,
      "quantisation_aware_global_invalid_HH":0,
      "source_production_approval":False,"postv5_approved":False,
      "DATM_ready":False,"spinup":False,
      "other_nine_manifest_selections_unchanged":True,
      "new_changed_RH_field_cells":cells}
    (out/"SYVH3_RESEARCH_SCIENCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SYVH3 18 ORIGINAL QC0 VPD RETAINED DERIVED RH CLOSED SCIENCE CANDIDATE PASS",out)
    print("SYVH3 NEW FULL CSV SHA256",hashnew)
    print("SYVH3 NEW TEN SITE RESEARCH INPUT MANIFEST",mfpath)
    print("SYVH3 PHYSICS ROUNDING 1 NATIVE THREE-DECIMAL EXCEPTION DOCUMENTED; no source data clipped")
    print("NO ORIGINAL, ERA5LAND RECEIPTS, PREVIOUS 297 TEMPERATURE, 415 HUMIDITY, OTHER NINE SITES, POSTV5 OR MODEL WRITES")
if __name__=="__main__":main()

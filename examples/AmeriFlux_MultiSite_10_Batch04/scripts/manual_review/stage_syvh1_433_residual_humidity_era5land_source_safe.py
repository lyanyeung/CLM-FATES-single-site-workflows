#!/usr/bin/env python3
"""US-Syv Stage SYVH1: leftover 433 original source humidity HOLDs, 191-T trial parent.

ONLY new research candidate. Keep all site T, original QC, previous six 106 HH
and new 191 HH T repairs, plus other nine site selection source paths UNCHANGED.
Residual original 606+10 science source HOLDs minus approved T replacements
must be EXACTLY 433 native HH; do not infer 433 physical VPD errors.

Independent ERA5-Land T2m/d2m/surface pressure verified with ORIGINAL BIF
local-standard UTC offset, CDS response SHA + full NetCDF hourly coverage.
Only replace VPD/RH at physically invalid source humidity if ERA5-Land RH
is valid, tower T & pressure physically plausible. In the absence of a
downloaded independent source, a physically valid original paired processed
FLUXNET ERA relative humidity may be projected to retained TA, provided
strictly validated 0<=VPD_ERA<=es(TA_ERA); it is labelled a DIFFERENT
lower-priority evidence class, not independent ERA5-Land. Otherwise HOLD.
At currently valid native T/VPD, retain VPD; compute derived RH only if
missing/invalid; source legacy science HOLD remains reported.
No direct copying of physically invalid VPD_ERA, no saturation clipping,
no overwrite of source, previous candidates, other nine sites or models.

--self-test       synthetic humidity and native-time tests ONLY, no writes
--check           read-only 433-census, physical categories and grid inventory
--apply-existing  make new research candidate using only SHARED VALID evidence
--run             retrieve at most --max-downloads missing CDS site-years,
                  then apply validated evidence into NEW full site version
"""
import argparse,csv,hashlib,importlib.util,json,math
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
from itertools import zip_longest
from uuid import uuid4

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=EXP/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
PREV=EXP/"manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved/candidate_20261026T010755Z_591ef88f"
PARENT=EXP/"manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_20261026T024759Z_6e1e07ad"
PARENT_SHA="508295cfb64d5cfd116e4e6f91acc304b15ee16d3c6fab4673e07680137592ad"
PARENT_CSV=PARENT/"US-Syv_all_remaining_QC0_QC1_ERA_T_full_FLUXMET_HH.csv"
MANIFEST=PARENT/"RESEARCH_TEN_SITE_MANIFEST.tsv"
HELPER=Path(__file__).resolve().with_name("10_era5land_independent_humidity_fill.py")
SITE="US-Syv";N=438288
OLD_ERA_TEMP_SEEDS=183
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
REQUIRED_CSV=("TIMESTAMP_START","TA_F","TA_F_QC","PA_F","VPD_F","VPD_F_QC","RH")
WHITELIST={"VPD_F","VPD_F_QC","RH"}

def ck(v,msg):
    if not v:raise ValueError(msg)
def file(p):
    ck(p.is_file() and not p.is_symlink(),"Missing or symlinked source "+str(p))
    return p
def digest(p):
    h=hashlib.sha256()
    with file(p).open("rb") as r:
        for c in iter(lambda:r.read(4<<20),b""):h.update(c)
    return h.hexdigest()
def records(p,cols,delimiter=","):
    with file(p).open(encoding="utf-8-sig",newline="") as r:
        rd=csv.DictReader(r,delimiter=delimiter)
        ck(rd.fieldnames and set(cols).issubset(rd.fieldnames),
           "Unverified input schema "+str(p))
        return rd.fieldnames,list(rd)
def jsonread(p):return json.loads(file(p).read_text(encoding="utf-8"))
def val(x):
    z=str(x if x is not None else "").strip()
    if z.upper() in MISSING:return None
    try:v=float(z)
    except ValueError:return None
    return v if math.isfinite(v) else None
def saturation(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -60<=t<=55 else None
def phys(v,t):
    es=saturation(t)
    return es is not None and v is not None and 0<=v<=es+1e-8
def fmt(v):return f"{v:.12g}"
def ext_module():
    f=file(HELPER)
    s=importlib.util.spec_from_file_location("syvh1_stage10_helper",str(f))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    for fn in ("bif","response_receipt","download_one","grid_read","local_to_utc","rh_hour"):
        ck(callable(getattr(m,fn,None)),"Required external helper missing "+fn)
    return m
def sources():
    stage5=jsonread(S05/"report.json")
    stage7=jsonread(S07/"stage07_sha_receipt.json")
    ck(stage5.get("mode")=="BUILD_CANDIDATE_OVERLAY" and
       stage5["sites"][SITE]["hold_rows"]==606 and
       stage5["sites"][SITE]["rows"]==N and
       stage7.get("inherited_stage05_holds")==754 and
       stage7.get("invalid_era_endpoints_held")==12,
       "Immutable original Stage05 / Stage07 census shifted")
    ck(digest(S05/"report.json")==stage7["source_stage05_report_sha256"],
       "Immutable Stage05 report changed")
    ck(digest(PARENT_CSV)==PARENT_SHA and
       jsonread(PARENT/"SCIENCE_RESEARCH_RECEIPT.json")["complete_derived_SHA256"]==PARENT_SHA,
       "Already operator-VERIFIED 191 new T full parent SHA differs")
    _,holds=records(S05/"unresolved_hold.csv",("site","TIMESTAMP_START","reason"))
    _,skips=records(S07/"stage07_unsafe_ERA_target_holds.csv",
                    ("site","TIMESTAMP_START","reason"))
    h={x["TIMESTAMP_START"]:x["reason"] for x in holds if x["site"]==SITE}
    e={x["TIMESTAMP_START"]:x["reason"] for x in skips if x["site"]==SITE}
    ck(len(holds)==754 and len(h)==606 and len(e)==10 and not set(h)&set(e),
       "Original residual 606+10 HOLD source changed")
    # 183 original T source-HOLD timestamps have been user-adjudicated.
    previous=set()
    r=jsonread(PREV/"SCIENCE_RESEARCH_RECEIPT.json")
    ck(r["total_operator_selected_native_HH"]==106 and
       r["new_US_Syv_full_SHA256"]==
       "8ac03873ad573e2885569f371ce6a413d4f3f230d7f473ece6c7e20bb7bf1b73",
       "Old six temperature alternative provenance changed")
    _,first=records(PREV/"SIX_OPERATOR_106_HH_ERA_T_FULL_PROVENANCE.tsv",
                    ("TIMESTAMP_START",),"\t")
    previous.update(x["TIMESTAMP_START"] for x in first)
    _,second=records(PARENT/"NEW_SOURCE_TA_ERA_REPAIR_LEDGER.tsv",
                     ("TIMESTAMP_START",),"\t")
    ck(len(first)==106 and len(second)==191,"191/106 user repair ledger count changed")
    previous.update(x["TIMESTAMP_START"] for x in second)
    ck(len(previous)==297,"Prior user 106 and new 191 T half-hours must be disjoint")
    old=set(h)|set(e)
    left=old-previous
    tsource={k for k,reason in h.items() if
             reason=="SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID"}
    ck(len(tsource)==OLD_ERA_TEMP_SEEDS and not tsource-left,
       "All 183 T-vs-ERA science source HOLDs must be explicitly adjudicated")
    ck(len(left)==433,"Exactly 433 remaining historical non-T source science HOLD HH")
    m=stage5["sites"][SITE]
    raw=Path(m["paths"]["native"]);era=Path(m["paths"]["era"])
    ck(digest(raw)==m["source_provenance"]["native"]["sha256"] and
       digest(era)==m["source_provenance"]["era"]["sha256"],
       "Original tower or paired grid full source SHA mismatch")
    fields,manifest=records(MANIFEST,
                            ("site","source_path","source_SHA256","latest_stage"),"\t")
    ck(len(manifest)==10 and len(set(x["site"] for x in manifest))==10,
       "Research final parent manifest must contain 10 unique sites")
    selected=[x for x in manifest if x["site"]==SITE]
    ck(len(selected)==1 and Path(selected[0]["source_path"])==PARENT_CSV and
       selected[0]["source_SHA256"]==PARENT_SHA,
       "Parent manifest does not select operator-audited full Syv parent")
    print("SOURCE CONTRACT PASS parent 191HH+106HH full SHA; 606+10 original source; 433 residual exact native keys")
    return stage5,fields,manifest,raw,era,h,e,left
def selected_rows(path,keys,fields,expected=None):
    got={};n=0
    with file(path).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        ck(rd.fieldnames is not None and set(fields).issubset(rd.fieldnames),
           "Site source schema changed "+str(path))
        for r in rd:
            n+=1;k=r["TIMESTAMP_START"]
            if k in keys:
                ck(k not in got,"Duplicate original native HH "+k)
                got[k]={v:r[v] for v in fields}
    if expected is not None:ck(n==expected,"Source full-length original native count changed")
    ck(keys.issubset(got),"Unmatched exact original time keys "+str(path))
    return got
def plan():
    meta,fields,manifest,raw,era,h,e,left=sources()
    native=selected_rows(PARENT_CSV,set(left),REQUIRED_CSV,N)
    paired=selected_rows(era,set(left),("TIMESTAMP_START","TA_ERA","VPD_ERA"))
    classes=Counter();byyear=Counter();physstatus=Counter()
    for k in left:
        src=h.get(k,"STAGE07_UNSAFE_PAIR_ERA_EDGE")
        classes[src]+=1
        byyear[int(k[:4])]+=1
        p=native[k];t=val(p["TA_F"]);v=val(p["VPD_F"])
        if t is None:physstatus["INVALID_T"]+=1
        elif phys(v,t):physstatus["PHYS_VALID_BUT_OLD_SOURCE_HOLD"]+=1
        else:physstatus["VPD_INVALID_AT_RETAINED_T"]+=1
    ck(sum(classes.values())==433,"433 source historical category tally incomplete")
    ex=ext_module()
    point=ex.bif(meta,SITE)
    status={}
    for year in sorted(byyear):
        status[year]=ex.response_receipt(SITE,year)
    print("US-SYV LEFTOVER_HUMIDITY_HOLD_COUNT",len(left),
          "TOWER_VPD_SOURCE_PHYSICS",dict(physstatus),
          "HISTORICAL_HOLD_REASONS",dict(classes))
    print("ERA5-LAND INDEPENDENT SOURCE AVAILABILITY (CDS verified by site, year and SHA)")
    for y,n in sorted(byyear.items(),key=lambda p:(-p[1],p[0])):
        print("SITE_YEAR",SITE,y,"HH",n,
              "GRID",("PRESENT_RECEIPT_SHA_VERIFIED" if status[y] else "MISSING"))
    return ex,point,status,byyear,fields,manifest,left,h,e,native,paired
def science(ex,point,status,left,h,e,native,paired):
    cache={}
    for year,p in status.items():
        if p:
            cache[year]=ex.grid_read(p,year,point)
            print("INDEPENDENT GRID FULL YEAR SOURCE VERIFIED",SITE,year)
    changes={};blocked=Counter();used=Counter();valid=0;priority=[]
    for k in sorted(left):
        a=native[k];t=val(a["TA_F"]);v=val(a["VPD_F"]);pa=val(a["PA_F"])
        reason=h.get(k,e.get(k,"UNRECOGNISED_HISTORICAL_HOLD"))
        if t is None or not -55<=t<=52 or pa is None or not 65<=pa<=110:
            blocked["INVALID_SITE_T_OR_PA"]+=1
            priority.append((k,reason,"SITE_T_OR_PA_INVALID"))
            continue
        if phys(v,t):
            valid+=1
            # This is a physical source validity test, NOT a science source HOLD approval.
            blocked["PHYS_VALID_OLD_HOLD_NEEDS_SCIENCE_REASON_CLOSURE"]+=1
            continue
        es=saturation(t); newrh=None;source=None;sourceproof=""
        grid=cache.get(int(k[:4]))
        if grid is not None:
            utc=ex.local_to_utc(k,point["offset_hours"])
            gridrh=ex.rh_hour(grid,utc)
            if gridrh is not None and 0<=gridrh<=100:
                newrh=gridrh;source="INDEPENDENT_ERA5LAND_D2M_T2M_SP"
                sourceproof=sha_str=status[int(k[:4])]
                # URI/path SHA ledger below; do not cache external arrays in output.
        if newrh is None:
            gridt=val(paired[k]["TA_ERA"]);gridv=val(paired[k]["VPD_ERA"])
            if phys(gridv,gridt):
                newrh=100*(1-gridv/saturation(gridt))
                source="PHYSICALLY_CHECKED_FLUXNET_PACKAGED_ERA_RH_PROJECTED_ON_TOWER_T"
                sourceproof="PACKAGED_ERA_SOURCE_SHA_PINNED"
        if newrh is None or not 0<=newrh<=100:
            blocked["NO_VALID_INDEPENDENT_OR_PACKAGED_ERA_HUMIDITY_SOURCE"]+=1
            priority.append((k,reason,"NO_VALID_ERA_HUMIDITY"))
            continue
        newv=es*(1-newrh/100)
        if not phys(newv,t):
            blocked["NEW_VPD_FAILED_PHYSICAL_CLOSURE"]+=1
            priority.append((k,reason,"NEW_VPD_INVALID"))
            continue
        used[source]+=1
        changes[k]={"site":SITE,"TIMESTAMP_START":k,
            "legacy_source_HOLD_reason":reason,
            "source_TA_F_C":a["TA_F"],"source_TA_F_QC":a["TA_F_QC"],
            "old_VPD_hPa":a["VPD_F"],"old_VPD_QC":a["VPD_F_QC"],
            "replacement_VPD_hPa":newv,"replacement_VPD_QC":"2",
            "replacement_RH_pct":newrh,"source_humidity_class":source,
            "external_source_proof":str(sourceproof),
            "original_TA_UNCHANGED":True,
            "research_only":"YES"}
    print("HUMIDITY REPAIR PLAN physical_invalid_target_corrections",len(changes),
          "source_methods",dict(used),
          "blocked_reason",dict(blocked))
    print("HUMIDITY UNRESOLVED FIRST_30",
          [(x[0],x[1],x[2]) for x in priority[:30]])
    return changes,blocked,used,priority
def write_new(parent,new,patches):
    n=0;matched=set()
    with file(parent).open(encoding="utf-8-sig",newline="") as a, \
         new.open("x",encoding="utf-8",newline="") as b:
        x=csv.DictReader(a)
        ck(x.fieldnames and set(REQUIRED_CSV).issubset(x.fieldnames),
           "Parent Syv research schema changed")
        w=csv.DictWriter(b,fieldnames=x.fieldnames);w.writeheader()
        for row in x:
            n+=1;k=row["TIMESTAMP_START"]
            if k in patches:
                ck(k not in matched,"Duplicate native Syv target "+k)
                matched.add(k)
                p=patches[k]
                row["VPD_F"]=fmt(p["replacement_VPD_hPa"])
                row["VPD_F_QC"]="2"
                row["RH"]=fmt(p["replacement_RH_pct"])
            w.writerow(row)
    ck(n==N and matched==set(patches),
       "New humidity only full-length Syv candidate incomplete")
    return digest(new)
def independent_audit(parent,output,patches):
    n=0;seen=set();changed=0
    with file(parent).open(encoding="utf-8-sig",newline="") as f, \
         file(output).open(encoding="utf-8-sig",newline="") as g:
        r=csv.DictReader(f);s=csv.DictReader(g)
        ck(r.fieldnames==s.fieldnames,"Humidity-only derived CSV schema changed")
        for x,y in zip_longest(r,s):
            ck(x is not None and y is not None and
               x["TIMESTAMP_START"]==y["TIMESTAMP_START"],
               "Humidity-only candidate row order changed")
            n+=1;k=x["TIMESTAMP_START"]
            diffs={z for z in r.fieldnames if x[z]!=y[z]}
            if k not in patches:
                ck(not diffs,"Outside source-limited humidity approval "+k)
                continue
            ck(k not in seen and diffs.issubset(WHITELIST),
               "Unexpected humidity columns or duplicate source target "+k)
            seen.add(k);p=patches[k]
            ck(all(x[z]==y[z] for z in ("TA_F","TA_F_QC","PA_F")),
               "Changed retained tower temperature/pressure "+k)
            ck(phys(val(y["VPD_F"]),val(y["TA_F"])) and
               abs(val(y["VPD_F"])-p["replacement_VPD_hPa"])<1e-8 and
               abs(val(y["RH"])-p["replacement_RH_pct"])<1e-8 and
               y["VPD_F_QC"]=="2","Candidate humidity physics/source mismatch "+k)
            changed+=len(diffs)
    ck(n==N and seen==set(patches),"Incomplete full-length humidity source audit")
    print("INDEPENDENT HUMIDITY FULL FILE AUDIT PASS",n,
          "new_humidity_target_HH",len(patches),"changed_field_cells",changed)
    return changed
def test():
    ck(phys(0.,-20.) and not phys(1.,-30.) and
       phys(10.,20.) and not phys(-1.,20.),
       "Synthetic saturated VPD physics incorrect")
    ck(abs(100*(1-phys_dummy(6.112,0)))<1e-9,
       "Synthetic relative humidity closure failed")
    print("SYVH1 SELF-TEST PASS: source physics, no scientific writes")
def phys_dummy(v,t):
    return v/saturation(t)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--apply-existing",action="store_true")
    modes.add_argument("--run",action="store_true")
    p.add_argument("--max-downloads",type=int,default=5)
    a=p.parse_args();test()
    if a.self_test:return
    ck(1<=a.max_downloads<=5,"CDS site-year max downloads must be 1..5")
    (ex,point,status,byyear,fields,manifest,left,h,e,native,paired)=plan()
    if a.check:
        print("SYVH1 READ ONLY CHECK COMPLETE; CDS zero requests, source/model zero writes")
        return
    if a.run:
        n=0
        for y,c in sorted(byyear.items(),key=lambda x:(-x[1],x[0])):
            if status[y] is not None:continue
            if n>=a.max_downloads:break
            path=ex.download_one(SITE,y,point)
            # Helper may return a receipt, not a direct path. Always fetch the SHA
            # verified site-year path with helper's documented response method.
            status[y]=ex.response_receipt(SITE,y)
            ck(status[y] is not None,"CDS download returned no verified source "+str(y))
            n+=1
        print("SYVH1 CDS DOWNLOADS THIS RUN",n,"MAX_REQUESTS",a.max_downloads)
    patches,blocked,used,priority=science(ex,point,status,left,h,e,native,paired)
    if not patches:
        print("NO SAFE INDEPENDENT OR VALID PAIRED HUMIDITY REPAIRS AVAILABLE; NO CANDIDATE WRITTEN")
        return
    out=EXP/"manual_US_Syv_stage_SYVH1_433_humidity_era5land_candidate_not_approved"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_NOT_FOR_POSTV5_DATM_CIME_SLURM_SPINUP").write_text(
        "Original 433 non-T source science HOLDs; humidity-only partial research candidate, further science approval required.\n")
    candidate=out/"US-Syv_SYVH1_433_residual_humidity_research_FLUXMET_HH.csv"
    csha=write_new(PARENT_CSV,candidate,patches)
    cells=independent_audit(PARENT_CSV,candidate,patches)
    nextmanifest=[]
    for x in manifest:
        y=dict(x)
        if y["site"]==SITE:
            y["source_path"]=str(candidate)
            y["source_SHA256"]=csha
            y["latest_stage"]="US_SYV_SYVH1_HUMIDITY_EVIDENCE_LIMITED_NOT_PRODUCTION"
        nextmanifest.append(y)
    ck([x for x in manifest if x["site"]!=SITE]==
       [x for x in nextmanifest if x["site"]!=SITE],
       "Changed other nine source selections")
    m=out/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    with m.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader();w.writerows(nextmanifest)
    ledger=out/"SYVH1_HUMIDITY_SOURCE_PROVENANCE.tsv"
    with ledger.open("x",encoding="utf-8",newline="") as f:
        rows=[patches[k] for k in sorted(patches)]
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t")
        w.writeheader();w.writerows(rows)
    remaining=left-set(patches)
    receipt={
       "status":"SOURCE_VERIFIED_RESEARCH_HUMIDITY_ONLY_NOT_POSTV5_APPROVED",
       "production_approval":False,
       "site":SITE,"native_rows":N,
       "parent_full_sha256":PARENT_SHA,
       "new_candidate_sha256":csha,
       "candidate_path":str(candidate),
       "initial_original_humidity_legacy_HOLD_HH":433,
       "actually_modified_source_HH":len(patches),
       "legacy_HOLD_remaining_not_numerically_repaired":len(remaining),
       "science_hold_dispositions":dict(blocked),
       "humidity_evidence_classes":dict(used),
       "parent_191_new_T_and_106_old_T_unchanged":True,
       "other_nine_site_manifest_unchanged":True,
       "source_ERA5Land_receipts_by_year":
       {str(y):({"path":str(q),"sha256":digest(q)} if q else "MISSING")
        for y,q in status.items()},
       "new_changed_field_cells":cells,
       "postv5_approved":False,"DATM_ready":False,"spinup":False
    }
    (out/"SYVH1_SCIENCE_RECEIPT.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    (out/"SYVH1_REMAINING_HUMIDITY_HOLDS.tsv").write_text(
        "TIMESTAMP_START\tOLD_REASON\tSTATUS\n"+
        "".join(k+"\t"+h.get(k,e.get(k,""))+"\t"+
                ("PHYS_VALID_OLD_HOLD" if phys(val(native[k]["VPD_F"]),val(native[k]["TA_F"]))
                 else "REQUIRES_INDEPENDENT_OR_VALID_PAIRED_HUMIDITY")+"\n"
                for k in sorted(remaining)),
        encoding="utf-8")
    print("US-SYV SYVH1 NUMERICALLY SAFE HUMIDITY CANDIDATE CREATED & FULL AUDIT PASS",out)
    print("NEW US-SYV CANDIDATE SHA256",csha)
    print("NEW TEN SITE RESEARCH INPUT MANIFEST",m)
    print("ORIGINAL_HUMIDITY_SOURCE_HOLDS_REMAINING",len(remaining),
          "PHYSICALLY_REPAIRED_THIS_RUN",len(patches))
    print("NO ORIGINAL, PREVIOUS 191/106 T CANDIDATES, OTHER NINE SITES OR MODEL WRITES")
if __name__=="__main__":main()

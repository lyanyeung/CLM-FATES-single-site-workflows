#!/usr/bin/env python3
"""Batch04 US-Syv: source-pinned QC decision review of residual humidity science HOLDs.

Read-only. Execute AFTER the operator's next SYVH1 --apply-existing (which
uses verified independent ERA5-Land for all remaining site-years). Require
the supplied candidate's own receipt/SHA and 10-site manifest, the original
606+10 source HOLDs, previous user-approved 106+191 temperature source
provenance, 438288 full original HH, exact source source fields and QC.

Report final residual science HOLD disposition, including all 18 historical
physically valid source-HOLD samples, checking native tower-source VPD QC,
ERA paired source, T, VPD, PA, saturation and RH closure. Identify whether
the historical flag concerns grid evidence ONLY or also native humidity.
Do not automatically remove historical source holds or overwrite science
source. Audit all full Syv candidate rows for any invalid T/VPD globally.

--check: stdout only
--report: print same and write a new HOME audit CSV
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

E=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=E/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=E/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
FIRST=E/"manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved/candidate_20261026T010755Z_591ef88f"
SECOND=E/"manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_20261026T024759Z_6e1e07ad"
SECONDFILE=SECOND/"US-Syv_all_remaining_QC0_QC1_ERA_T_full_FLUXMET_HH.csv"
SECOND_SHA="508295cfb64d5cfd116e4e6f91acc304b15ee16d3c6fab4673e07680137592ad"
N=438288
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
TARGET_COLS=("TIMESTAMP_START","TA_F","TA_F_QC","PA_F","VPD_F","VPD_F_QC","RH")

def check(p,msg):
    if not p:raise ValueError(msg)
def regular(p):
    check(p.is_file() and not p.is_symlink(),"File missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def obj(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def table(p,fields,delim=","):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter=delim)
        check(rd.fieldnames is not None and set(fields).issubset(rd.fieldnames),
              "Unexpected CSV columns "+str(p))
        return rd.fieldnames,list(rd)
def val(x):
    z=str(x if x is not None else "").strip()
    if z.upper() in MISSING:return None
    try:v=float(z)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None
def es(t):
    if t is None or t < -60 or t > 60:return None
    return 6.112*math.exp(17.67*t/(t+243.5))
def valid(t,v):
    s=es(t)
    return s is not None and v is not None and -1e-9<=v<=s+1e-8
def rhcheck(row):
    t=val(row["TA_F"]);v=val(row["VPD_F"]);r=val(row["RH"])
    if not valid(t,v):return "VPD_PHYSICAL_INVALID"
    if r is None:return "RH_MISSING"
    if not 0<=r<=100:return "RH_OUT_OF_RANGE"
    diff=abs(r-100*(1-v/es(t)))
    return "T_VPD_RH_CLOSURE_PASS" if diff<=0.15 else "RH_NOT_CLOSED_DELTA_"+format(diff,".3f")
def native_rows(p,fields,wanted,full=False):
    got={};n=0;bad=0;badexamples=[]
    qc=Counter()
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        check(rd.fieldnames is not None and set(fields).issubset(rd.fieldnames),
              "Full candidate source required schema missing "+str(p))
        for row in rd:
            n+=1;k=row["TIMESTAMP_START"]
            if k in wanted:
                check(k not in got,"Duplicate hold in full candidate "+k)
                got[k]={col:row[col] for col in fields}
            if full:
                t=val(row["TA_F"]);v=val(row["VPD_F"])
                qc[row["TA_F_QC"]]+=1
                if not valid(t,v):
                    bad+=1
                    if len(badexamples)<15:badexamples.append((k,row["TA_F"],row["VPD_F"],row["TA_F_QC"]))
    if full:check(n==N,"Full Syv candidate row count changed")
    check(set(wanted).issubset(got),"Missing full original science HOLD time keys "+str(p))
    return got,n,bad,badexamples,qc
def source_contract(candidate_dir):
    receipt=obj(candidate_dir/"SYVH1_SCIENCE_RECEIPT.json")
    check(receipt.get("native_rows")==N and
          receipt.get("parent_full_sha256")==SECOND_SHA and
          receipt.get("production_approval") is False and
          receipt.get("site")=="US-Syv",
          "Not a valid SYVH1 research-only source")
    cand=Path(receipt["candidate_path"])
    check(cand.parent==candidate_dir and
          sha(cand)==receipt["new_candidate_sha256"],
          "SYVH1 candidate path/SHA evidence invalid")
    check(sha(SECONDFILE)==SECOND_SHA,
          "Previous user-approved 297 Syv temperature research parent SHA changed")
    fields,manifest=table(candidate_dir/"RESEARCH_TEN_SITE_MANIFEST.tsv",
                          ("site","source_path","source_SHA256","latest_stage"),"\t")
    check(len(manifest)==10 and len({x["site"] for x in manifest})==10,
          "Final manifest not ten unique sites")
    chosen=[x for x in manifest if x["site"]=="US-Syv"]
    check(len(chosen)==1 and Path(chosen[0]["source_path"])==cand and
          chosen[0]["source_SHA256"]==receipt["new_candidate_sha256"],
          "Final 10-site manifest not selecting this verified SYVH1")
    _,previous_manifest=table(SECOND/"RESEARCH_TEN_SITE_MANIFEST.tsv",
                              ("site","source_path","source_SHA256","latest_stage"),"\t")
    a=[x for x in previous_manifest if x["site"]!="US-Syv"]
    b=[x for x in manifest if x["site"]!="US-Syv"]
    check(a==b,"One of other nine site source pointers unexpectedly changed")
    return cand,receipt
def provenance():
    stage5=obj(S05/"report.json")
    meta=stage5["sites"]["US-Syv"]
    check(meta["rows"]==N and meta["hold_rows"]==606 and
          sha(S05/"report.json")==obj(S07/"stage07_sha_receipt.json")["source_stage05_report_sha256"],
          "Stage05/07 provenance mismatch")
    original=Path(meta["paths"]["native"]);grid=Path(meta["paths"]["era"])
    check(sha(original)==meta["source_provenance"]["native"]["sha256"] and
          sha(grid)==meta["source_provenance"]["era"]["sha256"],
          "Original FLUXMET/packaged ERA source SHA mismatch")
    _,rows=table(S05/"unresolved_hold.csv",("site","TIMESTAMP_START","reason"))
    _,skips=table(S07/"stage07_unsafe_ERA_target_holds.csv",
                  ("site","TIMESTAMP_START","reason"))
    hold={x["TIMESTAMP_START"]:x["reason"] for x in rows if x["site"]=="US-Syv"}
    edge={x["TIMESTAMP_START"]:x["reason"] for x in skips if x["site"]=="US-Syv"}
    check(len(rows)==754 and len(hold)==606 and len(edge)==10 and
          not (set(hold)&set(edge)),"606+10 original archive census mismatch")
    done=set()
    for p,name,n in (
      (FIRST/"SIX_OPERATOR_106_HH_ERA_T_FULL_PROVENANCE.tsv","first",106),
      (SECOND/"NEW_SOURCE_TA_ERA_REPAIR_LEDGER.tsv","second",191)):
        _,data=table(p,("TIMESTAMP_START",),"\t")
        keys={x["TIMESTAMP_START"] for x in data}
        check(len(data)==n and len(keys)==n and not done.intersection(keys),
              "User old T repair history mismatch "+name)
        done.update(keys)
    check(len(done)==297,"Prior 297 user approved T target count shifted")
    left=(set(hold)|set(edge))-done
    check(len(left)==433,"Expected 433 unique old humidity source HOLDs")
    return original,grid,hold,edge,left,done
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate",required=True,help="Exact directory printed by SYVH1 last --apply-existing or --run")
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--report",action="store_true")
    arg=p.parse_args()
    directory=Path(arg.candidate)
    check(directory.is_dir() and not directory.is_symlink(),
          "Exact candidate path missing")
    result,receipt=source_contract(directory)
    original,grid,h,e,left,done=provenance()
    need=set(left)
    prev,_,_,_,_=native_rows(SECONDFILE,TARGET_COLS,need,True)
    latest,_,globally_invalid,glob_bad,qc=native_rows(result,TARGET_COLS,need,True)
    site,_,_,_,_=native_rows(original,
            ("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"),need,True)
    era,_,_,_,_=native_rows(grid,("TIMESTAMP_START","TA_ERA","VPD_ERA"),need)
    replaced={x["TIMESTAMP_START"] for x in
        table(directory/"SYVH1_HUMIDITY_SOURCE_PROVENANCE.tsv",
              ("TIMESTAMP_START",),"\t")[1]}
    still=need-replaced
    check(len(replaced)==receipt["actually_modified_source_HH"] and
          len(still)==receipt["legacy_HOLD_remaining_not_numerically_repaired"],
          "Receipt and source-ledger residual HOLD counts disagree")
    cls=Counter();qcval=Counter();allrows=[]
    print("LATEST VERIFIED SYVH1 RESEARCH SITE FULL SHA",receipt["new_candidate_sha256"])
    print("SYV FULL FILE GLOBAL INVALID T_VPD HH",globally_invalid,
          "SOURCE_TA_QC",dict(qc),"FIRST_15_GLOBAL_INVALID",glob_bad)
    print("ORIGINAL 433 H/H OLD SOURCE HANDLED",len(replaced),
          "UNMODIFIED_OLD_SOURCE_HH",len(still))
    print("EXACT UNMODIFIED HISTORICAL SOURCE H/H RECORDS")
    print("TIME SOURCE_REASON TA_C TA_QC ORIGINAL_TA_QC VPD_hPa VPD_QC RH_pct SAT_hPa VPD_RH_CLOSURE TA_ERA_C VPD_ERA_hPa SCIENCE_DISPOSITION")
    for k in sorted(still):
        z=latest[k];o=site[k];er=era[k]
        t=val(z["TA_F"]);v=val(z["VPD_F"])
        oldreason=h.get(k,e.get(k,"UNKNOWN"))
        if not valid(t,v):
            state="NEEDS_INDEPENDENT_HUMIDITY_SOURCE"
        elif z["VPD_F_QC"]=="0" and rhcheck(z)=="T_VPD_RH_CLOSURE_PASS":
            state="KEEP_NATIVE_QC0_HUMIDITY_PHYS_AND_CLOSURE_PASS_ARCHIVE_GRID_FLAG"
        elif z["VPD_F_QC"]=="0":
            state="KEEP_NATIVE_QC0_VPD_PHYSICAL_BUT_RH_QA_REQUIRED"
        elif valid(t,v) and rhcheck(z)=="T_VPD_RH_CLOSURE_PASS":
            state="NON_QC0_NATIVE_HUMIDITY_PHYS_PASS_QC_PROVENANCE_REVIEW"
        else:
            state="HISTORIC_ERA_SOURCE_HOLD_QC_OR_RH_REVIEW"
        cls[state]+=1;qcval[z["VPD_F_QC"]]+=1
        item=[k,oldreason,z["TA_F"],z["TA_F_QC"],o["TA_F_QC"],
              z["VPD_F"],z["VPD_F_QC"],z["RH"],
              str(es(t)) if es(t) is not None else "NA",
              rhcheck(z),er["TA_ERA"],er["VPD_ERA"],state]
        allrows.append(item)
        print(" ".join(item))
    print("RESIDUAL SCIENTIFIC DISPOSITIONS",dict(cls),
          "SOURCE_VPD_QC_COUNTS",dict(qcval))
    print("RESEARCH AUDIT ONLY, source grid HOLD remains immutable, no DATM/CIME/Slurm/CLM model release")
    if arg.report:
        home=Path.home()/"ameriflux_batch04_manual_review"
        home.mkdir(exist_ok=True,parents=True)
        dest=home/("US_Syv_SYVH1_after_all_grid_years_historical_18_and_global_physics_"+
                   uuid4().hex[:8]+".tsv")
        with dest.open("x",encoding="utf-8",newline="") as f:
            w=csv.writer(f,delimiter="\t")
            w.writerow(["native_HH","historical_reason","current_T_C","current_T_QC",
                       "source_original_T_QC","current_VPD_hPa","current_VPD_QC",
                       "current_RH_pct","es_newT_hPa","RH_physical_closure",
                       "processed_FLUXNET_TA_ERA_C","processed_FLUXNET_VPD_ERA_hPa",
                       "science_disposition"])
            w.writerows(allrows)
        print("AUDIT TSV",dest,"SHA256",sha(dest))
if __name__=="__main__":main()

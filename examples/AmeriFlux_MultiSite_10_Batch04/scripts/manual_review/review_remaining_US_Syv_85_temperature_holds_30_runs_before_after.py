#!/usr/bin/env python3
"""US-Syv remaining 85 native T-versus-grid HOLDs in 30 runs — complete before/after.

SHA-pin 2007/2003 already user-authorized 106 ERA-origin T alternatives,
the unchanged original, Stage05 science HOLD and paired FLUXNET ERA source.
Print all 85 old HOLD HH and +/- 2h in 30 contiguous science runs, including
original TA_F/TA_F_QC, TA_F_MDS, Stage07 T, final 106HH research candidate T,
packaged TA_ERA (not independent ERA5-Land!), VPD/QC and source HOLD reason.

--review: stdout only, no writes.
--report: also writes ONE CSV of all printed rows under HOME.
No original/HPC science candidate overwrite, DATM, CIME, Slurm or model jobs.
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta
from collections import Counter
from pathlib import Path
from uuid import uuid4

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=EXP/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
NEW=EXP/"manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved/candidate_20261026T010755Z_591ef88f"
NEW_FILE=NEW/"US-Syv_six_intervals_106HH_ERA_T_manual_research_FLUXMET_HH.csv"
NEW_SHA="8ac03873ad573e2885569f371ce6a413d4f3f230d7f473ece6c7e20bb7bf1b73"
N=438288
EXCLUDED=(
("200702081730","200702082130"),
("200702091730","200702092330"),
("200702101730","200702110700"),
("200702111730","200702120700"),
("200702121730","200702122230"),
("200304271130","200304271930"))
T_FIELDS=("TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS","TA_F_MDS_QC","VPD_F","VPD_F_QC")
S_FIELDS=("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC")
ERA_FIELDS=("TIMESTAMP_START","TA_ERA","VPD_ERA")
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Missing/symlink source: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):h.update(block)
    return h.hexdigest()
def obj(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def at(s):return datetime.strptime(s,"%Y%m%d%H%M")
def stamp(t):return t.strftime("%Y%m%d%H%M")
def seq(start,end):
    a=at(start);b=at(end)
    ck(b>=a and int((b-a).total_seconds())%1800==0,"Non-half-hour interval")
    return [stamp(a+timedelta(minutes=30*i)) for i in range(int((b-a).total_seconds()/1800)+1)]
def num(x):
    s=str(x if x is not None else "").strip()
    if s.upper() in MISSING:return None
    try:v=float(s)
    except ValueError:return None
    return v if math.isfinite(v) else None
def fmt(x):
    v=num(x)
    return "NA" if v is None else f"{v:.3f}"
def readholds():
    with regular(S05/"unresolved_hold.csv").open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        ck(r.fieldnames and {"site","TIMESTAMP_START","reason"}.issubset(r.fieldnames),
           "Old source HOLD schema changed")
        syv={}
        n=0
        for x in r:
            n+=1
            if x["site"]=="US-Syv":
                k=x["TIMESTAMP_START"]
                ck(k not in syv,"Duplicate source HOLD "+k)
                syv[k]=x["reason"]
    ck(n==754 and len(syv)==606,"Stage05 original source HOLD count changed")
    approved=set()
    for a,b in EXCLUDED:approved.update(seq(a,b))
    ck(len(approved)==106,"User-allowed source temperature set changed")
    rem={k:r for k,r in syv.items() if
         r=="SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID" and k not in approved}
    ck(len(rem)==85,"Expected exact 85 untouched original temperature discrepancy HOLDs")
    return rem,syv,approved
def groups(keys):
    out=[]
    for k in sorted(keys):
        if not out or (at(k)-at(out[-1][-1])).total_seconds()!=1800:
            out.append([k])
        else:out[-1].append(k)
    return out
def getsource():
    m=obj(S05/"report.json");r=obj(S07/"stage07_sha_receipt.json")
    ck(m.get("mode")=="BUILD_CANDIDATE_OVERLAY" and
       m["sites"]["US-Syv"]["rows"]==N and m["sites"]["US-Syv"]["hold_rows"]==606,
       "Stage05 source contract changed")
    ck(r.get("inherited_stage05_holds")==754 and
       r.get("invalid_era_endpoints_held")==12,"Stage07 science receipt contract changed")
    ck(sha(S05/"report.json")==r["source_stage05_report_sha256"],
       "Stage07 pinned Stage05 report changed")
    inf=m["sites"]["US-Syv"]
    original=Path(inf["paths"]["native"]);era=Path(inf["paths"]["era"])
    ck(sha(original)==inf["source_provenance"]["native"]["sha256"],
       "Original source full SHA changed")
    ck(sha(era)==inf["source_provenance"]["era"]["sha256"],
       "Original ERA full SHA changed")
    prior_meta=r["derived_full_length_files"]["US-Syv"]
    prior=Path(prior_meta["full_derived_file"])
    ck(sha(prior)==prior_meta["sha256"]=="5086cbc0f08f73b218d08fdcf34cf0643a6ae1ea95c05c200a98800452b5b32e",
       "Stage07 previous full Syv candidate SHA changed")
    ck(sha(NEW_FILE)==NEW_SHA,"User-executed 106HH research candidate SHA mismatch")
    receipt=obj(NEW/"SCIENCE_RESEARCH_RECEIPT.json")
    ck(receipt.get("total_operator_selected_native_HH")==106 and
       receipt.get("new_US_Syv_full_SHA256")==NEW_SHA and
       receipt.get("model_production_approval") is False,
       "Latest Syv research receipt mismatch")
    return original,prior,era
def subset(p,fields,keys,nrows=None):
    got={};n=0
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        ck(r.fieldnames and set(fields).issubset(r.fieldnames),
           "Unexpected source fields "+str(p))
        for x in r:
            n+=1;k=x["TIMESTAMP_START"]
            if k in keys:
                ck(k not in got,"Duplicate source halfhour "+k)
                got[k]={col:x[col] for col in fields}
    if nrows is not None:ck(n==nrows,"Complete original/candidate source row-count mismatch")
    ck(set(keys).issubset(got),"Some precise requested 30-min timestamps missing in "+str(p))
    return got
def run(write):
    source,prior,era=getsource()
    remain,legacy,approved=readholds()
    ev=groups(remain)
    ck(len(ev)==30 and sum(map(len,ev))==85,
       "Verified expected 30 unique runs 85 HH changed")
    requested=set()
    for g in ev:
        requested.update(seq(stamp(at(g[0])-timedelta(hours=2)),
                             stamp(at(g[-1])+timedelta(hours=2))))
    original=subset(source,T_FIELDS,requested,N)
    prev=subset(prior,S_FIELDS,requested,N)
    repaired=subset(NEW_FILE,S_FIELDS,requested,N)
    packed=subset(era,ERA_FIELDS,requested)
    print("US-SYV SOURCE SHA VERIFICATION PASS original, Stage07, 106HH final, packaged ERA")
    print("SIX USER-APPROVED ERA-T INTERVALS PRESERVED, 106 HH; NO NEW REPLACEMENTS")
    print("REMAINING_T_GRID_HOLD_HH",len(remain),"CONTIGUOUS_RUNS",len(ev),
          "FULL_HH_INC_2H_FLANKS",len(requested))
    print("NOTE TA_F_QC 0=original product observed, 1=MDS fill, 2=ERA fill.")
    print("NOTE TA_ERA=FLUXNET packaged processed ERA temperature, NOT independent ERA5-Land.")
    ranked=sorted(ev,key=lambda g:(-sum(original[k]["TA_F_QC"]=="0" for k in g),
                                     -len(g),g[0]))
    out=[]
    for i,g in enumerate(ranked,1):
        before=stamp(at(g[0])-timedelta(hours=2))
        after=stamp(at(g[-1])+timedelta(hours=2))
        q=Counter(original[k]["TA_F_QC"] for k in g)
        first=g[0]
        v1=num(original[first]["TA_F"]);v2=num(packed[first]["TA_ERA"])
        print(f"\n=== REVIEW {i}/30 FROM {g[0]} TO {g[-1]} | {len(g)} HH | SOURCE_QC {dict(q)} | FIRST_DELTA {(f'{v1-v2:+.3f}C' if v1 is not None and v2 is not None else 'NA')} ===")
        print("TIME FLAG RAW_TA_C RAW_TA_QC RAW_T_MDS_C RAW_MDS_QC FLUXNET_TA_ERA_C RAW_MINUS_ERA_C STAGE07_T_C LATEST_106_T_C LATEST_T_QC LATEST_VPD_hPa LATEST_VPD_QC HOLD_REASON")
        for k in seq(before,after):
            a=original[k];b=prev[k];c=repaired[k];d=packed[k]
            ta=num(a["TA_F"]);tref=num(d["TA_ERA"])
            delta="NA" if ta is None or tref is None else f"{ta-tref:+.3f}"
            flag="HOLD" if k in rem else ("BEFORE" if k<g[0] else "AFTER" if k>g[-1] else "OTHER")
            row=[str(i),g[0],g[-1],k,flag,a["TA_F"],a["TA_F_QC"],
                 a["TA_F_MDS"],a["TA_F_MDS_QC"],d["TA_ERA"],delta,
                 b["TA_F"],c["TA_F"],c["TA_F_QC"],c["VPD_F"],c["VPD_F_QC"],
                 legacy.get(k,"-")]
            print(" ".join(row[3:]))
            out.append(row)
    byQC=Counter(original[k]["TA_F_QC"] for k in rem)
    print("\nUS-SYV 85 ORIGINAL TA QC",dict(byQC))
    print("US-SYV COMPLETE READ ONLY T TRIAGE PASS 85/85 HOLD HH 30/30 RUNS")
    print("OTHER SCIENCE REMAIN 518 ORIGINAL HOLD HH; 500 BASIC SATURATION VPD FAIL BEFORE ANY NEXT HUMIDITY REPAIR")
    if write:
        folder=Path.home()/"ameriflux_batch04_manual_review"
        folder.mkdir(parents=True,exist_ok=True)
        outfile=folder/("US_Syv_remaining_85_temperature_HOLD_30_runs_full_flanks_"+uuid4().hex[:8]+".csv")
        cols=("review_rank","episode_first_HH","episode_last_HH","timestamp","flag",
              "original_TA_F_C","original_TA_F_QC","original_TA_F_MDS_C","original_MDS_QC",
              "packaged_FLUXNET_TA_ERA_C","original_minus_ERA_C",
              "prior_Stage07_T_C","final_106_candidate_T_C","final_T_QC",
              "final_106_candidate_VPD_hPa","final_VPD_QC","source_old_HOLD_reason")
        with outfile.open("x",encoding="utf-8",newline="") as f:
            w=csv.writer(f);w.writerow(cols);w.writerows(out)
        print("NEW READ-ONLY STUDY CSV",outfile,"SHA256",sha(outfile))
    print("NO ORIGINAL, STAGE05/07, USER-APPROVED 106/137-HH CANDIDATES, POSTV5 OR MODEL WRITES")
def selftest():
    t={x for a,b in EXCLUDED for x in seq(a,b)}
    ck(len(t)==106 and "200702120700" in t and "201702101730" not in t,
       "Manual approved 106 timestamp logic changed")
    ck(len(NEW_SHA)==64 and len(groups(["200305300730","200305300800","200305300930"]))==2,
       "Source 30min grouping invalid")
    print("US-SYV REMAINING 85 T HOLD SELF-TEST PASS, expected 30 runs; no writes")
if __name__=="__main__":
    a=argparse.ArgumentParser(description=__doc__)
    g=a.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--review",action="store_true")
    g.add_argument("--report",action="store_true")
    z=a.parse_args();selftest()
    if z.review or z.report:run(z.report)

#!/usr/bin/env python3
"""Stage 12: context/continuity audit of UNAPPLIED AmeriFlux VPD proposals.

This script reads the Stage11 ledger plus the exact pinned FLUXMET_HH source
for one site (default CA-Man). It checks proposal-to-original reproducibility,
the VPD physical bound using original site TA/PA, and VPD jumps at BOTH ends
of each run of consecutive proposed half-hours. The outputs are small reports
only; it does NOT write a revised forcing series or approve any change.
"""
import argparse
import csv
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
BATCH=Path(__file__).resolve().parents[2]
SELECT="PROPOSAL_VPD_ONLY_MANUAL_APPROVAL_REQUIRED"
STEP=timedelta(minutes=30)


def read(path, delim=","):
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter=delim))


def write(path, data, fields):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader()
        w.writerows(data)


def flt(x):
    try:
        a=float(x)
    except (ValueError,TypeError):
        return None
    return a if math.isfinite(a) and a>-9990 else None


def close(a,b):
    return a is not None and b is not None and math.isclose(a,b,abs_tol=1e-6,rel_tol=1e-8)


def nearest_source(site, package):
    folder=ROOT/site/"forcing"/"raw"/package
    match=sorted(x for x in folder.glob("*.csv") if "FLUXMET_HH" in x.name.upper())
    if len(match)!=1:
        raise RuntimeError("Expected one pinned FLUXMET_HH source in "+str(folder))
    return match[0]


def source_stamp(t):
    return t.strftime("%Y%m%d%H%M")


def source_matches(filename, wanted):
    result={}
    with filename.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required={"TIMESTAMP_START","TA_F","PA_F","VPD_F","VPD_F_QC"}
        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError("Source missing columns "+str(required-set(reader.fieldnames or [])))
        for row in reader:
            key=str(row["TIMESTAMP_START"]).strip()
            if key.endswith(".0"): key=key[:-2]
            if key not in wanted: continue
            if key in result:
                raise RuntimeError("Duplicated matching FLUXMET timestamp: "+key)
            result[key]={x:row.get(x) for x in required}
    return result


def calc(ta,pa,vpd):
    if None in (ta,pa,vpd):
        return None
    if not (-80<=ta<=65 and 50<=pa<=110):
        return None
    es=6.112*math.exp(17.67*ta/(ta+243.5))
    ea=es-vpd
    pressure=1000*pa
    denominator=pressure-0.378*ea*100
    if denominator<=0: return None
    q=0.622*ea*100/denominator
    return dict(es=es,ea=ea,q=q,rh=100*ea/es)


def report_location():
    folders=sorted(p for p in REPORTS.glob("stage11_vpd_candidates_*")
                   if (p/"all_flagged_source_event_decisions.csv").is_file())
    if not folders:
        raise RuntimeError("Stage11 report missing from "+str(REPORTS))
    return folders[-1]


def episodes(seq):
    bundles=[]
    current=[]
    for r in seq:
        if current and r["time"]-current[-1]["time"]!=STEP:
            bundles.append(current)
            current=[]
        current.append(r)
    if current: bundles.append(current)
    return bundles


def boundary(current, prefix, source):
    """A single edge; no missing-neighbour interpolation is attempted."""
    t=current["time"]
    neighbour=t-STEP if prefix=="PRE" else t+STEP
    match=source.get(source_stamp(neighbour))
    if not match: return dict(original=None,proposed=None)
    v=flt(match["VPD_F"])
    if v is None: return dict(original=None,proposed=None)
    old=current["original"]
    new=current["proposed"]
    return dict(original=abs(old-v),proposed=abs(new-v))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site",default="CA-Man")
    ap.add_argument("--stage11-dir",type=Path)
    ap.add_argument("--report-root",type=Path,default=REPORTS)
    args=ap.parse_args()
    manifest=read(BATCH/"sites.tsv", "\t")
    packages={r["site"]:r["package"] for r in manifest}
    if args.site not in packages:
        ap.error("Unknown batch site: "+args.site)
    base=args.stage11_dir or report_location()
    ledger=read(base/"all_flagged_source_event_decisions.csv")
    target=[r for r in ledger if r["site"]==args.site and
            r["flagged_source"]=="FLUXMET_HH"]
    proposals=[r for r in target if r["decision"]==SELECT]
    print("STAGE12 PREFLIGHT:",args.site,"FLUXMET flagged",len(target),
          "VPD proposals",len(proposals),"remaining HOLD",len(target)-len(proposals),
          flush=True)
    if not proposals:
        print("No Stage11 VPD candidates for selected site; nothing to audit.")
        return
    times={}
    needed=set()
    for r in proposals:
        dt=datetime.strptime(r["timestamp_local"],"%Y-%m-%d %H:%M")
        k=source_stamp(dt)
        if k in times:
            raise RuntimeError("Duplicate proposal timestamp "+k)
        times[k]=(r,dt)
        needed.update(source_stamp(dt+i*STEP) for i in range(-1,2))
    infile=nearest_source(args.site,packages[args.site])
    original=source_matches(infile,needed)
    print("PINNED SOURCE:",infile)
    print("Source rows matched:",len(original),"/",len(needed),"needed including neighbours")
    validations=[]
    issues=[]
    for key,(r,dt) in sorted(times.items()):
        match=original.get(key)
        if match is None:
            issues.append("MISSING_SOURCE "+key);continue
        vals={col:flt(match[col]) for col in ("TA_F","PA_F","VPD_F","VPD_F_QC")}
        for local,col in (("original_TA_C","TA_F"),
                          ("original_PA_kPa","PA_F"),
                          ("original_VPD_hPa","VPD_F")):
            if not close(flt(r[local]), vals[col]):
                issues.append("SOURCE_CHANGED "+key+" "+col)
        if not close(vals["VPD_F_QC"],1):
            issues.append("QC_NOT_1 "+key)
        proposed=flt(r["candidate_VPD_hPa"])
        old=calc(vals["TA_F"],vals["PA_F"],vals["VPD_F"])
        new=calc(vals["TA_F"],vals["PA_F"],proposed)
        if old is None or old["ea"]>0:
            issues.append("ORIGINAL_NOT_NONPHYSICAL "+key)
        if new is None or new["ea"]<=0 or not (0<=new["q"]<=.08):
            issues.append("PROPOSAL_NOT_PHYSICAL "+key)
        if issues and any(key in x for x in issues):
            continue
        validations.append(dict(
            time=dt, timestamp_local=r["timestamp_local"],
            original=vals["VPD_F"], proposed=proposed,
            temp_C=vals["TA_F"], original_rh=old["rh"], proposed_rh=new["rh"],
            delta_hPa=proposed-vals["VPD_F"],qc=int(vals["VPD_F_QC"])))
    if issues:
        print("BLOCKED: %d validation failures (first 20 shown)"%len(issues),flush=True)
        for item in issues[:20]:print("  ",item,flush=True)
        raise SystemExit("Source or candidate changed; no report generated.")

    runs=episodes(validations)
    events=[]
    for r in validations:
        events.append(dict(site=args.site,timestamp_local=r["timestamp_local"],
                           source_VPD_hPa=r["original"],proposed_VPD_hPa=r["proposed"],
                           delta_VPD_hPa=r["delta_hPa"],source_TA_C=r["temp_C"],
                           original_RH_pct=r["original_rh"],
                           proposed_RH_pct=r["proposed_rh"],
                           original_QC=r["qc"],decision="UNAPPLIED_MANUAL_REVIEW"))
    episode_rows=[]
    actions=Counter()
    for i,run in enumerate(runs,1):
        first,last=run[0],run[-1]
        pre=boundary(first,"PRE",original)
        post=boundary(last,"POST",original)
        original_sum=(pre["original"]+post["original"] if
                      pre["original"] is not None and post["original"] is not None
                      else None)
        proposed_sum=(pre["proposed"]+post["proposed"] if
                      pre["proposed"] is not None and post["proposed"] is not None
                      else None)
        if original_sum is None:
            status="MISSING_BOUNDARY"
        elif proposed_sum>=original_sum+2:
            status="CANDIDATE_INCREASES_EDGE_JUMP_SUM_GE2HPA"
        elif proposed_sum<=original_sum-2:
            status="CANDIDATE_DECREASES_EDGE_JUMP_SUM_GE2HPA"
        else:
            status="EDGE_CHANGE_WITHIN_2HPA"
        actions[status]+=1
        episode_rows.append(dict(site=args.site,episode=i,
                 first_local=first["timestamp_local"],last_local=last["timestamp_local"],
                 candidate_halfhours=len(run),duration_hours=len(run)*.5,
                 first_pre_jump_original_hPa=pre["original"],
                 first_pre_jump_proposal_hPa=pre["proposed"],
                 last_post_jump_original_hPa=post["original"],
                 last_post_jump_proposal_hPa=post["proposed"],
                 sum_boundary_jump_original_hPa=original_sum,
                 sum_boundary_jump_proposal_hPa=proposed_sum,
                 max_abs_VPD_change_hPa=max(abs(x["delta_hPa"]) for x in run),
                 min_proposal_RH_pct=min(x["proposed_rh"] for x in run),
                 boundary_diagnostic=status,
                 decision="HOLD_CONTEXT_REVIEW"))
    out=args.report_root/("stage12_candidate_context_"+args.site+"_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    out.mkdir(parents=True,exist_ok=False)
    write(out/"source_verified_unapplied_vpd_proposals.csv",events,list(events[0]))
    write(out/"candidate_episode_boundary_review.csv",episode_rows,list(episode_rows[0]))
    print("\nSTAGE12 SUMMARY: site",args.site,
          "validated_proposals",len(validations),
          "episodes",len(runs),"errors",len(issues),flush=True)
    print("Episode boundary diagnostics:",dict(actions),flush=True)
    print("Longest proposal episode:",max(len(r) for r in runs),"half-hours",flush=True)
    print("Candidate min RH:",round(min(r["proposed_rh"] for r in validations),3),
          "max RH:",round(max(r["proposed_rh"] for r in validations),3),flush=True)
    for item in sorted(episode_rows,key=lambda x:-x["candidate_halfhours"])[:8]:
        print("  %s -> %s count=%d boundary=%s" % (
            item["first_local"],item["last_local"],
            item["candidate_halfhours"],item["boundary_diagnostic"]),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("No forcing/DATM created and no VPD correction applied; reports only.",flush=True)
    print("Boundary jumps are heuristics, NOT approval criteria.",flush=True)


if __name__=="__main__":
    main()

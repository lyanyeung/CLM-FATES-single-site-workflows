#!/usr/bin/env python3
"""Stage 16: first AmeriFlux 10 sites -- ICOS-informed science/QC decision matrix.

INPUT: Stage15 verified full-cycle audit REPORTS ONLY.
Separately count nonphysical vapour, positive low-RH, suspicious TA/VPD
plateaux, temperature jumps/source disagreements, PA/LW, source-QC 0/1/2,
months/years, and overlapping flagged episodes.

Borrow CH-Aws's lesson that fixing RH<=0 does not guarantee CLM's diagnosed
2m RH is positive, and IT-Noe's paired TA/VPD/PA + source-seam checks.
US-Aud is arid grassland: 0<RH<10% alone is not permission to edit.

Runs a strict, fail-closed report-consistency audit. Reports alone, all
decisions HOLD. NEVER edits raw CSV, surface, forcing, DATM, CIME or Slurm.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SITES=("BR-Ma2","CA-Ca3","CA-Cbo","CA-LP1","CA-Man",
       "CA-TP1","CA-TP3","CA-TP4","US-Aud","US-Bar")
HARD=("EA_NONPOSITIVE","PA_OUTSIDE_50_110KPA","LW_OUTSIDE_60_800")
PAIR=("TA_30MIN_JUMP_GT8C","TA_VS_ERA_DIFF_GT15C",
      "PA_30MIN_JUMP_GT5KPA","ZERO_TA_VPD_PLATEAU_3HR",
      "TA_ZERO_VPD_6110")
LOW=("RH_POSITIVE_0_TO1","RH_POSITIVE_1_TO5","RH_POSITIVE_5_TO10")
FLAGS=HARD+PAIR+LOW
QC_VARS=("TA_F_QC","VPD_F_QC","PA_F_QC","LW_IN_F_QC")


def csv_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path,records,cols):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def count(row,col):
    try: return int(float(row.get(col) or 0))
    except (TypeError,ValueError):
        raise RuntimeError("Invalid count "+str(col)+" in "+str(row))


def yes(row,col):
    v=str(row.get(col,"")).strip().lower()
    if v in ("true","1","1.0"):return True
    if v in ("false","0","0.0","nan","none",""):return False
    raise RuntimeError("Unexpected boolean %s=%r"%(col,v))


def qc(row,col):
    value=str(row.get(col,"")).strip()
    if value in ("0","0.0"):return "QC0_MEASURED"
    if value in ("1","1.0"):return "QC1_GAPFILLED"
    if value in ("2","2.0"):return "QC2_ERA_DERIVED"
    return "QC_UNAVAILABLE_OTHER"


def find_report(root,explicit):
    if explicit:
        folder=explicit.expanduser()
    else:
        folders=sorted(f for f in root.glob("stage15_fullcycle_10sites_*")
                       if (f/"site_science_gate_summary.csv").is_file()
                       and (f/"two_hour_review_episode_ledger.csv").is_file())
        if not folders: raise RuntimeError("Cannot locate Stage15 full-cycle output")
        folder=folders[-1]
    needed=("site_science_gate_summary.csv",
            "annual_science_gate_counts.csv",
            "two_hour_review_episode_ledger.csv")
    for f in needed:
        if not (folder/f).is_file():
            raise RuntimeError("Missing input Stage15 report: "+str(folder/f))
    return folder


def triage(flags):
    if any(flags.get(x,False) for x in HARD):
        return "P0_INPUT_PHYSICAL"
    if any(flags.get(x,False) for x in PAIR):
        return "P1_TA_PA_SOURCE_CONTINUITY"
    if flags.get("RH_POSITIVE_0_TO1",False):
        return "P1_RH_POSITIVE_BELOW1"
    if flags.get("RH_POSITIVE_1_TO5",False):
        return "P2_RH_1_TO5"
    if flags.get("RH_POSITIVE_5_TO10",False):
        return "P3_RH_5_TO10"
    return "P3_OTHER_REVIEW"


def workstream(site):
    if site=="US-Aud":
        return "ARID_GRASSLAND_POSITIVE_LOW_RH_QC_SEASONALITY_NO_FLOOR;SURFACE_PFT"
    if site in ("CA-TP1","CA-TP3","CA-TP4"):
        return "TA_SOURCE_SEAM_AND_SURFACE_PFT_GRID_CROP"
    if site=="CA-Cbo":
        return "VPD_HUMIDITY_AND_TA_JUMPS;SURFACE_CROP_REPRESENTATIVENESS"
    if site=="CA-Man":
        return "STAGE14_105_253_RESIDUAL_RH;QC1_VPD_CONTEXT;TA_JUMPS"
    if site=="CA-LP1":
        return "EXPLAIN_TA_ERA_DISAGREEMENT_AND_LOW_RH;QC_PROVENANCE"
    if site=="US-Bar":
        return "IT_NOE_TA_JUMP_SOURCE_SWITCH;VPD_HUMIDITY"
    return "STATION_SPECIFIC_SOURCE_AND_CONTEXT_REVIEW"


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report-root",type=Path,default=DEFAULT_ROOT)
    ap.add_argument("--stage15-dir",type=Path)
    ap.add_argument("--top-events",type=int,default=12)
    args=ap.parse_args()
    if args.top_events<0: ap.error("--top-events must be nonnegative")

    source=find_report(args.report_root,args.stage15_dir)
    summary=csv_rows(source/"site_science_gate_summary.csv")
    annual=csv_rows(source/"annual_science_gate_counts.csv")
    episodes=csv_rows(source/"two_hour_review_episode_ledger.csv")
    smap={r["site"]:r for r in summary}
    if len(summary)!=10 or set(smap)!=set(SITES):
        raise RuntimeError("Expected exactly 10 unique Stage15 station summaries")
    annual_by_site=defaultdict(list)
    for r in annual:
        if r["site"] not in smap: raise RuntimeError("Unknown annual site")
        annual_by_site[r["site"]].append(r)
    episode_by_site=Counter(r["site"] for r in episodes)

    site_records=[]
    category_records=[]
    month_records=[]
    qc_records=[]
    priority_records=[]
    for site in SITES:
        f=source/(site+"_flagged_review_times.csv")
        if not f.is_file():raise RuntimeError("Missing "+str(f))
        rows=csv_rows(f)
        required={"time","episode_id","VPD_F_QC","RH_implied_pct",
                  "EA_implied_hPa"}|set(FLAGS)
        if rows and not required.issubset(rows[0]):
            raise RuntimeError("%s flagged CSV missing fields %s"%
                               (site,sorted(required-set(rows[0]))))
        if len(rows)!=count(smap[site],"fluxmet_flagged"):
            raise RuntimeError("%s: review row count mismatch %d vs %s"%
                               (site,len(rows),smap[site]["fluxmet_flagged"]))
        if episode_by_site[site]!=count(smap[site],"episodes"):
            raise RuntimeError(site+": episode count mismatch")
        if len(annual_by_site[site])!=count(smap[site],"years"):
            raise RuntimeError(site+": annual year coverage mismatch")
        for flag in FLAGS:
            reported=sum(count(r,flag) for r in annual_by_site[site])
            from_events=sum(yes(r,flag) for r in rows)
            if reported!=from_events:
                raise RuntimeError("%s flag %s annual=%d flagged=%d" %
                                   (site,flag,reported,from_events))
        pcounts=Counter()
        reasons=Counter()
        qcount=Counter()
        months=Counter()
        low_groups=Counter()
        by_year=Counter()
        seen=set()
        for row in rows:
            ts=row["time"]
            if ts in seen:raise RuntimeError(site+": duplicate flagged time "+ts)
            seen.add(ts)
            fl={name:yes(row,name) for name in FLAGS}
            code=triage(fl)
            pcounts[code]+=1
            by_year[ts[:4]]+=1
            months[ts[5:7]]+=1
            for name,enabled in fl.items():
                if enabled:reasons[name]+=1
            for v in QC_VARS:
                qcount[(v,code,qc(row,v))]+=1
            if any(fl[x] for x in LOW):
                bucket=next(x for x in LOW if fl[x])
                low_groups[(bucket,qc(row,"VPD_F_QC"),ts[5:7])]+=1

        site_records.append({
            "site":site,"scanned":count(smap[site],"source_rows"),
            "review_halfhours":len(rows),
            "episodes":count(smap[site],"episodes"),
            "P0_physical":pcounts["P0_INPUT_PHYSICAL"],
            "P1_TA_PA":pcounts["P1_TA_PA_SOURCE_CONTINUITY"],
            "P1_positive_RH_lt1":pcounts["P1_RH_POSITIVE_BELOW1"],
            "P2_positive_RH_1to5":pcounts["P2_RH_1_TO5"],
            "P3_positive_RH_5to10":pcounts["P3_RH_5_TO10"],
            "EA_nonpositive":reasons["EA_NONPOSITIVE"],
            "temp_gt8C_step":reasons["TA_30MIN_JUMP_GT8C"],
            "temp_vs_ERA_gt15C":reasons["TA_VS_ERA_DIFF_GT15C"],
            "pressure_out_of_range":reasons["PA_OUTSIDE_50_110KPA"],
            "pressure_jump":reasons["PA_30MIN_JUMP_GT5KPA"],
            "longwave_out_of_range":reasons["LW_OUTSIDE_60_800"],
            "TA_zero_VPD_plateau":reasons["ZERO_TA_VPD_PLATEAU_3HR"],
            "low_RH_positive_0to10":sum(reasons[x] for x in LOW),
            "top_review_years":";".join("%s:%d"%(k,v)
                                   for k,v in by_year.most_common(5)),
            "recommended_next_review":workstream(site),
            "gate_status":"HOLD_SCIENCE_NOT_APPROVED_FOR_DATM"
        })
        for reason,n in sorted(reasons.items()):
            category_records.append({"site":site,"flag":reason,"records":n})
        for (var,level,qc_name),n in sorted(qcount.items()):
            qc_records.append({"site":site,"variable":var,"triage":level,
                               "source_QC":qc_name,"records":n})
        for (bucket,qc_name,month),n in sorted(low_groups.items()):
            month_records.append({"site":site,"RH_category":bucket,
                                 "VPD_F_QC":qc_name,"month":month,"records":n})
        for level,n in sorted(pcounts.items()):
            priority_records.append({"site":site,"review_priority":level,
                                     "records":n})

    total_rows=sum(x["review_halfhours"] for x in site_records)
    if total_rows!=len({(r["site"],r["time"]) for site in SITES
                         for r in csv_rows(source/(site+"_flagged_review_times.csv"))}):
        raise RuntimeError("Unique site-time count mismatch")

    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage16_science_decisions_"+stamp)
    out.mkdir(parents=True,exist_ok=False)
    save(out/"site_gate_decision_matrix.csv",site_records,list(site_records[0]))
    save(out/"fullcycle_flag_counts_by_site.csv",category_records,
         ["site","flag","records"])
    save(out/"qc_provenance_by_triage.csv",qc_records,
         ["site","variable","triage","source_QC","records"])
    save(out/"low_positive_RH_by_month_and_VPD_QC.csv",month_records,
         ["site","RH_category","VPD_F_QC","month","records"])
    save(out/"disjoint_triage_counts.csv",priority_records,
         ["site","review_priority","records"])

    print("STAGE16 SUMMARY: 10/10 sites; Stage15 REVIEW halfhours=%d; episodes=%d"%
          (total_rows,len(episodes)))
    print("SOURCE REPORT:",source)
    for rec in site_records:
        print("  %-7s P0_physical=%5d P1_TA_PA=%5d P1_RH_lt1=%5d P2_RH_1to5=%5d P3_RH_5to10=%5d total=%5d"%
              (rec["site"],rec["P0_physical"],rec["P1_TA_PA"],
               rec["P1_positive_RH_lt1"],rec["P2_positive_RH_1to5"],
               rec["P3_positive_RH_5to10"],rec["review_halfhours"]))
    aud=next(x for x in site_records if x["site"]=="US-Aud")
    aud_qc=Counter()
    for r in month_records:
        if r["site"]=="US-Aud":aud_qc[r["VPD_F_QC"]]+=r["records"]
    print("US-Aud positive low RH VPD source QC:",dict(aud_qc))
    print("US-Aud flagged positive RH<10%:",aud["low_RH_positive_0to10"],
          "not a blanket repair count.")
    lp=next(x for x in site_records if x["site"]=="CA-LP1")
    print("CA-LP1 full-cycle TA vs ERA >15C:",
          lp["temp_vs_ERA_gt15C"],"; investigate clock/source representativeness.")
    print("CA-Man Stage14 provisional sensitivity residual EA<=0:",
          "ORIGINAL 561; ROUTINE_ONLY 253; ALL_PROPOSALS 105 (prior report only)")
    print("REPORT DIR:",out)
    print("GATE=HOLD. NO FORCING, DATM, SURFACE, CIME or Slurm changed.")
    print("Next: site-specific decisions including ZBOT and surface/PFT review.")


if __name__=="__main__":
    main()

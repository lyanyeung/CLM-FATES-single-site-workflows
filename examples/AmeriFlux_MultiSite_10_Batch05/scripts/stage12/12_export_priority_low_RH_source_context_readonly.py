#!/usr/bin/env python3
"""Batch05 Stage12 — immutable report-only native time-window review.

Read SHA-pinned original FLUXMET/FULLSET HH and existing Stage10 event ledger.
Export +/-3h native context for flagged priority events:
  229 mathematically-feasible but UNAPPROVED bracketed VPD trials,
  11 nonphysical trial interpolations,
  27 QC0/0 water-formula-negative measured-pair events,
  170 unusable ERA/tower-T humidity pairing events.
These groups may overlap: deduplicate source event time per site, but do NOT
interpret as approved repairs. No science/forcing/Stage10/source writes.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re

ROOT=Path(os.getenv("FLUXNET_SITES_ROOT",
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
SITES={
"US-UiD":("2008-2024_v1.3_r1","130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318"),
"US-UMB":("FULLSET_2007-2021_3-5","ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6"),
"US-UMd":("2007-2025_v1.3_r1","e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2"),
"US-Var":("2000-2025_v1.3_r1","664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2"),
"US-Vcm":("2007-2025_v1.3_r1","c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c"),
"US-Vcp":("2007-2025_v1.3_r1","eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42"),
"US-WCr":("1999-2025_v1.3_r1","f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506"),
"US-Whs":("2007-2025_v1.3_r1","653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca"),
"US-Wjs":("2007-2025_v1.3_r1","9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6"),
"US-Wkg":("2004-2025_v1.3_r1","f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829")}
TYPES=("BRACKETED_MATH_UNAPPROVED","BRACKETED_NONPHYSICAL",
       "MEASURED_QC00_NEGATIVE","ERA_PAIR_HOLD")
EXPECTED={"BRACKETED_MATH_UNAPPROVED":229,"BRACKETED_NONPHYSICAL":11,
          "MEASURED_QC00_NEGATIVE":27,"ERA_PAIR_HOLD":170}
ORIG=("TIMESTAMP_START","TA_F","VPD_F","RH","TA_F_QC","VPD_F_QC",
      "TA_F_MDS","VPD_F_MDS","TA_F_MDS_QC","VPD_F_MDS_QC",
      "TA_ERA","VPD_ERA")
CONTEXT=("site","target_time","target_reasons","offset_half_hours",
  "native_time","TA_F_C","VPD_F_hPa","RH_original","RH_water_pct",
  "TA_F_QC","VPD_F_QC","TA_F_MDS","VPD_F_MDS",
  "TA_F_MDS_QC","VPD_F_MDS_QC","TA_ERA","VPD_ERA",
  "at_target","at_left_anchor","at_right_anchor",
  "source_measured_QC00_physically_coherent")
TARGET=("site","target_time","priority_tags","source_class","RH_derived_pct",
        "RH_original","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
        "ERA_pair_physics","MDS_pair_physics","left_anchor",
        "right_anchor","unapproved_interpolated_VPD","decision")

def num(x):
    try:
        v=float(x)
        if math.isfinite(v) and v not in (-9999.,-6999.):
            return v
    except (TypeError,ValueError):
        pass
    return None

def es(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -80<=t<=60 else None

def stamped(s):
    if not re.fullmatch(r"\d{12}",s or ""): raise ValueError("invalid source time "+repr(s))
    return datetime.strptime(s,"%Y%m%d%H%M")

def sha(p):
    dig=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):dig.update(chunk)
    return dig.hexdigest()

def source(site,root):
    release,expected=SITES[site]
    d=root/site/"forcing"/"raw"/("AMF_"+site+"_FLUXNET_"+release)
    if not d.is_dir() or d.is_symlink():raise ValueError("missing/unsafe native source "+str(d))
    kind="FULLSET" if site=="US-UMB" else "FLUXMET"
    pattern=re.compile("AMF_"+re.escape(site)+"_FLUXNET_"+kind+r"_HH_.+[.]csv",re.I)
    ps=[p for p in d.iterdir() if pattern.fullmatch(p.name)]
    if len(ps)!=1 or ps[0].is_symlink() or not ps[0].is_file():
        raise ValueError("expected one regular native HH CSV "+site)
    p=ps[0]
    digest=sha(p)
    if digest!=expected: raise ValueError("native CSV SHA mismatch "+site+" "+digest)
    return p,digest

def reasons(row):
    status=row["interpolation_diagnostic"]
    ans=[]
    if status=="UNAPPROVED_MATH_FEASIBLE":
        ans.append(TYPES[0])
    elif status=="INTERPOLATION_NONPHYSICAL":
        ans.append(TYPES[1])
    elif status!="NO_BOTH_QC0_ANCHORS_WITHIN_3H":
        raise ValueError("unknown Stage10 interpolation status "+status)
    if row["TA_F_QC"]=="0" and row["VPD_F_QC"]=="0" and row["class"]=="NEGATIVE":
        ans.append(TYPES[2])
    if row["ERA_pair_physics"] in ("ERA_INTERNAL_NONPHYSICAL",
                                  "ERA_E_WITH_TOWER_T_NOT_FEASIBLE"):
        ans.append(TYPES[3])
    if row["SCIENCE_APPROVAL"]!="HOLD_NOT_APPROVED":
        raise ValueError("unexpected scientific approval in report")
    return ans

def pick_events(report_dir,site):
    path=report_dir/(site+"_low_RH_review.csv")
    if not path.is_file() or path.is_symlink():
        raise ValueError("missing/nonregular Stage10 report "+str(path))
    targets={}
    all_events=0
    reasons_count=Counter()
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=csv.DictReader(f)
        needed=("time","class","RH_derived_pct","TA_F_C","VPD_F_hPa","RH_original_pct",
                "TA_F_QC","VPD_F_QC","ERA_pair_physics","MDS_pair_physics",
                "left_measured_anchor_time","right_measured_anchor_time",
                "interpolated_measured_vpd_hPa","interpolation_diagnostic","SCIENCE_APPROVAL")
        if not set(needed).issubset(rows.fieldnames or []):
            raise ValueError("missing Stage10 report columns")
        for row in rows:
            all_events+=1
            when=row["time"]
            stamped(when)
            r=reasons(row)
            if not r: continue
            if when in targets: raise ValueError("duplicate selected Stage10 time "+site+" "+when)
            for key in r:reasons_count[key]+=1
            targets[when]={"row":row,"why":r}
    return targets,all_events,reasons_count

def measured_anchor(row):
    ta,vpd,rh=(num(row[k]) for k in ("TA_F","VPD_F","RH"))
    s=es(ta)
    if s is None or vpd is None:return False
    drh=100*(1-vpd/s)
    return (row["TA_F_QC"].strip()=="0" and row["VPD_F_QC"].strip()=="0"
            and 1<=drh<=100 and
            (rh is None or 0<=rh<=100 and abs(rh-drh)<=5))

def get_context(site,source_file,targets):
    window=defaultdict(list)
    for time,obj in targets.items():
        center=stamped(time)
        for offset in range(-6,7):
            neighbor=(center+timedelta(minutes=30*offset)).strftime("%Y%m%d%H%M")
            window[neighbor].append((time,offset))
    center_found=set()
    anchors_found=defaultdict(set)
    result=[]
    before=(source_file.stat().st_size,source_file.stat().st_mtime_ns)
    with source_file.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not set(ORIG).issubset(reader.fieldnames or []) or len(set(reader.fieldnames or []))!=len(reader.fieldnames or []):
            raise ValueError("source columns missing/nonunique for "+site)
        for row in reader:
            stamp=row["TIMESTAMP_START"]
            items=window.get(stamp)
            if not items:continue
            t,v,rh=(num(row[x]) for x in ("TA_F","VPD_F","RH"))
            sat=es(t)
            derive=100*(1-v/sat) if sat is not None and v is not None else None
            anchor_ok=measured_anchor(row)
            for target_time,offset in items:
                original=targets[target_time]["row"]
                at_center=(stamp==target_time)
                if at_center:
                    if target_time in center_found:
                        raise ValueError("duplicate native source event "+site+" "+stamp)
                    center_found.add(target_time)
                    if (t is None or v is None or
                        abs(t-float(original["TA_F_C"]))>0.002 or
                        abs(v-float(original["VPD_F_hPa"]))>0.002 or
                        row["TA_F_QC"].strip()!=original["TA_F_QC"] or
                        row["VPD_F_QC"].strip()!=original["VPD_F_QC"]):
                        raise ValueError("Stage10/source event center mismatch "+site+" "+stamp)
                left=original["left_measured_anchor_time"]
                right=original["right_measured_anchor_time"]
                if stamp==left and left:
                    if not anchor_ok:raise ValueError("left anchor not eligible "+site+" "+stamp)
                    if abs(v-float(original["left_measured_anchor_vpd"]))>0.002:
                        raise ValueError("left anchor VPD disagreement")
                    anchors_found[target_time].add("LEFT")
                if stamp==right and right:
                    if not anchor_ok:raise ValueError("right anchor not eligible "+site+" "+stamp)
                    if abs(v-float(original["right_measured_anchor_vpd"]))>0.002:
                        raise ValueError("right anchor VPD disagreement")
                    anchors_found[target_time].add("RIGHT")
                entry={"site":site,"target_time":target_time,
                       "target_reasons":"|".join(targets[target_time]["why"]),
                       "offset_half_hours":offset,"native_time":stamp,
                       "TA_F_C":row["TA_F"],"VPD_F_hPa":row["VPD_F"],
                       "RH_original":row["RH"],
                       "RH_water_pct":round(derive,6) if derive is not None else "",
                       "TA_F_QC":row["TA_F_QC"],"VPD_F_QC":row["VPD_F_QC"],
                       "TA_F_MDS":row["TA_F_MDS"],"VPD_F_MDS":row["VPD_F_MDS"],
                       "TA_F_MDS_QC":row["TA_F_MDS_QC"],
                       "VPD_F_MDS_QC":row["VPD_F_MDS_QC"],
                       "TA_ERA":row["TA_ERA"],"VPD_ERA":row["VPD_ERA"],
                       "at_target":int(at_center),
                       "at_left_anchor":int(bool(left and stamp==left)),
                       "at_right_anchor":int(bool(right and stamp==right)),
                       "source_measured_QC00_physically_coherent":int(anchor_ok)}
                result.append(entry)
    if before!=(source_file.stat().st_size,source_file.stat().st_mtime_ns):
        raise ValueError("native source file changed during read "+site)
    missing=set(targets)-center_found
    if missing:raise ValueError("source target centers missing "+site+" "+str(sorted(missing)[:4]))
    for stamp,obj in targets.items():
        if "BRACKETED_MATH_UNAPPROVED" in obj["why"] or "BRACKETED_NONPHYSICAL" in obj["why"]:
            if anchors_found[stamp]!={"LEFT","RIGHT"}:
                raise ValueError("bracket source anchors not reverified "+site+" "+stamp)
    return result

def as_targets(site,events):
    entries=[]
    for stamp,obj in sorted(events.items()):
        r=obj["row"]
        entries.append({"site":site,"target_time":stamp,
          "priority_tags":"|".join(obj["why"]),"source_class":r["class"],
          "RH_derived_pct":r["RH_derived_pct"],"RH_original":r["RH_original_pct"],
          "TA_F_C":r["TA_F_C"],"VPD_F_hPa":r["VPD_F_hPa"],
          "TA_F_QC":r["TA_F_QC"],"VPD_F_QC":r["VPD_F_QC"],
          "ERA_pair_physics":r["ERA_pair_physics"],
          "MDS_pair_physics":r["MDS_pair_physics"],
          "left_anchor":r["left_measured_anchor_time"],
          "right_anchor":r["right_measured_anchor_time"],
          "unapproved_interpolated_VPD":r["interpolated_measured_vpd_hPa"],
          "decision":"HOLD_MANUAL_REVIEW_ONLY"})
    return entries

def selftest():
    blank={"interpolation_diagnostic":"UNAPPROVED_MATH_FEASIBLE",
      "TA_F_QC":"0","VPD_F_QC":"0","class":"NEGATIVE",
      "ERA_pair_physics":"ERA_E_WITH_TOWER_T_NOT_FEASIBLE",
      "SCIENCE_APPROVAL":"HOLD_NOT_APPROVED"}
    assert set(reasons(blank))=={"BRACKETED_MATH_UNAPPROVED",
              "MEASURED_QC00_NEGATIVE","ERA_PAIR_HOLD"}
    blank["SCIENCE_APPROVAL"]="AUTO_APPROVED"
    try: reasons(blank);raise AssertionError("unapproved guard failed")
    except ValueError:pass
    anchor={"TA_F":"10","VPD_F":"2","RH":"83.71","TA_F_QC":"0","VPD_F_QC":"0"}
    assert measured_anchor(anchor)
    anchor["VPD_F"]="14"
    assert not measured_anchor(anchor)
    assert es(10)>12
    print("STAGE12 SELF-TEST PASS | priority overlap, approval hold,"
          " measured physical anchors; report-only")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--report-dir",type=Path)
    p.add_argument("--sites-root",type=Path,default=ROOT)
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    if args.self_test:selftest();return 0
    if args.report_dir is None or args.output_dir is None:
        p.error("both --report-dir and --output-dir required")
    root=args.sites_root.expanduser().resolve()
    d=args.report_dir.expanduser().resolve()
    output=args.output_dir.expanduser().resolve()
    if not d.is_dir():p.error("missing Stage10 report directory")
    if output.exists():p.error("output folder must not exist")
    if (output==root or root in output.parents or output in root.parents or
        output==d or d in output.parents or output in d.parents):
        p.error("Stage12 report output must be separate from original data and Stage10 reports")
    if not output.parent.exists():p.error("Stage12 output parent must exist")
    all_targets=[]
    all_context=[]
    total=Counter()
    original_count=0
    by_site={}
    for site,expected in SITES.items():
        targets,n,reasons_count=pick_events(d,site)
        original_count+=n
        for k,v in reasons_count.items():total[k]+=v
        native,digest=source(site,root)
        context=get_context(site,native,targets)
        entries=as_targets(site,targets)
        all_targets+=entries
        all_context+=context
        by_site[site]={"source_SHA256":digest,"original_low_RH_events":n,
                        "priority_unique_events":len(targets),
                        "priority_counts_with_overlap":dict(reasons_count),
                        "context_rows":len(context)}
        print("STAGE12_SITE",site,json.dumps(by_site[site],sort_keys=True),flush=True)
    if original_count!=1750 or any(total.get(k,0)!=v for k,v in EXPECTED.items()):
        raise ValueError("Stage11 cohort priority invariants mismatch; NO REPORT WRITES")
    if not (len(all_targets)<=sum(EXPECTED.values()) and len(all_context)>=len(all_targets)):
        raise ValueError("invalid context target aggregation")
    output.mkdir(exist_ok=False)
    def csvfile(name,columns,rows):
        with (output/name).open("x",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=columns)
            writer.writeheader();writer.writerows(rows)
    csvfile("stage12_priority_targets.csv",TARGET,all_targets)
    csvfile("stage12_original_native_context.csv",CONTEXT,all_context)
    with (output/"stage12_summary.json").open("x",encoding="utf-8") as f:
        json.dump({"source":"original SHA pinned native HH and unchanged Stage10 CSV",
          "water_saturation_formula":"6.112*exp(17.67*T/(T+243.5)) hPa",
          "time_labels":"native local standard time: unchanged",
          "decision":"ALL_CANDIDATES_UNAPPROVED",
          "original_low_RH_events":original_count,
          "priority_counts_with_overlap":dict(total),
          "priority_unique_events":len(all_targets),
          "context_rows":len(all_context),"sites":by_site},f,indent=2,sort_keys=True)
    print("STAGE12 SUMMARY sites=10/10 original_events=1750 "
          "priority_unique={} context_rows={} approved=0 reports={}".format(
             len(all_targets),len(all_context),output),flush=True)
    print("ONLY NEW REVIEW CSV/JSON FILES WRITTEN; NO SOURCE/STAGE10/FORCING/MODEL/SLURM")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

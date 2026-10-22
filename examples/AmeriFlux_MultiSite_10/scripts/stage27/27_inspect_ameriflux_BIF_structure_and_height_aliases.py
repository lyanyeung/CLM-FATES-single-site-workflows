#!/usr/bin/env python3
"""AmeriFlux Batch01 Stage27: diagnose why Stage26 found 0 TA/WS BIF heights.

Stage26's exact-match requirement for VAR_INFO_VARNAME=TA_F/WS_F may not
match a given AmeriFlux BIF release. This script reads the ten original pinned
*_BIF_*.csv without modifying them and inventories:
- actual column names and variable-group counts
- variable-information group and VARNAME value frequencies
- TA/WS aliases or indexed variables and available HEIGHT/DATE fields
- incomplete/bad/ambiguous metadata groups
- independent Measurement Height product availability is NOT presumed.

A BIF value or an alternative HEIGHT field does not automatically provide
the TA_F measurement reference height or justify historical backfilling.
Outputs: only small timestamped scientific source-inspection reports.
"""
from __future__ import annotations
import argparse
import csv
import re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]
RAW=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")

def load_rows(path,sep=","):
    with path.open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
        reader=csv.DictReader(f,delimiter=sep)
        if not reader.fieldnames:raise RuntimeError("Empty header: "+str(path))
        return reader.fieldnames,list(reader)

def pinned():
    _,entries=load_rows(BASE/"sites.tsv","\t")
    if len(entries)!=10 or len({x["site"] for x in entries})!=10:
        raise RuntimeError("10 distinct site releases expected")
    return entries

def locate(entry,root):
    folder=root/entry["site"]/"forcing"/"raw"/entry["package"]
    hits=sorted(p for p in folder.glob("*.csv") if "_BIF_" in p.name.upper())
    if len(hits)!=1:raise RuntimeError("Expected one exact original BIF CSV in "+str(folder))
    return hits[0]

def choose(vals):
    distinct=sorted({str(x).strip() for x in vals if str(x).strip()})
    return distinct[0] if len(distinct)==1 else ("<MULTIPLE>" if len(distinct)>1 else "")

def save(path,rows,fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)

def summarize(entry,path):
    site=entry["site"]
    head,rows=load_rows(path)
    needed={"VARIABLE","DATAVALUE","GROUP_ID"}
    if not needed.issubset(set(head)):
        raise RuntimeError(site+": BIF missing "+repr(needed-set(head)))
    groups=defaultdict(lambda:defaultdict(list))
    groups_count=Counter();variable_count=Counter()
    for r in rows:
        group=(str(r.get("VARIABLE_GROUP") or "").strip(),
               str(r.get("GROUP_ID") or "").strip())
        var=str(r.get("VARIABLE") or "").strip().upper()
        val=str(r.get("DATAVALUE") or "").strip()
        groups[group][var].append(val)
        groups_count[group[0]]+=1
        variable_count[var]+=1

    stems=("TA","T_AIR","AIR_TEMP","WS","WIND","RH","HUMID")
    cand=[]; exact_ta=exact_ws=0
    info_groups=0; height_groups=0; dates=0; alias=Counter()
    for (kind,groupid),fields in groups.items():
        info=choose(fields.get("VAR_INFO_VARNAME",[])).upper()
        height=choose(fields.get("VAR_INFO_HEIGHT",[]))
        when=choose(fields.get("VAR_INFO_DATE",[]))
        if "VAR_INFO_VARNAME" in fields:info_groups+=1
        if "VAR_INFO_HEIGHT" in fields:height_groups+=1
        if "VAR_INFO_DATE" in fields:dates+=1
        if info=="TA_F":exact_ta+=1
        if info=="WS_F":exact_ws+=1
        plausible=info and any(info.startswith(x) for x in stems)
        if plausible:alias[info]+=1
        if plausible or (("VAR_INFO_HEIGHT" in fields) and
                         any(k.startswith("VAR_INFO") for k in fields)):
            if plausible or len(cand)<100:
                cand.append(dict(site=site,group_id=groupid,
                    variable_group=kind,var_info_varname=info or "NOT_PRESENT",
                    var_info_height=height,
                    var_info_date=when,
                    var_info_unit=choose(fields.get("VAR_INFO_UNIT",[])),
                    var_info_height_unit=choose(fields.get("VAR_INFO_HEIGHT_UNIT",[])),
                    note=("TA_F_EXACT_METADATA" if info=="TA_F" else
                          "WS_F_EXACT_METADATA" if info=="WS_F" else
                          "ALIAS_NOT_VALIDATED_AS_ZBOT" if plausible else
                          "UNMATCHED_VAR_INFO_HEIGHT_RECORD")))
    if info_groups==0:
        classif="NO_VAR_INFO_VARNAME_IN_BIF"
    elif exact_ta==0:
        classif="HAS_VAR_INFO_BUT_NO_EXACT_TA_F"
    elif exact_ta>0:
        classif="EXACT_TA_F_PRESENT_RECHECK_STAGE26_REJECTED_HEIGHT_DATE"
    else:classif="UNEXPECTED"
    summary=dict(site=site,bif_filename=path.name,bif_rows=len(rows),
        header_fields=";".join(head),group_instances=len(groups),
        variable_info_groups=info_groups,
        height_field_groups=height_groups,
        date_field_groups=dates,TA_F_group_instances=exact_ta,
        WS_F_group_instances=exact_ws,
        possible_TA_WS_alias_names=";".join(sorted(alias)[:30]),
        diagnosis=classif,
        stage26_zero_height_is_proof_of_absence="NO")
    print("  %-7s rows=%6d groups=%5d info=%4d heights=%4d dates=%4d TA_exact=%3d WS_exact=%3d %s" %
          (site,len(rows),len(groups),info_groups,height_groups,dates,exact_ta,exact_ws,classif),
          flush=True)
    return summary,cand,groups_count,variable_count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    p.add_argument("--sites-root",type=Path,default=RAW)
    p.add_argument("--report-root",type=Path,default=REPORTS)
    args=p.parse_args()
    entries=pinned()
    files=[]
    for e in entries:
        path=locate(e,args.sites_root);files.append((e,path))
        print("CHECK OK %-7s %s" %(e["site"],path.name),flush=True)
    print("STAGE27 PREFLIGHT 10/10 exact source BIF files",flush=True)
    if args.check:
        print("CHECK ONLY. No reports or ZBOT outputs written.")
        return

    sums=[];candidates=[];topvars=[];topgroups=[]
    for entry,path in files:
        summ,possible,grp,vr=summarize(entry,path)
        sums.append(summ);candidates.extend(possible)
        for k,n in grp.most_common(40):
            topgroups.append(dict(site=entry["site"],variable_group=k,bif_rows=n))
        for k,n in vr.most_common(80):
            topvars.append(dict(site=entry["site"],bif_field=k,bif_rows=n))
    directory=args.report_root/("stage27_BIF_schema_diagnosis_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    directory.mkdir(parents=True,exist_ok=False)
    save(directory/"01_ten_site_BIF_structure.csv",sums,list(sums[0]))
    save(directory/"02_possible_TA_WS_sensor_aliases_and_heights.csv",candidates,
         ["site","group_id","variable_group","var_info_varname",
          "var_info_height","var_info_date","var_info_unit",
          "var_info_height_unit","note"])
    save(directory/"03_BIF_variable_group_frequency.csv",topgroups,
         ["site","variable_group","bif_rows"])
    save(directory/"04_BIF_VARIABLE_field_frequency.csv",topvars,
         ["site","bif_field","bif_rows"])
    print("STAGE27 SUMMARY: no_VAR_INFO=%d; missing_exact_TA=%d; exact_TA_present=%d"%
          (sum(x["diagnosis"]=="NO_VAR_INFO_VARNAME_IN_BIF" for x in sums),
           sum(x["diagnosis"]=="HAS_VAR_INFO_BUT_NO_EXACT_TA_F" for x in sums),
           sum(x["TA_F_group_instances"]>0 for x in sums)),flush=True)
    print("REPORT DIR:",directory,flush=True)
    print("READ ONLY. Stage26 zero-height results remain UNRESOLVED, not confirmed absence.")
    print("If official BIF lacks TA metadata, consult AmeriFlux Measurement Height"
          " (separate site-team-curated BASE metadata) and site papers with a"
          " release/provenance note. Never substitute EC tower height automatically.")

if __name__=="__main__":
    main()

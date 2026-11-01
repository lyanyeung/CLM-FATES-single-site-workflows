#!/usr/bin/env python3
"""OzFlux Stage08: original Stage07 native-year/flag audit into actionable review tables.

Report-only, never reads or writes source NetCDF. The time convention,
L6 flag provenance, station surface/PFT/soil/height remain science HOLDs.
No model forcing files, no gap-filling, no Slurm.

Output:
- stage08_year_reason_ledger.tsv (one record per source-year)
- stage08_contiguous_candidate_blocks.tsv (native calendar-year runs)
- stage08_source_qc_per_year.tsv (per variable and source-year fractions)
- stage08_review_summary.json
"""
from __future__ import annotations
import argparse
import collections
import csv
import json
from pathlib import Path
import sys

SITES = {"AU-ASM":2, "AU-Cow":1,"AU-Cpr":1,"AU-DaS":1,"AU-Dry":1,
         "AU-Gin":1,"AU-How":1,"AU-Stp":1,"AU-Tum":1}
MET=("Ta","SH","ps","Fsd","Fld","Ws","Precip")
TYPES=("qc0","qc10","qc50","qc400","qc410","qc420","qc430","qc440",
       "qc_other_finite","qc_missing")
VALID_STATUS={"STRUCTURAL_CANDIDATE_ONLY_QC_UNAPPROVED",
              "HOLD_FORCING_PHYSICS_OR_UNITS","TIME_LABEL_OR_COUNT_REVIEW"}
YEAR_HEADERS=("site","filename","year","status","reason_codes","time_expected",
              "time_actual","time_boundaries_complete","met_missing_cells",
              "met_physical_alarm_cells","missing_by_variable",
              "physical_alarms_by_variable","native_qc0_fraction",
              "native_qc410_fraction","native_qc420_fraction",
              "native_qc440_fraction","total_qc_nonzero_fraction",
              "unknown_native_qc_count","source_provenance_approved",
              "timezone_approved")
BLOCK_HEADERS=("site","filename","start_year","end_year","length_years",
               "total_native_records","native_qc0_fraction",
               "native_qc410_fraction","native_qc420_fraction",
               "native_qc440_fraction","status","science_approval")
QC_HEADERS=("site","filename","year","variable","records","missing",
            "physical_alarm","native_qc0","native_qc10","native_qc50",
            "native_qc410","native_qc420","native_qc430","native_qc440",
            "other_qc","qc_not_available","native_qc0_fraction",
            "source_provenance_approved")
SOURCE_YEAR_FIELDS=("site","filename","year")
MODEL_STATUS="STRUCTURAL_CANDIDATE_ONLY_QC_UNAPPROVED"

def table(path):
    with path.open(encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp, delimiter="\t"))

def num(raw, name, kind=int):
    val=raw.get(name)
    if val is None or val=="":
        raise ValueError("Missing required "+name+" in "+str(raw)[:200])
    return kind(val)

def truth(raw,name):
    value=raw.get(name)
    if value not in ("True","False"):
        raise ValueError("Invalid boolean "+name+": "+repr(value))
    return value=="True"

def check_manifest(path):
    x=table(path)
    keys=set()
    sitecount=dict.fromkeys(SITES,0)
    for r in x:
        site,filename=r.get("site"),r.get("filename")
        if site not in sitecount or not filename or not filename.endswith(".nc") or any(v in filename for v in ("/","\\","..")):
            raise ValueError("Unexpected source in manifest")
        if (site,filename) in keys:
            raise ValueError("Duplicate source in manifest")
        keys.add((site,filename))
        sitecount[site]+=1
    if len(x)!=10 or sitecount!=SITES:
        raise ValueError("Expected nine sites/ten files, AU-ASM has two")
    return keys

def year_status_input(rows, keys):
    idx={}
    for r in rows:
        key=(r.get("site"),r.get("filename"),num(r,"year"))
        if key[:2] not in keys or key in idx:
            raise ValueError("Unexpected or duplicate year status "+str(key))
        if r.get("candidate_status") not in VALID_STATUS:
            raise ValueError("Unknown Stage07 year code for "+str(key))
        idx[key]=r
    return idx

def var_qc_input(rows, years):
    idx={}
    for r in rows:
        key=(r.get("site"),r.get("filename"),num(r,"year"),r.get("variable"))
        if key[:3] not in years or key[3] not in MET or key in idx:
            raise ValueError("Unexpected or duplicate variable "+str(key))
        n=num(r,"records")
        counts={k:num(r,k) for k in TYPES}
        if any(v<0 for v in counts.values()) or sum(counts.values())!=n:
            raise ValueError("QC counters do not partition source records for "+str(key))
        if num(r,"missing")<0 or num(r,"missing")>n:
            raise ValueError("Bad missing source data count "+str(key))
        alarm_raw=r.get("physical_alarm")
        alarms=(None if alarm_raw in ("",None) else int(alarm_raw))
        if alarms is not None and (alarms<0 or alarms>n):
            raise ValueError("Bad alarm count "+str(key))
        idx[key]={"row":r,"qc":counts,"alarms":alarms}
    if len(idx)!=len(years)*len(MET):
        raise ValueError("Stage07 variable row count mismatch "+str(len(idx)))
    return idx

def contiguous(years):
    """Return disjoint maximal consecutive numeric-year ranges."""
    years=sorted(set(years))
    if not years:
        return []
    a=b=years[0]
    out=[]
    for y in years[1:]:
        if y==b+1:
            b=y
        else:
            out.append((a,b))
            a=b=y
    out.append((a,b))
    return out

def aggregate_qc(yearkeys, varidx):
    tally=collections.Counter()
    for site,file,year in yearkeys:
        for name in MET:
            tally.update(varidx[(site,file,year,name)]["qc"])
    total=sum(tally.values())
    fractions={}
    for name in ("qc0","qc410","qc420","qc440"):
        fractions[name]=round(tally[name]/total,6) if total else None
    known=sum(tally[k] for k in ("qc0","qc10","qc50","qc400","qc410",
                                "qc420","qc430","qc440"))
    nonzero=(known-tally["qc0"])+tally["qc_other_finite"]
    fractions["nonzero"]=round(nonzero/total,6) if total else None
    fractions["unknown_count"]=tally["qc_other_finite"]+tally["qc_missing"]
    return tally, fractions

def explain(r, relevant, missing, alarming):
    reasons=[]
    if not truth(r,"time_count_matches"):
        reasons.append("NATIVE_YEAR_COUNT_MISMATCH")
    if not truth(r,"native_label_boundaries_match"):
        reasons.append("NATIVE_YEAR_BOUNDARY_INCOMPLETE")
    if missing:
        reasons.append("MET_MISSING")
    if alarming:
        reasons.append("MET_BROAD_PHYSICS_ALARM")
    if any(x["alarms"] is None for x in relevant.values()):
        reasons.append("MET_UNITS_NOT_PHYSICALLY_SCREENED")
    if not reasons:
        reasons=["STRUCTURAL_ONLY_QC_PROVENANCE_HOLD"]
    status=r["candidate_status"]
    if status==MODEL_STATUS and reasons!=["STRUCTURAL_ONLY_QC_PROVENANCE_HOLD"]:
        raise ValueError("Stage07 candidate has unexplained source/physics condition "+repr(r))
    if status=="TIME_LABEL_OR_COUNT_REVIEW" and (
            "NATIVE_YEAR_COUNT_MISMATCH" not in reasons and
            "NATIVE_YEAR_BOUNDARY_INCOMPLETE" not in reasons):
        raise ValueError("Stage07 time REVIEW does not correspond to time counts/boundaries")
    if status=="HOLD_FORCING_PHYSICS_OR_UNITS" and not any(x in reasons for x in (
            "MET_MISSING","MET_BROAD_PHYSICS_ALARM","MET_UNITS_NOT_PHYSICALLY_SCREENED")):
        raise ValueError("Stage07 physics HOLD has no identified physics reason")
    return reasons

def generate(manifest, years, variables, source_json):
    keyset=check_manifest(manifest)
    with source_json.open(encoding="utf-8") as h:
        source=json.load(h)
    if source.get("original_files_checked")!=10 or source.get("science_approval") is not False:
        raise ValueError("Stage07 source provenance report is incomplete or not explicitly unapproved")
    rawyears=table(years)
    rawvars=table(variables)
    yidx=year_status_input(rawyears,keyset)
    varidx=var_qc_input(rawvars,yidx)
    source_years=source.get("native_year_summary",[])
    jsonkeys={(r["site"],r["filename"],int(r["year"])) for r in source_years}
    if jsonkeys!=set(yidx) or len(source_years)!=len(yidx):
        raise ValueError("Stage07 JSON/year tables not identical in source-year membership")
    # Compare important status fields, not just the matching keys.
    for j in source_years:
        key=(j["site"],j["filename"],int(j["year"]))
        r=yidx[key]
        if j["candidate_status"]!=r["candidate_status"]:
            raise ValueError("Stage07 JSON/year status mismatch for "+str(key))

    ledger=[]
    bysource=collections.defaultdict(list)
    for (site,filename,year),r in sorted(yidx.items()):
        relevant={v:varidx[(site,filename,year,v)] for v in MET}
        miss={v:num(relevant[v]["row"],"missing") for v in MET}
        alarms={v:relevant[v]["alarms"] for v in MET}
        missing=sum(miss.values())
        alarm_total=sum(x or 0 for x in alarms.values())
        if missing!=num(r,"missing_met_rows_across_fields") or alarm_total!=num(r,"physical_alarm_met_rows_across_fields"):
            raise ValueError("Stage07 mismatch between per-year and per-variable sums "+str(year))
        rowkeys=[(site,filename,year)]
        tally,f=aggregate_qc(rowkeys,varidx)
        reasons=explain(r,relevant,missing,alarm_total)
        summary={
            "site":site,"filename":filename,"year":year,
            "status":r["candidate_status"],
            "reason_codes":"|".join(reasons),
            "time_expected":num(r,"expected_count"),
            "time_actual":num(r,"native_year_count"),
            "time_boundaries_complete":truth(r,"native_label_boundaries_match"),
            "met_missing_cells":missing,
            "met_physical_alarm_cells":alarm_total,
            "missing_by_variable":";".join(f"{k}:{v}" for k,v in miss.items() if v),
            "physical_alarms_by_variable":";".join(f"{k}:{v}" for k,v in alarms.items() if v),
            "native_qc0_fraction":f["qc0"],
            "native_qc410_fraction":f["qc410"],
            "native_qc420_fraction":f["qc420"],
            "native_qc440_fraction":f["qc440"],
            "total_qc_nonzero_fraction":f["nonzero"],
            "unknown_native_qc_count":f["unknown_count"],
            "source_provenance_approved":False,
            "timezone_approved":False,
        }
        ledger.append(summary)
        bysource[(site,filename)].append(summary)

    qcout=[]
    for (site,filename,year,variable),d in sorted(varidx.items()):
        r=d["row"]
        cnt=d["qc"]
        n=num(r,"records")
        qcout.append({
            "site":site,"filename":filename,"year":year,"variable":variable,
            "records":n,"missing":num(r,"missing"),"physical_alarm":d["alarms"],
            "native_qc0":cnt["qc0"],"native_qc10":cnt["qc10"],
            "native_qc50":cnt["qc50"],
            "native_qc410":cnt["qc410"],"native_qc420":cnt["qc420"],
            "native_qc430":cnt["qc430"],"native_qc440":cnt["qc440"],
            "other_qc":cnt["qc_other_finite"]+cnt["qc400"],
            "qc_not_available":cnt["qc_missing"],
            "native_qc0_fraction":round(cnt["qc0"]/n,6) if n else None,
            "source_provenance_approved":False,
        })

    blocks=[]
    for (site,filename),records in sorted(bysource.items()):
        good={int(r["year"]) for r in records if r["status"]==MODEL_STATUS}
        summary={int(r["year"]):r for r in records}
        for begin,end in contiguous(good):
            keys=[(site,filename,y) for y in range(begin,end+1)]
            _,f=aggregate_qc(keys,varidx)
            blocks.append({
                "site":site,"filename":filename,"start_year":begin,
                "end_year":end,"length_years":end-begin+1,
                "total_native_records":sum(summary[y]["time_actual"] for y in range(begin,end+1)),
                "native_qc0_fraction":f["qc0"],
                "native_qc410_fraction":f["qc410"],
                "native_qc420_fraction":f["qc420"],
                "native_qc440_fraction":f["qc440"],
                "status":"CONTIGUOUS_NATIVE_STRUCTURAL_ONLY",
                "science_approval":False,
            })
    blocks.sort(key=lambda x:(-x["length_years"],x["site"],x["start_year"]))
    reasoncounts=collections.Counter()
    for x in ledger:
        for reason in x["reason_codes"].split("|"):
            reasoncounts[reason]+=1
    candidatecount=sum(x["status"]==MODEL_STATUS for x in ledger)
    if candidatecount!=sum(x["length_years"] for x in blocks):
        raise AssertionError("Candidate-year run lengths do not sum to candidate-year rows")
    return {
        "stage":"OzFlux Stage08 year gaps/QC provenance triage",
        "original_source_opened":False,
        "source_science_approval":False,
        "timezone_or_timestamp_semantics_approved":False,
        "model_submission_authorised":False,
        "native_year_rows":len(ledger),
        "structural_candidate_years":candidatecount,
        "review_hold_years":len(ledger)-candidatecount,
        "reason_counts_nonexclusive":dict(reasoncounts),
        "longest_structural_blocks":blocks[:15],
        "year_counts_by_source":[
            {"site":key[0],"filename":key[1],
             "total":len(rows),
             "candidates":sum(r["status"]==MODEL_STATUS for r in rows),
             "hold":sum(r["status"]!=MODEL_STATUS for r in rows)}
            for key,rows in sorted(bysource.items())],
        "important_note":"QC0 does not prove measured source; SOURCE/UTC/PFT/SOIL/ZBOT are independent gates",
    }, ledger, blocks, qcout

def write_table(path, headers, rows):
    with path.open("w",encoding="utf-8",newline="") as fp:
        writer=csv.DictWriter(fp,fieldnames=headers,delimiter="\t",extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def selftest():
    assert contiguous([2015,2016,2018,2017,2022,2025,2024])==[
        (2015,2018),(2022,2022),(2024,2025)]
    d={k:0 for k in TYPES}
    d.update({"qc0":10,"qc420":5,"qc440":5})
    assert sum(d.values())==20
    assert explain({
        "time_count_matches":"True","native_label_boundaries_match":"True",
        "candidate_status":MODEL_STATUS
    },{"Fsd":{"alarms":0},"Ta":{"alarms":0}},0,0)==["STRUCTURAL_ONLY_QC_PROVENANCE_HOLD"]
    print("STAGE08 SELF-TEST PASS: exact contiguous-year blocks, hold reason taxonomy; NO SOURCE ACCESS")

def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return 0
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",required=True,type=Path)
    parser.add_argument("--stage07",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    source=args.stage07.resolve()
    out=args.out.resolve()
    if args.out.is_symlink() or out==source or source in out.parents:
        raise ValueError("Cannot overwrite Stage07 or its nested files")
    if out.exists():
        raise FileExistsError("Choose a fresh timestamped Stage08 directory")
    report,year_rows,blocks,qcout=generate(
        args.manifest,
        source/"stage07_year_status.tsv",
        source/"stage07_year_variable_qc.tsv",
        source/"stage07_native_year_provenance.json",
    )
    out.mkdir(parents=True)
    (out/"stage08_review_summary.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    write_table(out/"stage08_year_reason_ledger.tsv",YEAR_HEADERS,year_rows)
    write_table(out/"stage08_contiguous_candidate_blocks.tsv",BLOCK_HEADERS,blocks)
    write_table(out/"stage08_source_qc_per_year.tsv",QC_HEADERS,qcout)
    print("STAGE08 YEAR_TRIAGE",report["native_year_rows"],"YEARS",
          report["structural_candidate_years"],"STRUCTURAL_CANDIDATE",
          report["review_hold_years"],"REVIEW_HOLD")
    print("YEAR_HOLD_REASONS_NONEXCLUSIVE",report["reason_counts_nonexclusive"])
    for row in blocks[:12]:
        print("BLOCK",row["site"],row["filename"],row["start_year"],"-",
              row["end_year"],"YEARS",row["length_years"],
              "QC0_FRACTION_UNAPPROVED",row["native_qc0_fraction"])
    print("REPORT_DIR",out)
    print("SCIENCE APPROVAL FALSE; ORIGINAL NETCDF NEVER OPENED; NO FORCING/JOBS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

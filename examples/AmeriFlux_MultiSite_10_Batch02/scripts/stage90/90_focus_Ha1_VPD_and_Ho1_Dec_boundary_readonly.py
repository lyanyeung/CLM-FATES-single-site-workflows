#!/usr/bin/env python3
"""Batch02 Stage90: focus the last source decisions, no forcing/model writes.

Use SHA-verified original Stage88 24 QC0 and 274 Ho1 non-QC0 source records.
Cross-check raw native neighbor values for all 24 QC0 changed variables;
show Ha1 VPD/T physics context; split anomalous Ho1 December gap by
source TA_F versus TA_ERA and inspect first *actual* 2001 QC0 temperature
following the year-end episode. Evidence, not permission to repair.
"""
import argparse
import csv
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from uuid import uuid4

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S07 = ROOT / "qcv5_native_trial_20261022T010124Z_dfae01c2"
S88 = ROOT / "reports/stage88_Batch02_exact_manual_science_review_20261026T004817Z_d9022864"
EDITS = "24_original_QC0_modified_variable_records_REVIEW.csv"
HOLDS = "274_Ho1_2000_nonQC0_temperature_neighbor_context_REVIEW.csv"
FIVE = {"US-BZS":30, "US-CMW":30, "US-Ha1":60, "US-Ho2":30, "US-Ho3":30}
EXPECTED = {"US-BZS":1, "US-CMW":2, "US-Ha1":2, "US-Ho2":19, "US-Ho3":0}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def rows(path):
    with path.open(newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))

def num(x):
    try:
        x=float(x)
        return x if math.isfinite(x) and x>-9990 else None
    except (TypeError,ValueError): return None

def dt(x):
    return datetime.strptime(str(x).split(".")[0],"%Y%m%d%H%M")

def stamp(x):
    return x.strftime("%Y%m%d%H%M")

def iso(x):
    return datetime.fromisoformat(x)

def fmt(x):
    return ("NA" if x is None else f"{x:.2f}")

def preflight():
    m88=json.loads((S88/"review_summary.json").read_text())
    for n in (EDITS,HOLDS):
        if sha(S88/n)!=m88["output_sha256"][n]:
            raise ValueError("Stage88 review SHA mismatch "+n)
    ed=rows(S88/EDITS)
    ho=rows(S88/HOLDS)
    if len(ed)!=24 or len(ho)!=274 or Counter(r["site"] for r in ed)!=Counter({k:v for k,v in EXPECTED.items() if v}):
        raise ValueError("Stage88 exact decision population drift")
    if any(num(r["native_TA_F_original_QC"])==0 for r in ho):
        raise ValueError("Ho1 held record changed to measured QC0")
    if len({r["tower_local_start"] for r in ho})!=274:
        raise ValueError("Ho1 held native timestamp duplicate")
    m07=json.loads((S07/"exact_input_manifest.json").read_text())
    psha={str(Path(k).resolve()):v for k,v in m07["input_sha256"].items()}
    sites={r["site"]:r for r in m07["sites"]}
    if set(sites)!=set(FIVE)|{"US-EML","US-GLE","US-Ho1","US-ICh","US-ICt"}:
        raise ValueError("Batch02 Stage07 source site census drift")
    for s in set(FIVE)|{"US-Ho1"}:
        p=Path(sites[s]["primary"]).resolve()
        if str(p) not in psha:raise ValueError("Original raw product not pinned: "+s)
        print("VERIFY ORIGINAL PRIMARY SHA",s,flush=True)
        if sha(p)!=psha[str(p)]:raise ValueError("Original primary source drift: "+s)
    return ed,ho,sites

def source_context(ed,sites):
    wanted={s:set() for s in FIVE if EXPECTED[s]}
    for r in ed:
        event=iso(r["time"])
        step=FIVE[r["site"]]
        for d in (-2,-1,0,1,2):
            wanted[r["site"]].add(stamp(event+timedelta(minutes=d*step)))
    extracts={}
    for site, times in wanted.items():
        p=Path(sites[site]["primary"])
        found={}
        with p.open(newline="",encoding="utf8") as fh:
            reader=csv.DictReader(fh)
            need={"TIMESTAMP_START","TA_F","VPD_F","LW_IN_F"}
            if not need<=set(reader.fieldnames or []):
                raise ValueError("Primary release missing required tower variables: "+site)
            for row in reader:
                key=row["TIMESTAMP_START"].strip().split(".")[0]
                if key in times:
                    if key in found:raise ValueError("Duplicate original native time: "+site+" "+key)
                    found[key]={k:row.get(k,"") for k in (
                        "TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC","VPD_ERA",
                        "LW_IN_F","LW_IN_F_QC","LW_IN_ERA")}
        if not times<=set(found):
            raise ValueError("Missing expected original native neighbors: "+site+" "+str(sorted(times-set(found))[:5]))
        extracts[site]=found
    output=[]
    for x in sorted(ed,key=lambda z:(z["site"],z["time"],z["variable"])):
        site=x["site"];step=FIVE[site];target=iso(x["time"]);key=stamp(target)
        origin=extracts[site][key];var=x["variable"]
        original=num(x["original_value"])
        if original is None or num(origin.get(var)) is None or abs(num(origin[var])-original)>0.00001:
            raise ValueError("Changed QC0 original value differs from pinned primary: "+site+" "+key)
        qc=num(origin.get(var+"_QC"))
        if qc!=0:raise ValueError("Original QC0 classification mismatch: "+site+" "+key)
        enriched=dict(x)
        enriched["native_minutes"]=step
        for j,label in ((-2,"before2"),(-1,"before1"),(0,"at"),(1,"after1"),(2,"after2")):
            rr=extracts[site][stamp(target+timedelta(minutes=j*step))]
            for k in (var,var+"_QC","TA_F","TA_F_QC","TA_ERA","VPD_F","VPD_F_QC","VPD_ERA"):
                enriched[label+"_"+k]=rr.get(k,"")
        originprev=extracts[site][stamp(target-timedelta(minutes=step))]
        originnext=extracts[site][stamp(target+timedelta(minutes=step))]
        enriched["prev_original_target_variable"]=originprev.get(var,"")
        enriched["next_original_target_variable"]=originnext.get(var,"")
        output.append(enriched)
    return output

def ho1_future_boundary(sites):
    p=Path(sites["US-Ho1"]["primary"])
    first_2001=None
    first_QC0=None
    preview=[]
    with p.open(newline="",encoding="utf8") as fh:
        reader=csv.DictReader(fh)
        need={"TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","VPD_F"}
        if not need<=set(reader.fieldnames or []):
            raise ValueError("Original Ho1 primary missing year boundary fields")
        for r in reader:
            when=r["TIMESTAMP_START"].strip().split(".")[0]
            if "200101010000" <= when <= "200101022330":
                preview.append({k:r.get(k,"") for k in need})
            if when>="200101010000" and first_2001 is None:
                first_2001={k:r.get(k,"") for k in need}
            if when>="200101010000" and first_QC0 is None and num(r.get("TA_F_QC"))==0:
                first_QC0={k:r.get(k,"") for k in need}
            if when>"200101022330" and first_QC0 is not None:
                break
    return first_2001,first_QC0,preview

def contiguous(data):
    out=[];part=[]
    for r in data:
        when=dt(r["tower_local_start"])
        if part and when-dt(part[-1]["tower_local_start"])!=timedelta(minutes=30):
            out.append(part);part=[]
        part.append(r)
    if part:out.append(part)
    return out

def ho1_analysis(ho):
    dec=[r for r in ho if r["tower_local_start"]>="200012270900"]
    apr=[r for r in ho if r["tower_local_start"]<"200012270900"]
    if len(apr)!=52 or len(dec)!=222:raise ValueError("Ho1 original non-QC0 episode census changed")
    result=[]
    for r in dec:
        d=num(r.get("native_TA_F_original_preserved_C"))
        era=num(r.get("native_T_ERA"))
        z=dict(r)
        z["abs_native_T_minus_TA_ERA_C"]=abs(d-era) if d is not None and era is not None else ""
        z["ERA_discrepancy_gt8C"]=bool(d is not None and era is not None and abs(d-era)>8)
        z["ERA_discrepancy_gt12C"]=bool(d is not None and era is not None and abs(d-era)>12)
        result.append(z)
    high=[r for r in result if r["ERA_discrepancy_gt8C"]]
    very=[r for r in result if r["ERA_discrepancy_gt12C"]]
    groups=contiguous(high)
    print("\n=== Ho1 December 2000 | ORIGINAL NON-QC0 temperature ===")
    print("APR episode: 52 records; DEC episode: 222 records, all 274 source values preserved")
    print("December source T vs source TA_ERA: >8C",len(high),">12C",len(very))
    print(">8C contiguous periods:")
    for g in groups:
        print("  ",g[0]["tower_local_start"],g[-1]["tower_local_start"],
              "HH",len(g),"peak delta C",
              fmt(max(float(x["abs_native_T_minus_TA_ERA_C"]) for x in g)))
    print("Top 20 absolute T discrepancies:")
    for r in sorted(result,key=lambda z:(-float(z["abs_native_T_minus_TA_ERA_C"]) if z["abs_native_T_minus_TA_ERA_C"]!="" else float("inf")))[:20]:
        print("  ",r["tower_local_start"],"QC",r["native_TA_F_original_QC"],
              "TA_F",r["native_TA_F_original_preserved_C"],"TA_ERA",r["native_T_ERA"],
              "delta",fmt(r["abs_native_T_minus_TA_ERA_C"]))
    return result,len(high),len(very)

def write_csv(path,records):
    if not records:raise ValueError("Empty diagnostic CSV")
    keys=list(records[0])
    with path.open("w",newline="",encoding="utf8") as fh:
        writer=csv.DictWriter(fh,fieldnames=keys,extrasaction="ignore")
        writer.writeheader();writer.writerows(records)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert dt("200012312330")+timedelta(minutes=30)==dt("200101010000")
        assert len(contiguous([{"tower_local_start":x} for x in ("200004190930","200004191000","200004191130")]))==1
        assert fmt(None)=="NA"
        print("STAGE90 SELF-TEST PASS | native HH/HR source neighborhood and cross-year QC0 boundary; no writes")
        return
    if not a.audit:p.error("Use --audit or --self-test")
    ed,ho,sites=preflight()
    ctx=source_context(ed,sites)
    print("\n=== ALL 24 ORIGINAL QC0 CHANGES + NEAREST ORIGINAL NEIGHBORS ===")
    print("site | time | variable | original | ERA | final | previous original | next original | reason")
    for r in ctx:
        print(" | ".join(str(r[k]) for k in ("site","time","variable","original_value","era_reference","final_value",
                  "prev_original_target_variable","next_original_target_variable","reason")))
    print("\n=== 2 Ha1 VPD edits | native hourly T and humidity neighbors ===")
    for r in ctx:
        if r["site"]!="US-Ha1":continue
        print("Ha1",r["time"],"tower VPD",r["original_value"],"candidate",r["final_value"],"ERA",r["era_reference"])
        for label in ("before2","before1","at","after1","after2"):
            print(" ",label,"tower T",r.get(label+"_TA_F"),"TQC",r.get(label+"_TA_F_QC"),
                  "source VPD",r.get(label+"_VPD_F"),"VPDQC",r.get(label+"_VPD_F_QC"),
                  "source ERA T",r.get(label+"_TA_ERA"),"source ERA VPD",r.get(label+"_VPD_ERA"))
    dec,gt8,gt12=ho1_analysis(ho)
    a2001,first_qc0,first48=ho1_future_boundary(sites)
    print("\n=== Ho1 2000 Dec31 -> 2001 Jan native source boundary ===")
    print("FIRST 2001 ORIGINAL row",a2001)
    print("FIRST NEXT ORIGINAL QC0 T in 2001+",first_qc0)
    if first_qc0 is not None:
        nxt=dt(first_qc0["TIMESTAMP_START"])
        print("LAST_2000_HOLD_to_first_2001_QC0_hours",(nxt-dt("200012312330")).total_seconds()/3600)
    else:
        print("NO FOLLOWING MEASURED QC0 FOUND in source through file end")
    print("FIRST 2001 48h source row count",len(first48),"first 4",first48[:4])
    out=ROOT/"reports"/("stage90_Ha1_VPD_Ho1_Dec_source_context_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Source diagnostics only; not reviewed model forcing.\n")
    one=out/"24_QC0_original_neighborhoods.csv"
    two=out/"222_Ho1_Dec_nonQC0_raw_vs_ERA_T.csv"
    three=out/"Ho1_2001_first_48h_original.csv"
    write_csv(one,ctx);write_csv(two,dec)
    if first48:write_csv(three,first48)
    report={"source_report":str(S88),"source_report_manifest_sha":sha(S88/"review_summary.json"),
        "stage07_manifest_sha":sha(S07/"exact_input_manifest.json"),
        "original_QC0_edits":24,"original_Ho1_nonQC0_HH":274,
        "April_nonQC0_HH":52,"December_nonQC0_HH":222,
        "December_T_vs_TA_ERA_gt8C_HH":gt8,"December_T_vs_TA_ERA_gt12C_HH":gt12,
        "first_2001_native_source_record":a2001,
        "first_2001_or_later_measured_QC0_record":first_qc0,
        "previously_approved_17294_QC0_1068_humidity_32_VPD_untouched":True,
        "all_work_readonly_to_origins":True,
        "output_sha256":{x.name:sha(x) for x in (one,two,three) if x.exists()}}
    (out/"stage90_summary.json").write_text(json.dumps(report,indent=2)+"\n")
    marker.unlink()
    print("STAGE90 AUDIT PASS | 24 original QC0 changes with native neighbor source; 222 Ho1 December original-vs-ERA and cross-year actual source QC0")
    print("REPORT",out)
    print("NO SOURCE/FORCING/NETCDF/CIME/SLURM WRITES")
if __name__=="__main__":
    main()

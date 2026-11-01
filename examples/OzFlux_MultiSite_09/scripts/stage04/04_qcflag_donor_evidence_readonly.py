#!/usr/bin/env python3
"""OzFlux Stage04: source QC code catalogue, optional same-unit donor evidence.

Forensic, read-only: does NOT approve QC codes, merge sensors, alter times,
impute missing values, create DATM, or submit any Slurm/model jobs.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
from pathlib import Path
import re
import sys

import netCDF4
import numpy as np

SITE_COUNTS = {
    "AU-ASM": 2, "AU-Cow": 1, "AU-Cpr": 1, "AU-DaS": 1,
    "AU-Dry": 1, "AU-Gin": 1, "AU-How": 1, "AU-Stp": 1, "AU-Tum": 1,
}
MET = ("Ta","SH","ps","Fsd","Fld","Ws","Precip")
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")


def load_manifest(path):
    with path.open(encoding="utf-8-sig",newline="") as h:
        reader=csv.DictReader(h,delimiter="\t")
        if reader.fieldnames != ["site","filename"]:
            raise ValueError("Bad manifest columns")
        rows=list(reader)
    counts={key:0 for key in SITE_COUNTS}
    seen=set()
    for row in rows:
        site,name=row["site"],row["filename"]
        if site not in counts or not name.endswith(".nc") or any(x in name for x in ("/","\\","..")):
            raise ValueError("Unexpected source entry "+str(row))
        if (site,name) in seen:
            raise ValueError("Duplicate manifest entry "+str(row))
        counts[site]+=1
        seen.add((site,name))
    if counts!=SITE_COUNTS or len(rows)!=10:
        raise ValueError("Nine sites and ten exact files required")
    return rows


def text_attr(v,name):
    if name not in v.ncattrs():
        return None
    value=v.getncattr(name)
    if isinstance(value,np.ndarray):
        value=value.tolist()
    return str(value)[:500]


def units_key(text):
    return re.sub(r"[\s_]+","",(text or "").lower())


def time_data(v,time_dim,n):
    if not np.issubdtype(v.dtype,np.number):
        return None
    if v.dimensions.count(time_dim)!=1:
        return None
    if len(v.shape)<1 or v.shape[v.dimensions.index(time_dim)]!=n:
        return None
    if any(size!=1 for i,size in enumerate(v.shape) if v.dimensions[i]!=time_dim):
        return None
    arr=np.ma.asarray(v[:],dtype=np.float64).filled(np.nan).reshape(-1)
    return arr if len(arr)==n else None


def valid_met(arr):
    return np.isfinite(arr)&(arr>-9990)


def unit_same(a,b):
    return bool(a and b and units_key(a)==units_key(b))


def candidate_names(ds,main):
    # Restrict exclusions to suffix tokens. Never search the entire name for
    # "sd": Fsd_1 and Fsd_7m both legitimately contain that substring!
    # Same-prefix sensor candidates are evidence only, not authorised substitutes.
    p=main.lower()+"_"
    blocked={"qc","qcflag","flag","coverage","status","percent","source",
             "method","gap","range","sd","variance","sdev","std","se"}
    out=[]
    for name in ds.variables:
        z=name.lower()
        if not z.startswith(p):
            continue
        suffix=z[len(p):]
        if not suffix:
            continue
        if any(token in blocked for token in suffix.split("_")):
            continue
        out.append(name)
    return out[:25]


def qc_hist(q):
    if q is None:
        return None
    good=q[np.isfinite(q)]
    vals,counts=np.unique(good,return_counts=True)
    return {"n":int(len(q)), "nonfinite":int(len(q)-len(good)),
            "codes":{str(float(v)):int(c) for v,c in zip(vals,counts)}}


def get_flag_catalogue(ds):
    result={}
    for name in ds.ncattrs():
        if re.fullmatch(r"Flag\d+",name,re.IGNORECASE):
            result[name]=str(ds.getncattr(name))[:500]
    return result


def all_main_qc(ds,variable,dim,n):
    qname=variable+"_QCFlag"
    if qname not in ds.variables:
        return {"qc_name":None,"histogram":None}
    v=ds.variables[qname]
    q=time_data(v,dim,n)
    return {"qc_name":qname,"histogram":qc_hist(q),
            "flag_values":text_attr(v,"flag_values"),
            "flag_meanings":text_attr(v,"flag_meanings")}


def nearby_text(ds,base,indices):
    data={}
    for name in ("Ta","SH","ps","Fsd","Fld","Ws"):
        if name not in ds.variables:
            continue
        v=ds.variables[name]
        dim=ds.variables["time"].dimensions[0]
        n=ds.variables["time"].shape[0]
        arr=time_data(v,dim,n)
        if arr is None:
            continue
        data[name]={"units":text_attr(v,"units"),
                    "values":{str(i):float(arr[i]) if np.isfinite(arr[i]) else None for i in indices}}
        qname=name+"_QCFlag"
        if qname in ds.variables:
            qa=time_data(ds.variables[qname],dim,n)
            if qa is not None:
                data[name]["qc"]={str(i):float(qa[i]) if np.isfinite(qa[i]) else None for i in indices}
    return data


def audit_one(ds,site,fname,events):
    dim=ds.variables["time"].dimensions[0]
    n=len(ds.variables["time"])
    catalogue=get_flag_catalogue(ds)
    source={"site":site,"filename":fname,"records":n,
            "global_flag_meanings":catalogue,
            "timezone_attrs":{name:text_attr(ds,name) for name in ds.ncattrs()
                              if "time_zone" in name.lower() or "timezone" in name.lower()
                              or "time_step" in name.lower() or "time_coverage" in name.lower()},
            "qc_summary":{}, "candidate_donors":[], "spot_checks":[]}
    for key in MET:
        if key not in ds.variables:
            source["qc_summary"][key]={"missing_main_field":True}
            continue
        main=ds.variables[key]
        source["qc_summary"][key]=all_main_qc(ds,key,dim,n)
        relevant=[e for e in events if e["variable"]==key and e["event_type"]=="MISSING"]
        if not relevant:
            continue
        pieces=[]
        for e in relevant:
            lo=int(e["first_index"]);hi=int(e["last_index"])
            if hi>=n or lo<0 or hi<lo:
                raise ValueError("Stage03 interval indices outside source for "+site+" "+fname)
            pieces.append(np.arange(lo,hi+1,dtype=np.int64))
        ix=np.unique(np.concatenate(pieces))
        u_main=text_attr(main,"units")
        for donor_name in candidate_names(ds,key):
            alt=ds.variables[donor_name]
            u_alt=text_attr(alt,"units")
            result={"site":site,"filename":fname,"target_variable":key,
                    "target_missing_rows":len(ix),
                    "candidate":donor_name,"main_units":u_main,
                    "candidate_units":u_alt,"same_units":unit_same(u_main,u_alt),
                    "candidate_height":text_attr(alt,"height"),
                    "candidate_long_name":text_attr(alt,"long_name"),
                    "interpretation":"DIAGNOSTIC_ONLY_NOT_APPROVED"}
            if not result["same_units"]:
                result["decision"]="HOLD_INCOMPATIBLE_OR_UNDOCUMENTED_UNITS"
                source["candidate_donors"].append(result)
                continue
            arr=time_data(alt,dim,n)
            if arr is None:
                result["decision"]="HOLD_SHAPE_OR_NONNUMERIC"
                source["candidate_donors"].append(result)
                continue
            flagname=donor_name+"_QCFlag"
            q=time_data(ds.variables[flagname],dim,n) if flagname in ds.variables else None
            valid=valid_met(arr[ix])
            valid_indices=ix[valid]
            result["valid_at_target_missing"]=int(valid.sum())
            result["missing_at_target_missing"]=int((~valid).sum())
            result["candidate_qc_field"]=flagname if q is not None else None
            result["uninterpreted_qc_at_target_missing"]=qc_hist(q[ix]) if q is not None else None
            result["sample_values"]=[
                {"index":int(i),"candidate_value":float(arr[i]),
                 "candidate_qc_uninterpreted":float(q[i]) if q is not None and np.isfinite(q[i]) else None}
                for i in valid_indices[:8]]
            result["decision"]="REVIEW_RAW_INDEPENDENCE_HEIGHT_QC_NOT_APPROVED"
            source["candidate_donors"].append(result)

    # Science-critical point: Calperum SH alarm, preserve tower T/pressure
    # and raw flag context. No automatic supersaturation correction.
    if site=="AU-Cpr":
        for e in events:
            if e["variable"]=="SH" and e["event_type"]=="PHYSICAL_ALARM":
                center=int(e["first_index"])
                ix=list(range(max(0,center-2),min(n,center+3)))
                t=ds.variables["time"]
                units=str(t.units)
                cal=getattr(t,"calendar","standard")
                times={str(i):str(netCDF4.num2date(float(t[i]),units,calendar=cal)) for i in ix}
                source["spot_checks"].append({
                    "event_type":"SH_PHYSICAL_ALARM",
                    "index":center,"time_samples":times,
                    "original_variable_and_flag_context":nearby_text(ds,site,ix),
                    "note":"Do not change SH; check humidity units, saturation physics and QC provenance"})
    return source


def self_test():
    assert unit_same("W/m^2","W/m^2")
    assert not unit_same("W/m^2","W/m2")
    assert not valid_met(np.array([np.nan,-9999.0,1.0])).tolist()[:2]==[True,True]
    assert valid_met(np.array([np.nan,-9999.0,1.0])).tolist()==[False,False,True]
    assert qc_hist(np.array([0,10,10,np.nan]))["codes"]=={"0.0":1,"10.0":2}
    # Regression for Stage04 v1: "sd" substring must not hide all Fsd donors.
    class FakeDataset:
        variables={"Fsd":None,"Fsd_1":None,"Fsd_7m":None,
                   "Fsd_QCFlag":None,"Fsd_1_QCFlag":None,"Fsd_SD":None,
                   "Ta_HMP_2m":None,"Ta_QCFlag":None}
    assert candidate_names(FakeDataset(),"Fsd")==["Fsd_1","Fsd_7m"]
    assert candidate_names(FakeDataset(),"Ta")==["Ta_HMP_2m"]
    print("STAGE04 SELF-TEST PASS: same-unit donor guard, Fsd_1/Fsd_7m regression, source-fill guard and QC histogram")


def main():
    if sys.argv[1:]==["--self-test"]:
        self_test()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--stage03",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    root=args.root.resolve()
    out=args.out.resolve()
    if args.out.is_symlink() or out==root or root in out.parents or out==args.stage03.resolve():
        raise ValueError("Output must be new report directory outside source and Stage03 trees")
    if out.exists():
        raise FileExistsError("Output exists; use new timestamp")
    rows=load_manifest(args.manifest)
    with (args.stage03/"stage03_event_ledger.tsv").open(encoding="utf-8",newline="") as h:
        events=list(csv.DictReader(h,delimiter="\t"))
    groups=collections.defaultdict(list)
    for e in events:
        groups[(e["site"],e["filename"])].append(e)
    out.mkdir(parents=True)
    reports=[]
    table=[]
    for row in rows:
        site,fname=row["site"],row["filename"]
        src=root/site/"forcing"/"raw"/fname
        result={"site":site,"filename":fname}
        try:
            if src.is_symlink() or not src.is_file():
                raise FileNotFoundError("missing or symlink original")
            with netCDF4.Dataset(src,mode="r") as ds:
                result=audit_one(ds,site,fname,groups[(site,fname)])
            result["status"]="EVIDENCE_COLLECTED_NOT_APPROVED"
            table.extend(result["candidate_donors"])
            print("EVIDENCE",site,fname,"candidates",len(result["candidate_donors"]))
        except Exception as exc:
            result={"site":site,"filename":fname,"status":"ERROR",
                    "error":type(exc).__name__+": "+str(exc)[:350]}
            print("ERROR",site,fname,result["error"])
        reports.append(result)
    output={"stage":"OzFlux Stage04 QC provenance and donor evidence",
            "source_mode":"READ_ONLY", "science_approval":False,
            "files":reports,
            "audited":sum(r["status"]=="EVIDENCE_COLLECTED_NOT_APPROVED" for r in reports)}
    (out/"stage04_evidence.json").write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8")
    cols=["site","filename","target_variable","target_missing_rows","candidate",
          "main_units","candidate_units","same_units","valid_at_target_missing",
          "candidate_height","candidate_qc_field","decision"]
    with (out/"stage04_donor_candidates.tsv").open("w",encoding="utf-8",newline="") as h:
        writer=csv.DictWriter(h,fieldnames=cols,delimiter="\t",extrasaction="ignore")
        writer.writeheader()
        writer.writerows(table)
    print("EVIDENCE COLLECTED",output["audited"],"/10")
    print("REPORT DIRECTORY",out)
    print("QC FLAG VALUES UNINTERPRETED; NO SCIENCE APPROVAL OR FORCING GENERATED")
    return 0 if output["audited"]==10 else 1


if __name__=="__main__":
    raise SystemExit(main())

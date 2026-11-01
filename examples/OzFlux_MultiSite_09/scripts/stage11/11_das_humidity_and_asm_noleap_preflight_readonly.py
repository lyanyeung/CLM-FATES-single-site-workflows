#!/usr/bin/env python3
"""OzFlux Stage11: DaS 885-event cross-variable QC + ASM NOLEAP preview.

READ ONLY. Open original NetCDF source files with mode='r', never amend raw
values, write DATM NetCDF, or submit any model job. All date conversions are
hypothetical numeric views and not a science-approved clock transform.
"""
from __future__ import annotations
import argparse
import collections
import csv
import datetime as dt
import json
from pathlib import Path
import sys

import netCDF4
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DAS="DalyUncleared_20080101T0000_to_20260423T0000_L6.nc"
ASM="AliceSpringsMulga1_20100903T0000_to_20230308T0900_L6.nc"
STAGE10_LABEL="LOCAL_END_LABEL_TO_UTC_CENTER_CANDIDATE"
SHIFT_MIN=585  # Source native local END -> hypothetical UTC center
MET=("Ta","SH","ps","Fsd","Fld","Ws","Precip")
REPORT_ROWS=("source_index","native_time_UNVERIFIED_TIMEZONE",
             "Ta_degC","SH_kgkg","ps_kPa","qsat_kgkg",
             "ratio_SH_to_qsat","RH_from_T_SH_ps_percent",
             "VPD_from_T_SH_ps_kPa","source_SH_QCFlag","source_Ta_QCFlag",
             "source_ps_QCFlag","RH_source_value","RH_source_units",
             "RH_source_QCFlag","VPD_source_value","VPD_source_units",
             "VPD_source_QCFlag","RH_source_minus_derived_pct",
             "VPD_source_minus_derived_kPa",
             "SH_prev","SH_next","Ta_prev","Ta_next",
             "source_candidate_repair_approved")
ASM_COLS=("year","expected_records_with_leap","candidate_UTC_records",
          "candidate_UTC_first_center","candidate_UTC_last_center",
          "candidate_UTC_centers_consistent","removed_UTC_Feb29_rows",
          "candidate_NOLEAP_records","no_missing_met_values",
          "RHratio_gt1p05","unapproved_source_QC0_meteorological_fraction",
          "native_time_semantics_approved","surface_PFT_ZBOT_approved",
          "DATM_generation_authorised")
SECOND_PER_NUM={"days":86400,"day":86400,"hours":3600,"hour":3600,
                "minutes":60,"minute":60,"seconds":1,"second":1}


def get_number_units(t):
    unit=t.units.lower().split(" since ",1)[0].strip()
    if unit not in SECOND_PER_NUM:
        raise ValueError("Unexpected source time unit "+str(t.units))
    return float(SECOND_PER_NUM[unit])


def numeric(ds,name,dim,n,optional=False):
    if name not in ds.variables:
        if optional:
            return None
        raise ValueError("Missing "+name)
    v=ds.variables[name]
    if not np.issubdtype(v.dtype,np.number) or v.dimensions.count(dim)!=1:
        if optional: return None
        raise ValueError("Unsupported shape/dtype "+name)
    if v.shape[v.dimensions.index(dim)]!=n or any(
            d!=dim and v.shape[i]!=1 for i,d in enumerate(v.dimensions)):
        if optional: return None
        raise ValueError("Unexpected extra dims "+name)
    return np.ma.asarray(v[:],dtype=float).filled(np.nan).reshape(-1)


def valid(z):
    return np.isfinite(z)&(z>-9990)


def qsat(T,p):
    es=0.6112*np.exp(np.clip(17.67*T/(T+243.5),-50,30))
    return np.where(p-0.378*es>0,0.622*es/(p-0.378*es),np.nan)


def esat(T):
    return 0.6112*np.exp(np.clip(17.67*T/(T+243.5),-50,30))


def e_actual(q,p):
    return np.where((0.622+0.378*q)>0,p*q/(0.622+0.378*q),np.nan)


def optional_units(ds,key):
    if key not in ds.variables:
        return None
    v=ds.variables[key]
    return str(v.getncattr("units")) if "units" in v.ncattrs() else None


def rh_percent(value,units):
    if value is None or units is None:
        return None
    u=units.strip().lower()
    if u in ("%", "percent", "percentage", "percent_rh"):
        return value
    if u in ("1", "fraction", "unitless"):
        return value*100.
    return None


def vpd_kpa(value,units):
    if value is None or units is None:
        return None
    u=units.strip().lower()
    if u in ("kpa",): return value
    if u in ("hpa","mbar"): return value/10.
    if u in ("pa",): return value/1000.
    return None


def safe(x):
    return float(x) if np.isfinite(x) and x>-9990 else None


def label(v,val):
    return str(netCDF4.num2date(float(val),v.units,
                                calendar=getattr(v,"calendar","standard")))


def year_nums(v,year):
    cal=getattr(v,"calendar","standard")
    return (float(netCDF4.date2num(dt.datetime(year,1,1),v.units,calendar=cal)),
            float(netCDF4.date2num(dt.datetime(year+1,1,1),v.units,calendar=cal)))


def parse_tsv(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h,delimiter="\t"))


def original(ds):
    t=ds.variables["time"]
    vals=np.ma.asarray(t[:],dtype=float).filled(np.nan).reshape(-1)
    if len(vals)<10 or not np.isfinite(vals).all() or np.any(np.diff(vals)<=0):
        raise ValueError("Malformed source time")
    dim=t.dimensions[0]
    return t,vals,dim,len(vals)


def inspect_das(path,prior_rows):
    with netCDF4.Dataset(str(path),mode="r") as ds:
        t,times,dim,n=original(ds)
        Ta=numeric(ds,"Ta",dim,n)
        SH=numeric(ds,"SH",dim,n)
        ps=numeric(ds,"ps",dim,n)
        qTa=numeric(ds,"Ta_QCFlag",dim,n)
        qSH=numeric(ds,"SH_QCFlag",dim,n)
        qps=numeric(ds,"ps_QCFlag",dim,n)
        q=qsat(Ta,ps)
        ratio=SH/q
        ok=valid(Ta)&valid(SH)&valid(ps)&np.isfinite(q)&(q>0)
        intervals=[]
        for y in range(2009,2022):
            a,b=year_nums(t,y)
            i=int(np.searchsorted(times,a,"left"))
            j=int(np.searchsorted(times,b,"left"))
            intervals.append((i,j))
        mask=np.zeros(n,dtype=bool)
        for i,j in intervals:mask[i:j]=True
        suspect=mask&ok&(ratio>1.05)
        ids=np.flatnonzero(suspect)
        expected_ids=np.array([int(r["source_index"]) for r in prior_rows],dtype=int)
        if len(ids)!=885 or len(expected_ids)!=885 or not np.array_equal(ids,np.sort(expected_ids)):
            raise ValueError("Stage10 885 source event indices not reproduced")
        if np.any(qSH[ids]!=0):
            raise ValueError("Stage10 QC0 evidence changed")
        RH=numeric(ds,"RH",dim,n,optional=True)
        VPD=numeric(ds,"VPD",dim,n,optional=True)
        qRH=numeric(ds,"RH_QCFlag",dim,n,optional=True)
        qVPD=numeric(ds,"VPD_QCFlag",dim,n,optional=True)
        uRH=optional_units(ds,"RH")
        uVPD=optional_units(ds,"VPD")
        idx_rows=[]
        classes=collections.Counter()
        byyear=collections.defaultdict(lambda:{"n":0,"max_ratio":0.0,
                     "class_lt1p10":0,"class_1p10_1p20":0,
                     "class_1p20_1p50":0,"class_ge1p50":0,
                     "qc_Ta0":0,"qc_ps0":0,"rh_evidence_count":0,
                     "vpd_evidence_count":0})
        for i in ids:
            i=int(i)
            e=e_actual(SH[i],ps[i])
            sat=esat(Ta[i])
            RHcalc=100*e/sat
            VPDcalc=sat-e
            ru=safe(RH[i]) if RH is not None else None
            vu=safe(VPD[i]) if VPD is not None else None
            rp=rh_percent(ru,uRH)
            vp=vpd_kpa(vu,uVPD)
            year=int(label(t,times[i])[:4])
            yr=byyear[year]
            yr["n"]+=1
            yr["max_ratio"]=max(yr["max_ratio"],float(ratio[i]))
            if ratio[i]<1.10:
                classkey="class_lt1p10"
            elif ratio[i]<1.20:
                classkey="class_1p10_1p20"
            elif ratio[i]<1.50:
                classkey="class_1p20_1p50"
            else:
                classkey="class_ge1p50"
            yr[classkey]+=1;classes[classkey]+=1
            yr["qc_Ta0"]+=int(qTa[i]==0)
            yr["qc_ps0"]+=int(qps[i]==0)
            yr["rh_evidence_count"]+=int(rp is not None)
            yr["vpd_evidence_count"]+=int(vp is not None)
            idx_rows.append({
                "source_index":i,
                "native_time_UNVERIFIED_TIMEZONE":label(t,times[i]),
                "Ta_degC":safe(Ta[i]),"SH_kgkg":safe(SH[i]),
                "ps_kPa":safe(ps[i]),"qsat_kgkg":safe(q[i]),
                "ratio_SH_to_qsat":safe(ratio[i]),
                "RH_from_T_SH_ps_percent":float(RHcalc),
                "VPD_from_T_SH_ps_kPa":float(VPDcalc),
                "source_SH_QCFlag":safe(qSH[i]),
                "source_Ta_QCFlag":safe(qTa[i]),
                "source_ps_QCFlag":safe(qps[i]),
                "RH_source_value":ru,"RH_source_units":uRH,
                "RH_source_QCFlag":safe(qRH[i]) if qRH is not None else None,
                "VPD_source_value":vu,"VPD_source_units":uVPD,
                "VPD_source_QCFlag":safe(qVPD[i]) if qVPD is not None else None,
                "RH_source_minus_derived_pct":rp-float(RHcalc) if rp is not None else None,
                "VPD_source_minus_derived_kPa":vp-float(VPDcalc) if vp is not None else None,
                "SH_prev":safe(SH[i-1]) if i>0 else None,
                "SH_next":safe(SH[i+1]) if i+1<n else None,
                "Ta_prev":safe(Ta[i-1]) if i>0 else None,
                "Ta_next":safe(Ta[i+1]) if i+1<n else None,
                "source_candidate_repair_approved":False,
            })
        counts=sum(int(x["n"]) for x in byyear.values())
        if counts!=885:
            raise AssertionError("Unexplained source humidity count")
        metadata={
            "RH_present":RH is not None, "RH_units":uRH,
            "VPD_present":VPD is not None, "VPD_units":uVPD,
            "RH_is_same_processed_product_not_independent_observation":True,
            "SH_QC0_on_all_885":True,
            "source_measurements_not_modified":True,
            "formula_saturation_over_liquid_water_approx":True,
            "site_data_885":dict(sorted(byyear.items())),
            "severity_total":dict(classes),
            "top20_severity":sorted(
                [{k:r[k] for k in ("source_index",
                    "native_time_UNVERIFIED_TIMEZONE","Ta_degC","SH_kgkg",
                    "ps_kPa","ratio_SH_to_qsat","source_Ta_QCFlag",
                    "source_SH_QCFlag","source_ps_QCFlag")}
                 for r in idx_rows],
                key=lambda r:-r["ratio_SH_to_qsat"])[:20],
            "science_approval":False,
        }
        return idx_rows,metadata


def asm_view(path,st10_bounds):
    with netCDF4.Dataset(str(path),mode="r") as ds:
        t,times,dim,n=original(ds)
        unit=get_number_units(t)
        view=times-SHIFT_MIN*60/unit
        fields={key:numeric(ds,key,dim,n) for key in MET}
        flagfields={key:numeric(ds,key+"_QCFlag",dim,n) for key in MET}
        result=[]
        for year in range(2013,2019):
            low,high=year_nums(t,year)
            a=int(np.searchsorted(view,low,"left"))
            b=int(np.searchsorted(view,high,"left"))
            ix=np.arange(a,b,dtype=int)
            stamp_first=label(t,view[a]) if len(ix) else None
            stamp_last=label(t,view[b-1]) if len(ix) else None
            step=1800/unit
            expected=int(round((high-low)/step))
            centered=bool(
                len(ix)==expected and
                abs(view[a]-(low+step*.5))*unit<1 and
                abs(view[b-1]-(high-step*.5))*unit<1 and
                np.all(np.abs(np.diff(view[a:b])-step)*unit<1)
            )
            boundary=st10_bounds.get(year)
            if not boundary or boundary["structurally_complete_utc_calendar_year"]!="True" or not centered:
                raise ValueError("Stage10 UTC boundary view does not pass for ASM "+str(year))
            if len(ix)!=int(boundary["actual_records"]):
                raise ValueError("Stage10 and Stage11 UTC boundary count mismatch")
            nmiss=sum(int(np.sum(~valid(fields[k][ix]))) for k in MET)
            nQC0=sum(int(np.sum(flagfields[k][ix]==0)) for k in MET)
            # Convert only trial timestamp labels into Python time to test UTC leap
            # day classification, never write a new timestamp to source files.
            fromarray=netCDF4.num2date(view[a:b],t.units,
                    calendar=getattr(t,"calendar","standard"))
            leap_count=sum(int(x.month==2 and x.day==29) for x in fromarray)
            noleap=len(ix)-leap_count
            q=qsat(fields["Ta"][ix],fields["ps"][ix])
            ok=valid(fields["Ta"][ix])&valid(fields["SH"][ix])&valid(fields["ps"][ix])&np.isfinite(q)&(q>0)
            humidity=int(np.sum(ok & (fields["SH"][ix]>1.05*q)))
            if nmiss or humidity or noleap!=17520:
                raise ValueError("ASM trial year not physically/NOLEAP complete: "+str(year))
            result.append({
                "year":year,"expected_records_with_leap":expected,
                "candidate_UTC_records":len(ix),
                "candidate_UTC_first_center":stamp_first,
                "candidate_UTC_last_center":stamp_last,
                "candidate_UTC_centers_consistent":centered,
                "removed_UTC_Feb29_rows":leap_count,
                "candidate_NOLEAP_records":noleap,
                "no_missing_met_values":not bool(nmiss),
                "RHratio_gt1p05":humidity,
                "unapproved_source_QC0_meteorological_fraction":round(
                    nQC0/(len(ix)*len(MET)),6),
                "native_time_semantics_approved":False,
                "surface_PFT_ZBOT_approved":False,
                "DATM_generation_authorised":False,
            })
        metadata={
            "time_metadata":{x:str(t.getncattr(x))
                             for x in t.ncattrs()},
            "site_metadata":{x:str(ds.getncattr(x))[:750] for x in ds.ncattrs()
                             if any(k in x.lower() for k in (
                                 "lat","lon","time","site","height","vegetation",
                                 "processing","history"))},
            "meteorological_variable_metadata":{
                k:{a:str(ds.variables[k].getncattr(a))[:900]
                   for a in ds.variables[k].ncattrs() if a in (
                       "units","height","instrument","statistic_type",
                       "source","description_L4","description_L6")}
                for k in MET},
            "NOLEAP_datetime_preview_only_no_new_calendar_files":True,
        }
        return result,metadata


def write_tsv(path,columns,rows):
    with path.open("w",encoding="utf-8",newline="") as h:
        wr=csv.DictWriter(h,fieldnames=columns,delimiter="\t",extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)


def selftest():
    assert np.allclose(qsat(np.array([25.]),np.array([100.])),
                       np.array([qsat(np.array([25.]),np.array([100.]))[0]]))
    assert rh_percent(100.0,"%")==100
    assert rh_percent(1.0,"1")==100
    assert rh_percent(1.0,"unverified")==None
    assert vpd_kpa(10.0,"hPa")==1.0
    assert get_number_units(type("T",(),{"units":"days since 1800-01-01"})())==86400
    assert SHIFT_MIN==585
    print("STAGE11 SELF-TEST PASS: RH/VPD unit guards, qsat and time-offset preview; SOURCE READ-ONLY")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest()
        return 0
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage10",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    root,out=a.root.resolve(),a.out.resolve()
    if out.exists() or a.out.is_symlink() or root==out or root in out.parents:
        raise ValueError("Choose unused HOME report directory outside source trees")
    with (a.stage10/"stage10_source_time_humidity.json").open(encoding="utf-8") as h:
        prev=json.load(h)
    if prev.get("DaS_humidity_event_count")!=885 or prev.get("science_approval") is not False:
        raise ValueError("Stage10 science audit requires 885 records and unapproved status")
    records=parse_tsv(a.stage10/"stage10_DaS_SH_885_exact_records.tsv")
    if len(records)!=885:
        raise ValueError("Stage10 detailed humidity report is incomplete")
    boundary=parse_tsv(a.stage10/"stage10_hypothetical_UTC_year_bounds.tsv")
    bounds={int(r["year"]):r for r in boundary
            if r["site"]=="AU-ASM" and
            r["label_hypothesis"]=="LOCAL_END_LABEL_TO_UTC_CENTER_CANDIDATE"}
    if len(bounds)!=6:
        raise ValueError("Stage10 ASM expected 6 boundary report rows")
    das=root/"AU-DaS"/"forcing"/"raw"/DAS
    asm=root/"AU-ASM"/"forcing"/"raw"/ASM
    for src in (das,asm):
        if src.is_symlink() or not src.is_file():
            raise FileNotFoundError("Missing or symlink source: "+str(src))
    diagnostics, dasmeta=inspect_das(das,records)
    asmrows,asmmeta=asm_view(asm,bounds)
    if len(diagnostics)!=885 or len(asmrows)!=6:
        raise AssertionError("Unexpected Stage11 completeness")
    out.mkdir(parents=True)
    payload={
        "stage":"OzFlux Stage11 AU-DaS source humidity consistency / AU-ASM noleap preview",
        "source_read_only":True,"science_approval":False,
        "approved_DaS_humidity_fixes":0,"candidate_DATM_generated":False,
        "AU_DaS":dasmeta,"AU_ASM":asmmeta,
        "unresolved_source_time_interval_semantics":True,
        "unresolved_surface_PFT_soil_ZBOT":True,
    }
    (out/"stage11_science_evidence.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    write_tsv(out/"stage11_DaS_885_cross_variable.tsv",REPORT_ROWS,diagnostics)
    write_tsv(out/"stage11_ASM_UTC_NOLEAP_preview.tsv",ASM_COLS,asmrows)
    print("STAGE11 PASS",len(diagnostics),"DaS CROSS_VAR",
          len(asmrows),"ASM UTC NOLEAP PREVIEW YEARS")
    print("DaS 885 SEVERITY",dasmeta["severity_total"])
    print("DaS RH/VPD AVAILABLE",dasmeta["RH_present"],dasmeta["VPD_present"])
    for y in asmrows:
        print("ASM",y["year"],"UTC_RECORDS",y["candidate_UTC_records"],
              "NOLEAP_PREVIEW",y["candidate_NOLEAP_records"],
              "NO_MISSING_MET",y["no_missing_met_values"])
    print("REPORT_DIR",out)
    print("NO ORIGINAL NETCDF EDITS, NO NEW FORCING, SCIENCE APPROVAL FALSE")
    return 0


if __name__=="__main__":
    raise SystemExit(main())

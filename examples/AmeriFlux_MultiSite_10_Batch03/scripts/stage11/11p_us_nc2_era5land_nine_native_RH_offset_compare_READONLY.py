#!/usr/bin/env python3
"""Stage11p — Independent ERA5-Land hourly T2m/D2m/SP vs 9 US-NC2 source-native humidity review candidates.

Reuses the EXISTING previously downloaded and SHA-validated 288-hour CDS
ERA5-Land ZIP/NC and the sealed Stage11m 40-record source/companion RH
context and Stage11o (shifted sentinel) nine-event WHAT-IF report.

Tests local native timestamp to UTC hypotheses -6, -5 and -4 hours:
assumed UTC = native local time - candidate offset. These are
CLOCK SENSITIVITIES, NOT tower clock approval. Linear interpolation of
ERA5-Land hourly **temperature and dewpoint** to each half-hour, THEN
calculate RH from water-phase es(Td)/es(T). Do not replace tower TA/TBOT.
ERA5-Land is driven by ERA5, so this is a related but distinct gridded
product, not an independent EC tower RH measurement.

--self-test: time algebra, synthetic humidity checks; no source or writes.
--check: full source checksum, netCDF audit, compare 9x3 and 40x3; NO writes.
--run: same audit; make ONE NEW report-only directory + SHA receipt.
No source download, source modifications, forcing writes, DATM/CIME/Slurm,
approved time offset or new repair decisions.
"""
import argparse
from datetime import datetime,timezone,timedelta
import hashlib,importlib.util,json
from pathlib import Path
import sys,traceback,zipfile
from uuid import uuid4

import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="stage11p-v1-20261024-nine-source-era5land-3offset-RH-evidence"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
REPO=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
SOURCE_SCRIPT=REPO/"scripts/stage11/11o_us_nc2_2025_march_era5land_evidence.py"
SOURCE_BLOB="ba4e849619071bd462792e3b234d940bbf8dc8f2"
LAND=ROOT/"external_evidence/era5land_timeseries/US-NC2/2025"
STEM="ERA5Land_US-NC2_2025_Mar16_Mar27_t2m_d2m_sp"
M=ROOT/"reports/stage11m_stage11l_four_boundary_context_20261024T101551Z_e5027215"
O=ROOT/"reports/stage11o_two_shifted_RH_boundaries_READ_ONLY_20261024T103620Z_6abc437f"
L=ROOT/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
CONTEXT_NAME="40_halfhours_original_ERA_Stage07_Stage11h_Stage11l_context.csv"
NINE={
 "202503181730","202503181800",
 "202503230730","202503230800","202503230830",
 "202503231530","202503231600",
 "202503251030","202503251100"
}
PRIOR_STAGE07={"202503230730","202503230800","202503251030"}
OFFSETS=(-6,-5,-4)
SEALED_O={
 "2_new_shifted_edge_source_humidity_candidates.csv",
 "7_previous_human_review_candidates_no_changes.csv",
 "8_hypothetical_scenarios_summary.csv",
 "80_edge_comparisons_all_scenarios.csv",
 "SCIENTIFIC_HOLD.md"
}
SEALED_M={
 CONTEXT_NAME,"4_high_jump_boundary_differences.csv","SCIENTIFIC_HOLD.md"
}

def regular(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink SHA source: "+str(p))
    return p

def directory(p):
    p=Path(p)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or symlink source folder: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def gitblob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def module():
    if gitblob(SOURCE_SCRIPT)!=SOURCE_BLOB:
        raise ValueError("Stage11o ERA5-Land audited code Git blob changed")
    spec=importlib.util.spec_from_file_location("pinned_stage11o_era5land",SOURCE_SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def esw(ta_c):
    return 6.112*np.exp(17.67*np.asarray(ta_c,dtype=float)/
                        (np.asarray(ta_c,dtype=float)+243.5))

def rh_from_dewpoint(t_k,td_k):
    return 100.*esw(np.asarray(td_k,dtype=float)-273.15)/esw(
        np.asarray(t_k,dtype=float)-273.15)

def native_to_utc(native,offset):
    return datetime.strptime(str(native),"%Y%m%d%H%M").replace(
        tzinfo=timezone.utc)-timedelta(hours=offset)

def verify():
    for p in (ROOT,LAND,M,O,L):
        directory(p)
    regular(L/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    src=module()
    datafile=src.chosen_existing()
    rec=json.loads(regular(LAND/(STEM+".receipt.json")).read_text(encoding="utf-8"))
    if (rec.get("site")!="US-NC2"
        or rec.get("dataset")!="reanalysis-era5-land-timeseries"
        or rec.get("request")!=src.request()
        or rec.get("source_sha256")!=sha(datafile)
        or rec.get("clock_approved") is not False
        or rec.get("changed_original_or_shadow_forcing") is not False):
        raise ValueError("CDS ERA5-Land source checksum/request/clock gate does not match")
    audited=src.audit_dataset(datafile)
    if (audited["utc_hours"]!=288 or set(audited["variables"])!={"t2m","d2m","sp"}
        or audited["status"]!="NETCDF_STRUCTURALLY_VALID_NOT_CLOCK_OR_SCIENCE_APPROVED"):
        raise ValueError("CDS source structural audit not approved for scientific review")

    mrec=json.loads(regular(M/"stage11m_read_only_boundary_receipt.json").read_text())
    orec=json.loads(regular(O/"stage11o_read_only_science_receipt.json").read_text())
    lrec=json.loads(regular(L/"stage11l_scientific_hold_receipt.json").read_text())
    if (mrec.get("version")!="stage11m-v1-20261024-four-boundary-no-forcing-write"
        or mrec.get("original_native_context_rows")!=40
        or mrec.get("source_Stage11l_receipt_SHA256")!=sha(L/"stage11l_scientific_hold_receipt.json")
        or mrec.get("Postv5_approved")!=0
        or set(mrec.get("output_sha256",{}))!=SEALED_M):
        raise ValueError("Previous Stage11m 40-row context receipt changed")
    for name,sig in mrec["output_sha256"].items():
        if sha(M/name)!=sig:
            raise ValueError("Stage11m SHA mismatch: "+name)
    if (orec.get("version")!="stage11o-v1-20261024-two-shifted-edge-source-RH-sensitivity"
        or orec.get("new_hypothetical_only_native_times")!=2
        or orec.get("prior_hypothetical_only_native_times")!=7
        or orec.get("scenario_count")!=8
        or orec.get("boundary_comparison_rows")!=80
        or orec.get("new_human_approvals")!=0
        or orec.get("Postv5_approved")!=0
        or orec.get("source_Stage11m_receipt_SHA256")!=sha(M/"stage11m_read_only_boundary_receipt.json")
        or orec.get("source_Stage11l_receipt_SHA256")!=sha(L/"stage11l_scientific_hold_receipt.json")
        or set(orec.get("output_sha256",{}))!=SEALED_O):
        raise ValueError("Previous Stage11o nine-source what-if receipt changed")
    for name,sig in orec["output_sha256"].items():
        if sha(O/name)!=sig:
            raise ValueError("Stage11o SHA mismatch: "+name)
    if (lrec.get("version")!="stage11l-v1-20261024-11-humidity-only-successor"
        or lrec.get("retained_EC_tower_TA_and_TBOT") is not True
        or lrec.get("Postv5_approved")!=0 or lrec.get("DATM_ready")!=0
        or lrec.get("spinup_authorized")!=0):
        raise ValueError("Stage11l protected forcing scientific gate changed")

    ctx=pd.read_csv(regular(M/CONTEXT_NAME),dtype={"native_key":str},low_memory=False)
    prior=pd.read_csv(regular(O/"7_previous_human_review_candidates_no_changes.csv"),
                      dtype={"native_key":str},low_memory=False)
    added=pd.read_csv(regular(O/"2_new_shifted_edge_source_humidity_candidates.csv"),
                      dtype={"native_key":str},low_memory=False)
    if len(ctx)!=40 or ctx.duplicated(["boundary_id","native_key"]).any():
        raise ValueError("Stage11m original context count or identity changed")
    if len(prior)!=7 or len(added)!=2:
        raise ValueError("Stage11o original seven/two files changed")
    observed=set(prior.native_key)|set(added.native_key)
    if (observed!=NINE or len(observed)!=9
        or set(prior.native_key)&set(added.native_key)
        or not NINE<=set(ctx.native_key)
        or not set(prior.loc[prior.Stage07_previously_amended,"native_key"])==PRIOR_STAGE07):
        raise ValueError("Exact 9 expected read-only source-native event IDs changed")
    # 9 native timestamps uniquely represented in these four windows
    if ctx.loc[ctx.native_key.isin(NINE),"native_key"].duplicated().any():
        raise ValueError("Ambiguous duplicate sample at one of nine targets")
    return datafile,src,ctx,prior,added

def read_hourly(path,source_module):
    from netCDF4 import Dataset,num2date
    first=source_module.expected_hours()
    fields={}
    def collect(ds):
        times=ds.variables.get("valid_time",ds.variables.get("time"))
        if times is None:
            raise ValueError("Missing NetCDF valid_time")
        t=num2date(times[:],getattr(times,"units",""),
                  calendar=getattr(times,"calendar","standard"),
                  only_use_cftime_datetimes=False,
                  only_use_python_datetimes=True)
        hours=[datetime(x.year,x.month,x.day,x.hour,x.minute,x.second,
                        tzinfo=timezone.utc) for x in t]
        if hours!=first:
            raise ValueError("NetCDF exact UTC hours changed after CDS structural audit")
        for k in ("t2m","d2m","sp"):
            if k not in ds.variables:
                continue
            if k in fields:
                raise ValueError("ERA5-Land source duplicate variable "+k)
            a=np.asarray(np.ma.asarray(ds.variables[k][:]).filled(np.nan),
                         dtype=float).reshape(-1)
            if len(a)!=288 or not np.isfinite(a).all():
                raise ValueError("Nonfinite ERA5-Land source "+k)
            fields[k]=a
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for item in zf.infolist():
                if not item.is_dir():
                    with Dataset("source.nc","r",memory=zf.read(item)) as ds:
                        collect(ds)
    else:
        with Dataset(str(path),"r") as ds:
            collect(ds)
    if set(fields)!={"t2m","d2m","sp"}:
        raise ValueError("Missing required gridded ERA5-Land T/D2M/SP")
    return first,fields

def at_utc(time,first,fields):
    delta=(time-first[0]).total_seconds()/3600.
    if not 0<=delta<=len(first)-1:
        raise ValueError("Timestamp UTC outside ERA5-Land 288 hourly records: "+str(time))
    a=int(delta)
    b=min(a+1,len(first)-1)
    weight=delta-a
    t=(1-weight)*fields["t2m"][a]+weight*fields["t2m"][b]
    d=(1-weight)*fields["d2m"][a]+weight*fields["d2m"][b]
    p=(1-weight)*fields["sp"][a]+weight*fields["sp"][b]
    val=float(rh_from_dewpoint(t,d))
    if (not np.isfinite([t,d,p,val]).all()
        or not (0<val<=101. and 40000<p<110000 and d<=t+.1)):
        raise ValueError("Interpolated ERA5-Land thermodynamic closure invalid")
    return float(t-273.15),float(d-273.15),float(p),val,weight

def calculate():
    source,mod,context,prior,added=verify()
    first,fields=read_hourly(source,mod)
    records=[]
    for r in context.itertuples(index=False):
        site_rh=float(r.Stage11l_RH_water_pct)
        pair_rh=float(r.companion_ERA_RH_water_pct)
        orig_rh=float(r.original_implied_RH_water_pct)
        for offset in OFFSETS:
            utc=native_to_utc(r.native_key,offset)
            temp,dew,press,land_rh,w=at_utc(utc,first,fields)
            records.append({
                "site":"US-NC2","boundary_context":r.boundary_id,
                "native_key":str(r.native_key),
                "assumed_native_UTC_offset_hours":offset,
                "hypothetical_UTC":utc.isoformat(),
                "ERA5Land_fractional_hour_interpolation":w,
                "ERA5Land_t2m_C":temp,
                "ERA5Land_d2m_C":dew,
                "ERA5Land_surface_pressure_Pa":press,
                "ERA5Land_water_RH_pct":land_rh,
                "original_tower_TA_C":float(r.original_TA_F_C),
                "original_source_RH_pct":orig_rh,
                "source_companion_ERA_RH_pct":pair_rh,
                "Stage11l_current_RH_pct":site_rh,
                "Stage11l_tower_TA_C_preserved":float(r.retained_EC_tower_TA_C),
                "ERA5Land_minus_companion_RH_pp":land_rh-pair_rh,
                "ERA5Land_minus_Stage11l_RH_pp":land_rh-site_rh,
                "ERA5Land_minus_source_RH_pp":land_rh-orig_rh,
                "is_unapproved_nine_review_target":str(r.native_key) in NINE,
                "previously_Stage07_modified":
                    bool(r.Stage07_VPD_changed_from_source),
                "scientific_status":"REVIEW_ONLY_NO_SOURCE_CLOCK_REPAIR_APPROVAL"
            })
    frame=pd.DataFrame(records)
    focus=frame.loc[frame.is_unapproved_nine_review_target].copy()
    if len(frame)!=120 or len(focus)!=27 or focus.duplicated(
        ["native_key","assumed_native_UTC_offset_hours"]).any():
        raise ValueError("Expected 40*3 contexts and 9*3 focus records")

    rows=[]
    for offset,g in frame.groupby("assumed_native_UTC_offset_hours"):
        sub=focus.loc[focus.assumed_native_UTC_offset_hours.eq(offset)]
        rows.append({
            "assumed_native_UTC_offset_hours":int(offset),
            "all_context_rows":len(g),
            "nine_unapproved_target_rows":len(sub),
            "nine_MAE_ERA5Land_vs_companion_RH_pp":
                float(np.mean(np.abs(sub.ERA5Land_minus_companion_RH_pp))),
            "nine_median_abs_ERA5Land_vs_companion_RH_pp":
                float(np.median(np.abs(sub.ERA5Land_minus_companion_RH_pp))),
            "nine_MAE_ERA5Land_vs_Stage11l_RH_pp":
                float(np.mean(np.abs(sub.ERA5Land_minus_Stage11l_RH_pp))),
            "nine_MAE_ERA5Land_vs_original_source_RH_pp":
                float(np.mean(np.abs(sub.ERA5Land_minus_source_RH_pp))),
            "40_MAE_ERA5Land_vs_companion_RH_pp":
                float(np.mean(np.abs(g.ERA5Land_minus_companion_RH_pp))),
            "clock_offset_approved":False,
            "nine_RH_repair_approved":False
        })
    sums=pd.DataFrame(rows).sort_values("assumed_native_UTC_offset_hours")
    if len(sums)!=3 or not set(sums.assumed_native_UTC_offset_hours)==set(OFFSETS):
        raise ValueError("Three offset comparison groups not available")
    return source,frame,focus,sums

def self_test():
    assert len(NINE)==9 and len(PRIOR_STAGE07)==3
    assert native_to_utc("202503181730",-5)==datetime(
        2025,3,18,22,30,tzinfo=timezone.utc)
    start=[datetime(2025,3,18,h,tzinfo=timezone.utc) for h in (21,22,23)]
    fake={"t2m":np.array([290.,292.,294.]),
          "d2m":np.array([280.,282.,284.]),
          "sp":np.array([101000.,101100.,101200.])}
    t,d,p,rh,frac=at_utc(datetime(2025,3,18,21,30,tzinfo=timezone.utc),start,fake)
    assert abs(frac-.5)<1e-9 and abs(t-(291-273.15))<1e-9
    assert 0<rh<100 and p==101050.
    assert native_to_utc("202503251100",-4)==datetime(
        2025,3,25,15,0,tzinfo=timezone.utc)
    print("STAGE11P SELF-TEST PASS: native UTC offset hypotheses, hourly T/dewpoint interpolation, water RH physics, 9 source IDs, NO WRITES",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    opts=ap.add_mutually_exclusive_group(required=True)
    opts.add_argument("--self-test",action="store_true")
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE11P — US-NC2 NINE SOURCE NATIVE ERA5-LAND RH vs FLUXNET ERA COMPANION | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    filename,allrows,nine,summary=calculate()
    print("\n========== NINE NATIVE REVIEW TARGETS x THREE OFFSET HYPOTHESES ==========",flush=True)
    print(nine[["native_key","assumed_native_UTC_offset_hours",
        "ERA5Land_t2m_C","ERA5Land_d2m_C","ERA5Land_water_RH_pct",
        "source_companion_ERA_RH_pct","Stage11l_current_RH_pct",
        "ERA5Land_minus_companion_RH_pp",
        "ERA5Land_minus_source_RH_pp"]].to_string(index=False),flush=True)
    print("\n========== ALL 40 SOURCE CONTEXT ROWS x THREE OFFSETS: SUMMARY ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\nSTAGE11P SUMMARY: ERA5Land_hourly=288 validated_source_SHA=True "
        "nine_native_review_times=9 three_clock_hypotheses=3 comparison_rows=27 "
        "all_context_comparison_rows=120 EC_tower_T_preserved=True "
        "approved_clock_offset=0 approved_new_RH_repairs=0 "
        "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: NO SOURCE, REPORT, FORCING OR MODEL WRITES.",flush=True)
        return
    out=ROOT/"reports"/("stage11p_us_nc2_era5land_nine_RH_three_offsets_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    outputs={
        "nine_native_RH_source_vs_ERA5Land_three_UTC_offsets.csv":nine,
        "forty_source_context_x_three_offsets.csv":allrows,
        "three_UTC_offset_RH_comparison_statistics.csv":summary
    }
    for name,df in outputs.items():
        df.to_csv(out/name,index=False)
    note="""# Stage11p scientific hold: independent ERA5-Land evidence comparison only

ERA5-Land hourly T2m, D2m and pressure obtained from previously
downloaded and SHA-verified original CDS data (288 UTC hours). Three
hypothetical native tower UTC offsets (-6/-5/-4) and a simple temporal
interpolation are compared at nine unapproved US-NC2 humidity candidates,
with full 40-source-context evidence. Different ERA products are
ERA5-driven and are NOT independent tower humidity measurements.
No timestamp/clock offset is selected or adopted, and no forcing
or EC tower TA/TBOT is edited. No new humidity repair is approved.
Keep Stage07/11h/11l and their INCOMPLETE markers unchanged.
"""
    (out/"SCIENCE_HOLD.md").write_text(note,encoding="utf-8")
    receipt={
        "version":VERSION,
        "ERA5Land_original_source_file":str(filename),
        "ERA5Land_source_SHA256":sha(filename),
        "ERA5Land_source_receipt_SHA256":sha(LAND/(STEM+".receipt.json")),
        "source_Stage11m_receipt_SHA256":sha(M/"stage11m_read_only_boundary_receipt.json"),
        "source_Stage11o_sentinel_receipt_SHA256":sha(O/"stage11o_read_only_science_receipt.json"),
        "nine_unapproved_native_source_times":9,
        "clock_hypotheses_hours":list(OFFSETS),
        "comparison_focus_rows":27,"context_rows":120,
        "new_science_repair_approvals":0,
        "clock_offset_approved":False,"Postv5_approved":0,
        "DATM_ready":0,"spinup_authorized":0,
        "source_or_forcing_modified":False,
        "output_sha256":{n:sha(out/n) for n in [*outputs,"SCIENCE_HOLD.md"]}
    }
    (out/"stage11p_science_hold_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE11P SOURCE RH REVIEW REPORT DIR:",out,flush=True)
    print("NO NEW ERA5-LAND DOWNLOAD, SOURCE FORCING MODIFICATION, OR MODEL JOB.",flush=True)

if __name__=="__main__":
    try:
        main()
    except Exception as err:
        print("STAGE11P STOP:",str(err),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

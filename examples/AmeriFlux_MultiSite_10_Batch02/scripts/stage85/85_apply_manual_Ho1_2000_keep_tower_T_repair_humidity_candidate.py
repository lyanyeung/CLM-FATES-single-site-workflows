#!/usr/bin/env python3
"""Stage85 — APPLY operator manual science decision, Ho1 year-2000 only.

OPERATOR EXPLICIT SCIENTIFIC DECISION (2026-10-25):
  Preserve original FLUXNET Ho1 TA_F exactly. All 17,294 measured-source
  TA_F_QC0 are accepted as the tower air-temperature reference, including
  the 505 historical QC0-vs-ERA5 large-difference episodes and both
  Stage84 January episodes (14+18 HH). No further tower-T source audit.
  Original 274 source TA_F with nonzero QC are preserved as original
  product values, but flagged as NOT independently measured/approved.

ERA-downscaled FLUXNET VPD_F_QC=2 (17,568/17,568) and VPD_F==VPD_ERA.
Keep original VPD for every measured-QC0 Ho1 native HH *if* within
0..saturation_vapour_pressure_water(original TA_F).
Only where VPD_F > eswater(tower TA_F) and original VPD_ERA is
physically bounded by eswater(TA_ERA) (exactly 1,068 HH), transfer
the ERA source fractional saturation deficit D=VPD_ERA/eswater(TA_ERA)
to the approved tower temperature:
   VPD_new = eswater(TA_F)*D
   RH_new = 100*(1-VPD_new/eswater(TA_F))
   e_new = eswater(TA_F)-VPD_new.
This changes only those 1,068 humidity values, NO temperature value.
The separate 32 original ERA-self-inconsistent Jan 2000 records are
already compatible with original tower TA_F; KEEP their original VPD
exactly (no artificial RH=0 or 100 clamp; no interpolation).
For all other original measured-QC0 time steps, keep original VPD and
derive source-compatible RH and e consistently.

For pressure where present: retain native PA_F (FLUXNET kPa), else
use PA_ERA (also kPa) and record choice. Compute
   QBOT_kgkg = epsilon*e / (p - (1-epsilon)*e)
with e and pressure in hPa. Never invent a missing pressure. Non-QC0
original T remain preserved, but derived humidity/QBOT are explicitly
not authorized by this manual QC0-only decision.

Output: new append-only candidate CSV, 1,068 humidity edits ledger,
32 originals unchanged ledger, 274 non-QC0 original T source HOLD,
SHA-provenance manifest and concise decision audit.
Not a CIME/NetCDF/DATM/model job; integration is distinct and must
never overwrite existing source files.
"""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
SOURCE83=BASE/"scripts/stage83/83_Ho1_2000_QC2_ERA_VPD_native_source_provenance_audit.py"
BLOB83="8e2bdf99a404ba27dcb8832f734028bb084a8660"
S84=REPORT/"stage84_Ho1_2000_32_raw_ERA_VPD_vs_ERA_T_source_20261025T225213Z_82b02e9f"
S84_CASES="32_Ho1_2000_original_VPD_ERA_gt_eswater_TA_ERA_source_cases.csv"
N=17568
N_TQC0=17294
N_MANUAL_HUMIDITY_CHANGE=1068
N_ERA_SELF=32
N_NOT_QC0=274
EPS=0.622
MANUAL="USER_APPROVED_KEEP_ORIGINAL_HO1_TA_F_2000_20261025"
PA_PRIORITY=("PA_F","PA_ERA")

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda:f.read(1048576),b""):h.update(data)
    return h.hexdigest()

def blob(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Pinned original Stage83 script missing/nonregular")
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def parent():
    if blob(SOURCE83)!=BLOB83:
        raise ValueError("Original validated Stage83 source blob changed")
    s=importlib.util.spec_from_file_location("stage83_source",SOURCE83)
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

def sources():
    m=parent()
    stage,old_manifest=m.schema_check()
    spec,inv,fields,header=m.original_primary()
    original=m.original_2000(spec,fields,header)
    raw=m.compare_source(stage,original)
    if (len(raw)!=N or
        int(raw.native_T_QC.eq(0).sum())!=N_TQC0 or
        not raw.native_VPD_QC.eq(2).all() or
        not np.isclose(raw.native_VPD,raw.native_VPD_ERA,atol=1e-4,
                       rtol=0,equal_nan=True).all()):
        raise ValueError("Native approved source identity/2000 QC/ERA VPD changed")
    signed=json.loads((S84/"stage84_source_science_manifest.json").read_text())
    if (S84/"INCOMPLETE_DO_NOT_USE").exists() or
        signed.get("schema")!="STAGE84_HO1_2000_32_ORIGINAL_ERA_VPD_T_SOURCE_INCONSISTENCIES_v1" or
        signed.get("separate_source_ERA_VPD_exceeds_eswater_source_TA_ERA")!=32 or
        signed.get("all_previous_1068_are_consistent_at_source_TA_ERA") is not True or
        signed.get("source_temperature_repair_approved") is not False or
        signed.get("approved_for_DATM") is not False):
        raise ValueError("Original completed Stage84 scientific context changed")
    for name,digest in signed["outputs_SHA256"].items():
        if sha(S84/name)!=digest:
            raise ValueError("Stage84 original immutable output SHA differed: "+name)
    original32=pd.read_csv(S84/S84_CASES,dtype={
        "tower_local_start":str,"source_csv_row":str})
    if len(original32)!=N_ERA_SELF:
        raise ValueError("Operator reviewed Stage84 January 32 source census changed")
    return raw,original32,spec,inv,old_manifest,signed,m

def pressure_year(spec):
    f=Path(spec["file"])
    columns=set(pd.read_csv(f,nrows=0).columns)
    keys=[k for k in PA_PRIORITY if k in columns]
    # This is an optional pressure companion: never fabricate PA.
    chunks=[];physical=0
    for chunk in pd.read_csv(f,usecols=["TIMESTAMP_START"]+keys,
                             dtype="string",chunksize=120000):
        t=chunk.TIMESTAMP_START.str.strip()
        sel=t.str.startswith("2000",na=False).to_numpy(dtype=bool)
        if sel.any():
            r=pd.DataFrame({"tower_local_start":t.loc[sel].astype(str),
               "source_csv_row":np.arange(physical+2,physical+2+len(chunk))[sel].astype(str)})
            for key in PA_PRIORITY:
                r[key]=pd.to_numeric(chunk.loc[sel,key],errors="coerce").to_numpy() if key in keys else np.nan
            chunks.append(r)
        physical+=len(chunk)
    if not chunks:raise ValueError("Year2000 pressure source year missing")
    y=pd.concat(chunks,ignore_index=True)
    if len(y)!=N or y.duplicated(["tower_local_start","source_csv_row"]).any():
        raise ValueError("Original pressure HH/physical row alignment changed")
    return y,keys

def saturation_water(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def create(raw,stage84,pressure,pa_columns):
    z=raw.merge(pressure,on=["tower_local_start","source_csv_row"],
        how="left",validate="one_to_one",indicator=True)
    if len(z)!=N or not z["_merge"].eq("both").all():
        raise ValueError("Original source pressure physical rows not aligned")
    T=pd.to_numeric(z.native_T,errors="coerce")
    QC=pd.to_numeric(z.native_T_QC,errors="coerce")
    V=pd.to_numeric(z.native_VPD,errors="coerce")
    Tera=pd.to_numeric(z.native_T_ERA,errors="coerce")
    e_t=saturation_water(T)
    e_era=saturation_water(Tera)
    approved=QC.eq(0)&T.between(-80,65)&V.notna()
    inconsistent=approved&V.gt(e_t+1e-8)
    target_era_valid=(V.ge(0)&V.le(e_era+1e-8)&Tera.between(-80,65))
    if (int(inconsistent.sum())!=N_MANUAL_HUMIDITY_CHANGE or
        not target_era_valid.loc[inconsistent].all() or
        not approved.sum()==N_TQC0):
        raise ValueError("Original Ho1 source and manual 1068 QC0 humidity repair scope changed")
    manual32={(str(x.tower_local_start),str(x.source_csv_row))
              for x in stage84.itertuples(index=False)}
    listed32=set(zip(z.loc[V.gt(e_era+1e-8),"tower_local_start"].astype(str),
                     z.loc[V.gt(e_era+1e-8),"source_csv_row"].astype(str)))
    if (len(listed32)!=32 or manual32!=listed32 or
        not (approved.loc[V.gt(e_era+1e-8)]&
             V.loc[V.gt(e_era+1e-8)].le(
                e_t.loc[V.gt(e_era+1e-8)]+1e-8)).all()):
        raise ValueError("Stage84 32 reviewed ERA-self exceptions not fully compatible with original T")
    v_new=V.copy()
    fraction=V/e_era
    v_new.loc[inconsistent]=e_t.loc[inconsistent]*fraction.loc[inconsistent]
    rh=100*(1-v_new/e_t)
    e=e_t-v_new
    if (not v_new.loc[approved].ge(-1e-7).all() or
        not v_new.loc[approved].le(e_t.loc[approved]+1e-7).all() or
        not rh.loc[approved].between(-1e-6,100+1e-6).all() or
        not e.loc[approved].ge(-1e-7).all() or
        not np.allclose(v_new.loc[approved & ~inconsistent],
                        V.loc[approved & ~inconsistent],rtol=0,atol=1e-12)):
        raise ValueError("Manual approved tower-T humidity mathematically inconsistent")
    # FLUXNET FULLSET PA_F/PA_ERA units = kPa; 1 kPa=10 hPa.
    p=np.full(len(z),np.nan,dtype=float)
    p_label=np.array(["NO_SOURCE_PRESSURE"]*len(z),dtype=object)
    for field in PA_PRIORITY:
        src=pd.to_numeric(z[field],errors="coerce")
        valid=src.between(45,115)&np.isnan(p)
        p[valid.to_numpy()]=src.loc[valid].to_numpy()*10
        p_label[valid.to_numpy()]=field+"_ORIGINAL_kPa"
    p=pd.Series(p,index=z.index)
    e_use=e.where(approved & e.between(-1e-7,75))
    goodp=p.notna()&p.gt(e_use+10)
    q=(EPS*e_use/(p-(1-EPS)*e_use)).where(goodp)
    rh=rh.where(approved)
    vpd_selected=v_new.where(approved)
    z["manual_decision"]=np.where(approved,MANUAL,"SOURCE_T_QC_NONZERO_UNAPPROVED")
    z["native_TA_F_original_preserved_C"]=T
    z["native_TA_F_original_QC"]=QC
    z["native_VPD_F_original_hPa"]=V
    z["new_VPD_hPa"]=vpd_selected
    z["new_RH_percent_at_TA_F"]=rh
    z["new_vapor_pressure_hPa"]=e_use
    z["new_PA_hPa"]=p
    z["new_PA_source"]=p_label
    z["new_QBOT_kgkg"]=q
    z["new_VPD_source"]=np.where(inconsistent,
           "TRANSFER_ERA_SATURATION_DEFICIT_FRACTION_TO_NATIVE_T",
           np.where(approved,"ORIGINAL_VPD_F_UNCHANGED",
                    "NOT_APPROVED_NONZERO_T_QC"))
    z["original_VPD_value_changed"]=inconsistent
    z["original_ERA_VPD_self_invalid_32_but_kept_with_tower_T"]=list(
        (str(ts),str(row)) in manual32 for ts,row in zip(
            z.tower_local_start,z.source_csv_row))
    z["temperature_modified"]=False
    z["original_FLUXNET_modified"]=False
    z["DATM_cime_netcdf_modified"]=False
    z["active_model_forcing_approved"]=False
    z["nonQC0_tower_temperature_science_hold"]=~approved
    z["qbot_requires_original_source_pressure"]=approved & ~goodp
    if (int(z.original_VPD_value_changed.sum())!=1068 or
        int(z.original_ERA_VPD_self_invalid_32_but_kept_with_tower_T.sum())!=32 or
        int(z.nonQC0_tower_temperature_science_hold.sum())!=N_NOT_QC0):
        raise ValueError("Approved manual decision source-row population changed")
    if len(pa_columns)==0:
        print("STAGE85 CAUTION: original source lacks PA_F and PA_ERA; derived QBOT remains missing")
    return z

def write(z,stage84,spec,inventory,signed):
    out=REPORT/("stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Original temperature permanently preserved; humidity candidate only.\n")
    selected=[
      "tower_local_start","source_csv_row","native_TA_F_original_preserved_C",
      "native_TA_F_original_QC","native_VPD_F_original_hPa","native_T_ERA",
      "native_VPD_ERA","new_VPD_hPa","new_RH_percent_at_TA_F",
      "new_vapor_pressure_hPa","new_PA_hPa","new_PA_source",
      "new_QBOT_kgkg","new_VPD_source","manual_decision",
      "original_VPD_value_changed",
      "original_ERA_VPD_self_invalid_32_but_kept_with_tower_T",
      "nonQC0_tower_temperature_science_hold","qbot_requires_original_source_pressure",
      "temperature_modified","active_model_forcing_approved"]
    if not set(selected)<=set(z.columns):
        raise ValueError("Source output required column missing")
    files={
      "17568_Ho1_2000_tower_T_preserved_humidity_candidate.csv":z[selected],
      "1068_Ho1_2000_VPD_adjusted_no_temperature_change.csv":z.loc[
          z.original_VPD_value_changed,selected],
      "32_Ho1_2000_manual_T_keep_original_VPD_unchanged.csv":z.loc[
          z.original_ERA_VPD_self_invalid_32_but_kept_with_tower_T,selected],
      "274_Ho1_2000_nonQC0_temperature_source_HOLD.csv":z.loc[
          z.nonQC0_tower_temperature_science_hold,selected]
    }
    checksums={}
    for name,df in files.items():
        f=out/name;df.to_csv(f,index=False);checksums[name]=sha(f)
    if sha(Path(spec["file"]))!=spec["sha256"]:
        raise ValueError("Original FLUXNET changed mid-candidate generation")
    report={
        "schema":"STAGE85_MANUAL_TOWER_TEMP_PRESERVED_HO1_2000_HUMIDITY_CANDIDATE_v1",
        "manual_reviewer_decision":MANUAL,
        "manual_decision_scope":"US-Ho1 2000 native TA_F measured-source QC0: KEEP; no ERA5 replacement",
        "original_native_halfhour_count":N,
        "original_measured_T_QC0_preserved_count":N_TQC0,
        "ERA5_large_delta_505_T_QC0_operator_manually_keep":True,
        "original_tower_temperature_changed_count":0,
        "VPD_modified_humidity_only_count":1068,
        "VPD_original_unchanged_ERA_self_32_count":32,
        "nonQC0_original_T_retained_but_science_HOLD_count":274,
        "qbot_source_pressure_available_QC0":int(
             z.loc[z.native_TA_F_original_QC.eq(0),"new_QBOT_kgkg"].notna().sum()),
        "qbot_source_pressure_missing_QC0":int(z.qbot_requires_original_source_pressure.sum()),
        "humidity_transform":"Original VPD retained when already compatible with source T; for 1068 incompatible, transfer ERA VPD/eswater(T_ERA) ratio to eswater(original measured T)",
        "relative_humidity_is_derived_not_measured":True,
        "pressure_PA_F_then_PA_ERA_kPa_to_hPa":True,
        "no_synthetic_pressure_used":True,
        "temperature_values_native_source_preserved":True,
        "other_years_or_sites_unaffected":True,
        "original_Ho1_BZS_16874_humidity_review_historical_manifest_untouched":True,
        "original_15199_numeric_humidity_shadows_untouched":True,
        "original_1675_temperature_HOLD_historical_manifest_untouched":True,
        "other_stage64_9389_candidates_untouched":True,
        "active_forcing_or_DATM_approved":False,
        "original_source_and_ERA5_files_modified":False,
        "source_SHA256":{
            "stage83_code_git_blob":BLOB83,
            "original_Ho1_FLUXNET_HH":spec["sha256"],
            "Stage49_primary_inventory":sha(inventory),
            "Stage84_source_manifest":sha(S84/"stage84_source_science_manifest.json"),
            "Stage84_32_source_rows":sha(S84/S84_CASES)},
        "outputs_SHA256":checksums
    }
    (out/"stage85_source_decision_manifest.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE85 MANUAL DECISION APPLIED | original tower T unchanged 17568/17568; QC0 approved 17294")
    print("STAGE85 ORIGINAL VPD RETAINED FOR 32 ERA-SELF JAN SOURCE CASES")
    print("STAGE85 HUMIDITY-ONLY SATURATION-FRACTION REMAP 1068 QC0 HH; tower T never modified")
    print("STAGE85 NONQC0 ORIGINAL T SCIENCE HOLD 274")
    print("STAGE85 QBOT AVAILABLE QC0",
         report["qbot_source_pressure_available_QC0"],
         "MISSING",report["qbot_source_pressure_missing_QC0"])
    print("REPORT",out)
    print("STAGE85 CANDIDATE CREATED | new isolated CSV only; no formal DATM forcing/model jobs")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply-manual-decision",required=True,choices=[MANUAL])
    a=p.parse_args()
    raw,orig32,spec,inv,_,signed,module=sources()
    p,available=pressure_year(spec)
    candidate=create(raw,orig32,p,available)
    write(candidate,orig32,spec,inv,signed)

if __name__=="__main__":
    main()

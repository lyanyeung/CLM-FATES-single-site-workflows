#!/usr/bin/env python3
"""Stage83 | original US-Ho1 2000 VPD_F_QC2 ERA provenance / T consistency.

Read-only native-source science audit; user has Stage82 AUDIT PASS.
FLUXNET FULLSET HH official codes: VPD_F_QC=0 measured, 1 good gap-fill,
2 downscaled from ERA; VPD_F consolidates VPD_F_MDS and VPD_ERA.
Source TA_F_QC=0 measured. Therefore all-HH VPD_F_QC2 plus many
source TA_F_QC0 is scientifically IMPORTANT to establish, not to
automatically 'fix' a measured tower temperature.

Strictly verify SHA of six completed Stage82 outputs, original Stage82
code, physical primary FLUXNET HH source, original Stage49 inventory.
Read original 2000 HH VPD_F, VPD_F_QC, TA_F, TA_F_QC, TA_ERA, optional
VPD_ERA, VPD_F_MDS, VPD_F_MDS_QC, TA_F_MDS, TA_F_MDS_QC.
Compare every primary source row/time/TA_F/TA_ERA/VPD_F/QC with Stage82
source-provenance data. Do NOT infer optional fields if unavailable.

Then test source VPD_F vs native VPD_ERA (when available) and compare
saturation vapour pressure over WATER from original measured TA_F vs
ERA-derived TA_ERA. VPD_F > es(T) is a mathematical inconsistency for
same air mass/source T/humidity pair, not proof of fault in either
unmatched observation (especially cold canopy vs reanalysis).
Source air pressure, ice-vs-water, original FLUXNET product calibration,
heterogeneous station and time convention remain science caveats.

--self-test: source-free physical and schema assertions.
--check: source/report/primary file SHA and exact row identity; no writes.
--audit: new isolated diagnostic report only. No source or model changes.

Official FLUXNET variable page:
https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/
"""
import argparse,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

HOME=Path.home()
B="examples/AmeriFlux_MultiSite_10_Batch02"
PARENT=HOME/"CLM-FATES-single-site-workflows"/B/"scripts/stage82/82_Ho1_2000_full_year_bidirectional_T_VPD_source_lineage_audit.py"
PARENT_BLOB="cf4cbfcf80004548f9ce48af3edd1e1e5c5d3abb"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
STAGE82=REPORT/"stage82_Ho1_2000_full_year_bidirectional_native_T_VPD_source_QC_20261025T193617Z_ba9cfa2a"
YEAR="17568_original_Ho1_2000_T_VPD_QC_NOAA_native_source_triage.csv"
S61=REPORT/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
N=17568
COLD=1554
WARM=2518
QC0=17294
NOAA=17140
SCIENCE="QC2_DOWNSCALED_FROM_ERA_PER_FLUXNET_FULLSET_HH"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def blob(path):
    f=Path(path)
    if f.is_symlink() or not f.is_file():
        raise ValueError("Stage82 pinned code missing/symlinked")
    b=f.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def asnumber(x):
    z=pd.to_numeric(x,errors="coerce")
    return z.mask(z.le(-9990))

def es_water(t):
    return 6.112*np.exp(17.67*t/(t+243.5))

def schema_check():
    if blob(PARENT)!=PARENT_BLOB:
        raise ValueError("Stage82 completed source code Git blob changed")
    mfile=STAGE82/"stage82_source_science_manifest.json"
    if (STAGE82/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage82 original science report incomplete")
    m=json.loads(mfile.read_text())
    assert_science={
        "schema":"STAGE82_HO1_2000_NATIVE_QC0_T_NOAA_BIDIRECTIONAL_VPD_QC_SOURCE_TRIAGE_v1",
        "source_full_HH":N,
        "source_measured_native_T_QC0":QC0,
        "source_QC0_noaa_matched":NOAA,
        "NOAA_warmer_than_Ho1_gt8C_HH":COLD,
        "NOAA_colder_than_Ho1_gt8C_HH":WARM,
        "source_505_stage74_selected_cases":505,
        "source_1069_original_VPD_hard_HH":1069,
        "source_QC0_gt8C_run_count":289,
        "native_FLUXNET_TA_ERA_is_processed_not_independent_source":True,
        "native_VPD_water_es_physics_only_not_replacement_approval":True,
        "historical_BIF_UTC_offset_approved":False,
        "original_T_replacement_approved":False,
        "original_VPD_replacement_approved":False,
        "approved_for_DATM":False,
        "original_humidity_numeric_shadow_15199_unchanged":True,
        "original_T_HOLDs_1675_unchanged":True,
        "original_humidity_HOLDs_16874_unchanged":True,
        "previous_stage64_other_9389_candidates_untouched":True
    }
    for key,val in assert_science.items():
        if m.get(key)!=val:
            raise ValueError("Original Stage82 source scientific contract changed: "+key)
    if m.get("source_SHA256",{}).get("stage81_script_gitblob")!=(
        "6e584c3e446e6637e8dbdad3241a278d15c0f415"):
        raise ValueError("Stage82 original Stage81 input script pin changed")
    needed={
       YEAR,
       "Ho1_2000_month_original_T_signed_NOAA_VPD_QC_summary.csv",
       "Ho1_2000_source_VPD_QC_by_signed_T_difference.csv",
       "Ho1_2000_original_TA_ERA_support_context_by_signed_T_difference.csv",
       "Ho1_2000_289_cold_warm_source_regime_TA_ERA_VPD_evidence.csv",
       "Ho1_2000_original_QC0_T_30min_source_residual_direction_transitions.csv"
    }
    if set(m.get("outputs_SHA256",{}))!=needed:
        raise ValueError("Original Stage82 output files do not match original audit")
    for name,digest in m["outputs_SHA256"].items():
        if sha(STAGE82/name)!=digest:
            raise ValueError("Stage82 source output SHA changed: "+name)
    x=pd.read_csv(STAGE82/YEAR,dtype={
        "tower_local_start":str,"source_csv_row":str},low_memory=False)
    cols={"tower_local_start","source_csv_row","TA_C","TA_QC",
       "original_TA_ERA_C","original_VPD_F","original_VPD_F_QC",
       "native_VPD_hPa","science_group",
       "original_2000_hard_VPD",
       "original_505_T_delta_selected",
       "NOAA_minus_original_Ho1_T_C",
       "historical_UTC_approved","approved_for_DATM"}
    if not cols.issubset(x.columns):
        raise ValueError("Stage82 source native field set changed "+str(cols-set(x.columns)))
    if len(x)!=N or x.tower_local_start.duplicated().any() or x.source_csv_row.duplicated().any():
        raise ValueError("Year-2000 native source row identity changed")
    if not pd.DatetimeIndex(pd.to_datetime(x["tower_local_start"],format="%Y%m%d%H%M")).equals(
        pd.date_range("2000-01-01","2000-12-31 23:30",freq="30min")):
        raise ValueError("Stage82 whole-year original 30min time series changed")
    for flag in ("historical_UTC_approved","approved_for_DATM"):
        if x[flag].astype(str).str.lower().eq("true").any():
            raise ValueError("Stage82 source approval changed")
    if not x["original_VPD_F_QC"].astype(float).eq(2).all():
        raise ValueError("Stage82 original 2000 VPD_F_QC isn't exactly QC2 as observed")
    if not x["science_group"].value_counts().to_dict()=={
        "NOAA_WARMER_HO1_COLDER_GT8C":COLD,
        "NOAA_COLDER_HO1_WARMER_GT8C":WARM,
        "WITHIN_8C_OF_NOAA":13068,
        "NO_NATIVE_QC0_OR_NO_NOAA_QC_MATCH":428}:
        raise ValueError("Stage82 source original temperature groups changed")
    return x,m

def original_primary():
    m61=json.loads((S61/"coverage_manifest.json").read_text())
    if m61.get("schema")!="STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1" or m61.get("original_hard_total")!=26332:
        raise ValueError("Stage61 original primary source inventory population changed")
    m49=json.loads((Path(m61["stage49_source"])/"provenance_and_hold.json").read_text())
    inv=Path(m49["inventory"]).resolve(strict=True)
    if sha(inv)!=m49["inventory_sha256"]:
        raise ValueError("Stage49 original source inventory modified")
    specs=[row for row in json.loads(inv.read_text())["completed"]
           if row.get("site")=="US-Ho1" and not str(row.get("source","")).startswith("ERA5")]
    if len(specs)!=1:
        raise ValueError("US-Ho1 original source file inventory ambiguous")
    spec=specs[0]
    f=Path(spec["file"])
    if (f.is_symlink() or not f.is_file() or
        sha(f)!=spec["sha256"] or
        m49["primary_sha256_by_site"].get("US-Ho1")!=spec["sha256"]):
        raise ValueError("Original Ho1 FLUXNET source FILE SHA changed")
    h=set(pd.read_csv(f,nrows=0).columns)
    selected={
      "native_T":spec["columns"]["TA"],
      "native_T_QC":spec["qc_columns"]["TA"],
      "native_VPD":spec["columns"]["VPD"],
      "native_VPD_QC":spec["qc_columns"]["VPD"],
      "native_T_ERA":"TA_ERA",
      "native_VPD_ERA":"VPD_ERA",
      "native_VPD_MDS":"VPD_F_MDS",
      "native_VPD_MDS_QC":"VPD_F_MDS_QC",
      "native_T_MDS":"TA_F_MDS",
      "native_T_MDS_QC":"TA_F_MDS_QC"
    }
    required={"TIMESTAMP_START",selected["native_T"],selected["native_T_QC"],
              selected["native_VPD"],selected["native_VPD_QC"],"TA_ERA"}
    if not required.issubset(h):
        raise ValueError("Primary source lacks original TA/TA_ERA/VPD/QC: "+str(required-h))
    return spec,inv,selected,h

def original_2000(spec,mapping,header):
    f=Path(spec["file"])
    cols=["TIMESTAMP_START"]+list(dict.fromkeys(
        name for name in mapping.values() if name in header))
    rows=[];index=0
    for chunk in pd.read_csv(f,usecols=cols,dtype="string",chunksize=120000):
        t=chunk["TIMESTAMP_START"].str.strip()
        mask=t.str.startswith("2000",na=False).to_numpy(dtype=bool)
        if mask.any():
            z=chunk.loc[mask].copy()
            z["tower_local_start"]=t.loc[mask].astype(str)
            z["source_csv_row"]=np.arange(index+2,index+2+len(chunk))[mask].astype(str)
            for alias,col in mapping.items():
                z[alias]=asnumber(z[col]) if col in header else np.nan
            rows.append(z[["tower_local_start","source_csv_row"]+list(mapping)])
        index+=len(chunk)
    if not rows:raise ValueError("Original Ho1 2000 not found in primary file")
    z=pd.concat(rows,ignore_index=True)
    if len(z)!=N or z.tower_local_start.duplicated().any():
        raise ValueError("Original Ho1 2000 17568 source HH unexpectedly changed")
    return z

def compare_source(stage,raw):
    a=stage.copy()
    r=raw.copy()
    a["source_csv_row"]=a["source_csv_row"].astype(str)
    merged=a.merge(r,on=["tower_local_start","source_csv_row"],
        how="left",validate="one_to_one",indicator=True)
    if len(merged)!=N or not merged["_merge"].eq("both").all():
        raise ValueError("Stage82 original native source physical CSV row/time mismatch")
    compares=[
        ("TA_C","native_T",False),
        ("TA_QC","native_T_QC",False),
        ("original_VPD_F","native_VPD",True),
        ("original_VPD_F_QC","native_VPD_QC",False),
        ("original_TA_ERA_C","native_T_ERA",True)
    ]
    for a_name,b_name,missing in compares:
        left=asnumber(merged[a_name]) if missing else pd.to_numeric(
            merged[a_name],errors="coerce")
        right=merged[b_name]
        same=(np.isclose(left,right,rtol=0,atol=0.00011,equal_nan=True))
        if not bool(same.all()):
            raise ValueError("Stage82 original source independent numeric mismatch "+
                a_name+" vs "+b_name+" rows="+str(int((~same).sum())))
    if (not merged["native_VPD_QC"].eq(2).all() or
        not merged["native_T_QC"].eq(0).sum()==QC0):
        raise ValueError("Original primary source QC0 tower T or all VPD QC2 changed")
    return merged.drop(columns="_merge")

def assess(merged,header):
    z=merged.copy()
    z["source_month"]=z["tower_local_start"].str[:6]
    z["science_VPD_QC_provenance"]=SCIENCE
    z["native_VPD_ERA_column_present"]="VPD_ERA" in header
    z["native_VPD_MDS_column_present"]="VPD_F_MDS" in header
    z["native_VPD_MDS_QC_column_present"]="VPD_F_MDS_QC" in header
    z["original_VPD_F_hPa"]=z["native_VPD"]
    z["source_VPD_ERA_diff_hPa"]=z["native_VPD"]-z["native_VPD_ERA"]
    both=z["native_VPD"].notna()&z["native_VPD_ERA"].notna()
    z["source_VPD_F_ERA_numeric_pair"]=both
    z["VPD_F_equals_source_VPD_ERA_1e_minus_4_hPa"]=(
        both&z["source_VPD_ERA_diff_hPa"].abs().le(1e-4))
    z["es_water_from_original_T_QC0_hPa"]=es_water(
        z["native_T"].where(z["native_T_QC"].eq(0)))
    z["es_water_from_original_T_ERA_hPa"]=es_water(
        z["native_T_ERA"].where(z["native_T_ERA"].between(-80,65)))
    physical=z["native_VPD"].notna()&z["native_T_QC"].eq(0)
    era_physical=z["native_VPD"].notna()&z["native_T_ERA"].between(-80,65)
    z["VPD_gt_es_at_native_QC0_T"]=physical&z["native_VPD"].gt(
        z["es_water_from_original_T_QC0_hPa"]+1e-8)
    z["VPD_gt_es_at_native_TA_ERA"]=era_physical&z["native_VPD"].gt(
        z["es_water_from_original_T_ERA_hPa"]+1e-8)
    z["VPD_source_mathematically_valid_for_T_ERA_not_QC0_T"]=(
        z["VPD_gt_es_at_native_QC0_T"]&
        ~z["VPD_gt_es_at_native_TA_ERA"]&
        era_physical)
    z["VPD_gt_es_at_both_source_T"]=(
        z["VPD_gt_es_at_native_QC0_T"]&
        z["VPD_gt_es_at_native_TA_ERA"])
    z["source_original_VPD_F_QC2_means_downscaled_ERA"]=True
    z["ERA_product_not_same_as_independent_CDS_ERA5"]=True
    z["VPD_T_physics_source_mismatch_not_auto_repair"]=True
    z["temperature_repair_approved"]=False
    z["VPD_repair_approved"]=False
    z["historical_BIF_UTC_approved"]=False
    z["approved_for_DATM"]=False
    if int(z["VPD_gt_es_at_native_QC0_T"].sum())!=1068:
        raise ValueError("Stage82 original annual 1068 measured-QC0 impossible VPD source records changed")
    if (not z["native_VPD_QC"].eq(2).all() or
        int(z["native_T_QC"].eq(0).sum())!=QC0 or
        len(z)!=N):
        raise ValueError("Source original QC2 VPD and measured-T annual census changed")
    return z

def summarize(z,group_cols):
    rows=[]
    for group,part in z.groupby(group_cols,sort=True,dropna=False):
        if not isinstance(group,tuple):group=(group,)
        both=part.loc[part["source_VPD_F_ERA_numeric_pair"]]
        entry={**dict(zip(group_cols,group)),
         "original_HH":len(part),
         "source_VPD_F_QC2_HH":int(part["native_VPD_QC"].eq(2).sum()),
         "source_T_F_QC0_HH":int(part["native_T_QC"].eq(0).sum()),
         "original_VPD_F_ERA_numeric_pairs":len(both),
         "original_VPD_F_equals_VPD_ERA_HH":int(
             part["VPD_F_equals_source_VPD_ERA_1e_minus_4_hPa"].sum()),
         "VPD_F_ERA_median_signed_diff_hPa":float(
             both["source_VPD_ERA_diff_hPa"].median()) if len(both) else np.nan,
         "VPD_F_ERA_max_abs_diff_hPa":float(
             both["source_VPD_ERA_diff_hPa"].abs().max()) if len(both) else np.nan,
         "native_VPD_F_MDS_QC0_HH":int(part["native_VPD_MDS_QC"].eq(0).sum()),
         "native_VPD_F_MDS_QC1_HH":int(part["native_VPD_MDS_QC"].eq(1).sum()),
         "native_VPD_F_MDS_QC2_HH":int(part["native_VPD_MDS_QC"].eq(2).sum()),
         "native_VPD_F_MDS_QC3_HH":int(part["native_VPD_MDS_QC"].eq(3).sum()),
         "VPD_gt_es_water_original_QC0_T":int(part["VPD_gt_es_at_native_QC0_T"].sum()),
         "VPD_gt_es_water_original_T_ERA":int(part["VPD_gt_es_at_native_TA_ERA"].sum()),
         "VPD_mismatch_reconciled_by_T_ERA_mathematical":int(
             part["VPD_source_mathematically_valid_for_T_ERA_not_QC0_T"].sum()),
         "VPD_gt_es_water_both_T_orig_and_ERA":int(
             part["VPD_gt_es_at_both_source_T"].sum()),
         "NOAA_airport_source_temp_not_ground_truth":True,
         "original_Ho1_measured_T_not_automatically_faulty":True,
         "DATM_approved":False}
        rows.append(entry)
    return pd.DataFrame(rows)

def self_test():
    assert N==366*48 and QC0==17294 and NOAA==17140
    assert 1554+2518+13068==17140
    assert abs(es_water(-10)-2.867)<.05
    assert abs(es_water(20)-23.37)<.1
    assert SCIENCE=="QC2_DOWNSCALED_FROM_ERA_PER_FLUXNET_FULLSET_HH"
    print("STAGE83 SELF-TEST PASS | official VPD_F_QC2 ERA source definition, raw full-year VPD_F vs VPD_ERA and T physics; no writes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","audit"):g.add_argument("--"+mode,action="store_true")
    args=p.parse_args()
    if args.self_test:return self_test()
    d,m=schema_check()
    spec,inventory,fields,header=original_primary()
    native=original_2000(spec,fields,header)
    merged=compare_source(d,native)
    if args.check:
        print("STAGE83 CHECK PASS | Stage82 6 SHA outputs, Stage49 physical source SHA and exact 17568 native row QC2 VPD/QC0 TA; NO NETWORK/WRITES")
        print("STAGE83 PRIMARY SOURCE",spec.get("source"),"NATIVE VPD column",fields["native_VPD"],
              "VPD ERA column present","VPD_ERA" in header,
              "VPD MDS column present","VPD_F_MDS" in header)
        return
    z=assess(merged,header)
    z["original_source_month"]=z["tower_local_start"].str[:6]
    monthly=summarize(z,["original_source_month"])
    regime=summarize(z,["science_group"])
    bymonthregime=summarize(z,["original_source_month","science_group"])
    physics=z.loc[z["VPD_gt_es_at_native_QC0_T"]].copy()
    if (len(physics)!=1068 or
        regime.original_HH.sum()!=N or
        monthly.original_HH.sum()!=N or
        bymonthregime.original_HH.sum()!=N):
        raise ValueError("Original full year source QCs/eswater/month group counts changed")
    print("STAGE83 PRIMARY SOURCE",spec.get("source"),"SHA256",spec["sha256"])
    print("STAGE83 SOURCE PRESENCE",{
       "VPD_ERA":"VPD_ERA" in header,
       "VPD_F_MDS":"VPD_F_MDS" in header,
       "VPD_F_MDS_QC":"VPD_F_MDS_QC" in header,
       "TA_F_MDS":"TA_F_MDS" in header})
    print("STAGE83 ORIGINAL VPD_F_QC2",int(z.native_VPD_QC.eq(2).sum()),
          "/",N,"TA_F_QC0",int(z.native_T_QC.eq(0).sum()),"/",N)
    print("STAGE83 NATIVE VPD_F equals source VPD_ERA",int(
        z["VPD_F_equals_source_VPD_ERA_1e_minus_4_hPa"].sum()),"/",
        int(z["source_VPD_F_ERA_numeric_pair"].sum()))
    print("STAGE83 PRIMARY WATER SATURATION SOURCE PHYSICS COUNTS",{
       "VPD_gt_es_QC0_T":int(z.VPD_gt_es_at_native_QC0_T.sum()),
       "VPD_gt_es_TA_ERA":int(z.VPD_gt_es_at_native_TA_ERA.sum()),
       "original_T_QC0_issue_but_not_TA_ERA":int(
           z.VPD_source_mathematically_valid_for_T_ERA_not_QC0_T.sum()),
       "issue_with_both_native_T_and_T_ERA":int(
           z.VPD_gt_es_at_both_source_T.sum())})
    print("STAGE83 ORIGINAL SOURCE SCIENCE GROUPS")
    print(regime.to_string(index=False))
    print("STAGE83 MONTHLY PHYSICS/SOURCE PROVENANCE")
    print(monthly.to_string(index=False))
    print("STAGE83 IMPORTANT: VPD_F_QC2 IS ERA DOWNSCALED, NOT A MEASURED VPD")
    print("STAGE83 NO AUTOMATIC SOURCE VPD, TA OR CLM-FATES INPUT APPROVAL")
    dst=REPORT/("stage83_Ho1_2000_original_VPD_QC2_ERA_T_context_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dst.mkdir(parents=True,exist_ok=False)
    incomplete=dst/"INCOMPLETE_DO_NOT_USE"
    incomplete.write_text("Source science only; no original values or forcing modified.\n")
    outputs={}
    for name,df in {
       "17568_native_2000_Ho1_VPD_F_QC2_VPD_ERA_T_ERA_original_lineage.csv":z,
       "2000_original_VPD_ERA_T_QC0_T_ERA_source_month.csv":monthly,
       "2000_original_VPD_ERA_T_by_NOAA_signed_T_regime.csv":regime,
       "2000_original_VPD_ERA_T_month_by_NOAA_signed_T_regime.csv":bymonthregime,
       "1068_Ho1_2000_original_QC0_T_VPD_gt_eswater_ERA_comparison.csv":physics
    }.items():
        f=dst/name;df.to_csv(f,index=False);outputs[name]=sha(f)
    if sha(STAGE82/YEAR)!=m["outputs_SHA256"][YEAR] or sha(Path(spec["file"]))!=spec["sha256"]:
        raise ValueError("Source changed during writing Stage83 report")
    manifest={
       "schema":"STAGE83_HO1_2000_PRIMARY_VPD_QC2_ERA_T_PROVENANCE_v1",
       "original_source_HH":N,
       "source_VPD_F_QC2_ERA_downscaled_HH":N,
       "original_measured_T_QC0_HH":QC0,
       "original_NOAA_QC_matched_T_HH":NOAA,
       "native_QC0_VPD_gt_eswater_source_HH":1068,
       "primary_source_product":spec.get("source"),
       "source_original_columns":fields,
       "source_VPD_ERA_column_present":"VPD_ERA" in header,
       "source_VPD_F_MDS_column_present":"VPD_F_MDS" in header,
       "science_explanation":"QC2=ERA-downscaled per FLUXNET official variable codes; physically inconsistent VPD when combined with differently sourced air T requires provenance investigation",
       "ERA_VPD_not_independent_tower_observation":True,
       "NOAA_not_forest_canopy_truth":True,
       "original_temperature_source_replacement_approved":False,
       "original_VPD_source_replacement_approved":False,
       "historical_BIF_UTC_offset_approved":False,
       "approved_for_DATM":False,
       "original_16874_Ho1_BZS_hard_HOLD_unchanged":True,
       "original_15199_humidity_shadow_numerical_only_unchanged":True,
       "original_1675_temperature_HOLD_unchanged":True,
       "prior_stage64_9389_other_candidates_untouched":True,
       "source_SHA256":{
          "stage82_script_git_blob":PARENT_BLOB,
          "stage82_source_manifest":sha(STAGE82/"stage82_source_science_manifest.json"),
          "stage82_full_year_source":sha(STAGE82/YEAR),
          "stage49_primary_source_inventory":sha(inventory),
          "Ho1_original_FLUXNET_primary_HH":spec["sha256"]},
       "outputs_SHA256":outputs,
       "no_original_source_NOAA_CDS_forcing_DATM_CIME_Slurm_changes":True}
    (dst/"stage83_source_science_manifest.json").write_text(json.dumps(
        manifest,indent=2,sort_keys=True)+"\n")
    incomplete.unlink()
    print("STAGE83 AUDIT PASS | independently checked 17568 raw source VPD_F_QC2 provenance and original/ERA air T physics; no model approval")
    print("REPORT",dst)
    print("NO ORIGINAL TOWER, NOAA, CDS, STAGE49-82, FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage12aj (READ ONLY): exactly seven latest US-Kon / US-NR1 nonhumidity
source-row failures, source QC and +/-2 native HH context. Verifies signed
Stage12ai ten-site status and Stage07 original manifests, original Kon
Stage12ah and NR1 Stage12af SHA-sealed outputs. No repair or model access.
--self-test NO reads/writes; --check full audit NO writes;
--run full audit + independent SHA-sealed report only.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
V="batch03-stage12aj-v1-20261026-seven-nonhumidity-source-context"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AI=R/"reports/stage12ai_ten_site_selected_sources_current_20261026T030050Z_7717ee91"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
AI_TABLE="ten_site_current_source_native_selected_stage_status.csv"
EXPECTED={"US-Kon":3,"US-NR1":4}
MET=("TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE")
LOOKUP={"TBOT":"TA_F","TA_USE":"TA_F","PSRF":"PA_F",
        "FSDS":"SW_IN_F","FLDS":"LW_IN_F","WIND":"WS_F",
        "PRECTmms":"P_F"}
def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():raise ValueError("Missing/symlink protected source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def selftest():
    assert set(LOOKUP)==set(MET)
    assert sum(EXPECTED.values())==7
    assert (pd.Timestamp("2022-09-10 08:00")+pd.Timedelta(minutes=30)).strftime("%Y%m%d%H%M")=="202209100830"
    print("STAGE12AJ SELF-TEST PASS: Kon3 + NR1 4 original nonhumidity QC, native half-hour context; NO WRITES",flush=True)
def native(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def audit():
    a=json.loads(safe(AI/"stage12ai_ten_site_status_SHA_receipt.json").read_text())
    if not(a.get("site_count")==10 and a.get("science_only") is True
           and a.get("post_v5_approved_sites")==0
           and a.get("DATM_ready_sites")==0 and a.get("spinup_authorized_sites")==0
           and a.get("output_SHA256",{}).get(AI_TABLE)==sha(AI/AI_TABLE)):
        raise ValueError("Latest ten site Stage12ai signed receipt changed")
    tab=pd.read_csv(safe(AI/AI_TABLE),dtype={"site":str},low_memory=False)
    if len(tab)!=10 or set(tab.site)!={
       "US-Kon","US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj",
       "US-MtB","US-NC2","US-NR1","US-NR3"}:
        raise ValueError("Stage12ai exact 10 stations changed")
    manifest=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec={x["site"]:x for x in manifest["sites"]}
    pins={str(Path(k).resolve()):h for k,h in manifest["input_sha256"].items()}
    rows=[]
    science_keys=[]
    for site,expected in EXPECTED.items():
        entry=tab.loc[tab.site.eq(site)]
        if len(entry)!=1 or str(entry.iloc[0].selected_stage)!=(
                  "Stage12ah" if site=="US-Kon" else "Stage12af"):
            raise ValueError("Wrong latest approved-only successor selected "+site)
        entry=entry.iloc[0]
        candidate=safe(Path(str(entry.input_path)))
        if sha(candidate)!=str(entry.sha256):raise ValueError("Selected successor SHA changed "+site)
        raw=safe(spec[site]["primary"])
        era=safe(spec[site]["era"])
        for p in (raw,era):
            if sha(p)!=pins.get(str(p.resolve())):
                raise ValueError("Original Stage07 tower or paired ERA SHA changed "+site+" "+str(p))
        x=pd.read_csv(candidate,dtype={"time":str},low_memory=False)
        k=native(x.time)
        if k.duplicated().any():raise ValueError("Duplicate original source-native candidate time "+site)
        x.index=k
        vals=x[list(MET)].apply(pd.to_numeric,errors="coerce")
        missing=~np.isfinite(vals.to_numpy(dtype=float))
        badrows=np.flatnonzero(missing.any(axis=1))
        if len(badrows)!=expected or int(entry.nonhumidity_field_missing_rows)!=expected:
            raise ValueError("Unexpected corrected Kon/NR1 nonhumidity row count "+site+" "+str(len(badrows)))
        local_keys=set()
        for i in badrows:
            at=pd.to_datetime(k.iloc[i],format="%Y%m%d%H%M")
            for j in (-2,-1,0,1,2):
                local_keys.add((at+pd.Timedelta(minutes=30*j)).strftime("%Y%m%d%H%M"))
        original=pd.read_csv(raw,dtype={"TIMESTAMP_START":str},low_memory=False)
        original=original.loc[original.TIMESTAMP_START.isin(local_keys)]
        matched=original.set_index("TIMESTAMP_START",verify_integrity=True)
        er=pd.read_csv(era,dtype={"TIMESTAMP_START":str},low_memory=False)
        er=er.loc[er.TIMESTAMP_START.isin(local_keys)].set_index("TIMESTAMP_START",verify_integrity=True)
        if not local_keys<=set(matched.index) or not local_keys<=set(er.index):
            raise ValueError("Missing exact native source or paired ERA neighbor "+site)
        common_native=set(k)
        if not local_keys<=common_native:
            raise ValueError("Missing context native forcing "+site)
        for i in badrows:
            center=k.iloc[i]
            fields=[f for f in MET if bool(missing[i,MET.index(f)])]
            science_keys.append({"site":site,"native_key":center,"missing_fields":",".join(fields)})
            for offset in (-2,-1,0,1,2):
                key=(pd.to_datetime(center,format="%Y%m%d%H%M")+
                    pd.Timedelta(minutes=30*offset)).strftime("%Y%m%d%H%M")
                j=np.flatnonzero(k.eq(key))
                if len(j)!=1:raise ValueError("Missing candidate exact native context "+site+" "+key)
                t=x.iloc[int(j[0])]
                o=matched.loc[key];e=er.loc[key]
                row={"site":site,"center_native_key":center,
                     "native_key":key,"half_hour_offset":offset,
                     "center_originally_missing_fields":",".join(fields),
                     "candidate_VPD_USE":t.get("VPD_USE",np.nan),
                     "candidate_QBOT":t.get("QBOT",np.nan)}
                for met in MET:
                    originalfield=LOOKUP[met]
                    row["selected_"+met]=t.get(met,np.nan)
                    row["original_"+originalfield]=o.get(originalfield,np.nan)
                    row["original_"+originalfield+"_QC"]=o.get(originalfield+"_QC",np.nan)
                    row["original_companion_"+originalfield.replace("_F","")+"_ERA"]=e.get(originalfield.replace("_F","")+"_ERA",np.nan)
                rows.append(row)
    review=pd.DataFrame(rows)
    original=pd.DataFrame(science_keys)
    if len(original)!=7 or len(review)!=35 or original.duplicated(["site","native_key"]).any():
        raise ValueError("Seven exact missing source rows not recovered")
    return original,review
def main():
    pa=argparse.ArgumentParser()
    g=pa.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):g.add_argument("--"+opt,action="store_true")
    args=pa.parse_args()
    print("STAGE12AJ SEVEN KON/NR1 NONHUMIDITY CAUSES / NATIVE QC0 QC1 CONTEXT | "+V,flush=True)
    selftest()
    if args.self_test:return
    missing,neighbors=audit()
    print("\n========= EXACT 7 NONHUMIDITY MISSING TIMES AND VARIABLES =========",flush=True)
    print(missing.to_string(index=False),flush=True)
    print("\n========= ALL 7 × FIVE NATIVE HALFHOURS: T, P, SW, LW, WIND, RAIN ORIGINAL vs SELECTED =========",flush=True)
    for site,key in zip(missing.site,missing.native_key):
        n=neighbors[(neighbors.site==site)&neighbors.center_native_key.eq(key)]
        present=["native_key","half_hour_offset","center_originally_missing_fields"]
        for f in MET:
            if f in str(missing.loc[(missing.site==site)&missing.native_key.eq(key),"missing_fields"].iloc[0]):
                present+=["selected_"+f,"original_"+LOOKUP[f],"original_"+LOOKUP[f]+"_QC"]
        if "original_TA_F" in n:present+=["original_TA_F","original_TA_F_QC"]
        print("\n"+site+" "+key+"\n"+n[list(dict.fromkeys(present))].to_string(index=False),flush=True)
    print("\nSTAGE12AJ CONCLUSION: zero new science approvals; seven preexisting nonhumidity row causes localized; Kon Stage12ah/NR1 Stage12af immutable; all model gates HOLD.",flush=True)
    if args.check:
        print("STAGE12AJ CHECK ONLY: NO WRITES.",flush=True);return
    out=R/"reports"/("stage12aj_7_selected_nonhumidity_exact_native_source_QC_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={"seven_nonhumidity_missing_native_site_field_ids.csv":missing,
             "35_surrounding_source_tower_QC_companion_ERA_and_selected_forcing.csv":neighbors}
    for name,df in outputs.items():df.to_csv(out/name,index=False)
    (out/"SCIENCE_REVIEW_ONLY_DO_NOT_USE_MODEL").write_text(
       "Read-only missing-variable source/QC audit. No force-filling of TBOT/PSRF/FSDS/FLDS/WIND/PRECTmms/TA_USE; no source timestamp edits; no CIME/DATM/spinup.\n")
    files=[*outputs,"SCIENCE_REVIEW_ONLY_DO_NOT_USE_MODEL"]
    (out/"stage12aj_seven_nonhumidity_SHA_receipt.json").write_text(
      json.dumps({"version":V,"seven_missing_event_rows":7,
             "Kon_missing_rows":3,"NR1_missing_rows":4,
             "post_v5_approved":False,"model_ready":False,
             "output_SHA256":{p:sha(out/p) for p in files}},indent=2)+"\n")
    print("STAGE12AJ SCIENCE REVIEW REPORT DIR:",out,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AJ STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

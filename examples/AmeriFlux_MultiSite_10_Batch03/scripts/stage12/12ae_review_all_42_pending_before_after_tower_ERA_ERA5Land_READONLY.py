#!/usr/bin/env python3
"""Stage12ae: original half-hour center and +-2 neighbours at ALL 75
Stage12g high-priority rows, with measured tower TA, original gapfilled VPD
and QC, original paired/native ERA, gridded ERA5-Land t2m/dewpoint RH and
at-tower-T VPD, original sealed Stage12g and existing authorized Stage12ac.

42 original pending rows = 34 Kon jump + 3 NR1 jump + 4 MtB ice +
1 Kon QC0 protector. Remaining 33 US-Me6 source jump positions have
operator-approved source policy but are NOT yet applied as 33 repairs.
Show all 42 pending centers AND exact native 30min +/-1 comparison in
terminal. Save all 75 x five-neighbour provenance, including all 33 Me6,
only when --run. Original data and science holds never modified.

CRITICAL: ERA5-Land native→UTC BIF offsets from original Stage10b are
UNAPPROVED hypotheses. ERA5-Land is distinct from original companion
FLUXNET TA_ERA / VPD_ERA. All candidate estimates are DIAGNOSTIC ONLY.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VERSION="batch03-stage12ae-v1-20261026-42-pending-33-approved-source-context"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
G=R/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
A=R/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
T_SCRIPT=BASE/"scripts/stage10/10b_audit_external_humidity_1924.py"
T_BLOB="0bb3b2657c6a79c8ead68d81354f6c0b526d930a"
LEDGER="2810_original_missing_year_source_review_after_stage12g.csv"
GRID_MANIFEST="new_external_ERA5Land_SHA_manifest.json"
AC_FILE="US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv"
AC_REC="stage12ac_user_approved_5HH_SHA_receipt.json"
SITE_COUNTS={"US-Kon":35,"US-NR1":3,"US-MtB":4,"US-Me6":33}
GROUPS={"HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA",
        "HOLD_ICE_SUPERSATURATION","HOLD_ORIGINAL_QC_OR_SITE_T_P"}
EXACT={"US-Kon":{"HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA":34,
                 "HOLD_ORIGINAL_QC_OR_SITE_T_P":1},
       "US-NR1":{"HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA":3},
       "US-MtB":{"HOLD_ICE_SUPERSATURATION":4},
       "US-Me6":{"HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA":33}}

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise ValueError("Missing/symlink source: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def blob(p):
    b=safe(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def es(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def ice(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))

def hh(k):
    return pd.Timestamp.strptime(str(k),"%Y%m%d%H%M") if hasattr(pd.Timestamp,"strptime") else pd.to_datetime(str(k),format="%Y%m%d%H%M")

def nativekey(ser):
    return ser.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def selftest():
    assert sum(SITE_COUNTS.values())==75
    assert 34+3+4+1==42 and set(GROUPS)=={
      "HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA",
      "HOLD_ICE_SUPERSATURATION","HOLD_ORIGINAL_QC_OR_SITE_T_P"}
    assert abs(float(es(18.96))-21.90527376971348)<1e-6
    assert float(ice(-8.0))<float(es(-8.0))
    offsets=[-2,-1,0,1,2]
    sample=[pd.Timestamp("2022-09-10 07:00")+pd.Timedelta(minutes=30*x) for x in offsets]
    assert all((sample[i+1]-sample[i]).seconds==1800 for i in range(4))
    print("STAGE12AE SELF-TEST PASS: 75 cases/42 pending, 30min neighbors and water/ice physics; NO WRITES",flush=True)

def verify():
    gr=json.loads(safe(G/"stage12g_research_only_sha_receipt.json").read_text())
    ar=json.loads(safe(A/AC_REC).read_text())
    if not(gr.get("original_233_physics_holds_untouched") is True and
           gr.get("INCOMPLETE_marker_present") is True and
           gr.get("Postv5_approved")==0 and gr.get("DATM_ready")==0 and
           gr.get("spinup_authorized")==0):
        raise ValueError("Signed original Stage12g input gate changed")
    if not (ar.get("version")=="batch03-stage12ac-v1-20261025-operator-approved-five-HH-ERA-RH"
            and ar.get("original_Stage12g_receipt_SHA256")==sha(G/"stage12g_research_only_sha_receipt.json")
            and ar.get("two_old_G_HOLDs_released_in_NEW_derived_overlay_only") is True
            and ar.get("Postv5_approved")==0 and ar.get("DATM_ready")==0):
        raise ValueError("Original verified Stage12ac approved overlay chain differs")
    if sha(A/AC_FILE)!=ar["output_SHA256"][AC_FILE]:
        raise ValueError("Operator-approved Stage12ac overlay changed")
    for file in (LEDGER,GRID_MANIFEST):
        if sha(G/file)!=gr["output_sha256"][file]:
            raise ValueError("Original G signed review/grid source SHA mismatch "+file)
    manifest=json.loads(safe(S/"exact_input_manifest.json").read_text())
    specs={x["site"]:x for x in manifest["sites"]}
    pins={str(Path(p).resolve()):x for p,x in manifest["input_sha256"].items()}
    for site in SITE_COUNTS:
        if site not in specs:raise ValueError("Stage07 site source missing "+site)
        for name in ("primary","era"):
            p=safe(specs[site][name])
            if sha(p)!=pins.get(str(p.resolve())):
                raise ValueError("Stage07 original site or paired ERA SHA changed "+site+" "+name)
    for site in SITE_COUNTS:
        name=site+"_STAGE12G_INCOMPLETE_NOLEAP.csv"
        if sha(G/name)!=gr["output_sha256"][name]:
            raise ValueError("Original G time-series SHA changed "+name)
    if blob(T_SCRIPT)!=T_BLOB:
        raise ValueError("Pinned Stage10b grid time and physics code missing/modified in user's local workflow repo")
    spec=importlib.util.spec_from_file_location("source_stage10b_12ae",T_SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return gr,ar,specs,mod

def audit():
    gr,ar,specs,stage10=verify()
    original=pd.read_csv(safe(G/LEDGER),
                         dtype={"site":str,"native_key":str},low_memory=False)
    events=original.loc[
       original.site.isin(SITE_COUNTS)&original.reason.isin(GROUPS)].copy()
    # Two historical original Stage12g Me6 holds were explicitly released in
    # the separately SHA-sealed Stage12ac approved derivative. They remain
    # in the IMMUTABLE old G ledger, but must not count as pending events.
    old_me6_approved={("US-Me6","201707040700"),("US-Me6","201707040730")}
    historical=events.loc[[ (str(x.site),str(x.native_key)) in old_me6_approved
       for x in events.itertuples(index=False)]]
    if (len(historical)!=2 or
        historical.reason.ne("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA").any()):
        raise ValueError("Original two explicitly approved Me6 holds missing or altered")
    events=events.loc[[ (str(x.site),str(x.native_key)) not in old_me6_approved
        for x in events.itertuples(index=False)]].copy()
    print("STAGE12AE EXACT SOURCE HISTORY: 77 G old cases minus 2 approved Stage12ac holds = 75 remaining; 42 pending + 33 Me6 policy",flush=True)
    if (len(events)!=75 or events.duplicated(["site","native_key"]).any()
        or events.site.value_counts().to_dict()!=SITE_COUNTS
        or events.groupby(["site","reason"]).size().to_dict()!=
           {(s,r):n for s,v in EXACT.items() for r,n in v.items()}):
        raise ValueError("Exactly original 75 Stage12g science cases not found")
    events.sort_values(["site","native_key"],inplace=True)
    events["audit_class"]=np.select(
       [events.site.eq("US-Me6"),
        events.reason.eq("HOLD_ICE_SUPERSATURATION"),
        events.reason.eq("HOLD_ORIGINAL_QC_OR_SITE_T_P")],
       ["ME6_POLICY_USER_APPROVED_NOT_YET_APPLIED_33",
        "MTB_CONDITIONAL_ICE_CHECK",
        "KON_ORIGINAL_QC0_PROTECT"],
       default="PENDING_MANUAL_VPD_EDGE")
    allrows=[]
    gridprovenance=json.loads(safe(G/GRID_MANIFEST).read_text())
    inputs=[]
    for site in sorted(SITE_COUNTS):
        e=events.loc[events.site.eq(site)].copy()
        keys=set()
        for key in e.native_key:
            t=pd.to_datetime(key,format="%Y%m%d%H%M")
            keys.update((t+pd.Timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
                        for i in (-2,-1,0,1,2))
        rawfile=safe(specs[site]["primary"]);erafile=safe(specs[site]["era"])
        required_raw=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
        optional_raw=["VPD_F_MDS","VPD_F_MDS_QC"]
        available=set(pd.read_csv(rawfile,nrows=0).columns)
        if not set(required_raw)<=available:
            raise ValueError("Missing essential tower/source QC fields for "+site)
        raw_cols=required_raw+[name for name in optional_raw if name in available]
        rr=pd.read_csv(rawfile,usecols=raw_cols,dtype={"TIMESTAMP_START":str},low_memory=False)
        rr=rr.loc[rr.TIMESTAMP_START.isin(keys)].copy()
        for name in optional_raw:
            if name not in rr:rr[name]=np.nan
        era=pd.read_csv(erafile,usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                        dtype={"TIMESTAMP_START":str},low_memory=False)
        era=era.loc[era.TIMESTAMP_START.isin(keys)].copy()
        gfile=G/(site+"_STAGE12G_INCOMPLETE_NOLEAP.csv")
        g=pd.read_csv(gfile,usecols=["time","VPD_USE","QBOT","TA_USE","PSRF"],
                      dtype={"time":str},low_memory=False)
        g["TIMESTAMP_START"]=nativekey(g.time)
        g=g.loc[g.TIMESTAMP_START.isin(keys)].copy()
        g.rename(columns={"VPD_USE":"original_Stage12g_VPD_hPa",
                          "QBOT":"original_Stage12g_QBOT_kgkg",
                          "TA_USE":"retained_tower_TA_USE_C","PSRF":"retained_PSRF_Pa"},inplace=True)
        if site=="US-Me6":
            overlay=pd.read_csv(A/AC_FILE,usecols=["time","VPD_USE","QBOT"],
                                dtype={"time":str},low_memory=False)
            overlay["TIMESTAMP_START"]=nativekey(overlay.time)
            overlay=overlay.loc[overlay.TIMESTAMP_START.isin(keys)].copy()
            overlay.rename(columns={"VPD_USE":"selected_after_12ac_VPD_hPa",
                                    "QBOT":"selected_after_12ac_QBOT_kgkg"},inplace=True)
            g=g.merge(overlay[["TIMESTAMP_START","selected_after_12ac_VPD_hPa",
                               "selected_after_12ac_QBOT_kgkg"]],
                      on="TIMESTAMP_START",validate="one_to_one")
        else:
            g["selected_after_12ac_VPD_hPa"]=g["original_Stage12g_VPD_hPa"]
            g["selected_after_12ac_QBOT_kgkg"]=g["original_Stage12g_QBOT_kgkg"]
        df=(pd.DataFrame({"TIMESTAMP_START":sorted(keys)})
            .merge(rr,on="TIMESTAMP_START",validate="one_to_one",how="left")
            .merge(era,on="TIMESTAMP_START",validate="one_to_one",how="left")
            .merge(g.drop(columns=["time"]),on="TIMESTAMP_START",
                   validate="one_to_one",how="left"))
        if df[["TA_F","retained_tower_TA_USE_C","retained_PSRF_Pa"]].isna().any().any():
            raise ValueError("Source context missing essential measured/retained tower T or P "+site)
        if not np.allclose(df.TA_F,df.retained_tower_TA_USE_C,atol=1e-7,rtol=0):
            raise ValueError("Original measured tower T and retained model T differ "+site)
        df["source_original_RH_implied_pct"]=100*(1-df.VPD_F/es(df.TA_F))
        df["paired_native_ERA_RH_pct"]=100*(1-df.VPD_ERA/es(df.TA_ERA))
        df["paired_native_ERA_RH_at_tower_T_VPD_hPa"]=(
            es(df.TA_F)*(1-df.paired_native_ERA_RH_pct/100))
        df["ERA5Land_T2M_C"]=np.nan
        df["ERA5Land_dewpoint_C"]=np.nan
        df["ERA5Land_water_RH_pct"]=np.nan
        df["ERA5Land_PSRF_Pa"]=np.nan
        df["ERA5Land_RH_at_tower_T_VPD_hPa"]=np.nan
        df["ERA5Land_RH_at_tower_T_RHice_pct"]=np.nan
        df["gridded_UTC_offset_hypothesis_h"]=int(stage10.BIF_OFFSET[site])
        df["gridded_UTC_offset_APPROVED"]=False
        times=pd.to_datetime(df.TIMESTAMP_START,format="%Y%m%d%H%M")
        for year in sorted(times.dt.year.unique()):
            idx=np.flatnonzero(times.dt.year.to_numpy()==year)
            key=f"{site}:{int(year)}"
            if key not in gridprovenance:
                raise ValueError("No Stage12g SHA verified source-year for review "+key)
            metadata=gridprovenance[key]
            external=safe(metadata["source_file"])
            if sha(external)!=metadata["original_source_sha256"]:
                raise ValueError("Grid source year SHA mismatch "+key)
            receiptfile=external.with_suffix(".receipt.json")
            sr=json.loads(safe(receiptfile).read_text())
            # Original Stage09f uses response_sha256, while newer Stage12f
            # uses artifact_sha256. Both are SHA-verified original downloads.
            receipt_sha=sr.get("artifact_sha256",sr.get("response_sha256"))
            if (receipt_sha!=metadata["original_source_sha256"]
                or sr.get("site")!=site or int(sr.get("year",-1))!=int(year)
                or "request" not in sr):
                raise ValueError("Grid site/year/position receipt changed "+key)
            loc=sr["request"]["location"]
            coord=(float(loc["latitude"]),float(loc["longitude"]))
            dt,fields,_=stage10.grid_fields(external,int(year),coord)
            midpoint=times.iloc[idx]+pd.Timedelta(minutes=15)
            utc=midpoint-pd.Timedelta(hours=int(stage10.BIF_OFFSET[site]))
            gt=stage10.interpolate(dt,fields["t2m"],utc)-273.15
            gd=stage10.interpolate(dt,fields["d2m"],utc)-273.15
            gp=stage10.interpolate(dt,fields["sp"],utc)
            grh=100*es(gd)/es(gt)
            v=es(df.iloc[idx].TA_F.to_numpy(dtype=float))*(1-grh/100)
            icepct=grh*es(df.iloc[idx].TA_F.to_numpy(dtype=float))/ice(df.iloc[idx].TA_F.to_numpy(dtype=float))
            df.loc[idx,"ERA5Land_T2M_C"]=gt
            df.loc[idx,"ERA5Land_dewpoint_C"]=gd
            df.loc[idx,"ERA5Land_water_RH_pct"]=grh
            df.loc[idx,"ERA5Land_PSRF_Pa"]=gp
            df.loc[idx,"ERA5Land_RH_at_tower_T_VPD_hPa"]=v
            df.loc[idx,"ERA5Land_RH_at_tower_T_RHice_pct"]=icepct
            inputs.append({"site":site,"year":int(year),"external_source":str(external),
                           "external_source_SHA256":sha(external),
                           "grid_UTC_offset_hypothesis_h":int(stage10.BIF_OFFSET[site]),
                           "UTC_offset_approved":False})
        for row in e.itertuples(index=False):
            k=str(row.native_key)
            original_center=df.loc[df.TIMESTAMP_START.eq(k)]
            if len(original_center)!=1:raise ValueError("Missing source-review center "+site+" "+k)
            c=original_center.iloc[0]
            if (abs(float(c.ERA5Land_water_RH_pct)-float(row.grid_water_RH_pct))>0.005
                or abs(float(c.ERA5Land_T2M_C)-float(row.grid_T2M_C))>0.005
                or abs(float(c.TA_F)-float(row.original_tower_T_C))>0.005
                or int(c.VPD_F_QC)!=int(row.QC_VPD_F)):
                raise ValueError("Grid reconstruction mismatch with ORIGINAL signed Stage12g HOLD row "+site+" "+k)
            time=pd.to_datetime(k,format="%Y%m%d%H%M")
            for lag in (-2,-1,0,1,2):
                kk=(time+pd.Timedelta(minutes=30*lag)).strftime("%Y%m%d%H%M")
                match=df.loc[df.TIMESTAMP_START.eq(kk)]
                if len(match)!=1:raise ValueError("Missing actual original native +/-HH key "+kk)
                x=match.iloc[0].to_dict()
                x.update({"site":site,"center_native_key":k,
                          "center_reason":row.reason,
                          "audit_class":row.audit_class,
                          "relative_halfhours":lag,
                          "is_review_center":lag==0})
                allrows.append(x)
    context=pd.DataFrame(allrows)
    if len(context)!=375 or context.groupby(["site","center_native_key"]).size().nunique()!=1:
        raise ValueError("All 75 events x 5 exactly native halfhours not reconstructed")
    centers=context.loc[context.relative_halfhours.eq(0)].copy()
    if not (len(centers)==75 and centers.audit_class.ne("ME6_POLICY_USER_APPROVED_NOT_YET_APPLIED_33").sum()==42):
        raise ValueError("Pending 42 and policy-approved 33 counts changed")
    summary=[]
    for (site,key),part in context.groupby(["site","center_native_key"],sort=True):
        part=part.set_index("relative_halfhours")
        center=part.loc[0]
        p,n=part.loc[-1],part.loc[1]
        item={"site":site,"native_key":key,"reason":center.center_reason,
              "audit_class":center.audit_class,
              "original_center_VPD_F_QC":int(center.VPD_F_QC),
              "original_center_VPD_F_hPa":center.VPD_F,
              "original_center_tower_T_C":center.TA_F,
              "original_center_VPD_implied_RH_pct":center.source_original_RH_implied_pct,
              "native_companion_ERA_center_RH_pct":center.paired_native_ERA_RH_pct,
              "grid_ERA5Land_center_RH_pct":center.ERA5Land_water_RH_pct,
              "grid_ERA5Land_center_T_C":center.ERA5Land_T2M_C,
              "grid_candidate_center_VPD_hPa":center.ERA5Land_RH_at_tower_T_VPD_hPa,
              "companion_ERA_candidate_center_VPD_hPa":center.paired_native_ERA_RH_at_tower_T_VPD_hPa,
              "G_minus30_VPD_hPa":p.selected_after_12ac_VPD_hPa,
              "G_center_VPD_hPa":center.selected_after_12ac_VPD_hPa,
              "G_plus30_VPD_hPa":n.selected_after_12ac_VPD_hPa,
              "G_-30_to_center_jump_hPa":abs(center.selected_after_12ac_VPD_hPa-p.selected_after_12ac_VPD_hPa),
              "G_center_to_+30_jump_hPa":abs(n.selected_after_12ac_VPD_hPa-center.selected_after_12ac_VPD_hPa),
              "grid_-30_to_center_jump_hPa":abs(center.ERA5Land_RH_at_tower_T_VPD_hPa-p.ERA5Land_RH_at_tower_T_VPD_hPa),
              "grid_center_to_+30_jump_hPa":abs(n.ERA5Land_RH_at_tower_T_VPD_hPa-center.ERA5Land_RH_at_tower_T_VPD_hPa),
              "ERA_-30_to_center_jump_hPa":abs(center.paired_native_ERA_RH_at_tower_T_VPD_hPa-p.paired_native_ERA_RH_at_tower_T_VPD_hPa),
              "ERA_center_to_+30_jump_hPa":abs(n.paired_native_ERA_RH_at_tower_T_VPD_hPa-center.paired_native_ERA_RH_at_tower_T_VPD_hPa),
              "no_science_approvals_added":True}
        summary.append(item)
    return context,pd.DataFrame(summary),pd.DataFrame(inputs)

def main():
    pa=argparse.ArgumentParser()
    mode=pa.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","run"):mode.add_argument("--"+m,action="store_true")
    args=pa.parse_args()
    print("STAGE12AE — ALL 42 PENDING ORIGINAL TOWER/ERA/ERA5-LAND 30min BEFORE AFTER | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    context,summary,inputs=audit()
    pending=summary.loc[summary.audit_class.ne("ME6_POLICY_USER_APPROVED_NOT_YET_APPLIED_33")].copy()
    print("\n========== EXACT 42 PENDING CENTER EVENTS: ORIGINAL TOWER AND PAIR/GRID ERA RH ==========",flush=True)
    print(pending[["site","native_key","reason","original_center_VPD_F_QC",
      "original_center_tower_T_C","original_center_VPD_F_hPa",
      "G_minus30_VPD_hPa","G_center_VPD_hPa","G_plus30_VPD_hPa",
      "native_companion_ERA_center_RH_pct",
      "grid_ERA5Land_center_RH_pct",
      "companion_ERA_candidate_center_VPD_hPa",
      "grid_candidate_center_VPD_hPa"]].round(3).to_string(index=False),flush=True)
    cols=["TIMESTAMP_START","TA_F","VPD_F","VPD_F_QC",
      "TA_ERA","VPD_ERA","paired_native_ERA_RH_pct",
      "ERA5Land_T2M_C","ERA5Land_water_RH_pct",
      "ERA5Land_RH_at_tower_T_VPD_hPa",
      "original_Stage12g_VPD_hPa","selected_after_12ac_VPD_hPa"]
    print("\n========== ALL 42 PENDING CENTERS ±1 TRUE ORIGINAL NATIVE 30min HALF-HOUR ==========",flush=True)
    for row in pending.itertuples(index=False):
        part=context.loc[context.site.eq(row.site)&
          context.center_native_key.eq(row.native_key)&
          context.relative_halfhours.isin([-1,0,1])]
        print("\n"+row.site+" "+row.native_key+" "+row.reason,flush=True)
        print(part[cols].round(3).to_string(index=False),flush=True)
    me6=summary.loc[summary.audit_class.eq("ME6_POLICY_USER_APPROVED_NOT_YET_APPLIED_33")]
    print("\n========== ME6 33 SOURCE-POLICY APPROVED, NOT YET ALL APPLIED ==========",flush=True)
    print(me6[["native_key","original_center_tower_T_C","original_center_VPD_F_hPa",
      "native_companion_ERA_center_RH_pct","grid_ERA5Land_center_RH_pct",
      "companion_ERA_candidate_center_VPD_hPa","grid_candidate_center_VPD_hPa"]].round(3).to_string(index=False),flush=True)
    print("\nSTAGE12AE SUMMARY: 42 STILL HUMAN PENDING = Kon 34 VPD + Kon 1 QC0 + NR1 3 VPD + MtB 4 conditional ice; 33 Me6 policy approved but NOT automatically applied; SHA sources checked; no model/forcing writes.",flush=True)
    if args.check:
        print("STAGE12AE CHECK COMPLETE: ZERO REPORT OR SOURCE WRITES.",flush=True)
        return
    dest=R/"reports"/("stage12ae_all_42_pending_original_tower_ERA_ERA5Land_neighbors_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    outputs={
       "75_high_priority_cases_x_five_native_halfhours_all_three_source_comparisons.csv":context,
       "75_cases_center_prev_next_source_value_jumps.csv":summary,
       "verified_source_year_grid_provenance.csv":inputs}
    for name,table in outputs.items():table.to_csv(dest/name,index=False)
    (dest/"SCIENTIFIC_REVIEW_NOT_REPAIRS.md").write_text(
      "This includes 42 PENDING human review events (34 Kon jump, 3 NR1 jump, "
      "4 MtB conditional ice, 1 Kon QC0 protected) and 33 US-Me6 operator-approved "
      "source policy events not yet all applied. Original tower raw VPD_F with source QC, "
      "original paired ERA TA_ERA/VPD_ERA and ERA5-Land gridded T/D/RH have separate "
      "provenance columns. Original native UTC offsets for gridded data are unapproved "
      "published BIF hypotheses; do not shift clock or claim observational truth. "
      "Stage12g full forcing and already-applied Stage12ac derivative unchanged. "
      "No science holds released, no DATM/Post-v5/Slurm/spinup approvals.\n")
    dig={n:sha(dest/n) for n in [*outputs,"SCIENTIFIC_REVIEW_NOT_REPAIRS.md"]}
    (dest/"stage12ae_review_only_SHA_receipt.json").write_text(json.dumps(
        {"version":VERSION,"pending_human_review":42,
         "Me6_previous_source_policy_approved_awaiting_application":33,
         "source_G_receipt_SHA256":sha(G/"stage12g_research_only_sha_receipt.json"),
         "stage12ac_receipt_SHA256":sha(A/AC_REC),
         "original_clocks_changed":False,
         "original_86_plus_233_science_holds_preserved":True,
         "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
         "output_SHA256":dig},indent=2)+"\n")
    print("STAGE12AE FULL SOURCE-COMPARISON REPORT DIR:",dest,flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AE STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

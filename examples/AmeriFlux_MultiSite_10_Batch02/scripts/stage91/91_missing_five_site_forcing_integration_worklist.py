#!/usr/bin/env python3
"""Stage91: exact five-site 98-year forcing integration worklist.

Crosswalk Stage07 incomplete ten-site forcing, Stage64 9389 independent-ERA
numerical candidates, Stage74 15199 Ho1+BZS independent-CDS shadows, approved
Stage85 Ho1 2000 humidity-only source records, and Stage87 five-site NetCDF
technical previews. SHA-verify each archived candidate ledger and preserve
separate provenance. Detect and report overlap by native site/timestamp;
never sum overlapping rows as independent corrections. Read-only origin files;
--audit writes only a new report folder (no NetCDF/active DATM/jobs).
"""
import argparse
from collections import Counter,defaultdict
import csv,hashlib,json,re
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
S64=ROOT/"reports/stage64_9389_unique_ERA5_humidity_candidates_20261024T232045Z_c8678d94"
S74=ROOT/"reports/stage74_four_missing_years_16874_Ho1_BZS_CDS_SHADOW_20261025T090751Z_d0953fbc"
S85=ROOT/"reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954"
S87=ROOT/"reports/stage87_five_site_DATM_NetCDF_technical_preview_20261026T003934Z_30692f63"
S90=ROOT/"reports/stage90_Ha1_VPD_Ho1_Dec_source_context_20261026T011202Z_ca90b24c"
FIVE={"US-EML":16,"US-GLE":16,"US-Ho1":28,"US-ICh":19,"US-ICt":19}
READY={"US-BZS":15,"US-CMW":21,"US-Ha1":35,"US-Ho2":27,"US-Ho3":19}
BLOCKED={"US-EML":1327,"US-GLE":295,"US-Ho1":937,"US-ICh":169,"US-ICt":2176}
F64="9389_original_tower_time_unified_CDS_ERA5_humidity_candidates.csv"
F74="16874_original_hard_independent_CDS_shadow_refreshed.csv"
F85="1068_Ho1_2000_VPD_adjusted_no_temperature_change.csv"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def records(p):
    with Path(p).open(newline="",encoding="utf8") as f:return list(csv.DictReader(f))

def verify(folder,manifest,field,expected):
    if (folder/"INCOMPLETE_DO_NOT_USE").exists():raise ValueError("Incomplete archived source: "+str(folder))
    obj=json.loads((folder/manifest).read_text())
    hashes=obj[field]
    if expected not in hashes:raise ValueError("Expected ledger missing from SHA receipt: "+expected)
    for name,digest in hashes.items():
        p=folder/name
        if not p.is_file() or sha(p)!=digest:
            raise ValueError("Source SHA verification failed: "+str(p))
    print("SOURCE SHA VERIFIED",folder.name,len(hashes),"files")
    return obj

def normal_stamp(row):
    for name in ("tower_local_start","timestamp_start","time","TIMESTAMP_START"):
        raw=str(row.get(name,"")).strip()
        if not raw:continue
        dig=re.sub(r"[^0-9]","",raw)
        if len(dig)>=12:
            return dig[:12]
    raise ValueError("No valid original native timestamp in candidate ledger")

def keyed(rows,where):
    seen={}
    for r in rows:
        site=str(r.get("site",""))
        if not site:raise ValueError("Empty site in "+where)
        stamp=normal_stamp(r)
        key=(site,stamp)
        if key in seen:raise ValueError("Duplicate native site/time in "+where+" "+str(key))
        seen[key]=r
    return seen

def gate():
    m07=json.loads((S07/"exact_input_manifest.json").read_text())
    raw={r["site"]:r for r in m07["sites"]}
    if len(raw)!=10 or set(raw)!=set(FIVE)|set(READY):
        raise ValueError("Stage07 ten-site release list drift")
    s07=records(S07/"candidate_run_summary.csv")
    if len(s07)!=10 or {r["site"] for r in s07 if r["status"]=="FAIL"}!=set(FIVE):
        raise ValueError("Stage07 historical five blocked scope drift")
    for r in s07:
        if r["site"] in FIVE and not r["error"].startswith(str(BLOCKED[r["site"]])+" impossible humidity pairs"):
            raise ValueError("Original Stage07 blocker evidence drift: "+r["site"])

    m64=verify(S64,"unified_source_provenance_and_hold_manifest.json","output_sha256",F64)
    m74=verify(S74,"stage74_source_science_manifest.json","outputs_sha256",F74)
    m85=verify(S85,"stage85_source_decision_manifest.json","outputs_SHA256",F85)
    m87=json.loads((S87/"manifest.json").read_text())
    if (S87/"INCOMPLETE_DO_NOT_USE").exists() or m87.get("netcdf_year_files")!=117 or m87.get("sites_built")!=5 or m87.get("scientific_release") is not False:
        raise ValueError("Stage87 original 117 technical preview state drift")
    built={x["site"] for x in m87["sites"]}
    if built!=set(READY):raise ValueError("Stage87 built-site census drift")
    m90=json.loads((S90/"stage90_summary.json").read_text())
    for name,h in m90.get("output_sha256",{}).items():
        if sha(S90/name)!=h:raise ValueError("Stage90 original source audit changed")
    if m90.get("December_T_vs_TA_ERA_gt8C_HH")!=1 or m90.get("original_QC0_edits")!=24:
        raise ValueError("Stage90 human decision evidence changed")

    a=records(S64/F64)
    b=records(S74/F74)
    c=records(S85/F85)
    if len(a)!=9389 or len(b)!=16874 or len(c)!=1068:
        raise ValueError("Stage64/74/85 exact immutable candidate census drift")
    if m64.get("approved_for_DATM") is not False or m74.get("approved_for_DATM") is not False or m85.get("active_forcing_or_DATM_approved") is not False:
        raise ValueError("Archived shadow candidate status changed unexpectedly")
    if m85.get("VPD_modified_humidity_only_count")!=1068:
        raise ValueError("Ho1 manual Stage85 scope changed")
    ca=keyed(a,"Stage64")
    cb_all=keyed(b,"Stage74")
    cc=keyed(c,"Stage85")
    if set(cc) != {("US-Ho1",k[1]) for k in cc} or any(t[:4]!="2000" for s,t in cc):
        raise ValueError("Approved Stage85 overlay escaped Ho1 year 2000")
    statuses=Counter(str(r.get("science_status","")) for r in b)
    wanted="SHADOW_NUMERIC_VALID_KEEP_ORIGINAL_T_PA_BIF_DATE_HOLD"
    if statuses[wanted]!=15199 or sum(statuses.values())!=16874:
        raise ValueError("Stage74 numeric shadow status census changed: "+str(statuses))
    cb={key:r for key,r in cb_all.items() if str(r.get("science_status",""))==wanted}
    print("EXACT HISTORICAL SHADOW CENSUS Stage64",len(ca),"Stage74",len(cb),
          "Stage85 approved Ho1 2000 humidity",len(cc))
    print("STAGE74 OTHER HOLD",len(cb_all)-len(cb))
    print("OVERLAP Stage64-Stage74",len(ca.keys()&cb.keys()),
          "Stage64-Stage85",len(ca.keys()&cc.keys()),
          "Stage74-Stage85",len(cb.keys()&cc.keys()))
    return raw,ca,cb,cc,m87,statuses

def build():
    info,ca,cb,cc,m87,statuses=gate()
    chosen=defaultdict(lambda:{"s64":0,"s74":0,"s85":0,"unique":set(),"overlap":0})
    for tag,ledger in (("s64",ca),("s74",cb),("s85",cc)):
        for site,time in ledger:
            y=int(time[:4]);key=(site,y)
            if site not in FIVE and site!="US-BZS":
                # Other ready sites can have shadow rows; not construction targets
                continue
            slot=chosen[key]
            slot[tag]+=1
            if time in slot["unique"]:slot["overlap"]+=1
            slot["unique"].add(time)
    work=[]
    print("\nSTAGE91 FIVE MISSING SITE NC YEAR TARGETS: exactly 98 technical annual files")
    for site,years in FIVE.items():
        meta=info[site];start,end=int(meta["first_year"]),int(meta["last_year"])
        if end-start+1!=years:raise ValueError("Expected site-years drift "+site)
        total_shadow=0
        for year in range(start,end+1):
            x=chosen[(site,year)]
            note=("STAGE85_APPROVED_YEAR2000_QC0_HUMIDITY_ONLY" if site=="US-Ho1" and year==2000
                  else "SOURCE_SHADOWS_UNAPPROVED")
            n=len(x["unique"]);total_shadow+=n
            work.append(dict(site=site,year=year,native_minutes=meta["native_minutes"],
                source_primary=meta["primary"],source_era=meta["era"],
                source_stage64_numeric_candidates=x["s64"],
                source_stage74_numeric_shadows=x["s74"],
                source_stage85_approved_year2000_humidity_changes=x["s85"],
                unique_candidate_timestamps=n,
                double_count_deduplicated=x["overlap"],
                state="TECHNICAL_NC_NOT_BUILT_COMPLETE_FORCING_AND_POSTV5_PENDING",
                science_note=note,active_DATM_approved="NO"))
        print("SOURCE PLAN",site,start,end,"NC",years,
              "candidate/shadow source timestamps",total_shadow,
              "original Stage07 humidity-blocked rows",BLOCKED[site])
    if len(work)!=98:raise ValueError("Stage91 missing 98-year plan failed")
    print("\nFIVE READY SITES original 117 technical previews retained; never modified")
    print("REMAINING: build 5 scientifically-provenance-aware complete-year forcing,")
    print("preserve Stage85 Ho1 2000, redo Post-v5, THEN build 98 year NC technical previews.")
    print("No temperature QC2 relabeled measured; Ho1 2000-12-27 09:00/09:30 science discontinuity remains HOLD.")
    print("CLOCK/ZBOT/PFT/CIME/SLURM production gates remain separate.")
    return work

def audit(work):
    output=ROOT/"reports"/("stage91_five_site_98year_source_integration_worklist_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    dest=output/"98_missing_netcdf_year_source_worklist.csv"
    with dest.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(work[0]))
        w.writeheader();w.writerows(work)
    receipt={"schema":"STAGE91_FIVE_SITE_98YEAR_SOURCE_INTEGRATION_v1",
             "missing_NC_year_count":98,"already_built_NC_technical_years":117,
             "all_requested_technical_years":215,"complete_original_ten_site_forcing":False,
             "postv5_complete":False,"model_DATM_activated":False,
             "original_source_writes":False,
             "out_sha256":{dest.name:sha(dest)}}
    (output/"manifest.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE91 WORKLIST PASS | 98 missing NC source years, source candidate ledgers deduplicated")
    print("REPORT",output)
    print("NO RAW/SOURCE/FORCING/DATM/NETCDF/CIME/SLURM WRITES")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--check",action="store_true")
    p.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:
        assert sum(FIVE.values())==98 and sum(READY.values())==117
        assert sum(BLOCKED.values())==4904
        assert normal_stamp({"timestamp_start":"2000-12-27T09:30:00"})=="200012270930"
        assert len(keyed([{"site":"US-Ho1","time":"200012270930"}],"unit"))==1
        print("STAGE91 SELF-TEST PASS | exact 5-site 98-year target, native timestamp identity, distinct candidate sources; no writes")
        return
    if not (a.check or a.audit):p.error("Use --check/--audit or --self-test")
    work=build()
    if a.check:
        print("STAGE91 CHECK PASS | READ ONLY; 98 annual NC still not built")
    else:audit(work)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch04 Stage12: apply real non-US-Syv source HOLD resolutions, preserving towers.

Operates ONLY on US-SP1, US-Ton, US-Seg, US-SRG, US-Uaf:
  155 inherited science HOLDs + up to 2 separate US-SP1 Stage07 unsafe VPD edges.
  US-Syv 606 old HOLDs and 10 unsafe VPD edges remain explicitly deferred.
  US-Rpf/US-SRM 689/689 Stage10 fixes are retained in Stage11 latest selection.

Tower source TA is retained when consistent with trustworthy original neighbours.
Invalid and QC-nonzero isolated temperature readings may be interpolated from
adjacent native observations. Invalid native VPD or explicit missed edge targets
are replaced using independent ERA5-Land (T2m, dewpoint, surface pressure),
matched to BIF local-standard timestamps using verified site-specific offsets.
Derived RH and VPD must satisfy physical closure at RETAINED selected tower TA.

--run downloads at most N absent site-years from CDS, applies available valid
values, emits NEW complete derived FLUXMET_HH CSVs ONLY for modified sites,
latest-path selection manifest, still-HOLD cases and SHA receipt.
--apply-existing never downloads. --check reads no CDS or outputs.
All originals / Stage05-11 files untouched. No Post-v5/DATM/CLM approval.
"""
import argparse
import csv
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from uuid import uuid4

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=EXP/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
S08=EXP/"qcv5_stage08_remaining_seven_candidates/candidate_20261024T120137Z"
S11=EXP/"qcv5_stage11_latest_ten_manifest/candidate_20261024T232100Z_1c6ef02a"
HELPER=Path(__file__).resolve().with_name("10_era5land_independent_humidity_fill.py")
SELECT=("US-SP1","US-Ton","US-Seg","US-SRG","US-Uaf")
HOLD_COUNT={"US-SP1":147,"US-Ton":1,"US-Seg":4,"US-SRG":1,"US-Uaf":2}
EXPECTED_SITES={"US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg","US-Ses",
                "US-Slt","US-Syv","US-Ton","US-Uaf"}
EXPECTED_STAGE10={"US-Rpf","US-SRM"}
SEG_LOCATION={"GROUP_ID":"1495","latitude":34.3623,"longitude":-106.7020}
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def helper():
    if not HELPER.is_file() or HELPER.is_symlink():
        raise RuntimeError("Pinned Stage10 helper missing; download the matching Stage10 Python script beside Stage12")
    spec=importlib.util.spec_from_file_location("b04_stage10_helper",str(HELPER))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for required in ("response_receipt","download_one","grid_read","local_to_utc","rh_hour","sat_c","response_path"):
        if not callable(getattr(mod,required,None)):
            raise RuntimeError("Stage10 helper lacks "+required)
    return mod

def regular(p):
    if p.is_symlink() or not p.is_file():raise ValueError("Missing or symlink input "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()

def csvrows(p):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        d=csv.DictReader(f)
        if not d.fieldnames or len(set(d.fieldnames))!=len(d.fieldnames):
            raise ValueError("Invalid CSV header "+str(p))
        return list(d)

def value(s):
    x=str(s if s is not None else "").strip()
    if x.upper() in MISSING:return None
    try:v=float(x)
    except ValueError:return None
    return v if math.isfinite(v) else None

def fmt(x):return "%.12g"%x

def plus(k,m):
    return (datetime.strptime(k,"%Y%m%d%H%M")+
            timedelta(minutes=m)).strftime("%Y%m%d%H%M")

def physics(t,v):
    if t is None or v is None:return False
    es=6.112*math.exp(17.67*t/(243.5+t)) if -80<=t<=65 else None
    return es is not None and 0<=v<=es*1.00001

def rh_from(t,v):
    if not physics(t,v):return None
    return max(0.,min(100.,100*(1-v/(6.112*math.exp(17.67*t/(243.5+t))))))

def get_inputs():
    manifest=S11/"LATEST_10_SITES_FOR_POSTV5_INPUT.tsv"
    rows=csvrows_tsv(manifest)
    if len(rows)!=10 or {r["site"] for r in rows}!=EXPECTED_SITES:
        raise ValueError("Stage11 exact ten latest candidates mismatch")
    selections={r["site"]:r for r in rows}
    for site in SELECT:
        r=selections[site]
        p=Path(r["source_path"])
        if (p.is_symlink() or not p.is_file() or
                sha(p)!=r["source_SHA256"] or
                int(r["known_unresolved_HOLD_entries"])!=HOLD_COUNT[site]):
            raise ValueError("Stage11 input mismatch "+site)
    stage05=json.loads(regular(S05/"report.json").read_text())
    stage08=json.loads(regular(S08/"report.json").read_text())
    r07=json.loads(regular(S07/"stage07_sha_receipt.json").read_text())
    r11=json.loads(regular(S11/"stage11_selection_receipt.json").read_text())
    if (r07.get("inherited_stage05_holds")!=754 or
        r07.get("invalid_era_endpoints_held")!=12 or
        len(r11.get("latest_site_selection",[]))!=10 or
        r11.get("manifest_sha256")!=sha(manifest) or
        r11.get("Postv5_approved") is not False):
        raise ValueError("Pinned Stage07/11 provenance inconsistent")
    holds7=csvrows(S07/"stage07_inherited_754_holds.csv")
    skipped=csvrows(S07/"stage07_unsafe_ERA_target_holds.csv")
    holds8=csvrows(S08/"unresolved_hold.csv")
    if len(holds7)!=754 or len(skipped)!=12 or len(holds8)!=696:
        raise ValueError("Original Stage07/08 HOLD records changed")
    targets=defaultdict(set)
    byreason=Counter()
    for h in holds7:
        site=h["site"]
        if site in SELECT:
            targets[site,h["TIMESTAMP_START"]].add("ORIGINAL_S07_"+h["reason"])
            byreason[site,"ORIGINAL_S07"]+=1
    for h in holds8:
        site=h["site"]
        if site in SELECT:
            targets[site,h["TIMESTAMP_START"]].add("ORIGINAL_S08_"+h["reason"])
            byreason[site,"ORIGINAL_S08"]+=1
    for h in skipped:
        site=h["site"]
        if site=="US-SP1":
            targets[site,h["TIMESTAMP_START"]].add("STAGE07_SKIPPED_ERA_EDGE")
            byreason[site,"STAGE07_EDGE"]+=1
    if sum(byreason[s,"ORIGINAL_S07"]+byreason[s,"ORIGINAL_S08"] for s in SELECT)!=155:
        raise ValueError("Expected exactly 155 old non-Syv science holds")
    if byreason["US-SP1","STAGE07_EDGE"]!=2:
        raise ValueError("Expected exactly 2 US-SP1 high-jump edge skip records")
    if any(s not in SELECT for s,k in targets):
        raise ValueError("Unexpected site in target ledger")
    if len(targets)<155 or len(targets)>157:
        raise ValueError("Unexpected overlap of Stage07 jump-edge skips")
    met={}
    for site in SELECT:
        entry=stage05["sites"][site] if site in stage05["sites"] else stage08["sites"][site]
        raw=Path(entry["paths"]["native"])
        fingerprint=entry["source_provenance"]["native"]["sha256"]
        if sha(raw)!=fingerprint:raise ValueError("Original immutable tower source SHA mismatch "+site)
        met[site]={"native":raw,"sha256":fingerprint}
    return selections,targets,byreason,met

def csvrows_tsv(p):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        d=csv.DictReader(f,delimiter="\t")
        if not d.fieldnames:return []
        return list(d)

def point_for(site,native):
    sources=list(native.parent.glob(f"AMF_{site}_FLUXNET_BIF_*.csv"))
    if len(sources)!=1:raise ValueError("Expected unique raw BIF "+site)
    bif=sources[0]
    grouped=defaultdict(lambda:defaultdict(list))
    for r in csvrows(bif):
        if r.get("SITE_ID",site).strip() not in (site,""):
            raise ValueError("Wrong SITE_ID inside BIF")
        field=r.get("VARIABLE","").strip().upper()
        if field in {"LOCATION_LAT","LOCATION_LONG","UTC_OFFSET"}:
            grouped[r["GROUP_ID"].strip()][field].append(value(r.get("DATAVALUE")))
    if site=="US-Seg":
        group=SEG_LOCATION["GROUP_ID"]
        records=grouped.get(group)
        if not records:
            raise ValueError("Approved US-Seg BIF GROUP_ID 1495 absent")
        lat,long=SEG_LOCATION["latitude"],SEG_LOCATION["longitude"]
        if lat not in records["LOCATION_LAT"] or long not in records["LOCATION_LONG"]:
            raise ValueError("Approved US-Seg coordinates not present in original 1495 BIF")
        off=set(x for x in records["UTC_OFFSET"] if x is not None)
        if len(off)!=1:
            alloff={v for r in grouped.values() for v in r.get("UTC_OFFSET",[]) if v is not None}
            if len(alloff)!=1:
                raise ValueError("US-Seg standard UTC_OFFSET ambiguous")
            off=alloff
        offset=off.pop()
    else:
        def unambiguous(field):
            vals={v for records in grouped.values() for v in records.get(field,[]) if v is not None}
            if len(vals)!=1:raise ValueError("BIF ambiguous original "+site+" "+field+" "+repr(sorted(vals)))
            return vals.pop()
        lat,long,offset=[unambiguous(x) for x in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET")]
    if not (-90<=lat<=90 and -180<=long<=180 and -12<=offset<=14 and float(offset).is_integer()):
        raise ValueError("Invalid original BIF lat/lon/offset")
    print("BIF VERIFIED",site,"lat",lat,"lon",long,"UTC_OFFSET",offset,flush=True)
    return {"latitude":lat,"longitude":long,"offset_hours":int(offset),
            "BIF_file":str(bif),"BIF_sha256":sha(bif)}

def source_context(selections,targets):
    results={}
    for site in SELECT:
        keys={k for s,k in targets if s==site}
        need=set(keys)
        for k in keys:need.update((plus(k,-30),plus(k,30)))
        kept={};n=0
        p=Path(selections[site]["source_path"])
        with p.open(encoding="utf-8-sig",newline="") as f:
            rd=csv.DictReader(f)
            needed={"TIMESTAMP_START","TIMESTAMP_END","TA_F","PA_F","VPD_F","TA_F_QC","VPD_F_QC"}
            if not rd.fieldnames or not needed.issubset(rd.fieldnames):
                raise ValueError("Latest FLUXMET source field missing "+site)
            for row in rd:
                n+=1
                k=row["TIMESTAMP_START"]
                if k in need:
                    if k in kept:raise ValueError("Duplicate input halfhour "+site+" "+k)
                    kept[k]=row
        if n!=int(selections[site]["rows"]) or not keys.issubset(kept):
            raise ValueError("Source row count/target missing "+site)
        results[site]=kept
        print("LATEST SOURCE",site,"rows",n,"HOLD_TARGETS",len(keys),flush=True)
    return results

def neighbour_support(r,left,right):
    if left is None or right is None:return None
    a,b=value(left.get("TA_F")),value(right.get("TA_F"))
    t=value(r.get("TA_F"))
    if any(x is None or not -55<=x<=52 for x in (a,b)):return None
    if left["TA_F_QC"].strip() not in {"0","1"} or right["TA_F_QC"].strip() not in {"0","1"}:
        return None
    if abs(a-b)>6:return None
    if t is not None and -55<=t<=52 and abs(t-a)<=4 and abs(t-b)<=4:
        return ("KEEP_TOWER_TA",t)
    # Only override low-confidence or physically invalid target temperature.
    if (t is None or not -55<=t<=52 or r["TA_F_QC"].strip()!="0") and abs(a-b)<=4:
        return ("NATIVE_NEIGHBOUR_TA_INTERPOLATION",(a+b)/2)
    return None

def independent_grid_t_c(grid, utc):
    """Interpolate verified ERA5-Land T2m to exact native half-hour in °C."""
    if grid is None:return None
    diff=(utc-grid["start_utc"]).total_seconds()/3600
    pos=math.floor(diff); f=diff-pos
    values=grid["values"]["t2m"]
    if pos<0 or pos+1>=len(values):return None
    a,b=float(values[pos])-273.15,float(values[pos+1])-273.15
    v=a+(b-a)*f
    return v if math.isfinite(v) and -55<=v<=52 else None


def external_temperature_fallback(row,left,right,grid,utc):
    """ERA T only for invalid or non-QC0 tower T; never displace credible QC0."""
    tower=value(row.get("TA_F"))
    if tower is not None and -55<=tower<=52 and row["TA_F_QC"].strip()=="0":
        return None
    t=independent_grid_t_c(grid,utc)
    if t is None:return None
    for adj in (left,right):
        if adj is None:continue
        a=value(adj.get("TA_F"))
        if a is not None and -55<=a<=52 and adj["TA_F_QC"].strip() in ("0","1"):
            if abs(t-a)>6:
                return None
    return ("INDEPENDENT_ERA5LAND_TA_FOR_INVALID_TOWER",t)


def build_decisions(targets,contexts,points,grids,external):
    chosen=defaultdict(dict);status={};needsgrid=defaultdict(set)
    for (site,k),reasons in sorted(targets.items()):
        if site not in points:
            status[site,k]="BIF_COORDINATE_OR_UTC_OFFSET_UNRESOLVED"
            continue
        r=contexts[site][k]
        left=contexts[site].get(plus(k,-30));right=contexts[site].get(plus(k,30))
        decision=neighbour_support(r,left,right)
        is_jump="STAGE07_SKIPPED_ERA_EDGE" in reasons
        if decision is None:
            needsgrid[site,int(k[:4])].add(k)
            grid=grids.get((site,int(k[:4])))
            if grid is not None:
                utc=external.local_to_utc(k,points[site]["offset_hours"])
                decision=external_temperature_fallback(r,left,right,grid,utc)
            if decision is None:
                status[site,k]=("ERA5LAND_YEAR_MISSING" if grid is None
                                else "NEIGHBOUR_OR_GRID_TEMPERATURE_NOT_CONFIRMED")
                continue
        why,t=decision
        rawv=value(r.get("VPD_F"))
        if physics(t,rawv) and not is_jump:
            # Valid tower TA/VPD: retain original humidity, only derive RH
            # if missing or physically invalid, avoiding unnecessary ERA changes.
            rawrh=value(r.get("RH"))
            if rawrh is None or rawrh<0 or rawrh>100.05:
                chosen[site][k]={"RH":rh_from(t,rawv)}
            if why in ("NATIVE_NEIGHBOUR_TA_INTERPOLATION",
                       "INDEPENDENT_ERA5LAND_TA_FOR_INVALID_TOWER"):
                chosen[site][k]["TA_F"]=t
            status[site,k]="RESOLVED_RETAIN_PHYSICAL_NATIVE_"+why
            continue
        needsgrid[site,int(k[:4])].add(k)
        grid=grids.get((site,int(k[:4])))
        if grid is None:
            status[site,k]="ERA5LAND_YEAR_MISSING"
            continue
        utc=external.local_to_utc(k,points[site]["offset_hours"])
        rh=external.rh_hour(grid,utc)
        pressure=value(r.get("PA_F"))
        es=external.sat_c(t)
        if (rh is None or not 1<=rh<=100 or pressure is None or
            not 65<=pressure<=110 or es is None):
            status[site,k]="GRID_RH_OR_TOWER_PA_INVALID"
            continue
        vpd=es*(1-rh/100)
        if not physics(t,vpd):
            status[site,k]="GRID_RECONSTRUCTION_PHYSICALLY_INVALID"
            continue
        chosen[site][k]={"VPD_F":vpd,"RH":rh}
        if why in ("NATIVE_NEIGHBOUR_TA_INTERPOLATION",
                   "INDEPENDENT_ERA5LAND_TA_FOR_INVALID_TOWER"):
            chosen[site][k]["TA_F"]=t
        status[site,k]="RESOLVED_INDEPENDENT_ERA5LAND_"+why
    return chosen,status,needsgrid

def grid_targets(targets,contexts):
    """Download only where native VPD is invalid or original stage07 edge skipped."""
    years=defaultdict(set)
    for (site,k),reasons in targets.items():
        context=contexts[site];r=context[k]
        support=neighbour_support(r,context.get(plus(k,-30)),context.get(plus(k,30)))
        if support is None:
            years[site,int(k[:4])].add(k)
        elif not physics(support[1],value(r.get("VPD_F"))) or "STAGE07_SKIPPED_ERA_EDGE" in reasons:
            years[site,int(k[:4])].add(k)
    return dict(years)

def materialize(old,new,patches,expected):
    rows=0;changed=0;matched=set()
    with regular(old).open(encoding="utf-8-sig",newline="") as src, new.open(
            "x",encoding="utf-8",newline="") as dst:
        r=csv.DictReader(src)
        if not r.fieldnames or not {"TIMESTAMP_START","TA_F","VPD_F","PA_F"}.issubset(r.fieldnames):
            raise ValueError("Unusable source CSV columns")
        columns=list(r.fieldnames)
        if patches and "RH" not in columns:columns.append("RH")
        w=csv.DictWriter(dst,fieldnames=columns);w.writeheader()
        for row in r:
            rows+=1;k=row["TIMESTAMP_START"]
            if k in patches:
                if k in matched:raise ValueError("Duplicated source event")
                matched.add(k);did=False
                for var,val in patches[k].items():
                    oldval=value(row.get(var))
                    if oldval is None or abs(oldval-val)>1e-10:
                        row[var]=fmt(val);did=True
                changed+=int(did)
            w.writerow(row)
    if rows!=expected or matched!=set(patches):
        raise ValueError("Derived source row count or patch time join differs")
    return {"path":str(new),"sha256":sha(new),
            "rows":rows,"modified_halfhours":changed}

def self_test():
    t={"TA_F":"10","TA_F_QC":"0"}
    left={"TA_F":"9","TA_F_QC":"0"}
    right={"TA_F":"11","TA_F_QC":"0"}
    assert neighbour_support(t,left,right)==("KEEP_TOWER_TA",10)
    t={"TA_F":"-9999","TA_F_QC":"2"}
    assert neighbour_support(t,left,right)==("NATIVE_NEIGHBOUR_TA_INTERPOLATION",10)
    assert physics(10,0) and not physics(10,50)
    assert rh_from(10,0)==100
    grid={"start_utc":datetime(2025,1,1,tzinfo=timezone.utc),
          "values":{"t2m":[283.15,285.15]}}
    assert abs(independent_grid_t_c(grid,datetime(2025,1,1,0,30,tzinfo=timezone.utc))-11)<1e-9
    assert external_temperature_fallback(
        {"TA_F":"-9999","TA_F_QC":"2"},None,None,grid,
        datetime(2025,1,1,0,30,tzinfo=timezone.utc))[1]==11
    assert external_temperature_fallback(
        {"TA_F":"10","TA_F_QC":"0"},None,None,grid,
        datetime(2025,1,1,0,30,tzinfo=timezone.utc)) is None
    assert len(SELECT)==5 and sum(HOLD_COUNT.values())==155
    print("STAGE12 SELF-TEST PASS: native temperature neighbours, valid VPD retention, 5-site hold scope")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    modes.add_argument("--apply-existing",action="store_true")
    p.add_argument("--max-downloads",type=int,default=3)
    args=p.parse_args()
    self_test()
    if args.self_test:return
    if not 1<=args.max_downloads<=5:raise ValueError("max-downloads range 1..5")
    ext=helper()
    selections,targets,grouping,met=get_inputs()
    contexts=source_context(selections,targets)
    points={}
    missing_points={}
    for site in SELECT:
        try:
            points[site]=point_for(site,met[site]["native"])
        except ValueError as exc:
            missing_points[site]=str(exc)
            print("BIF SITE HOLD, OTHER SITES CONTINUE",site,str(exc),flush=True)
    years=grid_targets(targets,contexts)
    pending=sorted((k for k in years if k[0] in points),
                   key=lambda q:(-len(years[q]),q[0],q[1]))
    print("STAGE12 TARGETS inherited=155, original skipped-SP1-edge=2, unique",len(targets))
    print("STAGE12 CDS REQUIRED",len(years),"site-years")
    for site,year in pending:
        present=ext.response_receipt(site,year)
        print("SITE_YEAR",site,year,"targets",len(years[site,year]),
              "PRESENT" if present else "MISSING",flush=True)
    if args.check:
        print("STAGE12 CHECK ONLY no file/CDS writes")
        return
    if args.run:
        count=0
        for site,year in pending:
            if ext.response_receipt(site,year):continue
            if count>=args.max_downloads:break
            ext.download_one(site,year,points[site])
            count+=1
        print("STAGE12 NEW/RECOVERED CDS SITE-YEARS",count)
    grids={};gridsha={}
    for site,year in pending:
        f=ext.response_receipt(site,year)
        if f:
            grids[site,year]=ext.grid_read(f,year,points[site])
            gridsha[f"{site}_{year}"]=ext.sha(f)
    patches,status,_=build_decisions(targets,contexts,points,grids,ext)
    successes=sum(x.startswith("RESOLVED") for x in status.values())
    oldhold=len(targets)-successes
    if successes+oldhold!=len(targets):raise ValueError("Hold partition not exhaustive")
    out=EXP/"qcv5_stage12_non_syv_repaired"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage12 updated five-site subset only. Deferred US-Syv and other prior model science gates remain.\n")
    output={};selected=[]
    with (out/"stage12_repaired_source_candidates.tsv").open("x",encoding="utf-8",newline="") as f:
        cols=["site","latest_stage","source_path","source_SHA256","rows",
              "stage12_resolved_hold_times","stage12_remaining_target_times"]
        wr=csv.DictWriter(f,fieldnames=cols,delimiter="\t");wr.writeheader()
        for site in sorted(EXPECTED_SITES):
            r=selections[site]
            entry={"site":site,"latest_stage":r["source_stage"],
                   "source_path":r["source_path"],
                   "source_SHA256":r["source_SHA256"],
                   "rows":r["rows"],
                   "stage12_resolved_hold_times":sum(s==site and v.startswith("RESOLVED") for (s,k),v in status.items()),
                   "stage12_remaining_target_times":sum(s==site and not v.startswith("RESOLVED") for (s,k),v in status.items())}
            if site in SELECT and patches.get(site):
                path=out/(site+"_Stage12_repaired_FLUXMET_HH.csv")
                output[site]=materialize(Path(r["source_path"]),path,
                                         patches[site],int(r["rows"]))
                entry.update(latest_stage="STAGE12",source_path=str(path),
                             source_SHA256=output[site]["sha256"])
            wr.writerow(entry)
            selected.append(entry)
    with (out/"stage12_science_decisions.tsv").open("x",encoding="utf-8",newline="") as f:
        cols=["site","TIMESTAMP_START","status","requested_reasons",
              "new_TA_F_C","new_VPD_F_hPa","new_RH_pct"]
        wr=csv.DictWriter(f,fieldnames=cols,delimiter="\t");wr.writeheader()
        for (site,k),state in sorted(status.items()):
            p=patches.get(site,{}).get(k,{})
            wr.writerow({"site":site,"TIMESTAMP_START":k,"status":state,
                         "requested_reasons":";".join(sorted(targets[site,k])),
                         "new_TA_F_C":fmt(p["TA_F"]) if "TA_F" in p else "",
                         "new_VPD_F_hPa":fmt(p["VPD_F"]) if "VPD_F" in p else "",
                         "new_RH_pct":fmt(p["RH"]) if "RH" in p else ""})
    proof={"stage11_source_manifest_sha256":sha(S11/"LATEST_10_SITES_FOR_POSTV5_INPUT.tsv"),
           "original_native_BIF_points":points,
           "site_BIF_metadata_holds":missing_points,
           "ERA5Land_source_sha256":gridsha,
           "target_unique_non_Syv_events":len(targets),
           "successfully_resolved":successes,"unresolved":oldhold,
           "per_site_statuses":{site:dict(Counter(v for (s,k),v in status.items() if s==site)) for site in SELECT},
           "new_files":output,"new_selected_ten":selected,
           "deferred_US_Syv_original_HOLD":606,
           "deferred_US_Syv_original_ERA_edge_skips":10,
           "Postv5_approved":False,"DATM_ready":False,"spinup":False,
           "receipt_sha256":{
             n:sha(out/n) for n in ("stage12_repaired_source_candidates.tsv","stage12_science_decisions.tsv")},
           "created_utc":datetime.now(timezone.utc).isoformat()}
    (out/"stage12_receipt.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("STAGE12 RESULT",successes,"of",len(targets),"resolved",oldhold,"not resolved")
    print("STAGE12 TEN-SITE LATEST MANIFEST",out/"stage12_repaired_source_candidates.tsv")
    print("NO ORIGINAL OR STAGE05-11 DATA, DATM, CIME OR SLURM WRITES")

if __name__=="__main__":
    main()

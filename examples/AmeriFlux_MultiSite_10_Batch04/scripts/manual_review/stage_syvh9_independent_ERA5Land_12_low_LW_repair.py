#!/usr/bin/env python3
"""Batch04 SYVH9: independently downloaded ERA5-Land longwave for 12 bad LW HH.

The first source audit found original FLUXMET LW_IN_F and its original
packaged LW_IN_ERA BOTH equal to the same contaminated 44.764 W/m2.
Do not reuse the packaged source. Retrieve independent CDS ERA5-Land
reanalysis-era5-land-timeseries surface_thermal_radiation_downwards, which
is DE-ACCUMULATED hourly energy in J m^-2; divide by 3600 for W m^-2.
Native 30min halfhours represent each corresponding hourly mean by the
UTC END-OF-HOUR timestamp (00:00/00:30 start use next 01:00 end).
Exact tower BIF UTC_OFFSET, original source and pair SHAs and QC validated.

Six site-year responses: US-SP1 (2004,2016), US-Slt (2016),
US-Syv/Ton/Uaf (2004). Narrow 6-day CDS requests, no entire year.
--self-test  pure numerical time/unit tests, no files/network/writes.
--check      SHA source, input manifest, BIF and 12-HH original-vs-
             packaged evidence; no downloads or writes.
--run        download only missing CDS site-year response(s), integrity/
             unit/coordinate/time validate; enforce 12 LW-only choices;
             create five versioned full-length research sources and
             new ten-site manifest, independently audit each full source;
             check all ten 7-met/NOLEAP with old SYVH6 scientific checker.
No original, old trial, surface, DATM, CIME, Slurm, model writes.
"""
import argparse,csv,hashlib,importlib.util,io,json,math,os,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from collections import Counter
from uuid import uuid4

HERE=Path(__file__).resolve().parent
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
ERA7=HERE/"stage_syvh7_repair_12_low_longwave_5sites_ERA_exacttime.py"
H5=HERE/"stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py"
H6=HERE/"stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py"
CACHE=ROOT/"reports/stage_SYVH9_independent_CDS_ERA5Land_longwave"
OUTBASE=ROOT/"manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved"
DATASET="reanalysis-era5-land-timeseries"
VARIABLE="surface_thermal_radiation_downwards"
VAR_SHORT="strd"
SOURCE_NAME="ERA5LAND_TIMESERIES_DEACCUMULATED_STRD_JM2_HOURLY"
LIMIT_LOW=60.0;LIMIT_HIGH=700.0
MAX_INTERNAL_JUMP=110.
MAX_BOUNDARY_JUMP=180.
NATIVE_EXPECTED={"US-SP1":368208,"US-Slt":315552,"US-Syv":438288,
                 "US-Ton":438288,"US-Uaf":403248}
BIF_VARIABLES=("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET")
WINDOWS={2004:("2004-12-01","2004-12-06"),
         2016:("2016-10-07","2016-10-12")}
REQ={(s,datetime.strptime(group[0],"%Y%m%d%H%M").year)
     for s,events in {
       "US-SP1":(("200412040000","200412040030"),
                 ("201610091900","201610091930")),
       "US-Slt":(("201610091900","201610091930"),),
       "US-Syv":(("200412032300","200412032330"),),
       "US-Ton":(("200412032100","200412032130"),),
       "US-Uaf":(("200412032000","200412032030"),),
     }.items() for group in events}
N_REQUESTS=6

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def mod(p,n):
    ck(p.is_file() and not p.is_symlink(),"Missing pinned sibling module "+str(p))
    s=importlib.util.spec_from_file_location(n,str(p))
    module=importlib.util.module_from_spec(s)
    s.loader.exec_module(module)
    return module
def file(p):
    ck(p.is_file() and not p.is_symlink(),"Missing/symlink scientific source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for chunk in iter(lambda:f.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()
def formnum(s):
    try:
        v=float(s)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None
def str_time(x):
    return x.strftime("%Y%m%d%H%M")
def utc(k,off):
    return (datetime.strptime(k,"%Y%m%d%H%M")-timedelta(hours=off)).replace(tzinfo=timezone.utc)
def hour_ending(k,off):
    u=utc(k,off)
    ck(u.minute in (0,30),"Non-native half hour in UTC "+k)
    return u.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
def expected_times(year):
    start,end=WINDOWS[year]
    a=datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    b=datetime.fromisoformat(end).replace(tzinfo=timezone.utc)+timedelta(hours=23)
    return [a+timedelta(hours=h) for h in range(int((b-a).total_seconds()/3600)+1)]
def request(lat,lon,year):
    return {"variable":[VARIABLE],"date":list(WINDOWS[year]),
            "location":{"latitude":lat,"longitude":lon},
            "data_format":"netcdf"}
def bif(raw,site):
    folder=raw.parent
    choices=list(folder.glob("AMF_"+site+"_FLUXNET_BIF_*.csv"))
    ck(len(choices)==1,"Expected one unique original BIF metadata file "+site)
    p=file(choices[0]);values={x:set() for x in BIF_VARIABLES}
    with p.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        ck(reader.fieldnames and
           {"VARIABLE","DATAVALUE","GROUP_ID"}.issubset(reader.fieldnames),
           "Original BIF schema unexpected "+site)
        for r in reader:
            if r.get("SITE_ID",site).strip() not in (site,""):
                raise ValueError("BIF contains different site identifier "+site)
            key=r["VARIABLE"].strip().upper()
            if key in values:
                n=formnum(r["DATAVALUE"])
                if n is not None:values[key].add(n)
    ck(all(len(a)==1 for a in values.values()),
       "Cannot prove unique original tower site lat/lon/UTC_OFFSET "+site+
       " "+repr(values))
    lat=next(iter(values["LOCATION_LAT"]))
    lon=next(iter(values["LOCATION_LONG"]))
    off=next(iter(values["UTC_OFFSET"]))
    ck(-90<=lat<=90 and -180<=lon<=180 and
       off.is_integer() and -12<=off<=14,
       "Invalid original BIF geography/native local standard UTC offset "+site)
    return {"site":site,"lat":lat,"lon":lon,"offset":int(off),
            "original_BIF":str(p),"original_BIF_SHA256":sha(p)}
def cds_dir(site,year):
    return CACHE/site/str(year)
def cds_response(site,year):
    d=cds_dir(site,year)
    stem="ERA5Land_"+site+"_"+str(year)+"_STRD_SYVH9"
    return d,stem
def normalize_units(s):
    return (str(s).lower().replace(" ","").replace("*","")
            .replace("^","").replace("{","").replace("}",""))
def netcdf_read(p,year,point):
    import numpy as np
    from netCDF4 import Dataset,num2date
    hours=expected_times(year)
    values=None;sampled=None;source_units=None
    def absorb(ds,label):
        nonlocal values,sampled,source_units
        tm=ds.variables.get("valid_time")
        if tm is None:tm=ds.variables.get("time")
        ck(tm is not None,"CDS STRD NetCDF missing valid_time/time "+label)
        tim=num2date(tm[:],getattr(tm,"units",""),
                     calendar=getattr(tm,"calendar","standard"),
                     only_use_cftime_datetimes=False,only_use_python_datetimes=True)
        parsed=[datetime(x.year,x.month,x.day,x.hour,x.minute,x.second,
                         tzinfo=timezone.utc) for x in tim]
        ck(parsed==hours,
           "CDS STRD UTC hourly timeline missing/reordered for "+
           label+" first/last "+str((parsed[:1],parsed[-1:])))
        ck("latitude" in ds.variables and "longitude" in ds.variables,
           "CDS STRD point lacks sampled lat/lon")
        lat=float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
        lon=float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
        lon=((lon+180)%360)-180
        ck(abs(lat-point["lat"])<=.151 and
           abs(lon-point["lon"])<=.151,
           "CDS STRD wrong tower grid point "+str((lat,lon))+
           " expected "+str((point["lat"],point["lon"])))
        matching=[v for v in ("strd","surface_thermal_radiation_downwards")
                  if v in ds.variables]
        if not matching:return
        ck(values is None and len(matching)==1,
           "CDS STRD field duplicated across ZIP groups "+label)
        raw=ds.variables[matching[0]]
        units=str(getattr(raw,"units",""))
        ck(normalize_units(units) in ("jm-2","jm-02","jm-2"),
           "CDS STRD must be hourly deaccumulated J m^-2; units="+repr(units))
        arr=np.asarray(np.ma.asarray(raw[:]).filled(np.nan),dtype=float).reshape(-1)
        ck(len(arr)==len(hours) and np.isfinite(arr).all(),
           "CDS STRD missing/unexpected hourly grid values")
        # De-accumulated hourly J/m^2, NOT cumulative forecast-step values:
        # The CDS time-series product explicitly promises de-accumulation.
        wm2=arr/3600.
        ck(((wm2>=25)&(wm2<=750)).all(),
           "CDS STRD appears cumulative or wrong units, do NOT divide blindly")
        values=wm2;sampled={"lat":lat,"lon":lon};source_units=units
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(file(p)) as z:
            ck(z.testzip() is None,"Broken CDS STRD ZIP CRC")
            names=[a for a in z.infolist() if not a.is_dir()]
            ck(1<=len(names)<=5 and all(a.filename.endswith(".nc") and
               not a.filename.startswith("/") and
               ".." not in Path(a.filename).parts and
               a.file_size<80_000_000 for a in names),
               "CDS STRD ZIP structure unsafe")
            for item in names:
                with Dataset("inmem.nc","r",memory=z.read(item)) as ds:
                    absorb(ds,item.filename)
    else:
        with file(p).open("rb") as f:magic=f.read(8)
        ck(magic.startswith(b"CDF") or magic==b"\x89HDF\r\n\x1a\n",
           "Unrecognized CDS response payload")
        with Dataset(str(p),"r") as ds:absorb(ds,str(p))
    ck(values is not None and sampled is not None,
       "No verified deaccumulated STRD in CDS file")
    return {"utc_values":{str_time(h):float(x) for h,x in zip(hours,values)},
            "grid":sampled,"unit":source_units,"hours":len(hours),
            "range_W_m2":[float(values.min()),float(values.max())]}
def response(site,year,point):
    d,stem=cds_response(site,year)
    p=d/(stem+".receipt.json")
    if not p.exists():return None
    rec=json.loads(file(p).read_text(encoding="utf-8"))
    source=Path(rec["file"])
    ck(rec["site"]==site and rec["year"]==year and
       rec["variable"]==VARIABLE and rec["dataset"]==DATASET and
       source.parent==d and source.name in (stem+".zip",stem+".nc") and
       sha(source)==rec["sha256"] and
       rec["original_BIF_SHA256"]==point["original_BIF_SHA256"] and
       rec["source_unit_deaccumulated"]==True,
       "CDS independent longwave source receipt or hash changed "+site)
    parsed=netcdf_read(source,year,point)
    ck(parsed["hours"]==rec["hour_count"] and
       parsed["unit"]==rec["units"] and
       parsed["grid"]==rec["grid"],
       "CDS longwave receipt units/location/time changed "+site)
    return source,rec,parsed
def download(site,year,point):
    result=response(site,year,point)
    if result is not None:
        print("CDS STRD VERIFIED CACHE REUSED",site,year,
              result[1]["sha256"],flush=True)
        return result
    d,stem=cds_response(site,year)
    ck(not d.is_symlink() and not CACHE.is_symlink(),
       "Symlink in CDS science source output tree")
    if not d.exists():d.mkdir(parents=True,exist_ok=False)
    for ext in (".zip",".nc",".download.partial",".receipt.json"):
        ck(not (d/(stem+ext)).exists(),
           "Unreceipted prior CDS artifact exists; do not overwrite "+
           str(d/(stem+ext)))
    ck(importlib.util.find_spec("cdsapi") is not None,
       "cdsapi unavailable; requires working clm_fates_env")
    ck((Path.home()/".cdsapirc").is_file() or bool(os.getenv("CDSAPI_KEY")),
       "CDS credentials unavailable; no science/source writes")
    req=request(point["lat"],point["lon"],year)
    print("CDS INDEPENDENT STRD REQUEST",site,year,req,flush=True)
    import cdsapi
    temporary=d/(stem+".download.partial")
    cdsapi.Client().retrieve(DATASET,req).download(str(temporary))
    parsed=netcdf_read(file(temporary),year,point)
    suff=".zip" if zipfile.is_zipfile(temporary) else ".nc"
    final=d/(stem+suff)
    ck(not final.exists(),"CDS response race / duplicate science file")
    temporary.rename(final)
    rec={"site":site,"year":year,"dataset":DATASET,"variable":VARIABLE,
         "request":req,"file":str(final),"sha256":sha(final),
         "source_unit_deaccumulated":True,"units":parsed["unit"],
         "deaccumulated_hour_seconds":3600,
         "hour_count":parsed["hours"],"grid":parsed["grid"],
         "original_BIF_SHA256":point["original_BIF_SHA256"]}
    (d/(stem+".receipt.json")).write_text(json.dumps(rec,indent=2)+"\n")
    print("CDS INDEPENDENT STRD SOURCE SHA VERIFIED",site,year,
          rec["sha256"],"WM2_RANGE",parsed["range_W_m2"],flush=True)
    return final,rec,parsed
def check_original(g7):
    tt=g7.targets()
    fields,old,paths=g7.pinned_inputs()
    original_source={}
    print("SYVH9 SOURCE CHECK: PACKAGED ERA LW IS CONTAMINATED; NO PACKAGED ERA SUBSTITUTIONS")
    for site in sorted(tt):
        chosen,raw,era=paths[site]
        scope=set(tt[site])
        for start,end in g7.EXPECTED[site]:
            scope.update(g7.shift(start,i) for i in range(-4,0))
            scope.update(g7.shift(end,i) for i in range(1,5))
        selected,_=g7.subset(chosen,scope,("TIMESTAMP_START","LW_IN_F"),
                             NATIVE_EXPECTED[site])
        native,_=g7.subset(raw,scope,("TIMESTAMP_START","LW_IN_F"),
                           NATIVE_EXPECTED[site])
        packaged,_=g7.subset(era,scope,("TIMESTAMP_START","LW_IN_ERA"))
        for key in sorted(tt[site]):
            oldlw=g7.val(selected[key]["LW_IN_F"])
            orig=g7.val(native[key]["LW_IN_F"])
            pair=g7.val(packaged[key]["LW_IN_ERA"])
            wanted=g7.OLD_LW_EXPECTED[site][key]
            ck(oldlw is not None and orig is not None and pair is not None and
               abs(oldlw-wanted)<.002 and abs(orig-wanted)<.002 and
               abs(pair-wanted)<.002,
               "12 target source contaminated ERA/FLUXMET provenance differs "+
               site+" "+key+" "+str((oldlw,orig,pair)))
            ck(oldlw<60.,"Target source LW is not a low outlier "+site+" "+key)
            print("BAD PAIRED LW",site,key,
                  "SELECTED",oldlw,"RAW",orig,"PACKAGED_ERA",pair,
                  "RAW_QC",native[key].get("LW_IN_F_QC","UNAVAILABLE"))
        original_source[site]={"chosen":chosen,"raw":raw,"era":era,
            "selected":selected,"native":native,"packaged":packaged,
            "point":bif(raw,site)}
        pt=original_source[site]["point"]
        print("BIF VERIFIED",site,pt,"SELECTED_SOURCE_SHA",sha(chosen))
    ck(len(REQ)==N_REQUESTS and sum(map(len,tt.values()))==12,
       "Expected six independent CDS site-years / 12 original source HH")
    print("SYVH9 SOURCE/BIF/EARLIER_CANDIDATE SHA CHECK PASS",
          "FIVE_SITES",5,"TWELVE_HH",12,"SIX_SITE_YEARS",len(REQ))
    return fields,old,paths,tt,original_source
def decide(g7,tt,sources,grids):
    edits={};per=Counter()
    for site in sorted(tt):
        p=sources[site]["point"];existing=sources[site]["selected"]
        for start,end in g7.EXPECTED[site]:
            utc_start=hour_ending(start,p["offset"])
            utc_end=hour_ending(end,p["offset"])
            ck(utc_start==utc_end,"One two-HH low LW event does not share hourly UTC support "+
               site+" "+start+" "+end)
            gh=grids[(site,int(start[:4]))][2]
            hourkey=str_time(utc_start.replace(tzinfo=None))
            flux=gh["utc_values"].get(hourkey)
            ck(flux is not None and LIMIT_LOW<=flux<=LIMIT_HIGH,
               "Independent hour-ending ERA5Land downwelling longwave unavailable/invalid "+
               site+" "+start+" UTC_END="+hourkey+" VALUE="+str(flux))
            before=g7.val(existing[g7.shift(start,-1)]["LW_IN_F"])
            after=g7.val(existing[g7.shift(end,1)]["LW_IN_F"])
            ck(before is not None and after is not None and
               LIMIT_LOW<=before<=LIMIT_HIGH and
               LIMIT_LOW<=after<=LIMIT_HIGH,
               "Parent longwave anomaly extends beyond original 2HH target "+
               site+" "+start)
            ck(abs(flux-before)<=MAX_BOUNDARY_JUMP and
               abs(flux-after)<=MAX_BOUNDARY_JUMP,
               "Independent ERA5Land longwave leaves >180 W/m² boundary jump "+
               site+" "+start+" "+str((before,flux,after)))
            _,receipt,_=grids[(site,int(start[:4]))]
            print("INDEPENDENT STRD CLOSURE",site,start,end,
                  "PRE_LW",before,"TRIAL_LW_WM2",flux,"POST_LW",after,
                  "UTC_HOUR_END",hourkey,
                  "INDEPENDENT_CDS_SHA",receipt["sha256"])
            for k in (start,end):
                orig=sources[site]["native"][k]
                old=sources[site]["selected"][k]
                edits[(site,k)]={
                    "site":site,"TIMESTAMP_START":k,
                    "source_original_LW_IN_F_Wm2":g7.val(orig["LW_IN_F"]),
                    "source_original_LW_IN_F_QC":orig.get("LW_IN_F_QC","NOT_PRESENT"),
                    "selected_pre_trial_LW_IN_F_Wm2":g7.val(old["LW_IN_F"]),
                    "same_native_packaged_LW_IN_ERA_Wm2":
                        g7.val(sources[site]["packaged"][k]["LW_IN_ERA"]),
                    "new_research_LW_IN_F_Wm2":flux,
                    "native_UTC_offset_hours":p["offset"],
                    "hour_ending_UTC":hourkey,
                    "era5land_STRD_deaccumulated_J_m2":flux*3600.,
                    "era5land_STRD_hourly_W_m2":flux,
                    "era5land_raw_sha256":receipt["sha256"],
                    "era5land_BIF_SHA256":p["original_BIF_SHA256"],
                    "new_source_QC_if_available":"2",
                    "decision":"REPLACE_BAD_PACKAGED_ERA_LW_WITH_SEPARATELY_RETRIEVED_ERA5LAND_STRD",
                    "postv5_or_model_approved":False}
                per[site]+=1
    ck(len(edits)==12 and dict(per)==
       {"US-SP1":4,"US-Slt":2,"US-Syv":2,"US-Ton":2,"US-Uaf":2},
       "Independent longwave target exactness failed")
    print("SYVH9 INDEPENDENT CDS LONGWAVE 12/12 FOURTEEN? NO EXACT TWELVE PREFLIGHT PASS",
          dict(per))
    return edits
def apply(g7,helper,fields,old,paths,edits,grids):
    tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]
    out=OUTBASE/("candidate_"+tag)
    out.mkdir(parents=True,exist_ok=False)
    (out/"RESEARCH_ONLY_NOT_POSTV5_DATM_CIME_SLURM_SPINUP").write_text(
       "Independent ERA5Land deaccumulated hourly longwave, 12 exact HH; model release blocked.\n")
    sitefiles={};sitehash={}
    for site in sorted(paths):
        oldfile=paths[site][0]
        newfile=out/(site+"_SYVH9_independent_STRD_12HH_research_HH.csv")
        nsha=g7.create_one(oldfile,newfile,site,edits)
        g7.diff(oldfile,newfile,site,edits)
        sitefiles[site]=newfile;sitehash[site]=nsha
    combined=[]
    for r in old:
        d=dict(r)
        if d["site"] in sitefiles:
            d["source_path"]=str(sitefiles[d["site"]])
            d["source_SHA256"]=sitehash[d["site"]]
            d["latest_stage"]="SYVH9_INDEPENDENT_ERA5LAND_STRD_12HH_RESEARCH_NOT_MODEL"
        combined.append(d)
    ck([r for r in old if r["site"] not in sitefiles]==
       [r for r in combined if r["site"] not in sitefiles],
       "Unapproved other 5 source selection references changed")
    mf=out/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    with mf.open("x",encoding="utf-8",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        wr.writeheader();wr.writerows(combined)
    ledger=out/"SYVH9_INDEPENDENT_STRD_12_SOURCE_AUDIT.tsv"
    entries=[edits[k] for k in sorted(edits)]
    with ledger.open("x",encoding="utf-8",newline="") as f:
        wr=csv.DictWriter(f,fieldnames=list(entries[0]),delimiter="\t")
        wr.writeheader();wr.writerows(entries)
    receipt={
       "stage":"SYVH9_INDEPENDENT_ERA5LAND_DEACCUMULATED_STRD",
       "independently_retrieved_source_hh":12,
       "affected_sites":sorted(sitefiles),
       "six_site_year_CDS_response_SHAs":
          {s+"_"+str(y):grids[(s,y)][1]["sha256"] for s,y in sorted(REQ)},
       "source_native_HH_QC2_where_column_exists":True,
       "original_paired_ERA_contaminated_all_12_HH":True,
       "input_manifest_SHA256":sha(g7.MANIFEST),
       "new_manifest_sha256":sha(mf),
       "new_manifest_path":str(mf),
       "new_selected_site_SHAs":sitehash,
       "no_old_source_modified":True,"research_only":True,
       "model_ready":False,"DATM_ready":False,"Postv5_ready":False}
    (out/"SYVH9_SCIENCE_RECEIPT.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("SYVH9 FIVE SITE INDEPENDENT ERA5LAND RESEARCH FULL SOURCE DIFF PASS",out)
    print("SYVH9 NEW FINAL TEN SITE MANIFEST",mf)
    print("SYVH9 NEW FIVE SOURCE SHAS",sitehash)
    # Finally independently re-check all 10 complete native series with
    # the existing, source-independent SYVH6 seven-field/NOLEAP auditor.
    gate=mod(H6,"syvh9_existing_independent_seven_met_gate")
    gate.selftest(helper)
    results=[gate.analyze(r["site"],r,helper) for r in combined]
    bad={r["site"]:r["numeric_blockers"] for r in results if r["numeric_blockers"]}
    three=sum(x["conservative_nonproduction_policy_flags"].get(
        "VPD_NATIVE_THREE_DECIMAL_ROUNDING",0) for x in results)
    ck(three==3,"Expected precisely 3 preexisting native VPD roundoffs")
    (out/"SYVH9_TEN_SITE_GATE0_READONLY_RESULTS.json").write_text(
        json.dumps({"ten_sites":results,"blocked":bad,
          "native_VPD_source_rounding_HH":three,
          "numeric_gate0_pass":not bool(bad),
          "postv5_approved":False,"DATM_ready":False,
          "spinup_approved":False},indent=2)+"\n")
    print("SYVH9 FINAL 10 SITE NOLEAP SEVEN MET GATE0",
          "READY",10-len(bad),"BLOCKED",bad,"SOURCE_ROUNDING_HH",three)
    if not bad:
        print("SYVH9 COMPLETE TEN SITE NUMERICAL SEVEN MET GATE0 PASS - RESEARCH ONLY")
    print("NO ORIGINAL / UPSTREAM SCIENCE / SURFACE / DATM / CIME / SLURM WRITES")
def main():
    a=argparse.ArgumentParser(description=__doc__)
    group=a.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--check",action="store_true")
    group.add_argument("--run",action="store_true")
    z=a.parse_args()
    ck(len(REQ)==6 and
       hour_ending("200412040000",-6)==hour_ending("200412040030",-6) and
       abs((720000./3600.)-200)<1e-9 and
       hour_ending("201610091900",-7).hour==3,
       "Synthetic 2004/2016 native local UTC/hour-ending mapping invalid")
    print("SYVH9 SELF-TEST PASS 12 exact low LW, six independent site-years, UTC hour-ending, deaccumulated J/m2 to W/m2; no writes")
    if z.self_test:return
    g7=mod(ERA7,"syvh9_original_sha_source_stages")
    fields,old,paths,tt,sources=check_original(g7)
    if z.check:
        print("SYVH9 READ ONLY SOURCE AND 12HH PACKAGED ERA CONTAMINATION CHECK PASS; no downloads/no writes")
        return
    helper=mod(H5,"syvh9_source_aware_helper")
    ck(len({s for s,y in REQ})==5,"Expected five sites across six site-years")
    checked={}
    for site,year in sorted(REQ):
        checked[(site,year)]=download(site,year,sources[site]["point"])
    edits=decide(g7,tt,sources,checked)
    apply(g7,helper,fields,old,paths,edits,checked)
if __name__=="__main__":main()

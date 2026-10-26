#!/usr/bin/env python3
"""Stage87: immediately build *five* available Batch02 annual DATM NetCDF previews.

Stage86 operator proves no complete 10-site selection/Post-v5. The already
successful Stage07 five candidates are BZS, CMW, Ha1, Ho2, Ho3. Produce
only technical-preview NOLEAP NetCDF and UNACTIVATED stream templates,
no false claim the other five are complete. Do not rerun historical
Stage08 or rewrite Ho1 2000 Stage85. Do not auto-release QC0 changes,
sensor ZBOT or unverified clock/interval midpoint conventions.

SHA-verify original Stage07 manifest and original forcing CSV output
digests; retain source of all numeric candidate values. Point grid
lat/lon come ONLY from existing site CLM 2000 point surface NetCDF.
Ha1 native HOURLY (8760/year), remaining four sites halfhourly
(17520/year); leap Feb29 is absent in Stage07 numeric candidate.
No model jobs / CIME / original CSV / original surface modifications.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timedelta,timezone
from uuid import uuid4
from xml.sax.saxutils import escape

import numpy as np
try:
    import netCDF4 as nc
except ImportError as e:
    raise RuntimeError("Run inside clm_fates_env with netCDF4 installed") from e

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
SURFROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EXPECTED={"US-BZS":30,"US-CMW":30,"US-Ha1":60,
          "US-Ho2":30,"US-Ho3":30}
NC_FIELDS=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","SHUM","RH")
BASE_COLS=("time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms")
UNITS={"TBOT":"K","QBOT":"kg kg-1","SHUM":"kg kg-1",
       "RH":"percent","PSRF":"Pa","FSDS":"W m-2","FLDS":"W m-2",
       "WIND":"m s-1","PRECTmms":"mm s-1"}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for x in iter(lambda:f.read(1048576),b""):h.update(x)
    return h.hexdigest()

def source():
    if not STAGE07.is_dir():
        raise ValueError("Original Stage07 numeric candidate directory missing")
    if not (STAGE07/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Expected original incomplete ten-site Stage07 marker missing")
    m=json.loads((STAGE07/"exact_input_manifest.json").read_text())
    if m.get("algorithm")!="HISTORICAL_QCV5_NATIVE_HH_HR_ADAPTATION":
        raise ValueError("Original Stage07 method differs")
    if len(m["sites"])!=10:
        raise ValueError("Stage07 original release manifest requires 10 exact sites")
    record=json.loads((STAGE07/"output_sha256.json").read_text())
    preserved=json.loads((STAGE07/"input_preservation_check.json").read_text())
    if preserved.get("unchanged") is not True:
        raise ValueError("Original Stage07 input preservation was not PASS")
    statuses={}
    for r in m["sites"]:
        site=r["site"]
        if site not in EXPECTED:continue
        if r["native_minutes"]!=EXPECTED[site]:
            raise ValueError("Stage07 original site native interval changed")
        start,end=int(r["first_year"]),int(r["last_year"])
        p=STAGE07/site/"forcing/processed_v5"/f"{site}_CLM_forcing_{start}_{end}.csv"
        status_path=STAGE07/site/"forcing/qc_v5"/f"{site}_status.json"
        relative=str(p.relative_to(STAGE07))
        if not p.is_file() or relative not in record or sha(p)!=record[relative]:
            raise ValueError("Verified Stage07 forcing CSV absent or SHA drift: "+site)
        if status_path.is_file():
            old=json.loads(status_path.read_text())
            if (old.get("site")!=site or old.get("noleap_rows")!=
                (end-start+1)*365*1440//EXPECTED[site]):
                raise ValueError("Original Stage07 site numeric status census changed: "+site)
        else:
            raise ValueError("Original Stage07 numeric status missing: "+site)
        statuses[site]={"site":site,"first_year":start,"last_year":end,
          "step":EXPECTED[site],"source":p,"sha256":record[relative],
          "status":old.get("status"),"source_total_edits":old.get("changes")}
    if set(statuses)!=set(EXPECTED):
        raise ValueError("Five verified Stage07 site census incomplete")
    return [statuses[k] for k in sorted(statuses)]

def point_surface(site):
    options=list((SURFROOT/site/"subset_data_batch02_surf2000").glob("surfdata*.nc"))
    if len(options)!=1:
        raise ValueError(site+" requires exactly one existing Batch02 2000 point surface")
    path=options[0]
    with nc.Dataset(path) as d:
        for name in ("LONGXY","LATIXY"):
            if name not in d.variables:
                raise ValueError(site+" original point surface lacks "+name)
        lon=np.ma.filled(d.variables["LONGXY"][:],np.nan).astype(float).ravel()
        lat=np.ma.filled(d.variables["LATIXY"][:],np.nan).astype(float).ravel()
    if (len(lon)!=1 or len(lat)!=1 or not
        (np.isfinite(lon[0]) and np.isfinite(lat[0]) and
         -90<=lat[0]<=90 and -180<=lon[0]<=360)):
        raise ValueError(site+" original point surface not one valid point")
    return path,sha(path),float(lat[0]),float(lon[0])

def times(year,step):
    first=datetime(year,1,1)
    for day in range(366 if year%4==0 and (year%100!=0 or year%400==0) else 365):
        stamp=first+timedelta(days=day)
        if stamp.month==2 and stamp.day==29:continue
        for i in range(1440//step):
            yield stamp+timedelta(minutes=i*step)

def values(row,site,when,step):
    out={}
    for field in BASE_COLS[1:]:
        try: v=float(row[field])
        except (KeyError,TypeError,ValueError) as e:
            raise ValueError(site+" missing/nonnumeric "+field+" at "+when) from e
        if not math.isfinite(v):
            raise ValueError(site+" nonfinite "+field+" at "+when)
        out[field]=v
    if not (180<out["TBOT"]<340 and 49000<out["PSRF"]<111000
        and 0<out["QBOT"]<.08 and 0<=out["FSDS"]<=1600 and
        0<=out["FLDS"]<=800 and 0<=out["WIND"]<=75
        and 0<=out["PRECTmms"]<=300/(step*60)):
        raise ValueError(site+" source forcing numeric bounds fail "+when)
    T=out["TBOT"]-273.15
    p=out["PSRF"]/100.0
    e=out["QBOT"]*p/(.622+.378*out["QBOT"])
    es=6.112*math.exp(17.67*T/(T+243.5))
    RH=100*e/es
    if not math.isfinite(RH) or not (0<RH<=100.05):
        raise ValueError(site+" source QBOT/T/P RH inconsistent "+when)
    out["SHUM"]=out["QBOT"]
    out["RH"]=RH
    return out

def site_years(info):
    src=info["source"]; step=info["step"]; site=info["site"]
    per_year=365*1440//step
    with src.open("r",newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if len(reader.fieldnames or [])!=len(set(reader.fieldnames or [])) or not set(BASE_COLS)<=set(reader.fieldnames or []):
            raise ValueError(site+" Stage07 numeric forcing columns changed")
        for year in range(info["first_year"],info["last_year"]+1):
            current=[]
            for stamp in times(year,step):
                row=next(reader,None)
                if row is None:
                    raise ValueError(site+" forcing ended early at "+str(stamp))
                expected=stamp.strftime("%Y-%m-%d %H:%M:%S")
                if row["time"]!=expected:
                    raise ValueError(site+" wrong original NOLEAP time "+repr(row["time"])+" vs "+expected)
                current.append(values(row,site,expected,step))
            if len(current)!=per_year:
                raise ValueError(site+" incomplete original forcing year "+str(year))
            yield year,current
        if next(reader,None) is not None:
            raise ValueError(site+" forcing has extra rows after last release year")

def save_nc(path,info,year,rows,lat,lon,surf_hash):
    step=info["step"]
    n=len(rows)
    with nc.Dataset(path,"w",format="NETCDF4_CLASSIC") as d:
        d.createDimension("time",n)
        d.createDimension("lat",1)
        d.createDimension("lon",1)
        t=d.createVariable("time","f8",("time",))
        t.units=f"days since {year}-01-01 00:00:00"
        t.calendar="noleap"
        t.long_name="Original source local-start timestamp; actual interval centering requires case approval"
        t[:]=np.arange(n,dtype="f8")*step/(24*60)
        y=d.createVariable("lat","f8",("lat",));y.units="degrees_north";y[:]=[lat]
        x=d.createVariable("lon","f8",("lon",));x.units="degrees_east";x[:]=[lon]
        xx=d.createVariable("LONGXY","f8",("lat","lon"));xx[:]=[[lon]]
        yy=d.createVariable("LATIXY","f8",("lat","lon"));yy[:]=[[lat]]
        for name in NC_FIELDS:
            v=d.createVariable(name,"f8",("time","lat","lon"),zlib=True,complevel=2)
            v.units=UNITS[name]
            v[:,0,0]=np.asarray([r[name] for r in rows],dtype="f8")
        d.Conventions="CF-1.8"
        d.source_original_forcing_sha256=info["sha256"]
        d.source_original_surface_sha256=surf_hash
        d.site_id=info["site"]
        d.source_interval_minutes=step
        d.forcing_validation="STAGE07_NUMERIC_ONLY_STAGE09_POSTV5_NOT_RUN"
        d.ZBOT="UNVERIFIED_AND_NOT_WRITTEN"
        d.historical_clock="UNVERIFIED_NATIVE_SOURCE_LOCAL_LABEL"
        d.science_approval="FALSE_TECHNICAL_PREVIEW_ONLY"

def make_template(folder,site,years):
    names="\n".join("        "+str(year)+".nc" for year in years)
    names_fields="\n".join("        "+name+" "+name for name in (
        "FLDS","FSDS","PRECTmms","PSRF","TBOT","WIND","SHUM"))
    content=f"""<streamstemplate>
<stream><dataSource>CLMNCEP</dataSource>
<domainInfo><filePath>REPLACE_WITH_SITE_VERIFIED_DOMAIN</filePath>
<fileNames>REPLACE_WITH_SITE_VERIFIED_DOMAIN.nc</fileNames></domainInfo>
<fieldInfo>
<variableNames>
{names_fields}
</variableNames>
<offset>0</offset>
<filePath>{escape(str(folder))}</filePath>
<fileNames>
{names}
</fileNames>
</fieldInfo></stream></streamstemplate>
"""
    p=folder.parent/f"datm.streams.{site}.TEMPLATE_NOT_ACTIVATED.txt"
    p.write_text(content)
    return p

def self_test():
    assert len(list(times(2000,30)))==17520
    assert len(list(times(2000,60)))==8760
    assert datetime(2000,2,29,0,0) not in set(times(2000,60))
    assert len(EXPECTED)==5 and set(EXPECTED)=={
       "US-BZS","US-CMW","US-Ha1","US-Ho2","US-Ho3"}
    sample={"TBOT":273.15,"QBOT":0.003,"PSRF":100000,
            "FSDS":50,"FLDS":300,"WIND":2,"PRECTmms":0.0001}
    assert 0<values(sample,"TEST","2000",30)["RH"]<=100
    print("STAGE87 SELF-TEST PASS | five exact sources, native HH/HR NOLEAP, 7 DATM fields, no original writes")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","build"):
        g.add_argument("--"+mode,action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test();return
    entries=source()
    inputs=[]
    for entry in entries:
        surf,surfsha,lat,lon=point_surface(entry["site"])
        inputs.append({**entry,"surface":surf,"surface_sha":surfsha,
                       "lat":lat,"lon":lon})
    total=sum(x["last_year"]-x["first_year"]+1 for x in inputs)
    print("STAGE87 SOURCE AND SURFACE SHA PASS",len(inputs),"/5")
    for entry in inputs:
        print("SOURCE",entry["site"],entry["first_year"],entry["last_year"],
              "native_minutes",entry["step"],
              "netCDF",entry["last_year"]-entry["first_year"]+1,
              "numeric_original_status",entry["status"])
    print("STAGE87 TECHNICAL NC YEAR FILES EXPECTED",total)
    if a.check:
        print("STAGE87 CHECK PASS | 5 preserved candidate SHA and point-surfaces; no files written")
        return
    output=ROOT/"reports"/("stage87_five_site_DATM_NetCDF_technical_preview_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    marker=output/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Scientific/PFT/ZBOT/time/Stage09 approval not granted.\n")
    summary=[]
    for entry in inputs:
        site=entry["site"]
        directory=output/site/"yearly"
        directory.mkdir(parents=True)
        files=[]
        for year,rows in site_years(entry):
            target=directory/f"{year}.nc"
            save_nc(target,entry,year,rows,entry["lat"],entry["lon"],entry["surface_sha"])
            with nc.Dataset(target) as d:
                if (len(d.dimensions["time"])!=365*1440//entry["step"] or
                    d.variables["time"].calendar!="noleap" or
                    not set(NC_FIELDS)<=set(d.variables)):
                    raise ValueError(site+" independent NC readback failed")
            files.append({"year":year,"path":str(target),"sha256":sha(target)})
        template=make_template(directory,site,range(entry["first_year"],entry["last_year"]+1))
        summary.append({
          "site":site,"native_minutes":entry["step"],
          "original_stage07_forcing":str(entry["source"]),
          "original_stage07_forcing_sha256":entry["sha256"],
          "original_point_surface":str(entry["surface"]),
          "original_point_surface_sha256":entry["surface_sha"],
          "yearly_netcdf_files":files,
          "stream_template":str(template),
          "stream_template_sha256":sha(template)})
        print("STAGE87 NETCDF BUILD PASS",site,len(files),"annual files; template NOT ACTIVATED",flush=True)
    if sum(len(k["yearly_netcdf_files"]) for k in summary)!=total:
        raise ValueError("Incomplete five-site source year files")
    manifest={
      "schema":"STAGE87_BATCH02_FIVE_SITES_DATM_TECHNICAL_PREVIEW_v1",
      "sites_built":len(summary),"netcdf_year_files":total,
      "scientific_release":False,"active_DATM_streams_changed":False,
      "original_stage07_incomplete_marker_preserved":True,
      "Ho1_Stage85_candidate_not_overwritten_or_integrated":True,
      "other_five_sites_still_missing_numeric_complete_forcing":True,
      "unresolved_Stage09_postv5_science_ZBOT_local_offset":True,
      "historical_local_clock_time_support_unapproved":True,
      "original_source_CIME_Slurm_untouched":True,
      "Stage07_input_manifest_SHA256":sha(STAGE07/"exact_input_manifest.json"),
      "Stage07_output_receipt_SHA256":sha(STAGE07/"output_sha256.json"),
      "sites":summary}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    marker.unlink()
    print("STAGE87 BUILD PASS | FIVE SITES",len(summary),
          "NC ANNUAL FILES",total,"STREAM TEMPLATES",len(summary))
    print("STAGE87 TECHNICAL PREVIEW ONLY | 5 other sites, Post-v5 science, ZBOT, clock, CIME remain BLOCKED")
    print("REPORT",output)
    print("NO RAW SOURCE/CURRENT FORCING/DATM CASE/SLURM MODIFICATIONS")
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage63 Batch02: conservative AUTOMATIC source QC of Stage62's 246 |TA-ERA5|>8C.

Checks exact original FLUXNET primary SHA, native timestamp/row identity,
temperature QC, 1- and 2-step neighbor continuity, and extreme-cold physics.
Original tower T is retained for strong-consistency cases without another
user-by-user review; otherwise HOLD for localized source investigation.
Derives independent ERA5 water-RH/VPD/QBOT ONLY for temperature-accepted
cases from existing authenticated Stage62 t2m/RH and original EC pressure.
No changes to raw data, Stage60/62, official BIF, DATM or model forcing.
Also emits an original-release ZIP/BIF discovery inventory for US-BZS and
US-Ho1 WITHOUT presuming a candidate BIF is exact-release metadata.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
S62=REPORT/"stage62_nonHo1_5133_verified_CDS_stage_20261024T225848Z_db032320"
M62="candidate_ledger_manifest.json"
EVENTS="5133_uncovered_hard_events_CDS_candidate_status.csv"
T_ROUTE="HOLD_ORIGINAL_TOWER_T_VS_ERA5_GT8C"
SELECTED="AUTO_KEEP_ORIGINAL_TA_F_SOURCE_NEIGHBOR_VALIDATED_COLD"
BIF_SITES=("US-BZS","US-Ho1")
SITES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1","US-Ho1",
       "US-Ho2","US-Ho3","US-ICh","US-ICt")
BIF_MAX=20*1024*1024
DATASET="reanalysis-era5-single-levels-timeseries"

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def native_time(x):
    return pd.to_datetime(str(x).strip(),format="%Y%m%d%H%M",errors="raise")

def number(x):
    try:
        y=float(x)
        return y if math.isfinite(y) and y>-9990 else float("nan")
    except (ValueError,TypeError):
        return float("nan")

def read_source():
    m=json.loads((S62/M62).read_text())
    if ((S62/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE62_BATCH02_NONHO1_5133_CDS_ERA5_REUSE_OR_FETCH_v1" or
        m.get("target_original_hard_nonHo1")!=5133 or
        m.get("unresolved_original_hard_Ho1")!=16788 or
        m.get("prior_stage60_proposals_unmodified")!=4411 or
        m.get("missing_CDS_gridyears")!=0 or
        m.get("independently_verified_CDS_gridyears")!=50 or
        m.get("approved_for_DATM") is not False or
        m.get("no_original_or_model_changes") is not True):
        raise ValueError("Stage62 verified 50-gridyear source gate invalid")
    shas=m.get("outputs_SHA256",{})
    for name,expected in shas.items():
        if digest(S62/name)!=expected:
            raise ValueError("Stage62 source output SHA256 changed "+name)
    ds=pd.read_csv(S62/EVENTS,dtype={"site":str,"timestamp_start":str,
                                   "source_sha256":str})
    if len(ds)!=5133 or ds.duplicated(["site","timestamp_start"]).any():
        raise ValueError("Stage62 exact event census changed")
    if (not set(ds.site).issubset(set(SITES)) or
        ds.candidate_status.eq(T_ROUTE).sum()!=246 or
        ds.candidate_status.eq("HOLD_RELEASE_BIF_UNVERIFIED").sum()!=86 or
        ds.candidate_status.eq("CANDIDATE_EXTERNAL_ERA5_WATER_HUMIDITY_ORIGINAL_T_PA").sum()!=4801 or
        int(ds.candidate_status.str.startswith("HOLD_VERIFIED_EXTERNAL_CDS_GRIDYEAR_MISSING").sum())!=0):
        raise ValueError("Stage62 status science counts mismatch")
    target=ds.loc[ds.candidate_status.eq(T_ROUTE)].copy()
    if not m.get("source_SHA256",{}).get("Stage61_manifest_sha256"):
        raise ValueError("Missing Stage61 original source SHA reference")
    stage61=REPORT/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
    if digest(stage61/"coverage_manifest.json")!=m["source_SHA256"]["Stage61_manifest_sha256"]:
        raise ValueError("Stage61 parent changed")
    m61=json.loads((stage61/"coverage_manifest.json").read_text())
    m49=json.loads((Path(m61["stage49_source"])/"provenance_and_hold.json").read_text())
    inv=Path(m49["inventory"]).resolve(strict=True)
    if digest(inv)!=m49["inventory_sha256"]:
        raise ValueError("Stage49 source inventory changed")
    members=json.loads(inv.read_text()).get("completed",[])
    spec={}
    for site in SITES:
        a=[r for r in members if r["site"]==site and not str(r["source"]).startswith("ERA5")]
        if len(a)!=1:
            raise ValueError("Original input source not unique "+site)
        r=a[0]
        if digest(r["file"])!=r["sha256"] or m49["primary_sha256_by_site"].get(site)!=r["sha256"]:
            raise ValueError("Original primary SHA256 changed "+site)
        spec[site]=r
    for site,part in target.groupby("site"):
        if not part.source_sha256.eq(spec[site]["sha256"]).all():
            raise ValueError("Stage62/source original file identity differs "+site)
    return target,spec,dict(stage62_report_sha256=digest(S62/EVENTS),
          stage62_manifest_sha256=digest(S62/M62),
          stage49_inventory_sha256=digest(inv),
          primary_sha256={s:spec[s]["sha256"] for s in SITES})

def sample_original(p,spec,indices,chunk_size=120000):
    """Only selected physical CSV lines; never load multi-million-line EC CSV."""
    required=sorted(set(i for index in indices for i in
                   range(index-4,index+5) if i>=2))
    cols=spec.get("columns",{})
    q=spec.get("qc_columns",{}).get("TA")
    ta=cols.get("TA")
    if not ta:raise ValueError("Source TA_F column absent")
    head=set(pd.read_csv(p,nrows=0).columns)
    use=["TIMESTAMP_START",ta]+([q] if q in head else [])
    if not set(use).issubset(head):
        raise ValueError("Original tower TIMESTAMP_START/TA absent")
    lookup=set(required)
    found={}
    offset=0
    for chunk in pd.read_csv(p,dtype="string",usecols=use,chunksize=chunk_size):
        first=offset+2;last=first+len(chunk)-1
        ix=[i for i in required if first<=i<=last and i not in found]
        for physical_line in ix:
            record=chunk.iloc[physical_line-first]
            found[physical_line]={"time":str(record["TIMESTAMP_START"]).strip(),
               "TA":number(record[ta]),
               "QC":number(record[q]) if q in head else float("nan")}
        offset+=len(chunk)
    if not lookup.intersection(found):
        raise ValueError("No source row context found")
    return found

def classify_event(event,rows,step):
    index=int(event.source_csv_row)
    exact=rows.get(index)
    if not exact:
        raise ValueError("Original EC source row missing "+str(index))
    if native_time(exact["time"])!=native_time(event.timestamp_start):
        raise ValueError("Original site/native timestamp identity mismatch")
    t=number(event.TA_C)
    qc=number(event.TA_original_QC)
    era=number(event.ERA5_t2m_C)
    rh=number(event.ERA5_RH_water_pct)
    p=number(event.PA_kPa)
    if not np.isclose(t,exact["TA"],rtol=0,atol=1.e-5,equal_nan=True):
        raise ValueError("Original TA differs from Stage62 exact row")
    if not np.isclose(qc,exact["QC"],rtol=0,atol=1.e-6,equal_nan=True):
        raise ValueError("Original TA QC differs from Stage62 exact row")
    origin=native_time(exact["time"])
    details={}
    aligned=True;neighbor_good=True;deviations=[]
    for k in (-4,-2,-1,1,2,4):
        sample=rows.get(index+k)
        minutes=int(k*step)
        tag=("m" if k<0 else "p")+str(abs(minutes))
        valid=False
        if sample:
            try:
                valid=(native_time(sample["time"])-origin==pd.Timedelta(minutes=minutes)
                       and np.isfinite(sample["TA"]))
            except (TypeError,ValueError):
                valid=False
        if k in (-2,-1,1,2) and not valid:
            aligned=False
        if valid:
            value=sample["TA"]
            deviations.append(abs(value-t))
            if k in (-2,-1,1,2) and sample["QC"] not in (0,1):
                neighbor_good=False
            details["TA_"+tag+"_C"]=value
            details["QC_"+tag]=sample["QC"]
        else:
            details["TA_"+tag+"_C"]=np.nan
            details["QC_"+tag]=np.nan
    near=[details.get("TA_m"+str(step)+"_C"),details.get("TA_p"+str(step)+"_C")]
    outer=[details.get("TA_m"+str(step*2)+"_C"),details.get("TA_p"+str(step*2)+"_C")]
    close=all(np.isfinite(v) for v in near+outer)
    interp=(near[0]+near[1])/2 if close else np.nan
    smooth=(close and abs(near[1]-near[0])<=3
        and abs(t-interp)<=2 and all(abs(t-v)<=4 for v in near+outer))
    # QC2 auto-signoff requires a strict, quiet surrounding record and
    # moderate external discrepancy. QC0/1 get wider but finite tolerances.
    qc_acceptable=qc in (0,1,2)
    qc2_strong=(qc==2 and close and neighbor_good and
                abs(near[1]-near[0])<=2 and abs(t-interp)<=1
                and all(abs(t-v)<=2.5 for v in near+outer))
    phase_ok=(np.isfinite(t) and t<0)
    physics=(np.isfinite(t) and -80<t<65 and
       np.isfinite(p) and 50<p<110 and
       np.isfinite(era) and np.isfinite(rh) and 0<rh<=100.05)
    gap=abs(t-era)
    decision=("HOLD_CONTEXT_NEIGHBORS_OR_NATIVE_TIME_INCOMPLETE"
        if not aligned or not close else
        "HOLD_ORIGINAL_TA_OUTSIDE_COLD_POLICY" if not phase_ok else
        "HOLD_ORIGINAL_TA_OR_CDS_PHYSICS" if not physics else
        "HOLD_TA_QC_UNKNOWN" if not qc_acceptable else
        "HOLD_NEIGHBOR_QC_UNVERIFIED" if not neighbor_good else
        "HOLD_TEMPORAL_JUMP_OR_NONSTATIONARY" if not smooth else
        "HOLD_QC2_NEEDS_STRONGER_NEIGHBOR_CONTEXT" if qc==2 and not qc2_strong else
        "HOLD_EXTERNAL_T_DELTA_OVER25C" if gap>25 else
        SELECTED)
    es=6.112*np.exp(17.67*t/(t+243.5)) if physics else np.nan
    vap=es*rh/100 if physics else np.nan
    vpd=es-vap if physics else np.nan
    den=p*1000-.378*vap*100 if physics else np.nan
    q=.622*vap*100/den if physics and den>0 else np.nan
    if decision==SELECTED and not (
       0<=vpd and np.isfinite(q) and 0<q<.08):
        decision="HOLD_RECONSTRUCTED_WATER_VAPOR_PHYSICS"
    return dict(site=event.site,
       timestamp_start=event.timestamp_start,
       source_sha256=event.source_sha256,
       source_csv_row=index,
       original_TA_C=t,original_TA_QC=qc,
       ERA5_T2M_C=era,abs_tower_minus_ERA5_T_C=gap,
       source_PA_kPa=p,ERA5_RH_water_pct=rh,
       neighbor_temporal_continuity=bool(aligned),
       neighbor_QC0_or_QC1=bool(neighbor_good),
       neighbor_smooth_both_sides=bool(smooth),
       original_tower_T_decision=decision,
       independent_ERA5_water_VPD_hPa=vpd if decision==SELECTED else np.nan,
       independent_ERA5_water_QBOT_kgkg=q if decision==SELECTED else np.nan,
       approved_for_DATM=False,
       **details)

def zip_bif_discovery(spec):
    """Discover metadata candidates; never assert UTC_OFFSET from ZIP alone."""
    out=[]
    for site in BIF_SITES:
        primary=Path(spec[site]["file"]).resolve(strict=True)
        dirs=[primary.parent,primary.parent.parent,
              primary.parent.parent.parent]
        candidates={}
        for parent in dirs:
            if not parent.is_dir():continue
            for p in parent.glob("*.zip"):
                if site in p.name and p.is_file() and not p.is_symlink():
                    candidates[str(p.resolve())]=p
        count=0
        for p in sorted(candidates.values(),key=str)[:20]:
            count+=1
            record={"site":site,"zip_path":str(p),"zip_sha256":digest(p),
                    "matching_original_primary_name_in_zip":False,
                    "BIF_candidates":[],"source_release_verified":False}
            try:
                with zipfile.ZipFile(p) as z:
                    names=z.namelist()
                    originals=[x for x in z.infolist() if
                        not x.is_dir() and Path(x.filename).name==primary.name
                        and x.file_size==primary.stat().st_size]
                    record["matching_original_primary_name_in_zip"]=bool(originals)
                    source_exact=False
                    if len(originals)==1:
                        h=hashlib.sha256()
                        with z.open(originals[0]) as stream:
                            for block in iter(lambda:stream.read(1<<20),b""):
                                h.update(block)
                        source_exact=(h.hexdigest()==spec[site]["sha256"])
                    record["original_primary_SHA256_same_release"]=source_exact
                    bif=[x for x in z.infolist() if (not x.is_dir() and
                         site in Path(x.filename).name and
                         "_BIF_" in Path(x.filename).name and
                         x.file_size<=BIF_MAX)]
                    for member in bif:
                        try:
                            with z.open(member) as stream:
                                buf=io.TextIOWrapper(stream,encoding="utf-8-sig",newline="")
                                items=csv.DictReader(buf)
                                values={}
                                for item in items:
                                    if item.get("SITE_ID","").strip() not in ("",site):
                                        continue
                                    key=item.get("VARIABLE","").strip().upper()
                                    if key in ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET"):
                                        value=item.get("DATAVALUE","").strip()
                                        if value and value!="-9999":
                                            values.setdefault(key,set()).add(value)
                                unique={k:list(v)[0] for k,v in values.items()
                                        if len(v)==1}
                                valid=(source_exact and
                                   all(k in unique for k in
                                       ("LOCATION_LAT","LOCATION_LONG","UTC_OFFSET")))
                                if valid:
                                    lat=float(unique["LOCATION_LAT"])
                                    lon=float(unique["LOCATION_LONG"])
                                    utc=float(unique["UTC_OFFSET"])
                                    valid=(-90<=lat<=90 and -180<=lon<=180
                                           and -12<=utc<=14
                                           and utc*2==int(utc*2))
                                record["BIF_candidates"].append({
                                    "member":member.filename,
                                    "values":{k:sorted(v) for k,v in values.items()},
                                    "BIF_same_archive_original_primary_SHA256_verified":
                                        bool(valid)})
                                record["source_release_verified"]=bool(valid) or record["source_release_verified"]
                        except (OSError,UnicodeError,ValueError,csv.Error) as e:
                            record["BIF_candidates"].append({"member":member.filename,
                                "parse_error":str(e)})
            except (OSError,zipfile.BadZipFile) as e:
                record["zip_read_error"]=str(e)
            out.append(record)
        if count==0:
            out.append({"site":site,"zip_path":"",
              "source_release_verified":False,
              "metadata_status":"NO_ADJACENT_RELEASE_ARCHIVE_FOUND"})
    return out

def self_test():
    base=pd.Timestamp("2011-12-31 00:00")
    row={i:{"time":(base+pd.Timedelta(minutes=i*30)).strftime("%Y%m%d%H%M"),
             "TA":-30+.03*i,"QC":0.} for i in range(-4,5)}
    # Physical row number must be >=2
    rows={20+i:v for i,v in row.items()}
    z=type("E",(),dict(site="US-EML",timestamp_start="201112310000",
        source_csv_row=20,source_sha256="x",TA_C=-30.,TA_original_QC=0,
        ERA5_t2m_C=-40.,ERA5_RH_water_pct=75.,PA_kPa=98.))
    got=classify_event(z,rows,30)
    assert got["original_tower_T_decision"]==SELECTED
    assert got["independent_ERA5_water_QBOT_kgkg"]>0
    rows[19]["TA"]=-10
    bad=classify_event(z,rows,30)
    assert bad["original_tower_T_decision"]=="HOLD_TEMPORAL_JUMP_OR_NONSTATIONARY"
    assert got["approved_for_DATM"] is False
    print("STAGE63 SELF-TEST PASS | 246 exact original T >8C automatic cold neighbor screen + metadata discovery")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test",action="store_true")
    group.add_argument("--check",action="store_true")
    group.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    target,spec,pins=read_source()
    results=[]
    for site,d in target.groupby("site",sort=True):
        src=Path(spec[site]["file"])
        index=pd.to_numeric(d.source_csv_row,errors="raise").astype(int)
        samples=sample_original(src,spec[site],index)
        cadence=60 if site=="US-Ha1" else 30
        for row in d.itertuples(index=False):
            results.append(classify_event(row,samples,cadence))
        print("SITE TEMPERATURE SOURCE",site,"events",len(d),flush=True)
    table=pd.DataFrame(results).sort_values(["site","timestamp_start"])
    if len(table)!=246 or table.duplicated(["site","timestamp_start"]).any():
        raise ValueError("Stage63 expected 246 unique >8C original T evidence rows")
    # BIF metadata discovery may find candidates; no unverified release approval.
    meta=zip_bif_discovery(spec)
    counts=dict(Counter(table.original_tower_T_decision))
    print("STAGE63 ORIGINAL SOURCE CHECK PASS | exact 246 tower T differences")
    print("STAGE63 AUTOMATIC DECISIONS",counts)
    print("METADATA_CANDIDATE_ARCHIVES",json.dumps(meta,ensure_ascii=False))
    print("HOLD_ROWS",table.loc[table.original_tower_T_decision.ne(SELECTED),
           ["site","timestamp_start","original_TA_C","ERA5_T2M_C",
            "original_TA_QC","original_tower_T_decision"]].to_string(index=False))
    print("All acceptance is original TA-only; NO DATM/forcing approval")
    if a.check:
        print("STAGE63 CHECK PASS | zero report/model writes")
        return
    dest=REPORT/("stage63_246_temperature_auto_neighbor_QC_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Temperature candidates only; not model forcing.\n")
    outputs={"246_exact_original_temperature_neighbor_source_decisions.csv":table,
         "temperature_auto_decision_summary.csv":
             pd.DataFrame([{"status":k,"n":v} for k,v in sorted(counts.items())])}
    shas={}
    for name,frame in outputs.items():
        filename=dest/name
        frame.to_csv(filename,index=False)
        shas[name]=digest(filename)
    bif=dest/"BZS_Ho1_original_archive_BIF_discovery.json"
    bif.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+"\n")
    shas[bif.name]=digest(bif)
    if digest(S62/EVENTS)!=pins["stage62_report_sha256"]:
        raise ValueError("Stage62 source changed during audit")
    for site in SITES:
        if digest(spec[site]["file"])!=pins["primary_sha256"][site]:
            raise ValueError("Original primary changed during Stage63 audit")
    (dest/"source_and_science_manifest.json").write_text(json.dumps({
        "schema":"STAGE63_NONHO1_246_TOWER_T_NEIGHBOR_QC_v1",
        "n_original_GT8C":246,"n_auto_temperature_accepted":counts.get(SELECTED,0),
        "n_temperature_still_HOLD":246-counts.get(SELECTED,0),
        "n_Stage62_other_ERA5_humidity_proposals":4801,
        "n_Stage60_priors":4411,
        "n_unresolved_Ho1_original_hard":16788,
        "n_unverified_BZS_BIF_hard":86,
        "input_sha256":pins,"output_sha256":shas,
        "metadata_archive_discovery_only":True,
        "source_temperature_accepted_is_not_model_approval":True,
        "approved_for_DATM":False,"approved_for_spinup":False,
        "no_original_or_forcing_writes":True},indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE63 AUDIT PASS | 246 original T source-neighbor decisions recorded")
    print("REPORT",dest)
    print("NO RAW, STAGE60/62, DATM, CIME OR SLURM CHANGES")
if __name__=="__main__":
    main()

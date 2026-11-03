#!/usr/bin/env python3
"""JapanFlux Stage05AX — read-only ORIGINAL SOURCE half-hour QC-neighbor audit.

For each of FIVE source releases, use actual Stage05AW 45-field HOLD ledger
and original 11-site JPF manifest. Re-read original nested ZIP FLUXMET_HH
once per site (stream, no extraction), source README exact SHA, original
selected F, F_QC and same-release ERA at its exact original native time.
Collect ±48 original HH (=24 h each way), nearest measured QC0 and
MDS/gapfilled QC1 same-variable bracketing anchors, and the FULL contiguous
original QC2 episode length by scanning all original HH rows. Raw sensor
columns and MDS fields are reported if they actually exist in the source;
absence is explicit. QC1 is NEVER a genuine independent QC0 tower reading.

All output lives only in new --out-dir under HOME. No CDS/HTTP,
ZIP/forcing/model changes, no Slurm/AD400, no replacement numbers or
science approvals. Operator JST+9 for JP-Tef/Tmd remains a HYPOTHESIS;
the original 75-line README calls time "local solar". Do NOT change UTC.

Run five sites separately to cap peak memory; --aggregate later
reconciles exact 45 fields across five persisted site results.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path,PurePosixPath

SITES=Counter({"JP-Fjy":6,"JP-Khw":11,"JP-Yms":10,"JP-Tef":4,"JP-Tmd":14})
VARS=Counter({"PA":27,"TA":6,"LW_IN":12})
SOURCE_READMES={
  "JP-Fjy":"fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9",
  "JP-Khw":"fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9",
  "JP-Yms":"fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9",
  "JP-Tef":"17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5",
  "JP-Tmd":"17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5",
}
JST_SITES={"JP-Fjy","JP-Khw","JP-Yms"}
SOLAR_SITES={"JP-Tef","JP-Tmd"}
UNIT={"PA":"kPa","TA":"deg C","LW_IN":"W m-2"}
PHYSICAL={"PA":(50,115),"TA":(-70,65),"LW_IN":(70,650)}
WINDOW=48  # 48 half-hour time steps on BOTH sides of each flagged HH
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
CLOCK_USER="JST_UTC_PLUS9_DIAGNOSTIC_ONLY"
EVENT_COLS=("site","original_native_halfhour","variable","original_F_QC2",
            "selected_source_F_QC","selected_source_ERA","full_source_QC2_run_start",
            "full_source_QC2_run_end","full_source_QC2_run_HH",
            "observed_window_HH","observed_neighbor_QC0_count",
            "observed_neighbor_QC1_count","observed_neighbor_QC2_count",
            "nearest_left_QC0_time","nearest_left_QC0_value",
            "nearest_right_QC0_time","nearest_right_QC0_value",
            "nearest_left_QC0orQC1_time","nearest_left_QC0orQC1_value",
            "nearest_left_QC0orQC1_quality","nearest_right_QC0orQC1_time",
            "nearest_right_QC0orQC1_value","nearest_right_QC0orQC1_quality",
            "original_raw_measurement_field_present",
            "original_F_MDS_field_present","original_F_MDS_QC_field_present",
            "candidate_UTC_provenance","review_route","repair_value_approved")
NEIGHBOR_COLS=("site","anomaly_native","variable","neighbor_native","offset_half_hours",
               "source_F_value","source_F_QC","same_release_ERA",
               "source_raw_sensor","source_F_MDS","source_F_MDS_QC",
               "is_physically_plausible","is_independent_measured_QC0")
def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def jread(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict):raise ValueError("Expected source JSON dictionary")
    return data
def table(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        if not r.fieldnames or len(set(r.fieldnames))!=len(r.fieldnames):
            raise ValueError("Missing or duplicated TSV source field header "+str(path))
        return list(r)
def numeric(s):
    try:
        v=float(s)
        return v if math.isfinite(v) and v>-9990 else None
    except (ValueError,TypeError,OverflowError):
        return None
def close(a,b,atol=1e-6):
    """Compare independently read source CSV numbers and Stage05AW TSV strings.

    Both operands may be string or float. Nonfinite/source-missing values
    must fail source provenance verification rather than raising TypeError
    or treating a missing source value as an observation.
    """
    x=numeric(a)
    y=numeric(b)
    return x is not None and y is not None and math.isclose(x,y,abs_tol=atol,rel_tol=1e-10)
def qc_class(s):
    x=numeric(s)
    if x is not None and x in (0,1,2):return int(x)
    return "MISSING_OR_OTHER"
def point_field_snapshot(row,var,header):
    sensor=var if var in header else None
    mds=var+"_F_MDS" if var+"_F_MDS" in header else None
    mds_qc=var+"_F_MDS_QC" if var+"_F_MDS_QC" in header else None
    return {"source_F_value":row[var+"_F"],
            "source_F_QC":row[var+"_F_QC"],
            "same_release_ERA":row[var+"_ERA"],
            "source_raw_sensor":row[sensor] if sensor else "",
            "source_F_MDS":row[mds] if mds else "",
            "source_F_MDS_QC":row[mds_qc] if mds_qc else ""}
def ledger_gate(report,records):
    if (report.get("stage")!="JapanFlux Stage05AW"
        or report.get("status")!="ALL_45_ORIGINAL_QC2_INDEPENDENT_HOURLY_SOURCE_CONTEXT_RECONCILED_REPAIRS_UNAPPROVED"
        or report.get("original_source_selected_F_equals_same_release_ERA_QC2_variable_fields")!=45
        or report.get("original_distinct_site_native_halfhours")!=35
        or report.get("original_sites_by_field_count")!=dict(SITES)
        or report.get("original_variables_by_field_count")!=dict(VARS)
        or report.get("independent_context_compared_fields")!=45
        or report.get("independent_context_outside_fields")!=45
        or report.get("original_source_verified_JST_strong_context_fields")!=22
        or report.get("original_source_verified_JST_context_only_fields")!=5
        or report.get("operator_assumed_JST_source_README_solar_time_conflict_context_only_fields")!=18
        or report.get("science_approved_30min_replacement_values")!=0
        or report.get("all_45_original_source_fields_HOLD") is not True
        or report.get("original_source_ZIP_or_model_forcing_modified") is not False):
        raise ValueError("Stage05AW actual 45-source-field origin/science HOLD gate changed")
    if len(records)!=45 or Counter(r["site"] for r in records)!=SITES or Counter(r["variable"] for r in records)!=VARS:
        raise ValueError("Stage05AW original 45 source field site/variable counts changed")
    seen=set()
    for r in records:
        key=r["site"],r["native_source_halfhour_start"],r["variable"]
        if key in seen:raise ValueError("Duplicated original flagged source field")
        seen.add(key)
        if (r["original_QC"]!="2"
            or r["science_approval_status"]!="HOLD_NO_APPROVED_30MIN_REPLACEMENT"
            or r["candidate_replacement_value"]!="NOT_ESTIMATED"
            or r["unit"]!=UNIT[r["variable"]]
            or r["outside_independent_hourly_envelope"]!="True"
            or not close(numeric(r["original_source_F_QC2"]),numeric(r["original_same_release_ERA"]))):
            raise ValueError("Original source-selected F=ERA QC2 science HOLD/value mismatch "+repr(key))
        expected_clock=("ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED" if r["site"] in JST_SITES
                        else "OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT")
        if r["time_basis_provenance"]!=expected_clock:
            raise ValueError("Cannot silently promote original Tef/Tmd solar README to verified UTC")
        native=datetime.strptime(key[1],"%Y%m%d%H%M")
        utc=datetime.strptime(r["reference_candidate_UTC_start"],"%Y%m%d%H%M")
        if native-utc!=timedelta(hours=9):
            raise ValueError("Source clock offset changed")
    if len({(s,t) for s,t,v in seen})!=35:
        raise ValueError("Original 35 distinct source site/native HH changed")
def original_manifest(path):
    rows=table(path)
    if len(rows)!=11 or len({r["site"] for r in rows})!=11:
        raise ValueError("Source JPF 11-site original manifest changed")
    d={r["site"]:r["package"] for r in rows}
    for site in SITES:
        if d.get(site)!=f"JPF_{site}_FLUXNET_"+(
             {"JP-Fjy":"2001-2021","JP-Khw":"2000-2021",
              "JP-Yms":"2000-2023","JP-Tef":"2001-2023",
              "JP-Tmd":"2005-2023"}[site])+"_v1.3_r1":
            raise ValueError("Original JPF exact site release differs "+site)
    return d
def target_windows(events):
    wanted=defaultdict(list)
    for k in events:
        _,native,var=k
        t=datetime.strptime(native,"%Y%m%d%H%M")
        for off in range(-WINDOW,WINDOW+1):
            s=(t+timedelta(minutes=30*off)).strftime("%Y%m%d%H%M")
            wanted[s].append((k,off))
    return wanted
def read_site_source(site,package,events,root,max_mib):
    outer=root/site/"forcing"/"packages"/(package+".zip")
    if not outer.is_file() or outer.is_symlink():raise ValueError("Original source outer JPF ZIP missing "+str(outer))
    inner_name=package+".zip"
    cap=max_mib*1024*1024
    with zipfile.ZipFile(outer) as z:
        candidates=[info for info in z.infolist() if info.filename==inner_name and not info.is_dir()]
        if len(candidates)!=1 or not 0<candidates[0].file_size<=cap:
            raise ValueError("Original exact nested JPF member missing or over capped source memory")
        with io.BytesIO() as stream:
            with z.open(candidates[0]) as source:
                size=0
                for chunk in iter(lambda:source.read(2*1024*1024),b""):
                    size+=len(chunk)
                    if size>cap:raise ValueError("Original nested source byte cap exceeded")
                    stream.write(chunk)
            stream.seek(0)
            scanned=_inner_scan(site,package,events,stream)
            scanned["original_outer_zip"]=str(outer)
            return scanned
def _inner_scan(site,package,events,buffer):
    found={};window_rows=defaultdict(list);runs={};run_status={}
    varlist=sorted({k[2] for k in events})
    target=target_windows(events)
    target_stamps={k[1] for k in events}
    with zipfile.ZipFile(buffer) as z:
        members=[i for i in z.infolist() if not i.is_dir()]
        readme=[i for i in members if PurePosixPath(i.filename).name.lower()=="readme.txt"]
        expected_hh=f"JPF_{site}_FLUXNET_FLUXMET_HH_{package.split('_FLUXNET_')[1]}.csv"
        hh=[i for i in members if PurePosixPath(i.filename).name==expected_hh]
        if len(readme)!=1 or len(hh)!=1:
            raise ValueError("Original source nested README or FLUXMET_HH member missing")
        with z.open(readme[0]) as h:
            readme_digest=hashlib.sha256(h.read()).hexdigest()
        if readme_digest!=SOURCE_READMES[site]:
            raise ValueError("Original exact source README content SHA changed "+site)
        def finish_run(var):
            previous=runs.pop(var,None)
            if previous is None:return
            for key in previous["targets"]:
                if key in run_status:raise ValueError("Duplicate original target in multiple QC2 continuous runs")
                run_status[key]={"run_start":previous["start"],
                                 "run_end":previous["last"],
                                 "run_length":previous["n"]}
        rows_scanned=0;headers=[]
        with z.open(hh[0]) as handle:
            with io.TextIOWrapper(handle,encoding="utf-8-sig",newline="") as text:
                reader=csv.DictReader(text)
                headers=reader.fieldnames or []
                if not headers or len(set(headers))!=len(headers) or not {"TIMESTAMP_START","TIMESTAMP_END"}<=set(headers):
                    raise ValueError("Original source FLUXMET_HH malformed header")
                for var in varlist:
                    if not {var+"_F",var+"_ERA",var+"_F_QC"}<=set(headers):
                        raise ValueError("Original source selected field F/ERA/QC missing "+site+" "+var)
                for row in reader:
                    rows_scanned+=1
                    stamp=row["TIMESTAMP_START"]
                    if len(stamp)!=12 or not stamp.isdigit():
                        raise ValueError("Original JPF native HH timestamp malformed")
                    if stamp in target:
                        dt=datetime.strptime(stamp,"%Y%m%d%H%M")
                        if row["TIMESTAMP_END"]!=(dt+timedelta(minutes=30)).strftime("%Y%m%d%H%M"):
                            raise ValueError("Original source neighbor HH END not START+30m")
                        for k,off in target[stamp]:
                            snapshot=point_field_snapshot(row,k[2],headers)
                            window_rows[k].append((off,stamp,snapshot))
                    if stamp in target_stamps:
                        for key in events:
                            if key[1]!=stamp:continue
                            var=key[2]
                            f=numeric(row[var+"_F"]); era=numeric(row[var+"_ERA"])
                            qc=qc_class(row[var+"_F_QC"])
                            if key in found or not close(f,events[key]["original_source_F_QC2"]) or not close(era,events[key]["original_same_release_ERA"]) or qc!=2:
                                raise ValueError("Original source HH flagged F/ERA/QC2 differs from actual Stage05AW "+repr(key))
                            found[key]={"native":stamp,"F":f,"ERA":era,"QC":qc}
                    for var in varlist:
                        qc=qc_class(row[var+"_F_QC"])
                        current=runs.get(var)
                        if qc!=2:
                            if current is not None:finish_run(var)
                            continue
                        if current is not None:
                            expected=(datetime.strptime(current["last"],"%Y%m%d%H%M")+timedelta(minutes=30)).strftime("%Y%m%d%H%M")
                            if stamp!=expected:
                                finish_run(var);current=None
                        if var not in runs:
                            runs[var]={"start":stamp,"last":stamp,"n":0,"targets":[]}
                        runs[var]["n"]+=1
                        runs[var]["last"]=stamp
                        for k in events:
                            if k[1]==stamp and k[2]==var:
                                runs[var]["targets"].append(k)
        for var in varlist:finish_run(var)
    if set(found)!=set(events) or set(run_status)!=set(events):
        raise ValueError("Original source events or original contiguous QC2 run incomplete "+site)
    for k in events:
        if not any(off==0 for off,_,_ in window_rows[k]):
            raise ValueError("Missing original target source HH in neighbor window "+repr(k))
    return {"site":site,"package":package,
            "original_source_readme_sha256":readme_digest,
            "source_HH_member":expected_hh,"source_HH_rows_scanned":rows_scanned,
            "full_source_header":headers,"target_values":found,
            "source_window_rows":window_rows,"source_QC2_runs":run_status}
def finite_plausible(var,s):
    value=numeric(s)
    lo,hi=PHYSICAL[var]
    return value is not None and lo<=value<=hi
def summary_events(site,events,observed):
    source=observed["source_window_rows"]
    headers=set(observed["full_source_header"])
    results=[];neighbor=[]
    for key,event in sorted(events.items(),key=lambda x:(x[0][1],x[0][2])):
        _,native,var=key
        samples=sorted(source[key],key=lambda x:x[0])
        by_offset={off:(stamp,rec) for off,stamp,rec in samples}
        if len(samples)!=len(by_offset):raise ValueError("Original source duplicate native context row")
        left0=right0=left01=right01=None
        nquality=Counter()
        for off,stamp,rec in samples:
            q=qc_class(rec["source_F_QC"])
            nquality[q]+=1
            plaus=finite_plausible(var,rec["source_F_value"])
            measured=q==0 and plaus
            valid01=q in (0,1) and plaus
            if off<0:
                if measured:left0=(off,stamp,rec)
                if valid01:left01=(off,stamp,rec)
            if off>0:
                if measured and right0 is None:right0=(off,stamp,rec)
                if valid01 and right01 is None:right01=(off,stamp,rec)
            neighbor.append({
               "site":site,"anomaly_native":native,"variable":var,
               "neighbor_native":stamp,"offset_half_hours":off,
               **rec,"is_physically_plausible":plaus,
               "is_independent_measured_QC0":measured})
        run=observed["source_QC2_runs"][key]
        def detail(anchor):
            if anchor is None:return "","",""
            return anchor[1],anchor[2]["source_F_value"],qc_class(anchor[2]["source_F_QC"])
        l0=detail(left0);r0=detail(right0)
        l01=detail(left01);r01=detail(right01)
        # Conservative SCREEN only, never numeric replacement. QC1 is already
        # gap-filled and therefore weaker than paired original QC0.
        within0=(left0 is not None and right0 is not None
                 and abs(left0[0])<=4 and right0[0]<=4)
        within01=(left01 is not None and right01 is not None
                  and abs(left01[0])<=6 and right01[0]<=6)
        if within0 and run["run_length"]<=4:
            route="SHORT_QC0_BRACKETED_SHADOW_CANDIDATE_REVIEW_ONLY"
        elif within01 and run["run_length"]<=6:
            route="MIXED_QC0_QC1_BRACKETED_REVIEW_ONLY_QC1_IS_GAPFILL"
        else:
            route="LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED"
        clock=("ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED" if site in JST_SITES
               else "OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT")
        results.append({
            "site":site,"original_native_halfhour":native,"variable":var,
            "original_F_QC2":event["original_source_F_QC2"],
            "selected_source_F_QC":"2",
            "selected_source_ERA":event["original_same_release_ERA"],
            "full_source_QC2_run_start":run["run_start"],
            "full_source_QC2_run_end":run["run_end"],
            "full_source_QC2_run_HH":run["run_length"],
            "observed_window_HH":len(samples),
            "observed_neighbor_QC0_count":nquality[0],
            "observed_neighbor_QC1_count":nquality[1],
            "observed_neighbor_QC2_count":nquality[2],
            "nearest_left_QC0_time":l0[0],"nearest_left_QC0_value":l0[1],
            "nearest_right_QC0_time":r0[0],"nearest_right_QC0_value":r0[1],
            "nearest_left_QC0orQC1_time":l01[0],
            "nearest_left_QC0orQC1_value":l01[1],
            "nearest_left_QC0orQC1_quality":l01[2],
            "nearest_right_QC0orQC1_time":r01[0],
            "nearest_right_QC0orQC1_value":r01[1],
            "nearest_right_QC0orQC1_quality":r01[2],
            "original_raw_measurement_field_present":var in headers,
            "original_F_MDS_field_present":var+"_F_MDS" in headers,
            "original_F_MDS_QC_field_present":var+"_F_MDS_QC" in headers,
            "candidate_UTC_provenance":clock,
            "review_route":route,
            "repair_value_approved":False
        })
    if len(results)!=SITES[site]:
        raise ValueError("Site source-neighbor event count inconsistent")
    return results,neighbor
def science_summary(site,record,events,neighbor,ledger,manifest):
    routes=Counter(x["review_route"] for x in events)
    counts=Counter(x["variable"] for x in events)
    return {
     "stage":"JapanFlux Stage05AX","status":"ORIGINAL_JPF_QC0_QC1_NEIGHBOR_AND_CONTIGUOUS_QC2_RUN_AUDIT_HOLD",
     "site":site,
     "original_source_JPF_release":record["package"],
     "original_source_readme_sha256":record["original_source_readme_sha256"],
     "source_HH_csv_rows_scanned":record["source_HH_rows_scanned"],
     "source_HH_CSV_header":record["full_source_header"],
     "neighbor_halfhours_on_each_side":WINDOW,
     "original_source_QC2_fields_audited":len(events),
     "distinct_original_native_site_halfhours":len({r["original_native_halfhour"] for r in events}),
     "variable_field_counts":dict(counts),
     "source_original_QC2_run_length_max_HH":max(int(r["full_source_QC2_run_HH"]) for r in events),
     "repair_feasibility_routes":dict(routes),
     "original_source_measurement_QC0_is_separate_from_F_QC1_gapfill":True,
     "source_timebase_proven":site in JST_SITES,
     "operator_JST_plus9_time_hypothesis_only":site in SOLAR_SITES,
     "source_clock_solar_readme_conflict_preserved":site in SOLAR_SITES,
     "candidate_replacement_values_created":0,
     "all_45_original_QC2_fields_SCIENCE_HOLD":True,
     "CDS_requests":0,"Slurm_jobs":0,
     "original_JPF_source_ZIP_forcing_model_modified":False,
     "input_sha256":{"stage05aw_field_ledger":digest(ledger),"stage05aw_science_summary":digest(manifest)},
     "science_notes":[
       "QC0 means source-selected measured observation; QC1 is a source gapfill not independent measured sensor",
       "Neighbor QC0 or QC1 can be poor at the edge of a long QC2 run; continuous run length is measured across entire source HH",
       "The preview brackets are temporal QC screens only: not scientifically approved linear interpolation",
       "JPF original README local solar time conflicts with operator JST hypothesis for Tef/Tmd; original native timestamps retained",
       "No automatic ERA5-Land hourly-to-30min replacement is scientifically permitted"
     ]
    }
def run_site(a):
    source_report=jread(a.stage05aw_summary)
    records=table(a.stage05aw_fields)
    ledger_gate(source_report,records)
    packages=original_manifest(a.manifest)
    site=a.site
    events={(r["site"],r["native_source_halfhour_start"],r["variable"]):r
            for r in records if r["site"]==site}
    if len(events)!=SITES[site]:raise ValueError("Site event population incomplete")
    if a.out_dir.exists():raise ValueError("Output directory exists; never overwrite previous audit")
    record=read_site_source(site,packages[site],events,a.root,a.max_inner_mib)
    events_list,neighbor_rows=summary_events(site,events,record)
    science=science_summary(site,record,events_list,neighbor_rows,
                            a.stage05aw_fields,a.stage05aw_summary)
    a.out_dir.mkdir(parents=True)
    code=site.replace("-","_")
    eventfile=a.out_dir/f"stage05ax_{code}_original_45scope_source_QC2_run_neighbor_readonly.tsv"
    contextfile=a.out_dir/f"stage05ax_{code}_original_source_24h_each_side_QC0_QC1_F_MDS_ERA.tsv"
    reportfile=a.out_dir/f"stage05ax_{code}_source_neighbor_science_HOLD.json"
    with eventfile.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=EVENT_COLS,delimiter="\t");w.writeheader();w.writerows(events_list)
    with contextfile.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=NEIGHBOR_COLS,delimiter="\t");w.writeheader();w.writerows(neighbor_rows)
    with reportfile.open("x",encoding="utf-8") as f:
        json.dump(science,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AX ORIGINAL_SOURCE_QC0_QC1_NEIGHBOR_REVIEW_PASS",site,
          "FIELDS",len(events_list),"NATIVE_TIMES",science["distinct_original_native_site_halfhours"])
    print("SOURCE_HH_ROWS_SCANNED",record["source_HH_rows_scanned"],
          "README_SHA256",record["original_source_readme_sha256"])
    print("FULL_SOURCE_QC2_RUN_MAX_HH",science["source_original_QC2_run_length_max_HH"])
    print("TEMPORAL_BRACKET_SCREEN_ONLY",dict(sorted(science["repair_feasibility_routes"].items())))
    for r in events_list:
        print("EVENT",r["original_native_halfhour"],r["variable"],
            "QC2_RUN_HH",r["full_source_QC2_run_HH"],
            "LEFT_QC0",r["nearest_left_QC0_time"] or "NONE",
            "RIGHT_QC0",r["nearest_right_QC0_time"] or "NONE",
            "SCREEN",r["review_route"])
    print("SOURCE_NEIGHBOR_EVENT_TABLE",eventfile)
    print("SOURCE_24H_CONTEXT_TABLE",contextfile)
    print("ORIGINAL_SCIENCE_HOLD_REPORT",reportfile)
    print("NO_REPAIR_VALUES/NO_CDS/NO_ORIGINAL_SOURCE_OR_FORCING_WRITES/NO_SLURM_ALL_45_HOLD")
def aggregate(a):
    merged=[];rows=[]
    for site in SITES:
        code=site.replace("-","_")
        dirname=a.site_results_root/site
        report=dirname/f"stage05ax_{code}_source_neighbor_science_HOLD.json"
        data=dirname/f"stage05ax_{code}_original_45scope_source_QC2_run_neighbor_readonly.tsv"
        r=jread(report)
        sub=table(data)
        if (r.get("stage")!="JapanFlux Stage05AX"
            or r.get("status")!="ORIGINAL_JPF_QC0_QC1_NEIGHBOR_AND_CONTIGUOUS_QC2_RUN_AUDIT_HOLD"
            or r.get("site")!=site
            or r.get("original_source_QC2_fields_audited")!=SITES[site]
            or r.get("neighbor_halfhours_on_each_side")!=WINDOW
            or r.get("source_original_QC2_run_length_max_HH",0)<1
            or r.get("candidate_replacement_values_created")!=0
            or r.get("all_45_original_QC2_fields_SCIENCE_HOLD") is not True
            or r.get("source_timebase_proven")!=(site in JST_SITES)
            or r.get("operator_JST_plus9_time_hypothesis_only")!=(site in SOLAR_SITES)
            or r.get("original_source_readme_sha256")!=SOURCE_READMES[site]
            or len(sub)!=SITES[site]):
            raise ValueError("Original Stage05AX source-site report/status mismatch "+site)
        for line in sub:
            if (line["site"]!=site or line["selected_source_F_QC"]!="2"
                or line["repair_value_approved"]!="False"):
                raise ValueError("Source QC2/no repair original hold failed at "+site)
        merged.extend(sub);rows.append({"site":site,"field_count":len(sub),
            "distinct_native_times":r["distinct_original_native_site_halfhours"],
            "source_max_QC2_run_HH":r["source_original_QC2_run_length_max_HH"],
            "feasibility_routes":r["repair_feasibility_routes"],
            "original_source_readme_SHA256":r["original_source_readme_sha256"],
            "event_table_SHA256":digest(data),"site_summary_SHA256":digest(report)})
    if len(merged)!=45 or Counter(r["variable"] for r in merged)!=VARS or len({
       (r["site"],r["original_native_halfhour"]) for r in merged})!=35:
        raise ValueError("Source site 45 QC2 variable field/35 native HH population changed")
    if a.out_dir.exists():raise ValueError("Never overwrite source aggregate audit folder")
    a.out_dir.mkdir(parents=True)
    combined=a.out_dir/"stage05ax_45_original_QC2_native_source_quality_anchor_feasibility_NO_REPAIR.tsv"
    report=a.out_dir/"stage05ax_45_original_QC2_five_site_QC0_QC1_neighbor_HOLD_summary.json"
    with combined.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=EVENT_COLS,delimiter="\t");w.writeheader()
        w.writerows(sorted(merged,key=lambda r:(r["site"],r["original_native_halfhour"],r["variable"])))
    counts=Counter(r["review_route"] for r in merged)
    summary={"stage":"JapanFlux Stage05AX",
       "status":"FIVE_ORIGINAL_JPF_SITES_45_QC2_NEIGHBOR_QC0_QC1_AND_FULL_QC2_RUN_REVIEWED_NO_REPAIR",
       "original_source_fields":45,"distinct_site_native_halfhours":35,
       "source_variables":dict(VARS),"site_science_reports":rows,
       "source_QC0_QC1_temporal_feasibility_screens":dict(counts),
       "strong_context_evidence_from_prior_stage":22,
       "context_only_from_prior_stage":23,
       "science_approved_halfhour_replacements":0,
       "all_45_original_source_QC2_fields_HOLD":True,
       "source_clock_solar_vs_JST_conflict_sites":["JP-Tef","JP-Tmd"],
       "original_source_ZIP_or_model_forcing_modified":False,"CDS_requests":0,"Slurm_jobs":0}
    with report.open("x",encoding="utf-8") as f:
        json.dump(summary,f,indent=2,ensure_ascii=False);f.write("\n")
    print("STAGE05AX FIVE_SITES_45_ORIGINAL_SOURCE_QC2_QC0_QC1_NEIGHBOR_MERGE_PASS | NO_REPAIRS")
    print("SOURCE_EVENTS",45,"NATIVE_SITE_HALFHOURS",35,"ORIGINAL_VARS",dict(VARS))
    print("QC0/QC1_TEMPORAL_FEASIBILITY_SCREENS",dict(counts))
    print("FIVE_SOURCE_SITES_REVIEWED",len(rows),"ORIGINAL_README_TIME_CONFLICT_TEF_TMD_RETAINED")
    print("UNIFIED_NEIGHBOR_FEASIBILITY_TSV",combined)
    print("SCIENCE_HOLD_SOURCE_SUMMARY",report)
    print("ALL_45_SCIENCE_HOLD; NO_REPLACEMENTS/CDS/FORCING/SLURM")
def selftest():
    assert sum(SITES.values())==45 and sum(VARS.values())==45
    assert WINDOW==48 and len(SOURCE_READMES)==5
    assert qc_class("0")==0 and qc_class("1")==1 and qc_class("2")==2
    assert qc_class("-9999")=="MISSING_OR_OTHER"
    assert finite_plausible("PA","99.4") and not finite_plausible("PA","0")
    assert finite_plausible("LW_IN","200") and not finite_plausible("LW_IN","26.164")
    assert close(numeric("26.164"),26.164)
    assert close(26.164,"26.164") and close("26.164",26.164)
    assert close("0.0",0.0) and close(0,"0")
    assert not close("not-a-number",26.164)
    assert not close(None,"26.164") and not close("-9999","-9999")
    assert not close(26.164,"26.264")
    native=datetime(2011,12,17,6)
    assert (native-timedelta(hours=9)).strftime("%Y%m%d%H%M")=="201112162100"
    # Deterministic +-48 original halfhour window mapping, no file/ZIP access.
    sample={("JP-Tef","201112170600","LW_IN"):{"site":"JP-Tef"}}
    wanted=target_windows(sample)
    assert len(wanted)==97 and wanted["201112170600"][0][1]==0
    print("STAGE05AX SELF-TEST PASS | source 45 QC2 fields, nearest genuine QC0 vs QC1 gapfill, full original QC2 run, 24h each side; NO NETWORK/WRITES")
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--site",choices=tuple(SITES))
    ap.add_argument("--aggregate",action="store_true")
    ap.add_argument("--stage05aw-fields",type=Path)
    ap.add_argument("--stage05aw-summary",type=Path)
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--site-results-root",type=Path)
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--max-inner-mib",type=int,default=512)
    ap.add_argument("--out-dir",type=Path)
    a=ap.parse_args()
    if a.self_test:selftest();return
    if a.out_dir is None:ap.error("Fresh --out-dir required")
    if a.aggregate:
        if a.site is not None or a.site_results_root is None:
            ap.error("--aggregate requires --site-results-root and not --site")
        aggregate(a);return
    if a.site is None or any(x is None for x in (a.stage05aw_fields,a.stage05aw_summary,a.manifest)):
        ap.error("One --site with actual Stage05AW ledger/summary and original manifest required")
    if not 256<=a.max_inner_mib<=1024:ap.error("Source nested ZIP MiB memory cap must be 256..1024")
    run_site(a)
if __name__=="__main__":main()

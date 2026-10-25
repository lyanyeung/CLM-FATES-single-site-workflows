#!/usr/bin/env python3
"""Batch05 Stage17: group Stage16's 1750 low-RH half-hours into native episodes.

Evidence-request manifest only, not forcing repair. Uses no network, site
coordinates, fabricated UTC conversion, or Slurm; verifies Stage16 input
counts and original site-time groupings. New CSV/JSON output only.
"""
import argparse,csv,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
REQUIRED={"site","time","priority","TA_F_QC","VPD_F_QC","VPD_source",
    "TA_F_C","VPD_F_hPa","F_pair_RH_pct","ERA_pair_physical",
    "F_T_plus_ERA_VPD_physical","ERA_e_plus_F_T_physical",
    "MDS_pair_physical","F_minus_ERA_T_C","F_minus_ERA_VPD_hPa",
    "source_pair_flag","science_status"}
METAFIELDS=("site","need_latitude_longitude_elevation","need_native_clock_UTC_offset",
            "need_tower_instrument_and_FLUXNET_algorithm","reference_plan","approval")
EPFIELDS=("episode_id","site","native_start","native_end","half_hours",
          "duration_hours","native_calendar_year_start","native_calendar_year_end",
          "qc0_measured_HH","qc1_MDS_HH","qc2_ERA_HH","negative_RH_HH",
          "ERA_internal_nonphysical_HH","ERA_implied_e_towerT_nonphysical_HH",
          "direct_ERA_VPD_towerT_nonphysical_HH","MDS_pair_nonphysical_HH",
          "tower_minus_ERA_T_gt5C_HH","F_minus_ERA_VPD_gt5hPa_HH",
          "max_abs_tower_minus_ERA_T_C","max_abs_F_minus_ERA_VPD_hPa",
          "min_water_RH_pct","priority_tier","native_review_window_start",
          "native_review_window_end","UTC_window_status","next_evidence",
          "approval")
def num(x):
    try:
        a=float(x)
        return a if math.isfinite(a) else None
    except (ValueError,TypeError):return None
def clock(s):
    if len(s)!=12 or not s.isdigit():raise ValueError("invalid native time "+repr(s))
    return datetime.strptime(s,"%Y%m%d%H%M")
def readcsv(file):
    if not file.is_file() or file.is_symlink():raise ValueError("Stage16 source file not regular "+str(file))
    with file.open(newline="",encoding="utf-8-sig") as fh:
        rdr=csv.DictReader(fh)
        if not REQUIRED.issubset(rdr.fieldnames or []):
            raise ValueError("Stage16 source-pair CSV missing columns")
        rows=list(rdr)
        if any(None in x or any(v is None for v in x.values()) for x in rows):
            raise ValueError("Stage16 source-pair CSV malformed")
    return rows
def episodes_from(rows):
    groups=defaultdict(list);seen=set()
    for row in rows:
        site,stamp=row["site"],row["time"]
        if site not in SITES:raise ValueError("unexpected site "+site)
        key=(site,stamp)
        if key in seen:raise ValueError("repeated source site/timestamp "+repr(key))
        seen.add(key)
        if row["science_status"]!="HOLD_NOT_APPROVED":
            raise ValueError("source science HOLD changed")
        if row["VPD_F_QC"] not in ("0","1","2"):
            raise ValueError("unrecognised VPD source QC")
        when=clock(stamp)
        if when.minute not in (0,30):raise ValueError("unaligned half-hour "+stamp)
        groups[site].append(row)
    result=[]
    for site in SITES:
        members=sorted(groups[site],key=lambda r:r["time"])
        if not members:continue
        chunk=[members[0]]
        for item in members[1:]:
            if clock(item["time"])-clock(chunk[-1]["time"])==timedelta(minutes=30):
                chunk.append(item)
            else:
                result.append((site,chunk))
                chunk=[item]
        result.append((site,chunk))
    return result
def summarize(site,rows,ordinal):
    a,b=clock(rows[0]["time"]),clock(rows[-1]["time"])
    C=Counter()
    for row in rows:
        q=row["VPD_F_QC"];C["qc"+q]+=1
        rh=num(row["F_pair_RH_pct"])
        if rh is None or rh>=1:raise ValueError("source low-RH screen not reproducible")
        C["negative"]+=int(rh<0)
        for key,col in (("ERA_invalid","ERA_pair_physical"),
                        ("ERA_e_mix_invalid","ERA_e_plus_F_T_physical"),
                        ("direct_mix_invalid","F_T_plus_ERA_VPD_physical"),
                        ("MDS_invalid","MDS_pair_physical")):
            C[key]+=int(row[col]=="NONPHYSICAL")
        dT=num(row["F_minus_ERA_T_C"])
        dV=num(row["F_minus_ERA_VPD_hPa"])
        C["T_gt5"]+=int(dT is not None and abs(dT)>5)
        C["V_gt5"]+=int(dV is not None and abs(dV)>5)
    t=max([abs(num(r["F_minus_ERA_T_C"])) for r in rows
           if num(r["F_minus_ERA_T_C"]) is not None],default=None)
    v=max([abs(num(r["F_minus_ERA_VPD_hPa"])) for r in rows
           if num(r["F_minus_ERA_VPD_hPa"]) is not None],default=None)
    measured=C["qc0"]>0
    if measured or C["ERA_invalid"]>0:tier="P1_MEASURED_OR_ERA_INVALID"
    elif C["ERA_e_mix_invalid"]>0 or len(rows)>=12:tier="P2_MIX_OR_LONG_EPISODE"
    else:tier="P3_CONTEXT_AND_INDEPENDENT_REFERENCE"
    requested=("VERIFY_NATIVE_TA_VPD_RH_FORMULA_AND_ORIGINAL_INSTRUMENT"
        if measured else "VERIFY_ORIGINAL_ERA_SOURCE_AND_NATIVE_VPD_FORMULA"
        if C["ERA_invalid"] else "VERIFY_TOWER_MDS_ERA_PAIRS_AND_EXTERNAL_MET")
    rec={"episode_id":site+"_E"+str(ordinal).zfill(4),"site":site,
       "native_start":rows[0]["time"],"native_end":rows[-1]["time"],
       "half_hours":len(rows),"duration_hours":len(rows)*0.5,
       "native_calendar_year_start":a.year,"native_calendar_year_end":b.year,
       "qc0_measured_HH":C["qc0"],"qc1_MDS_HH":C["qc1"],
       "qc2_ERA_HH":C["qc2"],"negative_RH_HH":C["negative"],
       "ERA_internal_nonphysical_HH":C["ERA_invalid"],
       "ERA_implied_e_towerT_nonphysical_HH":C["ERA_e_mix_invalid"],
       "direct_ERA_VPD_towerT_nonphysical_HH":C["direct_mix_invalid"],
       "MDS_pair_nonphysical_HH":C["MDS_invalid"],
       "tower_minus_ERA_T_gt5C_HH":C["T_gt5"],
       "F_minus_ERA_VPD_gt5hPa_HH":C["V_gt5"],
       "max_abs_tower_minus_ERA_T_C":t if t is not None else "",
       "max_abs_F_minus_ERA_VPD_hPa":v if v is not None else "",
       "min_water_RH_pct":min(num(r["F_pair_RH_pct"]) for r in rows),
       "priority_tier":tier,
       "native_review_window_start":(a-timedelta(hours=6)).strftime("%Y%m%d%H%M"),
       "native_review_window_end":(b+timedelta(hours=6)).strftime("%Y%m%d%H%M"),
       "UTC_window_status":"HOLD_SITE_NATIVE_UTC_OFFSET_NOT_VERIFIED",
       "next_evidence":requested,
       "approval":"HOLD_NOT_APPROVED"}
    return rec
def selftest():
    base={"site":"US-UMB","priority":"test","TA_F_QC":"0",
       "VPD_F_QC":"1","VPD_source":"GOOD_MDS_QC1","TA_F_C":"10",
       "VPD_F_hPa":"20","F_pair_RH_pct":"-20",
       "ERA_pair_physical":"PHYSICAL",
       "ERA_e_plus_F_T_physical":"PHYSICAL",
       "F_T_plus_ERA_VPD_physical":"PHYSICAL",
       "MDS_pair_physical":"NONPHYSICAL",
       "F_minus_ERA_T_C":"1","F_minus_ERA_VPD_hPa":"10",
       "source_pair_flag":"MDS_SOURCE_EXTREME_LOW",
       "science_status":"HOLD_NOT_APPROVED"}
    a=dict(base,time="202001010000")
    b=dict(base,time="202001010030")
    c=dict(base,time="202001010200")
    e=episodes_from([b,c,a])
    assert len(e)==2 and len(e[0][1])==2
    rec=summarize(*e[0],1)
    assert rec["half_hours"]==2 and rec["qc1_MDS_HH"]==2
    assert rec["UTC_window_status"].startswith("HOLD_")
    print("STAGE17 SELF-TEST PASS | contiguous native-HH episodes, no guessed UTC mapping, science holds")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage16-dir",type=Path)
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    if args.self_test:selftest();return
    if not args.stage16_dir or not args.output_dir:
        p.error("--stage16-dir and --output-dir required")
    d=args.stage16_dir.expanduser().resolve()
    out=args.output_dir.expanduser().resolve()
    if not d.is_dir():p.error("Stage16 source review folder missing")
    if out.exists() or not out.parent.is_dir() or out==d or d in out.parents or out in d.parents:
        p.error("Stage17 output must be NEW and disjoint from existing reports")
    meta=d/"stage16_summary.json"
    if not meta.is_file() or meta.is_symlink():p.error("Stage16 summary missing")
    m=json.loads(meta.read_text(encoding="utf-8"))
    if m.get("decision")!="HOLD_ALL_UNAPPROVED" or m.get("events")!=1750:
        raise ValueError("Stage16 exact approved state/cohort mismatch")
    data=readcsv(d/"stage16_all_1750_source_pair_review.csv")
    if len(data)!=1750:raise ValueError("Stage16 source-event count changed")
    original=Counter(r["VPD_F_QC"] for r in data)
    if original!=Counter({"0":119,"1":965,"2":666}):
        raise ValueError("Stage16 original provenance breakdown changed")
    groups=episodes_from(data)
    idx=Counter();entries=[]
    for site,episode in groups:
        idx[site]+=1
        entries.append(summarize(site,episode,idx[site]))
    if sum(x["half_hours"] for x in entries)!=1750:
        raise ValueError("episode source HH coverage incomplete")
    for site in SITES:
        if sum(x["half_hours"] for x in entries if x["site"]==site)!=m["sites"][site].get("events",0):
            raise ValueError("episode site HH coverage mismatch "+site)
    total=Counter(e["priority_tier"] for e in entries)
    stations={site:{"events":m["sites"][site].get("events",0),
       "episodes":idx[site],"highest_priority_episodes":sum(
           e["priority_tier"]=="P1_MEASURED_OR_ERA_INVALID"
           for e in entries if e["site"]==site)} for site in SITES}
    entries.sort(key=lambda r:(r["priority_tier"],-r["half_hours"],r["site"],r["native_start"]))
    output={"decision":"NO_SCIENCE_APPROVAL",
            "stage16_original_events":1750,"episode_count":len(entries),
            "counts_by_tier":dict(total),"sites":stations,
            "source_clock_policy":"native printed labels only; do not convert to UTC without verified site-specific metadata",
            "future_reference_plan":"Original independent site sensors and/or alternative ERA5-Land 2m T/dewpoint as corroboration only; require actual UTC offset, exact coordinates, elevation, version, and unit evidence",
            "note":"ERA5-Land is another reanalysis, not an independent observed weather station"}
    out.mkdir(exist_ok=False)
    with (out/"stage17_episodes_evidence_requests.csv").open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=EPFIELDS);w.writeheader();w.writerows(entries)
    meta_rows=[dict(zip(METAFIELDS,(site,"REQUIRED_BEFORE_EXTERNAL_REFERENCE",
          "REQUIRED_BEFORE_NATIVE_TIME_TO_UTC_CONVERSION",
          "REQUIRED_TO_VALIDATE_NATIVE_VPD_FORMULA",
          "ERA5-Land 2m T/dewpoint or independently observed station (not downloaded)",
          "HOLD_NOT_APPROVED"))) for site in SITES]
    with (out/"stage17_site_metadata_gates.csv").open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=METAFIELDS);w.writeheader();w.writerows(meta_rows)
    with (out/"stage17_summary.json").open("x",encoding="utf-8") as f:
        json.dump(output,f,indent=2,sort_keys=True)
    print("STAGE17 AGGREGATE",json.dumps({"events":1750,"episodes":len(entries),
            "priority_tiers":dict(total)},sort_keys=True),flush=True)
    for site in SITES:
        print("STAGE17_SITE",site,json.dumps(stations[site],sort_keys=True),flush=True)
    print("STAGE17_PRIORITY_TOP20",json.dumps(entries[:20],sort_keys=True),flush=True)
    print("STAGE17 SUMMARY sites=10/10 original_HH=1750 episodes={} approved=0 reports={}".format(
        len(entries),out),flush=True)
    print("ONLY NEW EVIDENCE REQUEST CSV/JSON; NO ORIGINAL/OTHER_REPORTS/FORCING/MODEL/SLURM WRITES")
if __name__=="__main__":main()

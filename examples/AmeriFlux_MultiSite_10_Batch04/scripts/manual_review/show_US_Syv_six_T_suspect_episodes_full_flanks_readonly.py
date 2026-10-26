#!/usr/bin/env python3
"""US-Syv: complete 30-min source temperature and paired ERA across 6 suspect episodes.

Six exactly source-identified anomalous episodes:
  2007 Feb 08 17:30-21:30 (9 HH); Feb09 17:30-23:30 (13 HH);
  Feb10 17:30-Feb11 07:00 (28 HH); Feb11 17:30-Feb12 03:00 (20 HH);
  Feb12 17:30-22:30 (11 HH); 2003 Apr27 11:30-19:30 (17 HH).
Print EVERY episode half-hour and +/- 2 hours around episode boundaries.
Values from original full AmeriFlux FLUXMET_HH TA_F with native TA_F_QC,
original paired same-native-time FLUXNET ERA TA_ERA, plus separately
Stage07 output, VPD/QC, and source hold reason. TA_F QC0=source observed,
QC1=filled (not independent tower measurement), QC2=ERA-origin fill;
TA_ERA is a processed FLUXNET ERA5-derived product, NOT independently
retrieved ERA5-Land. No original/candidate/model/forcing file changes.
Use --report to create a stand-alone CSV report under user HOME only.
"""
import argparse,csv,hashlib,json,math
from uuid import uuid4
from datetime import datetime,timedelta
from pathlib import Path

SITE="US-Syv"; N=438288
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=ROOT/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=ROOT/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
EPISODES=[
 ("E1_2007Feb08", "200702081730","200702082130",9),
 ("E2_2007Feb09", "200702091730","200702092330",13),
 ("E3_2007Feb10to11","200702101730","200702110700",28),
 ("E4_2007Feb11to12","200702111730","200702120300",20),
 ("E5_2007Feb12", "200702121730","200702122230",11),
 ("E6_2003Apr27","200304271130","200304271930",17)
]
NATIVE=("TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS","TA_F_MDS_QC","VPD_F","VPD_F_QC")
ERA=("TIMESTAMP_START","TA_ERA","VPD_ERA","PA_ERA")
REQUIRED={"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"}
def ck(test,message):
    if not test:raise ValueError(message)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Verified source absent or symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):h.update(block)
    return h.hexdigest()
def jsonread(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def datetime_key(k):return datetime.strptime(k,"%Y%m%d%H%M")
def timekeys(start,end):
    a=datetime_key(start);b=datetime_key(end)
    ck(b>=a and (b-a).total_seconds()%1800==0,"Non half-hour interval")
    return [(a+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
            for i in range(int((b-a).total_seconds()/1800)+1)]
def target_and_context():
    target=set(); allkeys=set()
    for name,a,b,n in EPISODES:
        times=timekeys(a,b)
        ck(len(times)==n,name+" expected HH count disagrees")
        ck(not target.intersection(times),name+" overlaps another episode")
        target.update(times)
        a2=(datetime_key(a)-timedelta(hours=2)).strftime("%Y%m%d%H%M")
        b2=(datetime_key(b)+timedelta(hours=2)).strftime("%Y%m%d%H%M")
        allkeys.update(timekeys(a2,b2))
    ck(len(target)==98,"Expected exactly 98 science suspect native HH")
    # Cover complete local calendar days, not just source-HOLD boundaries:
    # some QC1 anomalies extend past the original science HOLD endpoint.
    allkeys.update(timekeys("200702080000","200702132330"))
    allkeys.update(timekeys("200304270000","200304272330"))
    ck(len(allkeys)==336,"Expected complete Feb08-13 + Apr27 = 336 HH")
    return target,allkeys
def table(p,cols,want,full_n=None):
    seen={};count=0
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        ck(r.fieldnames is not None and set(cols).issubset(r.fieldnames),
           "Required original/ERA fields missing "+str(p))
        for line in r:
            count+=1;k=line["TIMESTAMP_START"]
            if k in want:
                ck(k not in seen,"Duplicate original native timestamp "+k)
                seen[k]={x:line[x] for x in cols}
    if full_n is not None:ck(count==full_n,"Original/candidate native row count changed")
    ck(set(want).issubset(seen),
       "Missing expected complete native episode/flanking 30-min times from "+str(p))
    return seen
def source_files():
    m=jsonread(S05/"report.json")
    r=jsonread(S07/"stage07_sha_receipt.json")
    ck(m.get("mode")=="BUILD_CANDIDATE_OVERLAY" and
       m["sites"][SITE]["hold_rows"]==606 and
       m["sites"][SITE]["rows"]==N,
       "Stage05 original source provenance changed")
    ck(r.get("inherited_stage05_holds")==754,"Stage07 hold metadata changed")
    ck(sha(S05/"report.json")==r["source_stage05_report_sha256"],
       "Stage07 pinned Stage05 report SHA changed")
    meta=m["sites"][SITE]
    native=Path(meta["paths"]["native"])
    era=Path(meta["paths"]["era"])
    candidateinfo=r["derived_full_length_files"][SITE]
    candidate=Path(candidateinfo["full_derived_file"])
    ck(sha(native)==meta["source_provenance"]["native"]["sha256"],
       "Original tower full file SHA mismatch")
    ck(sha(era)==meta["source_provenance"]["era"]["sha256"],
       "Packaged paired original ERA source file SHA mismatch")
    ck(candidateinfo["source_rows"]==N and
       sha(candidate)==candidateinfo["sha256"],"Stage07 Syv full file SHA mismatch")
    ck(sha(S07/"stage07_inherited_754_holds.csv")==
       r["new_receipts_sha256"]["stage07_inherited_754_holds.csv"],
       "Stage07 inherited hold file changed")
    return native,era,candidate
def holdmap():
    d={}
    with regular(S05/"unresolved_hold.csv").open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        ck(rd.fieldnames is not None and
           {"site","TIMESTAMP_START","reason"}.issubset(rd.fieldnames),
           "Stage05 hold file wrong schema")
        for row in rd:
            if row["site"]!=SITE:continue
            k=row["TIMESTAMP_START"]
            ck(k not in d,"Duplicate Syv hold timestamp "+k)
            d[k]=row["reason"]
    ck(len(d)==606,"Stage05 original Syv 606 hold count changed")
    return d
def human_report():
    native,era,candidate=source_files()
    targets,context=target_and_context()
    original=table(native,NATIVE,context,full_n=N)
    latest=table(candidate,NATIVE,context,full_n=N)
    era_rows=table(era,ERA,context) # require all exact native HH and 2h flanks
    reasons=holdmap()
    ck(targets.issubset(reasons),"An expected suspect event is no longer a recorded original hold")
    output=[]
    print("US-SYV ORIGINAL AND STAGE07 VERIFIED ORIGINAL_ALL_ROWS",N,
          "six episodes",len(EPISODES),"suspect_unique_HH",len(targets),
          "full_boundary_context_HH",len(context))
    print("CAUTION QC0=SOURCE OBSERVED, QC1=GAP FILLED, QC2=ERA FILL.")
    print("TA_ERA/VPD_ERA=FLUXNET PROCESSED PACKAGED ERA. NOT INDEPENDENT ERA5-LAND.")
    for name,a,b,n in EPISODES:
        start=(datetime_key(a)-timedelta(hours=2)).strftime("%Y%m%d%H%M")
        stop=(datetime_key(b)+timedelta(hours=2)).strftime("%Y%m%d%H%M")
        print("\n"+"="*120)
        print(name,"SUSPECT_FIRST",a,"SUSPECT_LAST",b,"SUSPECT_HH",n,
              "FLANKS_2_HOURS_EACH_SIDE")
        print("TIME SEGMENT ORIG_TA_F_C ORIG_TA_QC TA_F_MDS MDS_QC PROCESSED_TA_ERA_C ORIGINAL_T_minus_ERA_C STAGE07_TA_F_C STAGE07_TA_QC ORIGINAL_VPD_hPa STAGE07_VPD_hPa VPD_QC HOLD_REASON")
        for k in timekeys(start,stop):
            o=original[k];q=latest[k];e=era_rows[k]
            try:
                dt=float(o["TA_F"]); de=float(e["TA_ERA"])
                delta=f"{dt-de:.3f}" if (math.isfinite(dt) and math.isfinite(de)
                     and dt not in (-9999.,-6999.) and de not in (-9999.,-6999.)) else "NA"
            except (TypeError,ValueError):
                delta="NA"
            segment="HOLD" if a<=k<=b else ("BEFORE" if k<a else "AFTER")
            vals=[k,segment,o["TA_F"],o["TA_F_QC"],o["TA_F_MDS"],
                  o["TA_F_MDS_QC"],e["TA_ERA"],delta,
                  q["TA_F"],q["TA_F_QC"],o["VPD_F"],q["VPD_F"],
                  q["VPD_F_QC"],reasons.get(k,"-")]
            print(" ".join(vals))
            output.append([name,*vals])
        ck(n==sum(a<=k<=b for k in timekeys(start,stop)),
           "Boundary event interval census mismatch")
        print("END",name)
    full_days=[]
    print("\n"+"="*120)
    print("COMPLETE 2007 FEB08-13 + 2003 APR27 ALL 336 NATIVE HH (includes any abnormal continuation past a HOLD boundary)")
    print("TIME STATUS ORIGINAL_TA_F_C ORIGINAL_TA_F_QC TA_F_MDS TA_F_MDS_QC TA_ERA_C ORIG_MINUS_ERA_C STAGE07_TA_C STAGE07_TA_QC ORIGINAL_VPD_F STAGE07_VPD_F STAGE07_VPD_QC STAGE05_HOLD_REASON")
    for k in sorted(context):
        o=original[k];q=latest[k];e=era_rows[k]
        try:
            dt=float(o["TA_F"]);de=float(e["TA_ERA"])
            delta=f"{dt-de:.3f}" if all(math.isfinite(x) and x not in (-9999.,-6999.)
                                     for x in (dt,de)) else "NA"
        except (TypeError,ValueError):delta="NA"
        row=[k,"SUSPECT" if k in targets else "OTHER",o["TA_F"],o["TA_F_QC"],
             o["TA_F_MDS"],o["TA_F_MDS_QC"],e["TA_ERA"],delta,
             q["TA_F"],q["TA_F_QC"],o["VPD_F"],q["VPD_F"],
             q["VPD_F_QC"],reasons.get(k,"-")]
        print(" ".join(row))
        full_days.append(row)
    ck(len(full_days)==336,"Not all six Feb days + Apr27 fully captured")
    print("\nUS-SYV SIX EPISODE FULL BEFORE/DURING/AFTER READOUT PASS; "
          "SOURCE TA, STAGE07, ERA, RH AND ALL MODEL FORCINGS UNCHANGED")
    return output,full_days
def write_report(rows,full_days):
    base=Path.home()/"ameriflux_batch04_manual_review"
    base.mkdir(parents=True,exist_ok=True)
    out=base/("US-Syv_six_suspected_temperature_episodes_98HH_full_flanks_"+
              uuid4().hex[:8]+".csv")
    names=["episode","TIMESTAMP_START","segment","original_TA_F_C",
           "original_TA_F_QC","original_TA_F_MDS","TA_F_MDS_QC",
           "FLUXNET_processed_TA_ERA_C","original_T_minus_ERA_C",
           "Stage07_TA_F_C","Stage07_TA_F_QC","original_VPD_F_hPa",
           "Stage07_VPD_F_hPa","Stage07_VPD_F_QC","Stage05_hold_reason"]
    with out.open("x",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(names);w.writerows(rows)
    print("NEW HUMAN REVIEW CSV",out,"sha256",sha(out))
    complete=base/("US-Syv_ALL_2007_Feb08-13_and_2003_Apr27_336HH_TA_ERA_QC_"+
                    uuid4().hex[:8]+".csv")
    with complete.open("x",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(names[1:]);w.writerows(full_days)
    print("ALL 336 FULL-DAY SOURCE/ERA/QC CSV",complete,"sha256",sha(complete))
    print("ONLY NEW REPORTS UNDER HOME WRITTEN; ORIGINAL/DERIVED FORCING READ-ONLY")
def selftest():
    x,y=target_and_context()
    ck(len(x)==98 and len(y)==336,"Expected six exact abnormal intervals + 336 full-day native HH")
    ck(timekeys("200702101730","200702110700")[-1]=="200702110700",
       "Episode midnight crossing failed")
    print("US-SYV SIX T EPISODE SELF TEST PASS: 98 original hold HH, six episodes, ±2h, no science rewrites")
def main():
    a=argparse.ArgumentParser(description=__doc__)
    g=a.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--inspect",action="store_true")
    g.add_argument("--report",action="store_true")
    p=a.parse_args();selftest()
    if p.self_test:return
    output,full_days=human_report()
    if p.report:write_report(output,full_days)
if __name__=="__main__":main()

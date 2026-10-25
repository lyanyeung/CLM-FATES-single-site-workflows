#!/usr/bin/env python3
"""Stage16 Batch05: scientific SOURCE-PAIR audit of all 1750 Stage10 flags.

Compare (F TA, F VPD), (MDS TA, MDS VPD), (ERA TA, ERA VPD),
(FLUXNET TA, ERA VPD) and hypothetical ERA implied vapor pressure with F TA.
All are DIAGNOSTICS; the latter mixed pair is not an approved forcing.
Read existing Stage10 and Stage15 reports; make NEW CSV+JSON only.
Never modify original sources, case inputs, earlier report folders or Slurm.
"""
import argparse,csv,json,math
from collections import Counter,defaultdict
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
EXPECTED={"US-UiD":0,"US-UMB":23,"US-UMd":15,"US-Var":62,
          "US-Vcm":509,"US-Vcp":629,"US-WCr":88,"US-Whs":1,
          "US-Wjs":401,"US-Wkg":22}
REQUIRED10={"time","class","RH_derived_pct","RH_original_pct","TA_F_C",
 "VPD_F_hPa","TA_F_QC","VPD_F_QC","TA_MDS_C","VPD_MDS_hPa",
 "TA_MDS_QC","VPD_MDS_QC","TA_ERA_C","VPD_ERA_hPa",
 "MDS_pair_physics","ERA_pair_physics","SCIENCE_APPROVAL"}
REQUIRED15={"site","time","source_class","reason_rank","classification",
 "RH_derived_water_pct","TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
 "MDS_pair_physics","ERA_pair_physics","science_status"}
OUTCOLS=("site","time","priority","TA_F_QC","VPD_F_QC","VPD_source",
          "TA_F_C","VPD_F_hPa","original_RH_pct","F_pair_RH_pct",
          "TA_MDS_C","VPD_MDS_hPa","TA_MDS_QC","VPD_MDS_QC",
          "MDS_pair_physical","MDS_pair_RH_pct",
          "TA_ERA_C","VPD_ERA_hPa","ERA_pair_physical","ERA_pair_RH_pct",
          "F_T_plus_ERA_VPD_physical","F_T_plus_ERA_VPD_RH_pct",
          "ERA_implied_e_hPa","ERA_e_plus_F_T_physical",
          "ERA_e_plus_F_T_RH_pct","F_minus_ERA_T_C",
          "F_minus_ERA_VPD_hPa","F_VPD_minus_MDS_VPD_hPa",
          "source_pair_flag","science_status")
KIND={"0":"MEASURED_QC0","1":"GOOD_MDS_QC1","2":"ERA_DOWNSCALED_QC2"}
def num(x):
    try:
        v=float(x)
        if math.isfinite(v) and v not in (-9999.,-6999.):return v
    except (TypeError,ValueError):pass
    return None
def sat(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -80<=t<=60 else None
def pair(t,v):
    s=sat(t)
    if s is None or v is None:return ("MISSING",None)
    return ("PHYSICAL" if 0<=v<=s else "NONPHYSICAL",100*(1-v/s))
def readcsv(file,needed):
    if not file.is_file() or file.is_symlink():raise ValueError("review report absent or symlink: "+str(file))
    with file.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not needed.issubset(reader.fieldnames or []):raise ValueError("review CSV columns missing "+str(file))
        rows=list(reader)
        if any(None in r or any(x is None for x in r.values()) for r in rows):
            raise ValueError("invalid rows "+str(file))
        return rows
def readjson(file):
    if not file.is_file() or file.is_symlink():raise ValueError("review summary not regular "+str(file))
    return json.loads(file.read_text(encoding="utf-8"))
def close(a,b,tol=.002):
    return a is not None and b is not None and abs(a-b)<=tol
def science_row(site,old,ledger):
    stamp=old["time"]
    if ledger["site"]!=site or ledger["time"]!=stamp:
        raise ValueError("Stage15 key mismatch "+site+" "+stamp)
    if old["SCIENCE_APPROVAL"]!="HOLD_NOT_APPROVED" or ledger["science_status"]!="HOLD_NOT_APPROVED":
        raise ValueError("prior data unexpectedly science-approved "+site+" "+stamp)
    T,V=(num(old[k]) for k in ("TA_F_C","VPD_F_hPa"))
    TM,VM=(num(old[k]) for k in ("TA_MDS_C","VPD_MDS_hPa"))
    TE,VE=(num(old[k]) for k in ("TA_ERA_C","VPD_ERA_hPa"))
    t_q,v_q=old["TA_F_QC"],old["VPD_F_QC"]
    if t_q not in KIND or v_q not in KIND:raise ValueError("bad consolidated QC "+site)
    if ledger["TA_F_QC"]!=t_q or ledger["VPD_F_QC"]!=v_q:
        raise ValueError("source QC changed between Stage10 and Stage15")
    if not close(T,num(ledger["TA_F_C"])) or not close(V,num(ledger["VPD_F_hPa"])):
        raise ValueError("Stage15 selected TA/VPD mismatch")
    if v_q=="2" and old["VPD_MDS_QC"] not in ("2","3"):
        raise ValueError("QC2 alternative MDS not poor source "+site)
    if (t_q=="2" and not close(T,TE)) or (t_q!="2" and not close(T,TM)):
        raise ValueError("selected F TA original QA mismatch "+site)
    if (v_q=="2" and not close(V,VE)) or (v_q!="2" and not close(V,VM)):
        raise ValueError("selected F VPD original QA mismatch "+site)
    F,f_rh=pair(T,V)
    M,m_rh=pair(TM,VM)
    E,e_rh=pair(TE,VE)
    MIX,mix_rh=pair(T,VE)
    if f_rh is None or f_rh>=1 or not close(f_rh,num(old["RH_derived_pct"]),.001):
        raise ValueError("screened original low-RH identity failed")
    if (f_rh<0)!=(old["class"]=="NEGATIVE"):
        raise ValueError("original anomaly class mismatch "+site)
    if (f_rh<0)!=(ledger["classification"]=="NEGATIVE"):
        raise ValueError("prior ledger classification mismatch "+site)
    if old["MDS_pair_physics"] not in ("FEASIBLE","NONPHYSICAL") or (M=="PHYSICAL")!=(old["MDS_pair_physics"]=="FEASIBLE"):
        raise ValueError("MDS math label changed "+site)
    E_OLD=old["ERA_pair_physics"]
    if E=="NONPHYSICAL" and E_OLD!="ERA_INTERNAL_NONPHYSICAL":
        raise ValueError("ERA source physics disagreement "+site)
    if E=="PHYSICAL" and E_OLD=="ERA_INTERNAL_NONPHYSICAL":
        raise ValueError("ERA internal physics disagreement "+site)
    inferred_e=None;shadow=None;shadow_rh=None
    if E=="PHYSICAL":
        inferred_e=sat(TE)-VE
        ss=sat(T)
        shadow="PHYSICAL" if 0<=inferred_e<=ss else "NONPHYSICAL"
        if shadow=="PHYSICAL":shadow_rh=100*inferred_e/ss
        old_shadow=("HYPOTHETICAL_ERA_VAPOUR_PAIR_FEASIBLE"
                    if shadow=="PHYSICAL" else "ERA_E_WITH_TOWER_T_NOT_FEASIBLE")
        if E_OLD!=old_shadow:
            raise ValueError("ERA water-vapor shadow incompatibility "+site)
    if old["ERA_pair_physics"]!=ledger["ERA_pair_physics"]:
        raise ValueError("scientific ERA label mismatch")
    source=(KIND[v_q])
    flag=("ERA_SELF_NONPHYSICAL" if E=="NONPHYSICAL" else
          "ERA_IMPLIED_E_INCOMPATIBLE_WITH_TOWER_T" if shadow=="NONPHYSICAL" else
          "MEASURED_EXTREME_LOW" if v_q=="0" else
          "MDS_SOURCE_EXTREME_LOW" if v_q=="1" else
          "ERA_SELECTED_EXTREME_LOW")
    rec={"site":site,"time":stamp,"priority":ledger["reason_rank"],
       "TA_F_QC":t_q,"VPD_F_QC":v_q,"VPD_source":source,
       "TA_F_C":T,"VPD_F_hPa":V,"original_RH_pct":old["RH_original_pct"],
       "F_pair_RH_pct":f_rh,"TA_MDS_C":TM,"VPD_MDS_hPa":VM,
       "TA_MDS_QC":old["TA_MDS_QC"],"VPD_MDS_QC":old["VPD_MDS_QC"],
       "MDS_pair_physical":M,"MDS_pair_RH_pct":m_rh,
       "TA_ERA_C":TE,"VPD_ERA_hPa":VE,
       "ERA_pair_physical":E,"ERA_pair_RH_pct":e_rh,
       "F_T_plus_ERA_VPD_physical":MIX,"F_T_plus_ERA_VPD_RH_pct":mix_rh,
       "ERA_implied_e_hPa":inferred_e,"ERA_e_plus_F_T_physical":shadow,
       "ERA_e_plus_F_T_RH_pct":shadow_rh,
       "F_minus_ERA_T_C":T-TE if T is not None and TE is not None else None,
       "F_minus_ERA_VPD_hPa":V-VE if V is not None and VE is not None else None,
       "F_VPD_minus_MDS_VPD_hPa":V-VM if V is not None and VM is not None else None,
       "source_pair_flag":flag,"science_status":"HOLD_NOT_APPROVED"}
    return {k:rec.get(k) for k in OUTCOLS}
def assess(directory10,directory15):
    m10=readjson(directory10/"audit_summary.json")
    m15=readjson(directory15/"stage15_summary.json")
    if set(m10.get("sites",{}))!=set(SITES) or set(m15.get("sites",{}))!=set(SITES):
        raise ValueError("10-site review cohorts do not match")
    if m15.get("decision")!="ALL_1750_HOLD_NOT_APPROVED":
        raise ValueError("Stage15 global science HOLD missing")
    ledger=readcsv(directory15/"stage15_all_1750_science_holds.csv",REQUIRED15)
    keyed={}
    for r in ledger:
        k=(r["site"],r["time"])
        if k in keyed:raise ValueError("Stage15 duplicate review key "+str(k))
        keyed[k]=r
    results=[];counts=Counter();sites=defaultdict(Counter)
    seen=set()
    for site in SITES:
        rows=readcsv(directory10/(site+"_low_RH_review.csv"),REQUIRED10)
        if len(rows)!=EXPECTED[site]:raise ValueError("Stage10 site count mismatch "+site)
        for row in rows:
            k=(site,row["time"])
            if k in seen or k not in keyed:raise ValueError("Stage10 duplicate/missing key "+str(k))
            seen.add(k)
            scored=science_row(site,row,keyed[k])
            results.append(scored)
            q=scored["VPD_F_QC"]
            counts["SOURCE_VPD_QC"+q]+=1
            sites[site]["SOURCE_VPD_QC"+q]+=1
            for label,column in (("MDS_PHYSICAL","MDS_pair_physical"),
                                  ("ERA_SELF_PHYSICAL","ERA_pair_physical"),
                                  ("ERA_DIRECT_VPD_TOWER_T_PHYSICAL","F_T_plus_ERA_VPD_physical"),
                                  ("ERA_IMPLIED_E_TOWER_T_PHYSICAL","ERA_e_plus_F_T_physical")):
                if scored[column]=="PHYSICAL":
                    counts[label]+=1;sites[site][label]+=1
                elif scored[column]=="NONPHYSICAL":
                    counts[label.replace("PHYSICAL","NONPHYSICAL")]+=1
            if scored["F_minus_ERA_T_C"] is not None and abs(scored["F_minus_ERA_T_C"])>5:
                counts["ABS_TOWER_MINUS_ERA_T_GT5C"]+=1
                sites[site]["ABS_TOWER_MINUS_ERA_T_GT5C"]+=1
            if scored["F_minus_ERA_VPD_hPa"] is not None and abs(scored["F_minus_ERA_VPD_hPa"])>5:
                counts["ABS_F_MINUS_ERA_VPD_GT5hPa"]+=1
            counts["source_flag_"+scored["source_pair_flag"]]+=1
            counts["events"]+=1;sites[site]["events"]+=1
    if seen!=set(keyed):raise ValueError("Stage15 review ledger has orphan source times")
    invariants={"events":1750,"SOURCE_VPD_QC0":119,"SOURCE_VPD_QC1":965,
      "SOURCE_VPD_QC2":666,"MDS_PHYSICAL":700,
      "MDS_NONPHYSICAL":1050,"ERA_SELF_NONPHYSICAL":55,
      "ERA_SELF_PHYSICAL":1695,"ERA_IMPLIED_E_TOWER_T_PHYSICAL":1580,
      "ERA_IMPLIED_E_TOWER_T_NONPHYSICAL":115}
    for k,n in invariants.items():
        if counts[k]!=n:raise ValueError("Stage09/15 original physics invariant "+
                                      k+": "+str(counts[k])+" != "+str(n))
    return results,counts,sites
def selftest():
    assert pair(10,2)[0]=="PHYSICAL"
    assert pair(10,20)[0]=="NONPHYSICAL"
    assert pair(None,2)[0]=="MISSING"
    assert sat(10)>12
    print("STAGE16 SELF-TEST PASS | independent paired-source water-RH, ERA vapor pressure holds; NO ORIGINAL WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage10-dir",type=Path)
    p.add_argument("--stage15-dir",type=Path)
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:selftest();return
    if not args.stage10_dir or not args.stage15_dir or not args.output_dir:
        p.error("requires --stage10-dir --stage15-dir --output-dir")
    src10=args.stage10_dir.expanduser().resolve()
    src15=args.stage15_dir.expanduser().resolve()
    out=args.output_dir.expanduser().resolve()
    if not src10.is_dir() or not src15.is_dir():p.error("input report directory missing")
    if out.exists() or not out.parent.is_dir() or any(
        out==p or p in out.parents or out in p.parents for p in (src10,src15)):
        p.error("report-only output must be new and disjoint from old report folders")
    records,counts,sites=assess(src10,src15)
    out.mkdir(exist_ok=False)
    with (out/"stage16_all_1750_source_pair_review.csv").open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=OUTCOLS)
        writer.writeheader();writer.writerows(sorted(records,key=lambda r:(r["site"],r["time"])))
    output={"decision":"HOLD_ALL_UNAPPROVED","events":1750,
      "unit_note":"T in Celsius, VPD in hPa, RH %; Magnus water saturation only",
      "scientific_caution":"physical feasibility is not validation; ERA VPD and ERA e counterfactuals differ",
      "counts":dict(counts),"sites":{s:dict(sites[s]) for s in SITES}}
    with (out/"stage16_summary.json").open("x",encoding="utf-8") as f:
        json.dump(output,f,indent=2,sort_keys=True)
    print("STAGE16 AGGREGATE",json.dumps(dict(counts),sort_keys=True),flush=True)
    for site in SITES:
        print("STAGE16 SITE",site,json.dumps(dict(sites[site]),sort_keys=True),flush=True)
    print("STAGE16 SUMMARY sites=10/10 events=1750 measured=119 MDS=965 ERA=666 approved=0 reports="+str(out),flush=True)
    print("NEW REVIEW CSV/JSON ONLY; NO ORIGINAL SOURCES/STAGE10/STAGE15/FORCING/MODEL/SLURM CHANGES")
if __name__=="__main__":main()

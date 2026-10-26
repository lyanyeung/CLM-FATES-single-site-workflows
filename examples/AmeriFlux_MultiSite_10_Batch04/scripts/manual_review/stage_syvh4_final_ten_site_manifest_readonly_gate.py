#!/usr/bin/env python3
"""Batch04 SYVH4: independently audit FINAL operator-selected TEN full met CSVs.

After SYVH3 18 RH-only edits has actually completed (not before):
--manifest exact resulting final research RESEARCH_TEN_SITE_MANIFEST.tsv
--check: verifies SYVH3 receipt 438288 Syv HH, 18 RH modifications, the
         reported final full Syv SHA, unchanged nine older selected sources.
         For EVERY selected site: SHA256, 30min native cadence and END,
         finite values, saturation/negative VPD, RH range and closure,
         pressure plausibility, raw QC mixes. All original files READ ONLY.
--report: additionally save small new timestamped JSON and TSV to HOME.
NEVER implies that any other site's unresolved source science holds passed,
or DATM/CIME/Postv5/Slurm/spinup is authorised. This is a DIAGNOSTIC.
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from uuid import uuid4

E=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
OLD=E/"manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_20261026T024759Z_6e1e07ad"
OLD_MAN=OLD/"RESEARCH_TEN_SITE_MANIFEST.tsv"
SITES={"US-Rpf","US-Seg","US-Ses","US-Slt","US-SP1",
       "US-SRG","US-SRM","US-Syv","US-Ton","US-Uaf"}
SHOLD="200803091300"
SOURCE_SYV_N=438288
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def ck(cond,msg):
    if not cond:raise ValueError(msg)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Missing/symlinked full scientific source "+str(p))
    return p
def digest(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def tab(p,need,sep="\t"):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter=sep)
        ck(r.fieldnames is not None and len(set(r.fieldnames))==len(r.fieldnames)
           and set(need).issubset(r.fieldnames),"Research 10-site manifest fields changed "+str(p))
        return r.fieldnames,list(r)
def obj(p):
    return json.loads(regular(p).read_text(encoding="utf-8"))
def value(s):
    x=str(s if s is not None else "").strip()
    if x.upper() in MISSING:return None
    try:v=float(x)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) else None
def es(t):
    if t is None or t< -60 or t>60:return None
    return 6.112*math.exp(17.67*t/(t+243.5))
def parse(k):
    ck(len(k)==12 and k.isdigit(),"Malformed native YYMMDDHHMM "+repr(k))
    return datetime.strptime(k,"%Y%m%d%H%M")
def check_manifest(directory):
    rec=obj(directory/"SYVH3_RESEARCH_SCIENCE_RECEIPT.json")
    syv=Path(rec["new_full_candidate_path"])
    ck(syv.parent==directory and rec.get("full_site_rows")==SOURCE_SYV_N
       and rec.get("derived_RH_only_repaired_HH")==18
       and rec.get("QC0_T_and_VPD_preserved_HH")==18
       and rec.get("strict_global_invalid_HH")==1
       and rec.get("quantisation_aware_global_invalid_HH")==0
       and rec.get("source_production_approval") is False
       and rec.get("postv5_approved") is False,
       "SYVH3 final source receipt/QA safety fields changed")
    ck(digest(syv)==rec["new_full_SHA256"],
       "Final Syv candidate full 438288-HH SHA mismatch")
    fields,now=tab(directory/"RESEARCH_TEN_SITE_MANIFEST.tsv",
                   ("site","source_path","source_SHA256","latest_stage"))
    _,prior=tab(OLD_MAN,("site","source_path","source_SHA256","latest_stage"))
    ck(len(now)==10 and len(prior)==10 and
       {x["site"] for x in now}==SITES and
       {x["site"] for x in prior}==SITES,
       "Expected exact ten site names, duplicates not allowed")
    by={x["site"]:x for x in now}
    ck(len(by)==10,"Duplicate site in ten-site input selection")
    ck(Path(by["US-Syv"]["source_path"])==syv and
       by["US-Syv"]["source_SHA256"]==rec["new_full_SHA256"],
       "Latest ten-site selection is not final SYVH3 Syv file")
    ck([x for x in prior if x["site"]!="US-Syv"]==
       [x for x in now if x["site"]!="US-Syv"],
       "One or more of NINE other previous research sites changed")
    ck(all(not Path(x["source_path"]).is_symlink() and
           Path(x["source_path"]).is_file() for x in now),
       "Source manifest has missing/symlinked full site file")
    paths=[str(Path(x["source_path"]).resolve()) for x in now]
    ck(len(set(paths))==10,"Two sites map to same input forcing file")
    return rec,by
def audit_one(site,p,claimed_sha):
    sha=digest(p)
    ck(sha==claimed_sha,"SOURCE SHA mismatch "+site+" "+str(p))
    n=0;badclock=0;badend=0;missing=Counter();flags=Counter()
    errs=Counter();physical=Counter();qc=Counter();sample=Counter()
    minT=None;maxT=None;prev=None;first=None;last=None
    examples=[]
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        required={"TIMESTAMP_START","TIMESTAMP_END","TA_F","TA_F_QC","VPD_F",
                  "VPD_F_QC","PA_F"}
        ck(r.fieldnames is not None and required.issubset(r.fieldnames)
           and len(set(r.fieldnames))==len(r.fieldnames),
           "Selected source has broken FLUXMET native schema "+site)
        hasRH="RH" in r.fieldnames
        for row in r:
            n+=1
            tkey=row["TIMESTAMP_START"];e=row["TIMESTAMP_END"]
            if first is None:first=tkey
            last=tkey
            if prev is not None and tkey!=prev:
                badclock+=1
                if len(examples)<14:examples.append(("NATIVE_CADENCE",tkey,prev))
            try:
                start=parse(tkey)
                end=parse(e)
            except (ValueError,TypeError):
                errs["INVALID_TIMESTAMP"]+=1
                if len(examples)<14:examples.append(("INVALID_TIMESTAMP",tkey,e))
                break
            if (end-start)!=timedelta(minutes=30):
                badend+=1
                if len(examples)<14:examples.append(("END_INTERVAL_NOT_30MIN",tkey,e))
            prev=(start+timedelta(minutes=30)).strftime("%Y%m%d%H%M")
            t=value(row["TA_F"]);v=value(row["VPD_F"]);pa=value(row["PA_F"])
            rh=value(row["RH"]) if hasRH else None
            qc[row["TA_F_QC"]]+=1
            flags[row["VPD_F_QC"]]+=1
            if t is None:missing["TA_F"]+=1
            if v is None:missing["VPD_F"]+=1
            if pa is None:missing["PA_F"]+=1
            if hasRH and rh is None:missing["RH"]+=1
            if t is not None:
                minT=t if minT is None else min(minT,t)
                maxT=t if maxT is None else max(maxT,t)
            sat=es(t)
            if sat is None:
                physical["TA_UNPHYSICAL_OR_MISSING"]+=1
                if len(examples)<14:examples.append(("TA_INVALID",tkey,row["TA_F"]))
            elif v is None:
                physical["VPD_MISSING"]+=1
            elif v < 0:
                physical["VPD_NEGATIVE"]+=1
                if len(examples)<14:examples.append(("VPD_NEGATIVE",tkey,v))
            elif v>sat+0.0005:
                physical["VPD_ABOVE_WATER_SATURATION_BEYOND_PRECISION"]+=1
                if len(examples)<14:examples.append(("VPD_OVERSAT",tkey,t,v,sat))
            elif v>sat:
                physical["VPD_WITHIN_THREE_DECIMAL_ROUNDING"]+=1
                if len(examples)<14:examples.append(("VPD_ROUNDING",tkey,t,v,sat))
            else:physical["VPD_BASIC_VALID"]+=1
            if hasRH and rh is not None:
                if not 0<=rh<=100:
                    physical["RH_OUT_OF_RANGE"]+=1
                    if len(examples)<14:examples.append(("RH_INVALID",tkey,rh))
                elif sat is not None and v is not None and 0<=v<=sat+0.0005:
                    # Allow native source 3-decimal resolution to propagate
                    # into derived RH uncertainty, especially in subfreezing
                    # sites with es(T)<1hPa.
                    pred=100*(1-v/sat)
                    tolerance=max(0.2,100*.0005/sat+.01)
                    if abs(pred-rh)>tolerance:
                        physical["RH_NOT_CLOSED_BEYOND_VPD_RESOLUTION"]+=1
                        if len(examples)<14:examples.append(("RH_CLOSURE",tkey,t,v,rh,pred))
            if pa is not None and not 40<=pa<=115:
                physical["PA_OUTSIDE_PLAUSIBILITY_RANGE_KPA"]+=1
                if len(examples)<14:examples.append(("PA_INVALID",tkey,pa))
    ck(n>0,"Empty site full native forcing file "+site)
    if site=="US-Syv":
        ck(n==SOURCE_SYV_N,"SYVH3 fully verified Syv native source row count changed")
    problems=sum(physical[k] for k in ("TA_UNPHYSICAL_OR_MISSING",
          "VPD_MISSING","VPD_NEGATIVE","VPD_ABOVE_WATER_SATURATION_BEYOND_PRECISION",
          "RH_OUT_OF_RANGE","RH_NOT_CLOSED_BEYOND_VPD_RESOLUTION",
          "PA_OUTSIDE_PLAUSIBILITY_RANGE_KPA"))
    if badclock or badend or errs["INVALID_TIMESTAMP"]:
        problems+=badclock+badend+errs["INVALID_TIMESTAMP"]
    print("SITE",site,"FULL_HH",n,"SOURCE_SHA_PASS",sha,
          "FIRST",first,"LAST",last,
          "TA_QC",dict(qc),"VPD_QC",dict(flags),
          "MISSING",dict(missing),"PHYSICAL",dict(physical),
          "CLOCK_GAPS_OR_DUP",badclock,"BAD_30M_END",badend,
          "SCIENCE_QA_EVENTS",problems)
    if examples:print("EXAMPLES",site,examples)
    return {"site":site,"path":str(p),"sha256":sha,"native_halfhours":n,
            "first_timestamp":first,"last_timestamp":last,
            "temperature_min_C":minT,"temperature_max_C":maxT,
            "temperature_QC_counts":dict(qc),"vpd_QC_counts":dict(flags),
            "missing":dict(missing),"physics":dict(physical),
            "bad_cadence":badclock,"bad_end_timestamp":badend,
            "errors":dict(errs),"science_qa_event_count":problems,
            "examples":examples}
def selftest():
    ck(parse("200802290030")+timedelta(minutes=30)==parse("200802290100"),
       "Native leap-day half-hour parse broken")
    s=es(-6.234)
    ck(3.842>s and 3.842-s<0.0005 and es(-27.817)>.595,
       "Native precision exception / extreme cold saturation test wrong")
    print("SYVH4 TEN SITE SELF TEST PASS leap-day, VPD source precision, no writes")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest-dir",required=True,
         help="Exact final output directory printed by US-Syv SYVH3 --apply")
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--report",action="store_true")
    x=p.parse_args();selftest()
    folder=Path(x.manifest_dir)
    ck(folder.is_dir() and not folder.is_symlink(),
       "Cannot locate exact output SYVH3 full candidate")
    rec,selected=check_manifest(folder)
    print("FINAL SYVH3 SOURCE VERIFIED",rec["new_full_SHA256"],
          "SOURCE_18_DERIVED_RH_CLOSURE",rec["derived_RH_only_repaired_HH"],
          "PRECISION_EXCEPTIONS",rec["precision_only_boundary_exception"])
    outputs=[]
    for site in sorted(SITES):
        row=selected[site]
        outputs.append(audit_one(site,Path(row["source_path"]),row["source_SHA256"]))
    events={r["site"]:r["science_qa_event_count"] for r in outputs}
    print("TEN SITE SCIENTIFIC QA TOTALS",events,
          "PRODUCTION_GATE","NOT_APPROVED_RESEARCH_CANDIDATES",
          "NO_POSTV5_DATM_CIME_SLURM_SPINUP")
    if x.report:
        directory=Path.home()/"ameriflux_batch04_manual_review"
        directory.mkdir(parents=True,exist_ok=True)
        label=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:6]
        jpath=directory/("Batch04_SYVH4_FINAL_TEN_SITE_SOURCE_QA_"+label+".json")
        tpath=directory/("Batch04_SYVH4_FINAL_TEN_SITE_SOURCE_QA_"+label+".tsv")
        jpath.write_text(json.dumps(
            {"research_only":True,"syv_final_sha256":rec["new_full_SHA256"],
             "n_sites":10,"sites":outputs,"science_gate":events,
             "DATM_ready":False,"production_approved":False},
             indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        with tpath.open("x",encoding="utf-8",newline="") as f:
            w=csv.writer(f,delimiter="\t")
            w.writerow(["site","native_HH","first_HH","last_HH","science_QA_events",
                        "physical_qc_flags_JSON","missing_fields_JSON","source_SHA256"])
            for r in outputs:
                w.writerow([r["site"],r["native_halfhours"],r["first_timestamp"],
                          r["last_timestamp"],r["science_qa_event_count"],
                          json.dumps(r["physics"],sort_keys=True),
                          json.dumps(r["missing"],sort_keys=True),r["sha256"]])
        print("TEN SITE READ ONLY QA REPORT",jpath,"SHA",digest(jpath))
        print("TEN SITE READ ONLY QA TSV",tpath,"SHA",digest(tpath))
    print("TEN SITE FULL SOURCE CHECK COMPLETE; source and candidate immutable; no model jobs submitted")
if __name__=="__main__":main()

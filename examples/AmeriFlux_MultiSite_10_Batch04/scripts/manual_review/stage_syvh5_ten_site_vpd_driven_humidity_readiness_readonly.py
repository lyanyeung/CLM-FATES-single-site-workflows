#!/usr/bin/env python3
"""Batch04 SYVH5: ten-site SOURCE-VERIFIED humidity/forcing readiness audit.

Starts from actual operator-passed SYVH3 RESEARCH_TEN_SITE_MANIFEST.tsv,
not any older Stage11/Stage14 manifest. Full CSV SHA and original nine-site
selection are verified with the existing SYVH4 pin. NO met changes, no source
writes, NO original RH redefinition/overwrite, NO model/CIME/Slurm jobs.

Scientific distinction:
  FLUXMET T [°C], VPD [hPa], PA_F [kPa] are the primary physical humidity
  source for model derivation. A stored optional RH column is NOT NECESSARILY
  reconstructed from the same three values; it may be independent
  measurement or earlier-processing lineage. RH differences and missingness
  are therefore strictly diagnostics, not automatic "unphysical T/VPD".
  Model RH_calc and QBOT_calc must be generated together from the SAME
  selected T, VPD, pressure in a separately reviewed conversion stage.
  q = eps*e / [p - (1-eps)*e], e = es_water(T)-VPD, eps=.622;
  pressure conversion kPa->hPa. No source fields are overwritten.

--check: no writes, prints per-site physical-humidity forcing readiness,
         RH diag distribution, top egregious source RH mismatches,
         explicit native VPD rounding compatible exceptions.
--report: same read-only audit; new small HOME JSON/TSV reports only.
Any source T/VPD/PA violation beyond input precision blocks the numerical
readiness gate. A quantisation-only VPD exception is a separate gate, NOT
silently capped or converted to QBOT as 0 without a conversion policy.
Other user temperature-source approval gates / Post-v5 remain separate.
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timezone,timedelta
from pathlib import Path
from collections import Counter,defaultdict
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
EXPECTED={"US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
          "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf"}
EXPECTED_FINAL_SYV_SHA="9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa"
N_SYV=438288
EPS=0.622
HALF_VPD_PRECISION_HPA=0.0005
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
SAME_SOURCE_QC_POLICY="PRESERVE_INPUT_RH_DO_NOT_OVERWRITE_SOURCE"

def guard(ok,msg):
    if not ok:raise ValueError(msg)
def file(p):
    guard(p.is_file() and not p.is_symlink(),"Absent/symlink source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def num(s):
    z=str(s if s is not None else "").strip()
    if z.upper() in MISSING:return None
    try:f=float(z)
    except (TypeError,ValueError):return None
    return f if math.isfinite(f) else None
def sat(t):
    return 6.112*math.exp(17.67*t/(243.5+t)) if t is not None and -60<t<60 else None
def table(p,required,sep="\t"):
    with file(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter=sep)
        guard(r.fieldnames and set(required).issubset(r.fieldnames) and
              len(set(r.fieldnames))==len(r.fieldnames),"Manifest source header changed")
        return r.fieldnames,list(r)
def canonical(folder):
    rpath=folder/"SYVH3_RESEARCH_SCIENCE_RECEIPT.json"
    rec=json.loads(file(rpath).read_text(encoding="utf-8"))
    guard(rec.get("full_site_rows")==N_SYV and
          rec.get("derived_RH_only_repaired_HH")==18 and
          rec.get("new_full_SHA256")==EXPECTED_FINAL_SYV_SHA and
          rec.get("source_production_approval") is False and
          rec.get("postv5_approved") is False,
          "Actual operator SYVH3 final source evidence mismatch")
    sitefile=Path(rec["new_full_candidate_path"])
    guard(sitefile.parent==folder and sha(sitefile)==EXPECTED_FINAL_SYV_SHA,
          "Final Syv full candidate immutable SHA mismatch")
    _,items=table(folder/"RESEARCH_TEN_SITE_MANIFEST.tsv",
                  ("site","source_path","source_SHA256","latest_stage"))
    guard(len(items)==10 and {x["site"] for x in items}==EXPECTED,
          "Exact ten-site final roster changed")
    fields={x["site"]:x for x in items}
    guard(Path(fields["US-Syv"]["source_path"])==sitefile and
          fields["US-Syv"]["source_SHA256"]==EXPECTED_FINAL_SYV_SHA,
          "Final Syv not selected in ten-site manifest")
    prior=ROOT/"manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved/candidate_20261026T024759Z_6e1e07ad/RESEARCH_TEN_SITE_MANIFEST.tsv"
    _,was=table(prior,("site","source_path","source_SHA256","latest_stage"))
    guard([x for x in items if x["site"]!="US-Syv"]==
          [x for x in was if x["site"]!="US-Syv"],
          "Nine other source manifest rows changed since source-verified repair")
    return fields

def classify_delta(delta,s,t):
    tolerance=max(.2,100*HALF_VPD_PRECISION_HPA/s+.01)
    if abs(delta)<=tolerance:return "RH_CLOSURE_WITHIN_INPUT_RESOLUTION"
    if abs(delta)<=1:return "RH_DIFFERENCE_0TO1_PP"
    if abs(delta)<=5:return "RH_DIFFERENCE_1TO5_PP"
    if abs(delta)<=20:return "RH_DIFFERENCE_5TO20_PP"
    return "RH_DIFFERENCE_GT20_PP"

def one(site,filepath,expected_sha):
    digest=sha(filepath)
    guard(digest==expected_sha,"Full native source SHA mismatch "+site)
    n=0;first=last=prev=None
    blockers=Counter();native=Counter();rh_bucket=Counter()
    qc=Counter();vq=Counter();year_counts=defaultdict(Counter)
    special=[]; worst=[];max_error=0
    n_qbot=0; qmin=None;qmax=None
    with file(filepath).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        required={"TIMESTAMP_START","TIMESTAMP_END","TA_F","VPD_F",
                  "PA_F","TA_F_QC","VPD_F_QC"}
        guard(rd.fieldnames and set(required).issubset(rd.fieldnames) and
              len(set(rd.fieldnames))==len(rd.fieldnames),
              "Malformed selected FLUXMET_HH source fields "+site)
        hasRH="RH" in rd.fieldnames
        for row in rd:
            n+=1
            k=row["TIMESTAMP_START"];end=row["TIMESTAMP_END"]
            if first is None:first=k
            if prev is not None and prev!=k:
                blockers["NATIVE_TIME_GAP_DUPLICATE"]+=1
                if len(special)<12:special.append(["CLOCK",k,prev])
            try:
                st=datetime.strptime(k,"%Y%m%d%H%M")
                en=datetime.strptime(end,"%Y%m%d%H%M")
                if en-st!=timedelta(minutes=30):
                    blockers["TIMESTAMP_END_NOT_30_MIN"]+=1
            except (ValueError,TypeError):
                blockers["MALFORMED_TIMESTAMP"]+=1
                break
            prev=(st+timedelta(minutes=30)).strftime("%Y%m%d%H%M")
            last=k
            year=int(k[:4])
            t=num(row["TA_F"]);v=num(row["VPD_F"]);p=num(row["PA_F"])
            rh=num(row["RH"]) if hasRH else None
            qc[row["TA_F_QC"]]+=1;vq[row["VPD_F_QC"]]+=1
            if t is None or not -55<=t<=55:
                blockers["TA_MISSING_OR_OUTSIDE_BOUND"]+=1
                continue
            if v is None or v<0:
                blockers["VPD_MISSING_OR_NEGATIVE"]+=1
                continue
            if p is None or not 65<=p<=110:
                blockers["PA_KPA_MISSING_OR_OUTSIDE_65_110"]+=1
                continue
            s=sat(t)
            if s is None:
                blockers["TA_NO_SATURATION_CALC"]+=1
                continue
            if v>s:
                x=v-s
                if x<=HALF_VPD_PRECISION_HPA:
                    native["VPD_ROUNDING_ONLY"]+=1
                    year_counts[year]["VPD_ROUNDING_ONLY"]+=1
                    if len(special)<12:
                        special.append(["VPD_ROUNDING",k,t,v,s,x,row["VPD_F_QC"]])
                else:
                    blockers["VPD_EXCEEDS_SATURATION_OUTSIDE_PRECISION"]+=1
                    if len(special)<12:special.append(["VPD_BAD",k,t,v,s,x])
                continue
            e=s-v
            press_hpa=p*10
            denom=press_hpa-(1-EPS)*e
            if e<0 or denom<=0:
                blockers["HUMIDITY_MASS_FRACTION_DENOMINATOR_INVALID"]+=1
                continue
            q=EPS*e/denom
            if not 0<=q<.10:
                blockers["QBOT_UNPHYSICAL_0_TO_0P1"]+=1
                if len(special)<12:special.append(["QBOT_BAD",k,t,v,p,q])
                continue
            n_qbot+=1
            qmin=q if qmin is None else min(qmin,q)
            qmax=q if qmax is None else max(qmax,q)
            if hasRH:
                if rh is None:
                    rh_bucket["RH_SOURCE_NOT_PRESENT"]+=1
                    year_counts[year]["RH_SOURCE_NOT_PRESENT"]+=1
                elif not 0<=rh<=100:
                    rh_bucket["RH_SOURCE_OUT_OF_RANGE"]+=1
                    year_counts[year]["RH_SOURCE_OUT_OF_RANGE"]+=1
                    if len(special)<12:special.append(["RH_RANGE",k,rh])
                else:
                    implied=100*(1-v/s)
                    error=rh-implied
                    name=classify_delta(error,s,t)
                    rh_bucket[name]+=1
                    year_counts[year][name]+=1
                    err=abs(error)
                    max_error=max(max_error,err)
                    if err>20:
                        candidate=(round(err,3),k,round(t,3),round(v,3),
                                   round(rh,3),round(implied,3),
                                   row["TA_F_QC"],row["VPD_F_QC"])
                        worst.append(candidate)
                        if len(worst)>20:
                            worst.sort(reverse=True)
                            worst=worst[:20]
    guard(n>0 and (site!="US-Syv" or n==N_SYV),"Empty/truncated site "+site)
    issue_n=sum(blockers.values())
    status=("MODEL_NUMERICAL_HUMIDITY_PASS_WITH_EXPLICIT_VPD_ROUNDING"
            if issue_n==0 else "BLOCKED_NUMERICAL_HUMIDITY")
    print("SITE",site,"FULL_HH",n,"SHA256_PASS",digest,
          "NUMERICAL_HUMIDITY_PREPARED_HH",n_qbot,
          "VPD_ROUNDING_EXCEPTIONS",native["VPD_ROUNDING_ONLY"],
          "SOURCE_RH_PROVENANCE_DIAGNOSTIC",dict(rh_bucket),
          "NUMERIC_BLOCKERS",dict(blockers),
          "QBOT_RANGE_KG_KG",[qmin,qmax],
          "SOURCE_RH_MAX_ABS_DIFF_PP",round(max_error,3),
          "STATUS",status)
    print("WORST_20_RH_DIFFERENCES",site,sorted(worst,reverse=True)[:20])
    if special:print("ADDITIONAL_SOURCE_FLAGS",site,special)
    return {"site":site,"full_halfhours":n,"sha256":digest,
            "first_timestamp":first,"last_timestamp":last,
            "numerically_derived_QBOT_halfhours":n_qbot,
            "rounding_only_HH":native["VPD_ROUNDING_ONLY"],
            "numeric_blockers":dict(blockers),
            "native_RH_source_diagnostics":dict(rh_bucket),
            "rh_year_source_discrepancy_counts":
                {str(y):dict(c) for y,c in sorted(year_counts.items())},
            "max_raw_vs_derived_RH_difference_pp":round(max_error,5),
            "worst_20_raw_vs_derived_rh":sorted(worst,reverse=True)[:20],
            "TA_source_QC":dict(qc),"VPD_source_QC":dict(vq),
            "candidate_specific_humidity_range_kg_kg":[qmin,qmax],
            "status":status}

def selftest():
    guard(abs(sat(-6.234)-3.841976803313088)<1e-10,
          "Water saturation subfreezing precision wrong")
    guard(sat(5)>sat(-5),"VPD saturation trend wrong")
    guard(classify_delta(10,10,20)=="RH_DIFFERENCE_5TO20_PP",
          "RH source-difference bucket wrong")
    print("SYVH5 SELF-TEST PASS: VPD source precision, water saturation, RH source diagnostic. No writes.")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest-dir",required=True)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--report",action="store_true")
    a=p.parse_args();selftest()
    if a.self_test:return
    folder=Path(a.manifest_dir)
    guard(folder.is_dir() and not folder.is_symlink(),
          "Invalid exact final SYVH3 source directory")
    items=canonical(folder)
    print("SOURCE MANIFEST SHA PINNED 10/10 FINAL OPERATOR SYVH3",
          EXPECTED_FINAL_SYV_SHA)
    allout=[]
    for site in sorted(EXPECTED):
        row=items[site]
        allout.append(one(site,Path(row["source_path"]),row["source_SHA256"]))
    b={x["site"]:x["status"] for x in allout}
    print("TEN SITE PRIMARY VPD_PA_T HUMIDITY NUMERICAL GATE",b)
    print("RH SOURCE IS AUXILIARY DIAGNOSTIC: NEVER OVERWRITE INPUT RH OR QC0 SOURCE.")
    print("CONSISTENT RH/QBOT MUST BE DERIVED TOGETHER WHEN FUTURE DATM SOURCE PROCESSING IS APPROVED.")
    print("PRODUCTION AND POSTV5 GATE STILL REQUIRES INDEPENDENT SCIENCE SOURCE/TOWER APPROVAL.")
    if a.report:
        home=Path.home()/"ameriflux_batch04_manual_review"
        home.mkdir(parents=True,exist_ok=True)
        tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:6]
        jpath=home/("Batch04_SYVH5_SOURCE_RH_VS_PRIMARY_FORCING_"+tag+".json")
        tpath=home/("Batch04_SYVH5_SOURCE_RH_VS_PRIMARY_FORCING_"+tag+".tsv")
        jpath.write_text(json.dumps({
            "operator_final_SYVH3_source_sha":EXPECTED_FINAL_SYV_SHA,
            "ten_sites_scanned":len(allout),
            "primary_humidity_numeric_readiness":b,
            "source_RH_policy":SAME_SOURCE_QC_POLICY,
            "not_production_approved":True,"no_source_changed":True,
            "all_sites":allout
         },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        with tpath.open("x",encoding="utf-8",newline="") as f:
            w=csv.writer(f,delimiter="\t")
            w.writerow(["site","full_HH","num_QBOT_ready","rounding_HH",
                        "numeric_blockers","RH_source_diagnostics","model_numeric_status","SHA256"])
            for x in allout:
                w.writerow([x["site"],x["full_halfhours"],x["numerically_derived_QBOT_halfhours"],
                    x["rounding_only_HH"],json.dumps(x["numeric_blockers"],sort_keys=True),
                    json.dumps(x["native_RH_source_diagnostics"],sort_keys=True),
                    x["status"],x["sha256"]])
        print("SOURCE AWARE READONLY TEN SITE REPORT",jpath,"SHA256",sha(jpath))
        print("SOURCE AWARE READONLY TEN SITE TSV",tpath,"SHA256",sha(tpath))
    print("SYVH5 TEN SITE SOURCE-AWARE HUMIDITY SCREEN COMPLETE: NO MET/CIME/MODEL FILE WRITES")
if __name__=="__main__":main()

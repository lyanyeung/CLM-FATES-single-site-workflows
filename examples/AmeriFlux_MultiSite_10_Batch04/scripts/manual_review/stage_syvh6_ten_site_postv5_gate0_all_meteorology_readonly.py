#!/usr/bin/env python3
"""Batch04 SYVH6: all seven native met fields, NOLEAP and DATM Gate-0 audit.

Runs on the FINAL US-Syv SYVH3 RESEARCH_TEN_SITE_MANIFEST.tsv, not a
historical Stage11/Stage14 manifest. Imports SYVH5's independent source
pinning helper from the same exact GitHub commit next to this script.
Original tower FLUXMET files are READ ONLY; no repaired file copies, no
surface/ZBOT/NetCDF/DATM/CIME/Slurm/spinup changes.

Audit TA_F, VPD_F, PA_F, SW_IN_F, LW_IN_F, WS_F, P_F, including
units: TA in Celsius, VPD in hPa, PA in kPa, SW/LW Wm-2,
WS m/s, precipitation P_F in mm/30min. Conversion previews are
TBOT=TA+273.15, PSRF=PA*1000, FSDS=SW, FLDS=LW, WIND=WS,
PRECTmms=P_F/1800, QBOT from TA/VPD/PA.

Small raw -SW/-WS/-P near observed numerical tolerance are counted
separately, never silently clipped in original files. VPD oversat at
<=0.0005 hPa is a separate model-QBOT quantisation HOLD; 3 known source
examples must be exact, not silently set to zero or physical floor.
NOLEAP excludes Feb29 at conversion only: verify all original native
half hours, each non-leap year 17520 model steps.

This Gate-0 is NUMERIC/STRUCTURAL ONLY. Source tower scientific approvals,
wind/temperature measurement height/ZBOT, calendar centering, solar and
precipitation semantics, surface/PFT and production release remain separate.
"""
import argparse,csv,hashlib,importlib.util,json,math
from collections import Counter
from datetime import datetime,timedelta,timezone
from pathlib import Path
from uuid import uuid4

SITES=("US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
       "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf")
NATIVE_FIELDS=("TA_F","VPD_F","PA_F","SW_IN_F","LW_IN_F","WS_F","P_F")
D=Path(__file__).resolve().with_name("stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py")
ROUNDING={("US-Rpf","200802060700"),("US-Rpf","200802060900"),("US-Syv","200803091300")}
NOLEAP_ROWS=365*48
EPS=.622
LIMITS={"TA_F":(-55,55),"PA_F":(65,110),
        "SW_IN_F":(-5,1600),"LW_IN_F":(60,800),
        "WS_F":(-.1,75),"P_F":(-.001,300)}
NEG_TOL={"SW_IN_F":-5,"WS_F":-.1,"P_F":-.001}

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def read_helper():
    ck(D.is_file() and not D.is_symlink(),"SYVH5 sibling source helper absent "+str(D))
    spec=importlib.util.spec_from_file_location("syvh6_pinned_syvh5",str(D))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for a in ("canonical","sha","num","sat"):
        ck(callable(getattr(module,a,None)),"SYVH5 helper missing "+a)
    return module
def timeparse(s):
    ck(len(s)==12 and s.isdigit(),"Not numeric YYYYMMDDHHMM "+repr(s))
    return datetime.strptime(s,"%Y%m%d%H%M")
def ffmt(x):return f"{x:.9g}"
def analyze(site,entry,helper):
    p=Path(entry["source_path"])
    gotsha=helper.sha(p)
    ck(gotsha==entry["source_SHA256"],"Selected source SHA changed "+site)
    first=last=previous=None
    n=0;noleap=0;feb29=0
    issues=Counter();caution=Counter();sourceqc=Counter();samples=[]
    years=Counter();precip_count=0;wet_total_mm=0.
    qmin=qmax=None
    with p.open(encoding="utf-8-sig",newline="") as file:
        rd=csv.DictReader(file)
        mandatory={"TIMESTAMP_START","TIMESTAMP_END",*NATIVE_FIELDS}
        ck(rd.fieldnames is not None and mandatory.issubset(rd.fieldnames)
           and len(set(rd.fieldnames))==len(rd.fieldnames),
           "Missing seven essential FLUXMET original fields: "+site)
        for row in rd:
            n+=1;key=row["TIMESTAMP_START"]
            dt=timeparse(key)
            end=timeparse(row["TIMESTAMP_END"])
            if first is None:first=key
            last=key
            if previous is not None and dt!=previous:
                issues["NATIVE_30MIN_MISSING_OR_DUP"]+=1
                if len(samples)<18:samples.append(("CLOCK_GAP",key))
            previous=dt+timedelta(minutes=30)
            if end-dt!=timedelta(minutes=30):
                issues["TIMESTAMP_END_NOT_30MIN"]+=1
                if len(samples)<18:samples.append(("BAD_END",key))
            years[dt.year]+=1
            if dt.month==2 and dt.day==29:
                feb29+=1;continue
            noleap+=1
            values={fld:helper.num(row[fld]) for fld in NATIVE_FIELDS}
            for name,val in values.items():
                if val is None:
                    issues["MISSING_"+name]+=1
                    if len(samples)<18:samples.append(("MISSING_"+name,key))
                elif name in LIMITS:
                    lo,hi=LIMITS[name]
                    if val<lo or val>hi:
                        issues["OUTSIDE_CONSERVATIVE_"+name]+=1
                        if len(samples)<18:samples.append(("OUTSIDE_"+name,key,ffmt(val)))
                    elif name in NEG_TOL and val<0:
                        caution["SMALL_NEGATIVE_"+name]+=1
                        if len(samples)<18:samples.append(("SMALL_NEG_"+name,key,ffmt(val)))
            qc=row.get("TA_F_QC","?")
            sourceqc[qc]+=1
            t=values["TA_F"];v=values["VPD_F"];pa=values["PA_F"]
            sat=helper.sat(t)
            if sat is None or t is None or v is None or pa is None:
                continue
            if v<0 or not 65<=pa<=110:
                continue
            if v>sat:
                excess=v-sat
                if excess<=.0005:
                    caution["VPD_NATIVE_THREE_DECIMAL_ROUNDING"]+=1
                    ck((site,key) in ROUNDING,
                       "Unexpected VPD three-decimal source rounding timestamp "+site+" "+key)
                    if len(samples)<18:samples.append(("ROUNDING",key,ffmt(excess)))
                else:
                    issues["VPD_SATURATION_UNPHYSICAL"]+=1
                    if len(samples)<18:samples.append(("VPD_SATURATION",key,ffmt(excess)))
                continue
            if v<0:continue
            pa_hpa=pa*10.;actual_e=sat-v
            if actual_e<0 or actual_e>pa_hpa:
                issues["VAPOUR_PRESSURE_NOT_BETWEEN_0_AND_PSFR"]+=1
                continue
            q=EPS*actual_e/(pa_hpa-(1-EPS)*actual_e)
            if not 0<=q<.08 or not math.isfinite(q):
                issues["MODEL_QBOT_OUTSIDE_0_TO_0P08"]+=1
                if len(samples)<18:samples.append(("QBOT",key,ffmt(q)))
            else:
                qmin=q if qmin is None else min(qmin,q)
                qmax=q if qmax is None else max(qmax,q)
                if q==0:caution["DRY_ZERO_QBOT_MODEL_POLICY_REQUIRED"]+=1
            sw=values["SW_IN_F"];lw=values["LW_IN_F"];wind=values["WS_F"];pr=values["P_F"]
            # In native released source, small negative radiation/wind/rain
            # must not be silently clipped; Gate-0 logs their frequency.
            if pr is not None and pr>=0:
                wet_total_mm+=pr
                if pr>0:precip_count+=1
    ck(n>0,"Empty selected source "+site)
    expected=sum(NOLEAP_ROWS + (48 if
        (year%4==0 and (year%100!=0 or year%400==0)) else 0)
        for year in range(min(years),max(years)+1))
    if n!=expected:issues["NATIVE_FULL_YEAR_COUNT_INCONSISTENT"]+=1
    for year,count in years.items():
        expected_year=NOLEAP_ROWS+(48 if
          (year%4==0 and (year%100!=0 or year%400==0)) else 0)
        if count!=expected_year:
            issues["YEAR_NOT_FULL_30MIN_"+str(year)]+=1
            if len(samples)<18:samples.append(("YEAR_COVERAGE",year,count,expected_year))
    if feb29!=n-noleap:
        issues["NOLEAP_FEB29_EXCLUSION_MISMATCH"]+=1
    if (site=="US-Syv" and n!=438288):
        issues["SOURCE_SYV_438288_ROWS_CHANGED"]+=1
    print("SITE",site,"SOURCE_SHA_PASS",gotsha,"SOURCE_HH",n,
          "NOLEAP_HH",noleap,"LEAP_REMOVED_HH",feb29,
          "SOURCE_YEARS",f"{min(years)}-{max(years)}",
          "NUMERIC_BLOCKERS",dict(issues),
          "NONPRODUCTION_POLICIES",dict(caution),
          "TA_QC",dict(sourceqc),
          "QBOT_PREVIEW_RANGE_KG_KG",[qmin,qmax],
          "P_F_POSITIVE_HH",precip_count,
          "NONNEGATIVE_RAIN_TOTAL_MM",round(wet_total_mm,3))
    if samples:print("EVIDENCE_SAMPLES",site,samples[:18])
    return {"site":site,"SHA256":gotsha,"source_halfhours":n,
        "model_noleap_halfhours":noleap,"removed_feb29_halfhours":feb29,
        "source_years":[min(years),max(years)],
        "numeric_blockers":dict(issues),"conservative_nonproduction_policy_flags":dict(caution),
        "TA_source_QC":dict(sourceqc),"qbot_preview_range_kgkg":[qmin,qmax],
        "P_F_positive_HH":precip_count,"nonnegative_source_rain_sum_mm":wet_total_mm,
        "source_evidence_examples":samples,
        "numeric_gate_no_blockers":not bool(issues)}
def selftest(helper):
    s=helper.sat(-6.234)
    ck(abs(s-3.841976803313088)<1e-9 and .0<3.842-s<.0005,
       "Original Syv source VPD rounding exception changed")
    ck((datetime(2008,2,29,23,30)+timedelta(minutes=30))==datetime(2008,3,1),
       "Native leap-day 30min converter math failed")
    print("SYVH6 SYNTHETIC SELF-TEST PASS: 7 met source fields, noleap, VPD rounding physics")
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-dir",required=True)
    flag=parser.add_mutually_exclusive_group(required=True)
    flag.add_argument("--check",action="store_true")
    flag.add_argument("--report",action="store_true")
    z=parser.parse_args()
    helper=read_helper();selftest(helper)
    folder=Path(z.manifest_dir)
    ck(folder.is_dir() and not folder.is_symlink(),
       "Required final operator SYVH3 manifest directory missing")
    selected=helper.canonical(folder)
    ck(set(selected)==set(SITES),"Unexpected source selection roster")
    print("SOURCE PIN VERIFIED FINAL SYVH3+9 OTHER SITES 10/10")
    stats=[analyze(site,selected[site],helper) for site in SITES]
    ready=[r["site"] for r in stats if r["numeric_gate_no_blockers"]]
    blocker=[r["site"] for r in stats if not r["numeric_gate_no_blockers"]]
    all_round=sum(r["conservative_nonproduction_policy_flags"].get(
           "VPD_NATIVE_THREE_DECIMAL_ROUNDING",0) for r in stats)
    ck(all_round==3,
       "Exact 2 US-Rpf+1 US-Syv rounding events expected; check changed source")
    print("SYVH6 TEN SITE NATIVE SEVEN_MET NOLEAP GATE",
          "SOURCE_NUMERIC_READY",ready,
          "NUMERIC_BLOCKED",blocker,
          "ROUNDING_HH_NEED_MODEL_CONVERSION_POLICY",all_round)
    print("SOURCE AUXILIARY RH IS NOT A FORCE INPUT TO THIS NUMERIC GATE.")
    print("STAGE81 BATCH01 EXEMPLAR SHUM=QBOT; ORIGINAL T/VPD/PA, RADIATION, WIND, RAIN SCIENCE SOURCE AND METADATA STILL REQUIRED BEFORE MODEL RELEASE.")
    print("POST_V5_DATM_CIME_SLURM_SPINUP","NOT_APPROVED_RESEARCH_DIAGNOSTIC_ONLY")
    if z.report:
        out=Path.home()/"ameriflux_batch04_manual_review"
        out.mkdir(parents=True,exist_ok=True)
        tag=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:6]
        js=out/("Batch04_SYVH6_TEN_SOURCE_MET_GATE0_"+tag+".json")
        tab=out/("Batch04_SYVH6_TEN_SOURCE_MET_GATE0_"+tag+".tsv")
        js.write_text(json.dumps({"sites":stats,"postv5_approved":False,
           "all_site_numeric_gate_pass":len(ready)==10,
           "rounding_policy_hh":all_round,
           "unresolved_independent_tower_science_and_ZBOT":True},
           indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        with tab.open("x",encoding="utf-8",newline="") as f:
            w=csv.writer(f,delimiter="\t")
            w.writerow(["site","source_HH","noleap_HH","site_numeric_blockers_JSON",
                        "nonproduction_flags_JSON","SHA256"])
            for r in stats:
                w.writerow([r["site"],r["source_halfhours"],r["model_noleap_halfhours"],
                     json.dumps(r["numeric_blockers"],sort_keys=True),
                     json.dumps(r["conservative_nonproduction_policy_flags"],sort_keys=True),
                     r["SHA256"]])
        print("SYVH6 READONLY MET GATE REPORT",js,"SHA",helper.sha(js))
        print("SYVH6 READONLY MET GATE TSV",tab,"SHA",helper.sha(tab))
    print("SYVH6 NO SOURCE/RESEARCH MODEL DATM CASE OR SLURM WRITES")
if __name__=="__main__":main()

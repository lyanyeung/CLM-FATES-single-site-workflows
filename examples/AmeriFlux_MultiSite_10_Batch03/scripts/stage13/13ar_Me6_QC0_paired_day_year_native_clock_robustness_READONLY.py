#!/usr/bin/env python3
"""Stage13AR: original US-Me6 QC0 paired-edge day/year and native-clock robustness.
Verify signed Stage13AQ raw measured QC0 halfhour-pair report, then compare
pair-weighted, date-weighted and year-weighted 5-95% e-change ranges.
Native halfhour clock matching is not an independently verified local solar time.
No data/model/research-shadow/source/DATM/Slurm changes or approvals.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
VER="batch03-stage13ar-v1-20261029-Me6-QC0-day-year-native-clock-robustness"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
AQ=ROOT/"reports/stage13aq_Me6_QC0_30min_vapour_pairs_original_READONLY_20261029T001725Z_1a3a933d"
AQ_REC="stage13aq_READONLY_science_SHA_receipt.json"
AQ_POP="8_actual_source_QC0_paired_regime_support.csv"
AQ_DONOR="original_source_QC0_halfhour_pair_provenance.csv"
AQ_COMP="24_comparisons_actual_source_QC0_pairs_vs_three_QC2_border_hypotheses.csv"
AQ_SUM="stage13aq_source_measured_QC0_30min_edge_science_summary.json"
AQ_FLAG="NO_19HH_OR_QC2_BOUNDARY_FORCING_SCIENCE_APPROVAL"
AQ_NAMES={AQ_POP,AQ_DONOR,AQ_COMP,AQ_SUM,AQ_FLAG}
AQ_VER="batch03-stage13aq-v1-20261029-Me6-30min-QC0-pair-vapour-e-QBOT-edges"
AQ_SOURCE=HERE/"13aq_Me6_2015_QC0_measured_30min_edge_vapour_transition_READONLY.py"
AQ_GIT="ff9bc87a9bd56e1365f2b93a55edc6d2b5a71aa4"
LABELS=("STRICT_T3_DELTA1_ERA3","MODERATE_T3_DELTA2_ERA3",
        "BROAD_T5_DELTA3_ERA5","TEMP_ONLY_T5_DELTA3")
TARGET=0.367397657574
def need(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AR SOURCE SCIENCE HOLD: "+str(msg))
def must(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def blob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def quant(values):
    x=np.asarray(values,float)
    x=x[np.isfinite(x)]
    if not len(x):return {"n":0,"p05":None,"median":None,"p95":None,
                           "candidate_percentile":None,"candidate_inside_p05p95":None}
    low,mid,hi=np.percentile(x,[5,50,95])
    return {"n":int(len(x)),"p05":float(low),"median":float(mid),
            "p95":float(hi),"candidate_percentile":float(100*np.mean(x<=TARGET)),
            "candidate_inside_p05p95":bool(low<=TARGET<=hi)}
def test():
    q=quant([.1,.2,.3,.4])
    need(q["n"]==4 and q["p05"]<q["median"]<q["p95"] and
         quant([])["candidate_inside_p05p95"] is None,
         "quantile/zero evidence")
    need(len(pd.date_range("2014-12-31 23:30","2015-01-01 08:30",
                           freq="30min"))==19,"exact original event")
    print("STAGE13AR SELF-TEST PASS | measured QC0 source pair date/year/native-clock sensitivity, NO WRITES",flush=True)
def verify():
    need(blob(AQ_SOURCE)==AQ_GIT,"signed Stage13AQ original source code changed")
    receipt=json.loads(must(AQ/AQ_REC).read_text())
    need(receipt.get("site")=="US-Me6" and receipt.get("version")==AQ_VER and
         receipt.get("scientific_method_approved") is False and
         receipt.get("source_or_shadow_or_forcing_written") is False and
         set(receipt.get("outputs_SHA256",{}))==AQ_NAMES,
         "actual successful Stage13AQ signed original source inventory differs")
    for name,h in receipt["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AQ/name)==h,
             "actual Stage13AQ signed source report SHA changed "+name)
    parent=json.loads(must(AQ/AQ_SUM).read_text())
    need(parent.get("site")=="US-Me6" and
         parent.get("original_Stage13AI_site_VPD_QBOT_missing_HH")==45 and
         parent.get("original_source_19_HH_QC2_HOLD")==19 and
         parent.get("scientific_method_or_candidate_approved") is False and
         parent.get("no_source_or_forcing_or_research_shadow_written") is True,
         "prior original source science policy changed")
    pop=pd.read_csv(must(AQ/AQ_POP))
    donor=pd.read_csv(must(AQ/AQ_DONOR))
    comp=pd.read_csv(must(AQ/AQ_COMP))
    need(len(pop)==8 and len(comp)==24 and
         comp.no_QC2_source_or_model_change.eq(True).all(),
         "exact Stage13AQ original source populations/three candidates changed")
    counts=dict(zip(LABELS,(11,35,527,962)))
    for side in ("LEFT","RIGHT"):
        for label in LABELS:
            subset=donor[(donor.side==side)&(donor.match_label==label)]
            p=pop[(pop.side==side)&(pop.match_label==label)]
            n=counts[label] if side=="RIGHT" else 0
            need(len(p)==1 and len(subset)==n and
                 int(p.iloc[0].native_original_measured_QC0_paired_HH)==n,
                 "Stage13AQ actual QC0 original 8 groups unexpected count")
            if n:
                before=pd.to_datetime(subset.native_before)
                after=pd.to_datetime(subset.native_after)
                need(((after-before)==pd.Timedelta(minutes=30)).all()
                     and after.is_unique and
                     (subset.original_before_T_QC.eq(0)&
                      subset.original_after_T_QC.eq(0)&
                      subset.original_before_VPD_QC.eq(0)&
                      subset.original_after_VPD_QC.eq(0)).all()
                     and subset.original_source_or_forcing_unchanged.eq(True).all()
                     and after.dt.month.isin([12,1,2]).all()
                     and after.dt.normalize().nunique()==
                         int(p.iloc[0].source_QC0_native_dates)
                     and after.dt.year.nunique()==
                         int(p.iloc[0].source_QC0_distinct_years),
                     "source measured QC0 same original 30min pair provenance changed")
    c=comp[(comp.side=="RIGHT")&
           (comp.border_hypothesis=="exploratory_border_QC0_median_calibrated")]
    need(len(c)==4 and
         np.allclose(c.border_hypothesis_e_delta_hPa,TARGET,rtol=0,atol=1e-8),
         "right original Stage13AP calibrated border hypothesis changed")
    return donor
def review():
    donor=verify()
    rows=[];years=[];folds=[]
    for label in LABELS:
        d=donor[(donor.side=="RIGHT")&(donor.match_label==label)].copy()
        times=pd.to_datetime(d.native_after)
        d["day"]=times.dt.normalize()
        d["yr"]=times.dt.year
        d["e"]=d.original_measured_actual_e_change_hPa.astype(float)
        d["q"]=d.original_measured_QBOT_change_kgkg.astype(float)
        d["hour"]=times.dt.hour+times.dt.minute/60
        daily=d.groupby("day").agg(e=("e","median"),q=("q","median"),
                                   count=("e","size"),yr=("yr","first"),
                                   hour=("hour","median"))
        year=daily.groupby("yr").agg(e=("e","median"),q=("q","median"),
                                      days=("e","size"))
        for y,record in year.iterrows():
            years.append({"match_label":label,"source_year":int(y),
                "QC0_source_dates":int(record.days),
                "median_per_day_measured_e_change_hPa":float(record.e),
                "median_per_day_measured_QBOT_change_kgkg":float(record.q),
                "new_scientific_approval":False})
        def add(method,values,dates):
            v=quant(values)
            rows.append({"edge":"RIGHT","match_label":label,
                "independence_and_clock_screen":method,
                "source_distinct_QC0_dates":int(dates),
                "source_distinct_years":int(d.yr.nunique()),
                "QC0_samples_after_aggregation":v["n"],
                "measured_e_p05_hPa":v["p05"],
                "measured_e_median_hPa":v["median"],
                "measured_e_p95_hPa":v["p95"],
                "hypothetical_right_border_delta_e_hPa":TARGET,
                "hypothetical_delta_e_percentile":v["candidate_percentile"],
                "hypothetical_delta_e_inside_p05_p95":v["candidate_inside_p05p95"],
                "scientific_method_approved":False})
        add("native_individual_measured_QC0_pairs",d.e,len(daily))
        add("independent_calendar_day_medians",daily.e,len(daily))
        add("per_year_median_of_calendar_day_medians",year.e,len(daily))
        for tol in (1,2,4):
            picked=daily[abs(daily.hour-9)<=tol]
            add("native_clock_09_plusminus_"+str(tol)+"h_daily_medians",
                picked.e,len(picked))
        for leave in year.index:
            other=daily[daily.yr!=leave]
            stats=quant(other.e)
            folds.append({"match_label":label,
                "held_out_original_source_year":int(leave),
                "other_year_QC0_dates":int(len(other)),
                "other_source_years":int(other.yr.nunique()),
                "daily_measured_e_p05_hPa":stats["p05"],
                "daily_measured_e_p95_hPa":stats["p95"],
                "candidate_delta_e_percentile":stats["candidate_percentile"],
                "candidate_delta_e_in_p05p95":stats["candidate_inside_p05p95"],
                "no_source_or_model_approval":True})
    result=pd.DataFrame(rows);peryear=pd.DataFrame(years);loyo=pd.DataFrame(folds)
    need(len(result)==24 and len(loyo)==53 and
         peryear.source_year.nunique()==16 and
         result.scientific_method_approved.eq(False).all(),
         "expected 4 match bins x 6 independent screens and 49 leave-year-out folds")
    info={"version":VER,"site":"US-Me6","original_AQ_receipt_SHA256":sha(AQ/AQ_REC),
          "right_original_ERA_QC2_border_remains_unchanged":True,
          "left_2014_temperature_splice_no_true_QC0_pairs":True,
          "source_original_19HH_QC2_event_hold":19,
          "latest_original_Stage13AI_VPD_QBOT_missing_HH":45,
          "source_right_calibrated_hypothetical_delta_e_hPa":TARGET,
          "native_clock_09_ref_timezone_not_verified":True,
          "QC0_pairs_not_independent_when_multiple_within_a_date":True,
          "scientific_approval":False,"source_or_forcing_or_shadow_written":False,
          "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AR ORIGINAL RIGHT QC0 PAIRED e CHANGE DAY/YEAR/LOCAL-CLOCK SENSITIVITY",flush=True)
    print(result.to_string(index=False),flush=True)
    print("STAGE13AR PER-YEAR SOURCE ORIGINAL QC0 DAY-MEDIAN e/QBOT",flush=True)
    print(peryear.to_string(index=False),flush=True)
    print("STAGE13AR LEAVE-WHOLE-YEAR-OUT DAILY SOURCE ROBUSTNESS",flush=True)
    print(loyo.to_string(index=False),flush=True)
    print("STAGE13AR SCIENCE HOLD SUMMARY",json.dumps(info,indent=2),flush=True)
    return result,peryear,loyo,info
def main():
    p=argparse.ArgumentParser()
    opts=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","run"):opts.add_argument("--"+k,action="store_true")
    a=p.parse_args()
    test()
    if a.self_test:return
    result,years,folds,summary=review()
    if a.check:
        print("STAGE13AR ORIGINAL QC0 SOURCE DAY/YEAR AUDIT READONLY CHECK PASS; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13ar_Me6_right_QC0_day_year_clock_source_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    docs={"24_aggregation_and_native_clock_conditional_QC0_source_screens.csv":result,
          "53_source_year_leaveout_daily_QC0_e_percentiles.csv":folds,
          "per_year_QC0_source_date_weighted_e_QBOT.csv":years}
    for n,d in docs.items():d.to_csv(out/n,index=False,float_format="%.17g")
    summ="stage13ar_source_QC0_day_year_clock_robustness_summary.json"
    marker="NO_19HH_OR_TWO_QC2_BORDER_SCIENTIFIC_REPAIR_APPROVAL"
    (out/summ).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text("Original measured QC0 source pairs only, not direct 2015 event humidity. No scientific or model acceptance.\n")
    receipt={"version":VER,"site":"US-Me6","source_or_forcing_written":False,
             "method_approved":False,
             "outputs_SHA256":{name:sha(out/name) for name in [*docs,summ,marker]}}
    (out/"stage13ar_READONLY_science_SHA_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AR READONLY SCIENCE REPORT DIR:",out,flush=True)
    print("STAGE13AR TRUE QC0 DAY YEAR NATIVE CLOCK ROBUSTNESS COMPLETE; NO SHADOW/FORCING/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AR SCIENCE HOLD:",exc,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

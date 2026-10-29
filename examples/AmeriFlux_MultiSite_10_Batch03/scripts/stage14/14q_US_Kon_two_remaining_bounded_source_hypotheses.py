#!/usr/bin/env python3
"""US-Kon 14Q: 2 exactly bounded remaining source-humidity research hypotheses.

Input: the ACTUALLY EXECUTED signed Stage14P original 3 groups, 4 HOLD
isolated research source. Test:
 (1) 2011-10-15 07:30 original T QC0 / VPD QC1 single source centre:
     RH interpolation between immediate 07:00 and 08:00 published
     VPD QC1 endpoint estimates (NOT observed humidity QC0).
 (2) 2012-08-05 09:00–11:00 one contiguous 5 HH VPD QC1 group:
     original both-QC0 VPD+T 08:30 and 11:30 for RH interpolation;
     temperature at 09:30–11:00 original T QC1 interpolated between
     09:00 and 11:30 actual T QC0; 09:00 original T QC0 preserved.
 Every original/source QC0 immutable; other two high-uncertainty May26
 and Sep29 special humidity HOLDs left NaN. Atomic per-group gate:
 complete 30-min native source, actual QC, no earlier source edits,
 all 2 external boundaries + internal T/VPD/RH/QBOT physical jumps.
 All candidate values remain research, not independently measured tower
 humidity; original signed 14P and all historical inputs untouched.
 --check: read-only; --run: NEW independently receipted science shadow.
 """
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VER="batch03-Kon-14Q-two-bounded-remaining-low-confidence-research-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
P=R/"science_trials/US_Kon_14P_QC0_3_CONNECTED_GROUPS_4HOLD_RESEARCH_ONLY_20261029T070041Z_0ec4c927"
PF="US-Kon_280320_QC0_CONNECTED_GROUPS_RESEARCH_NOT_DATM.csv"
PR="US-Kon_14P_SHA_receipt.json"
C="time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE".split()
HOLD4={"201105261100","201109291830","201110150730","201208050900"}
HOLD2={"201105261100","201109291830"}
G=[
  dict(name="OCT15_0730_QC1_ENDPOINT_RH_LOW_CONFIDENCE",
       l="201110150700",r="201110150800",
       target=["201110150730"],t0=None,t1=None,confidence="QC1_RH_ENDPOINT_ONLY"),
  dict(name="AUG05_0900_1100_TRUE_QC0_ENDPOINT_RH",
       l="201208050830",r="201208051130",
       target=["201208050900","201208050930","201208051000",
               "201208051030","201208051100"],
       t0="201208050900",t1="201208051130",
       confidence="TRUE_TWO_QC0_RH_ENDPOINTS_WITH_QC1_T_INTERPOLATION")
]
def stop(check,message):
    if not bool(check):raise RuntimeError("US-Kon 14Q STOP: "+str(message))
def file(path):
    path=Path(path);stop(path.is_file() and not path.is_symlink(),
                             "missing protected source: "+str(path))
    return path
def sha(path):
    h=hashlib.sha256()
    with file(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def es(t):return 6.112*np.exp(17.67*float(t)/(float(t)+243.5))
def ice(t):return 6.112*np.exp(22.46*float(t)/(float(t)+272.62))
def humid(t,p,v,q):
    if not np.isfinite([t,p,v,q]).all():return None
    if not (-75<t<65 and 50000<p<110000 and 0<=v<es(t) and 0<q<.08):
        return None
    e=es(t)-v
    calc=.622*100*e/(p-.378*100*e)
    if e<=0 or not np.isclose(calc,q,rtol=1e-6,atol=1e-8):return None
    if t<0 and 100*e/ice(t)>102:return None
    return 100*e/es(t)
def qval(e,p):return .622*100*e/(p-.378*100*e)
def key(x):
    return x.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
def test():
    stop(len(HOLD4)==4 and len(HOLD2)==2 and
         sum(len(x["target"]) for x in G)==6 and
         np.isclose(qval(8,100000),.005,atol=.00002),
         "source group 1+5 original and ideal humidity regression")
    print("US-Kon Stage14Q ONEPASS TWO-CASE SCIENCE SELF-TEST PASS",flush=True)
def read():
    rec=json.loads(file(P/PR).read_text())
    stop(rec.get("version")=="batch03-Kon-14P-three-true-QC0-connected-group-research-v1-20261029"
         and rec.get("science_operator_approved") is False
         and rec.get("DATM_ready") is False
         and rec.get("output_SHA256",{}).get(PF)==sha(P/PF),
         "signed Stage14P actual completed 4 hold research source differs")
    for n,h in rec["output_SHA256"].items():
        stop(sha(P/n)==h,"Stage14P SHA receipt changed "+n)
    mf=json.loads(file(S/"exact_input_manifest.json").read_text())
    matches=[x for x in mf["sites"] if x["site"]=="US-Kon"]
    stop(len(matches)==1 and int(matches[0]["native_minutes"])==30 and
         int(matches[0]["first_year"])==2004 and
         int(matches[0]["last_year"])==2019,
         "actual original source site/year/clock not US-Kon 2004–2019")
    sc=matches[0]
    for field in ("primary","era"):
        p=file(sc[field])
        stop(sha(p)==mf["input_sha256"].get(str(p.resolve())),
             "original release companion ERA/tower source SHA changed "+field)
    parent=pd.read_csv(file(P/PF),dtype={"time":str},low_memory=False)
    stop(len(parent)==280320 and list(parent.columns)==C,
         "signed model selected 280320 native fields")
    kk=key(parent.time)
    tt=pd.to_datetime(kk,format="%Y%m%d%H%M")
    stop(kk.is_unique and tt.is_monotonic_increasing and
         kk.iat[0]=="200401010000" and kk.iat[-1]=="201912312330" and
         not bool(((tt.dt.month==2)&(tt.dt.day==29)).any()),
         "original selected NOLEAP chronological source changed")
    stop(set(kk[parent.VPD_USE.isna()])==HOLD4 and
         set(kk[parent.QBOT.isna()])==HOLD4,
         "actual Stage14P previous four science native HOLDs not intact")
    wanted={z for g in G for z in [g["l"],*g["target"],g["r"]]}
    raw=pd.read_csv(file(sc["primary"]),
       usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
       dtype={"TIMESTAMP_START":str},low_memory=False)
    stop(raw.TIMESTAMP_START.is_unique,"original native release has duplicates")
    raw=raw.loc[raw.TIMESTAMP_START.isin(wanted)].copy()
    raw.index=raw.TIMESTAMP_START
    stop(set(raw.index)==wanted,"native published raw missing two groups' source times")
    for col in ("TA_F","TA_F_QC","VPD_F","VPD_F_QC"):
        raw[col]=pd.to_numeric(raw[col],errors="coerce")
        raw[col]=raw[col].mask(raw[col]<=-9990)
    return parent,kk,tt,{z:i for i,z in enumerate(kk)},raw

def assess():
    parent,keys,times,idx,obs=read()
    new=parent.copy(deep=True)
    proposed=[];review=[];changed_v=set();changed_t=set()
    for group in G:
        name=group["name"]
        left,right=group["l"],group["r"]
        left_time=pd.to_datetime(left,format="%Y%m%d%H%M")
        right_time=pd.to_datetime(right,format="%Y%m%d%H%M")
        path=[left,*group["target"],right]
        stop(all((pd.to_datetime(b,format="%Y%m%d%H%M")-
                  pd.to_datetime(a,format="%Y%m%d%H%M"))==
                   pd.Timedelta(minutes=30) for a,b in zip(path,path[1:])),
             "native source time not contiguous 30-minute event "+name)
        for anchor in (left,right):
            r=obs.loc[anchor];i=idx[anchor]
            stop(int(r.TA_F_QC)==0 and
                 int(r.VPD_F_QC)==(1 if name.startswith("OCT15") else 0) and
                 np.isclose(float(parent.TA_USE.iat[i]),float(r.TA_F),
                      rtol=0,atol=1e-8) and
                 np.isclose(float(parent.VPD_USE.iat[i]),float(r.VPD_F),
                      rtol=0,atol=1e-8),
                 "actual source T-QC0 and required RH endpoint QC class/value "+anchor)
        x=obs.loc[left];z=obs.loc[right]
        rh0=100*(1-float(x.VPD_F)/es(x.TA_F))
        rh1=100*(1-float(z.VPD_F)/es(z.TA_F))
        stop(np.isfinite([rh0,rh1]).all() and
             0<rh0<100 and 0<rh1<100 and abs(rh0-rh1)<=30,
             "original source endpoint RH disparity or supersaturation "+name)
        temp_left,temp_right=group["t0"],group["t1"]
        if temp_left:
            stop(int(obs.loc[temp_left].TA_F_QC)==0 and
                 int(obs.loc[temp_right].TA_F_QC)==0 and
                 np.isclose(float(parent.TA_USE.iat[idx[temp_left]]),
                            float(obs.loc[temp_left].TA_F),rtol=0,atol=1e-8) and
                 np.isclose(float(parent.TA_USE.iat[idx[temp_right]]),
                            float(obs.loc[temp_right].TA_F),rtol=0,atol=1e-8),
                 "AUG05 actual independently measured temperature QC0 anchors lost")
        data={}
        for keyid in group["target"]:
            raw=obs.loc[keyid];i=idx[keyid]
            stop(int(raw.VPD_F_QC)==1,
                 "target original VPD not QC1 "+keyid)
            if keyid not in HOLD4:
                stop(np.isclose(float(parent.VPD_USE.iat[i]),float(raw.VPD_F),
                                atol=1e-6,rtol=0),
                     "historically selected VPD no longer identical original QC1 "+keyid)
            t=float(parent.TA_USE.iat[i]);orig_t=t
            if temp_left and keyid!=temp_left:
                stop(int(raw.TA_F_QC)==1 and
                     np.isclose(t,float(raw.TA_F),atol=1e-8,rtol=0),
                     "original August QC1 temperature already changed by other science "+keyid)
                fraction=(pd.to_datetime(keyid,format="%Y%m%d%H%M")-
                     pd.to_datetime(temp_left,format="%Y%m%d%H%M"))/(
                     pd.to_datetime(temp_right,format="%Y%m%d%H%M")-
                     pd.to_datetime(temp_left,format="%Y%m%d%H%M"))
                t=float(obs.loc[temp_left].TA_F)+fraction*(
                   float(obs.loc[temp_right].TA_F)-float(obs.loc[temp_left].TA_F))
            else:
                stop(int(raw.TA_F_QC)==0,"original target measured T QC0 lost "+keyid)
            w=(pd.to_datetime(keyid,format="%Y%m%d%H%M")-left_time)/(
                 right_time-left_time)
            rh=rh0+(rh1-rh0)*w
            pressure=float(parent.PSRF.iat[i])
            e=es(t)*rh/100;v=es(t)-e;q=qval(e,pressure)
            stop(humid(t,pressure,v,q) is not None,
                 "native original source proposed water/ice/QBOT invalid "+keyid)
            data[i]=(t,v,q,rh)
            proposed.append(dict(group=name,native_key=keyid,
               original_T_C=float(raw.TA_F),original_T_QC=int(raw.TA_F_QC),
               selected_prior_T_C=orig_t,proposed_T_C=t,
               original_VPD_F_hPa=float(raw.VPD_F),original_VPD_QC=int(raw.VPD_F_QC),
               selected_prior_VPD_hPa=float(parent.VPD_USE.iat[i]),
               source_left_RHwater_pct=rh0,source_right_RHwater_pct=rh1,
               source_anchor_humidity_independently_measured=(
                 group["confidence"]!="QC1_RH_ENDPOINT_ONLY"),
               candidate_RHwater_pct=rh,candidate_VPD_hPa=v,candidate_QBOT=q,
               eligible_as_measured_source_observation=False,
               production_DATM_approved=False))
        def sample(j):
            if j in data:return data[j]
            r=parent.iloc[j];temp=float(r.TA_USE)
            vap=float(r.VPD_USE);qb=float(r.QBOT)
            rh=humid(temp,float(r.PSRF),vap,qb)
            return temp,vap,qb,rh
        errs=[];worst=dict(max_dVPD_hPa=0.,max_dRH_pp=0.,max_dQBOT=0.,max_dTA_C=0.)
        for u,vk in zip(path,path[1:]):
            i,j=idx[u],idx[vk]
            ta,va,qa,rha=sample(i)
            tb,vb,qb,rhb=sample(j)
            if rha is None or rhb is None:
                errs.append("BAD_PHYSICS_"+u+"_"+vk);continue
            jumps=dict(max_dVPD_hPa=abs(vb-va),max_dRH_pp=abs(rhb-rha),
                       max_dQBOT=abs(qb-qa),max_dTA_C=abs(tb-ta))
            for n,x in jumps.items():worst[n]=max(worst[n],x)
            if (jumps["max_dVPD_hPa"]>4 or jumps["max_dRH_pp"]>20 or
                jumps["max_dQBOT"]>.003 or jumps["max_dTA_C"]>4):
                errs.append("HALF_HOUR_"+u+"_"+vk+" "+json.dumps(jumps))
        ok=not errs
        if ok:
            for i,(t,v,q,rh) in data.items():
                new.at[i,"VPD_USE"]=v
                new.at[i,"QBOT"]=q
                changed_v.add(i)
                if abs(t-float(parent.TA_USE.iat[i]))>1e-10:
                    new.at[i,"TA_USE"]=t
                    new.at[i,"TBOT"]=t+273.15
                    changed_t.add(i)
        review.append(dict(group=name,source_grade=group["confidence"],
             group_target_count=len(data),original_HOLD_count=sum(
                    keys.iat[j] in HOLD4 for j in data),
             original_both_observed_RH_QC0_at_endpoints=(
                    name.startswith("AUG05")),
             original_QC0_temperature_protected=True,
             **worst,group_NUMERIC_PASS=ok,group_fail_reasons=";".join(errs)))
        print("US-Kon Stage14Q ORIGINAL SCIENCE CASE",name,
              "PASS",ok,"max_jumps",worst,"reasons",errs,flush=True)
    for c in C:
        altered=(changed_v if c in ("VPD_USE","QBOT") else
                 changed_t if c in ("TA_USE","TBOT") else set())
        mask=np.ones(len(parent),bool)
        if altered:mask[list(altered)]=False
        stop(parent.loc[mask,c].reset_index(drop=True).equals(
                new.loc[mask,c].reset_index(drop=True)),
             "original signed source modified out-of-scope "+c)
    miss=set(keys[new.VPD_USE.isna()])
    stop(HOLD2<=miss<=HOLD4 and miss==set(keys[new.QBOT.isna()]),
         "original two hard science HOLDs incorrectly cleared")
    data={
        "version":VER,"site":"US-Kon","selected_native_HH":280320,
        "source_Stage14P_SHA256":sha(P/PF),
        "two_group_science_tests":len(G),
        "approved_numerical_research_groups":sum(g["group_NUMERIC_PASS"] for g in review),
        "original_four_holds":sorted(HOLD4),
        "remaining_source_HOLD_keys":sorted(miss),
        "remaining_original_HOLD_n":len(miss),
        "extra_finite_QC1_VPD_research_changes":len(changed_v)-(4-len(miss)),
        "extra_original_QC1_T_research_changes":len(changed_t),
        "original_site_VPD_QC0_untouched":True,
        "original_site_T_QC0_untouched":True,
        "may26_and_sep29_original_source_science_HOLD_untouched":True,
        "oct15_endpoint_source_humidity_QC1_not_independently_measured":True,
        "not_scientifically_approved_for_DATM_AD400":True,
        "original_forcing_and_Slurm_untouched":True}
    print("US-Kon Stage14Q TWO GROUP SOURCE REVIEW:",flush=True)
    print(pd.DataFrame(review).to_string(index=False),flush=True)
    print("US-Kon Stage14Q ALL SPECIFIC SOURCE QCs/NUMERIC HYPOTHESES:",flush=True)
    print(pd.DataFrame(proposed).round(5).to_string(index=False),flush=True)
    print("US-Kon Stage14Q CONCLUSION:",json.dumps(data,indent=2),flush=True)
    return new,pd.DataFrame(proposed),pd.DataFrame(review),data

def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    for kind in ("self-test","check","run"):
        a.add_argument("--"+kind,action="store_true")
    args=p.parse_args()
    test()
    if args.self_test:return
    output,rows,summary,receipt=assess()
    if args.check:
        print("US-Kon Stage14Q READONLY PREVIEW PASS; NO WRITES",flush=True)
        return
    out=R/"science_trials"/("US_Kon_14Q_two_remaining_bounded_humidity_research_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={"US-Kon_14Q_280320_original_QC0_preserved_research_NOT_DATM.csv":output,
           "US-Kon_14Q_exact_source_QC_and_two_group_candidates.csv":rows,
           "US-Kon_14Q_two_groups_all_30min_boundary_science.csv":summary}
    hashes={}
    for name,obj in files.items():
        obj.to_csv(out/name,index=False,float_format="%.17g")
        hashes[name]=sha(out/name)
    f=pd.read_csv(out/list(files)[0])
    stop(len(f)==280320 and list(f.columns)==C and
         f.VPD_USE.isna().sum()==receipt["remaining_original_HOLD_n"] and
         f.QBOT.isna().sum()==receipt["remaining_original_HOLD_n"],
         "serialized new science 280320 model research source missing inventory changed")
    (out/"US-Kon_14Q_review_summary.json").write_text(json.dumps(receipt,indent=2)+"\n")
    hashes["US-Kon_14Q_review_summary.json"]=sha(out/"US-Kon_14Q_review_summary.json")
    (out/"RESEARCH_ONLY_NOT_DATM_OR_SPINUP").write_text(
        "This is a separate low-confidence source/RH sensitivity, not observed "
        "humidity at original QC1 timestamps. May26 and Sep29 original science "
        "HOLDs are still NaN; Oct15 RH endpoints were original QC1 estimates "
        "not independent sensor measurements; Aug05 candidate T/QC1 derives "
        "from true observed QC0 anchors. No prior source or Slurm writes.\n")
    hashes["RESEARCH_ONLY_NOT_DATM_OR_SPINUP"]=sha(out/"RESEARCH_ONLY_NOT_DATM_OR_SPINUP")
    (out/"US-Kon_14Q_SHA_receipt.json").write_text(json.dumps(dict(
         version=VER,source_Stage14P_sha256=receipt["source_Stage14P_SHA256"],
         output_SHA256=hashes,operator_science_approved=False,
         DATM_ready=False,Slurm_jobs_submitted=False),indent=2)+"\n")
    print("US-Kon Stage14Q ISOLATED RESEARCH OUTPUT:",out,flush=True)
    print("US-Kon Stage14Q TWO ORIGINAL SOURCE GROUPS TESTED; MAY26/SEP29 INTACT; NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("US-Kon 14Q STOP WITHOUT ORIGINAL SOURCE WRITES:",ex,file=sys.stderr,flush=True)
        raise

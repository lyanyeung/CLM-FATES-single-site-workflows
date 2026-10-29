#!/usr/bin/env python3
"""US-MMS manually chosen source-regime repair, isolated sensitivity-only derivative.

Exactly 16 missing HR resolved. Sep-2014 47 source VPD QC1 positions are
replaced together by valid same-release companion ERA water RH at original
tower T/P; one source QC2 remains original. March-2000 six QC2 source
RH transfers are LOW CONFIDENCE due source T QC1 and ~10C ERA mismatch.
Five below-freezing Feb-2015/Jan-2019 source-ERA-negative-e gaps use
bounded RH over ice interpolated between actual selected, physically closed
two-sided source neighbours. No source files/case/Slurm are changed.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np,pandas as pd
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S=R/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
O=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
A=R/"reports/us_mms_16hour_onepass_manual_science_20261029T031440Z_b66bdf1c"
M=["200003051700","200003061600","200003061700","200003061800","200003061900","200003062000"]
C=["201502240700","201901301000","201901301100","201901301200","201901301300"]
D=["201409220700","201409220900","201409221000","201409230700","201409230800"]
H=set(M+C+D)
F="US-MMS_STAGE12G_INCOMPLETE_NOLEAP.csv"
def ck(ok,msg):
    if not bool(ok):raise RuntimeError("US-MMS ISOLATED SCIENCE STOP: "+str(msg))
def sha(p):
    p=Path(p);ck(p.is_file() and not p.is_symlink(),"source missing "+str(p))
    h=hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda:stream.read(1048576),b""):h.update(block)
    return h.hexdigest()
def ew(t):return 6.112*np.exp(17.67*np.asarray(t,float)/(np.asarray(t,float)+243.5))
def ei(t):return 6.112*np.exp(22.46*np.asarray(t,float)/(np.asarray(t,float)+272.62))
def qfun(e,p):return .622*100*e/(p-.378*100*e)
def test():
    ck(len(H)==16 and 25*365*24==219000 and
       0<ew(-20)<ew(0) and ei(-20)<ew(-20),"clock/physics unit regression")
    print("US-MMS MANUAL ONEPASS SELF-TEST PASS",flush=True)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run",action="store_true",required=True)
    args=p.parse_args()
    test()
    r=json.loads((S/"stage12g_research_only_sha_receipt.json").read_text())
    ck(r["output_sha256"][F]==sha(S/F),"selected Stage12G SHA mismatch")
    a=json.loads((A/"US_MMS_readonly_source_science_SHA_receipt.json").read_text())
    ledger=A/"US_MMS_16_missing_hour_manual_science_decisions.csv"
    ck(a["outputs_SHA256"][ledger.name]==sha(ledger),"actual Stage14B audit SHA changed")
    j=json.loads((O/"exact_input_manifest.json").read_text())
    site=next(z for z in j["sites"] if z["site"]=="US-MMS")
    ck(site["native_minutes"]==60,"original HR source changed")
    for k in ("primary","era"):
        pp=Path(site[k])
        ck(j["input_sha256"][str(pp.resolve())]==sha(pp),"original source SHA "+k)
    raw=pd.read_csv(site["primary"],usecols=["TIMESTAMP_START","TA_F_QC","VPD_F_QC"],
                    dtype={"TIMESTAMP_START":str}).set_index("TIMESTAMP_START")
    er=pd.read_csv(site["era"],usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                   dtype={"TIMESTAMP_START":str}).set_index("TIMESTAMP_START")
    old=pd.read_csv(S/F)
    ck(len(old)==219000 and list(old)==["time","TBOT","QBOT","PSRF","FSDS",
        "FLDS","WIND","PRECTmms","TA_USE","VPD_USE"],"selected full source schema")
    old.index=pd.to_datetime(old.time).strftime("%Y%m%d%H%M")
    ck(old.index.is_unique and set(old.index[old.VPD_USE.isna()])==H
        and set(old.index[old.QBOT.isna()])==H
        and not old.drop(columns=["time","VPD_USE","QBOT"]).isna().any().any(),
        "16 original held source identities changed")
    x=old.copy(deep=True)
    audit=[]
    def apply(key,v,method,details):
        ck(key not in {z["native_key"] for z in audit},"duplicate source patch")
        t=float(old.at[key,"TA_USE"]);p=float(old.at[key,"PSRF"])
        e=float(ew(t))-float(v);q=float(qfun(e,p))
        ck(np.isfinite([e,v,q,p]).all() and e>0 and 0<=v<float(ew(t)) and
           0<q<.08 and (t>=0 or e/float(ei(t))<=1.001),
           "candidate water/ice thermodynamics "+key)
        audit.append(dict(native_key=key,method=method,
          before_VPD=old.at[key,"VPD_USE"],after_VPD=v,
          before_QBOT=old.at[key,"QBOT"],after_QBOT=q,
          original_VPD_QC=raw.at[key,"VPD_F_QC"],
          original_T_QC=raw.at[key,"TA_F_QC"],e_hPa=e,
          RHwater_pct=100*e/float(ew(t)),RHice_pct=100*e/float(ei(t)),
          numerical_only_NOT_scientific_approval=True,**details))
        x.at[key,"VPD_USE"]=float(v);x.at[key,"QBOT"]=q
    def trans(key,method):
        t=float(old.at[key,"TA_USE"]);p=float(old.at[key,"PSRF"])
        ta=float(er.at[key,"TA_ERA"]);vp=float(er.at[key,"VPD_ERA"])
        frac=1-vp/float(ew(ta))
        ck(0<frac<1,"original ERA RH physically invalid "+key)
        e=float(ew(t))*frac
        apply(key,float(ew(t))-e,method,dict(
          original_RH_ERA_pct=100*frac,source_T_minus_ERA_C=t-ta))
    times=pd.date_range("2014-09-22","2014-09-23 23:00",freq="1h").strftime("%Y%m%d%H%M")
    ck(len(times)==48 and (raw.loc[times,"VPD_F_QC"]==1).sum()==47 and
       (raw.loc[times,"VPD_F_QC"]==0).sum()==0 and
       set(old.loc[times].index[old.loc[times,"VPD_USE"].isna()])==set(D),
       "2014 entire QC1 48H source scope changed")
    for key in times:
        if raw.at[key,"VPD_F_QC"]==1:
            ck(raw.at[key,"TA_F_QC"]==0,"2014 tower T no longer QC0")
            trans(key,"2014_ALL_47_VPD_QC1_RH_TRANSFER_T_QC0")
    for key in M:
        ck(raw.at[key,"TA_F_QC"]==1 and raw.at[key,"VPD_F_QC"]==2,
           "2000 fixed T QC1 VPD QC2 scope changed")
        trans(key,"2000_SIX_HOUR_ERA_RH_TRANSFER_T_QC1_HIGH_UNCERTAINTY")
    es=ew(x.TA_USE.to_numpy(float))
    ea=es-x.VPD_USE.to_numpy(float)
    qi=qfun(ea,x.PSRF.to_numpy(float))
    ri=ea/ei(x.TA_USE.to_numpy(float))
    good=np.isfinite(ri)&np.isfinite(qi)&(ea>0)&(ri>0)&(ri<=1.01)&
         (x.VPD_USE.to_numpy(float)>=0)&
         np.isclose(qi,x.QBOT.to_numpy(float),atol=1e-8,rtol=1e-5)
    pos={key:i for i,key in enumerate(x.index)}
    for group in ([C[0]],C[1:]):
        lo=pos[group[0]];hi=pos[group[-1]]
        before=[i for i in range(max(0,lo-48),lo) if good[i]]
        after=[i for i in range(hi+1,min(len(x),hi+49)) if good[i]]
        ck(bool(before and after),"no 48h two-sided valid source humidity for "+group[0])
        a1=before[-1];a2=after[0]
        day0=pd.Timestamp(x.iloc[a1].time);day1=pd.Timestamp(x.iloc[a2].time)
        ck(pd.Timedelta(0)<day1-day0<=pd.Timedelta(hours=97),
           "source interpolation spans unacceptable length")
        for key in group:
            ck(raw.at[key,"VPD_F_QC"]==2 and old.at[key,"TA_USE"]<0,
               "exact cold source QC2 hold changed")
            f=float((pd.Timestamp(old.at[key,"time"])-day0)/(day1-day0))
            rh=float(ri[a1]+f*(ri[a2]-ri[a1]))
            bounded=float(np.clip(rh,.01,.98))
            e=float(ei(old.at[key,"TA_USE"]))*bounded
            apply(key,float(ew(old.at[key,"TA_USE"]))-e,
                  "COLD_INTERPOLATED_SELECTED_ICE_RH_SENSITIVITY",
                  dict(earlier_anchor=x.index[a1],later_anchor=x.index[a2],
                       anchor_earlier_original_VPD_QC=raw.at[x.index[a1],"VPD_F_QC"],
                       anchor_later_original_VPD_QC=raw.at[x.index[a2],"VPD_F_QC"],
                       raw_ice_RH_pct=100*rh,
                       explicit_ice_RH_bounding_applied=abs(bounded-rh)>1e-12))
    changes=pd.DataFrame(audit)
    target=set(times[raw.loc[times,"VPD_F_QC"]==1])|set(M+C)
    ck(len(changes)==58 and set(changes.native_key)==target and
       int(changes.before_VPD.isna().sum())==16 and
       int(changes.before_VPD.notna().sum())==42,
       "manual repair count scope 47 + 6 + 1 + 4 drift")
    mask=~old.index.isin(target)
    for col in old:
        if col not in ("QBOT","VPD_USE"):
            ck(np.array_equal(old[col].to_numpy(),x[col].to_numpy(),equal_nan=True),
               "protected selected field altered "+col)
        else:
            ck(np.array_equal(old.loc[mask,col].to_numpy(float),
                x.loc[mask,col].to_numpy(float),equal_nan=True),
               "protected off-target humidity altered "+col)
    ck(not x.isna().any().any(),"218k+ hourly source numerical completeness failed")
    v=x.VPD_USE.to_numpy(float);t=x.TA_USE.to_numpy(float)
    e=ew(t)-v
    q=qfun(e,x.PSRF.to_numpy(float))
    ok=np.isfinite(q)&(e>0)&(v>=0)&(v<ew(t))&
       np.isclose(q,x.QBOT.to_numpy(float),atol=1e-8,rtol=1e-5)
    ck(bool(ok.all()),"entire selected 219000 numeric VPD/QBOT physics not closed")
    out=R/"science_trials"/("US_MMS_MANUAL_ISOLATED_16_FILLED_47QC1_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={"US-MMS_219000_ISOLATED_NUMERIC_SENSITIVITY_NOT_DATM.csv":x,
           "US-MMS_58_EXACT_HUMIDITY_EDITS_SCIENCE_PROVENANCE.csv":changes}
    hashes={}
    for name,frame in files.items():
        frame.to_csv(out/name,index=False)
        hashes[name]=sha(out/name)
    summary=dict(site="US-MMS",source_missing_before=16,new_missing=0,
       full_hourly_rows=219000,modified_source_QC1_2014=47,all_modified=58,
       previously_finite_changed=42,source_or_prior_shadow_modified=False,
       user_requested_exploratory_numerical_completion=True,
       observational_truth_established=False,scientific_repair_approved=False,
       postv5=False,DATM=False,AD400=False,Slurm=False)
    (out/"NOT_APPROVED_FOR_DATM_OR_SCIENTIFIC_INFERENCE").write_text(
        "This version is a bounded research-only humidity sensitivity, not independently observed tower humidity. No automatic Post-v5/DATM/Slurm authorisation.\n")
    hashes["NOT_APPROVED_FOR_DATM_OR_SCIENTIFIC_INFERENCE"]=sha(out/"NOT_APPROVED_FOR_DATM_OR_SCIENTIFIC_INFERENCE")
    (out/"US_MMS_MANUAL_16H_RESEARCH_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    hashes["US_MMS_MANUAL_16H_RESEARCH_SUMMARY.json"]=sha(out/"US_MMS_MANUAL_16H_RESEARCH_SUMMARY.json")
    (out/"US_MMS_16H_RESEARCH_SHA_RECEIPT.json").write_text(
       json.dumps(dict(summary=summary,outputs_SHA256=hashes),indent=2)+"\n")
    print("US-MMS HUMAN SCIENCE DECISION: 16/16 missing filled NUMERICALLY; 47 original Sep2014 QC1 replaced together; 58 total humidity edits",flush=True)
    print(changes[changes.native_key.isin(H)][["native_key","method","after_VPD","after_QBOT","RHwater_pct","RHice_pct"]].to_string(index=False),flush=True)
    print("US-MMS ALL 219000 HOURLY ROWS PHYSICALLY CLOSED; DO NOT CLAIM MEASURED TRUTH OR POST-V5 APPROVAL",flush=True)
    print("US-MMS NEW ISOLATED RESEARCH CANDIDATE:",out,flush=True)
    print("US-MMS MANUAL NUMERICAL GAP CLOSURE COMPLETE | ORIGINAL UNCHANGED | NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as err:
        print("US-MMS FAIL CLOSED:",err,file=sys.stderr);raise

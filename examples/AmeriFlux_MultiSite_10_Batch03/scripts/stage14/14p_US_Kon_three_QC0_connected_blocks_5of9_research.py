#!/usr/bin/env python3
"""US-Kon Stage14P: 3 original truly-QC0 endpoint event-linked research blocks.

ACTUAL Stage14O source 2011/2012 original tower+companion ERA+separate
ERA5-Land review found single-centre Stage14N 0/3 fails because immediate
original native QC1 T/VPD neighbours are inconsistent. Test three bounded,
independently physically checked science research *alternatives*:
A 2011-02-22 08:30-09:30, three missing VPD/QBOT with already approved
   original source-QC0-neighbour temperature repairs retained exactly;
B 2011-10-23 06:00-08:00, five original VPD_QC1 with measured original
   both-QC0 RH anchors 05:30 and 08:30, T QC0 all five untouched;
C 2012-02-25 10:30-11:30, three original VPD_QC1, two original T-QC1
   temperature candidate repairs at 11:00 and 11:30 bounded by actual
   original 10:30 and 12:00 T QC0; RH bounded by 10:00 and 12:00
   genuine paired original tower T+VPD QC0.
At most five of nine original VPD/QBOT hard HOLDs are filled. Four
independently protected HOLDs must remain missing. Group transaction
is atomic: if any native boundary, original source QC, pressure, ice
physics, source SHA, provenance, temperature or thermodynamic gate fails,
do not modify ANY row in that group. Other seven previous neighbour
sensitivity changes are NOT carried forward. Research-only new isolated
source + ledger; no old source, original tower, DATM or Slurm writes.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
V="batch03-Kon-14P-three-true-QC0-connected-group-research-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
K=R/"science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_20261029T044949Z_ebbfd739"
F="US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv"
COLS="time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE".split()
HOLD9={"201102220830","201102220900","201102220930","201105261100",
       "201109291830","201110150730","201110230730",
       "201202251030","201208050900"}
HOLD4={"201105261100","201109291830","201110150730","201208050900"}
GROUPS=[
    dict(name="FEB22_QC0_RH_3",
         start="201102220830",end="201102220930",
         rh_left="201102220800",rh_right="201102221000",
         t_left=None,t_right=None,
         original_t_qc=(1,0,1)),
    dict(name="OCT23_QC0_RH_5",
         start="201110230600",end="201110230800",
         rh_left="201110230530",rh_right="201110230830",
         t_left=None,t_right=None,
         original_t_qc=(0,0,0,0,0)),
    dict(name="FEB25_QC0_RH_T_3",
         start="201202251030",end="201202251130",
         rh_left="201202251000",rh_right="201202251200",
         t_left="201202251030",t_right="201202251200",
         original_t_qc=(0,1,1))
]
def ensure(ok,msg):
    if not bool(ok):raise RuntimeError("Kon Stage14P PROTECTED STOP: "+str(msg))
def safe(p):
    p=Path(p);ensure(p.is_file() and not p.is_symlink(),"missing immutable source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
def es(t):
    a=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*a/(a+243.5))
def ice(t):
    a=np.asarray(t,dtype=float)
    return 6.112*np.exp(22.46*a/(a+272.62))
def qfrom(e,pa):
    return .622*100*e/(pa-.378*100*e)
def derived(t,p,v,q):
    if not np.isfinite([t,p,v,q]).all():return None
    if not (50000<p<110000 and -75<t<65):return None
    sat=float(es(t));vap=sat-v
    if not (0<=v<sat and 0<vap and 0<q<.08):return None
    if not np.isclose(q,qfrom(vap,p),rtol=1e-6,atol=1e-8):return None
    rh=100*vap/sat
    rhice=100*vap/float(ice(t)) if t<0 else np.nan
    if t<0 and rhice>102:return None
    return rh
def timekey(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
def selftest():
    ensure(len(HOLD9)==9 and len(HOLD4)==4 and
           sum(len(pd.date_range(pd.to_datetime(g["start"],format="%Y%m%d%H%M"),
                                 pd.to_datetime(g["end"],format="%Y%m%d%H%M"),
                                 freq="30min")) for g in GROUPS)==11 and
           np.isclose(qfrom(8,100000),.005,atol=.00002),
           "three-source group interval/humidity synthetic test")
    print("US-Kon 14P THREE ORIGINAL-QC0 CONNECTED SCIENCE SELF-TEST PASS",flush=True)
def inputs():
    krec=json.loads(safe(K/"US_Kon_68_9_SHA_receipt.json").read_text())
    ensure(krec.get("version")=="batch03-US-Kon-68ERA-RH-research-9HOLD-v1-20261029" and
           krec.get("DATM_ready") is False and
           krec.get("output_SHA256",{}).get(F)==sha(K/F),
           "actual Stage14K exact low-confidence source/input SHA changed")
    m=json.loads(safe(S/"exact_input_manifest.json").read_text())
    sites=[z for z in m["sites"] if z["site"]=="US-Kon"]
    ensure(len(sites)==1 and
           int(sites[0]["native_minutes"])==30 and
           int(sites[0]["first_year"])==2004 and
           int(sites[0]["last_year"])==2019,
           "original Kon release clock source changed")
    spec=sites[0]
    for field in ("primary","era"):
        f=safe(spec[field])
        ensure(m["input_sha256"].get(str(f.resolve()))==sha(f),
               "original published source SHA changed "+field)
    k=pd.read_csv(safe(K/F),dtype={"time":str},low_memory=False)
    ensure(len(k)==280320 and list(k.columns)==COLS,
           "actual original model NOLEAP source schema changed")
    keys=timekey(k.time)
    dt=pd.to_datetime(keys,format="%Y%m%d%H%M",errors="raise")
    ensure(keys.is_unique and dt.is_monotonic_increasing and
           keys.iat[0]=="200401010000" and keys.iat[-1]=="201912312330" and
           not bool(((dt.dt.month==2)&(dt.dt.day==29)).any()),
           "signed original selected 2004–2019 native clock changed")
    ensure(set(keys[k.VPD_USE.isna()])==HOLD9 and
           set(keys[k.QBOT.isna()])==HOLD9,
           "original nine HOLDs changed")
    positions={kk:i for i,kk in enumerate(keys)}
    needed=set()
    for g in GROUPS:
        needed.update(pd.date_range(pd.to_datetime(g["rh_left"],format="%Y%m%d%H%M"),
                                    pd.to_datetime(g["rh_right"],format="%Y%m%d%H%M"),
                                    freq="30min").strftime("%Y%m%d%H%M"))
    cols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    raw=pd.read_csv(safe(spec["primary"]),usecols=cols,dtype={"TIMESTAMP_START":str},low_memory=False)
    ensure(raw.TIMESTAMP_START.is_unique,"original source release has repeated HH")
    raw=raw.loc[raw.TIMESTAMP_START.isin(needed)].copy()
    raw.index=raw.TIMESTAMP_START
    ensure(set(raw.index)==needed,"an original source QC HH missing in 3 groups")
    for c in cols[1:]:
        raw[c]=pd.to_numeric(raw[c],errors="coerce").mask(lambda x:x<=-9990)
    return k,keys,dt,positions,raw

def review():
    base,keys,dt,pos,raw=inputs()
    new=base.copy(deep=True)
    ledger=[]
    groups=[]
    touched_v=set()
    touched_t=set()
    for g in GROUPS:
        title=g["name"]
        ts=pd.date_range(pd.to_datetime(g["start"],format="%Y%m%d%H%M"),
                         pd.to_datetime(g["end"],format="%Y%m%d%H%M"),freq="30min")
        slots=ts.strftime("%Y%m%d%H%M").tolist()
        l=g["rh_left"];r=g["rh_right"]
        a=raw.loc[l];z=raw.loc[r]
        ensure(int(a.TA_F_QC)==0 and int(a.VPD_F_QC)==0 and
               int(z.TA_F_QC)==0 and int(z.VPD_F_QC)==0,
               title+": both ORIGINAL independently observed temperature/VPD QC0 RH anchors missing")
        ensure(np.isclose(float(base.TA_USE.iat[pos[l]]),float(a.TA_F),atol=1e-8,rtol=0) and
               np.isclose(float(base.TA_USE.iat[pos[r]]),float(z.TA_F),atol=1e-8,rtol=0) and
               np.isclose(float(base.VPD_USE.iat[pos[l]]),float(a.VPD_F),atol=1e-8,rtol=0) and
               np.isclose(float(base.VPD_USE.iat[pos[r]]),float(z.VPD_F),atol=1e-8,rtol=0),
               title+": selected source QC0 RH anchor values altered")
        rl=100*(1-float(a.VPD_F)/float(es(a.TA_F)))
        rr=100*(1-float(z.VPD_F)/float(es(z.TA_F)))
        ensure(0<rl<100 and 0<rr<100 and abs(rl-rr)<=30,
               title+": actual measured donor RH too different/unphysical")
        first=pd.to_datetime(l,format="%Y%m%d%H%M")
        last=pd.to_datetime(r,format="%Y%m%d%H%M")
        proposed={}
        blocks=[]
        for n,key in enumerate(slots):
            i=pos[key]
            original=raw.loc[key]
            ensure(int(original.VPD_F_QC)==1 and
                   int(original.TA_F_QC)==g["original_t_qc"][n],
                   title+": target source original QC1 VPD / temperature identity changed "+key)
            if key not in HOLD9:
                ensure(np.isclose(float(base.VPD_USE.iat[i]),float(original.VPD_F),
                                  rtol=0,atol=1e-6),
                       title+": previous selected finite VPD was already independently edited "+key)
            temp=float(base.TA_USE.iat[i])
            if g["t_left"] and original.TA_F_QC==1:
                tl=g["t_left"];tr=g["t_right"]
                ensure(int(raw.loc[tl].TA_F_QC)==0 and int(raw.loc[tr].TA_F_QC)==0,
                       title+": bounded original temperature QC0 anchors missing")
                t0=pd.to_datetime(tl,format="%Y%m%d%H%M")
                t1=pd.to_datetime(tr,format="%Y%m%d%H%M")
                factor=(pd.to_datetime(key,format="%Y%m%d%H%M")-t0)/(t1-t0)
                temp=float(raw.loc[tl].TA_F)+(float(raw.loc[tr].TA_F)-float(raw.loc[tl].TA_F))*factor
                ensure(np.isclose(float(base.TA_USE.iat[i]),float(original.TA_F),
                                  rtol=0,atol=1e-6),
                       title+": original QC1 source T previously changed; protect it")
            if title=="FEB22_QC0_RH_3" and int(original.TA_F_QC)==1:
                ensure(abs(float(base.TA_USE.iat[i])-temp)<1e-12 and
                       abs(temp-float(original.TA_F))>=5,
                       title+": historical already-approved T correction missing")
            fraction=(pd.to_datetime(key,format="%Y%m%d%H%M")-first)/(last-first)
            rh=rl+(rr-rl)*fraction
            e=float(es(temp))*rh/100
            v=float(es(temp))-e
            q=float(qfrom(e,float(base.PSRF.iat[i])))
            require_rh=derived(temp,float(base.PSRF.iat[i]),v,q)
            ensure(require_rh is not None and abs(require_rh-rh)<=1e-7,
                   title+": candidate water/ice/QBOT inconsistent")
            proposed[i]=(temp,v,q,rh)
            blocks.append(dict(group=title,native_key=key,
                original_tower_T_C=float(original.TA_F),
                original_tower_T_QC=int(original.TA_F_QC),
                original_source_VPD_hPa=float(original.VPD_F),
                original_source_VPD_QC=int(original.VPD_F_QC),
                original_selected_T_C=float(base.TA_USE.iat[i]),
                proposed_T_C=temp,
                original_selected_VPD_hPa=float(base.VPD_USE.iat[i]),
                measured_left_QC0_RH_pct=rl,
                measured_right_QC0_RH_pct=rr,
                proposed_RHwater_pct=rh,
                proposed_VPD_hPa=v,
                proposed_QBOT_kgkg=q,
                source_original_QC0_values_preserved=True,
                independently_measured_target_RH=False))
        # Every ORIGINAL adjacent 30min source link from left measured QC0
        # through all candidate HH and right measured QC0 must pass *as a group*.
        path=[l]+slots+[r]
        failures=[]
        worst={"max_VPD_hPa":0.0,"max_RH_pp":0.0,"max_QBOT_kgkg":0.0,"max_T_C":0.0}
        for ka,kb in zip(path,path[1:]):
            ia=pos[ka];ib=pos[kb]
            ensure(dt.iat[ib]-dt.iat[ia]==pd.Timedelta(minutes=30),
                   title+": selected time not contiguous 30min")
            def rowval(i):
                if i in proposed:return proposed[i]
                t=float(base.TA_USE.iat[i])
                v=float(base.VPD_USE.iat[i]);q=float(base.QBOT.iat[i])
                rh=derived(t,float(base.PSRF.iat[i]),v,q)
                return t,v,q,rh
            ta,va,qa,rha=rowval(ia)
            tb,vb,qb,rhb=rowval(ib)
            if rha is None or rhb is None:
                failures.append("ENDPOINT_WATER_OR_ICE_NOT_CLOSED_"+ka+"_"+kb)
                continue
            jumps={"max_VPD_hPa":abs(vb-va),"max_RH_pp":abs(rhb-rha),
                   "max_QBOT_kgkg":abs(qb-qa),"max_T_C":abs(tb-ta)}
            for label,value in jumps.items():worst[label]=max(value,worst[label])
            if jumps["max_VPD_hPa"]>4 or jumps["max_RH_pp"]>20 or jumps["max_QBOT_kgkg"]>.003 or jumps["max_T_C"]>4:
                failures.append("BOUNDARY_"+ka+"_"+kb+"_"+str(jumps))
        accepted=(len(failures)==0)
        if accepted:
            for i,(tt,vv,qq,rrh) in proposed.items():
                new.at[i,"VPD_USE"]=vv
                new.at[i,"QBOT"]=qq
                touched_v.add(i)
                if abs(tt-float(base.TA_USE.iat[i]))>1e-10:
                    new.at[i,"TA_USE"]=tt
                    new.at[i,"TBOT"]=tt+273.15
                    touched_t.add(i)
        for row in blocks:
            row["group_numerical_PASS"]=accepted
            row["group_error"]=";".join(failures)
            row["Postv5_DATM_AD400_approved"]=False
            ledger.append(row)
        groups.append(dict(group=title,
            targets=len(slots),orig_nine_missing_to_fill=sum(x in HOLD9 for x in slots),
            source_true_QC0_left=l,source_true_QC0_right=r,
            left_RH_pct=rl,right_RH_pct=rr,
            numerical_group_PASS=accepted,
            failures=";".join(failures),
            **worst))
        print("US-Kon Stage14P SOURCE GROUP",title,"NUMERIC_PASS",accepted,
              "source HH",len(slots),"max jumps",worst,
              "reasons",failures,flush=True)
    # Exactly original science fields outside the candidate group untouched.
    for col in COLS:
        changed=touched_v if col in ("VPD_USE","QBOT") else touched_t if col in ("TA_USE","TBOT") else set()
        mask=np.ones(len(base),bool)
        if changed:mask[list(changed)]=False
        ensure(base.loc[mask,col].reset_index(drop=True).equals(
               new.loc[mask,col].reset_index(drop=True)),
               "outside-source event modification to "+col)
    missing=set(keys[new.VPD_USE.isna()])
    ensure(missing==set(keys[new.QBOT.isna()]) and HOLD4<=missing and
           missing<=HOLD9,"source hard HOLD accounting violated")
    summary=dict(version=V,site="US-Kon",
        original_selected_native_HH=280320,
        parent_Stage14K_SHA256=sha(K/F),
        source_original_FLUXMET_manifest_SHA256=sha(S/"exact_input_manifest.json"),
        original_nine_missing=9,
        group_science_tests=len(GROUPS),
        numerical_PASS_groups=sum(x["numerical_group_PASS"] for x in groups),
        tested_QC1_VPD_native_hh=11,
        newly_filled_original_HOLD_n=9-len(missing),
        protected_original_four_HOLD=sorted(HOLD4),
        remaining_original_scientific_HOLD_n=len(missing),
        selected_additional_finite_original_QC1_VPD_modifications=len(touched_v)-(9-len(missing)),
        selected_additional_original_QC1_temperature_modifications=len(touched_t),
        source_only_research_trial_not_independent_target_measured_RH=True,
        original_QC0_temperature_and_VPD_immutable=True,
        no_original_or_model_writes=True,
        Postv5_DATM_AD400_Slurm_authorized=False)
    print("\nUS-Kon Stage14P EXACT THREE CONNECTED ORIGINAL-QC0 RH DECISIONS",flush=True)
    print(pd.DataFrame(groups).to_string(index=False),flush=True)
    print("\nUS-Kon Stage14P ALL 11 SCIENTIFIC ORIGINAL SOURCE ROWS",flush=True)
    print(pd.DataFrame(ledger).round(5).to_string(index=False),flush=True)
    print("\nUS-Kon Stage14P SOURCE SUMMARY",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("US-Kon Stage14P THREE SOURCE GROUPS CHECKED; FOUR ORIGINAL SPECIAL SCIENCE HOLDS UNTOUCHED; NO SLURM",flush=True)
    return new,pd.DataFrame(ledger),pd.DataFrame(groups),summary
def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):group.add_argument("--"+mode,action="store_true")
    a=parser.parse_args()
    selftest()
    if a.self_test:return
    trial,detail,groups,summary=review()
    if a.check:
        print("US-Kon Stage14P READONLY PREVIEW DONE; NO OUTPUT WRITES",flush=True)
        return
    out=R/"science_trials"/("US_Kon_14P_QC0_3_CONNECTED_GROUPS_4HOLD_RESEARCH_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={}
    files={
      "US-Kon_280320_QC0_CONNECTED_GROUPS_RESEARCH_NOT_DATM.csv":trial,
      "US-Kon_14P_exact_11_original_QC1_source_science_candidates.csv":detail,
      "US-Kon_14P_three_connected_groups_two_boundary_results.csv":groups
    }
    for name,frame in files.items():
        frame.to_csv(out/name,index=False,float_format="%.17g")
        outputs[name]=sha(out/name)
    reread=pd.read_csv(out/list(files)[0])
    ensure(len(reread)==280320 and list(reread.columns)==COLS and
           reread.VPD_USE.isna().sum()==summary["remaining_original_scientific_HOLD_n"] and
           reread.QBOT.isna().sum()==summary["remaining_original_scientific_HOLD_n"],
           "saved separate candidate source changed missing masks")
    (out/"US-Kon_14P_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    outputs["US-Kon_14P_summary.json"]=sha(out/"US-Kon_14P_summary.json")
    (out/"NO_APPROVAL_DATM_AD400").write_text(
      "Original QC0 temperature/VPD and historical Stage14K inputs unchanged. "
      "New candidate is an interpolation between truly original paired tower QC0 "
      "observations over three exact connected QC1 source episodes, NOT an "
      "independently measured RH source at the candidate timestamps. "
      "At least 4 science-held humidity sources remain missing. "
      "DO NOT use as production DATM or AD400 or Slurm.\n")
    outputs["NO_APPROVAL_DATM_AD400"]=sha(out/"NO_APPROVAL_DATM_AD400")
    (out/"US-Kon_14P_SHA_receipt.json").write_text(json.dumps(dict(
         version=V,source_Stage14K_SHA256=summary["parent_Stage14K_SHA256"],
         output_SHA256=outputs,science_operator_approved=False,
         DATM_ready=False,Slurm_jobs_submitted=False),indent=2)+"\n")
    print("US-Kon Stage14P ISOLATED RESEARCH OUTPUT:",out,flush=True)
    print("US-Kon Stage14P GROUP-CONNECTED RESEARCH SOURCE GENERATED; EXACT ORIGINAL QC0 PRESERVED; NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as err:
        print("US-Kon Stage14P FAIL CLOSED:",err,file=sys.stderr,flush=True)
        raise

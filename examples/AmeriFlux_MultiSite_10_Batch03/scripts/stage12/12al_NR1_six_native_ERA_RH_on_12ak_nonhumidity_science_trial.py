#!/usr/bin/env python3
"""Stage12al: close six contiguous 2022-09-10 US-NR1 VPD/QBOT gaps by
source-native FLUXNET paired ERA-RH, at three previously user-approved
interpolated TA_USE + three measured QC0 TA_USE.

Base: SHA-sealed Stage12ak research-only two-site corrected nonhumidity trial,
so 7 nonhumidity bad HH / 8 fields are already corrected in an INCOMPLETE
science-only candidate (not individually approved for production).
The SIX ERA-RH changes are also a RESEARCH-ONLY candidate, NOT operator-
approved source adoption or a Post-v5/DATM/spinup release.

--self-test: synthetic, no reads/writes.
--check: strict signed inputs, six exact source-native VPD/QBOT physics, 
         05:30--09:00 boundaries, off-target immutability, NO file writes.
--trial: same + one INCOMPLETE isolated NR1 full NOLEAP derived CSV and
         SHA-sealed six-row source-provenance and seven VPD-edge evidence.
No modification to original G/AF/AK, timestamps, T, P, PFT, or other sites.
"""
import argparse, hashlib, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VERSION="batch03-stage12al-v1-20261026-NR1-six-ERA-RH-research-only"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AK=ROOT/"science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AF=ROOT/"science_trials/stage12af_NR1_20220910_user_approved_three_T_only_20261026T013349Z_34ff1cda"
S=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
AK_FILE="US-NR1_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
AF_FILE="US-NR1_STAGE12AF_USER_APPROVED_T_ONLY_INCOMPLETE_NOLEAP.csv"
AF_ERA="six_unapproved_same_native_ERA_RH_humidity_candidates.csv"
TARGETS=("202209100600","202209100630","202209100700",
         "202209100730","202209100800","202209100830")
CORRECTED=("202209100630","202209100730","202209100800")
FLANKS=("202209100530","202209100900")
EXPECTED_VPD=(1.811838,1.873343,1.936537,1.912989,1.890739,1.853710)
COLUMNS=("time","TA_USE","TBOT","PSRF","VPD_USE","QBOT")
def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing/symlink original signed source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def key(series):
    return series.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def sat(c):
    v=np.asarray(c,dtype=float)
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        return 6.112*np.exp(17.67*v/(v+243.5))
def qbot(t,p,v):
    ea=(float(sat(t))-float(v))*100.
    return .622*ea/(float(p)-.378*ea)
def selftest():
    assert len(TARGETS)==6 and len(set(TARGETS))==6
    assert len(CORRECTED)==3 and set(CORRECTED)<set(TARGETS)
    assert all((pd.to_datetime(TARGETS[i+1],format="%Y%m%d%H%M")-
               pd.to_datetime(TARGETS[i],format="%Y%m%d%H%M")).total_seconds()==1800 for i in range(5))
    assert 0<qbot(1.241,70000,1.873343)<.08
    assert max(abs(EXPECTED_VPD[i+1]-EXPECTED_VPD[i]) for i in range(5))<4
    print("STAGE12AL SELF-TEST PASS: exact 6 original-native RH candidates, 7 local edges, no writes",flush=True)
def original_sources():
    ar=json.loads(safe(AK/"stage12ak_research_proposal_SHA_receipt.json").read_text())
    fr=json.loads(safe(AF/"stage12af_three_temperature_SHA_receipt.json").read_text())
    if not(ar.get("unique_native_rows")==7 and ar.get("original_variable_fields")==8
       and ar.get("science_user_approved_to_production") is False
       and ar.get("post_v5_approved") is False
       and ar.get("DATM_ready") is False and ar.get("spinup_authorized") is False
       and ar.get("output_SHA256",{}).get(AK_FILE)==sha(AK/AK_FILE)
       and fr.get("three_T_interpolation_operator_approved") is True
       and fr.get("six_ERA_RH_humidity_proposal_APPROVED") is False
       and fr.get("Postv5_approved")==0
       and fr.get("output_SHA256",{}).get(AF_FILE)==sha(AF/AF_FILE)
       and fr.get("output_SHA256",{}).get(AF_ERA)==sha(AF/AF_ERA)):
        raise ValueError("Stage12ak / Stage12af signed research source chain changed")
    m=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next(x for x in m["sites"] if x["site"]=="US-NR1")
    pins={str(Path(name).resolve()):v for name,v in m["input_sha256"].items()}
    for kind in ("primary","era"):
        p=safe(spec[kind])
        if sha(p)!=pins.get(str(p.resolve())):
            raise ValueError("Stage07 published tower/companion ERA native source SHA changed "+kind)
    return spec
def audit():
    spec=original_sources()
    base=pd.read_csv(safe(AK/AK_FILE),dtype={"time":str},low_memory=False)
    af=pd.read_csv(safe(AF/AF_FILE),dtype={"time":str},low_memory=False)
    if not set(COLUMNS)<=set(base) or list(base.columns)!=list(af.columns):
        raise ValueError("Stage12ak site CSV does not match user-approved Stage12af source schema")
    if len(base)!=490560 or len(af)!=len(base) or not af.time.equals(base.time):
        raise ValueError("Approved source-native timestamps/NOLEAP grid changed")
    tkey=key(base.time)
    if tkey.duplicated().any() or not set(TARGETS+FLANKS)<=set(tkey):
        raise ValueError("Exact six + neighboring native timeline missing")
    ix={str(v):i for i,v in enumerate(tkey)}
    for col in base:
        if col not in ("PSRF","FLDS") and not af[col].equals(base[col]):
            raise ValueError("Existing Stage12ak nonhumidity proposal altered approved temperature or humidity "+col)
    for k in TARGETS+FLANKS:
        j=ix[k]
        if not np.isclose(float(base.TA_USE.iat[j]),float(af.TA_USE.iat[j]),atol=1e-9,rtol=0):
            raise ValueError("Previously operator-approved target temperature changed "+k)
        if not np.isclose(float(base.TBOT.iat[j]),float(base.TA_USE.iat[j])+273.15,atol=1e-9,rtol=0):
            raise ValueError("TBOT and site TA_USE physically inconsistent "+k)
    orig=pd.read_csv(safe(spec["primary"]),
                     usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
                     dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(safe(spec["era"]),
                    usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    orig=orig.loc[orig.TIMESTAMP_START.isin(TARGETS)].copy()
    era=era.loc[era.TIMESTAMP_START.isin(TARGETS)].copy()
    if (len(orig)!=6 or len(era)!=6 or
        orig.TIMESTAMP_START.duplicated().any() or
        era.TIMESTAMP_START.duplicated().any()):
        raise ValueError("Original signed six exact native source rows missing/duplicate")
    evidence=orig.merge(era,on="TIMESTAMP_START",validate="one_to_one").set_index("TIMESTAMP_START")
    earlier=pd.read_csv(safe(AF/AF_ERA),dtype={"native_key":str},low_memory=False)
    if len(earlier)!=6 or set(earlier.native_key)!=set(TARGETS):
        raise ValueError("Stage12af six prior source-native humidity reference changed")
    earlier.set_index("native_key",inplace=True)
    selected=base.copy(deep=True)
    patches=[]
    for n,k in enumerate(TARGETS):
        j=ix[k];o=evidence.loc[k]
        if not(pd.isna(base.VPD_USE.iat[j]) and pd.isna(base.QBOT.iat[j])):
            raise ValueError("Unapproved existing finite source humidity at target "+k)
        source_t=float(o.TA_F);source_qc=int(o.TA_F_QC);t=float(base.TA_USE.iat[j])
        if k in CORRECTED:
            if source_qc!=1 or abs(source_t-t)<5:
                raise ValueError("One of three formerly approved anomalous QC1 air temperatures changed "+k)
        elif source_qc!=0 or not np.isclose(source_t,t,atol=1e-9,rtol=0):
            raise ValueError("One of three retained measured QC0 temperatures changed "+k)
        tera=float(o.TA_ERA)
        vera=float(o.VPD_ERA)
        r=1-vera/float(sat(tera))
        v=float(sat(t))*(1-r)
        p=float(base.PSRF.iat[j])
        q=qbot(t,p,v)
        if not(0<r<1 and 0<=v<float(sat(t)) and 0<q<.08
               and 50000<p<110000 and abs(t-tera)<5
               and np.isclose(v,EXPECTED_VPD[n],atol=1.1e-6,rtol=0)
               and np.isclose(v,float(earlier.loc[k,"hypothetical_unapproved_ERA_RH_VPD_hPa"]),atol=1e-9,rtol=0)
               and np.isclose(q,float(earlier.loc[k,"hypothetical_unapproved_ERA_RH_QBOT_kgkg"]),atol=1e-9,rtol=0)):
            raise ValueError("Six exact independent source RH/VPD/QBOT physics not reproduced "+k)
        selected.loc[j,"VPD_USE"]=v
        selected.loc[j,"QBOT"]=q
        patches.append({
          "site":"US-NR1","native_key":k,
          "source_tower_TA_F_C":source_t,
          "source_tower_TA_F_QC":source_qc,
          "retained_or_user_approved_TA_USE_C":t,
          "original_paired_TA_ERA_C":tera,
          "original_paired_VPD_ERA_hPa":vera,
          "paired_native_source_ERA_RH_pct":100*r,
          "numerical_research_candidate_VPD_hPa":v,
          "numerical_research_candidate_QBOT_kgkg":q,
          "retained_PSRF_Pa":p,
          "original_vpd_source_QC":int(o.VPD_F_QC),
          "operator_humidity_source_adoption_APPROVED":False
        })
    mask=tkey.isin(TARGETS).to_numpy(dtype=bool)
    for col in base.columns:
        if col not in ("VPD_USE","QBOT"):
            if not base[col].equals(selected[col]):
                raise ValueError("Off-target site field changed "+col)
        elif not np.array_equal(
                base.loc[~mask,col].to_numpy(dtype=float),
                selected.loc[~mask,col].to_numpy(dtype=float),equal_nan=True):
            raise ValueError("Off-target humidity or existing science holds modified "+col)
    edges=[]
    checks=(FLANKS[0],*TARGETS,FLANKS[1])
    for first,second in zip(checks[:-1],checks[1:]):
        fi,si=ix[first],ix[second]
        olda=base.VPD_USE.iat[fi];oldb=base.VPD_USE.iat[si]
        currenta=float(selected.VPD_USE.iat[fi])
        currentb=float(selected.VPD_USE.iat[si])
        d=abs(currentb-currenta)
        if not(np.isfinite([currenta,currentb,d]).all() and d<=4.0):
            raise ValueError("New 05:30–09:00 halfhour ERA-RH bridge fails VPD 4hPa continuity guard "+first+"/"+second)
        edges.append({"native_key_left":first,"native_key_right":second,
                      "original_left_VPD_hPa":olda,"original_right_VPD_hPa":oldb,
                      "trial_left_VPD_hPa":currenta,"trial_right_VPD_hPa":currentb,
                      "trial_absolute_jump_hPa":d,
                      "scientific_source_adoption_approved":False})
    if len(edges)!=7 or not (selected.VPD_USE.isna().sum()==234 and selected.QBOT.isna().sum()==234):
        raise ValueError("Expected 240->234 exact selected NR1 native VPD/QBOT gaps not achieved")
    met=("TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE")
    if int(selected[list(met)].isna().any(axis=1).sum())!=0:
        raise ValueError("Prior Stage12ak 7 nonhumidity source gap candidate unexpectedly lost")
    return selected,pd.DataFrame(patches),pd.DataFrame(edges)
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","trial"):g.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    print("STAGE12AL NR1 SIX PAIRED ORIGINAL-NATIVE ERA-RH SCIENCE CANDIDATES | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    selected,patches,edges=audit()
    print("\n===== SIX EXACT NATIVE 2022 NR1 SOURCE-PROVENANCE HUMIDITY PATCH CANDIDATES =====",flush=True)
    print(patches.round(9).to_string(index=False),flush=True)
    print("\n===== EXACT SEVEN 30-MINUTE VPD EDGES 05:30--09:00 =====",flush=True)
    print(edges.round(9).to_string(index=False),flush=True)
    print("STAGE12AL RESULT: NR1 VPD/QBOT 240->234 missing in research-only candidate; Kon Stage12ak candidate still 389; six-site total 3788->3782 hypothetical, NOT approved or DATM-ready.",flush=True)
    if args.check:
        print("STAGE12AL CHECK ONLY: ZERO SOURCE / REPORT / MODEL WRITES.",flush=True)
        return
    output=ROOT/"science_trials"/("stage12al_NR1_20220910_six_original_native_ERA_RH_RESEARCH_ONLY_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    files={
       "US-NR1_STAGE12AL_NONHUMIDITY_PLUS_6_ERA_RH_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv":selected,
       "six_original_source_native_ERA_RH_candidate_values_and_QC.csv":patches,
       "seven_exact_adjacent_native_30min_VPD_edges.csv":edges}
    for name,df in files.items():df.to_csv(output/name,index=False)
    marker="RESEARCH_ONLY_PENDING_OPERATOR_APPROVAL_NOT_DATM_READY"
    (output/marker).write_text(
        "Original 3 NR1 temperature edits were operator-approved in Stage12af. "
        "Original Stage12ak 7 native time/8 nonhumidity edits and new Stage12al "
        "six source-native companion ERA-RH replacements are numerical proposals "
        "ONLY, pending explicit science/source approval. No original or earlier "
        "successor modified. More historic humidity, physics and time holds remain. "
        "Do NOT use for Post-v5 / DATM / CLM-FATES spinup.\n")
    rec={
       "version":VERSION,
       "input_Stage12ak_receipt_sha256":sha(AK/"stage12ak_research_proposal_SHA_receipt.json"),
       "input_Stage12af_receipt_sha256":sha(AF/"stage12af_three_temperature_SHA_receipt.json"),
       "six_contiguous_original_source_ERA_RH_humidity_candidates":6,
       "nine_station_current_noleap_humidity_missing_if_selected":3782,
       "NR1_old_VPD_missing":240,"NR1_research_only_new_VPD_missing":234,
       "old_original_approved_temperature_retained":True,
       "nonhumidity_7HH_8field_repair_user_approved":False,
       "ERA_RH_six_humidity_replacement_user_approved":False,
       "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
       "output_SHA256":{name:sha(output/name) for name in [*files,marker]}
    }
    (output/"stage12al_NR1_six_ERA_RH_science_only_SHA_receipt.json").write_text(
       json.dumps(rec,indent=2)+"\n")
    print("STAGE12AL NR1 SIX SOURCE-NATIVE HUMIDITY RESEARCH TRIAL DIR:",output,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as err:
        print("STAGE12AL STOP:",err,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

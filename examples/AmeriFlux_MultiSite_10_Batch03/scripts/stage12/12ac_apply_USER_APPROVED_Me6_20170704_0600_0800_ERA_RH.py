#!/usr/bin/env python3
"""Stage12ac USER-APPROVED targeted humidity correction: US-Me6, 2017-07-04,
06:00 through 08:00 INCLUSIVE: exactly five native half-hours.

Approved by the operator 2026-10-25: directly adopt original-native paired
ERA-RH at unchanged measured tower TA_F and signed Stage12g PSRF. The
07:00->07:30 VPD jump 4.190815 hPa is an explicitly LIMITED USER APPROVED
4hPa-screen exception for this single adjacent pair only. This does not
relax any other 4hPa criterion. No additional candidate experiments.

Creates an isolated corrected full US-Me6 Stage12g NOLEAP derivative with
both VPD_USE and QBOT changed only for the five designated timestamps.
Leave original FLUXMET, S07, Stage12g files, ledgers, 86 science events and
233 old science holds unchanged. The 07:00 and 07:30 G missing values are
explicitly released ONLY in this separate user-approved derivative.
OTHER sites, source QC, T/P/clock, meteorology and PFT remain untouched.

--self-test: synthetic maths; NO reads and NO writes
--check: verify upstream source/report SHA, construct final targeted repair
         in memory; ZERO WRITES
--apply: same checks, then write only a NEW independent approved derivative
         plus SHA provenance and per-record before/after; NO Slurm, DATM,
         Post-v5 or spinup. Entire Batch03 is still NOT model-ready.
"""
import argparse, hashlib, json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION="batch03-stage12ac-v1-20261025-operator-approved-five-HH-ERA-RH"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
AA=ROOT/"reports/stage12aa_20170704_original_QC1_QC2_native_ERA_RH_20261025T231228Z_9ff46365"
GCSV="US-Me6_STAGE12G_INCOMPLETE_NOLEAP.csv"
AREC="stage12aa_readonly_SHA_receipt.json"
GREC="stage12g_research_only_sha_receipt.json"
ASRC="seven_original_native_QC1_QC2_RH_and_three_scenarios.csv"
TARGETS=("201707040600","201707040630","201707040700",
         "201707040730","201707040800")
EXPECTED={
    "201707040600":3.205763,
    "201707040630":3.974495,
    "201707040700":5.154795,
    "201707040730":9.345609,
    "201707040800":12.292544
}
EXEMPT=("201707040700","201707040730")
FIELDS=("time","TBOT","QBOT","PSRF","FSDS","FLDS",
        "WIND","PRECTmms","TA_USE","VPD_USE")

def safe(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Source missing or symlinked: "+str(p))
    return p

def sha(path):
    h=hashlib.sha256()
    with safe(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def es_water(t):
    x=np.asarray(t,dtype=float)
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        return 6.112*np.exp(17.67*x/(x+243.5))

def humidity(t,p,era_t,era_v):
    s=es_water(era_t)
    rh=100*(1-era_v/s)
    vapor=es_water(t)*rh/100
    vpd=es_water(t)-vapor
    epa=100*vapor
    qb=0.622*epa/(p-0.378*epa)
    return float(vpd),float(qb),float(rh)

def close(x,y,atol=1e-8):
    return (pd.isna(x) and pd.isna(y)) or (
        np.isfinite(x) and np.isfinite(y) and abs(float(x)-float(y))<=atol)

def keyset(df):
    return df["time"].astype(str).str.replace(
        r"[^0-9]","",regex=True).str.slice(0,12)

def selftest():
    v,q,rh=humidity(18.96,90000.,18.039,11.603)
    assert abs(v-12.29254386)<1e-6
    assert 0<rh<100 and 0<q<.08
    assert len(TARGETS)==5 and set(EXEMPT)<set(TARGETS)
    times=pd.to_datetime(TARGETS,format="%Y%m%d%H%M")
    assert (np.diff(times.to_numpy()).astype("timedelta64[m]").astype(int)==30).all()
    assert abs(9.345609-5.154795-4.190814)<1e-5
    print("STAGE12AC SELF-TEST PASS: five native HH, same-source ERA RH, VPD/QBOT, scoped one-edge exception; NO WRITES",flush=True)

def verify():
    a=json.loads(safe(AA/AREC).read_text())
    g=json.loads(safe(G/GREC).read_text())
    if (a.get("version")!="batch03-stage12aa-v1-20261025-QC1-QC2-original-native-30min-ERA-RH"
        or a.get("original_86_plus_233_science_holds_preserved") is not True
        or a.get("new_repairs")!=0
        or a.get("Postv5_approved")!=0 or a.get("DATM_ready")!=0
        or a.get("spinup_authorized")!=0):
        raise ValueError("Original Stage12aa 86+233 science hold/source receipt changed")
    for name,digest in a.get("output_SHA256",{}).items():
        if sha(AA/name)!=digest:
            raise ValueError("Signed original Stage12aa source report changed "+name)
    if (g.get("original_233_physics_holds_untouched") is not True
        or g.get("original_six_site_T_P_native_clock_unchanged") is not True
        or g.get("all_original_Stage12e_finite_humidity_untouched") is not True
        or g.get("INCOMPLETE_marker_present") is not True
        or g.get("Postv5_approved")!=0 or g.get("DATM_ready")!=0
        or g.get("spinup_authorized")!=0
        or sha(G/GCSV)!=g["output_sha256"].get(GCSV)):
        raise ValueError("Original Stage12g immutable source/science gate changed")
    safe(G/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    manifest=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    spec=next(s for s in manifest["sites"] if s["site"]=="US-Me6")
    pins={str(Path(path).resolve()):dig
          for path,dig in manifest["input_sha256"].items()}
    for field in ("primary","era"):
        f=safe(spec[field])
        if sha(f)!=pins.get(str(f.resolve())):
            raise ValueError("Original FLUXMET/companion ERA source SHA changed: "+field)
    return spec,a,g

def build():
    spec,a,g=verify()
    aa=pd.read_csv(safe(AA/ASRC),dtype={"TIMESTAMP_START":str},low_memory=False)
    if (len(aa)!=7 or
        aa.TIMESTAMP_START.tolist()!=[
          "201707040600","201707040630","201707040700",
          "201707040730","201707040800","201707040830","201707040900"]):
        raise ValueError("Signed 7-row source origin timeline changed")
    orig=pd.read_csv(safe(G/GCSV),dtype={"time":str},low_memory=False)
    if not set(FIELDS)<=set(orig.columns):
        raise ValueError("Signed original Stage12g field schema differs")
    keys=keyset(orig)
    if keys.duplicated().any() or not set(TARGETS)<=set(keys):
        raise ValueError("Duplicate/missing original native Stage12g target")
    positions={key:i for i,key in enumerate(keys)}
    trial=orig.copy(deep=True)
    changes=[]
    for key in TARGETS:
        i=positions[key]
        src=aa.loc[aa.TIMESTAMP_START.eq(key)]
        if len(src)!=1:raise ValueError("Signed ERA source target missing "+key)
        x=src.iloc[0]
        t=float(x.TA_F)
        if (float(x.TA_F_QC)!=0 or float(x.VPD_F_QC)!=1
            or abs(float(x.VPD_F)-float(x.VPD_F_MDS))>1e-7
            or abs(float(trial.TA_USE.iat[i])-t)>1e-7):
            raise ValueError("Operator authorized target QC0 temperature / MDS source not retained: "+key)
        p=float(trial.PSRF.iat[i])
        et=t+float(x.native_companion_T_minus_original_T_C)
        rh=float(x.native_companion_ERA_RH_pct)
        vv=float(x.scenario_C_all_companion_RH_referenced_VPD_hPa)
        # The original signed Stage12aa VPD candidate already used exact
        # original same-native TA_ERA/VPD_ERA; derive a compatible QBOT at
        # original unchanged tower TA and site PSRF.
        vapor=es_water(t)*rh/100.
        vpd=float(es_water(t)-vapor)
        epa=float(vapor*100)
        q=float(.622*epa/(p-.378*epa))
        if (not (0<rh<=100 and abs(t-et)<=5 and 50000<=p<=110000
                 and 0<=vpd<float(es_water(t)) and 0<q<.08)
            or abs(vpd-vv)>1e-7 or abs(vpd-EXPECTED[key])>1e-5):
            raise ValueError("Signed original same-native ERA RH or VPD/QBOT closure failed: "+key)
        old_v=float(orig.VPD_USE.iat[i])
        old_q=float(orig.QBOT.iat[i])
        if key in ("201707040700","201707040730"):
            if not np.isnan(old_v) or not np.isnan(old_q):
                raise ValueError("Two previously held original G records must remain missing in original: "+key)
        elif key in ("201707040600","201707040630"):
            if not close(old_v,vpd,atol=1e-6) or not close(old_q,q,atol=1e-7):
                raise ValueError("Previously retained 06:00 / 06:30 companion ERA RH disagreement: "+key)
        elif key=="201707040800":
            if not close(old_v,21.391,atol=1e-7):
                raise ValueError("Original inherited 08:00 MDS source changed")
        trial.loc[i,"VPD_USE"]=vpd
        trial.loc[i,"QBOT"]=q
        changes.append({
            "site":"US-Me6","native_key":key,
            "operator_user_approved_20261025":True,
            "source_VPD_F_QC_MDS":int(x.VPD_F_QC),
            "original_QC0_tower_T_C":t,"source_companion_ERA_T_C":et,
            "signed_same_native_ERA_RH_pct":rh,"unchanged_PSRF_Pa":p,
            "before_Stage12g_VPD_hPa":old_v,
            "after_approved_VPD_hPa":vpd,
            "before_Stage12g_QBOT":old_q,
            "after_approved_QBOT":q,
            "target_VPD_was_original_HOLD":bool(np.isnan(old_v)),
            "explicit_4hPa_exception_only_when_next_is_0730":key=="201707040700",
            "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False
        })
    # Guarantee all untouched records, variables and existing G finite
    # values are unchanged (source values, not source serialisation bytes).
    target_mask=keys.isin(TARGETS).to_numpy(dtype=bool)
    for col in orig.columns:
        if col in ("VPD_USE","QBOT"):
            if not np.array_equal(
                pd.to_numeric(orig.loc[~target_mask,col],errors="coerce").to_numpy(),
                pd.to_numeric(trial.loc[~target_mask,col],errors="coerce").to_numpy(),
                equal_nan=True):
                raise ValueError("Unapproved off-target humidity modification "+col)
        elif not orig[col].equals(trial[col]):
            raise ValueError("Unapproved tower T/P/time/other source column modification "+col)
    vv=pd.to_numeric(trial.VPD_USE,errors="coerce").to_numpy(dtype=float)
    qq=pd.to_numeric(trial.QBOT,errors="coerce").to_numpy(dtype=float)
    pressure=pd.to_numeric(trial.PSRF,errors="coerce").to_numpy(dtype=float)
    t=pd.to_numeric(trial.TA_USE,errors="coerce").to_numpy(dtype=float)
    for key in TARGETS:
        i=positions[key]
        ea_hpa=float(es_water(t[i])-vv[i])
        ideal=.622*(ea_hpa*100)/(pressure[i]-.378*(ea_hpa*100))
        if not np.isclose(ideal,qq[i],atol=1e-10,rtol=1e-8):
            raise ValueError("Approved QBOT/VPD moisture closure failed "+key)
    boundary=[]
    for l,r in zip(("201707040530",*TARGETS),
                   (*TARGETS,"201707040830")):
        if l not in positions or r not in positions:
            raise ValueError("Missing neighbor context around approved 5 records")
        a,b=positions[l],positions[r]
        if b!=a+1:
            raise ValueError("Target edge not consecutive source-native half-hour")
        prev=float(vv[a]);nextv=float(vv[b])
        jump=abs(nextv-prev) if np.isfinite(prev) and np.isfinite(nextv) else np.nan
        exempt=(l,r)==EXEMPT
        if np.isfinite(jump) and jump>4.0+1e-9 and not exempt:
            # Already-existing 05:30->06:00 must not cause a new violation
            # since the 06:00 value is unchanged, but report it separately.
            if not (l=="201707040530" and close(
                float(orig.VPD_USE.iat[b]),nextv,atol=1e-6)):
                raise ValueError("New >4 hPa jump outside exactly approved 07:00->07:30 edge: "+l+" "+r)
        if exempt and not np.isclose(jump,4.190815,atol=1e-5):
            raise ValueError("User approved specific 07:00->07:30 exception altered")
        boundary.append({
            "native_from":l,"native_to":r,"jump_hPa":jump,
            "over_4hPa":bool(np.isfinite(jump) and jump>4),
            "single_user_approved_exception":exempt,
            "target_or_neighbor_source_unchanged":True
        })
    records=pd.DataFrame(changes)
    edges=pd.DataFrame(boundary)
    if (len(records)!=5 or not records.native_key.tolist()==list(TARGETS)
        or records.target_VPD_was_original_HOLD.sum()!=2
        or int(edges.single_user_approved_exception.sum())!=1):
        raise ValueError("Exactly five site-specific operator-approved repairs did not reconcile")
    return orig,trial,records,edges

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","apply"):
        modes.add_argument("--"+mode,action="store_true")
    args=parser.parse_args()
    print("STAGE12AC — USER APPROVED US-Me6 FIVE HALF-HOUR ERA RH DIRECT REPLACEMENT | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    orig,trial,records,edges=build()
    print("\n========== EXACT FIVE USER-APPROVED NATIVE SOURCE REPLACEMENTS ==========",flush=True)
    print(records.to_string(index=False),flush=True)
    print("\n========== APPROVED SEGMENT PLUS BOTH NATIVE ADJACENT BOUNDARIES ==========",flush=True)
    print(edges.to_string(index=False),flush=True)
    print("\nSTAGE12AC APPROVAL: 5 HH, exactly 2 source HOLUM gaps now filled "
          "only in NEW derivative; 07:00->07:30 single >4hPa exception; "
          "original G/source unchanged; other holds preserved; "
          "Postv5=0 DATM=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12AC CHECK ONLY: ZERO FILE WRITES.",flush=True)
        return
    dest=ROOT/"science_trials"/(
        "stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    outputs={
      "US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv":trial,
      "five_operator_approved_original_native_ERA_RH_replacements.csv":records,
      "seven_edges_user_approved_interval_plus_neighbors.csv":edges
    }
    for n,df in outputs.items():
        df.to_csv(dest/n,index=False)
    (dest/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "User-approved 5HH site-specific replacement applied to new separate "
        "source shadow. This whole batch is not fully forcing-ready. "
        "No Post-v5 / DATM / CIME / Slurm or spinup approval.\n")
    (dest/"APPROVAL_DECISION.md").write_text(
        "User explicitly approved replacing VPD_USE and corresponding QBOT "
        "using original-native companion ERA RH at measured tower T and "
        "existing Stage12g site PSRF for US-Me6 2017-07-04 inclusive "
        "06:00, 06:30, 07:00, 07:30 and 08:00. "
        "Do not perform further alternative-candidate experiments for these "
        "five targets. Explicitly permit the one 07:00->07:30 VPD 4.190815 "
        "hPa jump notwithstanding default scientific 4hPa filter. "
        "The 07:00/07:30 prior G missing HOLD values are released ONLY "
        "in this new approved derivative. All other source values and "
        "other scientific holds remain unchanged in original Stage12g. "
        "Original source files and Stage12g must never be overwritten.\n")
    dig={name:sha(dest/name) for name in [*outputs,
        "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP","APPROVAL_DECISION.md"]}
    receipt={
       "version":VERSION,
       "approved_by_user_on":"2026-10-25",
       "approved_exact_native_halfhours":list(TARGETS),
       "original_Stage12g_SHA256":sha(G/GCSV),
       "original_Stage12g_receipt_SHA256":sha(G/GREC),
       "original_Stage12aa_receipt_SHA256":sha(AA/AREC),
       "two_old_G_HOLDs_released_in_NEW_derived_overlay_only":True,
       "other_HOLDs_not_changed":True,
       "single_exact_07h00_07h30_4hPa_exception":True,
       "original_FLUXMET_source_or_Stage12g_changed":False,
       "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
       "output_SHA256":dig
    }
    (dest/"stage12ac_user_approved_5HH_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12AC USER-APPROVED CORRECTED DERIVATIVE DIR:",dest,flush=True)
    print("NO ORIGINAL SOURCE, STAGE12G, OFF-TARGET RECORDS, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12AC STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

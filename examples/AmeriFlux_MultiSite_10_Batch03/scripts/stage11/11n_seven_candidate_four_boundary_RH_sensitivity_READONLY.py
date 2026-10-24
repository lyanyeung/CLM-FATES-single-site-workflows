#!/usr/bin/env python3
"""Stage11n: ZERO-WRITE source/ERA RH sensitivity for seven *UNAPPROVED* US-NC2 points.

INPUT: SHA-sealed Stage11m 40-row source/ERA context and sealed Stage11l
US-NC2 full forcing. Source-native records are matched EXACTLY, not by
approximate times. EC tower TA_USE/TBOT and all other fields are retained.
Compare Stage11l reference with independent-in-memory reanalysed humidity
for 1 Mar18 + 5 Mar23 + 1 Mar25 targeted source-native half-hours.

The seven are proposed REVIEW cases, NOT human-approved repairs.
Three had already been repaired by Stage07, so NO edits to archived v5
are allowed. Examines four known residual transitions and *both sides*
of every hypothetical replacement. Reports candidate RH/VPD/QBOT and
new vs pre-existing discontinuities. Independent ERA5-Land not used.

--self-test: no IRIDIS input or writes
--check    : full SHA-locked source comparison, in-memory only, NO writes
--run      : new SHA-receipted read-only reports/stage11n_* ONLY;
             NEVER writes a forcing or modifies Stage07/11h/11l.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import pandas as pd
import numpy as np

sys.dont_write_bytecode=True
VERSION="stage11n-v1-20261024-seven-unapproved-RH-source-sensitivity"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
M=ROOT/"reports/stage11m_stage11l_four_boundary_context_20261024T101551Z_e5027215"
L=ROOT/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
SOURCE="US-NC2_humidity_only_new_shadow_NOLEAP.csv"
CONTEXT="40_halfhours_original_ERA_Stage07_Stage11h_Stage11l_context.csv"
BOUNDARIES="4_high_jump_boundary_differences.csv"
GROUPS={
    "MAR18":("202503181800",),
    "MAR23":("202503230730","202503230800","202503230830",
             "202503231530","202503231600"),
    "MAR25":("202503251030",)
}
SEVEN={key for group in GROUPS.values() for key in group}
PRIOR_STAGE07={"202503230730","202503230800","202503251030"}
PINNED_BOUNDARIES={
    "MAR18_NEW_START":("202503181800","202503181830",4.997141),
    "MAR23_OLD_START":("202503230830","202503230900",9.467392),
    "MAR23_NEW_END":("202503231500","202503231530",4.812737),
    "MAR25_NEW_END":("202503251000","202503251030",5.859252),
}
RECEIPT_OUTPUTS={CONTEXT,BOUNDARIES,"SCIENTIFIC_HOLD.md"}


def checked_file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink original: "+str(p))
    return p


def checked_dir(path):
    p=Path(path)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Missing or symlink source dir: "+str(p))
    return p


def sha(path):
    h=hashlib.sha256()
    with checked_file(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def sat(ta):
    with np.errstate(invalid="ignore",over="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*np.asarray(ta,dtype=float)/
                           (np.asarray(ta,dtype=float)+243.5))


def q_from_rh(t,p,rhf):
    vapour=100*sat(t)*rhf
    return 0.622*vapour/(p-0.378*vapour)


def transfer(t,p,era_t,era_v):
    e_era=float(sat(era_t))
    fraction=(e_era-era_v)/e_era
    if not np.isfinite(fraction) or not 0<fraction<=1:
        raise ValueError("Source companion ERA RH is invalid: no clipping")
    v=float(sat(t))*(1-fraction)
    q=float(q_from_rh(t,p,fraction))
    if not (np.isfinite([v,q]).all() and 0<=v<float(sat(t))
            and 0<q<0.08 and 49000<=p<=111000):
        raise ValueError("Inconsistent RH transfer at retained EC tower TA")
    return v,q,fraction*100


def self_test():
    v,q,rh=transfer(20,101325,15,5)
    assert 0<v<float(sat(20)) and 0<q<.08 and 0<rh<100
    try:
        transfer(20,101325,10,50)
    except ValueError:
        pass
    else:
        raise AssertionError("Source negative vapour was accepted")
    assert len(SEVEN)==7 and len(PRIOR_STAGE07)==3
    assert set(PRIOR_STAGE07)<=SEVEN and len(PINNED_BOUNDARIES)==4
    print("STAGE11N SELF-TEST PASS: 7 review points (3 Stage07-amended), fixed EC TA, original/ERA humidity algebra; NO WRITES",flush=True)


def inputs():
    for p in (ROOT,M,L,H,S07):
        checked_dir(p)
    for p in (L,H,S07):
        checked_file(p/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    receipt=json.loads(checked_file(M/"stage11m_read_only_boundary_receipt.json").read_text())
    lreceipt=json.loads(checked_file(L/"stage11l_scientific_hold_receipt.json").read_text())
    if (receipt.get("version")!="stage11m-v1-20261024-four-boundary-no-forcing-write"
        or receipt.get("source_Stage11l_receipt_SHA256")!=sha(L/"stage11l_scientific_hold_receipt.json")
        or receipt.get("source_Stage11h_receipt_SHA256")!=sha(H/"sha_sealed_shadow_trial_receipt.json")
        or receipt.get("source_Stage07_manifest_SHA256")!=sha(S07/"exact_input_manifest.json")
        or receipt.get("boundary_transitions")!=4
        or receipt.get("original_native_context_rows")!=40
        or receipt.get("new_repair_approvals")!=0
        or receipt.get("Postv5_approved")!=0
        or receipt.get("DATM_ready")!=0
        or receipt.get("spinup_authorizations")!=0
        or receipt.get("input_forcing_unmodified") is not True
        or set(receipt.get("output_sha256",{}))!=RECEIPT_OUTPUTS):
        raise ValueError("Stage11m sealed 40 native source/ERA rows differ from verified receipt")
    for name,value in receipt["output_sha256"].items():
        if sha(M/name)!=value:
            raise ValueError("Stage11m original data SHA changed: "+name)
    if (lreceipt.get("version")!="stage11l-v1-20261024-11-humidity-only-successor"
        or lreceipt.get("added_neighbour_events")!=11
        or lreceipt.get("newly_different_VPD")!=11
        or lreceipt.get("combined_ERA_RH_target_count")!=64
        or lreceipt.get("retained_EC_tower_TA_and_TBOT") is not True
        or lreceipt.get("Postv5_approved")!=0
        or lreceipt.get("DATM_ready")!=0
        or lreceipt.get("spinup_authorized")!=0
        or lreceipt.get("INCOMPLETE_marker_present") is not True
        or sha(L/SOURCE)!=lreceipt["output_sha256"][SOURCE]):
        raise ValueError("Stage11l source trial/forcing is not pinned or held")
    sample=pd.read_csv(checked_file(M/CONTEXT),dtype={"native_key":str},low_memory=False)
    bounds=pd.read_csv(checked_file(M/BOUNDARIES),low_memory=False)
    if (len(sample)!=40 or len(bounds)!=4
        or sample.duplicated(["boundary_id","native_key"]).any()):
        raise ValueError("Stage11m context count or four boundary identity changed")
    seen=set(sample.native_key)
    if not SEVEN<=seen or set(bounds.boundary_id)!=set(PINNED_BOUNDARIES):
        raise ValueError("Not all seven review cases and four boundary IDs in sealed Stage11m")
    for b in bounds.itertuples(index=False):
        a,c,_=PINNED_BOUNDARIES[b.boundary_id]
        if str(b.left_key)!=a or str(b.right_key)!=c:
            raise ValueError("Named Stage11m source-native boundary differs")
    return sample,bounds


def audit():
    context,bounds=inputs()
    frame=pd.read_csv(checked_file(L/SOURCE),low_memory=False)
    columns=["time","TBOT","QBOT","PSRF","FSDS","FLDS",
             "WIND","PRECTmms","TA_USE","VPD_USE"]
    if len(frame)!=367920 or list(frame.columns)!=columns:
        raise ValueError("Full preserved US-NC2 successor changed schema")
    when=pd.to_datetime(frame.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    stamps=when.dt.strftime("%Y%m%d%H%M").to_numpy()
    if len(set(stamps))!=len(stamps):
        raise ValueError("Duplicate Stage11l original native time")
    ix={v:i for i,v in enumerate(stamps)}
    by=context.groupby("native_key",sort=False)
    detail=[]
    for key in sorted(SEVEN):
        if key not in ix or key not in by.groups:
            raise ValueError("Lost pinned user review point "+key)
        rows=by.get_group(key)
        if len(rows)!=1:
            raise ValueError("Ambiguous duplicated original/ERA source-native time "+key)
        r=rows.iloc[0]
        i=ix[key]
        site_t=float(frame.TA_USE.iloc[i]);pa=float(frame.PSRF.iloc[i])
        original_v=float(frame.VPD_USE.iloc[i])
        original_q=float(frame.QBOT.iloc[i])
        if not (abs(original_v-float(r.Stage11l_VPD_hPa))<1e-8
                and abs(site_t-float(r.retained_EC_tower_TA_C))<1e-8
                and not bool(r.Stage11l_VPD_changed_from_Stage11h)
                and bool(r.Stage07_VPD_changed_from_source)==(key in PRIOR_STAGE07)):
            raise ValueError("Sealed source candidate provenance mismatch "+key)
        v,q,rh=transfer(site_t,pa,float(r.companion_ERA_T_C),
                         float(r.companion_ERA_VPD_hPa))
        if abs(rh-float(r.companion_ERA_RH_water_pct))>1e-5:
            raise ValueError("Companion ERA RH formula does not match sealed source")
        detail.append({
            "site":"US-NC2","native_key":key,
            "review_group":next(x for x,z in GROUPS.items() if key in z),
            "Stage07_previously_amended":key in PRIOR_STAGE07,
            "original_source_QC":float(r.original_VPD_F_QC),
            "original_source_implied_RH_pct":float(r.original_implied_RH_water_pct),
            "Stage11l_current_RH_pct":float(r.Stage11l_RH_water_pct),
            "ERA_companion_RH_pct":rh,
            "EC_tower_TA_retained_C":site_t,
            "Stage11l_current_VPD_hPa":original_v,
            "what_if_ERA_RH_VPD_hPa":v,
            "VPD_delta_hPa":v-original_v,
            "Stage11l_current_QBOT":original_q,
            "what_if_ERA_RH_QBOT":q,
            "change_authorized":False,
            "science_status":"HOLD_UNAPPROVED_WHAT_IF_ONLY"
        })
    details=pd.DataFrame(detail)
    original=frame.VPD_USE.to_numpy(dtype=float)
    variants={}
    variants["STAGE11L_BASELINE"]=original
    for grp,keys in GROUPS.items():
        v=original.copy()
        for k in keys:
            val=float(details.loc[details.native_key.eq(k),"what_if_ERA_RH_VPD_hPa"].iloc[0])
            v[ix[k]]=val
        variants[grp+"_ONLY"]=v
    va=original.copy()
    for r in details.itertuples(index=False):
        va[ix[r.native_key]]=r.what_if_ERA_RH_VPD_hPa
    variants["ALL7_UNAPPROVED"]=va
    rows=[]
    for scenario,arr in variants.items():
        for label,(left,right,ref) in PINNED_BOUNDARIES.items():
            i,j=ix[left],ix[right]
            if j!=i+1:
                raise ValueError("Sealed four boundary endpoints are not 30min adjacent")
            old=abs(original[j]-original[i])
            candidate=abs(arr[j]-arr[i])
            if abs(old-ref)>1e-5:
                raise ValueError("Stage11l audited boundary value differs: "+label)
            rows.append({"scenario":scenario,"boundary_id":label,"left_key":left,
                        "right_key":right,"Stage11l_jump_hPa":old,
                        "what_if_jump_hPa":candidate,
                        "difference_from_Stage11l_hPa":candidate-old,
                        "scientific_approval":False})
    boundaries=pd.DataFrame(rows)
    transitions=set()
    for key in SEVEN:
        i=ix[key]
        if i<=0 or i+1>=len(frame):
            raise ValueError("Seven source-native cases hit source bounds")
        transitions|={(i-1,i),(i,i+1)}
    edge=[]
    for i,j in sorted(transitions):
        old=abs(original[j]-original[i])
        candidate=abs(va[j]-va[i])
        edge.append({"left_key":stamps[i],"right_key":stamps[j],
            "Stage11l_jump_hPa":old,
            "hypothetical_all7_jump_hPa":candidate,
            "new_minus_existing_jump_hPa":candidate-old,
            "all7_total_jump_over4hPa":bool(candidate>4),
            "all7_added_jump_over2hPa":bool(candidate-old>2),
            "human_review_needed":True})
    edge=pd.DataFrame(edge).sort_values("hypothetical_all7_jump_hPa",ascending=False)
    if len(details)!=7 or len(boundaries)!=20 or len(edge)<7:
        raise ValueError("Missing what-if candidate or change windows")
    # In-memory-only; never mutate the original full input DataFrame.
    assert len(va)==367920 and frame.TA_USE.equals(frame.TA_USE)
    return details,boundaries,edge


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    args=p.parse_args()
    print("STAGE11N — SEVEN UNAPPROVED HUMIDITY SOURCE WHAT-IF CASES | "+VERSION,flush=True)
    self_test()
    if args.self_test:
        return
    detail,bounds,adjacent=audit()
    print("\n========== SEVEN REVIEW-ONLY ORIGINAL AND ERA HUMIDITY CANDIDATES ==========",flush=True)
    print(detail[["review_group","native_key","Stage07_previously_amended",
        "original_source_QC","Stage11l_current_RH_pct","ERA_companion_RH_pct",
        "Stage11l_current_VPD_hPa","what_if_ERA_RH_VPD_hPa"]].to_string(index=False),flush=True)
    print("\n========== FOUR RESIDUAL BOUNDARIES IN FIVE WHAT-IF SCENARIOS ==========",flush=True)
    print(bounds[["scenario","boundary_id","Stage11l_jump_hPa",
                  "what_if_jump_hPa","difference_from_Stage11l_hPa"]].to_string(index=False),flush=True)
    print("\n========== ALL7 HYPOTHETICAL NEIGHBOUR JUMPS, DESCENDING ==========",flush=True)
    print(adjacent.to_string(index=False),flush=True)
    print("\nSTAGE11N SUMMARY: 7 source-native review cases=7 (previously_Stage07_repaired=3) "
          "hypothetical_VPD_only=7 EC_tower_T_unchanged=True "
          "source/forcing_writes=0 new_human_decisions=0 "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("CHECK ONLY: NO REPORTS, FORCING OR MODEL FILES MODIFIED.",flush=True)
        return
    out=ROOT/"reports"/("stage11n_seven_unapproved_RH_source_what_if_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    tables={
        "7_source_native_candidate_RH_comparisons.csv":detail,
        "4_boundaries_x_5_hypothetical_scenarios.csv":bounds,
        "all7_new_adjacent_jump_sensitivity.csv":adjacent
    }
    for name,df in tables.items():
        df.to_csv(out/name,index=False)
    note="""# UNAPPROVED Stage11n read-only RH source sensitivity

Seven source-native US-NC2 times are proposed only for possible human
review. Exactly 3 were previously changed by Stage07, and this what-if
MUST NOT override that earlier method/choice without an explicit new
separate human decision. All seven original/ERA paired values derive
from SHA-locked Stage11m source; source ERA5 is NOT tower ground truth.

No source, Stage07, Stage11h or Stage11l forcing file changed. The
what-if arrays existed in memory only; the CSVs are review results,
never DATM-ready forcing. Tower TA_USE/TBOT are unchanged.
Do not judge a VPD humidity series as correct solely by smoothness.
Post-v5, DATM, spinup authorizations remain ZERO.
"""
    (out/"SCIENTIFIC_HOLD.md").write_text(note)
    receipt={
        "version":VERSION,
        "Stage11m_source_receipt_SHA256":sha(M/"stage11m_read_only_boundary_receipt.json"),
        "Stage11l_source_receipt_SHA256":sha(L/"stage11l_scientific_hold_receipt.json"),
        "unapproved_review_native_times":7,"Stage07_previously_amended":3,
        "hypothetical_scenarios":5,"four_edges_each":4,
        "source_or_forcing_modified":False,
        "human_scientific_repair_decisions":0,
        "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
        "output_sha256":{x:sha(out/x) for x in [*tables,"SCIENTIFIC_HOLD.md"]}
    }
    (out/"stage11n_read_only_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE11N REVIEW REPORT DIR:",out,flush=True)
    print("NO SOURCE, STAGE07, STAGE11H, STAGE11L, DATM OR SLURM MODIFIED.",flush=True)


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print("STAGE11N STOP:",str(e),file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

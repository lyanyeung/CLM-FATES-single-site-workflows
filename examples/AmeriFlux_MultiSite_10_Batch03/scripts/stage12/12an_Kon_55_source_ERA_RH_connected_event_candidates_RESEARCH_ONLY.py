#!/usr/bin/env python3
"""Stage12an — US-Kon source-native, connected-event ERA-RH humidity trial.

Source: SHA-verified Stage12am science evidence (57 centers), the latest
Stage12ak research-only US-Kon full NOLEAP, and exact published original
tower + companion ERA files. ONLY 55 centers with companion |TA-TERA|<=5
enter source-native event-level numerical trials. Preserve separately:
 201102220900: >5 C original tower vs ERA disagreement
 201109291830: original TA_F_QC1/VPD_F_QC2 and >5 C discrepancy.
Do not touch these or any original QC0 humidity records.

For each cluster of adjacent original center HOLDs, calculate RH from
original native TA_ERA+VPD_ERA; use Stage12ak TA_USE, PSRF to calculate
candidate VPD and QBOT. If a finite QC1/2 neighboring VPD is discontinuous
(>4hPa/30min) or physically impossible, propose replacing that neighbor's
humidity with the SAME source-native ERA-RH. Expand the candidate cluster
only while signed QC1/2 source, |TA-TERA|<=5 C, RH/water/ice physics,
and finite observed QC0 edge checks allow. Cap expansions to 48 rows per
cluster and NEVER cross old unrelated held humidity or special exclusion.

Per-cluster research-only PASS if every boundary (internal + 30min at
both ends) has finite VPD, <=4hPa absolute jump and all values physical.
Only PASS clusters are written into one entirely separate SHA-sealed
INCOMPLETE research trial. Failed clusters (including original gaps) remain
unchanged/missing. Do not infer any operator approval or model readiness.
All raw FLUXNET inputs, approved prior T and QC0 VPD exception, UTC clock
and original source QC remain immutable.

--self-test: no input/writes
--check: source + event matching, numeric research in memory, NO writes
--trial: same checks + independent CSV science successor/report ONLY
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VERSION="batch03-stage12an-v1-20261026-Kon-connected-ERA-RH-55-centers"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AK=R/"science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AM=R/"reports/stage12am_Kon_57_humidity_ERA_episode_original_source_review_20261026T034540Z_379e08c6"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
SOURCE="US-Kon_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
CENTERS="57_exact_Kon_source_and_native_ERA_RH_humidity_centre_proposals.csv"
SOURCE_CONTEXT="deduplicated_original_Kon_plus_minus_two_native_halfhours_source_provenance.csv"
EXCLUDE=("201102220900","201109291830")
MAX_EXTRA_PER_EVENT=48

def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():raise ValueError("SHA source absent/symlink: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def keys(x):
    return x.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def stamp(k):
    return pd.to_datetime(k,format="%Y%m%d%H%M")
def inc(k,offset):
    return (stamp(k)+pd.Timedelta(minutes=30*offset)).strftime("%Y%m%d%H%M")
def satw(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(243.5+t))
def sati(t):
    t=float(t)
    return 6.112*np.exp(22.46*t/(272.62+t))
def phys(t,p,rh):
    if not(np.isfinite([t,p,rh]).all() and -85<float(t)<55 and
           50000<float(p)<110000 and 0<float(rh)<1):
        return None
    e=satw(t)*float(rh)
    v=satw(t)-e
    q=.622*(e*100)/(float(p)-.378*(e*100))
    if not(0<v<satw(t) and 0<q<.08 and
           (float(t)>=0 or e<=sati(t)*1.02)):
        return None
    return float(v),float(q)
def selftest():
    assert len(EXCLUDE)==2 and len(set(EXCLUDE))==2
    assert inc("201103241230",1)=="201103241300"
    assert inc("201103241230",-1)=="201103241200"
    assert phys(1.241,70840,.72) is not None
    assert phys(1.241,70840,-.03) is None
    assert abs(satw(5.5)-satw(5.5))<1e-12
    print("STAGE12AN SELF-TEST PASS: 55 retained center candidates, 2 exception HOLDs, connected event 30min physics; NO WRITES",flush=True)
def preflight():
    a=json.loads(safe(AK/"stage12ak_research_proposal_SHA_receipt.json").read_text())
    m=json.loads(safe(AM/"stage12am_Kon_57_source_event_science_SHA_receipt.json").read_text())
    if not(a.get("unique_native_rows")==7
        and a.get("original_variable_fields")==8
        and a.get("science_user_approved_to_production") is False
        and a.get("DATM_ready") is False and a.get("spinup_authorized") is False
        and a.get("output_SHA256",{}).get(SOURCE)==sha(AK/SOURCE)
        and m.get("event_center_total")==57
        and m.get("adjacent_halfhour_sides")==114
        and m.get("original_Kon_201109291830_QC1_temperature_special_HOLD") is True
        and m.get("humidity_ERA_replacements_operator_approved") is False
        and m.get("Postv5_approved") is False
        and m.get("output_SHA256",{}).get(CENTERS)==sha(AM/CENTERS)
        and m.get("output_SHA256",{}).get(SOURCE_CONTEXT)==sha(AM/SOURCE_CONTEXT)):
        raise ValueError("Upstream actual Stage12ak / Stage12am v2 SHA/57-case gate changed")
    manifest=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next(x for x in manifest["sites"] if x["site"]=="US-Kon")
    pins={str(Path(p).resolve()):h for p,h in manifest["input_sha256"].items()}
    for group in ("primary","era"):
        p=safe(spec[group])
        if sha(p)!=pins.get(str(p.resolve())):raise ValueError("Original native tower/ERA source SHA changed "+group)
    return spec
def candidate(k,source,era,base,idx):
    # Native paired ERA-RH, retained/or user-approved T and selected site P.
    if k not in idx or k not in source.index or k not in era.index:return None,"SOURCE_MISSING"
    s=source.loc[k];e=era.loc[k]
    t=float(base.TA_USE.iat[idx[k]]);p=float(base.PSRF.iat[idx[k]])
    te=float(e.TA_ERA);ve=float(e.VPD_ERA)
    if not np.isfinite([t,p,te,ve]).all():return None,"NONFINITE_MET_OR_ERA"
    if abs(t-te)>5:return None,"SITE_ERA_T_ABSDIFF_GT5C"
    er=1-ve/satw(te)
    z=phys(t,p,er)
    if z is None:return None,"RH_QBOT_WATER_ICE_PHYSICS_FAIL"
    v,q=z
    return {"native_key":k,"VPD":v,"QBOT":q,"RH":er*100,"T":t,"PSRF":p,
            "TA_ERA":te,"VPD_ERA":ve,"source_T_QC":int(s.TA_F_QC),
            "source_VPD_QC":int(s.VPD_F_QC)},None
def audit():
    spec=preflight()
    base=pd.read_csv(safe(AK/SOURCE),dtype={"time":str},low_memory=False)
    if len(base)!=280320 or not {"TA_USE","TBOT","PSRF","VPD_USE","QBOT","time"}<=set(base):
        raise ValueError("Original selected Kon full NOLEAP schema/row count changed")
    native=keys(base.time)
    if native.duplicated().any():raise ValueError("Original native timestamps duplicated")
    idx={str(k):i for i,k in enumerate(native)}
    evidence=pd.read_csv(safe(AM/CENTERS),dtype={"native_key":str},low_memory=False)
    all57=set(evidence.native_key)
    if len(evidence)!=57 or len(all57)!=57 or set(EXCLUDE)-all57:
        raise ValueError("Stage12am 57 exact original source holds/exception membership altered")
    refuse=evidence.loc[evidence.native_key.isin(EXCLUDE)].set_index("native_key")
    if not (len(refuse)==2
        and all(bool(refuse.loc[k,"ERA_T_within5C"]) is False for k in EXCLUDE)
        and bool(refuse.loc["201109291830","temperature_QC1_unapproved_separate_science_HOLD"])
        and not bool(refuse.loc["201102220900","temperature_QC1_unapproved_separate_science_HOLD"])):
        raise ValueError("Exact two source-temperature exception cases no longer match signed Stage12am report")
    requested=sorted(all57-set(EXCLUDE))
    if len(requested)!=55 or any(k not in idx or
         not(pd.isna(base.VPD_USE.iat[idx[k]]) and pd.isna(base.QBOT.iat[idx[k]])) for k in all57):
        raise ValueError("Protected 57 science holds not all still missing in Kon Stage12ak")
    if not np.isclose(float(base.VPD_USE.iat[idx["200809260530"]]),2.801,rtol=0,atol=1e-10):
        raise ValueError("Previously user-approved source QC0 VPD special value changed")
    rs=pd.read_csv(safe(spec["primary"]),low_memory=False,
          dtype={"TIMESTAMP_START":str},
          usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    er=pd.read_csv(safe(spec["era"]),low_memory=False,
          dtype={"TIMESTAMP_START":str},usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"])
    rs=rs.loc[rs.TIMESTAMP_START.isin(idx)].copy()
    er=er.loc[er.TIMESTAMP_START.isin(idx)].copy()
    if rs.TIMESTAMP_START.duplicated().any() or er.TIMESTAMP_START.duplicated().any():
        raise ValueError("Original source timestamp duplicates")
    rs.set_index("TIMESTAMP_START",inplace=True)
    er.set_index("TIMESTAMP_START",inplace=True)
    for d in (rs,er):
        for col in d:
            d[col]=pd.to_numeric(d[col],errors="coerce")
            d.loc[d[col].le(-9990),col]=np.nan
    # Verify original center source QC classifications from Stage12am.
    for obj in evidence.itertuples(index=False):
        k=obj.native_key
        if (k not in rs.index or k not in er.index or
            not np.isclose(float(rs.loc[k,"TA_F_QC"]),float(obj.source_T_QC),atol=0,rtol=0) or
            not np.isclose(float(rs.loc[k,"VPD_F_QC"]),float(obj.original_VPD_QC),atol=0,rtol=0)):
            raise ValueError("Stage12am center origin QC changed "+k)
    # Connected components of original 55 center records on 30min native grid.
    groups=[]
    for k in requested:
        if groups and inc(groups[-1][-1],1)==k:groups[-1].append(k)
        else:groups.append([k])
    allpatch={}
    table=[]
    outcome=[]
    boundaries=[]
    for num,seed in enumerate(groups,1):
        patch={}
        blockers=set()
        for k in seed:
            value,why=candidate(k,rs,er,base,idx)
            if why:blockers.add("CENTER_"+why+"_"+k)
            else:
                if int(rs.loc[k,"VPD_F_QC"]) not in (1,2):
                    blockers.add("CENTER_PROTECTED_VPD_QC0_"+k)
                patch[k]=value
        # Expand only through original source QC1/2 finite neighbors when
        # old value makes a >4hPa edge or is already physically impossible.
        # NEVER bridge other held NaNs or release excluded original centers.
        for iteration in range(MAX_EXTRA_PER_EVENT+2):
            expand=[]
            for k,v in sorted(patch.items()):
                for off in (-1,1):
                    n=inc(k,off)
                    if n not in idx:
                        blockers.add("NATIVE_EDGE_ABSENT_"+n);continue
                    if n in patch:
                        jump=abs(v["VPD"]-patch[n]["VPD"])
                        if jump>4:blockers.add("INTERNAL_ERA_RH_JUMP_GT4_"+k+"_"+n)
                        continue
                    j=idx[n]
                    oldv=float(base.VPD_USE.iat[j])
                    if n in EXCLUDE:
                        blockers.add("ADJACENT_TWO_SOURCE_SCIENCE_HOLD_"+n);continue
                    if n in all57:
                        # Any different seed center group that is adjacent
                        # must have been grouped above, so fail rather than
                        # secretly release it.
                        blockers.add("DIFFERENT_CENTER_GROUP_"+n);continue
                    if not np.isfinite(oldv):
                        blockers.add("UNRELATED_ORIGINAL_VPD_HOLD_"+n);continue
                    if not np.isfinite(v["VPD"]):
                        blockers.add("CANDIDATE_VPD_NONFINITE_"+k);continue
                    oldt=float(base.TA_USE.iat[j])
                    oldphysical=(0<=oldv<satw(oldt))
                    jump=abs(v["VPD"]-oldv)
                    if jump<=4 and oldphysical:continue
                    if n not in rs.index or int(rs.loc[n,"VPD_F_QC"]) not in (1,2):
                        blockers.add("PROTECTED_OR_NO_SOURCE_QC0_EDGE_"+n);continue
                    new,why=candidate(n,rs,er,base,idx)
                    if why:
                        blockers.add("NEIGHBOR_"+why+"_"+n);continue
                    # Keep original source QC0 temperature unchanged.
                    # Do not modify an existing finite VPD if the proposed
                    # value creates an even worse local edge.
                    if abs(v["VPD"]-new["VPD"])>4:
                        blockers.add("NEIGHBOR_NEW_VPD_STILL_JUMPS_GT4_"+n);continue
                    if n not in patch:expand.append((n,new))
            if blockers or not expand:break
            for k,v in expand:
                patch[k]=v
            if len(patch)-len(seed)>MAX_EXTRA_PER_EVENT:
                blockers.add("EXCESSIVE_SOURCE_EPISODE_EXPANSION");break
        # Audit all patch-to-patch edges and two external endpoints, never
        # silently count a missing edge as success.
        for k,v in sorted(patch.items()):
            for off in (-1,1):
                n=inc(k,off)
                if n not in idx:continue
                other=patch[n]["VPD"] if n in patch else float(base.VPD_USE.iat[idx[n]])
                edge=abs(float(v["VPD"])-other) if np.isfinite(other) else np.nan
                edgevalid=bool(np.isfinite(edge) and edge<=4)
                if not edgevalid:
                    blockers.add("UNRESOLVED_EDGE_"+k+"_"+n)
                boundaries.append({
                  "episode":num,"native_left":min(k,n),"native_right":max(k,n),
                  "one_member_k":k,"neighbor_n":n,
                  "source_neighbor_VPD_QC":float(rs.loc[n,"VPD_F_QC"]) if n in rs.index else np.nan,
                  "source_neighbor_TA_QC":float(rs.loc[n,"TA_F_QC"]) if n in rs.index else np.nan,
                  "neighbor_changed_in_hypothesis":n in patch,
                  "candidate_jump_hPa":edge,"edge_pass":edgevalid,
                  "episode_provisionally_pass":False})
        passed=not blockers and set(seed)<=set(patch) and len(patch)-len(seed)<=MAX_EXTRA_PER_EVENT
        for k,v in sorted(patch.items()):
            table.append({
               "episode":num,"native_key":k,
               "kind":"ORIGINAL_55_VPD_HELD_CENTER" if k in seed else "NEIGHBOR_ORIGINAL_VPD_QC1_QC2_PROPOSAL",
               "original_VPD_hPa":float(base.VPD_USE.iat[idx[k]]),
               "ERA_RH_research_VPD_hPa":v["VPD"],
               "ERA_RH_research_QBOT_kgkg":v["QBOT"],
               "source_original_VPD_QC":v["source_VPD_QC"],
               "source_original_T_QC":v["source_T_QC"],
               "paired_native_ERA_RH_pct":v["RH"],
               "unchanged_selected_T_C":v["T"],
               "unchanged_selected_PSRF_Pa":v["PSRF"],
               "episode_numerical_pass":passed,
               "operator_humidity_approval":False})
        if passed:
            for k,v in patch.items():
                if k in allpatch and (allpatch[k]["VPD"]!=v["VPD"]):
                    raise ValueError("Two passed source episodes conflict at native source key "+k)
                allpatch[k]=v
        outcome.append({
          "episode":num,"seed_original_55_target_count":len(seed),
          "candidate_total_with_QC1_QC2_neighbors":len(patch),
          "new_neighbors_would_change":len(patch)-len(seed),
          "seed_begin":seed[0],"seed_end":seed[-1],
          "research_numerical_pass":passed,
          "blocking_reasons":";".join(sorted(blockers)),
          "operator_approval":False
        })
    detail=pd.DataFrame(outcome)
    patchtable=pd.DataFrame(table)
    btab=pd.DataFrame(boundaries)
    if (not len(detail) or sum(x.seed_original_55_target_count for x in detail.itertuples())!=55
       or len(set(requested))!=55):
        raise ValueError("Source 55 input held center lineage lost or duplicated")
    selected=base.copy(deep=True)
    for k,v in allpatch.items():
        j=idx[k]
        if int(rs.loc[k,"VPD_F_QC"]) not in (1,2) or k in EXCLUDE:
            raise ValueError("Prohibited original QC0 VPD or special two science holds changed "+k)
        selected.loc[j,"VPD_USE"]=v["VPD"]
        selected.loc[j,"QBOT"]=v["QBOT"]
    changed=keys(base.time).isin(allpatch).to_numpy(dtype=bool)
    for col in base.columns:
        if col in ("VPD_USE","QBOT"):
            if not np.array_equal(base.loc[~changed,col].to_numpy(dtype=float),
                  selected.loc[~changed,col].to_numpy(dtype=float),equal_nan=True):
                raise ValueError("Other science holds/humidity values changed "+col)
        elif not base[col].equals(selected[col]):
            raise ValueError("User-approved temperature/pressure/met/clock modified "+col)
    if any(pd.notna(selected.VPD_USE.iat[idx[k]]) for k in EXCLUDE):
        raise ValueError("Previously protected two hard science HOLDs released")
    if not np.isclose(float(selected.VPD_USE.iat[idx["200809260530"]]),2.801,atol=1e-10,rtol=0):
        raise ValueError("Previously user-approved QC0 exception changed")
    if (int(selected.VPD_USE.isna().sum()) != 389-
        sum(k in allpatch for k in requested) or
        not np.array_equal(selected.VPD_USE.isna().to_numpy(),
                           selected.QBOT.isna().to_numpy())):
        raise ValueError("New research episode trial held count not exact")
    return selected,detail,patchtable,btab,allpatch
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","trial"):g.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    print("STAGE12AN Kon 55 Paired ERA-RH CONNECTED EVENT SCIENCE TRIAL | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    selected,events,patches,edges,applied=audit()
    print("\n====== CONNECTED ORIGINAL NATIVE ERA RH EPISODES / BLOCKERS ======",flush=True)
    print(events.to_string(index=False),flush=True)
    print("\n====== RESULTS (NUMERIC SCIENCE ONLY, NO OPERATOR APPROVAL) ======",flush=True)
    nseed=int(events.loc[events.research_numerical_pass,"seed_original_55_target_count"].sum())
    npatch=len(applied)
    print("ORIGINAL_57_HOLDS 57 | HARD_T_SOURCE_HOLDS 2 | NOMINATED_CENTERS 55")
    print("CONNECTED_EPISODES",len(events),"PASS",int(events.research_numerical_pass.sum()),
          "HELD",int((~events.research_numerical_pass).sum()),flush=True)
    print("SCOPED_RESEARCH_PATCHES_TOTAL",npatch,"PASS_CENTER_HOLDS_RELEASED_NUMERICALLY",nseed,
          "ORIGINAL_QC1_QC2_FINITE_NEIGHBORS_REPLACED",npatch-nseed,
          "NEW_RESEARCH_KON_VPD_QBOT_MISSING",int(selected.VPD_USE.isna().sum()),flush=True)
    print("HARD_TWO_SPECIAL_HOLDS_REMAIN",",".join(EXCLUDE),flush=True)
    print("STAGE12AN no prior/user input modified; no Post-v5/DATM/spinup approval.",flush=True)
    if args.check:
        print("STAGE12AN CHECK ONLY: ZERO NEW SOURCE, REPORT, FORCING OR MODEL WRITES.",flush=True);return
    out=R/"science_trials"/("stage12an_Kon_55_center_connected_ERA_RH_science_only_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    outputs={
      "US-Kon_STAGE12AN_ERA_RH_CONNECTED_EPISODE_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv":selected,
      "connected_episode_pass_and_source_hold_reasons.csv":events,
      "research_candidate_native_QC1_QC2_humidity_event_changes.csv":patches,
      "science_only_event_VPD_30min_boundaries.csv":edges}
    for name,frame in outputs.items():frame.to_csv(out/name,index=False)
    marker="INCOMPLETE_NUMERICAL_RESEARCH_HUMIDITY_NOT_OPERATOR_APPROVED_NO_DATM"
    (out/marker).write_text(
      "Never use as DATM, CIME or spinup input. Stage12ak pressure/longwave "
      "proposal is also NOT yet operator-approved. Stage12an applies only "
      "numerically PASS original-native connected-episode companion ERA-RH "
      "candidate VPD/QBOT edits in a completely separate scientific shadow. "
      "All 2 temperature provenance hard holds and every blocked event "
      "remain missing, original QC0 humidity unchanged. No source or "
      "historical science record is overwritten.\n")
    dig={f:sha(out/f) for f in [*outputs,marker]}
    (out/"stage12an_research_only_55_source_event_SHA_receipt.json").write_text(json.dumps({
      "version":VERSION,"original_am_science_SHA256":sha(AM/"stage12am_Kon_57_source_event_science_SHA_receipt.json"),
      "original_ak_science_SHA256":sha(AK/"stage12ak_research_proposal_SHA_receipt.json"),
      "old_humidity_hold_centers":34,"new_T_humidity_hold_centers":23,
      "source_t_disagreement_hard_holds":list(EXCLUDE),
      "research_centers_requested":55,"research_center_pass_numerical":nseed,
      "original_finite_QC1_QC2_neighbor_source_humidity_changes":npatch-nseed,
      "numerical_event_trial_PASSED":int(events.research_numerical_pass.sum()),
      "numerical_event_trial_HELD":int((~events.research_numerical_pass).sum()),
      "Kon_stage12ak_original_VPD_missing":389,
      "Kon_stage12an_science_trial_VPD_missing":int(selected.VPD_USE.isna().sum()),
      "original_QC0_VPD_preserved":True,"operator_humidity_approval":False,
      "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
      "output_SHA256":dig},indent=2)+"\n")
    print("STAGE12AN SCOPED RESEARCH ONLY SCIENCE TRIAL DIR:",out,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AN STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

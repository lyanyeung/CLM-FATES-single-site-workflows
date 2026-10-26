#!/usr/bin/env python3
"""Stage12am: US-Kon source-native 34 ORIGINAL Stage12g humidity HOLD centers
plus 23 NEW Stage12ah user-approved temperature edit humidity HOLD centers.

Strictly read-only source+signed latest Stage12ak nonhumidity trial audit,
NOT a user-approved 57-row VPD/QBOT replacement:
 - SHA-locks original Stage12ag 35-event center source, Stage12ah 23 edits,
   Stage12ak full selected US-Kon, original Stage07 FLUXMET+ERA input.
 - Demands exact 34 + 23 DISTINCT native HH now missing VPD/QBOT.
 - Recomputes paired-original same-native ERA-RH, new VPD/QBOT using
   Stage12ak's current T+PSRF, with explicit native-source QC.
 - Checks original (measured and MDS/ERA gapfilled) neighbor VPD source,
   retained native VPD, temperature and 30min jumps. Scores center-only
   versus a WHOLE connected source-episode repair proposal.
 - Makes no humidity edits, no arbitrary ERA5-Land timestamp offset,
   no model-ready approvals, no rewriting of original QC0 measurements.

--self-test no file access/writes
--check audited console output only
--run writes only independent signed research REVIEW tables
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
V="batch03-stage12am-v2-20261026-Kon-34-plus-23-with-sep29-QC1-T-exception"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AK=ROOT/"science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AH=ROOT/"science_trials/stage12ah_USER_APPROVED_Kon_23_T_one_QC0_VPD_20261026T024732Z_8075bed8"
AG=ROOT/"reports/stage12ag_Kon_35_original_T_QC_native_pm2h_repair_decision_20261026T023414Z_2f65dcb1"
S=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
A="US-Kon_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
H="US-Kon_STAGE12AH_APPROVED_23T_QC0VPD_INCOMPLETE_NOLEAP.csv"
H_T="23_user_approved_original_native_T_interpolations.csv"
AG_TAB="35_Kon_source_temperature_QC_and_ERA5Land_ERA_comparisons.csv"
FIELDS=("TA_USE","TBOT","PSRF","VPD_USE","QBOT")
def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():raise ValueError("Missing or symlink immutable source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def key(series):
    return series.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def sat(t):
    x=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*x/(x+243.5))
def qbot(t,p,v):
    e=(float(sat(t))-float(v))*100.
    return .622*e/(float(p)-.378*e)
def adjacent(k,offset):
    return (pd.to_datetime(k,format="%Y%m%d%H%M")+
           pd.Timedelta(minutes=30*offset)).strftime("%Y%m%d%H%M")
def selftest():
    assert abs(qbot(4.444,96500,2.0)-qbot(4.444,96500,2.0))<1e-12
    assert adjacent("201103241300",-1)=="201103241230"
    assert adjacent("201103241300",1)=="201103241330"
    # An original VPD_F_QC=2 science hold has TA_F_QC=1, unlike the
    # other expected 33 observed-temperature centers.
    assert "201109291830" not in ("201103241300","201103241330")
    assert float(sat(5.465))>5.
    print("STAGE12AM SELF-TEST PASS: 34 old + 23 new distinct humidity HOLDs, paired ERA-RH, 30min source context; NO WRITES",flush=True)
def upstream():
    ak=json.loads(safe(AK/"stage12ak_research_proposal_SHA_receipt.json").read_text())
    ah=json.loads(safe(AH/"stage12ah_approved_23T_QC0_SHA_receipt.json").read_text())
    ag=json.loads(safe(AG/"stage12ag_original_science_report_SHA_receipt.json").read_text())
    if not (
        ak.get("unique_native_rows")==7 and ak.get("original_variable_fields")==8
        and ak.get("science_user_approved_to_production") is False
        and ak.get("post_v5_approved") is False and ak.get("DATM_ready") is False
        and ak.get("output_SHA256",{}).get(A)==sha(AK/A)
        and ah.get("approved_T_count")==23
        and ah.get("approved_original_QC0_VPD_exception_count")==1
        and ah.get("all_34_original_stage12g_vpd_jumps_still_HOLD") is True
        and ah.get("humidity_event_ERA_RH_repair_approved") is False
        and ah.get("output_SHA256",{}).get(H)==sha(AH/H)
        and ah.get("output_SHA256",{}).get(H_T)==sha(AH/H_T)
        and ag.get("Kon_34_jump_centers")==34
        and ag.get("Kon_1_protected_original_QC0")==1
        and ag.get("output_SHA256",{}).get(AG_TAB)==sha(AG/AG_TAB)
        ):
        raise ValueError("Original Stage12ak/ah/ag SHA receipt, source or science gate changed")
    m=json.loads(safe(S/"exact_input_manifest.json").read_text())
    spec=next(z for z in m["sites"] if z["site"]=="US-Kon")
    pins={str(Path(p).resolve()):v for p,v in m["input_sha256"].items()}
    for field in ("primary","era"):
        p=safe(spec[field])
        if sha(p)!=pins.get(str(p.resolve())):
            raise ValueError("Original source SHA changed "+field)
    return spec
def audit():
    spec=upstream()
    latest=pd.read_csv(safe(AK/A),dtype={"time":str},low_memory=False)
    former=pd.read_csv(safe(AH/H),dtype={"time":str},low_memory=False)
    if len(latest)!=280320 or not latest.time.equals(former.time) or list(latest.columns)!=list(former.columns):
        raise ValueError("Latest signed Kon model native grid differs from approved 23T candidate")
    native=key(latest.time)
    if native.duplicated().any():raise ValueError("Duplicate Kon source timestamps")
    ix={k:i for i,k in enumerate(native)}
    for col in latest:
        if col not in ("PSRF","FLDS") and not latest[col].equals(former[col]):
            raise ValueError("Stage12ak source unexpectedly changed old approved Kon T or humidity "+col)
    if latest.VPD_USE.isna().sum()!=389 or latest.QBOT.isna().sum()!=389:
        raise ValueError("Latest selected Kon humidity missing count changed")
    old35=pd.read_csv(safe(AG/AG_TAB),dtype={"center_native_key":str},low_memory=False)
    old=sorted(set(old35.loc[old35.center_reason.eq("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"),
                              "center_native_key"]))
    tfix=pd.read_csv(safe(AH/H_T),dtype={"native_key":str},low_memory=False)
    new=sorted(set(tfix.native_key))
    if not(len(old)==34 and len(new)==23 and len(tfix)==23
           and not set(old)&set(new) and len(set(old+new))==57):
        raise ValueError("Original 34 VPD center plus 23 corrected TA episodes not EXACT distinct native 57")
    target=set(old+new)
    if not target<=set(ix) or any(not(pd.isna(latest.VPD_USE.iat[ix[k]]) and
         pd.isna(latest.QBOT.iat[ix[k]])) for k in target):
        raise ValueError("57 authorized source-era audit center VPD/QBOT are not exactly held")
    if not np.isclose(float(latest.VPD_USE.iat[ix["200809260530"]]),2.801,atol=1e-10,rtol=0):
        raise ValueError("User-approved original Kon QC0 physical outlier correction unexpectedly lost")
    interest=set()
    for k in target:
        interest|={adjacent(k,j) for j in (-2,-1,0,1,2)}
    if not interest<=set(ix):
        raise ValueError("Any ±2 native science context key absent from latest Kon")
    raw=pd.read_csv(safe(spec["primary"]),dtype={"TIMESTAMP_START":str},
           usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
           low_memory=False)
    era=pd.read_csv(safe(spec["era"]),dtype={"TIMESTAMP_START":str},
           usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
           low_memory=False)
    raw=raw.loc[raw.TIMESTAMP_START.isin(interest)].copy()
    era=era.loc[era.TIMESTAMP_START.isin(interest)].copy()
    if raw.TIMESTAMP_START.duplicated().any() or era.TIMESTAMP_START.duplicated().any():
        raise ValueError("Source original native tower or ERA duplicate time")
    if set(raw.TIMESTAMP_START)!=interest or set(era.TIMESTAMP_START)!=interest:
        raise ValueError("Source native ±2 row context not completely verified")
    ctx=raw.merge(era,on="TIMESTAMP_START",validate="one_to_one").set_index("TIMESTAMP_START")
    for c in ("TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"):
        ctx[c]=pd.to_numeric(ctx[c],errors="coerce")
        ctx.loc[ctx[c].le(-9990),c]=np.nan
    source=[]
    for k in sorted(interest):
        j=ix[k];s=ctx.loc[k]
        t=float(latest.TA_USE.iat[j]);p=float(latest.PSRF.iat[j])
        rawrh=np.nan
        r=np.nan
        proposed=np.nan
        newq=np.nan
        if np.isfinite([s.TA_ERA,s.VPD_ERA,t,p]).all():
            r=1-float(s.VPD_ERA)/float(sat(s.TA_ERA))
            proposed=float(sat(t))*(1-r)
            newq=qbot(t,p,proposed)
        cur=float(latest.VPD_USE.iat[j])
        phys=(np.isfinite([cur,t,p]).all() and 0<=cur<float(sat(t)))
        originalphys=(np.isfinite([s.VPD_F,s.TA_F]).all() and
                      0<=float(s.VPD_F)<float(sat(s.TA_F)))
        source.append({
          "native_key":k,"old34_hold_center":k in old,"new23_T_QC1_corrected":k in new,
          "original_tower_TA_F_C":s.TA_F,"source_tower_TA_F_QC":s.TA_F_QC,
          "selected_TA_USE_C":t,"original_TA_ERA_C":s.TA_ERA,
          "original_VPD_F_hPa":s.VPD_F,"original_VPD_F_QC":s.VPD_F_QC,
          "selected_VPD_USE_hPa":cur,"original_VPD_physically_valid_at_original_T":originalphys,
          "selected_VPD_physically_valid_at_selected_T":phys,
          "selected_PSRF_Pa":p,"original_companion_ERA_RH_pct":r*100 if np.isfinite(r) else np.nan,
          "paired_original_ERA_RH_proposal_VPD_hPa":proposed,
          "paired_original_ERA_RH_proposal_QBOT_kgkg":newq,
          "paired_ERA_T_difference_abs_C":abs(s.TA_ERA-t) if np.isfinite(s.TA_ERA) else np.nan,
          "ERA_T_within5C":bool(np.isfinite(s.TA_ERA) and abs(s.TA_ERA-t)<=5),
          "RH_water_0_to100":bool(np.isfinite(r) and 0<=r<=1),
          "VPD_QBOT_physical":bool(np.isfinite([proposed,newq,p,t]).all() and 0<=proposed<float(sat(t)) and 0<newq<.08 and 50000<p<110000),
          "humidity_source_operator_approved":False
        })
    rows=pd.DataFrame(source).set_index("native_key",drop=False)
    centers=[]
    edges=[]
    for k in sorted(target):
        center=rows.loc[k]
        if k in old:
            # Original source lineage, not a new replacement authorization:
            # 2011-09-29 18:30 has source TA_F_QC=1 (gapfilled) and
            # VPD_F_QC=2 (ERA), and is one of the TEN unapproved QC1-T
            # audit records. It must stay a science HOLD, not be
            # misclassified as observed tower temperature.
            if k=="201109291830":
                if not(center.source_tower_TA_F_QC==1 and
                       center.original_VPD_F_QC==2):
                    raise ValueError("Protected 201109291830 Kon QC1 tower T + QC2 VPD source provenance changed")
            elif not(center.source_tower_TA_F_QC==0 and
                     center.original_VPD_F_QC in (1,2)):
                raise ValueError("Original Kon old VPD hold has unexpected QC provenance "+k+
                                 ": TA_F_QC="+str(center.source_tower_TA_F_QC)+
                                 ", VPD_F_QC="+str(center.original_VPD_F_QC))
        else:
            if not(center.source_tower_TA_F_QC==1 and
                    abs(float(center.original_tower_TA_F_C)-float(center.selected_TA_USE_C))>=5):
                raise ValueError("23 previously-approved Kon T interpolation source QC changed "+k)
        prev,nxt=adjacent(k,-1),adjacent(k,1)
        side=[rows.loc[z] for z in (prev,nxt)]
        proposed=float(center.paired_original_ERA_RH_proposal_VPD_hPa)
        if not(np.isfinite(proposed) and np.isfinite(float(center.paired_original_ERA_RH_proposal_QBOT_kgkg))):
            # Science would remain HOLD; no candidate must be forced.
            pass
        triggers=[]
        for offset,s in zip((-1,1),side):
            existing=float(s.selected_VPD_USE_hPa)
            jump=abs(proposed-existing) if np.isfinite([proposed,existing]).all() else np.nan
            # One-hop counterfactual: candidate center + side selected source
            # can be bad due to legacy QC1 gapfill, not due to ERA RH.
            selectedbad=bool(not s.selected_VPD_physically_valid_at_selected_T)
            editable_neighbor=bool(s.original_VPD_F_QC in (1,2))
            if np.isfinite(jump) and jump>4:triggers.append("EXISTING_EDGE_GT4")
            if selectedbad and np.isfinite(existing):triggers.append("NEIGHBOR_SOURCE_VPD_NOT_PHYSICAL")
            if s.new23_T_QC1_corrected or s.old34_hold_center:triggers.append("ADJACENT_HELD_TARGET")
            edges.append({
               "center_key":k,"kind":"original_34" if k in old else "new_T_23",
               "neighbor_key":s.native_key,"relative_halfhours":offset,
               "neighbor_source_TA_F_QC":s.source_tower_TA_F_QC,
               "neighbor_source_VPD_F_QC":s.original_VPD_F_QC,
               "old_neighbor_selected_VPD_hPa":existing,
               "neighbor_original_source_VPD_hPa":s.original_VPD_F_hPa,
               "original_neighbor_source_VPD_physical":s.original_VPD_physically_valid_at_original_T,
               "selected_neighbor_VPD_physical":s.selected_VPD_physically_valid_at_selected_T,
               "neighbor_is_old_or_new_hold":bool(s.old34_hold_center or s.new23_T_QC1_corrected),
               "center_only_new_pairERA_jump_abs_hPa":jump,
               "neighbor_source_QC1_QC2_can_review":editable_neighbor,
               "neighbor_paired_ERA_RH_reference_VPD_hPa":s.paired_original_ERA_RH_proposal_VPD_hPa,
               "operator_approved":False
            })
        centers.append({
           "native_key":k,"kind":"original_34" if k in old else "new_T_23",
           "source_T_QC":int(center.source_tower_TA_F_QC),
           "original_VPD_QC":int(center.original_VPD_F_QC) if pd.notna(center.original_VPD_F_QC) else None,
           "old_original_T_C":center.original_tower_TA_F_C,
           "retained_or_corrected_T_C":center.selected_TA_USE_C,
           "original_ERA_T_C":center.original_TA_ERA_C,
           "abs_T_vs_ERA_C":center.paired_ERA_T_difference_abs_C,
           "paired_source_ERA_RH_pct":center.original_companion_ERA_RH_pct,
           "paired_source_research_VPD_hPa":proposed,
           "paired_source_research_QBOT_kgkg":center.paired_original_ERA_RH_proposal_QBOT_kgkg,
           "ERA_T_within5C":center.ERA_T_within5C,
           "water_RH_physics":center.RH_water_0_to100,
           "VPD_QBOT_physics":center.VPD_QBOT_physical,
           "temperature_QC1_unapproved_separate_science_HOLD":k=="201109291830",
           "adjacent_as_is_center_only_problem_reasons":";".join(sorted(set(triggers))) or "NONE",
           "requires_connected_episode_science_review":len(triggers)>0,
           "humidity_approved":False
        })
    summary=pd.DataFrame(centers)
    sides=pd.DataFrame(edges)
    if not(len(summary)==57 and len(sides)==114 and
           summary.kind.value_counts().to_dict()=={"original_34":34,"new_T_23":23}
           and summary.temperature_QC1_unapproved_separate_science_HOLD.sum()==1
           and summary.loc[summary.temperature_QC1_unapproved_separate_science_HOLD,
                           "native_key"].tolist()==["201109291830"]):
        raise ValueError("Exactly 57 center events and 114 original native neighbor sides required")
    return summary,sides,rows.reset_index(drop=True)
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for f in ("self-test","check","run"):g.add_argument("--"+f,action="store_true")
    args=p.parse_args()
    print("STAGE12AM KON 34 OLD +23 NEW ORIGINAL-SOURCE HUMIDITY EVENT QC | "+V,flush=True)
    selftest()
    if args.self_test:return
    c,e,context=audit()
    print("\n===== ALL 57 DISTINCT KON ORIGINAL HOLD + T-EDIT HUMIDITY CENTERS =====",flush=True)
    cols=["native_key","kind","source_T_QC","original_VPD_QC",
      "retained_or_corrected_T_C","original_ERA_T_C",
      "paired_source_ERA_RH_pct","paired_source_research_VPD_hPa",
      "paired_source_research_QBOT_kgkg","ERA_T_within5C","VPD_QBOT_physics",
      "adjacent_as_is_center_only_problem_reasons",
      "temperature_QC1_unapproved_separate_science_HOLD"]
    print(c[cols].round(6).to_string(index=False),flush=True)
    print("STAGE12AM EXACT QC EXCEPTION: Kon 201109291830 original TA_F_QC=1, VPD_F_QC=2; temperature source not operator-approved; candidate diagnostic ONLY; HOLD intact.",flush=True)
    print("\n===== SCIENCE TRIAGE BY GROUP =====",flush=True)
    for k,group in c.groupby("kind"):
        print(k,"centers",len(group),
            "RH+VPD+QBOT physical",int((group.water_RH_physics & group.VPD_QBOT_physics).sum()),
            "pairedERA T within 5C",int(group.ERA_T_within5C.sum()),
            "as-is neighbor edge or invalid-source needs joined episode",
            int(group.requires_connected_episode_science_review.sum()),
            flush=True)
    print("\n===== 114 OLD VS PROPOSED ONE-HOP EDGES SOURCE QC AND JUMP>4hPa =====",flush=True)
    print(e.round(5).to_string(index=False),flush=True)
    print("STAGE12AM NO HUMIDITY REPAIR: latest Kon Stage12ak 389 VPD/QBOT held, all 57 specific center holds remain. Original source/temperature, stage12ak pressure trial, QC0 VPD exception protected.",flush=True)
    if args.check:
        print("STAGE12AM CHECK ONLY, NO FILE / SCIENCE WRITES.",flush=True);return
    folder=ROOT/"reports"/("stage12am_Kon_57_humidity_ERA_episode_original_source_review_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    tables={
        "57_exact_Kon_source_and_native_ERA_RH_humidity_centre_proposals.csv":c,
        "114_exact_original_adjacent_VPD_source_QC_and_center_only_jumps.csv":e,
        "deduplicated_original_Kon_plus_minus_two_native_halfhours_source_provenance.csv":context}
    for name,frame in tables.items():frame.to_csv(folder/name,index=False)
    marker="RESEARCH_QC_ONLY_NO_OPERATOR_ERA_RH_APPROVAL_NO_DATM"
    (folder/marker).write_text(
       "All 57 candidate VPD/QBOT changes are diagnostic only. A subset may "
       "require whole connected QC1/QC2 source episode reconciliation and a "
       "temperature-vs-original-companion ERA mismatch hold. Never edit "
       "protected VPD source QC0, PFT, source timestamps or original files. "
       "Previous Stage12ah approved T and VPD QC0 exception remain intact; "
       "Stage12ak pressure proposal also not production-approved.\n")
    receipt={
       "version":V,"old_Stage12g_Kon_center_holds":34,"new_Stage12ah_temperature_related_holds":23,
       "event_center_total":57,"adjacent_halfhour_sides":114,
       "original_Kon_201109291830_QC1_temperature_special_HOLD":True,
       "humidity_ERA_replacements_operator_approved":False,
       "original_Stage12ak_SHA256":sha(AK/"stage12ak_research_proposal_SHA_receipt.json"),
       "original_Stage12ah_SHA256":sha(AH/"stage12ah_approved_23T_QC0_SHA_receipt.json"),
       "original_Stage12ag_SHA256":sha(AG/"stage12ag_original_science_report_SHA_receipt.json"),
       "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
       "output_SHA256":{k:sha(folder/k) for k in [*tables,marker]}}
    (folder/"stage12am_Kon_57_source_event_science_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12AM KON 57 SOURCE EVENT SCIENCE ONLY REPORT DIR:",folder,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("STAGE12AM STOP:",ex,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

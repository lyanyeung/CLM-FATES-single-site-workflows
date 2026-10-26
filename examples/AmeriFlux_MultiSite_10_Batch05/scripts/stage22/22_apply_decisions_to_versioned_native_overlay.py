#!/usr/bin/env python3
"""Batch05 Stage22: APPLY investigator's approved RH+VPD changes to a NEW native overlay.

Inputs: unmodified Stage18 source reports, successful Stage20 117 candidates,
and successful Stage21 57 P1 triage. Produces an authoritative VERSIONED
SCIENTIFIC OVERLAY (162 new RH/VPD candidate pairs), separate HOLD ledger,
and native half-hour discontinuity checks.

Original tower CSV, all previous reports, source QC codes, DATM forcing,
CIME cases and Slurm are NEVER written or submitted by this program.
No unapproved time rows are added. Overlay alone is NOT model-ready forcing.
FLUXMET processed TA_ERA / VPD_ERA are NOT independent ERA5-Land downloads.
"""
import argparse
import csv
import json
import math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

ORIG={"site","time_native","is_P1","TA_F_C","VPD_F_hPa","RH_original_pct",
      "TA_F_QC","VPD_F_QC","TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_water_pct"}
C20={"site","time_native","decision_group","decision_scope","TA_F_C_original",
     "VPD_F_hPa_original","candidate_RH_pct","candidate_VPD_hPa_with_original_TA"}
H20={"site","time_native","group","reason"}
R21={"class","site","time_native","TA_F_C","TA_F_QC","VPD_F_hPa",
     "VPD_F_QC","RH_original_pct","ERA_RH_Magnus_water_pct",
     "proposed_RH_pct","proposed_VPD_hPa"}
EDGE21={"boundary","site","time_native","phase","original_VPD_hPa",
        "selected_VPD_hPa"}
OVERLAY_COLS=("site","native_time","source_cohort","decision_id",
 "source_TA_C","source_TA_QC","source_VPD_hPa","source_VPD_QC",
 "source_RH_pct","source_processed_ERA_T_C","source_processed_ERA_VPD_hPa",
 "source_processed_ERA_RH_derived_pct",
 "modified_TA_C","modified_RH_pct","modified_VPD_hPa",
 "delta_VPD_hPa","replacement_RH_provenance","new_VPD_derivation",
 "source_QC_provenance_only","overlay_status")
HOLD_COLS=("site","native_time","hold_reason","group","original_TA_C",
 "original_VPD_hPa","original_RH_pct","TA_QC","VPD_QC",
 "processed_ERA_RH_pct","action")
BOUNDARIES=(
 ("WCr_start","US-WCr","202508251230","202508251300"),
 ("WCr_end","US-WCr","202508260130","202508260200"),
 ("Vcm_Oct2025_end","US-Vcm","202510141100","202510141130")
)

def num(x):
    try:
        n=float(x)
        if math.isfinite(n) and n not in (-9999.0,-6999.0):return n
    except (ValueError,TypeError):pass
    return None

def saturation(t):
    if t is None or not -80<=t<=60:raise ValueError("nonphysical or missing air temperature")
    return 6.112*math.exp(17.67*t/(t+243.5))

def rh_of(t,v):
    return 100*(1-v/saturation(t))

def native_dt(s):
    if len(s)!=12 or not s.isdigit():raise ValueError("invalid native timestamp "+repr(s))
    return datetime.strptime(s,"%Y%m%d%H%M")

def native_fmt(d):
    return d.strftime("%Y%m%d%H%M")

def read_csv(f,needed):
    if not f.is_file() or f.is_symlink():raise ValueError("missing or symlink file "+str(f))
    with f.open("r",encoding="utf-8-sig",newline="") as h:
        rd=csv.DictReader(h)
        if not needed.issubset(rd.fieldnames or []) or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError("source columns missing/duplicate "+str(f))
        rows=list(rd)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("bad source CSV row "+str(f))
    return rows

def index(rows):
    x={}
    for row in rows:
        k=row["site"],row["time_native"]
        native_dt(k[1])
        if k in x:raise ValueError("duplicate original source key "+str(k))
        x[k]=row
    return x

def original_reports(d18,d20,d21):
    s18=json.loads((d18/"stage18_summary.json").read_text())
    s20=json.loads((d20/"stage20_summary.json").read_text())
    s21=json.loads((d21/"stage21_summary.json").read_text())
    if (s18.get("P1_original_HH"),s18.get("context_rows"),s18.get("science_approved"))!=(176,775,0):
        raise ValueError("original Stage18 summary changed")
    if (s20.get("candidate_rows"),s20.get("unresolved_rows"),s20.get("forcing_written"))!=(117,34,False):
        raise ValueError("original Stage20 summary changed")
    if (s21.get("remaining_p1"),s21.get("remaining_measured"),
        s21.get("remaining_era_source_RH_present"),
        s21.get("remaining_era_source_RH_missing"))!=(57,44,11,2):
        raise ValueError("Stage21 source split changed")
    context=index(read_csv(d18/"stage18_all_p1_original_6hour_context.csv",ORIG))
    p1=index(read_csv(d18/"stage18_all_p1_original_flagged_HH.csv",ORIG))
    c20=index(read_csv(d20/"stage20_approved_scope_candidate_TA_RH_VPD.csv",C20))
    h20=index(read_csv(d20/"stage20_original_RH_missing_and_QC1_context_holds.csv",H20))
    r21=index(read_csv(d21/"stage21_remaining_57_original_ERA_candidate_comparison.csv",R21))
    edges=read_csv(d21/"stage21_three_boundaries_before_after.csv",EDGE21)
    if tuple(map(len,(context,p1,c20,h20,r21,edges)))!=(775,176,117,34,57,6):
        raise ValueError("Stage18-21 original cohort count mismatch")
    if not set(p1).issubset(context):
        raise ValueError("Stage18 original P1 not in contexts")
    if not set(c20).issubset(context) or not set(r21).issubset(p1):
        raise ValueError("candidate source keys not in native originals")
    if set(c20)&set(h20) or set(c20)&set(r21) or set(h20)&set(r21):
        raise ValueError("duplicate candidate/hold/remaining key")
    if len(set(p1)-set(c20)-set(h20)-set(r21))!=0:
        raise ValueError("original 176 P1 partition not complete")
    return context,p1,c20,h20,r21,edges

def check_source(r,ta,rh,vpd,source_label):
    if ta is None or rh is None or vpd is None or not (0<=rh<=100):
        raise ValueError("candidate outside physical RH [0,100] "+str(r))
    if not 0<=vpd<=saturation(ta)+1e-7:
        raise ValueError("candidate outside VPD physical range "+str(r))
    if abs(rh_of(ta,vpd)-rh)>1.1e-5:
        raise ValueError("candidate pair incoherent "+str(r))
    if source_label=="SOURCE_PROCESSED_ERA_RH":
        expected=num(r["ERA_RH_Magnus_water_pct"])
        if expected is None or abs(expected-rh)>1.2e-5:
            raise ValueError("source ERA RH changed "+str(r))
    if source_label=="ORIGINAL_NATIVE_RH":
        raw=num(r["RH_original_pct"])
        if raw is None or abs(raw-rh)>1.2e-5:
            raise ValueError("original RH changed "+str(r))
    # Pin original T and original VPD to source Stage18, not to chosen ERA.
    return True

def merge(context,p1,c20,h20,r21):
    chosen={}
    hold={}
    n=Counter()
    def insert(k,r,rh,vpd,group,src,cohort):
        if k in chosen or k in hold:
            raise ValueError("double-application or hold conflict "+str(k))
        original=context[k]
        ta=num(original["TA_F_C"])
        old_vpd=num(original["VPD_F_hPa"])
        if ta is None or old_vpd is None:raise ValueError("missing source TA/VPD "+str(k))
        # Stage20 candidates were rounded to 7 decimal hPa and Stage21 to
        # 6 decimals. At -15 C the latter can change inferred RH by
        # 0.00002 percentage points: more than Stage22's strict identity
        # threshold despite a physically correct source value.
        #
        # Verify the supplied rounded proposal against the authoritative
        # original RH source. Then use FULL source RH precision to recompute
        # VPD, rather than validating the CSV's rounded VPD as exact.
        native_rh=(num(original["RH_original_pct"]) if src=="ORIGINAL_NATIVE_RH"
                   else num(original["ERA_RH_Magnus_water_pct"]))
        if native_rh is None or rh is None or vpd is None:
            raise ValueError("missing source RH or original candidate "+str(k))
        if abs(rh-native_rh)>1.2e-5:
            raise ValueError("rounded candidate RH disagrees with original RH source "+str(k))
        exact_vpd=saturation(ta)*(1-native_rh/100)
        if abs(vpd-exact_vpd)>2.0e-6:
            raise ValueError("rounded proposed VPD disagrees with source-derived VPD "+str(k))
        rh=native_rh
        vpd=exact_vpd
        check_source(original,ta,rh,vpd,src)
        chosen[k]=dict(site=k[0],native_time=k[1],source_cohort=cohort,
           decision_id=group,source_TA_C=original["TA_F_C"],
           source_TA_QC=original["TA_F_QC"],source_VPD_hPa=original["VPD_F_hPa"],
           source_VPD_QC=original["VPD_F_QC"],
           source_RH_pct=original["RH_original_pct"],
           source_processed_ERA_T_C=original["TA_ERA_C"],
           source_processed_ERA_VPD_hPa=original["VPD_ERA_hPa"],
           source_processed_ERA_RH_derived_pct=original["ERA_RH_Magnus_water_pct"],
           modified_TA_C=original["TA_F_C"],
           modified_RH_pct=round(rh,9),
           modified_VPD_hPa=round(vpd,10),
           delta_VPD_hPa=round(vpd-old_vpd,10),
           replacement_RH_provenance=src,
           new_VPD_derivation="MAGNUS_WATER_SOURCE_SELECTED_TA",
           source_QC_provenance_only="ORIGINAL_SOURCE_QC_UNCHANGED_IN_AUDIT_NOT_RENEWED_MEASUREMENT",
           overlay_status="APPROVED_APPLIED_TO_NEW_OVERLAY_NOT_NATIVE_SOURCE_OR_DATM")
        n[group]+=1

    for k,r in sorted(c20.items()):
        original=context[k]
        if abs(num(r["TA_F_C_original"])-num(original["TA_F_C"]))>0.002 or abs(
            num(r["VPD_F_hPa_original"])-num(original["VPD_F_hPa"]))>0.002:
            raise ValueError("Stage20 target not original Stage18 source "+str(k))
        src=("ORIGINAL_NATIVE_RH" if r["decision_group"]=="G03_Vcm_Jan2007"
             else "SOURCE_PROCESSED_ERA_RH")
        cohort="P1_FLAGGED" if k in p1 else "USER_APPROVED_TRANSITION_OR_QC1"
        insert(k,r,num(r["candidate_RH_pct"]),
               num(r["candidate_VPD_hPa_with_original_TA"]),
               r["decision_group"],src,cohort)

    for k,r in sorted(h20.items()):
        orig=context[k]
        hold[k]=dict(site=k[0],native_time=k[1],
                     hold_reason="PRIOR_RH_MISSING_OR_NONPHYSICAL_ERA",
                     group=r["group"],original_TA_C=orig["TA_F_C"],
                     original_VPD_hPa=orig["VPD_F_hPa"],
                     original_RH_pct=orig["RH_original_pct"],
                     TA_QC=orig["TA_F_QC"],VPD_QC=orig["VPD_F_QC"],
                     processed_ERA_RH_pct=orig["ERA_RH_Magnus_water_pct"],
                     action="USER_MANUAL_REVIEW_NO_AUTO_REPAIR")

    for k,r in sorted(r21.items()):
        cls=r["class"]
        if cls=="A" and k[1].startswith("2015"):
            why="MANUAL_HOLD_2015_ERA_T_MISMATCH_AND_ERA_RH_UNDER10"
        elif cls=="C":
            why="MANUAL_HOLD_ORIGINAL_RH_MISSING_ERA_PAIR_INVALID"
        elif cls in ("A","B"):
            orig=context[k]
            if any(r[c]!=orig[c] for c in ("TA_F_C","VPD_F_hPa","TA_F_QC",
                                            "VPD_F_QC","RH_original_pct")):
                raise ValueError("Stage21 source not identical to Stage18 "+str(k))
            src=("SOURCE_PROCESSED_ERA_RH" if cls=="A" else "ORIGINAL_NATIVE_RH")
            insert(k,r,num(r["proposed_RH_pct"]),num(r["proposed_VPD_hPa"]),
                   "STAGE21_A_EXCEPT_2015" if cls=="A" else "STAGE21_B_NATIVE_RH",
                   src,"P1_FLAGGED")
            continue
        else:
            raise ValueError("Unexpected Stage21 class "+cls)
        orig=context[k]
        hold[k]=dict(site=k[0],native_time=k[1],
            hold_reason=why,group="STAGE21_"+cls,
            original_TA_C=orig["TA_F_C"],original_VPD_hPa=orig["VPD_F_hPa"],
            original_RH_pct=orig["RH_original_pct"],
            TA_QC=orig["TA_F_QC"],VPD_QC=orig["VPD_F_QC"],
            processed_ERA_RH_pct=orig["ERA_RH_Magnus_water_pct"],
            action="USER_MANUAL_REVIEW_NO_AUTO_REPAIR")

    if len(chosen)!=162 or len(hold)!=46:
        raise ValueError("expected 162 approved / 46 manual holds: "+str((len(chosen),len(hold))))
    if n["STAGE21_A_EXCEPT_2015"]!=34 or n["STAGE21_B_NATIVE_RH"]!=11:
        raise ValueError("approved Stage21 scope mismatch "+str(n))
    if len(chosen.keys() & p1.keys())!=130 or len(hold.keys() & p1.keys())!=46:
        raise ValueError("P1 176 partition=130 approved + 46 holds failed")
    if set(hold)&set(chosen):raise ValueError("manual hold accidentally edited")
    return chosen,hold,n

def boundaries(context,chosen):
    """Checks every APPROVED overlay segment edge, and preserves 3 explicit HOLD edges."""
    stamps=defaultdict(set)
    for (site,t) in chosen:
        stamps[site].add(t)
    records=[]
    explicit=set((site,a,b) for _,site,a,b in BOUNDARIES)
    for site,times in stamps.items():
        for tm in sorted(times):
            now=native_dt(tm)
            prev=native_fmt(now-timedelta(minutes=30))
            nex=native_fmt(now+timedelta(minutes=30))
            for before,after in ((prev,tm),(tm,nex)):
                key1,key2=(site,before),(site,after)
                if key1 not in context or key2 not in context:
                    continue # Outside proven Stage18 context: no fabricated interval.
                if (key1 in chosen)==(key2 in chosen):
                    continue # Boundary check only when transitioning overlay->original.
                v1=num(chosen[key1]["modified_VPD_hPa"]) if key1 in chosen else num(context[key1]["VPD_F_hPa"])
                v2=num(chosen[key2]["modified_VPD_hPa"]) if key2 in chosen else num(context[key2]["VPD_F_hPa"])
                if v1 is None or v2 is None:raise ValueError("boundary missing VPD")
                j=v2-v1
                records.append(dict(site=site,start_native=before,end_native=after,
                   start_status="APPROVED_OVERLAY" if key1 in chosen else "ORIGINAL_UNMODIFIED",
                   end_status="APPROVED_OVERLAY" if key2 in chosen else "ORIGINAL_UNMODIFIED",
                   start_TA_C=context[key1]["TA_F_C"],end_TA_C=context[key2]["TA_F_C"],
                   start_source_RH_pct=context[key1]["RH_original_pct"],
                   end_source_RH_pct=context[key2]["RH_original_pct"],
                   start_processed_ERA_RH_pct=context[key1]["ERA_RH_Magnus_water_pct"],
                   end_processed_ERA_RH_pct=context[key2]["ERA_RH_Magnus_water_pct"],
                   start_selected_VPD_hPa=round(v1,7),end_selected_VPD_hPa=round(v2,7),
                   jump_VPD_hPa=round(j,7),
                   over_4hPa_30min=abs(j)>4,
                   explicitly_held_for_manual_review=(site,before,after) in explicit))
    # unique boundary signatures (neighbors can be visited from both approved keys)
    uniq={}
    for row in records:
        k=row["site"],row["start_native"],row["end_native"]
        if k in uniq and uniq[k]!=row:raise ValueError("boundary conflict")
        uniq[k]=row
    for site,a,b in explicit:
        if (site,a,b) not in uniq:
            raise ValueError("expected explicit hold boundary not checked "+str((site,a,b)))
    return sorted(uniq.values(),key=lambda r:(r["site"],r["start_native"]))

def write_csv(path,fields,rows):
    with path.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def selftest():
    assert round(rh_of(10,saturation(10)*(1-67/100)),8)==67.0
    assert round(rh_of(-15,saturation(-15)*(1-88/100)),8)==88.0
    assert len(BOUNDARIES)==3
    # Actual Stage21 error reproduction, source US-Vcm 2008-01-16 21:00:
    # saving VPD as 0.222795 (6 decimals) at -14.802 C makes the
    # inferred RH differ from 88.56054 by ~2.34e-5 percentage points.
    t=-14.802
    source_rh=88.56054
    exact_vpd=saturation(t)*(1-source_rh/100)
    stage21_six_digits=round(exact_vpd,6)
    assert abs(rh_of(t,stage21_six_digits)-source_rh)>1.1e-5
    assert abs(stage21_six_digits-exact_vpd)<2.0e-6
    check_source({"RH_original_pct":str(source_rh)},t,source_rh,
                 exact_vpd,"ORIGINAL_NATIVE_RH")
    print("STAGE22 SELF-TEST PASS | six-decimal Stage21 roundoff correctly reconstructed using source RH; physical constraints unchanged; no source writes")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--stage18-dir",type=Path)
    ap.add_argument("--stage20-dir",type=Path)
    ap.add_argument("--stage21-dir",type=Path)
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    if a.self_test:selftest();return
    if not all((a.stage18_dir,a.stage20_dir,a.stage21_dir,a.out)):
        ap.error("all of --stage18-dir --stage20-dir --stage21-dir --out required")
    sources=[v.expanduser().resolve() for v in (a.stage18_dir,a.stage20_dir,a.stage21_dir)]
    out=a.out.expanduser().resolve()
    if (not all(p.is_dir() for p in sources) or not out.parent.is_dir() or out.exists()
        or any(out==p or out in p.parents or p in out.parents for p in sources)):
        ap.error("new disjoint output location and existing source report dirs required")
    orig,p1,c20,h20,r21,edges=original_reports(*sources)
    chosen,held,counts=merge(orig,p1,c20,h20,r21)
    boundaries_all=boundaries(orig,chosen)
    hard=[r for r in boundaries_all if r["over_4hPa_30min"]]
    summary={
      "science_revision":"STAGE22_USER_APPROVED_NON_HOLD_APPLICATION",
      "original_input_files_unchanged":True,
      "FLUXMET_written":False,"DATM_forcing_written":False,"Slurm_submitted":False,
      "candidate_overlay_is_full_model_forcing":False,
      "approved_modified_RH_VPD_native_half_hours":162,
      "source_original_TA_preserved_at_all_overlays":True,
      "prior_stage20_modified":117,
      "new_stage21_A_ERA_RH_excluding_2015":34,
      "new_stage21_B_original_RH":11,
      "hold_original_P1_half_hours":46,
      "P1_original_176_partition":{"approved_P1":130,"held_P1":46},
      "extra_approved_nonP1_transitions":32,
      "three_explicit_edges_unmodified":True,
      "edge_checks":len(boundaries_all),"edge_jumps_abs_gt4hPa":len(hard),
      "science_unapproved_P2_P3_not_touched":True,
      "processed_ERA_reference_independent_ERA5_Land":False,
      "new_candidates_by_decision":dict(counts),
      "requires_additional_full_cohort_science_QC_before_DATM":True
    }
    out.mkdir(exist_ok=False)
    write_csv(out/"stage22_VERSIONED_APPROVED_RH_VPD_native_overlay.csv",
              OVERLAY_COLS,[chosen[k] for k in sorted(chosen)])
    write_csv(out/"stage22_46_MANUAL_HOLD_P1_untouched.csv",
              HOLD_COLS,[held[k] for k in sorted(held)])
    if boundaries_all:
        write_csv(out/"stage22_all_overlay_boundary_transitions.csv",
                  list(boundaries_all[0]),boundaries_all)
    (out/"stage22_manifest.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    lines=[
      "# Stage22 investigator-approved native RH/VPD overlay",
      "","**APPLIED only to NEW versioned overlay, NOT source/forcing.**",
      "Original FLUXMET rows and QC0/1/2 remain untouched.",
      "Candidate changed humidity and VPD are reconstructed; do not label them measured QC0.",
      "Approved: Stage20=117 + Stage21 A excluding 2015=34 + B original RH=11 = **162**.",
      "Manual HOLD: previous missing source RH=34 + A2015=10 + CmissingRH=2 = **46**.",
      "Original 176 P1 = approved 130 + held 46; additional 32 approved transition/QC1 rows.",
      "Do not automatically expand or repair three explicit user-review boundaries.",
      "Original source processed ERA counterpart is not independent ERA5-Land.",
      "Stage17 P2/P3 remain unapproved; no DATM or model jobs should be run.","",
      "## Manual boundary review",
      "| site | before | after | selected VPD jump hPa |",
      "|---|---|---|---:|"]
    for row in boundaries_all:
        if row["explicitly_held_for_manual_review"]:
            lines.append("| {} | {} | {} | {:.3f} |".format(
                row["site"],row["start_native"],row["end_native"],
                row["jump_VPD_hPa"]))
    lines+=["","Additional native boundary jumps >4hPa: "+str(len(hard))+".",
            "Exact additional transitions: stage22_all_overlay_boundary_transitions.csv.",
            "All HOLD timestamps: stage22_46_MANUAL_HOLD_P1_untouched.csv."]
    (out/"STAGE22_OPERATOR_REVIEW.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("STAGE22 APPROVED_OVERLAY 162 = Stage20 117 + Stage21 A non2015 34 + Stage21 B 11")
    print("STAGE22 HUMAN_HOLD 46 = prior 34 + Stage21 A2015 10 + C missing 2")
    print("STAGE22 P1_TOTAL 176 = approved 130 + held 46; extra nonP1 transitions 32")
    print("STAGE22 OVERLAY_EDGE_CHECKS",len(boundaries_all),
          "JUMPS_GT4hPa",len(hard),flush=True)
    for row in boundaries_all:
        if row["explicitly_held_for_manual_review"]:
            print("STAGE22 MANUAL_EDGE",row["site"],row["start_native"],
                  row["end_native"],"post_candidate_delta_VPD_hPa",
                  row["jump_VPD_hPa"],flush=True)
    print("STAGE22_OUTPUT="+str(out))
    print("STAGE22 SUCCESS: new overlay/HOLD/audit files only. Original FLUXMET=UNCHANGED,"
          " DATM=UNCHANGED, model jobs=NONE.")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Stage94: exact, concise science decision brief for REAL Stage93 10-site QC0 events.

Read only verified Stage93 122 original QC0 changes grouped as 30 native
episodes. Audit source/decision row identity, print original/candidate/ERA/
native neighbors, compare physical plausibility, and supply an editable
operator decision template. This NEVER grants science approval or edits
original sources/forcing/NC/CIME/Slurm. The separate Ho1 QC1/QC2 source
temperature transition is also printed and left pending.

Run --self-test / --check / --audit. Only --audit writes a NEW report folder.
"""
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S93=ROOT/"reports/stage93_ten_site_postv5_QC0_manual_triage_20261026T025946Z_97c41d3b"
F_QC="all_122_QC0_original_source_candidate_nearest_neighbors.csv"
F_EP="QC0_human_review_priority_episodes.csv"
F_HO1="US-Ho1_2000_temperature_QC_transition_boundary.csv"
QC_COUNT={"US-BZS":1,"US-CMW":2,"US-EML":3,"US-GLE":0,
          "US-Ha1":2,"US-Ho1":5,"US-Ho2":19,"US-Ho3":0,
          "US-ICh":0,"US-ICt":90}
ALLOWED=("APPROVE_CANDIDATE","KEEP_ORIGINAL","USE_VERIFIED_ALTERNATIVE","HOLD")
FIELDS=("decision_id","site","variable","start_local","end_local","native_records",
        "original_range","candidate_range","ERA_range",
        "raw_first_neighbor","raw_last_neighbor","largest_abs_change",
        "original_RH_range","evidence_class","scientific_recommendation",
        "manual_attention","operator_choice","production_approved","reason")

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def records(p):
    with open(p,newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))
def fl(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else float("nan")
    except (ValueError,TypeError):return float("nan")
def finite(v):return math.isfinite(fl(v))
def rng(items,field):
    vals=[fl(r.get(field)) for r in items]
    ok=sorted(x for x in vals if math.isfinite(x))
    return ("NA" if not ok else "%.4f..%.4f"%(ok[0],ok[-1]))
def one(v):return "NA" if not finite(v) else "%.4f"%fl(v)
def positive_relative_humidity_from_vpd(t,v):
    if not finite(t) or not finite(v):return False
    t,v=fl(t),fl(v)
    if not -80<t<65:return False
    es=6.112*math.exp(17.67*t/(t+243.5))
    return v>=0 and v<es

def gate():
    manifest=json.loads((S93/"manifest.json").read_text())
    expect={
       "schema":"STAGE93_TEN_SITE_UNIFIED_POSTV5_AND_ORIGINAL_QC0_TRIAGE_v1",
       "numerically_reviewed_sites":10,"site_failures":0,
       "expected_annual_NC":215,"original_QC0_changed_variable_records":122,
       "production_DATM_approved":False}
    for k,v in expect.items():
        if manifest.get(k)!=v:raise ValueError("Stage93 verified review state differs: "+k)
    for fn,digest in manifest["out_sha256"].items():
        if sha(S93/fn)!=digest:
            raise ValueError("Stage93 original report SHA mismatch "+fn)
    qc=records(S93/F_QC)
    ep=records(S93/F_EP)
    ho1=records(S93/F_HO1)
    if len(qc)!=122 or len(ep)!=30 or len(ho1)!=8:
        raise ValueError("Expected Stage93 122 raw-QC0 records, 30 episodes, 8 Ho1 boundaries")
    if Counter(x["site"] for x in qc)!=Counter({k:v for k,v in QC_COUNT.items() if v}):
        raise ValueError("Original source QC0 changes-by-site count differs")
    lookup=defaultdict(list)
    for r in qc:
        if str(r.get("source_QC","")) not in ("0","0.0"):
            raise ValueError("Stage93 source QC0 provenance was mislabeled")
        key=(r["site"],r["variable"],r["time"])
        if key in lookup:raise ValueError("Repeated original QC0 source variable record")
        lookup[key].append(r)
    covered=set()
    ordered=[]
    for i,e in enumerate(ep,1):
        site,var=e["site"],e["variable"]
        if site not in QC_COUNT:raise ValueError("Episode site is not in Batch02")
        start=datetime.fromisoformat(e["first"])
        end=datetime.fromisoformat(e["last"])
        if start>end:raise ValueError("Episode clock sequence invalid")
        rows=sorted((x for x in qc if x["site"]==site and x["variable"]==var
                     and start<=datetime.fromisoformat(x["time"])<=end),
                    key=lambda x:x["time"])
        if len(rows)!=int(e["native_records"]) or not rows:
            raise ValueError("Episode does not reconcile exactly to native QC0 rows "+site)
        if rows[0]["time"]!=e["first"] or rows[-1]["time"]!=e["last"]:
            raise ValueError("Episode boundaries differ from exact source rows")
        step=60 if site=="US-Ha1" else 30
        for prev,next_ in zip(rows,rows[1:]):
            if (datetime.fromisoformat(next_["time"])-
                 datetime.fromisoformat(prev["time"])).total_seconds()!=step*60:
                raise ValueError("Episode crossed missing native time step")
        for x in rows:
            key=(x["site"],x["variable"],x["time"])
            if key in covered:raise ValueError("Overlapping source QC0 episode")
            covered.add(key)
        ordered.append((i,e,rows))
    if covered!=set(lookup):
        raise ValueError("Stage93 event grouping did not cover all 122 original QC0 records")
    core={x["timestamp"]:x for x in ho1}
    left,right=core.get("200012270900"),core.get("200012270930")
    if not left or not right:
        raise ValueError("Ho1 QC1→QC2 boundary source proof missing")
    jump=fl(right["original_TA_C"])-fl(left["original_TA_C"])
    if not 18.70<jump<18.80 or fl(left["original_TA_F_QC"])!=1 or fl(right["original_TA_F_QC"])!=2:
        raise ValueError("Ho1 original 18.746C source jump identity changed")
    print("STAGE94 ORIGINAL SOURCE PASS | Stage93 report SHA, 122 QC0 values, 30 uninterrupted events, Ho1 +%.3f C source transition"%jump,flush=True)
    return manifest,ordered,ho1

def evaluate(i,e,rows):
    site,var=e["site"],e["variable"]
    count=len(rows)
    delta=max(abs(fl(r["delta"])) for r in rows)
    a,b=rows[0],rows[-1]
    rh=[fl(r["original_implied_RH_pct"]) for r in rows]
    bad_rh=sum(math.isfinite(z) and z<0 for z in rh)
    mid_count=0
    strong_temp=strong_lw=True
    valid_vpd=0
    for x in rows:
        orig,cand,era=map(lambda k:fl(x[k]),
            ("original_value","candidate_value","ERA_reference"))
        left,right=fl(x["raw_previous"]),fl(x["raw_next"])
        if finite(left) and finite(right) and finite(orig) and finite(cand) and finite(era):
            mid=(left+right)/2
            if var=="TA_F":
                ok=(abs(orig-mid)>=8 and abs(left-right)<=6
                    and abs(cand-mid)<=4 and abs(era-mid)<=8)
                strong_temp &=ok
            elif var=="LW_IN_F":
                ok=(abs(orig-mid)>=120 and abs(left-right)<=55
                    and abs(cand-mid)<=35 and abs(era-mid)<=80)
                strong_lw &=ok
            else:
                strong_temp=False;strong_lw=False
            mid_count+=1
        else:
            strong_temp=False;strong_lw=False
        if var=="VPD_F" and positive_relative_humidity_from_vpd(
            x["original_TA_C"],cand):valid_vpd+=1
    if var=="TA_F":
        # Operator 2026-10-26: candidate T must match BOTH ORIGINAL native neighbors.
        # An ERA match alone never grants QC0 replacement approval.
        valid_temperature_neighbors=all(
            finite(x["raw_previous"]) and finite(x["raw_next"])
            and finite(x["original_value"]) and finite(x["candidate_value"])
            and abs(fl(x["raw_previous"])-fl(x["raw_next"]))<=6
            and abs(fl(x["candidate_value"])-fl(x["raw_previous"]))<=4
            and abs(fl(x["candidate_value"])-fl(x["raw_next"]))<=4
            and abs(fl(x["candidate_value"])-fl(x["original_value"]))>=5
            for x in rows)
        if valid_temperature_neighbors:
            label="USER_RULE_T_CANDIDATE_MATCHES_BOTH_ORIGINAL_NEIGHBORS"
            advice="用户条件批准：候选温度与两个原始相邻观测均相差不超过4C，两邻点差不超过6C"
            attention="RECOMMEND_ACCEPT_REQUIRES_OPERATOR"
        else:
            label="QC0_T_CHANGE_NOT_FULLY_PROVEN"
            advice="人工决定：保留塔实测或批准候选；不可仅因ERA差异替换QC0"
            attention="MANUAL_REQUIRED_P0"
    elif var=="LW_IN_F":
        if count==1 and mid_count==1 and strong_lw:
            label="STRONG_ISOLATED_LW_SPIKE_NEIGHBOR_AND_ERA"
            advice="建议接受候选长波辐射：邻点+ERA支持孤立尖峰修复"
            attention="RECOMMEND_ACCEPT_REQUIRES_OPERATOR"
        else:
            label="QC0_LW_CHANGE_NEEDS_CONTEXT"
            advice="人工确认辐射探头尖峰、云变化或ERA偏差"
            attention="MANUAL_REQUIRED"
    elif var=="VPD_F":
        if site=="US-ICt" and count>=6:
            label="ICt_87_HH_QC0_VPD_SOURCE_NOT_PROVEN"
            advice="保留HOLD：原始QC0 VPD连续87条，不可仅依ERA差异推断传感器故障"
            attention="MANUAL_REQUIRED_P0"
        elif site=="US-Ho2" and count<=4 and valid_vpd==count and all(
             "near_zero_vapor_pressure" in (r.get("reason","") or "") or
             "ERA_RH" in (r.get("candidate_source","") or "")
             for r in rows):
            label="USER_APPROVED_HO2_WET_HUMIDITY_PHYSICAL_CANDIDATE"
            advice="按照用户指示接受候选：经已核验ERA湿度重建且在塔温下物理有效"
            attention="RECOMMEND_ACCEPT_REQUIRES_OPERATOR"
        elif bad_rh==count and valid_vpd==count:
            label="ORIGINAL_NEGATIVE_RH_ALL_ROWS_FIXED_PHYSICALLY"
            advice="建议接受候选VPD：全部原始配对RH<0且候选RH物理有效"
            attention="RECOMMEND_ACCEPT_REQUIRES_OPERATOR"
        elif count>=6:
            label="LONG_QC0_VPD_INTERVAL_MIXED_OR_VALID_ORIGINAL"
            advice="必须人工决定：整段QC0是否存在传感器/插补故障；不允许仅依据ERA自动替换"
            attention="MANUAL_REQUIRED_P0"
        else:
            label="QC0_VPD_CHANGE_MIXED_SOURCE"
            advice="人工确认原始VPD合理性、时序和替代方法"
            attention="MANUAL_REQUIRED"
    else:
        label="OTHER_QC0_REVIEW";advice="人工确认";attention="MANUAL_REQUIRED"
    # User already gave the conditional approval in this conversation.
    # This changes the versioned DECISION LEDGER only; never overwrites a
    # preview CSV/NC or elevates a site with remaining HOLD to production.
    choice=("APPROVE_CANDIDATE" if attention=="RECOMMEND_ACCEPT_REQUIRES_OPERATOR"
            else "HOLD")
    return dict(
       decision_id="B02-94-%02d"%i,site=site,variable=var,
       start_local=a["time"],end_local=b["time"],native_records=count,
       original_range=rng(rows,"original_value"),
       candidate_range=rng(rows,"candidate_value"),
       ERA_range=rng(rows,"ERA_reference"),
       raw_first_neighbor=one(a["raw_previous"]),
       raw_last_neighbor=one(b["raw_next"]),
       largest_abs_change=one(delta),
       original_RH_range=rng(rows,"original_implied_RH_pct"),
       evidence_class=label,scientific_recommendation=advice,
       manual_attention=attention,operator_choice=choice,
       production_approved="NO",
       reason="USER_2026_10_26_CONDITIONAL_RULE_EVALUATED; original/source/clock preserved"
    )

def ho1_conditional_era_decision(ho1):
    """User condition: only ERA-replace 09:00 if preceding ORIGINAL T is ~0C."""
    idx={str(r["timestamp"]):r for r in ho1}
    wanted=("200012270800","200012270830","200012270900","200012270930")
    if not all(k in idx for k in wanted):
        raise ValueError("Ho1 exact 08:00/08:30/09:00/09:30 source context absent")
    t=[fl(idx[k]["original_TA_C"]) for k in wanted]
    qc=[fl(idx[k]["original_TA_F_QC"]) for k in wanted]
    if not (abs(t[2]+15.4)<0.05 and abs(t[3]-3.346)<0.05
            and qc[2]==1 and qc[3]==2):
        raise ValueError("Ho1 historical 2000-12-27 source transition changed")
    # "Around zero" means -2 to +2 C for both preceding native records.
    allow=all(finite(val) and abs(val)<=2.0 for val in t[:2])
    return {"time":"2000-12-27 09:00","previous_0800_original_T_C":t[0],
            "previous_0830_original_T_C":t[1],
            "original_0900_QC1_T_C":t[2],
            "original_0930_QC2_T_C":t[3],
            "interpretation_near_zero":"both preceding original 30min temperatures within +-2 C",
            "operator_condition_met":allow,
            "source_decision":"CONDITIONALLY_AUTHORIZE_ERA_T_HUMIDITY_VERSIONED_OVERLAY" if allow
                else "HOLD_PRECEDING_T_NOT_NEAR_ZERO_DO_NOT_USE_ERA",
            "production_DATM_approved":False}


def show(decisions,ordered,ho1):
    print("\n========== STAGE94 HUMAN DECISIONS (30 episodes) ==========",flush=True)
    for d in decisions:
        print("REVIEW",d["decision_id"],d["site"],d["variable"],
          d["start_local"],"to",d["end_local"],
          "N",d["native_records"],
          "ORIG",d["original_range"],
          "CAND",d["candidate_range"],
          "ERA",d["ERA_range"],
          "NEIGHBOR",d["raw_first_neighbor"],d["raw_last_neighbor"],
          "MAX_CHANGE",d["largest_abs_change"],
          "ORIG_RH",d["original_RH_range"],
          "CLASS",d["evidence_class"],flush=True)
    print("\n=== US-ICt 87-HH CONTINUOUS VPD: HUMAN CRITICAL ===",flush=True)
    for i,e,rows in ordered:
        if e["site"]=="US-ICt" and e["variable"]=="VPD_F" and len(rows)>10:
            for r in rows[::max(1,len(rows)//9)]:
                print("ICt_87HH_SAMPLE",r["time"],"orig",r["original_value"],
                    "candidate",r["candidate_value"],
                    "ERA",r["ERA_reference"],"orig_RH",r["original_implied_RH_pct"],
                    "reason",r["reason"],flush=True)
    print("\n=== HO1 2000 DEC/JAN OFFICIAL SOURCE TRANSITION: UNRESOLVED ===",flush=True)
    for r in ho1:
        if r["timestamp"] in ("200012270830","200012270900","200012270930",
                              "200012271000","200012312330","200101010000"):
            print("HO1_BOUNDARY",r["timestamp"],"ORIG_T",r["original_TA_C"],
                  "QC",r["original_TA_F_QC"],"SELECTED_T",r["selected_TA_C"],
                  "selected_VPD",r["selected_VPD_hPa"],
                  "status",r["science_status"],flush=True)
    count=Counter(d["manual_attention"] for d in decisions)
    print("\nSTAGE94 REVIEW CATEGORY COUNTS",dict(count),flush=True)
    print("STAGE94 OPERATOR APPROVAL EPISODES",
          dict(Counter(x["operator_choice"] for x in decisions)),flush=True)
    verdict=ho1_conditional_era_decision(ho1)
    print("STAGE94 HO1 PREVIOUS ORIGINAL TEMPERATURES 08:00",
          verdict["previous_0800_original_T_C"],"08:30",
          verdict["previous_0830_original_T_C"],"DECISION",
          verdict["source_decision"],flush=True)
    print("APPROVED USER CONDITIONALLY != PRODUCTION DATM APPROVAL")

def save(dest,decisions,ordered,ho1,manifest):
    dest.mkdir(parents=True,exist_ok=False)
    out=dest/"30_QC0_episodes_operator_DECISION_TEMPLATE.csv"
    with out.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(decisions)
    priority=dest/"manual_required_priority.csv"
    with priority.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(x for x in decisions
                                      if x["manual_attention"].startswith("MANUAL_REQUIRED"))
    strongest=dest/"strong_source_evidence_review.csv"
    with strongest.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(x for x in decisions
            if x["manual_attention"].startswith("RECOMMEND_ACCEPT"))
    accepted=dest/"operator_approved_conditional_QC0_episodes.csv"
    with accepted.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(x for x in decisions if x["operator_choice"]=="APPROVE_CANDIDATE")
    stillhold=dest/"operator_remaining_QC0_HOLD_episodes.csv"
    with stillhold.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(x for x in decisions if x["operator_choice"]=="HOLD")
    verdict=ho1_conditional_era_decision(ho1)
    (dest/"Ho1_2000_Dec27_0900_user_conditional_ERA.json").write_text(
        json.dumps(verdict,indent=2)+chr(10))
    proof={
        "schema":"STAGE94_QC0_OPERATOR_EVIDENCE_NON_ACTIVATING_v1",
        "input_stage93_manifest_sha256":sha(S93/"manifest.json"),
        "QC0_original_variable_records":sum(x["native_records"] for x in decisions),
        "human_episodes":len(decisions),
        "remaining_Ho1_nonQC0_T_science_disposition":"HOLD",
        "production_DATM_approved":False,
        "scientific_signoff_by_operator_recorded":"USER_CONDITIONAL_RULE_ONLY",
        "operator_approved_conditional_QC0_variable_records":sum(int(x["native_records"]) for x in decisions if x["operator_choice"]=="APPROVE_CANDIDATE"),
        "operator_remaining_QC0_HOLD_variable_records":sum(int(x["native_records"]) for x in decisions if x["operator_choice"]=="HOLD"),
        "Ho1_0900_source_operator_condition":verdict["source_decision"],
        "allowed_operator_choices":list(ALLOWED),
        "no_source_forcing_nc_cime_slurm_writes":True,
        "reports_sha256":{p.name:sha(p) for p in (out,priority,strongest,accepted,stillhold,
            dest/"Ho1_2000_Dec27_0900_user_conditional_ERA.json")}}
    (dest/"manifest.json").write_text(json.dumps(proof,indent=2)+"\n")
    print("\nSTAGE94 REPORT",dest,flush=True)
    print("STAGE94 USER CONDITIONAL DECISIONS CLASSIFIED | 30 episodes; 122 original QC0 changes",flush=True)
    print("STAGE94 APPROVE",proof["operator_approved_conditional_QC0_variable_records"],
          "HOLD",proof["operator_remaining_QC0_HOLD_variable_records"],flush=True)
    print("NO ORIGINAL SOURCE / CSV FORCING / NC / DATM / CASE / SLURM CHANGES",flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","audit"):
        modes.add_argument("--"+m,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert sum(QC_COUNT.values())==122
        assert positive_relative_humidity_from_vpd(10,2)
        assert not positive_relative_humidity_from_vpd(10,100)
        assert not positive_relative_humidity_from_vpd(-9999,1)
        demo={"site":"US-ICt","variable":"VPD_F","first":"2016-05-21 15:30:00","last":"2016-05-23 10:30:00","native_records":"87"}
        assert (datetime.fromisoformat(demo["last"])-datetime.fromisoformat(demo["first"])).total_seconds()==86*1800
        sample={"site":"US-BZS","variable":"TA_F","first":"2012-10-12 16:00:00",
           "last":"2012-10-12 16:00:00"}
        datum={"original_value":"21.56","candidate_value":"-0.8765",
               "ERA_reference":"-0.653","raw_previous":"-0.864",
               "raw_next":"-0.889","delta":"-22.4365"}
        trial=evaluate(1,sample,[{**datum,"time":sample["first"],"original_implied_RH_pct":"NA"}])
        assert trial["operator_choice"]=="APPROVE_CANDIDATE"
        assert sum(QC_COUNT.values())==122
        print("STAGE94 SELF-TEST PASS | user conditional T, 30 episodes, native 87-HH, fail-closed physics; no writes")
        return
    manifest,ordered,ho1=gate()
    decisions=[evaluate(i,e,rows) for i,e,rows in ordered]
    if len(decisions)!=30 or sum(x["native_records"] for x in decisions)!=122:
        raise ValueError("Stage94 original 30-episode 122-QC0 census changed")
    show(decisions,ordered,ho1)
    if a.check:
        print("STAGE94 CHECK PASS | original source hash verified; no writes")
        return
    dest=ROOT/"reports"/("stage94_30_QC0_final_operator_decisions_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    save(dest,decisions,ordered,ho1,manifest)
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Batch04 US-Syv 106 HH operator-approved ERA temperature substitution.

IMPORTANT: 2017-02-10/11 in typed user instruction is resolved to
2007-02-10/11 by exact preceding US-Syv original source evidence.
Six explicit intervals. Two 17:30-to-07:00 spans are BOTH exactly 28HH.
Second spans *eight HH beyond* the original science HOLD 03:00 endpoint.

At selected native HH, trial TA_F := same-native FLUXNET packaged TA_ERA,
trial TA_F_QC := 2 (ERA origin), no bias fitting. No edits to original
FLUXNET, Stage05-Stage14, earlier SP1/SRG manual alternatives or models.
Use verified parent ten-site manifest from already audited Oct2007 SP1
137-HH repair, changing ONLY the US-Syv selected source pointer.

Humidity: if paired packaged ERA VPD is finite and 0<=VPD<=es(new TA),
use it, mark trial VPD QC2, derive physically consistent RH.
Else retain physically valid current Stage07 VPD at new T and derive RH.
If neither source is physically admissible, apply operator T replacement
but retain existing VPD/RH and explicitly HOLD humidity in provenance.
Never cap/synthesize ungrounded VPD. Output is NOT MODEL APPROVED.

--assess: all source SHA receipts, 106 native HH, provenance, physics, a
         prioritized remaining-source-science HOLD report. READ ONLY.
--apply: independently audited separate full 438288HH US-Syv CSV, 10-site
         provenance selection, per-HH ledger, remaining-science HOLD summary.
         No Slurm, DATM, CIME or Post-v5.
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from pathlib import Path
from uuid import uuid4
from collections import Counter,defaultdict

EXP=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=EXP/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=EXP/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
PARENT=EXP/"manual_sp1_six_day_bias_adjusted_research_not_approved/candidate_20261025T231828Z_ed7de7ac"
PARENT_MF=PARENT/"RESEARCH_TEN_SITE_MANIFEST.tsv"
PARENT_SP1_SHA="357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0"
PARENT_SYV_SHA="5086cbc0f08f73b218d08fdcf34cf0643a6ae1ea95c05c200a98800452b5b32e"
N=438288
SIX=(
 ("FEB08_2007","200702081730","200702082130",9),
 ("FEB09_2007","200702091730","200702092330",13),
 ("FEB10_TO_FEB11_2007","200702101730","200702110700",28),
 ("FEB11_TO_FEB12_2007","200702111730","200702120700",28),
 ("FEB12_2007","200702121730","200702122230",11),
 ("APR27_2003","200304271130","200304271930",17),
)
ALLOW={"TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"}
MISS={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def regular(p):
    ck(p.is_file() and not p.is_symlink(),"Required regular input missing: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def obj(p):return json.loads(regular(p).read_text(encoding="utf-8"))
def tab(p,required,sep=","):
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter=sep)
        ck(r.fieldnames is not None and set(required).issubset(r.fieldnames),
           "Source table schema changed "+str(p))
        return r.fieldnames,list(r)
def num(x):
    x=str(x if x is not None else "").strip()
    if x.upper() in MISS:return None
    try:v=float(x)
    except ValueError:return None
    return v if math.isfinite(v) else None
def tkey(s):return datetime.strptime(s,"%Y%m%d%H%M")
def timekeys(a,b):
    left,right=tkey(a),tkey(b)
    ck(right>=left and (right-left).total_seconds()%1800==0,"Not native 30min time")
    return [(left+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M")
            for i in range(int((right-left).total_seconds()/1800)+1)]
def targets():
    selected={}
    for name,start,end,expected in SIX:
        keys=timekeys(start,end)
        ck(len(keys)==expected,name+" user-mandated count changed")
        for k in keys:
            ck(k not in selected,"Overlapping user repair ranges "+k)
            selected[k]=name
    ck(len(selected)==106,"Exactly 106 authorisations required")
    assert "200702120700" in selected and "200702120730" not in selected
    assert "201702101730" not in selected
    return selected
def saturation(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -60<t<60 else None
def vpd_valid(v,t):
    es=saturation(t)
    return v is not None and es is not None and -1e-9<=v<=es+1e-8
def subset(p,fields,wanted,expected_rows=None):
    found={};n=0
    with regular(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        ck(rd.fieldnames is not None and set(fields).issubset(rd.fieldnames),
           "Expected site native schema missing "+str(p))
        for row in rd:
            n+=1;k=row["TIMESTAMP_START"]
            if k in wanted:
                ck(k not in found,"Duplicate timestamp "+k)
                found[k]={x:row[x] for x in fields}
    if expected_rows is not None:ck(n==expected_rows,"Exact full-length source records changed")
    ck(wanted.issubset(found),"Exact source target timestamps missing from "+str(p))
    return found
def inputs():
    m=obj(S05/"report.json")
    r=obj(S07/"stage07_sha_receipt.json")
    ck(m.get("mode")=="BUILD_CANDIDATE_OVERLAY" and
       m["sites"]["US-Syv"]["rows"]==N and
       m["sites"]["US-Syv"]["hold_rows"]==606,
       "Stage05 metadata changed")
    ck(r.get("inherited_stage05_holds")==754 and
       r.get("invalid_era_endpoints_held")==12,
       "Stage07 source HOLD metadata changed")
    ck(sha(S05/"report.json")==r["source_stage05_report_sha256"],
       "Stage05 science source SHA changed")
    for nm in ("stage07_unsafe_ERA_target_holds.csv","stage07_inherited_754_holds.csv"):
        ck(sha(S07/nm)==r["new_receipts_sha256"][nm],
           "Stage07 HOLD metadata SHA mismatch "+nm)
    sm=m["sites"]["US-Syv"]
    raw=Path(sm["paths"]["native"]);era=Path(sm["paths"]["era"])
    ck(sha(raw)==sm["source_provenance"]["native"]["sha256"],
       "Original FLUXMET source SHA changed")
    ck(sha(era)==sm["source_provenance"]["era"]["sha256"],
       "Packaged FLUXNET ERA source SHA changed")
    s7info=r["derived_full_length_files"]["US-Syv"]
    syv=Path(s7info["full_derived_file"])
    ck(s7info["source_rows"]==N and
       sha(syv)==s7info["sha256"]==PARENT_SYV_SHA,
       "Prior Stage07 Syv derived source SHA changed")
    fields,rows=tab(PARENT_MF,("site","source_path","source_SHA256","latest_stage"),sep="\t")
    ck(len(rows)==10 and len({x["site"] for x in rows})==10,"Parent manifest must have exact 10 sites")
    bysite={x["site"]:x for x in rows}
    ck(Path(bysite["US-Syv"]["source_path"])==syv and
       bysite["US-Syv"]["source_SHA256"]==PARENT_SYV_SHA,
       "Already verified SP1 137HH ten-site manifest does not select expected Syv Stage07")
    ck(bysite["US-SP1"]["source_SHA256"]==PARENT_SP1_SHA and
       sha(Path(bysite["US-SP1"]["source_path"]))==PARENT_SP1_SHA,
       "Previously verified 137HH SP1 full source no longer matches")
    for x in rows:
        ck(regular(Path(x["source_path"])).is_file(),"Manifest site missing "+x["site"])
    print("PARENT RESEARCH TEN SITE INPUTS PINNED: US-SP1 137HH SHA verified; US-Syv Stage07 SHA verified; 9 other selected site source pointers untouched")
    _,holds=tab(S05/"unresolved_hold.csv",("site","TIMESTAMP_START","reason"))
    _,edges=tab(S07/"stage07_unsafe_ERA_target_holds.csv",("site","TIMESTAMP_START","reason"))
    h={x["TIMESTAMP_START"]:x["reason"] for x in holds if x["site"]=="US-Syv"}
    e={x["TIMESTAMP_START"]:x["reason"] for x in edges if x["site"]=="US-Syv"}
    ck(len(h)==606 and len(e)==10 and not set(h)&set(e),"606 + 10 hold provenance changed")
    return raw,era,syv,fields,rows,h,e
def build(raw,era,syv,h,e,selection):
    want=set(selection)|set(h)|set(e)
    for k in list(want):
        d=tkey(k)
        for off in (-2,-1,1,2):
            want.add((d+timedelta(minutes=30*off)).strftime("%Y%m%d%H%M"))
    native= subset(raw,("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"),want,expected_rows=N)
    latest= subset(syv,("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"),want,expected_rows=N)
    reference=subset(era,("TIMESTAMP_START","TA_ERA","VPD_ERA"),want)
    changes={}
    treatment=Counter()
    qc=Counter()
    for k,label in sorted(selection.items()):
        a=latest[k];original=native[k];src=reference[k]
        tau=num(src["TA_ERA"])
        ck(tau is not None and -55<=tau<=50,
           "ERA5-origin same-native T physically impossible/missing "+k)
        prior_t=num(a["TA_F"])
        ck(prior_t is not None and abs(prior_t-tau)<75,
           "Parent Syv source temperature missing/extreme mismatch "+k)
        oldv=num(a["VPD_F"])
        paired_vpd=num(src["VPD_ERA"])
        if vpd_valid(paired_vpd,tau):
            v=paired_vpd
            vqc="2"
            rh=100*(1-v/saturation(tau))
            method="PAIRED_FLUXNET_ERA_VPD_VALID_AT_REPLACED_ERA_T"
        elif vpd_valid(oldv,tau):
            v=oldv
            vqc=a["VPD_F_QC"]
            rh=100*(1-v/saturation(tau))
            method="RETAIN_STAGE07_VPD_VALID_AT_REPLACED_ERA_T"
        else:
            # Mandatory operator TA edit is still applied; no fabricated
            # humidity. Explicitly hold affected humidity for later repair.
            v=oldv
            vqc=a["VPD_F_QC"]
            rh=None
            method="HUMIDITY_UNRESOLVED_NO_VALID_PAIRED_ERA_OR_STAGE07_VPD"
        if rh is not None:
            ck(-1e-7<=rh<=100+1e-7,"RH violates final saturation physics "+k)
            rh=min(100.,max(0.,rh))
        treatment[method]+=1
        qc[original["TA_F_QC"]]+=1
        changes[k]={"site":"US-Syv","TIMESTAMP_START":k,"interval":label,
            "original_FLUXMET_TA_C":original["TA_F"],
            "original_FLUXMET_TA_QC":original["TA_F_QC"],
            "prior_Stage07_TA_C":a["TA_F"],"prior_Stage07_TA_QC":a["TA_F_QC"],
            "FLUXNET_processed_TA_ERA_C":src["TA_ERA"],
            "new_trial_TA_C":tau,"new_trial_TA_QC":"2",
            "prior_Stage07_VPD_hPa":a["VPD_F"],
            "prior_Stage07_VPD_QC":a["VPD_F_QC"],
            "FLUXNET_processed_VPD_ERA_hPa":src["VPD_ERA"],
            "new_trial_VPD_hPa":v,
            "new_trial_VPD_QC":vqc,
            "new_trial_RH_pct":rh,
            "humidity_method":method,
            "historical_HOLD_reason":h.get(k,e.get(k,"ADDED_BY_OPERATOR_NEW_INTERVAL")),
            "decision":"OPERATOR_USER_DIRECT_ERA_TEMPERATURE_REPLACEMENT",
            "production_approval":"NO"}
    ck(len(changes)==106,"Selection count changed")
    print("OPERATOR ERA TEMPERATURE REPLACEMENT PREFLIGHT PASS exact_106_HH, six user intervals")
    print("ORIGINAL_TA_QC_COUNTS",dict(qc))
    print("HUMIDITY_TREATMENT_COUNTS",dict(treatment))
    for name,start,end,n in SIX:
        first=changes[start];last=changes[end]
        print("AUTHORIZED",name,start,end,"HH",n,
              "new_first_T",round(first["new_trial_TA_C"],3),
              "new_last_T",round(last["new_trial_TA_C"],3))
    for k in sorted(changes)[:5]:
        x=changes[k]
        print("EXAMPLE",k,"old_T",x["prior_Stage07_TA_C"],
              "ERA_new_T",x["new_trial_TA_C"],
              "old_T_QC",x["prior_Stage07_TA_QC"],
              "new_QC",x["new_trial_TA_QC"])
    # Classification of original 616 HOLD timestamps with and without
    # the operator-approvals, using retained tower T where not selected.
    union=set(h)|set(e)
    retained=union-set(selection)
    print("REMAINING ORIGINAL SCIENCE HOLD CLASSIFICATION",
          "original_union",len(union),
          "operator_T_authorized_inside_union",len(union&set(selection)),
          "operator_extra_HH_outside_old_HOLD",len(set(selection)-union),
          "remaining_distinct_old_HOLD_HH",len(retained))
    status=Counter()
    for k in retained:
        x=latest[k]
        if num(x["TA_F"]) is None:typ="INVALID_TA"
        elif not vpd_valid(num(x["VPD_F"]),num(x["TA_F"])):
            typ="VPD_NOT_PHYSICAL_AT_RETAINED_TA"
        else:typ="CURRENT_VPD_BASIC_PHYSICS_VALID"
        status[typ]+=1
    print("REMAINING_POST_T_REPAIR_UNCHANGED_HH_PHYSICS",dict(status))
    further=[k for k in retained if h.get(k,"").startswith("SITE_ERA_TA_DIFFERENCE")]
    # Consecutive runs of old grid-vs-T holds not covered by these six.
    runs=[]
    for k in sorted(further):
        if not runs or (tkey(k)-tkey(runs[-1][-1])).total_seconds()!=1800:
            runs.append([k])
        else:runs[-1].append(k)
    runs.sort(key=lambda v:(-len(v),v[0]))
    print("FURTHER_ORIGINAL_T_GRID_DIFFERENCE_HOLD_HH",len(further),
          "CONTIGUOUS_RUNS",len(runs))
    print("NEXT_MANUAL_T_SOURCE_REVIEW_TOP_20_RUNS")
    for run in runs[:20]:
        q=Counter(latest[k]["TA_F_QC"] for k in run)
        bad=sum(not vpd_valid(num(latest[k]["VPD_F"]),num(latest[k]["TA_F"])) for k in run)
        k=run[0];x=latest[k];er=reference[k]
        print("RUN",run[0],run[-1],"HH",len(run),
              "QC",dict(q),"VPD_PHYS_FAIL",bad,
              "first_source_T",x["TA_F"],
              "first_TA_ERA",er["TA_ERA"])
    return changes,h,e,latest,reference
def write_candidate(parent,changes,output):
    seen=set();n=0
    with regular(parent).open(encoding="utf-8-sig",newline="") as f, \
         output.open("x",encoding="utf-8",newline="") as g:
        r=csv.DictReader(f)
        ck(r.fieldnames is not None and {"TIMESTAMP_START","TA_F","TA_F_QC",
                    "VPD_F","VPD_F_QC","RH"}.issubset(r.fieldnames),
           "Candidate parent schema incompatible")
        w=csv.DictWriter(g,fieldnames=r.fieldnames)
        w.writeheader()
        for row in r:
            n+=1;k=row["TIMESTAMP_START"]
            if k in changes:
                ck(k not in seen,"Duplicate half hour in candidate input "+k)
                seen.add(k)
                u=changes[k]
                row["TA_F"]=f"{u['new_trial_TA_C']:.12g}"
                row["TA_F_QC"]="2"
                if u["humidity_method"]!="HUMIDITY_UNRESOLVED_NO_VALID_PAIRED_ERA_OR_STAGE07_VPD":
                    row["VPD_F"]=f"{u['new_trial_VPD_hPa']:.12g}"
                    row["VPD_F_QC"]=u["new_trial_VPD_QC"]
                    row["RH"]=f"{u['new_trial_RH_pct']:.12g}"
            w.writerow(row)
    ck(n==N and seen==set(changes),"Incomplete candidate native source")
    return sha(output)
def audit(parent,out,changes):
    seen=set();altered=0;cells=0;humidity_hold=0
    with regular(parent).open(encoding="utf-8-sig",newline="") as a, \
         regular(out).open(encoding="utf-8-sig",newline="") as b:
        r=csv.DictReader(a);s=csv.DictReader(b)
        ck(r.fieldnames==s.fieldnames,"Changed output schema")
        for x,y in zip_longest(r,s):
            ck(x is not None and y is not None,"Output native row-count differs")
            ck(x["TIMESTAMP_START"]==y["TIMESTAMP_START"],"Output native ordering changed")
            k=x["TIMESTAMP_START"];altered+=1
            diffs={z for z in r.fieldnames if x[z]!=y[z]}
            if k in changes:
                ck(k not in seen,"Repeated approved HH")
                seen.add(k);u=changes[k]
                ck(diffs.issubset(ALLOW),"Unexpected modified fields "+k+" "+str(diffs))
                ck(y["TA_F_QC"]=="2" and
                   abs(float(y["TA_F"])-u["new_trial_TA_C"])<1e-8,
                   "Authorized ERA T or QC2 not applied "+k)
                if u["humidity_method"]=="HUMIDITY_UNRESOLVED_NO_VALID_PAIRED_ERA_OR_STAGE07_VPD":
                    ck(all(x[z]==y[z] for z in ("VPD_F","VPD_F_QC","RH")),
                       "Unresolved humidity sources must retain old values "+k)
                    humidity_hold+=1
                else:
                    ck(vpd_valid(num(y["VPD_F"]),num(y["TA_F"])),
                       "New trial VPD exceeds saturation "+k)
                    ck(-1e-6 <=float(y["RH"])<=100.000001,
                       "New trial RH out of 0-100 "+k)
                if diffs:cells+=len(diffs)
            else:
                ck(not diffs,"Non-operator native record was unexpectedly modified "+k)
    ck(altered==N and seen==set(changes),"Whole-US-Syv candidate verification incomplete")
    print("INDEPENDENT FULL FILE SOURCE AUDIT PASS",altered,
          "authorized_target_HH",len(seen),
          "modified_field_cells",cells,
          "humidity_still_HOLD_at_approved_T_HH",humidity_hold)
    return cells,humidity_hold

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--assess",action="store_true")
    g.add_argument("--apply",action="store_true")
    o=p.parse_args()
    selected=targets()
    print("US-SYV SIX USER T INTERVAL SELF-TEST PASS: exactly 106 HH, 2007 corrected from typo, Feb11->12 extended to 07:00")
    if o.self_test:return
    raw,era,parent,fields,mf,h,e=inputs()
    decisions,h,e,latest,ref=build(raw,era,parent,h,e,selected)
    if o.assess:
        print("US-SYV ASSESS READ-ONLY COMPLETE NO WRITES")
        return
    dest=EXP/"manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    (dest/"INCOMPLETE_NOT_FOR_POSTV5_DATM_CIME_OR_SPINUP").write_text(
        "US-Syv: operator-approved ERA-T scientific research alternative. "
        "Remaining humidity and source physics must be reviewed; no model release.\n")
    out=dest/"US-Syv_six_intervals_106HH_ERA_T_manual_research_FLUXMET_HH.csv"
    sh=write_candidate(parent,decisions,out)
    cells,unresolved=audit(parent,out,decisions)
    newmf=[]
    for entry in mf:
        row=dict(entry)
        if row["site"]=="US-Syv":
            row["source_path"]=str(out)
            row["source_SHA256"]=sh
            row["latest_stage"]="USER_SIX_ERA_T_INTERVALS_106HH_RESEARCH_CANDIDATE_NOT_APPROVED"
        newmf.append(row)
    manifest=dest/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    with manifest.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader();w.writerows(newmf)
    ck(all(a==b for a,b in zip(
         (x for x in mf if x["site"]!="US-Syv"),
         (x for x in newmf if x["site"]!="US-Syv"))),
       "Nine other site manifest entries changed")
    tsv=dest/"SIX_OPERATOR_106_HH_ERA_T_FULL_PROVENANCE.tsv"
    rows=[decisions[x] for x in sorted(decisions)]
    with tsv.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t")
        w.writeheader();w.writerows(rows)
    union=set(h)|set(e)
    counters=Counter()
    for k in sorted(union-set(decisions)):
        t=num(latest[k]["TA_F"]);v=num(latest[k]["VPD_F"])
        counters["retained_HH"]+=1
        counters["remaining_VPD_invalid"]+=not vpd_valid(v,t)
        counters["remaining_source_T_grid_HOLD"]+=h.get(k,"").startswith("SITE_ERA_TA_DIFFERENCE")
    receipt={
        "approval":"USER_APPROVED_ERA_ORIGIN_TEMPERATURE_SUBSTITUTION_IN_RESEARCH_CANDIDATE_ONLY",
        "original_source_status":"UNCHANGED",
        "model_production_approval":False,
        "user_typo_interpretation":"2017-02-10/11 resolved to 2007-02-10/11 from original evidence",
        "intervals":[{"name":nm,"start":st,"end":en,"HH":cnt} for nm,st,en,cnt in SIX],
        "total_operator_selected_native_HH":len(decisions),
        "stage07_original_syvs_sha256":PARENT_SYV_SHA,
        "parent_Sp1_137HH_sha256":PARENT_SP1_SHA,
        "stage07_parent_full_native_rows":N,
        "new_US_Syv_full_derived_source":str(out),
        "new_US_Syv_full_SHA256":sh,
        "changed_field_cells":cells,
        "temperature_authorized_HH_where_humidity_source_still_HOLD":unresolved,
        "other_nine_site_manifest_entries_unchanged":True,
        "remaining_original_source_holds_not_authorized_for_T_replacement":dict(counters),
        "science_gate":"BLOCKED_UNTIL_RESIDUAL_SCIENCE_REVIEW",
    }
    (dest/"SCIENCE_RESEARCH_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    (dest/"SIX_INTERVAL_HUMIDITY_HOLD_TIMESTAMPS.txt").write_text(
        "".join(k+"\n" for k in sorted(decisions) if decisions[k]["humidity_method"].startswith("HUMIDITY_UNRESOLVED")),
        encoding="utf-8")
    print("US-SYV SIX INTERVALS SCIENCE CANDIDATE CREATED & VERIFIED",dest)
    print("NEW US-SYV FULL SHA256",sh)
    print("TEN-SITE RESEARCH MANIFEST",manifest)
    print("NEXT SCIENCE HOLD SUMMARY",dict(counters),
          "additional_humidity_HOLD_in_selected_ERA_T",unresolved)
    print("ORIGINAL/OTHER NINE SITE FILES UNCHANGED; NO POSTV5 DATM CIME SLURM MODEL RELEASE")
if __name__=="__main__":main()

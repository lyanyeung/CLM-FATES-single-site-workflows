#!/usr/bin/env python3
"""Batch04 US-Syv: USER APPROVED replace ALL remaining anomalous QC0 + QC1 TA with ERA.

Contract: 85 ORIGINAL native half-hours, 30 historical HOLD episodes (24 QC0,
61 QC1), all user-approved for SAME-TIMESTAMP packaged FLUXNET TA_ERA -> QC2.
Additionally follow contiguous original QC0/QC1 negative TA-minus-ERA
anomalies >=8 deg C beyond a historical HOLD on BOTH sides, inside a pinned
96-hour flank. Candidate extension is a strongly bounded scientific rule,
NOT permission to replace other nearby normal tower temperatures. An
extension must remain continuously anomalous (no crossing an unflagged
healthy half-hour). No interpolation or calibration offset.

Research candidate inherits the operator-VERIFIED 106-HH US-Syv final
candidate and the nine other site selections. Paired processed FLUXNET
VPD_ERA is applied at new ERA-origin TA only if physical. Otherwise use
physically valid prior VPD. Else humidity remains explicitly HOLD.
No original/site/model overwrites or Slurm/DATM/CIME/Post-v5 release.

--self-test : synthetic tests, NO WRITES
--assess    : source SHA checked, episode/extension/physics report, NO WRITES
--apply     : same preflight plus an independently full-file audited NEW
              US-Syv 438288-HH candidate; report all remaining science holds
"""
import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from collections import Counter,defaultdict
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=ROOT/"qcv5_stage05_candidates/candidate_20261024T103113Z"
S07=ROOT/"qcv5_stage07_applied/candidate_20261024T114538Z_6a6b36ba"
PARENT=ROOT/"manual_US_Syv_six_ERA_T_106HH_science_candidate_not_approved/candidate_20261026T010755Z_591ef88f"
PARENT_CSV=PARENT/"US-Syv_six_intervals_106HH_ERA_T_manual_research_FLUXMET_HH.csv"
PARENT_MANIFEST=PARENT/"RESEARCH_TEN_SITE_MANIFEST.tsv"
PARENT_SHA="8ac03873ad573e2885569f371ce6a413d4f3f230d7f473ece6c7e20bb7bf1b73"
NROWS=438288
ORIGINAL_HOLD_REASON="SITE_ERA_TA_DIFFERENCE_GT8C_OR_SITE_TA_INVALID"
QC={"0","1"}
FLANK_HOURS=96
SUSPECT_DELTA_C=-8.0
MAX_NEW_EXTENSION_HH=1600
MAX_BOUNDARY_JUMP_C=11.0
MODIFIABLE={"TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"}
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}
PREVIOUS_SIX=(
("200702081730","200702082130"),
("200702091730","200702092330"),
("200702101730","200702110700"),
("200702111730","200702120700"),
("200702121730","200702122230"),
("200304271130","200304271930"))

def require(cond,msg):
    if not cond:raise ValueError(msg)
def reg(p):
    require(p.is_file() and not p.is_symlink(),"Source absent/not regular: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with reg(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def obj(p):return json.loads(reg(p).read_text(encoding="utf-8"))
def number(x):
    s=str(x if x is not None else "").strip()
    if s.upper() in MISSING:return None
    try:n=float(s)
    except ValueError:return None
    return n if math.isfinite(n) else None
def dt(k):return datetime.strptime(k,"%Y%m%d%H%M")
def key(d):return d.strftime("%Y%m%d%H%M")
def shift(k,half):return key(dt(k)+timedelta(minutes=30*half))
def within(a,b):
    x=dt(a);y=dt(b)
    require(y>=x and (y-x).total_seconds()%1800==0,"Non-native time interval")
    return [key(x+timedelta(minutes=30*i)) for i in range(int((y-x).total_seconds()/1800)+1)]
def sat(t):
    return 6.112*math.exp(17.67*t/(t+243.5)) if t is not None and -60<t<60 else None
def phys(v,t):
    e=sat(t)
    return v is not None and e is not None and 0<=v<=e+1e-8
def tab(p,need,delimiter=","):
    with reg(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter=delimiter)
        require(rd.fieldnames is not None and set(need).issubset(rd.fieldnames),
                "Input schema mismatch "+str(p))
        return rd.fieldnames,list(rd)
def lookup(p,cols,times,expected_rows=None):
    got={};n=0
    with reg(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        require(rd.fieldnames is not None and set(cols).issubset(rd.fieldnames),
                "Site input missing expected fields "+str(p))
        for r in rd:
            n+=1;k=r["TIMESTAMP_START"]
            if k in times:
                require(k not in got,"Duplicate timestamp "+k)
                got[k]={c:r[c] for c in cols}
    if expected_rows is not None:require(n==expected_rows,"Complete site row count mismatch")
    require(times.issubset(got),"Source lacks requested HH: "+str(p))
    return got
def runs(keys):
    out=[]
    for k in sorted(keys):
        if not out or shift(out[-1][-1],1)!=k:out.append([k])
        else:out[-1].append(k)
    return out
def provenance():
    stage5=obj(S05/"report.json");stage7=obj(S07/"stage07_sha_receipt.json")
    prior=obj(PARENT/"SCIENCE_RESEARCH_RECEIPT.json")
    require(stage5.get("mode")=="BUILD_CANDIDATE_OVERLAY" and
            stage5["sites"]["US-Syv"]["rows"]==NROWS and
            stage5["sites"]["US-Syv"]["hold_rows"]==606,
            "Original verified Stage05 science summary changed")
    require(stage7.get("inherited_stage05_holds")==754 and
            stage7.get("invalid_era_endpoints_held")==12 and
            sha(S05/"report.json")==stage7["source_stage05_report_sha256"],
            "Stage05/07 SHA-HOLD contract changed")
    require(sha(PARENT_CSV)==PARENT_SHA and
            prior.get("new_US_Syv_full_SHA256")==PARENT_SHA and
            prior.get("total_operator_selected_native_HH")==106 and
            prior.get("model_production_approval") is False,
            "Operator-approved 106-HH Syv source/receipt changed")
    m=stage5["sites"]["US-Syv"]
    raw=Path(m["paths"]["native"]);era=Path(m["paths"]["era"])
    require(sha(raw)==m["source_provenance"]["native"]["sha256"],
            "Original FLUXMET Syv SHA mismatch")
    require(sha(era)==m["source_provenance"]["era"]["sha256"],
            "Original paired FLUXNET ERA SHA mismatch")
    fields,manifest=tab(PARENT_MANIFEST,
                        ("site","source_path","source_SHA256","latest_stage"),"\t")
    require(len(manifest)==10 and len({r["site"] for r in manifest})==10,
            "Expected exactly ten prior research site sources")
    old=[r for r in manifest if r["site"]=="US-Syv"]
    require(len(old)==1 and Path(old[0]["source_path"])==PARENT_CSV and
            old[0]["source_SHA256"]==PARENT_SHA,
            "Prior 106-HH Syv manifest selection mismatch")
    _,allholds=tab(S05/"unresolved_hold.csv",
                   ("site","TIMESTAMP_START","reason"))
    hold={r["TIMESTAMP_START"]:r["reason"] for r in allholds if r["site"]=="US-Syv"}
    require(len(allholds)==754 and len(hold)==606,
            "Original 606-Syv / 754-total HOLD archive changed")
    seed={k for k,why in hold.items() if why==ORIGINAL_HOLD_REASON}
    done=set()
    for a,b in PREVIOUS_SIX:done.update(within(a,b))
    require(len(done)==106 and
            len(seed)==183 and len(seed-done)==85 and
            len(seed&done)==98,
            "Exactly 85 new T/HOLD seeds and 98 prior original-HOLD HH required")
    _,skip=tab(S07/"stage07_unsafe_ERA_target_holds.csv",
               ("site","TIMESTAMP_START","reason"))
    skipkeys={r["TIMESTAMP_START"] for r in skip if r["site"]=="US-Syv"}
    require(len(skipkeys)==10 and not set(hold)&skipkeys,
            "Previous 606+10 Syv hold union changed")
    require(len(runs(seed-done))==30,
            "Expected 30 contiguous old T discrepancy episodes")
    return raw,era,fields,manifest,hold,skipkeys,seed-done,done
def anomaly(k,original,era):
    if k not in original or k not in era:return False
    a=original[k];e=era[k]
    ta=number(a["TA_F"]);te=number(e["TA_ERA"])
    return (a["TA_F_QC"] in QC and ta is not None and te is not None
            and -55<=te<=50 and ta-te<=SUSPECT_DELTA_C)
def expand(seed,prior_done,original,era):
    selected=set(seed)
    for k in sorted(seed):
        for direction in (-1,1):
            t=shift(k,direction)
            while anomaly(t,original,era) and t not in prior_done:
                selected.add(t)
                t=shift(t,direction)
            # The provided +/-96h flank MUST not truncate an anomaly.
            require(t in original and t in era,
                    "Anomaly continuation reaches 96h window boundary near "+k+
                    "; NO WRITES. Increase inspected native window only after review")
    return selected
def candidate_selection(raw,era,final,seed,previous,hold):
    inspected=set(seed)
    for k in seed:
        inspected.update(within(shift(k,-FLANK_HOURS*2),
                                shift(k,FLANK_HOURS*2)))
    original=lookup(raw,("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"),
                    inspected,NROWS)
    reference=lookup(era,("TIMESTAMP_START","TA_ERA","VPD_ERA"),inspected)
    chosen=expand(seed,previous,original,reference)
    require(seed.issubset(chosen) and not (chosen&previous),
            "Approved old T points omitted / previously approved 106 modified")
    extra=chosen-seed
    require(len(extra)<=MAX_NEW_EXTENSION_HH,
            "Unexpected >1600 automatic anomaly extension HH, no writing")
    # Original 85 seed HH were chosen on science hold, validate QC0/QC1 and T.
    for k in seed:
        require(original[k]["TA_F_QC"] in QC and
                number(original[k]["TA_F"]) is not None and
                number(reference[k]["TA_ERA"]) is not None,
                "Original seed untrusted T source / missing ERA at "+k)
    contexts=set(chosen)
    for k in chosen:
        contexts.update((shift(k,-1),shift(k,1)))
    require(contexts.issubset(inspected),
            "New extensions not completely flanked, refuse unsafe boundary")
    latest=lookup(final,("TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"),
                  contexts,NROWS)
    edits={}
    hum=Counter()
    rawqc=Counter()
    for k in sorted(chosen):
        a=original[k];e=reference[k];old=latest[k]
        t=number(e["TA_ERA"]);prior_t=number(old["TA_F"])
        require(t is not None and -55<=t<=50 and prior_t is not None,
                "Operator selected missing/out-of-range processed ERA T "+k)
        v=number(e["VPD_ERA"])
        if phys(v,t):
            meth="PAIRED_FLUXNET_ERA_VPD_PHYSICAL_AT_ERA_T"
            newqc="2"
        elif phys(number(old["VPD_F"]),t):
            v=number(old["VPD_F"])
            newqc=old["VPD_F_QC"]
            meth="RETAIN_PRIOR_VPD_PHYSICAL_AT_NEW_T"
        else:
            v=number(old["VPD_F"])
            newqc=old["VPD_F_QC"]
            meth="VPD_HUMIDITY_UNRESOLVED_RETAIN_OLD_FOR_QA"
        rh=None if meth.startswith("VPD_HUMIDITY_UNRESOLVED") else max(
            0.0,min(100.0,100*(1-v/sat(t))))
        hum[meth]+=1
        rawqc[a["TA_F_QC"]]+=1
        edits[k]={
            "site":"US-Syv","TIMESTAMP_START":k,
            "basis":"ORIGINAL_85_USER_APPROVED_SOURCE_HOLD" if k in seed else
                    "CONTIGUOUS_PROVEN_MINUS8C_SOURCE_ANOMALY_EXTENSION",
            "original_native_TA_C":a["TA_F"],
            "original_native_QC":a["TA_F_QC"],
            "previous_106_candidate_TA_C":old["TA_F"],
            "processed_FLUXNET_TA_ERA_C":e["TA_ERA"],
            "approved_ERA_trial_TA_C":t,
            "approved_ERA_trial_TA_QC":"2",
            "original_VPD_hPa":old["VPD_F"],
            "processed_FLUXNET_VPD_ERA_hPa":e["VPD_ERA"],
            "new_VPD_hPa":v,
            "new_VPD_QC":newqc,
            "new_RH_pct":rh,
            "humidity_method":meth,
            "preexisting_Stage05_HOLD_reason":hold.get(k,""),
            "status":"RESEARCH_ALTERNATIVE_USER_APPROVED_NOT_PRODUCTION"}
    for group in runs(chosen):
        before=latest[shift(group[0],-1)]
        after=latest[shift(group[-1],1)]
        start_delta=abs(edits[group[0]]["approved_ERA_trial_TA_C"]-
                        number(before["TA_F"]))
        end_delta=abs(edits[group[-1]]["approved_ERA_trial_TA_C"]-
                      number(after["TA_F"]))
        require(start_delta<=MAX_BOUNDARY_JUMP_C and
                end_delta<=MAX_BOUNDARY_JUMP_C,
                "Unsafe source/boundary >11C after replacement near "+
                group[0]+".."+group[-1]+" START/END "+
                f"{start_delta:.3f}/{end_delta:.3f}C; NO WRITES")
    print("USER-APPROVED US-SYV ALL QC0/QC1 T HOLD PREFLIGHT PASS",
          "85_original_new_HH",len(seed),
          "extra_contiguous_source_ERA_difference_HH",len(extra),
          "exact_new_T_HH",len(chosen),
          "prior_user_106_T_HH_unchanged",True)
    print("SOURCE_ORIGINAL_QC_COMPOSITION",dict(rawqc),
          "HUMIDITY_METHOD_COUNTS",dict(hum))
    print("SOURCE_OLD_HOLD_RUNS",len(runs(seed)),
          "NEW_ANOMALOUS_CONTIGUOUS_TRIAL_RUNS",len(runs(chosen)))
    print("ALL_T_REPLACEMENT_RUNS_WITH_NATIVE_ERA_AND_BOUNDARIES")
    for n,g in enumerate(runs(chosen),1):
        a=edits[g[0]];b=edits[g[-1]]
        print("RUN",n,g[0],g[-1],"HH",len(g),
              "FIRST_T",a["original_native_TA_C"],
              "FIRST_NEW_ERA_T",a["approved_ERA_trial_TA_C"],
              "LAST_NEW_ERA_T",b["approved_ERA_trial_TA_C"],
              "EXTRA_HH",sum(k in extra for k in g))
    return edits,chosen,extra,latest,hum
def write_csv(parent,output,changes):
    count=0;seen=set()
    with reg(parent).open(encoding="utf-8-sig",newline="") as f, \
         output.open("x",encoding="utf-8",newline="") as g:
        r=csv.DictReader(f)
        require(r.fieldnames is not None and
                {"TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","RH"}.issubset(r.fieldnames),
                "Existing full Syv CSV schema changed")
        w=csv.DictWriter(g,fieldnames=r.fieldnames);w.writeheader()
        for row in r:
            count+=1;k=row["TIMESTAMP_START"]
            if k in changes:
                require(k not in seen,"Duplicate user changed time "+k)
                seen.add(k);z=changes[k]
                row["TA_F"]=f"{z['approved_ERA_trial_TA_C']:.12g}"
                row["TA_F_QC"]="2"
                if z["new_RH_pct"] is not None:
                    row["VPD_F"]=f"{z['new_VPD_hPa']:.12g}"
                    row["VPD_F_QC"]=z["new_VPD_QC"]
                    row["RH"]=f"{z['new_RH_pct']:.12g}"
            w.writerow(row)
    require(count==NROWS and seen==set(changes),
            "Candidate not full original-length or missing expected target")
    return sha(output)
def audit(old,new,changes):
    seen=set();n=0;cells=0;invalid_humidity=0
    with reg(old).open(encoding="utf-8-sig",newline="") as f,\
         reg(new).open(encoding="utf-8-sig",newline="") as g:
        a=csv.DictReader(f);b=csv.DictReader(g)
        require(a.fieldnames==b.fieldnames,"Changed site schema")
        for x,y in zip_longest(a,b):
            require(x is not None and y is not None and
                    x["TIMESTAMP_START"]==y["TIMESTAMP_START"],
                    "Candidate changed source native full HH sequence")
            n+=1;k=x["TIMESTAMP_START"]
            altered={z for z in a.fieldnames if x[z]!=y[z]}
            if k not in changes:
                require(not altered,"Unapproved source data modified at "+k)
                continue
            require(k not in seen and altered.issubset(MODIFIABLE),
                    "Unexpected edited columns/duplicate at "+k)
            seen.add(k);p=changes[k]
            require(y["TA_F_QC"]=="2" and
                    abs(float(y["TA_F"])-p["approved_ERA_trial_TA_C"])<1e-8,
                    "User-approved ERA temperature not applied "+k)
            if p["new_RH_pct"] is None:
                invalid_humidity+=1
                require(all(x[z]==y[z] for z in ("VPD_F","VPD_F_QC","RH")),
                        "Unproven humidity should be left unchanged "+k)
            else:
                require(phys(number(y["VPD_F"]),number(y["TA_F"])) and
                        abs(float(y["RH"])-p["new_RH_pct"])<1e-8,
                        "Output VPD/RH physics failed "+k)
            cells+=len(altered)
    require(n==NROWS and seen==set(changes),
            "Full native site readback/audit did not account for all target records")
    print("INDEPENDENT US-SYV FULL OUTPUT SCIENCE AUDIT PASS",
          "source_HH",n,"new_authorized_HH",len(changes),
          "altered_cells",cells,"new_humidity_HOLD",invalid_humidity)
    return cells,invalid_humidity
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--assess",action="store_true")
    g.add_argument("--apply",action="store_true")
    args=p.parse_args()
    a=within("200305081130","200305081400")
    require(len(a)==6 and shift(a[-1],1)=="200305081430" and
            len(runs({"200305300730","200305300800","200305300930"}))==2,
            "Native 30min time/episode self-test wrong")
    # Synthetic exact abnormal condition, do not mistake missing or valid for anomalies.
    o={"200001010000":{"TA_F":"0","TA_F_QC":"0"}}
    e={"200001010000":{"TA_ERA":"13"}}
    require(anomaly("200001010000",o,e) and
            not anomaly("200001010030",o,e),
            "Synthetic ERA negative source T anomaly classification failed")
    print("US-SYV 85 ORIGINAL QC0+QC1 USER APPROVAL SELF-TEST PASS: "
          "30 episodes; 96h bounded continuation; no source writes")
    if args.self_test:return
    raw,era,fields,manifest,hold,skips,seeds,previous=provenance()
    require(len(seeds)==85 and len(runs(seeds))==30,"Unexpected source seed changes")
    edits,selected,extra,latest,hum=candidate_selection(raw,era,PARENT_CSV,seeds,previous,hold)
    if args.assess:
        print("US-SYV 85HH+CONTIGUOUS-EXTENSION SCIENCE ASSESS PASS; NO WRITES")
        return
    dest=ROOT/"manual_US_Syv_remaining_T_all_QC0_QC1_ERA_research_candidate_not_approved"/(
         "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
         "_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    (dest/"INCOMPLETE_NOT_FOR_POSTV5_DATM_CIME_SLURM_SPINUP").write_text(
        "User-approved new Syv QC0/QC1 ERA T science trial; remaining site science not passed.\n")
    output=dest/"US-Syv_all_remaining_QC0_QC1_ERA_T_full_FLUXMET_HH.csv"
    outsha=write_csv(PARENT_CSV,output,edits)
    cells,humidity_hold=audit(PARENT_CSV,output,edits)
    newmf=[]
    for r in manifest:
        d=dict(r)
        if d["site"]=="US-Syv":
            d["source_path"]=str(output)
            d["source_SHA256"]=outsha
            d["latest_stage"]="US_SYV_USER_APPROVED_ALL_REMAINING_QC0_QC1_ERA_T_NOT_PRODUCTION"
        newmf.append(d)
    require([r for r in manifest if r["site"]!="US-Syv"]==
            [r for r in newmf if r["site"]!="US-Syv"],
            "Non-Syv research selection unexpectedly changed")
    mf=dest/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    with mf.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader();w.writerows(newmf)
    prov=dest/"NEW_SOURCE_TA_ERA_REPAIR_LEDGER.tsv"
    records=[edits[k] for k in sorted(edits)]
    with prov.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]),delimiter="\t")
        w.writeheader();w.writerows(records)
    oldhold=set(hold)|set(skips)
    remain=oldhold-set(edits)-previous
    results={
        "status":"SOURCE_PINNED_INDEPENDENT_FULL_CANDIDATE_AUDIT_PASS_RESEARCH_ONLY",
        "production_approval":False,
        "operator_scope":"ALL_85_ORIGINAL_QC0_QC1_T_GRID_HOLDS_PLUS_CONTIGUOUS_PROVEN_BAD_T_EXTENSION",
        "old_106_approved_HH_preserved":106,
        "this_new_original_T_HOLD_HH":85,
        "this_extra_adjacent_source_proven_anomalous_HH":len(extra),
        "this_total_new_T_HH":len(edits),
        "complete_derived_halfhours":NROWS,
        "complete_derived_SHA256":outsha,
        "candidate_full_file":str(output),
        "new_manifest":str(mf),
        "new_Syv_humidity_HOLD":humidity_hold,
        "remaining_legacy_science_HOLD_HH_excluding_user_T_approvals":len(remain),
        "remaining_legacy_basic_source_VPD_physics_fail_not_yet_repaired":"REQUIRES_SEPARATE_FULL_SCAN",
        "changed_field_cells":cells,
        "flank_selection_rule":"SOURCE_QC0_OR_QC1_AND_RAW_TA_MINUS_PACKAGED_TA_ERA_LE_MINUS8C_CONTIGUOUS_TO_85_SEEDS",
        "all_original_and_prior_research_sources_unchanged":True,
        "other_nine_site_manifest_rows_unchanged":True,
        "DATM_ready":False,"spinup_approved":False}
    (dest/"SCIENCE_RESEARCH_RECEIPT.json").write_text(
        json.dumps(results,indent=2)+"\n",encoding="utf-8")
    (dest/"NEW_T_HUMIDITY_REMAINING_HOLD.txt").write_text(
        "".join(k+"\n" for k in sorted(edits) if edits[k]["new_RH_pct"] is None),
        encoding="utf-8")
    print("US-SYV ALL REMAINING USER T APPROVALS REPAIR FULL AUDIT PASS",dest)
    print("NEW US-SYV COMPLETE CSV SHA256",outsha)
    print("NEW TEN SITE SCIENCE MANIFEST",mf)
    print("STILL_UNDECIDED_NON_T_SCIENCE_HOLD_HH",len(remain))
    print("NO ORIGINAL/SYV_106HH/OTHER_NINE_SITE/MODEL/DATM/SLURM WRITES")
if __name__=="__main__":main()

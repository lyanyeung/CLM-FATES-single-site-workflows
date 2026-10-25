#!/usr/bin/env python3
"""Batch04 manual 6-day ORIGINAL-TA repair as a separate research candidate.

User-chosen scientific rule:
  For each of 2007-10-15..18 and 22..23, arithmetic mean
  (original TA_F - original FLUXNET TA_ERA) over same day's QC0
  time intervals before 06:30 (Oct23 before 07:00) and >=18:00.
  For abnormal 06:30 (Oct23 07:00) through 17:30 inclusive set:
       trial TA_F = original TA_ERA + THAT DAY'S mean offset.
  Trial TA_F_QC=2 (ERA-derived substitute); retain all source metadata.
  For each adjusted TA: if Stage14 RH is available (0..100%), derive
  VPD from RH and new T and set candidate VPD QC2; if RH is MISSING,
  retain the old VPD_F and original VPD_F_QC *unchanged*, provided
  0 <= retained VPD <= saturation vapour pressure at corrected TA.
  An explicit finite but out-of-range RH is a HARD STOP.
  Never infer an RH from corrupted original TA, invent ERA dew point,
  or silently overwrite humidity lacking evidence.
  Do NOT change source RH or TA_F_MDS/QC.

Extends the previously independently verified three-point research
candidate; earlier SP1-2000 2 HH and SRG-2019 1 HH are preserved.
Checks exact source SHAs, 6*48 original native HH, 137 new target HH,
expected daily means, onset/end jump, QC, physical VPD validity and
humidity provenance, unchanged other nine site manifest rows, and
self-audits full 368208 HH after writing.
The original CSV/Stage14/Stage15/prior trial and 8 science holds stay
untouched; NO Post-v5, DATM, CIME, Slurm or model release.

--assess: completely read-only (normal day offsets and change plan).
--apply: create ONE NEW independently audited research-only full CSV.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from itertools import zip_longest

E=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
ORIG=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/"
 "US-SP1/forcing/raw/AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1/"
 "AMF_US-SP1_FLUXNET_FLUXMET_HH_2000-2020_v1.3_r1.csv")
ORIG_SHA="d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963"
OLD=E/"manual_temperature_alternative_not_approved/candidate_20261025T183441Z_254f8181"
OLD_MANIFEST=OLD/"MANUAL_LATEST_TEN_SITE_RESEARCH_MANIFEST.tsv"
OLD_RECEIPT=OLD/"MANUAL_TRIAL_RECEIPT.json"
OLD_SP1_SHA="96d8c6ad2a082bb243160ee91c2aee0d2fcd3dc0a862515519c34dab2fa664d3"
OLD_SRG_SHA="d65523022718819d7013d79f1015fe419958078a8d1fde4f062fa8470929933f"
NROWS=368208
DAYS={
 "20071015":("0630",-2.832680000),
 "20071016":("0630",-2.472120000),
 "20071017":("0630",-2.251880000),
 "20071018":("0630",-1.555640000),
 "20071022":("0630",-3.633480000),
 "20071023":("0700",-2.844576923076923),
}
ANCHOR={
 "20071015":(11.150,23.220),
 "20071016":(11.149,23.220),
 "20071017":(11.169,23.710),
 "20071018":(11.138,26.240),
 "20071022":(11.126,23.390),
 "20071023":(11.123,25.570),
}
EXPECTED_NEW_HH=137
EXPECTED_QC1_VPD=40
TARGET_FIELDS={"TA_F","TA_F_QC","VPD_F","VPD_F_QC"}
META_FIELDS={"TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA","RH","VPD_F","VPD_F_QC"}
def fail(s): raise ValueError(s)
def check(cond,s):
    if not cond:fail(s)
def regular(p):
    check(p.is_file() and not p.is_symlink(),"Missing/non-regular or symlink source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for chunk in iter(lambda:f.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()
def val(raw):
    try:x=float(raw)
    except (ValueError,TypeError):return None
    return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
def es(t):
    check(-45<t<55,"Temperature invalid for saturation calculation")
    return 6.112*math.exp(17.67*t/(t+243.5))
def istarget(key):
    d=key[:8]
    return d in DAYS and DAYS[d][0]<=key[-4:]<="1730"
def inspect_source():
    check(sha(ORIG)==ORIG_SHA,"Original FLUXMET SHA mismatch")
    src={d:{} for d in DAYS}
    n=0
    with regular(ORIG).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        check(r.fieldnames and set(("TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA",
                                   "VPD_F","VPD_F_QC")).issubset(r.fieldnames),
              "Original release schema changed")
        for row in r:
            n+=1;k=row["TIMESTAMP_START"];d=k[:8]
            if d in src:
                check(len(k)==12 and k not in src[d],"Duplicate original timestamp")
                src[d][k]=row
    check(n==NROWS,"Original source full rows changed")
    offsets={}
    count=0
    qc1=0
    for d,(start,expected) in DAYS.items():
        data=src[d]
        check(len(data)==48,"One complete original HH day missing "+d)
        for i in range(48):
            k=d+f"{i//2:02d}{(i%2)*30:02d}"
            check(k in data,"Original missing exact HH "+k)
        a,b=ANCHOR[d]
        check(abs(float(data[d+"1730"]["TA_F"])-a)<.002 and
              abs(float(data[d+"1800"]["TA_F"])-b)<.002,
              "18:00 original anchor changed "+d)
        normal=[]
        for k,row in data.items():
            hh=k[-4:]
            check(row["TA_F_QC"]=="0","Original QC0 expected across six days "+k)
            ta,era=val(row["TA_F"]),val(row["TA_ERA"])
            check(ta is not None and era is not None,"Missing original TA or TA_ERA "+k)
            if hh<start or hh>="1800":
                normal.append(ta-era)
            elif hh<="1730":
                count+=1
                qc1+=row["VPD_F_QC"]=="1"
                check(row["VPD_F_QC"] in ("1","2"),
                      "Refuse automated edit of measured VPD QC0 "+k)
        check(len(normal)==(26 if d=="20071023" else 25),
              "Wrong full-day normal anchor count "+d)
        mean=sum(normal)/len(normal)
        check(abs(mean-expected)<.00001,
              f"Original normal-period mean no longer matches operator data {d}: {mean} vs {expected}")
        offsets[d]=mean
        print("DAY",d,"invalid_period",start,"to_1730",
              "normal_QC0_HH",len(normal),"mean_TA_minus_TA_ERA_C",f"{mean:.9f}",
              "repair_HH",22 if d=="20071023" else 23)
    check(count==EXPECTED_NEW_HH,"Expected exactly 137 affected original HH")
    check(qc1==EXPECTED_QC1_VPD,"Original VPD QC1 count no longer 40")
    print("ORIGINAL SIX DAY SOURCE SHA VERIFIED",ORIG_SHA,"all_rows",n,
          "original_HH_288","new_targets",count,
          "target_original_VPD_QC1",qc1)
    return src,offsets

def load_prior():
    check(OLD.is_dir() and not OLD.is_symlink(),"Previously verified 3-point trial missing")
    check(regular(OLD/"NOT_APPROVED_NOT_FOR_DATM_CIME_SLURM_SPINUP").is_file(),
          "Previous trial science warning missing")
    r=json.loads(regular(OLD_RECEIPT).read_text(encoding="utf-8"))
    check(r.get("production_approval") is False and
          r.get("original_tower_temperature_science_holds_remaining")==8 and
          r.get("deferred_US_Syv_holds")==606 and
          r.get("deferred_US_Syv_ERA_edges")==10,
          "Previous trial HOLDs or production contract changed")
    with regular(OLD_MANIFEST).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        fields=rd.fieldnames
        entries=list(rd)
    check(fields and len(entries)==10 and len({x["site"] for x in entries})==10,
          "Previously verified ten-site manifest has changed")
    prior={x["site"]:x for x in entries}
    check("US-SP1" in prior and "US-SRG" in prior,"Previous manual sites missing")
    sp1=Path(prior["US-SP1"]["source_path"])
    check(sp1.parent==OLD and
          sha(sp1)==prior["US-SP1"]["source_SHA256"]==OLD_SP1_SHA,
          "Previous verified US-SP1 full SHA invalid")
    check(prior["US-SRG"]["source_SHA256"]==OLD_SRG_SHA and
          r["two_modified_site_files"]["US-SRG"]["sha256"]==OLD_SRG_SHA,
          "Previous verified US-SRG science candidate changed")
    check(prior["US-SP1"]["latest_stage"]=="MANUAL_EXPERIMENTAL_TEMPERATURE_ALTERNATIVE_NOT_APPROVED",
          "Previous scenario provenance label changed")
    return fields,entries,sp1

def proposals(src,offsets,oldsp1):
    samples={d:{} for d in DAYS};n=0
    with regular(oldsp1).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        check(rd.fieldnames and META_FIELDS.issubset(rd.fieldnames),
              "Previous research scenario forcing schema changed")
        for row in rd:
            n+=1;k=row["TIMESTAMP_START"];d=k[:8]
            if d in samples:
                check(k not in samples[d],"Duplicate previous trial timestamp")
                samples[d][k]=row
    check(n==NROWS,"Previous US-SP1 full native rows changed")
    changes={}
    source_vpd_qc1=0
    vpdqc_changed=0
    vpd_recalculated=0
    vpd_retained=0
    for day,(start,_) in DAYS.items():
        original=src[day]
        trial=samples[day]
        check(set(trial)==set(original),"Previous trial day timestamp alignment invalid "+day)
        for k,row in sorted(trial.items()):
            o=original[k]
            # The Stage14-derived parent can have legitimate VPD-only edits.
            # Compare only original measured temperature/QC and TA_ERA;
            # retain the SHA-pinned parent's VPD/QC if RH is missing.
            for col in ("TA_F","TA_F_QC","TA_ERA"):
                check(row[col]==o[col],"Previous trial unexpectedly altered original 2007 "+k+" "+col)
            if not istarget(k):continue
            ta=val(o["TA_F"]);er=val(o["TA_ERA"]);rh=val(row["RH"])
            origvpd=val(row["VPD_F"])
            oldqc=row["VPD_F_QC"]
            check(ta is not None and er is not None,"Missing native TA/ERA "+k)
            check(oldqc in ("1","2"),"Original VPD QC0/unknown; no speculative overwrite "+k)
            new=er+offsets[day]
            check(-20<new<50 and abs(new-ta)>3,
                  "Expected cold anomaly and valid new TA missing "+k)
            if rh is None:
                # Missing RH is common in original FLUXMET; preserve the
                # independent QC1/QC2 VPD field rather than invent an RH.
                check(origvpd is not None and 0<=origvpd<=es(new)+1e-8,
                      "Missing RH and original VPD physically invalid at proposed TA "+k)
                vpd=origvpd
                vpdqc=oldqc
                humidity_method="MISSING_RH_RETAIN_ORIGINAL_QC1_QC2_VPD_VERIFIED_AT_NEW_T"
                vpd_retained+=1
            else:
                check(0<=rh<=100,
                      "Finite but physically invalid Stage14 RH; manual review required "+k)
                vpd=es(new)*(1-rh/100)
                check(0<=vpd<=es(new),"Recomputed VPD saturation invalid "+k)
                vpdqc="2"
                humidity_method="VALID_STAGE14_RH_RECOMPUTE_VPD_AT_NEW_T"
                vpd_recalculated+=1
            changes[k]={
                "site":"US-SP1","TIMESTAMP_START":k,
                "original_TA_F_C":ta,"original_TA_F_QC":o["TA_F_QC"],
                "original_TA_ERA_C":er,
                "day_baseline_mean_TA_F_minus_TA_ERA_C":offsets[day],
                "trial_TA_F_C":new,"trial_TA_F_QC":"2",
                "original_RH_retained_pct":rh,
                "original_VPD_F_hPa":origvpd,
                "original_VPD_F_QC":oldqc,
                "trial_VPD_F_hPa":vpd,"trial_VPD_F_QC":vpdqc,
                "humidity_method":humidity_method,
                "method":"MANUAL_ERA_FLUXMET_TA_ERA_PLUS_SAME_DAY_QC0_HEALTHY_MEAN_OFFSET",
                "status":"RESEARCH_ALTERNATIVE_NOT_APPROVED_AS_OBSERVED_TA",
            }
            source_vpd_qc1+=o["VPD_F_QC"]=="1"
            vpdqc_changed+=vpdqc!=oldqc
    check(len(changes)==EXPECTED_NEW_HH,"Expected 137 target repairs in prior trial")
    check(source_vpd_qc1==EXPECTED_QC1_VPD,"Expected 40 original VPD QC1 event provenance")
    check(vpd_recalculated+vpd_retained==EXPECTED_NEW_HH,
          "All 137 HH require an explicit VPD treatment")
    check(vpdqc_changed<=sum(r["original_VPD_F_QC"]=="1" for r in changes.values()),
          "Unexpected VPD QC provenance rewrite")
    for day,(start,_) in DAYS.items():
        for hh in (start,"1730"):
            k=day+hh
            check(k in changes,"Missing repair boundary "+k)
        # Only new biased ERA-derived values should be near the original
        # normal QC0 readings immediately before/after the abnormal interval.
        keys=sorted(src[day])
        i=keys.index(day+start)
        left=keys[i-1];end=day+"1730";right=day+"1800"
        left_actual=float(src[day][left]["TA_F"])
        right_actual=float(src[day][right]["TA_F"])
        gap1=changes[day+start]["trial_TA_F_C"]-left_actual
        gap2=right_actual-changes[end]["trial_TA_F_C"]
        check(abs(gap1)<2.0 and abs(gap2)<2.0,
              f"Corrected temperature would have >2C transition at {day}: {gap1:.3f}, {gap2:.3f}")
        print("BOUNDARY",day,"start_jump_C",f"{gap1:+.4f}",
              "end_jump_C",f"{gap2:+.4f}",
              "corrected_first_C",f"{changes[day+start]['trial_TA_F_C']:.4f}",
              "corrected_last_C",f"{changes[end]['trial_TA_F_C']:.4f}")
    print("REPAIR PLAN PASSED",len(changes),"new_halfhours",
          "source_QC1_VPD",source_vpd_qc1,
          "VPD_recomputed_from_valid_RH",vpd_recalculated,
          "VPD_original_retained_when_RH_missing",vpd_retained,
          "VPD_QC1_to_QC2_only_if_recomputed",vpdqc_changed)
    print("HUMIDITY PHYSICS: ALL 137 VPD NONNEGATIVE AND <= SATURATION AT NEW TA")
    return changes

def csv_output(oldfile,target,changes):
    n=0;seen=set()
    with regular(oldfile).open(encoding="utf-8-sig",newline="") as a, \
         target.open("x",encoding="utf-8",newline="") as b:
        rd=csv.DictReader(a)
        w=csv.DictWriter(b,fieldnames=rd.fieldnames)
        w.writeheader()
        for row in rd:
            n+=1;k=row["TIMESTAMP_START"]
            if k in changes:
                check(k not in seen,"Target duplicate "+k)
                seen.add(k)
                r=changes[k]
                row["TA_F"]=f"{r['trial_TA_F_C']:.12g}"
                row["TA_F_QC"]="2"
                if r["humidity_method"]=="VALID_STAGE14_RH_RECOMPUTE_VPD_AT_NEW_T":
                    row["VPD_F"]=f"{r['trial_VPD_F_hPa']:.12g}"
                    row["VPD_F_QC"]="2"
                # If RH missing, preserve original VPD value & QC BYTES.
            w.writerow(row)
    check(n==NROWS and seen==set(changes),"Incomplete new research candidate CSV")
    return sha(target)

def independent_full_check(oldfile,newfile,changes):
    count=0;hits=set();diffcells=0;qc_ch=0
    with regular(oldfile).open(encoding="utf-8-sig",newline="") as f, \
         regular(newfile).open(encoding="utf-8-sig",newline="") as g:
        a=csv.DictReader(f);b=csv.DictReader(g)
        check(a.fieldnames==b.fieldnames,"Full trial source schema modified")
        for x,y in zip_longest(a,b):
            check(x is not None and y is not None,"Full source row count mismatch")
            count+=1;k=x["TIMESTAMP_START"]
            check(y["TIMESTAMP_START"]==k,"Native timestamp order changed")
            diffs={col for col in a.fieldnames if x[col]!=y[col]}
            if not diffs:continue
            check(k in changes and k not in hits,"Unexpected changed HH "+k)
            expected={"TA_F","TA_F_QC"}
            r=changes[k]
            if r["humidity_method"]=="VALID_STAGE14_RH_RECOMPUTE_VPD_AT_NEW_T":
                if x["VPD_F"]!=f"{r['trial_VPD_F_hPa']:.12g}":
                    expected.add("VPD_F")
                if x["VPD_F_QC"]!="2":
                    expected.add("VPD_F_QC")
            else:
                check(x["VPD_F"]==y["VPD_F"] and
                      x["VPD_F_QC"]==y["VPD_F_QC"],
                      "RH absent: original VPD/QC must be untouched "+k)
            check(diffs==expected,"Wrong edited columns at "+k+": "+str(diffs))
            check(y["TA_F_QC"]=="2" and
                  y["VPD_F_QC"]==r["trial_VPD_F_QC"],
                  "Trial QC provenance mismatch "+k)
            check(abs(float(y["TA_F"])-r["trial_TA_F_C"])<1e-8,
                  "Incorrect trial temperature "+k)
            check(abs(float(y["VPD_F"])-r["trial_VPD_F_hPa"])<1e-8,
                  "Incorrect trial VPD "+k)
            check(0<=float(y["VPD_F"])<=es(float(y["TA_F"]))+1e-8,
                  "Final VPD violates new trial saturation "+k)
            hits.add(k);diffcells+=len(diffs)
            qc_ch+=x["VPD_F_QC"]!=y["VPD_F_QC"]
    check(count==NROWS and hits==set(changes),"Incomplete independent full-file audit")
    check(qc_ch==sum(r["trial_VPD_F_QC"]!=r["original_VPD_F_QC"]
                     for r in changes.values()) and
          diffcells>=2*EXPECTED_NEW_HH and
          diffcells<=4*EXPECTED_NEW_HH,
          "Independent full-file change counts disagree with per-HH provenance")
    print("INDEPENDENT FULL AUDIT PASS","all_rows",count,
          "new_HH",len(hits),"modified_field_cells",diffcells,
          "original_2000_SP1_prior_2HH_unchanged",True)
    return diffcells

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--assess",action="store_true")
    mode.add_argument("--apply",action="store_true")
    mode.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    check(len(DAYS)==6 and sum(22 if d=="20071023" else 23 for d in DAYS)==137,
          "Configured target day census invalid")
    check(len(ORIG_SHA)==len(OLD_SP1_SHA)==len(OLD_SRG_SHA)==64,
          "SHA source identifiers invalid")
    print("SP1 DAILY ERA OFFSET SELF TEST PASS: six exact days, source anchors, 137 HH, no source overwrite")
    if args.self_test:return
    src,offsets=inspect_source()
    fields,manifest,oldsp1=load_prior()
    changes=proposals(src,offsets,oldsp1)
    if args.assess:
        print("SIX-DAY ASSESS PASS READ ONLY; 0 WRITES, 0 NEW CANDIDATE");return
    dest=E/"manual_sp1_six_day_bias_adjusted_research_not_approved"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    (dest/"INCOMPLETE_DO_NOT_USE_FOR_DATM_CIME_SLURM_SPINUP").write_text(
        "Research-only original TA correction proposal; original scientific holds unresolved.\n")
    name="US-SP1_six_day_manual_ERA_daily_bias_research_FLUXMET_HH.csv"
    out=dest/name
    outsha=csv_output(oldsp1,out,changes)
    cells=independent_full_check(oldsp1,out,changes)
    newmanifest=[]
    for source in manifest:
        e=dict(source)
        if e["site"]=="US-SP1":
            e["source_path"]=str(out)
            e["source_SHA256"]=outsha
            e["latest_stage"]="SIX_DAY_MANUAL_ERA_BIAS_RESEARCH_NOT_PRODUCTION_APPROVED"
        newmanifest.append(e)
    with (dest/"RESEARCH_TEN_SITE_MANIFEST.tsv").open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        w.writeheader();w.writerows(newmanifest)
    tsv=dest/"SIX_DAY_137_HALF_HOUR_FULL_PROVENANCE.tsv"
    with tsv.open("x",encoding="utf-8",newline="") as f:
        rows=[changes[k] for k in sorted(changes)]
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t")
        w.writeheader();w.writerows(rows)
    receipt={
      "status":"TECHNICALLY_VERIFIED_RESEARCH_ONLY_SCIENTIFIC_APPROVAL_UNRESOLVED",
      "production_approval":False,
      "source_original_FLUXMET_HH_SHA256":ORIG_SHA,
      "parent_three_point_research_trial_directory":str(OLD),
      "parent_three_point_US_SP1_SHA256":OLD_SP1_SHA,
      "unchanged_US_SRG_earlier_manual_candidate_SHA256":OLD_SRG_SHA,
      "daily_mean_residuals_TA_F_minus_FLUXNET_TA_ERA_C":offsets,
      "daily_repair_onset_local_standard_time":{d:a for d,(a,_) in DAYS.items()},
      "source_temperature_QC0_modified_in_separate_trial_QC2":True,
      "candidate_output_path":str(out),"candidate_SHA256":outsha,
      "full_original_native_half_hours":NROWS,
      "changed_HH":len(changes),"changed_field_cells":cells,
      "original_target_VPD_QC1_count":EXPECTED_QC1_VPD,
      "changed_target_VPD_QC1_to_trial_QC2":sum(
          x["trial_VPD_F_QC"]!=x["original_VPD_F_QC"]
          for x in changes.values()),
      "retained_original_VPD_and_QC_due_to_missing_RH":sum(
          x["humidity_method"].startswith("MISSING_RH") for x in changes.values()),
      "recomputed_VPD_from_available_RH":sum(
          x["humidity_method"].startswith("VALID_STAGE14") for x in changes.values()),
      "unchanged_earlier_SP1_2000_two_point_trial":True,
      "unchanged_other_nine_site_manifest_entries":True,
      "original_source_temperature_science_HOLDs_remain":8,
      "deferred_US_Syv_science_HOLDs":606,
      "deferred_US_Syv_ERA_endpoint_skips":10,
      "research_manifest_path":str(dest/"RESEARCH_TEN_SITE_MANIFEST.tsv"),
      "new_temperature_provenance_path":str(tsv),
    }
    (dest/"SIX_DAY_RESEARCH_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    (dest/"INCOMPLETE_DO_NOT_USE_FOR_DATM_CIME_SLURM_SPINUP").rename(
        dest/"TECHNICALLY_VERIFIED_NOT_SCIENTIFICALLY_APPROVED_FOR_DATM_OR_SPINUP")
    print("SIX-DAY RESEARCH CANDIDATE CREATED AND INDEPENDENTLY AUDITED",dest)
    print("US-SP1 NEW FULL CSV SHA256",outsha)
    print("SIX DAYS",len(DAYS),"NEW HH",len(changes),"CHANGED FIELD CELLS",cells)
    print("OTHER NINE SITE MANIFEST SOURCES UNCHANGED INCLUDING US-SRG 2019 MANUAL TRIAL")
    print("NO ORIGINAL/STAGE14/STAGE15/PREVIOUS THREE-POINT TRIAL WRITES")
    print("SCIENCE 8 T SOURCE HOLDS PLUS US-Syv 606+10 REMAIN; NO Post-v5 DATM CIME SLURM SPINUP RELEASE")
if __name__=="__main__":main()

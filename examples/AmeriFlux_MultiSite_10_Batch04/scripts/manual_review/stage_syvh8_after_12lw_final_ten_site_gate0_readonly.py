#!/usr/bin/env python3
"""Batch04 SYVH8: after five-site 12 LW_IN_ERA research corrections, ten-site Gate-0.

NO MODIFICATIONS. Import the exact sibling SYVH5+SYVH6 source-physics
auditors and verify the newly created SYVH7 receipt's input SHA, output SHA,
original exact parent ten-site selected manifest, and every one of its new
affected-five-site source paths. Recalculate all ten native 7-met+NOLEAP
audits and report source VPD precision-only exceptions separately.

Gate-0 successful NUMERIC_10_OF_10 is NOT full scientific model release;
ZBOT, rainfall height, CIME time centering and site-level remaining source
QC/human approvals must be independently checked before DATM.
"""
import argparse,csv,hashlib,importlib.util,json
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
OLD=ROOT/"manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c/RESEARCH_TEN_SITE_MANIFEST.tsv"
HERE=Path(__file__).resolve().parent
H5=HERE/"stage_syvh5_ten_site_vpd_driven_humidity_readiness_readonly.py"
H6=HERE/"stage_syvh6_ten_site_postv5_gate0_all_meteorology_readonly.py"
AFFECTED={"US-SP1":4,"US-Slt":2,"US-Syv":2,"US-Ton":2,"US-Uaf":2}
ALL10={"US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
       "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf"}
N_SYV=438288
FINAL_SYV_SHA="9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa"
def ck(ok,msg):
    if not ok:raise ValueError(msg)
def reg(p):
    ck(p.is_file() and not p.is_symlink(),"Original or final source missing/symlink "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with reg(p).open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()
def table(p):
    with reg(p).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        ck(rd.fieldnames and
           {"site","source_path","source_SHA256","latest_stage"}.issubset(rd.fieldnames),
           "Selected source manifest missing required fields")
        data=list(rd)
    ck(len(data)==10 and set(x["site"] for x in data)==ALL10,
       "Ten-site final research roster unexpected")
    return data
def mod(path,name):
    ck(path.is_file() and not path.is_symlink(),
       "Required pinned independent audit module missing "+str(path))
    spec=importlib.util.spec_from_file_location(name,str(path))
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
def run():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--candidate-dir",required=True)
    g=a.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--report",action="store_true")
    args=a.parse_args()
    d=Path(args.candidate_dir)
    ck(d.is_dir() and not d.is_symlink(),"SYVH7 candidate directory missing")
    receipt=json.loads(reg(d/"SYVH7_RESEARCH_RECEIPT.json").read_text(encoding="utf-8"))
    ck(receipt.get("scientific_stage")=="SYVH7_12_LOW_LW_PAIRS_RESEARCH_ONLY" and
       receipt.get("production_approval") is False and
       receipt.get("DATM_ready") is False and
       receipt.get("exact_source_12_low_LW_HH")==12 and
       receipt.get("affected_site_count")==5 and
       receipt.get("final_original_SYVH3_Syv_SHA")==FINAL_SYV_SHA,
       "SYVH7 research science receipt contract differs")
    ck(Path(receipt["new_manifest"])==d/"RESEARCH_TEN_SITE_MANIFEST.tsv" and
       sha(d/"RESEARCH_TEN_SITE_MANIFEST.tsv")==
       receipt["new_manifest_SHA256"] and
       sha(OLD)==receipt["input_manifest_SHA256"],
       "Source/derived ten-site manifest SHA invalid")
    old=table(OLD);new=table(d/"RESEARCH_TEN_SITE_MANIFEST.tsv")
    was={x["site"]:x for x in old};now={x["site"]:x for x in new}
    ck(len(was)==len(now)==10 and set(now)==ALL10,
       "Duplicated or missing final selection site")
    newsha=receipt["site_new_source_SHA256"]
    ck(set(newsha)==set(AFFECTED),"Not exactly five operator-reviewed new LW sources")
    for site in ALL10:
        r=now[site]
        path=Path(r["source_path"])
        ck(sha(path)==r["source_SHA256"],"Final selected source SHA differs "+site)
        if site in AFFECTED:
            ck(path.parent==d and
               r["source_SHA256"]==newsha[site] and
               r["latest_stage"]==
                   "SYVH7_12_LOW_LW_PAIRED_FLUXNET_ERA_RESEARCH_NOT_APPROVED",
               "Affected LW research source not pinned "+site)
        else:
            ck(r==was[site],"Unaffected original research source changed "+site)
    ledger=d/"SYVH7_EXACT_12_HH_LW_ORIGINAL_AND_PAIRED_ERA.tsv"
    with reg(ledger).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        ck(rd.fieldnames and
           {"site","TIMESTAMP_START","new_research_LW_IN_F_Wm2"}.issubset(rd.fieldnames),
           "New 12HH source ERA longwave ledger schema differs")
        rr=list(rd)
    c=Counter(r["site"] for r in rr)
    ck(len(rr)==12 and dict(c)==AFFECTED and
       len({(r["site"],r["TIMESTAMP_START"]) for r in rr})==12,
       "Source historical 12 LW event counts changed")
    a5=mod(H5,"batch04_syvh8_h5")
    a6=mod(H6,"batch04_syvh8_h6")
    a6.selftest(a5)
    print("SYVH8 VERIFIED FIVE SOURCE LW REPLACEMENT SHAS AND 12HH ERA/QC PROVENANCE")
    results=[]
    for site in sorted(ALL10):
        results.append(a6.analyze(site,now[site],a5))
    blocked={r["site"]:r["numeric_blockers"] for r in results if r["numeric_blockers"]}
    rounding=sum(r["conservative_nonproduction_policy_flags"].get(
             "VPD_NATIVE_THREE_DECIMAL_ROUNDING",0) for r in results)
    ck(rounding==3,
       "Unexpected three source VPD three-decimal quantisation cases after LW changes")
    print("SYVH8 POST-SYVH7 TEN SITE GATE0", "FULL_DATA_SITES",10,
          "NUMERICAL_READY_SITES",10-len(blocked),
          "BLOCKED_SITES",blocked,
          "SOURCE_VPD_ROUNDING_HH",rounding)
    if blocked:
        print("SYVH8 SITE SCIENCE NUMERIC BLOCKERS REMAIN; NO SPINUP AUTHORISED")
    else:
        print("SYVH8 ALL TEN PRIMARY SEVEN MET NOLEAP NUMERIC GATE0 PASS")
    if args.report:
        dest=Path.home()/"ameriflux_batch04_manual_review"
        dest.mkdir(parents=True,exist_ok=True)
        name=("Batch04_SYVH8_POST_12LW_TEN_SITE_MET_GATE0_"+
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
        output=dest/(name+".json")
        output.write_text(json.dumps({
            "source_manifest":str(d/"RESEARCH_TEN_SITE_MANIFEST.tsv"),
            "source_manifest_sha256":receipt["new_manifest_SHA256"],
            "source_LW_operator_source_ledger":str(ledger),
            "all_ten_native_source_SA_verified":True,
            "research_only":True,"numeric_blockers":blocked,
            "nine_plus_one_site_full_results":results,
            "primary_met_numeric_gate0_pass":not bool(blocked),
            "unapproved_ZBOT_surface_PFT_CIME_release":True,
            "model_jobs_submitted":False},indent=2)+"\n",encoding="utf-8")
        print("SYVH8 READONLY GATE0 JSON",output,"SHA256",sha(output))
    print("SYVH8 NO CHANGES TO ORIGINAL, SOURCE, DATM, CIME, SURFACE OR SLURM")
if __name__=="__main__":run()

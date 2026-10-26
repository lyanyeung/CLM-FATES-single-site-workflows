#!/usr/bin/env python3
"""Stage95: ten-site versioned operator-QC0-approved forcing + 215 yearly NC.

Strictly reuses SHA-verified existing Stage87/92 selected source forcings,
original Stage93 122 QC0 event proof, Stage94 27/33 approved episodes and
the user's exact final approval of THREE US-ICt VPD episodes (87+1+1).
Creates truly separate forcing copies and REGENERATES all 215 NOLEAP NC
using pinned Stage87 code; compares every new NC variable to its corresponding
source preview. Re-runs Stage07 independent numeric provenance audit and
Stage09 Post-v5 physics/source/extreme tests on the versioned forcing.

Source QC1/QC2 Ho1 2000 temperature transition remains a SCIENCE HOLD.
No original/old CSV, NC, case, DATM stream, surface, or Slurm job changed.
Even a 10/10 PASS is an approved-QC0 candidate, NOT production permission.
"""
import argparse,csv,hashlib,importlib.util,json,math,shutil,sys
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
S87=ROOT/"reports/stage87_five_site_DATM_NetCDF_technical_preview_20261026T003934Z_30692f63"
S92=ROOT/"reports/stage92_five_site_complete_forcing_candidates_20261026T023951Z_ca1243de"
S93=ROOT/"reports/stage93_ten_site_postv5_QC0_manual_triage_20261026T025946Z_97c41d3b"
S94=ROOT/"reports/stage94_30_QC0_final_operator_decisions_20261026T032553Z_94d4c9ab"
PINS={"stage93":("93_ten_site_postv5_and_manual_decision_priority.py",
 "1d06c2b68d1ebc7f108be32abd358771dc8e9326"),
 "stage94":("94_qc0_final_operator_decision_table.py",
 "9193bc91a92e27b0deca87030697ae222919b65a"),
 "stage09":("09_post_qcv5_batch02.py",
 "b2353089ff15b95b6a25c5c0e2fcf4e7be2671c7"),
 "stage87":("87_build_five_verified_Stage07_DATM_noleap_technical_preview.py",
 "4f62ba03f52b41b98d7b6db3e89af2bf10bee8a1")}
QC0_BY_SITE={"US-BZS":1,"US-CMW":2,"US-EML":3,"US-GLE":0,
 "US-Ha1":2,"US-Ho1":5,"US-Ho2":19,"US-Ho3":0,"US-ICh":0,"US-ICt":90}
YEARS={"US-BZS":15,"US-CMW":21,"US-EML":16,"US-GLE":16,
       "US-Ha1":35,"US-Ho1":28,"US-Ho2":27,"US-Ho3":19,
       "US-ICh":19,"US-ICt":19}
USER_NEW={
 ("US-ICt","VPD_F","2016-05-21 15:30:00","2016-05-23 10:30:00",87),
 ("US-ICt","VPD_F","2008-08-07 19:00:00","2008-08-07 19:00:00",1),
 ("US-ICt","VPD_F","2008-09-18 12:30:00","2008-09-18 12:30:00",1)}
SOURCE_FIELDS={"TA_F":"TA_USE","VPD_F":"VPD_USE","LW_IN_F":"FLDS",
               "PA_F":"PSRF","SW_IN_F":"FSDS","WS_F":"WIND","P_F":"PRECTmms"}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def gitblob(p):
    b=Path(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def loadmodule(p,name):
    spec=importlib.util.spec_from_file_location(name,p)
    if spec is None or spec.loader is None:raise ValueError("Cannot import "+str(p))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
def csvread(p):
    with Path(p).open(newline="",encoding="utf8") as fh:
        return list(csv.DictReader(fh))
def csvwrite(p,rows,fields):
    with Path(p).open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)
def key(e):
    return (e["site"],e["variable"],e["first"],e["last"],int(e["native_records"]))
def sign_source(run):
    for name,exp in PINS.values():
        p=run/name
        if not p.is_file() or gitblob(p)!=exp:
            raise ValueError("Pinned source module unavailable or changed: "+name)
    return (
        loadmodule(run/PINS["stage93"][0],"stage95_original_stage93"),
        loadmodule(run/PINS["stage94"][0],"stage95_original_stage94"),
        loadmodule(run/PINS["stage09"][0],"stage95_original_stage09"),
        loadmodule(run/PINS["stage87"][0],"stage95_original_stage87"))

def operator_ledger(st94):
    m,events,ho1=st94.gate()
    digest=j(S94/"manifest.json")
    if (digest.get("human_episodes")!=30 or
        digest.get("QC0_original_variable_records")!=122 or
        digest.get("operator_approved_conditional_QC0_variable_records")!=33 or
        digest.get("operator_remaining_QC0_HOLD_variable_records")!=89 or
        digest.get("production_DATM_approved") is not False):
        raise ValueError("Stage94 exact 33/89 evidence and existing scientific HOLD changed")
    for name,value in digest["reports_sha256"].items():
        if sha(S94/name)!=value:raise ValueError("Stage94 decision receipt SHA mismatch "+name)
    old_approved=csvread(S94/"operator_approved_conditional_QC0_episodes.csv")
    old_held=csvread(S94/"operator_remaining_QC0_HOLD_episodes.csv")
    if len(old_approved)!=27 or len(old_held)!=3:
        raise ValueError("Stage94 expected 27 already-approved / 3 user-new episodes")
    oldapp={e["decision_id"] for e in old_approved}
    oldhold={e["decision_id"] for e in old_held}
    if len(oldapp)!=27 or len(oldhold)!=3 or oldapp&oldhold:
        raise ValueError("Stage94 original decision ID duplication")
    verdict=st94.ho1_conditional_era_decision(ho1)
    stored=j(S94/"Ho1_2000_Dec27_0900_user_conditional_ERA.json")
    if (verdict!=stored or verdict["operator_condition_met"] is not False or
        verdict["source_decision"]!="HOLD_PRECEDING_T_NOT_NEAR_ZERO_DO_NOT_USE_ERA"):
        raise ValueError("Ho1 original preceding -15.7/-15.1C source condition altered")
    decisions=[]
    covered=set()
    for i,e,rows in events:
        d=st94.evaluate(i,e,rows)
        episode=key(e)
        id_=d["decision_id"]
        if id_ in oldapp:
            if d["operator_choice"]!="APPROVE_CANDIDATE":
                raise ValueError("Stage94 accepted condition no longer reproducible "+id_)
            basis="STAGE94_PREVIOUS_USER_CONDITIONAL"
        elif id_ in oldhold:
            if d["operator_choice"]!="HOLD" or episode not in USER_NEW:
                raise ValueError("An unapproved Stage94 HOLD is outside user's three named US-ICt episodes")
            basis="USER_2026_10_26_EXPLICIT_US_ICt_89_VPD_APPROVAL"
            d["operator_choice"]="APPROVE_CANDIDATE"
        else:
            raise ValueError("Stage94 episode missing in operator signoff "+id_)
        d["decision_provenance"]=basis
        d["production_approved"]="NO"
        decisions.append(d)
        covered.add(episode)
    if len(decisions)!=30 or len(covered)!=30:
        raise ValueError("Operator approved exact episode population changed")
    overrides={key(e) for i,e,rows in events if
        st94.evaluate(i,e,rows)["decision_id"] in oldhold}
    if overrides!=USER_NEW:
        raise ValueError("User's 87+1+1 source events not exact")
    if sum(int(d["native_records"]) for d in decisions)!=122:
        raise ValueError("User signed exact 122 changed original QC0 variable records required")
    r93=csvread(S93/"all_122_QC0_original_source_candidate_nearest_neighbors.csv")
    bysite=defaultdict(list)
    linked=set()
    for d in decisions:
        site,var=d["site"],d["variable"]
        start,end=d["start_local"],d["end_local"]
        rows=[r for r in r93 if r["site"]==site and r["variable"]==var and start<=r["time"]<=end]
        if len(rows)!=int(d["native_records"]):
            raise ValueError("Decision did not cover its exact original QC0 records "+d["decision_id"])
        for r in rows:
            stamp=(r["site"],r["variable"],r["time"])
            if stamp in linked:raise ValueError("QC0 record covered by multiple decisions")
            linked.add(stamp)
            row=dict(r,decision_id=d["decision_id"],
                     operator_decision="APPROVE_CANDIDATE",
                     decision_provenance=d["decision_provenance"],
                     production_DATM_approved="NO")
            bysite[site].append(row)
    if len(linked)!=122 or Counter({k:len(v) for k,v in bysite.items()})!=Counter(
         {k:v for k,v in QC0_BY_SITE.items() if v}):
        raise ValueError("122 original QC0 records or ten-site population incomplete")
    print("STAGE95 USER DECISIONS VERIFIED | Stage94 33 + final US-ICt 89 = 122 QC0 source-variable records; 30 episodes",flush=True)
    print("STAGE95 HO1 09:00 SOURCE CONDITION NOT MET | ERA replacement prohibited; 274 non-QC0 2000 T remain source SCIENCE HOLD",flush=True)
    return decisions,bysite,verdict

def source_audit_copy(site,info,oldroot,dest,bysite):
    start,end=int(info["first_year"]),int(info["last_year"])
    srccsv=Path(oldroot)/site/"forcing/processed_v5"/f"{site}_CLM_forcing_{start}_{end}.csv"
    outdir=dest/site/"forcing/processed_v5"
    outdir.mkdir(parents=True,exist_ok=True)
    csvout=outdir/srccsv.name
    shutil.copyfile(srccsv,csvout)
    oldsha=sha(srccsv)
    if sha(csvout)!=oldsha:raise ValueError("Copied forcing differs from selected source "+site)
    qcsource=Path(oldroot)/site/"forcing/qc_v5"
    qcout=dest/site/"forcing/qc_v5"
    qcout.mkdir(parents=True,exist_ok=True)
    qcfiles={}
    for pattern in ("*_replacement_events.csv","*_manual_review.csv","*_qc_summary.csv","*_status.json"):
        group=list(qcsource.glob(site+pattern.removeprefix("*")))
        if len(group)!=1:raise ValueError("Original source event evidence missing or not unique "+site+" "+pattern)
        p=group[0];out=qcout/p.name
        shutil.copyfile(p,out)
        if sha(p)!=sha(out):raise ValueError("Source event evidence copied incorrectly "+str(p))
        qcfiles[p.name]=sha(out)
    target=[r for r in bysite.get(site,[])]
    if len(target)!=QC0_BY_SITE[site]:
        raise ValueError("Operator source QC0 count differed "+site)
    wanted={r["time"]:[] for r in target}
    for r in target:wanted[r["time"]].append(r)
    cols=["time",*sorted(set(SOURCE_FIELDS[x["variable"]] for x in target))]
    if len(cols)==1:cols=["time","TA_USE"]
    # A native timestamp may contain more than one variable edit.
    checked=set()
    for chunk in pd.read_csv(csvout,usecols=cols,chunksize=250000):
        sub=chunk.loc[chunk["time"].isin(wanted)]
        for row in sub.to_dict("records"):
            stamp=row["time"]
            for spec in wanted[stamp]:
                variable=spec["variable"]
                field=SOURCE_FIELDS[variable]
                actual=float(row[field])
                expected=float(spec["candidate_value"])
                # Stage93 display CSV rounds original candidate to five
                # decimals, so exact source must agree within 0.00002 units.
                if not (math.isfinite(actual) and abs(actual-expected)<2e-5):
                    raise ValueError("User approved candidate value differs: "+site+" "+stamp+" "+variable)
                id_=(stamp,variable)
                if id_ in checked:raise ValueError("Duplicate forcing timestamp/variable in source "+site)
                checked.add(id_)
    if len(checked)!=len(target):
        raise ValueError("Operator 122 original QC0 records missing from candidate source "+site)
    return csvout,oldsha,qcfiles

def readback_new_nc(ncmod,produced,old):
    with ncmod.nc.Dataset(produced) as a, ncmod.nc.Dataset(old) as b:
        if set(ncmod.NC_FIELDS)-set(a.variables) or set(ncmod.NC_FIELDS)-set(b.variables):
            raise ValueError("NC canonical meteorology fields changed")
        if (len(a.dimensions["time"])!=len(b.dimensions["time"]) or
            a.variables["time"].calendar!="noleap"):
            raise ValueError("Native NOLEAP NC time count changed")
        fields=("time","lat","lon",*ncmod.NC_FIELDS)
        for col in fields:
            aa=np.asarray(a.variables[col][:],dtype="float64")
            bb=np.asarray(b.variables[col][:],dtype="float64")
            if aa.shape!=bb.shape or not np.array_equal(aa,bb):
                raise ValueError("Independent 215-NC canonical field discrepancy "+str(produced)+" "+col)
        if a.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY":
            raise ValueError("Production scientific release incorrectly granted on NC")

def site_process(job,dest,by_site,mods,helper):
    site,info,source_root,source_forcing,events_path=job
    stage09,ncmod=mods
    output,original_sha,qcsha=source_audit_copy(site,info,source_root,dest,by_site)
    # A new full-site forcing file and original-to-event provenance now exist.
    audit=helper.independent_audit(info,dest)
    if audit.get("status")!="CANDIDATE_NUMERIC_OK_REVIEW_REQUIRED":
        raise ValueError("Original-source-to-versioned-forcing independent numeric audit failed "+site)
    summary,extremes,qc0,annual=stage09.science_review(info,dest,output)
    if (summary.get("QC0_edits")!=QC0_BY_SITE[site] or
        summary.get("RH_NONPOSITIVE")!=0 or
        summary.get("QBOT_OUTSIDE_0_TO008")!=0 or
        summary.get("NEW_TA_NATIVE_STEP_RATE_GT16C_H")!=0):
        raise ValueError("Versioned Post-v5 physical/new-temperature-extreme/QC0 gate failed "+site)
    report=dest/site/"postv5"
    report.mkdir(parents=True,exist_ok=True)
    (report/"postv5_summary.json").write_text(json.dumps(
        {"numeric":audit,"science":summary,
         "production_DATM_approved":False,
         "raw_source_changes_applied_to_selected_forcing":False},
        indent=2,default=str)+chr(10))
    pd.DataFrame(annual).to_csv(report/"annual_extreme_counts.csv",index=False)
    # Retain all flags as science evidence, NOT automatically permission.
    extremes.to_csv(report/"all_native_extreme_and_source_review.csv",index=False)
    first,last=int(info["first_year"]),int(info["last_year"])
    entry={"site":site,"first_year":first,"last_year":last,
           "step":info["native_minutes"],"source":output,
           "sha256":sha(output)}
    surf,surfsha,lat,lon=ncmod.point_surface(site)
    source_m=j(S87/"manifest.json") if site in (
          "US-BZS","US-CMW","US-Ha1","US-Ho2","US-Ho3") else j(S92/"manifest.json")
    srcinfo=next(x for x in source_m["sites"] if x["site"]==site)
    originals=srcinfo["yearly_netcdf_files"] if site in (
          "US-BZS","US-CMW","US-Ha1","US-Ho2","US-Ho3") else srcinfo["netcdf_year_files"]
    old_by_year={int(x["year"]):x for x in originals}
    folder=dest/site/"noleap_yearly_NC_TECHNICAL_NOT_ACTIVE"
    folder.mkdir(parents=True,exist_ok=True)
    files=[]
    for year,rows in ncmod.site_years(entry):
        out=folder/(str(year)+".nc")
        ncmod.save_nc(out,entry,year,rows,lat,lon,surfsha)
        # Stage87 writer retains FALSE_TECHNICAL_PREVIEW_ONLY. Attach the
        # operator decision proof but NEVER label a preview as active DATM.
        with ncmod.nc.Dataset(out,"a") as dataset:
            dataset.user_QC0_decision="122_original_QC0_variable_edits_approved_20261026"
            dataset.production_DATM_release="NO_Ho1_nonQC0_2000_and_clock_ZBOT_pending"
            dataset.scientific_site_provenance="versioned_source_copy_and_source_event_ledger_verified"
        before=Path(old_by_year[year]["path"])
        if sha(before)!=old_by_year[year]["sha256"]:
            raise ValueError("Prior NC changed while reproducing original candidate "+site+" "+str(year))
        readback_new_nc(ncmod,out,before)
        files.append({"year":year,"path":str(out),"sha256":sha(out)})
    if len(files)!=YEARS[site]:
        raise ValueError("Site NC annual complete time coverage failed "+site)
    templ=ncmod.make_template(folder,site,range(first,last+1))
    result={"site":site,"year_count":YEARS[site],"source_forcing_csv":str(source_forcing),
            "versioned_forcing":str(output),"source_forcing_sha256":original_sha,
            "versioned_forcing_sha256":sha(output),
            "original_event_files_sha256":qcsha,
            "QC0_user_approved_variable_records":QC0_BY_SITE[site],
            "independent_numeric_audit":"PASS","postv5_numeric_extremes_audit":"PASS",
            "postv5_summary":summary,"NC_technical_preview_files":files,
            "NC_count":len(files),
            "site_surface_SHA256":surfsha,
            "unactivated_stream_template":str(templ),
            "unactivated_stream_template_SHA256":sha(templ),
            "production_DATM_approved":False}
    print("STAGE95 SITE PASS",site,"QC0",QC0_BY_SITE[site],
          "NC",len(files),"Post-v5 OK; production DATM NOT ACTIVATED",flush=True)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    for flag in ("self-test","check","build"):
        g.add_argument("--"+flag,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert sum(YEARS.values())==215 and sum(QC0_BY_SITE.values())==122
        assert sum(x[-1] for x in USER_NEW)==89 and len(USER_NEW)==3
        assert len(USER_NEW)==3 and len(PINS)==4
        print("STAGE95 SELF-TEST PASS | 122 exact approvals (33+89), 215 annual NC; no writes",flush=True)
        return 0
    run=Path(__file__).resolve().parent
    st93,st94,stage09,ncmod=sign_source(run)
    jobs=st93.verify_inputs()
    decisions,by_site,ho1=operator_ledger(st94)
    originals=j(S07/"exact_input_manifest.json")
    helperpath=[Path(k) for k in originals["input_sha256"]
                if Path(k).name=="07_build_batch02_qcv5_candidates.py"]
    if len(helperpath)!=1:raise ValueError("Original pinned Stage07 numerical audit module not unique")
    hp=helperpath[0]
    if sha(hp)!=originals["input_sha256"][str(hp)]:
        raise ValueError("Original Stage07 checksum-pinned independent auditor changed")
    helper=loadmodule(hp,"stage95_independent_original_QC")
    if a.check:
        print("STAGE95 CHECK PASS | 10 sites, all 215 original NC SHA, 122 explicit user-approved QC0 edits, Ho1 hold, no writes",flush=True)
        return 0
    output=ROOT/"reports"/("stage95_ten_site_122_user_approved_versioned_forcing_215NC_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    incomplete=output/"INCOMPLETE_DO_NOT_USE"
    incomplete.write_text("Never activate incomplete numerical site candidates."+chr(10))
    (output/"SCIENCE_HOLD_DO_NOT_ACTIVATE_DATM_OR_SUBMIT").write_text(
        "Original Ho1 year 2000 non-QC0 source-T transition 18.746C, source/clock/interval/ZBOT/landunit/PFT/CIME approvals remain; these are independent research candidates."+chr(10))
    fields=list(decisions[0])
    csvwrite(output/"30_user_approved_QC0_source_episodes.csv",decisions,fields)
    full=[]
    for site in sorted(by_site):full.extend(by_site[site])
    csvwrite(output/"122_user_approved_original_QC0_variable_records.csv",full,
             list(full[0]))
    (output/"Ho1_original_QC1_QC2_science_hold.json").write_text(
        json.dumps(ho1,indent=2)+chr(10))
    statuses=[]
    for job in jobs:
        site=job[0]
        print("\nSTAGE95 BUILD VERSIONED",site,flush=True)
        try:
            done=site_process(job,output,by_site,(stage09,ncmod),helper)
            statuses.append(done)
        except Exception as e:
            print("STAGE95 SITE HOLD/FAIL",site,type(e).__name__,str(e),flush=True)
            statuses.append({"site":site,"status":"FAIL","error":str(e),
                "production_DATM_approved":False})
        (output/"progress.json").write_text(json.dumps(statuses,indent=2,default=str)+chr(10))
    complete=sum(s.get("NC_count",0) for s in statuses)
    count=sum("NC_count" in x for x in statuses)
    srcsha_changed=[]
    for job in jobs:
        src=Path(job[3])
        ver=output/job[0]/"forcing/processed_v5"/src.name
        if not src.is_file() or not ver.is_file() or sha(src)!=sha(ver):
            srcsha_changed.append(str(src))
    result={"schema":"STAGE95_BATCH02_VERSIONED_122_ORIGINAL_QC0_APPROVED_10SITE_215_NC_v1",
      "operator_approval_20261026":{"prior_Stage94_QC0_variables":33,
             "new_user_approved_US_ICt_QC0_VPD_variables":89,
             "all_user_approved_original_QC0_variables":122,
             "exact_user_new_episodes":list(map(list,sorted(USER_NEW)))},
      "site_pass":count,"site_requested":10,
      "annual_netcdf_generated_and_readback_verified":complete,
      "annual_netcdf_requested":215,
      "source_forcing_sha256_unchanged":not srcsha_changed,
      "source_forcing_changed":srcsha_changed,
      "stage93_report_manifest_sha256":sha(S93/"manifest.json"),
      "stage94_report_manifest_sha256":sha(S94/"manifest.json"),
      "stage87_report_manifest_sha256":sha(S87/"manifest.json"),
      "stage92_report_manifest_sha256":sha(S92/"manifest.json"),
      "Ho1_QC1_QC2_gap_temperature_jump_scientifically_approved":False,
      "site_timezone_interval_center_ZBOT_landunit_PFT_CIME_verified":False,
      "production_DATM_approved":False,"Slurm_jobs_submitted":False,
      "old_source_CIME_NC_files_modified":False,
      "sites":statuses}
    (output/"manifest.json").write_text(json.dumps(result,indent=2,default=str)+chr(10))
    if count==10 and complete==215 and not srcsha_changed:
        incomplete.unlink()
        print("STAGE95 VERSIONED 10 SITE POST-V5 PASS | 122 USER QC0 APPROVED; 215 REGENERATED NOLEAP NC VERIFIED",flush=True)
    else:
        print("STAGE95 PARTIAL HOLD | site",count,"/10 annual_NC",complete,
            "/215 input_source_changed",bool(srcsha_changed),flush=True)
    print("STAGE95 REPORT",output,flush=True)
    print("STAGE95 SCIENCE HOLD | US-Ho1 nonQC0 source T / clocks / ZBOT / PFT / CIME; NO DATM ACTIVATION OR SLURM",flush=True)
    return 0 if count==10 and complete==215 and not srcsha_changed else 2

if __name__=="__main__":
    raise SystemExit(main())

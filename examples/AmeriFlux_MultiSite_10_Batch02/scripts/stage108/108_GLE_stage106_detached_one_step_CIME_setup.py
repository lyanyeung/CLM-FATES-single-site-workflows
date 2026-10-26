#!/usr/bin/env python3
"""Batch02 Stage108: GLE one-step CIME DATA-READ test case CONFIGURATION ONLY.

--check: source SHA gates Stage106 true-dated ERA backfilled 2005–2020
         and successful Stage107 28-window comparison; no writes.
--prepare: unique GF-Guy keepexe clone using prior proven Stage103 site
           user_mods, same original GLE surface and exact 16 Stage106 NC.
           nsteps=1; RESUBMIT=0; datafiles provenance pinned. CIME case.setup,
           preview_namelists only. NO case.build, model run, case.submit,
           sbatch, srun or input-data rewrites.

2009–2019 is recorded as leading future spinup *candidate*; one-step
CIME stream test uses FULL 2005–2020 to test 2005-01-01 ERA backfill.
The CIME/ERA model data READ is not verified until an explicitly
authorized separate one-step model job actually succeeds.
"""
import argparse,csv,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S106=ROOT/"reports/stage106_GLE_ERA_2004LST_14HH_backfilled_UTCmid_16NC_20261026T125959Z_bfa2ba7f"
S107=ROOT/"reports/stage107_GLE_real_source_contiguous_cycle_selection_READONLY_20261026T131102Z_c4ad22bd"
STAGE103_NAME="103_GLE_seam_CIME_detached_namelist_preflight.py"
STAGE103_GITBLOB="c67aa9c5c4e358b0c2efba99da46e08d8a8341c5"
COUNTS=tuple(range(2005,2021))
SRC_FIELDS=("PRECTmms","FSDS","ZBOT","TBOT","WIND","QBOT","PSRF","FLDS")
SCIENCE_HOLD="SCIENCE_HOLD_DO_NOT_SUBMIT_OR_RUN"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def gblob(path):
    p=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(p)).encode()+b"\0"+p).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def write(path,record):path.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")

def module():
    script=Path(__file__).resolve().parent/STAGE103_NAME
    if not script.is_file() or gblob(script)!=STAGE103_GITBLOB:
        raise ValueError("Prior proved Stage103 GF-Guy CIME parser script Git blob invalid or missing")
    spec=importlib.util.spec_from_file_location("gle_stage103_proven",
                                                 str(script))
    lib=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lib)
    if not all(hasattr(lib,n) for n in ("preflight","create_isolated_case","original_stream")):
        raise ValueError("Stage103 successful case-clone entrypoints absent")
    return lib,script

def source():
    m106=load(S106/"manifest.json")
    m107=load(S107/"manifest.json")
    if (m106.get("schema")!="BATCH02_STAGE106_GLE_TRUE_DATED_ERA_LST_PREHISTORY_16UTC_MID_NC"
        or m106.get("16_year_new_NC_count")!=16
        or m106.get("2004_LST_ERA_replaced_UTC_first_slots")!=14
        or m106.get("science_DATM_approved") is not False
        or m106.get("Slurm_jobs_submitted") is not False
        or m106.get("model_CIME_clock_runtime_verified") is not False
        or m106.get("source_2020_synthetic_weather_seam_removed") is not True
        or (S106/"INCOMPLETE_DO_NOT_USE").exists()
        or not (S106/"SCIENCE_HOLD_NO_CIME_MODEL_OR_SPINUP").is_file()
        or m107.get("schema")!="STAGE107_GLE_DATM_CYCLE_WINDOW_SOURCE_ROSTER_READONLY"
        or m107.get("Stage106_manifest_sha256")!=sha(S106/"manifest.json")
        or m107.get("candidate_consecutive_year_intervals_10to16")!=28
        or m107.get("science_approved") is not False
        or m107.get("Slurm_jobs_submitted") is not False):
        raise ValueError("Stage106 authentic prehistory or Stage107 original 28 cycle windows changed")
    for root,key in ((S106,"out_sha256"),(S107,"receipt_sha256")):
        for fn,dig in load(root/"manifest.json")[key].items():
            if sha(root/fn)!=dig:
                raise ValueError("Completed Stage106/107 provenance altered "+str(root/fn))
    docs=sorted(load(S106/"16_year_independent_NC_receipts.json"),key=lambda r:r["year"])
    if len(docs)!=16 or {r["year"] for r in docs}!=set(COUNTS):
        raise ValueError("Yearly authentic GLE source selection changed")
    for r in docs:
        if sha(r["new"])!=r["sha256"] or sha(r["source_Stage102"])!=r["source_sha256"]:
            raise ValueError("Verified GLE source dataset altered "+str(r["year"]))
        if r["changed_original_samples"]!=(14 if r["year"]==2005 else 0):
            raise ValueError("Unexpected ERA replacement scope in original Stage106")
    ranks=list(csv.DictReader((S107/"28_real_10to16year_cycle_boundary_options.csv").open()))
    if len(ranks)!=28 or (ranks[0]["first_year"],ranks[0]["last_year"])!=("2009","2019"):
        raise ValueError("Actual Stage107 proposed 2009–2019 leading candidate changed")
    return docs,ranks

def check():
    lib,script=module()
    docs,ranks=source()
    ref,orig_files,coord,surface,seams=lib.preflight()
    if (not (abs(coord[0]-41.3665)<1e-4 and
             abs(((coord[1]+180)%360)-180+106.2399)<1e-4)):
        raise ValueError("Original GLE site reference coords do not match official BIF")
    if surface.get("tower_true_FATES_PFT_approved") is not False:
        raise ValueError("Reference gridded surface is not approved tower ENF PFT")
    # Prior proven Stage103 source-layer CIME pointer will be *replaced
    # only in the NEW clone*, never in that successful old test.
    print("STAGE108 GLE VERIFIED SOURCE | Stage106 16/16 NC, 14 genuine original ERA halfhours at Jan1 2005 UTC, Stage107 28/28 windows",flush=True)
    print("STAGE108 SMOKE DATA PERIOD 2005-2020 | START 2005-01-01 STOP_N 1 nsteps, RESUBMIT 0, full-source UTC midpoint, not 2009-only",flush=True)
    print("STAGE108 FUTURE SPINUP CANDIDATE 2009-2019 | source window 11y; original non-spun-up historical 2005-2020 preserved",flush=True)
    print("STAGE108 WEATHER SCIENCE HOLD | full source periodic edge, 0.75m WS-vs-TA height, tower ENF PFT, actual model read",flush=True)
    return lib,script,docs,ranks,ref,coord,surface

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--prepare",action="store_true")
    mode=p.parse_args()
    if mode.self_test:
        assert len(COUNTS)==16 and COUNTS[0]==2005 and COUNTS[-1]==2020
        assert len(SRC_FIELDS)==8 and "QBOT" in SRC_FIELDS and "ZBOT" in SRC_FIELDS
        print("STAGE108 SELF-TEST PASS | full 16-year Stage106 GLE one-step model reader candidate, no model submission")
        return
    lib,script,docs,ranks,reference,coord,surface=check()
    if mode.check:
        print("STAGE108 CHECK PASS | full16 original real ERA and successful Stage103 CIME recipe; NO WRITES")
        return
    root=ROOT/"reports"/("stage108_GLE_STAGE106_TRUE_ERA_DETACHED_CIME_ONE_STEP_SETUP_ONLY_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    root.mkdir(parents=True,exist_ok=False)
    (root/SCIENCE_HOLD).write_text(
        "STAGE108 GLE ONLY: Case.setup and preview_namelists, not a model run. Do not call case.submit until a future explicit single-timestep science/test decision. Weather periodic edge, wind reference and ENF tower footprint PFT remain unapproved.\n")
    (root/"INCOMPLETE_DO_NOT_USE").write_text("New CIME clone preview not yet validated.\n")
    case=root/"GLE_STAGE108_1TIMESTEP_NOT_SUBMITTED"
    log=root/"detached_GLE_CIME_stage108_case_setup_preview.log"
    try:
        receipt=lib.create_isolated_case(case,Path(surface["mods"]),
             docs,coord,surface,log)
        # Verify exact new 16 annual sources, not the old Stage102 sources.
        stream=(case/"user_nl_datm_streams").read_text()
        expected=lib.original_stream(docs)
        if stream!=expected:
            raise ValueError("Prepared GLE CIME stream does not exactly map all 16 authentic ERA source files")
        if "stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC" in stream:
            raise ValueError("Prepared CIME accidentally reads old artificial 2020 cyc source")
        if stream.count("stage106_GLE_ERA_2004LST_14HH_backfilled_UTCmid_16NC")!=16:
            raise ValueError("Detached CIME stream missing 16 Stage106 genuine ERA source paths")
        if not ("CLM_USRDAT.UNSET:taxmode = cycle" in stream and
                "CLM_USRDAT.UNSET:tintalgo = linear" in stream and
                "QBOT Sa_shum" in stream and "ZBOT Sa_z" in stream):
            raise ValueError("CIME DATM proven original field/time mapping missing")
        conf=(case/"CaseDocs/lnd_in").read_text(errors="replace")
        if Path(surface["surface"]).name not in conf:
            raise ValueError("GLE source surface not selected in CaseDocs")
        receipt.update({"source_Stage106_manifest_SHA256":sha(S106/"manifest.json"),
            "verified_annual_ERA_NC":16,
            "year_first":2005,"year_last":2020,
            "actual_met_reader_model_executed":False,
            "submit_authorized":False,
            "run_length_steps":1,
            "spinuplength_years_authorized":0,
            "stage107_future_spinup_candidate":"2009-2019_UNAPPROVED"})
        write(root/"detached_GLE_one_step_CASE_NOT_SUBMITTED_receipt.json",receipt)
        unactivated=lib.original_stream([r for r in docs if 2009<=r["year"]<=2019])
        unactivated=unactivated.replace("year_first = 2005","year_first = 2009").replace(
             "year_last = 2020","year_last = 2019").replace("year_align = 2005","year_align = 2009")
        (root/"SPINUP_2009_2019_STREAM_CANDIDATE_NOT_APPLIED.txt").write_text(
             "# Planning only; NOT APPLIED to Stage108 one-step candidate.\n"+unactivated)
        metadata={"schema":"STAGE108_GLE_SOURCE106_16YEAR_CIME_ONE_STEP_PARSER_ONLY",
            "stage106_manifest_sha256":sha(S106/"manifest.json"),
            "stage107_manifest_sha256":sha(S107/"manifest.json"),
            "Stage103_proven_Git_blob":STAGE103_GITBLOB,
            "clone_case":str(case),"stage108_short_case_parser_PASS":True,
            "STOP_OPTION":"nsteps","STOP_N":1,"RESUBMIT":0,
            "all_16_new_GLE_ERA_sources_in_CIME_stream":True,
            "actual_model_met_read_verified":False,"actual_model_run_performed":False,
            "Slurm_jobs_submitted":False,"science_FATES_PFT_approved":False,
            "prod_DATM_approved":False,
            "immutable_215_and_16_original_NC_modified":False,
            "receipt_sha256":{q.name:sha(q) for q in root.iterdir()
                 if q.is_file() and q.name!="INCOMPLETE_DO_NOT_USE"}}
        write(root/"manifest.json",metadata)
        (root/"INCOMPLETE_DO_NOT_USE").unlink()
        print("STAGE108 CIME ONE_STEP CASE PREVIEW PASS | 16 Stage106 genuine ERA annual NC, 2005-2020, STOP_N 1, RESUBMIT 0, NO SUBMIT",flush=True)
        print("STAGE108 CASE",case,flush=True)
        print("STAGE108 REPORT",root,flush=True)
        print("STAGE108 SCIENCE HOLD | model not run, no jobs; verify source period edge, tower PFT and ZBOT before long spinup",flush=True)
    except Exception as e:
        write(root/"failure.json",{"kind":type(e).__name__,"error":str(e),"no_submission":True})
        print("STAGE108 PREPARE STOP",type(e).__name__,str(e),flush=True)
        print("STAGE108 REPORT",root,flush=True)
        raise

if __name__=="__main__":
    main()

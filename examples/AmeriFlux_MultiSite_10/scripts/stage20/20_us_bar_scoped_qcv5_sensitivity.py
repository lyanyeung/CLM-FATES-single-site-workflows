#!/usr/bin/env python3
"""STAGE20: Isolated US-Bar ORIGINAL-QCv5 sensitivity for exact three blockers.

Original eight-site QC-v5 is loaded verbatim except for ONE extremely narrow
permission: at US-Bar 2004-01-14 08:00, 08:30, 09:00, accept ERA-computed RH
between -3 and -2% (strictly negative), when TA_F/VPD_F are QC=2 and both
are numerically identical to the downscaled ERA values. This then follows
THE EXISTING QC-v5 1%-RH floor and provenance/manual-review logic.

THIS IS A SENSITIVITY EXPERIMENT, NOT A METEOROLOGICAL VALIDATION OR AN
APPROVED FORCING REPAIR. Both sources share provenance; physical realism
must be evaluated with independent evidence (e.g., verified ERA5-Land).

--check: read/check original script and pinned input files only.
--run: write a NEW US-Bar-only versioned experimental candidate directory.
Never modifies original QCv5 engine, original CSVs, prior nine candidates,
the incomplete Stage18 run, DATM, surfaces, CIME cases or Slurm jobs.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
EXPERIMENTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments")
BATCH = Path(__file__).resolve().parents[2]
SITE="US-Bar"
SOURCE_SHA256="61be3c46b69ee77739019fab499c94dd1fc1f66a77b1c830815e33baf5351a35"
TIMESTAMPS=("2004-01-14 08:00","2004-01-14 08:30","2004-01-14 09:00")
FLOOR_RH_PCT=1.0

# Exact text anchors in the 2026-10-12 original 8-site QCv5 SHA256 script.
ANCHOR_A="        min_rh_pct = 1.0\n        allowed = (\n"
ANCHOR_B="            rh_era.between(-2.0, 100.05) &\n"

# Inject exact-site/time/QC/ERA-provenance guarded exception into the existing
# QC-v5 humidity-reconciliation block, not into its interpolation or gapfill.
INJECT = '''        # US-Bar isolated sensitivity ONLY: known 3 QC2 winter artefacts.
        scoped_usbar = (
            (site == "US-Bar")
            & d.time.isin(pd.to_datetime([
                "2004-01-14 08:00",
                "2004-01-14 08:30",
                "2004-01-14 09:00",
            ]))
            & d["TA_F_QC"].eq(2)
            & d["VPD_F_QC"].eq(2)
            & (d["TA_F"] - d["TA_ERA"]).abs().le(1.0e-6)
            & (d["VPD_F"] - d["VPD_ERA"]).abs().le(1.0e-6)
            & rh_era.between(-3.0, -2.0, inclusive="left")
        )
        if int(scoped_usbar.sum()) != 3:
            raise RuntimeError(
                "US-Bar scoped floor gate did not identify exactly 3 pinned QC2 ERA records; "
                "source changed, do not apply patch"
            )
        min_rh_pct = 1.0
        allowed = (
'''


def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(2**20),b""):
            h.update(block)
    return h.hexdigest()


def pinned_sources(root):
    with (BATCH/"sites.tsv").open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=10 or len({r["site"] for r in rows})!=10:
        raise RuntimeError("Expected ten unique pinned AmeriFlux batch release sites")
    manifest=next(r for r in rows if r["site"]==SITE)
    raw=root/SITE/"forcing"/"raw"/manifest["package"]
    src={}
    for key in ("FLUXMET_HH","ERA5_HH"):
        found=sorted(p for p in raw.glob("*.csv") if key in p.name.upper())
        if len(found)!=1:
            raise RuntimeError("Expected 1 pinned %s under %s, got %d" %
                               (key,raw,len(found)))
        src[key]=found[0]
    return manifest,src


def patch_text(content):
    if content.count(ANCHOR_A)!=1 or content.count(ANCHOR_B)!=1:
        raise RuntimeError("Original engine code anchors changed; abort site-specific sensitivity")
    result=content.replace(ANCHOR_A,INJECT,1)
    result=result.replace(ANCHOR_B,
        '            (rh_era.between(-2.0, 100.05) | scoped_usbar) &\n',1)
    if result==content or result.count("scoped_usbar")!=3:
        raise RuntimeError("Patch application did not match expected constrained scope")
    compile(result,"<scoped_USBar_original_qcv5>", "exec")
    return result


def load_module(path):
    spec=importlib.util.spec_from_file_location("usbar_scoped_original_qcv5",path)
    if not spec or not spec.loader:
        raise RuntimeError("Could not import scoped copy of original QCv5")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_candidate(candidate_dir, stage20_root):
    forcfile=(candidate_dir/SITE/"forcing"/"processed_v5"/
              "US-Bar_CLM_forcing_2004_2023.csv")
    qcdir=candidate_dir/SITE/"forcing"/"qc_v5"
    if not forcfile.is_file():
        raise RuntimeError("US-Bar QC-v5 forcing CSV absent")
    force=pd.read_csv(forcfile)
    required={"time","QBOT","TBOT","PSRF","TA_USE","VPD_USE"}
    if not required.issubset(force.columns):
        raise RuntimeError("US-Bar candidate forcing missing columns "+str(required-set(force.columns)))
    if len(force)!=20*17520:
        raise RuntimeError("US-Bar candidate length not NO_LEAP 20-year")
    for field in ("QBOT","TBOT","PSRF","TA_USE","VPD_USE"):
        if force[field].isna().any():
            raise RuntimeError("US-Bar candidate has NaNs: "+field)
    if not force["QBOT"].between(0,0.08).all():
        raise RuntimeError("US-Bar candidate invalid QBOT")
    manual=qcdir/"US-Bar_manual_review.csv"
    events=qcdir/"US-Bar_replacement_events.csv"
    status=qcdir/"US-Bar_status.json"
    if not all(p.is_file() for p in (manual,events,status)):
        raise RuntimeError("Missing source QC provenance/review/status records")
    review=pd.read_csv(manual)
    replace=pd.read_csv(events)
    target_time=pd.to_datetime(list(TIMESTAMPS)).strftime("%Y-%m-%d %H:%M:%S")
    affected=force.loc[force["time"].isin(target_time)]
    if len(affected)!=3:
        raise RuntimeError("Three target timestamps not found uniquely in candidate")
    es=6.112*(2.718281828459045**(
        17.67*affected["TA_USE"]/(affected["TA_USE"]+243.5)))
    rh=100*(es-affected["VPD_USE"])/es
    if not ((rh-1.0).abs()<1e-5).all():
        raise RuntimeError("Scoped three times not at precise candidate RH=1%")
    for stamp in target_time:
        review_row=review.loc[
            (review["time"]==pd.Timestamp(stamp).isoformat()) &
            (review["reason"]=="ERA_RH_below_1pct_adjusted_review_needed")
        ]
        if len(review_row)!=1:
            raise RuntimeError("Missing manual low-RH provenance for "+stamp)
        rep=replace.loc[
            (replace["time"]==pd.Timestamp(stamp).isoformat()) &
            (replace["variable"]=="VPD_F")
        ]
        if len(rep)!=1:
            raise RuntimeError("Missing replacement event provenance for "+stamp)
    return len(force),len(replace),len(review)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    ap.add_argument("--base-script",type=Path,required=True)
    ap.add_argument("--sites-root",type=Path,default=ROOT)
    ap.add_argument("--output-root",type=Path,
                    help="Required for --run: absent new directory inside CLM_FATES/experiments")
    args=ap.parse_args()
    base=args.base_script.expanduser().resolve()
    raw_root=args.sites_root.expanduser().resolve()
    if not base.is_file():
        raise RuntimeError("Original QCv5 base script missing: "+str(base))
    digest=sha256(base)
    if digest!=SOURCE_SHA256:
        raise RuntimeError("Original QCv5 method SHA256 changed: "+digest)
    manifest,sources=pinned_sources(raw_root)
    if (manifest["first_year"],manifest["last_year"])!=("2004","2023"):
        raise RuntimeError("US-Bar release window changed")
    patch=patch_text(base.read_text(encoding="utf-8"))
    print("STAGE20 CHECK: ORIGINAL SHA256",digest)
    print("PINNED FLUXMET:",sources["FLUXMET_HH"])
    print("PINNED ERA5:",sources["ERA5_HH"])
    print("TARGET: US-Bar",", ".join(TIMESTAMPS))
    print("SCOPED EXPERIMENT: original QCv5 plus 3 verified QC2 RH[-3,-2)% allowances")
    if args.check:
        print("CHECK ONLY: no output or source files written")
        return
    if args.output_root is None:
        ap.error("--output-root is required for --run")
    output=args.output_root.expanduser().resolve()
    experiment_root=EXPERIMENTS.resolve()
    if output.exists() or output==experiment_root or experiment_root not in output.parents:
        raise RuntimeError("Output must be a new absent child of "+str(experiment_root))
    output.mkdir(parents=True,exist_ok=False)
    marker=output/"INCOMPLETE_NOT_APPROVED"
    marker.write_text("Source/site scoped sensitivity. Never eligible for DATM by itself.\n")
    engine_file=output/"scoped_usbar_engine_copy.py"
    engine_file.write_text(patch,encoding="utf-8")
    (output/"method_manifest.json").write_text(json.dumps({
        "method":"Original 8-site QCv5 with exact 3-timestep US-Bar RH sensitivity",
        "original_method_sha256":digest,
        "derived_engine_sha256":sha256(engine_file),
        "target_site":SITE,
        "target_times":TIMESTAMPS,
        "input_release":manifest,
        "FLUXMET_HH":str(sources["FLUXMET_HH"]),
        "ERA5_HH":str(sources["ERA5_HH"]),
        "science_status":"NOT_APPROVED; INDEPENDENT_EVIDENCE_MISSING",
        "created_utc":datetime.now(timezone.utc).isoformat(),
    },indent=2)+"\n")
    original=load_module(engine_file)
    original.SITE_YEARS={SITE:(2004,2023)}
    def exact_get_one(root,pattern):
        if root.resolve()!= (raw_root/SITE/"forcing"/"raw").resolve():
            raise RuntimeError("Unexpected raw source selection:"+str(root))
        mapping={
            "*FLUXMET_HH*.csv":sources["FLUXMET_HH"],
            "*ERA5_HH*.csv":sources["ERA5_HH"],
        }
        if pattern not in mapping:
            raise RuntimeError("Unexpected QCv5 source selection: "+pattern)
        return mapping[pattern]
    original.get_one=exact_get_one
    print("STAGE20 RUN: isolated US-Bar QCv5 scoped sensitivity",flush=True)
    status=original.parse_site(SITE,raw_root,output)
    length,changes,reviews=verify_candidate(output,output)
    print("STAGE20 SUMMARY: US-Bar="+status["status"],
          "rows="+str(length),"changes="+str(changes),
          "manual_reviews="+str(reviews),flush=True)
    print("CANDIDATE OUTPUT:",output,flush=True)
    # No signal of scientific approval: retain a distinct marker on success.
    marker.unlink()
    (output/"COMPLETE_SENSITIVITY_NOT_SCIENCE_APPROVED").write_text(
        "US-Bar original QCv5 numerically passed scoped three-time sensitivity.\n"
        "Not validated vs independent observations/ERA5-Land. Do not submit DATM.\n")
    print("SUCCESSFUL NUMERIC SENSITIVITY; NOT APPROVED FOR DATM OR SPINUP.")


if __name__=="__main__":
    main()

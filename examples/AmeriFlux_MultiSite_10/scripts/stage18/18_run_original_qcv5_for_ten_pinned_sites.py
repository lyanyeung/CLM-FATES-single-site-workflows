#!/usr/bin/env python3
"""Run the ACTUAL eight-site QC-v5 algorithm on ten pinned AmeriFlux releases.

Method precedence follows FLUXNET_MultiSite_13's Stage03 driver: dynamically
import examples/FLUXNET_MultiSite_8/scripts/03_prepare_eight_site_forcing_v5.py,
replace ONLY its site year windows and exact input-file selection. Physics,
short-gap interpolation, long-gap ERA fallback, humidity reconciliation and
event ledgers are unchanged. Do NOT interpret this as independent verification.

--check reads source filenames/headers only, writes NOTHING.
--run creates a NEW isolated experiment output root, never within MY_EC_SITE.
Refuses output-root existing; partial site failures retain an INCOMPLETE marker.
Data/site owners must examine all QC=0 changes and manual-review entries
before DATM creation. No native ERA5-Land downloaded or used by QC-v5.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_EXPERIMENTS = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments")
MET = ("TA","VPD","PA","SW_IN","LW_IN","WS","P")


def load_manifest():
    with (HERE/"sites.tsv").open("r", newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=10 or len({r["site"] for r in rows})!=10:
        raise RuntimeError("Expected ten unique AmeriFlux pinned-release stations")
    expected={"site","package","first_year","last_year"}
    if set(rows[0])!=expected:
        raise RuntimeError("Manifest columns must be "+str(expected))
    for r in rows:
        first,last=int(r["first_year"]),int(r["last_year"])
        if first<1980 or last>2030 or first>last:
            raise RuntimeError("Invalid year window for "+r["site"])
    return rows


def exact_csv(folder, token):
    choices=sorted(p for p in folder.glob("*.csv") if token in p.name.upper())
    if len(choices)!=1:
        raise RuntimeError("Expected ONE %s inside %s, got %d"%
                           (token,folder,len(choices)))
    return choices[0]


def head(path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return set(next(csv.reader(f)))


def pinned_release(root, r):
    folder=root/r["site"]/"forcing"/"raw"/r["package"]
    if not folder.is_dir():
        raise RuntimeError("Missing pinned raw release "+str(folder))
    met=exact_csv(folder,"FLUXMET_HH")
    era=exact_csv(folder,"ERA5_HH")
    h=head(met)
    e=head(era)
    needed={"TIMESTAMP_START"}|{v+"_F" for v in MET}
    if not needed.issubset(h):
        raise RuntimeError("FLUXMET missing columns: "+repr(sorted(needed-h)))
    # The original v5 will need _ERA values from either the FLUXMET
    # embedded columns or the standalone companion. Check all seven.
    for v in MET:
        c=v+"_ERA"
        if c not in h and c not in e:
            raise RuntimeError("Missing %s in both original FLUXMET and ERA5"%c)
    if "TIMESTAMP_START" not in e:
        raise RuntimeError("ERA5_HH companion has no TIMESTAMP_START")
    return {"site":r["site"],"release":r["package"],
            "start":int(r["first_year"]),"end":int(r["last_year"]),
            "met":str(met),"era":str(era)}


def load_original_v5(path):
    spec=importlib.util.spec_from_file_location("original_eight_site_qcv5",path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to import original eight-site QC v5: "+str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module,"parse_site") or not hasattr(module,"get_one"):
        raise RuntimeError("Original v5 code missing parse_site/get_one")
    # Stop if original v5 interface or interpolation settings materially
    # differ from the validated historical script.
    expected={"TA_F":4,"VPD_F":4,"PA_F":4,"SW_IN_F":2,
              "LW_IN_F":4,"WS_F":4,"P_F":0}
    if getattr(module,"INTERPOLATE",None)!=expected:
        raise RuntimeError("Original QC v5 short interpolation policy changed")
    return module


def hash_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(2**20),b""):
            h.update(chunk)
    return h.hexdigest()


def output_summary_file(outcomes, target):
    with target.open("w", newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=[
            "site","release","first_year","last_year","status",
            "changes","manual_review_records","error"
        ])
        w.writeheader()
        w.writerows(outcomes)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--run",action="store_true")
    ap.add_argument("--sites-root",type=Path,default=DEFAULT_ROOT)
    ap.add_argument("--base-script",type=Path,required=True,
                    help="Directly downloaded original QC-v5 8-site Python script")
    ap.add_argument("--output-root",type=Path,
                    help="Required for --run; MUST be a new absent experiment folder")
    ap.add_argument("--sites",nargs="+",help="Run a subset, when debugging")
    args=ap.parse_args()
    rows=load_manifest()
    choices={r["site"] for r in rows}
    if args.sites:
        unknown=set(args.sites)-choices
        if unknown: ap.error("Unexpected site codes: "+repr(sorted(unknown)))
        rows=[r for r in rows if r["site"] in args.sites]
    root=args.sites_root.expanduser().resolve()
    base=args.base_script.expanduser().resolve()
    if not base.is_file():
        raise RuntimeError("Original v5 script not downloaded: "+str(base))
    original=load_original_v5(base)
    source_hash=hash_file(base)
    checkouts=[]
    failures=[]
    print("METHOD: unmodified original FLUXNET_MultiSite_8 QC v5 engine")
    print("ORIGINAL SCRIPT:",base)
    print("ORIGINAL SCRIPT SHA256:",source_hash)
    for r in rows:
        try:
            info=pinned_release(root,r)
            checkouts.append(info)
            print("CHECK OK %-7s %s–%s" %
                  (info["site"],info["start"],info["end"]),flush=True)
        except Exception as exc:
            failures.append((r["site"],str(exc)))
            print("CHECK FAIL",r["site"],str(exc),flush=True)
    if failures:
        raise RuntimeError("Preflight FAILED; no candidate writes: "+repr(failures))
    print("PREFLIGHT OK %d/%d; method=ORIGINAL_QCV5" %
          (len(checkouts),len(rows)))
    if args.check:
        print("CHECK ONLY: no outputs; no repair has run.")
        return 0
    if args.output_root is None:
        ap.error("--output-root NEW_ABSENT_PATH is required for --run")
    out=args.output_root.expanduser().resolve()
    if (out==root or root in out.parents or
        out==DEFAULT_EXPERIMENTS or
        out==Path.home() or
        (out.exists())):
        raise RuntimeError("Refusing existing/unsafe output destination: "+str(out))
    # Only permit a new nested directory within scratch experiments so
    # local Home or site folders never receive production trial writes.
    experiment_root=DEFAULT_EXPERIMENTS.resolve()
    if experiment_root not in out.parents:
        raise RuntimeError("Output MUST be a new dir under "+str(experiment_root))
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "This run may have failed partway; inspect final summary first.\n",
        encoding="utf-8")
    manifest={
        "algorithm":"ORIGINAL_FLUXNET_MultiSite_8_QC_V5",
        "method_script_path":str(base),
        "method_script_sha256":source_hash,
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source_policy":"ten pinned AmeriFlux releases; no other raw packages",
        "era_source":"FLUXNET site-downscaled ERA5_HH, not ERA5-Land",
        "science_status":"UNAPPROVED_EXPLORATORY_CANDIDATES",
        "sites":checkouts,
    }
    (out/"exact_input_manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    fixed={x["site"]:x for x in checkouts}
    def choose_exact(raw_folder,pattern):
        site=raw_folder.parent.parent.name
        if site not in fixed:
            raise RuntimeError("Unrecognized source site "+site)
        if pattern=="*FLUXMET_HH*.csv":return Path(fixed[site]["met"])
        if pattern=="*ERA5_HH*.csv":return Path(fixed[site]["era"])
        raise RuntimeError("Unrecognized original QC v5 selector "+repr(pattern))
    original.get_one=choose_exact
    original.SITE_YEARS={x["site"]:(x["start"],x["end"]) for x in checkouts}
    outcomes=[]
    for r in rows:
        name=r["site"]
        print("\n===== APPLY HISTORICAL QC-v5 CANDIDATE =====",name,flush=True)
        try:
            s=original.parse_site(name,root,out)
            outcomes.append(dict(site=name,release=r["package"],
                                 first_year=r["first_year"],last_year=r["last_year"],
                                 status=s["status"],changes=s["changes"],
                                 manual_review_records=s["manual_review_records"],
                                 error=""))
            print("CANDIDATE WRITTEN",name,
                  "changes",s["changes"],"review",s["manual_review_records"],flush=True)
        except Exception as err:
            outcomes.append(dict(site=name,release=r["package"],
                                 first_year=r["first_year"],last_year=r["last_year"],
                                 status="FAIL",changes="",manual_review_records="",
                                 error=repr(err)))
            print("SITE BLOCKED:",name,repr(err),flush=True)
    output_summary_file(outcomes,out/"qc_v5_adaptation_run_summary.csv")
    failures=[x["site"] for x in outcomes if x["status"]=="FAIL"]
    print("\nSTAGE18 SUMMARY: sites=%d, candidate_written=%d, FAILED=%d"%
          (len(rows),len(rows)-len(failures),len(failures)))
    for s in outcomes:
        print(" %-7s %-7s changes=%s reviews=%s error=%s"%
              (s["site"],s["status"],s["changes"],
               s["manual_review_records"],s["error"]))
    print("CANDIDATE OUTPUT:",out)
    if failures:
        print("BLOCKED SITES:",", ".join(failures))
        print("INCOMPLETE marker kept. No failed output eligible for DATM.")
        return 2
    (out/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").unlink()
    (out/"COMPLETE_NUMERIC_CANDIDATES_NOT_SCIENCE_APPROVED").write_text(
        "All sites emitted original-v5 candidates; review all changes, especially QC0.\n"
        "Do not use in DATM or spin-up before scientific QC / measurement heights /\n"
        "PFT and forcing gates.\n",encoding="utf-8")
    print("All site candidates written; still NOT approved for DATM/spin-up.")
    return 0


if __name__=="__main__":
    sys.exit(main())

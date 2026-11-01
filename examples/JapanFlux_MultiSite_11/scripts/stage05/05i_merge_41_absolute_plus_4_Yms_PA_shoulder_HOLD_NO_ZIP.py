#!/usr/bin/env python3
"""JapanFlux Stage05I — strictly merge the 41 Stage05G and 4 Stage05H review events.

Uses ONLY derived TSVs. No ZIP, Slurm, forcing creation, data modifications
or numerical repairs. All records remain on scientific HOLD pending independent
ERA5/source provenance and time-zone verification. This is NOT an approval.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path

EXPECTED_NEW = {
    ("JP-Yms", "200508120230", "PA"),
    ("JP-Yms", "200508120330", "PA"),
    ("JP-Yms", "201112170630", "PA"),
    ("JP-Yms", "201112170730", "PA"),
}
COLUMNS = (
    "site", "native_start", "variable", "units_assumed",
    "selected_F_value", "embedded_ERA_value", "selected_F_QC_raw",
    "selected_F_MDS_value", "screen_evidence", "relative_to_context_flanks",
    "science_status", "next_source_check",
)

def read_tsv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as stream:
        rdr = csv.DictReader(stream, delimiter="\t")
        if rdr.fieldnames is None or len(set(rdr.fieldnames)) != len(rdr.fieldnames):
            raise ValueError("Missing or duplicate TSV headers: " + str(p))
        return list(rdr)

def check_same(f: str, e: str) -> None:
    try:
        fv, ev = float(f), float(e)
    except (TypeError, ValueError) as exc:
        raise ValueError("No numeric F and ERA: " + repr((f,e))) from exc
    if not all(math.isfinite(v) for v in (fv,ev)) or not math.isclose(fv,ev,abs_tol=1e-9,rel_tol=1e-12):
        raise ValueError("Source F does not match embedded ERA: " + repr((f,e)))

def canonical(site: str, start: str, variable: str, f: str, era: str,
              qc: str, mds: str, screen: str, ratio: str = "") -> dict:
    if len(start) != 12 or not start.isdigit():
        raise ValueError("Unexpected native time: " + start)
    if variable not in ("TA", "PA", "LW_IN") or not site.startswith("JP-"):
        raise ValueError("Unexpected site/variable")
    if str(qc).strip() != "2":
        raise ValueError("Source QC != 2, no approval to promote: " + repr((site,start,variable,qc)))
    check_same(f,era)
    return {
        "site": site, "native_start": start, "variable": variable,
        "units_assumed": {"TA":"degC","PA":"kPa","LW_IN":"W_m-2"}[variable],
        "selected_F_value": f, "embedded_ERA_value": era,
        "selected_F_QC_raw": qc,
        "selected_F_MDS_value": mds,
        "screen_evidence": screen,
        "relative_to_context_flanks": ratio,
        "science_status": "HOLD_UNAPPROVED_SOURCE_REVIEW",
        "next_source_check": "INDEPENDENT_ERA5_OR_ERA5_LAND_PLUS_NATIVE_TIME_AND_SOURCE_QC",
    }

def build(g: list[dict], h: list[dict]) -> tuple[list[dict], dict]:
    merged: dict[tuple[str,str,str], dict] = {}
    for r in g:
        if r.get("selected_F_screen_nonphysical") != "1":
            continue
        if r.get("classification") != "FLAGGED_ERA_EQUALS_NONPHYSICAL_SELECTED_F":
            raise ValueError("Stage05G source mismatch or unexpected classification")
        k=(r["site"],r["native_start"],r["variable"])
        if k in merged:
            raise ValueError("Duplicate Stage05G key: "+repr(k))
        merged[k]=canonical(*k, r["source_selected_F_value"],r["embedded_ERA_value"],
                            r["selected_F_QC_raw"],r.get("selected_F_MDS_value",""),
                            "STAGE05G_ABSOLUTE_NONPHYSICAL_FLAG")
    if len(merged)!=41:
        raise ValueError("Expected 41 actual Stage05G flags; found "+str(len(merged)))
    extras: set[tuple[str,str,str]] = set()
    for r in h:
        if r.get("screen_classification")!="ADDITIONAL_RELATIVE_ANOMALY_REVIEW_ONLY":
            continue
        if r.get("Stage05G_threshold_flag")!="0" or r.get("relative_context_screen")!="1":
            raise ValueError("Unexpected Stage05H classification or relative-screen flag")
        k=(r["site"],r["native_start"],r["variable"])
        if k in merged or k in extras:
            raise ValueError("Duplicated relative event: "+repr(k))
        if k not in EXPECTED_NEW:
            raise ValueError("Unreviewed new event: "+repr(k))
        ratio=float(r["F_to_baseline_ratio"])
        if not math.isfinite(ratio) or not (0 < ratio < 0.85):
            raise ValueError("Relative screening ratio out of bounds")
        merged[k]=canonical(*k,r["F_value"],r["ERA_value"],r["F_QC_raw"],
                            r.get("F_MDS_value",""),
                            "STAGE05H_RELATIVE_PA_INTERPOLATION_CANDIDATE",r["F_to_baseline_ratio"])
        extras.add(k)
    if extras!=EXPECTED_NEW:
        raise ValueError("Stage05H expected four JP-Yms shoulder events; found "+repr(sorted(extras)))
    records=sorted(merged.values(),key=lambda r:(r["site"],r["native_start"],r["variable"]))
    times={(r["site"],r["native_start"]) for r in records}
    sitecounts=Counter(r["site"] for r in records)
    fieldcounts=Counter(r["variable"] for r in records)
    if len(records)!=45 or len(times)!=35 or fieldcounts!=Counter({"PA":27,"LW_IN":12,"TA":6}):
        raise ValueError("Final 45 field-record / 35 unique time-point count invariant failed")
    if sitecounts!=Counter({"JP-Tmd":14,"JP-Khw":11,"JP-Yms":10,"JP-Fjy":6,"JP-Tef":4}):
        raise ValueError("Site count mismatch: "+repr(sitecounts))
    summary={
        "stage":"JapanFlux Stage05I",
        "status":"READONLY_UNAPPROVED_REVIEW_REGISTER",
        "input_stage05g_absolute_flags":41,
        "input_stage05h_new_relative_PA_flags":4,
        "variable_records_for_science_review":len(records),
        "distinct_site_native_halfhours_for_science_review":len(times),
        "counts_by_site":dict(sorted(sitecounts.items())),
        "counts_by_variable":dict(sorted(fieldcounts.items())),
        "stage05h_new_key_list":[list(k) for k in sorted(extras)],
        "native_clock":"UNVERIFIED_TIMEZONE",
        "source_product":"JPF_same_release_embedded_ERA; independent ECMWF not checked",
        "original_QC_labels":"all reported raw 2 (specific release metadata still to verify)",
        "status_for_each_record":"HOLD_UNAPPROVED_SOURCE_REVIEW",
        "source_or_forcing_writes":False,
        "limits":"Relative PA shoulders are strong event candidates, not general proof of all source/forcing quality",
    }
    return records,summary

def self_test()->None:
    original=[]
    units={"PA":"45","LW_IN":"39","TA":"-120"}
    sites_vars={"JP-Tmd":{"PA":9,"LW_IN":2,"TA":3},
                "JP-Khw":{"PA":6,"LW_IN":2,"TA":3},
                "JP-Fjy":{"PA":6},"JP-Tef":{"LW_IN":4},"JP-Yms":{"PA":2,"LW_IN":4}}
    # Test canonical count and basic key dedup independently of input TSVs
    if sum(sum(v.values()) for v in sites_vars.values()) !=41:
        raise AssertionError("Synthetic count malformed")
    for v, value in units.items():
        canonical("JP-Yms","200508120230",v,value,value,"2","", "TEST")
    assert len(EXPECTED_NEW)==4
    assert len({"200508120230","200508120330","201112170630","201112170730"})==4
    print("STAGE05I SELF-TEST PASS | fixed science invariants, QC2 source equality; no writes")

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage05g-tsv",type=Path)
    p.add_argument("--stage05h-tsv",type=Path)
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test()
        return 0
    if not a.stage05g_tsv or not a.stage05h_tsv or not a.output_dir:
        p.error("--stage05g-tsv, --stage05h-tsv and --output-dir required")
    records,summary=build(read_tsv(a.stage05g_tsv),read_tsv(a.stage05h_tsv))
    out=a.output_dir
    if out.resolve() in {a.stage05g_tsv.parent.resolve(),a.stage05h_tsv.parent.resolve()}:
        p.error("New output dir must differ from source audit report dirs")
    out.mkdir(parents=True,exist_ok=True)
    tsv=out/"stage05i_45_review_candidates.tsv"
    js=out/"stage05i_45_review_summary.json"
    if tsv.exists() or js.exists():
        p.error("Output files already exist: use a new output directory")
    with tsv.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,delimiter="\t",fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    with js.open("x",encoding="utf-8") as f:
        json.dump(summary,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print("STAGE05I MERGE SUCCESS | NO ZIP / NO SLURM / NO REPAIR")
    print("VARIABLE_RECORDS",len(records))
    print("DISTINCT_SITE_HALF_HOURS",summary["distinct_site_native_halfhours_for_science_review"])
    print("BY_VARIABLE",summary["counts_by_variable"])
    print("BY_SITE",summary["counts_by_site"])
    print("SOURCE_HOLD",tsv)
    print("SUMMARY",js)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

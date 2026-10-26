#!/usr/bin/env python3
"""Build/check the 50-site evidence inventory using only Python's standard library.

No network, model, surface, forcing or scheduler access. Run --build to regenerate
the documentation tables; --check validates the sources and generated files.
"""
import argparse
import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "20261026"
SOURCE_COMMIT = "5b21921cad1d0b0f7c89edb3c1cc5c62d5aa4358"
MODEL_URL = "https://doi.org/10.1029/2021JG006400"
# Source-native ORCHIDEE names, NOT FATES slots or newly measured fractions.
MODEL_FCOVER = {
    "US-Aud": ({"BS": 30, "C4G": 70}, "2004-2009"),
    "US-Mpj": ({"BS": 20, "TeNE": 60, "C4G": 20}, "2008-2014"),
    "US-Seg": ({"BS": 40, "C4G": 60}, "2007-2014"),
    "US-Ses": ({"BS": 20, "TeBE": 55, "C4G": 25}, "2007-2014"),
    "US-SRG": ({"BS": 45, "TeBD": 11, "C4G": 44}, "2009-2014"),
    "US-SRM": ({"BS": 50, "TeBD": 35, "C4G": 15}, "2004-2014"),
    "US-Vcm": ({"TeNE": 100}, "2007-2012; prefire"),
    "US-Vcp": ({"TeNE": 100}, "2007-2014"),
    "US-Whs": ({"BS": 57, "TeBE": 40, "C4G": 3}, "2008-2014"),
    "US-Wjs": ({"TeNE": 15, "C4G": 85}, "2008-2014"),
    "US-Wkg": ({"BS": 60, "TeBE": 3, "C4G": 37}, "2004-2013"),
}


def csv_text(rows, columns):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def cell(value):
    return str(value).replace("|", "&#124;").replace("\n", " ").strip()


def source_links(value):
    urls = [x.strip() for x in value.split(";") if x.strip()]
    return ", ".join(f"[source {n}]({url})" for n, url in enumerate(urls, 1))


def read_inputs():
    with (ROOT / "metadata/sites_50_manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        manifest = list(csv.DictReader(f))
    assert len(manifest) == 50, "Expected exactly 50 release-manifest entries"
    assert len({x["site"] for x in manifest}) == 50, "Duplicate site in release manifest"
    assert Counter(x["batch"] for x in manifest) == {f"Batch{i:02}": 10 for i in range(1, 6)}
    records = []
    for i in range(1, 6):
        data = json.loads((ROOT / f"metadata/source_records_batch{i:02}.json").read_text(encoding="utf-8-sig"))
        assert len(data) == 10, f"Batch{i:02} source-record count"
        expected = {x["site"] for x in manifest if x["batch"] == f"Batch{i:02}"}
        assert {x["site"] for x in data} == expected, f"Batch{i:02} membership mismatch"
        records.extend(data)
    assert len({r["site"] for r in records}) == 50, "Duplicate research record"
    bysite = {r["site"]: r for r in records}
    required = ("site_name", "igbp", "vegetation", "observed_composition", "observed_pft_summary",
                "evidence_level", "denominator", "observation_period", "spatial_scope", "bare_ground",
                "source_title", "source_url", "source_locator", "verification_status", "candidate_pft",
                "candidate_basis", "uncertainties", "next_evidence", "numeric_percent_evidence")
    joined = []
    for item in manifest:
        r = dict(bysite[item["site"]])
        for key in required:
            assert key in r and str(r[key]).strip(), f"{r['site']}: missing {key}"
        assert isinstance(r["numeric_percent_evidence"], bool)
        assert all(u.strip().startswith("https://") for u in r["source_url"].split(";")), r["site"]
        # LAI/density alone must never inflate the percentage-evidence count.
        if r["evidence_level"] in {"NUMERIC_LAI_NO_PERCENT_VECTOR",
                                  "NUMERIC_DENSITY_WITH_QUALITATIVE_GROUND_COVER",
                                  "QUALITATIVE_COMPOSITION_WITH_NUMERIC_TOTAL_LAI"}:
            assert r["numeric_percent_evidence"] is False, r["site"]
        groups = r.get("functional_group_percent", {})
        for value in groups.values():
            assert isinstance(value, (float, int)) and math.isfinite(value) and 0 <= value <= 100
        # Source percentages can be rounded, partial or overlapping: no forced sum-to-100.
        r.update(item)
        model, period = MODEL_FCOVER.get(r["site"], ({}, ""))
        if model:
            assert abs(sum(model.values()) - 100) < 1e-9
        r.update(
            inventory_as_of="2026-10-26",
            source_repository_commit=SOURCE_COMMIT,
            official_site_url=f"https://ameriflux.lbl.gov/sites/siteinfo/{r['site']}",
            functional_group_percent_json=json.dumps(groups, sort_keys=True),
            functional_group_percent_basis=r.get("functional_group_percent_basis", "No machine-readable scalar group vector established; see original evidence."),
            published_model_fcover_json=json.dumps(model, sort_keys=True) if model else "",
            published_model_period=period,
            published_model_source_url=MODEL_URL if model else "",
            published_model_meaning="ORCHIDEE Table1 site-based prescribed fCover; not new observations or FATES PFT indices" if model else "",
            fates_final_vegc_percent="",
            fates_output_status="NOT_FOUND_IN_REVIEWED_GITHUB_AMERIFLUX_RECORDS",
            actual_fates_paramfile_verified="NO",
            area_fraction_status="NOT_ESTABLISHED_AS_COMPLETE_TOWER_AREA_VECTOR",
            case_or_surface_modified="NO",
            prior_operator_decision=r.get("prior_operator_decision", "NO_SPECIFIC_PERCENT_APPROVAL_RECORDED"),
        )
        joined.append(r)
    return joined


def outputs(rows):
    prefix = ["site", "batch", "package", "first_year", "last_year", "site_manifest_path"]
    evidence_cols = ["site_name", "igbp", "vegetation", "observed_composition", "observed_pft_summary",
                     "numeric_percent_evidence", "evidence_level", "denominator", "observation_period", "spatial_scope",
                     "bare_ground", "functional_group_percent_json", "functional_group_percent_basis", "source_title",
                     "source_url", "source_locator", "verification_status", "candidate_pft", "candidate_basis",
                     "uncertainties", "next_evidence", "official_site_url"]
    master_cols = prefix + evidence_cols + [
        "published_model_fcover_json", "published_model_period", "published_model_source_url", "published_model_meaning",
        "prior_operator_decision", "fates_final_vegc_percent", "fates_output_status", "actual_fates_paramfile_verified",
        "area_fraction_status", "case_or_surface_modified", "inventory_as_of", "source_repository_commit"]
    result = {
        f"MASTER_50_SITE_OBSERVED_VS_FATES_PFT_{DATE}.csv": csv_text(rows, master_cols),
        "50_site_PFT_evidence.csv": csv_text(rows, prefix + evidence_cols),
        f"FINAL_50_SITE_PFT_CANDIDATES_{DATE}.csv": csv_text(rows, [
            "site", "batch", "igbp", "candidate_pft", "candidate_basis", "functional_group_percent_json",
            "functional_group_percent_basis", "published_model_fcover_json", "published_model_period",
            "published_model_source_url", "prior_operator_decision", "area_fraction_status",
            "actual_fates_paramfile_verified", "case_or_surface_modified", "uncertainties", "source_url"]),
        "50_site_further_research_leads.csv": csv_text(rows, [
            "site", "batch", "numeric_percent_evidence", "evidence_level", "next_evidence", "uncertainties", "source_url"]),
    }
    counts = {b: sum(r["numeric_percent_evidence"] for r in rows if r["batch"] == b)
              for b in sorted({r["batch"] for r in rows})}
    n = sum(counts.values())
    report = ["# AmeriFlux 50-site observed vegetation and PFT percentage evidence", "",
              "**Evidence snapshot: 26 October 2026.** Membership is the five original 10-site release manifests.", "",
              f"**{n}/50 sites have at least one numerical vegetation-composition or cover lead; {50-n}/50 have only qualitative composition, LAI/density, or model-assumption evidence in the reviewed sources.** Numerical leads include partial, local, historical and conflicting records; they are not complete prescribed PFT area vectors.", "",
              "| Batch | Stations | Numerical composition/cover leads |",
              "| --- | ---: | ---: |"]
    report += [f"| {b} | 10 | {c} |" for b, c in counts.items()]
    report += ["", "A numeric percentage flag counts composition/cover evidence, including explicitly scoped historical transects. It excludes tree density and LAI alone. All scalar group aggregations retain the source denominator. No normalization fills missing components.", "",
               "The separate `published_model_fcover_json` column records 11 relevant sites from [Mahmud et al. (2021), Table 1](https://doi.org/10.1029/2021JG006400). Those are site-based ORCHIDEE configurations, not measured FATES area fractions. Source-native TeBE may stand for a shrub ecosystem in that model; it is not permission to map shrubs to FATES trees.", "",
               "No end-spin-up FATES PFT vector was found in the reviewed AmeriFlux GitHub records at the pinned repository snapshot. Model-output cells stay blank. This is a GitHub evidence audit, not a live IRIDIS status query.", "",
               "## Reading the functional groups", "",
               "ENF/NE = evergreen needleleaf; DBF/BD = deciduous broadleaf; DNF = deciduous needleleaf; EBF = evergreen broadleaf. Grass/herbaceous and shrub functional mappings require species traits and the actual parameter file. Bare ground is a surface fraction, not a living FATES PFT. Ground cover can overlap vertically; basal area, stems, biomass, LAI, crown cover and modeled vegetation carbon are distinct quantities.", ""]
    for batch in sorted(counts):
        report += [f"## {batch}", ""]
        for r in rows:
            if r["batch"] != batch:
                continue
            report += [f"### {r['site']} — {r['site_name']}", "",
                       f"**Vegetation:** {r['vegetation']}", "",
                       f"**Reported composition:** {r['observed_composition']}", "",
                       f"**Functional interpretation:** {r['observed_pft_summary']}", "",
                       f"**Measurement basis:** {r['denominator']} **Period:** {r['observation_period']}", "",
                       f"**Spatial scope:** {r['spatial_scope']} **Bare ground:** {r['bare_ground']}", "",
                       f"**Evidence:** `{r['evidence_level']}`. {r['verification_status']}. {r['source_title']}. Locator: {r['source_locator']} {source_links(r['source_url'])}.", "",
                       f"**Candidate and limits:** {r['candidate_pft']} {r['uncertainties']}", ""]
            if r["published_model_fcover_json"]:
                report += [f"**Separate published model configuration:** `{r['published_model_fcover_json']}` ({r['published_model_period']}; source-native ORCHIDEE groups). [Table 1]({MODEL_URL}).", ""]
            report += [f"**Next evidence:** {r['next_evidence']}", ""]
    result[f"50_SITE_OBSERVED_PFT_PERCENT_REPORT_{DATE}.md"] = "\n".join(report) + "\n"
    overview = ["# AmeriFlux PFT evidence — all 50 stations", "",
                "## Recommended CLM-FATES inputs — 26 October 2026", "",
                "[**50-site recommended input percentages (v1)**](RECOMMENDED_INPUT_PFT_50_SITES_20261026.md) now gives a complete FIXNC prescription for each station, plus 35 sensitivity or period alternatives. [Full input CSV](RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_20261026.csv), [CLM host matrix](RECOMMENDED_50_SITE_CLM_PCT_NAT_PFT_20261026.csv), and [FATES natural-landunit / vegetated-only matrices](RECOMMENDED_50_SITE_FATES_PFT_PERCENT_20261026.csv) distinguish proposed model fractions from the original observations below. Nine primary prescriptions require a site-private Arctic or hydrodeciduous-shrub HLM map; defaults do not reproduce those targets. No existing surface, parameter file or case was changed.", "",
                "## Original observation inventory", "",
                "Updated 26 October 2026. The five experiment manifests contain **50 distinct stations, 10 per batch**. This collection follows the central-table/report structure of [ICOS_PFT](../../ICOS_sites/ICOS_PFT/).", "",
                f"**Search result: {n} sites with numerical composition/cover leads; {50-n} with qualitative composition, LAI/density or model-only evidence.** Numbers below keep their measured denominators, period and sampling extent. None is automatically an approved full tower-area prescription.", "",
                "| File | Contents |", "| --- | --- |",
                f"| [Master 50-site table](MASTER_50_SITE_OBSERVED_VS_FATES_PFT_{DATE}.csv) | Exact release membership, observed evidence, scalar groups, candidate mapping, published model fCover and missing FATES output status |",
                f"| [Full source report](50_SITE_OBSERVED_PFT_PERCENT_REPORT_{DATE}.md) | Per-site measurement basis, source locator, date, footprint scope and unresolved issues |",
                "| [Evidence CSV](50_site_PFT_evidence.csv) | All 50 observed-composition records |",
                f"| [50-site candidate table](FINAL_50_SITE_PFT_CANDIDATES_{DATE}.csv) | Final consolidated research candidates; filename does not imply approved surface fractions |",
                "| [Further research](50_site_further_research_leads.csv) | Concrete next evidence for each station |",
                "| [Source records and membership](metadata/) | Five curated JSON source ledgers and exact 50-release manifest |",
                "| [Mapping and experiment design](PFT_MAPPING_AND_EXPERIMENT_DESIGN.md) | Source-to-functional mapping and requirements for fixed or competition experiments |",
                "| [Search and provenance](SEARCH_AND_PROVENANCE_20261026.md) | GitHub reuse, primary-source checks and limits of the search |", "",
                "## Five-batch composition index", "",
                "A concise index follows. Read the full report before selecting a modeling proxy. Percentages may describe stems, basal area, specific transects or overstory alone.", "",
                "| Batch | Site | IGBP | Observed/source functional composition | Basis |",
                "| --- | --- | --- | --- | --- |"]
    overview += [f"| {r['batch']} | [{r['site']}](50_SITE_OBSERVED_PFT_PERCENT_REPORT_{DATE}.md) | {cell(r['igbp'])} | {cell(r['observed_pft_summary'])} | {cell(r['evidence_level'])} |" for r in rows]
    overview += ["", "## Published modeling precedents kept separate", "",
                 "[Mahmud et al. (2021) Table 1](https://doi.org/10.1029/2021JG006400) supplies 11 relevant historical ORCHIDEE fCover configurations. The machine-readable JSON preserves the original group names: BS=bare soil; TeNE=temperate needleleaf evergreen; TeBE=temperate broadleaf evergreen; TeBD=temperate broadleaf deciduous; C4G=C4 grass. These are candidate precedents. Shrub versus tree growth form and bare-ground treatment must be checked independently in FATES. US-Aud retains the existing operator-selected 70% C4/30% bare experimental policy, with its model-assumption label.", "",
                 "## Rebuild and validate", "", "```bash", "python3 scripts/build_inventory.py --build", "python3 scripts/build_inventory.py --check", "```", "",
                 "Python standard library only. The script checks 50 unique IDs, 10 per batch, exact release membership, source fields, percentage-versus-LAI/density classification, numerical ranges, complete published model-vector sums, and reproducibility of generated tables. Source percentages are never silently normalized. It writes only documentation tables inside this directory.", "",
                 "No surface, parameter file, forcing, CIME case, restart or Slurm job was modified. Exact active FATES names/indices remain unverified for new configurations. Blank modeled-PFT columns mean not found in the reviewed GitHub snapshot, not proof that a model has never run."]
    result["README.md"] = "\n".join(overview) + "\n"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = read_inputs()
    generated = outputs(rows)
    failures = []
    for name, text in generated.items():
        path = ROOT / name
        if args.build:
            path.write_text(text, encoding="utf-8", newline="\n")
        elif not path.exists() or path.read_text(encoding="utf-8-sig") != text:
            failures.append(name)
    if failures:
        raise SystemExit("Generated output differs or is missing: " + ", ".join(failures))
    n = sum(r["numeric_percent_evidence"] for r in rows)
    print(f"PASS: 50 unique sites; five batches x10; {n} numerical composition/cover leads; "
          f"{50-n} other-evidence sites; 11 separate published model vectors; {len(generated)} reproducible files")


if __name__ == "__main__":
    main()

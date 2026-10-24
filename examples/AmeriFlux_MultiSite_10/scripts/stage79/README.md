# Stage79 — 89 *actual* newly/worsened RH/T edges: source-switch science triage

> **SUPERSEDED AS THE CURRENT OPERATOR RULE BY STAGE80 (24 October 2026).** This Stage79 document remains an archival reproducibility record only. The user now explicitly requests **only 18 original RH<1% half-hours replaced by the already-computed native ERA5 T/D2m/P joint state; all 1,091 original RH 1–5% and every other Stage75 record remain unchanged**. Do not select the former Stage77 1,109-row trial as current forcing. See [Stage80](../stage80/README.md). Existing outputs and evidence are retained; no new ERA5 downloads required.


## Why this step exists

Stage77 **successfully recomputed 1,109 original RH<5% half-hours** (six independent candidate forcings, same-source native ERA5 2 m T + 2 m dewpoint + surface pressure, five coupled variables, no original edits). Stage78 compared the final-to-final candidate against original-to-original RH/T across affected consecutive 30-minute edges. **89 edges** meet its new/worsened high-risk rule:

| Site | Flagged edges | Illustrative maximum new RH jump | Example original RH jump |
|---|---:|---:|---:|
| CA-Ca3 | 13 | 44.91 pp | 3.95 pp |
| CA-Cbo | 18 | 67.02 pp | 2.40 pp |
| CA-Man | 42 | 84.37 pp | 4.00 pp |
| CA-TP4 | 5 | 56.29 pp | 4.45 pp |
| US-Aud | **0** | — | — |
| US-Bar | 11 | 69.85 pp | 2.05 pp |
| **Total** | **89** | | |

**Physical thermodynamic closure alone is not a production science pass.** The boundary differences might reflect a source mismatch between native ERA5 and the unmodified tower neighboring row; or they could reflect actual ERA5 discontinuity, station time-offset/interval meaning, or source QC problems. Do not assume the 89 are errors in the original data or edit non-target QC0 records just to smooth them.

## Stage79 diagnostic (report-only; no patches)

The script `79_era_transition_source_diagnosis.py` uses only existing IRIDIS6 records and **never downloads ERA5 again**:

- Re-verifies Stage77 original/candidate forcing and change-ledger SHA checksums via the Stage78 helper.
- Re-verifies the saved **89-row Stage78 edge CSV** against the corresponding manifest SHA.
- Loads the original downloaded native ERA5 hourly T2m+D2m+surface-pressure CSV, using exactly the provisional source timestamps and interpolation already used by Stage77 (never substituting FLUXNET VPD-based pseudo dewpoint).
- Retrieves the **original and modified RH of both sides** of each affected edge; computes independent **ERA5 RH at each side**, including *unmodified neighboring time*. Checks that the changed side of a Stage77 trial really equals native ERA5 within rounding.
- Optionally reads FLUXMET `TA_F_QC`, `VPD_F_QC`, `TA_F`, `VPD_F` at exact provisional timestamps; these are **source QC context**, not proof that the final forcing uses those exact underlying fields.
- Distinguishes native ERA5 internally sharp episodes from **ERA-vs-unchanged-tower source-switch mismatches** (≥10/≥25 pp) and reports these as risks, *without automatically extending ERA substitutions into unmodified and possibly QC0 observations*.
- Clusters the 89 flagged edges into review groups separated by >2 hours. This is a triage convention, not a natural synoptic event boundary or independent clock verification.

Generated only with `--audit`: `89_edge_native_ERA_vs_unchanged_tower_context.csv`, `clustered_89_edge_source_review.csv`, and `manifest.json` in a new date-stamped `reports/stage79_89_native_ERA_source_transitions_*/` directory.

## IRIDIS6 Stage79 first run: corrected script typo

The initial Stage79 `--audit` run stopped safely at `raw_qc()` with **`NameError: name 'poss' is not defined`**. The code had defined `possibles=sorted(...)` but tested `len(poss)`. This is a Python script typo, **not** an ERA5 source, humidity, or forcing failure; it occurred before report generation. The corrected script now calls `len(possibles)` and its **self-test deliberately exercises the missing-FLUXMET-file condition**, so the bug cannot silently recur. Redownload the new pinned script and rerun `--audit`; no Stage77 native ERA5 downloads, forcing replacements or Stage78 analyses need to be repeated.

## Commands

```bash
python3 -B examples/AmeriFlux_MultiSite_10/scripts/stage79/79_era_transition_source_diagnosis.py --self-test
python3 -B examples/AmeriFlux_MultiSite_10/scripts/stage79/79_era_transition_source_diagnosis.py --check
python3 -B examples/AmeriFlux_MultiSite_10/scripts/stage79/79_era_transition_source_diagnosis.py --audit
```

It is scientifically premature to overwrite active CIME/DATM cases, claim all 89 discontinuities acceptable, or convert original/tower QC0 records to ERA based on a 25-84 pp RH disagreement alone. **The user explicitly chose all 1,109 native ERA5 recomputations as operator-selected *candidate* changes**; they remain intact and check-summed while the 89 edges are investigated. Remaining actual production gate: independently verify LST→UTC/half-hour interval support and decide whether source switching at each edge is acceptable or needs an evidence-supported source-coherent window extension.

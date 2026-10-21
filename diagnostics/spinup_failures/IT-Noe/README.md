# IT-Noe — Negative near-surface RH abort and forcing-source investigation

**Status:** OPEN / UNRESOLVED. This directory contains a **read-only** analysis script, not a forcing repair or a model restart workflow.

**Campaign:** [ICOS / FLUXNET MultiSite 11](../../../examples/FLUXNET_MultiSite_11/README.md)  
**Original incident:** [IT_No e RH abort record](../../../examples/FLUXNET_MultiSite_11/docs/IT_Noe_RH_ABORT_2026-10-18.md)  
**Case:** `IT-Noe_FATES_SPINUP500_11P` (historic name; intended 1,000 model-year spin-up)

## Observed evidence (operator reports, 20 October 2026)

- First five years of startup completed, with archived restart at `2009-01-01-00000`; continuation job `4286761` aborted; `RESUBMIT=198` remained configured, but there was no active job at that snapshot.
- Land log: `rh = -0.481600369697994`; `ERROR RH is negative` in `HumanIndexMod.F90:1019`; call chain from `BareGroundFluxesMod.F90`. This is **model-diagnosed 2-m RH**, not directly negative input QBOT.
- The last visible history record at `nstep=112176` corresponds to approximately 2010-05-28 00:00 under a 2004 start and 48 steps/day. **This does not establish the precise abort timestamp.**
- The selected surface has `PCT_NATVEG=69.4605%`, `PCT_CROP=30.5395%`, and a 15-element natural-PFT axis summing to 100%. It was referenced correctly in `CaseDocs/lnd_in`. Its ecological representativeness remains to be assessed independently.
- Selected FLUXNET2015 `TA_F` on 2010-05-28 reached **-18.46°C (04:00)** and **-16.16°C (07:30)**, with 30-minute changes of +29.399°C and -31.053°C in nearby records. Independent ICOS ERA5 temperature was approximately 16.7°C at those anomalous times. These entries are **strong scientific-QC candidates**, not automatically approved replacements.
- The operator's preliminary 2004–2025 threshold screening found **563 rows flagged by at least one** of TA < -8°C, half-hour |ΔTA| > 8°C, or RH < 10%. Counts in different categories overlap; they are review flags, not the number of confirmed corrupt observations.
- The selected `FLX_F` pairing sometimes combined observational/gap-filled temperature with `VPD_F_QC=2`, indicative of a reanalysis-derived estimate under the FLUXNET2015 product conventions. Pairwise humidity plausibility alone does not verify temporal continuity.

**Important causality limit:** Some 2010-05-28 temperature anomalies occur *after* the last visible history timestamp. They cannot yet be named as the direct abort trigger. Inspect the exact model timestep, state and surface-layer exchange calculations before attributing the failure to forcing.

## Read-only executable

[`it_noe_era_source_audit.py`](it_noe_era_source_audit.py) compares selected candidate TA/VPD/PA against separately supplied ICOS ERA5 for 2010, 2024 and 2025. It reports annual screening counts, source/QC breakdown, largest TA discrepancies, and the candidate failure window.

Run on IRIDIS6 after updating the checkout:

```bash
cd /iridisfs/home/ly3n24/CLM-FATES-single-site-workflows
git pull --ff-only
conda activate clm_fates_env

python3 diagnostics/spinup_failures/IT-Noe/it_noe_era_source_audit.py \
  2>&1 | tee "$HOME/IT-Noe_ERA_comparison.log"
```

Default output: `~/IT-Noe_source_diagnosis/era_comparison_v1/`

- `yearly_QC_vs_ERA_summary.csv`: per-year coverage, temperature discrepancies and review thresholds.
- `review_events_not_approved_for_replacement.csv`: flagged records with provenance.
- `selected_years_joined_readonly.csv`: candidate and ICOS ERA5 joined on timestamp.

Optional: `--root /path/to/IT-Noe/forcing --out /path/to/reports --years 2010 2024 2025`.

Requires Python, NumPy and pandas in the `clm_fates_env` environment. Input files must already exist locally and must respect their providers' license terms. The script refuses a comparison with fewer than 95% matching ERA temperatures. Flag cutoffs (TA < -8°C, |ΔTA| > 8°C/30 min, |TA-ERA| > 15°C, RH < 10%) are **screening triggers only**; ERA is reference information, not automatic ground truth.

**Safety:** Reading existing CSVs and writing new local reports only; no writes to forcing, NetCDF, surface, restart, job scheduler, or GitHub. Re-running to the same `--out` *will overwrite its generated report CSVs*, so choose a new report directory when preserving audit snapshots.

## Next decisions (not yet executed)

1. Verify time alignment and isolate the exact failed model step from the original log and CIME calendar settings.
2. Review selected-source differences and source-specific QC for 2010 and 2024–2025; examine temperature/VPD/pressure **as a thermodynamically consistent triplet**. Do not mass-replace years with ERA automatically.
3. Create a separately versioned correction ledger and candidate forcing **only after** source verification; independently validate revised DATM.
4. Test in an isolated CIME case against the 2009 restart where compatible; if surface/PFT is changed materially, use a new startup case instead.
5. Only resume a long spin-up after short-run numerical and scientific verification. Keep the original case and archival restart intact.

No corrected forcing, resolved RH abort, or successful 1000-year continuation is claimed here.


## 21 October 2026 — Full-cycle review ledger (diagnostic only)

The IT-Noe ERA5 branch continuation job 4613318 failed because CLM calculated negative 2-m RH at HumanIndexMod.F90:1019. The May 2010 ERA5 trial has been created but is NOT a validated production forcing. The 2054-01-01 restart is retained pending validation.

The 2004–2025 source audit covered 385,440 half-hours, marking 922 records. The two-hour-gap grouping found 208 review episodes: 26 in 2010, 69 in 2024, 92 in 2025, and 21 in other years. Screening results are NOT automatic correction decisions.

New script: [it_noe_build_review_ledger.py](it_noe_build_review_ledger.py). It checks that all flagged records map to exactly one episode, adds four hours of original context on both sides, includes source and QC provenance, assigns triage priorities, and defaults every review decision to PENDING_SCIENTIFIC_REVIEW. It NEVER edits forcing, restart, CIME or Slurm.

### Run on IRIDIS6 without git pull

~~~bash
conda activate clm_fates_env
mkdir -p "$HOME/IT-Noe_source_diagnosis/scripts"
SCRIPT="$HOME/IT-Noe_source_diagnosis/scripts/it_noe_build_review_ledger.py"
curl -fLsS "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/diagnostics/spinup_failures/IT-Noe/it_noe_build_review_ledger.py" -o "$SCRIPT" || exit 1
python3 -m py_compile "$SCRIPT" || exit 1
ROOT="$HOME/IT-Noe_source_diagnosis"
JOINED="$ROOT/full_2004_2025_20261021_213316/selected_years_joined_readonly.csv"
EPISODES="$(find "$ROOT" -maxdepth 2 -type f -name meteorological_review_episodes.csv -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2-)"
test -s "$JOINED" && test -s "$EPISODES" || { echo "Missing audit or episode input"; exit 1; }
OUT="$ROOT/ledger_$(date +%Y%m%d_%H%M%S)"
python3 "$SCRIPT" --joined "$JOINED" --episodes "$EPISODES" --out "$OUT" --context-hours 4
~~~

New local outputs: event_decision_ledger.csv, flagged_records_with_event_key.csv, event_context_plus_minus_hours.csv, yearly_review_summary.csv, review_provenance.json, and README.md.

Priority P0 identifies incidents on 2010-05-13 and 2010-05-28; all thresholds are triage only. Episode start/end are FIRST/LAST flagged records, not final replacement boundaries. Review original FLUXNET/ICOS provenance, date conventions, ERA5 corroboration, and the wider unflagged context before approving any corrections. Test proposed versioned DATM in an isolated CIME case. Do NOT resume the production 1000-year spin-up on these automated flags alone.


## Next step: unapproved correction brackets and ERA boundary checks

The review ledger was successfully built at
`/home/ly3n24/IT-Noe_source_diagnosis/ledger_20261021_215448`
with 385,440 observations, 922 flagged records and 208 events:
3 P0 incidents, 75 P1 high priority, and 130 P2 review.

Run [it_noe_prepare_correction_candidates.py](it_noe_prepare_correction_candidates.py)
on those existing CSVs. The script creates review-only hypothetical replacement
brackets with optional one-hour buffers, compares selected source with independent
ERA observations, recalculates implied relative humidity and humidity physical
limits, and checks temperature jumps at both hypothetical replacement boundaries.
All decisions remain scientifically **UNAPPROVED**.

~~~bash
conda activate clm_fates_env
DIR="$HOME/IT-Noe_source_diagnosis"
mkdir -p "$DIR/scripts"
SCRIPT="$DIR/scripts/it_noe_prepare_correction_candidates.py"
curl -fLsS "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/diagnostics/spinup_failures/IT-Noe/it_noe_prepare_correction_candidates.py" -o "$SCRIPT" || exit 1
python3 -m py_compile "$SCRIPT" || exit 1
JOINED="$DIR/full_2004_2025_20261021_213316/selected_years_joined_readonly.csv"
LEDGER="$DIR/ledger_20261021_215448/event_decision_ledger.csv"
OUT="$DIR/correction_candidates_$(date +%Y%m%d_%H%M%S)"
python3 "$SCRIPT" --joined "$JOINED" --ledger "$LEDGER" --out "$OUT" --buffer-hours 1
~~~

Outputs: candidate_review_brackets_UNAPPROVED.csv,
priority_P0_P1_UNAPPROVED.csv, hypothetical_boundary_checks.csv,
review_priority_summary.csv, provenance.json, README.md.
The proposed bounds are NOT scientifically approved. Replacing a full
interval solely on these flags is not appropriate. Note that the tool
assumes VPD in hPa and PA in kPa in the source-audit CSV; verify
metadata before using numerical conclusions. Preserve 2054 restart,
all original and versioned DATM files, and the production case.


## Next: READ-ONLY isolated CIME trial preflight (after 208-candidate scan)

The latest correction candidate report is
`/home/ly3n24/IT-Noe_source_diagnosis/correction_candidates_20261021_220229`.
It reported 208 candidate episodes, 78 P0+P1 priorities, 208/208 ERA
physical-triplet preflight passes, zero overlaps of 1-hour brackets, and
64 hypothetical temperature boundary warnings. These results do not approve
replacement of a single record.

Before any model job, run
[it_noe_isolated_test_preflight.py](it_noe_isolated_test_preflight.py)
to verify the existing, separate **whole-May 2010 diagnostic trial**, its
provenance SHA256, original 2004–2025 symlinks, the model's read-only CIME
configuration and presence of the three 2054 restart components. This
is an INPUT and compatibility inventory, not scientific approval for
restart, and it DOES NOT submit jobs or edit files.

~~~bash
conda activate clm_fates_env
DIR="$HOME/IT-Noe_source_diagnosis/scripts"
mkdir -p "$DIR"
SCRIPT="$DIR/it_noe_isolated_test_preflight.py"
curl -fLsS "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/diagnostics/spinup_failures/IT-Noe/it_noe_isolated_test_preflight.py" -o "$SCRIPT" || exit 1
python3 -m py_compile "$SCRIPT" || exit 1
python3 "$SCRIPT" 2>&1 | tee "$HOME/IT-Noe_isolated_test_preflight_20261021.log"
~~~

Expected source trial: datm_11_IT-Noe_ERA5_may2010_diagnostic_20261021_214215.
Production case: IT-Noe_ERA5_ABW_BRANCH2009, blocked after job 4613318.
Restart inventory: archive of the production case at 2054-01-01-00000.
Do not switch production DATM, edit the restart, or resubmit production.
After reviewing preflight output, configure and verify an independently named
test case; only then choose to submit a limited, reversible trial.


## Direct 1000-year continuation policy (operator decision, 21 October 2026)

**Operator choice:** skip the separately submitted short model test and, after
complete forcing repairs and validations, proceed directly to the remaining
**950 model years** of the existing 1000-year experiment. Existing case
`IT-Noe_ERA5_ABW_BRANCH2009`, checkpoint
`2054-01-01-00000` = 50/1000 years, STOP_N=5 and RESUBMIT=189,
represent 190 remaining five-year model segments.

**Not ready for production:** the current `may2010` trial only replaces 1488
May-2010 half-hour records; 21 other years are unchanged. The existing CIME
DATM stream still points at the previous abort-window sensitivity dataset.
All 208 flagged source/QC review episodes require resolution, and 64
hypothetical replacement boundaries raised temperature-jump warnings.
The 2054 restart file inventory does not prove scientifically consistent
states under subsequently corrected forcing.

An additional fail-closed, **read-only** gate is provided in
[it_noe_1000yr_direct_resume_gate.py](it_noe_1000yr_direct_resume_gate.py).
It checks all 22 annual forcing paths, CIME stream references, 2054 restart
components, Slurm jobs, plus a version-specific scientific approval manifest
with SHA256 hashes and complete source/boundary/full-cycle QC attestation.
No actual production approval has been created; do not fabricate it.
The tool never changes any files or submits/cancels Slurm jobs.

~~~bash
conda activate clm_fates_env
mkdir -p "$HOME/IT-Noe_source_diagnosis/scripts"
SCRIPT="$HOME/IT-Noe_source_diagnosis/scripts/it_noe_1000yr_direct_resume_gate.py"
curl -fLsS "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/diagnostics/spinup_failures/IT-Noe/it_noe_1000yr_direct_resume_gate.py" -o "$SCRIPT" || exit 1
python3 -m py_compile "$SCRIPT" || exit 1
python3 "$SCRIPT" 2>&1 | tee "$HOME/IT-Noe_direct_resume_gate.log"
~~~

Expect READY_FOR_DIRECT_RESUME=NO until a real full-cycle corrected
`datm_11_IT-Noe_corrected_v2` and provenance-checked approval exist,
and until the production DATM references that approved directory.
Do not invoke `maintenance/recover_blocked_spinups.py run --site IT-Noe`
before then: the recovery tool preserves the science namelists and could
re-submit the SAME defective forcing. After approvals, production case and
restart staging must be audited separately before the job is submitted.

**Scientific caveat:** continuing from 2054 does not erase the effects of
the defective forcing in prior model years. Report as legacy-state
continuation unless an equivalence/restart-consistency assessment supports
the intended scientific interpretation.

## Full-cycle IT-Noe QC forcing candidate (October 2026)

[New builder](it_noe_qc_v2_builder.py) constructs a distinct 2004–2025 DATM candidate, using ICOS ERA5 TA/VPD/PA within the 208 unapproved review brackets and cosine shoulder interpolation of TBOT/QBOT/PSRF. It does NOT approve data or change the production CIME case. It copies all 22 annual NetCDFs, keeps SHA256 provenance and a row-level edit log. Inspect annual residual QC before considering model submission.

IRIDIS6: download the builder directly from GitHub, run `python3 it_noe_qc_v2_builder.py --out /new/unique/forcing/path` for dry run, then repeat with `--write-candidate` for a NEW path. The input defaults are the existing 20261021 213316 audit and 220229 bracket reports. Run with `-h` to review parameters. Original forcing, checkpoint 2054 and Slurm jobs are untouched. The generated `CANDIDATE_PROVENANCE.json` explicitly marks the result UNAPPROVED; do not fabricate production approval or use the production recovery command yet.

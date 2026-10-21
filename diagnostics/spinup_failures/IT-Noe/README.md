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

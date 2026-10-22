# AmeriFlux sites — CLM-FATES experiment collection

This collection keeps AmeriFlux batches separate from the existing [ICOS multi-site campaigns](../ICOS_sites/) and the [AmeriFlux US-Ha1 single-site example](../AmeriFlux_US-Ha1/).

| Batch | Sites | Current record |
| --- | ---: | --- |
| [AmeriFlux Batch 01](../AmeriFlux_MultiSite_10/) | 10 | See the batch-specific operational record and scripts |
| **[AmeriFlux Batch 02](../AmeriFlux_MultiSite_10_Batch02/)** | 10 | Stages00–10 published. Operator Stage07: 5 numeric candidates; 5 sites blocked by 4,904 unresolved humidity pairs. Stage08 sensitivity and the follow-on Post-v5 gates/runner are ready for execution. |
| **[AmeriFlux Batch 03](../AmeriFlux_MultiSite_10_Batch03/)** | 10 | Stages00–01 ready: single-connection WSL upload and recursive extraction; live transfer pending. |

Batch03 sites: US-Kon, US-Me2, US-Me6, US-MMS, US-MOz, US-Mpj, US-MtB, US-NC2, US-NR1 and US-NR3. See its [exact releases](../AmeriFlux_MultiSite_10_Batch03/sites.tsv) and [instructions](../AmeriFlux_MultiSite_10_Batch03/README.md). Later processing includes QCv5 and a separate Post-QCv5 audit before DATM or spin-up.

Batch02 sites: US-BZS, US-CMW, US-EML, US-GLE, US-Ha1, US-Ho1, US-Ho2, US-Ho3, US-ICh and US-ICt. Its [exact releases](../AmeriFlux_MultiSite_10_Batch02/sites.tsv), [operating instructions](../AmeriFlux_MultiSite_10_Batch02/README.md) and [stage scripts](../AmeriFlux_MultiSite_10_Batch02/scripts/) are maintained as a separate case under `main/examples/`.

Batch02 candidates are not approved forcing or model cases. No DATM or Slurm jobs were created for this batch. Raw tower packages and large model NetCDFs remain on local/IRIDIS storage rather than GitHub.

## Shared measurement-height metadata for ALL AmeriFlux batches

Use the versioned, **complete** user-supplied [2026-09-08 BASE Measurement Height CSV](metadata/BASE_MeasurementHeight_20260908.csv) and the [shared height candidate auditor](scripts/28_audit_shared_BASE_measurement_heights.py). This covers 40,306 source rows and 587 AmeriFlux sites. Raw upload SHA256: `1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a`.

The older Batch01 Stage26/27 BIF-height scripts were retired and deleted; they assumed FLUXNET BIF `VAR_INFO_*` fields that the ten AmeriFlux BIF files do not contain. **BIF coordinates remain valid as a separate workflow.**

For any batch, supply that batch's `sites.tsv` via `--sites-tsv`. All candidate TA/WS heights retain their original variable names, missing/partial dates, instruments and comments. Do not automatically map an indexed TA level, wind height or EC measurement height to model `ZBOT`. Create a new separately versioned snapshot when the monthly BASE metadata changes; do not overwrite this source file. The numerical QC and meteorological science gates are also separate from the height source audit.

## Stage30 — open height-science decisions

[Stage30 read-only mapping/date audit](scripts/30_audit_BASE_height_mapping_gaps_and_date_windows.py) follows Stage29. Batch01 has 5 unapproved static candidates, 3 dynamic candidates with partial dates, and 2 unresolved multi-layer TA arrays (CA-Cbo, CA-Man). Stage30 writes only candidate evidence, blocked sensor alternatives, uncertain date windows, and blank approval decisions. It does not equate `TA_PI_F` with FLUXNET `TA_F` or create ZBOT/DATM. Scientific approval remains pending.

## Stage31 — user-selected static/dynamic height policy, provisional scenarios

The user selected the same practical policy as the earlier ICOS/FLUXNET work: use **dynamic TA measurement heights when changes are documented**, otherwise a **static single TA measurement height**, and apply the first known TA height backward over earlier forcing years **as an explicitly flagged model assumption**. [Stage31](scripts/31_build_provisional_ZBOT_policy_scenarios.py) implements this rule for independently auditable source candidates. It models incomplete month/year change dates as two bracketing scenarios (earliest vs upper-bound effective date) and reports the number of affected half-hours. It **does not** silently fix a date or claim sensor matching to `TA_F` has been verified. Multi-layer sites CA-Cbo and CA-Man remain blocked pending specific TA-level mapping. This produces only JSON/CSV policies and comparisons, not a ZBOT NetCDF or a model job. Scientific sign-off is still required before final DATM use.

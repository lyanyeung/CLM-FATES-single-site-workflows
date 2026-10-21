# CLM-FATES Spin-up Failure Diagnostics

A repository-wide home for **site-specific, evidence-led investigation** of failed, stalled, or scientifically suspect CTSM/CLM-FATES spin-ups on IRIDIS6.

## Cases

| Site | Investigation | Status |
| --- | --- | --- |
| [IT-Noe](IT-Noe/README.md) | Negative model-diagnosed near-surface RH; source-aware FLUXNET/ERA5 meteorological audit | **Unresolved — read-only investigation** |
| [CH-Aws](../../examples/FLUXNET_MultiSite_11/docs/CH_Aws_HUMIDITY_FAILURES_2026-10-15.md) | Failed humidity sensitivity runs; winter humidity-source uncertainty | **Unresolved — existing incident record** |
| [FR-Hes](../../examples/FLUXNET_MultiSite_8/README.md) | Interrupted spin-up/archival recovery | **Under separate investigation** |

## Principles

1. Preserve original tower observations, licensed meteorology, forcing NetCDF, surface NetCDF, checkpoints, original CIME cases, and logs.
2. Start with read-only triage, isolate the exact failure timestep, and compare original source/QC fields before designing changes.
3. Separate **numerical failure attribution** from **ecological representativeness**, including surface/PFT choices.
4. Version any proposed correction and preserve original provenance and SHA-256 hashes. A numerical screening threshold is not scientific approval.
5. Use independent short test cases before any long production restart; never rerun original Stage18 batch submission against existing cases.
6. Do not commit raw FLUXNET/ICOS CSVs, downloaded ERA datasets, NetCDFs, run archives, private logs, or account credentials.

See each site's README for evidence, diagnostics, limitations, and next steps. These notes are **not proof that an incident is resolved**.

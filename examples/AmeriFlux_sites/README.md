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

# DK-Sor: spin-up years 1000–2425

These figures cover the DK-Sor 2425-year archived snapshot dated 2026-10-24. They were rendered locally using the repository's Python plotting script and the archived CSV/metadata inputs; they are not the byte-for-byte files produced by the separate IRIDIS execution. No raw model history files are included.

- Carbon pools: 1000–2425 inclusive, model years 2995–4420.
- Last 250 years: spin-up years 2176–2425.
- PFT plot: vegetation carbon shares for up to six PFTs selected by the original stage-27 criterion.
- GPP/NEE: last complete 29-year forcing cycle, model years 4374–4402 mapped to observation years 1996–2024; model years 4403–4420 are an incomplete tail excluded from that comparison.

CLM pools use g C m-2; the original FATES pool metadata records kg m-2, retained as given. The GPP/NEE plot uses paired monthly means in g C m-2 d-1. PNG, PDF and SVG plots and the filtered annual carbon/PFT CSVs are included.

Reproduction script: [31_plot_DK_Sor_year1000_to_final.py](../../../../scripts/31_plot_DK_Sor_year1000_to_final.py). Inputs: [archived snapshot](../../../convergence_snapshots/20261024T100510Z_DK_Sor_2425_archive_snapshot/DK-Sor/). Completing this spin-up does not establish ecosystem equilibrium.

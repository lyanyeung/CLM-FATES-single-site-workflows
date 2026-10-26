# ICOS ETC ancillary reports — PFT and soil evidence for the 38 European sites

**Why:** the FLUXNET package BIF (e.g. `EUF_AT-Neu_FLUXNET_BIF_*.csv`) is only a subset of the site metadata. For AT-Neu it has IGBP GRA, canopy height 0.3 m (C3 grass), a site description, climate and UTC. It has no species composition (`GRP_SPP_*`) and no soil texture. The `BIFVARINFO_HH/DD/WW/MM/YY` files hold per-variable definitions and sensor heights (AT-Neu `TA_F` 2.5 m, `WS_F` 2.5 m), not vegetation.

The ICOS equivalent of the AmeriFlux full BADM is the ICOS ETC ancillary data:
- [Summary report](https://icos.uantwerpen.be/Content/AncillaryReports/CH-Dav_Ancillary_Report.html): charts.
- [Full report](https://icos.uantwerpen.be/Content/AncillaryReports/SE-Nor_Full_Ancillary_Report.html): numeric tables. For example, the `GRP_TREE` stand table gives `SPP_PERC` per species, year and plot (CP/SP).
- `GRP_SOIL` has SOC, N and bulk density for 0–100 cm. **Soil texture is not part of the ICOS ETC soil protocol shown in these reports.**

Reports exist only for ICOS-labelled ecosystem stations. Non-ICOS sites return HTTP 404, and the script records that.

**Script:** [01_fetch_ICOS_ancillary_reports.py](scripts/01_fetch_ICOS_ancillary_reports.py) uses the standard library only (WSL, laptop or IRIDIS). For all 38 sites it downloads both reports and exports every HTML table and every embedded DataTables widget to CSV. It also collects species-like and soil-like tables, plus a keyword context file (sand/silt/clay/texture/SPP_PERC/WRB).

```bash
python3 -B 01_fetch_ICOS_ancillary_reports.py --self-test
python3 -B 01_fetch_ICOS_ancillary_reports.py --out ~/ICOS_ancillary_20261026
```

It outputs `01_report_inventory.csv`, `02_species_tables_long.csv`, `03_soil_tables_long.csv`, `04_keyword_context.csv`, `tables/*.csv` and `raw/*.html`. The next step is to map the species onto FATES PFTs and compare the result with [FINAL_38_SITE_FIXNC_PFT_20261025.csv](../ICOS_PFT/FINAL_38_SITE_FIXNC_PFT_20261025.csv).

## Run 1 (operator, 26 Oct 2026 18:16 UK)

- **14/38 sites have a summary report:** BE-Bra, BE-Vie, CH-Dav, CZ-BK1, DE-Tha, DK-Sor, FI-Hyy, FI-Sod, FR-FBn, FR-Fon, FR-Hes, FR-Pue, IT-Ren, NL-Loo. The other 24 return 404.
- **Full reports:** HTTP 404 for all 38 sites.
- **No HTML tables with species or soil:** the 3–7 MB summary reports carry their numbers inside chart widgets. `--from-raw` re-parses the downloaded `raw/*.html` without network. It exports every plotly trace point by report section (`05_plotly_traces_long.csv`) and a per-section count of tables, widgets and embedded images (`06_report_structure_by_section.csv`). Images cannot be read numerically.

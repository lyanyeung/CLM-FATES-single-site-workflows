# US-MtB: Claude workstream handback (2026-10-29)

This answers [the 2026-10-28 handoff](US_MTB_CLAUDE_INDEPENDENT_HIGH_ALTITUDE_RESEARCH_HANDOFF_20261028.md). US-Me6 was not touched.

## Result

The complete US-MtB research shadow timeline has been built under each decision the user approved:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/mtb04_US-MtB_research_shadow_20261029T034057Z_ed54796b/`

- **File:** `US-MtB_MTB04_RESEARCH_SHADOW_NOLEAP.csv`. It has 280 320 HH with the same columns and conventions as Stage12g, and no NaN in any column.
- **Provenance:** every change is listed in `MTB04_change_provenance.csv`, with an SHA receipt in `mtb04_research_shadow_receipt.json`.
- **Status:** the folder keeps the `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker. Post-v5, DATM and spin-up still need a separate user decision.
- **Changes against Stage12g:**
  - TA_USE/TBOT replaced in 103 HH;
  - VPD_USE/QBOT filled or recomputed in 2942 HH.

| Change | HH | Evidence |
| --- | --- | --- |
| 31 m temperature fault replaced by the 16 m consensus transfer | 44 | Faults include the 2022 31 m+24 m failure at −39.3 °C (RH 0.5–0.7 %) and MDS fills that disagree with three measured levels. The synthetic 31 m gaps (1/5/22 HH) give MAE 0.13/0.18/0.27 °C. |
| 31 m clipped below −10 °C (2016–2020), replaced by 16 m | 59 | In BASE, the 31 m and 24 m sensors go missing below −10 °C. |
| Humidity from measured 24 m RH | 94 | FLUXMET QC0 validation: MAE 0.23 hPa, 0.6 % of errors > 2 hPa, 12/12 years pass. |
| Humidity from measured 16 m RH | 54 | MAE 0.13 hPa, 0.05 % > 2 hPa, 9/9 years. 2 of these are capped by 0.04 % to the DATM saturation. |
| COMPANION_E (release-paired ERA vapour pressure at tower T), user option B | 2668 | Gap regime with TA_F − TA_ERA ≤ −5 °C: MAE 0.94 hPa, bias +0.27 hPa, 8.3 % > 2 hPa, 12/15 years. The predeclared per-year gate is **not** met (2015, 2017, 2018). |
| COMPANION_E outside the validated regime (labelled) | 57 | User decision. This regime has a typical MAE of about 1.7 hPa. |
| Saturation at DATM `datm_eSat` (Flatau; over ice when T < 0 °C) | 10 | These points have companion e above saturation at the tower T. DATM would cap them anyway (CDEPS 1.0.105). |
| Temperature changed only: vapour pressure kept, VPD recomputed | 59 | 2 of these are capped to the DATM saturation. |

## Handoff checklist

| # | Item | Status |
| --- | --- | --- |
| 1 | True grid height, instrument heights, inversions, grid selection | Instrument heights were taken from BASE: TA/RH at 31, 24, 16, 8.75 and 1.5 m, and the sonic at 29.8 m. Night inversions were documented across those levels. **ERA5-Land geopotential was not downloaded**: the Stage12f files hold only t2m, d2m and sp. It is not needed for the final method, which uses no ERA5-Land values. It stays open if the grid height itself is wanted. |
| 2 | Time alignment | BIF UTC−7. Arizona has no DST, so standard time is UTC−7 all year. The BASE and FLUXMET clocks agree (TA_1_1_1 = TA_F at 100 % of QC0 rows). No clock was changed. The ERA5-Land pairing was used only for diagnostics. |
| 3 | Humidity validated against tower QC0 | Done in MtB01–03: all years, by temperature-difference regime, season, 3-hour block, temperature bin and VPD bin, plus runs of errors above 2 hPa. |
| 4 | Terrain-aware humidity alternatives | Done: COMPANION_E, two block-excluded empirical methods, and 24/16 m level transfer. |
| 5 | Four frozen-phase events against installed code | Done. CDEPS `datm_eSat` caps specific humidity at ice saturation, so GRID_RH would be capped. These points now take COMPANION_E, which is not supersaturated. |
| 6 | ± 2 h context tables | Done, saved as SHA-sealed reports: `reports/mtb01_US-MtB_regime_matched_QC0_humidity_20261029T034346Z_fefd1c18/E_context_pm2h.csv` (frozen-phase events and cold episodes) and `reports/mtb02_US-MtB_T_fault_bridge_regime_humidity_20261029T034408Z_b77a2dc7/X_context_pm2h.csv` (fault and review runs). |
| 7 | Decision package | [MTB02 package](MTB02_RESULTS_AND_DECISION_PACKAGE_20261028.md), [BASE evidence and decisions](MTB_BASE_5-5_MULTILEVEL_EVIDENCE_20261029.md). Each decision was the user's. |

## Additional findings outside the original brief

- The FLUXMET TA_F for 2013–2020 has no value below −10 °C. The FLUXMET release therefore understates cold extremes in those years, apart from the 59 HH replaced here.
- Warm constant nights, such as 13.33 °C for 3.5 h, are 0.5 °F quantisation and not faults; T_SONIC confirms this.
- The 2011-02-02/03 reading of −24 °C matches the documented Southwest cold outbreak; Tucson recorded a low of 18 °F. It was kept.

Scripts: `scripts/mtb/MtB01`–`MtB04`, each pinned to the one before.

## Read-only verification for the Batch03 workstream (Codex/ChatGPT)

The following read-only check (no writes) runs on IRIDIS6. It verifies:
- the SHA receipt of all four MtB folders;
- the shadow's shape, columns and NaN count;
- unchanged rows against Stage12g;
- the change counts.

```bash
python3 - <<'PY'
import json, hashlib, pandas as pd, numpy as np
from pathlib import Path
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
F={"mtb01":R/"reports/mtb01_US-MtB_regime_matched_QC0_humidity_20261029T034346Z_fefd1c18/mtb01_receipt.json",
   "mtb02":R/"reports/mtb02_US-MtB_T_fault_bridge_regime_humidity_20261029T034408Z_b77a2dc7/mtb02_receipt.json",
   "mtb03":R/"reports/mtb03_US-MtB_multilevel_fill_candidates_20261029T031536Z_50d84498/mtb03_receipt.json",
   "mtb04":R/"science_trials/mtb04_US-MtB_research_shadow_20261029T034057Z_ed54796b/mtb04_research_shadow_receipt.json"}
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for k,f in F.items():
    rec=json.loads(f.read_text()); bad=[n for n,d in rec["output_sha256"].items() if sha(f.parent/n)!=d]
    print(k,"receipt",rec["version"],"| files",len(rec["output_sha256"]),"| SHA mismatches",bad or "NONE")
S=F["mtb04"].parent; s=pd.read_csv(S/"US-MtB_MTB04_RESEARCH_SHADOW_NOLEAP.csv")
g=pd.read_csv(R/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/US-MtB_STAGE12G_INCOMPLETE_NOLEAP.csv")
print("rows",len(s),"| columns equal Stage12g",list(s)==list(g),"| NaN",int(s.drop(columns="time").isna().sum().sum()))
prov=pd.read_csv(S/"MTB04_change_provenance.csv",dtype={"native_key":str})
key=pd.to_datetime(g.time).dt.strftime("%Y%m%d%H%M"); ch=key.isin(set(prov.native_key))
same=all(((g[c]==s[c])|(g[c].isna()&s[c].isna()))[~ch].all() for c in g.columns)
print("changed rows",int(ch.sum()),"| unchanged rows identical to Stage12g",same)
print(pd.read_csv(S/"MTB04_change_counts.csv").to_string(index=False))
e=(6.112*np.exp(17.67*s.TA_USE/(s.TA_USE+243.5))-s.VPD_USE)*100; q=0.622*e/(s.PSRF-0.378*e)
print("QBOT closure max rel err",float(np.nanmax(np.abs(q/s.QBOT-1))),"| TBOT-TA_USE-273.15 max",float(np.nanmax(np.abs(s.TBOT-s.TA_USE-273.15))))
PY
```

Expected output:
- SHA mismatches: NONE for all four folders;
- rows: 280320, with columns equal to Stage12g;
- NaN: 0;
- unchanged rows identical to Stage12g: True;
- the change counts in the table above;
- QBOT closure error near 1e-15;
- TBOT offset near 1e-13.

The decision still open for the user: whether to admit this shadow to Post-v5, build the DATM forcing and enter the Batch03 AD400. Until then the `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker stays in place.

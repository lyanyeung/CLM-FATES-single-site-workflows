# US-Whs 2012 May and all-year original TA discontinuity audit — Stage66

## Operator-supplied source evidence, from 25–27 May 2012

The user supplied complete original 48×3 US-Whs half-hour `TA_F`, `TA_F_QC`, `TA_ERA` rows from SHA-verified AmeriFlux FLUXMET original archive. On **25 May** the source QC1 to QC2 transitions lead to extreme 30-minute temperature changes:

| Native time before → after | Original TA_F before → after (°C) | TA jump °C | Source QC before→after |
|---|---|---:|---|
| 05:00→05:30 | 23.584 → 31.635 | +8.051 | 1→1 |
| 05:30→06:00 | 31.635 → 17.814 | −13.821 | 1→2 |
| 08:30→09:00 | 21.288 → 33.085 | +11.797 | 2→1 |
| 09:00→09:30 | 33.085 → 23.191 | −9.894 | 1→2 |
| 09:30→10:00 | 23.191 → 32.765 | +9.574 | 2→1 |

25 May QC2 source TA_F equals source TA_ERA exactly (e.g. 06:00=17.814°C); 26 and 27 May TA_F are entirely QC1, and can diverge from source TA_ERA by +11.489°C at 26 May 06:00 and +19.938°C at 27 May 06:00. Stage65 confirmed no source QC0 measured TA within ±3 days and normal contemporaneous measurement–processed-ERA median differences much smaller (±7-day all QC0 median +0.915°C; near-06:00 QC0 median +1.734°C). These facts justify broader investigation of **both** filled source branches.

## Important provenance and science scope

`TA_F_QC=0` indicates original source-reported observed TA; `1` MDS-fill; `2` source processed ERA fill. They are **lineage labels, not interchangeable confidence scores**. Do **not** simply change QC2 to QC1 or directly copy a QC1 interpolation between potentially erroneous QC1 neighboring temperatures; instead any eventual repair needs a versioned original-QC-preserving candidate, complete local physics and explicit investigator approval. Source `TA_ERA` is original FLUXMET processed companion, **not separately downloaded ERA5-Land**.

User requests: audit all remaining original US-Whs temperature spikes before deciding whether the site can be finished. Original Stage63 has **only one P2/P3 low RH HH** `201205260600` but this does **not** mean only one suspicious source temperature HH.

## Stage66 immutable source scripts

- [All-year source TA step checker](../scripts/stage66/66_US_Whs_full_record_TA_jump_QC_READONLY.py) at GitHub commit `a702a2f144a6bbb0e02acfab04e27200e7594e84`, Git blob `736f7be58b5ca1426ac8adae745c4dd380f1765a`.
- [IRIDIS6 SHA-pinned launcher](../scripts/stage66/run_stage66_US_Whs_all_TA_jumps_iridis6.sh) commit `f5d1332ab069f2d8600c3f519c84a8956e2f09eb`, Git blob `bbf544de1f5fdbc0045bdc86166157e44137cd12`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/f5d1332ab069f2d8600c3f519c84a8956e2f09eb/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage66/run_stage66_US_Whs_all_TA_jumps_iridis6.sh" -o "$HOME/run_stage66_Whs.sh" && test "$(git hash-object "$HOME/run_stage66_Whs.sh")" = "bbf544de1f5fdbc0045bdc86166157e44137cd12" && bash "$HOME/run_stage66_Whs.sh"
```

### Outputs and review gate

- Original full-record QC0/1/2 source counts, yearly counts and 30-minute jumps ≥3, ≥5, ≥8 and ≥10°C.
- Breakdown of ≥5°C jumps by QC transitions `0→0`, `1→1`, `1→2`, `2→1`, etc.
- All 25–27 May 2012 half-hour jumps ≥3°C, and the top 35 largest original TA jumps anywhere in the site record, printed to operator terminal.
- New report `stage66_US_Whs_ALL_YEARS_original_TA_30min_jumps_ge3C.csv` with original source TA_F, TA_F_QC, TA_ERA, SW and the before/after values for every flagged original native 30-minute pair.

Status: GitHub source and launcher SHA verified, **operator IRIDIS6 Stage66 execution not yet reported**. Results are numeric screens; they do not authorize QC relabels, original source modifications, approved 204-overlay changes, DATM/CIME or Slurm. The site is not scientifically complete just because the original P2/P3 low-RH screen found only one HH.

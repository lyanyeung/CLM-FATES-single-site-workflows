# Stage80 — LATEST operator rule: **RH <1% only**, all other forcing rows unchanged

**Priority: FINAL operator decision, 24 October 2026.** This **supersedes** Stage77's full RH<5% replacement choice, Stage78's provisional ten-site selection and Stage79's request for 89 new boundary reviews. The operator explicitly directs:

- Replace **EVERY original RH below 1% record**, regardless of its ERA/tower boundary differences. Use the **already computed native ERA5 2m temperature + 2m dewpoint + surface pressure** state, with the five coupled downstream variables `TBOT`, `TA_USE`, `QBOT`, `PSRF`, `VPD_USE`.
- **Preserve EVERY other record** (including all **1,091 original RH 1–5% half-hours**, unchanged in the selected Stage75 candidate). Do not extend the ERA5 repair across neighboring tower QC0 or QC1 values to smooth edges.
- The original selected baseline is the validated **Stage75 ten-site set**; it includes the separate Stage74 CA-Man 18-row user-reviewed meteorological replacement. Those Stage74 edits remain unchanged because they predate the latest RH threshold choice.

## Exact approved scope

| Site | Original RH<1% → Native ERA5 joint replacement | Original RH 1–5% retained |
|---|---:|---:|
| CA-Ca3 | **7** | 34 |
| CA-Cbo | **2** | 26 |
| CA-Man | **1** | 120 |
| CA-TP4 | **0** | 6 |
| US-Aud | **0** | 874 |
| US-Bar | **8** | 31 |
| Other 4 sites (BR-Ma2, CA-LP1, CA-TP1, CA-TP3) | **0** | 0 |
| **Total** | **18** | **1,091** |

Stage77 has already calculated all 18 corrected ERA5 states and Stage77/78 confirms that they are thermodynamically consistent and remove every original RH<1% observation. **No CDS re-download** is necessary. Stage79 determined that the earlier 89 warnings were predominantly **ERA5-to-unchanged-tower source switches**, and the user's instruction chooses not to extend the replacements, even if some RH transitions remain large. Do not misinterpret their presence as a failure to implement the rule.

## Stage80 script

[80_operator_RH_lt1_only_native_ERA5_selected.py](80_operator_RH_lt1_only_native_ERA5_selected.py)

`--self-test` tests the explicit threshold and coherent five-field substitution. `--check` reads the validated Stage75 and Stage77 source/trial receipts and calculates the four-site patch scope without writing anything. `--trial --outdir NEW_UNIQUE_DIR` creates four **complete** new forcing CSVs at `SITE/forcing/processed_stage80_RH_lt1_native_ERA5/SITE_CLM_forcing_FIRST_LAST.csv` and a ten-site source-selection manifest. The other six sites are kept by original Stage75 path and checksum; they are **not** copied or modified.

Checks include:

1. Verify SHA-256 hashes of the ten Stage75 baselines, all six Stage77 full trials, and exact 1,109-row original operator ledgers through the Stage78 source validator.
2. At **every row** in the four selected modified sites, choose native ERA5 full row **iff** original Stage75 RH<1%; otherwise keep all fields of the original Stage75 row. Verify 18/18 replacements and 1,091 original RH1–5 observations.
3. Independently reread entire written files and **fail** if any non-target row or any column other than the five coupled met fields changed.
4. Run the Stage58 complete NOLEAP/calendar/physics audit on each of the four new files. Document any **new RH>=25 pp / temperature>10°C edges** as *operator-accepted* risks rather than automatically changing unflagged tower neighbors.
5. Write `10_site_selected_forcing_sources.tsv`, `18_native_ERA5_RH_lt1_operator_change_ledger.csv`, `operator_accepted_new_RH_T_boundary_warnings.csv`, and `manifest.json` including SHA checksums and source provenance.

**After Stage80**, follow the ten-site selected-candidate manifest for later forcing packaging or model preparation. No existing active CIME or DATM cases are changed automatically. The user has approved the *18 precise meteorological replacements* and acceptance of their boundary risks. ERA5 source LST/UTC offset and half-hour sampling conventions remain provisional and should be documented before an actual model run; do not claim this script independently resolved them.

**Other QC:** Stage80 does not clear unrelated Stage75 P1/P2 temperature-review issues or retroactively convert the entire Batch01 forcing into production-validated meteorology. It finalizes the exact RH-related human decision and outputs the selected reproducible candidates for the next workflow.

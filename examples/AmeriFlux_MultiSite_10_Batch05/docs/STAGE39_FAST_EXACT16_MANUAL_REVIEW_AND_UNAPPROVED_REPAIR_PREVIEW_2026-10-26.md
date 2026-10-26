# AmeriFlux Batch05 — Stage38 REAL PASS, Stage39 isolate exactly 16 favourable method×episode options

## Stage38 actual IRIDIS6 operator outcome (2026-10-26)

- `STAGE38 SOURCE VERIFIED` and Python self-test passed; Stage38 reported `SUCCESS`. Source input report `/home/ly3n24/ameriflux_batch05_stage38/fast_closeout_20261026T173610Z_1368437`.
- Exact original P2/P3 universe: **1,574 native HH, 483 original events, all 10 sites**. Site original P2/P3 native counts: US-UiD 0; US-UMB 23; US-UMd 15; US-Var 62; US-Vcm 362; US-Vcp 626; US-WCr 62; US-Whs 1; US-Wjs 401; US-Wkg 22. **Zero formal forcing science complete passes** — UiD 0 P2/P3 alone is not a complete meteorological/forcing pass.
- Successfully source ZIP native-T/VPD/QC verified US-UMd 15, US-Var 62, US-WCr 62, US-Whs 1, US-Wkg 22, US-Vcp 626. US-UMB original FLUXMET_HH source still fails to match archive naming under its site directory; site explicitly `ORIGINAL_SOURCE_UNVERIFIED_SITE_HOLD` (13 source ZIP/CSV candidate files).
- US-Vcm and US-Wjs were not examined by Stage38 full-episode programme; their 362 and 401 original P2/P3 source HH remain unapproved.
- Stage38 source-verified **669 method×episode** scientific research tests: 224 `MISSING_SOURCE_METHOD_RH`, 114 `NEIGHBOR_UNAPPROVED_OR_NONMEASURED`, 125 `NEW_JUMP_GT2`, 190 `NEW_SEVERE_JUMP_GT4`, **16 `NUMERIC_CANDIDATE_REVIEW_NO_SCIENCE_APPROVAL`**. **These are METHOD×EPISODE tests, NOT counts of source HH.** 1,564 rows of research-only native candidate metadata across suitable full-event methods, not 1,564 approved or unique source HH.
- Single-method ERA reviews by site in Stage38: US-Var 3, US-WCr 1, US-Wkg 2, US-Vcp 9; zero US-UMd and US-Whs. Total of 16 favourable tests may include another method in addition to these 15 ERA tests, and some tests may concern the same underlying episode; Stage39 identifies exactly which rather than guessing.
- Existing approved Stage24 166 native overlay, all 46 human P1 HOLD, 10 suspect saturation-platform HH, and original 1574 P2/P3 remain unchanged. No original FLUXMET/DATM/CIME/Slurm writes.

## Stage39 GitHub source

[Stage39 code](../scripts/stage39/39_fast_16_event_shortlist_safe_trial_and_US_UMB_source_inventory.py), pinned commit `b3e311dcdd9e8efd1d40e6e8ac44315794eb7308`, blob SHA `72e9e146799dd550788f8ca8055395a5081dd116`.

[Stage39 one-click IRIDIS6 launcher](../scripts/stage39/run_stage39_iridis6.sh), pinned commit `344087ccb071896f2c77acc6d7cd2cb1189f61e8`, blob SHA `0447676b49a2cba4bcc97465b372a33519fb3ecb`.

This stage takes the 669 actual Stage38 method-event records, the complete original 1,574 Stage27 native P2/P3 source/QC population, Stage24 approved and manual/HOLD and saturation status, and the original Stage38 1,564 research-only candidate-native rows. It requires exactly 16 favourable event-method pairs, all with physical, contiguous source-native times and zero newly created >2/>4 hPa original event internal/external VPD jumps, preserving original QC0. Full original native source TA/VPD/QC and water-saturation candidate VPD are checked numerically. **Zero source science approvals**.

It produces:

- `stage39_EXACT16_ORIGINAL_EVENT_METHOD_REVIEW.csv`: **exact source site, event ID, original native time range, method, HH count, max/mean proposed VPD difference and method ambiguity flag**. This is the information the user needs to make *event-level*, not 1574 single-record, decisions.
- `stage39_ISOLATED_SINGLE_METHOD_NATIVE_RESEARCH_PREVIEW_NOT_FORCING.csv`: new research-only native-row VPD draft, **only for original episodes with exactly one passing method**; duplicate favourable methods in same episode remain HOLD. For every row: status `UNAPPROVED_ISOLATED_EXPERIMENT_NOT_DATM`, `manual_science_approval=NOT_GRANTED`, `DATM_forcing_authorized=NO`. It does not merge with or modify Stage24 approved166. This is not a production forcing overlay.
- `stage39_ALL10_SITE_NEXT_ACTIONS.csv`: current original P2/P3 counts, shortlisted event counts, research HH and site statuses.
- `stage39_US_UMB_READONLY_REAL_FILE_AND_ZIP_MEMBER_INVENTORY.csv`: names/sizes/SHA of actual source-site ZIP/CSV candidates, exact ZIP central member filenames containing original FLUXMET_HH metadata, or explanation that standard source is not yet present. No guessed source, no output under original source directories.
- `STAGE39_SHORTLIST_MANUAL_DECISIONS_AND_NEXT_ACTIONS.md`: one screen-friendly prioritised report; `stage39_manifest.json`: original SHA input chain and zero-write status.

### Copy/paste 3-line IRIDIS6

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/344087ccb071896f2c77acc6d7cd2cb1189f61e8/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage39/run_stage39_iridis6.sh" -o "$HOME/run_stage39.sh"
test "$(git hash-object "$HOME/run_stage39.sh")" = "0447676b49a2cba4bcc97465b372a33519fb3ecb"
bash "$HOME/run_stage39.sh"
```

**GitHub script committed; awaiting operator IRIDIS6 execution.** No claim that the 16 have already been approved, that any Batch05 station is forcing-ready, or that US-UMB source data have been recovered. Continue only after the source verification.

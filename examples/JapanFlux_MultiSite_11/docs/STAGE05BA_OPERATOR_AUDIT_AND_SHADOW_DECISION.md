# Stage05BA: actual batch audit, shadow package and review decisions

## What was received and what was created

The operator pasted three Stage05AZ outputs from `/home/ly3n24/japanflux_stage05az/run_20261103T073924Z_2301092`: 38 group/scenario rows, 99 candidate/scenario rows and 1,936 background pairs. Their reported SHA256s were `ed5597796982bafd86a253f670870e90ebabb67212706b0f185d6ee147e7cd61`, `e7b3ca99f28e27e7b0a508697c607241767d238548dc3405f9231620737be785`, and `6ff971ca857be54cc9eff1253087cc3179b19a53f2215672bced6e865a9b199b` respectively. The pasted text SHA256 is `bd96cc5f0d80fe440c2db3540a8492d75c2641b8ee7bf95b810765f64925a26c`. These remote output hashes were printed by the operator; they were not independently recomputed from IRIDIS6 here. **The pasted excerpt begins at the group table and omits the execution log and summary_HOLD.json**, so its individual source-ZIP gate attestations cannot be independently inspected in this review. The committed Stage05AZ code is designed to require those gates before writing the tables; do not claim to have seen an omitted terminal PASS.

The Stage05BA local processor combined the above paste with the previously supplied 45-field Stage05AW and 1,677-row Stage05AY window pastes. It independently reconstructed each of the 17 full-group bridge shadows, checked source F/ERA QC2 flags, unflagged QC2 endpoints, exact 45-field key/value join and Stage05AW envelope bounds, and checked candidate/grid and candidate/background arithmetic. It created **a separate local, unapproved shadow ledger** and a **1,677-row window preview**, not a complete source release or forcing. The preview keeps the original F column and uses a separate shadow F column: 45 flagged fields differ and the other 1,632 F strings are identical to the input excerpt. Co-variable columns remain original source values and should not be interpreted as a fully patched multivariate forcing. All 45 shadow records are `HOLD_NO_APPROVED_REPLACEMENT`.

The locally generated artifacts (not uploaded as original data to GitHub) have SHA256: `shadow_45_NOT_APPROVED.tsv` = `35f9f064983bec73c16fac44a8259093ffa7ec36f23caa4b28c93e44113677f2`; `shadow_window_preview_NOT_FORCING.tsv` = `81eaab3abff605991fe3fe1321eabea740279b8c09f629ce2aa664670953d8a7`; `group_review_HOLD.tsv` = `6fe0969e0ed1ecbdb9e8dd8ff55eb148b5dd343b637ec7de6de11e07cf01bb6b`.

## Automatic versus manual decision

No production repair is scientifically approved. For the UTC+9 diagnostic alignment, all **897** matched clean background pairs in the pasted result are source-QC2/ERA-derived; none is an independent selected-QC0 measurement in this matched, ±2 h-excluded subset. This is not a claim that no QC0 exists elsewhere. A smooth same-source bridge and consistency with the same-source background cannot establish tower truth. The independent reference is hourly grid context with unverified grid elevation, not a tower half-hour. A blanket production change would exceed the user's existing restriction on production forcing and the existing evidence.

The evidence supports automatically **preparing**, not approving, the 45 full-group continuity shadows. All 17 groups require scientific review. Seven Tef/Tmd groups (18 fields) additionally have the explicit solar-versus-JST source-clock conflict; ten groups (27 fields) have source-standard-time provenance but still lack paired QC0 validation in this comparison. Whether a source/grid residual lies within the observed background range is only an exploratory descriptive screen, not a statistical threshold or repair approval.

| Site | Variable / group start, native | Flags | QC2 paired background n | Median source−grid | Candidate residuals outside observed background range |
|---|---|---:|---:|---:|---:|
| Fjy | PA 2005-08-12 02:30 | 3 | 35 | +1.292 kPa | 2 |
| Fjy | PA 2011-12-17 06:30 | 3 | 83 | +1.581 kPa | 0 |
| Khw | LW 2005-08-12 02:00 | 2 | 38 | +12.73 W m⁻² | 0 |
| Khw | PA 2005-08-12 02:30 | 3 | 35 | −0.0066 kPa | 0 |
| Khw | PA 2011-12-17 06:30 | 3 | 83 | −0.0036 kPa | 0 |
| Khw | TA 2005-08-12 02:30 | 3 | 35 | +0.834 °C | 0 |
| Yms | LW 2005-08-12 02:00 | 2 | 38 | +8.46 W m⁻² | 0 |
| Yms | LW 2011-12-17 06:00 | 2 | 84 | +24.17 W m⁻² | 0 |
| Yms | PA 2005-08-12 02:30 | 3 | 35 | −0.649 kPa | 0 |
| Yms | PA 2011-12-17 06:30 | 3 | 83 | −0.995 kPa | 0 |
| Tef | LW 2011-12-17 06:00 | 2 | 84 | −12.39 W m⁻² | 0 |
| Tef | LW 2022-04-09 02:00 | 2 | 38 | −25.24 W m⁻² | 0 |
| Tmd | LW 2005-08-12 02:00 | 2 | 38 | +6.34 W m⁻² | 0 |
| Tmd | PA 2005-08-12 02:30 | 3 | 35 | −0.678 kPa | 0 |
| Tmd | PA 2011-12-17 06:30 | 3 | 83 | −0.735 kPa | 0 |
| Tmd | PA 2022-04-09 02:30 | 3 | 35 | −0.776 kPa | 1 |
| Tmd | TA 2005-08-12 02:30 | 3 | 35 | +0.078 °C | 0 |

Three candidate residuals, two in Fjy 2005 PA and one in Tmd 2022 PA, are just outside their observed QC2 background minima/maxima. These are review priorities, not automatic rejection or statistical anomalies; the background records overlap in time and are not independent measurements. The other 42 being within an observed background range does not certify them. Tef/Tmd clock, elevation/representativeness, MDS quality and longwave hour/half-hour mismatch remain separate review questions.

## Clock scenario label correction

The original `aa0e0e...` Stage05AZ output computed the longitude-based offsets correctly (Tef 568.428488 min, Tmd 566.092588 min) and used those values in the numerical calculation. Its conditional label compared minutes with longitude in degrees, so those two offset rows were erroneously labelled `HYPOTHETICAL_FIXED_OFFSET_SENSITIVITY` instead of `LOCAL_MEAN_SOLAR_LONGITUDE_DIAGNOSTIC_NOT_PROVEN`. The numeric grid matching was not altered by that label bug. The code is fixed and tested; retain the original outputs unchanged and interpret their numerical offsets with the corrected labels. Mean solar time itself remains a hypothesis, not source-clock proof.

## Remaining evidence before any production approval

Resolve the Tef/Tmd clock with the original publisher or a defensible documented alternative; identify ERA5-Land grid elevation and assess station/grid representativeness; obtain independent QC0 or another validated independent check where feasible; compare the bridge and reference-assisted scenarios with held-out errors appropriate to each variable; explicitly review the three background-range flags and all longwave interval/variability limitations. Only an evidence-backed, per-field scientific decision and explicit authorization can move a value out of HOLD. None has been granted here. No source ZIP, production forcing, PFT, model case, Slurm or AD400 was modified.

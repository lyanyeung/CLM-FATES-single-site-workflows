# Stage70 — First paired temperature–moisture sensitivity alternatives for CA-Man

**Stage69 verified Stage68's first 19 shadow temperature edits across all 262,800 forcing rows.** The original forcing was unchanged and the complete >10°C / 30 min temperature-step count declined from 185 to 150 (35 local flagged jumps removed). But **all 19 edits failed the independent science-approval gate**: 16 yielded RH changes of at least 25 percentage points, three produced RH below 20%, and 15 changed VPD by at least 10 hPa. The 15 other short, QC0-bounded CA-Man QC1 episodes rejected by Stage68's fixed-Q physical test also remain unchanged.

The next scientific question is not whether a temperature trace can be numerically smoothed, but **what measured humidity variable should be preserved when TA changes**. The pinned `70_compare_CA_Man_joint_T_Q_hypotheses.py` runs **only a report-level sensitivity comparison** on all 34 bounded QC1 episodes and uses the original Stage58-pinned CA-Man forcing SHA256. It reproduces the Stage68 19/15 screening, checks the Stage68/Stage69 manifests/ledger, and reports three scenarios at each candidate half-hour:

1. `FIXED_QBOT`: adjust temperature, leave original specific humidity unchanged, derive RH and VPD — Stage68 baseline, which can yield drastic RH/VPD changes.
2. `PRESERVE_ORIGINAL_RH`: adjust T and compute the specific humidity needed to retain the *original implied* RH. This is a **numerical hypothesis, not an observed RH measurement**. Large QBOT changes are reported, not automatically approved.
3. `PRESERVE_ORIGINAL_VPD`: adjust T and compute the specific humidity needed to retain the original VPD. Reject any required vapor pressure that is nonphysical at the candidate temperature.

All estimates use (e=q(p/100)/(0.622+0.378q)), (e_s(T)=6.112exp(17.67T/(T+243.5))) (hPa), and the inverse (q=0.622e/(p/100-0.378e)). `PSRF` stays fixed. Optional `source_FLUXMET_VPD_F` and `source_ERA5_VPD_ERA` are **contextual provisional source comparisons, not independent verified humidity truth**.

Modes:
- `--self-test`: synthetic water-vapor formula/inverse and physically impossible cold-temperature VPD check, no HPC data.
- `--check`: joins the exact Stage59, 61, 64, 67, 68 and 69 report directories; SHA-checks the pinned original and Stage68 source script; reproduces 19/15 and prints scenario counts; **no writes**.
- `--audit`: creates only a timestamped `reports/stage70_CA-Man_T_Q_hypotheses_*` directory containing the full counterfactual scenario ledger and three scenario-specific CSVs. **No new forcing is generated or edited.**

**Decision gate:** To select scientifically supportable coupled TA–QBOT changes, first verify clock conventions, original tower air temperature and independent humidity (RH/dewpoint/VPD) observations or credible auxiliary station evidence. Neither preserving an implied original RH nor preserving an implied original VPD is itself grounds for a repair. The original Stage68 shadow forcing must remain a non-production sensitivity experiment. Do not run a production spin-up or automatically modify QBOT.

Other unresolved cases: 13 US-Bar QC0→QC1 gaps, its 2015-11-06 native QC0 sensor jump, 14 time-ambiguous P1 episodes, ten currently unavailable BASE event sources, 15 Stage68 fixed-Q rejected cases, remaining P2 temperature episodes, and 17 low-RH science holds.

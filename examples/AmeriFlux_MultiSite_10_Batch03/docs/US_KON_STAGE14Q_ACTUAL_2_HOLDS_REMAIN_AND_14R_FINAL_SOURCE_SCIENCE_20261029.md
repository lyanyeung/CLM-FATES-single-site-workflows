# US-Kon — ACTUAL Stage14Q 2/2 group PASS, last two original science holds, Stage14R proposal (2026-10-29 ~07:08 UTC)

## Actual operator Stage14Q run

All source syntax/self tests passed; two exact original-QC source groups PASS native physical/thermodynamic and full group 30min checks. New separate SHA-receipted **research-only** selected 280320 2004–2019 NOLEAP source (original Stage14Q inputs not modified):

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_14Q_two_remaining_bounded_humidity_research_20261029T070830Z_ffcea3a8
```

Signed Stage14Q full-tape parent Stage14P SHA256 `c6fb133de59dd93bce5a944f272de5c4f9235dc98e44ca207f894ac88c9bc933`.

| Stage14Q episode | Accepted original source VPD QC1 native HH | Newly filled original HOLD | Extra finite original QC1 VPD revised | Original QC1 temperature corrected | Maximum 30-min ΔVPD | Max ΔRH | Max ΔQBOT | Max ΔTA | |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2011-10-15 07:30 | 1 | 1 | 0 | 0 | 1.904160 hPa | 8.09366 pp | 0.00045985 kg/kg | 1.933°C | **PASS**, but ONLY source QC1 RH endpoints |
| 2012-08-05 09:00–11:00 | 5 | 1 | 4 | 4 | 1.586725 hPa | 1.63099 pp | 0.00013287 kg/kg | 0.890°C | **PASS**, true tower paired QC0 RH endpoints |
| **Combined** | **6** | **2** | **4** | **4** | | | | | Original QC0 unchanged |

Most important caveat: Oct15 source 07:00 and 08:00 humidity grades are **both QC1**, not independent measured RH; interpolated 07:30 RH41.49985%, VPD6.42084hPa, QBOT0.00293. Aug05 true-QC0-bracketed RH and source T interpolation is much better supported, though still inferred not observed at candidate source hours.

The entire selected science source original 77 missing was rebuilt by Stage14K 68, Stage14P 5, Stage14Q 2; **two exact remaining original humidity HOLDs**:
- **201105261100**, original TA_F **16.777°C QC0**, VPD_F **20.573 hPa QC1**; FLUXNET companion ERA RH **50.034%**, independent downloadable original ERA5-Land RH **49.218%**. Prior 09:00/09:30/10:00/10:30 T original QC1 **24.379,25.909,25.825,22.709°C** versus grid original T2m ~**15.326,15.954,16.575,17.188°C**. Previously selected 11:30 original T QC0 17.311°C with VPD_USE10.049hPa, versus raw VPD QC1 20.764hPa. Single center repair would create large jumps with original QC1 neighbourhood.
- **201109291830**, original TA_F **15.617°C QC1** and original VPD_F **19.933 hPa QC2**; companion ERA at that half-hour TA_ERA **21.991°C** and VPD_ERA **19.933hPa**, inferred companion ERA RH **24.536%**; independent grid ERA5-Land T2m **19.956°C**, dewpoint **-0.740°C**, RH **24.851%**. Source VPD QC2 across a connected native period represents *absolute grid VPD*, not same-RH at original tower temperature. Local original measured T QC0 at 17:00=21.687, 18:00=19.133, 19:00=16.343°C; the original 17:30 and 18:30 temperatures are QC1 and can be tested via immediate QC0 interpolation, without altering any measured T.

## Next LAST combined TWO-GROUP experiment — Stage14R, not yet executed on IRIDIS6

Pinned [Stage14R final two original source episodes + FLUXNET companion ERA and verified ERA5-Land research-only sensitivity](../scripts/stage14/14r_US_Kon_final_two_connected_dual_ERA_sensitivity.py), source commit `30750b7e2264ab0688236cc0635b1d084ebabeec`, Git blob `c454ffedc4eac7aafe2e6e75cc54a4a037d7f7a0`.

Design rules: independently SHA-check original Stage14Q 280320 native source with **exactly two** held NaNs; original Stage07 published primary FLUXMET and companion ERA source SHA; original Stage14O (same successfully used `$HOME/US_Kon_nine_tower_ERA5Land_pm2h.py`, exact Git blob `dabc868924ec46a5a2905ad3505a100fd1974e52`) loads actual previously downloaded/shasigned point-year ERA5-Land ZIP 2011. Original BIF UTC−6 native midpoint mapping. **No new CDS download**.

- May26 method: derive native ERA5-Land RH from original T2m/dewpoint; recompute selected VPD/QBOT at source selected temperature, using validated ERA5-Land T2m **only for original T QC1** from 09:00–10:30 and possibly at most 12 additional earlier source QC1/2 VPD records if the LEFT 30min contact fails; original measured 11:00 T QC0 remains. Cross-check independently downloaded grid RH against paired source ERA RH; stop source group if difference >15pp or if encountered original VPD QC0 or an unexplained prior source-T edit. Do not touch existing selected 11:30 value or T QC0.
- Sep29 method: in a **bounded original 17:00–20:00 source-VPD-QC2 connected group**, transfer FLUXNET companion ERA RH to unchanged original tower T QC0 (rather than copying ERA absolute VPD); interpolate **only** original T-QC1 at 17:30/18:30 using immediate measured original QC0 T anchors. Keep other original QC1 T only if physical and provenance supported. Independently cross-compare against downloaded ERA5-Land RH at every native halfhour (≤15 percentage points). Source QC2 original selected VPD had a few earlier research-only overrides; edits occur **only in a separate new sensitivity copy**, and source/parent Stage14Q remain immutable.
- Both groups **transactional**: every 30min adjacent interior and BOTH exterior source joins must meet VPD jump ≤4hPa, RH jump ≤20pp, QBOT jump ≤0.003kg/kg, T jump ≤4°C and water/ice/QBOT physics. No original measured T/VPD QC0 fields changed. Failed group stays identical to parent; one group may PASS while the other stays HOLD. Print entire source/numerical/compare ledger and all contact warnings. User may review, no model job run.

**DO NOT state 0 missing before actual HPC Stage14R run.** Even a successful 0-NaN isolated research version would still not be scientific source approval or Post-v5/DATM/AD400 readiness; it would only complete the numerical forcing candidates. Residual VPD QC1/QC2 discontinuities outside these two episodes and PFT/site model checks still require their own gate.

```bash
(
  set -euo pipefail
  SCRIPT="$HOME/US_Kon_final_two_ERA_connected.py"
  READER="$HOME/US_Kon_nine_tower_ERA5Land_pm2h.py"

  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/30c4f7d3acdfe3df642ec83af756c67ebc547874/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14o_US_Kon_FINAL_nine_original_tower_ERA5Land_pm2h_READONLY.py" -o "$READER"
  test "$(git hash-object "$READER")" = "dabc868924ec46a5a2905ad3505a100fd1974e52"

  curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/30750b7e2264ab0688236cc0635b1d084ebabeec/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14r_US_Kon_final_two_connected_dual_ERA_sensitivity.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "c454ffedc4eac7aafe2e6e75cc54a4a037d7f7a0"
  python3 -B -c 'import pathlib,sys;p=pathlib.Path(sys.argv[1]);compile(p.read_text(),str(p),"exec");print("SYNTAX PASS")' "$SCRIPT"
  python3 -B "$SCRIPT" --run 2>&1 | tee "$HOME/US_Kon_final_two_ERA_connected.log"
)
```

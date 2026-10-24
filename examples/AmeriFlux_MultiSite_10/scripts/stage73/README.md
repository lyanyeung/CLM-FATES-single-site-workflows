# Stage73 — source-coherent ERA thermodynamics audit for CA-Man

## Mandatory policy: `TA_ERA + VPD_ERA + PA_ERA` from the SAME `ERA5_HH` record

The [root README's required source-consistency rule](../../../../README.md) governs this and all future workflows. This stage **does not carry forward Stage72's fixed original `QBOT`**; it computes vapor pressure, RH, dew point, and specific humidity from the same raw product, observation-time key, and pressure source, otherwise HOLD.

- Raw FLUXNET `ERA5_HH` columns: `TA_ERA` in **°C**, `VPD_ERA` in **hPa**, `PA_ERA` in **kPa** (source: [FLUXNET FULLSET variable definitions](https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/)).
- For each of the 35 previously flagged isolated CA-Man QC1 temperature events, preserve the **exact provisional raw timestamp** recorded in Stage61's source context; fetch `TA_ERA`, `VPD_ERA` and `PA_ERA` from **one ERA5_HH CSV row**. Do not use original forcing `QBOT`, `VPD_USE`, or `PSRF` as inputs to the alternative's humidity state.
- Equations, `e_s(T)=6.112 exp(17.67 T/(T+243.5))` hPa; `e=e_s(T)-VPD_ERA` hPa; `RH=100 e/e_s`%; `q=0.622 e/(10 PA_ERA-0.378 e)` kg/kg, where `PA_ERA` is kPa; `p=1000 PA_ERA` Pa; dew point is inverted from `e`. Test numerical closure with `q` and `p`. This analysis uses saturation over liquid water; for subfreezing temperatures, the ice/water convention must be reviewed before any scientific approval.
- If `PA_ERA` is absent/missing, or if the resulting vapor pressure is nonpositive or greater than saturation, mark **HOLD**. The script has **no fallback** to the tower's original `QBOT` or `PSRF` as a supposed same-source repair.
- The ERA values can be independently downscaled/regressed variable-by-variable against tower data; "same source row" does **not** guarantee an independent, scientifically exact joint atmospheric state. QC0 neighbor comparison only measures plausibility/continuity, not truth.
- Source timestamps and offset are **provisional**, as explicitly recorded by Stage61. Therefore **all 35 remain science HOLD**, even if thermodynamic checks pass.
- `--self-test` verifies calculations; `--check` is read-only and lists all 35 same-source thermodynamic candidates and reasons for HOLD; `--audit` writes **only a new CSV review report**, not a shadow forcing or repaired product.

### Why Stage72 remains sensitivity-only

Stage72 retained original `QBOT` when replacing `TA` with the FLUXNET ERA reference: 20/35 substitutions fell within broad physical limits but had large RH/VPD changes; 15/35 failed basic physical constraints. The existing Stage72 shadow was a *mixed-source stress test*, **not a coupled meteorological correction**, and must not be copied into a model production pipeline.

### Safe execution on IRIDIS6

```bash
SCRIPT="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10/scripts/stage73/73_CA_Man_same_source_ERA_T_VPD_PA_audit.py"
python3 -B "$SCRIPT" --self-test
python3 -B "$SCRIPT" --check
python3 -B "$SCRIPT" --audit
```

Run only with the exact reviewed script; the original forcing, QC0, DATM, CIME, PFT, Slurm, and historical experiments are unaffected.

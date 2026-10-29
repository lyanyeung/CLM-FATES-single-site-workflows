# US-Me6 / US-NR1: Claude handback, 2026-10-29

**Scope.** This handback covers the two handoffs:
- `US_ME6_CLAUDE_DIFFICULT_SITE_HANDOFF_20261029.md`
- `US_NR1_CLAUDE_DIFFICULT_SITE_HANDOFF_20261029.md`

The user approved every decision below. Both outputs are **research shadows only**. Each carries the `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP` marker; DATM, Post-v5, CIME and spin-up need a separate user decision.

No original FLUXMET, ERA or BASE file was changed, and no job was submitted. No other site was touched.

## Outputs

| Site | Research shadow (under `experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/`) | Rows | Period | Filled HH | NaN |
| --- | --- | --- | --- | --- | --- |
| US-Me6 | `cl03_US-Me6_research_shadow_20261029T044209Z_6513e2db` | 280320 | 2010-01-01 → 2025-12-31 | 45 | 0 |
| US-NR1 | `cl03_US-NR1_research_shadow_20261029T044240Z_88750f74` | 473040 | **1999-01-01** → 2025-12-31 | 191 (+43 dropped with 1998) | 0 |

Input shadows (approved, read only):
- Me6: `stage13ai_…_0eaab8b2`
- NR1: `stage13p_…_6b3f07eb`

## Evidence chain

All scripts are under `scripts/claude/`. Each is pinned by Git blob to the one before it.

1. **CL01** (`200ac5f`):
   - ledger of every missing half-hour (HH), with the BASE multi-level evidence;
   - site-specific QC0 validation;
   - classes.

   Reports: `cl01_US-Me6_…_d5d8e181`, `cl01_US-NR1_…_7c92edb7`.
2. **CL02** (`3776753`):
   - side-by-side alternatives (CEC, EMP, SAT), validated by tower-T bin;
   - predeclared recommendation;
   - coverage audit;
   - ERA anomaly rows.

   Reports: `cl02_US-Me6_…_873b540f`, `cl02_US-NR1_…_89ce56f5`.
3. **CL03** (`718ab6f`):
   - validation of time interpolation;
   - final fill and research shadow.

## Final sources

| Source | Me6 | NR1 | Validation on site QC0 truth |
| --- | --- | --- | --- |
| MEASURED BASE RH transfer (NR1 RH_1_2_1 / RH_1_3_1) | 0 | 47 / 15 | MAE 0.28 / 0.50 hPa, all years pass |
| SOURCE_QC0_VPD_F_RESTORED | 0 | 3 | The row's own QC0 measurement |
| EMP: block-excluded QC0 RH climatology (month, 3-h block, T bin) | 27 | 36 (+4 `+T_REANALYSIS`) | Passes in the cold bins; ≤ −10 °C MAE 0.05–0.28 hPa |
| CEC: COMPANION_E capped at DATM saturation | 11 | 70 | Passes in its row's T bin |
| CEC_LOW_CONFIDENCE (former HOLD) | 7 | 16 | No method passes the 5–25 °C bin with a formable value (see below) |
| DROPPED_BEFORE_FORCING_START_1999 | 0 | 43 | Jan–Oct 1998 is 100 % ERA |

**The former HOLD rows (23).**
- Time interpolation of `e` between QC0 anchors validates very well:
  - 3-HH pseudo-gaps: MAE 0.18–0.23 hPa, and every T bin passes;
  - Me6: 16/16 years;
  - NR1: 28/28 years.
- None of the 23 rows has a QC0 anchor within 4 HH, however. Their neighbours are MDS/ERA-filled.
- They therefore took the predeclared fallback, `CEC_LOW_CONFIDENCE`.
- For NR1 2017-06-30 and 2021-06-21, CEC is moist (0.5–1.3 hPa) while EMP is dry (about 4 hPa). Measured 2 m RH on 2021-06-21 at 16:30 gives VPD 0.02 hPa, which supports the moist reading.

## Root causes

**Me6 winter, 2014-12-31 23:30 → 2015-01-01 08:30 (19 HH).**
- The tower temperature is −16.6 to −18 °C, confirmed by BASE 14 m.
- The ERA reanalysis is about 10 °C warmer, so its vapour pressure exceeds ice saturation at the tower temperature.
- EMP gives VPD 0.28–0.32 hPa, just below ice saturation (0.24–0.25 hPa).

**Me6 2017 summer.** The QC1 VPD values exceed saturation, which is physically impossible.

**NR1 1998.** The tower started in November 1998. See `US_NR1_FORCING_START_1999_DECISION_20261029.md`.

**NR1 2004-12-03 22:30–23:30.**
- The companion ERA record is corrupt: TA_ERA is −111.7, −216.8 and −111.8 °C, and PA is 30.9, −8.2 and 30.9 kPa.
- The source VPD_F is QC0 (3.19–3.45 hPa) and was restored.
- This is confirmed independently: interpolation gives 3.24–3.46 hPa, and 2 m RH gives 3.28–3.53 hPa.

**NR1 2001, 2009 and 2018–2021.** These are short QC1/QC2 VPD gaps where the companion e is negative or above saturation (2009-01-26: QC1 VPD above saturation at −10 to −14.5 °C).

## Preserved approved edits

CL03 proves that every non-gap row and every other column is bit-identical to the approved input shadow. The NR1 Stage12AF 2022-09-10 TA values were also checked by value.

## Read-only verification (for Codex)

Run this on IRIDIS. It reads only and writes nothing. It recomputes everything from the files and does not import CL01–CL03.

```bash
python3 - <<'PY'
import glob, hashlib, json, os, sys
import numpy as np, pandas as pd
R = os.environ.get("CL03_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
IN = {"US-Me6": ("stage13ai_Me6_20151111_0900_VPD_GT_ESphysically_invalid_QC1_SINGLE_RESEARCH_ONLY_20261028T193928Z_0eaab8b2",
                 "US-Me6_STAGE13AI_Run14_20151111_0900_physically_invalid_QC1_SINGLE_ONLY_NOLEAP.csv", None),
      "US-NR1": ("stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_20261026T223628Z_6b3f07eb",
                 "US-NR1_STAGE13P_APPROVED_2022_ERA_RH_AND_2004_PSRF_FLDS_RESEARCH_ONLY_NOLEAP.csv", 1999)}
TA_OK = {"US-NR1": {"2022-09-10 06:30:00": 1.241, "2022-09-10 07:30:00": 1.556666667, "2022-09-10 08:00:00": 1.393333333}}
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)
esw = lambda t: 6.112 * np.exp(17.67 * t / (t + 243.5))
q = lambda e, p: 0.622 * e * 100 / (p - 0.378 * e * 100)
def datm(t):
    tc = np.clip(t, -50, 50); f = lambda k: k[0] + tc*(k[1] + tc*(k[2] + tc*(k[3] + tc*(k[4] + tc*(k[5] + tc*k[6])))))
    return np.where(t < 0, f(B), f(A))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
bad = 0
def ok(c, msg):
    global bad
    print(("PASS " if c else "FAIL ") + msg); bad += (not c)
for site, (fold, csv, start) in IN.items():
    d = sorted(glob.glob(f"{R}/science_trials/cl03_{site}_research_shadow_*")); print(f"\n##### {site}")
    if not d: ok(False, "no CL03 folder"); continue
    d = d[-1]; print(d)
    rec = json.load(open(glob.glob(d + "/cl03_*_receipt.json")[0]))
    ok(all(sha(f"{d}/{n}") == h for n, h in rec["output_sha256"].items()), f"receipt SHA of {len(rec['output_sha256'])} files")
    ok(os.path.isfile(d + "/INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"), "INCOMPLETE marker present")
    s = pd.read_csv(f"{R}/science_trials/{fold}/{csv}", low_memory=False); o = pd.read_csv(f"{d}/{site}_CL03_RESEARCH_SHADOW_NOLEAP.csv", low_memory=False)
    ok(rec["input_shadow"]["shadow_sha256"] == sha(f"{R}/science_trials/{fold}/{csv}"), "input shadow SHA equals the one CL03 used")
    if start: s = s.loc[pd.to_datetime(s.time).dt.year >= start].reset_index(drop=True)
    ok(list(s.columns) == list(o.columns) and len(s) == len(o) and (s.time.values == o.time.values).all(), f"same columns/clock, {len(o)} rows, {o.time.iloc[0]} .. {o.time.iloc[-1]}")
    ok(int(o.drop(columns="time").isna().sum().sum()) == 0, "no NaN in any column")
    pv = pd.read_csv(d + "/CL03_change_provenance.csv", dtype={"native_key": str})
    k = pd.to_datetime(o.time).dt.strftime("%Y%m%d%H%M"); ch = k.isin(set(pv.native_key)).to_numpy()
    gap = (s.VPD_USE.isna() | s.QBOT.isna()).to_numpy()
    ok((ch == gap).all(), f"changed rows ({ch.sum()}) are exactly the input gaps ({gap.sum()})")
    for c in o.columns:
        a, b = s[c].to_numpy(), o[c].to_numpy(); same = (a == b) | (pd.isna(a) & pd.isna(b))
        if c in ("VPD_USE", "QBOT"): ok(same[~ch].all(), f"{c} bit-identical on all {(~ch).sum()} unchanged rows")
        elif not same.all(): ok(False, f"{c} changed")
    ok(True, "all other columns bit-identical")
    T, P, V, Q = (o[c].to_numpy(float) for c in ("TA_USE", "PSRF", "VPD_USE", "QBOT"))
    ok(np.allclose(q(esw(T[ch]) - V[ch], P[ch]), Q[ch], rtol=1e-8), "new QBOT = 0.622e/(p-0.378e), e = esw(TA_USE) - VPD_USE")
    ok((Q[ch] <= q(datm(T[ch]), P[ch]) + 1e-9).all() and (V[ch] >= -1e-9).all(), "new QBOT <= DATM saturation, VPD >= 0")
    if "TBOT" in o: ok(np.allclose(o.TBOT, o.TA_USE + 273.15, rtol=0, atol=1e-6), "TBOT = TA_USE + 273.15")
    for t, v in TA_OK.get(site, {}).items(): ok(abs(float(o.loc[o.time == t, "TA_USE"].iloc[0]) - v) < 1e-6, f"approved TA {t} = {v}")
    print(pv.source.value_counts().to_string())
print("\nVERIFY", "ALL PASS" if bad == 0 else f"{bad} FAIL")
PY
```

The last line must be `VERIFY ALL PASS`.

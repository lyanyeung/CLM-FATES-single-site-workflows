# US-NR3: Claude handback, 2026-10-29

**Scope and status.**
- US-NR3 only. This document follows `US_NR3_CLAUDE_SCIENTIFIC_HANDOFF_STAGE01_TO_STAGE05_20261029.md`.
- The user approved every recommendation of the Stage07/08 report on 2026-10-29: "按照你的建议" and "那就都按照你说的建议弄，ERA5-Land其实也是可以的".
- The outputs are **research shadows only**. They carry `INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP`.
- No original BASE, FLUXMET, ERA or Stage12G file was changed, and no job was submitted.

## Outputs

**Folder.** `science_trials/nr3_09_claude_research_shadow_20261029T063921Z_6fdb9945/`, built by `scripts/us_nr3_science/nr3_09_claude_research_shadow.py` (commit `980fdce`).

**Shadows.**

| Shadow | Rows | Changed HH | T changed | Gaps filled | NaN |
| --- | --- | --- | --- | --- | --- |
| MAIN `US-NR3_NR3_09_MAIN_RESEARCH_SHADOW_NOLEAP.csv` | 315,360 | 12,175 | 11,983 | **238 / 238** | 0 |
| SENSITIVITY `US-NR3_NR3_09_SENSITIVITY_DRY_QC2_SHADOW_NOLEAP.csv` | 315,360 | 75,116 | 11,983 | 238 / 238 | 0 |

**MAIN sources.**

| Label | In the 238 | Outside |
| --- | --- | --- |
| `MEASURED_PAIR_TSTAR_RH` (TA = humidity-corrected sonic T\*, e = BASE RH × esw(T\*)) | 43 (+1 capped) | 11,495 (+442 capped to DATM ice saturation) |
| `ERA5LAND_E` (e = esw(ERA5-Land d2m)) | 106 (+11 capped) | — |
| `EMP_CLIMATOLOGY` (leave-one-year-out QC0 RH × esw(TA_USE)) | 69 (+6 capped) | — |
| `TSONIC_SPIKE_REPLACEMENT+EMP_CLIMATOLOGY` (2011-11-29 13:30 and 14:00) | 2 | — |

**SENSITIVITY.** This is MAIN plus the same humidity rule, ERA5-Land first and then climatology, applied to every other `VPD_F_QC = 2` row with TA_USE < 0 °C: 62,941 rows. It quantifies the 1.449 hPa VPD-floor dry bias. It is not the main line.

**Evidence chain.** All steps are read-only except Stage09, and all are pinned.
- Stage07 (`07b8581`): mechanism, validation and classes.
- Stage08 (`11068aa`): alternatives and gap locations.
- Stage09 (`980fdce`): the shadow builder.
- Report: `US_NR3_CLAUDE_STAGE07_EVENT_DECISION_REPORT_20261029.md`.

## Known limitations (deliberately not hidden)

- **Temperature steps at measured-pair window edges.** There are 198 window edges; 123 have a temperature step above 3 °C, and the largest is 12.4 °C. They occur where ERA TA (QC2, cold-season MAE 4.2 °C) meets T\* (MAE 0.6 °C). The ERA side is the wrong one, but the step is a discontinuity in the forcing. The verifier below lists the largest steps.
- **ERA temperature elsewhere.** QC2 rows outside the measured-pair windows keep ERA TA. Their humidity is changed only in SENSITIVITY.
- **Sensor metadata.** No BASE-BADM workbook is available on IRIDIS, so the instrument history behind the 2017–2018 and 2023 losses is still unverified.
- **2021-05-31 06:30–09:30.** These MDS VPD rows (RH missing, then 99 % from 10:00) are not in the 238 and were not changed.
- **Downstream approval.** DATM / Post-v5 / CIME / spin-up need a separate approval. Use a QBOT (specific-humidity) stream, not RH: below 0 °C DATM interprets RH relative to ice.

## Read-only verification (for Codex)

Run this on IRIDIS. It reads only and is independent of the Stage07–09 code: T\* is recomputed from the original BASE.

```bash
python3 - <<'PY'
import glob, hashlib, json, os
import numpy as np, pandas as pd
R = os.environ.get("NR3_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE = os.environ.get("NR3_BASE", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv")
G = R + "/science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv"
SHA_G = os.environ.get("NR3_SHA_G", "b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f")
SHA_B = os.environ.get("NR3_SHA_B", "85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b")
esw = lambda t: 6.112 * np.exp(17.67 * t / (t + 243.5))
q = lambda e, p: 0.622 * e * 100 / (p - 0.378 * e * 100)
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)
def datm(t):
    tc = np.clip(t, -50, 50); f = lambda k: k[0] + tc*(k[1] + tc*(k[2] + tc*(k[3] + tc*(k[4] + tc*(k[5] + tc*k[6])))))
    return np.where(t < 0, f(B), f(A))
def tstar(ts, rh, pa):
    t = ts.copy()
    for _ in range(60): t = (ts + 273.15) / (1 + 0.51 * q(esw(t) * rh / 100, pa * 1000)) - 273.15
    return t
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
bad = 0
def ok(c, m):
    global bad; print(("PASS " if c else "FAIL ") + m); bad += (not c)
d = sorted(glob.glob(R + "/science_trials/nr3_09_claude_research_shadow_*"))[-1]; print(d)
rec = json.load(open(d + "/nr3_09_research_shadow_receipt.json"))
ok(all(sha(f"{d}/{n}") == h for n, h in rec["output_sha256"].items()), f"receipt SHA of {len(rec['output_sha256'])} files")
ok(os.path.isfile(d + "/INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"), "INCOMPLETE marker")
ok(sha(G) == SHA_G, "Stage12G input SHA unchanged"); ok(sha(BASE) == SHA_B, "BASE input SHA unchanged")
g = pd.read_csv(G, low_memory=False); key = pd.to_datetime(g.time.str.replace("T", " ")).dt.strftime("%Y%m%d%H%M").to_numpy()
gap = (g.VPD_USE.isna() | g.QBOT.isna()).to_numpy(); ok(gap.sum() == 238, f"Stage12G gaps {gap.sum()} == 238")
b = pd.read_csv(BASE, comment="#", usecols=["TIMESTAMP_START", "RH", "T_SONIC", "PA"], na_values=-9999, dtype={"TIMESTAMP_START": str}).set_index("TIMESTAMP_START")
for nm in ("MAIN", "SENSITIVITY"):
    print(f"\n##### {nm}")
    o = pd.read_csv(glob.glob(f"{d}/US-NR3_NR3_09_{nm}*_NOLEAP.csv")[0], low_memory=False)
    pv = pd.read_csv(f"{d}/NR3_09_{nm}_provenance.csv", dtype={"native_key": str})
    ok(list(o.columns) == list(g.columns) and len(o) == len(g) and (o.time.values == g.time.values).all(), f"same columns/clock, {len(o)} rows")
    ok(int(o.drop(columns="time").isna().sum().sum()) == 0, "no NaN in any column")
    ch = np.isin(key, pv.native_key.to_numpy()); ok(ch[gap].all(), "all 238 gaps are in the provenance")
    for c in g.columns:
        a, x = g[c].to_numpy(), o[c].to_numpy(); same = (a == x) | (pd.isna(a) & pd.isna(x))
        if c in ("TA_USE", "TBOT", "VPD_USE", "QBOT"):
            if not same[~ch].all(): ok(False, f"{c} changed outside provenance")
        elif not same.all(): ok(False, f"{c} changed")
    ok(True, f"untouched rows ({(~ch).sum()}) and other columns bit-identical (no FAIL above)")
    T, P, V, Q = (o[c].to_numpy(float) for c in ("TA_USE", "PSRF", "VPD_USE", "QBOT"))
    ok(np.allclose(q(esw(T[ch]) - V[ch], P[ch]), Q[ch], rtol=1e-8), "QBOT = 0.622e/(p-0.378e), e = esw(TA_USE) - VPD_USE")
    ok((Q[ch] <= q(datm(T[ch]), P[ch]) * (1 + 1e-9)).all() and (V[ch] >= -1e-9).all(), "QBOT <= DATM saturation, VPD >= 0")
    if "TBOT" in o: ok(np.allclose(o.TBOT, o.TA_USE + 273.15, rtol=0, atol=1e-6), "TBOT = TA_USE + 273.15")
    m = pv.loc[pv.label.str.startswith("MEASURED")].set_index("native_key"); bb = b.loc[m.index]
    ts = tstar(bb.T_SONIC.to_numpy(float), bb.RH.to_numpy(float), bb.PA.to_numpy(float))
    ok(np.allclose(ts, m.new_TA_USE.to_numpy(float), atol=1e-6), f"measured-pair TA_USE = T* recomputed from BASE ({len(m)} rows)")
    e_new = esw(m.new_TA_USE.to_numpy(float)) - m.new_VPD_USE.to_numpy(float)
    e_rh = np.minimum(bb.RH.to_numpy(float) / 100 * esw(ts), datm(ts))
    ok(np.allclose(e_new, e_rh, atol=1e-6), "measured-pair e = min(RH x esw(T*), DATM sat)")
    print(pv.label.value_counts().to_string())
    if nm == "MAIN":
        dT = np.abs(np.diff(T)); w = np.isin(key, m.index); edge = np.flatnonzero(np.diff(w.astype(int)) != 0)
        top = pd.DataFrame({"from": key[edge], "to": key[edge + 1], "TA_from": T[edge], "TA_to": T[edge + 1], "jump_C": dT[edge]}).sort_values("jump_C", ascending=False)
        print("window edges", len(edge), "| >3 C", int((top.jump_C > 3).sum()), "| largest:"); print(top.head(10).round(2).to_string(index=False))
print("\nVERIFY", "ALL PASS" if bad == 0 else f"{bad} FAIL")
PY
```

The last line must be `VERIFY ALL PASS`.

## Verification result (operator, 2026-10-29)

The independent verifier above was run on IRIDIS and returned **VERIFY ALL PASS** for both MAIN and SENSITIVITY. In detail:
- receipt SHA: 6 files;
- Stage12G and BASE inputs unchanged;
- 238/238 gaps filled, NaN 0;
- untouched rows bit-identical: 303,185 in MAIN, 240,244 in SENSITIVITY;
- QBOT closure holds and QBOT ≤ DATM saturation;
- TBOT = TA_USE + 273.15;
- for all 11,981 measured-pair rows, T\* recomputed from the original BASE matches.

**Edge steps.** The largest temperature steps are mostly **isolated ERA rows inside measured windows**, i.e. single half-hours where the BASE triplet is missing:
- 2017-02-26 00:30: ERA −24.66 °C between T\* −12.64 and −12.24 °C;
- 2016-12-08 06:30 and 07:30: ERA −28.08 and −27.65 °C between T\* ≈ −18.6 °C.

Filling such short holes (≤ 2 HH) by interpolating the measured pair (T\* and e) would remove most of these steps. This is a proposed follow-up and is not applied.

## Shadow v2: measured-window holes (user approved 2026-10-29 06:59)

**What v2 does.** `scripts/us_nr3_science/nr3_10_claude_shadow_v2_window_holes.py` fills runs of ≤ 2 HH (no BASE triplet) that sit inside measured-pair windows.
- Both T and e are linearly interpolated from the bounding measured T\* and e, and capped at DATM saturation.
- It is applied only if the 1–2 HH pseudo-hole validation gives Dec–Mar T MAE ≤ 0.5 °C and e MAE ≤ 0.10 hPa.
- All other rows are bit-identical to Stage09.

**Output.** One new folder, `science_trials/nr3_10_claude_research_shadow_v2_*`.

**Verification v2 (read-only).** This is the same verifier with the v2 folder and file names, plus a hole-interpolation check:

```bash
python3 - <<'PY'
import glob, hashlib, json, os
import numpy as np, pandas as pd
R = os.environ.get("NR3_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE = os.environ.get("NR3_BASE", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-NR3/forcing/raw/AMF_US-NR3_BASE_HH_6-5.csv")
G = R + "/science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f/US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv"
SHA_G = os.environ.get("NR3_SHA_G", "b16f81d125944c47cf6d1886d51461053091cd819cb3d5048cea49247bccc48f")
SHA_B = os.environ.get("NR3_SHA_B", "85db3e85463aaf300f326c0766f24c8a228b174f679968265e97b69bd619a35b")
esw = lambda t: 6.112 * np.exp(17.67 * t / (t + 243.5))
q = lambda e, p: 0.622 * e * 100 / (p - 0.378 * e * 100)
A = (6.107799961, 4.436518521e-01, 1.428945805e-02, 2.650648471e-04, 3.031240396e-06, 2.034080948e-08, 6.136820929e-11)
B = (6.109177956, 5.034698970e-01, 1.886013408e-02, 4.176223716e-04, 5.824720280e-06, 4.838803174e-08, 1.838826904e-10)
def datm(t):
    tc = np.clip(t, -50, 50); f = lambda k: k[0] + tc*(k[1] + tc*(k[2] + tc*(k[3] + tc*(k[4] + tc*(k[5] + tc*k[6])))))
    return np.where(t < 0, f(B), f(A))
def tstar(ts, rh, pa):
    t = ts.copy()
    for _ in range(60): t = (ts + 273.15) / (1 + 0.51 * q(esw(t) * rh / 100, pa * 1000)) - 273.15
    return t
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
bad = 0
def ok(c, m):
    global bad; print(("PASS " if c else "FAIL ") + m); bad += (not c)
d = sorted(glob.glob(R + "/science_trials/nr3_10_claude_research_shadow_v2_*"))[-1]; print(d)
rec = json.load(open(d + "/nr3_10_research_shadow_v2_receipt.json"))
ok(all(sha(f"{d}/{n}") == h for n, h in rec["output_sha256"].items()), f"receipt SHA of {len(rec['output_sha256'])} files")
ok(os.path.isfile(d + "/INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"), "INCOMPLETE marker")
ok(sha(G) == SHA_G, "Stage12G input SHA unchanged"); ok(sha(BASE) == SHA_B, "BASE input SHA unchanged")
g = pd.read_csv(G, low_memory=False); key = pd.to_datetime(g.time.str.replace("T", " ")).dt.strftime("%Y%m%d%H%M").to_numpy()
gap = (g.VPD_USE.isna() | g.QBOT.isna()).to_numpy(); ok(gap.sum() == 238, f"Stage12G gaps {gap.sum()} == 238")
b = pd.read_csv(BASE, comment="#", usecols=["TIMESTAMP_START", "RH", "T_SONIC", "PA"], na_values=-9999, dtype={"TIMESTAMP_START": str}).set_index("TIMESTAMP_START")
for nm in ("MAIN", "SENSITIVITY"):
    print(f"\n##### {nm}")
    o = pd.read_csv(glob.glob(f"{d}/US-NR3_NR3_10_{nm}*_NOLEAP.csv")[0], low_memory=False)
    pv = pd.read_csv(f"{d}/NR3_10_{nm}_provenance.csv", dtype={"native_key": str})
    ok(list(o.columns) == list(g.columns) and len(o) == len(g) and (o.time.values == g.time.values).all(), f"same columns/clock, {len(o)} rows")
    ok(int(o.drop(columns="time").isna().sum().sum()) == 0, "no NaN in any column")
    ch = np.isin(key, pv.native_key.to_numpy()); ok(ch[gap].all(), "all 238 gaps are in the provenance")
    for c in g.columns:
        a, x = g[c].to_numpy(), o[c].to_numpy(); same = (a == x) | (pd.isna(a) & pd.isna(x))
        if c in ("TA_USE", "TBOT", "VPD_USE", "QBOT"):
            if not same[~ch].all(): ok(False, f"{c} changed outside provenance")
        elif not same.all(): ok(False, f"{c} changed")
    ok(True, f"untouched rows ({(~ch).sum()}) and other columns bit-identical (no FAIL above)")
    T, P, V, Q = (o[c].to_numpy(float) for c in ("TA_USE", "PSRF", "VPD_USE", "QBOT"))
    ok(np.allclose(q(esw(T[ch]) - V[ch], P[ch]), Q[ch], rtol=1e-8), "QBOT = 0.622e/(p-0.378e), e = esw(TA_USE) - VPD_USE")
    ok((Q[ch] <= q(datm(T[ch]), P[ch]) * (1 + 1e-9)).all() and (V[ch] >= -1e-9).all(), "QBOT <= DATM saturation, VPD >= 0")
    if "TBOT" in o: ok(np.allclose(o.TBOT, o.TA_USE + 273.15, rtol=0, atol=1e-6), "TBOT = TA_USE + 273.15")
    m = pv.loc[pv.label.str.startswith("MEASURED")].set_index("native_key"); bb = b.loc[m.index]
    ts = tstar(bb.T_SONIC.to_numpy(float), bb.RH.to_numpy(float), bb.PA.to_numpy(float))
    ok(np.allclose(ts, m.new_TA_USE.to_numpy(float), atol=1e-6), f"measured-pair TA_USE = T* recomputed from BASE ({len(m)} rows)")
    e_new = esw(m.new_TA_USE.to_numpy(float)) - m.new_VPD_USE.to_numpy(float)
    e_rh = np.minimum(bb.RH.to_numpy(float) / 100 * esw(ts), datm(ts))
    ok(np.allclose(e_new, e_rh, atol=1e-6), "measured-pair e = min(RH x esw(T*), DATM sat)")
    hk = pv.loc[pv.label.str.contains("WINDOW_HOLE"), "native_key"].to_numpy()
    mi = np.flatnonzero(np.isin(key, m.index)); hi_ = np.flatnonzero(np.isin(key, hk)); okh = True
    for i in hi_:
        a_ = mi[mi < i].max(); b_ = mi[mi > i].min(); okh &= (b_ - a_ <= 3) and abs(T[i] - (T[a_] + (T[b_] - T[a_]) * (i - a_) / (b_ - a_))) < 1e-6
    ok(bool(okh), f"window-hole rows ({len(hi_)}) = linear interpolation of bounding measured T*, holes <= 2 HH")
    print(pv.label.value_counts().to_string())
    if nm == "MAIN":
        dT = np.abs(np.diff(T)); w = np.isin(key, m.index) | np.isin(key, hk); edge = np.flatnonzero(np.diff(w.astype(int)) != 0)
        top = pd.DataFrame({"from": key[edge], "to": key[edge + 1], "TA_from": T[edge], "TA_to": T[edge + 1], "jump_C": dT[edge]}).sort_values("jump_C", ascending=False)
        print("window edges", len(edge), "| >3 C", int((top.jump_C > 3).sum()), "| largest:"); print(top.head(10).round(2).to_string(index=False))
print("\nVERIFY", "ALL PASS" if bad == 0 else f"{bad} FAIL")
PY
```

### v2 result (operator run 2026-10-29 07:02), VERIFY ALL PASS

**Folder.** `science_trials/nr3_10_claude_research_shadow_v2_20261029T070254Z_63df7497`

**Gate.**
- 1–2 HH pseudo-holes in Dec–Mar (N 17,556): T MAE **0.175 °C**, e MAE **0.051 hPa**. The gate passed.
- All seasons: T MAE 0.18–0.23 °C, e MAE 0.08–0.10 hPa.

**Changes.**
- 84 holes, 97 rows. 4 of them are among the 238; 11 were capped to DATM saturation.
- Window edges dropped from 198 to 30. Steps above 3 °C dropped from 123 to **15**. The maximum step went from 12.42 to 10.18 °C.
- The largest remaining step, 2019-01-02 10:00, is a genuine window start: ERA −15.3 °C against T\* −5.1 °C.
- Example: 2016-12-08 07:30 changed from ERA −27.65 °C to −18.26 °C.

**Independent v2 verifier: ALL PASS** for both MAIN and SENSITIVITY.
- Untouched rows are bit-identical to Stage12G: 303,092 in MAIN, 240,240 in SENSITIVITY.
- All 11,981 measured-pair rows match T\* recomputed from BASE.
- All 97 hole rows equal the linear interpolation of the bounding T\*.

**Current recommended US-NR3 research input.** The v2 MAIN shadow. DATM / Post-v5 still need a separate user decision.

# Stage67 — Native BASE vs gap-filled FLUXMET temperature evidence crosswalk

Stage66 read-only results for the **60 targeted P1 event groups**:
- **CA-Man: 36 QC0→QC1 episodes**, BASE_HH has numeric temperature **only on the before side**. This is consistent with missing observed measurements needing gap-fill at the QC1 time and **is not proof of invalid filled values**.
- **US-Bar: 14 episodes**, native BASE channels have numerical before/after pairs; 13 differ from forcing/FLUXMET's step and 1 matches. In the **2015-11-06 20:00** QC0→QC0 event, the native BASE channel `TA_1_1_1` and FLUXMET/forcing both show **−39.877 °C/30 min** provisionally. That does **not** prove the sudden cooling was meteorologically genuine: it may be inherited from an original sensor/recording anomaly.
- **10 episodes across CA-Cbo, CA-TP1, CA-TP4, US-Aud** have no BASE ZIP in Stage65's checked original directories, not proof no original observations exist.

`67_resolve_native_vs_gapfill_temperature_evidence.py` joins the **exact** Stage63, Stage65 and Stage66 report paths, confirms Stage65→Stage66 file hashes, and compares *each native sensor channel separately* with candidate and FLUXMET before/current temperature. No channel is automatically selected as the correct instrument, and raw `TA_*_QC` labels are displayed without inventing their meaning.

Modes:
- `--self-test`: synthetic QC0 measured, QC0→QC1 before-only and missing-source tests; does not read experiment files.
- `--check --stage63-dir ... --stage65-dir ... --stage66-dir ...`: validation and concise all-14 US-Bar / CA-Man source-matching report. No output writes.
- `--audit`: identical input checks, then creates only a new `reports/stage67_native_temperature_crosswalk_<UTC>/` with per-event, per-sensor, US-Bar, CA-Man and missing BASE CSVs plus hashed manifest.

### Critical scientific HOLD

Native BASE exact timestamp matching is not an independent clock validation. BASE channel identity, measured sensor height and BADM provenance are still unverified. Values in BASE and FLUXMET may originate from **the same physical observation**; agreement alone does not independently validate weather authenticity. BASE sensor availability at a QC1 moment does not demonstrate that FLUXMET was wrong to reject or gap-fill it.

**Next science checks:** (1) US-Bar 14 native channels' `TA_*_QC`, instrument identity, temperature trajectory and original QC metadata, (2) CA-Man gapfill continuity relative to its last measured TA and adjacent temporal records, (3) original tower archive discovery for 10 missing-source episodes, (4) separately the 14 clock-ambiguous P1 groups and 17 RH<1% cases, (5) the remaining 184 P2 temperature episode groups. **No forcing replacements, production spin-up, or automatic scientific approval.**

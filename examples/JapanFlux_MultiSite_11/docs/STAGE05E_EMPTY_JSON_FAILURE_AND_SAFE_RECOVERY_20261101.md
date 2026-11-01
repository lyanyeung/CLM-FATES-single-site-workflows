# JapanFlux Stage05E: invalid saved JSON failure and non-destructive recovery (2026-11-01)

## Operator output

Operator ran Stage05D individually, serially and without Slurm for the six remaining JPF sites: `JP-Api JP-Fhk JP-Khw JP-Spp JP-Tak JP-Tmd`. Terminal output printed `AUDITING` for all six and returned to the shell. Subsequently the unpatched Stage05E aggregator crashed in `json.loads(f.read_text(...))` with:

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

This shows **at least one existing saved `JP-*_ERA5_audit.json` is empty or not valid JSON**. The user did **not** show which JSON failed, exact report sizes or independent Stage05D success checks for the six new files. Therefore it would be incorrect to mark these six sites `ERA5_FULL_SCAN_COMPLETED` solely from their `AUDITING` terminal lines or to claim all original sources were corrupted.

The earlier actual 3-site Stage05D results (`JP-Fjy`, `JP-Yms`, `JP-Tef`) are evidence of completed audits **at the time reported**, but the current filesystem report files must also be checked. A Python JSON parsing exception in a report aggregator is **not evidence of damage to original JPF ZIP packages or model runs**.

## Patch

[Stage05E](../scripts/stage05/05e_summarize_ERA5_audits_from_JSON_NO_ZIP_NO_SLURM.py) now has:

- `--check`: enumerates exact 9 expected per-site filenames, checks non-empty size, valid JSON object, `stage`, `site`, `status=ERA5_FULL_SCAN_COMPLETED`, `read_only=true`, positive integer `rows`, prints VALID/MISSING/EMPTY/INVALID and exits successfully for diagnosis.
- Default summary: detects invalid JSON **before** aggregating and gives a clear offending-site error; it does **not** silently treat corrupt reports as completed.
- `--ignore-invalid`: an **explicit** partial summary that labels invalid reports excluded; not scientific acceptance. Missing site JSON has been allowed in partial Stage05E since the original implementation.

## Recommended recovery (no Slurm)

1. Fetch the updated Stage05E from a pinned Git commit and run `--check`. Do not rescan original ZIPs until exact invalid site IDs are known.
2. If needed, rerun Stage05D for **only missing/invalid JSON** one site at a time, writing JSON to a temporary file. Validate the temporary file with `json.load`, verify stage/site/status and only then atomically move it to the expected report path. Do **not overwrite any valid JSON**.
3. Run Stage05E `--check` again and only claim 9/9 if it verifies 9 valid reports; then run `--events` and archive terminal output.
4. Do not use Slurm, alter tower or ERA original ZIP, repair an anomalous climate value, or submit AD400 as part of Stage05E recovery.

Cause of the incomplete JSON report has **not** been isolated; no speculative reason (job interruption, out-of-memory, wrong file location) should be promoted to verified diagnosis without the per-file check.

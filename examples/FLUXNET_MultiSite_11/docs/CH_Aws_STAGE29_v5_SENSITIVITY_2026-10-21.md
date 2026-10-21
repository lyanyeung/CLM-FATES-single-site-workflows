# CH-Aws Stage29 — 2014 reanalysis evidence and full-cycle v5 humidity sensitivity

**Status: code published; user-site execution and validation pending.** This is an exploratory 77-record forcing sensitivity, **not observational QC**, and no spin-up success is claimed.

Source scripts:

- [30_chaws_fetch_2014_reference.py](../scripts/stage29/30_chaws_fetch_2014_reference.py) verifies or fetches **2014-only** ERA5 and ERA5-Land hourly T/dew point references. Stores year-specific JSON in the previous Stage09 cache; refuses overwriting existing caches. Local station-clock mapping assumes UTC+1 standard time, without DST. The 2014 station-vs-grid/clock correspondence is a scientific caveat.
- [31_chaws_build_full_v5_sensitivity.py](../scripts/stage29/31_chaws_build_full_v5_sensitivity.py) has default `--audit` (read-only), `--write --acknowledge-reanalysis-uncertainty` (new output only), and `--verify` (read-only). It operates on the 77 `EUF_F` QC2 RH<10% half hours. It checks that ERA5-Land is wetter than existing values before any modification. If this is false for any record, it **aborts for manual review** rather than using a blind blanket replacement.
- Existing Stage28 v4 edits (nine half hours on 2006-01-14) are preserved in the independent 2006 output. All other variable values must match RH25A v3. Intended destination `datm_11_stage29_all77_rh_sensitivity_v5` consists of seven separately modified annual NetCDFs plus twelve links to unmodified RH25A v3 annual NetCDFs, **only if all preflight checks pass**. Symlinks require the v3 parent to remain accessible. Metadata must be read alongside the Stage29 ledger; historical v3/v4 attributes can refer to previous parent products.

## Run without git pull, checkout conflicts, or downloading scripts

On IRIDIS6 using the existing repository, fetch commits only (no working tree modification):

```bash
cd /iridisfs/home/ly3n24/CLM-FATES-single-site-workflows
git fetch origin main
P=examples/FLUXNET_MultiSite_11/scripts/stage29
PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python

git show "origin/main:$P/30_chaws_fetch_2014_reference.py" | "$PY" - --audit
git show "origin/main:$P/30_chaws_fetch_2014_reference.py" | "$PY" - --fetch
git show "origin/main:$P/31_chaws_build_full_v5_sensitivity.py" | "$PY" - --audit
```

If full preflight reports acceptable science assumptions and user specifically elects to build this exploratory sensitivity candidate:

```bash
git show "origin/main:$P/31_chaws_build_full_v5_sensitivity.py" | "$PY" - --write --acknowledge-reanalysis-uncertainty
git show "origin/main:$P/31_chaws_build_full_v5_sensitivity.py" | "$PY" - --verify
```

**Do not** change original Stage28 v4 / RH25A v3 directories, CIME cases, `ZBOT`, executable, or ongoing Slurm jobs. This candidate may still cause internally diagnosed negative 2 m RH: that remains subject to actual model-run confirmation after scientific review. No new Slurm diagnostic tests are provided.

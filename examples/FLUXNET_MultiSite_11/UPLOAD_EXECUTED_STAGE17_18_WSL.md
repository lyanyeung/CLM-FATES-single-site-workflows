# Preserving the EXACT Stage17/18 scripts used on IRIDIS6

The Stage17/18 scripts were prepared and executed on IRIDIS6 but their file bytes are **not yet committed to this directory**. The scientific and operational record is already published in [Stage17–18 notes](docs/SPINUP_1000YEAR_STAGE17_18_2026-10-15.md). Do **not** mistake a retyped or reconstructed script for the actually executed version.

From **WSL** (not IRIDIS6), follow this recipe to copy the exact scripts and commit them safely. It does not execute either spin-up script.

```bash
set -euo pipefail
REPO="$HOME/CLM-FATES-single-site-workflows"
if [[ -d "$REPO/.git" ]]; then
  git -C "$REPO" pull --ff-only
else
  git clone https://github.com/lyanyeung/CLM-FATES-single-site-workflows.git "$REPO"
fi
DST="$REPO/examples/FLUXNET_MultiSite_11/scripts"
mkdir -p "$DST/stage17" "$DST/stage18"
scp ly3n24@iridis6.soton.ac.uk:~/17_11site_spinup500_srun_pmix.sh "$DST/stage17/"
scp ly3n24@iridis6.soton.ac.uk:~/18_upgrade_prepared_11site_to_spinup1000_submit_all.sh "$DST/stage18/"
bash -n "$DST/stage17/17_11site_spinup500_srun_pmix.sh"
bash -n "$DST/stage18/18_upgrade_prepared_11site_to_spinup1000_submit_all.sh"
grep -n 'for comp in ATM LND CPL' "$DST/stage18/18_upgrade_prepared_11site_to_spinup1000_submit_all.sh" ||
  { echo "STOP: Stage18 historical shadowing fix absent, review before commit"; exit 1; }
cd "$REPO"
git status --short
git add examples/FLUXNET_MultiSite_11/scripts/stage17/17_11site_spinup500_srun_pmix.sh
git add examples/FLUXNET_MultiSite_11/scripts/stage18/18_upgrade_prepared_11site_to_spinup1000_submit_all.sh
git diff --cached --stat
git commit -m "archive: executed IRIDIS6 Stage17/18 11-site PMIx spin-up scripts"
git push origin main
```

**If an `scp` file is absent** do not silently use another local version. Find the saved script and inspect differences against the HOTFIX package first. If `git push` is rejected because the remote moved, run `git pull --rebase` with care; never `git push --force` to `main`.

For later CH-Aws diagnosis, original scripts and run logs should remain in IRIDIS6; copies of the diagnostic **code** (not licensed data) can be put into `scripts/chaws_archived/` by the same mechanism. The separate published [CH-Aws incident chronology](docs/CH_Aws_HUMIDITY_FAILURES_2026-10-15.md) enumerates Stage19–27 versions and exact scientific caveats.

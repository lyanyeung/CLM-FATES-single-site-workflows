# FLUXNET_MultiSite_8 restart — IRIDIS6

The companion script is `21_resume_eight_site_after_quota.py`. This is a checkpoint-safe recovery for the existing `*_FATES_SPINUP500` CIME cases. It does not start new model cases or overwrite the original science inputs. Its operations are **inspect** (read-only), **prepare SITE** (stages a backed-up checkpoint and resets CIME `RESUBMIT` to remaining segments minus one, no Slurm job submitted), and **submit SESSION** (one-shot job submission).

Targets from GitHub (18 October 2026): CZ-BK1, IT-Ren, FR-FBn, DE-Hzd, CH-Dav, BE-Vie, IT-Lav -> 1000 cumulative model years. FR-Hes -> 500 years, until its original run is complete. Latest **live** progress is not known; derive from IRIDIS6 archives, not dated GitHub diagnostics.

**Do not run** the older `09_eight_site_spinup500.sh` creation, `12_resume_eight_site_srun_pmix500.sh prepare` on 500-year-complete cases, or `13_extend_seven_site_spinup500_to1000.sh run` without a per-case progress and activity check. The local Git repo may have a merge conflict; place the downloaded script in `$HOME` independently, without running `git pull`.

## Usage
1. The script is already committed on GitHub. Because the local repository has unresolved merge conflicts, download **only this script** directly to Home using `curl` (no `git pull`):

```bash
mkdir -p "$HOME/FLUXNET8_recovery"
curl -fL --retry 3 'https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/FLUXNET_MultiSite_8/scripts/21_resume_eight_site_after_quota.py' -o "$HOME/FLUXNET8_recovery/21_resume_eight_site_after_quota.py"
```

2. On IRIDIS6:

```bash
conda activate clm_fates_env
SCRIPT="$HOME/FLUXNET8_recovery/21_resume_eight_site_after_quota.py"
python3 -m py_compile "$SCRIPT"
python3 "$SCRIPT" inspect | tee "$HOME/FLUXNET8_resume_audit_20261020.log"
myfiles
```

3. Only when the audit reports READY for a site and you have checked recent `CaseStatus` and failed model logs, prepare that site (one example):

```bash
python3 "$SCRIPT" prepare CZ-BK1 | tee "$HOME/CZ-BK1_prepare.log"
SESSION=$(sed -n 's/^SESSION=//p' "$HOME/CZ-BK1_prepare.log" | head -1)
test -f "$SESSION/PREPARED" || exit 1
cat "$SESSION/manifest.json"
```

4. Only after manifest review, submit **one time**:

```bash
python3 "$SCRIPT" submit "$SESSION"
```

5. Monitor `squeue`, `sacct`, and `CaseStatus` for both run and archive success before accepting a 5-year segment:

```bash
squeue -u ly3n24 -o '%.12i %.55j %.10T %R'
myfiles
```

Repeat `prepare SITE`/`submit SESSION` only for other READY cases. Never repeat `submit` on the same SESSION, and do not manually modify failed dependency jobs or CIME Git locks until checked. Preserve all restarts/backups. All CIME state remains on IRIDIS6, not on GitHub.
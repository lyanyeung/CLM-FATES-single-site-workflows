CLM-FATES 7-SITE 500-YEAR DIAGNOSTICS - IRIDIS6
================================================
Reference GitHub repo: https://github.com/lyanyeung/CLM-FATES-single-site-workflows
Target: examples/FLUXNET_MultiSite_8/scripts/

Seven sites:
CZ-BK1, IT-Ren, FR-FBn, DE-Hzd, CH-Dav, BE-Vie, IT-Lav.
FR-Hes excluded, not yet confirmed 500/500 at document review 2026-10-18.

Files:
18_plot_seven_site_spinup500.py     Main read-only Python plotting script
19_submit_seven_site_spinup500.sbatch  Slurm compute-node helper

USING VS CODE REMOTE SSH
1. Download both files and copy into remote folder:
   ~/CLM-FATES-single-site-workflows/examples/FLUXNET_MultiSite_8/scripts/
2. On IRIDIS6 login terminal:
   conda activate clm_fates_env
   cd ~/CLM-FATES-single-site-workflows
   git status --short  # verify only intended edits; do not pull over conflicts
   python -m py_compile examples/FLUXNET_MultiSite_8/scripts/18_plot_seven_site_spinup500.py
   sbatch examples/FLUXNET_MultiSite_8/scripts/19_submit_seven_site_spinup500.sbatch
3. Check progress:
   squeue -u "$USER"
   tail -f seven_site_spinup500_<jobid>.log
4. Results:
   ~/seven_site_spinup500_final/<SITE>/{PNG,CSV,JSON}
   ~/seven_site_spinup500_final/seven_site_spinup500_summary.csv

Only generate carbon charts if EC observations cannot be found:
   python examples/FLUXNET_MultiSite_8/scripts/18_plot_seven_site_spinup500.py \
      --carbon-only --repo "$PWD"
For explicit ICOS/EUF EC source:
   python examples/FLUXNET_MultiSite_8/scripts/18_plot_seven_site_spinup500.py \
      --sites CZ-BK1 --repo "$PWD" \
      --obs-csv CZ-BK1=/absolute/path/to/FLUXES_HH.csv

Scientific notes:
- Requires 500 consecutive annual archived h0a files; no partial-year claims.
- Uses the last FULL forcing cycle, not the final incomplete cycle.
- FATES NEE = -FATES_NEP; EC NEE = NEE_VUT_REF.
- Preserve observational FLUXNET/ICOS licences; do not publish restricted source CSVs.
- A finished 500-year simulation is not proof of carbon equilibrium.

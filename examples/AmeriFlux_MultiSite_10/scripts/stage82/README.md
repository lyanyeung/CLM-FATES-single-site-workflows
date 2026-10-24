# Stage82 — read-only DATM integration preflight


## Verified execution, 24 October 2026

**Operator's IRIDIS6 log:** both `--check --hash-all` and `--report --hash-all` **PASS** on the entire Stage81 output. **213/213 annual NetCDF SHA256 hashes verified**, ten site-specific first/last year NC samples reopened successfully, 10/10 yearly record/time/variable layouts passed those sampled checks, and all ten site stream templates remain unactivated. Report:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage82_DATM_case_integration_preflight_20261024T231124502670Z/`.

The reference-case argument was not supplied in that run: `REFERENCE CASE: NO_REFERENCE_CASE_PROVIDED UNKNOWN None`. The user subsequently found a **potential reference** with `env_run.xml` at:
`/home/ly3n24/NL_Loo_recovery_20261021/direct_20261021T021800Z_1708443`.
This is a **recovery folder**, NOT yet verified as a fully configured or working CIME/DATM case. Do not transplant station-specific metadata from NL-Loo.

**Immediate next step:** re-run the same read-only script with `--reference-case` set to that folder and inspect the generated report's `reference_case.runtime_xml`, `CaseDocs_datm_files` and `stream_mode`. This step does not need to re-hash all 213 NetCDF files. The actual DATM/CDEPS version, stream file syntax, time support, domain, approved ZBOT and single-site smoke-test case are still pending.


Stage80 successfully selected 10 forcing CSVs (only 18 original RH<1% ERA5 corrections). Stage81 successfully built 213 annual 30-minute NOLEAP NetCDF and 10 stream templates. The templates were not activated.

Run `82_readonly_DATM_case_integration_preflight.py --self-test`, then `--check --hash-all`, then `--report --hash-all`. This checks the exact Stage80 and Stage81 manifests, source checksum links, annual NetCDF SHA256 files, sample NetCDF time axes and seven core fields. Only `--report` creates a new report in the experiment reports directory.

Optionally pass `--reference-case /path/to/existing/cime/case` to inspect that case's existing `env_run.xml`, DATM settings and CaseDocs in read-only mode. An ICOS case is a format reference, not a source of site-specific settings.

Next: inspect whether the actual CIME case needs legacy DATM or CDEPS, establish site temperature/wind measurement heights for ZBOT (especially CA-Cbo and CA-Man), confirm the half-hour interval-centering and local-clock policy, and prepare a separate 1–5-day single-site smoke-test case. CLM1PT nearest requires interval-midpoint timestamps; do not leave a long run on default `extend` when forcing should cycle. The existing Stage81 stream templates still have domain placeholders and must not be enabled as-is.

This stage never edits original NetCDF, forcing CSVs, active model cases or Slurm jobs. NetCDF creation is complete; model coupling and smoke tests are not.

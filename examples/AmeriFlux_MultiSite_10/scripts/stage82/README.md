# Stage82 — read-only DATM integration preflight

Stage80 successfully selected 10 forcing CSVs (only 18 original RH<1% ERA5 corrections). Stage81 successfully built 213 annual 30-minute NOLEAP NetCDF and 10 stream templates. The templates were not activated.

Run `82_readonly_DATM_case_integration_preflight.py --self-test`, then `--check --hash-all`, then `--report --hash-all`. This checks the exact Stage80 and Stage81 manifests, source checksum links, annual NetCDF SHA256 files, sample NetCDF time axes and seven core fields. Only `--report` creates a new report in the experiment reports directory.

Optionally pass `--reference-case /path/to/existing/cime/case` to inspect that case's existing `env_run.xml`, DATM settings and CaseDocs in read-only mode. An ICOS case is a format reference, not a source of site-specific settings.

Next: inspect whether the actual CIME case needs legacy DATM or CDEPS, establish site temperature/wind measurement heights for ZBOT (especially CA-Cbo and CA-Man), confirm the half-hour interval-centering and local-clock policy, and prepare a separate 1–5-day single-site smoke-test case. CLM1PT nearest requires interval-midpoint timestamps; do not leave a long run on default `extend` when forcing should cycle. The existing Stage81 stream templates still have domain placeholders and must not be enabled as-is.

This stage never edits original NetCDF, forcing CSVs, active model cases or Slurm jobs. NetCDF creation is complete; model coupling and smoke tests are not.

# Research Filestore for CLM-FATES on IRIDIS6

This is a repository-wide guide for archiving model output to Southampton Research Filestore. It is separate from individual experiments under `examples/`.

## Storage locations

- Scratch: `/scratch/ly3n24/CTSM_FATES_OUTPUTS/`
- Research Filestore: `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/`
- Windows share: `\\\\xclimatetbm.files.soton.ac.uk\\xclimatetbm`

## Rules

Copy completed history NetCDF and snapshots first; verify byte-level checksums and annual-year inventories before considering removal from Scratch. Preserve active CIME cases, run directories, recovery backups, current restart pointers and checkpoint data. Do not commit .nc or flux-tower raw data to GitHub.

The observed Scratch issue on 18 October 2026 was the **per-user file-count quota** (614400/614400), despite 629/2000 GB capacity usage. A prior `df -i` on the NFS share measured the underlying filesystem, not necessarily a research-project quota.

## Case study: six FLUXNET sites

Five sites (RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat) previously produced complete 1000-year `h0a` time series, figures and diagnostics; DE-Hai is a backup-only case and its 1000-year completion was not confirmed.

- [Detailed case-study archival record](FLUXNET_MultiSite_6.md)
- [Existing science results and figures](../../examples/FLUXNET_MultiSite_6/README.md)
- [Read-only six-site archive audit](../../scripts/research_filestore/audit_six_site_archive.py)
- [Reusable case-by-case read-only inspector](../../scripts/research_filestore/inspect_archive.py)

**Transfer completion and Scratch deletion are not independently confirmed in these documents.** Only live checksum manifests and post-cleanup quota output can verify success.

## IRIDIS6 commands

```bash
myfiles
df -h /research/xclimatetbm
python3 scripts/research_filestore/audit_six_site_archive.py
```

This audit is read-only and must not be interpreted as cryptographic proof of migration.

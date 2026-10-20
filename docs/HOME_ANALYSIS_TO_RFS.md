# FLUXNET Home analyses → Research Filestore

A separate Home-to-RFS workflow complements the existing [Scratch analysis archive](SCRATCH_ANALYSIS_TO_RFS.md). Based on the 21 October 2026 Home image inventory: 963 images across Home, including 536 in unrelated `~/R`, 21 in `~/seven_site_spinup500_final`, 15 in `~/six_site_spinup1000_final`, and repeated publication/checkpoint directories. The inventory is **not** evidence all 963 need archiving.

[Source](../scripts/research_filestore/archive_home_analyses.py) — standard-library Python 3.9+, no Slurm; execute on an IRIDIS6 **login** node with RFS mounted as NFS. Default `audit` produces stdout only; `copy` creates files **only on Research Filestore** and SHA256-validates copies; `verify` checks a receipt independently. **No Home deletion mode exists**.

Explicit Home directory allowlist:
- `six_site_spinup1000_final` → `FLUXNET_MultiSite_6`
- `seven_site_spinup500_final` and `eight_site_targeted_review` → `FLUXNET_MultiSite_8`
- `plot11_1000_HOME_*/results` and dedicated `CLM-FATES-11site-plot-*/results` paths → `FLUXNET_MultiSite_11`; previously matching files under `spinup1000_final` are recognized by SHA256 and not recopied
- `CLM_FATES_13_checkpoint` → `FLUXNET_MultiSite_13`
- With `--include-snapshots`, also scan `FLUXNET13_PUBLICATION_*` for reproducible versioned snapshots under the 13-site batch.

Each eligible directory must include image files. Associated CSV/TSV/JSON/TXT/MD in image-bearing folders are copied for analysis provenance. Paths retain their Home folder names. Git repositories, Home `R`, `fcm`, `CARDAMOM`, arbitrary Python code, CIME run/restart/NetCDF and raw tower observations are outside scope.

## No-clone / no Home or Scratch writes

```bash
URL="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/scripts/research_filestore/archive_home_analyses.py"

# Inventory proposed files only
curl -fsSL "$URL" | python3 -B - audit --batch all

# Optionally inspect historical thirteen-site publication snapshots
curl -fsSL "$URL" | python3 -B - audit --batch FLUXNET_MultiSite_13 --include-snapshots

# Copy all allowlisted outputs and two versioned thirteen-site snapshots, if desired
curl -fsSL "$URL" | python3 -B - copy --batch all --include-snapshots
```

Each nonempty batch prints a `RECEIPT:` path under:
`/research/xclimatetbm/ly3n24/CLM_FATES/<batch>/home_analysis_archive/_receipts/`

Verify one actual receipt (replace path with output from copy):

```bash
curl -fsSL "$URL" | python3 -B - verify --receipt "/research/xclimatetbm/ly3n24/CLM_FATES/FLUXNET_MultiSite_6/home_analysis_archive/_receipts/ACTUAL_RECEIPT.json"
```

Results live under:
`/research/xclimatetbm/ly3n24/CLM_FATES/<batch>/home_analysis_archive/<original-Home-folder>/...`

This preserves independently re-creatable outputs and distinct publication versions; repeated image contents are checked by SHA256 but version directories are intentionally retained. The two publication folders may include duplicate image snapshots, not necessarily independent results. **Do not remove Home folders until the archived contents, intended downstream references and GitHub reproducibility are reviewed.** Existing eleven-site final archive remains untouched.

As of this documentation update: code and runbook have been published; **this is not evidence that Home-to-RFS transfers have actually run**.

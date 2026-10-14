# Publish Stage13–16 code (run in WSL, not on IRIDIS6)

This package contains only source code/docs. Repository root scripts/stage02–11 are left unchanged.

1. Unzip the package into a temporary folder.
2. Clone your existing repo or update a local checkout.
3. `rsync -av --exclude=__pycache__/ <package>/examples/FLUXNET_MultiSite_11/scripts/stage13/ <repo>/examples/FLUXNET_MultiSite_11/scripts/stage13/` (repeat stage13b, stage14, stage15, stage16), or use the one-block WSL shell instructions in ChatGPT.
4. Run `python3 -m compileall -q <repo>/examples/FLUXNET_MultiSite_11/scripts/stage{13b,14,15,16}`.
5. `git add examples/FLUXNET_MultiSite_11/scripts/stage13* examples/FLUXNET_MultiSite_11/scripts/stage14 examples/FLUXNET_MultiSite_11/scripts/stage15 examples/FLUXNET_MultiSite_11/scripts/stage16` and commit/push.

NOTE the patched Stage15 script for CH-Fru/CZ-Stn checks `trial_sha256` and never bypasses digest verification. No user source CSV, policy JSON, audit report, private data or site outputs are included.

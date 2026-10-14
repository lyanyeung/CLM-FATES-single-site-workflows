# Upload this eleven-site example to the public GitHub repository

This directory contains all Python scripts and documentation. To publish without uploading any restricted observational data, run the ZIP's top-level `publish_to_github_from_wsl.sh` from **WSL** after downloading the ZIP. The script stages only the new `examples/FLUXNET_MultiSite_11/` folder and one README index addition, refuses to replace an existing eleven-site folder, performs `git diff --cached --check`, commits, and pushes to `main` using your configured GitHub SSH credentials.

It does **not** need IRIDIS6 or any raw files; executable code and documentation only. The push will fail safely if WSL is not authorized to write to GitHub. You may manually inspect the staged files before running `git push`.

# Batch04 Stage12 second ERA5-Land completion — 148 of 156 target timestamps resolved

**Operator result (2026-10-25, IRIDIS6):** Stage12 second execution completed, with `STAGE12 RESULT 148 of 156 resolved 8 not resolved`. Initial Stage12 run had 143/156 resolved. Thus the new execution resolved 5 additional distinct timestamps, and there are **8** remaining non-US-Syv target times. All eight previously missing external ERA5-Land site-years have been acquired/recovered; a third blind download would be unnecessary.

The 156 unique targets represent 155 old science HOLD entries at US-SP1, US-Ton, US-Seg, US-SRG, US-Uaf plus 2 separately listed US-SP1 jump-boundary exceptions with one overlap. The separate US-Syv 606 original holds and 10 jump-boundary exceptions are **not part of the 156** and remain deferred.

## Source acquisition completed

The first execution provided US-SP1 2008, 2007 and 2000. The second execution provided all remaining five:

| Site | Year | Target HH records requiring this grid year | Retrieved response SHA256 | Retrieval mode |
|---|---:|---:|---|---|
| US-Seg | 2018 | 2 | `1a207213c327faebd2aed31d8594fc42dfe446a90a4af8f49a61df45fa4775e5` | Reused previously complete partial |
| US-Uaf | 2004 | 2 | `a74bdd5b31b48f6df802f8d889d37460f941937f0c6f9ec420ec8459c733b9ae` | Successful new CDS response |
| US-SRG | 2019 | 1 | `7be344039c47ed5c1326d89a95f2acd494a82fcfd1dff599facf5f9446ea0d03` | Successful new CDS response |
| US-Seg | 2014 | 1 | `13ffde210933cda93901f68caf314a4c27983ae74978541765ddfa1bc9d9f77f` | Successful new CDS response |
| US-Seg | 2016 | 1 | `5f7d7eb862aa30641f626a8a925c6774e0b99d63820ba2f31d1df7da98eca480` | Successful new CDS response |

**Latest Stage12 derived directory:**

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c
```

Full ten-site candidate-path manifest: `stage12_repaired_source_candidates.tsv`.
Detailed scientific decision ledger: `stage12_science_decisions.tsv`.
SHA receipts and site status counts: `stage12_receipt.json`.

No original FLUXNET, Stages 05–11, CIME, DATM or Slurm job inputs changed. Stage12 produced new derived source-version candidates; they are not yet Post-v5-approved model forcing.

## Exact remaining eight — need their decision statuses, not further CDS retries

Operator console states **8** unresolved but does *not* show which sites/clock times or hold reasons they correspond to. They could reflect failed tower-neighbour temperature support, source pressure constraints, ERA5-Land RH physics or other fail-closed conditions. Do not assume they are all missing values or manually approve them.

Use the command below to extract the exact eight from the generated scientific ledger:

```bash
python3 - <<'PY'
import csv
from pathlib import Path
from collections import Counter
p=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage12_non_syv_repaired/candidate_20261025T065108Z_6814ab0c/stage12_science_decisions.tsv")
with p.open(encoding="utf-8",newline="") as fh:
    rows=list(csv.DictReader(fh, delimiter="\t"))
holds=[x for x in rows if not x["status"].startswith("RESOLVED")]
assert len(rows)==156 and len(holds)==8,(len(rows),len(holds))
print("UNRESOLVED 8 / 156:")
for x in holds:print(x["site"],x["TIMESTAMP_START"],x["status"],x["requested_reasons"])
print("GROUPS",dict(Counter((x["site"],x["status"]) for x in holds)))
PY
```

**No further CDS download** is required for this existing set of eight grid years. The next repair operation should be restricted to genuinely fixable situations identified in those eight records; respect physical closure and user preference for trustworthy tower measurements. US-Syv remains deferred until expressly resumed.

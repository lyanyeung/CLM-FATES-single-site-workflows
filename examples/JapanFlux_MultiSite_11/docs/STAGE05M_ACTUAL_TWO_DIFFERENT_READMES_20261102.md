# JapanFlux Stage05M actual two native README release editions (2026-11-02)

## Operator's actual results

The operator executed [Stage05M JSON-only saved README provenance review](../scripts/stage05/05m_inspect_saved_stage05k_README_time_hints_NO_ZIP_NO_SLURM.py). The script returned `STAGE05M SELF-TEST PASS` and completed five-site JSON inspection without Slurm or any source ZIP reopening.

| JPF site | Saved README SHA256 | Saved README lines | README Stage05L strict local-standard/no-DST match | Excerpt truncation |
|---|---|---:|---|---|
| JP-Fjy | `fe96facec6fafc57b126e850140152a540a16d97c3bfde8adfa090a3747598f9` | 85 | Yes | No |
| JP-Khw | same 85-line version | 85 | Yes | No |
| JP-Yms | same 85-line version | 85 | Yes | No |
| JP-Tef | `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` | 75 | **No** | No |
| JP-Tmd | same 75-line version | 75 | **No** | No |

The three 85-line README reports all include source original line 69:

> The data are in ASCII format, comma delimited, with first row as header. Missing data are indicated as -9999 and time is expressed in local standard time (without DST). Metadata about the measurements are reported in the BIFVARINFO files.

The JP-Tef and JP-Tmd source README documents have a **different SHA256 and 10 fewer lines**; their saved Stage05K **time/unit metadata excerpt** has no strict `local standard time (without DST)` match and no recognized equivalent wording. The excerpt cap was **not** reached for either. **This does not yet prove that the entire original 75-line README lacks a relevant clock statement**, merely that Stage05K's regex-selected excerpts did not capture one. It is incorrect to mark the 75-line releases as UTC=0, time-incompatible, physically broken, or automatically equivalent to the other README by assuming shared semantics.

Five site BIF source rows each still establish **`UTC_OFFSET=9`**, and all five pass the original Stage05L source unit, QC and ERA-downscaling-definition tests. Current metadata gate remains **3/5 VERIFIED**, **2/5 HOLD**, with **no Stage05L UTC join output**. The full 45 source-selected variable-level science candidates / 35 site×native half-hour keys remain **HOLD**, unaffected by README differences.

## Next forensic step

[Stage05N original complete 75-line README read-only check](../scripts/stage05/05n_full_alternate_Tef_Tmd_README_source_SHA_readonly.py) is **published, not yet run on the operator's IRIDIS6 originals**. It opens **only JP-Tef's original nested ZIP once** (bounded RAM) to read a single small `README.txt` source member, verifies its **original byte SHA256 and line count** exactly against the two saved JP-Tef and JP-Tmd Stage05K metadata hashes, and prints the entire original 75 lines with source line labels. The two saved exact SHA digests match, so one original README read is sufficient to check the document's currently recorded identical contents. No gas/meteorological CSV rows are read, and no Slurm/model/forcing repair action occurs.

After seeing exact original text, assess whether an explicit authoritative source rule exists; if none exists in the 75-line README, **retain Stage05L HOLD** and look for an additional original JPF data-producer documentation/source or authoritative FLUXNET local-time convention before proposing a narrow metadata gate correction. Do not simply disable the time gate.

## Important status

- Stage05M: **complete**, identical original README SHA by source group and distinct README editions confirmed.
- Stage05L: **3/5** verified; JP-Tef and JP-Tmd remain pending time semantics.
- All 45 Stage05I source-contamination field candidates: **HOLD / NOT APPROVED**; no original edits, no forcing, no Slurm/AD400.

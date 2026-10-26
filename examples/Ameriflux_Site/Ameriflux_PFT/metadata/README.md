# Curated source ledgers and membership

`sites_50_manifest.csv` copies the50 exact memberships from the five original campaign `sites.tsv` files. Package labels and years are provenance, not a new coverage/QC certification.

`source_records_batch01.json` through `source_records_batch05.json` each contain10 manually curated research records. They are summaries with source links, not full-text paper reproductions. They retain measured composition, denominator, observation date/extent, source locator, verification basis, uncertainties and next evidence.

| Field | Meaning |
| --- | --- |
| `numeric_percent_evidence` | At least one composition/cover percentage lead. Can be partial, local, historical or conflicting; excludes LAI/density alone and model fCover alone |
| `functional_group_percent` | Scalar percentages for explicitly named source groups. Empty object means no suitable scalar summary. Keys are not FATES parameter slots |
| `functional_group_percent_basis` | Source denominator, observation period and spatial scope. Different years or overlapping strata must not be added together |
| `candidate_pft` | Botanical-to-functional interpretation for a subsequent experiment. Numbers may be source-basis proxies, not land area |
| `verification_status` | How source content was accessed and what was actually verified |
| `existing_github_path` | Earlier repository ledger or campaign README used as provenance |
| `prior_operator_decision` | Earlier specific input policy, if any. US-Aud70C4/30bare remains a model assumption |

The generator joins these records to the membership manifest and adds the11 separately labeled historical ORCHIDEE fCover configurations. It leaves FATES end-state percentages empty because none was found in the reviewed AmeriFlux repository records. It does not download BADM, assign active FATES slots or create model inputs.

Source sums can be partial or rounded: Borden100.3, Harvard99, Bartlett97, UMBS2001 total98. A sum is not repaired by normalization. Ranges such as US-SRM cover40–50% bare remain in the source text rather than being replaced with an invented midpoint.

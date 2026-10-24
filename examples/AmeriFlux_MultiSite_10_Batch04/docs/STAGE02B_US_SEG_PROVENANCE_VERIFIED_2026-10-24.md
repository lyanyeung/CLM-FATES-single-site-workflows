# Batch04 Stage02B: US-Seg BIF coordinate provenance (2026-10-24)

**Evidence:** operator-provided read-only Stage02B IRIDIS6 output; not an assistant-operated cluster session.

| Original BIF GROUP_ID | Latitude | Longitude | Elevation | Other source information |
| --- | ---: | ---: | ---: | --- |
| 1479 | 34.3623 | -106.7019 | 1622 m | BIF line 11: "From CDIAC Tom Boden database dump" |
| 1495 | 34.3623 | -106.7020 | 1596 m | BIF line 45: LOCATION_DATE_START 200701010000 |

The paired BIF records differ by approximately 9.2 m in longitude and 26 m in elevation.

**External independent references, not replacements:**
- [Litvak Lab US-Seg](https://www.litvaklab.org/grassland---us-seg.html): 34.3623, -106.7019, 1622 m; matches 1479.
- [Current AmeriFlux US-Seg](https://ameriflux.lbl.gov/sites/siteinfo/US-Seg): 34.3603, -106.7003, 1596 m; elevation matches 1495, but latitude/longitude do not.
- [AmeriFlux Core Sites](https://ameriflux.lbl.gov/sites/ameriflux-core-sites/): US-Seg desert grassland 1622 m.
- Original BIF IGBP label is GRA.

**Interpretation:** The BIF contains two internally paired, provenance-distinct coordinate groups. Group 1495 has a 2007 start date and is a candidate to investigate for this 2007–2025 release. Group 1479 is independently corroborated by the site research team. Neither explains the current AmeriFlux page's different position, and the information does not establish tower movement.

> **Later decision (2026-10-24): User APPROVED GROUP_ID 1495 latitude 34.3623, longitude -106.7020, elevation 1596 m.** See [approval record](STAGE02_US_SEG_GROUP1495_USER_APPROVAL_2026-10-24.md). The below pending statement is retained as an earlier historical status.\n\n**Decision at the time of Stage02B: PENDING HUMAN SCIENTIFIC APPROVAL.** Do not edit the original release BIF, invent a merged coordinate, average positions, automatically select a surface-cell coordinate, assume ZBOT or mark Stage02 10/10. Stage02 remains 9/10; US-Seg under review. Full native HH time-series checks can proceed independently.

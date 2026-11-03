# Stage05BI/BJ: ICOS identity evidence and Tmd PA boundary decomposition

## ICOS published records, 2026-11-03

Read-only ICOS portal browsing identified the following same-version products. Public metadata were viewed, but the ICOS ZIPs were not downloaded and the operator's IRIDIS6 nested ZIPs were not read here.

| Site | ICOS full archive | Published archive SHA256 | Separate half-hour subset |
|---|---|---|---|
| Tef | [`JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1.zip`](https://meta.icos-cp.eu/objects/U36jKvGfGICHSJO01Sk4jEZT) | `537ea32af19f1880874893b4d529388c465331ccfc42dd5987341568a5427527` | [FLUXMET HH subset](https://meta.icos-cp.eu/objects/5EPoidiNgWdizvMjVuk1G1vC), 403,200 rows |
| Tmd | [`JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1.zip`](https://meta.icos-cp.eu/objects/0o-e7G4yJgKYUrpjjLe7w0lt) | `d28f9eec6e3226029852ba638cb7bbc3496d74880da8f3f29fec95b0ea3cb48f` | [FLUXMET HH subset](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS), 333,072 rows |

Both half-hour subset pages describe `TIMESTAMP_END` as **local non-DST time**, and show UTC coverage consistent with midnight-to-midnight site years in UTC+9. Both earlier BIF metadata reported UTC_OFFSET=9. This is stronger publisher-specific support for using UTC+9 as the current diagnostic interpretation than was available in Stage05BH. However, the separately packaged half-hour subset is not byte-identical evidence for the exact member in the operator's full archive, and both source README files were previously verified to state local solar time without DST. Those statements are not yet reconciled; no final clock proof or scientific repair approval is asserted. Do not infer precise half-hour UTC from the nominal annual coverage in the **full archive** metadata: its advertised UTC year bounds differ from the subset page's bounds.

ICOS states that the public full archive and the half-hour plotting subset are separate objects. Operator's source is an outer ZIP containing an identically named inner ZIP; its outer SHA differs from the ICOS full-archive SHA, which is expected to be compared with the **inner ZIP**, not the outer wrapper. The inner identity has **not yet been checked**. A local attempt to read the exact publisher archive README through its advertised member link encountered an ICOS login requirement; no login, agreement or download was performed.

`05bi_icos_nested_identity_clock_audit_READONLY.py` is prepared to hash the two operator nested ZIPs in memory, compare against the published ICOS archive SHA256s, check outer ZIP and source README SHA before/after, and print the exact source README lines mentioning the clock. An equal nested SHA confirms byte identity to the published full archive; a difference is explicitly reported and can reflect repackaging or another release artifact. Either outcome leaves the conflict and all 45 values HOLD. Script self-test and a synthetic test covering equality, inequality and outer-ZIP tampering passed locally; **the script has not yet run on IRIDIS6**.

## Tmd PA left-boundary diagnosis from existing evidence

The Stage05BE selected candidate is `grid_first + median(QC2−grid)`. Let `L` be the immediate left source QC2 value, and `grid_left` the existing hourly PA grid interpolated to that left half-hour midpoint under UTC+9. Then the signed jump is exactly

`selected_first − L = (grid_first − grid_left) + [median(QC2−grid) − (L − grid_left)]`.

The first term represents the saved reference-grid change; the second is the change from the *individual left endpoint residual* to the selected constant background median. This is an algebraic decomposition of a method discontinuity, not an independent estimate of physical truth. The left grid value is approximated from six-decimal operator-pasted hourly values, with matching conventions inherited from Stage05AZ; no ERA5-Land comparison was rerun.

| Tmd PA native group start | Grid change, kPa | Residual transition, kPa | Selected first − left source, kPa |
|---|---:|---:|---:|
| 2005-08-12 02:30 | −0.001575 | −0.020863 | −0.022438 |
| 2011-12-17 06:30 | +0.020490 | +0.055855 | +0.076345 |
| 2022-04-09 02:30 | −0.012078 | −0.122073 | −0.134150 |

For 2022, roughly 91% of the signed jump magnitude comes from this residual transition, not a comparably large reference-grid change. This explains the *mechanism in the chosen construction*; it does not prove the reference, left source QC2 or median is correct. The user-selected method is unchanged. The pressure background, endpoint representativeness, clock and possible mitigation remain science-review questions; all 45 remain HOLD.

`05bj_tmd_pressure_boundary_decomposition_READONLY.py` reproduces the three rows using the operator-pasted Stage05AU/AV hourly context and SHA-pinned local Stage05BE/BA ledgers. The script's self-test and two unit tests passed locally; it reads no original ZIP and writes no forcing. No CDS comparisons were repeated, and no PFT, Soil Texture, case, Slurm or AD400 changes were made.

# Batch05 US-UMd — manual assessment of all six Stage63 original P2/P3 RH/VPD events (15 HH)

**Operator-provided source data: 2026-10-29.** Original SHA-verified AmeriFlux US-UMd FLUXMET_HH archive has SHA256 `27095ccd71a1c28cee5e730ca2ad99d0acb6fba7a4be07ffaa8cff7a41f2e3c5`; Stage63 precisely six source episodes, 15 unapproved original source-native HH. Human reviewer supplied exact original tower TA_F (all QC0), selected VPD_F (all QC1), paired companion TA_ERA/VPD_ERA, precipitation and shortwave before and after each of six events.

## Findings

**All 15 source flags are physically non-feasible implied RH < 0%, while corresponding TA_F_QC=0 and VPD_F_QC=1. Preserve tower TA/QC0; the moisture/VPD MDS fill is the source concern, NOT tower-measured TA.**

| Episode | Native flagged HH | Count | Most negative RH | Assessment |
| --- | --- | ---: | ---: | --- |
| E0001 | 2015-04-30 10:00 | 1 | −6.10% | VPD QC1 fill physically impossible |
| E0002 | 2015-05-01 08:30–09:00 | 2 | −0.36% | VPD QC1 fill slightly exceeds saturation constraint |
| E0003 | 2015-05-04 09:00–09:30 | 2 | −33.80% | VPD QC1 fill impossible, contemporaneous rain makes dry-state source neighbors suspect |
| E0004 | 2015-05-04 17:30 | 1 | −12.89% | VPD QC1 isolated spike |
| E0005 | 2015-05-05 07:30–09:30 | 5 | −72.90% | Severe MDS high-VPD plateau; nearby 07:00 RH=8.05% and 10:00 RH=2.71%, also low and potentially unreliable |
| E0006 | 2015-05-06 07:30–09:00 | 4 | −9.97% | MDS VPD overly high during strong morning warming; nearby 09:30 RH=3.77% also suspicious |

## Exact reproducible *numerical* candidate for discussion only

One local continuity method that is strictly finite and retains the measured original T uses **linear interpolation of inferred RH** (NOT raw VPD, because VPD linear interpolation can leave RH negative) between the immediate bracketing original *valid implied-RH QC1* source-neighbor half-hours of each event; then `VPD_candidate=es(original TA_F_QC0)*(1-RH_interpolated/100)`, with `es(T)=6.112 exp(17.67 T/(T+243.5))` hPa. All source QC fields remain unchanged. **These anchors are themselves QC1 filled VPD, not measured RH: numerical continuity cannot prove scientific realism. E0003 has precipitation and E0005 unusually low neighbor RH.** A distinct physically based alternative is source processed ERA RH at measured T, but replacing the 15 HH alone with that method produces large new source-boundary discontinuities (e.g. E0003 09:30 candidate 1.278 vs unmodified 10:00 source VPD 18.120 hPa).

| Event | Native HH | Original VPD hPa | Original RH % | Inferred-RH interpolation VPD hPa | Interpolated RH % | Source ERA RH-at-measured-T VPD hPa |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| E0001 | 201504301000 | 10.671 | −6.10 | 8.297 | 17.50 | 2.220 |
| E0002 | 201505010830 | 12.289 | −0.32 | 10.651 | 13.06 | 2.176 |
| E0002 | 201505010900 | 13.419 | −0.36 | 11.946 | 10.65 | 2.609 |
| E0003 | 201505040900 | 20.824 | −33.80 | 8.145 | 47.66 | 1.061 |
| E0003 | 201505040930 | 17.869 | −4.28 | 12.759 | 25.54 | 1.278 |
| E0004 | 201505041730 | 20.824 | −12.89 | 11.937 | 35.29 | 10.569 |
| E0005 | 201505050730 | 20.029 | −72.90 | 10.754 | 7.16 | 2.255 |
| E0005 | 201505050800 | 20.029 | −58.66 | 11.832 | 6.27 | 2.576 |
| E0005 | 201505050830 | 16.486 | −20.24 | 12.973 | 5.38 | 3.344 |
| E0005 | 201505050900 | 16.773 | −11.43 | 14.377 | 4.49 | 4.203 |
| E0005 | 201505050930 | 17.554 | −8.38 | 15.613 | 3.60 | 5.746 |
| E0006 | 201505060730 | 15.317 | −9.97 | 6.904 | 50.43 | 3.714 |
| E0006 | 201505060800 | 16.592 | −4.66 | 9.707 | 38.77 | 4.737 |
| E0006 | 201505060830 | 17.107 | −0.49 | 12.409 | 27.10 | 5.846 |
| E0006 | 201505060900 | 17.830 | −0.69 | 14.974 | 15.44 | 6.761 |

**Decision state:** Original source instrument TA_QC0 retained; 15 QC1-VPD points established physically invalid. No user science approval or DATM permission for either candidate method yet. All original site archive, original QC, full-site 204-approved overlay and DATM/CIME/Slurm remain unchanged. This report does not claim the other source QC1 VPD HH, some with RH near 0%, are physically well constrained. Science reviewer may approve an explicit proposed versioned RH/VPD overlay after assessing the source adjacent records and rain.

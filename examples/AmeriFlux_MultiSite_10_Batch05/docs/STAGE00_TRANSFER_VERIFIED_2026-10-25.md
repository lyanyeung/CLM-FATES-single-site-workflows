# Batch05 Stage00 transfer evidence — 2026-10-25

Status: **UPLOAD VERIFIED 10/10, operator-reported**. The user supplied a successful terminal excerpt ending with:

```text
UPLOAD VERIFIED: 10/10 (AmeriFlux Batch 05). Originals retained. No extraction or model jobs started.
```

Visible per-site evidence in this excerpt:

| Site | ZIP bytes | SHA256 |
| --- | ---: | --- |
| US-WCr | 175898416 | `f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75` |
| US-Whs | 141028159 | `0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767` |
| US-Wjs | 184586029 | `75c7132fe8695a61f32dd4ad64235e97dccc786fcea75eb09a37d4ac1ea9ccda` |
| US-Wkg | 230682926 | `d9c31372ad29fa79946a97ac30eb02ad679b261f0b925db97ef88cf6b325221e` |

The final line establishes the script's aggregate successful verification of ten releases. Individual sizes/checksums for US-UiD, US-UMB, US-UMd, US-Var, US-Vcm and US-Vcp were not included in the provided excerpt; they remain available in the operator's full WSL log. No checksum is inferred for those six. Stage01 computes all source ZIP checksums again and records them in a separate extraction inventory.

Stage01 script publication and local synthetic self-test do not establish actual extraction success on IRIDIS6. Raw data are not committed to GitHub. No model jobs were started by this transfer.

# Stage92 invalid-CDS-RH hotfix — original operator evidence (26 Oct 2026)

## Error and bounded interpretation

IRIDIS6 Stage92 initial code `ALL 3 SYNTAX PASS`, `SELF-TEST PASS`, all 5 × original FLUXMET+ERA raw pairs SHA PASS, then raised:

```
ValueError: Stage74 physical RH shadow bounds violated US-Ho1 201104201300
```

This was a **driver policy bug**: Stage74's 16,874 provenance rows include original-T QC science HOLD and possible physically invalid independent ERA5 RH. A row outside `0 < RH <=100`, `-80 < TA < 65 C`, or `50 < PA < 110 kPa` must NOT be used as a correction; it need not prevent processing all five site/year source candidates. Error occurred **before** any Stage92 build output or source changes.

## Fix

[Stage92 source driver](../scripts/stage92/92_build_remaining_five_candidate_forcing_and_nc.py), commit `ebe0a9b01f9c61d191cb437a73c4f1e9af7f4ab7`, blob `9d18536a3910d3b3a7fdea8a2879ce5634b9af43`, is changed to:
- Reject invalid Stage64/Stage74 original source RH/T/PA rows **individually** (no floor, cap, interpolation or synthetic value).
- Keep exact source site/native timestamp/row number/source T-QC/RH/status/reason in `source_row_holds_stage64_stage74.csv`, which is immutable per isolated Stage92 run and checksum-protected in manifest.
- Preserve source-time uniqueness: duplicate Stage64/74 site+time does NOT silently overwrite the earlier provenance source. It becomes a visible HOLD.
- Print summary and up to 20 individual first HOLD records, then continue every other site and timestamp.
- Existing Stage92 engine checks that source T and P match current selected forcing before applying external RH, and original Stage07 remaining humidity reconciliation can be attempted without the rejected source. A site unable to produce physically valid complete forcing is printed as `STAGE92 SITE HOLD/FAIL`, while other sites continue.
- Keep source SHA / Stage85 exact approved decision / original-input provenance gates **fail closed**: source corruption, mismatch or missing source must never be ignored just to complete technical files.

Repaired driver is compatible with unchanged Stage92 source engine (commit `9b0e3b2f956205f37065b4066f58aa65f80efef4`, blob `e0c938d1115650db1ffaa4450947b549a514d1f3`) and original Stage87 preview writer commit `7e4c3cd653289872d09f7a6a71e75fa35a258c2b`, blob `4f62ba03f52b41b98d7b6db3e89af2bf10bee8a1`.

## Shell behavior

Use shell code that independently captures the build command's exit code through `PIPESTATUS[0]` after piping to `tee`, prints the report path and per-site `STAGE92 SITE HOLD/FAIL` or `STAGE92 COMPLETE FORCE CSV` lines, and **never uses `set -e` to terminate the parent login shell**. The program reports nonzero status for incomplete five-site source/NC technical production, but preserves completed independent site outputs and recorded source HOLDs. Do not relabel incomplete NetCDF technical previews as active DATM.

Operator rerun on IRIDIS6 pending. Original Stage91 PASS, original Stage87 117 NC previews and Stage85 manually approved Ho1 2000 QC0 temperature/humidity remain unchanged.

# Stage05AP — ready-to-send original JPF v1.3_r1 timebase provenance enquiry (NOT SENT, 2026-11-02)

## Purpose

Stage05AO **actually PASS**: JP-Tef original 403,200 and JP-Tmd original 333,072 half-hour source records validated, all 18 selected source QC2 fields matched. **27 other source QC2 flagged variables already independently meteorologically contextualized; 18 remain `UTC=UNRESOLVED`**, and all **45 original records science HOLD**. User confirms JapanFlux PFT updated, which is unrelated.

The 75-line original JPF README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`, line 64 says `time is expressed in local solar time (without DST)`, but original site BIF `UTC_OFFSET=9` and [ICOS same-revision JP-Tmd FLUXMET_HH metadata](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS) report local non-DST and acquisition start `2004-12-31 15:00 UTC`; this is a source-level **contradiction**, not enough to automatically map timestamps.

Preferred recipient: ICOS Carbon Portal general support **info@icos-ri.eu** (from the official exact JP-Tmd catalogue, for routing to Ecosystem Thematic Centre/original JPF product time-processor). [Same-revision JP-Tmd product](https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS), authored Hirano/Hirata; [2025 JapanFlux2024 corresponding author Masahito Ueyama](https://essd.copernicus.org/articles/17/3807/2025/) is *only a possible referral* and JapanFlux2024 is a **different dataset**, so do not assume their time processing equals JPF v1.3_r1.

## Draft email (not sent)

To: info@icos-ri.eu

Subject: Timestamp convention for JPF JP-Tef / JP-Tmd FLUXNET v1.3_r1

Dear ICOS ETC team,

I'm using these exact JPF FLUXNET releases for meteorological forcing:

- `JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1`
- `JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1`

Their original `README.txt` states **local solar time (without DST)**, while the BIF reports **UTC_OFFSET=9** and ICOS metadata for JP-Tmd lists `TIMESTAMP_END` as local non-DST time with a UTC start of **2004-12-31 15:00**.

Could you confirm whether the distributed `FLUXMET_HH` `TIMESTAMP_START/END` are already **Japan Standard Time (UTC+9)**, or **local solar time**? If solar, is it mean or apparent solar time, and was there any conversion during processing? A release-specific processing note or the contact of the responsible data processor would be very helpful.

Thank you for your help.

Best regards,

[Your name]

## Science safety

Do not assume the email has been sent, replied to, or proves the source conversion. No further date-specific CDS for Tef/Tmd or automatic `TIMESTAMP_START - 9h` source mapping is approved without a credible release-specific timebase answer. Retain all 45 original QC2 source-variable fields `HOLD`; do not modify original ZIP/forcing/model or submit Slurm.

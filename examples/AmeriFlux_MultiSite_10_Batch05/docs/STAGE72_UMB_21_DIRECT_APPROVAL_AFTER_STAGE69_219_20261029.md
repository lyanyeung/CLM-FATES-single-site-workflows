# Batch05 US-UMB Stage72 negative RH direct repairs

Operator ran Stage69 successfully 2026-10-29: US-UMd 15/15 originally negative RH half-hours were directly approved in new versioned 219 RH/VPD record overlay. Previous 204 user approved native RH/VPD rows preserved. The immutable SHA256 of that approved 219 overlay is `a4d9944d0f890078e77903d015700e2a4521da512097f3d921b478bfe9c76fda`.

Stage70 original US-UMB FULLSET_HH SHA256 `ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6` and source TA/VPD/QC exactly match all 23 historical Stage27 flagged times; 22 remain for 8 original events. **21/22 have negative implied RH; the exception is 2010-04-08 06:30 RH approximately +0.0258%** (displayed as +0.03%): physical nonnegative. All these 22 have TA_F_QC=0 and VPD_F_QC=1. Temperature must be preserved.

Following the operator's explicit scientific rule on 2026-10-29, every original RH<0 HH is **directly approved for versioned RH interpolation correction with source measured TA fixed**, not sent to additional candidate/HOLD review. The one nonnegative original source HH is **PASS unchanged**, not edited and not inserted in the repaired overlay.

Stage72 reads original Stage69 219 overlay and SHA, Stage63 original exact pending 22 US-UMB HH, Stage27 original historical 23 US-UMB source T/VPD/QC, and original SHA-pinned FULLSET_HH. It finds eight contiguous negative RH runs (including 2010-04-08 07:00–12:30, 12 negative HH adjacent to the nonnegative 06:30 original HH). For each source-invalid run, linearly interpolates implied RH between the immediately adjacent native nonnegative source RH values and recalculates VPD at the **unchanged original tower TA_F_QC0**. The method uses original source neighbor QC0/1/2 values; source QC1 and QC2 RH anchors are not direct humidity measurements.

The original source 2010-04-08 06:30 RH+0.03% is **outside the user's automatic RH<0 rule** and passes unchanged, despite being exceptionally dry for the date. This is a selective source numerical repair policy. It does not claim that the entire original source moisture field was independently validated or meteorologically accurate.

Expected Stage72 after IRIDIS6 execution:
- New user-approved RH/VPD overlay **219+21=240 HH**.
- Historical 219 versioned approved rows and original source/QC exactly preserved.
- US-UMB original 8 episodes / 22 flagged source HH all scientifically disposed under investigator rule: 21 repaired and one pass unchanged.
- Stage63 historical unmatched P2/P3 after Stage69 1550, after Stage72 versioned repair 1529. One remaining original unmatched US-UMB HH is passed unchanged in a separate source decision ledger; 1528 original flags would remain in need of source-science work across other sites.
- No original FULLSET, DATM, CIME or Slurm modifications.

Source script [Stage72 direct 21 negative RH into 240](../scripts/stage72/72_US_UMB_negative_RH_21HH_direct_approved_240.py), immutable commit `2db26af772756d41002e7eee1bf620ac24ca4afa`, Git blob `2e3f2b9eba5827c6541999b16fc1f6239bc27006`.

[Stage72 pinned launcher](../scripts/stage72/run_stage72_UMB_21_direct_approve_iridis6.sh), immutable commit `5cee54e707ea8afa5a44e6e185882f532ba6a2e2`, Git blob `c7831ce788e330939b6bc7dbc0ab8310b1e533fd`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/5cee54e707ea8afa5a44e6e185882f532ba6a2e2/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage72/run_stage72_UMB_21_direct_approve_iridis6.sh" -o "$HOME/run_stage72_UMB.sh" && test "$(git hash-object "$HOME/run_stage72_UMB.sh")" = "c7831ce788e330939b6bc7dbc0ab8310b1e533fd" && bash "$HOME/run_stage72_UMB.sh"
```

Execution state: code and launcher GitHub blob SHA verified; Stage72 has not yet been executed on IRIDIS6 at time of writing.

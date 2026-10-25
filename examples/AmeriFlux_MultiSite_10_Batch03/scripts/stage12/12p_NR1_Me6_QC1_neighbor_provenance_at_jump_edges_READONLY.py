#!/usr/bin/env python3
"""Stage12p: source-provenance diagnosis of 76 sides of 38 VPD jump holds.

Inputs: SHA-signed Stage12o and Stage12n research reports, original
source-time edge identities. Stage12o proved 71/76 neighboring VPD
sides were original VPD_F_QC1; only 39/71 numerically matched preserved
Stage12e VPD. Determine the *type* of the other 32 differences:
  both source VPD_F and Stage12e VPD finite but different;
  only original FLUXMET finite; only Stage12e finite; both absent.
Also compare original versus earlier accepted Stage12e versus later
final Stage12g VPD to the same originally rejected candidate.
An original source QC1 flag means not an independent QC0 measurement;
a numerical source discrepancy alone cannot justify changing the
originally predeclared >4 hPa VPD-jump rejection.

This script NEVER reconstructs exact pre-rejection Stage12g chronology;
Stage12g may have rejected two neighboring candidate values, and
Stage12o records only preserved final neighbor VPD.

--self-test: synthetic exhaustive source states and regression counts
--check: full signed original Stage12o/Stage12n receipt and source IDs,
         numerical edge comparison, zero writes.
--run: new report-only isolated SHA-receipted tables. No forcing, source
       measurements, clock, physics threshold, CIME or Slurm mutation.
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12p-v1-20261025-NR1-Me6-VPD-QC1-neighbor-provenance"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
O=ROOT/"reports/stage12o_original_QC0_T_episodes_and_QC1_VPD_edges_20261025T090451Z_a15453b8"
N=ROOT/"reports/stage12n_NR1_Me6_original_T_VPD_QC_and_companion_TA_ERA_20261025T085220Z_39e37c1b"
O_FILES={
  "86_original_QC0_T_persistence_events.csv",
  "76_original_VPD_neighbor_QC_provenance.csv",
  "six_site_year_hold_reason_episode_summary.csv",
  "original_VPD_neighbor_QC1_vs_stage12e_source_summary.csv",
  "three_year_QC0_tower_native_TA_ERA_year_context.csv",
  "SCIENCE_HOLD.md"
}
N_FILES={
  "86_held_original_source_T_and_VPD_QC.csv",
  "held_source_event_immediate_native_neighbors.csv",
  "held_source_T_by_site_year_reason_and_QC.csv",
  "38_original_jump_hold_neighbor_QC_summary.csv",
  "three_year_original_TA_F_QC0_companion_TA_ERA_context.csv",
  "SCIENCE_HOLD.md"
}
KEYS=["site","held_native_key","neighbor_native_key","neighbor_side"]
C_RAW="original_FLUXMET_VPD_F_hPa"
C_E="original_stage12e_repaired_neighbor_VPD_USE_hPa"
C_G="final_stage12g_neighbor_VPD_USE_hPa"
C_C="held_rejected_hypothetical_VPD_hPa"
THRESHOLD=4.

def file(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Unsigned missing or symlinked source: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()
def receipt(folder,name,expected_version,files):
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Signed research folder missing: "+str(folder))
    r=json.loads(file(folder/name).read_text())
    if r.get("version")!=expected_version or set(r.get("output_SHA256",{}))!=files:
        raise ValueError("Previous fixed scientific report receipt differs")
    for fn,expected in r["output_SHA256"].items():
        if sha(folder/fn)!=expected:
            raise ValueError("Original signed source report file differs: "+fn)
    if (r.get("Postv5_approved")!=0 or r.get("DATM_ready")!=0 or
        r.get("spinup_authorized")!=0):
        raise ValueError("Upstream production release unexpectedly changed")
    return r
def provenance(a,b):
    if np.isfinite(a) and np.isfinite(b):
        return "BOTH_FINITE_MATCH" if abs(a-b)<=1e-7 else "BOTH_FINITE_DIFFER"
    if np.isfinite(a):
        return "RAW_ONLY_FINITE"
    if np.isfinite(b):
        return "STAGE12E_ONLY_FINITE"
    return "BOTH_MISSING"
def full_diff(a,b):
    if np.isfinite(a) and np.isfinite(b):return abs(a-b)
    return np.nan
def selftest():
    assert provenance(2.,2.)=="BOTH_FINITE_MATCH"
    assert provenance(2.,2.01)=="BOTH_FINITE_DIFFER"
    assert provenance(2.,np.nan)=="RAW_ONLY_FINITE"
    assert provenance(np.nan,2.)=="STAGE12E_ONLY_FINITE"
    assert provenance(np.nan,np.nan)=="BOTH_MISSING"
    assert np.isnan(full_diff(np.nan,3.))
    assert full_diff(5.,1.)==THRESHOLD
    assert len(O_FILES)==6 and len(N_FILES)==6
    print("STAGE12P SELF-TEST PASS: all QC1 raw-vs-Stage12e origin classes, 76 sides, 38 holds, no writes",flush=True)
def load_inputs():
    r_o=receipt(O,"stage12o_science_only_SHA_receipt.json",
                "batch03-stage12o-v1-20261025-source-QC0-T-episode-QC1-VPD-edges",O_FILES)
    r_n=receipt(N,"stage12n_original_source_QC_companion_T_SHA_receipt.json",
                "batch03-stage12n-v1-20261025-NR1-Me6-original-QC-companion-T",N_FILES)
    if (r_o.get("original_Stage12n_SHA256")!=sha(
            N/"stage12n_original_source_QC_companion_T_SHA_receipt.json")
        or r_o.get("original_86_holds_unchanged") is not True
        or r_o.get("original_71_QC1_and_5_QC0_neighbour_sides") is not True
        or r_o.get("new_humidity_repair_candidates")!=0
        or r_o.get("original_tower_T_P_clock_unchanged") is not True
        or r_n.get("original_86_science_holds_unmodified") is not True
        or r_n.get("original_source_time_T_P_unmodified") is not True
        or r_n.get("new_humidity_repairs")!=0):
        raise ValueError("Stage12o/Stage12n scientific source hold policy changed")
    a=pd.read_csv(file(O/"76_original_VPD_neighbor_QC_provenance.csv"),
                  dtype={"held_native_key":str,"neighbor_native_key":str})
    b=pd.read_csv(file(N/"held_source_event_immediate_native_neighbors.csv"),
                  dtype={"held_native_key":str,"neighbor_native_key":str})
    b=b.loc[b.held_reason.eq("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA")].copy()
    c=pd.read_csv(file(O/"86_original_QC0_T_persistence_events.csv"),
                  dtype={"native_key":str})
    if (len(a)!=76 or len(b)!=76 or len(c)!=86 or
        len(c.loc[c.prior_source_hold_reason.eq("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA")])!=38 or
        a.duplicated(KEYS).any() or b.duplicated(KEYS).any() or
        not a.original_FLUXMET_VPD_F_QC.isin(["QC0","QC1"]).all()):
        raise ValueError("Exact 38 original VPD jump events / 76 reference sides changed")
    if (len(a.loc[a.original_FLUXMET_VPD_F_QC.eq("QC0")])!=5 or
        len(a.loc[a.original_FLUXMET_VPD_F_QC.eq("QC1")])!=71 or
        int(a.loc[a.original_FLUXMET_VPD_F_QC.eq("QC1"),
             "original_FLUXMET_VPD_F_matches_prior_shadow_finite"].sum())!=39):
        raise ValueError("Signed Stage12o QC1/0 and source-match 71/5/39 counts changed")
    # Source ledger join is one-to-one; fail closed if any original
    # held source identity or native neighbor clock differs.
    merged=a.merge(b[KEYS+[
      "original_FLUXMET_neighbor_VPD_F_hPa",
      "original_Stage12e_neighbor_VPD_USE_hPa",
      "final_Stage12g_neighbor_VPD_USE_hPa",
      "held_rejected_hypothetical_VPD_hPa"]],
      on=KEYS,how="outer",validate="one_to_one",indicator=True)
    if len(merged)!=76 or not merged._merge.eq("both").all():
        raise ValueError("Stage12o and Stage12n signed native neighbor identity differs")
    for original,from_n in (
       (C_RAW,"original_FLUXMET_neighbor_VPD_F_hPa"),
       (C_E,"original_Stage12e_neighbor_VPD_USE_hPa"),
       (C_G,"final_Stage12g_neighbor_VPD_USE_hPa")):
        lhs=pd.to_numeric(merged[original],errors="coerce").to_numpy(dtype=float)
        rhs=pd.to_numeric(merged[from_n],errors="coerce").to_numpy(dtype=float)
        if not np.allclose(lhs,rhs,atol=1e-7,rtol=0,equal_nan=True):
            raise ValueError("Original Stage12o/native Stage12n neighbor source VPD differs: "+original)
    return merged,r_o

def evaluate():
    df,r=load_inputs()
    for col in (C_RAW,C_E,C_G,C_C):
        df[col]=pd.to_numeric(df[col],errors="coerce")
    df["source_origin_class"]=[
       provenance(a,b) for a,b in zip(df[C_RAW],df[C_E])]
    df["absolute_RAW_vs_Stage12e_hPa"]=[
       full_diff(a,b) for a,b in zip(df[C_RAW],df[C_E])]
    df["absolute_candidate_vs_RAW_hPa"]=[
       full_diff(a,b) for a,b in zip(df[C_C],df[C_RAW])]
    df["absolute_candidate_vs_Stage12e_hPa"]=[
       full_diff(a,b) for a,b in zip(df[C_C],df[C_E])]
    df["absolute_candidate_vs_final_Stage12g_hPa"]=[
       full_diff(a,b) for a,b in zip(df[C_C],df[C_G])]
    df["absolute_Stage12e_vs_final_Stage12g_hPa"]=[
       full_diff(a,b) for a,b in zip(df[C_E],df[C_G])]
    df["candidate_jump_vs_RAW_gt4hPa"]=df.absolute_candidate_vs_RAW_hPa.gt(THRESHOLD)
    df["candidate_jump_vs_Stage12e_gt4hPa"]=df.absolute_candidate_vs_Stage12e_hPa.gt(THRESHOLD)
    df["candidate_jump_vs_final_gt4hPa"]=df.absolute_candidate_vs_final_Stage12g_hPa.gt(THRESHOLD)
    # Unknown references are explicitly UNKNOWN, never counted as passed.
    df["RAW_jump_test_possible"]=df.absolute_candidate_vs_RAW_hPa.notna()
    df["Stage12e_jump_test_possible"]=df.absolute_candidate_vs_Stage12e_hPa.notna()
    df["final_jump_test_possible"]=df.absolute_candidate_vs_final_Stage12g_hPa.notna()
    df["model_release_approved"]=False
    qc1=df.loc[df.original_FLUXMET_VPD_F_QC.eq("QC1")].copy()
    if (len(qc1)!=71 or
        int(qc1.source_origin_class.eq("BOTH_FINITE_MATCH").sum())!=39 or
        int(qc1.source_origin_class.ne("BOTH_FINITE_MATCH").sum())!=32):
        raise ValueError("Original 39-of-71 QC1 agreement / 32 differences did not reproduce")
    # Every source member must still belong to one original hold.
    events=df.groupby(["site","held_native_key"],dropna=False).agg(
        sides=("neighbor_side","size"),
        QC0_sides=("original_FLUXMET_VPD_F_QC",
                   lambda x:int(x.eq("QC0").sum())),
        QC1_sides=("original_FLUXMET_VPD_F_QC",
                   lambda x:int(x.eq("QC1").sum())),
        source_differing_or_missing_sides=("source_origin_class",
                   lambda x:int(x.ne("BOTH_FINITE_MATCH").sum())),
        both_finite_source_difference_sides=("source_origin_class",
                   lambda x:int(x.eq("BOTH_FINITE_DIFFER").sum())),
        rejected_candidate_gt4_from_RAW_sides=("candidate_jump_vs_RAW_gt4hPa","sum"),
        rejected_candidate_gt4_from_Stage12e_sides=("candidate_jump_vs_Stage12e_gt4hPa","sum"),
        rejected_candidate_gt4_from_final_sides=("candidate_jump_vs_final_gt4hPa","sum")
        ).reset_index()
    if len(events)!=38 or not events.sides.eq(2).all():
        raise ValueError("Original exact 38 VPD jump held source-time identities lost")
    agg=df.groupby(
        ["site","original_FLUXMET_VPD_F_QC","source_origin_class"],
        as_index=False,dropna=False).agg(
        adjacent_source_sides=("held_native_key","size"),
        raw_jump_possible_sides=("RAW_jump_test_possible","sum"),
        stage12e_jump_possible_sides=("Stage12e_jump_test_possible","sum"),
        final_jump_possible_sides=("final_jump_test_possible","sum"),
        candidate_raw_absjump_gt4_sides=("candidate_jump_vs_RAW_gt4hPa","sum"),
        candidate_stage12e_absjump_gt4_sides=("candidate_jump_vs_Stage12e_gt4hPa","sum"),
        candidate_final_absjump_gt4_sides=("candidate_jump_vs_final_gt4hPa","sum"))
    if agg.adjacent_source_sides.sum()!=76:
        raise ValueError("76 original VPD source neighbor sides missing from summary")
    duplicates=df.groupby(["site","neighbor_native_key"],as_index=False).agg(
        reference_side_occurrences=("held_native_key","size"),
        original_QC_classes=("original_FLUXMET_VPD_F_QC",lambda x:",".join(sorted(set(x)))),
        source_classifications=("source_origin_class",lambda x:",".join(sorted(set(x)))))
    duplicates=duplicates.loc[duplicates.reference_side_occurrences.gt(1)]
    return df,agg,events,duplicates

def main():
    p=argparse.ArgumentParser(description=__doc__)
    a=p.add_mutually_exclusive_group(required=True)
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--check",action="store_true")
    a.add_argument("--run",action="store_true")
    options=p.parse_args()
    print("STAGE12P — VERIFIED QC1 VPD NEIGHBOR SOURCE / BOUNDARY PROVENANCE | "+VERSION,flush=True)
    selftest()
    if options.self_test:return
    cases,agg,events,duplicates=evaluate()
    print("\n========== EXACT QC1 SOURCE STATES AND VPD JUMP REFERENCES ==========",flush=True)
    print(agg.to_string(index=False),flush=True)
    print("\n========== UNIQUE 38 HELD EVENTS BY ORIGINAL QC1/QC0 REFERENCE SIDES ==========",flush=True)
    print(events.to_string(index=False),flush=True)
    print("\nSTAGE12P SUMMARY: original_38_jump_holds_preserved=TRUE "
          "original_76_neighbor_sides_preserved=TRUE "
          "QC1_sides=71 QC0_sides=5 QC1_original_RAW_vs_Stage12e_matches=39 "
          "QC1_RAW_vs_Stage12e_not_matched=32 "
          f"duplicate_neighbor_reference_source_times={len(duplicates)} "
          "new_source_or_forcing_repairs=0 "
          "original_T_P_clock_unchanged=TRUE "
          "Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if options.check:
        print("STAGE12P CHECK ONLY: no source, science report, forcing or model writes.",flush=True)
        return
    dest=ROOT/"reports"/("stage12p_NR1_Me6_QC1_VPD_neighbor_origin_and_jump_sensitivity_"+
           datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    outputs={
      "76_native_edge_rejected_candidate_RAW_vs_Stage12e_vs_final.csv":cases,
      "QC0_QC1_source_origins_and_reference_jump_statistics.csv":agg,
      "38_original_VPD_jump_science_hold_event_reference_summary.csv":events,
      "reused_original_neighbor_source_times.csv":duplicates
    }
    for name,table in outputs.items():
        table.to_csv(dest/name,index=False)
    (dest/"SCIENCE_HOLD.md").write_text(
       "SCIENCE HOLD: QC1 VPD_F and Stage12e prior VPD can be different "
       "for real, source-dependent reasons. Neither one is automatically "
       "ground truth; the 4hPa jump gate remains unchanged. These are "
       "76 neighbor SIDES of 38 native event HOLDS, not 76 independent "
       "measurements. Their Stage12g final-shadow neighbors may have "
       "been jointly rejected; exact original pre-rejection chronology "
       "is not reconstructed here. No original data, forcing or model "
       "writes. Post-v5, DATM and spinup are NOT authorised.\n")
    shas={name:sha(dest/name) for name in [*outputs,"SCIENCE_HOLD.md"]}
    receipt_data={"version":VERSION,
      "original_Stage12o_SHA256":sha(O/"stage12o_science_only_SHA_receipt.json"),
      "original_76_source_neighbors_unchanged":True,
      "original_38_VPD_jump_holds_unchanged":True,
      "original_86_T_or_VPD_holds_unchanged":True,
      "new_humidity_repair_candidates":0,
      "original_source_T_P_clock_unchanged":True,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":shas}
    (dest/"stage12p_QC1_source_provenance_SHA_receipt.json").write_text(
         json.dumps(receipt_data,indent=2)+"\n")
    print("STAGE12P READ-ONLY QC1 VPD REFERENCE ORIGIN REPORT DIR:",dest,flush=True)
    print("NO ORIGINAL EC DATA, STAGE12E/G/O OR MODEL INPUT WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12P STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Batch05 Stage15 — all 1750 native low-RH source events: provenance-first ledger.

Only existing Stage10 and Stage14 review artifacts are inputs. Validate original
ledger, join verified 240 bracketed-VPD risk tests and 27 measured formula tests.
Write NEW evidence CSV/JSON only. No sources, Stage10/14, forcing, model or Slurm
writes. No candidate is approved. This does not independently establish FLUXNET
native VPD or original RH provenance.
"""
import argparse,csv,json,math
from collections import Counter,defaultdict
from pathlib import Path

SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
EXPECTED={"US-UiD":0,"US-UMB":23,"US-UMd":15,"US-Var":62,
          "US-Vcm":509,"US-Vcp":629,"US-WCr":88,"US-Whs":1,
          "US-Wjs":401,"US-Wkg":22}
FQCS={"0":"MEASURED_VPD_QC0","1":"GOOD_MDS_VPD_QC1","2":"ERA_DOWNSCALED_VPD_QC2"}
ST10={"time","class","RH_derived_pct","RH_original_pct","TA_F_C","VPD_F_hPa",
      "TA_F_QC","VPD_F_QC","TA_MDS_C","VPD_MDS_hPa","TA_MDS_QC",
      "VPD_MDS_QC","TA_ERA_C","VPD_ERA_hPa","MDS_pair_physics",
      "ERA_pair_physics","left_measured_anchor_time",
      "right_measured_anchor_time","interpolated_measured_vpd_hPa",
      "interpolation_diagnostic","SCIENCE_APPROVAL"}
TRIAL={"site","native_time","source_T_C","source_VPD_hPa",
       "hypothetical_interp_VPD_hPa","candidate_minus_original_hPa",
       "science_class","magnitude_band","science_status"}
MEASURED={"site","native_time","source_T_C","source_VPD_hPa",
          "original_RH_pct","magnus_water_RH_pct","buck_water_RH_pct",
          "tetens_water_RH_pct","buck_nonnegative","tetens_nonnegative",
          "science_status"}
COLS=("site","time","source_class","reason_rank","classification",
      "RH_derived_water_pct","RH_original_pct","original_RH_missing",
      "TA_F_C","VPD_F_hPa","TA_F_QC","VPD_F_QC",
      "TA_MDS_QC","VPD_MDS_QC","MDS_pair_physics","ERA_pair_physics",
      "interpolation_status","Stage14_interpolation_hPa",
      "Stage14_candidate_minus_original_hPa","Stage14_magnitude_band",
      "Stage14_measured_Buck_RH_pct","Stage14_measured_Tetens_RH_pct",
      "has_Stage12_priority_review","science_status","next_evidence_needed")
def number(value):
    try:
        x=float(value)
        return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
    except (ValueError,TypeError):
        return None
def saturation(t):
    return 6.112*math.exp(17.67*t/(243.5+t)) if t is not None and -80<=t<=60 else None
def readcsv(path,fields):
    if not path.is_file() or path.is_symlink():raise ValueError("missing original review artifact "+str(path))
    with path.open(newline="",encoding="utf-8-sig") as f:
        rdr=csv.DictReader(f)
        if not fields.issubset(rdr.fieldnames or []):raise ValueError("missing CSV field in "+str(path))
        rows=list(rdr)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError("malformed existing CSV "+str(path))
        return rows
def read_json(path):
    if not path.is_file() or path.is_symlink():raise ValueError("missing review summary "+str(path))
    return json.loads(path.read_text(encoding="utf-8"))
def gate_reason(q,neg,era_class,trial):
    if q=="0":
        if neg: return "01_QC00_MEASURED_FORMULA_NEGATIVE","CHECK_SENSOR_OR_DERIVATION_ZERO_RH_AND_NATIVE_VPD_FORMULA"
        return "03_QC00_MEASURED_EXTREME_LOW","CHECK_MEASURED_HUMIDITY_EXTREME_AND_NATIVE_VPD_FORMULA"
    if era_class=="ERA_INTERNAL_NONPHYSICAL":
        return "02_ERA_PAIR_INTERNAL_NONPHYSICAL","VERIFY_ERA_REFERENCE_T_VPD_AND_NATIVE_RELEASE_CONVERSION"
    if trial is not None and abs(number(trial["candidate_minus_original_hPa"]))>10:
        return "04_LARGE_BRACKETED_CHANGE","VERIFY_TOWER_BEFORE_AFTER_AND_EXTERNAL_MET_NOT_AUTOINTERPOLATE"
    if era_class=="ERA_E_WITH_TOWER_T_NOT_FEASIBLE":
        return "05_ERA_TOWER_MIX_UNPHYSICAL","COMPARE_INDEPENDENT_MET_AND_PAIRED_VAPOUR_PRESSURE"
    if q=="1":
        return "06_GOOD_MDS_VPD_HUMIDITY_REVIEW","CHECK_MDS_VPD_SOURCE_AND_TOWER_T_PROVENANCE"
    return "07_ERA_VPD_HUMIDITY_REVIEW","CHECK_ERA_VPD_WITH_ERA_T_AND_INDEPENDENT_MET"
def match_sample(site,source,other):
    if abs(number(source["TA_F_C"])-number(other["source_T_C"]))>0.002:
        raise ValueError("Stage14 vs Stage10 source TA disagreement "+site)
    if abs(number(source["VPD_F_hPa"])-number(other["source_VPD_hPa"]))>0.002:
        raise ValueError("Stage14 vs Stage10 source VPD disagreement "+site)
def review(stage10_dir,stage14_dir):
    stage10_summary=read_json(stage10_dir/"audit_summary.json")
    stage14_summary=read_json(stage14_dir/"stage14_summary.json")
    if set(stage10_summary.get("sites",{}))!=set(SITES):
        raise ValueError("Stage10 not the exact 10-site cohort")
    if stage14_summary.get("status")!="NO_REPAIR_APPROVED":
        raise ValueError("Stage14 scientific approval marker changed")
    if stage14_summary.get("total_priority")!=382 or stage14_summary.get("original_context_rows")!=4966:
        raise ValueError("Stage14 source context counts changed")
    if not stage14_summary.get("formulas_are_sensitivity_tests_not_verified_source_methods"):
        raise ValueError("Stage14 source formula provenance guard missing")
    trial_rows=readcsv(stage14_dir/"stage14_all_240_bracketed_risk.csv",TRIAL)
    measured_rows=readcsv(stage14_dir/"stage14_27_measured_saturation_formulas.csv",MEASURED)
    if len(trial_rows)!=240 or len(measured_rows)!=27:
        raise ValueError("Stage14 expected 240 bracketed and 27 measured")
    trials={}; measured={}
    all_counts=Counter(); site_counts=defaultdict(Counter)
    for row in trial_rows:
        key=(row["site"],row["native_time"])
        if key in trials or key[0] not in SITES:raise ValueError("duplicate/non-cohort Stage14 bracketed")
        if row["science_status"]!="HOLD_NOT_APPROVED":
            raise ValueError("Stage14 trial unexpectedly approved")
        band=row["magnitude_band"]
        d=number(row["candidate_minus_original_hPa"])
        if d is None or band not in ("LE1","GT1_TO_5","GT5_TO_10","GT10"):
            raise ValueError("Stage14 trial magnitude bad")
        expect="GT10" if abs(d)>10 else ("GT5_TO_10" if abs(d)>5 else
           ("GT1_TO_5" if abs(d)>1 else "LE1"))
        if band!=expect:raise ValueError("Stage14 candidate magnitude band mismatch")
        all_counts["trial_band_"+band]+=1
        if row["science_class"]=="MATH_FEASIBLE_UNAPPROVED":
            all_counts["trial_feasible"]+=1
        elif row["science_class"]=="NONPHYSICAL_HOLD":
            all_counts["trial_nonphysical"]+=1
        else:raise ValueError("Stage14 unrecognised candidate status")
        trials[key]=row
    for row in measured_rows:
        key=(row["site"],row["native_time"])
        if key in measured or key[0] not in SITES:raise ValueError("duplicate/non-cohort Stage14 measured")
        if row["science_status"]!="HOLD_NOT_APPROVED":
            raise ValueError("Stage14 original measured data unexpectedly approved")
        measured[key]=row
        for formula in ("buck","tetens"):
            actual=int(row[formula+"_nonnegative"])
            if actual!=int(number(row[formula+"_water_RH_pct"])>=0):
                raise ValueError("Stage14 saturation sign is not reproducible")
            all_counts["measured_"+formula+"_nonnegative"]+=actual
    all_records=[]
    used_trials=set();used_measured=set()
    for site in SITES:
        rows=readcsv(stage10_dir/(site+"_low_RH_review.csv"),ST10)
        if len(rows)!=EXPECTED[site]:
            raise ValueError("Stage10 site low-RH count disagreement "+site)
        past=stage10_summary["sites"][site].get("counts",{})
        if past.get("events",0)!=len(rows):
            raise ValueError("Stage10 audit_summary source file rows disagreement "+site)
        seen=set()
        for row in rows:
            stamp=row["time"]
            if stamp in seen:raise ValueError("duplicate Stage10 source event "+site+" "+stamp)
            seen.add(stamp)
            k=(site,stamp)
            qta,qv=row["TA_F_QC"],row["VPD_F_QC"]
            if qta not in FQCS or qv not in FQCS:
                raise ValueError("unknown original consolidated QC")
            t,v=number(row["TA_F_C"]),number(row["VPD_F_hPa"])
            sat=saturation(t)
            if sat is None or v is None:raise ValueError("missing original T or VPD at "+str(k))
            RH=100*(1-v/sat)
            claimed=number(row["RH_derived_pct"])
            if claimed is None or abs(RH-claimed)>0.001 or RH>=1:
                raise ValueError("Stage10 source low RH could not be reproduced "+str(k))
            neg=RH<0
            if row["class"]!=("NEGATIVE" if neg else "NONNEGATIVE_UNDER_1PCT"):
                raise ValueError("Stage10 source event class mismatch "+str(k))
            if row["SCIENCE_APPROVAL"]!="HOLD_NOT_APPROVED":
                raise ValueError("original source event was silently approved "+str(k))
            trial=trials.get(k)
            mt=measured.get(k)
            interp=row["interpolation_diagnostic"]
            if interp not in ("UNAPPROVED_MATH_FEASIBLE","INTERPOLATION_NONPHYSICAL",
                              "NO_BOTH_QC0_ANCHORS_WITHIN_3H"):
                raise ValueError("unknown original bracket state")
            if (trial is not None)!=(interp in ("UNAPPROVED_MATH_FEASIBLE","INTERPOLATION_NONPHYSICAL")):
                raise ValueError("Stage14 vs Stage10 bracketed candidate membership mismatch "+str(k))
            if trial is not None:
                used_trials.add(k);match_sample(site,row,trial)
                if (trial["science_class"]=="MATH_FEASIBLE_UNAPPROVED")!=(
                    interp=="UNAPPROVED_MATH_FEASIBLE"):
                    raise ValueError("Stage14 bracket physics and Stage10 disagree")
                if interp=="UNAPPROVED_MATH_FEASIBLE":
                    cv=number(row["interpolated_measured_vpd_hPa"])
                    if cv is None or abs(cv-number(trial["hypothetical_interp_VPD_hPa"]))>0.0005:
                        raise ValueError("Stage14 vs Stage10 VPD interpolation disagreement")
            if (mt is not None)!=(qta=="0" and qv=="0" and neg):
                raise ValueError("Stage14 measured negative cohort mismatch "+str(k))
            if mt is not None:
                used_measured.add(k);match_sample(site,row,mt)
                original=number(row["RH_original_pct"])
                if original is None or abs(original-number(mt["original_RH_pct"]))>0.0001:
                    raise ValueError("Stage14 original RH measured mismatch "+str(k))
            era=row["ERA_pair_physics"]
            if era not in ("ERA_INTERNAL_NONPHYSICAL","ERA_E_WITH_TOWER_T_NOT_FEASIBLE",
                           "HYPOTHETICAL_ERA_VAPOUR_PAIR_FEASIBLE"):
                raise ValueError("unexpected scientific ERA-pair class "+str(k))
            rank,needed=gate_reason(qv,neg,era,trial)
            has_focus=(trial is not None or mt is not None or
                       era in ("ERA_INTERNAL_NONPHYSICAL","ERA_E_WITH_TOWER_T_NOT_FEASIBLE"))
            if qv=="2" and row["VPD_MDS_QC"] not in ("2","3"):
                raise ValueError("ERA QC2 alternative MDS QC is not 2/3 "+str(k))
            rec=dict.fromkeys(COLS,"")
            rec.update({"site":site,"time":stamp,"source_class":FQCS[qv],
                "reason_rank":rank,"classification":row["class"],
                "RH_derived_water_pct":row["RH_derived_pct"],
                "RH_original_pct":row["RH_original_pct"],
                "original_RH_missing":int(number(row["RH_original_pct"]) is None),
                "TA_F_C":row["TA_F_C"],"VPD_F_hPa":row["VPD_F_hPa"],
                "TA_F_QC":qta,"VPD_F_QC":qv,
                "TA_MDS_QC":row["TA_MDS_QC"],"VPD_MDS_QC":row["VPD_MDS_QC"],
                "MDS_pair_physics":row["MDS_pair_physics"],
                "ERA_pair_physics":era,"interpolation_status":interp,
                "Stage14_interpolation_hPa":(
                    trial["hypothetical_interp_VPD_hPa"] if trial is not None else ""),
                "Stage14_candidate_minus_original_hPa":(
                    trial["candidate_minus_original_hPa"] if trial is not None else ""),
                "Stage14_magnitude_band":(trial["magnitude_band"] if trial is not None else ""),
                "Stage14_measured_Buck_RH_pct":(
                    mt["buck_water_RH_pct"] if mt is not None else ""),
                "Stage14_measured_Tetens_RH_pct":(
                    mt["tetens_water_RH_pct"] if mt is not None else ""),
                "has_Stage12_priority_review":int(has_focus),
                "science_status":"HOLD_NOT_APPROVED","next_evidence_needed":needed})
            all_records.append(rec)
            all_counts["events"]+=1;all_counts["FQC_VPD_"+qv]+=1
            all_counts["NEGATIVE"]+=int(neg)
            all_counts["nonnegative_low"]+=int(not neg)
            all_counts["original_RH_missing"]+=int(number(row["RH_original_pct"]) is None)
            all_counts["Stage12_focus"]+=int(has_focus)
            all_counts["reason_"+rank]+=1
            site_counts[site]["events"]+=1
            site_counts[site]["source_"+FQCS[qv]]+=1
            site_counts[site]["reason_"+rank]+=1
    if set(trials)!=used_trials or set(measured)!=used_measured:
        raise ValueError("Stage14 priority source times not contained in exact Stage10 cohort")
    targets={"events":1750,"NEGATIVE":1559,"nonnegative_low":191,
             "FQC_VPD_0":119,"FQC_VPD_1":965,"FQC_VPD_2":666,
             "original_RH_missing":1605,"trial_feasible":229,
             "trial_nonphysical":11,"Stage12_focus":382,
             "measured_buck_nonnegative":1,"measured_tetens_nonnegative":1,
             "trial_band_GT10":51,"trial_band_GT5_TO_10":122,
             "trial_band_GT1_TO_5":42,"trial_band_LE1":25}
    for key,expected in targets.items():
        if all_counts[key]!=expected:
            raise ValueError("Original Batch05 Stage09/14 invariant "+key+" "
                             +str(all_counts[key])+" vs "+str(expected))
    return all_records,all_counts,site_counts
def selftest():
    assert gate_reason("0",True,"HYPOTHETICAL_ERA_VAPOUR_PAIR_FEASIBLE",None)[0].startswith("01")
    assert gate_reason("0",False,"HYPOTHETICAL_ERA_VAPOUR_PAIR_FEASIBLE",None)[0].startswith("03")
    assert gate_reason("1",True,"ERA_INTERNAL_NONPHYSICAL",None)[0].startswith("02")
    assert gate_reason("2",True,"ERA_E_WITH_TOWER_T_NOT_FEASIBLE",None)[0].startswith("05")
    assert saturation(10)>12
    print("STAGE15 SELF-TEST PASS | mutually exclusive VPD source, immutable science holds; NO WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage10-dir",type=Path)
    p.add_argument("--stage14-dir",type=Path)
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    if args.self_test:selftest();return
    if not args.stage10_dir or not args.stage14_dir or not args.output_dir:
        p.error("--stage10-dir --stage14-dir --output-dir required")
    src10=args.stage10_dir.expanduser().resolve()
    src14=args.stage14_dir.expanduser().resolve()
    dst=args.output_dir.expanduser().resolve()
    if not src10.is_dir() or not src14.is_dir():
        p.error("missing original Stage10/Stage14 review report directory")
    if dst.exists() or not dst.parent.is_dir() or any(
            dst==p or p in dst.parents or dst in p.parents for p in (src10,src14)):
        p.error("Stage15 report output must be NEW and separate from existing reports")
    rows,stats,by_site=review(src10,src14)
    dst.mkdir(exist_ok=False)
    with (dst/"stage15_all_1750_science_holds.csv").open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=COLS)
        w.writeheader();w.writerows(sorted(rows,key=lambda r:(r["reason_rank"],r["site"],r["time"])))
    metadata={"decision":"ALL_1750_HOLD_NOT_APPROVED",
              "basis":"Stage10 exact source SHA-audited CSV and Stage14 scientific sensitivity CSV",
              "native_timestamps":"unchanged tower local standard printed labels",
              "methods":"mathematical evidence triage; no independent sensor/ERA5-L verification",
              "summary":dict(stats),"sites":{s:dict(by_site[s]) for s in SITES}}
    with (dst/"stage15_summary.json").open("x",encoding="utf-8") as f:
        json.dump(metadata,f,indent=2,sort_keys=True)
    print("STAGE15 AGGREGATE",json.dumps(dict(stats),sort_keys=True),flush=True)
    for site in SITES:
        print("STAGE15 SITE",site,json.dumps(dict(by_site[site]),sort_keys=True),flush=True)
    print("STAGE15 SUMMARY sites=10/10 reviewed=1750 negative=1559 "
          "measured=119 good_MDS=965 ERA=666 approved=0 reports="+str(dst),flush=True)
    print("ONLY NEW REVIEW CSV/JSON; NO ORIGINAL, STAGE10/14, FORCING, MODEL OR SLURM WRITES")
if __name__=="__main__":main()

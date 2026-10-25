#!/usr/bin/env python3
"""Batch05 Stage14: NO-REPAIR independent saturation and VPD-trial risk review.

Only existing Stage12 evidence input. Exports new review CSV/JSON files; never
writes to original tower data, Stage10, Stage12, forcing, CIME or Slurm.
Math-feasible is not scientifically approved. Native RH is not proven independent.
"""
import argparse,csv,json,math
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timedelta
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
CATEGORIES={"BRACKETED_MATH_UNAPPROVED":229,"BRACKETED_NONPHYSICAL":11,
            "MEASURED_QC00_NEGATIVE":27,"ERA_PAIR_HOLD":170}
T_COLS={"site","target_time","priority_tags","TA_F_C","VPD_F_hPa",
        "TA_F_QC","VPD_F_QC","RH_derived_pct","left_anchor","right_anchor",
        "unapproved_interpolated_VPD","decision","ERA_pair_physics"}
C_COLS={"site","target_time","offset_half_hours","native_time",
        "target_reasons","TA_F_C","VPD_F_hPa","RH_original",
        "TA_F_QC","VPD_F_QC","at_target","at_left_anchor","at_right_anchor"}
def num(v):
    try:
        x=float(v)
        return x if math.isfinite(x) and x not in (-9999.,-6999.) else None
    except (ValueError,TypeError):return None
def saturation(t,formula="magnus"):
    if t is None or not -80<=t<=60:return None
    if formula=="magnus":return 6.112*math.exp(17.67*t/(t+243.5))
    if formula=="buck":return 6.1121*math.exp((18.678-t/234.5)*t/(257.14+t))
    if formula=="tetens":return 6.1078*10**(7.5*t/(237.3+t))
    raise ValueError("unknown RH screening formula")
def time(s):
    if len(s)!=12 or not s.isdigit():raise ValueError("invalid native HH time "+repr(s))
    return datetime.strptime(s,"%Y%m%d%H%M")
def readcsv(p,need):
    if not p.is_file() or p.is_symlink():raise ValueError("missing regular report "+str(p))
    with p.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        if not need.issubset(r.fieldnames or []):raise ValueError("Stage12 CSV schema mismatch "+str(p))
        rows=list(r)
        if any(None in row or any(x is None for x in row.values()) for row in rows):
            raise ValueError("malformed Stage12 CSV")
        return rows
def anchor(r):
    t,v,rh=num(r["TA_F_C"]),num(r["VPD_F_hPa"]),num(r["RH_original"])
    s=saturation(t)
    if s is None or v is None:return False
    derived=100*(1-v/s)
    return r["TA_F_QC"]==r["VPD_F_QC"]=="0" and 1<=derived<=100 and (
        rh is None or 0<=rh<=100 and abs(rh-derived)<=5)
def audit(targets,contexts):
    windows=defaultdict(dict)
    for row in contexts:
        k=(row["site"],row["target_time"])
        step=int(row["offset_half_hours"])
        if step not in range(-6,7) or step in windows[k]:
            raise ValueError("bad or repeated context half-hour offset")
        if time(row["native_time"])!=time(k[1])+timedelta(minutes=30*step):
            raise ValueError("printed native source time mismatch")
        windows[k][step]=row
    seen=set();total=Counter();sites=defaultdict(Counter);trials=[];measured=[]
    for target in targets:
        site,stamp=target["site"],target["target_time"]
        key=(site,stamp)
        if site not in SITES or key in seen:raise ValueError("wrong or duplicate station/timestamp")
        seen.add(key)
        context=windows.get(key,{})
        if set(context)!=set(range(-6,7)):raise ValueError("expected 13 source HH "+str(key))
        center=context[0]
        if target["decision"]!="HOLD_MANUAL_REVIEW_ONLY" or center["at_target"]!="1":
            raise ValueError("science guard or center flag failed")
        if center["target_reasons"]!=target["priority_tags"]:
            raise ValueError("Stage12 context category mismatch")
        t,v=num(center["TA_F_C"]),num(center["VPD_F_hPa"])
        s=saturation(t)
        if s is None or v is None:raise ValueError("source center TA or VPD missing")
        if num(target["TA_F_C"]) is None or num(target["VPD_F_hPa"]) is None:
            raise ValueError("target TA or VPD missing")
        if abs(t-num(target["TA_F_C"]))>0.002 or abs(v-num(target["VPD_F_hPa"]))>0.002:
            raise ValueError("target and original source value disagree")
        if target["TA_F_QC"]!=center["TA_F_QC"] or target["VPD_F_QC"]!=center["VPD_F_QC"]:
            raise ValueError("target original QC mismatch")
        rh=100*(1-v/s)
        if num(target["RH_derived_pct"]) is None or abs(rh-num(target["RH_derived_pct"]))>0.001 or rh>=1:
            raise ValueError("original water RH could not be reproduced")
        reasons=target["priority_tags"].split("|")
        if len(set(reasons))!=len(reasons) or not set(reasons).issubset(CATEGORIES):
            raise ValueError("unrecognised Stage12 science priority reason")
        for reason in reasons:total[reason]+=1;sites[site][reason]+=1
        total["priority_unique"]+=1;sites[site]["priority_unique"]+=1
        if "ERA_PAIR_HOLD" in reasons and target["ERA_pair_physics"] not in (
            "ERA_INTERNAL_NONPHYSICAL","ERA_E_WITH_TOWER_T_NOT_FEASIBLE"):
            raise ValueError("ERA hold science label mismatch")
        if "MEASURED_QC00_NEGATIVE" in reasons:
            if target["TA_F_QC"]!="0" or target["VPD_F_QC"]!="0" or rh>=0:
                raise ValueError("original measured negative tag unjustified")
            rh0=num(center["RH_original"])
            out={"site":site,"native_time":stamp,"source_T_C":t,"source_VPD_hPa":v,
                 "original_RH_pct":rh0,
                 "native_minus_magnus_pp":round(rh0-rh,8) if rh0 is not None else "",
                 "science_status":"HOLD_NOT_APPROVED"}
            for formula in ("magnus","buck","tetens"):
                r=100*(1-v/saturation(t,formula))
                out[formula+"_water_RH_pct"]=round(r,8)
                out[formula+"_nonnegative"]=int(r>=0)
                out[formula+"_abs_native_disagreement_pp"]=(
                    round(abs(r-rh0),8) if rh0 is not None else "")
                total["QC00_"+formula+"_nonnegative"]+=int(r>=0)
            measured.append(out)
        if "BRACKETED_MATH_UNAPPROVED" in reasons or "BRACKETED_NONPHYSICAL" in reasons:
            center_time=time(stamp)
            left,right=time(target["left_anchor"]),time(target["right_anchor"])
            if not (left<center_time<right and center_time-left<=timedelta(hours=3)
                    and right-center_time<=timedelta(hours=3)):
                raise ValueError("source original measured bracket outside +/-3h")
            li=int((left-center_time).total_seconds()/1800)
            ri=int((right-center_time).total_seconds()/1800)
            lrow,rrow=context[li],context[ri]
            if not anchor(lrow) or not anchor(rrow):
                raise ValueError("not an acceptable original QC0/0 source anchor")
            if lrow["at_left_anchor"]!="1" or rrow["at_right_anchor"]!="1":
                raise ValueError("source measured anchor label mismatch")
            vl,vr=num(lrow["VPD_F_hPa"]),num(rrow["VPD_F_hPa"])
            interp=vl+(vr-vl)*((center_time-left)/(right-left))
            model=num(target["unapproved_interpolated_VPD"])
            feasible=0<=interp<=s
            if "BRACKETED_MATH_UNAPPROVED" in reasons:
                if not feasible or model is None or abs(interp-model)>0.0005:
                    raise ValueError("Stage12 math-feasible candidate failed reproducibility")
                total["interp_reverified"]+=1
            elif feasible or model is not None:
                raise ValueError("Stage12 nonphysical interpolation improperly classified")
            delta=interp-v; change=abs(delta)
            band=("GT10" if change>10 else "GT5_TO_10" if change>5 else
                  "GT1_TO_5" if change>1 else "LE1")
            total["interp_magnitude_"+band]+=1
            sites[site]["interp_magnitude_"+band]+=1
            trials.append({"site":site,"native_time":stamp,
               "science_class":"MATH_FEASIBLE_UNAPPROVED" if feasible else "NONPHYSICAL_HOLD",
               "source_T_C":t,"source_VPD_hPa":v,"source_water_RH_pct":round(rh,7),
               "anchor_gap_hours":(right-left).total_seconds()/3600,
               "left_source_VPD_hPa":vl,"right_source_VPD_hPa":vr,
               "hypothetical_interp_VPD_hPa":round(interp,7),
               "candidate_minus_original_hPa":round(delta,7),
               "magnitude_band":band,"ERA_pair_physics":target["ERA_pair_physics"],
               "science_status":"HOLD_NOT_APPROVED"})
    if seen!=set(windows):raise ValueError("orphan original context data")
    return trials,measured,total,sites
def selftest():
    t=11.686;v=13.731
    assert 100*(1-v/saturation(t,"magnus"))<0
    assert 100*(1-v/saturation(t,"buck"))>0
    assert 100*(1-v/saturation(t,"tetens"))>0
    assert saturation(15,"buck")>0
    print("STAGE14 SELF-TEST PASS | Magnus/Buck/Tetens near-boundary water RH; NO WRITES")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--stage12-dir",type=Path)
    p.add_argument("--output-dir",type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if not a.stage12_dir or not a.output_dir:p.error("--stage12-dir and --output-dir required")
    root=a.stage12_dir.expanduser().resolve()
    dest=a.output_dir.expanduser().resolve()
    if dest.exists() or dest==root or root in dest.parents or dest in root.parents:
        p.error("report-only output must not exist and cannot be within Stage12 reports")
    if not dest.parent.is_dir():p.error("Stage14 output parent must exist")
    targets=readcsv(root/"stage12_priority_targets.csv",T_COLS)
    context=readcsv(root/"stage12_original_native_context.csv",C_COLS)
    summary=root/"stage12_summary.json"
    if not summary.is_file() or summary.is_symlink():raise ValueError("Stage12 summary missing")
    meta=json.loads(summary.read_text(encoding="utf-8"))
    if (meta.get("decision")!="ALL_CANDIDATES_UNAPPROVED"
        or meta.get("priority_unique_events")!=382
        or meta.get("context_rows")!=4966):
        raise ValueError("Stage12 original report identity/approval mismatch")
    trial,measured,total,by_site=audit(targets,context)
    if (len(targets),len(context),len(trial),len(measured))!=(382,4966,240,27):
        raise ValueError("Stage12 source cohort has changed")
    if any(total[k]!=v for k,v in CATEGORIES.items()) or total["interp_reverified"]!=229:
        raise ValueError("Stage13 original category and interpolation guard mismatch")
    trial.sort(key=lambda r:-abs(r["candidate_minus_original_hPa"]))
    dest.mkdir(exist_ok=False)
    for name,rows in (("stage14_all_240_bracketed_risk.csv",trial),
                      ("stage14_27_measured_saturation_formulas.csv",measured)):
        with (dest/name).open("x",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    result={"status":"NO_REPAIR_APPROVED","total_priority":382,
       "original_context_rows":4966,"formulas_are_sensitivity_tests_not_verified_source_methods":True,
       "counts":dict(total),"by_site":{s:dict(by_site[s]) for s in SITES}}
    with (dest/"stage14_summary.json").open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True)
    print("STAGE14 AGGREGATE",json.dumps(result["counts"],sort_keys=True),flush=True)
    print("STAGE14 VPD_INTERPOLATION_TOP20",json.dumps(trial[:20],sort_keys=True),flush=True)
    print("STAGE14 MEASURED_FORMULA_27",json.dumps(measured,sort_keys=True),flush=True)
    print("STAGE14 SUMMARY sites=10/10 priority=382 context=4966 bracketed=229 nonphysical_bracketed=11 measured=27 approved=0 reports="+str(dest),flush=True)
    print("ONLY NEW DIAGNOSTIC CSV/JSON; NO ORIGINAL/STAGE10/STAGE12/FORCING/MODEL/SLURM WRITES")
if __name__=="__main__":main()

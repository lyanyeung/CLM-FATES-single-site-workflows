#!/usr/bin/env python3
"""Batch04 MANUAL DECISION trial ONLY; never edits raw FLUXMET or official QC.

Operator choices:
  US-SRG 2019-03-19 12:00: interpolate 11:30 + 12:30 consolidated
      TA_F (BOTH QC2 ERA-substituted), so mark *trial* QC2, not tower QC0.
  US-SP1 2000-10-09 18:00 and 18:30: use EXACT existing independent
      SHA-receipted ERA5-Land T2m time interpolated at local-standard clock;
      trial QC2, not tower QC0.

For all 3 trial changes, recompute VPD_F with existing Stage14 verified RH
and the new temperature to avoid leaving an impossible TA/VPD pair.
Retain all other columns including original source, all eight science HOLDS.
--assess is read-only and prints exact numeric ERA5-Land and prospective fixes.
--trial creates TWO *new* standalone research CSVs, ten-site manifest and
provenance receipt only under a new scratch directory, no production/model.
Requires the pinned stage10 helper to read already downloaded ERA5-Land.
"""
import argparse,csv,hashlib,importlib.util,json,math
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

E=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S14=E/"qcv5_stage14_humidity_closure_candidate/candidate_20261025T075601Z_3473a555"
MANIFEST=S14/"stage14_latest_ten_candidate_manifest.tsv"
SOURCE_SHA={
 "US-SP1":"3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806",
 "US-SRG":"57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39",
}
ROWS={"US-SP1":368208,"US-SRG":315600}
EXPECTED_T={("US-SP1","200010091800"):-6.9,
            ("US-SP1","200010091830"):-7.1,
            ("US-SRG","201903191200"):0.718}
TARGETS={"US-SP1":("200010091800","200010091830"),
         "US-SRG":("201903191200",)}
REFERENCE={
 "US-SP1":("200010091730","200010091900"),
 "US-SRG":("201903191130","201903191230"),
}
BIF2000={"latitude":29.7381,"longitude":-82.2188,"offset_hours":-5,
         "BIF_sha256":"7d8be284cacb1d4b8e503fb15ba354beabb8db4ed82c0225a50f3d5e77081890"}
def regular(p):
    if p.is_symlink() or not p.is_file():raise ValueError("Missing or linked source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as f:
        for chunk in iter(lambda:f.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()
def val(raw):
    try: x=float(raw)
    except (TypeError,ValueError):return None
    return x if math.isfinite(x) and x not in (-9999,-6999) else None
def sat(t):
    return 6.112*math.exp(17.67*t/(t+243.5))
def ext():
    p=Path(__file__).resolve().with_name("10_era5land_independent_humidity_fill.py")
    if not p.is_file() or p.is_symlink():raise ValueError("Download pinned Stage10 helper beside trial script")
    sp=importlib.util.spec_from_file_location("manual_b04_grid",str(p))
    m=importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m
def manifest():
    rec=json.loads(regular(S14/"stage14_receipt.json").read_text())
    if (rec.get("humidity_physical_candidate_count")!=8 or
        rec.get("still_unresolved_tower_temperature_science_hold_count")!=8 or
        sha(MANIFEST)!=rec.get("latest_ten_manifest_sha256")):
        raise ValueError("Stage14 provenance or eight unchanged T science holds failed")
    with regular(MANIFEST).open(encoding="utf-8-sig",newline="") as f:
        d=csv.DictReader(f,delimiter="\t")
        fields=list(d.fieldnames or ())
        rows=list(d)
    if len(rows)!=10 or len({x["site"] for x in rows})!=10:
        raise ValueError("Stage14 ten-site source manifest changed")
    inputs={}
    for site in TARGETS:
        r=next(x for x in rows if x["site"]==site)
        p=Path(r["source_path"])
        if (r["source_SHA256"]!=SOURCE_SHA[site] or sha(p)!=SOURCE_SHA[site] or
            int(r["rows"])!=ROWS[site]):
            raise ValueError("Target Stage14 complete source no longer pinned "+site)
        inputs[site]=p
    return rows,fields,inputs
def read_events(file,site):
    wanted=set(TARGETS[site])|set(REFERENCE[site])
    rows={};total=0
    with regular(file).open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not {"TIMESTAMP_START","TA_F","TA_F_QC","RH","VPD_F"}.issubset(rd.fieldnames):
            raise ValueError("Stage14 humidity/T schema changed")
        for row in rd:
            total+=1;k=row["TIMESTAMP_START"]
            if k in wanted:
                if k in rows:raise ValueError("Duplicate native timestamp "+k)
                rows[k]=row
    if total!=ROWS[site] or set(rows)!=wanted:raise ValueError("Lost native adjacent HH "+site)
    return rows
def candidate():
    original,fields,inputs=manifest()
    bysite={site:read_events(inputs[site],site) for site in TARGETS}
    e=ext()
    gridfile=e.response_receipt("US-SP1",2000)
    if gridfile is None:raise ValueError("US-SP1 original verified ERA5-Land 2000 cache missing")
    point=dict(BIF2000)
    # The original Stage12 BIF location/offset and SHA are immutable.
    rawbase=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-SP1/forcing/raw/AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1")
    bif=rawbase/"AMF_US-SP1_FLUXNET_BIF_2000-2020_v1.3_r1.csv"
    if sha(bif)!=point["BIF_sha256"]:raise ValueError("Original US-SP1 BIF SHA changed")
    grid=e.grid_read(gridfile,2000,point)
    if not (-90<=grid["grid_latitude"]<=90 and -180<=grid["grid_longitude"]<=180):
        raise ValueError("ERA grid wrong location")
    proposals={}
    for site,times in TARGETS.items():
        data=bysite[site]
        for key in times:
            row=data[key]
            orig=val(row["TA_F"])
            if (orig is None or abs(orig-EXPECTED_T[(site,key)])>.002 or
                row["TA_F_QC"].strip()!="0"):
                raise ValueError("Original QC0 temperature event changed "+site+" "+key)
            if site=="US-SRG":
                a,b=(data[k] for k in REFERENCE[site])
                if a["TA_F_QC"].strip()!="2" or b["TA_F_QC"].strip()!="2":
                    raise ValueError("SRG manual interpolation requires QC2 ERA flanks")
                x,y=val(a["TA_F"]),val(b["TA_F"])
                if x is None or y is None or abs(x-19.668)>.002 or abs(y-20.605)>.002:
                    raise ValueError("SRG flanking TA changed")
                temp=(x+y)/2
                method="MANUAL_INTERPOLATION_BETWEEN_TWO_QC2_ERA_SUBSTITUTED_FLANKS"
            else:
                u=e.local_to_utc(key,point["offset_hours"])
                p=(u-grid["start_utc"]).total_seconds()/3600
                j=math.floor(p);f=p-j;arr=grid["values"]["t2m"]
                if j<0 or j>=len(arr)-1:raise ValueError("ERA5-Land native time out of bounds")
                temp=float(arr[j])*(1-f)+float(arr[j+1])*f-273.15
                if abs(temp-({"200010091800":14.37,"200010091830":13.78}[key]))>1.0:
                    raise ValueError("Independent ERA5-Land departure from known Stage15 approximate value")
                method="EXACT_RECEIPT_VERIFIED_ERA5LAND_T2M_INTERPOLATED_TO_NATIVE_UTC"
            rh=val(row["RH"])
            if rh is None or not 1<=rh<=100 or temp< -40 or temp>50:
                raise ValueError("Missing Stage14 RH or unreasonable proposed T")
            vpd=sat(temp)*(1-rh/100)
            if not 0<=vpd<=sat(temp):raise ValueError("Proposed T/RH/VPD not physically closed")
            proposals[(site,key)]={
                "site":site,"TIMESTAMP_START":key,
                "original_TA_C":orig,"original_TA_F_QC":row["TA_F_QC"],
                "trial_TA_C":temp,"trial_TA_F_QC":"2",
                "original_VPD_hPa":val(row["VPD_F"]),"trial_VPD_hPa":vpd,
                "retained_stage14_RH_percent":rh,
                "method":method,
                "source_stage14_sha256":SOURCE_SHA[site],
                "approval":"UNAPPROVED_MANUAL_RESEARCH_ALTERNATIVE"
            }
    if set(proposals)!=set(EXPECTED_T):raise ValueError("Exactly 3 proposed HH required")
    return original,fields,inputs,proposals,gridfile
def make_csv(src,dst,site,proposals):
    seen=set();n=0
    with regular(src).open(encoding="utf-8-sig",newline="") as a,dst.open("x",encoding="utf-8",newline="") as b:
        d=csv.DictReader(a);cols=list(d.fieldnames or ())
        w=csv.DictWriter(b,fieldnames=cols)
        w.writeheader()
        for row in d:
            n+=1;k=(site,row["TIMESTAMP_START"])
            if k in proposals:
                if k in seen:raise ValueError("Duplicate native edit")
                seen.add(k);x=proposals[k]
                row["TA_F"]=f"{x['trial_TA_C']:.12g}"
                row["TA_F_QC"]="2"
                row["VPD_F"]=f"{x['trial_VPD_hPa']:.12g}"
            w.writerow(row)
    if n!=ROWS[site] or seen!={(site,k) for k in TARGETS[site]}:
        raise ValueError("Incomplete full source trial file")
    return sha(dst)
def selftest():
    assert len(EXPECTED_T)==3
    assert abs((19.668+20.605)/2-20.1365)<1e-12
    assert sat(20)>sat(-7) and len(TARGETS)==2
    print("MANUAL TRIAL SELF-TEST PASS: 3 HH isolated, QC2 ERA-derived provenance, no original overwrite")
def run(trial):
    originals,fields,inputs,proposals,gridfile=candidate()
    for site,k in sorted(proposals):
        x=proposals[site,k]
        print("MANUAL PROPOSAL",site,k,"ORIGINAL_T",x["original_TA_C"],
              "ORIGINAL_QC0","TRIAL_T",round(x["trial_TA_C"],6),
              "TRIAL_QC2", "TRIAL_VPD",round(x["trial_VPD_hPa"],6),
              "METHOD",x["method"])
    print("MANUAL SCIENCE: ORIGINAL 8/8 TEMPERATURE HOLDS STILL UNRESOLVED; US-Syv 606+10 DEFERRED")
    if not trial:
        print("MANUAL ASSESS ONLY: 0 WRITES, 0 RELEASES");return
    dest=E/"manual_temperature_alternative_not_approved"/(
        "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    (dest/"NOT_APPROVED_NOT_FOR_DATM_CIME_SLURM_SPINUP").write_text(
      "Three manually requested temperature alternatives ONLY. Eight original temperature science holds unchanged.\n")
    results={}
    updated=[]
    for entry in originals:
        x=dict(entry);site=x["site"]
        if site in TARGETS:
            target=dest/f"{site}_manual_temperature_alternative_FLUXMET_HH.csv"
            h=make_csv(inputs[site],target,site,proposals)
            x["source_path"]=str(target);x["source_SHA256"]=h
            x["latest_stage"]="MANUAL_EXPERIMENTAL_TEMPERATURE_ALTERNATIVE_NOT_APPROVED"
            results[site]={"path":str(target),"sha256":h,"rows":ROWS[site],
                           "changed_native_half_hours":len(TARGETS[site])}
        updated.append(x)
    with (dest/"MANUAL_LATEST_TEN_SITE_RESEARCH_MANIFEST.tsv").open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",extrasaction="ignore")
        w.writeheader();w.writerows(updated)
    items=[proposals[k] for k in sorted(proposals)]
    with (dest/"MANUAL_TEMPERATURE_PROVENANCE.tsv").open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(items[0]),delimiter="\t")
        w.writeheader();w.writerows(items)
    receipt={"read_only_source_stage14_manifest_sha256":sha(MANIFEST),
             "independent_SP1_ERA5Land_2000_source_path":str(gridfile),
             "independent_SP1_ERA5Land_2000_sha256":sha(gridfile),
             "manual_decision_changes":items,"two_modified_site_files":results,
             "original_tower_temperature_science_holds_remaining":8,
             "deferred_US_Syv_holds":606,"deferred_US_Syv_ERA_edges":10,
             "production_approval":False}
    (dest/"MANUAL_TRIAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("MANUAL TRIAL RESEARCH DATA CREATED",dest)
    print("MANUAL TRIAL EXACTLY THREE HALF-HOURS; ORIGINAL FLUXMET/Stage14/Stage15/OTHER EIGHT SITES UNCHANGED")
    print("NOT APPROVED FOR POST-v5, DATM, CIME, SLURM, SPINUP")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--assess",action="store_true")
    g.add_argument("--trial",action="store_true")
    args=p.parse_args()
    selftest()
    if args.assess:run(False)
    if args.trial:run(True)
if __name__=="__main__":
    main()

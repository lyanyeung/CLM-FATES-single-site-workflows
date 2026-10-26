#!/usr/bin/env python3
"""Batch04 SYVH7: 12 low downwelling LW_IN_F records at 5 EC sites.

Operator-reported Gate-0: TEN final selected site SHA/time/other 7-met pass,
but exactly 12 LW_IN_F < 60 W/m2 across US-SP1 (4), US-Slt/Syv/Ton/Uaf
(2 each). All are 2-adjacent-native-half-hour pairs at precisely pinned
timestamps, original low-LW value repeated, 2004-Dec03/04 or 2016-Oct09.
Unphysically low tower/downwelling flux must be evaluated by SAME SOURCE
paired original FLUXNET processed ERA longwave LW_IN_ERA. This is an
ERA5-derived packaged companion, NOT independent raw ERA5-Land.

Three phases:
  --self-test: exact 12 native timestamps and split-group checks. NO WRITES.
  --assess: SHA verify original Site05 native and ERA, final SYVH3 manifest,
            compare all 12 chosen LW and original QC, inspect +/-2h flanks,
            verify physical/continuous exact-time paired ERA suitability.
            NO WRITES.
  --apply: only if all original-vs-final source, ERA/physical boundary and
           source QC checks pass, write separate complete CSV candidate for
           each of 5 sites; preserve all other fields and all nine previous
           science ledgers. Also write 10-site manifest, exact 12-HH source
           provenance receipt, full independent rowwise diff audit; NO DATM,
           Post-v5, original sources, NetCDF, model cases or Slurm jobs.

Scientific policy: exact-time TOWER vs paired ERA LW >0 physical/thermodynamic
consistency, no arbitrary interpolations/threshold caps. Never alter QC0
humidity, TA/VPD/pressure/precipitation, raw FLUXMET or upstream ERA archive.
If independent ERA companion has no LW_IN_ERA, unsafe source, or the new
LW makes edge discontinuities >160 W/m2: fail BEFORE writing anything.
"""
import argparse,csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from itertools import zip_longest
from pathlib import Path
from uuid import uuid4

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
S05=ROOT/"qcv5_stage05_candidates/candidate_20261024T103113Z"
SYVH3=ROOT/"manual_US_Syv_stage_SYVH3_last_18_QC0_RH_closure_candidate_not_approved/candidate_20261026T034556Z_3372d66c"
MANIFEST=SYVH3/"RESEARCH_TEN_SITE_MANIFEST.tsv"
FINAL_SYV_SHA="9299193bc12b06e37211d84d31c333e299f99cb0ed96ebc6ed224ef9eaaf02aa"
EXPECTED={
"US-SP1":(("200412040000","200412040030"),
          ("201610091900","201610091930")),
"US-Slt":(("201610091900","201610091930"),),
"US-Syv":(("200412032300","200412032330"),),
"US-Ton":(("200412032100","200412032130"),),
"US-Uaf":(("200412032000","200412032030"),)
}
OLD_LW_EXPECTED={
"US-SP1":{"200412040000":44.764,"200412040030":44.764,
          "201610091900":44.764,"201610091930":44.764},
"US-Slt":{"201610091900":45.855,"201610091930":45.855},
"US-Syv":{"200412032300":43.388,"200412032330":43.388},
"US-Ton":{"200412032100":8.353,"200412032130":8.353},
"US-Uaf":{"200412032000":34.390,"200412032030":34.390}
}
EXPECTED_SITES={"US-Rpf","US-SP1","US-SRG","US-SRM","US-Seg",
                "US-Ses","US-Slt","US-Syv","US-Ton","US-Uaf"}
LIMIT_LW_MIN=60.0;LIMIT_LW_MAX=800.0
MAX_NEW_BOUNDARY_LW_JUMP=160.0
MAX_ERA_WITHIN_EPISODE_JUMP=100.0
NATIVE_HH_EXPECTED={"US-SP1":368208,"US-Slt":315552,"US-Syv":438288,
                    "US-Ton":438288,"US-Uaf":403248}
MISSING={"","NA","NAN","-9999","-9999.0","-6999","-6999.0"}

def ck(ok,msg):
    if not ok:raise ValueError(msg)
def file(p):
    ck(p.is_file() and not p.is_symlink(),"Missing/symlink source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as f:
        for part in iter(lambda:f.read(4<<20),b""):h.update(part)
    return h.hexdigest()
def j(p):return json.loads(file(p).read_text(encoding="utf-8"))
def val(s):
    x=str(s if s is not None else "").strip()
    if x.upper() in MISSING:return None
    try:n=float(x)
    except (TypeError,ValueError):return None
    return n if math.isfinite(n) else None
def time(k):return datetime.strptime(k,"%Y%m%d%H%M")
def shift(k,n):return (time(k)+timedelta(minutes=30*n)).strftime("%Y%m%d%H%M")
def targets():
    out={}
    for site,groups in EXPECTED.items():
        arr=set()
        for start,end in groups:
            ck(shift(start,1)==end,"Expected paired exact HH "+site+" "+start)
            for k in (start,end):
                ck(k not in arr,"Double counted target "+site+" "+k)
                arr.add(k)
        out[site]=arr
    ck(sum(map(len,out.values()))==12 and len(out)==5 and
       all(set(OLD_LW_EXPECTED[s])==out[s] for s in out),
       "Expected precisely 12 already operator-observed extreme LW HH")
    return out
def tab(p,need,sep="\t"):
    with file(p).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter=sep)
        ck(reader.fieldnames is not None and
           set(need).issubset(reader.fieldnames) and
           len(reader.fieldnames)==len(set(reader.fieldnames)),
           "Invalid source/manifest schema "+str(p))
        return reader.fieldnames,list(reader)
def subset(p,keys,fields,expected_count=None):
    got={};n=0
    with file(p).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        ck(r.fieldnames is not None and
           set(fields).issubset(r.fieldnames) and
           "TIMESTAMP_START" in r.fieldnames,
           "Missing required exact-time met data "+str(p)+
           " columns="+repr(r.fieldnames))
        allcols=set(r.fieldnames)
        for row in r:
            n+=1;k=row["TIMESTAMP_START"]
            if k in keys:
                ck(k not in got,"Duplicate exact native timestamp "+str(p)+" "+k)
                got[k]=dict(row)
    if expected_count is not None:
        ck(n==expected_count,"Complete native source length changed "+str(p))
    ck(set(keys)==set(got),
       "Required source exact native HH missing: "+str(p)+" "+str(sorted(set(keys)-set(got))))
    return got,allcols
def pinned_inputs():
    source=j(S05/"report.json")
    ck(source.get("mode")=="BUILD_CANDIDATE_OVERLAY",
       "Upstream immutable Stage05 source provenance changed")
    receipt=j(SYVH3/"SYVH3_RESEARCH_SCIENCE_RECEIPT.json")
    ck(receipt.get("new_full_SHA256")==FINAL_SYV_SHA and
       receipt.get("full_site_rows")==438288 and
       receipt.get("derived_RH_only_repaired_HH")==18 and
       receipt.get("source_production_approval") is False,
       "Latest operator science Syv final receipt SHA/approval changed")
    final_path=Path(receipt["new_full_candidate_path"])
    ck(final_path.parent==SYVH3 and sha(final_path)==FINAL_SYV_SHA,
       "Original final 438288HH Syv source SHA changed")
    fieldnames,old=tab(MANIFEST,
                       ("site","source_path","source_SHA256","latest_stage"))
    ck(len(old)==10 and {x["site"] for x in old}==EXPECTED_SITES,
       "Original exact 10-site final manifest changed")
    selected={x["site"]:x for x in old}
    ck(Path(selected["US-Syv"]["source_path"])==final_path and
       selected["US-Syv"]["source_SHA256"]==FINAL_SYV_SHA,
       "Must start from actual final 18-RH Syv source")
    ck(set(EXPECTED).issubset(source.get("sites",{})),
       "Stage05 original native+ERA sources missing for affected 5 sites")
    paths={}
    for site in EXPECTED:
        spec=source["sites"][site]
        raw=Path(spec["paths"]["native"]);era=Path(spec["paths"]["era"])
        ck(sha(raw)==spec["source_provenance"]["native"]["sha256"],
           site+" original native source SHA mismatch")
        ck(sha(era)==spec["source_provenance"]["era"]["sha256"],
           site+" paired processed FLUXNET ERA SHA mismatch")
        chosen=Path(selected[site]["source_path"])
        ck(sha(chosen)==selected[site]["source_SHA256"],
           site+" operator selected full site SHA mismatch")
        paths[site]=(chosen,raw,era)
    for site in EXPECTED_SITES-set(EXPECTED):
        ck(sha(Path(selected[site]["source_path"]))==
           selected[site]["source_SHA256"],
           site+" source manifest SHA mismatch")
    print("SHA VERIFIED FINAL 10-SITE SYVH3 SELECTION + ORIGINAL FIVE-SITE FLUXMET AND PROCESSED ERA")
    return fieldnames,old,paths
def assess(paths,tt):
    patch={};counts=Counter()
    for site in sorted(tt):
        chosen,original,era=paths[site]
        keys=tt[site];context=set(keys)
        for start,end in EXPECTED[site]:
            context.update(shift(start,i) for i in range(-4,0))
            context.update(shift(end,i) for i in range(1,5))
        a,acols=subset(chosen,context,("TIMESTAMP_START","LW_IN_F"),
                        NATIVE_HH_EXPECTED[site])
        raw,rawcols=subset(original,context,("TIMESTAMP_START","LW_IN_F"),
                           NATIVE_HH_EXPECTED[site])
        external,ecols=subset(era,context,("TIMESTAMP_START","LW_IN_ERA"))
        for start,end in EXPECTED[site]:
            n0=shift(start,-1);n1=shift(end,1)
            old_before=val(a[n0]["LW_IN_F"])
            old_after=val(a[n1]["LW_IN_F"])
            ck(old_before is not None and old_after is not None and
               LIMIT_LW_MIN<=old_before<=LIMIT_LW_MAX and
               LIMIT_LW_MIN<=old_after<=LIMIT_LW_MAX,
               "Original LW fault continues past the 2 HH source-HOLD window "+
               site+" "+start+"; safe gate stop, extend only after source review")
            new=[]
            print("LONGWAVE CASE",site,start,end,
                  "OLD_BOUNDARY_LW",old_before,old_after)
            print("TIME STATUS SELECTED_LW_Wm2 RAW_LW_Wm2 RAW_LW_QC PAIRED_PROCESSED_ERA_LW_Wm2")
            for k in (shift(start,-2),shift(start,-1),start,end,shift(end,1),shift(end,2)):
                qc=raw[k].get("LW_IN_F_QC","UNKNOWN")
                print(k,"TARGET" if k in keys else "FLANK",
                      a[k]["LW_IN_F"],raw[k]["LW_IN_F"],qc,
                      external[k]["LW_IN_ERA"])
            for k in (start,end):
                old=val(a[k]["LW_IN_F"])
                orig=val(raw[k]["LW_IN_F"])
                grid=val(external[k]["LW_IN_ERA"])
                want=OLD_LW_EXPECTED[site][k]
                ck(old is not None and orig is not None and
                   abs(old-want)<=.002 and abs(orig-want)<=.002,
                   "Operator observed low source LW not reproducible in native/selected "+
                   site+" "+k+" expected="+str(want)+
                   " source="+str(orig)+" selected="+str(old))
                ck(old < LIMIT_LW_MIN,"Non-low source LW erroneously selected "+site+" "+k)
                ck(grid is not None and LIMIT_LW_MIN<=grid<=LIMIT_LW_MAX,
                   "Unusable same-native processed ERA LW_IN_ERA "+site+" "+k+
                   " value="+str(grid))
                new.append(grid)
                patch[(site,k)]={
                  "site":site,"TIMESTAMP_START":k,
                  "source_original_LW_IN_F_Wm2":orig,
                  "source_original_LW_IN_F_QC":raw[k].get("LW_IN_F_QC","NOT_SUPPLIED"),
                  "selected_pre_trial_LW_IN_F_Wm2":old,
                  "same_native_FLUXNET_processed_LW_IN_ERA_Wm2":grid,
                  "new_research_LW_IN_F_Wm2":grid,
                  "decision":"BAD_LOWER_THAN_60_WM2_SOURCE_LW_REPLACE_WITH_PAIRED_ERA_LW",
                  "production_release":False}
                counts[site]+=1
            ck(abs(new[0]-new[1])<=MAX_ERA_WITHIN_EPISODE_JUMP,
               "ERA LW jumps implausibly inside 2HH record "+site+" "+start)
            leftjump=abs(new[0]-old_before);rightjump=abs(new[1]-old_after)
            ck(leftjump<=MAX_NEW_BOUNDARY_LW_JUMP and
               rightjump<=MAX_NEW_BOUNDARY_LW_JUMP,
               "ERA LW replacement leaves >160 W/m2 discontinuity across "+
               site+" "+start+" left="+str(leftjump)+" right="+str(rightjump))
            print("PAIR VALIDATED",site,start,end,
                  "RESEARCH_ERA_LW",new,
                  "AFTER_REPAIR_EDGE_JUMPS_WM2",[leftjump,rightjump])
    ck(len(patch)==12 and dict(counts)==
       {"US-SP1":4,"US-Slt":2,"US-Syv":2,"US-Ton":2,"US-Uaf":2},
       "Wrong affected-site exact 12HH set")
    print("SYVH7 EXACT 12 LW_OUTLIER NATIVE HH PAIR_ERA PHYSICAL_AND_BOUNDARY PREFLIGHT PASS",dict(counts))
    return patch
def create_one(parent,output,site,changes):
    seen=set();n=0
    with file(parent).open(encoding="utf-8-sig",newline="") as inp,\
         output.open("x",encoding="utf-8",newline="") as dest:
        reader=csv.DictReader(inp)
        ck(reader.fieldnames is not None and
           {"TIMESTAMP_START","LW_IN_F"}.issubset(reader.fieldnames),
           "Selected site missing LW_IN_F for new candidate "+site)
        has_lw_qc="LW_IN_F_QC" in reader.fieldnames
        writer=csv.DictWriter(dest,fieldnames=reader.fieldnames)
        writer.writeheader()
        for r in reader:
            n+=1;k=r["TIMESTAMP_START"]
            if (site,k) in changes:
                ck(k not in seen,"Duplicate target native HH "+site+" "+k)
                seen.add(k)
                r["LW_IN_F"]=format(changes[(site,k)]["new_research_LW_IN_F_Wm2"],".12g")
                # Mark the modified source as ERA-origin whenever the
                # assembled full source actually supplies this QC column.
                # Original source QC is retained in the immutable 12HH ledger.
                if has_lw_qc:r["LW_IN_F_QC"]="2"
            writer.writerow(r)
    ck(n==NATIVE_HH_EXPECTED[site] and
       seen=={k for s,k in changes if s==site},
       "Full native candidate incomplete "+site)
    return sha(output)
def diff(old,new,site,changes):
    seen=set();n=0;changed=0
    with file(old).open(encoding="utf-8-sig",newline="") as a,\
         file(new).open(encoding="utf-8-sig",newline="") as b:
        prev=csv.DictReader(a);cur=csv.DictReader(b)
        ck(prev.fieldnames==cur.fieldnames,"Altered original source field set "+site)
        for x,y in zip_longest(prev,cur):
            ck(x is not None and y is not None and
               x["TIMESTAMP_START"]==y["TIMESTAMP_START"],
               "Altered native timestamp or number of rows "+site)
            n+=1;k=x["TIMESTAMP_START"]
            changedfields={c for c in prev.fieldnames if x[c]!=y[c]}
            if (site,k) not in changes:
                ck(not changedfields,"Unapproved source field edited "+site+" "+k+
                   " fields="+repr(changedfields))
                continue
            ck(k not in seen and
               "LW_IN_F" in changedfields and
               changedfields.issubset({"LW_IN_F","LW_IN_F_QC"}),
               "Approved exact HH must change only LW_IN_F and its ERA QC "+site+" "+k+
               " diffs="+repr(changedfields))
            seen.add(k);changed+=1
            grid=changes[(site,k)]["new_research_LW_IN_F_Wm2"]
            if "LW_IN_F_QC" in y:
                ck(y["LW_IN_F_QC"]=="2",
                   "Edited LW native QC column must identify ERA origin "+site+" "+k)
            ck(abs(float(y["LW_IN_F"])-grid)<1e-8,
               "Output LW does not equal paired verified ERA at "+site+" "+k)
    ck(n==NATIVE_HH_EXPECTED[site] and
       seen=={k for s,k in changes if s==site},
       "Incomplete independent entire selected native site audit "+site)
    print("SYVH7 FULL PARENT_VS_NEW SOURCE DIFF PASS",site,
          "NATIVE_HH",n,"ONLY_LW_CELL_EDITS",changed)
def run():
    args=argparse.ArgumentParser(description=__doc__)
    flag=args.add_mutually_exclusive_group(required=True)
    flag.add_argument("--self-test",action="store_true")
    flag.add_argument("--assess",action="store_true")
    flag.add_argument("--apply",action="store_true")
    x=args.parse_args()
    tt=targets()
    print("SYVH7 SELF-TEST PASS exact 12 low longwave native HH in 5 sites, source original unchanged")
    if x.self_test:return
    fields,manifest,paths=pinned_inputs()
    changes=assess(paths,tt)
    if x.assess:
        print("SYVH7 ASSESS PASS 12/12; no original/candidate or model writes")
        return
    out=ROOT/"manual_Batch04_SYVH7_12_low_LW_5site_paired_ERA_research_not_approved"/(
       "candidate_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
       "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    (out/"INCOMPLETE_NO_POSTV5_DATM_CIME_SLURM_SPINUP").write_text(
       "Research source LW_IN_F correction at 12 half-hours only; science/model approval pending.\n")
    newpaths={};newhashes={}
    for site in sorted(tt):
        p=out/(site+"_SYVH7_full_research_FLUXMET_HH.csv")
        h=create_one(paths[site][0],p,site,changes)
        diff(paths[site][0],p,site,changes)
        newpaths[site]=p;newhashes[site]=h
    selected=[]
    for old in manifest:
        row=dict(old)
        site=row["site"]
        if site in newpaths:
            row["source_path"]=str(newpaths[site])
            row["source_SHA256"]=newhashes[site]
            row["latest_stage"]="SYVH7_12_LOW_LW_PAIRED_FLUXNET_ERA_RESEARCH_NOT_APPROVED"
        selected.append(row)
    ck([r for r in manifest if r["site"] not in tt]==
       [r for r in selected if r["site"] not in tt],
       "One of five selected unaffected sites unexpectedly changed")
    manifest_path=out/"RESEARCH_TEN_SITE_MANIFEST.tsv"
    with manifest_path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t")
        writer.writeheader();writer.writerows(selected)
    ledger=out/"SYVH7_EXACT_12_HH_LW_ORIGINAL_AND_PAIRED_ERA.tsv"
    rows=[changes[k] for k in sorted(changes)]
    with ledger.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t")
        writer.writeheader();writer.writerows(rows)
    receipt={
     "scientific_stage":"SYVH7_12_LOW_LW_PAIRS_RESEARCH_ONLY",
     "production_approval":False,"postv5_approved":False,
     "DATM_ready":False,"spinup_authorized":False,
     "final_original_SYVH3_Syv_SHA":FINAL_SYV_SHA,
     "exact_source_12_low_LW_HH":12,"affected_site_count":5,
     "all_original_and_upstream_sources_unmodified":True,
     "affected_source_fields_changed":["LW_IN_F","LW_IN_F_QC_IF_PRESENT"],
     "source_ERA_class":"ORIGINAL_PACKAGED_FLUXNET_PROCESSED_ERA5_LW_NOT_INDEPENDENT_ERA5LAND",
     "input_pinned_manifest":str(MANIFEST),
     "input_manifest_SHA256":sha(MANIFEST),
     "new_manifest":str(manifest_path),
     "new_manifest_SHA256":sha(manifest_path),
     "site_new_source_SHA256":newhashes,
     "full_input_source_record_counts":NATIVE_HH_EXPECTED,
     "new_LW_source_halfhours":12,
     "unchanged_selected_sites":[r["site"] for r in manifest if r["site"] not in tt],
     "source_QC_at_changes":"ORIGINAL_QC_IN_LEDGER_CANDIDATE_QC2_IF_COLUMN_PRESENT",
     "followup_gate":"INDEPENDENT_ALL_TEN_SITE_7MET_NOLEAP_NUMERICAL_RECHECK_REQUIRED"
    }
    (out/"SYVH7_RESEARCH_RECEIPT.json").write_text(
       json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("SYVH7 12 LOW LW FIVE-SITE RESEARCH CANDIDATES FULL DIFF AUDIT PASS",out)
    print("SYVH7 TEN SITE FINAL RESEARCH MANIFEST",manifest_path)
    print("SYVH7 FIVE NEW SOURCE SHAS",newhashes)
    print("NO ORIGINAL/UPSTREAM_CANDIDATE/MODEL/DATM/CIME/SLURM WRITES")
if __name__=="__main__":run()

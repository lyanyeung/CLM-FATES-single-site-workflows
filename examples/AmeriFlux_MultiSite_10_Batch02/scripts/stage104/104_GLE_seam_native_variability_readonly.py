#!/usr/bin/env python3
"""Stage104: GLE 16-year artificial seam versus native 30-minute changes. Read-only."""
import argparse,csv,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import netCDF4 as nc

R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports")
P=R/"stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_20261026T114427Z_e63d3051"
C=R/"stage103_GLE_DETACHED_CIME_NAMELIST_PREVIEW_NO_SUBMIT_20261026T120236Z_10b337c3"
FIELDS=("TBOT","WIND","PSRF","QBOT","FSDS","FLDS","PRECTmms","ZBOT")

def digest(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def obj(p):return json.loads(Path(p).read_text())

def run():
    pm=obj(P/"manifest.json");cm=obj(C/"manifest.json")
    if not (pm["NC_technical_preview_count"]==16 and pm["source_cyclic_wrap_halfhours"]==14
        and pm["CIME_DATM_approved"] is False and cm["stage103_CIME_parser_pass"] is True
        and cm["real_model_run_performed"] is False and cm["Slurm_jobs_submitted"] is False
        and cm["source_Stage102_manifest_sha256"]==digest(P/"manifest.json")
        and (C/"SCIENCE_HOLD_DO_NOT_SUBMIT_OR_RUN").is_file()):
        raise ValueError("Stage102/103 source or science-HOLD changed")
    for name,h in pm["out_sha256"].items():
        if digest(P/name)!=h:raise ValueError("Stage102 evidence SHA changed")
    files=sorted(obj(P/"16_year_UTC_midpoint_NC_source_manifest.json"),
                 key=lambda x:x["year"])
    if len(files)!=16:raise ValueError("Missing GLE 16 source years")
    arrays={f:[] for f in FIELDS}
    for x in files:
        if digest(x["new"])!=x["sha256"]:raise ValueError("Original GLE NC changed")
        with nc.Dataset(x["new"]) as ds:
            t=np.asarray(ds["time"][:],dtype=float)
            if ds["time"].calendar!="noleap" or len(t)!=17520 or not np.allclose(
                t,(np.arange(17520)+0.5)/48,atol=1e-10,rtol=0):
                raise ValueError("GLE UTC midpoint axis changed")
            for f in FIELDS:
                a=np.ma.filled(ds[f][:],np.nan).astype(float).ravel()
                if not np.isfinite(a).all() or len(a)!=17520:
                    raise ValueError("GLE field missing "+f)
                arrays[f].append(a)
    rows=[]
    for f,blocks in arrays.items():
        a=np.concatenate(blocks);d=np.diff(a)
        if len(a)!=280320:raise ValueError("GLE data length changed")
        seam=float(d[13])
        native=np.abs(np.concatenate([d[:13],d[14:]]))
        p95,p99,p999=np.quantile(native,[.95,.99,.999])
        tail=int(np.count_nonzero(native>=abs(seam)))
        record={"variable":f,"synthetic_seam_UTC":"2005-01-01 07:15",
            "synthetic_jump":seam,"abs_jump":abs(seam),
            "native_p95_abs_30min":float(p95),"native_p99_abs_30min":float(p99),
            "native_p999_abs_30min":float(p999),
            "native_intervals_ge_jump":tail,"native_interval_count":len(native),
            "native_tail_fraction":tail/len(native),
            "true_16year_cycle_file_edge_jump":float(a[0]-a[-1]),
            "manual_science_approval":"HOLD"}
        rows.append(record)
        print("STAGE104 SEAM",f,"jump",round(seam,8),"p99",round(float(p99),8),
              "tail",round(record["native_tail_fraction"],8),
              "cycle-edge",round(record["true_16year_cycle_file_edge_jump"],8),flush=True)
    case=Path(cm["isolated_case_path"])
    receipt=obj(C/"detached_CIME_case_preview_receipt.json")
    if digest(case/"user_nl_datm_streams")!=receipt["user_nl_datm_streams_SHA256"]:
        raise ValueError("Detached CIME stream changed")
    docs={}
    for f in ("CaseDocs/datm_in","CaseDocs/lnd_in","user_nl_datm_streams"):
        path=case/f
        docs[f]={"exists":path.is_file()}
        if path.is_file():
            docs[f]["sha256"]=digest(path)
            docs[f]["selected_lines"]=[x.strip() for x in path.read_text(
                errors="replace").splitlines()
                if any(z in x.lower() for z in ("qbot","shum","zbot",
                "taxmode","tintalgo","year_first","year_last"))][:45]
    pft=obj(C/"original_GLE_surface_PFT_NOT_APPROVED.json")
    if pft["tower_true_FATES_PFT_approved"] is not False:
        raise ValueError("Gridded PFT science approval unexpectedly changed")
    print("STAGE104 CIME DATM_IN",docs["CaseDocs/datm_in"]["exists"],
          "runtime data read not yet tested")
    print("STAGE104 GLE NAT",round(pft["natural_pct"],4),
          "CROP",round(pft["crop_pct"],4),
          "tower official IGBP ENF, not observed PFT fractions")
    return rows,docs,pft

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","audit"):g.add_argument("--"+k,action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert len(FIELDS)==8 and 16*17520==280320
        print("STAGE104 SELF-TEST PASS | 8 fields, original 16y 280320, no writes")
        return
    rows,docs,pft=run()
    if a.check:
        print("STAGE104 CHECK PASS | no writes")
        return
    out=R/("stage104_GLE_CIME_seam_quantiles_READONLY_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    with (out/"8_field_seam_quantiles.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
    (out/"detached_CIME_docs.json").write_text(json.dumps(docs,indent=2)+"\n")
    (out/"original_GLE_gridded_PFT_HOLD.json").write_text(json.dumps(pft,indent=2)+"\n")
    metadata={"stage102_sha256":digest(P/"manifest.json"),
              "stage103_sha256":digest(C/"manifest.json"),
              "read_only":True,"production_DATM_approved":False,
              "Slurm_jobs_submitted":False,
              "output_SHA256":{f.name:digest(f) for f in out.iterdir()}}
    (out/"manifest.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print("STAGE104 REPORT",out)
    print("STAGE104 PASS | 8-variable seam climatology and CIME case evidence; no model/source writes")
    print("STAGE104 SCIENCE HOLD | cyclic seam, actual CIME runtime, wind height and tower PFT")

if __name__=="__main__":main()

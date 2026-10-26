#!/usr/bin/env python3
"""Stage107: read-only scoring of contiguous 10–16-year GLE spinup DATM cycles.

Use immutable Stage106 2005–2020 UTC MIDPOINT NetCDF with REAL 2004 LST ERA
records at 2005 Jan1 00:15–06:45 UTC. Inspect ALL 8 CIME fields, all 16
source years. Quantify each possible >=10-year contiguous interval's
end-of-last-year -> start-of-first-year artificial cycle jump relative to
native observed 30-minute changes. Also audit retained temperature, solar
and rain climatology. This is a period SELECTION candidate, not an edit,
invented source, auto-production approval, CIME rebuild or Slurm job.
"""
import argparse,csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4

import netCDF4 as nc
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S106=ROOT/"reports/stage106_GLE_ERA_2004LST_14HH_backfilled_UTCmid_16NC_20261026T125959Z_bfa2ba7f"
S102=ROOT/"reports/stage102_GLE_UTC_plus7_midpoint_CYCLIC_16NC_TECHNICAL_ONLY_20261026T114427Z_e63d3051"
FIELDS=("TBOT","WIND","PSRF","QBOT","FSDS","FLDS","PRECTmms","ZBOT")
CORE=("TBOT","PSRF","WIND")
YEARS=tuple(range(2005,2021))
N=17520
MIN_YEARS=10

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):h.update(x)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def writejson(p,v):p.write_text(json.dumps(v,indent=2,default=str)+"\n")
def csvwrite(p,rows,fields):
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)

def provenance():
    m=read(S106/"manifest.json")
    s=read(S102/"manifest.json")
    if not (m.get("schema")=="BATCH02_STAGE106_GLE_TRUE_DATED_ERA_LST_PREHISTORY_16UTC_MID_NC"
        and m.get("16_year_new_NC_count")==16
        and m.get("2004_LST_ERA_replaced_UTC_first_slots")==14
        and m.get("source_2020_synthetic_weather_seam_removed") is True
        and m.get("all_original_2005_later_and_other_15_year_values_unchanged") is True
        and m.get("science_DATM_approved") is False
        and m.get("Slurm_jobs_submitted") is False
        and m.get("stage102_manifest_SHA256")==sha(S102/"manifest.json")
        and s.get("CIME_DATM_approved") is False
        and not (S106/"INCOMPLETE_DO_NOT_USE").exists()
        and (S106/"SCIENCE_HOLD_NO_CIME_MODEL_OR_SPINUP").is_file()):
        raise ValueError("Stage106 authentic ERA replacement or science HOLD has changed")
    for name,digest in m["out_sha256"].items():
        if sha(S106/name)!=digest:
            raise ValueError("Stage106 original receipt changed: "+name)
    docs=read(S106/"16_year_independent_NC_receipts.json")
    if len(docs)!=16 or {x["year"] for x in docs}!=set(YEARS):
        raise ValueError("Original 16 yearly source manifest changed")
    docs=sorted(docs,key=lambda x:x["year"])
    series={x:[] for x in FIELDS}
    original_site=None
    for x in docs:
        p=Path(x["new"])
        if sha(p)!=x["sha256"] or sha(x["source_Stage102"])!=x["source_sha256"]:
            raise ValueError("Original Stage106 or Stage102 NC changed "+str(p))
        with nc.Dataset(p) as ds:
            if ds.science_approval!="FALSE_TECHNICAL_PREVIEW_ONLY":
                raise ValueError("GLE original NC mislabelled production")
            t=ds["time"]
            if (t.calendar!="noleap" or
                t.units!=f"days since {x['year']}-01-01 00:00:00" or
                not np.allclose(np.asarray(t[:],dtype=float),
                (np.arange(N)+0.5)/48,atol=1e-10,rtol=0)):
                raise ValueError("GLE verified midpoint UTC clock or 30min grid changed")
            coords=(round(float(ds["LATIXY"][0,0]),6),
                    round(((float(ds["LONGXY"][0,0])+180)%360)-180,6))
            if original_site is None:original_site=coords
            if coords!=original_site:
                raise ValueError("GLE site coordinates differ between years")
            for name in FIELDS:
                a=np.ma.filled(ds[name][:],np.nan).astype(float).reshape(-1)
                if len(a)!=N or not np.isfinite(a).all():
                    raise ValueError("Missing/nonfinite source met "+name)
                series[name].append(a)
    if abs(original_site[0]-41.3665)>1e-4 or abs(original_site[1]+106.2399)>1e-4:
        raise ValueError("Original BIF site lat/lon no longer matches GLE NC")
    return docs,series,m

def assess(series,docs):
    original={name:np.concatenate(seq) for name,seq in series.items()}
    scale={}
    for name,x in original.items():
        # Reference distribution: actual adjacent historical source
        # differences; exclude all post-2020 to 2005 hypothetical wrapping.
        a=np.abs(np.diff(x))
        q=float(np.quantile(a,0.99))
        scale[name]=max(q,1e-12)
    summaries={k:float(np.mean(v)) for k,v in original.items()}
    first={k:np.array([b[0] for b in seq]) for k,seq in series.items()}
    last={k:np.array([b[-1] for b in seq]) for k,seq in series.items()}
    data=[]
    for i in range(16):
        for j in range(i+MIN_YEARS-1,16):
            years=j-i+1
            d={k:float(first[k][i]-last[k][j]) for k in FIELDS}
            normalized={k:abs(v)/scale[k] for k,v in d.items()}
            q=max(normalized[v] for v in CORE)
            mix=float(np.sqrt(sum(normalized[x]**2 for x in CORE)/len(CORE)))
            m={k:float(np.mean(np.concatenate(series[k][i:j+1]))) for k in
               ("TBOT","WIND","PSRF","QBOT","FSDS","PRECTmms")}
            temp_bias=m["TBOT"]-summaries["TBOT"]
            precip_change_pct=100*(m["PRECTmms"]-summaries["PRECTmms"])/max(summaries["PRECTmms"],1e-10)
            sw_change_pct=100*(m["FSDS"]-summaries["FSDS"])/max(summaries["FSDS"],1e-10)
            record={
                "first_year":YEARS[i],"last_year":YEARS[j],
                "retained_years":years,
                "cycle_jump_TBOT_K":d["TBOT"],"cycle_jump_PSRF_Pa":d["PSRF"],
                "cycle_jump_WIND_mps":d["WIND"],
                "cycle_jump_QBOT_kgkg":d["QBOT"],
                "cycle_jump_FSDS_Wm2":d["FSDS"],
                "cycle_jump_FLDS_Wm2":d["FLDS"],
                "cycle_jump_PRECTmms":d["PRECTmms"],
                "cycle_jump_ZBOT_m":d["ZBOT"],
                "TBOT_jump_div_native_P99":normalized["TBOT"],
                "PSRF_jump_div_native_P99":normalized["PSRF"],
                "WIND_jump_div_native_P99":normalized["WIND"],
                "worst_T_P_W_jump_vs_native_P99":q,
                "T_P_W_rms_jump_vs_native_P99":mix,
                "mean_TBOT_difference_vs_full16_K":temp_bias,
                "precipitation_mean_diff_vs_full16_pct":precip_change_pct,
                "mean_FSDS_diff_vs_full16_pct":sw_change_pct,
                "site_FATES_PFT_approved":"NO",
                "original_meteorological_records_altered":"NO",
                "CIME_runtime_approved":"NO"}
            data.append(record)
    data.sort(key=lambda r:(r["worst_T_P_W_jump_vs_native_P99"],-r["retained_years"]))
    return data,scale

def main():
    p=argparse.ArgumentParser(description=__doc__)
    q=p.add_mutually_exclusive_group(required=True)
    q.add_argument("--self-test",action="store_true")
    q.add_argument("--check",action="store_true")
    q.add_argument("--audit",action="store_true")
    opt=p.parse_args()
    if opt.self_test:
        assert len(YEARS)==16 and len(FIELDS)==8
        assert sum(16-k+1 for k in range(10,17))==28
        print("STAGE107 SELF-TEST PASS | 28 contiguous 10-16-year cycles, science HOLD, no writes")
        return
    docs,series,_=provenance()
    rows,scale=assess(series,docs)
    if len(rows)!=28:raise ValueError("Expected 28 contiguous candidate windows")
    full=next(x for x in rows if x["first_year"]==2005 and x["last_year"]==2020)
    fullq=full["worst_T_P_W_jump_vs_native_P99"]
    print("STAGE107 FULL16 2005-2020 WORST_NATIVE_P99_RATIO",
          round(fullq,5),"TEMP",round(full["cycle_jump_TBOT_K"],5),
          "PSRF",round(full["cycle_jump_PSRF_Pa"],4),
          "WIND",round(full["cycle_jump_WIND_mps"],5),flush=True)
    for k,r in enumerate(rows[:8],1):
        print("STAGE107 RANK",k,r["first_year"],r["last_year"],
              "YEARS",r["retained_years"],
              "WORST_RATIO",round(r["worst_T_P_W_jump_vs_native_P99"],5),
              "T",round(r["cycle_jump_TBOT_K"],4),
              "P",round(r["cycle_jump_PSRF_Pa"],2),
              "W",round(r["cycle_jump_WIND_mps"],4),
              "TBOT_MEAN_BIAS",round(r["mean_TBOT_difference_vs_full16_K"],4),
              "PRECIP_MEAN_CHANGE_PCT",round(r["precipitation_mean_diff_vs_full16_pct"],3),
              flush=True)
    if opt.check:
        print("STAGE107 CHECK PASS | 28 real source year-window CIME candidate edges; no writes")
        return
    out=ROOT/"reports"/("stage107_GLE_real_source_contiguous_cycle_selection_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    csvwrite(out/"28_real_10to16year_cycle_boundary_options.csv",rows,list(rows[0]))
    writejson(out/"year_window_science_hold.json",{
        "reference_full16_2005_2020":full,
        "native_30min_P99_per_source_field":scale,
        "ranking_criterion":"minimize worst absolute T/P/W climate discontinuity divided by source native P99",
        "top_is_not_automatically_science_best":True,
        "requires_retain_climate_extremes_and_post_beetle_2008_years":True,
        "time_phase_midpoint":True,"reference_BIF_IGBP":"ENF",
        "observed_percent_tree_species_engelmann_spruce":85,
        "observed_percent_tree_species_subalpine_fir":15,
        "observed_footprint_percent_crop":None,
        "reference_grid_pct_crop":7.514438754520235,
        "CIME_actual_model_read_tested":False,
        "source_original_16_year_FATES_DATM_APPROVED":False})
    rec={"schema":"STAGE107_GLE_DATM_CYCLE_WINDOW_SOURCE_ROSTER_READONLY",
        "Stage106_manifest_sha256":sha(S106/"manifest.json"),
        "candidate_consecutive_year_intervals_10to16":28,
        "source_16_years_checked":True,
        "science_approved":False,"source_NC_modified":False,
        "CIME_case_modified":False,"Slurm_jobs_submitted":False,
        "receipt_sha256":{x.name:sha(x) for x in out.iterdir()}}
    writejson(out/"manifest.json",rec)
    print("STAGE107 REPORT",out,flush=True)
    print("STAGE107 PASS | 28 original unedited historical windows compared; no data imputation or case/model runs",flush=True)
    print("STAGE107 HOLD | CIME clock/model test; tower ENF PFT/footprint; 0.75m wind; no spinup",flush=True)

if __name__=="__main__":
    main()

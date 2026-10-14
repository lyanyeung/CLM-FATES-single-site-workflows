#!/usr/bin/env python3
"""User-approved earliest-BIF-height backfill policy for 11 site TA_F/WS_F.

Uses Stage13b dates/height history. Preflight by default, writes an immutable
*assumption* manifest only with --write-policy. Does not change BIF/forcing.
Unknown WS height (CH-Aws) stays unknown; TA_F ZBOT remains defined.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SITES = {
    'BE-Bra':(1996,2025,'v07a'), 'FR-Fon':(2005,2025,'v07a'),
    'GL-ZaH':(2000,2025,'v07a'), 'IT-Noe':(2004,2025,'v07a'),
    'AT-Neu':(2002,2020,'v07a'), 'FI-Sod':(2001,2025,'v07a'),
    'CH-Aws':(2006,2024,'landrh11a'), 'CH-Cha':(2005,2024,'v07a'),
    'CH-Fru':(2005,2024,'pressure07a'), 'CH-Lae':(2004,2024,'pressurelw08a'),
    'CZ-Stn':(2010,2024,'pressure07a'),
}
DEFAULT_STAGE13 = Path.home()/'FLUXNET_MultiSite_11'/'stage13b_ZBOT_policy_audit'
DEFAULT_OUTPUT = Path.home()/'FLUXNET_MultiSite_11'/'stage15_provisional_DATM'/'height_policy_v1.json'


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def construct(stage13):
    required = ['01_corrected_site_summary.csv','02_dated_TA_WS_height_history.csv',
                '03_manual_review_issues.csv','05_BIF_source_checksums.csv']
    for name in required:
        if not (stage13/name).is_file():
            raise ValueError(f'Missing Stage13b source {stage13/name}')
    summary = pd.read_csv(stage13/required[0]).set_index('site')
    histories = pd.read_csv(stage13/required[1])
    issues = pd.read_csv(stage13/required[2]).fillna('')
    inventory = pd.read_csv(stage13/required[3])
    if set(summary.index)!=set(SITES):raise ValueError('Stage13b summary missing/extra site')
    blockers=issues[issues.kind.isin(['CONFLICTING_BIF_HEIGHT','NO_VALID_TA_HEIGHT','BIF_READ_ERROR','NO_HH_BIF'])]
    if not blockers.empty:raise ValueError('Unresolved BIF blockers: '+blockers.to_string(index=False))
    source=[]
    for r in inventory.itertuples(index=False):
        path=Path(str(r.BIF_HH_file))
        if not path.is_file() or sha256(path)!=r.sha256:
            raise ValueError(f'BIF source changed or missing: {path}')
        source.append({'site':r.site,'path':str(path),'sha256':r.sha256})
    manifest={
      'format':'eleven_site_zbot_policy_v1',
      'experiment':'FLUXNET_MultiSite_11',
      'approval_scope':'EXPLICIT USER CHOICE TO BACKFILL UNKNOWN EARLY HEIGHT WITH FIRST DOCUMENTED HEIGHT; MODEL ASSUMPTION, NOT HISTORICAL MEASUREMENT',
      'authorization_date':'2026-10-14',
      'date_only_rule':'BIF YYYYMMDD assumed effective 00:00 local standard time',
      'zbot_definition':'TA_F sensor height; piecewise constant at subsequent actual BIF effective dates',
      'wind_rule':'WS_F height tracked separately; no wind-speed vertical correction; unknown WS remains unknown',
      'source_inventory':source,
      'source_stage13b_sha256':{x:sha256(stage13/x) for x in required},
      'sites':{}
    }
    for site,(start,end,tag) in SITES.items():
        r=summary.loc[site]
        vhist={}
        for var in ('TA_F','WS_F'):
            d=histories[(histories.site==site)&(histories.variable==var)].copy()
            d['effective_from']=pd.to_datetime(d['effective_from'])
            d=d.sort_values('effective_from')
            if d.effective_from.duplicated().any():raise ValueError(f'{site} duplicate BIF dates {var}')
            rec=[]
            for row in d.itertuples(index=False):
                height=float(row.height_m)
                if not (.5<=height<=150):raise ValueError(f'{site} invalid {var} height {height}')
                rec.append({'effective_from':row.effective_from.isoformat(sep=' '),
                            'height_m':height,'date_precision':str(row.date_precision),
                            'source_file':str(row.source_file)})
            if var=='TA_F' and not rec:raise ValueError(f'{site}: cannot define ZBOT without TA BIF')
            expected=int(r['TA_undocumented_early_halfhours' if var=='TA_F' else 'WS_undocumented_early_halfhours'])
            if rec:
                idx=pd.date_range(f'{start}-01-01 00:00',f'{end}-12-31 23:30',freq='30min')
                idx=idx[~((idx.month==2)&(idx.day==29))]
                early=int((idx<pd.Timestamp(rec[0]['effective_from'])).sum())
                if early!=expected:raise ValueError(f'{site} {var} Stage13b early count mismatch {early} != {expected}')
                backfill=rec[0]['height_m']
                rule='FIRST_KNOWN_BACKFILLED_BEFORE_FIRST_BIF' if early else 'BIF_COVERS_FORCING'
            else:
                backfill=None
                rule='UNKNOWN_NO_VALID_BIF_NO_HEIGHT_INFERRED'
                early=(end-start+1)*17520
            vhist[var]={'recorded_history':rec,'early_noleap_halfhours':early,
                        'early_fill_m':backfill if early>0 else None,
                        'assumption':rule}
        manifest['sites'][site]={'years':[start,end],'candidate_tag':tag,
                                 'TA_F':vhist['TA_F'],'WS_F':vhist['WS_F'],
                                 'science_status':'HEIGHT_ASSUMPTION_ACCEPTED_FOR_PROVISIONAL_DATM_ONLY'}
        print(f'{site:<7s} TA early={vhist["TA_F"]["early_noleap_halfhours"]:>7d} '
              f'fill={vhist["TA_F"]["early_fill_m"]!s:<6s} '
              f'WS={vhist["WS_F"]["assumption"]}',flush=True)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage13',type=Path,default=DEFAULT_STAGE13)
    p.add_argument('--policy',type=Path,default=DEFAULT_OUTPUT)
    p.add_argument('--write-policy',action='store_true')
    a=p.parse_args()
    obj=construct(a.stage13)
    print('HEIGHT POLICY VALIDATED; observed BIF heights preserved, early values are explicit assumptions.')
    if a.write_policy:
        a.policy.parent.mkdir(parents=True,exist_ok=True)
        with a.policy.open('x',encoding='utf-8') as out:
            json.dump(obj,out,indent=2,ensure_ascii=False)
            out.write('\n')
        print('WRITTEN:',a.policy,'SHA256:',sha256(a.policy))
    else:
        print('PREFLIGHT: nothing written. Use --write-policy for this approved height policy.')

if __name__=='__main__':main()

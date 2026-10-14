#!/usr/bin/env python3
"""Create a review checklist for BIF height gaps; NO acceptance and NO forcing edits.

Use after 01_BIF_height_timeline_corrected.py. This records scientific choices
needed before attempting time-varying ZBOT, consistent with eight-site
--allow-early-extrapolation being explicit rather than silent.
"""
import argparse
from pathlib import Path
import pandas as pd

DEFAULT_OUT = Path.home()/'FLUXNET_MultiSite_11'/'stage13b_ZBOT_policy_audit'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=DEFAULT_OUT)
    x=p.parse_args()
    summary=x.out/'01_corrected_site_summary.csv'
    target=x.out/'06_manual_height_policy_DECISIONS_TO_EDIT.csv'
    if target.exists():raise SystemExit(f'Refusing to overwrite human decisions: {target}')
    if not summary.exists():raise SystemExit(f'Missing summary; run 01 first: {summary}')
    df=pd.read_csv(summary)
    rows=[]
    for r in df.itertuples(index=False):
        start=r.years.split('-')[0]+'-01-01 00:00:00'
        for variable,prefix in [('TA_F','TA'),('WS_F','WS')]:
            n=int(getattr(r,prefix+'_undocumented_early_halfhours'))
            if n<=0:continue
            first_time=getattr(r,prefix+'_first_date')
            first_height=getattr(r,prefix+'_first_height_m')
            if pd.isna(first_time) or str(first_time).strip()=='':
                first_time='NO_VALID_BIF'
            rows.append({
                'site':r.site,'variable':variable,
                'forcing_start_local':start,'earliest_documented_height_since_local':first_time,
                'undocumented_halfhours':n,
                'first_documented_height_m':first_height,
                'possible_eight_site_style_option':'backfill_first_documented_height_ONLY_IF_EVIDENCE',
                'decision':'PENDING_MANUAL_REVIEW',
                'approved_backfill_height_m':'',
                'evidence_and_assumptions':'',
                'approved_by':'',
                'approved_date':'',
                'notes':('For TA_F this determines ZBOT; no automatic extrapolation' if variable=='TA_F'
                         else 'WS_F used for mismatch diagnostics only, not ZBOT; no automatic wind adjustment'),
            })
    col=['site','variable','forcing_start_local','earliest_documented_height_since_local',
         'undocumented_halfhours','first_documented_height_m','possible_eight_site_style_option',
         'decision','approved_backfill_height_m','evidence_and_assumptions','approved_by','approved_date','notes']
    pd.DataFrame(rows,columns=col).to_csv(target,index=False)
    print(f'WROTE {len(rows)} PENDING height decisions to {target}')
    print('No height policy was approved or executed, no source/Candidate/NetCDF changed.')

if __name__=='__main__':main()

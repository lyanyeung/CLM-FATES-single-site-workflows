#!/usr/bin/env python3
"""Stage05BZ: proposed values for every HOLD cell left in the Stage05BW shadow tables. Read-only; NOT APPROVED.

Inputs are the twelve Stage05BW tables (SHA-256 pinned; identical locally and on IRIDIS6), the original ZIPs (for
same-release ERA at t+1h and the JapanFlux2024 ERA5 fill) and, on IRIDIS6, the Stage05BT offset table for D8.
Proposed rules, one per open item of the Stage05BV packet:
  D8   45 shifted ERA-artifact PA/TA/LW cells: user-selected grid + QC2-median value at the 600 min offset (05BT)
  D13  other shifted ERA-artifact cells (WS/VPD/P/SW): linear bridge between the nearest non-HOLD neighbours
  D3a  Tgf RH>100: RH=100, VPD=0          D3b  Tom 2011-2013: excluded from the forcing period (values kept)
  D4   Tgf 2003-12-31 23:30 TA/RH/PA bridged, VPD from them (Bolton); 2015-12-15 14:30 SW = JapanFlux2024 ERA5 fill
  D6   Spp 2009-07-15 08:30 P = 0        D7  stuck WS -> same-release WS_ERA(t+1h)
  D9   VPD>=es -> VPD at tower TA from same-release ERA RH(t+1h), RH floored at 1 %
  D11  Tef 2023 measured PA -> same-release PA_ERA(t+1h)
  D14  Tom/Tgf SW below -5 W m-2 with UTC+9 TOA >= 200 W m-2 (sun well up) -> JapanFlux2024 ERA5 fill SW at t;
       low-sun and night negatives are thermal offsets that the builder clips to 0
  D9b  Tom/Tgf VPD>=es (Bolton, the JapanFlux2024 formula) -> RH from JapanFlux2024 ERA5 fill at t, VPD from it
Cells without a HOLD tag must be byte-identical to Stage05BW; this is checked cell by cell. Every proposed cell is
also listed in approval_list_NOT_APPROVED.tsv. Nothing here writes a forcing, case, Slurm job or source file.
"""
import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

BW_PIN=('05bw_decided_corrections_shadow_tables_READONLY.py','444746ed0751fbb2f0bab71b2a3654ac3c7dbe9ba4e4d2719ce78ca6fda18fdc')
BW_TABLES={'JP-Api':'6ec8d5eab3ae65825abd34a68c1e7776a63798b04cc11d48e79dbe8019b0a255','JP-Fhk':'b1a7a0b870140016721c0a1f3cc8b87575ddf1903e159bc6495e2a5bc4ce8bcb',
 'JP-Fjy':'aa5ba0591733cfbe5608772473ffe37000718d05f4d1b3c5b832602a4e7c6640','JP-Khw':'8c99d0b579da66a796d9fd8a44193a85d23530e8d31944d5eece5314915318d2',
 'JP-Spp':'729fbbbf319c91f91d8f8372282b358d33f0c2ee1ab73b86b7fab68842c4c3b9','JP-Tak':'27201fe0b2f4d5100564aa9bf265f8650157f7bac44c7448ec0e278fa417a975',
 'JP-Tef':'e06d63f0d087e621e95ab89e6f5727f5e3c520fc70f1224d4b600bb41825df53','JP-Tmd':'3d3e2f34910d64bb07027c68ca1f574b7b66158d05e10aa8efb6d56e114d3936',
 'JP-Yms':'1b79b4dfc2c6d6d9a1547928ff44846c6e17b9fecec7dc0b7a8a5294f0241eeb','JP-Tgf_HH':'60f90d54030629f8626a0f5025a3d26ec84ad19efa15b5c6f80c68b34d03565b',
 'JP-Tom_HH':'ba96a2b2842e69c46c0d7361e9f635097c7588f13e7a8f2ee91fdf86803d9f71','JP-Tom_HR':'59fba16a38dad2afd3da28bb782335873ff0b235610e71026299ee35de75dc29'}
BT_TSV_SHA='070732bcca151a8da0cf16390c24d865efe5c2eae8f517f84f9de943831a240f'
# D8: Stage05BT candidates at 600 min, printed by the operator's Stage05BX run (keys are original native group starts).
D8={('JP-Fjy','PA','200508120230'):['89.954475','89.945248','89.931173'],('JP-Fjy','PA','201112170630'):['89.945595','89.974578','90.006068'],
 ('JP-Khw','LW_IN','200508120200'):['401.342','401.342'],('JP-Khw','PA','200508120230'):['97.772085','97.774608','97.777032'],
 ('JP-Khw','PA','201112170630'):['99.023088','99.05482','99.09881'],('JP-Khw','TA','200508120230'):['23.716505','23.600265','23.497215'],
 ('JP-Tef','LW_IN','201112170600'):['209.897389','209.897389'],('JP-Tef','LW_IN','202204090200'):['270.288278','270.288278'],
 ('JP-Tmd','LW_IN','200508120200'):['398.763333','398.763333'],('JP-Tmd','PA','200508120230'):['98.997123','98.994395','98.99282'],
 ('JP-Tmd','PA','201112170630'):['98.934218','98.95895','98.97944'],('JP-Tmd','PA','202204090230'):['99.145792','99.120256','99.108179'],
 ('JP-Tmd','TA','200508120230'):['19.11986','19.060745','19.000655'],('JP-Yms','LW_IN','200508120200'):['418.831','418.831'],
 ('JP-Yms','LW_IN','201112170600'):['243.384903','243.384903'],('JP-Yms','PA','200508120230'):['98.25807','98.260592','98.258017'],
 ('JP-Yms','PA','201112170630'):['98.966025','98.993257','99.031247']}
STEP=timedelta(minutes=30);HOUR=timedelta(hours=1);HIGH_SUN_TOA=200.

def load_bw():
    name,expected=BW_PIN;path=Path(__file__).with_name(name)
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 05BW hash mismatch')
    spec=importlib.util.spec_from_file_location('stage05bw',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bw=load_bw();br=bw.br;bs=bw.bs;num=br.num;finite=br.finite;fmt=bw.fmt;ts=bw.ts

def read_table(path,expected):
    br.check(path,expected)
    with gzip.open(path,'rt',encoding='utf-8',newline='') as f:
        reader=csv.reader(f,delimiter='\t');header=next(reader);rows=[list(r) for r in reader]
    variables=[header[i] for i in range(1,len(header),3)]
    return header,variables,rows

def d8_cells(bt_tsv):
    """Shifted cell (one hour before each original 45-field cell) -> proposed value; optionally verified on the 05BT table."""
    verified=False
    if bt_tsv is not None:
        br.check(bt_tsv,BT_TSV_SHA)
        with bt_tsv.open(encoding='utf-8',newline='') as f:
            got={(r['site'],r['variable'],r['group_start']):r['candidates_NOT_APPROVED'].split(',') for r in csv.DictReader(f,delimiter='\t') if r['offset_minutes']=='600'}
        if got!=D8:raise ValueError('embedded D8 values differ from the Stage05BT offset table')
        verified=True
    out={}
    for (site,var,start),vals in D8.items():
        for j,v in enumerate(vals):out[(site,var+'_F',ts(br.stamp(start)-HOUR+j*STEP))]=v
    if len(out)!=45:raise ValueError('D8 scope')
    return out,verified

def era_after(site,root,layout,keys):
    """Same-release ERA strings at t+1h for the requested JPF timestamps."""
    pkg,expected,_=br.SITES[site];path=br.source(root,layout,site);br.check(path,expected);want={ts(br.stamp(t)+HOUR):t for t in keys};out={}
    with zipfile.ZipFile(path) as outer:raw=outer.read(pkg+'.zip')
    with zipfile.ZipFile(io.BytesIO(raw)) as nz:
        name=[n for n in nz.namelist() if '_ERA5_HH_' in n][0]
        for r in bw.csv_rows(nz,name):
            if r['TIMESTAMP_START'] in want:out[want[r['TIMESTAMP_START']]]=r
    br.check(path,expected)
    if set(out)!=set(keys):raise ValueError('missing ERA at t+1h for '+site)
    return out

def bridge_runs(rows,col,pick):
    """Linear bridge over consecutive rows selected by pick(row); neighbours must be outside the run and finite."""
    out={};i=0;n=len(rows)
    while i<n:
        if not pick(rows[i]):i+=1;continue
        j=i
        while j+1<n and pick(rows[j+1]):j+=1
        if i==0 or j==n-1:raise ValueError('HOLD run touches the table edge')
        a=num(rows[i-1][col]);b=num(rows[j+1][col])
        if not (finite(a) and finite(b)):raise ValueError('non-finite bridge neighbour')
        for k in range(i,j+1):out[k]=fmt(a+(b-a)*(k-i+1)/(j-i+2))
        i=j+1
    return out

def resolve_jpf(site,header,variables,rows,d8,root,layout,listing):
    col={v:1+3*i for i,v in enumerate(variables)};tagc={v:c+2 for v,c in col.items()};counts=Counter()
    need=[r[0] for r in rows if any(r[tagc[v]].startswith(('HOLD_D7','HOLD_D9','HOLD_D11')) for v in variables)]
    era=era_after(site,root,layout,need) if need else {}
    def put(i,v,val,rule):
        r=rows[i];listing.append([site,v,r[0],r[col[v]],val,rule,r[tagc[v]]]);r[col[v]]=val;r[tagc[v]]='PROPOSED_'+rule+'_NOT_APPROVED|'+r[tagc[v]];counts[(v,rule)]+=1
    for v in variables:
        hold=lambda r,v=v:r[tagc[v]].startswith('HOLD_ERA_ARTIFACT_SHIFTED') and (site,v,r[0]) not in d8
        bridges=bridge_runs(rows,col[v],hold)
        for i,r in enumerate(rows):
            t=r[0];tag=r[tagc[v]]
            if not tag.startswith('HOLD'):continue
            if tag.startswith('HOLD_ERA_ARTIFACT_SHIFTED'):
                if (site,v,t) in d8:put(i,v,d8[(site,v,t)],'D8_GRID_QC2_MEDIAN_600')
                else:put(i,v,bridges[i],'D13_BRIDGE')
            elif tag.startswith('HOLD_D6'):put(i,v,'0','D6_GAUGE_SPIKE_ZERO')
            elif tag.startswith('HOLD_D7'):put(i,v,era[t]['WS_ERA'],'D7_WS_ERA_T_PLUS_1H')
            elif tag.startswith('HOLD_D11'):put(i,v,era[t]['PA_ERA'],'D11_PA_ERA_T_PLUS_1H')
            elif tag.startswith('HOLD_D9'):
                ta=num(r[col['TA_F']]);e=era[t];te=num(e['TA_ERA']);ve=num(e['VPD_ERA'])
                rh=100*(1-ve/br.es(te,'oneflux_qc_auto'));rh=min(100.,max(1.,rh))
                put(i,v,fmt(br.es(ta,'oneflux_qc_auto')*(1-rh/100)),'D9_ERA_RH_AT_TOWER_TA')
            else:raise ValueError('unhandled HOLD tag '+tag)
    return counts

def resolve_tgf(rows,variables,root,layout,listing):
    col={v:1+3*i for i,v in enumerate(variables)};tagc={v:c+2 for v,c in col.items()};counts=Counter()
    idx={r[0]:i for i,r in enumerate(rows)}
    _,expected,_=bs.SOURCES['JP-Tgf'];path=bs.source(root,layout,'JP-Tgf');br.check(path,expected)
    with zipfile.ZipFile(path) as z:
        fill=[n for n in z.namelist() if 'ERA5_FILL' in n and '_HH_' in n][0]
        sw=next(r['SW_IN_ERA5'] for r in bw.csv_rows(z,fill) if r['TIMESTAMP_START']=='201512151430')
    br.check(path,expected)
    def put(i,v,val,rule):
        r=rows[i];listing.append(['JP-Tgf',v,r[0],r[col[v]],val,rule,r[tagc[v]]]);r[col[v]]=val;r[tagc[v]]='PROPOSED_'+rule+'_NOT_APPROVED|'+r[tagc[v]];counts[(v,rule)]+=1
    i=idx['200312312330'];b={v:(num(rows[i-1][col[v]])+num(rows[i+1][col[v]]))/2 for v in ('TA_F','RH_F','PA_F')}
    for v in ('TA_F','RH_F','PA_F'):put(i,v,fmt(b[v]),'D4_TGF_ROW_BRIDGE')
    put(i,'VPD_F',fmt(br.es(b['TA_F'],'bolton1980')*(1-b['RH_F']/100)),'D4_TGF_VPD_FROM_BRIDGED_TA_RH')
    put(idx['201512151430'],'SW_IN_F',sw,'D4_TGF_SW_JF2024_ERA5_FILL')
    for k,r in enumerate(rows):
        if r[tagc['RH_F']].startswith('HOLD_D3_TGF'):
            put(k,'RH_F','100','D3A_TGF_RH_CAP100');put(k,'VPD_F','0','D3A_TGF_VPD_ZERO')
        for v in variables:
            if r[tagc[v]].startswith('HOLD'):raise ValueError('unhandled Tgf HOLD '+r[tagc[v]])
    return counts

def special_extra(key,rows,variables,root,layout,listing):
    """D14 and D9b for Tom/Tgf after their main rules; Tom 2011-2013 rows are excluded from the forcing period."""
    site,cad=key.split('_');col={v:1+3*i for i,v in enumerate(variables)};tagc={v:c+2 for v,c in col.items()};counts=Counter()
    _,expected,_=bs.SOURCES[site];path=bs.source(root,layout,site);br.check(path,expected)
    with zipfile.ZipFile(path) as z:
        fill=[n for n in z.namelist() if 'ERA5_FILL' in n and '_'+cad+'_' in n][0]
        era={r['TIMESTAMP_START']:(r['SW_IN_ERA5'],r['RH_ERA5']) for r in bw.csv_rows(z,fill)}
    br.check(path,expected);lat,lon=bs.LOCATION[site]
    def put(i,v,val,rule):
        r=rows[i];listing.append([site,v,r[0],r[col[v]],val,rule,r[tagc[v]]]);r[col[v]]=val;r[tagc[v]]='PROPOSED_'+rule+'_NOT_APPROVED|'+r[tagc[v]];counts[(v,rule)]+=1
    for i,r in enumerate(rows):
        t=r[0]
        if site=='JP-Tom' and t[:4] in ('2011','2012','2013'):continue
        sw=num(r[col['SW_IN_F']])
        if finite(sw) and sw<-5 and toa(site,cad,t)>=HIGH_SUN_TOA and not r[tagc['SW_IN_F']].startswith('PROPOSED'):put(i,'SW_IN_F',era[t][0],'D14_DAYTIME_NEGATIVE_SW_ERA5_FILL')
        ta=num(r[col['TA_F']]);vpd=num(r[col['VPD_F']])
        if finite(ta) and finite(vpd) and vpd>=br.es(ta,'bolton1980') and not r[tagc['VPD_F']].startswith('PROPOSED'):
            rh=min(100.,max(1.,num(era[t][1])));put(i,'RH_F',fmt(rh),'D9B_RH_JF2024_ERA5_FILL');put(i,'VPD_F',fmt(br.es(ta,'bolton1980')*(1-rh/100)),'D9B_VPD_FROM_ERA5_RH')
    return counts

def toa(site,cad,t):
    lat,lon=bs.LOCATION[site];s=br.stamp(t)
    return br.toa_mean(s,lat,lon,9.) if cad=='HH' else (br.toa_mean(s,lat,lon,9.)+br.toa_mean(s+STEP,lat,lon,9.))/2

def resolve_tom(rows,variables,listing):
    col={v:1+3*i for i,v in enumerate(variables)};tagc={v:c+2 for v,c in col.items()};counts=Counter()
    for r in rows:
        for v in variables:
            tag=r[tagc[v]]
            if tag.startswith('HOLD_D3_TOM'):
                listing.append(['JP-Tom',v,r[0],r[col[v]],r[col[v]],'D3B_TOM_EXCLUDE_2011_2013',tag])
                r[tagc[v]]='PROPOSED_D3B_TOM_EXCLUDE_2011_2013_NOT_APPROVED|'+tag;counts[(v,'D3B_TOM_EXCLUDE_2011_2013')]+=1
            elif tag.startswith('HOLD'):raise ValueError('unhandled Tom HOLD '+tag)
    return counts

def cells_identical_unless_proposed(before,after):
    """A variable cell (value, QC, tag) may differ only if 05BW tagged it HOLD or it is a new D14/D9b proposal."""
    for r0,r1 in zip(before,after):
        if r0[0]!=r1[0]:return False
        for c in range(1,len(r0),3):
            if r0[c:c+3]==r1[c:c+3]:continue
            if r0[c+2].startswith('HOLD') or r1[c+2].startswith(('PROPOSED_D14','PROPOSED_D9B')):continue
            return False
    return len(before)==len(after)

def post_checks(site,variables,rows):
    """Broad physical limits on the proposed tables; Tom 2011-2013 rows are excluded from the forcing period."""
    col={v:1+3*i for i,v in enumerate(variables)};bad=Counter()
    for r in rows:
        if site.startswith('JP-Tom') and r[0][:4] in ('2011','2012','2013'):continue
        x={v:num(r[col[v]]) for v in variables}
        if finite(x['TA_F']) and not -45<=x['TA_F']<=45:bad['TA_F']+=1
        if finite(x['PA_F']) and not 70<=x['PA_F']<=110:bad['PA_F']+=1
        if finite(x['LW_IN_F']) and not 100<=x['LW_IN_F']<=600:bad['LW_IN_F']+=1
        if finite(x['WS_F']) and not 0<=x['WS_F']<=35:bad['WS_F']+=1
        if finite(x['P_F']) and not 0<=x['P_F']<=50:bad['P_F']+=1
        special=site.startswith(('JP-Tom','JP-Tgf'));formula='bolton1980' if special else 'oneflux_qc_auto'
        if finite(x['SW_IN_F']) and x['SW_IN_F']<-5:
            day=toa(*site.split('_'),r[0])>=HIGH_SUN_TOA if special else True
            bad['SW_IN_F_below_-5_high_sun' if day else 'INFO_night_or_low_sun_SW_below_-5_clipped_to_0_by_builder']+=1
        if finite(x['VPD_F']) and finite(x['TA_F']) and (x['VPD_F']<0 or x['VPD_F']>=br.es(x['TA_F'],formula)):bad['VPD_F']+=1
        if 'RH_F' in x and finite(x['RH_F']) and not 0<x['RH_F']<=100:bad['RH_F']+=1
        if any(r[col[v]+2].startswith('HOLD') for v in variables):bad['HOLD_left']+=1
    return dict(sorted(bad.items()))

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    d8,verified=d8_cells(a.bt_tsv);a.out.mkdir();listing=[];report={'stage':'05BZ','status':'PROPOSED_VALUES_NOT_APPROVED','approved_replacements_new':0,'tables':{}}
    for key,expected in BW_TABLES.items():
        print('STAGE05BZ',key,flush=True)
        header,variables,rows=read_table(a.bw_dir/(key+'_decided_shadow_HOLD.tsv.gz'),expected)
        before=[list(r) for r in rows]
        if key=='JP-Tgf_HH':counts=resolve_tgf(rows,variables,a.root,a.layout,listing)
        elif key.startswith('JP-Tom'):counts=resolve_tom(rows,variables,listing)
        else:counts=resolve_jpf(key,header,variables,rows,d8,a.root,a.layout,listing)
        if key.startswith(('JP-Tgf','JP-Tom')):counts.update(special_extra(key,rows,variables,a.root,a.layout,listing))
        changed=sum(1 for r0,r1 in zip(before,rows) for c in range(len(r0)) if r0[c]!=r1[c] and not header[c].endswith('_TAG'))
        identity=cells_identical_unless_proposed(before,rows)
        w=bw.Writer(a.out/(key+'_proposed_NOT_APPROVED.tsv.gz'),header)
        for r in rows:w.line(r)
        digest,n=w.close()
        report['tables'][key]={'rows':n,'uncompressed_tsv_sha256':digest,'value_cells_changed':changed,
            'unproposed_cells_identical_to_05BW':identity,'proposed_by_variable_rule':{v+'|'+k:c for (v,k),c in sorted(counts.items())},
            'post_check_violations':post_checks(key,variables,rows)}
        if not identity:raise ValueError('a cell changed without a HOLD tag or a D14/D9b proposal in '+key)
    lst=a.out/'approval_list_NOT_APPROVED.tsv'
    with lst.open('x',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(['site','variable','native_start','value_in_05BW','proposed_value','rule','05BW_tag']);w.writerows(listing)
    report['approval_list_rows']=len(listing);report['approval_list_sha256']=br.sha(lst)
    report['rule_totals']=dict(sorted(Counter(r[5] for r in listing).items()))
    # Fingerprint before the verification flag: it is True on IRIDIS6 (05BT table present) and False locally.
    report['fingerprint_integers_strings']=br.fingerprint(report);report['D8_values_verified_against_05BT_table']=verified
    with (a.out/'summary_NOT_APPROVED.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE05BZ COMPLETE; PROPOSED VALUES ONLY; NOTHING APPROVED OR WRITTEN TO FORCING');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'rule_totals':report['rule_totals'],'approval_list_sha256':report['approval_list_sha256'],
        'D8_verified':verified,'post_checks':{k:v['post_check_violations'] for k,v in report['tables'].items()}},indent=1))

def selftest():
    rows=[['a','1','0','ORIGINAL'],['b','9','2','HOLD_ERA_ARTIFACT_SHIFTED+C3'],['c','9','2','HOLD_ERA_ARTIFACT_SHIFTED+C3'],['d','4','0','ORIGINAL']]
    assert bridge_runs(rows,1,lambda r:r[3].startswith('HOLD'))=={1:'2.0',2:'3.0'}
    cells,verified=d8_cells(None);assert len(cells)==45 and not verified and cells[('JP-Khw','PA_F','200508120130')]=='97.772085'
    print('STAGE05BZ SELF-TEST PASS; PROPOSED VALUES ONLY; NOTHING APPROVED')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--root',type=Path,default=br.IRIDIS_ROOT);p.add_argument('--layout',choices=('iridis','local'),default='iridis')
    p.add_argument('--bw-dir',type=Path);p.add_argument('--bt-tsv',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.out is None or a.bw_dir is None:p.error('--bw-dir and --out required')
    run(a)
if __name__=='__main__':main()

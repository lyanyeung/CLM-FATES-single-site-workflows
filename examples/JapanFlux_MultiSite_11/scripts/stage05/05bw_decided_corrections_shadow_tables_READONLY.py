#!/usr/bin/env python3
"""Stage05BW: shadow tables with the user-approved (D1, D2) and delegated clock (C2, C3) corrections. Read-only.

Every cell of the seven (JPF) or eight (Tom/Tgf, plus RH_F) forcing variables is written with its original QC and a
provenance tag. Unchanged cells carry the original source string byte-for-byte. Rules:
  D1  P at Api/Tak/Tmd: P_F(t+1h)/3.6 (same-release ERA back to raw ERA5 units and time); Yms: the JapanFlux2024
      rain gauge P_RAIN_1_1_1 (ALLVARS) where it is present, otherwise the same /3.6 rule.  [approved 2026-11-04]
      JapanFlux2024 Yms P_F is NOT used: despite QC 0 it equals its bias-corrected ERA5 (P_ERA5) month by month.
  D2  -1e-12<P<0 -> 0 and -1e-9<=VPD<0 -> 0 at Tom/Tgf; must equal the 5,099 audited cells.  [approved 2026-11-04]
  C2  Tom TA/RH/VPD/SW: value at t is the tower value labelled t+1h when that is QC0, else the JapanFlux2024
      bias-corrected ERA5 at t (identical to its QC1 fill). P/LW/PA/WS unchanged.     [delegated clock decision]
  C3  JPF QC2 cells (same-release ERA) take the same-release ERA value at t+1h.        [delegated clock decision]
Cells whose shifted ERA source is a known ERA artifact, and open items D3/D4/D6/D7/D9/D11, are tagged HOLD_* (joined
with any rule already applied, e.g. HOLD_D3_TOM_RH_DRIFT+D2_TINY_ZERO) and must be resolved before a forcing is
built. The clear-day SW centroid is reported before and after C2/C3 as a check of the timing correction.
Nothing here writes a forcing, case, Slurm job or source file.
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
from datetime import datetime, timedelta
from pathlib import Path

PINS={'05br':('05br_nine_site_jpf_forcing_variable_qc_READONLY.py','67ecfb0dbfeda1599986de7d995aadf581570022450b5c5055fae6cc8a1f30cb'),
      '05bs':('05bs_tom_tgf_humidity_tiny_negative_isolated_forensics_READONLY.py','83555cd1b1ec81c6b42410fa5cee1327292862b104f03b4b50afda57e222baa2')}
JF2024_YMS=('A20241022-024_2.00_selected','a112e8650592040b92698280416ac4b308a214ff1c5af8b8ee8d6e1ecf55d37d')
JPF_VARS=('TA_F','PA_F','VPD_F','SW_IN_F','LW_IN_F','WS_F','P_F')
SPECIAL_VARS=('TA_F','RH_F','VPD_F','PA_F','SW_IN_F','LW_IN_F','WS_F','P_F')
ERA_COL={'TA_F':'TA_ERA','PA_F':'PA_ERA','VPD_F':'VPD_ERA','SW_IN_F':'SW_IN_ERA','LW_IN_F':'LW_IN_ERA','WS_F':'WS_ERA','P_F':'P_ERA'}
INSTANT=('TA_F','PA_F','VPD_F','WS_F')
D1A_SITES=('JP-Api','JP-Tak','JP-Tmd','JP-Yms')
C2_VARS=('TA_F','RH_F','VPD_F','SW_IN_F')
FILL_COL={'TA_F':'TA_ERA5','RH_F':'RH_ERA5','VPD_F':'VPD_ERA5','SW_IN_F':'SW_IN_ERA5'}
D2_EXPECTED=5099
HOLD_CELLS={('JP-Spp','200907150830','P_F'):'HOLD_D6_SPP_GAUGE_SPIKE',
            ('JP-Tgf','200312312330','TA_F'):'HOLD_D4_TGF_ZERO_ROW',('JP-Tgf','200312312330','RH_F'):'HOLD_D4_TGF_ZERO_ROW',
            ('JP-Tgf','200312312330','VPD_F'):'HOLD_D4_TGF_ZERO_ROW',('JP-Tgf','200312312330','PA_F'):'HOLD_D4_TGF_ZERO_ROW',
            ('JP-Tgf','201512151430','SW_IN_F'):'HOLD_D4_TGF_SW_NEGATIVE'}
STEP=timedelta(minutes=30);HOUR=timedelta(hours=1)

def load(key):
    name,expected=PINS[key];path=Path(__file__).with_name(name)
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned module hash mismatch '+name)
    spec=importlib.util.spec_from_file_location('stage'+key,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
br=load('05br');bs=load('05bs')
num=br.num;finite=br.finite
def ts(t):return t.strftime('%Y%m%d%H%M')
def fmt(x):return repr(round(x,6))
def is_qc(q,k):return q in (str(k),str(k)+'.0')
def hold(tag,current):return tag if current=='ORIGINAL' else tag+'+'+current
def csv_rows(z,name):
    with z.open(name) as raw,io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        yield from csv.DictReader(text)

class Writer:
    """Deterministic gzip TSV (mtime 0, no name) plus SHA-256 of the uncompressed text."""
    def __init__(self,path,header):
        self.f=path.open('xb');self.gz=gzip.GzipFile(filename='',mode='wb',fileobj=self.f,mtime=0);self.h=hashlib.sha256();self.n=0
        self.line(header)
    def line(self,cells):
        b=('\t'.join(cells)+'\n').encode('utf-8');self.gz.write(b);self.h.update(b);self.n+=1
    def close(self):
        self.gz.close();self.f.close();return self.h.hexdigest(),self.n-1

def artifact_rows(era_ts,era):
    """Instant-variable triplet rows (TA_ERA<-60) and interval pair rows (LW_IN_ERA below half the local median)."""
    idx={t:i for i,t in enumerate(era_ts)}
    inst=[t for t in era_ts if finite(num(era['TA_ERA'][idx[t]])) and num(era['TA_ERA'][idx[t]])<-60]
    groups=[]
    for t in inst:
        if groups and idx[t]-idx[groups[-1][-1]]==1:groups[-1].append(t)
        else:groups.append([t])
    interval=set()
    for g in groups:
        lo=max(0,idx[g[0]]-3);hi=min(len(era_ts)-1,idx[g[-1]]+3)
        lw=sorted(num(era['LW_IN_ERA'][i]) for i in range(lo,hi+1) if finite(num(era['LW_IN_ERA'][i])))
        half=.5*lw[len(lw)//2]
        pair=[era_ts[i] for i in range(lo,hi+1) if finite(num(era['LW_IN_ERA'][i])) and num(era['LW_IN_ERA'][i])<half]
        if len(pair)!=2 or idx[pair[0]]!=idx[g[0]]-1:raise ValueError('artifact interval pair not where expected near '+g[0])
        interval.update(pair)
    return set(inst),interval,[g[0] for g in groups]

def clear_day_offsets(times,sw_by_label,toa,qc_ok):
    """Median clear-day SW centroid minus UTC+9 TOA centroid (minutes) for each labelled series."""
    out=defaultdict(list)
    for s in range(0,len(times)-47,48):
        day=range(s,s+48);top=[toa[i] for i in day]
        if sum(top)<=0 or any(not qc_ok[i] for i in day if toa[i]>0):continue
        ref=sw_by_label['tower'];vals=[ref[i] for i in day]
        if any(not finite(x) for i,x in zip(day,vals) if toa[i]>0) or sum(max(x,0.) for x in vals if finite(x))/sum(top)<.6:continue
        c0=br.centroid(top)
        for k,series in sw_by_label.items():
            v=[max(series[i],0.) if finite(series[i]) else 0. for i in day]
            c=br.centroid(v)
            if c is not None:out[k].append(c-c0)
    return {k:br.summary(v) for k,v in sorted(out.items())}

def jpf_site(site,path,yms,out):
    pkg,expected,rows_expected=br.SITES[site];br.check(path,expected)
    years=pkg.split('_FLUXNET_')[1].split('_')[0].split('-');lo=years[0]+'01010000';hi=str(int(years[1])+1)+'01020000'
    with zipfile.ZipFile(path) as outer:raw=outer.read(pkg+'.zip')
    meta=br.bif_metadata(raw,pkg);lat=float(meta['bif']['LOCATION_LAT'][0]);lon=float(meta['bif']['LOCATION_LONG'][0])
    with zipfile.ZipFile(io.BytesIO(raw)) as nz:
        names=nz.namelist();met=[n for n in names if '_FLUXMET_HH_' in n];eran=[n for n in names if '_ERA5_HH_' in n]
        if len(met)!=1 or len(eran)!=1:raise ValueError('JPF member scope')
        era_ts=[];era={ERA_COL[v]:[] for v in JPF_VARS}
        for r in csv_rows(nz,eran[0]):
            if lo<=r['TIMESTAMP_START']<=hi:
                era_ts.append(r['TIMESTAMP_START'])
                for c in era:era[c].append(r[c])
        eidx={t:i for i,t in enumerate(era_ts)}
        data={c:[] for c in ['TIMESTAMP_START']+[x for v in JPF_VARS for x in (v,v+'_QC')]}
        for r in csv_rows(nz,met[0]):
            t=r['TIMESTAMP_START']
            if t not in eidx:raise ValueError('FLUXMET time outside ERA5_HH '+t)
            for v in JPF_VARS:
                a=num(r[ERA_COL[v]]);e=num(era[ERA_COL[v]][eidx[t]])
                if finite(a)!=finite(e) or (finite(a) and abs(a-e)>1e-9):raise ValueError('FLUXMET ERA != ERA5_HH at '+t+' '+v)
                if is_qc(r[v+'_QC'],2) and finite(a) and abs(num(r[v])-a)>1e-9:raise ValueError('QC2 F != ERA at '+t+' '+v)
            for c in data:data[c].append(r[c])
    n=len(data['TIMESTAMP_START'])
    if n!=rows_expected:raise ValueError('row count')
    inst,interval,events=artifact_rows(era_ts,era)
    if site=='JP-Yms':
        pairs=[(num(data['TA_F'][i]),yms['TA'].get(data['TIMESTAMP_START'][i])) for i in range(n) if is_qc(data['TA_F_QC'][i],0)]
        pairs=[(a,b) for a,b in pairs if b is not None and finite(b)]
        share=sum(1 for a,b in pairs if abs(a-b)<=.01)/max(len(pairs),1)
        if share<.99:raise ValueError('JapanFlux2024 Yms labels do not match JPF (TA identity %.4f)'%share)
    stuck=ws_stuck(data,n);tags=defaultdict(Counter);annual=defaultdict(lambda:[0.,0.])
    t0=br.stamp(data['TIMESTAMP_START'][0]);toa=[br.toa_mean(t0+i*STEP,lat,lon,9.) for i in range(n)]
    sw={'tower':[num(x) for x in data['SW_IN_F']],'same_release_ERA_original':[],'same_release_ERA_shifted_C3':[]}
    w=Writer(out/(site+'_decided_shadow_HOLD.tsv.gz'),['TIMESTAMP_START']+[c for v in JPF_VARS for c in (v,v+'_QC_ORIGINAL',v+'_TAG')])
    for i in range(n):
        t=data['TIMESTAMP_START'][i];src=ts(br.stamp(t)+HOUR);cells=[t];final={}
        sw['same_release_ERA_original'].append(num(era['SW_IN_ERA'][eidx[t]]))
        sw['same_release_ERA_shifted_C3'].append(num(era['SW_IN_ERA'][eidx[src]]) if src in eidx else float('nan'))
        for v in JPF_VARS:
            val=data[v][i];q=data[v+'_QC'][i];tag='ORIGINAL';bad=inst if v in INSTANT else interval
            if v=='P_F' and site in D1A_SITES:
                if site=='JP-Yms' and t in yms['P']:val=yms['P'][t];tag='D1B_JF2024_RAIN_GAUGE'
                elif src in eidx:
                    val=fmt(num(era['P_ERA'][eidx[src]])/3.6);tag='D1A_ERA5_DIV3P6_SHIFTM60'
                    if src in bad:tag=hold('HOLD_ERA_ARTIFACT_SHIFTED',tag)
                else:val=fmt(num(data[v][i])/3.6);tag='D1A_EDGE_DIV3P6_UNSHIFTED'
            elif is_qc(q,2):
                if src in eidx:
                    val=era[ERA_COL[v]][eidx[src]];tag='C3_QC2_ERA_SHIFTM60'
                    if src in bad:tag=hold('HOLD_ERA_ARTIFACT_SHIFTED',tag)
                else:tag='C3_EDGE_UNSHIFTED'
            if (site,t,v) in HOLD_CELLS:tag=hold(HOLD_CELLS[(site,t,v)],tag)
            elif v=='WS_F' and i in stuck:tag=hold('HOLD_D7_WS_STUCK',tag)
            elif v=='PA_F' and site=='JP-Tef' and t.startswith('2023') and is_qc(q,0):tag=hold('HOLD_D11_TEF_PA_2023',tag)
            final[v]=val;cells+=[val,q,tag]
        ta=num(final['TA_F']);vpd=num(final['VPD_F']);k=3+3*JPF_VARS.index('VPD_F')
        if finite(ta) and finite(vpd) and -70<ta<60 and vpd>=br.es(ta,'oneflux_qc_auto') and not cells[k].startswith('HOLD'):
            cells[k]=hold('HOLD_D9_VPD_GE_ES',cells[k])
        for j,v in enumerate(JPF_VARS):tags[v][cells[3+3*j]]+=1
        p0=num(data['P_F'][i]);p1=num(final['P_F'])
        if finite(p0):annual[t[:4]][0]+=p0
        if finite(p1):annual[t[:4]][1]+=p1
        w.line(cells)
    digest,rows=w.close();br.check(path,expected)
    qc_ok=[is_qc(q,0) for q in data['SW_IN_F_QC']]
    return {'rows':rows,'uncompressed_tsv_sha256':digest,'tag_counts':{v:dict(sorted(tags[v].items())) for v in JPF_VARS},
            'artifact_event_starts':events,'annual_P_F_mm_original_vs_shadow':{y:[br.r6(a),br.r6(b)] for y,(a,b) in sorted(annual.items())},
            'clear_day_SW_centroid_offset_min_vs_UTC9_TOA':clear_day_offsets(data['TIMESTAMP_START'],sw,toa,qc_ok),
            'stuck_WS_cells':len(stuck),'source_zip_sha256_pre_post':expected}

def ws_stuck(data,n,minimum=24,limit=.5):
    """QC0 wind speed constant for >=12 h below 0.5 m/s (suspected frozen or stuck anemometer)."""
    out=set();i=0
    while i<n:
        x=num(data['WS_F'][i])
        if not is_qc(data['WS_F_QC'][i],0) or not finite(x) or x>=limit:i+=1;continue
        j=i
        while j+1<n and is_qc(data['WS_F_QC'][j+1],0) and data['WS_F'][j+1]==data['WS_F'][i]:j+=1
        if j-i+1>=minimum:out.update(range(i,j+1))
        i=j+1
    return out

def load_yms_gauge(path):
    """JapanFlux2024 Yms ALLVARS: raw rain-gauge P_RAIN_1_1_1 (present values only) and QC0 TA_F for the label check."""
    br.check(path,JF2024_YMS[1]);out={'P':{},'TA':{}}
    with zipfile.ZipFile(path) as z:
        allv=[n for n in z.namelist() if '_ALLVARS_HH_' in n and '/ALLVARS/' in '/'+n]
        if len(allv)!=1:raise ValueError('JapanFlux2024 Yms ALLVARS scope')
        for r in csv_rows(z,allv[0]):
            t=r['TIMESTAMP_START'];p=num(r['P_RAIN_1_1_1'])
            if finite(p):
                if p<0:raise ValueError('negative Yms gauge rain at '+t)
                out['P'][t]=r['P_RAIN_1_1_1']
            out['TA'][t]=num(r['TA_F']) if is_qc(r['TA_F_QC'],0) else float('nan')
    br.check(path,JF2024_YMS[1]);return out

def c2_value(d,f,v,i,t,cad,index,hh,hh_index):
    """Tom tower variables: value labelled t+1h if QC0, else JapanFlux2024 corrected ERA5 at t (its own QC1 value)."""
    src=br.stamp(t)+HOUR;k=index.get(ts(src))
    if k is not None:
        if is_qc(d[v+'_QC'][k],0):return d[v][k],'C2_TOM_TOWER_SHIFTM60'
    elif cad=='HR':
        a=hh_index.get(ts(src));b=hh_index.get(ts(src+STEP))
        if a is not None and b is not None and is_qc(hh[v+'_QC'][a],0) and is_qc(hh[v+'_QC'][b],0):
            return fmt((num(hh[v][a])+num(hh[v][b]))/2),'C2_TOM_TOWER_SHIFTM60_FROM_HH_MEAN'
    if is_qc(d[v+'_QC'][i],1):return d[v][i],'C2_TOM_QC1_ERA5_FRAME_KEPT'
    return f[FILL_COL[v]][i],'C2_TOM_ERA5CORR_AT_T'

def special_site(site,path,out):
    _,expected,_=bs.SOURCES[site];br.check(path,expected);res={};loaded={}
    with zipfile.ZipFile(path) as z:
        for cad in (('HR','HH') if site=='JP-Tom' else ('HH',)):
            core=bs.member(z,'_COREVARS_'+cad+'_','COREVARS')
            fill=[n for n in z.namelist() if 'ERA5_FILL' in n and '_'+cad+'_' in n]
            if len(fill)!=1:raise ValueError('ERA5_FILL scope '+cad)
            d={c:[] for c in ['TIMESTAMP_START']+[x for v in SPECIAL_VARS for x in (v,v+'_QC')]}
            for r in csv_rows(z,core.filename):
                for c in d:d[c].append(r[c])
            f={c:[] for c in ['TIMESTAMP_START']+list(FILL_COL.values())}
            for r in csv_rows(z,fill[0]):
                for c in f:f[c].append(r[c])
            if f['TIMESTAMP_START']!=d['TIMESTAMP_START']:raise ValueError('ERA5_FILL and COREVARS labels differ '+cad)
            loaded[cad]=(d,f)
    br.check(path,expected)
    hh=loaded['HH'][0];hh_index={t:i for i,t in enumerate(hh['TIMESTAMP_START'])};d2=0;lat,lon=bs.LOCATION[site]
    for cad,(d,f) in loaded.items():
        n=len(d['TIMESTAMP_START']);tags=defaultdict(Counter);index={t:i for i,t in enumerate(d['TIMESTAMP_START'])};new_sw=[]
        w=Writer(out/(site+'_'+cad+'_decided_shadow_HOLD.tsv.gz'),['TIMESTAMP_START']+[c for v in SPECIAL_VARS for c in (v,v+'_QC_ORIGINAL',v+'_TAG')])
        for i in range(n):
            t=d['TIMESTAMP_START'][i];cells=[t];final={}
            for v in SPECIAL_VARS:
                val=d[v][i];q=d[v+'_QC'][i];tag='ORIGINAL'
                if site=='JP-Tom' and v in C2_VARS:val,tag=c2_value(d,f,v,i,t,cad,index,hh,hh_index)
                final[v]=val;x=num(val)
                if (v=='P_F' and finite(x) and -1e-12<x<0) or (v=='VPD_F' and finite(x) and -1e-9<=x<0):
                    val='0';tag='D2_TINY_ZERO' if tag=='ORIGINAL' else tag+'+D2_TINY_ZERO';d2+=1
                if (site,t,v) in HOLD_CELLS:tag=hold(HOLD_CELLS[(site,t,v)],tag)
                elif site=='JP-Tom' and v in ('RH_F','VPD_F') and t[:4] in ('2011','2012','2013'):tag=hold('HOLD_D3_TOM_RH_DRIFT',tag)
                elif site=='JP-Tgf' and v in ('RH_F','VPD_F') and finite(num(final['RH_F'])) and num(final['RH_F'])>100:tag=hold('HOLD_D3_TGF_RH_GT100',tag)
                tags[v][tag]+=1;cells+=[val,q,tag]
            new_sw.append(num(final['SW_IN_F']))
            w.line(cells)
        digest,rows=w.close();item={'rows':rows,'uncompressed_tsv_sha256':digest,'tag_counts':{v:dict(sorted(tags[v].items())) for v in SPECIAL_VARS}}
        if cad=='HH':
            t0=br.stamp(d['TIMESTAMP_START'][0]);toa=[br.toa_mean(t0+i*STEP,lat,lon,9.) for i in range(n)]
            item['clear_day_SW_centroid_offset_min_vs_UTC9_TOA']=clear_day_offsets(d['TIMESTAMP_START'],
                {'tower':[num(x) for x in d['SW_IN_F']],'shadow_after_C2':new_sw},toa,[is_qc(q,0) for q in d['SW_IN_F_QC']])
        res[cad]=item
    res['D2_zeroed_cells']=d2;res['source_zip_sha256_pre_post']=expected
    return res

def run(a):
    if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
    yms=load_yms_gauge(a.jf2024_yms);a.out.mkdir()
    report={'stage':'05BW','status':'DECIDED_CORRECTIONS_SHADOW_ONLY_HOLD_CELLS_UNRESOLVED','approved_by_user_20261104':['D1','D2'],
        'delegated_clock_decisions_20261104':['C1_TEF_TMD_UTC9_NO_CHANGE','C2_TOM_TOWER_TA_RH_VPD_SW_SHIFTM60','C3_JPF_QC2_ERA_SHIFTM60','C4_DATM_LABEL_UNCHANGED'],
        'jf2024_yms_sha256':JF2024_YMS[1],'sites':{}}
    for site in br.SITES:
        print('STAGE05BW JPF',site,flush=True);report['sites'][site]=jpf_site(site,br.source(a.root,a.layout,site),yms,a.out)
    for site in ('JP-Tom','JP-Tgf'):
        print('STAGE05BW SPECIAL',site,flush=True);report['sites'][site]=special_site(site,bs.source(a.root,a.layout,site),a.out)
    d2=report['sites']['JP-Tom']['D2_zeroed_cells']+report['sites']['JP-Tgf']['D2_zeroed_cells']
    if d2!=D2_EXPECTED:raise ValueError('D2 zeroed %d cells, expected %d'%(d2,D2_EXPECTED))
    report['D2_zeroed_cells_total']=d2;report['fingerprint_integers_strings']=br.fingerprint(report)
    with (a.out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    sums={s:(v['uncompressed_tsv_sha256'] if 'uncompressed_tsv_sha256' in v else {c:v[c]['uncompressed_tsv_sha256'] for c in ('HR','HH') if c in v}) for s,v in report['sites'].items()}
    print('STAGE05BW COMPLETE; SHADOW TABLES ONLY; HOLD CELLS UNRESOLVED; NO FORCING WRITTEN');print('OUTPUT',a.out)
    print(json.dumps({'fingerprint':report['fingerprint_integers_strings'],'D2_zeroed_cells_total':d2,'uncompressed_sha256':sums},indent=1))

def selftest():
    era_ts=[ts(datetime(2005,8,12,0)+i*STEP) for i in range(12)]
    era={'TA_ERA':['20']*12,'LW_IN_ERA':['400']*12}
    for i,x in ((5,'-120'),(6,'-270'),(7,'-120')):era['TA_ERA'][i]=x
    for i in (4,5):era['LW_IN_ERA'][i]='40'
    inst,interval,ev=artifact_rows(era_ts,era)
    assert inst=={era_ts[5],era_ts[6],era_ts[7]} and interval=={era_ts[4],era_ts[5]} and ev==[era_ts[5]]
    assert fmt(3.6/3.6)=='1.0' and fmt(1/3)=='0.333333' and hold('HOLD_X','ORIGINAL')=='HOLD_X' and hold('HOLD_X','C3')=='HOLD_X+C3'
    assert len(ws_stuck({'WS_F':['0.1']*30+['1.0'],'WS_F_QC':['0']*31},31))==30
    print('STAGE05BW SELF-TEST PASS; DECIDED-RULE SHADOWS ONLY; HOLD CELLS STAY HOLD')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--root',type=Path,default=br.IRIDIS_ROOT);p.add_argument('--layout',choices=('iridis','local'),default='iridis')
    p.add_argument('--jf2024-yms',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.out is None or a.jf2024_yms is None:p.error('--out and --jf2024-yms required')
    run(a)
if __name__=='__main__':main()

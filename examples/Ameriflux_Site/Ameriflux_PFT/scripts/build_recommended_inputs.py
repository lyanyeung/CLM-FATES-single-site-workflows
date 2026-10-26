#!/usr/bin/env python3
"""Rebuild/check the50 explicit FIXNC input hypotheses; no model files are edited."""
import argparse
import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATE='20261026'
DATA=ROOT/'metadata/recommended_inputs_v1_20261026.json'
MAP=ROOT/'metadata/recommended_hlm_profiles_v1_20261026.json'
LABEL={1:'TropEBF',2:'ENF',3:'DNF',4:'TempEBF',5:'TropHydroDT',6:'DBF',7:'EvergreenShrub',8:'HydrodecidShrub',9:'ColdDecidShrub',10:'ArcticEvergreenShrub',11:'ArcticDecidShrub',12:'ArcticC3',13:'CoolC3',14:'C4'}
BOREAL_NE={'CA-LP1','CA-Man','US-BZS','US-GLE','US-NR1','US-Uaf'}
BOREAL_BD={'US-Rpf'}

def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def csv_string(rows,fields):
    out=io.StringIO(newline='')
    w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
    w.writeheader();w.writerows(rows)
    return out.getvalue()

def textcell(value):
    return str(value).replace('|','&#124;').replace('\n',' ')

def choose_profile(vector):
    if 10 in vector or 11 in vector:
        if 8 in vector:
            raise ValueError('A joint Arctic+hydro mapping profile must be defined before use')
        return 'ARCTIC_PURE'
    return 'HYDRO_SHRUB' if 8 in vector else 'DEFAULT14'

def prescription(record,profiles):
    vector={int(k):float(v) for k,v in record['fates_natland_percent'].items()}
    bare=float(record['bare_percent'])
    if not 0<=bare<100 or any(k not in LABEL or not math.isfinite(v) or not 0<v<=100 for k,v in vector.items()):
        raise ValueError(f"Invalid percentage in{record['site']}")
    if abs(sum(vector.values())+bare-100)>1e-8:
        raise ValueError(f"Area sum is not100:{record['site']}")
    if len(vector)>4:
        raise ValueError(f"Default primary-land cap of4 live PFTs exceeded:{record['site']}")
    profile=choose_profile(vector)
    matrix=profiles['profiles'][profile]['map_stored_rows']
    if len(matrix)!=14 or any(len(row)!=14 or abs(sum(row)-1)>1e-9 for row in matrix):
        raise ValueError('Expected14x14 HLM map with unit row sums')
    host=[0.0]*15;host[0]=bare
    for slot,value in vector.items():
        candidates=[i+1 for i,row in enumerate(matrix)
                    if abs(row[slot-1]-1)<1e-9 and all(abs(x)<1e-9 for j,x in enumerate(row) if j!=slot-1)]
        if not candidates:
            raise ValueError(f'{record["site"]}: FATES{slot} not purely reachable in{profile}')
        preferred=2 if slot==2 and record['site'] in BOREAL_NE else 8 if slot==6 and record['site'] in BOREAL_BD else candidates[0]
        host[preferred if preferred in candidates else candidates[0]]+=value
    forward=[sum(host[i+1]*matrix[i][j] for i in range(14)) for j in range(14)]
    if abs(sum(host)-100)>1e-8 or any(abs(forward[j]-vector.get(j+1,0))>1e-8 for j in range(14)):
        raise ValueError('Host->FATES round-trip does not preserve prescribed natural-landunit areas')
    live={str(k):round(100*v/(100-bare),6) for k,v in vector.items()}
    if abs(sum(live.values())-100)>1e-5:
        raise ValueError('Vegetated-only normalized fractions do not sum100')
    human=' / '.join(f'{LABEL[k]} {v:g}' for k,v in sorted(vector.items()))
    if bare:
        human+=f' / bare {bare:g}'
    return vector,bare,profile,host,live,human

def generate():
    data=json.loads(DATA.read_text(encoding='utf-8'))
    profiles=json.loads(MAP.read_text(encoding='utf-8'))
    with (ROOT/'metadata/sites_50_manifest.csv').open(encoding='utf-8',newline='') as f:
        manifest=list(csv.DictReader(f))
    evidence={r['site']:r for p in sorted((ROOT/'metadata').glob('source_records_batch*.json')) for r in json.loads(p.read_text(encoding='utf-8'))}
    records={r['site']:r for r in data['records']}
    if len(data['records'])!=50 or len(records)!=50 or set(records)!={r['site'] for r in manifest}:
        raise ValueError('Expected exactly the50 original site IDs')
    primary=[];hostrows=[];fatesrows=[];all_diagnostics=[]
    for member in manifest:
        rec=records[member['site']]
        for key in ['target_state','target_period','basis','rationale','residual_policy','bare_policy','nonvascular_policy','uncertainty']:
            if not rec.get(key):
                raise ValueError(f'Missing decision provenance:{member["site"]}:{key}')
        vec,bare,profile,host,live,human=prescription(rec,profiles)
        if profile!=rec['mapping_profile']:
            raise ValueError(f"Incorrect profile label:{rec['site']}")
        row={**member,**rec,'recommended_percent':human,'fates_natland_percent_json':encode({str(k):v for k,v in vec.items()}),
             'clm_pct_nat_pft_json':encode({str(i):v for i,v in enumerate(host) if v}),
             'fates_vegetated_only_percent_json':encode(live),'mapping_profile':profile,
             'source_composition':evidence[rec['site']]['observed_composition'],
             'source_denominator':evidence[rec['site']]['denominator'],
             'source_urls':evidence[rec['site']]['source_url'],
             'source_locator':evidence[rec['site']]['source_locator'],
             'mode':'FIXNC; fixed_biogeog=true; nocomp=true; cold_start',
             'denominator':'MODEL_NATVEG_SOIL_LANDUNIT_INCLUDING_HOST_BARE0',
             'status':'RECOMMENDED_MODEL_HYPOTHESIS_V1_NOT_OBSERVATION',
             'active_case_parameter_verified':'NO','case_surface_or_job_modified':'NO'}
        primary.append(row)
        hostrows.append({'site':rec['site'],'batch':member['batch'],'mapping_profile':profile,
                         **{f'PCT_NAT_PFT_{i}':host[i] for i in range(15)}})
        fatesrows.append({'site':rec['site'],'batch':member['batch'],'mapping_profile':profile,'bare_pct_natland':bare,
                          **{f'FATES_PFT_{i:02}_pct_natland':vec.get(i,0) for i in range(1,15)},
                          **{f'FATES_PFT_{i:02}_pct_vegetated_only':live.get(str(i),0) for i in range(1,15)}})
        all_diagnostics.append({'site':rec['site'],'scenario':'PRIMARY','natural_area_sum':sum(host),'live_type_count':len(vec),'round_trip':'PASS','mapping_profile':profile})
    sensitivities=[]
    for alt in data['sensitivity_scenarios']:
        if alt['site'] not in records:
            raise ValueError('Unknown site in sensitivity table')
        vec,bare,profile,host,live,human=prescription(alt,profiles)
        sensitivities.append({**alt,'recommended_percent':human,'mapping_profile':profile,
                              'fates_natland_percent_json':encode({str(k):v for k,v in vec.items()}),
                              'clm_pct_nat_pft_json':encode({str(i):v for i,v in enumerate(host) if v}),
                              'fates_vegetated_only_percent_json':encode(live)})
        all_diagnostics.append({'site':alt['site'],'scenario':alt['scenario'],'natural_area_sum':sum(host),'live_type_count':len(vec),'round_trip':'PASS','mapping_profile':profile})
    fields=['site','batch','recommended_percent','bare_percent','mapping_profile','uncertainty','basis','target_state','target_period',
            'fates_natland_percent_json','clm_pct_nat_pft_json','fates_vegetated_only_percent_json','rationale','residual_policy','bare_policy',
            'nonvascular_policy','source_composition','source_denominator','source_urls','source_locator','mode','denominator','status',
            'active_case_parameter_verified','case_surface_or_job_modified']
    out={f'RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_{DATE}.csv':csv_string(primary,fields),
         f'RECOMMENDED_50_SITE_CLM_PCT_NAT_PFT_{DATE}.csv':csv_string(hostrows,['site','batch','mapping_profile']+[f'PCT_NAT_PFT_{i}' for i in range(15)]),
         f'RECOMMENDED_50_SITE_FATES_PFT_PERCENT_{DATE}.csv':csv_string(fatesrows,['site','batch','mapping_profile','bare_pct_natland']+[f'FATES_PFT_{i:02}_pct_natland' for i in range(1,15)]+[f'FATES_PFT_{i:02}_pct_vegetated_only' for i in range(1,15)]),
         f'PFT_INPUT_SENSITIVITY_SCENARIOS_{DATE}.csv':csv_string(sensitivities,['site','scenario','recommended_percent','bare_percent','mapping_profile','fates_natland_percent_json','clm_pct_nat_pft_json','fates_vegetated_only_percent_json','interpretation']),
         f'PFT_INPUT_VALIDATION_{DATE}.csv':csv_string(all_diagnostics,['site','scenario','natural_area_sum','live_type_count','round_trip','mapping_profile'])}
    report=['# 50个AmeriFlux站点：建议的CLM-FATES输入PFT百分比 v1','',
            '**2026年10月26日。下表已为全部50站给出具体、闭合到100%的主推荐；另有38组敏感性/时段替代方案。** 这是建模建议表，原实测证据表保持不变。', '',
            '适用范围：独立cold start、`use_fates_fixed_biogeog=.true.`且`use_fates_nocomp=.true.`（FIXNC）。下列百分比是**模型自然土壤landunit内的面积分配，含裸地host0**，不自动等于原始网格全部土地或观测足迹的实测覆盖率。竞争模式不能保证保持这些面积比例。','',
            '对新的理想化塔点，可将研究域定义为NATVEG100/CROP0的自然土壤点；这是另一个显式建模假设，不能因此改掉现有surface中的湖泊、湿地、农业等真实地类。本次只写建议表和参数映射配置，不写surface、现有parameter文件或作业。','',
            '## 可以直接查看的输入文件','',
            f'- [完整50站建议总表CSV](RECOMMENDED_50_SITE_CLM_FATES_INPUT_PFT_{DATE}.csv)：比例、目标状态、依据、余项处理、裸地假设及原始来源。',
            f'- [CLM host输入矩阵CSV](RECOMMENDED_50_SITE_CLM_PCT_NAT_PFT_{DATE}.csv)：`PCT_NAT_PFT_0`至`14`，每站合计100；0为裸地。若实际surface包含额外crop PFT槽位，先核对维度，不能盲目按15维重建变量。',
            f'- [FATES两种分母矩阵CSV](RECOMMENDED_50_SITE_FATES_PFT_PERCENT_{DATE}.csv)：`pct_natland`列加bare合计100；`pct_vegetated_only`列自身合计100。**不能将bare加到第二组再要求合计100。**',
            f'- [38组敏感性/时段替代CSV](PFT_INPUT_SENSITIVITY_SCENARIOS_{DATE}.csv)。',
            '- [三种HLM映射配置](metadata/recommended_hlm_profiles_v1_20261026.json)：包括原始默认映射及建议的独立站点映射。','',
            '例如US-Aud：自然土壤面积中C4=70、bare=30；活体植被内部C4=100。对应host14=70、host0=30。不能先把host14归一成100而丢掉裸地。','',
            '## 50站主推荐（%）','',
            '`ENF`常绿针叶树；`DBF`落叶阔叶树；`DNF`落叶针叶树；`TropEBF`热带常绿阔叶树；`EvergreenShrub`常绿灌木；`HydrodecidShrub`旱季落叶灌木；`ColdDecidShrub`寒季落叶灌木；`ArcticEvergreenShrub/ArcticDecidShrub`北极型常绿/落叶灌木；`ArcticC3/CoolC3/C4`分别为北极型C3、非北极型C3和C4草本代理。`bare`为无植被地表的模型分配。','',
            '| 批次 | 站点 | 建议百分比：自然土壤面积，含bare | 依据类型 | 不确定性 |','| --- | --- | --- | --- | --- |']
    for r in primary:
        report.append(f"| {r['batch']} | {r['site']} | {r['recommended_percent']} | {r['basis']} | {r['uncertainty']} |")
    counts=Counter(r['mapping_profile'] for r in primary)
    if data.get('revisions'):
        report+=['','## 修订记录','']
        for rv in data['revisions']:
            report.append(f"- **{rv['date']}**：{rv['change']}。{rv['reason']} 维持不变：{', '.join(rv.get('unchanged_by_decision',[]))}。")
    report+=['','## HLM映射与实际代码约束','',
             f"主推荐中DEFAULT14为{counts['DEFAULT14']}站，ARCTIC_PURE为{counts['ARCTIC_PURE']}站，HYDRO_SHRUB为{counts['HYDRO_SHRUB']}站。后两类需要站点独立参数文件的映射改动，不能只改surface后沿用原参数。",'',
             '| 配置 | 用途 | 修改范围 |','| --- | --- | --- |',
             '| DEFAULT14 | 常规树木、常绿灌木、冷落叶灌木及草 | 保留项目已记录的14×14映射 |',
             '| ARCTIC_PURE | BZS、EML、ICh、ICt、Uaf中的纯北极灌木 | host9→FATES10；host11→FATES11；其他行不变。host编号是映射选择器，实际植被性状由FATES列定义 |',
             '| HYDRO_SHRUB | Me2、Me6、Whs、Wkg的旱季落叶灌木 | host10→FATES8；其他行不变。默认映射无法到达FATES8 |','',
             '默认host11混合映射为FATES9/10/11=10/10/80，并非纯落叶北极灌木；默认host10映射到FATES9，并非FATES8。表内已按目标映射生成CLM输入，并逐站正向计算回FATES面积核对。', '',
             '项目所用代码仅在FIXNC中建立host0对应的固定裸地patch；固定生物地理＋竞争模式主要限制允许出现的PFT，整个column仍可用于竞争。现有restart不会因为替换surface自动重置面积。主推荐和替代方案均不超过默认primary land最多4个活体PFT的上限；裸地不计入这4类。', '',
             '[已记录的项目映射](https://github.com/lyanyeung/Non-Competition-CLM-experiment/blob/5165099b8daa47cc149b6b82750413d578cf0921/data/batch02_verified_HLM_FATES_map_20261025.json)；[所用FATES初始化代码](https://github.com/NGEET/fates/blob/121723f64e94be97fd91fc95cfd1ba72dfc191ee/main/EDInitMod.F90#L598-L658)；[裸地及面积初始化](https://github.com/NGEET/fates/blob/121723f64e94be97fd91fc95cfd1ba72dfc191ee/main/EDInitMod.F90#L855-L936)。这些代码依据不代表50个新case的实际parameter文件已经逐一检查。','',
             '## 采用建议时最重要的解释','',
             '1. **有观测数值也不自动是面积输入。** Borden、Harvard、Howland等使用株数/基面积作为面积代理；原始分母和归一化方法保存在CSV。Bartlett的3%余项在本建议中明确假定为其他针叶树，原始83/14/unknown3没有改写。',
             '2. **森林只有一种PFT不等于实测全地表100%树冠。** ENF100/DBF100是理想化森林功能型方案；林下与冠层的垂直重叠不能逐层相加。Me6、SP1、NC2等的林下比例属于显式先验。',
             '3. **苔原与泥炭地是高不确定性的维管植物投影。** Moss、lichen和biocrust没有独立PFT；没有把它们的观测份额改叫bare或grass。所列权重定义一个省略其显式功能的模型情景，不是完整生态系统地表分类；bare0只是该情景的约定。',
             '4. **干旱地裸地来源逐站区别。** Aud70/30保留既有用户选择；SRM35/20/45位于已报告范围内；Ses、Seg、Mpj、Wjs采用文献模型先例。Whs57、Wkg60及SRG45为模型面积分配，不能重新标成独立实测裸地。NR3 bare20完全是假设，附0/40替代。',
             '5. **物候和株型仍有近似。** 干旱落叶灌木用FATES8并配置独立映射；mesquite保持树型FATES6，但该默认类型的冷落叶性状并不等同于真实旱季落叶，后续需核对性状/根系。将苔草、阔叶草本合并到草PFT同样是功能代理。',
             '6. **固定状态不重建整段历史。** Vcm主推荐仅代表2013火灾前；Me2仅代表2020火灾前；Slt主推荐代表2018虫害后；UMd主推荐代表2008处理前。完整release年份的气象循环可驱动一个固定状态实验，但不能据此声称模拟了真实扰动历史。','',
             '## 每站决策与来源','']
    for r in primary:
        report += [f"### {r['site']} — {r['recommended_percent']}",'',
                   f"目标：{r['target_state']}；时段：{r['target_period']}。",'',
                   f"依据及建议：{r['rationale']} 余项处理：{r['residual_policy']}",'',
                   f"裸地：{r['bare_policy']} 非维管植物/地表约定：{r['nonvascular_policy']}",'',
                   f"原证据分母：{r['source_denominator']}。原始来源："+', '.join(f'[source{i}]({u.strip()})' for i,u in enumerate(r['source_urls'].split(';'),1) if u.strip())+'.','']
    report+=['## 重建与验证','','```bash','python3 scripts/build_recommended_inputs.py --build','python3 scripts/build_recommended_inputs.py --check','```','',
             '纯Python标准库。检查50个唯一站点、每批10个、所有主/替代方案面积闭合、活体PFT≤4、host→FATES精确回算、活体内部比例归一化，以及生成文件可重复。验证表列出全部88组方案。本次未修改已有模型输入或提交作业。']
    out[f'RECOMMENDED_INPUT_PFT_50_SITES_{DATE}.md']='\n'.join(report)+'\n'
    return out,len(primary),len(sensitivities),counts

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build',action='store_true');mode.add_argument('--check',action='store_true')
    args=parser.parse_args()
    generated,n,s,profiles=generate()
    failures=[]
    for name,content in generated.items():
        path=ROOT/name
        if args.build:
            path.write_text(content,encoding='utf-8',newline='\n')
        elif not path.exists() or path.read_text(encoding='utf-8')!=content:
            failures.append(name)
    if failures:
        raise SystemExit('Missing or different generated files:'+','.join(failures))
    print(f'PASS:{n}primary/{s}sensitivity;all natural-area sums100;vegetated-only sums100;max4livePFTs;host->FATES roundtrip exact;profiles={dict(profiles)};{len(generated)}reproducible outputs')

if __name__=='__main__':
    main()

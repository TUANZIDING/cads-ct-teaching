#!/usr/bin/env python3
"""项目检查 v1.1 / Offline project check (runs in CI on every push)
检查：本地链接与图片存在；文献编号与网页引用一一对应；167 个标签完整；论文原图都有 CC BY 4.0 署名与 DOI；
真实 CT 图都注明数据来源；许可文件齐全；不含个人邮箱/电话；新文件名不含下划线且带版本号；JSON 可解析。
v1.1 新增阅片器检查：数据文件齐全且体积受控（单文件 < 50 MB、合计 < 30 MB）；结构表与 验证/解剖名词对照表v1.1.csv 一致（每个名称可追溯）；
颜色两两可分、相邻结构色差足够；NiiVue 本地打包且附 BSD-2 许可；页面不引用任何 CDN 脚本；阅片器控件齐全；数据来源与许可在页面上可见。
（真实浏览器交互检查见 工具/阅片检查v1.1.py，需要 WebGL，CI 中不运行。）
Usage: python3 验证/项目检查v1.1.py"""
import os, re, json, sys, glob, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
fails, notes = [], []
def ok(cond, msg):
    (notes if cond else fails).append(('OK   ' if cond else 'FAIL ') + msg)

page = open('index.html', encoding='utf-8').read()
# 1) 本地资源
refs = set(re.findall(r'(?<![\w-])(?:src|href|data-full)="([^"#:]+?)"', page))
missing = [r for r in refs if not r.startswith(('http', 'mailto')) and not os.path.exists(html.unescape(r))]
ok(not missing, f'local links/images in index.html exist ({len(refs)} checked) {missing[:5]}')
# 1b) 阅片器 / interactive viewer (v1.1)
import csv, gzip, struct
V = 'assets/viewer/'
VF = ['ct-s0423-v1.1.nii.gz', 'ref-s0423-v1.1.nii.gz', 'cads554-s0423-v1.1.nii.gz', 'structures-v1.1.json', 'niivue-v0.69.0.umd.js']
ok(all(os.path.exists(V + f) for f in VF), f'viewer files present {[f for f in VF if not os.path.exists(V + f)]}')
sizes = {f: os.path.getsize(V + f) for f in VF if os.path.exists(V + f)}
ok(max(sizes.values()) < 50e6, f'every viewer file < 50 MB (max {max(sizes.values()) / 1e6:.1f} MB)')
pay = sum(v for k, v in sizes.items() if k.endswith(('.nii.gz', '.json')))
ok(pay < 30e6, f'viewer data payload < 30 MB ({pay / 1e6:.1f} MB; + NiiVue {sizes.get("niivue-v0.69.0.umd.js", 0) / 1e6:.1f} MB)')
VM = json.load(open(V + 'structures-v1.1.json', encoding='utf-8'))
ok(all(VM['sizes_bytes'][k] == sizes[k] for k in VM['sizes_bytes']), 'structures json records the actual file sizes')
TERMS = {r['totalsegmentator_class']: r for r in csv.DictReader(open('验证/解剖名词对照表v1.1.csv', encoding='utf-8'))}
ok(len(TERMS) == 117, f'term table covers all 117 TotalSegmentator v2 classes ({len(TERMS)})')
ok(all(r['中文名'] and r['English'] and r['Latin (TA2)'] and r['system'] for r in TERMS.values()), 'every term row has 中文 / English / Latin / system')
VS = VM['structures']
ok(len(VS) >= 100 and [s['idx'] for s in VS] == list(range(1, len(VS) + 1)), f'{len(VS)} viewer structures, label values 1..{len(VS)}')
ok(all(s['ts'] in TERMS and s['zh'] == TERMS[s['ts']]['中文名'] and s['en'] == TERMS[s['ts']]['English'] and s['la'] == TERMS[s['ts']]['Latin (TA2)'] for s in VS), 'every viewer name traceable to the term table')
cols = [tuple(s['rgb']) for s in VS]
ok(len(set(cols)) == len(cols), 'every structure has a unique colour')
ok(VM['min_deltaE_neighbours'] >= 30, f'adjacent / left-right / serial neighbours differ by ΔE ≥ 30 (min {VM["min_deltaE_neighbours"]})')
for f in VF[:3]:
    h = gzip.open(V + f).read(352)
    dims = struct.unpack('<8h', h[40:56]); pix = struct.unpack('<8f', h[76:108])
    ok(dims[0] == 3 and list(dims[1:4]) == VM['shape'] and abs(pix[1] - 1.5) < 1e-3, f'{f}: shape {dims[1:4]} spacing {pix[1]:.2f} mm')
nv = open(V + 'niivue-v0.69.0.umd.js', encoding='utf-8', errors='ignore').read(600)
ok('niivue' in nv, 'NiiVue UMD bundle is local')
ok(os.path.exists('LICENSES/NiiVue-BSD-2-Clause.txt') and 'BSD 2-Clause' in open('LICENSES/NiiVue-BSD-2-Clause.txt', encoding='utf-8').read(), 'NiiVue BSD-2-Clause notice in LICENSES/')
scripts = re.findall(r'<script[^>]+src="([^"]+)"', page) + re.findall(r'<link[^>]+href="([^"]+)"', page)
ok(not [u for u in scripts if u.startswith(('http:', 'https:', '//'))], f'no CDN scripts or stylesheets {scripts}')
for el in ['id="vw"', 'id="vwCanvas"', 'id="vwPlane"', 'data-p="ax"', 'data-p="cor"', 'data-p="sag"', 'data-p="r3d"', 'data-w="soft"', 'data-w="bone"', 'data-w="lung"',
           'data-src="ref"', 'data-src="cads"', 'id="vwAlpha"', 'data-m="outline"', 'id="vwTagBtn"', 'id="vwSearch"', 'id="vwLegend"', 'id="vwStops"', 'id="vwQuizBtn"', 'id="vwSl-ax"']:
    ok(el in page, f'viewer control {el}')
ok(page.index('id="viewer"') < page.index('id="why"'), 'viewer is the first section after the header')
ok('CC BY-NC-SA 4.0' in page and 'NiiVue' in page and 'BSD-2-Clause' in page, 'viewer provenance and licences shown on the page')
# 2) 文献
R = json.load(open('验证/参考文献v1.0.json', encoding='utf-8'))
ids = set(int(x) for x in re.findall(r'id="ref-(\d+)"', page))
cited = set(int(x) for x in re.findall(r'href="#ref-(\d+)"', page))
ok(ids == set(range(1, len(R) + 1)), f'reference list has {len(R)} entries, all rendered')
ok(cited <= ids, f'every in-text citation resolves ({len(cited)} distinct)')
ok(all(r.get('doi') for r in R), 'every reference has a DOI')
uncited = sorted(ids - cited)
notes.append(f'INFO references listed but not cited in text: {uncited} (listed as further reading)')
# 3) 标签
L = json.load(open('assets/data/labelsv1.0.json', encoding='utf-8'))['labels']
ok(len(L) == 167 and len({l['id'] for l in L}) == 167, '167 unique labels')
ok(all(l.get('snomed') and l.get('cases') and l.get('zh') for l in L), 'every label has SNOMED code, prevalence and Chinese name')
from collections import Counter
cnt = Counter(l['group'] for l in L)
ok(cnt == Counter({551: 17, 552: 24, 553: 18, 554: 21, 555: 24, 556: 15, 557: 9, 558: 29, 559: 10}), f'group sizes {dict(cnt)}')
# 4) 论文原图署名
figs = sorted(glob.glob('图片/论文原图/fig*v1.0.webp'))
figs = [f for f in figs if not f.endswith('-sm.webp')]
ok(len(figs) == 6, f'6 paper figures present ({len(figs)})')
for f in figs:
    i = page.find(f)
    seg = page[i:i + 3000]
    ok(i >= 0 and 'CC BY 4.0' in seg and '10.1038/s41467-026-78732-1' in seg, f'attribution + DOI next to {os.path.basename(f)}')
credits = open('文档/图片说明v1.1.md', encoding='utf-8').read()
for f in glob.glob('图片/*/*.webp'):
    if f.endswith('-sm.webp') or f.endswith('-raw.webp'): continue
    ok(os.path.basename(f) in credits, f'credited in 文档/图片说明v1.1.md: {os.path.basename(f)}')
# 5) 真实 CT 来源
ok(page.count('10.5281/zenodo.10047292') >= 5, 'TotalSegmentator dataset DOI shown with real-CT figures')
# 6) 许可
for p in ['LICENSES/NiiVue-BSD-2-Clause.txt', 'LICENSE', 'LICENSES/CC-BY-NC-4.0.txt', 'LICENSES/CC-BY-4.0.txt', 'LICENSES/PolyForm-Noncommercial-1.0.0.md', 'LICENSES/Apache-2.0.txt', 'CITATION.cff']:
    ok(os.path.exists(p), f'{p} present')
lic = open('LICENSE', encoding='utf-8').read()
ok('https://tuanziding.github.io/#contact' in lic and 'https://tuanziding.github.io/#contact' in page, 'commercial-use contact link present')
# 7) 隐私
alltext = ''
for f in glob.glob('**/*', recursive=True):
    if os.path.isfile(f) and f.endswith(('.md', '.html', '.json', '.py', '.cff', '.yml', '.js', '.css', '.bib', '.sh')) and not f.startswith('LICENSES/') and not f.endswith('.umd.js'):  # 第三方压缩包不扫描
        alltext += open(f, encoding='utf-8', errors='ignore').read()
emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', alltext)) - {'murong.xu@uzh.ch', 'git@github.com'}
emails = {e for e in emails if not e.endswith('users.noreply.github.com')}
ok(not emails, f'no personal e-mail addresses {sorted(emails)[:3]}')
ok(not re.search(r'(?<!\d)1[3-9]\d{9}(?!\d)', alltext), 'no mobile phone numbers')
# 8) 命名规则：新文件名不含下划线且带版本号（README/LICENSE/index.html/CITATION/.nojekyll/assets/ct 切片除外）
EXEMPT = {'README.md', 'LICENSE', 'index.html', 'CITATION.cff', '.nojekyll'}
bad = []
for f in glob.glob('**/*', recursive=True):
    if not os.path.isfile(f) or f.startswith(('LICENSES/', '.git/')): continue
    b = os.path.basename(f)
    if b in EXEMPT: continue
    if '_' in b or not re.search(r'v\d+\.\d+', b): bad.append(f)
ok(not bad, f'file names: no underscores, carry a version {bad[:5]}')
# 9) JSON
for f in glob.glob('**/*.json', recursive=True):
    try: json.load(open(f, encoding='utf-8'))
    except Exception as e: fails.append(f'FAIL invalid JSON {f}: {e}')
# 10) 不分发 CADS 数据/权重
heavy = [f for f in glob.glob('**/*', recursive=True) if f.endswith(('.pth', '.nii.gz', '.nii', '.zip')) and not f.startswith('assets/viewer/')]
ok(not heavy, f'no CADS weights / CADS-dataset volumes redistributed (only the s0423 viewer volumes) {heavy[:3]}')

print('\n'.join(notes + fails))
print(f'\n{len(notes)} ok/info, {len(fails)} failed')
sys.exit(1 if fails else 0)

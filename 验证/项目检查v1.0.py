#!/usr/bin/env python3
"""项目检查 v1.0 / Offline project check (runs in CI on every push)
检查：本地链接与图片存在；文献编号与网页引用一一对应；167 个标签完整；论文原图都有 CC BY 4.0 署名与 DOI；
真实 CT 图都注明数据来源；许可文件齐全；不含个人邮箱/电话；新文件名不含下划线且带版本号；JSON 可解析。
Usage: python3 验证/项目检查v1.0.py"""
import os, re, json, sys, glob, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
fails, notes = [], []
def ok(cond, msg):
    (notes if cond else fails).append(('OK   ' if cond else 'FAIL ') + msg)

page = open('index.html', encoding='utf-8').read()
# 1) 本地资源
refs = set(re.findall(r'(?:src|href|data-full)="([^"#:]+?)"', page))
missing = [r for r in refs if not r.startswith(('http', 'mailto')) and not os.path.exists(html.unescape(r))]
ok(not missing, f'local links/images in index.html exist ({len(refs)} checked) {missing[:5]}')
ct = json.load(open('assets/data/ctcasev1.0.json', encoding='utf-8'))
n = len(ct['zs'])
miss_ct = [k for k in range(n) for t in ('soft.webp', 'wide.webp', 'lab.png') if not os.path.exists(f'assets/ct/ax-{k:03d}-{t}')]
ok(not miss_ct, f'viewer slices complete ({n} × 3 files)')
if 'cads_inference' in ct:
    miss_p = [k for k in ct['cads_inference']['viewer_slices'] if not os.path.exists(f'assets/ct/ax-{k:03d}-cads.png')]
    ok(not miss_p, f'CADS inference slices complete ({len(ct["cads_inference"]["viewer_slices"])})')
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
credits = open('文档/图片说明v1.0.md', encoding='utf-8').read()
for f in glob.glob('图片/*/*.webp'):
    if f.endswith('-sm.webp') or f.endswith('-raw.webp'): continue
    ok(os.path.basename(f) in credits, f'credited in 文档/图片说明v1.0.md: {os.path.basename(f)}')
# 5) 真实 CT 来源
ok(page.count('10.5281/zenodo.10047292') >= 5, 'TotalSegmentator dataset DOI shown with real-CT figures')
# 6) 许可
for p in ['LICENSE', 'LICENSES/CC-BY-NC-4.0.txt', 'LICENSES/CC-BY-4.0.txt', 'LICENSES/PolyForm-Noncommercial-1.0.0.md', 'LICENSES/Apache-2.0.txt', 'CITATION.cff']:
    ok(os.path.exists(p), f'{p} present')
lic = open('LICENSE', encoding='utf-8').read()
ok('https://tuanziding.github.io/#contact' in lic and 'https://tuanziding.github.io/#contact' in page, 'commercial-use contact link present')
# 7) 隐私
alltext = ''
for f in glob.glob('**/*', recursive=True):
    if os.path.isfile(f) and f.endswith(('.md', '.html', '.json', '.py', '.cff', '.yml', '.js', '.css', '.bib', '.sh')) and not f.startswith('LICENSES/'):
        alltext += open(f, encoding='utf-8', errors='ignore').read()
emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', alltext)) - {'murong.xu@uzh.ch', 'git@github.com'}
emails = {e for e in emails if not e.endswith('users.noreply.github.com')}
ok(not emails, f'no personal e-mail addresses {sorted(emails)[:3]}')
ok(not re.search(r'(?<!\d)1[3-9]\d{9}(?!\d)', alltext), 'no mobile phone numbers')
# 8) 命名规则：新文件名不含下划线且带版本号（README/LICENSE/index.html/CITATION/.nojekyll/assets/ct 切片除外）
EXEMPT = {'README.md', 'LICENSE', 'index.html', 'CITATION.cff', '.nojekyll'}
bad = []
for f in glob.glob('**/*', recursive=True):
    if not os.path.isfile(f) or f.startswith(('LICENSES/', 'assets/ct/', '.git/')): continue
    b = os.path.basename(f)
    if b in EXEMPT: continue
    if '_' in b or not re.search(r'v\d+\.\d+', b): bad.append(f)
ok(not bad, f'file names: no underscores, carry a version {bad[:5]}')
# 9) JSON
for f in glob.glob('**/*.json', recursive=True):
    try: json.load(open(f, encoding='utf-8'))
    except Exception as e: fails.append(f'FAIL invalid JSON {f}: {e}')
# 10) 不分发 CADS 数据/权重
heavy = [f for f in glob.glob('**/*', recursive=True) if f.endswith(('.pth', '.nii.gz', '.nii', '.zip'))]
ok(not heavy, f'no CADS weights / NIfTI volumes redistributed {heavy[:3]}')

print('\n'.join(notes + fails))
print(f'\n{len(notes)} ok/info, {len(fails)} failed')
sys.exit(1 if fails else 0)

#!/usr/bin/env python3
"""构建讲义 v1.0 / Build Markdown handouts from index.html
把网页拆成中文、英文两份单语 HTML，再用 pandoc 转为 GitHub Markdown：
  文档/教学讲义-中文v1.0.md   文档/教学讲义-英文v1.0.md
互动部分（标签浏览器、阅片器、测验按钮）在讲义中以文字提示代替。
Usage: python3 工具/构建讲义v1.0.py [repo_root]   (需要 beautifulsoup4 与 pandoc)"""
import sys, os, subprocess, re
from bs4 import BeautifulSoup
R = sys.argv[1] if len(sys.argv) > 1 else '.'
src = open(f'{R}/index.html', encoding='utf-8').read()
for lang, other, out, note in [('zh', 'en', '教学讲义-中文v1.0.md', '> 本讲义由网页自动生成（v1.0.0）。互动功能（167 结构浏览器、真实 CT 阅片器、测验）请在线使用：https://tuanziding.github.io/cads-ct-teaching/'),
                               ('en', 'zh', '教学讲义-英文v1.0.md', '> Generated from the web page (v1.0.0). Interactive parts (label browser, real-CT viewer, quiz) are online: https://tuanziding.github.io/cads-ct-teaching/')]:
    s = BeautifulSoup(src, 'html.parser')
    for el in s.select(f'.{other}'): el.decompose()
    for sel in ['script', '.bar', '.lbx', '.vside', '.lbtools', '#lbChips', '#lbList', '#lbDetail', '.vmain', '.btns', 'footer', '.sr']:
        for el in s.select(sel): el.decompose()
    for t in s.select('span.tag'): t.replace_with(f'【{t.get_text()}】')
    for t in s.select('span.no'): t.replace_with(t.get_text() + ' · ')
    for t in s.select('.stat b'): t.replace_with(t.get_text() + ' ')
    for b in s.select('figure button'):
        img = b.find('img')
        if img: img['src'] = '../' + b.get('data-full', img['src']); b.replace_with(img)
    for img in s.find_all('img'):
        if not img['src'].startswith(('../', 'http')): img['src'] = '../' + img['src']
    for q in s.select('.q'):
        ans = int(q.get('data-a', 0))
        for i, o in enumerate(q.select('button.o')):
            o.name = 'p'; o.string = ('✅ ' if i == ans else '◻️ ') + o.get_text()
    for b in s.find_all('button'): b.decompose()
    main = s.find('main')
    h = f'<html><body>{main}</body></html>'
    md = subprocess.run(['pandoc', '-f', 'html', '-t', 'gfm-raw_html', '--wrap=none'], input=h, capture_output=True, text=True, check=True).stdout
    md = re.sub(r'\n{3,}', '\n\n', md)
    import json
    L = json.load(open(f'{R}/assets/data/labelsv1.0.json', encoding='utf-8'))['labels']
    hdr = ('\n\n## 附录 · 167 个结构（来源：官方 labelmap、论文表 2、补充表 1）\n\n| 组 | # | 中文 | English | SNOMED CT | 出现于（/22,022） | 中位体素 |\n| --- | --- | --- | --- | --- | --- | --- |\n' if lang == 'zh' else
           '\n\n## Appendix · the 167 structures (sources: official labelmap, Table 2, Suppl. Table 1)\n\n| Group | # | English | Chinese | SNOMED CT | Present in (/22,022) | Median voxels |\n| --- | --- | --- | --- | --- | --- | --- |\n')
    md += hdr + ''.join(f"| T{l['group']} | {l['index']} | {l['zh'] if lang=='zh' else l['en']} | {l['en'] if lang=='zh' else l['zh']} | {l['snomed']}{(' \\| ' + l['snomed_lat']) if l.get('snomed_lat') else ''} | {l['cases']:,} | {l['median_voxels']:,} |\n" for l in L)
    title = '# CADS 全身 CT 解剖分割 · 教学讲义 v1.0' if lang == 'zh' else '# CADS whole-body CT anatomy segmentation · teaching handout v1.0'
    open(f'{R}/文档/{out}', 'w', encoding='utf-8').write(title + '\n\n' + note + '\n\n' + md)
    print(out, len(md))

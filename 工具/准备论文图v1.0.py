#!/usr/bin/env python3
"""准备论文图 v1.0 / Prepare paper figures (CC BY 4.0)
从 Nature Communications 的 Article-in-Press PDF（https://www.nature.com/articles/s41467-026-78732-1_reference.pdf）
渲染第 5、6、7、9、10、11 页，按图题位置裁出 Fig. 1–6（连同原图注），转为 WebP；除裁剪、缩放和格式转换外不作改动。
Usage: python3 工具/准备论文图v1.0.py <aip.pdf> <out_dir>   (需要 poppler-utils: pdftoppm, pdftotext)"""
import subprocess, re, sys, os
import numpy as np
from PIL import Image
pdf, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
DPI = 220; S = DPI / 72
FIGS = {5: 1, 6: 2, 7: 3, 9: 4, 10: 5, 11: 6}
NAMES = {1: 'fig1-anatomical-coverage', 2: 'fig2-pipeline', 3: 'fig3-structure-dice', 4: 'fig4-benchmark', 5: 'fig5-qualitative', 6: 'fig6-slicer'}
for p, n in FIGS.items():
    base = f'/tmp/cadsfig-p{p}'
    subprocess.run(['pdftoppm', '-f', str(p), '-l', str(p), '-r', str(DPI), '-png', '-singlefile', pdf, base], check=True)
    x = subprocess.run(['pdftotext', '-f', str(p), '-l', str(p), '-bbox', pdf, '-'], capture_output=True, text=True).stdout
    w = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', x)
    cap = next(float(w[i][1]) for i in range(len(w) - 1) if w[i][4] == 'Fig.' and w[i + 1][4] == str(n))
    im = Image.open(base + '.png'); a = np.array(im.convert('L')); rows = (a < 235).sum(1)
    y = int(cap * S); blank = 0
    while y < a.shape[0]:
        blank = blank + 1 if rows[y] == 0 else 0
        if blank >= int(22 * DPI / 200): break
        y += 1
    bottom = y - blank + 6
    top = int(0.045 * a.shape[0])
    while rows[top] == 0: top += 1
    # 跳过页眉横线（若存在）
    if rows[top] > 0.6 * a.shape[1]: top += 4
    while rows[top] == 0: top += 1
    crop = im.crop((int(60 * DPI / 200), top - 8, a.shape[1] - int(60 * DPI / 200), bottom)).convert('RGB')
    crop.save(f'{out}/{NAMES[n]}v1.0.webp', quality=90, method=6)
    sm = crop.copy(); sm.thumbnail((900, 900)); sm.save(f'{out}/{NAMES[n]}v1.0-sm.webp', quality=82, method=6)
    print(n, crop.size)

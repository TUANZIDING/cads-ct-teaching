#!/usr/bin/env python3
"""制作封面 v1.0 / Make cover image
用本仓库的真实 CT 渲染图（TotalSegmentator 数据集 s0423，CC BY 4.0）与标题文字合成封面；不含任何 AI 生成图像。
Usage: python3 工具/制作封面v1.0.py [repo_root]   (需要 Noto Sans CJK 字体)"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
R = sys.argv[1] if len(sys.argv) > 1 else '.'
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; FR = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if not os.path.exists(FB): FB = FR
W, H = 1600, 800
c = Image.new('RGB', (W, H), (6, 10, 15)); d = ImageDraw.Draw(c)
for x in range(0, W, 32): d.line([(x, 0), (x, H)], fill=(10, 20, 28))
for y in range(0, H, 32): d.line([(0, y), (W, y)], fill=(10, 20, 28))
cor = Image.open(f'{R}/图片/真实CT/ct-coronal-ts-v1.0.webp').convert('RGB')
cor = cor.resize((int(cor.width * 760 / cor.height), 760)); c.paste(cor, (W - cor.width - 20, 20))
ax = Image.open(f'{R}/图片/真实CT/ct-l3-ts-v1.0.webp').convert('RGB').crop((90, 180, 726, 700)); ax = ax.resize((int(ax.width * 0.62), int(ax.height * 0.62)))
c.paste(ax, (W - cor.width - 40 - ax.width, H - ax.height - 80))
d.rectangle([W - cor.width - 40 - ax.width, H - ax.height - 80, W - cor.width - 40, H - 80], outline=(70, 211, 234), width=2)
f = lambda p, s: ImageFont.truetype(p, s, index=2 if p.endswith('.ttc') else 0)
d.text((60, 70), 'MEDICAL IMAGING AI · TEACHING MODULE v1.0.0', font=f(FR, 22), fill=(70, 211, 234))
d.text((60, 115), 'CADS', font=f(FB, 96), fill=(230, 238, 245))
d.text((60, 235), '全身 CT 的 167 个解剖结构', font=f(FB, 52), fill=(230, 238, 245))
d.text((60, 305), 'Whole-body CT · 167 structures · 中文 / English', font=f(FR, 28), fill=(159, 179, 196))
y = 380
for big, small in [('22,022', 'CT 体数据 · CT volumes'), ('40 / 100+ / 16', '来源 / 中心 / 国家 · sources / centres / countries'), ('18 + 2,864', '公开测试集 + 真实世界 CT · public test sets + real-world CTs')]:
    d.text((60, y), big, font=f(FB, 40), fill=(230, 238, 245)); d.text((60, y + 52), small, font=f(FR, 20), fill=(159, 179, 196)); y += 100
d.text((60, H - 46), 'Xu M et al. Nat Commun 2026 · doi:10.1038/s41467-026-78732-1 · 图像：TotalSegmentator s0423 真实 CT（CC BY 4.0）', font=f(FR, 17), fill=(125, 147, 166))
os.makedirs(f'{R}/文档/主图', exist_ok=True)
c.save(f'{R}/文档/主图/封面v1.0.jpg', quality=88)
print('cover saved')

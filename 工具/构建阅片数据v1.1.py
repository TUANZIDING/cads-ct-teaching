#!/usr/bin/env python3
"""构建阅片数据 v1.1 / Build the interactive viewer data
输入：TotalSegmentator dataset v2.0.1 病例 s0423（ct.nii.gz + segmentations/*.nii.gz；doi:10.5281/zenodo.10047292，CC BY 4.0）
      CADS-model-research 任务 554 在该病例上的真实推理结果（见 验证/推理记录v1.0.md；输出 CC BY-NC-SA 4.0）
输出（assets/viewer/）：
  ct-s0423-v1.1.nii.gz        int16 HU，1.5 mm 各向同性 RAS，裁去体外空气（体外体素置 -1024）
  ref-s0423-v1.1.nii.gz       uint8 合并标签体积：全部非空参考掩膜（≥50 体素），标签值 = structures 表的 idx
  cads554-s0423-v1.1.nii.gz   uint8 CADS 推理结果，按同名类别映射到同一 idx（同一结构同一颜色）
  structures-v1.1.json        名称（中/英/拉丁，来自 验证/解剖名词对照表v1.1.csv）、系统、颜色、体素数、跳转点
颜色：在 CIELAB 中生成高饱和候选色，按“与相邻结构（3D 接触或 ≤2 体素）及左右对侧结构的最小色差最大”贪心分配。
Usage: python3 工具/构建阅片数据v1.1.py <s0423_dir> <cads554.nii.gz> <cads554.json> [repo_root]
       python3 工具/构建阅片数据v1.1.py - - - [repo_root] --recolour   （只重算颜色）"""
import sys, os, json, csv, glob
import numpy as np, nibabel as nib
from scipy import ndimage

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
case, cads_p, cads_j = (ARGS + [None] * 3)[:3]
ROOT = ARGS[3] if len(ARGS) > 3 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f'{ROOT}/assets/viewer'; os.makedirs(OUT, exist_ok=True)
TERMS = {r['totalsegmentator_class']: r for r in csv.DictReader(open(f'{ROOT}/验证/解剖名词对照表v1.1.csv', encoding='utf-8'))}

def palette(lab, names):
    import re
    # 邻接图（3D 6 邻域，间隔 1 与 2 体素）
    pairs = set()
    for ax in range(3):
        for g in (1, 2):
            a = np.take(lab, range(0, lab.shape[ax] - g), axis=ax); c = np.take(lab, range(g, lab.shape[ax]), axis=ax)
            m = (a != c) & (a > 0) & (c > 0)
            code = np.unique(a[m].astype(np.int32) * 256 + c[m])
            pairs |= {tuple(sorted((int(v // 256), int(v % 256)))) for v in code}
            del a, c, m
    N = len(names)
    nb = {i: set() for i in range(1, N + 1)}
    for a, c in pairs: nb[a].add(c); nb[c].add(a)
    for i, n in enumerate(names, 1):  # 左右对侧视为邻居
        for s, o in (('left', 'right'), ('right', 'left')):
            if s in n.split('_'):
                j = n.replace(s, o)
                if j in names: nb[i].add(names.index(j) + 1)
    # 同类序列（相邻肋骨、相邻椎骨）也视为邻居
    import re
    for i, n in enumerate(names, 1):
        m = re.match(r'(rib_(?:left|right)_|vertebrae_[CTLS])(\d+)$', n)
        if m:
            for d in (-1, 1):
                j = f'{m.group(1)}{int(m.group(2)) + d}'
                if j in names: nb[i].add(names.index(j) + 1)

    # CIELAB 候选色
    def lab2rgb(L, a, b_):
        fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b_ / 200
        f = lambda t: np.where(t > 6 / 29, t ** 3, 3 * (6 / 29) ** 2 * (t - 4 / 29))
        X, Y, Z = 0.95047 * f(fx), f(fy), 1.08883 * f(fz)
        r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z; g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z; bb = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
        rgb = np.stack([r, g, bb], -1); ok = np.all((rgb >= 0) & (rgb <= 1), -1)
        c = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * np.clip(rgb, 1e-9, None) ** (1 / 2.4) - 0.055)
        return np.clip(c, 0, 1), ok
    cand = []
    for L in (52, 62, 72, 82):
        for h in np.arange(0, 360, 6):
            for C in (55, 75, 95):
                rgb, ok = lab2rgb(np.array(L, float), C * np.cos(np.radians(h)), C * np.sin(np.radians(h)))
                if ok: cand.append(((L, C * np.cos(np.radians(h)), C * np.sin(np.radians(h))), rgb))
    CL = np.array([c[0] for c in cand]); CR = np.array([c[1] for c in cand])
    print('candidates', len(cand))
    order = sorted(range(1, N + 1), key=lambda i: -len(nb[i]))
    col = {}
    for i in order:
        dn = np.full(len(CL), 999.0); da = np.full(len(CL), 999.0)
        for j in nb[i]:
            if j in col: dn = np.minimum(dn, np.linalg.norm(CL - CL[col[j]], axis=1))
        for j in col.values(): da = np.minimum(da, np.linalg.norm(CL - CL[j], axis=1))
        score = np.minimum(dn, 60) * 3 + np.minimum(da, 25)
        score[list(col.values())] = -1e9   # 每个结构一种独有颜色 / every structure gets its own colour
        col[i] = int(np.argmax(score))
    rgb = {i: [int(round(v * 255)) for v in CR[col[i]]] for i in col}
    mind = min(np.linalg.norm(CL[col[a]] - CL[col[c]]) for a, c in pairs) if pairs else 0
    mind_lr = min(np.linalg.norm(CL[col[i]] - CL[col[j]]) for i in nb for j in nb[i])
    print('min ΔE among neighbours', round(float(mind), 1), 'incl. L/R & series', round(float(mind_lr), 1))

    return rgb, pairs, mind_lr

# 跳转点：结构中位层面上二维距离变换最大的体素（保证落在结构内部、远离边界）
# jump point: on the structure's median axial slice, the voxel farthest from the boundary (2D distance transform maximum)
def jump_point(lab, i, o):
    m = lab[o] == i; zz = np.where(m.any((0, 1)))[0]; z = int(zz[len(zz) // 2])
    d = ndimage.distance_transform_edt(np.pad(m[:, :, z], 1))[1:-1, 1:-1]
    p = np.unravel_index(int(np.argmax(d)), d.shape)
    return m, zz, [int(p[0] + o[0].start), int(p[1] + o[1].start), int(z + o[2].start)], [int(zz[0] + o[2].start), int(zz[-1] + o[2].start)]

# --recolour：只按现有标签体积重新分配颜色（不重读 CT / 掩膜，省内存）/ recompute colours only from the existing label volume
if '--recolour' in sys.argv:
    M = json.load(open(f'{OUT}/structures-v1.1.json', encoding='utf-8'))
    lab = np.asanyarray(nib.load(f'{OUT}/ref-s0423-v1.1.nii.gz').dataobj)
    names = [d['ts'] for d in M['structures']]
    rgb, pairs, mind_lr = palette(lab, names)
    objs = ndimage.find_objects(lab)
    for d in M['structures']:
        d['rgb'] = rgb[d['idx']]
        if objs[d['idx'] - 1] is not None:
            _, _, d['jump'], d['zrange'] = jump_point(lab, d['idx'], objs[d['idx'] - 1])
        assert lab[tuple(d['jump'])] == d['idx'], d['ts']
    M['min_deltaE_neighbours'] = round(float(mind_lr), 1)
    json.dump(M, open(f'{OUT}/structures-v1.1.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('recoloured', len(names), 'min ΔE', M['min_deltaE_neighbours'], 'unique', len({tuple(v) for v in rgb.values()}), 'jump points inside mask: all'); sys.exit(0)

img = nib.load(f'{case}/ct.nii.gz'); assert nib.aff2axcodes(img.affine) == ('R', 'A', 'S')
assert np.allclose(img.header.get_zooms()[:3], 1.5)
ct = np.asanyarray(img.dataobj).astype(np.int16)

# 体部掩膜：HU>-500 的最大连通域（2 倍下采样求取后放大），膨胀 3 体素
b = ndimage.binary_opening(ct[::2, ::2, ::2] > -500, iterations=2)
cc, n = ndimage.label(b); k = int(np.argmax(ndimage.sum(b, cc, range(1, n + 1)))) + 1
body = ndimage.binary_dilation(cc == k, iterations=3).repeat(2, 0).repeat(2, 1).repeat(2, 2)[:ct.shape[0], :ct.shape[1], :ct.shape[2]]
del b, cc
idx = np.argwhere(body[::2, ::2, ::2]) * 2
lo = np.maximum(idx.min(0) - 2, 0); hi = np.minimum(idx.max(0) + 4, ct.shape)
sl = tuple(slice(a, b) for a, b in zip(lo, hi))
ctc = np.clip(ct[sl], -1024, 3071); ctc[~body[sl]] = -1024
del ct, body
aff = img.affine.copy(); aff[:3, 3] = img.affine[:3, :3] @ lo + img.affine[:3, 3]

# 合并参考掩膜：按体积从大到小写入，小结构覆盖重叠处
names, vols = [], {}
for f in sorted(glob.glob(f'{case}/segmentations/*.nii.gz')):
    n = os.path.basename(f)[:-7]; m = np.asanyarray(nib.load(f).dataobj)[sl] > 0
    if m.sum() >= 50: vols[n] = m
SYS_ORDER = ['skeletal', 'muscular', 'cardiovascular', 'respiratory', 'digestive', 'urinary', 'reproductive', 'endocrine', 'lymphatic', 'nervous', 'other']
def sortkey(n):
    t = TERMS[n]; import re
    m = re.match(r'(rib|vertebrae)_(?:(left|right)_)?([A-Z]?)(\d+)', n)
    if m: return (SYS_ORDER.index(t['system']), m.group(1), {'C': 0, 'T': 1, 'L': 2, 'S': 3}.get(m.group(3), 0), int(m.group(4)), m.group(2) or '')
    return (SYS_ORDER.index(t['system']), n, 0, 0, '')
names = sorted(vols, key=sortkey)
lab = np.zeros(ctc.shape, np.uint8); overlap = {}
for n in sorted(names, key=lambda n: -vols[n].sum()):
    i = names.index(n) + 1; m = vols[n]
    ov = int((m & (lab > 0)).sum())
    if ov: overlap[n] = ov
    lab[m] = i
del vols

rgb, pairs, mind_lr = palette(lab, names)

objs = ndimage.find_objects(lab)
S = []
for i, n in enumerate(names, 1):
    o = objs[i - 1]; m, zz, jp, zr = jump_point(lab, i, o)
    t = TERMS[n]
    S.append({'idx': i, 'ts': n, 'zh': t['中文名'], 'en': t['English'], 'la': t['Latin (TA2)'], 'sys': t['system'], 'side': t['side'],
              'note': t['备注 note'], 'rgb': rgb[i], 'voxels': int(m.sum()), 'ml': round(float(m.sum()) * 1.5 ** 3 / 1000, 1),
              'jump': jp, 'zrange': zr, 'overlap_voxels': overlap.get(n, 0)})

# CADS 推理：同名类别映射到同一 idx
cj = json.load(open(cads_j))
cp = np.asanyarray(nib.load(cads_p).dataobj)[sl].astype(np.uint8)
remap = np.zeros(256, np.uint8); cads_names = []
for n, v in cj['labels'].items():
    if v and n in names: remap[v] = names.index(n) + 1
    if v: cads_names.append(n)
cl = remap[cp]; present = sorted(int(v) for v in np.unique(cl) if v)
X0, X1, Y0, Y1, Z0, Z1 = cj['crop_xyz']
cads_box = [X0 - int(lo[0]), X1 - int(lo[0]), Y0 - int(lo[1]), Y1 - int(lo[1]), Z0 - int(lo[2]), Z1 - int(lo[2])]

def save(a, fn, desc):
    im = nib.Nifti1Image(a, aff); im.header['descrip'] = desc.encode()[:79]; im.header.set_xyzt_units('mm')
    im.set_qform(aff, 1); im.set_sform(aff, 1)
    nib.save(im, f'{OUT}/{fn}'); return os.path.getsize(f'{OUT}/{fn}')
sizes = {
 'ct-s0423-v1.1.nii.gz': save(ctc, 'ct-s0423-v1.1.nii.gz', 'TotalSegmentator v2.0.1 s0423 CT, CC BY 4.0'),
 'ref-s0423-v1.1.nii.gz': save(lab, 'ref-s0423-v1.1.nii.gz', 'TotalSegmentator v2.0.1 s0423 reference masks, CC BY 4.0'),
 'cads554-s0423-v1.1.nii.gz': save(cl, 'cads554-s0423-v1.1.nii.gz', 'CADS-model-research T554 output on s0423, CC BY-NC-SA 4.0'),
}
meta = {'version': '1.1.0', 'case': 's0423', 'shape': list(ctc.shape), 'spacing_mm': 1.5, 'orientation': 'RAS+: voxel i increases toward patient Right, j Anterior, k Superior',
        'crop_from_original': [int(v) for v in lo], 'original_shape': list(img.shape),
        'sources': {'ref': 'TotalSegmentator dataset v2.0.1 (Wasserthal et al. 2023), doi:10.5281/zenodo.10047292, CC BY 4.0; masks = dataset reference annotations',
                    'cads': 'CADS-model-research v1.0.0 task 554 (Dataset554_Totalseg254), run once by the author on CPU; output CC BY-NC-SA 4.0; see 验证/推理记录v1.0.md'},
        'cads_box_vox': cads_box, 'cads_classes': cads_names, 'cads_present_idx': present,
        'min_deltaE_neighbours': round(float(mind_lr), 1), 'sizes_bytes': sizes, 'structures': S}
json.dump(meta, open(f'{OUT}/structures-v1.1.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('structures', N, 'shape', ctc.shape, 'sizes MB', {k: round(v / 1e6, 2) for k, v in sizes.items()}, 'overlaps', overlap)

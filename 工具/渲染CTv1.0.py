#!/usr/bin/env python3
"""渲染CT v1.0 / Render real CT slices with real reference masks
数据：TotalSegmentator dataset v2.0.1（Wasserthal et al., Zenodo, doi:10.5281/zenodo.10047292, CC BY 4.0）病例 s0423
（元数据：65 岁男性，ct neck-thorax-abdomen-pelvis，pathology=trauma，location=thorax；属于 CADS 论文公开的测试划分）。
掩膜是该数据集自带的参考标注（TotalSegmentator 团队：模型生成 + 人工校正），不是 CADS 的输出。
输出：
  assets/ct/ax-NNN-soft.webp / ax-NNN-wide.webp / ax-NNN-lab.png   交互阅片器切片（每 3 层取 1 层）
  assets/ct/cor-soft.webp                                             冠状位定位图
  assets/data/ctcasev1.0.json                                         切片索引、标签表、L3 测量
  图片/真实CT/*.webp                                                   静态教学图（无文字，图注在网页/README）
Usage: python3 工具/渲染CTv1.0.py <case_dir> <repo_root> [cads_pred.nii.gz]"""
import sys, os, json, glob
import numpy as np, nibabel as nib
from PIL import Image

case, root = sys.argv[1], sys.argv[2]
pred_path = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(f'{root}/assets/ct', exist_ok=True); os.makedirs(f'{root}/图片/真实CT', exist_ok=True)

img = nib.load(f'{case}/ct.nii.gz'); assert nib.aff2axcodes(img.affine) == ('R', 'A', 'S')
ct = img.get_fdata(dtype=np.float32)            # 轴码 RAS：i→患者右，j→前，k→上
sp = [float(v) for v in img.header.get_zooms()]
names = sorted(os.path.basename(f)[:-7] for f in glob.glob(f'{case}/segmentations/*.nii.gz'))
lab = np.zeros(ct.shape, np.uint8)
for i, n in enumerate(names, 1):
    m = nib.load(f'{case}/segmentations/{n}.nii.gz').get_fdata(dtype=np.float32) > 0.5
    lab[m & (lab == 0)] = i

# TotalSegmentator 类名 -> CADS 结构名（同义时）与中文名、教学系统
def ts_info(n):
    side = {'left': ('L', '左'), 'right': ('R', '右')}
    p = n.split('_')
    sd = next((side[s] for s in p if s in side), None)
    base = '_'.join(s for s in p if s not in side)
    T = {  # base: (CADS name template or None, 中文, system)
     'adrenal_gland': ('Adrenal gland {S}', '肾上腺', 'glandular'), 'aorta': ('Aorta', '主动脉', 'cardiovascular'),
     'atrial_appendage': (None, '心耳', 'cardiovascular'), 'autochthon': ('Deep muscle of back {S}', '背深肌（竖脊肌群）', 'muscular'),
     'brachiocephalic_trunk': (None, '头臂干', 'cardiovascular'), 'brachiocephalic_vein': (None, '头臂静脉', 'cardiovascular'),
     'brain': ('Brain', '脑', 'nervous'), 'clavicula': ('Clavicle {S}', '锁骨', 'skeletal'), 'colon': ('Colon', '结肠', 'digestive'),
     'common_carotid_artery': (None, '颈总动脉', 'cardiovascular'), 'costal_cartilages': (None, '肋软骨', 'skeletal'),
     'duodenum': ('Duodenum', '十二指肠', 'digestive'), 'esophagus': ('Esophagus', '食管', 'digestive'), 'femur': ('Femur {S}', '股骨', 'skeletal'),
     'gallbladder': ('Gallbladder', '胆囊', 'digestive'), 'gluteus_maximus': ('Gluteus maximus muscle {S}', '臀大肌', 'muscular'),
     'gluteus_medius': ('Gluteus medius muscle {S}', '臀中肌', 'muscular'), 'gluteus_minimus': ('Gluteus minimus muscle {S}', '臀小肌', 'muscular'),
     'heart': ('Heart', '心脏', 'cardiovascular'), 'hip': ('Hip {S}', '髋骨', 'skeletal'), 'humerus': ('Humerus {S}', '肱骨', 'skeletal'),
     'iliac_artery': ('Common iliac artery {S}', '髂动脉', 'cardiovascular'), 'iliac_vena': ('Common iliac vein {S}', '髂静脉', 'cardiovascular'),
     'iliopsoas': ('Iliopsoas muscle {S}', '髂腰肌', 'muscular'), 'inferior_vena_cava': ('Inferior vena cava', '下腔静脉', 'cardiovascular'),
     'kidney_cyst': (None, '肾囊肿', 'urinary'), 'kidney': ('Kidney {S}', '肾', 'urinary'), 'liver': ('Liver', '肝', 'digestive'),
     'lung_lower_lobe': ('Lower lobe of lung {S}', '肺下叶', 'respiratory'), 'lung_middle_lobe': ('Middle lobe of lung {S}', '肺中叶', 'respiratory'),
     'lung_upper_lobe': ('Upper lobe of lung {S}', '肺上叶', 'respiratory'), 'pancreas': ('Pancreas', '胰腺', 'digestive'),
     'portal_vein_and_splenic_vein': ('Portal vein and splenic vein', '门静脉与脾静脉', 'cardiovascular'), 'prostate': ('Prostate', '前列腺', 'reproductive'),
     'pulmonary_vein': (None, '肺静脉', 'cardiovascular'), 'sacrum': ('Sacrum', '骶骨', 'skeletal'), 'scapula': ('Scapula {S}', '肩胛骨', 'skeletal'),
     'skull': (None, '颅骨', 'skeletal'), 'small_bowel': ('Small intestine', '小肠', 'digestive'), 'spinal_cord': ('Spinal cord', '脊髓', 'nervous'),
     'spleen': ('Spleen', '脾', 'lymphatic'), 'sternum': ('Sternum', '胸骨', 'skeletal'), 'stomach': ('Stomach', '胃', 'digestive'),
     'subclavian_artery': (None, '锁骨下动脉', 'cardiovascular'), 'superior_vena_cava': (None, '上腔静脉', 'cardiovascular'),
     'thyroid_gland': ('Thyroid', '甲状腺', 'glandular'), 'trachea': ('Trachea', '气管', 'respiratory'), 'urinary_bladder': ('Urinary bladder', '膀胱', 'urinary'),
    }
    if base.startswith('rib'):
        k = p[-1]; return {'ts': n, 'cads': f'Rib-{k} {sd[0]}', 'zh': f'{sd[1]}第 {k} 肋', 'sys': 'skeletal'}
    if base.startswith('vertebrae'):
        v = p[1]; zh = {'C': '颈', 'T': '胸', 'L': '腰', 'S': '骶'}[v[0]] + v[1:] + ' 椎骨'
        return {'ts': n, 'cads': (None if v == 'S1' else f'Vertebra {v}'), 'zh': zh, 'sys': 'skeletal'}
    c, zh, s = T[base]
    return {'ts': n, 'cads': ((c.replace('{S}', sd[0]) if '{S}' in c else c) if c else None), 'zh': (sd[1] if sd else '') + zh, 'sys': s}
info = [ts_info(n) for n in names]

COL = {'skeletal': (233, 223, 196), 'muscular': (226, 87, 76), 'cardiovascular': (214, 40, 90), 'respiratory': (86, 180, 233),
       'digestive': (240, 170, 60), 'urinary': (240, 228, 66), 'reproductive': (204, 121, 167), 'glandular': (160, 120, 230),
       'nervous': (120, 220, 160), 'sensory': (0, 158, 115), 'lymphatic': (150, 90, 200), 'cavities': (120, 140, 160), 'other': (170, 170, 170)}
rng = np.random.default_rng(7)
lut = np.zeros((256, 3), np.float32)
for i, d in enumerate(info, 1):  # 同系统内轻微抖动颜色，便于区分相邻结构
    base = np.array(COL[d['sys']], np.float32); lut[i] = np.clip(base * rng.uniform(0.78, 1.12), 0, 255)
    d['rgb'] = [int(v) for v in lut[i]]

def win(a, lo, hi): return (np.clip((a - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
def axial(arr, z):  # 显示为放射学惯例：患者右侧在图像左侧，前方在上
    s = arr[:, :, z]                 # (x, y)
    return np.flipud(s.T)[:, ::-1]
# nibabel 轴码 RAS：体素 i 增大指向患者右侧、j 指向前方。s.T 的列 = i，再左右翻转 ⇒ 图像左侧 = 患者右侧（放射学惯例）；flipud 使前方在上。

def overlay(gray, labs, alpha=0.5, outline=True, only=None):
    rgb = np.stack([gray] * 3, -1).astype(np.float32)
    m = labs > 0
    if only is not None: m &= np.isin(labs, only)
    col = lut[labs]
    rgb[m] = rgb[m] * (1 - alpha) + col[m] * alpha
    if outline:
        e = np.zeros_like(m)
        e[1:, :] |= labs[1:, :] != labs[:-1, :]; e[:, 1:] |= labs[:, 1:] != labs[:, :-1]
        e &= m
        rgb[e] = col[e]
    return Image.fromarray(rgb.astype(np.uint8))

# 交互阅片器：每 3 层取 1 层
Z = ct.shape[2]; zs = list(range(1, Z, 3))
for k, z in enumerate(zs):
    a = axial(ct, z); l = axial(lab, z)
    Image.fromarray(win(a, -160, 240)).save(f'{root}/assets/ct/ax-{k:03d}-soft.webp', quality=82, method=6)
    Image.fromarray(win(a, -1024, 1400)).save(f'{root}/assets/ct/ax-{k:03d}-wide.webp', quality=90, method=6)  # 有损压缩，仅用于显示
    Image.fromarray(l).save(f'{root}/assets/ct/ax-{k:03d}-lab.png', optimize=True)

# 冠状位定位图（经脊柱中线的层面）
ycor = int(np.median(np.where(lab == names.index('vertebrae_L3') + 1)[1]))
cor = np.flipud(ct[:, ycor, :].T)[:, ::-1]   # 冠状位同样采用放射学惯例
Image.fromarray(win(cor, -160, 240)).save(f'{root}/assets/ct/cor-soft.webp', quality=85)
corl = np.flipud(lab[:, ycor, :].T)[:, ::-1]
overlay(win(cor, -160, 240), corl, 0.45).resize((ct.shape[0] * 2, Z * 2), Image.NEAREST).save(f'{root}/图片/真实CT/ct-coronal-ts-v1.0.webp', quality=90)

def zmid(n):
    zz = np.where((lab == names.index(n) + 1).any((0, 1)))[0]; return int((zz.min() + zz.max()) // 2), int(zz.min()), int(zz.max())
z_l3, l3lo, l3hi = zmid('vertebrae_L3')
z_t6, _, _ = zmid('vertebrae_T6')
z_hip = zmid('femur_left')[2] + 6   # 股骨头上方的髋臼层面附近
statics = {'ct-chest-t6-ts-v1.0': (z_t6, -1000, 400), 'ct-l3-ts-v1.0': (z_l3, -160, 240), 'ct-pelvis-ts-v1.0': (z_hip, -160, 240)}
for nm, (z, lo, hi) in statics.items():
    a = axial(ct, z); l = axial(lab, z)
    overlay(win(a, lo, hi), l, 0.45).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST).save(f'{root}/图片/真实CT/{nm}.webp', quality=90)
    Image.fromarray(win(a, lo, hi)).resize((a.shape[1] * 3, a.shape[0] * 3), Image.BICUBIC).save(f'{root}/图片/真实CT/{nm}-raw.webp', quality=90)
# 胸部骨窗（看肋骨编号）
a = axial(ct, z_t6); l = axial(lab, z_t6)
ribs = [i for i, d in enumerate(info, 1) if d['ts'].startswith(('rib', 'vertebrae', 'sternum', 'scapula', 'costal'))]
overlay(win(a, -450, 1050), l, 0.55, only=ribs).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST).save(f'{root}/图片/真实CT/ct-chest-t6-bone-ts-v1.0.webp', quality=90)

# L3 层面：参考掩膜面积（演示用，不是完整骨骼肌面积 SMA）
px = sp[0] * sp[1] / 100.0  # cm²
l3 = lab[:, :, z_l3]; a3 = ct[:, :, z_l3]
meas = {}
for n in ['iliopsoas_left', 'iliopsoas_right', 'autochthon_left', 'autochthon_right', 'vertebrae_L3']:
    m = l3 == names.index(n) + 1
    meas[n] = {'area_cm2': round(float(m.sum() * px), 1), 'mean_hu': round(float(a3[m].mean()), 0) if m.any() else None}

case_json = {'case': 's0423', 'source': 'TotalSegmentator dataset v2.0.1, doi:10.5281/zenodo.10047292, CC BY 4.0',
             'meta': {'age': 65, 'sex': 'm', 'study_type': 'ct neck-thorax-abdomen-pelvis', 'pathology': 'trauma', 'pathology_location': 'thorax',
                      'ts_split': 'test', 'in_cads_test_split': True},
             'shape': list(ct.shape), 'spacing_mm': sp, 'step': 3, 'zs': zs, 'z_l3': z_l3, 'z_t6': z_t6, 'z_hip': z_hip, 'ycor': ycor,
             'labels': info, 'l3_reference_measurements': meas, 'colors': {k: list(v) for k, v in COL.items()}}

# 可选：CADS-model-research T554 在本病例的真实推理结果（只覆盖裁剪区域）
if pred_path:
    pj = json.load(open(pred_path.replace('.nii.gz', '.json')))
    pr = nib.load(pred_path).get_fdata(dtype=np.float32).astype(np.uint8)
    names554 = {int(v): k for k, v in pj['labels'].items()}
    X0, X1, Y0, Y1, z0, z1 = pj['crop_xyz']
    pairs = {1: 'humerus_left', 2: 'humerus_right', 3: 'scapula_left', 4: 'scapula_right', 5: 'clavicula_left', 6: 'clavicula_right',
             7: 'femur_left', 8: 'femur_right', 9: 'hip_left', 10: 'hip_right', 11: 'sacrum', 12: 'gluteus_maximus_left', 13: 'gluteus_maximus_right',
             14: 'gluteus_medius_left', 15: 'gluteus_medius_right', 16: 'gluteus_minimus_left', 17: 'gluteus_minimus_right',
             18: 'autochthon_left', 19: 'autochthon_right', 20: 'iliopsoas_left', 21: 'iliopsoas_right'}
    dice = {}
    for k, tsn in pairs.items():
        g = lab[X0:X1, Y0:Y1, z0:z1] == names.index(tsn) + 1; p = pr[X0:X1, Y0:Y1, z0:z1] == k
        if g.sum() == 0 and p.sum() == 0: continue
        dice[names554.get(k, str(k))] = {'ts': tsn, 'dice': round(float(2 * (g & p).sum() / max(g.sum() + p.sum(), 1)), 3),
                                          'ref_voxels': int(g.sum()), 'pred_voxels': int(p.sum()), 'idx': k}
    # 将 CADS 预测映射到与参考相同的配色（对应的 TS 类）
    plab = np.zeros_like(lab)
    for k, tsn in pairs.items(): plab[pr == k] = names.index(tsn) + 1
    z_iliac = z0 + 20  # 髂骨翼/骶骨上部层面（推理区间内）
    case_json['z_iliac'] = z_iliac
    zsel = [z for z in (z_l3, z_iliac) if z0 <= z < z1]
    for z in zsel:
        a = axial(ct, z)
        tag = 'l3' if z == z_l3 else 'pelvis'
        only = [names.index(t) + 1 for t in pairs.values()]
        overlay(win(a, -160, 240), axial(plab, z), 0.5).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST).save(f'{root}/图片/真实CT/ct-{tag}-cads554-v1.0.webp', quality=90)
        overlay(win(a, -160, 240), axial(lab, z), 0.5, only=only).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST).save(f'{root}/图片/真实CT/ct-{tag}-ts554-v1.0.webp', quality=90)
    pm = {}
    p3 = plab[:, :, z_l3]
    for n in ['iliopsoas_left', 'iliopsoas_right', 'autochthon_left', 'autochthon_right']:
        m = p3 == names.index(n) + 1
        pm[n] = {'area_cm2': round(float(m.sum() * px), 1), 'mean_hu': round(float(a3[m].mean()), 0) if m.any() else None}
    # 阅片器用的预测标签切片（仅推理区间）
    pz = []
    for k2, z in enumerate(zs):
        if z0 <= z < z1:
            Image.fromarray(axial(plab, z)).save(f'{root}/assets/ct/ax-{k2:03d}-cads.png', optimize=True); pz.append(k2)
    case_json['cads_inference'] = {'model': 'CADS-model-research (CC BY-NC-SA 4.0), task 554, release cads-model-research_v1.0.0',
                                   'crop_xyz': pj['crop_xyz'], 'patch': pj['patch'], 'seconds': round(pj['seconds']), 'dice_vs_reference': dice,
                                   'l3_pred_measurements': pm, 'viewer_slices': pz}
json.dump(case_json, open(f'{root}/assets/data/ctcasev1.0.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('slices', len(zs), 'z_l3', z_l3, 'z_t6', z_t6, 'z_hip', z_hip, json.dumps(meas, ensure_ascii=False))

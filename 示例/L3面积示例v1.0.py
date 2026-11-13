#!/usr/bin/env python3
"""L3 面积示例 v1.0 / L3 cross-sectional area example (teaching only)
在 L3 椎体中层计算若干掩膜的横截面积（cm²）与平均 HU。适用于 TotalSegmentator 格式（每个结构一个 .nii.gz），
也适用于把 CADS 输出按标签拆开后的掩膜。仅演示“掩膜 → 面积”的计算，不是经过验证的身体成分分析流程。
Usage:
  python3 示例/L3面积示例v1.0.py <ct.nii.gz> <vertebra_L3_mask.nii.gz> <mask1.nii.gz> [mask2.nii.gz ...]
Example (TotalSegmentator dataset v2.0.1, case s0423, CC BY 4.0):
  python3 示例/L3面积示例v1.0.py s0423/ct.nii.gz s0423/segmentations/vertebrae_L3.nii.gz \
      s0423/segmentations/iliopsoas_left.nii.gz s0423/segmentations/iliopsoas_right.nii.gz"""
import sys, os
import numpy as np, nibabel as nib
ct_p, l3_p, masks = sys.argv[1], sys.argv[2], sys.argv[3:]
ct = nib.load(ct_p); a = ct.get_fdata(dtype=np.float32)
ax = nib.aff2axcodes(ct.affine); assert ax[2] in ('S', 'I'), f'third axis must be superior/inferior, got {ax}'
l3 = nib.load(l3_p).get_fdata(dtype=np.float32) > 0.5
zz = np.where(l3.any((0, 1)))[0]
if not len(zz): sys.exit('L3 mask is empty')
z = int((zz.min() + zz.max()) // 2)
sx, sy = [float(v) for v in ct.header.get_zooms()[:2]]
px = sx * sy / 100.0
print(f'L3 mid-slice z={z} (L3 spans z={zz.min()}–{zz.max()}), pixel {sx:.2f}×{sy:.2f} mm')
total = 0.0
for p in masks:
    m = nib.load(p).get_fdata(dtype=np.float32)[:, :, z] > 0.5
    area = m.sum() * px; total += area
    hu = a[:, :, z][m].mean() if m.any() else float('nan')
    print(f'{os.path.basename(p):40s} area {area:7.1f} cm²   mean HU {hu:7.1f}')
print(f'{"sum":40s} area {total:7.1f} cm²')
print('Teaching example only — not total skeletal muscle area and no HU thresholding applied.')

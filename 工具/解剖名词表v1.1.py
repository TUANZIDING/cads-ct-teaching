#!/usr/bin/env python3
"""解剖名词表 v1.1 / Anatomical term table for the 117 TotalSegmentator v2 classes
生成 验证/解剖名词对照表v1.1.csv：TotalSegmentator 类名 → 中文解剖学名词 / English / 拉丁（Terminologia Anatomica）/ 系统。
来源 / sources:
  - TotalSegmentator v2 类名：Wasserthal J et al. Radiol Artif Intell 2023;5:e230024, doi:10.1148/ryai.230024；
    github.com/wasserth/TotalSegmentator（resources/ 类名表），数据集 doi:10.5281/zenodo.10047292（CC BY 4.0）。
  - 中文：全国科学技术名词审定委员会《人体解剖学名词》（第二版，科学出版社，2014）所采用的规范名（术语在线 termonline.cn 可检索）。
  - 拉丁：FIPAT. Terminologia Anatomica, 2nd ed. 2019（TA2）；与 TA 1998 一致处不另注。
说明：名词由作者按上述规范整理；“备注”列写明 TotalSegmentator 掩膜的实际范围与规范名不完全对应之处。
Usage: python3 工具/解剖名词表v1.1.py [repo_root]"""
import csv, os, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
# base: (中文, English, Latin TA, system, 备注)
B = {
 'adrenal_gland': ('肾上腺', 'Adrenal gland', 'Glandula suprarenalis', 'endocrine', ''),
 'aorta': ('主动脉', 'Aorta', 'Aorta', 'cardiovascular', '掩膜含升主动脉、主动脉弓与降主动脉 / ascending, arch and descending'),
 'atrial_appendage': ('心耳', 'Atrial appendage (auricle)'.replace(' (auricle)', ''), 'Auricula atrii', 'cardiovascular', 'TotalSegmentator 只有左心耳 / left only'),
 'autochthon': ('背深肌', 'Deep (autochthonous) back muscles', 'Musculi dorsi proprii', 'muscular', '以竖脊肌、横突棘肌为主的固有背肌群 / mainly erector spinae + transversospinales'),
 'brachiocephalic_trunk': ('头臂干', 'Brachiocephalic trunk', 'Truncus brachiocephalicus', 'cardiovascular', ''),
 'brachiocephalic_vein': ('头臂静脉', 'Brachiocephalic vein', 'Vena brachiocephalica', 'cardiovascular', ''),
 'brain': ('脑', 'Brain', 'Encephalon', 'nervous', ''),
 'clavicula': ('锁骨', 'Clavicle', 'Clavicula', 'skeletal', ''),
 'colon': ('结肠', 'Colon', 'Colon', 'digestive', ''),
 'common_carotid_artery': ('颈总动脉', 'Common carotid artery', 'Arteria carotis communis', 'cardiovascular', ''),
 'costal_cartilages': ('肋软骨', 'Costal cartilages', 'Cartilagines costales', 'skeletal', '双侧合为一类 / both sides one class'),
 'duodenum': ('十二指肠', 'Duodenum', 'Duodenum', 'digestive', ''),
 'esophagus': ('食管', 'Oesophagus', 'Oesophagus', 'digestive', ''),
 'femur': ('股骨', 'Femur', 'Femur', 'skeletal', '视野内为股骨近端 / proximal part in field'),
 'gallbladder': ('胆囊', 'Gallbladder', 'Vesica biliaris', 'digestive', 'TA1998 作 Vesica fellea'),
 'gluteus_maximus': ('臀大肌', 'Gluteus maximus', 'Musculus gluteus maximus', 'muscular', ''),
 'gluteus_medius': ('臀中肌', 'Gluteus medius', 'Musculus gluteus medius', 'muscular', ''),
 'gluteus_minimus': ('臀小肌', 'Gluteus minimus', 'Musculus gluteus minimus', 'muscular', ''),
 'heart': ('心', 'Heart', 'Cor', 'cardiovascular', '“心脏”为通用说法，规范名为“心” / standard Chinese term 心'),
 'hip': ('髋骨', 'Hip bone', 'Os coxae', 'skeletal', '髂骨、坐骨、耻骨合称 / ilium + ischium + pubis'),
 'humerus': ('肱骨', 'Humerus', 'Humerus', 'skeletal', ''),
 'iliac_artery': ('髂总动脉', 'Common iliac artery', 'Arteria iliaca communis', 'cardiovascular', '掩膜可向下延续到髂外动脉起始段 / may extend into external iliac'),
 'iliac_vena': ('髂总静脉', 'Common iliac vein', 'Vena iliaca communis', 'cardiovascular', '掩膜可向下延续到髂外静脉起始段 / may extend into external iliac'),
 'iliopsoas': ('髂腰肌', 'Iliopsoas', 'Musculus iliopsoas', 'muscular', '腰大肌 + 髂肌 / psoas major + iliacus'),
 'inferior_vena_cava': ('下腔静脉', 'Inferior vena cava', 'Vena cava inferior', 'cardiovascular', ''),
 'kidney_cyst': ('肾囊肿', 'Kidney cyst', '—', 'other', '病变而非解剖结构，无 TA 名 / lesion, no TA term'),
 'kidney': ('肾', 'Kidney', 'Ren', 'urinary', ''),
 'liver': ('肝', 'Liver', 'Hepar', 'digestive', ''),
 'lung_lower_lobe': ('肺下叶', 'Lower lobe of lung', 'Lobus inferior pulmonis', 'respiratory', ''),
 'lung_middle_lobe': ('右肺中叶', 'Middle lobe of right lung', 'Lobus medius pulmonis dextri', 'respiratory', ''),
 'lung_upper_lobe': ('肺上叶', 'Upper lobe of lung', 'Lobus superior pulmonis', 'respiratory', ''),
 'pancreas': ('胰', 'Pancreas', 'Pancreas', 'digestive', '“胰腺”为通用说法 / 胰 is the standard term'),
 'portal_vein_and_splenic_vein': ('肝门静脉和脾静脉', 'Portal vein and splenic vein', 'Vena portae hepatis; Vena splenica', 'cardiovascular', '两条静脉合为一类 / one class'),
 'prostate': ('前列腺', 'Prostate', 'Prostata', 'reproductive', ''),
 'pulmonary_vein': ('肺静脉', 'Pulmonary veins', 'Venae pulmonales', 'cardiovascular', ''),
 'sacrum': ('骶骨', 'Sacrum', 'Os sacrum', 'skeletal', ''),
 'scapula': ('肩胛骨', 'Scapula', 'Scapula', 'skeletal', ''),
 'skull': ('颅骨', 'Skull', 'Cranium', 'skeletal', '本例仅视野上缘少量 / only a sliver in field'),
 'small_bowel': ('小肠', 'Small intestine', 'Intestinum tenue', 'digestive', '空肠 + 回肠 / jejunum + ileum'),
 'spinal_cord': ('脊髓', 'Spinal cord', 'Medulla spinalis', 'nervous', ''),
 'spleen': ('脾', 'Spleen', 'Splen', 'lymphatic', ''),
 'sternum': ('胸骨', 'Sternum', 'Sternum', 'skeletal', ''),
 'stomach': ('胃', 'Stomach', 'Gaster', 'digestive', ''),
 'subclavian_artery': ('锁骨下动脉', 'Subclavian artery', 'Arteria subclavia', 'cardiovascular', ''),
 'superior_vena_cava': ('上腔静脉', 'Superior vena cava', 'Vena cava superior', 'cardiovascular', ''),
 'thyroid_gland': ('甲状腺', 'Thyroid gland', 'Glandula thyroidea', 'endocrine', ''),
 'trachea': ('气管', 'Trachea', 'Trachea', 'respiratory', ''),
 'urinary_bladder': ('膀胱', 'Urinary bladder', 'Vesica urinaria', 'urinary', ''),
}
SIDE = {'left': ('左', 'left', 'sinister/sinistra', 'L'), 'right': ('右', 'right', 'dexter/dextra', 'R')}
VERT = {'C': ('颈椎', 'cervical vertebra', 'Vertebra cervicalis'), 'T': ('胸椎', 'thoracic vertebra', 'Vertebra thoracica'),
        'L': ('腰椎', 'lumbar vertebra', 'Vertebra lumbalis'), 'S': ('骶椎', 'sacral vertebra', 'Vertebra sacralis')}
CN = '一二三四五六七八九十'
def cnum(k): return CN[k - 1] if k <= 10 else '十' + CN[k - 11]

def term(n):
    p = n.split('_'); sd = next((s for s in p if s in SIDE), None)
    if p[0] == 'rib':
        k = int(p[2]); s = SIDE[p[1]]
        return dict(ts=n, zh=f'{s[0]}第{k}肋', en=f'{s[1].capitalize()} rib {k}', la=f'Costa {ROMAN[k]} {s[2].split("/")[1]}', sys='skeletal', side=s[3], note='')
    if p[0] == 'vertebrae':
        r, k = p[1][0], int(p[1][1:]); z, e, l = VERT[r]
        zh = {('C', 1): '寰椎', ('C', 2): '枢椎', ('C', 7): '第7颈椎（隆椎）'}.get((r, k), f'第{k}{z}')
        la = {('C', 1): 'Atlas', ('C', 2): 'Axis', ('C', 7): 'Vertebra prominens (C VII)'}.get((r, k), f'{l} {ROMAN[k]}')
        note = 'S1 是骶骨的一部分，TotalSegmentator 单列 / S1 is part of the sacrum, separate class in TotalSegmentator' if r == 'S' else ''
        return dict(ts=n, zh=zh, en=f'{p[1]} {e}', la=la, sys='skeletal', side='', note=note)
    base = '_'.join(s for s in p if s not in SIDE); zh, en, la, sy, note = B[base]
    if sd and base != 'lung_middle_lobe':
        s = SIDE[sd]; zh = s[0] + zh; en = f'{en} ({s[1]})'
        if la != '—':
            la = la.replace('Auricula atrii', 'Auricula') + ' ' + LAT_SIDE[GENDER.get(base, 'f')][sd]
    return dict(ts=n, zh=zh, en=en, la=la, sys=sy, side=(SIDE[sd][3] if sd else ''), note=note)

# 拉丁形容词性别一致 / Latin adjective agreement for side
LAT_SIDE = {'m': {'left': 'sinister', 'right': 'dexter'}, 'f': {'left': 'sinistra', 'right': 'dextra'},
            'n': {'left': 'sinistrum', 'right': 'dextrum'}, 'mpl': {'left': 'sinistri', 'right': 'dextri'}}
GENDER = {'autochthon': 'mpl', 'femur': 'n', 'hip': 'n', 'humerus': 'm', 'kidney': 'm', 'lung_lower_lobe': 'mpl', 'lung_upper_lobe': 'mpl'  # 肺叶：pulmonis sinistri/dextri（属格）
         ,
          'gluteus_maximus': 'm', 'gluteus_medius': 'm', 'gluteus_minimus': 'm', 'iliopsoas': 'm'}

TS117 = ([f'{b}_{s}' for b in ['adrenal_gland', 'autochthon', 'brachiocephalic_vein', 'clavicula', 'common_carotid_artery', 'femur', 'gluteus_maximus',
          'gluteus_medius', 'gluteus_minimus', 'hip', 'humerus', 'iliac_artery', 'iliac_vena', 'iliopsoas', 'kidney_cyst', 'kidney', 'lung_lower_lobe',
          'lung_upper_lobe', 'scapula', 'subclavian_artery'] for s in ('left', 'right')]
         + ['lung_middle_lobe_right', 'atrial_appendage_left', 'aorta', 'brachiocephalic_trunk', 'brain', 'colon', 'costal_cartilages', 'duodenum', 'esophagus',
            'gallbladder', 'heart', 'inferior_vena_cava', 'liver', 'pancreas', 'portal_vein_and_splenic_vein', 'prostate', 'pulmonary_vein', 'sacrum', 'skull',
            'small_bowel', 'spinal_cord', 'spleen', 'sternum', 'stomach', 'superior_vena_cava', 'thyroid_gland', 'trachea', 'urinary_bladder']
         + [f'rib_{s}_{k}' for s in ('left', 'right') for k in range(1, 13)]
         + [f'vertebrae_C{k}' for k in range(1, 8)] + [f'vertebrae_T{k}' for k in range(1, 13)] + [f'vertebrae_L{k}' for k in range(1, 6)] + ['vertebrae_S1'])

if __name__ == '__main__':
    assert len(TS117) == 117 and len(set(TS117)) == 117, len(TS117)
    rows = [term(n) for n in sorted(TS117)]
    with open(f'{ROOT}/验证/解剖名词对照表v1.1.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['totalsegmentator_class', '中文名', 'English', 'Latin (TA2)', 'system', 'side', '备注 note'])
        for r in rows: w.writerow([r['ts'], r['zh'], r['en'], r['la'], r['sys'], r['side'], r['note']])
    print(len(rows), 'rows')

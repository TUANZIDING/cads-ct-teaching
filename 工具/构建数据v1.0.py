#!/usr/bin/env python3
"""构建数据 v1.0 / Build label data
从 CADS 官方仓库 labelmap.md（Apache-2.0）、论文 Table 2（CC BY 4.0）与补充材料 Suppl. Table 1（CC BY 4.0）
生成 assets/data/labelsv1.0.json：167 个结构的中英文名、模型组、SNOMED CT 编码、上级系统、出现例数与中位体积。
Usage: python3 工具/构建数据v1.0.py <labelmap.md> <paper-text.txt> <supp-text.txt> <out.json>
文本由 `pdftotext -layout` 从论文 AIP PDF 与 Supplementary Information PDF 提取。"""
import re, json, sys

labelmap, paper_txt, supp_txt, out = sys.argv[1:5]

GROUPS = {  # 官方 README「Target Structures in Each Task」与 3D Slicer 插件的任务名
 551: ('腹部主要器官、肺叶与腹部大血管', 'Major abdominal organs, lung lobes and abdominal vessels', 'Core organs'),
 552: ('全脊柱椎骨 C1–L5', 'Individual vertebrae C1–L5', 'Spine complete'),
 553: ('胸腹器官、心腔、脑、盆腔血管与面部', 'Thoracic/abdominal organs, heart chambers, brain, pelvic vessels, face', 'Heart & vessels'),
 554: ('四肢带骨、骶骨与躯干大肌群', 'Appendicular bones, sacrum and large trunk muscles', 'Trunk muscles'),
 555: ('左右第 1–12 肋', 'Ribs 1–12, left and right', 'Ribs complete'),
 556: ('放疗相关结构', 'Miscellaneous structures for radiation therapy', 'RT risk organs'),
 557: ('脑与头部组织', 'Brain and head tissues', 'Brain tissues'),
 558: ('头颈部结构（放疗危及器官）', 'Head and neck structures', 'Head-neck organs'),
 559: ('组织类型与体腔', 'General tissue types and body cavities', 'Body regions'),
}

ZH = {
 'Spleen':'脾','Kidney R':'右肾','Kidney L':'左肾','Gallbladder':'胆囊','Liver':'肝','Stomach':'胃','Aorta':'主动脉',
 'Inferior vena cava':'下腔静脉','Portal vein and splenic vein':'门静脉与脾静脉','Pancreas':'胰腺','Adrenal gland R':'右肾上腺',
 'Adrenal gland L':'左肾上腺','Upper lobe of lung L':'左肺上叶','Lower lobe of lung L':'左肺下叶','Upper lobe of lung R':'右肺上叶',
 'Middle lobe of lung R':'右肺中叶','Lower lobe of lung R':'右肺下叶','Esophagus':'食管','Trachea':'气管','Myocardium':'心肌',
 'Heart atrium L':'左心房','Heart ventricle L':'左心室','Heart atrium R':'右心房','Heart ventricle R':'右心室','Pulmonary artery':'肺动脉',
 'Brain':'脑','Common iliac artery L':'左髂总动脉','Common iliac artery R':'右髂总动脉','Common iliac vein L':'左髂总静脉',
 'Common iliac vein R':'右髂总静脉','Small intestine':'小肠（空肠+回肠）','Duodenum':'十二指肠','Colon':'结肠','Urinary bladder':'膀胱','Face':'面部（去标识区域）',
 'Humerus L':'左肱骨','Humerus R':'右肱骨','Scapula L':'左肩胛骨','Scapula R':'右肩胛骨','Clavicle L':'左锁骨','Clavicle R':'右锁骨',
 'Femur L':'左股骨','Femur R':'右股骨','Hip L':'左髋骨','Hip R':'右髋骨','Sacrum':'骶骨',
 'Gluteus maximus muscle L':'左臀大肌','Gluteus maximus muscle R':'右臀大肌','Gluteus medius muscle L':'左臀中肌','Gluteus medius muscle R':'右臀中肌',
 'Gluteus minimus muscle L':'左臀小肌','Gluteus minimus muscle R':'右臀小肌','Deep muscle of back L':'左背深肌（竖脊肌群）','Deep muscle of back R':'右背深肌（竖脊肌群）',
 'Iliopsoas muscle L':'左髂腰肌','Iliopsoas muscle R':'右髂腰肌','Spinal canal':'椎管','Larynx':'喉','Heart':'心脏（含心包囊）','Bowel space':'肠道空间',
 'Sigmoid colon':'乙状结肠','Rectum':'直肠','Prostate':'前列腺','Seminal vesicle':'精囊','Mammary gland L':'左乳腺','Mammary gland R':'右乳腺','Sternum':'胸骨',
 'Psoas major muscle R':'右腰大肌','Psoas major muscle L':'左腰大肌','Rectus abdominis muscle R':'右腹直肌','Rectus abdominis muscle L':'左腹直肌',
 'White matter':'脑白质','Gray matter':'脑灰质','Cerebrospinal fluid':'脑脊液','Scalp':'头皮','Eyeballs':'眼球','Compact bone':'密质骨（颅骨）',
 'Spongy bone':'松质骨（颅骨）','Vascular structure of head':'头部血管结构','Rectus eye muscle structure':'眼直肌',
 'Carotid artery L':'左颈动脉','Carotid artery R':'右颈动脉','Arytenoid cartilage':'杓状软骨','Mandible':'下颌骨','Brain stem':'脑干','Buccal mucosa':'颊黏膜',
 'Oral cavity':'口腔','Cochlea L':'左耳蜗','Cochlea R':'右耳蜗','Cricopharyngeus':'环咽肌（环咽入口）','Cervical esophagus':'颈段食管',
 'Anterior eyeball segment L':'左眼前节','Anterior eyeball segment R':'右眼前节','Posterior eyeball segment L':'左眼后节','Posterior eyeball segment R':'右眼后节',
 'Lacrimal gland L':'左泪腺','Lacrimal gland R':'右泪腺','Submandibular gland L':'左下颌下腺','Submandibular gland R':'右下颌下腺','Thyroid':'甲状腺',
 'Glottis':'声门区','Supraglottis':'声门上区','Lip':'唇','Optic chiasm':'视交叉','Optic nerve L':'左视神经','Optic nerve R':'右视神经',
 'Parotid gland L':'左腮腺','Parotid gland R':'右腮腺','Pituitary gland':'垂体','Subcutaneous tissue':'皮下组织','Muscle':'肌肉（全身肌肉软组织）',
 'Abdominopelvic cavity':'腹盆腔','Thoracic cavity':'胸腔','Bone structure':'骨骼（整体）','Gland structure':'腺体（合并类）','Pericardium':'心包',
 'Breast implant':'乳房假体','Mediastinum':'纵隔','Spinal cord':'脊髓',
}
def zh_name(en):
    m = re.match(r'Vertebra ([CTL])(\d+)', en)
    if m: return {'C':'颈','T':'胸','L':'腰'}[m.group(1)] + m.group(2) + ' 椎骨'
    m = re.match(r'Rib-(\d+) ([LR])', en)
    if m: return ('左' if m.group(2)=='L' else '右') + f'第 {m.group(1)} 肋'
    return ZH[en]

# 教学用系统分组（作者解读，非论文分组）/ teaching grouping (author's interpretation)
def teach_system(en, g):
    e = en.lower()
    if g in (552, 555) or any(k in e for k in ['humerus','scapula','clavicle','femur','hip ','sacrum','sternum','mandible','compact bone','spongy bone','bone structure']) or e in ('hip l','hip r'):
        return 'skeletal'
    if any(k in e for k in ['muscle','gluteus','iliopsoas','psoas','rectus abdominis','cricopharyngeus']): return 'muscular'
    if any(k in e for k in ['aorta','vena cava','portal','myocardium','atrium','ventricle','pulmonary artery','iliac','carotid','vascular','heart','pericardium']): return 'cardiovascular'
    if any(k in e for k in ['lung','trachea','larynx','glottis','arytenoid']): return 'respiratory'
    if any(k in e for k in ['liver','stomach','pancreas','gallbladder','esophagus','intestine','duodenum','colon','rectum','bowel','oral cavity','lip','buccal']): return 'digestive'
    if any(k in e for k in ['kidney','bladder']): return 'urinary'
    if any(k in e for k in ['prostate','seminal','mammary','breast']): return 'reproductive'
    if any(k in e for k in ['thyroid','adrenal','pituitary','parotid','submandibular','lacrimal','gland structure']): return 'glandular'
    if any(k in e for k in ['brain','matter','cerebrospinal','spinal','optic']): return 'nervous'
    if any(k in e for k in ['eye','cochlea']): return 'sensory'
    if 'spleen' in e: return 'lymphatic'
    if any(k in e for k in ['cavity','mediastinum','subcutaneous','scalp','face']): return 'cavities'
    return 'other'

# 1) labelmap（官方仓库）
lm = open(labelmap, encoding='utf-8').read()
labels = []
for mid, body in re.findall(r'Model (\d+)</strong></summary>(.*?)</details>', lm, re.S):
    for idx, name in re.findall(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|', body):
        if idx != '0': labels.append({'group': int(mid), 'index': int(idx), 'en': name.strip()})
assert len(labels) == 167, len(labels)

# 2) Suppl. Table 1：SNOMED CT、上级系统、模型组（逐行对齐，组号核对）
L = open(supp_txt, encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(L) if l.startswith('Supplementary Table 1: CADS label-space'))
end = next(i for i, l in enumerate(L) if 'System abbreviations:' in l)
rows = []
for i in range(start, end):
    l = L[i]
    m = re.search(r'\s(\d{6,10})(?: \||\s)', l); g = re.search(r'\s(55[1-9])\s', l)
    if m and g: rows.append((i, l, m.group(1), int(g.group(1))))
assert len(rows) == 167, len(rows)
SYS = ['LYM','IMM','UR','DIG','CV','RESP','MSK','ENDO','NS','REP','HNSS','CAV','MSOPS','MSOLS','MSOTS','MSOCS']
for lab, (i, l, code, g) in zip(labels, rows):
    assert lab['group'] == g, (lab, l)
    lab['snomed'] = code
    toks = re.findall(r'\b(' + '|'.join(SYS) + r')\b', l)
    nxt = L[i+1] if i+1 < len(L) else ''
    if l.rstrip().endswith(',') or re.search(r'\b(LYM|MSK|MSOPS),\s', l):
        toks += re.findall(r'\b(IMM|MSOLS|MSOTS|MSOCS|MSK)\b', nxt)
    lat = re.search(r'([LR]):(\d+)', nxt) or re.search(r'([LR]):(\d+)', l)
    if lat: lab['snomed_lat'] = f'{lat.group(1)}:{lat.group(2)}'
    lab['systems'] = list(dict.fromkeys(toks))

# 3) Table 2：出现例数、中位体素数（1.5 mm 各向同性，1 体素 = 3.375 mm³）
t = open(paper_txt, encoding='utf-8').read()
s = t[t.index('Table 2 | Summary statistics'):t.index('Cases, number of the 22,022')]
cells = re.findall(r'([A-Za-z][A-Za-z ]*?(?: [LR])?|Vertebra [CTL]\d+|Rib \d+ [LR])\s+([\d,]+)\s+([\d,]+)', s)
assert len(cells) == 167, len(cells)
for lab, (nm, cases, med) in zip(labels, cells):
    lab['table2_name'] = nm
    lab['cases'] = int(cases.replace(',', ''))
    lab['median_voxels'] = int(med.replace(',', ''))
    lab['median_ml'] = round(lab['median_voxels'] * 3.375 / 1000, 1)  # 派生值 derived
    lab['zh'] = zh_name(lab['en'])
    lab['teach'] = teach_system(lab['en'], lab['group'])
    lab['id'] = f"{lab['group']}-{lab['index']}"

json.dump({'version': '1.0.0',
           'sources': {
             'labelmap': 'https://github.com/murong-xu/CADS/blob/main/resources/info/labelmap.md (Apache-2.0)',
             'table2': 'Xu M et al. Nat Commun 2026, Table 2, doi:10.1038/s41467-026-78732-1 (CC BY 4.0)',
             'suppl_table1': 'Xu M et al. Nat Commun 2026, Supplementary Information, Suppl. Table 1 (CC BY 4.0)'},
           'notes': {'median_ml': '作者由 median_voxels × 3.375 mm³ 换算，非论文直接报告 / derived by the author',
                     'teach': '教学用系统分组，为作者解读，不是论文的分组 / teaching grouping, author interpretation',
                     'muscle_median_voxels': '论文 Table 2 印为 “16,09,604”，按 1,609,604 解析 / printed as 16,09,604 in Table 2'},
           'groups': {str(k): {'zh': v[0], 'en': v[1], 'slicer': v[2]} for k, v in GROUPS.items()},
           'labels': labels}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('labels', len(labels), '->', out)

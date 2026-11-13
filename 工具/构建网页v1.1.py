#!/usr/bin/env python3
"""构建网页 v1.1 / Build index.html（v1.1：页首为真实 CT 交互多平面解剖阅片器，基于本地打包的 NiiVue）
把双语正文、论文原图、真实 CT 数据（assets/data/*.json）组装成单页静态网页 index.html。
所有数字均来自 Xu et al., Nat Commun 2026（doi:10.1038/s41467-026-78732-1，CC BY 4.0）正文/图表/补充材料，
或官方仓库 README；作者解读与作者计算分别用「教学解读」「作者计算」标签标出。
Usage: python3 工具/构建阅片数据v1.1.py ... 之后运行 python3 工具/构建网页v1.1.py [repo_root]"""
import json, sys, os, html

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = '1.1.0'; DATE = '2026-11-13'
DOI = 'https://doi.org/10.1038/s41467-026-78732-1'
LAB = json.load(open(f'{ROOT}/assets/data/labelsv1.0.json', encoding='utf-8'))
VW = json.load(open(f'{ROOT}/assets/viewer/structures-v1.1.json', encoding='utf-8'))
CASE = json.load(open(f'{ROOT}/assets/data/ctcasev1.0.json', encoding='utf-8'))
REFS = json.load(open(f'{ROOT}/验证/参考文献v1.0.json', encoding='utf-8'))
RIDX = {r['key']: i + 1 for i, r in enumerate(REFS)}

def T(zh, en, tag='span'):
    return f'<{tag} class="zh">{zh}</{tag}><{tag} class="en">{en}</{tag}>'
def R(*keys):  # 引用 [n]
    return '<sup>' + ','.join(f'<a href="#ref-{RIDX[k]}">[{RIDX[k]}]</a>' for k in keys) + '</sup>'
FACT = T('<span class="tag fact">论文事实</span>', '<span class="tag fact">FACT · paper</span>')
TEACH = T('<span class="tag teach">教学解读</span>', '<span class="tag teach">TEACHING</span>')
DER = T('<span class="tag derived">作者计算</span>', '<span class="tag derived">DERIVED</span>')
REAL = T('<span class="tag real">真实数据</span>', '<span class="tag real">REAL DATA</span>')

SYS = {
 'skeletal': ('骨骼系统', 'Skeletal', '#e9dfc4'), 'muscular': ('肌肉系统', 'Muscular', '#e2574c'),
 'cardiovascular': ('心血管系统', 'Cardiovascular', '#d6285a'), 'respiratory': ('呼吸系统', 'Respiratory', '#56b4e9'),
 'digestive': ('消化系统', 'Digestive', '#f0aa3c'), 'urinary': ('泌尿系统', 'Urinary', '#f0e442'),
 'reproductive': ('生殖系统与乳腺', 'Reproductive & breast', '#cc79a7'), 'glandular': ('腺体与内分泌', 'Glands & endocrine', '#a078e6'),
 'nervous': ('神经系统', 'Nervous', '#78dca0'), 'sensory': ('感觉器官', 'Sensory organs', '#009e73'),
 'lymphatic': ('淋巴与免疫', 'Lymphatic & immune', '#965ac8'), 'cavities': ('体腔与组织区域', 'Body cavities & tissue regions', '#788ca0'),
 'other': ('其他', 'Other', '#aaaaaa')}
# 面部、头皮归入“其他”
for l in LAB['labels']:
    if l['en'] in ('Face', 'Scalp'): l['teach'] = 'other'

def fig(file, n, zh, en, alt_zh, alt_en, extra_zh='', extra_en=''):
    att_en = (f'Reproduced from Xu, M. et al. Nat. Commun. (2026), Fig. {n}, <a href="{DOI}">doi:10.1038/s41467-026-78732-1</a>, '
              'licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Cropped from the Article-in-Press PDF page '
              '(original caption kept), resized and converted to WebP; no other changes.')
    att_zh = (f'转载自 Xu M 等，Nat Commun 2026，图 {n}，<a href="{DOI}">doi:10.1038/s41467-026-78732-1</a>，'
              '<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>。从 Article-in-Press PDF 页面裁出（保留原英文图注），缩放并转为 WebP，无其他改动。')
    return (f'<figure class="fig"><button type="button" data-full="图片/论文原图/{file}v1.0.webp" data-cap-zh="{html.escape(alt_zh)}" data-cap-en="{html.escape(alt_en)}">'
            f'<img src="图片/论文原图/{file}v1.0-sm.webp" loading="lazy" width="900" alt="{html.escape(alt_en)}"></button>'
            f'<figcaption class="figcap">{FACT}{T(zh, en)}{T(extra_zh, extra_en) if extra_zh else ""}'
            f'<span class="att">{T(att_zh, att_en)}</span></figcaption></figure>')

def ctfig(file, zh, en, alt):
    return (f'<figure class="fig ctfig"><button type="button" data-full="图片/真实CT/{file}.webp" data-cap-zh="{html.escape(alt)}" data-cap-en="{html.escape(alt)}">'
            f'<img src="图片/真实CT/{file}.webp" loading="lazy" width="816" alt="{html.escape(alt)}"></button>'
            f'<figcaption class="figcap">{REAL}{T(zh, en)}<span class="att">{T(CT_ATT_ZH, CT_ATT_EN)}</span></figcaption></figure>')
CT_ATT_EN = ('Rendered by the author in code from case s0423 of the TotalSegmentator dataset v2.0.1 (Wasserthal et al., '
             '<a href="https://doi.org/10.5281/zenodo.10047292">doi:10.5281/zenodo.10047292</a>, CC BY 4.0). Overlay = the dataset\'s own reference masks '
             '(not CADS output) unless stated. Image left = patient right.')
CT_ATT_ZH = ('作者用代码从 TotalSegmentator 数据集 v2.0.1 病例 s0423 渲染（Wasserthal 等，'
             '<a href="https://doi.org/10.5281/zenodo.10047292">doi:10.5281/zenodo.10047292</a>，CC BY 4.0）。除特别注明外，彩色叠加为该数据集自带的参考掩膜，'
             '不是 CADS 的输出。图像左侧 = 患者右侧。')

inf = CASE.get('cads_inference')
m = CASE['l3_reference_measurements']
psoas_ref = round(m['iliopsoas_left']['area_cm2'] + m['iliopsoas_right']['area_cm2'], 1)
back_ref = round(m['autochthon_left']['area_cm2'] + m['autochthon_right']['area_cm2'], 1)

# ---------------- sections ----------------
S = []
nav = [('viewer', '阅片器', 'Viewer'), ('why', '问题', 'Problem'), ('dataset', '数据集', 'Dataset'), ('pipeline', '流程', 'Pipeline'), ('labels', '167 结构', '167 labels'),
       ('models', '模型', 'Models'), ('eval', '评估', 'Evaluation'), ('realworld', '真实世界', 'Real world'), ('lab', 'CADS 推理', 'CADS run'),
       ('cases', '临床教学', 'Clinical cases'), ('tutorial', '动手', 'Hands-on'), ('quiz', '测验', 'Quiz'), ('limits', '局限', 'Limits'),
       ('refs', '文献', 'References'), ('license', '许可', 'License')]

SZ = VW['sizes_bytes']; PAY = round(sum(SZ.values()) / 1e6, 1); NSTR = len(VW['structures']); DIMS = '×'.join(str(v) for v in VW['shape'])
hero = f'''
<header class="hero compact" id="top"><div class="wrap">
<div class="kicker">{T('医学影像 AI · 教学模块 v' + VERSION, 'Medical imaging AI · teaching module v' + VERSION)}</div>
<h1>{T('真实全身 CT · 交互解剖阅片', 'Real whole-body CT · interactive anatomy viewer')}
<small>{T('横断面 / 冠状面 / 矢状面 / 3D 联动 · ' + str(NSTR) + ' 个彩色标注结构 · 中文 / English / Latin · 附 CADS 全身分割论文课件', 'Axial / coronal / sagittal / 3D, linked · ' + str(NSTR) + ' colour-coded structures · 中文 / English / Latin · with the CADS whole-body segmentation course')}</small></h1>
<p class="lead">{T('在任一切面上按住拖动，另外两个切面与 3D 同步换层；鼠标悬停（手机上点按）即显示该处结构的中文名、英文名、拉丁名与 CT 值。数据是一例真实的开放许可创伤 CT 及其逐体素参考标注，可与 CADS 模型的真实推理结果切换对照。',
 'Press and drag on any plane and the other two planes and the 3D view follow; hover (tap on phones) to see the structure\'s Chinese, English and Latin name and its HU. The data are one real, openly licensed trauma CT with voxel-wise reference labels, switchable to a real CADS model run for comparison.')}</p>
</div></header>
<section id="viewer" class="vw-sec"><div class="wrap vw-wrap">
<div id="vw" class="vw" data-base="assets/viewer/" data-src="ref">
<div class="vw-top">
 <div class="vw-seg vw-plane" id="vwPlane" role="group" aria-label="plane"><button type="button" class="on vw-grid" data-p="grid">{T('四窗', '4-up')}</button><button type="button" data-p="ax">{T('横断面', 'Axial')}</button><button type="button" data-p="cor">{T('冠状面', 'Coronal')}</button><button type="button" data-p="sag">{T('矢状面', 'Sagittal')}</button><button type="button" data-p="r3d">3D</button></div>
 <div class="vw-seg" id="vwWin" role="group" aria-label="window"><button type="button" class="on" data-w="soft">{T('软组织窗', 'Soft tissue')}</button><button type="button" data-w="bone">{T('骨窗', 'Bone')}</button><button type="button" data-w="lung">{T('肺窗', 'Lung')}</button></div>
 <div class="vw-seg" id="vwSrc" role="group" aria-label="label source"><button type="button" class="on" data-src="ref">{T('参考标注', 'Reference labels')}</button><button type="button" data-src="cads">{T('CADS 实测推理', 'CADS inference')}</button></div>
 <div class="vw-seg vw-zoom"><button type="button" id="vwZoomOut" aria-label="zoom out">−</button><button type="button" id="vwZoomIn" aria-label="zoom in">＋</button><button type="button" id="vwReset">{T('复位', 'Reset')}</button></div>
</div>
<div class="vw-body">
 <div class="vw-stage">
  <canvas id="vwCanvas" aria-label="CT multiplanar viewer"></canvas><canvas id="vwTags" class="vw-tags" aria-hidden="true"></canvas>
  <div id="vwTip" class="vw-tip" role="status"></div>
  <div class="vw-load"><div class="vw-prog"><i id="vwBar"></i></div></div>
 </div>
 <aside class="vw-side">
  <div class="vw-card vw-readcard"><div class="vw-lbl">{T('十字线处结构', 'Structure at the crosshair')}</div><div id="vwRead" class="vw-read">—</div></div>
  <div class="vw-card vw-sliders">
   <label><span>{T('横断面', 'Axial')}</span><input type="range" id="vwSl-ax" min="0" max="{VW['shape'][2] - 1}" value="0"><em id="vwSlv-ax"></em></label>
   <label><span>{T('冠状面', 'Coronal')}</span><input type="range" id="vwSl-cor" min="0" max="{VW['shape'][1] - 1}" value="0"><em id="vwSlv-cor"></em></label>
   <label><span>{T('矢状面', 'Sagittal')}</span><input type="range" id="vwSl-sag" min="0" max="{VW['shape'][0] - 1}" value="0"><em id="vwSlv-sag"></em></label>
  </div>
  <div class="vw-card">
   <label class="vw-row"><span>{T('标注透明度', 'Label opacity')}</span><input type="range" id="vwAlpha" min="0" max="1" step="0.05" value="0.6"></label>
   <div class="vw-row"><div class="vw-seg sm" id="vwMode"><button type="button" class="on" data-m="fill">{T('填充', 'Fill')}</button><button type="button" data-m="outline">{T('轮廓', 'Outline')}</button></div>
   <button type="button" class="vw-tog" id="vwTagBtn" aria-pressed="false">{T('名称标签', 'Name tags')}</button></div>
   <button type="button" class="vw-tog wide" id="vwClearFocus" hidden>{T('取消高亮，显示全部', 'Clear highlight, show all')}</button>
  </div>
  <div class="vw-card vw-legcard"><div class="vw-lbl">{T('结构图例', 'Legend')} · <b id="vwCount">{NSTR}</b> · {T('点名称跳转', 'click a name to jump')}</div>
   <input type="search" id="vwSearch" placeholder="搜索 / search: 肝, kidney, costa…" aria-label="search structures">
   <div id="vwLegend" class="vw-legend"></div></div>
 </aside>
</div>
<div class="vw-status" id="vwStatus">{T('阅片器进入视口后自动载入真实 CT 数据（约 ' + str(PAY) + ' MB，首次载入需要一些时间）。', 'The viewer loads the real CT data (about ' + str(PAY) + ' MB) when it scrolls into view; the first load takes a moment.')} <button type="button" class="vw-tog" id="vwStart">{T('立即载入', 'Load now')}</button></div>
<div class="vw-teach">
 <div class="vw-card"><div class="vw-lbl">{T('教学导览 · 一键跳到三个切面并高亮', 'Guided stops · jump all planes and highlight')}</div><div id="vwStops" class="vw-stops"></div><div id="vwStopText" class="vw-stoptext"></div></div>
 <div class="vw-card"><div class="vw-lbl">{T('找结构测验 · 标注隐藏，在切面上点击指定结构，按标签值判分', 'Find-the-structure quiz · labels hidden; click the named structure, scored by label value')}</div>
  <button type="button" class="btn primary" id="vwQuizBtn">{T('开始找结构测验', 'Start find-the-structure quiz')}</button>
  <div id="vwQuizBox" class="vw-quiz" hidden><div id="vwQuizQ"></div><div id="vwQuizFb" class="vw-fb"></div>
  <div class="vw-row"><span>{T('得分（首次即中）', 'Score (first try)')} <b id="vwQuizScore"></b></span><button type="button" class="vw-tog" id="vwQuizHint">{T('提示', 'Hint')}</button><button type="button" class="vw-tog" id="vwQuizNext">{T('下一题', 'Next')}</button></div></div></div>
</div>
<p class="vw-help">{T('操作：左键按住拖动 = 移动十字线并联动换层；滚轮 = 逐层；右键拖动 = 平移；＋/− = 缩放；在 3D 窗格拖动 = 旋转。手机：单指点按或拖动；用上方标签切换横断面 / 冠状面 / 矢状面 / 3D。方位：横断面和冠状面图像左侧 = 患者右侧（放射学惯例），图上 R/L/A/P/S/I 为方位标记。',
 'Controls: left-drag = move the crosshair and scroll the linked planes; wheel = step slices; right-drag = pan; ＋/− = zoom; drag in the 3D pane = rotate. Phones: tap or drag with one finger; use the tabs to switch axial / coronal / sagittal / 3D. Orientation: on axial and coronal images, image left = patient right (radiological convention); R/L/A/P/S/I markers are drawn on each pane.')}</p>
<p class="vw-src" id="vwSrcNote"></p>
<p class="vw-prov">{REAL}{T('数据来源：TotalSegmentator 数据集 v2.0.1 病例 s0423（65 岁男性，颈-胸-腹-盆 CT，元数据“创伤 / 胸部”；Wasserthal 等，<a href="https://doi.org/10.5281/zenodo.10047292">doi:10.5281/zenodo.10047292</a>，CC BY 4.0），CT 与参考掩膜经裁剪体外空气后以 1.5 mm 各向同性 NIfTI 提供（' + DIMS + ' 体素）。CADS 实测推理：CADS-model-research 任务 554 的真实输出，CC BY-NC-SA 4.0。名称：TotalSegmentator 类名 → 中文规范名（全国科学技术名词审定委员会《人体解剖学名词》）与拉丁名（Terminologia Anatomica 2），对照表见仓库 <code>验证/解剖名词对照表v1.1.csv</code>。阅片引擎：NiiVue 0.69.0（BSD-2-Clause，本地打包，不依赖 CDN）。仅供教学，不用于诊断。',
 'Data: TotalSegmentator dataset v2.0.1 case s0423 (65-year-old man, neck–chest–abdomen–pelvis CT, metadata "trauma / thorax"; Wasserthal et al., <a href="https://doi.org/10.5281/zenodo.10047292">doi:10.5281/zenodo.10047292</a>, CC BY 4.0); CT and reference masks cropped to the body and served as 1.5 mm isotropic NIfTI (' + DIMS + ' voxels). CADS inference: real output of CADS-model-research task 554, CC BY-NC-SA 4.0. Names: TotalSegmentator class → standard Chinese term (CNTERM 人体解剖学名词) and Latin (Terminologia Anatomica 2); mapping table in <code>验证/解剖名词对照表v1.1.csv</code>. Engine: NiiVue 0.69.0 (BSD-2-Clause, bundled locally, no CDN). Teaching only, not for diagnosis.')}</p>
</div>
<div class="hero-after">
<p class="cite">{T('课件来源论文：', 'Course source paper: ')}Xu M, Navarro F, Fritsak M, … Amiranashvili T, Menze B. <i>Nature Communications</i> (2026), open access, CC BY 4.0. <a href="{DOI}">doi:10.1038/s41467-026-78732-1</a>{R('xu2026')}</p>
<div class="stats">
 <div class="stat"><b>22,022</b><span>{T('个 CT 体数据（CADS 数据集）', 'CT volumes (CADS dataset)')}</span></div>
 <div class="stat"><b>167</b><span>{T('个解剖结构，头到膝', 'structures, head to knees')}</span></div>
 <div class="stat"><b>40/100+/16</b><span>{T('数据来源 · 影像中心 · 国家', 'sources · centres · countries')}</span></div>
 <div class="stat"><b>18+2,864</b><span>{T('公开测试集 + 真实世界肿瘤 CT', 'public test sets + real-world oncology CTs')}</span></div>
</div>
<div class="legend">{T('标签说明：', 'Legend: ')}{FACT}{T('论文或官方 README 直接写明', 'stated in the paper or official README')} {TEACH}{T('作者的教学解读', "author's teaching interpretation")} {DER}{T('作者由论文数字换算', 'computed by the author from paper numbers')} {REAL}{T('真实影像与真实掩膜', 'real images, real masks')}</div>
<p class="note red">{T('仅供教学与科研学习。CADS 是研究用软件，论文明确说专家审阅“不构成临床效用的正式证明”；本页任何内容都不能用于临床诊断或放疗计划。',
 'For teaching and research learning only. CADS is research software; the paper states that its expert review "does not constitute a formal demonstration of clinical utility". Nothing here is for clinical diagnosis or treatment planning.')}</p>
</div>
</div></section>'''


S.append(f'''<section id="why"><div class="wrap">
<h2><span class="no">01</span>{T('为什么需要 CADS', 'Why CADS')}</h2>
<p class="sub">{T('CT 全身分割能把影像变成结构化的解剖信息，用于放疗计划、异常检测与分诊、转移灶定位和身体成分分析。', 'Whole-body CT segmentation turns images into structured anatomy for radiotherapy planning, abnormality detection and triage, metastasis localisation and body-composition analysis.')}{R('xu2026', 'shi2022', 'weston2019')}</p>
<div class="grid3">
<div class="card"><h4>{FACT}{T('标注稀缺', 'Labels are scarce')}</h4><p>{T('本研究纳入的 40 个公开 CT 来源中，只有 21% 的扫描带解剖标注，而且大多只标了一两个结构。', 'Across the 40 public CT sources in this study, only 21% of scans had anatomical annotations, mostly of one or two structures.')}</p></div>
<div class="card"><h4>{FACT}{T('模型碎片化', 'Fragmented models')}</h4><p>{T('多数 AI 方法只针对单一器官，标签定义不一致，训练与评估方案各不相同。', 'Most AI methods are organ-specific, with inconsistent label definitions and heterogeneous training and evaluation protocols.')}</p></div>
<div class="card"><h4>{FACT}{T('现有资源的缺口', 'Gaps in existing resources')}</h4><p>{T('解剖覆盖有限、数据多样性不足、复杂结构存在系统性标注错误、依赖人工流程、外部验证不足、模型或数据不开放、缺少易用工具。', 'Limited anatomical coverage, insufficient diversity, systematic label errors in complex structures, human-dependent workflows, limited external validation, restricted availability and a lack of accessible tools.')}</p></div>
</div>
<p class="note cy">{TEACH}{T('一句话理解：CADS 的贡献不是新的网络结构，而是“数据为中心”——把碎片化的公开数据整理成统一、完整、可复用的标注，再用成熟的 nnU-Net 训练。论文原话：“The contribution is not a new network architecture”。',
 'In one line: CADS contributes a data-centric resource, not a new network. The paper says so directly: "The contribution is not a new network architecture" — it curates fragmented public data into consistent, complete labels and trains an established nnU-Net on them.')}</p>
</div></section>''')

SOURCES = [  # name, region (Table 1), vols, license (HF dataset card / Table 1)
 ('VISCERAL Gold Corpus', 'WB, VR', 40, 'Customized'), ('VISCERAL Silver Corpus', 'WB, VR', 127, 'Customized'), ('KiTS', 'AB', 300, 'CC BY-NC-SA 4.0'),
 ('LiTS', 'AB', 201, 'CC BY-NC-SA 4.0'), ('BTCV-Abdomen', 'AB', 50, 'CC BY 4.0'), ('BTCV-Cervix', 'PR', 50, 'CC BY 4.0'), ('CHAOS (CT)', 'AB', 40, 'CC BY-NC-SA 4.0'),
 ('CT-ORG', 'WB, AB', 140, 'CC BY 3.0'), ('AbdomenCT-1K', 'AB', 1062, 'CC BY 4.0'), ('VerSe', 'SP', 374, 'CC BY-SA 4.0'), ("EXACT'09", 'TH', 40, 'Customized'),
 ('CAD-PE', 'TH', 40, 'CC BY 4.0'), ('RibFrac', 'TH, AB', 660, 'CC BY-NC 4.0'), ('Learn2Reg', 'AB', 16, 'CC BY 3.0 + TCIA'), ('LNDb', 'TH', 294, 'CC BY-NC-ND 4.0'),
 ('LIDC-IDRI', 'TH', 997, 'CC BY 3.0'), ('LOLA11', 'TH', 55, 'Customized'), ('SLIVER07', 'TH', 30, 'Customized'), ('CT Lymph Nodes', 'TH, AB', 174, 'CC BY 3.0'),
 ('CPTAC-CCRCC', 'TH, AB', 258, 'CC BY 3.0'), ('CPTAC-LUAD', 'TH, AB', 133, 'CC BY 3.0'), ('CT Images in COVID-19', 'TH', 121, 'CC BY 4.0'),
 ('NSCLC Radiogenomics', 'TH', 131, 'CC BY 3.0'), ('Pancreas-CT', 'AB', 80, 'CC BY 3.0'), ('Pancreatic-CT-CBCT-SEG', 'TH, AB', 93, 'CC BY 4.0'),
 ('RIDER Lung CT', 'TH', 59, 'CC BY 4.0'), ('TCGA-KICH', 'AB', 17, 'CC BY 3.0'), ('TCGA-KIRC', 'AB', 398, 'CC BY 3.0'), ('TCGA-KIRP', 'AB', 19, 'CC BY 3.0'),
 ('TCGA-LIHC', 'AB', 242, 'CC BY 3.0'), ('STOIC2021', 'TH', 2000, 'CC BY-NC 4.0'), ('NLST', 'TH', 7172, 'CC BY 4.0'), ('EMPIRE10', 'TH', 60, 'Customized'),
 ('TotalSegmentator', 'VR', 1203, 'CC BY 4.0'), ('AMOS', 'AB', 200, 'CC BY 4.0'), ('HaN-Seg', 'HN', 42, 'CC BY-NC-ND 4.0'),
 ('SAROS', 'WB, VR', 900, 'CC BY 3.0 / 4.0 / BY-NC 3.0'), ('CT-RATE', 'TH', 3134, 'CC BY-NC-SA 4.0'), ('New: BrainCT-1mm (head CT)', 'HN', 484, 'CC BY 4.0'),
 ('New: CT-TRI (triphasic abdomen)', 'AB', 586, 'CC BY-NC-SA 4.0')]
assert len(SOURCES) == 40 and sum(s[2] for s in SOURCES) == 22022, sum(s[2] for s in SOURCES)
rows = ''.join(f'<tr><td>{n}</td><td>{r}</td><td class="n">{v:,}</td><td>{lic}</td></tr>' for n, r, v, lic in sorted(SOURCES, key=lambda s: -s[2]))
S.append(f'''<section id="dataset"><div class="wrap">
<h2><span class="no">02</span>{T('CADS-dataset：22,022 个 CT', 'CADS-dataset: 22,022 CT volumes')}</h2>
<p class="sub">{T('把公开档案、挑战赛数据和两份新医院数据整合到同一个解剖标签空间。', 'Public archives, challenge datasets and two new hospital cohorts merged into one anatomical label space.')}</p>
<div class="grid2">
<div class="card"><h4>{FACT}{T('规模与来源', 'Scale and sources')}{R('xu2026')}</h4><ul>
<li>{T('22,022 个 CT，来自 40 个来源、16 个国家、100 多个影像中心，采集年份 2007–2024。', '22,022 CT volumes from 40 sources, 16 countries and more than 100 centres, acquired 2007–2024.')}</li>
<li>{T('其中只有 4,695 个（21%）带部分标注；约 79% 完全没有标注。', 'Only 4,695 (21%) carry partial annotations; about 79% have none.')}</li>
<li>{T('与 TotalSegmentator 数据集相比：扫描数约 18 倍，独立目标多 60%。', 'Versus the TotalSegmentator dataset: about 18× as many scans and 60% more distinct targets.')}{R('wasserthal2023')}</li>
<li>{T('大宗来源：NLST 7,172、CT-RATE 3,134、TotalSegmentator 1,203（104 个结构的标注）、AbdomenCT-1K 1,062。', 'Largest sources: NLST 7,172, CT-RATE 3,134, TotalSegmentator 1,203 (annotated for 104 structures), AbdomenCT-1K 1,062.')}</li>
<li>{T('新贡献：484 个头部 CT（土耳其，Istanbul Medipol University 伦理批准）与 586 个三期增强腹部 CT（德国，TUM 伦理批准）。', 'New contributions: 484 head CTs (Türkiye; Istanbul Medipol University ethics approval) and 586 triphasic contrast-enhanced abdominal CTs (Germany; TUM ethics approval).')}</li>
<li>{T('涵盖健康人与多种疾病：肿瘤（癌、淋巴瘤、转移）、COVID-19、创伤和罕见病；增强与平扫；头颈、胸、腹、盆、脊柱及全身视野。', 'Healthy and pathological cases — cancers, lymphoma, metastases, COVID-19, trauma, rare disorders; contrast and non-contrast; head–neck, chest, abdomen, pelvis, spine and whole-body fields of view.')}</li></ul></div>
<div class="card"><h4>{FACT}{T('统一预处理', 'Harmonised preprocessing')}{R('xu2026')}</h4><ul>
<li>{T('全部重定向到 RAS 坐标，并重采样到 1.5 mm 各向同性。', 'All scans reoriented to RAS and resampled to 1.5 mm isotropic.')}</li>
<li>{T('简化仿射矩阵：去除旋转与平移，保留缩放与剪切，便于形状质控和跨扫描比较。', 'Affines simplified by removing rotation and translation (keeping scale and shear) to support shape-based QC and cross-scan comparison.')}</li>
<li>{T('新头部 CT 的面部区域用高斯滤波模糊（1.5 mm 下 σ = 5 体素）以降低可识别性。', 'Faces in the new head CTs blurred with a Gaussian filter (σ = 5 voxels at 1.5 mm) to reduce identifiability.')}</li>
<li>{T('标签空间以 SNOMED CT 为参照：每个目标给出 SNOMED 编码、包含/重叠关系与标注规范（补充表 1）。', 'Label space referenced to SNOMED CT: every target has a SNOMED code, containment/overlap relations and a contouring convention (Suppl. Table 1).')}</li></ul>
<p class="note">{TEACH}{T('教学提示：1.5 mm 各向同性重采样意味着耳蜗（中位仅 33 体素）这类小结构天然受部分容积效应限制——这也解释了后面小结构分割较难。', 'Teaching tip: at 1.5 mm isotropic, tiny targets such as the cochlea (median 33 voxels) are inherently limited by partial-volume effects — which foreshadows why small structures are harder later.')}</p></div>
</div>
<h3>{FACT}{T('40 个数据来源（体数据量与许可）', 'The 40 data sources (volumes and licence)')}</h3>
<p class="src">{T('数量与身体区域来自论文表 1；许可来自 Hugging Face 数据集卡片与表 1。区域：WB 全身，HN 头颈，TH 胸，AB 腹，PR 盆，SP 脊柱，VR 多区域。合计 22,022。', 'Counts and body regions from Table 1 of the paper; licences from the Hugging Face dataset card and Table 1. Regions: WB whole body, HN head–neck, TH thorax, AB abdomen, PR pelvis, SP spine, VR various. Total 22,022.')}</p>
<div class="tbl" style="max-height:420px"><table><thead><tr><th>{T('来源', 'Source')}</th><th>{T('区域', 'Region')}</th><th class="n">{T('CT 数', 'Volumes')}</th><th>{T('许可', 'Licence')}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note red">{T('数据许可是逐来源的：CADS 团队并不拥有外部来源 CT 的原始所有权；在 Hugging Face 申请访问时须同意逐个数据集的许可条款（其中包含 CC BY-NC-ND、定制许可等）。本课件不转载任何 CADS-dataset 的影像或掩膜，只链接。',
 'Data licensing is per source: the CADS team does not own the externally sourced CT images, and gated access on Hugging Face requires agreeing to each source\'s terms (including CC BY-NC-ND and customised licences). This module redistributes no CADS-dataset images or masks; it only links to them.')}</p>
</div></section>''')

S.append(f'''<section id="pipeline"><div class="wrap">
<h2><span class="no">03</span>{T('从稀疏标注到 167 类全身标签：四步流程', 'From sparse labels to 167-class whole-body labels: the four-step pipeline')}</h2>
<p class="sub">{T('两轮迭代：先用全标注数据训练模型生成伪标签，再用筛选后的标签训练最终模型。', 'Two iterations: models trained on fully annotated data generate pseudo-labels; curated labels then train the final model.')}</p>
<div class="steps">
<div class="step"><h4>{T('全身伪标注', 'Whole-body pseudo-labelling')}</h4><p>{FACT}{T('把 167 个目标分成 9 个解剖组，每组训练一个专用 nnU-Net，初始训练数据来自 5 个来源：TotalSegmentator（104 类，构成 9 组中的 5 组）、VISCERAL 上新勾画的 10 个放疗危及器官、HaN-Seg 头颈结构、经 ANTs 配准 SimNIBS 图谱得到的脑结构、SAROS 体腔/组织（2D 稀疏标注层间插值成 3D）。随后对 22,022 个 CT 全部生成伪标签。', 'Split the 167 targets into 9 groups and train a specialised nnU-Net per group from 5 sources: TotalSegmentator (104 classes, forming 5 of the 9 groups), 10 newly contoured radiotherapy OARs on VISCERAL, HaN-Seg head–neck structures, brain labels from the SimNIBS atlas via ANTs registration, and SAROS cavities/tissues (sparse 2D slices interpolated to 3D). Then pseudo-label all 22,022 CTs.')}</p></div>
<div class="step"><h4>{T('形状质控', 'Shape-based quality control')}</h4><p>{FACT}{T('用神经隐式函数的 auto-decoder 只在真实标注上学习“正常形状”；对每个伪标签求最能重建它的隐编码，以伪标签与重建之间的 90 百分位 Hausdorff 距离作为异常分数。总分最差的 10% 图像不进入 Shape 版本的训练集。', 'An auto-decoder based on neural implicit functions learns plausible shapes from ground truth only; each pseudo-label is reconstructed by optimising a latent code, and the 90th-percentile Hausdorff distance between label and reconstruction is the outlier score. The worst-scoring 10% of images are withheld from the Shape-flavour training set.')}{R('amiranashvili2024')}</p></div>
<div class="step"><h4>{T('逐结构选标签', 'Structure-wise label selection')}</h4><p>{FACT}{T('训练三种“口味”模型：GT（只用原始真标注）、Pseudo（全部伪标签）、Shape（质控后伪标签）。每个结构在验证集上按 Dice 排名（优先用来源不匹配的 OOD 验证），p < 0.05 无差异时用 HD95 决胜。最终标签：原始真标注优先，其余用选中口味的预测，并按可靠性逐步合并。', 'Train three flavours: GT (original labels only), Pseudo (all pseudo-labels) and Shape (QC-filtered pseudo-labels). For each structure, rank by Dice on validation (out-of-distribution when available); ties at p < 0.05 broken by HD95. Final labels: original ground truth first, otherwise the selected flavour, merged in order of reliability.')}</p></div>
<div class="step"><h4>{T('训练最终模型', 'Train the final model')}</h4><p>{FACT}{T('nnU-Net v2.5.1 的残差编码器 U-Net（ResEnc-L），按类出现概率的倒数做类均衡采样——例如 C1–C5 椎骨只出现在 905–3,255 个 CT 中，而肝、脾、主动脉都超过 21,000 个。9 个分区模型共同覆盖 167 个目标。', 'nnU-Net v2.5.1 residual-encoder U-Net (ResEnc-L) with class-balanced sampling weighted by inverse class-occurrence probability — e.g. C1–C5 each appear in only 905–3,255 CTs, while liver, spleen and aorta each exceed 21,000. Nine region models together cover all 167 targets.')}{R('isensee2021', 'isensee2024')}</p></div>
</div>
{fig('fig2-pipeline', 2, '图 2：CADS-dataset 与 CADS-model 的开发流程（上：两轮迭代；下：四步流程）。', 'Fig. 2: development pipeline of the CADS-dataset and CADS-model (top: two-iteration workflow; bottom: four steps).', 'Fig. 2 of the CADS paper: pipeline', 'Fig. 2 of the CADS paper: pipeline')}
<p class="note cy">{TEACH}{T('类比：Pseudo 像“大量实习生勾画”，Shape 像“先让主任按解剖常识剔除明显离谱的勾画”，GT 像“少量专家金标准”。CADS 不是只信一种，而是对每个结构挑在外部数据上表现最好的那一种。论文讨论部分指出，多模型平均主要降低伪标签中随机（方差）部分的误差；系统性错误需要像保留肋椎关节这样的定向解剖修正。',
 'Analogy: Pseudo is "many trainees contouring", Shape is "a senior removing anatomically absurd contours first", GT is "a small expert gold standard". CADS picks, per structure, whichever generalises best. The Discussion notes that averaging across models mainly reduces the random (variance) part of pseudo-label error; systematic errors need targeted anatomical fixes such as preserving costovertebral joints.')}</p>
</div></section>''')

grp_rows = ''.join(f'<tr><td class="n">T{k}</td><td>{T(v["zh"], v["en"])}</td><td>{v["slicer"]}</td><td class="n">{sum(1 for l in LAB["labels"] if l["group"] == int(k))}</td></tr>' for k, v in LAB['groups'].items())
S.append(f'''<section id="labels"><div class="wrap">
<h2><span class="no">04</span>{T('167 个结构：交互式标签浏览器', 'The 167 structures: interactive label browser')}</h2>
<p class="sub">{T('按教学系统或按模型组（T551–T559）浏览；点击任一结构查看 SNOMED CT 编码、出现例数与中位体积。', 'Browse by teaching system or by model group (T551–T559); click a structure for its SNOMED CT code, prevalence and median size.')}</p>
{fig('fig1-anatomical-coverage', 1, '图 1：CADS 从头到膝分割 167 个结构；中间为全身分割的前后位三维渲染，周围为 9 个模型组。', 'Fig. 1: CADS segments 167 structures from head to knees; centre, anterior and posterior 3D renderings; around it, the nine model groups.', 'Fig. 1 of the CADS paper: anatomical coverage', 'Fig. 1 of the CADS paper: anatomical coverage')}
<div class="lbtools"><input id="lbSearch" type="search" data-ph-zh="搜索：中文名、英文名、SNOMED 编码、T55x…" data-ph-en="Search: name, Chinese name, SNOMED code, T55x…" aria-label="search">
<div class="seg" id="lbMode"><button type="button" class="on" data-m="teach">{T('按系统', 'By system')}</button><button type="button" data-m="group">{T('按模型组', 'By model group')}</button></div><span class="lbcount" id="lbCount"></span></div>
<div class="chips" id="lbChips"></div>
<div id="lbList"></div>
<div class="lbdetail" id="lbDetail" aria-live="polite"></div>
<p class="src">{FACT}{T('名称与组号：官方 labelmap.md（Apache-2.0）；SNOMED CT 与上级系统：补充表 1；出现例数与中位体素：论文表 2。', 'Names and groups: official labelmap.md (Apache-2.0); SNOMED CT and parent systems: Suppl. Table 1; prevalence and median voxels: Table 2.')} {TEACH}{T('“按系统”分组是作者为教学做的归类（论文图 3 用了类似但不完全相同的系统配色），不是论文的正式分组。', '"By system" is the author\'s teaching grouping (Fig. 3 of the paper uses a similar, not identical, colour scheme), not an official grouping.')}</p>
<h3>{FACT}{T('9 个模型组', 'The nine model groups')}</h3>
<div class="tbl"><table><thead><tr><th>{T('任务', 'Task')}</th><th>{T('内容（官方 README）', 'Content (official README)')}</th><th>{T('3D Slicer 中的名称', 'Name in 3D Slicer')}</th><th class="n">{T('结构数', 'Labels')}</th></tr></thead><tbody>{grp_rows}</tbody></table></div>
<p class="note cy">{TEACH}{T('标签空间是“层级的”：粗类和细类可以共存并重叠。例如 T559 的“肌肉”覆盖全身肌肉软组织，而 T554 的髂腰肌、T556 的腰大肌是其中的细类；T556 的“心脏”含心包囊，T553 另有四个心腔和心肌。用于计量时要先想清楚取哪一级。', 'The label space is hierarchical: coarse and fine labels coexist and may overlap. T559 "Muscle" covers all muscular soft tissue, while T554 iliopsoas and T556 psoas major are finer labels inside it; T556 "Heart" includes the pericardial sac, while T553 adds four chambers and myocardium. Decide which level you need before measuring.')}</p>
</div></section>''')

S.append(f'''<section id="models"><div class="wrap">
<h2><span class="no">05</span>{T('CADS-model：权重版本与许可', 'CADS-model: weight variants and licences')}</h2>
<p class="sub">{T('同一网络结构、同样 9 个任务（T551–T559）、同样 167 个目标；差别在训练数据的许可范围。', 'Same architecture, same nine tasks (T551–T559) and 167 targets; the variants differ in which licensed data were used for training.')}</p>
<div class="tbl"><table><thead><tr><th>{T('版本（CLI 名）', 'Variant (CLI name)')}</th><th>{T('权重许可', 'Weight licence')}</th><th class="n">{T('最大训练集', 'Max. training set')}</th><th>{T('适用', 'Intended use')}</th></tr></thead><tbody>
<tr><td><code>reference</code></td><td>{T('CADS 定制模型许可', 'CADS customised model licence')}</td><td class="n">21,277</td><td>{T('复现论文结果；额外用了 EXACT09、LOLA11、SLIVER07、EMPIRE10，须遵守这些挑战赛条款', 'Reproduce the paper; additionally trained on EXACT09, LOLA11, SLIVER07, EMPIRE10, whose terms apply')}</td></tr>
<tr><td><code>research</code></td><td>CC BY-NC-SA 4.0</td><td class="n">21,124</td><td>{T('官方推荐：多数学术、非商业研究；在报告的评估中与 reference 近乎相同', 'Officially recommended for most academic, non-commercial research; nearly identical to reference in the reported evaluation')}</td></tr>
<tr><td><code>open</code></td><td>CC BY-SA 4.0</td><td class="n">13,269</td><td>{T('需要可再分发（含商业）的派生权重；部分精细头颈危及器官性能可能下降', 'When redistributable (incl. commercial) derived weights are needed; some detailed head–neck OARs may degrade')}</td></tr>
<tr><td>CADS-region</td><td>{T('同 reference 的定制许可', 'Same customised licence as reference')}</td><td class="n">–</td><td>{T('按解剖区域重组为 13 个任务（T601–T613）', 'Reorganised into 13 region tasks (T601–T613)')}</td></tr>
</tbody></table></div>
<p class="src">{FACT}{T('来源：官方仓库 README 与 cads/LICENSE_MODEL；代码本身为 Apache-2.0。“最大训练集”指过滤后 9 个任务中最大的训练集。', 'Source: official README and cads/LICENSE_MODEL; the code itself is Apache-2.0. "Max. training set" is the largest per-task training set after filtering.')}</p>
<div class="grid2" style="margin-top:14px">
<div class="card"><h4>{FACT}{T('工程参数（官方文档）', 'Engineering facts (official docs)')}</h4><ul>
<li>{T('代码版本 v1.0.3；reference 权重为 release v1.0.0。', 'Code release v1.0.3; reference weights release v1.0.0.')}</li>
<li>{T('每个任务的预训练模型约 727 MB；全部 9 个任务建议预留约 7 GB 磁盘。', 'About 727 MB per task model; reserve about 7 GB for all nine tasks.')}</li>
<li>{T('CPU 模式更慢：胸腹 CT 约需 10 分钟以上（3D Slicer 插件 README）。', 'CPU mode is slower: 10+ minutes for a chest–abdomen CT (3D Slicer plugin README).')}</li>
<li>{T('输出可显示为 SNOMED CT 标准名称，便于进入临床研究流程。', 'Outputs can be shown with SNOMED CT standard names for clinical-research workflows.')}</li></ul></div>
<div class="card"><h4>{FACT}{T('网络结构基准（补充说明 3）', 'Architecture benchmark (Suppl. Note 3)')}</h4><p>{T('在相同数据、预处理和划分下，把 ResEnc-L 与 MedNeXt-M、SegResNet、SwinUNETR、U-Mamba Bot 比较；论文把这作为补充分析，正文结论不依赖新结构。', 'With identical data, preprocessing and split, ResEnc-L was compared with MedNeXt-M, SegResNet, SwinUNETR and U-Mamba Bot; this is a supplementary analysis and the main claims do not rely on a new architecture.')}</p></div>
</div>
</div></section>''')

DS = [('BTCV-Cervix', 18.63), ('HaN-Seg', 12.18), ('VISCERAL GC-Extra', 9.01), ('SAROS', 3.67), ('KiTS', 2.95), ('TotalSegmentator', 1.66), ('VISCERAL SC', 1.16),
      ('AbdomenCT-1K', 0.78), ('VISCERAL GC', 0.27), ('VerSe', 0.22), ('SLIVER07', 0.22), ('LiTS', 0.19), ('AMOS', 0.18), ('Learn2reg', 0.15), ('CHAOS', 0.06),
      ('CT-ORG', -0.24), ('BTCV-Abdomen', -1.31), ('EMPIRE10', -6.49)]
lo, hi = -7.0, 20.0
def bar(n, v):
    zero = (0 - lo) / (hi - lo) * 100; x = (v - lo) / (hi - lo) * 100
    left, w = (zero, x - zero) if v >= 0 else (x, zero - x)
    col = 'var(--green)' if v >= 0 else 'var(--red)'
    return f'<div class="barrow"><span class="t">{n}</span><span class="track"><span class="fill" style="left:{left:.1f}%;width:{max(w,0.4):.1f}%;background:{col}"></span></span><span class="v {"pos" if v>=0 else "neg"}">{v:+.2f}</span></div>'
bars = ''.join(bar(n, v) for n, v in DS)
S.append(f'''<section id="eval"><div class="wrap">
<h2><span class="no">06</span>{T('评估：18 个公开数据集', 'Evaluation: 18 public datasets')}</h2>
<p class="sub">{T('主对照是同样基于 nnU-Net 的 TotalSegmentator v2.4.0（最强推理配置），以把“数据的贡献”与“网络的贡献”分开。', 'The main baseline is TotalSegmentator v2.4.0 (strongest inference setting), which also uses nnU-Net — isolating the contribution of data from that of architecture.')}{R('wasserthal2023')}</p>
<div class="tbl"><table><thead><tr><th>{T('测试数据', 'Test data')}</th><th class="n">TotalSeg Dice %</th><th class="n">CADS Dice %</th><th class="n">TotalSeg HD95 mm</th><th class="n">CADS HD95 mm</th></tr></thead><tbody>
<tr><td>{T('主测试（完整标注，117 个共同目标）', 'Primary (complete labels, 117 mutual targets)')}</td><td class="n">89.22</td><td class="n">91.51</td><td class="n">5.63</td><td class="n">3.21</td></tr>
<tr><td>{T('次测试（部分标注）', 'Secondary (partial labels)')}</td><td class="n">81.78</td><td class="n">83.90</td><td class="n">10.70</td><td class="n">7.60</td></tr>
<tr><td>{T('全部测试数据（117 个共同目标）', 'Full test data (117 mutual targets)')}</td><td class="n">88.12</td><td class="n">90.52</td><td class="n">7.38</td><td class="n">4.36</td></tr>
<tr><td>{T('CADS 全部目标（图 4a：不含面部，共 166 个）', 'CADS all targets (Fig. 4a: 166, face excluded)')}</td><td class="n">–</td><td class="n">85.87</td><td class="n">–</td><td class="n">5.23</td></tr>
</tbody></table></div>
<p class="src">{FACT}{T('来源：图 4a 表格与正文。共同目标的宏平均 Dice：CADS 90.52%（95% CI 88.12–92.41，中位 92.33）对 TotalSegmentator 88.12%（95% CI 85.18–90.48，中位 90.13）。CADS 在 71 个结构上 Dice 更高，其中 44 个 p < 0.05（逐结构配对比较，未做多重比较校正）。',
 'Source: Fig. 4a table and text. Macro-averaged Dice on mutual targets: CADS 90.52% (95% CI 88.12–92.41; median 92.33) vs TotalSegmentator 88.12% (95% CI 85.18–90.48; median 90.13). CADS had higher Dice in 71 structures, 44 with p < 0.05 (structure-wise paired tests, no multiple-testing correction).')}</p>
{fig('fig3-structure-dice', 3, '图 3：167 个结构的平均 Dice（橙：CADS；紫：TotalSegmentator）。绿色十字标出 49 个只有 CADS 能分割的结构。', 'Fig. 3: mean Dice for all 167 structures (orange CADS, purple TotalSegmentator). Green crosses mark the 49 structures only CADS segments.', 'Fig. 3 of the CADS paper: structure-level Dice', 'Fig. 3 of the CADS paper: structure-level Dice')}
<div class="grid2">
<div class="card"><h4>{FACT}{T('数据集层面：Dice 差值（CADS − TotalSeg，百分点）', 'Dataset level: Dice difference (CADS − TotalSeg, percentage points)')}</h4>
<div class="bars">{bars}</div>
<p class="src">{T('数值读自图 4b 的标注。18 个数据集中 15 个 Dice 更高、16 个 HD95 更低；18 个数据集平均 Dice 高 2.40 个百分点、HD95 低 3.96 mm；HD95 降幅最大的是 BTCV-Cervix（42.21 mm）与 HaN-Seg（14.18 mm）。', 'Values as annotated in Fig. 4b. Higher Dice in 15 of 18 datasets and lower HD95 in 16; on average +2.40 points Dice and −3.96 mm HD95; largest HD95 reductions in BTCV-Cervix (42.21 mm) and HaN-Seg (14.18 mm).')}</p></div>
<div class="card"><h4>{FACT}{T('为什么全部 167 个的平均更低？', 'Why is the all-167 average lower?')}</h4><ul>
<li>{T('训练数据有限：如颊黏膜只出现在不到 1,000 个扫描中，且只有 30 个真标注。', 'Limited training data: e.g. buccal mucosa appears in fewer than 1,000 scans with only 30 ground-truth annotations.')}</li>
<li>{T('极小器官（< 0.5 mL），如杓状软骨，受 CT 分辨率与部分容积效应限制。', 'Very small organs (< 0.5 mL) such as the arytenoid cartilage, limited by CT resolution and partial-volume effects.')}</li>
<li>{T('解剖复杂的结构，尤其小腺体。', 'Anatomically complex structures, particularly small glands.')}</li></ul>
<h4 style="margin-top:12px">{FACT}{T('参考标注本身也会错', 'Reference labels can be wrong too')}</h4>
<p>{T('作者逐一审阅 TotalSegmentator 测试集的 4,597 个“病例-结构”对，3,002 个判定可靠并保留；肋骨与椎骨错误最突出。放射科医师人工修正了 9 个结构共 72 个被排除的对，作为修正后的小基准。在专家核实子集上 CADS 的 Dice 为 93.15%。', 'The authors reviewed 4,597 case–structure pairs in the TotalSegmentator test set; 3,002 were judged reliable and kept, with errors most prominent in ribs and vertebrae. Radiologists corrected 72 excluded pairs across nine structures as a mini-benchmark. On the expert-verified subset CADS reached a Dice of 93.15%.')}</p></div>
</div>
{fig('fig4-benchmark', 4, '图 4：(a) 主/次/全部测试数据的 Dice 与 HD95；(b) 18 个数据集的 Dice 与 HD95；(c) 苏黎世大学医院队列 38 个结构的 Dice 对比。', 'Fig. 4: (a) Dice and HD95 on primary/secondary/full test data; (b) per-dataset Dice and HD95 across 18 datasets; (c) Dice for 38 structures in the University Hospital Zurich cohort.', 'Fig. 4 of the CADS paper: benchmark', 'Fig. 4 of the CADS paper: benchmark')}
<p class="note cy">{TEACH}{T('读数要点：Dice 衡量重叠（越高越好），HD95 衡量边界最差处的距离（越低越好）。论文提醒，CADS 与基线在数据规模、解剖覆盖、来源多样性和标签整理上都不同，提升不应只归因于训练集变大。',
 'Reading tip: Dice measures overlap (higher is better); HD95 measures near-worst boundary distance (lower is better). The paper cautions that CADS differs from the baseline in scale, coverage, diversity and curation, so gains should not be attributed to training-set size alone.')}</p>
</div></section>''')

S.append(f'''<section id="realworld"><div class="wrap">
<h2><span class="no">07</span>{T('真实世界：苏黎世大学医院 2,864 例肿瘤 CT', 'Real world: 2,864 oncology CTs from University Hospital Zurich')}</h2>
<p class="sub">{T('独立队列，未参与模型开发；参考掩膜在 MIM 软件中生成并经医师确认，或由放射肿瘤医师按临床规范直接勾画。', 'An independent cohort not used in development; reference masks were generated in MIM and validated by physicians, or contoured directly by radiation oncologists to clinical protocols.')}</p>
<div class="grid3">
<div class="card"><h4>{FACT}{T('队列', 'Cohort')}</h4><p>{T('2,864 个 CT，38 个有临床参考的结构（28 个两模型都支持 + 10 个仅 CADS 支持）；最大病种组为中枢神经系统恶性肿瘤、骨肿瘤和头颈癌。数据不对外开放。', '2,864 CTs; 38 structures with clinical references (28 supported by both models, 10 by CADS only); largest disease groups CNS malignancies, bone tumours and head–neck cancers. Data are not available externally.')}</p></div>
<div class="card"><h4>{FACT}{T('最大提升', 'Largest gains')}</h4><p>{T('都是放疗相关结构：脑干 +23.08 个百分点，腮腺左 +19.40、右 +21.02。', 'All radiotherapy-relevant: brainstem +23.08 points, parotid glands left +19.40 and right +21.02.')}</p></div>
<div class="card"><h4>{FACT}{T('专家审阅', 'Expert review')}</h4><p>{T('一位有 5.5 年经验的放射肿瘤医师逐层审阅；每个结构看中位 Dice 附近的 3 例，以反映“典型”而非最好表现。另有 6 个外部队列共 1,160 个 CT（补充说明 6）。', 'A radiation oncologist with 5.5 years of experience reviewed slice by slice — three cases around the median Dice per structure, to reflect typical rather than best-case performance. Six further external cohorts with 1,160 CTs are in Suppl. Note 6.')}</p></div>
</div>
{fig('fig5-qualitative', 5, '图 5：(a) 肋椎关节与相邻椎骨分离；(b) 达到临床标准的结构与审阅意见；(c) 需要改进或定义不同的结构（气管只含气腔、下腔静脉不精确、直肠偏短、心脏缺少部分上层、脑掩膜定义宽、视交叉偏小）。', 'Fig. 5: (a) costovertebral joints and separation of adjacent vertebrae; (b) structures meeting clinical standards with reviewer comments; (c) structures needing refinement or defined differently (trachea air only, imprecise IVC, short rectum, heart missing superior slices, broad brain mask, undersized chiasm).', 'Fig. 5 of the CADS paper: qualitative assessment', 'Fig. 5 of the CADS paper: qualitative assessment')}
<p class="note red">{FACT}{T('论文原意：这项定性评估提示 CADS 可能与放疗勾画工作流相关，但不构成临床效用的正式证明；那需要盲法、多读者、把 CADS 勾画与人工临床勾画对比的研究。审阅者只有一位且未设盲。', 'In the paper\'s words, this qualitative assessment suggests potential relevance for radiation-oncology contouring but does not constitute a formal demonstration of clinical utility, which would require blinded multi-reader studies against manual clinical contours. There was a single, non-blinded reviewer.')}</p>
</div></section>''')

# ----- real CT lab -----
_unused_sys_btns = ''.join(f'<button type="button" data-s="{k}">{T(v[0], v[1])}</button>' for k, v in SYS.items() if any(d['sys'] == k for d in CASE['labels']))
if inf:
    d = inf['dice_vs_reference']
    n554 = {l['index']: l for l in LAB['labels'] if l['group'] == 554}
    drows = ''.join(f'<tr><td>{T(n554[v["idx"]]["zh"], n554[v["idx"]]["en"])}</td><td>{v["ts"]}</td><td class="n">{v["dice"]:.3f}</td><td class="n">{v["ref_voxels"]:,}</td><td class="n">{v["pred_voxels"]:,}</td></tr>' for k, v in d.items())
    pm = inf['l3_pred_measurements']
    infer_html = f'''<h3>{REAL}{T('真的跑了一次 CADS：T554（躯干肌肉与骨盆）在 CPU 上的推理', 'We actually ran CADS: task T554 (trunk muscles and pelvis) on CPU')}</h3>
<p>{T(f'模型：CADS-model-research（CC BY-NC-SA 4.0）任务 554 的官方权重，经 nnU-Net 2.5.2 推理接口在 2 核 CPU 上运行，约 {inf["seconds"]//60} 分钟。为适应约 8 GB 内存，我们把滑窗块从 192³ 缩小到 128³，并只推理骨盆到 L2 的躯干区域（裁剪范围见数据文件），也没有执行官方脚本的 TPTBox 后处理——所以这是“近似官方流程”的真实输出，不等同于论文报告的性能。本页不分发权重，只展示在一例开放数据上的结果。',
 f'Model: official CADS-model-research weights (CC BY-NC-SA 4.0) for task 554, run through the nnU-Net 2.5.2 predictor on a 2-core CPU in about {inf["seconds"]//60} min. To fit ~8 GB RAM we reduced the sliding-window patch from 192³ to 128³, inferred only the trunk from the pelvis up to L2 (crop recorded in the data file), and skipped the official TPTBox post-processing — so this is a real output of a near-official pipeline, not a reproduction of the paper\'s reported performance. Weights are not redistributed here.')}</p>
<div class="ctpair">{ctfig('ct-l3-cads554-v1.0', 'L3 层面：CADS T554 的真实推理结果（髂腰肌、背深肌）。', 'L3 level: real CADS T554 inference (iliopsoas, deep back muscles).', 'CADS T554 output at L3')}{ctfig('ct-l3-ts554-v1.0', '同一层面：数据集自带的参考掩膜（同类结构）。', 'Same slice: the dataset\'s reference masks for the same structures.', 'Reference masks at L3')}</div>
<div class="ctpair">{ctfig('ct-pelvis-cads554-v1.0', '髂骨翼 / 骶骨上部层面：CADS T554 推理（髋骨、骶骨、臀肌、髂腰肌、背深肌）。', 'Iliac-wing / upper-sacrum level: CADS T554 inference (hip bones, sacrum, gluteal muscles, iliopsoas, deep back muscles).', 'CADS T554 output, iliac wings')}{ctfig('ct-pelvis-ts554-v1.0', '同一层面：参考掩膜。', 'Same slice: reference masks.', 'Reference masks, pelvis')}</div>
<h4>{DER}{T('与参考掩膜的 Dice（推理区域内，体素级）', 'Dice against the reference masks (inside the inferred region, voxel level)')}</h4>
<div class="tbl"><table><thead><tr><th>CADS T554</th><th>TotalSegmentator</th><th class="n">Dice</th><th class="n">{T('参考体素', 'Ref. voxels')}</th><th class="n">{T('预测体素', 'Pred. voxels')}</th></tr></thead><tbody>{drows}</tbody></table></div>
<p class="src">{TEACH}{T('解读注意：(1) 只有 1 例，不能代表整体性能；(2) 参考掩膜是 TotalSegmentator 的“模型生成 + 人工校正”标注，标签定义与 CADS 不完全相同（例如“背深肌”对应 autochthon）；(3) 被推理区域截断的结构（如股骨下段）会拉低 Dice；(4) 该病例在 CADS 公开的测试划分中，未用于训练。', 'Caveats: (1) a single case cannot represent overall performance; (2) the reference is TotalSegmentator\'s model-plus-manual-correction labelling, whose definitions differ slightly from CADS (e.g. "deep muscle of back" ↔ autochthon); (3) structures cut by the inferred region (e.g. lower femur) lower the Dice; (4) this case is in the published CADS test split, so it was not used for training.')}</p>'''
else:
    infer_html = f'''<p class="note red">{T('本版本未能在 CPU 上完成 CADS 推理，阅片器只显示数据集自带的参考掩膜。', 'CADS inference could not be completed on CPU for this version; the viewer shows the dataset\'s reference masks only.')}</p>'''

S.append(f'''<section id="lab"><div class="wrap">
<h2><span class="no">08</span>{T('CADS 真实推理：与参考标注对照', 'A real CADS run, compared with the reference labels')}</h2>
<p class="sub">{REAL}{T('页首阅片器的“CADS 实测推理”开关显示的就是这次推理的逐体素结果（同一结构与参考标注同色）。下方为静态对照图与 Dice。', 'The "CADS inference" switch in the viewer at the top shows this run voxel by voxel (same colour as the matching reference structure). Static comparisons and Dice are below.')}</p>
<p class="vw-open"><a class="btn" href="#viewer" data-vw-stop="l3">{T('▶ 回到阅片器，切换“CADS 实测推理”对照', '▶ Back to the viewer and switch to "CADS inference"')}</a></p>
{infer_html}
</div></section>''')


S.append(f'''<section id="cases"><div class="wrap">
<h2><span class="no">09</span>{T('临床教学案例（急诊创伤外科视角）', 'Clinical teaching cases (emergency & trauma surgery perspective)')}</h2>
<p class="sub">{TEACH}{T('以下三例用同一例真实 CT 讲解“全身分割能帮临床看什么”。它们是教学解读，不是论文结论，也不是诊断建议。', 'Three cases on the same real CT show what whole-body segmentation can help clinicians see. They are teaching interpretations, not paper findings or diagnostic advice.')}</p>
<h3>{T('案例 1 · 创伤 CT 的解剖定位：数肋骨、数椎骨', 'Case 1 · Anatomical orientation in trauma CT: counting ribs and vertebrae')}</h3><p class="vw-open"><a class="btn" href="#viewer" data-vw-stop="chest">{T('▶ 在阅片器中打开：肋骨与肺叶', '▶ Open in the viewer: ribs and lung lobes')}</a></p>
<div class="grid2">{ctfig('ct-chest-t6-bone-ts-v1.0', 'T6 层面骨窗：参考掩膜把每根肋骨、胸椎、胸骨、肩胛骨分别着色。', 'T6 level, bone window: each rib, the thoracic vertebra, sternum and scapulae coloured separately.', 'Chest bone window with rib labels')}
<div class="card"><h4>{TEACH}{T('教学要点', 'Teaching points')}</h4><ul>
<li>{T('在创伤 CT 报告中，“左第 6 肋骨折”的准确性依赖逐根计数；逐根肋骨、逐节椎骨的分割（CADS 的 T552、T555）可以作为计数的核对工具。', 'In trauma reports, "left 6th rib fracture" depends on counting correctly; per-rib and per-vertebra segmentation (CADS T552, T555) can serve as a counting cross-check.')}</li>
<li>{FACT}{T('CADS 专门修正了肋骨标注，保留常被公开数据集漏掉的肋椎关节，并更好地区分相邻椎骨（图 5a）。', 'CADS specifically refined rib labels to keep the costovertebral joints often missing from public datasets, and better separates adjacent vertebrae (Fig. 5a).')}</li>
<li>{T('注意：分割模型不检测骨折；CADS 的标签空间中没有“骨折”“出血”“气胸”等病灶类别。', 'Caution: segmentation models do not detect fractures; the CADS label space has no lesion classes such as fracture, haemorrhage or pneumothorax.')}</li>
<li>{FACT}{T('数据集中颈椎上段（C1–C5）出现例数少（905–3,255 例），模型训练时专门做了类均衡采样。', 'Upper cervical vertebrae (C1–C5) are rare in the data (905–3,255 volumes), which is why class-balanced sampling was used.')}</li></ul></div></div>
<h3>{T('案例 2 · 放疗危及器官（OAR）', 'Case 2 · Radiotherapy organs at risk (OARs)')}</h3><p class="vw-open"><a class="btn" href="#viewer" data-vw-stop="pelvis">{T('▶ 在阅片器中打开：骨盆环与盆腔', '▶ Open in the viewer: pelvic ring and pelvis')}</a></p>
<div class="grid2">{ctfig('ct-pelvis-ts-v1.0', '髋臼层面软组织窗：膀胱、髋骨、股骨头、臀肌、髂血管等参考掩膜。', 'Acetabular level, soft-tissue window: bladder, hip bones, femoral heads, gluteal muscles, iliac vessels.', 'Pelvis soft tissue with reference masks')}
<div class="card"><h4>{TEACH}{T('教学要点', 'Teaching points')}</h4><ul>
<li>{FACT}{T('T556（放疗相关结构：椎管、喉、心脏、肠道空间、乙状结肠、直肠、前列腺、精囊、乳腺、胸骨、腰大肌、腹直肌）与 T558（头颈 OAR 29 个）直接服务于放疗勾画。', 'T556 (RT structures: spinal canal, larynx, heart, bowel space, sigmoid, rectum, prostate, seminal vesicle, mammary glands, sternum, psoas major, rectus abdominis) and T558 (29 head–neck OARs) serve radiotherapy contouring directly.')}</li>
<li>{FACT}{T('T556 的多个结构按放疗规范定义：例如“肠道空间”是从幽门到直乙交界肠管可能占据的空间，“心脏”包含心包囊；头颈 OAR 的勾画参照 HaN-Seg 与国际共识。', 'Several T556 structures follow RT conventions: "bowel space" is the space bowel may occupy from pylorus to rectosigmoid junction, "heart" includes the pericardial sac; head–neck OARs follow HaN-Seg and consensus guidance.')}{R('podobnik2023', 'mir2020')}</li>
<li>{T('自动勾画的价值在于“先给初稿、再由医师逐层修改”；论文专家指出的问题（直肠偏短、视交叉偏小等）正是需要人工复核的位置。', 'Auto-contours are a first draft for physicians to edit slice by slice; the issues flagged by the expert (short rectum, undersized chiasm, etc.) are exactly where human review is needed.')}</li></ul></div></div>
<h3>{T('案例 3 · 身体成分：L3 层面的肌肉', 'Case 3 · Body composition: muscle at the L3 level')}</h3><p class="vw-open"><a class="btn" href="#viewer" data-vw-stop="l3">{T('▶ 在阅片器中打开：L3 层面', '▶ Open in the viewer: L3 level')}</a></p>
<div class="grid2">{ctfig('ct-l3-ts-v1.0', 'L3 椎体中层软组织窗：髂腰肌、背深肌（竖脊肌群）、肾、肝、结肠、小肠、主动脉、下腔静脉的参考掩膜。', 'Mid-L3 level, soft-tissue window: reference masks of iliopsoas, deep back muscles, kidneys, liver, colon, small bowel, aorta and IVC.', 'L3 level with reference masks')}
<div class="card"><h4>{TEACH}{T('教学要点', 'Teaching points')}</h4><ul>
<li>{T('L3 单层面的组织面积与全身脂肪和去脂组织量高度相关（r = 0.86–0.94），因此 L3 常被用作 CT 身体成分分析的标准层面。', 'Tissue areas on a single L3 slice correlate strongly with whole-body fat and fat-free mass (r = 0.86–0.94), which is why L3 is the usual landmark for CT body composition.')}{R('mourtzakis2008')}</li>
<li>{T('骨骼肌面积常用身高平方校正为骨骼肌指数（SMI）；具体诊断阈值因人群而异，引用时应回到原始文献。', 'Muscle area is usually normalised by height² as the skeletal muscle index (SMI); diagnostic cut-offs vary by population and should be taken from the original literature.')}{R('prado2008', 'mitsiopoulos1998')}</li>
<li>{FACT}{T('CADS 提供多级肌肉标签：T559“肌肉”（全身肌肉软组织，SAROS 定义，含筋膜与肌间脂肪，后续自动扣除肌间/肌内脂肪）、T556 腰大肌与腹直肌、T554 髂腰肌与背深肌。', 'CADS offers muscle labels at several levels: T559 "Muscle" (all muscular soft tissue, SAROS definition including fascia and intermuscular fat, with inter/intramuscular fat subtracted automatically), T556 psoas major and rectus abdominis, T554 iliopsoas and deep back muscles.')}</li>
<li>{DER}{T(f'本例 L3 中层，参考掩膜面积：双侧髂腰肌 {psoas_ref} cm²，双侧背深肌 {back_ref} cm²（像素 1.5 × 1.5 mm）。这只是演示“掩膜 → 面积”的计算，不是完整的骨骼肌面积，也未做 HU 阈值处理。',
 f'At mid-L3 in this case the reference masks give: iliopsoas (both sides) {psoas_ref} cm², deep back muscles (both sides) {back_ref} cm² (pixel 1.5 × 1.5 mm). This only demonstrates mask-to-area arithmetic; it is not total skeletal muscle area and no HU thresholding was applied.')}</li></ul></div></div>
</div></section>''')

S.append(f'''<section id="tutorial"><div class="wrap">
<h2><span class="no">10</span>{T('动手教程：命令行与 3D Slicer', 'Hands-on: command line and 3D Slicer')}</h2>
<p class="sub">{FACT}{T('步骤摘自官方 README（2026-11 版本）。使用权重即表示接受对应的模型许可。', 'Steps from the official READMEs (November 2026). Using the weights means accepting the corresponding model licence.')}</p>
<div class="grid2">
<div class="card"><h4>{T('A. Python 命令行', 'A. Python command line')}</h4>
<pre><code># 1) {T('克隆仓库', 'clone')}
git clone https://github.com/murong-xu/CADS.git
# 2) {T('环境（Python ≥ 3.9）', 'environment (Python ≥ 3.9)')}
conda create -n CADS_env python=3.11
conda activate CADS_env
# 3) {T('按系统/CUDA 安装 PyTorch（要求 torch ≥ 2.1.2），例如 Linux + CUDA 12.4：', 'install PyTorch for your OS/CUDA (torch ≥ 2.1.2), e.g. Linux + CUDA 12.4:')}
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \\
  --index-url https://download.pytorch.org/whl/cu124
# 4) {T('安装 CADS', 'install CADS')}
cd CADS && pip install -e .

# {T('一条命令推理（-task 为 all 或 551–559；-license 为 reference/research/open）', 'one-command inference (-task all or 551–559; -license reference/research/open)')}
python cads/scripts/predict_images.py \\
  -in /path/to/ct_images -out /path/to/output \\
  -task all -license research          # {T('无 GPU 时加 --cpu', 'add --cpu without a GPU')}</code></pre>
<p>{T('大批量（约 100–1000 例以上）用分阶段流程：<code>run_01_preprocess.py</code>（CPU，重定向+重采样）→ <code>run_02_inference.py</code>（GPU，输出 _part_551…_part_559）→ <code>run_03_restore_seg.py</code>（CPU，还原到原始几何）。', 'For large batches (≈100–1000+ scans) use the staged pipeline: <code>run_01_preprocess.py</code> (CPU, reorient + resample) → <code>run_02_inference.py</code> (GPU, outputs _part_551…_part_559) → <code>run_03_restore_seg.py</code> (CPU, back to original geometry).')}</p></div>
<div class="card"><h4>{T('B. 3D Slicer 插件（CADSWholeBodyCTSeg）', 'B. 3D Slicer extension (CADSWholeBodyCTSeg)')}</h4>
<ol class="tut">
<li>{T('安装 3D Slicer（官方测试过 5.10.0 稳定版与 5.11.0 预览版）。', 'Install 3D Slicer (tested with stable 5.10.0 and preview 5.11.0).')}</li>
<li>{T('Extension Manager 搜索 <b>PyTorch</b> 安装并重启；在 PyTorch Utils 中输入 <code>&gt;=2.1.2</code> 安装（2.1.2–2.8.0 均可）。', 'Extension Manager → install <b>PyTorch</b>, restart; in PyTorch Utils enter <code>&gt;=2.1.2</code> and install (2.1.2–2.8.0 work).')}</li>
<li>{T('Extension Manager 搜索 <b>NNUNet</b> 安装并重启；在 nnUNet 模块中安装<b>精确版本</b> <code>==2.5.2</code>。', 'Extension Manager → install <b>NNUNet</b>, restart; in the nnUNet module install <b>exactly</b> <code>==2.5.2</code>.')}</li>
<li>{T('Extension Manager 搜索 <b>CADSWholeBodyCTSeg</b> 安装并重启。', 'Extension Manager → install <b>CADSWholeBodyCTSeg</b>, restart.')}</li>
<li>{T('载入 CT → 选 Input volume、Segmentation task（或 All）、Target mode → Apply。默认显示 SNOMED CT 标准名；无 GPU 可勾选 Force to use CPU。', 'Load a CT → choose Input volume, Segmentation task (or All), Target mode → Apply. SNOMED CT names are shown by default; tick Force to use CPU if you have no GPU.')}</li>
<li>{T('每个任务首次运行会下载约 727 MB 模型；全部任务预留约 7 GB。Windows + Slicer ≤ 5.10.0 可能遇到路径反斜杠问题，官方建议升级到 5.11.0。', 'Each task downloads about 727 MB on first run; reserve ~7 GB for all. Windows with Slicer ≤ 5.10.0 may hit a backslash path issue; upgrading to 5.11.0 is recommended.')}</li></ol></div>
</div>
<div class="grid2">
<figure class="fig"><button type="button" data-full="图片/插件截图/slicer-plugin-screenshot02v1.0.webp" data-cap-zh="CADS 3D Slicer 插件截图（官方仓库，Apache-2.0）" data-cap-en="CADS 3D Slicer plugin screenshot (official repository, Apache-2.0)"><img src="图片/插件截图/slicer-plugin-screenshot02v1.0-sm.webp" loading="lazy" width="900" alt="CADS 3D Slicer plugin screenshot"></button>
<figcaption class="figcap">{FACT}{T('插件运行后的界面：左侧按模型组列出结构，悬停显示 SNOMED CT 术语。', 'Plugin after a run: structures listed by model group; hovering shows SNOMED CT terminology.')}<span class="att">{T('Screenshot_02.png，来自 <a href="https://github.com/murong-xu/SlicerCADSWholeBodyCTSeg">murong-xu/SlicerCADSWholeBodyCTSeg</a>（Apache-2.0），缩放并转为 WebP。', 'Screenshot_02.png from <a href="https://github.com/murong-xu/SlicerCADSWholeBodyCTSeg">murong-xu/SlicerCADSWholeBodyCTSeg</a> (Apache-2.0), resized and converted to WebP.')}</span></figcaption></figure>
{fig('fig6-slicer', 6, '图 6：3D Slicer 中的 CADS 扩展，VISCERAL Gold Corpus 去标识 CT 的全身分割（轴、冠、矢状位与三维）。', 'Fig. 6: the CADS extension in 3D Slicer, whole-body segmentation of a de-identified VISCERAL Gold Corpus CT (axial, coronal, sagittal and 3D).', 'Fig. 6 of the CADS paper: 3D Slicer', 'Fig. 6 of the CADS paper: 3D Slicer')}
</div>
<p class="note cy">{TEACH}{T('课堂建议：先用 3D Slicer 跑单个任务（如 T551 腹部器官）让学员看结果，再讨论“模型输出 ≠ 诊断”；需要批量研究时再用命令行。本仓库 <code>示例/</code> 给出了在开放数据上计算 L3 肌肉面积的脚本。', 'Classroom tip: run a single task in 3D Slicer first (e.g. T551 abdominal organs) so learners see the output, then discuss "model output ≠ diagnosis"; use the command line for batch research. <code>示例/</code> in this repository has a script computing L3 muscle area on open data.')}</p>
</div></section>''')

QUIZ = [
 ('CADS-dataset 一共有多少个 CT？', 'How many CT volumes are in the CADS-dataset?', ['4,695', '22,022', '2,864', '1,203'], 1,
  '22,022 个，来自 40 个来源；其中只有 4,695 个（21%）带部分标注。', '22,022 from 40 sources; only 4,695 (21%) carry partial annotations.'),
 ('CADS 的核心贡献是什么？', 'What is the core contribution of CADS?', ['一种新的 Transformer 网络', '数据为中心：统一、补全并整理大规模标注，再用成熟的 nnU-Net 训练', '一种新的骨折检测算法', '一台新的 CT 设备'], 1,
  '论文明确说贡献“不是新的网络结构”，而是大规模、一致整理的标注。', 'The paper states the contribution "is not a new network architecture" but consistently curated large-scale labels.'),
 ('形状质控用什么度量判断伪标签是否离谱？', 'Which metric does the shape QC use to flag implausible pseudo-labels?', ['Dice', '90 百分位 Hausdorff 距离（伪标签与其形状重建之间）', '体积', 'HU 均值'], 1,
  '它对离群点敏感、又不被少数远处体素主导；最差的 10% 图像不进 Shape 版本训练。', 'It is outlier-sensitive yet robust to a few far voxels; the worst 10% of images are withheld from the Shape flavour.'),
 ('最终每个结构的标签来自哪里？', 'Where does each structure\'s final label come from?', ['永远来自 Pseudo 模型', '原始真标注优先；没有时用在验证集上排名最高的口味（GT/Pseudo/Shape）', '随机挑一个', '由 3D Slicer 用户手工勾画'], 1,
  '逐结构选择，优先用来源不匹配的 OOD 验证排名。', 'Selection is per structure, preferring out-of-distribution validation for ranking.'),
 ('在 117 个共同目标上，CADS 与 TotalSegmentator 的宏平均 Dice 分别是？', 'On the 117 mutual targets, macro-averaged Dice for CADS vs TotalSegmentator was?', ['85.87% vs 88.12%', '90.52% vs 88.12%', '93.15% vs 90.52%', '99% vs 80%'], 1,
  '90.52%（95% CI 88.12–92.41）对 88.12%（95% CI 85.18–90.48）。93.15% 是专家核实子集上的结果，85.87% 是 CADS 全部目标的平均。', '90.52% (95% CI 88.12–92.41) vs 88.12% (95% CI 85.18–90.48). 93.15% is on the expert-verified subset; 85.87% is CADS over all targets.'),
 ('真实世界队列中提升最大的结构是？', 'Which structure gained most in the real-world cohort?', ['肝', '脑干（+23.08 个百分点）', '股骨', '主动脉'], 1,
  '脑干 +23.08，腮腺左 +19.40、右 +21.02，都是放疗相关结构。', 'Brainstem +23.08, parotids +19.40 (L) and +21.02 (R) — all radiotherapy-relevant.'),
 ('下列哪项是论文自己承认的局限？', 'Which is a limitation acknowledged by the paper?', ['覆盖了手和足', '定性审阅只有一位未设盲的专家', 'CADS 不能在 CPU 上运行', '数据全部来自一家医院'], 1,
  '还包括：形状质控可能滤掉有价值的病理/变异解剖；覆盖头到膝、不含手足；气管、视交叉、直肠、脑等标签需改进。', 'Others: shape QC may filter informative pathological/atypical anatomy; coverage is head to knees without hands/feet; trachea, chiasm, rectum and brain labels need refinement.'),
 ('想把 CADS 权重用于商业产品，哪个版本的许可允许（遵守相同方式共享）？', 'Which weight variant\'s licence allows commercial use (share-alike)?', ['reference', 'research（CC BY-NC-SA 4.0）', 'open（CC BY-SA 4.0）', 'CADS-region'], 2,
  'open 版本为 CC BY-SA 4.0；research 为非商业；reference 与 CADS-region 为定制许可。使用前仍需自行核对许可与法规。', 'open is CC BY-SA 4.0; research is non-commercial; reference and CADS-region use a customised licence. Always check the licence and regulations yourself.'),
]
qhtml = ''
for i, (qz, qe, opts, a, wz, we) in enumerate(QUIZ, 1):
    if isinstance(opts[0], str) and all(isinstance(o, str) for o in opts):
        pass
    o_html = ''.join(f'<button type="button" class="o" data-k="{j}">{chr(65+j)}. {o}</button>' for j, o in enumerate(opts))
    qhtml += f'<div class="q" data-a="{a}"><h4>{i}. {T(qz, qe)}</h4><div class="opts">{o_html}</div><div class="why">{T(wz, we)}</div></div>'
S.append(f'''<section id="quiz"><div class="wrap">
<h2><span class="no">11</span>{T('小测验', 'Quick quiz')}</h2>
<p class="sub">{T('点击选项即判分；每题都附出处要点。得分：', 'Click an option to answer; each comes with its source point. Score: ')}<span class="score" id="qScore">0 / 0</span> <button type="button" class="btn" id="qReset" style="min-height:36px;padding:4px 10px;margin-left:8px">{T('重做', 'Reset')}</button></p>
{qhtml}
<p class="src">{T('选项文字为中文（专业名词与数字中英通用）；题干与解析随语言切换。', 'Options are in Chinese where wording differs (numbers and terms are shared); questions and explanations follow the language toggle.')}</p>
</div></section>''')

S.append(f'''<section id="limits"><div class="wrap">
<h2><span class="no">12</span>{T('局限与注意事项', 'Limitations and cautions')}</h2>
<div class="grid2">
<div class="card"><h4>{FACT}{T('论文自述的局限', "The paper's own limitations")}</h4><ul>
<li>{T('伪标签：形状质控会把低质量伪标签挡在 Shape 版本之外，但也可能滤掉有临床价值的病理或变异解剖；大规模下无法逐例人工修正。', 'Pseudo-labels: shape QC withholds low-quality pseudo-labels from the Shape flavour, but may also filter clinically important pathological or atypical anatomy; manual correction is not feasible at this scale.')}</li>
<li>{T('临床评估：只有一位、未设盲的放射肿瘤医师做定性审阅，目的是找优缺点而非证明临床效用；需要多读者、盲法和临床终点。', 'Clinical evaluation: a single non-blinded radiation oncologist reviewed to find strengths and weaknesses, not to prove clinical utility; multiple readers, blinding and clinical endpoints are needed.')}</li>
<li>{T('覆盖范围：头到膝，不含手足；中枢神经、肌骨和血管系统的精细结构仍缺。', 'Coverage: head to knees, without hands and feet; fine-grained CNS, musculoskeletal and vascular structures are still missing.')}</li>
<li>{T('标签定义：脑掩膜包含颅内全部中枢神经成分（某些用途过宽）；气管只含气腔不含软骨；视交叉偏小；直肠短于解剖范围；面部去标识化限制了面部分析。', 'Label definitions: the brain mask includes all intracranial CNS components (too broad for some uses); trachea covers the lumen, not cartilage; optic chiasm under-segmented; rectum shorter than its anatomical extent; facial anonymisation limits facial analysis.')}</li>
<li>{T('提升来源：数据规模、覆盖、多样性和标签整理同时变化，不能只归因于数据量。', 'Source of gains: scale, coverage, diversity and curation all changed, so gains cannot be attributed to size alone.')}</li></ul></div>
<div class="card"><h4>{TEACH}{T('教学与使用提醒', 'Teaching and usage reminders')}</h4><ul>
<li>{T('分割 ≠ 诊断：CADS 不识别骨折、出血、肿瘤等病灶，正常解剖标签在病变区域可能失真。', 'Segmentation ≠ diagnosis: CADS does not detect fractures, haemorrhage or tumours, and normal-anatomy labels may distort around lesions.')}</li>
<li>{T('许可分层：代码 Apache-2.0；权重分 reference（定制）、research（CC BY-NC-SA 4.0）、open（CC BY-SA 4.0）；数据按 40 个来源各自的许可。用于商业或临床前请逐项核对。', 'Layered licences: code Apache-2.0; weights reference (customised), research (CC BY-NC-SA 4.0), open (CC BY-SA 4.0); data follow each of the 40 sources\' licences. Check each before commercial or clinical use.')}</li>
<li>{T('本页 CPU 推理只有 1 例，且偏离官方配置（块大小、裁剪、无后处理），不能用来评价性能。', 'The CPU inference here is one case with deviations from the official setup (patch size, crop, no post-processing); it cannot be used to judge performance.')}</li>
<li>{T('论文目前是 Article in Press（加速发表版），最终版本可能还有编辑改动；本页数字以 2026-11-13 获取的版本为准。', 'The paper is an Article in Press; the final Version of Record may still change. Numbers here follow the version retrieved on 2026-11-13.')}</li></ul></div>
</div></div></section>''')

S.append(f'''<section id="resources"><div class="wrap">
<h2><span class="no">13</span>{T('资源', 'Resources')}</h2>
<div class="tbl"><table><thead><tr><th>{T('资源', 'Resource')}</th><th>{T('链接', 'Link')}</th><th>{T('许可', 'Licence')}</th></tr></thead><tbody>
<tr><td>{T('论文', 'Paper')}</td><td><a href="{DOI}">doi:10.1038/s41467-026-78732-1</a> · <a href="https://arxiv.org/abs/2507.22953">arXiv:2507.22953</a></td><td>CC BY 4.0</td></tr>
<tr><td>{T('代码与权重', 'Code and weights')}</td><td><a href="https://github.com/murong-xu/CADS">github.com/murong-xu/CADS</a> · <a href="https://github.com/murong-xu/CADS/releases">releases</a></td><td>{T('代码 Apache-2.0；权重见上表', 'Code Apache-2.0; weights see above')}</td></tr>
<tr><td>CADS-dataset</td><td><a href="https://huggingface.co/datasets/mrmrx/CADS-dataset">huggingface.co/datasets/mrmrx/CADS-dataset</a></td><td>{T('“cadsdataset”定制条款 + 各来源许可；需登录申请访问', '"cadsdataset" terms + each source\'s licence; gated access')}</td></tr>
<tr><td>{T('3D Slicer 插件', '3D Slicer extension')}</td><td><a href="https://github.com/murong-xu/SlicerCADSWholeBodyCTSeg">github.com/murong-xu/SlicerCADSWholeBodyCTSeg</a></td><td>Apache-2.0</td></tr>
<tr><td>{T('本页真实 CT', 'Real CT used here')}</td><td><a href="https://doi.org/10.5281/zenodo.10047292">TotalSegmentator dataset v2.0.1（Zenodo）</a></td><td>CC BY 4.0</td></tr>
<tr><td>{T('本课件仓库', 'This module\'s repository')}</td><td><a href="https://github.com/TUANZIDING/cads-ct-teaching">github.com/TUANZIDING/cads-ct-teaching</a></td><td>{T('见下方许可', 'see licence below')}</td></tr>
</tbody></table></div></div></section>''')

def fmt_ref(r):
    au = ', '.join(r['authors'][:3]) + (' et al.' if r.get('n_authors', 0) > 3 or r.get('etal') else '')
    vol = f", {r['volume']}" if r.get('volume') else ''
    pg = f", {r['page']}" if r.get('page') else ''
    return f'{au}. {r["title"]}. <i>{r["container"]}</i> ({r["year"]}){vol}{pg}. <a href="https://doi.org/{r["doi"]}">doi:{r["doi"]}</a>'
refs = ''.join(f'<li id="ref-{i}">{fmt_ref(r)}</li>' for i, r in enumerate(REFS, 1))
S.append(f'''<section id="refs"><div class="wrap">
<h2><span class="no">14</span>{T('参考文献', 'References')}</h2>
<p class="sub">{T('每条 DOI 都经 Crossref / DataCite 核对（题名、年份、卷页）。', 'Every DOI was checked against Crossref / DataCite (title, year, volume, pages).')}</p>
<ol class="refs">{refs}</ol></div></section>''')

S.append(f'''<section id="license"><div class="wrap">
<h2><span class="no">15</span>{T('版权与许可', 'Copyright and licence')}</h2>
<div class="tbl"><table><thead><tr><th>{T('部分', 'Part')}</th><th>{T('许可', 'Licence')}</th></tr></thead><tbody>
<tr><td>{T('作者原创文字、讲义、数据整理（assets/data/*.json 中的作者部分）、截图与封面', "Author's text, handouts, curated data (author parts of assets/data/*.json), screenshots and cover")}</td><td><a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a></td></tr>
<tr><td>{T('代码：页面结构与脚本、CSS/JS、工具/、验证/、示例/ 中的脚本', 'Code: page structure and scripts, CSS/JS, scripts in 工具/, 验证/, 示例/')}</td><td><a href="https://polyformproject.org/licenses/noncommercial/1.0.0/">PolyForm Noncommercial 1.0.0</a></td></tr>
<tr><td>{T('论文原图 图 1–6（Xu 等，Nat Commun 2026）', 'Paper figures 1–6 (Xu et al., Nat Commun 2026)')}</td><td>{T('仍为原作者的 CC BY 4.0，不属于本仓库的非商业许可', "Remain the original authors' CC BY 4.0; not covered by this repository's non-commercial licence")}</td></tr>
<tr><td>{T('真实 CT 切片与掩膜渲染图（TotalSegmentator 数据集派生）', 'Real CT slices and mask renderings (derived from the TotalSegmentator dataset)')}</td><td>{T('CC BY 4.0（Wasserthal 等，Zenodo 10047292）；渲染方式见 工具/渲染CTv1.0.py', 'CC BY 4.0 (Wasserthal et al., Zenodo 10047292); rendering in 工具/渲染CTv1.0.py')}</td></tr>
<tr><td>{T('阅片器数据 assets/viewer/*.nii.gz（CT 与参考掩膜的裁剪、合并、重编号版本）', 'Viewer data assets/viewer/*.nii.gz (cropped, merged, re-indexed CT and reference masks)')}</td><td>{T('CC BY 4.0（Wasserthal 等，Zenodo 10047292）；处理方式见 工具/构建阅片数据v1.1.py', 'CC BY 4.0 (Wasserthal et al., Zenodo 10047292); processing in 工具/构建阅片数据v1.1.py')}</td></tr>
<tr><td>{T('阅片器中的 CADS 推理体积 cads554-s0423-v1.1.nii.gz', 'CADS inference volume in the viewer, cads554-s0423-v1.1.nii.gz')}</td><td>CC BY-NC-SA 4.0</td></tr>
<tr><td>{T('阅片引擎 NiiVue 0.69.0（assets/viewer/niivue-v0.69.0.umd.js，未修改）', 'Viewer engine NiiVue 0.69.0 (assets/viewer/niivue-v0.69.0.umd.js, unmodified)')}</td><td>{T('BSD-2-Clause，见 LICENSES/NiiVue-BSD-2-Clause.txt', 'BSD-2-Clause, see LICENSES/NiiVue-BSD-2-Clause.txt')}</td></tr>
<tr><td>{T('解剖名词对照表（验证/解剖名词对照表v1.1.csv）', 'Anatomical term table (验证/解剖名词对照表v1.1.csv)')}</td><td>{T('作者整理，CC BY-NC 4.0；术语本身为公共规范名词', "Author's compilation, CC BY-NC 4.0; the terms themselves are public standard nomenclature")}</td></tr>
<tr><td>{T('3D Slicer 插件截图、CADS 标签表（labelmap.md）', '3D Slicer plugin screenshot, CADS labelmap (labelmap.md)')}</td><td>{T('Apache-2.0（murong-xu/CADS、SlicerCADSWholeBodyCTSeg），署名保留', 'Apache-2.0 (murong-xu/CADS, SlicerCADSWholeBodyCTSeg), attribution kept')}</td></tr>
<tr><td>{T('CADS 推理结果（L3/骨盆 4 张图与 Dice 表）', 'CADS inference outputs (4 L3/pelvis images and the Dice table)')}</td><td>{T('由 CADS-model-research（CC BY-NC-SA 4.0）生成，按该许可的署名-非商业-相同方式共享条件提供', 'Produced with CADS-model-research (CC BY-NC-SA 4.0) and shared under its attribution, non-commercial, share-alike terms')}</td></tr>
</tbody></table></div>
<p class="note">{T('商业用途需事先联系作者获得授权合作（第三方材料仍须遵守其原始许可）：', 'Commercial use requires prior permission from the author (third-party material remains under its original licence): ')}<a href="https://tuanziding.github.io/#contact">tuanziding.github.io/#contact</a></p>
<p class="src">{T('本课件未分发 CADS-dataset 的任何影像或掩膜，也未分发 CADS 模型权重。', 'No CADS-dataset images or masks and no CADS model weights are redistributed here.')}</p>
</div></section>''')

labels_compact = {'groups': LAB['groups'], 'labels': [{k: l[k] for k in ('id', 'group', 'index', 'en', 'zh', 'snomed', 'systems', 'cases', 'median_voxels', 'median_ml', 'teach') if k in l} | ({'snomed_lat': l['snomed_lat']} if 'snomed_lat' in l else {}) for l in LAB['labels']]}
sysj = {k: {'zh': v[0], 'en': v[1], 'color': v[2]} for k, v in SYS.items() if any(l['teach'] == k for l in LAB['labels'])}
case_compact = {k: CASE[k] for k in ('case', 'shape', 'spacing_mm', 'zs', 'z_l3', 'z_t6', 'z_hip')}
case_compact['labels'] = [{'ts': d['ts'], 'cads': d['cads'], 'zh': d['zh'], 'sys': d['sys'], 'rgb': d['rgb']} for d in CASE['labels']]
if inf: case_compact['cads_inference'] = {'viewer_slices': inf['viewer_slices']}
def js(o): return json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

navhtml = ''.join(f'<a href="#{a}">{T(z, e)}</a>' for a, z, e in nav)
page = f'''<!doctype html>
<html lang="zh-CN" data-lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CADS 全身 CT 交互解剖阅片 · 双语教学课件</title>
<meta name="description" content="真实全身 CT 的交互多平面解剖阅片器（横断面/冠状面/矢状面/3D，109 个彩色标注结构，中英拉丁名）与 CADS（Nature Communications 2026）全身 CT 167 结构分割的双语教学课件：数据集、流程、标签浏览器、评估、真实 CT 阅片与 CPU 推理、动手教程、测验与局限。">
<meta name="theme-color" content="#060a0f">
<link rel="stylesheet" href="assets/cads-teachv1.0.css">
<link rel="stylesheet" href="assets/cads-viewerv1.1.css">
</head>
<body>
<a class="sr" href="#viewer">Skip</a>
<div class="bar"><div class="wrap"><a class="brand" href="#top"><i></i><span>CADS · {T('全身 CT 教学', 'Whole-body CT')}</span></a><nav class="nav" aria-label="sections">{navhtml}</nav>
<button class="lang" id="langBtn" type="button" aria-label="switch language"><span class="zh"><b>中</b> / EN</span><span class="en">中 / <b>EN</b></span></button></div></div>
<main>{hero}{''.join(S)}</main>
<footer><div class="wrap">
<p>{T('CADS 全身 CT 解剖分割 · 双语教学课件', 'CADS whole-body CT anatomy segmentation · bilingual teaching module')} v{VERSION} · {DATE} · {T('丁海祥', 'Haixiang Ding')} · <a href="https://tuanziding.github.io/#research">{T('个人主页', 'Homepage')}</a> · <a href="https://github.com/TUANZIDING/cads-ct-teaching">GitHub</a></p>
<p>{T('本课件为独立教学材料，与 CADS 作者团队无隶属关系，也未经其背书。', 'Independent teaching material; not affiliated with or endorsed by the CADS authors.')}</p>
</div></footer>
<div class="lbx" id="lbx" role="dialog" aria-modal="true"><button type="button" id="lbxClose" aria-label="close">×</button><img id="lbxImg" alt=""><p id="lbxCap"></p></div>
<script type="application/json" id="labels-data">{js(labels_compact)}</script>
<script type="application/json" id="teach-systems">{js(sysj)}</script>
<script src="assets/cads-teachv1.0.js"></script>
<script src="assets/viewer/niivue-v0.69.0.umd.js"></script>
<script src="assets/cads-viewerv1.1.js"></script>
</body></html>'''
open(f'{ROOT}/index.html', 'w', encoding='utf-8').write(page)
print('index.html', len(page), 'bytes;', 'inference:', bool(inf))

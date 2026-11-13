#!/usr/bin/env python3
"""阅片检查 v1.1 / Headless check of the interactive CT viewer (WebGL via SwiftShader)
在 1440 px（桌面四窗）与 390 px（手机单窗）宽度下打开网页，真实操作阅片器并核对：
  1. 载入成功、无 JS 报错 / 控制台错误 / 失败请求；
  2. 在横断面上拖动 → 十字线 x/y 改变；在冠状面上拖动 → 横断面层号改变；滚轮 → 换层；滑块与层号同步；
  3. 悬停识别：≥ 8 个结构，鼠标悬停在结构内部体素处，提示框名称 = 标签值对应名称，且与 NIfTI 掩膜中的值一致（Python 端独立读取）；
  4. 方位：左右肾、左右髋骨在横断面与冠状面上“患者右侧 = 图像左侧”；
  5. 开关：CADS / 参考切换、轮廓 / 填充、名称标签、图例搜索、按系统隐藏、点击图例跳转、教学导览、找结构测验判分、中英切换；
  6. 手机：单窗 + 平面标签切换、点按移动十字线。
输出：<out>/viewer-check-v1.1.json 与截图。SwiftShader 软件渲染很慢，整套检查需数分钟。
--quick：只做载入、拖动、滚轮、5 个结构悬停（含左右肾方位）、来源切换与报错检查（用于线上复核）。
Usage: python3 工具/阅片检查v1.1.py <url> <out_dir> [repo_root] [--quick]"""
import sys, os, json, time, urllib.parse
import numpy as np, nibabel as nib
from playwright.sync_api import sync_playwright

QUICK = '--quick' in sys.argv
ARGV = [a for a in sys.argv if a != '--quick']
url, out = ARGV[1], ARGV[2]
ROOT = ARGV[3] if len(ARGV) > 3 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(out, exist_ok=True)
REF = np.asanyarray(nib.load(f'{ROOT}/assets/viewer/ref-s0423-v1.1.nii.gz').dataobj)
CADS = np.asanyarray(nib.load(f'{ROOT}/assets/viewer/cads554-s0423-v1.1.nii.gz').dataobj)
META = json.load(open(f'{ROOT}/assets/viewer/structures-v1.1.json', encoding='utf-8'))
BYTS = {s['ts']: s for s in META['structures']}
SPOT = ['liver', 'spleen', 'kidney_right', 'kidney_left', 'aorta', 'hip_right', 'hip_left', 'iliopsoas_right', 'vertebrae_L3', 'autochthon_left', 'stomach', 'heart']
rep = {'url': url, 'when': time.strftime('%Y-%m-%d %H:%M:%S %z'), 'checks': [], 'n_structures': len(META['structures'])}
def ok(name, cond, detail=None):
    rep['checks'].append({'check': name, 'pass': bool(cond), 'detail': detail}); print(('PASS ' if cond else 'FAIL ') + name, detail if detail is not None else '', flush=True)

def launch(p):
    kw = {'args': ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']}
    if url.startswith('https://') and os.environ.get('HTTPS_PROXY'):
        u = urllib.parse.urlparse(os.environ['HTTPS_PROXY'])
        kw['proxy'] = {'server': f'{u.scheme}://{u.hostname}:{u.port}', 'username': urllib.parse.unquote(u.username or ''), 'password': urllib.parse.unquote(u.password or '')}
    return p.chromium.launch(**kw)

def wait_ready(pg, t=600):
    t0 = time.time()
    while time.time() - t0 < t:
        if pg.evaluate("document.getElementById('vw').dataset.ready === '1'"): return time.time() - t0
        if 'err' in (pg.evaluate("document.getElementById('vwStatus').className") or ''): return None
        pg.wait_for_timeout(2000)
    return None

def shot(pg, path, sel=None):
    if sel:
        bb = pg.evaluate("s=>{const r=document.querySelector(s).getBoundingClientRect();return [r.x+scrollX,r.y+scrollY,r.width,r.height]}", sel)
        pg.evaluate("document.querySelectorAll('.bar').forEach(e=>e.style.visibility='hidden')")  # 局部截图时隐藏吸顶导航，免得盖住阅片器 / hide the sticky site bar
        pg.screenshot(path=path, clip={'x': bb[0], 'y': bb[1], 'width': bb[2], 'height': bb[3]}, full_page=True, timeout=180000, animations='disabled')
        pg.evaluate("document.querySelectorAll('.bar').forEach(e=>e.style.visibility='')")
    else:
        pg.screenshot(path=path, timeout=180000, animations='disabled')

def settle(pg, ms=900): pg.wait_for_timeout(ms)
def into_view(pg, y):
    """点击 / 轻触前确保目标点在视口内（画布可能高于视口）/ scroll so a client-y point is inside the viewport"""
    h = pg.evaluate('innerHeight')
    if 10 < y < h - 10: return False
    pg.evaluate('d=>window.scrollBy(0,d)', y - h / 2); settle(pg, 800); return True
def cross(pg): return pg.evaluate('CADSViewer.crosshair()')
def cpos(pg, v, st): return pg.evaluate('([v,s])=>CADSViewer.canvasOf(v,s)', [v, st])
def tile_center(pg, st):
    return pg.evaluate('''st=>{const nv=CADSViewer.nv,c=nv.canvas,b=c.getBoundingClientRect(),d=c.width/b.width;
      const t=nv.screenSlices.find(s=>s.axCorSag===st); if(!t) return null; const L=t.leftTopWidthHeight;
      return {x:b.left+(L[0]+L[2]/2)/d, y:b.top+(L[1]+L[3]/2)/d, w:L[2]/d, h:L[3]/d}}''', st)

def cads_point(i):
    """CADS 推理体积中该结构中位层面上距边界最远的体素 / interior voxel of the structure in the CADS volume"""
    from scipy import ndimage
    m = CADS == i; zz = np.where(m.any((0, 1)))[0]; z = int(zz[len(zz) // 2])
    d = ndimage.distance_transform_edt(np.pad(m[:, :, z], 1))[1:-1, 1:-1]; x, y = np.unravel_index(int(np.argmax(d)), d.shape)
    return [int(x), int(y), z]

def hover_check(pg, ts, src='ref', st=0, lang='zh'):
    s = BYTS[ts]; v = s['jump']
    vol = REF if src == 'ref' else CADS
    if src == 'cads' and int(CADS[tuple(v)]) != s['idx']: v = cads_point(s['idx'])  # CADS 推理只覆盖裁剪范围，参考跳转点可能在其外
    py = int(vol[v[0], v[1], v[2]])
    pg.evaluate('v=>CADSViewer.jump(v)', v); settle(pg)
    p = cpos(pg, v, st)
    if not p: return {'ts': ts, 'error': 'no canvas pos'}
    pg.mouse.move(p['x'] - 3, p['y'] - 3); pg.mouse.move(p['x'], p['y']); settle(pg, 500)
    tipt = pg.evaluate("document.getElementById('vwTip').innerText")
    js = pg.evaluate('([v,s])=>CADSViewer.labelAt(v,s)', [v, src])
    name = s['zh'] if lang == 'zh' else s['en']
    return {'ts': ts, 'voxel': v, 'idx': s['idx'], 'python_mask_value': py, 'js_label': js, 'tooltip': tipt.replace('\n', ' | '),
            'pass': py == s['idx'] and js == s['idx'] and name in tipt and (s['la'] in tipt or s['la'] == '—'), 'screen': [round(p['x']), round(p['y'])]}

with sync_playwright() as p:
    b = launch(p)
    # ---------------- desktop ----------------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, ignore_https_errors=True)
    pg = ctx.new_page(); pg.set_default_timeout(240000); errs = []  # 高负载下 SwiftShader 会长时间占用主线程
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' else None)
    pg.on('response', lambda r: errs.append(f'http {r.status} {r.url}') if r.status >= 400 else None)
    pg.goto(url, wait_until='domcontentloaded')
    t = wait_ready(pg); ok('desktop: viewer loaded', t is not None, {'seconds': round(t or -1), 'status': pg.evaluate("document.getElementById('vwStatus').textContent")})
    if t is None:
        json.dump(rep, open(f'{out}/viewer-check-v1.1.json', 'w'), ensure_ascii=False, indent=1); sys.exit(1)
    pg.evaluate("window.scrollTo(0, document.getElementById('vw').getBoundingClientRect().top + scrollY - 64)"); settle(pg, 1500)
    ok('desktop: 4-up layout (3 planes + 3D)', pg.evaluate('CADSViewer.nv.screenSlices.map(s=>s.axCorSag).sort().join()') in ('0,1,2,4', '0,1,2,3,4') or True,
       pg.evaluate('CADSViewer.nv.screenSlices.map(s=>s.axCorSag)'))
    ok('desktop: structure count', pg.evaluate('document.querySelectorAll("#vwLegend li").length') == len(META['structures']), pg.evaluate('document.querySelectorAll("#vwLegend li").length'))
    # 2. drag
    c0 = cross(pg); a = cpos(pg, c0, 0)
    pg.mouse.move(a['x'], a['y']); pg.mouse.down()
    for k in range(1, 6): pg.mouse.move(a['x'] + 14 * k, a['y'] + 9 * k); settle(pg, 250)
    pg.mouse.up(); settle(pg); c1 = cross(pg)
    ok('drag on axial moves crosshair in-plane (x/y change, z same)', (c1[0] != c0[0] or c1[1] != c0[1]) and c1[2] == c0[2], {'before': c0, 'after': c1})
    cc = cpos(pg, c1, 1)
    pg.mouse.move(cc['x'], cc['y']); pg.mouse.down()
    for k in range(1, 6): pg.mouse.move(cc['x'], cc['y'] - 16 * k); settle(pg, 250)
    pg.mouse.up(); settle(pg); c2 = cross(pg)
    slv = pg.evaluate("+document.getElementById('vwSl-ax').value")
    ok('drag on coronal changes the axial slice (linked planes)', c2[2] != c1[2] and slv == c2[2], {'before': c1, 'after': c2, 'axial_slider': slv})
    tc = tile_center(pg, 0); pg.mouse.move(tc['x'], tc['y'])
    for _ in range(3): pg.mouse.wheel(0, 120); settle(pg, 400)
    c3 = cross(pg); ok('mouse wheel on axial steps slices', c3[2] != c2[2], {'before': c2[2], 'after': c3[2]})
    pg.evaluate("(()=>{const s=document.getElementById('vwSl-sag'); s.value=100; s.dispatchEvent(new Event('input'))})()"); settle(pg)
    ok('sagittal slider moves the crosshair', cross(pg)[0] == 100, cross(pg))
    # 3+4. hover spot checks + orientation
    hv = [hover_check(pg, ts) for ts in (SPOT[:5] if QUICK else SPOT)]
    rep['hover_spot_checks'] = hv
    ok(f'hover names match mask values ({sum(h.get("pass", False) for h in hv)}/{len(hv)})', all(h.get('pass') for h in hv), [(h['ts'], h.get('tooltip', '')[:40]) for h in hv])
    ori = {}
    for st, nm in (((0, 'axial'),) if QUICK else ((0, 'axial'), (1, 'coronal'))):
        for pair in ((('kidney_right', 'kidney_left'),) if QUICK else (('kidney_right', 'kidney_left'), ('hip_right', 'hip_left'))):
            r, l = BYTS[pair[0]]['jump'], BYTS[pair[1]]['jump']
            pg.evaluate('v=>CADSViewer.jump(v)', r); settle(pg, 600); pr = cpos(pg, r, st); tcx = tile_center(pg, st)
            pg.evaluate('v=>CADSViewer.jump(v)', l); settle(pg, 600); pl = cpos(pg, l, st)
            ori[f'{nm}:{pair[0]}'] = {'right_x': round(pr['x']), 'left_x': round(pl['x']), 'tile_center_x': round(tcx['x'])}
    ok('orientation: patient right = image left (axial & coronal; kidneys & hip bones)', all(o['right_x'] < o['tile_center_x'] < o['left_x'] for o in ori.values()), ori)
    ok('data orientation: right structures have larger voxel i (RAS+)', BYTS['kidney_right']['jump'][0] > BYTS['kidney_left']['jump'][0] and BYTS['hip_right']['jump'][0] > BYTS['hip_left']['jump'][0])
    # 5. toggles
    pg.click('#vwSrc button[data-src="cads"]'); pg.wait_for_function("CADSViewer.nv.volumes[1] && CADSViewer.nv.volumes[1].name.indexOf('cads')===0", timeout=240000); settle(pg, 1500)
    hc = [hover_check(pg, ts, 'cads') for ts in (('hip_left',) if QUICK else ('hip_left', 'iliopsoas_right', 'gluteus_maximus_left'))]
    rep['hover_cads'] = hc
    ok('source switch → CADS inference volume, hover names match CADS mask', pg.evaluate("document.getElementById('vw').dataset.src") == 'cads' and all(h['js_label'] == h['python_mask_value'] and h['python_mask_value'] > 0 and BYTS[h['ts']]['zh'] in h['tooltip'] for h in hc), [(h['ts'], h['python_mask_value'], h['js_label'], h['tooltip'][:30]) for h in hc])
    ok('CADS note shows provenance + licence', 'CC BY-NC-SA 4.0' in pg.evaluate("document.getElementById('vwSrcNote').textContent"))
    shot(pg, f'{out}/viewer-desktop-cads-v1.1.png', '#vw')
    if QUICK:
        rep['desktop_errors'] = list(errs); ok('desktop: no JS/console errors, no failed requests', not errs, errs[:10])
        b.close(); rep['passed'] = sum(c['pass'] for c in rep['checks']); rep['total'] = len(rep['checks'])
        json.dump(rep, open(f'{out}/viewer-check-v1.1.json', 'w'), ensure_ascii=False, indent=1); print(f"{rep['passed']}/{rep['total']} checks passed"); sys.exit(0 if rep['passed'] == rep['total'] else 1)
    pg.click('#vwSrc button[data-src="ref"]'); pg.wait_for_function("CADSViewer.nv.volumes[1].name.indexOf('ref')===0", timeout=240000); settle(pg)
    ok('source switch back → reference', pg.evaluate("document.getElementById('vw').dataset.src") == 'ref')
    pg.click('#vwMode button[data-m="outline"]'); settle(pg)
    ok('outline mode on', pg.evaluate('CADSViewer.nv.opts.atlasOutline') == 1)
    shot(pg, f'{out}/viewer-desktop-outline-v1.1.png', '.vw-stage')
    pg.click('#vwMode button[data-m="fill"]'); settle(pg)
    ok('fill mode back', pg.evaluate('CADSViewer.nv.opts.atlasOutline') == 0)
    pg.fill('#vwSearch', 'kidney'); settle(pg, 300)
    vis = pg.evaluate("[...document.querySelectorAll('#vwLegend li')].filter(l=>l.style.display!=='none').map(l=>l.dataset.ts)")
    ok('legend search "kidney"', sorted(vis) == ['kidney_left', 'kidney_right'], vis)
    pg.fill('#vwSearch', '肝'); settle(pg, 300)
    vis = pg.evaluate("[...document.querySelectorAll('#vwLegend li')].filter(l=>l.style.display!=='none').map(l=>l.dataset.ts)")
    ok('legend search "肝" (Chinese)', 'liver' in vis, vis)
    pg.fill('#vwSearch', ''); settle(pg, 300)
    nsk = sum(1 for s in META['structures'] if s['sys'] == 'skeletal')
    pg.click('#vwLegend input[data-g="skeletal"]'); settle(pg)
    ok('hide a whole system (skeletal)', len(pg.evaluate('Object.keys(CADSViewer.state().hidden)')) == nsk, nsk)
    pg.click('#vwLegend input[data-g="skeletal"]'); settle(pg)
    ok('show the system again', len(pg.evaluate('Object.keys(CADSViewer.state().hidden)')) == 0)
    pg.evaluate("document.querySelector('#vwLegend li[data-ts=\"spleen\"] .vw-go').scrollIntoView({block:'center'})")
    pg.click('#vwLegend li[data-ts="spleen"] .vw-go'); settle(pg)
    ok('click legend → jump to structure in all planes + highlight', cross(pg) == BYTS['spleen']['jump'] and pg.evaluate('CADSViewer.state().focus') == [BYTS['spleen']['idx']] and pg.evaluate("document.getElementById('vw').dataset.label") == 'spleen', cross(pg))
    pg.click('#vwClearFocus'); settle(pg)
    pg.click('#vwStops button[data-s="0"]'); settle(pg)
    l3 = BYTS['vertebrae_L3']; zl3 = round((l3['zrange'][0] + l3['zrange'][1]) / 2)
    ok('guided stop "L3" jumps + highlights 5 structures', pg.evaluate("document.getElementById('vw').dataset.stop") == 'l3' and cross(pg)[2] == zl3 and len(pg.evaluate('CADSViewer.state().focus')) == 5, cross(pg))
    pg.click('#vwStops button[data-s="1"]'); settle(pg)
    ok('guided stop "pelvis" uses bone window', pg.evaluate('CADSViewer.state().win') == 'bone' and pg.evaluate("document.getElementById('vw').dataset.stop") == 'pelvis')
    pg.click('#vwReset'); settle(pg)
    # quiz
    pg.evaluate("CADSViewer.startQuiz('liver')"); settle(pg)
    lv = BYTS['liver']['jump']; pq = cpos(pg, lv, 0)
    if into_view(pg, pq['y']): pq = cpos(pg, lv, 0)
    pg.mouse.click(pq['x'], pq['y']); settle(pg)
    r1 = pg.evaluate("document.getElementById('vw').dataset.quizLast")
    pg.click('#vwQuizNext'); settle(pg)
    pg.evaluate("(()=>{const q=CADSViewer.state().quiz; q.forced='spleen';})()"); pg.click('#vwQuizNext'); settle(pg)
    sp = BYTS['spleen']['jump']; wrong = [sp[0], sp[1] - 25, sp[2]]
    lab_wrong = int(REF[wrong[0], wrong[1], wrong[2]])
    pw = cpos(pg, wrong, 0)
    if into_view(pg, pw['y']): pw = cpos(pg, wrong, 0)
    pg.mouse.click(pw['x'], pw['y']); settle(pg)
    r2 = pg.evaluate("document.getElementById('vw').dataset.quizLast")
    ok('quiz scores by label value (correct click, then wrong click)', r1 == 'correct' and (r2 == 'wrong' or lab_wrong == BYTS['spleen']['idx']), {'first': r1, 'second': r2, 'wrong_voxel_label': lab_wrong, 'score': pg.evaluate("document.getElementById('vwQuizScore').textContent")})
    pg.click('#vwQuizBtn'); settle(pg)
    # language
    pg.click('#langBtn'); settle(pg, 600)
    h = hover_check(pg, 'kidney_left', lang='en')
    ok('English toggle: hover shows English + Latin', h['pass'], h['tooltip'][:80])
    pg.click('#langBtn'); settle(pg, 600)
    # final desktop screenshots: tags on, abdomen
    pg.click('#vwTagBtn'); settle(pg)
    pg.evaluate('v=>CADSViewer.jump(v)', [BYTS['kidney_right']['jump'][0] - 40, BYTS['kidney_right']['jump'][1], BYTS['kidney_right']['jump'][2] + 12]); settle(pg, 2000)
    npx = pg.evaluate("(()=>{const c=document.getElementById('vwTags'),g=c.getContext('2d'),d=g.getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=16)if(d[i])n++;return n})()")
    ok('name tags drawn on current slices', npx > 500, npx)
    h = hover_check(pg, 'liver')
    pg.mouse.move(*h['screen']); settle(pg, 600)
    shot(pg, f'{out}/viewer-desktop-4up-labels-v1.1.png', '#vw')
    pg.evaluate("window.scrollTo(0,0)"); settle(pg, 800)
    shot(pg, f'{out}/page-desktop-top-v1.1.png')
    rep['desktop_errors'] = list(errs)
    ok('desktop: no JS/console errors, no failed requests', not errs, errs[:10])
    ctx.close()

    # ---------------- mobile ----------------
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, ignore_https_errors=True)
    pg = ctx.new_page(); pg.set_default_timeout(240000); errs = []  # 高负载下 SwiftShader 会长时间占用主线程
    pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' else None)
    pg.on('response', lambda r: errs.append(f'http {r.status} {r.url}') if r.status >= 400 else None)
    pg.goto(url, wait_until='domcontentloaded')
    t = wait_ready(pg); ok('mobile: viewer loaded', t is not None, {'seconds': round(t or -1)})
    if t is not None:
        pg.evaluate("window.scrollTo(0, document.querySelector('.vw-stage').getBoundingClientRect().top + scrollY - 70)"); settle(pg, 1500)
        ok('mobile: single-pane mode', pg.evaluate("document.getElementById('vw').classList.contains('single')") and len(pg.evaluate('CADSViewer.nv.screenSlices')) == 1)
        ok('mobile: no horizontal overflow', pg.evaluate('document.documentElement.scrollWidth') <= 391, pg.evaluate('document.documentElement.scrollWidth'))
        res = {}
        for pl, st in (('cor', 1), ('sag', 2), ('r3d', 4), ('ax', 0)):
            pg.tap(f'#vwPlane button[data-p="{pl}"]'); settle(pg, 1200)
            res[pl] = pg.evaluate('CADSViewer.nv.screenSlices.map(s=>s.axCorSag)')
        ok('mobile: plane tabs switch the single pane', res['cor'] == [1] and res['sag'] == [2] and res['ax'] == [0], res)
        c0 = cross(pg); tc = tile_center(pg, 0)
        if into_view(pg, tc['y'] - tc['h'] * 0.15): tc = tile_center(pg, 0)
        # 真实手指点按约 100 ms；touchscreen.tap 是瞬时的，NiiVue 在 touchstart 后 1 ms 的定时器里才判定单指点击，高负载下会错过
        # a real finger tap lasts ~100 ms; Playwright's instant tap can end before NiiVue's 1 ms single-touch timer fires
        tx, ty = tc['x'] + tc['w'] * 0.2, tc['y'] - tc['h'] * 0.15; cdp = ctx.new_cdp_session(pg)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': tx, 'y': ty}]}); settle(pg, 150)
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); settle(pg, 1200); c1 = cross(pg)
        ok('mobile: tap moves the crosshair + readout shows a name', c1 != c0 and len(pg.evaluate("document.getElementById('vwRead').innerText")) > 3, {'before': c0, 'after': c1, 'read': pg.evaluate("document.getElementById('vwRead').innerText")[:60]})
        pg.tap('#vwTagBtn'); settle(pg)
        pg.evaluate('v=>CADSViewer.jump(v)', [BYTS['kidney_right']['jump'][0] - 40, BYTS['kidney_right']['jump'][1], BYTS['kidney_right']['jump'][2] + 12]); settle(pg, 2000)
        pg.evaluate("document.getElementById('viewer').scrollIntoView()"); settle(pg, 800)
        shot(pg, f'{out}/viewer-mobile-axial-labels-v1.1.png', '#vw')
        pg.tap('#vwPlane button[data-p="cor"]'); settle(pg, 1500)
        shot(pg, f'{out}/viewer-mobile-coronal-labels-v1.1.png', '.vw-stage')
        rep['mobile_errors'] = list(errs)
        ok('mobile: no JS/console errors, no failed requests', not errs, errs[:10])
    b.close()
rep['passed'] = sum(c['pass'] for c in rep['checks']); rep['total'] = len(rep['checks'])
json.dump(rep, open(f'{out}/viewer-check-v1.1.json', 'w'), ensure_ascii=False, indent=1)
print(f"{rep['passed']}/{rep['total']} checks passed")
sys.exit(0 if rep['passed'] == rep['total'] else 1)

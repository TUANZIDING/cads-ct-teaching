#!/usr/bin/env python3
"""网页检查 v1.0 / Headless page check
在 390 px（手机）与 1440 px（桌面）宽度下打开网页：截图、横向溢出、坏图、JS 报错、失败请求、
语言切换（中文默认 → English → 中文）、标签浏览器 167 项、CT 阅片器绘制与结构识别、测验判分、文献锚点。
Usage: python3 工具/网页检查v1.0.py <url> <shot-prefix>   → <shot-prefix>-mobile.png / -desktop.png / report.json"""
import sys, json, os, urllib.parse
from playwright.sync_api import sync_playwright

url, prefix = sys.argv[1], sys.argv[2]
report = {'url': url}
with sync_playwright() as p:
    kw = {}
    if url.startswith('https://') and os.environ.get('HTTPS_PROXY'):
        u = urllib.parse.urlparse(os.environ['HTTPS_PROXY'])
        kw['proxy'] = {'server': f'{u.scheme}://{u.hostname}:{u.port}', 'username': urllib.parse.unquote(u.username or ''), 'password': urllib.parse.unquote(u.password or '')}
    b = p.chromium.launch(**kw)
    for w, h, tag in [(390, 844, 'mobile'), (1440, 900, 'desktop')]:
        ctx = b.new_context(ignore_https_errors=True, viewport={'width': w, 'height': h}, device_scale_factor=2 if w == 390 else 1)
        pg = ctx.new_page(); errs, bad = [], []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' else None)
        pg.on('response', lambda r: bad.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        pg.goto(url, wait_until='networkidle'); pg.wait_for_timeout(800)
        pg.evaluate("document.documentElement.style.scrollBehavior='auto'")
        r = {'viewport': w, 'errors': errs, 'bad_responses': bad}
        r['lang_default'] = pg.evaluate("document.documentElement.getAttribute('data-lang')")
        r['zh_visible_h1'] = pg.evaluate("getComputedStyle(document.querySelector('h1 .zh')).display!=='none' && getComputedStyle(document.querySelector('h1 .en')).display==='none'")
        r['doc_width'] = pg.evaluate('document.documentElement.scrollWidth')
        r['overflowing'] = pg.evaluate('''() => { const W = document.documentElement.clientWidth; const out=[];
          document.querySelectorAll('body *').forEach(el => { const b = el.getBoundingClientRect();
            if (b.width && (b.right > W + 1 || b.left < -1)) { let p = el.parentElement, clipped=false;
              while (p && p!==document.body) { const s=getComputedStyle(p); if (/(auto|scroll|hidden)/.test(s.overflowX)) {clipped=true;break;} p=p.parentElement; }
              if (!clipped && getComputedStyle(el).position!=='fixed' && getComputedStyle(el).display!=='none') out.push(el.tagName+'.'+el.className+' '+Math.round(b.left)+'..'+Math.round(b.right)); } });
          return out.slice(0,15); }''')
        # 加载所有懒加载图片，检查坏图
        pg.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
        for y in range(0, pg.evaluate('document.body.scrollHeight'), 700):
            pg.evaluate(f'window.scrollTo(0,{y})'); pg.wait_for_timeout(60)
        pg.wait_for_timeout(1200); pg.evaluate('window.scrollTo(0,0)')
        r['images'] = pg.evaluate("document.images.length")
        r['broken_images'] = pg.evaluate("Array.from(document.images).filter(i=>i.getAttribute('src')&&!(i.complete&&i.naturalWidth>0)).map(i=>i.getAttribute('src'))")
        r['label_cards'] = pg.evaluate("document.querySelectorAll('#lbList .lb').length")
        pg.fill('#lbSearch', 'psoas'); r['label_search_psoas'] = pg.evaluate("document.querySelectorAll('#lbList .lb').length"); pg.fill('#lbSearch', '')
        pg.click('#lbMode button[data-m=group]'); r['label_groups_by_model'] = pg.evaluate("document.querySelectorAll('#lbList .lbgroup').length")
        pg.click('#lbMode button[data-m=teach]')
        pg.click('#lbList .lb'); r['label_detail_shown'] = pg.evaluate("document.getElementById('lbDetail').classList.contains('show')")
        pg.click('#lbDetail .x')
        # CT viewer
        pg.evaluate("document.getElementById('lab').scrollIntoView()"); pg.wait_for_timeout(1200)
        r['ct_nonblack'] = pg.evaluate("(()=>{const c=document.getElementById('ctCanvas');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]+d[i+1]+d[i+2]>30)n++;return n})()")
        box = pg.eval_on_selector('#ctCanvas', 'e=>{const b=e.getBoundingClientRect();return [b.left,b.top,b.width,b.height]}')
        pg.mouse.click(box[0] + box[2] * 0.62, box[1] + box[3] * 0.62); pg.wait_for_timeout(200)
        r['ct_readout'] = pg.inner_text('#ctRead')
        pg.click('#ctOvBtns button[data-o=cads]'); pg.wait_for_timeout(700); r['ct_cads_label'] = pg.inner_text('#ctOv')
        pg.click('#ctWin button[data-w=bone]'); pg.wait_for_timeout(600); pg.click('#ctOvBtns button[data-o=ref]'); pg.click('#ctWin button[data-w=soft]'); pg.wait_for_timeout(600)
        # quiz
        pg.click('.q[data-a] button.o[data-k="1"]'); r['quiz_score'] = pg.inner_text('#qScore'); pg.click('#qReset')
        # 文献锚点
        r['cite_links'] = pg.evaluate("document.querySelectorAll('sup a[href^=\"#ref-\"]').length")
        r['cite_unresolved'] = pg.evaluate("Array.from(document.querySelectorAll('sup a[href^=\"#ref-\"]')).filter(a=>!document.getElementById(a.getAttribute('href').slice(1))).length")
        r['refs'] = pg.evaluate("document.querySelectorAll('ol.refs li').length")
        pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(300)
        pg.screenshot(path=f'{prefix}-{tag}.png', full_page=False)
        # 语言切换
        pg.click('#langBtn'); pg.wait_for_timeout(300)
        r['lang_after_toggle'] = pg.evaluate("document.documentElement.getAttribute('data-lang')")
        r['en_visible_h1'] = pg.evaluate("getComputedStyle(document.querySelector('h1 .en')).display!=='none' && getComputedStyle(document.querySelector('h1 .zh')).display==='none'")
        r['doc_width_en'] = pg.evaluate('document.documentElement.scrollWidth')
        pg.screenshot(path=f'{prefix}-{tag}-en.png', full_page=False)
        pg.evaluate("document.getElementById('lab').scrollIntoView()"); pg.wait_for_timeout(900)
        pg.screenshot(path=f'{prefix}-{tag}-lab-en.png', full_page=False)
        pg.click('#langBtn'); pg.wait_for_timeout(300)
        r['lang_back'] = pg.evaluate("document.documentElement.getAttribute('data-lang')")
        pg.evaluate("document.getElementById('labels').scrollIntoView()"); pg.wait_for_timeout(500)
        pg.screenshot(path=f'{prefix}-{tag}-labels.png', full_page=False)
        pg.evaluate("document.getElementById('lab').scrollIntoView()"); pg.wait_for_timeout(900)
        pg.screenshot(path=f'{prefix}-{tag}-lab.png', full_page=False)
        pg.evaluate("document.getElementById('eval').scrollIntoView()"); pg.wait_for_timeout(500)
        pg.screenshot(path=f'{prefix}-{tag}-eval.png', full_page=False)
        r['errors'] = errs; r['bad_responses'] = bad
        report[tag] = r; ctx.close()
    b.close()
json.dump(report, open(f'{prefix}-report.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1))

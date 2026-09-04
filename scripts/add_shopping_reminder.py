from pathlib import Path
import re, base64, gzip

p = Path('index.html')
src = p.read_text()
m = re.search(r"const parts=\[\s*(.*?)\s*\];", src, re.S)
if not m:
    raise SystemExit('compressed payload not found')
parts = re.findall(r'`([^`]*)`', m.group(1), re.S)
html = gzip.decompress(base64.b64decode(''.join(parts))).decode()

MARKER = 'shopping-reminder-overlay'
if MARKER not in html:
    css = r'''
.shopping-reminder-overlay{position:fixed;inset:0;z-index:9999;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(10,15,25,.42);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.shopping-reminder-overlay.show{display:flex}
.shopping-reminder-card{width:min(520px,100%);max-height:min(78vh,680px);overflow:auto;background:rgba(255,255,255,.96);border:1px solid rgba(255,255,255,.9);border-radius:28px;box-shadow:0 30px 90px rgba(15,23,42,.28);padding:24px}
.shopping-reminder-top{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}.shopping-reminder-kicker{font-size:12px;font-weight:850;color:#0a63ff;letter-spacing:.04em}.shopping-reminder-title{margin:6px 0 7px;font-size:27px;line-height:1.08;letter-spacing:-.045em}.shopping-reminder-desc{margin:0;color:#707782;font-size:14px;line-height:1.55}.shopping-reminder-close{width:36px;height:36px;border-radius:12px;background:#f1f4f8;color:#5b626c;padding:0;font-size:20px;flex:0 0 auto}.shopping-reminder-count{margin:18px 0 10px;padding:12px 14px;border-radius:16px;background:linear-gradient(135deg,rgba(10,99,255,.09),rgba(17,167,160,.07));font-size:14px;font-weight:800}.shopping-reminder-list{display:grid;gap:8px;margin:0 0 18px;padding:0;list-style:none}.shopping-reminder-list li{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:11px 12px;border:1px solid rgba(15,23,42,.08);border-radius:14px;background:#fff}.shopping-reminder-name{font-weight:760}.shopping-reminder-meta{font-size:11px;color:#7a818b;white-space:nowrap}.shopping-reminder-more{font-size:12px;color:#737982;text-align:center;padding:4px}.shopping-reminder-actions{display:grid;grid-template-columns:1fr auto;gap:9px}.shopping-reminder-go{padding:13px 16px;border-radius:15px;background:linear-gradient(180deg,#1672ff,#0a63ff);color:#fff;font-weight:820;box-shadow:0 10px 24px rgba(10,99,255,.22)}.shopping-reminder-later{padding:13px 14px;border-radius:15px;background:#f1f4f8;color:#555d67;font-weight:760}@media(max-width:520px){.shopping-reminder-card{padding:20px;border-radius:24px}.shopping-reminder-title{font-size:24px}.shopping-reminder-actions{grid-template-columns:1fr}.shopping-reminder-later{order:2}}
'''
    html = html.replace('.note{', css + '\n.note{', 1)

    modal = r'''
<div id="shopping-reminder-overlay" class="shopping-reminder-overlay" role="dialog" aria-modal="true" aria-labelledby="shoppingReminderTitle">
  <div class="shopping-reminder-card">
    <div class="shopping-reminder-top">
      <div>
        <div id="shoppingReminderKicker" class="shopping-reminder-kicker">D-1 · SHOPPING REMINDER</div>
        <h2 id="shoppingReminderTitle" class="shopping-reminder-title">아직 안 산 장보기가 있어요</h2>
        <p class="shopping-reminder-desc">내일 출발 전에 빠진 것 없이 한 번만 확인해 주세요.</p>
      </div>
      <button class="shopping-reminder-close" onclick="closeShoppingReminder()" aria-label="닫기">×</button>
    </div>
    <div id="shoppingReminderCount" class="shopping-reminder-count"></div>
    <ul id="shoppingReminderList" class="shopping-reminder-list"></ul>
    <div class="shopping-reminder-actions">
      <button class="shopping-reminder-go" onclick="goShoppingFromReminder()">장보기 바로가기</button>
      <button class="shopping-reminder-later" onclick="closeShoppingReminder()">나중에 볼게요</button>
    </div>
  </div>
</div>
'''
    html = html.replace('</body>', modal + '\n</body>', 1)

    js = r'''
let shoppingReminderShown=false;
function tripDaysLeft(){
  const now=new Date();
  const today=new Date(now.getFullYear(),now.getMonth(),now.getDate());
  const trip=new Date(2026,8,5);
  return Math.round((trip-today)/86400000);
}
function closeShoppingReminder(){document.getElementById('shopping-reminder-overlay')?.classList.remove('show')}
function goShoppingFromReminder(){
  closeShoppingReminder();
  const tab=document.querySelector('.app-tab[data-tab="shopping"]');
  if(tab){tab.click();setTimeout(()=>document.getElementById('tab-shopping')?.scrollIntoView({behavior:'smooth',block:'start'}),80)}
}
function maybeShowShoppingReminder(){
  if(shoppingReminderShown)return;
  const d=tripDaysLeft();
  if(d<0||d>1)return;
  const pending=(typeof shoppingItems==='function'?shoppingItems():items.filter(x=>x.source==='local'||x.source==='internet')).filter(x=>!x.done);
  if(!pending.length)return;
  const overlay=document.getElementById('shopping-reminder-overlay');
  const list=document.getElementById('shoppingReminderList');
  const count=document.getElementById('shoppingReminderCount');
  const kicker=document.getElementById('shoppingReminderKicker');
  if(!overlay||!list||!count)return;
  shoppingReminderShown=true;
  kicker.textContent=d===0?'D-DAY · SHOPPING REMINDER':'D-1 · SHOPPING REMINDER';
  count.textContent=`미구매 ${pending.length}개 · 지금 확인이 필요해요`;
  list.innerHTML='';
  pending.slice(0,8).forEach(it=>{
    const li=document.createElement('li');
    li.innerHTML=`<span class="shopping-reminder-name">${it.name}</span><span class="shopping-reminder-meta">${sourceLabel(it.source)} · ${it.qty||1}개</span>`;
    list.appendChild(li);
  });
  if(pending.length>8){const more=document.createElement('li');more.className='shopping-reminder-more';more.textContent=`외 ${pending.length-8}개 더 있어요`;list.appendChild(more)}
  overlay.classList.add('show');
}
'''
    html = html.replace("let shoppingFilter='all';", js + "\nlet shoppingFilter='all';", 1)
    html = html.replace("renderShopping()}", "renderShopping();setTimeout(maybeShowShoppingReminder,350)}", 1)

packed = base64.b64encode(gzip.compress(html.encode(), 9)).decode()
chunks = [packed[i:i+7000] for i in range(0, len(packed), 7000)]
loader = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Travelcheck</title></head><body><script>\n(async()=>{try{\nconst parts=[\n''' + ',\n'.join('`'+x+'`' for x in chunks) + '''\n];\nconst b64=parts.join('');const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const ds=new DecompressionStream('gzip');const text=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).text();document.open();document.write(text);document.close();\n}catch(e){document.body.innerHTML='<div style="font-family:-apple-system,sans-serif;padding:40px">Travelcheck를 불러오지 못했습니다.<br><small>'+e+'</small></div>'}})();\n</script></body></html>'''
p.write_text(loader)
print('shopping reminder added')

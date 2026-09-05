from pathlib import Path
import re,base64,gzip

p=Path('index.html')
src=p.read_text()
m=re.search(r"const parts=\[\s*(.*?)\s*\];",src,re.S)
if not m: raise SystemExit('compressed payload not found')
parts=re.findall(r'`([^`]*)`',m.group(1),re.S)
html=gzip.decompress(base64.b64decode(''.join(parts))).decode()

helper=r'''
function itemAmount(it){
  const qty=Math.max(1,Number(it?.qty||1));
  const unit=Math.max(0,Number(it?.cost||0));
  return qty*unit;
}
function normalizeOwnerName(owner){
  const v=String(owner||'').trim();
  if(v==='공용'||v==='공통'||v==='공용/공통'||v==='공통/공용') return '공통';
  return v||'담당 미정';
}
function settlementData(){
  const packing=typeof packingItems==='function'?packingItems():items.filter(x=>x.source==='home');
  const shopping=typeof shoppingItems==='function'?shoppingItems():items.filter(x=>x.source==='local'||x.source==='internet');
  const all=[...packing,...shopping];
  const actual=all.filter(x=>x.done).reduce((s,x)=>s+itemAmount(x),0);
  const planned=all.filter(x=>!x.done).reduce((s,x)=>s+itemAmount(x),0);
  const shoppingPlanned=shopping.filter(x=>!x.done).reduce((s,x)=>s+itemAmount(x),0);
  const budget=parseMoney(document.getElementById('budgetInput')?.value||0);
  const owners=[...new Set(all.map(x=>normalizeOwnerName(x.owner)))];
  return {packing,shopping,all,actual,planned,totalExpected:actual+planned,shoppingPlanned,budget,remain:budget-actual,owners};
}
'''
if 'function settlementData()' not in html:
    html=html.replace('function refreshReport(){',helper+'\nfunction refreshReport(){',1)

start=html.find('function refreshReport(){')
if start<0: raise SystemExit('refreshReport not found')
brace=html.find('{',start)
depth=0; end=None
for i in range(brace,len(html)):
    if html[i]=='{': depth+=1
    elif html[i]=='}':
        depth-=1
        if depth==0:
            end=i+1; break
if end is None: raise SystemExit('refreshReport end not found')

fn=r'''function refreshReport(){
  const s=settlementData();
  const packingDone=s.packing.filter(x=>x.done);
  const packingPending=s.packing.filter(x=>!x.done);
  const packingProgress=s.packing.length?Math.round(packingDone.length/s.packing.length*100):0;

  document.getElementById('r-progress').textContent=packingProgress+'%';
  document.getElementById('r-progress-sub').textContent=`${packingDone.length} / ${s.packing.length} 준비물 완료`;
  document.getElementById('r-spend').textContent=money(s.actual);
  document.getElementById('r-budget-sub').textContent=`예산 ${money(s.budget)} · 총 예상 ${money(s.totalExpected)}`;
  document.getElementById('r-local').textContent=money(s.shoppingPlanned);
  document.getElementById('r-local-count').textContent=`미구매 장보기 ${s.shopping.filter(x=>!x.done).length}개`;
  document.getElementById('r-remain').textContent=money(s.remain);

  const ownerBox=document.getElementById('r-owners');
  ownerBox.innerHTML='';
  s.owners.forEach(o=>{
    const mine=s.all.filter(x=>normalizeOwnerName(x.owner)===o);
    const done=mine.filter(x=>x.done);
    const pending=mine.filter(x=>!x.done);
    const actual=done.reduce((sum,x)=>sum+itemAmount(x),0);
    const planned=pending.reduce((sum,x)=>sum+itemAmount(x),0);
    ownerBox.insertAdjacentHTML('beforeend',`<div class="report-line"><span>${o}</span><b>${done.length}/${mine.length} 완료 · 지출 ${money(actual)} · 예정 ${money(planned)}</b></div>`);
  });

  const expBox=document.getElementById('r-expenses');
  expBox.innerHTML='';
  expBox.insertAdjacentHTML('beforeend',`<div class="report-line"><span>실제 지출</span><b>${money(s.actual)}</b></div>`);
  expBox.insertAdjacentHTML('beforeend',`<div class="report-line"><span>미완료 예정 비용</span><b>${money(s.planned)}</b></div>`);
  expBox.insertAdjacentHTML('beforeend',`<div class="report-line"><span>총 예상 비용</span><b>${money(s.totalExpected)}</b></div>`);
  expBox.insertAdjacentHTML('beforeend',`<div class="report-line"><span>남은 예산</span><b>${money(s.remain)}</b></div>`);
  orderedCategories(s.all).forEach(cat=>{
    const catItems=s.all.filter(x=>x.category===cat);
    const actual=catItems.filter(x=>x.done).reduce((sum,x)=>sum+itemAmount(x),0);
    const planned=catItems.filter(x=>!x.done).reduce((sum,x)=>sum+itemAmount(x),0);
    if(actual>0||planned>0) expBox.insertAdjacentHTML('beforeend',`<div class="report-line"><span>${cat}</span><b>지출 ${money(actual)} · 예정 ${money(planned)}</b></div>`);
  });

  function fill(target,list){
    const box=document.getElementById(target); box.innerHTML='';
    if(!list.length){box.innerHTML='<div class="report-empty">항목이 없습니다.</div>';return;}
    list.forEach(x=>{
      const amount=itemAmount(x);
      const kind=(typeof itemKind==='function'&&itemKind(x)==='shopping')?'장보기':'준비물';
      box.insertAdjacentHTML('beforeend',`<div class="report-item"><div><b>${x.name}</b><div class="signal-sub">${kind} · ${x.category} · ${sourceLabel(x.source)}</div></div><div>${normalizeOwnerName(x.owner)}</div><div>${x.qty||1}개</div><div class="hide-mobile">${money(amount)}</div></div>`);
    });
  }
  fill('r-done-items',s.all.filter(x=>x.done));
  fill('r-pending-items',s.all.filter(x=>!x.done));
}'''
html=html[:start]+fn+html[end:]

packed=base64.b64encode(gzip.compress(html.encode(),9)).decode()
chunks=[packed[i:i+7000] for i in range(0,len(packed),7000)]
loader='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Travelcheck</title></head><body><script>\n(async()=>{try{\nconst parts=[\n'''+',\n'.join('`'+x+'`' for x in chunks)+'''\n];\nconst b64=parts.join('');const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const ds=new DecompressionStream('gzip');const text=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).text();document.open();document.write(text);document.close();\n}catch(e){document.body.innerHTML='<div style="font-family:-apple-system,sans-serif;padding:40px">Travelcheck를 불러오지 못했습니다.<br><small>'+e+'</small></div>'}})();\n</script></body></html>'''
p.write_text(loader)
print('report settlement logic fixed')

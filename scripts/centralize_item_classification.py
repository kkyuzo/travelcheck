from pathlib import Path
import re,base64,gzip

p=Path('index.html')
src=p.read_text()
m=re.search(r"const parts=\[\s*(.*?)\s*\];",src,re.S)
if not m: raise SystemExit('compressed payload not found')
parts=re.findall(r'`([^`]*)`',m.group(1),re.S)
html=gzip.decompress(base64.b64decode(''.join(parts))).decode()

helper=r'''
function itemKind(it){
  const s=String(it?.source||'').trim();
  if(s==='local'||s==='internet') return 'shopping';
  return 'packing';
}
function packingItems(){return items.filter(x=>itemKind(x)==='packing')}
'''

if 'function itemKind(it)' not in html:
    html=html.replace("let shoppingFilter='all';",helper+"\nlet shoppingFilter='all';",1)

# One canonical classifier for both views.
html=html.replace("function shoppingItems(){return items.filter(x=>x.source==='local'||x.source==='internet')}","function shoppingItems(){return items.filter(x=>itemKind(x)==='shopping')}")
html=html.replace("if(it.source!=='home') return false;","if(itemKind(it)!=='packing') return false;")

# Defensive normalization when opening/creating shopping items.
html=html.replace("if(!id){document.getElementById('fSource').value='local';document.getElementById('fOwner').value=''}","if(!id){document.getElementById('fSource').value='local';document.getElementById('fOwner').value=''}")

# Make labels clearer without changing DB schema.
html=html.replace('현지구매와 인터넷구매 항목을 준비물과 분리해 관리합니다. 체크하면 구매 완료로 저장됩니다.','장보기는 현지구매·인터넷구매로만 분류되고, 준비물은 집에서 가져오는 항목으로만 분류됩니다. 체크 상태와 수정 내용은 DB에 저장됩니다.')

packed=base64.b64encode(gzip.compress(html.encode(),9)).decode()
chunks=[packed[i:i+7000] for i in range(0,len(packed),7000)]
loader='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Travelcheck</title></head><body><script>\n(async()=>{try{\nconst parts=[\n'''+',\n'.join('`'+x+'`' for x in chunks)+'''\n];\nconst b64=parts.join('');const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const ds=new DecompressionStream('gzip');const text=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).text();document.open();document.write(text);document.close();\n}catch(e){document.body.innerHTML='<div style="font-family:-apple-system,sans-serif;padding:40px">Travelcheck를 불러오지 못했습니다.<br><small>'+e+'</small></div>'}})();\n</script></body></html>'''
p.write_text(loader)
print('item classification centralized')

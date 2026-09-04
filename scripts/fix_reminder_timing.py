from pathlib import Path
import re, base64, gzip

p=Path('index.html')
src=p.read_text()
m=re.search(r"const parts=\[\s*(.*?)\s*\];",src,re.S)
if not m: raise SystemExit('compressed payload not found')
parts=re.findall(r'`([^`]*)`',m.group(1),re.S)
html=gzip.decompress(base64.b64decode(''.join(parts))).decode()

marker='shopping-reminder-db-ready'
if marker not in html and 'maybeShowShoppingReminder' in html:
    retry="""\n/* shopping-reminder-db-ready */\n[800,1600,3000,5000].forEach(ms=>setTimeout(()=>{\n  try{ if(!shoppingReminderShown) maybeShowShoppingReminder(); }catch(e){}\n},ms));\n"""
    if 'const STAY_ADDRESS=' in html:
        html=html.replace('const STAY_ADDRESS=',retry+'\nconst STAY_ADDRESS=',1)
    else:
        html=html.replace('</script>',retry+'\n</script>',1)

packed=base64.b64encode(gzip.compress(html.encode(),9)).decode()
chunks=[packed[i:i+7000] for i in range(0,len(packed),7000)]
loader='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>Travelcheck</title></head><body><script>\n(async()=>{try{\nconst parts=[\n'''+',\n'.join('`'+x+'`' for x in chunks)+'''\n];\nconst b64=parts.join('');const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const ds=new DecompressionStream('gzip');const text=await new Response(new Blob([bytes]).stream().pipeThrough(ds)).text();document.open();document.write(text);document.close();\n}catch(e){document.body.innerHTML='<div style="font-family:-apple-system,sans-serif;padding:40px">Travelcheck를 불러오지 못했습니다.<br><small>'+e+'</small></div>'}})();\n</script></body></html>'''
p.write_text(loader)
print('reminder timing fixed')

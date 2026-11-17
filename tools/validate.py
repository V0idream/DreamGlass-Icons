from pathlib import Path
import hashlib,json,re
from PIL import Image
r=Path(__file__).resolve().parents[1]
data=json.loads((r/'index.json').read_text(encoding='utf8'))
assert data['schema']==1
seen=set()
for e in data['icons']:
    assert re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+',e['package'])
    assert e['package'] not in seen;seen.add(e['package'])
    assert re.fullmatch(r'icons/[a-z0-9-]+\.png',e['path'])
    p=r/e['path'];assert len(p.read_bytes())<=262144
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
    with Image.open(p) as im:
        assert im.format=='PNG' and im.size==(256,256) and im.mode=='RGBA'
        assert im.getchannel('A').getextrema()==(0,255)
    assert e.get('render','') in ('','engraved')
    assert e.get('dynamic','') in ('','clock','calendar')
assert len(data['icons'])<=500
print(f'Validated {len(seen)} package mappings and all PNG hashes/geometry')

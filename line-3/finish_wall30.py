"""One-use exporter for the generated motif; refuses an already finished wall.

The fresh generated motif must occupy wall-v10.png. The exporter replaces it
with the complete inherited wall plus extracted pigment and writes record 30.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('codec28', Path(__file__).with_name('finish_wall28.py'))
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
ancestor = Path('artifacts/line-3/wall-v9.png')
out = Path('artifacts/line-3/wall-v10.png')
draft_hash = hashlib.sha256(out.read_bytes()).hexdigest()
assert draft_hash == 'c73cc1225b95e4103682839952184dc6dc596a70846c63f883add9535319a042', 'expected fresh generated motif; refusing to overwrite finished output'
w, h, c, original = codec.read_png(ancestor)
gw, gh, gc, draft = codec.read_png(out)
assert (w, h, c) == (1254, 1254, 3)
assert (gw, gh, gc) == (1774, 887, 3)
final = original[:]
x0, y0, mw, mh = 850, 960, 200, 65
for y in range(mh):
    for x in range(mw):
        sx, sy = 30 + x * 1720 // mw, 280 + y * 320 // mh
        at = (sy * gw + sx) * gc
        r, g, b = draft[at:at+3]
        # Extract only dark strokes, discarding white backdrop and pale shadows.
        darkness = 1 - max(r, g, b) / 255
        red = r > g * 1.65 and r > b * 1.65 and r > 85
        alpha = min(.75, max(0, ((1 - (g+b)/510) if red else darkness) - .35) * 1.5)
        # Deterministic worn pigment gaps; no lines or shapes are added by code.
        if (x * 17 + y * 29) % 11 < 3:
            continue
        pigment = (163, 64, 29) if red else (38, 29, 20)
        target = ((y0+y)*w+x0+x)*3
        for ch in range(3):
            final[target+ch] = round(original[target+ch]*(1-alpha) + pigment[ch]*alpha)
changed = outside = 0
for n in range(w*h):
    if original[n*3:n*3+3] != final[n*3:n*3+3]:
        changed += 1
        outside += not (x0 <= n%w < x0+mw and y0 <= n//w < y0+mh)
assert changed and outside == 0
sha = codec.write_png(out, w, h, final)
continuation = Path('artifacts/line-3/wall.png')
assert not continuation.exists() or continuation.is_symlink()
if continuation.is_symlink():
    continuation.unlink()
continuation.symlink_to(out.name)
rgba = bytearray()
for y in range(512):
    ya, yb = y*h//512, (y+1)*h//512
    for x in range(512):
        xa, xb = x*w//512, (x+1)*w//512
        for ch in range(3):
            rgba.append(round(sum(final[(sy*w+sx)*3+ch] for sy in range(ya,yb) for sx in range(xa,xb))/((yb-ya)*(xb-xa))))
        rgba.append(255)
js = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
const result = encode({data,width:512,height:512},77);
fs.writeFileSync('dist/line-3/30.jpg', result.data);
"""
subprocess.run(['node','-e',js],input=rgba,check=True)
report = {'wall':'artifacts/line-3/wall-v10.png','format':'PNG','dimensions':[w,h],
          'mode':'RGB','sha256':sha,'ancestor_sha256':hashlib.sha256(ancestor.read_bytes()).hexdigest(),
          'generated_motif_sha256':draft_hash,'changed_pixels':changed,
          'changed_pixels_outside_rectangle':outside,'new_mark_rectangle':[x0,y0,mw,mh],
          'thumbnail':{'path':'dist/line-3/30.jpg','format':'JPEG','dimensions':[512,512],
                       'bytes':Path('dist/line-3/30.jpg').stat().st_size},
          'unmet_visual_requirements':[], 'visual_review':'pending'}
Path('line-3/IMAGE-30.json').write_text(json.dumps(report,indent=2)+'\n')
record = {'name':'The Found Place','image':'https://api.imd.fun/artifacts/'+sha,
          'attributes':[{'trait_type':k,'value':v} for k,v in [
              ('Cave','Crystal'),('Wall','Line 3'),('Number',30),
              ('Left behind','Citation Reanchor'),
              ('Meaning','A pebble found in a new ring marks an exact passage located after its lines moved.'),
              ('One thing','Offline document search with exact source line citations')]]}
Path('dist/line-3/30.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(report,indent=2))

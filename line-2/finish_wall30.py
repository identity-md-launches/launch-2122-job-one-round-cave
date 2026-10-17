"""Composite image-tool pigment onto bare inherited rock; retain all other pixels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('png30', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)
OLD = Path('artifacts/line-2/wall-v9.png')
NEW = Path('artifacts/line-2/wall-v10.png')
RECT = (450, 900, 125, 120)


def main():
    ancestor = hashlib.sha256(OLD.read_bytes()).hexdigest()
    assert ancestor == '744900e6314e4d651db68b36b749e7b2e912b3495c3c982520314a7dadf8b15b'
    generated = hashlib.sha256(NEW.read_bytes()).hexdigest()
    assert generated == 'c70599f8164f73a6039afe8c64200849c7018a390071cd9f1d5f34862f564fc3', 'expected original generated motif; do not run twice'
    width, height, original = png.read_png(OLD)
    dw, dh, draft = png.read_png(NEW)
    assert (width, height) == (1254, 1254)
    final = original[:]
    dx, dy, pw, ph = RECT
    assert (dw, dh) == (width, height)
    # Only the new pigment on unused lower rock is retained from the edit.
    for y in range(ph):
        for x in range(pw):
            target = ((dy+y)*width+dx+x)*3
            r, g, b = draft[target:target+3]
            ochre = r > 65 and r > 1.65*g and r > 2.3*b
            pebble = ((x-52)/23)**2 + ((y-57)/28)**2 < 1 and r > 125 and g > 95
            if ochre or pebble:
                fade = max(0, min(1, x/5, y/5, (pw-1-x)/5, (ph-1-y)/5))
                alpha = .87 * fade
                for c in range(3):
                    final[target+c] = round(original[target+c]*(1-alpha)+draft[target+c]*alpha)
    changed = outside = 0
    for i in range(width*height):
        if final[3*i:3*i+3] != original[3*i:3*i+3]:
            changed += 1
            x, y = i % width, i // width
            outside += not (dx <= x < dx+pw and dy <= y < dy+ph)
    assert outside == 0 and changed > 1000
    digest = png.write_png(NEW, width, height, final)
    continuation = Path('artifacts/line-2/wall.png')
    if continuation.is_symlink():
        continuation.unlink()
    continuation.symlink_to('wall-v10.png')
    rgba = bytearray()
    for y in range(512):
        ya, yb = y*height//512, (y+1)*height//512
        for x in range(512):
            xa, xb = x*width//512, (x+1)*width//512
            count = (yb-ya)*(xb-xa)
            for c in range(3):
                rgba.append(round(sum(final[(sy*width+sx)*3+c] for sy in range(ya,yb) for sx in range(xa,xb))/count))
            rgba.append(255)
    # The inherited ordinary-file JPEG encoder is used only for media conversion.
    js = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
const result = encode({data,width:512,height:512},78);
if(result.data.length>100000)throw Error('JPEG too large');
fs.writeFileSync('dist/line-2/30.jpg',result.data);
"""
    subprocess.run(['node','-e',js],input=rgba,check=True)
    report = {'round':30,'ancestorSha256':ancestor,'generatedMotifSha256':generated,
              'wallSha256':digest,'dimensions':[width,height],'format':'PNG','channels':'RGB',
              'newMarkRectangle':list(RECT),'changedPixels':changed,
              'changedPixelsOutsideRectangle':outside,
              'method':'Image-tool-generated ochre enclosure and chalk pebble; selected pigment composited onto unused inherited rock.',
              'visualReview':'Pending final inspection','unmetVisualRequirements':[], 'images':[]}
    for path, kind, size in ((NEW,'PNG',[1254,1254]),(continuation,'PNG',[1254,1254]),
                             (Path('dist/line-2/30.jpg'),'JPEG',[512,512])):
        data = path.read_bytes()
        report['images'].append({'path':str(path),'format':kind,'dimensions':size,
                                 'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    Path('line-2/REVIEW-30.json').write_text(json.dumps(report,indent=2)+'\n')
    traits = [('Cave','Crystal'),('Wall','Line 2'),('Number',30),('Left behind','State Gate'),
              ('Meaning','A small enclosure admits only the pebble that belongs.'),
              ('One thing','Verify Ethereum account and storage proofs against trusted state roots')]
    record = {'name':'The Kept Pebble','image':'https://api.imd.fun/artifacts/'+digest,
              'attributes':[{'trait_type':key,'value':value} for key,value in traits]}
    Path('dist/line-2/30.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()

"""One-shot conservation of the generated linked-stone mark; no artwork synthesis."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    codec = module('png28', 'finish_wall22.py')
    preview = module('jpeg28', 'preview_jpeg27.py')
    ancestor = Path('artifacts/line-4/wall.png')
    output = Path('artifacts/line-4/wall-v10.png')
    assert ancestor.read_bytes() == Path('artifacts/line-4/wall-v9.png').read_bytes(), 'one-shot ancestor guard'
    ancestor_hash = hashlib.sha256(ancestor.read_bytes()).hexdigest()
    width, height, original = codec.read_png(ancestor)
    dw, dh, draft = codec.read_png(output)
    assert (width, height) == (dw, dh) == (1254, 1254)
    final = original[:]
    circles = [(638,1118,21), (693,1148,22), (755,1168,21), (781,1166,15)]
    segments = [(650,1127,681,1144), (707,1156,744,1167)]
    for y in range(1090,1192):
        for x in range(610,808):
            distance = min(math.hypot(x-cx,y-cy)-radius for cx,cy,radius in circles)
            for ax,ay,bx,by in segments:
                t = max(0,min(1,((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2)))
                distance = min(distance, math.hypot(x-ax-t*(bx-ax),y-ay-t*(by-ay))-9)
            alpha = max(0,min(1,-distance/3))
            if not alpha:
                continue
            at = (y*width+x)*3
            for c in range(3):
                final[at+c] = round(original[at+c]*(1-alpha)+draft[at+c]*alpha)
    points = [(i%width,i//width) for i in range(width*height)
              if final[i*3:i*3+3] != original[i*3:i*3+3]]
    assert points and all(610 <= x < 808 and 1090 <= y < 1192 for x,y in points)
    sha = codec.write_png(output,width,height,final)
    assert codec.read_png(output)[2] == final
    jpeg = preview.encode(preview.resize(final,width,height),512,512,quality=40)
    assert len(jpeg) < 100000
    Path('dist/line-4/28.jpg').write_bytes(jpeg)
    ancestor.write_bytes(output.read_bytes())
    evidence = {'ancestor_sha256':ancestor_hash,'wall_sha256':sha,
                'dimensions':[width,height],'format':'PNG','mode':'RGB',
                'changed_pixels':len(points),'changed_pixels_outside_mark_region':0,
                'mark_region_xyxy':[610,1090,808,1192],
                'method':'Imagegen edited the ancestral wall; only its new linked-stone pigment was retained through feathered local masks. Every other pixel is identical to the ancestor.',
                'outputs':['artifacts/line-4/wall-v10.png','artifacts/line-4/wall.png'],
                'preview':{'path':'dist/line-4/28.jpg','dimensions':[512,512],'format':'JPEG','bytes':len(jpeg)},
                'unmet_visual_requirements':[]}
    Path('line-4/IMAGE-28.json').write_text(json.dumps(evidence,indent=2)+'\n')
    record = {'name':'Follow the Cause','image':'https://api.imd.fun/artifacts/'+sha,
              'attributes':[{'trait_type':'Cave','value':'Crystal'},
                            {'trait_type':'Wall','value':'Line 4'},
                            {'trait_type':'Number','value':28},
                            {'trait_type':'Left behind','value':'Selection Explain'},
                            {'trait_type':'Meaning','value':'Three chalk stones joined by charcoal trace a choice back through its causes.'},
                            {'trait_type':'One thing','value':'Finite offline dependency resolution'}]}
    assert not Path('dist/line-4/28.json').exists()
    Path('dist/line-4/28.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__ == '__main__':
    main()

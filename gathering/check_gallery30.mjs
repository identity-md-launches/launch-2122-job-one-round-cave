// Exercise the self-contained gallery without a browser dependency or network.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const page=fs.readFileSync('dist/index.html','utf8');
const embedded=page.match(/<script id="records" type="application\/json">([\s\S]*?)<\/script>/)[1];
const groups=JSON.parse(embedded);
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.attrs={};this.hidden=false;}
  append(...nodes){this.children.push(...nodes);}
  setAttribute(name,value){this.attrs[name]=value;}
  getAttribute(name){return this.attrs[name]??null;}
}
const elements={records:{textContent:embedded},walls:new Element('div'),toggle:new Element('button')};
elements.toggle.setAttribute('aria-pressed','false');
const created=[];
const document={
  getElementById:id=>elements[id],
  createElement:tag=>{const e=new Element(tag);created.push(e);return e;},
  querySelectorAll:selector=>{assert.equal(selector,'.pending');return created.filter(e=>e.className==='pending');}
};
const script=page.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
vm.runInNewContext(script,{document}, {timeout:1000});
assert.equal(elements.walls.children.length,5);
let count=0,pending=0;
for(const [i,group] of groups.entries()){
  const section=elements.walls.children[i];
  assert.equal(section.id,i<4?'line'+(i+1):'gathering');
  const cards=section.children[1].children;
  assert.equal(cards.length,group.records.length);
  assert.deepEqual(group.records.map(r=>r.number),group.records.map(r=>r.number).sort((a,b)=>b-a));
  for(const [j,r] of group.records.entries()){
    const card=cards[j],image=card.children[0];count++;
    assert.equal(image.src,r.image);assert.equal(image.alt,r.name);
    assert.equal(card.children[3].href,r.path);
    if(r.name==='Not painted yet'){pending++;assert.equal(card.hidden,true);}
    else {image.onerror();assert.equal(image.src,r.path.replace(/\.json$/,'.jpg'));assert.equal(image.onerror,null);}
  }
}
assert.equal(count,147);assert.equal(pending,100);
elements.toggle.onclick();assert.equal(elements.toggle.getAttribute('aria-pressed'),'true');
assert(document.querySelectorAll('.pending').every(e=>!e.hidden));
elements.toggle.onclick();assert(document.querySelectorAll('.pending').every(e=>e.hidden));
assert(!/<script[^>]+src=|<link[^>]+(?:stylesheet|preload)/i.test(page));
const result={passed:true,records:count,groups:5,placeholders:pending,
  newest_gathering:groups[4].records[0].number,descending_order:true,
  toggle_and_image_fallback:true,external_script_or_style_dependencies:false,
  method:'Executed inline script against a minimal DOM; no full-browser layout or network image-loading claim.'};
fs.writeFileSync('gathering/gallery-checks-30.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));

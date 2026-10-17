// Composite only image-tool pigment on unused rock; preserve all ancestor marks.
import fs from 'node:fs';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const encode=require('../line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function crc(b){let v=0xffffffff;for(const c of b){v^=c;for(let j=0;j<8;j++)v=(v>>>1)^((v&1)?0xedb88320:0);}return (v^0xffffffff)>>>0;}
function read(path){
 const raw=fs.readFileSync(path);let w,h,ch,parts=[];
 for(let p=8;p<raw.length;){const n=raw.readUInt32BE(p),k=raw.toString('ascii',p+4,p+8),b=raw.subarray(p+8,p+8+n);
  if(crc(raw.subarray(p+4,p+8+n))!==raw.readUInt32BE(p+8+n))throw Error('CRC');
  if(k==='IHDR'){w=b.readUInt32BE(0);h=b.readUInt32BE(4);ch=b[9]===2?3:b[9]===6?4:0;if(b[8]!==8||b[12]!==0||!ch)throw Error('PNG format');}
  if(k==='IDAT')parts.push(b);p+=n+12;
 }
 const data=zlib.inflateSync(Buffer.concat(parts)),stride=w*ch,out=Buffer.alloc(w*h*3);let prev=Buffer.alloc(stride),at=0;
 for(let y=0;y<h;y++){let mode=data[at++],row=Buffer.from(data.subarray(at,at+stride));at+=stride;
  for(let x=0;x<stride;x++){let a=x>=ch?row[x-ch]:0,b=prev[x],c=x>=ch?prev[x-ch]:0,v=0;
   if(mode===1)v=a;else if(mode===2)v=b;else if(mode===3)v=(a+b)>>1;else if(mode===4){let p=a+b-c,ds=[Math.abs(p-a),Math.abs(p-b),Math.abs(p-c)];v=[a,b,c][ds.indexOf(Math.min(...ds))];}else if(mode!==0)throw Error('filter');
   row[x]=(row[x]+v)&255;
  }
  for(let x=0;x<w;x++)row.copy(out,(y*w+x)*3,x*ch,x*ch+3);prev=row;
 }
 return {w,h,pixels:out,raw};
}
function chunk(k,b){let tag=Buffer.from(k),n=Buffer.alloc(4),sum=Buffer.alloc(4);n.writeUInt32BE(b.length);sum.writeUInt32BE(crc(Buffer.concat([tag,b])));return Buffer.concat([n,tag,b,sum]);}
function png(w,h,pixels){let ih=Buffer.alloc(13);ih.writeUInt32BE(w);ih.writeUInt32BE(h,4);ih[8]=8;ih[9]=2;
 let rows=[];for(let y=0;y<h;y++)rows.push(Buffer.from([0]),pixels.subarray(y*w*3,(y+1)*w*3));
 return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(Buffer.concat(rows),{level:9})),chunk('IEND',Buffer.alloc(0))]);}
const source='artifacts/gathering/wall-v9.png',target='artifacts/gathering/wall-v10.png';
const original=read(source),draft=read(target),{w,h}=original;
if(w!==1254||h!==1254||draft.w!==w||draft.h!==h)throw Error('dimensions');
if(fs.existsSync('gathering/image-preservation-30.json'))throw Error('Already finished; do not apply twice');
const final=Buffer.from(original.pixels);let changed=0;
const rect=[489,973,66,76];
for(let y=rect[1];y<rect[1]+rect[3];y++)for(let x=rect[0];x<rect[0]+rect[2];x++){
 let i=(y*w+x)*3;
 // Fade only the generated local mark into bare stone. The inherited wall is
 // copied byte-for-byte everywhere else, including all ancestor pictographs.
 let d=((x-522)/33)**2+((y-1011)/38)**2;
 let a=d<0.80?1:d<1?((1-d)/.20):0;
 if(a){for(let c=0;c<3;c++)final[i+c]=Math.round(original.pixels[i+c]*(1-a)+draft.pixels[i+c]*a);}
 if(!final.subarray(i,i+3).equals(original.pixels.subarray(i,i+3)))changed++;
}
if(changed<500)throw Error('missing pigment');
const result=png(w,h,final);fs.writeFileSync(target,result);
const thumb=Buffer.alloc(512*512*4);
// Area average to keep the weathered pigment readable at wallet/gallery size.
for(let y=0;y<512;y++)for(let x=0;x<512;x++){
 let sums=[0,0,0],n=0;
 for(let yy=Math.floor(y*h/512);yy<Math.floor((y+1)*h/512);yy++)for(let xx=Math.floor(x*w/512);xx<Math.floor((x+1)*w/512);xx++){
  for(let c=0;c<3;c++)sums[c]+=final[(yy*w+xx)*3+c];n++;
 }
 let p=(y*512+x)*4;for(let c=0;c<3;c++)thumb[p+c]=Math.round(sums[c]/n);thumb[p+3]=255;
}
const jpg=encode({data:thumb,width:512,height:512},80).data;if(jpg.length>100000)throw Error('thumbnail size');
fs.writeFileSync('dist/gathering/30.jpg',jpg);
const continuation='artifacts/gathering/wall.png';if(fs.existsSync(continuation)||(()=>{try{return fs.lstatSync(continuation).isSymbolicLink();}catch{return false;}})())fs.unlinkSync(continuation);fs.symlinkSync('wall-v10.png',continuation);
const evidence={ancestor_sha256:hash(original.raw),wall_sha256:hash(result),dimensions:[w,h],format:'PNG',mode:'RGB',new_mark_rectangle:rect,changed_pixels:changed,changed_pixels_outside_rectangle:0,method:'Image tool edit; only the new mark area was blended onto unused rock. All other pixels copied from ancestor.',preview:{dimensions:[512,512],format:'JPEG',bytes:jpg.length},unmet_visual_requirements:[]};
fs.writeFileSync('gathering/image-preservation-30.json',JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify(evidence));

#!/usr/bin/env node
// Actual decoder acceptance through browser APIs; only owned disposable state.
import assert from 'node:assert/strict';
import {spawn,execFileSync} from 'node:child_process';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,existsSync,readdirSync,realpathSync,rmSync,openSync,closeSync} from 'node:fs';
import {join} from 'node:path';
const args=process.argv.slice(2);assert(args.length===4,'Usage: --chrome ABS --artifact-root ABS');
const opts=Object.fromEntries([[args[0],args[1]],[args[2],args[3]]]);
assert(opts['--chrome']?.startsWith('/')&&opts['--artifact-root']?.startsWith('/'),'Absolute paths required');
const root=opts['--artifact-root'];mkdirSync(root,{recursive:true,mode:0o700});assert(!existsSync(join(root,'result.json')),'Use a fresh run root');
const chrome=realpathSync(opts['--chrome']);const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const result={schema:'stealthcdp.codec-acceptance.v1',startedAt:new Date().toISOString(),chrome,sha256:sha(chrome),harnessSha256:sha(new URL(import.meta.url)),phase:'prepared'};
const save=()=>writeFileSync(join(root,'result.json'),JSON.stringify(result,null,2)+'\n',{mode:0o600});save();
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label,ms=15000){const end=Date.now()+ms;do{const v=fn();if(v)return v;await delay(100)}while(Date.now()<end);throw Error('Timeout: '+label)}
function profileWriters(profile){return readdirSync('/proc').filter(n=>/^\d+$/.test(n)).filter(n=>{try{return readFileSync('/proc/'+n+'/cmdline').includes(Buffer.from('--user-data-dir='+profile+'\0'))}catch{return false}})}
let child,profile,ws,server;let next=1;const pending=new Map();
async function cdp(method,params={}){const id=next++;return await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout '+method))},30000);pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params}))})}
try{
 result.version=execFileSync(chrome,['--version'],{encoding:'utf8',timeout:15000}).trim();assert(result.version.startsWith('Chromium '));assert(!result.version.includes('Testing'));
 result.ffmpegVersion=execFileSync('ffmpeg',['-version'],{encoding:'utf8'}).split('\n')[0];
 const common=['-hide_banner','-loglevel','error','-n'];
 const fixtures=[['sample.mp4',['-f','lavfi','-i','color=c=black:s=64x64:r=10','-f','lavfi','-i','sine=frequency=1000:sample_rate=48000','-t','1','-c:v','libx264','-profile:v','baseline','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart']],['sample.webm',['-f','lavfi','-i','color=c=black:s=64x64:r=10','-f','lavfi','-i','sine=frequency=1000:sample_rate=48000','-t','1','-c:v','libvpx-vp9','-c:a','libopus']],['sample.m4a',['-f','lavfi','-i','sine=frequency=1000:sample_rate=48000','-t','1','-c:a','aac','-movflags','+faststart']]];
 for(const [name,a] of fixtures)execFileSync('ffmpeg',[...common,...a,join(root,name)],{timeout:30000,stdio:['ignore','ignore','pipe']});
 result.fixtures=Object.fromEntries(fixtures.map(([n])=>[n,sha(join(root,n))]));save();
 server=createServer((req,res)=>{const p=req.url?.split('?')[0];const names={'/sample.mp4':'video/mp4','/sample.webm':'video/webm','/sample.m4a':'audio/mp4'};res.setHeader('Cache-Control','no-store');if(names[p]){res.setHeader('Content-Type',names[p]);res.end(readFileSync(join(root,p.slice(1))))}else{res.setHeader('Content-Type','text/html');res.end('<!doctype html><title>Owned codec acceptance</title>')}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port;
 profile=mkdtempSync(join(root,'profile-'));const fd=openSync(join(root,'browser.log'),'a',0o600);
 child=spawn(chrome,['--headless=new','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-gpu','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{detached:true,stdio:['ignore',fd,fd]});closeSync(fd);
 result.pid=child.pid;result.phase='launched';save();child.on('error',e=>{result.launchError=e.message;save()});
 await until(()=>existsSync(join(profile,'DevToolsActivePort')),'CDP port');assert(child.exitCode===null);
 const port=readFileSync(join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];assert(/^\d+$/.test(port));
 const target=await fetch('http://127.0.0.1:'+port+'/json/new?'+encodeURIComponent(url),{method:'PUT'}).then(r=>r.json());
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
 ws.addEventListener('message',e=>{const v=JSON.parse(e.data);const p=pending.get(v.id);if(!p)return;clearTimeout(p.timer);pending.delete(v.id);v.error?p.reject(Error(JSON.stringify(v.error))):p.resolve(v.result)});
 await until(async()=>true,'ready');
 await cdp('Page.enable');await cdp('Page.navigate',{url});
 // Wait for the committed local document; do not use a stale about:blank origin.
 const end=Date.now()+15000;let ready=false;while(Date.now()<end){const x=await cdp('Runtime.evaluate',{expression:'location.origin',returnByValue:true});if(x.result.value===url){ready=true;break}await delay(100)}assert(ready,'Local fixture navigation');
 const expression=`(async()=>{const timeout=(p)=>{let timer;return Promise.race([p,new Promise((_,r)=>timer=setTimeout(()=>r(Error('decoder timeout')),10000))]).finally(()=>clearTimeout(timer))};
 async function video(name){const v=document.createElement('video');v.muted=true;v.src='/'+name;document.body.append(v);try{await timeout(new Promise((resolve,reject)=>{v.onended=resolve;v.onerror=()=>reject(Error('media error '+v.error?.code));v.play().catch(reject)}));return {decoded:true,width:v.videoWidth,height:v.videoHeight,frames:v.getVideoPlaybackQuality().totalVideoFrames}}catch(e){return {decoded:false,error:e.message}}finally{v.pause();v.removeAttribute('src');v.load();v.remove()}}
 async function aac(){let context;try{context=new AudioContext();const bytes=await fetch('/sample.m4a').then(r=>r.arrayBuffer());const b=await timeout(context.decodeAudioData(bytes));const pcm=b.getChannelData(0);let sum=0;for(const x of pcm)sum+=x*x;return {decoded:true,duration:b.duration,channels:b.numberOfChannels,sampleRate:b.sampleRate,samples:b.length,rms:Math.sqrt(sum/pcm.length)}}catch(e){return {decoded:false,error:e.message}}finally{if(context)await context.close()}}
 return {webdriver:navigator.webdriver,h264:await video('sample.mp4'),webm:await video('sample.webm'),aac:await aac()}})()`;
 const observed=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:false});assert(!observed.exceptionDetails,JSON.stringify(observed.exceptionDetails));result.observed=observed.result.value;save();
 const o=result.observed;assert.equal(o.webdriver,false,'StealthCDP webdriver posture');
 for(const key of ['h264','webm']){assert.equal(o[key].decoded,true,key+' actual video decode: '+o[key].error);assert.equal(o[key].width,64);assert.equal(o[key].height,64);assert(o[key].frames>0,key+' decoded frames')}
 assert.equal(o.aac.decoded,true,'AAC actual PCM decode: '+o.aac.error);assert(o.aac.duration>0.9&&o.aac.duration<1.2);assert.equal(o.aac.channels,1);assert(o.aac.sampleRate>0&&o.aac.samples>40000);assert(o.aac.rms>0.01,'AAC tone has nonzero decoded PCM');result.phase='accepted';result.success=true;
}catch(error){result.success=false;result.phase='failed';result.error=error.stack;process.exitCode=1}
finally{
 ws?.close();for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('CDP cleanup'))}pending.clear();
 try{if(child?.pid){try{process.kill(-child.pid,'SIGTERM')}catch{};await until(()=>profileWriters(profile).length===0,'owned profile writers exit',5000).catch(async()=>{try{process.kill(-child.pid,'SIGKILL')}catch{};await until(()=>profileWriters(profile).length===0,'owned profile writers exit after kill')});result.profileWritersGone=true}if(profile&&result.profileWritersGone){rmSync(profile,{recursive:true});result.profileRemoved=true}}catch(e){result.cleanupError=e.message;result.success=false;process.exitCode=1}
 if(server){server.closeAllConnections();await new Promise(r=>server.close(r))}result.finishedAt=new Date().toISOString();save();console.log(JSON.stringify({success:result.success,observed:result.observed,error:result.error,profileWritersGone:result.profileWritersGone}));
}

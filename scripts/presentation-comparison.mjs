#!/usr/bin/env node
// Controlled local measurement only. Does not change browser/service settings.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {spawn,execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,readdirSync,readlinkSync,realpathSync,existsSync,openSync,closeSync,rmSync} from 'node:fs';
import {join,basename} from 'node:path';
import {pathToFileURL} from 'node:url';

const options=Object.fromEntries(process.argv.slice(2).reduce((a,v,i,x)=>i%2?a:[...a,[v.replace(/^--/,''),x[i+1]]],[]));
for(const key of ['artifact-root','mcp-helper','stock','stealth','agent']) assert(options[key]?.startsWith('/'),`Require absolute --${key}`);
const root=options['artifact-root'];mkdirSync(root,{recursive:true,mode:0o700});
assert(!existsSync(join(root,'run.json')),'Use a fresh artifact root; never replay an uncertain run');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const binaries=Object.fromEntries(['stock','stealth','agent'].map(k=>[k,{path:realpathSync(options[k]),sha256:hash(realpathSync(options[k]))}]));
for(const key of ['stock','stealth']) binaries[key].version=execFileSync(binaries[key].path,['--version'],{encoding:'utf8'}).trim();
assert(binaries.stock.version.startsWith('Google Chrome '));assert(binaries.stealth.version.startsWith('Chromium '));
assert(!binaries.stock.version.includes('Testing'));assert(!binaries.stealth.version.includes('Testing'));
for(const name of ['sample.mp4','sample.webm'])assert(existsSync(join(root,name)),'Generate synthetic media before launch: '+name);
const run={fixtureHashes:Object.fromEntries(['sample.mp4','sample.webm'].map(n=>[n,hash(join(root,n))])),harnessSha256:hash(new URL(import.meta.url)),schema:'stealthcdp.presentation-comparison.v1',startedAt:new Date().toISOString(),binaries,transport:'loopback-http',rows:[],phase:'prepared'};
const save=()=>writeFileSync(join(root,'run.json'),JSON.stringify(run,null,2)+'\n',{mode:0o600});save();
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms,label){const end=Date.now()+ms;do{const v=fn();if(v)return v;await delay(200)}while(Date.now()<end);throw Error(`Timed out: ${label}`)}
const reports=new Map(),requests=[];
const selectHeaders=h=>Object.fromEntries(Object.entries(h).filter(([k])=>k==='user-agent'||k==='accept-language'||k.startsWith('sec-ch-ua')));
// Verify the existing desktop without changing its server or authentication.
const manualDisplay=options.display??':0';
assert(/^:\d+(?:\.\d+)?$/.test(manualDisplay),'Require local X display');
execFileSync('/usr/bin/xdpyinfo',[],{env:{...process.env,DISPLAY:manualDisplay},stdio:['ignore','ignore','pipe']});
run.manualDisplay={display:manualDisplay,source:'verified-existing-X-server',managedWindowProofRequired:true};save();
const js=String.raw`
async function identity(n){let high;try{high=await n.userAgentData?.getHighEntropyValues(['architecture','bitness','platformVersion','fullVersionList','model','wow64'])}catch(e){high={error:e.name}}return {userAgent:n.userAgent,platform:n.platform,languages:[...n.languages],language:n.language,webdriver:n.webdriver,hardwareConcurrency:n.hardwareConcurrency,deviceMemory:n.deviceMemory,uaData:n.userAgentData?.toJSON(),high}}
async function bounded(p,label,ms=4000){let t;try{return await Promise.race([p,new Promise(r=>t=setTimeout(()=>r({unavailable:label}),ms))])}catch(e){return {error:e.name,message:e.message}}finally{clearTimeout(t)}}
async function collect(){
 const report={identity:await identity(navigator),secureContext:isSecureContext,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,locale:Intl.DateTimeFormat().resolvedOptions().locale,geometry:{screen:{width:screen.width,height:screen.height,availWidth:screen.availWidth,availHeight:screen.availHeight,colorDepth:screen.colorDepth},innerWidth,innerHeight,outerWidth,outerHeight,dpr:devicePixelRatio},visibility:document.visibilityState,focused:document.hasFocus(),cookieEnabled:navigator.cookieEnabled};
 report.headers=await fetch('/echo'+location.search).then(r=>r.json());
 report.worker=await bounded(new Promise((resolve,reject)=>{const w=new Worker('/worker.js');w.onmessage=e=>{resolve(e.data);w.terminate()};w.onerror=e=>reject(Error(e.message))}),'worker');
 report.frame=await bounded(new Promise(resolve=>{const f=document.createElement('iframe');f.src='/frame'+location.search;window.addEventListener('message',function on(e){if(e.origin===location.origin&&e.data?.kind==='frame'){removeEventListener('message',on);resolve(e.data.identity);f.remove()}});document.body.append(f)}),'frame');
 report.permissions={};for(const name of ['geolocation','notifications','camera','microphone','clipboard-read'])try{report.permissions[name]=(await navigator.permissions.query({name})).state}catch(e){report.permissions[name]=e.name}
 report.pdfViewerEnabled=navigator.pdfViewerEnabled;report.plugins=[...navigator.plugins].map(p=>({name:p.name,filename:p.filename}));
 const cv=document.createElement('canvas');const gl=cv.getContext('webgl2')||cv.getContext('webgl');report.webgl={available:!!gl};if(gl){const ext=gl.getExtension('WEBGL_debug_renderer_info');Object.assign(report.webgl,{version:gl.getParameter(gl.VERSION),vendor:gl.getParameter(gl.VENDOR),renderer:gl.getParameter(gl.RENDERER),unmaskedVendor:ext?gl.getParameter(ext.UNMASKED_VENDOR_WEBGL):null,unmaskedRenderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):null,maxTextureSize:gl.getParameter(gl.MAX_TEXTURE_SIZE)});gl.getExtension('WEBGL_lose_context')?.loseContext()}
 report.webgpu=await bounded((async()=>{if(!navigator.gpu)return {available:false};const a=await navigator.gpu.requestAdapter();return {available:!!a,info:a?{vendor:a.info?.vendor,architecture:a.info?.architecture,device:a.info?.device,description:a.info?.description}:null}})(),'webgpu');
 const cx=document.createElement('canvas').getContext('2d');report.fontWidths={};for(const font of ['sans-serif','serif','monospace','Arial','Liberation Sans','Noto Sans','DejaVu Sans','Times New Roman','Courier New']){cx.font='16px '+(['sans-serif','serif','monospace'].includes(font)?font:'"'+font+'", monospace');report.fontWidths[font]=cx.measureText('Presentation probe: WWW iii 0123456789').width}
 report.media={};for(const [key,type] of [['h264','video/mp4; codecs="avc1.42E01E"'],['aac','audio/mp4; codecs="mp4a.40.2"'],['vp9','video/webm; codecs="vp9"'],['opus','audio/webm; codecs="opus"']])report.media[key]=document.createElement('video').canPlayType(type);
 report.mediaCapabilities=await bounded(navigator.mediaCapabilities.decodingInfo({type:'file',video:{contentType:'video/mp4; codecs="avc1.42E01E"',width:64,height:64,bitrate:50000,framerate:10}}),'mediaCapabilities');
 report.eme={};for(const key of ['org.w3.clearkey','com.widevine.alpha'])report.eme[key]=await bounded(navigator.requestMediaKeySystemAccess(key,[{initDataTypes:['cenc'],videoCapabilities:[{contentType:'video/mp4; codecs="avc1.42E01E"'}]}]).then(()=>({supported:true})),key);
 report.playback={};for(const file of ['sample.mp4','sample.webm'])report.playback[file]=await bounded(new Promise(resolve=>{const v=document.createElement('video');v.muted=true;v.playsInline=true;v.src='/'+file;document.body.append(v);const finish=value=>{v.pause();v.removeAttribute('src');v.load();v.remove();resolve(value)};v.onerror=()=>finish({decoded:false,code:v.error?.code});v.onended=()=>finish({decoded:true,width:v.videoWidth,height:v.videoHeight,frames:v.getVideoPlaybackQuality?.().totalVideoFrames});v.play().catch(e=>finish({decoded:false,error:e.name}))}),'playback-'+file,5000);
 const popup=window.open('/popup','presentation-popup','width=180,height=100');report.popup={openedWithoutUserGesture:!!popup};if(popup)popup.close();
 return report;
}
collect().then(data=>fetch('/report'+location.search,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})).then(()=>{document.title='Presentation comparison complete';document.body.append(' Measurement complete.');}).catch(e=>fetch('/report'+location.search,{method:'POST',body:JSON.stringify({fatal:{name:e.name,message:e.message}})}));
`;
const server=createServer(async(req,res)=>{
 try {
 const u=new URL(req.url,'http://localhost');requests.push({path:u.pathname,id:u.searchParams.get('id'),headers:selectHeaders(req.headers)});
 res.setHeader('Accept-CH','Sec-CH-UA-Full-Version-List, Sec-CH-UA-Platform-Version, Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Model, Sec-CH-UA-WoW64');res.setHeader('Cache-Control','no-store');
 if(u.pathname==='/report'){if(!/^(managed-stealth|manual-stealth|stock-chrome)-[12]$/.test(u.searchParams.get('id')??'')||req.headers.origin!==origin){res.writeHead(403).end();return}let body='';for await(const x of req){body+=x;if(body.length>1000000){res.writeHead(413).end();return}}const data=JSON.parse(body);reports.set(u.searchParams.get('id'),data);writeFileSync(join(root,u.searchParams.get('id')+'.json'),JSON.stringify(data,null,2)+'\n',{mode:0o600});res.end('ok');return}
 if(u.pathname==='/echo'){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(selectHeaders(req.headers)));return}
 if(u.pathname==='/worker.js'){res.setHeader('Content-Type','text/javascript');res.end(js.slice(0,js.indexOf('async function bounded'))+'identity(navigator).then(v=>postMessage(v));');return}
 if(u.pathname==='/frame'){res.setHeader('Content-Type','text/html');res.end('<script>'+js.slice(0,js.indexOf('async function bounded'))+'identity(navigator).then(v=>parent.postMessage({kind:"frame",identity:v},location.origin));</script>');return}
 if(u.pathname==='/sample.mp4'||u.pathname==='/sample.webm'){res.setHeader('Content-Type',u.pathname.endsWith('mp4')?'video/mp4':'video/webm');res.end(readFileSync(join(root,u.pathname.slice(1))));return}
 res.setHeader('Content-Type','text/html');res.end(u.pathname==='/popup'?'<title>Owned synthetic popup</title>':'<!doctype html><meta charset="utf-8"><title>Presentation measurement</title><body><h1>Controlled presentation measurement</h1><script>'+js+'</script>');
 } catch(error) {run.fixtureError=error.message;save();if(!res.headersSent)res.writeHead(500);res.end('Synthetic fixture failure')}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://localhost:'+server.address().port;run.origin=origin;save();
try{new Function(js);const check=await fetch(origin+'/echo?id=fixture-preflight');assert.equal(check.status,200);await check.json();const worker=await fetch(origin+'/worker.js');assert.equal(worker.status,200);new Function(await worker.text());console.log('Fixture HTTP and script preflight passed')}catch(error){run.phase='fixture_preflight_failed';run.error=error.message;save();server.closeAllConnections();server.close();throw error}
if(options['preflight-only']==='true'){
 const denied=await fetch(origin+'/report?id=../../invalid',{method:'POST',headers:{Origin:origin},body:'{}'});assert.equal(denied.status,403);
 const accepted=await fetch(origin+'/report?id=manual-stealth-1',{method:'POST',headers:{Origin:origin},body:JSON.stringify({fixturePreflightOnly:true})});assert.equal(accepted.status,200);assert.equal(reports.get('manual-stealth-1').fixturePreflightOnly,true);
 run.phase='fixture_preflight_passed';save();server.closeAllConnections();await new Promise(r=>server.close(r));console.log('PASS: fixture routes, script syntax and report path/origin guards; zero browser launches');process.exit(0);
}
function processProof(pid){try{const base='/proc/'+pid;return {pid:Number(pid),exe:readlinkSync(base+'/exe'),start:readFileSync(base+'/stat','utf8').split(') ')[1].split(' ')[19],argv:readFileSync(base+'/cmdline','utf8').replaceAll('\0',' ').trim()}}catch{return null}}
function profileProcesses(profile,rootOnly=false){return readdirSync('/proc').filter(x=>/^\d+$/.test(x)).map(processProof).filter(x=>x&&x.argv.includes('--user-data-dir='+profile)&&(!rootOnly||!x.argv.includes('--type=')))}
let desktopEnv={DISPLAY:manualDisplay};let client;
const modes=(options.modes??'managed-stealth,manual-stealth,stock-chrome').split(',');assert(modes.every(x=>['managed-stealth','manual-stealth','stock-chrome'].includes(x)));assert.equal(new Set(modes).size,modes.length,'No duplicate measurement modes');run.modes=modes;save();
async function call(name,args){const r=await client.send('tools/call',{name,arguments:args});const t=r.content?.find(x=>x.type==='text');assert(t,'MCP text required');const v=JSON.parse(t.text);assert.equal(v.success,true,JSON.stringify(v.error));return v.data}
try{
 if(modes.includes('managed-stealth')) {const {createMcpStdioClient}=await import(pathToFileURL(options['mcp-helper']));const env={...process.env,AGENT_BROWSER_SMOKE_AGENT_BROWSER_CMD:binaries.agent.path};delete env.AGENT_BROWSER_EXECUTABLE_PATH;
 client=createMcpStdioClient({context:{env},args:['mcp','serve'],onFatal:()=>{}});await client.send('initialize',{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'controlled-presentation-comparison',version:'1'}});client.notify('notifications/initialized');}
 for(let iteration=1;iteration<=2;iteration++)for(const mode of modes){
  const id=mode+'-'+iteration,row={id,mode,phase:'prepared'};run.rows.push(row);save();let opened,child,profile;
  try{
   row.phase='launch_requested';save();
   if(mode==='managed-stealth'){
    opened=await call('browser_open',{profileMode:'disposable',taskKey:basename(root)+'-'+id,url:origin+'/?id='+id,serviceName:'chromium-stealthcdp',agentName:'codex',taskName:'Measure synthetic desktop presentation '+id});row.task=opened;save();
    const matches=readdirSync('/proc').filter(x=>/^\d+$/.test(x)).map(processProof).filter(x=>x&&!x.argv.includes('--type=')&&x.argv.match(/--user-data-dir=([^ ]+)/)?.[1].split('/').pop()===opened.profileId);assert.equal(matches.length,1,'Exact managed browser process');row.process=matches[0];assert.equal(realpathSync(row.process.exe),binaries.stealth.path,'Required StealthCDP only');profile=row.process.argv.match(/--user-data-dir=([^ ]+)/)[1];
    const values=Object.fromEntries(readFileSync('/proc/'+row.process.pid+'/environ','utf8').split('\0').filter(Boolean).map(x=>{const i=x.indexOf('=');return[x.slice(0,i),x.slice(i+1)]}));row.display=values.DISPLAY??null;row.displayObservation=row.display?'proc-environment':'unavailable-in-proc';assert(!row.process.argv.includes('--headless'),'Headless row cannot qualify desktop comparison');let ids=[];try{ids=execFileSync('/usr/bin/xdotool',['search','--pid',String(row.process.pid)],{env:{...process.env,DISPLAY:manualDisplay},encoding:'utf8'}).trim().split('\n').filter(Boolean)}catch{}if(ids.length){row.display=manualDisplay;row.displayObservation='exact-PID-X-window';row.windowIds=ids}else row.displayObservation='not-proven-on-manual-display';
   }else{
    assert(desktopEnv?.DISPLAY);profile=mkdtempSync(join(root,id+'-profile-'));const binary=mode==='manual-stealth'?binaries.stealth:binaries.stock;const fd=openSync(join(root,id+'.stderr'),'w',0o600);child=spawn(binary.path,['--user-data-dir='+profile,'--no-first-run','--no-default-browser-check','--new-window',origin+'/?id='+id],{env:{...process.env,...desktopEnv},stdio:['ignore',fd,fd]});closeSync(fd);row.process=await until(()=>processProof(child.pid),5000,'manual process identity');assert.equal(realpathSync(row.process.exe),binary.path);row.display=desktopEnv.DISPLAY;
   }
   row.profile=profile;row.phase='launched';save();const data=await until(()=>reports.get(id),45000,'fixture report '+id);assert(!data.fatal,JSON.stringify(data.fatal));assert.equal(data.secureContext,true,'Loopback must be secure context');row.report=id+'.json';row.phase='measured';save();console.log(JSON.stringify({id,phase:row.phase,display:row.display,webdriver:data.identity.webdriver,popup:data.popup,playback:data.playback}));
  }catch(e){row.error=e.message;row.phase='failed';save();throw e}
  finally{
   if(opened){row.close=await call('browser_close',{taskId:opened.taskId,reason:'Controlled presentation measurement complete'});assert.equal(row.close.closed,true)}
   else if(child&&row.process){const now=processProof(row.process.pid);if(now&&now.start===row.process.start&&now.exe===row.process.exe&&now.argv.includes('--user-data-dir='+profile)){process.kill(row.process.pid,'SIGTERM');row.close={signal:'SIGTERM',verifiedOwnedProcess:true}}}
   if(row.process){await until(()=>!processProof(row.process.pid),10000,'owned browser exit '+id);row.originalPidGone=true}
   if(profile){await until(()=>profileProcesses(profile).length===0,10000,'profile writers gone '+id);row.profileWritersGone=true;if(child){assert(profile.startsWith(join(root,id+'-profile-')),'Only remove this run-owned manual profile');rmSync(profile,{recursive:true});row.disposableProfileRemoved=true}}
   row.phase=row.error?'failed_closed':'closed';save();
  }
 }
 run.phase='complete';run.completedAt=new Date().toISOString();save();
}catch(e){run.phase='failed';run.error=e.message;save();console.error(e);process.exitCode=1}
finally{client?.close();writeFileSync(join(root,'requests.json'),JSON.stringify(requests,null,2)+'\n',{mode:0o600});server.closeAllConnections();await new Promise(r=>server.close(r));}

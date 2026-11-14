#!/usr/bin/env node
// Fresh installed public MCP proof; no global reset or retained profile effects.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createInterface} from 'node:readline';
import {readFileSync,writeFileSync,appendFileSync,readdirSync,readlinkSync,realpathSync,mkdirSync,existsSync} from 'node:fs';
import {join,basename,resolve} from 'node:path';
const [agentArg,manifestArg,rootArg]=process.argv.slice(2);
assert([agentArg,manifestArg,rootArg].every(x=>x?.startsWith('/')),'Usage: ABS_AGENT ABS_MANIFEST ABS_FRESH_ROOT');
const agent=realpathSync(agentArg),manifest=JSON.parse(readFileSync(manifestArg)),root=resolve(rootArg);
mkdirSync(root,{recursive:true,mode:0o700});assert(!existsSync(join(root,'result.json')),'Never replay an uncertain acceptance root');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const expected=manifest.executable.sha256;
const receipt={schema:'stealthcdp.managed-browser-acceptance.v1',phase:'prepared',startedAt:new Date().toISOString(),agent,agentSha256:hash(agent),expectedBrowserSha256:expected,taskKey:'stealthcdp-managed-'+basename(root),success:false};
const save=()=>writeFileSync(join(root,'result.json'),JSON.stringify(receipt,null,2)+'\n',{mode:0o600});save();
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,label,ms=15000){const end=Date.now()+ms;do{const value=fn();if(value)return value;await delay(100)}while(Date.now()<end);throw Error('Timeout: '+label)}
function browsers(){return readdirSync('/proc').filter(n=>/^\d+$/.test(n)).flatMap(n=>{try{const raw=readFileSync('/proc/'+n+'/cmdline','utf8');const argv=raw.replaceAll('\0',' ');const direct=raw.split('\0').find(x=>x.startsWith('--user-data-dir='));const match=argv.match(/--user-data-dir=(.*?)(?= --[a-zA-Z]|\s*$)/);const profile=direct?direct.slice('--user-data-dir='.length):match?.[1].trim();if(!profile)return[];return[{pid:Number(n),profile,argv,executable:readlinkSync('/proc/'+n+'/exe')}]}catch{return[]}})}
const env={...process.env};for(const key of ['AGENT_BROWSER_EXECUTABLE_PATH','AGENT_BROWSER_CONFIG','AGENT_BROWSER_RUNTIME_PROFILE','AGENT_BROWSER_PROFILE','AGENT_BROWSER_CDP','AGENT_BROWSER_AUTO_CONNECT','AGENT_BROWSER_SOCKET_DIR','AGENT_BROWSER_HOME'])delete env[key];
const child=spawn(agent,['mcp','serve'],{env,stdio:['pipe','pipe','pipe']});
let next=1,task,profile;const pending=new Map();
function fail(error){for(const p of pending.values()){clearTimeout(p.timer);p.reject(error)}pending.clear()}
child.stdin.on('error',fail);child.on('error',fail);child.on('exit',()=>fail(Error('MCP transport exited')));
child.stderr.on('data',d=>appendFileSync(join(root,'transport.stderr.log'),d,{mode:0o600}));
createInterface({input:child.stdout}).on('line',line=>{try{const v=JSON.parse(line),p=pending.get(v.id);if(!p)return;clearTimeout(p.timer);pending.delete(v.id);v.error?p.reject(Error(JSON.stringify(v.error))):p.resolve(v.result)}catch(e){fail(e)}});
function send(method,params){const id=next++;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(Error('MCP timeout '+method))},60000);pending.set(id,{resolve,reject,timer});child.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n')})}
async function call(name,args){const r=await send('tools/call',{name,arguments:args});const t=r.content?.find(x=>x.type==='text');assert(t,'MCP text response required');const v=JSON.parse(t.text);assert.equal(v.success,true,JSON.stringify(v.error));return v.data}
try{
 await send('initialize',{protocolVersion:'2025-06-18',capabilities:{},clientInfo:{name:'stealthcdp-updater-acceptance',version:'1'}});
 child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n');
 receipt.phase='open_requested';save();
 task=await call('browser_open',{profileMode:'disposable',taskKey:receipt.taskKey,url:'about:blank',serviceName:'chromium-stealthcdp',agentName:'stealthcdp-updater',taskName:'Verify fresh managed browser executable after update'});
 receipt.task=task;receipt.phase='opened';save();assert(task.taskId&&task.profileId);
 const found=await until(()=>{const rows=browsers().filter(p=>basename(p.profile)===task.profileId&&!p.argv.includes('--type='));assert(rows.length<=1,'Ambiguous managed browser identity');return rows[0]},'exact managed browser process');
 profile=found.profile;receipt.browserPid=found.pid;receipt.browserExecutable=found.executable;receipt.browserSha256=hash('/proc/'+found.pid+'/exe');save();
 assert.equal(receipt.browserSha256,expected,'Managed MCP launched a different executable');receipt.phase='accepted';
}catch(error){receipt.error=error.stack;receipt.phase='failed';process.exitCode=1}
finally{
 try{
  if(task?.taskId){receipt.close=await call('browser_close',{taskId:task.taskId,reason:'Fresh managed updater acceptance complete'});assert.equal(receipt.close.closed,true);if(!profile&&task.profileId){await until(()=>!browsers().some(p=>basename(p.profile)===task.profileId),'owned profile writers exit');receipt.profileWritersGone=true}else if(profile){await until(()=>!browsers().some(p=>p.profile===profile),'owned profile writers exit');receipt.profileWritersGone=true}}
  receipt.success=receipt.phase==='accepted'&&receipt.profileWritersGone===true;
 }catch(error){receipt.cleanupError=error.stack;receipt.success=false;process.exitCode=1}
 receipt.phase=receipt.success?'accepted_closed':receipt.phase;receipt.finishedAt=new Date().toISOString();save();
 fail(Error('MCP client closing'));child.stdin.end();await Promise.race([new Promise(r=>child.once('exit',r)),delay(2000)]);if(child.exitCode===null&&child.signalCode===null)child.kill('SIGTERM');
 console.log(JSON.stringify({success:receipt.success,browserSha256:receipt.browserSha256,profileWritersGone:receipt.profileWritersGone,receipt:join(root,'result.json')}));
}

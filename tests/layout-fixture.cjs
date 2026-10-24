const assert=require('node:assert/strict'),fs=require('node:fs'),{spawn,execFileSync}=require('node:child_process'),readline=require('node:readline');
const {JSDOM,VirtualConsole}=require('jsdom');
const python=process.env.CODEX_PRIMARY_RUNTIME_PYTHON||'python3';
const raw=execFileSync(python,['-c',`import ast;from pathlib import Path;t=ast.parse(Path('Electricity-circuit.py').read_text());print(next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(getattr(a,'id','')=='APP_HTML' for a in n.targets)))`],{encoding:'utf8'});
const start=Date.parse('2099-10-23T17:00:00+03:00'),end=start+90000000;
let now=start-86400000;
const intervals=[{start:new Date(start).toISOString(),end:new Date(end).toISOString()},{start:new Date(start+7*86400000).toISOString(),end:new Date(end+7*86400000).toISOString()}];
const html=raw.replace('/* COURSE_EXTENSION */',['course_practice.js','courses.js','learning_tools.js'].map(p=>fs.readFileSync(p,'utf8')).join('\n')).replace('/* SHABBAT_FALLBACK */[]',JSON.stringify(intervals)).replace('/* SHABBAT_METADATA */null',JSON.stringify({generated_at:'2099-10-20T12:00:00Z'}));
const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!e.message.includes('CSS stylesheet'))errors.push(e.message);});
const dom=new JSDOM(html,{url:'https://unit.test/',runScripts:'outside-only',virtualConsole:vc}),w=dom.window,d=w.document;
w.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});w.requestAnimationFrame=()=>0;w.cancelAnimationFrame=()=>{};w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=()=>{};
w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'));};
w.Date.now=()=>now;
w.localStorage.setItem('dc.basics.personal.v1',JSON.stringify({version:1,profile:{name:'UX tests',birth:'1990-01-01',termsVersion:'2026-10-14.1'},preferences:{textScale:100,theme:'light',motion:false},sessions:[],topics:{},totals:{}}));
const child=spawn(python,['tests/course_bridge.py'],{stdio:['pipe','pipe','inherit']});
const dispatch=reply=>w.dispatchEvent(new w.MessageEvent('message',{source:w,data:{type:'streamlit:render',args:{course_config:{names:{hvac:'קורס מיזוג וקירור',security:'קורס מיגון',mobile:'קורס סלולר'}},course_response:reply}}}));
readline.createInterface({input:child.stdout}).on('line',line=>dispatch(JSON.parse(line)));
w.postMessage=message=>{if(message.type==='streamlit:setComponentValue'&&message.value.type==='course')child.stdin.write(JSON.stringify(message.value)+'\n');};
w.eval([...d.querySelectorAll('script')].map(n=>n.textContent).join('\n')+'\nwindow.uxState={profile:()=>personal};');dispatch();
const click=s=>{assert.ok(d.querySelector(s),'Missing '+s);d.querySelector(s).click();};
const change=(s,value)=>{const n=d.querySelector(s);assert.ok(n,'Missing '+s);if(n.type==='checkbox')n.checked=value;else n.value=value;n.dispatchEvent(new w.Event('change',{bubbles:true}));};
const input=(s,value)=>{const n=d.querySelector(s);n.value=value;n.dispatchEvent(new w.Event('input',{bubbles:true}));};
const waitFor=async test=>{for(let n=0;n<100;n++){if(test())return;await new Promise(resolve=>setTimeout(resolve,20));}throw Error('Timed out');};
const openSettings=()=>click('[data-open-site-settings]'),closeSettings=()=>click('[data-close-dialog="site-settings-dialog"]');
async function layoutFixtures(){
 try{
  click('[data-select-course="security"]');click('[data-open-qa]');input('#qa-password','210592');d.querySelector('#qa-login-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await waitFor(()=>d.querySelector('#course-admin'));
  const frames=[];
  const capture=name=>{const copy=d.documentElement.cloneNode(true);copy.classList.add('ui-ready');copy.querySelectorAll('script,iframe,link,img').forEach(n=>n.remove());copy.querySelector('head').insertAdjacentHTML('afterbegin','<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;; img-src data:">');frames.push({name,html:'<!doctype html>'+copy.outerHTML});};
  for(const course of ['security','mobile','hvac']){
   change('#qa-course-switch',course);change('#qa-topic','ohm');capture(course+'-ohm');
   for(const topic of course==='security'?['mixed','battery']:course==='mobile'?['battery']:[]){
    change('#qa-topic',topic);capture(course+'-'+topic+'-closed');
    d.querySelector('#qa-tools').open=true;d.querySelector('#qa-tools').dispatchEvent(new w.Event('toggle'));
    for(let level=0;level<(course==='mobile'?2:3);level++){
     change('#qa-extra-level',String(level));
     for(let i=0;i<10;i++){
      change('#qa-extra-exercise',String(i));d.querySelector('#qa-tools').open=true;d.querySelector('#qa-tools').dispatchEvent(new w.Event('toggle'));const q=w.CourseApp.formulaQuestion();capture(course+'-'+topic+'-'+level+'-'+i);
      if(topic==='mixed'||q.unitFamily==='Rs'){
       click('[data-extra-action="solution"]');capture(course+'-'+topic+'-solution-'+level+'-'+i);click('[data-extra-action="solution"]');
       if(i===0&&topic==='mixed'){openSettings();change('#expanded-learning',true);closeSettings();click('[data-reduction-action="next"]');capture(course+'-mixed-walkthrough-'+level);openSettings();change('#expanded-learning',false);closeSettings();}
       if(i===0){change('#qa-topic','simulator');capture(course+'-'+topic+'-sim-'+level);click('[data-qa-focus]');}
      }
     }
    }
   }
  }
  assert.equal(errors.length,0,errors.join('\n'));return frames;
 }finally{child.kill();w.close();}
}
module.exports=layoutFixtures;
if(require.main===module)layoutFixtures().then(frames=>{fs.writeFileSync(process.argv[2],JSON.stringify(frames));console.log('Inert QA layout snapshots: '+frames.length);}).catch(error=>{console.error(error);process.exitCode=1;});
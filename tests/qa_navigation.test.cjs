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
w.eval([...d.querySelectorAll('script')].map(n=>n.textContent).join('\n')+'\nwindow.uxState={profile:()=>personal,simulatorMode:()=>simulatorMode,simulatorIsCurrent:()=>simulatorQuestion===currentQuestion()};');dispatch();
const click=s=>{assert.ok(d.querySelector(s),'Missing '+s);d.querySelector(s).click();};
const change=(s,value)=>{const n=d.querySelector(s);assert.ok(n,'Missing '+s);if(n.type==='checkbox')n.checked=value;else n.value=value;n.dispatchEvent(new w.Event('change',{bubbles:true}));};
const input=(s,value)=>{const n=d.querySelector(s);n.value=value;n.dispatchEvent(new w.Event('input',{bubbles:true}));};
const waitFor=async test=>{for(let n=0;n<100;n++){if(test())return;await new Promise(resolve=>setTimeout(resolve,20));}throw Error('Timed out');};
const openSettings=()=>click('[data-open-site-settings]'),closeSettings=()=>click('[data-close-dialog="site-settings-dialog"]');
(async()=>{try{
 click('[data-select-course="security"]');const before=w.localStorage.getItem('dc.basics.personal.v1.security');
 click('[data-open-qa]');input('#qa-password','210592');d.querySelector('#qa-login-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await waitFor(()=>d.querySelector('#course-admin'));
 const categories=()=>[...d.querySelector('#qa-topic').options].map(n=>n.value);
 const nav=()=>{assert.equal(d.querySelectorAll('#qa-course-switch').length,1);assert.equal(d.querySelectorAll('#qa-topic').length,1);assert.ok(d.querySelector('.qa-navigation #qa-course-switch'));assert.ok(d.querySelector('.qa-navigation #qa-topic'));assert.equal(d.querySelector('#qa-course-switch').closest('#qa-tools'),null);assert.equal(d.querySelector('#qa-topic').closest('#qa-tools'),null);};
 nav();assert.deepEqual(categories(),['ohm','series','parallel','mixed','battery','simulator','formulas']);
 for(const topic of ['mixed','battery']){change('#qa-topic',topic);nav();assert.equal(w.CourseApp.formulaQuestion().kind,topic);if(topic==='battery')for(let i=0;i<10;i++){change('#qa-extra-exercise',String(i));if(w.CourseApp.formulaQuestion().unitFamily==='Rs')break;}assert.equal(d.querySelector('#qa-topic').value,topic);assert.ok(d.querySelector('#qa-extra-exercise'));change('#qa-extra-step','1');assert.equal(w.CourseApp.formulaQuestion().cursor,1);if(topic==='battery')continue;change('#qa-topic','simulator');assert.ok(d.querySelector('#course-simulator'));assert.equal(d.querySelector('#qa-topic').value,'simulator');click('[data-qa-focus]');assert.equal(w.CourseApp.formulaQuestion().simulatorOpen,false);assert.equal(d.querySelector('#qa-topic').value,topic);}
 change('#qa-topic','formulas');assert.ok(d.querySelector('.course-formula-page'));assert.ok(d.querySelector('#formula-dialog').open);click('[data-close-dialog="formula-dialog"]');click('[data-qa-focus]');assert.equal(d.querySelector('#qa-topic').value,'battery');
 for(const topic of ['ohm','series','parallel']){change('#qa-topic',topic);assert.equal(d.querySelector('#qa-topic').value,topic);assert.equal(d.querySelector('#qa-level').closest('.qa-selectors').hidden,false);nav();}
 change('#qa-course-switch','mobile');nav();assert.deepEqual(categories(),['ohm','series','parallel','battery','simulator','formulas']);assert.ok(d.querySelector('#qa-topic option[value="battery"]').textContent.includes('התנגדות פנימית'));change('#qa-topic','battery');assert.equal(w.CourseApp.formulaQuestion().kind,'battery');
 change('#qa-course-switch','hvac');nav();assert.deepEqual(categories().filter(Boolean),['ohm','series','parallel','simulator','formulas','theory']);assert.equal(d.querySelector('#qa-topic').value,'','Menu must not pretend to show a practice exercise');change('#qa-topic','theory');await waitFor(()=>d.querySelector('.theory-question'));assert.equal(d.querySelector('#qa-topic').value,'theory');nav();change('#qa-topic','parallel');assert.equal(d.querySelector('#qa-topic').value,'parallel');change('#qa-topic','simulator');assert.equal(d.querySelector('#qa-topic').value,'simulator');assert.equal(d.querySelector('#simulator-section').hidden,false);assert.equal(w.uxState.simulatorMode(),'exercise');assert.equal(w.uxState.simulatorIsCurrent(),true,'QA simulator opens the selected exercise');
 change('#qa-course-switch','security');change('#qa-topic','mixed');click('[data-exit-qa]');assert.equal(w.localStorage.getItem('dc.basics.personal.v1.security'),before,'QA course and topic navigation never changes saved progress');
 assert.equal(errors.length,0,errors.join('\n'));console.log('QA navigation: course-specific categories, visible course/topic controls, all routes, simulation bypass, theory, focus and progress isolation passed');
}finally{child.kill();w.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
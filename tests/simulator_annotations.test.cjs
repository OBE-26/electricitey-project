const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {JSDOM}=require('jsdom'),practice=require('../course_practice.js');
const source=fs.readFileSync('Electricity-circuit.py','utf8');
const dc=source.slice(source.indexOf('const DC = (() => {'),source.indexOf('\nfunction circuitSVG('));
const renderers=source.slice(source.indexOf('function circuitSVG('),source.indexOf('\nconst $ ='));
const conversions=source.slice(source.indexOf('const units ='),source.indexOf('\nfunction unitNote('));
const formats=source.slice(source.indexOf('function formatCustomNumber('),source.indexOf('\nfunction customBuilderHTML('));
const context=vm.createContext({CoursePractice:practice});
vm.runInContext(dc+'\n'+renderers+'\n'+conversions+'\n'+formats+'\nthis.test={DC,circuitSVG,customCircuitSVG};',context);
const {DC,circuitSVG,customCircuitSVG}=context.test,document=new JSDOM('').window.document;
const close=(a,b,message)=>assert.ok(Math.abs(a-b)<=1e-10*Math.max(1,Math.abs(b)),message??`${a} != ${b}`);
const capture=(name,svg)=>{if(process.env.SIM_CAPTURE_DIR){fs.mkdirSync(process.env.SIM_CAPTURE_DIR,{recursive:true});fs.writeFileSync(path.join(process.env.SIM_CAPTURE_DIR,name+'.svg'),svg);}};
function check(svg,expected,number=practice.simulationNumber){
 const box=document.createElement('div');box.innerHTML=svg;
 const components=[...box.querySelectorAll('.sim-component')];assert.equal(components.length,expected.length);
 for(const e of expected){
  const node=box.querySelector(`.sim-component[data-component="${e.id}"]`);assert.ok(node,e.id);
  for(const [key,value] of Object.entries({resistance:e.r,current:e.i,voltage:e.u}))close(Number(node.dataset[key]),value,`${e.id} ${key}`);
  for(const [selector,value,unit,color] of [['.sim-resistance',e.r,e.ru,'#fff'],['.sim-current',e.i,e.iu,'#ff6565'],['.sim-voltage-drop',e.u,e.uu??'V','#65e680']]){
   const group=node.querySelector(selector),label=group.querySelector('text:last-child');assert.ok(group);
   assert.ok(label.textContent.endsWith(`= ${number(value)} ${unit}`),label.textContent);
   assert.equal(label.getAttribute('fill'),color);
   if(value===0||Math.abs(value)>=(number===practice.milliSimulationNumber?.5:.00005))assert.ok(!/\d+\.\d{5}/.test(label.textContent),'Four decimal places except tiny nonzero values');
   if(selector!=='.sim-resistance'){
    const arrow=group.querySelector('path.sim-arrow');assert.ok(arrow,'Directional arrow alongside the value');assert.equal(arrow.getAttribute('stroke'),color);
   }
  }
  assert.ok(node.querySelector('.sim-voltage-drop').textContent.includes('+'));
  assert.ok(node.querySelector('.sim-voltage-drop').textContent.includes('−'));
  const endpoints=selector=>{
   const [,x1,y1,x2,y2]=/^M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)/.exec(node.querySelector(selector+' .sim-arrow').getAttribute('d')).map(Number);
   return {x1,y1,x2,y2,dx:x2-x1,dy:y2-y1};
  };
  const current=endpoints('.sim-current'),voltage=endpoints('.sim-voltage-drop');
  assert.ok(current.dx*voltage.dx+current.dy*voltage.dy<0,'Voltage reference arrow opposes the current arrow');
  const polarity=sign=>[...node.querySelectorAll('.sim-voltage-drop text')].find(t=>t.textContent===sign);
  const distance=sign=>Math.hypot(voltage.x2-Number(polarity(sign).getAttribute('x')),voltage.y2-Number(polarity(sign).getAttribute('y')));
  assert.ok(distance('+')<distance('−'),'Voltage arrowhead points toward the positive terminal');
 }
 return box;
}
// Each course, kind, level, scaled unit and source voltage uses the real renderer.
for(const profile of ['hvac','security','mobile']){
 const course=DC.course(42,[],profile);
 for(const kind of DC.kinds)for(const questions of course[kind])for(const q of [questions[0],questions.at(-1)]){
  assert.ok(!circuitSVG(q).includes('sim-component'),'Practice diagrams do not reveal answers');
  for(const ratio of [0,.5,1]){
   const voltage=q.voltage*ratio,totalR=q.resistances.reduce((a,b)=>a+b,0),scale=q.resistanceScale??1;
   const expected=q.resistances.map((r,i)=>{
    const current=kind==='parallel'?voltage/r:voltage/totalR;
    return {id:'R'+(i+1),r:r/scale,i:current*scale,u:current*r,ru:q.units.R,iu:q.units.I};
   });
   check(circuitSVG(q,{complete:true,voltage}),expected);
  }
 }
}
for(const kind of ['series','parallel'])for(const count of [1,2,3,6]){
 const resistances=Array.from({length:count},(_,i)=>i+1.23456789),q={custom:true,kind,voltage:24.123456,resistances,lamps:resistances.map(()=>false),givens:{}};
 const expected=resistances.map((r,i)=>{const current=kind==='parallel'?q.voltage/r:q.voltage/resistances.reduce((a,b)=>a+b,0);return {id:'R'+(i+1),r,i:current,u:current*r,ru:'Ω',iu:'A'};});
 const svg=customCircuitSVG(q,{complete:true});check(svg,expected);
 if(count===3)capture(kind,svg);
 if(count===6&&kind==='parallel')capture('custom-six-branches',svg);
}
// Compute branch currents independently from each topology, including R6's return direction.
for(const level of [0,1,2])for(const q of practice.batch('security','mixed',level,42)){
 assert.ok(!practice.mixedSVG(q).includes('sim-component'));
 const equivalents=q.groups.map(g=>1/g.branches.reduce((sum,branch)=>sum+1/branch.reduce((r,i)=>r+q.r[i],0),0));
 for(const ratio of [0,.5,1]){
  const total=q.u*ratio/equivalents.reduce((a,b)=>a+b,0),expected=[];
  q.groups.forEach((g,gi)=>g.branches.forEach(branch=>{
   const current=total*equivalents[gi]/branch.reduce((r,i)=>r+q.r[i],0);
   branch.forEach(i=>expected.push({id:'R'+(i+1),r:q.r[i],i:current,u:current*q.r[i],ru:q.resistanceUnit,iu:q.currentUnit}));
  }));
  const simQ={...q,u:q.u*ratio,it:q.it*ratio,currents:q.currents.map(i=>i*ratio),voltages:q.voltages.map(u=>u*ratio)};
  const svg=practice.mixedSVG(simQ,0,false,true),box=check(svg,expected);
  if(q.variant.startsWith('parallel-groups'))assert.ok(box.querySelector('[data-component="R6"] .sim-current path').getAttribute('d').startsWith('M892 440L866 440'),'Return branch current flows right to left');
  if(ratio===0)assert.equal(box.querySelectorAll('.mixed-current-flow').length,0,'Zero voltage has no moving current');
  if(level===1&&ratio===1)capture(q.variant,svg);
 }
}
for(const whole of [false,true]){
 const q=practice.internalResistance(practice.random(41),1,0,whole),g=Object.fromEntries(q.givens.map(([key,value])=>[key,value]));
 const load=g.U_L/g.I;
 for(const ratio of [0,.5,1])for(const rs of [0,q.rs,whole?2000:2]){
  const voltage=g.U_t*ratio,current=voltage*(whole?.001:1)/((rs+load)*(whole?.001:1)),drop=current*rs,ul=current*load;
  const simQ={...q,rs,simCurrentUnit:whole?'mA':'A',simLoadResistance:load,givens:[['U_t',voltage],['U_L',ul],['I',current]],simAnimate:ratio!==.5};
  const svg=practice.phoneBatterySVG(simQ,true),box=check(svg,[{id:'R_s',r:rs,i:current*(whole?1000:1),u:drop,ru:q.resistanceUnit,iu:whole?'mA':'A',uu:q.voltageUnit},{id:'R_L',r:load,i:current*(whole?1000:1),u:ul,ru:q.resistanceUnit,iu:whole?'mA':'A',uu:q.voltageUnit}],whole?practice.milliSimulationNumber:practice.simulationNumber);
  close(Number(box.querySelector('.phone-current-flow').dataset.current),current);
  if(!whole&&ratio===1&&rs===q.rs)capture('phone-internal',svg);
 }
}
console.log('Simulator annotations: all courses, basic and custom entry points, every mixed topology, per-component currents/resistances, voltage arrows, zero source, units and four-decimal labels passed');

const examples=[
 [0,'0'],[1.234567,'1.2346'],[.000001,'0.000001'],[.000000123456,'0.0000001235'],[-.000001,'-0.000001']
];
for(const [value,text] of examples)assert.equal(practice.simulationNumber(value),text);
for(const [value,text] of [[0,'0'],[4200,'4200'],[1234.567,'1235'],[9999.49,'9999'],[9999.5,'1 × 10⁴'],[12345.6,'1235 × 10¹'],[175000,'175 × 10³'],[.001,'0.001'],[.000001,'0.000001'],[-.001,'-0.001']])assert.equal(practice.milliSimulationNumber(value),text);
// One microamp remains visible in both units, exactly as requested.
for(const milli of [false,true]){
 const tiny={rs:milli?1000:1,voltageUnit:milli?'mV':'V',resistanceUnit:milli?'mΩ':'Ω',simCurrentUnit:milli?'mA':'A',simLoadResistance:milli?1000:1,givens:[['U_t',milli?.002:.000002],['U_L',milli?.001:.000001],['I',.000001]]};
 check(practice.phoneBatterySVG(tiny,true),[
  {id:'R_s',r:tiny.rs,i:milli?.001:.000001,u:milli?.001:.000001,ru:tiny.resistanceUnit,iu:tiny.simCurrentUnit,uu:tiny.voltageUnit},
  {id:'R_L',r:tiny.simLoadResistance,i:milli?.001:.000001,u:milli?.001:.000001,ru:tiny.resistanceUnit,iu:tiny.simCurrentUnit,uu:tiny.voltageUnit}
 ],milli?practice.milliSimulationNumber:practice.simulationNumber);
 if(milli)capture('tiny-milli',practice.phoneBatterySVG(tiny,true));
}
console.log('Display precision: integer milli values, compact large quantities and nonzero micro quantities in both modes passed');

const microBasic={custom:true,kind:'series',voltage:.000001,resistances:[1],lamps:[false],givens:{}};
check(customCircuitSVG(microBasic,{complete:true}),[{id:'R1',r:1,i:.000001,u:.000001,ru:'Ω',iu:'A'}]);

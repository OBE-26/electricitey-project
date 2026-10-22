const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('Electricity-circuit.py','utf8');
const dc=source.slice(source.indexOf('const DC = (() => {'),source.indexOf('\nfunction circuitSVG('));
const context=vm.createContext({});vm.runInContext(dc+'\nthis.DC=DC;',context);const DC=context.DC;
const practice=require('../course_practice.js');
for(let seed=1;seed<=60;seed++){
 for(const profile of ['hvac','security','mobile']){
  const course=DC.course(seed,[],profile);
  for(const kind of DC.kinds){
   assert.equal(course[kind].length,profile==='mobile'?2:3);
   for(const [level,questions] of course[kind].entries()){
    const direct=questions.filter(q=>q.powerResistance);
    assert.equal(direct.length,profile==='hvac'&&kind==='ohm'&&level<2?9:0);
    if(kind==='parallel')assert.equal(questions.filter(q=>q.resistances.every(r=>r===q.resistances[0])).length,3);
    for(const q of questions){
     if(profile==='mobile'&&kind==='parallel')assert.equal(q.resistances.length,2);
     if(level===1){assert.ok(q.resistances.every(Number.isInteger));assert.ok(Number.isInteger(q.voltage));}
     if(q.powerResistance){assert.equal(q.steps[0].key,'R');assert.ok(Math.abs(q.givens.U*q.givens.U/q.givens.P-q.steps[0].value)<1e-7);}
     if(level===0)assert.ok(q.steps.every(s=>Math.abs(s.value-Math.round(s.value))<1e-7));
     assert.ok(q.steps.every(s=>Number.isFinite(s.value)&&s.value>0));
    }
   }
  }
 }
 for(const level of [0,1,2]){
  const mixed=practice.batch('security','mixed',level,seed);
  for(const q of mixed){
   assert.ok(Math.abs(q.rp-(1/q.r.reduce((a,r)=>a+1/r,0)))<1e-8);
   assert.ok(Math.abs(q.up+q.u4-q.u)<1e-8);
   assert.ok(Math.abs(q.branch.reduce((a,b)=>a+b,0)-q.it)<1e-8);
   if(level===0)assert.ok(q.steps.every(s=>Math.abs(s.value-Math.round(s.value))<1e-7));
  }
  const security=practice.batch('security','battery',level,seed);
  assert.equal(security.filter(q=>q.unitFamily==='Ah').length,7);
  assert.equal(security.filter(q=>q.unitFamily==='Wh').length,3);
  const mobile=practice.batch('mobile','battery',level,seed);
  assert.equal(mobile.filter(q=>q.unitFamily==='Wh').length,0);
  assert.equal(mobile.filter(q=>q.unitFamily==='Rs').length,3);
  for(const q of [...security,...mobile])assert.ok(q.steps.every(s=>Number.isFinite(s.value)&&s.value>0));
 }
}
console.log('Practice generators: 60 seeds, all courses and levels passed');

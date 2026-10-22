const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('Electricity-circuit.py','utf8');
const dc=source.slice(source.indexOf('const DC = (() => {'),source.indexOf('\nfunction circuitSVG('));
const context=vm.createContext({});vm.runInContext(dc+'\nthis.DC=DC;',context);const DC=context.DC;
const practice=require('../course_practice.js');
const close=(a,b,message)=>assert.ok(Math.abs(a-b)<1e-7*Math.max(1,Math.abs(b)),message??`${a} != ${b}`);
// Independent nodal analysis checks both the original circuit and every
// reduction, including shared parallel endpoints and retained node letters.
function solveNetwork(edges,positive,negative,voltage){
 const known={[positive]:voltage,[negative]:0};
 const unknown=[...new Set(edges.flatMap(e=>[e.from,e.to]))].filter(n=>!(n in known));
 const matrix=unknown.map(()=>Array(unknown.length+1).fill(0));
 for(const [row,n] of unknown.entries())for(const e of edges){
  if(e.from!==n&&e.to!==n)continue;
  const other=e.from===n?e.to:e.from,g=1/e.value;
  matrix[row][row]+=g;
  if(other in known)matrix[row][unknown.length]+=g*known[other];
  else matrix[row][unknown.indexOf(other)]-=g;
 }
 for(let column=0;column<unknown.length;column++){
  const pivot=matrix[column][column];assert.ok(Math.abs(pivot)>1e-12,'Connected network');
  for(let j=column;j<=unknown.length;j++)matrix[column][j]/=pivot;
  for(let i=0;i<unknown.length;i++)if(i!==column){const scale=matrix[i][column];for(let j=column;j<=unknown.length;j++)matrix[i][j]-=scale*matrix[column][j];}
 }
 unknown.forEach((n,i)=>known[n]=matrix[i][unknown.length]);
 const current=edges.reduce((sum,e)=>e.from===positive?sum+(voltage-known[e.to])/e.value:e.to===positive?sum+(voltage-known[e.from])/e.value:sum,0);
 return {voltages:known,current,resistance:voltage/current};
}
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
  assert.equal(mixed.filter(q=>q.family==='series-parallel').length,5);
  assert.equal(mixed.filter(q=>q.family==='parallel-series').length,5);
  assert.equal(new Set(mixed.map(q=>q.variant)).size,6);
  for(const q of mixed){
   assert.equal(q.diagrams.length,3);assert.equal(q.reductions.length,2);
   const solve=edges=>solveNetwork(edges,'A',q.groups.at(-1).to,q.u);
   const original=solve(q.diagrams[0].flat(2));
   close(original.resistance,q.rt);close(original.current,q.it);
   for(const [i,nodes] of q.resistorNodes.entries()){
    assert.notEqual(nodes.from,nodes.to,'A resistor separates distinct nodes');
    close(original.voltages[nodes.from]-original.voltages[nodes.to],q.voltages[i]);
    close(q.voltages[i]/q.r[i],q.currents[i]);
    close(q.voltages[i]*q.currents[i],q.powers[i]);
    for(const key of ['I','U','P'])assert.ok(q.steps.some(s=>s.key===key+(i+1)),'Every resistor has I,U,P');
   }
   close(q.powers.reduce((a,b)=>a+b,0),q.u*q.it,'Conservation of power');
   for(const group of q.groups)for(const branch of group.branches){
    assert.equal(q.resistorNodes[branch[0]].from,group.from,'All parallel branches share the first endpoint');
    assert.equal(q.resistorNodes[branch.at(-1)].to,group.to,'All parallel branches share the second endpoint');
   }
   q.diagrams.forEach((diagram,stage)=>{
    close(solve(diagram.flat(2)).resistance,q.rt,'Each reduction preserves terminal resistance');
    assert.ok(!practice.mixedSVG(q,stage).includes('data-node='),'Question schematics have no node markings');
    const svg=practice.mixedSVG(q,stage,true);
    for(const node of new Set(diagram.flat(2).flatMap(e=>[e.from,e.to])))assert.ok(svg.includes(`data-node="${node}"`),'Display every surviving node '+node);
    for(const e of diagram.flat(2))assert.ok(svg.includes(`data-symbol="${e.symbol}" data-from="${e.from}" data-to="${e.to}"`));
   });
   assert.ok(q.steps.every(s=>Number.isFinite(s.value)&&s.value>0));
   assert.equal(new Set(q.steps.map(s=>s.key)).size,q.steps.length,'Each requested quantity appears once');
   if(level===0)assert.ok(q.steps.every(s=>Math.abs(s.value-Math.round(s.value))<1e-7));
   if(level===1)assert.ok(q.givens.every(([,value])=>Number.isInteger(value)));
   if(level===2){assert.ok(['kΩ','MΩ'].includes(q.resistanceUnit));assert.equal(q.powerUnit,q.currentUnit==='mA'?'mW':'μW');}
  }
  const security=practice.batch('security','battery',level,seed);
  assert.equal(security.filter(q=>q.unitFamily==='Ah').length,7);
  assert.equal(security.filter(q=>q.unitFamily==='Wh').length,3);
  const mobile=practice.batch('mobile','battery',level,seed);
  assert.equal(mobile.filter(q=>q.unitFamily==='Wh').length,0);
  assert.equal(mobile.filter(q=>q.unitFamily==='Rs').length,3);
  for(const batch of [security,mobile]){
   const integral=batch.filter(q=>q.givens.every(([,value])=>Number.isInteger(value))&&q.steps.every(s=>Number.isInteger(s.value)));
   assert.equal(integral.length,7,'Exactly 70% integral questions in every batch and level');
   assert.ok(integral.every(q=>q.steps.every(s=>s.value>=2&&s.value<=10)),'Integral answers are 2–10');
   assert.ok(batch.filter(q=>q.steps.some(s=>s.value===1)).length<=2,'At most 20% with answer 1');
   const fractional=batch.filter(q=>!integral.includes(q));
   assert.equal(fractional.length,3);
   assert.ok(fractional.every(q=>q.steps.some(s=>!Number.isInteger(s.value))),'Every fractional question has a fractional answer');
   assert.ok(fractional.some(q=>q.steps.some(s=>s.key==='t_h')),'Minutes to fractional hours');
   assert.ok(fractional.some(q=>q.steps.some(s=>s.key==='t_minutes')&&q.steps.some(s=>s.key==='t_remainder')),'Fractional hours to hours and minutes');
   for(const q of batch){
    assert.equal(q.schemaVersion,3);
    const given=Object.fromEntries(q.givens.map(([key,value,unit])=>[key,unit==='min'?value/60:value]));
    const primary=q.steps.find(s=>['Q','I','t','E','R_s'].includes(s.key));
    if(q.unitFamily==='Rs'){
     const drop=given.U_t-given.U_L;close(q.steps[0].value,drop);close(primary.value,drop/given.I);
     assert.equal(q.steps[1].unit,q.givens[0][2]==='mV'?'mΩ':'Ω');
    }else{
     const expected={Q:()=>given.E!==undefined?given.E/given.U:given.I*given.t,I:()=>given.Q/given.t,t:()=>given.E!==undefined?given.E/given.P:given.Q/given.I,E:()=>given.P*given.t};
     close(primary.value,expected[primary.key](),'Solve from the displayed givens, including time conversion');
    }
   }
  }
  for(const q of [...security,...mobile])assert.ok(q.steps.every(s=>Number.isFinite(s.value)&&s.value>0));
  for(const q of mobile.filter(q=>q.unitFamily==='Rs')){const svg=practice.phoneBatterySVG(q);assert.ok(svg.includes('phone-battery-svg'));assert.ok(svg.includes('מעגלי הטלפון'));assert.ok(svg.includes(' = ?'));assert.ok(svg.includes('dy="5"'));}
 }
}
console.log('Practice generators: 60 seeds, all courses and levels passed');

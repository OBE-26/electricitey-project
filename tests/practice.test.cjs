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
  assert.equal(new Set(mixed.map(q=>q.variant)).size,7,'Seven mixed-circuit variants in the current generator');
  const worksheet=mixed.find(q=>q.variant==='parallel-groups-worksheet');
  assert.ok(worksheet,'Preserve the six-resistor circuit from worksheet exercise 15');
  assert.deepEqual(worksheet.groups.map(g=>g.branches),[[[0],[1]],[[2]],[[3],[4]],[[5]]]);
  if(level===1){assert.equal(worksheet.u,45);assert.deepEqual(worksheet.r,[15,10,3,6,12,5]);close(worksheet.rt,18);close(worksheet.it,2.5);}
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
  for(const q of [...security,...mobile])assert.ok(q.steps.every(s=>Number.isFinite(s.value)&&s.value>0));
  for(const q of mobile.filter(q=>q.unitFamily==='Rs')){
   const svg=practice.phoneBatterySVG(q);assert.ok(svg.includes('phone-battery-svg'));assert.ok(svg.includes('מעגלי הטלפון'));assert.ok(svg.includes(' = ?'));assert.ok(svg.includes('dy="5"'));
   assert.ok(!svg.includes('phone-current-flow'),'Exercise diagrams stay static and hide unknown answers');
   const simulated=practice.phoneBatterySVG(q,true);assert.ok(simulated.includes('phone-current-flow'));assert.ok(!simulated.includes(' = ?'),'Simulator shows the calculated internal resistance and voltage drop');
  }
 }
}
console.log('Practice generators: 60 seeds, all courses and levels passed');

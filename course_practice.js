/* Pure generators: displayed units form one coherent unit system. */
const CoursePractice = (() => {
  const pick = (rng, list) => list[Math.floor(rng() * list.length)];
  const integer = (rng, lo, hi) => lo + Math.floor(rng() * (hi - lo + 1));
  const fmt = value => String(Math.round((value + Number.EPSILON) * 100) / 100);
  // Display the same rounded physical quantity in every unit scale. Leading
  // zeros do not count; the physics model keeps its full calculation precision.
  const simulationFormat=new Intl.NumberFormat('en-US',{useGrouping:false,maximumSignificantDigits:4});
  const simulationNumber=value=>simulationFormat.format(value).replace(/^-0$/,'0');
  const milliSimulationNumber=simulationNumber;
  const step = (key, label, unit, value, formula, substitution) => ({key,label,unit,value,formula,substitution});
  const integralBatteryIndices=[0,1,2,3,5,7,8];
  function random(seed) {
    let value=seed>>>0;
    return ()=>{value+=0x6D2B79F5;let t=value;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};
  }
  // Both families from the supplied worksheet: series of parallel groups,
  // and parallel branches containing series resistors. Indices preserve R1..Rn.
  const mixedVariants = [
    {id:'series-parallel-2',family:'series-parallel',title:'נגד בטור לשני נגדים במקביל',r:[2,6,3],groups:[[[0]],[[1],[2]]]},
    {id:'parallel-series',family:'parallel-series',title:'נגד במקביל לענף עם שני נגדים בטור',r:[6,2,4],groups:[[[0],[1,2]]]},
    {id:'series-parallel-3',family:'series-parallel',title:'נגד בטור לשלושה נגדים במקביל',r:[5,20,40,40],groups:[[[0]],[[1],[2],[3]]]},
    {id:'two-series-branches',family:'parallel-series',title:'שני ענפים מקבילים עם שני נגדים בטור בכל ענף',r:[2,4,1,2],groups:[[[0,1],[2,3]]]},
    {id:'series-parallel-4',family:'series-parallel',title:'נגד בטור לארבעה נגדים במקביל',r:[2,12,12,12,12],groups:[[[0]],[[1],[2],[3],[4]]]},
    {id:'parallel-series',family:'parallel-series',title:'נגד במקביל לענף עם שני נגדים בטור',r:[6,2,4],groups:[[[0],[1,2]]]},
    {id:'parallel-groups',family:'series-parallel',title:'שתי קבוצות מקבילות ונגדים בטור',r:[6,3,2,4,4,2],groups:[[[0],[1]],[[2]],[[3],[4]],[[5]]]},
    {id:'two-series-branches',family:'parallel-series',title:'שני ענפים מקבילים עם שני נגדים בטור בכל ענף',r:[2,4,1,2],groups:[[[0,1],[2,3]]]},
    {id:'parallel-groups-worksheet',family:'series-parallel',title:'שתי קבוצות מקבילות עם נגד ביניהן ונגד בטור בתחתית',r:[6,3,2,4,4,2],worksheetR:[15,10,3,6,12,5],groups:[[[0],[1]],[[2]],[[3],[4]],[[5]]]},
    {id:'parallel-series',family:'parallel-series',title:'נגד במקביל לענף עם שני נגדים בטור',r:[6,2,4],groups:[[[0],[1,2]]]}
  ];
  function mixed(rng, level, index) {
    const variant=mixedVariants[index%mixedVariants.length],k=integer(rng,1,4);
    const worksheet=level===1&&!!variant.worksheetR;
    const r=worksheet?variant.worksheetR.slice():variant.r.map(value=>level===1?integer(rng,2,60):value*k);
    const resistanceUnit=level===2?(index%2?'MΩ':'kΩ'):'Ω';
    const currentUnit=level===2?(index%2?'μA':'mA'):'A',powerUnit=level===2?(index%2?'μW':'mW'):'W';
    const total=values=>values.reduce((sum,value)=>sum+value,0);
    const symbol=members=>'R'+members.map(i=>i+1).join('');
    const groups=variant.groups.map(branches=>{
      const sums=branches.map(branch=>total(branch.map(i=>r[i])));
      return {branches,sums,resistance:1/total(sums.map(value=>1/value)),symbol:symbol(branches.flat())};
    });
    let nextNode=1,startNode='A';const resistorNodes=Array(r.length);
    const allocateNode=()=>String.fromCharCode(65+nextNode++);
    groups.forEach(g=>{
      let endNode;
      g.branches.forEach(branch=>{
        let from=startNode;
        branch.forEach((i,ri)=>{
          const to=ri<branch.length-1?allocateNode():(endNode??=allocateNode());
          resistorNodes[i]={from,to};from=to;
        });
      });
      g.from=startNode;g.to=endNode;startNode=endNode;
    });
    const rt=total(groups.map(g=>g.resistance));
    // Structured values give integral answers (including per-resistor power) in A.
    const itBase=variant.id==='series-parallel-3'?4:variant.id==='series-parallel-4'?4:variant.id.startsWith('parallel-groups')?6:variant.id==='parallel-series'?2:3;
    const u=worksheet?45:level===1?integer(rng,12,60):rt*itBase*integer(rng,1,2),it=u/rt;
    const currents=Array(r.length),voltages=Array(r.length),powers=Array(r.length),steps=[],reductions=[];
    const original=groups.map(g=>g.branches.map(branch=>branch.map(i=>({symbol:'R'+(i+1),value:r[i],members:[i],...resistorNodes[i]}))));
    const diagrams=[original];
    const nodes=original.map(group=>group.map(branch=>branch.map(node=>({...node}))));
    const resistanceStep=(key,label,value,formula,substitution)=>{const s=step(key,label,resistanceUnit,value,formula,substitution);steps.push(s);return s;};
    const seriesSteps=[];
    groups.forEach((g,gi)=>g.branches.forEach((branch,bi)=>{
      if(branch.length<2)return;
      const key=symbol(branch),parts=branch.map(i=>'R'+(i+1));
      seriesSteps.push(resistanceStep(key,'צמצום הנגדים '+parts.join(', ')+' שבטור באותו ענף',g.sums[bi],`${key} = ${parts.join(' + ')}`,branch.map(i=>r[i]).join(' + ')));
      nodes[gi][bi]=[{symbol:key,value:g.sums[bi],members:branch,from:resistorNodes[branch[0]].from,to:resistorNodes[branch.at(-1)].to}];
    }));
    if(seriesSteps.length){
      reductions.push({title:'מצמצמים תחילה את הנגדים שבטור בתוך כל ענף',steps:seriesSteps});
      diagrams.push(JSON.parse(JSON.stringify(nodes)));
    }
    const parallelSteps=[];
    groups.forEach((g,gi)=>{
      if(g.branches.length===1)return;
      const parts=nodes[gi].map(branch=>branch[0].symbol),key=groups.length===1?'R_T':g.symbol;
      parallelSteps.push(resistanceStep(key,'ההתנגדות השקולה של '+parts.join(', ')+' במקביל',g.resistance,`${key} = 1 ÷ (${parts.map(part=>'1/'+part).join(' + ')})`,`1 ÷ (${g.sums.map(value=>'1/'+fmt(value)).join(' + ')})`));
      nodes[gi]=[[{symbol:key,value:g.resistance,members:g.branches.flat(),from:g.from,to:g.to}]];
    });
    reductions.push({title:'מצמצמים את הענפים המקבילים לנגד שקול',steps:parallelSteps});
    diagrams.push(JSON.parse(JSON.stringify(nodes)));
    if(groups.length>1){
      const totalStep=resistanceStep('R_T','ההתנגדות השקולה של כל המעגל',rt,`R_T = ${nodes.map(g=>g[0][0].symbol).join(' + ')}`,groups.map(g=>fmt(g.resistance)).join(' + '));
      reductions.push({title:'מחברים את הנגדים שנותרו בטור',steps:[totalStep]});
      diagrams.push([[[{symbol:'R_T',value:rt,members:r.map((_,i)=>i),from:'A',to:startNode}]]]);
    }
    steps.push(step('I_T','הזרם הכולל ממקור המתח',currentUnit,it,'I_T = U ÷ R_T',`${fmt(u)} ÷ ${fmt(rt)}`));
    groups.forEach(g=>{
      const groupU=it*g.resistance;
      const voltageSymbol=groups.length===1?'U':g.branches.length===1&&g.branches[0].length===1?'U'+(g.branches[0][0]+1):'U'+g.branches.flat().map(i=>i+1).join('');
      if(groups.length>1&&g.branches.length>1)steps.push(step(voltageSymbol,'המתח על '+g.symbol,'V',groupU,`${voltageSymbol} = I_T × ${g.symbol}`,`${fmt(it)} × ${fmt(g.resistance)}`));
      g.branches.forEach((branch,bi)=>{
        const current=groupU/g.sums[bi],first=branch[0];
        for(const i of branch){
          const currentSymbol='I'+(i+1),resistanceSymbol='R'+(i+1);
          const formula=g.branches.length===1?`${currentSymbol} = I_T`:i===first?`${currentSymbol} = ${voltageSymbol} ÷ ${symbol(branch)}`:`${currentSymbol} = I${first+1}`;
          const substitution=g.branches.length===1||i!==first?fmt(current):`${fmt(groupU)} ÷ ${fmt(g.sums[bi])}`;
          currents[i]=current;voltages[i]=current*r[i];powers[i]=voltages[i]*current;
          steps.push(step(currentSymbol,'הזרם בנגד '+resistanceSymbol,currentUnit,current,formula,substitution));
        }
      });
    });
    r.forEach((value,i)=>steps.push(step('U'+(i+1),'המתח על נגד R'+(i+1),'V',voltages[i],`U${i+1} = I${i+1} × R${i+1}`,`${fmt(currents[i])} × ${value}`)));
    r.forEach((value,i)=>steps.push(step('P'+(i+1),'ההספק המתפתח על נגד R'+(i+1),powerUnit,powers[i],`P${i+1} = U${i+1} × I${i+1}`,`${fmt(voltages[i])} × ${fmt(currents[i])}`)));
    return {kind:'mixed',schemaVersion:3,variant:variant.id,family:variant.family,level,index,title:variant.title,
      text:'חשבו את ההתנגדות הכללית, את הזרם מהמקור ואת הזרם, המתח וההספק בכל נגד.',
      caption:variant.family==='series-parallel'?'מתחילים בצמצום הקבוצות המקבילות, ואז מחברים את הנגדים שבטור.':'מתחילים בצמצום הנגדים שבטור בתוך הענפים, ואז מצמצמים את המקביל.',
      u,r,rt,it,groups,resistorNodes,currents,voltages,powers,resistanceUnit,currentUnit,powerUnit,steps,reductions,diagrams,
      givens:[['U',u,'V'],...r.map((value,i)=>['R'+(i+1),value,resistanceUnit])]};
  }
  function battery(rng, course, level, index) {
    // Seven integral exercises and three fractional exercises per batch,
    // independently of the topic split (Ah / Wh / internal resistance).
    const whole=integralBatteryIndices.includes(index%10);
    if(course==='mobile'&&index>=7)return internalResistance(rng,level,index,whole);
    const energy=course==='security'&&index>=7;
    const variant=index%3,charging=index%2===0,minutes=level===2||!whole;
    const currents=whole?Array.from({length:10},(_,i)=>i+1):[.2,.4,.5,.75,1.25,1.5,2.5];
    const times=whole?Array.from({length:9},(_,i)=>i+2):[1.25,1.5,1.75,2.25,2.5,2.75,3.5,4.5];
    const pairs=currents.flatMap(current=>times.map(hours=>({current,hours}))).filter(({current,hours})=>{
      const answer=variant===0?current*hours:variant===1?hours:energy?current*hours:current;
      const exactDisplay=Math.abs(current*hours*100-Math.round(current*hours*100))<1e-7;
      return whole?Number.isInteger(answer)&&answer>=2&&answer<=10:exactDisplay&&!Number.isInteger(answer);
    });
    const {current,hours}=pick(rng,pairs);
    const voltage=pick(rng,[6,12,24]),q=Number(fmt(current*hours)),p=Number(fmt(energy&&variant===0?current:voltage*current)),e=Number(fmt(p*hours));
    const timeText=minutes?`${fmt(hours*60)} דקות`:`${fmt(hours)} שעות`;
    const device=course==='security'?'מערכת מיגון':'מכשיר סלולרי';
    let title,text,steps,givens;
    if(energy){
      title=charging?'אנרגיה בטעינת סוללת גיבוי':'זמן פעולה של סוללת גיבוי';
      if(variant===0){text=`סוללת גיבוי מזינה ${device} בהספק קבוע של ${fmt(p)} ואט במשך ${timeText}. מה האנרגיה שנצרכה בוואט־שעה?`;steps=[step('E','האנרגיה שנצרכה','Wh',e,'E = P × t',`${fmt(p)} × ${fmt(hours)}`)];givens=[['P',p,'W'],['t',minutes?hours*60:hours,minutes?'min':'h']];}
      if(variant===1){text=`בסוללת הגיבוי זמינות ${fmt(e)} ואט־שעה. מערכת מיגון צורכת הספק קבוע של ${fmt(p)} ואט. לכמה שעות תספיק הסוללה?`;steps=[step('t','משך הפעולה','h',hours,'t = E ÷ P',`${fmt(e)} ÷ ${fmt(p)}`)];givens=[['E',e,'Wh'],['P',p,'W']];}
      if(variant===2){text=`סוללת גיבוי במתח ${voltage} וולט אוגרת ${fmt(e)} ואט־שעה. מה המטען שלה באמפר־שעה?`;steps=[step('Q','מטען הסוללה','Ah',q,'Q = E ÷ U',`${fmt(e)} ÷ ${voltage}`)];givens=[['E',e,'Wh'],['U',voltage,'V']];}
    }else{
      title=charging?'טעינת סוללה בזרם קבוע':'פריקת סוללה בזרם קבוע';
      if(variant===0){text=charging?`מטען מטעין סוללה של ${device} בזרם קבוע של ${fmt(current)} אמפר במשך ${timeText}. כמה אמפר־שעה נוספו לסוללה?`:`סוללה מזינה ${device} בזרם קבוע של ${fmt(current)} אמפר במשך ${timeText}. כמה אמפר־שעה נפרקו ממנה?`;steps=[step('Q',charging?'המטען שנוסף לסוללה':'המטען שנפרק מהסוללה','Ah',q,'Q = I × t',`${fmt(current)} × ${fmt(hours)}`)];givens=[['I',current,'A'],['t',minutes?hours*60:hours,minutes?'min':'h']];}
      if(variant===1){text=charging?`יש להשלים לסוללה מטען של ${fmt(q)} אמפר־שעה. זרם הטעינה קבוע ושווה ל־${fmt(current)} אמפר. כמה שעות נדרשות?`:`בסוללת ${device} נשאר מטען של ${fmt(q)} אמפר־שעה. צריכת הזרם קבועה ושווה ל־${fmt(current)} אמפר. לכמה שעות יספיק המטען?`;steps=[step('t',charging?'זמן הטעינה':'זמן הפריקה','h',hours,'t = Q ÷ I',`${fmt(q)} ÷ ${fmt(current)}`)];givens=[['Q',q,'Ah'],['I',current,'A']];}
      if(variant===2){text=`במהלך ${charging?'טעינה':'פריקה'} של סוללת ${device}, מטען של ${fmt(q)} אמפר־שעה הועבר במשך ${timeText}. מה היה הזרם הקבוע?`;steps=[step('I',charging?'זרם הטעינה':'זרם הפריקה','A',current,'I = Q ÷ t',`${fmt(q)} ÷ ${fmt(hours)}`)];givens=[['Q',q,'Ah'],['t',minutes?hours*60:hours,minutes?'min':'h']];}
    }
    if(minutes&&givens.some(([key,_,unit])=>key==='t'&&unit==='min')){
      steps.unshift(step('t_h','המרת זמן מדקות לשעות','h',hours,'t_h = t_min ÷ 60',`${fmt(hours*60)} ÷ 60`));
    }
    if(!whole&&variant===1){
      const wholeHours=Math.floor(hours),remainder=Math.round((hours-wholeHours)*60);
      steps.push(step('t_minutes','הזמן הכולל בדקות','min',hours*60,'t_min = t × 60',`${fmt(hours)} × 60`));
      steps.push(step('t_remainder',`הדקות הנותרות מעבר ל־${wholeHours} שעות שלמות`,'min',remainder,'t_remaining = t_min − t_whole × 60',`${fmt(hours*60)} − ${wholeHours} × 60`));
      text+=` לאחר החישוב, המירו לדקות והציגו את הזמן גם בשעות ובדקות.`;
    }
    return {kind:'battery',schemaVersion:3,whole,level,index,title,text,steps,givens,unitFamily:energy?'Wh':'Ah',note:'בתרגיל מניחים זרם קבוע ומודל אידאלי ללא הפסדים.'};
  }
  function internalResistance(rng,level,index,whole=integralBatteryIndices.includes(index%10)){
    const pairs=[2,3,4,5].flatMap(rs=>[2,3,4,5].filter(current=>rs*current<=10).map(current=>({rs,current})));
    const integral=whole?pick(rng,pairs):null;
    const ut=whole?pick(rng,[3800,4000,4200]):pick(rng,[3.8,4,4.2]);
    const rs=whole?integral.rs:pick(rng,[.04,.06,.08,.12,.16]);
    const current=whole?integral.current:pick(rng,[1.5,2,2.5]);
    const du=rs*current,ul=ut-du;
    const voltageUnit=whole?'mV':'V',resistanceUnit=whole?'mΩ':'Ω',rsOhms=whole?rs/1000:rs;
    return {kind:'battery',schemaVersion:3,whole,level,index,unitFamily:'Rs',title:'התנגדות פנימית של סוללה',voltageUnit,resistanceUnit,
      text:`מתח הסוללה ללא עומס הוא ${fmt(ut)} ${whole?'מיליוולט':'וולט'}. כשהסוללה מספקת זרם של ${fmt(current)} אמפר, מתח העומס שלה הוא ${fmt(ul)} ${whole?'מיליוולט':'וולט'}. חשבו את מפל המתח הפנימי ואת ההתנגדות הפנימית${whole?' במיליאוהם':''}.`,
      givens:[['U_t',ut,voltageUnit],['U_L',ul,voltageUnit],['I',current,'A']],
      steps:[step('ΔU','מפל המתח על ההתנגדות הפנימית',voltageUnit,du,'ΔU = U_t − U_L',`${fmt(ut)} − ${fmt(ul)}`),step('R_s','ההתנגדות הפנימית',resistanceUnit,rs,'R_s = ΔU ÷ I',`${fmt(du)} ÷ ${fmt(current)}`)],
      note:'',rs,rsOhms};
  }
  function batch(course,kind,level,seed){
    const rng=random(seed),result=Array.from({length:10},(_,index)=>kind==='mixed'?mixed(rng,level,index):battery(rng,course,level,index));
    // The generator assigns seven Ah and three Wh exercises in security.
    // Shuffle their presentation, retaining the stable generated question IDs.
    for(let i=result.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[result[i],result[j]]=[result[j],result[i]];}
    return result.map(q=>({...q,cursor:0,draft:'',attempts:0,hint:false,solution:false,accepted:false,helped:false}));
  }
  // One notation and palette for every simulator, including enlarged diagrams.
  // Values stay unrounded in the model; rounding is only applied to these labels.
  function simulationCurrentLabel(right,bottom,value){
    return `<text class="sim-current-label" x="${right}" y="${bottom}" fill="#ff6565" text-anchor="end" dominant-baseline="text-after-edge" font-size="16" font-family="Arial,sans-serif" direction="ltr" paint-order="stroke" stroke="#000" stroke-width="4" stroke-linejoin="round">${value}</text>`;
  }
  function simulationAnnotations({id,x,y,vertical=false,reverse=false,r,current,drop,resistanceUnit='Ω',currentUnit='A',voltageUnit='V',number=simulationNumber,formatQuantity}){
    const ink='#fff',red='#ff6565',green='#65e680',n=number;
    const quantity=formatQuantity??((value,unit)=>n(value)+' '+unit);
    const label=(tx,ty,value,color,anchor='middle')=>`<text x="${tx}" y="${ty}" fill="${color}" text-anchor="${anchor}" font-size="16" font-family="Arial,sans-serif" direction="ltr">${value}</text>`;
    const arrow=(x1,y1,x2,y2,color)=>{
      const dx=x2-x1,dy=y2-y1,length=Math.hypot(dx,dy),ux=dx/length,uy=dy/length;
      return `<path class="sim-arrow" d="M${x1} ${y1}L${x2} ${y2}M${x2-ux*8-uy*4} ${y2-uy*8+ux*4}L${x2} ${y2}L${x2-ux*8+uy*4} ${y2-uy*8-ux*4}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`;
    };
    const iSymbol=id.replace(/^R/,'I'),uSymbol=id==='R_s'?'ΔU_s':id.replace(/^R/,'U');
    const tx=x+(vertical?35:0),anchor=vertical?'start':'middle';
    const currentArrow=vertical?arrow(x,y-67,x,y-42,red):reverse?arrow(x+72,y,x+46,y,red):arrow(x-72,y,x-46,y,red);
    // Anchor the label's bottom-right corner above the right edge of its arrow.
    // Extra clearance on horizontal wires keeps text above adjacent resistors.
    const currentX=vertical?x:x+(reverse?72:-46),currentY=y-(vertical?78:26);
    // Voltage reference points toward +, opposite to conventional resistor current.
    const voltageArrow=vertical?arrow(x-30,y+30,x-30,y-30,green):reverse?arrow(x-38,y+29,x+38,y+29,green):arrow(x+38,y+29,x-38,y+29,green);
    const polarity=vertical?label(x-43,y-23,'+',green)+label(x-43,y+34,'−',green):label(x+(reverse?49:-49),y+34,'+',green)+label(x+(reverse?-49:49),y+34,'−',green);
    return `<g class="sim-component" data-component="${id}" data-resistance="${r}" data-current="${current}" data-voltage="${drop}" data-resistance-unit="${resistanceUnit}" data-current-unit="${currentUnit}" data-voltage-unit="${voltageUnit}"><title>${id}: ${quantity(r,resistanceUnit)}; ${iSymbol} = ${quantity(current,currentUnit)}; ${uSymbol} = ${quantity(drop,voltageUnit)}</title><g class="sim-resistance">${label(tx,y+(vertical?-16:-55),`${id} = ${quantity(r,resistanceUnit)}`,ink,anchor)}</g><g class="sim-current">${currentArrow}${simulationCurrentLabel(currentX,currentY,`${iSymbol} = ${quantity(current,currentUnit)}`)}</g><g class="sim-voltage-drop">${voltageArrow}${polarity}${label(tx,y+(vertical?32:51),`${uSymbol} = ${quantity(drop,voltageUnit)}`,green,anchor)}</g></g>`;
  }
  function mixedSimulationSVG(q){
    const n=simulationNumber,ink='#fff',red='#ff6565',green='#65e680';
    const quantity=q.formatQuantity??((value,unit)=>n(value)+' '+unit);
    const scale=q.currentUnit==='mA'?.001:q.currentUnit==='μA'?.000001:1;
    const text=(x,y,value,color=ink,anchor='middle')=>`<text x="${x}" y="${y}" fill="${color}" text-anchor="${anchor}" font-size="17" font-family="Arial,sans-serif" direction="ltr">${value}</text>`;
    const wire=(d,current)=>{
      const amps=current*scale,duration=Math.max(.25,Math.min(8,3/Math.max(.01,amps)));
      const flow=current>0?`<path class="mixed-current-flow${q.simAnimate===false?' is-paused':''}" d="${d}" fill="none" stroke="${red}" stroke-width="3.5" style="--mixed-flow-duration:${duration}s" data-current="${amps}" aria-hidden="true"/>`:'';
      return `<path d="${d}" fill="none" stroke="${ink}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>${flow}`;
    };
    const node=(x,y,i,vertical=false,reverse=false)=>`<g class="mixed-resistor" data-symbol="R${i+1}" data-from="${q.resistorNodes[i].from}" data-to="${q.resistorNodes[i].to}"><rect x="${x-(vertical?12:38)}" y="${y-(vertical?30:12)}" width="${vertical?24:76}" height="${vertical?60:24}" fill="#000" stroke="${ink}" stroke-width="2.5"/>${simulationAnnotations({id:'R'+(i+1),x,y,vertical,reverse,r:q.r[i],current:q.currents[i],drop:q.voltages[i],resistanceUnit:q.resistanceUnit,currentUnit:q.currentUnit,formatQuantity:quantity})}</g>`;
    const junction=(x,y)=>`<circle cx="${x}" cy="${y}" r="4" fill="${ink}"/>`;
    const source=(top,bottom)=>{
      const mid=(top+bottom)/2;
      return wire(`M100 ${top}V${mid-14}M100 ${mid+14}V${bottom}M77 ${mid-14}H123M87 ${mid+14}H113`)+text(69,mid-16,'+')+text(69,mid+26,'−')+text(145,mid+5,`U = ${quantity(q.u,'V')}`,green,'start');
    };
    let content='',width=960,height=560;
    if(q.variant.startsWith('parallel-groups')){
      width=1160;height=550;const top=190,bottom=440;
      content=wire('M110 440V190H200',q.it)+wire('M440 190H700',q.it)+wire('M940 190H1050V440H485',q.it)+wire('M455 440H110',q.it)
        +wire('M455 417V463M485 427V453')+text(441,418,'+')+text(499,418,'−')+text(470,514,`U = ${quantity(q.u,'V')}`,green);
      const group=(g,left,right)=>g.branches.map((branch,bi)=>{
        const x=(left+right)/2,y=bi===0?100:280,i=branch[0];
        return wire(`M${left} ${top}V${y}H${right}V${top}`,q.currents[i])+node(x,y,i);
      }).join('')+junction(left,top)+junction(right,top);
      content+=group(q.groups[0],200,440)+node(570,top,2)+group(q.groups[2],700,940)+node(820,bottom,5,false,true);
    }else if(q.family==='parallel-series'){
      const top=65,bottom=490,xs=[350,680];
      content=source(top,bottom)+wire(`M100 ${top}H680`,q.it)+wire(`M680 ${bottom}H100`,q.it);
      q.groups[0].branches.forEach((branch,bi)=>{
        const x=xs[bi],ys=branch.length===1?[280]:[180,370];
        content+=wire(`M${x} ${top}V${bottom}`,q.currents[branch[0]])+junction(x,top)+junction(x,bottom);
        branch.forEach((i,j)=>{content+=node(x,ys[j],i,true);});
      });
    }else{
      const top=100,bottom=490,xs=q.groups[1].branches.map((_,i)=>500+i*290),end=xs.at(-1);
      width=end+230;
      content=source(top,bottom)+wire(`M100 ${top}H${end}`,q.it)+wire(`M${end} ${bottom}H100`,q.it)+node(270,top,0);
      q.groups[1].branches.forEach((branch,bi)=>{
        const x=xs[bi],i=branch[0];
        content+=wire(`M${x} ${top}V${bottom}`,q.currents[i])+node(x,300,i,true)+junction(x,top)+junction(x,bottom);
      });
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" class="mixed-circuit-svg mixed-simulation-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="סימולטור ${q.title}: זרם בכל ענף, מפל מתח עם כיוון וערך ההתנגדות על כל נגד" data-family="${q.family}" data-stage="0" style="background:#000"><desc>זרם מוסכם באדום; מפל מתח בירוק עם ראש החץ לכיוון הפלוס; התנגדות בלבן.</desc>${content}</svg>`;
  }
  function mixedSVG(q,stage=0,showNodes=false,simulation=false){
    if(simulation)return mixedSimulationSVG(q);
    const groups=q.diagrams[Math.max(0,Math.min(stage,q.diagrams.length-1))];
    const ink='var(--ink)',card='var(--card)';
    const wire=path=>`<path d="${path}" fill="none" stroke="${ink}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;
    const text=(x,y,value,anchor='middle')=>`<text x="${x}" y="${y}" fill="${ink}" text-anchor="${anchor}" font-size="18" font-family="Arial,sans-serif" direction="ltr">${value}</text>`;
    const symbol=(x,y,value,anchor='middle')=>{const m=/^([A-Za-z]+)_?([A-Za-z]+|\d+)$/.exec(value);return m?`<text x="${x}" y="${y}" fill="${ink}" text-anchor="${anchor}" font-size="19" font-family="Arial,sans-serif" direction="ltr">${m[1]}<tspan dy="5" font-size="13">${m[2]}</tspan><tspan dy="-5"> </tspan></text>`:text(x,y,value,anchor);};
    const node=(x,y,resistor,vertical=false)=>`<g class="mixed-resistor" data-symbol="${resistor.symbol}" data-from="${resistor.from}" data-to="${resistor.to}"><rect x="${x-(vertical?12:38)}" y="${y-(vertical?30:12)}" width="${vertical?24:76}" height="${vertical?60:24}" fill="${card}" stroke="${ink}" stroke-width="2.5"/>${symbol(x+(vertical?29:0),y+(vertical?-4:-26),resistor.symbol,vertical?'start':'middle')}${text(x+(vertical?29:0),y+(vertical?22:43),fmt(resistor.value)+' '+q.resistanceUnit,vertical?'start':'middle')}</g>`;
    const dot=(x,y)=>`<circle cx="${x}" cy="${y}" r="4" fill="${ink}"/>`;
    const junction=(x,y,label,dx=-18,dy=-13)=>showNodes?`<g class="mixed-junction" data-node="${label}">${dot(x,y)}${text(x+dx,y+dy,label)}</g>`:dot(x,y);
    const source=(x,top,bottom)=>{
      const mid=(top+bottom)/2;
      return wire(`M${x} ${top}V${mid-13}M${x} ${mid+13}V${bottom}M${x-23} ${mid-13}H${x+23}M${x-13} ${mid+13}H${x+13}`)+text(x-32,mid-21,'+')+text(x-32,mid+30,'−')+symbol(x-46,mid-14,'U','end')+text(x-46,mid+20,fmt(q.u)+' V','end');
    };
    let content='',width=800,height=440;
    if(q.family==='parallel-series'){
      const top=65,bottom=405,branches=groups[0],xs=branches.length===1?[445]:[330,610];
      width=790;height=445;
      content=source(120,top,bottom)+wire(`M120 ${top}H${xs.at(-1)}M120 ${bottom}H${xs.at(-1)}`);
      branches.forEach((branch,bi)=>{
        const x=xs[bi],ys=branch.length===1?[235]:[155,315];let previous=top;
        branch.forEach((resistor,ri)=>{content+=wire(`M${x} ${previous}V${ys[ri]-30}`)+node(x,ys[ri],resistor,true);previous=ys[ri]+30;});
        content+=wire(`M${x} ${previous}V${bottom}`)+junction(x,top,branch[0].from)+junction(x,bottom,branch.at(-1).to,-18,26);
        if(branch.length>1)content+=junction(x,235,branch[0].to,-20,6);
      });
    }else if(q.variant.startsWith('parallel-groups')&&stage<q.diagrams.length-1){
      // Same A-B / R3 / C-D / R6 order as worksheet exercise 15.
      width=920;height=445;const top=155,bottom=365;
      content=wire('M110 365V155H190M350 155H425M501 155H565M725 155H820V365H668M592 365H385M355 365H110M355 342V388M385 352V378')
        +text(343,345,'+')+text(400,345,'−')+symbol(370,322,'U')+text(370,414,fmt(q.u)+' V');
      const group=(network,left,right)=>{
        let out='';const ys=network.length===1?[top]:[80,230];
        network.forEach((branch,bi)=>{const x=(left+right)/2,y=ys[bi];out+=wire(`M${left} ${top}V${y}H${x-38}M${x+38} ${y}H${right}V${top}`)+node(x,y,branch[0]);});
        return out+dot(left,top)+dot(right,top);
      };
      content+=group(groups[0],190,350)+node(463,top,groups[1][0][0])+group(groups[2],565,725)+node(630,bottom,groups[3][0][0]);
      content+=junction(190,top,groups[0][0][0].from)+junction(350,top,groups[0][0][0].to,15,-13)+junction(565,top,groups[2][0][0].from)+junction(725,top,groups[2][0][0].to,15,-13)+junction(450,bottom,groups[3][0][0].to,0,28);
    }else if(stage===q.diagrams.length-1){
      width=790;height=420;content=source(120,80,370)+wire('M120 80H367M443 80H670V370H120')+node(405,80,groups[0][0][0])+junction(190,80,groups[0][0][0].from)+junction(620,80,groups[0][0][0].to);
    }else{
      const count=q.groups[1].branches.length,top=80,bottom=370,start=400,gap=155;
      const end=start+(count-1)*gap; width=end+160;height=420;
      const branches=groups[1],xs=branches.length===1?[(start+end)/2]:branches.map((_,i)=>start+i*gap);
      content=source(120,top,bottom)+wire(`M120 ${top}H227M303 ${top}H${xs.at(-1)}M120 ${bottom}H${xs.at(-1)}`)+node(265,top,groups[0][0][0]);
      branches.forEach((branch,i)=>{const x=xs[i];content+=wire(`M${x} ${top}V195M${x} 255V${bottom}`)+node(x,225,branch[0],true)+junction(x,top,branch[0].from)+junction(x,bottom,branch[0].to,-18,28);});
      content+=junction(180,top,groups[0][0][0].from);
    }
    const label=stage===0?'המעגל המקורי — '+q.title:'צמצום '+stage+': '+q.reductions[stage-1].title;
    return `<svg class="mixed-circuit-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${label}" data-family="${q.family}" data-stage="${stage}">${content}</svg>`;
  }
  function phoneSimulationSVG(q){
    const given=Object.fromEntries(q.givens.map(([key,value])=>[key,value]));
    const n=simulationNumber;
    const ink='#fff',red='#ff6565',green='#65e680',voltageUnit=q.voltageUnit??'V',resistanceUnit=q.resistanceUnit??'Ω';
    const currentUnit=q.simCurrentUnit==='mA'?'mA':'A',current=given.I*(currentUnit==='mA'?1000:1);
    const load=q.simLoadResistance??given.U_L/given.I;
    const text=(x,y,value,color=ink,size=17)=>`<text x="${x}" y="${y}" fill="${color}" font-size="${size}" font-family="Arial,sans-serif" text-anchor="middle" direction="ltr">${value}</text>`;
    const duration=Math.max(.25,Math.min(8,3/Math.max(.01,given.I))),paused=q.simAnimate===false||given.I<=0;
    return `<svg xmlns="http://www.w3.org/2000/svg" class="phone-battery-svg" viewBox="0 0 950 500" role="img" aria-label="סוללה עם התנגדות פנימית ועומס: זרם, התנגדות ומפל מתח בכל רכיב" style="background:#000">
      <rect x="40" y="40" width="390" height="425" rx="17" fill="none" stroke="#69717b" stroke-dasharray="6 5"/>
      ${text(235,24,'סוללה',ink,19)}
      <path d="M110 249V125H277M353 125H690V250M690 310V430H110V301" fill="none" stroke="${ink}" stroke-width="2.5"/>
      <circle cx="110" cy="275" r="26" fill="#000" stroke="${ink}" stroke-width="2.5"/>
      ${text(110,269,'+',ink,22)}${text(110,292,'−',ink,22)}${text(265,280,`U_t = ${n(given.U_t)} ${voltageUnit}`,green)}
      <rect x="277" y="113" width="76" height="24" fill="#000" stroke="${ink}" stroke-width="2.5"/>
      <circle cx="550" cy="125" r="4" fill="${ink}"/><circle cx="550" cy="430" r="4" fill="${ink}"/>
      <rect x="605" y="65" width="310" height="400" rx="24" fill="none" stroke="${ink}" stroke-width="2.5"/>
      <path d="M730 85H790M730 449H790" stroke="${ink}" stroke-width="3"/>
      <rect x="678" y="250" width="24" height="60" fill="#000" stroke="${ink}" stroke-width="2.5"/>
      <path class="phone-current-flow${paused?' is-paused':''}" d="M110 249V125H690V430H110V301" fill="none" stroke="${red}" stroke-width="3.5" stroke-linecap="round" style="--phone-flow-duration:${duration}s" data-current="${given.I}" aria-hidden="true"/>
      ${simulationAnnotations({id:'R_s',x:315,y:125,r:q.rs,current,drop:given.I*q.rs,resistanceUnit,currentUnit,voltageUnit,number:n})}
      ${simulationAnnotations({id:'R_L',x:690,y:280,vertical:true,r:load,current,drop:given.U_L,resistanceUnit,currentUnit,voltageUnit,number:n})}
      ${text(760,390,'מעגלי הטלפון',ink,19)}${text(235,488,'מקור אידאלי והתנגדות פנימית',ink,16)}
    </svg>`;
  }
  function phoneBatterySVG(q,simulation=false){
    if(simulation)return phoneSimulationSVG(q);
    const format=simulation?simulationNumber:fmt;
    const given=Object.fromEntries(q.givens.map(([key,value])=>[key,value]));
    const showDrop=simulation||q.solution||q.cursor>0||q.cursor===0&&q.accepted;
    const showResistance=simulation||q.solution||q.cursor>1||q.cursor===1&&q.accepted;
    const ink='var(--ink)',current='var(--phone-current,#b52e2e)',voltage='var(--phone-voltage,#116e65)';
    const symbolText=(x,y,base,sub,suffix='',color=ink)=>`<text x="${x}" y="${y}" fill="${color}" font-family="Arial,sans-serif" font-size="17" text-anchor="start" direction="ltr">${base}<tspan dy="5" font-size="12">${sub}</tspan><tspan dy="-5" font-size="17">${suffix}</tspan></text>`;
    const text=(x,y,value,color=ink,size=17)=>`<text x="${x}" y="${y}" fill="${color}" font-size="${size}" font-family="Arial,sans-serif" text-anchor="middle" direction="ltr">${value}</text>`;
    const voltageUnit=q.voltageUnit??'V',resistanceUnit=q.resistanceUnit??'Ω';
    const rs=showResistance?`${format(q.rs)} ${resistanceUnit}`:'?',drop=showDrop?`${format(given.U_t-given.U_L)} ${voltageUnit}`:'?';
    const currentUnit=simulation&&q.simCurrentUnit==='mA'?'mA':'A',displayCurrent=given.I*(currentUnit==='mA'?1000:1);
    const duration=Math.max(.25,Math.min(8,3/Math.max(.01,given.I))),paused=q.simAnimate===false||given.I<=0;
    const flow=simulation?`<path class="phone-current-flow${paused?' is-paused':''}" d="M100 144V90H515V280H100V196" fill="none" stroke="${current}" stroke-width="3.5" stroke-linecap="round" style="--phone-flow-duration:${duration}s" data-current="${given.I}" aria-hidden="true"/>`:'';
    return `<svg class="phone-battery-svg" viewBox="0 0 640 345" role="img" aria-label="מודל סוללת טלפון: מתח ללא עומס, התנגדות פנימית בטור, ועומס המייצג את מעגלי הטלפון">
      <rect x="30" y="65" width="270" height="242" rx="17" fill="none" stroke="var(--line)" stroke-dasharray="6 5"/>
      ${text(177,30,'סוללה',ink,19)}
      <path d="M100 144V90H205M275 90H515V145M515 215V280H100V196" fill="none" stroke="${ink}" stroke-width="2.5"/>
      <circle cx="100" cy="170" r="26" fill="var(--card)" stroke="${ink}" stroke-width="2.5"/>
      ${text(100,164,'+',ink,22)}${text(100,187,'−',ink,22)}
      ${symbolText(144,178,'U','t',` = ${format(given.U_t)} ${voltageUnit}`,simulation?voltage:ink)}
      <rect x="205" y="77" width="70" height="26" fill="var(--card)" stroke="${ink}" stroke-width="2.5"/>
      ${symbolText(215,130,'R','s',` = ${rs}`)}
      <path d="M205 61H275M205 61l7 -4M205 61l7 4M275 61l-7 -4M275 61l-7 4" fill="none" stroke="${voltage}" stroke-width="2"/>
      ${text(240,52,`ΔU = ${drop}`,voltage,16)}
      <path d="M345 90H373l-9 -5M373 90l-9 5" fill="none" stroke="${current}" stroke-width="3"/>
      ${text(365,72,`I = ${format(displayCurrent)} ${currentUnit}`,current,16)}
      <circle cx="390" cy="90" r="4" fill="${ink}"/><circle cx="390" cy="280" r="4" fill="${ink}"/>
      <path d="M391 112V258M391 112l-5 9M391 112l5 9M391 258l-5 -9M391 258l5 -9" fill="none" stroke="${voltage}" stroke-width="2"/>
      ${symbolText(343,187,'U','L','',voltage)}${text(354,211,`${format(given.U_L)} ${voltageUnit}`,voltage,16)}
      <rect x="437" y="45" width="168" height="272" rx="24" fill="none" stroke="${ink}" stroke-width="2.5"/>
      <path d="M490 60H550M495 302H545" stroke="${ink}" stroke-width="3"/>
      <rect x="500" y="145" width="30" height="70" fill="var(--card)" stroke="${ink}" stroke-width="2.5"/>
      ${flow}
      ${symbolText(550,184,'R','L')}${q.simLoadResistance!==undefined?text(521,232,`${format(q.simLoadResistance)} ${resistanceUnit}`,ink,14):''}${text(521,258,'מעגלי הטלפון',ink,18)}
      ${text(177,334,'מקור אידאלי והתנגדות פנימית',ink,15)}
    </svg>`;
  }
  return {random,mixed,battery,internalResistance,batch,mixedSVG,phoneBatterySVG,simulationNumber,milliSimulationNumber,simulationCurrentLabel,simulationAnnotations};
})();
if(typeof module!=='undefined')module.exports=CoursePractice;

/* Pure generators: displayed units form one coherent unit system. */
const CoursePractice = (() => {
  const pick = (rng, list) => list[Math.floor(rng() * list.length)];
  const integer = (rng, lo, hi) => lo + Math.floor(rng() * (hi - lo + 1));
  const fmt = value => String(Math.round((value + Number.EPSILON) * 100) / 100);
  const step = (key, label, unit, value, formula, substitution) => ({key,label,unit,value,formula,substitution});
  function random(seed) {
    let value=seed>>>0;
    return ()=>{value+=0x6D2B79F5;let t=value;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};
  }
  function mixed(rng, level, index) {
    const k=integer(rng,2,16),r=level===1?[integer(rng,4,15),integer(rng,16,28),integer(rng,29,42)]:[2*k,3*k,6*k];
    const r4=integer(rng,3,20),rp=1/r.reduce((sum,value)=>sum+1/value,0),rt=rp+r4;
    const u=level===1?integer(rng,12,60):rt*pick(rng,[6,12]);
    const it=u/rt,up=it*rp,u4=it*r4,branch=r.map(value=>up/value);
    const resistanceUnit=level===2?(index%2?'MΩ':'kΩ'):'Ω',currentUnit=level===2?(index%2?'μA':'mA'):'A';
    const steps=[
      step('R_p','התנגדות שלושת הענפים במקביל',resistanceUnit,rp,'R_p = 1 ÷ (1/R1 + 1/R2 + 1/R3)',`1 ÷ (1/${r[0]} + 1/${r[1]} + 1/${r[2]})`),
      step('R_T','ההתנגדות השקולה של כל המעגל',resistanceUnit,rt,'R_T = R_p + R4',`${fmt(rp)} + ${r4}`),
      step('I_T','הזרם הכולל מהמקור',currentUnit,it,'I_T = U ÷ R_T',`${fmt(u)} ÷ ${fmt(rt)}`),
      step('U4','מפל המתח על הנגד שבטור','V',u4,'U4 = I_T × R4',`${fmt(it)} × ${r4}`),
      step('U_p','המתח על קבוצת הענפים המקבילים','V',up,'U_p = U − U4',`${fmt(u)} − ${fmt(u4)}`),
      ...r.map((value,j)=>step('I'+(j+1),'הזרם בענף '+(j+1),currentUnit,branch[j],`I${j+1} = U_p ÷ R${j+1}`,`${fmt(up)} ÷ ${value}`))
    ];
    return {kind:'mixed',level,index,title:'שלושה ענפים במקביל ונגד בטור למקור',u,r,r4,rp,rt,it,up,u4,branch,resistanceUnit,currentUnit,steps,
      givens:[['U',u,'V'],...r.map((v,i)=>['R'+(i+1),v,resistanceUnit]),['R4',r4,resistanceUnit]]};
  }
  function battery(rng, course, level, index) {
    if(course==='mobile'&&index>=7)return internalResistance(rng,level,index);
    const energy=course==='security'&&index>=7;
    const current=level===0?integer(rng,1,6):pick(rng,[.2,.4,.5,.8,1.2,1.5,2.5]);
    const hours=level===0?integer(rng,2,8):pick(rng,[.5,.75,1.25,1.5,2.5,3.5]);
    const voltage=pick(rng,[6,12,24]),q=current*hours,p=voltage*current,e=p*hours;
    const variant=index%3,charging=index%2===0,minutes=level===2;
    const timeText=minutes?`${fmt(hours*60)} דקות`:`${fmt(hours)} שעות`;
    const device=course==='security'?'מערכת מיגון':'מכשיר סלולרי';
    let title,text,steps,givens;
    if(energy){
      title=charging?'אנרגיה בטעינת סוללת גיבוי':'זמן פעולה של סוללת גיבוי';
      if(variant===0){text=`סוללת גיבוי מזינה ${device} במתח ${voltage} וולט ובזרם קבוע של ${fmt(current)} אמפר במשך ${timeText}. מה האנרגיה שנצרכה בוואט־שעה?`;steps=[step('E','האנרגיה שנצרכה','Wh',e,'E = U × I × t',`${voltage} × ${fmt(current)} × ${fmt(hours)}`)];givens=[['U',voltage,'V'],['I',current,'A'],['t',minutes?hours*60:hours,minutes?'min':'h']];}
      if(variant===1){text=`בסוללת הגיבוי זמינות ${fmt(e)} ואט־שעה. מערכת מיגון צורכת הספק קבוע של ${fmt(p)} ואט. לכמה שעות תספיק הסוללה?`;steps=[step('t','משך הפעולה','h',hours,'t = E ÷ P',`${fmt(e)} ÷ ${fmt(p)}`)];givens=[['E',e,'Wh'],['P',p,'W']];}
      if(variant===2){text=`סוללת גיבוי במתח ${voltage} וולט אוגרת ${fmt(e)} ואט־שעה. מה המטען שלה באמפר־שעה?`;steps=[step('Q','מטען הסוללה','Ah',q,'Q = E ÷ U',`${fmt(e)} ÷ ${voltage}`)];givens=[['E',e,'Wh'],['U',voltage,'V']];}
    }else{
      title=charging?'טעינת סוללה בזרם קבוע':'פריקת סוללה בזרם קבוע';
      if(variant===0){text=charging?`מטען מטעין סוללה של ${device} בזרם קבוע של ${fmt(current)} אמפר במשך ${timeText}. כמה אמפר־שעה נוספו לסוללה?`:`סוללה מזינה ${device} בזרם קבוע של ${fmt(current)} אמפר במשך ${timeText}. כמה אמפר־שעה נפרקו ממנה?`;steps=[step('Q',charging?'המטען שנוסף לסוללה':'המטען שנפרק מהסוללה','Ah',q,'Q = I × t',`${fmt(current)} × ${fmt(hours)}`)];givens=[['I',current,'A'],['t',minutes?hours*60:hours,minutes?'min':'h']];}
      if(variant===1){text=charging?`יש להשלים לסוללה מטען של ${fmt(q)} אמפר־שעה. זרם הטעינה קבוע ושווה ל־${fmt(current)} אמפר. כמה שעות נדרשות?`:`בסוללת ${device} נשאר מטען של ${fmt(q)} אמפר־שעה. צריכת הזרם קבועה ושווה ל־${fmt(current)} אמפר. לכמה שעות יספיק המטען?`;steps=[step('t',charging?'זמן הטעינה':'זמן הפריקה','h',hours,'t = Q ÷ I',`${fmt(q)} ÷ ${fmt(current)}`)];givens=[['Q',q,'Ah'],['I',current,'A']];}
      if(variant===2){text=`במהלך ${charging?'טעינה':'פריקה'} של סוללת ${device}, מטען של ${fmt(q)} אמפר־שעה הועבר במשך ${timeText}. מה היה הזרם הקבוע?`;steps=[step('I',charging?'זרם הטעינה':'זרם הפריקה','A',current,'I = Q ÷ t',`${fmt(q)} ÷ ${fmt(hours)}`)];givens=[['Q',q,'Ah'],['t',minutes?hours*60:hours,minutes?'min':'h']];}
    }
    if(minutes&&variant!==1){steps.unshift(step('t_h','המרת זמן מדקות לשעות','h',hours,'t_h = t_min ÷ 60',`${fmt(hours*60)} ÷ 60`));}
    return {kind:'battery',level,index,title,text,steps,givens,unitFamily:energy?'Wh':'Ah',note:'בתרגיל מניחים זרם קבוע ומודל אידאלי ללא הפסדים.'};
  }
  function internalResistance(rng,level,index){
    const ut=pick(rng,[3.8,4,4.2]),rs=pick(rng,[.04,.06,.08,.1,.12,.16,.2]),current=pick(rng,[1,1.5,2,2.5]);
    const du=rs*current,ul=ut-du,limit=.12;
    return {kind:'battery',level,index,unitFamily:'Rs',title:'התנגדות פנימית של סוללה',
      text:`מתח הסוללה ללא עומס הוא ${fmt(ut)} וולט. כשהסוללה מספקת זרם של ${fmt(current)} אמפר, מתח העומס שלה הוא ${fmt(ul)} וולט. חשבו את מפל המתח הפנימי ואת ההתנגדות הפנימית.`,
      givens:[['U_t',ut,'V'],['U_L',ul,'V'],['I',current,'A']],
      steps:[step('ΔU','מפל המתח על ההתנגדות הפנימית','V',du,'ΔU = U_t − U_L',`${fmt(ut)} − ${fmt(ul)}`),step('R_s','ההתנגדות הפנימית','Ω',rs,'R_s = ΔU ÷ I',`${fmt(du)} ÷ ${fmt(current)}`)],
      note:`לצורך התרגיל בלבד, נתון יצרן: התנגדות פנימית מרבית ${fmt(limit)} Ω. ${rs<=limit?'התוצאה עומדת בגבול הנתון.':'התוצאה חורגת מהגבול הנתון ונדרשת בדיקה לפי הוראות היצרן.'} התנגדות פנימית לבדה אינה קובעת אחוז בריאות סוללה.`,limit,rs};
  }
  function batch(course,kind,level,seed){
    const rng=random(seed),result=Array.from({length:10},(_,index)=>kind==='mixed'?mixed(rng,level,index):battery(rng,course,level,index));
    // The generator assigns seven Ah and three Wh exercises in security.
    // Shuffle their presentation, retaining the stable generated question IDs.
    for(let i=result.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[result[i],result[j]]=[result[j],result[i]];}
    return result.map(q=>({...q,cursor:0,draft:'',attempts:0,hint:false,solution:false,accepted:false,helped:false}));
  }
  function mixedSVG(q,stage=0){
    const color='var(--ink)',wire=`fill="none" stroke="${color}" stroke-width="2.5"`,text=(x,y,value)=>`<text x="${x}" y="${y}" fill="${color}" text-anchor="middle" font-size="16" direction="ltr">${value}</text>`;
    const r=(x,y,label,value)=>`<rect x="${x-40}" y="${y-13}" width="80" height="26" fill="var(--card)" stroke="${color}" stroke-width="2"/>${text(x,y-23,label)}${text(x,y+43,fmt(value)+' '+q.resistanceUnit)}`;
    let content=`<path d="M55 125V45H510V255H55V165" ${wire}/><circle cx="55" cy="145" r="20" fill="var(--card)" stroke="${color}" stroke-width="2"/>${text(55,151,'+ −')}${text(55,199,fmt(q.u)+' V')}`;
    if(stage===0){content=`<path d="M55 125V45H180M390 45H510V255H55V165M180 45V195M390 45V195" ${wire}/><circle cx="55" cy="145" r="20" fill="var(--card)" stroke="${color}" stroke-width="2"/>${text(55,151,'+ −')}${text(55,199,fmt(q.u)+' V')}`;
      [45,120,195].forEach((y,i)=>{content+=`<path d="M180 ${y}H245M325 ${y}H390" ${wire}/>`+r(285,y,'R'+(i+1),q.r[i]);});content+=r(445,255,'R4',q.r4);
    }else if(stage===1){content+=r(285,45,'Rₚ',q.rp)+r(285,255,'R4',q.r4);}
    else content+=r(285,45,'Rₜ',q.rt);
    return `<svg viewBox="0 0 560 320" role="img" aria-label="${stage===0?'המעגל המקורי: שלושה ענפים במקביל ונגד בטור':stage===1?'החלפת קבוצת המקביל בנגד שקול':'צמצום כל המעגל לנגד שקול אחד'}">${content}</svg>`;
  }
  return {random,mixed,battery,internalResistance,batch,mixedSVG};
})();
if(typeof module!=='undefined')module.exports=CoursePractice;

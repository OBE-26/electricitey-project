/* Course navigation, theory UI, and additional practice. Uses the existing tools. */
const CourseApp = window.CourseApp = (() => {
  let screen='home',extra=null,selected='hvac',config={names:{hvac:'קורס מיזוג וקירור',security:'קורס מיגון',mobile:'קורס סלולר'}};
  let theoryGeneration=0;
  let adminToken='',examToken='',adminConfig=null,adminDraft=null,qaReturn=null,pending=null,ready=false;
  let extraLevel=0,extraState={},extraMessage='',extraError=false,examMessage='',examError=false,examBusy=false,finishConfirm=false;
  const rootPersonal='dc.basics.personal.v1',entryKey='dc.basics.entry.v1',examKey='dc.basics.theory.v1';
  const get=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}};
  const put=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));}catch{storageAvailable=false;showStorageNotice();}};
  let theory=get(examKey,{seen:[],previous:[],history:[],current:null});
  if(!Array.isArray(theory.seen)||!Array.isArray(theory.previous)||!Array.isArray(theory.history))theory={seen:[],previous:[],history:[],current:null};
  function saveTheory(){if(!qaActive)put(examKey,theory);}
  const extKey=()=>`dc.basics.extra.${selected}.v1`;
  const nonce=()=>crypto.randomUUID?.()??`course-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const status=(message,error=false)=>message?`<div class="feedback ${error?'error':'success'}" role="status">${escapeHTML(message)}</div>`:'';
  const math=(formula)=>mathNotation(formula);
  function courseIcon(id){
    const paths={
      hvac:'<rect x="5" y="6" width="38" height="20" rx="4"/><path d="M9 19h30M12 23h24M35 11h3M14 31v5c0 3-3 3-3 6M24 31v10M34 31v5c0 3 3 3 3 6"/>',
      security:'<path d="M24 4 41 11v12c0 11-9 18-17 22C16 41 7 34 7 23V11z"/><rect x="16" y="21" width="16" height="13" rx="3"/><path d="M19 21v-4a5 5 0 0 1 10 0v4M24 27v3"/>',
      mobile:'<rect x="12" y="3" width="24" height="42" rx="5"/><path d="M20 8h8M21 39h6M17 14h14v19H17z"/>'
    };
    return `<svg class="course-icon" data-course-icon="${id}" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${paths[id]??''}</svg>`;
  }
  const number=(value,unit)=>`<span class="course-quantity">${math(DC.fmt(value))}<span class="math-unit">${escapeHTML(unit)}</span></span>`;
  function request(action,data={}){
    if(!ready)return Promise.reject(Error('החיבור לאתר עדיין נטען. נסו שוב בעוד רגע.'));
    if(pending)return Promise.reject(Error('ממתינים לסיום הפעולה הקודמת.'));
    return new Promise((resolve,reject)=>{
      const id=nonce(),timer=setTimeout(()=>{if(pending?.id===id){pending=null;reject(Error('הפעולה מתעכבת. אפשר לנסות שוב.'));}},40000);
      pending={id,resolve,reject,timer};
      sendStreamlitMessage('streamlit:setComponentValue',{value:{type:'course',id,action,...data},dataType:'json'});
    });
  }
  function applyConfig(value){
    if(value?.names)config={...config,...value,names:{...config.names,...value.names}};
    document.querySelectorAll('[data-course-name]').forEach(node=>node.textContent=config.names[node.dataset.courseName]??'');
    $('course-title').innerHTML=courseIcon(selected)+`<span>${escapeHTML(config.names[selected])}</span>`;
  }
  function syncProfile(){
    if(personal.profile)put(entryKey,{profile:personal.profile,preferences:personal.preferences});
  }
  function setKeys(id){
    courseProfile=id;courseKey='dc.basics.course.v1'+(id==='hvac'?'':'.'+id);
    personalKey=rootPersonal+(id==='hvac'?'':'.'+id);
    recentKey='dc.basics.recent.v1'+(id==='hvac'?'':'.'+id);
  }
  function switchCourse(id){
    if(!Object.hasOwn(config.names,id))return;
    if(!qaActive){saveCourse();savePersonal();}
    const shared=get(entryKey,null)??{profile:personal.profile,preferences:personal.preferences};
    selected=id;setKeys(id);personal=loadPersonal();
    if(shared?.profile)personal.profile=shared.profile;
    if(shared?.preferences)personal.preferences=shared.preferences;
    activeSessionId=null;previous=get(recentKey,[]);
    levels={ohm:0,series:0,parallel:0};tab='ohm';viewTab='ohm';
    extraState=get(extKey(),{});extra=null;extraLevel=0;extraMessage='';
    screen=id==='hvac'?'menu':'practice';
    if(qaActive||!restoreCourse())newCourse();
    applyPreferences();render();window.scrollTo(0,0);
  }
  function showPractice(){screen='practice';extra=null;}
  function backHome(){if(!qaActive){saveCourse();savePersonal();}screen='home';extra=null;render();window.scrollTo(0,0);}
  function saveExtra(){if(!qaActive)put(extKey(),extraState);}
  function currentExtra(){
    const key=extra+':'+extraLevel;
    if(!extraState[key]||!Array.isArray(extraState[key].questions)||extraState[key].questions.length!==10||extra==='mixed'&&extraState[key].questions.some(q=>q.schemaVersion!==2)){
      const seed=crypto.getRandomValues(new Uint32Array(1))[0];
      extraState[key]={seed,index:0,questions:CoursePractice.batch(selected,extra,extraLevel,seed)};
    }
    const state=extraState[key];state.index=Math.max(0,Math.min(9,state.index??0));
    return {state,q:state.questions[state.index]};
  }
  function tabMarkup(){return (selected==='security'?['mixed','battery','formulas']:selected==='mobile'?['battery','formulas']:[]).map(kind=>`<button class="tab" type="button" role="tab" id="tab-${kind}" aria-controls="course-panel" data-extra-tab="${kind}" aria-selected="${extra===kind}" tabindex="${extra===kind?0:-1}">${kind==='formulas'?'דף נוסחאות':kind==='mixed'?'מעגל מעורב מורכב':'סוללות'}<span>${kind==='formulas'?'חשמל וסוללות':kind==='mixed'?'טור של קבוצות מקבילות · מקביל של ענפי טור':selected==='mobile'?'מטען · טעינה ופריקה · התנגדות פנימית':'מטען ואנרגיה · טעינה ופריקה'}</span></button>`).join('');}
  function updateChrome(){
    const practice=screen==='practice';
    document.body.classList.toggle('course-home',screen==='home');
    document.body.classList.toggle('course-menu',!practice&&screen!=='home');
    document.body.classList.toggle('course-theory',screen.startsWith('theory'));
    $('course-navigation').hidden=screen==='home';
    $('course-panel').hidden=practice&&!extra;
    document.querySelector('.tabs').hidden=!practice;
    $('learning-main').hidden=!practice||!!extra;
    $('course-optional-tabs').innerHTML=tabMarkup();
    document.querySelectorAll('[role="tab"][data-tab]').forEach(node=>{if(extra){node.setAttribute('aria-selected','false');node.tabIndex=-1;}});
    applyConfig(config);
  }
  function renderOverride(){
    updateChrome();
    if(screen==='practice'&&!extra)return false;
    hideIconTooltip();renderQA();
    const panel=$('course-panel');
    if(screen==='home')panel.innerHTML=`<h1 class="sr-only">בחירת קורס</h1><div class="course-choices">${Object.keys(config.names).map(id=>`<button class="btn course-choice" data-select-course="${id}">${courseIcon(id)}<span data-course-name="${id}">${escapeHTML(config.names[id])}</span></button>`).join('')}</div>`;
    else if(screen==='menu')panel.innerHTML=`<h1 class="sr-only">${escapeHTML(config.names[selected])}</h1><div class="course-choices"><button class="btn course-choice" data-course-action="practice">תרגילים</button><button class="btn course-choice" data-course-action="theory">שאלות למבחן עיוני</button></div>`;
    else if(screen==='theory-result')renderTheoryResult();
    else if(screen==='theory'||screen==='theory-review')renderTheory();
    else if(screen==='theory-progress')renderTheoryProgress();
    else if(extra==='formulas')renderCourseFormulas();
    else if(extra)renderExtra();
    fitDialogs();resizeFrame();return true;
  }
  function statementRows(q){return q.givens.map(([key,value,unit])=>`<div class="given"><small>${math(key)}</small>${number(value,unit)}</div>`).join('');}
  function notationKey(){return `<div class="battery-key"><span>${math('U_t')} — מתח הסוללה ללא עומס</span><span>${math('ΔU')} — מפל המתח על ההתנגדות הפנימית</span><span>${math('U_L')} — מתח עומס</span><span>${math('R_s')} — התנגדות פנימית</span></div>`;}
  function solutionRows(q,steps=q.steps){return steps.map(s=>`<div class="course-solution-step"><strong>${escapeHTML(s.label)}</strong><div class="math">${math(s.formula)}</div><div class="math">${math(s.substitution)} <span>=</span> ${number(s.value,s.unit)}</div></div>`).join('');}
  function courseSimulatorDisplay(q){
    if(q.kind==='mixed'){
      const u=Number(q.simVoltage??q.u),ratio=q.u?u/q.u:0,scale2=ratio*ratio;
      return `<figure class="diagram course-sim-diagram">${CoursePractice.mixedSVG({...q,u},0)}</figure><p class="sim-legend"><span class="current">הזרם מוצג באדום</span></p><div class="metrics"><div class="metric"><small>התנגדות שקולה</small><bdi>${DC.fmt(q.rt)} ${escapeHTML(q.resistanceUnit)}</bdi></div><div class="metric"><small>זרם כולל</small><bdi>${DC.fmt(q.it*ratio)} ${escapeHTML(q.currentUnit)}</bdi></div><div class="metric"><small>הספק כולל</small><bdi>${DC.fmt(q.u*q.it*scale2)} ${escapeHTML(q.powerUnit)}</bdi></div></div><div class="course-table"><table><thead><tr><th>נגד</th><th>זרם</th><th>מתח</th><th>הספק</th></tr></thead><tbody>${q.r.map((r,i)=>`<tr><td>R${i+1} · ${DC.fmt(r)} ${escapeHTML(q.resistanceUnit)}</td><td>${DC.fmt(q.currents[i]*ratio)} ${escapeHTML(q.currentUnit)}</td><td>${DC.fmt(q.voltages[i]*ratio)} V</td><td>${DC.fmt(q.powers[i]*scale2)} ${escapeHTML(q.powerUnit)}</td></tr>`).join('')}</tbody></table></div>`;
    }
    if(q.unitFamily==='Rs'){
      const given=Object.fromEntries(q.givens.map(([k,v])=>[k,v])),base=given.U_L/given.I,rl=Number(q.simLoadResistance??base),current=given.U_t/(q.rs+rl),ul=current*rl,drop=current*q.rs;
      const model={...q,solution:true,cursor:2,givens:[['U_t',given.U_t,'V'],['U_L',ul,'V'],['I',current,'A']],simLoadResistance:rl};
      return `<figure class="diagram phone-schematic">${CoursePractice.phoneBatterySVG(model)}</figure><div class="metrics"><div class="metric"><small>זרם במעגל</small><bdi>${DC.fmt(current)} A</bdi></div><div class="metric"><small>מתח על העומס</small><bdi>${DC.fmt(ul)} V</bdi></div><div class="metric"><small>מפל מתח פנימי</small><bdi>${DC.fmt(drop)} V</bdi></div><div class="metric"><small>התנגדות עומס</small><bdi>${DC.fmt(rl)} Ω</bdi></div></div>`;
    }
    return '<p class="small muted">לתרגיל הזה אין כרגע סימולציה. בחרו תרגיל מעגל מעורב או התנגדות פנימית.</p>';
  }
  function courseSimulatorHTML(q){
    if(!q.simulatorOpen||q.cursor<q.steps.length)return '';
    if(q.kind==='mixed'){
      const value=Number(q.simVoltage??q.u),max=Math.max(1,q.u*2);
      return `<section class="card course-simulator"><div class="sim-head"><h3>סימולטור המעגל</h3><button class="btn secondary tiny" data-course-action="simulator">סגירת סימולטור</button></div><label for="course-sim-voltage">מתח מקור: <bdi id="course-sim-voltage-value">${DC.fmt(value)} V</bdi></label><input id="course-sim-voltage" type="range" min="0" max="${max}" step="${Math.max(.01,max/1000)}" value="${value}"><div id="course-sim-display">${courseSimulatorDisplay(q)}</div><button class="btn secondary tiny" data-course-action="reset-simulator">חזרה למתח התרגיל</button></section>`;
    }
    if(q.unitFamily==='Rs'){
      const given=Object.fromEntries(q.givens.map(([k,v])=>[k,v])),base=given.U_L/given.I,value=Number(q.simLoadResistance??base),min=Math.max(.001,base/4),max=Math.max(min*2,base*4);
      return `<section class="card course-simulator"><div class="sim-head"><h3>סימולטור ההתנגדות הפנימית</h3><button class="btn secondary tiny" data-course-action="simulator">סגירת סימולטור</button></div><label for="course-sim-load">התנגדות העומס: <bdi id="course-sim-load-value">${DC.fmt(value)} Ω</bdi></label><input id="course-sim-load" type="range" min="${min}" max="${max}" step="${Math.max(.001,(max-min)/1000)}" value="${value}"><div id="course-sim-display">${courseSimulatorDisplay(q)}</div><button class="btn secondary tiny" data-course-action="reset-simulator">חזרה לנתוני התרגיל</button></section>`;
    }
    return `<section class="card course-simulator"><div class="sim-head"><h3>סימולטור</h3><button class="btn secondary tiny" data-course-action="simulator">סגירה</button></div>${courseSimulatorDisplay(q)}</section>`;
  }
  function updateCourseSimulator(q){const display=document.getElementById('course-sim-display');if(display)display.innerHTML=courseSimulatorDisplay(q);const v=document.getElementById('course-sim-voltage-value');if(v)v.textContent=`${DC.fmt(q.simVoltage)} V`;const r=document.getElementById('course-sim-load-value');if(r)r.textContent=`${DC.fmt(q.simLoadResistance)} Ω`;}
  function nodeGuide(q){
    return `<div class="mixed-node-guide"><p><strong>סימון צמתים:</strong> מעבר לכל נגד מגיעים לצומת אחרת. לאורך מוליך רציף נשארת אותה אות. ענפים במקביל מחוברים לאותן שתי צמתים.</p><details><summary>מפת החיבורים לפי הצמתים</summary><div class="mixed-node-map">${q.resistorNodes.map((nodes,i)=>`<span>${math('R'+(i+1))}: <bdi>${nodes.from} ↔ ${nodes.to}</bdi></span>`).join('')}</div></details></div>`;
  }
  function mixedPreview(q,stage=0){return `<button type="button" class="diagram-preview" data-open-mixed="${stage}" aria-label="הגדלת סכמה ${stage===0?'מקורית':'לאחר צמצום '+stage}">${CoursePractice.mixedSVG(q,stage)}<span class="diagram-open-label">הגדלת הסכמה ⤢</span></button>`;}
  function openMixedDiagram(stage){
    const {q}=currentExtra();if(q.kind!=='mixed')return;
    diagramReturnToFormulas=false;diagramReturnFieldId=null;diagramZoom=1;diagramBaseWidth=0;
    $('diagram-dialog').classList.remove('dark-diagram');
    $('diagram-context').innerHTML=`<h3>${escapeHTML(q.title)}</h3><p>${stage===0?'המעגל המקורי':escapeHTML(q.reductions[stage-1].title)}</p>`;
    $('diagram-canvas').innerHTML=CoursePractice.mixedSVG(q,stage);
    $('diagram-canvas').style.width='100%';openDialog('diagram-dialog');zoomDiagram('reset');
  }
  function renderExtra(){
    const {state,q}=currentExtra(),s=q.steps[q.cursor],done=!s,levelCount=selected==='mobile'?2:3;
    const levelsHTML=Array.from({length:levelCount},(_,i)=>`<button class="level" data-extra-level="${i}" aria-pressed="${extraLevel===i}">רמה ${letters[i]}<small>${extra==='mixed'?DC.levelNames[i]:i===0?'חישובים בסיסיים':i===1?'מספרים עשרוניים':'המרת דקות לשעות'}</small></button>`).join('');
    const qaPicker=qaActive?`<label class="qa-extra-picker" for="qa-extra-exercise">תרגיל לבדיקה<select id="qa-extra-exercise">${state.questions.map((item,i)=>`<option value="${i}" ${state.index===i?'selected':''}>${i+1}. ${escapeHTML(item.title)}</option>`).join('')}</select></label>`:'';
    const picture=q.unitFamily==='Rs'?`<figure class="diagram phone-schematic">${CoursePractice.phoneBatterySVG(q)}<figcaption>מודל שקול של סוללת טלפון. ההתנגדות הפנימית מחוברת בטור לעומס של מעגלי הטלפון.</figcaption></figure>`:extra==='mixed'?`<figure class="diagram mixed-schematic">${mixedPreview(q)}<figcaption>${escapeHTML(q.caption)}</figcaption></figure>${nodeGuide(q)}`:'';
    const reduction=extra==='mixed'?`<div class="circuit-reductions"><h3>צמצום המעגל לפי הצמתים</h3>${q.reductions.map((item,i)=>`<section class="circuit-reduction"><h4>${i+1}. ${escapeHTML(item.title)}</h4>${solutionRows(q,item.steps)}<figure class="diagram">${mixedPreview(q,i+1)}</figure></section>`).join('')}<p class="small muted">אותיות הצמתים נשמרות. צומת פנימית שנבלעה בנגד שקול אינה מסומנת בסכמה המצומצמת.</p></div>`:'';
    const remainingSteps=extra==='mixed'?q.steps.slice(q.reductions.reduce((sum,item)=>sum+item.steps.length,0)):q.steps;
    const answer=done?`<div class="complete-badge">✓ התרגיל הושלם</div><h2>כל החישובים הושלמו</h2><button class="btn" data-extra-action="next">${state.index===9?'סבב חדש':'לתרגיל הבא ←'}</button>`:`<div class="task-kicker">שלב ${q.cursor+1} מתוך ${q.steps.length}</div><h2>${escapeHTML(s.label)}</h2><form id="extra-answer-form"><label for="extra-answer">התשובה ביחידות ${escapeHTML(s.unit)}</label><div class="answer-row"><div class="answer-wrap"><input class="numeric${q.accepted?' answer-correct':q.attempts?' answer-incorrect':''}" id="extra-answer" inputmode="decimal" autocomplete="off" maxlength="24" value="${escapeHTML(q.draft??'')}" ${q.accepted?'readonly':''}><span class="unit">${escapeHTML(s.unit)}</span></div><button class="btn" type="${q.accepted?'button':'submit'}" ${q.accepted?'data-extra-action="step"':''}>${q.accepted?'הבא ←':'בדיקת תשובה'}</button></div></form><p class="small muted">אפשר לעגל לשתי ספרות אחרי הנקודה.</p>`;
    const simulatorEligible=done&&(q.kind==='mixed'||q.unitFamily==='Rs'),simulatorButton=simulatorEligible?`<button class="btn soft tiny" data-course-action="simulator">${q.simulatorOpen?'סגירת סימולטור':'סימולטור'}</button>`:'';
    $('course-panel').innerHTML=`<div class="course-head"><h2>${extra==='mixed'?'מעגל מעורב מורכב':'חישובי סוללות'}</h2><div class="levels">${levelsHTML}</div></div>${qaPicker}<div class="progress-row"><span>תרגיל ${state.index+1} מתוך 10</span><span>רמה ${letters[extraLevel]}</span></div><div class="exercise-grid"><section class="card"><h3>${escapeHTML(q.title)}</h3>${q.text?`<p>${escapeHTML(q.text)}</p>`:''}<div class="givens">${statementRows(q)}</div>${picture}${q.unitFamily==='Rs'?notationKey():''}${q.kind==='battery'&&q.unitFamily!=='Rs'?`<p class="small muted">${escapeHTML(q.note)}</p>`:''}</section><section class="card">${answer}<div class="answer-tools"><button class="btn secondary tiny" data-extra-action="hint">רמז</button><button class="btn secondary tiny" data-extra-action="solution">${q.solution?'סגירת פתרון מלא':'פתרון מלא'}</button>${simulatorButton}<button class="btn secondary tiny" data-open-calculator>מחשבון</button><button class="btn secondary tiny" data-extra-action="new">תרגילים חדשים</button></div>${status(extraMessage,extraError)}${q.hint&&s?`<div class="hint">השתמשו בנוסחה ${math(s.formula)}</div>`:''}${q.solution?`<div class="solution"><div class="dialog-head"><h3>פתרון מלא</h3><button class="close" data-extra-action="solution" aria-label="סגירת פתרון מלא">×</button></div>${reduction}${solutionRows(q,remainingSteps)}</div>`:''}${done?`<div class="completed-steps">${solutionRows(q)}</div>`:''}${(done||q.solution)&&q.unitFamily==='Rs'?`<p class="small muted">${escapeHTML(q.note)}</p>`:''}</section></div>${courseSimulatorHTML(q)}`;
    saveExtra();
  }
  function markExtraHelp(q){
    if(qaActive||q.helped)return;q.helped=true;
    personal.totals.helped++;personal.topics[extra].helped++;savePersonal();
  }
  function checkExtra(){
    const {q}=currentExtra(),s=q.steps[q.cursor];if(!s||q.accepted)return;
    q.draft=$('extra-answer').value;
    const correct=DC.accepted(q.draft,s.value),attempt=q.attempts??0;
    if(!qaActive&&profileReady()){
      for(const counters of [personal.totals,personal.topics[extra]]){if(!attempt)counters.attempted++;counters.attempts++;if(correct){counters.solved++;if(!attempt)counters.first++;}}
      const session=currentSession();if(!attempt){session.attempted++;if(correct)session.first++;}
      if(correct&&q.cursor===q.steps.length-1)personal.totals.exercises++;
      savePersonal();
    }
    q.attempts=attempt+1;q.accepted=correct;extraMessage=correct?'נכון! אפשר להמשיך לשלב הבא.':'התשובה אינה נכונה. אפשר לנסות שוב.';extraError=!correct;
    render();$('extra-answer')?.focus();
  }
  function extraAction(action){
    const {state,q}=currentExtra();extraMessage='';extraError=false;
    if(action==='hint'){q.hint=!q.hint;if(q.hint)markExtraHelp(q);}
    if(action==='solution'){q.solution=!q.solution;if(q.solution)markExtraHelp(q);}
    if(action==='simulator'&&q.cursor>=q.steps.length){q.simulatorOpen=!q.simulatorOpen;if(q.simulatorOpen&&q.kind==='mixed')q.simVoltage??=q.u;if(q.simulatorOpen&&q.unitFamily==='Rs'){const g=Object.fromEntries(q.givens.map(([k,v])=>[k,v]));q.simLoadResistance??=g.U_L/g.I;}}
    if(action==='reset-simulator'){if(q.kind==='mixed')q.simVoltage=q.u;else if(q.unitFamily==='Rs'){const g=Object.fromEntries(q.givens.map(([k,v])=>[k,v]));q.simLoadResistance=g.U_L/g.I;}}
    if(action==='step'&&q.accepted){q.cursor++;q.accepted=false;q.attempts=0;q.draft='';q.hint=false;}
    if(action==='next'){if(state.index<9)state.index++;else delete extraState[extra+':'+extraLevel];}
    if(action==='new')delete extraState[extra+':'+extraLevel];
    render();
  }
  function examChoices(q,index,result=false){
    const chosen=result?q.selected_choice_id:theory.current?.answers?.[q.id];
    return q.choices.map(c=>{
      const correct=result&&c.id===q.correct_choice_id,wrong=result&&chosen===c.id&&!correct;
      return `<label class="theory-choice${correct?' theory-correct':wrong?' theory-wrong':''}"><input type="radio" name="theory-${q.id}" value="${escapeHTML(c.id)}" data-theory-answer="${escapeHTML(q.id)}" ${chosen===c.id?'checked':''} ${result?'disabled':''}><span><strong>${escapeHTML(c.label)}.</strong> ${escapeHTML(c.text)}${correct?' <strong>✓ התשובה הנכונה</strong>':wrong?' <strong>✕ התשובה שבחרת</strong>':''}</span></label>`;
    }).join('');
  }
  function questionHTML(q,index,result=false){
    const unanswered=result&&!q.selected_choice_id;
    // The one bank formula is rendered as native MathML, without a CDN dependency.
    const formula=q.math_latex?`<div class="math"><math dir="ltr"><mi>ρ</mi><mo>=</mo><mn>0.018</mn><mfrac><mrow><mi>Ω</mi><mo>·</mo><msup><mi>mm</mi><mn>2</mn></msup></mrow><mi>m</mi></mfrac></math></div>`:'';
    return `<section class="card theory-question" id="theory-q-${index}"><h3>${index+1}. ${escapeHTML(q.text)}</h3>${formula}${q.figure?`<figure class="theory-figure"><img src="${escapeHTML(q.figure.src)}" alt="${escapeHTML(q.figure.alt)}"></figure>`:''}<fieldset><legend class="sr-only">בחירת תשובה לשאלה ${index+1}</legend>${examChoices(q,index,result)}</fieldset>${unanswered?'<p class="feedback error">לא נבחרה תשובה לשאלה זו.</p>':''}</section>`;
  }
  function renderTheoryResult(){
    if(!qaActive&&!examToken)return renderTheory();
    const current=theory.current,result=current?.result;
    if(!result){screen='theory';return renderTheory();}
    const learner=current.learnerName||personal.profile?.name||'לומד/ת';
    const unanswered=result.questions.filter(q=>!q.selected_choice_id).length;
    $('course-panel').innerHTML=`<section class="card theory-summary theory-result-page" role="status"><div class="eyebrow">${qaActive?'תוצאת מבחן בדיקה':'תוצאות המבחן העיוני'}</div><h1>${escapeHTML(learner)}</h1><p class="muted">הציון שלך במבחן</p><p class="theory-score">${Math.round(result.correct/result.total*100)}%</p><h2>${result.correct} מתוך ${result.total} תשובות נכונות</h2>${unanswered?`<p>${unanswered} שאלות לא נענו.</p>`:''}${qaActive?'<p class="small muted">התוצאה אינה נשמרת בדירוג האישי.</p>':''}<div class="completion-actions"><button class="btn" data-theory-action="review">מעבר על התשובות</button><button class="btn secondary" data-theory-action="new">20 שאלות חדשות</button><button class="btn secondary" data-theory-action="progress">דירוג עצמי</button></div>${status(examMessage,examError)}</section>`;
  }
  function renderTheory(){
    const panel=$('course-panel');
    if(!qaActive&&!examToken){panel.innerHTML=`<section class="card theory-login"><h1>שאלות למבחן עיוני</h1><p>מבחן של 20 שאלות מהמאגר, ללא הגבלת זמן.</p><form id="theory-login-form"><label for="theory-password">סיסמת כניסה</label><input id="theory-password" type="password" autocomplete="current-password" maxlength="128" required><button class="btn" ${examBusy?'disabled':''}>כניסה למבחנים</button></form>${status(examMessage,examError)}</section>`;return;}
    const current=theory.current,result=current?.result;
    if(result&&screen!=='theory-review'){screen='theory-result';return renderTheoryResult();}
    panel.innerHTML=`<div class="course-head"><div><h1>${result?'סקירת תשובות':'מבחן עיוני'}</h1><p class="muted">20 שאלות · ללא הגבלת זמן${qaActive?' · מצב בדיקות':''}</p></div><div class="completion-actions">${result?'<button class="btn" data-theory-action="result">חזרה לציון</button>':''}<button class="btn" data-theory-action="new" ${examBusy?'disabled':''}>שאלות חדשות</button><button class="btn secondary" data-theory-action="progress">דירוג עצמי</button><button class="btn secondary" data-open-calculator>מחשבון</button>${qaActive?'':'<button class="btn secondary tiny" data-theory-action="logout">יציאה מהמבחנים</button>'}</div></div>${status(examMessage,examError)}${current?`<div class="theory-grid">${(result?.questions??current.questions).map((q,index)=>questionHTML(q,index,!!result)).join('')}</div>${!result?`<div class="theory-submit"><p id="theory-answered">נענו ${Object.keys(current.answers??{}).length} מתוך 20 שאלות</p>${finishConfirm?'<p class="feedback error">נותרו שאלות ללא תשובה. הגשה עכשיו תחשיב אותן כשגויות.</p>':''}<button class="btn" data-theory-action="submit" ${examBusy?'disabled':''}>${finishConfirm?'הגשת המבחן עם השאלות שלא נענו':'בדוק מבחן'}</button></div>`:''}`:`<section class="card"><p>מוכנים להתחיל?</p><button class="btn" data-theory-action="new" ${examBusy?'disabled':''}>הגרלת 20 שאלות</button></section>`}`;
  }
  async function theoryRequest(action){
    if(examBusy)return;const generation=theoryGeneration,qaRequest=qaActive;examBusy=true;examMessage='';examError=false;
    if(action==='submit'&&Object.keys(theory.current?.answers??{}).length<20&&!finishConfirm){finishConfirm=true;examBusy=false;render();return;}
    if(action==='new'&&theory.current&&!theory.current.result&&Object.keys(theory.current.answers??{}).length&&!theory.current.replaceConfirm){theory.current.replaceConfirm=true;examMessage='כדי להחליף את המבחן שלא הסתיים, לחצו שוב על ״שאלות חדשות״.';examBusy=false;render();return;}
    render();
    try{
      const reply=await request('exam_'+action,{token:qaActive?adminToken:examToken,qa:qaActive,...action==='new'?{seen:theory.seen,previous:theory.previous}:{exam:theory.current?.exam,answers:theory.current?.answers??{}}});
      if(generation!==theoryGeneration||qaRequest!==qaActive)return;
      if(!reply.ok){if(reply.unauthorized)examToken='';throw Error(reply.message);}
      if(action==='new'){
        const ids=reply.questions.map(q=>q.id);theory.previous=ids;
        theory.seen=[...theory.seen.filter(id=>!ids.includes(id)),...ids];
        theory.current={id:reply.id,exam:reply.exam,questions:reply.questions,answers:{},result:null};finishConfirm=false;screen='theory';
      }else if(action==='submit'){
        theory.current.result=reply;theory.current.learnerName=personal.profile?.name||'לומד/ת';screen='theory-result';
        if(!qaActive&&!theory.history.some(item=>item.id===reply.id))theory.history.push({id:reply.id,correct:reply.correct,total:reply.total,finished_at:reply.finished_at});
      }else if(action==='resume'&&theory.current){theory.current.questions=reply.questions;}
      saveTheory();
    }catch(error){if(generation!==theoryGeneration)return;examMessage=error.message;examError=true;}
    examBusy=false;render();if(action!=='resume')window.scrollTo(0,0);
  }
  async function theoryLogin(){
    if(examBusy)return;const password=$('theory-password').value;examBusy=true;examMessage='';render();
    try{const reply=await request('exam_login',{password});if(!reply.ok)throw Error(reply.message);examToken=reply.token;}
    catch(error){examMessage=error.message;examError=true;}
    examBusy=false;render();
    if(examToken&&theory.current)await theoryRequest('resume');
    else if(examToken)await theoryRequest('new');
  }
  function renderTheoryProgress(){
    const history=theory.history,visible=history.slice(-25),offset=history.length-visible.length;
    const points=visible.map((h,i)=>[60+(visible.length===1?240:i*480/(visible.length-1)),210-h.correct/h.total*170]);
    const chart=history.length?`<svg class="theory-chart" viewBox="0 0 600 270" role="img" aria-label="אחוז תשובות נכונות לפי מספר מבחן"><path d="M60 30V210H555" fill="none" stroke="var(--ink)"/>${[0,25,50,75,100].map(v=>`<path d="M60 ${210-v*1.7}H555" stroke="var(--line)"/><text x="45" y="${215-v*1.7}" text-anchor="end" fill="var(--ink)">${v}%</text>`).join('')}<polyline points="${points.map(p=>p.join(',')).join(' ')}" fill="none" stroke="var(--green)" stroke-width="3"/>${points.map(([x,y],i)=>`<circle cx="${x}" cy="${y}" r="5" fill="var(--green)"><title>מבחן ${offset+i+1}: ${visible[i].correct} מתוך 20</title></circle><text x="${x}" y="230" text-anchor="middle" fill="var(--ink)">${offset+i+1}</text>`).join('')}<text x="305" y="260" text-anchor="middle" fill="var(--ink)">מספר מבחן</text></svg>`:'<p>לאחר השלמת המבחן הראשון תוצג כאן ההתקדמות.</p>';
    $('course-panel').innerHTML=`<div class="course-head"><h1>הדירוג העצמי שלי</h1><button class="btn secondary" data-theory-action="return">חזרה למבחן</button></div><section class="card"><h2>אחוז תשובות נכונות לאורך המבחנים</h2><div class="theory-chart-wrap">${chart}</div><p class="small muted">${history.length} מבחנים הושלמו. הגרף מציג עד 25 מבחנים אחרונים.</p>${history.length?`<div class="course-table"><table><thead><tr><th>מבחן</th><th>תאריך</th><th>תשובות נכונות</th><th>ציון</th></tr></thead><tbody>${history.map((h,i)=>`<tr><td>${i+1}</td><td>${escapeHTML(new Date(h.finished_at).toLocaleDateString('he-IL'))}</td><td>${h.correct} מתוך ${h.total}</td><td>${Math.round(h.correct/h.total*100)}%</td></tr>`).join('')}</tbody></table></div>`:''}</section>`;
  }
  async function loginAdmin(){
    const input=$('qa-password'),error=$('qa-login-error'),button=$('qa-login-form').querySelector('button');button.disabled=true;
    try{const reply=await request('admin_login',{password:input.value});if(!reply.ok)throw Error(reply.message);adminToken=reply.token;adminConfig=reply.config;adminDraft=JSON.parse(JSON.stringify(adminConfig));applyConfig(reply.config);return true;}
    catch(problem){error.textContent=problem.message;input.setAttribute('aria-invalid','true');fitDialogs();return false;}
    finally{button.disabled=false;}
  }
  function renderAdmin(){
    if(!qaActive||!adminConfig)return;
    $('course-admin')?.remove();
    const value=adminDraft??adminConfig,container=document.createElement('section');container.id='course-admin';container.className='qa-banner';
    container.innerHTML=`<div class="qa-course-switch"><label for="qa-course-switch">מעבר מהיר בין קורסים<select id="qa-course-switch">${Object.entries(config.names).map(([id,name])=>`<option value="${id}" ${selected===id?'selected':''}>${escapeHTML(name)}</option>`).join('')}</select></label>${selected==='hvac'?'<button class="btn" data-course-action="theory">מבחן עיוני ללא סיסמה נוספת</button>':''}</div><h2>ניהול קורסים וגישה למבחן העיוני</h2><form id="course-admin-form"><div class="qa-selectors">${Object.keys(config.names).map(id=>`<label>שם כפתור הקורס<input data-admin-name="${id}" value="${escapeHTML(value.names[id])}" maxlength="60" required></label>`).join('')}</div><h3>סיסמאות למבחן העיוני במיזוג וקירור</h3><p class="small">תוקף הסיסמה כולל את כל התאריך שנבחר, לפי שעון ישראל. תאריך ריק משאיר את הסיסמה ללא תאריך תפוגה.</p><div id="admin-passwords">${value.passwords.map((row,i)=>`<div class="admin-password-row"><label>שם הסיסמה<input data-admin-row="${i}" data-field="label" value="${escapeHTML(row.label)}" maxlength="60" required></label><label>${row.id?'החלפת סיסמה (רשות)':'סיסמה חדשה'}<input type="password" autocomplete="new-password" data-admin-row="${i}" data-field="password" minlength="4" maxlength="128" value="${escapeHTML(row.password??'')}" ${row.id?'':'required'}></label><label>בתוקף עד<input type="date" data-admin-row="${i}" data-field="expires_on" value="${escapeHTML(row.expires_on)}"></label><label class="admin-active"><input type="checkbox" data-admin-row="${i}" data-field="active" ${row.active?'checked':''}> פעילה</label><button class="btn secondary tiny" type="button" data-remove-password="${i}">הסרה</button></div>`).join('')}</div><div class="completion-actions"><button class="btn secondary" type="button" data-course-action="add-password">הוספת סיסמה</button><button class="btn" type="submit">שמירת שמות וסיסמאות</button></div><div id="admin-status" role="status"></div>${!value.durable?'<p class="small muted">השינויים משותפים לכל המשתמשים בשרת הנוכחי. לשמירה גם לאחר התקנה מחדש יש להגדיר אחסון קבוע לפי README.</p>':''}</form>`;
    $('qa-panel').append(container);
  }
  async function saveAdmin(){
    const message=$('admin-status'),button=$('course-admin-form').querySelector('[type="submit"]');button.disabled=true;message.textContent='שומרים…';
    try{const reply=await request('admin_save',{token:adminToken,names:adminDraft.names,passwords:adminDraft.passwords});if(!reply.ok)throw Error(reply.message);adminConfig=reply.config;adminDraft=JSON.parse(JSON.stringify(adminConfig));applyConfig(reply.config);renderAdmin();$('admin-status').className='feedback success';$('admin-status').textContent=reply.message;}
    catch(error){message.className='feedback error';message.textContent=error.message;button.disabled=false;}resizeFrame();
  }
  function renderCourseFormulas(){
    const card=(title,formulas,note='')=>`<section class="formula-card"><h2>${escapeHTML(title)}</h2>${formulas.map(f=>`<div class="math">${math(f)}</div>`).join('')}${note?`<p class="small muted">${escapeHTML(note)}</p>`:''}</section>`;
    const ohm=['U = I × R','I = U ÷ R','R = U ÷ I','P = U × I','P = I² × R','P = U² ÷ R','R = U² ÷ P'];
    const parallel=['R_T = (R1 × R2) ÷ (R1 + R2)','R_T = R ÷ n','I1 = U ÷ R1','I2 = U ÷ R2','I_T = I1 + I2'];
    if(selected==='security')parallel.splice(1,0,'R_T = 1 ÷ (1/R1 + 1/R2 + 1/R3)');
    $('course-panel').innerHTML=`<section class="course-formula-page"><div class="course-head"><div><h1>דף נוסחאות</h1><p class="muted">${escapeHTML(config.names[selected])}</p></div><button class="btn secondary" data-open-calculator>מחשבון</button></div><div class="formula-grid">${card('חוק אוהם והספק',ohm)}${card('מעגל טורי',['R_T = R1 + R2 + R3','I = U ÷ R_T','U1 = I × R1','U = U1 + U2 + U3'],'אותו זרם בכל הרכיבים; מתח המקור שווה לסכום מפלי המתח.')}${card('מעגל מקבילי',parallel,'אותו מתח בכל הענפים. R/n מתאים לנגדים זהים בלבד.')}${card('מטען, טעינה ופריקה',['Q = I × t','I = Q ÷ t','t = Q ÷ I','t_h = t_min ÷ 60'],'Q באמפר־שעה, I באמפר ו־t בשעות. המודל מניח זרם קבוע וללא הפסדים.')}${selected==='security'?card('אנרגיה בסוללה',['E = P × t','E = U × Q','t = E ÷ P','Q = E ÷ U'],'E בוואט־שעה, P בוואט ו־t בשעות.'):card('התנגדות פנימית של סוללת טלפון',['U_t = U_L + ΔU','ΔU = U_t − U_L','ΔU = I × R_s','R_s = ΔU ÷ I','U_L = U_t − I × R_s'])}${selected==='security'?card('נגד בטור לקבוצה מקבילה',['R234 = 1 ÷ (1/R2 + 1/R3 + 1/R4)','R_T = R1 + R234','I_T = U ÷ R_T','U1 = I_T × R1','U234 = U − U1','I2 = U234 ÷ R2','P2 = U2 × I2'],'מצמצמים את המקביל, ואז את הטור. הנגדים R2, R3, R4 מחוברים לאותן שתי צמתים. צריכת ההספק הכוללת שווה לסכום ההספקים בכל הנגדים.')+card('ענפי טור המחוברים במקביל',['R23 = R2 + R3','R_T = (R1 × R23) ÷ (R1 + R23)','I_T = U ÷ R_T','I1 = U ÷ R1','I2 = U ÷ R23','I3 = I2','U2 = I2 × R2','U3 = I3 × R3'],'מצמצמים קודם את R2 ו־R3 שבאותו ענף בטור, ואז את המקביל. לאורך מוליך רציף נשמרת אותה אות צומת; מעבר לכל נגד מגיעים לצומת אחרת.'):''}</div>${selected==='mobile'?notationKey():''}</section>`;
  }
  function appendFormulas(){
    $('course-formulas')?.remove();
    if(!['mobile','security'].includes(selected))return;
    const node=document.createElement('section');node.id='course-formulas';node.className='card';
    node.innerHTML=`<h3>סוללות — מטען, טעינה ופריקה</h3>${['Q = I × t','I = Q ÷ t','t = Q ÷ I'].map(f=>`<div class="math">${math(f)}</div>`).join('')}<p class="small">מטען באמפר־שעה, זרם באמפר וזמן בשעות.</p>${selected==='security'?['E = P × t','E = U × Q'].map(f=>`<div class="math">${math(f)}</div>`).join(''):`${notationKey()}${['U_t = U_L + ΔU','ΔU = U_t − U_L','ΔU = I × R_s','R_s = ΔU ÷ I','U_L = U_t − ΔU'].map(f=>`<div class="math">${math(f)}</div>`).join('')}`}`;
    $('formula-body').append(node);fitDialogs();
  }
  function initialize(){
    const style=document.createElement('style');style.textContent=`
      .course-panel{margin:24px 0;min-width:0}.course-choices{display:grid;gap:20px;width:min(460px,100%);margin:60px auto}.course-choice{min-height:90px;font-size:calc(23px * var(--text-scale));box-shadow:var(--shadow);display:flex;align-items:center;justify-content:center;gap:18px}.course-icon{width:42px;height:42px;flex:0 0 auto;display:inline-block;color:inherit}#course-title{display:flex;align-items:center;gap:12px}#course-title .course-icon{width:34px;height:34px}.mixed-node-guide{padding:12px;border:1px solid var(--line);border-radius:10px;font-size:calc(14px * var(--text-scale));margin-top:12px}.mixed-node-guide p{margin:0 0 10px}.mixed-node-guide summary{cursor:pointer;font-weight:700}.mixed-node-map{display:flex;flex-wrap:wrap;gap:10px 20px;padding-top:12px}.mixed-node-map>span{display:inline-flex;gap:7px;align-items:center}.circuit-reduction{padding:10px 0;border-bottom:1px solid var(--line)}.mixed-circuit-svg .mixed-junction text{font-weight:700}
      .course-home .topbar,.course-home .hero,.course-home .quickbar-space,.course-home .footer-row>div:first-child,.course-home .footer-links button:not([data-open-qa]):not([data-open-terms]):not([data-open-accessibility]){display:none}.course-home .course-panel{min-height:55vh;display:grid;align-content:center}.course-home .course-choices{width:min(460px,80vw)}
      .course-menu .hero,.course-menu .topbar,.course-menu .quickbar-space,.course-theory .hero{display:none}.course-navigation{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:16px 0}.course-navigation h2{margin:0}.course-panel .mathml{display:inline-block;vertical-align:middle}.course-quantity{display:inline-flex;gap:7px;direction:ltr;align-items:center;font-size:calc(20px * var(--text-scale))}.math-unit{font-size:.8em}.course-solution-step{padding:12px 0;border-bottom:1px solid var(--line)}.course-solution-step .math{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.battery-key{display:grid;gap:8px;padding:12px 0}.battery-key .mathml{display:inline-block}.circuit-reductions svg{width:100%;max-width:520px}.circuit-reductions p{margin-top:15px}.course-panel h1{font-size:calc(30px * var(--text-scale))}
      #course-optional-tabs{display:contents}.tabs{grid-template-columns:repeat(auto-fit,minmax(175px,1fr))}.question-dots{flex-wrap:wrap}.theory-grid{display:grid;gap:16px}.theory-question fieldset{border:0;margin:0;padding:0}.theory-choice{display:flex;gap:10px;padding:14px;margin:9px 0;border:1px solid var(--line);border-radius:10px;cursor:pointer;background:var(--card)}.theory-choice input{flex:none;align-self:flex-start;margin-top:7px;accent-color:var(--green)}.theory-choice:has(input:checked){border-color:var(--green);box-shadow:inset 0 0 0 1px var(--green)}.theory-choice.theory-correct{background:#e2f1e9;border-color:#26734c;color:#126044}.theory-choice.theory-wrong{background:#fff0ed;border-color:#a43d34;color:#933b32}.dark-mode .theory-choice.theory-correct{background:#173e30;color:#a4edc7;border-color:#518562}.dark-mode .theory-choice.theory-wrong{background:#48272c;color:#ffd2ca;border-color:#9c615b}.theory-summary{margin-bottom:22px;text-align:center}.theory-score{font-size:36px;font-weight:bold;color:var(--green);margin:0}.theory-submit{margin:24px 0;padding:20px;background:var(--card);border:1px solid var(--line);border-radius:15px}.theory-login{max-width:570px;margin:35px auto}.theory-login form{display:grid;gap:12px}.course-panel input[type=password],#course-admin input:not([type=checkbox]){width:100%;min-height:44px;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}.theory-figure{margin:14px 0;max-width:100%;background:#fff;padding:8px;border-radius:8px}.theory-figure img{display:block;max-width:100%;height:auto;margin:auto}.theory-choice.theory-correct:has(input:checked),.theory-choice.theory-wrong:has(input:checked){box-shadow:none}.dark-mode .theory-choice.theory-correct:has(input:checked){border-color:#518562}.dark-mode .theory-choice.theory-wrong:has(input:checked){border-color:#9c615b}.dark-mode .theory-figure{background:#000}.dark-mode .theory-figure img{filter:invert(1)}.admin-password-row{display:grid;grid-template-columns:1fr 1fr 1fr auto auto;gap:12px;align-items:end;border-bottom:1px solid var(--line);padding:16px 0}.admin-active{white-space:nowrap;align-self:center}.theory-chart-wrap{overflow-x:auto}.theory-chart{display:block;width:100%;min-width:540px;height:auto;direction:ltr}.course-table{overflow-x:auto}.course-table table{border-collapse:collapse;width:100%}.course-table th,.course-table td{text-align:right;padding:9px;border-bottom:1px solid var(--line)}
      .theory-result-page{max-width:720px;margin:36px auto;padding:32px}.theory-result-page .completion-actions{justify-content:center}.theory-result-page .theory-score{font-size:calc(64px * var(--text-scale))}.qa-course-switch{display:flex;gap:14px;align-items:end;flex-wrap:wrap;margin-bottom:22px}.qa-course-switch label{display:grid;gap:6px}.qa-course-switch select{min-height:46px;padding:8px;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px}.qa-extra-picker{display:grid;gap:5px;margin:12px 0}.qa-extra-picker select{padding:8px;min-height:44px;max-width:100%;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px}.phone-schematic{--phone-current:#b52e2e;--phone-voltage:#116e65}.dark-mode .phone-schematic{--phone-current:#ff6565;--phone-voltage:#65e680}.course-formula-page .math{margin:10px 0;overflow-x:auto}.course-formula-page .formula-card{margin-bottom:12px}.course-simulator{margin-top:20px}.course-simulator input[type=range]{width:100%;min-height:38px;accent-color:var(--green)}.course-simulator .mixed-circuit-svg path{stroke:#ff6565!important;stroke-dasharray:7 10;animation:courseSimFlow 1.2s linear infinite}.course-simulator .metrics{grid-template-columns:repeat(auto-fit,minmax(130px,1fr))}.course-simulator .course-table{overflow-x:auto}.course-simulator table{min-width:440px}.course-simulator .sim-legend .current{color:#b52e2e}.phone-schematic .phone-battery-svg{max-width:640px;margin:auto}@keyframes courseSimFlow{to{stroke-dashoffset:-34}}
      @media(max-width:650px){.course-navigation{flex-wrap:wrap}.course-navigation h2{font-size:20px}.course-head{flex-wrap:wrap}.course-panel .exercise-grid{grid-template-columns:1fr}.admin-password-row{grid-template-columns:1fr 1fr}.course-choice{min-height:80px}.theory-choice{padding:12px}.course-panel{margin-top:14px}.tabs{grid-template-columns:repeat(2,minmax(0,1fr))}}
    `;document.head.append(style);
    const nav=document.createElement('nav');nav.id='course-navigation';nav.className='course-navigation';nav.setAttribute('aria-label','ניווט קורסים');nav.innerHTML='<div class="completion-actions"><button class="btn secondary tiny" data-course-action="home">כל הקורסים</button><button class="btn secondary tiny" data-course-action="course-menu" id="course-back-menu">חזרה לקורס</button></div><h2 id="course-title"></h2>';
    document.querySelector('.topbar').before(nav);
    const panel=document.createElement('main');panel.id='course-panel';panel.className='course-panel';$('learning-main').before(panel);
    const optional=document.createElement('span');optional.id='course-optional-tabs';document.querySelector('.tabs').append(optional);
    const entry=get(entryKey,null);if(entry?.profile){personal.profile=entry.profile;if(entry.preferences)personal.preferences=entry.preferences;}else syncProfile();
    document.addEventListener('click',event=>{
      const b=event.target.closest('button');if(!b)return;
      if(b.hasAttribute('data-open-mixed')){event.preventDefault();event.stopImmediatePropagation();return openMixedDiagram(Number(b.dataset.openMixed));}
      const action=b.dataset.courseAction;
      const handled=b.dataset.selectCourse||action||b.dataset.extraTab||b.dataset.extraLevel!==undefined||b.dataset.extraAction||b.dataset.theoryAction||b.dataset.removePassword!==undefined;
      if(handled){event.preventDefault();event.stopImmediatePropagation();}
      if(b.dataset.selectCourse)return switchCourse(b.dataset.selectCourse);
      if(action==='home')return backHome();
      if(action==='simulator'||action==='reset-simulator'){if(extra&&extra!=='formulas')return extraAction(action);}
      if(action==='practice'){screen='practice';extra=null;return render();}
      if(action==='course-menu'){screen=selected==='hvac'?'menu':'practice';extra=null;return render();}
      if(action==='theory'){screen='theory';examMessage='';render();if(qaActive&&!theory.current)return theoryRequest('new');return;}
      if(action==='add-password'){adminDraft.passwords.push({label:'',expires_on:'',active:true,password:''});renderAdmin();resizeFrame();return;}
      if(b.dataset.removePassword!==undefined){adminDraft.passwords.splice(Number(b.dataset.removePassword),1);renderAdmin();resizeFrame();return;}
      if(b.dataset.extraTab){screen='practice';extra=b.dataset.extraTab;extraLevel=0;extraMessage='';return render();}
      if(b.dataset.extraLevel!==undefined){extraLevel=Number(b.dataset.extraLevel);extraMessage='';return render();}
      if(b.dataset.extraAction)return extraAction(b.dataset.extraAction);
      if(b.dataset.theoryAction){
        const a=b.dataset.theoryAction;
        if(a==='logout'){examToken='';examMessage='';return render();}
        if(a==='progress'){screen='theory-progress';return render();}
        if(a==='review'){screen='theory-review';render();window.scrollTo(0,0);return;}
        if(a==='result'||a==='return'){screen=theory.current?.result?'theory-result':'theory';return render();}
        return theoryRequest(a);
      }
      if(b.hasAttribute('data-show-progress')&&screen.startsWith('theory')){event.stopImmediatePropagation();screen='theory-progress';render();return;}
      if(b.id==='new-course-confirm'){extraState={};saveExtra();}
      if(b.hasAttribute('data-new-course')&&extra&&extra!=='formulas'){event.stopImmediatePropagation();extraAction('new');return;}
      if(b.id==='calc-use'&&extra&&extra!=='formulas'&&calculatorValue!==null){event.stopImmediatePropagation();const {q}=currentExtra();if(q.steps[q.cursor]){q.draft=DC.fmt(calculatorValue);saveExtra();$('calculator-dialog').close();render();}return;}
      if(b.hasAttribute('data-open-formulas'))setTimeout(appendFormulas,0);
    },true);
    document.addEventListener('keydown',event=>{
      const button=event.target.closest('.tabs [role=tab]');
      if(!button||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();event.stopImmediatePropagation();
      const buttons=[...document.querySelectorAll('.tabs [role=tab]')],i=buttons.indexOf(button);
      const next=buttons[event.key==='Home'?0:event.key==='End'?buttons.length-1:(i+(event.key==='ArrowLeft'?1:buttons.length-1))%buttons.length];
      next.click();document.getElementById(next.id)?.focus();
    },true);
    document.addEventListener('submit',event=>{
      if(event.target.id==='extra-answer-form'){event.preventDefault();event.stopImmediatePropagation();checkExtra();}
      if(event.target.id==='theory-login-form'){event.preventDefault();event.stopImmediatePropagation();theoryLogin();}
      if(event.target.id==='course-admin-form'){event.preventDefault();event.stopImmediatePropagation();saveAdmin();}
    },true);
    document.addEventListener('input',event=>{
      const node=event.target;
      if(node.dataset.adminName)adminDraft.names[node.dataset.adminName]=node.value;
      if(node.dataset.adminRow!==undefined)adminDraft.passwords[Number(node.dataset.adminRow)][node.dataset.field]=node.type==='checkbox'?node.checked:node.value;
      if(node.id==='extra-answer'&&extra){currentExtra().q.draft=node.value;saveExtra();}
      if(node.id==='course-sim-voltage'&&extra){const q=currentExtra().q;q.simVoltage=Number(node.value);saveExtra();updateCourseSimulator(q);}
      if(node.id==='course-sim-load'&&extra){const q=currentExtra().q;q.simLoadResistance=Number(node.value);saveExtra();updateCourseSimulator(q);}
    });
    document.addEventListener('change',event=>{
      const node=event.target;
      if(node.id==='qa-extra-exercise'&&qaActive&&extra&&extra!=='formulas'){const index=Number(node.value);if(Number.isInteger(index)&&index>=0&&index<10){currentExtra().state.index=index;extraMessage='';render();}return;}
      if(node.id==='qa-course-switch'&&qaActive){switchCourse(node.value);return;}
      if(node.dataset.theoryAnswer&&theory.current&&!theory.current.result){theory.current.answers??={};theory.current.answers[node.dataset.theoryAnswer]=node.value;finishConfirm=false;saveTheory();if($('theory-answered'))$('theory-answered').textContent=`נענו ${Object.keys(theory.current.answers).length} מתוך 20 שאלות`;}
    });
    window.addEventListener('message',event=>{
      if(event.source!==window.parent||event.data?.type!=='streamlit:render')return;
      ready=true;const args=event.data.args??{};applyConfig(args.course_config);
      const reply=args.course_response;
      if(reply&&reply.request_id===pending?.id){const p=pending;pending=null;clearTimeout(p.timer);p.resolve(reply);}
    });
    setInterval(()=>{if(screen.startsWith('theory')&&(qaActive||examToken)&&theory.current&&!examBusy&&!pending)theoryRequest('resume');},60000);
  }
  function onEnterQA(){theoryGeneration++;qaReturn={selected,screen,extra,extraLevel,extraState:JSON.parse(JSON.stringify(extraState)),courseProfile,courseKey,personalKey,recentKey,theory,examToken,examMessage,examError,finishConfirm};examBusy=false;examMessage='';examError=false;finishConfirm=false;theory={seen:[],previous:[],history:[],current:null};examToken='';}
  function onExitQA(){if(!qaReturn)return;theoryGeneration++;examBusy=false;if(adminToken&&!pending)request('admin_logout',{token:adminToken}).catch(()=>{});({selected,screen,extra,extraLevel,extraState,courseProfile,courseKey,personalKey,recentKey,theory,examToken,examMessage,examError,finishConfirm}=qaReturn);qaReturn=null;adminToken='';adminDraft=null;}
  function standalone(){return screen!=='practice';}
  function topicVisible(kind){return !['mixed','battery'].includes(kind)||kind==='mixed'&&selected==='security'||kind==='battery'&&selected!=='hvac';}
  return {standalone,topicVisible,initialize,renderOverride,showPractice,loginAdmin,renderAdmin,onEnterQA,onExitQA,syncProfile,appendFormulas};
})();

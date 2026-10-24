/* Optional learning tools. They never change the underlying exercise answers. */
const LearningTools=window.LearningTools=(()=>{
  const key='dc.basics.site-settings.v1',byId=id=>document.getElementById(id);
  let settings={expandedLearning:false},qaSettings=null,selection='',busy=false;
  try{settings.expandedLearning=JSON.parse(localStorage.getItem(key)||'null')?.expandedLearning===true;}catch{}
  const enabled=()=>settings.expandedLearning;
  const escape=value=>escapeHTML(value);
  function persist(){if(!qaActive)try{localStorage.setItem(key,JSON.stringify(settings));}catch{showStorageNotice();}}
  function explanation(value,expected,unit){
    if(!enabled())return '';
    const actual=Number(String(value).replace(',','.'));
    if(!Number.isFinite(actual))return 'הקלידו מספר בלבד. היחידה כבר מופיעה ליד השדה.';
    if(expected!==0&&[.000001,.001,1000,1000000].some(f=>Math.abs(actual-expected*f)<=Math.max(1e-9,Math.abs(expected*f)*.002)))return `נראה שהמספר הוזן בסדר גודל אחר. בדקו את היחידה ${unit}: מילי הוא אלפית, ומיקרו הוא מיליונית. המירו את כל הנתונים ליחידות התואמות לפני ההצבה.`;
    if(expected!==0&&actual!==0&&Math.abs(actual*expected-1)<.02)return 'ייתכן שסדר החילוק התהפך. בדקו מה מופיע במונה ומה במכנה בנוסחה.';
    return 'עברו בשלושה צעדים: מה מבקשים למצוא? אילו נתונים ויחידות נתונים? איזו נוסחה מקשרת ביניהם? הציבו לפני החישוב, ובדקו אם התוצאה מתאימה לטור או למקביל.';
  }
  function enterQA(){qaSettings={...settings};}
  function exitQA(){if(qaSettings)settings=qaSettings;qaSettings=null;syncSettings();}
  function syncSettings(){const n=byId('expanded-learning');if(n)n.checked=enabled();document.body.classList.toggle('expanded-learning',enabled());}
  function initialize(){
    const button=document.createElement('button');button.type='button';button.className='icon-button';button.dataset.openSiteSettings='';button.dataset.tooltip='הגדרות אתר';button.setAttribute('aria-label','הגדרות אתר');button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-controls','site-settings-dialog');
    button.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m10 3-1 3-3 1-2 3 2 2-1 3 3 2 3-1 2 3 3-1 1-3 3-1v-4l-3-1-1-3z"/><circle cx="12" cy="12" r="3"/></svg>';
    byId('quickbar').append(button);
    const dialog=document.createElement('dialog');dialog.id='site-settings-dialog';dialog.setAttribute('aria-labelledby','site-settings-title');
    dialog.innerHTML=`<div class="dialog-head"><h2 id="site-settings-title">הגדרות אתר</h2><button type="button" class="close" data-close-dialog="site-settings-dialog" aria-label="סגירת הגדרות אתר">×</button></div><label class="toggle expanded-learning-switch"><input id="expanded-learning" type="checkbox" role="switch">למידה מורחבת</label><p>משוב שמכוון לסוג הטעות, המלצה לתרגול ממוקד וניסויים מודרכים בסימולטור. כשהמתג כבוי נשמרת דרך התרגול הרגילה.</p><div class="completion-actions"><button type="button" class="btn secondary" data-open-accessibility>התאמות נגישות</button></div><h3>גיבוי ההתקדמות במכשיר</h3><p>הקובץ כולל את הפרופיל, ההתקדמות והתרגילים. הוא נשמר במכשיר שלכם. מבחן עיוני פעיל אינו משוחזר.</p><div class="completion-actions"><button type="button" class="btn" data-learning-export>הורדת גיבוי</button><label class="btn secondary" for="learning-import">בחירת קובץ לשחזור</label><input id="learning-import" type="file" accept=".json,application/json"></div><div id="learning-backup-status" role="status" aria-live="polite"></div><div id="learning-import-review" hidden><p id="learning-import-summary"></p><button class="btn" type="button" data-learning-import-confirm>אישור שחזור ההתקדמות</button><button class="btn secondary" type="button" data-learning-import-cancel>ביטול</button></div>`;
    document.body.append(dialog);
    dialog.addEventListener('close',()=>document.querySelector('[data-open-site-settings]')?.focus());
    const style=document.createElement('style');style.textContent=`
      .expanded-learning-switch{font-size:20px;font-weight:bold;padding:16px;background:var(--soft);border-radius:12px}#learning-import{max-width:100%;margin-top:12px}#learning-backup-status{margin-top:12px}.learning-recommendation{margin:14px 0}.learning-recommendation h3{margin:0 0 6px}.sim-learning-tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0}.sim-learning-tools label{display:inline-flex!important;gap:6px;align-items:center;min-height:44px}.sim-learning-tools input{width:auto!important}.sim-learning-tools .btn{min-height:44px}.sim-component{cursor:pointer}.sim-component.is-selected{filter:drop-shadow(0 0 4px #ffc65d)}.sim-component.is-selected text{font-weight:bold}.sim-row-selected{outline:2px solid #c38330;outline-offset:-2px}.sim-component-link{background:transparent;color:inherit;text-decoration:underline;text-underline-offset:4px;min-height:44px;padding:4px 8px;border:1px solid transparent;border-radius:6px}.sim-component-link:focus-visible{outline:3px solid #c38330}.sim-hide-current .sim-current,.sim-hide-current .sim-current-flow,.sim-hide-current .phone-current-flow,.sim-hide-current .mixed-current-flow,.sim-hide-current polygon[fill="#ff6565"]{display:none}.sim-hide-voltage .sim-voltage-drop,.sim-hide-power .sim-power{display:none}.sim-expanded{position:fixed!important;inset:0!important;z-index:10010!important;margin:0!important;padding:12px!important;overflow:auto!important;background:#000!important;color:#fff!important;max-height:100vh!important}.sim-expanded svg{min-width:800px;max-width:none!important}.sim-expanded:fullscreen{width:100vw;height:100vh}.sim-prediction{padding:12px;border:1px solid var(--line);border-radius:12px;margin:12px 0}.sim-prediction summary{cursor:pointer;min-height:44px;align-content:center}.qa-context-note{padding:10px;border:1px solid #739bc2;border-radius:10px;margin:10px 0}.qa-management-warning{padding:12px;border:2px solid #b75b2a;border-radius:10px}.qa-banner details>summary{min-height:44px;align-content:center;cursor:pointer}@media(max-width:600px){.sim-learning-tools{gap:6px}.sim-learning-tools label{font-size:14px}.sim-component-link{padding:4px}.learning-recommendation{padding:12px}}
    `;document.head.append(style);
    document.addEventListener('click',onClick,true);
    document.addEventListener('change',onChange);
    document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement)document.querySelectorAll('.sim-expanded').forEach(n=>{n.classList.remove('sim-expanded');n.querySelector('[data-sim-fullscreen]').textContent='מסך מלא / הרחבת הסכמה';});});
    document.addEventListener('keydown',event=>{if(event.key==='Escape')document.querySelectorAll('.sim-expanded').forEach(n=>{n.classList.remove('sim-expanded');const b=n.querySelector('[data-sim-fullscreen]');if(b)b.textContent='מסך מלא / הרחבת הסכמה';});const target=event.target.closest('[data-link-component]');if(target&&['Enter',' '].includes(event.key)&&target.tagName.toLowerCase()==='g'){event.preventDefault();selectComponent(target.dataset.linkComponent);}},true);
    syncSettings();
  }
  const allowedKey=k=>/^dc\.basics\.(?:(?:personal|course|recent)\.v\d+(?:\.(?:security|mobile))?|(?:entry|theory|formulaViews|site-settings|calculator\.settings)\.v\d+|extra\.(?:security|mobile)\.v\d+)$/.test(k);
  function backupData(){
    if(qaActive)throw Error('יש לצאת מ־QA לפני גיבוי או שחזור של ההתקדמות האישית.');
    const data={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(allowedKey(k)){let value=JSON.parse(localStorage.getItem(k));if(k==='dc.basics.theory.v1')value={...value,current:null};data[k]=JSON.stringify(value);}}
    return {format:'electricity-learning-backup',version:1,createdAt:new Date().toISOString(),data};
  }
  function validateBackup(raw){
    if(typeof raw!=='string'||raw.length>5*1024*1024)throw Error('קובץ הגיבוי גדול מדי.');
    const input=JSON.parse(raw);if(input?.format!=='electricity-learning-backup'||input.version!==1||!input.data||Array.isArray(input.data)||typeof input.data!=='object')throw Error('זה אינו קובץ גיבוי נתמך של האתר.');
    const data={};for(const [k,v]of Object.entries(input.data)){
      if(!allowedKey(k)||typeof v!=='string')throw Error('קובץ הגיבוי מכיל שדה שאינו נתמך.');
      const value=JSON.parse(v);
      if(k.includes('.extra.')){
        const course=k.includes('.security.')?'security':'mobile',clean={};
        for(const [topic,state]of Object.entries(value)){
          if(!/^(mixed|battery):[012]$/.test(topic)||!Number.isSafeInteger(state.seed)||!Array.isArray(state.questions))throw Error('תרגילים לא תקינים בגיבוי.');
          const [kind,level]=topic.split(':'),questions=CoursePractice.batch(course,kind,Number(level),state.seed);
          questions.forEach((q,i)=>{const old=state.questions[i]??{};q.cursor=Math.max(0,Math.min(q.steps.length,Number.isSafeInteger(old.cursor)?old.cursor:0));q.draft=typeof old.draft==='string'?old.draft.slice(0,24):'';q.accepted=old.accepted===true;for(const field of ['hint','solution','helped','simAnimate'])if(typeof old[field]==='boolean')q[field]=old[field];for(const field of ['attempts','simVoltage','simSourceVolts','simInternalOhms','simLoadOhms'])if(Number.isFinite(old[field])&&old[field]>=0)q[field]=old[field];if(['milli','base'].includes(old.simUnitMode))q.simUnitMode=old.simUnitMode;if(q.kind==='mixed'&&q.simVoltage>q.u*2)q.simVoltage=q.u;
          if(q.unitFamily==='Rs'){const g=Object.fromEntries(q.givens.map(([k,v])=>[k,v])),vs=q.voltageUnit==='mV'?.001:1,rl=g.U_L*vs/g.I;if(q.simInternalOhms>2)q.simInternalOhms=2;if(q.simSourceVolts>g.U_t*vs*2)q.simSourceVolts=g.U_t*vs;if(q.simLoadOhms!==undefined&&(q.simLoadOhms<rl/4||q.simLoadOhms>rl*4))q.simLoadOhms=rl;}
          q.manualWork=restoreManualWork(old.manualWork,q);q.helpedSteps=Object.fromEntries(Object.entries(old.helpedSteps??{}).filter(([step,v])=>/^\d+$/.test(step)&&Number(step)<q.steps.length&&v===true));});
          clean[topic]={seed:state.seed,index:Math.max(0,Math.min(9,Number.isSafeInteger(state.index)?state.index:0)),questions};
        }data[k]=JSON.stringify(clean);
      }else if(k==='dc.basics.theory.v1')data[k]=JSON.stringify({...value,current:null});
      else data[k]=v;
    }
    if(!Object.keys(data).length)throw Error('הגיבוי ריק.');
    return {data,createdAt:typeof input.createdAt==='string'?input.createdAt:''};
  }
  let pendingImport=null;
  function restoreBackup(backup){
    if(qaActive)throw Error('יש לצאת מ־QA לפני השחזור.');
    const previous={};for(const k of Object.keys(backup.data))previous[k]=localStorage.getItem(k);
    try{for(const [k,v]of Object.entries(backup.data))localStorage.setItem(k,v);}catch(error){for(const [k,v]of Object.entries(previous))try{if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v);}catch{}throw Error('השחזור לא הושלם. הנתונים הקודמים נשמרו ככל שניתן; בדקו מקום פנוי בדפדפן.');}
  }
  function selectComponent(id,scroll=true){
    selection=id;document.querySelectorAll('.sim-component').forEach(n=>{const active=n.dataset.component===id;n.classList.toggle('is-selected',active);n.setAttribute('aria-pressed',String(active));});
    document.querySelectorAll('[data-link-component]').forEach(n=>{const active=n.dataset.linkComponent===id;if(n.tagName.toLowerCase()==='button')n.setAttribute('aria-pressed',String(active));n.closest('tr')?.classList.toggle('sim-row-selected',active);});
    if(scroll)document.querySelector(`tr[data-link-component="${id}"]`)?.scrollIntoView({block:'nearest',behavior:personal.preferences.motion?'auto':'smooth'});
  }
  function simulatorRoot(){return document.querySelector('#course-simulator')??document.querySelector('#simulator-section');}
  function decorateSimulator(){
    const root=simulatorRoot();if(!root)return;
    if(!root.querySelector('.sim-learning-tools')){
      const tools=document.createElement('div');tools.className='sim-learning-tools';tools.setAttribute('role','group');tools.setAttribute('aria-label','תצוגת הסימולטור');
      tools.innerHTML='<label><input type="checkbox" data-sim-layer="current" checked>זרמים</label><label><input type="checkbox" data-sim-layer="voltage" checked>מתחים</label><label><input type="checkbox" data-sim-layer="power" checked>הספקים</label><button class="btn secondary tiny" type="button" data-sim-fullscreen>מסך מלא / הרחבת הסכמה</button>';
      root.querySelector('.sim-head')?.after(tools);
    }
    root.querySelectorAll('.sim-component').forEach(n=>{n.dataset.linkComponent=n.dataset.component;n.setAttribute('role','button');n.setAttribute('tabindex','0');n.setAttribute('aria-label',`הדגשת ${n.dataset.component} בטבלה ובסכמה`);});
    const ids=[...root.querySelectorAll('.sim-component')].map(n=>n.dataset.component);
    root.querySelectorAll('table tbody tr').forEach((row,i)=>{const id=ids[i];if(!id)return;row.dataset.linkComponent=id;const cell=row.querySelector('th,td');if(cell&&!cell.querySelector('button')){const button=document.createElement('button');button.type='button';button.className='sim-component-link';button.dataset.linkComponent=id;button.setAttribute('aria-label',`הדגשת ${id} בסכמה`);button.innerHTML=cell.innerHTML;cell.replaceChildren(button);}});
    root.querySelectorAll('svg text').forEach(n=>{if(/^P\d*\s*=/.test(n.textContent))n.classList.add('sim-power');});
    const powerToggle=root.querySelector('[data-sim-layer="power"]');if(powerToggle)powerToggle.closest('label').hidden=!root.querySelector('.sim-power');
    if(selection)selectComponent(selection,false);
    if(enabled()&&!root.querySelector('.sim-prediction')){
      const prediction=document.createElement('details');prediction.className='sim-prediction';prediction.innerHTML='<summary>ניסוי מודרך: מה יקרה לזרם אם נחצה את מתח המקור?</summary><p>כאשר ההתנגדויות קבועות, בחרו תחזית ואז נסו במעגל.</p><div class="completion-actions"><button class="btn secondary tiny" data-predict="decrease">יקטן לחצי</button><button class="btn secondary tiny" data-predict="same">יישאר ללא שינוי</button><button class="btn secondary tiny" data-predict="increase">יגדל</button><button class="btn tiny" data-apply-prediction hidden>ניסוי במעגל</button></div><p class="prediction-result" role="status" aria-live="polite"></p>';root.querySelector('.sim-learning-tools').after(prediction);
    }
    if(!enabled())root.querySelector('.sim-prediction')?.remove();
  }
  function recommendedTopic(){
    const choices=Object.entries(personal.topics).filter(([topic])=>topic!=='power'&&(!window.CourseApp||CourseApp.topicVisible(topic)));
    return choices.filter(([,c])=>c.attempted>=3&&(c.first/c.attempted<.85||c.attempts/c.attempted>1.3)).sort((a,b)=>a[1].first/a[1].attempted-b[1].first/b[1].attempted||b[1].attempts/b[1].attempted-a[1].attempts/a[1].attempted)[0]?.[0]??null;
  }
  function afterRender(){
    if(busy)return;busy=true;try{
      syncSettings();decorateSimulator();
      document.querySelectorAll('.learning-recommendation').forEach(n=>n.remove());
      const topic=enabled()&&!qaActive?recommendedTopic():null;
      const target=byId('course-panel')?.hidden?byId('workspace'):byId('course-panel');
      if(topic&&target&&!target.hidden&&!simulatorRoot()){
        const block=document.createElement('section');block.className='card learning-recommendation';block.innerHTML=`<h3>תרגול ממוקד להמשך</h3><p>לפי הדיוק בניסיון הראשון והניסיונות החוזרים, כדאי לחזק את ${escape(topicNames[topic])}. שימוש בעזרה הוא חלק מתהליך הלמידה.</p><button class="btn secondary tiny" data-focused-topic="${topic}">תרגול ${escape(topicNames[topic])}</button>`;target.prepend(block);
      }
      if(qaActive){
        const q=window.CourseApp?.formulaQuestion(),banner=document.querySelector('.qa-banner');
        if(q&&banner){banner.querySelectorAll('.qa-context-note').forEach(n=>n.remove());banner.querySelector('.qa-selectors').hidden=true;banner.querySelector('.qa-actions').hidden=true;const note=document.createElement('div');note.className='qa-context-note';note.innerHTML=`<p>בודקים: ${escape(q.title)}</p><div class="qa-selectors"><label for="qa-extra-level">רמה<select id="qa-extra-level">${Array.from({length:courseProfile==='mobile'?2:3},(_,i)=>`<option value="${i}" ${CourseApp.qaExtraLevel()===i?'selected':''}>${letters[i]}</option>`).join('')}</select></label><label for="qa-extra-step">סעיף<select id="qa-extra-step">${[...q.steps.map((step,i)=>[i,step.label]),[q.steps.length,'סיום התרגיל']].map(([i,label])=>`<option value="${i}" ${i===q.cursor?'selected':''}>${escape(label)}</option>`).join('')}</select></label></div><button class="btn secondary tiny" data-qa-extra-answer>${q.qaInspect?'הסתר תשובת QA':'הצג תשובת QA'}</button>${q.qaInspect&&q.steps[q.cursor]?`<p class="math" role="status">${escape(q.steps[q.cursor].formula)} = ${escape(String(q.steps[q.cursor].value))} ${escape(q.steps[q.cursor].unit)}</p>`:''}`;banner.querySelector('.qa-banner-head').after(note);const picker=document.querySelector('#course-panel .qa-extra-picker');if(picker)note.querySelector('.qa-selectors').append(picker);const sim=banner.querySelector('.qa-actions [data-go-simulator]');if(sim)note.append(sim);}
      }
    }finally{busy=false;}
  }
  // Preserve SVG paths, animations, focus and table nodes during slider updates.
  function patchDisplay(container,html){
    if(!container)return;const template=document.createElement('template');template.innerHTML=html;
    function sync(old,fresh){
      if(old.nodeType!==fresh.nodeType||old.nodeName!==fresh.nodeName){old.replaceWith(fresh.cloneNode(true));return;}
      if(old.nodeType===3){if(old.nodeValue!==fresh.nodeValue)old.nodeValue=fresh.nodeValue;return;}
      if(old.nodeType!==1)return;
      if(/^(TD|TH)$/.test(old.nodeName)&&old.querySelector(':scope > button[data-link-component]')&&!fresh.querySelector('button')){const button=old.firstElementChild;if(button.innerHTML!==fresh.innerHTML)button.innerHTML=fresh.innerHTML;return;}
      const keepClass=old.classList.contains('is-selected');
      for(const a of [...old.attributes])if(!fresh.hasAttribute(a.name)&&!['data-link-component','tabindex','aria-pressed'].includes(a.name)&&!(a.name==='role'&&old.matches('.sim-component')))old.removeAttribute(a.name);
      for(const a of [...fresh.attributes])if(old.getAttribute(a.name)!==a.value)old.setAttribute(a.name,a.value);
      if(keepClass)old.classList.add('is-selected');
      const count=Math.max(old.childNodes.length,fresh.childNodes.length);
      for(let i=0;i<count;i++){const a=old.childNodes[i],b=fresh.childNodes[i];if(!b){while(old.childNodes.length>i)old.lastChild.remove();break;}if(!a)old.appendChild(b.cloneNode(true));else sync(a,b);}
    }
    const holder=container.cloneNode(false);holder.append(template.content);sync(container,holder);afterRender();
  }
  function onClick(event){
    const button=event.target.closest('button,[data-link-component]');if(!button)return;
    if(button.hasAttribute('data-open-site-settings')){event.preventDefault();event.stopImmediatePropagation();byId('site-settings-dialog').showModal();syncSettings();return;}
    if(button.dataset.linkComponent){event.preventDefault();event.stopImmediatePropagation();selectComponent(button.dataset.linkComponent);return;}
    if(button.hasAttribute('data-qa-extra-answer')){event.stopImmediatePropagation();CourseApp.qaExtraNavigate('answer');return;}
    if(button.dataset.focusedTopic){event.stopImmediatePropagation();CourseApp.focusPractice(button.dataset.focusedTopic);return;}
    if(button.hasAttribute('data-sim-fullscreen')){event.preventDefault();event.stopImmediatePropagation();const root=simulatorRoot();if(!root)return;if(root.classList.contains('sim-expanded')){root.classList.remove('sim-expanded');if(document.fullscreenElement)document.exitFullscreen?.();button.textContent='מסך מלא / הרחבת הסכמה';}else{root.classList.add('sim-expanded');button.textContent='יציאה ממסך מלא';root.requestFullscreen?.().catch(()=>{});}return;}
    if(button.dataset.predict){event.stopImmediatePropagation();const root=simulatorRoot(),slider=root.querySelector('#sim-voltage,#course-sim-voltage,#course-sim-source'),correct=Number(slider?.value)===0?'same':'decrease';root.querySelector('.prediction-result').textContent=button.dataset.predict===correct?'נכון: בהתנגדות קבועה הזרם יחסי למתח.':'נסו את חוק אוהם: I = U ÷ R. ההתנגדות אינה משתנה.';root.querySelector('[data-apply-prediction]').hidden=false;return;}
    if(button.hasAttribute('data-apply-prediction')){event.stopImmediatePropagation();const slider=simulatorRoot().querySelector('#sim-voltage,#course-sim-voltage,#course-sim-source');if(slider){slider.value=String(Number(slider.value)/2);slider.dispatchEvent(new Event('input',{bubbles:true}));}return;}
    if(button.hasAttribute('data-learning-export')){event.stopImmediatePropagation();try{const data=backupData(),blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='electricity-learning-backup.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);byId('learning-backup-status').textContent='קובץ הגיבוי הוכן להורדה.';}catch(error){byId('learning-backup-status').textContent=error.message;}return;}
    if(button.hasAttribute('data-learning-import-cancel')){pendingImport=null;byId('learning-import-review').hidden=true;return;}
    if(button.hasAttribute('data-learning-import-confirm')){try{if(!pendingImport)return;restoreBackup(pendingImport);pendingImport=null;byId('learning-backup-status').textContent='השחזור הושלם. טענו מחדש את האתר כדי להמשיך מהנתונים ששוחזרו.';byId('learning-import-review').hidden=true;window.location.reload();}catch(error){byId('learning-backup-status').textContent=error.message;}}
  }
  async function onChange(event){
    const node=event.target;
    if(node.id==='qa-extra-level')CourseApp.qaExtraNavigate('level',Number(node.value));
    if(node.id==='qa-extra-step')CourseApp.qaExtraNavigate('step',Number(node.value));
    if(node.id==='expanded-learning'){settings.expandedLearning=node.checked;persist();render();}
    if(node.dataset.simLayer){const root=simulatorRoot();root?.classList.toggle('sim-hide-'+node.dataset.simLayer,!node.checked);}
    if(node.id==='learning-import')try{if(qaActive)throw Error('יש לצאת מ־QA לפני השחזור.');const file=node.files?.[0];if(!file)return;if(file.size>5*1024*1024)throw Error('קובץ הגיבוי גדול מדי.');pendingImport=validateBackup(await file.text());byId('learning-import-summary').textContent=`הקובץ מכיל ${Object.keys(pendingImport.data).length} קבוצות נתונים. השחזור יחליף את הנתונים המתאימים במכשיר. להמשיך?`;byId('learning-import-review').hidden=false;byId('learning-backup-status').textContent='הקובץ נבדק. ממתינים לאישור השחזור.';}catch(error){pendingImport=null;byId('learning-backup-status').textContent=error.message;}
  }
  return {initialize,afterRender,enabled,explanation,enterQA,exitQA,patchDisplay,backupData,validateBackup,restoreBackup,recommendedTopic};
})();

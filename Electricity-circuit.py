"""יסודות החשמל — תרגול DC למבוגרים המתחילים ללמוד חשמל.

Streamlit app with embedded browser assets and server-side course administration.
Local browser profiles and learning statistics persist between exercise rounds.
Review the draft terms/privacy wording and accessibility statement before publication.
Install: python -m pip install streamlit
Run:     streamlit run Electricity-circuit.py

Includes Ohm/power, series and parallel practice, interactive formula triangles,
four-operation calculator and a DC circuit simulator with resistive lamp models.
Practice resumes at the saved exercise; reset creates fresh exercises for the selected course.
Parallel levels contain exactly 3 equal-resistance and 7 pairwise-distinct exercises.
Level C uses coherent kΩ/mA/mW or MΩ/μA/μW units; physics and simulation remain in SI.
Level B has whole resistances/source voltage and decimal currents; parallel Req is decimal.
Password-gated QA runs on an in-memory copy and never saves practice progress.
Recent question signatures are
kept in browser storage to avoid immediate repeats; public reviews and private notes use separate GitHub repositories with server-side tokens.
Public reviews require 1–5 stars, optional text, and update a GitHub summary issue.
Level A Ohm/power contains one-amp exercises in 20% of slots; other displayed currents range from 2 to 12.
Profile details and progress remain in local browser storage. Theory answers are sent to the server for grading.
"""
from pathlib import Path
import tempfile
import hashlib
import json
import re
import time
import threading
import types
import urllib.error
import urllib.request
import streamlit as st
import streamlit.components.v1 as components

APP_HTML = r'''<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>יסודות החשמל | תרגול DC</title>
  <script>
    // Use the same scale before the first paint and after an accessibility change.
    function applyTextScale(value) {
      const scale = [100,125,150].includes(value) ? value : 100;
      const root = document.documentElement;
      root.style.setProperty('--text-scale', String(scale / 100));
      for (const size of [125,150]) root.classList.toggle('text-scale-' + size, scale === size);
    }
    const systemThemeQuery = '(prefers-color-scheme: dark)';
    function findSystemThemeContext() {
      let source=window;
      // An iframe can report its host's forced color scheme instead of the device preference.
      // Read from the highest accessible browsing context without changing the host's theme.
      for(let depth=0;depth<16;depth++){
        try{
          if(source.parent===source)break;
          const candidate=source.parent;
          candidate.matchMedia(systemThemeQuery);
          source=candidate;
        }catch{break;}
      }
      return source;
    }
    const systemThemeContext = findSystemThemeContext();
    const systemColorScheme = systemThemeContext.matchMedia(systemThemeQuery);
    function systemPrefersDark() {
      // A fresh query also handles mobile browsers resuming a page after suspension.
      try{return systemThemeContext.matchMedia(systemThemeQuery).matches;}
      catch{return window.matchMedia(systemThemeQuery).matches;}
    }
    function applyTheme(value) {
      const theme = ['system','dark','light'].includes(value) ? value : 'system';
      const dark=theme==='dark'||theme==='system'&&systemPrefersDark();
      document.documentElement.classList.toggle('dark-mode',dark);
      try {
        if(window.parent!==window&&window.parent.document.querySelector('.stApp,[data-testid="stAppViewContainer"]')) {
          const host=window.parent.document;
          let style=host.getElementById('dc-basics-host-surface');
          if(!style){style=host.createElement('style');style.id='dc-basics-host-surface';host.head.append(style);}
          style.textContent='.stApp,[data-testid="stAppViewContainer"],html,body{background:'+(dark?'#000000':'#fff8e8')+'!important}';
        }
      }catch{}

    }
    try {
      const saved = JSON.parse(localStorage.getItem('dc.basics.personal.v1') || 'null');
      const sharedEntry=JSON.parse(localStorage.getItem('dc.basics.entry.v1')||'null');
      const prefs=sharedEntry?.preferences??(saved?.version===1?saved.preferences:null);
      applyTextScale(prefs?.textScale??100);
      applyTheme(prefs?.theme??'system');
    } catch { applyTextScale(100); applyTheme('system'); }
  </script>
  <script>
    // Jerusalem Shabbat schedule from Hebcal; keep cached times available offline.
    (function(){
      const KEY='dc.basics.shabbat.jerusalem.v1',now=()=>Date.now();
      let schedule=[],mode='auto',previewProgress=0,locked=false,access={isQA:()=>false,canUseApp:()=>true,onUnlock:()=>{}};
      function makeSchedule(items){return items.filter(x=>x&&x.category==='candles'&&x.date).map(c=>{const h=items.find(x=>x&&x.category==='havdalah'&&x.date>c.date);return h?{start:Date.parse(c.date),end:Date.parse(h.date)}:null;}).filter(x=>x&&Number.isFinite(x.start)&&Number.isFinite(x.end));}
      function candlesHTML(){
        return '<svg viewBox="0 0 140 150" role="img" aria-hidden="true">'+[51,88].map(x=>`<rect class="candle-wax" x="${x-12}" y="58" width="25" height="70" fill="#fff7e7" stroke="#c99c56" stroke-width="2"/><g class="candle-burning-top"><path d="M${x} 59V47" stroke="#5a3c27" stroke-width="2"/><g class="shabbat-flame"><path d="M${x} 49c-12-14 7-19 0-34 18 17 13 27 0 34Z" fill="#ffbf45"/><path d="M${x} 46c-6-8 4-11 1-18 9 9 6 14-1 18Z" fill="#fff2a6"/></g></g><ellipse cx="${x}" cy="130" rx="22" ry="5" fill="#d8bd8e"/>`).join('')+'</svg>';
      }
      function show(end,test,qa,progress){
        let screen=document.getElementById('shabbat-screen');
        const created=!screen;
        if(!screen){
          screen=document.createElement('section');screen.id='shabbat-screen';screen.tabIndex=-1;screen.setAttribute('role','dialog');screen.setAttribute('aria-modal','true');screen.setAttribute('aria-labelledby','shabbat-title');
          screen.innerHTML=`<div class="shabbat-card"><div class="shabbat-candles" aria-label="שני נרות שבת">${candlesHTML()}</div><h1 id="shabbat-title">שבת שלום</h1><p>האתר סגור לשימוש במהלך השבת.</p><p class="shabbat-return">נשוב לפעול בצאת השבת</p><p class="shabbat-time">צאת השבת בירושלים: <bdi id="shabbat-until"></bdi></p></div>`;
          document.body.appendChild(screen);
        }
        const wax=100-95*Math.min(1,Math.max(0,progress)),height=70*wax/100;
        screen.dataset.waxPercent=String(Math.round(wax*100)/100);
        screen.querySelectorAll('.candle-wax').forEach(node=>{node.setAttribute('y',String(128-height));node.setAttribute('height',String(height));});
        screen.querySelectorAll('.candle-burning-top').forEach(node=>node.setAttribute('transform',`translate(0 ${70-height})`));
        if(!screen.querySelector('.shabbat-branding')){
          const branding=document.createElement('footer');branding.className='shabbat-branding';
          const logo=document.querySelector('.footer-logo');
          if(logo){
            const zoom=document.createElement('button');zoom.type='button';zoom.className='logo-zoom';zoom.dataset.openLogo='';zoom.setAttribute('aria-label','הגדלת לוגו OBE-26');zoom.setAttribute('aria-haspopup','dialog');zoom.setAttribute('aria-controls','logo-dialog');
            const image=logo.cloneNode(false);image.className='shabbat-logo';zoom.appendChild(image);branding.appendChild(zoom);
          }
          const rights=document.createElement('p');rights.textContent='© OBE-26 · כל הזכויות שמורות';branding.appendChild(rights);screen.querySelector('.shabbat-card').appendChild(branding);
        }
        const time=document.getElementById('shabbat-until');
        time.parentElement.hidden=!Number.isFinite(end);
        if(Number.isFinite(end))time.textContent=new Intl.DateTimeFormat('he-IL',{timeZone:'Asia/Jerusalem',hour:'2-digit',minute:'2-digit'}).format(new Date(end));
        let controls=screen.querySelector('.shabbat-qa-controls');
        if(!controls){controls=document.createElement('div');controls.className='shabbat-qa-controls';screen.querySelector('.shabbat-branding').before(controls);}
        const controlsKey=qa+':'+test;
        if(controls.dataset.mode!==controlsKey){
          controls.dataset.mode=controlsKey;
          controls.innerHTML=qa?`${test?'<p class="shabbat-test-label" role="status">מצב טסט — תצוגת שבת לבדיקה</p><label class="shabbat-preview-time" for="qa-shabbat-progress">התקדמות השבת בבדיקה: <output id="qa-shabbat-progress-value">0%</output><input id="qa-shabbat-progress" type="range" min="0" max="100" step="1" value="0"></label>':''}<button type="button" class="btn" data-shabbat-mode="bypass">${test?'סיום הבדיקה וחזרה ל־QA':'עקיפת שבת וחזרה ל־QA'}</button><button type="button" class="btn secondary" data-exit-qa>חזרה למצב רגיל</button>`:'<button type="button" class="btn secondary tiny" data-open-qa>כניסת מנהל / QA</button>';
        }
        if(test){screen.querySelector('#qa-shabbat-progress').value=String(previewProgress*100);screen.querySelector('#qa-shabbat-progress-value').textContent=Math.round(previewProgress*100)+'%';}
        screen.hidden=false;document.getElementById('app')?.setAttribute('inert','');
        document.querySelectorAll('dialog[open]').forEach(dialog=>{if(!['qa-login-dialog','logo-dialog'].includes(dialog.id))dialog.close();});
        if(created&&!document.getElementById('qa-login-dialog')?.open)screen.focus({preventScroll:true});
      }
      function apply(){
        const qa=access.isQA();if(!qa)mode='auto';
        const active=schedule.find(x=>x.start<=now()&&now()<x.end),test=qa&&mode==='test';
        if(test||(active&&!(qa&&mode==='bypass'))){
          const interval=active??schedule.find(x=>x.end>now());
          locked=true;show(interval?.end,test,qa,test?previewProgress:(now()-interval.start)/(interval.end-interval.start));
        }else if(locked){
          locked=false;document.getElementById('shabbat-screen')?.remove();
          document.getElementById('app')?.toggleAttribute('inert',!access.canUseApp());access.onUnlock();
        }
      }
      async function refresh(){
        try{const cached=JSON.parse(localStorage.getItem(KEY)||'null')?.schedule;if(Array.isArray(cached))schedule=cached.filter(x=>Number.isFinite(x?.start)&&Number.isFinite(x?.end)&&x.start<x.end);}catch{}
        apply();
        try{const url='https://www.hebcal.com/shabbat?cfg=json&geonameid=281184&b=40&M=on&leyning=off',response=await fetch(url,{cache:'no-store'});if(!response.ok)throw Error('schedule unavailable');const data=await response.json();schedule=makeSchedule(data.items||[]);localStorage.setItem(KEY,JSON.stringify({saved:now(),schedule}));}catch{}
        apply();
      }
      window.ShabbatMode=Object.freeze({
        configure(callbacks){access=callbacks;},
        getMode:()=>mode,
        isLocked:()=>locked,
        resetQA(){mode=access.isQA()?'bypass':'auto';previewProgress=0;apply();},
        setMode(value){if(!access.isQA()||!['auto','test','bypass'].includes(value))return false;if(value!==mode)previewProgress=0;mode=value;apply();return true;},
        setPreviewProgress(value){if(!access.isQA()||mode!=='test'||!Number.isFinite(value)||value<0||value>100)return false;previewProgress=value/100;apply();return true;}
      });
      document.addEventListener('DOMContentLoaded',()=>{refresh();setInterval(refresh,60000);setInterval(apply,1000);});
    })();
  </script>
  <style>
    #shabbat-screen{position:fixed;inset:0;z-index:2147483000;display:flex;overflow-y:auto;padding:clamp(12px,3vw,24px);background:radial-gradient(ellipse at center,#fff5d8 0%,#e9c98d 100%);color:#422f1b;text-align:center}
    #shabbat-screen[hidden]{display:none!important}.shabbat-card{width:min(100%,520px);padding:30px 24px;border:1px solid #d6b576;border-radius:24px;background:#fffaf0;box-shadow:0 22px 80px #50340d30}.shabbat-candles svg{display:block;width:132px;height:142px;margin:0 auto 12px}.shabbat-card h1{font-size:clamp(36px,8vw,54px);margin:0 0 12px;color:#80521c}.shabbat-card p{font-size:20px;margin:8px 0}.shabbat-card .shabbat-return{font-weight:700;color:#4a6654}.shabbat-card .shabbat-time{font-size:16px;color:#74604a}
    .shabbat-card{margin:auto;flex-shrink:0}.shabbat-qa-controls{display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:10px;margin:18px 0}.shabbat-card .shabbat-test-label{width:100%;font-size:16px;font-weight:700;color:#80521c}.shabbat-branding{margin-top:22px;padding-top:18px;border-top:1px solid #d6b576}.shabbat-logo{display:block;width:170px;max-width:100%;height:auto;margin:0 auto 10px;padding:8px;background:#fff8e8;border-radius:8px}.shabbat-card .shabbat-branding p{font-size:14px;color:#74604a}.qa-shabbat{margin-top:16px;padding-top:12px;border-top:1px solid var(--line)}.qa-shabbat h3{margin-bottom:8px}.qa-shabbat-controls{display:flex;flex-wrap:wrap;gap:8px}.qa-shabbat-controls [aria-pressed=true]{outline:2px solid var(--green);outline-offset:2px}
    .dark-mode #shabbat-screen{background:radial-gradient(ellipse at center,#17202b 0%,#07090d 100%);color:#f0eadf}.dark-mode .shabbat-card{background:#161b23;border-color:#8e7956;box-shadow:0 22px 80px #0008}.dark-mode .shabbat-card h1,.dark-mode .shabbat-card .shabbat-test-label{color:#f8d58b}.dark-mode .shabbat-card .shabbat-return{color:#b9e0c7}.dark-mode .shabbat-card .shabbat-time,.dark-mode .shabbat-card .shabbat-branding p{color:#c2bcaf}.dark-mode .shabbat-branding{border-color:#8e7956}
    #shabbat-screen .btn{background:#116e65;color:#fff}#shabbat-screen .btn.secondary{background:#fffaf0;color:#422f1b;border-color:#a3844d}.dark-mode #shabbat-screen .btn{background:#4b381d;color:#f2e6d0}.dark-mode #shabbat-screen .btn.secondary{background:#212a36;color:#f0eadf;border-color:#8e7956}
    .shabbat-preview-time{display:block;width:100%;font-size:14px}.shabbat-preview-time input{display:block;width:100%;min-height:36px;accent-color:#116e65}.dark-mode .shabbat-preview-time input{accent-color:#f8d58b}.shabbat-flame{transform-box:fill-box;transform-origin:center bottom;animation:shabbat-flame-sway 2.4s ease-in-out infinite alternate}.candle-burning-top:nth-of-type(2) .shabbat-flame{animation-delay:-1.2s}@keyframes shabbat-flame-sway{0%{transform:rotate(-4deg) scale(.96,1.02)}50%{transform:rotate(2deg) scale(1.02,.97)}100%{transform:rotate(4deg) scale(.98,1.04)}}.reduce-motion .shabbat-flame{animation:none}@media(prefers-reduced-motion:reduce){.shabbat-flame{animation:none!important}}
    :root{--text-scale:1;color-scheme:light;--paper:#fff8e8;--card:#fffbf2;--ink:#3b3027;--muted:#74604a;--line:#e8cfa2;--green:#116e65;--soft:#ffebc4;--accent:#ffc45c;--amber:#a65b20;--shadow:0 8px 28px #7045110a}
    html:not(.ui-ready) body{visibility:hidden}
    .footer.footer{display:block}
    .footer-row,.footer-links{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
    .footer-row{justify-content:space-between}
    .footer-divider{width:100%;border:0;border-top:1px solid var(--line);margin:20px 0 16px}
    .site-credits{display:flex;align-items:center;justify-content:center;gap:10px 16px;flex-wrap:wrap;text-align:center}
    .footer-logo{display:block;width:120px;max-width:100%;height:auto;border-radius:4px}
    .logo-zoom{display:inline-flex;flex-shrink:0;padding:0;background:transparent;border-radius:4px;cursor:zoom-in;line-height:0}
    .logo-dialog{max-width:1040px}
    .logo-large{display:block;width:100%;height:auto;max-height:65vh;object-fit:contain;border-radius:8px}
    .credit-line{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px}
    /* Prevent mobile font inflation in the embedded frame; accessibility uses --text-scale. */
    html,body{-webkit-text-size-adjust:none;text-size-adjust:none}
    html{font-size:16px}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,"Noto Sans Hebrew",sans-serif;line-height:1.65;text-align:right}button,input,select{font:inherit}button{cursor:pointer;touch-action:manipulation}button:disabled{opacity:.48;cursor:default}button,input{font-size:calc(16px * var(--text-scale,1))}input[aria-invalid=true]{border-color:#b05242!important}button{border:0}button:focus-visible,input:focus-visible,summary:focus-visible,a:focus-visible{outline:3px solid #c38330;outline-offset:3px}[hidden]{display:none!important}h1,h2,h3,p{margin-top:0}h1,h2,h3{line-height:1.35}h1{font-size:clamp(calc(30px * var(--text-scale,1)),calc(5vw * var(--text-scale,1)),calc(46px * var(--text-scale,1)));letter-spacing:-.04em;margin-bottom:12px}h2{font-size:calc(25px * var(--text-scale,1));margin-bottom:8px}h3{font-size:calc(20px * var(--text-scale,1));margin-bottom:12px}p{margin-bottom:12px}bdi,.math{direction:ltr;unicode-bidi:isolate;font-variant-numeric:tabular-nums}bdi{display:inline-block}.math{display:block;text-align:left}input.numeric{direction:ltr;text-align:left;font-variant-numeric:tabular-nums}
    button,input,select,textarea{font-family:Arial,"Noto Sans Hebrew",sans-serif;font-size:calc(16px * var(--text-scale,1))}
    .app{max-width:1160px;margin:auto;padding:22px 24px 40px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:22px;border-bottom:1px solid var(--line)}.identity{display:flex;align-items:center;gap:12px}.brand-icon{background:var(--ink);color:white;border-radius:14px;width:46px;height:46px;display:grid;place-items:center;font-size:calc(27px * var(--text-scale,1))}.brand-title{font-weight:700;font-size:calc(18px * var(--text-scale,1))}.eyebrow{color:var(--green);font-weight:700;font-size:calc(12px * var(--text-scale,1));letter-spacing:.06em}.muted{color:var(--muted)}.small{font-size:calc(13px * var(--text-scale,1))}
    .btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:46px;padding:10px 17px;border-radius:11px;color:white;background:var(--green);font-weight:700;border:1px solid transparent;line-height:1.45}.btn.secondary{background:var(--card);color:var(--ink);border-color:var(--line)}.btn.soft{background:var(--soft);color:var(--green)}.btn.tiny{font-size:calc(14px * var(--text-scale,1));min-height:40px;padding:8px 11px}.btn:hover:enabled{filter:brightness(.97)}.text-btn{background:none;color:var(--green);text-decoration:underline;padding:8px;min-height:40px}.hero{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:32px 0 24px}.hero-copy{max-width:710px}.hero-copy p{color:var(--muted);font-size:calc(17px * var(--text-scale,1))}.hero-symbol{width:150px;height:150px;border-radius:28px;border:1px solid #cdded7;background:linear-gradient(140deg,#e9f0e8,#f9f5e8);display:grid;place-content:center;direction:ltr;text-align:center;color:var(--green);font-size:calc(31px * var(--text-scale,1));font-weight:700;flex-shrink:0;transform:rotate(-3deg)}.hero-symbol small{font-size:calc(13px * var(--text-scale,1));color:var(--muted);font-weight:400;margin-top:8px}.pills{display:flex;flex-wrap:wrap;gap:7px}.pill{border:1px solid var(--line);background:var(--card);padding:4px 10px;border-radius:20px;font-size:calc(12px * var(--text-scale,1));color:var(--muted)}
    .tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:8px 0 22px}.tab{min-height:64px;padding:12px 16px;background:#e8ede7;border-radius:13px;color:var(--muted);font-weight:700;text-align:right}.tab span{font-size:calc(12px * var(--text-scale,1));font-weight:400;display:block;margin-top:2px}.tab[aria-selected=true]{background:var(--ink);color:white}.course-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.levels{display:flex;gap:7px;flex-wrap:wrap}.level{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 13px;min-height:46px;color:var(--muted);font-weight:700}.level[aria-pressed=true]{color:var(--green);border-color:var(--green);box-shadow:inset 0 0 0 1px var(--green)}.level small{display:block;font-weight:400;font-size:calc(12px * var(--text-scale,1))}.card{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:var(--shadow)}.progress-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;font-size:calc(14px * var(--text-scale,1))}.question-dots{display:flex;gap:6px;direction:ltr}.question-dot{height:9px;width:23px;border-radius:5px;background:var(--line)}.question-dot.current{background:#80b5a6}.question-dot.done{background:var(--green)}.progress-track{height:5px;background:var(--line);border-radius:5px;overflow:hidden;margin-bottom:22px}.progress-track>div{height:100%;background:var(--green);transition:width .25s;}
    .exercise-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:18px;align-items:start}.exercise-title{margin-bottom:16px}.givens{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.given{background:#f1f4ed;border:1px solid #e0e7dc;border-radius:10px;padding:8px 12px;min-width:92px}.given small{display:block;color:var(--muted);font-size:calc(12px * var(--text-scale,1))}.given bdi{font-weight:700;font-size:calc(19px * var(--text-scale,1))}.diagram{margin:8px 0 0;overflow-x:auto;max-width:100%}.diagram svg{display:block;width:100%;height:auto;min-width:0}.diagram figcaption{color:var(--muted);font-size:calc(12px * var(--text-scale,1));margin-top:5px}.flow{stroke-dasharray:7 20;animation:currentFlow 2.4s linear infinite}@keyframes currentFlow{to{stroke-dashoffset:-216}}
    .step-list{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}.step-pill{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;border-radius:50%;font-size:calc(12px * var(--text-scale,1));border:1px solid var(--line);color:var(--muted)}.step-pill.done{background:var(--soft);color:var(--green);border-color:#b4d2c7}.step-pill.active{background:var(--ink);color:white;border-color:var(--ink)}.task-kicker{color:var(--green);font-weight:700;font-size:calc(13px * var(--text-scale,1));margin-bottom:5px}.answer-row{display:flex;gap:9px;margin:14px 0 6px;align-items:center}.answer-wrap{display:flex;align-items:center;gap:10px;flex:1;min-width:0}.answer-wrap input{min-width:0;width:100%;min-height:52px;border:2px solid #b9cec3;border-radius:11px;padding:10px 12px;background:white;font-size:calc(23px * var(--text-scale,1));color:var(--ink)}.unit{font-size:calc(19px * var(--text-scale,1));color:var(--muted)}.answer-tools{display:flex;flex-wrap:wrap;gap:7px;margin:16px 0}.rounding{font-size:calc(13px * var(--text-scale,1));color:var(--muted)}.feedback{border-radius:10px;padding:11px 13px;margin-top:12px;line-height:1.7}.feedback:empty{display:none}.feedback.error{background:#fff0ed;color:#933b32}.feedback.success{background:#e2f1e9;color:#126044}.hint{background:#f7f1df;border:1px solid #eadcbc;border-radius:12px;padding:14px;margin:12px 0;font-size:calc(14px * var(--text-scale,1))}.hint strong{display:block;margin-bottom:5px}.solution{border-inline-start:3px solid var(--green);padding:11px 15px;background:#f1f6ef;border-radius:8px;margin:12px 0}.solution .math{font-size:calc(21px * var(--text-scale,1));font-weight:700;overflow-wrap:anywhere;margin:6px 0}.solution p{font-size:calc(14px * var(--text-scale,1));color:var(--muted);margin-bottom:0}.completed-steps{margin-top:18px;border-top:1px solid var(--line);padding-top:12px}.completed-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:7px 0;font-size:calc(14px * var(--text-scale,1))}.completed-row bdi{font-weight:700}.complete-badge{color:var(--green);background:var(--soft);font-size:calc(13px * var(--text-scale,1));border-radius:20px;padding:6px 12px;display:inline-block;margin-bottom:14px}.completion-actions{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0 0}.success-summary{border-color:#b9d9c9}.level-note{border:1px dashed #b9cfc2;border-radius:12px;padding:12px;margin-top:14px;font-size:calc(14px * var(--text-scale,1));color:var(--muted)}
    .simulator{margin-top:20px}.sim-head{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}.sim-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(240px,.55fr);gap:20px;align-items:start}.sim-controls{padding:18px;background:#f1f4ed;border-radius:13px}.sim-controls label{display:block;font-weight:700;font-size:calc(14px * var(--text-scale,1))}.sim-controls input[type=range]{width:100%;accent-color:var(--green);margin:12px 0;min-height:36px}.sim-value{font-size:calc(24px * var(--text-scale,1));color:var(--green);font-weight:700}.toggle{display:flex!important;align-items:center;gap:9px;margin:16px 0}.toggle input{width:20px;height:20px;accent-color:var(--green)}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}.metric{padding:10px;border:1px solid var(--line);border-radius:10px}.metric small{display:block;color:var(--muted);font-size:calc(12px * var(--text-scale,1))}.metric bdi{font-weight:700;font-size:calc(17px * var(--text-scale,1))}.table-scroll{overflow:auto;margin-top:15px}table{border-collapse:collapse;width:100%;font-size:calc(14px * var(--text-scale,1))}th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:right;white-space:nowrap}th{background:#f2f4ed;color:var(--muted);font-weight:700}td bdi{font-weight:700}.footer{margin-top:25px;padding-top:18px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:calc(12px * var(--text-scale,1));color:var(--muted)}
    dialog{color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:20px;padding:22px;width:min(1040px,calc(100% - 24px));max-height:85vh;overflow:auto;text-align:right;box-shadow:0 20px 80px #182e3c40}dialog::backdrop{background:#102c3980;backdrop-filter:blur(3px)}.dialog-head{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;margin-bottom:14px}.dialog-head h2{margin:0}.close{border-radius:50%;min-width:40px;min-height:40px;background:#e4ebe3;color:var(--ink);font-size:calc(24px * var(--text-scale,1))}.formula-intro{font-size:calc(14px * var(--text-scale,1));color:var(--muted)}.formula-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.formula-card{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:17px;min-width:0}.formula-card h3{font-size:calc(18px * var(--text-scale,1));text-align:center}.formula-card .formula-lines{direction:ltr;text-align:center;font-size:calc(17px * var(--text-scale,1));line-height:1.8;margin-top:10px}.triangle{position:relative;width:260px;height:225px;margin:0 auto;direction:ltr;max-width:100%}.triangle svg{width:100%;height:100%;position:absolute;inset:0}.triangle-slot{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;width:82px;gap:3px;line-height:1.2}.triangle-slot.top{top:41px;left:calc(50% - 41px)}.triangle-slot.left{top:144px;left:calc(28% - 41px)}.triangle-slot.right{top:144px;left:calc(72% - 41px)}.triangle-slot strong{font-size:calc(21px * var(--text-scale,1))}.triangle-slot small{font-size:calc(10px * var(--text-scale,1));color:var(--muted)}.triangle-slot input{width:78px;min-height:33px;border:2px solid var(--green);border-radius:7px;padding:3px 6px;direction:ltr;text-align:center;background:white;font-size:calc(17px * var(--text-scale,1))}.triangle-slot bdi{font-size:calc(16px * var(--text-scale,1));color:var(--green);font-weight:700}.triangle-help{font-size:calc(12px * var(--text-scale,1));color:var(--muted);text-align:center;margin:8px 0}.triangle-check{width:100%;margin-top:6px}.formula-context{background:#e7f0e9;border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:calc(14px * var(--text-scale,1))}.formula-networks{margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:14px}.formula-networks .math{font-size:calc(17px * var(--text-scale,1));line-height:1.9;overflow-wrap:anywhere}.formula-networks h3{font-size:calc(18px * var(--text-scale,1))}.units-list{display:flex;flex-wrap:wrap;gap:15px;margin:14px 0;color:var(--muted);font-size:calc(13px * var(--text-scale,1))}.sheet-answer{padding:15px;background:var(--card);border:1px solid var(--line);border-radius:12px;margin-bottom:14px}.sheet-answer label{display:block;font-weight:700}.sheet-answer input{width:160px;min-height:44px;border:2px solid var(--green);border-radius:8px;padding:7px 10px;font-size:calc(21px * var(--text-scale,1))}.sheet-feedback{margin-bottom:13px}.calc-dialog{max-width:370px}.calc-screen{width:100%;border:1px solid #b4c9be;border-radius:11px;background:white;min-height:56px;padding:10px;font-size:calc(23px * var(--text-scale,1));direction:ltr;text-align:left}.calc-result{direction:ltr;text-align:left;font-size:calc(22px * var(--text-scale,1));color:var(--green);min-height:40px;overflow-wrap:anywhere;margin:8px 0}.calc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;direction:ltr}.calc-grid button{height:48px;border-radius:9px;background:var(--card);border:1px solid var(--line);font-size:calc(21px * var(--text-scale,1));color:var(--ink)}.calc-grid button.operator{background:#e4eee7;color:var(--green)}.calc-grid button.equals{background:var(--green);color:white}.calc-actions{display:flex;gap:8px;margin-top:13px}.calc-actions .btn{flex:1;font-size:calc(14px * var(--text-scale,1))}.confirm-dialog{max-width:460px}.large-text{font-size:calc(19px * var(--text-scale,1))}.large-text .small,.large-text .rounding,.large-text .triangle-help{font-size:calc(15px * var(--text-scale,1))}
    @media(max-width:850px){.exercise-grid,.sim-layout{grid-template-columns:1fr}.hero-symbol{width:115px;height:115px;font-size:calc(25px * var(--text-scale,1))}.course-head{flex-direction:column}.sim-controls{display:grid;grid-template-columns:1fr auto;gap:5px 16px}.sim-controls input[type=range]{grid-column:1/-1}.sim-controls .toggle{margin:5px 0;grid-column:1}.sim-controls .btn{grid-column:2}.sim-controls .small{grid-column:1/-1}.metrics{margin-top:14px}}
    .diagram-preview{display:block;width:100%;padding:0;background:transparent;color:inherit;border-radius:10px}.diagram-preview svg{max-width:100%}.diagram-open-label{display:block;padding:7px;color:var(--green);font-size:calc(13px * var(--text-scale,1));font-weight:700;text-align:center}.diagram-preview:hover{background:var(--soft)}.diagram-toolbar{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px}.diagram-toolbar .btn{min-width:44px;min-height:44px}.diagram-viewport{overflow:auto;max-height:60vh;direction:ltr;overscroll-behavior:contain;touch-action:pan-x pan-y pinch-zoom;border:1px solid var(--line);border-radius:12px;background:var(--card)}.diagram-canvas{width:100%;min-width:100%}.diagram-canvas svg{display:block;width:100%;height:auto;max-width:none}.formula-tabs{display:flex;gap:8px;margin-bottom:16px}.formula-tab{flex:1;min-height:46px;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--muted);font-weight:700}.formula-tab[aria-selected=true]{background:var(--ink);border-color:var(--ink);color:white}.sheet-givens{margin:10px 0}.sheet-givens .given{min-width:0}.sheet-answer input{max-width:100%;min-width:0}
    @media(max-width:570px){.app{padding:14px 12px 25px}.topbar{align-items:flex-start;padding-bottom:14px;flex-wrap:wrap}.brand-title{font-size:calc(17px * var(--text-scale,1))}.hero{padding:23px 0 18px}.hero-symbol{display:none}.hero-copy p{font-size:calc(15px * var(--text-scale,1))}.tabs{gap:5px}.tab{padding:11px 8px;font-size:calc(14px * var(--text-scale,1));min-height:73px}.tab span{font-size:calc(10px * var(--text-scale,1))}.card{padding:16px}.level{font-size:calc(14px * var(--text-scale,1))}.given{min-width:85px;padding:7px 10px}.given bdi{font-size:calc(17px * var(--text-scale,1))}.answer-row{flex-wrap:wrap}.answer-row>.btn{width:100%}.answer-tools .btn{font-size:calc(13px * var(--text-scale,1));flex:1;padding:9px}.formula-grid,.formula-networks{grid-template-columns:1fr}.formula-card{padding:13px}dialog{padding:16px;border-radius:16px}.sim-controls{grid-template-columns:1fr}.sim-controls .btn{grid-column:1}.metrics{grid-template-columns:1fr 1fr 1fr}.metric{padding:7px}.metric bdi{font-size:calc(14px * var(--text-scale,1))}.metric small{font-size:calc(10px * var(--text-scale,1))}h2{font-size:calc(22px * var(--text-scale,1))}.footer .text-btn{font-size:calc(12px * var(--text-scale,1))}}
    .sim-layout>div{min-width:0}
    .formula-tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}.formula-tab{min-width:0}.manual-entry{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:18px}.manual-intro{margin-bottom:14px}.manual-choices{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:10px 0 18px}.manual-choice{min-width:0;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:11px;padding:12px;text-align:right}.manual-choice strong{display:block;font-size:calc(15px * var(--text-scale,1));line-height:1.5}.manual-choice bdi{font-size:calc(14px * var(--text-scale,1));color:var(--muted);margin-top:5px}.manual-choice[aria-pressed=true]{border-color:var(--green);box-shadow:inset 0 0 0 1px var(--green);background:var(--soft)}.manual-workspace{display:grid;grid-template-columns:170px minmax(0,1fr);gap:22px;align-items:start}.manual-list{min-width:0;background:var(--soft);padding:12px;border-radius:12px}.manual-list>.btn{width:100%;margin-bottom:10px}.manual-list h3{font-size:calc(14px * var(--text-scale,1));margin-bottom:10px}.manual-list-row{display:flex;direction:ltr;align-items:center;gap:6px;margin:8px 0}.manual-list-row bdi{font-weight:700;white-space:nowrap}.manual-list-row input{width:0;min-width:0;flex:1;min-height:42px;border:1px solid #a8c4b6;border-radius:7px;background:white;padding:5px;direction:ltr;text-align:center;font-size:calc(17px * var(--text-scale,1))}.manual-form{min-width:0}.manual-form h3{text-align:center;font-size:calc(17px * var(--text-scale,1))}.manual-placeholder{border:1px dashed #b9cfc2;border-radius:13px;padding:30px 15px;text-align:center;color:var(--muted)}.manual-triangle{width:100%;max-width:360px;height:auto;aspect-ratio:260/225}.manual-triangle .triangle-slot{width:32%;gap:3px}.manual-triangle .triangle-slot.top{top:18%;left:34%}.manual-triangle .triangle-slot.left{top:63%;left:12%}.manual-triangle .triangle-slot.right{top:63%;left:56%}.manual-triangle .triangle-slot input{width:100%;min-width:0;max-width:100px;min-height:40px;padding:4px;font-size:calc(20px * var(--text-scale,1))}.manual-answer{margin-top:15px}.manual-answer label{display:block;margin-bottom:7px;font-weight:700}.manual-answer input{width:100%;min-width:0;min-height:46px;padding:8px 10px;border:2px solid var(--green);border-radius:9px;background:white;font-size:calc(21px * var(--text-scale,1));direction:ltr;text-align:left}.manual-answer .btn{width:100%;margin-top:10px}.manual-note{margin:14px 0 0}.manual-status{min-height:0}.manual-status:empty{display:none}
    @media(max-width:570px){.formula-tab{padding:8px 5px;font-size:calc(13px * var(--text-scale,1))}.manual-choices{gap:7px}.manual-choice{padding:9px}.manual-choice strong{font-size:calc(13px * var(--text-scale,1))}.manual-choice bdi{font-size:calc(12px * var(--text-scale,1))}.manual-workspace{grid-template-columns:84px minmax(0,1fr);gap:10px}.manual-list{padding:6px}.manual-list>.btn{padding:7px 3px;font-size:calc(13px * var(--text-scale,1))}.manual-list h3{font-size:calc(12px * var(--text-scale,1));line-height:1.5}.manual-list-row{gap:3px}.manual-list-row bdi{font-size:calc(14px * var(--text-scale,1))}.manual-list-row input{min-height:36px;padding:3px;font-size:calc(16px * var(--text-scale,1))}.manual-triangle .triangle-slot{gap:2px}.manual-triangle .triangle-slot strong{font-size:calc(17px * var(--text-scale,1))}.manual-triangle .triangle-slot input{min-height:28px;height:28px;font-size:calc(16px * var(--text-scale,1));padding:2px}.manual-form h3{font-size:calc(14px * var(--text-scale,1))}.manual-answer label{font-size:calc(14px * var(--text-scale,1))}.manual-answer .btn{font-size:calc(13px * var(--text-scale,1));padding:9px 6px}.manual-answer input{font-size:calc(18px * var(--text-scale,1))}.manual-list .small{font-size:calc(11px * var(--text-scale,1))}}
    @media(max-width:570px){.sim-layout{display:flex;flex-direction:column;gap:14px}.sim-layout>div:first-child{display:contents}.sim-layout .diagram{order:0;width:100%}.sim-layout .sim-controls{order:1;width:100%}.sim-layout #sim-metrics{order:2;width:100%}.table-scroll table,.table-scroll tbody{display:block;width:100%}.table-scroll caption{display:block;width:100%;white-space:normal}.table-scroll thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}.table-scroll tbody tr{display:block;margin-bottom:12px;border:1px solid var(--line);border-radius:10px;overflow:hidden}.table-scroll tbody td{display:flex;align-items:center;justify-content:space-between;gap:12px;white-space:normal;padding:8px 12px}.table-scroll tbody td::before{content:attr(data-label);color:var(--muted);font-size:calc(13px * var(--text-scale,1))}.table-scroll tbody td:last-child{border-bottom:0}}
    .skip-link{position:fixed;top:-100px;right:12px;z-index:10000;background:#182e3c;color:white;padding:12px 18px;border-radius:8px}.skip-link:focus{top:12px}.profile-dialog{max-width:650px}.profile-fields{display:grid;grid-template-columns:1fr 1fr;gap:14px}.profile-fields label{display:block;font-weight:700}.profile-fields input{display:block;min-width:0;width:100%;min-height:46px;padding:9px;border:1px solid #a8c4b6;border-radius:9px;background:white;color:var(--ink)}.terms-document{margin:18px 0;border:1px solid var(--line);border-radius:12px;padding:13px}.terms-document summary,.profile-accessibility summary{cursor:pointer;font-weight:700;min-height:44px;align-content:center}.terms-document p,.terms-document li{font-size:calc(14px * var(--text-scale,1))}.terms-document h3{font-size:calc(17px * var(--text-scale,1));margin-top:18px}.consent-row{display:flex;align-items:flex-start;gap:10px;margin:18px 0;font-size:calc(14px * var(--text-scale,1))}.consent-row input{flex:0 0 22px;width:22px;height:22px;margin:2px 0;accent-color:var(--green)}.profile-accessibility{margin-top:18px}.accessibility-dialog{max-width:650px}.accessibility-options{display:grid;gap:12px;margin:14px 0}.accessibility-options label{display:flex;align-items:center;gap:10px;min-height:44px}.accessibility-options input[type=checkbox]{width:22px;height:22px;accent-color:var(--green)}.accessibility-options select{min-height:44px;padding:7px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}.text-scale-150 .manual-workspace{grid-template-columns:1fr}.text-scale-150 .manual-list{max-width:none}.text-scale-150 .manual-list-row input{max-width:220px}.high-contrast{--paper:#fff;--card:#fff;--ink:#000;--muted:#242424;--line:#333;--green:#005b4f;--soft:#e8f4ed}.high-contrast .triangle svg path{stroke:#000}.high-contrast .manual-choice,.high-contrast .formula-tab,.high-contrast .level{border-color:#000}.reduce-motion *,.reduce-motion *::before,.reduce-motion *::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.highlight-links a,.highlight-links .text-btn{text-decoration:underline;text-decoration-thickness:2px}.personal-progress{margin-top:28px}.personal-progress h2:focus,#sim-title:focus{outline:3px solid #c38330;outline-offset:4px}.progress-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.personal-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0}.personal-stat{border:1px solid var(--line);border-radius:12px;padding:13px}.personal-stat strong{display:block;font-size:calc(25px * var(--text-scale,1));color:var(--green)}.personal-chart{margin:22px 0}.personal-chart-row{display:grid;grid-template-columns:115px minmax(0,1fr) 58px;align-items:center;gap:12px;margin:16px 0;font-size:calc(14px * var(--text-scale,1))}.personal-bar{height:25px;border-radius:6px;overflow:hidden;background:#e2e9e2;border:1px solid #c9d8cd}.personal-bar>div{height:100%;background:#116e65;min-width:0}.personal-rate{direction:ltr;text-align:left;font-weight:700}.personal-progress .table-scroll th,.personal-progress .table-scroll td{white-space:normal}.personal-progress .table-scroll td:first-child{font-weight:700}.sim-jump{margin-top:10px}.simulator{background:#050505;color:#fff;border-color:#555}.simulator .eyebrow,.simulator .muted,.simulator .small,.simulator .metric small,.simulator caption{color:#fff}.simulator .sim-controls,.simulator .metric,.simulator th,.simulator .btn.secondary{background:#111;color:#fff;border-color:#666}.simulator .sim-value,.simulator .metric bdi{color:#fff}.simulator td[data-label="זרם"] bdi,.simulator .metric:nth-child(2) bdi{color:#ff6565}.simulator td[data-label="מתח"] bdi{color:#65e680}.simulator .diagram-preview,.simulator .diagram-preview:hover{background:#000;color:#fff}.simulator .diagram-open-label{color:#fff}.simulator .metric,.simulator .table-scroll td,.simulator .table-scroll tbody tr{border-color:#666}.simulator th{color:#fff}.simulator input[type=range],.simulator input[type=checkbox]{accent-color:#fff}.sim-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:calc(13px * var(--text-scale,1));margin:12px 0;color:#fff}.sim-legend .current{color:#ff6565}.sim-legend .voltage{color:#65e680}.simulator .table-scroll tbody td::before{color:#fff}.dark-diagram .diagram-viewport{background:#000;border-color:#666}.manual-choice svg{display:block;max-width:115px;width:100%;height:auto;margin:6px auto}.manual-choice math{font-size:calc(15px * var(--text-scale,1))}.formula-lines math{margin:3px 0}.mathml{font-family:"Cambria Math","STIX Two Math","Times New Roman",serif;direction:ltr;unicode-bidi:isolate;max-width:100%}.formula-networks .math{overflow-x:auto;max-width:100%}.formula-card .mathml{font-size:calc(20px * var(--text-scale,1))}select:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{outline:3px solid #c38330;outline-offset:3px}
    @media(max-width:570px){.profile-fields{grid-template-columns:1fr}.personal-summary{gap:6px}.personal-stat{padding:9px}.personal-stat strong{font-size:calc(21px * var(--text-scale,1))}.personal-stat .small{font-size:calc(11px * var(--text-scale,1))}.personal-chart-row{grid-template-columns:82px minmax(0,1fr) 43px;gap:7px;font-size:calc(12px * var(--text-scale,1))}.personal-chart-row .personal-rate{font-size:calc(12px * var(--text-scale,1))}.personal-progress .table-scroll tbody td{gap:10px}.personal-progress .table-scroll tbody td::before{max-width:55%}.text-scale-150 .tabs,.text-scale-150 .formula-tabs,.text-scale-150 .manual-choices{grid-template-columns:1fr}.text-scale-150 .personal-summary{grid-template-columns:1fr}.text-scale-150 .personal-chart-row{grid-template-columns:1fr;gap:5px}.text-scale-150 .personal-rate{text-align:right}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}

    .text-scale-125 .triangle:not(.manual-triangle){height:265px}.text-scale-150 .triangle:not(.manual-triangle){height:300px}.text-scale-125 .triangle:not(.manual-triangle) .triangle-slot.top,.text-scale-150 .triangle:not(.manual-triangle) .triangle-slot.top{top:18%}.text-scale-125 .triangle:not(.manual-triangle) .triangle-slot.left,.text-scale-125 .triangle:not(.manual-triangle) .triangle-slot.right,.text-scale-150 .triangle:not(.manual-triangle) .triangle-slot.left,.text-scale-150 .triangle:not(.manual-triangle) .triangle-slot.right{top:63%}
    body{font-size:calc(16px * var(--text-scale,1))}.text-scale-125 .progress-row,.text-scale-150 .progress-row{flex-wrap:wrap}.text-scale-125 .manual-triangle input,.text-scale-150 .manual-triangle input{height:40px;min-height:40px}.attempt-values{display:inline-flex;gap:5px;flex-wrap:wrap;align-items:center}
    .tabs{grid-template-columns:repeat(4,minmax(0,1fr))}
    .progress-dialog{max-width:980px}.progress-dialog .personal-progress{margin-top:0}
    .progress-trend{margin:22px 0}.trend-scroll{overflow-x:auto;direction:ltr}
    .trend-chart{display:block;width:100%;min-width:540px;height:auto}
    .sim-modes{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
    .sim-modes .level[aria-pressed=true]{background:var(--soft)}
    .sim-choice{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:16px}
    .sim-choice label{font-weight:700}.sim-choice select{min-width:0;max-width:100%;min-height:44px;padding:8px;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:9px;font-size:calc(16px * var(--text-scale,1))}
    .custom-fields{display:flex;flex-wrap:wrap;gap:16px;margin:16px 0}
    .custom-field{flex:1;min-width:140px}.custom-field label{display:block;font-weight:700;margin-bottom:5px}
    .custom-field input,.custom-field select{display:block;width:100%;min-width:0;min-height:44px;padding:8px 10px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink);font-size:calc(16px * var(--text-scale,1))}
    .custom-resistors{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:16px 0}
    .custom-resistor{display:flex;align-items:flex-end;gap:8px;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--soft)}
    .custom-resistor .custom-field{min-width:0}.custom-resistor .btn{flex-shrink:0}
    .custom-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
    .custom-simulator .diagram{direction:ltr}
    .custom-sim-note{margin:12px 0 0;color:var(--muted);font-size:calc(13px * var(--text-scale,1))}
    @media(max-width:570px){.tabs{grid-template-columns:repeat(2,minmax(0,1fr))}.custom-resistors{grid-template-columns:1fr}.sim-choice select{width:100%}.text-scale-150 .tabs{grid-template-columns:1fr}}
    .manual-list .manual-fill{min-height:50px;padding:12px 8px;background:#1769c2;color:#fff;border:1px solid #1769c2;font-size:calc(17px * var(--text-scale,1));font-weight:700;line-height:1.4}
    .manual-list .manual-fill:hover{background:#1257a3;color:#fff}
    .manual-paper-note{margin:0 0 8px;padding:7px 6px;border-radius:7px;background:#dceeff;color:#000;font-size:calc(12px * var(--text-scale,1));line-height:1.5}
    .feedback.success,.complete-badge,.completed-row,.step-pill.done{background:#087b38;color:#fff;border-color:#087b38}
    .feedback.error{background:#bd2525;color:#fff}
    input.answer-correct{background:#087b38;color:#fff;border-color:#087b38;opacity:1;-webkit-text-fill-color:#fff}
    input.answer-incorrect{background:#bd2525;color:#fff;border-color:#bd2525!important;-webkit-text-fill-color:#fff}
    .completed-row{padding:8px 10px;border-radius:8px}
    .manual-keypad{position:sticky;bottom:0;margin-top:16px;padding:12px;background:var(--paper);border:1px solid var(--line);border-radius:12px;box-shadow:0 -5px 20px #182e3c12;z-index:2}
    .manual-keypad-header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px}
    #manual-keypad-value{font-size:calc(19px * var(--text-scale,1));font-weight:700;max-width:100%;overflow-wrap:anywhere}
    .manual-keypad-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;direction:ltr}
    .manual-keypad-grid button{min-width:0;min-height:44px;padding:6px 4px;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;font-size:calc(19px * var(--text-scale,1));font-weight:700}
    .manual-keypad-grid button[data-manual-key="X"],.manual-keypad-grid button[data-manual-key="?"]{background:var(--soft);color:var(--green)}
    .manual-keypad-grid button[data-manual-key="enter"]{grid-column:span 3;background:var(--green);color:white;font-size:calc(23px * var(--text-scale,1))}
    .manual-keypad-grid button[data-manual-key="done"]{font-size:calc(23px * var(--text-scale,1))}
    .manual-keypad-grid button[data-manual-key="clear"]{grid-column:span 2;font-size:calc(14px * var(--text-scale,1))}
    .manual-keypad.numeric-only .manual-keypad-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
    .manual-keypad.numeric-only button[data-manual-key="clear"]{grid-column:1;grid-row:5}
    .manual-keypad.numeric-only button[data-manual-key="enter"]{grid-column:2;grid-row:5}
    .manual-keypad.numeric-only button[data-manual-key="done"]{grid-column:3;grid-row:5}
    .parallel-formulas{display:flex;flex-direction:column;gap:calc(22px * var(--text-scale,1));margin-top:16px}
    .parallel-formulas .network-formula{padding:4px 0;line-height:1.5}
    body:not(.high-contrast) .brand-icon{background:var(--accent);color:#623b05}
    body:not(.high-contrast) .hero-symbol{background:linear-gradient(140deg,#ffe7ae,#ffcf8a);border-color:var(--line);color:#9c570d}
    body:not(.high-contrast) .tab{background:var(--soft);color:var(--ink)}
    body:not(.high-contrast) .tab[aria-selected=true],body:not(.high-contrast) .formula-tab[aria-selected=true]{background:var(--accent);color:var(--ink)}
    body:not(.high-contrast) .formula-tab[aria-selected=true]{border-color:var(--accent)}
    body:not(.high-contrast) .given,body:not(.high-contrast) .formula-context,body:not(.high-contrast) .hint,body:not(.high-contrast) .solution,body:not(.high-contrast) .close,body:not(.high-contrast) .calc-grid button.operator{background:var(--soft)}
    body:not(.high-contrast) .given,body:not(.high-contrast) .hint{border-color:var(--line)}
    body:not(.high-contrast) .personal-bar{background:var(--soft);border-color:var(--line)}
    body:not(.high-contrast) .personal-progress th{background:var(--soft)}
    body:not(.high-contrast) .triangle svg path[fill="#f3f6ee"],body:not(.high-contrast) .manual-choice svg path[fill="#f3f6ee"]{fill:#fff1d5}
    .tab,.formula-tab{border-width:2px;border-style:solid;border-color:var(--line)}
    body:not(.high-contrast) .tab,body:not(.high-contrast) .formula-tab{border-color:#dab568}
    body:not(.high-contrast) .tab[aria-selected=true],body:not(.high-contrast) .formula-tab[aria-selected=true]{border-color:#b9822b}
    .hint .mathml,.solution .mathml{font-size:calc(20px * var(--text-scale,1))}
    .exercise-navigation{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:12px 0}
    .solved-picker{display:flex;align-items:center;gap:8px;flex:1;min-width:0;flex-wrap:wrap}
    .solved-picker select{max-width:100%;min-width:0;min-height:44px;padding:8px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink);font-size:calc(14px * var(--text-scale,1))}
    @media(max-width:570px){.solved-picker{flex-basis:100%}.solved-picker select{flex:1}}
    .triangle-entry-note{margin:4px 0;font-size:calc(13px * var(--text-scale,1));color:var(--muted)}
    .circuit-summary{font-size:calc(13px * var(--text-scale,1));margin:10px 0 14px}
    .circuit-summary-group{margin:8px 0}.circuit-summary-label{display:block;color:var(--muted);font-size:calc(12px * var(--text-scale,1));margin-bottom:5px}
    .circuit-values{display:flex;flex-wrap:wrap;gap:6px}.circuit-value{display:inline-flex;align-items:center;gap:4px;direction:ltr;white-space:nowrap;padding:5px 8px;border:1px solid var(--line);border-radius:8px;background:var(--soft)}
    .circuit-summary .mathml,.triangle-entry-note .mathml{font-size:1em}
    .circuit-target{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin:10px 0 0}.circuit-target .circuit-value{font-weight:700;border-color:var(--green)}
    .solution-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.solution-head .close{flex:none;width:44px;height:44px;border:2px solid var(--green);color:var(--green);font-size:28px;font-weight:800}
    .manual-circuit-reference{display:none}
    .manual-editor,.manual-triangle-panel{min-width:0}
    .manual-show-circuit{width:100%;margin-bottom:12px}
    .calc-grid button[data-calc="²"]{grid-column:1/-1}
    .calc-main{min-width:0}
    .calc-triangle-reference{padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--soft);align-self:start}
    .calc-triangle-reference h3{font-size:calc(15px * var(--text-scale,1));margin:0 0 4px;overflow-wrap:anywhere}
    .calc-reference-icon{display:block;width:22px;height:22px;margin-bottom:5px;color:var(--green)}
    .calc-triangle-reference p{font-size:calc(12px * var(--text-scale,1));margin:0 0 8px}
    .calc-reference-values{display:grid;gap:6px;margin:0}
    .calc-reference-row{display:flex;direction:ltr;align-items:center;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px solid var(--line)}
    .calc-reference-row:last-child{border-bottom:0}
    .calc-reference-row dt,.calc-reference-row dd{margin:0;min-width:0}
    .calc-reference-row dd{display:flex;align-items:baseline;gap:5px;flex-wrap:wrap;justify-content:flex-end;font-size:calc(15px * var(--text-scale,1))}
    .calc-reference-row bdi{overflow-wrap:anywhere;max-width:100%}
    .calc-reference-row small{font-size:calc(12px * var(--text-scale,1));color:var(--muted)}
    .calc-reference-row .mathml{font-size:calc(16px * var(--text-scale,1))}
    @media(min-width:600px){
      .calc-dialog.with-triangle-reference{max-width:680px}
      .with-triangle-reference .calc-layout{display:grid;grid-template-columns:minmax(170px,.8fr) minmax(0,1.2fr);gap:16px;align-items:start}
    }
    @media(max-width:599px){
      .calc-triangle-reference{position:sticky;top:0;z-index:1;margin-bottom:12px;padding:9px}
      .calc-reference-values{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
      .calc-reference-row{flex-direction:column;justify-content:flex-start;gap:3px;padding:5px 3px;border:0;text-align:center}
      .calc-reference-row dd{justify-content:center;font-size:calc(14px * var(--text-scale,1))}
    }
    @media(min-width:375px) and (max-width:599px){
      .calc-dialog.with-triangle-reference{max-width:680px}
      .with-triangle-reference .calc-layout{display:grid;grid-template-columns:minmax(100px,.7fr) minmax(197px,1.3fr);gap:12px;align-items:start}
      .calc-triangle-reference{margin-bottom:0;padding:8px}
      .calc-reference-values{grid-template-columns:1fr}
    }
    @media(min-width:1000px) and (hover:hover) and (pointer:fine){
      #formula-dialog.manual-desktop-view{width:min(1280px,calc(100% - 24px))}
      .manual-desktop-layout{display:grid;grid-template-columns:minmax(280px,.8fr) minmax(552px,1.2fr);gap:24px;align-items:start}
      .manual-circuit-reference{display:block;position:sticky;top:12px;align-self:start;padding:16px;background:var(--card);border:1px solid var(--line);border-radius:14px;max-height:var(--manual-reference-height,660px);overflow:auto}
      .manual-circuit-reference h3{font-size:calc(18px * var(--text-scale,1));margin-bottom:8px}
      .manual-circuit-reference .givens{gap:6px;margin:12px 0}
      .manual-circuit-reference .given{min-width:0;padding:6px 8px}
      .manual-circuit-reference .given bdi{font-size:calc(16px * var(--text-scale,1))}
      .manual-circuit-reference .completed-row{font-size:calc(13px * var(--text-scale,1))}
      #formula-dialog.manual-desktop-view .manual-keypad{width:max(552px,calc(60% - 14.4px));max-width:100%;margin-right:auto;margin-left:0}
      .manual-show-circuit{display:none}
    }
    body.qa-mode:not(.high-contrast){--paper:#eaf3fc;--card:#f6faff;--soft:#dcecff;--line:#b8d1ea;--ink:#173a59;--muted:#486983;--green:#245c96;--accent:#c0dcfa}
    .qa-banner{margin:18px 0;padding:16px;border:2px solid #75a6d6;border-radius:14px;background:var(--soft)}
    .qa-banner-head,.qa-actions{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
    .qa-banner h2{margin:0;color:var(--green)}.qa-banner p{margin:8px 0}
    .qa-selectors{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0}
    .qa-selectors label{display:flex;flex-direction:column;gap:5px;font-size:calc(14px * var(--text-scale,1))}
    .qa-selectors select{width:100%;min-width:0;min-height:44px;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px}
    .qa-answer{border:1px solid var(--green);border-radius:10px;padding:10px;margin-top:10px;background:var(--card)}
    .qa-login input{width:100%;min-height:48px;border:1px solid var(--line);border-radius:9px;padding:10px;direction:ltr}
    .unit-note{padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--soft);font-size:calc(13px * var(--text-scale,1));margin:12px 0}
    .question-dots{flex-wrap:wrap;justify-content:flex-end}.question-dot{width:16px}
    @media(max-width:570px){.qa-selectors{grid-template-columns:repeat(2,minmax(0,1fr))}.qa-actions .btn{flex:1}.progress-row{align-items:flex-start}.question-dots{max-width:110px}}

    /* Content-sized rows keep iframe resizing from distributing height between controls. */
    .top-tools{display:block;width:490px;max-width:100%;min-width:0;height:auto;min-height:0}
    .top-tool-row{display:flex;align-items:stretch;gap:8px;min-width:0}
    .top-tool-row + .top-tool-row{margin-top:8px}
    .top-tools .btn{flex:1 1 0;align-self:stretch;width:0;min-width:0;max-width:100%;height:auto;min-height:46px;margin:0;padding:10px 8px;overflow-wrap:anywhere;font-size:calc(15px * var(--text-scale,1))}
    .access-icon{font-size:21px;line-height:1}
    html{scroll-padding-top:66px}
    #app :where(h2,h3,input,button,section){scroll-margin-top:66px}
    .quickbar-space{height:58px}
    .quickbar{position:fixed;top:var(--quickbar-top,0px);left:0;right:0;z-index:30;display:flex;align-items:center;justify-content:center;gap:12px;height:58px;padding:6px 12px;background:var(--paper);border-bottom:1px solid var(--line);box-shadow:0 3px 12px #7045110a;isolation:isolate}
    .icon-button{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;min-width:44px;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--green);touch-action:manipulation;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
    .exercise-tools{flex-wrap:nowrap;align-items:stretch;gap:5px}
    .exercise-tools>.icon-button{flex:0 0 44px;height:auto;min-height:44px}
    .exercise-tools>.solution-tool{display:inline-flex;align-items:center;justify-content:center;flex:1 1 auto;min-width:0;min-height:44px;margin:0;padding:6px 5px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--green);font-size:calc(12px * var(--text-scale,1));line-height:1.35;white-space:normal;overflow-wrap:anywhere}
    .exercise-tools>.solution-tool:hover{background:var(--soft)}
    .hint-tool svg{filter:drop-shadow(0 0 3px #e7b73399)}
    .solution-step{margin:14px 0}.solution-step p{margin:0 0 6px}
    .solution-methods{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}
    .solution-methods .level{flex:1 1 150px;min-width:0;font-size:calc(12px * var(--text-scale,1));padding:8px;white-space:normal}
    .solution-step .math{max-width:100%;overflow-x:auto;direction:ltr;text-align:center;padding:4px 0 7px}
    .solution-step .mathml{font-size:calc(17px * var(--text-scale,1))}
    .annotated-sum{display:flex;direction:ltr;align-items:flex-end;justify-content:center;gap:8px;width:max-content;min-width:100%;padding:4px 3px}
    .annotated-term{display:flex;flex-direction:column;align-items:center;flex:none;gap:1px;padding-left:calc(var(--factor-width) * var(--text-scale,1))}
    .annotated-prefix{display:flex;align-items:center;gap:6px}
    .annotated-operator{display:inline-flex;align-items:center;height:2.1em}
    .expansion-mark{position:relative;display:block;width:12px;height:18px;flex:none}
    .expansion-factor{position:absolute;right:calc(100% - 3px);top:-1px;white-space:nowrap;line-height:1}
    .solution-step .expansion-factor .mathml{font-size:calc(12px * var(--text-scale,1))}
    .expansion-slash{display:block;width:12px;height:18px;color:var(--green)}
    .decimal-addition{direction:ltr;width:max-content;max-width:100%;margin:10px auto;font-size:calc(17px * var(--text-scale,1));font-variant-numeric:tabular-nums;text-align:right}
    .decimal-addition>div{display:flex;justify-content:space-between;gap:14px;padding:3px 6px}
    .decimal-addition .decimal-total{border-top:1px solid var(--ink);margin-top:4px;padding-top:7px}
    .icon-button:hover{background:var(--soft)}.icon-button svg{width:22px;height:22px;pointer-events:none}
    .icon-tooltip{position:fixed;z-index:40;max-width:calc(100vw - 24px);padding:7px 11px;border:1px solid var(--line);border-radius:8px;background:var(--ink);color:var(--paper);font-size:calc(14px * var(--text-scale,1));line-height:1.5;pointer-events:none;text-align:center}
    .guide-dialog{max-width:740px}
    .guide-dialog .close{border:2px solid var(--green);min-width:44px;min-height:44px;flex:none}
    .guide-intro{color:var(--muted);margin:0 0 16px}
    .guide-section{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:0 14px;margin:10px 0}
    .guide-section summary{cursor:pointer;font-weight:700;min-height:48px;align-content:center;padding:10px 0}
    .guide-section p,.guide-section li{font-size:calc(15px * var(--text-scale,1));line-height:1.75;overflow-wrap:anywhere}
    .guide-section ol,.guide-section ul{padding-inline-start:24px}
    .guide-section li+li{margin-top:7px}
    .guide-section p:last-child,.guide-section ol:last-child,.guide-section ul:last-child{margin-bottom:14px}
    .guide-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
    .feedback-dialog{max-width:600px}
    .rating-dialog{max-width:560px}
    .rating-dialog .public-rating{margin:12px 0 20px}
    .contact-choices{display:grid;grid-template-columns:1fr;gap:12px;margin:16px 0}
    .contact-choices .btn{width:100%;min-height:54px}
    .contact-public-link{color:var(--green);font-weight:700}
    .feedback-rating{margin:16px 0 8px;padding:10px;border:1px solid var(--line);border-radius:10px;min-width:0}
    .feedback-rating legend{padding:0 4px;font-weight:700}
    .rating-stars{display:flex;direction:ltr;justify-content:center;gap:2px}
    .feedback-form .rating-stars label{position:relative;display:grid;place-items:center;min-width:44px;min-height:44px;margin:0;cursor:pointer;border:1px solid transparent;border-radius:8px}
    .rating-stars input{position:absolute;width:1px;height:1px;opacity:0}
    .rating-stars span{font-size:32px;line-height:1;color:var(--muted)}
    .rating-stars label.rated span{color:#a65b00}.rating-stars label:focus-within{outline:3px solid var(--green);outline-offset:2px}
    .rating-caption{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap}

    .feedback-form label{display:block;margin:12px 0 5px;font-weight:700}
    .feedback-form input[type=text],.feedback-form textarea{display:block;width:100%;min-width:0;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink);padding:10px 12px;font-size:calc(16px * var(--text-scale,1));line-height:1.5}
    .feedback-form textarea{min-height:130px;resize:vertical;font-family:inherit}
    .feedback-form .feedback-context{display:flex;gap:8px;align-items:flex-start;font-weight:400;font-size:calc(14px * var(--text-scale,1));margin:12px 0}
    .feedback-context input{width:18px;height:18px;flex-shrink:0;margin-top:4px;accent-color:var(--green)}
    .feedback-form .completion-actions{align-items:center}
    .public-rating{display:flex;align-items:center;justify-content:center;gap:7px 12px;flex-wrap:wrap;margin:16px 0 0;padding:10px;border-radius:10px;background:var(--soft);font-size:calc(14px * var(--text-scale,1))}
    .public-rating-stars{position:relative;display:inline-block;direction:ltr;line-height:1.1;font-size:22px;letter-spacing:2px;color:var(--muted)}
    .public-rating-fill{position:absolute;left:0;top:0;overflow:hidden;white-space:nowrap;width:0;color:#a65b00}
    .public-rating-summary{font-size:calc(14px * var(--text-scale,1));margin:10px 0;color:var(--green);font-weight:700}
    @media(max-width:570px){.top-tools{width:100%;flex-basis:100%}.quickbar{gap:clamp(4px,1.5vw,8px);padding-inline:8px}}
    /* Controls use their content height even while the host resizes its iframe. */
    .tabs,.formula-tabs,.manual-choices,.profile-fields,.accessibility-options,.qa-selectors,.contact-choices,.calc-grid,.manual-keypad-grid{grid-auto-rows:max-content;align-content:start}
    .tabs{height:auto;align-items:start}
    .tab{height:auto;align-self:start}
    html.dark-mode{color-scheme:dark;--paper:#121821;--card:#1c2531;--ink:#f0f3f7;--muted:#bdc9d8;--line:#536170;--green:#83dfc7;--soft:#253c3a;--accent:#efb64a;--amber:#f1c078;--shadow:0 8px 28px #0004;--diagram-ink:#edf4fc;--diagram-wire:#a7bacb;--diagram-surface:#1c2531;--diagram-current:#83dfc7;--diagram-power:#f1c078}
    .dark-mode body.high-contrast{--paper:#000;--card:#000;--ink:#fff;--muted:#eee;--line:#fff;--green:#9affdc;--soft:#102c24}
    .dark-mode body.qa-mode:not(.high-contrast){--paper:#101e2c;--card:#182b3e;--soft:#223c54;--line:#6f96b8;--ink:#eef6ff;--muted:#bfd5e8;--green:#a5d4ff;--accent:#87b7df}
    .dark-mode .btn{color:#10271f}
    .dark-mode .btn.secondary,.dark-mode .btn.soft{color:var(--ink)}
    .dark-mode .tab[aria-selected=true],.dark-mode .formula-tab[aria-selected=true]{color:#171d24}
    .dark-mode body:not(.high-contrast) .tab[aria-selected=true],.dark-mode body:not(.high-contrast) .formula-tab[aria-selected=true]{color:#171d24}
    .high-contrast .tab[aria-selected=true],.high-contrast .formula-tab[aria-selected=true]{background:var(--ink);color:var(--paper)}
    .dark-mode .calc-grid button.equals{color:#10271f}
    .dark-mode body:not(.high-contrast) .hero-symbol{background:linear-gradient(140deg,#41351e,#282621);color:var(--accent)}
    .dark-mode body :is(.given,.formula-context,.hint,.solution,.close,.calc-grid button.operator){background:var(--soft);color:var(--ink)}
    .dark-mode :is(.step-pill.done,.complete-badge){background:var(--soft);color:var(--green)}
    .dark-mode :is(.step-pill.active,.tab[aria-selected=true]){color:#171d24}
    .dark-mode input:not([type=checkbox]):not([type=radio]):not([type=range]),.dark-mode select,.dark-mode textarea{background:var(--card);color:var(--ink)}
    .dark-mode :is(input,textarea)::placeholder{color:var(--muted);opacity:1}
    .dark-mode .mathml,.dark-mode .mathml *{color:inherit;-webkit-text-fill-color:currentColor}
    .dark-mode .personal-bar>div{background:var(--green)}
    .dark-mode .personal-bar{background:var(--soft);border-color:var(--line)}
    .dark-mode body.high-contrast .brand-icon{background:var(--green);color:var(--paper)}
    .dark-mode body.high-contrast .hero-symbol{background:var(--paper);color:var(--green);border-color:var(--line)}
    .dark-mode body.high-contrast .tab:not([aria-selected=true]){background:var(--card);color:var(--ink)}
    .dark-mode :is(.sim-controls,th){background:var(--soft);color:var(--ink)}
    .dark-mode .simulator :is(.sim-controls,th){background:#111;color:#fff}
    .dark-mode .feedback.error{background:#48272c;color:#ffd2ca}
    .dark-mode .feedback.success{background:#173e30;color:#a4edc7}
    /* Include body so night colors win over the daytime SVG fill rule. */
    html.dark-mode body :is(.triangle,.manual-choice,.manual-triangle) svg path[fill="#f3f6ee"]{fill:var(--soft)}
    html.dark-mode body :is(.triangle,.manual-choice,.manual-triangle) svg path{stroke:var(--line)}
    .dark-mode .manual-choice svg g{fill:var(--ink)}
    .dark-mode #formula-dialog{--ink:#fff;--green:#147d64;--formula-value-bg:#e5fff2}
    .dark-mode body.high-contrast #formula-dialog{--green:#005b46}
    .dark-mode #formula-dialog .mathml,.dark-mode #formula-dialog .mathml *{color:inherit;-webkit-text-fill-color:currentColor}
    .dark-mode #formula-dialog .triangle-slot :is(strong,small){color:var(--ink)}
    .dark-mode #formula-dialog .manual-choice svg :is(g,text){fill:var(--ink)}
    .dark-mode #formula-dialog .triangle-slot bdi{color:var(--green);background:var(--formula-value-bg);border-radius:5px;padding:1px 5px}
    .dark-mode #formula-dialog .btn:not(.secondary):not(.soft){color:#fff}
    .dark-mode #formula-dialog .formula-tab[aria-selected=true]{background:var(--green);border-color:var(--green);color:#fff}
    .dark-mode #formula-dialog :is(.manual-paper-note,.text-btn,.diagram-open-label){color:var(--ink)}
    .dark-mode #formula-dialog .manual-paper-note{background:var(--soft)}
    .dark-mode #formula-dialog :is(.manual-keypad-grid button[data-manual-key="X"],.manual-keypad-grid button[data-manual-key="?"],.solution-head .close,.expansion-mark){color:var(--green);background:var(--formula-value-bg)}
    .dark-mode #formula-dialog .expansion-factor{color:var(--ink)}
    .dark-mode #formula-dialog .solution-methods .level[aria-pressed=true]{background:var(--green);color:#fff}
    .dark-mode #formula-dialog .complete-badge{color:#fff;background:var(--green)}
    .dark-mode .rating-stars label.rated span,.dark-mode .public-rating-fill{color:#ffd06a}

    /* Black night surfaces, with restrained warm accents matching the site. */
    html.dark-mode{--paper:#000000;--card:#121212;--soft:#221e17;--ink:#e9e2d6;--muted:#c0b49e;--line:#665a43;--green:#d7b575;--accent:#d3ac65;--amber:#d0ad75;--diagram-surface:#121212;--diagram-ink:#e9e2d6;--diagram-wire:#b7aa92;--diagram-current:#d7b575;--diagram-power:#d0ad75}
    .dark-mode dialog::backdrop{background:#000b}
    .dark-mode body.qa-mode:not(.high-contrast){--paper:#000;--card:#101820;--soft:#172634;--line:#4c6b86;--ink:#e3ecf3;--muted:#b5c6d4;--green:#a9c9e5;--accent:#7599b8}
    .dark-mode .btn:not(.secondary):not(.soft){background:#4b381d;color:#f2e6d0;border-color:#80643a}
    .dark-mode .btn.secondary,.dark-mode .btn.soft{background:var(--soft);color:var(--ink);border-color:var(--line)}
    .dark-mode body:not(.high-contrast) :is(.tab,.formula-tab){background:var(--card);color:var(--muted);border-color:var(--line)}
    .dark-mode body:not(.high-contrast) :is(.tab,.formula-tab)[aria-selected=true]{background:#46341c;color:#f2dfb8;border-color:#a48145}
    .dark-mode .step-pill.active{background:#4b381d;color:#f2dfb8;border-color:#a48145}
    .dark-mode body:not(.high-contrast) .brand-icon{background:#4b381d;color:#f2dfb8}
    .dark-mode body:not(.high-contrast) .hero-symbol{background:linear-gradient(140deg,#292318,#15130f);border-color:var(--line);color:var(--accent)}
    .dark-mode input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=color]),.dark-mode select,.dark-mode textarea{background:var(--card);color:var(--ink);border-color:var(--line)}
    .dark-mode .question-dot.current{background:#9b7d47}
    .dark-mode :is(.completed-row,.complete-badge,.step-pill.done){background:#172b20;color:#c1dfcb;border-color:#486650}
    .dark-mode input.answer-correct{background:#173322;color:#c5e8ce;border-color:#518562;-webkit-text-fill-color:#c5e8ce}
    .dark-mode input.answer-incorrect{background:#3c2020;color:#f1c9c4;border-color:#9c615b!important;-webkit-text-fill-color:#f1c9c4}
    .dark-mode #formula-dialog{--ink:#e9e2d6;--green:#d7b575;--formula-value-bg:#302719}
    .dark-mode #formula-dialog .btn:not(.secondary):not(.soft){color:#f2e6d0;background:#4b381d;border-color:#80643a}
    .dark-mode #formula-dialog .manual-fill{background:#233a50;color:#dce8f3;border-color:#45647f}
    .dark-mode #formula-dialog .formula-tab[aria-selected=true],.dark-mode #formula-dialog .solution-methods .level[aria-pressed=true]{background:#46341c;color:#f2dfb8;border-color:#a48145}
    .dark-mode #formula-dialog .complete-badge{background:#172b20;color:#c1dfcb}
    .dark-mode #formula-dialog .manual-paper-note{background:var(--soft);color:var(--ink)}
    .dark-mode #formula-dialog .triangle-slot bdi{background:var(--formula-value-bg);color:#e2c891}
    .dark-mode #manual-keypad .manual-keypad-grid button[data-manual-key=enter]{background:#4b381d;color:#f2e6d0;border-color:#80643a}
    .dark-mode body.high-contrast #formula-dialog{--ink:#fff;--green:#ffe0a1;--formula-value-bg:#171717}
    .dark-mode body.high-contrast .btn,.dark-mode body.high-contrast .step-pill.active{background:#000;color:#fff;border-color:#fff}
    .calc-dialog{max-width:420px}
    .calc-head-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
    .calc-settings{border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:16px;background:var(--soft)}
    .calc-settings label{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;font-size:calc(14px * var(--text-scale,1))}
    .calc-settings label:has(input[type=checkbox]){justify-content:flex-start}
    .calc-settings select{max-width:100%;min-width:0;min-height:44px;border:1px solid var(--line);border-radius:8px;padding:6px;background:var(--card);color:var(--ink)}
    .calc-settings input[type=color]{width:66px;height:44px;border:1px solid var(--line);border-radius:8px;padding:4px;background:var(--card)}
    .calc-settings input[type=checkbox]{width:20px;height:20px;accent-color:var(--green)}
    .calc-settings p{margin:4px 0 14px}
    .calc-toolbar,.calc-fraction-nav{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}
    .calc-toolbar>.btn{flex:1;min-width:0;font-size:calc(13px * var(--text-scale,1));padding:8px}
    .calc-fraction-icon{display:inline-flex;flex-direction:column;line-height:1.05;font-size:14px;direction:ltr}
    .calc-fraction-icon>span:first-child{border-bottom:1.5px solid currentColor;padding-bottom:2px}
    .calc-fraction-icon>span:last-child{padding-top:2px}
    .calc-expression-preview{direction:ltr;text-align:left;overflow-x:auto;max-width:100%;padding:12px 8px;min-height:58px;border:1px solid var(--line);border-radius:9px;margin-top:8px;background:var(--soft)}
    .calc-expression-preview .mathml,.calc-result .mathml{font-size:calc(24px * var(--text-scale,1))}
    .calc-result{color:var(--ink);overflow-x:auto;padding-block:8px;min-height:52px}
    #calc-result-note:empty{display:none}
    #calc-result-note{margin:0 0 10px;font-size:calc(12px * var(--text-scale,1))}
    .calc-fraction-editor{padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--soft)}
    .calc-fraction-fields{display:grid;max-width:100%;width:200px;margin:auto;gap:6px;text-align:center}
    .calc-fraction-fields label{display:grid;min-width:0;gap:2px}
    .calc-fraction-fields .calc-numerator{border-bottom:2px solid var(--ink);padding-bottom:8px}
    .calc-fraction-fields input{display:block;width:100%;min-width:0;min-height:44px;text-align:center;direction:ltr;border:1px solid var(--line);border-radius:8px;padding:7px;background:var(--card);color:var(--ink)}
    .calc-fraction-nav{justify-content:center}
    .calc-grid button{min-width:0;height:auto;min-height:48px;padding:6px 3px}
    .calc-dialog .calc-grid{gap:7px}
    .calc-dialog .calc-actions{flex-wrap:wrap}
    body:not(.high-contrast) #calculator-dialog{--paper:var(--calc-paper);--card:var(--calc-card);--soft:var(--calc-soft);--line:var(--calc-line);--ink:var(--calc-ink);--muted:var(--calc-muted);--green:var(--calc-accent);background:var(--paper);color:var(--ink)}
    body:not(.high-contrast) #calculator-dialog :is(.calc-screen,.calc-fraction-fields input){background:var(--calc-screen);color:var(--ink);border-color:var(--line)}
    body:not(.high-contrast) #calculator-dialog .calc-grid button{background:var(--card);color:var(--ink);border-color:var(--line)}
    body:not(.high-contrast) #calculator-dialog :is(.calc-grid button.operator,.btn.secondary,.close){background:var(--soft);color:var(--ink);border-color:var(--line)}
    body:not(.high-contrast) #calculator-dialog :is(.calc-grid button.equals,.btn:not(.secondary):not(.soft)){background:var(--calc-accent);color:var(--calc-onAccent);border-color:var(--line)}
    body:not(.high-contrast) #calculator-dialog .text-btn{color:var(--ink)}
    body:not(.high-contrast) #calculator-dialog #calc-format[aria-pressed=true]{border:2px solid var(--calc-accent)}
    .high-contrast #calculator-dialog :is(.calc-grid button,.calc-fraction-fields input,.calc-screen){background:var(--paper);color:var(--ink);border-color:var(--line)}
    .high-contrast #calculator-dialog .calc-grid button.equals{background:var(--ink);color:var(--paper)}
    @media(max-width:420px){.calc-dialog{padding:14px}.calc-head-actions{gap:5px}.calc-head-actions .btn{padding:7px}.calc-toolbar{gap:6px}.calc-toolbar>.btn{font-size:calc(12px * var(--text-scale,1))}.calc-settings label{align-items:flex-start}.calc-settings select{width:100%}}


    .birth-input-row{display:flex;align-items:stretch;gap:8px;direction:ltr}
    .profile-fields .birth-input-row>input{flex:1;min-width:0;text-align:left;font-variant-numeric:tabular-nums;letter-spacing:.04em}
    .profile-fields label.birth-calendar{position:relative;display:grid;place-items:center;flex:0 0 46px;min-height:46px;border:1px solid var(--line);border-radius:9px;background:var(--soft);color:var(--ink);overflow:hidden;cursor:pointer}
    .birth-calendar svg{width:23px;height:23px;pointer-events:none}
    .profile-fields .birth-calendar input{position:absolute;inset:0;display:block;width:100%;height:100%;min-height:0;opacity:0;padding:0;border:0;cursor:pointer}
    .birth-calendar:focus-within{outline:3px solid #c38330;outline-offset:3px}
    .birth-help{margin:6px 0 0;line-height:1.6;font-weight:400}
    .dark-mode .profile-fields label.birth-calendar{background:var(--soft);color:var(--ink);border-color:var(--line)}
  </style>
</head>
<body>
<a class="skip-link" href="#learning-main">דילוג לתרגול</a>
<div class="app" id="app">
  <div class="quickbar-space"><nav class="quickbar" id="quickbar" aria-label="כלים מהירים"><button type="button" class="icon-button" data-open-formulas data-tooltip="דף נוסחאות" aria-label="דף נוסחאות"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 12h7M9 16h7"/></svg></button><button type="button" class="icon-button" data-open-calculator data-tooltip="מחשבון" aria-label="מחשבון"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8M8 11h1M12 11h1M16 11h0M8 15h1M12 15h1M16 15h0M8 19h1M12 19h1M16 19h0"/></svg></button><button type="button" class="icon-button" data-new-course data-tooltip="תרגילים חדשים" aria-label="תרגילים חדשים"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 7a8 8 0 1 0 0 10M20 3v5h-5"/></svg></button><button type="button" class="icon-button" data-show-progress data-tooltip="התקדמות אישית" aria-label="התקדמות אישית"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 3v17h17M8 16v-4M13 16V8M18 16V4"/></svg></button><button type="button" class="icon-button" data-open-ratings data-tooltip="דירוג האתר" aria-label="דירוג האתר" aria-haspopup="dialog" aria-controls="ratings-dialog"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9z"/></svg></button><button type="button" class="icon-button" data-open-guide data-tooltip="מדריך שימוש" aria-label="מדריך שימוש" aria-haspopup="dialog" aria-controls="guide-dialog"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1ZM12 5v15"/><path d="M6 8h2M6 12h2M16 8h2M16 12h2"/></svg></button></nav></div>
  <header class="topbar">
    <div class="identity"><div class="brand-icon" aria-hidden="true">ϟ</div><div><div class="brand-title">יסודות החשמל</div><div class="eyebrow">תרגול למתחילים · DC</div></div></div>
    <div class="top-tools">
      <div class="top-tool-row"><button class="btn secondary" data-open-profile id="profile-label">פרופיל</button><button class="btn secondary" id="text-size" aria-pressed="false" aria-label="שינוי גודל טקסט">שינוי גודל טקסט</button></div>
      <div class="top-tool-row"><button class="btn secondary" data-show-progress>התקדמות אישית</button><button class="btn secondary" data-open-accessibility><span class="access-icon" aria-hidden="true">♿</span>נגישות</button></div>
      <div class="top-tool-row"><button class="btn secondary" data-new-course>איפוס תרגילים</button><button class="btn secondary" data-open-feedback>פנייה לעומר</button></div>
    </div>
  </header>
  <div id="qa-panel" hidden></div>
  <section class="hero"><div class="hero-copy"><div class="eyebrow">לומדים להבין, ואז לחשב</div><h1>חשמל, צעד אחרי צעד.</h1><p>תרגול קצר של חוק אום, הספק ומעגלים. מתחילים במספרים שלמים, ממשיכים לעשרוניים ומתקדמים לקילו ומגה־אוהם — עם מחשבון, רמזים ודף נוסחאות בכל שלב.</p></div><div class="hero-symbol" aria-hidden="true">U = I × R<small>להבין את הקשר בין הנתונים</small></div></section>
  <nav class="tabs" role="tablist" aria-label="תחומי התרגול">
    <button id="tab-ohm" class="tab" data-tab="ohm" role="tab" aria-controls="workspace" aria-selected="true" tabindex="0">חוק אום והספק<span>מתח · זרם · התנגדות · הספק</span></button>
    <button id="tab-series" class="tab" data-tab="series" role="tab" aria-controls="workspace" aria-selected="false" tabindex="-1">מעגל טורי<span>אותו זרם בכל הרכיבים</span></button>
    <button id="tab-parallel" class="tab" data-tab="parallel" role="tab" aria-controls="workspace" aria-selected="false" tabindex="-1">מעגל מקבילי<span>אותו מתח בכל הענפים</span></button>
    <button id="tab-simulator" class="tab" data-tab="simulator" role="tab" aria-controls="simulator-workspace" aria-selected="false" tabindex="-1">סימולטור<span>מעגל מתרגיל או מעגל משלכם</span></button>
  </nav>
  <main id="learning-main" tabindex="-1" aria-label="תרגול והתקדמות"><div id="storage-notice" class="feedback error" role="status" hidden></div><section id="workspace" role="tabpanel" aria-labelledby="tab-ohm"></section><section id="simulator-workspace" role="tabpanel" aria-labelledby="tab-simulator" hidden></section></main>
  <footer class="footer">
    <div class="footer-row"><div>הפרופיל וההתקדמות האישית נשמרים בדפדפן במכשיר הזה. אפשר להמשיך מהתרגיל האחרון או לקבל תרגילים חדשים בכפתור האיפוס.</div><div class="footer-links"><button class="text-btn" data-open-formulas>דף נוסחאות</button><button class="text-btn" id="new-course">איפוס תרגילים</button><button class="text-btn" data-open-terms>תנאי שימוש ופרטיות</button><button class="text-btn" data-open-accessibility>הצהרת נגישות</button><button class="text-btn" data-open-ratings aria-haspopup="dialog" aria-controls="ratings-dialog">דירוג</button><button class="text-btn" data-open-qa>QA</button></div></div>

    <hr class="footer-divider">
    <div class="site-credits"><button type="button" class="logo-zoom" data-open-logo aria-label="הגדלת לוגו OBE-26" aria-haspopup="dialog" aria-controls="logo-dialog"><img class="footer-logo" src="data:image/jpeg;base64,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" alt="לוגו OBE-26 Electronic Systems" width="1536" height="614"></button><div class="credit-line"><bdi lang="en">Designed by OBE-26</bdi><span>© <bdi>OBE-26</bdi> · כל הזכויות שמורות</span></div></div>
  </footer>
</div>
<div id="icon-tooltip" class="icon-tooltip" role="tooltip" hidden></div>
<dialog id="ratings-dialog" class="rating-dialog" aria-labelledby="ratings-title"><div class="dialog-head"><h2 id="ratings-title">דירוג האתר</h2><button type="button" class="close" data-close-dialog="ratings-dialog" aria-label="סגירת דירוג האתר">×</button></div><p id="rating-status" class="muted" role="status">תוצאות הדירוג נטענות…</p><section class="public-rating" id="public-rating" aria-label="דירוג האתר" aria-live="polite" hidden><strong>דירוג האתר</strong><span class="public-rating-stars" aria-hidden="true"><span>★★★★★</span><span class="public-rating-fill" id="public-rating-fill">★★★★★</span></span><span data-public-rating-text></span><a id="public-reviews-link" class="contact-public-link" target="_blank" rel="noopener noreferrer" hidden>משובים ב־GitHub</a></section><div class="completion-actions"><button type="button" class="btn" data-contact-mode="review">משוב ודירוג אפליקציה</button></div></dialog>
<dialog id="contact-dialog" class="confirm-dialog" aria-labelledby="contact-title"><div class="dialog-head"><h2 id="contact-title">פנייה לעומר</h2><button type="button" class="close" data-close-dialog="contact-dialog" aria-label="סגירת פנייה לעומר">×</button></div><div class="contact-choices"><button class="btn" type="button" data-contact-mode="review">משוב ודירוג אפליקציה</button><button class="btn secondary" type="button" data-contact-mode="note">הערות</button></div></dialog>
<dialog id="feedback-dialog" class="feedback-dialog" aria-labelledby="feedback-title"><div class="dialog-head"><h2 id="feedback-title">משוב ודירוג אפליקציה</h2><button type="button" class="close" data-close-dialog="feedback-dialog" aria-label="סגירת הפנייה">×</button></div><p class="small muted" id="feedback-disclosure"></p><p class="public-rating-summary" data-public-rating-text hidden></p><form id="feedback-form" class="feedback-form" novalidate aria-describedby="feedback-disclosure"><div data-note-only hidden><label for="feedback-subject">נושא ההערה (רשות)</label><input type="text" id="feedback-subject" maxlength="120" autocomplete="off" aria-describedby="feedback-status"></div><fieldset class="feedback-rating" id="feedback-rating-group" data-review-only><legend>דירוג האפליקציה</legend><div class="rating-stars"><label><input type="radio" name="feedback-rating" value="1" aria-label="1 מתוך 5 כוכבים"><span aria-hidden="true">★</span></label><label><input type="radio" name="feedback-rating" value="2" aria-label="2 מתוך 5 כוכבים"><span aria-hidden="true">★</span></label><label><input type="radio" name="feedback-rating" value="3" aria-label="3 מתוך 5 כוכבים"><span aria-hidden="true">★</span></label><label><input type="radio" name="feedback-rating" value="4" aria-label="4 מתוך 5 כוכבים"><span aria-hidden="true">★</span></label><label><input type="radio" name="feedback-rating" value="5" aria-label="5 מתוך 5 כוכבים"><span aria-hidden="true">★</span></label></div><div class="rating-caption"><span id="feedback-rating-label" class="small muted" role="status">עדיין לא נבחר דירוג</span><button type="button" class="text-btn" id="feedback-rating-clear">ניקוי דירוג</button></div></fieldset><label for="feedback-message" id="feedback-message-label">מה דעתכם על האפליקציה? (רשות)</label><textarea id="feedback-message" maxlength="4000" aria-describedby="feedback-status"></textarea><div data-note-only hidden><label class="feedback-context"><input type="checkbox" id="feedback-context" checked>צירוף מיקום התרגיל הנוכחי כדי לעזור בבדיקה</label><p id="feedback-context-label" class="small muted"></p></div><div id="feedback-status" class="feedback" role="status" aria-live="polite"></div><div class="completion-actions"><button type="submit" class="btn" id="feedback-send" disabled>שליחת משוב ודירוג</button><button type="button" class="btn secondary" data-contact-back>חזרה</button><a id="feedback-result-link" class="contact-public-link" target="_blank" rel="noopener noreferrer" hidden>צפייה במשוב ב־GitHub</a></div></form></dialog>
<dialog id="logo-dialog" class="logo-dialog" aria-labelledby="logo-title"><div class="dialog-head"><h2 id="logo-title">OBE-26</h2><button type="button" class="close" data-close-dialog="logo-dialog" aria-label="סגירת הלוגו המוגדל" autofocus>×</button></div><img id="logo-large" class="logo-large" alt="לוגו OBE-26 Electronic Systems מוגדל" width="1536" height="614"></dialog>
<dialog id="qa-login-dialog" class="confirm-dialog qa-login" aria-labelledby="qa-login-title"><div class="dialog-head"><h2 id="qa-login-title">כניסה למצב בדיקות</h2><button class="close" data-close-dialog="qa-login-dialog" aria-label="סגירת כניסה למצב בדיקות">×</button></div><form id="qa-login-form"><label for="qa-password">סיסמה</label><input id="qa-password" type="password" inputmode="numeric" autocomplete="off" maxlength="32" required aria-describedby="qa-login-error"><div id="qa-login-error" class="feedback error" role="alert"></div><button class="btn" type="submit">כניסה למצב בדיקות</button></form></dialog>
<dialog id="progress-dialog" class="progress-dialog" aria-labelledby="progress-dialog-title"><div class="dialog-head"><h2 id="progress-dialog-title">התקדמות אישית</h2><button class="close" data-close-dialog="progress-dialog" aria-label="סגירת ההתקדמות האישית">×</button></div><section id="personal-progress" class="card personal-progress" aria-labelledby="personal-progress-title"></section></dialog>
<dialog id="formula-dialog" aria-labelledby="formula-title"><div class="dialog-head"><h2 id="formula-title">דף נוסחאות</h2><button class="close" data-close-dialog="formula-dialog" aria-label="סגירת דף הנוסחאות">×</button></div><nav class="formula-tabs" role="tablist" aria-label="תצוגת דף הנוסחאות"><button id="formula-tab-reference" class="formula-tab" data-formula-tab="reference" role="tab" aria-selected="true" aria-controls="formula-body" tabindex="0">נוסחאות</button><button id="formula-tab-help" class="formula-tab" data-formula-tab="help" role="tab" aria-selected="false" aria-controls="formula-body" tabindex="-1">עזרה</button><button id="formula-tab-manual" class="formula-tab" data-formula-tab="manual" role="tab" aria-selected="false" aria-controls="formula-body" tabindex="-1">פתירה בעזרת המשולש</button></nav><p class="formula-intro">החלק העליון במשולש הוא מכפלת שני החלקים התחתונים. כדי למצוא חלק תחתון, מחלקים את העליון בחלק התחתון הידוע. בלשונית עזרה מופיעים נתוני התרגיל ואפשר לענות במשולש המתאים.</p><div id="formula-body" role="tabpanel" aria-labelledby="formula-tab-reference" tabindex="0"></div><section id="manual-keypad" class="manual-keypad" aria-label="מקלדת מספרים X וסימן שאלה" hidden><div class="manual-keypad-header"><span class="small muted">מקלדת נתונים</span><bdi id="manual-keypad-value"></bdi></div><div class="manual-keypad-grid"><button type="button" data-manual-key="7" aria-label="7">7</button><button type="button" data-manual-key="8" aria-label="8">8</button><button type="button" data-manual-key="9" aria-label="9">9</button><button type="button" data-manual-key="X" aria-label="ערך שלא התבקש לחשב">X</button><button type="button" data-manual-key="4" aria-label="4">4</button><button type="button" data-manual-key="5" aria-label="5">5</button><button type="button" data-manual-key="6" aria-label="6">6</button><button type="button" data-manual-key="?" aria-label="נעלם">?</button><button type="button" data-manual-key="1" aria-label="1">1</button><button type="button" data-manual-key="2" aria-label="2">2</button><button type="button" data-manual-key="3" aria-label="3">3</button><button type="button" data-manual-key="backspace" aria-label="מחיקת תו">⌫</button><button type="button" data-manual-key="0" aria-label="0">0</button><button type="button" data-manual-key="." aria-label="נקודה עשרונית">.</button><button type="button" data-manual-key="clear" aria-label="ניקוי השדה">ניקוי</button><button type="button" data-manual-key="enter" aria-label="אישור ומעבר לשדה הבא">✓</button><button type="button" data-manual-key="done" aria-label="סגירת המקלדת">↓</button></div></section></dialog>
<dialog id="diagram-dialog" aria-labelledby="diagram-title"><div class="dialog-head"><h2 id="diagram-title">הגדלת הסכמה</h2><button class="close" data-close-dialog="diagram-dialog" aria-label="סגירת הסכמה המוגדלת">×</button></div><div id="diagram-context"></div><div class="diagram-toolbar" role="group" aria-label="הגדלת הסכמה"><button class="btn secondary tiny" data-diagram-zoom="in" aria-label="הגדלה">+</button><button class="btn secondary tiny" data-diagram-zoom="out" aria-label="הקטנה">−</button><button class="btn soft tiny" data-diagram-zoom="reset">התאמה למסך</button><bdi id="diagram-zoom-label" role="status" aria-live="polite">100%</bdi></div><p class="small muted">אפשר להגדיל באמצעות הכפתורים ולגלול בתוך הסכמה.</p><div class="diagram-viewport" id="diagram-viewport" tabindex="0" role="region" aria-label="סכמה מוגדלת — אפשר לגלול לצדדים ולמעלה ולמטה"><div class="diagram-canvas" id="diagram-canvas"></div></div></dialog>
<dialog id="calculator-dialog" class="calc-dialog" aria-labelledby="calc-title">
  <div class="dialog-head"><h2 id="calc-title">מחשבון</h2><div class="calc-head-actions"><button class="btn secondary tiny" id="calc-settings-toggle" type="button" aria-expanded="false" aria-controls="calc-settings">⚙ הגדרות</button><button class="close" data-close-dialog="calculator-dialog" aria-label="סגירת המחשבון">×</button></div></div>
  <section id="calc-settings" class="calc-settings" aria-label="הגדרות המחשבון" hidden>
    <label for="calc-color">צבע המחשבון <input id="calc-color" type="color" value="#c78b2d" aria-describedby="calc-color-note"></label>
    <p class="small muted" id="calc-color-note">בחרו צבע נוח לעיניים. במצב לילה הרקע נשאר שחור והכפתורים מקבלים גוון כהה מתאים.</p>
    <label for="calc-expression-style">תצוגת הביטוי <select id="calc-expression-style"><option value="math">כתב מתמטי</option><option value="linear">כתיבה בשורה</option></select></label>
    <label for="calc-result-style">תוצאת ברירת מחדל <select id="calc-result-style"><option value="decimal">שבר עשרוני</option><option value="fraction">שבר בכתב מתמטי</option></select></label>
    <label for="calc-rounding"><input id="calc-rounding" type="checkbox" checked> עיגול תוצאה עשרונית — פעיל</label>
    <label for="calc-digits">עד כמה ספרות אחרי הנקודה? <select id="calc-digits"><option value="3">3</option><option value="4">4</option><option value="5">5</option><option value="6">6</option></select></label>
    <p class="small muted">העיגול משנה את התצוגה בלבד. החישוב הבא משתמש בתוצאה המלאה. כשהעיגול כבוי מוצג הדיוק הזמין במחשבון.</p>
    <button class="btn secondary tiny" id="calc-reset-settings" type="button">איפוס הגדרות המחשבון</button>
  </section>
  <div class="calc-layout"><aside id="calc-triangle-reference" class="calc-triangle-reference" aria-labelledby="calc-triangle-title" hidden></aside><div class="calc-main">
    <label class="small muted" for="calc-screen">חיבור, חיסור, כפל, חילוק, סוגריים ושברים</label>
    <input id="calc-screen" class="calc-screen" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" maxlength="160" placeholder="12 ÷ 3" aria-describedby="calc-input-help">
    <div id="calc-expression-preview" class="calc-expression-preview" aria-label="הביטוי בכתב מתמטי"></div>
    <div class="calc-toolbar"><button class="btn secondary tiny" id="calc-fraction" type="button" aria-expanded="false" aria-controls="calc-fraction-editor"><span class="calc-fraction-icon" aria-hidden="true"><span>□</span><span>□</span></span> הכנסת שבר</button><button class="btn secondary tiny" id="calc-format" type="button" aria-label="מעבר בין תוצאה עשרונית לשבר בכתב מתמטי" aria-pressed="false">עשרוני ↔ שבר</button></div>
    <section id="calc-fraction-editor" class="calc-fraction-editor" aria-label="הכנסת שבר לביטוי" hidden>
      <div class="calc-fraction-fields" dir="ltr"><label for="calc-numerator" class="calc-numerator"><span class="small">מונה</span><input id="calc-numerator" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" maxlength="70" placeholder="מונה"></label><label for="calc-denominator"><span class="small">מכנה</span><input id="calc-denominator" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" maxlength="70" placeholder="מכנה"></label></div>
      <div class="calc-fraction-nav"><button class="btn secondary tiny" type="button" data-calc-part="calc-numerator">מונה ↑</button><button class="btn secondary tiny" type="button" data-calc-part="calc-denominator">מכנה ↓</button></div>
      <div class="calc-fraction-nav"><button class="btn tiny" id="calc-insert-fraction" type="button">הוספה לביטוי</button><button class="btn secondary tiny" id="calc-cancel-fraction" type="button">ביטול</button></div>
    </section>
    <div id="calc-result" class="calc-result" role="status" aria-live="polite"></div><p id="calc-result-note" class="small muted"></p>
    <div class="calc-grid" id="calc-grid"></div><p id="calc-error" class="feedback error" role="alert"></p>
    <div class="calc-actions"><button class="btn" id="calc-use" disabled>העברה לתשובה</button><button class="btn secondary" id="calc-clear">ניקוי</button></div><button class="text-btn" data-open-formulas>דף נוסחאות △</button>
    <p class="small muted" id="calc-input-help" style="margin-top:12px;margin-bottom:0">מספר ליד סוגריים פירושו כפל, למשל <bdi>6(2+3)</bdi>. כפתור הכנסת שבר והמעבר עשרוני ↔ שבר זמינים בכל סגנון תצוגה.</p>
  </div></div>
</dialog>
<dialog id="guide-dialog" class="guide-dialog" aria-labelledby="guide-title" aria-describedby="guide-intro">
  <div class="dialog-head"><h2 id="guide-title">מדריך שימוש באתר</h2><button type="button" class="close" data-close-dialog="guide-dialog" aria-label="סגירת מדריך השימוש">×</button></div>
  <p class="guide-intro" id="guide-intro">לומדים ומתרגלים חשמל בקצב שלכם: חוק אום והספק, מעגל טורי ומעגל מקבילי. פתחו נושא במדריך כדי לקרוא את ההוראות.</p>
  <details class="guide-section" open><summary>איך מתחילים לתרגל?</summary><ol>
    <li>בכניסה הראשונה ממלאים פרופיל ומאשרים את תנאי השימוש.</li>
    <li>בוחרים תחום תרגול ורמה: א׳ — מספרים שלמים; ב׳ — עשרוניים; ג׳ — המרות יחידות. בכל רמה יש 10 תרגילים.</li>
    <li>קוראים את הנתונים ואת השאלה של הצעד הנוכחי, ומקלידים בתשובה מספר בלבד, ביחידה שמופיעה ליד השדה.</li>
    <li>לוחצים על בדיקת התשובה. אם יש טעות, אפשר לתקן ולנסות שוב. לאחר תשובה נכונה ממשיכים בכפתור ״הבא״.</li>
  </ol></details>
  <details class="guide-section"><summary>דף הנוסחאות — מה יש בו ואיך משתמשים?</summary><ul>
    <li>אייקון הדף פותח את דף הנוסחאות. בלשונית ״נוסחאות״ מוצגים משולשי חוק אום וההספק, נוסחאות למעגל טורי ומקבילי והסברי היחידות.</li>
    <li>בוחרים נוסחה שיש בה את הנעלם ושני נתונים שכבר ידועים. במשולש: כיסוי המשתנה העליון נותן כפל של שני המשתנים התחתונים; כיסוי משתנה תחתון נותן חילוק של העליון בתחתון שנשאר.</li>
    <li>הסימונים: <bdi>U</bdi> — מתח בוולט; <bdi>I</bdi> — זרם באמפר; <bdi>R</bdi> — התנגדות באוהם; <bdi>P</bdi> — הספק בוואט; <bdi>R<sub>T</sub></bdi> — התנגדות שקולה.</li>
    <li>בלשונית העזרה לתרגיל אפשר לראות את הנתונים שכבר ידועים ולחשב את הנעלם המתאים. נתונים שטרם חושבו אינם נחשפים.</li>
  </ul></details>
  <details class="guide-section"><summary>פתירה בעזרת המשולש</summary><ol>
    <li>לוחצים על אייקון המשולש ליד התשובה, בוחרים משולש מתאים ומציבים בעצמכם את הנתונים במשבצות. במשולש נפתחת מקלדת המספרים של הטלפון רק בלחיצה על שדה. ברשימת הנתונים שבצד משתמשים במקלדת האתר, כולל X וסימן שאלה.</li>
    <li>בחישובי ריבוע, למשל <bdi>I²</bdi>, מציבים את הזרם כפול עצמו. מקפידים על היחידות שמופיעות ליד כל משבצת.</li>
    <li>אפשר לפתוח את המחשבון. הרשימה ״הערכים שהזנת במשולש״ מציגה את ההצבה שלכם כפי שהוקלדה, גם אם נפלה בה טעות.</li>
    <li>לאחר החישוב מעבירים את התוצאה למשולש ולוחצים ״בדוק״. נבדקים גם הנתונים שהצבתם וגם התוצאה. ״הצג סכמה״ מציג את המעגל, הנתונים והנעלם בקצרה.</li>
    <li>בחישוב התנגדות שקולה משתמשים בנוסחת המעגל המתאימה; אין משולש לחישוב הזה.</li>
  </ol></details>
  <details class="guide-section"><summary>מחשבון, רמז ופתרון מוסבר</summary><ul>
    <li>אייקון המחשבון פותח מחשבון עם כפל, חילוק, חיבור, חיסור, סוגריים וריבוע. מקלידים ביטוי, לוחצים <bdi>=</bdi> ואז ״העברה לתשובה״. מתוך המשולש התוצאה מועברת למשבצת הנעלם. מספר הצמוד לסוגריים מזוהה ככפל. כפתור ״הכנסת שבר״ מאפשר למלא מונה ומכנה. הכפתור ״עשרוני ↔ שבר״ מחליף את תצוגת התוצאה לחישוב הנוכחי.</li>
    <li>ב״הגדרות״ במחשבון אפשר לבחור צבע, תצוגת ביטוי ותוצאה, ולהפעיל או לכבות עיגול ל־3–6 ספרות אחרי הנקודה. ההגדרות נשמרות במכשיר. במצב לילה הרקע נשאר שחור והכפתורים מותאמים אליו.</li>
    <li>אייקון המנורה פותח רמז. לחיצה נוספת סוגרת אותו.</li>
    <li>״פתרון מוסבר״ פותח את שלבי החישוב. אפשר לסגור בלחיצה נוספת או ב־× ולפתוח שוב. כשמוצעות דרך א׳ ודרך ב׳, אפשר לעבור ביניהן.</li>
    <li>מעבר עם העכבר או לחיצה ארוכה על אייקון מציגים את שמו. לחיצה רגילה מפעילה את הכלי.</li>
  </ul></details>
  <details class="guide-section"><summary>התקדמות, תרגילים חדשים וסימולטור</summary><ul>
    <li>אייקון הגרף ו״התקדמות אישית״ פותחים את נתוני התרגול שלכם. הפרופיל וההתקדמות נשמרים בדפדפן ובמכשיר הנוכחיים; ניקוי נתוני הדפדפן עלול למחוק אותם.</li>
    <li>אייקון החץ המעגלי ו״איפוס תרגילים״ מאפשרים לקבל סבב חדש, לאחר אישור. הפרופיל וההתקדמות האישית נשמרים.</li>
    <li>בסימולטור אפשר לבחון מעגל מתרגיל או מעגל משלכם ולשנות את מתח המקור. שינוי בסימולטור אינו משנה את תשובות התרגיל.</li>
  </ul></details>
  <details class="guide-section"><summary>נגישות, מצב לילה ופנייה לעומר</summary><ul>
    <li>״שינוי גודל טקסט״ ו״נגישות״ מאפשרים להתאים את התצוגה. בנגישות אפשר לבחור מצב לילה פעיל, כבוי או בהתאם למכשיר; ברירת המחדל היא בהתאם למכשיר.</li>
    <li>״פנייה לעומר״ פותחת שתי אפשרויות: ״משוב ודירוג אפליקציה״ — דירוג כוכבים חובה ומלל לבחירה, שמתפרסמים ב־GitHub; ״הערות״ — הודעה פרטית לעומר.</li>
    <li>אייקון הכוכב פותח את תוצאות הדירוג. אפשר לפתוח אותן גם דרך ״דירוג״ בתחתית האתר.</li>
    <li>במחשב אפשר לנוע באמצעות <bdi>Tab</bdi> ו־<bdi>Shift+Tab</bdi>, ולסגור חלון באמצעות <bdi>Escape</bdi> או כפתור ×.</li>
  </ul></details>
  <div class="guide-actions"><button type="button" class="btn" data-close-dialog="guide-dialog">חזרה לתרגול</button><button type="button" class="btn secondary" data-open-formulas>פתיחת דף הנוסחאות</button></div>
</dialog>
<dialog id="new-course-dialog" class="confirm-dialog" aria-labelledby="new-course-title"><div class="dialog-head"><h2 id="new-course-title">להתחיל סבב חדש?</h2><button class="close" data-close-dialog="new-course-dialog" aria-label="סגירה">×</button></div><p>התרגילים בסבב יוחלפו. ההתקדמות האישית, הגרף, הטבלה והפרופיל שלכם יישמרו.</p><div class="completion-actions"><button class="btn" id="new-course-confirm">כן, תרגילים חדשים</button><button class="btn secondary" data-close-dialog="new-course-dialog">חזרה לתרגול</button></div></dialog>
<dialog id="profile-dialog" class="profile-dialog" aria-labelledby="profile-title"><div class="dialog-head"><h2 id="profile-title">הפרופיל שלי במכשיר הזה</h2><button class="close" id="profile-close" data-close-dialog="profile-dialog" aria-label="סגירת הפרופיל">×</button></div><p class="small muted">בכניסה הראשונה מזינים שם ותאריך לידה ומאשרים את תנאי השימוש. הפרטים וההתקדמות יישמרו בדפדפן הזה; ניקוי נתוני הדפדפן עלול למחוק אותם.</p><form id="profile-form" novalidate><div class="profile-fields"><label for="profile-name">שם<input id="profile-name" aria-describedby="profile-error" type="text" autocomplete="name" maxlength="80" required></label><div class="profile-birth-field"><label for="profile-birth">תאריך לידה</label><div class="birth-input-row"><input id="profile-birth" aria-describedby="profile-birth-help profile-error" type="text" inputmode="numeric" autocomplete="bday" placeholder="DD/MM/YY" maxlength="10" dir="ltr" spellcheck="false" required><label class="birth-calendar" title="בחירה מלוח שנה"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 11h18M7 15h3M14 15h3"/></svg><input id="profile-birth-picker" type="date" aria-label="בחירה מלוח שנה" tabindex="0"></label></div><p class="small muted birth-help" id="profile-birth-help">יום/חודש/שנה · הלוכסנים נוספים אוטומטית. אפשר להקליד שנה בשתי ספרות, למשל 92 עבור 1992.</p></div></div><details class="terms-document" id="profile-terms"><summary>תנאי שימוש ופרטיות — לקריאה לפני האישור</summary><div data-terms-document></div></details><label class="consent-row" for="profile-consent"><input id="profile-consent" aria-describedby="profile-error" type="checkbox" required>אני מסכים/ה לתנאי השימוש ולשמירת הפרופיל ונתוני התרגול באופן מקומי במכשיר הזה.</label><div id="profile-error" class="feedback error" role="alert"></div><button class="btn" type="submit">שמירה ותחילת תרגול</button></form><details class="profile-accessibility"><summary>התאמות נגישות לפני תחילת התרגול</summary><div id="profile-accessibility-controls"></div></details></dialog>
<dialog id="terms-dialog" aria-labelledby="terms-title"><div class="dialog-head"><h2 id="terms-title">תנאי שימוש ופרטיות</h2><button class="close" data-close-dialog="terms-dialog" aria-label="סגירת תנאי השימוש">×</button></div><div data-terms-document></div></dialog>
<dialog id="accessibility-dialog" class="accessibility-dialog" aria-labelledby="accessibility-title"><div class="dialog-head"><h2 id="accessibility-title">נגישות</h2><button class="close" data-close-dialog="accessibility-dialog" aria-label="סגירת הנגישות">×</button></div><div id="accessibility-controls"></div><details class="terms-document"><summary>הצהרת נגישות</summary><p>באתר יש תמיכה בניווט במקלדת, סימון מיקוד, תוויות לשדות, הודעות שגיאה כתובות, הגדלת טקסט, ניגודיות מוגברת והפחתת תנועה. התרשימים והגרף מלווים בתיאור ובנתונים כתובים.</p><p>אפשר לנוע בין שדות וכפתורים באמצעות Tab ו־Shift+Tab, לבחור לשונית באמצעות החצים ולסגור חלון באמצעות Escape. הסימולטור כולל מקרא וכיתוב כך שהמידע אינו תלוי בצבע בלבד.</p><p>מתבצעים שיפורים שוטפים. לבדיקת עמידה מלאה בתקן נדרשת הערכת נגישות מקיפה. לדיווח על קושי אפשר לפנות למפעיל האתר בערוץ שדרכו התקבל הקישור, ולציין את המכשיר, הדפדפן והפעולה שבה נתקלים בקושי.</p></details></dialog>
<script>
const DC = (() => {
  const kinds = ['ohm', 'series', 'parallel'];
  const round = n => Math.round((n + Number.EPSILON) * 100) / 100;
  const fmt = n => String(round(n));
  function random(seed) {
    let a = seed >>> 0;
    return () => {
      a += 0x6D2B79F5;
      let t = a;
      t = Math.imul(t ^ t >>> 15, t | 1);
      t ^= t + Math.imul(t ^ t >>> 7, t | 61);
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  const pick = (rng, list) => list[Math.floor(rng() * list.length)];
  const integer = (rng, lo, hi) => lo + Math.floor(rng() * (hi - lo + 1));
  const levelNames = ['מספרים שלמים', 'מספרים עשרוניים', 'קילו ומגה־אוהם'];
  function shuffle(rng, values) {
    const result = values.slice();
    for (let i = result.length - 1; i > 0; i--) {
      const j = integer(rng, 0, i);
      [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
  }
  function withUnits(q) {
    const scale = q.level === 2 ? (q.index % 2 ? 1e6 : 1e3) : 1;
    q.resistanceScale = scale;
    q.units = scale === 1e6 ? {U:'V',R:'MΩ',I:'μA',P:'μW'}
      : scale === 1e3 ? {U:'V',R:'kΩ',I:'mA',P:'mW'} : {U:'V',R:'Ω',I:'A',P:'W'};
    // Answers and substitutions use one coherent unit system. The circuit model uses SI.
    if (scale !== 1) {
      q.resistances = q.resistances.map(value => value * scale);
      for (const key of Object.keys(q.givens)) {
        if (key[0] === 'R') q.givens[key] *= scale;
        if (key[0] === 'I' || key[0] === 'P') q.givens[key] /= scale;
      }
      for (const item of q.steps) {
        item.unit = q.units[item.key === 'Req' ? 'R' : item.key[0]];
        item.explanation = item.explanation
          .replace('אמפר (A)',scale===1e6?'מיקרואמפר (μA)':'מיליאמפר (mA)')
          .replace('אוהם (Ω)',scale===1e6?'מגה־אוהם (MΩ)':'קילו־אוהם (kΩ)')
          .replace('ואט (W)',scale===1e6?'מיקרוואט (μW)':'מיליוואט (mW)');
      }
    }
    return q;
  }
  function physics(kind, voltage, resistances) {
    const req = kind === 'parallel' ? 1 / resistances.reduce((s, r) => s + 1 / r, 0)
      : resistances.reduce((s, r) => s + r, 0);
    const total = voltage / req;
    const currents = resistances.map(r => kind === 'parallel' ? voltage / r : total);
    const drops = resistances.map((r, i) => currents[i] * r);
    const powers = resistances.map((r, i) => currents[i] * currents[i] * r);
    return { req, total, currents, drops, powers, power: voltage * total };
  }
  function step(key, label, unit, value, formula, substitution, hint, explanation) {
    return { key, label, unit, value, formula, substitution, hint, explanation };
  }
  function ohm(rng, level, index, oneAmp = false, inputs = null, powerResistance = false) {
    const r = inputs ? inputs.resistances[0] : level ? integer(rng, 1 + index, 10 + index * 3) + .5
      : integer(rng, 2 + index, 8 + index * 4);
    // Level A uses one-amp currents in 20% of slots; other currents are 2–12.
    // Decimal levels use non-integer displayed currents from 2.1 to 11.9.
    // withUnits converts level C to the corresponding mA/μA unit system.
    const i = inputs ? inputs.voltage / r : level ? integer(rng, 2, 11) + integer(rng, 1, 9) / 10
      : oneAmp ? 1 : integer(rng, 2, 12);
    const u = inputs ? inputs.voltage : r * i, p = u * i;
    const fields = {
      I: step('I', 'הזרם במעגל', 'A', i, 'I = U ÷ R', `${fmt(u)} ÷ ${fmt(r)}`, 'כדי למצוא זרם, מחלקים את המתח בהתנגדות.', 'יחידת הזרם היא אמפר (A).'),
      U: step('U', 'מתח המקור', 'V', u, 'U = I × R', `${fmt(i)} × ${fmt(r)}`, 'כדי למצוא מתח, כופלים את הזרם בהתנגדות.', 'יחידת המתח היא וולט (V).'),
      R: step('R', 'התנגדות הנגד', 'Ω', r, 'R = U ÷ I', `${fmt(u)} ÷ ${fmt(i)}`, 'כדי למצוא התנגדות, מחלקים את המתח בזרם.', 'יחידת ההתנגדות היא אוהם (Ω).'),
      P: step('P', 'ההספק החשמלי', 'W', p, 'P = U × I', `${fmt(u)} × ${fmt(i)}`, 'הספק הוא המתח כפול הזרם.', 'יחידת ההספק היא ואט (W).'),
    };
    let givens, steps, title;
    const variant = index % 5;
    if (variant === 0) { givens = { U: u, R: r }; steps = [fields.I]; title = 'מוצאים את הזרם'; }
    if (variant === 1) { givens = { I: i, R: r }; steps = [fields.U]; title = 'מוצאים את המתח'; }
    if (variant === 2) { givens = { U: u, I: i }; steps = [fields.R]; title = 'מוצאים את ההתנגדות'; }
    if (variant === 3) { givens = { U: u, I: i }; steps = [fields.P]; title = 'מחשבים הספק'; }
    if (variant === 4) {
      givens = { U: u, P: p }; title = 'מההספק אל הזרם וההתנגדות';
      steps = [step('I', 'הזרם במעגל', 'A', i, 'I = P ÷ U', `${fmt(p)} ÷ ${fmt(u)}`,
        'מתחילים בנוסחת ההספק: כדי לבודד את הזרם, מחלקים את ההספק במתח.', 'אחרי מציאת הזרם אפשר להשתמש בחוק אום.'), fields.R];
    }
    if(powerResistance){
      givens={U:u,P:p};title='התנגדות מתוך מתח והספק';
      steps=[step('R','התנגדות הנגד','Ω',r,'R = U² ÷ P',`${fmt(u)}² ÷ ${fmt(p)}`,'כדי למצוא התנגדות מתוך מתח והספק, מעלים את המתח בריבוע ומחלקים בהספק.','יחידת ההתנגדות היא אוהם (Ω).')];
    }
    return withUnits({ kind: 'ohm', level, index, title, powerResistance, voltage: u, resistances: [r], lamps: [false], givens, steps });
  }
  function circuit(rng, kind, level, index, equal = false, inputs = null, branchCount = null) {
    let resistances, voltage;
    if (inputs) {
      ({resistances, voltage} = inputs);
    } else if (kind === 'series') {
      const count = index < 5 ? 2 : 3;
      resistances = Array.from({ length: count }, () => integer(rng, 2 + index, 7 + index * 4) + (level ? .5 : 0));
      const current = level ? pick(rng, [.2, .4, .6, .8, 1.2, 1.4, 1.6]) : integer(rng, 1, 2 + Math.floor(index / 2));
      voltage = resistances.reduce((s, r) => s + r, 0) * current;
    } else {
      const count = branchCount ?? (index < 5 ? 2 : 3);
      const k = integer(rng, 2 + index, 24 + index * 4) + (level ? .5 : 0);
      const m = level ? integer(rng, 1, 8) / 2 : integer(rng, 1, 5 + Math.floor(index / 3));
      if (equal) {
        // n equal resistors n*k give Req=k and integer branch currents for level A.
        resistances = Array(count).fill(count * k);
        voltage = count * k * m;
      } else {
        // Two branches: 1/(3k)+1/(6k)=1/(2k), U=6km -> I1=2m, I2=m.
        // Three branches: 1/(2k)+1/(3k)+1/(6k)=1/k, U=6km -> I=[3m,2m,m].
        resistances = shuffle(rng, (count === 2 ? [3, 6] : [2, 3, 6]).map(r => r * k));
        voltage = 6 * k * m;
      }
    }
    const model = physics(kind, voltage, resistances);
    const lamps = resistances.map((r, j) => (index === 1 || index === 3) ? j === 0 || j === resistances.length - 1 : index === 4 && j === 1);
    const givens = { U: voltage };
    resistances.forEach((r, j) => { givens['R' + (j + 1)] = r; });
    const identical = resistances.every(r => Math.abs(r - resistances[0]) < 1e-8);
    const reqFormula = kind === 'series' ? 'R_eq = R1 + R2' + (resistances.length === 3 ? ' + R3' : '')
      : identical ? `R_eq = R ÷ ${resistances.length}`
      : resistances.length === 2 ? 'R_eq = (R1 × R2) ÷ (R1 + R2)' : 'R_eq = 1 ÷ (1/R1 + 1/R2 + 1/R3)';
    const reqSub = kind === 'series' ? resistances.map(fmt).join(' + ')
      : identical ? `${fmt(resistances[0])} ÷ ${resistances.length}`
      : resistances.length === 2 ? `(${fmt(resistances[0])} × ${fmt(resistances[1])}) ÷ (${fmt(resistances[0])} + ${fmt(resistances[1])})`
      : `1 ÷ (1/${fmt(resistances[0])} + 1/${fmt(resistances[1])} + 1/${fmt(resistances[2])})`;
    const steps = [step('Req', 'ההתנגדות השקולה', 'Ω', model.req, reqFormula, reqSub,
      kind === 'series' ? 'בטור מחברים את כל ההתנגדויות.' : identical ? 'במקביל, כשכל הנגדים זהים, מחלקים את התנגדות הנגד במספר הענפים.' : resistances.length === 2 ? 'בשני נגדים במקביל: כופלים את ההתנגדויות ומחלקים בסכומן.' : 'בשלושה ענפים מחברים את ההופכיים של ההתנגדויות, ואז מחשבים את ההופכי של הסכום.',
      kind === 'series' ? 'בטור הנגד השקול גדול מכל נגד בנפרד.' : 'במקביל הנגד השקול קטן מהנגד הקטן ביותר.'),
      step('I', 'הזרם הכולל מהמקור', 'A', model.total, 'I_total = U ÷ R_eq', `${fmt(voltage)} ÷ ${fmt(model.req)}`,
        'מחליפים את כל המעגל בנגד השקול ומשתמשים בחוק אום.', kind === 'series' ? 'בטור אותו זרם עובר בכל הרכיבים.' : 'הזרם הכולל מתפצל לענפים. סכום זרמי הענפים שווה לזרם המקור.')];
    if (kind === 'series') {
      const first = index % resistances.length, second = (first + 1) % resistances.length;
      steps.push(step('U' + (first + 1), `מפל המתח על R${first + 1}`, 'V', model.drops[first], `U${first + 1} = I × R${first + 1}`,
        `${fmt(model.total)} × ${fmt(resistances[first])}`, 'בטור משתמשים בזרם הכולל ובהתנגדות של הרכיב המסוים.', 'סכום מפלי המתח על כל הרכיבים שווה למתח המקור.'));
      for (const j of [first, second]) steps.push(step('P' + (j + 1), `ההספק על R${j + 1}`, 'W', model.powers[j], `P${j + 1} = I × I × R${j + 1}`,
        `${fmt(model.total)} × ${fmt(model.total)} × ${fmt(resistances[j])}`, 'בטור הזרם זהה בכל הרכיבים. כופלים אותו בעצמו ובערך הנגד המבוקש.', 'אפשר גם לחשב הספק באמצעות מפל המתח על אותו רכיב כפול הזרם.'));
    } else {
      resistances.forEach((r, j) => steps.push(step('I' + (j + 1), `הזרם בענף ${j + 1}`, 'A', model.currents[j], `I${j + 1} = U ÷ R${j + 1}`,
        `${fmt(voltage)} ÷ ${fmt(r)}`, 'במקביל כל ענף מחובר לאותו מתח מקור.', 'ענף עם התנגדות קטנה יותר מעביר זרם גדול יותר.')));
      resistances.forEach((r, j) => steps.push(step('P' + (j + 1), `ההספק בענף ${j + 1}`, 'W', model.powers[j], `P${j + 1} = U × I${j + 1}`,
        `${fmt(voltage)} × ${fmt(model.currents[j])}`, 'משתמשים במתח המקור ובזרם של הענף המבוקש.', 'ההספק הכולל שווה לסכום ההספקים בענפים.')));
    }
    return withUnits({ kind, level, index, title: kind === 'series' ? `מעגל טורי עם ${resistances.length} רכיבים` : `מעגל מקבילי עם ${resistances.length} ענפים`,
      voltage, resistances, lamps, givens, steps });
  }
  function decimalInputs(rng, kind, index, equal, branchCount = null) {
    // Keep every given resistance and source voltage whole. Given Ohm currents
    // and powers also have exact finite decimals, so displayed givens are exact.
    const divisor = pick(rng, [2, 4, 5, 10]);
    if (kind === 'ohm') {
      const resistance = divisor * integer(rng, 1 + Math.floor(index / 4), 4 + Math.floor(index / 2));
      const numerator = pick(rng, Array.from({length:10 * divisor - 1}, (_,i) => 2 * divisor + 1 + i).filter(n => n % divisor));
      return {resistances:[resistance], voltage:resistance / divisor * numerator};
    }
    const count = kind==='parallel'&&branchCount ? branchCount : (index < 5 ? 2 : 3);
    if (kind === 'series') {
      const resistances = Array.from({length:count}, () => integer(rng, 2 + index, 7 + index * 4));
      const sum = resistances.reduce((a,b) => a + b, 0);
      resistances[count - 1] += (divisor - sum % divisor) % divisor;
      const req = resistances.reduce((a,b) => a + b, 0);
      const numerator = pick(rng, Array.from({length:2 * divisor - 1}, (_,i) => i + 1).filter(n => n % divisor));
      return {resistances, voltage:req / divisor * numerator};
    }
    const voltage = pick(rng, Array.from({length:19 + index * 4}, (_,i) => 12 + index * 2 + i).filter(u => u % 5));
    const nonInteger = value => Math.abs(value - Math.round(value)) > 1e-7;
    const pool = [4,5,8,10,16,20,25,40,50,80,100].filter(r => voltage * 100 % r === 0 && voltage % r !== 0);
    const candidates = [];
    const consider = resistances => {
      const model = physics('parallel', voltage, resistances);
      if (nonInteger(round(model.req)) && nonInteger(round(model.total))) candidates.push(resistances);
    };
    if (equal) pool.forEach(r => consider(Array(count).fill(r)));
    else {
      const collect = (start, values) => {
        if (values.length === count) { consider(values); return; }
        for (let j = start; j < pool.length; j++) collect(j + 1, [...values, pool[j]]);
      };
      collect(0, []);
    }
    // The pool always contains 5, 10 and 25; U is not divisible by 5.
    // Thus equal and distinct candidates exist for both branch counts.
    return {resistances:shuffle(rng, pick(rng, candidates)), voltage};
  }
  function course(seed, previous = [], profile = 'hvac') {
    const rng = random(seed), seen = new Set(previous), result = {};
    for (const kind of kinds) {
      result[kind] = Array.from({ length: profile==='mobile'?2:3 }, (_, level) => {
        const count=profile==='hvac'&&kind==='ohm'&&level<2?20:10;
        const powerSlots=profile==='hvac'&&kind==='ohm'&&level<2?shuffle(rng,Array.from({length:count},(_,i)=>i<9)):[];
        // Decide the exact ratio once per level, outside the duplicate-retry loop.
        const equalSlots = kind === 'parallel' ? shuffle(rng, [true,true,true,false,false,false,false,false,false,false]) : [];
        const oneAmpSlots = kind === 'ohm' && level === 0 ? shuffle(rng, Array.from({length:count},(_,i)=>i<count/5)) : [];
        return Array.from({ length: count }, (_, index) => {
          let q;
          for (let attempt = 0; attempt < 400; attempt++) {
            q = kind === 'ohm' ? ohm(rng, level, index, oneAmpSlots[index],null,powerSlots[index]===true) : circuit(rng, kind, level, index, equalSlots[index],null,profile==='mobile'?2:null);
            const signatureR = kind === 'parallel' ? q.resistances.slice().sort((a,b)=>a-b) : q.resistances;
            q.signature = JSON.stringify([kind, level, q.voltage, signatureR, Object.keys(q.givens)]);
            const hasDecimal = Object.values(q.givens).some(v => Math.abs(v - Math.round(v)) > 1e-7);
            if (!seen.has(q.signature) && (level !== 1 || hasDecimal)) break;
          }
          seen.add(q.signature);
          return q;
        });
      });
    }
    // Preserve the original random stream for levels A/C and old saved courses.
    // Replace only level B using an independent deterministic random stream.
    const decimalRng = random((seed ^ 0xBDEC1A1) >>> 0);
    for (const kind of kinds) {
      const equalSlots = result[kind][1].map(q => q.resistances.every(r => r === q.resistances[0]));
      result[kind][1] = result[kind][1].map((old, index) => {
        let q;
        for (let attempt = 0; attempt < 400; attempt++) {
          const inputs = decimalInputs(decimalRng, kind, index, equalSlots[index],profile==='mobile'?2:null);
          q = kind === 'ohm' ? ohm(decimalRng, 1, index, false, inputs,old.powerResistance) : circuit(decimalRng, kind, 1, index, equalSlots[index], inputs,profile==='mobile'?2:null);
          const signatureR = kind === 'parallel' ? q.resistances.slice().sort((a,b) => a-b) : q.resistances;
          q.signature = JSON.stringify([kind, 1, q.voltage, signatureR, Object.keys(q.givens)]);
          if (!seen.has(q.signature)) break;
        }
        seen.add(q.signature);
        return q;
      });
    }
    return result;
  }
  function accepted(text, value) {
    const cleaned = String(text).trim().replace(',', '.');
    if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(cleaned)) return false;
    const answer = Number(cleaned);
    return Number.isFinite(answer) && Math.abs(answer - round(value)) < 1e-7;
  }
  // Parse arithmetic without eval. Keep exact rational values for fraction display
  // and decimal rounding; the numeric value remains available to the exercise.
  function evaluateCalculation(text) {
    const input = String(text).replace(/,/g,'.').replace(/×/g,'*').replace(/÷/g,'/').replace(/−/g,'-').replace(/\s/g,'');
    if (!input || input.length > 160) throw Error(input ? 'התרגיל ארוך מדי.' : 'יש להזין תרגיל עם מספרים ופעולות חשבון.');
    let cursor = 0;
    const abs = n => n < 0n ? -n : n;
    function rational(n,d) {
      if (d === 0n) throw Error('אי אפשר לחלק באפס.');
      if (d < 0n) { n=-n; d=-d; }
      let a=abs(n),b=d;
      while (b) { const rest=a%b; a=b; b=rest; }
      n/=a; d/=a;
      return n.toString().length+d.toString().length <= 4096 ? {n,d} : null;
    }
    function decimalFraction(token) {
      const [mantissa,power='0']=token.toLowerCase().split('e');
      const decimals=(mantissa.split('.')[1]||'').length, scale=decimals-Number(power);
      if (Math.abs(scale)>400) return null;
      const digits=BigInt(mantissa.replace('.',''));
      return scale>=0 ? rational(digits,10n**BigInt(scale)) : rational(digits*10n**BigInt(-scale),1n);
    }
    function result(value,exact,tree) {
      if(exact) {
        const n=Number(exact.n),d=Number(exact.d);
        if(Number.isFinite(n)&&Number.isFinite(d))value=n/d;
      }
      if(!Number.isFinite(value))throw Error('התוצאה גדולה מדי. יש לבדוק את המספרים.');
      return {value:Object.is(value,-0)?0:value,exact,tree};
    }
    function combine(left,right,op,implicit=false) {
      if(op==='/'&&(right.exact ? right.exact.n===0n : right.value===0))throw Error('אי אפשר לחלק באפס.');
      let exact=null;
      if(left.exact&&right.exact) {
        const {n:a,d:b}=left.exact,{n:c,d:d}=right.exact;
        exact=op==='+'?rational(a*d+c*b,b*d):op==='-'?rational(a*d-c*b,b*d):op==='*'?rational(a*c,b*d):rational(a*d,b*c);
      }
      const value=op==='+'?left.value+right.value:op==='-'?left.value-right.value:op==='*'?left.value*right.value:left.value/right.value;
      return result(value,exact,{kind:'binary',op,implicit,left:left.tree,right:right.tree});
    }
    function expression() {
      let value=product();
      while(input[cursor]==='+'||input[cursor]==='-') { const op=input[cursor++]; value=combine(value,product(),op); }
      return value;
    }
    function product() {
      let value=factor();
      while(cursor<input.length) {
        const explicit=input[cursor]==='*'||input[cursor]==='/';
        const implicit=input[cursor]==='('||(/[)²]/.test(input[cursor-1]||'')&&/[0-9.]/.test(input[cursor]||''));
        if(!explicit&&!implicit)break;
        const op=explicit?input[cursor++]:'*';
        value=combine(value,factor(),op,!explicit);
      }
      return value;
    }
    function factor() {
      if(input[cursor]==='+'||input[cursor]==='-') {
        const op=input[cursor++],child=factor();
        return result(op==='-'?-child.value:child.value,child.exact?{n:op==='-'?-child.exact.n:child.exact.n,d:child.exact.d}:null,{kind:'unary',op,child:child.tree});
      }
      let value;
      if(input[cursor]==='(') {
        cursor++; value=expression();
        if(input[cursor++]!==')')throw Error('יש לסגור את הסוגריים.');
        value={...value,tree:{kind:'group',child:value.tree}};
      } else {
        const match=/^(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?/.exec(input.slice(cursor));
        if(!match)throw Error('יש להזין תרגיל עם מספרים ופעולות חשבון.');
        cursor+=match[0].length;
        value=result(Number(match[0]),decimalFraction(match[0]),{kind:'number',text:match[0]});
      }
      while(input[cursor]==='²') {
        cursor++;
        value=result(value.value*value.value,value.exact?rational(value.exact.n*value.exact.n,value.exact.d*value.exact.d):null,{kind:'square',child:value.tree});
      }
      return value;
    }
    const value=expression();
    if(cursor!==input.length)throw Error('יש לבדוק את התרגיל שהוקלד.');
    return value;
  }
  function calculate(text) { return evaluateCalculation(text).value; }
  return { kinds, levelNames, round, fmt, physics, course, accepted, calculate, evaluateCalculation };
})();

function circuitSVG(q, options = {}) {
  const complete = options.complete === true;
  const palette = complete ? {text:'#ffffff',wire:'#ffffff',surface:'#000000',current:'#ff6565',voltage:'#65e680',power:'#ffffff'} : {text:'var(--diagram-ink,#203c47)',wire:'var(--diagram-wire,#687e84)',surface:'var(--diagram-surface,#fffefa)',current:'var(--diagram-current,#159485)',voltage:'var(--diagram-ink,#203c47)',power:'var(--diagram-power,#956122)'};
  const voltage = options.voltage ?? q.voltage;
  const moving = complete && options.animate !== false && voltage > 0;
  const model = DC.physics(q.kind, voltage, q.resistances);
  const baseline = DC.physics(q.kind, q.voltage, q.resistances);
  const referencePower = baseline.powers.reduce((largest,power)=>Math.max(largest,power),0);
  const parallel = q.kind === 'parallel';
  const count = q.resistances.length;
  const extended = count > 3, spacing = complete&&parallel ? 280 : 210;
  const width = extended ? 240+count*spacing : complete&&parallel&&count===3 ? 1100 : complete&&parallel&&count===2 ? 940 : 820;
  const xs = extended ? Array.from({length:count},(_,i)=>280+i*spacing) : parallel ? (count === 1 ? [450] : count === 2 ? [350, complete?670:610] : complete ? [300,580,860] : [280,475,670])
    : count === 1 ? [450] : count === 2 ? [330, 600] : [260, 450, 640];
  const right = extended ? xs.at(-1)+90 : 735;
  const number = complete ? CoursePractice.simulationNumber : DC.fmt;
  const quantityValue = (key,value) => complete ? simulatorQuantity(q,key,value) : quantity(q,key,value);
  const parts = [];
  const text = (x, y, value, size = 17, anchor = 'middle', color = palette.text) =>
    `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" fill="${color}" direction="ltr">${value}</text>`;
  const wire = d => `<path d="${d}" fill="none" stroke="${palette.wire}" stroke-width="3" stroke-linecap="round"/>`;
  const flow = (d, current) => `<path d="${d}" fill="none" stroke="${palette.current}" stroke-width="4" stroke-dasharray="7 20" class="sim-current-flow${moving ? ' flow' : ''}" data-current="${current}" style="${moving ? `animation-duration:${Math.max(.65, 3.2 / (1 + current * .35))}s` : 'animation:none'}" opacity="${voltage > 0 ? .9 : 0}"/>`;
  const arrow = (x, y, direction) => {
    const coordinates = direction === 'right' ? `${x - 7},${y - 5} ${x + 6},${y} ${x - 7},${y + 5}`
      : direction === 'down' ? `${x - 5},${y - 7} ${x},${y + 6} ${x + 5},${y - 7}`
      : `${x + 7},${y - 5} ${x - 6},${y} ${x + 7},${y + 5}`;
    return `<polygon points="${coordinates}" fill="${palette.current}"/>`;
  };
  if (parallel) {
    const end=xs[count-1];
    parts.push(wire(`M85 184 L85 100 L${end} 100`), wire(`M85 246 L85 330 L${end} 330`));
    xs.forEach(x => parts.push(wire(`M${x} 100 L${x} 330`)));
    if (complete) {
      parts.push(flow(`M85 184V100H${xs[0]}`,model.total),flow(`M${xs[0]} 330H85V246`,model.total));
      xs.forEach((x,j)=>{
        parts.push(flow(`M${x} 100V330`,model.currents[j]));
        if(j>0){const remaining=model.currents.slice(j).reduce((sum,i)=>sum+i,0);parts.push(flow(`M${xs[j-1]} 100H${x}`,remaining),flow(`M${x} 330H${xs[j-1]}`,remaining));}
      });
      parts.push(text(420,354,`I_T = ${quantityValue('I',model.total)}`,16,'middle',palette.current));
      if (voltage > 0) {
        parts.push(arrow(175, 100, 'right'), arrow(185, 330, 'left'));
      }
    }
    xs.forEach(x => parts.push(`<circle cx="${x}" cy="100" r="4" fill="${palette.wire}"/><circle cx="${x}" cy="330" r="4" fill="${palette.wire}"/>`));
  } else {
    const path = `M85 184 L85 100 L${right} 100 L${right} 330 L85 330 L85 246`;
    parts.push(wire(path));
    if (complete) {
      parts.push(flow(path, model.total));
      if (voltage > 0) parts.push(arrow(166, 100, 'right'), arrow(right, 214, 'down'), arrow((85+right)/2, 330, 'left'), text((85+right)/2, 312, `I = ${quantityValue('I',model.total)}`, 16, 'middle', palette.current));
    }
  }
  q.resistances.forEach((r, j) => {
    const x = xs[j], y = parallel ? 215 : 100;
    const known = complete || q.kind !== 'ohm' || Object.hasOwn(q.givens, 'R');
    const resistance = known ? quantityValue('R',r) : `? ${q.units?.R??'Ω'}`;
    if (q.lamps[j]) {
      const brightness = complete && voltage > 0 ? Math.min(1, model.powers[j] / (referencePower * 1.4)) : 0;
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="43" fill="#ffffff" opacity="${brightness * .32}"/>`);
      parts.push(`<circle cx="${x}" cy="${y}" r="25" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="21" fill="#ffffff" opacity="${brightness * .15}"/>`);
      parts.push(`<path d="M${x - 16} ${y - 16} L${x + 16} ${y + 16} M${x + 16} ${y - 16} L${x - 16} ${y + 16}" stroke="${palette.wire}" stroke-width="2"/>`);
    } else {
      parts.push(`<rect x="${x - (parallel ? 17 : 31)}" y="${y - (parallel ? 30 : 17)}" width="${parallel ? 34 : 62}" height="${parallel ? 60 : 34}" rx="2" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
    }
    if (complete) {
      parts.push(CoursePractice.simulationAnnotations({id:'R'+(j+1),x,y,vertical:parallel,r:displayValue(q,'R',r),current:displayValue(q,'I',model.currents[j]),drop:model.drops[j],resistanceUnit:q.units?.R??'Ω',currentUnit:q.units?.I??'A'}));
      parts.push(parallel ? text(x+35,y+57,`P${j+1} = ${quantityValue('P',model.powers[j])}`,13,'start',palette.power) : text(x,177,`P${j+1} = ${quantityValue('P',model.powers[j])}`,14,'middle',palette.power));
    } else if (parallel) {
      parts.push(text(x+35,y-10,`R${j+1}`,16,'start'),text(x+35,y+14,resistance,16,'start'));
    } else parts.push(text(x,53,`R${j+1} = ${resistance}`,17));
  });
  parts.push(`<circle cx="85" cy="215" r="31" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
  parts.push(text(85, 204, '+', 19), text(85, 223, 'DC', 14), text(85, 239, '−', 18));
  const knownVoltage = complete || Object.hasOwn(q.givens, 'U');
  parts.push(text(138, 222, `U = ${knownVoltage ? number(voltage) : '?'} V`, 16, 'start', complete ? palette.voltage : palette.text));
  const title = `${q.kind === 'parallel' ? 'מעגל מקבילי' : q.kind === 'series' ? 'מעגל טורי' : 'מעגל DC'} עם ${count} רכיבים`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} 365" role="img" aria-label="${title}" dir="ltr"${complete ? ` style="background:#000000${extended ? ';width:'+width+'px;max-width:none' : ''}"` : ''}><title>${title}</title><desc>${complete ? `מתח המקור ${number(voltage)} וולט. זרם כולל ${quantityValue('I',model.total)}. זרם מסומן באדום ומפלי מתח בירוק; ראש חץ המתח פונה לפלוס, נגד כיוון הזרם. הערכים כתובים ליד הרכיבים.` : 'סכמה של נתוני התרגיל. מלבן הוא נגד ועיגול עם X הוא נורה.'}</desc>${parts.join('')}</svg>`;
}


function customCircuitSVG(q,options={}) { return circuitSVG(q,options); }

const $ = id => document.getElementById(id);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const names = { ohm: 'חוק אום והספק', series: 'מעגל טורי', parallel: 'מעגל מקבילי' };
const letters = ['א׳', 'ב׳', 'ג׳'];
const units = { U: 'V', I: 'A', R: 'Ω', P: 'W' };
function displayValue(q,key,value) {
  const scale=q.resistanceScale??1,kind=key==='Req'?'R':key[0];
  return kind==='R'?value/scale:kind==='I'||kind==='P'?value*scale:value;
}
function physicalValue(q,key,value) {
  const scale=q.resistanceScale??1,kind=key==='Req'?'R':key[0];
  return kind==='R'?value*scale:kind==='I'||kind==='P'?value/scale:value;
}
function quantity(q,key,value) { return `${DC.fmt(displayValue(q,key,value))} ${(q.units??units)[key==='Req'?'R':key[0]]}`; }
function unitNote(q=currentQuestion()) {
  const scale=q.resistanceScale??1;if(scale===1)return '';
  const mega=scale===1e6;
  return `<div class="unit-note"><strong>יחידות ברמה ג׳</strong><br>${bdi('1 kΩ = 1,000 Ω')} · ${bdi('1 MΩ = 1,000 kΩ = 1,000,000 Ω')}<br>בתרגיל הזה משתמשים ב־${bdi(mega?'MΩ, μA, μW':'kΩ, mA, mW')} לצד וולט. ${bdi(mega?'1 μA = 0.000001 A':'1 mA = 0.001 A')}; ${bdi(mega?'1 μW = 0.000001 W':'1 mW = 0.001 W')}. אלה יחידות תואמות לנוסחאות: ${bdi(mega?'V = μA × MΩ':'V = mA × kΩ')}. הקלידו את התשובה ביחידה שמופיעה ליד השדה.</div>`;
}
function slotUnit(slot,q=currentQuestion()) { return slot.key==='I2'?`${q.units?.I??'A'} × ${q.units?.I??'A'}`:slot.key==='U2'?'V × V':q.units?.[slot.key]??slot.unit; }
const triangleDefinitions = [
    {id:'battery-charge',title:'מטען, זרם וזמן',slots:[{key:'Q',symbol:'Q',unit:'Ah'},{key:'I',symbol:'I',unit:'A'},{key:'t',symbol:'t',unit:'h'}],formulas:['Q = I × t','I = Q ÷ t','t = Q ÷ I']},
    {id:'battery-energy',title:'אנרגיה, הספק וזמן',slots:[{key:'E',symbol:'E',unit:'Wh'},{key:'P',symbol:'P',unit:'W'},{key:'t',symbol:'t',unit:'h'}],formulas:['E = P × t','P = E ÷ t','t = E ÷ P']},
    {id:'battery-voltage-charge',title:'אנרגיה, מתח ומטען',slots:[{key:'E',symbol:'E',unit:'Wh'},{key:'U',symbol:'U',unit:'V'},{key:'Q',symbol:'Q',unit:'Ah'}],formulas:['E = U × Q','U = E ÷ Q','Q = E ÷ U']},
    {id:'battery-internal',title:'מפל מתח והתנגדות פנימית',slots:[{key:'ΔU',symbol:'ΔU',unit:'V'},{key:'I',symbol:'I',unit:'A'},{key:'R_s',symbol:'Rₛ',unit:'Ω'}],formulas:['ΔU = I × R_s','I = ΔU ÷ R_s','R_s = ΔU ÷ I']},
    { id:'ohm', title:'חוק אום', slots:[{key:'U',symbol:'U',unit:'V'},{key:'I',symbol:'I',unit:'A'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['U = I × R','I = U ÷ R','R = U ÷ I'] },
    { id:'power-ui', title:'הספק לפי מתח וזרם', slots:[{key:'P',symbol:'P',unit:'W'},{key:'U',symbol:'U',unit:'V'},{key:'I',symbol:'I',unit:'A'}], formulas:['P = U × I','U = P ÷ I','I = P ÷ U'] },
    { id:'power-ir', title:'הספק לפי זרם והתנגדות', slots:[{key:'P',symbol:'P',unit:'W'},{key:'I2',symbol:'I²',unit:'I × I'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['P = I² × R','R = P ÷ I²'], note:'I² פירושו I כפול I. בתרגול משתמשים כאן בזרם ידוע; לא מוציאים שורש.' },
    { id:'power-ur', title:'הספק לפי מתח והתנגדות', slots:[{key:'U2',symbol:'U²',unit:'U × U'},{key:'P',symbol:'P',unit:'W'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['U² = P × R','P = U² ÷ R','R = U² ÷ P'], note:'U² פירושו U כפול U. בתרגול משתמשים כאן במתח ידוע; לא מוציאים שורש.' },
];
let recentKey = 'dc.basics.recent.v1';
let viewTab = 'ohm', simulatorMode = 'custom', simulatorQuestion = null;
let reviewReturn=null;
const customDraft = {kind:'series',voltage:'24',resistances:['10','10']};
let customSimulator = {custom:true,kind:'series',voltage:24,simVoltage:24,resistances:[10,10],lamps:[false,false],givens:{},simAnimate:true};
let courseProfile='hvac';
let courseKey='dc.basics.course.v1';
let courseSeed=null,coursePrevious=[];
let questions, tab = 'ohm', levels = { ohm:0, series:0, parallel:0 }, positions, previous = [];
let qaActive=false,qaSnapshot=null,qaAnswerVisible=false;
let feedback = '', feedbackType = 'success', calculatorValue = null, calculatorFresh = false;
let formulaView = 'reference', calculatorReturnToFormulas = false;
let diagramZoom = 1, diagramBaseWidth = 0;
let diagramReturnToFormulas=false,diagramReturnFieldId=null,diagramReturnScroll=0;
let manualKeypadTarget = null, manualKeypadFieldId = null;
let personalKey = 'dc.basics.personal.v1';
const termsVersion = '2026-10-14.1';
const topicNames = { ohm:'חוק אום', power:'הספק', series:'מעגל טורי', parallel:'מעגל מקבילי',mixed:'מעגל מעורב',battery:'סוללות' };
let storageAvailable = true, profileRequired = false;
const entryStartedAt = new Date().toISOString();
let activeSessionId = null;
let personal = loadPersonal();
function emptyCounters() { return { attempted:0, first:0, attempts:0, solved:0, helped:0 }; }
function emptyPersonal() {
  return { version:1, profile:null, preferences:{textScale:100,theme:'system',contrast:false,motion:window.matchMedia('(prefers-reduced-motion: reduce)').matches,links:false},
    sessions:[],topics:Object.fromEntries(Object.keys(topicNames).map(key => [key,emptyCounters()])), totals:{...emptyCounters(),exercises:0} };
}
function loadPersonal() {
  const result = emptyPersonal();
  try {
    const saved = JSON.parse(localStorage.getItem(personalKey) || 'null');
    if (!saved || saved.version !== 1) return result;
    if (saved.profile && typeof saved.profile.name === 'string' && typeof saved.profile.birth === 'string') result.profile = {name:saved.profile.name.slice(0,80),birth:saved.profile.birth,termsVersion:saved.profile.termsVersion,acceptedAt:saved.profile.acceptedAt};
    if ([100,125,150].includes(saved.preferences?.textScale)) result.preferences.textScale = saved.preferences.textScale;
    if (['system','dark','light'].includes(saved.preferences?.theme)) result.preferences.theme = saved.preferences.theme;
    for (const key of ['contrast','motion','links']) if (typeof saved.preferences?.[key] === 'boolean') result.preferences[key] = saved.preferences[key];
    if(Array.isArray(saved.sessions)) result.sessions=saved.sessions.filter(item=>item&&typeof item.id==='string'&&typeof item.startedAt==='string'&&Number.isFinite(Date.parse(item.startedAt))&&Number.isSafeInteger(item.attempted)&&item.attempted>=0&&Number.isSafeInteger(item.first)&&item.first>=0&&item.first<=item.attempted).map(item=>({id:item.id,startedAt:item.startedAt,attempted:item.attempted,first:item.first}));
    for (const [key,counters] of Object.entries(result.topics)) for (const metric of Object.keys(counters)) if (Number.isSafeInteger(saved.topics?.[key]?.[metric]) && saved.topics[key][metric] >= 0) counters[metric] = saved.topics[key][metric];
    for (const metric of Object.keys(result.totals)) if (Number.isSafeInteger(saved.totals?.[metric]) && saved.totals[metric] >= 0) result.totals[metric] = saved.totals[metric];
  } catch { storageAvailable = false; }
  return result;
}
function savePersonal() {
  if(qaActive)return;
  try { localStorage.setItem(personalKey,JSON.stringify(personal)); storageAvailable = true; }
  catch { storageAvailable = false; }
  window.CourseApp?.syncProfile();
  showStorageNotice();
}
function showStorageNotice() {
  const note = $('storage-notice'); if (!note) return;
  note.hidden = storageAvailable;
  note.textContent = storageAvailable ? '' : 'השמירה בדפדפן אינה זמינה. אפשר לתרגל בכרטיסייה הזו, אך הפרופיל וההתקדמות החדשה עלולים להיעלם בסגירתה. בדקו שהדפדפן מאפשר שמירת נתונים לאתר.';
}
function localDateValue(date = new Date()) { return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`; }
function validBirth(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(value + 'T12:00:00'), oldest = new Date(); oldest.setFullYear(oldest.getFullYear()-130);
  return Number.isFinite(date.getTime()) && localDateValue(date) === value && value <= localDateValue() && value >= localDateValue(oldest);
}
function birthTextFromISO(value) {
  const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value));
  return match?`${match[3]}/${match[2]}/${match[1]}`:'';
}
function birthISOFromText(value) {
  const text=String(value).trim();
  if(/^\d{4}-\d{2}-\d{2}$/.test(text))return validBirth(text)?text:'';
  const match=/^(\d{2})\/(\d{2})\/(\d{2}|\d{4})$/.exec(text);
  if(!match)return '';
  let year=Number(match[3]);
  if(match[3].length===2){
    const current=new Date().getFullYear();
    year=Math.floor(current/100)*100+year;
    if(year>current)year-=100;
  }
  const iso=`${String(year).padStart(4,'0')}-${match[2]}-${match[1]}`;
  return validBirth(iso)?iso:'';
}
function birthFeedback(message='') {
  const error=$('profile-error');
  if(message){error.textContent=message;error.dataset.field='profile-birth';}
  else if(error.dataset.field==='profile-birth'){error.textContent='';delete error.dataset.field;}
}
function normalizeBirthInput(report=false) {
  const input=$('profile-birth'),iso=birthISOFromText(input.value);
  $('profile-birth-picker').value=iso;
  if(iso){input.value=birthTextFromISO(iso);input.removeAttribute('aria-invalid');birthFeedback();}
  else if(report&&input.value.trim()){
    input.setAttribute('aria-invalid','true');
    birthFeedback('יש להזין תאריך לידה תקין שאינו בעתיד, לפי יום/חודש/שנה.');
  }
  return iso;
}
function maskBirthInput(event) {
  const input=event.target,raw=input.value,position=input.selectionStart??raw.length;
  const deleting=event.inputType?.startsWith('delete');
  if(/^\d{4}-\d{2}-\d{2}$/.test(raw)){
    input.value=birthTextFromISO(raw);
  }else{
    const short=/^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/.exec(raw);
    const digits=(short?short[1].padStart(2,'0')+short[2].padStart(2,'0')+short[3]:raw.replace(/\D/g,'')).slice(0,8);
    let formatted=digits.slice(0,2);
    if(digits.length>2||digits.length===2&&!deleting)formatted+='/'+digits.slice(2,4);
    if(digits.length>4||digits.length===4&&!deleting)formatted+='/'+digits.slice(4);
    const count=raw.slice(0,position).replace(/\D/g,'').length;
    input.value=formatted;
    let caret=formatted.length;
    if(position<raw.length){
      caret=0;let seen=0;
      while(caret<formatted.length&&seen<count){if(/\d/.test(formatted[caret]))seen++;caret++;}
      if(!deleting&&formatted[caret]==='/')caret++;
    }
    input.setSelectionRange(caret,caret);
  }
  $('profile-birth-picker').value='';input.removeAttribute('aria-invalid');birthFeedback();
}
$('profile-birth').addEventListener('input',maskBirthInput);
$('profile-birth').addEventListener('beforeinput',event=>{
  const data=event.data??'';
  const date=/^(?:\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}\/(?:\d{2}|\d{4}))$/.test(data);
  if(event.inputType==='insertText'&&event.data!==null&&!/^[0-9]+$/.test(data)&&!date)event.preventDefault();
});
$('profile-birth').addEventListener('keydown',event=>{
  if(!event.ctrlKey&&!event.metaKey&&event.key.length===1&&!/^[0-9]$/.test(event.key))event.preventDefault();
});
$('profile-birth').addEventListener('blur',()=>normalizeBirthInput(true));
$('profile-birth-picker').addEventListener('change',event=>{
  $('profile-birth').value=birthTextFromISO(event.target.value);normalizeBirthInput(true);
});
$('profile-birth-picker').addEventListener('click',event=>{
  try{event.target.showPicker?.();}catch{}
});

function profileReady() { return !!personal.profile && personal.profile.name.trim().length >= 2 && validBirth(personal.profile.birth) && personal.profile.termsVersion === termsVersion; }
function termsHTML() {
  return `<p class="small muted">עדכון: 14.10.2026</p><h3>מטרת האתר והשימוש בתוכן</h3><p>האתר מיועד ללימוד ולתרגול עיוני של יסודות החשמל ומעגלי DC באמצעות מודלים פשוטים. התרגילים והסימולטור אינם הוראות לביצוע עבודות חשמל ואינם תחליף להכשרה, להסמכה, לייעוץ מקצועי או לבדיקה של איש מקצוע מוסמך. אין לבצע חיבור, תיקון, מדידה או שינוי במערכת חשמל ממשית על סמך האתר.</p><h3>דיוק, זמינות והגבלת אחריות</h3><p>ייתכנו טעויות, עיגול מספרים, השמטות ותקלות. המודלים אינם מציגים את כל התופעות או את הסיכונים שבמערכות אמיתיות. אין התחייבות לשלמות התוכן, להתאמה למטרה מסוימת, לזמינות רציפה או לשמירת נתונים ללא תקלות.</p><p>במידה המרבית המותרת על פי דין, מפעילי האתר לא יישאו באחריות לנזק עקיף או תוצאתי עקב הסתמכות על התוכן, שימוש שלא למטרות לימוד או אובדן נתונים מקומיים. אין בתנאים אלה כדי לפטור מאחריות שאי אפשר להתנות עליה על פי דין, לרבות אחריות לנזק גוף או למעשה זדון ככל שהדין אוסר את הגבלתה, או כדי לגרוע מזכויות שאינן ניתנות לוויתור.</p><h3>פרטיות ופרופיל מקומי</h3><p>השם, תאריך הלידה, מועד האישור וגרסת התנאים, התאמות הנגישות ונתוני ההתקדמות נשמרים בדפדפן במכשיר הזה. קוד היישום אינו שולח את פרטי הפרופיל לשרת. במבחן העיוני נשלחים מזהי השאלות והתשובות שנבחרו לשרת האתר לצורך בדיקה; תוצאות המבחנים וההתקדמות נשמרות בדפדפן במכשיר הזה. שירות האירוח עשוי לעבד נתוני תקשורת טכניים בהתאם לתנאיו.</p><p>אין סנכרון בין מכשירים. מי שניגש לדפדפן הזה עלול לצפות בפרופיל ובהתקדמות. ניקוי נתוני האתר או שימוש בגלישה פרטית עשויים למחוק את השמירה. שליחת הערות לעומר היא פעולה לבחירתכם. במסלול משוב ודירוג אפליקציה, דירוג הכוכבים והמלל שבחרתם לצרף נשלחים לשרת האתר ומתפרסמים במאגר GitHub ציבורי. באתר ובפניית סיכום ב־GitHub מוצגים ממוצע הדירוגים ומספר הדירוגים. במסלול הערות, המלל ומיקום התרגיל אם בחרתם לצרף אותו נשמרים במאגר GitHub פרטי, הזמין למפעיל האתר ולבעלי הרשאת גישה למאגר. הערות פרטיות אינן מתפרסמות במשוב הציבורי ואינן נכללות בדירוג. פרטי הפרופיל ותאריך הלידה אינם מצורפים למשוב באופן אוטומטי. ניתן למחוק את הפרטים באמצעות מחיקת נתוני האתר בהגדרות הדפדפן. איפוס התרגילים באתר שומר על הפרופיל ועל ההתקדמות האישית.</p><h3>הסכמה ושימוש אחראי</h3><p>אפשר לעיין בתנאים לפני האישור וגם בהמשך דרך הקישור בתחתית האתר. יש להשתמש באתר באופן תקין, בלי לפגוע בפעולתו או בזכויות אחרים. שינוי מהותי בתנאים עשוי לחייב אישור מחדש. אם הוראה אינה תקפה, יתר ההוראות יחולו ככל שהדין מאפשר זאת.</p>`;
}
function accessibilityControls(prefix) {
  const prefs = personal.preferences;
  return `<div class="accessibility-options"><label for="${prefix}-scale">גודל טקסט <select id="${prefix}-scale" data-preference="textScale">${[100,125,150].map(size=>`<option value="${size}"${prefs.textScale===size?' selected':''}>${size}%</option>`).join('')}</select></label><label for="${prefix}-theme">מצב לילה <select id="${prefix}-theme" data-preference="theme">${[['system','בהתאם לטלפון'],['dark','פעיל'],['light','כבוי']].map(([value,label])=>`<option value="${value}"${prefs.theme===value?' selected':''}>${label}</option>`).join('')}</select></label>${[['contrast','ניגודיות מוגברת'],['motion','הפחתת תנועה והנפשות'],['links','הדגשת קישורים']].map(([key,label])=>`<label for="${prefix}-${key}"><input id="${prefix}-${key}" data-preference="${key}" type="checkbox"${prefs[key]?' checked':''}>${label}</label>`).join('')}<button class="btn secondary" data-reset-accessibility type="button">איפוס התאמות נגישות</button></div>`;
}
function applyPreferences() {
  const prefs = personal.preferences;
  applyTextScale(prefs.textScale);
  applyTheme(prefs.theme);
  document.body.classList.remove('large-text','text-scale-125','text-scale-150');
  document.body.classList.toggle('high-contrast',prefs.contrast);
  document.body.classList.toggle('reduce-motion',prefs.motion);
  document.body.classList.toggle('highlight-links',prefs.links);
  $('text-size').setAttribute('aria-pressed',prefs.textScale!==100);
  document.querySelectorAll('[data-preference]').forEach(input => { const value = prefs[input.dataset.preference]; if (input.type==='checkbox') input.checked=value; else input.value=String(value); });
  if (typeof questions !== 'undefined' && questions && prefs.motion) for (const levels of Object.values(questions)) for (const list of levels) for (const q of list) q.simAnimate=false;
  if(prefs.motion) customSimulator.simAnimate=false;
  if ($('sim-diagram')) updateSimulator();
  fitDialogs(); resizeFrame();
}
function paintProfileButton() { $('profile-label').textContent = 'פרופיל'; }
function openProfile() {
  if(window.ShabbatMode.isLocked()||qaActive&&!profileReady())return;
  profileRequired = !profileReady(); $('app').inert = profileRequired;
  if (!$('profile-dialog').open) {
    $('profile-name').value = personal.profile?.name ?? ''; $('profile-birth').value = birthTextFromISO(personal.profile?.birth ?? '');$('profile-birth-picker').value=personal.profile?.birth??'';
    $('profile-consent').checked = profileReady(); $('profile-error').textContent='';
  }
  $('profile-close').hidden = profileRequired;
  openDialog('profile-dialog');
}
function submitProfile() {
  const name=$('profile-name').value.trim(), birth=normalizeBirthInput(), consent=$('profile-consent').checked;
  for (const id of ['profile-name','profile-birth','profile-consent']) $(id).removeAttribute('aria-invalid');
  let invalid, message;
  if(name.length<2){invalid='profile-name';message='יש להזין שם באורך של שתי אותיות לפחות.';}
  else if(!validBirth(birth)){invalid='profile-birth';message='יש להזין תאריך לידה תקין שאינו בעתיד.';}
  else if(!consent){invalid='profile-consent';message='כדי להמשיך יש לאשר את תנאי השימוש ואת השמירה המקומית.';}
  if(invalid){$('profile-error').dataset.field=invalid;$('profile-error').textContent=message;$(invalid).setAttribute('aria-invalid','true');$(invalid).focus();fitDialogs();return;}
  personal.profile={name,birth,termsVersion,acceptedAt:new Date().toISOString()};savePersonal();
  profileRequired=false;$('app').inert=false;$('profile-dialog').close();paintProfileButton();renderProgress();resizeFrame();
}
function stepTopics(q,step) {
  const power = /^P/.test(step.key) || (q.kind==='ohm' && /P/.test(step.formula));
  return q.kind==='ohm' ? [power?'power':'ohm'] : [q.kind,...(power?['power']:[])];
}
function trackedStep() {
  if(qaActive)return null;
  const q=currentQuestion(),step=currentStep();if(!step||q.accepted||!profileReady())return null;
  q.personalSteps??={};
  return q.personalSteps[q.cursor]??={topics:stepTopics(q,step),attempts:0,helped:false};
}
function recordAttempt(correct,mode='answer') {
  const tracked=trackedStep();if(!tracked)return;
  const counters=[personal.totals,...tracked.topics.map(key=>personal.topics[key])];
  for(const value of counters){if(!tracked.attempts)value.attempted++;value.attempts++;if(correct){value.solved++;if(!tracked.attempts)value.first++;}}
  const session = currentSession();
  if(!tracked.attempts){session.attempted++;if(correct)session.first++;}
  tracked.attempts++;tracked.mode=mode;
  if(correct && currentQuestion().cursor===currentQuestion().steps.length-1)personal.totals.exercises++;
  savePersonal();renderProgress();
}
function markHelp() {
  const tracked=trackedStep();if(!tracked||tracked.helped)return;
  tracked.helped=true;personal.totals.helped++;
  for(const key of tracked.topics)personal.topics[key].helped++;
  savePersonal();renderProgress();resizeFrame();
}
function currentSession() {
  let session = personal.sessions.find(item=>item.id===activeSessionId);
  if(!session) {
    activeSessionId = entryStartedAt+'-'+Math.random().toString(36).slice(2);
    session = {id:activeSessionId,startedAt:entryStartedAt,attempted:0,first:0}; personal.sessions.push(session);
  }
  return session;
}
function progressTrendHTML() {
  const entries = personal.sessions.filter(item=>item.attempted>0).sort((a,b)=>Date.parse(a.startedAt)-Date.parse(b.startedAt)).slice(-30);
  const description = 'ציר X: מועד הכניסה לאפליקציה. ציר Y: אחוז התשובות הנכונות בניסיון הראשון באותה כניסה.';
  if(!entries.length) return `<section class="progress-trend"><h3>שיפור לאורך זמן</h3><p class="small muted">${description}</p><p class="small muted">הגרף יתחיל להצטבר לאחר בדיקת תשובות. ההתקדמות הקודמת נשמרת, אך אין לה מועדי כניסה שאפשר לשחזר.</p></section>`;
  const dates = new Intl.DateTimeFormat('he-IL',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const width=800,height=300,left=64,right=760,top=28,bottom=214;
  const start=Date.parse(entries[0].startedAt),end=Date.parse(entries[entries.length-1].startedAt);
  const points=entries.map(item=>{const rate=100*item.first/item.attempted;return {...item,rate,x:end===start?(left+right)/2:left+(Date.parse(item.startedAt)-start)/(end-start)*(right-left),y:bottom-rate/100*(bottom-top),label:dates.format(new Date(item.startedAt))};});
  const grid=[0,25,50,75,100].map(value=>{const y=bottom-value/100*(bottom-top);return `<path d="M${left} ${y} H${right}" stroke="var(--line)"/><text x="${left-10}" y="${y+5}" text-anchor="end" fill="var(--muted)" font-size="14">${value}%</text>`;}).join('');
  const tickIndices=[...new Set(Array.from({length:Math.min(5,points.length)},(_,i)=>Math.round(i*(points.length-1)/Math.max(1,Math.min(5,points.length)-1))))];
  const ticks=tickIndices.map(index=>{const p=points[index];return `<text x="${p.x}" y="${bottom+27}" text-anchor="${index===0&&points.length>1?'start':index===points.length-1&&points.length>1?'end':'middle'}" fill="var(--muted)" font-size="12">${escapeHTML(p.label)}</text>`;}).join('');
  const line=points.length>1?`<polyline points="${points.map(p=>`${p.x},${p.y}`).join(' ')}" fill="none" stroke="var(--green)" stroke-width="3"/>`:'';
  const dots=points.map(p=>`<circle cx="${p.x}" cy="${p.y}" r="5" fill="var(--green)"><title>${escapeHTML(p.label)} · ${DC.fmt(p.rate)}% · ${p.first} מתוך ${p.attempted} תשובות</title></circle>`).join('');
  const table=points.map(p=>`<tr><td data-label="מועד כניסה">${escapeHTML(new Date(p.startedAt).toLocaleString('he-IL'))}</td><td data-label="תשובות שנוסו">${p.attempted}</td><td data-label="נכונות בניסיון הראשון">${p.first}</td><td data-label="ממוצע דיוק">${bdi(DC.fmt(p.rate)+'%')}</td></tr>`).join('');
  return `<section class="progress-trend"><h3>שיפור לאורך זמן</h3><p class="small muted">${description} כל נקודה היא כניסה שבה נבדקו תשובות; מוצגות עד 30 הכניסות האחרונות.</p><div class="trend-scroll"><svg class="trend-chart" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="גרף אחוז התשובות הנכונות בניסיון הראשון לאורך זמן" direction="ltr"><title>שיפור לאורך זמן</title><desc>${escapeHTML(points.map(p=>p.label+': '+DC.fmt(p.rate)+' אחוז').join('; '))}</desc>${grid}<path d="M${left} ${top} V${bottom} H${right}" fill="none" stroke="var(--muted)"/>${line}${dots}${ticks}<text x="${(left+right)/2}" y="${height-12}" text-anchor="middle" fill="var(--ink)" font-size="15" direction="rtl">מועד הכניסה לאפליקציה</text></svg></div><details><summary>נתוני גרף השיפור</summary><div class="table-scroll"><table><thead><tr><th>מועד כניסה</th><th>תשובות שנוסו</th><th>נכונות בניסיון הראשון</th><th>ממוצע דיוק</th></tr></thead><tbody>${table}</tbody></table></div></details></section>`;
}
function renderProgress() {
  if(!$('personal-progress'))return;
  const total=personal.totals,rate=value=>value.attempted?Math.round(value.first/value.attempted*100):null;
  const rows=Object.entries(topicNames).filter(([key])=>!window.CourseApp||CourseApp.topicVisible(key)).map(([key,name])=>{
    const value=personal.topics[key],accuracy=rate(value),average=value.attempted?DC.fmt(value.attempts/value.attempted):'—';
    return {name,value,accuracy,average};
  });
  const chart=rows.map(({name,value,accuracy})=>`<div class="personal-chart-row"><span>${name}</span><div class="personal-bar" role="meter" aria-label="דיוק בניסיון הראשון — ${name}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${accuracy??0}" aria-valuetext="${accuracy===null?'עדיין אין תשובות':accuracy+' אחוז, מתוך '+value.attempted+' שלבים'}"><div style="width:${accuracy??0}%"></div></div><span class="personal-rate">${accuracy===null?'—':accuracy+'%'}</span></div>`).join('');
  const table=rows.map(({name,value,accuracy,average})=>`<tr><td data-label="נושא">${name}</td><td data-label="שלבים שנוסו">${value.attempted}</td><td data-label="שלבים שהושלמו">${value.solved}</td><td data-label="דיוק בניסיון ראשון">${accuracy===null?'—':accuracy+'%'}</td><td data-label="ניסיונות"><span class="attempt-values">${value.attempts}<span class="small muted"> · ממוצע ${average}</span></span></td><td data-label="שלבים עם עזרה">${value.helped}</td></tr>`).join('');
  $('personal-progress').innerHTML=`<div class="progress-heading"><div><div class="eyebrow">לומדים להכיר את ההתקדמות</div><h2 id="personal-progress-title" tabindex="-1">ההתקדמות האישית${profileReady()?' של '+escapeHTML(personal.profile.name):''}</h2></div><button class="btn secondary tiny" data-new-course>איפוס תרגילים</button></div><p class="small muted">הנתונים נשמרים במכשיר הזה ומצטברים בין סבבי תרגול. איפוס תרגילים שומר על ההתקדמות האישית.</p><div class="personal-summary"><div class="personal-stat"><strong>${total.exercises}</strong><span class="small">תרגילים שהושלמו</span></div><div class="personal-stat"><strong>${rate(total)===null?'—':rate(total)+'%'}</strong><span class="small">דיוק בניסיון הראשון</span></div><div class="personal-stat"><strong>${total.attempts}</strong><span class="small">ניסיונות בסך הכול</span></div></div>${progressTrendHTML()}<h3>דיוק בניסיון הראשון לפי נושא</h3><div class="personal-chart" aria-label="גרף דיוק לפי נושא">${chart}</div><div class="table-scroll"><table><caption class="small muted">פירוט התרגול לפי נושאים</caption><thead><tr><th scope="col">נושא</th><th scope="col">שלבים שנוסו</th><th scope="col">שלבים שהושלמו</th><th scope="col">דיוק בניסיון ראשון</th><th scope="col">ניסיונות</th><th scope="col">שלבים עם עזרה</th></tr></thead><tbody>${table}</tbody></table></div><p class="small muted">הדיוק מחושב לפי השליחה הראשונה בכל צעד. מספר הניסיונות כולל בדיקות תשובה והצבה במשולש. עזרה כוללת רמזים, פתרון מוסבר, לשונית עזרה ומילוי רשימת הנתונים. עזרה נספרת פעם אחת בכל צעד, גם אם נעזרים שוב. גם רמז שמוצג אחרי טעות נחשב עזרה. שאלות הספק במעגל טורי או מקבילי נספרות גם בהספק וגם בנושא המעגל.</p>`;
}
function showProgress() { renderProgress(); openDialog('progress-dialog'); }
function initializePersonal() {
  document.querySelectorAll('[data-terms-document]').forEach(node=>node.innerHTML=termsHTML());
  $('profile-birth-picker').max=localDateValue();
  const oldestBirth=new Date();oldestBirth.setFullYear(oldestBirth.getFullYear()-130);$('profile-birth-picker').min=localDateValue(oldestBirth);
  $('accessibility-controls').innerHTML=accessibilityControls('access');
  $('profile-accessibility-controls').innerHTML=accessibilityControls('entry');
  applyPreferences();paintProfileButton();renderProgress();showStorageNotice();
  if(!profileReady())openProfile();
}
try { const saved = JSON.parse(localStorage.getItem(recentKey)); if (Array.isArray(saved)) previous = saved.filter(s => typeof s === 'string').slice(-280); } catch {}
function saveCourse() {
  if(qaActive)return;
  if(!questions||courseSeed===null)return;
  const states=Object.fromEntries(DC.kinds.map(kind=>[kind,questions[kind].map(list=>list.map(q=>({
    cursor:q.cursor,draft:q.draft,accepted:q.accepted===true,attempts:q.attempts,help:q.help,hint:q.hint,solution:q.solution,
    simVoltage:q.simVoltage,simAnimate:q.simAnimate,manualWork:q.manualWork,personalSteps:q.personalSteps
  })))]));
  try{localStorage.setItem(courseKey,JSON.stringify({version:5,seed:courseSeed,generationPrevious:coursePrevious,states,tab,levels,positions,feedback,feedbackType,reviewReturn}));}
  catch{storageAvailable=false;showStorageNotice();}
}
function restoreManualWork(raw,q) {
  const work={},text=value=>typeof value==='string'?value.slice(0,24):'';
  if(!raw||typeof raw!=='object')return work;
  for(let index=0;index<=q.steps.length;index++) {
    const item=raw[index];if(!item||typeof item!=='object')continue;
    const drafts={};
    const legacy=Object.values(item.drafts??{}).some(draft=>draft&&Object.prototype.hasOwnProperty.call(draft,'answer'));
    for(const definition of triangleDefinitions) {
      const draft=item.drafts?.[definition.id];if(!draft||typeof draft!=='object')continue;
      const values=Object.fromEntries(definition.slots.map(slot=>{
        const value=text(draft.values?.[slot.key]);
        return [slot.key,manualTokenKind(value)==='number'?value:''];
      }));
      const stepKey=q.steps[index]?.key;
      const target=/^[UIRP]\d+$/.test(stepKey??'')?stepKey[0]:stepKey;
      if(definition.slots.some(slot=>slot.key===target)&&!values[target]&&manualTokenKind(text(draft.answer))==='number')values[target]=text(draft.answer);
      drafts[definition.id]={values};
    }
    work[index]={list:Object.fromEntries(['U','R','I','P'].map(key=>[key,text(item.list?.[key])])),
      selected:triangleDefinitions.some(def=>def.id===item.selected)?item.selected:'',drafts,
      message:!legacy&&typeof item.message==='string'?item.message.slice(0,1000):'',type:item.type==='success'?'success':'error',
      errors:!legacy&&Array.isArray(item.errors)?item.errors.filter(value=>typeof value==='string').slice(0,5):[],
      listStatus:typeof item.listStatus==='string'?item.listStatus.slice(0,500):''};
  }
  return work;
}
function restoreCourse() {
  try {
    const saved=JSON.parse(localStorage.getItem(courseKey)||'null');
    // Version 4 changes only level B; preserve A/C and personal totals/profile.
    // Never apply version 3 answers to the new level B questions.
    if(!saved||saved.version!==5||!Number.isSafeInteger(saved.seed)||!Array.isArray(saved.generationPrevious))return false;
    const prior=saved.generationPrevious.filter(value=>typeof value==='string').slice(-280);
    const restored=DC.course(saved.seed,prior,courseProfile),restoredLevels={},restoredPositions={};
    for(const kind of DC.kinds) {
      const stateLevels=saved.states?.[kind];
      if(!Array.isArray(stateLevels)||stateLevels.length!==restored[kind].length)return false;
      const level=saved.levels?.[kind];
      if(!Number.isInteger(level)||level<0||level>=restored[kind].length)return false;
      restoredLevels[kind]=level;restoredPositions[kind]=[];
      for(let j=0;j<restored[kind].length;j++) {
        const list=restored[kind][j],states=stateLevels[j],position=saved.positions?.[kind]?.[j];
        if(!Array.isArray(states)||states.length!==list.length||!Number.isInteger(position)||position<0||position>=list.length)return false;
        const resetDecimalLevel=saved.version===3&&j===1;
        restoredPositions[kind].push(resetDecimalLevel?0:position);
        for(let i=0;i<list.length;i++) {
          const q=list[i],state=states[i];
          if(resetDecimalLevel) {
            Object.assign(q,{cursor:0,draft:'',accepted:false,attempts:0,help:{},hint:false,solution:false,
              simVoltage:q.voltage,simAnimate:!personal.preferences.motion,manualWork:{},personalSteps:{}});
            continue;
          }
          if(!state||!Number.isInteger(state.cursor)||state.cursor<0||state.cursor>q.steps.length)return false;
          Object.assign(q,{cursor:state.cursor,draft:typeof state.draft==='string'?state.draft.slice(0,24):'',
            attempts:Number.isSafeInteger(state.attempts)&&state.attempts>=0?state.attempts:0,
            help:Object.fromEntries(q.steps.map((_,index)=>[index,state.help?.[index]===true])),
            hint:state.hint===true,solution:state.solution===true,
            simVoltage:Number.isFinite(state.simVoltage)&&state.simVoltage>=0&&state.simVoltage<=q.voltage*2?state.simVoltage:q.voltage,
            simAnimate:!personal.preferences.motion&&state.simAnimate!==false,
            manualWork:restoreManualWork(state.manualWork,q),personalSteps:{}});
          q.accepted=state.accepted===true&&q.cursor<q.steps.length&&DC.accepted(q.draft,q.steps[q.cursor].value);
          for(let index=0;index<q.steps.length;index++) {
            const tracked=state.personalSteps?.[index];
            if(tracked&&Number.isSafeInteger(tracked.attempts)&&tracked.attempts>=0)
              q.personalSteps[index]={topics:stepTopics(q,q.steps[index]),attempts:tracked.attempts,helped:tracked.helped===true,mode:tracked.mode==='manual'?'manual':'answer'};
          }
        }
      }
    }
    questions=restored;courseSeed=saved.seed;coursePrevious=prior;
    levels=restoredLevels;positions=restoredPositions;tab=DC.kinds.includes(saved.tab)?saved.tab:'ohm';viewTab=tab;
    const back=saved.reviewReturn;
    reviewReturn=back&&!(saved.version===3&&back.level===1)&&DC.kinds.includes(back.kind)&&Number.isInteger(back.level)&&Number.isInteger(back.index)&&questions[back.kind]?.[back.level]?.[back.index]?{kind:back.kind,level:back.level,index:back.index}:null;
    feedback=saved.version===3&&levels[tab]===1?'':typeof saved.feedback==='string'?saved.feedback.slice(0,1000):'';feedbackType=saved.feedbackType==='error'?'error':'success';
    render();return true;
  }catch{return false;}
}
function newCourse() {
  const seed = window.crypto?.getRandomValues ? window.crypto.getRandomValues(new Uint32Array(1))[0] : (Date.now() ^ Math.floor(Math.random() * 4294967296));
  courseSeed=seed;coursePrevious=previous.slice();
  questions = DC.course(seed, coursePrevious,courseProfile);
  reviewReturn=null;
  viewTab=tab;
  simulatorQuestion = null;
  positions = Object.fromEntries(DC.kinds.map(kind=>[kind,questions[kind].map(()=>0)]));
  for (const kind of DC.kinds) for (const level of questions[kind]) for (const q of level) {
    q.cursor = 0; q.draft = ''; q.accepted = false; q.attempts = 0; q.help = {}; q.hint = false; q.solution = false; q.simVoltage = q.voltage; q.simAnimate = !personal.preferences.motion;
    previous.push(q.signature);
  }
  previous = previous.slice(-280);
  if(!qaActive)try { localStorage.setItem(recentKey, JSON.stringify(previous)); } catch {}
  feedback = '';feedbackType='success'; render();
}
function openQA() {
  if(qaActive){$('qa-panel').scrollIntoView({block:'start'});return;}
  $('qa-password').value='';$('qa-password').removeAttribute('aria-invalid');$('qa-login-error').textContent='';
  openDialog('qa-login-dialog');$('qa-password').focus();
}
async function enterQA() {
  if(qaActive)return;
  if(!await window.CourseApp.loginAdmin())return;
  window.CourseApp.onEnterQA();
  saveCourse();
  qaSnapshot={questions,levels,positions,tab,viewTab,courseSeed,coursePrevious,previous,feedback,feedbackType,reviewReturn,
    personal,activeSessionId,storageAvailable,simulatorMode,simulatorQuestion,customSimulator,
    customDraft:JSON.parse(JSON.stringify(customDraft)),formulaView,scroll:window.scrollY};
  questions=JSON.parse(JSON.stringify(questions));levels={...levels};positions=JSON.parse(JSON.stringify(positions));
  coursePrevious=coursePrevious.slice();previous=previous.slice();personal=JSON.parse(JSON.stringify(personal));
  customSimulator=JSON.parse(JSON.stringify(customSimulator));reviewReturn=null;simulatorQuestion=null;
  viewTab=tab;feedback='';feedbackType='success';qaActive=true;qaAnswerVisible=false;
  window.ShabbatMode.resetQA();
  document.querySelectorAll('dialog[open]').forEach(dialog=>dialog.close());hideManualKeypad();
  $('qa-password').value='';document.body.classList.add('qa-mode');
  applyPreferences();render();$('qa-panel').scrollIntoView({block:'start'});
}
function exitQA() {
  if(!qaActive||!qaSnapshot)return;
  document.querySelectorAll('dialog[open]').forEach(dialog=>dialog.close());hideManualKeypad();
  const saved=qaSnapshot;
  ({questions,levels,positions,tab,viewTab,courseSeed,coursePrevious,previous,feedback,feedbackType,reviewReturn,
    personal,activeSessionId,storageAvailable,simulatorMode,simulatorQuestion,customSimulator,formulaView}=saved);
  customDraft.kind=saved.customDraft.kind;customDraft.voltage=saved.customDraft.voltage;customDraft.resistances=saved.customDraft.resistances;
  qaActive=false;qaSnapshot=null;qaAnswerVisible=false;document.body.classList.remove('qa-mode');
  window.ShabbatMode.resetQA();
  window.CourseApp.onExitQA();clearCalculator();applyPreferences();render();requestAnimationFrame(()=>window.scrollTo(0,saved.scroll));
  if(!profileReady()&&!window.ShabbatMode.isLocked())openProfile();
}
function qaExercises() {
  return DC.kinds.flatMap(kind=>questions[kind].flatMap((list,level)=>list.map((q,index)=>({kind,level,index,q}))));
}
function qaGo(kind,level,index,cursor=0) {
  if(!qaActive)return;
  const q=questions[kind]?.[level]?.[index];
  if(!q||!Number.isInteger(cursor)||cursor<0||cursor>q.steps.length)return;
  q.cursor=cursor;q.accepted=false;q.draft='';q.attempts=0;q.hint=false;q.solution=false;
  qaAnswerVisible=false;showExercise({kind,level,index});
}
function qaMove(delta) {
  if(!qaActive)return;
  const list=qaExercises(),here=list.findIndex(item=>item.q===currentQuestion()),q=currentQuestion();
  const next=q.cursor+delta;
  if(next>=0&&next<=q.steps.length)return qaGo(tab,levels[tab],positions[tab][levels[tab]],next);
  const other=list[here+delta];
  if(other)qaGo(other.kind,other.level,other.index,delta>0?0:other.q.steps.length);
}
function renderQA() {
  const panel=$('qa-panel');panel.hidden=!qaActive;
  document.querySelectorAll('[data-open-qa]').forEach(button=>{button.hidden=qaActive;});
  if(!qaActive){panel.innerHTML='';return;}
  const q=currentQuestion(),level=levels[tab],index=positions[tab][level];
  const options=(values,selected)=>values.map(([value,label])=>`<option value="${value}"${value===selected?' selected':''}>${escapeHTML(label)}</option>`).join('');
  const all=qaExercises(),at=all.findIndex(item=>item.q===q),step=currentStep();
  panel.innerHTML=`<section class="qa-banner" aria-labelledby="qa-mode-title"><div class="qa-banner-head"><h2 id="qa-mode-title">מצב בדיקות</h2><button class="btn" data-exit-qa>חזרה למצב רגיל</button></div><p class="small">אפשר לעבור בחופשיות בין כל הנושאים, התרגילים והסעיפים. הפעולות במצב הזה אינן נשמרות בהתקדמות האישית.</p><div class="qa-selectors"><label for="qa-topic">נושא<select id="qa-topic">${options(DC.kinds.map(kind=>[kind,names[kind]]),tab)}</select></label><label for="qa-level">רמה<select id="qa-level">${options(questions[tab].map((_,i)=>[i,`רמה ${letters[i]} — ${DC.levelNames[i]}`]),level)}</select></label><label for="qa-exercise">תרגיל<select id="qa-exercise">${options(questions[tab][level].map((item,i)=>[i,`${i+1}. ${item.title}`]),index)}</select></label><label for="qa-step">סעיף<select id="qa-step">${options([...q.steps.map((item,i)=>[i,`${i+1}. ${item.label}`]),[q.steps.length,'סיום התרגיל']],q.cursor)}</select></label></div><div class="qa-actions"><button class="btn secondary tiny" data-qa-previous${at===0&&q.cursor===0?' disabled':''}>סעיף קודם</button><button class="btn tiny" data-qa-next${at===all.length-1&&completed(q)?' disabled':''}>עבור סעיף</button><button class="btn secondary tiny" data-qa-answer${step?'':' disabled'} aria-expanded="${qaAnswerVisible}">${qaAnswerVisible?'הסתר תשובה':'הצג תשובה'}</button><button class="btn secondary tiny" data-go-simulator>הצג בסימולטור</button></div>${qaAnswerVisible&&step?`<div class="qa-answer" role="status"><strong>${escapeHTML(step.label)}</strong><div class="math">${mathNotation(step.formula)}</div><div class="math">${mathNotation(step.substitution)} = ${DC.fmt(step.value)} ${step.unit}</div></div>`:''}</section>`;
  window.CourseApp?.renderAdmin();
  const mode=window.ShabbatMode.getMode(),status=mode==='bypass'?'עקיפת שבת פעילה ב־QA בלבד':mode==='test'?'מצב טסט — תצוגת שבת לבדיקה':'מצב אוטומטי לפי זמני ירושלים';
  panel.querySelector('.qa-banner').insertAdjacentHTML('beforeend',`<section class="qa-shabbat" aria-labelledby="qa-shabbat-title"><h3 id="qa-shabbat-title">בדיקת מצב שבת</h3><p id="qa-shabbat-status" class="small" role="status">${status}</p><div class="qa-shabbat-controls"><button type="button" class="btn secondary tiny" data-shabbat-mode="test" aria-pressed="${mode==='test'}">מצב טסט — הצגת שבת</button><button type="button" class="btn secondary tiny" data-shabbat-mode="bypass" aria-pressed="${mode==='bypass'}">עקיפת מצב שבת</button><button type="button" class="btn secondary tiny" data-shabbat-mode="auto" aria-pressed="${mode==='auto'}">לפי זמני ירושלים</button></div><p class="small muted">השינויים חלים רק בבדיקות הנוכחיות. יציאה מ־QA או רענון הדף מחזירים את מצב השבת האוטומטי.</p></section>`);
}
function currentQuestion() { return questions[tab][levels[tab]][positions[tab][levels[tab]]]; }
function completed(q) { return q.cursor === q.steps.length; }
function simulationReady(q) { return qaActive||completed(q)||q.accepted&&q.cursor===q.steps.length-1; }
function currentStep() { const q = currentQuestion(); return q.steps[q.cursor]; }
function bdi(value) { return `<bdi>${escapeHTML(value)}</bdi>`; }
function mathNotation(formula) {
  const notation=String(formula).replace(/\bR_?eq\b/gi,'R_T');
  const input=notation.replace(/\s/g,''),tokens=input.match(/[A-Za-zΔ]+(?:_[A-Za-z]+|\d+)?|\d+(?:\.\d+)?|[²×÷+−*/=≈()?]/g)||[];
  if(tokens.join('')!==input)return bdi(notation);
  let cursor=0;
  const symbol=token=>{
    if(/^\d/.test(token))return `<mn>${token}</mn>`;
    if(token==='ΔU')return '<mrow><mi>Δ</mi><mi>U</mi></mrow>';
    const match=/^([A-Za-z]+)(?:_([A-Za-z]+)|(\d+))$/.exec(token);
    return match?`<msub><mi>${match[1]}</mi><${match[3]?'mn':'mi'}>${match[2]||match[3]}</${match[3]?'mn':'mi'}></msub>`:`<mi>${escapeHTML(token)}</mi>`;
  };
  function factor(){
    let value,token=tokens[cursor++];
    if(token==='('){value=`<mrow><mo>(</mo>${sum()}<mo>)</mo></mrow>`;if(tokens[cursor++]!==')')throw Error('parenthesis');}
    else if(token==='?')value='<mo>?</mo>';else if(token&&/^[A-Za-zΔ0-9]/.test(token))value=symbol(token);else throw Error('factor');
    if(tokens[cursor]==='²'){cursor++;value=`<msup>${value}<mn>2</mn></msup>`;}
    return value;
  }
  function product(){let value=factor();while(['×','*','÷','/'].includes(tokens[cursor])){const op=tokens[cursor++],right=factor();value=['÷','/'].includes(op)?`<mfrac>${value}${right}</mfrac>`:`<mrow>${value}<mo>×</mo>${right}</mrow>`;}return value;}
  function sum(){let value=product();while(['+','−'].includes(tokens[cursor])){const op=tokens[cursor++];value=`<mrow>${value}<mo>${op}</mo>${product()}</mrow>`;}return value;}
  try{
    let value=sum();while(['=','≈'].includes(tokens[cursor])){const op=tokens[cursor++];value=`<mrow>${value}<mo>${op}</mo>${sum()}</mrow>`;}
    if(cursor!==tokens.length)throw Error('remaining');
    return `<math xmlns="http://www.w3.org/1998/Math/MathML" class="mathml" dir="ltr" aria-label="${escapeHTML(notation)}">${value}</math>`;
  }catch{return bdi(notation);}
}
function circuitSymbol(q,key) {
  return key==='Req'?'R_T':key==='I'&&q.kind!=='ohm'?'I_T':key;
}
function circuitSummaryHTML(q) {
  const valueHTML=(key,value,unit)=>`<span class="circuit-value" data-circuit-key="${escapeHTML(key)}">${mathNotation(`${circuitSymbol(q,key)} = ${DC.fmt(value)}`)}<bdi>${escapeHTML(unit)}</bdi></span>`;
  const givens=Object.entries(q.givens).map(([key,value])=>valueHTML(key,displayValue(q,key,value),(q.units??units)[key[0]])).join('');
  const solved=q.steps.slice(0,q.cursor).map(step=>valueHTML(step.key,step.value,step.unit)).join('');
  const task=q.steps[q.cursor];
  return `<div class="circuit-summary" aria-label="נתוני המעגל והנעלם"><div class="circuit-summary-group" data-circuit-givens><span class="circuit-summary-label">נתונים</span><div class="circuit-values">${givens}</div></div>${solved?`<div class="circuit-summary-group" data-circuit-solved><span class="circuit-summary-label">חושב</span><div class="circuit-values">${solved}</div></div>`:''}${task?`<p class="circuit-target"><span>נדרש למצוא</span><span class="circuit-value" data-circuit-target="${escapeHTML(task.key)}">${mathNotation(`${circuitSymbol(q,task.key)} = ?`)}</span></p>`:''}</div>`;
}
function solutionHeadingHTML() {
  return '<div class="solution-head"><strong>כך פותרים</strong><button type="button" class="close" data-close-solution aria-label="סגירת הפתרון המוסבר">×</button></div>';
}
function exerciseToolsHTML(q) {
  const active=!completed(q),canHelp=active&&!q.accepted;
  const icon=(attrs,label,svg)=>`<button type="button" class="icon-button${attrs.startsWith('data-hint')?' hint-tool':''}" ${attrs} data-tooltip="${label}" aria-label="${label}">${svg}</button>`;
  const formulas=document.querySelector('.quickbar [data-open-formulas] svg').outerHTML;
  const calculator=document.querySelector('.quickbar [data-open-calculator] svg').outerHTML;
  const bulb='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.5 15.5a6 6 0 1 1 7 0L15 18H9z" fill="#f5cb58" fill-opacity=".45"/><path d="M9 21h6M12 1v1M3.5 4.5l1 1M20.5 4.5l-1 1M1 11h2M21 11h2"/></svg>';
  const triangle='<svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 2 23h17M7 14h9M12 14v9M17 23l2.8-.6L26 16.2 23.8 14 17.6 20.2zM22.5 15.3l2.2 2.2"/></svg>';
  return `<div class="answer-tools exercise-tools" role="group" aria-label="כלי עזרה לפתרון">${icon('data-open-formulas aria-haspopup="dialog" aria-controls="formula-dialog"','דף נוסחאות',formulas)}${icon(`data-open-calculator aria-haspopup="dialog" aria-controls="calculator-dialog"${q.accepted?' disabled':''}`,'מחשבון',calculator)}${canHelp?icon(`data-hint aria-expanded="${q.hint}" aria-controls="exercise-hint"`,'רמז',bulb)+`<button type="button" class="solution-tool" data-solution aria-expanded="${q.solution}" aria-controls="explained-solution">פתרון מוסבר</button>`:''}${active?icon(`data-open-manual ${currentStep()?.key==='Req'?'aria-controls="triangle-entry-note"':'aria-haspopup="dialog" aria-controls="formula-dialog"'}`,'פתירה בעזרת המשולש',triangle):''}</div>${active?'<p class="triangle-entry-note" id="triangle-entry-note" role="status" hidden></p>':''}`;
}
function annotatedReciprocalsHTML(values,factors) {
  const terms=values.map((value,i)=>`${i?'<span class="annotated-operator" aria-hidden="true">+</span>':''}<span class="annotated-term" style="--factor-width:${factors[i].join(' × ').length*7}px" data-expansion-denominator="${value}" data-expansion-factor="${factors[i].join(' × ')}"><span class="expansion-mark"><span class="expansion-factor" aria-label="גורם הרחבה: ${factors[i].join(' × ')}">${mathNotation(factors[i].join(' × '))}</span><svg class="expansion-slash" viewBox="0 0 12 18" aria-hidden="true"><path d="M1 17 L11 1" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></span>${mathNotation('1/'+value)}</span>`).join('');
  return `<div class="math"><div class="annotated-sum" role="math" aria-label="${escapeHTML('1/R_T = '+values.map(v=>'1/'+v).join(' + '))}; גורמי הרחבה מעל השברים"><span class="annotated-prefix">${mathNotation('1/R_T')}<span aria-hidden="true">=</span></span>${terms}</div></div>`;
}
let resistanceSolutionMethod='fractions';
function parallelResistanceSolutionHTML(q,step) {
  if(q.kind!=='parallel'||q.resistances.length<2||q.resistances.length>3||step.key!=='Req')return '';
  const gcd=(a,b)=>{while(b){[a,b]=[b,a%b];}return a;};
  // Work exactly with the resistance values and units shown in the question.
  const fractions=q.resistances.map(r=>{
    const [whole,decimal='']=DC.fmt(displayValue(q,'R',r)).split('.');
    const n=BigInt(whole+decimal),d=10n**BigInt(decimal.length),g=gcd(n,d);
    return {n:n/g,d:d/g};
  });
  const denominator=fractions.reduce((a,r)=>a/gcd(a,r.n)*r.n,1n);
  const numerators=fractions.map(r=>r.d*(denominator/r.n));
  const total=numerators.reduce((a,b)=>a+b,0n),g=gcd(denominator,total);
  const resultN=denominator/g,resultD=total/g;
  const stage=(caption,equation,unit='')=>`<div class="solution-step"><p>${caption}</p><div class="math">${mathNotation(equation)}${unit?' '+bdi(unit):''}</div></div>`;
  const reciprocal='1/R_T',values=q.resistances.map(r=>DC.fmt(displayValue(q,'R',r)));
  const methods=`<div class="solution-methods" role="group" aria-label="דרך החישוב של ההתנגדות השקולה"><button type="button" class="level" data-resistance-method="fractions" aria-pressed="${resistanceSolutionMethod==='fractions'}">דרך א׳ — מכנה משותף</button><button type="button" class="level" data-resistance-method="decimal" aria-pressed="${resistanceSolutionMethod==='decimal'}">דרך ב׳ — שבר עשרוני</button></div>`;
  const finalEquals=resultN*100n%resultD===0n?'=':'≈';
  const multiply=list=>list.reduce((a,r)=>({n:a.n*r.n,d:a.d*r.d}),{n:1n,d:1n});
  const add=list=>list.reduce((a,r)=>({n:a.n*r.d+r.n*a.d,d:a.d*r.d}),{n:0n,d:1n});
  // Products and sums of the given finite decimals remain exact finite decimals.
  const exactDecimal=({n,d})=>{
    let text=String(n/d),remainder=n%d;
    if(remainder){text+='.';while(remainder){remainder*=10n;text+=String(remainder/d);remainder%=d;}}
    return text;
  };
  if(values.every(value=>value===values[0])){
    return stage('1. בנגדים זהים במקביל מחלקים את התנגדות הנגד במספר הנגדים:', 'R_T = R/n')
      +stage(`2. יש ${values.length} נגדים זהים, ולכן מציבים:`, `R_T = ${values[0]}/${values.length}`)
      +stage(finalEquals==='='?'3. התוצאה:':'3. מעגלים רק את התוצאה הסופית לשתי ספרות אחרי הנקודה:',`R_T ${finalEquals} ${DC.fmt(step.value)}`,step.unit);
  }
  if(values.length===2){
    const product=exactDecimal(multiply(fractions)),sum=exactDecimal(add(fractions));
    return stage('1. לשני נגדים שונים במקביל משתמשים במכפלה חלקי סכום:', 'R_T = (R1 × R2)/(R1 + R2)')
      +stage('2. מציבים את ההתנגדויות באותה יחידה:',`R_T = (${values[0]} × ${values[1]})/(${values[0]} + ${values[1]})`)
      +stage('3. מחשבים את המכפלה ואת הסכום:',`R_T = ${product}/${sum}`)
      +stage(finalEquals==='='?'4. התוצאה:':'4. מעגלים רק את התוצאה הסופית לשתי ספרות אחרי הנקודה:',`R_T ${finalEquals} ${DC.fmt(step.value)}`,step.unit);
  }

  if(resistanceSolutionMethod==='decimal'){
    const decimal=n=>n.toFixed(10).replace(/\.?0+$/,'');
    const reciprocals=values.map(r=>1/Number(r)),sum=reciprocals.reduce((a,b)=>a+b,0);
    const shown=reciprocals.map(decimal),sumText=decimal(sum),precision=10n**10n;
    const exactTerms=fractions.every(r=>r.d*precision%r.n===0n),exactSum=total*precision%denominator===0n;
    let out=methods+'<p class="small muted">הסימן ≈ מציין קירוב. מספרים עשרוניים ארוכים מוצגים כאן בקיצור; בחישוב שומרים על הדיוק המלא עד לתוצאה הסופית.</p>';
    out+=stage('1. כותבים את הנוסחה:',`${reciprocal} = ${values.map((_,i)=>'1/R'+(i+1)).join(' + ')}`);
    out+='<div class="solution-step"><p>2. מחלקים 1 בכל התנגדות ומקבלים את ההופכי כשבר עשרוני:</p>'+values.map((r,i)=>`<div class="math">${mathNotation(`1/R${i+1} = 1/${r} ${fractions[i].d*precision%fractions[i].n===0n?'=':'≈'} ${shown[i]}`)}</div>`).join('')+'</div>';
    out+=`<div class="solution-step"><p>3. מחברים את ההופכיים:</p><div class="decimal-addition" role="math" aria-label="${escapeHTML(shown.join(' + '))} ${exactTerms&&exactSum?'=':'≈'} ${sumText}" data-decimal-sum="${shown.join('+')}">${shown.map((n,i)=>`<div><span aria-hidden="true">${i?'+':''}</span>${bdi(n)}</div>`).join('')}<div class="decimal-total"><span>${exactTerms&&exactSum?'=':'≈'}</span>${bdi(sumText)}</div></div><div class="math">${mathNotation(`${reciprocal} ${exactSum?'=':'≈'} ${sumText}`)}</div></div>`;
    out+=stage('4. מחלקים 1 בסכום כדי לקבל את ההתנגדות השקולה:',`R_T ${exactSum?'=':'≈'} 1/${sumText}`);
    out+=stage(finalEquals==='='?'5. התוצאה:':'5. מעגלים את התוצאה הסופית לשתי ספרות אחרי הנקודה:',`R_T ${finalEquals} ${DC.fmt(step.value)}`,step.unit);
    return out;
  }
  const otherIndices=values.map((_,i)=>values.map((_,j)=>j).filter(j=>j!==i));
  otherIndices[2].reverse();
  const factors=otherIndices.map(indices=>indices.map(i=>values[i]));
  const products=otherIndices.map(indices=>multiply(indices.map(i=>fractions[i])));
  const productTexts=products.map(exactDecimal),productDenominator=exactDecimal(multiply(fractions)),sumNumerator=exactDecimal(add(products));
  const denominatorExpression=values.join(' × '),numeratorExpression=factors.map(list=>list.join(' × ')).join(' + ');
  let out=methods+stage('1. כותבים את נוסחת שלושת הענפים במקביל:',`${reciprocal} = 1/R1 + 1/R2 + 1/R3`);
  out+=`<div class="solution-step"><p>2. מציבים את ההתנגדויות באותה יחידה. מעל כל שבר מסמנים את שני המכנים האחרים — בהם מכפילים גם את המונה וגם את המכנה:</p>${annotatedReciprocalsHTML(values,factors)}</div>`;
  out+=stage('3. המכנה המשותף הוא מכפלת שלושת המכנים. מחברים את המונים שהתקבלו:',`${reciprocal} = (${numeratorExpression})/(${denominatorExpression})`);
  out+=`<div class="solution-step"><p>4. מחשבים את המכפלות ואת סכום המונים:</p><div class="math">${mathNotation(`${reciprocal} = (${productTexts.join(' + ')})/${productDenominator}`)}</div><div class="math">${mathNotation(`${reciprocal} = ${sumNumerator}/${productDenominator}`)}</div></div>`;
  out+=stage('5. הופכים את השבר: המונה והמכנה מחליפים מקום, ומקבלים את ההתנגדות השקולה:',`R_T = ${productDenominator}/${sumNumerator}`);
  out+=stage(finalEquals==='='?'6. התוצאה:':'6. מעגלים רק את התוצאה הסופית לשתי ספרות אחרי הנקודה:',`R_T ${finalEquals} ${DC.fmt(step.value)}`,step.unit);
  return out;
}
function explainedSolutionHTML(q,step) {
  return parallelResistanceSolutionHTML(q,step)||`<div class="math">${mathNotation(step.formula)}</div><div class="math">${mathNotation(step.substitution)} = ${DC.fmt(step.value)} ${step.unit}</div><p>${escapeHTML(step.explanation)}</p>`;
}
function trianglePreview(definition) {
  const symbols=definition.slots.map(slot=>slot.symbol);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" role="img" aria-label="משולש ${escapeHTML(definition.title)}: ${symbols[0]} למעלה, ${symbols[1]} ו־${symbols[2]} למטה"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#526f62" stroke-width="3"/><path d="M65 125 L195 125 M130 125 L130 218" fill="none" stroke="#526f62" stroke-width="2"/><g fill="#182e3c" font-family="Arial,sans-serif" font-size="33" font-weight="700" text-anchor="middle" direction="ltr"><text x="130" y="96">${symbols[0]}</text><text x="80" y="183">${symbols[1]}</text><text x="181" y="183">${symbols[2]}</text></g></svg>`;
}
function diagramPreview(q, options = {}) {
  return `<button type="button" class="diagram-preview" data-open-diagram="${options.complete ? 'simulator' : 'exercise'}" aria-label="פתיחת הסכמה להגדלה">${q.custom ? customCircuitSVG(q, options) : circuitSVG(q, options)}<span class="diagram-open-label">הגדלת הסכמה ⤢</span></button>`;
}
function openDiagram(source) {
  diagramReturnToFormulas=$('formula-dialog').open;
  diagramReturnFieldId=diagramReturnToFormulas?manualKeypadFieldId:null;
  diagramReturnScroll=diagramReturnToFormulas?$('formula-dialog').scrollTop:0;
  diagramZoom = 1;
  $('diagram-dialog').classList.toggle('dark-diagram',source==='simulator');
  const q = source === 'simulator' ? activeSimulatorQuestion() : currentQuestion();
  $('diagram-context').innerHTML=source==='simulator'?'':circuitSummaryHTML(q);
  $('diagram-canvas').innerHTML = (q.custom ? customCircuitSVG : circuitSVG)(q, source === 'simulator' ? { complete:true, voltage:q.simVoltage, animate:q.simAnimate } : {});
  diagramBaseWidth = q.custom && q.resistances.length > 3 ? Number($('diagram-canvas').querySelector('svg').getAttribute('viewBox').split(/\s+/)[2]) : 0;
  if (diagramBaseWidth) $('diagram-canvas').querySelector('svg').style.width = '100%';
  $('diagram-canvas').style.width = '100%';
  openDialog('diagram-dialog');
  zoomDiagram('reset');
}
function zoomDiagram(action) {
  const viewport = $('diagram-viewport'), previousZoom = diagramZoom;
  diagramZoom = action === 'reset' ? 1 : Math.max(1, Math.min(4, diagramZoom + (action === 'in' ? .5 : -.5)));
  const centerX = (viewport.scrollLeft + viewport.clientWidth / 2) / previousZoom;
  const centerY = (viewport.scrollTop + viewport.clientHeight / 2) / previousZoom;
  $('diagram-canvas').style.width = diagramBaseWidth ? (diagramBaseWidth * diagramZoom) + 'px' : (diagramZoom * 100) + '%';
  $('diagram-zoom-label').textContent = (diagramZoom * 100) + '%';
  document.querySelector('[data-diagram-zoom="out"]').disabled = diagramZoom === 1;
  document.querySelector('[data-diagram-zoom="in"]').disabled = diagramZoom === 4;
  fitDialogs();
  viewport.scrollLeft = action === 'reset' ? 0 : centerX * diagramZoom - viewport.clientWidth / 2;
  viewport.scrollTop = action === 'reset' ? 0 : centerY * diagramZoom - viewport.clientHeight / 2;
}
function contextTitle(q, step) {
  if (!step) return 'המעגל הושלם';
  if (q.kind === 'ohm') return 'מעגל עם נגד יחיד';
  const match = /^[UIP](\d)$/.exec(step.key);
  return match ? `רכיב R${match[1]}${q.kind === 'parallel' ? ` בענף ${match[1]}` : ' במעגל הטורי'}` : 'המעגל כולו';
}
function selectTab(next) {
  window.CourseApp?.showPractice();
  qaAnswerVisible=false;
  viewTab=next;
  if(DC.kinds.includes(next)){tab=next;feedback='';}
  render();
}
function completedCircuits() {
  return DC.kinds.flatMap(kind=>questions[kind].flatMap((list,level)=>list.flatMap((q,index)=>simulationReady(q)?[{q,id:`${kind}:${level}:${index}`,label:`${names[kind]} · רמה ${letters[level]} · תרגיל ${index+1}`}]:[])));
}
function exerciseLocation() { return {kind:tab,level:levels[tab],index:positions[tab][levels[tab]]}; }
function previousSolvedExercise() {
  const here=exerciseLocation();
  return completedCircuits().filter(item=>{
    const [kind,level,index]=item.id.split(':');
    return kind===here.kind&&(Number(level)<here.level||Number(level)===here.level&&Number(index)<here.index);
  }).at(-1);
}
function showExercise(location) {
  if(!questions[location.kind]?.[location.level]?.[location.index])return;
  if($('formula-dialog').open)$('formula-dialog').close();hideManualKeypad();
  qaAnswerVisible=false;tab=location.kind;viewTab=tab;levels[tab]=location.level;positions[tab][location.level]=location.index;
  feedback='';feedbackType='success';render(true);
  requestAnimationFrame(()=>{
    const grid=$('workspace').querySelector('.exercise-grid');
    if(completed(currentQuestion())){const heading=grid?.querySelector('.success-summary h2');if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}}
    ($('workspace').querySelector('.exercise-navigation')??grid)?.scrollIntoView({block:'start'});
  });
}
function reviewSolvedExercise(id) {
  const item=completedCircuits().find(item=>item.id===id);if(!item)return;
  reviewReturn??=exerciseLocation();
  const [kind,level,index]=item.id.split(':');
  showExercise({kind,level:Number(level),index:Number(index)});
}
function resumeExercise() {
  if(!reviewReturn)return;
  const back=reviewReturn;reviewReturn=null;showExercise(back);
}
function exerciseNavigationHTML() {
  if(qaActive)return '';
  const circuits=completedCircuits();if(!circuits.length)return '';
  const here=exerciseLocation(),id=`${here.kind}:${here.level}:${here.index}`,previous=previousSolvedExercise();
  const options=circuits.map(item=>`<option value="${item.id}"${item.id===id?' selected':''}>${escapeHTML(item.label)}</option>`).join('');
  return `<nav class="exercise-navigation" aria-label="מעבר בין תרגילים"><button class="btn secondary tiny" data-previous-solved${previous?'':' disabled'}>תרגיל קודם →</button><label class="solved-picker" for="solved-exercises"><span class="small">תרגילים שנפתרו</span><select id="solved-exercises"><option value="">בחירת תרגיל פתור</option>${options}</select></label>${reviewReturn?'<button class="btn secondary tiny" data-resume-exercise>חזרה לתרגול הנוכחי</button>':''}</nav>`;
}
function activeSimulatorQuestion() { return simulatorMode==='custom' ? customSimulator : simulatorQuestion ?? currentQuestion(); }
function formatCustomNumber(value) { return CoursePractice.simulationNumber(value); }
function simulatorNumber(q,value) { return CoursePractice.simulationNumber(value); }
function simulatorQuantity(q,key,value) { return `${simulatorNumber(q,displayValue(q,key,value))} ${(q.units??units)[key==='Req'?'R':key[0]]}`; }
function customBuilderHTML() {
  const rows=customDraft.resistances.map((value,index)=>`<div class="custom-resistor"><div class="custom-field"><label for="custom-r-${index}">${bdi('R'+(index+1))} · התנגדות ${bdi('Ω')}</label><input id="custom-r-${index}" class="numeric" type="text" inputmode="decimal" maxlength="24" data-custom-resistance="${index}" value="${escapeHTML(value)}"></div><button class="btn secondary tiny" data-remove-resistor="${index}" ${customDraft.resistances.length===1?'disabled':''} aria-label="הסרת נגד R${index+1}">הסרה</button></div>`).join('');
  return `<section class="card"><h2>בניית מעגל משלכם</h2><div class="custom-fields"><div class="custom-field"><label for="custom-kind">סוג המעגל</label><select id="custom-kind"><option value="series"${customDraft.kind==='series'?' selected':''}>טורי</option><option value="parallel"${customDraft.kind==='parallel'?' selected':''}>מקבילי</option></select></div><div class="custom-field"><label for="custom-voltage">מתח מקור התחלתי ${bdi('V')}</label><input id="custom-voltage" class="numeric" type="text" inputmode="decimal" maxlength="24" value="${escapeHTML(customDraft.voltage)}"></div></div><div id="custom-resistors" class="custom-resistors">${rows}</div><div class="custom-actions"><button class="btn" data-add-resistor>+ הוספת ${customDraft.kind==='parallel'?'ענף / נגד':'נגד'}</button><span class="small muted">${customDraft.resistances.length} ${customDraft.kind==='parallel'?'ענפים':'נגדים'}</span></div><p class="custom-sim-note">כל נגד במקביל נמצא בענף נפרד. אפשר להוסיף ולהסיר נגדים; החישוב מתעדכן עם שינוי הערכים.</p><div id="custom-error" class="feedback error" role="status" hidden></div></section><div id="custom-output"></div>`;
}
function customNumber(text) {
  const raw=String(text).trim().replace(',','.');
  return /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(raw)?Number(raw):NaN;
}
function recalculateCustom() {
  const voltage=customNumber(customDraft.voltage),resistances=customDraft.resistances.map(customNumber);
  const badVoltage=!Number.isFinite(voltage)||voltage<0;
  const badResistance=resistances.map(value=>!Number.isFinite(value)||value<=0);
  const setInvalid=(node,bad)=>{if(!node)return;if(bad)node.setAttribute('aria-invalid','true');else node.removeAttribute('aria-invalid');};
  setInvalid($('custom-voltage'),badVoltage);badResistance.forEach((bad,i)=>setInvalid($('custom-r-'+i),bad));
  let error=badVoltage?'יש להזין מתח מספרי של אפס וולט ומעלה.':badResistance.some(Boolean)?'יש להזין לכל נגד התנגדות מספרית גדולה מאפס.':'';
  if(!error) {
    const model=DC.physics(customDraft.kind,voltage,resistances);
    if(!Number.isFinite(model.req)||model.req<=0||![model.total,model.power,...model.currents,...model.drops,...model.powers].every(Number.isFinite))error='הערכים חורגים מטווח החישוב. יש להזין ערכים קטנים יותר.';
  }
  $('custom-error').hidden=!error;$('custom-error').textContent=error;$('custom-output').hidden=!!error;
  if(error){resizeFrame();return;}
  const sourceChanged=customSimulator.voltage!==voltage;
  customSimulator={...customSimulator,custom:true,kind:customDraft.kind,voltage,resistances,lamps:resistances.map(()=>false),givens:{},simVoltage:sourceChanged?voltage:customSimulator.simVoltage,simAnimate:personal.preferences.motion?false:customSimulator.simAnimate};
  $('custom-output').innerHTML=simulatorHTML(customSimulator);
  fitDialogs();resizeFrame();
}
function renderSimulatorPanel() {
  const modes=`<div class="sim-modes" role="group" aria-label="סוג הסימולטור"><button class="level" data-sim-mode="custom" aria-pressed="${simulatorMode==='custom'}">בניית מעגל משלכם</button><button class="level" data-sim-mode="exercise" aria-pressed="${simulatorMode==='exercise'}">מעגל מתוך התרגול</button></div>`;
  if(simulatorMode==='custom'){$('simulator-workspace').innerHTML=modes+customBuilderHTML();recalculateCustom();return;}
  const circuits=completedCircuits();
  if(!circuits.some(item=>item.q===simulatorQuestion))simulatorQuestion=circuits[0]?.q??null;
  if(!simulatorQuestion){$('simulator-workspace').innerHTML=modes+`<section class="card"><h2>מעגל מתוך התרגול</h2><p>לאחר השלמת תרגיל, לחצו על כפתור הסימולטור שלו כדי להציג אותו כאן. אפשר גם לבנות מעגל משלכם ללא השלמת תרגיל.</p><button class="btn secondary" data-return-training>חזרה לתרגול</button></section>`;return;}
  const options=circuits.map(item=>`<option value="${item.id}"${item.q===simulatorQuestion?' selected':''}>${item.label}</option>`).join('');
  $('simulator-workspace').innerHTML=modes+`<div class="sim-choice"><label for="sim-circuit">המעגל להצגה</label><select id="sim-circuit">${options}</select><button class="btn secondary tiny" data-return-training>חזרה לתרגול</button></div>`+simulatorHTML(simulatorQuestion);
}
function render(focus = false) {
  if(window.CourseApp?.renderOverride(focus))return;
  hideIconTooltip();
  renderQA();
  document.querySelectorAll('[role="tab"][data-tab]').forEach(button=>{const active=button.dataset.tab===viewTab;button.setAttribute('aria-selected',active);button.tabIndex=active?0:-1;});
  $('workspace').hidden=viewTab==='simulator';$('simulator-workspace').hidden=viewTab!=='simulator';
  if(viewTab==='simulator'){renderSimulatorPanel();renderProgress();fitDialogs();resizeFrame();saveCourse();return;}
  $('simulator-workspace').innerHTML='';
  const level = levels[tab], sequence = questions[tab][level], index = positions[tab][level], q = sequence[index], done = completed(q), step = currentStep();
  if(reviewReturn&&reviewReturn.kind===tab&&reviewReturn.level===level&&reviewReturn.index===index)reviewReturn=null;
  if(q.accepted){feedbackType='success';feedback=acceptedMessage(q);}
  const doneCount = sequence.filter(completed).length;
  $('workspace').setAttribute('aria-labelledby', 'tab-' + tab);
  const levelButtons = questions[tab].map((list, j) => `<button class="level" data-level="${j}" aria-pressed="${j === level}">רמה ${letters[j]}<small>${DC.levelNames[j]} · ${list.filter(completed).length}/${list.length}</small></button>`).join('');
  const given = Object.entries(q.givens).map(([key, value]) => `<div class="given"><small>${key === 'U' ? 'מתח המקור' : key === 'I' ? 'זרם נתון' : key === 'P' ? 'הספק נתון' : /^R\d/.test(key) ? `התנגדות ${key}${q.lamps[Number(key.slice(1)) - 1] ? ' · נורה' : ''}` : 'התנגדות נתונה'}</small>${bdi(`${key} = ${quantity(q,key,value)}`)}</div>`).join('');
  const dots = sequence.map((item, j) => `<span class="question-dot ${completed(item) ? 'done' : j === index ? 'current' : ''}" aria-label="תרגיל ${j + 1}: ${completed(item) ? 'הושלם' : j === index ? 'נוכחי' : 'בהמשך'}"></span>`).join('');
  const stepPills = q.steps.map((s, j) => `<span class="step-pill ${j < q.cursor ? 'done' : j === q.cursor ? 'active' : ''}" title="${escapeHTML(s.label)}">${j < q.cursor ? '✓' : j + 1}</span>`).join('');
  const rounding = level === 0 ? 'ברמה הזאת כל התוצאות שלמות. אין צורך להקליד יחידות.' : 'יש לעגל את התשובה לשתי ספרות אחרי הנקודה לכל היותר. אפשר לכתוב נקודה או פסיק.';
  const rows = q.steps.slice(0, q.cursor).map((s, j) => `<div class="completed-row"><span>✓ ${escapeHTML(s.label)}${q.help[j] ? ' · בעזרת פתרון' : ''}</span>${bdi(`${DC.fmt(s.value)} ${s.unit}`)}</div>`).join('');
  const active = done ? `<div class="complete-badge">✓ התרגיל הושלם</div><h2>השלמתם את כל החישובים.</h2><p class="muted">${q.steps.length > 1 ? 'אפשר לעבור על התוצאות ולבדוק איך הן קשורות זו לזו.' : 'הקשר בין הנתונים ברור יותר עם כל תרגיל.'}</p>`
    : `<div class="step-list" aria-label="התקדמות שלבי הפתרון">${stepPills}</div><div class="task-kicker">צעד ${q.cursor + 1} מתוך ${q.steps.length} · ${escapeHTML(contextTitle(q, step))}</div><h2 id="answer-title">${escapeHTML(step.label)}</h2><form id="answer-form" novalidate><label class="small muted" for="answer">מה התוצאה, ביחידות ${bdi(step.unit)}?</label><div class="answer-row"><div class="answer-wrap"><input class="numeric${q.accepted?' answer-correct':q.attempts>0?' answer-incorrect':''}" id="answer" data-answer type="text" inputmode="decimal" autocomplete="off" maxlength="24" value="${escapeHTML(q.draft)}"${q.accepted?' readonly':''} aria-describedby="rounding-text form-feedback"><span class="unit" aria-hidden="true">${bdi(step.unit)}</span></div>${q.accepted?'<button class="btn" type="button" data-next-step>הבא ←</button>':'<button class="btn" type="submit">בדיקת תשובה</button>'}</div></form>`;
  const explain = !done && q.solution ? `<div class="solution" id="explained-solution">${solutionHeadingHTML()}${explainedSolutionHTML(q,step)}<p>הקלידו את התוצאה כדי להמשיך לצעד הבא.</p></div>` : '';
  const hints = !done && q.hint ? `<div class="hint" id="exercise-hint"><strong>כיוון לפתרון</strong>${escapeHTML(step.hint)}<div class="math" style="margin-top:8px">${mathNotation(step.formula)}</div></div>` : '';
  const tools = exerciseToolsHTML(q);
  const next = done ? `<div class="completion-actions">${index < sequence.length - 1 ? '<button class="btn" data-next-question>לתרגיל הבא ←</button>' : level < questions[tab].length - 1 ? '<button class="btn" data-next-level>לרמה הבאה ←</button>' : '<button class="btn" data-new-course>סבב חדש</button>'}</div>${doneCount === sequence.length ? `<div class="level-note">השלמתם את ${sequence.length} התרגילים ברמה ${letters[level]}. ${level < questions[tab].length - 1 ? 'אפשר להתקדם לרמה הבאה.' : 'אפשר לעבור ללשונית אחרת או להתחיל סבב חדש.'}</div>` : ''}` : '';
  const descriptions = { ohm:'מתחילים בנתונים ידועים ומוצאים את הערך החסר.', series:'בטור הזרם זהה בכל הרכיבים. המתח מתחלק ביניהם.', parallel:'' };
  $('workspace').innerHTML = `<div class="course-head"><div><h2>${names[tab]}</h2>${descriptions[tab]?`<p class="muted small" style="margin:0">${descriptions[tab]}</p>`:''}</div><div class="levels" aria-label="רמות תרגול">${levelButtons}</div></div><div class="progress-row"><span>תרגיל ${index + 1} מתוך ${sequence.length} · רמה ${letters[level]}</span><div class="question-dots">${dots}</div></div>${exerciseNavigationHTML()}<div class="progress-track" role="progressbar" aria-label="תרגילים שהושלמו ברמה" aria-valuemin="0" aria-valuemax="${sequence.length}" aria-valuenow="${doneCount}"><div style="width:${doneCount / sequence.length * 100}%"></div></div><div class="exercise-grid"><section class="card"><div class="exercise-title"><div class="eyebrow">הנתונים שלכם</div><h3 style="margin-top:6px">${q.title}</h3><p class="muted small" style="margin:0">${tab === 'ohm' ? 'המקור הוא מקור מתח ישר (DC). מצאו את הנעלם המבוקש.' : 'כל ההתנגדויות ומתח המקור נתונים. פתרו לפי הסדר.'}</p></div><div class="givens">${given}</div>${unitNote(q)}<figure class="diagram">${diagramPreview(q)}<figcaption>${q.lamps.some(Boolean) ? 'סימון עיגול עם X הוא נורה. בתרגול הנורה היא רכיב בעל התנגדות קבועה.' : 'מלבן הוא נגד. המקור הוא DC; U מציין מתח ו־I מציין זרם.'}${tab !== 'ohm' ? ' לאחר השלמת המעגל אפשר לפתוח אותו בלשונית הסימולטור. לחצו על הסכמה להגדלה.' : ''}</figcaption></figure>${simulationReady(q) ? '<button class="btn sim-jump" data-go-simulator>סימולטור</button>' : ''}</section><section class="card ${done ? 'success-summary' : ''}">${active}<p id="rounding-text" class="rounding">${rounding}</p>${tools}<div class="feedback ${feedbackType}" id="form-feedback" role="status" aria-live="polite">${escapeHTML(feedback)}</div>${hints}${explain}${q.cursor ? `<div class="completed-steps"><strong class="small">החישובים שהשלמתם</strong>${rows}</div>` : ''}${next}</section></div>`;
  if ($('formula-dialog').open) renderFormulas();
  if (focus && !done) requestAnimationFrame(() => {if($('formula-dialog').open&&formulaView==='manual')focusManualEntry();else ($('formula-dialog').open ? formulaAnswerField() : q.accepted ? $('workspace').querySelector('[data-next-step]') : $('answer'))?.focus();});
  renderProgress(); fitDialogs(); resizeFrame();saveCourse();
}
function acceptedMessage(q = currentQuestion()) {
  const step=q.steps[q.cursor];
  return `נכון. ${DC.fmt(step.value)} ${step.unit}. לחצו על הבא כדי להמשיך.`;
}
function nextStep() {
  const q=currentQuestion();
  if(!q.accepted)return;
  if($('formula-dialog').open)$('formula-dialog').close();
  hideManualKeypad();
  q.cursor++;q.accepted=false;q.draft='';q.attempts=0;q.hint=false;q.solution=false;
  if(completed(q)) {
    const sequence=questions[tab][levels[tab]];
    if(positions[tab][levels[tab]]<sequence.length-1)positions[tab][levels[tab]]++;
    else if(levels[tab]<questions[tab].length-1)levels[tab]++;
  }
  feedback='';feedbackType='success';render(true);
  requestAnimationFrame(()=>($('workspace').querySelector('.exercise-navigation')??$('workspace').querySelector('.exercise-grid'))?.scrollIntoView({block:'start'}));
}
function checkAnswer(value, mode = 'answer') {
  const q = currentQuestion(), step = currentStep();
  if (!step || q.accepted) return;
  q.draft = value;
  const correct = DC.accepted(value,step.value);
  recordAttempt(correct,mode);
  if (!correct) {
    q.attempts++; feedbackType = 'error';
    feedback = value.trim() ? 'לא נכון. בדקו את הנוסחה ואת סדר פעולות החשבון. אפשר להיעזר ברמז ובמחשבון.' : 'יש להקליד תשובה מספרית. אפשר להתחיל ברמז או בדף הנוסחאות.';
    q.hint = true; markHelp();
    if (q.attempts >= 3) { q.solution = true; q.help[q.cursor] = true; }
    render(true);
    document.querySelectorAll('[data-answer]').forEach(field => field.setAttribute('aria-invalid', 'true'));
    return;
  }
  q.accepted=true;q.attempts=0;q.hint=false;q.solution=false;
  feedbackType='success';feedback=acceptedMessage(q);
  const state=manualState();state.message=feedback;state.type='success';state.errors=[];
  render(true);
}
function syncDraft(value, source) {
  if(window.CourseApp?.syncFormulaDraft(value,source))return;
  if(currentQuestion().accepted)return;
  currentQuestion().draft = value;
  document.querySelectorAll('[data-answer]').forEach(field => { if (field !== source) field.value = value; field.removeAttribute('aria-invalid');field.classList.remove('answer-incorrect'); });
  saveCourse();
}
function simulatorHTML(q) {
  return `<section class="card simulator${q.custom?' custom-simulator':''}" id="simulator-section" aria-labelledby="sim-title"><div class="sim-head"><div><div class="eyebrow">אחרי החישוב — רואים את המעגל</div><h2 id="sim-title" tabindex="-1" style="margin:5px 0">סימולטור DC</h2></div><button class="btn secondary tiny" data-open-formulas>דף נוסחאות △</button></div><div class="sim-layout"><div><figure class="diagram" id="sim-diagram">${diagramPreview(q, { complete:true, voltage:q.simVoltage, animate:q.simAnimate })}</figure>${q.custom&&q.resistances.length>3?'<p class="small muted">אפשר לגלול את הסכמה לצדדים או לפתוח אותה בהגדלה.</p>':''}<div class="sim-legend"><span class="current">→ I — זרם</span><span class="voltage">ΔU — חץ לכיוון הפלוס</span><span>רכיבים ונתונים נוספים — לבן</span></div><div id="sim-metrics">${simMetrics(q)}</div></div><div class="sim-controls"><label for="sim-voltage">שינוי מתח המקור</label><div class="sim-value" id="sim-voltage-label">${bdi(`${simulatorNumber(q,q.simVoltage)} V`)}</div><input id="sim-voltage" type="range" min="0" max="${q.voltage * 2}" step="0.1" value="${q.simVoltage}" aria-describedby="sim-note"><label class="toggle"><input id="sim-animation" type="checkbox" ${personal.preferences.motion ? 'disabled' : ''} ${q.simAnimate ? 'checked' : ''}>הנפשת מסלול הזרם</label><button class="btn secondary tiny" data-reset-simulator>חזרה למתח התרגיל</button><p class="small muted" id="sim-note" style="margin:6px 0 0">החצים מציגים זרם מוסכם: מהפלוס אל המינוס דרך המעגל החיצוני. הבהירות ממחישה את ההספק בנורה בעלת התנגדות קבועה. שינוי המתח כאן אינו משנה את תשובות התרגיל.</p></div></div></section>`;
}
function simMetrics(q) {
  const m = DC.physics(q.kind, q.simVoltage, q.resistances);
  return `<div class="metrics"><div class="metric"><small>נגד שקול</small>${bdi(`${simulatorQuantity(q,'R',m.req)}`)}</div><div class="metric"><small>זרם כולל</small>${bdi(`${simulatorQuantity(q,'I',m.total)}`)}</div><div class="metric"><small>הספק כולל</small>${bdi(`${simulatorQuantity(q,'P',m.power)}`)}</div></div><div class="table-scroll"><table><caption class="small muted" style="text-align:right;margin-bottom:5px">נתוני המעגל במתח שנבחר בסימולטור</caption><thead><tr><th>רכיב</th><th>התנגדות</th><th>מתח</th><th>זרם</th><th>הספק</th></tr></thead><tbody>${q.resistances.map((r,j) => `<tr><td data-label="רכיב">${bdi('R' + (j+1))}${q.lamps[j] ? ' · נורה' : ''}</td><td data-label="התנגדות">${bdi(`${simulatorQuantity(q,'R',r)}`)}</td><td data-label="מתח">${bdi(`${simulatorQuantity(q,'U',m.drops[j])}`)}</td><td data-label="זרם">${bdi(`${simulatorQuantity(q,'I',m.currents[j])}`)}</td><td data-label="הספק">${bdi(`${simulatorQuantity(q,'P',m.powers[j])}`)}</td></tr>`).join('')}</tbody></table></div>`;
}
function updateSimulator() {
  const q = activeSimulatorQuestion();
  if (!$('sim-diagram')) return;
  $('sim-diagram').innerHTML = diagramPreview(q, { complete:true, voltage:q.simVoltage, animate:q.simAnimate });
  $('sim-metrics').innerHTML = simMetrics(q);
  $('sim-voltage-label').innerHTML = bdi(`${simulatorNumber(q,q.simVoltage)} V`);
  $('sim-voltage').value = q.simVoltage; $('sim-animation').checked = q.simAnimate; $('sim-animation').disabled = personal.preferences.motion;
  saveCourse();
}

function triangleContext() {
  const specialized=window.CourseApp?.triangleContext();if(specialized)return specialized;
  const q = currentQuestion(), task = currentStep(), model = DC.physics(q.kind, q.voltage, q.resistances);
  const finished = new Set(q.steps.slice(0, q.cursor).map(step => step.key));
  let values = {}, target = task?.key, label;
  if (q.kind === 'ohm') {
    values = { ...q.givens };
    q.steps.slice(0, q.cursor).forEach(step => { values[step.key] = physicalValue(q,step.key,step.value); });
    label = 'הנגד היחיד במעגל';
  } else if (!task || task.key === 'I' || task.key === 'Req') {
    values = { U:q.voltage, R:completed(q) || finished.has('Req') ? model.req : undefined,
      I:completed(q) || finished.has('I') ? model.total : undefined, P:completed(q) ? model.power : undefined };
    label = 'המעגל כולו — R כאן הוא הנגד השקול';
  } else {
    const j = Number(task.key.slice(1)) - 1;
    values = { R:q.resistances[j], U:q.kind === 'parallel' || finished.has('U' + (j + 1)) ? model.drops[j] : undefined,
      I:q.kind === 'series' ? (finished.has('I') ? model.total : undefined) : (finished.has('I' + (j + 1)) ? model.currents[j] : undefined),
      P:finished.has('P' + (j + 1)) ? model.powers[j] : undefined };
    target = task.key[0]; label = `רכיב R${j + 1}${q.kind === 'parallel' ? ` בענף ${j + 1}` : ' במעגל הטורי'}`;
  }
  for (const key of Object.keys(values)) values[key]=displayValue(q,key,values[key]);
  if (values.I !== undefined) values.I2 = values.I * values.I;
  if (values.U !== undefined) values.U2 = values.U * values.U;
  return { values, target, label, task, q };
}
function formulaQuestion() { return window.CourseApp?.formulaQuestion()??currentQuestion(); }
function formulaListKeys() { return triangleContext().listKeys??['U','R','I','P']; }
function formulaDefinitions(context=triangleContext()) {
  const ids=context.definitionIds??['ohm','power-ui','power-ir','power-ur'];
  return triangleDefinitions.filter(item=>ids.includes(item.id));
}
function saveFormulaWork() { saveCourse();window.CourseApp?.saveFormulaWork(); }
function markFormulaHelp() { if(!window.CourseApp?.markFormulaHelp())markHelp(); }
function finishFormulaRender() { window.CourseApp?.decorateFormulas();fitDialogs();resizeFrame(); }
function manualState() {
  const q = formulaQuestion();
  q.manualWork ??= {};
  return q.manualWork[q.cursor] ??= { list:Object.fromEntries(formulaListKeys().map(key=>[key,''])), selected:'', drafts:{}, message:'', type:'error', errors:[], listStatus:'' };
}
function manualDraft(state = manualState()) {
  return state.drafts[state.selected] ??= { values:{} };
}
function manualResultSlotKey() {
  const target=triangleContext().target;
  const definition=triangleDefinitions.find(item=>item.id===manualState().selected);
  return definition?.slots.some(slot=>slot.key===target)?target:null;
}
function renderCalculatorTriangleReference() {
  const panel=$('calc-triangle-reference'),dialog=$('calculator-dialog');
  const q=formulaQuestion(),state=q.manualWork?.[q.cursor];
  const definition=calculatorReturnToFormulas&&formulaView==='manual'?triangleDefinitions.find(item=>item.id===state?.selected):null;
  panel.hidden=!definition;dialog.classList.toggle('with-triangle-reference',!!definition);
  if(!definition){panel.innerHTML='';return;}
  const values=state.drafts?.[definition.id]?.values??{};
  const rows=definition.slots.map(slot=>{
    // Mirror the actual field, including mistaken placements; checking stays in the manual solver.
    const value=String($('manual-slot-'+slot.key)?.value??values[slot.key]??'');
    return `<div class="calc-reference-row" data-calc-triangle-slot="${slot.key}"><dt>${mathNotation(slot.symbol)}</dt><dd><bdi data-calc-triangle-value>${escapeHTML(value||'—')}</bdi><small>${bdi(slotUnit(slot,q))}</small></dd></div>`;
  }).join('');
  panel.innerHTML=`<h3 id="calc-triangle-title"><svg class="calc-reference-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 2 21h20zM7 12h10M12 12v9"/></svg>הערכים שהזנת במשולש</h3><p class="muted">${escapeHTML(definition.title)}</p><dl class="calc-reference-values">${rows}</dl>`;
}
function canUseCalculatorResult() {
  const specialized=window.CourseApp?.formulaCalculatorAvailable();if(specialized!==null&&specialized!==undefined)return specialized;
  if(window.CourseApp?.standalone())return false;
  if(viewTab==='simulator'||!currentStep()||formulaQuestion().accepted)return false;
  return !(calculatorReturnToFormulas&&formulaView==='manual')||manualResultSlotKey()!==null;
}
function hideManualKeypad() {
  manualKeypadTarget=null;manualKeypadFieldId=null;
  if($('manual-keypad'))$('manual-keypad').hidden=true;
}
function keypadInput() {
  const input=manualKeypadFieldId?$(manualKeypadFieldId):null;
  if(input)manualKeypadTarget=input;
  return input;
}
function paintManualKeypad() {
  const input=keypadInput();
  if(!input)return hideManualKeypad();
  const key=input.dataset.manualList??input.dataset.manualSlot;
  const numbersOnly=input.hasAttribute('data-manual-slot');
  $('manual-keypad').classList.toggle('numeric-only',numbersOnly);
  $('manual-keypad').querySelector('.manual-keypad-header .small').textContent=numbersOnly?'מספרים בלבד':'מקלדת נתונים';
  for(const token of ['X','?'])$('manual-keypad').querySelector(`[data-manual-key="${token}"]`).hidden=numbersOnly;
  $('manual-keypad').setAttribute('aria-label',numbersOnly?'מקלדת מספרים':'מקלדת מספרים X וסימן שאלה');
  $('manual-keypad-value').textContent=key+' = '+(input.value||'…');
}
function showManualKeypad(input) {
  if(input.hasAttribute('data-manual-slot')||input.disabled||formulaQuestion().accepted)return hideManualKeypad();
  manualKeypadTarget=input;manualKeypadFieldId=input.id;
  $('manual-keypad').hidden=false;paintManualKeypad();
  requestAnimationFrame(()=>{
    fitDialogs();if($('manual-keypad').hidden)return;
    if(window.matchMedia('(min-width:1000px) and (hover:hover) and (pointer:fine)').matches){
      const region=input.closest(input.hasAttribute('data-manual-slot')?'.manual-triangle-panel':'.manual-list');
      region?.scrollIntoView({block:'start'});
    }else $('manual-keypad').scrollIntoView({block:'nearest'});
  });
}
function writeKeypadValue(input,value,position) {
  const state=manualState();
  if(input.hasAttribute('data-manual-list'))state.list[input.dataset.manualList]=value;
  else {
    manualDraft(state).values[input.dataset.manualSlot]=value;
    state.message='';state.errors=[];$('manual-message').textContent='';
  }
  input.value=value;
  input.classList.remove('answer-incorrect');
  if(input.hasAttribute('data-manual-list'))syncManualEntryOrder();
  if(manualTokenKind(value)==='invalid')input.setAttribute('aria-invalid','true');
  else input.removeAttribute('aria-invalid');
  try{input.setSelectionRange(position,position);}catch{}
  saveFormulaWork();paintManualKeypad();
}
function pressManualKey(key) {
  const input=keypadInput();
  if(key==='done'){hideManualKeypad();$('formula-tab-manual').focus({preventScroll:true});return;}
  if(!input)return hideManualKeypad();
  if(input.hasAttribute('data-manual-slot')&&(key==='X'||key==='?'))return;
  if(key==='enter') {
    const kind=manualTokenKind(input.value);
    if(kind==='invalid'||input.hasAttribute('data-manual-slot')&&!['blank','number'].includes(kind)){input.setAttribute('aria-invalid','true');return;}
    saveFormulaWork();
    const fields=[...document.querySelectorAll(input.hasAttribute('data-manual-list')?'[data-manual-list]':'[data-manual-slot]')];
    const next=fields[fields.indexOf(input)+1]??(input.hasAttribute('data-manual-list')?document.querySelector('[data-manual-slot]'):document.querySelector('[data-check-manual]'));
    if(next?.hasAttribute('data-check-manual'))hideManualKeypad();
    if(next)next.focus({preventScroll:true});else{hideManualKeypad();$('formula-tab-manual').focus({preventScroll:true});}
    return;
  }
  let value=input.value,position=value.length;
  if(key==='clear'){value='';position=0;}
  else if(key==='X'||key==='?'){value=key;position=1;}
  else {
    if(value==='?'||/^x$/i.test(value))value='';
    const start=Math.min(input.selectionStart??value.length,value.length),end=Math.min(input.selectionEnd??start,value.length);
    if(key==='backspace') {
      const from=start===end?Math.max(0,start-1):start;
      value=value.slice(0,from)+value.slice(end);position=from;
    } else {
      if(key==='.'&&/[.,]/.test(value.slice(0,start)+value.slice(end)))return;
      if(value.length-(end-start)>=input.maxLength)return;
      value=value.slice(0,start)+key+value.slice(end);position=start+key.length;
    }
  }
  writeKeypadValue(input,value,position);
}
document.addEventListener('focusin',event=>{
  if(event.target.matches('[data-manual-list]'))showManualKeypad(event.target);
  else if(event.target.matches('input,select,textarea'))hideManualKeypad();
});
document.addEventListener('beforeinput',event=>{
  const input=event.target;
  if(!input.matches('[data-manual-list],[data-manual-slot]'))return;
  if(input.hasAttribute('data-manual-slot')){
    if(event.inputType.startsWith('insert')&&event.data!==null&&!/^[0-9.,]+$/.test(event.data))event.preventDefault();
    return;
  }
  if(event.inputType!=='insertText')return;
  if(/^[xX?]$/.test(event.data??'')){event.preventDefault();input.value=event.data.toUpperCase();input.dispatchEvent(new Event('input',{bubbles:true}));return;}
  if(/^[0-9.,]$/.test(event.data??'')&&/^[xX?]$/.test(input.value))input.value='';
});
document.addEventListener('paste',event=>{
  if(event.target.hasAttribute('data-manual-slot')&&manualTokenKind(event.clipboardData?.getData('text')??'')!=='number')event.preventDefault();
});
function manualTokenKind(value) {
  const text = String(value).trim();
  if (!text) return 'blank';
  if (text === '?') return 'unknown';
  if (text.toLowerCase() === 'x') return 'unused';
  return /^(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(text) && Number.isFinite(Number(text.replace(',', '.'))) ? 'number' : 'invalid';
}
function formulaAnswerField() {
  if(formulaQuestion().accepted)return $('formula-body').querySelector('[data-next-step]');
  return formulaView === 'manual' ? $('manual-slot-'+manualResultSlotKey())??document.querySelector('[data-manual-slot]') : $('formula-body').querySelector('[data-answer]');
}
function manualEntrySlots(definition, state = manualState(), context = triangleContext()) {
  const order=formulaListKeys();
  const source=slot=>{
    const key=slot.key.replace(/2$/,'');
    if(String(state.list[key]??'').trim())return state.list[key];
    if(key===(context.target==='Req'?'R':context.target))return '?';
    return context.values[slot.key]!==undefined?String(context.values[slot.key]):'X';
  };
  return [...definition.slots].sort((a,b)=>
    Number(manualTokenKind(source(a))!=='number')-Number(manualTokenKind(source(b))!=='number')||
    order.indexOf(a.key.replace(/2$/,''))-order.indexOf(b.key.replace(/2$/,'')));
}
function syncManualEntryOrder() {
  const definition=triangleDefinitions.find(item=>item.id===manualState().selected);
  const triangle=document.querySelector('.manual-triangle');
  if(!definition||!triangle)return;
  for(const slot of manualEntrySlots(definition)){
    const label=$('manual-slot-'+slot.key)?.closest('label');
    if(label)triangle.append(label);
  }
}
function focusManualEntry() {
  // Announce the selected triangle without focusing an input or opening a keyboard.
  const heading=$('manual-choice-title');
  if(heading){heading.tabIndex=-1;heading.focus({preventScroll:true});}
}
function nextManualTriangleField(input) {
  saveFormulaWork();
  const fields=[...document.querySelectorAll('[data-manual-slot]')];
  const next=fields[fields.indexOf(input)+1]??document.querySelector('[data-check-manual]');
  next?.focus({preventScroll:true});
}
function manualSolverHTML() {
  const context = triangleContext(), state = manualState();
  const definition = triangleDefinitions.find(item => item.id === state.selected);
  const circuitReference=window.CourseApp?.formulaCircuitReference()??`<aside class="manual-circuit-reference" aria-labelledby="manual-circuit-title"><h3 id="manual-circuit-title">המעגל של התרגיל</h3>${circuitSummaryHTML(context.q)}<figure class="diagram">${diagramPreview(context.q)}</figure></aside>`;
  const choices = formulaDefinitions(context).map(item => `<button type="button" class="manual-choice" data-manual-triangle="${item.id}" aria-pressed="${item.id === state.selected}"${context.q.accepted?' disabled':''}><strong>${item.title}</strong>${trianglePreview(item)}${mathNotation(item.formulas[0])}</button>`).join('');
  const list = formulaListKeys().map(key => `<label class="manual-list-row" for="manual-list-${key}"><bdi>${key} =</bdi><input id="manual-list-${key}" data-manual-list="${key}" type="text" inputmode="none" lang="en" maxlength="24" aria-controls="manual-keypad"${window.matchMedia('(pointer:coarse)').matches ? ' readonly' : ''}${context.q.accepted?' disabled':''} autocomplete="off" autocapitalize="off" spellcheck="false" value="${escapeHTML(state.list[key]??'')}" aria-label="${key} ברשימת הנתונים" aria-describedby="manual-token-help"${manualTokenKind(state.list[key]) === 'invalid' ? ' aria-invalid="true"' : ''}></label>`).join('');
  const feedbackState=window.CourseApp?.formulaFeedbackStatus()??{message:feedback,type:feedbackType};
  const message = context.q.accepted?acceptedMessage(context.q):state.message || (feedbackState.type === 'success' ? feedbackState.message : '');
  const status = `<div id="manual-message" class="feedback ${context.q.accepted?'success':state.message ? state.type : feedbackState.type}" role="status" aria-live="polite">${escapeHTML(message)}</div>`;
  let work = context.q.accepted?`<div class="manual-form">${status}<button class="btn" type="button" data-next-step>הבא ←</button></div>`:`<div><div class="manual-placeholder">בחרו משולש מהרשימה כדי להציב בו נתונים.</div>${status}</div>`;
  if (definition) {
    const draft = manualDraft(state), locations = ['top','left','right'];
    const geometry = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" preserveAspectRatio="none" aria-hidden="true"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#78958a" stroke-width="2.5"/><path d="M65 125 L195 125 M130 125 L130 218" stroke="#78958a" stroke-width="2"/></svg>';
    const fields = manualEntrySlots(definition,state,context).map(slot => `<label class="triangle-slot ${locations[definition.slots.indexOf(slot)]}" for="manual-slot-${slot.key}"><strong>${slot.symbol}</strong><small>${slotUnit(slot,context.q)}</small><input id="manual-slot-${slot.key}" data-manual-slot="${slot.key}" class="numeric${context.q.accepted&&slot.key===context.target?' answer-correct':state.errors.includes(slot.key)?' answer-incorrect':''}" type="text" inputmode="decimal" pattern="[0-9]*[.,]?[0-9]*" enterkeyhint="next" lang="en" maxlength="24"${context.q.accepted&&slot.key===context.target ? ' readonly' : ''}${context.q.accepted&&slot.key!==context.target?' disabled':''} autocomplete="off" autocapitalize="off" spellcheck="false" value="${escapeHTML(context.q.accepted&&slot.key===context.target?context.q.draft:draft.values[slot.key] ?? '')}" aria-label="${slot.key===context.target?'התוצאה שחישבתם עבור':'הצבת'} ${slot.symbol} במשולש" aria-describedby="manual-instructions"${state.errors.includes(slot.key) ? ' aria-invalid="true"' : ''}></label>`).join('');
    work = `<form id="manual-form" class="manual-form" novalidate><h3>${definition.title}</h3><div class="triangle manual-triangle">${geometry}${fields}</div><div class="manual-answer">${status}${context.q.accepted?'<button class="btn" type="button" data-next-step>הבא ←</button>':`<button class="btn" type="submit" data-check-manual${context.task ? '' : ' disabled'}>בדוק</button>`}<button class="btn secondary tiny" type="button" data-open-calculator${context.q.accepted?' disabled':''}>מחשבון</button></div></form>`;
  }
  const notice = !context.task ? '<p class="complete-badge">התרגיל הושלם. אפשר לחזור לתרגול ולהמשיך לתרגיל הבא.</p>' : context.target === 'Req' ? `<p class="triangle-entry-note">נדרש למצוא ${mathNotation('R_T')}</p>` : '';
  return `<div class="manual-intro"><h3>פתירה בעזרת המשולש</h3><p class="small muted">${escapeHTML(context.label)}${context.task ? ` · מחשבים: ${escapeHTML(context.task.label)}` : ''}</p><p id="manual-instructions" class="small">בחרו משולש והציבו בו את שני הנתונים הידועים. חשבו בעצמכם והקלידו במשבצת של הנעלם את התוצאה המספרית. המעבר בשדות מתחיל בנתונים הידועים לפי סדר רשימת הנתונים. לחצו על בדוק כדי לבדוק את ההצבה ואת התוצאה ולהעביר אותה לתרגיל. לאחר תשובה נכונה לחצו על הבא.</p></div>${notice}<div class="manual-desktop-layout">${circuitReference}<div class="manual-editor">${unitNote(context.q)}<strong class="small" id="manual-choice-title">בחרו את המשולש המתאים</strong><div class="manual-choices" role="group" aria-labelledby="manual-choice-title">${choices}</div><div class="manual-workspace"><aside class="manual-list" aria-labelledby="manual-list-title"><p class="manual-paper-note">מומלץ לרשום את הנתונים בדף.</p><button class="btn manual-fill" type="button" data-manual-list-help${context.q.accepted?' disabled':''}>מילוי מתרגיל</button><h3 id="manual-list-title">רשימת נתונים<br><span class="muted">רשות</span></h3>${list}</aside><div class="manual-triangle-panel"><button class="btn secondary tiny manual-show-circuit" type="button" data-show-manual-circuit>הצג סכמה</button>${work}</div></div><p id="manual-token-help" class="small muted manual-note">הרשימה היא כלי עזר ואפשר להשאיר אותה ריקה. ${bdi('?')} = הנעלם שמחפשים; ${bdi('X')} = ערך שלא ידוע ולא התבקש לחשב. אפשר להקליד מספרים, כולל עשרוניים. כפתור מילוי מתרגיל ממלא רק את הרשימה; את ההצבה והחישוב עושים בעצמכם.</p><p id="manual-list-status" class="small muted manual-status" role="status" aria-live="polite">${escapeHTML(state.listStatus)}</p>${definition?.note ? `<p class="small muted">${escapeHTML(definition.note)}</p>` : ''}</div></div>`;
}
function fillManualList() {
  if(formulaQuestion().accepted)return;
  markFormulaHelp();
  const context = triangleContext(), state = manualState();
  const target = context.target === 'Req' ? 'R' : context.target;
  for (const key of formulaListKeys()) {
    state.list[key] = key === target ? '?' : context.values[key] !== undefined ? DC.fmt(context.values[key]) : 'X';
    const input = $('manual-list-' + key);
    if (input) { input.value = state.list[key]; input.removeAttribute('aria-invalid'); }
  }
  state.listStatus = 'הרשימה מולאה. את הנתונים במשולש מציבים בעצמכם.';
  $('manual-list-status').textContent = state.listStatus;
  syncManualEntryOrder();fitDialogs();saveFormulaWork();
}
function manualFeedback(message, errors = []) {
  if(window.CourseApp?.formulaFeedback(message,errors))return;
  if(formulaQuestion().accepted)return;
  hideManualKeypad();
  recordAttempt(false,'manual');
  formulaQuestion().attempts++;
  const state = manualState(); state.message = 'לא נכון. '+message; state.type = 'error'; state.errors = errors;
  feedback=state.message;feedbackType='error';
  const notice = $('manual-message');
  notice.className = 'feedback error'; notice.textContent = state.message;
  $('form-feedback').className='feedback error';$('form-feedback').textContent=state.message;
  document.querySelectorAll('[data-answer]').forEach(input=>{input.classList.add('answer-incorrect');input.setAttribute('aria-invalid','true');});
  $('manual-form')?.querySelectorAll('input').forEach(input => {
    const invalid = errors.includes(input.dataset.manualSlot);
    if (invalid) input.setAttribute('aria-invalid','true'); else input.removeAttribute('aria-invalid');
    input.classList.toggle('answer-incorrect',invalid);
  });
  fitDialogs();saveFormulaWork();
}
function checkManualAnswer() {
  const context = triangleContext(), state = manualState();
  const definition = triangleDefinitions.find(item => item.id === state.selected);
  if (!context.task || !definition || context.q.accepted) return;
  if (!definition.slots.some(slot => slot.key === context.target)) {
    return manualFeedback(context.target === 'Req' ? 'בשלב הזה משתמשים בנוסחת התנגדות שקולה. אפשר למצוא אותה בלשונית נוסחאות.' : 'המשולש שבחרתם אינו מתאים לנעלם בצעד הזה. בחרו משולש אחר.');
  }
  const known = definition.slots.filter(slot => slot.key !== context.target);
  if (known.some(slot => context.values[slot.key] === undefined)) return manualFeedback('עדיין אין מספיק נתונים ידועים למשולש הזה. בחרו משולש שאפשר להציב בו שני נתונים ידועים.');
  const draft = manualDraft(state);
  const answer=String(draft.values[context.target]??'');
  syncDraft(answer);
  const incorrect = known.filter(slot => !DC.accepted(draft.values[slot.key] ?? '', context.values[slot.key]));
  if (incorrect.length) return manualFeedback('בדקו את הנתונים שהצבתם במשולש. בשני המקומות הידועים צריך להקליד מספרים שמתאימים לנתוני התרגיל. בסימון ריבוע כופלים את הנתון בעצמו.', incorrect.map(slot => slot.key));
  if(manualTokenKind(answer)!=='number')return manualFeedback('הקלידו במשבצת של הנעלם את התוצאה המספרית שחישבתם.',[context.target]);
  if (!DC.accepted(answer, context.task.value)) return manualFeedback('ההצבה במשולש נכונה. בדקו שוב את החישוב ואת התוצאה שהקלדתם במשבצת של הנעלם.', [context.target]);
  if(!window.CourseApp?.submitFormulaAnswer(answer))checkAnswer(answer,'manual');
}
function triangleCard(definition, context = null) {
  const slots = definition.slots;
  const enabled = !!context?.task && slots.some(slot => slot.key === context.target)
    && slots.filter(slot => slot.key !== context.target).every(slot => context.values[slot.key] !== undefined);
  const locations = ['top', 'left', 'right'];
  const geometry = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" preserveAspectRatio="none" aria-hidden="true"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#78958a" stroke-width="2.5"/><path d="M65 125 L195 125 M130 125 L130 218" stroke="#78958a" stroke-width="2"/></svg>';
  const inputs = slots.map((slot, j) => `<div class="triangle-slot ${locations[j]}"><strong>${slot.symbol}</strong><small>${slotUnit(slot,context?.q??formulaQuestion())}</small>${!context ? '' : enabled && slot.key === context.target
    ? `<input class="numeric${context.q.accepted?' answer-correct':context.q.attempts>0?' answer-incorrect':''}" data-answer type="text" inputmode="decimal" maxlength="24" autocomplete="off" value="${escapeHTML(context.q.draft)}"${context.q.accepted?' readonly':''} aria-label="${escapeHTML(context.task.label)} במשולש ${definition.title}">`
    : `<bdi>${context.values[slot.key] !== undefined ? DC.fmt(context.values[slot.key]) : '—'}</bdi>`}</div>`).join('');
  const triangle = `<div class="triangle">${geometry}${inputs}</div>`;
  const content = context ? `<form data-triangle-form novalidate>${triangle}${enabled ? context.q.accepted?'<button class="btn triangle-check tiny" type="button" data-next-step>הבא ←</button>':`<button class="btn triangle-check tiny" type="submit">בדיקת ${escapeHTML(context.task.label)}</button>` : '<p class="triangle-help">המשולש זמין למענה כשהנעלם ושני הנתונים מתאימים לשלב הנוכחי.</p>'}</form>` : triangle;
  return `<section class="formula-card"><h3>${definition.title}</h3>${content}<div class="formula-lines">${definition.formulas.map(mathNotation).join('<br>')}</div>${definition.note ? `<p class="triangle-help">${definition.note}</p>` : ''}</section>`;
}
function renderFormulas() {
  hideManualKeypad();saveFormulaWork();
  const context = formulaView === 'help' ? triangleContext() : null;
  $('formula-dialog').classList.toggle('manual-desktop-view',formulaView==='manual');
  if (context?.task) markFormulaHelp();
  document.querySelector('#formula-dialog .formula-intro').hidden = formulaView === 'manual';
  document.querySelectorAll('.formula-tabs [data-formula-tab]').forEach(button => {
    const active = button.dataset.formulaTab === formulaView;
    button.setAttribute('aria-selected', active); button.tabIndex = active ? 0 : -1;
  });
  $('formula-body').setAttribute('aria-labelledby', 'formula-tab-' + formulaView);
  if(formulaView==='reference'&&window.CourseApp?.renderFormulaReference()){finishFormulaRender();return;}
  if(formulaView==='help'&&window.CourseApp?.renderExtraFormulaHelp()){finishFormulaRender();return;}
  if (formulaView === 'manual') {
    $('formula-body').innerHTML = manualSolverHTML();
    finishFormulaRender(); return;
  }
  const sheetHelp = context?.task && (context.q.hint || context.q.solution) ? `<div class="${context.q.solution ? 'solution' : 'hint'}" id="sheet-explained-solution">${context.q.solution ? solutionHeadingHTML()+explainedSolutionHTML(context.q,context.task)+'<p>הקלידו את התוצאה בשדה המענה המודגש כדי להמשיך.</p>' : `<strong>כיוון לפתרון</strong><p>${escapeHTML(context.task.hint)}</p><div class="math">${mathNotation(context.task.formula)}</div>`}</div>` : '';
  const definitions = formulaDefinitions(context??triangleContext());
  const alternative = context?.task && context.target === 'Req' ? `<form class="sheet-answer" data-triangle-form novalidate><label for="sheet-answer">${escapeHTML(context.task.label)} — השתמשו בנוסחת טור או מקביל שמופיעה בהמשך</label><div class="answer-row"><input id="sheet-answer" class="numeric${context.q.accepted?' answer-correct':context.q.attempts>0?' answer-incorrect':''}" data-answer inputmode="decimal" type="text" maxlength="24" value="${escapeHTML(context.q.draft)}"${context.q.accepted?' readonly':''} autocomplete="off" aria-label="התנגדות שקולה"><span>${bdi(context.task.unit)}</span>${context.q.accepted?'<button class="btn tiny" type="button" data-next-step>הבא ←</button>':'<button class="btn tiny" type="submit">בדיקת תשובה</button>'}</div></form>` : '';
  const given = context ? Object.entries(context.q.givens).map(([key, value]) => `<div class="given">${bdi(`${key} = ${quantity(context.q,key,value)}`)}</div>`).join('') : '';
  const exerciseContext = context ? `<div class="formula-context"><strong>${escapeHTML(context.label)}</strong><div>${context.task ? `כעת מחשבים: ${escapeHTML(context.task.label)}. הנתונים במשולשים כוללים רק נתוני השאלה וצעדים שכבר השלמתם.` : 'אפשר לעבור על הנוסחאות ולהמשיך לתרגיל הבא.'}</div><div class="givens sheet-givens" aria-label="נתוני התרגיל">${given}</div><div class="answer-tools" style="margin:8px 0 0"><button class="btn secondary tiny" data-open-calculator>פתיחת המחשבון</button>${context.task&&!context.q.accepted?`<button class="text-btn small" data-solution aria-expanded="${context.q.solution}" aria-controls="sheet-explained-solution">פתרון מוסבר</button>`:''}<button class="btn soft tiny" data-close-dialog="formula-dialog">חזרה לתרגול</button></div></div>` : '';
  $('formula-body').innerHTML = `${formulaView === 'reference' ? '<div class="manual-entry"><button class="btn" data-formula-tab="manual">פתירה בעזרת המשולש</button><span class="small muted">בוחרים משולש, מציבים נתונים ופותרים בעצמכם.</span></div>' : ''}${exerciseContext}${unitNote(context?.q??formulaQuestion())}${context && feedback ? `<div class="feedback sheet-feedback ${feedbackType}" role="status" aria-live="polite">${escapeHTML(feedback)}</div>` : ''}${sheetHelp}${alternative}<div class="formula-grid">${definitions.map(def => triangleCard(def, context)).join('')}</div><div class="units-list"><span>${bdi('U')} — מתח, וולט ${bdi('V')}</span><span>${bdi('I')} — זרם, אמפר ${bdi('A')}</span><span>${bdi('R')} — התנגדות, אוהם ${bdi(context.task.unit)}</span><span>${bdi('P')} — הספק, ואט ${bdi('W')}</span></div><div class="formula-networks"><section class="formula-card"><h3>מעגל טורי</h3><div class="math">${mathNotation('R_T = R1 + R2 + R3')}<br>${mathNotation('I = U ÷ R_T')}<br>${mathNotation('U1 = I × R1')}<br>${mathNotation('U = U1 + U2 + U3')}<br>${mathNotation('P1 = I² × R1')}</div><p class="small muted" style="margin-top:10px">${mathNotation('R_T')} מציין התנגדות שקולה. בשני רכיבים מחברים רק את R1 ואת R2. אותו זרם עובר בכל הרכיבים.</p></section><section class="formula-card"><h3>מעגל מקבילי</h3><div class="math parallel-formulas"><div class="network-formula">${mathNotation('R_T = (R1 × R2) ÷ (R1 + R2)')}</div><div class="network-formula">${mathNotation('R_T = 1 ÷ (1/R1 + 1/R2 + 1/R3)')}</div><div class="network-formula">${mathNotation('R_T = R ÷ n')}</div><div class="network-formula">${mathNotation('I1 = U ÷ R1')}</div><div class="network-formula">${mathNotation('I_total = I1 + I2 + I3')}</div><div class="network-formula">${mathNotation('P1 = U × I1')}</div></div><p class="small muted" style="margin-top:10px">${mathNotation('R_T')} מציין התנגדות שקולה. הנוסחה R/n מתאימה רק לנגדים זהים. n הוא מספר הענפים. בכל הענפים אותו מתח.</p></section></div>`;
  finishFormulaRender();
}

function openDialog(id, { preserveFormulaView = false } = {}) {
  hideIconTooltip();
  if(window.ShabbatMode.isLocked()&&!['qa-login-dialog','logo-dialog'].includes(id))return;
  if (!profileReady() && !qaActive && !['profile-dialog','qa-login-dialog','logo-dialog'].includes(id)) { openProfile(); return; }
  calculatorReturnToFormulas = id === 'calculator-dialog' && $('formula-dialog').open;
  if(id==='calculator-dialog'){prepareCalculator();renderCalculatorTriangleReference();}
  if (id === 'formula-dialog' && !preserveFormulaView) formulaView = window.CourseApp?.preferredFormulaView()??'reference';
  document.querySelectorAll('dialog[open]').forEach(dialog => { if (dialog.id !== id) dialog.close(); });
  if (id === 'formula-dialog') renderFormulas();
  if (!$(id).open) $(id).showModal();
  fitDialogs(); resizeFrame();
}
function sendStreamlitMessage(type, data) { window.parent.postMessage({ isStreamlitMessage:true, type, ...data }, '*'); }
let frameResizeRequest = 0, lastFrameHeight = 0;
function resizeFrame() {
  if (frameResizeRequest) return;
  frameResizeRequest = requestAnimationFrame(() => {
    frameResizeRequest = 0;
    const height = Math.ceil($('app').getBoundingClientRect().height + 10);
    if (height <= 10 || height === lastFrameHeight) return;
    lastFrameHeight = height;
    sendStreamlitMessage('streamlit:setFrameHeight', { height });
  });
}
function fitDialogs() {
  let top = 0, height = Math.min(window.innerHeight, window.screen?.availHeight || 850);
  try {
    const frame = window.frameElement?.getBoundingClientRect();
    if (frame) {
      top = Math.max(0, -frame.top);
      height = Math.max(100, Math.min(window.innerHeight - top, window.parent.innerHeight - Math.max(0, frame.top)));
    }
  } catch {}
  if ($('diagram-dialog').open) $('diagram-viewport').style.maxHeight = Math.max(100, height - 230 - $('diagram-context').getBoundingClientRect().height) + 'px';
  document.querySelectorAll('dialog[open]').forEach(dialog => {
    dialog.style.position = 'fixed'; dialog.style.margin = '0 auto'; dialog.style.bottom = 'auto';
    dialog.style.maxHeight = Math.max(100, height - 24) + 'px';
    dialog.style.setProperty('--manual-reference-height',Math.max(180,height-150)+'px');
    dialog.style.top = top + Math.max(12, (height - dialog.getBoundingClientRect().height) / 2) + 'px';
  });
}
const calculatorSettingsKey='dc.basics.calculator.v1';
const calculatorDefaults={color:'#c78b2d',expressionStyle:'math',resultStyle:'decimal',rounding:true,digits:3};
function loadCalculatorSettings() {
  const prefs={...calculatorDefaults};
  try {
    const saved=JSON.parse(localStorage.getItem(calculatorSettingsKey)||'null');
    if(/^#[0-9a-f]{6}$/i.test(saved?.color))prefs.color=saved.color;
    if(['math','linear'].includes(saved?.expressionStyle))prefs.expressionStyle=saved.expressionStyle;
    if(['decimal','fraction'].includes(saved?.resultStyle))prefs.resultStyle=saved.resultStyle;
    if(typeof saved?.rounding==='boolean')prefs.rounding=saved.rounding;
    if([3,4,5,6].includes(saved?.digits))prefs.digits=saved.digits;
  } catch {}
  return prefs;
}
let calculatorSettings=loadCalculatorSettings(),calculatorDetails=null,calculatorLastExpression='',calculatorResultStyle=calculatorSettings.resultStyle;
let calculatorEntryField='calc-screen',calculatorFractionSelection={start:0,end:0};
function mixCalculatorColor(color,base,amount) {
  return '#'+[1,3,5].map(i=>Math.round(parseInt(color.slice(i,i+2),16)*amount+parseInt(base.slice(i,i+2),16)*(1-amount)).toString(16).padStart(2,'0')).join('');
}
function calculatorColorInk(hex) {
  const rgb=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
  return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]>.179?'#17130d':'#ffffff';
}
function applyCalculatorColors() {
  const dark=document.documentElement.classList.contains('dark-mode'),color=calculatorSettings.color;
  const vars=dark?{paper:'#000000',card:mixCalculatorColor(color,'#101010',.06),soft:mixCalculatorColor(color,'#151515',.18),line:mixCalculatorColor(color,'#666666',.25),accent:mixCalculatorColor(color,'#141414',.36),ink:'#e9e4da',muted:'#c2b8a5',screen:'#080808'}:
    {paper:mixCalculatorColor(color,'#ffffff',.05),card:mixCalculatorColor(color,'#ffffff',.08),soft:mixCalculatorColor(color,'#ffffff',.19),line:mixCalculatorColor(color,'#777777',.4),accent:color,ink:'#29251f',muted:'#62594d',screen:'#ffffff'};
  vars.onAccent=calculatorColorInk(vars.accent);
  const dialog=$('calculator-dialog');
  for(const [key,value] of Object.entries(vars))dialog.style.setProperty('--calc-'+key,value);
}
function paintCalculatorSettings() {
  $('calc-color').value=calculatorSettings.color;
  $('calc-expression-style').value=calculatorSettings.expressionStyle;
  $('calc-result-style').value=calculatorSettings.resultStyle;
  $('calc-rounding').checked=calculatorSettings.rounding;
  $('calc-rounding').parentElement.lastChild.textContent=' עיגול תוצאה עשרונית — '+(calculatorSettings.rounding?'פעיל':'לא פעיל');
  $('calc-digits').value=String(calculatorSettings.digits);
  $('calc-digits').disabled=!calculatorSettings.rounding;
  applyCalculatorColors();
}
function saveCalculatorSettings() {
  try{localStorage.setItem(calculatorSettingsKey,JSON.stringify(calculatorSettings));}catch{}
  paintCalculatorSettings();paintCalculatorExpression();paintCalculatorResult();fitDialogs();
}
function calculatorMathTree(tree,stripGroup=false) {
  if(tree.kind==='number')return `<mn>${escapeHTML(tree.text)}</mn>`;
  if(tree.kind==='group')return stripGroup||tree.child.kind==='binary'&&tree.child.op==='/'?calculatorMathTree(tree.child):`<mrow><mo>(</mo>${calculatorMathTree(tree.child)}<mo>)</mo></mrow>`;
  if(tree.kind==='unary')return `<mrow><mo>${tree.op==='-'?'−':'+'}</mo>${calculatorMathTree(tree.child)}</mrow>`;
  if(tree.kind==='square')return `<msup>${calculatorMathTree(tree.child)}<mn>2</mn></msup>`;
  if(tree.op==='/')return `<mfrac>${calculatorMathTree(tree.left,true)}${calculatorMathTree(tree.right,true)}</mfrac>`;
  return `<mrow>${calculatorMathTree(tree.left)}<mo>${tree.op==='*'?'×':tree.op==='-'?'−':'+'}</mo>${calculatorMathTree(tree.right)}</mrow>`;
}
function calculatorMath(markup,label) {
  return `<math xmlns="http://www.w3.org/1998/Math/MathML" class="mathml" display="inline" dir="ltr" aria-label="${escapeHTML(label)}">${markup}</math>`;
}
function paintCalculatorExpression() {
  const box=$('calc-expression-preview'),text=$('calc-screen').value;
  box.hidden=calculatorSettings.expressionStyle!=='math'||!text.trim();
  if(box.hidden){box.textContent='';return;}
  try{box.innerHTML=calculatorMath(calculatorMathTree(DC.evaluateCalculation(text).tree),text);}
  catch{box.textContent=text.replace(/\*/g,'×').replace(/\//g,'÷');}
}
function calculatorDecimal(details) {
  const {value,exact}=details,digits=calculatorSettings.digits;
  if(!calculatorSettings.rounding)return {text:String(value),approximate:!!exact&&Number(exact.n)/Number(exact.d)!==value};
  if(exact) {
    const negative=exact.n<0n,n=negative?-exact.n:exact.n,scale=10n**BigInt(digits);
    let rounded=n*scale/exact.d;
    if((n*scale%exact.d)*2n>=exact.d)rounded++;
    if(rounded===0n&&n!==0n)return {text:value.toExponential(digits-1),approximate:true,tiny:true};
    let text=rounded.toString().padStart(digits+1,'0');
    text=text.slice(0,-digits)+'.'+text.slice(-digits);
    text=text.replace(/0+$/,'').replace(/\.$/,'');
    return {text:(negative&&rounded!==0n?'-':'')+text,approximate:n*scale%exact.d!==0n};
  }
  if(value!==0&&Math.abs(value)<10**(-digits))return {text:value.toExponential(digits-1),approximate:true,tiny:true};
  const text=String(Number(value.toFixed(digits)));
  return {text,approximate:Number(text)!==value};
}
function paintCalculatorResult() {
  const box=$('calc-result'),note=$('calc-result-note');
  $('calc-format').setAttribute('aria-pressed',calculatorResultStyle==='fraction');
  if(!calculatorDetails){box.textContent='';note.textContent='';return;}
  const exact=calculatorDetails.exact;
  if(calculatorResultStyle==='fraction'&&exact) {
    const negative=exact.n<0n,n=String(negative?-exact.n:exact.n),d=String(exact.d);
    const fraction=d==='1'?`<mn>${n}</mn>`:`<mfrac><mn>${n}</mn><mn>${d}</mn></mfrac>`;
    box.innerHTML=calculatorMath(`<mrow>${negative?'<mo>−</mo>':''}${fraction}</mrow>`,(negative?'-':'')+n+(d==='1'?'':' חלקי '+d));
    note.textContent='תוצאה מדויקת בכתב מתמטי';
  } else {
    const decimal=calculatorDecimal(calculatorDetails);
    box.textContent=(decimal.approximate?'≈ ':'')+decimal.text;
    note.textContent=decimal.tiny?'כתיב מדעי שומר על מספר קטן שאחרת היה מוצג כ־0.':calculatorSettings.rounding?'עד '+calculatorSettings.digits+' ספרות אחרי הנקודה · העיגול לתצוגה בלבד':'עיגול כבוי · הדיוק הזמין במחשבון';
    if(calculatorResultStyle==='fraction'&&!exact)note.textContent='התוצאה מוצגת בקירוב בגלל גודל המספרים.';
  }
}
function invalidateCalculator() {
  calculatorValue=null;calculatorDetails=null;calculatorFresh=false;
  $('calc-use').disabled=true;$('calc-error').textContent='';
  paintCalculatorResult();paintCalculatorExpression();
}
function calculateScreen() {
  if(!$('calc-fraction-editor').hidden&&!insertCalculatorFraction())return;
  try {
    calculatorDetails=DC.evaluateCalculation($('calc-screen').value);
    calculatorValue=calculatorDetails.value;calculatorLastExpression=$('calc-screen').value;
    $('calc-error').textContent='';$('calc-use').disabled=!canUseCalculatorResult();calculatorFresh=true;
    paintCalculatorExpression();paintCalculatorResult();
  }catch(error){invalidateCalculator();$('calc-error').textContent=error.message;}
  fitDialogs();
}
function closeCalculatorFraction() {
  $('calc-fraction-editor').hidden=true;$('calc-fraction').setAttribute('aria-expanded','false');calculatorEntryField='calc-screen';
}
function clearCalculator() {
  $('calc-screen').value='';$('calc-numerator').value='';$('calc-denominator').value='';
  closeCalculatorFraction();invalidateCalculator();fitDialogs();
}
function openCalculatorFraction() {
  if(!$('calc-fraction-editor').hidden){$('calc-numerator').focus();return;}
  if(calculatorFresh){$('calc-screen').value='';invalidateCalculator();}
  const screen=$('calc-screen'),start=screen.selectionStart??screen.value.length,end=screen.selectionEnd??start;
  calculatorFractionSelection={start,end};
  invalidateCalculator();
  $('calc-numerator').value=screen.value.slice(start,end);$('calc-denominator').value='';
  $('calc-fraction-editor').hidden=false;$('calc-fraction').setAttribute('aria-expanded','true');
  $('calc-error').textContent='';calculatorEntryField='calc-numerator';
  $('calc-numerator').focus({preventScroll:true});fitDialogs();
  $('calc-fraction-editor').scrollIntoView({block:'nearest'});
}
function insertCalculatorFraction() {
  const numerator=$('calc-numerator').value.trim(),denominator=$('calc-denominator').value.trim();
  try {
    DC.evaluateCalculation(numerator);
    const bottom=DC.evaluateCalculation(denominator);
    if(bottom.exact?bottom.exact.n===0n:bottom.value===0)throw Error('המכנה אינו יכול להיות אפס.');
    const screen=$('calc-screen'),{start,end}=calculatorFractionSelection;
    const fraction=`((${numerator})/(${denominator}))`,next=screen.value.slice(0,start)+fraction+screen.value.slice(end);
    if(next.length>160)throw Error('התרגיל ארוך מדי. יש לקצר את הביטוי.');
    screen.value=next;screen.setSelectionRange(start+fraction.length,start+fraction.length);
    closeCalculatorFraction();invalidateCalculator();fitDialogs();return true;
  }catch(error){$('calc-error').textContent=!numerator||!denominator?'יש למלא גם מונה וגם מכנה.':error.message;fitDialogs();return false;}
}
function pressCalculatorKey(key) {
  if(key==='=')return calculateScreen();
  if(key==='C')return clearCalculator();
  const input=$('calc-fraction-editor').hidden?$('calc-screen'):$(calculatorEntryField==='calc-denominator'?'calc-denominator':'calc-numerator');
  const main=input.id==='calc-screen';
  if(main&&calculatorFresh&&calculatorValue!==null&&key!=='←') {
    input.value=['+','−','×','÷','²'].includes(key)?'('+calculatorLastExpression+')':'';
    input.setSelectionRange(input.value.length,input.value.length);
  }
  const start=input.selectionStart??input.value.length,end=input.selectionEnd??start;
  let before=input.value.slice(0,start),after=input.value.slice(end),position=start;
  if(key==='←') {
    if(start===end){before=before.slice(0,-1);position=Math.max(0,start-1);}
    input.value=before+after;
  }else {
    if(key==='²'&&!/[0-9.,)²]$/.test(before)){$('calc-error').textContent='יש להקליד מספר או לסיים את הביטוי לפני העלאה בריבוע.';fitDialogs();return;}
    if(before.length+key.length+after.length>input.maxLength){$('calc-error').textContent='הביטוי ארוך מדי.';return;}
    input.value=before+key+after;position=start+key.length;
  }
  input.setSelectionRange(position,position);invalidateCalculator();
  if(key==='²'&&main)calculateScreen();
}
function prepareCalculator() {
  calculatorResultStyle=calculatorSettings.resultStyle;
  $('calc-settings').hidden=true;$('calc-settings-toggle').setAttribute('aria-expanded','false');
  closeCalculatorFraction();paintCalculatorSettings();paintCalculatorExpression();paintCalculatorResult();
}
document.addEventListener('focusin',event=>{
  if(['calc-screen','calc-numerator','calc-denominator'].includes(event.target.id))calculatorEntryField=event.target.id;
});
document.addEventListener('pointerdown',event=>{
  // Keep the expression cursor when an on-screen calculator key is pressed.
  if(event.target.closest('#calc-grid button,#calc-fraction,#calc-format'))event.preventDefault();
});
document.addEventListener('input',event=>{
  if(event.target.id==='calc-color') {calculatorSettings.color=event.target.value;saveCalculatorSettings();}
  if(['calc-numerator','calc-denominator'].includes(event.target.id))$('calc-error').textContent='';
});
document.addEventListener('change',event=>{
  const ids={'calc-expression-style':'expressionStyle','calc-result-style':'resultStyle','calc-rounding':'rounding','calc-digits':'digits'};
  const key=ids[event.target.id];if(!key)return;
  calculatorSettings[key]=key==='rounding'?event.target.checked:key==='digits'?Number(event.target.value):event.target.value;
  if(key==='resultStyle')calculatorResultStyle=calculatorSettings.resultStyle;
  saveCalculatorSettings();
});
new MutationObserver(applyCalculatorColors).observe(document.documentElement,{attributes:true,attributeFilter:['class']});
paintCalculatorSettings();
const keypad=['C','←','(',')','7','8','9','÷','4','5','6','×','1','2','3','−','0','.','=','+','²'];
$('calc-grid').innerHTML=keypad.map(key=>`<button type="button" data-calc="${key}" class="${['÷','×','−','+','²'].includes(key)?'operator':key==='='?'equals':''}" aria-label="${key==='←'?'מחיקת תו':key==='C'?'ניקוי':key==='='?'חישוב':key==='²'?'העלאה בריבוע':key}">${key==='²'?'x²':key}</button>`).join('');
document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if(button.hasAttribute('data-open-feedback'))return openContact();
  if(button.hasAttribute('data-open-ratings'))return openDialog('ratings-dialog');
  if(button.hasAttribute('data-open-guide'))return openDialog('guide-dialog');
  if(button.dataset.contactMode)return openFeedback(button.dataset.contactMode);
  if(button.hasAttribute('data-contact-back'))return openContact();
  if(button.hasAttribute('data-open-logo')){
    $('logo-large').src=document.querySelector('.footer-logo').src;
    return openDialog('logo-dialog');
  }
  if(button.hasAttribute('data-open-qa'))return openQA();
  if(button.hasAttribute('data-exit-qa'))return exitQA();
  if(button.dataset.shabbatMode){if(window.ShabbatMode.setMode(button.dataset.shabbatMode)){renderQA();resizeFrame();}return;}
  if(button.hasAttribute('data-qa-previous'))return qaMove(-1);
  if(button.hasAttribute('data-qa-next'))return qaMove(1);
  if(button.hasAttribute('data-qa-answer')){if(qaActive){qaAnswerVisible=!qaAnswerVisible;renderQA();resizeFrame();}return;}
  if(button.dataset.manualKey!==undefined)return pressManualKey(button.dataset.manualKey);
  if (button.hasAttribute('data-open-profile')) return openProfile();
  if (button.hasAttribute('data-show-progress')) return showProgress();
  if (button.hasAttribute('data-previous-solved')) return reviewSolvedExercise(previousSolvedExercise()?.id);
  if (button.hasAttribute('data-resume-exercise')) return resumeExercise();
  if (button.hasAttribute('data-open-accessibility')) return openDialog('accessibility-dialog');
  if (button.hasAttribute('data-open-terms')) return openDialog('terms-dialog');
  if (button.hasAttribute('data-reset-accessibility')) {
    personal.preferences=emptyPersonal().preferences;savePersonal();applyPreferences();return;
  }
  if (button.hasAttribute('data-go-simulator')) {
    simulatorMode='exercise';simulatorQuestion=currentQuestion();selectTab('simulator');$('tab-simulator').focus({preventScroll:true});return;
  }
  if (button.hasAttribute('data-open-manual')) {
    const task=currentStep();if(!task)return;
    if(task.key==='Req'){
      const note=$('triangle-entry-note');note.innerHTML=`נדרש למצוא ${mathNotation('R_T')}`;note.hidden=false;resizeFrame();return;
    }
    formulaView='manual';openDialog('formula-dialog',{preserveFormulaView:true});$('formula-dialog').scrollTop=0;return;
  }
  if(button.dataset.resistanceMethod){
    if(!['fractions','decimal'].includes(button.dataset.resistanceMethod))return;
    resistanceSolutionMethod=button.dataset.resistanceMethod;
    const dialogOpen=$('formula-dialog').open,scroll=$('formula-dialog').scrollTop;
    render();
    (dialogOpen?$('formula-body'):$('workspace')).querySelector(`[data-resistance-method="${resistanceSolutionMethod}"]`)?.focus({preventScroll:true});
    if(dialogOpen)$('formula-dialog').scrollTop=scroll;
    fitDialogs();return;
  }
  if (button.hasAttribute('data-open-formulas')) return openDialog('formula-dialog');
  if (button.hasAttribute('data-show-manual-circuit')) return openDiagram('exercise');
  if (button.dataset.openDiagram) return openDiagram(button.dataset.openDiagram);
  if (button.dataset.diagramZoom) return zoomDiagram(button.dataset.diagramZoom);
  if (button.dataset.formulaTab) {
    formulaView = button.dataset.formulaTab; renderFormulas(); $('formula-dialog').scrollTop = 0;
    if(formulaView==='manual')focusManualEntry();return;
  }
  if (button.dataset.manualTriangle) {
    if(formulaQuestion().accepted)return;
    const state = manualState(); state.selected = button.dataset.manualTriangle; state.message = ''; state.errors = [];
    renderFormulas();focusManualEntry();return;
  }
  if (button.hasAttribute('data-manual-list-help')) return fillManualList();
  if (button.hasAttribute('data-open-calculator')) {
    openDialog('calculator-dialog');
    $('calc-use').disabled = calculatorValue === null || !canUseCalculatorResult();return;
  }
  if (button.dataset.closeDialog) {
    if(button.dataset.closeDialog==='profile-dialog'&&profileRequired)return;
    return $(button.dataset.closeDialog).close();
  }
  if (button.dataset.tab) { selectTab(button.dataset.tab); return; }
  if(button.hasAttribute('data-return-training')){selectTab(tab);$('tab-'+tab).focus({preventScroll:true});return;}
  if(button.dataset.simMode){simulatorMode=button.dataset.simMode;renderSimulatorPanel();resizeFrame();return;}
  if(button.hasAttribute('data-add-resistor')){customDraft.resistances.push('10');renderSimulatorPanel();$('custom-r-'+(customDraft.resistances.length-1)).focus({preventScroll:true});return;}
  if(button.dataset.removeResistor!==undefined){if(customDraft.resistances.length>1)customDraft.resistances.splice(Number(button.dataset.removeResistor),1);renderSimulatorPanel();$('custom-r-'+Math.min(Number(button.dataset.removeResistor),customDraft.resistances.length-1)).focus({preventScroll:true});return;}
  if (button.dataset.level !== undefined) { qaAnswerVisible=false; levels[tab] = Number(button.dataset.level); feedback = ''; render(); return; }
  const q = currentQuestion();
  if(button.hasAttribute('data-next-step'))return nextStep();
  if (button.hasAttribute('data-hint')) {
    q.hint=!q.hint;if(q.hint)markHelp();render();
    $('workspace').querySelector('[data-hint]')?.focus({preventScroll:true});return;
  }
  if (button.hasAttribute('data-close-solution')) {
    q.solution=false;render();
    ($('formula-dialog').open?$('formula-body'):$('workspace')).querySelector('[data-solution]')?.focus({preventScroll:true});return;
  }
  if (button.hasAttribute('data-solution')) {
    q.solution=!q.solution;if(q.solution){markHelp();q.help[q.cursor]=true;}render();
    ($('formula-dialog').open?$('formula-body'):$('workspace')).querySelector('[data-solution]')?.focus({preventScroll:true});return;
  }
  if (button.hasAttribute('data-next-question')) return showExercise({kind:tab,level:levels[tab],index:positions[tab][levels[tab]]+1});
  if (button.hasAttribute('data-next-level')) return showExercise({kind:tab,level:levels[tab]+1,index:positions[tab][levels[tab]+1]});
  if (button.id === 'new-course' || button.hasAttribute('data-new-course')) return openDialog('new-course-dialog');
  if (button.id === 'new-course-confirm') { $('new-course-dialog').close(); newCourse(); return; }
  if (button.id === 'text-size') {
    personal.preferences.textScale=personal.preferences.textScale===100?125:100;savePersonal();applyPreferences();return;
  }
  if (button.hasAttribute('data-reset-simulator')) { const model=activeSimulatorQuestion();model.simVoltage=model.voltage;updateSimulator();return; }
  if(button.id==='calc-settings-toggle') {
    const panel=$('calc-settings');panel.hidden=!panel.hidden;button.setAttribute('aria-expanded',!panel.hidden);fitDialogs();return;
  }
  if(button.id==='calc-reset-settings') {calculatorSettings={...calculatorDefaults};calculatorResultStyle=calculatorSettings.resultStyle;saveCalculatorSettings();return;}
  if(button.id==='calc-format') {calculatorResultStyle=calculatorResultStyle==='fraction'?'decimal':'fraction';paintCalculatorResult();fitDialogs();return;}
  if(button.id==='calc-fraction')return openCalculatorFraction();
  if(button.id==='calc-insert-fraction')return insertCalculatorFraction();
  if(button.id==='calc-cancel-fraction'){closeCalculatorFraction();$('calc-error').textContent='';fitDialogs();return;}
  if(button.dataset.calcPart){calculatorEntryField=button.dataset.calcPart;$(calculatorEntryField).focus({preventScroll:true});return;}
  if (button.id === 'calc-clear') { clearCalculator(); return; }
  if (button.id === 'calc-use' && calculatorValue !== null) {
    if(!canUseCalculatorResult())return;
    if (calculatorReturnToFormulas && formulaView === 'manual') manualDraft().values[manualResultSlotKey()] = DC.fmt(calculatorValue);
    else syncDraft(DC.fmt(calculatorValue));
    $('calculator-dialog').close();
    if (!calculatorReturnToFormulas) $('answer')?.focus();
    return;
  }
  if (button.dataset.calc !== undefined) return pressCalculatorKey(button.dataset.calc);
});
document.addEventListener('submit', event => {
  if(event.target.id==='feedback-form'){event.preventDefault();submitFeedback();return;}
  if(event.target.id==='qa-login-form'){event.preventDefault();enterQA();return;}
  if (event.target.id === 'profile-form') { event.preventDefault(); submitProfile(); return; }
  if (event.target.id === 'manual-form') { event.preventDefault(); checkManualAnswer(); return; }
  if (event.target.id !== 'answer-form' && !event.target.hasAttribute('data-triangle-form')) return;
  event.preventDefault();
  checkAnswer(event.target.querySelector('[data-answer]')?.value ?? currentQuestion().draft);
});
document.addEventListener('input', event => {
  if(event.target.id==='qa-shabbat-progress'){window.ShabbatMode.setPreviewProgress(Number(event.target.value));return;}
  if(event.target.id==='custom-voltage'){customDraft.voltage=event.target.value;recalculateCustom();return;}
  if(event.target.dataset.customResistance!==undefined){customDraft.resistances[Number(event.target.dataset.customResistance)]=event.target.value;recalculateCustom();return;}
  if (event.target.hasAttribute('data-manual-list')) {
    manualState().list[event.target.dataset.manualList] = event.target.value;
    if (manualTokenKind(event.target.value) === 'invalid') event.target.setAttribute('aria-invalid','true');
    else event.target.removeAttribute('aria-invalid');
    syncManualEntryOrder();
    if(manualKeypadTarget===event.target)paintManualKeypad();
    saveCourse();
  }
  if (event.target.hasAttribute('data-manual-slot')) {
    // inputmode requests a keypad; validate input as well, including IME input.
    const input=event.target,clean=input.value.replace(/[^0-9.,]/g,'');
    let separator=false;
    input.value=[...clean].filter(char=>{if(!/[.,]/.test(char))return true;if(separator)return false;separator=true;return true;}).join('');
    const state = manualState(), draft = manualDraft(state);
    draft.values[event.target.dataset.manualSlot] = event.target.value;
    state.message = ''; state.errors = []; event.target.removeAttribute('aria-invalid');event.target.classList.remove('answer-incorrect');
    $('manual-message').textContent = '';
    if(manualKeypadTarget===event.target)paintManualKeypad();
    saveCourse();
  }
  if (event.target.hasAttribute('data-answer')) syncDraft(event.target.value, event.target);
  if (event.target.id === 'sim-voltage') { activeSimulatorQuestion().simVoltage = Number(event.target.value); updateSimulator(); }
  if(event.target.id==='calc-screen')invalidateCalculator();
});
document.addEventListener('change', event => {
  if(qaActive&&event.target.id.startsWith('qa-')) {
    const id=event.target.id,value=event.target.value;
    if(id==='qa-topic')qaGo(value,0,0);
    if(id==='qa-level')qaGo(tab,Number(value),0);
    if(id==='qa-exercise')qaGo(tab,levels[tab],Number(value));
    if(id==='qa-step')qaGo(tab,levels[tab],positions[tab][levels[tab]],Number(value));
    return;
  }
  if(event.target.id==='solved-exercises'){if(event.target.value)reviewSolvedExercise(event.target.value);return;}
  if(event.target.id==='custom-kind'){customDraft.kind=event.target.value;renderSimulatorPanel();$('custom-kind').focus({preventScroll:true});return;}
  if(event.target.id==='sim-circuit'){simulatorQuestion=completedCircuits().find(item=>item.id===event.target.value)?.q??null;renderSimulatorPanel();$('sim-circuit')?.focus({preventScroll:true});resizeFrame();return;}
  if(event.target.hasAttribute('data-preference')){
    const key=event.target.dataset.preference;
    personal.preferences[key]=key==='theme'?event.target.value:event.target.type==='checkbox'?event.target.checked:Number(event.target.value);
    savePersonal();applyPreferences();return;
  }
  if (event.target.id === 'sim-animation') { activeSimulatorQuestion().simAnimate = event.target.checked; updateSimulator(); }
});
document.addEventListener('keydown', event => {
  if(event.key==='Tab'&&!event.shiftKey&&event.target.hasAttribute('data-manual-slot')&&event.target===[...document.querySelectorAll('[data-manual-slot]')].at(-1))hideManualKeypad();
  if(event.key==='Escape'&&manualKeypadTarget){event.preventDefault();hideManualKeypad();$('formula-tab-manual').focus({preventScroll:true});return;}
  if(event.key==='Enter'&&event.target.hasAttribute('data-manual-slot')){event.preventDefault();nextManualTriangleField(event.target);return;}
  if(event.key==='Enter'&&event.target.hasAttribute('data-manual-list')){event.preventDefault();pressManualKey('enter');return;}
  if(event.target.matches('[data-manual-list],[data-manual-slot]')&&!event.ctrlKey&&!event.metaKey&&event.key.length===1){
    const allowed=event.target.hasAttribute('data-manual-list')?/[0-9.,xX?]/:/[0-9.,]/;
    if(!allowed.test(event.key)){event.preventDefault();return;}
  }
  if(['calc-numerator','calc-denominator'].includes(event.target.id)&&event.key==='Enter') {
    event.preventDefault();
    if(event.target.id==='calc-numerator')$('calc-denominator').focus();else insertCalculatorFraction();return;
  }
  if (event.target.id === 'calc-screen' && event.key === 'Enter') { event.preventDefault(); calculateScreen(); return; }
  const formulaTab = event.target.closest('.formula-tab[data-formula-tab]');
  if (formulaTab && ['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) {
    event.preventDefault();
    const views = ['reference','manual'], index = views.indexOf(formulaView==='help'?'manual':formulaView);
    formulaView = views[event.key === 'Home' ? 0 : event.key === 'End' ? views.length - 1 : (index + (event.key === 'ArrowLeft' ? 1 : views.length - 1)) % views.length];
    renderFormulas(); $('formula-tab-' + formulaView).focus(); $('formula-dialog').scrollTop = 0; return;
  }
  const button = event.target.closest('[data-tab]');
  if (!button || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
  event.preventDefault();
  const views=[...DC.kinds,'simulator'],index=views.indexOf(button.dataset.tab);
  selectTab(views[event.key==='Home'?0:event.key==='End'?views.length-1:(index+(event.key==='ArrowLeft'?1:views.length-1))%views.length]);$('tab-'+viewTab).focus();
});
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.addEventListener('cancel', event => {if(dialog.id==='profile-dialog'&&profileRequired)event.preventDefault();});
  dialog.addEventListener('close', () => {
    if(dialog.id==='formula-dialog')hideManualKeypad();
    if(window.ShabbatMode.isLocked()){calculatorReturnToFormulas=false;diagramReturnToFormulas=false;return;}
    if(dialog.id==='profile-dialog'&&profileRequired&&!qaActive){requestAnimationFrame(openProfile);return;}
    if (dialog.id === 'calculator-dialog' && calculatorReturnToFormulas) {
      calculatorReturnToFormulas = false;
      openDialog('formula-dialog', { preserveFormulaView:true });
      if(formulaView==='manual')focusManualEntry();else formulaAnswerField()?.focus();
    }
    if(dialog.id==='diagram-dialog'&&diagramReturnToFormulas){
      const fieldId=diagramReturnFieldId,scroll=diagramReturnScroll;
      diagramReturnToFormulas=false;diagramReturnFieldId=null;
      openDialog('formula-dialog',{preserveFormulaView:true});
      const field=fieldId?$(fieldId):null,button=$('formula-dialog').querySelector('[data-show-manual-circuit]');
      if(field&&!field.disabled)field.focus({preventScroll:true});
      else if(button?.getClientRects().length)button.focus({preventScroll:true});
      else $('formula-tab-manual').focus({preventScroll:true});
      requestAnimationFrame(()=>{$('formula-dialog').scrollTop=scroll;fitDialogs();});
    }
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    if(dialog.id==='profile-dialog'&&profileRequired)return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
});
window.addEventListener('resize', () => { syncQuickbar();hideIconTooltip();fitDialogs(); resizeFrame(); });
window.visualViewport?.addEventListener('resize', fitDialogs);
try { if (window.parent !== window) { window.parent.addEventListener('scroll', handleViewportScroll, true); window.parent.addEventListener('resize', handleViewportScroll); } } catch {}
window.addEventListener('scroll',handleViewportScroll,{passive:true});
// A component iframe can be taller than the page viewport. Follow the host's
// scrolling container so the quick tools remain at the visible top edge.
function syncQuickbar() {
  let top=0;
  try {
    const frame=window.frameElement?.getBoundingClientRect();
    if(frame)top=Math.min(Math.max(0,-frame.top),Math.max(0,innerHeight-58));
  } catch {}
  document.documentElement.style.setProperty('--quickbar-top',`${top}px`);
}
function handleViewportScroll(){syncQuickbar();hideIconTooltip();fitDialogs();}
let iconTipTimer=null,iconTipHideTimer=null,iconTipButton=null,iconPressOrigin=null,iconSuppressButton=null,iconSuppressUntil=0;
function hideIconTooltip(){
  clearTimeout(iconTipTimer);clearTimeout(iconTipHideTimer);
  if(iconTipButton)iconTipButton.removeAttribute('aria-describedby');
  iconTipButton=null;
  $('icon-tooltip').hidden=true;
}
function showIconTooltip(button){
  if(!button.isConnected)return;
  hideIconTooltip();iconTipButton=button;
  const tip=$('icon-tooltip'),rect=button.getBoundingClientRect();
  tip.textContent=button.dataset.tooltip;tip.hidden=false;
  button.setAttribute('aria-describedby','icon-tooltip');
  tip.style.top=`${rect.bottom+7}px`;
  tip.style.left=`${Math.max(12,Math.min(innerWidth-tip.offsetWidth-12,rect.left+(rect.width-tip.offsetWidth)/2))}px`;
}
const tooltipButton=event=>event.target.closest?.('button[data-tooltip]');
// Delegate events so newly rendered exercise tools behave like the fixed quickbar.
document.addEventListener('pointerover',event=>{
  const button=tooltipButton(event);
  if(button&&event.pointerType==='mouse'&&!button.contains(event.relatedTarget))showIconTooltip(button);
});
document.addEventListener('pointerout',event=>{
  const button=tooltipButton(event);
  if(button&&event.pointerType==='mouse'&&!button.contains(event.relatedTarget))hideIconTooltip();
});
document.addEventListener('focusin',event=>{const button=tooltipButton(event);if(button)showIconTooltip(button);});
document.addEventListener('focusout',event=>{if(tooltipButton(event))hideIconTooltip();});
document.addEventListener('contextmenu',event=>{if(tooltipButton(event))event.preventDefault();});
document.addEventListener('pointerdown',event=>{
  const button=tooltipButton(event);if(!button||button.disabled||event.pointerType==='mouse')return;
  hideIconTooltip();iconPressOrigin={button,id:event.pointerId,x:event.clientX,y:event.clientY};
  iconTipTimer=setTimeout(()=>{if(!iconPressOrigin||!button.isConnected)return;showIconTooltip(button);iconSuppressButton=button;iconSuppressUntil=performance.now()+10000;},500);
});
document.addEventListener('pointermove',event=>{
  if(iconPressOrigin&&event.pointerId===iconPressOrigin.id&&Math.hypot(event.clientX-iconPressOrigin.x,event.clientY-iconPressOrigin.y)>10){iconPressOrigin=null;hideIconTooltip();}
});
document.addEventListener('pointerup',event=>{
  if(!iconPressOrigin||event.pointerId!==iconPressOrigin.id)return;
  clearTimeout(iconTipTimer);
  if(iconSuppressButton===iconPressOrigin.button&&iconSuppressUntil>performance.now()){
    iconSuppressUntil=performance.now()+600;iconTipHideTimer=setTimeout(hideIconTooltip,2200);
  }
  iconPressOrigin=null;
});
document.addEventListener('pointercancel',()=>{iconPressOrigin=null;hideIconTooltip();});
document.addEventListener('keydown',event=>{if(event.key==='Escape')hideIconTooltip();});
document.addEventListener('click',event=>{
  const button=tooltipButton(event);if(!button)return;
  if(button===iconSuppressButton&&performance.now()<iconSuppressUntil){event.preventDefault();event.stopImmediatePropagation();return;}
  hideIconTooltip();
},true);

function paintPublicRatings(summary,publicURL){
  const count=summary?.count,average=summary?.average;
  const valid=summary?.available===true&&Number.isSafeInteger(count)&&count>=0&&(count===0||Number.isFinite(average)&&average>=1&&average<=5);
  $('public-rating').hidden=!valid;
  $('rating-status').hidden=valid;
  $('rating-status').textContent=summary?'תוצאות הדירוג אינן זמינות כרגע. אפשר לנסות שוב בהמשך.':'תוצאות הדירוג נטענות…';
  document.querySelectorAll('[data-public-rating-text]').forEach(node=>{
    node.hidden=!valid||(node.closest('#feedback-dialog')&&feedbackMode==='note');
    node.textContent=!valid?'':count===0?'עדיין לא התקבלו דירוגים':`${average.toFixed(1)} מתוך 5 · ${count===1?'דירוג אחד':count+' דירוגים'}`;
  });
  $('public-rating-fill').style.width=valid&&count?`${average/5*100}%`:'0%';
  document.querySelector('.public-rating-stars').hidden=!valid||!count;
  const link=$('public-reviews-link');
  link.hidden=!valid||typeof publicURL!=='string'||!/^https:\/\/github\.com\/[^/]+\/[^/]+\/issues(?:\/\d+)?$/.test(publicURL);
  if(!link.hidden)link.href=publicURL;
}
let contactAvailability={review:false,note:false},feedbackMode='review',feedbackPending=null,feedbackTimeout=null,feedbackRating=null;
let lastRatingSummary=null,lastPublicFeedbackURL='';
const contactDrafts={review:{subject:'',message:'',rating:null,context:false},note:{subject:'',message:'',rating:null,context:true}};
function feedbackContext(){
  const q=currentQuestion();
  return `${topicNames[tab]??'סימולטור'} · ${DC.levelNames[levels[tab]]??''} · תרגיל ${positions[tab][levels[tab]]+1} · סעיף ${q.cursor+1}`;
}
function rememberContactDraft(){
  if(!feedbackMode)return;
  contactDrafts[feedbackMode]={subject:$('feedback-subject').value,message:$('feedback-message').value,
    rating:feedbackMode==='review'?feedbackRating:null,context:$('feedback-context').checked};
}
function paintFeedbackAvailability(){
  const enabled=contactAvailability[feedbackMode]===true;
  $('feedback-send').disabled=!enabled||!!feedbackPending;
  $('feedback-send').textContent=feedbackPending?'שולחים…':feedbackMode==='review'?'שליחת משוב ודירוג':'שליחת הערה';
  document.querySelectorAll('[data-contact-mode]').forEach(button=>button.disabled=!!feedbackPending);
  if(!feedbackPending&&!enabled){
    $('feedback-status').className='feedback';
    $('feedback-status').textContent='שליחת הפנייה הזו עדיין לא זמינה. אפשר לנסות שוב בהמשך.';
  }
}
function openContact(){
  if($('feedback-dialog').open)rememberContactDraft();
  paintFeedbackAvailability();openDialog('contact-dialog');
}
function openFeedback(mode){
  if(!['review','note'].includes(mode)||feedbackPending)return;
  rememberContactDraft();feedbackMode=mode;
  const review=mode==='review',draft=contactDrafts[mode];
  $('feedback-title').textContent=review?'משוב ודירוג אפליקציה':'הערות';
  $('feedback-disclosure').textContent=review?'דירוג הכוכבים חובה. אפשר לצרף מלל. המשוב והדירוג יפורסמו ב־GitHub ויהיו גלויים לכולם.':'ההערה תישלח לעומר באופן פרטי. רק בעלי הרשאה למאגר ההערות יוכלו לקרוא אותה.';
  document.querySelectorAll('[data-review-only]').forEach(node=>node.hidden=!review);
  document.querySelectorAll('[data-note-only]').forEach(node=>node.hidden=review);
  $('feedback-message-label').textContent=review?'מה דעתכם על האפליקציה? (רשות)':'ההערה שלכם';
  $('feedback-message').required=!review;
  $('feedback-subject').value=draft.subject;$('feedback-message').value=draft.message;
  $('feedback-context').checked=draft.context;$('feedback-context-label').textContent=feedbackContext();
  document.querySelectorAll('[name="feedback-rating"]').forEach(input=>input.required=review);
  updateFeedbackRating(review?draft.rating:null);
  $('feedback-subject').removeAttribute('aria-invalid');$('feedback-message').removeAttribute('aria-invalid');
  $('feedback-rating-group').removeAttribute('aria-invalid');
  $('feedback-status').textContent='';$('feedback-status').className='feedback';$('feedback-result-link').hidden=true;
  paintFeedbackAvailability();paintPublicRatings(lastRatingSummary,lastPublicFeedbackURL);openDialog('feedback-dialog');
}
function updateFeedbackRating(value){
  feedbackRating=value;
  document.querySelectorAll('[name="feedback-rating"]').forEach(input=>{
    input.checked=Number(input.value)===value;
    input.closest('label').classList.toggle('rated',value!==null&&Number(input.value)<=value);
  });
  $('feedback-rating-label').textContent=value===null?'עדיין לא נבחר דירוג':`${value} מתוך 5 כוכבים`;
  if(value!==null)$('feedback-rating-group').removeAttribute('aria-invalid');
}
document.querySelectorAll('[name="feedback-rating"]').forEach(input=>input.addEventListener('change',()=>updateFeedbackRating(Number(input.value))));
$('feedback-rating-clear').addEventListener('click',()=>updateFeedbackRating(null));
$('feedback-dialog').addEventListener('close',rememberContactDraft);
function submitFeedback(){
  if(!contactAvailability[feedbackMode]||feedbackPending)return;
  const subject=$('feedback-subject'),message=$('feedback-message'),status=$('feedback-status'),review=feedbackMode==='review';
  message.removeAttribute('aria-invalid');
  if(review&&feedbackRating===null){
    status.className='feedback error';status.textContent='יש לבחור דירוג של 1–5 כוכבים.';
    $('feedback-rating-group').setAttribute('aria-invalid','true');
    document.querySelector('[name="feedback-rating"]').focus();fitDialogs();return;
  }
  if(!review&&message.value.trim().length<5){
    status.className='feedback error';status.textContent='יש לכתוב הערה באורך של לפחות 5 תווים.';
    message.setAttribute('aria-invalid','true');message.focus();fitDialogs();return;
  }
  const id=crypto.randomUUID?.()??`feedback-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  feedbackPending={id,mode:feedbackMode};rememberContactDraft();
  status.className='feedback';status.textContent='שולחים את הפנייה לעומר…';
  $('feedback-result-link').hidden=true;paintFeedbackAvailability();
  sendStreamlitMessage('streamlit:setComponentValue',{value:{
    type:'feedback',id,mode:feedbackMode,subject:review?'':subject.value.trim(),message:message.value.trim(),rating:review?feedbackRating:null,
    context:!review&&$('feedback-context').checked?$('feedback-context-label').textContent:''
  },dataType:'json'});
  feedbackTimeout=setTimeout(()=>{
    if(!feedbackPending)return;
    status.className='feedback error';status.textContent='השליחה מתעכבת. אפשר להמתין לאישור או לנסות שוב בהמשך.';
    feedbackPending=null;paintFeedbackAvailability();fitDialogs();
  },25000);
  fitDialogs();
}
window.addEventListener('message',event=>{
  if(event.source!==window.parent||event.data?.type!=='streamlit:render')return;
  const args=event.data.args??{};
  contactAvailability={review:args.contact_availability?.review===true,note:args.contact_availability?.note===true};
  lastRatingSummary=args.rating_summary;lastPublicFeedbackURL=args.public_feedback_url??'';
  paintPublicRatings(lastRatingSummary,lastPublicFeedbackURL);
  const reply=args.feedback_response;
  if(reply&&reply.id===feedbackPending?.id){
    const mode=feedbackPending.mode;clearTimeout(feedbackTimeout);feedbackPending=null;
    const status=$('feedback-status');status.className=`feedback ${reply.ok?'success':'error'}`;status.textContent=reply.message;
    if(reply.ok){
      contactDrafts[mode]={subject:'',message:'',rating:null,context:mode==='note'};
      if(feedbackMode===mode){$('feedback-subject').value='';$('feedback-message').value='';updateFeedbackRating(null);}
      if(mode==='review'&&typeof reply.url==='string'&&/^https:\/\/github\.com\/[^/]+\/[^/]+\/issues\/\d+$/.test(reply.url)){
        const link=$('feedback-result-link');link.href=reply.url;link.hidden=false;
      }
    }
  }
  paintFeedbackAvailability();syncQuickbar();fitDialogs();resizeFrame();
});


/* COURSE_EXTENSION */
window.ShabbatMode.configure({isQA:()=>qaActive,canUseApp:()=>qaActive||profileReady(),onUnlock:()=>{if(!qaActive&&!profileReady())openProfile();}});
CourseApp.initialize();
sendStreamlitMessage('streamlit:componentReady', { apiVersion:1 });
if(!restoreCourse())newCourse();
initializePersonal();
function finishInitialLayout(){
  applyPreferences();
  const app = $('app'), started = performance.now();
  let viewport = '', unchangedSince = started;
  function settleLayout(){
    const nextViewport = `${innerWidth}x${innerHeight}`;
    if (nextViewport !== viewport) {
      viewport = nextViewport; unchangedSince = performance.now();
      // Rebuild every section's layout after the host applies its frame size.
      // This is done while hidden, without changing text preferences or DOM nodes.
      const display = app.style.getPropertyValue('display'), priority = app.style.getPropertyPriority('display');
      app.style.setProperty('display','none','important');
      void app.offsetHeight;
      if (display) app.style.setProperty('display',display,priority); else app.style.removeProperty('display');
      void app.offsetHeight;
    }
    syncQuickbar();fitDialogs();resizeFrame();
    const heightApplied = window.parent === window || Math.abs(innerHeight-lastFrameHeight) <= 2;
    const quiet = performance.now()-unchangedSince >= 80;
    if (quiet && (heightApplied || performance.now()-started >= 1500)) {
      document.documentElement.classList.add('ui-ready');
    } else requestAnimationFrame(settleLayout);
  }
  requestAnimationFrame(settleLayout);
}
if(document.fonts?.ready)document.fonts.ready.then(finishInitialLayout);else finishInitialLayout();
window.addEventListener('pageshow',event=>{
  followSystemTheme();
  if(event.persisted){document.documentElement.classList.remove('ui-ready');finishInitialLayout();}
});
function followSystemTheme() {
  if(personal.preferences.theme==='system'&&document.documentElement.classList.contains('dark-mode')!==systemPrefersDark())applyPreferences();
}
if (systemColorScheme.addEventListener) systemColorScheme.addEventListener('change',followSystemTheme);
else systemColorScheme.addListener(followSystemTheme);
window.addEventListener('focus',followSystemTheme);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)followSystemTheme();});
const followHostVisibility = () => { if(!systemThemeContext.document.hidden)followSystemTheme(); };
if(systemThemeContext!==window){
  systemThemeContext.addEventListener('focus',followSystemTheme);
  systemThemeContext.addEventListener('pageshow',followSystemTheme);
  systemThemeContext.document.addEventListener('visibilitychange',followHostVisibility);
}
window.addEventListener('pagehide',event=>{
  if(event.persisted)return;
  if(systemColorScheme.removeEventListener)systemColorScheme.removeEventListener('change',followSystemTheme);
  else systemColorScheme.removeListener(followSystemTheme);
  if(systemThemeContext!==window){
    systemThemeContext.removeEventListener('focus',followSystemTheme);
    systemThemeContext.removeEventListener('pageshow',followSystemTheme);
    systemThemeContext.document.removeEventListener('visibilitychange',followHostVisibility);
  }
});
window.addEventListener('pagehide',saveCourse);
if ('ResizeObserver' in window) new ResizeObserver(resizeFrame).observe($('app'));

</script>
</body>
</html>
'''

def feedback_configuration():
    """One server-side token with access to the public and private destinations."""
    defaults = {"public_repository": "OBE-26/electricitey-project", "private_repository": "OBE-26/electricity-feedback"}
    try:
        config = st.secrets.get("github_feedback", {})
        token = str(config.get("token", "")).strip()
        public = str(config.get("public_repository", defaults["public_repository"])).strip()
        private = str(config.get("private_repository", config.get("repository", defaults["private_repository"]))).strip()
    except (FileNotFoundError, KeyError):
        return {"token": "", **defaults}
    def valid_repository(value):
        return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", value)) and value.split("/", 1)[1] not in {".", ".."}
    return {"token": token, "public_repository": public if valid_repository(public) else "",
            "private_repository": private if valid_repository(private) else ""}


def github_feedback_request(token, repository, suffix="", payload=None, method=None):
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}{suffix}", data=data,
        method=method or ("GET" if payload is None else "POST"),
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "X-GitHub-Api-Version": "2026-03-10",
                 "User-Agent": "OBE-26-Electricity-Contact"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.load(response)


def require_contact_repository(token, repository, private):
    """Visibility is checked immediately before each write, without caching."""
    if not token or not repository:
        raise ValueError("Contact destination is not configured")
    details = github_feedback_request(token, repository)
    if not isinstance(details, dict) or details.get("private") is not private or details.get("has_issues") is not True:
        raise ValueError("Contact destination has the wrong visibility or Issues are disabled")


@st.cache_data(ttl=60, show_spinner=False)
def contact_channel_available(token, repository, private):
    try:
        require_contact_repository(token, repository, private)
        return True
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


@st.cache_data(ttl=60, show_spinner=False)
def public_rating_summary(token, repository):
    """Read public reviews only; private notes never contribute to ratings."""
    unavailable = {"available": False, "count": 0, "average": None, "summary_issue": None}
    try:
        require_contact_repository(token, repository, False)
        total, count, page, seen, summary_issue = 0, 0, 1, set(), None
        deadline = time.monotonic() + 20
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError("Rating aggregation timed out")
            before_count = len(seen)
            issues = github_feedback_request(token, repository, f"/issues?state=all&per_page=100&page={page}&sort=created&direction=asc")
            if not isinstance(issues, list):
                raise ValueError("Invalid issue list")
            for issue in issues:
                if not isinstance(issue, dict) or "pull_request" in issue:
                    continue
                number = issue.get("number")
                if type(number) is not int or number in seen:
                    continue
                seen.add(number)
                body = str(issue.get("body", ""))
                if body.startswith("<!-- dc-basics-rating-summary:v1 -->"):
                    summary_issue = summary_issue or number
                    continue
                if not str(issue.get("title", "")).startswith("[דירוג האפליקציה] "):
                    continue
                match = re.search(r"\n<!-- dc-basics-public-review:v1 rating=([1-5]) -->\s*\Z", body)
                if match:
                    total += int(match.group(1))
                    count += 1
            if len(issues) < 100:
                break
            if len(seen) == before_count:
                raise ValueError("Issue pagination did not advance")
            page += 1
        return {"available": True, "count": count, "average": round(total / count, 1) if count else None,
                "summary_issue": summary_issue}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return unavailable


@st.cache_resource
def rating_summary_lock():
    return threading.Lock()


def update_github_rating_summary(token, repository):
    """Create one summary issue, then update that same issue after each review."""
    with rating_summary_lock():
        require_contact_repository(token, repository, False)
        public_rating_summary.clear()
        summary = public_rating_summary(token, repository)
        if not summary["available"]:
            raise ValueError("Rating summary is unavailable")
        count, average = summary["count"], summary["average"]
        count_label = "דירוג אחד" if count == 1 else f"{count} דירוגים"
        score = f"**{average:.1f} מתוך 5** · **{count_label}**" if count else "עדיין לא התקבלו דירוגים."
        body = "\n\n".join([
            "<!-- dc-basics-rating-summary:v1 -->", "# סיכום דירוג האפליקציה", score,
            "הממוצע מחושב מכל הדירוגים הציבוריים שנשלחו דרך האפליקציה.",
            f"[צפייה במשובים ובמלל](https://github.com/{repository}/issues)",
            "הערות שנשלחו במסלול הפרטי נשמרות בנפרד ואינן מוצגות כאן.",
        ])
        number = summary["summary_issue"]
        # Recheck visibility after reading the ratings and before publishing.
        require_contact_repository(token, repository, False)
        result = github_feedback_request(token, repository, f"/issues/{number}" if number else "/issues",
            {"title": "סיכום דירוג האפליקציה", "body": body}, method="PATCH" if number else "POST")
        created_number = result.get("number") if isinstance(result, dict) else None
        if type(created_number) is not int or created_number < 1:
            raise ValueError("Missing summary issue number")
        public_rating_summary.clear()
        return created_number


def send_contact_message(token, repository, mode, subject, message, rating, context):
    require_contact_repository(token, repository, mode == "note")
    if mode == "review":
        title = f"[דירוג האפליקציה] {rating}/5"
        details = ["משוב ודירוג אפליקציה", f"דירוג: {'★' * rating}{'☆' * (5-rating)} ({rating}/5)"]
        if message:
            details += ["", message]
        details += ["", f"<!-- dc-basics-public-review:v1 rating={rating} -->"]
    else:
        title = "[הערה פרטית] " + (subject or "הערה לאפליקציה")
        details = ["הערה פרטית שנשלחה לעומר", "", message]
        if context:
            details += ["", "מיקום בתרגול:", context]
        details += ["", "<!-- dc-basics-private-note:v1 -->"]
    result = github_feedback_request(token, repository, "/issues", {"title": title, "body": "\n".join(details)})
    number = result.get("number") if isinstance(result, dict) else None
    if type(number) is not int or number < 1:
        raise ValueError("Missing issue number")
    return number


def handle_feedback(event, config, session):
    mode = event.get("mode")
    if not isinstance(mode, str) or mode not in {"review", "note"}:
        return {"ok": False, "message": "יש לבחור משוב ודירוג אפליקציה או הערות."}
    token = config["token"]
    repository = config["public_repository" if mode == "review" else "private_repository"]
    if not token or not repository:
        return {"ok": False, "message": "שליחת הפנייה עדיין לא זמינה. אפשר לנסות שוב בהמשך."}
    subject, message = event.get("subject", ""), event.get("message", "")
    rating, context = event.get("rating"), event.get("context", "")
    if not isinstance(subject, str) or len(subject) > 120:
        return {"ok": False, "message": "נושא ההערה יכול לכלול עד 120 תווים."}
    if not isinstance(message, str) or len(message.strip()) > 4000 or (mode == "note" and len(message.strip()) < 5):
        return {"ok": False, "message": "יש לכתוב הערה באורך 5–4,000 תווים." if mode == "note" else "המלל יכול לכלול עד 4,000 תווים."}
    if mode == "review" and (type(rating) is not int or not 1 <= rating <= 5):
        return {"ok": False, "message": "יש לבחור דירוג של 1–5 כוכבים לפני שליחת המשוב."}
    if mode == "note" and rating is not None:
        return {"ok": False, "message": "את דירוג האפליקציה שולחים דרך משוב ודירוג אפליקציה."}
    if not isinstance(context, str) or len(context) > 400 or (mode == "review" and context):
        return {"ok": False, "message": "לא ניתן לצרף את מיקום התרגיל לפנייה הזו."}
    now = time.monotonic()
    rate_key = "dc_contact_last_attempt_" + mode
    if now - session.get(rate_key, float("-inf")) < 30:
        return {"ok": False, "message": "יש להמתין חצי דקה בין פניות מאותו סוג."}
    session[rate_key] = now
    try:
        number = send_contact_message(token, repository, mode, subject.strip(), message.strip(), rating, context.strip())
    except urllib.error.HTTPError:
        return {"ok": False, "message": "לא הצלחנו לשלוח את הפנייה כרגע. אפשר לנסות שוב בהמשך."}
    except ValueError:
        return {"ok": False, "message": "הפנייה לא נשלחה. יש לבדוק את הגדרת מסלול הפנייה."}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"ok": False, "message": "לא התקבל אישור לשליחה. הטקסט נשאר בטופס; אפשר לנסות שוב בהמשך."}
    if mode == "note":
        return {"ok": True, "message": "תודה! ההערה נשלחה לעומר באופן פרטי."}
    result = {"ok": True, "message": "תודה! המשוב והדירוג פורסמו.", "url": f"https://github.com/{repository}/issues/{number}"}
    # A summary failure must not turn an already-published review into a failed
    # submission or cause a duplicate when the component reruns.
    try:
        update_github_rating_summary(token, repository)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        public_rating_summary.clear()
        result["message"] = "תודה! המשוב והדירוג פורסמו. עדכון פניית הסיכום לא הושלם כרגע."
    return result


st.set_page_config(page_title="יסודות החשמל | תרגול DC", layout="wide")
st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"]{background:#fff8e8}
[data-testid="stMainBlockContainer"],.block-container{max-width:1220px;padding:.5rem .25rem 1rem}
[data-testid="stHeader"]{display:none}
@media(max-width:600px){[data-testid="stMainBlockContainer"],.block-container{padding:.25rem 0 .5rem}}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def frontend_directory(html):
    directory = Path(tempfile.mkdtemp(prefix="dc_basics_"))
    (directory / "index.html").write_text(html, encoding="utf-8")
    return str(directory)

asset_root = Path(__file__).resolve().parent
extension = (asset_root / "course_practice.js").read_text(encoding="utf-8") + "\n" + (asset_root / "courses.js").read_text(encoding="utf-8")
APP_HTML = APP_HTML.replace("/* COURSE_EXTENSION */", extension)

@st.cache_resource
def shared_course_service(repository, token, admin_password, bank_revision, backend_revision):
    # A rerun can retain classes imported from a previous deployment in sys.modules.
    # Compile the deployed source into its own namespace on each cache miss.
    # Existing services keep their globals; the revision selects the new service.
    backend_path = asset_root / "course_backend.py"
    backend = types.ModuleType("dc_course_backend_" + backend_revision)
    backend.__file__ = str(backend_path)
    exec(compile(backend_path.read_bytes(), str(backend_path), "exec"), backend.__dict__)
    return backend.CourseService(backend.ConfigStore(repository=repository, token=token), asset_root / "data/questions.json", admin_password)

practice = components.declare_component("dc_electricity_basics", path=frontend_directory(APP_HTML))
contact_config = feedback_configuration()
contact_token = contact_config["token"]
public_repository = contact_config["public_repository"]
private_repository = contact_config["private_repository"]
review_ready = contact_channel_available(contact_token, public_repository, False)
note_ready = contact_channel_available(contact_token, private_repository, True)
rating_summary = public_rating_summary(contact_token, public_repository)
try:
    admin_settings = st.secrets.get("course_admin", {})
except Exception:
    admin_settings = {}
course_service = shared_course_service(
    str(admin_settings.get("storage_repository", "")),
    str(admin_settings.get("storage_token", contact_token)),
    str(admin_settings.get("password", "210592")),
    hashlib.sha256((asset_root / "data/questions.json").read_bytes()).hexdigest(),
    hashlib.sha256((asset_root / "course_backend.py").read_bytes()).hexdigest(),
)
try:
    course_public_config = course_service.store.public()
except (OSError, ValueError, urllib.error.URLError):
    course_public_config = {"names": {"hvac": "קורס מיזוג וקירור", "security": "קורס מיגון", "mobile": "קורס סלולר"}, "unavailable": True}
feedback_event = practice(
    key="dc_electricity_basics_v1", default=None,
    contact_availability={"review": review_ready, "note": note_ready},
    rating_summary=rating_summary,
    public_feedback_url=(f"https://github.com/{public_repository}/issues/" + str(rating_summary["summary_issue"]) if rating_summary.get("summary_issue") else f"https://github.com/{public_repository}/issues") if review_ready else "",
    feedback_response=st.session_state.get("dc_feedback_reply"),
    course_config=course_public_config,
    course_response=st.session_state.get("dc_course_reply"),
)
if isinstance(feedback_event, dict) and feedback_event.get("type") == "feedback":
    submission_id = feedback_event.get("id", "")
    if isinstance(submission_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{8,80}", submission_id):
        completed = st.session_state.setdefault("dc_feedback_completed", {})
        if submission_id not in completed:
            result = handle_feedback(feedback_event, contact_config, st.session_state)
            completed[submission_id] = result
            while len(completed) > 40:
                completed.pop(next(iter(completed)))
            st.session_state["dc_feedback_reply"] = {"id": submission_id, **result}
            st.rerun()

if isinstance(feedback_event, dict) and feedback_event.get("type") == "course":
    request_id = feedback_event.get("id", "")
    if isinstance(request_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{8,80}", request_id):
        completed_requests = st.session_state.setdefault("dc_course_completed", {})
        if request_id not in completed_requests:
            result = course_service.handle(feedback_event, st.session_state)
            completed_requests[request_id] = result
            while len(completed_requests) > 40:
                completed_requests.pop(next(iter(completed_requests)))
            st.session_state["dc_course_reply"] = {"request_id": request_id, **result}
            st.rerun()

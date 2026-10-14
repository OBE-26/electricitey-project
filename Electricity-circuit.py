""יסודות החשמל — תרגול מעגלים חשמליים.

Single-file Streamlit app. All browser assets are embedded; no database is needed.
Install: python -m pip install streamlit
Run:     streamlit run electricity_basics.py

Includes Ohm/power, series and parallel practice, interactive formula triangles,
four-operation calculator and a DC circuit simulator with resistive lamp models.
Each visit creates a fresh set of 35 exercises. Recent question signatures are
kept in browser storage to avoid immediate repeats; no student identity is stored.
"""
from pathlib import Path
import tempfile
import streamlit as st
import streamlit.components.v1 as components

APP_HTML = r'''<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>יסודות החשמל | תרגול DC</title>
  <style>
    :root{color-scheme:light;--paper:#f4f5f1;--card:#fffefa;--ink:#182e3c;--muted:#5b6f78;--line:#dce3df;--green:#116e65;--soft:#e7f1ed;--amber:#a65b20;--shadow:0 8px 28px #182e3c08}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,"Noto Sans Hebrew",sans-serif;line-height:1.65;text-align:right}button,input,select{font:inherit}button{cursor:pointer;touch-action:manipulation}button:disabled{opacity:.48;cursor:default}button,input{font-size:16px}input[aria-invalid=true]{border-color:#b05242!important}button{border:0}button:focus-visible,input:focus-visible,summary:focus-visible,a:focus-visible{outline:3px solid #c38330;outline-offset:3px}[hidden]{display:none!important}h1,h2,h3,p{margin-top:0}h1,h2,h3{line-height:1.35}h1{font-size:clamp(30px,5vw,46px);letter-spacing:-.04em;margin-bottom:12px}h2{font-size:25px;margin-bottom:8px}h3{font-size:20px;margin-bottom:12px}p{margin-bottom:12px}bdi,.math{direction:ltr;unicode-bidi:isolate;font-variant-numeric:tabular-nums}bdi{display:inline-block}.math{display:block;text-align:left}input.numeric{direction:ltr;text-align:left;font-variant-numeric:tabular-nums}
    .app{max-width:1160px;margin:auto;padding:22px 24px 40px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:22px;border-bottom:1px solid var(--line)}.identity{display:flex;align-items:center;gap:12px}.brand-icon{background:var(--ink);color:white;border-radius:14px;width:46px;height:46px;display:grid;place-items:center;font-size:27px}.brand-title{font-weight:700;font-size:18px}.eyebrow{color:var(--green);font-weight:700;font-size:12px;letter-spacing:.06em}.muted{color:var(--muted)}.small{font-size:13px}.top-tools{display:flex;gap:8px;flex-wrap:wrap}
    .btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:46px;padding:10px 17px;border-radius:11px;color:white;background:var(--green);font-weight:700;border:1px solid transparent;line-height:1.45}.btn.secondary{background:var(--card);color:var(--ink);border-color:var(--line)}.btn.soft{background:var(--soft);color:var(--green)}.btn.tiny{font-size:14px;min-height:40px;padding:8px 11px}.btn:hover:enabled{filter:brightness(.97)}.text-btn{background:none;color:var(--green);text-decoration:underline;padding:8px;min-height:40px}.hero{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:32px 0 24px}.hero-copy{max-width:710px}.hero-copy p{color:var(--muted);font-size:17px}.hero-symbol{width:150px;height:150px;border-radius:28px;border:1px solid #cdded7;background:linear-gradient(140deg,#e9f0e8,#f9f5e8);display:grid;place-content:center;direction:ltr;text-align:center;color:var(--green);font-size:31px;font-weight:700;flex-shrink:0;transform:rotate(-3deg)}.hero-symbol small{font-size:13px;color:var(--muted);font-weight:400;margin-top:8px}.pills{display:flex;flex-wrap:wrap;gap:7px}.pill{border:1px solid var(--line);background:var(--card);padding:4px 10px;border-radius:20px;font-size:12px;color:var(--muted)}
    .tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:8px 0 22px}.tab{min-height:64px;padding:12px 16px;background:#e8ede7;border-radius:13px;color:var(--muted);font-weight:700;text-align:right}.tab span{font-size:12px;font-weight:400;display:block;margin-top:2px}.tab[aria-selected=true]{background:var(--ink);color:white}.course-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.levels{display:flex;gap:7px;flex-wrap:wrap}.level{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 13px;min-height:46px;color:var(--muted);font-weight:700}.level[aria-pressed=true]{color:var(--green);border-color:var(--green);box-shadow:inset 0 0 0 1px var(--green)}.level small{display:block;font-weight:400;font-size:12px}.card{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:var(--shadow)}.progress-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;font-size:14px}.question-dots{display:flex;gap:6px;direction:ltr}.question-dot{height:9px;width:23px;border-radius:5px;background:var(--line)}.question-dot.current{background:#80b5a6}.question-dot.done{background:var(--green)}.progress-track{height:5px;background:var(--line);border-radius:5px;overflow:hidden;margin-bottom:22px}.progress-track>div{height:100%;background:var(--green);transition:width .25s;}
    .exercise-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:18px;align-items:start}.exercise-title{margin-bottom:16px}.givens{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.given{background:#f1f4ed;border:1px solid #e0e7dc;border-radius:10px;padding:8px 12px;min-width:92px}.given small{display:block;color:var(--muted);font-size:12px}.given bdi{font-weight:700;font-size:19px}.diagram{margin:8px 0 0;overflow-x:auto;max-width:100%}.diagram svg{display:block;width:100%;height:auto;min-width:0}.diagram figcaption{color:var(--muted);font-size:12px;margin-top:5px}.flow{stroke-dasharray:7 20;animation:currentFlow 2.4s linear infinite}@keyframes currentFlow{to{stroke-dashoffset:-216}}
    .step-list{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}.step-pill{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;border-radius:50%;font-size:12px;border:1px solid var(--line);color:var(--muted)}.step-pill.done{background:var(--soft);color:var(--green);border-color:#b4d2c7}.step-pill.active{background:var(--ink);color:white;border-color:var(--ink)}.task-kicker{color:var(--green);font-weight:700;font-size:13px;margin-bottom:5px}.answer-row{display:flex;gap:9px;margin:14px 0 6px;align-items:center}.answer-wrap{display:flex;align-items:center;gap:10px;flex:1;min-width:0}.answer-wrap input{min-width:0;width:100%;min-height:52px;border:2px solid #b9cec3;border-radius:11px;padding:10px 12px;background:white;font-size:23px;color:var(--ink)}.unit{font-size:19px;color:var(--muted)}.answer-tools{display:flex;flex-wrap:wrap;gap:7px;margin:16px 0}.rounding{font-size:13px;color:var(--muted)}.feedback{border-radius:10px;padding:11px 13px;margin-top:12px;line-height:1.7}.feedback:empty{display:none}.feedback.error{background:#fff0ed;color:#933b32}.feedback.success{background:#e2f1e9;color:#126044}.hint{background:#f7f1df;border:1px solid #eadcbc;border-radius:12px;padding:14px;margin:12px 0;font-size:14px}.hint strong{display:block;margin-bottom:5px}.solution{border-inline-start:3px solid var(--green);padding:11px 15px;background:#f1f6ef;border-radius:8px;margin:12px 0}.solution .math{font-size:21px;font-weight:700;overflow-wrap:anywhere;margin:6px 0}.solution p{font-size:14px;color:var(--muted);margin-bottom:0}.completed-steps{margin-top:18px;border-top:1px solid var(--line);padding-top:12px}.completed-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:7px 0;font-size:14px}.completed-row bdi{font-weight:700}.complete-badge{color:var(--green);background:var(--soft);font-size:13px;border-radius:20px;padding:6px 12px;display:inline-block;margin-bottom:14px}.completion-actions{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0 0}.success-summary{border-color:#b9d9c9}.level-note{border:1px dashed #b9cfc2;border-radius:12px;padding:12px;margin-top:14px;font-size:14px;color:var(--muted)}
    .simulator{margin-top:20px}.sim-head{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}.sim-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(240px,.55fr);gap:20px;align-items:start}.sim-controls{padding:18px;background:#f1f4ed;border-radius:13px}.sim-controls label{display:block;font-weight:700;font-size:14px}.sim-controls input[type=range]{width:100%;accent-color:var(--green);margin:12px 0;min-height:36px}.sim-value{font-size:24px;color:var(--green);font-weight:700}.toggle{display:flex!important;align-items:center;gap:9px;margin:16px 0}.toggle input{width:20px;height:20px;accent-color:var(--green)}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}.metric{padding:10px;border:1px solid var(--line);border-radius:10px}.metric small{display:block;color:var(--muted);font-size:12px}.metric bdi{font-weight:700;font-size:17px}.table-scroll{overflow:auto;margin-top:15px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:right;white-space:nowrap}th{background:#f2f4ed;color:var(--muted);font-weight:700}td bdi{font-weight:700}.footer{margin-top:25px;padding-top:18px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
    dialog{color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:20px;padding:22px;width:min(1040px,calc(100% - 24px));max-height:85vh;overflow:auto;text-align:right;box-shadow:0 20px 80px #182e3c40}dialog::backdrop{background:#102c3980;backdrop-filter:blur(3px)}.dialog-head{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;margin-bottom:14px}.dialog-head h2{margin:0}.close{border-radius:50%;min-width:40px;min-height:40px;background:#e4ebe3;color:var(--ink);font-size:24px}.formula-intro{font-size:14px;color:var(--muted)}.formula-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.formula-card{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:17px;min-width:0}.formula-card h3{font-size:18px;text-align:center}.formula-card .formula-lines{direction:ltr;text-align:center;font-size:17px;line-height:1.8;margin-top:10px}.triangle{position:relative;width:260px;height:225px;margin:0 auto;direction:ltr;max-width:100%}.triangle svg{width:100%;height:100%;position:absolute;inset:0}.triangle-slot{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;width:82px;gap:3px;line-height:1.2}.triangle-slot.top{top:41px;left:calc(50% - 41px)}.triangle-slot.left{top:144px;left:calc(28% - 41px)}.triangle-slot.right{top:144px;left:calc(72% - 41px)}.triangle-slot strong{font-size:21px}.triangle-slot small{font-size:10px;color:var(--muted)}.triangle-slot input{width:78px;min-height:33px;border:2px solid var(--green);border-radius:7px;padding:3px 6px;direction:ltr;text-align:center;background:white;font-size:17px}.triangle-slot bdi{font-size:16px;color:var(--green);font-weight:700}.triangle-help{font-size:12px;color:var(--muted);text-align:center;margin:8px 0}.triangle-check{width:100%;margin-top:6px}.formula-context{background:#e7f0e9;border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:14px}.formula-networks{margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:14px}.formula-networks .math{font-size:17px;line-height:1.9;overflow-wrap:anywhere}.formula-networks h3{font-size:18px}.units-list{display:flex;flex-wrap:wrap;gap:15px;margin:14px 0;color:var(--muted);font-size:13px}.sheet-answer{padding:15px;background:var(--card);border:1px solid var(--line);border-radius:12px;margin-bottom:14px}.sheet-answer label{display:block;font-weight:700}.sheet-answer input{width:160px;min-height:44px;border:2px solid var(--green);border-radius:8px;padding:7px 10px;font-size:21px}.sheet-feedback{margin-bottom:13px}.calc-dialog{max-width:370px}.calc-screen{width:100%;border:1px solid #b4c9be;border-radius:11px;background:white;min-height:56px;padding:10px;font-size:23px;direction:ltr;text-align:left}.calc-result{direction:ltr;text-align:left;font-size:22px;color:var(--green);min-height:40px;overflow-wrap:anywhere;margin:8px 0}.calc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;direction:ltr}.calc-grid button{height:48px;border-radius:9px;background:var(--card);border:1px solid var(--line);font-size:21px;color:var(--ink)}.calc-grid button.operator{background:#e4eee7;color:var(--green)}.calc-grid button.equals{background:var(--green);color:white}.calc-actions{display:flex;gap:8px;margin-top:13px}.calc-actions .btn{flex:1;font-size:14px}.confirm-dialog{max-width:460px}.large-text{font-size:19px}.large-text .small,.large-text .rounding,.large-text .triangle-help{font-size:15px}
    @media(max-width:850px){.exercise-grid,.sim-layout{grid-template-columns:1fr}.hero-symbol{width:115px;height:115px;font-size:25px}.course-head{flex-direction:column}.sim-controls{display:grid;grid-template-columns:1fr auto;gap:5px 16px}.sim-controls input[type=range]{grid-column:1/-1}.sim-controls .toggle{margin:5px 0;grid-column:1}.sim-controls .btn{grid-column:2}.sim-controls .small{grid-column:1/-1}.metrics{margin-top:14px}}
    @media(max-width:570px){.diagram svg{min-width:660px}.app{padding:14px 12px 25px}.topbar{align-items:flex-start;padding-bottom:14px;flex-wrap:wrap}.top-tools{width:100%}.top-tools .btn{flex:1;font-size:14px}.brand-title{font-size:17px}.hero{padding:23px 0 18px}.hero-symbol{display:none}.hero-copy p{font-size:15px}.tabs{gap:5px}.tab{padding:11px 8px;font-size:14px;min-height:73px}.tab span{font-size:10px}.card{padding:16px}.level{font-size:14px}.given{min-width:85px;padding:7px 10px}.given bdi{font-size:17px}.answer-row{flex-wrap:wrap}.answer-row>.btn{width:100%}.answer-tools .btn{font-size:13px;flex:1;padding:9px}.formula-grid,.formula-networks{grid-template-columns:1fr}.formula-card{padding:13px}dialog{padding:16px;border-radius:16px}.sim-controls{grid-template-columns:1fr}.sim-controls .btn{grid-column:1}.metrics{grid-template-columns:1fr 1fr 1fr}.metric{padding:7px}.metric bdi{font-size:14px}.metric small{font-size:10px}h2{font-size:22px}.footer .text-btn{font-size:12px}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
  </style>
</head>
<body>
<div class="app" id="app">
  <header class="topbar">
    <div class="identity"><div class="brand-icon" aria-hidden="true">ϟ</div><div><div class="brand-title">יסודות החשמל</div><div class="eyebrow">תרגול למתחילים · DC</div></div></div>
    <div class="top-tools"><button class="btn secondary" data-open-formulas>דף נוסחאות △</button><button class="btn secondary" data-open-calculator>מחשבון</button><button class="btn secondary" id="text-size" aria-pressed="false" aria-label="הגדלת טקסט">א＋</button></div>
  </header>
  <section class="hero"><div class="hero-copy"><div class="eyebrow">לומדים להבין, ואז לחשב</div><h1>חשמל, צעד אחרי צעד.</h1><p>תרגול קצר של חוק אום, הספק ומעגלים. מתחילים במספרים שלמים ומתקדמים לעשרוניים — עם מחשבון, רמזים ודף נוסחאות בכל שלב.</p><div class="pills"><span class="pill">מקור DC בלבד</span><span class="pill">ללא חישובי שורש</span><span class="pill">5 תרגילים בכל רמה</span><span class="pill">תרגילים חדשים בכל כניסה</span></div></div><div class="hero-symbol" aria-hidden="true">U = I × R<small>להבין את הקשר בין הנתונים</small></div></section>
  <nav class="tabs" role="tablist" aria-label="תחומי התרגול">
    <button id="tab-ohm" class="tab" data-tab="ohm" role="tab" aria-controls="workspace" aria-selected="true" tabindex="0">חוק אום והספק<span>מתח · זרם · התנגדות · הספק</span></button>
    <button id="tab-series" class="tab" data-tab="series" role="tab" aria-controls="workspace" aria-selected="false" tabindex="-1">מעגל טורי<span>אותו זרם בכל הרכיבים</span></button>
    <button id="tab-parallel" class="tab" data-tab="parallel" role="tab" aria-controls="workspace" aria-selected="false" tabindex="-1">מעגל מקבילי<span>אותו מתח בכל הענפים</span></button>
  </nav>
  <main id="workspace" role="tabpanel" aria-labelledby="tab-ohm"></main>
  <footer class="footer"><div>התרגול וההתקדמות בסבב פועלים במכשיר הזה. בכניסה מחדש נוצר סבב חדש.</div><div><button class="text-btn" data-open-formulas>דף נוסחאות</button><button class="text-btn" id="new-course">תרגילים חדשים</button></div></footer>
</div>
<dialog id="formula-dialog" aria-labelledby="formula-title"><div class="dialog-head"><h2 id="formula-title">דף נוסחאות</h2><button class="close" data-close-dialog="formula-dialog" aria-label="סגירת דף הנוסחאות">×</button></div><p class="formula-intro">החלק העליון במשולש הוא מכפלת שני החלקים התחתונים. כדי למצוא חלק תחתון, מחלקים את העליון בחלק התחתון הידוע. אפשר לענות בשדה המודגש במשולש המתאים לשלב הנוכחי.</p><div id="formula-body"></div></dialog>
<dialog id="calculator-dialog" class="calc-dialog" aria-labelledby="calc-title"><div class="dialog-head"><h2 id="calc-title">מחשבון</h2><button class="close" data-close-dialog="calculator-dialog" aria-label="סגירת המחשבון">×</button></div><label class="small muted" for="calc-screen">חיבור, חיסור, כפל וחילוק</label><input id="calc-screen" class="calc-screen" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" maxlength="160" placeholder="12 ÷ 3"><div id="calc-result" class="calc-result" role="status" aria-live="polite"></div><div class="calc-grid" id="calc-grid"></div><p id="calc-error" class="feedback error" role="alert"></p><div class="calc-actions"><button class="btn" id="calc-use" disabled>העברה לתשובה</button><button class="btn secondary" id="calc-clear">ניקוי</button></div><button class="text-btn" data-open-formulas>דף נוסחאות △</button><p class="small muted" style="margin-top:12px;margin-bottom:0">המחשבון שומר על סדר פעולות חשבון. אפשר להשתמש בסוגריים. אין פונקציית שורש.</p></dialog>
<dialog id="new-course-dialog" class="confirm-dialog" aria-labelledby="new-course-title"><div class="dialog-head"><h2 id="new-course-title">להתחיל סבב חדש?</h2><button class="close" data-close-dialog="new-course-dialog" aria-label="סגירה">×</button></div><p>כל התרגילים יוחלפו, וההתקדמות בסבב הנוכחי תתחיל מחדש.</p><div class="completion-actions"><button class="btn" id="new-course-confirm">כן, תרגילים חדשים</button><button class="btn secondary" data-close-dialog="new-course-dialog">חזרה לתרגול</button></div></dialog>
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
  function ohm(rng, level, index) {
    const r = level ? integer(rng, 1 + index, 10 + index * 3) + .5
      : integer(rng, 2 + index, 8 + index * 4);
    const i = level ? pick(rng, [.2, .4, .6, .8, 1.2, 1.4, 1.6, 1.8]) : integer(rng, 1, 3 + index);
    const u = r * i, p = u * i;
    const fields = {
      I: step('I', 'הזרם במעגל', 'A', i, 'I = U ÷ R', `${fmt(u)} ÷ ${fmt(r)}`, 'כדי למצוא זרם, מחלקים את המתח בהתנגדות.', 'יחידת הזרם היא אמפר (A).'),
      U: step('U', 'מתח המקור', 'V', u, 'U = I × R', `${fmt(i)} × ${fmt(r)}`, 'כדי למצוא מתח, כופלים את הזרם בהתנגדות.', 'יחידת המתח היא וולט (V).'),
      R: step('R', 'התנגדות הנגד', 'Ω', r, 'R = U ÷ I', `${fmt(u)} ÷ ${fmt(i)}`, 'כדי למצוא התנגדות, מחלקים את המתח בזרם.', 'יחידת ההתנגדות היא אוהם (Ω).'),
      P: step('P', 'ההספק החשמלי', 'W', p, 'P = U × I', `${fmt(u)} × ${fmt(i)}`, 'הספק הוא המתח כפול הזרם.', 'יחידת ההספק היא ואט (W).'),
    };
    let givens, steps, title;
    if (index === 0) { givens = { U: u, R: r }; steps = [fields.I]; title = 'מוצאים את הזרם'; }
    if (index === 1) { givens = { I: i, R: r }; steps = [fields.U]; title = 'מוצאים את המתח'; }
    if (index === 2) { givens = { U: u, I: i }; steps = [fields.R]; title = 'מוצאים את ההתנגדות'; }
    if (index === 3) { givens = { U: u, I: i }; steps = [fields.P]; title = 'מחשבים הספק'; }
    if (index === 4) {
      givens = { U: u, P: p }; title = 'מההספק אל הזרם וההתנגדות';
      steps = [step('I', 'הזרם במעגל', 'A', i, 'I = P ÷ U', `${fmt(p)} ÷ ${fmt(u)}`,
        'מתחילים בנוסחת ההספק: כדי לבודד את הזרם, מחלקים את ההספק במתח.', 'אחרי מציאת הזרם אפשר להשתמש בחוק אום.'), fields.R];
    }
    return { kind: 'ohm', level, index, title, voltage: u, resistances: [r], lamps: [false], givens, steps };
  }
  function circuit(rng, kind, level, index) {
    let resistances, voltage;
    if (kind === 'series') {
      const count = index < 2 ? 2 : 3;
      resistances = Array.from({ length: count }, () => integer(rng, 2 + index, 7 + index * 4) + (level ? .5 : 0));
      const current = level ? pick(rng, [.2, .4, .6, .8, 1.2, 1.4, 1.6]) : integer(rng, 1, 2 + Math.floor(index / 2));
      voltage = resistances.reduce((s, r) => s + r, 0) * current;
    } else if (level === 0) {
      const r = 2 * integer(rng, 2 + index, 8 + index * 3);
      resistances = [r, r]; voltage = r * integer(rng, 1, 2 + index);
    } else if (level === 1) {
      const ratio = index < 3 ? 2 : 4;
      const base = ratio === 2 ? 1.5 * (2 * integer(rng, 0 + index, 4 + index) + 1)
        : 2.5 * (2 * integer(rng, 0, 5) + 1);
      const current = (ratio === 2 ? .4 : .8) * integer(rng, 1, 3 + index);
      resistances = [base, base * ratio]; voltage = base * current;
    } else {
      const ratios = [[1, 1, 1], [1, 1, 2], [1, 2, 2], [1, 2, 3], [1, 3, 6]][index];
      let base, current;
      if (index === 0) { base = 3.3 * integer(rng, 1, 6); current = integer(rng, 1, 3); }
      if (index === 1) { base = 2.5 * (2 * integer(rng, 0, 5) + 1); current = .4 * integer(rng, 1, 4); }
      if (index === 2) { base = integer(rng, 2, 14) + .5; current = .4 * integer(rng, 1, 4); }
      if (index === 3) { base = 5.5 * (2 * integer(rng, 0, 4) + 1); current = 1.2 * integer(rng, 1, 3); }
      if (index === 4) { base = 1.5 * (2 * integer(rng, 0, 8) + 1); current = 1.2 * integer(rng, 1, 3); }
      resistances = ratios.map(r => base * r); voltage = base * current;
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
    return { kind, level, index, title: kind === 'series' ? `מעגל טורי עם ${resistances.length} רכיבים` : `מעגל מקבילי עם ${resistances.length} ענפים`,
      voltage, resistances, lamps, givens, steps };
  }
  function course(seed, previous = []) {
    const rng = random(seed), seen = new Set(previous), result = {};
    for (const kind of kinds) {
      result[kind] = Array.from({ length: kind === 'parallel' ? 3 : 2 }, (_, level) =>
        Array.from({ length: 5 }, (_, index) => {
          let q;
          for (let attempt = 0; attempt < 400; attempt++) {
            q = kind === 'ohm' ? ohm(rng, level, index) : circuit(rng, kind, level, index);
            q.signature = JSON.stringify([kind, level, index, q.voltage, q.resistances, Object.keys(q.givens)]);
            const hasDecimal = Object.values(q.givens).some(v => Math.abs(v - Math.round(v)) > 1e-7);
            if (!seen.has(q.signature) && (level === 0 || hasDecimal)) break;
          }
          seen.add(q.signature);
          return q;
        }));
    }
    return result;
  }
  function accepted(text, value) {
    const cleaned = String(text).trim().replace(',', '.');
    if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(cleaned)) return false;
    const answer = Number(cleaned);
    return Number.isFinite(answer) && Math.abs(answer - round(value)) < 1e-7;
  }
  // Four arithmetic operations, parentheses and decimals; no code evaluation.
  function calculate(text) {
    const input = String(text).replace(/,/g, '.').replace(/×/g, '*').replace(/÷/g, '/').replace(/−/g, '-').replace(/\s/g, '');
    let cursor = 0;
    function expression() {
      let value = product();
      while (input[cursor] === '+' || input[cursor] === '-') {
        const op = input[cursor++], next = product(); value = op === '+' ? value + next : value - next;
      }
      return value;
    }
    function product() {
      let value = factor();
      while (input[cursor] === '*' || input[cursor] === '/') {
        const op = input[cursor++], next = factor();
        if (op === '/' && next === 0) throw Error('אי אפשר לחלק באפס.');
        value = op === '*' ? value * next : value / next;
      }
      return value;
    }
    function factor() {
      if (input[cursor] === '+' || input[cursor] === '-') {
        const negative = input[cursor++] === '-'; return (negative ? -1 : 1) * factor();
      }
      if (input[cursor] === '(') {
        cursor++; const value = expression();
        if (input[cursor++] !== ')') throw Error('יש לסגור את הסוגריים.');
        return value;
      }
      const match = /^(?:\d+(?:\.\d*)?|\.\d+)/.exec(input.slice(cursor));
      if (!match) throw Error('יש להזין תרגיל עם מספרים ופעולות חשבון.');
      cursor += match[0].length; return Number(match[0]);
    }
    if (input.length > 160) throw Error('התרגיל ארוך מדי.');
    const value = expression();
    if (cursor !== input.length || !Number.isFinite(value)) throw Error('יש לבדוק את התרגיל שהוקלד.');
    return value;
  }
  return { kinds, round, fmt, physics, course, accepted, calculate };
})();

function circuitSVG(q, options = {}) {
  const complete = options.complete === true;
  const voltage = options.voltage ?? q.voltage;
  const moving = complete && options.animate !== false && voltage > 0;
  const model = DC.physics(q.kind, voltage, q.resistances);
  const baseline = DC.physics(q.kind, q.voltage, q.resistances);
  const referencePower = Math.max(...baseline.powers);
  const parallel = q.kind === 'parallel';
  const count = q.resistances.length;
  const xs = parallel ? (count === 2 ? [350, 610] : [280, 475, 670])
    : count === 1 ? [450] : count === 2 ? [330, 600] : [260, 450, 640];
  const parts = [];
  const text = (x, y, value, size = 17, anchor = 'middle', color = '#203c47') =>
    `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" fill="${color}" direction="ltr">${value}</text>`;
  const wire = d => `<path d="${d}" fill="none" stroke="#687e84" stroke-width="3" stroke-linecap="round"/>`;
  const flow = (d, current) => `<path d="${d}" fill="none" stroke="#159485" stroke-width="4" stroke-dasharray="7 20" class="${moving ? 'flow' : ''}" style="${moving ? `animation-duration:${Math.max(.65, 3.2 / (1 + current * .35))}s` : 'animation:none'}" opacity="${voltage > 0 ? .9 : 0}"/>`;
  const arrow = (x, y, direction) => {
    const coordinates = direction === 'right' ? `${x - 7},${y - 5} ${x + 6},${y} ${x - 7},${y + 5}`
      : direction === 'down' ? `${x - 5},${y - 7} ${x},${y + 6} ${x + 5},${y - 7}`
      : `${x + 7},${y - 5} ${x - 6},${y} ${x + 7},${y + 5}`;
    return `<polygon points="${coordinates}" fill="#116e65"/>`;
  };
  if (parallel) {
    parts.push(wire('M85 184 L85 100 L730 100'), wire('M85 246 L85 330 L730 330'));
    xs.forEach(x => parts.push(wire(`M${x} 100 L${x} 330`)));
    if (complete) {
      xs.forEach((x, j) => parts.push(flow(`M85 184 L85 100 L${x} 100 L${x} 330 L85 330 L85 246`, model.currents[j])));
      if (voltage > 0) {
        parts.push(arrow(175, 100, 'right'), arrow(185, 330, 'left'));
        xs.forEach((x, j) => { parts.push(arrow(x, 147, 'down')); parts.push(text(x + 35, 294, `I${j + 1} = ${DC.fmt(model.currents[j])} A`, 14, 'start')); });
      }
    }
    xs.forEach(x => parts.push(`<circle cx="${x}" cy="100" r="4" fill="#687e84"/><circle cx="${x}" cy="330" r="4" fill="#687e84"/>`));
  } else {
    const path = 'M85 184 L85 100 L735 100 L735 330 L85 330 L85 246';
    parts.push(wire(path));
    if (complete) {
      parts.push(flow(path, model.total));
      if (voltage > 0) parts.push(arrow(166, 100, 'right'), arrow(735, 214, 'down'), arrow(395, 330, 'left'), text(435, 312, `I = ${DC.fmt(model.total)} A`, 16));
    }
  }
  q.resistances.forEach((r, j) => {
    const x = xs[j], y = parallel ? 215 : 100;
    const known = complete || q.kind !== 'ohm' || Object.hasOwn(q.givens, 'R');
    const resistance = known ? `${DC.fmt(r)} Ω` : '? Ω';
    if (q.lamps[j]) {
      const brightness = complete && voltage > 0 ? Math.min(1, model.powers[j] / (referencePower * 1.4)) : 0;
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="43" fill="#ffcb5c" opacity="${brightness * .32}"/>`);
      parts.push(`<circle cx="${x}" cy="${y}" r="25" fill="${brightness ? '#ffe9a2' : '#fffefa'}" stroke="#526b72" stroke-width="2.5"/>`);
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="21" fill="#ffc63d" opacity="${brightness}"/>`);
      parts.push(`<path d="M${x - 16} ${y - 16} L${x + 16} ${y + 16} M${x + 16} ${y - 16} L${x - 16} ${y + 16}" stroke="#687e84" stroke-width="2"/>`);
    } else {
      parts.push(`<rect x="${x - (parallel ? 17 : 31)}" y="${y - (parallel ? 30 : 17)}" width="${parallel ? 34 : 62}" height="${parallel ? 60 : 34}" rx="2" fill="#fffefa" stroke="#526b72" stroke-width="2.5"/>`);
    }
    if (parallel) {
      parts.push(text(x + 35, y - 10, `R${j + 1}`, 16, 'start'), text(x + 35, y + 14, resistance, 16, 'start'));
      if (complete) parts.push(text(x + 35, y + 39, `${DC.fmt(model.powers[j])} W`, 13, 'start', '#956122'));
    } else {
      parts.push(text(x, 53, `R${j + 1} = ${resistance}`, 17));
      if (complete) {
        parts.push(text(x, 152, `U${j + 1} = ${DC.fmt(model.drops[j])} V`, 14));
        parts.push(text(x, 177, `P${j + 1} = ${DC.fmt(model.powers[j])} W`, 14, 'middle', '#956122'));
      }
    }
  });
  parts.push(`<circle cx="85" cy="215" r="31" fill="#fffefa" stroke="#526b72" stroke-width="2.5"/>`);
  parts.push(text(85, 204, '+', 19), text(85, 223, 'DC', 14), text(85, 239, '−', 18));
  const knownVoltage = complete || Object.hasOwn(q.givens, 'U');
  parts.push(text(138, 222, `U = ${knownVoltage ? DC.fmt(voltage) : '?'} V`, 16, 'start'));
  const title = `${q.kind === 'parallel' ? 'מעגל מקבילי' : q.kind === 'series' ? 'מעגל טורי' : 'מעגל DC'} עם ${count} רכיבים`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 365" role="img" aria-label="${title}" dir="ltr"><title>${title}</title>${parts.join('')}</svg>`;
}

const $ = id => document.getElementById(id);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const names = { ohm: 'חוק אום והספק', series: 'מעגל טורי', parallel: 'מעגל מקבילי' };
const letters = ['א׳', 'ב׳', 'ג׳'];
const units = { U: 'V', I: 'A', R: 'Ω', P: 'W' };
const recentKey = 'dc.basics.recent.v1';
let questions, tab = 'ohm', levels = { ohm:0, series:0, parallel:0 }, positions, previous = [];
let feedback = '', feedbackType = 'success', calculatorValue = null, calculatorFresh = false;
try { const saved = JSON.parse(localStorage.getItem(recentKey)); if (Array.isArray(saved)) previous = saved.filter(s => typeof s === 'string').slice(-280); } catch {}
function newCourse() {
  const seed = window.crypto?.getRandomValues ? window.crypto.getRandomValues(new Uint32Array(1))[0] : (Date.now() ^ Math.floor(Math.random() * 4294967296));
  questions = DC.course(seed, previous);
  positions = { ohm:[0,0], series:[0,0], parallel:[0,0,0] };
  for (const kind of DC.kinds) for (const level of questions[kind]) for (const q of level) {
    q.cursor = 0; q.draft = ''; q.attempts = 0; q.help = {}; q.hint = false; q.solution = false; q.simVoltage = q.voltage; q.simAnimate = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    previous.push(q.signature);
  }
  previous = previous.slice(-280);
  try { localStorage.setItem(recentKey, JSON.stringify(previous)); } catch {}
  feedback = ''; render();
}
function currentQuestion() { return questions[tab][levels[tab]][positions[tab][levels[tab]]]; }
function completed(q) { return q.cursor === q.steps.length; }
function currentStep() { const q = currentQuestion(); return q.steps[q.cursor]; }
function bdi(value) { return `<bdi>${escapeHTML(value)}</bdi>`; }
function contextTitle(q, step) {
  if (!step) return 'המעגל הושלם';
  if (q.kind === 'ohm') return 'מעגל עם נגד יחיד';
  const match = /^[UIP](\d)$/.exec(step.key);
  return match ? `רכיב R${match[1]}${q.kind === 'parallel' ? ` בענף ${match[1]}` : ' במעגל הטורי'}` : 'המעגל כולו';
}
function render(focus = false) {
  const level = levels[tab], sequence = questions[tab][level], index = positions[tab][level], q = sequence[index], done = completed(q), step = currentStep();
  const doneCount = sequence.filter(completed).length;
  document.querySelectorAll('[data-tab]').forEach(button => { const active = button.dataset.tab === tab; button.setAttribute('aria-selected', active); button.tabIndex = active ? 0 : -1; });
  $('workspace').setAttribute('aria-labelledby', 'tab-' + tab);
  const levelButtons = questions[tab].map((list, j) => `<button class="level" data-level="${j}" aria-pressed="${j === level}">רמה ${letters[j]}<small>${j === 0 ? 'מספרים שלמים' : j === 1 ? 'מספרים עשרוניים' : 'שלושה ענפים'} · ${list.filter(completed).length}/5</small></button>`).join('');
  const given = Object.entries(q.givens).map(([key, value]) => `<div class="given"><small>${key === 'U' ? 'מתח המקור' : key === 'I' ? 'זרם נתון' : key === 'P' ? 'הספק נתון' : /^R\d/.test(key) ? `התנגדות ${key}${q.lamps[Number(key.slice(1)) - 1] ? ' · נורה' : ''}` : 'התנגדות נתונה'}</small>${bdi(`${key} = ${DC.fmt(value)} ${units[key[0]]}`)}</div>`).join('');
  const dots = sequence.map((item, j) => `<span class="question-dot ${completed(item) ? 'done' : j === index ? 'current' : ''}" aria-label="תרגיל ${j + 1}: ${completed(item) ? 'הושלם' : j === index ? 'נוכחי' : 'בהמשך'}"></span>`).join('');
  const stepPills = q.steps.map((s, j) => `<span class="step-pill ${j < q.cursor ? 'done' : j === q.cursor ? 'active' : ''}" title="${escapeHTML(s.label)}">${j < q.cursor ? '✓' : j + 1}</span>`).join('');
  const rounding = level === 0 ? 'ברמה הזאת כל התוצאות שלמות. אין צורך להקליד יחידות.' : 'יש לעגל את התשובה לשתי ספרות אחרי הנקודה לכל היותר. אפשר לכתוב נקודה או פסיק.';
  const rows = q.steps.slice(0, q.cursor).map((s, j) => `<div class="completed-row"><span>✓ ${escapeHTML(s.label)}${q.help[j] ? ' · בעזרת פתרון' : ''}</span>${bdi(`${DC.fmt(s.value)} ${s.unit}`)}</div>`).join('');
  const active = done ? `<div class="complete-badge">✓ התרגיל הושלם</div><h2>השלמתם את כל החישובים.</h2><p class="muted">${q.steps.length > 1 ? 'אפשר לעבור על התוצאות ולבדוק איך הן קשורות זו לזו.' : 'הקשר בין הנתונים ברור יותר עם כל תרגיל.'}</p>`
    : `<div class="step-list" aria-label="התקדמות שלבי הפתרון">${stepPills}</div><div class="task-kicker">צעד ${q.cursor + 1} מתוך ${q.steps.length} · ${escapeHTML(contextTitle(q, step))}</div><h2 id="answer-title">${escapeHTML(step.label)}</h2><form id="answer-form" novalidate><label class="small muted" for="answer">מה התוצאה, ביחידות ${bdi(step.unit)}?</label><div class="answer-row"><div class="answer-wrap"><input class="numeric" id="answer" data-answer type="text" inputmode="decimal" autocomplete="off" maxlength="24" value="${escapeHTML(q.draft)}" aria-describedby="rounding-text form-feedback"><span class="unit" aria-hidden="true">${bdi(step.unit)}</span></div><button class="btn" type="submit">בדיקת תשובה</button></div></form>`;
  const explain = !done && q.solution ? `<div class="solution"><strong>כך פותרים</strong><div class="math">${escapeHTML(step.formula)}</div><div class="math">${escapeHTML(step.substitution)} = ${DC.fmt(step.value)} ${step.unit}</div><p>${escapeHTML(step.explanation)} הקלידו את התוצאה כדי להמשיך לצעד הבא.</p></div>` : '';
  const hints = !done && q.hint ? `<div class="hint"><strong>כיוון לפתרון</strong>${escapeHTML(step.hint)}<div class="math" style="margin-top:8px">${escapeHTML(step.formula)}</div></div>` : '';
  const tools = `<div class="answer-tools"><button class="btn secondary tiny" data-open-formulas>דף נוסחאות △</button><button class="btn secondary tiny" data-open-calculator>מחשבון</button>${!done ? '<button class="btn soft tiny" data-hint>רמז</button><button class="text-btn small" data-solution>פתרון מוסבר</button>' : ''}</div>`;
  const next = done ? `<div class="completion-actions">${index < 4 ? '<button class="btn" data-next-question>לתרגיל הבא ←</button>' : level < questions[tab].length - 1 ? '<button class="btn" data-next-level>לרמה הבאה ←</button>' : '<button class="btn" data-new-course>סבב חדש</button>'}</div>${doneCount === 5 ? `<div class="level-note">השלמתם את חמשת התרגילים ברמה ${letters[level]}. ${level < questions[tab].length - 1 ? 'אפשר להתקדם לרמה הבאה.' : 'אפשר לעבור ללשונית אחרת או להתחיל סבב חדש.'}</div>` : ''}` : '';
  const descriptions = { ohm:'מתחילים בנתונים ידועים ומוצאים את הערך החסר.', series:'בטור הזרם זהה בכל הרכיבים. המתח מתחלק ביניהם.', parallel:level === 0 ? 'שני נגדים זהים במקביל. בכל ענף אותו מתח.' : level === 1 ? 'שני נגדים שונים במקביל. הזרמים תלויים בהתנגדויות.' : 'שלושה ענפים במקביל: נגדים זהים ושונים.' };
  $('workspace').innerHTML = `<div class="course-head"><div><h2>${names[tab]}</h2><p class="muted small" style="margin:0">${descriptions[tab]}</p></div><div class="levels" aria-label="רמות תרגול">${levelButtons}</div></div><div class="progress-row"><span>תרגיל ${index + 1} מתוך 5 · רמה ${letters[level]}</span><div class="question-dots">${dots}</div></div><div class="progress-track" role="progressbar" aria-label="תרגילים שהושלמו ברמה" aria-valuemin="0" aria-valuemax="5" aria-valuenow="${doneCount}"><div style="width:${doneCount * 20}%"></div></div><div class="exercise-grid"><section class="card"><div class="exercise-title"><div class="eyebrow">הנתונים שלכם</div><h3 style="margin-top:6px">${q.title}</h3><p class="muted small" style="margin:0">${tab === 'ohm' ? 'המקור הוא מקור מתח ישר (DC). מצאו את הנעלם המבוקש.' : 'כל ההתנגדויות ומתח המקור נתונים. פתרו לפי הסדר.'}</p></div><div class="givens">${given}</div><figure class="diagram">${circuitSVG(q)}<figcaption>${q.lamps.some(Boolean) ? 'סימון עיגול עם X הוא נורה. בתרגול הנורה היא רכיב בעל התנגדות קבועה.' : 'מלבן הוא נגד. המקור הוא DC; U מציין מתח ו־I מציין זרם.'}${tab !== 'ohm' ? ' לאחר השלמת המעגל ייפתח הסימולטור. אפשר לגלול תרשים רחב לצדדים בטלפון.' : ''}</figcaption></figure></section><section class="card ${done ? 'success-summary' : ''}">${active}<p id="rounding-text" class="rounding">${rounding}</p>${tools}<div class="feedback ${feedbackType}" id="form-feedback" role="status" aria-live="polite">${escapeHTML(feedback)}</div>${hints}${explain}${q.cursor ? `<div class="completed-steps"><strong class="small">החישובים שהשלמתם</strong>${rows}</div>` : ''}${next}</section></div>${done && tab !== 'ohm' ? simulatorHTML(q) : ''}`;
  if ($('formula-dialog').open) renderFormulas();
  if (focus && !done) requestAnimationFrame(() => ($('formula-dialog').open ? $('formula-body').querySelector('[data-answer]') : $('answer'))?.focus());
  fitDialogs(); resizeFrame();
}
function checkAnswer(value) {
  const q = currentQuestion(), step = currentStep();
  if (!step) return;
  q.draft = value;
  if (!DC.accepted(value, step.value)) {
    q.attempts++; feedbackType = 'error';
    feedback = value.trim() ? 'התשובה עדיין לא מדויקת. בדקו את הנוסחה ואת סדר פעולות החשבון. אפשר להיעזר ברמז ובמחשבון.' : 'יש להקליד תשובה מספרית. אפשר להתחיל ברמז או בדף הנוסחאות.';
    q.hint = true;
    if (q.attempts >= 3) { q.solution = true; q.help[q.cursor] = true; }
    render(true);
    document.querySelectorAll('[data-answer]').forEach(field => field.setAttribute('aria-invalid', 'true'));
    return;
  }
  q.cursor++; q.draft = ''; q.attempts = 0; q.hint = false; q.solution = false;
  feedbackType = 'success'; feedback = completed(q) ? 'נכון. כל החישובים בתרגיל הושלמו.' : 'נכון. ממשיכים לצעד הבא.';
  render(true);
}
function syncDraft(value, source) {
  currentQuestion().draft = value;
  document.querySelectorAll('[data-answer]').forEach(field => { if (field !== source) field.value = value; field.removeAttribute('aria-invalid'); });
}
function simulatorHTML(q) {
  return `<section class="card simulator" aria-labelledby="sim-title"><div class="sim-head"><div><div class="eyebrow">אחרי החישוב — רואים את המעגל</div><h2 id="sim-title" style="margin:5px 0">סימולטור DC</h2></div><button class="btn secondary tiny" data-open-formulas>דף נוסחאות △</button></div><div class="sim-layout"><div><figure class="diagram" id="sim-diagram">${circuitSVG(q, { complete:true, voltage:q.simVoltage, animate:q.simAnimate })}</figure><div id="sim-metrics">${simMetrics(q)}</div></div><div class="sim-controls"><label for="sim-voltage">שינוי מתח המקור</label><div class="sim-value" id="sim-voltage-label">${bdi(`${DC.fmt(q.simVoltage)} V`)}</div><input id="sim-voltage" type="range" min="0" max="${DC.fmt(q.voltage * 2)}" step="0.1" value="${q.simVoltage}" aria-describedby="sim-note"><label class="toggle"><input id="sim-animation" type="checkbox" ${q.simAnimate ? 'checked' : ''}>הנפשת מסלול הזרם</label><button class="btn secondary tiny" data-reset-simulator>חזרה למתח התרגיל</button><p class="small muted" id="sim-note" style="margin:6px 0 0">החצים מציגים זרם מוסכם: מהפלוס אל המינוס דרך המעגל החיצוני. הבהירות ממחישה את ההספק בנורה בעלת התנגדות קבועה. שינוי המתח כאן אינו משנה את תשובות התרגיל.</p></div></div></section>`;
}
function simMetrics(q) {
  const m = DC.physics(q.kind, q.simVoltage, q.resistances);
  return `<div class="metrics"><div class="metric"><small>נגד שקול</small>${bdi(`${DC.fmt(m.req)} Ω`)}</div><div class="metric"><small>זרם כולל</small>${bdi(`${DC.fmt(m.total)} A`)}</div><div class="metric"><small>הספק כולל</small>${bdi(`${DC.fmt(m.power)} W`)}</div></div><div class="table-scroll"><table><caption class="small muted" style="text-align:right;margin-bottom:5px">נתוני המעגל במתח שנבחר בסימולטור</caption><thead><tr><th>רכיב</th><th>התנגדות</th><th>מתח</th><th>זרם</th><th>הספק</th></tr></thead><tbody>${q.resistances.map((r,j) => `<tr><td>${bdi('R' + (j+1))}${q.lamps[j] ? ' · נורה' : ''}</td><td>${bdi(`${DC.fmt(r)} Ω`)}</td><td>${bdi(`${DC.fmt(m.drops[j])} V`)}</td><td>${bdi(`${DC.fmt(m.currents[j])} A`)}</td><td>${bdi(`${DC.fmt(m.powers[j])} W`)}</td></tr>`).join('')}</tbody></table></div>`;
}
function updateSimulator() {
  const q = currentQuestion();
  if (!$('sim-diagram')) return;
  $('sim-diagram').innerHTML = circuitSVG(q, { complete:true, voltage:q.simVoltage, animate:q.simAnimate });
  $('sim-metrics').innerHTML = simMetrics(q);
  $('sim-voltage-label').innerHTML = bdi(`${DC.fmt(q.simVoltage)} V`);
  $('sim-voltage').value = q.simVoltage; $('sim-animation').checked = q.simAnimate;
}

function triangleContext() {
  const q = currentQuestion(), task = currentStep(), model = DC.physics(q.kind, q.voltage, q.resistances);
  const finished = new Set(q.steps.slice(0, q.cursor).map(step => step.key));
  let values = {}, target = task?.key, label;
  if (q.kind === 'ohm') {
    values = { ...q.givens };
    q.steps.slice(0, q.cursor).forEach(step => { values[step.key] = step.value; });
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
  if (values.I !== undefined) values.I2 = values.I * values.I;
  if (values.U !== undefined) values.U2 = values.U * values.U;
  return { values, target, label, task, q };
}
function triangleCard(definition, context) {
  const slots = definition.slots;
  const enabled = !!context.task && slots.some(slot => slot.key === context.target)
    && slots.filter(slot => slot.key !== context.target).every(slot => context.values[slot.key] !== undefined);
  const locations = ['top', 'left', 'right'];
  const geometry = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" aria-hidden="true"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#78958a" stroke-width="2.5"/><path d="M65 125 L195 125 M130 125 L130 218" stroke="#78958a" stroke-width="2"/></svg>';
  const inputs = slots.map((slot, j) => `<div class="triangle-slot ${locations[j]}"><strong>${slot.symbol}</strong><small>${slot.unit}</small>${enabled && slot.key === context.target
    ? `<input class="numeric" data-answer type="text" inputmode="decimal" maxlength="24" autocomplete="off" value="${escapeHTML(context.q.draft)}" aria-label="${escapeHTML(context.task.label)} במשולש ${definition.title}">`
    : `<bdi>${context.values[slot.key] !== undefined ? DC.fmt(context.values[slot.key]) : '—'}</bdi>`}</div>`).join('');
  return `<section class="formula-card"><h3>${definition.title}</h3><form data-triangle-form novalidate><div class="triangle">${geometry}${inputs}</div>${enabled ? `<button class="btn triangle-check tiny" type="submit">בדיקת ${escapeHTML(context.task.label)}</button>` : '<p class="triangle-help">המשולש זמין למענה כשהנעלם ושני הנתונים מתאימים לשלב הנוכחי.</p>'}</form><div class="formula-lines">${definition.formulas.map(bdi).join('<br>')}</div>${definition.note ? `<p class="triangle-help">${definition.note}</p>` : ''}</section>`;
}
function renderFormulas() {
  const context = triangleContext();
  const sheetHelp = context.task && (context.q.hint || context.q.solution) ? `<div class="${context.q.solution ? 'solution' : 'hint'}"><strong>${context.q.solution ? 'כך פותרים' : 'כיוון לפתרון'}</strong><p>${escapeHTML(context.task.hint)}</p><div class="math">${escapeHTML(context.task.formula)}</div>${context.q.solution ? `<div class="math">${escapeHTML(context.task.substitution)} = ${DC.fmt(context.task.value)} ${context.task.unit}</div><p>הקלידו את התוצאה בשדה המענה המודגש כדי להמשיך.</p>` : ''}</div>` : '';
  const definitions = [
    { title:'חוק אום', slots:[{key:'U',symbol:'U',unit:'V'},{key:'I',symbol:'I',unit:'A'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['U = I × R','I = U ÷ R','R = U ÷ I'] },
    { title:'הספק לפי מתח וזרם', slots:[{key:'P',symbol:'P',unit:'W'},{key:'U',symbol:'U',unit:'V'},{key:'I',symbol:'I',unit:'A'}], formulas:['P = U × I','U = P ÷ I','I = P ÷ U'] },
    { title:'הספק לפי זרם והתנגדות', slots:[{key:'P',symbol:'P',unit:'W'},{key:'I2',symbol:'I²',unit:'I × I'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['P = I² × R','R = P ÷ I²'], note:'I² פירושו I כפול I. בתרגול משתמשים כאן בזרם ידוע; לא מוציאים שורש.' },
    { title:'הספק לפי מתח והתנגדות', slots:[{key:'U2',symbol:'U²',unit:'U × U'},{key:'P',symbol:'P',unit:'W'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['U² = P × R','P = U² ÷ R','R = U² ÷ P'], note:'U² פירושו U כפול U. בתרגול משתמשים כאן במתח ידוע; לא מוציאים שורש.' },
  ];
  const alternative = context.task && context.target === 'Req' ? `<form class="sheet-answer" data-triangle-form novalidate><label for="sheet-answer">${escapeHTML(context.task.label)} — השתמשו בנוסחת טור או מקביל שמופיעה בהמשך</label><div class="answer-row"><input id="sheet-answer" class="numeric" data-answer inputmode="decimal" type="text" maxlength="24" value="${escapeHTML(context.q.draft)}" autocomplete="off" aria-label="התנגדות שקולה"><span>${bdi('Ω')}</span><button class="btn tiny" type="submit">בדיקת תשובה</button></div></form>` : '';
  $('formula-body').innerHTML = `<div class="formula-context"><strong>${escapeHTML(context.label)}</strong><div>${context.task ? `כעת מחשבים: ${escapeHTML(context.task.label)}. הנתונים במשולשים כוללים רק נתוני השאלה וצעדים שכבר השלמתם.` : 'אפשר לעבור על הנוסחאות ולהמשיך לתרגיל הבא.'}</div><div class="answer-tools" style="margin:8px 0 0"><button class="btn secondary tiny" data-open-calculator>פתיחת המחשבון</button><button class="btn soft tiny" data-close-dialog="formula-dialog">חזרה לתרגול</button></div></div>${feedback ? `<div class="feedback sheet-feedback ${feedbackType}" role="status" aria-live="polite">${escapeHTML(feedback)}</div>` : ''}${sheetHelp}${alternative}<div class="formula-grid">${definitions.map(def => triangleCard(def, context)).join('')}</div><div class="units-list"><span>${bdi('U')} — מתח, וולט ${bdi('V')}</span><span>${bdi('I')} — זרם, אמפר ${bdi('A')}</span><span>${bdi('R')} — התנגדות, אוהם ${bdi('Ω')}</span><span>${bdi('P')} — הספק, ואט ${bdi('W')}</span></div><div class="formula-networks"><section class="formula-card"><h3>מעגל טורי</h3><div class="math">${bdi('R_eq = R1 + R2 + R3')}<br>${bdi('I = U ÷ R_eq')}<br>${bdi('U1 = I × R1')}<br>${bdi('U = U1 + U2 + U3')}<br>${bdi('P1 = I² × R1')}</div><p class="small muted" style="margin-top:10px">R_eq מציין התנגדות שקולה. בשני רכיבים מחברים רק את R1 ואת R2. אותו זרם עובר בכל הרכיבים.</p></section><section class="formula-card"><h3>מעגל מקבילי</h3><div class="math">${bdi('R_eq = (R1 × R2) ÷ (R1 + R2)')}<br>${bdi('R_eq = 1 ÷ (1/R1 + 1/R2 + 1/R3)')}<br>${bdi('R_eq = R ÷ n')}<br>${bdi('I1 = U ÷ R1')}<br>${bdi('I_total = I1 + I2 + I3')}<br>${bdi('P1 = U × I1')}</div><p class="small muted" style="margin-top:10px">R_eq מציין התנגדות שקולה. הנוסחה R/n מתאימה רק לנגדים זהים. n הוא מספר הענפים. בכל הענפים אותו מתח.</p></section></div>`;
  fitDialogs(); resizeFrame();
}

function openDialog(id) {
  document.querySelectorAll('dialog[open]').forEach(dialog => { if (dialog.id !== id) dialog.close(); });
  if (id === 'formula-dialog') renderFormulas();
  if (!$(id).open) $(id).showModal();
  fitDialogs(); resizeFrame();
}
function postMessage(type, data) { window.parent.postMessage({ isStreamlitMessage:true, type, ...data }, '*'); }
function resizeFrame() {
  requestAnimationFrame(() => postMessage('streamlit:setFrameHeight', { height:Math.ceil($('app').getBoundingClientRect().height + 10) }));
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
  document.querySelectorAll('dialog[open]').forEach(dialog => {
    dialog.style.position = 'fixed'; dialog.style.margin = '0 auto'; dialog.style.bottom = 'auto';
    dialog.style.maxHeight = Math.max(100, height - 24) + 'px';
    dialog.style.top = top + Math.max(12, (height - dialog.getBoundingClientRect().height) / 2) + 'px';
  });
}
function calculateScreen() {
  try {
    calculatorValue = DC.calculate($('calc-screen').value);
    $('calc-result').textContent = String(Math.round(calculatorValue * 1e10) / 1e10);
    $('calc-error').textContent = ''; $('calc-use').disabled = !currentStep(); calculatorFresh = true;
  } catch (error) {
    calculatorValue = null; $('calc-result').textContent = ''; $('calc-error').textContent = error.message;
    $('calc-use').disabled = true;
  }
  fitDialogs();
}
function clearCalculator() {
  $('calc-screen').value = ''; $('calc-result').textContent = ''; $('calc-error').textContent = '';
  calculatorValue = null; calculatorFresh = false; $('calc-use').disabled = true;
}
const keypad = ['C','←','(',')','7','8','9','÷','4','5','6','×','1','2','3','−','0','.','=','+'];
$('calc-grid').innerHTML = keypad.map(key => `<button type="button" data-calc="${key}" class="${['÷','×','−','+'].includes(key) ? 'operator' : key === '=' ? 'equals' : ''}" aria-label="${key === '←' ? 'מחיקת תו' : key === 'C' ? 'ניקוי' : key === '=' ? 'חישוב' : key}">${key}</button>`).join('');
document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if (button.hasAttribute('data-open-formulas')) return openDialog('formula-dialog');
  if (button.hasAttribute('data-open-calculator')) {
    $('calc-use').disabled = calculatorValue === null || !currentStep();
    openDialog('calculator-dialog'); return;
  }
  if (button.dataset.closeDialog) return $(button.dataset.closeDialog).close();
  if (button.dataset.tab) { tab = button.dataset.tab; feedback = ''; render(); return; }
  if (button.dataset.level !== undefined) { levels[tab] = Number(button.dataset.level); feedback = ''; render(); return; }
  const q = currentQuestion();
  if (button.hasAttribute('data-hint')) { q.hint = true; render(); return; }
  if (button.hasAttribute('data-solution')) { q.solution = true; q.help[q.cursor] = true; render(); return; }
  if (button.hasAttribute('data-next-question')) { positions[tab][levels[tab]]++; feedback = ''; render(); return; }
  if (button.hasAttribute('data-next-level')) { levels[tab]++; feedback = ''; render(); return; }
  if (button.id === 'new-course' || button.hasAttribute('data-new-course')) return openDialog('new-course-dialog');
  if (button.id === 'new-course-confirm') { $('new-course-dialog').close(); newCourse(); return; }
  if (button.id === 'text-size') {
    const large = document.body.classList.toggle('large-text'); button.setAttribute('aria-pressed', large); resizeFrame(); return;
  }
  if (button.hasAttribute('data-reset-simulator')) { q.simVoltage = q.voltage; updateSimulator(); return; }
  if (button.id === 'calc-clear') { clearCalculator(); return; }
  if (button.id === 'calc-use' && calculatorValue !== null) {
    syncDraft(DC.fmt(calculatorValue)); $('calculator-dialog').close();
    if ($('formula-dialog').open) $('formula-body').querySelector('[data-answer]')?.focus();
    else $('answer')?.focus();
    return;
  }
  if (button.dataset.calc !== undefined) {
    const key = button.dataset.calc, screen = $('calc-screen');
    if (key === '=') return calculateScreen();
    if (key === 'C') return clearCalculator();
    if (key === '←') screen.value = screen.value.slice(0, -1);
    else {
      if (calculatorFresh) screen.value = ['+','−','×','÷'].includes(key) ? String(calculatorValue ?? '') : '';
      if (screen.value.length < 160) screen.value += key;
    }
    calculatorFresh = false; calculatorValue = null; $('calc-result').textContent = ''; $('calc-error').textContent = ''; $('calc-use').disabled = true;
  }
});
document.addEventListener('submit', event => {
  if (event.target.id !== 'answer-form' && !event.target.hasAttribute('data-triangle-form')) return;
  event.preventDefault();
  checkAnswer(event.target.querySelector('[data-answer]')?.value ?? currentQuestion().draft);
});
document.addEventListener('input', event => {
  if (event.target.hasAttribute('data-answer')) syncDraft(event.target.value, event.target);
  if (event.target.id === 'sim-voltage') { currentQuestion().simVoltage = Number(event.target.value); updateSimulator(); }
  if (event.target.id === 'calc-screen') { calculatorValue = null; calculatorFresh = false; $('calc-use').disabled = true; $('calc-result').textContent = ''; }
});
document.addEventListener('change', event => {
  if (event.target.id === 'sim-animation') { currentQuestion().simAnimate = event.target.checked; updateSimulator(); }
});
document.addEventListener('keydown', event => {
  if (event.target.id === 'calc-screen' && event.key === 'Enter') { event.preventDefault(); calculateScreen(); return; }
  const button = event.target.closest('[data-tab]');
  if (!button || !['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
  event.preventDefault();
  const index = DC.kinds.indexOf(button.dataset.tab);
  tab = DC.kinds[event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (index + (event.key === 'ArrowLeft' ? 1 : 2)) % 3];
  feedback = ''; render(); $('tab-' + tab).focus();
});
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
});
window.addEventListener('resize', () => { fitDialogs(); resizeFrame(); });
window.visualViewport?.addEventListener('resize', fitDialogs);
try { if (window.parent !== window) { window.parent.addEventListener('scroll', fitDialogs, true); window.parent.addEventListener('resize', fitDialogs); } } catch {}
postMessage('streamlit:componentReady', { apiVersion:1 });
newCourse();
if ('ResizeObserver' in window) new ResizeObserver(resizeFrame).observe($('app'));

</script>
</body>
</html>
'''

st.set_page_config(page_title="יסודות החשמל | תרגול DC", page_icon="⚡", layout="wide")
st.markdown("""<style>
.stApp,[data-testid="stAppViewContainer"]{background:#f4f5f1}
[data-testid="stMainBlockContainer"],.block-container{max-width:1220px;padding:.5rem .25rem 1rem}
[data-testid="stHeader"]{display:none}
@media(max-width:600px){[data-testid="stMainBlockContainer"],.block-container{padding:.25rem 0 .5rem}}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def frontend_directory(html):
    directory = Path(tempfile.mkdtemp(prefix="dc_basics_"))
    (directory / "index.html").write_text(html, encoding="utf-8")
    return str(directory)

practice = components.declare_component("dc_electricity_basics", path=frontend_directory(APP_HTML))
practice(key="dc_electricity_basics_v1", default=None)


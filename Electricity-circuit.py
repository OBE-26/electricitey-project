"""יסודות החשמל — תרגול DC למבוגרים המתחילים ללמוד חשמל.

Single-file Streamlit app. All browser assets are embedded; no database is needed.
Local browser profiles and learning statistics persist between exercise rounds.
Review the draft terms/privacy wording and accessibility statement before publication.
Install: python -m pip install streamlit
Run:     streamlit run Electricity-circuit.py

Includes Ohm/power, series and parallel practice, interactive formula triangles,
four-operation calculator and a DC circuit simulator with resistive lamp models.
Practice resumes at the saved exercise; reset creates 35 fresh exercises. Recent question signatures are
kept in browser storage to avoid immediate repeats; profile details and progress remain in local browser storage and are not sent by this app to the server.
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
  <script>
    try {
      const scale = JSON.parse(localStorage.getItem('dc.basics.personal.v1') || 'null')?.preferences?.textScale;
      document.documentElement.style.setProperty('--text-scale', String([100,125,150].includes(scale) ? scale / 100 : 1));
    } catch { document.documentElement.style.setProperty('--text-scale', '1'); }
  </script>
  <style>
    :root{--text-scale:1;color-scheme:light;--paper:#f4f5f1;--card:#fffefa;--ink:#182e3c;--muted:#5b6f78;--line:#dce3df;--green:#116e65;--soft:#e7f1ed;--amber:#a65b20;--shadow:0 8px 28px #182e3c08}
    html:not(.ui-ready) body{visibility:hidden}
    .top-tools .btn{align-self:start}
    html{font-size:16px;-webkit-text-size-adjust:100%;text-size-adjust:100%}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,"Noto Sans Hebrew",sans-serif;line-height:1.65;text-align:right}button,input,select{font:inherit}button{cursor:pointer;touch-action:manipulation}button:disabled{opacity:.48;cursor:default}button,input{font-size:calc(16px * var(--text-scale,1))}input[aria-invalid=true]{border-color:#b05242!important}button{border:0}button:focus-visible,input:focus-visible,summary:focus-visible,a:focus-visible{outline:3px solid #c38330;outline-offset:3px}[hidden]{display:none!important}h1,h2,h3,p{margin-top:0}h1,h2,h3{line-height:1.35}h1{font-size:clamp(calc(30px * var(--text-scale,1)),calc(5vw * var(--text-scale,1)),calc(46px * var(--text-scale,1)));letter-spacing:-.04em;margin-bottom:12px}h2{font-size:calc(25px * var(--text-scale,1));margin-bottom:8px}h3{font-size:calc(20px * var(--text-scale,1));margin-bottom:12px}p{margin-bottom:12px}bdi,.math{direction:ltr;unicode-bidi:isolate;font-variant-numeric:tabular-nums}bdi{display:inline-block}.math{display:block;text-align:left}input.numeric{direction:ltr;text-align:left;font-variant-numeric:tabular-nums}
    .app{max-width:1160px;margin:auto;padding:22px 24px 40px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:22px;border-bottom:1px solid var(--line)}.identity{display:flex;align-items:center;gap:12px}.brand-icon{background:var(--ink);color:white;border-radius:14px;width:46px;height:46px;display:grid;place-items:center;font-size:calc(27px * var(--text-scale,1))}.brand-title{font-weight:700;font-size:calc(18px * var(--text-scale,1))}.eyebrow{color:var(--green);font-weight:700;font-size:calc(12px * var(--text-scale,1));letter-spacing:.06em}.muted{color:var(--muted)}.small{font-size:calc(13px * var(--text-scale,1))}.top-tools{display:flex;gap:8px;flex-wrap:wrap}
    .btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:46px;padding:10px 17px;border-radius:11px;color:white;background:var(--green);font-weight:700;border:1px solid transparent;line-height:1.45}.btn.secondary{background:var(--card);color:var(--ink);border-color:var(--line)}.btn.soft{background:var(--soft);color:var(--green)}.btn.tiny{font-size:calc(14px * var(--text-scale,1));min-height:40px;padding:8px 11px}.btn:hover:enabled{filter:brightness(.97)}.text-btn{background:none;color:var(--green);text-decoration:underline;padding:8px;min-height:40px}.hero{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:32px 0 24px}.hero-copy{max-width:710px}.hero-copy p{color:var(--muted);font-size:calc(17px * var(--text-scale,1))}.hero-symbol{width:150px;height:150px;border-radius:28px;border:1px solid #cdded7;background:linear-gradient(140deg,#e9f0e8,#f9f5e8);display:grid;place-content:center;direction:ltr;text-align:center;color:var(--green);font-size:calc(31px * var(--text-scale,1));font-weight:700;flex-shrink:0;transform:rotate(-3deg)}.hero-symbol small{font-size:calc(13px * var(--text-scale,1));color:var(--muted);font-weight:400;margin-top:8px}.pills{display:flex;flex-wrap:wrap;gap:7px}.pill{border:1px solid var(--line);background:var(--card);padding:4px 10px;border-radius:20px;font-size:calc(12px * var(--text-scale,1));color:var(--muted)}
    .tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:8px 0 22px}.tab{min-height:64px;padding:12px 16px;background:#e8ede7;border-radius:13px;color:var(--muted);font-weight:700;text-align:right}.tab span{font-size:calc(12px * var(--text-scale,1));font-weight:400;display:block;margin-top:2px}.tab[aria-selected=true]{background:var(--ink);color:white}.course-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:16px}.levels{display:flex;gap:7px;flex-wrap:wrap}.level{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 13px;min-height:46px;color:var(--muted);font-weight:700}.level[aria-pressed=true]{color:var(--green);border-color:var(--green);box-shadow:inset 0 0 0 1px var(--green)}.level small{display:block;font-weight:400;font-size:calc(12px * var(--text-scale,1))}.card{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:var(--shadow)}.progress-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;font-size:calc(14px * var(--text-scale,1))}.question-dots{display:flex;gap:6px;direction:ltr}.question-dot{height:9px;width:23px;border-radius:5px;background:var(--line)}.question-dot.current{background:#80b5a6}.question-dot.done{background:var(--green)}.progress-track{height:5px;background:var(--line);border-radius:5px;overflow:hidden;margin-bottom:22px}.progress-track>div{height:100%;background:var(--green);transition:width .25s;}
    .exercise-grid{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(320px,.9fr);gap:18px;align-items:start}.exercise-title{margin-bottom:16px}.givens{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}.given{background:#f1f4ed;border:1px solid #e0e7dc;border-radius:10px;padding:8px 12px;min-width:92px}.given small{display:block;color:var(--muted);font-size:calc(12px * var(--text-scale,1))}.given bdi{font-weight:700;font-size:calc(19px * var(--text-scale,1))}.diagram{margin:8px 0 0;overflow-x:auto;max-width:100%}.diagram svg{display:block;width:100%;height:auto;min-width:0}.diagram figcaption{color:var(--muted);font-size:calc(12px * var(--text-scale,1));margin-top:5px}.flow{stroke-dasharray:7 20;animation:currentFlow 2.4s linear infinite}@keyframes currentFlow{to{stroke-dashoffset:-216}}
    .step-list{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}.step-pill{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;border-radius:50%;font-size:calc(12px * var(--text-scale,1));border:1px solid var(--line);color:var(--muted)}.step-pill.done{background:var(--soft);color:var(--green);border-color:#b4d2c7}.step-pill.active{background:var(--ink);color:white;border-color:var(--ink)}.task-kicker{color:var(--green);font-weight:700;font-size:calc(13px * var(--text-scale,1));margin-bottom:5px}.answer-row{display:flex;gap:9px;margin:14px 0 6px;align-items:center}.answer-wrap{display:flex;align-items:center;gap:10px;flex:1;min-width:0}.answer-wrap input{min-width:0;width:100%;min-height:52px;border:2px solid #b9cec3;border-radius:11px;padding:10px 12px;background:white;font-size:calc(23px * var(--text-scale,1));color:var(--ink)}.unit{font-size:calc(19px * var(--text-scale,1));color:var(--muted)}.answer-tools{display:flex;flex-wrap:wrap;gap:7px;margin:16px 0}.rounding{font-size:calc(13px * var(--text-scale,1));color:var(--muted)}.feedback{border-radius:10px;padding:11px 13px;margin-top:12px;line-height:1.7}.feedback:empty{display:none}.feedback.error{background:#fff0ed;color:#933b32}.feedback.success{background:#e2f1e9;color:#126044}.hint{background:#f7f1df;border:1px solid #eadcbc;border-radius:12px;padding:14px;margin:12px 0;font-size:calc(14px * var(--text-scale,1))}.hint strong{display:block;margin-bottom:5px}.solution{border-inline-start:3px solid var(--green);padding:11px 15px;background:#f1f6ef;border-radius:8px;margin:12px 0}.solution .math{font-size:calc(21px * var(--text-scale,1));font-weight:700;overflow-wrap:anywhere;margin:6px 0}.solution p{font-size:calc(14px * var(--text-scale,1));color:var(--muted);margin-bottom:0}.completed-steps{margin-top:18px;border-top:1px solid var(--line);padding-top:12px}.completed-row{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:7px 0;font-size:calc(14px * var(--text-scale,1))}.completed-row bdi{font-weight:700}.complete-badge{color:var(--green);background:var(--soft);font-size:calc(13px * var(--text-scale,1));border-radius:20px;padding:6px 12px;display:inline-block;margin-bottom:14px}.completion-actions{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0 0}.success-summary{border-color:#b9d9c9}.level-note{border:1px dashed #b9cfc2;border-radius:12px;padding:12px;margin-top:14px;font-size:calc(14px * var(--text-scale,1));color:var(--muted)}
    .simulator{margin-top:20px}.sim-head{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}.sim-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(240px,.55fr);gap:20px;align-items:start}.sim-controls{padding:18px;background:#f1f4ed;border-radius:13px}.sim-controls label{display:block;font-weight:700;font-size:calc(14px * var(--text-scale,1))}.sim-controls input[type=range]{width:100%;accent-color:var(--green);margin:12px 0;min-height:36px}.sim-value{font-size:calc(24px * var(--text-scale,1));color:var(--green);font-weight:700}.toggle{display:flex!important;align-items:center;gap:9px;margin:16px 0}.toggle input{width:20px;height:20px;accent-color:var(--green)}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}.metric{padding:10px;border:1px solid var(--line);border-radius:10px}.metric small{display:block;color:var(--muted);font-size:calc(12px * var(--text-scale,1))}.metric bdi{font-weight:700;font-size:calc(17px * var(--text-scale,1))}.table-scroll{overflow:auto;margin-top:15px}table{border-collapse:collapse;width:100%;font-size:calc(14px * var(--text-scale,1))}th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:right;white-space:nowrap}th{background:#f2f4ed;color:var(--muted);font-weight:700}td bdi{font-weight:700}.footer{margin-top:25px;padding-top:18px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:calc(12px * var(--text-scale,1));color:var(--muted)}
    dialog{color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:20px;padding:22px;width:min(1040px,calc(100% - 24px));max-height:85vh;overflow:auto;text-align:right;box-shadow:0 20px 80px #182e3c40}dialog::backdrop{background:#102c3980;backdrop-filter:blur(3px)}.dialog-head{display:flex;justify-content:space-between;align-items:flex-start;gap:15px;margin-bottom:14px}.dialog-head h2{margin:0}.close{border-radius:50%;min-width:40px;min-height:40px;background:#e4ebe3;color:var(--ink);font-size:calc(24px * var(--text-scale,1))}.formula-intro{font-size:calc(14px * var(--text-scale,1));color:var(--muted)}.formula-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.formula-card{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:17px;min-width:0}.formula-card h3{font-size:calc(18px * var(--text-scale,1));text-align:center}.formula-card .formula-lines{direction:ltr;text-align:center;font-size:calc(17px * var(--text-scale,1));line-height:1.8;margin-top:10px}.triangle{position:relative;width:260px;height:225px;margin:0 auto;direction:ltr;max-width:100%}.triangle svg{width:100%;height:100%;position:absolute;inset:0}.triangle-slot{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;width:82px;gap:3px;line-height:1.2}.triangle-slot.top{top:41px;left:calc(50% - 41px)}.triangle-slot.left{top:144px;left:calc(28% - 41px)}.triangle-slot.right{top:144px;left:calc(72% - 41px)}.triangle-slot strong{font-size:calc(21px * var(--text-scale,1))}.triangle-slot small{font-size:calc(10px * var(--text-scale,1));color:var(--muted)}.triangle-slot input{width:78px;min-height:33px;border:2px solid var(--green);border-radius:7px;padding:3px 6px;direction:ltr;text-align:center;background:white;font-size:calc(17px * var(--text-scale,1))}.triangle-slot bdi{font-size:calc(16px * var(--text-scale,1));color:var(--green);font-weight:700}.triangle-help{font-size:calc(12px * var(--text-scale,1));color:var(--muted);text-align:center;margin:8px 0}.triangle-check{width:100%;margin-top:6px}.formula-context{background:#e7f0e9;border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:calc(14px * var(--text-scale,1))}.formula-networks{margin-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:14px}.formula-networks .math{font-size:calc(17px * var(--text-scale,1));line-height:1.9;overflow-wrap:anywhere}.formula-networks h3{font-size:calc(18px * var(--text-scale,1))}.units-list{display:flex;flex-wrap:wrap;gap:15px;margin:14px 0;color:var(--muted);font-size:calc(13px * var(--text-scale,1))}.sheet-answer{padding:15px;background:var(--card);border:1px solid var(--line);border-radius:12px;margin-bottom:14px}.sheet-answer label{display:block;font-weight:700}.sheet-answer input{width:160px;min-height:44px;border:2px solid var(--green);border-radius:8px;padding:7px 10px;font-size:calc(21px * var(--text-scale,1))}.sheet-feedback{margin-bottom:13px}.calc-dialog{max-width:370px}.calc-screen{width:100%;border:1px solid #b4c9be;border-radius:11px;background:white;min-height:56px;padding:10px;font-size:calc(23px * var(--text-scale,1));direction:ltr;text-align:left}.calc-result{direction:ltr;text-align:left;font-size:calc(22px * var(--text-scale,1));color:var(--green);min-height:40px;overflow-wrap:anywhere;margin:8px 0}.calc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;direction:ltr}.calc-grid button{height:48px;border-radius:9px;background:var(--card);border:1px solid var(--line);font-size:calc(21px * var(--text-scale,1));color:var(--ink)}.calc-grid button.operator{background:#e4eee7;color:var(--green)}.calc-grid button.equals{background:var(--green);color:white}.calc-actions{display:flex;gap:8px;margin-top:13px}.calc-actions .btn{flex:1;font-size:calc(14px * var(--text-scale,1))}.confirm-dialog{max-width:460px}.large-text{font-size:calc(19px * var(--text-scale,1))}.large-text .small,.large-text .rounding,.large-text .triangle-help{font-size:calc(15px * var(--text-scale,1))}
    @media(max-width:850px){.exercise-grid,.sim-layout{grid-template-columns:1fr}.hero-symbol{width:115px;height:115px;font-size:calc(25px * var(--text-scale,1))}.course-head{flex-direction:column}.sim-controls{display:grid;grid-template-columns:1fr auto;gap:5px 16px}.sim-controls input[type=range]{grid-column:1/-1}.sim-controls .toggle{margin:5px 0;grid-column:1}.sim-controls .btn{grid-column:2}.sim-controls .small{grid-column:1/-1}.metrics{margin-top:14px}}
    .diagram-preview{display:block;width:100%;padding:0;background:transparent;color:inherit;border-radius:10px}.diagram-preview svg{max-width:100%}.diagram-open-label{display:block;padding:7px;color:var(--green);font-size:calc(13px * var(--text-scale,1));font-weight:700;text-align:center}.diagram-preview:hover{background:var(--soft)}.diagram-toolbar{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px}.diagram-toolbar .btn{min-width:44px;min-height:44px}.diagram-viewport{overflow:auto;max-height:60vh;direction:ltr;overscroll-behavior:contain;touch-action:pan-x pan-y pinch-zoom;border:1px solid var(--line);border-radius:12px;background:var(--card)}.diagram-canvas{width:100%;min-width:100%}.diagram-canvas svg{display:block;width:100%;height:auto;max-width:none}.formula-tabs{display:flex;gap:8px;margin-bottom:16px}.formula-tab{flex:1;min-height:46px;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--muted);font-weight:700}.formula-tab[aria-selected=true]{background:var(--ink);border-color:var(--ink);color:white}.sheet-givens{margin:10px 0}.sheet-givens .given{min-width:0}.sheet-answer input{max-width:100%;min-width:0}
    @media(max-width:570px){.app{padding:14px 12px 25px}.topbar{align-items:flex-start;padding-bottom:14px;flex-wrap:wrap}.top-tools{width:100%}.top-tools .btn{flex:1;font-size:calc(14px * var(--text-scale,1))}.brand-title{font-size:calc(17px * var(--text-scale,1))}.hero{padding:23px 0 18px}.hero-symbol{display:none}.hero-copy p{font-size:calc(15px * var(--text-scale,1))}.tabs{gap:5px}.tab{padding:11px 8px;font-size:calc(14px * var(--text-scale,1));min-height:73px}.tab span{font-size:calc(10px * var(--text-scale,1))}.card{padding:16px}.level{font-size:calc(14px * var(--text-scale,1))}.given{min-width:85px;padding:7px 10px}.given bdi{font-size:calc(17px * var(--text-scale,1))}.answer-row{flex-wrap:wrap}.answer-row>.btn{width:100%}.answer-tools .btn{font-size:calc(13px * var(--text-scale,1));flex:1;padding:9px}.formula-grid,.formula-networks{grid-template-columns:1fr}.formula-card{padding:13px}dialog{padding:16px;border-radius:16px}.sim-controls{grid-template-columns:1fr}.sim-controls .btn{grid-column:1}.metrics{grid-template-columns:1fr 1fr 1fr}.metric{padding:7px}.metric bdi{font-size:calc(14px * var(--text-scale,1))}.metric small{font-size:calc(10px * var(--text-scale,1))}h2{font-size:calc(22px * var(--text-scale,1))}.footer .text-btn{font-size:calc(12px * var(--text-scale,1))}}
    .sim-layout>div{min-width:0}
    .formula-tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}.formula-tab{min-width:0}.manual-entry{display:flex;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:18px}.manual-intro{margin-bottom:14px}.manual-choices{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:10px 0 18px}.manual-choice{min-width:0;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:11px;padding:12px;text-align:right}.manual-choice strong{display:block;font-size:calc(15px * var(--text-scale,1));line-height:1.5}.manual-choice bdi{font-size:calc(14px * var(--text-scale,1));color:var(--muted);margin-top:5px}.manual-choice[aria-pressed=true]{border-color:var(--green);box-shadow:inset 0 0 0 1px var(--green);background:var(--soft)}.manual-workspace{display:grid;grid-template-columns:170px minmax(0,1fr);gap:22px;align-items:start}.manual-list{min-width:0;background:var(--soft);padding:12px;border-radius:12px}.manual-list>.btn{width:100%;margin-bottom:10px}.manual-list h3{font-size:calc(14px * var(--text-scale,1));margin-bottom:10px}.manual-list-row{display:flex;direction:ltr;align-items:center;gap:6px;margin:8px 0}.manual-list-row bdi{font-weight:700;white-space:nowrap}.manual-list-row input{width:0;min-width:0;flex:1;min-height:42px;border:1px solid #a8c4b6;border-radius:7px;background:white;padding:5px;direction:ltr;text-align:center;font-size:calc(17px * var(--text-scale,1))}.manual-form{min-width:0}.manual-form h3{text-align:center;font-size:calc(17px * var(--text-scale,1))}.manual-placeholder{border:1px dashed #b9cfc2;border-radius:13px;padding:30px 15px;text-align:center;color:var(--muted)}.manual-triangle{width:100%;max-width:360px;height:auto;aspect-ratio:260/225}.manual-triangle .triangle-slot{width:32%;gap:3px}.manual-triangle .triangle-slot.top{top:18%;left:34%}.manual-triangle .triangle-slot.left{top:63%;left:12%}.manual-triangle .triangle-slot.right{top:63%;left:56%}.manual-triangle .triangle-slot input{width:100%;min-width:0;max-width:100px;min-height:40px;padding:4px;font-size:calc(20px * var(--text-scale,1))}.manual-answer{margin-top:15px}.manual-answer label{display:block;margin-bottom:7px;font-weight:700}.manual-answer input{width:100%;min-width:0;min-height:46px;padding:8px 10px;border:2px solid var(--green);border-radius:9px;background:white;font-size:calc(21px * var(--text-scale,1));direction:ltr;text-align:left}.manual-answer .btn{width:100%;margin-top:10px}.manual-note{margin:14px 0 0}.manual-status{min-height:0}.manual-status:empty{display:none}
    @media(max-width:570px){.formula-tab{padding:8px 5px;font-size:calc(13px * var(--text-scale,1))}.manual-choices{gap:7px}.manual-choice{padding:9px}.manual-choice strong{font-size:calc(13px * var(--text-scale,1))}.manual-choice bdi{font-size:calc(12px * var(--text-scale,1))}.manual-workspace{grid-template-columns:84px minmax(0,1fr);gap:10px}.manual-list{padding:6px}.manual-list>.btn{padding:7px 3px;font-size:calc(13px * var(--text-scale,1))}.manual-list h3{font-size:calc(12px * var(--text-scale,1));line-height:1.5}.manual-list-row{gap:3px}.manual-list-row bdi{font-size:calc(14px * var(--text-scale,1))}.manual-list-row input{min-height:36px;padding:3px;font-size:calc(16px * var(--text-scale,1))}.manual-triangle .triangle-slot{gap:2px}.manual-triangle .triangle-slot strong{font-size:calc(17px * var(--text-scale,1))}.manual-triangle .triangle-slot input{min-height:28px;height:28px;font-size:calc(16px * var(--text-scale,1));padding:2px}.manual-form h3{font-size:calc(14px * var(--text-scale,1))}.manual-answer label{font-size:calc(14px * var(--text-scale,1))}.manual-answer .btn{font-size:calc(13px * var(--text-scale,1));padding:9px 6px}.manual-answer input{font-size:calc(18px * var(--text-scale,1))}.manual-list .small{font-size:calc(11px * var(--text-scale,1))}}
    @media(max-width:570px){.sim-layout{display:flex;flex-direction:column;gap:14px}.sim-layout>div:first-child{display:contents}.sim-layout .diagram{order:0;width:100%}.sim-layout .sim-controls{order:1;width:100%}.sim-layout #sim-metrics{order:2;width:100%}.table-scroll table,.table-scroll tbody{display:block;width:100%}.table-scroll caption{display:block;width:100%;white-space:normal}.table-scroll thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}.table-scroll tbody tr{display:block;margin-bottom:12px;border:1px solid var(--line);border-radius:10px;overflow:hidden}.table-scroll tbody td{display:flex;align-items:center;justify-content:space-between;gap:12px;white-space:normal;padding:8px 12px}.table-scroll tbody td::before{content:attr(data-label);color:var(--muted);font-size:calc(13px * var(--text-scale,1))}.table-scroll tbody td:last-child{border-bottom:0}}
    .skip-link{position:fixed;top:-100px;right:12px;z-index:10000;background:#182e3c;color:white;padding:12px 18px;border-radius:8px}.skip-link:focus{top:12px}.top-tools{max-width:720px}.top-tools .btn{min-width:0;overflow-wrap:anywhere}.profile-dialog{max-width:650px}.profile-fields{display:grid;grid-template-columns:1fr 1fr;gap:14px}.profile-fields label{display:block;font-weight:700}.profile-fields input{display:block;min-width:0;width:100%;min-height:46px;padding:9px;border:1px solid #a8c4b6;border-radius:9px;background:white;color:var(--ink)}.terms-document{margin:18px 0;border:1px solid var(--line);border-radius:12px;padding:13px}.terms-document summary,.profile-accessibility summary{cursor:pointer;font-weight:700;min-height:44px;align-content:center}.terms-document p,.terms-document li{font-size:calc(14px * var(--text-scale,1))}.terms-document h3{font-size:calc(17px * var(--text-scale,1));margin-top:18px}.consent-row{display:flex;align-items:flex-start;gap:10px;margin:18px 0;font-size:calc(14px * var(--text-scale,1))}.consent-row input{flex:0 0 22px;width:22px;height:22px;margin:2px 0;accent-color:var(--green)}.profile-accessibility{margin-top:18px}.accessibility-dialog{max-width:650px}.accessibility-options{display:grid;gap:12px;margin:14px 0}.accessibility-options label{display:flex;align-items:center;gap:10px;min-height:44px}.accessibility-options input[type=checkbox]{width:22px;height:22px;accent-color:var(--green)}.accessibility-options select{min-height:44px;padding:7px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}.text-scale-150 .manual-workspace{grid-template-columns:1fr}.text-scale-150 .manual-list{max-width:none}.text-scale-150 .manual-list-row input{max-width:220px}.high-contrast{--paper:#fff;--card:#fff;--ink:#000;--muted:#242424;--line:#333;--green:#005b4f;--soft:#e8f4ed}.high-contrast .triangle svg path{stroke:#000}.high-contrast .manual-choice,.high-contrast .formula-tab,.high-contrast .level{border-color:#000}.reduce-motion *,.reduce-motion *::before,.reduce-motion *::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.highlight-links a,.highlight-links .text-btn{text-decoration:underline;text-decoration-thickness:2px}.personal-progress{margin-top:28px}.personal-progress h2:focus,#sim-title:focus{outline:3px solid #c38330;outline-offset:4px}.progress-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}.personal-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:18px 0}.personal-stat{border:1px solid var(--line);border-radius:12px;padding:13px}.personal-stat strong{display:block;font-size:calc(25px * var(--text-scale,1));color:var(--green)}.personal-chart{margin:22px 0}.personal-chart-row{display:grid;grid-template-columns:115px minmax(0,1fr) 58px;align-items:center;gap:12px;margin:16px 0;font-size:calc(14px * var(--text-scale,1))}.personal-bar{height:25px;border-radius:6px;overflow:hidden;background:#e2e9e2;border:1px solid #c9d8cd}.personal-bar>div{height:100%;background:#116e65;min-width:0}.personal-rate{direction:ltr;text-align:left;font-weight:700}.personal-progress .table-scroll th,.personal-progress .table-scroll td{white-space:normal}.personal-progress .table-scroll td:first-child{font-weight:700}.sim-jump{margin-top:10px}.simulator{background:#050505;color:#fff;border-color:#555}.simulator .eyebrow,.simulator .muted,.simulator .small,.simulator .metric small,.simulator caption{color:#fff}.simulator .sim-controls,.simulator .metric,.simulator th,.simulator .btn.secondary{background:#111;color:#fff;border-color:#666}.simulator .sim-value,.simulator .metric bdi{color:#fff}.simulator td[data-label="זרם"] bdi,.simulator .metric:nth-child(2) bdi{color:#ff6565}.simulator td[data-label="מתח"] bdi{color:#65e680}.simulator .diagram-preview,.simulator .diagram-preview:hover{background:#000;color:#fff}.simulator .diagram-open-label{color:#fff}.simulator .metric,.simulator .table-scroll td,.simulator .table-scroll tbody tr{border-color:#666}.simulator th{color:#fff}.simulator input[type=range],.simulator input[type=checkbox]{accent-color:#fff}.sim-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:calc(13px * var(--text-scale,1));margin:12px 0;color:#fff}.sim-legend .current{color:#ff6565}.sim-legend .voltage{color:#65e680}.simulator .table-scroll tbody td::before{color:#fff}.dark-diagram .diagram-viewport{background:#000;border-color:#666}.manual-choice svg{display:block;max-width:115px;width:100%;height:auto;margin:6px auto}.manual-choice math{font-size:calc(15px * var(--text-scale,1))}.formula-lines math{margin:3px 0}.mathml{font-family:"Cambria Math","STIX Two Math","Times New Roman",serif;direction:ltr;unicode-bidi:isolate;max-width:100%}.formula-networks .math{overflow-x:auto;max-width:100%}.formula-card .mathml{font-size:calc(20px * var(--text-scale,1))}select:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{outline:3px solid #c38330;outline-offset:3px}
    @media(max-width:570px){.top-tools{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));max-width:none}.profile-fields{grid-template-columns:1fr}.personal-summary{gap:6px}.personal-stat{padding:9px}.personal-stat strong{font-size:calc(21px * var(--text-scale,1))}.personal-stat .small{font-size:calc(11px * var(--text-scale,1))}.personal-chart-row{grid-template-columns:82px minmax(0,1fr) 43px;gap:7px;font-size:calc(12px * var(--text-scale,1))}.personal-chart-row .personal-rate{font-size:calc(12px * var(--text-scale,1))}.personal-progress .table-scroll tbody td{gap:10px}.personal-progress .table-scroll tbody td::before{max-width:55%}.text-scale-150 .top-tools,.text-scale-150 .tabs,.text-scale-150 .formula-tabs,.text-scale-150 .manual-choices{grid-template-columns:1fr}.text-scale-150 .personal-summary{grid-template-columns:1fr}.text-scale-150 .personal-chart-row{grid-template-columns:1fr;gap:5px}.text-scale-150 .personal-rate{text-align:right}}
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
    .parallel-formulas{display:flex;flex-direction:column;gap:calc(22px * var(--text-scale,1));margin-top:16px}
    .parallel-formulas .network-formula{padding:4px 0;line-height:1.5}
  </style>
</head>
<body>
<a class="skip-link" href="#learning-main">דילוג לתרגול</a>
<div class="app" id="app">
  <header class="topbar">
    <div class="identity"><div class="brand-icon" aria-hidden="true">ϟ</div><div><div class="brand-title">יסודות החשמל</div><div class="eyebrow">תרגול למתחילים · DC</div></div></div>
    <div class="top-tools"><button class="btn secondary" data-open-formulas>דף נוסחאות △</button><button class="btn secondary" data-open-calculator>מחשבון</button><button class="btn secondary" id="text-size" aria-pressed="false" aria-label="שינוי גודל טקסט">שינוי גודל טקסט</button><button class="btn secondary" data-open-profile id="profile-label">הפרופיל שלי</button><button class="btn secondary" data-show-progress>התקדמות אישית</button><button class="btn secondary" data-open-accessibility>נגישות</button><button class="btn secondary" data-new-course>תרגילים חדשים</button></div>
  </header>
  <section class="hero"><div class="hero-copy"><div class="eyebrow">לומדים להבין, ואז לחשב</div><h1>חשמל, צעד אחרי צעד.</h1><p>תרגול קצר של חוק אום, הספק ומעגלים. מתחילים במספרים שלמים ומתקדמים לעשרוניים — עם מחשבון, רמזים ודף נוסחאות בכל שלב.</p></div><div class="hero-symbol" aria-hidden="true">U = I × R<small>להבין את הקשר בין הנתונים</small></div></section>
  <nav class="tabs" role="tablist" aria-label="תחומי התרגול">
    <button id="tab-ohm" class="tab" data-tab="ohm" role="tab" aria-controls="workspace" aria-selected="true" tabindex="0">חוק אום והספק<span>מתח · זרם · התנגדות · הספק</span></button>
    <button id="tab-series" class="tab" data-tab="series" role="tab" aria-controls="workspace" aria-selected="false" tabindex="-1">מעגל טורי<span>אותו זרם בכל הרכיבים</span></button>
    <button id="tab-parallel" class="tab" data-tab="parallel" role="tab" aria-controls="workspace" aria-selected="false" tabindex="-1">מעגל מקבילי<span>אותו מתח בכל הענפים</span></button>
    <button id="tab-simulator" class="tab" data-tab="simulator" role="tab" aria-controls="simulator-workspace" aria-selected="false" tabindex="-1">סימולטור<span>מעגל מתרגיל או מעגל משלכם</span></button>
  </nav>
  <main id="learning-main" tabindex="-1" aria-label="תרגול והתקדמות"><div id="storage-notice" class="feedback error" role="status" hidden></div><section id="workspace" role="tabpanel" aria-labelledby="tab-ohm"></section><section id="simulator-workspace" role="tabpanel" aria-labelledby="tab-simulator" hidden></section></main>
  <footer class="footer"><div>הפרופיל וההתקדמות האישית נשמרים בדפדפן במכשיר הזה. אפשר להמשיך מהתרגיל האחרון או לקבל תרגילים חדשים בכפתור האיפוס.</div><div><button class="text-btn" data-open-formulas>דף נוסחאות</button><button class="text-btn" id="new-course">איפוס תרגילים</button><button class="text-btn" data-open-terms>תנאי שימוש ופרטיות</button><button class="text-btn" data-open-accessibility>הצהרת נגישות</button></div></footer>
</div>
<dialog id="progress-dialog" class="progress-dialog" aria-labelledby="progress-dialog-title"><div class="dialog-head"><h2 id="progress-dialog-title">התקדמות אישית</h2><button class="close" data-close-dialog="progress-dialog" aria-label="סגירת ההתקדמות האישית">×</button></div><section id="personal-progress" class="card personal-progress" aria-labelledby="personal-progress-title"></section></dialog>
<dialog id="formula-dialog" aria-labelledby="formula-title"><div class="dialog-head"><h2 id="formula-title">דף נוסחאות</h2><button class="close" data-close-dialog="formula-dialog" aria-label="סגירת דף הנוסחאות">×</button></div><nav class="formula-tabs" role="tablist" aria-label="תצוגת דף הנוסחאות"><button id="formula-tab-reference" class="formula-tab" data-formula-tab="reference" role="tab" aria-selected="true" aria-controls="formula-body" tabindex="0">נוסחאות</button><button id="formula-tab-help" class="formula-tab" data-formula-tab="help" role="tab" aria-selected="false" aria-controls="formula-body" tabindex="-1">עזרה</button><button id="formula-tab-manual" class="formula-tab" data-formula-tab="manual" role="tab" aria-selected="false" aria-controls="formula-body" tabindex="-1">פתירה בעזרת המשולש</button></nav><p class="formula-intro">החלק העליון במשולש הוא מכפלת שני החלקים התחתונים. כדי למצוא חלק תחתון, מחלקים את העליון בחלק התחתון הידוע. בלשונית עזרה מופיעים נתוני התרגיל ואפשר לענות במשולש המתאים.</p><div id="formula-body" role="tabpanel" aria-labelledby="formula-tab-reference" tabindex="0"></div><section id="manual-keypad" class="manual-keypad" aria-label="מקלדת מספרים X וסימן שאלה" hidden><div class="manual-keypad-header"><span class="small muted">מקלדת נתונים</span><bdi id="manual-keypad-value"></bdi></div><div class="manual-keypad-grid"><button type="button" data-manual-key="7" aria-label="7">7</button><button type="button" data-manual-key="8" aria-label="8">8</button><button type="button" data-manual-key="9" aria-label="9">9</button><button type="button" data-manual-key="X" aria-label="ערך שלא התבקש לחשב">X</button><button type="button" data-manual-key="4" aria-label="4">4</button><button type="button" data-manual-key="5" aria-label="5">5</button><button type="button" data-manual-key="6" aria-label="6">6</button><button type="button" data-manual-key="?" aria-label="נעלם">?</button><button type="button" data-manual-key="1" aria-label="1">1</button><button type="button" data-manual-key="2" aria-label="2">2</button><button type="button" data-manual-key="3" aria-label="3">3</button><button type="button" data-manual-key="backspace" aria-label="מחיקת תו">⌫</button><button type="button" data-manual-key="0" aria-label="0">0</button><button type="button" data-manual-key="." aria-label="נקודה עשרונית">.</button><button type="button" data-manual-key="clear" aria-label="ניקוי השדה">ניקוי</button><button type="button" data-manual-key="enter" aria-label="אישור ומעבר לשדה הבא">✓</button><button type="button" data-manual-key="done" aria-label="סגירת המקלדת">↓</button></div></section></dialog>
<dialog id="diagram-dialog" aria-labelledby="diagram-title"><div class="dialog-head"><h2 id="diagram-title">הגדלת הסכמה</h2><button class="close" data-close-dialog="diagram-dialog" aria-label="סגירת הסכמה המוגדלת">×</button></div><div class="diagram-toolbar" role="group" aria-label="הגדלת הסכמה"><button class="btn secondary tiny" data-diagram-zoom="in" aria-label="הגדלה">+</button><button class="btn secondary tiny" data-diagram-zoom="out" aria-label="הקטנה">−</button><button class="btn soft tiny" data-diagram-zoom="reset">התאמה למסך</button><bdi id="diagram-zoom-label" role="status" aria-live="polite">100%</bdi></div><p class="small muted">אפשר להגדיל באמצעות הכפתורים ולגלול בתוך הסכמה.</p><div class="diagram-viewport" id="diagram-viewport" tabindex="0" role="region" aria-label="סכמה מוגדלת — אפשר לגלול לצדדים ולמעלה ולמטה"><div class="diagram-canvas" id="diagram-canvas"></div></div></dialog>
<dialog id="calculator-dialog" class="calc-dialog" aria-labelledby="calc-title"><div class="dialog-head"><h2 id="calc-title">מחשבון</h2><button class="close" data-close-dialog="calculator-dialog" aria-label="סגירת המחשבון">×</button></div><label class="small muted" for="calc-screen">חיבור, חיסור, כפל וחילוק</label><input id="calc-screen" class="calc-screen" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" maxlength="160" placeholder="12 ÷ 3"><div id="calc-result" class="calc-result" role="status" aria-live="polite"></div><div class="calc-grid" id="calc-grid"></div><p id="calc-error" class="feedback error" role="alert"></p><div class="calc-actions"><button class="btn" id="calc-use" disabled>העברה לתשובה</button><button class="btn secondary" id="calc-clear">ניקוי</button></div><button class="text-btn" data-open-formulas>דף נוסחאות △</button><p class="small muted" style="margin-top:12px;margin-bottom:0">המחשבון שומר על סדר פעולות חשבון. אפשר להשתמש בסוגריים. אין פונקציית שורש.</p></dialog>
<dialog id="new-course-dialog" class="confirm-dialog" aria-labelledby="new-course-title"><div class="dialog-head"><h2 id="new-course-title">להתחיל סבב חדש?</h2><button class="close" data-close-dialog="new-course-dialog" aria-label="סגירה">×</button></div><p>התרגילים בסבב יוחלפו. ההתקדמות האישית, הגרף, הטבלה והפרופיל שלכם יישמרו.</p><div class="completion-actions"><button class="btn" id="new-course-confirm">כן, תרגילים חדשים</button><button class="btn secondary" data-close-dialog="new-course-dialog">חזרה לתרגול</button></div></dialog>
<dialog id="profile-dialog" class="profile-dialog" aria-labelledby="profile-title"><div class="dialog-head"><h2 id="profile-title">הפרופיל שלי במכשיר הזה</h2><button class="close" id="profile-close" data-close-dialog="profile-dialog" aria-label="סגירת הפרופיל">×</button></div><p class="small muted">בכניסה הראשונה מזינים שם ותאריך לידה ומאשרים את תנאי השימוש. הפרטים וההתקדמות יישמרו בדפדפן הזה; ניקוי נתוני הדפדפן עלול למחוק אותם.</p><form id="profile-form" novalidate><div class="profile-fields"><label for="profile-name">שם<input id="profile-name" aria-describedby="profile-error" type="text" autocomplete="name" maxlength="80" required></label><label for="profile-birth">תאריך לידה<input id="profile-birth" aria-describedby="profile-error" type="date" autocomplete="bday" required></label></div><details class="terms-document" id="profile-terms"><summary>תנאי שימוש ופרטיות — לקריאה לפני האישור</summary><div data-terms-document></div></details><label class="consent-row" for="profile-consent"><input id="profile-consent" aria-describedby="profile-error" type="checkbox" required>אני מסכים/ה לתנאי השימוש ולשמירת הפרופיל ונתוני התרגול באופן מקומי במכשיר הזה.</label><div id="profile-error" class="feedback error" role="alert"></div><button class="btn" type="submit">שמירה ותחילת תרגול</button></form><details class="profile-accessibility"><summary>התאמות נגישות לפני תחילת התרגול</summary><div id="profile-accessibility-controls"></div></details></dialog>
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
  const palette = complete ? {text:'#ffffff',wire:'#ffffff',surface:'#000000',current:'#ff6565',voltage:'#65e680',power:'#ffffff'} : {text:'#203c47',wire:'#687e84',surface:'#fffefa',current:'#159485',voltage:'#203c47',power:'#956122'};
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
  const text = (x, y, value, size = 17, anchor = 'middle', color = palette.text) =>
    `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" fill="${color}" direction="ltr">${value}</text>`;
  const wire = d => `<path d="${d}" fill="none" stroke="${palette.wire}" stroke-width="3" stroke-linecap="round"/>`;
  const flow = (d, current) => `<path d="${d}" fill="none" stroke="${palette.current}" stroke-width="4" stroke-dasharray="7 20" class="${moving ? 'flow' : ''}" style="${moving ? `animation-duration:${Math.max(.65, 3.2 / (1 + current * .35))}s` : 'animation:none'}" opacity="${voltage > 0 ? .9 : 0}"/>`;
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
      xs.forEach((x, j) => parts.push(flow(`M85 184 L85 100 L${x} 100 L${x} 330 L85 330 L85 246`, model.currents[j])));
      if (voltage > 0) {
        parts.push(arrow(175, 100, 'right'), arrow(185, 330, 'left'));
        xs.forEach((x, j) => { parts.push(arrow(x, 147, 'down')); parts.push(text(x + 35, 294, `I${j + 1} = ${DC.fmt(model.currents[j])} A`, 14, 'start', palette.current)); });
      }
    }
    xs.forEach(x => parts.push(`<circle cx="${x}" cy="100" r="4" fill="${palette.wire}"/><circle cx="${x}" cy="330" r="4" fill="${palette.wire}"/>`));
  } else {
    const path = 'M85 184 L85 100 L735 100 L735 330 L85 330 L85 246';
    parts.push(wire(path));
    if (complete) {
      parts.push(flow(path, model.total));
      if (voltage > 0) parts.push(arrow(166, 100, 'right'), arrow(735, 214, 'down'), arrow(395, 330, 'left'), text(435, 312, `I = ${DC.fmt(model.total)} A`, 16, 'middle', palette.current));
    }
  }
  q.resistances.forEach((r, j) => {
    const x = xs[j], y = parallel ? 215 : 100;
    const known = complete || q.kind !== 'ohm' || Object.hasOwn(q.givens, 'R');
    const resistance = known ? `${DC.fmt(r)} Ω` : '? Ω';
    if (q.lamps[j]) {
      const brightness = complete && voltage > 0 ? Math.min(1, model.powers[j] / (referencePower * 1.4)) : 0;
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="43" fill="#ffffff" opacity="${brightness * .32}"/>`);
      parts.push(`<circle cx="${x}" cy="${y}" r="25" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="21" fill="#ffffff" opacity="${brightness * .15}"/>`);
      parts.push(`<path d="M${x - 16} ${y - 16} L${x + 16} ${y + 16} M${x + 16} ${y - 16} L${x - 16} ${y + 16}" stroke="${palette.wire}" stroke-width="2"/>`);
    } else {
      parts.push(`<rect x="${x - (parallel ? 17 : 31)}" y="${y - (parallel ? 30 : 17)}" width="${parallel ? 34 : 62}" height="${parallel ? 60 : 34}" rx="2" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
    }
    if (parallel) {
      parts.push(text(x + 35, y - 10, `R${j + 1}`, 16, 'start'), text(x + 35, y + 14, resistance, 16, 'start'));
      if (complete) parts.push(text(x + 35, y + 39, `${DC.fmt(model.powers[j])} W`, 13, 'start', palette.power), text(x + 35, y + 61, `U${j + 1} = ${DC.fmt(model.drops[j])} V`, 13, 'start', palette.voltage));
    } else {
      parts.push(text(x, 53, `R${j + 1} = ${resistance}`, 17));
      if (complete) {
        parts.push(text(x, 152, `U${j + 1} = ${DC.fmt(model.drops[j])} V`, 14, 'middle', palette.voltage));
        parts.push(text(x, 177, `P${j + 1} = ${DC.fmt(model.powers[j])} W`, 14, 'middle', palette.power));
      }
    }
  });
  parts.push(`<circle cx="85" cy="215" r="31" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
  parts.push(text(85, 204, '+', 19), text(85, 223, 'DC', 14), text(85, 239, '−', 18));
  const knownVoltage = complete || Object.hasOwn(q.givens, 'U');
  parts.push(text(138, 222, `U = ${knownVoltage ? DC.fmt(voltage) : '?'} V`, 16, 'start'));
  const title = `${q.kind === 'parallel' ? 'מעגל מקבילי' : q.kind === 'series' ? 'מעגל טורי' : 'מעגל DC'} עם ${count} רכיבים`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 365" role="img" aria-label="${title}" dir="ltr"${complete ? ' style="background:#000000"' : ''}><title>${title}</title><desc>${complete ? `מתח המקור ${DC.fmt(voltage)} וולט. זרם כולל ${DC.fmt(model.total)} אמפר. זרם מסומן באדום ומפלי מתח בירוק; הערכים כתובים ליד הרכיבים.` : 'סכמה של נתוני התרגיל. מלבן הוא נגד ועיגול עם X הוא נורה.'}</desc>${parts.join('')}</svg>`;
}

function customCircuitSVG(q, options = {}) {
  const complete = options.complete === true;
  const palette = complete ? {text:'#ffffff',wire:'#ffffff',surface:'#000000',current:'#ff6565',voltage:'#65e680',power:'#ffffff'} : {text:'#203c47',wire:'#687e84',surface:'#fffefa',current:'#159485',voltage:'#203c47',power:'#956122'};
  const voltage = options.voltage ?? q.voltage;
  const moving = complete && options.animate !== false && voltage > 0;
  const model = DC.physics(q.kind, voltage, q.resistances);
  const baseline = DC.physics(q.kind, q.voltage, q.resistances);
  const referencePower = baseline.powers.reduce((largest,power)=>Math.max(largest,power),0);
  const parallel = q.kind === 'parallel';
  const count = q.resistances.length;
  const extended = count > 3, width = extended ? 240 + count * 210 : 820;
  const xs = extended ? Array.from({length:count},(_,i)=>280+i*210)
    : parallel ? (count === 1 ? [450] : count === 2 ? [350,610] : [280,475,670])
    : count === 1 ? [450] : count === 2 ? [330,600] : [260,450,640];
  const right = extended ? xs[xs.length-1]+90 : 735;
  const parts = [];
  const text = (x, y, value, size = 17, anchor = 'middle', color = palette.text) =>
    `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" fill="${color}" direction="ltr">${value}</text>`;
  const wire = d => `<path d="${d}" fill="none" stroke="${palette.wire}" stroke-width="3" stroke-linecap="round"/>`;
  const flow = (d, current) => `<path d="${d}" fill="none" stroke="${palette.current}" stroke-width="4" stroke-dasharray="7 20" class="${moving ? 'flow' : ''}" style="${moving ? `animation-duration:${Math.max(.65, 3.2 / (1 + current * .35))}s` : 'animation:none'}" opacity="${voltage > 0 ? .9 : 0}"/>`;
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
      xs.forEach((x, j) => parts.push(flow(`M85 184 L85 100 L${x} 100 L${x} 330 L85 330 L85 246`, model.currents[j])));
      if (voltage > 0) {
        parts.push(arrow(175, 100, 'right'), arrow(185, 330, 'left'));
        xs.forEach((x, j) => { parts.push(arrow(x, 147, 'down')); parts.push(text(x + 35, 294, `I${j + 1} = ${formatCustomNumber(model.currents[j])} A`, 14, 'start', palette.current)); });
      }
    }
    xs.forEach(x => parts.push(`<circle cx="${x}" cy="100" r="4" fill="${palette.wire}"/><circle cx="${x}" cy="330" r="4" fill="${palette.wire}"/>`));
  } else {
    const path = `M85 184 L85 100 L${right} 100 L${right} 330 L85 330 L85 246`;
    parts.push(wire(path));
    if (complete) {
      parts.push(flow(path, model.total));
      if (voltage > 0) parts.push(arrow(166, 100, 'right'), arrow(right, 214, 'down'), arrow((85+right)/2, 330, 'left'), text((85+right)/2, 312, `I = ${formatCustomNumber(model.total)} A`, 16, 'middle', palette.current));
    }
  }
  q.resistances.forEach((r, j) => {
    const x = xs[j], y = parallel ? 215 : 100;
    const known = complete || q.kind !== 'ohm' || Object.hasOwn(q.givens, 'R');
    const resistance = known ? `${formatCustomNumber(r)} Ω` : '? Ω';
    if (q.lamps[j]) {
      const brightness = complete && voltage > 0 ? Math.min(1, model.powers[j] / (referencePower * 1.4)) : 0;
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="43" fill="#ffffff" opacity="${brightness * .32}"/>`);
      parts.push(`<circle cx="${x}" cy="${y}" r="25" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
      if (brightness) parts.push(`<circle cx="${x}" cy="${y}" r="21" fill="#ffffff" opacity="${brightness * .15}"/>`);
      parts.push(`<path d="M${x - 16} ${y - 16} L${x + 16} ${y + 16} M${x + 16} ${y - 16} L${x - 16} ${y + 16}" stroke="${palette.wire}" stroke-width="2"/>`);
    } else {
      parts.push(`<rect x="${x - (parallel ? 17 : 31)}" y="${y - (parallel ? 30 : 17)}" width="${parallel ? 34 : 62}" height="${parallel ? 60 : 34}" rx="2" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
    }
    if (parallel) {
      parts.push(text(x + 35, y - 10, `R${j + 1}`, 16, 'start'), text(x + 35, y + 14, resistance, 16, 'start'));
      if (complete) parts.push(text(x + 35, y + 39, `${formatCustomNumber(model.powers[j])} W`, 13, 'start', palette.power), text(x + 35, y + 61, `U${j + 1} = ${formatCustomNumber(model.drops[j])} V`, 13, 'start', palette.voltage));
    } else {
      parts.push(text(x, 53, `R${j + 1} = ${resistance}`, 17));
      if (complete) {
        parts.push(text(x, 152, `U${j + 1} = ${formatCustomNumber(model.drops[j])} V`, 14, 'middle', palette.voltage));
        parts.push(text(x, 177, `P${j + 1} = ${formatCustomNumber(model.powers[j])} W`, 14, 'middle', palette.power));
      }
    }
  });
  parts.push(`<circle cx="85" cy="215" r="31" fill="${palette.surface}" stroke="${palette.wire}" stroke-width="2.5"/>`);
  parts.push(text(85, 204, '+', 19), text(85, 223, 'DC', 14), text(85, 239, '−', 18));
  const knownVoltage = complete || Object.hasOwn(q.givens, 'U');
  parts.push(text(138, 222, `U = ${knownVoltage ? formatCustomNumber(voltage) : '?'} V`, 16, 'start'));
  const title = `${q.kind === 'parallel' ? 'מעגל מקבילי' : q.kind === 'series' ? 'מעגל טורי' : 'מעגל DC'} עם ${count} רכיבים`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} 365" role="img" aria-label="${title}" dir="ltr"${complete ? ` style="background:#000000${extended ? ';width:'+width+'px;max-width:none' : ''}"` : ''}><title>${title}</title><desc>${complete ? `מתח המקור ${formatCustomNumber(voltage)} וולט. זרם כולל ${formatCustomNumber(model.total)} אמפר. זרם מסומן באדום ומפלי מתח בירוק; הערכים כתובים ליד הרכיבים.` : 'סכמה של נתוני התרגיל. מלבן הוא נגד ועיגול עם X הוא נורה.'}</desc>${parts.join('')}</svg>`;
}

const $ = id => document.getElementById(id);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
const names = { ohm: 'חוק אום והספק', series: 'מעגל טורי', parallel: 'מעגל מקבילי' };
const letters = ['א׳', 'ב׳', 'ג׳'];
const units = { U: 'V', I: 'A', R: 'Ω', P: 'W' };
const triangleDefinitions = [
    { id:'ohm', title:'חוק אום', slots:[{key:'U',symbol:'U',unit:'V'},{key:'I',symbol:'I',unit:'A'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['U = I × R','I = U ÷ R','R = U ÷ I'] },
    { id:'power-ui', title:'הספק לפי מתח וזרם', slots:[{key:'P',symbol:'P',unit:'W'},{key:'U',symbol:'U',unit:'V'},{key:'I',symbol:'I',unit:'A'}], formulas:['P = U × I','U = P ÷ I','I = P ÷ U'] },
    { id:'power-ir', title:'הספק לפי זרם והתנגדות', slots:[{key:'P',symbol:'P',unit:'W'},{key:'I2',symbol:'I²',unit:'I × I'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['P = I² × R','R = P ÷ I²'], note:'I² פירושו I כפול I. בתרגול משתמשים כאן בזרם ידוע; לא מוציאים שורש.' },
    { id:'power-ur', title:'הספק לפי מתח והתנגדות', slots:[{key:'U2',symbol:'U²',unit:'U × U'},{key:'P',symbol:'P',unit:'W'},{key:'R',symbol:'R',unit:'Ω'}], formulas:['U² = P × R','P = U² ÷ R','R = U² ÷ P'], note:'U² פירושו U כפול U. בתרגול משתמשים כאן במתח ידוע; לא מוציאים שורש.' },
];
const recentKey = 'dc.basics.recent.v1';
let viewTab = 'ohm', simulatorMode = 'custom', simulatorQuestion = null;
const customDraft = {kind:'series',voltage:'24',resistances:['10','10']};
let customSimulator = {custom:true,kind:'series',voltage:24,simVoltage:24,resistances:[10,10],lamps:[false,false],givens:{},simAnimate:true};
const courseKey='dc.basics.course.v1';
let courseSeed=null,coursePrevious=[];
let questions, tab = 'ohm', levels = { ohm:0, series:0, parallel:0 }, positions, previous = [];
let feedback = '', feedbackType = 'success', calculatorValue = null, calculatorFresh = false;
let formulaView = 'reference', calculatorReturnToFormulas = false;
let diagramZoom = 1, diagramBaseWidth = 0;
let manualKeypadTarget = null, manualKeypadFieldId = null;
const personalKey = 'dc.basics.personal.v1', termsVersion = '2026-10-14.1';
const topicNames = { ohm:'חוק אום', power:'הספק', series:'מעגל טורי', parallel:'מעגל מקבילי' };
let storageAvailable = true, profileRequired = false;
const entryStartedAt = new Date().toISOString();
let activeSessionId = null;
let personal = loadPersonal();
function emptyCounters() { return { attempted:0, first:0, attempts:0, solved:0, helped:0 }; }
function emptyPersonal() {
  return { version:1, profile:null, preferences:{textScale:100,contrast:false,motion:window.matchMedia('(prefers-reduced-motion: reduce)').matches,links:false},
    sessions:[],topics:Object.fromEntries(Object.keys(topicNames).map(key => [key,emptyCounters()])), totals:{...emptyCounters(),exercises:0} };
}
function loadPersonal() {
  const result = emptyPersonal();
  try {
    const saved = JSON.parse(localStorage.getItem(personalKey) || 'null');
    if (!saved || saved.version !== 1) return result;
    if (saved.profile && typeof saved.profile.name === 'string' && typeof saved.profile.birth === 'string') result.profile = {name:saved.profile.name.slice(0,80),birth:saved.profile.birth,termsVersion:saved.profile.termsVersion,acceptedAt:saved.profile.acceptedAt};
    if ([100,125,150].includes(saved.preferences?.textScale)) result.preferences.textScale = saved.preferences.textScale;
    for (const key of ['contrast','motion','links']) if (typeof saved.preferences?.[key] === 'boolean') result.preferences[key] = saved.preferences[key];
    if(Array.isArray(saved.sessions)) result.sessions=saved.sessions.filter(item=>item&&typeof item.id==='string'&&typeof item.startedAt==='string'&&Number.isFinite(Date.parse(item.startedAt))&&Number.isSafeInteger(item.attempted)&&item.attempted>=0&&Number.isSafeInteger(item.first)&&item.first>=0&&item.first<=item.attempted).map(item=>({id:item.id,startedAt:item.startedAt,attempted:item.attempted,first:item.first}));
    for (const [key,counters] of Object.entries(result.topics)) for (const metric of Object.keys(counters)) if (Number.isSafeInteger(saved.topics?.[key]?.[metric]) && saved.topics[key][metric] >= 0) counters[metric] = saved.topics[key][metric];
    for (const metric of Object.keys(result.totals)) if (Number.isSafeInteger(saved.totals?.[metric]) && saved.totals[metric] >= 0) result.totals[metric] = saved.totals[metric];
  } catch { storageAvailable = false; }
  return result;
}
function savePersonal() {
  try { localStorage.setItem(personalKey,JSON.stringify(personal)); storageAvailable = true; }
  catch { storageAvailable = false; }
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
function profileReady() { return !!personal.profile && personal.profile.name.trim().length >= 2 && validBirth(personal.profile.birth) && personal.profile.termsVersion === termsVersion; }
function termsHTML() {
  return `<p class="small muted">עדכון: 14.10.2026</p><h3>מטרת האתר והשימוש בתוכן</h3><p>האתר מיועד ללימוד ולתרגול עיוני של יסודות החשמל ומעגלי DC באמצעות מודלים פשוטים. התרגילים והסימולטור אינם הוראות לביצוע עבודות חשמל ואינם תחליף להכשרה, להסמכה, לייעוץ מקצועי או לבדיקה של איש מקצוע מוסמך. אין לבצע חיבור, תיקון, מדידה או שינוי במערכת חשמל ממשית על סמך האתר.</p><h3>דיוק, זמינות והגבלת אחריות</h3><p>ייתכנו טעויות, עיגול מספרים, השמטות ותקלות. המודלים אינם מציגים את כל התופעות או את הסיכונים שבמערכות אמיתיות. אין התחייבות לשלמות התוכן, להתאמה למטרה מסוימת, לזמינות רציפה או לשמירת נתונים ללא תקלות.</p><p>במידה המרבית המותרת על פי דין, מפעילי האתר לא יישאו באחריות לנזק עקיף או תוצאתי עקב הסתמכות על התוכן, שימוש שלא למטרות לימוד או אובדן נתונים מקומיים. אין בתנאים אלה כדי לפטור מאחריות שאי אפשר להתנות עליה על פי דין, לרבות אחריות לנזק גוף או למעשה זדון ככל שהדין אוסר את הגבלתה, או כדי לגרוע מזכויות שאינן ניתנות לוויתור.</p><h3>פרטיות ופרופיל מקומי</h3><p>השם, תאריך הלידה, מועד האישור וגרסת התנאים, התאמות הנגישות ונתוני ההתקדמות נשמרים בדפדפן במכשיר הזה. קוד היישום אינו שולח את פרטי הפרופיל או את נתוני ההתקדמות לשרת. שירות האירוח עשוי לעבד נתוני תקשורת טכניים בהתאם לתנאיו.</p><p>אין סנכרון בין מכשירים. מי שניגש לדפדפן הזה עלול לצפות בפרופיל ובהתקדמות. ניקוי נתוני האתר או שימוש בגלישה פרטית עשויים למחוק את השמירה. ניתן למחוק את הפרטים באמצעות מחיקת נתוני האתר בהגדרות הדפדפן. איפוס התרגילים באתר שומר על הפרופיל ועל ההתקדמות האישית.</p><h3>הסכמה ושימוש אחראי</h3><p>אפשר לעיין בתנאים לפני האישור וגם בהמשך דרך הקישור בתחתית האתר. יש להשתמש באתר באופן תקין, בלי לפגוע בפעולתו או בזכויות אחרים. שינוי מהותי בתנאים עשוי לחייב אישור מחדש. אם הוראה אינה תקפה, יתר ההוראות יחולו ככל שהדין מאפשר זאת.</p>`;
}
function accessibilityControls(prefix) {
  const prefs = personal.preferences;
  return `<div class="accessibility-options"><label for="${prefix}-scale">גודל טקסט <select id="${prefix}-scale" data-preference="textScale">${[100,125,150].map(size=>`<option value="${size}"${prefs.textScale===size?' selected':''}>${size}%</option>`).join('')}</select></label>${[['contrast','ניגודיות מוגברת'],['motion','הפחתת תנועה והנפשות'],['links','הדגשת קישורים']].map(([key,label])=>`<label for="${prefix}-${key}"><input id="${prefix}-${key}" data-preference="${key}" type="checkbox"${prefs[key]?' checked':''}>${label}</label>`).join('')}<button class="btn secondary" data-reset-accessibility type="button">איפוס התאמות נגישות</button></div>`;
}
function applyPreferences() {
  const prefs = personal.preferences;
  document.documentElement.style.setProperty('--text-scale',String(prefs.textScale/100));
  for (const size of [125,150]) document.body.classList.toggle('text-scale-'+size,prefs.textScale===size);
  document.body.classList.remove('large-text');
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
function paintProfileButton() { $('profile-label').textContent = 'הפרופיל שלי'; }
function openProfile() {
  profileRequired = !profileReady(); $('app').inert = profileRequired;
  if (!$('profile-dialog').open) {
    $('profile-name').value = personal.profile?.name ?? ''; $('profile-birth').value = personal.profile?.birth ?? '';
    $('profile-consent').checked = profileReady(); $('profile-error').textContent='';
  }
  $('profile-close').hidden = profileRequired;
  openDialog('profile-dialog');
}
function submitProfile() {
  const name=$('profile-name').value.trim(), birth=$('profile-birth').value, consent=$('profile-consent').checked;
  for (const id of ['profile-name','profile-birth','profile-consent']) $(id).removeAttribute('aria-invalid');
  let invalid, message;
  if(name.length<2){invalid='profile-name';message='יש להזין שם באורך של שתי אותיות לפחות.';}
  else if(!validBirth(birth)){invalid='profile-birth';message='יש להזין תאריך לידה תקין שאינו בעתיד.';}
  else if(!consent){invalid='profile-consent';message='כדי להמשיך יש לאשר את תנאי השימוש ואת השמירה המקומית.';}
  if(invalid){$('profile-error').textContent=message;$(invalid).setAttribute('aria-invalid','true');$(invalid).focus();fitDialogs();return;}
  personal.profile={name,birth,termsVersion,acceptedAt:new Date().toISOString()};savePersonal();
  profileRequired=false;$('app').inert=false;$('profile-dialog').close();paintProfileButton();renderProgress();resizeFrame();
}
function stepTopics(q,step) {
  const power = /^P/.test(step.key) || (q.kind==='ohm' && /P/.test(step.formula));
  return q.kind==='ohm' ? [power?'power':'ohm'] : [q.kind,...(power?['power']:[])];
}
function trackedStep() {
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
  const rows=Object.entries(topicNames).map(([key,name])=>{
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
  $('profile-birth').max=localDateValue();
  $('accessibility-controls').innerHTML=accessibilityControls('access');
  $('profile-accessibility-controls').innerHTML=accessibilityControls('entry');
  applyPreferences();paintProfileButton();renderProgress();showStorageNotice();
  if(!profileReady())openProfile();
}
try { const saved = JSON.parse(localStorage.getItem(recentKey)); if (Array.isArray(saved)) previous = saved.filter(s => typeof s === 'string').slice(-280); } catch {}
function saveCourse() {
  if(!questions||courseSeed===null)return;
  const states=Object.fromEntries(DC.kinds.map(kind=>[kind,questions[kind].map(list=>list.map(q=>({
    cursor:q.cursor,draft:q.draft,accepted:q.accepted===true,attempts:q.attempts,help:q.help,hint:q.hint,solution:q.solution,
    simVoltage:q.simVoltage,simAnimate:q.simAnimate,manualWork:q.manualWork,personalSteps:q.personalSteps
  })))]));
  try{localStorage.setItem(courseKey,JSON.stringify({version:1,seed:courseSeed,generationPrevious:coursePrevious,states,tab,levels,positions,feedback,feedbackType}));}
  catch{storageAvailable=false;showStorageNotice();}
}
function restoreManualWork(raw,q) {
  const work={},text=value=>typeof value==='string'?value.slice(0,24):'';
  if(!raw||typeof raw!=='object')return work;
  for(let index=0;index<=q.steps.length;index++) {
    const item=raw[index];if(!item||typeof item!=='object')continue;
    const drafts={};
    for(const definition of triangleDefinitions) {
      const draft=item.drafts?.[definition.id];if(!draft||typeof draft!=='object')continue;
      drafts[definition.id]={answer:text(draft.answer),values:Object.fromEntries(definition.slots.map(slot=>[slot.key,text(draft.values?.[slot.key])]))};
    }
    work[index]={list:Object.fromEntries(['U','R','I','P'].map(key=>[key,text(item.list?.[key])])),
      selected:triangleDefinitions.some(def=>def.id===item.selected)?item.selected:'',drafts,
      message:typeof item.message==='string'?item.message.slice(0,1000):'',type:item.type==='success'?'success':'error',
      errors:Array.isArray(item.errors)?item.errors.filter(value=>typeof value==='string').slice(0,5):[],
      listStatus:typeof item.listStatus==='string'?item.listStatus.slice(0,500):''};
  }
  return work;
}
function restoreCourse() {
  try {
    const saved=JSON.parse(localStorage.getItem(courseKey)||'null');
    if(!saved||saved.version!==1||!Number.isSafeInteger(saved.seed)||!Array.isArray(saved.generationPrevious))return false;
    const prior=saved.generationPrevious.filter(value=>typeof value==='string').slice(-280);
    const restored=DC.course(saved.seed,prior),restoredLevels={},restoredPositions={};
    for(const kind of DC.kinds) {
      const stateLevels=saved.states?.[kind];
      if(!Array.isArray(stateLevels)||stateLevels.length!==restored[kind].length)return false;
      const level=saved.levels?.[kind];
      if(!Number.isInteger(level)||level<0||level>=restored[kind].length)return false;
      restoredLevels[kind]=level;restoredPositions[kind]=[];
      for(let j=0;j<restored[kind].length;j++) {
        const list=restored[kind][j],states=stateLevels[j],position=saved.positions?.[kind]?.[j];
        if(!Array.isArray(states)||states.length!==list.length||!Number.isInteger(position)||position<0||position>=list.length)return false;
        restoredPositions[kind].push(position);
        for(let i=0;i<list.length;i++) {
          const q=list[i],state=states[i];
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
    feedback=typeof saved.feedback==='string'?saved.feedback.slice(0,1000):'';feedbackType=saved.feedbackType==='error'?'error':'success';
    render();return true;
  }catch{return false;}
}
function newCourse() {
  const seed = window.crypto?.getRandomValues ? window.crypto.getRandomValues(new Uint32Array(1))[0] : (Date.now() ^ Math.floor(Math.random() * 4294967296));
  courseSeed=seed;coursePrevious=previous.slice();
  questions = DC.course(seed, coursePrevious);
  viewTab=tab;
  simulatorQuestion = null;
  positions = { ohm:[0,0], series:[0,0], parallel:[0,0,0] };
  for (const kind of DC.kinds) for (const level of questions[kind]) for (const q of level) {
    q.cursor = 0; q.draft = ''; q.accepted = false; q.attempts = 0; q.help = {}; q.hint = false; q.solution = false; q.simVoltage = q.voltage; q.simAnimate = !personal.preferences.motion;
    previous.push(q.signature);
  }
  previous = previous.slice(-280);
  try { localStorage.setItem(recentKey, JSON.stringify(previous)); } catch {}
  feedback = '';feedbackType='success'; render();
}
function currentQuestion() { return questions[tab][levels[tab]][positions[tab][levels[tab]]]; }
function completed(q) { return q.cursor === q.steps.length; }
function currentStep() { const q = currentQuestion(); return q.steps[q.cursor]; }
function bdi(value) { return `<bdi>${escapeHTML(value)}</bdi>`; }
function mathNotation(formula) {
  const input=String(formula).replace(/\s/g,''),tokens=input.match(/R_T|R_eq|I_total|[A-Za-z]+\d*|\d+(?:\.\d+)?|[²×÷+−*/=()]/g)||[];
  if(tokens.join('')!==input)return bdi(formula);
  let cursor=0;
  const symbol=token=>{
    if(/^\d/.test(token))return `<mn>${token}</mn>`;
    const match=/^([A-Za-z]+)(?:_(T|eq|total)|(\d+))$/.exec(token);
    return match?`<msub><mi>${match[1]}</mi><${match[3]?'mn':'mi'}>${match[2]||match[3]}</${match[3]?'mn':'mi'}></msub>`:`<mi>${escapeHTML(token)}</mi>`;
  };
  function factor(){
    let value,token=tokens[cursor++];
    if(token==='('){value=`<mrow><mo>(</mo>${sum()}<mo>)</mo></mrow>`;if(tokens[cursor++]!==')')throw Error('parenthesis');}
    else if(token&&/^[A-Za-z0-9]/.test(token))value=symbol(token);else throw Error('factor');
    if(tokens[cursor]==='²'){cursor++;value=`<msup>${value}<mn>2</mn></msup>`;}
    return value;
  }
  function product(){let value=factor();while(['×','*','÷','/'].includes(tokens[cursor])){const op=tokens[cursor++],right=factor();value=['÷','/'].includes(op)?`<mfrac>${value}${right}</mfrac>`:`<mrow>${value}<mo>×</mo>${right}</mrow>`;}return value;}
  function sum(){let value=product();while(['+','−'].includes(tokens[cursor])){const op=tokens[cursor++];value=`<mrow>${value}<mo>${op}</mo>${product()}</mrow>`;}return value;}
  try{
    let value=sum();if(tokens[cursor]==='='){cursor++;value=`<mrow>${value}<mo>=</mo>${sum()}</mrow>`;}
    if(cursor!==tokens.length)throw Error('remaining');
    return `<math xmlns="http://www.w3.org/1998/Math/MathML" class="mathml" dir="ltr" aria-label="${escapeHTML(formula)}">${value}</math>`;
  }catch{return bdi(formula);}
}
function trianglePreview(definition) {
  const symbols=definition.slots.map(slot=>slot.symbol);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" role="img" aria-label="משולש ${escapeHTML(definition.title)}: ${symbols[0]} למעלה, ${symbols[1]} ו־${symbols[2]} למטה"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#526f62" stroke-width="3"/><path d="M65 125 L195 125 M130 125 L130 218" fill="none" stroke="#526f62" stroke-width="2"/><g fill="#182e3c" font-family="Arial,sans-serif" font-size="33" font-weight="700" text-anchor="middle" direction="ltr"><text x="130" y="96">${symbols[0]}</text><text x="80" y="183">${symbols[1]}</text><text x="181" y="183">${symbols[2]}</text></g></svg>`;
}
function diagramPreview(q, options = {}) {
  return `<button type="button" class="diagram-preview" data-open-diagram="${options.complete ? 'simulator' : 'exercise'}" aria-label="פתיחת הסכמה להגדלה">${q.custom ? customCircuitSVG(q, options) : circuitSVG(q, options)}<span class="diagram-open-label">הגדלת הסכמה ⤢</span></button>`;
}
function openDiagram(source) {
  diagramZoom = 1;
  $('diagram-dialog').classList.toggle('dark-diagram',source==='simulator');
  const q = source === 'simulator' ? activeSimulatorQuestion() : currentQuestion();
  $('diagram-canvas').innerHTML = (q.custom ? customCircuitSVG : circuitSVG)(q, source === 'simulator' ? { complete:true, voltage:q.simVoltage, animate:q.simAnimate } : {});
  diagramBaseWidth = q.custom && q.resistances.length > 3 ? 240 + q.resistances.length * 210 : 0;
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
  viewTab=next;
  if(DC.kinds.includes(next)){tab=next;feedback='';}
  render();
}
function completedCircuits() {
  return DC.kinds.flatMap(kind=>questions[kind].flatMap((list,level)=>list.flatMap((q,index)=>completed(q)?[{q,id:`${kind}:${level}:${index}`,label:`${names[kind]} · רמה ${letters[level]} · תרגיל ${index+1}`}]:[])));
}
function activeSimulatorQuestion() { return simulatorMode==='custom' ? customSimulator : simulatorQuestion ?? currentQuestion(); }
function formatCustomNumber(value) { return Number(value.toPrecision(6)).toString(); }
function simulatorNumber(q,value) { return q.custom ? formatCustomNumber(value) : DC.fmt(value); }
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
  document.querySelectorAll('[role="tab"][data-tab]').forEach(button=>{const active=button.dataset.tab===viewTab;button.setAttribute('aria-selected',active);button.tabIndex=active?0:-1;});
  $('workspace').hidden=viewTab==='simulator';$('simulator-workspace').hidden=viewTab!=='simulator';
  if(viewTab==='simulator'){renderSimulatorPanel();renderProgress();fitDialogs();resizeFrame();saveCourse();return;}
  $('simulator-workspace').innerHTML='';
  const level = levels[tab], sequence = questions[tab][level], index = positions[tab][level], q = sequence[index], done = completed(q), step = currentStep();
  if(q.accepted){feedbackType='success';feedback=acceptedMessage(q);}
  const doneCount = sequence.filter(completed).length;
  $('workspace').setAttribute('aria-labelledby', 'tab-' + tab);
  const levelButtons = questions[tab].map((list, j) => `<button class="level" data-level="${j}" aria-pressed="${j === level}">רמה ${letters[j]}<small>${j === 0 ? 'מספרים שלמים' : j === 1 ? 'מספרים עשרוניים' : 'שלושה ענפים'} · ${list.filter(completed).length}/5</small></button>`).join('');
  const given = Object.entries(q.givens).map(([key, value]) => `<div class="given"><small>${key === 'U' ? 'מתח המקור' : key === 'I' ? 'זרם נתון' : key === 'P' ? 'הספק נתון' : /^R\d/.test(key) ? `התנגדות ${key}${q.lamps[Number(key.slice(1)) - 1] ? ' · נורה' : ''}` : 'התנגדות נתונה'}</small>${bdi(`${key} = ${DC.fmt(value)} ${units[key[0]]}`)}</div>`).join('');
  const dots = sequence.map((item, j) => `<span class="question-dot ${completed(item) ? 'done' : j === index ? 'current' : ''}" aria-label="תרגיל ${j + 1}: ${completed(item) ? 'הושלם' : j === index ? 'נוכחי' : 'בהמשך'}"></span>`).join('');
  const stepPills = q.steps.map((s, j) => `<span class="step-pill ${j < q.cursor ? 'done' : j === q.cursor ? 'active' : ''}" title="${escapeHTML(s.label)}">${j < q.cursor ? '✓' : j + 1}</span>`).join('');
  const rounding = level === 0 ? 'ברמה הזאת כל התוצאות שלמות. אין צורך להקליד יחידות.' : 'יש לעגל את התשובה לשתי ספרות אחרי הנקודה לכל היותר. אפשר לכתוב נקודה או פסיק.';
  const rows = q.steps.slice(0, q.cursor).map((s, j) => `<div class="completed-row"><span>✓ ${escapeHTML(s.label)}${q.help[j] ? ' · בעזרת פתרון' : ''}</span>${bdi(`${DC.fmt(s.value)} ${s.unit}`)}</div>`).join('');
  const active = done ? `<div class="complete-badge">✓ התרגיל הושלם</div><h2>השלמתם את כל החישובים.</h2><p class="muted">${q.steps.length > 1 ? 'אפשר לעבור על התוצאות ולבדוק איך הן קשורות זו לזו.' : 'הקשר בין הנתונים ברור יותר עם כל תרגיל.'}</p>`
    : `<div class="step-list" aria-label="התקדמות שלבי הפתרון">${stepPills}</div><div class="task-kicker">צעד ${q.cursor + 1} מתוך ${q.steps.length} · ${escapeHTML(contextTitle(q, step))}</div><h2 id="answer-title">${escapeHTML(step.label)}</h2><form id="answer-form" novalidate><label class="small muted" for="answer">מה התוצאה, ביחידות ${bdi(step.unit)}?</label><div class="answer-row"><div class="answer-wrap"><input class="numeric${q.accepted?' answer-correct':q.attempts>0?' answer-incorrect':''}" id="answer" data-answer type="text" inputmode="decimal" autocomplete="off" maxlength="24" value="${escapeHTML(q.draft)}"${q.accepted?' readonly':''} aria-describedby="rounding-text form-feedback"><span class="unit" aria-hidden="true">${bdi(step.unit)}</span></div>${q.accepted?'<button class="btn" type="button" data-next-step>הבא ←</button>':'<button class="btn" type="submit">בדיקת תשובה</button>'}</div></form>`;
  const explain = !done && q.solution ? `<div class="solution"><strong>כך פותרים</strong><div class="math">${escapeHTML(step.formula)}</div><div class="math">${escapeHTML(step.substitution)} = ${DC.fmt(step.value)} ${step.unit}</div><p>${escapeHTML(step.explanation)} הקלידו את התוצאה כדי להמשיך לצעד הבא.</p></div>` : '';
  const hints = !done && q.hint ? `<div class="hint"><strong>כיוון לפתרון</strong>${escapeHTML(step.hint)}<div class="math" style="margin-top:8px">${escapeHTML(step.formula)}</div></div>` : '';
  const tools = `<div class="answer-tools"><button class="btn secondary tiny" data-open-formulas>דף נוסחאות △</button><button class="btn secondary tiny" data-open-calculator${q.accepted?' disabled':''}>מחשבון</button>${!done&&!q.accepted ? '<button class="btn soft tiny" data-hint>רמז</button><button class="text-btn small" data-solution>פתרון מוסבר</button>' : ''}</div>`;
  const next = done ? `<div class="completion-actions">${index < 4 ? '<button class="btn" data-next-question>לתרגיל הבא ←</button>' : level < questions[tab].length - 1 ? '<button class="btn" data-next-level>לרמה הבאה ←</button>' : '<button class="btn" data-new-course>סבב חדש</button>'}</div>${doneCount === 5 ? `<div class="level-note">השלמתם את חמשת התרגילים ברמה ${letters[level]}. ${level < questions[tab].length - 1 ? 'אפשר להתקדם לרמה הבאה.' : 'אפשר לעבור ללשונית אחרת או להתחיל סבב חדש.'}</div>` : ''}` : '';
  const descriptions = { ohm:'מתחילים בנתונים ידועים ומוצאים את הערך החסר.', series:'בטור הזרם זהה בכל הרכיבים. המתח מתחלק ביניהם.', parallel:level === 0 ? 'שני נגדים זהים במקביל. בכל ענף אותו מתח.' : level === 1 ? 'שני נגדים שונים במקביל. הזרמים תלויים בהתנגדויות.' : 'שלושה ענפים במקביל: נגדים זהים ושונים.' };
  $('workspace').innerHTML = `<div class="course-head"><div><h2>${names[tab]}</h2><p class="muted small" style="margin:0">${descriptions[tab]}</p></div><div class="levels" aria-label="רמות תרגול">${levelButtons}</div></div><div class="progress-row"><span>תרגיל ${index + 1} מתוך 5 · רמה ${letters[level]}</span><div class="question-dots">${dots}</div></div><div class="progress-track" role="progressbar" aria-label="תרגילים שהושלמו ברמה" aria-valuemin="0" aria-valuemax="5" aria-valuenow="${doneCount}"><div style="width:${doneCount * 20}%"></div></div><div class="exercise-grid"><section class="card"><div class="exercise-title"><div class="eyebrow">הנתונים שלכם</div><h3 style="margin-top:6px">${q.title}</h3><p class="muted small" style="margin:0">${tab === 'ohm' ? 'המקור הוא מקור מתח ישר (DC). מצאו את הנעלם המבוקש.' : 'כל ההתנגדויות ומתח המקור נתונים. פתרו לפי הסדר.'}</p></div><div class="givens">${given}</div><figure class="diagram">${diagramPreview(q)}<figcaption>${q.lamps.some(Boolean) ? 'סימון עיגול עם X הוא נורה. בתרגול הנורה היא רכיב בעל התנגדות קבועה.' : 'מלבן הוא נגד. המקור הוא DC; U מציין מתח ו־I מציין זרם.'}${tab !== 'ohm' ? ' לאחר השלמת המעגל אפשר לפתוח אותו בלשונית הסימולטור. לחצו על הסכמה להגדלה.' : ''}</figcaption></figure>${done ? '<button class="btn sim-jump" data-go-simulator>סימולטור</button>' : ''}</section><section class="card ${done ? 'success-summary' : ''}">${active}<p id="rounding-text" class="rounding">${rounding}</p>${tools}<div class="feedback ${feedbackType}" id="form-feedback" role="status" aria-live="polite">${escapeHTML(feedback)}</div>${hints}${explain}${q.cursor ? `<div class="completed-steps"><strong class="small">החישובים שהשלמתם</strong>${rows}</div>` : ''}${next}</section></div>`;
  if ($('formula-dialog').open) renderFormulas();
  if (focus && !done) requestAnimationFrame(() => ($('formula-dialog').open ? formulaAnswerField() : q.accepted ? $('workspace').querySelector('[data-next-step]') : $('answer'))?.focus());
  renderProgress(); fitDialogs(); resizeFrame();saveCourse();
}
function acceptedMessage(q = currentQuestion()) {
  const step=q.steps[q.cursor];
  return `נכון. ${DC.fmt(step.value)} ${step.unit}. לחצו על הבא כדי להמשיך.`;
}
function nextStep() {
  const q=currentQuestion();
  if(!q.accepted)return;
  q.cursor++;q.accepted=false;q.draft='';q.attempts=0;q.hint=false;q.solution=false;
  feedback='';feedbackType='success';render(true);
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
  if(currentQuestion().accepted)return;
  currentQuestion().draft = value;
  document.querySelectorAll('[data-answer]').forEach(field => { if (field !== source) field.value = value; field.removeAttribute('aria-invalid');field.classList.remove('answer-incorrect'); });
  saveCourse();
}
function simulatorHTML(q) {
  return `<section class="card simulator${q.custom?' custom-simulator':''}" id="simulator-section" aria-labelledby="sim-title"><div class="sim-head"><div><div class="eyebrow">אחרי החישוב — רואים את המעגל</div><h2 id="sim-title" tabindex="-1" style="margin:5px 0">סימולטור DC</h2></div><button class="btn secondary tiny" data-open-formulas>דף נוסחאות △</button></div><div class="sim-layout"><div><figure class="diagram" id="sim-diagram">${diagramPreview(q, { complete:true, voltage:q.simVoltage, animate:q.simAnimate })}</figure>${q.custom&&q.resistances.length>3?'<p class="small muted">אפשר לגלול את הסכמה לצדדים או לפתוח אותה בהגדלה.</p>':''}<div class="sim-legend"><span class="current">→ I — זרם</span><span class="voltage">ΔU — מפל מתח</span><span>רכיבים ונתונים נוספים — לבן</span></div><div id="sim-metrics">${simMetrics(q)}</div></div><div class="sim-controls"><label for="sim-voltage">שינוי מתח המקור</label><div class="sim-value" id="sim-voltage-label">${bdi(`${simulatorNumber(q,q.simVoltage)} V`)}</div><input id="sim-voltage" type="range" min="0" max="${simulatorNumber(q,q.voltage * 2)}" step="0.1" value="${q.simVoltage}" aria-describedby="sim-note"><label class="toggle"><input id="sim-animation" type="checkbox" ${personal.preferences.motion ? 'disabled' : ''} ${q.simAnimate ? 'checked' : ''}>הנפשת מסלול הזרם</label><button class="btn secondary tiny" data-reset-simulator>חזרה למתח התרגיל</button><p class="small muted" id="sim-note" style="margin:6px 0 0">החצים מציגים זרם מוסכם: מהפלוס אל המינוס דרך המעגל החיצוני. הבהירות ממחישה את ההספק בנורה בעלת התנגדות קבועה. שינוי המתח כאן אינו משנה את תשובות התרגיל.</p></div></div></section>`;
}
function simMetrics(q) {
  const m = DC.physics(q.kind, q.simVoltage, q.resistances);
  return `<div class="metrics"><div class="metric"><small>נגד שקול</small>${bdi(`${simulatorNumber(q,m.req)} Ω`)}</div><div class="metric"><small>זרם כולל</small>${bdi(`${simulatorNumber(q,m.total)} A`)}</div><div class="metric"><small>הספק כולל</small>${bdi(`${simulatorNumber(q,m.power)} W`)}</div></div><div class="table-scroll"><table><caption class="small muted" style="text-align:right;margin-bottom:5px">נתוני המעגל במתח שנבחר בסימולטור</caption><thead><tr><th>רכיב</th><th>התנגדות</th><th>מתח</th><th>זרם</th><th>הספק</th></tr></thead><tbody>${q.resistances.map((r,j) => `<tr><td data-label="רכיב">${bdi('R' + (j+1))}${q.lamps[j] ? ' · נורה' : ''}</td><td data-label="התנגדות">${bdi(`${simulatorNumber(q,r)} Ω`)}</td><td data-label="מתח">${bdi(`${simulatorNumber(q,m.drops[j])} V`)}</td><td data-label="זרם">${bdi(`${simulatorNumber(q,m.currents[j])} A`)}</td><td data-label="הספק">${bdi(`${simulatorNumber(q,m.powers[j])} W`)}</td></tr>`).join('')}</tbody></table></div>`;
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
function manualState() {
  const q = currentQuestion();
  q.manualWork ??= {};
  return q.manualWork[q.cursor] ??= { list:{U:'',R:'',I:'',P:''}, selected:'', drafts:{}, message:'', type:'error', errors:[], listStatus:'' };
}
function manualDraft(state = manualState()) {
  return state.drafts[state.selected] ??= { values:{}, answer:'' };
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
  $('manual-keypad-value').textContent=key+' = '+(input.value||'…');
}
function showManualKeypad(input) {
  if(input.disabled||currentQuestion().accepted)return hideManualKeypad();
  manualKeypadTarget=input;manualKeypadFieldId=input.id;
  $('manual-keypad').hidden=false;paintManualKeypad();
  requestAnimationFrame(()=>{fitDialogs();if(!$('manual-keypad').hidden)$('manual-keypad').scrollIntoView({block:'nearest'});});
}
function writeKeypadValue(input,value,position) {
  const state=manualState();
  if(input.hasAttribute('data-manual-list'))state.list[input.dataset.manualList]=value;
  else {
    manualDraft(state).values[input.dataset.manualSlot]=value;
    state.message='';state.errors=[];$('manual-message').textContent='';
  }
  input.value=value;
  if(input.hasAttribute('data-manual-list'))syncManualEntryOrder();
  if(manualTokenKind(value)==='invalid')input.setAttribute('aria-invalid','true');
  else input.removeAttribute('aria-invalid');
  try{input.setSelectionRange(position,position);}catch{}
  saveCourse();paintManualKeypad();
}
function pressManualKey(key) {
  const input=keypadInput();
  if(key==='done'){hideManualKeypad();$('formula-tab-manual').focus({preventScroll:true});return;}
  if(!input)return hideManualKeypad();
  if(key==='enter') {
    if(manualTokenKind(input.value)==='invalid'){input.setAttribute('aria-invalid','true');return;}
    saveCourse();
    const fields=[...document.querySelectorAll(input.hasAttribute('data-manual-list')?'[data-manual-list]':'[data-manual-slot]')];
    const next=fields[fields.indexOf(input)+1]??(input.hasAttribute('data-manual-list')?document.querySelector('[data-manual-slot]'):$('manual-answer'));
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
  if(event.target.matches('[data-manual-list],[data-manual-slot]'))showManualKeypad(event.target);
  else if(event.target.matches('input,select,textarea'))hideManualKeypad();
});
document.addEventListener('beforeinput',event=>{
  const input=event.target;
  if(!input.matches('[data-manual-list],[data-manual-slot]')||event.inputType!=='insertText')return;
  if(/^[xX?]$/.test(event.data??'')){event.preventDefault();input.value=event.data.toUpperCase();input.dispatchEvent(new Event('input',{bubbles:true}));return;}
  if(/^[0-9.,]$/.test(event.data??'')&&/^[xX?]$/.test(input.value))input.value='';
});
function manualTokenKind(value) {
  const text = String(value).trim();
  if (!text) return 'blank';
  if (text === '?') return 'unknown';
  if (text.toLowerCase() === 'x') return 'unused';
  return /^(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(text) && Number.isFinite(Number(text.replace(',', '.'))) ? 'number' : 'invalid';
}
function formulaAnswerField() {
  if(currentQuestion().accepted)return $('formula-body').querySelector('[data-next-step]');
  return formulaView === 'manual' ? $('manual-answer') : $('formula-body').querySelector('[data-answer]');
}
function manualEntrySlots(definition, state = manualState(), context = triangleContext()) {
  const order=['U','R','I','P'];
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
  const next=currentQuestion().accepted?$('formula-body').querySelector('[data-next-step]'):document.querySelector('[data-manual-slot]');
  next?.focus({preventScroll:true});
}
function manualSolverHTML() {
  const context = triangleContext(), state = manualState();
  const definition = triangleDefinitions.find(item => item.id === state.selected);
  const choices = triangleDefinitions.map(item => `<button type="button" class="manual-choice" data-manual-triangle="${item.id}" aria-pressed="${item.id === state.selected}"${context.q.accepted?' disabled':''}><strong>${item.title}</strong>${trianglePreview(item)}${mathNotation(item.formulas[0])}</button>`).join('');
  const list = ['U','R','I','P'].map(key => `<label class="manual-list-row" for="manual-list-${key}"><bdi>${key} =</bdi><input id="manual-list-${key}" data-manual-list="${key}" type="text" inputmode="none" lang="en" maxlength="24" aria-controls="manual-keypad"${window.matchMedia('(pointer:coarse)').matches ? ' readonly' : ''}${context.q.accepted?' disabled':''} autocomplete="off" autocapitalize="off" spellcheck="false" value="${escapeHTML(state.list[key])}" aria-label="${key} ברשימת הנתונים" aria-describedby="manual-token-help"${manualTokenKind(state.list[key]) === 'invalid' ? ' aria-invalid="true"' : ''}></label>`).join('');
  const message = context.q.accepted?acceptedMessage(context.q):state.message || (feedbackType === 'success' ? feedback : '');
  const status = `<div id="manual-message" class="feedback ${context.q.accepted?'success':state.message ? state.type : feedbackType}" role="status" aria-live="polite">${escapeHTML(message)}</div>`;
  let work = context.q.accepted?`<div class="manual-form">${status}<button class="btn" type="button" data-next-step>הבא ←</button></div>`:`<div><div class="manual-placeholder">בחרו משולש מהרשימה כדי להציב בו נתונים.</div>${status}</div>`;
  if (definition) {
    const draft = manualDraft(state), locations = ['top','left','right'];
    const geometry = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" preserveAspectRatio="none" aria-hidden="true"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#78958a" stroke-width="2.5"/><path d="M65 125 L195 125 M130 125 L130 218" stroke="#78958a" stroke-width="2"/></svg>';
    const fields = manualEntrySlots(definition,state,context).map(slot => `<label class="triangle-slot ${locations[definition.slots.indexOf(slot)]}" for="manual-slot-${slot.key}"><strong>${slot.symbol}</strong><input id="manual-slot-${slot.key}" data-manual-slot="${slot.key}" type="text" inputmode="none" lang="en" maxlength="24" aria-controls="manual-keypad"${window.matchMedia('(pointer:coarse)').matches ? ' readonly' : ''}${context.q.accepted?' disabled':''} autocomplete="off" autocapitalize="off" spellcheck="false" value="${escapeHTML(draft.values[slot.key] ?? '')}" aria-label="הצבת ${slot.symbol} במשולש" aria-describedby="manual-instructions"${state.errors.includes(slot.key) ? ' aria-invalid="true"' : ''}></label>`).join('');
    work = `<form id="manual-form" class="manual-form" novalidate><h3>${definition.title}</h3><div class="triangle manual-triangle">${geometry}${fields}</div><div class="manual-answer"><label for="manual-answer">התשובה שחישבתם${context.task ? ` (${bdi(context.task.unit)})` : ''}</label><input id="manual-answer" type="text" class="numeric${context.q.accepted?' answer-correct':state.errors.includes('answer')?' answer-incorrect':''}" inputmode="decimal" maxlength="24" autocomplete="off" value="${escapeHTML(context.q.accepted?context.q.draft:draft.answer)}"${context.q.accepted?' readonly':''}${state.errors.includes('answer') ? ' aria-invalid="true"' : ''}>${status}${context.q.accepted?'<button class="btn" type="button" data-next-step>הבא ←</button>':`<button class="btn" type="submit"${context.task ? '' : ' disabled'}>בדיקת ההצבה והתשובה</button>`}<button class="btn secondary tiny" type="button" data-open-calculator${context.q.accepted?' disabled':''}>מחשבון</button></div></form>`;
  }
  const notice = !context.task ? '<p class="complete-badge">התרגיל הושלם. אפשר לחזור לתרגול ולהמשיך לתרגיל הבא.</p>' : context.target === 'Req' ? '<p class="hint">בצעד הזה מחשבים התנגדות שקולה בעזרת נוסחת טור או מקביל. משולשי חוק אום וההספק מתאימים לצעדים הבאים. <button class="text-btn" data-formula-tab="reference">חזרה לנוסחאות</button></p>' : '';
  return `<div class="manual-intro"><h3>פתירה בעזרת המשולש</h3><p class="small muted">${escapeHTML(context.label)}${context.task ? ` · מחשבים: ${escapeHTML(context.task.label)}` : ''}</p><p id="manual-instructions" class="small">בחרו משולש, הציבו בעצמכם את הנתונים הידועים וסמנו ${bdi('?')} במקום הנעלם. המעבר בשדות מתחיל בנתונים המספריים לפי סדר רשימת הנתונים. חשבו והקלידו את התשובה מתחת למשולש; בדיקה תעביר אותה לתרגיל ותציג נכון או לא נכון. לאחר תשובה נכונה לחצו על הבא.</p></div>${notice}<strong class="small" id="manual-choice-title">בחרו את המשולש המתאים</strong><div class="manual-choices" role="group" aria-labelledby="manual-choice-title">${choices}</div><div class="manual-workspace"><aside class="manual-list" aria-labelledby="manual-list-title"><p class="manual-paper-note">מומלץ לרשום את הנתונים בדף.</p><button class="btn manual-fill" type="button" data-manual-list-help${context.q.accepted?' disabled':''}>מילוי מתרגיל</button><h3 id="manual-list-title">רשימת נתונים<br><span class="muted">רשות</span></h3>${list}</aside>${work}</div><p id="manual-token-help" class="small muted manual-note">הרשימה היא כלי עזר ואפשר להשאיר אותה ריקה. ${bdi('?')} = הנעלם שמחפשים; ${bdi('X')} = ערך שלא ידוע ולא התבקש לחשב. אפשר להקליד מספרים, כולל עשרוניים. כפתור מילוי מתרגיל ממלא רק את הרשימה; את ההצבה והחישוב עושים בעצמכם.</p><p id="manual-list-status" class="small muted manual-status" role="status" aria-live="polite">${escapeHTML(state.listStatus)}</p>${definition?.note ? `<p class="small muted">${escapeHTML(definition.note)}</p>` : ''}`;
}
function fillManualList() {
  if(currentQuestion().accepted)return;
  markHelp();
  const context = triangleContext(), state = manualState();
  const target = context.target === 'Req' ? 'R' : context.target;
  for (const key of ['U','R','I','P']) {
    state.list[key] = key === target ? '?' : context.values[key] !== undefined ? DC.fmt(context.values[key]) : 'X';
    const input = $('manual-list-' + key);
    if (input) { input.value = state.list[key]; input.removeAttribute('aria-invalid'); }
  }
  state.listStatus = 'הרשימה מולאה. את הנתונים במשולש מציבים בעצמכם.';
  $('manual-list-status').textContent = state.listStatus;
  syncManualEntryOrder();fitDialogs();saveCourse();
}
function manualFeedback(message, errors = []) {
  if(currentQuestion().accepted)return;
  recordAttempt(false,'manual');
  currentQuestion().attempts++;
  const state = manualState(); state.message = 'לא נכון. '+message; state.type = 'error'; state.errors = errors;
  feedback=state.message;feedbackType='error';
  const notice = $('manual-message');
  notice.className = 'feedback error'; notice.textContent = state.message;
  $('form-feedback').className='feedback error';$('form-feedback').textContent=state.message;
  document.querySelectorAll('[data-answer]').forEach(input=>{input.classList.add('answer-incorrect');input.setAttribute('aria-invalid','true');});
  $('manual-form')?.querySelectorAll('input').forEach(input => {
    const invalid = errors.includes(input.dataset.manualSlot ?? 'answer');
    if (invalid) input.setAttribute('aria-invalid','true'); else input.removeAttribute('aria-invalid');
    if(input.id==='manual-answer')input.classList.toggle('answer-incorrect',invalid);
  });
  fitDialogs();saveCourse();
}
function checkManualAnswer() {
  const context = triangleContext(), state = manualState();
  const definition = triangleDefinitions.find(item => item.id === state.selected);
  if (!context.task || !definition || context.q.accepted) return;
  syncDraft(manualDraft(state).answer);
  if (!definition.slots.some(slot => slot.key === context.target)) {
    return manualFeedback(context.target === 'Req' ? 'בשלב הזה משתמשים בנוסחת התנגדות שקולה. אפשר למצוא אותה בלשונית נוסחאות.' : 'המשולש שבחרתם אינו מתאים לנעלם בצעד הזה. בחרו משולש אחר.');
  }
  const known = definition.slots.filter(slot => slot.key !== context.target);
  if (known.some(slot => context.values[slot.key] === undefined)) return manualFeedback('עדיין אין מספיק נתונים ידועים למשולש הזה. בחרו משולש שאפשר להציב בו שני נתונים ידועים.');
  const draft = manualDraft(state);
  if (String(draft.values[context.target] ?? '').trim() !== '?') return manualFeedback('סמנו ? במקום הנעלם שמבקשים לחשב במשולש.', [context.target]);
  const incorrect = known.filter(slot => !DC.accepted(draft.values[slot.key] ?? '', context.values[slot.key]));
  if (incorrect.length) return manualFeedback('בדקו את הנתונים שהצבתם במשולש. בשני המקומות הידועים צריך להקליד מספרים שמתאימים לנתוני התרגיל. בסימון ריבוע כופלים את הנתון בעצמו.', incorrect.map(slot => slot.key));
  if (!DC.accepted(draft.answer, context.task.value)) return manualFeedback(draft.answer.trim() ? 'ההצבה במשולש נכונה. בדקו שוב את החישוב ואת התשובה שהקלדתם.' : 'ההצבה נכונה. חשבו והקלידו את התשובה בשדה שמתחת למשולש.', ['answer']);
  checkAnswer(draft.answer,'manual');
}
function triangleCard(definition, context = null) {
  const slots = definition.slots;
  const enabled = !!context?.task && slots.some(slot => slot.key === context.target)
    && slots.filter(slot => slot.key !== context.target).every(slot => context.values[slot.key] !== undefined);
  const locations = ['top', 'left', 'right'];
  const geometry = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 225" preserveAspectRatio="none" aria-hidden="true"><path d="M130 10 L15 218 L245 218 Z" fill="#f3f6ee" stroke="#78958a" stroke-width="2.5"/><path d="M65 125 L195 125 M130 125 L130 218" stroke="#78958a" stroke-width="2"/></svg>';
  const inputs = slots.map((slot, j) => `<div class="triangle-slot ${locations[j]}"><strong>${slot.symbol}</strong><small>${slot.unit}</small>${!context ? '' : enabled && slot.key === context.target
    ? `<input class="numeric${context.q.accepted?' answer-correct':context.q.attempts>0?' answer-incorrect':''}" data-answer type="text" inputmode="decimal" maxlength="24" autocomplete="off" value="${escapeHTML(context.q.draft)}"${context.q.accepted?' readonly':''} aria-label="${escapeHTML(context.task.label)} במשולש ${definition.title}">`
    : `<bdi>${context.values[slot.key] !== undefined ? DC.fmt(context.values[slot.key]) : '—'}</bdi>`}</div>`).join('');
  const triangle = `<div class="triangle">${geometry}${inputs}</div>`;
  const content = context ? `<form data-triangle-form novalidate>${triangle}${enabled ? context.q.accepted?'<button class="btn triangle-check tiny" type="button" data-next-step>הבא ←</button>':`<button class="btn triangle-check tiny" type="submit">בדיקת ${escapeHTML(context.task.label)}</button>` : '<p class="triangle-help">המשולש זמין למענה כשהנעלם ושני הנתונים מתאימים לשלב הנוכחי.</p>'}</form>` : triangle;
  return `<section class="formula-card"><h3>${definition.title}</h3>${content}<div class="formula-lines">${definition.formulas.map(mathNotation).join('<br>')}</div>${definition.note ? `<p class="triangle-help">${definition.note}</p>` : ''}</section>`;
}
function renderFormulas() {
  hideManualKeypad();saveCourse();
  const context = formulaView === 'help' ? triangleContext() : null;
  if (context?.task) markHelp();
  document.querySelector('#formula-dialog .formula-intro').hidden = formulaView === 'manual';
  document.querySelectorAll('.formula-tabs [data-formula-tab]').forEach(button => {
    const active = button.dataset.formulaTab === formulaView;
    button.setAttribute('aria-selected', active); button.tabIndex = active ? 0 : -1;
  });
  $('formula-body').setAttribute('aria-labelledby', 'formula-tab-' + formulaView);
  if (formulaView === 'manual') {
    $('formula-body').innerHTML = manualSolverHTML();
    fitDialogs(); resizeFrame(); return;
  }
  const sheetHelp = context?.task && (context.q.hint || context.q.solution) ? `<div class="${context.q.solution ? 'solution' : 'hint'}"><strong>${context.q.solution ? 'כך פותרים' : 'כיוון לפתרון'}</strong><p>${escapeHTML(context.task.hint)}</p><div class="math">${mathNotation(context.task.formula)}</div>${context.q.solution ? `<div class="math">${escapeHTML(context.task.substitution)} = ${DC.fmt(context.task.value)} ${context.task.unit}</div><p>הקלידו את התוצאה בשדה המענה המודגש כדי להמשיך.</p>` : ''}</div>` : '';
  const definitions = triangleDefinitions;
  const alternative = context?.task && context.target === 'Req' ? `<form class="sheet-answer" data-triangle-form novalidate><label for="sheet-answer">${escapeHTML(context.task.label)} — השתמשו בנוסחת טור או מקביל שמופיעה בהמשך</label><div class="answer-row"><input id="sheet-answer" class="numeric${context.q.accepted?' answer-correct':context.q.attempts>0?' answer-incorrect':''}" data-answer inputmode="decimal" type="text" maxlength="24" value="${escapeHTML(context.q.draft)}"${context.q.accepted?' readonly':''} autocomplete="off" aria-label="התנגדות שקולה"><span>${bdi('Ω')}</span>${context.q.accepted?'<button class="btn tiny" type="button" data-next-step>הבא ←</button>':'<button class="btn tiny" type="submit">בדיקת תשובה</button>'}</div></form>` : '';
  const given = context ? Object.entries(context.q.givens).map(([key, value]) => `<div class="given">${bdi(`${key} = ${DC.fmt(value)} ${units[key[0]]}`)}</div>`).join('') : '';
  const exerciseContext = context ? `<div class="formula-context"><strong>${escapeHTML(context.label)}</strong><div>${context.task ? `כעת מחשבים: ${escapeHTML(context.task.label)}. הנתונים במשולשים כוללים רק נתוני השאלה וצעדים שכבר השלמתם.` : 'אפשר לעבור על הנוסחאות ולהמשיך לתרגיל הבא.'}</div><div class="givens sheet-givens" aria-label="נתוני התרגיל">${given}</div><div class="answer-tools" style="margin:8px 0 0"><button class="btn secondary tiny" data-open-calculator>פתיחת המחשבון</button><button class="btn soft tiny" data-close-dialog="formula-dialog">חזרה לתרגול</button></div></div>` : '';
  $('formula-body').innerHTML = `${formulaView === 'reference' ? '<div class="manual-entry"><button class="btn" data-formula-tab="manual">פתירה בעזרת המשולש</button><span class="small muted">בוחרים משולש, מציבים נתונים ופותרים בעצמכם.</span></div>' : ''}${exerciseContext}${context && feedback ? `<div class="feedback sheet-feedback ${feedbackType}" role="status" aria-live="polite">${escapeHTML(feedback)}</div>` : ''}${sheetHelp}${alternative}<div class="formula-grid">${definitions.map(def => triangleCard(def, context)).join('')}</div><div class="units-list"><span>${bdi('U')} — מתח, וולט ${bdi('V')}</span><span>${bdi('I')} — זרם, אמפר ${bdi('A')}</span><span>${bdi('R')} — התנגדות, אוהם ${bdi('Ω')}</span><span>${bdi('P')} — הספק, ואט ${bdi('W')}</span></div><div class="formula-networks"><section class="formula-card"><h3>מעגל טורי</h3><div class="math">${mathNotation('R_T = R1 + R2 + R3')}<br>${mathNotation('I = U ÷ R_T')}<br>${mathNotation('U1 = I × R1')}<br>${mathNotation('U = U1 + U2 + U3')}<br>${mathNotation('P1 = I² × R1')}</div><p class="small muted" style="margin-top:10px">${mathNotation('R_T')} מציין התנגדות שקולה. בשני רכיבים מחברים רק את R1 ואת R2. אותו זרם עובר בכל הרכיבים.</p></section><section class="formula-card"><h3>מעגל מקבילי</h3><div class="math parallel-formulas"><div class="network-formula">${mathNotation('R_T = (R1 × R2) ÷ (R1 + R2)')}</div><div class="network-formula">${mathNotation('R_T = 1 ÷ (1/R1 + 1/R2 + 1/R3)')}</div><div class="network-formula">${mathNotation('R_T = R ÷ n')}</div><div class="network-formula">${mathNotation('I1 = U ÷ R1')}</div><div class="network-formula">${mathNotation('I_total = I1 + I2 + I3')}</div><div class="network-formula">${mathNotation('P1 = U × I1')}</div></div><p class="small muted" style="margin-top:10px">${mathNotation('R_T')} מציין התנגדות שקולה. הנוסחה R/n מתאימה רק לנגדים זהים. n הוא מספר הענפים. בכל הענפים אותו מתח.</p></section></div>`;
  fitDialogs(); resizeFrame();
}

function openDialog(id, { preserveFormulaView = false } = {}) {
  if (!profileReady() && id !== 'profile-dialog') { openProfile(); return; }
  calculatorReturnToFormulas = id === 'calculator-dialog' && $('formula-dialog').open;
  if (id === 'formula-dialog' && !preserveFormulaView) formulaView = 'reference';
  document.querySelectorAll('dialog[open]').forEach(dialog => { if (dialog.id !== id) dialog.close(); });
  if (id === 'formula-dialog') renderFormulas();
  if (!$(id).open) $(id).showModal();
  fitDialogs(); resizeFrame();
}
function sendStreamlitMessage(type, data) { window.parent.postMessage({ isStreamlitMessage:true, type, ...data }, '*'); }
function resizeFrame() {
  requestAnimationFrame(() => sendStreamlitMessage('streamlit:setFrameHeight', { height:Math.ceil($('app').getBoundingClientRect().height + 10) }));
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
  if ($('diagram-dialog').open) $('diagram-viewport').style.maxHeight = Math.max(100, height - 230) + 'px';
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
    $('calc-error').textContent = ''; $('calc-use').disabled = viewTab==='simulator'||!currentStep()||currentQuestion().accepted; calculatorFresh = true;
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
  if(button.dataset.manualKey!==undefined)return pressManualKey(button.dataset.manualKey);
  if (button.hasAttribute('data-open-profile')) return openProfile();
  if (button.hasAttribute('data-show-progress')) return showProgress();
  if (button.hasAttribute('data-open-accessibility')) return openDialog('accessibility-dialog');
  if (button.hasAttribute('data-open-terms')) return openDialog('terms-dialog');
  if (button.hasAttribute('data-reset-accessibility')) {
    personal.preferences=emptyPersonal().preferences;savePersonal();applyPreferences();return;
  }
  if (button.hasAttribute('data-go-simulator')) {
    simulatorMode='exercise';simulatorQuestion=currentQuestion();selectTab('simulator');$('tab-simulator').focus({preventScroll:true});return;
  }
  if (button.hasAttribute('data-open-formulas')) return openDialog('formula-dialog');
  if (button.dataset.openDiagram) return openDiagram(button.dataset.openDiagram);
  if (button.dataset.diagramZoom) return zoomDiagram(button.dataset.diagramZoom);
  if (button.dataset.formulaTab) {
    formulaView = button.dataset.formulaTab; renderFormulas(); $('formula-dialog').scrollTop = 0;
    if(formulaView==='manual')focusManualEntry();return;
  }
  if (button.dataset.manualTriangle) {
    if(currentQuestion().accepted)return;
    const state = manualState(); state.selected = button.dataset.manualTriangle; state.message = ''; state.errors = [];
    renderFormulas();focusManualEntry();return;
  }
  if (button.hasAttribute('data-manual-list-help')) return fillManualList();
  if (button.hasAttribute('data-open-calculator')) {
    $('calc-use').disabled = calculatorValue === null || viewTab==='simulator' || !currentStep() || currentQuestion().accepted;
    openDialog('calculator-dialog'); return;
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
  if (button.dataset.level !== undefined) { levels[tab] = Number(button.dataset.level); feedback = ''; render(); return; }
  const q = currentQuestion();
  if(button.hasAttribute('data-next-step'))return nextStep();
  if (button.hasAttribute('data-hint')) { markHelp(); q.hint = true; render(); return; }
  if (button.hasAttribute('data-solution')) { markHelp(); q.solution = true; q.help[q.cursor] = true; render(); return; }
  if (button.hasAttribute('data-next-question')) { positions[tab][levels[tab]]++; feedback = ''; render(); return; }
  if (button.hasAttribute('data-next-level')) { levels[tab]++; feedback = ''; render(); return; }
  if (button.id === 'new-course' || button.hasAttribute('data-new-course')) return openDialog('new-course-dialog');
  if (button.id === 'new-course-confirm') { $('new-course-dialog').close(); newCourse(); return; }
  if (button.id === 'text-size') {
    personal.preferences.textScale=personal.preferences.textScale===100?125:100;savePersonal();applyPreferences();return;
  }
  if (button.hasAttribute('data-reset-simulator')) { const model=activeSimulatorQuestion();model.simVoltage=model.voltage;updateSimulator();return; }
  if (button.id === 'calc-clear') { clearCalculator(); return; }
  if (button.id === 'calc-use' && calculatorValue !== null) {
    if (calculatorReturnToFormulas && formulaView === 'manual') manualDraft().answer = DC.fmt(calculatorValue);
    else syncDraft(DC.fmt(calculatorValue));
    $('calculator-dialog').close();
    if (!calculatorReturnToFormulas) $('answer')?.focus();
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
  if (event.target.id === 'profile-form') { event.preventDefault(); submitProfile(); return; }
  if (event.target.id === 'manual-form') { event.preventDefault(); checkManualAnswer(); return; }
  if (event.target.id !== 'answer-form' && !event.target.hasAttribute('data-triangle-form')) return;
  event.preventDefault();
  checkAnswer(event.target.querySelector('[data-answer]')?.value ?? currentQuestion().draft);
});
document.addEventListener('input', event => {
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
  if (event.target.hasAttribute('data-manual-slot') || event.target.id === 'manual-answer') {
    const state = manualState(), draft = manualDraft(state);
    if (event.target.id === 'manual-answer') draft.answer = event.target.value;
    else draft.values[event.target.dataset.manualSlot] = event.target.value;
    state.message = ''; state.errors = []; event.target.removeAttribute('aria-invalid');event.target.classList.remove('answer-incorrect');
    $('manual-message').textContent = '';
    if(manualKeypadTarget===event.target)paintManualKeypad();
    saveCourse();
  }
  if (event.target.hasAttribute('data-answer')) syncDraft(event.target.value, event.target);
  if (event.target.id === 'sim-voltage') { activeSimulatorQuestion().simVoltage = Number(event.target.value); updateSimulator(); }
  if (event.target.id === 'calc-screen') { calculatorValue = null; calculatorFresh = false; $('calc-use').disabled = true; $('calc-result').textContent = ''; }
});
document.addEventListener('change', event => {
  if(event.target.id==='custom-kind'){customDraft.kind=event.target.value;renderSimulatorPanel();$('custom-kind').focus({preventScroll:true});return;}
  if(event.target.id==='sim-circuit'){simulatorQuestion=completedCircuits().find(item=>item.id===event.target.value)?.q??null;renderSimulatorPanel();$('sim-circuit')?.focus({preventScroll:true});resizeFrame();return;}
  if(event.target.hasAttribute('data-preference')){
    const key=event.target.dataset.preference;
    personal.preferences[key]=event.target.type==='checkbox'?event.target.checked:Number(event.target.value);
    savePersonal();applyPreferences();return;
  }
  if (event.target.id === 'sim-animation') { activeSimulatorQuestion().simAnimate = event.target.checked; updateSimulator(); }
});
document.addEventListener('keydown', event => {
  if(event.key==='Escape'&&manualKeypadTarget){event.preventDefault();hideManualKeypad();$('formula-tab-manual').focus({preventScroll:true});return;}
  if(event.key==='Enter'&&event.target.matches('[data-manual-list],[data-manual-slot]')){event.preventDefault();pressManualKey('enter');return;}
  if(event.target.matches('[data-manual-list],[data-manual-slot]')&&!event.ctrlKey&&!event.metaKey&&event.key.length===1&&!/[0-9.,xX?]/.test(event.key)){event.preventDefault();return;}
  if (event.target.id === 'calc-screen' && event.key === 'Enter') { event.preventDefault(); calculateScreen(); return; }
  const formulaTab = event.target.closest('.formula-tab[data-formula-tab]');
  if (formulaTab && ['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) {
    event.preventDefault();
    const views = ['reference','help','manual'], index = views.indexOf(formulaView);
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
    if(dialog.id==='profile-dialog'&&profileRequired){requestAnimationFrame(openProfile);return;}
    if (dialog.id === 'calculator-dialog' && calculatorReturnToFormulas) {
      calculatorReturnToFormulas = false;
      openDialog('formula-dialog', { preserveFormulaView:true });
      formulaAnswerField()?.focus();
    }
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    if(dialog.id==='profile-dialog'&&profileRequired)return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  });
});
window.addEventListener('resize', () => { fitDialogs(); resizeFrame(); });
window.visualViewport?.addEventListener('resize', fitDialogs);
try { if (window.parent !== window) { window.parent.addEventListener('scroll', fitDialogs, true); window.parent.addEventListener('resize', fitDialogs); } } catch {}
sendStreamlitMessage('streamlit:componentReady', { apiVersion:1 });
if(!restoreCourse())newCourse();
initializePersonal();
function finishInitialLayout(){
  applyPreferences();resizeFrame();
  requestAnimationFrame(()=>requestAnimationFrame(()=>{applyPreferences();document.documentElement.classList.add('ui-ready');}));
}
if(document.fonts?.ready)document.fonts.ready.then(finishInitialLayout);else finishInitialLayout();
window.addEventListener('pagehide',saveCourse);
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

// This is a render-only regression: inert mock HTML, JS disabled and network blocked.
// Live-site interactions and authentication are never performed by this test.
const assert=require('node:assert/strict'),{webkit}=require('playwright');
const fixtures=require('./layout-fixture.cjs');
(async()=>{
 const frames=await fixtures(),browser=await webkit.launch();let checks=0;
 try{
  const profiles=[{width:390,scale:1,dark:false,all:true},...[320,375,430,768,1024].flatMap(width=>[{width,scale:1,dark:false},{width,scale:1.5,dark:true}])];
  for(const profile of profiles){
   const context=await browser.newContext({viewport:{width:profile.width,height:844},javaScriptEnabled:false,offline:true});
   await context.route('**/*',route=>route.abort());const page=await context.newPage();
   // Every generated circuit is checked at phone width; each layout variant is
   // also checked at narrow, tablet and desktop widths with enlarged dark text.
   const selected=profile.all?frames:frames.filter(f=>/ohm|closed|sim|walkthrough|solution-0-[0269]$|mixed-0-[0269]$|battery-0-[0269]$/.test(f.name));
   for(const frame of selected){
    const style=`<style>:root{--text-scale:${profile.scale}!important}</style>`;
    const html=frame.html.replace('</head>',style+'</head>').replace('<html ',`<html data-render-test="true" `).replace('class="ui-ready',`class="ui-ready${profile.dark?' dark-mode':''}${profile.scale===1.5?' text-scale-150':''}`);
    await page.setContent(html);await page.evaluate(()=>document.fonts.ready);
    const result=await page.evaluate(()=>{
     const width=document.documentElement.clientWidth;
     function locallyClipped(node){
      for(let p=node.parentElement;p&&p!==document.body&&p.id!=='app';p=p.parentElement)if(['auto','scroll','hidden','clip'].includes(getComputedStyle(p).overflowX))return true;
      return false;
     }
     const outside=[...document.querySelectorAll('#qa-panel, #course-panel, .qa-banner, .qa-navigation, .exercise-grid, .card, .tab, button, select, input, .course-panel .mathml')].filter(n=>{
      if(!n.checkVisibility({visibilityProperty:true,contentVisibilityAuto:true})||n.closest('dialog:not([open])')||locallyClipped(n))return false;
      const r=n.getBoundingClientRect();return r.width>0&&(r.left< -1||r.right>width+1);
     }).map(n=>({node:n.tagName+'#'+n.id+'.'+n.getAttribute('class'),left:n.getBoundingClientRect().left,right:n.getBoundingClientRect().right}));
     const navigation=[...document.querySelectorAll('.qa-navigation select')].map(n=>({width:n.getBoundingClientRect().width,height:n.getBoundingClientRect().height}));
     const labelIssues=[];
     for(const label of document.querySelectorAll('.sim-current-label')){
      if(!label.checkVisibility({visibilityProperty:true,contentVisibilityAuto:true}))continue;
      const b=label.getBBox(),v=label.ownerSVGElement.viewBox.baseVal,arrow=label.closest('.sim-component')?.querySelector('.sim-current .sim-arrow');
      if(b.x<0||b.y<0||b.x+b.width>v.width||b.y+b.height>v.height)labelIssues.push(label.textContent+' clipped by diagram');
      if(arrow&&b.y+b.height>arrow.getBBox().y-5)labelIssues.push(label.textContent+' needs more space above arrow');
      if(arrow){const a=arrow.getBBox();if(a.height>a.width){if(b.x+b.width>a.x-12)labelIssues.push(label.textContent+' too close to vertical arrow horizontally');if(b.y+b.height>a.y-22)labelIssues.push(label.textContent+' too close to vertical arrow vertically');}}
     }
     return {visible:getComputedStyle(document.body).visibility,scale:getComputedStyle(document.documentElement).getPropertyValue('--text-scale'),dark:document.documentElement.classList.contains('dark-mode'),width,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth,outside,navigation,labelIssues};
    });
    const label=frame.name+' '+JSON.stringify(profile);assert.equal(result.visible,'visible',label);assert.equal(Number(result.scale),profile.scale,label);assert.equal(result.dark,profile.dark,label);assert.equal(result.width,profile.width,label);
    assert.ok(result.scroll<=profile.width+1&&result.body<=profile.width+1,label+' document overflow '+JSON.stringify(result));
    assert.deepEqual(result.outside,[],label+' inaccessible content');assert.equal(result.navigation.length,2,label);
    assert.deepEqual(result.labelIssues,[],label+' readable current labels');
    assert.ok(result.navigation.every(n=>n.width>100&&n.height>=44),label+' usable selectors');checks++;
   }
   await context.close();
  }
  console.log(`WebKit layout: ${checks} render checks passed; all generated mixed/battery questions, solutions, QA open/closed, simulator, 320–1024px and 150% dark text; no page overflow or inaccessible controls`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

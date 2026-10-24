const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const source=fs.readFileSync('Electricity-circuit.py','utf8').match(/<script>\s*(\/\/ Jerusalem Shabbat schedule[\s\S]*?)\n  <\/script>/)[1];
const bundled=JSON.parse(fs.readFileSync('data/shabbat_jerusalem.json','utf8')).intervals;
async function scenario(now,intervals,expected,unknown){
 const dom=new JSDOM('<div id="app"><button>תרגול</button></div>',{url:'https://fresh-offline.test/',runScripts:'outside-only'}),w=dom.window;
 w.Date.now=()=>Date.parse(now);w.setInterval=()=>1;w.fetch=async()=>{throw Error('offline')};
 w.eval(source.replace('/* SHABBAT_FALLBACK */[]',JSON.stringify(intervals)));
 w.ShabbatMode.configure({isQA:()=>false,canUseApp:()=>true,onUnlock:()=>{}});
 await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(w.ShabbatMode.isLocked(),expected,now);
 if(expected)assert.equal(w.document.querySelector('#shabbat-screen').classList.contains('schedule-unavailable'),unknown);
 w.close();
}
(async()=>{
 await scenario('2026-10-24T12:00:00+03:00',bundled,true,false);
 await scenario('2026-10-22T12:00:00+03:00',bundled,false,false);
 await scenario('2026-10-24T23:00:00+03:00',bundled,false,false);
 await scenario('2026-10-24T12:00:00+03:00',[],true,true);
 await scenario('2026-10-24T18:00:00+03:00',[{start:'2026-10-30T16:00:00+02:00',end:'2026-10-31T17:15:00+02:00'}],true,true);
 console.log('Shabbat fallback: first offline visit, weekday, Saturday night, no coverage and future-only cache passed');
})().catch(error=>{console.error(error);process.exitCode=1;});

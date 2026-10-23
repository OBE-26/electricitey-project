const assert=require('node:assert/strict'),fs=require('node:fs'),{JSDOM}=require('jsdom');
const source=fs.readFileSync('Electricity-circuit.py','utf8');
const script=source.match(/<script>\s*(\/\/ Jerusalem Shabbat schedule[\s\S]*?)\n  <\/script>/)[1];
const dom=new JSDOM('<div id="app"><button>תרגול</button></div>',{url:'https://unit.test/',runScripts:'outside-only'});
const w=dom.window,d=w.document,start=Date.parse('2026-10-23T17:00:00+03:00'),end=Date.parse('2026-10-24T18:30:00+03:00');
let now=start-1,refresh,url,offline=false;
w.Date.now=()=>now;
w.setInterval=fn=>{refresh=fn;return 1;};
w.fetch=async request=>{url=request;if(offline)throw Error('test outage');return {ok:true,json:async()=>({items:[{category:'candles',date:new Date(start).toISOString()},{category:'havdalah',date:new Date(end).toISOString()}]})};};
w.eval(script);
(async()=>{
 try{
  await new Promise(resolve=>setTimeout(resolve,0));
  assert.ok(url.includes('geonameid=281184&b=40&M=on'));
  assert.equal(d.getElementById('shabbat-screen'),null,'Open before candle lighting');
  now=start;await refresh();
  assert.ok(d.getElementById('app').hasAttribute('inert'));
  assert.ok(d.getElementById('shabbat-screen').textContent.includes('שבת שלום'));
  assert.ok(d.getElementById('shabbat-screen').textContent.includes('נשוב לפעול בצאת השבת'));
  assert.equal(d.querySelectorAll('#shabbat-screen svg ellipse').length,2,'Two candle holders');
  offline=true;now=start+10000;await refresh();
  assert.ok(d.getElementById('app').hasAttribute('inert'),'Cached times survive a schedule-service outage');
  now=end;await refresh();
  assert.equal(d.getElementById('shabbat-screen'),null,'Reopen at Shabbat end');
  assert.equal(d.getElementById('app').hasAttribute('inert'),false);
  console.log('Shabbat: Jerusalem query, before/start/end boundaries, greeting, two candles and offline cache passed');
 }finally{w.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

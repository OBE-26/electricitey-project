// Read visible decimal or compact integer × 10^n quantities without treating
// a four-digit coefficient as the entire number.
function displayed(node){
 const text=typeof node==='string'?node:node.textContent;
 const match=/^\s*([+-]?\d+(?:\.\d+)?)(?:\s*×\s*10([⁰¹²³⁴⁵⁶⁷⁸⁹]+))?\s*(\S+)?\s*$/.exec(text);
 if(!match)throw Error('Unrecognized displayed quantity: '+text);
 const exponent=match[2]?Number([...match[2]].map(c=>'⁰¹²³⁴⁵⁶⁷⁸⁹'.indexOf(c)).join('')):0;
 return {value:Number(match[1])*10**exponent,unit:match[3]??''};
}
function physical(node){
 const {value,unit}=displayed(node);
 return value*({V:1,mV:.001,A:1,mA:.001,'Ω':1,'mΩ':.001,W:1,mW:.001}[unit]??NaN);
}
module.exports={displayed,physical};

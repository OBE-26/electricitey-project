import {spawn} from 'node:child_process';
import {existsSync,readFileSync} from 'node:fs';
// The preview supervisor appends Vite arguments; Streamlit uses its own flags.
const python=process.env.DC_PYTHON||process.env.CODEX_PRIMARY_RUNTIME_PYTHON||(existsSync('.openai/preview-python')?readFileSync('.openai/preview-python','utf8').trim():'python3');
const child=spawn(python,['-m','streamlit','run','Electricity-circuit.py','--server.port','4173','--server.address','0.0.0.0','--server.headless','true','--browser.gatherUsageStats','false'],{stdio:'inherit',env:process.env});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
child.on('exit',code=>process.exit(code??1));

"""Test-only JSON-lines bridge to the real course service (no HTTP/browser)."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from course_backend import ConfigStore,CourseService
root=Path(__file__).resolve().parents[1]
store=ConfigStore(Path(tempfile.mkdtemp())/'config.json')
store.save(store.public()['names'],[{'label':'unit tests','password':'test-only','expires_on':'','active':True}])
service=CourseService(store,root/'data/questions.json');session={}
for line in sys.stdin:
 event=json.loads(line)
 if event.get('action')=='config':reply={'ok':True,'config':store.public()}
 else:reply=service.handle(event,session)
 print(json.dumps({'request_id':event.get('id'),**reply},ensure_ascii=False),flush=True)

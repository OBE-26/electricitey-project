import importlib.util
import json
import random
import tempfile
import unittest
from datetime import date
from pathlib import Path
from course_backend import ConfigStore, CourseService, code_active, password_hash, password_matches, remap_choice_references, select_questions

ROOT=Path(__file__).resolve().parents[1]
class CoursesTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.store=ConfigStore(Path(self.temp.name)/'config.json')
  self.service=CourseService(self.store,ROOT/'data/questions.json')
  self.session={}
 def tearDown(self):self.temp.cleanup()
 def test_bank_and_requested_corrections(self):
  self.assertEqual(len(self.service.pool),190)
  self.assertEqual(self.service.by_id['a-001']['correct_choice_id'],'a-001-3')
  self.assertNotIn('c-010',self.service.by_id)
  self.assertEqual(self.service.by_id['c-016']['correct_choice_id'],'c-016-4')
  self.assertEqual(self.service.by_id['c-057']['correct_choice_id'],'c-057-1')
 def test_rotation_exhausts_fresh_items_and_avoids_previous(self):
  seen=[];previous=[];first=[]
  for index in range(30):
   drawn=select_questions(self.service.pool,seen,previous,rng=random.Random(index))
   ids=[q['id'] for q in drawn]
   self.assertEqual(len(set(ids)),20)
   self.assertFalse(set(ids)&set(previous))
   if index<9:first.extend(ids)
   seen=[i for i in seen if i not in ids]+ids;previous=ids
  self.assertEqual(len(set(first)),180)
 def test_small_pool_repeat_limit(self):
  pool=self.service.pool[:35]
  chosen=select_questions(pool,previous=[q['id'] for q in pool[:20]],rng=random.Random(1))
  self.assertEqual(len(set(q['id'] for q in chosen)&set(q['id'] for q in pool[:20])),5)
  with self.assertRaises(ValueError):select_questions(pool[:34],previous=[q['id'] for q in pool[:20]])
 def test_expiry_includes_last_date_and_revocation(self):
  code={'active':True,'expires_on':'2026-10-22'}
  self.assertTrue(code_active(code,date(2026,10,22)))
  self.assertFalse(code_active(code,date(2026,10,23)))
  self.assertFalse(code_active({**code,'active':False},date(2026,10,22)))
 def test_passwords_hashed_and_shared(self):
  result=self.store.save({'hvac':'מיזוג','security':'מיגון','mobile':'סלולר'},[{'label':'קבוצה א','password':'sample-pass','expires_on':'','active':True}])
  self.assertNotIn('hash',result['passwords'][0])
  data=self.store.read();self.assertNotIn('password',data['passwords'][0])
  self.assertTrue(password_matches('sample-pass',data['passwords'][0]))
  self.assertEqual(ConfigStore(self.store.path).public()['names']['hvac'],'מיזוג')
 def login(self):
  self.store.save(dict(self.store.public()['names']),[{'label':'test','password':'sample-pass','expires_on':'','active':True}])
  result=self.service.handle({'action':'exam_login','password':'sample-pass'},self.session)
  self.assertTrue(result['ok']);return result['token']
 def test_gate_grading_resume_and_tampering(self):
  self.assertTrue(self.service.handle({'action':'exam_new'},self.session)['unauthorized'])
  token=self.login()
  exam=self.service.handle({'action':'exam_new','token':token},self.session)
  self.assertTrue(exam['ok']);self.assertEqual(len(exam['questions']),20)
  self.assertNotIn('correct_choice_id',exam['questions'][0])
  for q in exam['questions']:
   original=self.service.by_id[q['id']]
   self.assertEqual({c['id'] for c in q['choices']},{c['id'] for c in original['choices']})
  answers={q['id']:self.service.by_id[q['id']]['correct_choice_id'] for q in exam['questions']}
  graded=self.service.handle({'action':'exam_submit','token':token,'exam':exam['exam'],'answers':answers},self.session)
  self.assertEqual(graded['correct'],20)
  self.assertEqual(graded['id'],exam['id'])
  self.assertTrue(all(q['correct_choice_id']==q['selected_choice_id'] for q in graded['questions']))
  resume=self.service.handle({'action':'exam_resume','token':token,'exam':exam['exam']},self.session)
  self.assertEqual(resume['questions'],exam['questions'])
  tampered=self.service.handle({'action':'exam_submit','token':token,'exam':exam['exam']+'x','answers':answers},self.session)
  self.assertFalse(tampered['ok'])
  rows=self.store.public(admin=True)['passwords'];rows[0]['active']=False
  self.store.save(dict(self.store.public()['names']),rows)
  self.assertTrue(self.service.handle({'action':'exam_submit','token':token,'exam':exam['exam'],'answers':answers},self.session)['unauthorized'])
 def test_wrong_and_unanswered(self):
  token=self.login();exam=self.service.handle({'action':'exam_new','token':token},self.session)
  q=exam['questions'][0];correct=self.service.by_id[q['id']]['correct_choice_id']
  wrong=next(c['id'] for c in q['choices'] if c['id']!=correct)
  graded=self.service.handle({'action':'exam_submit','token':token,'exam':exam['exam'],'answers':{q['id']:wrong}},self.session)
  self.assertEqual(graded['correct'],0);self.assertEqual(graded['questions'][0]['selected_choice_id'],wrong)
  self.assertIsNone(graded['questions'][1]['selected_choice_id'])
 def test_choice_reference_remapping(self):
  result=remap_choice_references('תשובות א׳ ו-ב׳ נכונות.',{'א':'ד','ב':'ג'})
  self.assertEqual(result,'תשובות ד׳ ו-ג׳ נכונות.')
  self.assertEqual(remap_choice_references("תשובות ב' ו-ג נכונות",{'ב':'א','ג':'ד'}),"תשובות א' ו-ד נכונות")
 def test_admin_requires_server_login(self):
  bad=self.service.handle({'action':'admin_save'},self.session);self.assertTrue(bad['unauthorized'])
  login=self.service.handle({'action':'admin_login','password':'210592'},self.session)
  self.assertTrue(login['ok'])
  saved=self.service.handle({'action':'admin_save','token':login['token'],'names':dict(self.store.public()['names']),'passwords':[]},self.session)
  self.assertTrue(saved['ok'])
if __name__=='__main__':unittest.main()

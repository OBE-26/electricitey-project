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
  self.assertEqual(len(self.service.pool),193)
  self.assertEqual(self.service.by_id['a-001']['correct_choice_id'],'a-001-3')
  self.assertNotIn('c-010',self.service.by_id)
  self.assertEqual(self.service.by_id['c-016']['correct_choice_id'],'c-016-4')
  self.assertEqual(self.service.by_id['c-057']['correct_choice_id'],'c-057-4')
 def test_new_source_keys_and_no_duplicate_imports(self):
  audit=json.loads((ROOT/'data/question_updates.json').read_text())
  self.assertEqual(len(audit['added_question_ids']),3)
  self.assertEqual(self.service.by_id['supp-photo-034']['correct_choice_id'],'supp-photo-034-2')
  self.assertEqual(len(audit['pdf_questions']),10)
  for row in audit['pdf_questions']:
   q=self.service.by_id[row['question_id']]
   label=next(c['label'] for c in q['choices'] if c['id']==q['correct_choice_id'])
   self.assertEqual(label,row['correct_choice_label'])
  q=self.service.by_id['c-087']
  self.assertIn('לא ניתן לבצע בהם איפוס',q['choices'][1]['text'])
  self.assertIn('מוביל',self.service.by_id['c-083']['text'])
  self.assertIn('כבל',self.service.by_id['supp-pdf-035']['text'])
 def test_qa_theory_requires_admin_and_cannot_resume_as_normal_exam(self):
  self.assertTrue(self.service.handle({'action':'exam_new','qa':True},self.session)['unauthorized'])
  normal=self.login()
  self.assertTrue(self.service.handle({'action':'exam_new','qa':True,'token':normal},self.session)['unauthorized'])
  admin=self.service.handle({'action':'admin_login','password':'210592'},self.session)['token']
  exam=self.service.handle({'action':'exam_new','qa':True,'token':admin},self.session)
  self.assertTrue(exam['ok']);self.assertTrue(exam['qa'])
  self.assertFalse(self.service.handle({'action':'exam_resume','token':normal,'exam':exam['exam']},self.session)['ok'])
  answers={q['id']:self.service.by_id[q['id']]['correct_choice_id'] for q in exam['questions']}
  result=self.service.handle({'action':'exam_submit','qa':True,'token':admin,'exam':exam['exam'],'answers':answers},self.session)
  self.assertEqual(result['correct'],20)
  self.assertTrue(result['qa'])
  self.assertTrue(self.service.handle({'action':'admin_logout','token':admin},self.session)['ok'])
  self.assertTrue(self.service.handle({'action':'exam_new','qa':True,'token':admin},self.session)['unauthorized'])
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
 def test_admin_can_manage_existing_password_without_replacing_other_settings(self):
  first=self.store.save(dict(self.store.public()['names']),[
   {'label':'first','password':'old-code','expires_on':'','active':True},
   {'label':'second','password':'other-code','expires_on':'','active':True}])
  admin=self.service.handle({'action':'admin_login','password':'210592'},self.session)
  token=admin['token'];row=admin['config']['passwords'][0]
  duplicate=self.service.handle({'action':'admin_password_save','token':token,'password':{**row,'password':'other-code'}},self.session)
  self.assertFalse(duplicate['ok'],'Editing an earlier row must not duplicate a later code')
  original_hash=self.store.read()['passwords'][0]['hash']
  result=self.service.handle({'action':'admin_password_save','token':token,'password':{**row,'label':'renamed','expires_on':'2099-12-31'}},self.session)
  self.assertTrue(result['ok']);self.assertEqual(len(result['config']['passwords']),2)
  self.assertEqual(self.store.read()['passwords'][0]['hash'],original_hash,'Empty replacement preserves the existing code')
  result=self.service.handle({'action':'admin_password_save','token':token,'password':{**row,'password':'new-code','expires_on':'','active':True}},self.session)
  self.assertTrue(result['ok'])
  self.assertFalse(self.service.handle({'action':'exam_login','password':'old-code'}, {})['ok'])
  self.assertTrue(self.service.handle({'action':'exam_login','password':'new-code'}, {})['ok'])
  self.assertTrue(self.service.handle({'action':'exam_login','password':'other-code'}, {})['ok'])
  names={**first['names'],'mobile':'new mobile name'}
  self.assertTrue(self.service.handle({'action':'admin_names_save','token':token,'names':names},self.session)['ok'])
  for active,status in [(False,'disabled'),(True,'active')]:
   result=self.service.handle({'action':'admin_password_save','token':token,'password':{**row,'active':active}},self.session)
   self.assertTrue(result['ok']);self.assertEqual(result['config']['passwords'][0]['status'],status)
   self.assertEqual(result['config']['names'],names)
  expired=self.service.handle({'action':'admin_password_save','token':token,'password':{**row,'expires_on':'2000-01-01'}},self.session)
  self.assertEqual(expired['config']['passwords'][0]['status'],'expired')
  other_store=ConfigStore(self.store.path)
  other_store.update(password={'label':'third','password':'third-code','expires_on':'','active':True})
  fresh=self.service.handle({'action':'admin_refresh','token':token},self.session)
  self.assertEqual(len(fresh['config']['passwords']),3)
  deleted=self.service.handle({'action':'admin_password_delete','token':token,'password_id':row['id']},self.session)
  self.assertEqual(len(deleted['config']['passwords']),2)
  self.assertFalse(self.service.handle({'action':'admin_password_save','token':token,'password':row},self.session)['ok'])
  for item in deleted['config']['passwords']:
   self.assertFalse({'hash','salt'}&set(item),'Password hashes never enter the admin browser response')
   self.assertIn('password_text',item)
  self.assertNotIn('passwords',self.store.public(),'The list is admin-only')
 def test_legacy_hash_only_password_can_be_reentered_for_admin_display(self):
  self.store.save(dict(self.store.public()['names']),[{'label':'legacy','password':'legacy-code','expires_on':'','active':True}])
  data=self.store.read();data['passwords'][0].pop('display_password');self.store._write_local(data)
  self.store._cached=None
  row=self.store.public(admin=True)['passwords'][0]
  self.assertIsNone(row['password_text'])
  self.assertTrue(self.service.handle({'action':'exam_login','password':'legacy-code'}, {})['ok'])
  self.store.update(password={**row,'password':'legacy-code'})
  self.assertEqual(self.store.public(admin=True)['passwords'][0]['password_text'],'legacy-code')
  self.assertNotIn('legacy-code',json.dumps(self.store.public()))
 def test_expired_code_automatically_blocks_login_and_an_existing_exam(self):
  token=self.login()
  exam=self.service.handle({'action':'exam_new','token':token},self.session)
  row=self.store.public(admin=True)['passwords'][0]
  self.store.update(password={**row,'expires_on':'2000-01-01'})
  self.assertEqual(self.store.public(admin=True)['passwords'][0]['status'],'expired')
  self.assertFalse(self.service.handle({'action':'exam_login','password':'sample-pass'}, {})['ok'])
  for action in ('exam_resume','exam_submit'):
   self.assertTrue(self.service.handle({'action':action,'token':token,'exam':exam['exam']},self.session)['unauthorized'])
 def test_password_management_routes_require_admin(self):
  for action in ('admin_refresh','admin_names_save','admin_password_save','admin_password_delete'):
   self.assertTrue(self.service.handle({'action':action},self.session)['unauthorized'])
 def test_admin_theory_entry_with_zero_student_passwords(self):
  self.assertEqual(self.store.public(admin=True)['passwords'],[])
  login=self.service.handle({'action':'admin_login','password':'210592'},self.session)
  self.assertTrue(login['capabilities']['qa_theory'])
  exam=self.service.handle({'action':'admin_exam_new','token':login['token']},self.session)
  self.assertTrue(exam['ok']);self.assertTrue(exam['qa']);self.assertEqual(len(exam['questions']),20)
  self.assertTrue(self.service.handle({'action':'admin_exam_resume','token':login['token'],'exam':exam['exam']},self.session)['ok'])
  self.assertTrue(self.service.handle({'action':'exam_new','token':login['token']},self.session)['unauthorized'])
  self.assertTrue(self.service.handle({'action':'admin_exam_new'},self.session)['unauthorized'])
if __name__=='__main__':unittest.main()

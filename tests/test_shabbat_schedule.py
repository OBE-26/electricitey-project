import importlib.util
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('schedule_update', ROOT/'scripts/update_shabbat_schedule.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)

class JerusalemScheduleTest(unittest.TestCase):
    def test_bundled_dates_cover_future_and_each_week(self):
        data = json.loads((ROOT/'data/shabbat_jerusalem.json').read_text())
        self.assertEqual(data['timezone'], 'Asia/Jerusalem')
        self.assertEqual(data['geonameid'], 281184)
        self.assertEqual(data['candle_minutes'], 40)
        self.assertEqual(data['havdalah'], 'nightfall_8.5_degrees')
        intervals = data['intervals']
        self.assertGreater(len(intervals), 100)
        self.assertGreater(datetime.fromisoformat(intervals[-1]['end']), datetime.now(timezone.utc)+timedelta(days=365))
        previous = None
        for item in intervals:
            start, end = [datetime.fromisoformat(item[k]) for k in ('start','end')]
            self.assertEqual(start.weekday(),4)
            self.assertEqual(end.weekday(),5)
            self.assertTrue(timedelta(hours=20)<end-start<timedelta(hours=30))
            if previous:self.assertEqual((start.date()-previous.date()).days,7)
            previous=start
    def test_missing_end_does_not_invent_a_time(self):
        with self.assertRaises(ValueError):
            update.build_schedule({'items':[{'category':'candles','date':'2026-10-23T17:00:00+03:00'}]},'fixture')
    def test_saturday_holiday_candles_mark_nightfall_when_no_havdalah(self):
        data=update.build_schedule({'items':[
            {'category':'candles','date':'2026-10-23T17:00:00+03:00'},
            {'category':'candles','date':'2026-10-24T18:30:00+03:00'}]},'fixture')
        self.assertEqual(data['intervals'][0]['end'],'2026-10-24T18:30:00+03:00')

"""Refresh the offline Jerusalem schedule from Hebcal's documented calendar API."""
import json
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

def build_schedule(data, source):
    events = []
    for item in data.get('items', []):
        if item.get('category') in ('candles', 'havdalah') and 'T' in item.get('date', ''):
            moment = datetime.fromisoformat(item['date'])
            events.append((moment, item['category']))
    intervals = []
    for start, category in sorted(events):
        if category != 'candles' or start.weekday() != 4:
            continue
        endings = [t for t, kind in events if t.weekday() == 5 and start < t < start + timedelta(hours=32)]
        if not endings:
            raise ValueError(f'Missing Saturday nightfall for {start.date()}')
        end = min(endings)
        intervals.append({'start': start.isoformat(), 'end': end.isoformat()})
    if not intervals:
        raise ValueError('The schedule contains no Shabbat intervals')
    return {'version': 1, 'timezone': 'Asia/Jerusalem', 'geonameid': 281184,
            'candle_minutes': 40, 'havdalah': 'nightfall_8.5_degrees', 'source': source,
            'generated_at': datetime.now(timezone.utc).isoformat(), 'intervals': intervals}

def main():
    today = date.today()
    start = today - timedelta(days=30)
    end = today + timedelta(days=800)
    source = ('https://www.hebcal.com/hebcal?v=1&cfg=json&c=on&geo=geoname&geonameid=281184'
              f'&b=40&M=on&i=on&start={start.isoformat()}&end={end.isoformat()}')
    with urllib.request.urlopen(source, timeout=30) as response:
        schedule = build_schedule(json.load(response), source)
    path = Path(__file__).resolve().parents[1] / 'data/shabbat_jerusalem.json'
    path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Updated {len(schedule["intervals"])} Jerusalem Shabbat intervals')

if __name__ == '__main__':
    main()

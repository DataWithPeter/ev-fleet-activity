"""Independent stdlib recount: decode every raw line before any tabular loader.

From the repository root, after generating expanded sources:
    python fleet_activity/scenarios/recount_expanded.py fleet_activity/data/sources recount.json expected_quality.json

The second and third arguments are output JSON files. Use --expected-days PATH
only to select a separately reviewed expected_vehicle_days.csv. No pandas needed.
"""
import collections
import csv
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import argparse


def recount(root, expected_path=None):
    root = Path(root)
    rejected = collections.Counter()
    valid = []
    reject_days = collections.Counter()
    line_count = 0
    invalid_lines = []
    for path in sorted((root / 'telemetry').glob('*.jsonl')):
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            line_count += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                rejected['malformed_json'] += 1
                invalid_lines.append([path.name, line_number])
                continue
            vehicle = row['vehicle_id']
            if not vehicle:
                rejected['missing_vehicle'] += 1
                continue
            try:
                timestamp = datetime.fromisoformat(row['event_timestamp'].replace('Z', '+00:00'))
            except ValueError:
                rejected['invalid_timestamp'] += 1
                continue
            day = timestamp.date().isoformat()
            if not '2026-08-01' <= day <= '2026-08-30':
                rejected['outside_report_period'] += 1
                continue
            if row['odometer_km'] < 0:
                rejected['invalid_odometer'] += 1
                reject_days[vehicle, day] += 1
                continue
            valid.append((vehicle, day, timestamp.isoformat(), row['odometer_km']))
    unique = set(valid)
    by_time = collections.defaultdict(list)
    by_day = collections.defaultdict(list)
    for vehicle, day, timestamp, value in unique:
        by_time[vehicle, day, timestamp].append(value)
        by_day[vehicle, day].append((timestamp, value))
    issues = collections.defaultdict(set)
    ordered = collections.defaultdict(list)
    for (vehicle, day, timestamp), values in by_time.items():
        if len(values) > 1:
            issues[vehicle, day].add('conflicting_timestamp')
        else:
            ordered[vehicle, day].append((timestamp, values[0]))
    for key, readings in ordered.items():
        readings.sort()
        for previous, current in zip(readings, readings[1:]):
            if current[1] < previous[1]:
                issues[key].add('odometer_decreased')
    for key in reject_days:
        issues[key].add('rejected_reading_in_day')
    with sqlite3.connect(root / 'fleet.sqlite') as db:
        vehicles = db.execute('SELECT vehicle_id,model,depot_id FROM vehicles ORDER BY vehicle_id').fetchall()
        depot_count = db.execute('SELECT COUNT(*) FROM depots').fetchone()[0]
    registered = {row[0] for row in vehicles}
    keys = {(v, f'2026-08-{d:02}') for v in registered for d in range(1,31)} | set(by_day) | set(reject_days)
    quality = []
    priority = ['conflicting_timestamp','odometer_decreased','rejected_reading_in_day',
                'missing_telemetry','insufficient_readings','unregistered_vehicle']
    for key in sorted(keys):
        vehicle, day = key
        reading_count = len(ordered[key])
        day_issues = set(issues[key])
        if day_issues:
            status = 'untrusted'
        elif key not in by_day:
            status = 'missing_telemetry'
            day_issues.add(status)
        elif reading_count < 2:
            status = 'insufficient_readings'
            day_issues.add(status)
        else:
            status = 'trusted'
        if vehicle not in registered:
            day_issues.add('unregistered_vehicle')
        codes = [code for code in priority if code in day_issues]
        quality.append({'vehicle_id':vehicle,'event_date':day,'distance_status':status,
            'reading_count':reading_count,'issue_codes':codes,'issue_count':len(codes),
            'primary_issue':codes[0] if codes else None,
            'accepted_reading_count':len(by_day[key]) if status != 'untrusted' else 0,
            'held_reading_count':len(by_day[key]) if status == 'untrusted' else 0,
            'rejected_record_count':reject_days[key]})
    summary = {'bronze':line_count,'json_decoded':line_count-len(invalid_lines),
        'json_parse_failures':invalid_lines,'reject_reasons':dict(rejected),'vehicles':len(vehicles),
        'depots':depot_count,'model_mix':dict(collections.Counter(m+'|'+d for _,m,d in vehicles)),
        'gold':len(quality),'statuses':dict(collections.Counter(q['distance_status'] for q in quality)),
        'affected':sum(q['distance_status']!='trusted' for q in quality),
        'exception_days':sum(q['issue_count']>0 for q in quality),
        'occurrences':sum(q['issue_count'] for q in quality),
        'accepted':sum(q['accepted_reading_count'] for q in quality),
        'rejected':sum(rejected.values()),'held':sum(q['held_reading_count'] for q in quality),
        'duplicates_independently_identified':len(valid)-len(unique),
        'linked':sum(reject_days.values()),'unlinked':sum(rejected.values())-sum(reject_days.values())}
    summary['quarantine'] = summary['held']+summary['rejected']
    summary['remainder'] = summary['bronze']-summary['accepted']-summary['rejected']-summary['held']
    summary['file_sha256'] = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(root.rglob('*')) if p.is_file()}
    if expected_path is None:
        expected_path = Path(__file__).parent / 'expanded_august_v1/expected_vehicle_days.csv'
    with Path(expected_path).open(newline='') as file:
        manifest_rows = list(csv.DictReader(file))
    for row in manifest_rows:
        for field in ['reading_count','accepted_reading_count','held_reading_count','rejected_record_count','issue_count']:
            row[field] = int(row[field])
        row['primary_issue'] = row['primary_issue'] or None
        row['issue_codes'] = row['issue_codes'].split(';') if row['issue_codes'] else []
    actual = {(q['vehicle_id'],q['event_date']):q for q in quality}
    for row in manifest_rows:
        assert actual[row['vehicle_id'],row['event_date']] == row, (row, actual[row['vehicle_id'],row['event_date']])
    summary['manifest_nondefault_days_verified'] = len(manifest_rows)
    expected = {'bronze':10652,'gold':1805,'affected':43,'exception_days':47,'occurrences':52,
        'accepted':10517,'rejected':19,'held':106,'remainder':10,'quarantine':125,'linked':8,'unlinked':11}
    assert all(summary[k]==v for k,v in expected.items()), summary
    assert summary['statuses']=={'trusted':1762,'untrusted':18,'insufficient_readings':9,'missing_telemetry':16}
    assert len(invalid_lines)==3 and summary['duplicates_independently_identified']==10
    assert len(manifest_rows)==71
    return summary, quality


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source_dir', type=Path, help='Generated directory with telemetry/ and fleet.sqlite')
    parser.add_argument('summary_json', type=Path, help='Output recount summary')
    parser.add_argument('quality_json', type=Path, help='Output independently recounted quality rows')
    parser.add_argument('--expected-days', type=Path, help='Reviewed expected CSV; defaults to bundled scenario CSV')
    arguments = parser.parse_args()
    summary, quality = recount(arguments.source_dir, arguments.expected_days)
    arguments.summary_json.write_text(json.dumps(summary, indent=2) + '\n')
    arguments.quality_json.write_text(json.dumps(quality, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'file_sha256'}, indent=2))

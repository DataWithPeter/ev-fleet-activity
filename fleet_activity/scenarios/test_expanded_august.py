"""Manual scenario checks. Run after the four local notebooks; baseline tests stay separate.
No pandas dependency: malformed JSON lines are counted before any DataFrame is built.
"""
from collections import Counter
import ast
import csv
import hashlib
import shutil
import json
from pathlib import Path
import sqlite3
import sys

import pytest
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from generate_sources import generate_sources
from recount_expanded import recount


@pytest.fixture(scope='module')
def raw():
    return recount(ROOT / 'data/sources')


@pytest.fixture(scope='module')
def spark():
    status = json.loads((ROOT / 'output/execution_status.json').read_text())
    assert status['state'] == 'succeeded', 'Run all four notebooks before scenario tests'
    builder = (SparkSession.builder.master('local[2]').appName('expanded-validation')
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension')
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog')
        .config('spark.sql.shuffle.partitions', '2'))
    session = configure_spark_with_delta_pip(builder).getOrCreate()
    session.conf.set('spark.sql.session.timeZone', 'UTC')
    session.sparkContext.setLogLevel('ERROR')
    yield session
    session.stop()


def table(spark, name):
    return spark.read.format('delta').load(str(ROOT / 'output/delta' / name))


def test_two_fresh_generations_are_identical(tmp_path):
    a, b = tmp_path/'a', tmp_path/'b'
    generate_sources(a, 'expanded_august_v1')
    generate_sources(b, 'expanded_august_v1')
    hashes = lambda root: {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in root.rglob('*') if p.is_file()}
    assert hashes(a) == hashes(b)
    assert recount(a)[0] == recount(b)[0]


def test_baseline_is_still_the_default(tmp_path):
    generate_sources(tmp_path)
    assert json.loads((tmp_path/'scenario_manifest.json').read_text())['scenario']=='baseline'
    assert sum(len(p.read_text().splitlines()) for p in (tmp_path/'telemetry').glob('*.jsonl'))==4316
    with sqlite3.connect(tmp_path/'fleet.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]==24


def test_unknown_scenario_is_rejected_before_writing(tmp_path):
    with pytest.raises(ValueError, match='Unknown scenario'):
        generate_sources(tmp_path/'unused', 'typo')
    assert not (tmp_path/'unused').exists()


def test_stale_out_of_period_file_is_not_silently_ingested(tmp_path):
    (tmp_path/'telemetry').mkdir()
    (tmp_path/'telemetry/2026-07-31.jsonl').write_text('{}\n')
    with pytest.raises(ValueError, match='Unexpected telemetry'):
        generate_sources(tmp_path, 'expanded_august_v1')


def test_raw_lines_and_reject_reasons(raw):
    counts, _ = raw
    assert counts['bronze']==10652 and counts['json_decoded']==10649
    assert counts['reject_reasons']=={'malformed_json':3,'missing_vehicle':3,
        'invalid_timestamp':3,'outside_report_period':2,'invalid_odometer':8}
    assert counts['duplicates_independently_identified']==10
    assert counts['manifest_nondefault_days_verified']==71


def test_all_quality_rows_match_independent_raw_recount(spark, raw):
    expected = {(r['vehicle_id'],r['event_date']):r for r in raw[1]}
    q = table(spark,'gold_vehicle_day_quality')
    actual = q.collect()
    assert len(actual)==len(expected)==1805
    for row in actual:
        wanted=expected[row.vehicle_id,str(row.event_date)]
        for field,value in wanted.items():
            if field not in ['event_date','issue_codes']:
                assert row[field]==value, (row.vehicle_id,row.event_date,field)
        assert row.vehicle_day_key==row.vehicle_id+'|'+str(row.event_date)


def test_all_issue_pairs_and_priorities_match_raw_recount(spark, raw):
    expected={(r['vehicle_id'],r['event_date'],code) for r in raw[1] for code in r['issue_codes']}
    rows=table(spark,'gold_vehicle_day_issue').collect()
    assert len(rows)==len(expected)==52
    assert {(r.vehicle_id,str(r.event_date),r.issue_code) for r in rows}==expected
    priority={'conflicting_timestamp':10,'odometer_decreased':20,'rejected_reading_in_day':30,
              'missing_telemetry':40,'insufficient_readings':50,'unregistered_vehicle':60}
    assert all(r.primary_priority==priority[r.issue_code] for r in rows)


def test_reconciliation_and_source_sums(spark):
    rows=table(spark,'gold_record_reconciliation').collect()
    assert len(rows)==1 and tuple(rows[0])==(10652,10517,19,106,125,8,11,10)
    assert table(spark,'bronze_telemetry').count()==10652
    assert table(spark,'silver_telemetry').count()==10517
    assert table(spark,'quarantine_telemetry').count()==125
    q=table(spark,'gold_vehicle_day_quality')
    sums=q.agg(F.sum('accepted_reading_count'),F.sum('held_reading_count'),F.sum('rejected_record_count')).first()
    assert tuple(sums)==(10517,106,8)


def test_gold_grain_weather_and_distance_rules(spark):
    gold=table(spark,'gold_daily_vehicle_activity')
    assert len(gold.columns)==14 and gold.count()==1805
    assert gold.select('vehicle_id','event_date').distinct().count()==1805
    assert gold.filter((F.col('distance_status')!='trusted') & F.col('observed_distance_km').isNotNull()).count()==0
    assert table(spark,'silver_weather').count()==60
    assert gold.filter(~F.col('event_date').between('2026-08-01','2026-08-30')).count()==0
    assert gold.filter(~F.col('registered_vehicle')).count()==5


def test_partial_days_really_end_at_14_and_keep_observed_only_distance(spark):
    gold=table(spark,'gold_daily_vehicle_activity')
    partial=gold.filter(F.col('vehicle_id').isin('EV014','EV023','EV029','EV040','EV050','EV056') & F.dayofmonth('event_date').isin(2,10,18,26))
    assert partial.count()==24
    assert partial.filter((F.col('reading_count')!=4) | (F.hour('first_reading')!=8) | (F.hour('last_reading')!=14) | (F.col('distance_status')!='trusted')).count()==0
    accepted=table(spark,'silver_telemetry').groupBy('vehicle_id','event_date').agg((F.max('odometer_km')-F.min('odometer_km')).alias('expected_distance'))
    assert partial.join(accepted,['vehicle_id','event_date']).filter(F.abs(F.col('observed_distance_km')-F.col('expected_distance'))>0.011).count()==0


def test_outages_overlaps_and_unregistered_insufficient(spark):
    q=table(spark,'gold_vehicle_day_quality')
    assert q.filter((F.col('distance_status')!='trusted')).count()==43
    assert q.filter(F.col('issue_count')>0).count()==47
    assert q.filter(F.col('issue_count')==2).count()==5
    assert q.filter((F.col('vehicle_id')=='EV003') & (F.col('primary_issue').isin('odometer_decreased','conflicting_timestamp'))).count()==3
    for vehicle in ['EV009','EV010','EV011','EV012']:
        assert q.filter((F.col('vehicle_id')==vehicle) & F.dayofmonth('event_date').isin(11,12) & (F.col('distance_status')=='missing_telemetry')).count()==2
    row=q.filter((F.col('vehicle_id')=='UNREG002') & (F.dayofmonth('event_date')==22)).first()
    assert (row.reading_count,row.accepted_reading_count,row.distance_status,row.issue_count,row.primary_issue)==(1,1,'insufficient_readings',2,'insufficient_readings')


@pytest.mark.parametrize('scenario', ['baseline','expanded_august_v1'])
def test_platform_proof_accepts_each_saved_local_reference(scenario):
    notebook=json.loads((ROOT/'databricks/03_gold_activity.ipynb').read_text())
    code=next(''.join(c['source']) for c in notebook['cells']
              if c['cell_type']=='code' and c['metadata']['tags'][0]=='platform_proof')
    code=code.split('print("PLATFORM_REPLAY_VALIDATION_PASSED")')[0]
    # Execute the reviewed-reference declaration separately, then test the actual proof.
    declaration=code[code.index('references = {'):code.index('if scenario not in references:')]
    context={}
    exec(declaration,context)
    reference=context['references'][scenario]
    class Manifest:
        def __truediv__(self, other): return self
        def read_text(self): return json.dumps({'scenario':scenario})
    exec(code,dict(json=json,source_dir=Manifest(),summary=dict(reference)))


@pytest.mark.parametrize('fault', ['unknown_scenario','wrong_hash','wrong_count'])
def test_platform_proof_fails_closed(fault):
    notebook=json.loads((ROOT/'databricks/03_gold_activity.ipynb').read_text())
    code=next(''.join(c['source']) for c in notebook['cells']
              if c['cell_type']=='code' and c['metadata']['tags'][0]=='platform_proof')
    code=code.split('print("PLATFORM_REPLAY_VALIDATION_PASSED")')[0]
    summary=json.loads((ROOT/'output/run_summary.json').read_text())
    if fault=='wrong_hash': summary['business_output_sha256']='incorrect'
    if fault=='wrong_count': summary['gold_rows']=1806
    scenario='typo' if fault=='unknown_scenario' else 'expanded_august_v1'
    class Manifest:
        def __truediv__(self, other): return self
        def read_text(self): return json.dumps({'scenario':scenario})
    with pytest.raises(ValueError):
        exec(code,dict(json=json,source_dir=Manifest(),summary=summary))


def copy_assets(tmp_path):
    target=tmp_path/'assets'
    shutil.copytree(ROOT/'scenarios/expanded_august_v1',target)
    return target


def write_events(path, rows, fields):
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def test_empty_events_csv_produces_no_injected_defects(tmp_path):
    assets=copy_assets(tmp_path)
    with (assets/'events.csv').open(newline='') as file:
        fields=csv.DictReader(file).fieldnames
    write_events(assets/'events.csv',[],fields)
    output=tmp_path/'sources'
    generate_sources(output,'expanded_august_v1',assets)
    records=[json.loads(line) for p in (output/'telemetry').glob('*.jsonl') for line in p.read_text().splitlines()]
    assert len(records)==10800
    assert len({(r['vehicle_id'],r['event_timestamp']) for r in records})==10800
    assert all(r['vehicle_id'].startswith('EV') and r['odometer_km']>=0 for r in records)
    grouped={}
    for row in records:
        key=(row['vehicle_id'],row['event_timestamp'][:10])
        grouped.setdefault(key,[]).append((row['event_timestamp'],row['odometer_km']))
    assert len(grouped)==1800
    for values in grouped.values():
        values.sort()
        assert len(values)==6 and all(b[1]>=a[1] for a,b in zip(values,values[1:]))


def test_removing_one_csv_outage_restores_exactly_six_readings(tmp_path):
    assets=copy_assets(tmp_path)
    with (assets/'events.csv').open(newline='') as file:
        reader=csv.DictReader(file);fields=reader.fieldnames;rows=list(reader)
    removed=rows.pop(0)
    assert (removed['event_type'],removed['vehicle_id'],removed['event_date'])==('missing_telemetry','EV009','2026-08-11')
    write_events(assets/'events.csv',rows,fields)
    output=tmp_path/'sources'
    generate_sources(output,'expanded_august_v1',assets)
    assert sum(len(p.read_text().splitlines()) for p in (output/'telemetry').glob('*.jsonl'))==10658
    records=[json.loads(line) for line in (output/'telemetry/2026-08-11.jsonl').read_text().splitlines()]
    assert len([r for r in records if r['vehicle_id']=='EV009'])==6


def test_expected_csv_is_independent_and_never_a_generation_input(tmp_path):
    assets=copy_assets(tmp_path)
    (assets/'expected_vehicle_days.csv').unlink()
    output=tmp_path/'sources'
    generate_sources(output,'expanded_august_v1',assets)
    for p in (ROOT/'data/sources/telemetry').glob('*.jsonl'):
        assert (output/'telemetry'/p.name).read_bytes()==p.read_bytes()
    manifest=json.loads((output/'scenario_manifest.json').read_text())
    assert set(manifest['input_sha256'])=={'scenario.json','events.csv'}
    assert 'expected_nondefault_days' not in manifest
    with (ROOT/'scenarios/expanded_august_v1/expected_vehicle_days.csv').open(newline='') as file:
        rows=list(csv.DictReader(file))
    assert len(rows)==len({(r['vehicle_id'],r['event_date']) for r in rows})==71


@pytest.mark.parametrize('fault',['unknown_type','duplicate_id','missing_csv'])
def test_bad_event_input_fails_before_output(tmp_path,fault):
    assets=copy_assets(tmp_path)
    with (assets/'events.csv').open(newline='') as file:
        reader=csv.DictReader(file);fields=reader.fieldnames;rows=list(reader)
    if fault=='unknown_type':rows[0]['event_type']='typo'
    if fault=='duplicate_id':rows[1]['event_id']=rows[0]['event_id']
    write_events(assets/'events.csv',rows,fields)
    if fault=='missing_csv':(assets/'events.csv').unlink()
    output=tmp_path/'sources'
    with pytest.raises((ValueError,FileNotFoundError)):
        generate_sources(output,'expanded_august_v1',assets)
    assert not output.exists()


def test_databricks_embeds_exact_assets_and_runs_without_repo_paths(tmp_path):
    notebook=json.loads((ROOT/'databricks/00_prepare_demo.ipynb').read_text())
    cells={c['metadata']['tags'][0]:''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code'}
    assert cells['source_generator']==(ROOT/'generate_sources.py').read_text().split('if __name__ == "__main__":')[0]
    assets=tmp_path/'volume-assets';assets.mkdir()
    extracted=[]
    for node in ast.walk(ast.parse(cells['platform_setup'])):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr!='write_text':continue
        target=node.func.value
        if isinstance(target,ast.BinOp) and isinstance(target.left,ast.Name) and target.left.id=='scenario_dir':
            name=ast.literal_eval(target.right);content=ast.literal_eval(node.args[0])
            assert content==(ROOT/'scenarios/expanded_august_v1'/name).read_text()
            (assets/name).write_text(content);extracted.append(name)
    assert set(extracted)=={'scenario.json','events.csv','expected_vehicle_days.csv'}
    context={'__name__':'embedded_demo'}  # No __file__, repo checkout or cloud needed.
    exec(cells['source_generator'],context)
    output=tmp_path/'embedded-sources'
    context['generate_sources'](output,'expanded_august_v1',assets)
    for p in (ROOT/'data/sources/telemetry').glob('*.jsonl'):
        assert (output/'telemetry'/p.name).read_bytes()==p.read_bytes()

"""Verify the live reporting tables after a fixed-hour refresh and retry."""
import os

import psycopg

with psycopg.connect(os.environ['TOWER_DSN']) as db:
    for table, expected in (
        ('demand', 336), ('inventory', 4), ('shipments', 48), ('inventory_hour', 672),
        ('forecast', 56), ('delay_panel', 32), ('alert', 3), ('refresh', 1), ('delivered_digest', 0),
    ):
        count = db.execute(f'select count(*) from tower.{table}').fetchone()[0]
        assert count == expected, f'{table}: expected {expected} rows, got {count}'
    assert db.execute('select count(*) from tower.scenario where delay_days=0 and incremental_unmet<>0').fetchone()[0] == 0
    print('Warehouse counts, baseline scenarios, and retry passed.')

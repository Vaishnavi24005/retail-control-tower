"""Generate the offline dashboard or refresh PostgreSQL and deliver threshold alerts."""
import argparse
import json
import os
import random
import smtplib
import ssl
import statistics
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRODUCTS = (
    ('SKU-101', 'Coffee beans', 'Northstar Foods', 42, 105, 170, 2),
    ('SKU-204', 'Oat milk', 'Evergreen Supply', 30, 80, 210, 1),
    ('SKU-307', 'Paper filters', 'Harbor Wholesale', 17, 145, 130, 4),
    ('SKU-412', 'Cold brew', 'Northstar Foods', 22, 34, 140, 3),
)
DEMO_HOUR = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)


def simulate(hour):
    """Fixed product histories advance with the UTC hour; only completed days are scored."""
    today = hour.date()
    history, inventory, shipments = [], [], []
    for index, (sku, name, supplier, rate, stock, incoming, eta) in enumerate(PRODUCTS):
        for offset in range(84, 0, -1):
            day = today - timedelta(days=offset)
            rng = random.Random(f'{sku}:{day.isoformat()}')
            units = max(0, rate + (7 if day.weekday() >= 5 else 0) + rng.randint(-5, 5))
            if sku == 'SKU-412' and offset == 1:
                units += 50
            history.append((sku, day, units))
        rng = random.Random(f'{sku}:{hour.isoformat()}')
        on_hand = max(0, stock + rng.randint(-12, 12))
        inventory.append((sku, name, supplier, on_hand, incoming, today + timedelta(days=eta)))
        for i in range(12):
            delivered = today - timedelta(days=1 + i * 3)
            late = (8 if i == 0 and index == 1 else int((i + index) % 5 == 0))
            promised = delivered - timedelta(days=late)
            ordered = promised - timedelta(days=4 + i % 3)
            shipments.append((f'{sku}-{i}', sku, supplier, ordered, promised, delivered))
    # Each record represents an observed SKU-hour, including completed stockout episodes.
    snapshots = []
    for sku, name, supplier, on_hand, *_ in inventory:
        for lag in range(168):
            slot = hour - timedelta(hours=lag)
            rng = random.Random(f'{sku}:{slot.isoformat()}:snapshot')
            units = on_hand if lag == 0 else (0 if rng.random() < (0.15 if sku == 'SKU-412' else 0.035)
                                             else rng.randint(15, 160))
            snapshots.append((sku, slot, units))
    return history, inventory, shipments, snapshots


def forecast(series, days, method):
    """Predict a complete daily horizon from history ordered by date."""
    if method == 'prophet':
        import pandas as pd
        from prophet import Prophet

        frame = pd.DataFrame(series, columns=['ds', 'y'])
        frame['ds'] = pd.to_datetime(frame['ds'])
        model = Prophet(weekly_seasonality=True, daily_seasonality=False,
                        yearly_seasonality=False, uncertainty_samples=0)
        model.fit(frame)
        future = model.make_future_dataframe(periods=days, include_history=False)
        return [round(max(0, value), 2) for value in model.predict(future)['yhat']]
    weeks = series[-28:]
    last_day = series[-1][0]
    return [round(statistics.mean(units for day, units in weeks
                                   if day.weekday() == (last_day.weekday() + step) % 7), 2)
            for step in range(1, days + 1)]


def scenario(on_hand, incoming, eta, demand, delay):
    """Receipts land at the start of the day. Unmet demand is lost."""
    available = on_hand
    unmet = 0
    first = None
    for day, units in enumerate(demand, 1):
        if day == eta + delay:
            available += incoming
        shortage = max(0, units - available)
        if shortage > 0:
            first = first or day
        unmet += shortage
        available = max(0, available - units)
    return round(unmet, 2), first, round(available, 2)


def zscore(value, baseline):
    mean = statistics.mean(baseline)
    spread = statistics.pstdev(baseline)
    return (value - mean) / max(spread, 1)


def analyze(hour, method):
    history, inventory, shipments, snapshots = simulate(hour)
    today = hour.date()
    products, scenarios, alerts, forecasts = [], [], [], []
    total_error = total_actual = 0
    for sku, name, supplier, stock, incoming, arrival in inventory:
        series = [(day, units) for key, day, units in history if key == sku]
        deliveries = [(o, p, d) for _, key, _, o, p, d in shipments if key == sku]
        test = forecast(series[:-14], 14, method)
        total_error += sum(abs(actual - predicted) for (_, actual), predicted in zip(series[-14:], test))
        total_actual += sum(units for _, units in series[-14:])
        demand = forecast(series, 14, method)
        forecasts.extend((sku, today + timedelta(days=day - 1), units)
                         for day, units in enumerate(demand, 1))
        eta = (arrival - today).days + 1
        coverage = stock / statistics.mean(demand[:7]) if any(demand[:7]) else None
        observed = [units for key, _, units in snapshots if key == sku]
        base_loss, _, _ = scenario(stock, incoming, eta, demand, 0)
        products.append(dict(sku=sku, product=name, supplier=supplier, on_hand=stock, inbound=incoming,
                             arrival=arrival.isoformat(), stockout_rate=observed.count(0) / len(observed),
                             on_time=sum(d <= p for _, p, d in deliveries) / len(deliveries),
                             lead_days=round(statistics.mean((d - o).days for o, _, d in deliveries), 2),
                             days_inventory=round(coverage, 2) if coverage is not None else None,
                             forecast_7d=round(sum(demand[:7]), 2), baseline_unmet=base_loss))
        for delay in range(8):
            unmet, first, ending = scenario(stock, incoming, eta, demand, delay)
            scenarios.append(dict(sku=sku, delay_days=delay, unmet_units=unmet,
                                  first_stockout_day=first, ending_stock=ending,
                                  incremental_unmet=round(unmet - base_loss, 2)))
        recent_day, latest = series[-1]
        matched = [units for day, units in series[:-1] if day.weekday() == recent_day.weekday()]
        demand_z = zscore(latest, matched[-8:])
        lateness = [(d - p).days for _, p, d in deliveries]
        delay_z = zscore(lateness[0], lateness[1:])
        checks = (
            ('demand_spike', demand_z >= 3, f'Prior-day demand was {latest} units (z={demand_z:.1f}).'),
            ('delivery_delay', delay_z >= 3, f'Latest receipt was {lateness[0]} days late (z={delay_z:.1f}).'),
            ('low_cover', coverage is not None and coverage < 2, f'Stock cover is {coverage:.2f} days.'),
        )
        for code, triggered, message in checks:
            if triggered:
                alerts.append(dict(sku=sku, code=code, message=message))
    return dict(hour=hour.isoformat(), method=method, wape=round(total_error / total_actual, 4),
                products=products, scenarios=scenarios, alerts=alerts), (history, inventory, shipments, snapshots, forecasts)


def refresh(hour, deliver_alerts):
    import psycopg

    started = time.perf_counter()
    payload, raw = analyze(hour, 'prophet')
    with psycopg.connect(os.environ['TOWER_DSN']) as connection, connection.cursor() as cursor:
        cursor.execute((ROOT / 'sql' / 'schema.sql').read_text(encoding='utf-8'))
        cursor.execute("select pg_advisory_xact_lock(930013)")
        cursor.execute('select max(as_of) from tower.refresh')
        current = cursor.fetchone()[0]
        if current is not None and current > hour:
            print('A newer refresh already exists.')
            return
        for table in ('demand', 'inventory', 'shipments', 'inventory_hour', 'forecast', 'product_kpi', 'scenario', 'alert'):
            cursor.execute(f'delete from tower.{table}')
        for table, rows in zip(('demand', 'inventory', 'shipments', 'inventory_hour', 'forecast'), raw):
            marks = ', '.join(['%s'] * len(rows[0]))
            cursor.executemany(f'insert into tower.{table} values ({marks})', rows)
        for key, table in (('products', 'product_kpi'), ('scenarios', 'scenario'), ('alerts', 'alert')):
            for row in payload[key]:
                columns = ', '.join(row)
                marks = ', '.join(['%s'] * len(row))
                cursor.execute(f'insert into tower.{table} ({columns}) values ({marks})', tuple(row.values()))
        cursor.execute('insert into tower.refresh values (%s,%s,%s) on conflict (as_of) do update set method=excluded.method,wape=excluded.wape',
                       (hour, payload['method'], payload['wape']))
    print(f'Refreshed {hour.isoformat()} in {time.perf_counter() - started:.2f}s')
    if deliver_alerts and payload['alerts']:
        notify(hour, payload['alerts'])


def notify(hour, alerts):
    """Send one digest per UTC hour; a crash after SMTP acceptance may duplicate a retry."""
    import psycopg

    with psycopg.connect(os.environ['TOWER_DSN']) as connection, connection.cursor() as cursor:
        cursor.execute('select pg_advisory_xact_lock(930014)')
        cursor.execute('select 1 from tower.delivered_digest where as_of=%s', (hour,))
        if cursor.fetchone():
            return
        message = EmailMessage()
        message['Subject'] = f'Control Tower alerts for {hour:%Y-%m-%d %H:%M} UTC'
        message['From'] = os.environ['TOWER_SMTP_FROM']
        message['To'] = os.environ['TOWER_SMTP_TO']
        message.set_content('\n'.join(f"{a['sku']} | {a['code']} | {a['message']}" for a in alerts))
        with smtplib.SMTP(os.environ['TOWER_SMTP_HOST'], int(os.getenv('TOWER_SMTP_PORT', '587')), timeout=30) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if os.getenv('TOWER_SMTP_USER'):
                smtp.login(os.environ['TOWER_SMTP_USER'], os.environ['TOWER_SMTP_PASSWORD'])
            smtp.send_message(message)
        cursor.execute('insert into tower.delivered_digest values (%s)', (hour,))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('demo', 'refresh'))
    parser.add_argument('--hour', help='ISO 8601 timestamp with timezone')
    parser.add_argument('--method', choices=('weekday', 'prophet'), default='weekday')
    parser.add_argument('--notify', action='store_true')
    args = parser.parse_args()
    hour = DEMO_HOUR if args.mode == 'demo' else datetime.now(timezone.utc)
    if args.hour:
        hour = datetime.fromisoformat(args.hour)
        if hour.tzinfo is None:
            parser.error('--hour requires a timezone')
    hour = hour.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    if args.mode == 'refresh':
        refresh(hour, args.notify)
    else:
        payload, _ = analyze(hour, args.method)
        (ROOT / 'demo' / 'data.js').write_text('window.TOWER = ' + json.dumps(payload) + ';\n', encoding='utf-8')
        print(f"{len(payload['products'])} SKUs, {len(payload['alerts'])} alerts, WAPE {payload['wape']:.2%}")


if __name__ == '__main__':
    main()

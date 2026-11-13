create schema if not exists tower;
create table if not exists tower.demand (sku text, day date, units integer check (units >= 0), primary key (sku, day));
create table if not exists tower.inventory (sku text primary key, product text, supplier text, on_hand integer, incoming integer, arrival date);
create table if not exists tower.shipments (shipment_id text primary key, sku text, supplier text, ordered date, promised date, delivered date);
create table if not exists tower.inventory_hour (sku text, observed_at timestamptz, on_hand integer, primary key (sku, observed_at));
create table if not exists tower.forecast (sku text, day date, units numeric, primary key (sku, day));
create table if not exists tower.product_kpi (
  sku text primary key, product text, supplier text, on_hand integer, inbound integer, arrival date,
  stockout_rate numeric, on_time numeric, lead_days numeric, days_inventory numeric,
  forecast_7d numeric, baseline_unmet numeric
);
create table if not exists tower.scenario (
  sku text, delay_days integer check (delay_days between 0 and 7), unmet_units numeric,
  first_stockout_day integer, ending_stock numeric, incremental_unmet numeric, primary key (sku, delay_days)
);
create table if not exists tower.alert (sku text, code text, message text, primary key (sku, code));
create table if not exists tower.refresh (as_of timestamptz primary key, method text, wape numeric);
create table if not exists tower.delivered_digest (as_of timestamptz primary key);
create or replace view tower.supplier_kpi as
select supplier, count(*) as delivered_shipments,
       avg(case when delivered <= promised then 1.0 else 0.0 end) as on_time_rate,
       avg(delivered - ordered) as mean_lead_days
from tower.shipments
group by supplier;
create or replace view tower.delay_panel as
select s.*, p.product, p.supplier, p.on_hand, p.forecast_7d
from tower.scenario s join tower.product_kpi p using (sku);

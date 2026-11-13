'use strict';
const data = window.TOWER;
const get = id => document.getElementById(id);
const pct = new Intl.NumberFormat('en-US', {style:'percent', maximumFractionDigits:1});
const num = new Intl.NumberFormat('en-US', {maximumFractionDigits:1});
const show = value => value == null ? '—' : num.format(value);
const names = new Map(data.products.map(product => [product.sku, product.product]));
function row(id, fields) {
    const tr = get(id).insertRow();
    for (const field of fields) tr.insertCell().textContent = field;
}
get('asof').textContent = data.hour.replace('T',' ').slice(0,16) + ' UTC · Synthetic data · ' +
    (data.method === 'prophet' ? 'Prophet' : 'Weekday average') + ' forecast';
get('stock').textContent = show(data.products.reduce((total, p) => total + p.on_hand, 0));
get('wape').textContent = pct.format(data.wape);
get('ontime').textContent = pct.format(data.products.reduce((total, p) => total+p.on_time,0)/data.products.length);
get('stockout').textContent = pct.format(data.products.reduce((total,p) => total+p.stockout_rate,0)/data.products.length);
for (const p of data.products) row('products', [
    p.product,p.supplier,show(p.on_hand),show(p.forecast_7d),show(p.days_inventory),
    show(p.lead_days)+' days',pct.format(p.on_time)
]);
const slider = get('delay');
function renderScenario() {
    const delay = Number(slider.value);
    get('delay-output').textContent = delay + (delay === 1 ? ' day' : ' days');
    get('scenarios').replaceChildren();
    for (const s of data.scenarios.filter(s => s.delay_days === delay)) {
        row('scenarios',[names.get(s.sku),show(s.unmet_units),show(s.incremental_unmet),show(s.first_stockout_day)]);
    }
}
slider.addEventListener('input',renderScenario);
renderScenario();
for (const a of data.alerts) {
    const item = document.createElement('li');
    const heading = document.createElement('strong');
    const detail = document.createElement('span');
    heading.textContent = names.get(a.sku)+' · '+a.code.replaceAll('_',' ');
    detail.textContent = a.message;
    item.append(heading,detail);
    get('alerts').append(item);
}
if (!data.alerts.length) get('alerts').textContent = 'No thresholds crossed.';

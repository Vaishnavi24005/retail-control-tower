# Ten-minute speaker guide

| Slide | Time | Talking points |
|---|---:|---|
| Retail Control Tower | 0:45 | A retailer needs a shared view of stock, delivery reliability, and shortages. Explain the operating decision the tool supports. |
| Architecture | 1:20 | Show the hourly Airflow trigger, the Python pipeline and the atomic PostgreSQL refresh. Explain the roles of Superset and SMTP. |
| Inventory and suppliers | 1:10 | Define the stock-out, on-time, lead-time, and inventory coverage measures. Point out the low-cover cold brew SKU. |
| Forecast validation | 1:20 | Describe the 14-day holdout, WAPE denominator, weekday baseline, and Prophet. Explain the effect of an injected demand spike. |
| Delay scenario | 1:35 | Switch between baseline and seven days in the demo. Discuss paper filters and cold brew. Explain why lost sales and timing can change even when a receipt still arrives in the horizon. |
| Alerts | 1:05 | Describe the matching-weekday and shipment baselines. Explain the delivery delay and demand-spike examples and optional email digest. |
| Verification and limits | 1:15 | Explain boundary tests and repeatable data. Discuss independent simulated feeds and the need for a live service test. |
| Next steps | 1:30 | Propose real feed reconciliation, service deployment, and a review of alert precision and replenishment response. |

Total speaking time is 10:00.

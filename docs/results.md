# Results and verification

The dashboard snapshot uses Prophet 1.5.0 on simulated data as of 13 November 2026 at 12:00 UTC. The run included four SKUs, three suppliers, 336 completed daily demand rows, 48 deliveries and 672 hourly inventory observations.

| Measure | Result |
|---|---:|
| Total on-hand units | 382 |
| On-time deliveries | 38 of 48 (79.2%) |
| Stock-out rate | 37 of 672 observations (5.5%) |
| Prophet 14-day holdout WAPE | 12.09% |
| Weekday-average holdout WAPE | 12.30% |
| Extra unmet demand with seven-day delay | 123.77 units |

Paper filters add 69.42 unmet units under a seven-day inbound delay despite having 7.68 days of inventory. Cold brew has 1.77 days of inventory and adds 43.09 unmet units under the same scenario. In a simulated response, prioritize the cold brew shortage by time and investigate whether paper filters can be moved forward by quantity. Confirm those choices with real orders and transfer costs before using the dashboard operationally.

Three alerts fired. Cold brew showed a demand spike and low coverage. Oat milk showed an eight-day delay on the latest simulated receipt.

The four local tests passed. They cover receipt timing and lost sales, repeatable feeds, an anomaly baseline with zero variance, and fixture counts and expected alerts. The Prophet run successfully generated forecasts and 32 SKU/delay combinations. The forecast comparison uses one synthetic holdout. It does not estimate real-world forecast error. The supplied GitHub workflow exercises PostgreSQL when run. Airflow scheduling, Superset chart setup, and SMTP delivery require configured services.

# Apache Superset dashboard setup

Connect Superset to the PostgreSQL service after running a refresh. Give its database user read access to the `tower` schema. Use a host reachable from the Superset server and keep the database connection string in Superset's connection settings.

Create physical datasets for `tower.product_kpi`, `tower.supplier_kpi`, `tower.forecast`, `tower.delay_panel`, and `tower.alert`. Build and save the following charts.

| Chart | Dataset | Superset controls |
|---|---|---|
| Inventory coverage | product_kpi | Table with SKU, product, on hand, seven-day forecast, days of inventory and stock-out rate. Sort by lowest coverage. |
| Supplier delivery | supplier_kpi | Table with supplier, delivered shipments, on-time rate and mean lead days. Sort by lowest on-time rate. |
| Forecast demand | forecast | Time-series line chart, day on the time axis, SKU as series and SUM(units) as the metric. |
| Delay scenario | delay_panel | Table with product, delay_days, unmet_units, incremental_unmet, first_stockout_day and ending_stock. |
| Active exceptions | alert | Table with SKU, code and message. |

Add the five charts to a dashboard called **Retail Control Tower**. Add a single-select native filter using the delay_panel dataset and delay_days column. Set the default to 7 and scope it only to the delay scenario chart. Set the filter to require a value. Switching to 0 shows the baseline. Use a Table chart in raw-record mode to avoid totaling multiple scenarios for a SKU.

The static demo exposes the same eight scenarios without a Superset installation. [Superset documentation](https://superset.apache.org/docs/intro)

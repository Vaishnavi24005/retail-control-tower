# Retail and Supply Chain Control Tower

Monitor inventory, supplier performance, and demand risk from a simulated retail feed. The dashboard compares current stock with forecast demand and lets you delay incoming shipments by up to seven days to see the effect on shortages.

## Interactive demo

Open [demo/index.html](demo/index.html) after downloading or cloning the repository. The page loads its data locally. Run the tests and regenerate the snapshot with Python 3.12:

```sh
python -m unittest discover -s tests -v
python tower.py demo
```

The default command uses a dependency-free weekday benchmark. To regenerate using Prophet, install the warehouse requirements and run `python tower.py demo --method prophet`. The dashboard labels the forecast method.

## Run PostgreSQL and the hourly refresh

1. Set `TOWER_DB_PASSWORD` in a local `.env` and run `docker compose up -d postgres`.
2. Create a Python 3.12 environment and install `pip install -r requirements.txt`.
3. Set `TOWER_DSN` in your environment, for example `postgresql://tower:<password>@localhost:5432/tower`. URL-encode special characters in the password.
4. Run `python tower.py refresh`. It initializes tables and loads the simulated snapshot with Prophet forecasts.
5. On an existing Apache Airflow 3 installation, add `dags/control_tower.py` to the DAG folder. Make this repository available on every worker's `PYTHONPATH`, install the requirements there, and set `TOWER_DSN` on the workers. Unpause `retail_control_tower` for an hourly UTC schedule. Use a hostname reachable by the worker.
6. Follow the [Superset dashboard guide](docs/superset.md) to connect a reporting account and build the operations and scenario views.

For opt-in email alerts, set `TOWER_SMTP_HOST`, `TOWER_SMTP_PORT` (defaults to 587), `TOWER_SMTP_FROM`, `TOWER_SMTP_TO`, and SMTP credentials `TOWER_SMTP_USER` and `TOWER_SMTP_PASSWORD` if required. Use a STARTTLS-capable SMTP server. Run `python tower.py refresh --notify` or set `TOWER_NOTIFY=1` on Airflow workers. Credentials belong in local environment variables or your deployment's secret store.

## Submission material

- [Architecture, data dictionary, and metrics](docs/architecture.md)
- [Measured results and validation](docs/results.md)
- [Ten-minute presentation](docs/Retail-Control-Tower.pptx) and [speaker guide](docs/presentation.md)
- [Individual reflection prompts](docs/reflection.md)

For GitHub Pages, configure GitHub Actions as the Pages source and dispatch **Deploy demo**. The workflow publishes the static snapshot and scenario controls.

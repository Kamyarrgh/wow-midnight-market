# WoW Midnight Market

A self-hosted dashboard for tracking **World of Warcraft auction-house material prices**.
It polls the market on a schedule, stores every price snapshot in PostgreSQL, and renders
current buyout prices, quantities, and trend analytics in a local web UI.

Built as a small, fully containerized stack — one `docker compose up` and it runs.

---

## What it does

- **Scheduled collection** — a background collector polls auction data at a configurable
  interval (default: hourly).
- **Price history** — every snapshot is persisted, so you can track how a material's price
  moved over time rather than only seeing the current listing.
- **Analytics** — aggregates and signals over stored snapshots (min buyout, quantity,
  deltas between snapshots).
- **Web UI** — current prices formatted for readability, with a "last updated" indicator
  so you know how fresh the data is.
- **Region-aware** — price data is scoped by region, so you only see the market you
  actually care about.

---

## Architecture
┌──────────────┐ ┌──────────────┐ ┌──────────────┐

│ frontend │─────▶│ api │─────▶│ db │

│ React + Vite │ /api │ FastAPI │ SQL │ PostgreSQL │

└──────────────┘ └──────┬───────┘ └──────────────┘

                        │

                        │ scheduled poll

                        ▼

              ┌──────────────────┐

              │ collector │──────▶ external auction API

              └──────────────────┘


Service	Role	Stack
frontend	Web UI	React, Vite, Tailwind CSS
api	REST endpoints, collector scheduling	FastAPI, SQLAlchemy
db	Snapshot + material storage	PostgreSQL
collector	Polls the auction API on an interval	Python
The frontend talks to the API through a Vite dev-server proxy, so the browser only ever

issues same-origin /api/... requests — no CORS configuration needed.

Getting started
Prerequisites
Docker Desktop (with Compose)
An API key for the auction data source
Git
Setup
bash

git clone https://github.com/YOUR-USERNAME/wow-midnight-market.git

cd wow-midnight-market

Create a .env file in the project root:

dotenv

---- required ----
UNDERMINE_API_KEY=your_api_key_here

WOW_REGION=eu

DATABASE_URL=postgresql://wow:wow@db:5432/wow_market

---- optional ----
How often the collector polls, in hours
COLLECTOR_INTERVAL_HOURS=1

⚠️ .env is git-ignored. Never commit it. Use the placeholder values above —

they contain no real secrets, and the app reads them at startup.

Then:

bash

docker compose up -d --build

Access

Service	URL
Web UI	http://localhost:5173
API	http://localhost:8000
On first run the database is empty. The collector populates it on its first interval —

price charts and analytics appear once at least one snapshot has been stored.

Configuration
All configuration lives in .env and is read by the backend at startup.


Variable	Required	Default	Description
UNDERMINE_API_KEY	✅	—	API key for the auction data source
WOW_REGION	✅	—	Region to collect, e.g. eu or us
DATABASE_URL	✅	—	PostgreSQL connection string
COLLECTOR_INTERVAL_HOURS	❌	1	Hours between collection runs
⚠️ WOW_REGION must match the region present in your stored snapshots. If they

disagree, the UI will show empty or zeroed prices — the data exists, but the query is

scoped to a different region.

API

Method	Endpoint	Description
GET	/api/health	Service status and configured region
GET	/api/materials	Tracked materials with current price and quantity
GET	/api/materials/{item_id}/history	Price history for one material
Project structure
wow-midnight-market/

├── backend/

│ ├── app/

│ │ ├── main.py # FastAPI app, startup, collector schedule

│ │ ├── config.py # env-var settings

│ │ ├── models.py # ORM models

│ │ ├── db.py # session / engine

│ │ ├── collector.py # scheduled price collection

│ │ ├── undermine.py # external auction API client

│ │ ├── signals.py # analytics / signals

│ │ └── stats.py # aggregations

│ ├── materials.JSON # tracked material definitions

│ ├── requirements.txt

│ └── Dockerfile

├── frontend/

│ ├── src/

│ │ ├── App.jsx # main dashboard

│ │ ├── main.jsx

│ │ └── index.css

│ ├── vite.config.js # dev server + /api proxy

│ ├── tailwind.config.js

│ └── Dockerfile

├── docker-compose.yml

├── .gitignore

└── README.md

Roadmap
[ ] Move the API key out of .env and into Docker secrets
[ ] Replace print() calls with structured logging
[ ] Add a composite index on snapshots (region, created_at) for scale
[ ] Tests for the collector and analytics paths

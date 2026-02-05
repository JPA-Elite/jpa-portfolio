# My Portfolio App

A personal portfolio web app built with Flask.

## Tech Stack

- Python / Flask
- MongoDB
- HTML / CSS / JavaScript

## Setup

### 1) Create a virtual environment

```bash
python -m venv .venv
```

### 2) Activate the virtual environment

- **Windows (cmd):**

```bat
.\.venv\Scripts\activate.bat
```

- **Linux / macOS (bash/zsh):**

```bash
source .venv/bin/activate
```

### 3) Install dependencies

```bash
cd backend && pip install -r requirements.txt
```

Or from the project root:

```bash
make package-install
```

## Run the app

From the project root:

```bash
make start-local
```

`start-local` uses Flask debug reloader, so code changes auto-reload during development.

Alternative (also supports auto-reload):

```bash
FLASK_DEBUG=1 python -m backend.app
```

## Run tests

From the project root:

```bash
pytest -q
```

Additional useful checks:

```bash
ruff check backend tests
python -m compileall -q backend
```

## Language translation commands

Run inside `backend/`:

```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel init -i messages.pot -d translations -l ceb
pybabel init -i messages.pot -d translations -l en
pybabel compile -d translations
```


## Trusted network access (optional for deployment)

To restrict site access in deployed environments to trusted networks/IPs:

```bash
ENFORCE_TRUSTED_NETWORK=1
TRUSTED_IPS=203.0.113.10,198.51.100.7
TRUSTED_CIDRS=203.0.113.0/24,198.51.100.0/24
```

Notes:
- Local development is not blocked when debug mode is enabled (`FLASK_DEBUG=1`).
- Requests outside trusted IP/CIDR lists return HTTP `403`.

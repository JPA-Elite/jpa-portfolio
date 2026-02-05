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

Alternative:

```bash
cd backend && python -m backend.app
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

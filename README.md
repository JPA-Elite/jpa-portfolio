# My Portfolio App

Short Description: a project for my own portfolio

Languages: flask (python)

## CREATE A VIRTUAL ENVIRONMENT

1. run command: `python -m venv .venv`
2. run command: `.\.venv\Scripts\activate.bat`

## INSTALL PACKAGE

- `cd backend && pip install -r requirements.txt` or run `make package-install`

## LANGUAGE TRANSLATION COMMANDS

1. `pybabel extract -F babel.cfg -o messages.pot .`
2. `pybabel init -i messages.pot -d translations -l ceb`
3. `pybabel init -i messages.pot -d translations -l en`
4. `pybabel compile -d translations`

## START UP

1. cd fask
2. run command: `cd backend && python -m backend.app`,
   run command: `make start-local` or `make run-local`

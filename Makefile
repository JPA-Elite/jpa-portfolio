# Define variables
APP_NAME := flask_app
DOCKER_IMAGE := flask_image
DOCKERFILE_DIR := .  # Path to the folder containing Dockerfile
PORT := 5000

# Build the Docker image
build:
	docker build -t $(DOCKER_IMAGE) $(DOCKERFILE_DIR)

# Install Package
package-install:
	cd app && if exist ..\.venv\Scripts\python.exe (..\.venv\Scripts\python.exe -m pip install -r requirements.txt) else (py -3.11 -m pip install -r requirements.txt)

# Uninstall Package
package-uninstall:
	cd app && if exist ..\.venv\Scripts\python.exe (..\.venv\Scripts\python.exe -m pip uninstall -r requirements.txt -y) else (py -3.11 -m pip uninstall -r requirements.txt -y)

# Run the Docker container
run:
	docker run -d -e PORT=$(PORT) -p $(PORT):$(PORT) --env-file app/.env --name $(APP_NAME) $(DOCKER_IMAGE)

# Docker build + run
start-build-docker: build run

# Run Docker with live local code (bind-mount ./app, Flask dev server, no page cache)
run-docker-local:
	docker compose -f compose.yaml -f compose.dev.yaml up -d --build

# Stop the live-local Docker setup
stop-docker-local:
	docker compose -f compose.yaml -f compose.dev.yaml down

build-frontend:
	npm run build:frontend

frontend-install:
	npm install

frontend-dev:
	npm run dev:frontend

clean-frontend:
	python -c "import shutil; shutil.rmtree('app/dist/frontend', ignore_errors=True)"

run-local:
	python -m app.app

start-local:
	python -m app.app

# Build frontend assets + run locally using dist
start-local-dist:
	FRONTEND_DIST=1 FRONTEND_DIST_TEMPLATES=1 python -m app.app

# Build frontend assets + run locally using dist (cmd/PowerShell friendly)
start-local-dist-cmd:
	cmd /C "set FRONTEND_DIST=1 && set FRONTEND_DIST_TEMPLATES=1 && python -m app.app"

start-build: build-frontend start-local-dist-cmd

dev:
	npm run dev

# Run Flask with Vite dev server assets (same-origin via proxy)
start-local-vite:
	VITE_DEV_SERVER=http://127.0.0.1:5173 python -m app.app

start-local-vite-cmd:
	cmd /C "set VITE_DEV_SERVER=http://127.0.0.1:5173 && python -m app.app"

# Stop the Docker container
stop:
	docker stop $(APP_NAME)

# Remove the Docker container
remove:
	docker rm $(APP_NAME)

# Restart the Docker container
restart: stop remove run

# Remove the Docker image
remove-image:
	docker rmi $(DOCKER_IMAGE)

# Clean up stopped containers and unused images
clean:
	docker system prune -f

# Run the Flask app in Docker using bash
shell:
	docker exec -it $(APP_NAME) /bin/bash

# Compile the translations
compile-translations:
	cd app && pybabel compile -d translations

# Run unit tests (controllers/services/repositories)
test:
	set FLASK_ENV= && python -W ignore::DeprecationWarning scripts/run_tests.py

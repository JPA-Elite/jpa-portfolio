# Define variables
APP_NAME := flask_app
DOCKER_IMAGE := flask_image
DOCKERFILE_DIR := ./backend  # Path to the folder containing Dockerfile
PORT := 5000

# Build the Docker image
build:
	docker build -t $(DOCKER_IMAGE) $(DOCKERFILE_DIR)

# Install Package
package-install:
	cd backend && pip install -r requirements.txt

# Run the Docker container
run:
	docker run -d -p $(PORT):5000 --name $(APP_NAME) $(DOCKER_IMAGE)

run-local:
	python -m backend.app

start-local:
	python -m backend.app

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
	cd backend && pybabel compile -d translations

# Run unit tests (controllers/services/repositories)
test:
	set FLASK_ENV= && python -W ignore::DeprecationWarning -m unittest discover -s tests -p "test_*.py"

# for render services
# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Install required packages
RUN apt-get update -qq \
      && apt-get install -y --no-install-recommends \
      build-essential \
      python3-dev \
      libgl1 \
      # libgl1-mesa-glx \ #deprecated
      libglib2.0-0 \
      nodejs \
      npm \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy only requirements first to leverage Docker cache
COPY ./backend/requirements.txt /app/

# Install dependencies inside the venv
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build config and install node deps
COPY ./package.json /app/
COPY ./vite.config.mjs /app/
RUN npm install

# Copy the rest of the app
COPY . /app

# Build frontend assets for hashed filenames
RUN npm run build:frontend

# Serve built frontend assets + templates by default
ENV FRONTEND_DIST=1
ENV FRONTEND_DIST_TEMPLATES=1

# Expose the port
EXPOSE 8080

# IMPORTANT: bind to :$PORT (Cloud Run injects PORT=8080)
CMD ["sh", "-c", "gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 backend.app:app"]

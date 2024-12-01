FROM python:3.11-slim

WORKDIR /app

# Install required system packages including dependencies for OpenCV
RUN apt-get update -qq \
      && apt-get install -y --no-install-recommends \
      build-essential \
      python3-dev \
      libgl1 \
      libgl1-mesa-glx \
      libglib2.0-0 \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container
COPY . /app

# Install the Python dependencies from the requirements.txt file
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Flask will run on
EXPOSE 5000

# Command to run your app
CMD ["python", "app.py"]

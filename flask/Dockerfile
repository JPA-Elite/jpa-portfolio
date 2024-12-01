FROM python:3.11-slim

WORKDIR /app

# Install required packages
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
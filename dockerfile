FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

WORKDIR /app

# Copy python dependencies first for better caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the repository
COPY . /app

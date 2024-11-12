# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /tautaras_worker

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the entrypoint for the container to start the Celery worker
ENTRYPOINT ["celery", "-A", "tasks", "worker", "--loglevel=info"]
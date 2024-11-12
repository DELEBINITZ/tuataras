# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /tautaras_server

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install the dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Set the default command to run the app (adjust if your app requires something else)
CMD ["python", "main.py", "--port", "80"]

# Expose the port the app runs on
EXPOSE 80

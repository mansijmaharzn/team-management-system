# Use the official Python image from the Docker Hub with Python 3.11
FROM python:3.11-slim

# Install the PostgreSQL development libraries
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run migrations and start the server (no need if using docker-compose.yml)
CMD ["sh", "-c", "cd team_mgmt_sys && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

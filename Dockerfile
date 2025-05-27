# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Add src to PYTHONPATH
ENV PYTHONPATH=/app/src

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Make port 8080 available to the world outside this container (for HTTP)
EXPOSE 8080
# Make port 7777 available for WebSocket
EXPOSE 7777

# Define environment variables for application configuration
# These can be overridden at runtime (e.g., by docker-compose)
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REDIS_DB=0
ENV HTTP_PORT=8080
ENV WEBSOCKET_PORT=7777
ENV LIVEAPI_CONFIG_PATH=/app/config.json

# Run main.py when the container launches
CMD ["python", "src/main.py"]

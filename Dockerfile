# Start from an official lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
# Everything from here on happens in /app
WORKDIR /app

# Copy requirements first (before the rest of the code)
COPY app/requirements.txt .

# Install dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual app code
COPY app/server.py .

# Tell Docker this container listens on port 5000
EXPOSE 5000

# The command that runs when the container starts
CMD ["python3", "server.py"]
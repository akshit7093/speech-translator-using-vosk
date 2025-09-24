# Use official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LOCAL_DATA=/app/local_data

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Ensure entrypoint.sh has execute permissions
RUN ["chmod", "+x", "/app/entrypoint.sh"]

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
CMD ["python", "app.py"]

# Expose port
EXPOSE 5000
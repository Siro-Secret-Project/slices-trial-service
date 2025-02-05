# Use an official Python base image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and enable buffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /slices-trial-service

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Install watchfiles for auto-reload
RUN pip install --no-cache-dir watchfiles

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application with watchfiles for auto-reload
CMD ["watchfiles", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

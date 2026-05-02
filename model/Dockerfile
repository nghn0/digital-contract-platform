FROM python:3.10-slim

WORKDIR /app

# Disable telemetry explicitly to fix Posthog/Chroma errors
ENV ANONYMIZED_TELEMETRY=False
ENV CHROMA_TELEMETRY_ENABLED=FALSE

# Install system dependencies (required for some python packages like building C extensions or grpc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download the spacy model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application code
COPY . .

# Expose the gRPC port
EXPOSE 50051

# Command to run the gRPC server
CMD ["python", "grpc_server.py"]

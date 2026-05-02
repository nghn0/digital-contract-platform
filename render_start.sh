#!/bin/bash

# Exit on any failure
set -e

echo "🚀 Booting All-In-One Render Container..."

# 1. Start the Python gRPC server in the background
echo "Starting Python gRPC server..."
export GRPC_PORT=50051
cd /app/model && python grpc_server.py &

# Wait a few seconds to let gRPC boot up
sleep 3

# 2. Start the Node.js backend
echo "Starting Node.js Backend..."
export MODEL_GRPC_URL="127.0.0.1:50051"
# Ensure Node uses the Render-assigned PORT (defaults to 5001 if missing)
export PORT=${PORT:-5001}
cd /app/backend && node server.js

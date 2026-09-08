#!/bin/bash

# Start the FastAPI backend in the background on port 8000
echo "Starting FastAPI backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait a moment to ensure the backend is up
sleep 3

# Start the Streamlit frontend in the foreground
# Streamlit will bind to $PORT if Render provides it, otherwise default to 8501
PORT=${PORT:-8501}
echo "Starting Streamlit frontend on port $PORT..."
streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0

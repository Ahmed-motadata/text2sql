#!/bin/bash

# Exit on error
set -e

# Get the absolute path to the project root
PROJECT_ROOT="/home/ahmedraza/Motadata/text2sql"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to kill process on a port
kill_port() {
    local port=$1
    echo "Checking for processes on port $port..."
    if lsof -i :$port > /dev/null; then
        echo "Killing process on port $port..."
        sudo fuser -k $port/tcp || true
        sleep 2
    fi
}

# Function to cleanup background processes
cleanup() {
    echo "Cleaning up processes..."
    kill $(jobs -p) 2>/dev/null || true
    kill_port 5001
    kill_port 3001
    exit 0
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Check if npm is installed
if ! command_exists npm; then
    echo "Error: npm is not installed"
    exit 1
fi

# Check if directories exist
if [ ! -d "$PROJECT_ROOT/backend" ]; then
    echo "Error: Backend directory not found at $PROJECT_ROOT/backend"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/frontend" ]; then
    echo "Error: Frontend directory not found at $PROJECT_ROOT/frontend"
    exit 1
fi

# Check if .env file exists in backend
if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
    echo "Warning: .env file not found in backend directory"
    echo "Please ensure your database configuration is set up correctly"
fi

# Kill any existing processes on required ports
kill_port 5001
kill_port 3001

# Start backend service
echo "Starting backend service..."
cd "$PROJECT_ROOT/backend" || exit 1
npm install || { echo "Failed to install backend dependencies"; exit 1; }

# Start backend with retry mechanism
start_backend() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt to start backend..."
        npm run dev &
        BACKEND_PID=$!
        
        # Wait for backend to initialize
        sleep 5
        
        # Check if backend is running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "Backend started successfully"
            return 0
        else
            echo "Backend failed to start, retrying..."
            kill_port 5001
            attempt=$((attempt + 1))
            sleep 2
        fi
    done
    
    echo "Error: Backend failed to start after $max_attempts attempts"
    return 1
}

if ! start_backend; then
    exit 1
fi

# Start frontend service
echo "Starting frontend service..."
cd "$PROJECT_ROOT/frontend" || exit 1
npm install || { echo "Failed to install frontend dependencies"; exit 1; }

# Start frontend with retry mechanism
start_frontend() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt to start frontend..."
        npm run dev &
        FRONTEND_PID=$!
        
        # Wait for frontend to initialize
        sleep 5
        
        # Check if frontend is running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "Frontend started successfully"
            return 0
        else
            echo "Frontend failed to start, retrying..."
            kill_port 3001
            attempt=$((attempt + 1))
            sleep 2
        fi
    done
    
    echo "Error: Frontend failed to start after $max_attempts attempts"
    return 1
}

if ! start_frontend; then
    kill $BACKEND_PID
    exit 1
fi

echo "Both services started successfully"
echo "Frontend running at http://localhost:3001"
echo "Backend running at http://localhost:5001"
echo "Press Ctrl+C to stop all services"

# Keep script running and show logs
wait
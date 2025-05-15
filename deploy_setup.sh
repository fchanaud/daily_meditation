#!/bin/bash
# Pre-deployment setup script
set -e  # Exit on error

echo "Starting pre-deployment setup..."

# Display Python version
echo "Python version:"
python3 --version

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run Supabase connection test
echo "Testing Supabase connection..."
python test_supabase.py

# Basic health check
echo "Running basic health check..."
if [ -f "main.py" ]; then
  echo "main.py exists ✓"
else
  echo "ERROR: main.py not found!"
  exit 1
fi

if [ -f "app/api/app.py" ]; then
  echo "app/api/app.py exists ✓"
else
  echo "ERROR: app/api/app.py not found!"
  exit 1
fi

if [ -f "app/utils/db.py" ]; then
  echo "app/utils/db.py exists ✓"
else
  echo "ERROR: app/utils/db.py not found!"
  exit 1
fi

# Environment variables check
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
  echo "WARNING: Supabase environment variables not set."
  echo "Make sure to configure them in your deployment environment."
else
  echo "Supabase environment variables found ✓"
fi

echo "Pre-deployment setup completed successfully" 
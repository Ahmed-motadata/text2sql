#!/bin/bash
# Run the Streamlit Text2SQL Application

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install any missing dependencies
pip install -r requirements.txt

# Run the Streamlit app
cd "$(dirname "$0")"
streamlit run ui/app.py
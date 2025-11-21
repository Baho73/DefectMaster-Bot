#!/bin/bash

echo "Starting DefectMaster Bot..."
echo ""

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then run: source venv/bin/activate"
    echo "Then run: pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in the values"
    exit 1
fi

# Run the bot
python main.py

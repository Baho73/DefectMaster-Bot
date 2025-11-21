#!/bin/bash

echo "DefectMaster Bot - Setup Script (Linux/Mac)"
echo "============================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found! Please install Python 3.10+"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Please edit .env file and fill in your API keys!"
fi

# Make start script executable
chmod +x start.sh

echo ""
echo "============================================="
echo "Setup completed successfully!"
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Place service-account.json in the project root"
echo "3. Run: ./start.sh"
echo ""

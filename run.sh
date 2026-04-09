#!/bin/bash
# Inventory Management System startup script

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating..."
    uv venv .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Run the application
python main.py

#!/bin/bash

# Set environment variables for WeasyPrint
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="/opt/homebrew/bin:$PATH"

# Activate virtual environment
source venv/bin/activate

# Run the application
python app.py 
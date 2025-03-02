#!/bin/bash

# Navigate to bot directory
cd /app

# Activate virtual environment (if it exists)
if [ -d "trading_bot_env" ]; then
    source trading_bot_env/bin/activate
fi

# Run bot
python trading_bot.py


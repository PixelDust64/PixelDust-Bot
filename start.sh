#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    ./venv/bin/pip install -r req.txt
fi

source venv/bin/activate
python bot.py

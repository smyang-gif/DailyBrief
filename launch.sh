#!/bin/bash
cd "/Users/mare/Projects/DailyBrief"
source "/Users/mare/Projects/DailyBrief/venv/bin/activate"
python3 app.py > /tmp/dailybrief.log 2>&1

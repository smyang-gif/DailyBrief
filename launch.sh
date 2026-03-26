#!/bin/bash
cd "/Users/mare/Documents/_Tools/DailyBrief"
export PYTHONPATH="/Users/mare/Documents/_Tools/DailyBrief/venv/lib/python3.9/site-packages"
/usr/bin/python3 app.py > /tmp/dailybrief.log 2>&1

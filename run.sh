#!/bin/bash
set -e

BOT_DIR="/home/duck/Yuuri-Bot"
venv="$BOT_DIR/venv"

cd "$BOT_DIR"
echo  "Setting up virtual environment..."
source "$VENV/bin/activate"
while true
do
  echo "Updating Yuuri Bot..."
  git pull
  pip install -r requirements.txt --upgrade --quiet

  echo "Bot is starting..."
  python3 main.py

  echo "Bot has stopped. Most likely due to an update, Restarting in 3 seconds."
  sleep 3
  done

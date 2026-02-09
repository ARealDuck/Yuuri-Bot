#!/bin/bash
set -e #exit if script fails for any reason

#set variables
BOT_DIR="/home/duck/Yuuri-Bot"
VENV="$BOT_DIR/venv"
LOG_FILE="$BOT_DIR/bot.log"

#redirect stdout and stderr to log file
exec >> "$LOG_FILE" 2>&1

#start script
cd "$BOT_DIR"

#create Venv environment if it does not exist.
if [ ! -d "$VENV"]; then
  echo "VENV not found creating new venv environment."
  python3 -m venv "$VENV"
fi

#activate Venv environment
echo  "Setting up virtual environment..."
source "$VENV/bin/activate"

#run auto update loop for the bot.
while true
do
  echo "Updating Yuuri Bot..."
  git pull
  REQ_HASH_FILE="$VENV/.req_hash"
  CURRENT_HASH=$(sha256sum requirements.txt | awk '{print $1}')
  PREV_HASH=''
  if [ -f "$REQ_HASH_FILE" ]; then
    PREV_HASH=$(cat "$REQ_HASH_FILE")
  fi

  if [ "$CURRENT_HASH" != "$PREV_HASH" ]; then
    echo "Installing / updating dependencies..."
  pip install -r requirements.txt --upgrade --quiet
    echo "$CURRENT_HASH" > "$REQ_HASH_FILE"
  else
    echo "Dependencies are up to date, Skipping."
  fi

  echo "Bot is starting..."
  python3 main.py

  echo "Bot has stopped. Most likely due to an update, Restarting in 3 seconds."
  sleep 3
  done

#!/bin/bash

while true
do
  echo "Checking for updates..."
  git pull
  pip install -r requirements.txt

  echo "Bot is starting..."
  python3 main.py

  echo "Bot has stopped. Most likely due to an update, Restarting in 3 seconds."
  sleep 3
  done

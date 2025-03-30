#!/usr/bin/env bash
# Exit on error
set -o errexit

#!/bin/bash
# Define installation directory
CHROME_DIR="/opt/render/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download Chrome (Prebuilt Binary)
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O chrome.deb
dpkg-deb -x chrome.deb $CHROME_DIR
mv $CHROME_DIR/opt/google/chrome/google-chrome $CHROME_DIR/google-chrome

# Download ChromeDriver (Manually match version)
CHROME_VERSION=$($CHROME_DIR/google-chrome --version | grep -oP '[0-9.]+' | head -1)
wget -q "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip" -O chromedriver.zip
unzip chromedriver.zip
mv chromedriver-linux64/chromedriver $CHROME_DIR/chromedriver
chmod +x $CHROME_DIR/chromedriver


pip install --upgrade pip
# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate
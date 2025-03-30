#!/usr/bin/env bash
# Exit on error
set -o errexit

#!/bin/bash
# Define installation directory
CHROME_DIR="/opt/render/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download Chrome (Prebuilt Binary)
CHROME_DIR="/opt/render/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download precompiled Chrome (NOT a .deb package)
wget -q https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.199/linux64/chrome-linux64.zip -O chrome.zip
unzip chrome.zip
mv chrome-linux64/chrome $CHROME_DIR/google-chrome
chmod +x $CHROME_DIR/google-chrome

# Download ChromeDriver (Match Chrome version manually)
wget -q https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.199/linux64/chromedriver-linux64.zip -O chromedriver.zip
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
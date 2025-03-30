#!/usr/bin/env bash
# Exit on error
set -o errexit

mkdir -p /opt/render/chrome/
cd /opt/render/chrome/

# Download and extract Chrome
mkdir -p /opt/render/chrome/
cd /opt/render/chrome/

# Download & extract Chrome (precompiled binary)
wget -q https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_120.0.6099.199-1_amd64.deb -O chrome.deb
dpkg-deb -x chrome.deb .
mv opt/google/chrome/google-chrome /opt/render/chrome/google-chrome

# Download ChromeDriver (match version manually)
wget -q https://storage.googleapis.com/chrome-for-testing-public/120.0.6099.199/linux64/chromedriver-linux64.zip -O chromedriver.zip
unzip chromedriver.zip
mv chromedriver-linux64/chromedriver /opt/render/chrome/chromedriver
chmod +x /opt/render/chrome/chromedriver

pip install --upgrade pip
# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate
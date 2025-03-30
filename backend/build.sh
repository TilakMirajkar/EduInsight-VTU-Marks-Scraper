#!/usr/bin/env bash
# Exit on error
set -o errexit

mkdir -p /opt/render/chrome/
cd /opt/render/chrome/

# Download and extract Chrome
wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > chrome.deb
ar x chrome.deb
tar -xf data.tar.xz
mv usr/bin/google-chrome-stable /opt/render/chrome/google-chrome

# Download ChromeDriver (version must match Chrome)
CHROME_VERSION=$(./google-chrome --version | grep -oP '[0-9.]+' | head -1)
wget -q "https://chromedriver.storage.googleapis.com/$CHROME_VERSION/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /opt/render/chrome/chromedriver

pip install --upgrade pip
# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate
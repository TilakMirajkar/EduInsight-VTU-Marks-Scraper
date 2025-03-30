#!/usr/bin/env bash
# Exit on error
set -o errexit

apt-get update
apt-get install -y \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils

# Define installation directory
CHROME_DIR="/opt/render/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download Chrome (Prebuilt Binary)
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O chrome.deb
dpkg-deb -x chrome.deb $CHROME_DIR

# Move Chrome binary to the correct location
if [ -f "$CHROME_DIR/opt/google/chrome/google-chrome" ]; then
    mv $CHROME_DIR/opt/google/chrome/google-chrome $CHROME_DIR/
else
    echo "Chrome binary not found!"
    exit 1
fi

# Download ChromeDriver (Manually match version)
CHROME_VERSION=$($CHROME_DIR/google-chrome --version | grep -oP '[0-9.]+' | head -1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O chromedriver.zip
unzip chromedriver.zip
mv chromedriver $CHROME_DIR/chromedriver
chmod +x $CHROME_DIR/chromedriver

# Check if ChromeDriver exists
if [ ! -f "$CHROME_DIR/chromedriver" ]; then
    echo "ChromeDriver not found!"
    exit 1
fi

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate
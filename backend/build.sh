#!/usr/bin/env bash
# Exit on error
set -o errexit

# Define installation directory
CHROME_DIR="/opt/render/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download Chrome (Prebuilt Binary)
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O chrome.deb
dpkg-deb -x chrome.deb $CHROME_DIR

# Check if Chrome binary exists
if [ ! -f "$CHROME_DIR/opt/google/chrome/google-chrome" ]; then
    echo "Chrome binary not found!"
    exit 1
fi

# Move Chrome binary
mv $CHROME_DIR/opt/google/chrome/google-chrome $CHROME_DIR/
ls $CHROME_DIR  # Debugging output

# Download ChromeDriver (Manually match version)
CHROME_VERSION=$($CHROME_DIR/google-chrome --version | grep -oP '[0-9.]+' | head -1)
wget -q "https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip" -O chromedriver.zip
unzip chromedriver.zip
mv chromedriver-linux64/chromedriver $CHROME_DIR/chromedriver
chmod +x $CHROME_DIR/chromedriver

# Check if ChromeDriver exists
if [ ! -f "$CHROME_DIR/chromedriver" ]; then
    echo "ChromeDriver not found!"
    exit 1
fi

pip install --upgrade pip
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate
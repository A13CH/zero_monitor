# Setup commands to enable I2C on Raspberry Pi

# sudo raspi-config
# Navigate to Interface Options (or “Interfacing Options”) → I2C → Choose “Yes” to enable it → allow it to automatically load kernel modules.
# sudo reboot 

# Install necessary libraries

# sudo apt update
# sudo apt install python3-pip python3-dev
# sudo pip3 install Adafruit-SSD1306
# sudo apt install python3-Pillow

# Connections:
# Raspberry Pi GPIO 2 (SDA) -> OLED SDA
# Raspberry Pi GPIO 3 (SCL) -> OLED SCL
# Raspberry Pi GND -> OLED GND
# Raspberry Pi 3.3V -> OLED VCC

import time
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306

display = Adafruit_SSD1306.SSD1306_128_64(rst=None)

# Initialize
display.begin()
display.clear()
display.display()

# Get display dimensions
width = display.width
height = display.height

# Create image buffer (1-bit color)
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Load default font
font = ImageFont.load_default()

# Write some text
draw.text((0, 0), "Hello, World!", font=font, fill=255)
draw.text((0, 20), "Line 2 text", font=font, fill=255)

# Display the image buffer
display.image(image)
display.display()

time.sleep(5)

# Clear and exit
display.clear()
display.display()

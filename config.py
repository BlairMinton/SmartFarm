# config.py
# Central configuration file — update this file with your own credentials and wiring before running main.py

# ── Wi-Fi credentials ─────────────────────────────────────────────────────────
WIFI_SSID     = "CyFi"  # Name of your Wi-Fi network
WIFI_PASSWORD = "SecurityA40"             # Password for your Wi-Fi network

# ── Supabase credentials ──────────────────────────────────────────────────────
# Copy these from Project Settings → API in the Supabase dashboard
SUPABASE_URL   = "https://xpyilzprpomzultikekk.supabase.co"  # Your project URL
SUPABASE_KEY   = "sb_publishable_R0tmuL3xh3obJQqJ_Yl5Vw_O8dqze3p"  # Your anon/public API key
TABLE_SENSORS  = "mod2_sensor_data"                            # Name of the sensor data table              
TABLE_SETTINGS = "mod2_settings"                                # Name of the settings table

# ── Pin Definitions ───────────────────────────────────────────────────────────
# Digital input sensors
PIN_PIR    = 23         # io23 — PIR Motion Sensor
PIN_BUTTON = 5          # io5  — Push Button (PULL_UP)

# Ultrasonic distance sensor (HC-SR04)
PIN_TRIG = 12           # D12  — Trigger pin (output pulse)
PIN_ECHO = 13           # D13  — Echo pin (measures return time)

# I2C bus for LCD display
I2C_SDA = 21            # I2C data line
I2C_SCL = 22            # I2C clock line

# DHT11 temperature and humidity sensor
PIN_DHT = 17            # io17 — DHT11 data pin

# Analogue sensors (ADC input-only pins)
PIN_STEAM       = 35    # io35 — Steam / Rain Sensor
PIN_PHOTO       = 34    # io34 — Photoresistor / Light Sensor
PIN_WATER_LEVEL = 33    # io33 — Water Level Sensor
PIN_SOIL        = 32    # io32 — Soil Moisture Sensor

# Output devices
PIN_BUZZER = 16         # io16 — Buzzer
PIN_LED   = 27          # io27 — LED indicator


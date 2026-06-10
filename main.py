# main.py — ESP32 MicroPython
# Entry point: sets up hardware, connects to Wi-Fi, then loops reading sensors and syncing with Supabase
import network   # Wi-Fi management
import time      # Delays and timing
import ujson     # JSON encoding/decoding
import urequests  # HTTP requests for API communication
from machine import Pin, ADC, SoftI2C  # Hardware control classes
from i2c_lcd import I2cLcd            # LCD display driver
from dht import DHT11              # DHT11 temperature/humidity driver
from config import (
    WIFI_SSID, WIFI_PASSWORD,
    PIN_PIR, PIN_BUTTON,
    PIN_TRIG, PIN_ECHO,
    I2C_SDA, I2C_SCL,
    PIN_DHT,
    PIN_STEAM, PIN_PHOTO, PIN_WATER_LEVEL, PIN_SOIL,
    PIN_BUZZER, PIN_LED
)
from supabase_client import post_reading, get_lcd_message, get_light_threshold


# ── Hardware setup ────────────────────────────────────────────────────────────
pir    = Pin(PIN_PIR,    Pin.IN, Pin.PULL_UP)   # PIR motion sensor — reads HIGH when motion detected
button = Pin(PIN_BUTTON, Pin.IN, Pin.PULL_UP)   # Button — LOW when pressed (internal pull-up)

trig = Pin(PIN_TRIG, Pin.OUT)  # Ultrasonic trigger — sends a short pulse to start measurement
echo = Pin(PIN_ECHO, Pin.IN)   # Ultrasonic echo — goes HIGH for the duration of the return pulse

# I2C bus for the LCD display (Bus 0, 400 kHz)
# Construct SoftI2C in a way that is compatible with multiple MicroPython ports
# Some ports accept keyword args `sda`/`scl`, others expect positional Pin args.
try:
    i2c = SoftI2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
except TypeError:
    try:
        i2c = SoftI2C(0, Pin(I2C_SDA), Pin(I2C_SCL), 400000)
    except TypeError:
        i2c = SoftI2C(sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)

# DHT11 sensor object — call .measure() before reading temperature or humidity
dht_sensor = DHT11(Pin(PIN_DHT))

# Analogue sensors — ADC objects read raw 12-bit values (0–4095)
steam       = ADC(Pin(PIN_STEAM))
photo       = ADC(Pin(PIN_PHOTO))
water_level = ADC(Pin(PIN_WATER_LEVEL))
soil        = ADC(Pin(PIN_SOIL))

# ATTN_11DB allows reading voltages up to ~3.6 V (full ESP32 ADC range)
for adc in (steam, photo, water_level, soil):
    adc.atten(ADC.ATTN_11DB)

buzzer = Pin(PIN_BUZZER, Pin.OUT)  # Buzzer — set HIGH to activate
led    = Pin(PIN_LED,    Pin.OUT)  # LED — set HIGH to turn on

lcd = I2cLcd(i2c, 0x27, 2, 16)  # Initialize LCD at I2C address 0x27 with 2 rows and 16 columns

wlan = network.WLAN(network.STA_IF)  # Create a station (client) Wi-Fi interface
wlan.active(False)
time.sleep(0.5)
# ── Wi-Fi ─────────────────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)  # Create a station (client) Wi-Fi interface
    wlan.active(True)                    # Enable the Wi-Fi radio
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connecting to Wi-Fi", end="")
    timeout = 0
    while not wlan.isconnected() and timeout < 15:  # Retry for up to 15 seconds
        print(".", end="")
        time.sleep(1)
        timeout += 1
    if wlan.isconnected():
        print("\nConnected! IP:", wlan.ifconfig()[0])  # Print assigned IP address
    else:
        print("\nFailed to connect. Check SSID and password.")


# ── Sensor readers ────────────────────────────────────────────────────────────
def read_dht11():
    # Trigger a new measurement then return temperature (°C) and humidity (%)
    dht_sensor.measure()
    return dht_sensor.temperature(), dht_sensor.humidity()

def read_ultrasonic():
    # Send a 10 µs trigger pulse to start the HC-SR04 measurement
    trig.value(0)
    time.sleep_us(2)   # Ensure trigger starts clean (LOW)
    trig.value(1)
    time.sleep_us(10)  # 10 µs pulse starts the measurement
    trig.value(0)

    # Wait for the echo pin to go HIGH (pulse start)
    while echo.value() == 0:
        pass
    t_start = time.ticks_us()

    # Wait for the echo pin to go LOW (pulse end)
    while echo.value() == 1:
        pass
    t_end = time.ticks_us()

    # Distance = (travel time / 2) / 29.1 — divides by 2 because sound travels there and back
    duration = time.ticks_diff(t_end, t_start)
    return (duration / 2) / 29.1     # cm

def read_soil():
    # Returns a raw ADC value — higher value = drier soil
    return soil.read()

def read_rain():
    # Returns True if the steam sensor reads above 2000 (indicating moisture/rain)
    return steam.read() > 2000

def read_pir():
    # Returns True if the PIR sensor detects motion
    return bool(pir.value())

def read_button():
    # Returns True if the button is currently pressed
    return not button.value()  # Active LOW


def read_photo():
    # Returns a raw ADC value — higher value = more light
    return photo.read()

def read_led():
    # Returns True if the LED is currently on
    return bool(led.value())



  

# Connect to Wi-Fi before entering the main loop
connect_wifi()

# PIR sensors need ~30 s to stabilise before they give reliable readings
print("Starting in 5s...")
time.sleep(5)  # Shortened for testing; in production, use time.sleep(30)

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    # Step 1 — Read all sensors
    light_level = read_photo()
    led_status = read_led()


    # Print a summary of all current sensor values to the console
    print("\n--- Sensor Reading ---")
    print("Light level: {}".format(light_level))
    print("LED status: {}".format("ON" if led_status else "OFF"))
    

    # Step 2 — POST all sensor values to Supabase (expect status 201)
    print("\n[POST] Sending sensor data...")
    post_reading(light_level, led_status)
    
    '''
    # Step 3 — GET the last 5 records back and print them (expect status 200)
    print("\n[GET] Fetching last 5 readings...")
    records = get_readings(limit=5)
    for row in records:
        print("light_level: {light_level}, light_threshold: {light_threshold}, led_status: {led_status}, lcd_message: {lcd_message}".format(
            light_level=row.get("light_level"),
            light_threshold=row.get("light_threshold"),
            led_status=row.get("led_status"),
            lcd_message=row.get("lcd_message")
        ))
    '''

    # Step 4 — Fetch and display the LCD message from TABLE_SETTINGS
    print("\n[GET] Fetching LCD message...")
    new_message = get_lcd_message()
    
    if new_message is not None:
        lcd.clear()           # Clear the screen first
        lcd.putstr(new_message) # Print the new string
    print("Displayed on LCD:", new_message)
    

    # Step 5 - GET the last recorded light threshold and adjust LED accordingly
    print("\n[GET] Fetching light threshold...")
    threshold = get_light_threshold()

    # Normalize possible return shapes: int/float, dict, or list of dicts
    threshold_value = None
    if isinstance(threshold, (list, tuple)):
        if len(threshold) > 0:
            row = threshold[0]
            threshold_value = row.get("value", row.get("light_threshold", None))
    elif isinstance(threshold, dict):
        threshold_value = threshold.get("value", threshold.get("light_threshold", None))
    elif isinstance(threshold, (int, float)):
        threshold_value = threshold

    if threshold_value is not None:
        print("Light threshold:", threshold_value)
        if light_level > threshold_value:
            led.value(1)
            print("LED ON")
        else:
            led.value(0)
            print("LED OFF")
    else:
        print("No threshold value found.")
    

    
    print("Cycle repeating in 10s...")
    time.sleep(10)

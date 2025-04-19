import network
import espnow
import time
import json
from machine import SoftI2C, I2C, ADC, Pin
import dht
import math
from max30102 import MAX30102
from bmp280 import BME280
import neopixel
import urequests

# ---- WIFI Credentials & Firebase URL ----
SSID = "..."
PASSWORD = "..."
FIREBASE_URL = "..."

# ---- Initialize ESP-NOW & Wifi ----
wlan = network.WLAN(network.STA_IF)  # STA interface for Wi-Fi connection
wlan.active(True)
time.sleep(0.5)
esp = espnow.ESPNow()
esp.active(True)
print("ESP-NOW Ready!")

# ---- Function to Switch Between ESP-NOW and Wi-Fi ----
def switch_to_wifi():
    """Disable ESP-NOW and enable Wi-Fi to send data to Firebase."""
    print("Switching to Wi-Fi...")
    esp.active(False)  # Disable ESP-NOW
    wlan.disconnect()
    wlan.connect(SSID, PASSWORD)
    
    while not wlan.isconnected():
        time.sleep(0.5)
    
    print("Connected to Wi-Fi:", wlan.ifconfig())
    time.sleep(2)

def switch_to_espnow():
    """Disable Wi-Fi and re-enable ESP-NOW."""
    print("Switching back to ESP-NOW...")

    wlan.disconnect()  
    wlan.active(False)
    time.sleep(1)

    wlan.active(True)
    esp.active(True)
    time.sleep(1)
    
# ---- Firebase Function ----
def send_to_firebase(data):
    switch_to_wifi()  # Switch to Wi-Fi before sending
    
    for attempt in range(3):  # ✅ Retry up to 3 times
        try:
            response = urequests.put(FIREBASE_URL, json=data)
            print("Firebase Response:", response.status_code)
            response.close()
            break  # ✅ Exit loop if successful
        except Exception as e:
            print(f"Firebase Error (Attempt {attempt+1}):", e)
            time.sleep(2)  # ✅ Wait before retrying
    
    # LED Blink to check if the system is ready
    light_up((50, 50, 0))  # Board LED to Yellow
    time.sleep(0.5)
    light_up((0, 0, 0))  # Board LED to Blank
    time.sleep(0.1)

    switch_to_espnow()  # Switch back to ESP-NOW

# ---- Initialize Sensors ----
time.sleep(2)  # Ensure I2C devices are ready

i2c = SoftI2C(sda=Pin(14), scl=Pin(15))  
sensor_heart = MAX30102(i2c)
sensor_heart.soft_reset()
time.sleep(1)
sensor_heart.setup_sensor()


i2c_bmp = I2C(0, scl=Pin(19), sda=Pin(20), freq=100000)
sensor_bmp = BME280(i2c=i2c_bmp)

dht_sensor = dht.DHT11(Pin(18))

air_adc = ADC(Pin(0))  
air_adc.atten(ADC.ATTN_11DB)  

flame_adc = ADC(Pin(1))  
flame_adc.atten(ADC.ATTN_11DB)  

# TCS3200 (Color Sensor)
S2 = Pin(4, Pin.OUT)
S3 = Pin(5, Pin.OUT)
OUT = Pin(3, Pin.IN)

# Color Calibration
RED_MIN, RED_MAX = 100, 1200  
GREEN_MIN, GREEN_MAX = 90, 1100
BLUE_MIN, BLUE_MAX = 80, 1000

# Timers
last_sensor_update = time.time()
last_espnow_message = time.time()

# Heart Rate & Color Detection States
heart_rate_state = None
color_state = None

# Neopixel Board LED
np = neopixel.NeoPixel(Pin(8), 1)

# ---- Sensor Functions ----
def light_up(color):
    np[0] = color
    np.write()

def get_heart_rate():
    start_time = time.time()
    ir_values = []
    time_stamps = []
    peak_threshold = 5000
    min_peak_interval = 300
    last_peak_time = 0
    light_up((0, 50, 0))  # Board LED to Red

    while time.time() - start_time < 7:
        ir_value = sensor_heart.get_ir()
        current_time = time.ticks_ms()

        if len(ir_values) > 2 and ir_values[-2] < ir_values[-1] > ir_value and ir_values[-1] > peak_threshold and (current_time - last_peak_time) > min_peak_interval:
            time_stamps.append(current_time)
            last_peak_time = current_time
            if len(time_stamps) > 10:
                time_stamps.pop(0)

        ir_values.append(ir_value)
        if len(ir_values) > 10:
            ir_values.pop(0)
        time.sleep(0.1)

    if len(time_stamps) < 2:
        return None  
    intervals = [time_stamps[i + 1] - time_stamps[i] for i in range(len(time_stamps) - 1)]
    avg_interval = sum(intervals) / len(intervals)
    bpm = 60000 / avg_interval
    
    light_up((0, 0, 0))  # Board LED to Blank
    
    return int(bpm) if 40 < bpm < 180 else None

def get_air_quality():
    voltage = (air_adc.read() / 4095) * 3.3
    RS = (3.3 - voltage) / voltage
    R0 = 10.0  # Assume a calibrated R0 value. You may need to calibrate this value for your specific sensor.
    
    # Gas concentration equations (calibrated values for MQ135)
    CO2 = 116.6020682 * math.pow((RS/R0), -2.769034857)  # CO2 concentration in ppm
    NH3 = 102.2 * math.pow((RS/R0), -2.588)  # NH3 concentration in ppm
    NOx = 10.0 * math.pow((RS/R0), -1.5)  # NOx concentration in ppm
    alcohol = 1.0 * math.pow((RS/R0), -1.5)  # Alcohol concentration in ppm
    Benzene = 1.0 * math.pow((RS/R0), -1.5)  # Benzene concentration in ppm
    smoke = 1.0 * math.pow((RS/R0), -1.5)  # Smoke concentration in ppm
    
    return {
        "CO2": round(CO2, 2),
        "NH3": round(NH3, 2),
        "NOx": round(NOx, 2),
        "alcohol": round(alcohol, 2),
        "Benzene": round(Benzene, 2),
        "smoke": round(smoke, 2)
    }

def get_dht11_data():
    try:
        dht_sensor.measure()
        return {"temperature": dht_sensor.temperature(), "humidity": dht_sensor.humidity()}
    except OSError:
        return {"temperature": None, "humidity": None}

def get_bmp280_data():
    return {
        "temperature": sensor_bmp.temperature,
        "pressure": sensor_bmp.pressure,
        "humidity": sensor_bmp.humidity
    }

def get_flame_intensity():
    raw_value = flame_adc.read()
    return {"intensity": raw_value, "fire_detected": raw_value < 1500}

def select_color(color):
    if color == "red":
        S2.off()
        S3.off()
    elif color == "green":
        S2.on()
        S3.on()
    elif color == "blue":
        S2.off()
        S3.on()

def read_frequency():
    start_time = time.ticks_us()
    pulse_count = 0
    while time.ticks_diff(time.ticks_us(), start_time) < 100000:
        if OUT.value() == 0:
            while OUT.value() == 0:
                pass
            while OUT.value() == 1:
                pass
            pulse_count += 1
    return pulse_count

def normalize(raw, min_val, max_val):
    return int(((max(min(raw, max_val), min_val) - min_val) / (max_val - min_val)) * 255)

def get_color_data():
    start_time = time.time()
    color_readings = {"red": [], "green": [], "blue": []}
    
    light_up((50, 0, 0))  # Board LED to Green

    while time.time() - start_time < 4:
        select_color("red")
        time.sleep(0.1)
        color_readings["red"].append(normalize(read_frequency(), RED_MIN, RED_MAX))

        select_color("green")
        time.sleep(0.1)
        color_readings["green"].append(normalize(read_frequency(), GREEN_MIN, GREEN_MAX))

        select_color("blue")
        time.sleep(0.1)
        color_readings["blue"].append(normalize(read_frequency(), BLUE_MIN, BLUE_MAX))
    
    light_up((0, 0, 0))  # Board LED to Blank

    return {
        "red": sum(color_readings["red"]) // len(color_readings["red"]),
        "green": sum(color_readings["green"]) // len(color_readings["green"]),
        "blue": sum(color_readings["blue"]) // len(color_readings["blue"])
    }

# ---- Main Loop ----
print("Starting sensor readings...")

# LED Blink to check if the system is ready
light_up((50, 50, 50))  # Board LED to White
time.sleep(0.5)
light_up((0, 0, 0))  # Board LED to White
time.sleep(0.5)

while True:
    current_time = time.time()

    # Check for ESP-NOW messages (instant response)
    peer_mac, msg = esp.irecv(500)
    if msg:
        try:
            data_str = msg.decode()
            data = eval(data_str)
#             print("ESP-NOW Data:", data)  # Debugging print
            last_espnow_message = current_time  # Update last ESP-NOW time

            # If Button 2 is pressed → Measure heart rate
            if data.get("Button2", 0):
                print("Button 2 Pressed: Measuring Heart Rate...")
                heart_rate_state = get_heart_rate()
                print(f"Heart Rate: {heart_rate_state} BPM")

            # If Button 3 is pressed → Detect color
            if data.get("Button3", 0):
                print("Button 3 Pressed: Detecting Color...")
                color_state = get_color_data()
                print(f"Detected Color: {color_state}")

        except Exception as e:
            print("Error decoding ESP-NOW message:", e)

    # Reset Heart Rate & Color if no ESP-NOW data for 300 seconds
    if current_time - last_espnow_message >= 300:
        heart_rate_state = None
        color_state = None

    # Update sensor data every 60 seconds
    if current_time - last_sensor_update >= 60:
        last_sensor_update = current_time  # Reset timer

        sensor_data = {
            "air_quality": get_air_quality(),
            "dht11": get_dht11_data(),
            "bmp280": get_bmp280_data(),
            "flame": get_flame_intensity(),
            "heart_rate": heart_rate_state,  # Send last measured heart rate
            "color": color_state  # Send last detected color
        }
        
        # LED Blink to check if the system is ready
        light_up((0, 50, 50))  # Board LED to Purple
        time.sleep(0.5)
        light_up((0, 0, 0))  # Board LED to Blank
        time.sleep(0.1)

        print("Sensor Data Updated:", sensor_data)
        send_to_firebase(sensor_data)  # Send data to Firebase

    time.sleep(1)  # Avoid CPU overload


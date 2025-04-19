# 🌡️ Sensor Hub with ESP-NOW Remote Control

A comprehensive sensor monitoring system built with MicroPython on ESP32, featuring real-time environmental monitoring and remote control capabilities via ESP-NOW.

## ✨ Features

### Environmental Monitoring
- Temperature, Humidity, and Pressure (BMP280)
- Air Quality (MQ135)
- Flame Detection
- Color Detection (TCS3200)
- Heart Rate Monitoring (MAX30102)

### Wireless Communication
- ESP-NOW for low-latency remote control
- Wi-Fi for data logging to Firebase
- Automatic switching between ESP-NOW and Wi-Fi modes

### Remote Control
- Custom ESP-NOW remote with button controls
- On-demand heart rate monitoring
- On-demand color detection
- Real-time sensor data updates

## 🔧 Hardware Requirements

### Main Components
- ESP32 Development Board
- BMP280 Temperature/Pressure Sensor
- MQ135 Air Quality Sensor
- MAX30102 Heart Rate Sensor
- TCS3200 Color Sensor
- Flame Sensor
- DHT11 Temperature/Humidity Sensor
- Neopixel LED (for status indication)
- Custom ESP-NOW Remote Controller

### Pin Connections

| Component | ESP32 Pin | Description |
|-----------|-----------|-------------|
| MAX30102 (Heart Rate) | SDA: GPIO14<br>SCL: GPIO15 | I2C Communication |
| BMP280 | SDA: GPIO20<br>SCL: GPIO19 | I2C Communication |
| DHT11 | GPIO18 | Digital Input |
| MQ135 (Air Quality) | GPIO0 | ADC Input |
| Flame Sensor | GPIO1 | ADC Input |
| TCS3200 (Color) | S2: GPIO4<br>S3: GPIO5<br>OUT: GPIO3 | Digital I/O |
| Neopixel LED | GPIO8 | Digital Output |

## 💻 Software Requirements

- MicroPython
- Required Libraries:
  - `network`
  - `espnow`
  - `machine`
  - `dht`
  - `max30102`
  - `bmp280`
  - `neopixel`
  - `urequests`

## 🚀 Setup Instructions

1. Flash MicroPython to your ESP32 board
2. Install required libraries
3. Configure Wi-Fi credentials in `sensorHub.py`:
   ```python
   SSID = "your_wifi_ssid"
   PASSWORD = "your_wifi_password"
   FIREBASE_URL = "your_firebase_url"
   ```
4. Upload the code to your ESP32
5. Power up the custom ESP-NOW remote

## 📱 Usage

### Automatic Data Collection
- The system automatically collects sensor data every 60 seconds
- Data is transmitted to Firebase for storage and analysis

### Remote Control Functions
- **Button 2**: Trigger heart rate measurement
- **Button 3**: Trigger color detection

### Status LED Indicators
| Color | Meaning |
|-------|---------|
| ⚪ White | System ready |
| 🔴 Red | Heart rate measurement in progress |
| 🟢 Green | Color detection in progress |
| 🟣 Purple | Data transmission to Firebase |
| 🟡 Yellow | Firebase transmission complete |

## 📊 Data Collection

Sensor data is collected and transmitted to Firebase at regular intervals, including:
- Air quality metrics (CO2, NH3, NOx, etc.)
- Temperature and humidity readings
- Pressure measurements
- Flame detection status
- Heart rate (when measured)
- Color detection (when measured)

## 🔍 Troubleshooting

### Sensor Reading Issues
- Check sensor connections
- Verify power supply
- Ensure proper I2C addressing

### ESP-NOW Communication Problems
- Verify remote is powered
- Check distance between devices
- Ensure both devices are in ESP-NOW mode

### Firebase Upload Failures
- Verify Wi-Fi credentials
- Check Firebase URL
- Ensure internet connectivity

## 📜 License

This project is open-source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
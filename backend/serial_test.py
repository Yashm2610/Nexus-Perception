import serial
import time

PORT = 'COM5'
BAUD = 9600

try:
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        print(f"Testing {PORT}...")
        for _ in range(10):
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Raw: '{line}'")
            time.sleep(0.5)
except Exception as e:
    print(f"Error: {e}")

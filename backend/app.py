import cv2
import asyncio
import json
import base64
import serial
import threading
import time
import sys
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from processor import PerceptionProcessor
import os

app = FastAPI()
# ... existing middleware ...
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the path to the frontend folder
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

# Mount the rest of the static files (css, js)
app.mount("/static", StaticFiles(directory=FRONTEND_PATH), name="static")


# --- CONFIG ---
ARDUINO_PORT = 'COM5'
BAUD_RATE = 9600

processor = PerceptionProcessor()
state = {"distance": 0, "angle": 0}

def serial_worker():
    global state
    while True:
        try:
            with serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) as ser:
                print(f"Connected to Arduino on {ARDUINO_PORT}")
                while True:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line and ',' in line:
                        print(f"[SERIAL] {line}", flush=True)
                        try:
                            angle, dist = map(int, line.split(','))
                            state["angle"] = angle
                            state["distance"] = dist
                        except ValueError:
                            pass
        except Exception as e:
            print(f"Serial Error: {e}. Retrying in 3s...")
            time.sleep(3)

threading.Thread(target=serial_worker, daemon=True).start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cap = cv2.VideoCapture(0)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Current telemetry
            d = state["distance"]
            a = state["angle"]

            # Process
            output, spectrum, meta = processor.process_frame(frame, d, a)
            signal_fft = processor.process_signal_fft(d)

            # Optimization: Downscale non-critical feeds
            output_small = cv2.resize(output, (320, 240))
            spectrum_small = cv2.resize(spectrum, (320, 240))

            # Encode images (Quality optimization)
            _, buffer_orig = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            _, buffer_edge = cv2.imencode('.jpg', output_small, [cv2.IMWRITE_JPEG_QUALITY, 50])
            _, buffer_spec = cv2.imencode('.jpg', spectrum_small, [cv2.IMWRITE_JPEG_QUALITY, 50])

            # Prepare message
            payload = {
                "telemetry": {
                    "angle": a,
                    "distance": d,
                    "confidence": meta["confidence"],
                    "label": meta["label"],
                    "signal_fft": signal_fft
                },
                "images": {
                    "original": base64.b64encode(buffer_orig).decode('utf-8'),
                    "edges": base64.b64encode(buffer_edge).decode('utf-8'),
                    "spectrum": base64.b64encode(buffer_spec).decode('utf-8')
                }
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.03) # Limit to ~30 FPS

    except Exception as e:
        print(f"WebSocket closed: {e}")
    finally:
        cap.release()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

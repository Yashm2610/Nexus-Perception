import cv2
import numpy as np
import os

class PerceptionProcessor:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.distance_buffer = []
        self.buffer_size = 32
        
        # --- Deep Learning Setup ---
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        
        # Adjust paths for FastAPI relative execution
        base_dir = os.path.dirname(__file__)
        proto = os.path.join(base_dir, "models", "deploy.prototxt")
        model = os.path.join(base_dir, "models", "mobilenet.caffemodel")
        
        if os.path.exists(proto) and os.path.exists(model):
            self.net = cv2.dnn.readNetFromCaffe(proto, model)
            self.has_dnn = True
        else:
            print("DNN Models not found. Deep Learning disabled.")
            self.has_dnn = False

    def process_frame(self, frame, distance, angle):
        if frame is None:
            return None, None, {}

        # 1. Image Enhancement
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        canny = cv2.Canny(blurred, 50, 150)
        output = cv2.cvtColor(canny, cv2.COLOR_GRAY2BGR)

        # 2. Frequency Domain (2D-FFT)
        dft = np.fft.fft2(gray)
        dft_shift = np.fft.fftshift(dft)
        magnitude_spectrum = 20 * np.log(np.abs(dft_shift) + 1)
        magnitude_spectrum = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 3. Spatial Mapping (Sonar to Camera)
        target_x = int((angle / 180.0) * self.width)
        target_x = np.clip(target_x, 0, self.width - 1)

        # 4. Deep Learning Object Detection (DNN)
        detected_label = "None"
        if self.has_dnn:
            blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
            self.net.setInput(blob)
            detections = self.net.forward()
            
            for i in range(detections.shape[2]):
                conf = detections[0, 0, i, 2]
                if conf > 0.5:
                    idx = int(detections[0, 0, i, 1])
                    label = self.classes[idx]
                    box = detections[0, 0, i, 3:7] * np.array([self.width, self.height, self.width, self.height])
                    (startX, startY, endX, endY) = box.astype("int")
                    
                    # Highlight Detected Objects
                    cv2.rectangle(output, (startX, startY), (endX, endY), (255, 255, 0), 1)
                    
                    # Neural Fusion: Check if sonar is looking at this object
                    if startX <= target_x <= endX:
                        detected_label = label
                        cv2.rectangle(output, (startX, startY), (endX, endY), (255, 255, 0), 3)
                        cv2.putText(output, f"NEURAL FUSION: {label.upper()}", (startX, startY - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # 5. Sensor Fusion Logic
        local_edges = canny[:, max(0, target_x-10):min(self.width, target_x+10)]
        edge_density = np.mean(local_edges) / 255.0
        fusion_confidence = 0.4 + (0.4 * edge_density)
        if detected_label != "None": fusion_confidence = min(1.0, fusion_confidence + 0.2)
        if distance < 0 or distance >= 400: fusion_confidence = 0

        # 6. Visual Overlay (Sonar Depth)
        if distance > 0 and distance < 400:
            color = (0, 0, 255) if distance < 20 else (0, 165, 255) if distance < 50 else (0, 255, 0)
            overlay = output.copy()
            cv2.rectangle(overlay, (target_x-10, 0), (target_x+10, self.height), color, -1)
            cv2.addWeighted(overlay, 0.4, output, 0.6, 0, output)
            cv2.putText(output, f"PROBE: {distance}cm", (target_x + 15, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        else:
            cv2.line(output, (target_x, 0), (target_x, self.height), (100, 100, 100), 1)

        return output, magnitude_spectrum, {
            "angle": angle,
            "distance": distance,
            "confidence": round(fusion_confidence, 2),
            "label": detected_label
        }

    def process_signal_fft(self, distance):
        self.distance_buffer.append(distance)
        if len(self.distance_buffer) > self.buffer_size:
            self.distance_buffer.pop(0)
        if len(self.distance_buffer) < self.buffer_size:
            return []
        signal = np.array(self.distance_buffer)
        signal_fft = np.abs(np.fft.fft(signal))
        return (signal_fft[:self.buffer_size // 2] / 10).tolist() # Normalize for chart

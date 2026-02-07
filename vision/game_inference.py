import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pickle
import numpy as np
import os

def get_relative_coordinates(hand_landmarks):
    """Extract relative coordinates from hand landmarks."""
    wrist_x = hand_landmarks[0].x
    wrist_y = hand_landmarks[0].y
    relative_coords = []
    for lm in hand_landmarks:
        rel_x = lm.x - wrist_x
        rel_y = lm.y - wrist_y
        relative_coords.extend([rel_x, rel_y])
    return relative_coords

def draw_landmarks_on_image(rgb_image, detection_result):
    """Draw hand landmarks on the image."""
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            # Draw landmarks as circles
            h, w, _ = rgb_image.shape
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(rgb_image, (cx, cy), 5, (0, 255, 0), -1)
            
            # Draw connections
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                (0, 5), (5, 6), (6, 7), (7, 8),  # Index
                (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
                (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
                (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                (5, 9), (9, 13), (13, 17)  # Palm
            ]
            for start, end in connections:
                x1, y1 = int(hand_landmarks[start].x * w), int(hand_landmarks[start].y * h)
                x2, y2 = int(hand_landmarks[end].x * w), int(hand_landmarks[end].y * h)
                cv2.line(rgb_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return rgb_image

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load Model
model_path = os.path.join(script_dir, 'model.p')
try:
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("Model not found! Train it first.")
    exit()

# Set up HandLandmarker with new tasks API
hand_landmarker_path = os.path.join(script_dir, 'hand_landmarker.task')
base_options = python.BaseOptions(model_asset_path=hand_landmarker_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.8,
    min_hand_presence_confidence=0.8,
    min_tracking_confidence=0.8
)
detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera lost, reconnecting...")
        cap.release()
        cv2.waitKey(500)
        cap = cv2.VideoCapture(0)
        continue
    
    # Convert BGR to RGB for mediapipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    
    # Detect hand landmarks
    results = detector.detect(mp_image)
    
    prediction_text = "Waiting..."
    
    if results.hand_landmarks:
        for hand_landmarks in results.hand_landmarks:
            # 1. Extract exactly the same features as training
            lm_list = get_relative_coordinates(hand_landmarks)
            
            # 2. Predict
            # Reshape to (1, -1) because we are predicting a single sample
            prediction = model.predict([lm_list])
            prediction_text = prediction[0]
            
            # Draw landmarks on frame
            frame = draw_landmarks_on_image(frame, results)

    # UI
    cv2.rectangle(frame, (0, 0), (300, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"Letter: {prediction_text}", (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    cv2.imshow("Game Inference", frame)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()
import cv2
import mediapipe as mp
import pickle
import numpy as np

def get_relative_coordinates(hand_landmarks):
    wrist_x = hand_landmarks.landmark[0].x
    wrist_y = hand_landmarks.landmark[0].y
    relative_coords = []
    for lm in hand_landmarks.landmark:
        rel_x = lm.x - wrist_x
        rel_y = lm.y - wrist_y
        relative_coords.extend([rel_x, rel_y])
    return relative_coords

# Load Model
try:
    with open('model.p', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("Model not found! Train it first.")
    exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.8)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera lost, reconnecting...")
        cap.release()
        cv2.waitKey(500)
        cap = cv2.VideoCapture(0)
        continue
    
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    
    prediction_text = "Waiting..."
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # 1. Extract exactly the same features as training
            lm_list = get_relative_coordinates(hand_landmarks)
            
            # 2. Predict
            # Reshape to (1, -1) because we are predicting a single sample
            prediction = model.predict([lm_list])
            prediction_text = prediction[0]
            
            # Draw
            mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # UI
    cv2.rectangle(frame, (0, 0), (300, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"Spell: {prediction_text}", (10, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    cv2.imshow("Game Inference", frame)
    if cv2.waitKey(1) == ord('q'): break

cap.release()
cv2.destroyAllWindows()
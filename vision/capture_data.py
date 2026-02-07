import cv2
import mediapipe as mp
import pandas as pd
import os

def get_relative_coordinates(hand_landmarks):
    # 1. Get the Wrist (Point 0) as the anchor
    wrist_x = hand_landmarks.landmark[0].x
    wrist_y = hand_landmarks.landmark[0].y
    
    relative_coords = []
    
    for lm in hand_landmarks.landmark:
        # Subtract wrist position from every point
        rel_x = lm.x - wrist_x
        rel_y = lm.y - wrist_y
        relative_coords.extend([rel_x, rel_y])
        
    return relative_coords

# CONFIG
DATA_FILE = "hand_data.csv"
SAMPLES_PER_CLASS = 1000

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.8)

# Initialize CSV if not exists
if not os.path.exists(DATA_FILE):
    cols = ["label"] + [f"x{i}" for i in range(21)] + [f"y{i}" for i in range(21)]
    df = pd.DataFrame(columns=cols)
    df.to_csv(DATA_FILE, index=False)

cap = cv2.VideoCapture(0)

while True:
    current_label = input("\nEnter the Label name to record (e.g. 'A', 'Fire'), or '0' to quit: ").strip()
    if current_label.lower() == '0':
        break

    print(f"--- RECORDING {current_label.upper()} ---")
    print("Press 'S' to start/stop saving. Press '0' to finish this label early.")

    saving = False
    counter = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw for visual feedback
                mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                if saving and counter < SAMPLES_PER_CLASS:
                    # Extract normalized coordinates
                    row = [current_label]
                    # Xs and Ys relative to wrist
                    row.extend(get_relative_coordinates(hand_landmarks))

                    # Append to CSV
                    df = pd.DataFrame([row])
                    df.to_csv(DATA_FILE, mode='a', header=False, index=False)
                    
                    counter += 1
                    cv2.putText(frame, f"Saved: {counter}/{SAMPLES_PER_CLASS}", (10, 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        status_color = (0, 255, 0) if saving else (0, 0, 255)
        cv2.putText(frame, f"Label: {current_label} | Saving: {saving}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        cv2.imshow("Data Collector", frame)
        key = cv2.waitKey(1)
        if key == ord('0'): break
        if key == ord('s'): saving = not saving

        # Auto-advance once we hit the sample limit
        if counter >= SAMPLES_PER_CLASS:
            print(f"Finished collecting {SAMPLES_PER_CLASS} samples for '{current_label}'.")
            break

cap.release()
cv2.destroyAllWindows()
print("Data collection complete.")
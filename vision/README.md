# ASL Detection Pipeline

The vision system detects American Sign Language (ASL) hand signs via webcam and feeds confirmed letters into the game in real time.

## Architecture

The pipeline runs in a **background thread** and uses two stages:

### Stage 1: Hand Detection (MediaPipe)

- Uses **MediaPipe's HandLandmarker** task to detect and track a single hand in the webcam feed
- Extracts **21 hand landmarks** (wrist, finger joints, fingertips) with x/y coordinates
- Configurable confidence thresholds for detection, presence, and tracking

### Stage 2: Letter Classification (Scikit-learn)

- A pre-trained **pickle-serialized ML model** (`model.p`) classifies the hand pose into ASL letters
- Features are **relative coordinates** — each landmark's (x, y) is normalized against the wrist position, producing a 42-element feature vector (21 landmarks × 2 coordinates)
- The model predicts a single uppercase letter (A–Z)

## Libraries

| Library            | Purpose                                                       |
|--------------------|---------------------------------------------------------------|
| **OpenCV** (`cv2`) | Webcam capture, frame processing, preview window rendering    |
| **MediaPipe**      | Hand landmark detection via the HandLandmarker task model     |
| **NumPy**          | Array operations for frame/feature manipulation               |
| **scikit-learn**   | The pickled classifier model (loaded at runtime via `pickle`) |

## Hold-to-Confirm State Machine

To avoid accidental inputs, the system implements a three-state machine:

1. **Waiting** — No hand detected, ready for input
2. **Holding** — Letter detected and must be held for 0.5s with consistent predictions to confirm
3. **Debouncing** — Letter fired to the game queue, waiting for hand to be removed before accepting new input

Confirmed letters are passed to the game via a **thread-safe queue** (`queue.Queue`), which the game polls each frame.

## Files

| File                   | Description                                                                                      |
|------------------------|--------------------------------------------------------------------------------------------------|
| `camera_input.py`      | Main pipeline: webcam capture, MediaPipe detection, classification, state machine, and threading |
| `train_model.py`       | Script to train the scikit-learn classifier from labeled hand landmark data                      |
| `capture_data.py`      | Utility to capture and label hand landmark data for training                                     |
| `game_inference.py`    | Standalone inference script for testing the model outside the game                               |
| `model.p`              | Pre-trained classifier model (pickle format)                                                     |
| `hand_landmarker.task` | MediaPipe HandLandmarker task bundle                                                             |
| `hand_data.csv`        | Labeled training data for the classifier                                                         |

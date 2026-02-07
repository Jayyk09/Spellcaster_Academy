"""
Camera input handler for ASL letter detection.

Runs hand detection in a background thread and provides a thread-safe
interface for the game to read detected letters.
"""
import threading
import queue
import time
import os

# Lazy imports to avoid loading heavy libraries until needed
cv2 = None
mp = None
np = None


def _load_dependencies():
    """Lazy load heavy dependencies."""
    global cv2, mp, np
    if cv2 is None:
        import cv2 as _cv2
        import mediapipe as _mp
        import numpy as _np
        cv2 = _cv2
        mp = _mp
        np = _np


class CameraInput:
    """
    Threaded camera input handler for ASL letter detection.
    
    Detects hand signs using MediaPipe and a trained ML model,
    with hold-to-confirm and debounce logic.
    """
    
    # Detection states
    STATE_WAITING = 'waiting'       # No hand detected, ready for new input
    STATE_HOLDING = 'holding'       # Letter detected, tracking hold time
    STATE_DEBOUNCING = 'debouncing' # Letter fired, waiting for hand to leave
    
    def __init__(self, hold_time: float = 0.5, confidence_threshold: float = 0.8,
                 show_preview: bool = True):
        """
        Initialize the camera input handler.
        
        Args:
            hold_time: Seconds a letter must be held before it's confirmed
            confidence_threshold: Minimum confidence for hand detection
            show_preview: Whether to show the camera preview window
        """
        self.hold_time = hold_time
        self.confidence_threshold = confidence_threshold
        self.show_preview = show_preview
        
        # Thread management
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        
        # Letter queue (thread-safe)
        self._letter_queue = queue.Queue()
        
        # State tracking
        self._state = self.STATE_WAITING
        self._current_letter = None
        self._hold_start_time = None
        
        # Current detection info (for UI display)
        self._current_detected_letter = None
        self._hold_progress = 0.0  # 0.0 to 1.0
        
        # Camera availability
        self._available = False
        self._error_message = None
        
        # Model and detector (initialized in thread)
        self._model = None
        self._detector = None
    
    def start(self):
        """Start the background detection thread."""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running
        
        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the background thread and release resources."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
    
    def is_available(self) -> bool:
        """Check if the camera is available and working."""
        return self._available
    
    def get_error_message(self) -> str | None:
        """Get the error message if camera is not available."""
        return self._error_message
    
    def get_pending_letters(self) -> list[str]:
        """
        Get all pending confirmed letters and clear the queue.
        
        Returns:
            List of confirmed letter strings (uppercase A-Z)
        """
        letters = []
        while True:
            try:
                letter = self._letter_queue.get_nowait()
                letters.append(letter)
            except queue.Empty:
                break
        return letters
    
    def get_current_detection(self) -> tuple[str | None, float]:
        """
        Get the currently detected letter and hold progress.
        
        Returns:
            Tuple of (letter or None, hold_progress 0.0-1.0)
        """
        with self._lock:
            return self._current_detected_letter, self._hold_progress
    
    def get_state(self) -> str:
        """Get the current detection state."""
        with self._lock:
            return self._state
    
    def _detection_loop(self):
        """Background thread that runs hand detection."""
        try:
            _load_dependencies()
            
            # Load the trained model
            if not self._load_model():
                return
            
            # Initialize MediaPipe hand detector
            if not self._init_detector():
                return
            
            # Open camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self._error_message = "Could not open camera"
                self._available = False
                return
            
            self._available = True
            
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    # Camera lost, try to reconnect
                    cap.release()
                    time.sleep(0.5)
                    cap = cv2.VideoCapture(0)
                    continue
                
                # Detect hand and predict letter (also draws on frame if preview enabled)
                detected_letter, hand_landmarks = self._detect_letter_with_landmarks(frame)
                
                # Update state machine
                self._update_state(detected_letter)
                
                # Show preview window if enabled
                if self.show_preview:
                    self._draw_preview(frame, hand_landmarks, detected_letter)
                    cv2.imshow("ASL Camera Input", frame)
                    if cv2.waitKey(1) == ord('q'):
                        self._running = False
                        break
                
                # Small delay to avoid hogging CPU
                time.sleep(0.01)  # ~60 FPS when showing preview
            
            # Cleanup
            cap.release()
            if self.show_preview:
                cv2.destroyAllWindows()
            
        except Exception as e:
            self._error_message = f"Camera error: {str(e)}"
            self._available = False
    
    def _load_model(self) -> bool:
        """Load the trained ML model."""
        import pickle
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'model.p')
        
        try:
            with open(model_path, 'rb') as f:
                self._model = pickle.load(f)
            return True
        except FileNotFoundError:
            self._error_message = "Model file not found (model.p)"
            self._available = False
            return False
        except Exception as e:
            self._error_message = f"Error loading model: {str(e)}"
            self._available = False
            return False
    
    def _init_detector(self) -> bool:
        """Initialize MediaPipe hand detector."""
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(script_dir, 'hand_landmarker.task')
            
            if not os.path.exists(model_path):
                self._error_message = "Hand landmarker model not found"
                self._available = False
                return False
            
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=1,
                min_hand_detection_confidence=self.confidence_threshold,
                min_hand_presence_confidence=self.confidence_threshold,
                min_tracking_confidence=self.confidence_threshold
            )
            self._detector = vision.HandLandmarker.create_from_options(options)
            return True
            
        except Exception as e:
            self._error_message = f"Error initializing detector: {str(e)}"
            self._available = False
            return False
    
    def _detect_letter(self, frame) -> str | None:
        """
        Detect hand in frame and predict letter.
        
        Returns:
            Predicted letter (uppercase) or None if no hand detected
        """
        letter, _ = self._detect_letter_with_landmarks(frame)
        return letter
    
    def _detect_letter_with_landmarks(self, frame) -> tuple[str | None, list | None]:
        """
        Detect hand in frame and predict letter, also returning landmarks.
        
        Returns:
            Tuple of (predicted letter or None, hand landmarks or None)
        """
        if self._detector is None or self._model is None:
            return None, None
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        # Detect hands
        results = self._detector.detect(mp_image)
        
        if not results.hand_landmarks:
            return None, None
        
        # Get first hand's landmarks
        hand_landmarks = results.hand_landmarks[0]
        
        # Extract features (same as training)
        features = self._get_relative_coordinates(hand_landmarks)
        
        # Predict
        try:
            prediction = self._model.predict([features])
            return prediction[0].upper(), hand_landmarks
        except Exception:
            return None, hand_landmarks
    
    def _draw_preview(self, frame, hand_landmarks, detected_letter: str | None):
        """Draw the preview overlay on the frame."""
        h, w, _ = frame.shape
        
        # Draw hand landmarks if detected
        if hand_landmarks:
            # Draw landmarks as circles
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            
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
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Get current state for display
        with self._lock:
            state = self._state
            progress = self._hold_progress
        
        # Draw status bar at top
        cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
        
        # Draw detected letter
        if detected_letter:
            # Color based on state
            if state == 'debouncing':
                color = (0, 255, 0)  # Green - confirmed
                status = "FIRED! Release hand..."
            elif state == 'holding':
                color = (0, 255, 255)  # Yellow - holding
                status = f"Hold: {progress*100:.0f}%"
            else:
                color = (255, 255, 255)  # White - detected
                status = "Detected"
            
            cv2.putText(frame, f"Letter: {detected_letter}", (10, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
            cv2.putText(frame, status, (10, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Draw progress bar when holding
            if state == 'holding':
                bar_x, bar_y = 250, 20
                bar_w, bar_h = 200, 30
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
                fill_w = int(bar_w * progress)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 200, 255), -1)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 2)
        else:
            cv2.putText(frame, "No hand detected", (10, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (150, 150, 150), 2)
            cv2.putText(frame, "Show ASL letter A-E", (10, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
        
        # Instructions at bottom
        cv2.rectangle(frame, (0, h - 30), (w, h), (0, 0, 0), -1)
        cv2.putText(frame, "Press 'Q' to close camera window", (10, h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    def _get_relative_coordinates(self, hand_landmarks) -> list[float]:
        """Extract relative coordinates from hand landmarks."""
        wrist_x = hand_landmarks[0].x
        wrist_y = hand_landmarks[0].y
        relative_coords = []
        for lm in hand_landmarks:
            rel_x = lm.x - wrist_x
            rel_y = lm.y - wrist_y
            relative_coords.extend([rel_x, rel_y])
        return relative_coords
    
    def _update_state(self, detected_letter: str | None):
        """Update the state machine based on detected letter."""
        current_time = time.time()
        
        with self._lock:
            if self._state == self.STATE_WAITING:
                if detected_letter is not None:
                    # Start holding a new letter
                    self._state = self.STATE_HOLDING
                    self._current_letter = detected_letter
                    self._hold_start_time = current_time
                    self._current_detected_letter = detected_letter
                    self._hold_progress = 0.0
                else:
                    self._current_detected_letter = None
                    self._hold_progress = 0.0
            
            elif self._state == self.STATE_HOLDING:
                if detected_letter is None:
                    # Hand removed, go back to waiting
                    self._state = self.STATE_WAITING
                    self._current_letter = None
                    self._hold_start_time = None
                    self._current_detected_letter = None
                    self._hold_progress = 0.0
                
                elif detected_letter != self._current_letter:
                    # Different letter, restart hold
                    self._current_letter = detected_letter
                    self._hold_start_time = current_time
                    self._current_detected_letter = detected_letter
                    self._hold_progress = 0.0
                
                else:
                    # Same letter, check hold duration
                    hold_duration = current_time - self._hold_start_time
                    self._hold_progress = min(1.0, hold_duration / self.hold_time)
                    
                    if hold_duration >= self.hold_time:
                        # Confirmed! Queue the letter
                        self._letter_queue.put(self._current_letter)
                        self._state = self.STATE_DEBOUNCING
                        self._hold_progress = 1.0
            
            elif self._state == self.STATE_DEBOUNCING:
                # Update display
                self._current_detected_letter = detected_letter
                
                if detected_letter is None:
                    # Hand removed, ready for new input
                    self._state = self.STATE_WAITING
                    self._current_letter = None
                    self._hold_start_time = None
                    self._hold_progress = 0.0
                # If letter still detected, stay in debouncing state

import cv2
import mediapipe as mp
import numpy as np
import ctypes
import math

# --- 1. Get True Fullscreen Resolution ---
def get_screen_resolution():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:
        pass
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

SCREEN_W, SCREEN_H = get_screen_resolution()

# --- 2. Setup Webcam & MediaPipe ---
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1, 
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.85  
)
LEFT_IRIS_CENTER = 473

# --- 3. Setup True Fullscreen Window ---
WIN = "Final Review Demo - 25 Grid"
cv2.namedWindow(WIN, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(WIN, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# --- 4. Core Variables & Tuning ---
eye_x_min, eye_y_min = 9999, 9999
eye_x_max, eye_y_max = 0, 0
calib_step = 0 

# Rolling Average Buffer (Raw Signal Smoothing)
history_buffer = []
BUFFER_SIZE = 17  

# 🎛️ NEW STABILIZATION TUNING 🎛️
cursor_x, cursor_y = SCREEN_W // 2, SCREEN_H // 2 # Start in the center
DEADZONE_RADIUS = 26  # Ignores micro-movements under 30 pixels
SMOOTHING = 0.18      # Rubber-band pull (0.01 is slow, 1.0 is instant)

print("Starting Stabilized 25-Box Engine...")

while True:
    ret, frame = cap.read()
    if not ret: break
        
    frame = cv2.flip(frame, 1) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    canvas = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        img_h, img_w, _ = frame.shape
        
        iris_x = int(landmarks[LEFT_IRIS_CENTER].x * img_w)
        iris_y = int(landmarks[LEFT_IRIS_CENTER].y * img_h)

        # --- PHASE 1: 2-POINT CALIBRATION ---
        if calib_step == 0:
            cv2.putText(canvas, "Look TOP-LEFT and press 'c'", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        elif calib_step == 1:
            cv2.putText(canvas, "Look BOTTOM-RIGHT and press 'c'", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            
        # --- PHASE 2: LIVE DEMO (25-BOX GRID) ---
        elif calib_step == 2:
            
            # Anti-Twist Auto-Sort
            safe_x_min = min(eye_x_min, eye_x_max)
            safe_x_max = max(eye_x_min, eye_x_max)
            safe_y_min = min(eye_y_min, eye_y_max)
            safe_y_max = max(eye_y_min, eye_y_max)

            if (safe_x_max - safe_x_min) < 5: safe_x_max = safe_x_min + 5
            if (safe_y_max - safe_y_min) < 5: safe_y_max = safe_y_min + 5

            raw_x_percent = (iris_x - safe_x_min) / (safe_x_max - safe_x_min)
            raw_y_percent = (iris_y - safe_y_min) / (safe_y_max - safe_y_min)

            # Edge Stretch Multiplier
            stretch = 1.3
            stretched_x = 0.5 + ((raw_x_percent - 0.5) * stretch)
            stretched_y = 0.5 + ((raw_y_percent - 0.5) * stretch)
            
            final_x_percent = np.clip(stretched_x, 0, 1)
            final_y_percent = np.clip(stretched_y, 0, 1)

            # 1st Layer Filter: Rolling Buffer
            history_buffer.append((final_x_percent, final_y_percent))
            if len(history_buffer) > BUFFER_SIZE:
                history_buffer.pop(0)

            avg_x = sum([pt[0] for pt in history_buffer]) / len(history_buffer)
            avg_y = sum([pt[1] for pt in history_buffer]) / len(history_buffer)

            # --- 2nd Layer Filter: THE LERP STABILIZER ---
            target_x = int(avg_x * SCREEN_W)
            target_y = int(avg_y * SCREEN_H)
            
            distance = math.hypot(target_x - cursor_x, target_y - cursor_y)
            
            # Only update if it breaks the deadzone
            if distance > DEADZONE_RADIUS:
                cursor_x = int(cursor_x + (target_x - cursor_x) * SMOOTHING)
                cursor_y = int(cursor_y + (target_y - cursor_y) * SMOOTHING)
            
            # --- THE 25-BOX MATH (5x5) ---
            box_w = SCREEN_W // 5
            box_h = SCREEN_H // 5
            
            active_col = min(max(cursor_x // box_w, 0), 4)
            active_row = min(max(cursor_y // box_h, 0), 4)
            
            for row in range(5):
                for col in range(5):
                    x1 = col * box_w
                    y1 = row * box_h
                    x2 = x1 + box_w
                    y2 = y1 + box_h
                    
                    if row == active_row and col == active_col:
                        bg_color = (0, 180, 0) # Bright Green
                        text = "TARGET"
                    else:
                        bg_color = (30, 30, 30) # Dark Gray
                        text = f"R{row+1}-C{col+1}"
                        
                    cv2.rectangle(canvas, (x1, y1), (x2, y2), bg_color, -1)
                    cv2.rectangle(canvas, (x1, y1), (x2, y2), (100, 100, 100), 2)
                    
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    text_x = x1 + (box_w - text_size[0]) // 2
                    text_y = y1 + (box_h + text_size[1]) // 2
                    cv2.putText(canvas, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Draw the stabilized yellow gaze cursor
            cv2.circle(canvas, (cursor_x, cursor_y), 20, (0, 255, 255), -1)
            cv2.circle(canvas, (cursor_x, cursor_y), 20, (0, 0, 0), 3) 
            
            cv2.putText(canvas, "Press 'q' to exit", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): 
        break
    elif key == ord('c'):
        if calib_step == 0:
            eye_x_min, eye_y_min = iris_x, iris_y
            calib_step = 1
        elif calib_step == 1:
            eye_x_max, eye_y_max = iris_x, iris_y
            calib_step = 2

    cv2.imshow(WIN, canvas)

cap.release()
cv2.destroyAllWindows()
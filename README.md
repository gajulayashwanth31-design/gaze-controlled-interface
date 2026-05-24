# Gaze-Controlled Interface (25-Box Stabilized Engine)

A real-time, zero-hardware eye-tracking engine built for a web-based gaze-control interface. This module captures standard webcam feeds and translates pupil movement into stable, mapped 2D screen coordinates across a high-fidelity 5x5 grid.

## 🚀 Features
* **Zero Custom Hardware:** Runs entirely on standard webcams using MediaPipe Face Mesh.
* **Dynamic LERP Stabilization:** Implements a deadzone radius and Linear Interpolation (rubber-banding) to eliminate webcam micro-jitter while maintaining rapid snap-to-target responsiveness.
* **Anti-Twist Auto-Sort:** Mathematically prevents coordinate inversion if the user tilts their head during the calibration phase.
* **25-Grid Demo UI:** Includes a full-screen verification dashboard that divides the monitor into 25 interactive targeting regions.

## 🛠️ Tech Stack
* Python 3.x
* OpenCV (`cv2`) - Video capture and UI rendering
* MediaPipe - Facial landmark detection
* NumPy - Mathematical clipping and array management

## ⚙️ Installation & Usage
1. Clone the repository to your local machine.
2. Install the required dependencies: 
   ```bash
   pip install -r requirements.txt

import cv2 as cv
import numpy as np
import time

# -----------------------------
# 1. Load ArUco dictionary
# -----------------------------
aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
detector_params = cv.aruco.DetectorParameters()
detector = cv.aruco.ArucoDetector(aruco_dict, detector_params)

TARGET_ID = 42

# -----------------------------
# 2. Select Camera Source
# -----------------------------
USE_GSTREAMER = False   # Set to True if using Pi Camera + GStreamer

def gstreamer_pipeline(width=640, height=480, fps=30):
    return (
        f"libcamerasrc ! video/x-raw, width={width}, height={height}, "
        f"framerate={fps}/1 ! videoconvert ! appsink"
    )

if USE_GSTREAMER:
    print("Opening Pi Camera using GStreamer…")
    cap = cv.VideoCapture(gstreamer_pipeline(), cv.CAP_GSTREAMER)
else:
    print("Opening USB webcam…")
    cap = cv.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("❌ ERROR: Could not open camera")


# Allow camera to warm up
time.sleep(1.0)

print("Camera opened successfully!")

# -----------------------------
# 3. Main loop
# -----------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera frame read failed.")
        break

    # Optional: Resize to improve speed on Pi
    frame = cv.resize(frame, (640, 480))

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # Detect markers
    corners, ids, rejected = detector.detectMarkers(gray)

    if ids is not None:
        ids_flat = ids.flatten()
        matches = np.where(ids_flat == TARGET_ID)[0]

        if len(matches) > 0:
            for idx in matches:
                marker_corners = corners[idx].astype(int)

                cv.polylines(
                    frame, [marker_corners], True, (0, 255, 0), 2
                )

                c = marker_corners[0][0]
                cv.putText(frame, f"ID {ids_flat[idx]}",
                           (c[0], c[1] - 10),
                           cv.FONT_HERSHEY_SIMPLEX, 0.6,
                           (0, 255, 0), 2)

            cv.putText(frame, "Marker 42 DETECTED", (10, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.8,
                       (0, 255, 0), 2)
        else:
            cv.putText(frame, "Marker 42 not in frame", (10, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.8,
                       (0, 0, 255), 2)
    else:
        cv.putText(frame, "No markers detected", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8,
                   (0, 0, 255), 2)

    cv.imshow("ArUco Detection (Pi)", frame)

    # Exit gracefully
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()

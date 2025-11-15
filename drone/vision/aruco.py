import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

# Define the dictionary we want to use
aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
detector_params = cv.aruco.DetectorParameters()

# Generate a marker
marker_id = 42
marker_size = 200  # Size in pixels
marker_image = cv.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)

cv.imwrite('marker_42.png', marker_image)
plt.imshow(marker_image, cmap='gray', interpolation='nearest')
plt.axis('off')  # Hide axes
plt.title(f'ArUco Marker {marker_id}')
plt.show()


# Newer OpenCV API (4.7+)
detector = cv.aruco.ArucoDetector(aruco_dict, detector_params)

TARGET_ID = 42

# --- 2. Open camera (0 = default webcam; change if needed) ---
cap = cv.VideoCapture(0)   # or your drone camera index / URI

if not cap.isOpened():
    raise RuntimeError("Could not open camera")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to grayscale (ArUco works on grayscale)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # --- 3. Detect markers ---
    corners, ids, rejected = detector.detectMarkers(gray)

    if ids is not None:
        # Flatten ids array to 1D for easier handling
        ids_flat = ids.flatten()

        # Find indices where id == TARGET_ID
        matches = np.where(ids_flat == TARGET_ID)[0]

        if len(matches) > 0:
            for idx in matches:
                marker_corners = corners[idx].astype(int)

                # Draw polygon around the marker
                cv.polylines(frame, [marker_corners], isClosed=True, thickness=2, color=(0, 255, 0))

                # Draw the ID near one corner
                c = marker_corners[0][0]
                cv.putText(frame, f"ID {ids_flat[idx]}", (c[0], c[1] - 10),
                           cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv.putText(frame, "Marker 42 DETECTED", (10, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            cv.putText(frame, "Marker 42 not in frame", (10, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    else:
        cv.putText(frame, "No markers detected", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv.imshow("ArUco Detection", frame)

    # Press 'q' to exit
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()

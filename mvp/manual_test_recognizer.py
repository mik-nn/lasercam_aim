# mvp/test_recognizer.py
import cv2
from camera import Camera
from recognizer import MarkerRecognizer


def main():
    camera = Camera()
    recognizer = MarkerRecognizer()

    while True:
        frame = camera.get_frame()
        if frame is None:
            break

        found, center = recognizer.find_marker(frame)

        if found:
            print(f"Marker found at: {center}")
            cv2.circle(frame, center, 5, (0, 0, 255), -1)

        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

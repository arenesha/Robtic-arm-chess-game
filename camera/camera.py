import cv2
import logging

logger = logging.getLogger(__name__)

class Camera:
    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap = None

    def initialize(self) -> bool:
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_id}")
            return False
        logger.info(f"Camera {self.camera_id} initialized.")
        return True

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def release(self):
        if self.cap:
            self.cap.release()

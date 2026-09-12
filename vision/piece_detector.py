import numpy as np
import cv2
import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class PieceDetector:
    def __init__(self, model_path: str = None):
        self.model = None
        if model_path:
            try:
                self.model = YOLO(model_path)
                logger.info(f"Loaded YOLO model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")

    def detect_occupancy_fallback(self, square_image: np.ndarray) -> bool:
        """
        Simple contour-based fallback to detect if a square is occupied.
        """
        gray = cv2.cvtColor(square_image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Count non-zero pixels
        non_zero = cv2.countNonZero(thresh)
        ratio = non_zero / (square_image.shape[0] * square_image.shape[1])
        
        # If more than 15% of the square is "foreground", consider it occupied
        return ratio > 0.15

    def detect_pieces(self, crops: dict) -> dict:
        """
        Takes a dict of 64 crops (keyed by square name) and returns a dict of
        occupancy or piece classifications.
        """
        state = {}
        for square, crop in crops.items():
            if self.model:
                # YOLO inference (placeholder logic for custom trained model)
                results = self.model(crop, verbose=False)
                if len(results[0].boxes) > 0:
                    cls_id = int(results[0].boxes[0].cls[0])
                    # Map cls_id to piece name based on your model's names list
                    state[square] = self.model.names[cls_id]
                else:
                    state[square] = None
            else:
                # Fallback
                is_occupied = self.detect_occupancy_fallback(crop)
                state[square] = "Occupied" if is_occupied else None
                
        return state

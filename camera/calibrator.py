import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class CameraRobotCalibrator:
    def __init__(self):
        # 3x3 transformation matrix from camera pixels to robot mm
        self.transform_matrix = None
        
    def calibrate_from_points(self, image_points, robot_points):
        """
        Takes 4 image points (pixels) and 4 corresponding robot points (mm).
        Computes the perspective transformation matrix.
        """
        if len(image_points) != 4 or len(robot_points) != 4:
            logger.error("Calibration requires exactly 4 points.")
            return False
            
        src_pts = np.array(image_points, dtype="float32")
        dst_pts = np.array(robot_points, dtype="float32")
        
        self.transform_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        logger.info("Camera-to-Robot Transformation Matrix generated.")
        return True
        
    def pixel_to_mm(self, px, py):
        """
        Transforms a (pixel_x, pixel_y) coordinate into (robot_mm_x, robot_mm_y).
        Returns None if not calibrated.
        """
        if self.transform_matrix is None:
            return None
            
        # Homogeneous coordinates
        pt = np.array([[[px, py]]], dtype="float32")
        transformed = cv2.perspectiveTransform(pt, self.transform_matrix)
        
        rx = transformed[0][0][0]
        ry = transformed[0][0][1]
        return (float(rx), float(ry))
        
    def load_matrix(self, matrix_list):
        if matrix_list and len(matrix_list) == 9:
            self.transform_matrix = np.array(matrix_list).reshape(3, 3)
            return True
        return False
        
    def get_matrix_as_list(self):
        if self.transform_matrix is not None:
            return self.transform_matrix.flatten().tolist()
        return None

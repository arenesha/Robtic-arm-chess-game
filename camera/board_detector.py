import numpy as np
import cv2

class BoardDetector:
    def __init__(self, output_size=800):
        self.output_size = output_size
        self.transform_matrix = None
        # Standard 4 corners of a square board (top-left, top-right, bottom-right, bottom-left)
        self.dst_points = np.array([
            [0, 0],
            [self.output_size - 1, 0],
            [self.output_size - 1, self.output_size - 1],
            [0, self.output_size - 1]
        ], dtype="float32")

    def calibrate(self, image_corners: list) -> bool:
        """
        Takes 4 points (TL, TR, BR, BL) clicked by the user on the camera feed
        and computes the perspective transform matrix.
        """
        if len(image_corners) != 4:
            return False
        
        src_points = np.array(image_corners, dtype="float32")
        self.transform_matrix = cv2.getPerspectiveTransform(src_points, self.dst_points)
        return True

    def auto_find_corners(self, frame: np.ndarray) -> list:
        """
        Attempts to automatically detect the 4 outermost corners of a standard chessboard 
        in the provided frame. Returns a list of 4 (x,y) points, or None if failed.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Using 7x7 inner corners (standard 8x8 chessboard)
        ret, corners = cv2.findChessboardCorners(gray, (7, 7), None)
        
        if ret:
            # Refine corner locations
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            
            # Extract the 4 outermost corners
            # corners are ordered row by row, left to right
            # TL = 0, TR = 6, BL = 42, BR = 48
            tl = corners2[0][0].tolist()
            tr = corners2[6][0].tolist()
            bl = corners2[42][0].tolist()
            br = corners2[48][0].tolist()
            
            # The inner corners don't cover the full outer square. 
            # We must extrapolate to get the actual board edges.
            # For a 8x8 board, the distance from inner corner to edge is 1 square.
            # The distance between inner corners is 6 squares total.
            dx_top = (tr[0] - tl[0]) / 6.0
            dy_top = (tr[1] - tl[1]) / 6.0
            
            dx_left = (bl[0] - tl[0]) / 6.0
            dy_left = (bl[1] - tl[1]) / 6.0
            
            dx_right = (br[0] - tr[0]) / 6.0
            dy_right = (br[1] - tr[1]) / 6.0
            
            dx_bottom = (br[0] - bl[0]) / 6.0
            dy_bottom = (br[1] - bl[1]) / 6.0
            
            actual_tl = [tl[0] - dx_top - dx_left, tl[1] - dy_top - dy_left]
            actual_tr = [tr[0] + dx_top - dx_right, tr[1] + dy_top - dy_right]
            actual_br = [br[0] + dx_bottom + dx_right, br[1] + dy_bottom + dy_right]
            actual_bl = [bl[0] - dx_bottom + dx_left, bl[1] + dy_bottom + dy_left]
            
            # Points are returned in TL, TR, BR, BL order
            return [actual_tl, actual_tr, actual_br, actual_bl]
        
        return None

    def warp_board(self, frame: np.ndarray) -> np.ndarray:
        """
        Applies perspective transform to get a top-down view of the board.
        Returns the original frame if not calibrated.
        """
        if self.transform_matrix is None:
            return frame
            
        return cv2.warpPerspective(frame, self.transform_matrix, (self.output_size, self.output_size))
        
    def get_square_crops(self, warped_frame: np.ndarray) -> dict:
        """
        Takes a warped 800x800 board image and returns a dict of 64 crops
        keyed by algebraic notation (e.g., 'a1', 'e4').
        Assumes board is oriented with White at bottom (ranks 1-2).
        """
        square_size = self.output_size // 8
        crops = {}
        
        for row in range(8):
            for col in range(8):
                # Rank 8 is row 0, Rank 1 is row 7
                rank = 8 - row
                # File A is col 0, File H is col 7
                file = chr(ord('a') + col)
                square_name = f"{file}{rank}"
                
                y_start = row * square_size
                y_end = y_start + square_size
                x_start = col * square_size
                x_end = x_start + square_size
                
                crops[square_name] = warped_frame[y_start:y_end, x_start:x_end]
                
        return crops

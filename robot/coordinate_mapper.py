class CoordinateMapper:
    def __init__(self, corners_config=None):
        if corners_config:
            self.corners = corners_config
        else:
            self.corners = {
                "a1": (0, 0, 0),
                "h1": (280, 0, 0),
                "a8": (0, 280, 0),
                "h8": (280, 280, 0)
            }
        self.safe_z = 100 # Safe height for moving
        self.pick_z = 10  # Height for picking/placing

    def calibrate(self, a1, h1, a8, h8):
        self.corners["a1"] = a1
        self.corners["h1"] = h1
        self.corners["a8"] = a8
        self.corners["h8"] = h8
        # In a real system, you would calculate the affine transform or interpolation grid here.

    def square_to_robot_coords(self, square: str):
        """
        Converts algebraic notation (e.g., 'e2') to physical robot coordinates (x, y) 
        using bilinear interpolation between the 4 calibrated corners.
        """
        file = ord(square[0]) - ord('a') # 0-7
        rank = int(square[1]) - 1        # 0-7

        # Normalize file and rank to [0.0, 1.0] representing the center of the square
        u = (file + 0.5) / 8.0
        v = (rank + 0.5) / 8.0

        a1_x, a1_y, _ = self.corners["a1"]
        h1_x, h1_y, _ = self.corners["h1"]
        a8_x, a8_y, _ = self.corners["a8"]
        h8_x, h8_y, _ = self.corners["h8"]

        # Interpolate along the bottom (rank 1) and top (rank 8) edges
        bottom_x = (1 - u) * a1_x + u * h1_x
        bottom_y = (1 - u) * a1_y + u * h1_y
        
        top_x = (1 - u) * a8_x + u * h8_x
        top_y = (1 - u) * a8_y + u * h8_y

        # Interpolate between the bottom and top edges
        x = (1 - v) * bottom_x + v * top_x
        y = (1 - v) * bottom_y + v * top_y

        return (x, y)

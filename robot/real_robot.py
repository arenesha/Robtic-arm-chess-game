import logging
import time
import serial
from .robot_controller import RobotController
from .coordinate_mapper import CoordinateMapper

logger = logging.getLogger(__name__)

class RealRobot(RobotController):
    def __init__(self, port: str = "COM3", baudrate: int = 115200, corners_config=None):
        self.port = port
        self.baudrate = baudrate
        self.status = "DISCONNECTED"
        self.mapper = CoordinateMapper(corners_config)
        self.serial = None

    def initialize(self) -> bool:
        logger.info(f"Connecting to real robot on {self.port} at {self.baudrate}")
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2) # Wait for GRBL/controller to boot
            self._send_gcode("G21") # Use millimeters
            self._send_gcode("G90") # Absolute positioning
            self._send_gcode("G28") # Home all axes
            self.status = "READY"
            return True
        except Exception as e:
            logger.error(f"Failed to connect to robot: {e}")
            self.status = "ERROR"
            return False

    def _send_gcode(self, cmd: str):
        if self.serial and self.serial.is_open:
            logger.info(f"Robot TX: {cmd}")
            self.serial.write(f"{cmd}\n".encode())
            # Simple wait for 'ok'
            while True:
                response = self.serial.readline().decode().strip()
                if response == 'ok':
                    break
                elif "error" in response.lower():
                    logger.error(f"Robot Error: {response}")
                    break
        else:
            logger.warning(f"Simulating TX (Not Connected): {cmd}")

    def move_piece(self, from_square: str, to_square: str) -> bool:
        if self.status not in ["READY", "MOVING"]:
            logger.error("Robot is not ready.")
            return False
            
        self.status = "MOVING"
        from_coords = self.mapper.square_to_robot_coords(from_square)
        to_coords = self.mapper.square_to_robot_coords(to_square)
        
        logger.info(f"REAL ROBOT: Picking at {from_coords}, Placing at {to_coords}")
        
        # Safe Z move
        self._send_gcode(f"G0 Z{self.mapper.safe_z} F1000")
        
        # Move to source
        self._send_gcode(f"G0 X{from_coords[0]:.1f} Y{from_coords[1]:.1f} F2000")
        self._send_gcode(f"G1 Z{self.mapper.pick_z} F500")
        
        # Close Gripper (assuming M3 controls an electromagnet or servo)
        self._send_gcode("M3 S1000")
        time.sleep(0.5)
        
        # Lift
        self._send_gcode(f"G0 Z{self.mapper.safe_z} F1000")
        
        # Move to dest
        self._send_gcode(f"G0 X{to_coords[0]:.1f} Y{to_coords[1]:.1f} F2000")
        self._send_gcode(f"G1 Z{self.mapper.pick_z} F500")
        
        # Open Gripper
        self._send_gcode("M5")
        time.sleep(0.5)
        
        # Lift and Home
        self._send_gcode(f"G0 Z{self.mapper.safe_z} F1000")
        self._send_gcode("G0 X0 Y0")
        
        self.status = "READY"
        return True

    def remove_piece(self, square: str) -> bool:
        logger.info(f"REAL ROBOT: Removing piece at {square}")
        return True

    def get_status(self) -> str:
        return self.status

    def arrange_board(self, current_fen: str) -> bool:
        if self.status not in ["READY", "MOVING"]:
            logger.error("Robot is not ready.")
            return False
            
        self.status = "MOVING"
        logger.info("REAL ROBOT: Starting board arrangement sequence.")
        
        import chess
        current_board = chess.Board(current_fen)
        start_board = chess.Board()
        
        # NOTE: This is a simplified arrangement that logs the intent.
        # Full implementation would require a path-planning algorithm 
        # and a physical capture graveyard.
        for sq in chess.SQUARES:
            target_piece = start_board.piece_at(sq)
            curr_piece = current_board.piece_at(sq)
            if target_piece and target_piece != curr_piece:
                logger.info(f"Need to place {target_piece.symbol()} at {chess.square_name(sq)}")
        
        # Home sequence
        self._send_gcode(f"G0 Z{self.mapper.safe_z} F1000")
        self._send_gcode("G0 X0 Y0 F2000")
        self.status = "READY"
        return True

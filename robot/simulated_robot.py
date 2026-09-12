import time
import logging
from .robot_controller import RobotController
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class SimulatedRobot(RobotController, QObject):
    # Signals for updating the UI during the simulated movement
    status_changed = Signal(str)
    action_changed = Signal(str)
    move_completed = Signal(bool)

    def __init__(self):
        QObject.__init__(self)
        self.status = "DISCONNECTED"
        self.current_action = ""

    def initialize(self) -> bool:
        self.set_status("INITIALIZING")
        time.sleep(0.5)
        self.set_status("READY")
        return True

    def set_status(self, status: str):
        self.status = status
        self.status_changed.emit(self.status)
        logger.info(f"Simulated Robot Status: {status}")

    def set_action(self, action: str):
        self.current_action = action
        self.action_changed.emit(self.current_action)
        logger.info(f"Simulated Robot Action: {action}")

    def move_piece(self, from_square: str, to_square: str) -> bool:
        self.set_status("MOVING")
        
        self.set_action(f"Moving to {from_square}")
        time.sleep(1.0)
        
        self.set_action(f"Picking piece at {from_square}")
        time.sleep(0.5)
        
        self.set_action(f"Moving to {to_square}")
        time.sleep(1.0)
        
        self.set_action(f"Placing piece at {to_square}")
        time.sleep(0.5)
        
        self.set_action("Returning HOME")
        time.sleep(1.0)
        
        self.set_status("READY")
        self.set_action("")
        
        self.move_completed.emit(True)
        return True

    def remove_piece(self, square: str) -> bool:
        self.set_status("MOVING")
        
        self.set_action(f"Moving to {square} to remove captured piece")
        time.sleep(1.0)
        
        self.set_action(f"Picking piece at {square}")
        time.sleep(0.5)
        
        self.set_action("Moving to capture area")
        time.sleep(1.0)
        
        self.set_action("Placing captured piece")
        time.sleep(0.5)
        
        self.set_status("READY")
        self.set_action("")
        return True

    def get_status(self) -> str:
        return self.status

    def arrange_board(self, current_fen: str) -> bool:
        self.set_status("MOVING")
        self.set_action("Arranging board back to start...")
        time.sleep(2.0)
        self.set_action("Returning HOME")
        time.sleep(1.0)
        self.set_status("READY")
        self.set_action("")
        self.move_completed.emit(True)
        return True

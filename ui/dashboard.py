import os
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QRadioButton, QButtonGroup, 
                               QGroupBox, QTextEdit, QDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np

from chess_engine.game import ChessGame
from chess_engine.stockfish import StockfishEngine
from robot.simulated_robot import SimulatedRobot
from simulation.chessboard import ChessboardWidget
from camera.camera import Camera
from camera.board_detector import BoardDetector
from vision.piece_detector import PieceDetector
from vision.move_detector import MoveDetector

logger = logging.getLogger(__name__)

class RobotWorker(QThread):
    finished_move = Signal(bool)
    
    def __init__(self, robot, from_sq, to_sq):
        super().__init__()
        self.robot = robot
        self.from_sq = from_sq
        self.to_sq = to_sq
        
    def run(self):
        result = self.robot.move_piece(self.from_sq, self.to_sq)
        self.finished_move.emit(result)

class ArrangeWorker(QThread):
    finished_arrange = Signal(bool)
    
    def __init__(self, robot, current_fen):
        super().__init__()
        self.robot = robot
        self.current_fen = current_fen
        
    def run(self):
        result = self.robot.arrange_board(self.current_fen)
        self.finished_arrange.emit(result)

class CalibrationDialog(QDialog):
    def __init__(self, camera, board_detector, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibrate Chessboard")
        self.camera = camera
        self.board_detector = board_detector
        self.points = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.info_label = QLabel("Click the 4 corners of the board (Top-Left, Top-Right, Bottom-Right, Bottom-Left).")
        layout.addWidget(self.info_label)
        
        self.image_label = QLabel()
        self.image_label.mousePressEvent = self.on_image_clicked
        layout.addWidget(self.image_label)
        
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Points")
        self.clear_btn.clicked.connect(self.clear_points)
        self.save_btn = QPushButton("Save & Close")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        frame = self.camera.get_frame()
        if frame is not None:
            # Draw points
            display_frame = frame.copy()
            for pt in self.points:
                cv2.circle(display_frame, pt, 5, (0, 255, 0), -1)
            
            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    def on_image_clicked(self, event):
        if len(self.points) < 4:
            self.points.append((int(event.position().x()), int(event.position().y())))
            if len(self.points) == 4:
                self.save_btn.setEnabled(True)
                self.info_label.setText("4 points selected. You can save or clear.")

    def clear_points(self):
        self.points = []
        self.save_btn.setEnabled(False)
        self.info_label.setText("Click the 4 corners of the board (Top-Left, Top-Right, Bottom-Right, Bottom-Left).")

    def accept(self):
        if len(self.points) == 4:
            self.board_detector.calibrate(self.points)
            logger.info(f"Calibrated with points: {self.points}")
        super().accept()

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Robotic Chess Player")
        self.resize(1000, 700)
        
        from ui.style import get_stylesheet
        self.setStyleSheet(get_stylesheet())
        
        # Core components
        from config.config_manager import ConfigManager
        self.config = ConfigManager()
        
        self.game = ChessGame()
        
        sf_path = self.config.get("stockfish", "path", "stockfish")
        sf_depth = self.config.get("stockfish", "depth", 15)
        self.stockfish = StockfishEngine(stockfish_path=sf_path, depth=sf_depth) 
        self.robot = SimulatedRobot()
        
        # Vision components
        cam_id = self.config.get("camera", "camera_id", 0)
        self.camera = Camera(camera_id=cam_id)
        self.board_detector = BoardDetector()
        
        yolo_path = self.config.get("vision", "yolo_model_path", "")
        self.piece_detector = PieceDetector(model_path=yolo_path if yolo_path else None)
        self.move_detector = MoveDetector()
        
        self.previous_gray_frame = None
        self.stable_frames = 0
        self.REQUIRED_STABLE_FRAMES = 45 # ~1.5 seconds at 30 fps
        self.last_known_board_state = {}
        
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_view)
        
        from camera.calibrator import CameraRobotCalibrator
        self.calibrator = CameraRobotCalibrator()
        
        self.human_wins = 0
        self.robot_wins = 0
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel: Controls & Status
        left_panel = QVBoxLayout()
        
        # Mode Selection
        mode_group = QGroupBox("MODE")
        mode_layout = QHBoxLayout()
        self.sim_radio = QRadioButton("SIMULATION")
        self.sim_radio.setChecked(True)
        self.real_radio = QRadioButton("REAL HARDWARE")
        mode_layout.addWidget(self.sim_radio)
        mode_layout.addWidget(self.real_radio)
        mode_group.setLayout(mode_layout)
        left_panel.addWidget(mode_group)
        
        # Series Score
        score_group = QGroupBox("SERIES SCORE (Best of 3)")
        score_layout = QHBoxLayout()
        self.score_label = QLabel("Human: 0  |  Robot: 0")
        self.score_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #F1C40F;")
        score_layout.addWidget(self.score_label, alignment=Qt.AlignCenter)
        score_group.setLayout(score_layout)
        left_panel.addWidget(score_group)
        
        # Game Status
        status_group = QGroupBox("GAME STATUS")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        self.turn_label = QLabel("🟢 YOUR TURN (HUMAN)")
        self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #2ECC71; background-color: #1A3A2A; padding: 15px; border-radius: 8px;")
        self.turn_label.setAlignment(Qt.AlignCenter)
        
        self.human_move_label = QLabel("Human Move: -")
        self.robot_move_label = QLabel("Robot Move: -")
        self.robot_status_label = QLabel("Status: READY")
        self.robot_action_label = QLabel("Action: -")
        
        status_layout.addWidget(self.turn_label)
        status_layout.addWidget(self.human_move_label)
        status_layout.addWidget(self.robot_move_label)
        status_layout.addWidget(self.robot_status_label)
        status_layout.addWidget(self.robot_action_label)
        status_group.setLayout(status_layout)
        left_panel.addWidget(status_group)
        
        # System checks
        sys_group = QGroupBox("SYSTEM")
        sys_layout = QVBoxLayout()
        sf_status = "✓" if self.stockfish.is_ready() else "✗ (Check PATH)"
        self.sys_stockfish = QLabel(f"Stockfish: {sf_status}")
        self.sys_camera = QLabel("Camera: Virtual")
        self.sys_robot = QLabel("Robot: Virtual")
        sys_layout.addWidget(self.sys_stockfish)
        sys_layout.addWidget(self.sys_camera)
        sys_layout.addWidget(self.sys_robot)
        sys_group.setLayout(sys_layout)
        left_panel.addWidget(sys_group)
        
        # Action Buttons
        self.auto_calibrate_btn = QPushButton("AUTO-DETECT BOARD")
        self.auto_calibrate_btn.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; font-size: 14px;")
        self.auto_calibrate_btn.setEnabled(False)
        self.auto_calibrate_btn.clicked.connect(self.on_auto_calibrate)
        left_panel.addWidget(self.auto_calibrate_btn)

        self.calibrate_btn = QPushButton("MANUAL CALIBRATE CAMERA")
        self.calibrate_btn.setEnabled(False)
        self.calibrate_btn.clicked.connect(self.open_calibration)
        left_panel.addWidget(self.calibrate_btn)
        
        self.restart_btn = QPushButton("ARRANGE BOARD FOR NEXT GAME")
        self.restart_btn.setStyleSheet("background-color: #9B59B6; color: white; font-weight: bold; font-size: 16px; margin-top: 10px;")
        self.restart_btn.clicked.connect(self.on_restart_clicked)
        self.restart_btn.hide()
        left_panel.addWidget(self.restart_btn)
        
        left_panel.addStretch()
        
        # Right Panel: Board / Camera View
        right_panel = QVBoxLayout()
        self.board_widget = ChessboardWidget()
        
        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.hide()
        
        right_panel.addWidget(self.board_widget, alignment=Qt.AlignCenter)
        right_panel.addWidget(self.camera_view, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

    def setup_connections(self):
        self.board_widget.move_requested.connect(self.on_human_move)
        
        self.robot.status_changed.connect(self.update_robot_status)
        self.robot.action_changed.connect(self.update_robot_action)
        
        self.sim_radio.toggled.connect(self.toggle_mode)
        self.real_radio.toggled.connect(self.toggle_mode)
        
        self.calibrate_btn.clicked.connect(self.open_calibration)

    def update_robot_status(self, status):
        self.robot_status_label.setText(f"Status: {status}")

    def update_robot_action(self, action):
        self.robot_action_label.setText(f"Action: {action}")
        if action.startswith("Moving to") or action.startswith("Picking piece at") or action.startswith("Placing piece at"):
            square = action.split(" ")[-1]
            if len(square) == 2:
                self.board_widget.animate_arm_to_square(square)
        elif action == "Returning HOME" or not action:
            self.board_widget.animate_arm_home()

    def on_human_move(self, move_str):
        if "HUMAN" not in self.turn_label.text():
            return
            
        self.human_move_label.setText(f"Human Move: {move_str[:2]} -> {move_str[2:]}")
        self.game.push_move(move_str)
        self.board_widget.sync_board(self.game.get_fen())
        
        if self.game.is_game_over():
            self.handle_game_over()
            return
            
        self.turn_label.setText("🤔 ROBOT IS THINKING...")
        self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #F39C12; background-color: #4A3B1B; padding: 15px; border-radius: 8px;")
        self.trigger_ai_move()

    def trigger_ai_move(self):
        if not self.stockfish.is_ready():
            logger.error("Stockfish not available. Cannot make move.")
            self.turn_label.setText("❌ AI ERROR (Check Stockfish)")
            self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #E74C3C; background-color: #4A1B1B; padding: 15px; border-radius: 8px;")
            return
            
        best_move = self.stockfish.get_best_move(self.game.get_fen())
        if best_move:
            self.robot_move_label.setText(f"Robot Move: {best_move[:2]} -> {best_move[2:]}")
            self.game.push_move(best_move)
            
            # Start robot animation
            self.turn_label.setText("🤖 ROBOT IS MOVING...")
            self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #E74C3C; background-color: #4A1B1B; padding: 15px; border-radius: 8px;")
            
            # Disable board interaction during robot move
            self.board_widget.setEnabled(False)
            
            self.worker = RobotWorker(self.robot, best_move[:2], best_move[2:])
            self.worker.finished_move.connect(self.on_robot_finished)
            self.worker.start()

    def on_robot_finished(self, success):
        self.board_widget.sync_board(self.game.get_fen())
        self.board_widget.setEnabled(True)
        
        if self.game.is_game_over():
            self.handle_game_over()
            return
            
        if self.real_radio.isChecked():
            self.turn_label.setText("👀 VERIFYING BOARD...")
            self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #3498DB; background-color: #1B3A4A; padding: 15px; border-radius: 8px;")
            self.stable_frames = 0
        else:
            self.turn_label.setText("🟢 YOUR TURN (HUMAN)")
            self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #2ECC71; background-color: #1A3A2A; padding: 15px; border-radius: 8px;")

    def handle_game_over(self):
        result = self.game.get_result()
        if result == "1-0":
            self.human_wins += 1
            winner = "HUMAN WINS!"
        elif result == "0-1":
            self.robot_wins += 1
            winner = "ROBOT WINS!"
        else:
            winner = "DRAW!"
            
        self.score_label.setText(f"Human: {self.human_wins}  |  Robot: {self.robot_wins}")
        
        if self.human_wins == 2 or self.robot_wins == 2:
            series_winner = "HUMAN" if self.human_wins == 2 else "ROBOT"
            self.turn_label.setText(f"🏆 {series_winner} WINS THE SERIES!")
            self.restart_btn.setText("RESTART SERIES")
        else:
            self.turn_label.setText(f"🏁 GAME OVER: {winner}")
            self.restart_btn.setText("ARRANGE BOARD FOR NEXT GAME")
            
        self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #9B59B6; background-color: #3B1B4A; padding: 15px; border-radius: 8px;")
        self.restart_btn.show()

    def on_restart_clicked(self):
        self.restart_btn.hide()
        self.turn_label.setText("🤖 ARRANGING BOARD...")
        self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #3498DB; background-color: #1B3A4A; padding: 15px; border-radius: 8px;")
        self.board_widget.setEnabled(False)
        
        self.arrange_worker = ArrangeWorker(self.robot, self.game.get_fen())
        self.arrange_worker.finished_arrange.connect(self.on_arrange_finished)
        self.arrange_worker.start()

    def on_arrange_finished(self, success):
        self.game.reset()
        self.board_widget.sync_board(self.game.get_fen())
        self.board_widget.setEnabled(True)
        self.human_move_label.setText("Human Move: -")
        self.robot_move_label.setText("Robot Move: -")
        
        if self.human_wins == 2 or self.robot_wins == 2:
            self.human_wins = 0
            self.robot_wins = 0
            self.score_label.setText("Human: 0  |  Robot: 0")
            
        self.turn_label.setText("🟢 YOUR TURN (HUMAN)")
        self.turn_label.setStyleSheet("font-weight: bold; font-size: 20px; color: #2ECC71; background-color: #1A3A2A; padding: 15px; border-radius: 8px;")

    def toggle_mode(self):
        if self.real_radio.isChecked():
            # Try to init hardware
            self.sys_camera.setText("Camera: Checking...")
            self.sys_robot.setText("Robot: Checking...")
            
            camera_ready = self.camera.initialize()
            
            if camera_ready:
                self.sys_camera.setText("Camera: ✓ Connected")
                self.calibrate_btn.setEnabled(True)
                self.auto_calibrate_btn.setEnabled(True)
                self.board_widget.hide()
                self.camera_view.show()
                self.camera_timer.start(30)
            else:
                self.sys_camera.setText("Camera: ✗ Not Connected")
            
            # Since robot hardware isn't attached on dev machine, fail gracefully
            # But we instantiate RealRobot anyway to test the logic
            from robot.real_robot import RealRobot
            corners_config = self.config.get("robot", "corners", None)
            port = self.config.get("robot", "port", "COM3")
            baudrate = self.config.get("robot", "baudrate", 115200)
            
            self.robot = RealRobot(port=port, baudrate=baudrate, corners_config=corners_config)
            robot_ready = self.robot.initialize()
            
            if robot_ready:
                self.sys_robot.setText("Robot:  ✓ Connected")
                self.robot_status_label.setText("Status: READY")
            else:
                self.sys_robot.setText("Robot:  ✗ Not Connected")
                self.robot_status_label.setText("Real hardware is not fully ready (Simulating TX).")
            
        else:
            self.camera_timer.stop()
            self.camera.release()
            
            from robot.simulated_robot import SimulatedRobot
            self.robot = SimulatedRobot()
            self.robot.move_completed.connect(self.on_robot_finished)
            
            self.sys_camera.setText("Camera: Virtual")
            self.sys_robot.setText("Robot: Virtual")
            self.robot_status_label.setText("Status: READY")
            self.robot_action_label.setText("Action: -")
            self.calibrate_btn.setEnabled(False)
            self.auto_calibrate_btn.setEnabled(False)
            self.camera_view.hide()
            self.board_widget.show()

    def open_calibration(self):
        if self.camera.cap and self.camera.cap.isOpened():
            dialog = CalibrationDialog(self.camera, self.board_detector, self)
            dialog.exec()

    def on_auto_calibrate(self):
        frame = self.camera.get_frame()
        if frame is not None:
            corners = self.board_detector.auto_find_corners(frame)
            if corners:
                self.board_detector.calibrate(corners)
                self.info_label.setText("Auto-Calibration Successful!")
                
                # If we have a saved Camera-to-Robot transform matrix, we can map pixels to mm:
                if self.calibrator.transform_matrix is not None:
                    try:
                        # corners are in TL, TR, BR, BL
                        # map them to robot coords
                        a8_mm = self.calibrator.pixel_to_mm(*corners[0]) # TL
                        h8_mm = self.calibrator.pixel_to_mm(*corners[1]) # TR
                        h1_mm = self.calibrator.pixel_to_mm(*corners[2]) # BR
                        a1_mm = self.calibrator.pixel_to_mm(*corners[3]) # BL
                        
                        corners_config = {
                            "a1": (a1_mm[0], a1_mm[1], 0),
                            "h1": (h1_mm[0], h1_mm[1], 0),
                            "a8": (a8_mm[0], a8_mm[1], 0),
                            "h8": (h8_mm[0], h8_mm[1], 0)
                        }
                        self.robot.mapper.corners = corners_config
                        self.config.set("robot", "corners", corners_config)
                        self.info_label.setText("Board physical mm calculated automatically!")
                    except Exception as e:
                        logger.error(f"Failed to apply camera-to-robot transform: {e}")
            else:
                self.info_label.setText("Auto-Detect Failed. Ensure board is visible.")

    def update_camera_view(self):
        frame = self.camera.get_frame()
        if frame is not None:
            # If calibrated, show warped view and process
            if self.board_detector.transform_matrix is not None:
                display_frame = self.board_detector.warp_board(frame)
                self.process_auto_move(display_frame)
            else:
                display_frame = frame
                
            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
            self.camera_view.setPixmap(QPixmap.fromImage(qt_img).scaled(
                self.camera_view.width(), self.camera_view.height(), Qt.KeepAspectRatio))

    def process_auto_move(self, warped_frame: np.ndarray):
        current_turn = self.turn_label.text()
        
        # We only process frames for Auto-Move (HUMAN) or Verification (VERIFYING)
        if current_turn not in ["Current Turn: HUMAN", "Current Turn: VERIFYING"]:
            return

        gray = cv2.cvtColor(warped_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_gray_frame is None:
            self.previous_gray_frame = gray
            crops = self.board_detector.get_square_crops(warped_frame)
            self.last_known_board_state = self.piece_detector.detect_pieces(crops)
            return

        # Compute absolute difference for motion
        frame_delta = cv2.absdiff(self.previous_gray_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        motion_pixels = cv2.countNonZero(thresh)
        self.previous_gray_frame = gray

        if motion_pixels > 500:
            self.stable_frames = 0
        else:
            self.stable_frames += 1

        if self.stable_frames == self.REQUIRED_STABLE_FRAMES:
            crops = self.board_detector.get_square_crops(warped_frame)
            current_state = self.piece_detector.detect_pieces(crops)
            
            if current_turn == "Current Turn: HUMAN":
                move_str = self.move_detector.detect_move(self.last_known_board_state, current_state)
                if move_str and self.game.is_valid_move(move_str):
                    logger.info(f"Auto-detected move: {move_str}")
                    self.on_human_move(move_str)
                    self.last_known_board_state = current_state
            
            elif current_turn == "Current Turn: VERIFYING":
                logger.info("Verifying robot move...")
                # Here we would do a deep check. For now, update baseline and proceed.
                self.last_known_board_state = current_state
                self.turn_label.setText("Current Turn: HUMAN")
                self.robot_status_label.setText("Status: READY")
                self.robot_action_label.setText("Action: -")
            
            self.stable_frames += 1

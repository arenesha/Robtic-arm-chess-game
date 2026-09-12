import sys
import chess
from PySide6.QtWidgets import (QWidget, QGridLayout, QPushButton, QVBoxLayout, 
                               QLabel, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, Signal, QVariantAnimation, QPointF
from PySide6.QtGui import QFont, QPainter, QPen, QColor

# Unicode mapping for chess pieces
PIECE_UNICODE = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}

class ArmOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.effector_pos = QPointF(-100, -100) # Start offscreen
        self.base_pos = QPointF(0, 0) # Will be set on resize
        
        self.anim = QVariantAnimation(self)
        self.anim.valueChanged.connect(self.update_pos)
        self.anim.setDuration(600)

    def update_pos(self, pos):
        self.effector_pos = pos
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.base_pos = QPointF(self.width() / 2, -30) # Base is slightly above the board

    def move_to(self, target_pos):
        self.anim.stop()
        self.anim.setStartValue(self.effector_pos)
        self.anim.setEndValue(target_pos)
        self.anim.start()

    def paintEvent(self, event):
        if self.effector_pos.x() < 0 and self.effector_pos.y() < 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw base
        painter.setBrush(QColor("#2C3E50"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.base_pos, 25, 25)
        
        # Simple 2-link IK (just visual approximations for a sleek look)
        dx = self.effector_pos.x() - self.base_pos.x()
        dy = self.effector_pos.y() - self.base_pos.y()
        
        elbow_x = self.base_pos.x() + dx * 0.7 + 60
        elbow_y = self.base_pos.y() + dy * 0.3 + 20
        elbow = QPointF(elbow_x, elbow_y)
        
        # Draw links
        pen = QPen(QColor("#7F8C8D"), 14, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.base_pos, elbow)
        painter.drawLine(elbow, self.effector_pos)
        
        # Draw joints
        painter.setBrush(QColor("#E74C3C"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(elbow, 12, 12)
        
        # Draw effector
        painter.setBrush(QColor("#2ECC71"))
        painter.drawEllipse(self.effector_pos, 16, 16)

class ChessboardWidget(QWidget):
    # Emits standard algebraic notation like "e2e4"
    move_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.buttons = {}
        self.selected_square = None
        self.init_ui()

    def init_ui(self):
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        
        # Create an 8x8 grid of buttons
        font = QFont("Arial", 52, QFont.Bold)
        for row in range(8):
            for col in range(8):
                btn = QPushButton()
                btn.setFixedSize(80, 80)
                btn.setFont(font)
                
                # Chess logic uses 0-63, a1 is 0, h8 is 63.
                square_idx = chess.square(col, 7 - row)
                btn.setProperty("square", square_idx)
                
                btn.clicked.connect(self.on_square_clicked)
                
                self.buttons[square_idx] = btn
                self.grid.addWidget(btn, row, col)
                
        self.setLayout(self.grid)
        self.overlay = ArmOverlay(self)
        self.update_board()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())

    def get_color(self, square_idx, selected=False, highlight=False):
        row = 7 - chess.square_rank(square_idx)
        col = chess.square_file(square_idx)
        
        # Modern chess.com style colors
        light_sq = "#EBECD0"
        dark_sq = "#739552"
        
        if selected:
            return "#F4F680" if (row + col) % 2 == 0 else "#BACA44"
        if highlight:
            return "#F4F680" if (row + col) % 2 == 0 else "#BACA44"
            
        return light_sq if (row + col) % 2 == 0 else dark_sq

    def update_board(self, highlight_squares=None):
        if highlight_squares is None:
            highlight_squares = []
            
        for square_idx, btn in self.buttons.items():
            piece = self.board.piece_at(square_idx)
            if piece:
                btn.setText(PIECE_UNICODE[piece.symbol()])
            else:
                btn.setText("")
                
            is_selected = (self.selected_square == square_idx)
            is_highlighted = (square_idx in highlight_squares)
            
            color = self.get_color(square_idx, is_selected, is_highlighted)
            btn.setStyleSheet(f"background-color: {color}; border: none; color: #111111; font-size: 52px; font-weight: bold; padding: 0px; border-radius: 0px;")

    def on_square_clicked(self):
        btn = self.sender()
        square_idx = btn.property("square")
        
        if self.selected_square is None:
            piece = self.board.piece_at(square_idx)
            if piece and piece.color == self.board.turn:
                self.selected_square = square_idx
                self.update_board()
        else:
            move_str = chess.square_name(self.selected_square) + chess.square_name(square_idx)
            
            if (self.board.piece_at(self.selected_square) and 
                self.board.piece_at(self.selected_square).piece_type == chess.PAWN):
                if chess.square_rank(square_idx) == 0 or chess.square_rank(square_idx) == 7:
                    move_str += "q"
            
            move = chess.Move.from_uci(move_str)
            
            if move in self.board.legal_moves:
                self.move_requested.emit(move_str)
            
            self.selected_square = None
            self.update_board()

    def sync_board(self, fen):
        self.board.set_fen(fen)
        self.update_board()

    def animate_arm_to_square(self, square_str):
        if len(square_str) != 2:
            return
        idx = chess.parse_square(square_str)
        btn = self.buttons.get(idx)
        if btn:
            center = btn.geometry().center()
            self.overlay.move_to(QPointF(center.x(), center.y()))
            
    def animate_arm_home(self):
        self.overlay.move_to(QPointF(-100, -100))

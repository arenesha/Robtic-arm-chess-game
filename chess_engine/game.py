import chess
import logging

logger = logging.getLogger(__name__)

class ChessGame:
    def __init__(self):
        self.board = chess.Board()

    def is_valid_move(self, move_str: str) -> bool:
        """Checks if a move string (e.g. 'e2e4') is legal on the current board."""
        try:
            move = chess.Move.from_uci(move_str)
            return move in self.board.legal_moves
        except ValueError:
            return False

    def push_move(self, move_str: str) -> bool:
        """Executes a move on the board if legal."""
        if self.is_valid_move(move_str):
            move = chess.Move.from_uci(move_str)
            self.board.push(move)
            logger.info(f"Move executed: {move_str}")
            return True
        logger.warning(f"Attempted invalid move: {move_str}")
        return False

    def get_fen(self) -> str:
        """Returns the current board state in FEN notation."""
        return self.board.fen()

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def get_result(self) -> str:
        return self.board.result()

    def reset(self):
        self.board.reset()

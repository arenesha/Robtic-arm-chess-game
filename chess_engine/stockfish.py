from stockfish import Stockfish
import logging

logger = logging.getLogger(__name__)

class StockfishEngine:
    def __init__(self, stockfish_path: str = "stockfish", depth: int = 15, threads: int = 2):
        """
        Initializes the Stockfish engine.
        Ensure that the stockfish binary is installed and in the PATH, or provide the exact path.
        """
        try:
            self.stockfish = Stockfish(path=stockfish_path, depth=depth, parameters={"Threads": threads, "Minimum Thinking Time": 30})
            logger.info("Stockfish engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Stockfish: {e}")
            self.stockfish = None

    def get_best_move(self, fen: str) -> str:
        """
        Takes a FEN string representing the board state and returns the best move in UCI format (e.g., 'e2e4').
        """
        if not self.stockfish:
            logger.error("Stockfish is not available.")
            return ""
        
        try:
            self.stockfish.set_fen_position(fen)
            best_move = self.stockfish.get_best_move()
            return best_move if best_move else ""
        except Exception as e:
            logger.error(f"Error getting best move from Stockfish: {e}")
            return ""

    def is_ready(self) -> bool:
        return self.stockfish is not None

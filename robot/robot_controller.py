class RobotController:
    def initialize(self) -> bool:
        """Initializes the connection and homes the robot."""
        raise NotImplementedError

    def move_piece(self, from_square: str, to_square: str) -> bool:
        """
        Executes a pick and place operation from the source square to the destination square.
        """
        raise NotImplementedError
    
    def remove_piece(self, square: str) -> bool:
        """
        Removes a piece from the board (e.g., for captures or en passant).
        """
        raise NotImplementedError

    def get_status(self) -> str:
        """Returns the current status of the robot (e.g., 'READY', 'MOVING', 'ERROR')."""
        raise NotImplementedError

    def arrange_board(self, current_fen: str) -> bool:
        """
        Physically (or simulatively) arranges the pieces from the current_fen back to the starting position.
        """
        raise NotImplementedError

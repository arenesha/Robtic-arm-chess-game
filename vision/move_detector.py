class MoveDetector:
    def __init__(self):
        pass

    def detect_move(self, previous_state: dict, current_state: dict) -> str:
        """
        Compares the previous piece dictionary with the current one to deduce the human's move.
        Returns UCI string (e.g., 'e2e4') or empty string if no valid move detected.
        Assumes dict values are either a string (piece name / "Occupied") or None.
        """
        disappeared = []
        appeared = []
        
        for square in previous_state.keys():
            prev = previous_state.get(square)
            curr = current_state.get(square)
            
            if prev is not None and curr is None:
                disappeared.append(square)
            elif prev is None and curr is not None:
                appeared.append(square)
            elif prev is not None and curr is not None and prev != curr:
                # E.g., Black piece replaced by White piece (Capture with full model)
                disappeared.append(square)
                appeared.append(square)

        # Standard Move (e.g., e2 -> e4)
        if len(disappeared) == 1 and len(appeared) == 1:
            return f"{disappeared[0]}{appeared[0]}"
            
        # Capture (e.g., e4xe5). With fallback, both were occupied, now one is empty, one is occupied.
        # Wait, if e4 moves to e5 and captures, e4 becomes empty (disappeared), e5 stays occupied.
        if len(disappeared) == 1 and len(appeared) == 0:
            # We don't know the destination if it was just "Occupied" -> "Occupied". 
            # We would need a real piece classifier, or to track hand movement.
            # But with a full YOLO model, we'd see 'White Pawn' at e5 replace 'Black Pawn' at e5.
            pass
            
        # Castling: 2 disappeared, 2 appeared
        if len(disappeared) == 2 and len(appeared) == 2:
            # E1, H1 disappear. G1, F1 appear. Move is E1G1.
            # Simplified castling check: find the king's start and end.
            kings_start = [s for s in disappeared if 'e1' in s or 'e8' in s]
            if kings_start:
                king_start = kings_start[0]
                # If E1 disappeared, and G1 appeared
                if king_start == 'e1' and 'g1' in appeared: return 'e1g1'
                if king_start == 'e1' and 'c1' in appeared: return 'e1c1'
                if king_start == 'e8' and 'g8' in appeared: return 'e8g8'
                if king_start == 'e8' and 'c8' in appeared: return 'e8c8'
                
        return ""

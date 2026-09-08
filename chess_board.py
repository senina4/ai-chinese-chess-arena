from xiangqi import Env, Camp

PIECE_NAMES = {
    21: "帥", 22: "仕", 23: "相", 24: "傌", 25: "俥", 26: "炮", 27: "兵",
    11: "將", 12: "士", 13: "象", 14: "馬", 15: "車", 16: "砲", 17: "卒",
    0: "．",
}

PIECE_LETTERS = {
    21: "K", 22: "A", 23: "B", 24: "N", 25: "R", 26: "C", 27: "P",
    11: "k", 12: "a", 13: "b", 14: "n", 15: "r", 16: "c", 17: "p",
}


class ChessBoard:
    def __init__(self):
        self.env = Env()

    def reset(self):
        return self.env.reset()

    def get_ascii(self) -> str:
        grid = self.env.board.encode()
        lines = []
        lines.append("  a  b  c  d  e  f  g  h  i")
        # row 0 = black back rank = ICCS row 9, printed at top
        for internal_row in range(10):
            iccs_row = 9 - internal_row
            pieces = [PIECE_NAMES[grid[internal_row][col]] for col in range(9)]
            lines.append(f"{iccs_row} {' '.join(pieces)}")
        return "\n".join(lines)

    def get_valid_actions(self) -> list[str]:
        return self.env.get_valid_actions()

    def make_move(self, move: str) -> tuple:
        return self.env.step(move)

    def get_fen(self) -> str:
        return self.env.to_fen()

    def cur_player(self) -> str:
        return "red" if self.env.cur_player == Camp.RED else "black"

    def is_done(self) -> bool:
        return self.env.done

    def get_winner(self) -> str | None:
        if self.env.winner is None:
            return None
        return "red" if self.env.winner == Camp.RED else "black"

    def move_to_chinese(self, move: str) -> str:
        """Convert ICCS move to a short description like '馬 b0->c2'."""
        src_col = ord(move[0]) - ord('a')
        src_row = 9 - int(move[1])
        grid = self.env.board.encode()
        piece_code = grid[src_row][src_col]
        piece_name = PIECE_NAMES.get(piece_code, "？")
        return f"{piece_name} {move[:2]}->{move[2:]}"

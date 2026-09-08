import time

from chess_board import ChessBoard
from ai_player import AIPlayer
from config import MAX_RETRIES


def play_game(red: AIPlayer, black: AIPlayer, game_id: int = 0,
              on_event=None) -> dict:
    """Play a single game. on_event(event_type, data) is called for live updates."""
    board = ChessBoard()
    board.reset()

    moves = []
    move_history = []
    illegal_counts = {"red": 0, "black": 0}
    reason = None
    forced_winner = None

    def emit(event_type, data=None):
        if on_event:
            on_event(event_type, data or {})

    print(f"  Game #{game_id}: {red.name} (紅) vs {black.name} (黑)")
    emit("game_start", {
        "game_id": game_id,
        "red": red.name,
        "black": black.name,
        "board": board.get_ascii(),
        "fen": board.get_fen(),
    })

    while not board.is_done():
        color = board.cur_player()
        player = red if color == "red" else black
        valid_actions = board.get_valid_actions()
        fen_before = board.get_fen()

        emit("thinking", {
            "game_id": game_id,
            "color": color,
            "model": player.name,
        })

        illegal_attempts = []
        move = None
        thinking = ""

        for attempt in range(MAX_RETRIES + 1):
            if attempt == 0:
                response = player.get_move(
                    board.get_ascii(), valid_actions, move_history, color,
                )
            else:
                response = player.get_retry(
                    response.get("move", ""), valid_actions,
                )

            thinking = response.get("thinking", "")
            candidate = response.get("move")

            if candidate and candidate in valid_actions:
                move = candidate
                break

            illegal_counts[color] += 1
            illegal_attempts.append({
                "attempt": attempt + 1,
                "move": candidate,
                "thinking": thinking,
            })
            print(f"    {color} illegal move: {candidate} (attempt {attempt + 1}/{MAX_RETRIES + 1})")
            emit("illegal_move", {
                "game_id": game_id,
                "color": color,
                "model": player.name,
                "move": candidate,
                "attempt": attempt + 1,
            })

        if move is None:
            forced_winner = "black" if color == "red" else "red"
            reason = "illegal_move_limit"
            print(f"    {color} exceeded retry limit, loses.")
            break

        desc = board.move_to_chinese(move)
        obs, reward, done, info = board.make_move(move)

        move_record = {
            "turn": len(moves) + 1,
            "color": color,
            "move": move,
            "description": desc,
            "thinking": thinking,
            "fen_before": fen_before,
            "illegal_attempts": illegal_attempts,
        }
        moves.append(move_record)
        move_history.append({"color": color, "move": move})

        emit("move", {
            "game_id": game_id,
            "color": color,
            "model": player.name,
            "move": move,
            "description": desc,
            "thinking": thinking,
            "board": board.get_ascii(),
            "fen": board.get_fen(),
            "turn": len(moves),
            "illegal_attempts": len(illegal_attempts),
        })

        if done and reason is None:
            winner = board.get_winner()
            if winner is None:
                reason = "draw"
            elif reward == 1:
                reason = "checkmate"
            else:
                reason = "game_over"

    winner = forced_winner if forced_winner else board.get_winner()
    if reason is None:
        reason = "draw" if winner is None else "unknown"

    result_str = f"{winner}方勝" if winner else "和棋"
    print(f"    Result: {result_str} ({reason}), {len(moves)} moves")

    result = {
        "game_id": game_id,
        "red": red.name,
        "black": black.name,
        "winner": winner,
        "reason": reason,
        "moves": moves,
        "total_moves": len(moves),
        "illegal_counts": illegal_counts,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    emit("game_end", {
        "game_id": game_id,
        "red": red.name,
        "black": black.name,
        "winner": winner,
        "reason": reason,
        "total_moves": len(moves),
        "illegal_counts": illegal_counts,
    })

    return result

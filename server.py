import threading
from itertools import combinations

from flask import Flask, render_template
from flask_socketio import SocketIO

from config import MODELS, GAMES_PER_PAIR
from ai_player import AIPlayer
from game import play_game
from stats import generate_report

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

tournament_state = {
    "status": "waiting",
    "records": [],
    "current_game": None,
}


def emit_event(event_type, data):
    if event_type == "game_start":
        tournament_state["current_game"] = data
    elif event_type == "game_end":
        tournament_state["current_game"] = None
    socketio.emit(event_type, data)


def run_tournament():
    tournament_state["status"] = "running"
    socketio.emit("tournament_start", {
        "models": [m["name"] for m in MODELS],
        "games_per_pair": GAMES_PER_PAIR,
        "total_games": len(list(combinations(MODELS, 2))) * GAMES_PER_PAIR,
    })

    players = [AIPlayer(cfg) for cfg in MODELS]
    all_records = []
    game_counter = 1

    for p1, p2 in combinations(players, 2):
        for game_num in range(GAMES_PER_PAIR):
            if game_num < GAMES_PER_PAIR // 2:
                red, black = p1, p2
            else:
                red, black = p2, p1

            record = play_game(red, black, game_id=game_counter, on_event=emit_event)
            all_records.append(record)
            tournament_state["records"].append(record)
            game_counter += 1

    report = generate_report(all_records)
    tournament_state["status"] = "finished"
    socketio.emit("tournament_end", {"report": report})


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("start_tournament")
def handle_start():
    if tournament_state["status"] == "running":
        return
    tournament_state["status"] = "waiting"
    tournament_state["records"] = []
    tournament_state["current_game"] = None
    thread = threading.Thread(target=run_tournament, daemon=True)
    thread.start()


if __name__ == "__main__":
    print("Starting AI Chinese Chess Arena Web UI...")
    print("Open http://localhost:5000 in your browser")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)

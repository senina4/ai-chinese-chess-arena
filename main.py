from itertools import combinations

from config import MODELS, GAMES_PER_PAIR
from ai_player import AIPlayer
from game import play_game
from stats import generate_report


def main():
    players = [AIPlayer(cfg) for cfg in MODELS]
    all_records = []
    game_counter = 1

    print(f"=== AI Chinese Chess Arena ===")
    print(f"Models: {', '.join(p.name for p in players)}")
    print(f"Games per pair: {GAMES_PER_PAIR} ({GAMES_PER_PAIR // 2} as red, {GAMES_PER_PAIR // 2} as black)")
    print(f"Total games: {len(list(combinations(players, 2))) * GAMES_PER_PAIR}")
    print()

    for p1, p2 in combinations(players, 2):
        print(f"--- {p1.name} vs {p2.name} ---")
        for game_num in range(GAMES_PER_PAIR):
            if game_num < GAMES_PER_PAIR // 2:
                red, black = p1, p2
            else:
                red, black = p2, p1

            record = play_game(red, black, game_id=game_counter)
            all_records.append(record)
            game_counter += 1
        print()

    print("=== Generating Report ===")
    generate_report(all_records)


if __name__ == "__main__":
    main()

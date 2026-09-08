import json
import os
from collections import defaultdict

from config import OUTPUT_DIR


def generate_report(records: list[dict]):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save raw data
    with open(os.path.join(OUTPUT_DIR, "raw_results.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    models = sorted({r["red"] for r in records} | {r["black"] for r in records})
    report_lines = ["# AI Chinese Chess Arena — 結果報告\n"]

    # --- Win rate matrix ---
    wins = defaultdict(lambda: defaultdict(int))
    losses = defaultdict(lambda: defaultdict(int))
    draws = defaultdict(lambda: defaultdict(int))

    for r in records:
        red, black, winner = r["red"], r["black"], r["winner"]
        if winner == "red":
            wins[red][black] += 1
            losses[black][red] += 1
        elif winner == "black":
            wins[black][red] += 1
            losses[red][black] += 1
        else:
            draws[red][black] += 1
            draws[black][red] += 1

    report_lines.append("## 勝率矩陣\n")
    header = "| 模型 | " + " | ".join(models) + " | 總計 |"
    sep = "|---" * (len(models) + 2) + "|"
    report_lines.append(header)
    report_lines.append(sep)

    for m in models:
        cells = []
        total_w, total_l, total_d = 0, 0, 0
        for opp in models:
            if m == opp:
                cells.append("-")
                continue
            w = wins[m][opp]
            l = losses[m][opp]
            d = draws[m][opp]
            total_w += w
            total_l += l
            total_d += d
            cell = f"{w}W/{l}L"
            if d:
                cell += f"/{d}D"
            cells.append(cell)
        total_games = total_w + total_l + total_d
        pct = f"{total_w/total_games*100:.0f}%" if total_games else "N/A"
        cells.append(f"{total_w}W/{total_l}L ({pct})")
        report_lines.append(f"| {m} | " + " | ".join(cells) + " |")

    # --- Legal move rate ---
    report_lines.append("\n## 合法走步率\n")
    report_lines.append("| 模型 | 合法率 | 非法次數 | 總走步數 | 因非法判負 |")
    report_lines.append("|---|---|---|---|---|")

    model_illegal = defaultdict(int)
    model_total_moves = defaultdict(int)
    model_illegal_losses = defaultdict(int)

    for r in records:
        for move in r["moves"]:
            model_name = r["red"] if move["color"] == "red" else r["black"]
            model_total_moves[model_name] += 1
            model_illegal[model_name] += len(move["illegal_attempts"])
        if r["reason"] == "illegal_move_limit":
            loser = r["black"] if r["winner"] == "red" else r["red"]
            model_illegal_losses[loser] += 1

    for m in models:
        total = model_total_moves[m]
        illegal = model_illegal[m]
        total_attempts = total + illegal
        rate = f"{total/total_attempts*100:.1f}%" if total_attempts else "N/A"
        report_lines.append(
            f"| {m} | {rate} | {illegal} | {total} | {model_illegal_losses[m]} |"
        )

    # --- Game summaries ---
    report_lines.append("\n## 對局記錄\n")
    report_lines.append("| # | 紅方 | 黑方 | 結果 | 原因 | 步數 | 非法(紅/黑) |")
    report_lines.append("|---|---|---|---|---|---|---|")

    for r in records:
        winner_str = r["winner"] or "和棋"
        ic = r["illegal_counts"]
        report_lines.append(
            f"| {r['game_id']} | {r['red']} | {r['black']} | "
            f"{winner_str} | {r['reason']} | {r['total_moves']} | "
            f"{ic['red']}/{ic['black']} |"
        )

    # --- Style analysis ---
    report_lines.append("\n## 棋風分析\n")
    report_lines.append("| 模型 | 平均 thinking 長度 | 平均步數 | 開局首步 |")
    report_lines.append("|---|---|---|---|")

    model_thinking_lens = defaultdict(list)
    model_game_lengths = defaultdict(list)
    model_first_moves = defaultdict(list)

    for r in records:
        for side in ["red", "black"]:
            model_name = r[side]
            side_moves = [m for m in r["moves"] if m["color"] == side]
            if not side_moves:
                continue
            model_game_lengths[model_name].append(len(side_moves))
            for m in side_moves:
                model_thinking_lens[model_name].append(len(m.get("thinking", "")))
            model_first_moves[model_name].append(side_moves[0]["move"])

    for m in models:
        avg_thinking = 0
        if model_thinking_lens[m]:
            avg_thinking = sum(model_thinking_lens[m]) / len(model_thinking_lens[m])
        avg_moves = 0
        if model_game_lengths[m]:
            avg_moves = sum(model_game_lengths[m]) / len(model_game_lengths[m])

        # Most common first move
        first_moves = model_first_moves[m]
        if first_moves:
            from collections import Counter
            top_move = Counter(first_moves).most_common(1)[0]
            first_str = f"{top_move[0]} ({top_move[1]}x)"
        else:
            first_str = "N/A"

        report_lines.append(
            f"| {m} | {avg_thinking:.0f} chars | {avg_moves:.1f} | {first_str} |"
        )

    report_text = "\n".join(report_lines) + "\n"

    report_path = os.path.join(OUTPUT_DIR, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nReport saved to {report_path}")
    print(f"Raw data saved to {os.path.join(OUTPUT_DIR, 'raw_results.json')}")
    return report_text

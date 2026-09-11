MODELS = [
    {"name": "gpt-via-codex", "provider": "codex", "model_id": "codex"},
    {"name": "gemini-via-cli", "provider": "gemini-cli", "model_id": "gemini-cli"},
    {"name": "claude-via-cc", "provider": "claude-code", "model_id": "claude-code"},
]

GAMES_PER_PAIR = 10
MAX_RETRIES = 3
OUTPUT_DIR = "results"

SYSTEM_PROMPT = "你是一個中國象棋高手。你會收到當前棋盤狀態和合法走步列表，請選擇最佳的下一步。"

MOVE_PROMPT_TEMPLATE = """\
你正在下中國象棋，你是{color}方（{color_desc}）。

當前棋盤：
{board}

{history_section}

合法走步：{valid_actions}

請用 JSON 回傳你的下一步，格式如下：
{{"thinking": "你的分析過程...", "move": "走步座標，如 b0c2"}}

注意：
- move 必須是上方合法走步列表中的其中一個
- 座標格式為 ICCS：起點列行+終點列行（如 b0c2 表示 b0 位置的棋子移動到 c2）
"""

RETRY_PROMPT_TEMPLATE = """\
你上一步的走法「{invalid_move}」不在合法走步列表中。

合法走步：{valid_actions}

請重新選擇，用 JSON 回傳：
{{"thinking": "你的分析過程...", "move": "走步座標"}}
"""

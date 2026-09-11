import json
import re
import subprocess

from config import SYSTEM_PROMPT, MOVE_PROMPT_TEMPLATE, RETRY_PROMPT_TEMPLATE


def _build_move_prompt(board_ascii: str, valid_actions: list[str],
                       move_history: list[dict], color: str) -> str:
    color_name = "紅" if color == "red" else "黑"
    color_desc = "下方，大寫棋子" if color == "red" else "上方，小寫棋子"

    history_section = ""
    if move_history:
        lines = []
        for i in range(0, len(move_history), 2):
            turn = i // 2 + 1
            red_move = move_history[i]
            parts = f"{turn}. 紅 {red_move['move']}"
            if i + 1 < len(move_history):
                black_move = move_history[i + 1]
                parts += f"  黑 {black_move['move']}"
            lines.append(parts)
        history_section = "走棋歷史：\n" + "\n".join(lines)
    else:
        history_section = "這是第一步。"

    return MOVE_PROMPT_TEMPLATE.format(
        color=color_name,
        color_desc=color_desc,
        board=board_ascii,
        history_section=history_section,
        valid_actions=", ".join(valid_actions),
    )


def _build_retry_prompt(invalid_move: str, valid_actions: list[str]) -> str:
    return RETRY_PROMPT_TEMPLATE.format(
        invalid_move=invalid_move,
        valid_actions=", ".join(valid_actions),
    )


def _parse_response(text: str) -> dict:
    """Extract {thinking, move} from AI response text."""
    # Try direct JSON parse
    try:
        data = json.loads(text)
        if "move" in data:
            return {"thinking": data.get("thinking", ""), "move": data["move"]}
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if "move" in data:
                return {"thinking": data.get("thinking", ""), "move": data["move"]}
        except json.JSONDecodeError:
            pass

    # Try finding any JSON object in text
    match = re.search(r'\{[^{}]*"move"\s*:\s*"[^"]*"[^{}]*\}', text)
    if match:
        try:
            data = json.loads(match.group(0))
            return {"thinking": data.get("thinking", ""), "move": data["move"]}
        except json.JSONDecodeError:
            pass

    return {"thinking": text, "move": None}


class AIPlayer:
    def __init__(self, config: dict):
        self.name = config["name"]
        self.provider = config["provider"]
        self.model_id = config["model_id"]
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI()
        elif self.provider == "google":
            import google.generativeai as genai
            self._client = genai
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic()
        elif self.provider == "claude-code":
            self._client = True
        return self._client

    def _call_api(self, messages: list[dict]) -> str:
        client = self._get_client()

        if self.provider == "openai":
            response = client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            return response.choices[0].message.content

        elif self.provider == "google":
            model = client.GenerativeModel(self.model_id)
            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [msg["content"]]})
            system_msgs = [m["content"] for m in messages if m["role"] == "system"]
            system_instruction = "\n".join(system_msgs) if system_msgs else None
            if system_instruction:
                model = client.GenerativeModel(
                    self.model_id,
                    system_instruction=system_instruction,
                )
            response = model.generate_content(
                contents,
                generation_config={"response_mime_type": "application/json", "temperature": 0.7},
            )
            return response.text

        elif self.provider == "anthropic":
            system = ""
            api_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    api_messages.append(msg)
            response = client.messages.create(
                model=self.model_id,
                max_tokens=1024,
                system=system,
                messages=api_messages,
                temperature=0.7,
            )
            return response.content[0].text

        elif self.provider == "claude-code":
            system = ""
            user_text = ""
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    user_text = msg["content"]
            full_prompt = f"{system}\n\n{user_text}" if system else user_text
            result = subprocess.run(
                ["claude", "-p", "--output-format", "text", full_prompt],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"claude -p failed: {result.stderr}")
            return result.stdout

    def get_move(self, board_ascii: str, valid_actions: list[str],
                 move_history: list[dict], color: str) -> dict:
        prompt = _build_move_prompt(board_ascii, valid_actions, move_history, color)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        try:
            raw = self._call_api(messages)
            return _parse_response(raw)
        except Exception as e:
            return {"thinking": f"API error: {e}", "move": None}

    def get_retry(self, invalid_move: str, valid_actions: list[str]) -> dict:
        prompt = _build_retry_prompt(invalid_move, valid_actions)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        try:
            raw = self._call_api(messages)
            return _parse_response(raw)
        except Exception as e:
            return {"thinking": f"API error: {e}", "move": None}

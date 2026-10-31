"""Strip a Claude Code session .jsonl down to user inputs and assistant replies.

Drops tool calls, tool results, thinking, system reminders, slash-command noise
and metadata. Consecutive assistant text blocks are merged into one reply.

Usage:
    python scripts/extract_session.py <session.jsonl> [output.jsonl]
"""

import json
import re
import sys
from pathlib import Path

NOISE = re.compile(
    r"<system-reminder>.*?</system-reminder>|<ide_\w+>.*?</ide_\w+>", re.S
)
SKIP_PREFIXES = (
    "<command",
    "<local-command",
    "<task-notification",
    "[Request interrupted",
    "This session is being continued",
)


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def extract(src: Path) -> list[dict]:
    turns: list[dict] = []
    for line in src.open(encoding="utf-8", errors="ignore"):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = entry.get("type")
        if role not in ("user", "assistant") or entry.get("isMeta") or entry.get("isSidechain"):
            continue

        text = NOISE.sub("", text_of(entry.get("message", {}).get("content"))).strip()
        if not text or text.startswith(SKIP_PREFIXES):
            continue

        if turns and turns[-1]["role"] == role == "assistant":
            turns[-1]["text"] += "\n\n" + text
        else:
            turns.append({"role": role, "timestamp": entry.get("timestamp"), "text": text})
    return turns


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("session.jsonl")

    turns = extract(src)
    with dst.open("w", encoding="utf-8") as f:
        for turn in turns:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")
    print(f"{len(turns)} turns -> {dst}")


if __name__ == "__main__":
    main()

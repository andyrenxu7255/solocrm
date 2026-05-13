from __future__ import annotations

from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")

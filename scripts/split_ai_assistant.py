from pathlib import Path

SRC = Path(r"d:\Git\百姓助手\tmp_ai_assistant_utf8.py")
TARGET_DIR = Path(r"d:\Git\百姓助手\backend\app\services\ai")

text = SRC.read_text(encoding="utf-8")
lines = text.splitlines()

start = end = None
for i, line in enumerate(lines):
    if line.startswith("class LegalKnowledgeBase"):
        start = i
    if line.startswith("class AILegalAssistant") and start is not None and end is None:
        end = i
        break

if start is None or end is None:
    raise SystemExit("class markers not found")

legal_lines = lines[start:end]
assistant_lines = lines[:start] + lines[end:]

kb_imports = [
    '"""法律知识库管理"""',
    'from __future__ import annotations',
    '',
    'import logging',
    'from typing import cast',
    '',
    'from langchain_chroma import Chroma',
    'from langchain_openai import OpenAIEmbeddings',
    'from langchain_text_splitters import RecursiveCharacterTextSplitter',
    'from pydantic import SecretStr',
    '',
    'from ..config import get_settings',
    '',
]

kb_content = "\n".join(kb_imports + legal_lines) + "\n"
TARGET_DIR.joinpath("knowledge_base.py").write_text(kb_content, encoding="utf-8")

inserted = False
for i, line in enumerate(assistant_lines):
    if line.startswith("from ..config import get_settings"):
        assistant_lines.insert(i + 1, "from .knowledge_base import LegalKnowledgeBase")
        inserted = True
        break

if not inserted:
    assistant_lines.insert(0, "from .knowledge_base import LegalKnowledgeBase")

assistant_text = "\n".join(assistant_lines) + "\n"
TARGET_DIR.joinpath("assistant.py").write_text(assistant_text, encoding="utf-8")

print("split done")

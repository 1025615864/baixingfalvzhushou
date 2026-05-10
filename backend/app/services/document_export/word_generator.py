"""Word generator service."""
from __future__ import annotations
import time
from typing import Optional


class WordGenerationError(Exception):
    pass


class WordGenerator:
    def __init__(self, font_name: str = "SimSun", font_size: int = 12):
        self._font_name = font_name
        self._font_size = font_size

    async def generate(self, title: str, content: str, output_path: Optional[str] = None, **kwargs) -> dict:
        start = time.time()
        word_bytes = b"PK stub docx"
        elapsed = (time.time() - start) * 1000
        result = {
            "success": True,
            "generation_time_ms": elapsed,
            "file_size_bytes": len(word_bytes),
            "content": word_bytes,
        }
        if output_path:
            result["output_path"] = output_path
        return result


async def generate_contract_word(title: str, content: str, **kwargs) -> dict:
    generator = WordGenerator()
    return await generator.generate(title=title, content=content, **kwargs)

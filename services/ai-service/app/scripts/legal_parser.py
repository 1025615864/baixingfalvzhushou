"""
法律文档语义切块脚本

基于"法条层级"的精准解析，配合富元数据注入
支持 Word (.docx) 和 PDF 格式
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader


@dataclass
class LegalChunk:
    """法律文档切块"""
    chunk_id: str
    text: str
    law_name: str
    part: str
    chapter: str
    article_num: str
    article_title: Optional[str]
    clause_level: str
    parent_context: str
    effective_date: str
    category: str


class LegalDocumentParser:
    """
    法律文档解析器

    支持语义层级的精准切分：
    - 编 (Part)
    - 章 (Chapter)
    - 节 (Section)
    - 条 (Article)
    - 款 (Clause)
    - 项 (Item)
    """

    ARTICLE_PATTERN = re.compile(r"第([一二三四五六七八九十百千零\d]+)[条款项]")
    PART_PATTERN = re.compile(r"第([一二三四五六七八九十百千零\d]+)[编部]")
    CHAPTER_PATTERN = re.compile(r"第([一二三四五六七八九十百千零\d]+)章")
    SECTION_PATTERN = re.compile(r"第([一二三四五六七八九十百千零\d]+)节")

    CHINESE_NUMBERS = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        "百": 100, "千": 1000, "零": 0
    }

    def __init__(self, law_name: str = "", effective_date: str = ""):
        self.law_name = law_name
        self.effective_date = effective_date
        self.current_part = ""
        self.current_chapter = ""
        self.current_section = ""
        self.chunks: List[LegalChunk] = []

    def parse_chinese_number(self, text: str) -> int:
        """将中文数字转换为整数"""
        if text.isdigit():
            return int(text)

        total = 0
        for char in text:
            if char in self.CHINESE_NUMBERS:
                total = total * 10 + self.CHINESE_NUMBERS[char]
        return total

    def extract_hierarchy(self, text: str) -> Dict[str, str]:
        """从文本中提取层级结构"""
        hierarchy = {
            "part": self.current_part,
            "chapter": self.current_chapter,
            "section": self.current_section
        }

        part_match = self.PART_PATTERN.search(text)
        if part_match:
            self.current_part = f"第{part_match.group(1)}编"
            hierarchy["part"] = self.current_part

        chapter_match = self.CHAPTER_PATTERN.search(text)
        if chapter_match:
            self.current_chapter = f"第{chapter_match.group(1)}章"
            hierarchy["chapter"] = self.current_chapter

        section_match = self.SECTION_PATTERN.search(text)
        if section_match:
            self.current_section = f"第{section_match.group(1)}节"
            hierarchy["section"] = self.current_section

        return hierarchy

    def split_into_chunks(self, text: str, max_tokens: int = 1000) -> List[str]:
        """
        按法条层级切分文本

        Args:
            text: 原始法律文本
            max_tokens: 最大 token 数（估算）

        Returns:
            切分后的文本块列表
        """
        chunks = []
        lines = text.split("\n")
        current_chunk = []
        current_length = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_length = len(line)

            if current_length + line_length > max_tokens * 4:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                current_length = 0

            current_chunk.append(line)
            current_length += line_length

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def parse_document(self, file_path: str) -> List[LegalChunk]:
        """
        解析法律文档

        Args:
            file_path: 文档路径

        Returns:
            LegalChunk 列表
        """
        suffix = Path(file_path).suffix.lower()

        if suffix == ".pdf":
            loader = PyPDFLoader(file_path)
        elif suffix == ".docx":
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        pages = loader.load()
        full_text = "\n".join([page.page_content for page in pages])

        chunks_text = self.split_into_chunks(full_text)

        for idx, chunk_text in enumerate(chunks_text):
            hierarchy = self.extract_hierarchy(chunk_text)

            article_match = self.ARTICLE_PATTERN.search(chunk_text)
            article_num = article_match.group(0) if article_match else f"附录{idx + 1}"

            chunk_id = f"{self.law_name}_{article_num}_{idx}".replace(" ", "_")

            parent_context = " > ".join([
                hierarchy["part"],
                hierarchy["chapter"],
                hierarchy["section"]
            ])
            parent_context = parent_context.strip(" > ")

            self.chunks.append(LegalChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                law_name=self.law_name,
                part=hierarchy["part"],
                chapter=hierarchy["chapter"],
                article_num=article_num,
                article_title=None,
                clause_level="条",
                parent_context=parent_context,
                effective_date=self.effective_date,
                category=""
            ))

        return self.chunks

    def to_langchain_documents(self) -> List[Document]:
        """转换为 LangChain Document 对象"""
        documents = []

        for chunk in self.chunks:
            metadata = {
                "chunk_id": chunk.chunk_id,
                "law_name": chunk.law_name,
                "part": chunk.part,
                "chapter": chunk.chapter,
                "section": chunk.article_title,
                "article_num": chunk.article_num,
                "effective_date": chunk.effective_date,
                "category": chunk.category,
                "parent_context": chunk.parent_context
            }

            documents.append(Document(
                page_content=chunk.text,
                metadata=metadata
            ))

        return documents


class FAQGenerator:
    """
    为法条生成大白话摘要（可选增强）

    调用 LLM 为每条法条生成可能的日常提问
    """

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    def generate_faq(self, article_text: str, article_num: str) -> List[str]:
        """
        为法条生成 FAQ

        Args:
            article_text: 法条原文
            article_num: 条文编号

        Returns:
            可能的日常提问列表
        """
        if not self.llm_service:
            return []

        prompt = f"""请为以下法律条文生成3个普通人在日常生活中可能会问的问题。

法律条文（第{article_num}条）：
{article_text}

要求：
1. 问题要通俗易懂，使用大白话
2. 涵盖不同的实际场景
3. 每个问题不超过30字

问题："""

        response = self.llm_service.chat([{"role": "user", "content": prompt}])

        questions = [
            q.strip() for q in response["content"].split("\n")
            if q.strip() and ("？" in q or "?" in q)
        ]

        return questions[:3]


def process_legal_documents(
    input_dir: str,
    output_file: str,
    law_name: str,
    effective_date: str
) -> Tuple[int, List[str]]:
    """
    批量处理法律文档

    Args:
        input_dir: 输入目录
        output_file: 输出 JSON 文件路径
        law_name: 法律名称
        effective_date: 生效日期

    Returns:
        (处理的文档数, 生成的 chunk_id 列表)
    """
    parser = LegalDocumentParser(
        law_name=law_name,
        effective_date=effective_date
    )

    input_path = Path(input_dir)
    chunk_ids = []

    for file_path in input_path.glob("*.pdf"):
        chunks = parser.parse_document(str(file_path))
        chunk_ids.extend([c.chunk_id for c in chunks])

    for file_path in input_path.glob("*.docx"):
        chunks = parser.parse_document(str(file_path))
        chunk_ids.extend([c.chunk_id for c in chunks])

    documents = parser.to_langchain_documents()

    output_data = [
        {
            "chunk_id": doc.metadata["chunk_id"],
            "text": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in documents
    ]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return len(list(input_path.glob("*"))), chunk_ids


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python -m app.scripts.legal_parser <input_dir> <output_file> <law_name>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_file = sys.argv[2]
    law_name = sys.argv[3]
    effective_date = sys.argv[4] if len(sys.argv) > 4 else ""

    count, chunk_ids = process_legal_documents(
        input_dir=input_dir,
        output_file=output_file,
        law_name=law_name,
        effective_date=effective_date
    )

    print(f"Processed {count} documents")
    print(f"Generated {len(chunk_ids)} chunks")
    print(f"Output saved to {output_file}")

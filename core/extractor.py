import re
import json
import os
import pypdf

class UniversalPDFExtractor:
    """Universal PDF page extractor with sentence-level segmentation."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found at: {pdf_path}")
        self.reader = pypdf.PdfReader(pdf_path)
        self.total_pages = len(self.reader.pages)

    @staticmethod
    def split_sentences(text: str) -> list[str]:
        """Segments text into sentences while respecting abbreviations, quotes, and bullets."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned = " ".join(lines)
        raw = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'•\-])', cleaned)
        sentences = []
        for item in raw:
            item_clean = item.strip()
            if not item_clean:
                continue
            sub_items = re.split(r'(?<=\w)\s*(?=[•\-\*]\s+)', item_clean)
            for sub in sub_items:
                sub_clean = sub.strip()
                if sub_clean:
                    sentences.append(sub_clean)
        return sentences

    def extract_page(self, page_num: int) -> dict:
        """Extracts text and sentence segmentation for a 1-based page number."""
        idx = page_num - 1
        if idx < 0 or idx >= self.total_pages:
            raise IndexError(f"Page number {page_num} out of bounds (1-{self.total_pages})")

        page = self.reader.pages[idx]
        raw_text = page.extract_text() or ""
        sentences = self.split_sentences(raw_text)
        words = raw_text.split()

        return {
            "page_num": page_num,
            "char_count": len(raw_text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "sentences": sentences,
            "raw_text": raw_text
        }

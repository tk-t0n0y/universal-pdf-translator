import re
from datetime import datetime

class MultiLingualVerifier:
    """Verifies sentence fidelity between source extract and translated text."""

    DELIMITER_PATTERNS = {
        "bengali": r'[।!?\n]+',
        "hindi": r'[।!?\n]+',
        "cjk": r'[。！？\n]+',
        "general": r'[.!?\n]+'
    }

    def __init__(self, target_lang: str = "bengali", min_coverage: float = 0.8):
        self.target_lang = target_lang.lower()
        self.min_coverage = min_coverage
        self.pattern = self.DELIMITER_PATTERNS.get(self.target_lang, self.DELIMITER_PATTERNS["general"])

    def segment_translation(self, text: str) -> list[str]:
        """Segments translated markdown body into individual sentences."""
        lines = [line for line in text.splitlines() if not line.startswith('#') and not line.startswith('[') and not line.startswith('---')]
        body = "\n".join(lines).strip()
        tokens = re.split(self.pattern, body)
        return [tok.strip() for tok in tokens if tok.strip()]

    def verify(self, page_num: int, source_data: dict, translated_content: str) -> dict:
        """Calculates fidelity metrics and returns verification result."""
        translated_sentences = self.segment_translation(translated_content)
        translated_words = translated_content.split()

        src_s_count = source_data.get("sentence_count", 0)
        tr_s_count = len(translated_sentences)

        coverage_ratio = (tr_s_count / src_s_count) if src_s_count > 0 else 1.0
        threshold = max(1, int(src_s_count * self.min_coverage))
        is_verified = tr_s_count >= threshold

        return {
            "page_num": page_num,
            "source_sentences": src_s_count,
            "source_words": source_data.get("word_count", 0),
            "translated_sentences": tr_s_count,
            "translated_words": len(translated_words),
            "coverage_ratio": round(coverage_ratio, 2),
            "status": "VERIFIED" if is_verified else "FLAGGED_INCOMPLETE",
            "verified_at": datetime.now().isoformat()
        }

import re
from typing import Dict, Any, Tuple

BN_DIGITS = {'০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'}
EN_TO_BN = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}

def to_bengali_digits(num: Any) -> str:
    """Converts English integers/strings to Bengali numeral digits."""
    return "".join(EN_TO_BN.get(c, c) for c in str(num))

def to_english_digits(text: str) -> str:
    """Converts Bengali numeral digits to English ASCII digits."""
    return "".join(BN_DIGITS.get(c, c) for c in str(text))

class PageContentCleaner:
    """
    Cleans translated markdown page files by extracting structured metadata
    and stripping verification statistics/debug headers to yield pure publication prose.
    """

    @classmethod
    def parse_page(cls, raw_text: str, fallback_page_num: int = 0) -> Dict[str, Any]:
        """
        Parses a page's raw markdown text and returns:
        - page_num: int
        - chapter_title: str
        - body_markdown: str
        - is_part_intro: bool
        - is_chapter_opener: bool
        """
        lines = raw_text.splitlines()
        page_num = fallback_page_num
        chapter_title = ""
        body_start_idx = 0
        has_hr = False

        # 1. Check if file starts with YAML frontmatter (---)
        first_non_empty = -1
        for i, l in enumerate(lines[:5]):
            if l.strip():
                first_non_empty = i
                break

        if first_non_empty != -1 and lines[first_non_empty].strip() in ["---", "***"]:
            for i in range(first_non_empty + 1, min(len(lines), 25)):
                s = lines[i].strip()
                if s in ["---", "***"]:
                    has_hr = True
                    body_start_idx = i + 1
                    break
                if s.startswith("page:"):
                    m_pg = re.search(r'\d+', s)
                    if m_pg:
                        page_num = int(m_pg.group())
                elif s.startswith("title:"):
                    cand = s.replace("title:", "").strip().strip('"').strip("'")
                    if cand:
                        chapter_title = cand
                elif s.startswith("chapter:") and not chapter_title:
                    m_ch = re.search(r'\d+', s)
                    if m_ch:
                        chapter_title = f"অধ্যায় {m_ch.group()}"
        else:
            # 2. Format B or C (Blockquotes or markdown headers)
            for i, line in enumerate(lines[:15]):
                s = line.strip()
                if s in ["---", "***", "___"]:
                    has_hr = True
                    body_start_idx = i + 1
                    break

                if "পৃষ্ঠা" in s or "Page" in s:
                    m_pg = re.search(r'Page\s+(\d+)', s, re.IGNORECASE)
                    if m_pg:
                        page_num = int(m_pg.group(1))
                    else:
                        m_bn_pg = re.search(r'পৃষ্ঠা\s+([০-৯]+)', s)
                        if m_bn_pg and page_num == fallback_page_num:
                            page_num = int(to_english_digits(m_bn_pg.group(1)))

                    if "—" in s or "–" in s:
                        parts = re.split(r'[—–]', s, maxsplit=1)
                        if len(parts) > 1:
                            candidate = parts[1].strip().rstrip('*').rstrip()
                            if candidate and "পরিসংখ্যান" not in candidate and "Status" not in candidate:
                                chapter_title = candidate

            if not has_hr:
                for i, line in enumerate(lines[:12]):
                    s = line.strip()
                    if "পরিসংখ্যান" in s or "Status" in s or "যাচাইকৃত" in s or "status:" in s:
                        body_start_idx = i + 1
                        break

        # Slice body
        body_lines = lines[body_start_idx:]

        # Trim leading blank lines and redundant top metadata
        cleaned_body_lines = []
        skipping_intro = True
        for line in body_lines:
            s = line.strip()
            if skipping_intro:
                if not s:
                    continue
                if (s.startswith("# দ্য ব্ল্যাক বুক") or s.startswith("# The Black Book")) and page_num > 1:
                    continue
                if s.startswith("# পৃষ্ঠা") or s.startswith("## পৃষ্ঠা") or s.startswith("> **পৃষ্ঠা"):
                    continue
                if s in ["---", "***"]:
                    continue
                if any(s.startswith(k) for k in ["পরিসংখ্যান:", "> *পরিসংখ্যান*", "status:", "coverage_ratio:", "source_sentences:", "translated_sentences:", "total_pages:"]):
                    continue
                skipping_intro = False
            cleaned_body_lines.append(line)

        body_markdown = "\n".join(cleaned_body_lines).strip()

        # Check if this page is a Part or Chapter opener
        is_part_intro = bool(re.search(r'^#{1,2}\s+(প্রথম|দ্বিতীয়|তৃতীয়|চতুর্থ|পঞ্চম|ষষ্ঠ|সপ্তম|অষ্টম|খণ্ড|পর্ব|Part\s+[IVXLCDM]+)', body_markdown, re.MULTILINE | re.IGNORECASE))
        is_chapter_opener = bool(re.search(r'^#{1,3}\s+(অধ্যায়|অধ্যায়|Chapter\s+\d+|ভূমিকা|Preface|Introduction)', body_markdown, re.MULTILINE | re.IGNORECASE))

        # If chapter_title wasn't found in header, look for first header in body
        if not chapter_title:
            h_match = re.search(r'^#{1,3}\s+(.+)', body_markdown, re.MULTILINE)
            if h_match:
                chapter_title = h_match.group(1).strip()
            else:
                chapter_title = "দ্য ব্ল্যাক বুক অব পাওয়ার"

        return {
            "page_num": page_num,
            "chapter_title": chapter_title,
            "body_markdown": body_markdown,
            "is_part_intro": is_part_intro,
            "is_chapter_opener": is_chapter_opener,
        }

    @classmethod
    def enhance_markdown_for_typography(cls, md_text: str) -> str:
        """
        Enhances markdown with semantic HTML wrappers for luxury typography:
        - Callout boxes for legal warnings, case studies, protocols
        - Ornamental section dividers
        """
        lines = md_text.splitlines()
        enhanced_lines = []

        in_warning = False
        in_casestudy = False

        for line in lines:
            stripped = line.strip()

            # If encountering ANY heading, close any currently open callout
            if stripped.startswith("#"):
                if in_warning:
                    enhanced_lines.append("</div>\n")
                    in_warning = False
                if in_casestudy:
                    enhanced_lines.append("</div>\n")
                    in_casestudy = False

            # Detect Warning sections
            if any(term in stripped for term in ["আইনি সতর্কবার্তাসমূহ", "আইনি সতর্কতা", "Legal Warnings", "ঝুঁকি গ্রহণ"]):
                enhanced_lines.append(f'<div class="callout callout-warning">\n\n{line}')
                in_warning = True
                continue

            # Detect Case Studies
            if any(term in stripped for term in ["কেস স্টাডি", "বাস্তব কেস", "Case Study"]):
                enhanced_lines.append(f'<div class="callout callout-case">\n\n{line}')
                in_casestudy = True
                continue

            # Convert standalone '---' in body to elegant ornament
            if stripped == "---":
                if in_warning:
                    enhanced_lines.append("</div>\n")
                    in_warning = False
                if in_casestudy:
                    enhanced_lines.append("</div>\n")
                    in_casestudy = False
                enhanced_lines.append('\n<div class="divider-ornament">❖ ❖ ❖</div>\n')
                continue

            enhanced_lines.append(line)

        if in_warning:
            enhanced_lines.append("</div>")
        if in_casestudy:
            enhanced_lines.append("</div>")

        return "\n".join(enhanced_lines)

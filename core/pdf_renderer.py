import os
import sys
import glob
import re
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF

from core.content_cleaner import PageContentCleaner
from core.book_builder import BookBuilder

class PDFRenderer:
    """
    Renders publication-grade PDFs from markdown page files using
    embedded typography, HTML5/CSS Paged Media, and headless Chromium/Edge.
    """

    BOOK_OUTLINE = [
        [1, "প্রচ্ছদ ও শিরোনাম (Title & Cover)", 1],
        [1, "উৎসর্গ ও আইনি দায়মুক্তি (Dedication & Disclaimer)", 2],
        [1, "ভূমিকা: বেদনার সওদাগর (Preface: The Pain Merchant)", 6],
        [1, "প্রথম পর্ব – জাগরণ (Part I: The Awakening)", 15],
        [2, "অধ্যায় ১ – চলমান লাশ (Chapter 1: The Walking Dead)", 23],
        [2, "অধ্যায় ২ – বাস্তবতার কারিগরগণ (Chapter 2: Masters of Reality)", 57],
        [2, "অধ্যায় ৩ – দাসত্বের অলিখিত চুক্তি (Chapter 3: The Contract)", 83],
        [1, "দ্বিতীয় খণ্ড — ক্রিসালিস (Part II: The Chrysalis)", 123],
        [2, "অধ্যায় ৪ — মার্বেল পাথরের ভাস্কর্য (Chapter 4: The Marble Statue)", 132],
        [2, "অধ্যায় ৫ — দ্য প্যারাসাইট (Chapter 5: The Parasite)", 186],
        [2, "অধ্যায় ৬ — নগ্ন রাজা (Chapter 6: The Naked King)", 207],
        [1, "তৃতীয় খণ্ড — দ্য শ্যাডো অ্যাকাডেমি (Part III: The Shadow Academy)", 242],
        [2, "অধ্যায় ৭ — হৃদয়ের সুতো (Chapter 7: Heartstrings)", 242],
        [2, "অধ্যায় ৮ — আত্মার বন্ধন (Chapter 8: The Bonding of Souls)", 306],
        [2, "অধ্যায় ৯ — দ্য কগনিটিভ ক্যাসকেডস (Chapter 9: The Cognitive Cascades)", 337],
        [2, "অধ্যায় ১০ — শত্রুর উপহার (Chapter 10: The Enemy’s Gift)", 386],
        [2, "অধ্যায় ১১ — সর্পজিহ্বা (Chapter 11: The Serpent’s Tongue)", 434],
        [2, "অধ্যায় ১২ — স্বপ্নবয়নকারী (Chapter 12: The Dream Weaver)", 495],
        [2, "অধ্যায় ১৩ — দ্য হ্যালো ইফেক্ট (Chapter 13: The Halo Effect)", 542],
        [1, "চতুর্থ খণ্ড – দ্য গ্রেট গেম (Part IV: The Great Game)", 568],
        [2, "অধ্যায় ১৪ – ক্ষমতার অদৃশ্য জাল (Chapter 14: The Power Webs)", 573],
        [2, "অধ্যায় ১৫ – স্বর্ণখনি (Chapter 15: The Gold Mine)", 593],
        [2, "অধ্যায় ১৬ – ঈশ্বর ও দানবগণ (Chapter 16: The Gods & Monsters)", 637],
        [2, "অধ্যায় ১৭ — অন্ধদের রাখাল (Chapter 17: The Shepherd of the Blind)", 683],
        [2, "অধ্যায় ১৮ — প্রেমের বিষ (Chapter 18: The Love Poison)", 709],
        [1, "পঞ্চম খণ্ড – সৎ কারসাজিকারী (Part V: The Good Manipulator)", 746],
        [2, "অধ্যায় ১৯ — চিকিৎসকের প্রচলিত-বিরুদ্ধ নীতি (Chapter 19: The Healer's Heresy)", 752],
        [2, "অধ্যায় ২০ — নিঃসঙ্গ একনায়ক (Chapter 20: The Lonely Dictator)", 774],
        [2, "অধ্যায় ২১ — ছায়ার মুকুট (Chapter 21: The Crown of Shadows)", 802],
        [1, "ষষ্ঠ পর্ব – কারসাজির ভল্ট ও পরিশিষ্ট (Part VI: The Vault & Appendices)", 818],
        [2, "ষষ্ঠ পর্ব: কারসাজির ভল্ট (The Manipulation Vault)", 818],
        [2, "পরিশিষ্ট: শব্দকোষ (The Glossary)", 920]
    ]

    DEFAULT_EDGE_PATHS = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]

    # Pre-calculated Part boundaries based on original book structure
    PARTS_MAP = {
        1: {
            "title": "প্রথম পর্ব – জাগরণ (Part I – The Awakening)",
            "start": 1,
            "end": 122,
            "vol_bn": "জাগরণ",
            "vol_en": "The Awakening",
            "subtitle": "বাস্তবতার মুখোমুখি হওয়া, বিভ্রমের পর্দা উন্মোচন ও মনস্তাত্ত্বিক গোলামির শেকল ভাঙা (পৃষ্ঠা ১ – ১২২)"
        },
        2: {
            "title": "দ্বিতীয় খণ্ড — ক্রিসালিস (Part II – The Chrysalis)",
            "start": 123,
            "end": 241,
            "vol_bn": "ক্রিসালিস",
            "vol_en": "The Chrysalis",
            "subtitle": "মনস্তাত্ত্বিক রূপান্তর, অভ্যন্তরীণ প্রতিরক্ষা ও নতুন চরিত্র গঠন (পৃষ্ঠা ১২৩ – ২৪১)"
        },
        3: {
            "title": "তৃতীয় খণ্ড — দ্য শ্যাডো অ্যাকাডেমি (Part III – The Shadow Academy)",
            "start": 242,
            "end": 567,
            "vol_bn": "দ্য শ্যাডো অ্যাকাডেমি",
            "vol_en": "The Shadow Academy",
            "subtitle": "অন্ধকারের কলাকৌশল, প্রভাব বিস্তার ও নীরব আধিপত্য (পৃষ্ঠা ২৪২ – ৫৬৭)"
        },
        4: {
            "title": "চতুর্থ খণ্ড – দ্য গ্রেট গেম (Part IV – The Great Game)",
            "start": 568,
            "end": 745,
            "vol_bn": "দ্য গ্রেট গেম",
            "vol_en": "The Great Game",
            "subtitle": "ক্ষমতার মহাসমর, প্রতিদ্বন্দ্বী দমন ও দীর্ঘমেয়াদী নিয়ন্ত্রণ (পৃষ্ঠা ৫৬৮ – ৭৪৫)"
        },
        5: {
            "title": "পঞ্চম খণ্ড – সৎ কারসাজিকারী (Part V – The Good Manipulator)",
            "start": 746,
            "end": 817,
            "vol_bn": "সৎ কারসাজিকারী",
            "vol_en": "The Good Manipulator",
            "subtitle": "নৈতিক প্রভাব, সুরক্ষা ও ভারসাম্যপূর্ণ মনস্তত্ত্ব (পৃষ্ঠা ৭৪৬ – ৮১৭)"
        },
        6: {
            "title": "ষষ্ঠ পর্ব – কারসাজির ভল্ট ও পরিশিষ্ট (Part VI – Vault & Appendices)",
            "start": 818,
            "end": 933,
            "vol_bn": "কারসাজির ভল্ট ও পরিশিষ্ট",
            "vol_en": "The Manipulation Vault & Appendices",
            "subtitle": "কৌশলকোষ, বিশ্লেষণাত্মক ভল্ট ও পূর্ণাঙ্গ রেফারেন্স নির্দেশিকা (পৃষ্ঠা ৮১৮ – ৯৩৩)"
        },
    }

    def __init__(self, pages_dir: str = "translations/pages", edge_binary: Optional[str] = None):
        self.pages_dir = pages_dir
        self.edge_binary = edge_binary or self._locate_browser()
        if not self.edge_binary or not os.path.exists(self.edge_binary):
            raise FileNotFoundError(f"Headless browser binary not found. Checked: {self.DEFAULT_EDGE_PATHS}")

    def _locate_browser(self) -> Optional[str]:
        for path in self.DEFAULT_EDGE_PATHS:
            if os.path.exists(path):
                return path
        return None

    def get_available_pages(self) -> List[int]:
        files = glob.glob(os.path.join(self.pages_dir, "page_*.md"))
        pages = []
        for f in files:
            m = re.search(r'page_(\d+)\.md', f)
            if m:
                pages.append(int(m.group(1)))
        return sorted(pages)

    def load_cleaned_pages(self, start_page: int, end_page: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Loads and parses markdown files within the given page range.
        Returns (cleaned_pages, toc_items).
        """
        cleaned_pages = []
        toc_items = []
        current_part = ""

        for p in range(start_page, end_page + 1):
            fpath = os.path.join(self.pages_dir, f"page_{p:03d}.md")
            if not os.path.exists(fpath):
                continue
            with open(fpath, "r", encoding="utf-8") as f:
                raw_text = f.read()

            parsed = PageContentCleaner.parse_page(raw_text, fallback_page_num=p)
            cleaned_pages.append(parsed)

            # Check if this page should be in TOC
            body = parsed["body_markdown"]
            for line in body.splitlines():
                line_s = line.strip()
                part_m = re.search(r'^#{1,2}\s+((প্রথম|দ্বিতীয়|তৃতীয়|চতুর্থ|পঞ্চম|ষষ্ঠ|খণ্ড|পর্ব|Part\s+[IVXLCDM]+).*?)$', line_s, re.I)
                if part_m:
                    current_part = part_m.group(1).strip()
                    toc_items.append({"type": "part", "page": p, "title": current_part})
                    break

                ch_m = re.search(r'^#{1,3}\s+((অধ্যায়|অধ্যায়|ভূমিকা|Chapter\s+\d+|Preface|উপসংহার|পরিশিষ্ট).*?)$', line_s, re.I)
                if ch_m:
                    ch_title = re.sub(r'^[#\s]+', '', ch_m.group(1)).strip()
                    toc_items.append({"type": "chapter", "page": p, "title": ch_title, "part": current_part})
                    break

        return cleaned_pages, toc_items

    def render_html_to_pdf(self, html_content: str, output_pdf_path: str) -> str:
        """Invokes headless browser to compile HTML string into a PDF document."""
        abs_output_pdf = os.path.abspath(output_pdf_path)
        os.makedirs(os.path.dirname(abs_output_pdf), exist_ok=True)
        
        # Write temporary HTML file
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False) as tf:
            tf.write(html_content)
            temp_html_path = tf.name

        try:
            file_url = "file:///" + os.path.abspath(temp_html_path).replace("\\", "/")
            cmd = [
                self.edge_binary,
                "--headless",
                "--disable-gpu",
                "--run-all-compositor-stages-before-draw",
                "--no-pdf-header-footer",
                f"--print-to-pdf={abs_output_pdf}",
                file_url
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"Edge PDF rendering failed with code {res.returncode}: {res.stderr}")

            if not os.path.exists(abs_output_pdf) or os.path.getsize(abs_output_pdf) == 0:
                raise RuntimeError("Edge finished but output PDF was not generated or is empty.")

            return abs_output_pdf
        finally:
            if os.path.exists(temp_html_path):
                try:
                    os.remove(temp_html_path)
                except Exception:
                    pass

    def render_range(
        self,
        start_page: int,
        end_page: int,
        output_pdf_path: str,
        mode: str = "1to1",
        include_cover: bool = True,
        include_toc: bool = True,
        volume_number: Optional[int] = None,
        volume_title_bn: Optional[str] = None,
        volume_title_en: Optional[str] = None,
        volume_subtitle: Optional[str] = None,
        page_range_str: Optional[str] = None,
        is_master: bool = False
    ) -> Dict[str, Any]:
        """Renders a range of pages into a publication PDF."""
        cleaned_pages, toc_items = self.load_cleaned_pages(start_page, end_page)
        if not cleaned_pages:
            raise ValueError(f"No pages found in range {start_page} to {end_page}")

        # Filter TOC items to only those within start_page and end_page
        filtered_toc = [item for item in toc_items if start_page <= item["page"] <= end_page]

        builder = BookBuilder(
            mode=mode,
            include_cover=include_cover,
            include_toc=include_toc and len(cleaned_pages) > 10,
            volume_number=volume_number,
            volume_title_bn=volume_title_bn,
            volume_title_en=volume_title_en,
            volume_subtitle=volume_subtitle,
            page_range_str=page_range_str,
            is_master=is_master
        )
        html_doc = builder.assemble_document(cleaned_pages, filtered_toc)
        pdf_path = self.render_html_to_pdf(html_doc, output_pdf_path)

        # Inspect resulting PDF
        doc = fitz.open(pdf_path)
        stats = {
            "output_path": pdf_path,
            "page_count": len(doc),
            "file_size_bytes": os.path.getsize(pdf_path),
            "source_pages": len(cleaned_pages),
            "mode": mode,
            "sample_text": doc[0].get_text()[:200] if len(doc) > 0 else ""
        }
        doc.close()
        return stats

    def render_volume(self, volume_num: int, output_pdf_path: str, mode: str = "1to1") -> Dict[str, Any]:
        """Renders one of the 6 defined book volumes with bespoke cover and styling."""
        if volume_num not in self.PARTS_MAP:
            raise ValueError(f"Invalid volume number: {volume_num}. Valid volumes are 1 through 6.")
        part_info = self.PARTS_MAP[volume_num]
        return self.render_range(
            start_page=part_info["start"],
            end_page=part_info["end"],
            output_pdf_path=output_pdf_path,
            mode=mode,
            include_cover=True,
            include_toc=True,
            volume_number=volume_num,
            volume_title_bn=part_info["vol_bn"],
            volume_title_en=part_info["vol_en"],
            volume_subtitle=part_info["subtitle"],
            page_range_str=f"পৃষ্ঠা {part_info['start']} – {part_info['end']}",
            is_master=False
        )

    def render_full_book(
        self,
        output_pdf_path: str,
        mode: str = "1to1",
        batch_size: int = 100,
        temp_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renders the complete 933-page book in batches and merges them into a single PDF,
        ensuring 1:1 page-to-page correspondence (PDF Page N = page_NNN.md).
        """
        total_pages = 933
        work_dir = temp_dir or os.path.join(tempfile.gettempdir(), "pdf_book_batches")
        os.makedirs(work_dir, exist_ok=True)

        batch_files = []
        merged_doc = fitz.open()

        print(f"\n=======================================================")
        print(f"🚀 Starting Full Book PDF Generation (Pages 1 to {total_pages})")
        print(f"   Mode: {mode} | Batch Size: {batch_size}")
        print(f"=======================================================\n")

        for b_start in range(1, total_pages + 1, batch_size):
            b_end = min(b_start + batch_size - 1, total_pages)
            b_pdf = os.path.join(work_dir, f"batch_{b_start:03d}_{b_end:03d}.pdf")
            print(f"--> [Batch {b_start:03d}-{b_end:03d}] Compiling HTML & Rendering PDF...")

            self.render_range(
                start_page=b_start,
                end_page=b_end,
                output_pdf_path=b_pdf,
                mode=mode,
                include_cover=False,
                include_toc=False
            )

            # Verify batch count
            b_doc = fitz.open(b_pdf)
            expected_count = b_end - b_start + 1
            if len(b_doc) != expected_count:
                print(f"    ⚠️ WARNING: Batch {b_start}-{b_end} produced {len(b_doc)} pages (expected {expected_count})")
            else:
                print(f"    ✅ Batch Verified: Exactly {len(b_doc)}/{expected_count} pages match.")

            merged_doc.insert_pdf(b_doc)
            b_doc.close()
            batch_files.append(b_pdf)

        abs_out = os.path.abspath(output_pdf_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        print(f"\n--> Injecting interactive sidebar chapter bookmarks (TOC outline)...")
        merged_doc.set_toc(self.BOOK_OUTLINE)
        merged_doc.set_metadata({
            "title": "দ্য ব্ল্যাক বুক অব পাওয়ার (The Black Book of Power)",
            "author": "Stan Taylor (স্ট্যান টেলর)",
            "subject": "মনস্তত্ত্ব, ক্ষমতা ও সার্বভৌম সত্তা (Psychology & Power)",
            "keywords": "Power, Psychology, Manipulation, Sovereignty, Bangla Translation",
            "creator": "Universal PDF Publishing Engine"
        })
        print(f"--> Merging all {len(batch_files)} batches into final publication volume...")
        merged_doc.save(abs_out)
        final_count = len(merged_doc)
        file_size = os.path.getsize(abs_out)
        merged_doc.close()

        # Clean up batch temp files
        for bf in batch_files:
            try:
                os.remove(bf)
            except Exception:
                pass

        print(f"\n🎉 Successfully Generated: {abs_out}")
        print(f"   Total Pages: {final_count} / Expected: {total_pages}")
        print(f"   File Size: {file_size / (1024*1024):.2f} MB\n")

        return {
            "output_path": abs_out,
            "page_count": final_count,
            "file_size_bytes": file_size,
            "expected_pages": total_pages,
            "status": "SUCCESS" if final_count == total_pages else "MISMATCH"
        }

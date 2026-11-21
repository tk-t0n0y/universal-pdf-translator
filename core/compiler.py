import os
import glob
import re
from typing import Optional
from core.content_cleaner import PageContentCleaner
from core.pdf_renderer import PDFRenderer

class DocumentCompiler:
    """
    Assembles individual translated page markdown files into a single unified
    clean Markdown book or publication-grade PDF document.
    """

    def __init__(self, pages_dir: str = "translations/pages", output_path: str = "translations/compiled_book.md"):
        self.pages_dir = pages_dir
        self.output_path = output_path

    def compile_markdown(self) -> str:
        """Compiles all translated pages into a single clean markdown file without debug metadata."""
        md_files = glob.glob(os.path.join(self.pages_dir, "page_*.md"))
        if not md_files:
            return ""

        def extract_page_id(filepath):
            filename = os.path.basename(filepath)
            match = re.search(r'page_(\d+)', filename)
            return int(match.group(1)) if match else 0

        md_files.sort(key=extract_page_id)

        compiled_parts = [
            "# দ্য ব্ল্যাক বুক অব পাওয়ার (The Black Book of Power)\n",
            "**স্ট্যান টেলর (Stan Taylor)**\n\n---\n"
        ]

        for fpath in md_files:
            p_id = extract_page_id(fpath)
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()

            parsed = PageContentCleaner.parse_page(raw, fallback_page_num=p_id)
            body = parsed["body_markdown"].strip()
            if body:
                compiled_parts.append(f"\n\n<!-- Page {p_id} -->\n{body}\n\n---\n")

        full_doc = "\n".join(compiled_parts)
        os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as out:
            out.write(full_doc)

        return self.output_path

    def compile_pdf(
        self,
        start_page: int = 1,
        end_page: int = 933,
        mode: str = "1to1",
        include_cover: bool = True,
        include_toc: bool = True
    ) -> str:
        """Compiles translated pages into a publication-grade PDF document."""
        renderer = PDFRenderer(pages_dir=self.pages_dir)
        stats = renderer.render_range(
            start_page=start_page,
            end_page=end_page,
            output_pdf_path=self.output_path,
            mode=mode,
            include_cover=include_cover,
            include_toc=include_toc
        )
        return self.output_path

    def compile(self) -> str:
        """Default compile entrypoint based on output extension."""
        if self.output_path.lower().endswith(".pdf"):
            return self.compile_pdf()
        return self.compile_markdown()
